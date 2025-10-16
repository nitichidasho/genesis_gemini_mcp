"""
Genesis World Simulation Service - Clean Architecture
シンプルで明確な設計：
1. Phase別テンプレート提供のみ（実行しない）
2. Gemini出力コードのみ実行
3. シンプルな状態管理
"""

import re
import sys
import time
import logging
from io import StringIO
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

try:
    import genesis as gs
    GENESIS_AVAILABLE = True
except ImportError:
    GENESIS_AVAILABLE = False
    print("⚠️ Genesis not available. Running in simulation mode.")


class SimulationPhase(Enum):
    """Genesis シミュレーションの段階定義"""
    INIT = "init"           # Genesis初期化段階
    SCENE = "scene"         # シーン作成段階  
    ENTITIES = "entities"   # エンティティ追加段階
    BUILD = "build"         # シーンビルド段階
    SIMULATION = "simulation"  # シミュレーション実行段階


class GenesisState:
    """Genesis状態管理 - シンプルな設計"""
    
    def __init__(self):
        self.is_initialized = False
        self.has_scene = False
        self.is_built = False
        self.current_phase = SimulationPhase.INIT
        self.entities = {}
        self.error_count = 0
        
    def advance_to_phase(self, phase: SimulationPhase):
        """指定段階に進む"""
        self.current_phase = phase
        
    def can_execute_phase(self, phase: SimulationPhase) -> bool:
        """指定段階が実行可能か判定"""
        phase_order = {
            SimulationPhase.INIT: 0,
            SimulationPhase.SCENE: 1,
            SimulationPhase.ENTITIES: 2,
            SimulationPhase.BUILD: 3,
            SimulationPhase.SIMULATION: 4
        }
        current_order = phase_order[self.current_phase]
        target_order = phase_order[phase]
        return target_order >= current_order
        
    def get_summary(self) -> str:
        """状態サマリを取得"""
        return f"""
📊 Genesis Status:
{'✅' if self.is_initialized else '❌'} Genesis Initialized
{'✅' if self.has_scene else '❌'} Scene Created  
{'✅' if self.is_built else '❌'} Scene Built
🎯 Current Phase: {self.current_phase.value}
🏷️ Entities: {len(self.entities)}
⚠️ Errors: {self.error_count}
"""


class PhaseTemplateProvider:
    """Phase別テンプレート提供（実行しない）"""
    
    @staticmethod
    def get_init_template() -> str:
        """初期化段階のテンプレート"""
        return """
# Genesis初期化テンプレート
import genesis as gs
gs.init(backend=gs.gpu)  # または gs.cpu
"""
    
    @staticmethod
    def get_scene_template() -> str:
        """シーン作成段階のテンプレート"""
        return """
# シーン作成テンプレート
scene = gs.Scene(show_viewer=True)
"""
    
    @staticmethod
    def get_entities_template() -> str:
        """エンティティ追加段階のテンプレート"""
        return """
# エンティティ追加テンプレート
# 地面
plane = scene.add_entity(gs.morphs.Plane())

# 球体
sphere = scene.add_entity(
    gs.morphs.Sphere(radius=0.2, pos=(0, 0, 1))
)

# ロボットアーム
robot = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml")
)
"""
    
    @staticmethod
    def get_build_template() -> str:
        """ビルド段階のテンプレート"""
        return """
# シーンビルドテンプレート
scene.build()
"""
    
    @staticmethod
    def get_simulation_template() -> str:
        """シミュレーション段階のテンプレート"""
        return """
# シミュレーション実行テンプレート
# 基本ループ
for i in range(100):
    scene.step()

# または実行
scene.run(duration=5.0)
"""


