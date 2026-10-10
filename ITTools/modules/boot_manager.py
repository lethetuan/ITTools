"""
Boot Manager Module - BCDEDIT Manager & WinPE Boot Configurator
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import os
import sys
import re
import shutil
import ctypes
import string

import uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS


class BootManager:
    def __init__(self, parent):
        self.parent = parent
        self.parent.title("Boot Manager")
        self.parent.geometry('750x620')
        self.parent.configure(bg=COLORS['bg'])
        self.entries_data = []
        self.setup_ui()
        self.load_entries()

    def setup_ui(self):
        # Header
        hdr = tk.Frame(self.parent, bg=COLORS['bg_header'])
        hdr.pack(fill='x')
        tk.Label(hdr, text='⚙️  Boot Manager', font=FONTS['large'],
                 bg=COLORS['bg_header'], fg='white', pady=8).pack(side='left', padx=15)

        # Top Toolbar (Set Default, Timeout, Refresh)
        toolbar = tk.Frame(self.parent, bg=COLORS['bg_dark'])
        toolbar.pack(fill='x')

        tk.Button(toolbar, text='🔄 Refresh', font=FONTS['small'],
                  bg=COLORS['info'], fg='white', relief='flat', padx=8, pady=3,
                  cursor='hand2', command=self.load_entries).pack(side='left', padx=4, pady=3)

        tk.Button(toolbar, text='⭐ Set Default', font=FONTS['small'],
                  bg=COLORS['accent'], fg='white', relief='flat', padx=8, pady=3,
                  cursor='hand2', command=self.set_default).pack(side='left', padx=4, pady=3)

        tk.Label(toolbar, text='Timeout (s):', font=FONTS['small'],
                 bg=COLORS['bg_dark'], fg='white').pack(side='left', padx=(15, 2))
        self.timeout_var = tk.StringVar(value='30')
        tk.Spinbox(toolbar, from_=0, to=999, textvariable=self.timeout_var,
                   font=FONTS['small'], width=5).pack(side='left', padx=2)
        tk.Button(toolbar, text='Set Timeout', font=FONTS['small'],
                  bg=COLORS['warning'], fg='white', relief='flat', padx=6, pady=2,
                  cursor='hand2', command=self.apply_timeout).pack(side='left', padx=4)

        # Boot Entries Table
        table_frame = tk.Frame(self.parent, bg=COLORS['bg'])
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)

        cols = ('Boot Name', 'GUID', 'Default')
        self.tree = ttk.Treeview(table_frame, columns=cols, show='headings', selectmode='browse', height=7)
        self.tree.heading('Boot Name', text='Boot Name', anchor='w')
        self.tree.heading('GUID', text='GUID', anchor='w')
        self.tree.heading('Default', text='Default', anchor='center')

        self.tree.column('Boot Name', width=260, minwidth=150)
        self.tree.column('GUID', width=360, minwidth=200)
        self.tree.column('Default', width=80, anchor='center')

        vsb = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True)

        self.tree.bind('<<TreeviewSelect>>', self.on_select_entry)

        # Form Controls (WinPE Path, Boot Name, Buttons)
        form_frame = tk.Frame(self.parent, bg=COLORS['bg'])
        form_frame.pack(fill='x', padx=10, pady=5)

        # Inputs Row 1: Source file & Target drive
        row1 = tk.Frame(form_frame, bg=COLORS['bg'])
        row1.pack(fill='x', pady=4)

        tk.Label(row1, text='WinPE Source (.iso/.wim):', font=FONTS['normal'], bg=COLORS['bg']).grid(row=0, column=0, sticky='w', padx=5)
        self.path_var = tk.StringVar()
        tk.Entry(row1, textvariable=self.path_var, font=FONTS['normal'], width=28).grid(row=0, column=1, padx=5)
        tk.Button(row1, text='📁', font=FONTS['small'], bg='#E2E8F0', relief='flat', command=self.browse_source).grid(row=0, column=2, padx=2)

        tk.Label(row1, text='Ổ Đích:', font=FONTS['normal'], bg=COLORS['bg']).grid(row=0, column=3, sticky='w', padx=(10, 5))
        self.drive_var = tk.StringVar(value='C:')
        self.drive_combo = ttk.Combobox(row1, textvariable=self.drive_var, width=16, state='readonly')
        self.drive_combo.grid(row=0, column=4, padx=5)
        self.populate_partitions_combo()

        # Inputs Row 2: Boot Name
        row2 = tk.Frame(form_frame, bg=COLORS['bg'])
        row2.pack(fill='x', pady=4)

        tk.Label(row2, text='Boot Name (Tên Menu):', font=FONTS['normal'], bg=COLORS['bg']).grid(row=0, column=0, sticky='w', padx=5)
        self.name_var = tk.StringVar()
        tk.Entry(row2, textvariable=self.name_var, font=FONTS['normal'], width=38).grid(row=0, column=1, columnspan=2, padx=5, sticky='w')

        # Buttons Row
        btn_row = tk.Frame(form_frame, bg=COLORS['bg'])
        btn_row.pack(pady=6)

        tk.Button(btn_row, text='➕ Tích Hợp WinPE vào ổ cứng', font=FONTS['subtitle'], bg='#2ECC71', fg='white',
                  relief='flat', padx=14, pady=4, cursor='hand2', command=self.integrate_pe_gui).pack(side='left', padx=6)

        tk.Button(btn_row, text='➖ Xóa Mục Boot', font=FONTS['subtitle'], bg='#E74C3C', fg='white',
                  relief='flat', padx=14, pady=4, cursor='hand2', command=self.delete_selected).pack(side='left', padx=6)

        tk.Button(btn_row, text='💾 Đổi Tên Mục Boot', font=FONTS['subtitle'], bg='#3498DB', fg='white',
                  relief='flat', padx=14, pady=4, cursor='hand2', command=self.save_boot).pack(side='left', padx=6)

        # Details Output Box
        raw_frame = tk.LabelFrame(self.parent, text='  Selected Boot Details  ', font=FONTS['subtitle'], bg=COLORS['bg'])
        raw_frame.pack(fill='x', padx=10, pady=5)

        self.detail_text = tk.Text(raw_frame, font=FONTS['mono'], bg='#FFF8DC', fg='#333333',
                                   height=6, relief='flat', padx=8, pady=5)
        self.detail_text.pack(fill='x', padx=5, pady=5)

    def populate_partitions_combo(self):
        try:
            parts = get_available_partitions()
            vals = [p['drive'] for p in parts]
            if not vals:
                vals = ['C:']
            self.drive_combo['values'] = vals
            # Default to D: if available and has free space, else C:
            d_part = next((p['drive'] for p in parts if p['drive'].upper() == 'D:'), None)
            if d_part:
                self.drive_var.set(d_part)
            elif vals:
                self.drive_var.set(vals[0])
        except Exception:
            self.drive_combo['values'] = ['C:']
            self.drive_var.set('C:')

    def load_entries(self):
        self.tree.delete(*self.tree.get_children())
        entries, default_guid, timeout = get_boot_entries()
        self.entries_data = entries
        self.timeout_var.set(timeout or '30')

        guid_counts = {}
        for item in entries:
            g = item.get('guid', '').lower()
            guid_counts[g] = guid_counts.get(g, 0) + 1

        for idx, item in enumerate(entries):
            is_def = '⭐ Default' if item['is_default'] else ''
            dup_tag = ' [⚠️ TRÙNG GUID]' if guid_counts.get(item.get('guid', '').lower(), 0) > 1 else ''
            item_id = f"item_{idx}_{item['guid']}"
            self.tree.insert('', 'end', iid=item_id, values=(item['name'] + dup_tag, item['guid'], is_def))

        if entries:
            first_id = f"item_0_{entries[0]['guid']}"
            self.tree.selection_set(first_id)

    def _get_selected_guid(self):
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0], 'values')
        if vals and len(vals) >= 2:
            return vals[1]
        return None

    def on_select_entry(self, event=None):
        guid = self._get_selected_guid()
        if not guid:
            return
        selected_item = next((x for x in self.entries_data if x['guid'] == guid), None)
        if selected_item:
            self.name_var.set(selected_item['name'])
            self.detail_text.configure(state='normal')
            self.detail_text.delete('1.0', 'end')
            self.detail_text.insert('1.0', selected_item['raw'])
            self.detail_text.configure(state='disabled')

    def browse_source(self):
        path = filedialog.askopenfilename(
            title='Chọn file WinPE (.iso hoặc .wim)',
            filetypes=[
                ('WinPE Images (*.iso; *.wim)', '*.iso;*.wim'),
                ('ISO Disk Images (*.iso)', '*.iso'),
                ('WIM Images (*.wim)', '*.wim'),
                ('All Files', '*.*')
            ]
        )
        if path:
            self.path_var.set(path)
            info = inspect_winpe_source(path)
            if info.get('success'):
                self.name_var.set(info.get('default_name', 'WinPE Rescue'))
            elif not self.name_var.get():
                base_name = os.path.splitext(os.path.basename(path))[0]
                self.name_var.set(f"WinPE - {base_name}")

    def browse_wim(self):
        self.browse_source()

    def integrate_pe_gui(self):
        src_path = self.path_var.get().strip()
        target_drive = self.drive_var.get().strip() or 'C:'
        boot_name = self.name_var.get().strip()

        if not src_path:
            messagebox.showwarning('Warning', 'Vui lòng chọn file WinPE (.iso hoặc .wim) cần tích hợp!')
            return

        if messagebox.askyesno('Xác nhận tích hợp',
                               f'Bạn có chắc chắn muốn tích hợp WinPE vào phân vùng [{target_drive}]?\n\n'
                               f'- File nguồn: {src_path}\n'
                               f'- Thư mục lưu: {target_drive}\\WinPE\\\n'
                               f'- Tên menu boot: {boot_name}\n\n'
                               'Quá trình có thể mất từ 10 - 45 giây tùy dung lượng file...'):
            res = integrate_winpe_boot(src_path, target_drive, boot_name)
            if res.get('success'):
                messagebox.showinfo('Thành công', res.get('message'))
                self.path_var.set('')
                self.load_entries()
            else:
                messagebox.showerror('Lỗi', res.get('message'))

    def save_boot(self):
        boot_name = self.name_var.get().strip()
        guid = self._get_selected_guid()

        if guid and boot_name:
            res = update_boot_name(guid, boot_name)
            if res['success']:
                messagebox.showinfo('Success', res['message'])
                self.load_entries()
            else:
                messagebox.showerror('Error', res['message'])
        else:
            messagebox.showwarning('Warning', 'Vui lòng chọn mục Boot trong danh sách và nhập tên mới!')

    def delete_selected(self):
        guid = self._get_selected_guid()
        if not guid:
            messagebox.showwarning('Warning', 'Vui lòng chọn mục Boot cần xóa trong danh sách!')
            return
        selected_item = next((x for x in self.entries_data if x['guid'] == guid), None)
        name = selected_item['name'] if selected_item else guid

        if messagebox.askyesno('Confirm Delete', f'Bạn có chắc chắn muốn xóa mục Boot:\n"{name}"\n({guid})?'):
            res = delete_boot_entry(guid)
            if res['success']:
                messagebox.showinfo('Success', res['message'])
                self.load_entries()
            else:
                messagebox.showerror('Error', res['message'])

    def set_default(self):
        guid = self._get_selected_guid()
        if not guid:
            messagebox.showwarning('Warning', 'Vui lòng chọn mục Boot trong danh sách!')
            return
        res = set_default_boot(guid)
        if res['success']:
            messagebox.showinfo('Success', res['message'])
            self.load_entries()
        else:
            messagebox.showerror('Error', res['message'])

    def apply_timeout(self):
        val = self.timeout_var.get().strip()
        res = set_boot_timeout(val)
        if res['success']:
            messagebox.showinfo('Success', res['message'])
        else:
            messagebox.showerror('Error', res['message'])


# ── STANDALONE BOOT MANAGER API FUNCTIONS FOR WEB/CLI ─────────────────────

def get_boot_entries():
    """Fetches clean list of BCD boot entries via bcdedit /v."""
    try:
        res = subprocess.run(['bcdedit', '/v'], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if res.returncode != 0:
            res = subprocess.run(['bcdedit'], capture_output=True, text=True, encoding='utf-8', errors='ignore')

        output = res.stdout
        entries = []
        current_type = ""
        current_entry = {}
        current_raw = []

        default_guid = ""
        timeout_val = "30"

        for line in output.splitlines():
            line_str = line.strip()
            if not line_str:
                if current_entry and "identifier" in current_entry:
                    current_entry["raw"] = "\n".join(current_raw)
                    current_entry["type"] = current_type or "Boot Entry"
                    entries.append(current_entry)
                current_entry = {}
                current_raw = []
                continue

            if "---" in line_str or (not ":" in line and not "  " in line and len(line_str) > 3 and not line_str.startswith("{")):
                current_type = line_str.replace("-", "").strip()
                continue

            current_raw.append(line)

            parts = line.split(None, 1)
            if len(parts) == 2:
                key = parts[0].lower().strip()
                val = parts[1].strip()
                current_entry[key] = val
                if key == "default":
                    default_guid = val
                if key == "timeout":
                    timeout_val = val

        if current_entry and "identifier" in current_entry:
            current_entry["raw"] = "\n".join(current_raw)
            current_entry["type"] = current_type or "Boot Entry"
            entries.append(current_entry)

        cleaned_entries = []
        for item in entries:
            guid = item.get("identifier", "")
            desc = item.get("description", item.get("type", "Unknown Entry"))
            path = item.get("path", "")
            device = item.get("device", item.get("osdevice", ""))
            is_def = (guid.lower() == default_guid.lower())

            cleaned_entries.append({
                "guid": guid,
                "name": desc,
                "path": path,
                "device": device,
                "type": item.get("type", "Boot Entry"),
                "is_default": is_def,
                "raw": item.get("raw", "")
            })

        return cleaned_entries, default_guid, timeout_val
    except Exception as e:
        return [], "", "30"

def get_available_partitions():
    """Returns list of fixed local disk partitions (HDD/SSD) suitable for storing WinPE."""
    partitions = []
    kernel32 = ctypes.windll.kernel32

    for letter in string.ascii_uppercase:
        root_path = f"{letter}:\\"
        drive_name = f"{letter}:"
        if not os.path.exists(root_path):
            continue

        dtype = kernel32.GetDriveTypeW(root_path)
        if dtype not in (3, 2):  # 3=Fixed (HDD/SSD), 2=Removable (USB)
            continue

        vol_name_buf = ctypes.create_unicode_buffer(1024)
        fs_buf = ctypes.create_unicode_buffer(1024)
        rc = kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(root_path),
            vol_name_buf,
            ctypes.sizeof(vol_name_buf),
            None, None, None,
            fs_buf,
            ctypes.sizeof(fs_buf)
        )
        label = vol_name_buf.value if rc else ""
        fs_type = fs_buf.value if rc else ""

        try:
            usage = shutil.disk_usage(root_path)
            total_gb = round(usage.total / (1024 ** 3), 1)
            free_gb = round(usage.free / (1024 ** 3), 1)
            used_gb = round(usage.used / (1024 ** 3), 1)
        except Exception:
            total_gb = free_gb = used_gb = 0

        is_system = (letter.upper() == os.environ.get("SystemDrive", "C:")[0].upper())
        is_removable = (dtype == 2)

        type_str = "USB" if is_removable else ("Hệ thống Windows" if is_system else "Ổ đĩa dữ liệu")
        label_str = f" [{label}]" if label else ""
        rec_tag = " - Khuyên dùng lưu WinPE" if (not is_system and free_gb >= 5 and not is_removable) else ""

        display = f"{drive_name}{label_str} ({free_gb} GB trống / {total_gb} GB) - {type_str}{rec_tag}"

        partitions.append({
            "drive": drive_name,
            "root": root_path,
            "label": label,
            "fs_type": fs_type,
            "total_gb": total_gb,
            "free_gb": free_gb,
            "used_gb": used_gb,
            "is_system": is_system,
            "is_removable": is_removable,
            "display": display
        })

    partitions.sort(key=lambda x: (x["is_removable"], -x["free_gb"]))
    return partitions

def is_uefi_system():
    """Detects whether current Windows boots via UEFI or BIOS/MBR."""
    if os.environ.get("firmware_type", "").upper() == "UEFI":
        return True
    try:
        res = subprocess.run(['bcdedit', '/enum', '{bootmgr}'], capture_output=True, text=True, errors='ignore')
        if '.efi' in res.stdout.lower():
            return True
    except Exception:
        pass
    return os.path.exists(r"C:\Windows\System32\boot\winload.efi") or os.path.exists(r"C:\Windows\Boot\EFI")

def inspect_winpe_source(source_path):
    """
    Inspects a WinPE source file (.iso or .wim).
    If ISO, temporarily mounts it to discover internal .wim files and companion Apps.
    """
    if not source_path or not os.path.exists(source_path):
        return {"success": False, "message": "File nguồn không tồn tại!"}

    ext = os.path.splitext(source_path)[1].lower()
    base_name = os.path.splitext(os.path.basename(source_path))[0]

    if ext == ".wim":
        size_mb = round(os.path.getsize(source_path) / (1024 * 1024), 1)
        wim_info = {
            "name": os.path.basename(source_path),
            "rel_path": "",
            "size_mb": size_mb,
            "is_recommended": True,
            "description": f"{os.path.basename(source_path)} ({size_mb} MB)"
        }
        return {
            "success": True,
            "is_iso": False,
            "filename": os.path.basename(source_path),
            "wims": [wim_info],
            "has_apps": False,
            "default_name": f"WinPE - {base_name}"
        }

    elif ext == ".iso":
        ps_inspect = f"""
