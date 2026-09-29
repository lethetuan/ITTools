"""
Browser Backup/Restore Module 2026 - Chrome, Edge, Brave, Cốc Cốc, Firefox, Opera
Author: Lê Thế Tuấn | 0352 194 195 | https://lethetuanpc.blogspot.com/
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
            try:
                with winreg.OpenKey(root, f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{proc}") as k:
                    val, _ = winreg.QueryValueEx(k, "")
                    val = val.strip('"')
                    if os.path.exists(val):
                        return val
            except Exception:
                pass

    # 2. Search Registry StartMenuInternet
    for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
        try:
            with winreg.OpenKey(root, r"SOFTWARE\Clients\StartMenuInternet") as key:
                num_subkeys = winreg.QueryInfoKey(key)[0]
                for i in range(num_subkeys):
                    sname = winreg.EnumKey(key, i)
                    if browser_key.lower() in sname.lower() or (browser_key == 'Edge' and 'msedge' in sname.lower()) or (browser_key == 'CocCoc' and 'coccoc' in sname.lower()):
                        try:
                            with winreg.OpenKey(key, rf"{sname}\shell\open\command") as cmd_k:
                                val, _ = winreg.QueryValueEx(cmd_k, "")
                                val = val.strip('"')
                                if os.path.exists(val):
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
            r'C:\Program Files (x86)\Microsoft\Edge*\*\msedge.exe',
            r'C:\Program Files\Microsoft\Edge*\*\msedge.exe',
            os.path.join(programfilesx86, r'Microsoft\Edge\Application\msedge.exe'),
            os.path.join(programfiles, r'Microsoft\Edge\Application\msedge.exe'),
        ],
        'Brave': [
            os.path.join(programfiles, r'BraveSoftware\Brave-Browser\Application\brave.exe'),
            os.path.join(localappdata, r'BraveSoftware\Brave-Browser\Application\brave.exe'),
        ],
        'CocCoc': [
            os.path.join(localappdata, r'CocCoc\Browser\Application\browser.exe'),
            os.path.join(programfiles, r'CocCoc\Browser\Application\browser.exe'),
        ],
        'Firefox': [
            os.path.join(programfiles, r'Mozilla Firefox\firefox.exe'),
            os.path.join(programfilesx86, r'Mozilla Firefox\firefox.exe'),
        ],
        'Opera': [
            os.path.join(localappdata, r'Programs\Opera\opera.exe'),
            os.path.join(programfiles, r'Opera\opera.exe'),
        ],
        'OperaGX': [
            os.path.join(localappdata, r'Programs\Opera GX\opera.exe'),
        ]
    }

    patterns = glob_patterns.get(browser_key, [])
    for pat in patterns:
        matches = glob.glob(pat)
        for m in matches:
            if os.path.exists(m):
                return m

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
        is_installed = os.path.exists(root)
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
            exe_p = find_browser_exe_path(key)
            if exe_p:
                real_icon = extract_exe_icon_base64(exe_p)

            b_type = info['type']
            items['full_profile'] = True
            
            if b_type == 'chromium':
                # Check Default and Profile X
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
                # Check Firefox profiles
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

        results.append({
            'key': key,
            'name': info['name'],
            'icon': info['icon'],
            'real_icon': real_icon,
            'type': info['type'],
            'is_installed': is_installed,
            'profile_root': root,
            'size': size_str,
            'items': items,
            'profiles_count': len(profiles_found)
        })

    return results


def close_browser_processes(process_names):
    """Closes running processes for specified browsers."""
    for proc in process_names:
        try:
            subprocess.run(f'taskkill /f /im "{proc}"', shell=True, capture_output=True)
        except Exception:
            pass


def _copy_file_safe(src, dst):
    """Safely copies file ignoring locks."""
    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        return True
    except Exception:
        try:
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


def backup_browser_data(selected_browsers, options, target_dir="", logger=None):
    """Performs full backup of selected browsers based on options."""
    definitions = get_browser_definitions()
    
    def log(msg, level="INFO"):
        if logger:
            if hasattr(logger, 'log'):
                logger.log(level, msg)
            elif callable(logger):
                logger(msg)

    if not target_dir:
        user_profile = os.environ.get('USERPROFILE', 'C:\\')
        target_dir = os.path.join(user_profile, 'Desktop', 'Browser_Backups')

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder_name = f"BrowserBackup_{timestamp}"
    backup_path = os.path.join(target_dir, backup_folder_name)
    os.makedirs(backup_path, exist_ok=True)

    log(f"Bắt đầu sao lưu trình duyệt vào thư mục: {backup_path}...", "INFO")

    manifest = {
        'timestamp': timestamp,
        'created_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'browsers': {},
        'options': options
    }

    success_count = 0

    for b_key in selected_browsers:
        if b_key not in definitions:
            continue
        info = definitions[b_key]
        root = info['profile_root']
        if not os.path.exists(root):
            log(f"Bỏ qua {info['name']}: Không tìm thấy thư mục profile ({root})", "WARN")
            continue

        log(f"Đang sao lưu {info['name']}...", "INFO")
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
                    log(f"  ➜ Sao lưu Toàn Bộ Hồ Sơ (Full Profile) {pname}...", "INFO")
                    count = _copy_tree_safe(pd, pd_dest)
                    b_manifest['files_backed_up'] += count
                else:
                    if options.get('bookmarks'):
                        bm = os.path.join(pd, 'Bookmarks')
                        if os.path.exists(bm):
                            _copy_file_safe(bm, os.path.join(pd_dest, 'Bookmarks'))
                            b_manifest['files_backed_up'] += 1
                            log(f"  ✅ [Bookmarks] {pname}", "SUCCESS")

                    if options.get('passwords'):
                        for pass_file in ['Login Data', 'Login Data For Account', 'Web Data']:
                            pf = os.path.join(pd, pass_file)
                            if os.path.exists(pf):
                                _copy_file_safe(pf, os.path.join(pd_dest, pass_file))
                                b_manifest['files_backed_up'] += 1
                        log(f"  ✅ [Passwords & Login Data] {pname}", "SUCCESS")

                    if options.get('history'):
                        hf = os.path.join(pd, 'History')
                        if os.path.exists(hf):
                            _copy_file_safe(hf, os.path.join(pd_dest, 'History'))
                            b_manifest['files_backed_up'] += 1
                            log(f"  ✅ [History] {pname}", "SUCCESS")

                    if options.get('extensions'):
                        ext_dir = os.path.join(pd, 'Extensions')
                        if os.path.exists(ext_dir):
                            count = _copy_tree_safe(ext_dir, os.path.join(pd_dest, 'Extensions'))
                            b_manifest['files_backed_up'] += count
                            log(f"  ✅ [Extensions] {pname} ({count} files)", "SUCCESS")

        elif info['type'] == 'firefox':
            p_dirs = [d for d in glob.glob(os.path.join(root, '*')) if os.path.isdir(d)]
            for pd in p_dirs:
                pname = os.path.basename(pd)
                pd_dest = os.path.join(b_backup_dir, pname)
                os.makedirs(pd_dest, exist_ok=True)

                if options.get('full_profile'):
                    log(f"  ➜ Sao lưu Toàn Bộ Hồ Sơ Firefox {pname}...", "INFO")
                    count = _copy_tree_safe(pd, pd_dest)
                    b_manifest['files_backed_up'] += count
                else:
                    if options.get('bookmarks') or options.get('history'):
                        for f in ['places.sqlite', 'favicons.sqlite']:
                            fp = os.path.join(pd, f)
                            if os.path.exists(fp):
                                _copy_file_safe(fp, os.path.join(pd_dest, f))
                                b_manifest['files_backed_up'] += 1
                        log(f"  ✅ [Bookmarks & History] Firefox {pname}", "SUCCESS")

                    if options.get('passwords'):
                        for f in ['key4.db', 'logins.json']:
                            fp = os.path.join(pd, f)
                            if os.path.exists(fp):
                                _copy_file_safe(fp, os.path.join(pd_dest, f))
                                b_manifest['files_backed_up'] += 1
                        log(f"  ✅ [Passwords] Firefox {pname}", "SUCCESS")

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

    # Save manifest.json
    manifest_path = os.path.join(backup_path, 'manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    log(f"Hoàn tất sao lưu {success_count} trình duyệt! Lưu tại: {backup_path}", "SUCCESS")

    return {
        'success': True,
        'backup_dir': backup_path,
        'folder_name': backup_folder_name,
        'timestamp': timestamp,
        'browsers_count': success_count,
        'message': f"Đã sao lưu thành công {success_count} trình duyệt vào:\n{backup_path}"
    }


def restore_browser_data(backup_folder, selected_browsers, options, logger=None):
    """Restores browser data from backup folder."""
    definitions = get_browser_definitions()
    
    def log(msg, level="INFO"):
        if logger:
            if hasattr(logger, 'log'):
                logger.log(level, msg)
            elif callable(logger):
                logger(msg)

    if not backup_folder or not os.path.exists(backup_folder):
        return {'success': False, 'message': 'Thư mục Sao Lưu không tồn tại!'}

    manifest_path = os.path.join(backup_folder, 'manifest.json')
    manifest = {}
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        except Exception:
            pass

    log(f"Đang tiến hành phục hồi dữ liệu từ: {backup_folder}...", "INFO")
    restored_count = 0

    for b_key in selected_browsers:
        if b_key not in definitions:
            continue
        info = definitions[b_key]
        b_backup_src = os.path.join(backup_folder, b_key)
        if not os.path.exists(b_backup_src):
            log(f"Bỏ qua {info['name']}: Không tìm thấy bản sao lưu trong thư mục.", "WARN")
            continue

        target_root = info['profile_root']
        os.makedirs(target_root, exist_ok=True)

        # Close running processes
        close_browser_processes(info['process'])
        log(f"Đang phục hồi cho {info['name']}...", "INFO")

        # Copy backed up files back into profile directories
        sub_dirs = [d for d in glob.glob(os.path.join(b_backup_src, '*')) if os.path.isdir(d)]
        if not sub_dirs:
            sub_dirs = [b_backup_src]

        for s_dir in sub_dirs:
            pname = os.path.basename(s_dir)
            target_profile = os.path.join(target_root, pname) if info['type'] in ['chromium', 'firefox'] else target_root
            os.makedirs(target_profile, exist_ok=True)

            count = _copy_tree_safe(s_dir, target_profile)
            log(f"  ✅ [Khôi phục] {info['name']} -> {pname} ({count} files)", "SUCCESS")

        restored_count += 1

    log(f"Hoàn tất phục hồi cho {restored_count} trình duyệt!", "SUCCESS")
    return {
        'success': True,
        'browsers_count': restored_count,
        'message': f"Đã phục hồi thành công {restored_count} trình duyệt từ:\n{backup_folder}"
    }


def get_backup_history(search_dir=""):
    """Scans for previous backup packages."""
    if not search_dir:
        user_profile = os.environ.get('USERPROFILE', 'C:\\')
        search_dir = os.path.join(user_profile, 'Desktop', 'Browser_Backups')

    history = []
    if not os.path.exists(search_dir):
        return history

    try:
        subfolders = [os.path.join(search_dir, d) for d in os.listdir(search_dir) if os.path.isdir(os.path.join(search_dir, d))]
        for folder in subfolders:
            manifest_p = os.path.join(folder, 'manifest.json')
            if os.path.exists(manifest_p):
                try:
                    with open(manifest_p, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    data['path'] = folder
                    data['folder_name'] = os.path.basename(folder)
                    data['size'] = fmt_bytes(get_dir_size_fast(folder))
                    history.append(data)
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
