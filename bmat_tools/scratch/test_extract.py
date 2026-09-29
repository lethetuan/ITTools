import os
import subprocess
import winreg

def get_browser_exe_icon(exe_path):
    if not exe_path or not os.path.exists(exe_path):
        return None

    # Escape quotes for PowerShell
    script = f'''
    try {{
        [Reflection.Assembly]::LoadWithPartialName("System.Drawing") | Out-Null
        $icon = [System.Drawing.Icon]::ExtractAssociatedIcon("{exe_path}")
        if ($icon) {{
            $bmp = $icon.ToBitmap()
            $ms = New-Object System.IO.MemoryStream
            $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
            [Convert]::ToBase64String($ms.ToArray())
        }}
    }} catch {{
        Write-Output ""
    }}
    '''

    try:
        r = subprocess.run(['powershell', '-NoProfile', '-Command', script], capture_output=True, text=True, timeout=8)
        b64 = r.stdout.strip()
        if b64 and len(b64) > 100:
            return f"data:image/png;base64,{b64}"
    except Exception as e:
        print("Extract exception:", e)

    return None

paths = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\EdgeCore\153.0.4234.48\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\EdgeWebView\Application\msedge.exe",
    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
]

for p in paths:
    res = get_browser_exe_icon(p)
    print(p, "-> Base64 Len:", len(res) if res else None)