$iso = "{source_path}"
$mount = Mount-DiskImage -ImagePath $iso -StorageType ISO -PassThru
$dl = ($mount | Get-Volume).DriveLetter
if (-not $dl) {{
    $disk = Get-DiskImage -ImagePath $iso | Get-Disk
    $part = Get-Partition -DiskNumber $disk.Number | Where-Object DriveLetter
    $dl = $part.DriveLetter
}}
$root = $dl + ":\\"
$wims = Get-ChildItem -Path $root -Filter "*.wim" -Recurse -ErrorAction SilentlyContinue | Select-Object FullName, Length, Name
$hasApps = Test-Path ($root + "Apps")
$sdi = Get-ChildItem -Path $root -Filter "boot.sdi" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1

foreach ($w in $wims) {{
    $rel = $w.FullName.Substring($root.Length)
    Write-Host "WIM::$($w.Name)::$($w.Length)::$rel"
}}
if ($hasApps) {{
    Write-Host "HAS_APPS::TRUE"
}}
if ($sdi) {{
    Write-Host "HAS_SDI::$($sdi.FullName)"
}}
Dismount-DiskImage -ImagePath $iso | Out-Null
"""
        try:
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_inspect],
                                 capture_output=True, text=True, encoding="utf-8", errors="ignore")
            lines = res.stdout.splitlines()
            wims = []
            has_apps = False
            for line in lines:
                if line.startswith("WIM::"):
                    parts = line.split("::")
                    if len(parts) >= 4:
                        w_name = parts[1]
                        w_len = int(parts[2]) if parts[2].isdigit() else 0
                        w_rel = parts[3]
                        size_mb = round(w_len / (1024 * 1024), 1)
                        is_rec = ("64" in w_name.lower() or "boot.wim" in w_name.lower() or "w11" in w_name.lower())
                        wims.append({
                            "name": w_name,
                            "rel_path": w_rel,
                            "size_mb": size_mb,
                            "is_recommended": is_rec,
                            "description": f"{w_name} ({size_mb} MB)"
                        })
                elif line.startswith("HAS_APPS::TRUE"):
                    has_apps = True

            if not wims:
                return {"success": False, "message": "Không tìm thấy file .wim nào bên trong file ISO này!"}

            wims.sort(key=lambda x: (not x["is_recommended"], -x["size_mb"]))
            wims[0]["is_recommended"] = True

            chosen_wim_name = os.path.splitext(wims[0]["name"])[0]
            default_name = f"WinPE - {base_name} ({chosen_wim_name})"

            return {
                "success": True,
                "is_iso": True,
                "filename": os.path.basename(source_path),
                "wims": wims,
                "has_apps": has_apps,
                "default_name": default_name
            }
        except Exception as e:
            subprocess.run(["powershell", "-NoProfile", "-Command", f'Dismount-DiskImage -ImagePath "{source_path}" -ErrorAction SilentlyContinue'],
                           capture_output=True)
            return {"success": False, "message": f"Lỗi đọc file ISO: {str(e)}"}
    else:
        return {"success": False, "message": "Định dạng file không hỗ trợ! Vui lòng chọn file .iso hoặc .wim."}

def safe_copy_file(src, dst):
    """Safely copies a file, removing ReadOnly attribute if dst already exists and clearing ReadOnly on the copied file."""
    import stat
    if os.path.abspath(src).lower() == os.path.abspath(dst).lower():
        try:
            os.chmod(dst, stat.S_IWRITE | stat.S_IREAD)
        except Exception:
            pass
        return
    if os.path.exists(dst):
        try:
            os.chmod(dst, stat.S_IWRITE | stat.S_IREAD)
        except Exception:
            pass
    shutil.copy2(src, dst)
    try:
        os.chmod(dst, stat.S_IWRITE | stat.S_IREAD)
    except Exception:
        pass

def generate_unique_guid():
    """
    Sinh mã GUID mới hoàn toàn ngẫu nhiên (UUID Version 4) bằng Windows API CoCreateGuid (ole32.dll)
    kết hợp thư viện chuẩn uuid, đảm bảo từng cụm ký tự đều ngẫu nhiên và khác biệt hoàn toàn.
    """
    try:
        class GUID(ctypes.Structure):
            _fields_ = [
                ('Data1', ctypes.c_ulong),
                ('Data2', ctypes.c_ushort),
                ('Data3', ctypes.c_ushort),
                ('Data4', ctypes.c_ubyte * 8)
            ]
        guid = GUID()
        if ctypes.windll.ole32.CoCreateGuid(ctypes.byref(guid)) == 0:
            return '{{{0:08x}-{1:04x}-{2:04x}-{3:02x}{4:02x}-{5:02x}{6:02x}{7:02x}{8:02x}{9:02x}{10:02x}}}'.format(
                guid.Data1, guid.Data2, guid.Data3,
                guid.Data4[0], guid.Data4[1],
                guid.Data4[2], guid.Data4[3], guid.Data4[4], guid.Data4[5], guid.Data4[6], guid.Data4[7]
            ).lower()
    except Exception:
        pass
    return f"{{{uuid.uuid4()}}}".lower()

def get_fresh_unique_guid():
    """
    Sinh một GUID mới và kiểm tra đối chiếu trực tiếp với toàn bộ danh sách GUID hiện có trong BCD
    để cam kết 100% không bao giờ xảy ra trùng lặp.
    """
    try:
        existing_entries, _, _ = get_boot_entries()
        existing_guids = {e.get('guid', '').strip().lower() for e in existing_entries}
    except Exception:
        existing_guids = set()

    for _ in range(50):
        candidate = generate_unique_guid()
        if candidate.lower() not in existing_guids:
            return candidate
    return f"{{{uuid.uuid4()}}}".lower()

def integrate_winpe_boot(source_path, target_drive='C:', boot_name='WinPE Rescue', selected_wim_rel=None, copy_apps=False):
    """
    Integrates a WinPE image (.iso or .wim) directly into an onboard hard drive partition
    and registers an entry in the Windows BCD.
    """
    if not source_path or not os.path.exists(source_path):
        return {"success": False, "message": "File nguồn (.iso hoặc .wim) không tồn tại!"}

    target_drive = target_drive.strip().rstrip('\\/:').upper() + ":"
    target_root = f"{target_drive}\\"
    if not os.path.exists(target_root):
        return {"success": False, "message": f"Phân vùng đích '{target_drive}' không tồn tại trên hệ thống!"}

    ext = os.path.splitext(source_path)[1].lower()
    base_name = os.path.splitext(os.path.basename(source_path))[0]
    if not boot_name:
        boot_name = f"WinPE - {base_name}"

    target_pe_dir = os.path.join(target_root, "WinPE")
    os.makedirs(target_pe_dir, exist_ok=True)
    target_wim_path = os.path.join(target_pe_dir, "boot.wim")
    target_sdi_path = os.path.join(target_pe_dir, "boot.sdi")

    mounted_iso = False
    temp_mounted_root = ""

    try:
        if ext == ".iso":
            ps_mount = f"""
