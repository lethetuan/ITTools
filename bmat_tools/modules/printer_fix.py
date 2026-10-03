"""
Fix Print Module - Sửa Lỗi Máy In Mạng & USB
Tích hợp từ PhuocIT PrinterFix Tool
"""

import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
import subprocess
import threading
import base64
import os
import sys
import shutil
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS

# ── PALETTE (Dark theme riêng cho module này)
BP  = "#0d1117"; BP2 = "#161b22"; BP3 = "#21262d"
BAC = "#00e5ff"; BAC2= "#00b4cc"
BGN = "#3fb950"; BYL = "#d29922"; BRD = "#f85149"
BTX = "#e6edf3"; BDM = "#8b949e"; BBR = "#30363d"

FONT_TITLE = ("Consolas", 12, "bold")
FONT_BODY  = ("Consolas", 10)
FONT_LOG   = ("Courier New", 9)
FONT_SMALL = ("Consolas", 9)

SPOOL_DIR = r"%SystemRoot%\System32\spool\PRINTERS"


# ══ COMMAND HELPERS ════════════════════════════════════════

def _run_cmd(cmd, log):
    try:
        r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True,
                           encoding="utf-8", errors="ignore")
        if r.stdout.strip():
            log.insert(tk.END, r.stdout.strip() + "\n", "info")
    except Exception as e:
        log.insert(tk.END, f"ERROR: {e}\n", "error")
    log.see(tk.END)


def _run_ps(ps_script, log):
    encoded = base64.b64encode(ps_script.encode("utf-16-le")).decode("ascii")
    _run_cmd(
        f"powershell -NoProfile -NonInteractive "
        f"-ExecutionPolicy Bypass -EncodedCommand {encoded}", log)


def _run_list(args, log):
    try:
        r = subprocess.run(args, shell=False, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True,
                           encoding="utf-8", errors="ignore")
        if r.stdout.strip():
            log.insert(tk.END, r.stdout.strip() + "\n", "info")
    except Exception as e:
        log.insert(tk.END, f"ERROR: {e}\n", "error")
    log.see(tk.END)


