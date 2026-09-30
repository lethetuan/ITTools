"""
IT Tool LTT Constants & Theme Configuration
"""
import os

APP_NAME = "IT Tool LTT"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Lê Thế Tuấn"
APP_PHONE = "0352 194 195"
APP_WEBSITE = "https://lethetuanpc.blogspot.com"
APP_TELEGRAM = "https://t.me/lethetuanpc"
AUTOSTART_KEY_NAME = "IT Tool LTT"
SINGLE_INSTANCE_PORT = 49285

# Color Theme
COLORS = {
    'bg': '#F0F0F0',
    'bg_dark': '#E1E1E1',
    'bg_header': '#2C3E50',
    'accent': '#27AE60',
    'accent_hover': '#2ECC71',
    'danger': '#E74C3C',
    'warning': '#F39C12',
    'info': '#2980B9',
    'text': '#2C3E50',
    'text_light': '#7F8C8D',
    'white': '#FFFFFF',
    'border': '#BDC3C7',
    'btn_bg': '#ECF0F1',
    'btn_hover': '#D5DBDB',
    'selected': '#AED6F1',
    'tab_active': '#2980B9',
    'tab_inactive': '#BDC3C7',
    'green_text': '#27AE60',
    'red_text': '#E74C3C',
    'header_text': '#FFFFFF',
}

# Font Configuration
FONTS = {
    'title': ('Segoe UI', 11, 'bold'),
    'subtitle': ('Segoe UI', 10, 'bold'),
    'normal': ('Segoe UI', 9),
    'small': ('Segoe UI', 8),
    'mono': ('Consolas', 9),
    'large': ('Segoe UI', 12, 'bold'),
    'icon': ('Segoe UI', 18),
}

# Registry paths for startup
STARTUP_PATHS = {
    'HKCU': r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
    'HKLM': r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
    'HKCU_RunOnce': r'SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce',
    'HKLM_RunOnce': r'SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce',
    'User': os.path.join(os.environ.get('APPDATA', ''), 
                         r'Microsoft\Windows\Start Menu\Programs\Startup'),
    'Common': r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup',
}