$iso = "{source_path}"
$mount = Mount-DiskImage -ImagePath $iso -StorageType ISO -PassThru
$dl = ($mount | Get-Volume).DriveLetter
if (-not $dl) {{
    $disk = Get-DiskImage -ImagePath $iso | Get-Disk
    $part = Get-Partition -DiskNumber $disk.Number | Where-Object DriveLetter
    $dl = $part.DriveLetter
}}
Write-Host "MOUNTED_DRIVE::$dl"
"""
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_mount],
                                 capture_output=True, text=True, encoding="utf-8", errors="ignore")
            dl = ""
            for line in res.stdout.splitlines():
                if line.startswith("MOUNTED_DRIVE::"):
                    dl = line.split("::")[1].strip()
                    break

            if not dl:
                return {"success": False, "message": "Không thể gắn (mount) file ISO trong Windows!"}

            mounted_iso = True
            temp_mounted_root = f"{dl}:\\"

            src_wim = ""
            if selected_wim_rel and os.path.exists(os.path.join(temp_mounted_root, selected_wim_rel)):
                src_wim = os.path.join(temp_mounted_root, selected_wim_rel)
            else:
                found_wims = []
                for r, _, files in os.walk(temp_mounted_root):
                    for f in files:
                        if f.lower().endswith(".wim"):
                            f_path = os.path.join(r, f)
                            is_rec = ("64" in f.lower() or "boot.wim" in f.lower() or "w11" in f.lower())
                            found_wims.append((is_rec, os.path.getsize(f_path), f_path))
                if not found_wims:
                    return {"success": False, "message": "Không tìm thấy file .wim nào bên trong file ISO đã chọn!"}
                found_wims.sort(key=lambda x: (not x[0], -x[1]))
                src_wim = found_wims[0][2]

            safe_copy_file(src_wim, target_wim_path)

            sdi_candidates = [
                os.path.join(temp_mounted_root, "boot", "boot.sdi"),
                os.path.join(temp_mounted_root, "sources", "boot.sdi"),
                os.path.join(temp_mounted_root, "PXESRV", "Boot.sdi"),
            ]
            for c in sdi_candidates:
                if os.path.exists(c):
                    safe_copy_file(c, target_sdi_path)
                    break
            if not os.path.exists(target_sdi_path):
                for r, _, files in os.walk(temp_mounted_root):
                    for f in files:
                        if f.lower() == "boot.sdi":
                            safe_copy_file(os.path.join(r, f), target_sdi_path)
                            break
                    if os.path.exists(target_sdi_path):
                        break

            if copy_apps:
                iso_apps = os.path.join(temp_mounted_root, "Apps")
                if os.path.exists(iso_apps):
                    target_apps = os.path.join(target_root, "Apps")
                    if not os.path.exists(target_apps):
                        shutil.copytree(iso_apps, target_apps)

        elif ext == ".wim":
            if os.path.abspath(source_path) != os.path.abspath(target_wim_path):
                safe_copy_file(source_path, target_wim_path)
        else:
            return {"success": False, "message": "Định dạng file không hỗ trợ (.iso hoặc .wim)!"}

        if not os.path.exists(target_sdi_path):
            sys_sdi_candidates = [
                r"C:\Windows\Boot\DVD\EFI\boot.sdi",
                r"C:\Windows\Boot\DVD\PCAT\boot.sdi",
                r"C:\Windows\System32\boot.sdi",
                r"C:\Windows\SysWOW64\boot.sdi"
            ]
            for s in sys_sdi_candidates:
                if os.path.exists(s):
                    safe_copy_file(s, target_sdi_path)
                    break

        if not os.path.exists(target_sdi_path):
            return {"success": False, "message": "Không tìm thấy file boot.sdi cần thiết để tạo Ramdisk!"}

    finally:
        if mounted_iso:
            subprocess.run(["powershell", "-NoProfile", "-Command", f'Dismount-DiskImage -ImagePath "{source_path}" -ErrorAction SilentlyContinue'],
                           capture_output=True)

    # ── BCDEDIT CONFIGURATION ──────────────────────────────────────────
    try:
        # 1. Setup {ramdiskoptions}
        subprocess.run(['bcdedit', '/create', '{ramdiskoptions}', '/d', 'Ramdisk Options'], capture_output=True, text=True, errors='ignore')
        subprocess.run(['bcdedit', '/set', '{ramdiskoptions}', 'ramdisksdidevice', f'partition={target_drive}'], capture_output=True, text=True, errors='ignore')
        subprocess.run(['bcdedit', '/set', '{ramdiskoptions}', 'ramdisksdipath', r'\WinPE\boot.sdi'], capture_output=True, text=True, errors='ignore')

        # 2. Create isolated SDI device options with fresh random GUID
        sdi_guid = get_fresh_unique_guid()
        res_sdi = subprocess.run(['bcdedit', '/create', sdi_guid, '/d', 'WinPE Ramdisk Device', '/device'], capture_output=True, text=True, errors='ignore')
        if res_sdi.returncode != 0 or sdi_guid.lower() not in res_sdi.stdout.lower():
            # Fallback to auto-created device ID if explicit guid rejected
            res_sdi = subprocess.run(['bcdedit', '/create', '/d', 'WinPE Ramdisk Device', '/device'], capture_output=True, text=True, errors='ignore')
            match_sdi = re.search(r'\{[0-9a-fA-F\-]{36}\}', res_sdi.stdout)
            sdi_guid = match_sdi.group(0) if match_sdi else "{ramdiskoptions}"

        if sdi_guid != "{ramdiskoptions}":
            subprocess.run(['bcdedit', '/set', sdi_guid, 'ramdisksdidevice', f'partition={target_drive}'], capture_output=True, text=True, errors='ignore')
            subprocess.run(['bcdedit', '/set', sdi_guid, 'ramdisksdipath', r'\WinPE\boot.sdi'], capture_output=True, text=True, errors='ignore')

        # 3. Create OS Loader entry with brand new unique random GUID
        guid = get_fresh_unique_guid()
        res_loader = subprocess.run(['bcdedit', '/create', guid, '/d', boot_name, '/application', 'osloader'], capture_output=True, text=True, errors='ignore')
        
        # Fallback if bcdedit does not accept custom GUID directly
        if res_loader.returncode != 0 or guid.lower() not in res_loader.stdout.lower():
            res_loader = subprocess.run(['bcdedit', '/create', '/d', boot_name, '/application', 'osloader'], capture_output=True, text=True, errors='ignore')
            match_loader = re.search(r'\{[0-9a-fA-F\-]{36}\}', res_loader.stdout)
            if not match_loader:
                err_msg = res_loader.stderr.strip() or res_loader.stdout.strip()
                return {"success": False, "message": f"Không thể tạo BCD Entry: {err_msg}"}
            guid = match_loader.group(0)

        # Detect UEFI or BIOS
        is_uefi = is_uefi_system()
        loader_path = r"\Windows\System32\boot\winload.efi" if is_uefi else r"\Windows\System32\boot\winload.exe"

        # 4. Set Loader properties
        cmds = [
            ['bcdedit', '/set', guid, 'device', f'ramdisk=[{target_drive}]\\WinPE\\boot.wim,{sdi_guid}'],
            ['bcdedit', '/set', guid, 'osdevice', f'ramdisk=[{target_drive}]\\WinPE\\boot.wim,{sdi_guid}'],
            ['bcdedit', '/set', guid, 'path', loader_path],
            ['bcdedit', '/set', guid, 'systemroot', r'\Windows'],
            ['bcdedit', '/set', guid, 'winpe', 'yes'],
            ['bcdedit', '/set', guid, 'detecthal', 'yes'],
            ['bcdedit', '/displayorder', guid, '/addlast']
        ]
        for c in cmds:
            subprocess.run(c, capture_output=True, text=True, errors='ignore')

        # 5. Ensure timeout >= 30s
        try:
            _, _, cur_timeout = get_boot_entries()
            if int(cur_timeout) < 15:
                set_boot_timeout(30)
        except Exception:
            pass

        return {
            "success": True,
            "message": f"Đã tích hợp thành công WinPE vào ổ cứng ({target_drive}\\WinPE\\boot.wim)!\n\n- Menu Boot: '{boot_name}' (GUID: {guid})\n- Chế độ Boot: {'UEFI (winload.efi)' if is_uefi else 'Legacy BIOS (winload.exe)'}\n\nKhi máy tính gặp sự cố, bạn chỉ cần khởi động lại máy và chọn '{boot_name}' để boot trực tiếp vào WinPE cứu hộ mà không cần USB!",
            "guid": guid,
            "target_path": f"{target_drive}\\WinPE\\boot.wim"
        }
    except Exception as e:
        return {"success": False, "message": f"Lỗi cấu hình BCD: {str(e)}"}

def add_wim_boot_entry(wim_path, boot_name="WinPE Boot", target_drive="C:"):
    """Compatibility wrapper calling integrate_winpe_boot."""
    return integrate_winpe_boot(wim_path, target_drive=target_drive, boot_name=boot_name)

def delete_boot_entry(guid):
    """Deletes a BCD entry by GUID."""
    if not guid:
        return {"success": False, "message": "Vui lòng chọn mục Boot cần xóa!"}
    try:
        res = subprocess.run(['bcdedit', '/delete', guid, '/f'], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if res.returncode == 0 or "successfully" in res.stdout.lower() or "thành công" in res.stdout.lower():
            return {"success": True, "message": f"Đã xóa mục boot {guid} thành công!"}
        else:
            return {"success": False, "message": res.stderr.strip() or res.stdout.strip()}
    except Exception as e:
        return {"success": False, "message": str(e)}

def set_default_boot(guid):
    """Sets entry as default boot entry."""
    if not guid:
        return {"success": False, "message": "Vui lòng chọn mục Boot làm mặc định!"}
    try:
        res = subprocess.run(['bcdedit', '/default', guid], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if res.returncode == 0:
            return {"success": True, "message": f"Đã đặt {guid} làm hệ điều hành mặc định!"}
        else:
            return {"success": False, "message": res.stderr.strip() or res.stdout.strip()}
    except Exception as e:
        return {"success": False, "message": str(e)}

def set_boot_timeout(seconds):
    """Sets boot menu timeout in seconds."""
    try:
        sec = int(seconds)
        res = subprocess.run(['bcdedit', '/timeout', str(sec)], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if res.returncode == 0:
            return {"success": True, "message": f"Đã đặt thời gian chờ Boot menu là {sec} giây."}
        else:
            return {"success": False, "message": res.stderr.strip() or res.stdout.strip()}
    except Exception as e:
        return {"success": False, "message": str(e)}

def update_boot_name(guid, new_name):
    """Updates description/name of a boot entry."""
    if not guid or not new_name:
        return {"success": False, "message": "Vui lòng chỉ định GUID và tên mới!"}
    try:
        res = subprocess.run(['bcdedit', '/set', guid, 'description', new_name], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if res.returncode == 0:
            return {"success": True, "message": f"Đã đổi tên mục Boot sang '{new_name}' thành công!"}
        else:
            return {"success": False, "message": res.stderr.strip() or res.stdout.strip()}
    except Exception as e:
        return {"success": False, "message": str(e)}



def open_boot_manager_gui():
    """Launches Tkinter Boot Manager GUI window."""
    try:
        if getattr(sys, 'frozen', False):
            subprocess.Popen([sys.executable, "--module", "boot_manager"])
        else:
            main_py = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
            subprocess.Popen([sys.executable, main_py, "--module", "boot_manager"])
        return {"success": True, "message": "Đã mở giao diện Boot Manager GUI!"}
    except Exception as e:
        return {"success": False, "message": str(e)}
