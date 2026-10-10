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
    Strictly reports real machine state without false assumptions.
    If a status cannot be accurately verified, returns None (displayed as '⚪ N/A').
    """
    # ── BATCH QUERY POWERSHELL FOR FAST, CONSOLIDATED STATUS ──────────────────
    ps_data = {}
    try:
        ps_cmd = """& {
            $ProgressPreference = 'SilentlyContinue'
            $r = [ordered]@{}
            try {
                $r['av'] = @(Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct -ErrorAction Stop | Select-Object displayName, productState)
            } catch {
                $r['av'] = $null
            }
            try {
                $s = Get-MpComputerStatus -ErrorAction Stop
                $r['mp_rt'] = [bool]$s.RealTimeProtectionEnabled
                $r['mp_av'] = [bool]$s.AntivirusEnabled
                $r['mp_ok'] = $true
            } catch {
                $r['mp_rt'] = $null
                $r['mp_av'] = $null
                $r['mp_ok'] = $false
            }
            try {
                $p = Get-MpPreference -ErrorAction Stop
                $r['pref_drm'] = [bool]$p.DisableRealtimeMonitoring
                $r['pref_ok'] = $true
            } catch {
                $r['pref_drm'] = $null
                $r['pref_ok'] = $false
            }
            try {
                $r['svc'] = @(Get-Service wuauserv, UsoSvc -ErrorAction SilentlyContinue | Select-Object Name, Status, StartType)
            } catch {
                $r['svc'] = $null
            }
            $r | ConvertTo-Json -Depth 3 -Compress
        }"""
        r = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', ps_cmd],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            ps_data = json.loads(r.stdout.strip())
    except Exception:
        ps_data = {}

    # ── 1. WINDOWS UPDATE DETECTION ──────────────────────────────────────────
    wu_enabled = None
    wu_badge = "⚪ N/A"
    wu_text = "⚪ N/A (Không lấy được trạng thái Windows Update)"

    # A. Check Pause Expiry in UX Settings
    pause_until_str = None
    try:
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, WU_UX_REG, 0, winreg.KEY_READ)
        for p_key in ['PauseUpdatesExpiryTime', 'PauseFeatureUpdatesEndTime', 'PauseQualityUpdatesEndTime']:
            try:
                val, _ = winreg.QueryValueEx(k, p_key)
                if val:
                    dt = datetime.datetime.fromisoformat(str(val).replace('Z', '+00:00'))
                    if dt > datetime.datetime.now(datetime.timezone.utc):
                        pause_until_str = dt.astimezone().strftime('%d/%m/%Y %H:%M')
                        break
            except Exception:
                pass
        winreg.CloseKey(k)
    except Exception:
        pass

    # B. Check Group Policy
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

    # C. Service details (Primary Source of Truth: wuauserv service)
    svc_list = ps_data.get('svc')
    wuauserv_found = False
    wuauserv_running = False
    wuauserv_start = ""
    usosvc_running = False

    if isinstance(svc_list, list):
        for s in svc_list:
            if not isinstance(s, dict):
                continue
            name = str(s.get('Name', '')).lower()
            status_raw = s.get('Status')
            start_raw = s.get('StartType')
            is_running = (status_raw == 4 or str(status_raw).lower() == 'running')
            start_str = str(start_raw).lower()

            if name == 'wuauserv':
                wuauserv_found = True
                wuauserv_running = is_running
                wuauserv_start = start_str
            elif name == 'usosvc':
                usosvc_running = is_running

    # Fallback to direct sc command if not found via PowerShell
    if not wuauserv_found:
        try:
            qc = subprocess.run('sc qc wuauserv', shell=True, capture_output=True, text=True, timeout=3).stdout
            q = subprocess.run('sc query wuauserv', shell=True, capture_output=True, text=True, timeout=3).stdout
            if 'START_TYPE' in qc:
                wuauserv_found = True
                if 'AUTO_START' in qc:
                    wuauserv_start = '2'
                elif 'DEMAND_START' in qc:
                    wuauserv_start = '3'
                elif 'DISABLED' in qc:
                    wuauserv_start = '4'
                wuauserv_running = ('STATE' in q and 'RUNNING' in q)
        except Exception:
            pass

    # D. Evaluate Windows Update status based on real machine state
    if pause_until_str:
        wu_enabled = False
        wu_badge = "⏸️ TẠM DỪNG"
        wu_text = f"⏸️ Đang TẠM DỪNG cập nhật đến {pause_until_str}"
    elif wuauserv_found:
        if wuauserv_running:
            wu_enabled = True
            wu_badge = "🟢 ĐANG BẬT"
            wu_text = "🟢 Đang BẬT (Dịch vụ Windows Update đang chạy)"
        elif wuauserv_start in ('disabled', '4'):
            wu_enabled = False
            wu_badge = "🔴 ĐÃ TẮT"
            wu_text = "🔴 Đã TẮT VĨNH VIỄN (Dịch vụ wuauserv: Disabled)"
        elif wuauserv_start in ('automatic', 'auto', '2'):
            wu_enabled = True
            wu_badge = "🟢 ĐANG BẬT"
            wu_text = "🟢 Đang BẬT (Khởi động: Tự động / Trigger Start)"
        elif wuauserv_start in ('manual', 'demand', '3'):
            wu_enabled = True
            wu_badge = "🟢 SẴN SÀNG"
            wu_text = "🟢 Đang BẬT (Khởi động: Thủ công / Manual)"
        elif usosvc_running:
            wu_enabled = True
            wu_badge = "🟢 ĐANG BẬT"
            wu_text = "🟢 Đang BẬT (Update Orchestrator đang chạy)"
        else:
            wu_enabled = None
            wu_badge = "⚪ N/A"
            wu_text = "⚪ N/A (Không xác định được trạng thái)"
    elif disable_access == 1:
        wu_enabled = False
        wu_badge = "🔴 ĐÃ TẮT"
        wu_text = "🔴 Đã TẮT (Chính sách: DisableWindowsUpdateAccess)"
    else:
        wu_enabled = None
        wu_badge = "⚪ N/A"
        wu_text = "⚪ N/A (Không lấy được trạng thái Windows Update)"

    # ── 2. ANTIVIRUS / DEFENDER REAL-TIME PROTECTION DETECTION ───────────────
    wd_enabled = None
    wd_badge = "⚪ N/A"
    wd_text = "⚪ N/A (Không xác định được trạng thái)"
    has_third_party = False
    third_party_name = ""

    av_list = ps_data.get('av')
    if isinstance(av_list, dict):
        av_list = [av_list]
    elif not isinstance(av_list, list):
        av_list = []

    # Check for 3rd-party antivirus first
    for p in av_list:
        if not isinstance(p, dict):
            continue
        name = str(p.get('displayName', '')).strip()
        if not name or 'windows defender' in name.lower():
            continue

        has_third_party = True
        third_party_name = name
        state = int(p.get('productState', 0))
        # Bitmask 0x1000 indicates real-time protection enabled in SecurityCenter2
        is_rt_enabled = bool((state & 0x1000) != 0)
        wd_enabled = is_rt_enabled
        if is_rt_enabled:
            wd_badge = "🟢 AN TOÀN"
            wd_text = f"🛡️ Đang bảo vệ bởi: {third_party_name} (Defender đã nhường quyền)"
        else:
            wd_badge = "🔴 ĐÃ TẮT"
            wd_text = f"🔴 Đã TẮT bảo vệ: {third_party_name}"
        break

    if not has_third_party:
        # NO 3rd-party antivirus -> Check Windows Defender Real-Time Protection directly
        mp_ok = ps_data.get('mp_ok', False)
        mp_rt = ps_data.get('mp_rt')

        if mp_ok and mp_rt is not None:
            # Direct status from Get-MpComputerStatus.RealTimeProtectionEnabled
            wd_enabled = bool(mp_rt)
            if wd_enabled:
                wd_badge = "🟢 ĐANG BẬT"
                wd_text = "🟢 Đang BẬT (Real-Time Protection)"
            else:
                wd_badge = "🔴 ĐÃ TẮT"
                wd_text = "🔴 Đã TẮT (Real-Time Protection không hoạt động)"
        else:
            # Fallback 1: Check Get-MpPreference.DisableRealtimeMonitoring
            pref_ok = ps_data.get('pref_ok', False)
            pref_drm = ps_data.get('pref_drm')
            if pref_ok and pref_drm is not None:
                if pref_drm is True:
                    wd_enabled = False
                    wd_badge = "🔴 ĐÃ TẮT"
                    wd_text = "🔴 Đã TẮT (DisableRealtimeMonitoring = True)"
                else:
                    wd_enabled = True
                    wd_badge = "🟢 ĐANG BẬT"
                    wd_text = "🟢 Đang BẬT (Real-Time Protection)"
            else:
                # Fallback 2: Check Windows Defender entry in SecurityCenter2
                defender_in_sc = None
                for p in av_list:
                    if isinstance(p, dict) and 'windows defender' in str(p.get('displayName', '')).lower():
                        defender_in_sc = p
                        break

                if defender_in_sc:
                    state = int(defender_in_sc.get('productState', 0))
                    is_rt = bool((state & 0x1000) != 0)
                    wd_enabled = is_rt
                    wd_badge = "🟢 ĐANG BẬT" if is_rt else "🔴 ĐÃ TẮT"
                    wd_text = "🟢 Đang BẬT (Real-Time Protection)" if is_rt else "🔴 Đã TẮT (Real-Time Protection không hoạt động)"
                else:
                    # Fallback 3: Registry policies
                    try:
                        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection', 0, winreg.KEY_READ)
                        drm, _ = winreg.QueryValueEx(k, 'DisableRealtimeMonitoring')
                        winreg.CloseKey(k)
                        if drm == 1:
                            wd_enabled = False
                            wd_badge = "🔴 ĐÃ TẮT"
                            wd_text = "🔴 Đã TẮT (Chính sách: DisableRealtimeMonitoring)"
                    except Exception:
                        pass

                    if wd_enabled is None:
                        try:
                            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Policies\Microsoft\Windows Defender', 0, winreg.KEY_READ)
                            das, _ = winreg.QueryValueEx(k, 'DisableAntiSpyware')
                            winreg.CloseKey(k)
                            if das == 1:
                                wd_enabled = False
                                wd_badge = "🔴 ĐÃ TẮT"
                                wd_text = "🔴 Đã TẮT (Chính sách: DisableAntiSpyware)"
                        except Exception:
                            pass

    # ── 3. UAC DETECTION ─────────────────────────────────────────────────────
    uac_enabled = None
    uac_badge = "⚪ N/A"
    uac_text = "⚪ N/A (Không đọc được Registry UAC)"
    try:
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, UAC_REG_PATH, 0, winreg.KEY_READ)
        v, _ = winreg.QueryValueEx(k, 'EnableLUA')
        winreg.CloseKey(k)
        if v == 0:
            uac_enabled = False
            uac_badge = "🔴 ĐÃ TẮT"
            uac_text = "🔴 Đã TẮT (EnableLUA = 0)"
        else:
            uac_enabled = True
            uac_badge = "🟢 ĐANG BẬT"
            uac_text = "🟢 Đang BẬT (Mặc định Windows)"
    except Exception:
        pass

    # ── 4. SMARTSCREEN DETECTION ─────────────────────────────────────────────
    ss_enabled = None
    ss_badge = "⚪ N/A"
    ss_text = "⚪ N/A (Không đọc được Registry SmartScreen)"
    ss_found = False

    # Check Explorer key
    try:
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, SMARTSCREEN_REG_PATH, 0, winreg.KEY_READ)
        v, _ = winreg.QueryValueEx(k, 'SmartScreenEnabled')
        winreg.CloseKey(k)
        val_str = str(v).strip().lower()
        if val_str in ('off', '0'):
            ss_enabled = False
            ss_found = True
        elif val_str in ('warn', 'requireadmin', 'on', '1'):
            ss_enabled = True
            ss_found = True
    except Exception:
        pass

    # Check Policy key
    if not ss_found:
        try:
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Policies\Microsoft\Windows\System', 0, winreg.KEY_READ)
            v, _ = winreg.QueryValueEx(k, 'EnableSmartScreen')
            winreg.CloseKey(k)
            val_str = str(v).strip().lower()
            if val_str in ('0', 'off'):
                ss_enabled = False
                ss_found = True
            elif val_str in ('1', 'warn', 'on'):
                ss_enabled = True
                ss_found = True
        except Exception:
            pass

    if ss_found:
        if ss_enabled:
            ss_badge = "🟢 ĐANG BẬT"
            ss_text = "🟢 Đang BẬT"
        else:
            ss_badge = "🔴 ĐÃ TẮT"
            ss_text = "🔴 Đã TẮT"

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
        "uac_badge": uac_badge,
        "uac_status_text": uac_text,
        "smartscreen_enabled": ss_enabled,
        "smartscreen_badge": ss_badge,
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
