# Genesis MCP Server

🚀 **AI駆動の物理シミュレーション** - Genesis World をGemini AIと統合したModel Context Protocol (MCP) サーバー

Genesis WorldとGoogle Gemini AIを組み合わせ、自然言語から物理シミュレーションコードを生成。VNC機能により、SSH/リモート環境でも3D表示を実現します。

---

## ✨ 主な特徴

🧠 **Gemini AI統合**
- 自然言語からGenesis Worldコードを自動生成
- 物理シミュレーション特化のテンプレートシステム
- インテリジェントなコード補完と最適化

🖥️ **VNC最適化表示**
- SSH環境でGenesis World 3Dビューアーをリアルタイム表示
- 低遅延のx11vnc最適化設定（800x600@15fps）
- Windows/Mac/LinuxのVNCクライアント対応

⚡ **高性能アーキテクチャ**
- Model Context Protocol (MCP) による標準化された通信
- 非同期処理によるレスポンス向上
- UV高速パッケージ管理とクリーンな仮想環境

🎯 **開発者体験**
- ワンコマンド環境セットアップ
- 統合テストとデバッグツール

---

## 🚀 クイックスタート

### 📋 前提条件

- **Python**: 3.11以上
- **OS**: Linux (推奨) / macOS / Windows (WSL2)
- **GPU**: CUDA対応GPU (推奨、CPUでも動作)
- **Gemini API**: Google AI Studio APIキー

### 1️⃣ プロジェクト取得

```bash
git clone https://github.com/dustland/genesis-mcp.git
cd genesis-mcp
```

### 2️⃣ 環境設定

```bash
# Gemini APIキーを設定
cp .env.example .env

# .envファイルを編集してGEMINI_API_KEY=your_api_key_here を設定
# または、setup.pyを使って設定
python setup.py --gemini-key YOUR_KEY  # APIキー設定

# 自動セットアップ
python setup.py --all

# 環境チェック
python setup.py --check
```

### 3️⃣ VNC環境セットアップ（リモート表示用）

```bash
# VNC環境構築
python start_vnc.py --start

# VNC接続確認
python start_vnc.py --status

# 接続: VNCクライアントで localhost:5900
```

### 4️⃣ 実行

```bash
# 仮想環境アクティベート
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# インタラクティブモード（推奨）
python genesis_client.py

# デモ実行
python genesis_client.py --demo

# MCPサーバー起動
python genesis_server.py
```

---

## 🎮 使用例

### 基本的な使用方法

```bash
$ python genesis_client.py
🤖 Genesis MCP クライアント起動
📝 シミュレーション内容を入力: 赤い球体が3つ落下するシミュレーション

🧠 Gemini AIでコード生成中...
🔄 Genesis シミュレーション実行中...
✅ シミュレーション完了 - VNCで3D表示を確認してください
```

### デモモード

```bash
$ python genesis_client.py --demo
🎪 Genesis MCP デモ実行

📺 デモ 1/3: 赤い球体が落下するシミュレーション
📺 デモ 2/3: 2つの箱が接触するシミュレーション  
📺 デモ 3/3: 球体が箱の上を転がるシミュレーション

✅ 全デモ完了
```

### 生成されるコード例

**入力**: "青い箱と赤い球が衝突するシミュレーション"

**Gemini AI生成コード**:
```python
import genesis as gs

# 初期化（GPU使用）
gs.init(backend=gs.gpu)

# シーン作成（VNC最適化）
scene = gs.Scene(
    viewer_options=gs.options.ViewerOptions(
        resolution=(800, 600),
        max_FPS=15,
        camera_pos=(3.0, 2.0, 2.0)
    ),
    show_viewer=True
)

# 地面
plane = scene.add_entity(gs.morphs.Plane())

# 青い箱
box_material = gs.materials.Rigid(color=(0.0, 0.0, 1.0))
box = scene.add_entity(
    gs.morphs.Box(size=(1, 1, 1)),
    pos=(0, 0, 2),
    material=box_material
)

# 赤い球
sphere_material = gs.materials.Rigid(color=(1.0, 0.0, 0.0))
sphere = scene.add_entity(
    gs.morphs.Sphere(radius=0.5),
    pos=(2, 0, 4),
    material=sphere_material
)

# シーンビルド
scene.build()

# 物理シミュレーション実行
for i in range(1000):
    scene.step()
```

