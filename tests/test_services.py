#!/usr/bin/env python3
"""
Genesis MCP サービステストスクリプト

使用方法:
    python test_services.py --all           # 全テスト実行
    python test_services.py --gemini        # GeminiCLIサービステスト
    python test_services.py --simulation    # シミュレーションサービステスト
    python test_services.py --integration   # 統合テスト
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# プロジェクトパスを追加
sys.path.append('.')

from src.genesis_mcp.services.gemini_service import GeminiCLIService
from src.genesis_mcp.services.simulation import SimulationService
from src.genesis_mcp.models import SimulationResult

class ServiceTester:
    """サービステストクラス"""
    
    def __init__(self):
        self.gemini_service = None
        self.simulation_service = None
        
    async def test_gemini_service(self) -> bool:
        """GeminiCLIサービステスト"""
        print("🔍 GeminiCLIサービステスト開始...")
        
        try:
            # サービス初期化
            self.gemini_service = GeminiCLIService()
            
            # API キー確認
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                print("⚠️ GEMINI_API_KEY が設定されていません")
                print("💡 フォールバック機能をテストします")
            
            # 基本テキスト生成テスト
            print("\n📝 テキスト生成テスト:")
            response = await self.gemini_service.generate_text("Hello, this is a test.")
            print(f"✅ 応答: {response[:100]}...")
            
            # Genesis専用プロンプトテスト
            print("\n🎯 Genesis専用プロンプトテスト:")
            genesis_prompt = """Generate Genesis World v0.3.3 Python code for: 
            A red sphere falling under gravity.
            
            Requirements:
            1. Import genesis as gs
            2. Use gs.morphs.Sphere
            3. Set position and run simulation loop
            
            Return only executable Python code."""
            
            genesis_code = await self.gemini_service.generate_text(genesis_prompt)
            print(f"✅ Genesis コード生成: {len(genesis_code)} characters")
            print("📋 生成されたコード:")
            print("-" * 40)
            print(genesis_code[:200] + "..." if len(genesis_code) > 200 else genesis_code)
            print("-" * 40)
            
            return True
            
        except Exception as e:
            print(f"❌ GeminiCLIサービステスト失敗: {e}")
            return False
    
    def test_simulation_service(self) -> bool:
        """シミュレーションサービステスト"""
        print("\n🔍 シミュレーションサービステスト開始...")
        
        try:
            # サービス初期化
            self.simulation_service = SimulationService()
            
            # 基本Genesis コードテスト
            print("\n🎯 基本Genesisコードテスト:")
            test_code = """
import genesis as gs
import time
import math

# Genesis初期化
gs.init(backend=gs.cpu)

# シーン作成
scene = gs.Scene(show_viewer=False)  # テスト用にviewer無効

# 球体作成
sphere = scene.add_entity(gs.morphs.Sphere(radius=0.5))

# シーンビルド
scene.build()

# 位置設定
sphere.set_pos((0, 0, 2))

print("🎯 テストシミュレーション開始")

# 短いシミュレーション実行
for i in range(10):
    scene.step()
    if i % 5 == 0:
        print(f"Step: {i}")

result = {
    "entities": len(scene.entities) if hasattr(scene, 'entities') else 1,
    "status": "test_completed",
    "genesis_available": True
}

