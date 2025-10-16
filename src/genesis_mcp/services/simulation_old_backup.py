"""Simulation service for Genesis World."""

import inspect
import logging
import sys
import traceback
import time
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

try:
    import genesis as gs
    GENESIS_AVAILABLE = True
except ImportError:
    print("Warning: Genesis World not installed. Using mock implementation.")
    GENESIS_AVAILABLE = False
    # Genesis World モック（改善版）
    class MockGenesis:
        def init(self, **kwargs):
            print(f"Mock Genesis initialized with {kwargs}")
            return True
            
        @property
        def cpu(self):
            return "cpu_backend"
            
        @property  
        def gpu(self):
            return "gpu_backend"
            
        class Scene:
            def __init__(self, **kwargs):
                self.entities = []
                self.show_viewer = kwargs.get('show_viewer', True)
                print(f"Mock Scene created (show_viewer={self.show_viewer})")
                
            def add_entity(self, morph):
                entity_id = f"entity_{len(self.entities)}"
                self.entities.append({"id": entity_id, "type": str(morph)})
                print(f"Added entity: {morph}")
                return MockEntity(entity_id)
                
            def build(self):
                print("Mock Scene built")
                
            def step(self):
                pass  # Silent stepping
                
        class morphs:
            @staticmethod
            def Plane():
                return "Plane()"
            @staticmethod
            def Box(size=(1,1,1)):
                return f"Box(size={size})"
            @staticmethod
            def Sphere(radius=1.0):
                return f"Sphere(radius={radius})"
            @staticmethod
            def Cylinder(radius=0.5, height=1.0):
                return f"Cylinder(radius={radius}, height={height})"
                
        class materials:
            @staticmethod
            def Rigid(color=(0,0,1)):
                return f"Rigid(color={color})"
    
    class MockEntity:
        def __init__(self, entity_id):
            self.id = entity_id
            self.position = [0, 0, 0]
            
        def set_pos(self, pos):
            self.position = list(pos)
            print(f"Entity {self.id} position set to {pos}")
            
        def set_position(self, pos):
            self.set_pos(pos)
            
        def set_color(self, color):
            print(f"Entity {self.id} color set to {color}")
    
    gs = MockGenesis()

from pydantic import BaseModel

from src.genesis_mcp.models import SimulationResult

logger = logging.getLogger(__name__)


# 会話履歴ベースシステム（Phaseシステム廃止）


