"""
Browser Backup/Restore Module 2026 - Chrome, Edge, Brave, Cốc Cốc, Firefox, Opera
Author: Lê Thế Tuấn | 0352 194 195 | https://lethetuanpc.blogspot.com | Telegram: https://t.me/lethetuanpc
"""

import os
import sys
import shutil
import json
import subprocess
import datetime
import threading
import glob
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS


def get_browser_definitions():
    """Returns definition dictionary for all popular Windows web browsers."""
    localappdata = os.environ.get('LOCALAPPDATA', '')
    appdata = os.environ.get('APPDATA', '')

    return {
        'Chrome': {
            'name': 'Google Chrome',
            'icon': '🌐',
            'type': 'chromium',
            'process': ['chrome.exe'],
            'profile_root': os.path.join(localappdata, r'Google\Chrome\User Data'),
        },
        'Edge': {
            'name': 'Microsoft Edge',
            'icon': '🌊',
            'type': 'chromium',
            'process': ['msedge.exe'],
            'profile_root': os.path.join(localappdata, r'Microsoft\Edge\User Data'),
        },
        'Brave': {
            'name': 'Brave Browser',
            'icon': '🦁',
            'type': 'chromium',
            'process': ['brave.exe'],
            'profile_root': os.path.join(localappdata, r'BraveSoftware\Brave-Browser\User Data'),
        },
        'CocCoc': {
            'name': 'Cốc Cốc Browser',
            'icon': '🥥',
            'type': 'chromium',
            'process': ['browser.exe', 'coccoc.exe'],
            'profile_root': os.path.join(localappdata, r'CocCoc\Browser\User Data'),
        },
        'Firefox': {
            'name': 'Mozilla Firefox',
            'icon': '🦊',
            'type': 'firefox',
            'process': ['firefox.exe'],
            'profile_root': os.path.join(appdata, r'Mozilla\Firefox\Profiles'),
        },
        'Opera': {
            'name': 'Opera Stable',
            'icon': '🔴',
            'type': 'opera',
            'process': ['opera.exe'],
            'profile_root': os.path.join(appdata, r'Opera Software\Opera Stable'),
        },
        'OperaGX': {
            'name': 'Opera GX',
            'icon': '🎮',
            'type': 'opera',
            'process': ['opera.exe'],
            'profile_root': os.path.join(appdata, r'Opera Software\Opera GX Stable'),
        }
    }


def fmt_bytes(size):
    """Formats bytes into human readable string."""
    if not size or size <= 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def get_dir_size_fast(path, max_files=1000):
    """Fast size estimation for directory."""
    total = 0
    count = 0
    try:
        if not os.path.exists(path):
            return 0
        for root, dirs, files in os.walk(path):
            # Skip heavy cache folders
            dirs[:] = [d for d in dirs if d.lower() not in ['cache', 'code cache', 'gpucache', 'cache2', 'startupcache']]
            for f in files:
                try:
                    fp = os.path.join(root, f)
                    total += os.path.getsize(fp)
                    count += 1
                    if count >= max_files:
                        break
                except Exception:
                    pass
            if count >= max_files:
                break
    except Exception:
        pass
    return total


import winreg