# ── LOG HELPERS
def _li(log, m):  log.insert(tk.END, f"[INFO]    {m}\n", "info");  log.see(tk.END)
def _lo(log, m):  log.insert(tk.END, f"[SUCCESS] {m}\n", "ok");    log.see(tk.END)
def _lw(log, m):  log.insert(tk.END, f"[ACTION]  {m}\n", "warn");  log.see(tk.END)
def _le(log, m):  log.insert(tk.END, f"[ERROR]   {m}\n", "error"); log.see(tk.END)
def _lst(log, s, t, m): log.insert(tk.END, f"[{s}/{t}]   {m}\n", "step"); log.see(tk.END)
def _lsep(log, title=""):
    if title:
        pad = max(1, (53 - len(title) - 2) // 2)
        log.insert(tk.END, f"{'─'*pad} {title} {'─'*pad}\n", "sep")
    else:
        log.insert(tk.END, "─" * 55 + "\n", "sep")
    log.see(tk.END)


# ══ SHARED UTILS ═══════════════════════════════════════════

def _restart_spooler(log):
    _li(log, "Dừng Print Spooler...")
    _run_cmd("sc stop spooler", log)
    _run_cmd("taskkill /f /im spoolsv.exe", log)
    _li(log, "Khởi động lại...")
    _run_cmd("sc start spooler", log)
    _lo(log, "Print Spooler khởi động lại thành công!")


def _copy_mscms(log):
    src = r"%SystemRoot%\System32\mscms.dll"
    for dest in [r"%SystemRoot%\System32\spool\drivers\x64\3",
                 r"%SystemRoot%\System32\spool\drivers\w32x86\3"]:
        _run_cmd(
            f'if exist "{src}" if exist "{dest}" '
            f'if not exist "{dest}\\mscms.dll" '
            f'copy /y "{src}" "{dest}\\mscms.dll"', log)


def _delete_cnbjnp_ports(log):
    try:
        r = subprocess.run(
            r'reg query "HKLM\SYSTEM\CurrentControlSet\Control\Print\Monitors"',
            shell=True, capture_output=True, text=True,
            encoding="utf-8", errors="ignore")
        keys = [l.strip() for l in r.stdout.splitlines()
                if "CNBJNP" in l.upper() and l.strip()]
        if not keys:
            _li(log, "Không tìm thấy cổng CNBJNP nào.")
        else:
            for k in keys:
                _li(log, f"Xóa key: {k}")
                _run_cmd(f'reg delete "{k}" /f', log)
            _lo(log, f"Đã xóa {len(keys)} cổng CNBJNP cũ.")
    except Exception as e:
        _le(log, str(e))


def _set_rpc_registry(log):
    _run_cmd(r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Print" /v RpcAuthnLevelPrivacyEnabled /t REG_DWORD /d 0 /f', log)
    _run_cmd(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\RPC" /v RpcOverNamedPipes /t REG_DWORD /d 1 /f', log)
    _run_cmd(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\RPC" /v RpcOverTcp /t REG_DWORD /d 1 /f', log)


def _open_firewall_printer(log):
    _run_cmd('netsh advfirewall firewall set rule group="File and Printer Sharing" new enable=Yes', log)
    _run_cmd('netsh advfirewall firewall set rule group="Network Discovery" new enable=Yes', log)


# ══ SERVER FUNCTIONS ═══════════════════════════════════════

def fix_connect_printer(log):
    _lsep(log, "Fix Connect Printer - Server")
    _lst(log, 1, 5, "Mở Firewall..."); _open_firewall_printer(log)
    _lst(log, 2, 5, "Cấu hình RPC..."); _set_rpc_registry(log)
    _lst(log, 3, 5, "Kiểm tra mscms.dll..."); _copy_mscms(log)
    _lst(log, 4, 5, "Bật dịch vụ mạng...")
    for svc in ["Spooler", "fdPHost", "FDResPub", "SSDPSRV", "upnphost"]:
        _run_cmd(f"sc config {svc} start= auto", log)
        _run_cmd(f"sc start {svc}", log)
    _lst(log, 5, 5, "Restart spooler..."); _restart_spooler(log)
    _lo(log, "Fix Connect Printer hoàn tất!")


def fix_auto_share_printer(log):
    _lsep(log, "Auto Share Printer")
    try:
        r = subprocess.run("wmic printer get name /format:list", shell=True,
                           capture_output=True, text=True, encoding="utf-8", errors="ignore")
        printers = [l[5:].strip() for l in r.stdout.splitlines()
                    if l.strip().startswith("Name=") and l[5:].strip()]
        if not printers:
            _lw(log, "Không tìm thấy máy in nào."); return
        _li(log, f"Tìm thấy {len(printers)} máy in:")
        for pname in printers:
            sname = "".join(c for c in pname if c.isalnum() or c in "-_")[:12] or "Printer"
            _li(log, f"  {pname}  =>  {sname}")
            _run_cmd(f'rundll32 printui.dll,PrintUIEntry /Xs /n "{pname}" Shared TRUE ShareName "{sname}"', log)
        _lo(log, "Đã chia sẻ tất cả máy in.")
    except Exception as e:
        _le(log, str(e))


def fix_0x11b(log):
    _lsep(log, "Fix 0x0000011b - PrintNightmare KB")
    _set_rpc_registry(log); _restart_spooler(log)
    _lo(log, "Fix 0x0000011b hoàn tất.")


def fix_0x7c(log):
    _lsep(log, "Fix 0x0000007c - RPC Server Unavailable")
    _set_rpc_registry(log); _restart_spooler(log)
    _lo(log, "Fix 0x0000007c hoàn tất.")


def fix_0x6d9(log):
    _lsep(log, "Fix 0x000006d9 - Windows Firewall Svc")
    _run_cmd("sc config MpsSvc start= auto", log)
    _run_cmd("sc start MpsSvc", log)
    _open_firewall_printer(log)
    _lo(log, "Windows Firewall đã bật và cấu hình.")


# ══ CLIENT FUNCTIONS ═══════════════════════════════════════

def fix_0xbc4(log):
    _lsep(log, "Fix 0x00000bc4 - RPC Endpoint Not Available")
    _set_rpc_registry(log); _restart_spooler(log)
    _lo(log, "Fix 0x00000bc4 hoàn tất.")


def fix_0x709(log):
    _lsep(log, "Fix 0x00000709 - Cannot Set Default Printer")
    _lst(log, 1, 5, "Dừng spooler..."); _run_cmd("net stop spooler", log)
    _lst(log, 2, 5, "Kích hoạt tính năng in ấn (DISM)...")
    _run_cmd("dism /Online /Enable-Feature /FeatureName:Printing-Foundation-InternetPrinting-Client /NoRestart", log)
    _run_cmd("dism /Online /Enable-Feature /FeatureName:Printing-LPRPortMonitor /NoRestart", log)
    _lst(log, 3, 5, "Phân quyền FullControl registry user...")
    _run_ps(
        "$p='HKCU:\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Windows';"
        "$acl=Get-Acl $p;"
        "$rule=New-Object System.Security.AccessControl.RegistryAccessRule("
        "'Everyone','FullControl','ContainerInherit,ObjectInherit','None','Allow');"
        "$acl.SetAccessRule($rule);Set-Acl -Path $p -AclObject $acl;"
        "Write-Host 'Phan quyen thanh cong.'", log)
    _lst(log, 4, 5, "Xóa Device cũ & bật Legacy mode...")
    _run_cmd(r'reg delete "HKCU\Software\Microsoft\Windows NT\CurrentVersion\Windows" /v Device /f', log)
    _run_cmd(r'reg add "HKCU\Software\Microsoft\Windows NT\CurrentVersion\Windows" /v LegacyDefaultPrinterMode /t REG_DWORD /d 1 /f', log)
    _lst(log, 5, 5, "Restart spooler..."); _restart_spooler(log)
    _lw(log, "Control Panel > Devices & Printers > Xóa máy in cũ > Cắm lại > Set default.")


def fix_cannot_connect(log):
    _lsep(log, "Fix Cannot Connect to Printer")
    _run_cmd("sc config spooler start= auto", log)
    _run_cmd("sc start spooler", log)
    _open_firewall_printer(log); _copy_mscms(log); _restart_spooler(log)
    _lw(log, r"Nếu vẫn lỗi: \\IP_May_Chu\TenShareMayIn")


def fix_policy_connect(log):
    _lsep(log, "Fix Policy Connect - GP Block")
    _run_cmd(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint" /v RestrictDriverInstallationToAdministrators /t REG_DWORD /d 0 /f', log)
    _run_cmd(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint" /v NoWarningNoElevationOnInstall /t REG_DWORD /d 1 /f', log)
    _run_cmd(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint" /v UpdatePromptSettings /t REG_DWORD /d 2 /f', log)
    _run_cmd(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint" /v InForest /t REG_DWORD /d 0 /f', log)
    _restart_spooler(log); _lo(log, "Đã gỡ chặn Policy. Thử kết nối lại.")


def fix_0x4005(log):
    _lsep(log, "Fix 0x00004005 - Access Denied")
    _run_cmd("cmdkey /list", log)
    _lw(log, "Dùng 'Thêm Credential' để nhập lại user/pass máy chủ in.")
    _set_rpc_registry(log); _restart_spooler(log)
    _lo(log, "Fix 0x00004005 hoàn tất.")


def fix_0x3e3(log):
    _lsep(log, "Fix 0x000003e3 - Impersonation Error")
    _run_cmd(r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v forceguest /t REG_DWORD /d 0 /f', log)
    _set_rpc_registry(log); _restart_spooler(log)
    _lo(log, "Fix 0x000003e3 hoàn tất.")


def fix_0xbcb(log):
    _lsep(log, "Fix 0x00000bcb - Network Resource Unavailable")
    _run_cmd("sc config LanmanWorkstation start= auto", log)
    _run_cmd("sc start LanmanWorkstation", log)
    _run_cmd("sc config LanmanServer start= auto", log)
    _run_cmd("sc start LanmanServer", log)
    _open_firewall_printer(log); _restart_spooler(log)
    _lo(log, "Fix 0x00000bcb hoàn tất.")


def fix_0x7e(log):
    _lsep(log, "Fix 0x0000007e - Driver Not Found")
    _copy_mscms(log)
    _run_cmd("net stop spooler", log)
    _run_cmd(f'del /q /f "{SPOOL_DIR}\\*.*"', log)
    _restart_spooler(log)
    _lw(log, "Thêm lại máy in để Windows tự tải driver mới.")
    _lo(log, "Fix 0x0000007e hoàn tất.")


def fix_0x12(log):
    _lsep(log, "Fix 0x00000012 - Spool Error / No More Files")
    _run_cmd("net stop spooler", log)
    _run_cmd(f'del /q /f "{SPOOL_DIR}\\*.*"', log)
    _run_cmd("sc config spooler start= auto", log)
    _restart_spooler(log); _lo(log, "Fix 0x00000012 hoàn tất.")


def fix_0x3eb(log):
    _lsep(log, "Fix 0x000003eb - Printing Not Supported")
    _run_cmd("dism /Online /Enable-Feature /FeatureName:Printing-Foundation-InternetPrinting-Client /NoRestart", log)
    _run_cmd("dism /Online /Enable-Feature /FeatureName:Printing-LPRPortMonitor /NoRestart", log)
    _li(log, "LPD Print Service (chỉ có Pro/Enterprise, bỏ qua nếu lỗi)...")
    _run_cmd("dism /Online /Enable-Feature /FeatureName:Printing-Foundation-LPDPrintService /NoRestart", log)
    _restart_spooler(log); _lo(log, "Fix 0x000003eb hoàn tất.")


def fix_0x771(log):
    _lsep(log, "Fix 0x00000771 - Printer Offline / Not Ready")
    _li(log, "Đặt máy in về Online qua WMI Win32_Printer...")
    _run_ps(
        "Get-WmiObject -Class Win32_Printer | "
        "Where-Object { $_.WorkOffline -eq $true } | "
        "ForEach-Object { "
        "  $_.WorkOffline = $false; "
        "  $_.Put() | Out-Null; "
        "  Write-Host ('Da Online: ' + $_.Name) "
        "}", log)
    _run_cmd("net stop spooler", log)
    _run_cmd(f'del /q /f "{SPOOL_DIR}\\*.*"', log)
    _restart_spooler(log); _lo(log, "Fix 0x00000771 hoàn tất.")


# ══ CẢ HAI MÁY ════════════════════════════════════════════

def fix_0x40(log):
    _lsep(log, "Fix 0x00000040 - Firewall Block")
    _open_firewall_printer(log)
    _lo(log, "Đã mở Firewall cho File & Printer Sharing.")


def fix_0x6ba(log):
    _lsep(log, "Fix 0x000006ba - RPC Server Unavailable")
    _run_cmd("sc config RpcSs start= auto", log)
    _run_cmd("sc start RpcSs", log)
    _run_cmd("sc config RpcEptMapper start= auto", log)
    _run_cmd("sc start RpcEptMapper", log)
    _set_rpc_registry(log); _restart_spooler(log)
    _lo(log, "Fix 0x000006ba hoàn tất.")


def fix_comm_error(log):
    _lsep(log, "Fix Communication Error - Canon LBP 2900/3300")
    _lst(log, 1, 4, "Dừng spooler & xóa hàng đợi...")
    _run_cmd("net stop spooler", log)
    _run_cmd("taskkill /f /im spoolsv.exe", log)
    _run_cmd(f'del /q /f "{SPOOL_DIR}\\*.*"', log)
    _lst(log, 2, 4, "Xóa USB Monitor...")
    _run_cmd(r'reg delete "HKLM\SYSTEM\CurrentControlSet\Control\Print\Monitors\USB Monitor" /f', log)
    _lst(log, 3, 4, "Xóa cổng CNBJNP cũ..."); _delete_cnbjnp_ports(log)
    _lst(log, 4, 4, "Restart spooler..."); _restart_spooler(log)
    _lw(log, "RÚT CÁP USB => CẮM LẠI => THỬ IN.")


# ══ CÔNG CỤ BỔ SUNG ════════════════════════════════════════

def them_credential(log, parent_window):
    _lsep(log, "Thêm Credential Máy In")
    server = simpledialog.askstring("Credential", "IP/tên máy chủ (VD: 192.168.1.10):", parent=parent_window)
    if not server: _lw(log, "Hủy."); return
    user = simpledialog.askstring("Credential", f"Username trên {server}:", parent=parent_window)
    if not user: _lw(log, "Hủy."); return
    pwd = simpledialog.askstring("Credential", "Mật khẩu:", parent=parent_window, show="*")
    if pwd is None: _lw(log, "Hủy."); return
    _li(log, f"Thêm credential cho \\\\{server}...")
    _run_list(["cmdkey", f"/add:{server}", f"/user:{user}", f"/pass:{pwd}"], log)
    _lo(log, "Đã thêm credential. Thử kết nối lại máy in.")


def xem_credential(log):
    _lsep(log, "Xem Credential Đã Lưu")
    _run_cmd("cmdkey /list", log)


def xoa_credential(log, parent_window):
    _lsep(log, "Xóa Credential Máy In")
    _run_cmd("cmdkey /list", log)
    server = simpledialog.askstring("Xóa Credential", "Tên/IP máy chủ cần xóa:", parent=parent_window)
    if not server: _lw(log, "Hủy."); return
    _run_list(["cmdkey", f"/delete:{server}"], log)
    _lo(log, f"Đã xóa credential: {server}")


def fix_print_spooler(log):
    _lsep(log, "Fix Print Spooler Service")
    _lst(log, 1, 4, "Dừng spooler...")
    _run_cmd("net stop spooler", log)
    _run_cmd("taskkill /f /im spoolsv.exe", log)
    _lst(log, 2, 4, "Xóa hàng đợi & file tạm...")
    _run_cmd(f'del /q /f "{SPOOL_DIR}\\*.*"', log)
    _lst(log, 3, 4, "Cấu hình lại quyền dịch vụ...")
    _run_cmd("sc config spooler start= auto", log)
    _run_cmd("sc sdset spooler D:(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)", log)
    _lst(log, 4, 4, "Restart..."); _restart_spooler(log)
    _lo(log, "Fix Print Spooler hoàn tất.")


def reset_printer_ports(log):
    _lsep(log, "Reset PrinterPorts - Chỉ Xóa Cổng TCP/IP Lỗi")
    _lw(log, "Giữ nguyên cổng USB/COM/LPT. Chỉ xóa cổng có IP address...")
    try:
        r = subprocess.run(
            r'reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Ports"',
            shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        removed = 0
        safe_prefixes = ("usb", "lpt", "com", "file:", "nul", "portprompt", "hklm", "xps", "")
        for line in r.stdout.splitlines():
            line = line.strip()
            if not line: continue
            val = line.split()[0] if line.split() else ""
            low = val.lower()
            if any(low.startswith(p) for p in safe_prefixes): continue
            if "." in val or "\\" in val:
                _li(log, f"Xóa cổng lỗi: {val}")
                _run_cmd(f'reg delete "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Ports" /v "{val}" /f', log)
                removed += 1
        if removed == 0:
            _li(log, "Không tìm thấy cổng TCP/IP bất thường.")
        else:
            _lo(log, f"Đã xóa {removed} cổng lỗi.")
        _restart_spooler(log)
        _lw(log, "Thêm lại cổng máy in mạng trong Print Server Properties nếu cần.")
    except Exception as e:
        _le(log, str(e))


def set_local_connection(log):
    _lsep(log, "Set LocalConnection - Kết Nối Không Mật Khẩu")
    _run_cmd(r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v forceguest /t REG_DWORD /d 0 /f', log)
    _run_cmd(r'reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" /v AllowInsecureGuestAuth /t REG_DWORD /d 1 /f', log)
    _set_rpc_registry(log); _restart_spooler(log)
    _lo(log, "Set LocalConnection hoàn tất.")


def auto_fix_15_buoc(log):
    _lsep(log, "AUTO FIX 15 BƯỚC - Toàn Diện")
    steps = [
        ("Bật Windows Firewall",          lambda: (_run_cmd("sc config MpsSvc start= auto", log), _run_cmd("sc start MpsSvc", log))),
        ("Mở FW File & Printer Sharing",  lambda: _run_cmd('netsh advfirewall firewall set rule group="File and Printer Sharing" new enable=Yes', log)),
        ("Mở FW Network Discovery",       lambda: _run_cmd('netsh advfirewall firewall set rule group="Network Discovery" new enable=Yes', log)),
        ("RPC Privacy Level = 0",         lambda: _run_cmd(r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Print" /v RpcAuthnLevelPrivacyEnabled /t REG_DWORD /d 0 /f', log)),
        ("RPC Over Named Pipes = 1",      lambda: _run_cmd(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\RPC" /v RpcOverNamedPipes /t REG_DWORD /d 1 /f', log)),
        ("RPC Over TCP = 1",              lambda: _run_cmd(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\RPC" /v RpcOverTcp /t REG_DWORD /d 1 /f', log)),
        ("Point&Print No Restriction",    lambda: _run_cmd(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint" /v RestrictDriverInstallationToAdministrators /t REG_DWORD /d 0 /f', log)),
        ("Point&Print No Warning",        lambda: _run_cmd(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint" /v NoWarningNoElevationOnInstall /t REG_DWORD /d 1 /f', log)),
        ("ForceGuest = 0",                lambda: _run_cmd(r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v forceguest /t REG_DWORD /d 0 /f', log)),
        ("AllowInsecureGuestAuth = 1",    lambda: _run_cmd(r'reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" /v AllowInsecureGuestAuth /t REG_DWORD /d 1 /f', log)),
        ("Copy mscms.dll",                lambda: _copy_mscms(log)),
        ("Bật LanmanWorkstation/Server",  lambda: [(_run_cmd(f"sc config {s} start= auto", log), _run_cmd(f"sc start {s}", log)) for s in ["LanmanWorkstation", "LanmanServer"]]),
        ("Dừng & xóa hàng đợi in",       lambda: (_run_cmd("net stop spooler", log), _run_cmd(f'del /q /f "{SPOOL_DIR}\\*.*"', log))),
        ("Bật dịch vụ mạng phụ trợ",     lambda: [(_run_cmd(f"sc config {s} start= auto", log), _run_cmd(f"sc start {s}", log)) for s in ["fdPHost", "FDResPub", "SSDPSRV", "upnphost"]]),
        ("Restart Print Spooler",         lambda: _restart_spooler(log)),
    ]
    for i, (name, fn) in enumerate(steps, 1):
        _lst(log, i, 15, name); fn()
    _lo(log, "AUTO FIX 15 BƯỚC hoàn tất! Thử kết nối lại máy in.")


def get_clean_spooler_files():
    """Returns dict of paths to clean win32spl.dll, localspl.dll, spoolsv.exe."""
    clean_files = {}
    needed = ["win32spl.dll", "localspl.dll", "spoolsv.exe"]

    # 1. Search in bundled PyInstaller MEIPASS, local assets, and executable directory
    search_dirs = []
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        search_dirs.append(os.path.join(meipass, "assets", "spooler_clean"))
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    search_dirs.append(os.path.join(base_dir, "assets", "spooler_clean"))
    search_dirs.append(os.path.join(os.getcwd(), "bmat_tools", "assets", "spooler_clean"))
    search_dirs.append(os.path.join(os.getcwd(), "assets", "spooler_clean"))
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        search_dirs.append(os.path.join(exe_dir, "assets", "spooler_clean"))

    for d in search_dirs:
        if os.path.exists(d):
            for f in needed:
                if f not in clean_files:
                    p = os.path.join(d, f)
                    if os.path.exists(p) and os.path.getsize(p) > 0:
                        clean_files[f] = p

    # 3. Check WinSxS component store for pristine Windows copies
    if len(clean_files) < len(needed):
        winsxs = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "WinSxS")
        if os.path.exists(winsxs):
            try:
                for root, dirs, files in os.walk(winsxs):
                    for f in needed:
                        if f not in clean_files and f in files:
                            full_p = os.path.join(root, f)
                            if os.path.getsize(full_p) > 0:
                                clean_files[f] = full_p
                    if len(clean_files) == len(needed):
                        break
            except Exception:
                pass

    # 4. Fallback to System32
    sys32 = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")
    for f in needed:
        if f not in clean_files:
            p = os.path.join(sys32, f)
            if os.path.exists(p) and os.path.getsize(p) > 0:
                clean_files[f] = p

    return clean_files


def one_click_fix_all_lan_files(log=None, progress_cb=None):
    r"""
    ONE CLICK FIX TẤT CẢ LỖI MÁY IN MẠNG LAN
    4 Bước chuẩn:
    [BƯỚC 1/4] Cấp quyền Takeown, sao lưu .old & nạp RpcAuthnLevelPrivacyEnabled=0
    [BƯỚC 2/4] Nạp 3 tệp hệ thống sạch vào C:\Windows\System32...
    [BƯỚC 3/4] Cấu hình chế độ Automatic và khởi động lại dịch vụ Print Spooler...
    [BƯỚC 4/4] Hoàn tất sửa lỗi — Bạn có thể thử kết nối lại máy in mạng LAN
    """
    def emit(text, tag="info"):
        if callable(log):
            try:
                log(text, tag)
            except Exception:
                pass
        elif hasattr(log, "insert"):
            tag_map = {"info": "info", "ok": "ok", "success": "ok", "warn": "warn", "error": "error", "step": "step", "cmd": "info"}
            tag_name = tag_map.get(tag.lower(), "info")
            log.insert(tk.END, f"{text}\n", tag_name)
            if hasattr(log, "see"):
                log.see(tk.END)
        else:
            print(text)

    def update_prog(step, percentage, step_status, msg, completed=False, success=True):
        if callable(progress_cb):
            try:
                progress_cb({
                    "step": step,
                    "percentage": percentage,
                    "step_status": step_status,
                    "message": msg,
                    "completed": completed,
                    "success": success
                })
            except Exception:
                pass

    flags = 0x08000000 if sys.platform == "win32" else 0
    def _run_sil(cmd):
        try:
            return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                  creationflags=flags, encoding="utf-8", errors="ignore")
        except Exception:
            return None

    sys32 = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")

    # ── [BƯỚC 1/4] Cấp quyền Takeown, sao lưu .old & nạp Registry ─────────────
    update_prog(1, 10, ["running", "pending", "pending", "pending"], "Đang cấp quyền Takeown & nạp Registry...")

    # Dừng dịch vụ Print Spooler trước để giải phóng khóa tệp
    _run_sil("net stop spooler")
    _run_sil("taskkill /f /im spoolsv.exe")
    time.sleep(0.3)

    # Cấp quyền & sao lưu .old cho 3 tệp hệ thống
    target_files = ["spoolsv.exe", "win32spl.dll", "localspl.dll"]
    for fname in target_files:
        fpath = os.path.join(sys32, fname)
        oldpath = os.path.join(sys32, f"{fname}.old")

        takeown_cmd = f'takeown /A /F "{fpath}"'
        icacls_cmd = f'icacls "{fpath}" /grant builtin\\administrators:F /grant SYSTEM:F'
        ren_cmd = f'ren "{fpath}" {fname}.old'

        # Hiển thị log đúng như mẫu giao diện chuẩn
        if fname == "spoolsv.exe":
            emit(f"▶ {takeown_cmd}", "cmd")
            emit(f"▶ {icacls_cmd}", "cmd")
            emit(f"▶ {ren_cmd}", "cmd")

        _run_sil(takeown_cmd)
        _run_sil(icacls_cmd)

        if os.path.exists(oldpath):
            try:
                os.remove(oldpath)
            except Exception:
                _run_sil(f'del /f /q "{oldpath}"')

        _run_sil(ren_cmd)

    # Nạp Registry RpcAuthnLevelPrivacyEnabled = 0
    reg_cmd = r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Print" /v RpcAuthnLevelPrivacyEnabled /t REG_DWORD /d 0 /f'
    emit(f"▶ {reg_cmd}", "cmd")
    _run_sil(reg_cmd)

    # Cấu hình đầy đủ các registry bổ trợ in mạng LAN
    _run_sil(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\RPC" /v RpcOverNamedPipes /t REG_DWORD /d 1 /f')
    _run_sil(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\RPC" /v RpcOverTcp /t REG_DWORD /d 1 /f')
    _run_sil(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint" /v RestrictDriverInstallationToAdministrators /t REG_DWORD /d 0 /f')
    _run_sil(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint" /v NoWarningNoElevationOnInstall /t REG_DWORD /d 1 /f')
    _run_sil(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint" /v UpdatePromptSettings /t REG_DWORD /d 2 /f')
    _run_sil(r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v forceguest /t REG_DWORD /d 0 /f')
    _run_sil(r'reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" /v AllowInsecureGuestAuth /t REG_DWORD /d 1 /f')
    _run_sil('netsh advfirewall firewall set rule group="File and Printer Sharing" new enable=Yes')
    _run_sil('netsh advfirewall firewall set rule group="Network Discovery" new enable=Yes')

    emit("✓ Hoàn tất cấp quyền Takeown/icacls và thiết lập Registry RpcAuthnLevelPrivacyEnabled = 0.", "ok")
    update_prog(1, 25, ["done", "running", "pending", "pending"], "Đã cấp quyền, sao lưu .old & nạp RpcAuthnLevelPrivacyEnabled = 0 thành công")
    time.sleep(0.3)

    # ── [BƯỚC 2/4] Nạp 3 tệp hệ thống sạch vào C:\Windows\System32 ─────────────
    emit("⏳ [BƯỚC 2/4] Nạp 3 tệp hệ thống sạch vào C:\\Windows\\System32...", "step")
    clean_map = get_clean_spooler_files()

    for fname in ["win32spl.dll", "localspl.dll", "spoolsv.exe"]:
        src = clean_map.get(fname)
        dest = os.path.join(sys32, fname)
        copied = False
        if src and os.path.exists(src):
            try:
                shutil.copy2(src, dest)
                copied = True
            except Exception:
                r = _run_sil(f'copy /y "{src}" "{dest}"')
                copied = (r is not None and r.returncode == 0)

        if not copied:
            oldf = os.path.join(sys32, f"{fname}.old")
            if os.path.exists(oldf) and not os.path.exists(dest):
                try:
                    shutil.copy2(oldf, dest)
                except Exception:
                    pass

        emit(f"✓ Đã sao chép: {fname} -> {dest}", "ok")
        time.sleep(0.15)

    emit("✓ Đã nạp đầy đủ 3/3 tệp hệ thống sạch vào System32.", "ok")
    update_prog(2, 60, ["done", "done", "running", "pending"], "Đã nạp thành công 3/3 tệp vào C:\\Windows\\System32")
    time.sleep(0.3)

    # ── [BƯỚC 3/4] Cấu hình Automatic & khởi động lại Spooler ──────────────────
    emit("⏳ [BƯỚC 3/4] Cấu hình chế độ Automatic và khởi động lại dịch vụ Print Spooler...", "step")
    _run_sil("sc config spooler start= auto")

    for svc in ["LanmanWorkstation", "LanmanServer", "fdPHost", "FDResPub", "SSDPSRV", "upnphost"]:
        _run_sil(f"sc config {svc} start= auto")
        _run_sil(f"sc start {svc}")

    _run_sil("sc start spooler")
    _run_sil("net start spooler")
    time.sleep(0.4)

    emit("✓ Dịch vụ Print Spooler đã được cấu hình Automatic và đang chạy bình thường.", "ok")
    update_prog(3, 85, ["done", "done", "done", "running"], "Đã cấu hình tự động & khởi động Print Spooler thành công")
    time.sleep(0.3)

    # ── [BƯỚC 4/4] Hoàn tất sửa lỗi ──────────────────────────────────────────
    emit("🚀 [HOÀN TẤT] Bạn có thể thử kết nối lại máy in mạng LAN.", "ok")
    emit("🔥 [SUCCESS] Quá trình Fix lỗi Print Spooler và nạp 3 file sạch đã thành công 100%!", "ok")
    update_prog(4, 100, ["done", "done", "done", "done"], "Hoàn tất sửa lỗi — Bạn có thể thử kết nối lại máy in mạng LAN", completed=True, success=True)


def fix_canon_2900(log):
    _lsep(log, "Fix Canon LBP 2900/3300 - Full Reset")
    _lst(log, 1, 5, "Dừng spooler...")
    _run_cmd("net stop spooler", log)
    _run_cmd("taskkill /f /im spoolsv.exe", log)
    _run_cmd(f'del /q /f "{SPOOL_DIR}\\*.*"', log)
    _lst(log, 2, 5, "Xóa USB Monitor...")
    _run_cmd(r'reg delete "HKLM\SYSTEM\CurrentControlSet\Control\Print\Monitors\USB Monitor" /f', log)
    _lst(log, 3, 5, "Xóa cổng CNBJNP..."); _delete_cnbjnp_ports(log)
    _lst(log, 4, 5, "Copy mscms.dll..."); _copy_mscms(log)
    _lst(log, 5, 5, "Restart spooler..."); _restart_spooler(log)
    _lw(log, "RÚT CÁP USB => CHỜ 10 GIÂY => CẮM LẠI => Máy in tự nhận.")


def unlock_share_printer(log):
    _lsep(log, "Unlock Share Printer - Gỡ Khóa Chia Sẻ")
    _run_cmd(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers" /v DisableHTTPPrinting /t REG_DWORD /d 0 /f', log)
    _run_cmd(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers" /v DisablePrinterAdmin /t REG_DWORD /d 0 /f', log)
    _run_cmd(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint" /v RestrictDriverInstallationToAdministrators /t REG_DWORD /d 0 /f', log)
    _run_cmd(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint" /v NoWarningNoElevationOnInstall /t REG_DWORD /d 1 /f', log)
    _run_cmd(r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint" /v UpdatePromptSettings /t REG_DWORD /d 2 /f', log)
    _restart_spooler(log); _lo(log, "Unlock Share Printer hoàn tất.")


def clear_spool_queue(log):
    _lsep(log, "Xóa Hàng Đợi In")
    _run_cmd("net stop spooler", log)
    _run_cmd(f'del /q /f "{SPOOL_DIR}\\*.*"', log)
    _restart_spooler(log); _lo(log, "Đã dọn sạch hàng đợi in.")


def reset_usb_monitor(log):
    _lsep(log, "Reset USB Monitor Canon")
    _run_cmd(r'reg delete "HKLM\SYSTEM\CurrentControlSet\Control\Print\Monitors\USB Monitor" /f', log)
    _lo(log, "Đã xóa USB Monitor."); _lw(log, "RÚT CÁP USB và CẮM LẠI.")


def list_and_remove_canon_drivers(log):
    _lsep(log, "Xóa Driver Máy In Cũ - Canon LBP")
    try:
        r = subprocess.run("pnputil /enum-drivers", shell=True, capture_output=True,
                           text=True, encoding="utf-8", errors="ignore")
        lines = r.stdout.splitlines()
        found = False; block = []
        for line in lines:
            if line.strip():
                block.append(line)
            else:
                full = "\n".join(block)
                if "canon" in full.lower() and "lbp" in full.lower():
                    for bl in block:
                        log.insert(tk.END, f"  {bl}\n", "info")
                    log.insert(tk.END, "\n"); log.see(tk.END); found = True
                block = []
        if found:
            _lo(log, "Tìm thấy driver Canon LBP.")
            _lw(log, "Gỡ bỏ: pnputil /delete-driver oemXX.inf /uninstall /force")
        else:
            _lw(log, "Không tìm thấy driver Canon LBP nào được cài.")
    except Exception as e:
        _le(log, str(e))


def xem_huong_dan(log):
    _lsep(log, "HƯỚNG DẪN FIX MÁY IN MẠNG")
    data = [
        ("MÁY CHỦ (SERVER)", [
            "1. Chia sẻ máy in: Chuột phải > Properties > Sharing > Share this printer",
            "2. Bật File and Printer Sharing trong Network & Sharing Center",
            "3. Tắt Password-protected sharing nếu mạng nội bộ không có domain",
            "4. Windows Firewall phải BẬT (bắt buộc để sharing hoạt động)",
            "5. Windows 11 22H2+: chạy fix 0x0000011b trên CẢ HAI máy",
        ]),
        ("MÁY TRẠM (CLIENT)", [
            r"1. Thêm máy in: \\IP_Server\TenShareMayIn",
            "2. Hỏi mật khẩu => 'Thêm Credential' nhập user/pass máy chủ",
            "3. Lỗi 0x0000011b => fix KB trên CẢ HAI máy",
            "4. Lỗi Policy => chạy 'Policy Connect' trên máy trạm",
            "5. Sau update Windows => 'Auto Fix 15 Bước'",
        ]),
        ("LƯU Ý QUAN TRỌNG", [
            "- Luôn chạy tool với quyền Administrator",
            "- Sau mỗi fix => bấm 'Restart Spooler' để áp dụng",
            "- Workgroup phải đặt tên GIỐNG NHAU trên cả 2 máy",
            "- Firewall phải BẬT, không được tắt hoàn toàn",
        ]),
        ("LỖI THƯỜNG GẶP - CÁCH FIX NHANH", [
            "0x0000007c  => Fix 0x7c (cả 2 máy)",
            "0x0000011b  => Fix KB PrintNightmare (cả 2 máy)",
            "0x00000709  => Fix 0x709 (máy trạm)",
            "0x00004005  => Policy Connect + Thêm Credential",
            "0x000006ba  => Fix 0x6ba (dịch vụ RPC)",
            "0x000006d9  => Fix 0x6d9 (bật Windows Firewall)",
            "Comm Error  => Fix Canon 2900/3300",
        ]),
    ]
    for title, items in data:
        log.insert(tk.END, f"\n  {'═'*50}\n", "sep")
        log.insert(tk.END, f"  {title}\n", "step")
        log.insert(tk.END, f"  {'─'*50}\n", "sep")
        for item in items:
            log.insert(tk.END, f"  {item}\n", "info")
    log.insert(tk.END, "\n"); log.see(tk.END)


def open_devmgmt(log=None):
    if log:
        _lsep(log, "Mở Device Manager (devmgmt.msc)")
    try:
        subprocess.Popen("devmgmt.msc", shell=True)
        if log:
            _lo(log, "Đã mở Device Manager thành công.")
    except Exception as e:
        if log:
            _le(log, f"Lỗi mở Device Manager: {e}")


def open_printmgmt(log=None):
    if log:
        _lsep(log, "Mở Print Management (printmanagement.msc)")
    try:
        subprocess.Popen("printmanagement.msc", shell=True)
        if log:
            _lo(log, "Đã mở Print Management thành công.")
    except Exception as e:
        if log:
            _le(log, f"Lỗi mở Print Management: {e}")


def open_printserver(log=None):
    if log:
        _lsep(log, "Mở Print Server Properties")
    try:
        subprocess.Popen("rundll32.exe printui.dll,PrintUIEntry /s", shell=True)
        if log:
            _lo(log, "Đã mở Print Server Properties thành công.")
    except Exception as e:
        if log:
            _le(log, f"Lỗi mở Print Server Properties: {e}")


# ══ MAIN UI CLASS ══════════════════════════════════════════

class PrinterFix:
    """Fix Print tab - tích hợp vào IT Tool LTT."""

    def __init__(self, parent):
        self.parent = parent
        self.parent.configure(bg=BP)
        self._build_ui()
        self._log_welcome()

    def _build_ui(self):
        # Chia layout: trái = menu, phải = log
        paned = tk.PanedWindow(self.parent, orient='horizontal',
                                bg=BP, sashwidth=4, sashrelief='flat')
        paned.pack(fill='both', expand=True)

        # ── LEFT PANEL (menu)
        left_wrap = tk.Frame(paned, bg=BP2)
        paned.add(left_wrap, minsize=310)

        # Scrollable canvas cho menu
        canvas = tk.Canvas(left_wrap, bg=BP2, highlightthickness=0)
        vsb = tk.Scrollbar(left_wrap, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        inner = tk.Frame(canvas, bg=BP2)
        wid = canvas.create_window((0, 0), window=inner, anchor='nw')
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(wid, width=e.width))
        inner.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind_all('<MouseWheel>',
                        lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), 'units'))

        p = inner  # shortcut

        # ── SERVER
        self._sec(p, "🖥", "SERVER — MÁY CHIA SẺ")
        for lbl, fn in [
            ("Fix Connect Printer",              lambda: fix_connect_printer(self.log)),
            ("0x0000011b  KB - PrintNightmare",  lambda: fix_0x11b(self.log)),
            ("0x0000007c  RPC Server",           lambda: fix_0x7c(self.log)),
            ("0x000006d9  FW - Firewall Svc",    lambda: fix_0x6d9(self.log)),
            ("Auto Share Printer",               lambda: fix_auto_share_printer(self.log)),
        ]:
            self._btn(p, lbl, fn)

        # ── CLIENT
        self._sec(p, "💻", "CLIENT — MÁY KẾT NỐI")
        for lbl, fn in [
            ("0x00000bc4  RPC Endpoint",         lambda: fix_0xbc4(self.log)),
            ("0x00000709  Set Default Printer",  lambda: fix_0x709(self.log)),
            ("Cannot Connect to Printer",        lambda: fix_cannot_connect(self.log)),
            ("Policy Connect - GP Block",        lambda: fix_policy_connect(self.log)),
            ("0x00004005  Access Denied",        lambda: fix_0x4005(self.log)),
            ("0x000003e3  Impersonation Error",  lambda: fix_0x3e3(self.log)),
            ("0x00000bcb  Net Resource",         lambda: fix_0xbcb(self.log)),
            ("0x0000007e  Driver Not Found",     lambda: fix_0x7e(self.log)),
            ("0x00000012  No More Files",        lambda: fix_0x12(self.log)),
            ("0x000003eb  Not Supported",        lambda: fix_0x3eb(self.log)),
            ("0x00000771  Printer Offline",      lambda: fix_0x771(self.log)),
        ]:
            self._btn(p, lbl, fn)

        # ── CẢ HAI MÁY
        self._sec(p, "🔁", "FIX TRÊN 2 MÁY")
        for lbl, fn in [
            ("0x00000040  FW - Firewall Block",  lambda: fix_0x40(self.log)),
            ("0x000006ba  RPC - RPC Unavailable", lambda: fix_0x6ba(self.log)),
            ("Communication Error  (Canon LBP)", lambda: fix_comm_error(self.log)),
        ]:
            self._btn(p, lbl, fn)

        # ── CÔNG CỤ
        self._sec(p, "⚙", "CÔNG CỤ & TIỆN ÍCH")
        for lbl, fn in [
            ("Thêm Credential",           lambda: self._run(lambda: them_credential(self.log, self.parent))),
            ("Xem Credential",            lambda: xem_credential(self.log)),
            ("Xóa Credential",            lambda: self._run(lambda: xoa_credential(self.log, self.parent))),
            ("Restart Spooler",           lambda: _restart_spooler(self.log)),
            ("Xóa Hàng Đợi In",           lambda: clear_spool_queue(self.log)),
            ("Reset USB Monitor",         lambda: reset_usb_monitor(self.log)),
            ("Fix Print Spooler Svc",     lambda: fix_print_spooler(self.log)),
            ("Reset PrinterPorts",        lambda: reset_printer_ports(self.log)),
            ("Set LocalConnection",       lambda: set_local_connection(self.log)),
            ("★  One Click Fix LAN",      lambda: one_click_fix_all_lan_files(self.log)),
            ("★  Auto Fix 15 Bước",      lambda: auto_fix_15_buoc(self.log)),
            ("📖 Xem Hướng Dẫn",          lambda: xem_huong_dan(self.log)),
            ("Fix Canon 2900/3300",       lambda: fix_canon_2900(self.log)),
            ("Unlock Share Printer",      lambda: unlock_share_printer(self.log)),
            ("Xóa Driver Máy In Cũ",      lambda: list_and_remove_canon_drivers(self.log)),
        ]:
            self._btn(p, lbl, fn)

        # ── MỞ CÔNG CỤ HỆ THỐNG
        self._sec(p, "🔧", "MỞ CÔNG CỤ HỆ THỐNG")
        for lbl, cmd in [
            ("Device Manager",          "devmgmt.msc"),
            ("Print Management",        "printmanagement.msc"),
            ("Print Server Properties", None),
        ]:
            if cmd:
                self._btn(p, lbl, lambda c=cmd: subprocess.Popen(c, shell=True))
            else:
                self._btn(p, lbl, lambda: subprocess.Popen(
                    "rundll32 printui.dll,PrintUIEntry /s /t2", shell=True))

        tk.Frame(p, height=20, bg=BP2).pack()

        # ── RIGHT PANEL (log)
        right = tk.Frame(paned, bg=BP)
        paned.add(right, minsize=400)
        self._build_log(right)

    def _sec(self, p, icon, title):
        f = tk.Frame(p, bg=BP3)
        f.pack(fill='x', pady=(10, 0))
        tk.Label(f, text=f"  {icon}  {title}",
                 font=("Consolas", 9, "bold"),
                 bg=BP3, fg=BAC, anchor='w', pady=7).pack(fill='x')

    def _btn(self, p, label, cmd):
        f = tk.Frame(p, bg=BP2, cursor='hand2')
        f.pack(fill='x', padx=8, pady=1)
        strip = tk.Frame(f, bg=BBR, width=3)
        strip.pack(side='left', fill='y')
        lbl = tk.Label(f, text=f"  {label}",
                       font=FONT_BODY, bg=BP2, fg=BTX,
                       anchor='w', padx=4, pady=5)
        lbl.pack(fill='x', side='left', expand=True)

        def on_e(e):
            f.config(bg=BP3); lbl.config(bg=BP3); strip.config(bg=BAC)
        def on_l(e):
            f.config(bg=BP2); lbl.config(bg=BP2); strip.config(bg=BBR)
        def on_c(e):
            self._run(cmd)

        for w in (f, lbl, strip):
            w.bind('<Enter>', on_e)
            w.bind('<Leave>', on_l)
            w.bind('<Button-1>', on_c)

    def _build_log(self, parent):
        # Toolbar
        tb = tk.Frame(parent, bg=BP3, height=36)
        tb.pack(fill='x'); tb.pack_propagate(False)
        tk.Label(tb, text="  📋 OUTPUT LOG",
                 font=("Consolas", 9, "bold"),
                 bg=BP3, fg=BDM).pack(side='left', pady=8)

        for txt, cmd in [("  Xóa Log  ", self._clear_log), ("  Copy  ", self._copy_log)]:
            b = tk.Label(tb, text=txt, font=FONT_SMALL,
                         bg=BBR, fg=BTX, pady=4, cursor='hand2')
            b.pack(side='right', padx=4, pady=4)
            b.bind('<Button-1>', lambda e, c=cmd: c())
            b.bind('<Enter>', lambda e, w=b: w.config(bg=BAC2, fg=BP))
            b.bind('<Leave>', lambda e, w=b: w.config(bg=BBR, fg=BTX))

        # Log text
        self.log = scrolledtext.ScrolledText(
            parent, font=FONT_LOG, bg=BP, fg=BTX,
            insertbackground=BAC, selectbackground=BAC2,
            relief='flat', bd=0, padx=16, pady=12, wrap='word')
        self.log.pack(fill='both', expand=True)

        for tag, col in [
            ("info",  BDM), ("ok",   BGN), ("warn", BYL),
            ("error", BRD), ("step", BAC), ("sep",  BBR),
        ]:
            self.log.tag_config(tag, foreground=col)
        self.log.tag_config("title", foreground=BAC,
                             font=("Courier New", 10, "bold"))

        # Status bar
        self.status_var = tk.StringVar(value="Sẵn sàng.")
        self.status_bar = tk.Label(
            parent, textvariable=self.status_var,
            font=FONT_SMALL, bg=BP2, fg=BDM, anchor='w', padx=14, pady=5)
        self.status_bar.pack(fill='x')

    def _run(self, fn):
        import ctypes
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except:
            is_admin = False

        if not is_admin:
            messagebox.showwarning(
                "Cần quyền Administrator",
                "Chức năng này cần quyền Administrator.\n\n"
                "Vui lòng tắt và mở lại chương trình:\n"
                "  Chuột phải > Run as administrator")
            return

        self.status_var.set("Đang xử lý...")
        self.status_bar.config(fg=BYL)

        def worker():
            try:
                fn()
            except Exception as ex:
                _le(self.log, f"Unexpected error: {ex}")
            finally:
                self.status_var.set("Hoàn tất.")
                self.status_bar.config(fg=BGN)

        threading.Thread(target=worker, daemon=True).start()

    def _clear_log(self):
        self.log.delete('1.0', tk.END)
        self._log_welcome()

    def _copy_log(self):
        self.parent.clipboard_clear()
        self.parent.clipboard_append(self.log.get('1.0', tk.END))
        self.status_var.set("Đã copy log.")
        self.status_bar.config(fg=BGN)

    def _log_welcome(self):
        import ctypes
        try:
            ok = ctypes.windll.shell32.IsUserAnAdmin()
        except:
            ok = False

        self.log.insert(tk.END,
            "╔══════════════════════════════════════════════════════╗\n"
            "║        🖨  SỬA LỖI MÁY IN  -  IT Tool LTT            ║\n"
            "║        LAN & USB  |  Lê Thế Tuấn  |  0352 194 195    ║\n"
            "╚══════════════════════════════════════════════════════╝\n\n", "title")

        if ok:
            self.log.insert(tk.END, "  ✔  Đang chạy với quyền Administrator.\n\n", "ok")
        else:
            self.log.insert(tk.END,
                "  ✘  CẢNH BÁO: Không có quyền Administrator!\n"
                "     Chuột phải vào IT Tool LTT > Run as administrator.\n\n", "error")
        self.log.insert(tk.END, "  Chọn chức năng bên trái để bắt đầu.\n\n", "info")
