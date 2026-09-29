"""
Windows Update & Security Manager
Enable/Disable Windows Update, Defender, UAC, SmartScreen with Status inspection
"""

import subprocess
import winreg
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS

WU_REG_PATH = r'SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU'
DEFENDER_REG = r'SOFTWARE\Policies\Microsoft\Windows Defender'
UAC_REG_PATH = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System'
SMARTSCREEN_REG_PATH = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer'


def get_win_update_status():
    """Returns complete real-time status of Windows Update, Defender, UAC, and SmartScreen."""
    wu_enabled = True
    wu_text = "🟢 Đang BẬT (Tự động cập nhật)"
    
    # 1. Check Registry Policy
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, WU_REG_PATH)
        val, _ = winreg.QueryValueEx(key, 'NoAutoUpdate')
        winreg.CloseKey(key)
        if val == 1:
            wu_enabled = False
            wu_text = "🔴 Đã TẮT VĨNH VIỄN (Group Policy)"
    except Exception:
        pass

    # 2. Check wuauserv Service status
    try:
        ps_out = subprocess.check_output(
            'powershell -NoProfile -Command "$s=Get-Service wuauserv; Write-Output ($s.Status.ToString() + \'|\' + $s.StartType.ToString())"',
            shell=True, text=True
        ).strip()
        if ps_out:
            parts = ps_out.split('|')
            status = parts[0] if len(parts) > 0 else ""
            start_type = parts[1] if len(parts) > 1 else ""
            if start_type.lower() == 'disabled' or status.lower() == 'stopped':
                if start_type.lower() == 'disabled':
                    wu_enabled = False
                    wu_text = "🔴 Đã TẮT VĨNH VIỄN (Dịch vụ wuauserv Disabled)"
    except Exception:
        pass

    # 3. Windows Defender
    wd_enabled = True
    wd_text = "🟢 Đang BẬT (Real-Time Protection)"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, DEFENDER_REG)
        val, _ = winreg.QueryValueEx(key, 'DisableAntiSpyware')
        winreg.CloseKey(key)
        if val == 1:
            wd_enabled = False
            wd_text = "🔴 Đã TẮT (Policy)"
    except Exception:
        pass

    # 4. UAC
    uac_enabled = True
    uac_text = "🟢 Đang BẬT (UAC Security Active)"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, UAC_REG_PATH)
        val, _ = winreg.QueryValueEx(key, 'EnableLUA')
        winreg.CloseKey(key)
        if val == 0:
            uac_enabled = False
            uac_text = "🔴 Đã TẮT (EnableLUA = 0)"
    except Exception:
        pass

    # 5. SmartScreen
    ss_enabled = True
    ss_text = "🟢 Đang BẬT"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, SMARTSCREEN_REG_PATH)
        val, _ = winreg.QueryValueEx(key, 'SmartScreenEnabled')
        winreg.CloseKey(key)
        if str(val).lower() in ('off', '0'):
            ss_enabled = False
            ss_text = "🔴 Đã TẮT"
    except Exception:
        pass

    return {
        "success": True,
        "wu_enabled": wu_enabled,
        "wu_status_text": wu_text,
        "defender_enabled": wd_enabled,
        "defender_status_text": wd_text,
        "uac_enabled": uac_enabled,
        "uac_status_text": uac_text,
        "smartscreen_enabled": ss_enabled,
        "smartscreen_status_text": ss_text
    }


