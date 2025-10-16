#!/usr/bin/env python3
"""
Genesis MCP 統合サーバー

使用方法:
    python genesis_server.py                    # 標準モード
    python genesis_server.py --stdio            # STDIO通信モード  
    python genesis_server.py --tcp              # TCP通信モード
    python genesis_server.py --debug            # デバッグモード

オプション:
    -h, --help          このヘルプを表示
    -s, --stdio         STDIO通信モード
    -t, --tcp           TCP通信モード
    -d, --debug         デバッグモード
    --host HOST         TCPサーバーホスト (デフォルト: localhost)
    --port PORT         TCPサーバーポート (デフォルト: 8000)
    --log-level LEVEL   ログレベル (DEBUG/INFO/WARNING/ERROR)
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# プロジェクトパスを追加
sys.path.append('.')

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    print("✅ MCP ライブラリの読み込み成功")
except ImportError as e:
    print(f"❌ MCP not installed or version incompatible: {e}")
    print("Install with: uv pip install mcp")
    sys.exit(1)

try:
    import genesis as gs
except ImportError:
    print("❌ Genesis World not installed. Install with: uv pip install genesis-world")
    sys.exit(1)

from src.genesis_mcp.services.gemini_service import GeminiCLIService
from src.genesis_mcp.services.simulation import SimulationService

class GenesisServer:
    """Genesis MCP 統合サーバー"""
    
    def __init__(self, debug: bool = False, log_level: str = "INFO"):
        # ログ設定を最初に
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("genesis-server")
        
        # MCPサーバー初期化
        self.server = Server("genesis-mcp")
        self.debug = debug
        self.gemini_service = None
        self.simulation_service = None
        
        # サービス初期化
        self._initialize_services()
        
        # MCPツール登録
        self._register_tools()
    
    def _initialize_services(self):
        """サービス初期化"""
        try:
            self.gemini_service = GeminiCLIService()
            self.simulation_service = SimulationService()
            self.logger.info("✅ サービス初期化完了")
        except Exception as e:
            self.logger.error(f"❌ サービス初期化エラー: {e}")
    
    def _register_tools(self):
        """MCPツール登録"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """利用可能なツール一覧"""
            return [
                Tool(
                    name="generate_simulation",
                    description="自然言語からGenesis Worldシミュレーションコードを生成",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "description": "シミュレーション内容の説明"
                            },
                            "use_llm": {
                                "type": "boolean", 
                                "description": "LLMを使用するかどうか",
                                "default": True
                            }
                        },
                        "required": ["description"]
                    }
                ),
                Tool(
                    name="execute_simulation",
                    description="Genesis Worldシミュレーションを実行",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "実行するGenesis Worldコード"
                            },
                            "show_gui": {
                                "type": "boolean",
                                "description": "GUIを表示するかどうか",
                                "default": True
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="get_templates",
                    description="Genesis Worldテンプレート一覧を取得",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "テンプレートカテゴリ (basic/physics/advanced)",
                                "default": "basic"
                            }
                        }
                    }
                ),
                Tool(
                    name="check_environment",
                    description="Genesis環境とサービス状態をチェック",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """ツール実行"""
            try:
                if name == "generate_simulation":
                    return await self._generate_simulation(arguments)
                elif name == "execute_simulation":
                    return await self._execute_simulation(arguments)
                elif name == "get_templates":
                    return await self._get_templates(arguments)
                elif name == "check_environment":
                    return await self._check_environment(arguments)
                else:
                    return [TextContent(type="text", text=f"❌ 不明なツール: {name}")]
            
            except Exception as e:
                error_msg = f"❌ ツール実行エラー ({name}): {e}"
                self.logger.error(error_msg)
                if self.debug:
                    import traceback
                    error_msg += f"\\n{traceback.format_exc()}"
                return [TextContent(type="text", text=error_msg)]
    
    async def _generate_simulation(self, args: Dict[str, Any]) -> List[TextContent]:
        """シミュレーションコード生成"""
        description = args["description"]
        use_llm = args.get("use_llm", True)
        
        self.logger.info(f"シミュレーション生成: {description}")
        
        if use_llm and self.gemini_service:
            try:
                # GeminiCLI経由でコード生成
                system_prompt = """You are an expert Genesis World v0.3.3 code generator. Generate Python code that follows these requirements:

1. MANDATORY imports: import genesis as gs, import time, import math
2. Use gs.morphs.Sphere(radius=0.5) for spheres
3. Use gs.morphs.Box(size=(1.0, 1.0, 1.0)) for boxes  
4. Set positions after scene.build()
5. Include simulation loop with time.sleep(0.01)

