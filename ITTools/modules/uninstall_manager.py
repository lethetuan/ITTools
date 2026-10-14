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
import base64
import glob
import json

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


def get_store_app_icon_b64(install_location):
    """Extracts a high-res PNG icon from a Windows Store App directory."""
    if not install_location or not os.path.exists(install_location):
        return ""
    patterns = [
        os.path.join(install_location, "Assets", "*Square44x44Logo*.png"),
        os.path.join(install_location, "Assets", "*Square150x150Logo*.png"),
        os.path.join(install_location, "Assets", "*storelogo*.png"),
        os.path.join(install_location, "Assets", "*Logo*.png"),
        os.path.join(install_location, "images", "*logo*.png"),
        os.path.join(install_location, "*logo*.png"),
    ]
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            normal_matches = [m for m in matches if "contrast" not in os.path.basename(m).lower()]
            best = normal_matches[0] if normal_matches else matches[0]
            try:
                with open(best, "rb") as f:
                    b64_str = base64.b64encode(f.read()).decode("utf-8")
                    return f"data:image/png;base64,{b64_str}"
            except Exception:
                pass
    return ""


def _check_store_app_exists(package_full_name="", package_name=""):
    """Returns True if the AppX package is still installed on the system."""
    try:
        if package_name:
            cmd = f"[bool](Get-AppxPackage -Name '{package_name}' -AllUsers -ErrorAction SilentlyContinue)"
        elif package_full_name:
            cmd = f"[bool](Get-AppxPackage -AllUsers -ErrorAction SilentlyContinue | Where-Object {{ $_.PackageFullName -eq '{package_full_name}' }})"
        else:
            return False
        res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=10)
        return "True" in res.stdout
    except Exception:
        return False


def clean_store_app_leftovers(package_name, package_family_name=""):
    """Scans and safely deletes leftover AppData\\Packages folders for uninstalled Store apps."""
    cleaned_folders = []
    local_app = os.environ.get('LOCALAPPDATA', '')
    if not local_app or not os.path.exists(local_app):
        return cleaned_folders

    pkgs_dir = os.path.join(local_app, 'Packages')
    if os.path.exists(pkgs_dir):
        try:
            for item in os.listdir(pkgs_dir):
                target = os.path.join(pkgs_dir, item)
                if not os.path.isdir(target):
                    continue
                matched = False
                if package_family_name and package_family_name.lower() == item.lower():
                    matched = True
                elif package_name and (item.lower().startswith(package_name.lower() + "_") or item.lower() == package_name.lower()):
                    matched = True

                if matched:
                    try:
                        shutil.rmtree(target, ignore_errors=True)
                        if not os.path.exists(target):
                            cleaned_folders.append(target)
                    except Exception:
                        pass
        except Exception:
            pass

    return cleaned_folders


