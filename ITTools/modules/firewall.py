"""
Firewall Manager Module
Allow All, Off, Default rules
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS


class FirewallManager:
    def __init__(self, parent):
        self.parent = parent
        self.parent.geometry('700x600')
        self.parent.configure(bg=COLORS['bg'])
        self.setup_ui()
        threading.Thread(target=self.load_status, daemon=True).start()

    def setup_ui(self):
        hdr = tk.Frame(self.parent, bg=COLORS['bg_header'])
        hdr.pack(fill='x')
        tk.Label(hdr, text='🛡️  Firewall Manager', font=FONTS['large'],
                  bg=COLORS['bg_header'], fg='white', pady=10).pack(side='left', padx=15)

        # Status panels
        status_frame = tk.LabelFrame(self.parent, text='  Firewall Status by Profile  ',
                                      font=FONTS['subtitle'], bg=COLORS['bg'])
        status_frame.pack(fill='x', padx=15, pady=10)

        self.profile_vars = {}
        profiles = [
            ('Domain Profile', 'Domain', '#2980B9'),
            ('Private Profile', 'Private', '#27AE60'),
            ('Public Profile', 'Public', '#E74C3C'),
        ]
        for name, key, color in profiles:
            frame = tk.Frame(status_frame, bg=COLORS['bg'], relief='groove',
                              bd=1, padx=15, pady=8)
            frame.pack(side='left', expand=True, fill='x', padx=5, pady=5)
            tk.Label(frame, text=name, font=FONTS['subtitle'],
                      bg=COLORS['bg'], fg=color).pack()
            var = tk.StringVar(value='Checking...')
            self.profile_vars[key] = var
            tk.Label(frame, textvariable=var, font=FONTS['subtitle'],
                      bg=COLORS['bg']).pack()

        # Quick actions
        action_frame = tk.LabelFrame(self.parent, text='  Quick Actions  ',
                                      font=FONTS['subtitle'], bg=COLORS['bg'],
                                      relief='groove')
        action_frame.pack(fill='x', padx=15, pady=5)

        buttons = [
            ('✅ Enable Firewall\n(All Profiles)', self.enable_all, COLORS['accent']),
            ('🚫 Disable Firewall\n(All Profiles)', self.disable_all, COLORS['danger']),
            ('⚙️ Default Settings\n(Reset)', self.reset_default, COLORS['warning']),
            ('🔓 Allow All\n(Inbound)', self.allow_all_inbound, '#8E44AD'),
        ]
        for text, cmd, color in buttons:
            tk.Button(action_frame, text=text, font=FONTS['normal'],
                       bg=color, fg='white', relief='flat',
                       padx=15, pady=10, cursor='hand2',
                       command=cmd, wraplength=120).pack(
                side='left', padx=8, pady=8, expand=True, fill='x')

        # Rules list
        rules_frame = tk.LabelFrame(self.parent, text='  Firewall Rules (Active)  ',
                                     font=FONTS['subtitle'], bg=COLORS['bg'])
        rules_frame.pack(fill='both', expand=True, padx=15, pady=5)

        # Toolbar
        bar = tk.Frame(rules_frame, bg=COLORS['bg'])
        bar.pack(fill='x', padx=5, pady=3)
        tk.Label(bar, text='Filter:', font=FONTS['small'],
                  bg=COLORS['bg']).pack(side='left', padx=3)
        self.rule_filter = tk.StringVar()
        self.rule_filter.trace_add('write', self.filter_rules)
        tk.Entry(bar, textvariable=self.rule_filter,
                  font=FONTS['normal'], width=25).pack(side='left', padx=3)

        self.dir_filter = tk.StringVar(value='All')
        for val in ['All', 'Inbound', 'Outbound']:
            tk.Radiobutton(bar, text=val, value=val, variable=self.dir_filter,
                            font=FONTS['small'], bg=COLORS['bg'],
                            selectcolor=COLORS['selected'],
                            command=self.filter_rules).pack(side='left', padx=5)

        tk.Button(bar, text='🔄 Refresh Rules', font=FONTS['small'],
                   bg=COLORS['info'], fg='white', relief='flat', padx=8,
                   cursor='hand2',
                   command=lambda: threading.Thread(
                       target=self.load_rules, daemon=True).start()
                   ).pack(side='right', padx=5)

        cols = ('Name', 'Direction', 'Action', 'Protocol', 'LocalPort')
        self.tree = ttk.Treeview(rules_frame, columns=cols, show='headings', height=8)
        widths = [200, 80, 70, 70, 80]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col, anchor='w')
            self.tree.column(col, width=w, minwidth=40)

        vsb = ttk.Scrollbar(rules_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True, padx=5, pady=3)

        self.tree.tag_configure('allow', foreground='#27AE60')
        self.tree.tag_configure('block', foreground='#E74C3C')
        self.all_rules = []

        self.progress = ttk.Progressbar(self.parent, mode='indeterminate')
        self.progress.pack(fill='x', padx=15, pady=2)

    def load_status(self):
        result = subprocess.run(
            ['netsh', 'advfirewall', 'show', 'allprofiles', 'state'],
            capture_output=True, text=True
        )
        current_profile = None
        for line in result.stdout.splitlines():
            line = line.strip()
            for profile in ('Domain', 'Private', 'Public'):
                if profile.lower() in line.lower() and 'profile' in line.lower():
                    current_profile = profile
            if current_profile and 'State' in line:
                state = '✅ ON' if 'ON' in line else '🚫 OFF'
                self.profile_vars[current_profile].set(state)

        threading.Thread(target=self.load_rules, daemon=True).start()

    def load_rules(self):
        self.progress.start()
        self.all_rules = []
        result = subprocess.run(
            ['powershell', '-Command',
             'Get-NetFirewallRule | Where-Object Enabled -eq True '
             '| Select-Object -First 200 DisplayName, Direction, Action, Protocol, '
             'LocalPort | ConvertTo-Csv -NoTypeInformation'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines()[1:]:
                parts = [p.strip('"') for p in line.split(',')]
                if len(parts) >= 5:
                    self.all_rules.append(parts[:5])

        self.filter_rules()
        self.progress.stop()

    def filter_rules(self, *args):
        q = self.rule_filter.get().lower()
        df = self.dir_filter.get()
        self.tree.delete(*self.tree.get_children())
        for rule in self.all_rules:
            name, direction, action = rule[0], rule[1], rule[2]
            if q and q not in name.lower():
                continue
            if df != 'All' and df.lower() not in direction.lower():
                continue
            tag = 'allow' if 'Allow' in action else 'block'
            self.tree.insert('', 'end', values=rule, tags=(tag,))

    def enable_all(self):
        if messagebox.askyesno('Confirm', 'Bật Firewall cho tất cả profiles?'):
            subprocess.run(['netsh', 'advfirewall', 'set', 'allprofiles',
                             'state', 'on'])
            self.load_status()
            messagebox.showinfo('Firewall', '✅ Firewall đã được bật!')

    def disable_all(self):
        if messagebox.askyesno('⚠️ Warning',
                                'TẮT Firewall cho tất cả profiles?\n'
                                'Máy tính của bạn sẽ kém bảo mật hơn!'):
            subprocess.run(['netsh', 'advfirewall', 'set', 'allprofiles',
                             'state', 'off'])
            self.load_status()
            messagebox.showinfo('Firewall', '🚫 Firewall đã tắt!')

    def reset_default(self):
        if messagebox.askyesno('Reset', 'Khôi phục cài đặt Firewall mặc định?'):
            subprocess.run(['netsh', 'advfirewall', 'reset'])
            self.load_status()
            messagebox.showinfo('Reset', '✅ Đã khôi phục cài đặt mặc định!')

    def allow_all_inbound(self):
        if messagebox.askyesno('Warning',
                                'Cho phép tất cả kết nối Inbound?\n'
                                '⚠️ Chỉ dùng trong môi trường tin cậy!'):
            subprocess.run(['netsh', 'advfirewall', 'set', 'allprofiles',
                             'firewallpolicy', 'allowinbound,allowoutbound'])
            messagebox.showinfo('Firewall', '✅ Đã Allow All Inbound!')


def get_firewall_status():
    """Returns real-time status of Domain, Private, and Public Firewall profiles, inbound policy, and common rule groups."""
    import winreg
    from concurrent.futures import ThreadPoolExecutor

    profiles = {"domain": False, "private": False, "public": False}
    policies = {"domain": "BlockInbound", "private": "BlockInbound", "public": "BlockInbound"}
    inbound_allowed = False
    fps_active = False
    fps_count = 0
    rdp_active = False
    rdp_count = 0
    ping_active = False
    ping_count = 0
    kaspersky_active = False
    has_block_fps = False
    has_block_ping = False
    has_block_rdp = False

    def _fetch_profiles():
        nonlocal profiles, policies, inbound_allowed
        try:
            res = subprocess.run(["netsh", "advfirewall", "show", "allprofiles"], capture_output=True, text=True, timeout=8)
            current_prof = None
            for line in res.stdout.splitlines():
                line_s = line.strip()
                for p in ["Domain", "Private", "Public"]:
                    if f"{p} Profile Settings:" in line_s or f"{p.lower()} profile" in line_s.lower():
                        current_prof = p.lower()
                if current_prof:
                    if line_s.startswith("State"):
                        profiles[current_prof] = "on" in line_s.lower()
                    elif line_s.startswith("Firewall Policy"):
                        policies[current_prof] = line_s.split(None, 2)[-1].strip()
            inbound_allowed = any("allowinbound" in pol.lower() for pol in policies.values())
        except Exception:
            pass

    def _fetch_rules():
        nonlocal fps_active, fps_count, rdp_active, rdp_count, ping_active, ping_count, kaspersky_active
        nonlocal has_block_fps, has_block_ping, has_block_rdp
        try:
            res = subprocess.run(["netsh", "advfirewall", "firewall", "show", "rule", "name=all"], capture_output=True, text=True, timeout=8)
            for block in res.stdout.split("Rule Name:"):
                if not block.strip():
                    continue
                is_enabled = False
                is_inbound = False
                is_fps = False
                is_rdp = False
                is_ping = False
                is_block = False
                name = block.splitlines()[0].strip()
                name_u = name.upper()

                if "ITTOOL_BLOCK_PING" in name_u:
                    has_block_ping = True
                if "ITTOOL_BLOCK_FILE_SHARING" in name_u:
                    has_block_fps = True
                if "ITTOOL_BLOCK_RDP" in name_u:
                    has_block_rdp = True

                for line in block.splitlines():
                    line_s = line.strip()
                    if line_s.startswith("Enabled:"):
                        is_enabled = (line_s.split(":", 1)[1].strip().lower() == "yes")
                    elif line_s.startswith("Direction:"):
                        is_inbound = ("in" in line_s.split(":", 1)[1].strip().lower())
                    elif line_s.startswith("Action:"):
                        is_block = ("block" in line_s.split(":", 1)[1].strip().lower())
                    elif line_s.startswith("Grouping:"):
                        grp = line_s.split(":", 1)[1].strip()
                        if "File and Printer Sharing" in grp or "@FirewallAPI.dll,-28502" in grp or "@FirewallAPI.dll,-28672" in grp:
                            is_fps = True
                        elif "Remote Desktop" in grp or "@FirewallAPI.dll,-28752" in grp or "@FirewallAPI.dll,-28753" in grp:
                            is_rdp = True

                if "ECHO REQUEST" in name_u or "ICMP4-ERQ" in name_u or "ICMP6-ERQ" in name_u:
                    is_ping = True

                if is_enabled and not is_block:
                    if is_fps and is_inbound:
                        fps_count += 1
                    if is_rdp and is_inbound:
                        rdp_count += 1
                    if is_ping and is_inbound:
                        ping_count += 1

            # Check LanmanServer (Server) service status for SMB File Sharing
            fps_service_running = False
            fps_service_disabled = False
            try:
                sc_res = subprocess.run(["sc", "query", "LanmanServer"], capture_output=True, text=True, timeout=3)
                fps_service_running = ("RUNNING" in sc_res.stdout.upper())
                sc_qc = subprocess.run(["sc", "qc", "LanmanServer"], capture_output=True, text=True, timeout=3)
                fps_service_disabled = ("DISABLED" in sc_qc.stdout.upper())
            except Exception:
                pass

            # True state of File Sharing:
            # File sharing is live and accessible if LanmanServer is running and not disabled.
            # When LanmanServer is stopped and disabled, no remote PC can connect to IP or share names.
            fps_active = fps_service_running and (not fps_service_disabled)

            # Check IPSec ICMP policy
            has_ipsec_block_ping = False
            try:
                ipsec_res = subprocess.run(["netsh", "ipsec", "static", "show", "policy", "name=ITTOOL_BLOCK_ICMP_POLICY"], capture_output=True, text=True, timeout=3)
                has_ipsec_block_ping = ("YES" in ipsec_res.stdout.upper() and "ITTOOL_BLOCK_ICMP_POLICY" in ipsec_res.stdout)
            except Exception:
                pass

            # Check Kaspersky Service
            kaspersky_active = False
            try:
                k_res = subprocess.run(["sc", "query", "AVP21.25"], capture_output=True, text=True, timeout=3)
                if "RUNNING" in k_res.stdout.upper():
                    kaspersky_active = True
            except Exception:
                pass

            # Check Registry for RDP fDenyTSConnections (checking both GPO Policy key and Local key)
            rdp_reg_allowed = True
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services") as key:
                    fDeny, _ = winreg.QueryValueEx(key, "fDenyTSConnections")
                    if fDeny == 1:
                        rdp_reg_allowed = False
            except Exception:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Terminal Server") as key:
                        fDeny, _ = winreg.QueryValueEx(key, "fDenyTSConnections")
                        if fDeny == 1:
                            rdp_reg_allowed = False
                except Exception:
                    pass

            # Check TermService service status
            rdp_service_running = False
            try:
                sc_rdp = subprocess.run(["sc", "query", "TermService"], capture_output=True, text=True, timeout=2)
                rdp_service_running = ("RUNNING" in sc_rdp.stdout.upper())
            except Exception:
                pass

            # Check if port 3389 is actively listening
            rdp_port_open = False
            try:
                import socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.2)
                    rdp_port_open = (s.connect_ex(('127.0.0.1', 3389)) == 0)
            except Exception:
                pass

            if has_ipsec_block_ping or has_block_ping:
                ping_active = False
            else:
                ping_active = (ping_count > 0)
            rdp_active = rdp_service_running and rdp_port_open and rdp_reg_allowed
        except Exception:
            pass

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(_fetch_profiles)
            f2 = executor.submit(_fetch_rules)
            f1.result()
            f2.result()
    except Exception:
        _fetch_profiles()
        _fetch_rules()

    return {
        "success": True,
        "domain": profiles["domain"],
        "private": profiles["private"],
        "public": profiles["public"],
        "all_on": all(profiles.values()),
        "any_on": any(profiles.values()),
        "allow_inbound": inbound_allowed,
        "policies": policies,
        "file_sharing": fps_active,
        "file_sharing_count": fps_count,
        "rdp": rdp_active,
        "rdp_count": rdp_count,
        "ping": ping_active,
        "ping_count": ping_count,
        "kaspersky_active": kaspersky_active,
        "domain_gpo_locked": True
    }


def _run_bg(cmd):
    """Runs secondary synchronization commands in a background daemon thread."""
    def _worker():
        try:
            subprocess.run(cmd, capture_output=True, timeout=10)
        except Exception:
            pass
    threading.Thread(target=_worker, daemon=True).start()


def set_firewall_action(action):
    """Executes firewall enable, disable, reset, or rule commands with dual PowerShell/netsh sync and explicit block overrides."""
    try:
        if action == "enable_all":
            subprocess.run("netsh advfirewall set allprofiles state on", shell=True)
            return {"success": True, "message": "✅ Đã BẬT Windows Firewall cho tất cả Profile!"}

        elif action == "disable_all":
            subprocess.run("netsh advfirewall set allprofiles state off", shell=True)
            return {"success": True, "message": "🚫 Đã TẮT Windows Firewall cho tất cả Profile!"}

        elif action == "reset_defaults":
            subprocess.run("netsh advfirewall reset", shell=True)
            return {"success": True, "message": "⚙️ Đã khôi phục cài đặt Firewall mặc định!"}

        elif action == "allow_inbound":
            subprocess.run("netsh advfirewall set allprofiles firewallpolicy allowinbound,allowoutbound", shell=True)
            return {"success": True, "message": "🔓 Đã Cho Phép tất cả kết nối Inbound!"}

        elif action == "block_inbound":
            subprocess.run("netsh advfirewall set allprofiles firewallpolicy blockinbound,allowoutbound", shell=True)
            return {"success": True, "message": "🔒 Đã Chặn Inbound (Khôi phục mặc định an toàn)!"}

        elif action == "enable_sharing":
            # 1. Delete explicit block rule
            subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", "name=ITTOOL_BLOCK_FILE_SHARING"], capture_output=True)
            # 2. Enable standard rules via netsh
            subprocess.run(['netsh', 'advfirewall', 'firewall', 'set', 'rule', 'group=File and Printer Sharing', 'new', 'enable=Yes'], capture_output=True)
            subprocess.run(['netsh', 'advfirewall', 'firewall', 'set', 'rule', 'group=File and Printer Sharing (Restrictive)', 'new', 'enable=Yes'], capture_output=True)
            # 3. Restore registry AutoShare parameters
            subprocess.run(r'reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" /v AutoShareWks /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
            subprocess.run(r'reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" /v AutoShareServer /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
            # 4. Set LanmanServer to automatic and start it
            subprocess.run("sc config LanmanServer start= auto", shell=True, capture_output=True)
            subprocess.run("net start LanmanServer", shell=True, capture_output=True)
            # 5. Background PowerShell sync
            _run_bg(['powershell', '-NoProfile', '-Command', 'Set-Service -Name LanmanServer -StartupType Automatic -ErrorAction SilentlyContinue; Start-Service -Name LanmanServer -ErrorAction SilentlyContinue; Set-NetFirewallRule -DisplayGroup "File and Printer Sharing*" -Enabled True -ErrorAction SilentlyContinue'])
            return {"success": True, "message": "📂 Đã MỞ Chia Sẻ File & Máy In (LAN)! Dịch vụ Server và cổng 445/139 đã sẵn sàng nhận kết nối."}

        elif action == "disable_sharing":
            # 1. Terminate all active sessions immediately (kicks out connected workstations instantly)
            subprocess.run("net session /delete /y", shell=True, capture_output=True)
            # 2. Force stop LanmanServer service
            subprocess.run("net stop LanmanServer /y", shell=True, capture_output=True)
            subprocess.run(['powershell', '-NoProfile', '-Command', 'Stop-Service -Name LanmanServer -Force -ErrorAction SilentlyContinue'], capture_output=True)
            # 3. Set LanmanServer to DISABLED (crucial: prevents Windows from demand-restarting it)
            subprocess.run("sc config LanmanServer start= disabled", shell=True, capture_output=True)
            subprocess.run(['powershell', '-NoProfile', '-Command', 'Set-Service -Name LanmanServer -StartupType Disabled -ErrorAction SilentlyContinue'], capture_output=True)
            # 4. Disable registry AutoShare parameters
            subprocess.run(r'reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" /v AutoShareWks /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
            subprocess.run(r'reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" /v AutoShareServer /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
            # 5. Disable standard rules via netsh
            subprocess.run(['netsh', 'advfirewall', 'firewall', 'set', 'rule', 'group=File and Printer Sharing', 'new', 'enable=No'], capture_output=True)
            subprocess.run(['netsh', 'advfirewall', 'firewall', 'set', 'rule', 'group=File and Printer Sharing (Restrictive)', 'new', 'enable=No'], capture_output=True)
            # 6. Add explicit high-priority BLOCK rule for all profiles (overrides allow rules even on Domain networks)
            subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", "name=ITTOOL_BLOCK_FILE_SHARING"], capture_output=True)
            subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule", "name=ITTOOL_BLOCK_FILE_SHARING", "protocol=TCP", "localport=445,139", "dir=in", "action=block", "profile=domain,private,public"], capture_output=True)
            subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule", "name=ITTOOL_BLOCK_FILE_SHARING", "protocol=UDP", "localport=137,138", "dir=in", "action=block", "profile=domain,private,public"], capture_output=True)
            # 7. Background PowerShell sync
            _run_bg(['powershell', '-NoProfile', '-Command', 'Set-NetFirewallRule -DisplayGroup "File and Printer Sharing*" -Enabled False -ErrorAction SilentlyContinue'])
            return {"success": True, "message": "🔒 Đã ĐÓNG & CHẶN hoàn toàn Chia Sẻ File! Dịch vụ Server đã dừng và toàn bộ kết nối từ máy khác đã bị ngắt."}

        elif action == "enable_ping":
            # 1. Unassign and delete IPSec ICMP policy
            subprocess.run('netsh ipsec static set policy name="ITTOOL_BLOCK_ICMP_POLICY" assign=n', shell=True, capture_output=True)
            subprocess.run('netsh ipsec static delete policy name="ITTOOL_BLOCK_ICMP_POLICY"', shell=True, capture_output=True)
            subprocess.run('netsh ipsec static delete filterlist name="ITTOOL_ICMP_LIST"', shell=True, capture_output=True)
            subprocess.run('netsh ipsec static delete filteraction name="ITTOOL_BLOCK_ACTION"', shell=True, capture_output=True)
            # 2. Delete explicit block rule
            subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", "name=ITTOOL_BLOCK_PING"], capture_output=True)
            # 3. Enable all ICMPv4 and ICMPv6 echo request rules
            for rule_name in [
                'File and Printer Sharing (Echo Request - ICMPv4-In)',
                'File and Printer Sharing (Echo Request - ICMPv6-In)',
                'Core Networking Diagnostics - ICMP Echo Request (ICMPv4-In)',
                'Core Networking Diagnostics - ICMP Echo Request (ICMPv6-In)',
                'File and Printer Sharing (Restrictive) (Echo Request - ICMPv4-In)',
                'File and Printer Sharing (Restrictive) (Echo Request - ICMPv6-In)',
                'Virtual Machine Monitoring (Echo Request - ICMPv4-In)',
                'Virtual Machine Monitoring (Echo Request - ICMPv6-In)'
            ]:
                subprocess.run(['netsh', 'advfirewall', 'firewall', 'set', 'rule', f'name={rule_name}', 'new', 'enable=Yes'], capture_output=True)
            # 4. Background PowerShell sync
            _run_bg(['powershell', '-NoProfile', '-Command', "Get-NetFirewallRule | Where-Object { $_.Direction -eq 'Inbound' -and ($_.DisplayName -like '*Echo Request*' -or $_.Name -like '*EchoRequest*' -or $_.Name -like '*ERQ*') } | Set-NetFirewallRule -Enabled True -ErrorAction SilentlyContinue"])
            return {"success": True, "message": "🏓 Đã BẬT phản hồi Ping (ICMP Echo Request Inbound)! Các máy khác có thể ping tới máy này."}

        elif action == "disable_ping":
            # 1. Disable all ICMPv4 and ICMPv6 echo request rules
            for rule_name in [
                'File and Printer Sharing (Echo Request - ICMPv4-In)',
                'File and Printer Sharing (Echo Request - ICMPv6-In)',
                'Core Networking Diagnostics - ICMP Echo Request (ICMPv4-In)',
                'Core Networking Diagnostics - ICMP Echo Request (ICMPv6-In)',
                'File and Printer Sharing (Restrictive) (Echo Request - ICMPv4-In)',
                'File and Printer Sharing (Restrictive) (Echo Request - ICMPv6-In)',
                'Virtual Machine Monitoring (Echo Request - ICMPv4-In)',
                'Virtual Machine Monitoring (Echo Request - ICMPv6-In)'
            ]:
                subprocess.run(['netsh', 'advfirewall', 'firewall', 'set', 'rule', f'name={rule_name}', 'new', 'enable=No'], capture_output=True)
            # 2. Add explicit high-priority BLOCK rule for both IPv4 and IPv6 ICMP echo
            subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", "name=ITTOOL_BLOCK_PING"], capture_output=True)
            subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule", "name=ITTOOL_BLOCK_PING", "protocol=icmpv4:8,any", "dir=in", "action=block"], capture_output=True)
            subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule", "name=ITTOOL_BLOCK_PING", "protocol=icmpv6:128,any", "dir=in", "action=block"], capture_output=True)
            # 3. Create and assign Layer-3 IPSec ICMP Block Policy (enforced directly at IP driver layer)
            subprocess.run('netsh ipsec static set policy name="ITTOOL_BLOCK_ICMP_POLICY" assign=n & netsh ipsec static delete policy name="ITTOOL_BLOCK_ICMP_POLICY"', shell=True, capture_output=True)
            subprocess.run('netsh ipsec static add policy name="ITTOOL_BLOCK_ICMP_POLICY"', shell=True, capture_output=True)
            subprocess.run('netsh ipsec static add filteraction name="ITTOOL_BLOCK_ACTION" action=block', shell=True, capture_output=True)
            subprocess.run('netsh ipsec static add filterlist name="ITTOOL_ICMP_LIST"', shell=True, capture_output=True)
            subprocess.run('netsh ipsec static add filter filterlist="ITTOOL_ICMP_LIST" srcaddr=any dstaddr=me protocol=ICMP', shell=True, capture_output=True)
            subprocess.run('netsh ipsec static add rule name="ITTOOL_BLOCK_ICMP_RULE" policy="ITTOOL_BLOCK_ICMP_POLICY" filterlist="ITTOOL_ICMP_LIST" filteraction="ITTOOL_BLOCK_ACTION"', shell=True, capture_output=True)
            subprocess.run('netsh ipsec static set policy name="ITTOOL_BLOCK_ICMP_POLICY" assign=y', shell=True, capture_output=True)
            # 4. Background PowerShell sync
            _run_bg(['powershell', '-NoProfile', '-Command', "Get-NetFirewallRule | Where-Object { $_.Direction -eq 'Inbound' -and ($_.DisplayName -like '*Echo Request*' -or $_.Name -like '*EchoRequest*' -or $_.Name -like '*ERQ*') } | Set-NetFirewallRule -Enabled False -ErrorAction SilentlyContinue"])
            return {"success": True, "message": "🔒 Đã ĐÓNG & CHẶN phản hồi Ping (IPSec + Firewall Layer-3 Block)! Các máy khác sẽ không thể ping tới máy này."}

        elif action == "enable_rdp":
            # 1. Registry: enable Remote Desktop in both Local and GPO Policy trees
            subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
            subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" /v UserAuthentication /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
            subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\Terminal Services" /v fDenyTSConnections /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
            # 2. Start and ensure TermService is running cleanly with port 3389 listening
            subprocess.run(['powershell', '-NoProfile', '-Command', 'Set-Service TermService -StartupType Automatic; Restart-Service TermService -Force'], capture_output=True)
            # 3. Delete block rule
            subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", "name=ITTOOL_BLOCK_RDP"], capture_output=True)
            # 4. Enable firewall rules
            subprocess.run(['netsh', 'advfirewall', 'firewall', 'set', 'rule', 'group=Remote Desktop', 'new', 'enable=Yes'], capture_output=True)
            subprocess.run(['netsh', 'advfirewall', 'firewall', 'set', 'rule', 'group=Remote Desktop (WebSocket)', 'new', 'enable=Yes'], capture_output=True)
            _run_bg(['powershell', '-NoProfile', '-Command', 'Set-NetFirewallRule -DisplayGroup "Remote Desktop*" -Enabled True -ErrorAction SilentlyContinue'])
            return {"success": True, "message": "🖥️ Đã MỞ Remote Desktop (RDP)! Dịch vụ TermService đã bật và cổng 3389 sẵn sàng nhận kết nối."}

        elif action == "disable_rdp":
            # 1. Stop TermService immediately (closes port 3389 and disconnects active remote sessions)
            subprocess.run(['powershell', '-NoProfile', '-Command', 'Stop-Service TermService -Force; Set-Service TermService -StartupType Disabled'], capture_output=True)
            # 2. Registry: disable Remote Desktop in both Local and GPO Policy trees
            subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
            subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\Terminal Services" /v fDenyTSConnections /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
            # 3. Disable firewall rules
            subprocess.run(['netsh', 'advfirewall', 'firewall', 'set', 'rule', 'group=Remote Desktop', 'new', 'enable=No'], capture_output=True)
            subprocess.run(['netsh', 'advfirewall', 'firewall', 'set', 'rule', 'group=Remote Desktop (WebSocket)', 'new', 'enable=No'], capture_output=True)
            # 4. Add explicit high-priority BLOCK rule
            subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", "name=ITTOOL_BLOCK_RDP"], capture_output=True)
            subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule", "name=ITTOOL_BLOCK_RDP", "protocol=TCP", "localport=3389", "dir=in", "action=block"], capture_output=True)
            _run_bg(['powershell', '-NoProfile', '-Command', 'Set-NetFirewallRule -DisplayGroup "Remote Desktop*" -Enabled False -ErrorAction SilentlyContinue'])
            return {"success": True, "message": "🔒 Đã ĐÓNG & DỪNG Remote Desktop (RDP)! Cổng 3389 đã đóng và ngắt kết nối điều khiển từ xa ngay lập tức."}

        else:
            return {"success": False, "message": "Hành động không hợp lệ."}
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_firewall_rules_detail(filter_type="fps"):
    """Returns detailed list of firewall rules matching the filter_type."""
    try:
        res = subprocess.run(["netsh", "advfirewall", "firewall", "show", "rule", "name=all"], capture_output=True, text=True, timeout=10)
        rules = []
        for block in res.stdout.split("Rule Name:"):
            if not block.strip():
                continue
            r = {}
            lines = block.splitlines()
            r["name"] = lines[0].strip()
            for line in lines[1:]:
                line_s = line.strip()
                for field, key in [
                    ("Enabled:", "enabled"),
                    ("Direction:", "direction"),
                    ("Profiles:", "profiles"),
                    ("Grouping:", "grouping"),
                    ("LocalIP:", "local_ip"),
                    ("RemoteIP:", "remote_ip"),
                    ("Protocol:", "protocol"),
                    ("LocalPort:", "local_port"),
                    ("RemotePort:", "remote_port"),
                    ("Action:", "action")
                ]:
                    if line_s.startswith(field):
                        r[key] = line_s.split(":", 1)[1].strip()

            grp = r.get("grouping", "")
            name_u = r["name"].upper()
            is_fps = "File and Printer Sharing" in grp or "@FirewallAPI.dll,-28502" in grp or "@FirewallAPI.dll,-28672" in grp
            is_rdp = "Remote Desktop" in grp or "@FirewallAPI.dll,-28752" in grp or "@FirewallAPI.dll,-28753" in grp
            is_ping = "ECHO REQUEST" in name_u or "ICMP4-ERQ" in name_u or ("ICMP" in name_u and r.get("direction", "").lower() == "in")

            # Category detection for UX
            if "ECHO REQUEST" in name_u or "ICMP" in name_u:
                r["category"] = "ICMP Ping (Kiểm tra kết nối)"
            elif "SMB" in name_u:
                r["category"] = "SMB (Chia sẻ File & In)"
            elif "SPOOLER" in name_u or "RPC" in name_u:
                r["category"] = "Print Spooler RPC (Máy in)"
            elif "NB-" in name_u or "NETBIOS" in name_u:
                r["category"] = "NetBIOS (Định danh LAN)"
            elif "LLMNR" in name_u:
                r["category"] = "LLMNR (Dò tìm Hostname)"
            elif "REMOTE DESKTOP" in name_u or "RDP" in name_u:
                r["category"] = "Remote Desktop (RDP)"
            else:
                r["category"] = "Khác"

            if filter_type == "fps" and is_fps:
                rules.append(r)
            elif filter_type == "rdp" and is_rdp:
                rules.append(r)
            elif filter_type == "ping" and is_ping:
                rules.append(r)
            elif filter_type == "all":
                rules.append(r)

        if filter_type == "ping":
            try:
                ipsec_res = subprocess.run(["netsh", "ipsec", "static", "show", "policy", "name=ITTOOL_BLOCK_ICMP_POLICY"], capture_output=True, text=True, timeout=2)
                if "YES" in ipsec_res.stdout.upper() and "ITTOOL_BLOCK_ICMP_POLICY" in ipsec_res.stdout:
                    rules.insert(0, {
                        "name": "⚡ Windows IPSec Layer-3 Filter (ITTOOL_BLOCK_ICMP_POLICY)",
                        "enabled": "Yes",
                        "direction": "In",
                        "profiles": "Domain / Private / Public",
                        "grouping": "IPSec Security Policy",
                        "protocol": "ICMP",
                        "action": "Block",
                        "category": "IPSec Layer-3 Policy (Chặn triệt để tại Driver IP)"
                    })
            except Exception:
                pass
        elif filter_type == "fps":
            try:
                sc_res = subprocess.run(["sc", "query", "LanmanServer"], capture_output=True, text=True, timeout=2)
                is_running = "RUNNING" in sc_res.stdout.upper()
                rules.insert(0, {
                    "name": "📂 Dịch Vụ Máy Chủ Tệp Windows (LanmanServer Service)",
                    "enabled": "Yes" if is_running else "No",
                    "direction": "In",
                    "profiles": "Hệ thống mạng LAN",
                    "grouping": "Windows File Server",
                    "protocol": "TCP (Port 445, 139)",
                    "action": "Allow" if is_running else "Block",
                    "category": "Dịch vụ chia sẻ file LAN (Đang Bật)" if is_running else "Dịch vụ đã DỪNG (Ngắt mọi kết nối)"
                })
            except Exception:
                pass
        elif filter_type == "rdp":
            try:
                sc_res = subprocess.run(["sc", "query", "TermService"], capture_output=True, text=True, timeout=2)
                is_running = "RUNNING" in sc_res.stdout.upper()
                rules.insert(0, {
                    "name": "🖥️ Dịch Vụ Remote Desktop (TermService)",
                    "enabled": "Yes" if is_running else "No",
                    "direction": "In",
                    "profiles": "Hệ thống mạng LAN & Internet",
                    "grouping": "Windows Remote Desktop",
                    "protocol": "TCP / UDP (Port 3389)",
                    "action": "Allow" if is_running else "Block",
                    "category": "Dịch vụ RDP (Đang Lắng Nghe Cổng 3389)" if is_running else "Dịch vụ đã DỪNG (Đóng cổng 3389)"
                })
            except Exception:
                pass

        return {"success": True, "rules": rules, "total": len(rules)}
    except Exception as e:
        return {"success": False, "message": str(e), "rules": [], "total": 0}
