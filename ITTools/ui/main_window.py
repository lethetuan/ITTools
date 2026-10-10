"""
IT Tool LTT Main Window
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS, APP_NAME, APP_VERSION, APP_AUTHOR, APP_PHONE, APP_WEBSITE, APP_TELEGRAM
from modules.printer_fix import PrinterFix


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.create_styles()
        self.create_layout()

    def setup_window(self):
        self.root.title(f"{APP_NAME} v{APP_VERSION} - {APP_AUTHOR} | Zalo: {APP_PHONE}")
        self.root.geometry("920x720")
        self.root.minsize(750, 580)
        self.root.resizable(True, True)
        self.root.configure(bg=COLORS['bg'])
        # Center window
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'+{x}+{y}')

    def create_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        # Notebook tab style
        self.style.configure('Main.TNotebook', background=COLORS['bg_dark'])
        self.style.configure('Main.TNotebook.Tab',
                              font=FONTS['subtitle'],
                              padding=[10, 5],
                              background=COLORS['tab_inactive'])
        self.style.map('Main.TNotebook.Tab',
                        background=[('selected', COLORS['tab_active'])],
                        foreground=[('selected', COLORS['white'])])
        # Button style
        self.style.configure('Tool.TButton',
                              font=FONTS['normal'],
                              padding=[5, 8],
                              background=COLORS['btn_bg'],
                              relief='raised')
        self.style.map('Tool.TButton',
                        background=[('active', COLORS['btn_hover']),
                                    ('pressed', COLORS['selected'])])

    def create_layout(self):
        # Header
        self.create_header()
        # Main notebook tabs
        self.notebook = ttk.Notebook(self.root, style='Main.TNotebook')
        self.notebook.pack(fill='both', expand=True, padx=5, pady=2)

        # Tab 1: Tools
        self.tools_frame = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.tools_frame, text='  🔧 Tools  ')

        # Tab 2: Fix Print
        self.printer_frame = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.printer_frame, text='  🖨️ Fix Print  ')

        # Tab 3: Startup Manager
        self.startup_frame = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.startup_frame, text='  🚀 Startup Manager  ')

        # Tab 4: Uninstall Manager
        self.uninstall_frame = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.uninstall_frame, text='  🗑 Uninstall Manager  ')

        # Tab 5: History
        self.history_frame = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.history_frame, text='  📋 History  ')

        self.create_tools_tab()
        self.create_printer_tab()
        self.create_startup_tab()
        self.create_uninstall_tab()
        self.create_history_tab()
        self.create_footer()

    def create_header(self):
        header = tk.Frame(self.root, bg=COLORS['bg_header'], height=50)
        header.pack(fill='x', padx=0, pady=0)
        header.pack_propagate(False)

        # Logo/Title
        title_frame = tk.Frame(header, bg=COLORS['bg_header'])
        title_frame.pack(side='left', padx=15, pady=8)

        lbl_icon = tk.Label(title_frame, text='🔧', font=('Segoe UI', 18),
                             bg=COLORS['bg_header'], fg='#F39C12')
        lbl_icon.pack(side='left', padx=(0, 5))

        lbl_title = tk.Label(title_frame, text=APP_NAME,
                              font=('Segoe UI', 14, 'bold'),
                              bg=COLORS['bg_header'], fg=COLORS['white'])
        lbl_title.pack(side='left')

        # Author + contact info on header right side
        info_frame = tk.Frame(header, bg=COLORS['bg_header'])
        info_frame.pack(side='right', padx=15)
        tk.Label(info_frame, text=APP_AUTHOR,
                 font=('Segoe UI', 9, 'bold'),
                 bg=COLORS['bg_header'], fg='#F39C12').pack(anchor='e')
        tk.Label(info_frame, text=f'☎ {APP_PHONE}',
                 font=FONTS['small'],
                 bg=COLORS['bg_header'], fg='#BDC3C7').pack(anchor='e')
        tk.Label(info_frame, text=f'v{APP_VERSION}',
                 font=FONTS['small'],
                 bg=COLORS['bg_header'], fg='#7F8C8D').pack(anchor='e')

    def create_tools_tab(self):
        # Label
        lbl = tk.Label(self.tools_frame, text='Tools Available',
                        font=FONTS['subtitle'],
                        bg=COLORS['bg'], fg=COLORS['text'])
        lbl.pack(anchor='w', padx=10, pady=(8, 2))

        # Author label với link website
        lbl_auth = tk.Label(self.tools_frame,
                             text=f'{APP_AUTHOR}  |  ☎ {APP_PHONE}',
                             font=('Segoe UI', 9, 'bold'),
                             bg=COLORS['bg'], fg=COLORS['green_text'],
                             cursor='hand2')
        lbl_auth.pack(anchor='e', padx=15)
        # Grid frame for tool buttons
        grid_frame = tk.Frame(self.tools_frame, bg=COLORS['bg'])
        grid_frame.pack(fill='both', expand=True, padx=10, pady=5)

        tools = [
            ('🖨️ Fix Print',         self.open_printer_fix,      '#00E5FF'),
            ('⏻ Auto Shutdown',     self.open_auto_shutdown,    '#E74C3C'),
            ('🔑 IP Manager',        self.open_ip_manager,       '#8E44AD'),
            ('📝 Hosts File Editor', self.open_hosts_editor,     '#2980B9'),
            ('💻 Computer Info',     self.open_computer_info,    '#27AE60'),
            ('📤 SendTo Editor',     self.open_sendto_editor,    '#F39C12'),
            ('🪟 Classic Menu',      self.open_classic_menu,     '#16A085'),
            ('🌐 Your IP',           self.open_your_ip,          '#2980B9'),
            ('🖥️ Desktop Icon',      self.open_desktop_icon,     '#8E44AD'),
            ('🔍 IP Scanner',        self.open_ip_scanner,       '#D35400'),
            ('🔒 BitLocker',         self.open_bitlocker,        '#2C3E50'),
            ('🛡️ Firewall Manager',  self.open_firewall,         '#C0392B'),
            ('🕐 Date Time',         self.open_datetime,         '#1ABC9C'),
            ('💾 Backup/Restore Driver', self.open_backup_driver,'#7F8C8D'),
            ('📊 Office Optimization',self.open_office_opt,      '#2980B9'),
            ('🌍 Browser Backup',    self.open_browser_backup,   '#E67E22'),
            ('🔄 Windows Update/Security', self.open_win_update, '#27AE60'),
            ('⚙️ Boot Manager',      self.open_boot_manager,     '#95A5A6'),
            ('⚙️ Services Manager',  self.open_services,         '#8E44AD'),
            ('🖧 Server Tools',      self.open_server_tools,     '#2C3E50'),
            ('📁 Folder Size',       self.open_folder_size,      '#D35400'),
            ('🔧 Other Tools',       self.open_other_tools,      '#7F8C8D'),
            ('💰 Currency',          self.open_currency,         '#F1C40F'),
        ]

        cols = 2
        for i, (text, cmd, color) in enumerate(tools):
            row = i // cols
            col = i % cols
            btn = tk.Button(grid_frame,
                            text=text,
                            font=FONTS['normal'],
                            bg=COLORS['btn_bg'],
                            fg=COLORS['text'],
                            activebackground=COLORS['btn_hover'],
                            activeforeground=COLORS['text'],
                            relief='groove',
                            bd=1,
                            padx=10,
                            pady=6,
                            anchor='w',
                            cursor='hand2',
                            command=cmd)
            btn.grid(row=row, column=col, padx=4, pady=3, sticky='ew')
            # Hover effects
            def on_enter(e, b=btn, c=color):
                b.configure(bg=c, fg='white')
            def on_leave(e, b=btn):
                b.configure(bg=COLORS['btn_bg'], fg=COLORS['text'])
            btn.bind('<Enter>', on_enter)
            btn.bind('<Leave>', on_leave)

        for c in range(cols):
            grid_frame.columnconfigure(c, weight=1)

    def create_printer_tab(self):
        PrinterFix(self.printer_frame)

    def create_startup_tab(self):
        from modules.startup_manager import StartupManager
        StartupManager(self.startup_frame)

    def create_uninstall_tab(self):
        from modules.uninstall_manager import UninstallManager
        UninstallManager(self.uninstall_frame)

    def create_history_tab(self):
        self.history_text = tk.Text(self.history_frame,
                                     font=FONTS['mono'],
                                     bg='#1E1E1E',
                                     fg='#00FF41',
                                     insertbackground='white',
                                     relief='flat',
                                     padx=10, pady=10)
        scrollbar = ttk.Scrollbar(self.history_frame, command=self.history_text.yview)
        self.history_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.history_text.pack(fill='both', expand=True)
        self.history_text.insert('1.0', f'=== {APP_NAME} History Log ===\n\n')
        self.history_text.configure(state='disabled')

    def create_footer(self):
        footer = tk.Frame(self.root, bg=COLORS['bg_dark'], height=40)
        footer.pack(fill='x', side='bottom')
        footer.pack_propagate(False)

        btn_info = tk.Button(footer, text='ℹ️', font=FONTS['icon'],
                              bg=COLORS['info'], fg='white',
                              relief='flat', cursor='hand2', width=3,
                              command=self.show_about)
        btn_info.pack(side='right', padx=(2, 10), pady=5)

        btn_update = tk.Button(footer, text='⬇️', font=FONTS['icon'],
                                bg=COLORS['accent'], fg='white',
                                relief='flat', cursor='hand2', width=3,
                                command=self.check_update)
        btn_update.pack(side='right', padx=2, pady=5)

        # Status label
        self.status_var = tk.StringVar(value='Ready')
        lbl_status = tk.Label(footer, textvariable=self.status_var,
                               font=FONTS['small'],
                               bg=COLORS['bg_dark'], fg=COLORS['text_light'])
        lbl_status.pack(side='left', padx=10)

    def show_about(self):
        import webbrowser
        from tkinter import messagebox
        result = messagebox.askokcancel(
            f'About {APP_NAME}',
            f"{APP_NAME} v{APP_VERSION}\n"
            f"─────────────────────────────\n"
            f"Tác giả  : {APP_AUTHOR}\n"
            f"Điện thoại: {APP_PHONE}\n"
            f"Zalo     : {APP_PHONE}\n"
            f"Website  : {APP_WEBSITE}\n"
            f"Telegram : {APP_TELEGRAM}\n"
            f"─────────────────────────────\n"
            "Windows System Management Utility\n"
            "Built with Python & Tkinter\n\n"
            "Features:\n"
            "• Auto Shutdown/Restart/Hibernate\n"
            "• Startup/Uninstall Manager\n"
            "• IP Scanner & Manager\n"
            "• System Information\n"
            "• And many more...\n\n"
            "[OK] để mở Website",
            icon='info'
        )
        if result:
            webbrowser.open(APP_WEBSITE)

    def check_update(self):
        messagebox.showinfo("Update", "Bạn đang dùng phiên bản mới nhất!")

    def _open_website(self):
        import webbrowser
        webbrowser.open(APP_WEBSITE)

    def log_history(self, msg):
        self.history_text.configure(state='normal')
        import datetime
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.history_text.insert('end', f'[{ts}] {msg}\n')
        self.history_text.see('end')
        self.history_text.configure(state='disabled')

    # ─── Tool openers ───────────────────────────────────────────────────────

    def _open_module(self, module_path, class_name, title):
        try:
            import importlib
            mod = importlib.import_module(module_path)
            cls = getattr(mod, class_name)
            win = tk.Toplevel(self.root)
            win.title(title)
            win.resizable(True, True)
            cls(win)
            self.log_history(f"Opened: {title}")
        except Exception as e:
            messagebox.showerror("Error", f"Không thể mở {title}:\n{e}")

    def open_printer_fix(self):
        self.notebook.select(self.printer_frame)
        self.log_history("Switched to: 🖨️ Fix Print")

    def open_auto_shutdown(self):
        self._open_module('modules.auto_shutdown', 'AutoShutdown', '⏻ Auto Shutdown')

    def open_hosts_editor(self):
        self._open_module('modules.hosts_editor', 'HostsEditor', '📝 Hosts File Editor')

    def open_computer_info(self):
        self._open_module('modules.computer_info', 'ComputerInfo', '💻 Computer Info')

    def open_sendto_editor(self):
        self._open_module('modules.sendto_editor', 'SendToEditor', '📤 SendTo Editor')

    def open_classic_menu(self):
        self._open_module('modules.classic_menu', 'ClassicMenu', '🪟 Classic Context Menu')

    def open_your_ip(self):
        self._open_module('modules.ip_manager', 'IPManager', '🌐 IP Manager')

    def open_ip_manager(self):
        self._open_module('modules.ip_manager', 'IPManager', '🌐 IP Manager')

    def open_desktop_icon(self):
        self._open_module('modules.desktop_icon', 'DesktopIcon', '🖥️ Desktop Icon')

    def open_ip_scanner(self):
        self._open_module('modules.ip_scanner', 'IPScanner', '🔍 IP Scanner')

    def open_bitlocker(self):
        self._open_module('modules.bitlocker', 'BitLocker', '🔒 BitLocker')

    def open_firewall(self):
        self._open_module('modules.firewall', 'FirewallManager', '🛡️ Firewall Manager')

    def open_datetime(self):
        self._open_module('modules.datetime_tool', 'DateTimeTool', '🕐 Date & Time')

    def open_backup_driver(self):
        self._open_module('modules.backup_driver', 'BackupDriver', '💾 Backup/Restore Driver')

    def open_office_opt(self):
        self._open_module('modules.office_opt', 'OfficeOptimization', '📊 Office Optimization')

    def open_browser_backup(self):
        self._open_module('modules.browser_backup', 'BrowserBackup', '🌍 Browser Backup')

    def open_win_update(self):
        self._open_module('modules.win_update', 'WindowsUpdate', '🔄 Windows Update/Security')

    def open_boot_manager(self):
        self._open_module('modules.boot_manager', 'BootManager', '⚙️ Boot Manager')

    def open_services(self):
        self._open_module('modules.services_manager', 'ServicesManager', '⚙️ Services Manager')

    def open_server_tools(self):
        self._open_module('modules.server_tools', 'ServerTools', '🖧 Server Tools')

    def open_folder_size(self):
        self._open_module('modules.folder_size', 'FolderSize', '📁 Folder Size')

    def open_currency(self):
        self._open_module('modules.currency', 'Currency', '💰 Currency Converter')

    def open_other_tools(self):
        self._open_module('modules.other_tools', 'OtherTools', '🔧 Other Tools')
