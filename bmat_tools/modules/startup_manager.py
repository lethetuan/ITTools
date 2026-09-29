"""
Startup Manager Module
Manages startup entries from HKCU, HKLM, RunOnce, User folder, Common folder
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import winreg
import os
import sys
import shutil
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS, STARTUP_PATHS


class StartupManager:
    def __init__(self, parent):
        self.parent = parent
        self.current_tab = 'HKCU'
        self.setup_ui()
        self.load_entries('HKCU')

    def setup_ui(self):
        # Sub-tab bar
        tab_frame = tk.Frame(self.parent, bg=COLORS['bg_dark'])
        tab_frame.pack(fill='x', padx=0, pady=0)

        self.tabs = {}
        tab_names = ['HKCU', 'HKLM', 'User', 'Common', 'RunOnce', 'Read All']
        colors = ['#2980B9', '#8E44AD', '#27AE60', '#D35400', '#C0392B', '#16A085']
        for i, (name, color) in enumerate(zip(tab_names, colors)):
            btn = tk.Button(tab_frame, text=name, font=FONTS['small'],
                             bg=COLORS['tab_inactive'], fg=COLORS['text'],
                             relief='flat', padx=10, pady=4,
                             cursor='hand2',
                             command=lambda n=name: self.switch_tab(n))
            btn.pack(side='left', padx=1, pady=2)
            self.tabs[name] = (btn, color)

        # Treeview
        tree_frame = tk.Frame(self.parent, bg=COLORS['bg'])
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)

        cols = ('Name', 'Path', 'Status')
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings',
                                  selectmode='browse')
        self.tree.heading('Name', text='Name', anchor='w')
        self.tree.heading('Path', text='Path', anchor='w')
        self.tree.heading('Status', text='Status', anchor='center')
        self.tree.column('Name', width=160, minwidth=100)
        self.tree.column('Path', width=380, minwidth=200)
        self.tree.column('Status', width=80, minwidth=60)

        vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.tree.pack(fill='both', expand=True)

        # Tag colors
        self.tree.tag_configure('enabled', foreground='#000000')
        self.tree.tag_configure('disabled', foreground='#AAAAAA')
        self.tree.tag_configure('selected_row', background=COLORS['selected'])

        # Context menu
        self.context_menu = tk.Menu(self.parent, tearoff=0)
        self.context_menu.add_command(label='➕ Add New...', command=self.add_entry)
        self.context_menu.add_command(label='📂 Browse...', command=self.browse_entry)
        self.context_menu.add_command(label='✏️ Edit...', command=self.edit_entry)
        self.context_menu.add_command(label='❌ Delete', command=self.delete_entry)
        self.context_menu.add_separator()
        self.context_menu.add_command(label='🔄 Refresh', command=self.refresh)
        self.context_menu.add_command(label='▶️ Run Now', command=self.run_entry)
        self.context_menu.add_separator()

        # Move to submenu
        move_menu = tk.Menu(self.context_menu, tearoff=0)
        for dest in ['HKCU (User)', 'HKLM (Machine)', 'User (Folder)',
                      'Common (Folder)', 'RunOnce (User)', 'RunOnce (Machine)']:
            move_menu.add_command(label=dest,
                                   command=lambda d=dest: self.move_entry(d))
        self.context_menu.add_cascade(label='➡️ Move to...', menu=move_menu)
        self.tree.bind('<Button-3>', self.show_context_menu)
        self.tree.bind('<Double-1>', lambda e: self.edit_entry())

        # Checkbox toggle enable/disable via click on Name
        self.tree.bind('<Button-1>', self.toggle_enable)

        # Bottom buttons
        btn_bar = tk.Frame(self.parent, bg=COLORS['bg'])
        btn_bar.pack(fill='x', padx=5, pady=3)

        for text, cmd, color in [
            ('➕ Add', self.add_entry, COLORS['accent']),
            ('✏️ Edit', self.edit_entry, COLORS['info']),
            ('❌ Delete', self.delete_entry, COLORS['danger']),
            ('🔄 Refresh', self.refresh, COLORS['warning']),
            ('▶️ Run', self.run_entry, '#8E44AD'),
        ]:
            tk.Button(btn_bar, text=text, font=FONTS['small'],
                       bg=color, fg='white', relief='flat',
                       padx=8, pady=4, cursor='hand2',
                       command=cmd).pack(side='left', padx=2)

    def switch_tab(self, name):
        self.current_tab = name
        # Update button appearance
        for tab_name, (btn, color) in self.tabs.items():
            if tab_name == name:
                btn.configure(bg=color, fg='white')
            else:
                btn.configure(bg=COLORS['tab_inactive'], fg=COLORS['text'])
        if name == 'Read All':
            self.load_all()
        else:
            self.load_entries(name)

    def _read_registry(self, hive, path):
        entries = []
        try:
            key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    entries.append((name, value, 'Enabled'))
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception as e:
            pass
        return entries

    def _read_folder(self, folder_path):
        entries = []
        if os.path.exists(folder_path):
            for f in os.listdir(folder_path):
                full = os.path.join(folder_path, f)
                entries.append((f, full, 'Enabled'))
        return entries

    def load_entries(self, tab):
        self.tree.delete(*self.tree.get_children())
        entries = []
        if tab == 'HKCU':
            entries = self._read_registry(winreg.HKEY_CURRENT_USER,
                                           STARTUP_PATHS['HKCU'])
        elif tab == 'HKLM':
            entries = self._read_registry(winreg.HKEY_LOCAL_MACHINE,
                                           STARTUP_PATHS['HKLM'])
        elif tab == 'RunOnce':
            entries = (
                self._read_registry(winreg.HKEY_CURRENT_USER, STARTUP_PATHS['HKCU_RunOnce']) +
                self._read_registry(winreg.HKEY_LOCAL_MACHINE, STARTUP_PATHS['HKLM_RunOnce'])
            )
        elif tab == 'User':
            entries = self._read_folder(STARTUP_PATHS['User'])
        elif tab == 'Common':
            entries = self._read_folder(STARTUP_PATHS['Common'])

        for name, path, status in entries:
            tag = 'enabled' if status == 'Enabled' else 'disabled'
            short_path = path if len(path) < 60 else path[:57] + '...'
            self.tree.insert('', 'end', values=(
                f'☑ {name}', short_path, status
            ), tags=(tag,))
            self.tree.item(self.tree.get_children()[-1], tags=(tag,))

    def load_all(self):
        self.tree.delete(*self.tree.get_children())
        all_entries = []
        all_entries += [('HKCU - ' + n, p, s) for n, p, s in
                         self._read_registry(winreg.HKEY_CURRENT_USER, STARTUP_PATHS['HKCU'])]
        all_entries += [('HKLM - ' + n, p, s) for n, p, s in
                         self._read_registry(winreg.HKEY_LOCAL_MACHINE, STARTUP_PATHS['HKLM'])]
        all_entries += [('User - ' + n, p, s) for n, p, s in
                         self._read_folder(STARTUP_PATHS['User'])]
        all_entries += [('Common - ' + n, p, s) for n, p, s in
                         self._read_folder(STARTUP_PATHS['Common'])]
        for name, path, status in all_entries:
            self.tree.insert('', 'end', values=(f'☑ {name}', path, status))

    def refresh(self):
        self.load_entries(self.current_tab)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
        self.context_menu.post(event.x_root, event.y_root)

    def toggle_enable(self, event):
        pass  # Toggle enable/disable functionality

    def get_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('Warning', 'Chọn một mục!')
            return None
        return self.tree.item(sel[0], 'values')

    def add_entry(self):
        self._show_entry_dialog('Add New Entry')

    def edit_entry(self):
        vals = self.get_selected()
        if vals:
            name = vals[0].replace('☑ ', '').replace('☐ ', '')
            path = vals[1]
            self._show_entry_dialog('Edit Entry', name, path)

    def _show_entry_dialog(self, title, name='', path=''):
        dlg = tk.Toplevel(self.parent)
        dlg.title(title)
        dlg.geometry('500x180')
        dlg.configure(bg=COLORS['bg'])
        dlg.grab_set()
        dlg.resizable(False, False)

        tk.Label(dlg, text='Name:', font=FONTS['normal'],
                  bg=COLORS['bg']).grid(row=0, column=0, padx=10, pady=10, sticky='w')
        name_var = tk.StringVar(value=name)
        tk.Entry(dlg, textvariable=name_var, font=FONTS['normal'],
                  width=45).grid(row=0, column=1, columnspan=2, padx=5, pady=10, sticky='ew')

        tk.Label(dlg, text='Path:', font=FONTS['normal'],
                  bg=COLORS['bg']).grid(row=1, column=0, padx=10, pady=5, sticky='w')
        path_var = tk.StringVar(value=path)
        tk.Entry(dlg, textvariable=path_var, font=FONTS['normal'],
                  width=38).grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        tk.Button(dlg, text='...', font=FONTS['small'],
                   bg=COLORS['info'], fg='white', relief='flat',
                   command=lambda: path_var.set(
                       filedialog.askopenfilename(
                           filetypes=[('EXE', '*.exe'), ('All', '*.*')]
                       ) or path_var.get()
                   )).grid(row=1, column=2, padx=5)

        def save():
            n, p = name_var.get().strip(), path_var.get().strip()
            if not n or not p:
                messagebox.showwarning('Warning', 'Điền đầy đủ thông tin!')
                return
            try:
                if self.current_tab == 'HKCU':
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                          STARTUP_PATHS['HKCU'], 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, n, 0, winreg.REG_SZ, p)
                    winreg.CloseKey(key)
                elif self.current_tab == 'HKLM':
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                          STARTUP_PATHS['HKLM'], 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, n, 0, winreg.REG_SZ, p)
                    winreg.CloseKey(key)
                elif self.current_tab in ('User', 'Common'):
                    folder = STARTUP_PATHS[self.current_tab]
                    lnk = os.path.join(folder, n + '.lnk')
                    subprocess.run(['powershell', '-Command',
                                     f'$s=(New-Object -COM WScript.Shell).CreateShortcut("{lnk}"); '
                                     f'$s.TargetPath="{p}"; $s.Save()'])
                messagebox.showinfo('Success', 'Đã lưu thành công!')
                dlg.destroy()
                self.refresh()
            except Exception as e:
                messagebox.showerror('Error', str(e))

        btn_row = tk.Frame(dlg, bg=COLORS['bg'])
        btn_row.grid(row=2, column=0, columnspan=3, pady=15)
        tk.Button(btn_row, text='💾 Save', bg=COLORS['accent'], fg='white',
                   relief='flat', padx=15, pady=5, cursor='hand2',
                   command=save).pack(side='left', padx=5)
        tk.Button(btn_row, text='❌ Cancel', bg=COLORS['danger'], fg='white',
                   relief='flat', padx=15, pady=5, cursor='hand2',
                   command=dlg.destroy).pack(side='left', padx=5)
        dlg.columnconfigure(1, weight=1)

    def delete_entry(self):
        vals = self.get_selected()
        if not vals:
            return
        name = vals[0].replace('☑ ', '').replace('☐ ', '')
        if messagebox.askyesno('Confirm', f'Xóa "{name}"?'):
            try:
                if self.current_tab in ('HKCU',):
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                          STARTUP_PATHS['HKCU'], 0, winreg.KEY_SET_VALUE)
                    winreg.DeleteValue(key, name)
                    winreg.CloseKey(key)
                elif self.current_tab == 'HKLM':
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                          STARTUP_PATHS['HKLM'], 0, winreg.KEY_SET_VALUE)
                    winreg.DeleteValue(key, name)
                    winreg.CloseKey(key)
                elif self.current_tab in ('User', 'Common'):
                    folder = STARTUP_PATHS[self.current_tab]
                    path = vals[1]
                    if os.path.exists(path):
                        os.remove(path)
                self.refresh()
            except Exception as e:
                messagebox.showerror('Error', str(e))

    def browse_entry(self):
        path = filedialog.askopenfilename(
            filetypes=[('EXE', '*.exe'), ('All', '*.*')]
        )
        if path:
            messagebox.showinfo('Path', path)

    def run_entry(self):
        vals = self.get_selected()
        if vals:
            path = vals[1]
            try:
                subprocess.Popen(path)
            except Exception as e:
                messagebox.showerror('Error', str(e))

    def move_entry(self, destination):
        vals = self.get_selected()
        if not vals:
            return
        messagebox.showinfo('Move', f'Di chuyển đến {destination}.\n(Tính năng đang phát triển)')


import ctypes
from ctypes import wintypes
import re
import base64

class GdiplusStartupInput(ctypes.Structure):
    _fields_ = [
        ('GdiplusVersion', ctypes.c_uint32),
        ('DebugEventCallback', ctypes.c_void_p),
        ('SuppressBackgroundThread', ctypes.c_bool),
        ('SuppressExternalCodecs', ctypes.c_bool)
    ]

class SHFILEINFOW(ctypes.Structure):
    _fields_ = [
        ('hIcon', wintypes.HICON),
        ('iIcon', ctypes.c_int),
        ('dwAttributes', wintypes.DWORD),
        ('szDisplayName', wintypes.WCHAR * 260),
        ('szTypeName', wintypes.WCHAR * 80)
    ]

class CLSID(ctypes.Structure):
    _fields_ = [
        ('Data1', ctypes.c_ulong),
        ('Data2', ctypes.c_ushort),
        ('Data3', ctypes.c_ushort),
        ('Data4', ctypes.c_ubyte * 8)
    ]

_icon_ctypes_initialized = False

def _init_icon_extractor_ctypes():
    try:
        shell32 = ctypes.windll.shell32
        user32 = ctypes.windll.user32
        gdiplus = ctypes.windll.gdiplus
        ole32 = ctypes.windll.ole32
        kernel32 = ctypes.windll.kernel32

        shell32.SHGetFileInfoW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(SHFILEINFOW), ctypes.c_uint, ctypes.c_uint]
        shell32.SHGetFileInfoW.restype = ctypes.c_size_t

        user32.DestroyIcon.argtypes = [wintypes.HICON]
        user32.DestroyIcon.restype = wintypes.BOOL

        gdiplus.GdiplusStartup.argtypes = [ctypes.POINTER(ctypes.c_ulonglong), ctypes.c_void_p, ctypes.c_void_p]
        gdiplus.GdiplusStartup.restype = ctypes.c_int

        gdiplus.GdipCreateBitmapFromHICON.argtypes = [wintypes.HICON, ctypes.POINTER(ctypes.c_void_p)]
        gdiplus.GdipCreateBitmapFromHICON.restype = ctypes.c_int

        gdiplus.GdipDisposeImage.argtypes = [ctypes.c_void_p]
        gdiplus.GdipDisposeImage.restype = ctypes.c_int

        gdiplus.GdipSaveImageToStream.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        gdiplus.GdipSaveImageToStream.restype = ctypes.c_int

        gdiplus.GdiplusShutdown.argtypes = [ctypes.c_ulonglong]
        gdiplus.GdiplusShutdown.restype = None

        ole32.CreateStreamOnHGlobal.argtypes = [ctypes.c_void_p, wintypes.BOOL, ctypes.POINTER(ctypes.c_void_p)]
        ole32.CreateStreamOnHGlobal.restype = ctypes.c_long

        ole32.GetHGlobalFromStream.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.HGLOBAL)]
        ole32.GetHGlobalFromStream.restype = ctypes.c_long

        kernel32.GlobalSize.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalSize.restype = ctypes.c_size_t

        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalLock.restype = ctypes.c_void_p

        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalUnlock.restype = wintypes.BOOL
        return True
    except Exception:
        return False

def extract_exe_path(cmd_str):
    if not cmd_str:
        return ""
    clean = cmd_str.strip()
    m = re.match(r'^"([^"]+)"', clean)
    if m:
        return m.group(1)
    
    m2 = re.search(r'([a-zA-Z]:\\[^:\*\?"<>\|]+\.(?:exe|lnk|bat|cmd|com))', clean, re.IGNORECASE)
    if m2 and os.path.exists(m2.group(1)):
        return m2.group(1)
        
    parts = clean.split()
    for i in range(len(parts), 0, -1):
        candidate = " ".join(parts[:i]).strip('"')
        if os.path.exists(candidate):
            return candidate
            
    return clean.strip('"')

ICON_CACHE = {}

def extract_file_icon_base64(file_path):
    global _icon_ctypes_initialized
    clean = extract_exe_path(file_path)
    if not clean or not os.path.exists(clean):
        return ""

    if clean in ICON_CACHE:
        return ICON_CACHE[clean]

    if not _icon_ctypes_initialized:
        if _init_icon_extractor_ctypes():
            _icon_ctypes_initialized = True
        else:
            return ""

    try:
        shell32 = ctypes.windll.shell32
        user32 = ctypes.windll.user32
        gdiplus = ctypes.windll.gdiplus
        ole32 = ctypes.windll.ole32
        kernel32 = ctypes.windll.kernel32

        shfi = SHFILEINFOW()
        res = shell32.SHGetFileInfoW(clean, 0, ctypes.byref(shfi), ctypes.sizeof(shfi), 0x000000100 | 0x000000001)
        if not res or not shfi.hIcon:
            res = shell32.SHGetFileInfoW(clean, 0, ctypes.byref(shfi), ctypes.sizeof(shfi), 0x000000100)
            if not res or not shfi.hIcon:
                ICON_CACHE[clean] = ""
                return ""

        hIcon = shfi.hIcon

        token = ctypes.c_ulonglong(0)
        startup_input = GdiplusStartupInput(1, None, False, False)
        if gdiplus.GdiplusStartup(ctypes.byref(token), ctypes.byref(startup_input), None) != 0:
            user32.DestroyIcon(hIcon)
            ICON_CACHE[clean] = ""
            return ""

        pBitmap = ctypes.c_void_p(0)
        if gdiplus.GdipCreateBitmapFromHICON(hIcon, ctypes.byref(pBitmap)) != 0:
            user32.DestroyIcon(hIcon)
            gdiplus.GdiplusShutdown(token)
            ICON_CACHE[clean] = ""
            return ""

        pStream = ctypes.c_void_p(0)
        ole32.CreateStreamOnHGlobal(None, True, ctypes.byref(pStream))

        png_clsid = CLSID(0x557CF406, 0x1A04, 0x11D3, (ctypes.c_ubyte * 8)(0x9A, 0x73, 0x00, 0x00, 0xF8, 0x1E, 0xF3, 0x2E))
        res_save = gdiplus.GdipSaveImageToStream(pBitmap, pStream, ctypes.byref(png_clsid), None)

        base64_str = ""
        if res_save == 0:
            hGlobal = wintypes.HGLOBAL(0)
            ole32.GetHGlobalFromStream(pStream, ctypes.byref(hGlobal))
            size = kernel32.GlobalSize(hGlobal)
            ptr = kernel32.GlobalLock(hGlobal)
            if ptr and size > 0:
                buf = (ctypes.c_ubyte * size).from_address(ptr)
                bdata = bytes(buf)
                base64_str = "data:image/png;base64," + base64.b64encode(bdata).decode("ascii")
                kernel32.GlobalUnlock(hGlobal)

        gdiplus.GdipDisposeImage(pBitmap)
        gdiplus.GdiplusShutdown(token)
        user32.DestroyIcon(hIcon)

        ICON_CACHE[clean] = base64_str
        return base64_str
    except Exception:
        ICON_CACHE[clean] = ""
        return ""


def get_all_startup_entries():
    """Scans and returns all startup entries from HKCU, HKLM, RunOnce, and Startup Folders."""
    import winreg
    import os

    entries = []

    def scan_reg_key(hive, subkey, location_label):
        try:
            key = winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ)
            disabled_names = set()
            try:
                appr_key_path = subkey.replace(r'\CurrentVersion\Run', r'\CurrentVersion\Explorer\StartupApproved\Run')
                appr_key = winreg.OpenKey(hive, appr_key_path, 0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        n, v, _ = winreg.EnumValue(appr_key, i)
                        if isinstance(v, bytes) and len(v) > 0 and v[0] not in (0, 2):
                            disabled_names.add(n)
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(appr_key)
            except Exception:
                pass

            i = 0
            while True:
                try:
                    name, val, _ = winreg.EnumValue(key, i)
                    is_enabled = name not in disabled_names
                    path_str = str(val)
                    entries.append({
                        "name": name,
                        "path": path_str,
                        "location": location_label,
                        "reg_hive": "HKCU" if hive == winreg.HKEY_CURRENT_USER else "HKLM",
                        "reg_path": subkey,
                        "is_enabled": is_enabled,
                        "status": "Enable" if is_enabled else "Disabled",
                        "type": "registry",
                        "icon": extract_file_icon_base64(path_str)
                    })
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception:
            pass

    scan_reg_key(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 'HKCU\\Run')
    scan_reg_key(winreg.HKEY_LOCAL_MACHINE, r'Software\Microsoft\Windows\CurrentVersion\Run', 'HKLM\\Run')
    scan_reg_key(winreg.HKEY_LOCAL_MACHINE, r'Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run', 'HKLM\\WOW64Run')
    scan_reg_key(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\RunOnce', 'HKCU\\RunOnce')
    scan_reg_key(winreg.HKEY_LOCAL_MACHINE, r'Software\Microsoft\Windows\CurrentVersion\RunOnce', 'HKLM\\RunOnce')

    # Folders
    user_startup = os.path.expandvars(r'%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup')
    common_startup = os.path.expandvars(r'%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\Startup')

    def scan_folder(folder_path, label):
        if os.path.exists(folder_path):
            for item in os.listdir(folder_path):
                if item.lower() in ('desktop.ini', 'thumbs.db'):
                    continue
                full_path = os.path.join(folder_path, item)
                entries.append({
                    "name": os.path.splitext(item)[0],
                    "path": full_path,
                    "location": label,
                    "reg_hive": "",
                    "reg_path": folder_path,
                    "is_enabled": True,
                    "status": "Enable",
                    "type": "folder",
                    "icon": extract_file_icon_base64(full_path)
                })

    scan_folder(user_startup, 'User Startup')
    scan_folder(common_startup, 'Common Startup')

    return entries


def get_reg_info(location):
    import winreg
    loc = (location or "").upper()
    if "WOW64" in loc:
        return winreg.HKEY_LOCAL_MACHINE, r'Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run'
    elif "HKLM" in loc and "RUNONCE" in loc:
        return winreg.HKEY_LOCAL_MACHINE, r'Software\Microsoft\Windows\CurrentVersion\RunOnce'
    elif "HKLM" in loc:
        return winreg.HKEY_LOCAL_MACHINE, r'Software\Microsoft\Windows\CurrentVersion\Run'
    elif "RUNONCE" in loc:
        return winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\RunOnce'
    else:
        return winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run'


def toggle_startup_status(name, location, enable):
    """Enables or disables a registry startup entry via StartupApproved key."""
    import winreg
    if "HKLM" in (location or ""):
        hive = winreg.HKEY_LOCAL_MACHINE
        appr_path = r'Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run'
    else:
        hive = winreg.HKEY_CURRENT_USER
        appr_path = r'Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run'

    try:
        key = winreg.CreateKey(hive, appr_path)
        if enable:
            data = bytes([0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        else:
            data = bytes([0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        winreg.SetValueEx(key, name, 0, winreg.REG_BINARY, data)
        winreg.CloseKey(key)
        return {"success": True, "message": f"Đã {'bật' if enable else 'tắt'} ứng dụng {name} khởi động!"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def save_startup_entry(name, path, location="HKCU\\Run", old_name=None, old_location=None):
    """Creates or updates a startup entry in Registry or Startup Folder."""
    import winreg
    import os
    import subprocess

    if not name or not path:
        return {"success": False, "message": "Vui lòng nhập đầy đủ Tên (Value Name) và Đường dẫn (Value Data)!"}

    try:
        # Delete old entry if renamed or location changed
        target_old_loc = old_location if old_location else location
        target_old_name = old_name if old_name else name

        if old_name and (old_name != name or old_location != location):
            delete_startup_entry(target_old_name, target_old_loc)

        if "Startup" in location:
            folder = os.path.expandvars(r'%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup')
            if "Common" in location:
                folder = os.path.expandvars(r'%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\Startup')
            lnk_path = os.path.join(folder, f"{name}.lnk")
            ps = f'$s=(New-Object -COM WScript.Shell).CreateShortcut("{lnk_path}"); $s.TargetPath="{path}"; $s.Save()'
            subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
            return {"success": True, "message": f"Đã lưu khoản khởi động: {name}"}
        else:
            hive, reg_path = get_reg_info(location)
            try:
                key = winreg.OpenKey(hive, reg_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, path)
                winreg.CloseKey(key)
                return {"success": True, "message": f"Đã lưu khoản khởi động: {name}"}
            except PermissionError:
                reg_hive_str = "HKLM" if hive == winreg.HKEY_LOCAL_MACHINE else "HKCU"
                cmd = f'Start-Process reg -ArgumentList \'add "{reg_hive_str}\\{reg_path}" /v "{name}" /t REG_SZ /d "{path}" /f\' -Verb RunAs'
                subprocess.run(["powershell", "-NoProfile", "-Command", cmd])
                return {"success": True, "message": f"Đã lưu khoản khởi động: {name}"}

    except Exception as e:
        return {"success": False, "message": str(e)}


def delete_startup_entry(name, location, path=None):
    """Deletes a startup entry from Registry or Startup Folder."""
    import winreg
    import os
    import subprocess

    try:
        if "Startup" in location and path and os.path.exists(path):
            os.remove(path)
            return {"success": True, "message": f"Đã xóa file khởi động: {name}"}

        hive, reg_path = get_reg_info(location)
        try:
            key = winreg.OpenKey(hive, reg_path, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, name)
            winreg.CloseKey(key)
            return {"success": True, "message": f"Đã xóa khoản khởi động: {name}"}
        except PermissionError:
            reg_hive_str = "HKLM" if hive == winreg.HKEY_LOCAL_MACHINE else "HKCU"
            cmd = f'Start-Process reg -ArgumentList \'delete "{reg_hive_str}\\{reg_path}" /v "{name}" /f\' -Verb RunAs'
            subprocess.run(["powershell", "-NoProfile", "-Command", cmd])
            return {"success": True, "message": f"Đã xóa khoản khởi động: {name}"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def run_startup_entry(path):
    """Launches the executable of the specified startup entry."""
    import subprocess
    import os
    if not path:
        return {"success": False, "message": "Không có đường dẫn file!"}
    try:
        clean_exe = extract_exe_path(path)
        if clean_exe and os.path.exists(clean_exe):
            os.startfile(clean_exe)
            return {"success": True, "message": f"Đã chạy ứng dụng: {clean_exe}"}
        
        # Fallback to ShellExecute on raw path
        os.startfile(path.strip('"'))
        return {"success": True, "message": f"Đã chạy ứng dụng: {path}"}
    except Exception:
        try:
            subprocess.Popen(path, shell=True)
            return {"success": True, "message": f"Đã chạy ứng dụng: {path}"}
        except Exception as e:
            return {"success": False, "message": str(e)}


def browse_startup_file():
    """Opens native Windows file dialog to select an executable file."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        path = filedialog.askopenfilename(
            title="Chọn File Thực Thi Khởi Động",
            filetypes=[("Executable Files", "*.exe;*.cmd;*.bat;*.vbs"), ("All Files", "*.*")]
        )
        root.destroy()
        return path or ""
    except Exception:
        return ""

