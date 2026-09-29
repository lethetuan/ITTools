import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import subprocess
import socket
import urllib.request
import json

def get_network_adapters():
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    ext_ip = "N/A"
    try:
        ext_ip = urllib.request.urlopen('https://api.ipify.org', timeout=3).read().decode().strip()
    except Exception:
        pass

    adapters = []
    try:
        ps_script = (
            "Get-NetAdapter | ForEach-Object {"
            "  $n = $_.Name;"
            "  $m = $_.MacAddress;"
            "  $s = $_.Status;"
            "  $cfg = Get-NetIPConfiguration -InterfaceAlias $n -ErrorAction SilentlyContinue;"
            "  $ip = ($cfg.IPv4Address.IPAddress -join ', ');"
            "  $pfx = ($cfg.IPv4Address.PrefixLength -join ', ');"
            "  $gw = ($cfg.IPv4DefaultGateway.NextHop -join ', ');"
            "  $dns = ($cfg.DNSServer.ServerAddresses -join ', ');"
            "  [PSCustomObject]@{ Name=$n; IP=$ip; Prefix=$pfx; Gateway=$gw; DNS=$dns; MAC=$m; Status=$s }"
            "} | ConvertTo-Json -Depth 2"
        )
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, timeout=12)
        if res.returncode == 0 and res.stdout:
            data = json.loads(res.stdout)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                adapters.append({
                    "name": item.get("Name", ""),
                    "ip": item.get("IP", "") or "-",
                    "prefix": str(item.get("Prefix", "")) or "-",
                    "gateway": item.get("Gateway", "") or "-",
                    "dns": item.get("DNS", "") or "-",
                    "mac": item.get("MAC", "") or "-",
                    "status": item.get("Status", "Unknown")
                })
    except Exception as e:
        print("Lỗi get_network_adapters:", e)

    return {
        "local_ip": local_ip,
        "external_ip": ext_ip,
        "adapters": adapters
    }

if __name__ == "__main__":
    res = get_network_adapters()
    print("Local IP:", res["local_ip"])
    print("External IP:", res["external_ip"])
    print(f"Found {len(res['adapters'])} adapters:")
    for a in res["adapters"]:
        print(a)
