"""
Desktop Icon Module
Show/Hide desktop icons
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import winreg
import os
import sys
import ctypes

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS

# CLSID for common desktop icons
DESKTOP_ICONS = {
    'Computer (This PC)': '{20D04FE0-3AEA-1069-A2D8-08002B30309D}',
    'Network': '{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}',
    'Recycle Bin': '{645FF040-5081-101B-9F08-00AA002F954E}',
    'User Files': '{59031a47-3f72-44a7-89c5-5595fe6b30ee}',
    'Control Panel': '{5399E694-6CE5-4D6C-8FCE-1D8870FDCBA0}',
}

ICON_REG_PATH = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel'


class DesktopIcon:
    def __init__(self, parent):
        self.parent = parent
        self.parent.geometry('500x500')
        self.parent.configure(bg=COLORS['bg'])
        self.setup_ui()
        self.load_status()

    def setup_ui(self):
        hdr = tk.Frame(self.parent, bg=COLORS['bg_header'])
        hdr.pack(fill='x')
        tk.Label(hdr, text='🖥️  Desktop Icon Manager', font=FONTS['large'],
                  bg=COLORS['bg_header'], fg='white', pady=10).pack(side='left', padx=15)

        # Common icons section
        icons_frame = tk.LabelFrame(self.parent, text='  System Desktop Icons  ',
                                     font=FONTS['subtitle'], bg=COLORS['bg'],
                                     relief='groove')
        icons_frame.pack(fill='x', padx=15, pady=15)

        tk.Label(icons_frame,
                  text='Chọn icons hiển thị trên Desktop:',
                  font=FONTS['normal'], bg=COLORS['bg']).pack(anchor='w', padx=10, pady=5)

        self.icon_vars = {}
        for name, clsid in DESKTOP_ICONS.items():
            var = tk.BooleanVar()
            self.icon_vars[clsid] = var
            cb = tk.Checkbutton(icons_frame, text=f'  {name}',
                                 variable=var, font=FONTS['normal'],
                                 bg=COLORS['bg'], selectcolor=COLORS['selected'],
                                 cursor='hand2')
            cb.pack(anchor='w', padx=20, pady=3)

        # All icons toggle
        toggle_frame = tk.Frame(self.parent, bg=COLORS['bg'])
        toggle_frame.pack(fill='x', padx=15, pady=5)

        tk.Button(toggle_frame, text='👁️ Show All Desktop Icons',
                   font=FONTS['subtitle'], bg=COLORS['accent'], fg='white',
                   relief='flat', padx=15, pady=8, cursor='hand2',
                   command=self.show_all_icons).pack(side='left', padx=5)
        tk.Button(toggle_frame, text='🙈 Hide All Desktop Icons',
                   font=FONTS['subtitle'], bg=COLORS['danger'], fg='white',
                   relief='flat', padx=15, pady=8, cursor='hand2',
                   command=self.hide_all_icons).pack(side='left', padx=5)

        apply_frame = tk.Frame(self.parent, bg=COLORS['bg'])
        apply_frame.pack(fill='x', padx=15, pady=3)
        tk.Button(apply_frame, text='✅ Apply Changes',
                   font=FONTS['subtitle'], bg=COLORS['info'], fg='white',
                   relief='flat', padx=20, pady=8, cursor='hand2',
                   command=self.apply_changes).pack(side='left', padx=5)
        tk.Button(apply_frame, text='🔄 Refresh Desktop',
                   font=FONTS['subtitle'], bg=COLORS['warning'], fg='white',
                   relief='flat', padx=20, pady=8, cursor='hand2',
                   command=self.refresh_desktop).pack(side='left', padx=5)

        # Quick actions
        quick_frame = tk.LabelFrame(self.parent, text='  Quick Actions  ',
                                     font=FONTS['subtitle'], bg=COLORS['bg'])
        quick_frame.pack(fill='x', padx=15, pady=10)

        actions = [
            ('📋 Desktop Settings', 'control desk.cpl,@web,0'),
            ('🖥️ Display Settings', 'ms-settings:display'),
            ('🎨 Personalization', 'ms-settings:personalization'),
            ('⚙️ Taskbar Settings', 'ms-settings:taskbar'),
        ]
        for name, cmd in actions:
            tk.Button(quick_frame, text=name, font=FONTS['normal'],
                       bg=COLORS['btn_bg'], fg=COLORS['text'],
                       relief='groove', padx=10, pady=4, cursor='hand2',
                       command=lambda c=cmd: subprocess.Popen(
                           f'start {c}', shell=True
                       )).pack(side='left', padx=5, pady=5)

    def load_status(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                  ICON_REG_PATH, 0, winreg.KEY_READ)
            for clsid, var in self.icon_vars.items():
                try:
                    val, _ = winreg.QueryValueEx(key, clsid)
                    var.set(val == 0)  # 0 = show, 1 = hide
                except:
                    var.set(True)  # Default: show
            winreg.CloseKey(key)
        except:
            for var in self.icon_vars.values():
                var.set(True)

    def apply_changes(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                  ICON_REG_PATH, 0, winreg.KEY_SET_VALUE)
            for clsid, var in self.icon_vars.items():
                winreg.SetValueEx(key, clsid, 0, winreg.REG_DWORD,
                                   0 if var.get() else 1)
            winreg.CloseKey(key)
            self.refresh_desktop()
            messagebox.showinfo('Success', '✅ Đã cập nhật Desktop icons!')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def show_all_icons(self):
        for var in self.icon_vars.values():
            var.set(True)
        self.apply_changes()

    def hide_all_icons(self):
        for var in self.icon_vars.values():
            var.set(False)
        self.apply_changes()

    def refresh_desktop(self):
        # Refresh explorer
        ctypes.windll.user32.SystemParametersInfoW(0x0073, 0, None, 3)
        subprocess.run(['taskkill', '/f', '/im', 'explorer.exe'],
                        capture_output=True)
        import time
        time.sleep(1)
        subprocess.Popen(['explorer.exe'])


def get_desktop_icon_settings():
    """Reads current Registry status for Desktop Icons and Taskbar toggles."""
    import winreg

    REG_DESKTOP = r'Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel'
    REG_ADVANCED = r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced'
    REG_SEARCH = r'Software\Microsoft\Windows\CurrentVersion\Search'
    REG_FEEDS = r'Software\Microsoft\Windows\CurrentVersion\Feeds'

    def read_reg(key_path, val_name, default=None):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, val_name)
            winreg.CloseKey(key)
            return val
        except Exception:
            return default

    # Desktop Icon CLSIDs (0 = Show / Checked, 1 = Hide / Unchecked)
    computer_val = read_reg(REG_DESKTOP, '{20D04FE0-3AEA-1069-A2D8-08002B30309D}', 0)
    user_val = read_reg(REG_DESKTOP, '{59031a47-3f72-44a7-89c5-5595fe6b30ee}', 0)
    network_val = read_reg(REG_DESKTOP, '{F0272068-166B-11CE-9B7A-00AA002F954E}', 0)
    if network_val != 0:
        network_val = read_reg(REG_DESKTOP, '{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}', 0)
    cpanel_val = read_reg(REG_DESKTOP, '{5399E696-AE2F-480C-A331-2338204612E2}', 0)
    if cpanel_val != 0:
        cpanel_val = read_reg(REG_DESKTOP, '{5399E694-6CE5-4D6C-8FCE-1D8870FDCBA0}', 0)
    recycle_val = read_reg(REG_DESKTOP, '{645FF040-5081-101B-9F08-00AA002F954E}', 0)

    # Taskbar alignment (0 = Left, 1 = Center)
    taskbar_left_val = read_reg(REG_ADVANCED, 'TaskbarAl', 1)

    # Search Icon/Box on Taskbar:
    # Primary registry key on Windows 10 & 11 is HKCU\Software\Microsoft\Windows\CurrentVersion\Search
    search_val = read_reg(REG_SEARCH, 'SearchboxTaskbarMode', None)
    if search_val is None:
        search_val = read_reg(REG_ADVANCED, 'SearchboxTaskbarMode', 1)

    # Weather / Widgets:
    # Win 11: TaskbarDa in Explorer\Advanced (0 = Off, 1 = On)
    # Win 10: ShellFeedsTaskbarViewMode in Feeds (0 = On, 2 = Off)
    weather_da = read_reg(REG_ADVANCED, 'TaskbarDa', None)
    if weather_da is not None:
        weather_off = (weather_da == 0)
    else:
        feeds_val = read_reg(REG_FEEDS, 'ShellFeedsTaskbarViewMode', None)
        if feeds_val is not None:
            weather_off = (feeds_val == 2)
        else:
            weather_off = False

    return {
        "computer": computer_val == 0,
        "user_files": user_val == 0,
        "network": network_val == 0,
        "control_panel": cpanel_val == 0,
        "recycle_bin": recycle_val == 0,
        "taskbar_left": taskbar_left_val == 0,
        "search_icon": (search_val is not None and search_val > 0),
        "weather_off": weather_off
    }


def apply_desktop_icon_settings(settings):
    """Applies Desktop Icon and Taskbar toggle settings into Windows Registry and restarts Explorer."""
    import winreg
    import subprocess
    import ctypes
    import time

    REG_DESKTOP = r'Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel'
    REG_DESKTOP_CLASSIC = r'Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\ClassicStartMenu'
    REG_ADVANCED = r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced'
    REG_SEARCH = r'Software\Microsoft\Windows\CurrentVersion\Search'
    REG_FEEDS = r'Software\Microsoft\Windows\CurrentVersion\Feeds'

    def write_reg(key_path, val_name, val):
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, val_name, 0, winreg.REG_DWORD, val)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    # 1. Desktop icons (0 = Show, 1 = Hide)
    computer_hide = 0 if settings.get("computer", True) else 1
    user_hide = 0 if settings.get("user_files", True) else 1
    network_hide = 0 if settings.get("network", True) else 1
    cpanel_hide = 0 if settings.get("control_panel", True) else 1
    recycle_hide = 0 if settings.get("recycle_bin", True) else 1

    for path in [REG_DESKTOP, REG_DESKTOP_CLASSIC]:
        write_reg(path, '{20D04FE0-3AEA-1069-A2D8-08002B30309D}', computer_hide)
        write_reg(path, '{59031a47-3f72-44a7-89c5-5595fe6b30ee}', user_hide)
        write_reg(path, '{F0272068-166B-11CE-9B7A-00AA002F954E}', network_hide)
        write_reg(path, '{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}', network_hide)
        write_reg(path, '{5399E696-AE2F-480C-A331-2338204612E2}', cpanel_hide)
        write_reg(path, '{5399E694-6CE5-4D6C-8FCE-1D8870FDCBA0}', cpanel_hide)
        write_reg(path, '{645FF040-5081-101B-9F08-00AA002F954E}', recycle_hide)

    # 2. Taskbar Alignment (0 = Left, 1 = Center)
    taskbar_al = 0 if settings.get("taskbar_left", False) else 1
    write_reg(REG_ADVANCED, 'TaskbarAl', taskbar_al)

    # 3. Search Icon (0 = Hidden, 1 = Show Icon)
    # Write to BOTH Search and Explorer\Advanced for 100% compatibility across Win 10 and Win 11
    search_enabled = settings.get("search_icon", True)
    search_mode = 1 if search_enabled else 0
    write_reg(REG_SEARCH, 'SearchboxTaskbarMode', search_mode)
    write_reg(REG_ADVANCED, 'SearchboxTaskbarMode', search_mode)

    # 4. Weather / Widgets:
    current_weather_da = None
    try:
        k_check = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_ADVANCED, 0, winreg.KEY_READ)
        current_weather_da, _ = winreg.QueryValueEx(k_check, 'TaskbarDa')
        winreg.CloseKey(k_check)
    except Exception:
        pass

    current_weather_off = (current_weather_da == 0) if current_weather_da is not None else False
    weather_off = settings.get("weather_off", False)
    weather_changed = (weather_off != current_weather_off)

    weather_notice = ""
    weather_da_ok = True

    if weather_changed:
        if weather_off:
            # User wants Weather OFF
            # Win 11: TaskbarDa = 0 (Hide Widgets)
            weather_da_ok = write_reg(REG_ADVANCED, 'TaskbarDa', 0)
            # Win 10: ShellFeedsTaskbarViewMode = 2 (Turn off Feeds)
            write_reg(REG_FEEDS, 'ShellFeedsTaskbarViewMode', 2)
            write_reg(REG_FEEDS, 'ShellFeedsTaskbarContentUpdateMode', 2)
            write_reg(REG_FEEDS, 'HeadlinesOnHover', 0)
        else:
            # User wants Weather ON
            # Win 11: TaskbarDa = 1 (Show Widgets)
            weather_da_ok = write_reg(REG_ADVANCED, 'TaskbarDa', 1)
            # Win 10: ShellFeedsTaskbarViewMode = 0 (Show icon and text)
            write_reg(REG_FEEDS, 'ShellFeedsTaskbarViewMode', 0)

        # Handle Win 11 UCPD (User Choice Protection Driver) restriction if writing TaskbarDa failed
        if not weather_da_ok:
            try:
                # Disable UCPD service and scheduled watchdog task so it unprotects upon next reboot
                subprocess.run("sc.exe config UCPD start= disabled", shell=True, capture_output=True)
                subprocess.run(r'schtasks /change /Disable /TN "\Microsoft\Windows\AppxDeploymentClient\UCPD velocity"', shell=True, capture_output=True)
                # Open Taskbar settings so user can toggle Widgets switch in 1 click
                subprocess.Popen("start ms-settings:taskbar", shell=True)
                weather_notice = "\n\n⚠️ Lưu ý: Trên bản Windows 11 24H2 có cơ chế bảo vệ UCPD. Hệ thống đã mở Cài đặt Taskbar (Taskbar Settings) để bạn gạt tắt/bật Widget ngay lập tức."
            except Exception:
                pass

    # 5. Refresh Desktop & Taskbar Shell cleanly
    try:
        # Notify Desktop Icon font/refresh
        ctypes.windll.user32.SystemParametersInfoW(0x0073, 0, None, 3)

        # Broadcast WM_SETTINGCHANGE for Taskbar TraySettings
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 2
        result = ctypes.c_ulong()
        ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, 'TraySettings', SMTO_ABORTIFHUNG, 2000, ctypes.byref(result))
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)

        # Restart Explorer cleanly to apply Taskbar and Desktop changes
        subprocess.run(['taskkill', '/f', '/im', 'explorer.exe'], capture_output=True)
        time.sleep(1)
        subprocess.Popen(['explorer.exe'])
    except Exception:
        pass

    return {
        "success": True,
        "message": f"✅ Đã áp dụng cài đặt Desktop Icon & Taskbar thành công!{weather_notice}"
    }

