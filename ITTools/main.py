"""
IT Tool LTT - Windows System Management Utility 2026
Author: Lê Thế Tuấn
Phone/Zalo: 0352 194 195
Website: https://lethetuanpc.blogspot.com
Telegram: https://t.me/lethetuanpc
Version: 1.0.0
"""

import sys
import os
import ctypes
import subprocess

def patch_silent_subprocess():
    """Globally configures subprocess on Windows to:
    1. Never flash console or PowerShell windows (CREATE_NO_WINDOW).
    2. Enforce UTF-8 encoding with errors='replace' for text mode to avoid
       UnicodeDecodeError on non-UTF8 locales (e.g. cp1258 on Vietnamese Windows).
    """
    if sys.platform != 'win32':
        return
    if getattr(subprocess, '_ittools_silent_patched', False):
        return
    subprocess._ittools_silent_patched = True

    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        if hasattr(sys.stdout, 'reconfigure') and sys.stdout:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure') and sys.stderr:
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    orig_init = subprocess.Popen.__init__

    def silent_init(self, *args, **kwargs):
        # 0x08000000 = CREATE_NO_WINDOW
        flags = kwargs.get('creationflags', 0)
        flags |= 0x08000000
        kwargs['creationflags'] = flags

        # Check if text mode is requested
        is_text = kwargs.get('text') or kwargs.get('universal_newlines')
        if not is_text and len(args) > 11 and args[11]:
            is_text = True
        if not is_text and ('encoding' in kwargs or 'errors' in kwargs):
            is_text = True

        if is_text:
            if not kwargs.get('encoding'):
                kwargs['encoding'] = 'utf-8'
            if not kwargs.get('errors'):
                kwargs['errors'] = 'replace'

        orig_init(self, *args, **kwargs)

    subprocess.Popen.__init__ = silent_init

patch_silent_subprocess()

# Determine base directory (supports PyInstaller --onefile extracted path)
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Dedicated Native Zoom Screen GUI Subprocess Dispatcher
if len(sys.argv) > 1 and sys.argv[1] == '--zoom-screen':
    from modules import zoom_screen_gui
    mode = sys.argv[2] if len(sys.argv) > 2 else 'zoom'
    cx = sys.argv[3] if len(sys.argv) > 3 else None
    cy = sys.argv[4] if len(sys.argv) > 4 else None
    zoom_screen_gui.main(mode, cx, cy)
    sys.exit(0)

import socket
import threading

from constants import APP_NAME, APP_VERSION, APP_AUTHOR, APP_PHONE, SINGLE_INSTANCE_PORT
from web_api import Api

WIN_TITLE = f"{APP_NAME} 2026 ver {APP_VERSION} - {APP_AUTHOR} | Zalo: {APP_PHONE}"

