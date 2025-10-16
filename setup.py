#!/usr/bin/env python3
"""
Genesis MCP 統合セットアップスクリプト (x11vnc + Xvfb対応)

使用方法:
    python setup.py                    # 基本セットアップ
    python setup.py --env              # 仮想環境セットアップ
    python setup.py --vnc              # VNC環境セットアップ（x11vnc + Xvfb）
    python setup.py --genesis          # Genesis World セットアップ
    python setup.py --gemini-key KEY   # GeminiAPIキー設定
    python setup.py --all              # 全て実行

オプション:
    -h, --help          このヘルプを表示
    -e, --env           仮想環境(UV)をセットアップ
    -v, --vnc           x11vnc + Xvfb VNC環境をセットアップ（TigerVNC不要）
    -w, --genesis       Genesis World をGitHubからセットアップ
    -g, --gemini-key    GeminiAPIキーを設定
    -a, --all           全ての設定を実行
    --check             環境チェックのみ実行

VNC情報:
    - 使用技術: x11vnc + Xvfb（軽量で高性能）
    - 対応OS: Linux/Mac（Windowsは対象外）
    - 起動方法: python start_vnc.py --start
    - 接続先: localhost:5900
"""

import argparse
import asyncio
import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Dict, Any

# .envファイル読み込み関数
def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print(f"✅ .envファイルを読み込みました: {env_file}")
    else:
        print(f"⚠️ .envファイルが見つかりません: {env_file}")

