"""
IT Tool LTT - System Tray (Taskbar Notification Area) Manager
Author: Lê Thế Tuấn | Hotline/Zalo: 0352 194 195
Website: https://lethetuanpc.blogspot.com | Telegram: https://t.me/lethetuanpc
"""

import os
import sys
import threading
import ctypes
import webbrowser

try:
    import clr
    clr.AddReference('System.Windows.Forms')
    clr.AddReference('System.Drawing')
    from System.Windows.Forms import (
        NotifyIcon, ContextMenuStrip, ToolStripMenuItem, ToolStripSeparator,
        Application, ToolTipIcon, MouseButtons
    )
    from System.Drawing import Icon, Bitmap, SystemIcons, Font, FontStyle, FontFamily
    CLR_AVAILABLE = True
except Exception as e:
    CLR_AVAILABLE = False
    print(f"Warning: CLR Windows Forms not available for TrayManager: {e}")

from constants import APP_NAME, APP_VERSION, APP_AUTHOR, APP_PHONE, APP_WEBSITE, APP_TELEGRAM

user32 = ctypes.windll.user32


class TrayManager:
    def __init__(self, window=None, window_title=""):
        self.window = window
        self.window_title = window_title
        self.notify = None
        self.is_quitting = False
        self.is_hidden = False
        self.tray_thread = None
        self._first_minimize_notified = False

    def get_icon_path(self):
        """Locates the tray icon file (supporting PyInstaller frozen path)."""
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        
        candidates = [
            os.path.join(base_dir, 'assets', 'tray_icon.png'),
            os.path.join(base_dir, 'assets', 'tray_icon.ico'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'tray_icon.png'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'tray_icon.ico'),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def start(self, window=None, window_title=None):
        """Initializes and runs the System Tray icon in a dedicated daemon thread."""
        if window:
            self.window = window
        if window_title:
            self.window_title = window_title

        if not CLR_AVAILABLE:
            return

        self.tray_thread = threading.Thread(target=self._run_tray_loop, daemon=True)
        self.tray_thread.start()

    def _run_tray_loop(self):
        try:
            self.notify = NotifyIcon()

            # Load custom icon
            icon_path = self.get_icon_path()
            if icon_path and os.path.exists(icon_path):
                try:
                    bmp = Bitmap(icon_path)
                    h_icon = bmp.GetHicon()
                    loaded_icon = Icon.FromHandle(h_icon)
                    self.notify.Icon = loaded_icon
                    # Set icon on all PyWebView window forms
                    try:
                        for f in Application.OpenForms:
                            f.Icon = loaded_icon
                    except Exception:
                        pass
                except Exception as ex:
                    print(f"Lỗi load icon tray: {ex}")
                    self.notify.Icon = SystemIcons.Application
            else:
                self.notify.Icon = SystemIcons.Application

            # Text limited to 63 chars on Windows
            tip_text = f"{APP_NAME} - {APP_AUTHOR}"
            if len(tip_text) > 63:
                tip_text = tip_text[:63]
            self.notify.Text = tip_text

            # Create context menu
            menu = ContextMenuStrip()

            # Item 1: Mở giao diện chính
            item_open = menu.Items.Add("🚀 Mở IT Tool LTT")

            def on_open_click(sender, args):
                self.show_window()

            item_open.Click += on_open_click

            # Item 2: Thu nhỏ / Ẩn
            item_hide = ToolStripMenuItem("🔽 Thu nhỏ xuống Taskbar")

            def on_hide_click(sender, args):
                self.hide_window()

            item_hide.Click += on_hide_click
            menu.Items.Add(item_hide)

            menu.Items.Add(ToolStripSeparator())

            # Item 3: Website
            item_web = ToolStripMenuItem(f"🌐 Website: {APP_WEBSITE.replace('https://', '')}")

            def on_web_click(sender, args):
                try:
                    webbrowser.open(APP_WEBSITE)
                except Exception:
                    pass

            item_web.Click += on_web_click
            menu.Items.Add(item_web)

            # Item 4: Hotline / Zalo
            item_phone = ToolStripMenuItem(f"📱 Hotline/Zalo: {APP_PHONE}")

            def on_phone_click(sender, args):
                try:
                    webbrowser.open(f"https://zalo.me/{APP_PHONE.replace(' ', '')}")
                except Exception:
                    pass

            item_phone.Click += on_phone_click
            menu.Items.Add(item_phone)

            # Item 5: Telegram
            item_tele = ToolStripMenuItem("✈️ Telegram: @lethetuanpc")

            def on_tele_click(sender, args):
                try:
                    webbrowser.open(APP_TELEGRAM)
                except Exception:
                    pass

            item_tele.Click += on_tele_click
            menu.Items.Add(item_tele)

            menu.Items.Add(ToolStripSeparator())

            # Item 6: Thoát hoàn toàn
            item_exit = ToolStripMenuItem("❌ Thoát hoàn toàn")

            def on_exit_click(sender, args):
                self.quit_app()

            item_exit.Click += on_exit_click
            menu.Items.Add(item_exit)

            self.notify.ContextMenuStrip = menu

            # Handle mouse click and double click
            def on_mouse_click(sender, e):
                if e.Button == MouseButtons.Left:
                    self.toggle_window()

            self.notify.MouseClick += on_mouse_click

            self.notify.Visible = True

            # Start message loop for NotifyIcon
            Application.Run()

        except Exception as e:
            print(f"Error in TrayManager loop: {e}")

    def show_window(self):
        """Restores and brings the main window to front (handles minimized, hidden, or background states)."""
        self.is_hidden = False
        try:
            if self.window:
                self.window.show()
                self.window.restore()

            # Bring to front using Windows API
            if self.window_title:
                hwnd = user32.FindWindowW(None, self.window_title)
                if hwnd:
                    # Allow foreign threads to set foreground
                    try:
                        user32.AllowSetForegroundWindow(-1)
                    except Exception:
                        pass
                    # If window is minimized (IsIconic), restore it
                    if user32.IsIconic(hwnd):
                        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                    else:
                        user32.ShowWindow(hwnd, 5)  # SW_SHOW
                        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                    user32.SetForegroundWindow(hwnd)
                    user32.BringWindowToTop(hwnd)
        except Exception as e:
            print(f"Error showing window: {e}")

    def hide_window(self):
        """Hides the main window to system tray and shows notification."""
        self.is_hidden = True
        try:
            if self.window:
                self.window.hide()

            if self.notify and not self._first_minimize_notified:
                self._first_minimize_notified = True
                self.notify.ShowBalloonTip(
                    2500,
                    f"{APP_NAME} - {APP_AUTHOR}",
                    "Ứng dụng đang chạy ẩn dưới khay hệ thống (Taskbar Tray).\nClick chuột trái hoặc đúp vào icon để mở lại bất cứ lúc nào.",
                    ToolTipIcon.Info
                )
        except Exception as e:
            print(f"Error hiding window: {e}")

    def toggle_window(self):
        """Toggles between showing and hiding the window."""
        if self.is_hidden:
            self.show_window()
        else:
            self.show_window()

    def on_window_closing(self):
        """
        Handler attached to window.events.closing.
        When user clicks the red 'X' button:
        - If quitting: allows window to close.
        - Otherwise: intercepts, minimizes window to tray, and returns False.
        """
        if self.is_quitting:
            return True

        self.hide_window()
        return False

    def quit_app(self):
        """Completely terminates the application and cleans up tray icon."""
        self.is_quitting = True
        try:
            if self.notify:
                self.notify.Visible = False
                self.notify.Dispose()
        except Exception:
            pass

        try:
            if self.window:
                self.window.destroy()
        except Exception:
            pass

        try:
            Application.Exit()
        except Exception:
            pass

        os._exit(0)
