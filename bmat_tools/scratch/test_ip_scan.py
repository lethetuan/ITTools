import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import socket
import subprocess
import ipaddress
import threading
import queue
import time
from modules.ip_scanner import ping_host, get_hostname, get_mac_from_arp, get_mac_vendor, check_http

def get_local_subnet_range():
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

def scan_lan_network(subnet_str="", ip_start="", ip_end="", check_ping=True, check_hostname=True, check_mac=True, check_http_port=True, check_https_port=True, max_threads=50):
    ip_list = []
    if subnet_str and '/' in subnet_str:
        try:
            network = ipaddress.IPv4Network(subnet_str.strip(), strict=False)
            ip_list = [str(ip) for ip in list(network.hosts())[:500]]
        except Exception as e:
            print("Lỗi parse subnet:", e)

    if not ip_list and ip_start and ip_end:
        try:
            start = ipaddress.IPv4Address(ip_start.strip())
            end = ipaddress.IPv4Address(ip_end.strip())
            ip_list = [str(ipaddress.IPv4Address(i)) for i in range(int(start), int(end) + 1)]
        except Exception as e:
            print("Lỗi parse start/end ip:", e)

    if not ip_list:
        default_range = get_local_subnet_range()
        network = ipaddress.IPv4Network(default_range["subnet"], strict=False)
        ip_list = [str(ip) for ip in list(network.hosts())[:254]]

    results = []
    res_queue = queue.Queue()
    
    # We test scanning first 30 IPs for speed test
    test_ips = ip_list[:30]

    def worker(ip):
        alive, ping_time = ping_host(ip, timeout=300)
        if alive:
            hostname = get_hostname(ip, timeout=1) if check_hostname else ""
            mac = get_mac_from_arp(ip) if check_mac else ""
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
    for ip in test_ips:
        t = threading.Thread(target=worker, args=(ip,), daemon=True)
        threads.append(t)
        t.start()
        while len([x for x in threads if x.is_alive()]) >= max_threads:
            time.sleep(0.02)

    for t in threads:
        t.join(timeout=3)

    while not res_queue.empty():
        results.append(res_queue.get_nowait())

    return results

if __name__ == "__main__":
    print("Default range:", get_local_subnet_range())
    print("Scanning first 30 IPs...")
    found = scan_lan_network()
    print(f"Found {len(found)} online hosts:")
    for item in found:
        print(item)