class GenesisSetup:
    """Genesis MCP統合セットアップクラス"""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.is_windows = self.platform == "windows"
        self.project_root = Path(__file__).parent
        
        # .envファイルを自動読み込み
        load_env_file()
        
    def check_dependencies(self) -> Dict[str, bool]:
        """依存関係チェック"""
        results = {}
        
        # Python バージョンチェック
        results["python"] = sys.version_info >= (3, 8)
        
        # Git チェック
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
            results["git"] = True
        except:
            results["git"] = False
            
        # UV チェック
        try:
            subprocess.run(["uv", "--version"], capture_output=True, check=True)
            results["uv"] = True
        except:
            results["uv"] = False
        
        # MCP チェック
        try:
            import mcp
            results["mcp"] = True
        except ImportError:
            results["mcp"] = False
        
        # PyTorch チェック
        try:
            import torch
            results["torch"] = True
            results["torch_cuda"] = torch.cuda.is_available()
        except ImportError:
            results["torch"] = False
            results["torch_cuda"] = False
        
        # Genesis World チェック  
        try:
            import genesis as gs
            results["genesis_world"] = True
            results["genesis_version"] = getattr(gs, '__version__', 'unknown')
        except ImportError as e:
            results["genesis_world"] = False
            results["genesis_error"] = str(e)
        except Exception as e:
            results["genesis_world"] = False
            results["genesis_error"] = f"Unexpected error: {str(e)}"
        
        # Genesis World git repository チェック
        genesis_dir = self.project_root / "Genesis"
        results["genesis_repo"] = genesis_dir.exists() and (genesis_dir / ".git").exists()
        
        # VNC環境チェック（x11vnc + Xvfb）
        if not self.is_windows:
            try:
                # Xvfb チェック
                subprocess.run(["which", "Xvfb"], capture_output=True, check=True)
                results["xvfb"] = True
            except:
                results["xvfb"] = False
            
            try:
                # x11vnc チェック
                subprocess.run(["which", "x11vnc"], capture_output=True, check=True)
                results["x11vnc"] = True
            except:
                results["x11vnc"] = False
            
            try:
                # openbox チェック
                subprocess.run(["which", "openbox"], capture_output=True, check=True)
                results["openbox"] = True
            except:
                results["openbox"] = False
            
            # VNC環境総合判定
            results["vnc_environment"] = results.get("xvfb", False) and results.get("x11vnc", False)
        else:
            # Windows環境では VNC チェックをスキップ
            results["vnc_environment"] = False
            results["xvfb"] = False
            results["x11vnc"] = False
            results["openbox"] = False
            
        return results
    
    def install_uv(self) -> bool:
        """UV パッケージマネージャーをインストール"""
        print("📦 UV パッケージマネージャーをインストール中...")
        
        try:
            if self.is_windows:
                # Windows用UVインストール
                subprocess.run([
                    "powershell", "-c",
                    "irm https://astral.sh/uv/install.ps1 | iex"
                ], check=True)
            else:
                # Linux/Mac用UVインストール
                subprocess.run([
                    "curl", "-LsSf", "https://astral.sh/uv/install.sh", "|", "sh"
                ], shell=True, check=True)
            
            print("✅ UV インストール完了")
            return True
        except Exception as e:
            print(f"❌ UV インストール失敗: {e}")
            return False
    
    def setup_virtual_env(self) -> bool:
        """仮想環境セットアップ"""
        print("🔧 仮想環境セットアップ中...")
        
        try:
            # pyproject.tomlの存在確認
            pyproject_path = self.project_root / "pyproject.toml"
            if not pyproject_path.exists():
                print("❌ pyproject.toml が見つかりません")
                return False
            
            # UV仮想環境作成
            subprocess.run(["uv", "venv", ".venv"], cwd=self.project_root, check=True)
            
            # 依存関係インストール
            subprocess.run(["uv", "pip", "install", "-e", "."], cwd=self.project_root, check=True)
            
            print("✅ 仮想環境セットアップ完了")
            path = r'.\.venv\Scripts\activate' if self.is_windows else 'source .venv/bin/activate'
            print(f"💡 アクティベート: {path}")

            return True
            
        except Exception as e:
            print(f"❌ 仮想環境セットアップ失敗: {e}")
            return False
    
    def setup_vnc(self) -> bool:
        """x11vnc + Xvfb VNC環境セットアップ"""
        print("🖥️ x11vnc + Xvfb VNC環境セットアップ中...")
        print("📝 Genesis最適化VNCサーバー（TigerVNC不要）")
        
        if self.is_windows:
            print("⚠️ Windows環境ではVNCセットアップはスキップされます")
            print("💡 WindowsではWSL2またはDockerを使用してください")
            return True
        
        try:
            # x11vnc + Xvfb関連パッケージのインストール
            print("📦 必要パッケージをインストール中...")
            
            # 基本パッケージ（TigerVNC除外、x11vnc + Xvfb重視）
            base_packages = [
                "xorg",           # X Window System
                "xvfb",           # 仮想フレームバッファX server
                "x11vnc",         # X11用VNCサーバー
                "openbox",        # 軽量ウィンドウマネージャー
                "mesa-utils",     # OpenGL utilities
                "libgl1-mesa-glx", # OpenGL libraries
                "xterm"           # ターミナルエミュレータ
            ]
            
            # Ubuntu/Debian系
            if subprocess.run(["which", "apt"], capture_output=True).returncode == 0:
                print("🔧 Debian/Ubuntu系でパッケージインストール...")
                subprocess.run(["sudo", "apt", "update"], check=True)
                subprocess.run(["sudo", "apt", "install", "-y"] + base_packages, check=True)
                
                # 追加の開発ツール
                dev_packages = ["pkg-config", "build-essential"]
                subprocess.run(["sudo", "apt", "install", "-y"] + dev_packages, check=True)
            
            # CentOS/RHEL/Fedora系
            elif subprocess.run(["which", "yum"], capture_output=True).returncode == 0:
                print("🔧 Red Hat系でパッケージインストール...")
                yum_packages = [
                    "xorg-x11-server-Xorg", "xorg-x11-server-Xvfb", 
                    "x11vnc", "openbox", "mesa-libGL", "xterm"
                ]
                subprocess.run(["sudo", "yum", "install", "-y"] + yum_packages, check=True)
            
            elif subprocess.run(["which", "dnf"], capture_output=True).returncode == 0:
                print("🔧 Fedora系でパッケージインストール...")
                dnf_packages = [
                    "@base-x", "xorg-x11-server-Xvfb", 
                    "x11vnc", "openbox", "mesa-libGL", "xterm"
                ]
                subprocess.run(["sudo", "dnf", "install", "-y"] + dnf_packages, check=True)
            
            # パッケージ確認
            print("🔍 インストール確認中...")
            required_commands = ["Xvfb", "x11vnc", "openbox"]
            for cmd in required_commands:
                result = subprocess.run(["which", cmd], capture_output=True)
                if result.returncode == 0:
                    print(f"✅ {cmd}: 利用可能")
                else:
                    print(f"⚠️ {cmd}: 見つかりません")
            
            print("✅ x11vnc + Xvfb VNC環境セットアップ完了")
            print("🚀 使用方法: python start_vnc.py --start")
            return True
            
        except Exception as e:
            print(f"❌ VNC環境セットアップ失敗: {e}")
            print("💡 手動インストール: sudo apt install xvfb x11vnc openbox")
            return False
    
    def setup_gemini_key(self, api_key: str) -> bool:
        """GeminiAPIキー設定"""
        print("🔑 GeminiAPIキー設定中...")
        
        try:
            # 環境変数ファイル作成
            env_file = self.project_root / ".env"
            
            with open(env_file, "w") as f:
                f.write(f"GEMINI_API_KEY={api_key}\n")
            
            # 現在のセッションでも設定
            os.environ["GEMINI_API_KEY"] = api_key
            
            print("✅ GeminiAPIキー設定完了")
            print("💡 .envファイルに保存されました")
            return True
            
        except Exception as e:
            print(f"❌ GeminiAPIキー設定失敗: {e}")
            return False
    
    def setup_genesis_world(self) -> bool:
        """Genesis World をGitHubからクローンしてインストール"""
        print("🌍 Genesis World セットアップ中...")
        
        try:
            genesis_dir = self.project_root / "Genesis"
            
            # 既存のディレクトリがある場合は更新
            if genesis_dir.exists():
                print("📁 既存のGenesisディレクトリが見つかりました。更新中...")
                subprocess.run(["git", "pull"], cwd=genesis_dir, check=True)
            else:
                print("📥 Genesis リポジトリをクローン中...")
                subprocess.run([
                    "git", "clone", 
                    "https://github.com/Genesis-Embodied-AI/Genesis.git"
                ], cwd=self.project_root, check=True)
            
            # Genesis をインストール
            print("🔧 Genesis をインストール中...")
            if self.is_windows:
                # Windows用インストール
                subprocess.run([
                    "uv", "pip", "install", "-e", str(genesis_dir)
                ], check=True)
            else:
                # Linux/Mac用インストール
                subprocess.run([
                    "uv", "pip", "install", "-e", str(genesis_dir)
                ], check=True)
            
            print("✅ Genesis World セットアップ完了")
            return True
            
        except Exception as e:
            print(f"❌ Genesis World セットアップ失敗: {e}")
            print("💡 手動でインストール:")
            print("   git clone https://github.com/Genesis-Embodied-AI/Genesis.git")
            print("   cd Genesis")
            print("   uv pip install -e .")
            return False
    
    def check_environment(self) -> None:
        """環境チェック実行"""
        print("🔍 環境チェック実行中...\n")
        
        deps = self.check_dependencies()
        
        print("📋 依存関係チェック結果:")
        for name, status in deps.items():
            if name in ['genesis_version', 'genesis_error', 'torch_cuda', 'xvfb', 'x11vnc', 'openbox']:
                continue  # これらは後で表示
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {name}")
        
        # PyTorch詳細情報
        if deps.get("torch", False):
            cuda_status = "✅" if deps.get("torch_cuda", False) else "❌"
            print(f"  ✅ torch (CUDA: {cuda_status})")
        
        # Genesis World詳細情報
        if deps.get("genesis_world", False):
            version = deps.get("genesis_version", "unknown")
            print(f"  ✅ genesis_world (バージョン: {version})")
        else:
            error = deps.get("genesis_error", "不明なエラー")
            print(f"  ❌ genesis_world (エラー: {error})")
        
        # VNC環境詳細情報
        if not self.is_windows:
            vnc_status = "✅" if deps.get("vnc_environment", False) else "❌"
            print(f"  {vnc_status} vnc_environment (x11vnc + Xvfb)")
            
            # VNC詳細コンポーネント
            xvfb_status = "✅" if deps.get("xvfb", False) else "❌"
            x11vnc_status = "✅" if deps.get("x11vnc", False) else "❌"
            openbox_status = "✅" if deps.get("openbox", False) else "❌"
            
            print(f"    {xvfb_status} Xvfb (仮想フレームバッファ)")
            print(f"    {x11vnc_status} x11vnc (VNCサーバー)")
            print(f"    {openbox_status} openbox (ウィンドウマネージャー)")
        else:
            print("  ⚠️ vnc_environment (Windows環境ではスキップ)")
        
        # Geminiキーチェック
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            print(f"  ✅ GEMINI_API_KEY (長さ: {len(gemini_key)})")
        else:
            print("  ❌ GEMINI_API_KEY (未設定)")
        
        # Genesis Worldリポジトリチェック
        genesis_dir = self.project_root / "Genesis"
        if deps.get("genesis_repo", False):
            print("  ✅ Genesis Repository (クローン済み)")
        else:
            print("  ❌ Genesis Repository (未クローン)")
        
        print()
    
    def run_full_setup(self) -> bool:
        """フルセットアップ実行"""
        print("🚀 Genesis MCP フルセットアップ開始\n")
        
        success = True
        
        # 1. 依存関係チェック
        deps = self.check_dependencies()
        if not deps.get("uv", False):
            if not self.install_uv():
                success = False
        
        # 2. 仮想環境セットアップ
        if not self.setup_virtual_env():
            success = False
        
        # 3. Genesis World セットアップ
        if not self.setup_genesis_world():
            success = False
        
        # 4. VNCセットアップ（Linux/Macのみ）
        if not self.is_windows:
            if not self.setup_vnc():
                success = False
        
        if success:
            print("\n🎉 セットアップ完了!")
            print("\n次のステップ:")
            print("1. GeminiAPIキーを設定: python setup.py --gemini-key YOUR_KEY")
            print("2. 仮想環境をアクティベート")
            print("3. クライアント実行: python genesis_client.py")
            print("\n💡 個別セットアップコマンド:")
            print("   python setup.py --genesis    # Genesis Worldのみセットアップ")
        else:
            print("\n⚠️ セットアップ中にエラーが発生しました")
            print("💡 個別に実行してみてください:")
            print("   python setup.py --genesis    # Genesis World セットアップ")
        
        return success