def find_browser_exe_path(browser_key):
    """Dynamically finds installed executable file path for the browser."""
    definitions = get_browser_definitions()
    info = definitions.get(browser_key, {})
    proc_names = info.get('process', [])
    
    localappdata = os.environ.get('LOCALAPPDATA', '')
    programfiles = os.environ.get('ProgramFiles', 'C:\\Program Files')
    programfilesx86 = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')

    # 1. Search Registry App Paths
    for proc in proc_names:
        for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            for sub in [
                f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{proc}",
                f"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{proc}"
            ]:
                try:
                    with winreg.OpenKey(root, sub) as k:
                        val, _ = winreg.QueryValueEx(k, "")
                        val = val.strip('"')
                        if os.path.exists(val) and os.path.isfile(val):
                            return val
                except Exception:
                    pass

    # 2. Search Registry StartMenuInternet
    for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
        for sub in [r"SOFTWARE\Clients\StartMenuInternet", r"SOFTWARE\WOW6432Node\Clients\StartMenuInternet"]:
            try:
                with winreg.OpenKey(root, sub) as key:
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(num_subkeys):
                        sname = winreg.EnumKey(key, i)
                        sname_lower = sname.lower()
                        b_key_lower = browser_key.lower()
                        match = False
                        if b_key_lower in sname_lower:
                            match = True
                        elif browser_key == 'Edge' and ('edge' in sname_lower or 'msedge' in sname_lower):
                            match = True
                        elif browser_key == 'CocCoc' and ('coccoc' in sname_lower or 'corom' in sname_lower):
                            match = True
                        elif browser_key == 'Chrome' and 'chrome' in sname_lower:
                            match = True
                        
                        if match:
                            try:
                                with winreg.OpenKey(key, rf"{sname}\shell\open\command") as cmd_k:
                                    val, _ = winreg.QueryValueEx(cmd_k, "")
                                    val = val.strip('"')
                                    if '.exe' in val.lower():
                                        val = val.split('.exe')[0] + '.exe'
                                        val = val.strip('"')
                                    if os.path.exists(val) and os.path.isfile(val):
                                        return val
                            except Exception:
                                pass
            except Exception:
                pass

    # 3. Search Common Glob Patterns
    glob_patterns = {
        'Chrome': [
            os.path.join(programfiles, r'Google\Chrome\Application\chrome.exe'),
            os.path.join(programfilesx86, r'Google\Chrome\Application\chrome.exe'),
            os.path.join(localappdata, r'Google\Chrome\Application\chrome.exe'),
        ],
        'Edge': [
            os.path.join(programfilesx86, r'Microsoft\Edge\Application\msedge.exe'),
            os.path.join(programfiles, r'Microsoft\Edge\Application\msedge.exe'),
            r'C:\Program Files (x86)\Microsoft\Edge*\*\msedge.exe',
            r'C:\Program Files\Microsoft\Edge*\*\msedge.exe',
            os.path.join(localappdata, r'Microsoft\Edge\Application\msedge.exe'),
        ],
        'Brave': [
            os.path.join(programfiles, r'BraveSoftware\Brave-Browser\Application\brave.exe'),
            os.path.join(programfilesx86, r'BraveSoftware\Brave-Browser\Application\brave.exe'),
            os.path.join(localappdata, r'BraveSoftware\Brave-Browser\Application\brave.exe'),
        ],
        'CocCoc': [
            os.path.join(localappdata, r'CocCoc\Browser\Application\browser.exe'),
            os.path.join(localappdata, r'CocCoc\Browser\Application\coccoc.exe'),
            os.path.join(programfiles, r'CocCoc\Browser\Application\browser.exe'),
            os.path.join(programfilesx86, r'CocCoc\Browser\Application\browser.exe'),
        ],
        'Firefox': [
            os.path.join(programfiles, r'Mozilla Firefox\firefox.exe'),
            os.path.join(programfilesx86, r'Mozilla Firefox\firefox.exe'),
            os.path.join(localappdata, r'Mozilla Firefox\firefox.exe'),
        ],
        'Opera': [
            os.path.join(localappdata, r'Programs\Opera\opera.exe'),
            os.path.join(localappdata, r'Programs\Opera Stable\opera.exe'),
            os.path.join(programfiles, r'Opera\opera.exe'),
            os.path.join(programfilesx86, r'Opera\opera.exe'),
        ],
        'OperaGX': [
            os.path.join(localappdata, r'Programs\Opera GX\opera.exe'),
            os.path.join(programfiles, r'Opera GX\opera.exe'),
            os.path.join(programfilesx86, r'Opera GX\opera.exe'),
        ]
    }

    patterns = glob_patterns.get(browser_key, [])
    for pat in patterns:
        matches = glob.glob(pat)
        for m in matches:
            if os.path.exists(m) and os.path.isfile(m):
                return m

    # 4. Search Windows Uninstall Registry
    for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
        for sub in [
            r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
            r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'
        ]:
            try:
                with winreg.OpenKey(root, sub) as ukey:
                    for i in range(winreg.QueryInfoKey(ukey)[0]):
                        try:
                            kname = winreg.EnumKey(ukey, i)
                            with winreg.OpenKey(ukey, kname) as sk:
                                dn = winreg.QueryValueEx(sk, 'DisplayName')[0]
                                b_name = info['name'].lower()
                                if browser_key.lower() in dn.lower() or b_name in dn.lower():
                                    try:
                                        icon_val = winreg.QueryValueEx(sk, 'DisplayIcon')[0]
                                        icon_clean = icon_val.split(',')[0].strip('"')
                                        if os.path.exists(icon_clean) and icon_clean.lower().endswith('.exe'):
                                            return icon_clean
                                    except Exception:
                                        pass
                                    try:
                                        loc_val = winreg.QueryValueEx(sk, 'InstallLocation')[0].strip('"')
                                        for proc in proc_names:
                                            cand = os.path.join(loc_val, proc)
                                            if os.path.exists(cand) and os.path.isfile(cand):
                                                return cand
                                    except Exception:
                                        pass
                        except Exception:
                            pass
            except Exception:
                pass

    return None


def extract_exe_icon_base64(exe_path):
    """Extracts associated icon from Windows EXE file using PowerShell System.Drawing API."""
    if not exe_path or not os.path.exists(exe_path):
        return None

    exe_path_clean = exe_path.replace("'", "''")
    script = f'''
    try {{
        [Reflection.Assembly]::LoadWithPartialName("System.Drawing") | Out-Null
        $icon = [System.Drawing.Icon]::ExtractAssociatedIcon('{exe_path_clean}')
        if ($icon) {{
            $bmp = $icon.ToBitmap()
            $ms = New-Object System.IO.MemoryStream
            $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
            [Convert]::ToBase64String($ms.ToArray())
        }}
    }} catch {{
        Write-Output ""
    }}
    '''

    try:
        r = subprocess.run(['powershell', '-NoProfile', '-Command', script], capture_output=True, text=True, timeout=6)
        b64 = r.stdout.strip()
        if b64 and len(b64) > 100:
            return f"data:image/png;base64,{b64}"
    except Exception:
        pass

    return None


