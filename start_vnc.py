#!/usr/bin/env python3
"""
VNC環境構築・管理スクリプト

使用方法:
    python start_vnc.py                 # VNC環境を自動構築
    python start_vnc.py --start         # VNCサーバー開始
    python start_vnc.py --stop          # VNCサーバー停止
    python start_vnc.py --status        # VNC状況確認
    python start_vnc.py --cleanup       # クリーンアップ
    python start_vnc.py --display       # 利用可能ディスプレイ表示
"""

import argparse
import os
import subprocess
import time
import json
import signal
from pathlib import Path
from typing import List, Optional, Dict

class VNCManager:
    """VNC環境管理クラス"""
    
    def __init__(self):
        self.vnc_config_file = Path.home() / ".genesis_vnc_config.json"
        # Genesis最適化設定
        self.default_geometry = "800x600"    # 低解像度でパフォーマンス重視
        self.default_depth = "16"            # 色深度削減でVNC転送効率化
        self.genesis_optimized = True
    
    def setup_vnc_environment(self) -> Optional[str]:
        """VNC環境の完全セットアップ"""
        print("🚀 Genesis用VNC環境をセットアップ中...")
        
        # 1. 必要パッケージの確認・インストール
        if not self._check_dependencies():
            if not self._install_dependencies():
                return None
        
        # 2. 既存VNCセッションの確認
        existing_display = self._find_existing_vnc()
        if existing_display and self._test_display_connection(existing_display):
            print(f"✅ 既存VNCセッションを使用: {existing_display}")
            self._save_vnc_config(existing_display)
            return existing_display
        
        # 3. 新しいVNCサーバーの起動
        new_display = self._start_new_vnc_server()
        if new_display:
            print(f"✅ 新しいVNCセッションを作成: {new_display}")
            self._save_vnc_config(new_display)
            return new_display
        
        # 4. 仮想ディスプレイのフォールバック
        virtual_display = self._start_virtual_display()
        if virtual_display:
            print(f"✅ 仮想ディスプレイを作成: {virtual_display}")
            self._save_vnc_config(virtual_display, is_virtual=True)
            return virtual_display
        
        print("❌ VNC環境の構築に失敗しました")
        return None
    
    def _check_dependencies(self) -> bool:
        """必要パッケージの確認"""
        print("🔍 必要パッケージを確認中...")
        
        required_commands = ['vncserver', 'vncpasswd', 'Xvfb', 'xdpyinfo']
        missing_commands = []
        
        for cmd in required_commands:
            try:
                subprocess.run([cmd, '--help'], capture_output=True, timeout=5)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                missing_commands.append(cmd)
        
        if missing_commands:
            print(f"⚠️ 不足パッケージ: {', '.join(missing_commands)}")
            return False
        
        print("✅ 必要パッケージが確認できました")
        return True
    
    def _install_dependencies(self) -> bool:
        """必要パッケージの自動インストール"""
        print("📦 必要パッケージをインストール中...")
        
        try:
            # Ubuntu/Debian系
            install_commands = [
                ['sudo', 'apt', 'update'],
                ['sudo', 'apt', 'install', '-y', 'tightvncserver', 'xvfb', 'x11-utils', 'xfce4', 'xfce4-goodies']
            ]
            
            for cmd in install_commands:
                print(f"実行中: {' '.join(cmd)}")
                result = subprocess.run(cmd, timeout=300)
                if result.returncode != 0:
                    print(f"❌ インストールに失敗: {' '.join(cmd)}")
                    return False
            
            print("✅ パッケージインストール完了")
            return True
            
        except Exception as e:
            print(f"❌ インストールエラー: {e}")
            return False
    
    def _find_existing_vnc(self) -> Optional[str]:
        """既存VNCセッション（Xvfb + x11vnc）の検索"""
        print("🔍 既存VNCセッションを検索中...")
        
        # 設定ファイルから既存セッション確認
        config = self.load_vnc_config()
        if config:
            display = config['display']
            print(f"🔍 設定ファイルから発見: {display}")
            
            # ディスプレイとプロセスの存在確認
            if self._test_display_connection(display):
                xvfb_running = subprocess.run(['pgrep', '-f', f'Xvfb {display}'], capture_output=True).returncode == 0
                x11vnc_running = self._check_x11vnc_process(display)
                
                if xvfb_running and x11vnc_running:
                    print(f"✅ 動作中のVNCセッション発見: {display}")
                    return display
                else:
                    print(f"⚠️ {display} は設定されているが一部プロセスが停止中")
        
        # プロセス検索でのXvfbディスプレイ発見
        try:
            result = subprocess.run(['pgrep', '-a', 'Xvfb'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    # "12345 Xvfb :12 ..." の形式から抽出
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.startswith(':') and part[1:].isdigit():
                            display = part
                            if self._check_x11vnc_process(display):
                                print(f"🔍 プロセスから発見: {display}")
                                return display
        except Exception:
            pass
        
        return None
    
    def _start_new_vnc_server(self) -> Optional[str]:
        """新しいVNCサーバー（Xvfb + x11vnc）の起動"""
        print("🚀 新しいVNCサーバーを起動中...")
        
        # 直接仮想ディスプレイ起動に移行
        return self._start_virtual_display()
    
    def _setup_genesis_optimization(self, display: str):
        """Genesis表示最適化をVNC起動時に自動適用"""
        print(f"🎮 Genesis表示最適化を適用中... (ディスプレイ: {display})")
        
        try:
            # OpenGL環境変数設定（Genesis用）
            genesis_env = {
                'DISPLAY': display,
                'MESA_GL_VERSION_OVERRIDE': '3.3',
                'MESA_GLSL_VERSION_OVERRIDE': '330',
                'LIBGL_ALWAYS_SOFTWARE': '1',
                'GALLIUM_DRIVER': 'llvmpipe',
                'LIBGL_ALWAYS_INDIRECT': '1',
                'MESA_NO_ERROR': '1',
                'MESA_DEBUG': '0',
                '__GL_SYNC_TO_VBLANK': '0',
                '__GL_YIELD': 'NOTHING',
            }
            
            # 環境変数を設定
            for key, value in genesis_env.items():
                os.environ[key] = value
            
            # X11リソース設定
            xresources_config = """
! Genesis VNC 最適化設定
Xft.dpi: 96
Xft.antialias: true
Xft.rgba: rgb
Xft.hinting: true
Xft.hintstyle: hintslight

! OpenGL設定
Mesa.GLX_FORCE_SOFTWARE_RENDERING: true
Mesa.GLX_DONT_CARE_REFRESH_RATE: true
"""
            
            xresources_path = os.path.expanduser("~/.Xresources")
            with open(xresources_path, 'w') as f:
                f.write(xresources_config)
            
            # X11設定適用
            env = dict(os.environ, DISPLAY=display)
            subprocess.run(['xrdb', '-merge', xresources_path], 
                         env=env, capture_output=True)
            
            # 軽量ウィンドウマネージャー起動
            self._start_lightweight_wm(display)
            
            print("✅ Genesis最適化完了")
            
        except Exception as e:
            print(f"⚠️ Genesis最適化警告: {e}")
    
    def _start_lightweight_wm(self, display: str):
        """軽量ウィンドウマネージャーを起動（安全モード）"""
        print("🪟 ウィンドウマネージャーを起動中...")
        
        env = dict(os.environ, DISPLAY=display)
        
        # より安全な起動順序
        window_managers = [
            ('twm', '最小限WM'),           # 最も安全
            ('openbox', '軽量WM'),         # 2番目に安全  
            ('fluxbox', '代替軽量WM'),     # 3番目
            ('jwm', 'Java WM')             # 最後の選択肢
        ]
        
        for wm, desc in window_managers:
            try:
                # WMの存在チェック
                check_result = subprocess.run(['which', wm], capture_output=True, timeout=3)
                if check_result.returncode == 0:
                    print(f"🔧 {desc}（{wm}）を起動中...")
                    
                    # 既存のWMプロセスを確認
                    existing = subprocess.run(['pgrep', wm], capture_output=True)
                    if existing.returncode == 0:
                        print(f"⚠️ {wm}は既に起動済み")
                        continue
                    
                    # WMを起動
                    process = subprocess.Popen([wm], env=env, 
                                             stdout=subprocess.DEVNULL, 
                                             stderr=subprocess.DEVNULL)
                    
                    # 短時間待機して起動確認
                    time.sleep(1.5)
                    
                    if process.poll() is None:  # プロセスがまだ動いている
                        print(f"✅ {desc}起動成功: {wm}")
                        
                        # 基本的な背景色を設定（灰色画面対策）
                        try:
                            subprocess.run(['xsetroot', '-solid', '#2e3440'], 
                                         env=env, capture_output=True, timeout=2)
                        except:
                            pass
                        
                        return True
                    else:
                        print(f"❌ {wm}起動失敗")
                        
            except Exception as e:
                print(f"⚠️ {wm}起動エラー: {e}")
                continue
        
        # フォールバック: 背景色だけ設定
        print("⚠️ WM起動失敗 - 基本設定のみ適用")
        try:
            subprocess.run(['xsetroot', '-solid', '#404040'], 
                         env=env, capture_output=True, timeout=2)
            print("✅ 背景色設定完了")
        except:
            print("❌ 背景色設定も失敗")
        
        return False
    
    def _verify_display_working(self, display: str):
        """VNC表示が正常に動作しているか確認"""
        print("🔍 VNC表示状態を確認中...")
        
        env = dict(os.environ, DISPLAY=display)
        
        try:
            # X11サーバーの応答確認
            result = subprocess.run(['xdpyinfo'], env=env, 
                                  capture_output=True, timeout=5)
            
            if result.returncode == 0:
                print("✅ X11サーバー応答: 正常")
                
                # 簡単なテストウィンドウを表示
                try:
                    subprocess.run(['xterm', '-e', 'echo "VNC表示テスト"; sleep 2'], 
                                 env=env, capture_output=True, timeout=8)
                    print("✅ テストウィンドウ: 表示可能")
                except:
                    print("⚠️ テストウィンドウ: 表示できませんが継続")
                    
            else:
                print("❌ X11サーバー応答: 異常")
                print("💡 VNCサーバーの再起動が必要かもしれません")
                
        except subprocess.TimeoutExpired:
            print("⏰ 表示確認タイムアウト")
        except Exception as e:
            print(f"⚠️ 表示確認エラー: {e}")
    
    def _configure_vnc_scroll(self, display: str):
        """VNCスクロール機能を設定（安全モード）"""
        print("🖱️ VNCスクロール設定中...")
        
        try:
            # 安全なマウスホイール設定のみ
            env = dict(os.environ, DISPLAY=display)
            
            # 基本的なマウス設定（エラーが出ても続行）
            try:
                subprocess.run(['xmodmap', '-e', 'pointer = 1 2 3 4 5'], 
                             env=env, capture_output=True, timeout=3)
            except:
                pass  # エラーを無視して続行
            
            print("✅ VNCスクロール設定完了（基本設定）")
            
        except Exception as e:
            print(f"⚠️ スクロール設定をスキップ: {e}")
    
    def _setup_japanese_input(self, display: str):
        """日本語入力環境の設定"""
        print(f"🇯🇵 日本語入力環境をセットアップ中... (ディスプレイ: {display})")
        
        try:
            # 環境変数設定
            env = os.environ.copy()
            env['DISPLAY'] = display
            env['GTK_IM_MODULE'] = 'ibus'
            env['QT_IM_MODULE'] = 'ibus'
            env['XMODIFIERS'] = '@im=ibus'
            
            # ibus-daemon起動
            subprocess.Popen(
                ['ibus-daemon', '-drx'],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # 少し待ってからmozc-jp設定
            time.sleep(2)
            
            # mozc-jp エンジン設定
            subprocess.Popen(
                ['ibus', 'engine', 'mozc-jp'],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            print("✅ 日本語入力設定完了 (Ctrl+Space で切り替え)")
            
        except Exception as e:
            print(f"⚠️ 日本語入力設定エラー: {e}")
            print("💡 手動設定: DISPLAY=:X ibus engine mozc-jp &")
    
    def _setup_vnc_password(self):
        """VNCパスワードの設定（x11vnc用 - パスワード不要）"""
        print("🔑 x11vncはパスワード不要モード（-nopw）で起動します")
    
    def _is_display_in_use(self, display: str) -> bool:
        """ディスプレイが使用中かチェック"""
        try:
            result = subprocess.run(
                ['xdpyinfo', '-display', display],
                capture_output=True,
                timeout=3
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _start_virtual_display(self) -> Optional[str]:
        """仮想ディスプレイ（Xvfb）とVNCサーバーの統合起動"""
        print("🖼️ 仮想ディスプレイを起動中...")
        
        try:
            for display_num in range(10, 100):
                display = f":{display_num}"
                
                if self._is_display_in_use(display):
                    print(f"🔍 ディスプレイ {display} は使用中をスキップ")
                    continue
                
                print(f"📺 仮想ディスプレイ {display} の起動を試行中...")
                
                # Xvfb起動
                xvfb_cmd = [
                    'Xvfb', display,
                    '-screen', '0', f"{self.default_geometry}x{self.default_depth}",
                    '-ac', '+extension', 'GLX'
                ]
                
                print(f"🔧 Xvfbコマンド実行: {' '.join(xvfb_cmd)}")
                xvfb_process = subprocess.Popen(
                    xvfb_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                # 起動待ち
                print(f"⏳ Xvfb {display} の起動確認を待機中...")
                time.sleep(3)
                
                if self._test_display_connection(display):
                    print(f"✅ 仮想ディスプレイ起動成功: {display}")
                    
                    # VNCサーバーを起動（同じディスプレイ上で）
                    print(f"🚀 VNCサーバーを {display} で起動中...")
                    vnc_success = self._start_vnc_on_display(display)
                    
                    if vnc_success:
                        # プロセスIDを記録
                        self._save_virtual_display_pid(display, xvfb_process.pid)
                        return display
                    else:
                        print(f"❌ VNCサーバー起動失敗: {display}")
                        xvfb_process.terminate()
                else:
                    print(f"❌ 仮想ディスプレイ接続失敗: {display}")
                    xvfb_process.terminate()
                    
        except Exception as e:
            print(f"❌ 仮想ディスプレイ起動エラー: {e}")
        
        return None
    
    def _start_vnc_on_display(self, display: str) -> bool:
        """既存のディスプレイ上でVNCサーバーを起動"""
        try:
            # VNC起動コマンド（x11vncを使用してXvfbに接続）
            # 遅延改善のための最適化パラメータを追加
            vnc_cmd = [
                'x11vnc',
                '-display', display,
                '-forever',
                '-nopw',  # パスワード不要（ローカル開発用）
                '-shared',
                '-rfbport', '5900',  # 標準ポート
                '-geometry', self.default_geometry,
                # 遅延改善パラメータ
                '-wait', '20',          # ポーリング間隔（デフォルト20ms）
                '-defer', '20',         # 更新遅延（20ms）
                '-noxrecord',           # XRECORDエクステンション無効
                '-noxfixes',            # XFIXESエクステンション無効
                '-noxdamage',           # XDAMAGEエクステンション無効
                '-threads',             # マルチスレッド処理
                '-fixscreen', '5',      # 5秒毎に画面修復
                '-ncache', '0',         # キャッシュ無効（メモリ節約）
                '-speeds', 'modem',     # 低帯域モード
                '-nodpms',              # 電源管理無効
                '-nobell'               # ベル音無効
            ]
            
            print(f"🔧 VNCコマンド実行（最適化版）: {' '.join(vnc_cmd)}")
            vnc_process = subprocess.Popen(
                vnc_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # VNC起動確認
            time.sleep(2)
            if vnc_process.poll() is None:  # プロセスが生きている
                print(f"✅ VNCサーバー起動成功（最適化済み）: {display} (ポート5900)")
                return True
            else:
                print(f"❌ VNCプロセス異常終了: {display}")
                return False
                
        except Exception as e:
            print(f"❌ VNC起動エラー: {e}")
            return False
    
    def _test_display_connection(self, display: str) -> bool:
        """ディスプレイ接続テスト"""
        try:
            result = subprocess.run(
                ['xdpyinfo', '-display', display],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _save_vnc_config(self, display: str, is_virtual: bool = False):
        """VNC設定の保存"""
        config = {
            'display': display,
            'is_virtual': is_virtual,
            'geometry': self.default_geometry,
            'depth': self.default_depth,
            'created_at': time.time()
        }
        
        with open(self.vnc_config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"💾 VNC設定を保存しました: {self.vnc_config_file}")
    
    def _save_virtual_display_pid(self, display: str, pid: int):
        """仮想ディスプレイのPID記録"""
        pid_file = Path.home() / f".genesis_virtual_display_{display[1:]}.pid"
        with open(pid_file, 'w') as f:
            f.write(str(pid))
    
    def load_vnc_config(self) -> Optional[Dict]:
        """保存されたVNC設定の読み込み"""
        if not self.vnc_config_file.exists():
            return None
        
        try:
            with open(self.vnc_config_file, 'r') as f:
                config = json.load(f)
            
            # 設定の有効性確認
            if self._test_display_connection(config['display']):
                return config
            else:
                print(f"⚠️ 保存されたディスプレイ {config['display']} は利用できません")
                return None
                
        except Exception as e:
            print(f"⚠️ VNC設定読み込みエラー: {e}")
            return None
    
    def stop_vnc_services(self):
        """VNCサービスの停止（x11vnc + Xvfb対応）"""
        print("🛑 VNCサービスを停止中...")
        
        # 設定ファイルからディスプレイ情報取得
        config = self.load_vnc_config()
        
        if config:
            display = config['display']
            print(f"🎯 ディスプレイ {display} のサービスを停止中...")
            
            # x11vncプロセスの停止
            self._stop_x11vnc_process()
            
            # Xvfbプロセスの停止
            self._stop_xvfb_process(display)
        else:
            # 設定ファイルがない場合でも全プロセス停止を試行
            print("⚠️ 設定ファイルなし - 全プロセス停止を試行")
            self._stop_all_vnc_processes()
        
        # 設定ファイル削除
        if self.vnc_config_file.exists():
            self.vnc_config_file.unlink()
            print("🗑️ VNC設定ファイルを削除しました")
    
    def _stop_x11vnc_process(self):
        """x11vncプロセスの停止"""
        try:
            result = subprocess.run(['pkill', '-f', 'x11vnc'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ x11vncプロセスを停止しました")
            else:
                print("⚠️ x11vncプロセスが見つかりませんでした")
        except Exception as e:
            print(f"❌ x11vnc停止エラー: {e}")
    
    def _stop_xvfb_process(self, display: str):
        """Xvfbプロセスの停止"""
        try:
            # 該当ディスプレイのXvfbプロセスを検索
            result = subprocess.run(['pgrep', '-f', f'Xvfb {display}'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        subprocess.run(['kill', pid], check=True)
                        print(f"✅ Xvfbプロセス ({display}) を停止しました (PID: {pid})")
                    except subprocess.CalledProcessError:
                        print(f"⚠️ Xvfbプロセス停止失敗 (PID: {pid})")
            else:
                print(f"⚠️ Xvfbプロセス ({display}) が見つかりませんでした")
        except Exception as e:
            print(f"❌ Xvfb停止エラー: {e}")
    
    def _stop_all_vnc_processes(self):
        """全てのVNC関連プロセスを停止"""
        print("🔄 全VNC関連プロセスの停止を試行中...")
        
        # x11vncプロセス停止
        try:
            subprocess.run(['pkill', '-f', 'x11vnc'], capture_output=True)
            print("✅ 全x11vncプロセスを停止しました")
        except Exception:
            pass
        
        # Xvfbプロセス停止
        try:
            subprocess.run(['pkill', '-f', 'Xvfb'], capture_output=True)
            print("✅ 全Xvfbプロセスを停止しました")
        except Exception:
            pass
    
    def _check_x11vnc_process(self, display: str) -> bool:
        """x11vncプロセスが指定ディスプレイで実行中かチェック"""
        try:
            result = subprocess.run(['pgrep', '-f', f'x11vnc.*{display}'], capture_output=True, text=True)
            return result.returncode == 0 and result.stdout.strip()
        except Exception:
            return False
    
    def show_status(self):
        """VNC環境状況の表示（x11vnc + Xvfb対応）"""
        print("📊 VNC環境状況:")
        
        # 設定ファイル確認
        config = self.load_vnc_config()
        if config:
            print(f"💾 保存設定: {config['display']} (仮想ディスプレイ)")
            
            if self._test_display_connection(config['display']):
                print(f"✅ ディスプレイ {config['display']} は利用可能")
                
                # x11vncプロセス確認
                vnc_running = self._check_x11vnc_process(config['display'])
                if vnc_running:
                    print(f"✅ x11vncサーバー動作中: ポート5900")
                else:
                    print(f"⚠️ x11vncサーバー停止中")
            else:
                print(f"❌ ディスプレイ {config['display']} は利用不可")
        else:
            print("⚠️ VNC設定なし")
        
        # 実行中のXvfbプロセス一覧
        print("🖥️ 実行中Xvfbプロセス:")
        try:
            result = subprocess.run(['pgrep', '-a', 'Xvfb'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    print(f"   {line}")
            else:
                print("   なし")
        except Exception:
            print("   確認できませんでした")
        
        # 実行中のx11vncプロセス一覧
        print("� 実行中x11vncプロセス:")
        try:
            result = subprocess.run(['pgrep', '-a', 'x11vnc'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    print(f"   {line}")
            else:
                print("   なし")
        except Exception:
            print("   確認できませんでした")
        
        # 環境変数確認
        display_env = os.environ.get('DISPLAY')
        print(f"🔧 現在のDISPLAY環境変数: {display_env or '未設定'}")
    
    def get_recommended_display(self) -> Optional[str]:
        """推奨ディスプレイ設定を取得"""
        config = self.load_vnc_config()
        if config and self._test_display_connection(config['display']):
            return config['display']
        
        # 自動セットアップを試行
        return self.setup_vnc_environment()
    
    def test_genesis_display(self, display: str = None) -> bool:
        """Genesis表示テストを実行"""
        if not display:
            display = os.environ.get('DISPLAY', ':1')
        
        print(f"🧪 Genesis表示テスト開始 (ディスプレイ: {display})")
        
        # Xvfb + x11vncが起動しているかチェック
        xvfb_running = subprocess.run(['pgrep', 'Xvfb'], capture_output=True).returncode == 0
        x11vnc_running = subprocess.run(['pgrep', 'x11vnc'], capture_output=True).returncode == 0
        
        if not (xvfb_running and x11vnc_running):
            print("❌ VNCサーバー（Xvfb + x11vnc）が起動していません")
            print("💡 先に 'python start_vnc.py --start' を実行してください")
            return False
        
        # Genesis表示テストコード
        test_code = f"""
import os
os.environ['DISPLAY'] = '{display}'
os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
os.environ['__GL_SYNC_TO_VBLANK'] = '0'

try:
    import genesis as gs
    gs.init()
    scene = gs.Scene(show_viewer=True)
    plane = scene.add_entity(gs.morphs.Plane())
    sphere = scene.add_entity(gs.morphs.Sphere(pos=(0, 0, 2.0)))
    scene.build()
    
    for i in range(10):
        scene.step()
        if i % 5 == 0:
            print(f"Genesis テスト ステップ {{i}}/10")
    
    print("✅ Genesis VNC表示テスト成功!")
    
except Exception as e:
    print(f"❌ Genesis表示テストエラー: {{e}}")
    exit(1)
"""
        
        try:
            result = subprocess.run(['python3', '-c', test_code], 
                                  capture_output=True, text=True, timeout=60)
            print(result.stdout)
            if result.stderr:
                print(f"⚠️ 警告: {result.stderr}")
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            return False
    
    def _show_scroll_troubleshooting(self):
        """VNCスクロール設定のトラブルシューティング情報を表示"""
        print("\n📋 VNCスクロールが動かない場合の対処法:")
        
        # 現在のディスプレイを取得
        display = os.environ.get('DISPLAY', ':1')
        
        try:
            
            print("\n📋 VNCクライアント側の設定確認:")
            print("1. VNC Viewerの設定:")
            print("   - 右クリック → Options → Input")
            print("   - 'Enable mouse wheel scrolling' をオン")
            print("   - 'Pass special keys to VNC server' をオン")
            
            print("\n2. 使用VNCクライアント別設定:")
            print("   【TightVNC Viewer】")
            print("   - Encoding: Tight")
            print("   - 'ViewOnly' をオフ")
            
            print("   【RealVNC Viewer】") 
            print("   - Quality: High")
            print("   - 'Enable hardware cursor' をオン")
            
            print("   【TigerVNC Viewer】")
            print("   - RemoteResize: On")
            print("   - FullScreen: Off（推奨）")
            
            print("\n3. ブラウザVNCの場合:")
            print("   - ブラウザのズーム: 100%")
            print("   - JavaScript有効")
            print("   - ポップアップブロック無効")
            
            # マウス設定テスト
            print("\n🧪 マウス設定テスト実行中...")
            env = dict(os.environ, DISPLAY=display)
            
            test_commands = [
                (['xinput', 'list'], "入力デバイス一覧"),
                (['xmodmap', '-pp'], "ポインターマッピング"),
                (['xinput', 'list-props', 'pointer:'], "ポインター設定")
            ]
            
            for cmd, desc in test_commands:
                try:
                    result = subprocess.run(cmd, env=env, capture_output=True, 
                                          text=True, timeout=10)
                    print(f"✅ {desc}: OK")
                    if "pointer" in cmd[0]:
                        # ポインター情報の表示（簡略版）
                        lines = result.stdout.split('\n')[:3]
                        for line in lines:
                            if line.strip():
                                print(f"   {line.strip()}")
                except Exception as e:
                    print(f"⚠️ {desc}: {e}")
            
            print(f"\n💡 トラブルシューティング:")
            print(f"1. VNCクライアントを再接続してください")
            print(f"2. 接続URL: vnc://localhost:590{display[1:]}")
            print(f"3. まだ問題がある場合: python start_vnc.py --start")
            
        except Exception as e:
            print(f"❌ スクロール修正エラー: {e}")

def main():
    parser = argparse.ArgumentParser(description='Genesis VNC環境管理')
    parser.add_argument('--start', action='store_true', help='VNC環境をセットアップ（Genesis最適化含む）')
    parser.add_argument('--stop', action='store_true', help='VNCサービスを停止')
    parser.add_argument('--status', action='store_true', help='VNC状況を表示')
    parser.add_argument('--cleanup', action='store_true', help='全てクリーンアップ')
    parser.add_argument('--display', action='store_true', help='推奨ディスプレイ設定を表示')
    parser.add_argument('--genesis-test', action='store_true', help='Genesis表示テストを実行')
    
    args = parser.parse_args()
    manager = VNCManager()
    
    if args.stop:
        manager.stop_vnc_services()
    elif args.status:
        manager.show_status()
    elif args.cleanup:
        manager.stop_vnc_services()
        print("🧹 クリーンアップ完了")
    elif args.display:
        display = manager.get_recommended_display()
        if display:
            print(f"推奨DISPLAY設定: {display}")
        else:
            print("利用可能なディスプレイなし")
    elif args.genesis_test:
        manager.test_genesis_display()
    else:
        # デフォルトまたは--start
        display = manager.setup_vnc_environment()
        if display:
            print(f"\n🎉 VNC環境セットアップ完了!")
            print(f"📺 ディスプレイ: {display}")
            print(f"🔧 環境変数設定: export DISPLAY={display}")
            print(f"🖱️ スクロール設定: 自動適用済み")
            print(f"💡 スクロールが効かない場合: VNCクライアントでマウスホイール有効化")
            print("\n🚀 Genesis Clientを起動してください:")
            print("python genesis_client.py --interactive")
        else:
            print("❌ VNC環境のセットアップに失敗しました")
            return 1
    
    return 0

if __name__ == '__main__':
    exit(main())