def activate_existing_instance(port=SINGLE_INSTANCE_PORT, win_title=WIN_TITLE):
    """
    Checks if an instance of IT Tool LTT is already running.
    If running (minimized, hidden in tray, or in background):
    signals it to restore and bring to front, then returns True.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect(('127.0.0.1', port))
        try:
            ctypes.windll.user32.AllowSetForegroundWindow(-1)
        except Exception:
            pass
        s.sendall(b"ACTIVATE_WINDOW\n")
        try:
            s.recv(1024)
        except Exception:
            pass
        s.close()

        # Also directly attempt to restore and foreground window via Win32 API
        if win_title:
            try:
                user32 = ctypes.windll.user32
                hwnd = user32.FindWindowW(None, win_title)
                if hwnd:
                    user32.AllowSetForegroundWindow(-1)
                    if user32.IsIconic(hwnd):
                        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                    else:
                        user32.ShowWindow(hwnd, 5)  # SW_SHOW
                        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                    user32.SetForegroundWindow(hwnd)
                    user32.BringWindowToTop(hwnd)
            except Exception:
                pass
        return True
    except Exception:
        return False

def start_single_instance_server(wake_callback, port=SINGLE_INSTANCE_PORT):
    """Starts background IPC listener to restore window when a new instance is launched."""
    def server_loop():
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind(('127.0.0.1', port))
            server.listen(5)
        except Exception as e:
            print(f"IPC Server could not bind port {port}: {e}")
            return

        while True:
            try:
                conn, _ = server.accept()
                data = conn.recv(1024)
                if b"ACTIVATE" in data:
                    try:
                        wake_callback()
                    except Exception as ex:
                        print(f"Wake callback error: {ex}")
                    try:
                        conn.sendall(b"OK\n")
                    except Exception:
                        pass
                conn.close()
            except Exception:
                pass

    t = threading.Thread(target=server_loop, daemon=True)
    t.start()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def run_as_admin():
    """Re-launches the app with Administrator privileges.
    Returns True if elevation was successfully requested, False otherwise.
    """
    if sys.platform != 'win32':
        return False
    try:
        # lpDirectory: working directory for the elevated process
        # Must be set explicitly; otherwise defaults to C:\Windows\System32
        work_dir = BASE_DIR

        if getattr(sys, 'frozen', False):
            # Frozen (PyInstaller .exe): re-launch the exe itself
            params = " ".join(f'"{a}"' for a in sys.argv[1:])
            hinstance = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, params or None, work_dir, 1
            )
        else:
            # Running as plain Python script
            script = os.path.abspath(sys.argv[0])
            extra = " ".join(f'"{a}"' for a in sys.argv[1:])
            params = f'"{script}"' + (f' {extra}' if extra else '')
            hinstance = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, params, work_dir, 1
            )

        # ShellExecuteW returns > 32 on success, <= 32 on error
        if hinstance <= 32:
            # User likely clicked "No" on UAC or an error occurred
            ctypes.windll.user32.MessageBoxW(
                0,
                "Không thể nâng cấp quyền Administrator.\n\n"
                "Ứng dụng sẽ tiếp tục chạy với quyền hạn hiện tại.\n"
                "Một số tính năng có thể bị hạn chế.",
                "IT Tool LTT - Cảnh báo",
                0x30  # MB_ICONWARNING
            )
            return False
        return True
    except Exception as ex:
        print(f"[run_as_admin] Error: {ex}")
        return False

def is_webview2_runtime_installed():
    """
    Kiem tra su ton tai cua Microsoft Edge WebView2 Runtime tren Windows.
    Tra ve True neu da cai dat day du, False neu thieu.
    """
    if sys.platform != 'win32':
        return True

    # 1. Kiem tra truc tiep thong qua co is_chromium cua winforms pywebview
    try:
        import webview.platforms.winforms as wf
        if getattr(wf, 'is_chromium', None) is False:
            return False
        if getattr(wf, 'is_chromium', None) is True:
            return True
    except Exception:
        pass

    # 2. Quet cac khoa Windows Registry chinh thuc cua Microsoft Edge WebView2 Runtime
    try:
        import winreg
        guid_keys = [
            r'{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}',  # WebView2 Evergreen Runtime
            r'{2CD8A007-E189-409D-A2C8-9AF4EF3C72AA}',  # Edge Beta
            r'{0D50BFEC-CD6A-4F9A-964C-C7416E3ACB10}',  # Edge Dev
            r'{65C35B14-6C1D-4122-AC46-7148CC9D6497}',  # Edge Canary
        ]
        reg_paths = [
            r'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients',
            r'SOFTWARE\Microsoft\EdgeUpdate\Clients'
        ]
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for path in reg_paths:
                for guid in guid_keys:
                    try:
                        with winreg.OpenKey(root, f"{path}\\{guid}") as key:
                            val, _ = winreg.QueryValueEx(key, 'pv')
                            if val and val.strip() and val != '0.0.0.0' and val != '0':
                                return True
                    except Exception:
                        pass
    except Exception:
        pass

    return False

def handle_missing_webview2():
    """
    Thong bao cho nguoi dung khi may thieu Microsoft Edge WebView2 Runtime.
    Ho tro tu dong tai va chay bo cai dat Evergreen Bootstrapper tu Microsoft,
    hoac mo trang tai chinh thuc neu khong the tai tu dong.
    Ngan chan ung dung chay tren Internet Explorer (MSHTML) lam vo giao dien va chet script.
    """
    msg = (
        "PHÁT HIỆN THIẾU THÀNH PHẦN HỆ THỐNG:\n\n"
        "Máy tính của bạn chưa có 'Microsoft Edge WebView2 Runtime'.\n\n"
        "Nếu thiếu WebView2, giao diện IT Tool LTT sẽ bị lỗi vỡ khung (bị rơi vào trình duyệt cũ IE11) "
        "và các tính năng không thể hoạt động.\n\n"
        "Bạn có muốn tải và cài đặt Microsoft Edge WebView2 ngay bây giờ không?\n\n"
        "• Bấm 'Yes' (Có): Tự động tải và chạy bộ cài đặt chính thức từ Microsoft.\n"
        "• Bấm 'No' (Không): Thoát ứng dụng để cài đặt sau."
    )
    res = ctypes.windll.user32.MessageBoxW(
        0,
        msg,
        "IT Tool LTT - Yêu cầu Microsoft Edge WebView2",
        0x34  # MB_YESNO | MB_ICONWARNING
    )
    if res == 6:  # IDYES
        bootstrapper_url = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"
        import tempfile
        import urllib.request
        import webbrowser

        installer_path = os.path.join(tempfile.gettempdir(), "MicrosoftEdgeWebview2Setup.exe")
        downloaded = False
        try:
            req = urllib.request.Request(
                bootstrapper_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp, open(installer_path, "wb") as f:
                f.write(resp.read())

            if os.path.exists(installer_path) and os.path.getsize(installer_path) > 10000:
                downloaded = True
                subprocess.Popen([installer_path, "/install"])
                ctypes.windll.user32.MessageBoxW(
                    0,
                    "Bộ cài đặt Microsoft Edge WebView2 đã được kích hoạt!\n\n"
                    "Vui lòng đợi 1 - 2 phút để Windows hoàn tất cài đặt (yêu cầu có kết nối Internet),\n"
                    "sau đó khởi động lại IT Tool LTT.",
                    "IT Tool LTT - Đang cài đặt",
                    0x40  # MB_ICONINFORMATION
                )
        except Exception as ex:
            print(f"[WebView2] Auto-download failed: {ex}")
            downloaded = False

        if not downloaded:
            webbrowser.open("https://developer.microsoft.com/en-us/microsoft-edge/webview2/")
            ctypes.windll.user32.MessageBoxW(
                0,
                "Trình duyệt đã được mở tới trang tải Microsoft Edge WebView2.\n\n"
                "Vui lòng tải 'Evergreen Bootstrapper' hoặc 'Standalone Installer', "
                "tiến hành cài đặt rồi mở lại IT Tool LTT.",
                "IT Tool LTT - Hướng dẫn tải",
                0x40  # MB_ICONINFORMATION
            )

    sys.exit(0)

def main():
    # Handle standalone module GUI requests (e.g. --module boot_manager)
    if "--module" in sys.argv:
        try:
            idx = sys.argv.index("--module")
            if idx + 1 < len(sys.argv):
                mod_name = sys.argv[idx + 1]
                import tkinter as tk
                root = tk.Tk()
                icon_path = os.path.join(BASE_DIR, "assets", "tray_icon.ico")
                if os.path.exists(icon_path):
                    try:
                        root.iconbitmap(icon_path)
                    except Exception:
                        pass
                if mod_name == "boot_manager":
                    from modules.boot_manager import BootManager
                    root.title("⚙️ Boot Manager")
                    BootManager(root)
                elif mod_name == "server_tools":
                    from modules.server_tools import ServerTools
                    root.title("🖧 Server Tools")
                    ServerTools(root)
                else:
                    root.destroy()
                    print(f"[--module] Unknown module: '{mod_name}'. Valid: boot_manager, server_tools")
                    sys.exit(1)
                    return
                root.mainloop()
                return
        except Exception as e:
            print(f"Error opening module GUI: {e}")

    # 1. Single Instance Check:
    # If app is already open (minimized, in tray, or in background), restore it and exit
    if activate_existing_instance(port=SINGLE_INSTANCE_PORT, win_title=WIN_TITLE):
        sys.exit(0)

    # 2. Elevate to administrator if needed
    if not is_admin():
        elevated = run_as_admin()
        if elevated:
            # Successfully requested elevation — exit current (non-admin) instance
            sys.exit(0)
        # else: user denied UAC or elevation failed — continue running without admin

    # 3. Kiem tra moi truong Microsoft Edge WebView2 Runtime truoc khi mo giao dien Web
    if not is_webview2_runtime_installed():
        handle_missing_webview2()
        return

    # Launch PyWebView Modern Desktop Window
    web_index = os.path.join(BASE_DIR, "web", "index.html")

    try:
        import webview
        from tray_manager import TrayManager

        api = Api()
        window = webview.create_window(
            title=WIN_TITLE,
            url=web_index,
            js_api=api,
            width=1280,
            height=800,
            min_size=(1024, 680),
            resizable=True
        )

        # Tích hợp System Tray: Thu nhỏ xuống khay Taskbar khi bấm dấu X màu đỏ
        tray = TrayManager(window=window, window_title=WIN_TITLE)
        window.events.closing += tray.on_window_closing

        api._tray = tray

        # Khởi động IPC Server để lắng nghe tín hiệu đánh thức từ các lần mở sau
        def wake_up_callback():
            tray.show_window()

        start_single_instance_server(wake_up_callback, port=SINGLE_INSTANCE_PORT)

        # Tự động kích hoạt lắng nghe phím tắt toàn cầu của Zoom Screen ngay khi khởi động
        # Giúp phím tắt luôn hoạt động mọi lúc kể cả khi tool chạy ngầm, thu nhỏ hoặc ở khay hệ thống
        try:
            from modules import zoom_screen
            zoom_screen.start_zoomit(silent=True)
        except Exception as ex:
            print(f"[ZoomScreen] Auto-start hotkeys warning: {ex}")

        # Khởi chạy giao diện Web và tự động kích hoạt Tray icon khi Webview sẵn sàng
        webview.start(tray.start, debug=False, gui='edgechromium')
    except Exception as ex:
        try:
            ctypes.windll.user32.MessageBoxW(
                0,
                f"Lỗi khởi động giao diện Web IT Tool LTT:\n\n{ex}\n\nVui lòng kiểm tra lại môi trường Windows / WebView2 Runtime.",
                "IT Tool LTT - Lỗi",
                0x10
            )
        except Exception:
            pass

if __name__ == "__main__":
    main()
