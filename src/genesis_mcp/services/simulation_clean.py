"""
Genesis World Simulation Service - Clean Architecture v2
完全に新しい設計：
1. 会話履歴と実行コード履歴の分離管理
2. Geminiに基本テンプレート+制約+会話履歴を常時提供  
3. 重複実行禁止とPhase管理
4. genesis_templates.pyとの統合
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


class ConversationHistory:
    """会話履歴と実行コード履歴の管理"""
    
    def __init__(self):
        self.turns = []  # 会話ターン履歴
        self.executed_code_total = ""  # 累積実行コード
        
    def add_turn(self, user_input: str, generated_code: str, execution_result: Dict[str, Any]):
        """ターン追加"""
        turn = {
            'turn_number': len(self.turns) + 1,
            'user_input': user_input,
            'generated_code': generated_code,
            'execution_result': execution_result,
            'timestamp': time.time()
        }
        self.turns.append(turn)
        
        # 成功したコードのみ累積
        if execution_result.get('success'):
            self.executed_code_total += f"\n# Turn {turn['turn_number']}: {user_input}\n{generated_code}\n"
    
    def get_context_for_gemini(self) -> str:
        """Gemini用のコンテキスト生成"""
        if not self.turns:
            return "# 初回実行"
        
        context = f"# 会話履歴（{len(self.turns)}ターン目）\n"
        context += "# これまでに実行されたコード:\n"
        context += self.executed_code_total
        context += "\n# 続きを作成してください\n"
        
        return context


class GenesisConstraints:
    """Genesis制約とガイドライン"""
    
    @staticmethod
    def get_basic_template() -> str:
        """基本テンプレート（常に提供）"""
        return """
# Genesis基本テンプレート
import genesis as gs

# 1. 初期化（1回のみ実行可能）
gs.init(backend=gs.gpu)  # またはgs.cpu

# 2. シーン作成
scene = gs.Scene(show_viewer=True)

# 3. エンティティ追加（scene.build()前のみ）
plane = scene.add_entity(gs.morphs.Plane())
sphere = scene.add_entity(gs.morphs.Sphere(radius=0.2, pos=(0, 0, 1)))

# 4. シーンビルド（1回のみ実行可能）
scene.build()

# 5. シミュレーション実行
for i in range(100):
    scene.step()
"""
    
    @staticmethod 
    def get_constraints_info() -> str:
        """制約情報"""
        return """
# Genesis制約事項:
# ⚠️ 重複実行禁止関数:
#   - gs.init() : 1回のみ実行可能
#   - scene.build() : 1回のみ実行可能
# ⚠️ 順序制約:
#   - エンティティ追加はscene.build()前のみ
#   - scene.step()等はscene.build()後のみ
# ⚠️ Import注意:
#   - 正しい: import genesis as gs
#   - 間違い: import genesis_sim as gs
"""


class GenesisState:
    """Genesis状態管理"""
    
    def __init__(self):
        self.is_initialized = False
        self.has_scene = False
        self.is_built = False
        self.entities = {}
        self.error_count = 0
        
    def get_summary(self) -> str:
        """状態サマリを取得"""
        return f"""
📊 Genesis Status:
{'✅' if self.is_initialized else '❌'} Genesis Initialized
{'✅' if self.has_scene else '❌'} Scene Created  
{'✅' if self.is_built else '❌'} Scene Built
🏷️ Entities: {len(self.entities)}
⚠️ Errors: {self.error_count}
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


class CleanSimulationService:
    """クリーンなGenesis Simulation Service - 新しい設計"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.state = GenesisState()
        self.conversation_history = ConversationHistory()
        self.constraints = GenesisConstraints()
        self.code_extractor = CodeExtractor()
        self.scene = None
        self.entities = {}
        
        # VNC環境設定
        self._setup_vnc_environment()
        
    def _setup_vnc_environment(self):
        """VNC環境設定"""
        try:
            import os
            display = os.environ.get('DISPLAY', ':10')
            print(f"🖥️ VNC環境検出 ({display}) - 基本OpenGL設定適用中...")
            
            # OpenGL設定
            os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
            os.environ['MESA_GLSL_VERSION_OVERRIDE'] = '330'
            print("✅ VNC用OpenGL設定完了")
        except Exception as e:
            print(f"⚠️ VNC環境設定警告: {e}")
    
    def get_enhanced_context_for_gemini(self, user_input: str) -> str:
        """Gemini用の強化されたコンテキスト生成"""
        
        # 基本情報
        context_parts = []
        context_parts.append("# Genesis World コード生成タスク")
        context_parts.append(self.constraints.get_basic_template())
        context_parts.append(self.constraints.get_constraints_info())
        
        # 会話履歴
        conversation_context = self.conversation_history.get_context_for_gemini()
        context_parts.append(conversation_context)
        
        # キーワード検索によるテンプレート取得
        keyword_templates = self._get_keyword_templates(user_input)
        if keyword_templates:
            context_parts.append("# 関連テンプレート:")
            context_parts.append(keyword_templates)
        
        # 現在の状態
        context_parts.append(f"# 現在の状態:")
        context_parts.append(self.state.get_summary())
        
        # 指示
        context_parts.append(f"""
