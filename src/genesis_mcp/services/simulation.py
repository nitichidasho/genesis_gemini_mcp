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
    """会話履歴管理 - 簡素化版"""
    
    def __init__(self):
        self.turns = []  # 会話ターン履歴
        self.failed_code_parts = []  # 失敗したコード部分
        self.current_session_code = ""  # 現在のセッションで試行中のコード
        
    def add_turn(self, user_input: str, generated_code: str, execution_result: Dict[str, Any]):
        """ターン追加 - 簡素化版"""
        turn = {
            'turn_number': len(self.turns) + 1,
            'user_input': user_input,
            'generated_code': generated_code,
            'execution_result': execution_result,
            'timestamp': time.time(),
            'executed_successfully': execution_result.get('success', False)
        }
        self.turns.append(turn)
        
        # 失敗時のみ記録
        if not execution_result.get('success'):
            self.failed_code_parts.append({
                'turn': turn['turn_number'],
                'code': generated_code,
                'error': execution_result.get('error', 'Unknown error'),
                'user_input': user_input
            })
            self.current_session_code = generated_code
        else:
            self.current_session_code = ""
    
    def get_context_for_gemini(self, genesis_state: 'LogBasedGenesisState') -> str:
        """Gemini用のコンテキスト生成 - stdout状態ベース"""
        if not self.turns:
            return "# 初回実行です。完全なGenesisコードを生成してください。"
        
        context_parts = []
        
        # 実行済み段階の情報
        completed_stages = genesis_state.get_completed_stages()
        next_stage = genesis_state.get_next_required_stage()
        
        if completed_stages:
            context_parts.append("# ✅ 既に実行完了している段階:")
            for stage in completed_stages:
                stage_description = {
                    'init': 'Genesis初期化 (gs.init)',
                    'scene_creation': 'シーン作成 (gs.Scene)',
                    'entity_addition': 'エンティティ追加 (scene.add_entity)',
                    'scene_build': 'シーンビルド (scene.build)',
                    'simulation': 'シミュレーション実行 (scene.step)'
                }.get(stage, stage)
                context_parts.append(f"# ✅ {stage_description}")
            
            context_parts.append("# ⚠️ 上記の段階は既に実行済みです。重複して実行しないでください。")
        
        # 最新のエラー情報
        if self.failed_code_parts:
            latest_failure = self.failed_code_parts[-1]
            context_parts.append(f"# ❌ 前回失敗したコード (エラー: {latest_failure['error']}):")
            context_parts.append(f"# ユーザー要求: {latest_failure['user_input']}")
            context_parts.append("```python")
            context_parts.append(latest_failure['code'])
            context_parts.append("```")
        
        # 次のステップ指示
        context_parts.append(f"# 🎯 次に実行すべき段階: {next_stage}")
        
        # 継続実行指示
        if completed_stages:
            context_parts.append("""
# 🔧 【重要】継続実行指示:
# 1. 上記の完了済み段階は絶対に重複実行しないでください
# 2. 既に実行済みの処理 (init, scene作成など) は出力しないでください  
# 3. 次に必要な段階から開始するコードを生成してください
# 4. 前回のエラーがある場合は修正してください
""")
        else:
            context_parts.append("# 🔧 指示: 完全な新規コードを生成してください")
        
        return '\n'.join(context_parts)


