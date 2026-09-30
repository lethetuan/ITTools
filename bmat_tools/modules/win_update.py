"""
Windows Update & Security Manager
Enable/Disable Windows Update, Defender, UAC, SmartScreen with Status inspection
Accurate real-time detection based on Windows Services, SecurityCenter2, and Registry
"""

import subprocess
import winreg
import os
import sys
import json
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

WU_AU_REG = r'SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU'
WU_POLICY_REG = r'SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate'
WU_UX_REG = r'SOFTWARE\Microsoft\WindowsUpdate\UX\Settings'
DEFENDER_POLICY_REG = r'SOFTWARE\Policies\Microsoft\Windows Defender'
UAC_REG_PATH = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System'
SMARTSCREEN_REG_PATH = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer'


def get_win_update_status():
    """
    Returns complete, accurate real-time status of Windows Update,
    Antivirus/Defender, UAC, and SmartScreen.
    """
    # ── 1. WINDOWS UPDATE DETECTION ──────────────────────────────────────────
    wu_enabled = True
    wu_badge = "🟢 ĐANG BẬT"
    wu_text = "🟢 Đang BẬT (Tự động cập nhật)"

    # A. Check Services (wuauserv & UsoSvc)
    wuauserv_running = False
    wuauserv_start = "manual"
    usosvc_running = False

    try:
        ps_cmd = 'Get-Service wuauserv, UsoSvc -ErrorAction SilentlyContinue | Select-Object Name, Status, StartType | ConvertTo-Json'
        r = subprocess.run(['powershell', '-NoProfile', '-Command', ps_cmd],
                           capture_output=True, text=True, timeout=8)
        if r.returncode == 0 and r.stdout.strip():
            data = json.loads(r.stdout)
            if isinstance(data, dict):
                data = [data]
            for s in data:
                name = str(s.get('Name', '')).lower()
                status_raw = s.get('Status')
                start_raw = s.get('StartType')

                # 4=Running, 1=Stopped; or string 'Running'
                is_running = (status_raw == 4 or str(status_raw).lower() == 'running')
                start_type_str = str(start_raw).lower()

                if name == 'wuauserv':
                    wuauserv_running = is_running
                    wuauserv_start = start_type_str
                elif name == 'usosvc':
                    usosvc_running = is_running
    except Exception:
        pass

    # B. Check Pause Expiry in UX Settings
    pause_until_str = None
    try:
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, WU_UX_REG, 0, winreg.KEY_READ)
        try:
            val, _ = winreg.QueryValueEx(k, 'PauseUpdatesExpiryTime')
            if val:
                dt = datetime.datetime.fromisoformat(str(val).replace('Z', '+00:00'))
                if dt > datetime.datetime.now(datetime.timezone.utc):
                    pause_until_str = dt.astimezone().strftime('%d/%m/%Y %H:%M')
        except Exception:
            pass
        winreg.CloseKey(k)
    except Exception:
        pass

    # C. Check Group Policy
    no_auto = 0
    disable_access = 0
    try:
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, WU_AU_REG, 0, winreg.KEY_READ)
        try:
            no_auto, _ = winreg.QueryValueEx(k, 'NoAutoUpdate')
        except Exception:
            pass
        winreg.CloseKey(k)
    except Exception:
        pass

    try:
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, WU_POLICY_REG, 0, winreg.KEY_READ)
        try:
            disable_access, _ = winreg.QueryValueEx(k, 'DisableWindowsUpdateAccess')
        except Exception:
            pass
        winreg.CloseKey(k)
    except Exception:
        pass

    # D. Determine Windows Update Status
    if pause_until_str:
        wu_enabled = False
        wu_badge = "⏸️ TẠM DỪNG"
        wu_text = f"⏸️ Đang TẠM DỪNG cập nhật đến {pause_until_str}"
    elif (wuauserv_start in ('disabled', '4') and not wuauserv_running) or disable_access == 1:
        wu_enabled = False
        wu_badge = "🔴 ĐÃ TẮT"
        wu_text = "🔴 Đã TẮT VĨNH VIỄN (Dịch vụ wuauserv: Disabled)"
    elif wuauserv_running or usosvc_running:
        wu_enabled = True
        wu_badge = "🟢 ĐANG BẬT"
        if no_auto == 1:
            wu_text = "🟢 Đang BẬT (Dịch vụ đang chạy, bật chế độ tải thủ công)"
        else:
            wu_text = "🟢 Đang BẬT (Dịch vụ Windows Update đang hoạt động)"
    else:
        wu_enabled = True
        wu_badge = "🟢 SẴN SÀNG"
        wu_text = "🟢 Đang BẬT (Sẵn sàng khởi động khi có cập nhật)"

    # ── 2. ANTIVIRUS / DEFENDER DETECTION ────────────────────────────────────
    wd_enabled = True
    wd_badge = "🟢 ĐANG BẬT"
    wd_text = "🟢 Đang BẬT (Real-Time Protection)"
    has_third_party = False
    third_party_name = ""

    # A. Check 3rd party antivirus in SecurityCenter2
    try:
        ps_av = subprocess.run([
            'powershell', '-NoProfile', '-Command',
            'Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct -ErrorAction SilentlyContinue | Select-Object displayName, productState | ConvertTo-Json'
        ], capture_output=True, text=True, timeout=8)
        if ps_av.returncode == 0 and ps_av.stdout.strip():
            av_data = json.loads(ps_av.stdout)
            if isinstance(av_data, dict):
                av_data = [av_data]
            for p in av_data:
                name = str(p.get('displayName', '')).strip()
                state = int(p.get('productState', 0))
                # Bitmask: (state & 0x1000) != 0 indicates real-time protection is enabled
                is_rt_enabled = bool((state & 0x1000) != 0)
                if 'windows defender' not in name.lower() and is_rt_enabled and name:
                    has_third_party = True
                    third_party_name = name
                    break
    except Exception:
        pass

    if has_third_party:
        wd_enabled = True
        wd_badge = "🟢 AN TOÀN"
        wd_text = f"🛡️ Đang bảo vệ bởi: {third_party_name} (Defender đã nhường quyền)"
    else:
        # B. Check Windows Defender directly
        is_def_rt = False
        try:
            ps_def = subprocess.run([
                'powershell', '-NoProfile', '-Command',
                '$s = Get-MpComputerStatus -ErrorAction SilentlyContinue; [PSCustomObject]@{RT=$s.RealTimeProtectionEnabled; AM=$s.AMServiceEnabled} | ConvertTo-Json'
            ], capture_output=True, text=True, timeout=8)
            if ps_def.returncode == 0 and ps_def.stdout.strip():
                d_info = json.loads(ps_def.stdout)
                is_def_rt = bool(d_info.get('RT') or d_info.get('AM'))
            else:
                # Fallback to checking WinDefend service
                ps_svc = subprocess.run(
                    ['sc', 'query', 'WinDefend'],
                    capture_output=True, text=True, timeout=5
                )
                is_def_rt = 'RUNNING' in ps_svc.stdout
        except Exception:
            is_def_rt = True

        wd_enabled = is_def_rt
        wd_badge = "🟢 ĐANG BẬT" if is_def_rt else "🔴 ĐÃ TẮT"
        wd_text = "🟢 Đang BẬT (Real-Time Protection)" if is_def_rt else "🔴 Đã TẮT (Real-Time Protection không hoạt động)"

    # ── 3. UAC DETECTION ─────────────────────────────────────────────────────
    uac_enabled = True
    uac_text = "🟢 Đang BẬT (Mặc định Windows)"
    try:
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, UAC_REG_PATH, 0, winreg.KEY_READ)
        v, _ = winreg.QueryValueEx(k, 'EnableLUA')
        winreg.CloseKey(k)
        if v == 0:
            uac_enabled = False
            uac_text = "🔴 Đã TẮT (EnableLUA = 0)"
    except Exception:
        pass

    # ── 4. SMARTSCREEN DETECTION ─────────────────────────────────────────────
    ss_enabled = True
    ss_text = "🟢 Đang BẬT"
    try:
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, SMARTSCREEN_REG_PATH, 0, winreg.KEY_READ)
        v, _ = winreg.QueryValueEx(k, 'SmartScreenEnabled')
        winreg.CloseKey(k)
        if str(v).lower() in ('off', '0'):
            ss_enabled = False
            ss_text = "🔴 Đã TẮT"
    except Exception:
        pass

    return {
        "success": True,
        "wu_enabled": wu_enabled,
        "wu_badge": wu_badge,
        "wu_status_text": wu_text,
        "defender_enabled": wd_enabled,
        "defender_badge": wd_badge,
        "defender_status_text": wd_text,
        "has_third_party": has_third_party,
        "third_party_name": third_party_name,
        "uac_enabled": uac_enabled,
        "uac_status_text": uac_text,
        "smartscreen_enabled": ss_enabled,
        "smartscreen_status_text": ss_text
    }