def set_windows_update(enable):
    """Enables or permanently disables Windows Update service and registry policy."""
    try:
        if enable:
            try:
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, WU_REG_PATH)
                winreg.SetValueEx(key, 'NoAutoUpdate', 0, winreg.REG_DWORD, 0)
                winreg.SetValueEx(key, 'AUOptions', 0, winreg.REG_DWORD, 4)
                winreg.CloseKey(key)
            except Exception:
                pass
            subprocess.run("sc config wuauserv start= auto", shell=True)
            subprocess.run("net start wuauserv", shell=True)
            return {"success": True, "message": "✅ Đã BẬT thành công dịch vụ Windows Update & Security!"}
        else:
            try:
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, WU_REG_PATH)
                winreg.SetValueEx(key, 'NoAutoUpdate', 0, winreg.REG_DWORD, 1)
                winreg.CloseKey(key)
            except Exception:
                pass
            subprocess.run("net stop wuauserv", shell=True)
            subprocess.run("sc config wuauserv start= disabled", shell=True)
            return {"success": True, "message": "🚫 Đã TẮT VĨNH VIỄN dịch vụ Windows Update!"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def pause_windows_update_7days():
    """Pauses Windows Update for 7 days via PowerShell."""
    try:
        ps = '$date=(Get-Date).AddDays(7).ToString("yyyy-MM-dd"); Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" -Name "PauseUpdatesExpiryTime" -Value $date'
        subprocess.run(["powershell", "-NoProfile", "-Command", ps])
        return {"success": True, "message": "⏸️ Đã TẠM DỪNG Windows Update trong 7 ngày!"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def check_windows_update_now():
    """Opens native Windows Update action settings."""
    try:
        subprocess.Popen("explorer.exe ms-settings:windowsupdate-action", shell=True)
        return {"success": True, "message": "🔄 Đã mở trang kiểm tra Cập nhật Windows Update!"}
    except Exception as e:
        try:
            os.system("start ms-settings:windowsupdate")
            return {"success": True, "message": "🔄 Đã mở trang Windows Update!"}
        except Exception as ex:
            return {"success": False, "message": str(ex)}


def set_defender_status(enable):
    """Enables or disables Realtime Monitoring and Defender policy."""
    try:
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, DEFENDER_REG)
            winreg.SetValueEx(key, 'DisableAntiSpyware', 0, winreg.REG_DWORD, 0 if enable else 1)
            winreg.CloseKey(key)
        except Exception:
            pass

        flag = "$false" if enable else "$true"
        subprocess.run(f'powershell -NoProfile -Command "Set-MpPreference -DisableRealtimeMonitoring {flag}"', shell=True)
        return {"success": True, "message": f"{'✅ Đã BẬT' if enable else '🚫 Đã TẮT'} bảo vệ thời gian thực Windows Defender!"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def run_defender_scan(scan_type="quick"):
    """Runs QuickScan or FullScan via PowerShell."""
    try:
        st = "QuickScan" if scan_type == "quick" else "FullScan"
        subprocess.Popen(f'powershell -NoProfile -Command "Start-MpScan -ScanType {st}"', shell=True)
        return {"success": True, "message": f"🔍 Đã kích hoạt {st} cho Windows Defender!"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def set_uac_status(enable):
    """Enables or disables User Account Control (UAC)."""
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, UAC_REG_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, 'EnableLUA', 0, winreg.REG_DWORD, 1 if enable else 0)
        winreg.CloseKey(key)
        return {"success": True, "message": f"{'✅ Đã BẬT' if enable else '🚫 Đã TẮT'} UAC! (Cần khởi động lại máy để áp dụng)."}
    except Exception as e:
        return {"success": False, "message": str(e)}


def set_smartscreen_status(enable):
    """Enables or disables Windows SmartScreen guard."""
    try:
        val = "On" if enable else "Off"
        ps = f'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer" -Name "SmartScreenEnabled" -Value "{val}"'
        subprocess.run(["powershell", "-NoProfile", "-Command", ps])
        return {"success": True, "message": f"{'✅ Đã BẬT' if enable else '🚫 Đã TẮT'} SmartScreen!"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def open_security_shortcut(target):
    """Opens system setting shortcuts."""
    try:
        if target == "defender":
            try:
                subprocess.Popen("explorer.exe ms-settings:windowsdefender", shell=True)
            except Exception:
                subprocess.Popen("explorer.exe windowsdefender:", shell=True)
        elif target == "uac_settings":
            subprocess.Popen("UserAccountControlSettings.exe")
        else:
            try:
                subprocess.Popen("explorer.exe ms-settings:windowsupdate", shell=True)
            except Exception:
                os.system("start ms-settings:windowsupdate")
        return {"success": True, "message": "Đã mở trang cài đặt hệ thống!"}
    except Exception as e:
        return {"success": False, "message": str(e)}
