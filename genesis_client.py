#!/usr/bin/env python3
"""
Genesis MCP 統合クライアント

使用方法:
    python genesis_client.py                    # インタラクティブモード
    python genesis_client.py --gui              # GUIモード
    python genesis_client.py --server           # サーバーモード
    python genesis_client.py --demo             # デモ実行
    python genesis_client.py --vnc              # VNC表示モード

オプション:
    -h, --help          このヘルプを表示
    -g, --gui           Genesis World GUI表示
    -s, --server        MCPサーバーとして起動
    -d, --demo          デモシミュレーション実行
    -v, --vnc           VNC表示モード
    -i, --interactive   インタラクティブモード
    --host HOST         サーバーホスト (デフォルト: localhost)
    --port PORT         サーバーポート (デフォルト: 8000)
"""

import argparse
import asyncio
import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# .envファイル読み込み関数（強化版）
def load_env_file():
    """Load environment variables from .env file with validation"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        loaded_vars = []
        with open(env_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')  # クォート除去
                        
                        # 空の値をチェック
                        if value and not value.startswith('your_'):
                            os.environ[key] = value
                            loaded_vars.append(key)
                        elif key == 'GEMINI_API_KEY' and value.startswith('your_'):
                            print(f"⚠️ {key} が設定されていません（.envファイルを確認してください）")
                            
                    except ValueError:
                        print(f"⚠️ .envファイル {line_num}行目の形式エラー: {line}")
        
        print(f"✅ .envファイルを読み込みました（{len(loaded_vars)}個の設定）")
        if os.environ.get('VERBOSE_LOGGING') == 'True':
            print(f"📝 読み込み設定: {', '.join(loaded_vars[:5])}...")
    else:
        print(f"⚠️ .envファイルが見つかりません")
        print(f"💡 .env.example を .env にコピーしてAPIキーを設定してください")

# .envファイルを最初に読み込み
load_env_file()

# テンプレートライブラリをインポート
try:
    from genesis_templates import GenesisTemplateLibrary
    TEMPLATES_AVAILABLE = True
    print("✅ Genesis テンプレートライブラリを読み込みました")
except ImportError:
    TEMPLATES_AVAILABLE = False
    print("⚠️ Genesis テンプレートライブラリが見つかりません")

try:
    import genesis as gs
    import math
except ImportError:
    print("❌ Genesis World not installed. Install with: uv pip install genesis-world")
    sys.exit(1)

# プロジェクト内サービスのインポート
try:
    sys.path.append('.')
    from src.genesis_mcp.services.gemini_service import GeminiCLIService
    from src.genesis_mcp.services.simulation import CleanSimulationService
except ImportError as e:
    print(f"⚠️ Warning: Some services not available: {e}")

class GenesisClient:
    """Genesis MCP 統合クライアント"""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.gemini_service = None
        self.simulation_service = None
        self.display_method = self._detect_display_method()
        
        # サービス初期化
        self._initialize_services()
        
        # テンプレートライブラリ初期化
        self._initialize_template_library()
        
        # VNC環境設定
        self._setup_vnc_display_env()
    
    def _initialize_services(self):
        """サービス初期化"""
        try:
            self.gemini_service = GeminiCLIService()
            self.simulation_service = CleanSimulationService()
            print("✅ サービス初期化完了")
        except Exception as e:
            print(f"⚠️ サービス初期化警告: {e}")
    
    def _initialize_template_library(self):
        """テンプレートライブラリ初期化"""
        if TEMPLATES_AVAILABLE:
            try:
                self.template_lib = GenesisTemplateLibrary()
                print("📚 Genesis Template Library 初期化完了")
                print(f"   利用可能カテゴリ: {list(self.template_lib.templates.keys())}")
            except Exception as e:
                print(f"⚠️ テンプレートライブラリ初期化エラー: {e}")
                self.template_lib = None
        else:
            self.template_lib = None
            print("📚 テンプレートライブラリは利用できません")
    
    def _get_viewer_setting(self) -> str:
        """VNC環境に最適化されたビューワー設定"""
        if self.display_method == "vnc":
            return """show_viewer=True,
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, 2.0, 2.0),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=35,
            res=(800, 600),
            max_FPS=15
        )"""
        elif self.display_method == "gui":
            return """show_viewer=True,
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, 3.5, 2.5),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
            max_FPS=60
        )"""
        else:
            # ヘッドレスモード（SSH等）または仮想ディスプレイ
            if self.display_method == "headless":
                return "show_viewer=False"
            else:
                # 仮想ディスプレイの場合はVNC設定を使用
                return """show_viewer=True,
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(4.0, 4.0, 3.0),
            camera_lookat=(0.0, 0.0, 0.0),
            camera_fov=45,
            max_FPS=30
        )"""
    
    def _setup_vnc_display_env(self):
        """VNC環境のためのディスプレイ環境変数設定（シンプル版）"""
        # 現在のDISPLAY設定を確認
        current_display = os.environ.get('DISPLAY')
        
        # ディスプレイエラーの場合、VNC設定ファイルから設定を読み込み
        if not current_display or not self._test_display_connection(current_display):
            print("🔍 ディスプレイエラー検出。VNC設定を確認中...")
            vnc_display = self._load_vnc_display_setting()
            
            if vnc_display:
                os.environ['DISPLAY'] = vnc_display
                self.display_method = "vnc"
                print(f"✅ VNCディスプレイに設定しました: {vnc_display}")
            else:
                print("⚠️ VNC設定が見つかりません。start_vnc.py を先に実行してください。")
                print("💡 実行方法: python start_vnc.py")
                self.display_method = "headless"
                return
        
        if self.display_method == "vnc":
            # VNC用OpenGL設定
            os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
            os.environ['MESA_GLSL_VERSION_OVERRIDE'] = '330'
            os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
            
            print(f"🖥️ VNC Display設定: {os.environ.get('DISPLAY')}")
            print("🎨 VNC用OpenGL設定完了")
    
    def _test_display_connection(self, display: str) -> bool:
        """ディスプレイ接続をテスト"""
        if not display:
            return False
        
        try:
            # xdpyinfoコマンドでディスプレイ接続をテスト
            result = subprocess.run(
                ['xdpyinfo', '-display', display],
                capture_output=True, 
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False
    
    def _load_vnc_display_setting(self) -> Optional[str]:
        """start_vnc.pyで作成されたVNC設定を読み込み"""
        vnc_config_file = Path.home() / ".genesis_vnc_config.json"
        
        if not vnc_config_file.exists():
            return None
        
        try:
            import json
            with open(vnc_config_file, 'r') as f:
                config = json.load(f)
            
            display = config.get('display')
            if display and self._test_display_connection(display):
                print(f"📝 VNC設定ファイルから読み込み: {display}")
                return display
            else:
                print(f"⚠️ VNC設定 {display} は利用できません")
                return None
                
        except Exception as e:
            print(f"⚠️ VNC設定読み込みエラー: {e}")
            return None
    
    def _get_scene_context(self) -> Dict:
        """シーンコンテキストを取得（安全なアクセス）"""
        # simulation_serviceが存在しない場合は初期化
        if not self.simulation_service:
            print("⚠️ SimulationServiceが初期化されていません")
            return self._get_default_scene_context()
        
        # _scene_contextが存在しない場合は強制初期化
        if not hasattr(self.simulation_service, '_scene_context') or self.simulation_service._scene_context is None:
            print("🔧 シーンコンテキストを初期化中...")
            self.simulation_service._init_scene_context()
        
        context = self.simulation_service._scene_context
        
        # 安全なキー取得
        interaction_count = context.get('interaction_count', 0)
        scene_built = context.get('scene_built', False)
        entities = context.get('entities', {})
        executed_code_total = context.get('executed_code_total', '')
        
        return {
            'is_continuous': interaction_count > 0,
            'interaction_count': interaction_count,
            'scene_built': scene_built,
            'entities_count': len(entities),
            'last_code': executed_code_total[-200:] if executed_code_total else ''  # 最新200文字
        }
    
    def _get_default_scene_context(self) -> Dict:
        """デフォルトのシーンコンテキストを取得"""
        return {
            'is_continuous': False,
            'interaction_count': 0,
            'scene_built': False,
            'entities_count': 0,
            'last_code': ''
        }
    
    def _build_history_aware_system_prompt(self, relevant_templates: List[Dict], scene_context: Dict) -> str:
        """履歴ベースシステムプロンプト構築"""
        
        # Genesis制約状態を取得（安全アクセス）
        genesis_initialized = False
        scene_created = False
        scene_built = False
        executed_code = ''
        
        if self.simulation_service:
            if not hasattr(self.simulation_service, '_scene_context') or self.simulation_service._scene_context is None:
                self.simulation_service._init_scene_context()
            
            context = self.simulation_service._scene_context
            genesis_initialized = context.get('genesis_initialized', False)
            scene_created = context.get('scene_created', False)
            scene_built = context.get('scene_built', False)
            executed_code = context.get('executed_code_total', '')
        
        base_prompt = f"""You are an expert Genesis World continuation specialist.