def get_detected_browsers():
    """Detects installed browsers, profile details, and extracts native Windows executable icons."""
    definitions = get_browser_definitions()
    results = []

    for key, info in definitions.items():
        root = info['profile_root']
        exe_p = find_browser_exe_path(key)
        # Chỉ coi là đã cài đặt nếu file thực thi EXE của trình duyệt thực sự tồn tại trên máy
        is_installed = bool(exe_p and os.path.exists(exe_p))
        has_profile = bool(root and os.path.exists(root))

        size_str = "0 B"
        items = {
            'bookmarks': False,
            'passwords': False,
            'history': False,
            'extensions': False,
            'full_profile': False
        }
        profiles_found = []
        real_icon = None

        if is_installed:
            real_icon = extract_exe_icon_base64(exe_p)
            b_type = info['type']

            if has_profile:
                items['full_profile'] = True
                
                if b_type == 'chromium':
                    profile_dirs = glob.glob(os.path.join(root, 'Default')) + glob.glob(os.path.join(root, 'Profile *'))
                    if not profile_dirs and os.path.exists(root):
                        profile_dirs = [root]
                    
                    for pd in profile_dirs:
                        pname = os.path.basename(pd)
                        profiles_found.append(pname)
                        if os.path.exists(os.path.join(pd, 'Bookmarks')):
                            items['bookmarks'] = True
                        if os.path.exists(os.path.join(pd, 'Login Data')) or os.path.exists(os.path.join(pd, 'Login Data For Account')):
                            items['passwords'] = True
                        if os.path.exists(os.path.join(pd, 'History')):
                            items['history'] = True
                        if os.path.exists(os.path.join(pd, 'Extensions')):
                            items['extensions'] = True
                
                elif b_type == 'firefox':
                    p_dirs = [d for d in glob.glob(os.path.join(root, '*')) if os.path.isdir(d)]
                    for pd in p_dirs:
                        profiles_found.append(os.path.basename(pd))
                        if os.path.exists(os.path.join(pd, 'places.sqlite')):
                            items['bookmarks'] = True
                            items['history'] = True
                        if os.path.exists(os.path.join(pd, 'key4.db')) or os.path.exists(os.path.join(pd, 'logins.json')):
                            items['passwords'] = True
                        if os.path.exists(os.path.join(pd, 'extensions')):
                            items['extensions'] = True

                elif b_type == 'opera':
                    profiles_found.append('Default')
                    if os.path.exists(os.path.join(root, 'Bookmarks')):
                        items['bookmarks'] = True
                    if os.path.exists(os.path.join(root, 'Login Data')):
                        items['passwords'] = True
                    if os.path.exists(os.path.join(root, 'History')):
                        items['history'] = True
                    if os.path.exists(os.path.join(root, 'Extensions')):
                        items['extensions'] = True

                size_bytes = get_dir_size_fast(root)
                size_str = fmt_bytes(size_bytes)
            else:
                size_str = "Chưa có profile"

        results.append({
            'key': key,
            'name': info['name'],
            'icon': info['icon'],
            'real_icon': real_icon,
            'type': info['type'],
            'is_installed': is_installed,
            'has_profile': has_profile,
            'exe_path': exe_p,
            'profile_root': root,
            'size': size_str,
            'items': items,
            'profiles_count': len(profiles_found)
        })

    return results


def close_browser_processes(process_names):
    """Closes running processes and child process trees for specified browsers."""
    import time
    for proc in process_names:
        try:
            subprocess.run(f'taskkill /f /t /im "{proc}"', shell=True, capture_output=True)
        except Exception:
            pass
    time.sleep(0.5)


def _copy_file_safe(src, dst):
    """Safely copies file ignoring locks and removing read-only attributes."""
    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            try:
                os.chmod(dst, 0o777)
            except Exception:
                pass
        shutil.copy2(src, dst)
        return True
    except Exception:
        try:
            if os.path.exists(dst):
                try:
                    os.chmod(dst, 0o777)
                except Exception:
                    pass
            # Fallback byte copy
            with open(src, 'rb') as f_in:
                data = f_in.read()
            with open(dst, 'wb') as f_out:
                f_out.write(data)
            return True
        except Exception:
            return False


def _copy_tree_safe(src, dst, ignore_patterns=None):
    """Copies directory recursively skipping locks and heavy cache."""
    if not os.path.exists(src):
        return 0
    copied_count = 0
    skip_dirs = {'cache', 'code cache', 'gpucache', 'cache2', 'startupcache', 'crashpad', 'gpuCache'}
    
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d.lower() not in skip_dirs]
        rel_path = os.path.relpath(root, src)
        dest_dir = os.path.join(dst, rel_path) if rel_path != '.' else dst
        os.makedirs(dest_dir, exist_ok=True)
        
        for f in files:
            if f.lower().endswith(('.lock', '.tmp')):
                continue
            src_file = os.path.join(root, f)
            dst_file = os.path.join(dest_dir, f)
            if _copy_file_safe(src_file, dst_file):
                copied_count += 1
    return copied_count


def get_default_backup_dir():
    """
    Finds the optimal default backup directory.
    Prefers non-system drives (D:, E:, F:, G:) over system drive (C:) so that
    backups are safe across OS re-installations.
    """
    for letter in ['D', 'E', 'F', 'G', 'H']:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            try:
                candidate = os.path.join(drive, 'Browser_Backups')
                os.makedirs(candidate, exist_ok=True)
                return candidate
            except Exception:
                continue

    user_profile = os.environ.get('USERPROFILE', 'C:\\')
    default_c = os.path.join(user_profile, 'Desktop', 'Browser_Backups')
    try:
        os.makedirs(default_c, exist_ok=True)
    except Exception:
        pass
    return default_c


