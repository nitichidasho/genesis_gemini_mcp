# 自然言語Genesis MCP 使用ガイド

## 🚀 概要

このプロジェクトでは、自然言語でGenesis World物理シミュレーションを操作できるMCPサーバーを実装しています。

## 📊 データフロー

```
ユーザー入力: "ボックスを追加して"
        ↓
自然言語処理: 入力解析・コマンド生成  
        ↓
MCPクライアント: JSON-RPCメッセージ作成
        ↓
stdio transport: 標準入出力通信
        ↓  
MCPサーバー: リクエスト受信
        ↓
SimulationService: Genesis Worldコード生成
        ↓
Genesis World: 物理シミュレーション実行
        ↓
結果収集: ログ・状態情報
        ↓
MCPサーバー: JSON-RPCレスポンス
        ↓
stdio transport: 結果送信
        ↓
MCPクライアント: 結果受信・解釈
        ↓
ユーザー: 自然言語での結果表示
```

## 🛠️ セットアップ

### 1. 環境準備
```powershell
# 仮想環境アクティベート（既にセットアップ済みの場合）
.venv\Scripts\activate.bat

# 必要に応じて依存関係を再インストール
uv pip install -e .
```

### 2. サーバー起動確認
```powershell
# サーバーが正常に起動するかテスト
python server.py
```

## 🎯 使用方法

### 方法1: 自然言語クライアント（推奨）

完全な自然言語インターフェースを使用：

```powershell
python examples/natural_language_client.py
```

**対応する自然言語コマンド:**
- `"ボックスを追加して"`
- `"赤い球体を右側に配置"`
- `"サイズ2x2x2の青いキューブを中央に"`
- `"ロボットアームのあるシーンを作成"`
- `"基本的なシーンを作成して"`

### 方法2: 標準MCPクライアント

```powershell
python examples/stdio_client.py
```

### 方法3: テストクライアント

```powershell
python examples/test_client.py
```

## 🔧 新機能

### 追加されたMCPツール

#### 1. `create_scene`
**説明:** 自然言語説明からGenesis Worldシーンを作成

**パラメータ:**
- `description` (string): シーンの説明文
- `show_viewer` (boolean): 3Dビューアー表示の有無

**使用例:**
```json
{
  "name": "create_scene",
  "arguments": {
    "description": "ロボットアームと複数のオブジェクトがあるシーン",
    "show_viewer": true
  }
}
```

#### 2. `add_object`  
**説明:** 指定したオブジェクトをシーンに追加

**パラメータ:**
- `object_type` (string): オブジェクト種類 (box, sphere, cylinder, plane, robot)
- `position` (array): [x, y, z] 位置座標
- `properties` (object): サイズ、色などのプロパティ

**使用例:**
```json
{
  "name": "add_object", 
  "arguments": {
    "object_type": "box",
    "position": [1, 0, 1],
    "properties": {
      "size": [2, 2, 2],
      "color": "red"
    }
  }
}
```

### 自然言語パターン認識

#### オブジェクト種類
- **ボックス/キューブ:** "ボックス", "box", "立方体", "キューブ"
- **球体:** "球", "sphere", "ボール", "ball"
- **円柱:** "円柱", "cylinder"
- **平面:** "平面", "plane", "地面"
- **ロボット:** "ロボット", "robot", "アーム", "arm"

#### 位置指定
- **座標直接指定:** "座標(1,2,3)", "位置(0,0,1)"
- **相対位置:** "右側", "左側", "中央", "上"

#### プロパティ指定
- **サイズ:** "サイズ2x2x2", "大きさ1.5"
- **色:** "赤い", "青色の", "green"

## 🎬 実行例

### 例1: 基本的なボックス追加
```
入力: "ボックスを追加して"

処理フロー:
1. 自然言語解析 → object_type: "box"
2. MCPコマンド生成 → add_object
3. Genesis Worldコード生成:
   ```python
   import genesis as gs
   gs.init(backend=gs.gpu)
   scene = gs.Scene(show_viewer=True)
   obj = scene.add_entity(gs.morphs.Box(size=(1.0, 1.0, 1.0)))
   scene.build()
   for i in range(50):
       scene.step()
   ```
4. シミュレーション実行
5. 結果: "✅ boxを追加しました！"
```

### 例2: 詳細指定での球体追加
```
入力: "赤い球体を座標(2,1,1)に配置"

処理フロー:
1. 自然言語解析 → 
   - object_type: "sphere"
   - position: [2, 1, 1]
   - properties: {"color": "red"}
2. Genesis Worldコード生成:
   ```python
   obj = scene.add_entity(gs.morphs.Sphere(radius=0.5))
   obj.set_position([2, 1, 1])
   obj.set_color((1.0, 0.0, 0.0))
   ```
3. 結果: "✅ sphereを追加しました！位置: (2.0, 1.0, 1.0), 色: red"
```

### 例3: 複合シーン作成
```
入力: "ロボットアームと複数のオブジェクトがあるシーンを作成"

処理フロー:
1. 自然言語解析 → create_scene
2. Genesis Worldコード生成:
   ```python
   scene = gs.Scene(show_viewer=True)
   plane = scene.add_entity(gs.morphs.Plane())
   robot = scene.add_entity(gs.morphs.MJCF(file='xml/franka_emika_panda/panda.xml'))
   # 複数オブジェクトのランダム配置
   for i in range(3):
       pos = (random.uniform(-2, 2), random.uniform(-2, 2), random.uniform(0.5, 2))
       obj = scene.add_entity(gs.morphs.Box(size=(0.5, 0.5, 0.5)))
       obj.set_position(pos)
   ```
3. 結果: 3Dビューアーでロボットアームと複数ボックスのシーン表示
```

## 🔍 デバッグ

### サーバーログ確認
```powershell
# デバッグレベルでサーバー起動
python server.py
```

### 個別機能テスト
```powershell
# MCPツールテスト
python examples/test_client.py

# 選択: 1 (自動テスト)
```

### 生成コード確認
自然言語クライアントの実行時に、生成されたGenesis Worldコードが表示されます。

## ⚡ パフォーマンス最適化

### シーンの再利用
複数のオブジェクト追加時は、既存シーンを再利用するとパフォーマンスが向上します。

### GPU使用
```python
gs.init(backend=gs.gpu)  # GPU加速を有効化
```

## 🚨 トラブルシューティング

### よくある問題

**1. MCPサーバー起動失敗**
```
解決策: 依存関係を再インストール
uv pip install -e .
```

**2. Genesis World初期化エラー**  
```
解決策: GPU/CPUバックエンドを切り替え
gs.init(backend=gs.cpu)  # CPUバックエンドを使用
```

**3. 3Dビューアーが表示されない**
```
解決策: show_viewer=Falseに設定して実行
```

**4. 自然言語解析が正しく動作しない**
```
解決策: より具体的な表現を使用
❌ "何か追加"
✅ "ボックスを追加して"
```

## 📚 拡張可能性

### 新しいオブジェクト種類の追加
`simulation.py`の`generate_add_object_code`メソッドに新しいオブジェクト処理を追加

### 自然言語パターンの拡張
`natural_language_client.py`の`NaturalLanguageProcessor`クラスでパターンを追加

### 新しいMCPツールの追加
`server.py`に新しい`@mcp.tool()`デコレータ付き関数を追加

これで、完全な自然言語→MCP→Genesis World のデータフローが実装されました！