CRITICAL IMPORT - ALWAYS USE THIS EXACT SYNTAX:
import genesis as gs
(NEVER use: import genesis_system, import Genesis, etc.)

CONTEXT - GENESIS STATE:
- Genesis initialized: {genesis_initialized}
- Scene created: {scene_created}  
- Scene built: {scene_built}
- Entities count: {scene_context['entities_count']}
- Interaction: #{scene_context['interaction_count'] + 1}

PREVIOUSLY EXECUTED CODE:
{executed_code[-1000:] if executed_code else "# No previous code"}

CONSTRAINTS BASED ON CURRENT STATE:

{'✅ GENESIS ALREADY INITIALIZED - Do NOT call gs.init() again!' if genesis_initialized else '❌ GENESIS NOT INITIALIZED - Must call gs.init(backend=gs.gpu)'}

{'✅ SCENE ALREADY CREATED - Do NOT create scene again!' if scene_created else '❌ SCENE NOT CREATED - Must create scene = gs.Scene(...)'}

{'✅ SCENE ALREADY BUILT - Cannot add new entities! Only manipulate existing ones.' if scene_built else '❌ SCENE NOT BUILT - Can add entities before calling scene.build()'}

GENERATION RULES:
1. Generate CONTINUATION code only - not full programs
2. Respect the constraints above strictly  
3. Build on previously executed code
4. Use existing entity variables if they exist
5. Use EXACT import syntax: import genesis as gs