class CodeExtractor:
    """Gemini出力からPythonコードを抽出"""
    
    @staticmethod
    def extract_python_code(gemini_output: str) -> str:
        """Gemini出力からPythonコードを抽出"""
        # コードブロック（```python ... ```）を検索
        code_block_pattern = r'```python\s*\n(.*?)```'
        matches = re.findall(code_block_pattern, gemini_output, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # コードブロックがない場合、import文から始まる行を探す
        lines = gemini_output.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            stripped = line.strip()
            # Python文の開始を検出
            if (stripped.startswith('import ') or 
                stripped.startswith('from ') or
                stripped.startswith('gs.') or
                stripped.startswith('scene') or
                in_code):
                in_code = True
                code_lines.append(line)
            elif in_code and not stripped:
                # 空行で継続
                code_lines.append(line)
            elif in_code and not any(stripped.startswith(prefix) for prefix in 
                                    ['import', 'from', 'gs.', 'scene', '#', 'def', 'class', 'if', 'for', 'while']):
                # コード以外の行で終了
                break
        
        return '\n'.join(code_lines).strip()
    
    @staticmethod
    def detect_phase_from_code(code: str) -> SimulationPhase:
        """コードから実行段階を検出"""
        if 'gs.init(' in code or 'genesis.init(' in code:
            return SimulationPhase.INIT
        elif 'gs.Scene(' in code or '= scene' in code:
            return SimulationPhase.SCENE
        elif '.add_entity(' in code:
            return SimulationPhase.ENTITIES
        elif '.build()' in code:
            return SimulationPhase.BUILD
        elif '.step()' in code or '.run(' in code:
            return SimulationPhase.SIMULATION
        else:
            return SimulationPhase.SIMULATION  # デフォルト


class CleanSimulationService:
    """クリーンなGenesis Simulation Service"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.state = GenesisState()
        self.template_provider = PhaseTemplateProvider()
        self.code_extractor = CodeExtractor()
        self.scene = None
        self.entities = {}
        
    def get_phase_context_for_gemini(self, user_input: str) -> str:
        """Gemini用のPhaseコンテキストを生成（テンプレート提供のみ）"""
        current_phase = self._determine_needed_phase(user_input)
        
        context = f"""
# Genesis World Phase Context
## Current Phase: {current_phase.value}
## Current State:
{self.state.get_summary()}

## Available Templates (参考用 - 実行しない):
"""
        
        if current_phase == SimulationPhase.INIT:
            context += f"\n### Init Template:\n{self.template_provider.get_init_template()}"
        elif current_phase == SimulationPhase.SCENE:
            context += f"\n### Scene Template:\n{self.template_provider.get_scene_template()}"
        elif current_phase == SimulationPhase.ENTITIES:
            context += f"\n### Entities Template:\n{self.template_provider.get_entities_template()}"
        elif current_phase == SimulationPhase.BUILD:
            context += f"\n### Build Template:\n{self.template_provider.get_build_template()}"
        elif current_phase == SimulationPhase.SIMULATION:
            context += f"\n### Simulation Template:\n{self.template_provider.get_simulation_template()}"
        
        context += f"""

## Instructions:
ユーザー入力「{user_input}」に基づいて、適切なPythonコードを生成してください。
テンプレートは参考用です。実際のコードはユーザーの要求に合わせて調整してください。
現在の段階: {current_phase.value}
"""
        
        return context
    
    def _determine_needed_phase(self, user_input: str) -> SimulationPhase:
        """ユーザー入力から必要な段階を判定"""
        if not self.state.is_initialized:
            return SimulationPhase.INIT
        elif not self.state.has_scene:
            return SimulationPhase.SCENE
        elif '追加' in user_input or 'add' in user_input.lower():
            if self.state.is_built:
                return SimulationPhase.SIMULATION  # ビルド後は操作のみ
            else:
                return SimulationPhase.ENTITIES
        elif 'build' in user_input.lower() or 'ビルド' in user_input:
            return SimulationPhase.BUILD
        else:
            return SimulationPhase.SIMULATION
    
    def execute_gemini_code(self, gemini_output: str, user_input: str) -> Dict[str, Any]:
        """Gemini出力からコードを抽出して実行"""
        try:
            # 1. コード抽出
            python_code = self.code_extractor.extract_python_code(gemini_output)
            if not python_code:
                return {"success": False, "error": "No Python code found in Gemini output"}
            
            print(f"🔍 抽出されたコード:\n{python_code}")
            
            # 2. Phase検出
            detected_phase = self.code_extractor.detect_phase_from_code(python_code)
            print(f"🎯 検出されたPhase: {detected_phase.value}")
            
            # 3. Phase検証
            if not self.state.can_execute_phase(detected_phase):
                return {"success": False, "error": f"Cannot execute {detected_phase.value} in current state"}
            
            # 4. 重複実行防止
            if self._should_skip_execution(python_code, detected_phase):
                return {"success": True, "skipped": True, "message": "Code execution skipped (already executed)"}
            
            # 5. 実行
            result = self._execute_code_safely(python_code)
            
            # 6. 状態更新
            self._update_state_after_execution(python_code, detected_phase)
            
            return result
            
        except Exception as e:
            self.state.error_count += 1
            self.logger.error(f"Code execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _should_skip_execution(self, code: str, phase: SimulationPhase) -> bool:
        """実行スキップが必要か判定"""
        if phase == SimulationPhase.INIT and self.state.is_initialized:
            print("⚠️ Genesis already initialized - skipping init")
            return True
        elif phase == SimulationPhase.SCENE and self.state.has_scene:
            print("⚠️ Scene already created - skipping scene creation")
            return True
        elif phase == SimulationPhase.BUILD and self.state.is_built:
            print("⚠️ Scene already built - skipping build")
            return True
        return False
    
    def _execute_code_safely(self, code: str) -> Dict[str, Any]:
        """コードを安全に実行"""
        start_time = time.time()
        log_capture = StringIO()
        original_stdout = sys.stdout
        
        # 実行環境準備
        local_vars = {
            'gs': gs if GENESIS_AVAILABLE else None,
            'scene': self.scene,
            **self.entities
        }
        
        try:
            sys.stdout = log_capture
            
            # コード実行
            exec(code, local_vars, local_vars)
            
            # 結果取得
            execution_time = time.time() - start_time
            logs = log_capture.getvalue().splitlines()
            
            # 重要なオブジェクトを保存
            if 'scene' in local_vars and local_vars['scene'] is not None:
                self.scene = local_vars['scene']
                print("💾 Scene object saved")
            
            # エンティティを保存
            for key, value in local_vars.items():
                if key not in ['gs', 'scene'] and hasattr(value, '__class__'):
                    self.entities[key] = value
            
            return {
                "success": True,
                "execution_time": execution_time,
                "logs": logs,
                "entities_created": len([k for k in local_vars.keys() if k not in ['gs', 'scene']])
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            sys.stdout = original_stdout
    
    def _update_state_after_execution(self, code: str, phase: SimulationPhase):
        """実行後の状態更新"""
        if 'gs.init(' in code:
            self.state.is_initialized = True
            self.state.advance_to_phase(SimulationPhase.SCENE)
            print("✅ Genesis initialized")
            
        if 'gs.Scene(' in code or 'scene =' in code:
            self.state.has_scene = True
            self.state.advance_to_phase(SimulationPhase.ENTITIES)
            print("✅ Scene created")
            
        if '.build()' in code:
            self.state.is_built = True
            self.state.advance_to_phase(SimulationPhase.SIMULATION)
            print("✅ Scene built")
    
    def get_state_summary(self) -> str:
        """現在の状態サマリを取得"""
        return self.state.get_summary()