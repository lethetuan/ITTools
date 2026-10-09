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


# ─── OUI (Organizationally Unique Identifier) Database ───────────────────────
# Format: 'XX:XX:XX': ('Manufacturer', 'DeviceType')
# DeviceType: Router, Switch, AP, PC, Laptop, Phone, Tablet, Printer, Camera, TV, IoT, NAS, VM, Server, Unknown
OUI_DB = {
    # ── TP-Link ──
    'FC:AA:14': ('TP-Link', 'Router'), 'B0:BE:76': ('TP-Link', 'Router'),
    'C0:4A:00': ('TP-Link', 'Router'), '74:38:B7': ('TP-Link', 'Router'),
    '50:C7:BF': ('TP-Link', 'Router'), '14:CF:92': ('TP-Link', 'Router'),
    '18:A6:F7': ('TP-Link', 'Router'), 'A0:F3:C1': ('TP-Link', 'Router'),
    '50:3E:AA': ('TP-Link', 'Router'), '54:E6:FC': ('TP-Link', 'Router'),
    '30:B5:C2': ('TP-Link', 'Router'), 'EC:08:6B': ('TP-Link', 'Router'),
    '90:F6:52': ('TP-Link', 'Router'), '70:4F:57': ('TP-Link', 'Router'),
    '60:32:B1': ('TP-Link', 'Router'), 'AC:84:C6': ('TP-Link', 'Router'),
    # ── VMware / Virtual ──
    '00:50:56': ('VMware', 'VM'), '00:0C:29': ('VMware', 'VM'),
    '00:1C:14': ('VMware', 'VM'), '00:05:69': ('VMware', 'VM'),
    '00:0F:4B': ('VMware', 'VM'),
    # ── Apple ──
    'AC:BC:32': ('Apple', 'Mac'), '00:17:F2': ('Apple', 'Mac'),
    '00:1E:52': ('Apple', 'Mac'), '00:1F:F3': ('Apple', 'Mac'),
    '00:23:32': ('Apple', 'Mac'), '00:25:4B': ('Apple', 'Mac'),
    '00:26:B9': ('Apple', 'Mac'), '00:3E:E1': ('Apple', 'iPhone'),
    '04:54:53': ('Apple', 'iPhone'), '08:74:02': ('Apple', 'iPhone'),
    '0C:3E:9F': ('Apple', 'iPhone'), '10:40:F3': ('Apple', 'iPhone'),
    '18:AF:61': ('Apple', 'iPhone'), '1C:AB:A7': ('Apple', 'iPhone'),
    '20:78:F0': ('Apple', 'iPhone'), '28:E0:2C': ('Apple', 'iPhone'),
    '2C:B4:3A': ('Apple', 'iPhone'), '3C:15:C2': ('Apple', 'iPhone'),
    '40:4D:7F': ('Apple', 'iPhone'), '48:A1:95': ('Apple', 'iPhone'),
    '4C:32:75': ('Apple', 'iPhone'), '58:40:4E': ('Apple', 'iPhone'),
    '5C:96:9D': ('Apple', 'iPhone'), '60:03:08': ('Apple', 'Mac'),
    '60:F8:1D': ('Apple', 'iPhone'), '6C:40:08': ('Apple', 'iPhone'),
    '70:73:CB': ('Apple', 'iPhone'), '7C:6D:62': ('Apple', 'iPhone'),
    '8C:85:90': ('Apple', 'iPhone'), '8C:8D:28': ('Apple', 'iPad'),
    '90:72:40': ('Apple', 'iPhone'), '94:BF:2D': ('Apple', 'iPhone'),
    '98:01:A7': ('Apple', 'iPhone'), '9C:F4:8E': ('Apple', 'iPhone'),
    'A4:D1:8C': ('Apple', 'iPhone'), 'A8:96:8A': ('Apple', 'Mac'),
    'B8:63:4D': ('Apple', 'iPhone'), 'BC:67:78': ('Apple', 'iPhone'),
    'C0:CB:38': ('Apple', 'Mac'), 'C4:2C:03': ('Apple', 'iPhone'),
    'D0:03:DF': ('Apple', 'iPhone'), 'D4:9A:20': ('Apple', 'iPhone'),
    'D8:1D:72': ('Apple', 'iPhone'), 'DC:2B:2A': ('Apple', 'iPhone'),
    'E0:B5:5F': ('Apple', 'Mac'), 'E4:25:E7': ('Apple', 'iPhone'),
    'E8:06:88': ('Apple', 'iPhone'), 'EC:35:86': ('Apple', 'Mac'),
    'F0:18:98': ('Apple', 'iPhone'), 'F0:D1:A9': ('Apple', 'iPhone'),
    'F4:31:C3': ('Apple', 'iPhone'), 'F8:27:93': ('Apple', 'iPhone'),
    'FC:E9:98': ('Apple', 'iPhone'),
    # ── Dell ──
    '00:1A:A0': ('Dell', 'PC'), '00:14:22': ('Dell', 'PC'),
    'F8:DB:88': ('Dell', 'PC'), '00:21:9B': ('Dell', 'PC'),
    '18:03:73': ('Dell', 'PC'), '1C:40:24': ('Dell', 'PC'),
    '24:B6:FD': ('Dell', 'PC'), '54:BF:64': ('Dell', 'Server'),
    '74:86:7A': ('Dell', 'PC'), 'A4:1F:72': ('Dell', 'Server'),
    'B0:83:FE': ('Dell', 'PC'), 'BC:30:5B': ('Dell', 'PC'),
    'F0:1F:AF': ('Dell', 'Server'), 'F8:F5:5B': ('Dell', 'PC'),
    # ── HP / Hewlett-Packard ──
    'B4:2E:99': ('HP', 'Printer'), '3C:D9:2B': ('HP', 'PC'),
    '00:1E:0B': ('HP', 'PC'), '00:22:64': ('HP', 'PC'),
    '00:25:B3': ('HP', 'PC'), '00:26:55': ('HP', 'PC'),
    '10:60:4B': ('HP', 'Printer'), '1C:C1:DE': ('HP', 'Printer'),
    '20:16:D8': ('HP', 'Printer'), '30:8D:99': ('HP', 'PC'),
    '38:63:BB': ('HP', 'Printer'), '3C:52:82': ('HP', 'Printer'),
    '40:B0:34': ('HP', 'PC'), '48:0F:CF': ('HP', 'Printer'),
    '54:27:1E': ('HP', 'PC'), '58:20:B1': ('HP', 'Printer'),
    '70:5A:0F': ('HP', 'Printer'), '74:46:A0': ('HP', 'Printer'),
    '78:E7:D1': ('HP', 'PC'), '7C:C3:A1': ('HP', 'Printer'),
    '84:7B:EB': ('HP', 'PC'), '88:51:FB': ('HP', 'PC'),
    '98:E7:F4': ('HP', 'PC'), 'A0:D3:C1': ('HP', 'Printer'),
    'A4:5D:36': ('HP', 'Printer'), 'B4:99:BA': ('HP', 'PC'),
    'C4:34:6B': ('HP', 'PC'), 'D4:85:64': ('HP', 'PC'),
    'DC:4A:9E': ('HP', 'Printer'), 'E4:11:5B': ('HP', 'Printer'),
    'F4:CE:46': ('HP', 'Printer'), 'FC:15:B4': ('HP', 'PC'),
    # ── Cisco ──
    '00:23:AE': ('Cisco', 'Switch'), '00:1B:D4': ('Cisco', 'Switch'),
    '24:01:C7': ('Cisco', 'Router'), '00:0A:B7': ('Cisco', 'Switch'),
    '00:0B:BE': ('Cisco', 'Switch'), '00:1A:2F': ('Cisco', 'Router'),
    '00:1B:2A': ('Cisco', 'Switch'), '00:1D:45': ('Cisco', 'Switch'),
    '00:22:BD': ('Cisco', 'Switch'), '00:24:14': ('Cisco', 'Router'),
    '00:26:0A': ('Cisco', 'Switch'), '2C:36:F8': ('Cisco', 'Switch'),
    '34:DB:FD': ('Cisco', 'Router'), '3C:08:F6': ('Cisco', 'Switch'),
    '4C:4E:35': ('Cisco', 'Switch'), '68:EF:BD': ('Cisco', 'Switch'),
    '6C:41:0E': ('Cisco', 'Switch'), '70:CA:9B': ('Cisco', 'Switch'),
    '84:B8:02': ('Cisco', 'Switch'), '88:F0:31': ('Cisco', 'Switch'),
    'A0:EC:F9': ('Cisco', 'Switch'), 'AC:17:C8': ('Cisco', 'Router'),
    'B4:A4:E3': ('Cisco', 'Switch'), 'C8:9C:1D': ('Cisco', 'Switch'),
    'D0:C7:89': ('Cisco', 'Router'), 'F4:CF:E2': ('Cisco', 'Router'),
    # ── ASUS ──
    'A4:2B:B0': ('ASUS', 'Router'), '00:1A:92': ('ASUS', 'Router'),
    '00:1D:60': ('ASUS', 'PC'), '04:92:26': ('ASUS', 'Router'),
    '08:60:6E': ('ASUS', 'PC'), '10:BF:48': ('ASUS', 'Router'),
    '14:DA:E9': ('ASUS', 'PC'), '1C:87:2C': ('ASUS', 'PC'),
    '20:CF:30': ('ASUS', 'Router'), '2C:FD:A1': ('ASUS', 'PC'),
    '30:5A:3A': ('ASUS', 'PC'), '38:2C:4A': ('ASUS', 'PC'),
    '40:16:7E': ('ASUS', 'PC'), '4C:ED:FB': ('ASUS', 'PC'),
    '50:46:5D': ('ASUS', 'PC'), '5C:AC:4C': ('ASUS', 'PC'),
    '60:45:CB': ('ASUS', 'PC'), '70:4D:7B': ('ASUS', 'PC'),
    '74:D0:2B': ('ASUS', 'Router'), '80:65:6D': ('ASUS', 'PC'),
    '90:E6:BA': ('ASUS', 'PC'), 'AC:22:0B': ('ASUS', 'PC'),
    'B0:6E:BF': ('ASUS', 'Router'), 'BC:EE:7B': ('ASUS', 'PC'),
    'C8:60:00': ('ASUS', 'PC'), 'F0:79:59': ('ASUS', 'Router'),
    'F8:32:E4': ('ASUS', 'PC'),
    # ── Intel (Network adapters) ──
    '94:DE:80': ('Intel', 'PC'), '00:1B:21': ('Intel', 'PC'),
    '00:1E:67': ('Intel', 'PC'), '00:21:6A': ('Intel', 'PC'),
    '00:23:14': ('Intel', 'PC'), '00:24:D6': ('Intel', 'PC'),
    '00:26:C7': ('Intel', 'PC'), '00:27:10': ('Intel', 'PC'),
    '10:02:B5': ('Intel', 'PC'), '18:3D:A2': ('Intel', 'PC'),
    '24:77:03': ('Intel', 'PC'), '40:25:C2': ('Intel', 'PC'),
    '48:45:20': ('Intel', 'PC'), '5C:C5:D4': ('Intel', 'PC'),
    '60:6C:66': ('Intel', 'PC'), '7C:5C:F8': ('Intel', 'PC'),
    '80:19:34': ('Intel', 'PC'), '8C:EC:4B': ('Intel', 'PC'),
    '9C:69:B4': ('Intel', 'PC'), 'A0:88:B4': ('Intel', 'PC'),
    'A4:C3:F0': ('Intel', 'PC'), 'AC:7B:A1': ('Intel', 'PC'),
    'B4:D5:BD': ('Intel', 'PC'), 'C0:3F:D5': ('Intel', 'PC'),
    'C4:85:08': ('Intel', 'PC'), 'D0:50:99': ('Intel', 'PC'),
    'D4:BE:D9': ('Intel', 'PC'), 'DC:53:60': ('Intel', 'PC'),
    'E0:94:67': ('Intel', 'PC'), 'E4:70:B8': ('Intel', 'PC'),
    'E8:03:9A': ('Intel', 'PC'), 'EC:B1:D7': ('Intel', 'PC'),
    # ── Realtek ──
    '00:E0:4C': ('Realtek', 'PC'), '02:00:4C': ('Realtek', 'PC'),
    '52:54:00': ('Realtek', 'VM'),
    # ── Samsung ──
    '00:26:37': ('Samsung', 'Phone'), '00:15:99': ('Samsung', 'Phone'),
    '00:16:32': ('Samsung', 'Phone'), '00:17:C9': ('Samsung', 'Phone'),
    '00:1A:8A': ('Samsung', 'TV'), '08:D4:2B': ('Samsung', 'Phone'),
    '0C:14:20': ('Samsung', 'Phone'), '10:1D:C0': ('Samsung', 'TV'),
    '14:49:E0': ('Samsung', 'Phone'), '14:BB:6E': ('Samsung', 'Phone'),
    '18:3F:47': ('Samsung', 'Phone'), '1C:62:B8': ('Samsung', 'Phone'),
    '20:13:E0': ('Samsung', 'Phone'), '24:4B:81': ('Samsung', 'Phone'),
    '28:98:7B': ('Samsung', 'Phone'), '2C:54:CF': ('Samsung', 'Phone'),
    '30:19:66': ('Samsung', 'Phone'), '34:23:BA': ('Samsung', 'Phone'),
    '38:16:D1': ('Samsung', 'Phone'), '3C:49:37': ('Samsung', 'Phone'),
    '40:0E:85': ('Samsung', 'Phone'), '44:F4:59': ('Samsung', 'Phone'),
    '48:44:F7': ('Samsung', 'Phone'), '4C:3C:16': ('Samsung', 'TV'),
    '50:32:37': ('Samsung', 'Phone'), '54:88:0E': ('Samsung', 'Phone'),
    '58:00:E3': ('Samsung', 'Phone'), '5C:0A:5B': ('Samsung', 'Phone'),
    '60:6B:BD': ('Samsung', 'Phone'), '64:77:91': ('Samsung', 'Phone'),
    '68:27:37': ('Samsung', 'Phone'), '6C:83:36': ('Samsung', 'Phone'),
    '70:F9:27': ('Samsung', 'Phone'), '74:45:8A': ('Samsung', 'Phone'),
    '78:1F:DB': ('Samsung', 'Phone'), '7C:0B:C6': ('Samsung', 'Phone'),
    '80:57:19': ('Samsung', 'Phone'), '84:25:DB': ('Samsung', 'Phone'),
    '88:32:9B': ('Samsung', 'Phone'), '8C:C8:CD': ('Samsung', 'Phone'),
    '90:18:7C': ('Samsung', 'Phone'), '94:35:0A': ('Samsung', 'Phone'),
    '98:52:3D': ('Samsung', 'TV'), '9C:02:98': ('Samsung', 'Phone'),
    'A0:82:1F': ('Samsung', 'Phone'), 'A4:EB:D3': ('Samsung', 'Phone'),
    'A8:0C:63': ('Samsung', 'Phone'), 'AC:36:13': ('Samsung', 'Phone'),
    'B0:72:BF': ('Samsung', 'Phone'), 'B4:3A:28': ('Samsung', 'Phone'),
    'B8:5A:73': ('Samsung', 'Phone'), 'BC:44:86': ('Samsung', 'Phone'),
    'C0:97:27': ('Samsung', 'Phone'), 'C4:42:02': ('Samsung', 'Phone'),
    'C8:14:79': ('Samsung', 'Phone'), 'CC:05:1B': ('Samsung', 'Phone'),
    'D0:17:6A': ('Samsung', 'Phone'), 'D4:87:D8': ('Samsung', 'Phone'),
    'D8:57:EF': ('Samsung', 'Phone'), 'DC:71:96': ('Samsung', 'Phone'),
    'E0:CB:4E': ('Samsung', 'TV'), 'E4:40:E2': ('Samsung', 'Phone'),
    'E8:50:8B': ('Samsung', 'Phone'), 'EC:9B:F3': ('Samsung', 'Phone'),
    'F0:25:B7': ('Samsung', 'Phone'), 'F4:42:8F': ('Samsung', 'Phone'),
    'F8:04:2E': ('Samsung', 'Phone'), 'FC:A1:83': ('Samsung', 'Phone'),
    # ── Xiaomi / Redmi ──
    'D8:5D:E2': ('Xiaomi', 'Phone'), '28:6C:07': ('Xiaomi', 'Phone'),
    '00:9E:C8': ('Xiaomi', 'Phone'), '04:CF:8C': ('Xiaomi', 'Phone'),
    '08:21:EF': ('Xiaomi', 'Phone'), '0C:1D:AF': ('Xiaomi', 'Phone'),
    '10:2A:B3': ('Xiaomi', 'Phone'), '10:AB:66': ('Xiaomi', 'Phone'),
    '18:59:36': ('Xiaomi', 'Phone'), '20:34:FB': ('Xiaomi', 'Phone'),
    '28:E3:1F': ('Xiaomi', 'Phone'), '2C:4D:54': ('Xiaomi', 'Phone'),
    '34:80:B3': ('Xiaomi', 'Router'), '38:A4:ED': ('Xiaomi', 'Phone'),
    '40:31:3C': ('Xiaomi', 'Phone'), '44:1C:A8': ('Xiaomi', 'Phone'),
    '50:64:2B': ('Xiaomi', 'Phone'), '58:44:98': ('Xiaomi', 'Phone'),
    '60:AB:67': ('Xiaomi', 'Router'), '64:09:80': ('Xiaomi', 'Phone'),
    '68:DF:DD': ('Xiaomi', 'Phone'), '6C:2F:2C': ('Xiaomi', 'Phone'),
    '74:23:44': ('Xiaomi', 'Phone'), '78:02:F8': ('Xiaomi', 'Phone'),
    '7C:1D:D9': ('Xiaomi', 'Phone'), '80:35:C1': ('Xiaomi', 'Phone'),
    '8C:BE:BE': ('Xiaomi', 'Phone'), '90:C7:AA': ('Xiaomi', 'Phone'),
    '98:FA:E3': ('Xiaomi', 'Phone'), '9C:99:A0': ('Xiaomi', 'Phone'),
    'A0:86:C6': ('Xiaomi', 'Phone'), 'A4:DA:22': ('Xiaomi', 'Phone'),
    'AC:C1:EE': ('Xiaomi', 'Phone'), 'B0:E2:35': ('Xiaomi', 'Phone'),
    'B4:0B:44': ('Xiaomi', 'Phone'), 'BC:E1:43': ('Xiaomi', 'Phone'),
    'C4:0B:CB': ('Xiaomi', 'Phone'), 'C8:D3:A3': ('Xiaomi', 'Phone'),
    'CC:2D:E0': ('Xiaomi', 'Phone'), 'D4:97:0B': ('Xiaomi', 'Phone'),
    'DC:44:27': ('Xiaomi', 'Phone'), 'F0:B4:29': ('Xiaomi', 'Phone'),
    'F4:8E:92': ('Xiaomi', 'Phone'), 'F8:34:41': ('Xiaomi', 'Phone'),
    # ── Huawei ──
    '00:18:82': ('Huawei', 'Router'), '00:1E:10': ('Huawei', 'Router'),
    '00:25:68': ('Huawei', 'Router'), '00:46:4B': ('Huawei', 'Phone'),
    '04:02:1F': ('Huawei', 'Router'), '04:25:C5': ('Huawei', 'Phone'),
    '04:BD:70': ('Huawei', 'Phone'), '08:19:A6': ('Huawei', 'Router'),
    '0C:D6:96': ('Huawei', 'Phone'), '10:47:80': ('Huawei', 'Phone'),
    '14:A5:1A': ('Huawei', 'Phone'), '18:C5:8A': ('Huawei', 'Router'),
    '1C:8E:5C': ('Huawei', 'Phone'), '20:2B:C1': ('Huawei', 'Router'),
    '24:09:95': ('Huawei', 'Phone'), '28:31:52': ('Huawei', 'Phone'),
    '2C:AB:00': ('Huawei', 'Phone'), '30:D1:7E': ('Huawei', 'Phone'),
    '34:29:12': ('Huawei', 'Phone'), '38:37:8B': ('Huawei', 'Phone'),
    '3C:47:11': ('Huawei', 'Phone'), '40:4D:8E': ('Huawei', 'Phone'),
    '44:55:B1': ('Huawei', 'Phone'), '48:46:FB': ('Huawei', 'Phone'),
    '4C:1F:CC': ('Huawei', 'Router'), '50:3D:C6': ('Huawei', 'Phone'),
    '54:25:EA': ('Huawei', 'Phone'), '58:2A:F7': ('Huawei', 'Phone'),
    '5C:4C:A9': ('Huawei', 'Phone'), '60:DE:44': ('Huawei', 'Phone'),
    '64:A6:51': ('Huawei', 'Phone'), '68:A0:F6': ('Huawei', 'Phone'),
    '6C:8D:C1': ('Huawei', 'Phone'), '70:72:3C': ('Huawei', 'Phone'),
    '74:A5:28': ('Huawei', 'Phone'), '78:D6:F0': ('Huawei', 'Phone'),
    '7C:A2:3E': ('Huawei', 'Phone'), '80:FB:06': ('Huawei', 'Phone'),
    '84:74:2A': ('Huawei', 'Phone'), '88:66:A5': ('Huawei', 'Router'),
    '8C:34:FD': ('Huawei', 'Phone'), '90:4E:2B': ('Huawei', 'Phone'),
    '94:04:9C': ('Huawei', 'Phone'), '98:3B:16': ('Huawei', 'Phone'),
    '9C:74:1A': ('Huawei', 'Phone'), 'A0:08:6F': ('Huawei', 'Phone'),
    'A0:A0:DC': ('Huawei', 'Router'), 'A4:C6:4F': ('Huawei', 'Phone'),
    'AC:CF:85': ('Huawei', 'Phone'), 'B0:E5:ED': ('Huawei', 'Phone'),
    'B4:15:13': ('Huawei', 'Phone'), 'B8:08:CF': ('Huawei', 'Phone'),
    'BC:25:E0': ('Huawei', 'Phone'), 'C0:18:85': ('Huawei', 'Phone'),
    'C4:07:2F': ('Huawei', 'Phone'), 'C4:8E:8F': ('Huawei', 'Phone'),
    'C8:94:BB': ('Huawei', 'Phone'), 'CC:A2:23': ('Huawei', 'Phone'),
    'D0:27:88': ('Huawei', 'Phone'), 'D4:6E:5C': ('Huawei', 'Phone'),
    'D8:49:0B': ('Huawei', 'Phone'), 'DC:D2:FC': ('Huawei', 'Phone'),
    'E0:19:1D': ('Huawei', 'Phone'), 'E4:68:A3': ('Huawei', 'Phone'),
    'E8:BD:D1': ('Huawei', 'Phone'), 'EC:23:3D': ('Huawei', 'Phone'),
    'F0:7D:68': ('Huawei', 'Phone'), 'F4:9F:F3': ('Huawei', 'Phone'),
    'F8:4E:73': ('Huawei', 'Phone'), 'FC:48:EF': ('Huawei', 'Phone'),
    # ── Oppo / Realme / OnePlus (BBK Electronics) ──
    '00:1E:42': ('Oppo', 'Phone'), '04:D4:C4': ('Oppo', 'Phone'),
    '08:F9:E0': ('Oppo', 'Phone'), '0C:88:24': ('Oppo', 'Phone'),
    '10:A5:D0': ('Oppo', 'Phone'), '14:23:96': ('Oppo', 'Phone'),
    '18:26:49': ('Oppo', 'Phone'), '1C:77:F6': ('Oppo', 'Phone'),
    '20:AB:48': ('Oppo', 'Phone'), '24:62:AB': ('Oppo', 'Phone'),
    '28:3F:69': ('Oppo', 'Phone'), '2C:5B:B8': ('Oppo', 'Phone'),
    '30:D3:9A': ('Oppo', 'Phone'), '34:0A:FF': ('Oppo', 'Phone'),
    '38:BC:01': ('Oppo', 'Phone'), '3C:89:9B': ('Oppo', 'Phone'),
    '44:78:3E': ('Oppo', 'Phone'), '48:7A:DA': ('Oppo', 'Phone'),
    '4C:BC:48': ('Oppo', 'Phone'), '50:D4:F7': ('Oppo', 'Phone'),
    '54:35:30': ('Oppo', 'Phone'), '58:A2:B5': ('Oppo', 'Phone'),
    '5C:5F:67': ('Oppo', 'Phone'), '64:13:6C': ('Oppo', 'Phone'),
    '68:63:20': ('Oppo', 'Phone'), '6C:56:CC': ('Oppo', 'Phone'),
    '70:45:58': ('Oppo', 'Phone'), '74:FC:48': ('Oppo', 'Phone'),
    '78:A8:73': ('Oppo', 'Phone'), '7C:AC:D3': ('Oppo', 'Phone'),
    # ── Vivo ──
    '00:16:34': ('Vivo', 'Phone'), '00:17:88': ('Vivo', 'Phone'),
    '18:7A:93': ('Vivo', 'Phone'), '34:97:F6': ('Vivo', 'Phone'),
    '40:A8:F0': ('Vivo', 'Phone'), '6C:49:7A': ('Vivo', 'Phone'),
    '8C:4B:14': ('Vivo', 'Phone'), 'AC:23:3F': ('Vivo', 'Phone'),
    'B4:EE:25': ('Vivo', 'Phone'), 'C0:9F:42': ('Vivo', 'Phone'),
    'E0:00:84': ('Vivo', 'Phone'), 'EC:DF:3A': ('Vivo', 'Phone'),
    # ── Lenovo ──
    '00:22:FA': ('Lenovo', 'PC'), '00:24:7E': ('Lenovo', 'PC'),
    '28:6C:07': ('Lenovo', 'Laptop'), '3C:97:AE': ('Lenovo', 'Laptop'),
    '40:8D:5C': ('Lenovo', 'Laptop'), '44:38:39': ('Lenovo', 'PC'),
    '54:EE:75': ('Lenovo', 'Laptop'), '60:02:B4': ('Lenovo', 'Laptop'),
    '68:F7:28': ('Lenovo', 'Laptop'), '6C:0B:84': ('Lenovo', 'Laptop'),
    '70:E2:84': ('Lenovo', 'Laptop'), '7C:E9:D3': ('Lenovo', 'Laptop'),
    '80:FA:5B': ('Lenovo', 'Laptop'), '8C:EC:4B': ('Lenovo', 'Laptop'),
    '98:9E:63': ('Lenovo', 'Laptop'), '9C:B6:54': ('Lenovo', 'Laptop'),
    'A0:4E:A7': ('Lenovo', 'Laptop'), 'A8:6B:AD': ('Lenovo', 'Laptop'),
    'AC:B5:7D': ('Lenovo', 'Laptop'), 'B8:63:BC': ('Lenovo', 'Laptop'),
    'C4:34:6B': ('Lenovo', 'Laptop'), 'CC:52:AF': ('Lenovo', 'Laptop'),
    'D0:53:49': ('Lenovo', 'Laptop'), 'DC:FE:18': ('Lenovo', 'Laptop'),
    'E0:3F:49': ('Lenovo', 'Laptop'), 'E4:A7:C5': ('Lenovo', 'Laptop'),
    'E8:6F:38': ('Lenovo', 'Laptop'), 'F0:DE:F1': ('Lenovo', 'Laptop'),
    'F4:8E:38': ('Lenovo', 'Laptop'),
    # ── Acer ──
    '00:1D:92': ('Acer', 'Laptop'), '00:22:6B': ('Acer', 'Laptop'),
    '60:D8:19': ('Acer', 'Laptop'), '70:F1:A1': ('Acer', 'Laptop'),
    '90:00:4E': ('Acer', 'Laptop'), 'A0:4B:3B': ('Acer', 'Laptop'),
    'C0:9F:05': ('Acer', 'Laptop'), 'D4:21:22': ('Acer', 'Laptop'),
    # ── MSI ──
    '00:D8:61': ('MSI', 'PC'), '00:E0:4C': ('MSI', 'PC'),
    '08:BF:B8': ('MSI', 'PC'), '2C:60:0C': ('MSI', 'PC'),
    '4C:ED:DE': ('MSI', 'PC'), '60:45:BD': ('MSI', 'PC'),
    '88:D7:F6': ('MSI', 'PC'), 'C8:9C:DC': ('MSI', 'PC'),
    'E0:D5:5E': ('MSI', 'PC'),
    # ── Gigabyte ──
    '00:26:9E': ('Gigabyte', 'PC'), '1C:1B:0D': ('Gigabyte', 'PC'),
    '28:D2:44': ('Gigabyte', 'PC'), '50:E5:49': ('Gigabyte', 'PC'),
    '74:D4:35': ('Gigabyte', 'PC'), 'BC:EE:7B': ('Gigabyte', 'PC'),
    'E4:3A:6E': ('Gigabyte', 'PC'), 'FC:AA:14': ('Gigabyte', 'PC'),
    # ── Netgear ──
    '00:09:5B': ('Netgear', 'Router'), '00:14:6C': ('Netgear', 'Router'),
    '00:18:4D': ('Netgear', 'Router'), '00:1B:2F': ('Netgear', 'Router'),
    '00:1E:2A': ('Netgear', 'Router'), '00:22:3F': ('Netgear', 'Router'),
    '00:24:B2': ('Netgear', 'Router'), '00:26:F2': ('Netgear', 'Router'),
    '1C:AF:F7': ('Netgear', 'Router'), '20:4E:7F': ('Netgear', 'Router'),
    '2C:30:33': ('Netgear', 'Router'), '2C:B0:5D': ('Netgear', 'Router'),
    '30:46:9A': ('Netgear', 'Router'), '44:94:FC': ('Netgear', 'Router'),
    '4C:60:DE': ('Netgear', 'Router'), '6C:B0:CE': ('Netgear', 'Router'),
    '74:44:01': ('Netgear', 'Router'), '80:37:73': ('Netgear', 'Router'),
    '84:1B:5E': ('Netgear', 'Router'), '9C:3D:CF': ('Netgear', 'Router'),
    'A0:40:A0': ('Netgear', 'Router'), 'C4:3D:C7': ('Netgear', 'Router'),
    'C8:3A:35': ('Netgear', 'Router'), 'E0:91:F5': ('Netgear', 'Router'),
    # ── D-Link ──
    '00:05:5D': ('D-Link', 'Router'), '00:0D:88': ('D-Link', 'Router'),
    '00:11:95': ('D-Link', 'Router'), '00:17:9A': ('D-Link', 'Router'),
    '00:19:5B': ('D-Link', 'Router'), '00:1B:11': ('D-Link', 'Router'),
    '00:1C:F0': ('D-Link', 'Router'), '00:1E:58': ('D-Link', 'Router'),
    '00:22:B0': ('D-Link', 'Router'), '00:24:01': ('D-Link', 'Router'),
    '00:26:5A': ('D-Link', 'Router'), '00:D0:C0': ('D-Link', 'Router'),
    '14:D6:4D': ('D-Link', 'Router'), '1C:7E:E5': ('D-Link', 'Router'),
    '28:10:7B': ('D-Link', 'Router'), '34:08:04': ('D-Link', 'Router'),
    '40:FA:7F': ('D-Link', 'Router'), '5C:D9:98': ('D-Link', 'Router'),
    '6C:19:8F': ('D-Link', 'Router'), '78:54:2E': ('D-Link', 'Router'),
    '84:C9:B2': ('D-Link', 'Router'), '90:94:E4': ('D-Link', 'Router'),
    'AC:F1:DF': ('D-Link', 'Router'), 'B0:6E:BF': ('D-Link', 'Router'),
    'C8:BE:19': ('D-Link', 'Router'), 'CC:B2:55': ('D-Link', 'Router'),
    'D4:BF:7F': ('D-Link', 'Router'), 'E8:CC:18': ('D-Link', 'Router'),
    'F0:7D:68': ('D-Link', 'Router'), 'F8:1A:67': ('D-Link', 'Router'),
    # ── Ubiquiti (UniFi) ──
    '00:15:6D': ('Ubiquiti', 'AP'), '00:27:22': ('Ubiquiti', 'AP'),
    '04:18:D6': ('Ubiquiti', 'AP'), '18:E8:29': ('Ubiquiti', 'AP'),
    '24:A4:3C': ('Ubiquiti', 'AP'), '44:D9:E7': ('Ubiquiti', 'AP'),
    '68:72:51': ('Ubiquiti', 'AP'), '74:83:C2': ('Ubiquiti', 'AP'),
    '78:8A:20': ('Ubiquiti', 'AP'), '80:2A:A8': ('Ubiquiti', 'AP'),
    'B4:FB:E4': ('Ubiquiti', 'AP'), 'DC:9F:DB': ('Ubiquiti', 'AP'),
    'E0:63:DA': ('Ubiquiti', 'AP'), 'F0:9F:C2': ('Ubiquiti', 'AP'),
    'FC:EC:DA': ('Ubiquiti', 'AP'),
    # ── MikroTik ──
    '00:0C:42': ('MikroTik', 'Router'), '18:FD:74': ('MikroTik', 'Router'),
    '2C:C8:1B': ('MikroTik', 'Router'), '48:8F:5A': ('MikroTik', 'Router'),
    '4C:5E:0C': ('MikroTik', 'Router'), '6C:3B:6B': ('MikroTik', 'Router'),
    '74:4D:28': ('MikroTik', 'Router'), 'B8:69:F4': ('MikroTik', 'Router'),
    'C4:AD:34': ('MikroTik', 'Router'), 'CC:2D:E0': ('MikroTik', 'Router'),
    'D4:CA:6D': ('MikroTik', 'Router'), 'DC:2C:6E': ('MikroTik', 'Router'),
    'E4:8D:8C': ('MikroTik', 'Router'),
    # ── Tenda ──
    '00:B0:0C': ('Tenda', 'Router'), '1C:3B:C3': ('Tenda', 'Router'),
    '28:2C:B2': ('Tenda', 'Router'), '2A:28:5A': ('Tenda', 'Router'),
    '48:EE:0C': ('Tenda', 'Router'), '4C:11:BF': ('Tenda', 'Router'),
    '50:14:B3': ('Tenda', 'Router'), '6A:0D:C2': ('Tenda', 'Router'),
    '7C:B5:9B': ('Tenda', 'Router'), 'C8:3A:35': ('Tenda', 'Router'),
    'D4:76:EA': ('Tenda', 'Router'), 'F4:92:BF': ('Tenda', 'Router'),
    # ── Brother (Printer) ──
    '00:1B:A9': ('Brother', 'Printer'), '00:80:77': ('Brother', 'Printer'),
    '04:4B:ED': ('Brother', 'Printer'), '08:00:46': ('Brother', 'Printer'),
    '0C:EA:C7': ('Brother', 'Printer'), '10:1F:74': ('Brother', 'Printer'),
    '30:05:5C': ('Brother', 'Printer'), '34:12:98': ('Brother', 'Printer'),
    '3C:2A:F4': ('Brother', 'Printer'), '54:10:EC': ('Brother', 'Printer'),
    '90:F6:52': ('Brother', 'Printer'), 'C0:B8:83': ('Brother', 'Printer'),
    # ── Canon (Printer) ──
    '00:1E:8F': ('Canon', 'Printer'), '00:26:2D': ('Canon', 'Printer'),
    '04:B3:B2': ('Canon', 'Printer'), '08:00:85': ('Canon', 'Printer'),
    '10:94:97': ('Canon', 'Printer'), '18:22:7E': ('Canon', 'Printer'),
    '1C:88:79': ('Canon', 'Printer'), '40:B0:76': ('Canon', 'Printer'),
    '50:2F:A8': ('Canon', 'Printer'), '74:D4:35': ('Canon', 'Printer'),
    '7C:BB:8A': ('Canon', 'Printer'), '90:B1:1C': ('Canon', 'Printer'),
    'A0:06:E9': ('Canon', 'Printer'), 'AC:07:5F': ('Canon', 'Printer'),
    # ── Epson (Printer) ──
    '00:26:AB': ('Epson', 'Printer'), '04:61:0A': ('Epson', 'Printer'),
    '08:66:98': ('Epson', 'Printer'), '10:98:36': ('Epson', 'Printer'),
    '1C:A8:C3': ('Epson', 'Printer'), '34:3D:B7': ('Epson', 'Printer'),
    '58:CA:7F': ('Epson', 'Printer'), '64:EB:8C': ('Epson', 'Printer'),
    '70:48:0F': ('Epson', 'Printer'), '90:77:EE': ('Epson', 'Printer'),
    'AC:08:A2': ('Epson', 'Printer'), 'B8:53:AC': ('Epson', 'Printer'),
    # ── Synology (NAS) ──
    '00:11:32': ('Synology', 'NAS'), '20:4E:7F': ('Synology', 'NAS'),
    '28:5F:DB': ('Synology', 'NAS'), '34:80:0D': ('Synology', 'NAS'),
    '44:8A:5B': ('Synology', 'NAS'), '90:09:D0': ('Synology', 'NAS'),
    'BC:5F:F4': ('Synology', 'NAS'),
    # ── QNAP (NAS) ──
    '00:08:9B': ('QNAP', 'NAS'), '00:50:43': ('QNAP', 'NAS'),
    '24:5E:BE': ('QNAP', 'NAS'), '5C:D9:98': ('QNAP', 'NAS'),
    '68:4E:16': ('QNAP', 'NAS'),
    # ── Western Digital (NAS) ──
    '00:14:EE': ('Western Digital', 'NAS'), '00:90:A9': ('Western Digital', 'NAS'),
    '00:C0:9F': ('Western Digital', 'NAS'), '34:97:F6': ('Western Digital', 'NAS'),
    # ── Hikvision / Dahua (Camera) ──
    '0C:02:8A': ('Hikvision', 'Camera'), '44:19:B6': ('Hikvision', 'Camera'),
    '54:C4:15': ('Hikvision', 'Camera'), '8C:E7:48': ('Hikvision', 'Camera'),
    'A4:14:37': ('Hikvision', 'Camera'), 'B4:A3:82': ('Hikvision', 'Camera'),
    'C4:64:13': ('Hikvision', 'Camera'), 'D4:15:56': ('Hikvision', 'Camera'),
    'BC:AD:28': ('Dahua', 'Camera'), '30:74:96': ('Dahua', 'Camera'),
    '34:E0:CF': ('Dahua', 'Camera'), '90:02:A9': ('Dahua', 'Camera'),
    # ── LG ──
    '00:1E:75': ('LG', 'TV'), '00:26:E2': ('LG', 'TV'),
    '18:3D:5E': ('LG', 'TV'), '1C:28:AF': ('LG', 'TV'),
    '30:D6:C9': ('LG', 'TV'), '34:4D:F7': ('LG', 'Phone'),
    '40:B0:FA': ('LG', 'TV'), '48:59:29': ('LG', 'Phone'),
    '58:A2:B5': ('LG', 'TV'), '60:C5:47': ('LG', 'TV'),
    '64:BC:0C': ('LG', 'TV'), '70:93:F8': ('LG', 'TV'),
    '7C:1C:4E': ('LG', 'TV'), '88:36:6C': ('LG', 'TV'),
    '88:9F:FA': ('LG', 'TV'), '8C:3C:4A': ('LG', 'TV'),
    '8C:8D:28': ('LG', 'TV'), 'A0:39:F7': ('LG', 'TV'),
    'AC:0D:1B': ('LG', 'TV'), 'B4:E6:2D': ('LG', 'TV'),
    'C4:36:6C': ('LG', 'TV'), 'C8:08:E9': ('LG', 'TV'),
    'CC:2D:8C': ('LG', 'TV'), 'D8:F8:83': ('LG', 'TV'),
    'E8:5B:5B': ('LG', 'TV'), 'F8:A9:D0': ('LG', 'TV'),
    # ── Sony ──
    '00:01:4A': ('Sony', 'TV'), '00:04:1F': ('Sony', 'Phone'),
    '00:0A:D9': ('Sony', 'TV'), '00:13:A9': ('Sony', 'TV'),
    '00:1A:80': ('Sony', 'Phone'), '00:1D:0D': ('Sony', 'TV'),
    '04:D9:F5': ('Sony', 'TV'), '10:C2:5A': ('Sony', 'TV'),
    '14:7D:C5': ('Sony', 'TV'), '18:00:2D': ('Sony', 'TV'),
    '1C:7B:21': ('Sony', 'TV'), '30:17:C8': ('Sony', 'Phone'),
    '34:C7:31': ('Sony', 'Phone'), '3C:01:EF': ('Sony', 'TV'),
    '40:B8:37': ('Sony', 'TV'), '44:74:6C': ('Sony', 'TV'),
    '50:1A:C5': ('Sony', 'Phone'), '54:42:49': ('Sony', 'TV'),
    '5C:51:4F': ('Sony', 'Phone'), '64:BC:58': ('Sony', 'TV'),
    '70:35:09': ('Sony', 'TV'), '78:84:3C': ('Sony', 'TV'),
    '7C:57:3C': ('Sony', 'TV'), '7C:C3:A1': ('Sony', 'TV'),
    '80:19:70': ('Sony', 'Phone'), '84:16:F9': ('Sony', 'TV'),
    '88:78:73': ('Sony', 'Phone'), '90:C1:15': ('Sony', 'TV'),
    '98:0C:A5': ('Sony', 'TV'), 'A0:EA:D7': ('Sony', 'Phone'),
    'AC:9B:0A': ('Sony', 'TV'), 'B0:DF:C1': ('Sony', 'Phone'),
    'C0:28:8D': ('Sony', 'Phone'), 'CC:FB:65': ('Sony', 'TV'),
    'D4:C8:B0': ('Sony', 'TV'), 'D8:55:A3': ('Sony', 'Phone'),
    'E0:AC:CB': ('Sony', 'TV'), 'F0:BF:97': ('Sony', 'TV'),
    # ── Raspberry Pi ──
    'B8:27:EB': ('Raspberry Pi', 'IoT'), 'DC:A6:32': ('Raspberry Pi', 'IoT'),
    'E4:5F:01': ('Raspberry Pi', 'IoT'),
    # ── Amazon ──
    '00:BB:3A': ('Amazon', 'IoT'), '0C:47:C9': ('Amazon', 'IoT'),
    '18:74:2E': ('Amazon', 'IoT'), '34:D2:70': ('Amazon', 'IoT'),
    '40:B4:CD': ('Amazon', 'IoT'), '44:65:0D': ('Amazon', 'IoT'),
    '50:75:F1': ('Amazon', 'IoT'), '74:C2:46': ('Amazon', 'IoT'),
    '84:D6:D0': ('Amazon', 'IoT'), 'A4:08:F5': ('Amazon', 'IoT'),
    'B4:7C:9C': ('Amazon', 'IoT'), 'FC:65:DE': ('Amazon', 'IoT'),
    # ── Google / Nest ──
    '3C:5A:B4': ('Google', 'IoT'), '54:60:09': ('Google', 'IoT'),
    '6C:40:08': ('Google', 'IoT'), '94:95:A0': ('Google', 'IoT'),
    'A4:77:33': ('Google', 'IoT'), 'F4:F5:D8': ('Google', 'IoT'),
    'F4:F5:E8': ('Google', 'IoT'), 'FC:AA:14': ('Google', 'IoT'),
    # ── Microsoft ──
    '00:03:FF': ('Microsoft', 'PC'), '00:0D:3A': ('Microsoft', 'PC'),
    '00:12:5A': ('Microsoft', 'PC'), '00:15:5D': ('Microsoft', 'PC'),
    '00:17:FA': ('Microsoft', 'PC'), '00:1D:D8': ('Microsoft', 'PC'),
    '00:22:48': ('Microsoft', 'PC'), '00:50:F2': ('Microsoft', 'PC'),
    '28:18:78': ('Microsoft', 'PC'), '48:50:73': ('Microsoft', 'PC'),
    '60:45:BD': ('Microsoft', 'PC'), '7C:1E:52': ('Microsoft', 'PC'),
    '98:5F:D3': ('Microsoft', 'PC'), 'A4:02:B9': ('Microsoft', 'PC'),
    'B8:7E:F7': ('Microsoft', 'PC'), 'C8:51:22': ('Microsoft', 'PC'),
    'DC:0E:A1': ('Microsoft', 'PC'),
    # ── TP-Link Archer (additional) ──
    '3C:84:6A': ('TP-Link', 'Router'), '98:DA:C4': ('TP-Link', 'Router'),
    '98:DE:D0': ('TP-Link', 'Router'), 'A0:F3:C1': ('TP-Link', 'Router'),
    # ── ZTE ──
    '00:0F:E9': ('ZTE', 'Router'), '00:19:C6': ('ZTE', 'Router'),
    '00:26:ED': ('ZTE', 'Router'), '0C:05:E6': ('ZTE', 'Router'),
    '20:A6:CD': ('ZTE', 'Router'), '28:2C:02': ('ZTE', 'Router'),
    '2C:26:17': ('ZTE', 'Router'), '34:4B:50': ('ZTE', 'Router'),
    '40:65:A4': ('ZTE', 'Router'), '4C:54:99': ('ZTE', 'Router'),
    '50:6E:1F': ('ZTE', 'Router'), '54:22:F8': ('ZTE', 'Router'),
    '58:7A:62': ('ZTE', 'Router'), '5C:A8:6A': ('ZTE', 'Router'),
    '60:53:38': ('ZTE', 'Router'), '64:F6:9D': ('ZTE', 'Router'),
    '68:A3:78': ('ZTE', 'Router'), '6C:9C:ED': ('ZTE', 'Router'),
    '70:7C:58': ('ZTE', 'Router'), '74:1F:4A': ('ZTE', 'Router'),
    '78:39:7B': ('ZTE', 'Router'), '7C:B2:32': ('ZTE', 'Router'),
    '80:EC:CA': ('ZTE', 'Router'), '84:74:60': ('ZTE', 'Router'),
    '88:03:55': ('ZTE', 'Router'), '8C:97:EA': ('ZTE', 'Router'),
    '90:E6:BA': ('ZTE', 'Router'), '98:27:88': ('ZTE', 'Router'),
    '9C:00:65': ('ZTE', 'Router'),
    # ── VinGroup/VinFast (Vietnam) ──
    '00:00:2B': ('Viettel', 'Router'), '70:CC:73': ('Viettel', 'Router'),
    '9C:F6:DD': ('Viettel', 'Router'), 'AC:CF:23': ('Viettel', 'Router'),
    # ── Motorola ──
    '00:02:0F': ('Motorola', 'Phone'), '00:0A:28': ('Motorola', 'Phone'),
    '00:0B:06': ('Motorola', 'Phone'), '00:12:CE': ('Motorola', 'Phone'),
    '00:15:A0': ('Motorola', 'Phone'), '00:18:82': ('Motorola', 'Phone'),
    '00:1B:E3': ('Motorola', 'Phone'), '00:1C:9A': ('Motorola', 'Phone'),
    '24:DA:9B': ('Motorola', 'Phone'), '38:A5:1D': ('Motorola', 'Phone'),
    '3C:43:8E': ('Motorola', 'Phone'), '44:03:2C': ('Motorola', 'Phone'),
    '78:10:63': ('Motorola', 'Phone'), '84:58:A6': ('Motorola', 'Phone'),
    'AC:1F:74': ('Motorola', 'Phone'), 'C0:EE:40': ('Motorola', 'Phone'),
    'CC:F4:11': ('Motorola', 'Phone'), 'E0:75:0A': ('Motorola', 'Phone'),
    'F0:08:F1': ('Motorola', 'Phone'), 'FC:FC:48': ('Motorola', 'Phone'),
    # ── Nokia ──
    '00:1B:EE': ('Nokia', 'Phone'), '00:21:FE': ('Nokia', 'Phone'),
    '1C:77:F6': ('Nokia', 'Phone'), '20:A6:0C': ('Nokia', 'Phone'),
    '34:C8:6E': ('Nokia', 'Phone'), '40:04:0C': ('Nokia', 'Phone'),
    '44:74:6C': ('Nokia', 'Phone'), '4C:79:6E': ('Nokia', 'Phone'),
    '6C:B3:11': ('Nokia', 'Phone'), '8C:F5:A3': ('Nokia', 'Phone'),
    'A0:89:F0': ('Nokia', 'Phone'), 'D4:0A:A9': ('Nokia', 'Phone'),
    'E0:C7:67': ('Nokia', 'Phone'), 'EC:F4:51': ('Nokia', 'Phone'),
}