class GenesisConstraints:
    """Genesis制約とガイドライン"""
    
    @staticmethod
    def get_basic_template() -> str:
        """基本テンプレート（常に提供）- 低解像度設定"""
        return """
# Genesis基本テンプレート - 低解像度設定
import genesis as gs

# 1. 初期化（1回のみ実行可能）
gs.init(backend=gs.gpu)  # またはgs.cpu

# 2. シーン作成 - 低解像度でパフォーマンス重視
scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        resolution=(800, 600),             # VNCサーバーと同じ解像度
        max_FPS=30                         # フレームレート制限
    ),
    show_viewer=True
)

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

# �️ ビューワー設定推奨事項:
# ✅ resolution=(800, 600) でVNCサーバーと同じ解像度によりパフォーマンス向上
# ✅ max_FPS=30 でフレームレート制限により安定動作
"""
    
    @staticmethod
    def get_forbidden_apis() -> str:
        """禁止APIリスト - Geminiが間違いやすいAPI"""
        return """
# 🚫 絶対に使用禁止のAPI（存在しないメソッド）:
# ❌ franka.get_motors_dof_indices() - 存在しません
# ❌ franka.set_motor_pid() - 存在しません  
# ❌ franka.set_joint_target_positions() - 存在しません
# ❌ robot.get_motors_dof_indices() - 存在しません
# ❌ entity.robot - 存在しません

# 🚫 存在しないエンティティAPI:
# ❌ gs.morphs.Cube() - 存在しません！
# ❌ gs.morphs.Rectangle() - 存在しません
# ❌ gs.morphs.Cuboid() - 存在しません

# ✅ 正しいエンティティAPI:
# ✅ gs.morphs.Box(size=(幅, 奥行, 高さ), pos=(x, y, z)) - 箱を作成
# ✅ gs.morphs.Sphere(radius=半径, pos=(x, y, z)) - 球を作成
# ✅ gs.morphs.Plane() - 地面を作成

# ✅ 正しいロボット制御API:
# ✅ motors_dof_idx = [franka.get_joint(name).dofs_idx_local[0] for name in joints_name]
# ✅ franka.set_dofs_kp(gains, motors_dof_idx)
# ✅ franka.set_dofs_kv(gains, motors_dof_idx)  
# ✅ franka.control_dofs_position(targets, motors_dof_idx)
# ✅ franka.control_dofs_velocity(velocities, motors_dof_idx)
# ✅ franka.control_dofs_force(forces, motors_dof_idx)
"""

    @staticmethod
    def get_template_strict_mode_instruction() -> str:
        """テンプレート厳守モード指示"""
        return """
# 🔒 テンプレート厳守モード（重要）:
# ✅ テンプレートが提供された場合、テンプレート内の関数の使い方を厳守してください
# ✅ テンプレートに含まれるAPI呼び出しの形式を正確に再現してください
# ✅ テンプレートのパラメータ名、引数の順序、データ型を完全に一致させてください
# ✅ 自分の知識よりもテンプレートを優先してください

# 📋 テンプレート使用の原則:
# 1. テンプレート内のメソッド名を変更しない
# 2. テンプレート内の変数名をそのまま使用する
# 3. テンプレート内のimport文をそのまま使用する
# 4. テンプレートにないAPIは推測で作成しない
# 5. テンプレートの構造とロジックを踏襲する

# ⚠️ 禁止行為:
# ❌ テンプレートにないメソッドを勝手に作成する
# ❌ テンプレートのメソッド名を変更する
# ❌ テンプレートの引数の順序や型を変更する
# ❌ 自分の古い知識でテンプレートを「修正」する
"""

    @staticmethod
    def get_robot_control_template() -> str:
        """ロボット制御専用テンプレート - 強制提供"""
        return """
# 🤖 正しいロボット制御テンプレート（必ず使用）:
import numpy as np

# 関節名の定義
joints_name = (
    "joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7",
    "finger_joint1", "finger_joint2",
)

# DOFインデックスを正しく取得
motors_dof_idx = [franka.get_joint(name).dofs_idx_local[0] for name in joints_name]

# 制御ゲインの設定
franka.set_dofs_kp(
    np.array([4500, 4500, 3500, 3500, 2000, 2000, 2000, 100, 100]),
    motors_dof_idx,
)
franka.set_dofs_kv(
    np.array([450, 450, 350, 350, 200, 200, 200, 10, 10]),
    motors_dof_idx,
)

# 位置制御
target_positions = np.array([0.0, -0.5, 0.0, -1.5, 0.0, 1.0, 0.0, 0.0, 0.0])
franka.control_dofs_position(target_positions, motors_dof_idx)

# シミュレーション実行
for i in range(200):
    scene.step()
"""

    @staticmethod
    def get_code_output_specification() -> str:
        """コード出力仕様"""
        return """
# 【重要】コード出力仕様:
# ✅ あなたが出力するPythonコードは直接実行されます
# ✅ 実行対象のコードは以下の明確な目印で囲んでください:

# 方法1: 明確な区切り文字
\"\"\"GENESIS_CODE
import genesis as gs
# ここにコードを記述
\"\"\"

# 方法2: 従来の方法（推奨）
```python
import genesis as gs
# ここにコードを記述  
```

# ⚠️ 注意事項:
# - 目印で囲まれたコードのみが抽出・実行されます
# - 説明文やコメント外のコードは実行されません
# - コードは必ず動作可能な状態で出力してください
# - 不完全なコード例（...など）は使用しないでください
"""


