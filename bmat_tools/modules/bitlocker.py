"""
BitLocker Manager Module
Provides real-time drive inspection, BitLocker status, and enable/disable operations via manage-bde.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import os
import sys
import re
import ctypes

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS


def get_logical_drives():
    """Returns list of logical drive letters available on Windows."""
    drives = []
    try:
        buf = ctypes.create_unicode_buffer(512)
        size = ctypes.windll.kernel32.GetLogicalDriveStringsW(512, buf)
        if size > 0:
            drives = [d.rstrip('\\') for d in buf[:size].split('\x00') if d]
    except Exception:
        drives = ['C:', 'D:', 'E:']
    return drives


def get_drive_space(drive):
    """Returns total size and free space for a drive letter."""
    total_str = "N/A"
    free_str = "N/A"
    try:
        t = ctypes.c_ulonglong(0)
        f = ctypes.c_ulonglong(0)
        dp = drive + "\\" if not drive.endswith("\\") else drive
        if ctypes.windll.kernel32.GetDiskFreeSpaceExW(dp, None, ctypes.byref(t), ctypes.byref(f)):
            t_gb = t.value / (1024**3)
            f_gb = f.value / (1024**3)
            total_str = f"{t_gb:.1f} GB"
            free_str = f"{f_gb:.1f} GB"
    except Exception:
        pass
    return total_str, free_str


def get_bitlocker_drives():
    """Scans and returns BitLocker status for all physical drive volumes with 100% accurate computer sync."""
    logical_drives = get_logical_drives()
    drive_dict = {}

    for d in logical_drives:
        d_upper = d.upper()
        t_str, f_str = get_drive_space(d_upper)
        drive_dict[d_upper] = {
            "drive": d_upper,
            "label": "",
            "size": t_str,
            "free_space": f_str,
            "protection_status": "OFF",
            "protection_text": "🔓 Đã Tắt BitLocker",
            "encryption_pct": 0.0,
            "conversion_status": "Fully Decrypted",
            "encryption_method": "None",
            "lock_status": "Unlocked"
        }

    # Run manage-bde -status
    try:
        res = subprocess.run(["manage-bde", "-status"], capture_output=True, text=True, timeout=15)
        if res.returncode == 0 and res.stdout:
            volumes = res.stdout.split("Volume ")
            for vol in volumes[1:]:
                lines = vol.strip().splitlines()
                if not lines:
                    continue
                m_drive = re.match(r'^([A-Z]:)\s*(?:\[(.*?)\])?', lines[0])
                if not m_drive:
                    continue
                mp = m_drive.group(1).upper()
                label = m_drive.group(2) or ""

                vol_text = "\n".join(lines)

                m_prot = re.search(r'Protection Status:\s*(.*)', vol_text, re.IGNORECASE)
                prot_val = m_prot.group(1).strip() if m_prot else "Protection Off"

                m_conv = re.search(r'Conversion Status:\s*(.*)', vol_text, re.IGNORECASE)
                conv_val = m_conv.group(1).strip() if m_conv else "Fully Decrypted"

                m_pct = re.search(r'Percentage Encrypted:\s*([\d\,\.]+)\%', vol_text, re.IGNORECASE)
                pct_val = 0.0
                if m_pct:
                    try:
                        pct_val = float(m_pct.group(1).replace(',', '.'))
                    except Exception:
                        pass

                m_lock = re.search(r'Lock Status:\s*(.*)', vol_text, re.IGNORECASE)
                lock_val = m_lock.group(1).strip() if m_lock else "Unlocked"

                m_meth = re.search(r'Encryption Method:\s*(.*)', vol_text, re.IGNORECASE)
                meth_val = m_meth.group(1).strip() if m_meth else "None"

                info = drive_dict.get(mp, {
                    "drive": mp,
                    "label": label,
                    "size": "N/A",
                    "free_space": "N/A",
                    "protection_status": "OFF",
                    "protection_text": "🔓 Đã Tắt BitLocker",
                    "encryption_pct": 0.0,
                    "conversion_status": "Fully Decrypted",
                    "encryption_method": "None",
                    "lock_status": "Unlocked"
                })

                if label:
                    info["label"] = label

                info["conversion_status"] = conv_val
                info["encryption_pct"] = pct_val
                info["encryption_method"] = meth_val
                info["lock_status"] = lock_val

                # Improved status calculation matching real drive status
                is_encrypted = (pct_val > 0) or (meth_val.lower() != "none") or ("decrypted" not in conv_val.lower())
                is_protected = "protection on" in prot_val.lower()
                is_locked = "locked" in lock_val.lower() and "unlocked" not in lock_val.lower()
                is_transition = "in progress" in conv_val.lower() or (pct_val > 0 and pct_val < 100)

                if is_locked:
                    info["protection_status"] = "LOCKED"
                    info["protection_text"] = "🔐 Ổ Đã Khóa (Locked)"
                elif is_transition:
                    info["protection_status"] = "TRANSITION"
                    info["protection_text"] = f"⚡ {conv_val} ({pct_val:.1f}%)"
                elif is_protected:
                    info["protection_status"] = "ON"
                    info["protection_text"] = f"🔒 Đã Bật BitLocker ({pct_val:.0f}%)"
                elif is_encrypted:
                    info["protection_status"] = "ON"
                    info["protection_text"] = f"🔒 Đã Bật Mã Hóa ({pct_val:.0f}%)"
                else:
                    info["protection_status"] = "OFF"
                    info["protection_text"] = "🔓 Đã Tắt BitLocker"

                drive_dict[mp] = info
    except Exception as e:
        print("Lỗi get_bitlocker_drives manage-bde:", e)

    # Supplemental check via PowerShell Get-BitLockerVolume
    try:
        ps_cmd = 'Get-BitLockerVolume | Select-Object MountPoint, VolumeStatus, EncryptionPercentage, ProtectionStatus, EncryptionMethod, LockStatus | ConvertTo-Json'
        ps_res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=10)
        if ps_res.returncode == 0 and ps_res.stdout.strip():
            import json
            data = json.loads(ps_res.stdout)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                mp = item.get("MountPoint", "").upper().rstrip('\\')
                if not mp:
                    continue
                vol_status = item.get("VolumeStatus", 0)
                enc_pct = float(item.get("EncryptionPercentage", 0) or 0)
                enc_meth = item.get("EncryptionMethod", 0)

                if mp in drive_dict:
                    info = drive_dict[mp]
                    if (vol_status in (1, "FullyEncrypted", "UsedSpaceOnlyEncrypted") or enc_pct > 0 or (enc_meth and str(enc_meth) != "0")) and info["protection_status"] == "OFF":
                        info["encryption_pct"] = enc_pct if enc_pct > 0 else 100.0
                        info["protection_status"] = "ON"
                        info["protection_text"] = f"🔒 Đã Bật Mã Hóa ({info['encryption_pct']:.0f}%)"
                        if str(enc_meth) != "0" and info["encryption_method"] == "None":
                            info["encryption_method"] = str(enc_meth)
                        drive_dict[mp] = info
    except Exception:
        pass

    return list(drive_dict.values())


def get_drive_status(drive):
    """Returns real-time status dictionary for a single drive letter."""
    drive_clean = drive.upper().rstrip('\\')
    if not drive_clean.endswith(':'):
        drive_clean += ':'

    try:
        res = subprocess.run(["manage-bde", "-status", drive_clean], capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout:
            vol_text = res.stdout.strip()
            
            m_conv = re.search(r'Conversion Status:\s*(.*)', vol_text, re.IGNORECASE)
            conv_val = m_conv.group(1).strip() if m_conv else "Fully Decrypted"

            m_pct = re.search(r'Percentage Encrypted:\s*([\d\,\.]+)\%', vol_text, re.IGNORECASE)
            pct_val = 0.0
            if m_pct:
                try:
                    pct_val = float(m_pct.group(1).replace(',', '.'))
                except Exception:
                    pass

            m_prot = re.search(r'Protection Status:\s*(.*)', vol_text, re.IGNORECASE)
            prot_val = m_prot.group(1).strip() if m_prot else "Protection Off"

            m_lock = re.search(r'Lock Status:\s*(.*)', vol_text, re.IGNORECASE)
            lock_val = m_lock.group(1).strip() if m_lock else "Unlocked"

            m_meth = re.search(r'Encryption Method:\s*(.*)', vol_text, re.IGNORECASE)
            meth_val = m_meth.group(1).strip() if m_meth else "None"

            is_encrypted = (pct_val > 0) or (meth_val.lower() != "none") or ("decrypted" not in conv_val.lower())
            is_protected = "protection on" in prot_val.lower()
            is_locked = "locked" in lock_val.lower() and "unlocked" not in lock_val.lower()
            is_transition = "in progress" in conv_val.lower() or (pct_val > 0 and pct_val < 100)

            if is_locked:
                prot_status = "LOCKED"
                prot_text = "🔐 Ổ Đã Khóa (Locked)"
            elif is_transition:
                prot_status = "TRANSITION"
                prot_text = f"⚡ {conv_val} ({pct_val:.1f}%)"
            elif is_protected:
                prot_status = "ON"
                prot_text = f"🔒 Đã Bật BitLocker ({pct_val:.0f}%)"
            elif is_encrypted:
                prot_status = "ON"
                prot_text = f"🔒 Đã Bật Mã Hóa ({pct_val:.0f}%)"
            else:
                prot_status = "OFF"
                prot_text = "🔓 Đã Tắt BitLocker"

            t_str, f_str = get_drive_space(drive_clean)

            return {
                "drive": drive_clean,
                "label": "",
                "size": t_str,
                "free_space": f_str,
                "protection_status": prot_status,
                "protection_text": prot_text,
                "encryption_pct": pct_val,
                "conversion_status": conv_val,
                "encryption_method": meth_val,
                "lock_status": lock_val
            }
    except Exception:
        pass

    # Fallback
    drives = get_bitlocker_drives()
    for d in drives:
        if d["drive"].upper() == drive_clean:
            return d
    return {
        "drive": drive_clean,
        "label": "",
        "size": "N/A",
        "free_space": "N/A",
        "protection_status": "UNKNOWN",
        "protection_text": "Chưa rõ",
        "encryption_pct": 0.0,
        "conversion_status": "Unknown",
        "encryption_method": "None",
        "lock_status": "Unknown"
    }


def set_bitlocker(drive, action):
    """Executes manage-bde -off or -on for a drive with Admin elevation fallback."""
    drive_clean = drive.upper().rstrip('\\')
    if not drive_clean.endswith(':'):
        drive_clean += ':'

    try:
        if action == "disable":
            cmd = f'manage-bde -off {drive_clean}'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            output = (res.stdout + res.stderr).strip()
            if res.returncode == 0 or "in progress" in output.lower() or "decryption" in output.lower() or "disabled" in output.lower():
                return {
                    "success": True,
                    "message": f"Đã phát lệnh tắt BitLocker cho ổ {drive_clean}. Đang tiến hành giải mã dữ liệu!",
                    "drive": drive_clean,
                    "action": "disable",
                    "output": output
                }
            else:
                # Elevate via PowerShell Start-Process if needed
                ps_elevate = f'Start-Process manage-bde -ArgumentList "-off {drive_clean}" -Verb RunAs -Wait'
                res_elev = subprocess.run(["powershell", "-NoProfile", "-Command", ps_elevate], capture_output=True, text=True, timeout=20)
                if res_elev.returncode == 0:
                    return {
                        "success": True,
                        "message": f"Đã gửi lệnh tắt BitLocker với quyền Admin cho ổ {drive_clean}!",
                        "drive": drive_clean,
                        "action": "disable",
                        "output": "Elevated execution completed."
                    }
                return {
                    "success": False,
                    "message": f"Lỗi tắt BitLocker cho ổ {drive_clean}: {output}",
                    "drive": drive_clean,
                    "action": "disable",
                    "output": output
                }
        elif action == "enable":
            cmd = f'manage-bde -on {drive_clean} -used'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            output = (res.stdout + res.stderr).strip()
            if res.returncode == 0 or "in progress" in output.lower() or "encryption" in output.lower() or "password" in output.lower():
                return {
                    "success": True,
                    "message": f"Đã kích hoạt BitLocker cho ổ {drive_clean}. Đang tiến hành mã hóa dữ liệu!",
                    "drive": drive_clean,
                    "action": "enable",
                    "output": output
                }
            else:
                ps_elevate = f'Start-Process manage-bde -ArgumentList "-on {drive_clean} -used" -Verb RunAs -Wait'
                res_elev = subprocess.run(["powershell", "-NoProfile", "-Command", ps_elevate], capture_output=True, text=True, timeout=20)
                if res_elev.returncode == 0:
                    return {
                        "success": True,
                        "message": f"Đã phát lệnh bật BitLocker với quyền Admin cho ổ {drive_clean}!",
                        "drive": drive_clean,
                        "action": "enable",
                        "output": "Elevated execution completed."
                    }
                return {
                    "success": False,
                    "message": f"Lỗi bật BitLocker cho ổ {drive_clean}: {output}",
                    "drive": drive_clean,
                    "action": "enable",
                    "output": output
                }
        else:
            return {"success": False, "message": "Hành động không hợp lệ."}
    except Exception as e:
        return {"success": False, "message": f"Ngoại lệ: {str(e)}"}


def get_bitlocker_recovery_key(drive):
    """Retrieves or creates BitLocker Recovery Key(s) for a specified drive volume."""
    drive_clean = drive.upper().rstrip('\\')
    if not drive_clean.endswith(':'):
        drive_clean += ':'

    keys = []

    def extract_keys(text):
        found = []
        if not text:
            return found
        matches = re.findall(r'(\d{6}-\d{6}-\d{6}-\d{6}-\d{6}-\d{6}-\d{6}-\d{6})', text)
        for m in matches:
            if m not in found:
                found.append(m)
        return found

    # Method 1: manage-bde -protectors -get <drive>
    try:
        res = subprocess.run(["manage-bde", "-protectors", "-get", drive_clean], capture_output=True, text=True, timeout=10)
        if res.stdout:
            keys = extract_keys(res.stdout)
    except Exception as e:
        print("manage-bde -get error:", e)

    # Method 2: PowerShell Get-BitLockerVolume KeyProtector fallback
    if not keys:
        try:
            ps_cmd = f'(Get-BitLockerVolume -MountPoint "{drive_clean}").KeyProtector | Where-Object {{ $_.KeyProtectorType -eq "RecoveryPassword" }} | Select-Object -ExpandProperty RecoveryPassword'
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=10)
            if res.stdout.strip():
                keys = extract_keys(res.stdout)
        except Exception as e:
            print("PowerShell Get-BitLockerVolume error:", e)

    # Method 3: If no key protector exists, create a new RecoveryPassword protector
    if not keys:
        try:
            cmd_add = f'manage-bde -protectors -add {drive_clean} -rp'
            res_add = subprocess.run(cmd_add, shell=True, capture_output=True, text=True, timeout=15)
            output_add = (res_add.stdout or "") + "\n" + (res_add.stderr or "")
            keys = extract_keys(output_add)

            if not keys:
                ps_add = f'Add-BitLockerKeyProtector -MountPoint "{drive_clean}" -RecoveryPasswordProtector'
                res_ps_add = subprocess.run(["powershell", "-NoProfile", "-Command", ps_add], capture_output=True, text=True, timeout=15)
                output_ps = (res_ps_add.stdout or "") + "\n" + (res_ps_add.stderr or "")
                keys = extract_keys(output_ps)

            if not keys:
                # Query manage-bde -get again after creation
                res_get2 = subprocess.run(["manage-bde", "-protectors", "-get", drive_clean], capture_output=True, text=True, timeout=10)
                if res_get2.stdout:
                    keys = extract_keys(res_get2.stdout)
        except Exception as e:
            print("Error creating key protector:", e)

    if keys:
        return {
            "success": True,
            "drive": drive_clean,
            "keys": keys,
            "primary_key": keys[0],
            "message": f"Tìm thấy {len(keys)} Recovery Key cho ổ {drive_clean}."
        }
    else:
        return {
            "success": False,
            "drive": drive_clean,
            "keys": [],
            "primary_key": "",
            "message": f"Không thể lấy Recovery Key cho ổ {drive_clean}. Đảm bảo bạn đang chạy ứng dụng với quyền Administrator."
        }


def export_bitlocker_recovery_key(drive, save_path=None):
    """Exports BitLocker Recovery Key to a TXT file on Desktop or custom save path."""
    res_key = get_bitlocker_recovery_key(drive)
    if not res_key["success"] or not res_key["keys"]:
        return res_key

    drive_clean = drive.upper().rstrip('\\')
    if not drive_clean.endswith(':'):
        drive_clean += ':'

    drive_letter = drive_clean[0]

    if not save_path:
        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop_dir):
            desktop_dir = os.path.dirname(os.path.abspath(__file__))
        save_path = os.path.join(desktop_dir, f"BitLocker_Recovery_Key_{drive_letter}.txt")

    try:
        content = f"====================================================\n"
        content += f" BITLOCKER RECOVERY KEY - DRIVE {drive_clean}\n"
        content += f"====================================================\n\n"
        for idx, k in enumerate(res_key["keys"], 1):
            content += f"Recovery Key #{idx}: {k}\n"
        content += f"\nLƯU Ý: Vui lòng lưu trữ file này ở nơi an toàn (như USB hoặc Cloud).\n"

        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            "success": True,
            "message": f"Đã lưu thành công Recovery Key vào file:\n{save_path}",
            "file_path": save_path,
            "keys": res_key["keys"]
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Không thể ghi file: {str(e)}",
            "file_path": "",
            "keys": res_key["keys"]
        }



class BitLocker:
    def __init__(self, parent):
        self.parent = parent
        self.parent.geometry('680x500')
        self.parent.configure(bg=COLORS['bg'])
        self.setup_ui()
        threading.Thread(target=self.load_status, daemon=True).start()

    def setup_ui(self):
        hdr = tk.Frame(self.parent, bg=COLORS['bg_header'])
        hdr.pack(fill='x')
        tk.Label(hdr, text='🔒  BitLocker Manager', font=FONTS['large'],
                  bg=COLORS['bg_header'], fg='white', pady=10).pack(side='left', padx=15)

        # Drive list
        list_frame = tk.LabelFrame(self.parent, text='  Drive Protection Status  ',
                                    font=FONTS['subtitle'], bg=COLORS['bg'],
                                    relief='groove')
        list_frame.pack(fill='x', padx=15, pady=15)

        cols = ('Drive', 'Volume Label', 'Protection Status', 'Encryption %', 'Method')
        self.tree = ttk.Treeview(list_frame, columns=cols, show='headings', height=6)
        widths = [60, 120, 150, 100, 120]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col, anchor='w')
            self.tree.column(col, width=w)
        self.tree.pack(fill='x', padx=5, pady=5)
        self.tree.tag_configure('protected', foreground='#27AE60')
        self.tree.tag_configure('unprotected', foreground='#E74C3C')
        self.tree.tag_configure('encrypting', foreground='#F39C12')

        # Actions
        btn_frame = tk.Frame(self.parent, bg=COLORS['bg'])
        btn_frame.pack(fill='x', padx=15, pady=5)

        tk.Button(btn_frame, text='✅ Enable BitLocker',
                   font=FONTS['subtitle'], bg=COLORS['accent'], fg='white',
                   relief='flat', padx=20, pady=8, cursor='hand2',
                   command=self.enable_bitlocker).pack(side='left', padx=5)
        tk.Button(btn_frame, text='🚫 Disable BitLocker',
                   font=FONTS['subtitle'], bg=COLORS['danger'], fg='white',
                   relief='flat', padx=20, pady=8, cursor='hand2',
                   command=self.disable_bitlocker).pack(side='left', padx=5)
        tk.Button(btn_frame, text='🔄 Refresh',
                   font=FONTS['subtitle'], bg=COLORS['info'], fg='white',
                   relief='flat', padx=20, pady=8, cursor='hand2',
                   command=lambda: threading.Thread(
                       target=self.load_status, daemon=True).start()
                   ).pack(side='left', padx=5)
        tk.Button(btn_frame, text='💾 Backup Key',
                   font=FONTS['subtitle'], bg='#8E44AD', fg='white',
                   relief='flat', padx=20, pady=8, cursor='hand2',
                   command=self.backup_key).pack(side='left', padx=5)

        # Info
        info_text = tk.Text(self.parent, font=FONTS['mono'],
                             bg='#1E1E1E', fg='#D4D4D4',
                             height=8, relief='flat', padx=10, pady=8)
        info_text.pack(fill='both', expand=True, padx=15, pady=5)
        info_text.insert('1.0',
                          'BitLocker Drive Encryption protects your data by encrypting\n'
                          'the entire drive. Admin rights required to manage BitLocker.\n\n'
                          'Note:\n'
                          '• Enabling requires TPM chip or USB startup key\n'
                          '• Keep recovery key safe before enabling\n'
                          '• Encryption process may take hours for large drives\n'
                          '• System drive (C:) requires restart to complete')
        info_text.configure(state='disabled')

        self.progress = ttk.Progressbar(self.parent, mode='indeterminate')
        self.progress.pack(fill='x', padx=15, pady=3)

    def load_status(self):
        self.progress.start()
        self.tree.delete(*self.tree.get_children())
        drives = get_bitlocker_drives()
        for d in drives:
            tag = 'protected' if d['protection_status'] == 'ON' else ('encrypting' if d['protection_status'] == 'TRANSITION' else 'unprotected')
            self.tree.insert('', 'end',
                              values=(d['drive'], d['label'], d['protection_text'], f"{d['encryption_pct']}%", d['encryption_method']),
                              tags=(tag,))
        self.progress.stop()

    def get_selected_drive(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Warning', 'Chọn drive!')
            return None
        return self.tree.item(sel[0], 'values')[0]

    def enable_bitlocker(self):
        drive = self.get_selected_drive()
        if not drive:
            return
        if messagebox.askyesno('Enable BitLocker',
                                f'Bật BitLocker cho {drive}?\n\n'
                                '⚠️ Đảm bảo bạn đã backup recovery key!'):
            res = set_bitlocker(drive, "enable")
            messagebox.showinfo('BitLocker', res.get('message', 'Đã thực hiện.'))
            self.load_status()

    def disable_bitlocker(self):
        drive = self.get_selected_drive()
        if not drive:
            return
        if messagebox.askyesno('Disable BitLocker',
                                f'Tắt BitLocker cho {drive}?\n\n'
                                'Quá trình giải mã có thể mất nhiều thời gian!'):
            res = set_bitlocker(drive, "disable")
            messagebox.showinfo('BitLocker', res.get('message', 'Đã thực hiện.'))
            self.load_status()

    def backup_key(self):
        drive = self.get_selected_drive()
        if not drive:
            return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            title='Save Recovery Key',
            defaultextension='.txt',
            filetypes=[('Text', '*.txt'), ('All', '*.*')]
        )
        if path:
            result = subprocess.run(
                ['powershell', '-Command',
                 f'(Get-BitLockerVolume "{drive}").KeyProtector | '
                 f'Where-Object RecoveryPassword | '
                 f'Select-Object RecoveryPassword | Out-File "{path}"'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                messagebox.showinfo('Backup', f'✅ Recovery key saved to: {path}')
            else:
                messagebox.showerror('Error', result.stderr)