def set_windows_update(enable):
    """Enables or permanently disables Windows Update service and registry policy."""
    try:
        if enable:
            # 1. Clean Registry Policies
            try:
                k = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, WU_AU_REG)
                winreg.SetValueEx(k, 'NoAutoUpdate', 0, winreg.REG_DWORD, 0)
                winreg.SetValueEx(k, 'AUOptions', 0, winreg.REG_DWORD, 4)
                winreg.CloseKey(k)
            except Exception:
                pass

            try:
                k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, WU_POLICY_REG, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(k, 'DisableWindowsUpdateAccess')
                winreg.CloseKey(k)
            except Exception:
                pass

            # 2. Clear Pause Registry Keys
            try:
                k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, WU_UX_REG, 0, winreg.KEY_SET_VALUE)
                for name in [
                    'PauseUpdatesExpiryTime', 'PauseFeatureUpdatesStartTime',
                    'PauseFeatureUpdatesEndTime', 'PauseQualityUpdatesStartTime',
                    'PauseQualityUpdatesEndTime', 'PauseUpdatesStartTime'
                ]:
                    try:
                        winreg.DeleteValue(k, name)
                    except Exception:
                        pass
                winreg.CloseKey(k)
            except Exception:
                pass

            # 3. Configure and Start Services
            subprocess.run("sc config wuauserv start= auto", shell=True, capture_output=True)
            subprocess.run("net start wuauserv", shell=True, capture_output=True)
            subprocess.run("sc config UsoSvc start= auto", shell=True, capture_output=True)
            subprocess.run("net start UsoSvc", shell=True, capture_output=True)
            subprocess.run("sc config bits start= auto", shell=True, capture_output=True)
            subprocess.run("net start bits", shell=True, capture_output=True)

            # 4. Enable Scheduled Tasks
            subprocess.run('schtasks /Change /TN "\\Microsoft\\Windows\\WindowsUpdate\\Scheduled Start" /Enable', shell=True, capture_output=True)
            subprocess.run('schtasks /Change /TN "\\Microsoft\\Windows\\UpdateOrchestrator\\Schedule Scan" /Enable', shell=True, capture_output=True)

            return {"success": True, "message": "✅ Đã BẬT thành công dịch vụ Windows Update & hệ thống cập nhật!"}
        else:
            # 1. Set Registry Policies to Disable
            try:
                k = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, WU_AU_REG)
                winreg.SetValueEx(k, 'NoAutoUpdate', 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(k, 'AUOptions', 0, winreg.REG_DWORD, 1)
                winreg.CloseKey(k)
            except Exception:
                pass

            try:
                k = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, WU_POLICY_REG)
                winreg.SetValueEx(k, 'DisableWindowsUpdateAccess', 0, winreg.REG_DWORD, 1)
                winreg.CloseKey(k)
            except Exception:
                pass

            # 2. Stop and Disable Services
            subprocess.run("net stop wuauserv", shell=True, capture_output=True)
            subprocess.run("sc config wuauserv start= disabled", shell=True, capture_output=True)
            subprocess.run("net stop UsoSvc", shell=True, capture_output=True)
            subprocess.run("sc config UsoSvc start= disabled", shell=True, capture_output=True)
            subprocess.run("net stop WaaSMedicSvc", shell=True, capture_output=True)
            subprocess.run("sc config WaaSMedicSvc start= disabled", shell=True, capture_output=True)

            # 3. Disable Scheduled Tasks
            subprocess.run('schtasks /Change /TN "\\Microsoft\\Windows\\WindowsUpdate\\Scheduled Start" /Disable', shell=True, capture_output=True)
            subprocess.run('schtasks /Change /TN "\\Microsoft\\Windows\\UpdateOrchestrator\\Schedule Scan" /Disable', shell=True, capture_output=True)

            return {"success": True, "message": "🚫 Đã TẮT VĨNH VIỄN dịch vụ và các tiến trình Windows Update!"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def pause_windows_update_7days():
    """Pauses Windows Update for 7 days via direct UTC registry timestamps."""
    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        expiry = now + datetime.timedelta(days=7)
        start_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        expiry_str = expiry.strftime('%Y-%m-%dT%H:%M:%SZ')

        k = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, WU_UX_REG)
        winreg.SetValueEx(k, 'PauseUpdatesExpiryTime', 0, winreg.REG_SZ, expiry_str)
        winreg.SetValueEx(k, 'PauseFeatureUpdatesStartTime', 0, winreg.REG_SZ, start_str)
        winreg.SetValueEx(k, 'PauseFeatureUpdatesEndTime', 0, winreg.REG_SZ, expiry_str)
        winreg.SetValueEx(k, 'PauseQualityUpdatesStartTime', 0, winreg.REG_SZ, start_str)
        winreg.SetValueEx(k, 'PauseQualityUpdatesEndTime', 0, winreg.REG_SZ, expiry_str)
        winreg.SetValueEx(k, 'PauseUpdatesStartTime', 0, winreg.REG_SZ, start_str)
        winreg.CloseKey(k)

        expiry_local = expiry.astimezone().strftime('%d/%m/%Y')
        return {"success": True, "message": f"⏸️ Đã TẠM DỪNG Windows Update trong 7 ngày (đến ngày {expiry_local})!"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def check_windows_update_now():
    """Opens native Windows Update action settings."""
    try:
        subprocess.Popen("explorer.exe ms-settings:windowsupdate-action", shell=True)
        return {"success": True, "message": "🔄 Đã mở trang kiểm tra Cập nhật Windows Update!"}
    except Exception:
        try:
            os.startfile("ms-settings:windowsupdate")
            return {"success": True, "message": "🔄 Đã mở trang Windows Update!"}
        except Exception as ex:
            return {"success": False, "message": str(ex)}


def set_defender_status(enable):
    """Enables or disables Realtime Monitoring and Defender policy."""
    try:
        # Check if 3rd party antivirus is managing security
        status = get_win_update_status()
        if status.get("has_third_party"):
            tp_name = status.get("third_party_name", "Phần mềm diệt virus bên thứ 3")
            subprocess.Popen("explorer.exe windowsdefender:", shell=True)
            return {
                "success": True,
                "message": f"Máy tính đang sử dụng {tp_name} làm phần mềm bảo vệ chính. Để bật/tắt, vui lòng thao tác trong {tp_name} hoặc trong cửa sổ Windows Security vừa mở."
            }

        if enable:
            subprocess.run("sc start WinDefend", shell=True, capture_output=True)
            r = subprocess.run(
                'powershell -NoProfile -Command "Set-MpPreference -DisableRealtimeMonitoring 0"',
                shell=True, capture_output=True, text=True
            )
            return {"success": True, "message": "✅ Đã BẬT bảo vệ thời gian thực Windows Defender!"}
        else:
            r = subprocess.run(
                'powershell -NoProfile -Command "Set-MpPreference -DisableRealtimeMonitoring 1"',
                shell=True, capture_output=True, text=True
            )
            if r.returncode != 0:
                # Most likely Tamper Protection is active
                subprocess.Popen("explorer.exe windowsdefender://threatsettings", shell=True)
                return {
                    "success": False,
                    "message": "Không thể tắt Defender trực tiếp vì tính năng Tamper Protection đang bật. Vui lòng tắt Tamper Protection trong cửa sổ Windows Security vừa mở."
                }
            return {"success": True, "message": "🚫 Đã TẮT bảo vệ thời gian thực Windows Defender!"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def run_defender_scan(scan_type="quick"):
    """Runs QuickScan or FullScan via PowerShell."""
    try:
        status = get_win_update_status()
        if status.get("has_third_party"):
            tp_name = status.get("third_party_name", "Phần mềm diệt virus")
            subprocess.Popen("explorer.exe windowsdefender:", shell=True)
            return {
                "success": True,
                "message": f"Máy tính đang dùng {tp_name}. Đang mở Windows Security để bạn quản lý tính năng quét an toàn."
            }

        st = "QuickScan" if scan_type == "quick" else "FullScan"
        subprocess.run("sc start WinDefend", shell=True, capture_output=True)
        subprocess.Popen(f'powershell -NoProfile -Command "Start-MpScan -ScanType {st}"', shell=True)
        return {"success": True, "message": f"🔍 Đã kích hoạt {st} cho Windows Defender!"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def set_uac_status(enable):
    """Enables or disables User Account Control (UAC)."""
    try:
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, UAC_REG_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(k, 'EnableLUA', 0, winreg.REG_DWORD, 1 if enable else 0)
        winreg.SetValueEx(k, 'ConsentPromptBehaviorAdmin', 0, winreg.REG_DWORD, 5 if enable else 0)
        winreg.CloseKey(k)
        return {"success": True, "message": f"{'✅ Đã BẬT' if enable else '🚫 Đã TẮT'} UAC! (Cần khởi động lại máy để áp dụng hoàn toàn)."}
    except Exception as e:
        return {"success": False, "message": str(e)}


def set_smartscreen_status(enable):
    """Enables or disables Windows SmartScreen guard."""
    try:
        val = "On" if enable else "Off"
        # 1. Explorer SmartScreen
        k = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, SMARTSCREEN_REG_PATH)
        winreg.SetValueEx(k, 'SmartScreenEnabled', 0, winreg.REG_SZ, val)
        winreg.CloseKey(k)

        # 2. System Policy SmartScreen
        try:
            k = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Policies\Microsoft\Windows\System')
            winreg.SetValueEx(k, 'EnableSmartScreen', 0, winreg.REG_DWORD, 1 if enable else 0)
            winreg.CloseKey(k)
        except Exception:
            pass

        return {"success": True, "message": f"{'✅ Đã BẬT' if enable else '🚫 Đã TẮT'} Windows SmartScreen!"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def open_security_shortcut(target):
    """Opens system setting shortcuts."""
    try:
        if target == "defender":
            try:
                subprocess.Popen("explorer.exe windowsdefender:", shell=True)
            except Exception:
                subprocess.Popen("explorer.exe ms-settings:windowsdefender", shell=True)
        elif target == "uac_settings":
            subprocess.Popen("UserAccountControlSettings.exe")
        else:
            try:
                subprocess.Popen("explorer.exe ms-settings:windowsupdate", shell=True)
            except Exception:
                try:
                    os.startfile("ms-settings:windowsupdate")
                except Exception:
                    pass
        return {"success": True, "message": "Đã mở trang cài đặt hệ thống!"}
    except Exception as e:
        return {"success": False, "message": str(e)}