class LogBasedGenesisState:
    """stdout出力ベースのGenesis状態管理"""
    
    def __init__(self):
        self.stages_completed = {
            'init': False,
            'scene_creation': False,
            'entity_addition': False,
            'scene_build': False,
            'simulation': False
        }
        self.last_logs = []
        self.error_count = 0
        
    def update_from_logs(self, logs: List[str]):
        """ログから実行完了状態を更新"""
        self.last_logs = logs
        
        # ログから実際に完了した段階を検出
        for log in logs:
            if '🚀 Genesis initialized.' in log:
                self.stages_completed['init'] = True
                print("📋 ログから検出: Genesis初期化完了")
            elif 'Scene <' in log and '> created.' in log:
                self.stages_completed['scene_creation'] = True
                print("📋 ログから検出: シーン作成完了")
            elif 'Adding <gs.RigidEntity>' in log:
                self.stages_completed['entity_addition'] = True
                print("📋 ログから検出: エンティティ追加完了")
            elif 'Building scene <' in log:
                # シーンビルド開始は検出するが、完了は別途チェック
                pass
            elif 'Viewer created.' in log or ('Compiling simulation kernels...' in log):
                self.stages_completed['scene_build'] = True
                print("📋 ログから検出: シーンビルド完了")
            elif 'Running at' in log and 'FPS' in log:
                self.stages_completed['simulation'] = True
                print("📋 ログから検出: シミュレーション実行完了")
    
    def get_summary(self) -> str:
        """状態サマリを取得"""
        return f"""
📊 Genesis Status (stdout-based):
{'✅' if self.stages_completed['init'] else '❌'} Genesis Initialized
{'✅' if self.stages_completed['scene_creation'] else '❌'} Scene Created  
{'✅' if self.stages_completed['entity_addition'] else '❌'} Entities Added
{'✅' if self.stages_completed['scene_build'] else '❌'} Scene Built
{'✅' if self.stages_completed['simulation'] else '❌'} Simulation Running
⚠️ Errors: {self.error_count}
"""

    def is_stage_completed(self, stage: str) -> bool:
        """特定の段階が完了しているかチェック"""
        return self.stages_completed.get(stage, False)
    
    def get_completed_stages(self) -> List[str]:
        """完了した段階のリストを取得"""
        return [stage for stage, completed in self.stages_completed.items() if completed]
    
    def get_next_required_stage(self) -> str:
        """次に必要な段階を取得"""
        stage_order = ['init', 'scene_creation', 'entity_addition', 'scene_build', 'simulation']
        for stage in stage_order:
            if not self.stages_completed[stage]:
                return stage
        return 'simulation'  # 全部完了していたらシミュレーション継続


