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
    from concurrent.futures import ThreadPoolExecutor

    profiles = {"domain": False, "private": False, "public": False}
    policies = {"domain": "BlockInbound", "private": "BlockInbound", "public": "BlockInbound"}
    inbound_allowed = False
    fps_active = False
    fps_count = 0
    rdp_active = False
    rdp_count = 0

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
        nonlocal fps_active, fps_count, rdp_active, rdp_count
        try:
            res = subprocess.run(["netsh", "advfirewall", "firewall", "show", "rule", "name=all"], capture_output=True, text=True, timeout=8)
            for block in res.stdout.split("Rule Name:"):
                if not block.strip():
                    continue
                is_enabled = False
                is_fps = False
                is_rdp = False
                for line in block.splitlines():
                    line_s = line.strip()
                    if line_s.startswith("Enabled:"):
                        is_enabled = (line_s.split(":", 1)[1].strip().lower() == "yes")
                    elif line_s.startswith("Grouping:"):
                        grp = line_s.split(":", 1)[1].strip()
                        if "File and Printer Sharing" in grp or "@FirewallAPI.dll,-28502" in grp or "@FirewallAPI.dll,-28672" in grp:
                            is_fps = True
                        elif "Remote Desktop" in grp or "@FirewallAPI.dll,-28752" in grp or "@FirewallAPI.dll,-28753" in grp:
                            is_rdp = True
                if is_enabled:
                    if is_fps:
                        fps_count += 1
                    if is_rdp:
                        rdp_count += 1
            fps_active = fps_count > 0
            rdp_active = rdp_count > 0
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
        "rdp_count": rdp_count
    }


def set_firewall_action(action):
    """Executes firewall enable, disable, reset, or rule commands."""
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
            # Tối ưu an toàn tuyệt đối: Chỉ mở Inbound cho Private và Domain, loại bỏ hoàn toàn Public và Outbound
            ps_enable = (
                "$privRules = @('FPS-SMB-In-TCP','FPS-SpoolSvc-In-TCP','FPS-SpoolWorker-In-TCP','FPS-RPCSS-In-TCP','FPS-NB_Name-In-UDP','FPS-NB_Datagram-In-UDP','FPS-NB_Session-In-TCP','FPS-ICMP4-ERQ-In'); "
                "foreach ($r in $privRules) { Set-NetFirewallRule -Name $r -Profile Private -Enabled True }; "
                "$domRules = @('FPS-SMB-In-TCP-NoScope','FPS-SpoolSvc-In-TCP-NoScope','FPS-SpoolWorker-In-TCP-NoScope','FPS-RPCSS-In-TCP-NoScope','FPS-NB_Name-In-UDP-NoScope','FPS-NB_Datagram-In-UDP-NoScope','FPS-NB_Session-In-TCP-NoScope','FPS-ICMP4-ERQ-In-NoScope'); "
                "foreach ($r in $domRules) { Set-NetFirewallRule -Name $r -Profile Domain -Enabled True }"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_enable], capture_output=True, text=True)
            return {"success": True, "message": "📂 Đã kích hoạt 16 quy tắc File & Printer Sharing an toàn (Chỉ chiều IN trên Private & Domain, đóng hoàn toàn Public & Outbound)!"}
        elif action == "disable_sharing":
            subprocess.run('netsh advfirewall firewall set rule group="File and Printer Sharing" new enable=No', shell=True)
            subprocess.run('netsh advfirewall firewall set rule group="File and Printer Sharing (Restrictive)" new enable=No', shell=True)
            return {"success": True, "message": "🔒 Đã tắt/chặn toàn bộ Firewall cho File Sharing & Máy In!"}
        elif action == "enable_rdp":
            subprocess.run('netsh advfirewall firewall set rule group="Remote Desktop" new enable=Yes', shell=True)
            subprocess.run('netsh advfirewall firewall set rule group="Remote Desktop (WebSocket)" new enable=Yes', shell=True)
            return {"success": True, "message": "🖥️ Đã mở Firewall cho Remote Desktop (RDP)!"}
        elif action == "disable_rdp":
            subprocess.run('netsh advfirewall firewall set rule group="Remote Desktop" new enable=No', shell=True)
            subprocess.run('netsh advfirewall firewall set rule group="Remote Desktop (WebSocket)" new enable=No', shell=True)
            return {"success": True, "message": "🔒 Đã tắt/chặn Firewall cho Remote Desktop (RDP)!"}
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
            is_fps = "File and Printer Sharing" in grp or "@FirewallAPI.dll,-28502" in grp or "@FirewallAPI.dll,-28672" in grp
            is_rdp = "Remote Desktop" in grp or "@FirewallAPI.dll,-28752" in grp or "@FirewallAPI.dll,-28753" in grp

            # Category detection for UX
            name_u = r["name"].upper()
            if "SMB" in name_u:
                r["category"] = "SMB (Chia sẻ File & In)"
            elif "SPOOLER" in name_u or "RPC" in name_u:
                r["category"] = "Print Spooler RPC (Máy in)"
            elif "NB-" in name_u or "NETBIOS" in name_u:
                r["category"] = "NetBIOS (Định danh LAN)"
            elif "LLMNR" in name_u:
                r["category"] = "LLMNR (Dò tìm Hostname)"
            elif "ECHO REQUEST" in name_u or "ICMP" in name_u:
                r["category"] = "ICMP Ping (Kiểm tra kết nối)"
            elif "REMOTE DESKTOP" in name_u or "RDP" in name_u:
                r["category"] = "Remote Desktop (RDP)"
            else:
                r["category"] = "Khác"

            if filter_type == "fps" and is_fps:
                rules.append(r)
            elif filter_type == "rdp" and is_rdp:
                rules.append(r)
            elif filter_type == "all":
                rules.append(r)

        return {"success": True, "rules": rules, "total": len(rules)}
    except Exception as e:
        return {"success": False, "message": str(e), "rules": [], "total": 0}
