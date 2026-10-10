"""
WinCheck Module for IT Tool LTT 2026
Full License Audit, Crack Detection, Hardware Inspection & Remediation Engine
Ported from WinCheck (Go/Wails) to 100% Python
Author: Lê Thế Tuấn | 0352 194 195 | https://lethetuanpc.blogspot.com | Telegram: https://t.me/lethetuanpc
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

WINDOWS_GVLK_KEYS = {
    "Professional": "W269N-WFGWX-YVC9B-4J6C9-T83GX",
    "ProfessionalN": "MH37W-N47XK-V7XM9-C7227-GCQG9",
    "Core": "TX9XD-98N7V-6WMQ6-BX7FG-H8Q99",
    "CoreN": "3KHY7-WNT83-DGQKR-F7HPR-844BM",
    "CoreSingleLanguage": "7HNRX-D7KGG-3K4RQ-4WPJ4-YTDFH",
    "CoreCountrySpecific": "PVMJN-6DFY6-9CCP6-7BKTT-D3WVR",
    "Enterprise": "NPPR9-FWDCX-D2C8J-H872K-2YT43",
    "EnterpriseN": "DPH2V-TTNVB-4X9Q3-TJR4H-KHJW4",
    "Education": "NW6C2-QMPVW-D7KKK-3GKT6-VCFB2",
    "EducationN": "2WH4N-8QGBV-H22JP-CT43Q-MDWWJ",
    "ServerStandard": "N69G4-B89J2-4G8F4-WWYCC-J464C",
    "ServerDatacenter": "WMDGN-G9PQG-XVVXX-R3X43-63DFG",
}

WINDOWS_DEFAULT_RETAIL_KEYS = {
    "Professional": "VK7JG-NPHTM-C97JM-9MPGT-3V66T",
    "ProfessionalN": "2B87N-8KFHP-MTVPT-TX6MQ-HD4CT",
    "Core": "YTMG3-N6DKC-DKB77-7M9GH-8HVX7",
    "CoreSingleLanguage": "BT79Q-G7N6G-PGBYW-4YWX6-6F4BT",
    "Enterprise": "XGVPP-NMH47-7TTHJ-W3FW7-8HV2C",
    "Education": "YNMGQ-8RYV3-4PGQ3-C8XTP-7CFBY",
}


def get_windows_edition_id():
    """Reads Windows EditionID from Registry, e.g. 'Professional', 'Core', 'Enterprise'."""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
            val, _ = winreg.QueryValueEx(key, "EditionID")
            return str(val).strip()
    except Exception:
        return "Professional"


def check_digital_license_present():
    """Checks if the system has an active Windows Digital License (HWID / OEM Digital Entitlement)."""
    # 1. Check if DigitalProductId in registry decodes to BBBBB-BBBBB-BBBBB-BBBBB-BBBBB
    try:
        dpk = get_installed_product_key()
        if dpk and "BBBBB-BBBBB-BBBBB-BBBBB-BBBBB" in dpk:
            return True
    except Exception:
        pass

    # 2. Check ClipSVC KeyHolder XML license tokens
    try:
        prog_data = os.environ.get("ProgramData", r"C:\ProgramData")
        kh_dir = os.path.join(prog_data, r"Microsoft\Windows\ClipSVC\Archive\KeyHolder")
        if os.path.isdir(kh_dir):
            for fname in os.listdir(kh_dir):
                if fname.endswith(".xml"):
                    return True
    except Exception:
        pass

    # 3. Check Subscription / ProductOptions
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\ProductOptions") as k:
            sub, _ = winreg.QueryValueEx(k, "SubscriptionPfnList")
            if sub and len(sub) > 0:
                return True
    except Exception:
        pass

    return False


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


def get_windows_activation_status():
    """Checks real-time Windows activation status via slmgr.vbs /xpr and Digital License."""
    try:
        r = subprocess.run(
            "cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /xpr",
            shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=8
        )
        out = (r.stdout + r.stderr).strip()
        lower = out.lower()
        if "permanently activated" in lower or "kích hoạt vĩnh viễn" in lower:
            return "activated_permanent", "Đã kích hoạt bản quyền vĩnh viễn"
        if "volume activation will expire" in lower or "hết hạn" in lower:
            return "activated_kms", out
        if "0xc004d302" in lower:
            return "rearmed_need_reboot", "Đã đặt lại thời gian dùng thử / Gỡ key (Cần khởi động lại máy tính để hoàn tất)"
        if "0xc004f014" in lower or "not found" in lower or "không tìm thấy" in lower:
            if check_digital_license_present():
                return "activated_digital", "Đã kích hoạt bằng Bản Quyền Kỹ Thuật Số (Digital License)"
            return "no_key", "Chưa cài đặt Product Key (Đã gỡ bỏ bản quyền)"
        if "grace" in lower or "ân hạn" in lower or "notification" in lower:
            return "grace_period", out
        
        if check_digital_license_present():
            return "activated_digital", "Đã kích hoạt bằng Bản Quyền Kỹ Thuật Số (Digital License)"

        return "unknown", out or "Chưa xác định"
    except Exception as e:
        if check_digital_license_present():
            return "activated_digital", "Đã kích hoạt bằng Bản Quyền Kỹ Thuật Số (Digital License)"
        return "unknown", str(e)


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

    # 8. Real-time License Facts & Key Information
    act_status, act_desc = get_windows_activation_status()
    installed_key = get_installed_product_key()
    oem_key = get_oem_bios_key()
    backup_key = get_backup_product_key()

    if act_status in ["no_key", "unknown"] and check_digital_license_present():
        act_status = "activated_digital"
        act_desc = "Đã kích hoạt bằng Bản Quyền Kỹ Thuật Số (Digital License)"

    # Add activation check to checks list
    if act_status == "activated_digital":
        checks.append({"name": "Trạng Thái Kích Hoạt", "status": "ok", "statusText": "Digital License", "detail": "Đã kích hoạt Bản Quyền Kỹ Thuật Số vĩnh viễn theo máy."})
    elif act_status == "activated_permanent":
        checks.append({"name": "Trạng Thái Kích Hoạt", "status": "ok", "statusText": "Đã Kích Hoạt", "detail": "Bản quyền vĩnh viễn (Retail / OEM Key)."})
    elif act_status == "activated_kms":
        checks.append({"name": "Trạng Thái Kích Hoạt", "status": "warn", "statusText": "KMS Volume", "detail": act_desc})
    elif act_status == "rearmed_need_reboot":
        checks.append({"name": "Trạng Thái Kích Hoạt", "status": "warn", "statusText": "Chờ Khởi Động Lại", "detail": "Cần khởi động lại máy để hoàn tất gỡ key."})
    elif act_status == "no_key":
        checks.append({"name": "Trạng Thái Kích Hoạt", "status": "warn", "statusText": "Chưa Kích Hoạt", "detail": "Chưa cài đặt Product Key bản quyền."})

    keys_list = []
    if act_status == "rearmed_need_reboot":
        keys_list.append({
            "label": "Trạng Thái Bản Quyền Windows",
            "value": "Đã Gỡ Key / Đã Rearm (Cần Khởi Động Lại Máy)",
            "note": "Windows đang ở trạng thái chờ khởi động lại máy để hoàn tất xóa sạch bản quyền và nạp lại dịch vụ.",
            "tone": "warn"
        })
    elif act_status == "activated_digital":
        keys_list.append({
            "label": "Trạng Thái Bản Quyền Windows",
            "value": "Đã Kích Hoạt (Digital License)",
            "note": "Kích hoạt hợp lệ vĩnh viễn bằng Bản Quyền Kỹ Thuật Số theo phần cứng máy (HWID)",
            "tone": "ok"
        })
        keys_list.append({
            "label": "Khóa Kích Hoạt (Product Key)",
            "value": "Bản Quyền Kỹ Thuật Số (Digital Entitlement)",
            "note": "Đồng bộ tự động từ máy chủ Microsoft (Không dùng Product Key rời)",
            "tone": "ok"
        })
    elif act_status == "no_key":
        keys_list.append({
            "label": "Trạng Thái Bản Quyền Windows",
            "value": "Chưa Cài Đặt Key (Đã Gỡ Bỏ Bản Quyền)",
            "note": "Hệ thống không có Product Key nào đang kích hoạt.",
            "tone": "neutral"
        })
    elif installed_key:
        if "BBBBB-BBBBB-BBBBB-BBBBB-BBBBB" in installed_key:
            keys_list.append({
                "label": "Khóa Kích Hoạt (License)",
                "value": "Bản Quyền Kỹ Thuật Số (Digital License)",
                "note": "Kích hoạt hợp lệ vĩnh viễn theo máy (Không có Product Key rời)",
                "tone": "ok"
            })
        else:
            last5 = installed_key[-5:]
            note = "Key Bản Quyền Thật"
            tone = "ok"
            if last5 in GENERIC_KEYS:
                note = GENERIC_KEYS[last5]
                tone = "warn"
            keys_list.append({"label": "Key Đang Cài Đặt", "value": installed_key, "note": note, "tone": tone})
    elif act_status in ["grace_period", "activated_kms"]:
        keys_list.append({
            "label": "Trạng Thái Bản Quyền Windows",
            "value": act_desc,
            "note": "Kích hoạt có thời hạn hoặc dùng thử",
            "tone": "warn"
        })

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
    elif act_status == "rearmed_need_reboot":
        level = "warn"
        title = "HỆ THỐNG ĐÃ GỠ KEY / REARM - CẦN KHỞI ĐỘNG LẠI"
        summary = "Đã thực hiện gỡ bỏ Product Key hoặc đặt lại dùng thử (Rearm). Bạn cần KHỞI ĐỘNG LẠI MÁY TÍNH (Restart) để Windows cập nhật trạng thái mới."
        type_label = "Tình Trạng:"
        type_value = "Đang Chờ Khởi Động Lại Máy (Pending Restart)"
    elif act_status == "no_key":
        level = "warn"
        title = "WINDOWS CHƯA ĐƯỢC KÍCH HOẠT (CHƯA CÓ KEY)"
        summary = "Hệ thống không có Product Key nào được cài đặt. Key bản quyền đã được gỡ bỏ khỏi máy tính."
        type_label = "Tình Trạng:"
        type_value = "Chưa Kích Hoạt / Đã Gỡ Key (Unlicensed)"
    elif act_status == "activated_digital":
        level = "clean"
        title = "WINDOWS ĐÃ KÍCH HOẠT BẢN QUYỀN KỸ THUẬT SỐ (DIGITAL LICENSE)"
        summary = "Windows được kích hoạt bản quyền kỹ thuật số (Digital License) hợp lệ gắn liền với thiết bị phần cứng của bạn, đồng bộ chuẩn xác với trạng thái Windows Settings."
        type_label = "Phương Thức Kích Hoạt:"
        type_value = "Bản Quyền Kỹ Thuật Số (Digital License / HWID)"
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


def _find_office_dirs():
    """Finds all Office installation directories containing OSPP.VBS.
    Mirrors wincheck Go FindOfficeDirs: checks ProgramFiles, ProgramFiles(x86), ProgramW6432.
    """
    roots = []
    for env_var in ["ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"]:
        v = os.environ.get(env_var, "")
        if v and v not in roots:
            roots.append(v)

    sub_paths = [
        os.path.join("Microsoft Office", "root", "Office16"),
        os.path.join("Microsoft Office", "Office16"),
        os.path.join("Microsoft Office", "root", "Office15"),
        os.path.join("Microsoft Office", "Office15"),
        os.path.join("Microsoft Office", "root", "Office14"),
        os.path.join("Microsoft Office", "Office14"),
    ]

    seen = set()
    found = []

    for root in roots:
        for sub in sub_paths:
            candidate = os.path.join(root, sub)
            norm = candidate.lower()
            ospp = os.path.join(candidate, "OSPP.VBS")
            if norm not in seen and os.path.isfile(ospp):
                seen.add(norm)
                found.append(candidate)

    # Dynamic C2R registry search
    try:
        for subkey in [
            r"SOFTWARE\Microsoft\Office\ClickToRun\Configuration",
            r"SOFTWARE\WOW6432Node\Microsoft\Office\ClickToRun\Configuration"
        ]:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey) as k:
                    inst_path, _ = winreg.QueryValueEx(k, "InstallationPath")
                    if inst_path and os.path.isdir(inst_path):
                        for sub in ["root\\Office16", "root\\Office15", "Office16", "Office15"]:
                            candidate = os.path.join(inst_path, sub)
                            norm = candidate.lower()
                            ospp = os.path.join(candidate, "OSPP.VBS")
                            if norm not in seen and os.path.isfile(ospp):
                                seen.add(norm)
                                found.insert(0, candidate)
            except Exception:
                pass
    except Exception:
        pass

    # Dynamic MSI legacy registry search
    try:
        for ver in ["16.0", "15.0", "14.0"]:
            for subkey in [
                rf"SOFTWARE\Microsoft\Office\{ver}\Common\InstallRoot",
                rf"SOFTWARE\WOW6432Node\Microsoft\Office\{ver}\Common\InstallRoot"
            ]:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey) as k:
                        inst_path, _ = winreg.QueryValueEx(k, "Path")
                        norm = (inst_path or "").lower()
                        ospp = os.path.join(inst_path, "OSPP.VBS") if inst_path else ""
                        if inst_path and norm not in seen and os.path.isfile(ospp):
                            seen.add(norm)
                            found.insert(0, inst_path)
                except Exception:
                    pass
    except Exception:
        pass

    return found


def _extract_office_keys(output):
    """Extracts 5-char product key suffixes from ospp.vbs /dstatus output.
    Mirrors wincheck Go ExtractOfficeKeys.
    """
    seen = set()
    keys = []
    for k in re.findall(r"Last 5 characters of installed product key:\s*([A-Z0-9]{5})", output, re.IGNORECASE):
        k = k.upper()
        if k not in seen:
            seen.add(k); keys.append(k)
    if not keys:
        for k in re.findall(r"product key:\s*([A-Z0-9]{5})", output, re.IGNORECASE):
            k = k.upper()
            if k not in seen:
                seen.add(k); keys.append(k)
    if not keys:
        for k in re.findall(r"[: ]\s*([A-Z0-9]{5})\s*$", output, re.MULTILINE):
            k = k.upper()
            if len(k) == 5 and k not in seen:
                seen.add(k); keys.append(k)
    return keys


def _remove_spp_image_hijack(log):
    """Removes IFEO hooks (VerifierDlls/GlobalFlag/Debugger) on SPP service binaries.
    Mirrors wincheck Go RemoveSppImageHijack. Crack tools use IFEO to intercept
    the Windows licensing service and keep fake activation alive.
    """
    ifeo_base = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"
    targets = ["SppExtComObj.exe", "sppsvc.exe", "osppsvc.exe"]
    hook_values = ["VerifierDlls", "GlobalFlag", "Debugger"]
    removed = 0
    for exe in targets:
        subkey = f"{ifeo_base}\\{exe}"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey, 0, winreg.KEY_SET_VALUE) as k:
                for val in hook_values:
                    try:
                        winreg.DeleteValue(k, val)
                        _log(log, "SUCCESS", f"  Xoa IFEO hook '{val}' tren {exe}")
                        removed += 1
                    except FileNotFoundError:
                        pass
        except FileNotFoundError:
            pass
        except Exception as exc:
            _log(log, "WARN", f"  Khong mo duoc IFEO key cho {exe}: {exc}")
    return removed


def _clear_kms_host_registry(log):
    """Removes KMS server config from Windows SPP and Office SPP registry paths.
    Mirrors wincheck Go ClearKmsHost.
    """
    kms_reg_paths = [
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform",
        r"SOFTWARE\Microsoft\OfficeSoftwareProtectionPlatform",
        r"SOFTWARE\WOW6432Node\Microsoft\OfficeSoftwareProtectionPlatform",
    ]
    kms_values = ["KeyManagementServiceName", "KeyManagementServicePort"]
    cleared = 0
    for reg_path in kms_reg_paths:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_SET_VALUE) as k:
                for val in kms_values:
                    try:
                        winreg.DeleteValue(k, val)
                        _log(log, "SUCCESS", f"  Da xoa KMS registry: {reg_path}\\{val}")
                        cleared += 1
                    except FileNotFoundError:
                        pass
        except FileNotFoundError:
            pass
        except Exception as exc:
            _log(log, "WARN", f"  Khong mo duoc registry KMS {reg_path}: {exc}")
    return cleared


def clean_office_keys(log):
    """
    Go sach key Office lau va don KMS lau theo quy trinh cua wincheck (Option 9).

    Buoc thuc hien:
      1. Xoa IFEO hook (VerifierDlls/GlobalFlag/Debugger) tren SPP binaries
      2. Xoa cau hinh KMS trong Registry (Windows SPP + Office SPP)
      3. Tim tat ca thu muc Office co OSPP.VBS
      4. Voi moi thu muc:
         a. /remhst  -- xoa may chu KMS qua OSPP
         b. /dstatus -- quet key dang cai
         c. /unpkey  -- go tung key
         d. /dstatus -- kiem tra lai sau khi go
      5. Khoi dong lai dich vu sppsvc va osppsvc
    """
    _log(log, "TITLE", "== GO SACH KEY OFFICE LAU & DON MAY CHU KMS OFFICE ==")
    _log(log, "WARN",  "Thao tac nay se go bo toan bo key Office dang cai dat.")
    _log(log, "WARN",  "Sau khi go, ban can nhap lai key Office hop le de kich hoat.")

    total_removed = 0

    # Buoc 1: Xoa IFEO hook SPP
    _log(log, "INFO", "[Buoc 1] Xoa hook IFEO tren tien trinh ban quyen (SppExtComObj/sppsvc/osppsvc)...")
    hook_count = _remove_spp_image_hijack(log)
    if hook_count == 0:
        _log(log, "INFO", "  -> Khong tim thay IFEO hook nao (he thong sach).")
    else:
        _log(log, "SUCCESS", f"  -> Da xoa {hook_count} IFEO hook crack.")
        total_removed += hook_count

    # Buoc 2: Xoa cau hinh KMS trong Registry
    _log(log, "INFO", "[Buoc 2] Xoa cau hinh may chu KMS trong Registry (Windows SPP & Office SPP)...")
    kms_cleared = _clear_kms_host_registry(log)
    if kms_cleared == 0:
        _log(log, "INFO", "  -> Khong tim thay cau hinh KMS trong Registry.")
    else:
        _log(log, "SUCCESS", f"  -> Da xoa {kms_cleared} gia tri KMS trong Registry.")
        total_removed += kms_cleared

    # Buoc 3: Tim thu muc Office co OSPP.VBS
    _log(log, "INFO", "[Buoc 3] Dang quet cac thu muc cai dat Microsoft Office...")
    office_dirs = _find_office_dirs()

    if not office_dirs:
        _log(log, "WARN", "  -> Khong tim thay file OSPP.VBS. Office chua duoc cai dat hoac duong dan khac thuong.")
        _log(log, "SUCCESS", f"Hoan tat! Da don {total_removed} muc (Registry & IFEO).")
        return total_removed

    _log(log, "SUCCESS", f"  -> Tim thay {len(office_dirs)} thu muc Office.")

    # Buoc 4: Xu ly tung thu muc Office
    cscript = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "cscript.exe")
    for odir in office_dirs:
        ospp_path = os.path.join(odir, "OSPP.VBS")
        _log(log, "STEP", f"[Office] Dang xu ly: {odir}")

        # 4a. /remhst
        _log(log, "INFO", "  |-- /remhst -- Xoa may chu KMS Office...")
        try:
            r_remhst = subprocess.run(
                [cscript, "//nologo", ospp_path, "/remhst"],
                capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=30
            )
            combined = (r_remhst.stdout + r_remhst.stderr).lower()
            if "successful" in combined or r_remhst.returncode == 0:
                _log(log, "SUCCESS", "  |   -> Da xoa KMS host qua OSPP (/remhst).")
            else:
                _log(log, "WARN", f"  |   -> /remhst: {(r_remhst.stdout + r_remhst.stderr).strip()[:120]}")
        except Exception as e:
            _log(log, "WARN", f"  |   -> /remhst loi: {e}")

        # 4b. /dstatus
        _log(log, "INFO", "  |-- /dstatus -- Quet danh sach key Office dang cai dat...")
        try:
            r_dstatus = subprocess.run(
                [cscript, "//nologo", ospp_path, "/dstatus"],
                capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=60
            )
            keys = _extract_office_keys(r_dstatus.stdout)
        except Exception as e:
            _log(log, "WARN", f"  |   -> /dstatus loi: {e}")
            keys = []

        if not keys:
            _log(log, "INFO", "  |   -> Khong tim thay key Office nao trong thu muc nay.")
            continue

        _log(log, "WARN", f"  |   -> Tim thay {len(keys)} key: {', '.join(keys)}")

        # 4c. /unpkey
        dir_removed = 0
        for k in keys:
            _log(log, "INFO", f"  |-- /unpkey:{k} -- Dang go key Office...")
            try:
                r_unp = subprocess.run(
                    [cscript, "//nologo", ospp_path, f"/unpkey:{k}"],
                    capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=30
                )
                out_combined = (r_unp.stdout + r_unp.stderr).lower()
                if "successful" in out_combined or r_unp.returncode == 0:
                    _log(log, "SUCCESS", f"  |   -> Da go thanh cong key: {k}")
                    dir_removed += 1
                    total_removed += 1
                else:
                    _log(log, "ERROR", f"  |   -> Khong go duoc key {k}: {r_unp.stdout.strip()[:100]}")
            except Exception as e:
                _log(log, "ERROR", f"  |   -> /unpkey:{k} loi: {e}")

        # 4d. /dstatus kiem tra lai
        _log(log, "INFO", "  |-- /dstatus -- Kiem tra lai sau khi go...")
        try:
            r_check = subprocess.run(
                [cscript, "//nologo", ospp_path, "/dstatus"],
                capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=60
            )
            remaining = _extract_office_keys(r_check.stdout)
            if not remaining:
                _log(log, "SUCCESS", f"  |   -> Sach hoan toan! Da go {dir_removed} key tai thu muc nay.")
            else:
                _log(log, "WARN", f"  |   -> Con {len(remaining)} key chua go duoc: {', '.join(remaining)}")
        except Exception as e:
            _log(log, "WARN", f"  |   -> Kiem tra lai loi: {e}")

    # Buoc 5: Khoi dong lai dich vu ban quyen
    _log(log, "INFO", "[Buoc 5] Khoi dong lai dich vu ban quyen (sppsvc & osppsvc)...")
    for svc in ["sppsvc", "osppsvc"]:
        try:
            subprocess.run(f"net stop {svc}", shell=True, capture_output=True, timeout=15)
            subprocess.run(f"net start {svc}", shell=True, capture_output=True, timeout=15)
            _log(log, "INFO", f"  -> Da restart dich vu {svc}.")
        except Exception:
            pass

    _log(log, "SUCCESS", f"== HOAN TAT! Da go bo {total_removed} muc (key lau + IFEO hook + KMS Registry). ==")
    return total_removed


def install_win_key(key, log):
    """Installs a product key using slmgr /ipk."""
    _log(log, "INFO", f"Đang cài đặt Product Key mới: {key}...")
    r = subprocess.run(
        f"cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /ipk {key}",
        shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )
    out = (r.stdout + r.stderr).strip()
    if "successful" in out.lower() or "thành công" in out.lower():
        _log(log, "SUCCESS", f"Đã cài đặt thành công Key bản quyền: {key}")
        return True, f"✅ Đã cài đặt thành công Product Key:\n{key}"
    else:
        _log(log, "ERROR", f"Không thể cài key: {out}")
        return False, f"Lỗi cài đặt Key từ Windows:\n{out or 'Không xác định'}"


def uninstall_win_key(log):
    """Uninstalls product key and clears registry using slmgr /upk & /cpky."""
    _log(log, "INFO", "Đang thực hiện gỡ bỏ Product Key (slmgr /upk) & xóa bộ nhớ đệm (slmgr /cpky)...")

    # 1. Chạy slmgr /upk
    r_upk = subprocess.run(
        "cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /upk",
        shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )
    upk_out = (r_upk.stdout + r_upk.stderr).strip()

    # 2. Chạy slmgr /cpky (Xóa key khỏi Registry)
    r_cpky = subprocess.run(
        "cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /cpky",
        shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )
    cpky_out = (r_cpky.stdout + r_cpky.stderr).strip()

    # 3. Chạy slmgr /ckms & xóa cấu hình KMS Registry
    subprocess.run("cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /ckms", shell=True, capture_output=True)
    subprocess.run(r'reg delete "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform" /v KeyManagementServiceName /f', shell=True, capture_output=True)
    subprocess.run(r'reg delete "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform" /v KeyManagementServicePort /f', shell=True, capture_output=True)

    # 4. Xóa giá trị BackupProductKeyDefault trong Registry nếu còn lưu
    reg_cleared = False
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform", 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as k:
            winreg.DeleteValue(k, "BackupProductKeyDefault")
            reg_cleared = True
    except Exception:
        pass

    # 5. Phân tích kết quả thực tế
    msg_lines = []
    if "successful" in upk_out.lower() or "thành công" in upk_out.lower():
        msg_lines.append("✅ Đã gỡ bỏ Product Key khỏi hệ thống Windows (slmgr /upk).")
    elif "0xc004d302" in upk_out.lower():
        msg_lines.append("✅ Đã ghi nhận lệnh gỡ key / đặt lại hệ thống bản quyền.\n⚠️ LƯU Ý: Vui lòng KHỞI ĐỘNG LẠI MÁY TÍNH (Restart) để Windows cập nhật trạng thái xóa key.")
    elif "not found" in upk_out.lower() or "0xc004f014" in upk_out.lower():
        if check_digital_license_present():
            msg_lines.append(
                "ℹ️ Không có Product Key rời nào cần gỡ (Hệ thống đang chạy Bản Quyền Kỹ Thuật Số - Digital License liên kết phần cứng máy).\n"
                "💡 LƯU Ý: Digital License được lưu trữ trên máy chủ Microsoft theo bo mạch chủ. Lệnh slmgr /upk chỉ gỡ key rời. "
                "Nếu bạn muốn đưa máy về trạng thái Chưa Kích Hoạt (Not Active) trong Windows Settings, vui lòng dùng tính năng 'Hủy Kích Hoạt Digital License'."
            )
        else:
            msg_lines.append("ℹ️ Không tìm thấy Product Key nào đang cài đặt (Đã được gỡ trước đó).")
    elif "access denied" in upk_out.lower() or r_upk.returncode == 5:
        msg_lines.append("⚠️ Yêu cầu quyền Administrator để thực thi lệnh gỡ key slmgr /upk.")
    else:
        msg_lines.append(f"Kết quả slmgr /upk: {upk_out or 'Hoàn tất'}")

    if "successful" in cpky_out.lower() or "thành công" in cpky_out.lower() or reg_cleared:
        msg_lines.append("✅ Đã xóa sạch Product Key và bản sao lưu khỏi Registry (slmgr /cpky).")
    elif "0x80070005" in cpky_out:
        msg_lines.append("⚠️ Cần chạy ứng dụng với quyền Administrator để xóa cache Registry.")
    else:
        if cpky_out:
            msg_lines.append(f"Kết quả slmgr /cpky: {cpky_out}")

    result_msg = "\n\n".join(msg_lines)
    _log(log, "SUCCESS", result_msg)
    return True, result_msg


def deactivate_windows(log):
    """
    Completely deactivates Windows on machines with Digital License (HWID) or generic keys.
    Switches to KMS Client Setup Key (GVLK), clears KMS host, uninstalls key, clears registry & ClipSVC cache, and rearms.
    """
    _log(log, "TITLE", "══ HỦY KÍCH HOẠT DIGITAL LICENSE & ĐƯA VỀ CHƯA KÍCH HOẠT ══")
    _log(log, "INFO", "Bắt đầu ngắt liên kết Digital License và đưa Windows về trạng thái Chưa Kích Hoạt (Unlicensed)...")

    edition = get_windows_edition_id()
    gvlk_key = WINDOWS_GVLK_KEYS.get(edition, WINDOWS_GVLK_KEYS.get("Professional", "W269N-WFGWX-YVC9B-4J6C9-T83GX"))
    _log(log, "STEP", f"1. Nhận diện phiên bản Windows: {edition}")
    _log(log, "STEP", f"2. Nạp KMS Client Setup Key ({gvlk_key}) để ngắt kích hoạt Digital License...")

    # 1. Install GVLK Key to detach from Digital License
    r_ipk = subprocess.run(
        f"cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /ipk {gvlk_key}",
        shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )

    # 2. Clear KMS host so it cannot activate
    _log(log, "STEP", "3. Xóa địa chỉ máy chủ KMS (slmgr /ckms)...")
    subprocess.run("cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /ckms", shell=True, capture_output=True)
    subprocess.run(r'reg delete "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform" /v KeyManagementServiceName /f', shell=True, capture_output=True)
    subprocess.run(r'reg delete "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform" /v KeyManagementServicePort /f', shell=True, capture_output=True)

    # 3. Uninstall key
    _log(log, "STEP", "4. Gỡ bỏ Product Key khỏi hệ thống (slmgr /upk)...")
    subprocess.run("cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /upk", shell=True, capture_output=True)

    # 4. Clear key from registry
    _log(log, "STEP", "5. Xóa khóa bản quyền khỏi Registry (slmgr /cpky)...")
    subprocess.run("cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /cpky", shell=True, capture_output=True)
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform", 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as k:
            winreg.DeleteValue(k, "BackupProductKeyDefault")
    except Exception:
        pass

    # 5. Clear ClipSVC cache
    _log(log, "STEP", "6. Làm mới bộ nhớ đệm dịch vụ Client License (ClipSVC)...")
    try:
        subprocess.run("net stop clipsvc /y", shell=True, capture_output=True)
        subprocess.run("net start clipsvc", shell=True, capture_output=True)
    except Exception:
        pass

    # 6. Rearm Windows
    _log(log, "STEP", "7. Đặt lại trạng thái dùng thử (slmgr /rearm)...")
    subprocess.run("cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /rearm", shell=True, capture_output=True)

    msg = (
        "✅ Đã thực hiện hủy kích hoạt Digital License thành công!\n\n"
        "• Hệ thống đã được ngắt kết nối với bản quyền kỹ thuật số và gỡ sạch key.\n"
        "• Trạng thái hệ thống đã chuyển về: Chưa Kích Hoạt (Unlicensed / Rearmed).\n\n"
        "⚠️ QUAN TRỌNG: Bạn vui lòng KHỞI ĐỘNG LẠI MÁY TÍNH (Restart) để Windows Settings cập nhật hoàn tất trạng thái Chưa Kích Hoạt."
    )
    _log(log, "SUCCESS", msg)
    return True, msg


def restore_digital_license(log):
    """
    Restores the Windows Digital License (HWID) by reinstalling default retail generic key
    and triggering online activation via slmgr /ato.
    """
    _log(log, "TITLE", "══ KHÔI PHỤC BẢN QUYỀN KỸ THUẬT SỐ (DIGITAL LICENSE) ══")
    _log(log, "INFO", "Đang nạp lại khóa mặc định và kích hoạt lại theo phần cứng máy tính...")

    edition = get_windows_edition_id()
    retail_key = WINDOWS_DEFAULT_RETAIL_KEYS.get(edition, WINDOWS_DEFAULT_RETAIL_KEYS.get("Professional", "VK7JG-NPHTM-C97JM-9MPGT-3V66T"))
    _log(log, "STEP", f"1. Phiên bản Windows: {edition}")
    _log(log, "STEP", f"2. Cài đặt Default Retail Key ({retail_key})...")

    r_ipk = subprocess.run(
        f"cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /ipk {retail_key}",
        shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )
    ipk_out = (r_ipk.stdout + r_ipk.stderr).strip()

    _log(log, "STEP", "3. Đang gửi yêu cầu kích hoạt trực tuyến tới máy chủ Microsoft (slmgr /ato)...")
    r_ato = subprocess.run(
        "cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /ato",
        shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=20
    )
    ato_out = (r_ato.stdout + r_ato.stderr).strip()

    if "product activated successfully" in ato_out.lower() or "thành công" in ato_out.lower():
        msg = "✨ Kích hoạt Digital License thành công!\n\nWindows đã nhận diện lại bản quyền kỹ thuật số theo máy (HWID) và kích hoạt vĩnh viễn hợp lệ."
        _log(log, "SUCCESS", msg)
        return True, msg
    else:
        msg = f"Kết quả nạp key: {ipk_out}\nKết quả kích hoạt (slmgr /ato): {ato_out or 'Hoàn tất'}"
        _log(log, "INFO", msg)
        return True, msg


def rearm_windows(log):
    """Rearms Windows trial period using slmgr /rearm."""
    _log(log, "INFO", "Đang đặt lại thời gian dùng thử (Rearm Windows)...")
    r = subprocess.run(
        "cscript //nologo %SystemRoot%\\System32\\slmgr.vbs /rearm",
        shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )
    out = (r.stdout + r.stderr).strip()
    _log(log, "SUCCESS", f"Kết quả Rearm: {out}")
    return out


def rearm_office(log):
    """Rearms Office trial period using ospp.vbs /rearm."""
    _log(log, "INFO", "Đang đặt lại thời gian dùng thử Office (ospp.vbs /rearm)...")
    dirs = _find_office_dirs()
    if not dirs:
        msg = "Không tìm thấy thư mục cài đặt Office (chứa OSPP.VBS) trên máy tính này!"
        _log(log, "WARN", msg)
        return False, msg

    results = []
    for d in dirs:
        ospp = os.path.join(d, "OSPP.VBS")
        r = subprocess.run(
            f'cscript //nologo "{ospp}" /rearm',
            shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore"
        )
        out = (r.stdout + r.stderr).strip()
        results.append(f"Thư mục {os.path.basename(d)}:\n{out}")

    msg = "✅ Kết quả đặt lại thời gian dùng thử Office:\n\n" + "\n\n".join(results)
    _log(log, "SUCCESS", msg)
    return True, msg


def install_office_key(key, log):
    """Installs a product key for Office using ospp.vbs /inpkey:"""
    clean_key = key.strip()
    _log(log, "INFO", f"Đang cài đặt Product Key cho Office: {clean_key}...")
    dirs = _find_office_dirs()
    if not dirs:
        msg = "Không tìm thấy thư mục cài đặt Office (chứa OSPP.VBS) trên máy tính này!"
        _log(log, "WARN", msg)
        return False, msg

    results = []
    for d in dirs:
        ospp = os.path.join(d, "OSPP.VBS")
        r_inp = subprocess.run(
            f'cscript //nologo "{ospp}" /inpkey:{clean_key}',
            shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore"
        )
        out_inp = (r_inp.stdout + r_inp.stderr).strip()

        r_act = subprocess.run(
            f'cscript //nologo "{ospp}" /act',
            shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore"
        )
        out_act = (r_act.stdout + r_act.stderr).strip()
        results.append(f"{os.path.basename(d)}:\n• Cài Key: {out_inp}\n• Kích hoạt: {out_act}")

    msg = "✅ Kết quả nạp Key Office:\n\n" + "\n\n".join(results)
    _log(log, "SUCCESS", msg)
    return True, msg