---

## 📂 プロジェクト構造

```
genesis-mcp/
├── 🔧 コアファイル
│   ├── genesis_client.py        # メインクライアント
│   ├── genesis_server.py        # MCPサーバー
│   ├── genesis_templates.py     # AIテンプレートシステム
│   ├── setup.py                 # 統合セットアップ
│   └── start_vnc.py            # VNC環境管理
│
├── 📦 パッケージ
│   ├── src/genesis_mcp/
│   │   ├── models.py           # データモデル
│   │   └── services/
│   │       ├── simulation.py   # シミュレーション制御
│   │       └── gemini_service.py # Gemini AI統合
│   │
├── ⚙️ 設定ファイル
│   ├── pyproject.toml          # パッケージ設定
│   ├── .env.example            # 環境変数テンプレート
│   └── uv.lock                 # 依存関係ロック
│
├── � ドキュメント
│   ├── docs/                   # 詳細ドキュメント
│   ├── VNC_OPTIMIZATION_GUIDE.md # VNC最適化ガイド
│   └── USAGE_GUIDE.md          # 使用方法詳細
│
└── 🧪 テスト
    └── tests/
        ├── integration_test.py  # 統合テスト
        └── test_services.py    # サービステスト
```

---

## � 設定オプション

### セットアップオプション

```bash
# 個別セットアップ
python setup.py --env      # 仮想環境のみ
python setup.py --vnc      # VNC環境のみ  
python setup.py --genesis  # Genesis Worldのみ
python setup.py --gemini-key YOUR_KEY  # APIキー設定

# 環境確認
python setup.py --check
```

### VNC設定

```bash
# VNC詳細操作
python start_vnc.py --start     # VNC開始
python start_vnc.py --stop      # VNC停止
python start_vnc.py --status    # 状況確認
python start_vnc.py --cleanup   # クリーンアップ
python start_vnc.py --display   # 利用可能ディスプレイ
```

### クライアントオプション

```bash
# 表示モード指定
python genesis_client.py --vnc     # VNC表示モード
python genesis_client.py --gui     # 直接GUI表示
python genesis_client.py --web     # Web表示（実験的）

# デバッグモード
python genesis_client.py --debug
python genesis_server.py --debug
```

---

## 🌐 VNC リモート接続

### Windows → Linux サーバー

```bash
# 1. サーバー側でVNC起動
python start_vnc.py --start

# 2. SSH接続でポートフォワーディング
ssh -L 5900:localhost:5900 user@your-server

# 3. WindowsのVNCクライアントで接続
# 接続先: localhost:5900
```

### 接続フロー

```
Windows PC (VNC Viewer)
    ↓ SSH Tunnel (Port 5900)
Linux Server (VNC Server)
    ↓ DISPLAY :1
Genesis World 3D Viewer (800x600@15fps)
    ↓ 最適化転送
Windows PC (リアルタイム3D表示)
```

---

## 🎛️ API リファレンス

### MCPサーバー ツール

#### `run_simulation`
Genesis Worldシミュレーションを実行

**パラメータ**:
- `code`: Pythonコード（Gemini生成またはカスタム）
- `description`: シミュレーション説明
- `options`: 実行オプション

#### `get_simulation_template`
テンプレートベースのコード生成

**パラメータ**:
- `keywords`: 検索キーワード
- `style`: テンプレートスタイル

### MCPサーバー リソース

#### `world_info://features`
Genesis World機能情報