def is_locally_administered_mac(mac):
    """Returns True if MAC is locally-administered (randomized by OS for privacy).
    Locally administered bit = bit 1 of first octet.
    e.g. 42:xx:xx = 0100 0010 → bit1=1 → locally administered.
    """
    try:
        first_octet = int(mac.upper().replace('-', ':').split(':')[0], 16)
        return bool(first_octet & 0x02)  # bit 1 set
    except Exception:
        return False


def get_mac_vendor(mac):
    """Look up vendor name and device type from MAC address OUI.
    Also detects locally-administered (randomized/private) MACs."""
    if not mac or mac in ('-', ''):
        return 'Unknown', 'Unknown'
    normalized = mac.upper().replace('-', ':')
    # Detect MAC randomization (locally-administered bit)
    if is_locally_administered_mac(normalized):
        return 'Randomized MAC', 'Phone/PC (Privacy)'
    prefix = normalized[:8]
    result = OUI_DB.get(prefix)
    if result:
        return result[0], result[1]
    return 'Unknown', 'Unknown'


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


WINDOWS_PORTS_DEF = {
    80: {"name": "HTTP", "desc": "Web Server / Router Web Admin", "category": "Web"},
    443: {"name": "HTTPS", "desc": "Secure Web / SSL Server", "category": "Web"},
    3389: {"name": "RDP", "desc": "Remote Desktop Protocol (Điều khiển từ xa)", "category": "Windows Client/Server"},
    445: {"name": "SMB", "desc": "Server Message Block (Chia sẻ File & Máy in)", "category": "Windows File Sharing"},
    139: {"name": "NetBIOS", "desc": "NetBIOS Session Service", "category": "Windows File Sharing"},
    135: {"name": "RPC", "desc": "RPC Endpoint Mapper & WMI (Quản trị hệ thống)", "category": "Windows System"},
    1433: {"name": "MSSQL", "desc": "Microsoft SQL Server Database Engine", "category": "Database"},
    389: {"name": "LDAP", "desc": "Active Directory Domain Services (LDAP)", "category": "Active Directory"},
    636: {"name": "LDAPS", "desc": "Active Directory Secure LDAP (SSL)", "category": "Active Directory"},
    53: {"name": "DNS", "desc": "Domain Name System Server", "category": "Network Infrastructure"},
    88: {"name": "Kerberos", "desc": "Active Directory Kerberos Authentication", "category": "Active Directory"},
    5985: {"name": "WinRM HTTP", "desc": "Windows Remote Management (PowerShell Remoting)", "category": "Remote Admin"},
    5986: {"name": "WinRM HTTPS", "desc": "Windows Remote Management Secure (SSL)", "category": "Remote Admin"},
    22: {"name": "SSH", "desc": "OpenSSH Server / Thiết bị mạng / Linux", "category": "Remote Admin"},
    21: {"name": "FTP", "desc": "File Transfer Protocol (IIS FTP)", "category": "File Sharing"},
    3268: {"name": "Global Catalog", "desc": "Active Directory Global Catalog", "category": "Active Directory"},
    8080: {"name": "HTTP-Alt", "desc": "Alternate Web / Proxy / Tomcat", "category": "Web"},
    8443: {"name": "HTTPS-Alt", "desc": "Alternate HTTPS Web Admin", "category": "Web"},
    3306: {"name": "MySQL", "desc": "MySQL / MariaDB Database", "category": "Database"},
    5432: {"name": "PostgreSQL", "desc": "PostgreSQL Database Server", "category": "Database"}
}


