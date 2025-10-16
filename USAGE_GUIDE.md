# Genesis MCP Gemini 使用ガイド

## 🚀 クイックスタート

### 1. 環境セットアップ
```bash
# 統合セットアップスクリプト使用
python setup.py --all

# または個別設定
python setup.py --env        # 仮想環境のみ
python setup.py --vnc        # VNC設定のみ  
python setup.py --gemini-key # GeminiAPIキー設定のみ
```

### 2. 基本使用方法

#### インタラクティブクライアント
```bash
python genesis_client.py
# または
python genesis_client.py --interactive
```

#### デモモード
```bash
python genesis_client.py --demo
```

#### GUIモード
```bash
python genesis_client.py --gui
```

#### VNCモード
```bash
python genesis_client.py --vnc
```

#### MCPサーバーモード
```bash
python genesis_server.py              # STDIO通信（デフォルト）
python genesis_server.py --stdio      # STDIO通信
python genesis_server.py --tcp        # TCP通信（ポート8000）
python genesis_server.py --debug      # デバッグモード
```

## 🎯 実際の使用例

### Example 1: 自然言語でのシーン作成

```python
# インタラクティブクライアントで実行
python genesis_client.py

# プロンプト入力例:
> Create a red sphere falling onto a blue plane with realistic physics
```

**生成される Genesis コード例:**
```python
import genesis as gs
import time

# Genesis初期化
gs.init(backend=gs.gpu)

# シーン作成
scene = gs.Scene(show_viewer=True)

# 地面となる平面作成
plane = scene.add_entity(
    gs.morphs.Box(size=(10, 10, 0.1), pos=(0, 0, -0.05))
)
plane.set_material(gs.materials.Rigid(color=(0.2, 0.4, 0.8)))

# 落下する球体作成
sphere = scene.add_entity(
    gs.morphs.Sphere(radius=0.5, pos=(0, 0, 3))
)
sphere.set_material(gs.materials.Rigid(color=(0.8, 0.2, 0.2)))

# シーンビルド
scene.build()

# シミュレーション実行
for i in range(300):
    scene.step()
    time.sleep(0.01)
```

### Example 2: 複雑なロボットシミュレーション

```bash
# インタラクティブモードでの入力例
> Generate a quadruped robot walking simulation with 4 legs, each with 3 joints
```

### Example 3: 物理パラメータ調整

```bash
# プロンプト例
> Create a bouncing ball simulation with low gravity and high restitution
```

## 🔧 高度な使用方法

### 1. コード生成プロンプト

```python
# genesis_client.py で自動生成されるプロンプト例
system_prompt = """Generate Genesis World v0.3.3 Python code following these patterns:

1. Import genesis as gs, time, math
2. Object creation patterns:
   - Spheres: gs.morphs.Sphere(radius=0.5)
   - Boxes: gs.morphs.Box(size=(1.0, 1.0, 1.0))
3. Positioning after scene.build():
   - obj.set_pos((x, y, z))
4. Simulation loop with progress output

Return only executable Python code."""
```

### 2. 環境変数設定

```bash
# .env ファイル作成
GEMINI_API_KEY=your_api_key_here
GENESIS_BACKEND=gpu  # または cpu
DISPLAY=:1           # VNC使用時
```

### 3. MCPサーバーとしての使用

```python
# 外部アプリケーションからの使用例
import asyncio
from genesis_server import GenesisServer

async def use_mcp_server():
    server = GenesisServer()
    
    # シミュレーション実行リクエスト
    request = {
        "method": "call_tool",
        "params": {
            "name": "run_simulation",
            "arguments": {
                "description": "A car driving on a track"
            }
        }
    }
    
    response = await server.call_tool(**request["params"])
    print(response)

asyncio.run(use_mcp_server())
```

## 🧪 テストとデバッグ

