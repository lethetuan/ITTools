"""
Office Optimization Module
Turn off Spell, Grammar, Protected view
"""
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import winreg
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS


# Office registry paths for common versions
OFFICE_VERSIONS = {
    'Office 2016/2019/365': '16.0',
    'Office 2013': '15.0',
    'Office 2010': '14.0',
}
OFFICE_APPS = ['Word', 'Excel', 'PowerPoint', 'Outlook']


class OfficeOptimization:
    def __init__(self, parent):
        self.parent = parent
        self.parent.geometry('680x550')
        self.parent.configure(bg=COLORS['bg'])
        self.setup_ui()

    def setup_ui(self):
        hdr = tk.Frame(self.parent, bg=COLORS['bg_header'])
        hdr.pack(fill='x')
        tk.Label(hdr, text='📊  Office Optimization', font=FONTS['large'],
                  bg=COLORS['bg_header'], fg='white', pady=10).pack(side='left', padx=15)

        # Version selection
        ver_frame = tk.Frame(self.parent, bg=COLORS['bg'])
        ver_frame.pack(fill='x', padx=15, pady=8)
        tk.Label(ver_frame, text='Office Version:', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left', padx=5)
        self.version_var = tk.StringVar(value='16.0')
        for name, ver in OFFICE_VERSIONS.items():
            tk.Radiobutton(ver_frame, text=name, value=ver,
                            variable=self.version_var,
                            font=FONTS['normal'], bg=COLORS['bg'],
                            selectcolor=COLORS['selected'],
                            cursor='hand2').pack(side='left', padx=10)

        # Notebook for apps
        nb = ttk.Notebook(self.parent)
        nb.pack(fill='both', expand=True, padx=8, pady=5)

        app_map = {
            'Word': 'Microsoft\\Office\\{ver}\\Word\\Options',
            'Excel': 'Microsoft\\Office\\{ver}\\Excel\\Options',
            'PowerPoint': 'Microsoft\\Office\\{ver}\\PowerPoint\\Options',
            'Outlook': 'Microsoft\\Office\\{ver}\\Outlook\\Options\\Mail',
        }
        for app_name in OFFICE_APPS:
            frame = tk.Frame(nb, bg=COLORS['bg'])
            nb.add(frame, text=f'  {app_name}  ')
            self._build_app_tab(frame, app_name)

        # Apply all button
        btn_frame = tk.Frame(self.parent, bg=COLORS['bg'])
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text='⚡ Apply All Optimizations (All Apps)',
                   font=FONTS['subtitle'], bg=COLORS['accent'], fg='white',
                   relief='flat', padx=20, pady=8, cursor='hand2',
                   command=self.apply_all).pack(side='left', padx=5)
        tk.Button(btn_frame, text='🔄 Reset to Default',
                   font=FONTS['subtitle'], bg=COLORS['danger'], fg='white',
                   relief='flat', padx=20, pady=8, cursor='hand2',
                   command=self.reset_all).pack(side='left', padx=5)

    def _build_app_tab(self, parent, app_name):
        opts = [
            ('Spell Check', 'NoSpellCheck', 1),
            ('Grammar Check', 'NoGrammarCheck', 1),
            ('AutoCorrect', 'NoAutoCorrect', 1),
            ('Protected View - Internet', 'DisableInternetFilesInPV', 1),
            ('Protected View - Attachment', 'DisableAttachmentsInPV', 1),
            ('Protected View - Unsafe', 'DisableUnsafeLocationsInPV', 1),
            ('Read Only Recommendation', 'NoReadOnlyRecommend', 1),
            ('Document Recovery', 'NoAutoRecover', 0),
            ('Mini Toolbar', 'DisableMiniToolbar', 1),
            ('Animation', 'DisableAnimations', 1),
            ('Hardware Acceleration', 'DisableHardwareAcceleration', 0),
        ]
        frame = tk.LabelFrame(parent, text=f'  {app_name} Optimizations  ',
                               font=FONTS['subtitle'], bg=COLORS['bg'])
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        vars_dict = {}
        for i, (label, key, default_disable) in enumerate(opts):
            row = i // 2
            col = i % 2

            f = tk.Frame(frame, bg=COLORS['bg'])
            f.grid(row=row, column=col, padx=10, pady=4, sticky='w')

            var = tk.BooleanVar(value=True)
            vars_dict[key] = var
            tk.Checkbutton(f, text=f'Disable {label}', variable=var,
                            font=FONTS['normal'], bg=COLORS['bg'],
                            selectcolor=COLORS['selected'],
                            cursor='hand2').pack(anchor='w')

        for c in range(2):
            frame.columnconfigure(c, weight=1)

        # Buttons
        btn = tk.Frame(parent, bg=COLORS['bg'])
        btn.pack(pady=5)
        tk.Button(btn, text=f'✅ Apply {app_name}',
                   font=FONTS['subtitle'], bg=COLORS['accent'], fg='white',
                   relief='flat', padx=15, pady=6, cursor='hand2',
                   command=lambda a=app_name, v=vars_dict: self.apply_app(a, v)
                   ).pack(side='left', padx=5)

    def _get_reg_path(self, app_name):
        ver = self.version_var.get()
        paths = {
            'Word': f'Software\\Microsoft\\Office\\{ver}\\Word',
            'Excel': f'Software\\Microsoft\\Office\\{ver}\\Excel',
            'PowerPoint': f'Software\\Microsoft\\Office\\{ver}\\PowerPoint',
            'Outlook': f'Software\\Microsoft\\Office\\{ver}\\Outlook',
        }
        return paths.get(app_name, '')

    def apply_app(self, app_name, vars_dict):
        base_path = self._get_reg_path(app_name)
        success = 0
        for key, var in vars_dict.items():
            if var.get():
                try:
                    full_path = base_path + '\\Options'
                    reg_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, full_path)
                    winreg.SetValueEx(reg_key, key, 0, winreg.REG_DWORD, 1)
                    winreg.CloseKey(reg_key)
                    success += 1
                except:
                    pass
        messagebox.showinfo('Applied', f'✅ Applied {success} optimizations for {app_name}')

    def apply_all(self):
        for app in OFFICE_APPS:
            base_path = self._get_reg_path(app)
            try:
                # Disable spell/grammar/protected view
                settings = {
                    'NoSpellCheck': 1,
                    'DisableInternetFilesInPV': 1,
                    'DisableAttachmentsInPV': 1,
                    'DisableUnsafeLocationsInPV': 1,
                }
                for k, v in settings.items():
                    try:
                        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                                base_path + '\\Options')
                        winreg.SetValueEx(key, k, 0, winreg.REG_DWORD, v)
                        winreg.CloseKey(key)
                    except:
                        pass
            except:
                pass
        messagebox.showinfo('Done', '✅ All Office optimizations applied!')

    def reset_all(self):
        if messagebox.askyesno('Reset', 'Reset all Office settings to default?'):
            for app in OFFICE_APPS:
                base_path = self._get_reg_path(app)
                try:
                    subprocess.run(['reg', 'delete',
                                     f'HKCU\\{base_path}\\Options', '/f'],
                                    capture_output=True)
                except:
                    pass
            messagebox.showinfo('Reset', '✅ Office settings reset!')