CRITICAL API SYNTAX:
✅ CORRECT: import genesis as gs
✅ CORRECT: gs.init(backend=gs.gpu)
✅ CORRECT: scene = gs.Scene(show_viewer=True)
✅ CORRECT: gs.morphs.Box(), gs.morphs.Sphere()
❌ WRONG: import genesis_system as gs
❌ WRONG: import Genesis

CRITICAL: This is continuation code, not a standalone program!"""
        
        # テンプレート例を追加
        if relevant_templates:
            template_examples = "\n\nRELEVANT TEMPLATES:\n"
            for template in relevant_templates[:2]:
                template_examples += f"# {template['category']} - {template['name']}\n"
                template_examples += template['code'][:300] + "...\n\n"
            base_prompt += template_examples
        
        return base_prompt
    
    def _build_history_aware_user_prompt(self, description: str, relevant_templates: List[Dict], scene_context: Dict) -> str:
        """履歴ベースユーザープロンプト構築"""
        
        # 会話履歴を取得
        conversation_history = []
        if self.simulation_service and hasattr(self.simulation_service, '_scene_context'):
            conversation_history = self.simulation_service._scene_context.get('conversation_history', [])
        
        user_prompt = f"""CONTINUATION REQUEST: {description}

CONVERSATION HISTORY:"""
        
        # 最近の会話履歴を追加（最大3件）
        for i, entry in enumerate(conversation_history[-3:], 1):
            user_prompt += f"""
{i}. User: "{entry['input']}"
   Code: {entry['code'][:150]}{'...' if len(entry['code']) > 150 else ''}
"""
        
        if not conversation_history:
            user_prompt += "\n(No previous interactions - this is the first request)"
        
        user_prompt += f"""

CURRENT REQUEST: {description}

Generate CONTINUATION code that builds upon the previous interactions.
- Current entities: {scene_context['entities_count']}
- Interaction #{scene_context['interaction_count'] + 1}
- Focus on what user is asking for now
- Respect Genesis constraints shown in system prompt

