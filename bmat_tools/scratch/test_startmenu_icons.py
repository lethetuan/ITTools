import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import winreg
from modules.startup_manager import extract_file_icon_base64

def find_start_menu_icon(app_name):
    start_dirs = [
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
        os.path.expandvars(r"%USERPROFILE%\Desktop"),
        r"C:\Users\Public\Desktop"
    ]
    
    clean_name = app_name.lower().replace(" ", "").replace("-", "").replace("_", "")
    
    # Simple direct match first
    for sdir in start_dirs:
        if not os.path.exists(sdir): continue
        for root, dirs, files in os.walk(sdir):
            for f in files:
                if f.lower().endswith(".lnk"):
                    lnk_clean = f[:-4].lower().replace(" ", "").replace("-", "").replace("_", "")
                    if clean_name in lnk_clean or lnk_clean in clean_name:
                        full_path = os.path.join(root, f)
                        b64 = extract_file_icon_base64(full_path)
                        if b64:
                            return b64, full_path
    return "", ""

target_apps = ["7-Zip", "CapCut", "Google Chrome", "Adobe Photoshop", "UniKey", "Zalo", "UltraViewer"]
for app in target_apps:
    b64, path = find_start_menu_icon(app)
    print(f"App: {app:<20} | Found Icon: {bool(b64):<5} | Lnk Path: {path}")
