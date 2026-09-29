"""
Classic Menu Module - Windows 10/11 Classic Context Menu
"""
import tkinter as tk
from tkinter import messagebox
import subprocess
import winreg
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS


class ClassicMenu:
    def __init__(self, parent):
        self.parent = parent
        self.parent.geometry('550x400')
        self.parent.configure(bg=COLORS['bg'])
        self.setup_ui()
        self.check_status()

    def setup_ui(self):
        hdr = tk.Frame(self.parent, bg=COLORS['bg_header'])
        hdr.pack(fill='x')
        tk.Label(hdr, text='🪟  Classic Context Menu', font=FONTS['large'],
                  bg=COLORS['bg_header'], fg='white', pady=10).pack(side='left', padx=15)

        # Status
        status_frame = tk.Frame(self.parent, bg=COLORS['bg'], pady=20)
        status_frame.pack(fill='x')
        tk.Label(status_frame, text='Current Status:', font=FONTS['subtitle'],
                  bg=COLORS['bg']).pack()
        self.status_var = tk.StringVar(value='Checking...')
        tk.Label(status_frame, textvariable=self.status_var,
                  font=('Segoe UI', 14, 'bold'), bg=COLORS['bg'],
                  fg=COLORS['accent']).pack(pady=5)

        # Buttons
        btn_frame = tk.Frame(self.parent, bg=COLORS['bg'])
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text='🔙 Enable Classic Menu (Win10 style)',
                   font=FONTS['subtitle'], bg=COLORS['accent'], fg='white',
                   relief='flat', padx=20, pady=10, cursor='hand2',
                   command=self.enable_classic).pack(pady=8)
        tk.Button(btn_frame, text='🆕 Use New Win11 Menu',
                   font=FONTS['subtitle'], bg=COLORS['info'], fg='white',
                   relief='flat', padx=20, pady=10, cursor='hand2',
                   command=self.disable_classic).pack(pady=8)
        tk.Button(btn_frame, text='🔄 Restart Explorer',
                   font=FONTS['subtitle'], bg=COLORS['warning'], fg='white',
                   relief='flat', padx=20, pady=10, cursor='hand2',
                   command=self.restart_explorer).pack(pady=8)

        note = tk.Label(self.parent,
                         text='Note: Requires explorer restart to take effect',
                         font=FONTS['small'], bg=COLORS['bg'], fg=COLORS['text_light'])
        note.pack()

    def check_status(self):
        reg_path = r'Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32'
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path)
            winreg.CloseKey(key)
            self.status_var.set('✅ Classic Menu (Win10 style) - Active')
        except:
            self.status_var.set('🆕 New Win11 Context Menu - Active')

    def enable_classic(self):
        try:
            reg_path = r'Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32'
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)
            winreg.SetValueEx(key, '', 0, winreg.REG_SZ, '')
            winreg.CloseKey(key)
            self.status_var.set('✅ Classic Menu Enabled')
            if messagebox.askyesno('Restart', 'Khởi động lại Explorer để áp dụng?'):
                self.restart_explorer()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def disable_classic(self):
        try:
            reg_path = r'Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}'
            subprocess.run(['reg', 'delete',
                             f'HKCU\\{reg_path}', '/f'], capture_output=True)
            self.status_var.set('🆕 New Win11 Menu Active')
            if messagebox.askyesno('Restart', 'Khởi động lại Explorer?'):
                self.restart_explorer()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def restart_explorer(self):
        subprocess.run(['taskkill', '/f', '/im', 'explorer.exe'], capture_output=True)
        import time
        time.sleep(1)
        subprocess.Popen(['explorer.exe'])
        messagebox.showinfo('Done', '✅ Explorer đã restart!')
