"""
Server Tools Module
NIC Teaming SET, DHCP Backup/Restore, AD Backup, iSCSI Manager
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS


class ServerTools:
    def __init__(self, parent):
        self.parent = parent
        self.parent.geometry('750x600')
        self.parent.configure(bg=COLORS['bg'])
        self.setup_ui()

    def setup_ui(self):
        hdr = tk.Frame(self.parent, bg=COLORS['bg_header'])
        hdr.pack(fill='x')
        tk.Label(hdr, text='🖧  Server Tools', font=FONTS['large'],
                  bg=COLORS['bg_header'], fg='white', pady=10).pack(side='left', padx=15)

        nb = ttk.Notebook(self.parent)
        nb.pack(fill='both', expand=True, padx=8, pady=8)

        # NIC Teaming
        nic_frame = tk.Frame(nb, bg=COLORS['bg'])
        nb.add(nic_frame, text='🔌 NIC Teaming (SET)')
        self._build_nic_teaming(nic_frame)

        # DHCP
        dhcp_frame = tk.Frame(nb, bg=COLORS['bg'])
        nb.add(dhcp_frame, text='🌐 DHCP Backup/Restore')
        self._build_dhcp(dhcp_frame)

        # AD Backup
        ad_frame = tk.Frame(nb, bg=COLORS['bg'])
        nb.add(ad_frame, text='🏢 AD Backup')
        self._build_ad(ad_frame)

        # iSCSI
        iscsi_frame = tk.Frame(nb, bg=COLORS['bg'])
        nb.add(iscsi_frame, text='💾 iSCSI Manager')
        self._build_iscsi(iscsi_frame)

    def _build_nic_teaming(self, parent):
        info = tk.Label(parent, text='NIC Teaming (Switch Embedded Teaming - SET)',
                         font=FONTS['subtitle'], bg=COLORS['bg'],
                         fg=COLORS['text'], pady=10)
        info.pack()

        # Current teams
        list_frame = tk.LabelFrame(parent, text='  Current NIC Teams  ',
                                    font=FONTS['subtitle'], bg=COLORS['bg'])
        list_frame.pack(fill='x', padx=15, pady=5)

        cols = ('Team Name', 'Mode', 'Members', 'Status')
        tree = ttk.Treeview(list_frame, columns=cols, show='headings', height=5)
        for col in cols:
            tree.heading(col, text=col, anchor='w')
            tree.column(col, width=150, minwidth=80)
        tree.pack(fill='x', padx=5, pady=5)

        # Load teams
        def load_teams():
            result = subprocess.run(
                ['powershell', '-Command',
                 'Get-NetLbfoTeam | Select-Object Name, TeamingMode, Members, Status '
                 '| ConvertTo-Csv -NoTypeInformation'],
                capture_output=True, text=True, timeout=15
            )
            for line in result.stdout.strip().splitlines()[1:]:
                parts = [p.strip('"') for p in line.split(',')]
                if parts and parts[0]:
                    tree.insert('', 'end', values=parts[:4])

        load_teams()

        # Create team form
        create_frame = tk.LabelFrame(parent, text='  Create SET Team  ',
                                      font=FONTS['subtitle'], bg=COLORS['bg'])
        create_frame.pack(fill='x', padx=15, pady=5)

        form = tk.Frame(create_frame, bg=COLORS['bg'])
        form.pack(padx=10, pady=8)

        fields = [('Team Name:', 'name'), ('Adapters (comma):', 'adapters')]
        self.team_vars = {}
        for label, key in fields:
            tk.Label(form, text=label, font=FONTS['normal'],
                      bg=COLORS['bg']).grid(row=len(self.team_vars), column=0,
                                             padx=5, pady=4, sticky='w')
            var = tk.StringVar()
            self.team_vars[key] = var
            tk.Entry(form, textvariable=var, font=FONTS['normal'],
                      width=30).grid(row=len(self.team_vars)-1, column=1,
                                      padx=5, pady=4)

        tk.Label(form, text='Mode:', font=FONTS['normal'],
                  bg=COLORS['bg']).grid(row=2, column=0, padx=5, pady=4, sticky='w')
        self.team_mode = ttk.Combobox(form, values=[
            'SwitchIndependent', 'LACP', 'Static'
        ], width=20, state='readonly')
        self.team_mode.set('SwitchIndependent')
        self.team_mode.grid(row=2, column=1, padx=5, pady=4, sticky='w')

        btn_frame = tk.Frame(create_frame, bg=COLORS['bg'])
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text='➕ Create Team', font=FONTS['normal'],
                   bg=COLORS['accent'], fg='white', relief='flat',
                   padx=15, pady=5, cursor='hand2',
                   command=self.create_team).pack(side='left', padx=5)
        tk.Button(btn_frame, text='❌ Remove Team', font=FONTS['normal'],
                   bg=COLORS['danger'], fg='white', relief='flat',
                   padx=15, pady=5, cursor='hand2',
                   command=lambda: messagebox.showinfo('Info', 'Select team and remove'
                                                       )).pack(side='left', padx=5)

    def create_team(self):
        name = self.team_vars.get('name', tk.StringVar()).get()
        adapters = self.team_vars.get('adapters', tk.StringVar()).get()
        mode = self.team_mode.get()
        if not name or not adapters:
            messagebox.showwarning('Warning', 'Enter team name and adapters!')
            return
        adapter_list = [f'"{a.strip()}"' for a in adapters.split(',')]
        cmd = (f'New-NetLbfoTeam -Name "{name}" '
               f'-TeamMembers {",".join(adapter_list)} '
               f'-TeamingMode {mode}')
        result = subprocess.run(['powershell', '-Command', cmd],
                                 capture_output=True, text=True)
        if result.returncode == 0:
            messagebox.showinfo('Success', f'✅ Team "{name}" created!')
        else:
            messagebox.showerror('Error', result.stderr or result.stdout)

    def _build_dhcp(self, parent):
        tk.Label(parent, text='DHCP Server Backup/Restore',
                  font=FONTS['subtitle'], bg=COLORS['bg'], pady=10).pack()

        frame = tk.Frame(parent, bg=COLORS['bg'])
        frame.pack(padx=20, pady=10, fill='x')

        tk.Label(frame, text='DHCP Server:', font=FONTS['normal'],
                  bg=COLORS['bg']).grid(row=0, column=0, padx=5, pady=8, sticky='w')
        self.dhcp_server = tk.Entry(frame, font=FONTS['normal'], width=25)
        self.dhcp_server.insert(0, 'localhost')
        self.dhcp_server.grid(row=0, column=1, padx=5, pady=8)

        btn_frame = tk.Frame(parent, bg=COLORS['bg'])
        btn_frame.pack(pady=10)
        for text, cmd, color in [
            ('💾 Backup DHCP', self.backup_dhcp, COLORS['accent']),
            ('📥 Restore DHCP', self.restore_dhcp, COLORS['info']),
            ('📋 Export Leases', self.export_dhcp_leases, COLORS['warning']),
        ]:
            tk.Button(btn_frame, text=text, font=FONTS['normal'],
                       bg=color, fg='white', relief='flat',
                       padx=15, pady=8, cursor='hand2',
                       command=cmd).pack(side='left', padx=8)

    def backup_dhcp(self):
        dest = filedialog.askdirectory(title='DHCP Backup Destination')
        if not dest:
            return
        server = self.dhcp_server.get()
        result = subprocess.run(
            ['powershell', '-Command',
             f'Backup-DhcpServer -ComputerName {server} -Path "{dest}"'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            messagebox.showinfo('Backup', f'✅ DHCP backed up to: {dest}')
        else:
            messagebox.showerror('Error', result.stderr or 'DHCP Backup failed. Install DHCP server tools.')

    def restore_dhcp(self):
        folder = filedialog.askdirectory(title='DHCP Backup Folder')
        if not folder:
            return
        server = self.dhcp_server.get()
        result = subprocess.run(
            ['powershell', '-Command',
             f'Restore-DhcpServer -ComputerName {server} -Path "{folder}" -Force'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            messagebox.showinfo('Restore', '✅ DHCP restored!')
        else:
            messagebox.showerror('Error', result.stderr)

    def export_dhcp_leases(self):
        path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV', '*.csv'), ('All', '*.*')]
        )
        if not path:
            return
        server = self.dhcp_server.get()
        result = subprocess.run(
            ['powershell', '-Command',
             f'Get-DhcpServerv4Lease -ComputerName {server} -ScopeId 0.0.0.0 '
             f'| Export-Csv "{path}" -NoTypeInformation'],
            capture_output=True, text=True
        )
        messagebox.showinfo('Export', f'Exported to: {path}')

    def _build_ad(self, parent):
        tk.Label(parent, text='Active Directory Backup (Windows Server Backup)',
                  font=FONTS['subtitle'], bg=COLORS['bg'], pady=10).pack()

        frame = tk.Frame(parent, bg=COLORS['bg'])
        frame.pack(padx=20, pady=10)

        for text, cmd, color in [
            ('💾 Backup AD (System State)', self.backup_ad, COLORS['accent']),
            ('📥 Restore AD', self.restore_ad, COLORS['info']),
            ('📊 AD Info', self.ad_info, COLORS['warning']),
            ('👥 Export Users', self.export_users, '#8E44AD'),
        ]:
            tk.Button(frame, text=text, font=FONTS['subtitle'],
                       bg=color, fg='white', relief='flat',
                       padx=20, pady=10, cursor='hand2',
                       command=cmd).pack(pady=5, fill='x')

    def backup_ad(self):
        dest = filedialog.askdirectory(title='Select Backup Destination')
        if not dest:
            return
        result = subprocess.run(
            ['wbadmin', 'start', 'systemstatebackup', f'-backuptarget:{dest}', '-quiet'],
            capture_output=True, text=True
        )
        messagebox.showinfo('AD Backup',
                             result.stdout[:500] if result.returncode == 0
                             else f'Error: {result.stderr[:500]}')

    def restore_ad(self):
        messagebox.showinfo('AD Restore',
                             'AD Restore requires DSRM mode.\n'
                             'Restart server in Directory Services Restore Mode.')

    def ad_info(self):
        result = subprocess.run(
            ['powershell', '-Command',
             'Get-ADDomain | Select-Object Name, DNSRoot, DomainMode, '
             'PDCEmulator, RIDMaster | Format-List | Out-String'],
            capture_output=True, text=True, timeout=15
        )
        messagebox.showinfo('AD Info', result.stdout or 'AD cmdlets not available')

    def export_users(self):
        path = filedialog.asksaveasfilename(
            defaultextension='.csv', filetypes=[('CSV', '*.csv')]
        )
        if not path:
            return
        result = subprocess.run(
            ['powershell', '-Command',
             f'Get-ADUser -Filter * -Properties * | '
             f'Select-Object Name, SamAccountName, Email, Enabled, Created '
             f'| Export-Csv "{path}" -NoTypeInformation'],
            capture_output=True, text=True
        )
        messagebox.showinfo('Export', f'Exported users to: {path}')

    def _build_iscsi(self, parent):
        tk.Label(parent, text='iSCSI Target & Initiator Manager',
                  font=FONTS['subtitle'], bg=COLORS['bg'], pady=10).pack()

        # iSCSI Initiator
        init_frame = tk.LabelFrame(parent, text='  iSCSI Initiator  ',
                                    font=FONTS['subtitle'], bg=COLORS['bg'])
        init_frame.pack(fill='x', padx=15, pady=5)

        row = tk.Frame(init_frame, bg=COLORS['bg'])
        row.pack(padx=10, pady=8)
        tk.Label(row, text='Target Portal (IP):', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left', padx=5)
        self.iscsi_ip = tk.Entry(row, font=FONTS['normal'], width=20)
        self.iscsi_ip.pack(side='left', padx=5)
        tk.Label(row, text='Port:', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left', padx=5)
        self.iscsi_port = tk.Entry(row, font=FONTS['normal'], width=6)
        self.iscsi_port.insert(0, '3260')
        self.iscsi_port.pack(side='left', padx=5)

        btn_frame = tk.Frame(init_frame, bg=COLORS['bg'])
        btn_frame.pack(pady=5)
        for text, cmd, color in [
            ('🔌 Connect', self.iscsi_connect, COLORS['accent']),
            ('❌ Disconnect', self.iscsi_disconnect, COLORS['danger']),
            ('📋 List Targets', self.iscsi_list, COLORS['info']),
            ('⚙️ iSCSI Settings', lambda: subprocess.Popen('iscsicpl.exe'), COLORS['warning']),
        ]:
            tk.Button(btn_frame, text=text, font=FONTS['small'],
                       bg=color, fg='white', relief='flat',
                       padx=10, pady=5, cursor='hand2',
                       command=cmd).pack(side='left', padx=4)

        self.iscsi_output = tk.Text(parent, font=FONTS['mono'],
                                     bg='#1E1E1E', fg='#D4D4D4',
                                     height=8, relief='flat',
                                     padx=10, pady=5)
        self.iscsi_output.pack(fill='both', expand=True, padx=15, pady=5)

    def iscsi_connect(self):
        ip = self.iscsi_ip.get()
        port = self.iscsi_port.get()
        if not ip:
            messagebox.showwarning('Warning', 'Enter target portal IP!')
            return
        result = subprocess.run(
            ['iscsicli', 'AddTargetPortal', ip, port],
            capture_output=True, text=True
        )
        self.iscsi_output.configure(state='normal')
        self.iscsi_output.insert('end', result.stdout + result.stderr + '\n')
        self.iscsi_output.configure(state='disabled')

    def iscsi_disconnect(self):
        result = subprocess.run(['iscsicli', 'ListTargets'],
                                 capture_output=True, text=True)
        messagebox.showinfo('Disconnect', 'Use iSCSI Initiator applet for disconnect:\n' + result.stdout[:300])

    def iscsi_list(self):
        result = subprocess.run(['iscsicli', 'ListTargets'],
                                 capture_output=True, text=True)
        self.iscsi_output.configure(state='normal')
        self.iscsi_output.delete('1.0', 'end')
        self.iscsi_output.insert('1.0', result.stdout or 'No targets found')
        self.iscsi_output.configure(state='disabled')


# ── STANDALONE SERVER TOOLS API FUNCTIONS FOR WEB/CLI ─────────────────────

def get_nic_teams():
    """Gets list of NIC teams via Get-NetLbfoTeam."""
    try:
        cmd = 'Get-NetLbfoTeam | Select-Object Name, TeamingMode, Members, Status | ConvertTo-Json'
        res = subprocess.run(['powershell', '-NoProfile', '-Command', cmd], capture_output=True, text=True, timeout=15, encoding='utf-8', errors='ignore')
        teams = []
        if res.returncode == 0 and res.stdout.strip():
            import json
            data = json.loads(res.stdout)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                members_val = item.get("Members")
                if isinstance(members_val, list):
                    members_str = ", ".join(members_val)
                elif isinstance(members_val, dict):
                    members_str = str(members_val.get("Name", ""))
                else:
                    members_str = str(members_val or "")

                teams.append({
                    "name": item.get("Name", "N/A"),
                    "mode": str(item.get("TeamingMode", "N/A")),
                    "members": members_str,
                    "status": str(item.get("Status", "N/A"))
                })
        return {"success": True, "teams": teams}
    except Exception as e:
        return {"success": False, "message": str(e), "teams": []}

def create_nic_team(name, adapters_str, mode="SwitchIndependent"):
    """Creates a new NIC Team via PowerShell New-NetLbfoTeam."""
    if not name or not adapters_str:
        return {"success": False, "message": "Vui lòng nhập tên Team và danh sách Card mạng!"}
    try:
        adapters = [a.strip() for a in adapters_str.split(",") if a.strip()]
        adapter_list = [f'"{a}"' for a in adapters]
        cmd = f'New-NetLbfoTeam -Name "{name}" -TeamMembers {",".join(adapter_list)} -TeamingMode {mode} -Confirm:$false'
        res = subprocess.run(['powershell', '-NoProfile', '-Command', cmd], capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore')
        if res.returncode == 0:
            return {"success": True, "message": f"Đã tạo NIC Team '{name}' thành công!"}
        else:
            return {"success": False, "message": res.stderr.strip() or res.stdout.strip() or "Không thể tạo NIC Team."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def remove_nic_team(name):
    """Removes a NIC Team via PowerShell Remove-NetLbfoTeam."""
    if not name:
        return {"success": False, "message": "Vui lòng chỉ định tên Team cần xóa!"}
    try:
        cmd = f'Remove-NetLbfoTeam -Name "{name}" -Confirm:$false'
        res = subprocess.run(['powershell', '-NoProfile', '-Command', cmd], capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore')
        if res.returncode == 0:
            return {"success": True, "message": f"Đã xóa NIC Team '{name}' thành công!"}
        else:
            return {"success": False, "message": res.stderr.strip() or res.stdout.strip() or "Không thể xóa NIC Team."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def backup_dhcp(server="localhost", dest_path=""):
    """Backs up DHCP server configuration and leases."""
    if not dest_path:
        user_profile = os.environ.get('USERPROFILE', 'C:\\')
        dest_path = os.path.join(user_profile, 'Desktop', 'DHCP_Backup')
    try:
        os.makedirs(dest_path, exist_ok=True)
        cmd = f'Backup-DhcpServer -ComputerName "{server}" -Path "{dest_path}"'
        res = subprocess.run(['powershell', '-NoProfile', '-Command', cmd], capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore')
        if res.returncode == 0:
            return {"success": True, "message": f"Đã sao lưu DHCP vào: {dest_path}", "path": dest_path}
        else:
            return {"success": False, "message": res.stderr.strip() or res.stdout.strip() or "Không thể sao lưu DHCP. Kiểm tra xem DHCP Server role đã cài chưa."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def restore_dhcp(server="localhost", source_path=""):
    """Restores DHCP server from backup directory."""
    if not source_path or not os.path.exists(source_path):
        return {"success": False, "message": "Thư mục sao lưu DHCP không tồn tại!"}
    try:
        cmd = f'Restore-DhcpServer -ComputerName "{server}" -Path "{source_path}" -Force'
        res = subprocess.run(['powershell', '-NoProfile', '-Command', cmd], capture_output=True, text=True, timeout=45, encoding='utf-8', errors='ignore')
        if res.returncode == 0:
            return {"success": True, "message": "Đã khôi phục DHCP Server thành công!"}
        else:
            return {"success": False, "message": res.stderr.strip() or res.stdout.strip()}
    except Exception as e:
        return {"success": False, "message": str(e)}

def export_dhcp_leases(server="localhost", save_path=""):
    """Exports active DHCP leases to CSV."""
    if not save_path:
        user_profile = os.environ.get('USERPROFILE', 'C:\\')
        save_path = os.path.join(user_profile, 'Desktop', 'DHCP_Leases.csv')
    try:
        cmd = f'Get-DhcpServerv4Lease -ComputerName "{server}" -ScopeId 0.0.0.0 | Export-Csv "{save_path}" -NoTypeInformation'
        res = subprocess.run(['powershell', '-NoProfile', '-Command', cmd], capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore')
        if res.returncode == 0 and os.path.exists(save_path):
            return {"success": True, "message": f"Đã xuất danh sách DHCP Leases ra: {save_path}", "path": save_path}
        else:
            return {"success": False, "message": res.stderr.strip() or "Không thể xuất Leases. Cần quyền admin hoặc máy tính chưa bật DHCP Server."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def get_ad_info():
    """Fetches AD Domain Info via PowerShell Get-ADDomain."""
    try:
        cmd = 'Get-ADDomain | Select-Object Name, DNSRoot, DomainMode, PDCEmulator, RIDMaster | ConvertTo-Json'
        res = subprocess.run(['powershell', '-NoProfile', '-Command', cmd], capture_output=True, text=True, timeout=15, encoding='utf-8', errors='ignore')
        if res.returncode == 0 and res.stdout.strip():
            import json
            data = json.loads(res.stdout)
            return {"success": True, "info": data}
        else:
            return {"success": False, "message": "Không tìm thấy thông tin Active Directory (Máy chưa Join Domain hoặc chưa cài RSAT)."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def export_ad_users(save_path=""):
    """Exports Active Directory Users to CSV."""
    if not save_path:
        user_profile = os.environ.get('USERPROFILE', 'C:\\')
        save_path = os.path.join(user_profile, 'Desktop', 'AD_Users.csv')
    try:
        cmd = f'Get-ADUser -Filter * -Properties * | Select-Object Name, SamAccountName, EmailAddress, Enabled, Created | Export-Csv "{save_path}" -NoTypeInformation'
        res = subprocess.run(['powershell', '-NoProfile', '-Command', cmd], capture_output=True, text=True, timeout=45, encoding='utf-8', errors='ignore')
        if res.returncode == 0 and os.path.exists(save_path):
            return {"success": True, "message": f"Đã xuất danh sách AD Users ra: {save_path}", "path": save_path}
        else:
            return {"success": False, "message": res.stderr.strip() or "Không thể xuất AD Users. Cần module Active Directory."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def connect_iscsi_target(ip, port="3260"):
    """Connects to iSCSI Target Portal using iscsicli."""
    if not ip:
        return {"success": False, "message": "Vui lòng nhập IP Target Portal!"}
    try:
        res = subprocess.run(['iscsicli', 'AddTargetPortal', ip, str(port)], capture_output=True, text=True, timeout=15, encoding='utf-8', errors='ignore')
        out = (res.stdout or '') + '\n' + (res.stderr or '')
        if res.returncode == 0 or "operation completed successfully" in out.lower():
            return {"success": True, "message": f"Đã kết nối iSCSI Portal {ip}:{port}", "output": out.strip()}
        else:
            return {"success": False, "message": f"Lỗi kết nối iSCSI Portal: {out.strip()}", "output": out.strip()}
    except Exception as e:
        return {"success": False, "message": str(e)}

def list_iscsi_targets():
    """Lists current iSCSI Targets via iscsicli."""
    try:
        res = subprocess.run(['iscsicli', 'ListTargets'], capture_output=True, text=True, timeout=15, encoding='utf-8', errors='ignore')
        return {"success": True, "output": res.stdout.strip() or "Không tìm thấy iSCSI Targets nào."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def open_iscsi_cpl():
    """Opens native Windows iSCSI Initiator control panel applet."""
    try:
        subprocess.Popen('iscsicpl.exe', shell=True)
        return {"success": True, "message": "Đã mở Windows iSCSI Initiator Properties!"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def open_server_tools_gui():
    """Launches Tkinter Server Tools GUI."""
    try:
        main_py = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
        subprocess.Popen([sys.executable, main_py, "--module", "server_tools"])
        return {"success": True, "message": "Đã mở giao diện Server Tools GUI!"}
    except Exception as e:
        return {"success": False, "message": str(e)}

