import os
import psutil

for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if 'IT Tool' in p.info['name'] or (p.info['cmdline'] and any('IT Tool' in c for c in p.info['cmdline'])):
            print(f"PID: {p.info['pid']}, Name: {p.info['name']}")
    except Exception:
        pass