Return executable Python code for this continuation."""
        
        return user_prompt
    

    
    def _detect_display_method(self) -> str:
        """最適な表示方法を判定"""
        is_ssh = bool(os.environ.get('SSH_CLIENT') or os.environ.get('SSH_TTY'))
        has_display = bool(os.environ.get('DISPLAY'))
        
        if not is_ssh:
            return "local_gui"
        elif is_ssh and has_display:
            try:
                result = subprocess.run(['xset', 'q'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    return "x11_forwarding"
            except:
                pass
        return "vnc"
    
    async def check_environment(self) -> Dict[str, bool]:
        """環境チェック"""
        results = {}
        
        # Genesis World チェック（初期化は行わない）
        try:
            # Genesis モジュールがインポート可能かチェック
            import genesis as gs_check
            results["genesis"] = True
        except Exception as e:
            print(f"❌ Genesis World利用不可: {e}")
            results["genesis"] = False
        
        # GeminiCLI サービスチェック
        if self.gemini_service:
            try:
                test_response = await self.gemini_service.generate_text("test")
                results["gemini"] = bool(test_response)
            except Exception as e:
                print(f"❌ GeminiCLI接続エラー: {e}")
                results["gemini"] = False
        else:
            results["gemini"] = False
        
        return results
    
    def _extract_code(self, llm_response: str) -> str:
        """LLM応答からコードを抽出（改良版）"""
        # 改行文字を正規化
        response = llm_response.replace('\\\\n', '\n')
        lines = response.split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            stripped_line = line.strip()
            
            # コードブロック開始
            if stripped_line.startswith('```python') or stripped_line.startswith('```'):
                in_code_block = True
                continue
            # コードブロック終了
            elif stripped_line == '```' and in_code_block:
                in_code_block = False
                continue
            # コードブロック内
            elif in_code_block:
                code_lines.append(line)
        
        # コードブロックが見つからない場合は、import文から始まる行を探す
        if not code_lines:
            for line in lines:
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    # import文が見つかったらそこからコードとして扱う
                    start_index = lines.index(line)
                    code_lines = lines[start_index:]
                    break
        
        extracted_code = '\n'.join(code_lines) if code_lines else llm_response
        
        # 強化されたクリーンアップ
        extracted_code = extracted_code.replace('```python', '').replace('```', '').strip()
        
        # 特殊文字や制御文字の削除
        import re
        # <ctrl??> パターンや類似の制御文字を削除
        extracted_code = re.sub(r'<ctrl\d+>', '', extracted_code)
        extracted_code = re.sub(r'<[^>]+>', '', extracted_code)  # HTML-like tags
        extracted_code = re.sub(r'\x00-\x1f\x7f-\x9f', '', extracted_code)  # 制御文字
        
        # 複数の空行を単一の空行に
        extracted_code = re.sub(r'\n{3,}', '\n\n', extracted_code)
        
        return extracted_code.strip()
    
    async def generate_code(self, description: str) -> str:
        """強化されたGemini コード生成（連続操作対応）"""
        if not self.gemini_service:
            return self._get_fallback_code(description)
        
        # CleanSimulationServiceの初期化確認
        if not self.simulation_service:
            print("⚠️ CleanSimulationServiceを初期化中...")
            from src.genesis_mcp.services.simulation import CleanSimulationService
            self.simulation_service = CleanSimulationService()
            print("✅ CleanSimulationService初期化完了")
        
        # シーンコンテキストの確実な初期化
        if not hasattr(self.simulation_service, '_scene_context') or self.simulation_service._scene_context is None:
            print("🔧 強制的にシーンコンテキストを初期化...")
            self.simulation_service._init_scene_context()
            print("✅ シーンコンテキスト初期化完了")
        
        # シーンコンテキストを取得
        scene_context = self._get_scene_context()
        
        # 制約状態の表示
        if hasattr(self.simulation_service, 'get_genesis_state_summary'):
            print("📊 現在のGenesis状態:")
            print(self.simulation_service.get_genesis_state_summary())
            
        if scene_context['is_continuous']:
            print(f"🔄 連続操作モード ({scene_context['interaction_count']}回目)")
        else:
            print("🆕 新規セッション開始")
            
        print("🤖 Genesis Template Library + Gemini 2.5 Flash でコード生成中...")
        
        try:
            # テンプレートライブラリから関連テンプレート検索
            relevant_templates = self._get_relevant_templates(description)
            
            # 履歴ベースシステムプロンプト作成
            system_prompt = self._build_history_aware_system_prompt(relevant_templates, scene_context)
            
            # 履歴ベースユーザープロンプト作成  
            user_prompt = self._build_history_aware_user_prompt(description, relevant_templates, scene_context)
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = await self.gemini_service.generate_text(full_prompt)
            
            if response:
                genesis_code = self._extract_code(response)
                print("📝 生成されたコード:")
                print("=" * 50)
                print(genesis_code)
                print("=" * 50)
                return genesis_code
            else:
                return self._get_fallback_code(description)
                
        except Exception as e:
            print(f"⚠️ GeminiCLI生成エラー: {e}")
            return self._get_fallback_code(description)
    
    def _get_relevant_templates(self, description: str) -> List[Dict]:
        """説明文から関連テンプレートを検索"""
        if not TEMPLATES_AVAILABLE:
            return []
        
        try:
            template_lib = GenesisTemplateLibrary()
            
            # キーワード抽出（簡易版）
            keywords = []
            desc_lower = description.lower()
            
            # 形状キーワード
            shape_keywords = ['球', 'sphere', 'ball', '箱', 'box', 'cube', '円柱', 'cylinder', 
                            'ピラミッド', 'pyramid', 'タワー', 'tower', 'メッシュ', 'mesh']
            
            # 物理キーワード  
            physics_keywords = ['落下', 'drop', 'gravity', '衝突', 'collision', '重力', 
                              '外力', 'force', 'ジョイント', 'joint']
            
            # ロボットキーワード
            robot_keywords = ['robot', 'franka', 'ロボット', 'アーム', 'arm', 'グラスプ', 'grasp']
            
            # 材質キーワード
            material_keywords = ['弾性', 'bounce', 'friction', '摩擦', '密度', 'density']
            
            # 環境キーワード
            env_keywords = ['地形', 'terrain', 'lighting', '照明', 'camera', 'カメラ']
            
            # 高度なキーワード
            advanced_keywords = ['cloth', '布', 'fluid', '流体', 'soft', 'ソフト', 'muscle', '筋肉']
            
            all_keywords = [
                *shape_keywords, *physics_keywords, *robot_keywords, 
                *material_keywords, *env_keywords, *advanced_keywords
            ]
            
            for keyword in all_keywords:
                if keyword in desc_lower:
                    keywords.append(keyword)
            
            if not keywords:
                keywords = ['basic']  # デフォルト
            
            # テンプレート検索
            relevant_templates = template_lib.get_template_by_keywords(keywords)
            
            print(f"🔍 検索キーワード: {keywords}")
            print(f"📚 関連テンプレート: {len(relevant_templates)} 件")
            
            return relevant_templates[:3]  # 上位3件
            
        except Exception as e:
            print(f"⚠️ テンプレート検索エラー: {e}")
            return []
    
    def _build_comprehensive_system_prompt(self, relevant_templates: List[Dict]) -> str:
        """包括的なシステムプロンプト構築"""
        
        # VNC環境対応のビューワー設定を判定
        viewer_setting = self._get_viewer_setting()
        
        base_prompt = f"""You are an expert Genesis World v0.3.4 code generator. Generate ACCURATE Genesis code only.