#### `simulation_state://current`
現在のシミュレーション状態

---

## 🔍 トラブルシューティング

### VNC接続できない

```bash
# VNC再起動
python start_vnc.py --cleanup
python start_vnc.py --start

# ポート確認
netstat -tlnp | grep :5900

# ファイアウォール確認
sudo ufw allow 5900
```

### Genesis World表示されない

```bash
# DISPLAY設定確認
echo $DISPLAY

# X11テスト
export DISPLAY=:1
xclock

# Genesis Worldテスト
python -c "import genesis as gs; print('Genesis OK')"
```

### Gemini AI接続エラー

```bash
# APIキー確認
cat .env | grep GEMINI_API_KEY

# 接続テスト
python -c "
import os
import google.generativeai as genai
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
print('Gemini API接続OK')
"
```

### パフォーマンス問題

```bash
# GPU確認
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# VNC最適化確認
python start_vnc.py --status

# 解像度調整（pyproject.tomlで設定可能）
# resolution=(800, 600) → (640, 480) for better performance
```

---

## 🛠️ 開発

### 開発環境セットアップ

```bash
# 開発用依存関係インストール
uv pip install -e ".[dev]"

# テスト実行
python -m pytest tests/

# 統合テスト
python tests/integration_test.py

# コード品質チェック
black src/ tests/
isort src/ tests/
flake8 src/ tests/
```

### 新機能追加

1. **テンプレート追加**: `genesis_templates.py`にパターン追加
2. **AIプロンプト改善**: `src/genesis_mcp/services/gemini_service.py`を編集
3. **VNC最適化**: `start_vnc.py`のx11vncパラメータ調整

### プロファイリング

```bash
# パフォーマンス計測
python -m cProfile -o profile.stats genesis_client.py --demo

# メモリ使用量監視
python -m memory_profiler genesis_client.py
```

---

## � システム要件

### 最小要件
- **CPU**: Intel/AMD x64 または Apple Silicon
- **RAM**: 4GB以上
- **ストレージ**: 2GB以上
- **ネットワーク**: インターネット接続（Gemini API用）

### 推奨要件
- **CPU**: 4コア以上
- **RAM**: 8GB以上
- **GPU**: CUDA対応GPU（RTX系、GTX 1060以上）
- **ネットワーク**: 安定したブロードバンド接続

### 対応OS
- ✅ **Ubuntu** 20.04+ (推奨)
- ✅ **CentOS/RHEL** 8+
- ✅ **macOS** 12+
- ⚠️ **Windows** (WSL2経由で制限付き対応)

---

## 🤝 コントリビューション

### 貢献方法

1. **フォーク**: このリポジトリをフォーク
2. **ブランチ**: 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. **コミット**: 変更をコミット (`git commit -m 'Add amazing feature'`)
4. **プッシュ**: ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. **プルリクエスト**: プルリクエストを作成

### 開発ガイドライン

- **コード品質**: Black + isort + flake8準拠
- **テスト**: 新機能には必ずテスト追加
- **ドキュメント**: APIの変更は必ずドキュメント更新
- **互換性**: 既存機能を破綻させない

### 報告・要望

- 🐛 **バグ報告**: [Issues](https://github.com/dustland/genesis-mcp/issues)
- 💡 **機能要望**: [Discussions](https://github.com/dustland/genesis-mcp/discussions)
- 📧 **直接連絡**: メンテナ向けメール

---

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照

---

## 🙏 謝辞

- **[Genesis World](https://github.com/Genesis-Embodied-AI/Genesis)**: 革新的な物理シミュレーションフレームワーク
- **[Google Gemini](https://ai.google.dev/)**: 高品質なAIコード生成
- **[Model Context Protocol](https://modelcontextprotocol.io/)**: 標準化されたAI通信プロトコル

---

**🎬 Genesis MCP で、AIが創造する次世代物理シミュレーションを体験しよう！**
