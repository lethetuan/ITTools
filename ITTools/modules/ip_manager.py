"""
IP Manager Module
Adapter IP, Edit IP, Copy MAC/Name, Subnet Calculator, IPv6 Disable
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import socket
import os
import sys
import threading
import json
import ipaddress
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS


# ── STANDALONE BACKEND API FUNCTIONS ─────────────────────────────────────

def prefix_to_mask(pfx):
    """Converts IPv4 prefix length (CIDR) to Subnet Mask string."""
    try:
        if not pfx or str(pfx).strip() in ["-", ""]:
            return "255.255.255.0"
        pfx_val = str(pfx).split(',')[0].strip()
        if pfx_val.isdigit():
            return str(ipaddress.IPv4Network(f"0.0.0.0/{pfx_val}").netmask)
    except Exception:
        pass
    return "255.255.255.0"


_cached_external_ip = "N/A"
_last_ext_ip_fetch = 0

def get_external_ip():
    """Fetches public external IP address with multi-provider fallback and caching."""
    global _cached_external_ip, _last_ext_ip_fetch
    import time
    import urllib.request
    import re

    now = time.time()
    if _cached_external_ip != "N/A" and (now - _last_ext_ip_fetch < 120):
        return {"success": True, "ip": _cached_external_ip}

    urls = ['https://api.ipify.org', 'https://icanhazip.com', 'https://ifconfig.me/ip']
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'ITTools/2026'})
            with urllib.request.urlopen(req, timeout=2.5) as response:
                ip = response.read().decode('utf-8', errors='ignore').strip()
                if ip and re.match(r'^[0-9.]+$', ip):
                    _cached_external_ip = ip
                    _last_ext_ip_fetch = now
                    return {"success": True, "ip": ip}
        except Exception:
            continue

    return {"success": False, "ip": _cached_external_ip or "N/A"}


def mask_to_prefix(mask_str):
    """Converts subnet mask (e.g. 255.255.255.0) to CIDR prefix length (e.g. 24)."""
    try:
        if mask_str and mask_str != '-':
            return str(ipaddress.IPv4Network(f"0.0.0.0/{mask_str}").prefixlen)
    except Exception:
        pass
    return "24"


def get_network_adapters():
    """Returns network adapters, local IP, and external IP instantly (0.03s)."""
    import re
    import subprocess
    import socket

    # 1. Local IP
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    # 2. External IP (cached or async)
    global _cached_external_ip
    ext_ip = _cached_external_ip if _cached_external_ip != "N/A" else "Đang lấy..."
    if _cached_external_ip == "N/A":
        threading.Thread(target=get_external_ip, daemon=True).start()

    # 3. Fast Network Adapters parsing via native ipconfig /all (30ms execution)
    adapters = []
    try:
        res = subprocess.run('ipconfig /all', capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5)
        text = res.stdout
        sections = re.split(r'\r?\n(?=[A-Za-z0-9].*adapter )', text)

        for sec in sections:
            lines = sec.strip().splitlines()
            if not lines:
                continue
            header = lines[0]
            m_name = re.search(r'adapter (.*?):', header)
            if not m_name:
                continue
            adapter_name = m_name.group(1).strip()

            is_disconnected = 'media disconnected' in sec.lower()

            m_ip = re.search(r'IPv4 Address[.\s]+:\s*([0-9.]+)', sec)
            ip = m_ip.group(1) if m_ip else '-'

            m_mask = re.search(r'Subnet Mask[.\s]+:\s*([0-9.]+)', sec)
            mask = m_mask.group(1) if m_mask else '-'
            prefix = mask_to_prefix(mask)

            m_gw = re.search(r'Default Gateway[.\s]+:\s*([0-9.]+)', sec)
            gw = m_gw.group(1) if m_gw else '-'

            m_mac = re.search(r'Physical Address[.\s]+:\s*([0-9A-Fa-f]{2}(?:-[0-9A-Fa-f]{2}){5})', sec)
            mac = m_mac.group(1) if m_mac else '-'

            m_dhcp = re.search(r'DHCP Enabled[.\s]+:\s*(Yes|No)', sec)
            dhcp = 'Enabled' if (m_dhcp and m_dhcp.group(1) == 'Yes') else 'Disabled'

            dns_servers = []
            sec_lines = sec.splitlines()
            for idx, l in enumerate(sec_lines):
                if 'DNS Servers' in l:
                    m_d = re.search(r'DNS Servers[.\s]+:\s*([0-9a-fA-F.:]+)', l)
                    if m_d:
                        dns_servers.append(m_d.group(1))
                    for next_line in sec_lines[idx+1:]:
                        next_line_s = next_line.strip()
                        if re.match(r'^[0-9a-fA-F.:]+$', next_line_s):
                            dns_servers.append(next_line_s)
                        else:
                            break
                    break

            dns_str = ', '.join(dns_servers) if dns_servers else '-'
            dns1 = dns_servers[0] if len(dns_servers) > 0 else ''
            dns2 = dns_servers[1] if len(dns_servers) > 1 else ''

            status = 'Disconnected' if is_disconnected else ('Up' if ip != '-' else 'Unknown')

            adapters.append({
                'name': adapter_name,
                'ip': ip,
                'prefix': prefix,
                'mask': mask,
                'gateway': gw,
                'dns': dns_str,
                'dns1': dns1,
                'dns2': dns2,
                'mac': mac,
                'status': status,
                'dhcp': dhcp
            })
    except Exception as e:
        print("Lỗi parse ipconfig:", e)

    # 4. Fallback via psutil if ipconfig returned no adapters
    if not adapters:
        try:
            import psutil
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            for name, addr_list in addrs.items():
                if 'loopback' in name.lower():
                    continue
                ipv4 = '-'
                mask = '-'
                mac = '-'
                for a in addr_list:
                    if a.family == socket.AF_INET:
                        ipv4 = a.address
                        mask = a.netmask or '-'
                    elif a.family == psutil.AF_LINK or getattr(socket, 'AF_LINK', None) == a.family:
                        mac = a.address or '-'
                st = stats.get(name)
                is_up = st.isup if st else False
                adapters.append({
                    'name': name,
                    'ip': ipv4,
                    'prefix': mask_to_prefix(mask),
                    'mask': mask,
                    'gateway': '-',
                    'dns': '-',
                    'dns1': '',
                    'dns2': '',
                    'mac': mac,
                    'status': 'Up' if is_up else 'Disconnected',
                    'dhcp': 'Unknown'
                })
        except Exception:
            pass

    return {
        "local_ip": local_ip,
        "external_ip": ext_ip,
        "adapters": adapters
    }


def apply_ip_settings(adapter, mode, ip="", mask="255.255.255.0", gateway="", dns1="", dns2=""):
    """Applies IP/DHCP settings to a specified network adapter via netsh."""
    if not adapter:
        return {"success": False, "message": "Chưa chọn card mạng (Adapter)."}

    try:
        if mode == "dhcp":
            cmd_ip = f'netsh interface ip set address name="{adapter}" source=dhcp'
            cmd_dns = f'netsh interface ip set dns name="{adapter}" source=dhcp'
            r1 = subprocess.run(cmd_ip, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            r2 = subprocess.run(cmd_dns, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            if r1.returncode != 0:
                err_msg = r1.stderr.strip() or r1.stdout.strip()
                return {"success": False, "message": f"Lỗi đặt IP DHCP cho '{adapter}': {err_msg}"}
            return {
                "success": True,
                "message": f"Đã chuyển card mạng '{adapter}' sang chế độ DHCP (Tự động) thành công!"
            }
        else:
            if not ip or not mask:
                return {"success": False, "message": "Vui lòng nhập đầy đủ Địa chỉ IP và Subnet Mask!"}

            cmd_ip = f'netsh interface ip set address name="{adapter}" static {ip} {mask}'
            if gateway and gateway.strip():
                cmd_ip += f' {gateway.strip()}'

            r_ip = subprocess.run(cmd_ip, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            if r_ip.returncode != 0:
                err_msg = r_ip.stderr.strip() or r_ip.stdout.strip()
                return {"success": False, "message": f"Lỗi đặt IP tĩnh cho '{adapter}': {err_msg}"}

            if dns1 and dns1.strip():
                cmd_dns1 = f'netsh interface ip set dns name="{adapter}" static {dns1.strip()}'
                subprocess.run(cmd_dns1, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
                if dns2 and dns2.strip():
                    cmd_dns2 = f'netsh interface ip add dns name="{adapter}" {dns2.strip()} index=2'
                    subprocess.run(cmd_dns2, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')

            return {
                "success": True,
                "message": f"Đã cài đặt thành công IP Tĩnh {ip} cho card mạng '{adapter}'!"
            }
    except Exception as e:
        return {"success": False, "message": f"Ngoại lệ: {str(e)}"}


def calculate_subnet(ip_str, cidr_val):
    """Calculates IPv4 subnet information."""
    try:
        cidr = int(cidr_val)
        network = ipaddress.IPv4Network(f"{ip_str.strip()}/{cidr}", strict=False)

        first_byte = int(str(network.network_address).split('.')[0])
        ip_class = 'Class A' if first_byte < 128 else ('Class B' if first_byte < 192 else ('Class C' if first_byte < 224 else ('Class D (Multicast)' if first_byte < 240 else 'Class E (Reserved)')))

        return {
            "success": True,
            "data": {
                "network_address": str(network.network_address),
                "broadcast_address": str(network.broadcast_address),
                "subnet_mask": str(network.netmask),
                "wildcard_mask": str(network.hostmask),
                "cidr_notation": str(network),
                "first_host": str(network.network_address + 1) if network.num_addresses > 2 else str(network.network_address),
                "last_host": str(network.broadcast_address - 1) if network.num_addresses > 2 else str(network.broadcast_address),
                "total_hosts": f"{network.num_addresses:,}",
                "usable_hosts": f"{max(0, network.num_addresses - 2):,}",
                "ip_class": ip_class,
                "type": "Private" if network.is_private else "Public"
            }
        }
    except Exception as e:
        return {"success": False, "message": f"Lỗi tính Subnet: {str(e)}"}


def get_ipv6_status():
    """Checks IPv6 status across all adapters."""
    try:
        res = subprocess.run(
            ['powershell', '-Command',
             '(Get-NetAdapterBinding -ComponentID ms_tcpip6 | Where-Object Enabled -eq $true).Count'],
            capture_output=True, text=True, timeout=8
        )
        count_str = res.stdout.strip()
        count = int(count_str) if count_str and count_str.isdigit() else 0
        enabled = count > 0
        return {
            "success": True,
            "enabled": enabled,
            "count": count,
            "text": f"✅ IPv6 Đang Bật ({count} adapters)" if enabled else "🚫 IPv6 Đã Tắt"
        }
    except Exception as e:
        return {"success": False, "message": str(e), "enabled": False, "count": 0, "text": "🚫 Không thể kiểm tra IPv6"}


def set_ipv6_status(enable):
    """Enables or disables IPv6 across all adapters."""
    try:
        ps_cmd = 'Enable-NetAdapterBinding -Name "*" -ComponentID ms_tcpip6' if enable else 'Disable-NetAdapterBinding -Name "*" -ComponentID ms_tcpip6'
        subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, text=True, timeout=10)
        status = get_ipv6_status()
        return {
            "success": True,
            "message": f"Đã {'BẬT' if enable else 'TẮT'} IPv6 thành công!",
            "status": status
        }
    except Exception as e:
        return {"success": False, "message": f"Lỗi đặt trạng thái IPv6: {str(e)}"}


class IPManager:
    def __init__(self, parent):
        self.parent = parent
        self.parent.geometry('750x650')
        self.parent.configure(bg=COLORS['bg'])
        self.setup_ui()
        threading.Thread(target=self.load_adapters, daemon=True).start()

    def setup_ui(self):
        hdr = tk.Frame(self.parent, bg=COLORS['bg_header'])
        hdr.pack(fill='x')
        tk.Label(hdr, text='🌐  IP Manager', font=FONTS['large'],
                  bg=COLORS['bg_header'], fg='white', pady=10).pack(side='left', padx=15)

        self.nb = ttk.Notebook(self.parent)
        self.nb.pack(fill='both', expand=True, padx=8, pady=8)

        # Tab 1: Adapter List
        self.adapter_frame = tk.Frame(self.nb, bg=COLORS['bg'])
        self.nb.add(self.adapter_frame, text='🔌 Adapters')
        self._build_adapter_tab()

        # Tab 2: Edit IP
        self.edit_frame = tk.Frame(self.nb, bg=COLORS['bg'])
        self.nb.add(self.edit_frame, text='✏️ Edit IP')
        self._build_edit_tab()

        # Tab 3: Subnet Calculator
        self.subnet_frame = tk.Frame(self.nb, bg=COLORS['bg'])
        self.nb.add(self.subnet_frame, text='🧮 Subnet Calculator')
        self._build_subnet_tab()

        # Tab 4: IPv6
        self.ipv6_frame = tk.Frame(self.nb, bg=COLORS['bg'])
        self.nb.add(self.ipv6_frame, text='🔵 IPv6')
        self._build_ipv6_tab()

    def _build_adapter_tab(self):
        bar = tk.Frame(self.adapter_frame, bg=COLORS['bg_dark'])
        bar.pack(fill='x', pady=2)
        for text, cmd, color in [
            ('🔄 Refresh', self.load_adapters, COLORS['info']),
            ('📋 Copy IP', self.copy_ip, COLORS['accent']),
            ('📋 Copy MAC', self.copy_mac, '#8E44AD'),
            ('📋 Copy Name', self.copy_name, COLORS['warning']),
        ]:
            tk.Button(bar, text=text, font=FONTS['small'],
                       bg=color, fg='white', relief='flat',
                       padx=8, pady=3, cursor='hand2',
                       command=cmd).pack(side='left', padx=2, pady=2)

        cols = ('Adapter', 'IP Address', 'Subnet Mask', 'Gateway', 'MAC', 'Status')
        self.adapter_tree = ttk.Treeview(self.adapter_frame,
                                          columns=cols, show='headings',
                                          selectmode='browse')
        widths = [180, 130, 130, 130, 140, 70]
        for col, w in zip(cols, widths):
            self.adapter_tree.heading(col, text=col, anchor='w')
            self.adapter_tree.column(col, width=w, minwidth=50)

        vsb = ttk.Scrollbar(self.adapter_frame, command=self.adapter_tree.yview)
        hsb = ttk.Scrollbar(self.adapter_frame, orient='horizontal',
                              command=self.adapter_tree.xview)
        self.adapter_tree.configure(yscrollcommand=vsb.set,
                                     xscrollcommand=hsb.set)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.adapter_tree.pack(fill='both', expand=True, padx=5, pady=5)

        self.adapter_tree.tag_configure('connected', foreground='#27AE60')
        self.adapter_tree.tag_configure('disconnected', foreground='#E74C3C')

        ip_frame = tk.LabelFrame(self.adapter_frame, text='  Your IP  ',
                                  font=FONTS['subtitle'], bg=COLORS['bg'])
        ip_frame.pack(fill='x', padx=5, pady=3)
        row = tk.Frame(ip_frame, bg=COLORS['bg'])
        row.pack(padx=10, pady=5)

        self.local_ip_var = tk.StringVar(value='Loading...')
        self.ext_ip_var = tk.StringVar(value='Loading...')

        tk.Label(row, text='Local IP:', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left', padx=5)
        tk.Label(row, textvariable=self.local_ip_var, font=FONTS['subtitle'],
                  bg=COLORS['bg'], fg=COLORS['info']).pack(side='left', padx=3)
        tk.Label(row, text='  External IP:', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left', padx=5)
        tk.Label(row, textvariable=self.ext_ip_var, font=FONTS['subtitle'],
                  bg=COLORS['bg'], fg=COLORS['accent']).pack(side='left', padx=3)

    def _build_edit_tab(self):
        form = tk.LabelFrame(self.edit_frame, text='  Configure IP Address  ',
                              font=FONTS['subtitle'], bg=COLORS['bg'],
                              relief='groove')
        form.pack(fill='x', padx=15, pady=15)

        tk.Label(form, text='Adapter:', font=FONTS['normal'],
                  bg=COLORS['bg']).grid(row=0, column=0, padx=10, pady=8, sticky='w')
        self.edit_adapter_var = tk.StringVar()
        self.adapter_combo = ttk.Combobox(form, textvariable=self.edit_adapter_var,
                                           font=FONTS['normal'], width=35, state='readonly')
        self.adapter_combo.grid(row=0, column=1, columnspan=2, padx=5, pady=8, sticky='ew')

        self.ip_mode = tk.StringVar(value='static')
        tk.Radiobutton(form, text='DHCP (Automatic)', value='dhcp',
                        variable=self.ip_mode, font=FONTS['normal'],
                        bg=COLORS['bg'], selectcolor=COLORS['selected']).grid(
            row=1, column=0, columnspan=2, padx=10, pady=3, sticky='w')
        tk.Radiobutton(form, text='Static IP', value='static',
                        variable=self.ip_mode, font=FONTS['normal'],
                        bg=COLORS['bg'], selectcolor=COLORS['selected']).grid(
            row=1, column=2, padx=10, pady=3, sticky='w')

        fields = [
            ('IP Address:', 'ip'), ('Subnet Mask:', 'mask'),
            ('Default Gateway:', 'gateway'),
            ('DNS Primary:', 'dns1'), ('DNS Secondary:', 'dns2'),
        ]
        self.ip_fields = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(form, text=label, font=FONTS['normal'],
                      bg=COLORS['bg']).grid(row=2+i, column=0, padx=10, pady=5, sticky='w')
            var = tk.StringVar()
            entry = tk.Entry(form, textvariable=var, font=FONTS['normal'], width=25)
            entry.grid(row=2+i, column=1, columnspan=2, padx=5, pady=5, sticky='ew')
            self.ip_fields[key] = var

        preset_frame = tk.LabelFrame(self.edit_frame, text='  Quick Presets  ',
                                      font=FONTS['subtitle'], bg=COLORS['bg'])
        preset_frame.pack(fill='x', padx=15, pady=5)
        presets = [
            ('🏠 Home (192.168.1.x)', '192.168.1.', '255.255.255.0', '192.168.1.1', '8.8.8.8'),
            ('🏢 Office (192.168.0.x)', '192.168.0.', '255.255.255.0', '192.168.0.1', '8.8.8.8'),
            ('🌐 Google DNS', '', '', '', '8.8.8.8', '8.8.4.4'),
            ('🔵 Cloudflare DNS', '', '', '', '1.1.1.1', '1.0.0.1'),
        ]
        for i, preset in enumerate(presets):
            tk.Button(preset_frame, text=preset[0], font=FONTS['small'],
                       bg=COLORS['btn_bg'], fg=COLORS['text'],
                       relief='groove', padx=8, pady=3, cursor='hand2',
                       command=lambda p=preset: self.apply_preset(p)
                       ).grid(row=0, column=i, padx=5, pady=5)

        btn_frame = tk.Frame(self.edit_frame, bg=COLORS['bg'])
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text='✅ Apply IP Settings',
                   font=FONTS['subtitle'], bg=COLORS['accent'], fg='white',
                   relief='flat', padx=20, pady=8, cursor='hand2',
                   command=self.apply_ip).pack(side='left', padx=5)
        tk.Button(btn_frame, text='🔄 Set DHCP',
                   font=FONTS['subtitle'], bg=COLORS['info'], fg='white',
                   relief='flat', padx=20, pady=8, cursor='hand2',
                   command=self.set_dhcp).pack(side='left', padx=5)

    def apply_preset(self, preset):
        if len(preset) > 2:
            self.ip_fields['mask'].set(preset[2])
        if len(preset) > 3:
            self.ip_fields['gateway'].set(preset[3])
        if len(preset) > 4:
            self.ip_fields['dns1'].set(preset[4])
        if len(preset) > 5:
            self.ip_fields['dns2'].set(preset[5])

    def _build_subnet_tab(self):
        frame = tk.LabelFrame(self.subnet_frame, text='  Subnet Calculator  ',
                               font=FONTS['subtitle'], bg=COLORS['bg'],
                               relief='groove')
        frame.pack(fill='x', padx=15, pady=15)

        tk.Label(frame, text='IP Address:', font=FONTS['normal'],
                  bg=COLORS['bg']).grid(row=0, column=0, padx=10, pady=8, sticky='w')
        self.subnet_ip = tk.Entry(frame, font=FONTS['normal'], width=20)
        self.subnet_ip.insert(0, '192.168.1.0')
        self.subnet_ip.grid(row=0, column=1, padx=5, pady=8, sticky='ew')

        tk.Label(frame, text='Prefix / CIDR:', font=FONTS['normal'],
                  bg=COLORS['bg']).grid(row=1, column=0, padx=10, pady=5, sticky='w')
        self.subnet_cidr = tk.Spinbox(frame, from_=0, to=32, font=FONTS['normal'], width=6)
        self.subnet_cidr.delete(0, 'end')
        self.subnet_cidr.insert(0, '24')
        self.subnet_cidr.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        tk.Button(frame, text='🧮 Calculate', font=FONTS['subtitle'],
                   bg=COLORS['accent'], fg='white', relief='flat',
                   padx=15, pady=5, cursor='hand2',
                   command=self.calculate_subnet_gui).grid(
            row=2, column=0, columnspan=2, pady=10)

        self.subnet_result = tk.Text(self.subnet_frame,
                                      font=('Consolas', 10),
                                      bg='#1E1E1E', fg='#D4D4D4',
                                      height=15, relief='flat',
                                      padx=10, pady=10)
        self.subnet_result.pack(fill='both', expand=True, padx=15, pady=5)

    def calculate_subnet_gui(self):
        res = calculate_subnet(self.subnet_ip.get(), self.subnet_cidr.get())
        if res["success"]:
            self.subnet_result.configure(state='normal')
            self.subnet_result.delete('1.0', 'end')
            for key, val in res["data"].items():
                self.subnet_result.insert('end', f'  {key:<25} : {val}\n')
            self.subnet_result.configure(state='disabled')

    def _build_ipv6_tab(self):
        frame = tk.Frame(self.ipv6_frame, bg=COLORS['bg'])
        frame.pack(fill='both', expand=True, padx=20, pady=20)

        tk.Label(frame, text='IPv6 Management',
                  font=FONTS['large'], bg=COLORS['bg'],
                  fg=COLORS['text']).pack(pady=10)

        self.ipv6_status_var = tk.StringVar(value='Checking...')
        tk.Label(frame, textvariable=self.ipv6_status_var,
                  font=FONTS['subtitle'], bg=COLORS['bg'],
                  fg=COLORS['info']).pack(pady=5)

        btn_frame = tk.Frame(frame, bg=COLORS['bg'])
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text='✅ Enable IPv6',
                   font=FONTS['subtitle'], bg=COLORS['accent'], fg='white',
                   relief='flat', padx=20, pady=10, cursor='hand2',
                   command=self.enable_ipv6).pack(side='left', padx=10)
        tk.Button(btn_frame, text='🚫 Disable IPv6',
                   font=FONTS['subtitle'], bg=COLORS['danger'], fg='white',
                   relief='flat', padx=20, pady=10, cursor='hand2',
                   command=self.disable_ipv6).pack(side='left', padx=10)

        self.check_ipv6_status()

    def load_adapters(self):
        info = get_network_adapters()
        self.local_ip_var.set(info["local_ip"])
        self.ext_ip_var.set(info["external_ip"])

        self.adapter_tree.delete(*self.adapter_tree.get_children())
        names = []
        for a in info["adapters"]:
            names.append(a["name"])
            tag = 'connected' if a["status"] == 'Up' else 'disconnected'
            self.adapter_tree.insert('', 'end',
                                      values=(a["name"], a["ip"], a["prefix"], a["gateway"], a["mac"], a["status"]),
                                      tags=(tag,))
        self.adapter_combo['values'] = names
        if names:
            self.adapter_combo.set(names[0])

    def copy_ip(self):
        sel = self.adapter_tree.selection()
        if sel:
            ip = self.adapter_tree.item(sel[0], 'values')[1]
            self.parent.clipboard_clear()
            self.parent.clipboard_append(ip)
            messagebox.showinfo('Copied', f'IP đã copy: {ip}')

    def copy_mac(self):
        sel = self.adapter_tree.selection()
        if sel:
            mac = self.adapter_tree.item(sel[0], 'values')[4]
            self.parent.clipboard_clear()
            self.parent.clipboard_append(mac)
            messagebox.showinfo('Copied', f'MAC đã copy: {mac}')

    def copy_name(self):
        sel = self.adapter_tree.selection()
        if sel:
            name = self.adapter_tree.item(sel[0], 'values')[0]
            self.parent.clipboard_clear()
            self.parent.clipboard_append(name)
            messagebox.showinfo('Copied', f'Name đã copy: {name}')

    def apply_ip(self):
        adapter = self.edit_adapter_var.get()
        mode = self.ip_mode.get()
        res = apply_ip_settings(
            adapter=adapter,
            mode=mode,
            ip=self.ip_fields['ip'].get(),
            mask=self.ip_fields['mask'].get(),
            gateway=self.ip_fields['gateway'].get(),
            dns1=self.ip_fields['dns1'].get(),
            dns2=self.ip_fields['dns2'].get()
        )
        if res["success"]:
            messagebox.showinfo('Success', res["message"])
            threading.Thread(target=self.load_adapters, daemon=True).start()
        else:
            messagebox.showerror('Error', res["message"])

    def set_dhcp(self):
        adapter = self.edit_adapter_var.get()
        res = apply_ip_settings(adapter, "dhcp")
        messagebox.showinfo('Success', res["message"])
        threading.Thread(target=self.load_adapters, daemon=True).start()

    def check_ipv6_status(self):
        st = get_ipv6_status()
        self.ipv6_status_var.set(st["text"])

    def enable_ipv6(self):
        res = set_ipv6_status(True)
        messagebox.showinfo('IPv6', res["message"])
        self.check_ipv6_status()

    def disable_ipv6(self):
        if messagebox.askyesno('Confirm', 'Tắt IPv6 trên tất cả adapter?'):
            res = set_ipv6_status(False)
            messagebox.showinfo('IPv6', res["message"])
            self.check_ipv6_status()
