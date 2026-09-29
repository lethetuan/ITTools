"""
Boot Manager Module - BCDEDIT Manager & WinPE Boot Configurator
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import os
import sys
import re

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

        # Inputs Row
        row1 = tk.Frame(form_frame, bg=COLORS['bg'])
        row1.pack(fill='x', pady=4)

        tk.Label(row1, text='WinPE Path:', font=FONTS['normal'], bg=COLORS['bg']).grid(row=0, column=0, sticky='w', padx=5)
        self.path_var = tk.StringVar()
        tk.Entry(row1, textvariable=self.path_var, font=FONTS['normal'], width=32).grid(row=0, column=1, padx=5)
        tk.Button(row1, text='📁', font=FONTS['small'], bg='#E2E8F0', relief='flat', command=self.browse_wim).grid(row=0, column=2, padx=2)

        tk.Label(row1, text='Boot Name:', font=FONTS['normal'], bg=COLORS['bg']).grid(row=0, column=3, sticky='w', padx=(15, 5))
        self.name_var = tk.StringVar()
        tk.Entry(row1, textvariable=self.name_var, font=FONTS['normal'], width=25).grid(row=0, column=4, padx=5)

        # Buttons Row
        btn_row = tk.Frame(form_frame, bg=COLORS['bg'])
        btn_row.pack(pady=6)

        tk.Button(btn_row, text='➕ Add .wim', font=FONTS['subtitle'], bg='#2ECC71', fg='white',
                  relief='flat', padx=18, pady=4, cursor='hand2', command=self.browse_wim).pack(side='left', padx=8)

        tk.Button(btn_row, text='➖ Delete', font=FONTS['subtitle'], bg='#E74C3C', fg='white',
                  relief='flat', padx=18, pady=4, cursor='hand2', command=self.delete_selected).pack(side='left', padx=8)

        tk.Button(btn_row, text='💾 Save boot', font=FONTS['subtitle'], bg='#3498DB', fg='white',
                  relief='flat', padx=18, pady=4, cursor='hand2', command=self.save_boot).pack(side='left', padx=8)

        # Details Output Box
        raw_frame = tk.LabelFrame(self.parent, text='  Selected Boot Details  ', font=FONTS['subtitle'], bg=COLORS['bg'])
        raw_frame.pack(fill='x', padx=10, pady=5)

        self.detail_text = tk.Text(raw_frame, font=FONTS['mono'], bg='#FFF8DC', fg='#333333',
                                   height=6, relief='flat', padx=8, pady=5)
        self.detail_text.pack(fill='x', padx=5, pady=5)

    def load_entries(self):
        self.tree.delete(*self.tree.get_children())
        entries, default_guid, timeout = get_boot_entries()
        self.entries_data = entries
        self.timeout_var.set(timeout or '30')

        for item in entries:
            is_def = '⭐ Default' if item['is_default'] else ''
            self.tree.insert('', 'end', iid=item['guid'], values=(item['name'], item['guid'], is_def))

        if entries:
            first_id = entries[0]['guid']
            self.tree.selection_set(first_id)

    def on_select_entry(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        guid = sel[0]
        selected_item = next((x for x in self.entries_data if x['guid'] == guid), None)
        if selected_item:
            self.name_var.set(selected_item['name'])
            self.detail_text.configure(state='normal')
            self.detail_text.delete('1.0', 'end')
            self.detail_text.insert('1.0', selected_item['raw'])
            self.detail_text.configure(state='disabled')

    def browse_wim(self):
        path = filedialog.askopenfilename(
            title='Select WinPE WIM File',
            filetypes=[('WIM Files', '*.wim'), ('All Files', '*.*')]
        )
        if path:
            self.path_var.set(path)
            if not self.name_var.get():
                base_name = os.path.splitext(os.path.basename(path))[0]
                self.name_var.set(f"WinPE - {base_name}")

    def save_boot(self):
        wim_path = self.path_var.get().strip()
        boot_name = self.name_var.get().strip()
        sel = self.tree.selection()

        if wim_path:
            # Adding new WIM entry
            res = add_wim_boot_entry(wim_path, boot_name)
            if res['success']:
                messagebox.showinfo('Success', res['message'])
                self.path_var.set('')
                self.name_var.set('')
                self.load_entries()
            else:
                messagebox.showerror('Error', res['message'])
        elif sel and boot_name:
            # Updating entry name
            guid = sel[0]
            res = update_boot_name(guid, boot_name)
            if res['success']:
                messagebox.showinfo('Success', res['message'])
                self.load_entries()
            else:
                messagebox.showerror('Error', res['message'])
        else:
            messagebox.showwarning('Warning', 'Vui lòng chọn file WIM hoặc nhập tên Boot cần thay đổi!')

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Warning', 'Vui lòng chọn mục Boot cần xóa trong danh sách!')
            return
        guid = sel[0]
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
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Warning', 'Vui lòng chọn mục Boot trong danh sách!')
            return
        guid = sel[0]
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

def add_wim_boot_entry(wim_path, boot_name="WinPE Boot"):
    """Creates a new BCD boot entry for a WIM file."""
    if not wim_path or not os.path.exists(wim_path):
        return {"success": False, "message": "File WIM không tồn tại!"}

    if not boot_name:
        boot_name = f"WinPE ({os.path.basename(wim_path)})"

    try:
        drive_letter, rel_path = os.path.splitdrive(os.path.abspath(wim_path))
        if not drive_letter:
            drive_letter = "C:"

        # 1. Ensure ramdiskoptions exists
        subprocess.run('cmd /c "bcdedit /create {ramdiskoptions} /d ""Ramdisk Options"""', shell=True, capture_output=True)
        subprocess.run('cmd /c "bcdedit /set {ramdiskoptions} ramdisksdi-path \\boot\\boot.sdi"', shell=True, capture_output=True)

        # 2. Create entry
        cmd_create = f'cmd /c "bcdedit /create /d ""{boot_name}"" /application osloader"'
        res = subprocess.run(cmd_create, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')

        match = re.search(r'\{[0-9a-fA-F\-]{36}\}', res.stdout)
        if not match:
            return {"success": False, "message": f"Không thể tạo BCD Entry: {res.stderr or res.stdout}"}

        guid = match.group(0)

        # Detect UEFI or BIOS
        is_uefi = os.path.exists(r"C:\Windows\System32\boot\winload.efi") or os.path.exists(r"C:\Windows\System32\winload.efi")
        loader_path = r"\Windows\System32\boot\winload.efi" if is_uefi else r"\Windows\System32\boot\winload.exe"

        # 3. Set properties
        commands = [
            f'cmd /c "bcdedit /set {guid} device ramdisk="[{drive_letter}]{rel_path},{{ramdiskoptions}}""',
            f'cmd /c "bcdedit /set {guid} osdevice ramdisk="[{drive_letter}]{rel_path},{{ramdiskoptions}}""',
            f'cmd /c "bcdedit /set {guid} path {loader_path}"',
            f'cmd /c "bcdedit /set {guid} systemroot \\Windows"',
            f'cmd /c "bcdedit /set {guid} winpe yes"',
            f'cmd /c "bcdedit /set {guid} detecthal yes"',
            f'cmd /c "bcdedit /displayorder {guid} /addlast"'
        ]

        for c in commands:
            subprocess.run(c, shell=True, capture_output=True)

        return {"success": True, "message": f"Đã thêm menu boot WIM '{boot_name}' (GUID: {guid}) thành công!", "guid": guid}
    except Exception as e:
        return {"success": False, "message": str(e)}

def delete_boot_entry(guid):
    """Deletes a BCD entry by GUID."""
    if not guid:
        return {"success": False, "message": "Vui lòng chọn mục Boot cần xóa!"}
    try:
        cmd = f'cmd /c "bcdedit /delete {guid} /f"'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
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
        cmd = f'cmd /c "bcdedit /default {guid}"'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
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
        cmd = f'cmd /c "bcdedit /timeout {sec}"'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
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
        cmd = f'cmd /c "bcdedit /set {guid} description ""{new_name}"""'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if res.returncode == 0:
            return {"success": True, "message": f"Đã đổi tên mục Boot sang '{new_name}' thành công!"}
        else:
            return {"success": False, "message": res.stderr.strip() or res.stdout.strip()}
    except Exception as e:
        return {"success": False, "message": str(e)}

def open_boot_manager_gui():
    """Launches Tkinter Boot Manager GUI window."""
    try:
        main_py = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
        subprocess.Popen([sys.executable, main_py, "--module", "boot_manager"])
        return {"success": True, "message": "Đã mở giao diện Boot Manager GUI!"}
    except Exception as e:
        return {"success": False, "message": str(e)}