print("✅ テストシミュレーション完了")
"""
            
            simulation_result = self.simulation_service.run_simulation(test_code)
            
            print(f"✅ シミュレーション実行完了")
            print(f"📊 結果: {simulation_result.result}")
            print(f"⏱️ 実行時間: {simulation_result.execution_time:.3f}秒")
            print(f"📝 ログ行数: {len(simulation_result.logs)}")
            print(f"🎯 ステータス: {simulation_result.status}")
            
            if simulation_result.error:
                print(f"⚠️ エラー: {simulation_result.error}")
            
            # 自然言語コード生成テスト
            print("\n🤖 自然言語コード生成テスト:")
            generated_code = self.simulation_service.generate_scene_code(
                "A blue box and red sphere interacting",
                show_viewer=False
            )
            print(f"✅ コード生成完了: {len(generated_code)} characters")
            
            return True
            
        except Exception as e:
            print(f"❌ シミュレーションサービステスト失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_integration(self) -> bool:
        """統合テスト"""
        print("\n🔍 統合テスト開始...")
        
        try:
            # 両サービス初期化
            if not self.gemini_service:
                self.gemini_service = GeminiCLIService()
            if not self.simulation_service:
                self.simulation_service = SimulationService()
            
            # 自然言語からコード生成→実行のフルフロー
            print("\n🎭 フルフローテスト:")
            description = "A small red sphere bouncing on a plane"
            
            # 1. GeminiCLIでコード生成
            prompt = f"""Generate Genesis World v0.3.3 Python code for: {description}

Requirements:
1. Import genesis as gs and necessary modules
2. Initialize with gs.init(backend=gs.cpu)
3. Create scene with show_viewer=False (for testing)
4. Add plane and sphere
5. Set appropriate positions
6. Run simulation for 20 steps with progress output
7. Set result variable with final status

Return only executable Python code without explanations."""

            generated_code = await self.gemini_service.generate_text(prompt)
            print(f"✅ コード生成完了: {len(generated_code)} characters")
            
            # 2. 生成されたコードを実行
            print("\n⚡ 生成コード実行:")
            result = self.simulation_service.run_simulation(generated_code)
            
            print(f"✅ 統合テスト完了")
            print(f"📊 最終結果: {result.result}")
            print(f"🎯 ステータス: {result.status}")
            
            return result.status == "completed"
            
        except Exception as e:
            print(f"❌ 統合テスト失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def run_all_tests(self) -> None:
        """全テスト実行"""
        print("🚀 Genesis MCP サービス全テスト開始\n")
        
        results = {}
        
        # 環境チェック
        print("🔍 環境チェック:")
        print(f"  Python: {sys.version}")
        print(f"  GEMINI_API_KEY: {'設定済み' if os.environ.get('GEMINI_API_KEY') else '未設定'}")
        
        try:
            import genesis as gs
            print("  Genesis World: ✅ 利用可能")
        except ImportError:
            print("  Genesis World: ⚠️ 未インストール（モック使用）")
        
        # 個別テスト実行
        results["gemini"] = await self.test_gemini_service()
        results["simulation"] = self.test_simulation_service()
        results["integration"] = await self.test_integration()
        
        # 結果報告
        print("\n" + "="*50)
        print("📋 テスト結果サマリー:")
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {test_name.ljust(15)}: {status}")
        
        overall_success = all(results.values())
        print(f"\n🎯 総合結果: {'✅ 全テストPASS' if overall_success else '❌ 一部テスト失敗'}")
        
        if overall_success:
            print("\n🎉 Genesis MCPサービスは正常に動作しています！")
            print("\n次のステップ:")
            print("1. python genesis_client.py でインタラクティブ使用")
            print("2. python genesis_server.py でMCPサーバー起動")
        else:
            print("\n⚠️ 問題があるサービスを確認してください")

def main():
    parser = argparse.ArgumentParser(description="Genesis MCP サービステスト")
    parser.add_argument("--all", action="store_true", help="全テスト実行")
    parser.add_argument("--gemini", action="store_true", help="GeminiCLIサービステスト")
    parser.add_argument("--simulation", action="store_true", help="シミュレーションサービステスト")
    parser.add_argument("--integration", action="store_true", help="統合テスト")
    
    args = parser.parse_args()
    
    tester = ServiceTester()
    
    if args.all or not any([args.gemini, args.simulation, args.integration]):
        asyncio.run(tester.run_all_tests())
    else:
        async def run_selected_tests():
            if args.gemini:
                await tester.test_gemini_service()
            if args.simulation:
                tester.test_simulation_service()
            if args.integration:
                await tester.test_integration()
        
        asyncio.run(run_selected_tests())

if __name__ == "__main__":
    main()