def uninstall_store_app(package_full_name, package_name=""):
    """
    Thoroughly and reliably uninstalls a Windows Store (AppX) package:
    1. Force kills any active processes locking the package.
    2. Runs PowerShell removal with multi-stage fallback:
       - Stage 1: Remove-AppxPackage -Package <PackageFullName> (current user)
       - Stage 2: Remove-AppxPackage -Package <PackageFullName> -AllUsers (all user profiles)
       - Stage 3: Get-AppxPackage -Name <package_name> -AllUsers | Remove-AppxPackage -AllUsers
       - Stage 4: Remove-AppxProvisionedPackage if provisioned in Windows system image
    3. Verifies whether the package was truly removed.
    Returns dict: {"success": bool, "message": str, "errors": list}
    """
    results = {
        "success": False,
        "message": "",
        "errors": []
    }

    # 1. Kill any running processes related to package
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', package_name.lower()) if package_name else ""
    if clean_name and len(clean_name) >= 3:
        try:
            res = subprocess.run('tasklist /FO CSV /NH', shell=True, capture_output=True, text=True, errors='ignore')
            for line in res.stdout.splitlines():
                if not line:
                    continue
                proc_exe = [p.strip('"') for p in line.split(',')][0]
                proc_clean = re.sub(r'[^a-zA-Z0-9]', '', proc_exe.lower().replace('.exe', ''))
                if clean_name in proc_clean or proc_clean in clean_name:
                    subprocess.run(f'taskkill /f /im "{proc_exe}"', shell=True, capture_output=True)
        except Exception:
            pass

    # 2. Run PowerShell removal script with multi-stage fallback
    pkg_full_escaped = package_full_name.replace('"', '`"') if package_full_name else ""
    pkg_name_escaped = package_name.replace('"', '`"') if package_name else ""

    ps_script = f"""
$pkgFullName = "{pkg_full_escaped}"
$pkgName = "{pkg_name_escaped}"
$errors = @()

# Stage 1: Standard Remove-AppxPackage by PackageFullName
if ($pkgFullName) {{
    try {{
        Remove-AppxPackage -Package $pkgFullName -ErrorAction Stop
    }} catch {{
        $errors += "Stage 1 ($pkgFullName): " + $_.Exception.Message
    }}
}}

# Stage 2: Try with -AllUsers if still exists
$check1 = if ($pkgName) {{ 
    Get-AppxPackage -Name $pkgName -AllUsers -ErrorAction SilentlyContinue 
}} else {{ 
    Get-AppxPackage -AllUsers -ErrorAction SilentlyContinue | Where-Object {{ $_.PackageFullName -eq $pkgFullName }} 
}}

if ($check1 -and $pkgFullName) {{
    try {{
        Remove-AppxPackage -Package $pkgFullName -AllUsers -ErrorAction Stop
    }} catch {{
        $errors += "Stage 2 AllUsers: " + $_.Exception.Message
    }}
}}

# Stage 3: Fallback via Get-AppxPackage pipeline by Name
$check2 = if ($pkgName) {{ 
    Get-AppxPackage -Name $pkgName -AllUsers -ErrorAction SilentlyContinue 
}} else {{ $null }}

if ($check2) {{
    try {{
        Get-AppxPackage -Name $pkgName -AllUsers -ErrorAction Stop | Remove-AppxPackage -AllUsers -ErrorAction Stop
    }} catch {{
        $errors += "Stage 3 Pipeline AllUsers: " + $_.Exception.Message
    }}
    if (Get-AppxPackage -Name $pkgName -ErrorAction SilentlyContinue) {{
        try {{
            Get-AppxPackage -Name $pkgName -ErrorAction Stop | Remove-AppxPackage -ErrorAction Stop
        }} catch {{
            $errors += "Stage 3 Pipeline CurrentUser: " + $_.Exception.Message
        }}
    }}
}}

# Stage 4: Remove provisioned package so it doesn't return
try {{
    $prov = Get-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue | Where-Object {{
        ($pkgName -and ($_.DisplayName -eq $pkgName -or $_.PackageName -like "*$pkgName*")) -or
        ($pkgFullName -and $_.PackageName -eq $pkgFullName)
    }}
    if ($prov) {{
        $prov | Remove-AppxProvisionedPackage -Online -ErrorAction Stop
    }}
}} catch {{
    $errors += "Stage 4 Provisioned: " + $_.Exception.Message
}}

# Verification: Is the package completely gone?
$still = if ($pkgName) {{
    Get-AppxPackage -Name $pkgName -AllUsers -ErrorAction SilentlyContinue
}} else {{
    Get-AppxPackage -AllUsers -ErrorAction SilentlyContinue | Where-Object {{ $_.PackageFullName -eq $pkgFullName }}
}}

if ($still) {{
    Write-Output "STATUS:FAILED"
    $errors | ForEach-Object {{ Write-Output "ERR:$_" }}
}} else {{
    Write-Output "STATUS:SUCCESS"
}}
"""
    try:
        proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, timeout=90)
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()

        if "STATUS:SUCCESS" in stdout:
            results["success"] = True
            results["message"] = f"Đã gỡ bỏ thành công ứng dụng Store: {package_name or package_full_name}"
        else:
            err_lines = [l.replace("ERR:", "").strip() for l in stdout.splitlines() if l.startswith("ERR:")]
            if stderr:
                err_lines.append(stderr)
            results["success"] = False
            results["errors"] = err_lines
            err_summary = "; ".join(err_lines) if err_lines else "Gói ứng dụng vẫn tồn tại sau khi chạy lệnh gỡ bỏ."
            results["message"] = f"Không thể gỡ ứng dụng Store: {err_summary}"
    except subprocess.TimeoutExpired:
        results["success"] = False
        results["message"] = "Hết thời gian chờ lệnh gỡ ứng dụng Store (PowerShell timeout 90s)."
    except Exception as e:
        results["success"] = False
        results["message"] = f"Lỗi thực thi PowerShell: {str(e)}"

    return results


