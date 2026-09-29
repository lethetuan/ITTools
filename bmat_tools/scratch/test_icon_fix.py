import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import modules.uninstall_manager as um

apps = um.get_installed_apps()
icon_count = 0
for a in apps[:30]:
    raw_icon = a.get('icon_b64') or a.get('icon') or ''
    has_icon = bool(raw_icon)
    if has_icon:
        icon_count += 1
    prefix = raw_icon[:40] if raw_icon else "NONE"
    print(f"{a['display_name'][:35]:<35} | HasIcon: {str(has_icon):<5} | {prefix}")

print(f"\nTotal icons in first 30: {icon_count} / 30")