# 指示:
ユーザー入力: "{user_input}"
上記の制約とテンプレートを参考に、適切なPythonコードを生成してください。
重複実行禁止関数は必ず確認してください。
正しいimport: import genesis as gs
""")
        
        return '\n'.join(context_parts)
    
    def _get_keyword_templates(self, user_input: str) -> str:
        """キーワードに基づくテンプレート取得"""
        try:
            # genesis_templates.pyから検索
            keywords = self._extract_keywords(user_input)
            print(f"🔍 検索キーワード: {keywords}")
            
            # 基本的なマッピング
            template_mapping = {
                '球': 'sphere = scene.add_entity(gs.morphs.Sphere(radius=0.2, pos=(0, 0, 1)))',
                'アーム': 'robot = scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))',
                'ロボット': 'robot = scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))',
                '地面': 'plane = scene.add_entity(gs.morphs.Plane())',
                'ビルド': 'scene.build()',
                'シミュレーション': 'for i in range(100): scene.step()',
                '実行': 'scene.run(duration=5.0)'
            }
            
            templates = []
            for keyword in keywords:
                if keyword in template_mapping:
                    templates.append(f"# {keyword}: {template_mapping[keyword]}")
            
            return '\n'.join(templates) if templates else ""
            
        except Exception as e:
            print(f"⚠️ テンプレート取得エラー: {e}")
            return ""
    
    def _extract_keywords(self, text: str) -> List[str]:
        """テキストからキーワード抽出"""
        keywords = []
        keyword_patterns = ['球', 'アーム', 'ロボット', '地面', 'ビルド', 'シミュレーション', '実行']
        
        for pattern in keyword_patterns:
            if pattern in text:
                keywords.append(pattern)
        
        return keywords
    
    def execute_gemini_code(self, gemini_output: str, user_input: str) -> Dict[str, Any]:
        """Gemini出力からコードを抽出して実行"""
        try:
            # 1. コード抽出
            python_code = self.code_extractor.extract_python_code(gemini_output)
            if not python_code:
                return {"success": False, "error": "No Python code found in Gemini output"}
            
            # Import修正
            python_code = python_code.replace('import genesis_sim as gs', 'import genesis as gs')
            python_code = python_code.replace('genesis_sim', 'genesis')
            
            print(f"🔍 抽出されたコード:\n{'=' * 50}\n{python_code}\n{'=' * 50}")
            
            # 2. 重複実行チェック
            if self._should_skip_execution(python_code):
                return {"success": True, "skipped": True, "message": "Code execution skipped (already executed)"}
            
            # 3. 実行
            print("🔄 Genesis コード実行中...")
            result = self._execute_code_safely(python_code)
            
            # 4. 状態更新
            self._update_state_after_execution(python_code)
            
            # 5. 会話履歴に追加
            self.conversation_history.add_turn(user_input, python_code, result)
            
            return result
            
        except Exception as e:
            self.state.error_count += 1
            self.logger.error(f"Code execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _should_skip_execution(self, code: str) -> bool:
        """実行スキップが必要か判定"""
        if 'gs.init(' in code and self.state.is_initialized:
            print("⚠️ Genesis already initialized - skipping init")
            return True
        elif 'scene.build()' in code and self.state.is_built:
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
    
    def _update_state_after_execution(self, code: str):
        """実行後の状態更新"""
        if 'gs.init(' in code:
            self.state.is_initialized = True
            print("✅ Genesis initialized")
            
        if 'gs.Scene(' in code or 'scene =' in code:
            self.state.has_scene = True
            print("✅ Scene created")
            
        if '.build()' in code:
            self.state.is_built = True
            print("✅ Scene built")
    
    def get_state_summary(self) -> str:
        """現在の状態サマリを取得"""
        return self.state.get_summary()