class CodeExtractor:
    """Gemini出力からPythonコードを抽出 - 強化版"""
    
    @staticmethod
    def extract_python_code(gemini_output: str) -> str:
        """Gemini出力からPythonコードを抽出 - 複数の目印をサポート"""
        
        # 方法1: GENESIS_CODE目印での抽出
        genesis_code_pattern = r'"""GENESIS_CODE\s*\n(.*?)\s*"""'
        matches = re.findall(genesis_code_pattern, gemini_output, re.DOTALL)
        if matches:
            print("🎯 GENESIS_CODE目印でコード抽出")
            return matches[0].strip()
        
        # 方法2: 従来のpythonコードブロック抽出
        code_block_pattern = r'```python\s*\n(.*?)```'
        matches = re.findall(code_block_pattern, gemini_output, re.DOTALL)
        if matches:
            print("🎯 ```python```ブロックでコード抽出")
            return matches[0].strip()
        
        # 方法3: 一般的なコードブロック
        general_code_pattern = r'```\s*\n(.*?)```'
        matches = re.findall(general_code_pattern, gemini_output, re.DOTALL)
        if matches:
            # Pythonコードっぽいものを選択
            for match in matches:
                if 'import genesis' in match or 'gs.' in match or 'scene' in match:
                    print("🎯 一般コードブロックでコード抽出")
                    return match.strip()
        
        # 方法4: フォールバック - import文から始まる行を探す
        print("🎯 フォールバック: import文ベースでコード抽出")
        return CodeExtractor._extract_code_by_imports(gemini_output)
    
    @staticmethod
    def _extract_code_by_imports(gemini_output: str) -> str:
        """import文ベースのコード抽出（フォールバック）"""
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
        self.state = LogBasedGenesisState()
        self.conversation_history = ConversationHistory()
        self.constraints = GenesisConstraints()
        self.code_extractor = CodeExtractor()
        self.scene = None
        self.entities = {}
        
        # VNC環境設定
        self._setup_vnc_environment()
        
    def reset_scene_on_error(self):
        """エラー発生時のシーンリセット"""
        print("🔄 エラー検出 - シーンリセット実行中...")
        
        # 状態リセット（初期化は保持）
        if self.state.is_initialized:
            self.state.has_scene = False
            self.state.is_built = False
            self.state.entities.clear()
            
            print("✅ シーン状態をリセットしました")
            print("💡 新しいシーンを作成できます: scene = gs.Scene(show_viewer=True)")
        else:
            print("⚠️ Genesis が初期化されていません")
        
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
    
    def is_vnc_environment(self) -> bool:
        """VNC環境かどうかを判定"""
        import os
        display = os.environ.get('DISPLAY', '')
        is_vnc = display.startswith(':') and display != ':0'
        
        # デバッグ情報
        print(f"🔍 環境検出: DISPLAY='{display}', VNC判定={is_vnc}")
        
        return is_vnc
    
    def get_enhanced_context_for_gemini(self, user_input: str) -> str:
        """Gemini用の強化されたコンテキスト生成 - 禁止API対応版"""
        
        # 基本情報
        context_parts = []
        context_parts.append("# Genesis World コード生成タスク")
        context_parts.append(self.constraints.get_basic_template())
        context_parts.append(self.constraints.get_constraints_info())
        
        # テンプレート厳守モード指示（重要！）
        context_parts.append(self.constraints.get_template_strict_mode_instruction())
        
        # 禁止API情報（重要！）
        context_parts.append(self.constraints.get_forbidden_apis())
        
        # ロボット制御が含まれる場合は専用テンプレートを強制提供
        keywords = self._extract_keywords(user_input)
        if any(keyword in ['ロボット', '関節', '位置制御', '速度制御', '力制御'] for keyword in keywords):
            context_parts.append("# 🤖 ロボット制御専用テンプレート（必ず使用）:")
            context_parts.append(self.constraints.get_robot_control_template())
        
        context_parts.append(self.constraints.get_code_output_specification())
        
        # 継続実行コンテキスト（stdout状態ベース）
        continuation_context = self.conversation_history.get_context_for_gemini(self.state)
        context_parts.append(continuation_context)
        
        # 現在の実際の状態（stdout解析ベース）
        current_state = f"""
# 現在のGenesisシステム状態（stdout解析ベース）:
{self.state.get_summary()}
# 注意: 上記の状態はGenesis実行時のstdout出力から検出されています。
# エラーが発生しても、実際に完了した処理は正確に反映されています。
"""
        context_parts.append(current_state)
        
        # キーワード検索によるテンプレート取得
        keyword_templates = self._get_keyword_templates(user_input)
        template_provided = bool(keyword_templates)
        
        if keyword_templates:
            context_parts.append("# 📚 関連テンプレート（厳守対象）:")
            context_parts.append(keyword_templates)
            context_parts.append("""
# 🔒 テンプレート厳守指示:
# 上記テンプレートが提供されています。テンプレート内のAPI使用法を厳守してください。
# テンプレートにあるメソッド名、引数、変数名を正確に使用してください。
# 自分の知識でテンプレートを「改良」したり「修正」したりしないでください。
""")
        
        # 継続実行の具体的指示
        if self.conversation_history.turns:
            last_turn = self.conversation_history.turns[-1]
            if not last_turn.get('executed_successfully', False):
                context_parts.append(f"""
# 🔧 継続実行指示:
# 前回のエラーを修正して、実行済みコードの【続き】のみを生成してください
# ⚠️ import文やgs.init()など、既に実行済みの部分は出力しないでください
# ✅ 現在の段階から必要な修正を加えて続行してください
# 🚫 禁止APIは絶対に使用しないでください
""")
        
        # 指示
        template_instruction = ""
        if template_provided:
            template_instruction = """
🔒 【テンプレート厳守必須】:
提供されたテンプレートのAPI使用法を厳密に守ってください。
テンプレート内のメソッド名、引数、データ型を一文字も変更しないでください。
"""
        
        context_parts.append(f"""
# 指示:
ユーザー入力: "{user_input}"
上記の全ての情報を考慮して、適切なGenesisコードを生成してください。
特にロボット制御の場合は、禁止APIを避けて正しいテンプレートを使用してください。
{template_instruction}
""")
        
        return '\n'.join(context_parts)
    
    def _get_keyword_templates(self, user_input: str) -> str:
        """キーワードに基づくテンプレート取得 - genesis_templates.py統合"""
        print(f"🔍 テンプレート検索開始: user_input='{user_input}'")
        
        try:
            # genesis_templates.pyから検索
            keywords = self._extract_keywords(user_input)
            print(f"🔍 検索キーワード: {keywords}")
            
            if not keywords:
                print("⚠️ キーワードが抽出されませんでした")
                return ""
            
            # GenesisTemplateLibraryを使用
            try:
                import sys
                import os
                template_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                print(f"🔍 テンプレートライブラリパス: {template_path}")
                
                if template_path not in sys.path:
                    sys.path.append(template_path)
                
                from genesis_templates import GenesisTemplateLibrary
                print("✅ GenesisTemplateLibrary インポート成功")
                
                template_lib = GenesisTemplateLibrary()
                matches = template_lib.get_template_by_keywords(keywords)
                
                if matches:
                    templates = []
                    print(f"📚 関連テンプレート: {len(matches)} 件")
                    for i, match in enumerate(matches[:3]):  # 上位3件
                        print(f"  - テンプレート{i+1}: {match['category']}.{match['name']}")
                        templates.append(f"# {match['category']}.{match['name']}:")
                        templates.append(match['code'][:200] + "...")  # 先頭200文字
                    return '\n'.join(templates)
                else:
                    print("📚 関連テンプレート: 0 件 (GenesisTemplateLibrary)")
                    
            except ImportError as ie:
                print(f"⚠️ genesis_templates.py ImportError: {ie}")
                print("⚠️ フォールバックマッピングを使用します")
            except Exception as te:
                print(f"⚠️ テンプレートライブラリエラー: {te}")
            
            # フォールバック：基本的なマッピング
            print("🔍 フォールバックマッピングを使用")
            template_mapping = {
                '球': 'sphere = scene.add_entity(gs.morphs.Sphere(radius=0.2, pos=(0, 0, 1)))',
                'アーム': 'robot = scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))',
                'ロボット': 'robot = scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))',
                '地面': 'plane = scene.add_entity(gs.morphs.Plane())',
                'ビルド': 'scene.build()',
                'シミュレーション': 'for i in range(100): scene.step()',
                '実行': 'scene.run(duration=5.0)',
                '箱': '''# ✅ 正しい箱の作成方法
box = scene.add_entity(gs.morphs.Box(size=(1.0, 1.0, 1.0), pos=(0, 0, 0.5)))
# ⚠️ 注意: gs.morphs.Cube は存在しません！必ず gs.morphs.Box を使用してください
# ❌ 間違い: gs.morphs.Cube() 
# ✅ 正しい: gs.morphs.Box(size=(幅, 奥行, 高さ), pos=(x, y, z))'''
            }
            
            templates = []
            for keyword in keywords:
                if keyword in template_mapping:
                    templates.append(f"# {keyword}: {template_mapping[keyword]}")
                    print(f"  - フォールバック適用: {keyword}")
            
            result = '\n'.join(templates) if templates else ""
            print(f"📚 最終テンプレート結果: {len(result)} 文字")
            return result
            
        except Exception as e:
            print(f"⚠️ テンプレート取得エラー: {e}")
            return ""
    
    def _extract_keywords(self, text: str) -> List[str]:
        """テキストからキーワード抽出 - 強化版"""
        print(f"🔍 キーワード抽出開始: text='{text}'")
        keywords = []
        
        # 基本キーワードパターン
        basic_patterns = ['球', 'アーム', 'ロボット', '地面', 'ビルド', 'シミュレーション', '実行', '関節', '位置制御', '速度制御', '力制御', '箱']
        
        # 拡張キーワードパターン  
        extended_patterns = {
            '球': ['sphere', 'ボール', 'ball'],
            'アーム': ['arm', 'ロボットアーム', 'robot arm', 'franka'],
            'ロボット': ['robot', 'franka', 'panda'],
            '地面': ['plane', 'ground', 'floor'],
            'ビルド': ['build', '構築', 'construct'],
            'シミュレーション': ['simulation', 'sim', 'step'],
            '実行': ['run', 'execute', 'start'],
            '箱': ['box', 'cube', 'ボックス'],
            '円柱': ['cylinder', 'シリンダー'],
            '重力': ['gravity', 'drop', '落下'],
            '衝突': ['collision', 'contact', '接触'],
            '関節': ['joint', 'ジョイント', 'dof', '自由度'],
            '位置制御': ['position control', 'control_dofs_position', '位置', 'position'],
            '速度制御': ['velocity control', 'control_dofs_velocity', '速度', 'velocity'],
            '力制御': ['force control', 'control_dofs_force', '力', 'force', 'torque', 'トルク'],
            '材質': ['material', 'マテリアル'],
            '摩擦': ['friction'],
            '弾性': ['elastic', 'bouncy', '反発'],
            'カメラ': ['camera', 'viewer'],
            '照明': ['light', 'lighting'],
            'センサー': ['sensor', 'lidar', 'imu']
        }
        
        text_lower = text.lower()
        print(f"🔍 小文字変換後: '{text_lower}'")
        
        # 基本パターンチェック
        found_basic = []
        for pattern in basic_patterns:
            if pattern in text:
                keywords.append(pattern)
                found_basic.append(pattern)
        
        if found_basic:
            print(f"✅ 基本パターン発見: {found_basic}")
        
        # 拡張パターンチェック
        found_extended = []
        for main_keyword, synonyms in extended_patterns.items():
            if main_keyword not in keywords:  # 重複回避
                for synonym in synonyms:
                    if synonym in text_lower:
                        keywords.append(main_keyword)
                        found_extended.append(f"{main_keyword}({synonym})")
                        break
        
        if found_extended:
            print(f"✅ 拡張パターン発見: {found_extended}")
        
        print(f"🔍 最終キーワード: {keywords}")
        return keywords
    
    def execute_gemini_code(self, gemini_output: str, user_input: str) -> Dict[str, Any]:
        """Gemini出力からコードを抽出して実行 - 改善されたUI表示"""
        print("=" * 80)
        print("🤖 GEMINI 生成完了")
        print("=" * 80)
        
        try:
            # 1. Gemini出力の表示
            print("📝 Geminiの完全な回答:")
            print("-" * 60)
            print(gemini_output)
            print("-" * 60)
            
            # 2. コード抽出
            python_code = self.code_extractor.extract_python_code(gemini_output)
            if not python_code:
                error_msg = "Gemini出力からPythonコードが見つかりません"
                print(f"❌ エラー: {error_msg}")
                return {"success": False, "error": error_msg}
            
            # Import修正
            python_code = python_code.replace('import genesis_sim as gs', 'import genesis as gs')
            python_code = python_code.replace('genesis_sim', 'genesis')
            
            print("\n🔍 抽出されたPythonコード:")
            print("=" * 60)
            print(python_code)
            print("=" * 60)
            
            # 3. 重複実行チェック
            if self._should_skip_execution(python_code):
                skip_msg = "重複実行のためスキップされました"
                print(f"⏭️ {skip_msg}")
                return {"success": True, "skipped": True, "message": skip_msg}
            
            # 4. 実行開始
            print("\n🔄 Genesis コード実行開始...")
            print("=" * 60)
            result = self._execute_code_safely(python_code)
            print("=" * 60)
            
            # 5. 実行結果表示
            if result.get('success'):
                print("✅ Genesis コード実行成功!")
                if result.get('execution_time'):
                    print(f"⏱️  実行時間: {result['execution_time']:.2f}秒")
                if result.get('execution_mode'):
                    print(f"🖥️  実行モード: {result['execution_mode']}")
                if result.get('entities_created'):
                    print(f"🎯 作成されたエンティティ: {result['entities_created']}")
                
                # 6. stdout解析による状態更新（成功時）
                if result.get('logs'):
                    self.state.update_from_logs(result['logs'])
                    print("✅ stdout解析による状態更新完了")
                    
            else:
                print("❌ Genesis コード実行失敗!")
                print(f"💥 エラー: {result.get('error', 'Unknown error')}")
                
                # 6. stdout解析による状態更新（失敗時も実行）
                if result.get('logs'):
                    self.state.update_from_logs(result['logs'])
                    print("✅ stdout解析による状態更新完了（部分成功検出）")
                
                # エラーカウント増加
                self.state.error_count += 1
                
                # エラーが重大な場合の処理
                error_msg = result.get('error', '')
                if any(keyword in error_msg for keyword in ['add_entity', 'build', 'Scene']):
                    print("🔄 シーン関連エラー検出")
            
            # 7. 会話履歴に追加
            self.conversation_history.add_turn(user_input, python_code, result)
            
            return result
            
        except Exception as e:
            self.state.error_count += 1
            error_msg = f"予期しないエラー: {str(e)}"
            print(f"❌ {error_msg}")
            self.logger.error(f"Code execution failed: {e}")
            return {"success": False, "error": error_msg}
    
    def _should_skip_execution(self, code: str) -> bool:
        """実行スキップが必要か判定 - stdout状態ベース"""
        if 'gs.init(' in code and self.state.is_stage_completed('init'):
            print("⚠️ Genesis already initialized (detected from logs) - skipping init")
            return True
        elif 'scene.build()' in code and self.state.is_stage_completed('scene_build'):
            print("⚠️ Scene already built (detected from logs) - skipping build")
            return True
        return False
    
    def _execute_code_safely(self, code: str) -> Dict[str, Any]:
        """コードを安全に実行 - VNC環境対応版"""
        start_time = time.time()
        
        # 環境検出とデバッグ
        is_vnc = self.is_vnc_environment()
        
        # VNC環境の場合のみ出力キャプチャを使用
        if is_vnc:
            log_capture = StringIO()
            original_stdout = sys.stdout
            use_capture = True
            execution_mode = "VNC安全モード"
            print(f"🔧 VNC環境検出 - stdout キャプチャを使用します")
        else:
            use_capture = False
            execution_mode = "リアルタイムモード"
            print(f"🔧 ローカル環境検出 - リアルタイム出力を使用します")
        
        # 実行環境準備
        local_vars = {
            'gs': gs if GENESIS_AVAILABLE else None,
            'scene': self.scene,
            **self.entities
        }
        
        try:
            print(f"🚀 コード実行開始... ({execution_mode})")
            
            if use_capture:
                print("� stdout キャプチャ開始")
                sys.stdout = log_capture
            
            # 段階的実行
            result = self._execute_code_by_stages(code, local_vars)
            
            if use_capture:
                # VNC環境: キャプチャされたログを取得
                sys.stdout = original_stdout
                logs = log_capture.getvalue().splitlines()
                print("📋 stdout キャプチャ終了")
                result['logs'] = logs
            else:
                # ローカル環境: リアルタイム出力
                result['logs'] = []  # リアルタイム出力のためログは空
            
            # 実行時間を追加
            result['execution_time'] = time.time() - start_time
            result['execution_mode'] = execution_mode
            
            if result.get('success'):
                print("✨ コード実行完了")
                
                # 重要なオブジェクトを保存
                if 'scene' in local_vars and local_vars['scene'] is not None:
                    self.scene = local_vars['scene']
                    print("💾 Scene object saved")
                
                # エンティティを保存
                entity_count = 0
                for key, value in local_vars.items():
                    if key not in ['gs', 'scene'] and hasattr(value, '__class__'):
                        self.entities[key] = value
                        entity_count += 1
                
                result['entities_created'] = entity_count
            else:
                print(f"💥 段階的実行でエラー発生: {result.get('error', 'Unknown error')}")
                if result.get('partial_success'):
                    print(f"✅ 部分的成功: {result.get('successful_stages', [])}")
            
            return result
            
        except Exception as e:
            if use_capture:
                sys.stdout = original_stdout
                print(f"📋 例外発生によりstdout復元: {type(e).__name__}")
                
            execution_time = time.time() - start_time
            error_msg = str(e)
            print(f"💥 実行エラー ({execution_mode}): {error_msg}")
            return {
                "success": False, 
                "error": error_msg,
                "execution_time": execution_time,
                "execution_mode": execution_mode
            }
        finally:
            # 安全のため、stdoutを確実に復元
            if use_capture:
                try:
                    sys.stdout = original_stdout
                    print("🔧 finally ブロックでstdout復元完了")
                except:
                    pass
    
    def get_state_summary(self) -> str:
        """現在の状態サマリを取得"""
        return self.state.get_summary()
    
    def _execute_code_by_stages(self, code: str, local_vars: dict) -> Dict[str, Any]:
        """コードを単純実行 - stdout解析で状態管理"""
        try:
            # 単純にコード全体を実行
            exec(code, local_vars, local_vars)
            
            return {
                "success": True,
                "message": "Code executed successfully"
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ コード実行でエラー: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg
            }