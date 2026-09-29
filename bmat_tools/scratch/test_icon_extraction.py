import os
import sys
import winreg
import subprocess
import base64

def find_browser_exe(browser_key):
    exe_names = {
        'Chrome': ['chrome.exe'],
        'Edge': ['msedge.exe'],
        'Brave': ['brave.exe'],
        'CocCoc': ['coccoc.exe', 'browser.exe'],
        'Firefox': ['firefox.exe'],
        'Opera': ['opera.exe'],
        'OperaGX': ['opera.exe']
    }

    localappdata = os.environ.get('LOCALAPPDATA', '')
    programfiles = os.environ.get('ProgramFiles', 'C:\\Program Files')
    programfilesx86 = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')

    common_paths = {
        'Chrome': [
            os.path.join(programfiles, r'Google\Chrome\Application\chrome.exe'),
            os.path.join(programfilesx86, r'Google\Chrome\Application\chrome.exe'),
            os.path.join(localappdata, r'Google\Chrome\Application\chrome.exe'),
        ],
        'Edge': [
            os.path.join(programfilesx86, r'Microsoft\Edge\Application\msedge.exe'),
            os.path.join(programfiles, r'Microsoft\Edge\Application\msedge.exe'),
        ],
        'Brave': [
            os.path.join(programfiles, r'BraveSoftware\Brave-Browser\Application\brave.exe'),
            os.path.join(localappdata, r'BraveSoftware\Brave-Browser\Application\brave.exe'),
        ],
        'CocCoc': [
            os.path.join(localappdata, r'CocCoc\Browser\Application\browser.exe'),
            os.path.join(programfiles, r'CocCoc\Browser\Application\browser.exe'),
        ],
        'Firefox': [
            os.path.join(programfiles, r'Mozilla Firefox\firefox.exe'),
            os.path.join(programfilesx86, r'Mozilla Firefox\firefox.exe'),
        ],
        'Opera': [
            os.path.join(localappdata, r'Programs\Opera\opera.exe'),
            os.path.join(programfiles, r'Opera\opera.exe'),
        ],
        'OperaGX': [
            os.path.join(localappdata, r'Programs\Opera GX\opera.exe'),
        ]
    }

    # 0. Check StartMenuInternet Registry
    for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
        try:
            with winreg.OpenKey(root, r"SOFTWARE\Clients\StartMenuInternet") as key:
                num_subkeys = winreg.QueryInfoKey(key)[0]
                for i in range(num_subkeys):
                    subkey_name = winreg.EnumKey(key, i)
                    if browser_key.lower() in subkey_name.lower() or (browser_key == 'Edge' and 'msedge' in subkey_name.lower()) or (browser_key == 'CocCoc' and ('coccoc' in subkey_name.lower() or 'browser' in subkey_name.lower())):
                        try:
                            with winreg.OpenKey(key, rf"{subkey_name}\shell\open\command") as cmd_k:
                                val, _ = winreg.QueryValueEx(cmd_k, "")
                                val = val.strip('"')
                                if os.path.exists(val):
                                    return val
                        except Exception:
                            pass
        except Exception:
            pass

    # 1. Check Registry App Paths
    for exe in exe_names.get(browser_key, []):
        for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            try:
                key_path = f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{exe}"
                with winreg.OpenKey(root, key_path) as k:
                    val, _ = winreg.QueryValueEx(k, "")
                    val = val.strip('"')
                    if os.path.exists(val):
                        return val
            except Exception:
                pass

    # 2. Check common paths
    for p in common_paths.get(browser_key, []):
        if os.path.exists(p):
            return p

    return None


def extract_icon_base64(exe_path):
    """Extracts associated icon from EXE file and returns base64 PNG data URL."""
    if not exe_path or not os.path.exists(exe_path):
        return None

    exe_path_clean = exe_path.replace("'", "''")
    ps_cmd = f"""
    [Reflection.Assembly]::LoadWithPartialName('System.Drawing') | Out-Null
    $exe = '{exe_path_clean}'
    if (Test-Path $exe) {{
        $icon = [System.Drawing.Icon]::ExtractAssociatedIcon($exe)
        if ($icon) {{
            $bmp = $icon.ToBitmap()
            $ms = New-Object System.IO.MemoryStream
            $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
            [Convert]::ToBase64String($ms.ToArray())
        }}
    }}
    """

    try:
        r = subprocess.run(['powershell', '-NoProfile', '-Command', ps_cmd], capture_output=True, text=True, timeout=10)
        b64_str = r.stdout.strip()
        if b64_str and len(b64_str) > 50:
            return f"data:image/png;base64,{b64_str}"
    except Exception as ex:
        print(f"Error extracting icon for {exe_path}: {ex}")

    return None


if __name__ == "__main__":
    for b in ['Chrome', 'Edge', 'Brave', 'CocCoc', 'Firefox', 'Opera', 'OperaGX']:
        exe = find_browser_exe(b)
        icon_b64 = extract_icon_base64(exe) if exe else None
        print(f"{b}: EXE = {exe} | Icon Base64 len = {len(icon_b64) if icon_b64 else 0}")
