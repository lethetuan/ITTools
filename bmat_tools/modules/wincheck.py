"""
WinCheck Module for IT-Tools 2026
Full License Audit, Crack Detection, Hardware Inspection & Remediation Engine
Ported from WinCheck (Go/Wails) to 100% Python
Author: Lê Thế Tuấn | 0352 194 195 | https://lethetuanpc.blogspot.com/
"""

import os
import sys
import re
import json
import socket
import datetime
import subprocess
import winreg

# ── KNOWN PIRACY DOMAINS & PATTERNS ─────────────────────────────────────────
PIRACY_DOMAINS = [
    "kms.digiboy.ir", "kms.cx", "kms8.msguides.com", "kms9.msguides.com",
    "kms.luobotou.org", "kms.v2ray.com", "kms.03k.org", "kms.chinancu.xyz",
    "kms.cat333.com", "kms.ddns.net", "kms.lotro.cc", "kms.bServer.ir",
    "kms.c12.rtu.lv", "kms.pub", "kms.app", "kms.icu", "kms.space"
]

PIRACY_PROCESSES = [
    "kmspico", "kmsauto", "autopico", "sppextcomobjpatcher", "vlmcsd",
    "heu_kms", "kmstools", "kms4k", "tsforge", "kms38", "w10digital"
]

PIRACY_SERVICES = [
    "kmspico", "kmsauto", "sppextcomobj", "vlmcsd", "heu_kms", "kms38",
    "kmspicoservice", "kmsautosvc"
]

PIRACY_TASKS = [
    "autopico", "kmspico", "kmsauto", "kms38", "activation", "w10digitalactivation"
]

PIRACY_PATHS = [
    r"C:\Program Files\KMSpico",
    r"C:\Program Files (x86)\KMSpico",
    r"C:\Windows\KMS",
    r"C:\ProgramData\KMSAuto",
    r"C:\Windows\SECOH-QAD.exe",
    r"C:\Windows\SECOH-QAD.dll",
    r"C:\Windows\KMS-R@1n.exe"
]

GENERIC_KEYS = {
    "Y4G6T": "Windows 10/11 Pro (Generic Key)",
    "VK7JG": "Windows 10/11 Pro (Generic Key)",
    "W269N": "Windows 10/11 Pro Volume (GVLK)",
    "TX9XD": "Windows 10/11 Home (Generic Key)",
    "3KHY7": "Windows 10/11 Home Single Language",
    "DCPHK": "Windows 10/11 Enterprise (Generic Key)",
    "NPPR9": "Windows 10/11 Enterprise Volume (GVLK)",
}

# ── LOG HELPER ───────────────────────────────────────────────────────────────
def _log(log_obj, level, message):
    if hasattr(log_obj, "insert"):
        tag_map = {"INFO": "info", "SUCCESS": "ok", "WARN": "warn", "ERROR": "error", "STEP": "step"}
        tag = tag_map.get(level, "info")
        log_obj.insert("end", f"[{level}] {message}\n", tag)
        if hasattr(log_obj, "see"):
            log_obj.see("end")
    elif hasattr(log_obj, "log"):
        log_obj.log(level, message)
    else:
        print(f"[{level}] {message}")


# ── PRODUCT KEY DECODER (DigitalProductId) ──────────────────────────────────
def decode_digital_product_key(dpk_bytes):
    """Decodes 25-character Windows Product Key from Registry DigitalProductId binary data."""
    if not dpk_bytes or len(dpk_bytes) < 67:
        return None
    try:
        digits = "BCDFGHJKMPQRTVWXY2346789"
        key_offset = 52
        is_win8 = (dpk_bytes[key_offset + 14] >> 3) & 1
        dpk_bytes = bytearray(dpk_bytes)
        dpk_bytes[key_offset + 14] = (dpk_bytes[key_offset + 14] & 0xF7) | ((is_win8 & 1) << 3)

        decoded = []
        for i in range(24, -1, -1):
            cur = 0
            for j in range(14, -1, -1):
                cur = cur * 256 + dpk_bytes[key_offset + j]
                dpk_bytes[key_offset + j] = (cur // 24) & 0xFF
                cur %= 24
            decoded.insert(0, digits[cur])

        if is_win8:
            first_char = decoded[0]
            # Replace first char logic for Win8/10
            decoded_str = "".join(decoded)
            decoded_str = decoded_str[1:cur+1] + "N" + decoded_str[cur+1:]
        else:
            decoded_str = "".join(decoded)

        # Insert dashes
        return "-".join([decoded_str[i:i+5] for i in range(0, 25, 5)])
    except Exception:
        return None


def get_installed_product_key():
    """Reads installed Product Key from Windows Registry DigitalProductId."""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
            try:
                dpk, _ = winreg.QueryValueEx(key, "DigitalProductId")
                decoded = decode_digital_product_key(dpk)
                if decoded and len(decoded) == 29:
                    return decoded
            except Exception:
                pass
    except Exception:
        pass
    return None


def get_oem_bios_key():
    """Reads OEM Product Key embedded in BIOS/UEFI ACPI MSDM table via PowerShell/WMI."""
    try:
        ps_cmd = "(Get-WmiObject -Class SoftwareLicensingService).OA3xOriginalProductKey"
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, encoding="utf-8", errors="ignore")
        key = r.stdout.strip()
        if key and len(key) == 29:
            return key
    except Exception:
        pass
    return ""


