# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

base_dir = os.path.abspath(r'D:\AllinOne\bmat_tools')

# Collect all dynamic/static data files
webview_datas = collect_data_files('webview')
pythonnet_datas = collect_data_files('pythonnet')
clr_loader_datas = collect_data_files('clr_loader')

datas = [
    (os.path.join(base_dir, 'web'), 'web'),
    (os.path.join(base_dir, 'assets'), 'assets'),
    (os.path.join(base_dir, 'modules', 'install_office_silent.ps1'), 'modules'),
    (os.path.join(base_dir, 'modules', 'winget_runner.ps1'), 'modules'),
] + webview_datas + pythonnet_datas + clr_loader_datas

hiddenimports = [
    'clr',
    'pythonnet',
    'clr_loader',
    'tray_manager',
    'webview',
    'webview.platforms.winforms',
    'webview.platforms.edgechromium',
    'webview.platforms.win32',
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    'constants',
    'web_api',
    'modules.auto_shutdown',
    'modules.backup_driver',
    'modules.bitlocker',
    'modules.boot_manager',
    'modules.browser_backup',
    'modules.classic_menu',
    'modules.computer_info',
    'modules.currency',
    'modules.datetime_tool',
    'modules.desktop_icon',
    'modules.firewall',
    'modules.folder_size',
    'modules.hosts_editor',
    'modules.ip_manager',
    'modules.ip_scanner',
    'modules.office_opt',
    'modules.other_tools',
    'modules.printer_fix',
    'modules.sendto_editor',
    'modules.server_tools',
    'modules.services_manager',
    'modules.startup_manager',
    'modules.uninstall_manager',
    'modules.win_update',
    'modules.wincheck',
    'ui.main_window',
] + [m for m in collect_submodules('webview') if 'android' not in m and 'cocoa' not in m and 'gtk' not in m] + collect_submodules('pythonnet') + collect_submodules('clr_loader')

a = Analysis(
    [os.path.join(base_dir, 'main.py')],
    pathex=[base_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['scratch'],
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
    name='IT Tool LTT',
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
    uac_admin=True,
    icon=os.path.join(base_dir, 'assets', 'tray_icon.ico'),
)
