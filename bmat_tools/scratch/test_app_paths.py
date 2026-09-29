import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import winreg
import modules.uninstall_manager as um
from modules.startup_manager import extract_exe_path, extract_file_icon_base64

reg_paths = [
    (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'),
    (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'),
    (winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall')
]

target_apps = ["7-Zip", "CapCut", "UltraViewer", "UniKey", "Zalo", "Chrome", "Photoshop"]

for hive, path in reg_paths:
    try:
        key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
        i = 0
        while True:
            try:
                sub_name = winreg.EnumKey(key, i)
                sub_key = winreg.OpenKey(key, sub_name)
                def get_val(k, name):
                    try: return winreg.QueryValueEx(k, name)[0]
                    except: return ''
                disp = get_val(sub_key, 'DisplayName')
                if any(t.lower() in disp.lower() for t in target_apps):
                    icon_raw = get_val(sub_key, 'DisplayIcon')
                    inst_loc = get_val(sub_key, 'InstallLocation')
                    uninst = get_val(sub_key, 'UninstallString')
                    print(f"App: {disp}")
                    print(f"  DisplayIcon:     {icon_raw}")
                    print(f"  InstallLocation: {inst_loc}")
                    print(f"  UninstallString: {uninst}")
                    
                    # Test extraction strategies
                    clean_icon = extract_exe_path(icon_raw)
                    print(f"  clean_icon:      {clean_icon} (exists: {os.path.exists(clean_icon)})")
                    
                    # Test icon extraction
                    b64 = extract_file_icon_base64(clean_icon) or extract_file_icon_base64(inst_loc) or extract_file_icon_base64(uninst)
                    print(f"  Result Icon:     {bool(b64)}")
                    print("-" * 60)
                winreg.CloseKey(sub_key)
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except Exception as e:
        pass
