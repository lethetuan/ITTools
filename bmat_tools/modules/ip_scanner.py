"""
IP Scanner Module
Scan network for IP, Name, MAC, HTTP/HTTPS, Brand, Ping
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import socket
import threading
import os
import sys
import ipaddress
import queue
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS


# MAC vendor prefix lookup (partial)
MAC_VENDORS = {
    'FC:AA:14': 'TP-Link', 'B0:BE:76': 'TP-Link', 'C0:4A:00': 'TP-Link', '74:38:B7': 'TP-Link',
    '00:50:56': 'VMware', '00:0C:29': 'VMware', '00:1C:14': 'VMware',
    'AC:BC:32': 'Apple', '00:17:F2': 'Apple', '00:1E:52': 'Apple',
    '00:1A:A0': 'Dell', '00:14:22': 'Dell', 'F8:DB:88': 'Dell',
    '00:23:AE': 'Cisco', '00:1B:D4': 'Cisco', '24:01:C7': 'Cisco',
    'A4:2B:B0': 'ASUS', '00:E0:4C': 'Realtek', '94:DE:80': 'Intel',
    'B4:2E:99': 'HP', '3C:D9:2B': 'HP', '00:26:55': 'Samsung',
    'D8:5D:E2': 'Xiaomi', '28:6C:07': 'Xiaomi',
}


def get_mac_vendor(mac):
    if not mac: return 'Unknown'
    prefix = mac[:8].upper().replace('-', ':')
    for k, v in MAC_VENDORS.items():
        if prefix.startswith(k):
            return v
    return 'Unknown'


def get_mac_from_arp(ip):
    try:
        result = subprocess.run(['arp', '-a', ip], capture_output=True, text=True, timeout=3)
        for line in result.stdout.splitlines():
            if ip in line:
                parts = line.split()
                for part in parts:
                    if '-' in part and len(part) == 17:
                        return part.upper()
    except Exception:
        pass
    return ''


def check_http(ip, port=80, timeout=1):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        s.close()
        return True
    except Exception:
        return False


def ping_host(ip, timeout=400):
    try:
        result = subprocess.run(
            ['ping', '-n', '1', '-w', str(timeout), ip],
            capture_output=True, text=True
        )
        if 'TTL=' in result.stdout or 'ttl=' in result.stdout:
            for part in result.stdout.split():
                if 'ms' in part.lower() and ('=' in part or '<' in part):
                    return True, part.split('=')[-1]
            return True, '<1ms'
        return False, ''
    except Exception:
        return False, ''


def get_hostname(ip, timeout=1):
    try:
        socket.setdefaulttimeout(timeout)
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return ''


# ── STANDALONE BACKEND API FUNCTIONS ─────────────────────────────────────

def get_local_subnet_range():
    """Detects current active IPv4 address and default subnet range."""
    local_ip = "192.168.1.100"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    parts = local_ip.split('.')
    if len(parts) == 4:
        base = f"{parts[0]}.{parts[1]}.{parts[2]}"
        return {
            "local_ip": local_ip,
            "subnet": f"{base}.0/24",
            "start_ip": f"{base}.1",
            "end_ip": f"{base}.254"
        }
    return {
        "local_ip": local_ip,
        "subnet": "192.168.1.0/24",
        "start_ip": "192.168.1.1",
        "end_ip": "192.168.1.254"
    }


def get_all_arp_macs():
    """Returns map of IP -> MAC address from ARP cache."""
    arp_map = {}
    try:
        res = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=5)
        for line in res.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                ip = parts[0]
                mac = parts[1]
                if '-' in mac and len(mac) == 17:
                    arp_map[ip] = mac.upper()
    except Exception:
        pass
    return arp_map


def scan_lan_network(subnet_str="", ip_start="", ip_end="", check_ping=True, check_hostname=True, check_mac=True, check_http_port=True, check_https_port=True, max_threads=50):
    """Scans LAN network IP range with multi-threaded sweeps."""
    ip_list = []
    if subnet_str and '/' in subnet_str:
        try:
            network = ipaddress.IPv4Network(subnet_str.strip(), strict=False)
            ip_list = [str(ip) for ip in list(network.hosts())[:1000]]
        except Exception:
            pass

    if not ip_list and ip_start and ip_end:
        try:
            start = ipaddress.IPv4Address(ip_start.strip())
            end = ipaddress.IPv4Address(ip_end.strip())
            ip_list = [str(ipaddress.IPv4Address(i)) for i in range(int(start), int(end) + 1)]
        except Exception:
            pass

    if not ip_list:
        default_range = get_local_subnet_range()
        network = ipaddress.IPv4Network(default_range["subnet"], strict=False)
        ip_list = [str(ip) for ip in list(network.hosts())[:254]]

    arp_map = get_all_arp_macs() if check_mac else {}
    results = []
    res_queue = queue.Queue()

    def worker(ip):
        alive, ping_time = ping_host(ip, timeout=400)
        if alive:
            hostname = get_hostname(ip, timeout=1) if check_hostname else ""
            mac = arp_map.get(ip) or (get_mac_from_arp(ip) if check_mac else "")
            brand = get_mac_vendor(mac) if mac else ""
            http_open = check_http(ip, 80, timeout=1) if check_http_port else False
            https_open = check_http(ip, 443, timeout=1) if check_https_port else False

            res_queue.put({
                "ip": ip,
                "hostname": hostname or "-",
                "mac": mac or "-",
                "brand": brand or "Unknown",
                "ping": ping_time or "<1ms",
                "http": http_open,
                "https": https_open,
                "status": "Online"
            })

    threads = []
    thread_limit = min(max_threads, 100)

    for ip in ip_list:
        t = threading.Thread(target=worker, args=(ip,), daemon=True)
        threads.append(t)
        t.start()
        while len([x for x in threads if x.is_alive()]) >= thread_limit:
            time.sleep(0.02)

    for t in threads:
        t.join(timeout=4)

    while not res_queue.empty():
        results.append(res_queue.get_nowait())

    def ip_sort_key(item):
        try:
            return int(ipaddress.IPv4Address(item["ip"]))
        except Exception:
            return 0

    return sorted(results, key=ip_sort_key)


class IPScanner:
    def __init__(self, parent):
        self.parent = parent
        self.parent.geometry('900x620')
        self.parent.configure(bg=COLORS['bg'])
        self.scanning = False
        self.scan_queue = queue.Queue()
        self.results = []
        self.setup_ui()

    def setup_ui(self):
        hdr = tk.Frame(self.parent, bg=COLORS['bg_header'])
        hdr.pack(fill='x')
        tk.Label(hdr, text='🔍  IP Network Scanner', font=FONTS['large'],
                  bg=COLORS['bg_header'], fg='white', pady=10).pack(side='left', padx=15)

        config_frame = tk.LabelFrame(self.parent, text='  Scan Configuration  ',
                                      font=FONTS['subtitle'], bg=COLORS['bg'],
                                      relief='groove')
        config_frame.pack(fill='x', padx=10, pady=8)

        row1 = tk.Frame(config_frame, bg=COLORS['bg'])
        row1.pack(padx=10, pady=5, fill='x')

        tk.Label(row1, text='IP Range Start:', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left', padx=5)
        self.ip_start = tk.Entry(row1, font=FONTS['normal'], width=16)
        self.ip_start.insert(0, '192.168.1.1')
        self.ip_start.pack(side='left', padx=3)

        tk.Label(row1, text='IP Range End:', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left', padx=8)
        self.ip_end = tk.Entry(row1, font=FONTS['normal'], width=16)
        self.ip_end.insert(0, '192.168.1.254')
        self.ip_end.pack(side='left', padx=3)

        tk.Label(row1, text='OR Subnet:', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left', padx=8)
        self.subnet_entry = tk.Entry(row1, font=FONTS['normal'], width=18)
        self.subnet_entry.insert(0, '192.168.1.0/24')
        self.subnet_entry.pack(side='left', padx=3)

        row2 = tk.Frame(config_frame, bg=COLORS['bg'])
        row2.pack(padx=10, pady=5, fill='x')

        self.opt_ping = tk.BooleanVar(value=True)
        self.opt_hostname = tk.BooleanVar(value=True)
        self.opt_mac = tk.BooleanVar(value=True)
        self.opt_http = tk.BooleanVar(value=True)
        self.opt_https = tk.BooleanVar(value=True)

        for text, var in [
            ('Ping', self.opt_ping), ('Hostname', self.opt_hostname),
            ('MAC', self.opt_mac), ('HTTP', self.opt_http), ('HTTPS', self.opt_https)
        ]:
            tk.Checkbutton(row2, text=text, variable=var,
                            font=FONTS['normal'], bg=COLORS['bg'],
                            selectcolor=COLORS['selected']).pack(side='left', padx=8)

        tk.Label(row2, text='Threads:', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left', padx=8)
        self.thread_count = tk.Spinbox(row2, from_=1, to=100,
                                        font=FONTS['normal'], width=5)
        self.thread_count.delete(0, 'end')
        self.thread_count.insert(0, '50')
        self.thread_count.pack(side='left', padx=3)

        btn_frame = tk.Frame(config_frame, bg=COLORS['bg'])
        btn_frame.pack(padx=10, pady=5)
        self.btn_scan = tk.Button(btn_frame, text='▶ Start Scan',
                                   font=FONTS['subtitle'],
                                   bg=COLORS['accent'], fg='white',
                                   relief='flat', padx=20, pady=6,
                                   cursor='hand2', command=self.start_scan)
        self.btn_scan.pack(side='left', padx=5)

        prog_frame = tk.Frame(self.parent, bg=COLORS['bg'])
        prog_frame.pack(fill='x', padx=10, pady=2)
        self.progress = ttk.Progressbar(prog_frame, mode='determinate', length=500)
        self.progress.pack(side='left', padx=5)
        self.status_var = tk.StringVar(value='Ready to scan')
        tk.Label(prog_frame, textvariable=self.status_var,
                  font=FONTS['small'], bg=COLORS['bg'],
                  fg=COLORS['text_light']).pack(side='left', padx=10)

        tree_frame = tk.Frame(self.parent, bg=COLORS['bg'])
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)

        cols = ('IP', 'Hostname', 'MAC', 'Brand', 'Ping', 'HTTP', 'HTTPS', 'Status')
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings',
                                  selectmode='browse')
        widths = [120, 160, 140, 100, 60, 50, 55, 70]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col, anchor='w')
            self.tree.column(col, width=w, minwidth=40)

        vsb = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        vsb.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(fill='both', expand=True)

        self.tree.tag_configure('online', foreground='#27AE60')
        self.tree.tag_configure('offline', foreground='#E74C3C')

    def start_scan(self):
        def run():
            res = scan_lan_network(subnet_str=self.subnet_entry.get().strip())
            self.tree.delete(*self.tree.get_children())
            for item in res:
                self.tree.insert('', 'end', values=(item['ip'], item['hostname'], item['mac'], item['brand'], item['ping'], '✅' if item['http'] else '❌', '✅' if item['https'] else '❌', item['status']), tags=('online',))
        threading.Thread(target=run, daemon=True).start()