class SimulationService:
    """Service for running Genesis World simulations."""
    
    # クラス変数でGenesis初期化状態を管理
    _genesis_initialized = False
    _genesis_backend = None
    
    def __init__(self):
        """Initialize the simulation service."""
        self.gs = gs
        self.logger = logging.getLogger(__name__)
        
        # シーン管理用
        self._current_scenes = []
        self._current_scene = None  # 現在のアクティブシーン
        
        # コンテキスト初期化
        self._init_scene_context()
    
    def _init_scene_context(self):
        """会話履歴ベースシーンコンテキストを初期化"""
        self._scene_context = {
            'entities': {},  # エンティティ管理 {name: type}
            'genesis_initialized': False,  # gs.init状態
            'scene_created': False,  # gs.Scene()状態
            'scene_built': False,  # scene.build()状態
            'interaction_count': 0,  # 操作回数
            'max_interactions': 50,  # 最大相互作用数
            'executed_code_total': '',  # 累積実行コード
            'conversation_history': []  # 会話履歴 [{'input': str, 'code': str}, ...]
        }
        
    def safe_init_genesis(self, backend="gpu"):
        """Genesis を安全に初期化（重複初期化を防ぐ）"""
        # コンテキスト初期化確認
        if not hasattr(self, '_scene_context') or self._scene_context is None:
            self._init_scene_context()
            
        if not SimulationService._genesis_initialized and not self._scene_context.get('genesis_initialized', False):
            try:
                if backend == "gpu":
                    self.gs.init(backend=self.gs.gpu)
                else:
                    self.gs.init(backend=self.gs.cpu)
                    
                SimulationService._genesis_initialized = True
                SimulationService._genesis_backend = backend
                self._scene_context['genesis_initialized'] = True
                self.logger.info(f"✅ Genesis初期化完了 (backend: {backend})")
                
            except Exception as e:
                self.logger.error(f"❌ Genesis初期化エラー: {e}")
                # 既に初期化されている場合のエラーは無視
                if "already initialized" in str(e):
                    SimulationService._genesis_initialized = True
                    self._scene_context['genesis_initialized'] = True
                    self.logger.info("✅ Genesis は既に初期化済み")
                else:
                    raise
        else:
            self.logger.info(f"✅ Genesis は既に初期化済み (backend: {SimulationService._genesis_backend})")
            self._scene_context['genesis_initialized'] = True
    
    def cleanup_scenes(self):
        """既存のシーンをクリーンアップ（オプション）"""
        try:
            # 既存シーンを削除してメモリ解放
            for scene in self._current_scenes:
                if hasattr(scene, '__del__'):
                    scene.__del__()
                del scene
            
            self._current_scenes.clear()
            self._scene_context.clear()
            print("🧹 既存シーンをクリーンアップしました")
            
        except Exception as e:
            print(f"⚠️ シーンクリーンアップエラー: {e}")
    
    def register_scene(self, scene):
        """新しいシーンを登録"""
        self._current_scenes.append(scene)
        return scene
    
    def get_genesis_constraints(self) -> Dict:
        """Genesis関数の制約情報を返す"""
        return {
            'one_time_only': [
                'gs.init()',  # 一度だけ実行可能
            ],
            'before_build_only': [
                'scene.add_entity()',  # scene.build()前のみ
                'scene.add_camera()',
                'scene.add_light()',
            ],
            'after_build_only': [
                'entity.set_pos()',  # scene.build()後のみ
                'entity.set_vel()',
                'entity.apply_force()',
                'robot.set_dofs_position()',
                'scene.step()',  # いつでも実行可能
            ],
            'always_available': [
                'scene.step()',
                'time.sleep()',
                'print()',
                'math.*',
                'numpy.*'
            ]
        }
    
    def convert_to_scene_manipulation(self, new_code: str) -> str:
        """新規作成コードを既存シーン操作コードに変換"""
        # コンテキストサイズ制限チェック（安全なアクセス）
        if not hasattr(self, '_scene_context'):
            self._init_scene_context()
            
        if self._scene_context['interaction_count'] >= self._scene_context['max_interactions']:
            print(f"⚠️ 最大操作数({self._scene_context['max_interactions']})に達しました。シーンをリセットします。")
            self.cleanup_scenes()
            return self.preprocess_code(new_code)
        
        lines = new_code.split('\n')
        manipulation_code = []
        
        manipulation_code.append("# === 連続操作モード ===")
        manipulation_code.append(f"# 操作回数: {self._scene_context['interaction_count'] + 1}")
        manipulation_code.append("# Genesis制約: scene.build()後はエンティティ操作のみ可能")
        manipulation_code.append("")
        
        # VNCビューワー最適化のためのレンダリング制御
        manipulation_code.append("# VNC表示最適化")
        manipulation_code.append("import time")
        manipulation_code.append("render_interval = 5  # 5ステップ毎にレンダリング")
        manipulation_code.append("")
        
        # 既存エンティティ情報を表示
        if self._scene_context['entities']:
            manipulation_code.append("# 利用可能エンティティ:")
            for entity_name, entity_type in self._scene_context['entities'].items():
                manipulation_code.append(f"# - {entity_name}: {entity_type}")
            manipulation_code.append("")
        
        # 操作コード生成（制約を考慮）
        entity_operations = self._generate_safe_operations(lines)
        manipulation_code.extend(entity_operations)
        
        # VNC最適化シミュレーションループ
        manipulation_code.append("")
        manipulation_code.append("# VNC最適化シミュレーション")
        manipulation_code.append("for i in range(30):  # 短縮ループでVNC応答性向上")
        manipulation_code.append("    scene.step()")
        manipulation_code.append("    if i % render_interval == 0:")
        manipulation_code.append("        time.sleep(0.02)  # VNC用レンダリング待機")
        manipulation_code.append("        print(f'ステップ {i}/30 (VNC最適化)')")
        
        return '\n'.join(manipulation_code)
    
    def detect_genesis_constraints(self, code: str) -> Dict[str, bool]:
        """実行コードからGenesis制約状態を検出"""
        # コンテキスト初期化確認
        if not hasattr(self, '_scene_context') or self._scene_context is None:
            self._init_scene_context()
        
        import re
        
        constraints = {
            'has_init': False,
            'has_scene_creation': False,
            'has_build': False,
            'has_entity_addition': False,
            'has_simulation': False,
            'has_joint': False,
            'genesis_initialized': self._scene_context.get('genesis_initialized', False)
        }
        
        # Genesis初期化パターン
        init_patterns = [
            r'gs\.init\(',
            r'genesis\.init\(',
            r'\.init\s*\(\s*backend\s*=',
        ]
        
        # シーン作成パターン
        scene_patterns = [
            r'gs\.Scene\(',
            r'genesis\.Scene\(',
            r'scene\s*=.*Scene\(',
        ]
        
        # ビルドパターン
        build_patterns = [
            r'\.build\(\)',
            r'scene\.build\(\)',
        ]
        
        # エンティティ追加パターン
        entity_patterns = [
            r'\.add_entity\(',
            r'\.load_urdf\(',
            r'\.load_mjcf\(',
        ]
        
        # シミュレーションパターン
        simulation_patterns = [
            r'\.step\(\)',
            r'scene\.step\(\)',
        ]
        
        # ジョイントパターン
        joint_patterns = [
            r'Joint\(',
            r'\.add_joint\(',
            r'constraints\.',
        ]
        
        # パターンマッチング
        for pattern in init_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                constraints['has_init'] = True
                break
                
        for pattern in scene_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                constraints['has_scene_creation'] = True
                break
                
        for pattern in build_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                constraints['has_build'] = True
                break
                
        for pattern in entity_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                constraints['has_entity_addition'] = True
                break
                
        for pattern in simulation_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                constraints['has_simulation'] = True
                break
                
        for pattern in joint_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                constraints['has_joint'] = True
                break
        
        return constraints
    
    def get_genesis_state_summary(self) -> str:
        """現在のGenesis状態サマリを取得"""
        # コンテキスト初期化確認
        if not hasattr(self, '_scene_context') or self._scene_context is None:
            self._init_scene_context()
            
        state = self._scene_context
        summary = []
        
        if state.get('genesis_initialized', False):
            summary.append("✅ Genesis initialized (gs.init called)")
        else:
            summary.append("❌ Genesis not initialized")
            
        if state.get('scene_created', False):
            summary.append("✅ Scene created")
        else:
            summary.append("❌ Scene not created")
            
        if state.get('scene_built', False):
            summary.append("✅ Scene built (scene.build called)")
            summary.append("⚠️ No new entities can be added after build")
        else:
            summary.append("❌ Scene not built")
            summary.append("✅ Can add entities before build")
        
        summary.append(f"🎯 Entities: {len(state.get('entities', {}))}")
        summary.append(f"🔄 Interactions: {state.get('interaction_count', 0)}")
        
        return "\n".join(summary)
    
    def add_conversation_entry(self, user_input: str, executed_code: str):
        """会話履歴にエントリを追加"""
        # コンテキスト初期化確認
        if not hasattr(self, '_scene_context') or self._scene_context is None:
            self._init_scene_context()
        
        # 必要なキーが存在しない場合は追加
        if 'conversation_history' not in self._scene_context:
            self._scene_context['conversation_history'] = []
        if 'executed_code_total' not in self._scene_context:
            self._scene_context['executed_code_total'] = ''
            
        entry = {
            'input': user_input,
            'code': executed_code,
            'timestamp': time.time()
        }
        self._scene_context['conversation_history'].append(entry)
        
        # 累積コード更新
        self._scene_context['executed_code_total'] += f"\n# User: {user_input}\n{executed_code}\n"
        
        # 制約状態を更新（クラス変数と同期）
        constraints = self.detect_genesis_constraints(executed_code)
        if constraints['has_init']:
            self._scene_context['genesis_initialized'] = True
            SimulationService._genesis_initialized = True
            print("🔄 Genesis初期化状態を更新")
        if constraints['has_scene_creation']:
            self._scene_context['scene_created'] = True
            print("🔄 Scene作成状態を更新")
        if constraints['has_build']:
            self._scene_context['scene_built'] = True
            print("🔄 Scene構築状態を更新")
    
    def _generate_safe_operations(self, lines: List[str]) -> List[str]:
        """Genesis制約を考慮した安全な操作コードを生成"""
        operations = []
        constraints = self.get_genesis_constraints()
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # 制約チェック
            if any(constraint in line for constraint in constraints['one_time_only']):
                operations.append(f"# SKIP: {line} (一度のみ実行可能)")
                continue
                
            if any(constraint in line for constraint in constraints['before_build_only']):
                if self._scene_context['scene_built']:
                    # エンティティ追加の代替操作
                    if 'scene.add_entity(' in line:
                        operations.extend(self._convert_entity_addition_to_manipulation(line))
                    else:
                        operations.append(f"# SKIP: {line} (build後は不可)")
                else:
                    operations.append(line)
                continue
            
            # 許可された操作
            if any(constraint in line for constraint in constraints['after_build_only']) or \
               any(constraint in line for constraint in constraints['always_available']):
                operations.append(line)
            else:
                # 不明な操作は安全のためコメントアウト
                operations.append(f"# CAUTIOUS: {line}")
        
        return operations
    
    def process_code_with_constraints(self, code: str) -> str:
        """Genesis制約に基づいてコードを処理・修正"""
        # コンテキスト初期化確認
        if not hasattr(self, '_scene_context') or self._scene_context is None:
            self._init_scene_context()
            
        lines = code.split('\n')
        processed_lines = []
        state = self._scene_context
        
        # Genesisの実際の初期化状態を確認
        try:
            # Genesis内部状態を直接チェック
            if hasattr(self.gs, '_initialized') and self.gs._initialized:
                genesis_actually_initialized = True
                SimulationService._genesis_initialized = True
                state['genesis_initialized'] = True
            elif hasattr(self.gs, 'is_initialized') and callable(self.gs.is_initialized):
                genesis_actually_initialized = self.gs.is_initialized()
                if genesis_actually_initialized:
                    SimulationService._genesis_initialized = True
                    state['genesis_initialized'] = True
            else:
                genesis_actually_initialized = SimulationService._genesis_initialized or state.get('genesis_initialized', False)
        except:
            genesis_actually_initialized = SimulationService._genesis_initialized or state.get('genesis_initialized', False)
        
        # クラス変数での重複チェック追加
        genesis_init_status = genesis_actually_initialized
        
        processed_lines.append("# === 履歴ベース制約処理 ===")
        processed_lines.append(f"# Genesis initialized (class): {SimulationService._genesis_initialized}")
        processed_lines.append(f"# Genesis initialized (context): {state.get('genesis_initialized', False)}")
        processed_lines.append(f"# Genesis initialized (actual): {genesis_actually_initialized}")
        processed_lines.append(f"# Scene created: {state.get('scene_created', False)}")
        processed_lines.append(f"# Scene built: {state.get('scene_built', False)}")
        processed_lines.append("")
        
        for line in lines:
            stripped = line.strip()
            should_skip = False
            skip_reason = ""
            
            # 不正なimport修正
            if 'import genesis_system' in line:
                line = line.replace('import genesis_system as gs', 'import genesis as gs')
                line = line.replace('import genesis_system', 'import genesis as gs')
                print("🔧 修正: genesis_system → genesis")
            
            # Genesis初期化の重複チェック（より正確に）
            if ('gs.init(' in line or 'genesis.init(' in line) and genesis_init_status:
                should_skip = True
                skip_reason = "Genesis already initialized"
                print(f"🚫 Genesis初期化をスキップ: {stripped}")
                
            # Scene作成の重複チェック（より正確に）
            elif ('gs.Scene(' in line or 'genesis.Scene(' in line or 'scene =' in line) and state.get('scene_created', False):
                should_skip = True
                skip_reason = "Scene already created"
                print(f"🚫 Scene作成をスキップ: {stripped}")
                
            # ビルド後エンティティ追加チェック
            elif '.add_entity(' in line and state.get('scene_built', False):
                should_skip = True
                skip_reason = "Cannot add entities after scene.build()"
                print(f"🚫 エンティティ追加をスキップ: {stripped}")
                
            # Build重複チェック
            elif '.build()' in line and state.get('scene_built', False):
                should_skip = True
                skip_reason = "Scene already built"
                print(f"🚫 Build重複をスキップ: {stripped}")
            
            if should_skip:
                if stripped:
                    processed_lines.append(f"# SKIPPED ({skip_reason}): {line}")
                    print(f"⚠️ {skip_reason}: {stripped}")
                else:
                    processed_lines.append(line)
            else:
                processed_lines.append(line)
                if stripped and any(keyword in stripped for keyword in ['gs.init', 'gs.Scene', '.build()', '.add_entity(']):
                    print(f"✅ 実行許可: {stripped}")
        
        return '\n'.join(processed_lines)
    
    def _convert_entity_addition_to_manipulation(self, line: str) -> List[str]:
        """エンティティ追加を既存エンティティ操作に変換"""
        operations = []
        
        if 'Sphere' in line:
            operations.append("# 球体操作 (新規追加の代替)")
            operations.append("if 'sphere' in globals() and sphere is not None:")
            operations.append("    import numpy as np")
            operations.append("    new_pos = (np.random.uniform(-3, 3), np.random.uniform(-3, 3), 2.0)")
            operations.append("    sphere.set_pos(new_pos)")
            operations.append("    print(f'球体を移動: {new_pos}')")
            operations.append("else:")
            operations.append("    print('⚠️ 球体エンティティが見つかりません')")
            
        elif 'Box' in line:
            operations.append("# 箱操作 (新規追加の代替)")
            operations.append("if 'box1' in globals() and box1 is not None:")
            operations.append("    import numpy as np")
            operations.append("    new_pos = (np.random.uniform(-3, 3), np.random.uniform(-3, 3), 1.0)")
            operations.append("    box1.set_pos(new_pos)")
            operations.append("    print(f'箱を移動: {new_pos}')")
            operations.append("else:")
            operations.append("    print('⚠️ 箱エンティティが見つかりません')")
        
        return operations
    
    def preprocess_code(self, code: str) -> str:
        """Genesis コードの前処理（初期化部分を安全化）"""
        lines = code.split('\n')
        processed_lines = []
        
        for line in lines:
            # gs.init() の呼び出しを安全な呼び出しに置換
            if 'gs.init(' in line and not line.strip().startswith('#'):
                # コメントアウトして安全な初期化に置換
                processed_lines.append(f"# {line}")
                processed_lines.append("# Genesis初期化は自動で処理されます")
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def run_simulation(self, code: str, parameters: Dict[str, Any] = None) -> SimulationResult:
        """Run a Genesis World simulation from provided code.
        
        Args:
            code: Python code that uses Genesis World
            parameters: Optional parameters to pass to the simulation
            
        Returns:
            SimulationResult with simulation results and logs
        """
        # 必ず最初にコンテキストを初期化
        if not hasattr(self, '_scene_context'):
            self._init_scene_context()
            
        # 制約ベース処理
        print("🔧 Genesis制約チェック中...")
        print(self.get_genesis_state_summary())
        
        # クラス変数の状態も確認
        print(f"🔍 クラス変数状態: _genesis_initialized={SimulationService._genesis_initialized}")
        
        # 制約に基づいたコード処理
        processed_code = self.process_code_with_constraints(code)
        
        print(f"🔧 処理後のコード（最初の200文字）:")
        print(processed_code[:200] + "..." if len(processed_code) > 200 else processed_code)
        
        logs = []
        result = {}
        start_time = time.time()
        
        # Create a string buffer to capture stdout for logs
        log_capture = StringIO()
        
        # Create a safe execution environment
        local_vars = {
            "gs": self.gs,
            "time": time,
            "math": __import__('math'),
            "parameters": parameters or {},
            "result": result,
            "self": self,  # SimulationServiceへの参照を追加
        }
        
        # 既存シーンオブジェクトの提供
        if hasattr(self, '_current_scene') and self._current_scene is not None:
            local_vars["scene"] = self._current_scene
            print("✅ 既存シーンオブジェクトを使用")
        
        # Save original stdout and redirect to our capture
        original_stdout = sys.stdout
        sys.stdout = log_capture
        
        try:
            # Genesis を安全に初期化
            self.safe_init_genesis("gpu")  # デフォルトでGPUバックエンド
            
            # フェーズ対応コードを使用
            # 既に _process_code_for_phase で処理済み
            print(f"📝 実行するコード:\n{processed_code[:200]}...")
            
            # コンテキスト安全チェック
            if not hasattr(self, '_scene_context') or self._scene_context is None:
                self._init_scene_context()
            
            # 必要なキーが存在しない場合は追加
            if 'interaction_count' not in self._scene_context:
                self._scene_context['interaction_count'] = 0
            
            # 実行状態の判定
            is_continuous = self._scene_context['interaction_count'] > 0
            
            if is_continuous:
                print(f"🔄 連続操作モード (操作回数: {self._scene_context['interaction_count'] + 1})")
            else:
                print("🆕 新規セッション開始")
                # 既存シーンをクリーンアップして新規作成
                self.cleanup_scenes()
            
            # Add Genesis availability info
            local_vars["GENESIS_AVAILABLE"] = GENESIS_AVAILABLE
            
            # Execute the simulation code
            exec(processed_code, local_vars, local_vars)
            
            # 実行後にGenesis状態を確実に更新
            try:
                if hasattr(self.gs, '_initialized') and self.gs._initialized:
                    SimulationService._genesis_initialized = True
                    if hasattr(self, '_scene_context'):
                        self._scene_context['genesis_initialized'] = True
                    print("🔄 Genesis初期化状態を実行後に更新")
            except:
                pass
            
            # Extract any results assigned to the result variable
            if "result" in local_vars and local_vars["result"]:
                result = local_vars["result"]
            else:
                result = {"status": "executed", "genesis_available": GENESIS_AVAILABLE}
                
            # Get the logs
            logs = log_capture.getvalue().splitlines()
            
            execution_time = time.time() - start_time
            
            # コンテキストを更新（安全なアクセス）
            if not hasattr(self, '_scene_context'):
                self._init_scene_context()
            
            # 必要なキーが存在しない場合は追加
            if 'interaction_count' not in self._scene_context:
                self._scene_context['interaction_count'] = 0
            
            self._scene_context['interaction_count'] += 1
            self._scene_context['last_code'] = processed_code
            
            # シーンオブジェクトの保存
            if "scene" in local_vars and local_vars["scene"] is not None:
                self._current_scene = local_vars["scene"]
                print("💾 シーンオブジェクトを保存しました")
            
            # 制約状態の更新
            constraints = self.detect_genesis_constraints(processed_code)
            if constraints['has_build']:
                self._scene_context['scene_built'] = True
                print("✅ シーンビルド完了")
            if constraints['has_scene_creation']:
                self._scene_context['scene_created'] = True  
                print("✅ シーン作成完了")
            if constraints['has_init']:
                self._scene_context['genesis_initialized'] = True
                print("✅ Genesis初期化完了")
            
            # エンティティ追加の検出
            if '.add_entity(' in processed_code:
                import re
                entity_matches = re.findall(r'(\w+)\s*=\s*scene\.add_entity', processed_code)
                for entity_name in entity_matches:
                    self._scene_context['entities'][entity_name] = 'entity'
                print(f"🎯 エンティティ更新: {len(self._scene_context['entities'])}個")
            
            return SimulationResult(
                result=result,
                logs=logs,
                status="completed",
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            logs.extend(log_capture.getvalue().splitlines())
            logs.append(f"Error: {error_msg}")
            logs.append(traceback.format_exc())
            logger.exception("Error running simulation")
            
            return SimulationResult(
                result={"error": error_msg},
                logs=logs,
                status="error",
                error=error_msg,
                execution_time=execution_time
            )
            
        finally:
            # Restore stdout
            sys.stdout = original_stdout
    
    def get_world_info(self) -> Dict[str, Any]:
        """Get information about the Genesis World API.
        
        Returns:
            Dictionary with information about available modules, classes, and functions
        """
        world_info = {
            "version": getattr(self.gs, "__version__", "unknown"),
            "modules": {},
            "examples": self._get_examples(),
        }
        
        # Collect module information
        for name, obj in inspect.getmembers(self.gs):
            if name.startswith("_"):
                continue
                
            if inspect.ismodule(obj):
                module_info = self._get_module_info(obj)
                if module_info:
                    world_info["modules"][name] = module_info
            elif inspect.isclass(obj):
                world_info["classes"] = world_info.get("classes", {})
                world_info["classes"][name] = self._get_class_info(obj)
            elif inspect.isfunction(obj):
                world_info["functions"] = world_info.get("functions", {})
                world_info["functions"][name] = self._get_function_info(obj)
                
        return world_info
    
    def _get_module_info(self, module) -> Dict[str, Any]:
        """Extract information about a module."""
        info = {
            "doc": inspect.getdoc(module),
            "classes": {},
            "functions": {}
        }
        
        for name, obj in inspect.getmembers(module):
            if name.startswith("_"):
                continue
                
            if inspect.isclass(obj):
                info["classes"][name] = self._get_class_info(obj)
            elif inspect.isfunction(obj):
                info["functions"][name] = self._get_function_info(obj)
                
        return info
    
    def _get_class_info(self, cls) -> Dict[str, Any]:
        """Extract information about a class."""
        return {
            "doc": inspect.getdoc(cls),
            "methods": {
                name: self._get_function_info(method)
                for name, method in inspect.getmembers(cls, inspect.isfunction)
                if not name.startswith("_")
            }
        }
    
    def _get_function_info(self, func) -> Dict[str, Any]:
        """Extract information about a function."""
        sig = inspect.signature(func)
        
        return {
            "doc": inspect.getdoc(func),
            "signature": str(sig),
            "parameters": {
                name: {
                    "default": str(param.default) if param.default is not inspect.Parameter.empty else None,
                    "annotation": str(param.annotation) if param.annotation is not inspect.Parameter.empty else None,
                }
                for name, param in sig.parameters.items()
            }
        }
    
    def _get_examples(self) -> List[Dict[str, str]]:
        """Get example simulations."""
        return [
            {
                "name": "Basic Simulation",
                "description": "A simple simulation of a world with moving agents",
                "code": """
# Create a simple world with agents
world = gs.World()
agent = gs.Agent(position=(0, 0))
world.add_agent(agent)

# Run the simulation for 10 steps
for step in range(10):
    agent.move(direction="north", distance=1)
    world.step()
    print(f"Step {step}: Agent at position {agent.position}")

# Return final world state
result = {
    "world_state": world.get_state(),
    "agent_positions": [a.position for a in world.agents]
}
"""
            },
            {
                "name": "Resource Collection Simulation",
                "description": "Agents collecting resources in a world",
                "code": """
# Create a world with resources
world = gs.World()

# Add resources to the world
for i in range(5):
    resource = gs.Resource(position=(i*5, i*5), type="food", quantity=10)
    world.add_resource(resource)

# Add agents with different strategies
collector_agent = gs.Agent(position=(0, 0), type="collector")
explorer_agent = gs.Agent(position=(10, 10), type="explorer")
world.add_agent(collector_agent)
world.add_agent(explorer_agent)

# Run simulation
for step in range(20):
    # Agents follow their strategies
    for agent in world.agents:
        if agent.type == "collector":
            # Collectors move toward nearest resource
            nearest = world.find_nearest_resource(agent.position)
            if nearest:
                direction = world.get_direction(agent.position, nearest.position)
                agent.move(direction=direction, distance=1)
                # Collect if at resource
                if agent.position == nearest.position:
                    agent.collect(nearest, quantity=1)
        elif agent.type == "explorer":
            # Explorers move randomly
            direction = ["north", "east", "south", "west"][step % 4]
            agent.move(direction=direction, distance=2)
    
    # Step the world forward
    world.step()
    print(f"Step {step}: Collector has {collector_agent.inventory}, Explorer has {explorer_agent.inventory}")

# Return results
result = {
    "steps": step + 1,
    "collector_inventory": collector_agent.inventory,
    "explorer_inventory": explorer_agent.inventory,
    "remaining_resources": [
        {"position": r.position, "quantity": r.quantity}
        for r in world.resources
    ]
}
"""
            }
        ]

    def generate_scene_code(self, description: str, show_viewer: bool = True) -> str:
        """Generate Genesis Scene code based on natural language description.
        
        Args:
            description: Natural language description of the scene
            show_viewer: Whether to show the viewer
            
        Returns:
            Generated Python code for creating the scene
        """
        # Parse the description and generate appropriate code
        code_parts = [
            "import genesis as gs",
            "gs.init(backend=gs.gpu)",
            "",
            f"scene = gs.Scene(show_viewer={show_viewer})",
            ""
        ]
        
        # Parse description for objects to add
        description_lower = description.lower()
        
        # Always add a plane as ground unless explicitly mentioned not to
        if "no plane" not in description_lower and "no ground" not in description_lower:
            code_parts.append("plane = scene.add_entity(gs.morphs.Plane())")
        
        # Check for specific objects mentioned
        if "box" in description_lower or "cube" in description_lower:
            size = self._extract_size_from_description(description_lower, default=(1.0, 1.0, 1.0))
            code_parts.append(f"box = scene.add_entity(gs.morphs.Box(size={size}))")
            
        if "sphere" in description_lower or "ball" in description_lower:
            radius = self._extract_radius_from_description(description_lower, default=0.5)
            code_parts.append(f"sphere = scene.add_entity(gs.morphs.Sphere(radius={radius}))")
            
        if "cylinder" in description_lower:
            radius = self._extract_radius_from_description(description_lower, default=0.5)
            height = self._extract_height_from_description(description_lower, default=1.0)
            code_parts.append(f"cylinder = scene.add_entity(gs.morphs.Cylinder(radius={radius}, height={height}))")
            
        if "robot" in description_lower or "arm" in description_lower or "franka" in description_lower or "panda" in description_lower:
            code_parts.append("robot = scene.add_entity(gs.morphs.MJCF(file='xml/franka_emika_panda/panda.xml'))")
        
        # Add multiple objects if requested
        if "multiple" in description_lower or "several" in description_lower or "few" in description_lower:
            count = self._extract_count_from_description(description_lower, default=3)
            code_parts.append(f"# Adding {count} random objects")
            code_parts.append("import random")
            code_parts.append(f"for i in range({count}):")
            code_parts.append("    pos = (random.uniform(-2, 2), random.uniform(-2, 2), random.uniform(0.5, 2))")
            code_parts.append("    obj = scene.add_entity(gs.morphs.Box(size=(0.5, 0.5, 0.5)))")
            code_parts.append("    obj.set_position(pos)")
        
        # Add build and run steps
        code_parts.extend([
            "",
            "scene.build()",
            "",
            "# Run simulation for a few steps",
            "for i in range(100):",
            "    scene.step()",
            "",
            "# Return scene information",
            "result = {",
            "    'description': '" + description.replace("'", "\\'") + "',",
            "    'entities_count': len(scene.entities),",
            "    'status': 'scene_created'",
            "}"
        ])
        
        return "\n".join(code_parts)

    def generate_add_object_code(self, object_type: str, position: list = None, properties: dict = None) -> str:
        """Generate code to add a specific object to a scene.
        
        Args:
            object_type: Type of object (box, sphere, plane, etc.)
            position: Position coordinates
            properties: Object properties
            
        Returns:
            Generated Python code to add the object
        """
        pos = position or [0, 0, 1]
        props = properties or {}
        
        code_parts = [
            "import genesis as gs",
            "gs.init(backend=gs.gpu)",
            "",
            "# Create or get existing scene",
            "scene = gs.Scene(show_viewer=True)",
            ""
        ]
        
        # Generate object-specific code
        object_type_lower = object_type.lower()
        
        if object_type_lower in ["box", "cube"]:
            size = props.get("size", [1.0, 1.0, 1.0])
            if isinstance(size, (int, float)):
                size = [size, size, size]
            code_parts.append(f"obj = scene.add_entity(gs.morphs.Box(size={tuple(size)}))")
            
        elif object_type_lower in ["sphere", "ball"]:
            radius = props.get("radius", 0.5)
            code_parts.append(f"obj = scene.add_entity(gs.morphs.Sphere(radius={radius}))")
            
        elif object_type_lower == "cylinder":
            radius = props.get("radius", 0.5)
            height = props.get("height", 1.0)
            code_parts.append(f"obj = scene.add_entity(gs.morphs.Cylinder(radius={radius}, height={height}))")
            
        elif object_type_lower == "plane":
            code_parts.append("obj = scene.add_entity(gs.morphs.Plane())")
            
        elif object_type_lower in ["robot", "arm", "franka", "panda"]:
            code_parts.append("obj = scene.add_entity(gs.morphs.MJCF(file='xml/franka_emika_panda/panda.xml'))")
            
        else:
            # Default to box for unknown types
            code_parts.append(f"obj = scene.add_entity(gs.morphs.Box(size=(1.0, 1.0, 1.0)))  # {object_type}")
        
        # Add position setting if specified (except for plane)
        if position and object_type_lower != "plane":
            code_parts.append(f"obj.set_position([{pos[0]}, {pos[1]}, {pos[2]}])")
        
        # Add color if specified
        if "color" in props:
            color = props["color"]
            if isinstance(color, str):
                # Convert color names to RGB
                color_map = {
                    "red": (1.0, 0.0, 0.0),
                    "green": (0.0, 1.0, 0.0),
                    "blue": (0.0, 0.0, 1.0),
                    "yellow": (1.0, 1.0, 0.0),
                    "purple": (1.0, 0.0, 1.0),
                    "cyan": (0.0, 1.0, 1.0),
                    "white": (1.0, 1.0, 1.0),
                    "black": (0.0, 0.0, 0.0)
                }
                color = color_map.get(color.lower(), (0.5, 0.5, 0.5))
            code_parts.append(f"obj.set_color({color})")
        
        code_parts.extend([
            "",
            "scene.build()",
            "",
            "# Run for a few steps to see the object",
            "for i in range(50):",
            "    scene.step()",
            "",
            "result = {",
            f"    'object_type': '{object_type}',",
            f"    'position': {pos},",
            f"    'properties': {props},",
            "    'status': 'object_added'",
            "}"
        ])
        
        return "\n".join(code_parts)

    def _extract_size_from_description(self, description: str, default: tuple) -> tuple:
        """Extract size from natural language description."""
        import re
        # Look for patterns like "size 2x2x2" or "2 by 2 by 2"
        size_pattern = r"(?:size\s+)?(\d+(?:\.\d+)?)(?:\s*x\s*|\s+by\s+)(\d+(?:\.\d+)?)(?:\s*x\s*|\s+by\s+)(\d+(?:\.\d+)?)"
        match = re.search(size_pattern, description)
        if match:
            return (float(match.group(1)), float(match.group(2)), float(match.group(3)))
        
        # Look for single dimension like "size 2"
        single_size = re.search(r"size\s+(\d+(?:\.\d+)?)", description)
        if single_size:
            size = float(single_size.group(1))
            return (size, size, size)
            
        return default

    def _extract_radius_from_description(self, description: str, default: float) -> float:
        """Extract radius from natural language description."""
        import re
        radius_pattern = r"radius\s+(\d+(?:\.\d+)?)"
        match = re.search(radius_pattern, description)
        if match:
            return float(match.group(1))
        return default

    def _extract_height_from_description(self, description: str, default: float) -> float:
        """Extract height from natural language description."""
        import re
        height_pattern = r"height\s+(\d+(?:\.\d+)?)"
        match = re.search(height_pattern, description)
        if match:
            return float(match.group(1))
        return default

    def _extract_count_from_description(self, description: str, default: int) -> int:
        """Extract count from natural language description."""
        import re
        # Look for numbers in the description
        count_pattern = r"(\d+)\s+(?:objects?|items?|things?|boxes?|spheres?)"
        match = re.search(count_pattern, description)
        if match:
            return int(match.group(1))
        return default