CRITICAL API RULES - FOLLOW EXACTLY:

1. INITIALIZATION:
   gs.init(backend=gs.gpu)

2. VALID API MODULES (STRICT):
   ✅ VALID: gs.morphs.*, gs.options.*, gs.Scene()
   ❌ FORBIDDEN: gs.robots.* (does not exist), gs.materials.* (use morph params)
   
3. ViewerOptions ONLY VALID ATTRIBUTES:
   ✅ VALID: camera_pos, camera_lookat, camera_fov, res, max_FPS  
   ❌ INVALID: show_world_frame, show_axes, grid, world_frame

4. MANDATORY IMPORTS:
   import genesis as gs
   import time
   import math
   import numpy as np

5. SCENE STRUCTURE (VNC OPTIMIZED):
   - gs.init(backend=gs.gpu)
   - scene = gs.Scene({viewer_setting})  # Low-latency VNC viewer settings
   - plane = scene.add_entity(gs.morphs.Plane())  # MANDATORY: Always add ground plane
   - Add other entities with simple geometry
   - scene.build()
   - VNC-optimized simulation loop (max 50 steps, sleep intervals)

6. POSITIONING AFTER scene.build():
   - Use entity.set_pos() ONLY after scene.build()
   - Or use pos parameter in morph creation
   
7. MANDATORY GROUND PLANE:
   - ALWAYS include: plane = scene.add_entity(gs.morphs.Plane())
   - This provides ground for physics simulation

8. CORRECT SYNTAX EXAMPLES:
   ✅ SPHERE: gs.morphs.Sphere(radius=0.5, pos=(0, 0, 2.0))
   ✅ BOX: gs.morphs.Box(size=(1.0, 1.0, 1.0), pos=(1.0, 0, 1.0))
   ✅ ROBOT: gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml")
   ✅ VIEWER (VNC): gs.options.ViewerOptions(res=(800,600), max_FPS=15, camera_pos=(3, -1, 1.5))
   ❌ NEVER: gs.robots.* (does not exist)
   
