"""
SendTo Editor Module
Add, delete, run, browse, save list for SendTo menu
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import shutil
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS

SENDTO_PATH = os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\SendTo')


class SendToEditor:
    def __init__(self, parent):
        self.parent = parent
        self.parent.geometry('700x500')
        self.parent.configure(bg=COLORS['bg'])
        self.setup_ui()
        self.load_entries()

    def setup_ui(self):
        hdr = tk.Frame(self.parent, bg=COLORS['bg_header'])
        hdr.pack(fill='x')
        tk.Label(hdr, text='📤  SendTo Editor', font=FONTS['large'],
                  bg=COLORS['bg_header'], fg='white', pady=10).pack(side='left', padx=15)
        tk.Label(hdr, text=SENDTO_PATH, font=FONTS['small'],
                  bg=COLORS['bg_header'], fg='#BDC3C7').pack(side='right', padx=15)

        # Toolbar
        bar = tk.Frame(self.parent, bg=COLORS['bg_dark'])
        bar.pack(fill='x')
        for text, cmd, color in [
            ('➕ Add File', self.add_file, COLORS['accent']),
            ('➕ Add Folder', self.add_folder, '#27AE60'),
            ('❌ Delete', self.delete_entry, COLORS['danger']),
            ('▶️ Run', self.run_entry, '#8E44AD'),
            ('📂 Browse', self.browse_sendto, COLORS['info']),
            ('🔄 Refresh', self.load_entries, COLORS['warning']),
        ]:
            tk.Button(bar, text=text, font=FONTS['small'],
                       bg=color, fg='white', relief='flat',
                       padx=8, pady=4, cursor='hand2',
                       command=cmd).pack(side='left', padx=2, pady=3)

        # List
        list_frame = tk.Frame(self.parent, bg=COLORS['bg'])
        list_frame.pack(fill='both', expand=True, padx=10, pady=8)

        cols = ('Name', 'Type', 'Target', 'Size')
        self.tree = ttk.Treeview(list_frame, columns=cols, show='headings')
        widths = [200, 80, 300, 80]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col, anchor='w')
            self.tree.column(col, width=w, minwidth=50)

        vsb = ttk.Scrollbar(list_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True)

        self.tree.tag_configure('lnk', foreground='#2980B9')
        self.tree.tag_configure('exe', foreground='#27AE60')
        self.tree.tag_configure('folder', foreground='#F39C12')

        # Add entry form
        form_frame = tk.LabelFrame(self.parent, text='  Add Custom Entry  ',
                                    font=FONTS['subtitle'], bg=COLORS['bg'])
        form_frame.pack(fill='x', padx=10, pady=3)

        row = tk.Frame(form_frame, bg=COLORS['bg'])
        row.pack(padx=10, pady=8, fill='x')

        tk.Label(row, text='Name:', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left', padx=3)
        self.name_var = tk.StringVar()
        tk.Entry(row, textvariable=self.name_var, font=FONTS['normal'],
                  width=20).pack(side='left', padx=3)

        tk.Label(row, text='Target:', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left', padx=8)
        self.target_var = tk.StringVar()
        tk.Entry(row, textvariable=self.target_var, font=FONTS['normal'],
                  width=35).pack(side='left', padx=3)

        tk.Button(row, text='...', font=FONTS['small'],
                   bg=COLORS['info'], fg='white', relief='flat', cursor='hand2',
                   command=lambda: self.target_var.set(
                       filedialog.askopenfilename() or self.target_var.get()
                   )).pack(side='left', padx=3)

        tk.Button(row, text='💾 Create Shortcut',
                   font=FONTS['small'], bg=COLORS['accent'], fg='white',
                   relief='flat', padx=10, cursor='hand2',
                   command=self.create_shortcut).pack(side='left', padx=8)

    def load_entries(self):
        self.tree.delete(*self.tree.get_children())
        if not os.path.exists(SENDTO_PATH):
            os.makedirs(SENDTO_PATH, exist_ok=True)

        for fname in sorted(os.listdir(SENDTO_PATH)):
            fpath = os.path.join(SENDTO_PATH, fname)
            ext = os.path.splitext(fname)[1].lower()
            ftype = 'Shortcut' if ext == '.lnk' else 'Executable' if ext == '.exe' else 'Folder' if os.path.isdir(fpath) else 'File'
            try:
                size = os.path.getsize(fpath)
                size_str = f'{size:,} B'
            except:
                size_str = ''
            tag = 'lnk' if ext == '.lnk' else 'exe' if ext == '.exe' else 'folder'
            self.tree.insert('', 'end', values=(fname, ftype, fpath, size_str), tags=(tag,))

    def add_file(self):
        path = filedialog.askopenfilename(
            filetypes=[('All files', '*.*')]
        )
        if path:
            dest = os.path.join(SENDTO_PATH, os.path.basename(path))
            shutil.copy2(path, dest)
            self.load_entries()
            messagebox.showinfo('Added', f'Đã thêm: {os.path.basename(path)}')

    def add_folder(self):
        path = filedialog.askdirectory()
        if path:
            # Create shortcut to folder
            name = os.path.basename(path) + '.lnk'
            self._create_lnk(path, os.path.join(SENDTO_PATH, name))
            self.load_entries()

    def _create_lnk(self, target, lnk_path):
        cmd = (
            f'$s=(New-Object -COM WScript.Shell).CreateShortcut("{lnk_path}"); '
            f'$s.TargetPath="{target}"; $s.Save()'
        )
        subprocess.run(['powershell', '-Command', cmd], capture_output=True)

    def create_shortcut(self):
        name = self.name_var.get().strip()
        target = self.target_var.get().strip()
        if not name or not target:
            messagebox.showwarning('Warning', 'Nhập Name và Target!')
            return
        if not name.endswith('.lnk'):
            name += '.lnk'
        lnk_path = os.path.join(SENDTO_PATH, name)
        self._create_lnk(target, lnk_path)
        self.load_entries()
        messagebox.showinfo('Created', f'Đã tạo shortcut: {name}')

    def delete_entry(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Warning', 'Chọn mục cần xóa!')
            return
        vals = self.tree.item(sel[0], 'values')
        name, path = vals[0], vals[2]
        if messagebox.askyesno('Confirm', f'Xóa "{name}"?'):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.load_entries()
            except Exception as e:
                messagebox.showerror('Error', str(e))

    def run_entry(self):
        sel = self.tree.selection()
        if sel:
            path = self.tree.item(sel[0], 'values')[2]
            try:
                os.startfile(path)
            except Exception as e:
                messagebox.showerror('Error', str(e))

    def browse_sendto(self):
        os.startfile(SENDTO_PATH)
