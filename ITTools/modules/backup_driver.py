"""
Backup/Restore Driver Module
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import os
import sys
import threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS


class BackupDriver:
    def __init__(self, parent):
        self.parent = parent
        self.parent.geometry('750x580')
        self.parent.configure(bg=COLORS['bg'])
        self.all_drivers = []
        self.setup_ui()
        threading.Thread(target=self.load_drivers, daemon=True).start()

    def setup_ui(self):
        hdr = tk.Frame(self.parent, bg=COLORS['bg_header'])
        hdr.pack(fill='x')
        tk.Label(hdr, text='💾  Backup/Restore Drivers', font=FONTS['large'],
                  bg=COLORS['bg_header'], fg='white', pady=10).pack(side='left', padx=15)

        # Toolbar
        bar = tk.Frame(self.parent, bg=COLORS['bg_dark'])
        bar.pack(fill='x')
        for text, cmd, color in [
            ('💾 Backup All', self.backup_all, COLORS['accent']),
            ('💾 Backup Selected', self.backup_selected, COLORS['info']),
            ('📥 Restore', self.restore_drivers, '#8E44AD'),
            ('🔄 Refresh', self.load_drivers, COLORS['warning']),
        ]:
            tk.Button(bar, text=text, font=FONTS['small'],
                       bg=color, fg='white', relief='flat',
                       padx=8, pady=4, cursor='hand2',
                       command=cmd).pack(side='left', padx=2, pady=3)

        # Driver list
        cols = ('ProviderName', 'Driver', 'Class', 'Version', 'Date')
        self.tree = ttk.Treeview(self.parent, columns=cols, show='headings',
                                  selectmode='extended', height=15)
        widths = [160, 200, 100, 100, 100]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col, anchor='w')
            self.tree.column(col, width=w, minwidth=50)
        vsb = ttk.Scrollbar(self.parent, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True, padx=5, pady=5)

        self.progress = ttk.Progressbar(self.parent, mode='indeterminate')
        self.progress.pack(fill='x', padx=5, pady=2)

        self.status_var = tk.StringVar(value='Ready')
        tk.Label(self.parent, textvariable=self.status_var,
                  font=FONTS['small'], bg=COLORS['bg'],
                  fg=COLORS['text_light']).pack(anchor='w', padx=10)

    def load_drivers(self):
        self.progress.start()
        self.tree.delete(*self.tree.get_children())
        self.all_drivers = []
        loaded = False

        # 1. Fast native pnputil enumeration (<0.1s)
        try:
            res = subprocess.run(
                ['pnputil', '/enum-drivers'],
                capture_output=True, text=True, timeout=12, encoding='utf-8', errors='ignore'
            )
            if res.returncode == 0 and res.stdout.strip():
                current = {}
                for raw_line in res.stdout.splitlines():
                    line = raw_line.strip()
                    if not line:
                        if current.get("driver"):
                            self.all_drivers.append([
                                current.get("provider", "Unknown"),
                                current.get("driver", "-"),
                                current.get("class", "-"),
                                current.get("version", "-"),
                                current.get("date", "-")
                            ])
                            current = {}
                        continue
                    if ":" in line:
                        k, v = [x.strip() for x in line.split(":", 1)]
                        if k == "Published Name":
                            if current.get("driver"):
                                self.all_drivers.append([
                                    current.get("provider", "Unknown"),
                                    current.get("driver", "-"),
                                    current.get("class", "-"),
                                    current.get("version", "-"),
                                    current.get("date", "-")
                                ])
                                current = {}
                            current["driver"] = v
                        elif k == "Provider Name":
                            current["provider"] = v
                        elif k == "Class Name":
                            current["class"] = v
                        elif k == "Driver Version":
                            parts = v.split(" ", 1)
                            if len(parts) == 2:
                                current["date"] = parts[0]
                                current["version"] = parts[1]
                            else:
                                current["version"] = v
                                current["date"] = "-"

                if current.get("driver"):
                    self.all_drivers.append([
                        current.get("provider", "Unknown"),
                        current.get("driver", "-"),
                        current.get("class", "-"),
                        current.get("version", "-"),
                        current.get("date", "-")
                    ])

                if self.all_drivers:
                    loaded = True
                    for i, item in enumerate(self.all_drivers):
                        tag = 'odd' if i % 2 else 'even'
                        self.tree.insert('', 'end', values=item, tags=(tag,))
        except Exception:
            pass

        # 2. Fallback to PowerShell if needed
        if not loaded:
            try:
                result = subprocess.run(
                    ['powershell', '-Command',
                     'Get-WindowsDriver -Online | Select-Object ProviderName, '
                     'Driver, ClassDescription, Version, Date '
                     '| ConvertTo-Csv -NoTypeInformation'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().splitlines()
                    for i, line in enumerate(lines[1:]):
                        parts = [p.strip('"') for p in line.split(',')]
                        if len(parts) >= 4:
                            self.all_drivers.append(parts[:5])
                            tag = 'odd' if i % 2 else 'even'
                            self.tree.insert('', 'end', values=parts[:5], tags=(tag,))
            except Exception:
                pass

        self.progress.stop()
        self.status_var.set(f'{len(self.all_drivers)} drivers found')

    def backup_all(self):
        dest = filedialog.askdirectory(title='Select Backup Folder')
        if not dest:
            return
        os.makedirs(dest, exist_ok=True)
        self.progress.start()
        self.status_var.set('Backing up all drivers...')

        def do_backup():
            try:
                # 1. Try fast PowerShell Export-WindowsDriver first
                ps_cmd = [
                    'powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
                    f'$exp = Export-WindowsDriver -Online -Destination "{dest}" -ErrorAction Continue; @($exp) | Measure-Object'
                ]
                res = subprocess.run(ps_cmd, capture_output=True, text=True, timeout=600)
                items = [d for d in os.listdir(dest) if os.path.isdir(os.path.join(dest, d))] if os.path.exists(dest) else []

                # 2. Fallback to DISM if PowerShell produced 0 files or failed
                if not items or res.returncode != 0:
                    self.status_var.set('PowerShell failed, trying DISM...')
                    res = subprocess.run(
                        ['dism', '/Online', '/Export-Driver', f'/Destination:{dest}'],
                        capture_output=True, text=True, timeout=600
                    )
                    items = [d for d in os.listdir(dest) if os.path.isdir(os.path.join(dest, d))] if os.path.exists(dest) else []

                # 3. Individual Pnputil fallback per-driver if still empty
                if not items and self.all_drivers:
                    self.status_var.set('Trying individual Pnputil fallback...')
                    for drv in self.all_drivers:
                        driver_file = drv[1] if len(drv) > 1 else ''
                        if driver_file:
                            sub = os.path.join(dest, driver_file.replace('.inf', ''))
                            os.makedirs(sub, exist_ok=True)
                            subprocess.run(['pnputil', '/export-driver', driver_file, sub],
                                           capture_output=True, text=True, timeout=20)
                    items = [d for d in os.listdir(dest) if os.path.isdir(os.path.join(dest, d))] if os.path.exists(dest) else []

                self.progress.stop()
                if items:
                    messagebox.showinfo('Backup', f'✅ Successfully backed up {len(items)} driver(s) to:\n{dest}')
                    self.status_var.set(f'Backup complete ({len(items)} drivers)!')
                else:
                    messagebox.showerror('Error', res.stderr or res.stdout or 'Backup failed')
                    self.status_var.set('Backup failed!')
            except Exception as e:
                self.progress.stop()
                messagebox.showerror('Error', str(e))
                self.status_var.set('Backup error!')

        threading.Thread(target=do_backup, daemon=True).start()

    def backup_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Warning', 'Select drivers to backup!')
            return
        dest = filedialog.askdirectory(title='Select Backup Folder')
        if not dest:
            return
        os.makedirs(dest, exist_ok=True)
        self.progress.start()
        self.status_var.set('Backing up selected drivers...')

        def do_selected():
            count = 0
            for iid in sel:
                vals = self.tree.item(iid, 'values')
                driver = vals[1] if len(vals) > 1 else ''
                if driver:
                    res = subprocess.run(
                        ['pnputil', '/export-driver', driver, dest],
                        capture_output=True, text=True, timeout=60
                    )
                    if res.returncode == 0:
                        count += 1
            self.progress.stop()
            messagebox.showinfo('Backup', f'✅ {count} selected driver(s) backed up to:\n{dest}')
            self.status_var.set(f'{count} driver(s) backed up!')

        threading.Thread(target=do_selected, daemon=True).start()

    def restore_drivers(self):
        folder = filedialog.askdirectory(title='Select Driver Backup Folder')
        if not folder:
            return
        if messagebox.askyesno('Restore', f'Restore drivers from:\n{folder}?'):
            self.progress.start()
            self.status_var.set('Restoring drivers...')

            def do_restore():
                try:
                    result = subprocess.run(
                        ['pnputil', '/add-driver',
                         os.path.join(folder, '*.inf'),
                         '/subdirs', '/install'],
                        capture_output=True, text=True, shell=True, timeout=600
                    )
                    self.progress.stop()
                    # 0 = Success, 3010 = Reboot required
                    if result.returncode in [0, 3010]:
                        msg = '✅ Drivers restored successfully!'
                        if result.returncode == 3010:
                            msg += '\n(System restart may be required)'
                        messagebox.showinfo('Restore', msg)
                        self.status_var.set('Restore complete!')
                    else:
                        messagebox.showerror('Error', result.stderr or result.stdout)
                        self.status_var.set('Restore failed!')
                except Exception as e:
                    self.progress.stop()
                    messagebox.showerror('Error', str(e))
                    self.status_var.set('Restore error!')

            threading.Thread(target=do_restore, daemon=True).start()