9. VNC PERFORMANCE OPTIMIZATION:
   - Use res=(800,600) and max_FPS=15 for smooth VNC display
   - Limit simulation steps to maximum 50 iterations
   - Add time.sleep(0.05) between steps for better responsiveness
   - Avoid complex geometry or high polygon count models
   
10. ROBOT CONTROL:
   - Use: robot.set_dofs_position(angles) NOT set_joint_target_angles
   - Check DOF: dof_count = robot.n_dofs
   - Safe indexing: target_angles[:dof_count]"""
        
        if relevant_templates:
            template_examples = "\n\nRELEVANT TEMPLATE EXAMPLES:\n"
            for i, template in enumerate(relevant_templates[:3]):
                template_examples += f"\n=== {template['category'].upper()} - {template['name'].upper()} ===\n"
                template_examples += template['code']
                template_examples += "\n"
            
            base_prompt += template_examples
        
        base_prompt += "\n\nReturn ONLY executable Python code without explanations or markdown formatting."
        
        return base_prompt
    
    def _build_user_prompt(self, description: str, relevant_templates: List[Dict]) -> str:
        """ユーザープロンプト構築"""
        
        user_prompt = f"""Generate Genesis World v0.3.4 code for: {description}

REQUIREMENTS:
1. Use gs.init(backend=gs.gpu) for GPU acceleration
2. Default simulation: 100 steps (not 1000)
3. Progress display every 10 steps
4. Include appropriate templates from library
5. Ensure proper object positioning