Return ONLY executable Python code without explanations."""

                user_prompt = f"Generate Genesis World code for: {description}"
                full_prompt = f"{system_prompt}\\n\\n{user_prompt}"
                
                response = await self.gemini_service.generate_text(full_prompt)
                
                if response:
                    return [TextContent(
                        type="text", 
                        text=f"🤖 GeminiCLI生成コード:\\n```python\\n{response}\\n```"
                    )]
            
            except Exception as e:
                self.logger.error(f"GeminiCLI生成エラー: {e}")
        
        # フォールバック: 固定テンプレート
        template_code = self._get_fallback_code(description)
        return [TextContent(
            type="text",
            text=f"📝 テンプレートコード:\\n```python\\n{template_code}\\n```"
        )]
    
    async def _execute_simulation(self, args: Dict[str, Any]) -> List[TextContent]:
        """シミュレーション実行"""
        code = args["code"]
        show_gui = args.get("show_gui", True)
        
        self.logger.info("シミュレーション実行開始")
        
        try:
            # 実行環境設定
            if not show_gui:
                os.environ["GENESIS_SHOW_VIEWER"] = "false"
            
            # コード実行
            exec_globals = {
                '__name__': '__main__',
                '__builtins__': __builtins__,
                'gs': gs,
                'time': __import__('time'),
                'math': __import__('math'),
                'print': print
            }
            
            exec(code, exec_globals)
            
            return [TextContent(
                type="text",
                text="✅ シミュレーション実行完了"
            )]
            
        except Exception as e:
            error_msg = f"❌ 実行エラー: {e}"
            self.logger.error(error_msg)
            return [TextContent(type="text", text=error_msg)]
    
    async def _get_templates(self, args: Dict[str, Any]) -> List[TextContent]:
        """テンプレート取得"""
        category = args.get("category", "basic")
        
        templates = {
            "basic": {
                "falling_sphere": "球体落下シミュレーション",
                "bouncing_ball": "弾むボールシミュレーション", 
                "rolling_sphere": "転がる球体シミュレーション"
            },
            "physics": {
                "collision": "衝突シミュレーション",
                "friction": "摩擦力シミュレーション",
                "gravity": "重力シミュレーション"
            },
            "advanced": {
                "multi_body": "複数オブジェクトシミュレーション",
                "constraint": "制約付きシミュレーション"
            }
        }
        
        category_templates = templates.get(category, templates["basic"])
        
        template_list = "\\n".join([
            f"- **{name}**: {desc}" 
            for name, desc in category_templates.items()
        ])
        
        return [TextContent(
            type="text",
            text=f"📋 {category}カテゴリのテンプレート:\\n{template_list}"
        )]
    
    async def _check_environment(self, args: Dict[str, Any]) -> List[TextContent]:
        """環境チェック"""
        status = {}
        
        # Genesis World チェック
        try:
            gs.init()
            status["genesis"] = "✅ 利用可能"
        except Exception as e:
            status["genesis"] = f"❌ エラー: {e}"
        
        # GeminiCLI サービスチェック
        if self.gemini_service:
            try:
                test_response = await self.gemini_service.generate_text("test")
                status["gemini"] = "✅ 利用可能" if test_response else "❌ 応答なし"
            except Exception as e:
                status["gemini"] = f"❌ エラー: {e}"
        else:
            status["gemini"] = "❌ 初期化されていません"
        
        # 環境変数チェック
        gemini_key = os.environ.get("GEMINI_API_KEY")
        status["gemini_key"] = "✅ 設定済み" if gemini_key else "❌ 未設定"
        
        status_text = "\\n".join([
            f"**{name}**: {status_val}"
            for name, status_val in status.items()
        ])
        
        return [TextContent(
            type="text",
            text=f"🔍 環境チェック結果:\\n{status_text}"
        )]
    
    def _get_fallback_code(self, description: str) -> str:
        """フォールバック用コード"""
        return '''import genesis as gs
import time
import math

# Genesis初期化
gs.init(backend=gs.cpu)

# シーン作成
scene = gs.Scene(show_viewer=True)

# 球体オブジェクト作成
sphere = scene.add_entity(gs.morphs.Sphere(radius=0.5))

# シーンビルド
scene.build()

# 位置設定
sphere.set_pos((0, 0, 2))

print("🎯 シミュレーション開始")

# シミュレーション実行
for i in range(1000):
    scene.step()
    if i % 50 == 0:
        print(f"Step: {i}")
        time.sleep(0.01)

print("✅ シミュレーション完了")'''
    
    async def run_stdio(self):
        """STDIO通信モードで実行"""
        self.logger.info("📡 STDIO通信モードで起動")
        try:
            async with stdio_server() as streams:
                # MCP 1.17.0の初期化オプション
                initialization_options = {}
                await self.server.run(
                    streams[0], 
                    streams[1], 
                    initialization_options
                )
        except Exception as e:
            self.logger.error(f"STDIO実行エラー: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            raise
    
    async def run_tcp(self, host: str = "localhost", port: int = 8000):
        """TCP通信モードで実行"""
        self.logger.info(f"🌐 TCP通信モードで起動 ({host}:{port})")
        # TCP実装は将来的に追加
        raise NotImplementedError("TCP mode not yet implemented")

def main():
    parser = argparse.ArgumentParser(
        description="Genesis MCP 統合サーバー",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("-s", "--stdio", action="store_true",
                       help="STDIO通信モード")
    parser.add_argument("-t", "--tcp", action="store_true",
                       help="TCP通信モード")
    parser.add_argument("-d", "--debug", action="store_true",
                       help="デバッグモード")
    parser.add_argument("--host", default="localhost",
                       help="TCPサーバーホスト")
    parser.add_argument("--port", type=int, default=8000,
                       help="TCPサーバーポート")
    parser.add_argument("--log-level", default="INFO",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="ログレベル")
    
    args = parser.parse_args()
    
    server = GenesisServer(debug=args.debug, log_level=args.log_level)
    
    try:
        if args.tcp:
            asyncio.run(server.run_tcp(args.host, args.port))
        else:
            # デフォルトはSTDIO
            asyncio.run(server.run_stdio())
    except KeyboardInterrupt:
        print("\\n🛑 サーバーを停止しました")
    except Exception as e:
        print(f"❌ サーバーエラー: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()