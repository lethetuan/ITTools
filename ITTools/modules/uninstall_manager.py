"""
Uninstall Manager Module
Deep Clean Uninstall Wizard (Your Uninstaller! style)
Scans installed apps, runs uninstaller, cleans leftover registry keys & installation folders.
"""

import winreg
import os
import shutil
import subprocess
import sys
import re
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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


def get_installed_apps():
    """Returns all installed Win32 applications and Windows Store AppX packages with real native icons."""
    global _start_menu_shortcuts_cache
    _start_menu_shortcuts_cache = None  # Force fresh scan of Start Menu shortcuts on every scan

    apps = []
    seen_names = set()

    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall', 'HKLM'),
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall', 'HKLM_WOW64'),
        (winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall', 'HKCU'),
        (winreg.HKEY_CURRENT_USER, r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall', 'HKCU_WOW64')
    ]


    for hive, path, hive_name in reg_paths:
        try:
            key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
            i = 0
            while True:
                try:
                    sub_name = winreg.EnumKey(key, i)
                    sub_key = winreg.OpenKey(key, sub_name)

                    def get_val(k, name, default=''):
                        try:
                            return winreg.QueryValueEx(k, name)[0]
                        except:
                            return default

                    disp = get_val(sub_key, 'DisplayName')
                    uninstall = get_val(sub_key, 'UninstallString')
                    quiet_uninstall = get_val(sub_key, 'QuietUninstallString')
                    install_loc = get_val(sub_key, 'InstallLocation')
                    display_icon = get_val(sub_key, 'DisplayIcon')
                    publisher = get_val(sub_key, 'Publisher')
                    date = get_val(sub_key, 'InstallDate')
                    size_kb = get_val(sub_key, 'EstimatedSize', 0)
                    version = get_val(sub_key, 'DisplayVersion')

                    winreg.CloseKey(sub_key)
                    i += 1

                    if not disp or not disp.strip() or disp.strip() in seen_names:
                        continue

                    # Skip KB Windows patches
                    if disp.startswith('KB') and len(disp) > 8 and disp[2:8].isdigit():
                        continue

                    seen_names.add(disp.strip())

                    # Icon extraction via multi-layer resolution
                    icon_b64 = find_best_app_icon(disp.strip(), display_icon, install_loc, quiet_uninstall or uninstall)

                    size_str = ""
                    if size_kb:
                        try:
                            size_mb = int(size_kb) // 1024
                            size_str = f"{size_mb} MB" if size_mb > 0 else f"{size_kb} KB"
                        except:
                            pass

                    if date and len(str(date)) == 8:
                        d_str = str(date)
                        date = f"{d_str[0:4]}-{d_str[4:6]}-{d_str[6:8]}"

                    apps.append({
                        "display_name": disp.strip(),
                        "name": disp.strip(),
                        "publisher": publisher or "Windows App",
                        "install_date": date or "Unknown",
                        "date": date or "Unknown",
                        "estimated_size": size_kb or 0,
                        "size": size_str or "--",
                        "display_version": version or "1.0",
                        "version": version or "1.0",
                        "uninstall_cmd": quiet_uninstall or uninstall or "",
                        "uninstall": quiet_uninstall or uninstall or "",
                        "install_location": install_loc or "",
                        "reg_key_name": sub_name,
                        "hive_name": hive_name,
                        "icon_b64": icon_b64,
                        "icon": icon_b64,
                        "is_store": False,
                        "type": "win32"
                    })
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception:
            pass

    return sorted(apps, key=lambda x: x['display_name'].lower())


def get_store_apps():
    """Returns installed Windows Store (AppX) packages."""
    apps = []
    try:
        ps_cmd = 'Get-AppxPackage | Select-Object Name, Publisher, Version, InstallLocation | ConvertTo-Json -Depth 2'
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=15)
        if res.returncode == 0 and res.stdout:
            import json
            data = json.loads(res.stdout)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                name = item.get('Name', '')
                if not name or name.startswith('Microsoft.') or name.startswith('Windows.'):
                    continue
                parts = name.split('_')
                disp = parts[0] if parts else name
                loc = item.get('InstallLocation', '')
                icon_b64 = extract_file_icon_base64(loc) if loc else ""
                apps.append({
                    "display_name": disp,
                    "name": disp,
                    "publisher": item.get('Publisher', 'Microsoft Store'),
                    "install_date": "Store Package",
                    "date": "Store Package",
                    "estimated_size": 0,
                    "size": "--",
                    "display_version": item.get('Version', '1.0'),
                    "version": item.get('Version', '1.0'),
                    "uninstall_cmd": f'Remove-AppxPackage -Package {name}',
                    "uninstall": f'Remove-AppxPackage -Package {name}',
                    "install_location": loc,
                    "reg_key_name": name,
                    "hive_name": "Store",
                    "icon_b64": icon_b64,
                    "icon": icon_b64,
                    "is_store": True,
                    "type": "store"
                })
    except Exception:
        pass
    return sorted(apps, key=lambda x: x['display_name'].lower())