TEMPLATE CATEGORIES AVAILABLE:"""
        
        if relevant_templates:
            for template in relevant_templates:
                user_prompt += f"\n- {template['category']}: {template['name']}"
        
        user_prompt += "\n\nGenerate complete, executable Genesis code only."
        
        return user_prompt
    
    def _get_fallback_code(self, description: str) -> str:
        """フォールバック用固定コード（VNC対応・GPU設定・100ステップ）"""
        viewer_setting = self._get_viewer_setting()
        return f'''# Fallback Genesis Code (VNC-optimized with GPU & 100 steps)
import genesis as gs
import time
import math

# GPU初期化（高性能設定）
gs.init(backend=gs.gpu)

# VNC対応シーン作成
scene = gs.Scene({viewer_setting})

# 必須：地面を追加（物理シミュレーションの基盤）
plane = scene.add_entity(gs.morphs.Plane())

# 基本オブジェクト作成
sphere = scene.add_entity(gs.morphs.Sphere(radius=0.5, pos=(0, 0, 2.0)))

# シーンビルド
scene.build()

print("🎯 フォールバック GPU シミュレーション開始")
print(f"📄 要求: {description}")

# 100ステップシミュレーション（VNC対応）
for i in range(100):
    scene.step()
    if i % 10 == 0:
        print(f"Step: {{i}}/100 - VNC GPU Simulation")
        time.sleep(0.01)

print("✅ VNC GPU シミュレーション完了")
print(f"📄 要求: {description}")'''
    
    def _apply_vnc_optimization_if_needed(self):
        """VNC環境の場合、Genesis表示最適化を適用"""
        display = os.environ.get('DISPLAY', '')
        
        if display and display != ':0':  # VNC環境を検出
            print(f"🖥️ VNC環境検出 ({display}) - 基本OpenGL設定適用中...")
            
            # VNC最適化OpenGL設定（パフォーマンス重視）
            vnc_env = {
                'MESA_GL_VERSION_OVERRIDE': '3.3',
                'MESA_GLSL_VERSION_OVERRIDE': '330', 
                'LIBGL_ALWAYS_SOFTWARE': '1',
                '__GL_SYNC_TO_VBLANK': '0',
                'MESA_NO_ERROR': '1',           # エラーチェック無効化
                'GALLIUM_DRIVER': 'llvmpipe',   # CPU最適化
                '__GL_YIELD': 'NOTHING',        # GPU待機無効化
                'MESA_EXTENSION_OVERRIDE': '-GL_ARB_get_program_binary'  # バイナリ無効化
            }
            
            for key, value in vnc_env.items():
                if key not in os.environ:  # 既存設定を上書きしない
                    os.environ[key] = value
            
            print("✅ VNC用OpenGL設定完了")
    
    async def execute_genesis_code(self, genesis_code: str) -> str:
        """Genesis コード実行（制約・最適化統合版）"""
        print("🔄 Genesis コード実行中...")
        
        try:
            # VNC最適化適用（必要時）
            self._apply_vnc_optimization_if_needed()
            
            # SimulationServiceを使用して安全に実行
            if self.simulation_service:
                # Genesis制約を考慮したコード処理
                if hasattr(self.simulation_service, 'is_continuous_operation'):
                    if self.simulation_service.is_continuous_operation(genesis_code):
                        print("🔄 連続操作モード: Genesis制約適用")
                        processed_code = self.simulation_service.convert_to_scene_manipulation(genesis_code)
                    else:
                        print("🆕 新規シーン作成モード")
                        processed_code = genesis_code
                else:
                    processed_code = genesis_code
                
                result = self.simulation_service.run_simulation(processed_code)
                
                # 実行後に履歴を更新
                if hasattr(self.simulation_service, '_scene_context') and self.simulation_service._scene_context:
                    self.simulation_service._scene_context['interaction_count'] += 1
                    # 履歴に追加する処理は run_simulation で行う（user_inputが必要なため）
                    print(f"🔄 操作回数更新: {self.simulation_service._scene_context['interaction_count']}回")
                
                if result.status == "completed":
                    print("✅ シミュレーション完了")
                    return "✅ Genesis シミュレーション正常実行"
                else:
                    print(f"❌ シミュレーションエラー: {result.error}")
                    return f"❌ Genesis 実行エラー: {result.error}"
            else:
                # フォールバック: 直接実行（非推奨）
                # 一時的なグローバル名前空間を作成
                exec_globals = {
                    '__name__': '__main__',
                    '__builtins__': __builtins__,
                    'gs': gs,
                    'time': time,
                    'math': math,
                    'print': print
                }
                
                # コード実行
                exec(genesis_code, exec_globals)
            
            return "✅ Genesis シミュレーション実行完了"
            
        except Exception as e:
            error_msg = f"❌ Genesis 実行エラー: {e}"
            print(error_msg)
            return error_msg
    
    async def run_simulation(self, description: str):
        """シミュレーション実行 - 改善されたUI表示"""
        print(f"\n{'=' * 80}")
        print(f"🎯 Genesis World実行開始: {description}")
        print(f"{'=' * 80}")
        
        # 環境チェック
        env_status = await self.check_environment()
        if not env_status.get("genesis", False):
            print("❌ Genesis World環境に問題があります")
            return
        
        # 現在の状態を表示
        if self.simulation_service:
            print("\n📊 現在のシステム状態:")
            print(self.simulation_service.get_state_summary())
        
        # Phase別コンテキスト生成（会話履歴+制約+テンプレート）
        enhanced_context = ""
        if self.simulation_service:
            enhanced_context = self.simulation_service.get_enhanced_context_for_gemini(description)
        
        # Geminiでコード生成
        try:
            print(f"\n{'=' * 80}")
            print("🤖 Gemini 2.5 Flash でコード生成中...")
            print("📋 送信するコンテキスト情報:")
            print("-" * 40)
            print("✓ Genesis基本テンプレート")
            print("✓ 制約事項と注意点")
            print("✓ 会話履歴と実行済みコード")
            print("✓ 直近のエラー履歴")
            print("✓ キーワード検索テンプレート")
            print("✓ 現在のシステム状態")
            print("-" * 40)
            print(f"🎯 ユーザーリクエスト: {description}")
            print(f"{'=' * 80}")
            
            # コンテキスト付きプロンプト作成
            enhanced_prompt = f"""
{enhanced_context}

ユーザーリクエスト: {description}

