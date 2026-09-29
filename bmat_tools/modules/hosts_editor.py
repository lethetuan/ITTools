"""
Hosts File Editor Module
Edit, save, restore default Windows hosts file
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import shutil
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS

HOSTS_PATH = r'C:\Windows\System32\drivers\etc\hosts'
HOSTS_BACKUP = r'C:\Windows\System32\drivers\etc\hosts.bak'

DEFAULT_HOSTS = """# Copyright (c) 1993-2009 Microsoft Corp.
#
# This is a sample HOSTS file used by Microsoft TCP/IP for Windows.
#
# This file contains the mappings of IP addresses to host names. Each
# entry should be kept on an individual line. The IP address should
# be placed in the first column followed by the corresponding host name.
# The IP address and the host name should be separated by at least one
# space.
#
# Additionally, comments (such as these) may be inserted on individual
# lines or following the machine name denoted by a '#' symbol.
#
# For example:
#
#      102.54.94.97     rhino.acme.com          # source server
#       38.25.63.10     x.acme.com              # x client host

# localhost name resolution is handled within DNS itself.
127.0.0.1       localhost
::1             localhost
"""


class HostsEditor:
    def __init__(self, parent):
        self.parent = parent
        self.parent.geometry('750x550')
        self.parent.configure(bg=COLORS['bg'])
        self.setup_ui()
        self.load_hosts()

    def setup_ui(self):
        # Header
        hdr = tk.Frame(self.parent, bg=COLORS['bg_header'])
        hdr.pack(fill='x')
        tk.Label(hdr, text='📝  Hosts File Editor', font=FONTS['large'],
                  bg=COLORS['bg_header'], fg='white', pady=8).pack(side='left', padx=15)
        tk.Label(hdr, text=HOSTS_PATH, font=FONTS['small'],
                  bg=COLORS['bg_header'], fg='#BDC3C7').pack(side='right', padx=15)

        # Toolbar
        toolbar = tk.Frame(self.parent, bg=COLORS['bg_dark'])
        toolbar.pack(fill='x', padx=0, pady=0)

        buttons = [
            ('💾 Save', self.save_hosts, COLORS['accent']),
            ('🔄 Reload', self.load_hosts, COLORS['info']),
            ('📋 Default', self.restore_default, COLORS['warning']),
            ('📂 Backup', self.backup_hosts, '#8E44AD'),
            ('📥 Restore Backup', self.restore_backup, '#D35400'),
            ('✅ Validate', self.validate_hosts, '#16A085'),
        ]
        for text, cmd, color in buttons:
            tk.Button(toolbar, text=text, font=FONTS['small'],
                       bg=color, fg='white', relief='flat',
                       padx=8, pady=4, cursor='hand2',
                       command=cmd).pack(side='left', padx=2, pady=3)

        # Quick add panel
        quick_frame = tk.LabelFrame(self.parent, text='  Quick Add Entry  ',
                                     font=FONTS['subtitle'],
                                     bg=COLORS['bg'], fg=COLORS['text'],
                                     relief='groove')
        quick_frame.pack(fill='x', padx=10, pady=5)

        row = tk.Frame(quick_frame, bg=COLORS['bg'])
        row.pack(padx=10, pady=5)

        tk.Label(row, text='IP:', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left', padx=3)
        self.ip_entry = tk.Entry(row, font=FONTS['normal'], width=16)
        self.ip_entry.insert(0, '0.0.0.0')
        self.ip_entry.pack(side='left', padx=3)

        tk.Label(row, text='Hostname:', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left', padx=3)
        self.host_entry = tk.Entry(row, font=FONTS['normal'], width=30)
        self.host_entry.pack(side='left', padx=3)

        tk.Label(row, text='# Comment:', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left', padx=3)
        self.comment_entry = tk.Entry(row, font=FONTS['normal'], width=20)
        self.comment_entry.pack(side='left', padx=3)

        tk.Button(row, text='➕ Add', font=FONTS['small'],
                   bg=COLORS['accent'], fg='white', relief='flat',
                   padx=8, cursor='hand2',
                   command=self.quick_add).pack(side='left', padx=5)

        # Text editor
        editor_frame = tk.Frame(self.parent, bg=COLORS['bg'])
        editor_frame.pack(fill='both', expand=True, padx=10, pady=(0, 5))

        # Line numbers + text editor
        self.line_nums = tk.Text(editor_frame, width=4, padx=4,
                                  font=('Consolas', 10),
                                  bg='#2D2D2D', fg='#858585',
                                  state='disabled', relief='flat')
        self.line_nums.pack(side='left', fill='y')

        self.text_editor = tk.Text(editor_frame,
                                    font=('Consolas', 10),
                                    bg='#1E1E1E', fg='#D4D4D4',
                                    insertbackground='white',
                                    relief='flat',
                                    padx=8, pady=5,
                                    undo=True)
        vsb = ttk.Scrollbar(editor_frame, command=self._sync_scroll)
        self.text_editor.configure(yscrollcommand=self._update_scroll)
        vsb.pack(side='right', fill='y')
        self.text_editor.pack(fill='both', expand=True)
        self.text_editor.bind('<KeyRelease>', self._highlight_syntax)
        self.text_editor.bind('<MouseWheel>', lambda e: self._update_line_nums())

        # Configure text tags for syntax highlighting
        self.text_editor.tag_configure('comment', foreground='#6A9955')
        self.text_editor.tag_configure('ip', foreground='#569CD6')
        self.text_editor.tag_configure('hostname', foreground='#9CDCFE')
        self.text_editor.tag_configure('blocked', foreground='#F44747')

        # Status bar
        self.status = tk.StringVar(value='Ready')
        tk.Label(self.parent, textvariable=self.status,
                  font=FONTS['small'], bg=COLORS['bg_dark'],
                  fg=COLORS['text_light'], anchor='w',
                  pady=3).pack(fill='x', side='bottom', padx=5)

    def _sync_scroll(self, *args):
        self.text_editor.yview(*args)
        self._update_line_nums()

    def _update_scroll(self, *args):
        self._update_line_nums()

    def _update_line_nums(self):
        self.line_nums.configure(state='normal')
        self.line_nums.delete('1.0', 'end')
        lines = int(self.text_editor.index('end-1c').split('.')[0])
        line_nums_text = '\n'.join(str(i) for i in range(1, lines + 1))
        self.line_nums.insert('1.0', line_nums_text)
        self.line_nums.configure(state='disabled')

    def _highlight_syntax(self, event=None):
        # Remove existing tags
        for tag in ('comment', 'ip', 'hostname', 'blocked'):
            self.text_editor.tag_remove(tag, '1.0', 'end')

        content = self.text_editor.get('1.0', 'end')
        for i, line in enumerate(content.split('\n'), 1):
            stripped = line.strip()
            if stripped.startswith('#') or not stripped:
                start = f'{i}.0'
                end = f'{i}.{len(line)}'
                self.text_editor.tag_add('comment', start, end)
            else:
                parts = stripped.split()
                if parts:
                    # Color the IP
                    col = line.find(parts[0])
                    self.text_editor.tag_add('ip', f'{i}.{col}',
                                              f'{i}.{col + len(parts[0])}')
                    if len(parts) > 1:
                        col2 = line.find(parts[1], col + len(parts[0]))
                        tag = 'blocked' if parts[0] in ('0.0.0.0', '127.0.0.1') and len(parts) > 1 else 'hostname'
                        if parts[0] == '127.0.0.1' and parts[1] == 'localhost':
                            tag = 'hostname'
                        self.text_editor.tag_add(tag, f'{i}.{col2}',
                                                  f'{i}.{col2 + len(parts[1])}')
        self._update_line_nums()

    def load_hosts(self):
        try:
            with open(HOSTS_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            self.text_editor.delete('1.0', 'end')
            self.text_editor.insert('1.0', content)
            self._highlight_syntax()
            self.status.set(f'Loaded: {HOSTS_PATH}')
        except PermissionError:
            messagebox.showerror('Permission Error',
                                  'Cần quyền Administrator để đọc/ghi hosts file!\n'
                                  'Chạy BMAT-Tools với quyền Admin.')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def save_hosts(self):
        content = self.text_editor.get('1.0', 'end-1c')
        try:
            with open(HOSTS_PATH, 'w', encoding='utf-8') as f:
                f.write(content)
            self.status.set(f'Saved at {datetime.datetime.now().strftime("%H:%M:%S")}')
            messagebox.showinfo('Success', '✅ Đã lưu hosts file thành công!')
        except PermissionError:
            messagebox.showerror('Permission Error',
                                  'Cần quyền Administrator!\n'
                                  'Thử lưu bằng PowerShell...')
            # Try via PowerShell
            import tempfile
            tmp = tempfile.mktemp(suffix='.txt')
            with open(tmp, 'w') as f:
                f.write(content)
            result = subprocess.run(
                ['powershell', '-Command',
                 f'Copy-Item "{tmp}" "{HOSTS_PATH}" -Force'],
                capture_output=True
            )
            if result.returncode == 0:
                messagebox.showinfo('Success', 'Đã lưu qua PowerShell!')
            os.remove(tmp)
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def restore_default(self):
        if messagebox.askyesno('Confirm',
                                'Khôi phục hosts file về mặc định?\n'
                                'Các entry hiện tại sẽ bị xóa!'):
            self.text_editor.delete('1.0', 'end')
            self.text_editor.insert('1.0', DEFAULT_HOSTS)
            self._highlight_syntax()
            self.save_hosts()

    def backup_hosts(self):
        path = filedialog.asksaveasfilename(
            title='Backup hosts file',
            defaultextension='.txt',
            initialfile=f'hosts_backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.txt',
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')]
        )
        if path:
            try:
                shutil.copy2(HOSTS_PATH, path)
                messagebox.showinfo('Backup', f'✅ Đã backup: {path}')
            except Exception as e:
                messagebox.showerror('Error', str(e))

    def restore_backup(self):
        path = filedialog.askopenfilename(
            title='Chọn file backup',
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')]
        )
        if path:
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                self.text_editor.delete('1.0', 'end')
                self.text_editor.insert('1.0', content)
                self._highlight_syntax()
                self.save_hosts()
            except Exception as e:
                messagebox.showerror('Error', str(e))

    def quick_add(self):
        ip = self.ip_entry.get().strip()
        host = self.host_entry.get().strip()
        comment = self.comment_entry.get().strip()
        if not ip or not host:
            messagebox.showwarning('Warning', 'Nhập IP và Hostname!')
            return
        entry = f'\n{ip:<16} {host}'
        if comment:
            entry += f'  # {comment}'
        self.text_editor.insert('end', entry)
        self._highlight_syntax()

    def validate_hosts(self):
        content = self.text_editor.get('1.0', 'end')
        errors = []
        import re
        ip_pattern = re.compile(
            r'^(\d{1,3}\.){3}\d{1,3}$|^::1$|^fe80:.*$', re.IGNORECASE
        )
        for i, line in enumerate(content.split('\n'), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            parts = stripped.split()
            if len(parts) < 2:
                errors.append(f'Line {i}: Missing hostname')
            elif not ip_pattern.match(parts[0]):
                errors.append(f'Line {i}: Invalid IP "{parts[0]}"')

        if errors:
            messagebox.showwarning('Validation',
                                    f'Found {len(errors)} issue(s):\n\n' +
                                    '\n'.join(errors[:10]))
        else:
            messagebox.showinfo('Validation', '✅ Hosts file hợp lệ!')

import subprocess
