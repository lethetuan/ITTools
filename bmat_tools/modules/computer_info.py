"""
Computer Info Module
Shows RAM, CPU, GPU, HDD/SSD, Windows version, Battery, LAN info
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import os
import sys
import threading
import platform
import ctypes

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS


def run_wmic(query):
    try:
        result = subprocess.run(
            ['wmic'] + query.split() + ['get', '/format:list'],
            capture_output=True, text=True, timeout=10
        )
        data = {}
        for line in result.stdout.splitlines():
            if '=' in line:
                k, _, v = line.partition('=')
                data[k.strip()] = v.strip()
        return data
    except:
        return {}


def run_ps(cmd):
    try:
        result = subprocess.run(
            ['powershell', '-Command', cmd],
            capture_output=True, text=True, timeout=15
        )
        return result.stdout.strip()
    except:
        return ''


class ComputerInfo:
    def __init__(self, parent):
        self.parent = parent
        self.parent.geometry('800x650')
        self.parent.configure(bg=COLORS['bg'])
        self.setup_ui()
        threading.Thread(target=self.load_info, daemon=True).start()

    def setup_ui(self):
        # Header
        hdr = tk.Frame(self.parent, bg=COLORS['bg_header'])
        hdr.pack(fill='x')
        tk.Label(hdr, text='💻  Computer Information', font=FONTS['large'],
                  bg=COLORS['bg_header'], fg='white', pady=10).pack(side='left', padx=15)
        tk.Button(hdr, text='🔄 Refresh', font=FONTS['small'],
                   bg=COLORS['accent'], fg='white', relief='flat',
                   padx=8, pady=3, cursor='hand2',
                   command=lambda: threading.Thread(
                       target=self.load_info, daemon=True).start()
                   ).pack(side='right', padx=15, pady=8)

        # Notebook
        self.nb = ttk.Notebook(self.parent)
        self.nb.pack(fill='both', expand=True, padx=8, pady=8)

        # Tabs
        self.tabs = {}
        for tab_name in ['📋 Summary', '🖥️ CPU', '💾 RAM', '🎮 GPU',
                          '💿 Storage', '🌐 Network', '🔋 Battery', '🪟 Windows']:
            f = tk.Frame(self.nb, bg=COLORS['bg'])
            self.nb.add(f, text=tab_name)
            self.tabs[tab_name] = f

        # Create content areas
        self.info_widgets = {}
        for tab_name, frame in self.tabs.items():
            text = tk.Text(frame, font=FONTS['mono'],
                            bg='#1E1E1E', fg='#D4D4D4',
                            insertbackground='white',
                            relief='flat', padx=15, pady=10,
                            state='disabled')
            vsb = ttk.Scrollbar(frame, command=text.yview)
            text.configure(yscrollcommand=vsb.set)
            vsb.pack(side='right', fill='y')
            text.pack(fill='both', expand=True)
            self.info_widgets[tab_name] = text

            # Configure tags
            text.tag_configure('header', foreground='#569CD6',
                                font=('Segoe UI', 11, 'bold'))
            text.tag_configure('key', foreground='#9CDCFE')
            text.tag_configure('value', foreground='#CE9178')
            text.tag_configure('good', foreground='#4EC9B0')
            text.tag_configure('warn', foreground='#DCDCAA')
            text.tag_configure('bad', foreground='#F44747')
            text.tag_configure('section', foreground='#C586C0',
                                font=('Consolas', 10, 'bold'))

        self.loading_label = tk.Label(self.parent,
                                       text='⏳ Loading system information...',
                                       font=FONTS['subtitle'],
                                       bg=COLORS['bg'], fg=COLORS['text_light'])
        self.loading_label.pack()

    def _write(self, widget, text, tag=None):
        widget.configure(state='normal')
        if tag:
            widget.insert('end', text, tag)
        else:
            widget.insert('end', text)
        widget.configure(state='disabled')

    def _clear(self, widget):
        widget.configure(state='normal')
        widget.delete('1.0', 'end')
        widget.configure(state='disabled')

    def _fmt_bytes(self, b):
        b = int(b)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if b < 1024:
                return f'{b:.1f} {unit}'
            b /= 1024
        return f'{b:.1f} PB'

    def load_info(self):
        self.loading_label.configure(text='⏳ Loading...')
        try:
            self._load_summary()
            self._load_cpu()
            self._load_ram()
            self._load_gpu()
            self._load_storage()
            self._load_network()
            self._load_battery()
            self._load_windows()
        except Exception as e:
            pass
        self.loading_label.configure(text='')

    def _load_summary(self):
        w = self.info_widgets['📋 Summary']
        self._clear(w)
        self._write(w, '═' * 60 + '\n', 'section')
        self._write(w, '          BMAT-Tools - System Summary\n', 'header')
        self._write(w, '═' * 60 + '\n\n', 'section')

        # Computer name
        comp_name = platform.node()
        username = os.environ.get('USERNAME', 'Unknown')
        self._write(w, f'  Computer Name : ', 'key')
        self._write(w, f'{comp_name}\n', 'value')
        self._write(w, f'  Username      : ', 'key')
        self._write(w, f'{username}\n', 'value')
        self._write(w, f'  Platform      : ', 'key')
        self._write(w, f'{platform.system()} {platform.release()}\n', 'value')
        self._write(w, f'  Architecture  : ', 'key')
        self._write(w, f'{platform.machine()}\n', 'value')

        # CPU
        self._write(w, '\n  ── CPU ──────────────────────────────────\n', 'section')
        cpu_data = run_wmic('cpu')
        self._write(w, f'  Model         : ', 'key')
        self._write(w, f'{cpu_data.get("Name", "Unknown")}\n', 'value')
        self._write(w, f'  Cores/Threads : ', 'key')
        cores = cpu_data.get('NumberOfCores', '?')
        threads = cpu_data.get('NumberOfLogicalProcessors', '?')
        self._write(w, f'{cores} Cores / {threads} Threads\n', 'value')

        # RAM
        self._write(w, '\n  ── RAM ──────────────────────────────────\n', 'section')
        mem_data = run_wmic('os')
        total_kb = int(mem_data.get('TotalVisibleMemorySize', 0))
        free_kb = int(mem_data.get('FreePhysicalMemory', 0))
        used_kb = total_kb - free_kb
        pct = (used_kb / total_kb * 100) if total_kb > 0 else 0
        self._write(w, f'  Total RAM     : ', 'key')
        self._write(w, f'{total_kb // 1024:,} MB ({total_kb // (1024*1024):,} GB)\n', 'value')
        self._write(w, f'  Used / Free   : ', 'key')
        tag = 'good' if pct < 70 else 'warn' if pct < 90 else 'bad'
        self._write(w, f'{used_kb // 1024:,} MB / {free_kb // 1024:,} MB ({pct:.0f}% used)\n', tag)

        # OS
        self._write(w, '\n  ── Windows ──────────────────────────────\n', 'section')
        winver = run_ps('(Get-WmiObject Win32_OperatingSystem).Caption')
        build = run_ps('(Get-WmiObject Win32_OperatingSystem).BuildNumber')
        self._write(w, f'  Version       : ', 'key')
        self._write(w, f'{winver}\n', 'value')
        self._write(w, f'  Build         : ', 'key')
        self._write(w, f'{build}\n', 'value')

    def _load_cpu(self):
        w = self.info_widgets['🖥️ CPU']
        self._clear(w)
        self._write(w, '  CPU Information\n\n', 'header')
        cpu = run_wmic('cpu')
        fields = [
            ('Name', 'Model'), ('Manufacturer', 'Manufacturer'),
            ('NumberOfCores', 'Physical Cores'),
            ('NumberOfLogicalProcessors', 'Logical Processors'),
            ('MaxClockSpeed', 'Max Clock Speed (MHz)'),
            ('CurrentClockSpeed', 'Current Clock Speed (MHz)'),
            ('L2CacheSize', 'L2 Cache (KB)'),
            ('L3CacheSize', 'L3 Cache (KB)'),
            ('Architecture', 'Architecture'),
            ('Caption', 'Caption'),
            ('LoadPercentage', 'CPU Load %'),
        ]
        for key, label in fields:
            val = cpu.get(key, 'N/A')
            if val:
                self._write(w, f'  {label:<30} : ', 'key')
                self._write(w, f'{val}\n', 'value')

        # Current usage via PowerShell
        usage = run_ps('(Get-WmiObject Win32_Processor).LoadPercentage')
        self._write(w, f'\n  {"Current Usage":<30} : ', 'key')
        pct = int(usage) if usage.isdigit() else 0
        tag = 'good' if pct < 60 else 'warn' if pct < 85 else 'bad'
        self._write(w, f'{pct}%\n', tag)

    def _load_ram(self):
        w = self.info_widgets['💾 RAM']
        self._clear(w)
        self._write(w, '  RAM Information\n\n', 'header')

        mem = run_wmic('os')
        total_kb = int(mem.get('TotalVisibleMemorySize', 0))
        free_kb = int(mem.get('FreePhysicalMemory', 0))
        used_kb = total_kb - free_kb

        self._write(w, f'  {"Total Physical RAM":<30} : ', 'key')
        self._write(w, f'{total_kb // 1024:,} MB\n', 'value')
        self._write(w, f'  {"Used":<30} : ', 'key')
        self._write(w, f'{used_kb // 1024:,} MB\n', 'warn')
        self._write(w, f'  {"Free":<30} : ', 'key')
        self._write(w, f'{free_kb // 1024:,} MB\n', 'good')

        # Physical slots
        self._write(w, '\n  Memory Slots:\n', 'section')
        result = subprocess.run(
            ['wmic', 'memorychip', 'get', 'BankLabel,Capacity,Speed,MemoryType,Manufacturer,PartNumber',
             '/format:csv'],
            capture_output=True, text=True
        )
        for line in result.stdout.splitlines()[2:]:
            parts = line.strip().split(',')
            if len(parts) >= 5 and parts[1]:
                try:
                    cap = int(parts[2]) // (1024 * 1024)
                    self._write(w, f'    Slot {parts[1]}: ', 'key')
                    self._write(w, f'{cap} MB  Speed: {parts[5]} MHz  {parts[3]}\n', 'value')
                except:
                    pass

    def _load_gpu(self):
        w = self.info_widgets['🎮 GPU']
        self._clear(w)
        self._write(w, '  GPU Information\n\n', 'header')
        gpu = run_wmic('path win32_VideoController')
        fields = [
            ('Name', 'GPU Model'),
            ('AdapterRAM', 'VRAM'),
            ('DriverVersion', 'Driver Version'),
            ('VideoProcessor', 'GPU Processor'),
            ('CurrentHorizontalResolution', 'Resolution Width'),
            ('CurrentVerticalResolution', 'Resolution Height'),
            ('CurrentRefreshRate', 'Refresh Rate (Hz)'),
            ('VideoModeDescription', 'Display Mode'),
        ]
        for key, label in fields:
            val = gpu.get(key, '')
            if val:
                if key == 'AdapterRAM':
                    try:
                        val = f'{int(val) // (1024*1024)} MB'
                    except:
                        pass
                self._write(w, f'  {label:<30} : ', 'key')
                self._write(w, f'{val}\n', 'value')

    def _load_storage(self):
        w = self.info_widgets['💿 Storage']
        self._clear(w)
        self._write(w, '  Storage Information\n\n', 'header')

        # Disk partitions
        result = subprocess.run(
            ['wmic', 'logicaldisk', 'get',
             'DeviceID,DriveType,Size,FreeSpace,FileSystem,VolumeName',
             '/format:csv'],
            capture_output=True, text=True
        )
        self._write(w, '  Drive Partitions:\n', 'section')
        for line in result.stdout.splitlines()[2:]:
            parts = line.strip().split(',')
            if len(parts) >= 6 and parts[2]:
                try:
                    drive = parts[1]
                    fs = parts[3]
                    free = int(parts[4]) if parts[4] else 0
                    size = int(parts[5]) if parts[5] else 0
                    vol = parts[6] if len(parts) > 6 else ''
                    if size > 0:
                        pct = (size - free) / size * 100
                        used = size - free
                        tag = 'good' if pct < 70 else 'warn' if pct < 90 else 'bad'
                        self._write(w, f'\n    Drive {drive}  [{vol}] ({fs})\n', 'key')
                        self._write(w,
                                    f'      Total: {self._fmt_bytes(size)}'
                                    f'  Used: {self._fmt_bytes(used)}'
                                    f'  Free: {self._fmt_bytes(free)}'
                                    f'  ({pct:.0f}% full)\n', tag)
                except:
                    pass

        # Physical disks
        self._write(w, '\n  Physical Disks:\n', 'section')
        disk_info = subprocess.run(
            ['wmic', 'diskdrive', 'get', 'Caption,Size,MediaType,InterfaceType',
             '/format:csv'],
            capture_output=True, text=True
        )
        for line in disk_info.stdout.splitlines()[2:]:
            parts = line.strip().split(',')
            if len(parts) >= 5 and parts[2]:
                try:
                    size = int(parts[4]) if parts[4] else 0
                    self._write(w, f'    {parts[2]}\n', 'key')
                    self._write(w,
                                f'      Size: {self._fmt_bytes(size)}'
                                f'  Type: {parts[3]}  Interface: {parts[1]}\n', 'value')
                except:
                    pass

    def _load_network(self):
        w = self.info_widgets['🌐 Network']
        self._clear(w)
        self._write(w, '  Network Information\n\n', 'header')

        # Get all adapters
        result = run_ps(
            'Get-NetIPConfiguration | ForEach-Object {'
            '"Adapter: " + $_.InterfaceAlias + "`n"'
            ' + "  IPv4: " + ($_.IPv4Address.IPAddress -join ", ") + "`n"'
            ' + "  IPv6: " + ($_.IPv6Address.IPAddress -join ", ") + "`n"'
            ' + "  Gateway: " + ($_.IPv4DefaultGateway.NextHop -join ", ") + "`n"'
            ' + "  DNS: " + ($_.DNSServer.ServerAddresses -join ", ") + "`n"'
            '}'
        )
        if result:
            self._write(w, result + '\n', 'value')

        # MAC addresses
        self._write(w, '\n  MAC Addresses:\n', 'section')
        mac_result = run_ps(
            'Get-NetAdapter | Select-Object Name, MacAddress, Status, LinkSpeed '
            '| Format-Table -AutoSize | Out-String'
        )
        self._write(w, mac_result + '\n', 'value')

        # External IP
        self._write(w, '\n  External IP:\n', 'section')
        try:
            import urllib.request
            ext_ip = urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode()
            self._write(w, f'  {ext_ip}\n', 'good')
        except:
            self._write(w, '  Cannot retrieve (no internet)\n', 'bad')

    def _load_battery(self):
        w = self.info_widgets['🔋 Battery']
        self._clear(w)
        self._write(w, '  Battery Information\n\n', 'header')

        bat = run_wmic('path Win32_Battery')
        if not bat:
            self._write(w, '  No battery found (Desktop PC)\n', 'warn')
            return

        fields = [
            ('Name', 'Battery Name'),
            ('Status', 'Status'),
            ('BatteryStatus', 'Charge Status'),
            ('EstimatedChargeRemaining', 'Charge Remaining (%)'),
            ('EstimatedRunTime', 'Estimated Runtime (min)'),
            ('DesignCapacity', 'Design Capacity (mWh)'),
            ('FullChargeCapacity', 'Full Charge Capacity (mWh)'),
        ]
        for key, label in fields:
            val = bat.get(key, '')
            if val:
                self._write(w, f'  {label:<35} : ', 'key')
                if key == 'EstimatedChargeRemaining':
                    pct = int(val) if val.isdigit() else 0
                    tag = 'good' if pct > 40 else 'warn' if pct > 15 else 'bad'
                    self._write(w, f'{val}%\n', tag)
                else:
                    self._write(w, f'{val}\n', 'value')

        # Power plan
        self._write(w, '\n  Power Plan:\n', 'section')
        plan = run_ps('powercfg /getactivescheme')
        self._write(w, f'  {plan}\n', 'value')

    def _load_windows(self):
        w = self.info_widgets['🪟 Windows']
        self._clear(w)
        self._write(w, '  Windows Information\n\n', 'header')

        fields_ps = [
            ('(Get-WmiObject Win32_OperatingSystem).Caption', 'OS Name'),
            ('(Get-WmiObject Win32_OperatingSystem).Version', 'Version'),
            ('(Get-WmiObject Win32_OperatingSystem).BuildNumber', 'Build Number'),
            ('(Get-WmiObject Win32_OperatingSystem).OSArchitecture', 'Architecture'),
            ('(Get-WmiObject Win32_OperatingSystem).InstallDate', 'Install Date'),
            ('(Get-WmiObject Win32_OperatingSystem).LastBootUpTime', 'Last Boot'),
            ('(Get-WmiObject Win32_OperatingSystem).RegisteredUser', 'Registered User'),
            ('(Get-WmiObject Win32_OperatingSystem).SerialNumber', 'Serial Number'),
        ]
        for cmd, label in fields_ps:
            val = run_ps(cmd)
            if val:
                self._write(w, f'  {label:<30} : ', 'key')
                self._write(w, f'{val}\n', 'value')

        # Activation status
        self._write(w, '\n  Activation:\n', 'section')
        act = run_ps('(Get-WmiObject SoftwareLicensingProduct | Where-Object { $_.PartialProductKey }).LicenseStatus')
        status_map = {'1': 'Licensed ✅', '0': 'Unlicensed ❌'}
        self._write(w, f'  {status_map.get(act, act)}\n', 'value')

        # Product key (partial)
        self._write(w, '\n  Product Key (partial):\n', 'section')
        key = run_ps('(Get-WmiObject SoftwareLicensingProduct | Where-Object { $_.PartialProductKey }).PartialProductKey')
        self._write(w, f'  xxxxx-xxxxx-xxxxx-xxxxx-{key}\n', 'value')


def get_detailed_hardware_info():
    """Gathers comprehensive hardware & system info matching BTP Tool Pro 2026 inspection dashboard."""
    import subprocess
    import json
    import socket
    import datetime
    import os

    def fmt_bytes_gb(b):
        try:
            val = float(b)
            return f"{val / (1024**3):.1f} GB"
        except Exception:
            return "N/A"

    def run_ps_cmd(cmd):
        try:
            res = subprocess.run(
                ['powershell', '-NoProfile', '-Command', f"{cmd} | ConvertTo-Json -Depth 3"],
                capture_output=True, text=True, encoding='utf-8', errors='ignore'
            )
            if res.stdout.strip():
                parsed = json.loads(res.stdout.strip())
                if isinstance(parsed, dict):
                    return [parsed]
                elif isinstance(parsed, list):
                    return parsed
            return []
        except Exception:
            return []

    # 1. CPU
    cpu_list = run_ps_cmd('Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed, SocketDesignation, L2CacheSize, L3CacheSize')
    cpu_info = {
        "name": "N/A",
        "cores_threads": "N/A",
        "max_clock": "N/A",
        "socket": "N/A",
        "cache": "N/A"
    }
    if cpu_list:
        c = cpu_list[0]
        cpu_info["name"] = c.get("Name", "N/A").strip()
        cores = c.get("NumberOfCores", 0)
        threads = c.get("NumberOfLogicalProcessors", 0)
        cpu_info["cores_threads"] = f"{cores} nhân · {threads} luồng"
        clock_mhz = c.get("MaxClockSpeed", 0)
        cpu_info["max_clock"] = f"{clock_mhz / 1000.0:.2f} GHz" if clock_mhz else "N/A"
        cpu_info["socket"] = c.get("SocketDesignation", "N/A").strip() or "N/A"
        l2 = c.get("L2CacheSize", 0)
        l3 = c.get("L3CacheSize", 0)
        cache_strs = []
        if l2: cache_strs.append(f"{l2/1024:.1f} MB L2")
        if l3: cache_strs.append(f"{l3/1024:.1f} MB L3")
        cpu_info["cache"] = " · ".join(cache_strs) if cache_strs else "N/A"

    # 2. System & BaseBoard & BIOS
    cs_list = run_ps_cmd('Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer, Model, Name, TotalPhysicalMemory, SystemFamily, ChassisSKUNumber')
    board_list = run_ps_cmd('Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer, Product, SerialNumber, Version')
    bios_list = run_ps_cmd('Get-CimInstance Win32_BIOS | Select-Object Manufacturer, SMBIOSBIOSVersion, ReleaseDate, SerialNumber')
    prod_list = run_ps_cmd('Get-CimInstance Win32_ComputerSystemProduct | Select-Object IdentifyingNumber, UUID, Name, Vendor')

    system_info = {
        "vendor": "N/A",
        "manufacturer": "N/A",
        "model": "N/A",
        "computer_name": socket.gethostname(),
        "system_family": "N/A",
        "chassis_type": "Desktop",
        "is_laptop": False
    }
    ram_total_str = "N/A"
    ram_total_gb_num = 0.0

    if cs_list:
        cs = cs_list[0]
        mfg = cs.get("Manufacturer", "").strip()
        mdl = cs.get("Model", "").strip()
        system_info["manufacturer"] = mfg or "N/A"
        system_info["model"] = mdl or "N/A"
        system_info["vendor"] = f"{mfg} {mdl}".strip() or "N/A"
        system_info["computer_name"] = cs.get("Name", socket.gethostname()).strip()
        system_info["system_family"] = cs.get("SystemFamily", "").strip() or mdl or "N/A"
        if cs.get("TotalPhysicalMemory"):
            ram_b = float(cs.get("TotalPhysicalMemory", 0))
            ram_total_gb_num = round(ram_b / (1024**3), 1)
            ram_total_str = f"{ram_total_gb_num} GB"

    # Service Tag & UUID
    service_tag_info = {
        "serial": "N/A",
        "service_tag": "N/A",
        "product_id": "N/A",
        "uuid": "N/A"
    }

    if prod_list:
        p = prod_list[0]
        ident = p.get("IdentifyingNumber", "").strip()
        uuid_val = p.get("UUID", "").strip()
        if ident and ident.lower() != "default string":
            service_tag_info["serial"] = ident
            service_tag_info["service_tag"] = ident
            service_tag_info["product_id"] = ident
        if uuid_val:
            service_tag_info["uuid"] = uuid_val

    if bios_list:
        bi = bios_list[0]
        bios_serial = bi.get("SerialNumber", "").strip()
        if bios_serial and bios_serial.lower() != "default string":
            if service_tag_info["serial"] == "N/A":
                service_tag_info["serial"] = bios_serial
                service_tag_info["service_tag"] = bios_serial
                service_tag_info["product_id"] = bios_serial

    # Mainboard
    mainboard_info = {
        "manufacturer": "N/A",
        "model": "N/A",
        "serial": "N/A",
        "version": "N/A"
    }

    if board_list:
        b = board_list[0]
        mainboard_info["manufacturer"] = b.get("Manufacturer", "N/A").strip()
        mainboard_info["model"] = b.get("Product", "N/A").strip()
        mainboard_info["serial"] = b.get("SerialNumber", "N/A").strip() or "N/A"
        mainboard_info["version"] = b.get("Version", "A00").strip() or "A00"

    # BIOS Info
    bios_info = {
        "vendor": "N/A",
        "version": "N/A",
        "release_date": "N/A"
    }

    if bios_list:
        bi = bios_list[0]
        bios_info["vendor"] = bi.get("Manufacturer", "N/A").strip()
        bios_info["version"] = bi.get("SMBIOSBIOSVersion", "N/A").strip()
        b_date = bi.get("ReleaseDate", "")
        date_clean = ""
        if b_date and isinstance(b_date, str) and "Date(" in b_date:
            try:
                ms = int(b_date.split("(")[1].split(")")[0])
                date_clean = datetime.datetime.fromtimestamp(ms / 1000.0).strftime("%Y-%m-%d")
            except Exception:
                date_clean = ""
        elif b_date and isinstance(b_date, str) and len(b_date) >= 8:
            date_clean = f"{b_date[:4]}-{b_date[4:6]}-{b_date[6:8]}"
        bios_info["release_date"] = date_clean or "N/A"

    # 3. Battery Details & Health
    bat_list = run_ps_cmd('Get-CimInstance Win32_Battery | Select-Object Name, DeviceID, EstimatedChargeRemaining, BatteryStatus, DesignCapacity, FullChargeCapacity')
    battery_info = {
        "is_laptop": False,
        "name": "N/A",
        "level_pct": 100,
        "wear_pct": 0.0,
        "design_mwh": "N/A",
        "full_mwh": "N/A",
        "status_text": "Không có pin (Desktop PC)",
        "health_text": "PC Desktop"
    }

    if bat_list:
        bt = bat_list[0]
        battery_info["is_laptop"] = True
        system_info["is_laptop"] = True
        system_info["chassis_type"] = "Notebook"
        battery_info["name"] = bt.get("Name", bt.get("DeviceID", "Standard Battery")).strip()
        battery_info["level_pct"] = bt.get("EstimatedChargeRemaining", 100)
        
        design_cap = float(bt.get("DesignCapacity", 0) or 0)
        full_cap = float(bt.get("FullChargeCapacity", 0) or 0)

        if design_cap > 0 and full_cap > 0:
            battery_info["design_mwh"] = f"{int(design_cap)} mWh"
            battery_info["full_mwh"] = f"{int(full_cap)} mWh"
            wear = round(max(0.0, 100.0 - (full_cap / design_cap * 100.0)), 1)
            battery_info["wear_pct"] = wear
            if wear < 20:
                battery_info["health_text"] = "✓ Pin tốt"
            elif wear < 40:
                battery_info["health_text"] = "⚠️ Chai nhẹ"
            else:
                battery_info["health_text"] = "❌ Chai nặng (Nên thay)"
        else:
            battery_info["health_text"] = "✓ Hoạt động tốt"

        bat_status = bt.get("BatteryStatus", 1)
        if bat_status in [2, 6, 7, 8, 9]:
            battery_info["status_text"] = "Đang sạc (AC Powered)"
        elif bat_status == 3:
            battery_info["status_text"] = "Đầy 100% (Đang cắm sạc)"
        else:
            battery_info["status_text"] = "Đang dùng Pin (Battery Powered)"

    # 4. RAM Modules
    ram_list = run_ps_cmd('Get-CimInstance Win32_PhysicalMemory | Select-Object DeviceLocator, Capacity, Speed, Manufacturer, PartNumber')
    ram_modules = []
    for r in ram_list:
        loc = r.get("DeviceLocator", "DIMM").strip()
        cap = fmt_bytes_gb(r.get("Capacity", 0))
        speed = f"{r.get('Speed', 0)} MHz" if r.get('Speed') else ""
        mfg = r.get("Manufacturer", "").strip()
        part = r.get("PartNumber", "").strip()
        info_str = " · ".join(filter(None, [cap, speed, mfg, part]))
        ram_modules.append({
            "locator": loc,
            "details": info_str
        })

    # 5. GPU
    gpu_list = run_ps_cmd('Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion')
    gpus = []
    for idx, g in enumerate(gpu_list, 1):
        name = g.get("Name", "").strip()
        if not name:
            continue
        vram_b = g.get("AdapterRAM", 0)
        vram_str = fmt_bytes_gb(vram_b) if vram_b else ""
        driver = f"driver {g.get('DriverVersion', '').strip()}" if g.get('DriverVersion') else ""
        info_str = " · ".join(filter(None, [name, vram_str, driver]))
        gpus.append({
            "label": f"GPU {idx}",
            "name": name,
            "vram": vram_str,
            "driver": g.get("DriverVersion", "").strip(),
            "details": info_str
        })

    # 6. Physical Disks & Partitions
    disk_list = run_ps_cmd('Get-CimInstance Win32_DiskDrive | Select-Object Model, Size, MediaType')
    disks = []
    for idx, d in enumerate(disk_list, 1):
        model = d.get("Model", "").strip()
        if not model:
            continue
        size_str = fmt_bytes_gb(d.get("Size", 0))
        media = d.get("MediaType", "SSD / Fixed Disk").strip()
        info_str = " · ".join(filter(None, [model, size_str, media]))
        disks.append({
            "label": f"Ổ {idx}",
            "model": model,
            "size": size_str,
            "details": info_str
        })

    # Partitions (C:, D:, E:...)
    logical_disks = run_ps_cmd('Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | Select-Object DeviceID, FreeSpace, Size, VolumeName')
    partitions = []
    for ld in logical_disks:
        dev = ld.get("DeviceID", "C:").strip()
        free_b = float(ld.get("FreeSpace", 0))
        total_b = float(ld.get("Size", 0))
        free_gb = round(free_b / (1024**3), 1)
        total_gb = round(total_b / (1024**3), 1)
        partitions.append({
            "drive": dev,
            "free_gb": free_gb,
            "total_gb": total_gb,
            "label": f"{dev} {free_gb} GB tự do / {total_gb} GB"
        })

    # 7. OS Info
    os_list = run_ps_cmd('Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber, OSArchitecture, InstallDate')
    os_info = {
        "caption": "Windows 11 Pro 64-bit",
        "version": "",
        "build": "",
        "arch": "64-bit",
        "install_date": "N/A"
    }
    if os_list:
        o = os_list[0]
        os_info["caption"] = o.get("Caption", "Windows 11 Pro").strip()
        os_info["version"] = o.get("Version", "").strip()
        os_info["build"] = o.get("BuildNumber", "").strip()
        os_info["arch"] = o.get("OSArchitecture", "64-bit").strip()
        inst_date = o.get("InstallDate", "")
        if inst_date and isinstance(inst_date, str) and len(inst_date) >= 8:
            os_info["install_date"] = f"{inst_date[:4]}-{inst_date[4:6]}-{inst_date[6:8]}"

    # 8. Missing / Warning Drivers Check
    missing_drivers = []
    try:
        pnp_err = run_ps_cmd('Get-PnpDevice | Where-Object { $_.Status -eq "Error" -or $_.Status -eq "Unknown" } | Select-Object FriendlyName, Class, InstanceId')
        for dev in pnp_err:
            fname = dev.get("FriendlyName", "").strip()
            if fname:
                missing_drivers.append({
                    "name": fname,
                    "class": dev.get("Class", "Unknown").strip(),
                    "instance": dev.get("InstanceId", "").strip()
                })
    except Exception:
        pass

    return {
        "success": True,
        "cpu": cpu_info,
        "system": system_info,
        "service_tag": service_tag_info,
        "mainboard": mainboard_info,
        "bios_info": bios_info,
        "battery": battery_info,
        "ram_total": ram_total_str,
        "ram_modules": ram_modules,
        "gpus": gpus,
        "disks": disks,
        "partitions": partitions,
        "os": os_info,
        "missing_drivers": missing_drivers
    }

