import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web_api import Api

api = Api()
res = api.get_installed_apps('all')
apps = res.get('data', [])
print(f"Total apps: {len(apps)}")
for a in apps:
    name = a.get('display_name', '')
    if any(k in name.lower() for k in ['7-zip', 'photoshop', 'zalo', 'chrome', 'brave', 'capcut', 'ultraviewer', 'faststone']):
        b64 = a.get('icon_b64', '')
        print(f"{name:<38} | HasIcon: {str(bool(b64)):<5} | {b64[:35]}")