### サービステスト実行
```bash
# 全テスト実行
python tests/test_services.py --all

# 個別テスト
python tests/test_services.py --gemini      # GeminiCLI機能
python tests/test_services.py --simulation  # シミュレーション機能
python tests/test_services.py --integration # 統合テスト
```

### デバッグモード
```bash
# 詳細ログ出力でサーバー起動
python genesis_server.py --debug

# ログレベル指定
python genesis_server.py --log-level DEBUG
```

## 📊 パフォーマンス最適化

### 1. バックエンド選択
```python
# GPU使用（推奨）
gs.init(backend=gs.gpu)

# CPU使用（軽量）
gs.init(backend=gs.cpu)
```

### 2. ビューワー制御
```python
# 高速実行用（ビューワー無効）
scene = gs.Scene(show_viewer=False)

# GUI表示用
scene = gs.Scene(show_viewer=True)
```

### 3. バッチ処理
```python
# 複数シミュレーションの並列実行例
import asyncio

async def run_multiple_simulations():
    descriptions = [
        "Falling cubes",
        "Bouncing spheres", 
        "Rolling cylinders"
    ]
    
    tasks = [
        simulation_service.generate_and_run(desc) 
        for desc in descriptions
    ]
    
    results = await asyncio.gather(*tasks)
    return results
```

## 🚨 トラブルシューティング

### よくある問題と解決方法

#### 1. GEMINI_API_KEY エラー
```bash
# エラー: API key not found
# 解決:
python setup.py --gemini-key
# または手動で .env ファイルに追加
```

#### 2. Genesis World インポートエラー
```bash
# エラー: No module named 'genesis'
# 解決:
pip install genesis-world
# または
uv add genesis-world
```

#### 3. VNC表示問題
```bash
# エラー: Cannot connect to display
# 解決:
python setup.py --vnc
export DISPLAY=:1
```

#### 4. メモリ不足エラー
```python
# 解決: CPUバックエンド使用
gs.init(backend=gs.cpu)

# または軽量シーン作成
scene = gs.Scene(
    show_viewer=False,
    rigid_options=gs.options.RigidOptions(
        dt=0.01,
        constraint_solver=gs.constraint_solver.Newton
    )
)
```

## 📈 高度な機能

### 1. カスタムマテリアル
```python
# 生成プロンプト例
> Create a simulation with a rubber ball (high bounce) and a metal surface (low friction)
```

### 2. センサー統合
```python
# 生成プロンプト例  
> Add a camera sensor to track the motion of falling objects
```

### 3. 外力制御
```python
# 生成プロンプト例
> Apply wind force to cloth simulation with variable intensity
```

### 4. データエクスポート
```python
# シミュレーション結果の保存
result = simulation_service.run_simulation(code)
with open('simulation_data.json', 'w') as f:
    json.dump(result.result, f, indent=2)
```

## 🔗 統合例

### Jupyter Notebook での使用
```python
# notebook セル 1
%load_ext autoreload
%autoreload 2

import sys
sys.path.append('.')

from genesis_client import GenesisClient

# notebook セル 2
client = GenesisClient()

# notebook セル 3
result = await client.run_simulation("A pendulum swinging")
print(result)
```

### Web API としての使用
```python
# FastAPI wrapper例
from fastapi import FastAPI
from genesis_client import GenesisClient

app = FastAPI()

@app.post("/simulate")
async def create_simulation(description: str):
    client = GenesisClient()
    result = await client.run_simulation(description)
    return {"result": result}
```

## 📚 関連リソース

- [Genesis World ドキュメント](https://genesis-world.readthedocs.io/)
- [Google Gemini API リファレンス](https://ai.google.dev/docs)
- [Model Context Protocol 仕様](https://modelcontextprotocol.io/)

## 📞 サポート

問題が発生した場合:
1. `python tests/test_services.py --all` でテスト実行
2. ログファイル確認
3. GitHub Issues で報告

これでGenesis MCP Geminiプロジェクトの完全な使用ガイドが完成しました！