def get_backup_product_key():
    """Reads Backup Product Key from Registry BackupProductKeyDefault."""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform") as key:
            val, _ = winreg.QueryValueEx(key, "BackupProductKeyDefault")
            if val and len(val) == 29:
                return val
    except Exception:
        pass
    return ""


# ── FULL AUDIT ENGINE ────────────────────────────────────────────────────────
def run_wincheck_audit():
    """Performs full WinCheck 10-layer audit and returns structured Verdict object."""
    indicators = []
    checks = []
    suspicious_count = 0
    critical_kms = False

    # 1. Check KMS Host Name
    kms_host = ""
    try:
        ps_kms = "(Get-WmiObject -Class SoftwareLicensingService).KeyManagementServiceMachine"
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps_kms], capture_output=True, text=True, encoding="utf-8", errors="ignore")
        kms_host = r.stdout.strip()
    except Exception:
        pass

    if not kms_host:
        checks.append({"name": "Máy Chủ KMS", "status": "ok", "statusText": "Sạch (Không có)", "detail": "Không cấu hình máy chủ KMS ngoài."})
    else:
        kms_lower = kms_host.lower()
        if any(h in kms_lower for h in ["127.0.0.1", "localhost", "10.0.0.10", "127."]):
            critical_kms = True
            suspicious_count += 1
            indicators.append({"severity": "critical", "text": f"Phát hiện giả lập KMS cục bộ: {kms_host}"})
            checks.append({"name": "Máy Chủ KMS", "status": "detected", "statusText": "Phát Hiện Lậu", "detail": f"KMS Giả Lập Local ({kms_host})"})
        elif any(d in kms_lower for d in PIRACY_DOMAINS):
            critical_kms = True
            suspicious_count += 1
            indicators.append({"severity": "critical", "text": f"Phát hiện máy chủ KMS lậu công cộng: {kms_host}"})
            checks.append({"name": "Máy Chủ KMS", "status": "detected", "statusText": "Phát Hiện Lậu", "detail": f"KMS Lậu Công Cộng ({kms_host})"})
        else:
            checks.append({"name": "Máy Chủ KMS", "status": "info", "statusText": "Thông Tin", "detail": f"Máy chủ KMS: {kms_host}"})

    # 2. Check Port 1688 Listening (Local KMS Emulator)
    try:
        r = subprocess.run("netstat -ano", shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        if ":1688 " in r.stdout and "LISTENING" in r.stdout:
            # Check OS edition
            is_server = "server" in sys.platform.lower()
            if not is_server:
                critical_kms = True
                suspicious_count += 1
                indicators.append({"severity": "critical", "text": "Cổng KMS 1688 đang mở listening trên máy khách (Local KMS Emulator)"})
                checks.append({"name": "Cổng KMS 1688", "status": "detected", "statusText": "Phát Hiện Lậu", "detail": "Cổng 1688 đang mở (Local Emulator)"})
            else:
                checks.append({"name": "Cổng KMS 1688", "status": "ok", "statusText": "Bình Thường", "detail": "Server KMS Host Service"})
        else:
            checks.append({"name": "Cổng KMS 1688", "status": "ok", "statusText": "Sạch", "detail": "Cổng 1688 không mở."})
    except Exception:
        checks.append({"name": "Cổng KMS 1688", "status": "skipped", "statusText": "Bỏ Qua", "detail": "Không thể quét port 1688."})

    # 3. Check IFEO Hijacks
    ifeo_found = False
    try:
        reg_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as base_key:
            for target in ["sppsvc.exe", "osppsvc.exe", "slui.exe"]:
                try:
                    with winreg.OpenKey(base_key, target) as sub_key:
                        val, _ = winreg.QueryValueEx(sub_key, "Debugger")
                        if val:
                            ifeo_found = True
                            critical_kms = True
                            suspicious_count += 1
                            indicators.append({"severity": "critical", "text": f"Phát hiện can thiệp IFEO Debugger trên {target}: {val}"})
                except Exception:
                    pass
    except Exception:
        pass

    if ifeo_found:
        checks.append({"name": "Can Thiệp IFEO System", "status": "detected", "statusText": "Phát Hiện Lậu", "detail": "Phát hiện hook IFEO can thiệp dich vụ bản quyền."})
    else:
        checks.append({"name": "Can Thiệp IFEO System", "status": "ok", "statusText": "Sạch", "detail": "Không có hook IFEO can thiệp."})

    # 4. Check Crack Processes
    proc_found = []
    try:
        r = subprocess.run("tasklist /fo csv /nh", shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        for line in r.stdout.splitlines():
            name = line.split(",")[0].replace('"', '').lower()
            for p_pattern in PIRACY_PROCESSES:
                if p_pattern in name and name not in proc_found:
                    proc_found.append(name)
    except Exception:
        pass

    if proc_found:
        critical_kms = True
        suspicious_count += len(proc_found)
        indicators.append({"severity": "critical", "text": f"Đang chạy tiến trình crack: {', '.join(proc_found)}"})
        checks.append({"name": "Tiến Trình Crack", "status": "detected", "statusText": "Phát Hiện Lậu", "detail": f"Đang chạy: {', '.join(proc_found)}"})
    else:
        checks.append({"name": "Tiến Trình Crack", "status": "ok", "statusText": "Sạch", "detail": "Không thấy tiến trình crack chạy ngầm."})

    # 5. Check Crack Services
    svc_found = []
    try:
        r = subprocess.run("sc query state= all", shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        for line in r.stdout.splitlines():
            if line.strip().startswith("SERVICE_NAME:"):
                s_name = line.split(":", 1)[1].strip().lower()
                for s_pattern in PIRACY_SERVICES:
                    if s_pattern in s_name and s_name not in svc_found:
                        svc_found.append(s_name)
    except Exception:
        pass

    if svc_found:
        critical_kms = True
        suspicious_count += len(svc_found)
        indicators.append({"severity": "critical", "text": f"Phát hiện dịch vụ crack cài trên hệ thống: {', '.join(svc_found)}"})
        checks.append({"name": "Dịch Vụ Crack (Services)", "status": "detected", "statusText": "Phát Hiện Lậu", "detail": f"Dịch vụ lậu: {', '.join(svc_found)}"})
    else:
        checks.append({"name": "Dịch Vụ Crack (Services)", "status": "ok", "statusText": "Sạch", "detail": "Không có dịch vụ lậu cài cắm."})

    # 6. Check Crack Scheduled Tasks
    task_found = []
    try:
        r = subprocess.run("schtasks /query /fo csv /nh", shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        for line in r.stdout.splitlines():
            t_name = line.split(",")[0].replace('"', '').lower()
            for t_pattern in PIRACY_TASKS:
                if t_pattern in t_name and t_name not in task_found:
                    task_found.append(t_name)
    except Exception:
        pass

    if task_found:
        critical_kms = True
        suspicious_count += len(task_found)
        indicators.append({"severity": "critical", "text": f"Phát hiện tác vụ Task Scheduler gia hạn lậu: {', '.join(task_found)}"})
        checks.append({"name": "Tác Vụ Định Kỳ (Task Scheduler)", "status": "detected", "statusText": "Phát Hiện Lậu", "detail": f"Tác vụ gia hạn: {', '.join(task_found)}"})
    else:
        checks.append({"name": "Tác Vụ Định Kỳ (Task Scheduler)", "status": "ok", "statusText": "Sạch", "detail": "Không có tác vụ gia hạn lậu."})

    # 7. Check Crack Files & Folders
    files_found = []
    for path in PIRACY_PATHS:
        if os.path.exists(path):
            files_found.append(path)

    if files_found:
        critical_kms = True
        suspicious_count += len(files_found)
        indicators.append({"severity": "critical", "text": f"Phát hiện thư mục/file công cụ crack: {', '.join(files_found)}"})
        checks.append({"name": "Tệp Tín & Thư Mục Crack", "status": "detected", "statusText": "Phát Hiện Lậu", "detail": f"Tồn tại: {', '.join(files_found)}"})
    else:
        checks.append({"name": "Tệp Tín & Thư Mục Crack", "status": "ok", "statusText": "Sạch", "detail": "Không có thư mục công cụ lậu."})

    # 8. License Facts & Key Information
    installed_key = get_installed_product_key()
    oem_key = get_oem_bios_key()
    backup_key = get_backup_product_key()

    keys_list = []
    if installed_key:
        last5 = installed_key[-5:]
        note = "Key Bản Quyền Thật"
        tone = "ok"
        if last5 in GENERIC_KEYS:
            note = GENERIC_KEYS[last5]
            tone = "warn"
        keys_list.append({"label": "Key Đang Cài Đặt", "value": installed_key, "note": note, "tone": tone})

    if oem_key:
        keys_list.append({"label": "Key OEM BIOS (UEFI)", "value": oem_key, "note": "Key OEM Gốc Theo Máy", "tone": "neutral"})

    if backup_key:
        keys_list.append({"label": "Key Dự Phòng Registry", "value": backup_key, "note": "Bản Sao Lưu SPP Registry", "tone": "neutral"})

    # Determine Verdict Level
    if critical_kms:
        level = "critical"
        title = "PHÁT HIỆN DẤU HIỆU KÍCH HOẠT LẬU (CRACK / KMS EMULATOR)"
        summary = "Hệ thống đang sử dụng công cụ crack hoặc máy chủ KMS giả lập để kích hoạt Windows. Cần dọn dẹp sạch sẽ để đảm bảo an toàn bảo mật."
        type_label = "Kiểu Kích Hoạt Lậu:"
        if proc_found or svc_found or ":1688 " in str(checks):
            type_value = "KMS Giả Lập Cục Bộ (Local KMS Emulator / KMSpico)"
        elif kms_host:
            type_value = f"Máy Chủ KMS Lậu Mạng ({kms_host})"
        else:
            type_value = "Can Thiệp Cấu Hình Hệ Thống (IFEO / Registry Hack)"
    elif suspicious_count > 0:
        level = "suspicious"
        title = "PHÁT HIỆN ĐIỂM ĐÁNG NGỜ BẢN QUYỀN"
        summary = f"Phát hiện {suspicious_count} điểm nghi vấn cần kiểm tra kỹ hơn."
        type_label = "Tình Trạng:"
        type_value = f"Nghi Vấn ({suspicious_count} dấu hiệu)"
    else:
        level = "clean"
        title = "HỆ THỐNG SẠCH - KÍCH HOẠT HỢP LỆ"
        summary = "Windows được kích hoạt hợp lệ, không phát hiện dấu hiệu công cụ crack hay giả lập KMS lậu nào."
        type_label = "Phương Thức Kích Hoạt:"
        type_value = "Kích Hoạt Bản Quyền Hợp Lệ (Digital License / OEM / MAK)"

    return {
        "level": level,
        "title": title,
        "summary": summary,
        "typeLabel": type_label,
        "typeValue": type_value,
        "count": suspicious_count,
        "indicators": indicators,
        "checks": checks,
        "keys": keys_list
    }


# ── REMEDIATION ACTIONS ──────────────────────────────────────────────────────
def clean_crack(log):
    """Clean Crack / KMS Emulator / IFEO / Tasks / Services / Files / Keys (WinCheck Option 8)."""
    _log(log, "TITLE", "══ CLEAN CRACK & DỌN SẠCH KMS LẬU TOÀN DIỆN ══")
    _log(log, "WARN", "Cảnh báo: Thao tác này sẽ dọn sạch toàn bộ công cụ crack và gỡ bỏ key lậu khỏi Windows!")
    removed = 0

    # 1. Kill Crack Processes
    _log(log, "STEP", "1. Đang dừng các tiến trình crack...")
    try:
        r = subprocess.run("tasklist /fo csv /nh", shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        for line in r.stdout.splitlines():
            pname = line.split(",")[0].replace('"', '').lower()
            for pattern in PIRACY_PROCESSES:
                if pattern in pname and pname not in ["gatherosstate.exe", "clipup.exe"]:
                    _log(log, "INFO", f"Dừng tiến trình lậu: {pname}")
                    subprocess.run(f"taskkill /f /im {pname}", shell=True, capture_output=True)
                    removed += 1
    except Exception as e:
        _log(log, "ERROR", f"Lỗi dừng tiến trình: {e}")

    # 2. Stop and Delete Crack Services
    _log(log, "STEP", "2. Đang dừng & xóa dịch vụ crack...")
    try:
        r = subprocess.run("sc query state= all", shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        for line in r.stdout.splitlines():
            if line.strip().startswith("SERVICE_NAME:"):
                sname = line.split(":", 1)[1].strip().lower()
                for pattern in PIRACY_SERVICES:
                    if pattern in sname:
                        _log(log, "INFO", f"Xóa dịch vụ lậu: {sname}")
                        subprocess.run(f"sc stop {sname}", shell=True, capture_output=True)
                        subprocess.run(f"sc delete {sname}", shell=True, capture_output=True)
                        removed += 1
    except Exception as e:
        _log(log, "ERROR", f"Lỗi xóa dịch vụ: {e}")

    # 3. Remove Scheduled Tasks
    _log(log, "STEP", "3. Đang xóa tác vụ Task Scheduler lậu...")
    try:
        r = subprocess.run("schtasks /query /fo csv /nh", shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        for line in r.stdout.splitlines():
            tname = line.split(",")[0].replace('"', '').lower()
            for pattern in PIRACY_TASKS:
                if pattern in tname:
                    _log(log, "INFO", f"Xóa tác vụ lậu: {tname}")
                    subprocess.run(f'schtasks /delete /tn "{tname}" /f', shell=True, capture_output=True)
                    removed += 1
    except Exception as e:
        _log(log, "ERROR", f"Lỗi xóa tác vụ: {e}")

    # 4. Remove IFEO Hijacks
    _log(log, "STEP", "4. Đang gỡ bỏ hook IFEO can thiệp dịch vụ bản quyền...")
    reg_base = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"
    for target in ["sppsvc.exe", "osppsvc.exe", "slui.exe"]:
        try:
            subprocess.run(f'reg delete "HKLM\\{reg_base}\\{target}" /v Debugger /f', shell=True, capture_output=True)
            _log(log, "SUCCESS", f"Đã xóa hook IFEO Debugger trên {target}")
            removed += 1
        except Exception:
            pass

    # 5. Clear KMS Host Configuration
    _log(log, "STEP", "5. Đang xóa cấu hình máy chủ KMS trong Registry & Slmgr...")
    try:
        subprocess.run("cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /ckms", shell=True, capture_output=True)
        subprocess.run(r'reg delete "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform" /v KeyManagementServiceName /f', shell=True, capture_output=True)
        subprocess.run(r'reg delete "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform" /v KeyManagementServicePort /f', shell=True, capture_output=True)
        _log(log, "SUCCESS", "Đã gỡ máy chủ KMS lậu khỏi Windows.")
        removed += 1
    except Exception as e:
        _log(log, "ERROR", f"Lỗi gỡ KMS: {e}")

    # 6. Delete Crack Files & Folders
    _log(log, "STEP", "6. Đang xóa các tệp/thư mục công cụ crack...")
    for p in PIRACY_PATHS:
        if os.path.exists(p):
            try:
                if os.path.isdir(p):
                    subprocess.run(f'rmdir /s /q "{p}"', shell=True, capture_output=True)
                else:
                    os.remove(p)
                _log(log, "SUCCESS", f"Đã xóa: {p}")
                removed += 1
            except Exception as e:
                _log(log, "WARN", f"Không thể xóa {p}: {e}")

    # 7. Uninstall Product Keys
    _log(log, "STEP", "7. Đang gỡ bỏ key lậu & xóa bộ nhớ đệm Registry...")
    try:
        subprocess.run("cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /upk", shell=True, capture_output=True)
        subprocess.run("cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /cpky", shell=True, capture_output=True)
        _log(log, "SUCCESS", "Đã gỡ key bản quyền lậu và xóa sạch key khỏi Registry.")
        removed += 1
    except Exception as e:
        _log(log, "ERROR", f"Lỗi gỡ key: {e}")

    _log(log, "SUCCESS", f"Hoàn tất dọn sạch crack! Đã xử lý {removed} mục lậu.")


def clean_office_keys(log):
    """Finds Office installations, runs ospp.vbs /remhst, /dstatus, extracts keys, and /unpkey (WinCheck Option 9)."""
    _log(log, "TITLE", "══ CLEAN KEY OFFICE LẬU & DỌN MÁY CHỦ KMS OFFICE ══")
    _log(log, "INFO", "Đang quét các thư mục cài đặt Microsoft Office...")

    search_dirs = [
        r"C:\Program Files\Microsoft Office\Office16",
        r"C:\Program Files (x86)\Microsoft Office\Office16",
        r"C:\Program Files\Microsoft Office\Office15",
        r"C:\Program Files (x86)\Microsoft Office\Office15",
        r"C:\Program Files\Microsoft Office\Office14",
        r"C:\Program Files (x86)\Microsoft Office\Office14"
    ]

    found_dirs = [d for d in search_dirs if os.path.exists(os.path.join(d, "OSPP.VBS"))]

    if not found_dirs:
        _log(log, "WARN", "Không tìm thấy file OSPP.VBS của Microsoft Office trên máy tính.")
        return

    total_removed = 0
    for odir in found_dirs:
        _log(log, "STEP", f"Đang xử lý Office tại: {odir}")
        ospp_path = os.path.join(odir, "OSPP.VBS")

        # 1. Remove KMS host
        _log(log, "INFO", "Xóa cấu hình máy chủ KMS Office (/remhst)...")
        subprocess.run(f'cscript //nologo "{ospp_path}" /remhst', shell=True, capture_output=True)

        # 2. Check dstatus and extract keys
        _log(log, "INFO", "Quét danh sách key Office đang cài (/dstatus)...")
        r = subprocess.run(f'cscript //nologo "{ospp_path}" /dstatus', shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        output = r.stdout

        keys = re.findall(r"Last 5 characters of installed product key:\s*([A-Z0-9]{5})", output, re.IGNORECASE)
        if not keys:
            # Fallback regex
            keys = re.findall(r"[: ]\s*([A-Z0-9]{5})\s*$", output, re.MULTILINE)

        keys = list(set([k.upper() for k in keys if len(k) == 5]))

        if not keys:
            _log(log, "INFO", "Không tìm thấy key Office lậu nào trong thư mục này.")
            continue

        _log(log, "WARN", f"Tìm thấy {len(keys)} key Office: {', '.join(keys)}")
        for k in keys:
            _log(log, "INFO", f"Đang gỡ key Office: {k} (/unpkey:{k})...")
            unp = subprocess.run(f'cscript //nologo "{ospp_path}" /unpkey:{k}', shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
            if "successful" in unp.stdout.lower() or unp.returncode == 0:
                _log(log, "SUCCESS", f"Đã gỡ thành công key Office: {k}")
                total_removed += 1
            else:
                _log(log, "ERROR", f"Không thể gỡ key Office {k}")

    _log(log, "SUCCESS", f"Hoàn tất dọn dẹp Office! Đã gỡ bỏ {total_removed} key Office lậu.")


def install_win_key(key, log):
    """Installs a product key using slmgr /ipk."""
    _log(log, "INFO", f"Đang cài đặt Product Key mới: {key}...")
    r = subprocess.run(f"cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /ipk {key}", shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if "successful" in r.stdout.lower() or "thành công" in r.stdout.lower():
        _log(log, "SUCCESS", f"Đã cài đặt thành công Key bản quyền: {key}")
        return True
    else:
        _log(log, "ERROR", f"Không thể cài key: {r.stdout.strip()}")
        return False


def uninstall_win_key(log):
    """Uninstalls product key and clears registry using slmgr /upk & /cpky."""
    _log(log, "INFO", "Đang gỡ bỏ Product Key hiện tại...")
    subprocess.run("cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /upk", shell=True, capture_output=True)
    subprocess.run("cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /cpky", shell=True, capture_output=True)
    _log(log, "SUCCESS", "Đã gỡ bỏ key và xóa bộ nhớ đệm registry.")


def rearm_windows(log):
    """Rearms Windows trial period using slmgr /rearm."""
    _log(log, "INFO", "Đang đặt lại thời gian dùng thử (Rearm Windows)...")
    r = subprocess.run("cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /rearm", shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    _log(log, "SUCCESS", f"Kết quả Rearm: {r.stdout.strip()}")