適切なPythonコードを生成してください。テンプレートは参考用で、実際のコードはユーザーの要求に合わせて調整してください。
"""
            
            gemini_response = await self.gemini_service.generate_text(enhanced_prompt)
            
            # Gemini出力からコードを抽出して実行
            if self.simulation_service:
                result = self.simulation_service.execute_gemini_code(gemini_response, description)
                
                print(f"\n{'=' * 80}")
                print("🏁 実行結果サマリ")
                print(f"{'=' * 80}")
                
                if result.get("success"):
                    if result.get("skipped"):
                        print(f"⏭️ {result.get('message', 'コード実行がスキップされました')}")
                    else:
                        print(f"✅ Genesis 実行成功")
                        if result.get("execution_time"):
                            print(f"⏱️ 実行時間: {result['execution_time']:.2f}秒")
                        if result.get("entities_created"):
                            print(f"🎯 作成されたエンティティ: {result['entities_created']}")
                else:
                    print(f"❌ Genesis 実行エラー")
                    print(f"💥 エラー詳細: {result.get('error', 'Unknown error')}")
                    
                print(f"{'=' * 80}")
            
        except Exception as e:
            print(f"\n{'=' * 80}")
            print(f"❌ システムエラー")
            print(f"{'=' * 80}")
            print(f"💥 エラー詳細: {e}")
            print(f"{'=' * 80}")
    
    async def interactive_mode(self):
        """インタラクティブモード"""
        print("🎮 Genesis MCP インタラクティブモード")
        print("終了するには 'quit' または 'exit' を入力してください\\n")
        
        # 環境チェック
        env_status = await self.check_environment()
        if env_status.get("gemini", False):
            print("✅ GeminiCLI サービス利用可能")
        else:
            print("⚠️ GeminiCLI サービス利用不可 - フォールバックコードを使用")
        
        print(f"🖥️ 表示方法: {self.display_method}")
        print()
        
        while True:
            try:
                try:
                    user_input = input("📝 シミュレーション内容を入力: ").strip()
                except UnicodeDecodeError:
                    print("⚠️ 文字エンコーディングエラー。再入力してください。")
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 終了します")
                    break
                
                if not user_input:
                    continue
                
                await self.run_simulation(user_input)
                print()
                
            except KeyboardInterrupt:
                print("\\n👋 終了します")
                break
            except Exception as e:
                import traceback
                print(f"❌ エラー: {e}")
                print(f"📍 エラー詳細: {type(e).__name__}")
                if hasattr(e, '__traceback__'):
                    tb_lines = traceback.format_tb(e.__traceback__)
                    print(f"🔍 トレースバック: {tb_lines[-1].strip()}")
    
    def run_server_mode(self):
        """サーバーモード実行"""
        print(f"🚀 MCPサーバーを起動中 ({self.host}:{self.port})")
        
        try:
            # server.py を実行
            subprocess.run([sys.executable, "server.py"], check=True)
        except KeyboardInterrupt:
            print("\\n🛑 サーバーを停止しました")
        except Exception as e:
            print(f"❌ サーバー起動エラー: {e}")
    
    async def run_demo(self):
        """デモ実行"""
        print("🎪 Genesis MCP デモ実行")
        
        demos = [
            "赤い球体が落下するシミュレーション",
            "2つの箱が接触するシミュレーション", 
            "球体が箱の上を転がるシミュレーション"
        ]
        
        for i, demo in enumerate(demos, 1):
            print(f"\\n📺 デモ {i}/3: {demo}")
            await self.run_simulation(demo)
            
            if i < len(demos):
                input("Enterキーで次のデモへ...")
        
        print("\\n🎉 デモ完了!")

def main():
    parser = argparse.ArgumentParser(
        description="Genesis MCP 統合クライアント",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("-g", "--gui", action="store_true",
                       help="Genesis World GUI表示")
    parser.add_argument("-s", "--server", action="store_true", 
                       help="MCPサーバーとして起動")
    parser.add_argument("-d", "--demo", action="store_true",
                       help="デモシミュレーション実行")
    parser.add_argument("-v", "--vnc", action="store_true",
                       help="VNC表示モード")
    parser.add_argument("-i", "--interactive", action="store_true",
                       help="インタラクティブモード")
    parser.add_argument("--host", default="localhost",
                       help="サーバーホスト (デフォルト: localhost)")
    parser.add_argument("--port", type=int, default=8000,
                       help="サーバーポート (デフォルト: 8000)")
    
    args = parser.parse_args()
    
    client = GenesisClient(host=args.host, port=args.port)
    
    # VNCモード設定
    if args.vnc:
        os.environ["GENESIS_DISPLAY"] = "vnc"
    
    # GUIモード設定
    if args.gui:
        os.environ["GENESIS_SHOW_VIEWER"] = "true"
    
    # サーバーモード
    if args.server:
        client.run_server_mode()
        return
    
    # 非同期モードの処理
    if args.demo:
        asyncio.run(client.run_demo())
    elif args.interactive or not any([args.gui, args.server, args.demo, args.vnc]):
        # デフォルトはインタラクティブモード
        asyncio.run(client.interactive_mode())

if __name__ == "__main__":
    main()