def main():
    parser = argparse.ArgumentParser(
        description="Genesis MCP 統合セットアップスクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("-e", "--env", action="store_true", 
                       help="仮想環境セットアップ")
    parser.add_argument("-v", "--vnc", action="store_true",
                       help="VNC環境セットアップ")
    parser.add_argument("-w", "--genesis", action="store_true",
                       help="Genesis World セットアップ")
    parser.add_argument("-g", "--gemini-key", type=str, metavar="KEY",
                       help="GeminiAPIキー設定")
    parser.add_argument("-a", "--all", action="store_true",
                       help="全ての設定を実行")
    parser.add_argument("--check", action="store_true",
                       help="環境チェックのみ実行")
    
    args = parser.parse_args()
    
    setup = GenesisSetup()
    
    # オプションが何も指定されていない場合は基本セットアップ
    if not any([args.env, args.vnc, args.genesis, args.gemini_key, args.all, args.check]):
        setup.check_environment()
        return
    
    # 環境チェックのみ
    if args.check:
        setup.check_environment()
        return
    
    # 全てのセットアップ
    if args.all:
        setup.run_full_setup()
        return
    
    # 個別オプション処理
    if args.env:
        deps = setup.check_dependencies()
        if not deps.get("uv", False):
            setup.install_uv()
        setup.setup_virtual_env()
    
    if args.genesis:
        setup.setup_genesis_world()
    
    if args.vnc:
        setup.setup_vnc()
    
    if args.gemini_key:
        setup.setup_gemini_key(args.gemini_key)

if __name__ == "__main__":
    main()