"""
IT-Tools - Windows System Management Utility 2026
Author: Lê Thế Tuấn
Phone/Zalo: 0352 194 195
Website: https://lethetuanpc.blogspot.com/
Version: 1.0.0
"""

import sys
import os
import ctypes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from constants import APP_NAME, APP_VERSION, APP_AUTHOR, APP_PHONE
from web_api import Api

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def run_as_admin():
    if sys.platform == 'win32':
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{sys.argv[0]}"', None, 1
            )
        except Exception:
            pass

def main():
    # Attempt to launch PyWebView Modern Desktop Window
    web_index = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "index.html")
    
    try:
        import webview
        api = Api()
        window = webview.create_window(
            title=f"{APP_NAME} 2026 ver {APP_VERSION} - {APP_AUTHOR}",
            url=web_index,
            js_api=api,
            width=1280,
            height=800,
            min_size=(1024, 680),
            resizable=True
        )
        webview.start(debug=False)
    except Exception as ex:
        print(f"PyWebView failed: {ex}. Falling back to Tkinter...")
        import tkinter as tk
        from ui.main_window import MainWindow
        root = tk.Tk()
        app = MainWindow(root)
        root.mainloop()

if __name__ == "__main__":
    main()
