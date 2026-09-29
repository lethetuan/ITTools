"""
Other Tools Module
Camera, TaskManager, CMD, Registry, Run, Autorun, Unlock Files...
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import winreg
import os
import sys
import ctypes

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS

CAM_REG = r'SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam'
TASKMGR_REG = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System'


class OtherTools:
    def __init__(self, parent):
        self.parent = parent
        self.parent.geometry('750x650')
        self.parent.configure(bg=COLORS['bg'])
        self.setup_ui()

    def setup_ui(self):
        hdr = tk.Frame(self.parent, bg=COLORS['bg_header'])
        hdr.pack(fill='x')
        tk.Label(hdr, text='🔧  Other Tools', font=FONTS['large'],
                  bg=COLORS['bg_header'], fg='white', pady=10).pack(side='left', padx=15)

        # Notebook
        nb = ttk.Notebook(self.parent)
        nb.pack(fill='both', expand=True, padx=8, pady=8)

        # System Tools Tab
        sys_frame = tk.Frame(nb, bg=COLORS['bg'])
        nb.add(sys_frame, text='🖥️ System Tools')
        self._build_system_tools(sys_frame)

        # Enable/Disable Tab
        toggle_frame = tk.Frame(nb, bg=COLORS['bg'])
        nb.add(toggle_frame, text='🔛 Enable/Disable')
        self._build_toggle(toggle_frame)

        # Unlock Files Tab
        unlock_frame = tk.Frame(nb, bg=COLORS['bg'])
        nb.add(unlock_frame, text='🔓 Unlock Files')
        self._build_unlock(unlock_frame)

        # Quick Registry Tab
        reg_frame = tk.Frame(nb, bg=COLORS['bg'])
        nb.add(reg_frame, text='📝 Registry Tweaks')
        self._build_registry(reg_frame)

    def _build_system_tools(self, parent):
        tools = [
            ('📋 Task Manager', 'taskmgr.exe', COLORS['info']),
            ('⌨️ Command Prompt (Admin)', 'cmd_admin', COLORS['text']),
            ('💡 PowerShell (Admin)', 'ps_admin', '#8E44AD'),
            ('📝 Registry Editor', 'regedit.exe', '#E74C3C'),
            ('⚙️ System Configuration', 'msconfig.exe', '#F39C12'),
            ('💻 Device Manager', 'devmgmt.msc', '#27AE60'),
            ('💿 Disk Management', 'diskmgmt.msc', '#2980B9'),
            ('⚡ Event Viewer', 'eventvwr.msc', '#D35400'),
            ('🔧 Services', 'services.msc', '#16A085'),
            ('🖥️ System Info', 'msinfo32.exe', '#8E44AD'),
            ('🔤 Environment Vars', 'env_vars', '#2980B9'),
            ('🗂️ Folder Options', 'control folders', COLORS['warning']),
            ('🖨️ Control Panel', 'control.exe', COLORS['info']),
            ('🔍 Resource Monitor', 'resmon.exe', '#E74C3C'),
            ('📊 Performance Monitor', 'perfmon.exe', '#27AE60'),
            ('🌐 Network Connections', 'ncpa.cpl', '#2980B9'),
            ('🔒 Local Security Policy', 'secpol.msc', '#E74C3C'),
            ('👥 Computer Management', 'compmgmt.msc', '#8E44AD'),
        ]
        frame = tk.Frame(parent, bg=COLORS['bg'])
        frame.pack(fill='both', expand=True, padx=15, pady=10)

        row, col = 0, 0
        for name, cmd, color in tools:
            def make_cmd(c):
                if c == 'cmd_admin':
                    return lambda: subprocess.Popen(
                        ['powershell', 'Start-Process', 'cmd', '-Verb', 'RunAs'])
                elif c == 'ps_admin':
                    return lambda: subprocess.Popen(
                        ['powershell', 'Start-Process', 'powershell', '-Verb', 'RunAs'])
                elif c == 'env_vars':
                    return lambda: subprocess.Popen(
                        ['rundll32', 'sysdm.cpl,EditEnvironmentVariables'])
                else:
                    return lambda cmd=c: subprocess.Popen(cmd.split(), shell=True)

            btn = tk.Button(frame, text=name, font=FONTS['normal'],
                             bg=COLORS['btn_bg'], fg=COLORS['text'],
                             activebackground=color, activeforeground='white',
                             relief='groove', padx=10, pady=6,
                             anchor='w', cursor='hand2',
                             command=make_cmd(cmd))
            btn.grid(row=row, column=col, padx=4, pady=3, sticky='ew')

            def on_enter(e, b=btn, c=color):
                b.configure(bg=c, fg='white')
            def on_leave(e, b=btn):
                b.configure(bg=COLORS['btn_bg'], fg=COLORS['text'])
            btn.bind('<Enter>', on_enter)
            btn.bind('<Leave>', on_leave)

            col += 1
            if col >= 2:
                col = 0
                row += 1

        for c in range(2):
            frame.columnconfigure(c, weight=1)

    def _build_toggle(self, parent):
        toggles = [
            ('📷 Camera', 'camera'),
            ('📋 Task Manager', 'taskmgr'),
            ('⌨️ Command Prompt', 'cmd'),
            ('📝 Registry Editor', 'registry'),
            ('▶️ Run Dialog', 'run'),
            ('🚀 AutoRun', 'autorun'),
            ('🔍 Windows Search', 'search'),
            ('📰 News Feed', 'news'),
            ('🎮 Xbox Game Bar', 'gamebar'),
            ('🪟 Cortana', 'cortana'),
        ]
        frame = tk.Frame(parent, bg=COLORS['bg'])
        frame.pack(fill='both', expand=True, padx=15, pady=10)

        tk.Label(frame, text='Enable / Disable Windows Features',
                  font=FONTS['subtitle'], bg=COLORS['bg'],
                  fg=COLORS['text']).pack(pady=10)

        for name, key in toggles:
            row = tk.Frame(frame, bg=COLORS['bg'], relief='groove', bd=1)
            row.pack(fill='x', pady=2)

            tk.Label(row, text=name, font=FONTS['normal'],
                      bg=COLORS['bg'], width=25, anchor='w').pack(
                side='left', padx=15, pady=5)

            tk.Button(row, text='✅ Enable', font=FONTS['small'],
                       bg=COLORS['accent'], fg='white', relief='flat',
                       padx=10, pady=3, cursor='hand2',
                       command=lambda k=key: self.toggle_feature(k, True)
                       ).pack(side='left', padx=5, pady=3)
            tk.Button(row, text='🚫 Disable', font=FONTS['small'],
                       bg=COLORS['danger'], fg='white', relief='flat',
                       padx=10, pady=3, cursor='hand2',
                       command=lambda k=key: self.toggle_feature(k, False)
                       ).pack(side='left', padx=3)

    def _build_unlock(self, parent):
        tk.Label(parent, text='🔓 Unlock / Force Delete Files',
                  font=FONTS['subtitle'], bg=COLORS['bg'],
                  fg=COLORS['text'], pady=10).pack()

        # File selector
        row = tk.Frame(parent, bg=COLORS['bg'])
        row.pack(fill='x', padx=15, pady=5)
        tk.Label(row, text='File/Folder:', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left', padx=5)
        self.unlock_path = tk.StringVar()
        tk.Entry(row, textvariable=self.unlock_path,
                  font=FONTS['normal'], width=45).pack(side='left', padx=3)
        tk.Button(row, text='📂', font=FONTS['normal'],
                   bg=COLORS['info'], fg='white', relief='flat', cursor='hand2',
                   command=lambda: self.unlock_path.set(
                       filedialog.askopenfilename() or
                       filedialog.askdirectory() or
                       self.unlock_path.get()
                   )).pack(side='left', padx=3)

        btn_row = tk.Frame(parent, bg=COLORS['bg'])
        btn_row.pack(pady=8)
        for text, cmd, color in [
            ('🔓 Unlock File', self.unlock_file, COLORS['accent']),
            ('🗑️ Force Delete', self.force_delete, COLORS['danger']),
            ('📋 Who Locks?', self.check_lock, COLORS['info']),
            ('⚡ Kill Process', self.kill_process, '#8E44AD'),
        ]:
            tk.Button(btn_row, text=text, font=FONTS['normal'],
                       bg=color, fg='white', relief='flat',
                       padx=12, pady=6, cursor='hand2',
                       command=cmd).pack(side='left', padx=5)

        # Output
        tk.Label(parent, text='Output:', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(anchor='w', padx=15)
        self.unlock_output = tk.Text(parent, font=FONTS['mono'],
                                      bg='#1E1E1E', fg='#D4D4D4',
                                      height=12, relief='flat',
                                      padx=10, pady=5)
        self.unlock_output.pack(fill='both', expand=True, padx=15, pady=5)

    def _build_registry(self, parent):
        tweaks = [
            ('🖱️ Disable Right-click Ads', 'disable_rcads'),
            ('⚡ Boot faster (Num Processes)', 'fast_boot'),
            ('📁 Show Extensions', 'show_ext'),
            ('🔒 Disable Lock Screen', 'disable_lock'),
            ('🎨 Dark Mode', 'dark_mode'),
            ('💡 Light Mode', 'light_mode'),
            ('🔎 Classic Search', 'classic_search'),
            ('📌 Disable Sticky Keys', 'disable_sticky'),
            ('🏃 Faster Shutdown', 'fast_shutdown'),
            ('🔔 Disable Notifications', 'disable_notif'),
        ]
        frame = tk.Frame(parent, bg=COLORS['bg'])
        frame.pack(fill='both', expand=True, padx=15, pady=10)

        tk.Label(frame, text='Registry Tweaks (Apply with caution)',
                  font=FONTS['subtitle'], bg=COLORS['bg'],
                  fg=COLORS['warning']).pack(pady=5)

        for name, key in tweaks:
            row = tk.Frame(frame, bg=COLORS['bg'], relief='groove', bd=1)
            row.pack(fill='x', pady=2)
            tk.Label(row, text=name, font=FONTS['normal'],
                      bg=COLORS['bg'], width=35, anchor='w').pack(
                side='left', padx=15, pady=5)
            tk.Button(row, text='Apply', font=FONTS['small'],
                       bg=COLORS['accent'], fg='white', relief='flat',
                       padx=10, pady=3, cursor='hand2',
                       command=lambda k=key: self.apply_tweak(k)
                       ).pack(side='right', padx=10)

    def toggle_feature(self, feature, enable):
        try:
            if feature == 'camera':
                value = 'Allow' if enable else 'Deny'
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                      CAM_REG, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, 'Value', 0, winreg.REG_SZ, value)
                winreg.CloseKey(key)
                messagebox.showinfo('Camera',
                                     f'Camera: {"✅ Enabled" if enable else "🚫 Disabled"}')

            elif feature == 'taskmgr':
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                      r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System',
                                      0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, 'DisableTaskMgr', 0, winreg.REG_DWORD,
                                   0 if enable else 1)
                winreg.CloseKey(key)
                messagebox.showinfo('TaskMgr',
                                     f'Task Manager: {"✅ Enabled" if enable else "🚫 Disabled"}')

            elif feature == 'cmd':
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                      r'SOFTWARE\Policies\Microsoft\Windows\System',
                                      0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, 'DisableCMD', 0, winreg.REG_DWORD,
                                   0 if enable else 1)
                winreg.CloseKey(key)

            elif feature == 'registry':
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                      r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System',
                                      0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, 'DisableRegistryTools', 0, winreg.REG_DWORD,
                                   0 if enable else 1)
                winreg.CloseKey(key)

            elif feature == 'run':
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                      r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer',
                                      0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, 'NoRun', 0, winreg.REG_DWORD,
                                   0 if enable else 1)
                winreg.CloseKey(key)

            elif feature == 'autorun':
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                      r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer',
                                      0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, 'NoDriveTypeAutoRun', 0, winreg.REG_DWORD,
                                   0x91 if enable else 0xFF)
                winreg.CloseKey(key)

            else:
                messagebox.showinfo('Info',
                                     f'{feature}: {"✅ Enabled" if enable else "🚫 Disabled"}')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def unlock_file(self):
        path = self.unlock_path.get().strip()
        if not path:
            messagebox.showwarning('Warning', 'Chọn file/folder!')
            return
        # Try to release lock using PowerShell
        self.unlock_output.configure(state='normal')
        self.unlock_output.delete('1.0', 'end')
        result = subprocess.run(
            ['powershell', '-Command',
             f'$handle = [System.IO.FileStream]::new("{path}", [System.IO.FileMode]::Open); '
             f'$handle.Close(); "Unlocked successfully"'],
            capture_output=True, text=True
        )
        self.unlock_output.insert('1.0', result.stdout + result.stderr)
        self.unlock_output.configure(state='disabled')

    def force_delete(self):
        path = self.unlock_path.get().strip()
        if not path:
            messagebox.showwarning('Warning', 'Chọn file/folder!')
            return
        if not messagebox.askyesno('⚠️ Confirm',
                                    f'Force delete:\n{path}\n\nKhông thể hoàn tác!'):
            return
        self.unlock_output.configure(state='normal')
        self.unlock_output.delete('1.0', 'end')
        # Try multiple methods
        methods = [
            ['del', '/f', '/q', path],
            ['rd', '/s', '/q', path],
            ['powershell', '-Command', f'Remove-Item -Path "{path}" -Force -Recurse'],
        ]
        for method in methods:
            result = subprocess.run(method, capture_output=True, text=True,
                                     shell=(method[0] in ('del', 'rd')))
            if result.returncode == 0:
                self.unlock_output.insert('end', f'✅ Deleted with: {" ".join(method[:2])}\n')
                break
            else:
                self.unlock_output.insert('end', f'❌ Failed: {result.stderr}\n')
        self.unlock_output.configure(state='disabled')

    def check_lock(self):
        path = self.unlock_path.get().strip()
        if not path:
            messagebox.showwarning('Warning', 'Chọn file!')
            return
        self.unlock_output.configure(state='normal')
        self.unlock_output.delete('1.0', 'end')
        result = subprocess.run(
            ['powershell', '-Command',
             f'$lockingProcs = @(); '
             f'Get-Process | ForEach-Object {{ '
             f'  $proc = $_; '
             f'  $proc.Modules | ForEach-Object {{ '
             f'    if ($_.FileName -like "*{os.path.basename(path)}*") {{ '
             f'      $lockingProcs += "$($proc.Name) (PID: $($proc.Id))" '
             f'    }} '
             f'  }} '
             f'}}; '
             f'if ($lockingProcs) {{ $lockingProcs }} else {{ "No locking process found" }}'],
            capture_output=True, text=True, timeout=15
        )
        self.unlock_output.insert('1.0', result.stdout or 'Check complete\n')
        self.unlock_output.configure(state='disabled')

    def kill_process(self):
        dlg = tk.Toplevel(self.parent)
        dlg.title('Kill Process')
        dlg.geometry('400x120')
        dlg.configure(bg=COLORS['bg'])
        dlg.grab_set()

        row = tk.Frame(dlg, bg=COLORS['bg'])
        row.pack(padx=15, pady=15)
        tk.Label(row, text='Process name or PID:', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left', padx=5)
        proc_var = tk.StringVar()
        tk.Entry(row, textvariable=proc_var, font=FONTS['normal'],
                  width=20).pack(side='left', padx=5)

        def do_kill():
            proc = proc_var.get().strip()
            if proc:
                if proc.isdigit():
                    subprocess.run(['taskkill', '/f', '/pid', proc])
                else:
                    subprocess.run(['taskkill', '/f', '/im', proc])
                dlg.destroy()

        tk.Button(dlg, text='Kill', bg=COLORS['danger'], fg='white',
                   relief='flat', padx=15, cursor='hand2',
                   command=do_kill).pack(pady=5)

    def apply_tweak(self, tweak):
        tweaks_map = {
            'show_ext': lambda: self._reg_set(
                winreg.HKEY_CURRENT_USER,
                r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced',
                'HideFileExt', winreg.REG_DWORD, 0),
            'fast_shutdown': lambda: self._reg_set(
                winreg.HKEY_LOCAL_MACHINE,
                r'SYSTEM\CurrentControlSet\Control',
                'WaitToKillServiceTimeout', winreg.REG_SZ, '2000'),
            'dark_mode': lambda: self._reg_set(
                winreg.HKEY_CURRENT_USER,
                r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize',
                'AppsUseLightTheme', winreg.REG_DWORD, 0),
            'light_mode': lambda: self._reg_set(
                winreg.HKEY_CURRENT_USER,
                r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize',
                'AppsUseLightTheme', winreg.REG_DWORD, 1),
            'disable_sticky': lambda: self._reg_set(
                winreg.HKEY_CURRENT_USER,
                r'Control Panel\Accessibility\StickyKeys',
                'Flags', winreg.REG_SZ, '506'),
        }
        if tweak in tweaks_map:
            try:
                tweaks_map[tweak]()
                messagebox.showinfo('Applied', f'✅ Tweak applied: {tweak}')
            except Exception as e:
                messagebox.showerror('Error', str(e))
        else:
            messagebox.showinfo('Info', f'Tweak "{tweak}" - applying...')

    def _reg_set(self, hive, path, name, reg_type, value):
        key = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, name, 0, reg_type, value)
        winreg.CloseKey(key)
