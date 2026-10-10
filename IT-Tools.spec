# -*- mode: python ; coding: utf-8 -*-
# =====================================================================
# IT Tool LTT - Root PyInstaller Build Spec (Standalone Single-File EXE)
# Tac gia: Le The Tuan | Zalo: 0352 194 195
# Build from repo root: python -m PyInstaller IT-Tools.spec --noconfirm
# =====================================================================

import sys
import os
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

block_cipher = None

base_dir = os.path.abspath(os.path.join(SPECPATH, "ITTools"))

# Collect all dynamic/static data files and native C/C++/.NET binaries
datas_webview, binaries_webview, hiddenimports_webview = collect_all("webview")
datas_clr, binaries_clr, hiddenimports_clr = collect_all("clr_loader")
datas_pythonnet, binaries_pythonnet, hiddenimports_pythonnet = collect_all("pythonnet")
datas_psutil, binaries_psutil, hiddenimports_psutil = collect_all("psutil")
datas_pil, binaries_pil, hiddenimports_pil = collect_all("PIL")
datas_openpyxl, binaries_openpyxl, hiddenimports_openpyxl = collect_all("openpyxl")

project_datas = [
    (os.path.join(base_dir, "web"),     "web"),
    (os.path.join(base_dir, "assets"),  "assets"),
    (os.path.join(base_dir, "modules"), "modules"),
    (os.path.join(base_dir, "config"),  "config"),
    (os.path.join(base_dir, "ui"),      "ui"),
]

all_datas = (
    project_datas
    + datas_webview
    + datas_clr
    + datas_pythonnet
    + datas_psutil
    + datas_pil
    + datas_openpyxl
)

all_binaries = (
    binaries_webview
    + binaries_clr
    + binaries_pythonnet
    + binaries_psutil
    + binaries_pil
    + binaries_openpyxl
)

all_hiddenimports = list(set(
    hiddenimports_webview
    + hiddenimports_clr
    + hiddenimports_pythonnet
    + hiddenimports_psutil
    + hiddenimports_pil
    + hiddenimports_openpyxl
    + collect_submodules("webview")
    + collect_submodules("clr_loader")
    + collect_submodules("pythonnet")
    + collect_submodules("PIL")
    + collect_submodules("openpyxl")
    + [
        # Standard GUI & dialogs
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
        "tkinter.filedialog",
        "tkinter.simpledialog",
        "tkinter.scrolledtext",
        "_tkinter",

        # Core app modules
        "constants",
        "web_api",
        "tray_manager",
        "ui.main_window",
        "modules",
        "modules.auto_shutdown",
        "modules.backup_driver",
        "modules.bitlocker",
        "modules.boot_manager",
        "modules.browser_backup",
        "modules.classic_menu",
        "modules.computer_info",
        "modules.currency",
        "modules.datetime_tool",
        "modules.desktop_icon",
        "modules.firewall",
        "modules.folder_size",
        "modules.hosts_editor",
        "modules.ip_manager",
        "modules.ip_scanner",
        "modules.office_opt",
        "modules.other_tools",
        "modules.printer_fix",
        "modules.sendto_editor",
        "modules.server_tools",
        "modules.services_manager",
        "modules.startup_manager",
        "modules.uninstall_manager",
        "modules.wincheck",
        "modules.win_update",
        "modules.zoom_screen",
        "modules.zoom_screen_gui",

        # Windows system APIs and utilities
        "winreg",
        "ctypes", "ctypes.wintypes",
        "subprocess", "threading", "socket", "json", "queue",
        "ipaddress", "shutil", "glob", "tempfile", "hashlib",
        "base64", "struct", "time", "datetime", "calendar",
        "email", "urllib", "urllib.parse", "urllib.request",
        "http", "http.client", "html.parser",
        "xml", "xml.etree.ElementTree",
        "configparser", "platform", "locale", "codecs",
        "webbrowser", "uuid", "secrets", "getpass", "pathlib",
        "psutil", "psutil._pswindows",
        "clr", "clr_loader",
        "webview", "webview.platforms", "webview.platforms.winforms", "webview.platforms.edgechromium",
        "bottle",
        "openpyxl",
    ]
))

a = Analysis(
    [os.path.join(base_dir, "main.py")],
    pathex=[base_dir],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=all_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "unittest", "test",
        "xmlrpc", "ftplib", "telnetlib", "imaplib", "poplib", "smtplib",
        "curses", "readline", "pdb", "doctest",
        "webview.platforms.android",
        "webview.platforms.cocoa",
        "webview.platforms.gtk",
        "webview.platforms.qt",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="IT_Tool_LTT",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(base_dir, "assets", "tray_icon.ico"),
    uac_admin=True,
    uac_uiaccess=False,
)
