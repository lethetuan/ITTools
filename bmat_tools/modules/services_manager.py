"""
Services Manager Module
Start, Stop, Restart services, change startup type, view logs
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS


class ServicesManager:
    def __init__(self, parent):
        self.parent = parent
        self.parent.geometry('950x650')
        self.parent.configure(bg=COLORS['bg'])
        self.all_services = []
        self.setup_ui()
        threading.Thread(target=self.load_services, daemon=True).start()

    def setup_ui(self):
        hdr = tk.Frame(self.parent, bg=COLORS['bg_header'])
        hdr.pack(fill='x')
        tk.Label(hdr, text='⚙️  Services Manager', font=FONTS['large'],
                  bg=COLORS['bg_header'], fg='white', pady=10).pack(side='left', padx=15)

        # Toolbar
        bar = tk.Frame(self.parent, bg=COLORS['bg_dark'])
        bar.pack(fill='x')
        for text, cmd, color in [
            ('▶ Start', self.start_service, COLORS['accent']),
            ('⏹ Stop', self.stop_service, COLORS['danger']),
            ('🔄 Restart', self.restart_service, COLORS['warning']),
            ('🔄 Refresh', self.load_services, COLORS['info']),
            ('📋 Copy Name', self.copy_name, '#8E44AD'),
        ]:
            tk.Button(bar, text=text, font=FONTS['small'],
                       bg=color, fg='white', relief='flat',
                       padx=8, pady=4, cursor='hand2',
                       command=cmd).pack(side='left', padx=2, pady=3)

        # Startup type
        tk.Label(bar, text='  Set Type:', font=FONTS['small'],
                  bg=COLORS['bg_dark']).pack(side='left', padx=5)
        self.startup_type = ttk.Combobox(bar, values=[
            'Automatic', 'Automatic (Delayed)', 'Manual', 'Disabled'
        ], width=18, state='readonly', font=FONTS['small'])
        self.startup_type.set('Automatic')
        self.startup_type.pack(side='left', padx=3)
        tk.Button(bar, text='Apply Type', font=FONTS['small'],
                   bg='#16A085', fg='white', relief='flat',
                   padx=8, pady=4, cursor='hand2',
                   command=self.set_startup_type).pack(side='left', padx=3)

        # Filter
        filter_frame = tk.Frame(self.parent, bg=COLORS['bg'])
        filter_frame.pack(fill='x', padx=5, pady=3)
        tk.Label(filter_frame, text='🔍 Filter:', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left', padx=5)
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add('write', self.filter_services)
        tk.Entry(filter_frame, textvariable=self.filter_var,
                  font=FONTS['normal'], width=30).pack(side='left', padx=3)

        # Status filter
        self.status_filter = tk.StringVar(value='All')
        for val in ['All', 'Running', 'Stopped']:
            tk.Radiobutton(filter_frame, text=val, value=val,
                            variable=self.status_filter,
                            font=FONTS['normal'], bg=COLORS['bg'],
                            selectcolor=COLORS['selected'],
                            command=self.filter_services).pack(side='left', padx=5)

        self.count_var = tk.StringVar(value='0 services')
        tk.Label(filter_frame, textvariable=self.count_var,
                  font=FONTS['small'], bg=COLORS['bg'],
                  fg=COLORS['text_light']).pack(side='right', padx=10)

        # Main split pane
        paned = tk.PanedWindow(self.parent, orient='vertical', bg=COLORS['bg'],
                                sashwidth=4)
        paned.pack(fill='both', expand=True, padx=5, pady=3)

        # Treeview
        tree_frame = tk.Frame(paned, bg=COLORS['bg'])

        cols = ('Name', 'Display Name', 'Status', 'Start Type', 'Log On As')
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings',
                                  selectmode='browse')
        widths = [140, 220, 80, 120, 120]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col, anchor='w',
                               command=lambda c=col: self.sort_by(c))
            self.tree.column(col, width=w, minwidth=50)

        vsb = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient='horizontal',
                              command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.tree.pack(fill='both', expand=True)

        self.tree.tag_configure('running', foreground='#27AE60')
        self.tree.tag_configure('stopped', foreground='#E74C3C')
        self.tree.tag_configure('paused', foreground='#F39C12')

        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        paned.add(tree_frame, minsize=300)

        # Detail/Log panel
        detail_frame = tk.Frame(paned, bg=COLORS['bg'])
        tk.Label(detail_frame, text='Service Details / Log',
                  font=FONTS['subtitle'], bg=COLORS['bg_dark'],
                  fg=COLORS['text'], pady=3).pack(fill='x')
        self.detail_text = tk.Text(detail_frame, font=FONTS['mono'],
                                    bg='#1E1E1E', fg='#D4D4D4',
                                    height=8, relief='flat',
                                    padx=10, pady=5, state='disabled')
        vsb2 = ttk.Scrollbar(detail_frame, command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=vsb2.set)
        vsb2.pack(side='right', fill='y')
        self.detail_text.pack(fill='both', expand=True)
        paned.add(detail_frame, minsize=100)

        # Context menu
        ctx = tk.Menu(self.parent, tearoff=0)
        for text, cmd in [
            ('▶ Start', self.start_service),
            ('⏹ Stop', self.stop_service),
            ('🔄 Restart', self.restart_service),
            ('📋 Copy Name', self.copy_name),
            ('📄 View Log', self.view_log),
        ]:
            ctx.add_command(label=text, command=cmd)
        self.tree.bind('<Button-3>',
                        lambda e: ctx.post(e.x_root, e.y_root))

        # Progress
        self.progress = ttk.Progressbar(self.parent, mode='indeterminate')
        self.progress.pack(fill='x', padx=5)

    def load_services(self):
        self.progress.start()
        self.tree.delete(*self.tree.get_children())
        self.all_services = []

        result = subprocess.run(
            ['sc', 'query', 'type=', 'all', 'state=', 'all'],
            capture_output=True, text=True
        )
        # Also get detailed info via PowerShell
        ps_result = subprocess.run(
            ['powershell', '-Command',
             'Get-Service | Select-Object Name, DisplayName, Status, StartType, '
             '@{n="LogOn";e={(Get-WmiObject Win32_Service -Filter ("Name='" + "'" + $_.Name + "'" + "'")).StartName}} '
             '| ConvertTo-Csv -NoTypeInformation'],
            capture_output=True, text=True, timeout=30
        )

        if ps_result.returncode == 0:
            lines = ps_result.stdout.strip().splitlines()
            if len(lines) > 1:
                for line in lines[1:]:  # Skip header
                    parts = self._parse_csv_line(line)
                    if len(parts) >= 4:
                        name = parts[0].strip('"')
                        display = parts[1].strip('"')
                        status = parts[2].strip('"')
                        start_type = parts[3].strip('"')
                        logon = parts[4].strip('"') if len(parts) > 4 else ''
                        self.all_services.append({
                            'name': name,
                            'display': display,
                            'status': status,
                            'start_type': start_type,
                            'logon': logon,
                        })

        self.all_services.sort(key=lambda x: x['name'].lower())
        self._populate_tree(self.all_services)
        self.progress.stop()

    def _parse_csv_line(self, line):
        result = []
        current = ''
        in_quotes = False
        for ch in line:
            if ch == '"':
                in_quotes = not in_quotes
            elif ch == ',' and not in_quotes:
                result.append(current)
                current = ''
            else:
                current += ch
        result.append(current)
        return result

    def _populate_tree(self, services):
        self.tree.delete(*self.tree.get_children())
        for svc in services:
            status = svc['status']
            tag = 'running' if 'Running' in status else 'stopped' if 'Stopped' in status else 'paused'
            self.tree.insert('', 'end', iid=svc['name'],
                              values=(svc['name'], svc['display'],
                                      svc['status'], svc['start_type'],
                                      svc['logon']),
                              tags=(tag,))
        self.count_var.set(f'{len(services)} services')

    def filter_services(self, *args):
        q = self.filter_var.get().lower()
        sf = self.status_filter.get()
        filtered = [s for s in self.all_services
                     if (q in s['name'].lower() or q in s['display'].lower())
                     and (sf == 'All'
                          or (sf == 'Running' and 'Running' in s['status'])
                          or (sf == 'Stopped' and 'Stopped' in s['status']))]
        self._populate_tree(filtered)

    def sort_by(self, col):
        col_map = {'Name': 'name', 'Display Name': 'display',
                    'Status': 'status', 'Start Type': 'start_type'}
        key = col_map.get(col, 'name')
        self.all_services.sort(key=lambda x: x.get(key, '').lower())
        self._populate_tree(self.all_services)

    def get_selected_name(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Warning', 'Chọn một service!')
            return None
        return self.tree.item(sel[0], 'values')[0]

    def start_service(self):
        name = self.get_selected_name()
        if name:
            result = subprocess.run(['sc', 'start', name], capture_output=True, text=True)
            if result.returncode == 0:
                messagebox.showinfo('Success', f'✅ Đã start: {name}')
            else:
                messagebox.showerror('Error', result.stderr or result.stdout)
            threading.Thread(target=self.load_services, daemon=True).start()

    def stop_service(self):
        name = self.get_selected_name()
        if name:
            if messagebox.askyesno('Confirm', f'Stop service "{name}"?'):
                result = subprocess.run(['sc', 'stop', name],
                                         capture_output=True, text=True)
                if result.returncode == 0:
                    messagebox.showinfo('Success', f'✅ Đã stop: {name}')
                else:
                    messagebox.showerror('Error', result.stderr or result.stdout)
                threading.Thread(target=self.load_services, daemon=True).start()

    def restart_service(self):
        name = self.get_selected_name()
        if name:
            subprocess.run(['sc', 'stop', name], capture_output=True)
            import time
            time.sleep(2)
            result = subprocess.run(['sc', 'start', name], capture_output=True, text=True)
            messagebox.showinfo('Restart', f'Đã restart: {name}')
            threading.Thread(target=self.load_services, daemon=True).start()

    def set_startup_type(self):
        name = self.get_selected_name()
        if not name:
            return
        type_map = {
            'Automatic': 'auto',
            'Automatic (Delayed)': 'delayed-auto',
            'Manual': 'demand',
            'Disabled': 'disabled',
        }
        sc_type = type_map.get(self.startup_type.get(), 'demand')
        result = subprocess.run(['sc', 'config', name, f'start={sc_type}'],
                                 capture_output=True, text=True)
        if result.returncode == 0:
            messagebox.showinfo('Success', f'✅ Đã set {self.startup_type.get()} cho {name}')
        else:
            messagebox.showerror('Error', result.stdout)

    def copy_name(self):
        name = self.get_selected_name()
        if name:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(name)

    def on_select(self, event):
        name = self.get_selected_name() if self.tree.selection() else None
        if not name:
            return
        self.detail_text.configure(state='normal')
        self.detail_text.delete('1.0', 'end')

        result = subprocess.run(
            ['powershell', '-Command',
             f'Get-Service "{name}" | Format-List * | Out-String'],
            capture_output=True, text=True, timeout=10
        )
        self.detail_text.insert('1.0', result.stdout or 'No details available')
        self.detail_text.configure(state='disabled')

    def view_log(self):
        name = self.get_selected_name()
        if not name:
            return
        log_win = tk.Toplevel(self.parent)
        log_win.title(f'Log - {name}')
        log_win.geometry('700x400')
        log_win.configure(bg=COLORS['bg'])

        text = tk.Text(log_win, font=FONTS['mono'],
                        bg='#1E1E1E', fg='#D4D4D4', relief='flat')
        vsb = ttk.Scrollbar(log_win, command=text.yview)
        text.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        text.pack(fill='both', expand=True)

        def load_log():
            result = subprocess.run(
                ['powershell', '-Command',
                 f'Get-EventLog -LogName System -Source "*{name}*" -Newest 50 '
                 f'| Format-Table TimeGenerated, EntryType, Message -Wrap | Out-String'],
                capture_output=True, text=True, timeout=15
            )
            text.configure(state='normal')
            text.delete('1.0', 'end')
            text.insert('1.0', result.stdout or 'No log entries found')
            text.configure(state='disabled')

        threading.Thread(target=load_log, daemon=True).start()