def get_store_apps():
    """Returns installed Windows Store (AppX) packages with accurate FullName, high-res icons and clean publisher names."""
    apps = []
    try:
        ps_cmd = """
try {
    Get-AppxPackage -AllUsers | Where-Object { -not $_.IsFramework -and -not $_.NonRemovable } | Select-Object Name, PackageFullName, PackageFamilyName, Publisher, Version, InstallLocation | ConvertTo-Json -Depth 2
} catch {
    Get-AppxPackage | Where-Object { -not $_.IsFramework -and -not $_.NonRemovable } | Select-Object Name, PackageFullName, PackageFamilyName, Publisher, Version, InstallLocation | ConvertTo-Json -Depth 2
}
"""
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=30)
        if res.returncode == 0 and res.stdout and res.stdout.strip():
            data = json.loads(res.stdout)
            if isinstance(data, dict):
                data = [data]
            
            # System internal packages to exclude from user uninstaller
            SYSTEM_APPX_PREFIXES = (
                'microsoft.windows.search', 'microsoft.windows.shellexperiencehost',
                'microsoft.windows.startmenuexperiencehost', 'microsoft.windows.cortana',
                'microsoft.windows.sechealthui', 'microsoft.windows.cloudexperiencehost',
                'microsoft.aad.brokerplugin', 'microsoft.accountscontrol',
                'microsoft.bioenrollment', 'microsoft.lockapp', 'microsoft.win32webviewhost',
                'microsoft.asynctextservice', 'microsoft.ecapp', 'microsoft.creddialoghost',
                'microsoft.windows.oobenetworkconnectionflow', 'microsoft.windows.narratorquickstart',
                'microsoft.windows.parentalcontrols', 'microsoft.windows.peopleexperiencehost',
                'microsoft.windows.contentdeliverymanager', 'microsoft.windows.apprep.chxapp',
                'microsoft.windows.callingdatacapture'
            )

            seen_full_names = set()

            for item in data:
                name = item.get('Name', '')
                full_name = item.get('PackageFullName', '')
                family_name = item.get('PackageFamilyName', '')
                if not name or not full_name:
                    continue

                name_lower = name.lower()
                if any(name_lower.startswith(p) for p in SYSTEM_APPX_PREFIXES):
                    continue

                if full_name in seen_full_names:
                    continue
                seen_full_names.add(full_name)

                # Clean display name
                parts = name.split('_')
                disp = parts[0] if parts else name

                # Clean publisher name (extract from CN=... if present)
                raw_pub = item.get('Publisher', '')
                clean_pub = raw_pub
                if raw_pub:
                    m = re.search(r'CN=([^,]+)', raw_pub)
                    if m:
                        clean_pub = m.group(1).strip()
                    elif raw_pub.startswith("CN="):
                        clean_pub = raw_pub.replace("CN=", "").strip()
                if not clean_pub:
                    clean_pub = "Microsoft Store"

                loc = item.get('InstallLocation', '')
                version = item.get('Version', '1.0')

                # Native high-res PNG icon extraction for AppX packages
                icon_b64 = get_store_app_icon_b64(loc)

                apps.append({
                    "display_name": disp,
                    "name": disp,
                    "publisher": clean_pub,
                    "install_date": "Store Package",
                    "date": "Store Package",
                    "estimated_size": 0,
                    "size": "--",
                    "display_version": version,
                    "version": version,
                    "uninstall_cmd": f'Remove-AppxPackage -Package "{full_name}"',
                    "uninstall": f'Remove-AppxPackage -Package "{full_name}"',
                    "install_location": loc,
                    "reg_key_name": name,
                    "package_full_name": full_name,
                    "package_family_name": family_name,
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


def run_deep_clean_uninstall(app_name, uninstall_cmd, install_location=None, reg_key_name="", is_store=False, package_full_name=""):
    """
    Executes the 3-Step Your Uninstaller! Wizard process:
    For Store (AppX) Apps:
      Step 1: Terminate app processes & run PowerShell AppX uninstaller with multi-stage fallback
      Step 2: Deep scan & clean Windows Registry leftovers
      Step 3: Deep scan & clean AppData\\Packages leftovers
    For Win32 Apps:
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

    # ── BRANCH A: WINDOWS STORE (APPX) PACKAGES ──────────────────────────
    if is_store or (uninstall_cmd and "Remove-AppxPackage" in uninstall_cmd):
        pkg_full = package_full_name
        if not pkg_full and uninstall_cmd:
            m = re.search(r'Remove-AppxPackage\s+(?:-Package\s+)?["\']?([^"\']+)["\']?', uninstall_cmd, re.I)
            if m:
                cand = m.group(1).strip()
                if "_" in cand:
                    pkg_full = cand
        if not pkg_full and install_location and "WindowsApps" in install_location:
            pkg_full = os.path.basename(install_location.rstrip(r'\/'))
        if not pkg_full and reg_key_name and "_" in reg_key_name:
            pkg_full = reg_key_name

        pkg_name = reg_key_name if (reg_key_name and "_" not in reg_key_name) else (app_name or "")
        if "_" in pkg_name and not pkg_full:
            pkg_full = pkg_name
            pkg_name = pkg_name.split('_')[0]
        elif "_" in pkg_name:
            pkg_name = pkg_name.split('_')[0]

        # Step 1: Run Store uninstallation with multi-stage fallback
        store_res = uninstall_store_app(pkg_full, pkg_name)
        results["step1_success"] = store_res["success"]
        results["step1_msg"] = store_res["message"]

        # Step 2: Clean registry leftovers (vendor/app keys in HKCU/HKLM Software)
        try:
            del_keys = deep_scan_leftover_registry(pkg_name or app_name, "")
            results["step2_keys"] = del_keys
            results["registry_cleaned"] = del_keys
        except Exception:
            results["step2_keys"] = []
            results["registry_cleaned"] = []

        # Step 3: Clean Store AppData packages leftovers
        family_name = ""
        if pkg_full and "_" in pkg_full:
            parts = pkg_full.split('_')
            if len(parts) >= 5:
                family_name = f"{parts[0]}_{parts[-1]}"
        try:
            del_folders = clean_store_app_leftovers(pkg_name or app_name, family_name)
            results["step3_folders"] = del_folders
            results["folders_cleaned"] = del_folders
        except Exception:
            results["step3_folders"] = []
            results["folders_cleaned"] = []

        reg_cnt = len(results["step2_keys"])
        folder_cnt = len(results["step3_folders"])

        if results["step1_success"]:
            results["success"] = True
            results["summary"] = f"🎉 Đã gỡ siêu sạch Store App '{app_name}'! Xóa {reg_cnt} Registry Keys và {folder_cnt} Thư mục rác."
        else:
            results["success"] = False
            results["summary"] = f"⚠️ Không thể gỡ ứng dụng Store '{app_name}': {results['step1_msg']}"

        return results

    # ── BRANCH B: WIN32 DESKTOP APPLICATIONS ─────────────────────────────
    # Kill any running processes first to release file & registry locks
    kill_app_processes(app_name, install_location)

    # ── STEP 1: Run Default Uninstaller (Interactive — user sees the window) ──
    try:
        if uninstall_cmd:
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
            try:
                os.startfile(install_location)
                return {"success": True, "message": f"Đã mở thư mục: {install_location}"}
            except Exception:
                pass

        # Check AppData Packages folder for Store apps
        local_app = os.environ.get('LOCALAPPDATA', '')
        if local_app:
            pkgs_dir = os.path.join(local_app, 'Packages')
            if os.path.exists(pkgs_dir):
                for item in os.listdir(pkgs_dir):
                    if app_name and (app_name.lower() in item.lower()):
                        pkg_path = os.path.join(pkgs_dir, item)
                        try:
                            os.startfile(pkg_path)
                            return {"success": True, "message": f"Đã mở thư mục dữ liệu AppData: {pkg_path}"}
                        except Exception:
                            pass

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

