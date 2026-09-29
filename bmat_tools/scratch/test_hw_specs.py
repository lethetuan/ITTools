import subprocess
import json
import socket
import datetime
import os

def run_ps_json(cmd):
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-Command', f'{cmd} | ConvertTo-Json -Depth 3'], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if r.stdout.strip():
            data = json.loads(r.stdout.strip())
            if isinstance(data, dict):
                return [data]
            elif isinstance(data, list):
                return data
        return []
    except Exception as e:
        print("PS Error:", e)
        return []

print("=== LOGICAL DISKS ===")
disks = run_ps_json('Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | Select-Object DeviceID, FreeSpace, Size, VolumeName')
for d in disks:
    dev = d.get("DeviceID", "")
    free_gb = round(d.get("FreeSpace", 0) / (1024**3), 1)
    size_gb = round(d.get("Size", 0) / (1024**3), 1)
    print(f"Drive {dev}: {free_gb} GB free / {size_gb} GB total")

print("\n=== SYSTEM PRODUCT & SERVICE TAG ===")
prod = run_ps_json('Get-CimInstance Win32_ComputerSystemProduct | Select-Object IdentifyingNumber, UUID, Name, Vendor')
bios = run_ps_json('Get-CimInstance Win32_BIOS | Select-Object SerialNumber, Manufacturer, SMBIOSBIOSVersion, ReleaseDate')
print("Product:", prod)
print("BIOS:", bios)

print("\n=== BATTERY ===")
bat = run_ps_json('Get-CimInstance Win32_Battery | Select-Object Name, DeviceID, EstimatedChargeRemaining, BatteryStatus, DesignCapacity, FullChargeCapacity')
print("Battery:", bat)

print("\n=== NETWORK ADAPTERS ===")
net = run_ps_json('Get-CimInstance Win32_NetworkAdapter -Filter "NetConnectionStatus=2" | Select-Object Name, NetConnectionID, Speed')
print("Network:", net)
