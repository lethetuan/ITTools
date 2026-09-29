import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import re
import winreg
import modules.uninstall_manager as um
from modules.startup_manager import extract_file_icon_base64, extract_exe_path

_start_menu_shortcuts_cache = None

def _get_start_menu_shortcuts():
    global _start_menu_shortcuts_cache
    if _start_menu_shortcuts_cache is not None:
        return _start_menu_shortcuts_cache
    
    shortcuts = []
    start_dirs = [
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
        os.path.expandvars(r"%USERPROFILE%\Desktop"),
        r"C:\Users\Public\Desktop"
    ]
    for sdir in start_dirs:
        if not os.path.exists(sdir):
            continue
        for root, _, files in os.walk(sdir):
            for f in files:
                if f.lower().endswith(".lnk"):
                    lnk_name = f[:-4]
                    clean_key = re.sub(r'[^a-zA-Z0-9]', '', lnk_name.lower())
                    shortcuts.append((clean_key, os.path.join(root, f)))
    _start_menu_shortcuts_cache = shortcuts
    return shortcuts


def find_best_app_icon(disp_name, display_icon="", install_location="", uninstall_cmd=""):
    # 1. Try DisplayIcon
    if display_icon:
        clean = extract_exe_path(display_icon)
        if clean and os.path.exists(clean):
            b64 = extract_file_icon_base64(clean)
            if b64:
                return b64

    # 2. Try normalized name matching against Start Menu shortcuts
    clean_app = re.sub(r'[^a-zA-Z0-9]', '', disp_name.lower())
    norm_name = re.sub(r'(\d+|\b(x64|x86|edition|version|rc\d*|final|v\d+|build|suite|pro|free)\b)', '', disp_name, flags=re.I)
    clean_base = re.sub(r'[^a-zA-Z0-9]', '', norm_name.lower())

    shortcuts = _get_start_menu_shortcuts()
    for lnk_key, lnk_path in shortcuts:
        if (clean_base and len(clean_base) >= 3 and clean_base in lnk_key) or (clean_app in lnk_key) or (lnk_key in clean_base if len(lnk_key) >= 4 else False):
            b64 = extract_file_icon_base64(lnk_path)
            if b64:
                return b64

    # 3. Try InstallLocation
    if install_location and os.path.exists(install_location):
        if os.path.isfile(install_location) and install_location.lower().endswith(('.exe', '.ico')):
            b64 = extract_file_icon_base64(install_location)
            if b64:
                return b64
        elif os.path.isdir(install_location):
            try:
                exes = []
                for root, _, files in os.walk(install_location):
                    for f in files:
                        if f.lower().endswith('.exe') and not any(x in f.lower() for x in ['unins', 'setup', 'update', 'helper', 'crash']):
                            exes.append(os.path.join(root, f))
                exes.sort(key=lambda x: 0 if (clean_base and clean_base in re.sub(r'[^a-zA-Z0-9]', '', os.path.basename(x).lower())) else len(os.path.basename(x)))
                for exe in exes[:3]:
                    b64 = extract_file_icon_base64(exe)
                    if b64:
                        return b64
            except Exception:
                pass

    # 4. Try UninstallString
    if uninstall_cmd:
        clean_uninst = extract_exe_path(uninstall_cmd)
        if clean_uninst and os.path.exists(clean_uninst) and clean_uninst.lower().endswith('.exe'):
            b64 = extract_file_icon_base64(clean_uninst)
            if b64:
                return b64

    return ""

apps = um.get_installed_apps()
for a in apps[:20]:
    disp = a['display_name']
    d_icon = a.get('display_icon', '')
    loc = a.get('install_location', '')
    uninst = a.get('uninstall_cmd', '')
    icon = find_best_app_icon(disp, d_icon, loc, uninst)
    print(f"{disp[:38]:<38} | Icon: {bool(icon)}")