def backup_browser_data(selected_browsers, options, target_dir="", logger=None, progress_callback=None):
    """Performs full backup of selected browsers based on options with real-time progress callbacks."""
    definitions = get_browser_definitions()
    
    def log(msg, level="INFO"):
        if logger:
            if hasattr(logger, 'log'):
                logger.log(level, msg)
            elif callable(logger):
                logger(msg)

    def report(percent, browser_name, step_title, detail, log_msg=None):
        if log_msg:
            log(log_msg)
        if progress_callback and callable(progress_callback):
            try:
                progress_callback(percent, browser_name, step_title, detail, log_msg)
            except Exception:
                pass

    if not target_dir or not target_dir.strip():
        target_dir = get_default_backup_dir()

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder_name = f"BrowserBackup_{timestamp}"
    backup_path = os.path.join(target_dir, backup_folder_name)
    os.makedirs(backup_path, exist_ok=True)

    report(5, "", "Khởi tạo thư mục sao lưu", f"Tạo thư mục: {backup_folder_name}", f"Bắt đầu sao lưu trình duyệt vào thư mục: {backup_path}...")

    manifest = {
        'timestamp': timestamp,
        'created_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'browsers': {},
        'options': options
    }

    success_count = 0
    valid_browsers = [b for b in selected_browsers if b in definitions]
    total_browsers = max(1, len(valid_browsers))

    for idx, b_key in enumerate(valid_browsers):
        info = definitions[b_key]
        root = info['profile_root']
        b_name = info['name']

        b_pct_start = 5 + int((idx / total_browsers) * 85)
        b_pct_end = 5 + int(((idx + 1) / total_browsers) * 85)
        b_range = b_pct_end - b_pct_start

        if not os.path.exists(root):
            report(b_pct_end, b_name, f"Bỏ qua {b_name}", f"Chưa có dữ liệu profile ({root})", f"Bỏ qua {b_name}: Không tìm thấy thư mục profile ({root})")
            continue

        report(b_pct_start, b_name, f"Đang chuẩn bị {b_name}", f"Kiểm tra và đóng tiến trình {b_name}...", f"Đang sao lưu {b_name}...")
        b_backup_dir = os.path.join(backup_path, b_key)
        os.makedirs(b_backup_dir, exist_ok=True)
        
        # Kill process if necessary
        close_browser_processes(info['process'])

        b_manifest = {'type': info['type'], 'files_backed_up': 0, 'status': 'ok'}

        if info['type'] == 'chromium':
            profile_dirs = glob.glob(os.path.join(root, 'Default')) + glob.glob(os.path.join(root, 'Profile *'))
            if not profile_dirs:
                profile_dirs = [root]

            for pd in profile_dirs:
                pname = os.path.basename(pd)
                pd_dest = os.path.join(b_backup_dir, pname)
                os.makedirs(pd_dest, exist_ok=True)

                if options.get('full_profile'):
                    report(b_pct_start + int(b_range * 0.4), b_name, f"Sao lưu Toàn Bộ Hồ Sơ {pname}", f"Đang sao chép các tệp hồ sơ người dùng...", f"  ➜ Sao lưu Toàn Bộ Hồ Sơ (Full Profile) {pname}...")
                    count = _copy_tree_safe(pd, pd_dest)
                    b_manifest['files_backed_up'] += count
                else:
                    if options.get('bookmarks'):
                        report(b_pct_start + int(b_range * 0.2), b_name, f"Sao lưu Dấu trang (Bookmarks)", f"{pname} - Đang sao chép Bookmarks...", None)
                        bm = os.path.join(pd, 'Bookmarks')
                        if os.path.exists(bm):
                            _copy_file_safe(bm, os.path.join(pd_dest, 'Bookmarks'))
                            b_manifest['files_backed_up'] += 1
                            report(b_pct_start + int(b_range * 0.3), b_name, f"Đã lưu Bookmarks", f"{pname} - Bookmarks hoàn tất", f"  ✅ [Bookmarks] {b_name} ({pname})")

                    if options.get('passwords'):
                        report(b_pct_start + int(b_range * 0.4), b_name, f"Sao lưu Mật khẩu & Đăng nhập", f"{pname} - Đang sao chép Login Data...", None)
                        for pass_file in ['Login Data', 'Login Data For Account', 'Web Data']:
                            pf = os.path.join(pd, pass_file)
                            if os.path.exists(pf):
                                _copy_file_safe(pf, os.path.join(pd_dest, pass_file))
                                b_manifest['files_backed_up'] += 1
                        report(b_pct_start + int(b_range * 0.5), b_name, f"Đã lưu Mật khẩu", f"{pname} - Mật khẩu hoàn tất", f"  ✅ [Passwords & Login Data] {b_name} ({pname})")

                    if options.get('history'):
                        report(b_pct_start + int(b_range * 0.6), b_name, f"Sao lưu Lịch sử duyệt web", f"{pname} - Đang sao chép History...", None)
                        hf = os.path.join(pd, 'History')
                        if os.path.exists(hf):
                            _copy_file_safe(hf, os.path.join(pd_dest, 'History'))
                            b_manifest['files_backed_up'] += 1
                        report(b_pct_start + int(b_range * 0.7), b_name, f"Đã lưu Lịch sử", f"{pname} - History hoàn tất", f"  ✅ [History] {b_name} ({pname})")

                    if options.get('extensions'):
                        report(b_pct_start + int(b_range * 0.8), b_name, f"Sao lưu Tiện ích mở rộng", f"{pname} - Đang sao chép Extensions...", None)
                        ext_dir = os.path.join(pd, 'Extensions')
                        if os.path.exists(ext_dir):
                            count = _copy_tree_safe(ext_dir, os.path.join(pd_dest, 'Extensions'))
                            b_manifest['files_backed_up'] += count
                        report(b_pct_start + int(b_range * 0.9), b_name, f"Đã lưu Tiện ích", f"{pname} - Extensions hoàn tất", f"  ✅ [Extensions] {b_name} ({pname})")

        elif info['type'] == 'firefox':
            p_dirs = [d for d in glob.glob(os.path.join(root, '*')) if os.path.isdir(d)]
            for pd in p_dirs:
                pname = os.path.basename(pd)
                pd_dest = os.path.join(b_backup_dir, pname)
                os.makedirs(pd_dest, exist_ok=True)

                if options.get('full_profile'):
                    report(b_pct_start + int(b_range * 0.5), b_name, f"Sao lưu Toàn Bộ Hồ Sơ Firefox {pname}", "Đang sao chép toàn bộ tệp profile...", f"  ➜ Sao lưu Toàn Bộ Hồ Sơ Firefox {pname}...")
                    count = _copy_tree_safe(pd, pd_dest)
                    b_manifest['files_backed_up'] += count
                else:
                    if options.get('bookmarks') or options.get('history'):
                        for f in ['places.sqlite', 'favicons.sqlite']:
                            fp = os.path.join(pd, f)
                            if os.path.exists(fp):
                                _copy_file_safe(fp, os.path.join(pd_dest, f))
                                b_manifest['files_backed_up'] += 1
                        report(b_pct_start + int(b_range * 0.4), b_name, f"Đã lưu Bookmarks & History", f"Firefox {pname}", f"  ✅ [Bookmarks & History] Firefox {pname}")

                    if options.get('passwords'):
                        for f in ['key4.db', 'logins.json']:
                            fp = os.path.join(pd, f)
                            if os.path.exists(fp):
                                _copy_file_safe(fp, os.path.join(pd_dest, f))
                                b_manifest['files_backed_up'] += 1
                        report(b_pct_start + int(b_range * 0.8), b_name, f"Đã lưu Mật khẩu Firefox", f"Firefox {pname}", f"  ✅ [Passwords] Firefox {pname}")

        elif info['type'] == 'opera':
            pd_dest = os.path.join(b_backup_dir, 'Default')
            os.makedirs(pd_dest, exist_ok=True)
            if options.get('full_profile'):
                count = _copy_tree_safe(root, pd_dest)
                b_manifest['files_backed_up'] += count
            else:
                for target_file, opt_key in [('Bookmarks', 'bookmarks'), ('Login Data', 'passwords'), ('History', 'history')]:
                    if options.get(opt_key):
                        fp = os.path.join(root, target_file)
                        if os.path.exists(fp):
                            _copy_file_safe(fp, os.path.join(pd_dest, target_file))
                            b_manifest['files_backed_up'] += 1

        manifest['browsers'][b_key] = b_manifest
        success_count += 1
        report(b_pct_end, b_name, f"Hoàn tất {b_name}", f"Đã sao lưu thành công {b_name}", f"Hoàn tất sao lưu {b_name}")

    # Save manifest.json
    report(95, "", "Đang ghi Manifest", "Lưu thông tin gói sao lưu manifest.json...", "Đang lưu manifest.json...")
    manifest_path = os.path.join(backup_path, 'manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    package_size = fmt_bytes(get_dir_size_fast(backup_path))
    report(100, "", "Sao lưu hoàn tất!", f"Đã lưu thành công {success_count} trình duyệt ({package_size})", f"🎉 Hoàn tất sao lưu {success_count} trình duyệt! Dung lượng: {package_size}")

    return {
        'success': True,
        'backup_dir': backup_path,
        'folder_name': backup_folder_name,
        'timestamp': timestamp,
        'browsers_count': success_count,
        'size': package_size,
        'message': f"Đã sao lưu thành công {success_count} trình duyệt ({package_size}) vào:\n{backup_path}"
    }


def resolve_restore_plan(backup_folder, selected_browsers, definitions):
    """
    Intelligently maps backup sources to browser definitions and profiles.
    Accommodates:
    - User selected the Root backup package (e.g. BrowserBackup_YYYYMMDD_HHMMSS)
    - User selected a Browser folder directly (e.g. BrowserBackup_.../Brave or C:/MyBackups/Brave)
    - User selected a Profile folder directly (e.g. BrowserBackup_.../Brave/Default)
    - User selected a folder where backup files (Bookmarks, History...) are located directly
    """
    plan = {}
    norm_folder = os.path.normpath(backup_folder.strip().strip('"'))
    folder_name = os.path.basename(norm_folder)
    parent_dir = os.path.dirname(norm_folder)
    parent_name = os.path.basename(parent_dir) if parent_dir else ""

    # Detect if selected folder name or its parent name matches any known browser
    matched_browser_by_folder = None
    matched_browser_by_parent = None
    for b_k, b_inf in definitions.items():
        if folder_name.lower() in [b_k.lower(), b_inf['name'].lower()]:
            matched_browser_by_folder = b_k
        if parent_name and parent_name.lower() in [b_k.lower(), b_inf['name'].lower()]:
            matched_browser_by_parent = b_k

    # Determine candidate browser keys to examine
    candidates = list(selected_browsers) if selected_browsers else []
    if matched_browser_by_folder and matched_browser_by_folder not in candidates:
        candidates.append(matched_browser_by_folder)
    if matched_browser_by_parent and matched_browser_by_parent not in candidates:
        candidates.append(matched_browser_by_parent)

    valid_candidates = [b for b in candidates if b in definitions]
    if not valid_candidates:
        valid_candidates = list(definitions.keys())

    for b_key in valid_candidates:
        info = definitions[b_key]
        b_name = info['name']

        src_dir = None
        is_direct_profile = False

        # 1. Direct subfolder matching browser key or browser name inside norm_folder
        c_sub = os.path.join(norm_folder, b_key)
        c_name = os.path.join(norm_folder, b_name)
        if os.path.isdir(c_sub):
            src_dir = c_sub
        elif os.path.isdir(c_name):
            src_dir = c_name
        
        # 2. norm_folder IS the browser's backup folder (e.g. ".../Brave")
        elif matched_browser_by_folder == b_key:
            src_dir = norm_folder

        # 3. norm_folder is a profile folder inside browser folder (e.g. ".../Brave/Default")
        elif matched_browser_by_parent == b_key:
            src_dir = norm_folder
            is_direct_profile = True

        # 4. Sibling folder under parent_dir
        # (e.g. user selected ".../BrowserBackup_.../Brave" but also wants Edge, and parent has "Edge")
        elif parent_dir and os.path.isdir(os.path.join(parent_dir, b_key)):
            src_dir = os.path.join(parent_dir, b_key)

        # 5. Fallback: norm_folder contains profile data (Default, Bookmarks, History, Login Data...)
        # and user only selected 1 browser or b_key is the first/only candidate
        elif not src_dir and len(valid_candidates) == 1:
            if os.path.isdir(os.path.join(norm_folder, 'Default')):
                src_dir = norm_folder
            elif any(os.path.exists(os.path.join(norm_folder, x)) for x in ['Bookmarks', 'History', 'Login Data', 'Web Data', 'prefs.js']):
                src_dir = norm_folder
                is_direct_profile = True

        if not src_dir or not os.path.exists(src_dir):
            continue

        # Now extract list of profiles from src_dir
        profiles = []
        if is_direct_profile:
            pname = folder_name if folder_name.lower().startswith(('default', 'profile')) else 'Default'
            profiles.append({'src': src_dir, 'target_profile': pname})
        else:
            # Check subdirectories
            sub_dirs = [d for d in glob.glob(os.path.join(src_dir, '*')) if os.path.isdir(d)]
            p_subdirs = [d for d in sub_dirs if os.path.basename(d).lower().startswith(('default', 'profile'))]
            if not p_subdirs and info['type'] == 'firefox' and sub_dirs:
                p_subdirs = sub_dirs
            elif not p_subdirs and sub_dirs:
                p_subdirs = sub_dirs

            if p_subdirs:
                for pd in p_subdirs:
                    profiles.append({'src': pd, 'target_profile': os.path.basename(pd)})
            else:
                # Direct files in src_dir
                profiles.append({'src': src_dir, 'target_profile': 'Default'})

        if profiles:
            plan[b_key] = {
                'info': info,
                'src_dir': src_dir,
                'profiles': profiles
            }

    return plan


def restore_browser_data(backup_folder, selected_browsers, options=None, logger=None, progress_callback=None):
    """Restores browser data from backup folder with real-time progress callbacks."""
    definitions = get_browser_definitions()
    
    def log(msg, level="INFO"):
        if logger:
            if hasattr(logger, 'log'):
                logger.log(level, msg)
            elif callable(logger):
                logger(msg)

    def report(percent, browser_name, step_title, detail, log_msg=None):
        if log_msg:
            log(log_msg)
        if progress_callback and callable(progress_callback):
            try:
                progress_callback(percent, browser_name, step_title, detail, log_msg)
            except Exception:
                pass

    if not backup_folder or not os.path.exists(backup_folder):
        return {'success': False, 'message': 'Thư mục Sao Lưu không tồn tại!'}

    norm_folder = os.path.normpath(backup_folder.strip().strip('"'))
    report(5, "", "Đọc thông tin bản sao lưu", f"Kiểm tra thư mục: {norm_folder}", f"Đang tiến hành phân tích thư mục: {norm_folder}...")

    # Plan restore
    plan = resolve_restore_plan(norm_folder, selected_browsers, definitions)

    if not plan:
        report(100, "", "Không tìm thấy dữ liệu", "Thư mục không chứa bản sao lưu hợp lệ", f"❌ Không tìm thấy bản sao lưu trình duyệt hợp lệ trong: {norm_folder}")
        return {
            'success': False,
            'browsers_count': 0,
            'message': f"Không tìm thấy bản sao lưu trình duyệt hợp lệ trong:\n{norm_folder}\n\nVui lòng kiểm tra lại thư mục đã chọn!"
        }

    restored_count = 0
    total_browsers = max(1, len(plan))

    for idx, (b_key, p_data) in enumerate(plan.items()):
        info = p_data['info']
        b_name = info['name']
        profiles = p_data['profiles']
        
        b_pct_start = 5 + int((idx / total_browsers) * 90)
        b_pct_end = 5 + int(((idx + 1) / total_browsers) * 90)

        target_root = info['profile_root']
        os.makedirs(target_root, exist_ok=True)

        report(b_pct_start, b_name, f"Đang phục hồi {b_name}", f"Đóng tiến trình {b_name} và sao chép dữ liệu...", f"Đang phục hồi cho {b_name}...")
        close_browser_processes(info['process'])

        browser_files_count = 0
        for p_idx, prof in enumerate(profiles):
            src_p = prof['src']
            target_profile_name = prof['target_profile']
            target_profile = os.path.join(target_root, target_profile_name) if info['type'] in ['chromium', 'firefox'] else target_root
            os.makedirs(target_profile, exist_ok=True)

            step_sub_pct = b_pct_start + int((p_idx + 0.5) / len(profiles) * (b_pct_end - b_pct_start))
            report(step_sub_pct, b_name, f"Đang phục hồi hồ sơ {target_profile_name}", f"Sao chép dữ liệu từ {os.path.basename(src_p)}...", None)

            count = _copy_tree_safe(src_p, target_profile)
            browser_files_count += count
            
            step_done_pct = b_pct_start + int((p_idx + 1) / len(profiles) * (b_pct_end - b_pct_start))
            report(step_done_pct, b_name, f"Đã phục hồi {target_profile_name}", f"Đã sao chép {count} tệp tin", f"  ✅ [Khôi phục] {b_name} -> {target_profile_name} ({count} tệp tin)")

        restored_count += 1
        report(b_pct_end, b_name, f"Hoàn tất {b_name}", f"Đã phục hồi {browser_files_count} tệp tin cho {b_name}", f"Hoàn tất phục hồi {b_name} ({browser_files_count} tệp)")

    if restored_count == 0:
        report(100, "", "Phục hồi thất bại", "0 trình duyệt được phục hồi", f"❌ Không có trình duyệt nào được phục hồi!")
        return {
            'success': False,
            'browsers_count': 0,
            'message': f"Không thể phục hồi trình duyệt từ thư mục:\n{norm_folder}"
        }

    report(100, "", "Phục hồi hoàn tất!", f"Đã khôi phục thành công {restored_count} trình duyệt!", f"🎉 Hoàn tất phục hồi thành công cho {restored_count} trình duyệt!")
    return {
        'success': True,
        'browsers_count': restored_count,
        'message': f"Đã phục hồi thành công {restored_count} trình duyệt từ:\n{norm_folder}"
    }


def get_backup_history(search_dir=""):
    """Scans for previous backup packages across all candidate drives and search_dir."""
    candidate_dirs = []
    if search_dir and os.path.exists(search_dir):
        candidate_dirs.append(search_dir)
        
    def_dir = get_default_backup_dir()
    if def_dir not in candidate_dirs:
        candidate_dirs.append(def_dir)

    for letter in ['D', 'E', 'F', 'G']:
        p = f"{letter}:\\Browser_Backups"
        if os.path.exists(p) and p not in candidate_dirs:
            candidate_dirs.append(p)

    user_profile = os.environ.get('USERPROFILE', 'C:\\')
    desktop_backup = os.path.join(user_profile, 'Desktop', 'Browser_Backups')
    if desktop_backup not in candidate_dirs and os.path.exists(desktop_backup):
        candidate_dirs.append(desktop_backup)

    history = []
    seen_paths = set()
    for s_dir in candidate_dirs:
        if not os.path.exists(s_dir):
            continue
        try:
            subfolders = [os.path.join(s_dir, d) for d in os.listdir(s_dir) if os.path.isdir(os.path.join(s_dir, d))]
            for folder in subfolders:
                folder_norm = os.path.normpath(folder).lower()
                if folder_norm in seen_paths:
                    continue
                manifest_p = os.path.join(folder, 'manifest.json')
                if os.path.exists(manifest_p):
                    try:
                        with open(manifest_p, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        data['path'] = folder
                        data['folder_name'] = os.path.basename(folder)
                        data['size'] = fmt_bytes(get_dir_size_fast(folder))
                        history.append(data)
                        seen_paths.add(folder_norm)
                    except Exception:
                        pass
        except Exception:
            pass

    history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return history


# ── TKINTER FALLBACK CLASS ──────────────────────────────────────────────────
class BrowserBackup:
    def __init__(self, parent):
        self.parent = parent
        self.parent.geometry('720x580')
        self.parent.configure(bg=COLORS['bg'])
        self.setup_ui()
        self.refresh_browsers()

    def setup_ui(self):
        hdr = tk.Frame(self.parent, bg=COLORS['bg_header'])
        hdr.pack(fill='x')
        tk.Label(hdr, text='🌍  Browser Backup/Restore 2026', font=FONTS['large'],
                 bg=COLORS['bg_header'], fg='white', pady=10).pack(side='left', padx=15)

        # Status frame
        status_frame = tk.LabelFrame(self.parent, text='  Trình Duyệt Phát Hiện  ',
                                     font=FONTS['subtitle'], bg=COLORS['bg'])
        status_frame.pack(fill='x', padx=15, pady=8)

        self.browser_vars = {}
        self.status_labels = {}
        
        browsers = get_detected_browsers()
        for b in browsers:
            key = b['key']
            row = tk.Frame(status_frame, bg=COLORS['bg'])
            row.pack(fill='x', padx=10, pady=3)

            var = tk.BooleanVar(value=b['is_installed'])
            self.browser_vars[key] = var
            cb = tk.Checkbutton(row, text=f"{b['icon']} {b['name']}", variable=var,
                                font=FONTS['subtitle'], bg=COLORS['bg'],
                                selectcolor=COLORS['selected'], width=20, anchor='w')
            cb.pack(side='left', padx=5)

            status_text = f"✅ Đã tìm thấy ({b['size']})" if b['is_installed'] else "❌ Chưa cài đặt"
            fg_color = '#27AE60' if b['is_installed'] else '#7F8C8D'
            lbl = tk.Label(row, text=status_text, font=FONTS['normal'],
                           bg=COLORS['bg'], fg=fg_color)
            lbl.pack(side='left', padx=5)
            self.status_labels[key] = lbl

        # Options
        opt_frame = tk.LabelFrame(self.parent, text='  Tùy Chọn Sao Lưu  ',
                                   font=FONTS['subtitle'], bg=COLORS['bg'])
        opt_frame.pack(fill='x', padx=15, pady=5)

        self.opt_bookmarks = tk.BooleanVar(value=True)
        self.opt_passwords = tk.BooleanVar(value=True)
        self.opt_history = tk.BooleanVar(value=True)
        self.opt_extensions = tk.BooleanVar(value=False)
        self.opt_full_profile = tk.BooleanVar(value=False)

        opts_row = tk.Frame(opt_frame, bg=COLORS['bg'])
        opts_row.pack(padx=10, pady=5)
        for text, var in [
            ('📚 Bookmarks', self.opt_bookmarks),
            ('🔑 Passwords', self.opt_passwords),
            ('📋 History', self.opt_history),
            ('🧩 Extensions', self.opt_extensions),
            ('📁 Full Profile', self.opt_full_profile),
        ]:
            tk.Checkbutton(opts_row, text=text, variable=var,
                           font=FONTS['normal'], bg=COLORS['bg'],
                           selectcolor=COLORS['selected']).pack(side='left', padx=6)

        # Actions
        btn_frame = tk.Frame(self.parent, bg=COLORS['bg'])
        btn_frame.pack(pady=8)
        
        tk.Button(btn_frame, text='💾 Bắt Đầu Sao Lưu', font=FONTS['subtitle'],
                  bg=COLORS['accent'], fg='white', relief='flat', padx=15, pady=6,
                  cursor='hand2', command=self.do_backup).pack(side='left', padx=6)
        
        tk.Button(btn_frame, text='📥 Bắt Đầu Phục Hồi', font=FONTS['subtitle'],
                  bg=COLORS['info'], fg='white', relief='flat', padx=15, pady=6,
                  cursor='hand2', command=self.do_restore).pack(side='left', padx=6)
        
        tk.Button(btn_frame, text='📂 Mở Thư Mục Backup', font=FONTS['subtitle'],
                  bg=COLORS['warning'], fg='white', relief='flat', padx=15, pady=6,
                  cursor='hand2', command=self.open_backup_dir).pack(side='left', padx=6)

        # Log
        tk.Label(self.parent, text='Nhật Ký Tác Vụ:', font=FONTS['normal'],
                 bg=COLORS['bg']).pack(anchor='w', padx=15)
        self.log_text = tk.Text(self.parent, font=FONTS['mono'], bg='#1E1E1E', fg='#D4D4D4',
                                height=7, relief='flat', padx=8, pady=5)
        self.log_text.pack(fill='both', expand=True, padx=15, pady=5)

    def refresh_browsers(self):
        pass

    def log(self, level, msg):
        self.log_text.configure(state='normal')
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_text.insert('end', f'[{ts}] [{level}] {msg}\n')
        self.log_text.see('end')
        self.log_text.configure(state='disabled')

    def get_selected_browsers(self):
        return [k for k, v in self.browser_vars.items() if v.get()]

    def get_options(self):
        return {
            'bookmarks': self.opt_bookmarks.get(),
            'passwords': self.opt_passwords.get(),
            'history': self.opt_history.get(),
            'extensions': self.opt_extensions.get(),
            'full_profile': self.opt_full_profile.get()
        }

    def do_backup(self):
        selected = self.get_selected_browsers()
        if not selected:
            messagebox.showwarning('Cảnh Báo', 'Chưa chọn trình duyệt nào!')
            return
        dest = filedialog.askdirectory(title='Chọn thư mục lưu Backup')
        if not dest:
            return

        def worker():
            res = backup_browser_data(selected, self.get_options(), dest, logger=self)
            messagebox.showinfo('Hoàn Tất', res['message'])

        threading.Thread(target=worker, daemon=True).start()

    def do_restore(self):
        selected = self.get_selected_browsers()
        if not selected:
            messagebox.showwarning('Cảnh Báo', 'Chưa chọn trình duyệt cần phục hồi!')
            return
        folder = filedialog.askdirectory(title='Chọn Thư Mục Chứa Bản Sao Lưu BrowserBackup')
        if not folder:
            return

        def worker():
            res = restore_browser_data(folder, selected, self.get_options(), logger=self)
            messagebox.showinfo('Hoàn Tất', res['message'])

        threading.Thread(target=worker, daemon=True).start()

    def open_backup_dir(self):
        user_profile = os.environ.get('USERPROFILE', 'C:\\')
        target_dir = os.path.join(user_profile, 'Desktop', 'Browser_Backups')
        os.makedirs(target_dir, exist_ok=True)
        subprocess.run(f'explorer.exe "{target_dir}"', shell=True)