def _check_reg_key_exists(reg_key_name):
    """Returns True if the app's Uninstall registry key still exists (= still installed)."""
    if not reg_key_name:
        return False
    bases = [
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'),
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'),
        (winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'),
        (winreg.HKEY_CURRENT_USER, r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'),
    ]
    for hive, base in bases:
        try:
            key = winreg.OpenKey(hive, f"{base}\\{reg_key_name}")
            winreg.CloseKey(key)
            return True  # still exists
        except Exception:
            pass
    return False  # not found = uninstalled


SYSTEM_PROTECTED_ROOT_KEYS = {
    'classes', 'policies', 'registeredapplications', 'system', 'windows', 
    'microsoft', 'oem', 'realtek', 'asus', 'dell', 'hp', 'lenovo', 'acer', 
    'msi', 'broadcom', 'qualcomm', 'commonfiles', 'uninstall', 'windows nt',
    'common files', 'desktop', 'start menu', 'temp', 'windows defender'
}

PROTECTED_VENDOR_KEYS = {
    'google', 'adobe', 'apple', 'intel', 'nvidia', 'amd', 'mozilla', 
    'tencent', 'valve', 'oracle', 'electronic arts'
}

SYSTEM_EXES = {
    'explorer.exe', 'svchost.exe', 'cmd.exe', 'powershell.exe', 'python.exe', 
    'taskmgr.exe', 'system', 'conhost.exe', 'csrss.exe', 'lsass.exe', 
    'services.exe', 'smss.exe', 'wininit.exe', 'winlogon.exe', 'dwm.exe',
    'sihost.exe', 'ctfmon.exe', 'runtimebroker.exe', 'searchhost.exe'
}

_skip_step1_flag = False

def request_skip_step1():
    """Allows caller/UI to immediately skip waiting for the native uninstaller process."""
    global _skip_step1_flag
    _skip_step1_flag = True


def is_app_name_match(candidate_name, app_name):
    """Safely determines if candidate_name belongs to app_name without matching common parent vendors."""
    cand_clean = re.sub(r'[^a-zA-Z0-9]', '', str(candidate_name).lower())
    app_clean = re.sub(r'[^a-zA-Z0-9]', '', str(app_name).lower())
    if not cand_clean or not app_clean:
        return False
    if cand_clean in SYSTEM_PROTECTED_ROOT_KEYS or cand_clean in PROTECTED_VENDOR_KEYS:
        return False
    if cand_clean == app_clean:
        return True
    if len(app_clean) >= 4 and app_clean in cand_clean:
        return True
    words = [re.sub(r'[^a-zA-Z0-9]', '', w.lower()) for w in app_name.split() if len(w) >= 3]
    words = [w for w in words if w not in SYSTEM_PROTECTED_ROOT_KEYS and w not in PROTECTED_VENDOR_KEYS]
    for w in words:
        if len(w) >= 3 and cand_clean == w:
            return True
        if len(w) >= 4 and (cand_clean == w + 'setup' or cand_clean == w + 'data' or cand_clean == w + 'app'):
            return True
    return False


def _delete_reg_key_recursive(hive, key_path, max_depth=6):
    """Safely and recursively deletes a registry key and all its subkeys without infinite loops."""
    if max_depth <= 0:
        return False
    try:
        subkeys = []
        try:
            with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        subkeys.append(winreg.EnumKey(key, i))
                        i += 1
                    except OSError:
                        break
        except Exception:
            pass

        for sub in subkeys:
            _delete_reg_key_recursive(hive, f"{key_path}\\{sub}", max_depth - 1)

        try:
            winreg.DeleteKey(hive, key_path)
            return True
        except Exception:
            hive_str = "HKLM" if hive == winreg.HKEY_LOCAL_MACHINE else "HKCU"
            res = subprocess.run(f'reg delete "{hive_str}\\{key_path}" /f', shell=True, capture_output=True)
            return res.returncode == 0
    except Exception:
        return False


def kill_app_processes(app_name, install_location=None):
    """Terminates running processes associated with the app to release file and registry locks."""
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', app_name.lower())
    if not clean_name or len(clean_name) < 3:
        return

    # 1. Kill executables located in install_location
    if install_location and os.path.exists(install_location):
        try:
            for root, _, files in os.walk(install_location):
                for f in files:
                    if f.lower().endswith('.exe') and f.lower() not in SYSTEM_EXES:
                        proc_name = f.lower()
                        subprocess.run(f'taskkill /f /im "{proc_name}"', shell=True, capture_output=True)
        except Exception:
            pass

    # 2. Kill processes matching clean_name safely
    try:
        res = subprocess.run('tasklist /FO CSV /NH', shell=True, capture_output=True, text=True, errors='ignore')
        for line in res.stdout.splitlines():
            if not line:
                continue
            parts = [p.strip('"') for p in line.split(',')]
            proc_exe = parts[0]
            if proc_exe.lower() in SYSTEM_EXES:
                continue
            proc_clean = re.sub(r'[^a-zA-Z0-9]', '', proc_exe.lower().replace('.exe', ''))
            if is_app_name_match(proc_clean, app_name):
                subprocess.run(f'taskkill /f /im "{proc_exe}"', shell=True, capture_output=True)
    except Exception:
        pass


def deep_scan_leftover_registry(app_name, reg_key_name=""):
    """Scans and safely deletes leftover registry keys matching the app name."""
    deleted_keys = []

    # 1. Direct check for reg_key_name in Uninstall keys
    if reg_key_name:
        uninstall_bases = [
            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'),
            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'),
            (winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'),
            (winreg.HKEY_CURRENT_USER, r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'),
        ]
        for hive, base in uninstall_bases:
            full_key_path = f"{base}\\{reg_key_name}"
            hive_str = "HKLM" if hive == winreg.HKEY_LOCAL_MACHINE else "HKCU"
            disp_str = f"{hive_str}\\{full_key_path}"
            if disp_str not in deleted_keys:
                if _delete_reg_key_recursive(hive, full_key_path):
                    deleted_keys.append(disp_str)

    # 2. Scan SOFTWARE hives
    reg_bases = [
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE'),
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node'),
        (winreg.HKEY_CURRENT_USER, r'SOFTWARE'),
    ]

    for hive, base_path in reg_bases:
        hive_str = "HKLM" if hive == winreg.HKEY_LOCAL_MACHINE else "HKCU"
        try:
            with winreg.OpenKey(hive, base_path, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        sub_name = winreg.EnumKey(key, i)
                        i += 1
                        sub_clean = re.sub(r'[^a-zA-Z0-9]', '', sub_name.lower())
                        if sub_clean in SYSTEM_PROTECTED_ROOT_KEYS:
                            continue
                        if sub_clean in PROTECTED_VENDOR_KEYS:
                            # Vendor key like Google or Adobe - look inside for the app
                            try:
                                with winreg.OpenKey(hive, f"{base_path}\\{sub_name}", 0, winreg.KEY_READ) as vkey:
                                    j = 0
                                    while True:
                                        try:
                                            v_sub = winreg.EnumKey(vkey, j)
                                            j += 1
                                            if is_app_name_match(v_sub, app_name):
                                                target_path = f"{base_path}\\{sub_name}\\{v_sub}"
                                                disp_str = f"{hive_str}\\{target_path}"
                                                if disp_str not in deleted_keys:
                                                    if _delete_reg_key_recursive(hive, target_path):
                                                        deleted_keys.append(disp_str)
                                        except OSError:
                                            break
                            except Exception:
                                pass
                        elif is_app_name_match(sub_name, app_name):
                            target_path = f"{base_path}\\{sub_name}"
                            disp_str = f"{hive_str}\\{target_path}"
                            if disp_str not in deleted_keys:
                                if _delete_reg_key_recursive(hive, target_path):
                                    deleted_keys.append(disp_str)
                    except OSError:
                        break
        except Exception:
            pass

    return deleted_keys


def find_app_folders(app_name, install_location=None):
    """Finds existing folders belonging to the app without deleting them."""
    folders = []
    # Explicit install_location
    if install_location and os.path.exists(install_location):
        clean_loc = install_location.lower().rstrip('\\/')
        if len(clean_loc) > 8 and clean_loc not in [r'c:\program files', r'c:\program files (x86)', r'c:\programdata', r'c:\users', r'c:\windows']:
            folders.append(install_location)

    search_dirs = [
        os.environ.get('ProgramFiles', r'C:\Program Files'),
        os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)'),
        os.environ.get('APPDATA', ''),
        os.environ.get('LOCALAPPDATA', ''),
        os.environ.get('PROGRAMDATA', ''),
    ]
    for bdir in search_dirs:
        if not bdir or not os.path.exists(bdir):
            continue
        try:
            for item in os.listdir(bdir):
                item_path = os.path.join(bdir, item)
                if not os.path.isdir(item_path):
                    continue
                item_clean = re.sub(r'[^a-zA-Z0-9]', '', item.lower())
                if item_clean in SYSTEM_PROTECTED_ROOT_KEYS:
                    continue
                if item_clean in PROTECTED_VENDOR_KEYS:
                    try:
                        for v_item in os.listdir(item_path):
                            v_path = os.path.join(item_path, v_item)
                            if os.path.isdir(v_path) and is_app_name_match(v_item, app_name):
                                if v_path not in folders:
                                    folders.append(v_path)
                    except Exception:
                        pass
                elif is_app_name_match(item, app_name):
                    if item_path not in folders:
                        folders.append(item_path)
        except Exception:
            pass
    return folders


def deep_scan_leftover_folders(app_name, install_location=None):
    """Scans and safely deletes leftover installation folders & AppData trash."""
    folders = find_app_folders(app_name, install_location)
    deleted_folders = []
    for f in folders:
        if os.path.exists(f):
            try:
                shutil.rmtree(f, ignore_errors=True)
                if not os.path.exists(f):
                    deleted_folders.append(f)
            except Exception:
                pass
    return deleted_folders


def run_deep_clean_uninstall(app_name, uninstall_cmd, install_location=None, reg_key_name="", is_store=False):
    """
    Executes the 3-Step Your Uninstaller! Wizard process:
    Step 1: Terminate app processes & run the native uninstaller interactively
    Step 2: Deep scan & clean Windows Registry leftovers
    Step 3: Deep scan & clean installation folders & AppData trash
    """
    global _skip_step1_flag
    _skip_step1_flag = False

    results = {
        "success": True,
        "step1_success": False,
        "app_name": app_name,
        "step1_msg": "",
        "step2_keys": [],
        "registry_cleaned": [],
        "step3_folders": [],
        "folders_cleaned": [],
        "summary": ""
    }

    # Kill any running processes first to release file & registry locks
    kill_app_processes(app_name, install_location)

    # ── STEP 1: Run Default Uninstaller (Interactive — user sees the window) ──
    try:
        if is_store or (uninstall_cmd and "Remove-AppxPackage" in uninstall_cmd):
            # Store apps: must run silently via PowerShell
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", uninstall_cmd],
                capture_output=True, timeout=60
            )
            results["step1_msg"] = "✅ Step 1: Đã gỡ ứng dụng Windows Store (AppX)!"
            results["step1_success"] = not _check_reg_key_exists(reg_key_name)

        elif uninstall_cmd:
            cmd = uninstall_cmd.strip()
            cmd_lower = cmd.lower()

            if "msiexec" in cmd_lower:
                cmd_clean = re.sub(r'/I\b', '/X', cmd, flags=re.IGNORECASE)
                if '/x' not in cmd_clean.lower():
                    cmd_clean = cmd_clean.replace("msiexec.exe", "msiexec.exe /X").replace("msiexec", "msiexec /X")
                if not any(kw in cmd_clean.lower() for kw in ['/qn', '/qb', '/qf', '/qr']):
                    cmd_clean += ' /qb- /norestart'
                proc = subprocess.Popen(cmd_clean, shell=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Responsive polling loop:
            # - Stops when process exits
            # - OR when user clicks skip
            # - OR when the app is confirmed removed from Windows Registry!
            max_wait = 180  # 3 minutes maximum
            start_time = time.time()
            while time.time() - start_time < max_wait:
                if _skip_step1_flag:
                    results["step1_msg"] = "ℹ️ Đã chuyển sang quét dọn Registry theo yêu cầu người dùng."
                    break
                if proc.poll() is not None:
                    results["step1_msg"] = "✅ Đã chạy xong trình gỡ cài đặt gốc."
                    break
                if reg_key_name and not _check_reg_key_exists(reg_key_name):
                    # Uninstaller has already finished and removed the registry key!
                    time.sleep(1.5)  # Brief grace period for disk cleanup
                    results["step1_msg"] = "✅ Phần mềm đã được gỡ cài đặt hoàn tất."
                    break
                time.sleep(1)
            else:
                try:
                    proc.kill()
                except Exception:
                    pass
                results["step1_msg"] = "⚠️ Hết thời gian chờ trình gỡ gốc. Chuyển sang quét dọn Registry & Thư mục rác."

            results["step1_success"] = True
        else:
            results["step1_msg"] = "ℹ️ Step 1: Không tìm thấy lệnh gỡ cài đặt."
            results["step1_success"] = True

    except Exception as e:
        results["step1_msg"] = f"⚠️ Step 1 Error: {e}"

    # Wait for the uninstaller to release all file/registry locks
    time.sleep(1.5)
    kill_app_processes(app_name, install_location)

    # Verify whether Step 1 actually removed the app from registry
    if reg_key_name:
        still_exists = _check_reg_key_exists(reg_key_name)
        results["step1_success"] = not still_exists
    else:
        results["step1_success"] = True

    # ── STEP 2: Deep Scan & Clean Windows Registry leftovers ──────────────
    try:
        del_keys = deep_scan_leftover_registry(app_name, reg_key_name)
        results["step2_keys"] = del_keys
        results["registry_cleaned"] = del_keys
    except Exception:
        results["step2_keys"] = []
        results["registry_cleaned"] = []

    # ── STEP 3: Deep Scan & Clean Folders & AppData Trash ────────────────
    try:
        del_folders = deep_scan_leftover_folders(app_name, install_location)
        results["step3_folders"] = del_folders
        results["folders_cleaned"] = del_folders
    except Exception:
        results["step3_folders"] = []
        results["folders_cleaned"] = []

    # If the app's registry key was cleaned by Step 2 or native uninstaller:
    if reg_key_name and not _check_reg_key_exists(reg_key_name):
        results["step1_success"] = True

    # ── SUMMARY ──────────────────────────────────────────────────────────
    reg_cnt = len(results["step2_keys"])
    folder_cnt = len(results["step3_folders"])
    if results["step1_success"]:
        results["summary"] = f"🎉 Đã gỡ siêu sạch {app_name}! Xóa {reg_cnt} Registry Keys và {folder_cnt} Thư mục rác."
    else:
        results["success"] = False
        results["summary"] = (f"⚠️ {app_name} có thể chưa được gỡ hoàn toàn (phần mềm vẫn còn trong Registry). "
                              f"Đã dọn {reg_cnt} Keys và {folder_cnt} Thư mục rác phụ.")

    return results


def open_app_folder(install_location, app_name):
    """Opens the installation directory of the specified application."""
    try:
        if install_location and os.path.exists(install_location):
            os.startfile(install_location)
            return {"success": True, "message": f"Đã mở thư mục: {install_location}"}

        # Search program files
        folders = find_app_folders(app_name)
        if folders and os.path.exists(folders[0]):
            os.startfile(folders[0])
            return {"success": True, "message": f"Đã mở thư mục: {folders[0]}"}

        return {"success": False, "message": "Không tìm thấy thư mục cài đặt của phần mềm này!"}
    except Exception as e:
        return {"success": False, "message": str(e)}


class UninstallManager:
    """Tkinter fallback compatibility class."""
    def __init__(self, parent=None):
        self.parent = parent