def check_port(ip, port=80, timeout=0.35):
    """Fast TCP socket connect test. Returns True if port is open."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        code = s.connect_ex((ip, int(port)))
        s.close()
        return code == 0
    except Exception:
        return False


def check_http(ip, port=80, timeout=1):
    """Backward compatibility alias for check_port."""
    return check_port(ip, port, timeout)


def check_host_ports(ip, ports, timeout=0.35):
    """Checks multiple TCP ports on a host concurrently."""
    if not ports:
        return []
    
    unique_ports = sorted(list({int(p) for p in ports if str(p).isdigit()}))
    open_ports = []
    lock = threading.Lock()
    threads = []

    def test_single(p):
        if check_port(ip, p, timeout):
            with lock:
                open_ports.append(p)

    for p in unique_ports:
        t = threading.Thread(target=test_single, args=(p,), daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=timeout + 0.25)

    return sorted(open_ports)


def scan_single_host_ports(target_host, ports=None, timeout=0.45):
    """Scans specific or standard Windows/Server ports for a single host."""
    target = target_host.strip()
    if not target:
        return []

    if not ports:
        ports = list(WINDOWS_PORTS_DEF.keys())
    else:
        # Convert list of ints or string of ints
        parsed_ports = []
        for p in ports:
            if isinstance(p, int):
                parsed_ports.append(p)
            elif isinstance(p, str) and p.strip().isdigit():
                parsed_ports.append(int(p.strip()))
        ports = sorted(list(set(parsed_ports))) if parsed_ports else list(WINDOWS_PORTS_DEF.keys())

    results = []
    lock = threading.Lock()
    threads = []

    def worker(p):
        info = WINDOWS_PORTS_DEF.get(p, {
            "name": f"Port {p}",
            "desc": "Tùy chỉnh (Custom Port)",
            "category": "Custom"
        })
        t_start = time.time()
        is_open = check_port(target, p, timeout)
        duration_ms = round((time.time() - t_start) * 1000, 1)

        with lock:
            results.append({
                "port": p,
                "name": info["name"],
                "desc": info["desc"],
                "category": info["category"],
                "status": "OPEN" if is_open else "CLOSED",
                "is_open": is_open,
                "latency_ms": f"{duration_ms}ms"
            })

    for p in ports:
        t = threading.Thread(target=worker, args=(p,), daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=timeout + 0.3)

    return sorted(results, key=lambda x: x["port"])


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
    """Try DNS reverse lookup."""
    try:
        socket.setdefaulttimeout(timeout)
        name = socket.gethostbyaddr(ip)[0]
        return name if name and name != ip else ''
    except Exception:
        return ''


def get_hostname_netbios(ip, timeout=2):
    """Try NetBIOS name lookup via nbtstat (Windows only). Returns empty string on failure."""
    try:
        result = subprocess.run(
            ['nbtstat', '-A', ip],
            capture_output=True, text=True, timeout=timeout
        )
        output = result.stdout
        # Parse nbtstat output: look for <00> UNIQUE entries (workstation/domain name)
        for line in output.splitlines():
            # Example: '  DESKTOP-ABC123        <00>  UNIQUE'
            stripped = line.strip()
            if '<00>' in stripped and 'UNIQUE' in stripped:
                parts = stripped.split()
                if parts:
                    name = parts[0].strip()
                    if name and name.upper() not in ('NAME', 'REGISTERED', 'NODE'):
                        return name
    except Exception:
        pass
    return ''


def get_hostname_mdns(ip, timeout=1):
    """Try mDNS/Bonjour hostname lookup (sends query to port 5353).
    Works for Apple devices, Chromecasts, Linux avahi."""
    import struct
    try:
        # Build minimal mDNS PTR query for reverse lookup
        # Reverse IP e.g. 192.168.1.100 → 100.1.168.192.in-addr.arpa
        parts = ip.split('.')
        reverse = '.'.join(reversed(parts)) + '.in-addr.arpa'
        # DNS query packet
        query_id = 0x0000
        flags = 0x0000
        qdcount = 1
        header = struct.pack('>HHHHHH', query_id, flags, qdcount, 0, 0, 0)
        question = b''
        for label in reverse.split('.'):
            label_bytes = label.encode()
            question += bytes([len(label_bytes)]) + label_bytes
        question += b'\x00'  # End of name
        question += struct.pack('>HH', 12, 1)  # TYPE=PTR, CLASS=IN
        packet = header + question
        # Send to mDNS multicast
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.sendto(packet, ('224.0.0.251', 5353))
        data, _ = sock.recvfrom(4096)
        sock.close()
        # Try to extract domain name from response (simplified)
        if data and len(data) > 12:
            # Look for printable ASCII name in response after header
            resp = data[12:]
            name_parts = []
            i = 0
            while i < len(resp) - 1:
                length = resp[i]
                if length == 0:
                    break
                if length > 63 or i + 1 + length > len(resp):
                    break
                part = resp[i+1:i+1+length]
                if all(32 <= b < 127 for b in part):
                    name_parts.append(part.decode('ascii', errors='ignore'))
                i += 1 + length
            if name_parts:
                return '.'.join(name_parts[:2])  # hostname.local
    except Exception:
        pass
    return ''


def get_hostname_multi(ip, timeout=1):
    """Try multiple hostname resolution methods in order of speed:
    1. DNS reverse lookup (fast, works for routers + Windows with PTR)
    2. NetBIOS name (nbtstat, Windows machines on LAN)
    3. mDNS/Bonjour (Apple/Linux)
    Returns best available name, empty string if all fail."""
    # Method 1: DNS
    name = get_hostname(ip, timeout=timeout)
    if name:
        return name
    # Method 2: NetBIOS (Windows)
    name = get_hostname_netbios(ip, timeout=2)
    if name:
        return name
    # Method 3: mDNS
    name = get_hostname_mdns(ip, timeout=1)
    if name:
        return name
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


def scan_lan_network(subnet_str="", ip_start="", ip_end="", check_ping=True, check_hostname=True, check_mac=True, check_http_port=True, check_https_port=True, max_threads=50, ports_to_check=None):
    """Scans LAN network IP range with multi-threaded sweeps and Windows/Server port checks."""
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

    # Parse and combine ports to scan
    ports_list = []
    if ports_to_check:
        if isinstance(ports_to_check, (list, tuple)):
            for p in ports_to_check:
                if isinstance(p, int):
                    ports_list.append(p)
                elif isinstance(p, str) and p.strip().isdigit():
                    ports_list.append(int(p.strip()))
        elif isinstance(ports_to_check, str):
            for part in ports_to_check.replace(',', ' ').split():
                if part.isdigit():
                    ports_list.append(int(part))

    if check_http_port and 80 not in ports_list:
        ports_list.append(80)
    if check_https_port and 443 not in ports_list:
        ports_list.append(443)

    ports_list = sorted(list(set(ports_list)))

    arp_map = get_all_arp_macs() if check_mac else {}
    results = []
    res_queue = queue.Queue()

    def worker(ip):
        alive, ping_time = ping_host(ip, timeout=400)
        if alive:
            # Get MAC first (needed for vendor + hostname hints)
            mac = arp_map.get(ip) or (get_mac_from_arp(ip) if check_mac else "")

            # Vendor + device type lookup
            if mac and mac not in ('-', ''):
                vendor, device_type = get_mac_vendor(mac)
            else:
                vendor, device_type = '', 'Unknown'

            # Hostname: multi-method resolution
            if check_hostname:
                hostname = get_hostname_multi(ip, timeout=1)
            else:
                hostname = ''

            # Multi-port scanning for Windows & Server roles
            open_ports = check_host_ports(ip, ports_list, timeout=0.35) if ports_list else []
            http_open = (80 in open_ports)
            https_open = (443 in open_ports)

            # Determine final vendor display
            # If vendor unknown but we have MAC → show MAC OUI hint
            display_vendor = vendor if vendor else 'Unknown'

            res_queue.put({
                "ip": ip,
                "hostname": hostname if hostname else "",
                "mac": mac if mac else "",
                "vendor": display_vendor,
                "device_type": device_type,
                "brand": display_vendor,   # backward compat
                "latency_ms": ping_time or "<1ms",
                "ping": ping_time or "<1ms",
                "open_ports": open_ports,
                "http": http_open,
                "https": https_open,
                "rdp": (3389 in open_ports),
                "smb": (445 in open_ports),
                "sql": (1433 in open_ports),
                "winrm": (5985 in open_ports or 5986 in open_ports),
                "ldap": (389 in open_ports),
                "rpc": (135 in open_ports),
                "dns": (53 in open_ports),
                "ssh": (22 in open_ports),
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
        t.join(timeout=8)

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
