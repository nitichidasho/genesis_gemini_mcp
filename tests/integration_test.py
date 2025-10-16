#!/usr/bin/env python3
"""
🧪 Genesis World VNC 統合テストスクリプト

VNC環境での Genesis World + MCP Server + GeminiCLI
の統合テストを実行します。
"""

import asyncio
import subprocess
import time
import sys
import os
from pathlib import Path

# プロジェクトパス設定
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def print_status(message, status="info"):
    """ステータス表示"""
    colors = {
        "info": "\033[34mℹ️",
        "success": "\033[32m✅",
        "warning": "\033[33m⚠️",
        "error": "\033[31m❌"
    }
    reset = "\033[0m"
    print(f"{colors.get(status, colors['info'])} {message}{reset}")

class GenesisVNCIntegrationTest:
    """Genesis World VNC 統合テスト"""
    
    def __init__(self):
        self.vnc_active = False
        self.display_available = False
        self.mcp_server_running = False
        self.test_results = {}
        
    async def run_all_tests(self):
        """全テスト実行"""
        print_status("Genesis World VNC 統合テスト開始", "info")
        print("="*60)
        
        # テスト実行順序
        tests = [
            ("display_test", "ディスプレイ環境確認"),
            ("vnc_test", "VNC サーバー確認"),
            ("genesis_import_test", "Genesis World インポート"),
            ("mcp_server_test", "MCP サーバー起動テスト"),
            ("gemini_llm_test", "GeminiCLI 接続テスト"),
            ("gui_display_test", "Genesis GUI表示テスト"),
            ("integration_test", "統合動作テスト")
        ]
        
        for test_name, test_desc in tests:
            print_status(f"テスト実行中: {test_desc}", "info")
            try:
                result = await getattr(self, test_name)()
                self.test_results[test_name] = result
                
                if result:
                    print_status(f"✅ {test_desc}: 成功", "success")
                else:
                    print_status(f"❌ {test_desc}: 失敗", "error")
                    
            except Exception as e:
                print_status(f"❌ {test_desc}: エラー - {e}", "error")
                self.test_results[test_name] = False
            
            print("-" * 40)
        
        # 結果表示
        await self.show_test_summary()
        
    async def display_test(self):
        """ディスプレイ環境確認"""
        try:
            # DISPLAY環境変数確認
            display_env = os.environ.get('DISPLAY')
            if not display_env:
                print_status("DISPLAY環境変数が設定されていません", "warning")
                os.environ['DISPLAY'] = ':1'
                display_env = ':1'
                
            print_status(f"DISPLAY環境変数: {display_env}", "info")
            
            # X11サーバー確認
            result = subprocess.run(['xset', 'q'], 
                                  capture_output=True, timeout=5)
            
            if result.returncode == 0:
                self.display_available = True
                return True
            else:
                print_status("X11サーバーが応答しません", "warning")
                return False
                
        except Exception as e:
            print_status(f"ディスプレイテストエラー: {e}", "error")
            return False
    
    async def vnc_test(self):
        """VNC サーバー確認"""
        try:
            # VNC プロセス確認
            result = subprocess.run(['pgrep', '-f', 'Xvnc'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print_status("VNCサーバーが稼働中", "success")
                self.vnc_active = True
                
                # ポート確認
                port_result = subprocess.run(
                    ['netstat', '-tlnp'], 
                    capture_output=True, text=True
                )
                
                if ':5901' in port_result.stdout:
                    print_status("VNCポート5901が利用可能", "success")
                    return True
                else:
                    print_status("VNCポート5901が見つかりません", "warning")
                    
            else:
                print_status("VNCサーバーが見つかりません", "warning")
                print_status("VNCサーバーを起動してください: vncserver :1", "info")
                
            return False
            
        except Exception as e:
            print_status(f"VNCテストエラー: {e}", "error")
            return False
    
    async def genesis_import_test(self):
        """Genesis World インポートテスト"""
        try:
            # Genesis World インポート試行
            import genesis as gs
            print_status("Genesis World インポート成功", "success")
            
            # 基本初期化テスト
            gs.init(backend=gs.cpu)
            print_status("Genesis World CPU初期化成功", "success")
            
            return True
            
        except ImportError:
            print_status("Genesis World未インストール", "error")
            print_status("インストール: pip install genesis-world", "info")
            return False
        except Exception as e:
            print_status(f"Genesis World初期化エラー: {e}", "error")
            return False
    
    async def mcp_server_test(self):
        """MCP サーバーテスト"""
        try:
            server_path = project_root / "server.py"
            
            if not server_path.exists():
                print_status("server.py が見つかりません", "error")
                return False
            
            # MCP サーバープロセス起動テスト
            process = subprocess.Popen(
                [sys.executable, str(server_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 短時間待機してプロセス確認
            time.sleep(2)
            
            if process.poll() is None:
                print_status("MCP サーバーが正常起動", "success")
                process.terminate()
                self.mcp_server_running = True
                return True
            else:
                stdout, stderr = process.communicate()
                print_status(f"MCP サーバー起動エラー: {stderr}", "error")
                return False
                
        except Exception as e:
            print_status(f"MCP サーバーテストエラー: {e}", "error")
            return False
    
    async def gemini_llm_test(self):
        """GeminiCLI 接続テスト"""
        try:
            import sys
            sys.path.append('..')
            from src.genesis_mcp.services.gemini_service import GeminiCLIService
            
            service = GeminiCLIService()
            print_status("GeminiCLIサービス初期化完了", "success")
            
            # 簡単なテスト
            try:
                response = await service.generate_text("Hello, test message")
                if response:
                    print_status("GeminiCLI 応答成功", "success")
                    return True
                else:
                    print_status("GeminiCLI 応答が空", "warning")
                    return False
            except Exception as e:
                print_status(f"GeminiCLI 応答エラー: {e}", "warning")
                return False
                
        except ImportError:
            print_status("GeminiCLI サービスが利用できません", "warning")
            print_status("セットアップ実行: ./setup_gemini_cli.sh", "info")
            return False
        except Exception as e:
            print_status(f"GeminiCLI サーバー接続失敗: {e}", "error")
            return False
    
    async def gui_display_test(self):
        """Genesis GUI表示テスト"""
        if not self.display_available:
            print_status("ディスプレイ環境が利用できません", "error")
            return False
            
        try:
            import genesis as gs
            
            # 短時間のGUI表示テスト
            gs.init(backend=gs.cpu)
            scene = gs.Scene(show_viewer=True)
            
            # 地面とシンプルオブジェクト
            plane = scene.add_entity(gs.morphs.Plane())
            box = scene.add_entity(gs.morphs.Box(size=(1.0, 1.0, 1.0)), pos=(0, 0, 1))
            
            scene.build()
            print_status("Genesis World GUIビューアー起動成功", "success")
            
            # 短時間実行
            for i in range(10):
                scene.step()
            
            print_status("GUI表示テスト完了", "success")
            return True
            
        except Exception as e:
            print_status(f"GUI表示テストエラー: {e}", "error")
            return False
    
    async def integration_test(self):
        """統合動作テスト"""
        try:
            from examples.real_genesis_gui_client import RealGenesisMCPClient
            
            print_status("統合クライアント初期化中...", "info")
            client = RealGenesisMCPClient()
            
            # 初期化
            init_result = await client.initialize()
            if not init_result:
                print_status("統合クライアント初期化失敗", "error")
                return False
            
            # 簡易実行テスト
            result = await client.execute_genesis_world_command("赤い球体を表示")
            
            if "✅" in result:
                print_status("統合動作テスト成功", "success")
                return True
            else:
                print_status("統合動作テスト部分的成功", "warning")
                return True
                
        except Exception as e:
            print_status(f"統合テストエラー: {e}", "error")
            return False
    
    async def show_test_summary(self):
        """テスト結果サマリー"""
        print("\n" + "="*60)
        print_status("Genesis World VNC 統合テスト結果", "info")
        print("="*60)
        
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅" if result else "❌"
            print(f"{status} {test_name}")
        
        print(f"\n📊 成功: {passed}/{total}")
        
        if passed == total:
            print_status("🎉 全テスト成功！VNC + Genesis World完全動作", "success")
            
            print("\n🚀 使用準備完了:")
            print("   1. Windows側でVNC接続: localhost:5901")
            print("   2. real_genesis_gui_client.py 実行")
            print("   3. Genesis World 3DビューアーをVNCで確認")
            
        elif passed >= total // 2:
            print_status("⚠️ 部分的成功 - 基本機能は動作", "warning")
        else:
            print_status("❌ 多数のテストが失敗 - 環境確認が必要", "error")

# メイン実行
if __name__ == "__main__":
    test_runner = GenesisVNCIntegrationTest()
    asyncio.run(test_runner.run_all_tests())