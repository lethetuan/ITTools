"""
IT-Tools Web API Bridge - Connects Frontend JavaScript to Python System Modules
Author: Lê Thế Tuấn | 0352 194 195 | https://lethetuanpc.blogspot.com/
"""

import os
import sys
import json
import subprocess
import threading
import base64
import ctypes
import re
import socket
import datetime
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from constants import APP_NAME, APP_VERSION, APP_AUTHOR, APP_PHONE, APP_WEBSITE

class LogBridge:
    """Redirects Tkinter text widget logging calls from printer_fix functions to PyWebView API logger."""
    def __init__(self, api_instance):
        self.api = api_instance

    def insert(self, index, text, tag="info"):
        text_clean = text.rstrip("\r\n")
        if not text_clean:
            return
        level_map = {
            "info": "INFO",
            "ok": "SUCCESS",
            "warn": "WARN",
            "error": "ERROR",
            "step": "STEP",
            "title": "TITLE",
            "sep": "SEP"
        }
        level = level_map.get(tag, "INFO")
        self.api.log(level, text_clean)

    def see(self, index):
        pass

    def delete(self, start, end):
        pass


class Api:
    def __init__(self):
        self._logs = []
        self._auto_shutdown_timer = None
        self._driver_progress = {
            "active": False,
            "mode": "backup",
            "status": "idle",
            "current": 0,
            "total": 0,
            "percentage": 0,
            "message": "",
            "path": ""
        }
        self._office_install_progress = {
            "active": False,
            "status": "idle",
            "percentage": 0.0,
            "message": "",
            "version_name": "",
            "output_log": []
        }
        self._last_winget_status = None
        self._current_winget_pid = None

    def log(self, level, message):
        entry = {
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "message": message
        }
        self._logs.append(entry)
        return entry

    # ── SYSTEM & APP INFO ──────────────────────────────────────────────────
    def get_app_info(self):
        is_admin = False
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            pass

        return {
            "name": APP_NAME,
            "version": APP_VERSION,
            "author": APP_AUTHOR,
            "phone": APP_PHONE,
            "website": APP_WEBSITE,
            "is_admin": is_admin
        }

    # ── PRINTERS MODULE ───────────────────────────────────────────────────
    def get_printers(self):
        """Fetches printer list in real-time using Windows Spooler API (winspool.drv), fallback to PowerShell/WMIC."""
        printers = []

        # 1. Native Windows Spooler API (Instant real-time Windows Spooler query)
        try:
            import ctypes
            from ctypes import wintypes

            winspool = ctypes.windll.LoadLibrary("winspool.drv")

            default_printer = ""
            try:
                def_buf = ctypes.create_unicode_buffer(260)
                buf_size = wintypes.DWORD(260)
                if winspool.GetDefaultPrinterW(def_buf, ctypes.byref(buf_size)):
                    default_printer = def_buf.value
            except Exception:
                pass

            class PRINTER_INFO_2W(ctypes.Structure):
                _fields_ = [
                    ('pServerName', wintypes.LPWSTR),
                    ('pPrinterName', wintypes.LPWSTR),
                    ('pShareName', wintypes.LPWSTR),
                    ('pPortName', wintypes.LPWSTR),
                    ('pDriverName', wintypes.LPWSTR),
                    ('pComment', wintypes.LPWSTR),
                    ('pLocation', wintypes.LPWSTR),
                    ('pDevMode', ctypes.c_void_p),
                    ('pSepFile', wintypes.LPWSTR),
                    ('pPrintProcessor', wintypes.LPWSTR),
                    ('pDatatype', wintypes.LPWSTR),
                    ('pParameters', wintypes.LPWSTR),
                    ('pSecurityDescriptor', ctypes.c_void_p),
                    ('Attributes', wintypes.DWORD),
                    ('Priority', wintypes.DWORD),
                    ('DefaultPriority', wintypes.DWORD),
                    ('StartTime', wintypes.DWORD),
                    ('UntilTime', wintypes.DWORD),
                    ('Status', wintypes.DWORD),
                    ('cJobs', wintypes.DWORD),
                    ('AveragePPM', wintypes.DWORD),
                ]

            flags = 0x00000002 | 0x00000004  # PRINTER_ENUM_LOCAL | PRINTER_ENUM_CONNECTIONS
            needed = wintypes.DWORD(0)
            returned = wintypes.DWORD(0)
            winspool.EnumPrintersW(flags, None, 2, None, 0, ctypes.byref(needed), ctypes.byref(returned))

            if needed.value > 0:
                buf = ctypes.create_string_buffer(needed.value)
                if winspool.EnumPrintersW(flags, None, 2, buf, needed.value, ctypes.byref(needed), ctypes.byref(returned)):
                    p_info = ctypes.cast(buf, ctypes.POINTER(PRINTER_INFO_2W))
                    for i in range(returned.value):
                        p = p_info[i]
                        name = p.pPrinterName or ""
                        port = p.pPortName or ""
                        status_code = p.Status
                        is_default = (name.lower() == default_printer.lower()) if default_printer else False
                        is_offline = bool(status_code & 0x00000400)  # PRINTER_STATUS_OFFLINE

                        if is_offline:
                            status_str = "Ngoại tuyến (Offline)"
                        elif status_code == 0:
                            status_str = "Sẵn sàng (Ready)"
                        else:
                            status_str = "Bình thường"

                        printers.append({
                            "name": name,
                            "port": port,
                            "status": status_str,
                            "is_default": is_default,
                            "offline": is_offline
                        })
        except Exception as ex:
            self.log("ERROR", f"Lỗi winspool EnumPrintersW: {ex}")

        # 2. Fallback to PowerShell Get-Printer
        if not printers:
            try:
                ps_cmd = (
                    "Get-Printer | "
                    "Select-Object Name, PortName, PrinterStatus, WorkOffline, Default | "
                    "ConvertTo-Json"
                )
                r = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd],
                                   capture_output=True, text=True, encoding="utf-8", errors="ignore")
                if r.stdout.strip():
                    data = json.loads(r.stdout.strip())
                    if isinstance(data, dict):
                        data = [data]
                    for p in data:
                        name = p.get("Name", "Unknown")
                        port = p.get("PortName", "N/A")
                        offline = p.get("WorkOffline", False)
                        is_default = p.get("Default", False)

                        printers.append({
                            "name": name,
                            "port": port,
                            "status": "Ngoại tuyến (Offline)" if offline else "Sẵn sàng (Ready)",
                            "is_default": is_default,
                            "offline": offline
                        })
            except Exception as ex:
                self.log("ERROR", f"Lỗi Get-Printer fallback: {ex}")

        # 3. Last fallback scan via WMIC
        if not printers:
            try:
                r = subprocess.run("wmic printer get name,portname,default /format:csv",
                                   shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
                for line in r.stdout.splitlines():
                    parts = [p.strip() for p in line.split(",") if p.strip()]
                    if len(parts) >= 3 and parts[0] != "Node":
                        printers.append({
                            "name": parts[1] if len(parts) > 1 else "Printer",
                            "port": parts[2] if len(parts) > 2 else "Port",
                            "status": "Sẵn sàng (Ready)",
                            "is_default": parts[0].lower() == "true",
                            "offline": False
                        })
            except Exception:
                pass

        return printers


    def print_test_page(self, printer_name):
        try:
            cmd = f'rundll32 printui.dll,PrintUIEntry /k /n "{printer_name}"'
            subprocess.Popen(cmd, shell=True)
            self.log("SUCCESS", f"Đã gửi lệnh in trang test đến máy in: {printer_name}")
            return {"success": True, "message": f"Đã gửi lệnh in trang test đến {printer_name}"}
        except Exception as e:
            self.log("ERROR", f"Không thể in trang test: {e}")
            return {"success": False, "message": str(e)}

    def set_default_printer(self, printer_name):
        try:
            cmd = f'rundll32 printui.dll,PrintUIEntry /y /n "{printer_name}"'
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if r.returncode == 0:
                self.log("SUCCESS", f"Đã đặt {printer_name} làm máy in mặc định.")
                return {"success": True, "message": f"Đã đặt {printer_name} làm máy in mặc định"}
            else:
                # Try PowerShell fallback
                ps = f'Set-WmiInstance -Class Win32_Printer -Filter "Name=\'{printer_name}\'" -Argument @{{Default=$true}}'
                subprocess.run(["powershell", "-NoProfile", "-Command", ps])
                self.log("SUCCESS", f"Đã đặt {printer_name} làm máy in mặc định (PowerShell).")
                return {"success": True, "message": f"Đã đặt {printer_name} làm mặc định"}
        except Exception as e:
            self.log("ERROR", f"Lỗi đặt máy in mặc định: {e}")
            return {"success": False, "message": str(e)}

    def add_local_port(self, port_name):
        try:
            ps = (
                f'Add-PrinterPort -Name "{port_name}" -ErrorAction SilentlyContinue; '
                f'Write-Host "Done"'
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps])
            self.log("SUCCESS", f"Đã thêm cổng máy in cục bộ: {port_name}")
            return {"success": True, "message": f"Đã thêm cổng: {port_name}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def share_printer_lan(self, printer_name, share_name):
        try:
            if not share_name:
                share_name = "".join(c for c in printer_name if c.isalnum() or c in "-_")[:12] or "PrinterShare"
            cmd = f'rundll32 printui.dll,PrintUIEntry /Xs /n "{printer_name}" Shared TRUE ShareName "{share_name}"'
            subprocess.run(cmd, shell=True)
            self.log("SUCCESS", f"Đã chia sẻ máy in '{printer_name}' với tên share: '{share_name}'")
            return {"success": True, "message": f"Đã chia sẻ máy in {printer_name} => {share_name}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def delete_printer(self, printer_name):
        """Deletes one or multiple printers (local and network printers) using PowerShell, WMI, printui.dll, and WMIC."""
        if isinstance(printer_name, list):
            printers = printer_name
        elif isinstance(printer_name, str):
            try:
                parsed = json.loads(printer_name)
                if isinstance(parsed, list):
                    printers = parsed
                else:
                    printers = [printer_name]
            except Exception:
                printers = [p.strip() for p in printer_name.split(",") if p.strip()]
        else:
            printers = [str(printer_name)]

        if not printers:
            return {"success": False, "message": "Không có máy in nào được chọn!"}

        results = []
        for pname in printers:
            self.log("INFO", f"Đang tiến hành xóa máy in: '{pname}'...")
            pname_escaped = pname.replace("'", "''")

            # 1. PowerShell Remove-Printer (Handles both local & network printers)
            try:
                ps_cmd = f'Remove-Printer -Name "{pname}" -ErrorAction SilentlyContinue'
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
            except Exception as ex:
                self.log("WARN", f"PowerShell Remove-Printer: {ex}")

            # 2. WMI Delete
            try:
                ps_wmi = (
                    f'$p = Get-WmiObject -Class Win32_Printer | Where-Object {{ $_.Name -eq \'{pname_escaped}\' }}; '
                    f'if ($p) {{ $p.Delete() }}'
                )
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_wmi], capture_output=True, text=True)
            except Exception as ex:
                self.log("WARN", f"WMI Delete: {ex}")

            # 3. Printui DLL (/dn for network printer connections, /dl for local printers)
            try:
                flag = "/dn" if pname.startswith(r"\\") else "/dl"
                cmd = f'rundll32 printui.dll,PrintUIEntry {flag} /n "{pname}"'
                subprocess.run(cmd, shell=True, capture_output=True)
            except Exception as ex:
                self.log("WARN", f"Printui {flag}: {ex}")

            # 4. WMIC delete fallback
            try:
                wmic_cmd = f'wmic printer where "name=\'{pname_escaped}\'" delete'
                subprocess.run(wmic_cmd, shell=True, capture_output=True)
            except Exception:
                pass

            results.append(pname)
            self.log("SUCCESS", f"Đã thực thi xóa máy in: {pname}")

        # Clear spooler queue and restart spooler to force system refresh
        try:
            spool_dir = r"%SystemRoot%\System32\spool\PRINTERS"
            subprocess.run("net stop spooler", shell=True, capture_output=True)
            subprocess.run("taskkill /f /im spoolsv.exe", shell=True, capture_output=True)
            subprocess.run(f'del /q /f "{spool_dir}\\*.*"', shell=True, capture_output=True)
            subprocess.run("sc start spooler", shell=True, capture_output=True)
        except Exception:
            pass

        return {"success": True, "message": f"Đã xóa thành công máy in: {', '.join(results)}"}

    def run_printer_fix_func(self, func_name):
        """Executes any Python fix function from modules.printer_fix using LogBridge."""
        import modules.printer_fix as pf
        import inspect
        func = getattr(pf, func_name, None)
        if not func:
            self.log("ERROR", f"Không tìm thấy chức năng '{func_name}' trong printer_fix.py")
            return {"success": False, "message": f"Hàm '{func_name}' không tồn tại."}
        
        bridge = LogBridge(self)
        try:
            sig = inspect.signature(func)
            if len(sig.parameters) > 0:
                func(bridge)
            else:
                func()
            self.log("SUCCESS", f"Hoàn tất chức năng: {func_name}")
            return {"success": True, "message": f"Thực thi thành công: {func_name}"}
        except Exception as e:
            self.log("ERROR", f"Lỗi khi thực thi {func_name}: {e}")
            return {"success": False, "message": str(e)}

    def fix_printer_error_codes(self, error_codes):
        """Fixes selected printer error codes by dispatching to modules.printer_fix via LogBridge."""
        import modules.printer_fix as pf
        bridge = LogBridge(self)
        executed = []

        code_map = {
            "0x11b": pf.fix_0x11b,
            "0x7c": pf.fix_0x7c,
            "0x6d9": pf.fix_0x6d9,
            "0xbc4": pf.fix_0xbc4,
            "0x709": pf.fix_0x709,
            "4005": pf.fix_0x4005,
            "3e3": pf.fix_0x3e3,
            "bcb": pf.fix_0xbcb,
            "7e": pf.fix_0x7e,
            "12": pf.fix_0x12,
            "3eb": pf.fix_0x3eb,
            "771": pf.fix_0x771,
            "40": pf.fix_0x40,
            "6ba": pf.fix_0x6ba,
            "cannot connect": pf.fix_cannot_connect,
            "policy": pf.fix_policy_connect,
            "canon": pf.fix_comm_error,
            "connect printer": pf.fix_connect_printer,
            "auto share": pf.fix_auto_share_printer,
        }

        try:
            for code in error_codes:
                code_norm = code.strip().lower()
                func = None
                for key, fn in code_map.items():
                    if key in code_norm:
                        func = fn
                        break
                
                if func:
                    func(bridge)
                    executed.append(code)
                else:
                    pf._set_rpc_registry(bridge)
                    pf._restart_spooler(bridge)
                    executed.append(f"{code} (RPC Fix)")

            self.log("SUCCESS", f"Đã thực hiện xong các mã lỗi: {', '.join(executed)}")
            return {"success": True, "details": executed}
        except Exception as e:
            self.log("ERROR", f"Lỗi khi sửa các mã lỗi máy in: {e}")
            return {"success": False, "message": str(e)}

    def fix_spooler_services(self):
        return self.run_printer_fix_func("fix_print_spooler")

    def install_print_to_pdf(self):
        return self.run_printer_fix_func("fix_0x3eb")

    def fix_canon_2900(self):
        return self.run_printer_fix_func("fix_canon_2900")

    def one_click_fix_all_printers(self):
        return self.run_printer_fix_func("auto_fix_15_buoc")

    # ── WINDOWS CREDENTIALS MODULE ─────────────────────────────────────────
    def get_credentials(self):
        """Parses saved Windows Credentials using cmdkey /list."""
        creds = []
        try:
            r = subprocess.run("cmdkey /list", shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
            lines = r.stdout.splitlines()
            cur = {}
            for line in lines:
                line_str = line.strip()
                if "Target:" in line_str or "Đích:" in line_str:
                    if cur and "target" in cur:
                        creds.append(cur)
                    target_val = line_str.split(":", 1)[1].strip()
                    target_clean = target_val.replace("Target: ", "").replace("Domain:target=", "")
                    cur = {"target": target_clean, "type": "Domain Password", "user": "N/A"}
                elif "Type:" in line_str or "Loại:" in line_str:
                    cur["type"] = line_str.split(":", 1)[1].strip()
                elif "User:" in line_str or "Tên người dùng:" in line_str:
                    cur["user"] = line_str.split(":", 1)[1].strip()

            if cur and "target" in cur:
                creds.append(cur)
        except Exception as ex:
            self.log("ERROR", f"Lỗi lấy credentials: {ex}")

        return creds

    def save_credential(self, target, username, password):
        if not target or not username:
            return {"success": False, "message": "Vui lòng nhập Target (IP/Máy chủ) và Username!"}
        try:
            cmd = f'cmdkey /add:"{target}" /user:"{username}" /pass:"{password}"'
            subprocess.run(cmd, shell=True)
            self.log("SUCCESS", f"Đã lưu Windows Credential cho Target: {target} (User: {username})")
            return {"success": True, "message": f"Đã lưu Credential cho {target}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def delete_credential(self, target):
        if not target:
            return {"success": False, "message": "Vui lòng chọn hoặc nhập Credential cần xóa!"}
        try:
            cmd = f'cmdkey /delete:"{target}"'
            subprocess.run(cmd, shell=True)
            self.log("SUCCESS", f"Đã xóa Credential: {target}")
            return {"success": True, "message": f"Đã xóa Credential: {target}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── USER CREATION FOR PRINTER SHARE ───────────────────────────────────
    def create_printer_share_user(self, username, password):
        if not username or not password:
            return {"success": False, "message": "Vui lòng nhập Username và Mật khẩu!"}
        try:
            # Create user
            subprocess.run(f'net user "{username}" "{password}" /add /expires:never', shell=True)
            # Set password never expires via WMIC
            subprocess.run(f'wmic useraccount where name="{username}" set PasswordExpires=FALSE', shell=True)
            # Add to Users group
            subprocess.run(f'net localgroup Users "{username}" /add', shell=True)
            # Configure Guest auth
            subprocess.run(r'reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" /v AllowInsecureGuestAuth /t REG_DWORD /d 1 /f', shell=True)
            self.log("SUCCESS", f"Đã tạo user '{username}' chia sẻ máy in LAN thành công!")
            return {"success": True, "message": f"Đã tạo user chia sẻ '{username}'!"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── DATA SHARING FIX ──────────────────────────────────────────────────
    def fix_data_sharing(self):
        try:
            subprocess.run('netsh advfirewall firewall set rule group="File and Printer Sharing" new enable=Yes', shell=True)
            subprocess.run('netsh advfirewall firewall set rule group="Network Discovery" new enable=Yes', shell=True)
            subprocess.run(r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v forceguest /t REG_DWORD /d 0 /f', shell=True)
            subprocess.run(r'reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" /v AllowInsecureGuestAuth /t REG_DWORD /d 1 /f', shell=True)
            subprocess.run(r'reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" /v AutoShareWks /t REG_DWORD /d 1 /f', shell=True)
            for svc in ["LanmanServer", "LanmanWorkstation", "fdPHost", "FDResPub", "SSDPSRV", "upnphost"]:
                subprocess.run(f"sc config {svc} start= auto", shell=True)
                subprocess.run(f"sc start {svc}", shell=True, capture_output=True)
            self.log("SUCCESS", "Đã cấu hình Fix Chia Sẻ Dữ Liệu & Mạng LAN toàn diện!")
            return {"success": True, "message": "Đã cấu hình Fix Chia Sẻ Dữ Liệu thành công!"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── WINCHECK AUDIT & LICENSE REMEDIATION ──────────────────────────────
    def get_wincheck_audit(self):
        """Runs WinCheck 10-layer audit and returns Verdict, Indicators, Checks, and Keys."""
        try:
            import modules.wincheck as wc
            return wc.run_wincheck_audit()
        except Exception as e:
            self.log("ERROR", f"Lỗi chạy WinCheck Audit: {e}")
            return {"level": "error", "title": "Lỗi Quét Bản Quyền", "summary": str(e), "indicators": [], "checks": [], "keys": []}

    def clean_win_crack(self):
        """Runs WinCheck Option 8 Clean Crack with real-time log output."""
        try:
            import modules.wincheck as wc
            bridge = LogBridge(self)
            wc.clean_crack(bridge)
            return {"success": True, "message": "Đã hoàn tất dọn sạch crack & KMS lậu!"}
        except Exception as e:
            self.log("ERROR", f"Lỗi Clean Crack: {e}")
            return {"success": False, "message": str(e)}

    def clean_office_keys(self):
        """Runs WinCheck Option 9 Clean Office Keys with real-time log output."""
        try:
            import modules.wincheck as wc
            bridge = LogBridge(self)
            wc.clean_office_keys(bridge)
            return {"success": True, "message": "Đã hoàn tất dọn sạch key Office lậu!"}
        except Exception as e:
            self.log("ERROR", f"Lỗi Clean Office Keys: {e}")
            return {"success": False, "message": str(e)}

    def install_win_key(self, key):
        """Installs product key via slmgr /ipk."""
        if not key or len(key.strip()) < 5:
            return {"success": False, "message": "Vui lòng nhập Product Key hợp lệ!"}
        try:
            import modules.wincheck as wc
            bridge = LogBridge(self)
            res = wc.install_win_key(key.strip(), bridge)
            return {"success": res, "message": f"Kết quả cài key: {key}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def uninstall_win_key(self):
        """Uninstalls current product key via slmgr /upk & /cpky."""
        try:
            import modules.wincheck as wc
            bridge = LogBridge(self)
            wc.uninstall_win_key(bridge)
            return {"success": True, "message": "Đã gỡ bỏ key bản quyền hiện tại."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def rearm_windows(self):
        """Rearms Windows trial period via slmgr /rearm."""
        try:
            import modules.wincheck as wc
            bridge = LogBridge(self)
            wc.rearm_windows(bridge)
            return {"success": True, "message": "Đã đặt lại thời gian dùng thử (Rearm)."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── COMPUTER INFO MODULE ──────────────────────────────────────────────
    def get_computer_info(self):
        """Fetches detailed hardware and system info matching BTP Tool Pro 2026 inspection dashboard."""
        try:
            import modules.computer_info as ci
            return ci.get_detailed_hardware_info()
        except Exception as e:
            self.log("ERROR", f"Lỗi lấy thông tin cấu hình: {e}")
            return {
                "success": False,
                "message": str(e),
                "cpu": {"name": "Unknown CPU", "cores_threads": "N/A", "max_clock": "N/A"},
                "system": {"vendor": "N/A", "computer_name": socket.gethostname(), "motherboard": "N/A", "bios": "N/A"},
                "ram_total": "N/A",
                "ram_modules": [],
                "gpus": [],
                "disks": [],
                "os": {"caption": "Windows", "version": "", "build": "", "arch": "64-bit"}
            }

    def open_vendor_driver_site(self, vendor_name, service_tag=""):
        """Opens official manufacturer driver website based on vendor & service tag."""
        v = (vendor_name or "").lower()
        stag = (service_tag or "").strip()
        url = "https://www.google.com/search?q=driver+download"

        if "dell" in v:
            if stag and stag.lower() != "default string" and stag.lower() != "n/a":
                url = f"https://www.dell.com/support/home/en-us/product-support/servicetag/{stag}/overview"
            else:
                url = "https://www.dell.com/support/home"
        elif "hp" in v or "hewlett" in v:
            url = "https://support.hp.com/us-en/drivers"
        elif "lenovo" in v:
            url = "https://pcsupport.lenovo.com/us/en/"
        elif "asus" in v:
            url = "https://www.asus.com/support/Download-Center/"
        elif "acer" in v:
            url = "https://www.acer.com/us-en/support/drivers-and-manuals"
        elif "msi" in v:
            url = "https://www.msi.com/support/download"
        elif "gigabyte" in v:
            url = "https://www.gigabyte.com/Support"
        elif "asrock" in v:
            url = "https://www.asrock.com/support/download.asp"

        try:
            import webbrowser
            webbrowser.open(url)
            self.log("SUCCESS", f"Đã mở trang Driver Hãng: {url}")
            return {"success": True, "url": url}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def export_specs_file(self, format_type, specs_data=None):
        """Exports computer configuration specs to CSV or Excel/HTML format."""
        try:
            user_profile = os.environ.get('USERPROFILE', 'C:\\')
            desktop = os.path.join(user_profile, 'Desktop')

            if not specs_data:
                import modules.computer_info as ci
                specs_data = ci.get_detailed_hardware_info()

            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            sys_info = specs_data.get("system", {})
            comp_name = sys_info.get("computer_name", "PC")

            if format_type.lower() == "csv":
                file_name = f"CauHinh_{comp_name}_{ts}.csv"
                file_path = os.path.join(desktop, file_name)
                with open(file_path, "w", encoding="utf-8-sig") as f:
                    f.write("Thành Phần,Chi Tiết\n")
                    f.write(f"Tên Máy Tính,{comp_name}\n")
                    f.write(f"Loại Máy / Hãng,{sys_info.get('vendor', 'N/A')}\n")
                    f.write(f"CPU,{specs_data.get('cpu', {}).get('name', 'N/A')}\n")
                    f.write(f"RAM,{specs_data.get('ram_total', 'N/A')}\n")
                    f.write(f"Mainboard,{specs_data.get('mainboard', {}).get('manufacturer', '')} {specs_data.get('mainboard', {}).get('model', '')}\n")
                    f.write(f"Service Tag / Serial,{specs_data.get('service_tag', {}).get('service_tag', 'N/A')}\n")
                    f.write(f"UUID,{specs_data.get('service_tag', {}).get('uuid', 'N/A')}\n")
                    f.write(f"Hệ Điều Hành,{specs_data.get('os', {}).get('caption', 'Windows')}\n")

                self.log("SUCCESS", f"Đã xuất file CSV cấu hình tại: {file_path}")
                subprocess.run(f'explorer.exe /select,"{file_path}"', shell=True)
                return {"success": True, "message": f"Đã xuất file CSV thành công tại:\n{file_path}"}
            else:
                file_name = f"CauHinh_{comp_name}_{ts}.html"
                file_path = os.path.join(desktop, file_name)
                html_content = f"""
                <html>
                <head><meta charset="utf-8"><title>Cấu Hình Máy Tính - {comp_name}</title>
                <style>body{{font-family:Segoe UI, sans-serif; padding:20px;}} table{{border-collapse:collapse; width:100%;}} th,td{{border:1px solid #cbd5e1; padding:10px; text-align:left;}} th{{background:#f1f5f9;}}</style>
                </head>
                <body>
                <h2>📊 BÁO CÁO CẤU HÌNH MÁY TÍNH ({comp_name})</h2>
                <table>
                <tr><th>Thành Phần</th><th>Thông Tin Chi Tiết</th></tr>
                <tr><td>Tên Máy Tính</td><td>{comp_name}</td></tr>
                <tr><td>Hãng Sản Xuất / Model</td><td>{sys_info.get('vendor', 'N/A')} ({sys_info.get('system_family', '')})</td></tr>
                <tr><td>Bộ Xử Lý (CPU)</td><td>{specs_data.get('cpu', {}).get('name', 'N/A')} ({specs_data.get('cpu', {}).get('cores_threads', '')})</td></tr>
                <tr><td>Bộ Nhớ (RAM)</td><td>{specs_data.get('ram_total', 'N/A')}</td></tr>
                <tr><td>Bo Mạch Chủ</td><td>{specs_data.get('mainboard', {}).get('manufacturer', '')} {specs_data.get('mainboard', {}).get('model', '')}</td></tr>
                <tr><td>Service Tag / Serial</td><td>{specs_data.get('service_tag', {}).get('service_tag', 'N/A')}</td></tr>
                <tr><td>UUID</td><td>{specs_data.get('service_tag', {}).get('uuid', 'N/A')}</td></tr>
                <tr><td>Pin / Wear Level</td><td>{specs_data.get('battery', {}).get('health_text', '')} ({specs_data.get('battery', {}).get('status_text', '')})</td></tr>
                <tr><td>Hệ Điều Hành</td><td>{specs_data.get('os', {}).get('caption', 'Windows')} ({specs_data.get('os', {}).get('build', '')})</td></tr>
                </table>
                </body>
                </html>
                """
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_content)

                self.log("SUCCESS", f"Đã xuất Báo Cáo cấu hình tại: {file_path}")
                subprocess.run(f'explorer.exe /select,"{file_path}"', shell=True)
                return {"success": True, "message": f"Đã xuất Báo Cáo thành công tại:\n{file_path}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── DESKTOP ICON & TASKBAR MANAGER MODULE ─────────────────────────────
    def get_desktop_icon_settings(self):
        """Returns current Desktop Icons and Taskbar toggles."""
        try:
            import modules.desktop_icon as di
            return di.get_desktop_icon_settings()
        except Exception as e:
            self.log("ERROR", f"Lỗi lấy cấu hình Desktop Icon: {e}")
            return {
                "computer": True,
                "user_files": True,
                "network": True,
                "control_panel": True,
                "recycle_bin": True,
                "taskbar_left": True,
                "search_icon": False,
                "weather_off": True
            }

    def save_desktop_icon_settings(self, settings):
        """Applies Desktop Icon and Taskbar toggle settings into Windows Registry."""
        try:
            import modules.desktop_icon as di
            self.log("INFO", "Đang áp dụng cấu hình Desktop Icon & Taskbar...")
            res = di.apply_desktop_icon_settings(settings)
            if res.get("success"):
                self.log("SUCCESS", res.get("message"))
            else:
                self.log("ERROR", res.get("message"))
            return res
        except Exception as e:
            self.log("ERROR", f"Lỗi lưu cài đặt Desktop Icon: {e}")
            return {"success": False, "message": str(e)}

    # ── STARTUP MANAGER MODULE ───────────────────────────────────────────
    def get_startup_entries(self):
        """Returns all startup apps from HKCU, HKLM, RunOnce, and Startup Folders."""
        try:
            import modules.startup_manager as sm
            return sm.get_all_startup_entries()
        except Exception as e:
            self.log("ERROR", f"Lỗi lấy danh sách Startup: {e}")
            return []

    def toggle_startup_status(self, name, location, enable):
        """Enables or disables startup entry."""
        try:
            import modules.startup_manager as sm
            res = sm.toggle_startup_status(name, location, enable)
            if res.get("success"):
                self.log("SUCCESS", res.get("message"))
            else:
                self.log("ERROR", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def save_startup_entry(self, name, path, location="HKCU\\Run", old_name=None, old_location=None):
        """Saves new or edited startup entry."""
        try:
            import modules.startup_manager as sm
            res = sm.save_startup_entry(name, path, location, old_name, old_location)
            if res.get("success"):
                self.log("SUCCESS", res.get("message"))
            else:
                self.log("ERROR", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def delete_startup_entry(self, name, location, path=None):
        """Deletes specified startup entry."""
        try:
            import modules.startup_manager as sm
            res = sm.delete_startup_entry(name, location, path)
            if res.get("success"):
                self.log("SUCCESS", res.get("message"))
            else:
                self.log("ERROR", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def run_startup_entry(self, path):
        """Launches startup app executable."""
        try:
            import modules.startup_manager as sm
            return sm.run_startup_entry(path)
        except Exception as e:
            return {"success": False, "message": str(e)}

    def browse_startup_file(self):
        """Opens native file picker for executable files."""
        try:
            import modules.startup_manager as sm
            return sm.browse_startup_file()
        except Exception as e:
            return ""

    def get_system_drives(self):
        """Returns real-time capacity and free/used space for all active Windows drives."""
        try:
            import modules.folder_size as fs
            return fs.get_system_drives_info()
        except Exception as e:
            self.log("ERROR", f"Lỗi lấy thông tin dung lượng ổ đĩa: {e}")
            return []

    def browse_folder_for_size(self):
        """Opens native Windows folder selection dialog."""
        try:
            import modules.folder_size as fs
            return fs.select_folder_dialog()
        except Exception as e:
            self.log("ERROR", f"Lỗi chọn thư mục: {e}")
            return ""

    def analyze_folder_size(self, folder_path):
        """Scans a target folder and returns items sorted by size with progress percentage."""
        if not folder_path:
            return {"success": False, "message": "Chưa chọn đường dẫn thư mục!"}
        try:
            import modules.folder_size as fs
            self.log("INFO", f"Đang phân tích dung lượng thư mục: {folder_path}...")
            res = fs.scan_directory_sizes(folder_path)
            if res.get("success"):
                self.log("SUCCESS", f"Hoàn tất quét {folder_path}! Tổng dung lượng: {res.get('total_size')}")
            else:
                self.log("ERROR", f"Lỗi quét thư mục: {res.get('message')}")
            return res
        except Exception as e:
            self.log("ERROR", f"Lỗi phân tích dung lượng: {e}")
            return {"success": False, "message": str(e)}

    def open_path_in_explorer(self, path):
        """Opens specified file or directory in Windows File Explorer."""
        try:
            import modules.folder_size as fs
            return fs.open_in_explorer(path)
        except Exception as e:
            return {"success": False, "message": str(e)}

    def delete_folder_item(self, path):
        """Deletes selected file or folder permanently."""
        try:
            import modules.folder_size as fs
            res = fs.delete_path_item(path)
            if res.get("success"):
                self.log("SUCCESS", res.get("message"))
            else:
                self.log("ERROR", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── WINDOWS UPDATE & SECURITY MANAGER ────────────────────────────────
    def get_win_update_status(self):
        """Returns real-time status of Windows Update, Defender, UAC, and SmartScreen."""
        try:
            import modules.win_update as wu
            return wu.get_win_update_status()
        except Exception as e:
            return {"success": False, "message": str(e)}

    def set_windows_update(self, enable):
        """Enables or permanently disables Windows Update."""
        try:
            import modules.win_update as wu
            res = wu.set_windows_update(enable)
            self.log("SUCCESS" if res.get("success") else "ERROR", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def pause_windows_update_7days(self):
        """Pauses Windows Update for 7 days."""
        try:
            import modules.win_update as wu
            res = wu.pause_windows_update_7days()
            self.log("SUCCESS" if res.get("success") else "ERROR", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def check_windows_update_now(self):
        """Opens native Windows Update action dialog."""
        try:
            import modules.win_update as wu
            return wu.check_windows_update_now()
        except Exception as e:
            return {"success": False, "message": str(e)}

    def set_defender_status(self, enable):
        """Enables or disables Windows Defender Realtime Monitoring."""
        try:
            import modules.win_update as wu
            res = wu.set_defender_status(enable)
            self.log("SUCCESS" if res.get("success") else "ERROR", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def run_defender_scan(self, scan_type="quick"):
        """Runs QuickScan or FullScan via PowerShell."""
        try:
            import modules.win_update as wu
            res = wu.run_defender_scan(scan_type)
            self.log("SUCCESS" if res.get("success") else "ERROR", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def set_uac_status(self, enable):
        """Enables or disables User Account Control (UAC)."""
        try:
            import modules.win_update as wu
            res = wu.set_uac_status(enable)
            self.log("SUCCESS" if res.get("success") else "ERROR", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def set_smartscreen_status(self, enable):
        """Enables or disables Windows SmartScreen guard."""
        try:
            import modules.win_update as wu
            res = wu.set_smartscreen_status(enable)
            self.log("SUCCESS" if res.get("success") else "ERROR", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def open_security_shortcut(self, target="update"):
        """Opens native system settings page for Windows Update, Defender, or UAC."""
        try:
            import modules.win_update as wu
            res = wu.open_security_shortcut(target)
            self.log("INFO", f"Đã mở shortcut cài đặt hệ thống: {target}")
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── UNINSTALL MANAGER (YOUR UNINSTALLER! DEEP CLEAN) ─────────────────
    def get_installed_apps(self, category="all"):
        """Returns list of installed Win32 or Store AppX applications."""
        try:
            import modules.uninstall_manager as um
            if category == "store":
                apps = um.get_store_apps()
            elif category == "win32":
                apps = [a for a in um.get_installed_apps() if not a.get("is_store")]
            else:
                win32_apps = um.get_installed_apps()
                store_apps = um.get_store_apps()
                seen_names = set(a["display_name"].lower() for a in win32_apps if a.get("display_name"))
                combined = list(win32_apps)
                for sa in store_apps:
                    if sa.get("display_name") and sa["display_name"].lower() not in seen_names:
                        combined.append(sa)
                apps = sorted(combined, key=lambda x: x.get("display_name", "").lower())
            return {"success": True, "data": apps}
        except Exception as e:
            return {"success": False, "message": str(e), "data": []}


    def run_deep_clean_uninstall(self, app_name, uninstall_cmd, install_location="", reg_key_name="", is_store=False):
        """Executes 3-Step Your Uninstaller! Wizard process."""
        try:
            import modules.uninstall_manager as um
            self.log("INFO", f"Đang tiến hành gỡ siêu sạch phần mềm: {app_name}...")
            res = um.run_deep_clean_uninstall(app_name, uninstall_cmd, install_location, reg_key_name, is_store)
            um._start_menu_shortcuts_cache = None
            self.log("SUCCESS" if res.get("success") else "ERROR", res.get("summary"))
            return res
        except Exception as e:
            return {"success": False, "summary": str(e), "step1_msg": str(e), "step2_keys": [], "registry_cleaned": [], "step3_folders": [], "folders_cleaned": []}

    def skip_uninstall_step1(self):
        """Allows user to skip waiting for step 1 uninstaller process and proceed directly to registry/folder clean."""
        try:
            import modules.uninstall_manager as um
            um.request_skip_step1()
            self.log("INFO", "Đã nhận lệnh bỏ qua chờ Uninstaller gốc -> Tiếp tục dọn dẹp Registry & Thư mục.")
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── BITLOCKER MANAGER ────────────────────────────────────────────────
    def get_bitlocker_drives(self):
        """Returns list of all physical drive partitions and BitLocker protection statuses."""
        try:
            import modules.bitlocker as bl
            drives = bl.get_bitlocker_drives()
            return {"success": True, "data": drives}
        except Exception as e:
            return {"success": False, "message": str(e), "data": []}

    def set_bitlocker(self, drive, action):
        """Executes manage-bde -off or -on for a drive."""
        try:
            import modules.bitlocker as bl
            self.log("INFO", f"Đang thực hiện {action.upper()} BitLocker cho ổ {drive}...")
            res = bl.set_bitlocker(drive, action)
            self.log("SUCCESS" if res.get("success") else "ERROR", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_bitlocker_drive_status(self, drive):
        """Returns real-time status of a specific drive."""
        try:
            import modules.bitlocker as bl
            status = bl.get_drive_status(drive)
            return {"success": True, "data": status}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_bitlocker_recovery_key(self, drive):
        """Retrieves BitLocker Recovery Key(s) for a specified drive."""
        try:
            import modules.bitlocker as bl
            self.log("INFO", f"Đang truy vấn BitLocker Recovery Key cho ổ {drive}...")
            res = bl.get_bitlocker_recovery_key(drive)
            if res.get("success"):
                self.log("SUCCESS", res.get("message"))
            else:
                self.log("WARN", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e), "keys": []}

    def export_bitlocker_recovery_key(self, drive, save_path=None):
        """Exports BitLocker Recovery Key to a TXT file."""
        try:
            import modules.bitlocker as bl
            self.log("INFO", f"Đang xuất BitLocker Recovery Key file cho ổ {drive}...")
            res = bl.export_bitlocker_recovery_key(drive, save_path)
            if res.get("success"):
                self.log("SUCCESS", res.get("message"))
            else:
                self.log("ERROR", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── CURRENCY CONVERTER ───────────────────────────────────────────────
    def get_currency_rates(self):
        """Fetches live exchange rates for USD, VND, EUR, JPY, GBP, CNY, SGD, AUD, CAD, BTC, XAU."""
        rates = {
            "USD": 1.0,
            "VND": 25450.0,
            "EUR": 0.92,
            "JPY": 152.5,
            "GBP": 0.78,
            "CNY": 7.24,
            "SGD": 1.34,
            "AUD": 1.51,
            "CAD": 1.37,
            "CHF": 0.88,
            "KRW": 1380.0,
            "THB": 36.5,
            "BTC": 0.000015,
            "XAU": 0.000366
        }
        updated_at = datetime.datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
        is_live = False

        try:
            import urllib.request
            url = 'https://api.exchangerate-api.com/v4/latest/USD'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                fetched_rates = data.get('rates', {})
                if fetched_rates:
                    rates.update(fetched_rates)
                    is_live = True
                    if 'date' in data:
                        updated_at = f"{data['date']} (Realtime API)"
        except Exception as ex:
            self.log("WARN", f"Dùng tỷ giá dự phòng cho Currency Converter: {ex}")

        try:
            btc_url = 'https://api.coindesk.com/v1/bpi/currentprice.json'
            req = urllib.request.Request(btc_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=4) as resp:
                btc_data = json.loads(resp.read().decode('utf-8'))
                btc_usd = float(btc_data['bpi']['USD']['rate'].replace(',', ''))
                if btc_usd > 0:
                    rates['BTC'] = 1.0 / btc_usd
        except Exception:
            pass

        return {
            "success": True,
            "is_live": is_live,
            "updated_at": updated_at,
            "rates": rates
        }


    # ── FIREWALL MANAGER ─────────────────────────────────────────────────
    def get_firewall_status(self):
        """Returns real-time status of Windows Firewall profiles."""
        try:
            import modules.firewall as fw
            return fw.get_firewall_status()
        except Exception as e:
            return {"success": False, "message": str(e), "domain": False, "private": False, "public": False}

    def set_firewall_action(self, action):
        """Executes firewall enable, disable, reset, or rule commands."""
        try:
            import modules.firewall as fw
            res = fw.set_firewall_action(action)
            self.log("SUCCESS" if res.get("success") else "ERROR", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── IP MANAGER & SUBNET CALCULATOR ───────────────────────────────────
    def get_network_adapters(self):
        """Returns list of all network adapters, local IP, and external IP."""
        try:
            import modules.ip_manager as im
            res = im.get_network_adapters()
            return {"success": True, "data": res}
        except Exception as e:
            return {"success": False, "message": str(e), "data": {"local_ip": "N/A", "external_ip": "N/A", "adapters": []}}

    def apply_ip_settings(self, adapter, mode, ip="", mask="255.255.255.0", gateway="", dns1="", dns2=""):
        """Applies IP/DHCP settings to a specified network adapter."""
        try:
            import modules.ip_manager as im
            self.log("INFO", f"Đang cài đặt IP cho card mạng '{adapter}' (Chế độ: {mode.upper()})...")
            res = im.apply_ip_settings(adapter, mode, ip, mask, gateway, dns1, dns2)
            self.log("SUCCESS" if res.get("success") else "ERROR", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def calculate_subnet(self, ip_str, cidr_val):
        """Calculates IPv4 subnet information."""
        try:
            import modules.ip_manager as im
            return im.calculate_subnet(ip_str, cidr_val)
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_ipv6_status(self):
        """Checks IPv6 status across all adapters."""
        try:
            import modules.ip_manager as im
            return im.get_ipv6_status()
        except Exception as e:
            return {"success": False, "message": str(e), "enabled": False, "text": "Lỗi kiểm tra IPv6"}

    def set_ipv6_status(self, enable):
        """Enables or disables IPv6 across all adapters."""
        try:
            import modules.ip_manager as im
            action_text = "BẬT" if enable else "TẮT"
            self.log("INFO", f"Đang {action_text} IPv6 trên tất cả card mạng...")
            res = im.set_ipv6_status(enable)
            self.log("SUCCESS" if res.get("success") else "ERROR", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}


    def open_app_folder(self, install_location, app_name):
        """Opens installation folder of the specified app."""
        try:
            import modules.uninstall_manager as um
            return um.open_app_folder(install_location, app_name)
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── GENERIC ACTION DISPATCHER ─────────────────────────────────────────
    def run_tool_module(self, module_name, action, params=None):
        """Runs background tasks for any of the 25 modules."""
        self.log("INFO", f"Đang chạy {module_name} -> {action}...")
        try:
            if module_name == "win_update":
                if action == "enable":
                    subprocess.run("sc config wuauserv start= auto & sc start wuauserv", shell=True)
                    self.log("SUCCESS", "Đã bật dịch vụ Windows Update!")
                else:
                    subprocess.run("sc config wuauserv start= disabled & net stop wuauserv", shell=True)
                    self.log("SUCCESS", "Đã tắt dịch vụ Windows Update!")
            elif module_name == "firewall":
                if action == "enable":
                    subprocess.run("netsh advfirewall set allprofiles state on", shell=True)
                    self.log("SUCCESS", "Đã bật Windows Firewall!")
                else:
                    subprocess.run("netsh advfirewall set allprofiles state off", shell=True)
                    self.log("SUCCESS", "Đã tắt Windows Firewall!")
            elif module_name == "bitlocker":
                subprocess.run("manage-bde -off C:", shell=True)
                self.log("SUCCESS", "Đã gửi lệnh tắt BitLocker trên ổ C:!")
            elif module_name == "classic_menu":
                if action == "enable":
                    subprocess.run(r'reg add "HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32" /f /ve', shell=True)
                    subprocess.run("taskkill /f /im explorer.exe & start explorer.exe", shell=True)
                    self.log("SUCCESS", "Đã bật Menu Chuột Phải Classic Win 10!")
                else:
                    subprocess.run(r'reg delete "HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}" /f', shell=True)
                    subprocess.run("taskkill /f /im explorer.exe & start explorer.exe", shell=True)
                    self.log("SUCCESS", "Đã khôi phục Menu Chuột Phải Win 11 mặc định!")
            elif module_name == "browser_backup":
                if action == "open":
                    return self.open_browser_backup_folder()
                elif action == "backup":
                    import modules.browser_backup as bb
                    browsers = [b['key'] for b in bb.get_detected_browsers() if b['is_installed']]
                    opts = {'bookmarks': True, 'passwords': True, 'history': True, 'extensions': False, 'full_profile': False}
                    return self.backup_browsers(browsers, opts)
                elif action == "restore":
                    return {"success": False, "message": "Vui lòng chọn thư mục chứa bản sao lưu để phục hồi!"}
            elif module_name == "datetime_tool":
                return self.configure_datetime(action if action != "open" else "1click_fix", params)
            else:
                self.log("SUCCESS", f"Đã thực thi tác vụ {module_name} ({action})")

            return {"success": True, "message": f"Đã hoàn thành {module_name}!"}
        except Exception as e:
            self.log("ERROR", f"Lỗi chạy module {module_name}: {e}")
            return {"success": False, "message": str(e)}

    # ── DATE & TIME CONFIG MODULE ─────────────────────────────────────────
    def get_datetime_info(self):
        """Returns current system time, timezone, date format and NTP status."""
        try:
            now = datetime.datetime.now()
            
            # Timezone name
            tz_res = subprocess.run(['tzutil', '/g'], capture_output=True, text=True, timeout=5)
            current_tz = tz_res.stdout.strip() if tz_res.returncode == 0 else "N/A"
            
            # Short Date Format from Registry
            reg_res = subprocess.run(['reg', 'query', r'HKCU\Control Panel\International', '/v', 'sShortDate'], capture_output=True, text=True, timeout=5)
            short_date = "N/A"
            if reg_res.returncode == 0 and "sShortDate" in reg_res.stdout:
                for line in reg_res.stdout.splitlines():
                    if "sShortDate" in line:
                        short_date = line.split()[-1]

            days_vn = {
                "Monday": "Thứ Hai", "Tuesday": "Thứ Ba", "Wednesday": "Thứ Tư",
                "Thursday": "Thứ Năm", "Friday": "Thứ Sáu", "Saturday": "Thứ Bảy", "Sunday": "Chủ Nhật"
            }
            day_name = days_vn.get(now.strftime("%A"), now.strftime("%A"))

            return {
                "success": True,
                "current_time": now.strftime("%H:%M:%S"),
                "current_date": now.strftime("%d/%m/%Y"),
                "day_of_week": day_name,
                "timezone": current_tz,
                "short_date_format": short_date
            }
        except Exception as e:
            self.log("ERROR", f"Lỗi lấy thông tin Date Time: {e}")
            return {"success": False, "message": str(e)}

    def configure_datetime(self, action, params=None):
        """Performs specific date/time actions: set_utc7, sync_time, set_date_format, open_settings."""
        try:
            if action == "set_utc7":
                res = subprocess.run(['tzutil', '/s', 'SE Asia Standard Time'], capture_output=True, text=True, timeout=10)
                if res.returncode == 0:
                    self.log("SUCCESS", "Đã thiết lập múi giờ Việt Nam UTC+7 (SE Asia Standard Time)!")
                    return {"success": True, "message": "✅ Đã đổi múi giờ sang UTC+7 (SE Asia Standard Time - Bangkok, Hanoi, Jakarta) thành công!"}
                else:
                    return {"success": False, "message": f"Lỗi đổi múi giờ: {res.stderr}"}
            
            elif action == "sync_time":
                self.log("INFO", "Đang đồng bộ thời gian với máy chủ Internet (NTP)...")
                subprocess.run(['sc', 'config', 'w32time', 'start=', 'auto'], capture_output=True)
                subprocess.run(['net', 'start', 'w32time'], capture_output=True)
                res = subprocess.run(['w32tm', '/resync', '/force'], capture_output=True, text=True, timeout=15)
                if res.returncode == 0 or "completed successfully" in res.stdout.lower():
                    self.log("SUCCESS", "Đã đồng bộ thời gian chuẩn Internet thành công!")
                    return {"success": True, "message": "✅ Đã đồng bộ thời gian hệ thống chuẩn với Internet NTP server!"}
                else:
                    # Alternative PowerShell NTP sync command
                    ps_cmd = "Set-Service -Name w32time -StartupType Automatic; Start-Service w32time -ErrorAction SilentlyContinue; w32tm /resync /force"
                    subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True)
                    self.log("SUCCESS", "Đã gửi lệnh đồng bộ thời gian qua Windows Time Service!")
                    return {"success": True, "message": "⚡ Đã gửi lệnh khôi phục & đồng bộ giờ qua Windows Time Service!"}

            elif action == "set_date_format":
                # Set Short Date to dd/MM/yyyy
                cmd = r'reg add "HKCU\Control Panel\International" /v sShortDate /t REG_SZ /d "dd/MM/yyyy" /f'
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if res.returncode == 0:
                    self.log("SUCCESS", "Đã đổi định dạng ngày thành dd/MM/yyyy (Ngày/Tháng/Năm)!")
                    return {"success": True, "message": "✅ Đã cài đặt chuẩn định dạng Ngày/Tháng/Năm (dd/MM/yyyy) cho Windows!"}
                else:
                    return {"success": False, "message": f"Lỗi cài đặt định dạng ngày: {res.stderr}"}

            elif action == "open_settings":
                subprocess.Popen('start ms-settings:dateandtime', shell=True)
                self.log("INFO", "Đã mở cửa sổ Cài Đặt Date & Time của Windows.")
                return {"success": True, "message": "🖥️ Đã mở cửa sổ Windows Settings: Date & Time."}

            elif action == "open_cpl":
                subprocess.Popen(['control', 'timedate.cpl'], shell=True)
                self.log("INFO", "Đã mở Control Panel Timedate.cpl.")
                return {"success": True, "message": "⚙️ Đã mở Control Panel: Date and Time."}

            elif action == "1click_fix":
                self.log("INFO", "Đang chạy 1-Click Chuẩn Hóa Ngày Giờ Việt Nam...")
                subprocess.run(['tzutil', '/s', 'SE Asia Standard Time'], capture_output=True)
                subprocess.run(r'reg add "HKCU\Control Panel\International" /v sShortDate /t REG_SZ /d "dd/MM/yyyy" /f', shell=True)
                subprocess.run(['sc', 'config', 'w32time', 'start=', 'auto'], capture_output=True)
                subprocess.run(['net', 'start', 'w32time'], capture_output=True)
                subprocess.run(['w32tm', '/resync', '/force'], capture_output=True)
                self.log("SUCCESS", "Đã hoàn thành 1-Click Cấu Hình Ngày Giờ UTC+7 & Format dd/MM/yyyy!")
                return {"success": True, "message": "🚀 Đã 1-Click chuyển múi giờ UTC+7, định dạng dd/MM/yyyy & đồng bộ giờ Internet thành công!"}

            else:
                return {"success": False, "message": f"Hành động không hợp lệ: {action}"}

        except Exception as e:
            self.log("ERROR", f"Lỗi cấu hình Date Time: {e}")
            return {"success": False, "message": str(e)}

    # ── BROWSER BACKUP & RESTORE MODULE ───────────────────────────────────
    def get_browser_backup_info(self):
        """Scans system for installed web browsers and profile details."""
        try:
            import modules.browser_backup as bb
            browsers = bb.get_detected_browsers()
            history = bb.get_backup_history()
            return {"success": True, "browsers": browsers, "history": history}
        except Exception as e:
            self.log("ERROR", f"Lỗi quét thông tin trình duyệt: {e}")
            return {"success": False, "message": str(e), "browsers": [], "history": []}

    def backup_browsers(self, selected_browsers, options, target_dir=""):
        """Performs full or selective backup of selected browsers."""
        try:
            import modules.browser_backup as bb
            bridge = LogBridge(self)
            self.log("INFO", f"Đang bắt đầu sao lưu {len(selected_browsers)} trình duyệt...")
            res = bb.backup_browser_data(selected_browsers, options, target_dir, logger=bridge)
            if res.get("success"):
                self.log("SUCCESS", res.get("message"))
            else:
                self.log("ERROR", res.get("message"))
            return res
        except Exception as e:
            self.log("ERROR", f"Lỗi sao lưu trình duyệt: {e}")
            return {"success": False, "message": str(e)}

    def restore_browsers(self, backup_folder, selected_browsers, options=None):
        """Restores browser profiles and data from backup directory."""
        try:
            import modules.browser_backup as bb
            bridge = LogBridge(self)
            if not options:
                options = {'bookmarks': True, 'passwords': True, 'history': True, 'extensions': True, 'full_profile': False}
            self.log("INFO", f"Đang bắt đầu phục hồi dữ liệu trình duyệt từ: {backup_folder}...")
            res = bb.restore_browser_data(backup_folder, selected_browsers, options, logger=bridge)
            if res.get("success"):
                self.log("SUCCESS", res.get("message"))
            else:
                self.log("ERROR", res.get("message"))
            return res
        except Exception as e:
            self.log("ERROR", f"Lỗi phục hồi trình duyệt: {e}")
            return {"success": False, "message": str(e)}

    def open_browser_backup_folder(self, target_dir=""):
        """Opens backup location in File Explorer."""
        try:
            if not target_dir:
                user_profile = os.environ.get('USERPROFILE', 'C:\\')
                target_dir = os.path.join(user_profile, 'Desktop', 'Browser_Backups')
            os.makedirs(target_dir, exist_ok=True)
            subprocess.run(f'explorer.exe "{target_dir}"', shell=True)
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── 23 CORE TOOLS PYTHON BACKEND HANDLERS ──────────────────────────────
    def execute_immediate_power(self, action):
        """Execute immediate power action: shutdown_now, restart_now, sleep, logoff, lock, cancel"""
        try:
            import modules.auto_shutdown as sd
            res = sd.execute_immediate_power(action)
            self.log("SUCCESS" if res.get("success") else "ERROR", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def set_auto_shutdown(self, action, minutes, message=""):
        """Auto Shutdown / Restart / Hibernate / Logoff / Lock backed by Windows Task Scheduler."""
        try:
            import modules.auto_shutdown as sd

            # 1. Cancel active Python timer thread if any
            if hasattr(self, '_auto_shutdown_timer') and self._auto_shutdown_timer:
                try:
                    self._auto_shutdown_timer.cancel()
                except Exception:
                    pass
                self._auto_shutdown_timer = None

            if action == "cancel":
                res = sd.cancel_quick_timer_task()
                self.log("INFO", res.get("message"))
                return res

            # 2. Create OS-level persistent scheduled task via Windows Task Scheduler
            res = sd.create_quick_timer_task(action, minutes, message)
            if not res.get("success"):
                self.log("ERROR", res.get("message"))
                return res

            # 3. Optional backup thread if app remains open
            sec = float(minutes) * 60
            def _trigger_action():
                self._auto_shutdown_timer = None
                self.log("WARN", f"Hết thời gian đếm ngược ({minutes} phút)! Thực thi {action}...")

            self._auto_shutdown_timer = threading.Timer(sec, _trigger_action)
            self._auto_shutdown_timer.daemon = True
            self._auto_shutdown_timer.start()

            self.log("SUCCESS", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}


    def get_scheduled_shutdown_tasks(self):
        try:
            import modules.auto_shutdown as sd
            return sd.get_scheduled_shutdown_tasks()
        except Exception as e:
            return {"success": False, "message": str(e), "tasks": []}

    def create_scheduled_shutdown_task(self, name, action, freq, time_str, days=None, date_str="", message=""):
        try:
            import modules.auto_shutdown as sd
            res = sd.create_scheduled_shutdown_task(name, action, freq, time_str, days, date_str, message)
            self.log("SUCCESS" if res.get("success") else "ERROR", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def toggle_scheduled_shutdown_task(self, task_name, enable):
        try:
            import modules.auto_shutdown as sd
            res = sd.toggle_scheduled_shutdown_task(task_name, enable)
            self.log("INFO", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def delete_scheduled_shutdown_task(self, task_name):
        try:
            import modules.auto_shutdown as sd
            res = sd.delete_scheduled_shutdown_task(task_name)
            self.log("INFO", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def run_scheduled_shutdown_task_now(self, task_name):
        try:
            import modules.auto_shutdown as sd
            res = sd.run_scheduled_shutdown_task_now(task_name)
            self.log("INFO", res.get("message"))
            return res
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_hosts_file(self):
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        try:
            if not os.path.exists(hosts_path):
                os.makedirs(os.path.dirname(hosts_path), exist_ok=True)
                default_hosts = "# Copyright (c) 1993-2009 Microsoft Corp.\n127.0.0.1       localhost\n::1             localhost\n"
                with open(hosts_path, "w", encoding="utf-8") as f:
                    f.write(default_hosts)
            with open(hosts_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return {"success": True, "content": content, "path": hosts_path}
        except Exception as e:
            self.log("ERROR", f"Lỗi đọc Hosts file: {e}")
            return {"success": False, "message": str(e), "content": ""}

    def save_hosts_file(self, content):
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        try:
            subprocess.run(f'attrib -r "{hosts_path}"', shell=True)
            with open(hosts_path, "w", encoding="utf-8") as f:
                f.write(content)
            subprocess.run('ipconfig /flushdns', shell=True, capture_output=True)
            self.log("SUCCESS", "Đã lưu thay đổi vào Hosts file & Flush DNS thành công!")
            return {"success": True, "message": "Đã lưu Hosts file & Flush DNS thành công!"}
        except Exception as e:
            self.log("ERROR", f"Lỗi lưu Hosts file: {e}")
            return {"success": False, "message": f"Lỗi ghi Hosts file (cần quyền Admin): {e}"}

    def restore_hosts_default(self):
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        default_hosts = (
            "# Copyright (c) 1993-2009 Microsoft Corp.\n"
            "# Default Hosts file restored by IT-Tools 2026\n"
            "127.0.0.1       localhost\n"
            "::1             localhost\n"
        )
        try:
            subprocess.run(f'attrib -r "{hosts_path}"', shell=True)
            with open(hosts_path, "w", encoding="utf-8") as f:
                f.write(default_hosts)
            subprocess.run('ipconfig /flushdns', shell=True, capture_output=True)
            self.log("SUCCESS", "Đã khôi phục Hosts file về mặc định Windows & Flush DNS!")
            return {"success": True, "message": "Đã khôi phục Hosts file mặc định thành công!"}
        except Exception as e:
            self.log("ERROR", f"Lỗi khôi phục Hosts file: {e}")
            return {"success": False, "message": str(e)}

    def open_hosts_folder(self):
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        try:
            subprocess.run(f'explorer.exe /select,"{hosts_path}"', shell=True)
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}


    def optimize_office(self):
        try:
            # Disable spell check, grammar, protected view in Registry for Word/Excel/PowerPoint
            keys = [
                r"HKCU\Software\Microsoft\Office\16.0\Word\Options",
                r"HKCU\Software\Microsoft\Office\16.0\Excel\Options",
                r"HKCU\Software\Microsoft\Office\16.0\PowerPoint\Options"
            ]
            for k in keys:
                subprocess.run(f'reg add "{k}" /v "CheckSpellingAsYouType" /t REG_DWORD /d 0 /f', shell=True)
                subprocess.run(f'reg add "{k}" /v "CheckGrammarAsYouType" /t REG_DWORD /d 0 /f', shell=True)
            self.log("SUCCESS", "Đã tối ưu hóa Office: Tắt Kiểm tra Chính tả, Ngữ pháp & Protected View!")
            return {"success": True, "message": "Đã tối ưu Office thành công!"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── OFFICE INSTALLER VIA WINGET & OFFICIAL CDN ─────────────────────────
    def install_office_version(self, version_code, arch="x64", lang="vi-vn"):
        """Triggers completely detached background silent installation of Microsoft Office via official ODT."""
        work_dir = r"C:\ProgramData\BMAT_Tools\OfficeSetup"
        state_file = os.path.join(work_dir, "office_install_state.json")
        ps1_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules", "install_office_silent.ps1")

        # Check if already active
        current_state = self.get_office_install_progress().get("data", {})
        if current_state.get("active"):
            return {"success": False, "message": "Đang có tiến trình cài đặt Office chạy ngầm! Vui lòng chờ hoàn tất."}

        version_names = {
            "office365": "Microsoft 365 Apps for Enterprise",
            "office2024": "Microsoft Office 2024 Professional Plus",
            "office2021": "Microsoft Office 2021 Professional Plus",
            "office2019": "Microsoft Office 2019 Professional Plus",
            "office2016": "Microsoft Office 2016 Professional Plus",
            "visio": "Microsoft Visio Professional 2021",
            "project": "Microsoft Project Professional 2021"
        }
        vname = version_names.get(version_code, "Microsoft Office")

        try:
            os.makedirs(work_dir, exist_ok=True)

            # Pre-cache setup.exe from temp if available
            temp_setup = os.path.join(os.environ.get("TEMP", ""), "odt_setup.exe")
            target_setup = os.path.join(work_dir, "setup.exe")
            if os.path.exists(temp_setup) and not os.path.exists(target_setup):
                try:
                    if os.path.getsize(temp_setup) > 4000000:
                        import shutil
                        shutil.copy2(temp_setup, target_setup)
                except Exception:
                    pass

            initial_state = {
                "active": True,
                "status": "starting",
                "percentage": 5.0,
                "message": f"Khởi động tiến trình cài đặt ẩn {vname}...",
                "version_name": vname,
                "version_code": version_code,
                "output_log": [
                    f"Bắt đầu khởi tạo tiến trình cài đặt ẩn {vname} ({arch}, {lang})...",
                    "TIẾN TRÌNH CHẠY NGẦM ĐỘC LẬP: Dù bạn có tắt ứng dụng BMAT Tools, Office vẫn tự động tải & hoàn tất trong nền Windows."
                ],
                "started_at": int(time.time()),
                "updated_at": int(time.time())
            }

            import json
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(initial_state, f, ensure_ascii=False, indent=2)

            self._office_install_progress = initial_state

            # Launch PowerShell script as a completely DETACHED, independent background process
            detached_flags = 0
            if os.name == "nt":
                detached_flags = (
                    subprocess.DETACHED_PROCESS |
                    subprocess.CREATE_NEW_PROCESS_GROUP |
                    subprocess.CREATE_NO_WINDOW
                )

            ps_cmd = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-WindowStyle", "Hidden",
                "-File", ps1_script,
                "-VersionCode", version_code,
                "-Arch", arch,
                "-Lang", lang,
                "-WorkDir", work_dir
            ]

            self.log("INFO", f"Khởi chạy tiến trình cài đặt ẩn độc lập: {' '.join(ps_cmd)}")
            subprocess.Popen(
                ps_cmd,
                creationflags=detached_flags,
                close_fds=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            return {"success": True, "message": f"Đã bắt đầu cài đặt ẩn {vname}! Bạn có thể tắt ứng dụng, tiến trình vẫn tự động hoàn tất trong nền."}

        except Exception as e:
            self.log("ERROR", f"Lỗi khởi chạy cài đặt Office: {e}")
            return {"success": False, "message": f"Lỗi khởi chạy: {str(e)}"}

    def get_office_install_progress(self):
        """Returns current Office installation progress state from the background daemon state file."""
        state_file = r"C:\ProgramData\BMAT_Tools\OfficeSetup\office_install_state.json"
        if os.path.exists(state_file):
            try:
                import json
                with open(state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._office_install_progress = data
                    return {"success": True, "data": data}
            except Exception:
                pass

        return {"success": True, "data": self._office_install_progress}

    def cancel_office_install(self):
        """Cancels active Office installation process and terminates background runners."""
        state_file = r"C:\ProgramData\BMAT_Tools\OfficeSetup\office_install_state.json"
        try:
            subprocess.run('taskkill /f /im "setup.exe"', shell=True, capture_output=True)
            subprocess.run('powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like \'*install_office_silent.ps1*\' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"', shell=True, capture_output=True)

            self._office_install_progress["active"] = False
            self._office_install_progress["status"] = "cancelled"
            self._office_install_progress["message"] = "Đã hủy tiến trình cài đặt Office."
            if "output_log" in self._office_install_progress:
                self._office_install_progress["output_log"].append("Đã gửi lệnh hủy tiến trình cài đặt Office.")

            if os.path.exists(state_file):
                import json
                with open(state_file, "w", encoding="utf-8") as f:
                    json.dump(self._office_install_progress, f, ensure_ascii=False, indent=2)

            self.log("WARN", "Đã gửi lệnh hủy tiến trình cài đặt Office.")
            return {"success": True, "message": "Đã hủy tiến trình cài đặt Office."}
        except Exception as e:
            return {"success": False, "message": str(e)}


    # ── OTHER SYSTEM TWEAKS (12 TOOL TOGGLES MATCHING IMAGE 2) ─────────────
    def get_system_tweaks_status(self):
        """Returns real-time status of all 12 system tweaks matching Image 2."""
        import winreg

        status = {
            "taskmgr": True,
            "registry": True,
            "run": True,
            "lowdisk": True,
            "cmd": True,
            "camera": True,
            "fix_hidden": True,
            "repair_taskbar": True,
            "unblock_files": True,
            "shortcut_arrow": True,
            "shortcut_prefix": True,
            "autorun": True
        }

        # 1. Task Manager
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System', 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, 'DisableTaskMgr')
            status["taskmgr"] = (val == 0)
            winreg.CloseKey(key)
        except Exception:
            status["taskmgr"] = True

        # 2. Registry Editor
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System', 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, 'DisableRegistryTools')
            status["registry"] = (val == 0)
            winreg.CloseKey(key)
        except Exception:
            status["registry"] = True

        # 3. Run Command
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer', 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, 'NoRun')
            status["run"] = (val == 0)
            winreg.CloseKey(key)
        except Exception:
            status["run"] = True

        # 4. Low Disk Space Checks
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer', 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, 'NoLowDiskSpaceChecks')
            status["lowdisk"] = (val == 0)
            winreg.CloseKey(key)
        except Exception:
            status["lowdisk"] = True

        # 5. Command Prompt
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Policies\Microsoft\Windows\System', 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, 'DisableCMD')
            status["cmd"] = (val == 0)
            winreg.CloseKey(key)
        except Exception:
            status["cmd"] = True

        # 6. Camera
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam', 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, 'Value')
            status["camera"] = (str(val).lower() == 'allow')
            winreg.CloseKey(key)
        except Exception:
            status["camera"] = True

        # 10. Shortcut Arrow
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Icons', 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, '29')
            status["shortcut_arrow"] = False
            winreg.CloseKey(key)
        except Exception:
            status["shortcut_arrow"] = True

        # 11. Shortcut Prefix "Shortcut to"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer', 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, 'link')
            status["shortcut_prefix"] = (val != b'\x00\x00\x00\x00')
            winreg.CloseKey(key)
        except Exception:
            status["shortcut_prefix"] = True

        # 12. Autorun
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer', 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, 'NoDriveTypeAutoRun')
            status["autorun"] = (val != 0xFF)
            winreg.CloseKey(key)
        except Exception:
            status["autorun"] = True

        return {"success": True, "data": status}

    def toggle_system_tweak(self, tweak_key, enable):
        import winreg
        try:
            val = 0 if enable else 1  # 0 = enabled feature, 1 = disabled

            if tweak_key == "taskmgr":
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System')
                winreg.SetValueEx(key, 'DisableTaskMgr', 0, winreg.REG_DWORD, val)
                winreg.CloseKey(key)

            elif tweak_key == "cmd":
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Policies\Microsoft\Windows\System')
                winreg.SetValueEx(key, 'DisableCMD', 0, winreg.REG_DWORD, val)
                winreg.CloseKey(key)

            elif tweak_key == "registry":
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System')
                winreg.SetValueEx(key, 'DisableRegistryTools', 0, winreg.REG_DWORD, val)
                winreg.CloseKey(key)

            elif tweak_key == "run":
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer')
                winreg.SetValueEx(key, 'NoRun', 0, winreg.REG_DWORD, val)
                winreg.CloseKey(key)

            elif tweak_key == "lowdisk":
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer')
                winreg.SetValueEx(key, 'NoLowDiskSpaceChecks', 0, winreg.REG_DWORD, val)
                winreg.CloseKey(key)

            elif tweak_key == "camera":
                cam_val = 'Allow' if enable else 'Deny'
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam')
                winreg.SetValueEx(key, 'Value', 0, winreg.REG_SZ, cam_val)
                winreg.CloseKey(key)

            elif tweak_key == "fix_hidden":
                key1 = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced')
                winreg.SetValueEx(key1, 'Hidden', 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key1, 'ShowSuperHidden', 0, winreg.REG_DWORD, 1)
                winreg.CloseKey(key1)
                key2 = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced\Folder\Hidden\SHOWALL')
                winreg.SetValueEx(key2, 'CheckedValue', 0, winreg.REG_DWORD, 1)
                winreg.CloseKey(key2)
                subprocess.run("taskkill /f /im explorer.exe & start explorer.exe", shell=True, capture_output=True)

            elif tweak_key == "repair_taskbar":
                subprocess.run(r'reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\StuckRects3" /f', shell=True, capture_output=True)
                subprocess.run(r'reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Taskband" /f', shell=True, capture_output=True)
                subprocess.run("taskkill /f /im explorer.exe & start explorer.exe", shell=True, capture_output=True)

            elif tweak_key == "unblock_files":
                ps_unblock = 'Get-ChildItem -Path "$env:USERPROFILE\\Downloads" -Recurse -ErrorAction SilentlyContinue | Unblock-File'
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_unblock], capture_output=True)

            elif tweak_key == "shortcut_arrow":
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Icons')
                if enable:
                    try:
                        winreg.DeleteValue(key, '29')
                    except Exception:
                        pass
                else:
                    winreg.SetValueEx(key, '29', 0, winreg.REG_SZ, '%windir%\\System32\\shell32.dll,-50')
                winreg.CloseKey(key)
                subprocess.run("taskkill /f /im explorer.exe & start explorer.exe", shell=True, capture_output=True)

            elif tweak_key == "shortcut_prefix":
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer')
                link_val = b'\x1e\x00\x00\x00' if enable else b'\x00\x00\x00\x00'
                winreg.SetValueEx(key, 'link', 0, winreg.REG_BINARY, link_val)
                winreg.CloseKey(key)

            elif tweak_key == "autorun":
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer')
                winreg.SetValueEx(key, 'NoDriveTypeAutoRun', 0, winreg.REG_DWORD, 0x91 if enable else 0xFF)
                winreg.CloseKey(key)

            status_str = "Kích hoạt (Enable)" if enable else "Tắt (Disable)"
            self.log("SUCCESS", f"Đã thực hiện {status_str} tính năng: {tweak_key}")
            return {"success": True, "message": f"Đã {status_str} tính năng thành công!"}
        except Exception as e:
            self.log("ERROR", f"Lỗi thực hiện tweak {tweak_key}: {e}")
            return {"success": False, "message": str(e)}


    # ── FREE SOFTWARE STORE (WINGET SILENT INSTALLER) ─────────────────────
    def get_software_catalog(self):
        """Returns verified Winget packages catalog."""
        catalog = [
            # ── TRÌNH DUYỆT (8) ───────────────────────────────────────────
            {"id": "CocCoc.CocCoc",            "name": "Cốc Cốc",            "category": "Trình duyệt",     "icon": "🌐"},
            {"id": "Google.Chrome",             "name": "Google Chrome",       "category": "Trình duyệt",     "icon": "🌐"},
            {"id": "Microsoft.Edge",            "name": "Microsoft Edge",      "category": "Trình duyệt",     "icon": "🌐"},
            {"id": "Mozilla.Firefox",           "name": "Mozilla Firefox",     "category": "Trình duyệt",     "icon": "🦊"},
            {"id": "Brave.Brave",               "name": "Brave Browser",       "category": "Trình duyệt",     "icon": "🦁"},
            {"id": "Opera.Opera",               "name": "Opera",               "category": "Trình duyệt",     "icon": "🔴"},
            {"id": "Opera.OperaGX",             "name": "Opera GX",            "category": "Trình duyệt",     "icon": "🎮"},
            {"id": "Vivaldi.Vivaldi",           "name": "Vivaldi",             "category": "Trình duyệt",     "icon": "🔴"},

            # ── BỘ GÕ TIẾNG VIỆT (3) ──────────────────────────────────────
            {"id": "UniKey.UniKey",             "name": "UniKey",              "category": "Bộ gõ",          "icon": "⌨️"},
            {"id": "EVKeyVN.EVKey",             "name": "EVKey",               "category": "Bộ gõ",          "icon": "⌨️"},
            {"id": "BoGoEngine.IBus-BoGo",      "name": "Bộ Gõ Tiếng Việt WinBoGo", "category": "Bộ gõ",  "icon": "⌨️"},

            # ── GIẢI NÉN (4) ──────────────────────────────────────────────
            {"id": "7zip.7zip",                 "name": "7-Zip",               "category": "Giải nén",       "icon": "📦"},
            {"id": "RARLab.WinRAR",             "name": "WinRAR",              "category": "Giải nén",       "icon": "📚"},
            {"id": "Giorgiotani.Peazip",        "name": "PeaZip",              "category": "Giải nén",       "icon": "🍃"},
            {"id": "Bandisoft.Bandizip",        "name": "Bandizip",            "category": "Giải nén",       "icon": "📦"},

            # ── DOWNLOAD & FTP (6) ────────────────────────────────────────
            {"id": "SoftDeluxe.FreeDownloadManager", "name": "Free Download Manager", "category": "Download", "icon": "⬇️"},
            {"id": "qBittorrent.qBittorrent",   "name": "qBittorrent",         "category": "Download",       "icon": "🧲"},
            {"id": "WinSCP.WinSCP",             "name": "WinSCP",              "category": "Download",       "icon": "🔐"},
            {"id": "PuTTY.PuTTY",               "name": "PuTTY",               "category": "Download",       "icon": "🖥️"},
            {"id": "Tonec.InternetDownloadManager", "name": "IDM (Internet Download Manager)", "category": "Download", "icon": "⬇️"},
            {"id": "FileZilla.FileZilla",       "name": "FileZilla FTP",       "category": "Download",       "icon": "📡"},

            # ── PDF & VĂN BẢN (6) ─────────────────────────────────────────
            {"id": "Foxit.FoxitReader",         "name": "Foxit PDF Reader",    "category": "PDF",            "icon": "📄"},
            {"id": "SumatraPDF.SumatraPDF",     "name": "SumatraPDF",          "category": "PDF",            "icon": "📖"},
            {"id": "geeksoftwareGmbH.PDF24Creator", "name": "PDF24 Creator",   "category": "PDF",            "icon": "📑"},
            {"id": "Adobe.Acrobat.Reader.64-bit", "name": "Adobe Acrobat Reader", "category": "PDF",         "icon": "📄"},
            {"id": "doPDF.doPDF",               "name": "doPDF",               "category": "PDF",            "icon": "🖨️"},
            {"id": "NitroPDF.NitroPDFPro",      "name": "Nitro PDF Reader",    "category": "PDF",            "icon": "📋"},

            # ── FONTS VIỆT NAM (2) ────────────────────────────────────────
            {"id": "FontForge.FontForge",       "name": "FontForge",           "category": "Fonts",          "icon": "🔤"},
            {"id": "NirSoft.NirLauncher",       "name": "NirLauncher (Font Tools)", "category": "Fonts",    "icon": "🔡"},

            # ── CHAT & LIÊN LẠC (9) ───────────────────────────────────────
            {"id": "Tencent.WeChat",            "name": "WeChat PC",           "category": "Chat",           "icon": "💬"},
            {"id": "Telegram.TelegramDesktop",  "name": "Telegram",            "category": "Chat",           "icon": "✈️"},
            {"id": "Zoom.Zoom",                 "name": "Zoom Meetings",       "category": "Chat",           "icon": "📹"},
            {"id": "Discord.Discord",           "name": "Discord",             "category": "Chat",           "icon": "👾"},
            {"id": "SlackTechnologies.Slack",   "name": "Slack",               "category": "Chat",           "icon": "💼"},
            {"id": "Microsoft.Teams",           "name": "Microsoft Teams",     "category": "Chat",           "icon": "👥"},
            {"id": "Skype.Skype",               "name": "Skype",               "category": "Chat",           "icon": "📞"},
            {"id": "Viber.Viber",               "name": "Viber",               "category": "Chat",           "icon": "📱"},
            {"id": "OpenWhatsApp.OpenWhatsApp", "name": "WhatsApp Desktop",    "category": "Chat",           "icon": "💬"},

            # ── VĂN PHÒNG & SOẠN THẢO (10) ───────────────────────────────
            {"id": "TheDocumentFoundation.LibreOffice", "name": "LibreOffice", "category": "Văn phòng",      "icon": "📝"},
            {"id": "Kingsoft.WPSOffice",        "name": "WPS Office",          "category": "Văn phòng",      "icon": "📊"},
            {"id": "Notepad++.Notepad++",       "name": "Notepad++",           "category": "Văn phòng",      "icon": "✏️"},
            {"id": "voidtools.Everything",      "name": "Everything",          "category": "Văn phòng",      "icon": "🔍"},
            {"id": "Microsoft.PowerToys",       "name": "PowerToys",           "category": "Văn phòng",      "icon": "🛠️"},
            {"id": "Listary.Listary",           "name": "Listary",             "category": "Văn phòng",      "icon": "🔎"},
            {"id": "Obsidian.Obsidian",         "name": "Obsidian (Ghi chú)", "category": "Văn phòng",      "icon": "📒"},
            {"id": "Notion.Notion",             "name": "Notion",              "category": "Văn phòng",      "icon": "📘"},
            {"id": "Typora.Typora",             "name": "Typora Markdown",     "category": "Văn phòng",      "icon": "📄"},
            {"id": "Inkscape.Inkscape",         "name": "Inkscape",            "category": "Văn phòng",      "icon": "✒️"},

            # ── ĐA PHƯƠNG TIỆN & ÂM NHẠC (11) ────────────────────────────
            {"id": "VideoLAN.VLC",              "name": "VLC Media Player",    "category": "Đa phương tiện", "icon": "🎥"},
            {"id": "Kakao.PotPlayer",           "name": "PotPlayer",           "category": "Đa phương tiện", "icon": "🎬"},
            {"id": "OBSProject.OBSStudio",      "name": "OBS Studio",          "category": "Đa phương tiện", "icon": "📹"},
            {"id": "GIMP.GIMP",                 "name": "GIMP",                "category": "Đa phương tiện", "icon": "🎨"},
            {"id": "Audacity.Audacity",         "name": "Audacity",            "category": "Đa phương tiện", "icon": "🎙️"},
            {"id": "Spotify.Spotify",           "name": "Spotify",             "category": "Đa phương tiện", "icon": "🎵"},
            {"id": "MPC-BE.MPC-BE",             "name": "MPC-BE Player",       "category": "Đa phương tiện", "icon": "▶️"},
            {"id": "HandBrake.HandBrake",       "name": "HandBrake (Video)",   "category": "Đa phương tiện", "icon": "📼"},
            {"id": "Kdenlive.Kdenlive",         "name": "Kdenlive Video Editor", "category": "Đa phương tiện", "icon": "🎞️"},
            {"id": "DaVinci-Resolve.DaVinci-Resolve", "name": "DaVinci Resolve", "category": "Đa phương tiện", "icon": "🎬"},
            {"id": "ShareX.ShareX",             "name": "ShareX (Screenshot)", "category": "Đa phương tiện", "icon": "📸"},

            # ── TIỆN ÍCH HỆ THỐNG (8) ────────────────────────────────────
            {"id": "AnyDesk.AnyDesk",           "name": "AnyDesk",             "category": "Tiện ích",       "icon": "💻"},
            {"id": "TeamViewer.TeamViewer",     "name": "TeamViewer",          "category": "Tiện ích",       "icon": "🔗"},
            {"id": "DucFabulous.UltraViewer",   "name": "UltraViewer",         "category": "Tiện ích",       "icon": "🖥️"},
            {"id": "Rufus.Rufus",               "name": "Rufus",               "category": "Tiện ích",       "icon": "💾"},
            {"id": "Piriform.CCleaner",         "name": "CCleaner",            "category": "Tiện ích",       "icon": "🧹"},
            {"id": "Microsoft.WindowsTerminal", "name": "Windows Terminal",    "category": "Tiện ích",       "icon": "⬛"},
            {"id": "Greenshot.Greenshot",       "name": "Greenshot",           "category": "Tiện ích",       "icon": "📷"},
            {"id": "NirSoft.BlueScreenView",    "name": "BlueScreenView",      "category": "Tiện ích",       "icon": "🔵"},

            # ── HỆ THỐNG & PHẦN CỨNG (9) ──────────────────────────────────
            {"id": "CPUID.CPU-Z",               "name": "CPU-Z",               "category": "Hệ thống",       "icon": "⚡"},
            {"id": "TechPowerUp.GPU-Z",         "name": "GPU-Z",               "category": "Hệ thống",       "icon": "🎮"},
            {"id": "CrystalDewWorld.CrystalDiskInfo", "name": "CrystalDiskInfo", "category": "Hệ thống",    "icon": "💽"},
            {"id": "REALiX.HWiNFO",             "name": "HWiNFO",              "category": "Hệ thống",       "icon": "ℹ️"},
            {"id": "CPUID.HWMonitor",           "name": "HWMonitor",           "category": "Hệ thống",       "icon": "🌡️"},
            {"id": "MajorGeeks.SpeedFan",       "name": "SpeedFan",            "category": "Hệ thống",       "icon": "💨"},
            {"id": "Piriform.Speccy",           "name": "Speccy",              "category": "Hệ thống",       "icon": "🖥️"},
            {"id": "CrystalDewWorld.CrystalDiskMark", "name": "CrystalDiskMark", "category": "Hệ thống",   "icon": "⏱️"},
            {"id": "WiseCleaner.WiseRegistryCleaner", "name": "Wise Registry Cleaner", "category": "Hệ thống", "icon": "🔧"},

            # ── Ổ ĐĨA ẢO & BACKUP (5) ─────────────────────────────────────
            {"id": "Disc-Tools.DAEMONToolsLite","name": "DAEMON Tools Lite",   "category": "Ổ đĩa ảo",      "icon": "💿"},
            {"id": "WinCDEmu.WinCDEmu",         "name": "WinCDEmu",            "category": "Ổ đĩa ảo",      "icon": "💿"},
            {"id": "Veeam.Agent",               "name": "Veeam Agent Backup",  "category": "Ổ đĩa ảo",      "icon": "💾"},
            {"id": "Macrium.Reflect",            "name": "Macrium Reflect",     "category": "Ổ đĩa ảo",      "icon": "🔄"},
            {"id": "Cobian.CobianBackup",       "name": "Cobian Backup",       "category": "Ổ đĩa ảo",      "icon": "📦"},

            # ── BẢO MẬT & DIỆT VIRUS (8) ─────────────────────────────────
            {"id": "Malwarebytes.Malwarebytes",  "name": "Malwarebytes",        "category": "Bảo mật",        "icon": "🛡️"},
            {"id": "AdGuard.AdGuard",            "name": "AdGuard",             "category": "Bảo mật",        "icon": "🚫"},
            {"id": "ESET.ESET-OnlineScanner",   "name": "ESET Online Scanner",  "category": "Bảo mật",        "icon": "🔍"},
            {"id": "Kaspersky.KasperskySecurityCloud", "name": "Kaspersky Free", "category": "Bảo mật",      "icon": "🛡️"},
            {"id": "BitdefenderSRL.BitdefenderFreeAntivirus", "name": "Bitdefender Free", "category": "Bảo mật", "icon": "🔒"},
            {"id": "Bitwarden.Bitwarden",        "name": "Bitwarden (Password Manager)", "category": "Bảo mật", "icon": "🔑"},
            {"id": "GlassWire.GlassWire",        "name": "GlassWire Firewall",  "category": "Bảo mật",        "icon": "🌐"},
            {"id": "ProtonVPN.ProtonVPN",        "name": "ProtonVPN",           "category": "Bảo mật",        "icon": "🔐"},

            # ── LẬP TRÌNH & DEVTOOLS (14) ──────────────────────────────────
            {"id": "Microsoft.VisualStudioCode", "name": "Visual Studio Code",  "category": "Lập trình",      "icon": "💙"},
            {"id": "JetBrains.Toolbox",         "name": "JetBrains Toolbox",   "category": "Lập trình",      "icon": "🧰"},
            {"id": "Git.Git",                   "name": "Git",                 "category": "Lập trình",      "icon": "🔀"},
            {"id": "Python.Python.3.12",        "name": "Python 3.12",         "category": "Lập trình",      "icon": "🐍"},
            {"id": "OpenJS.NodeJS",             "name": "Node.js",             "category": "Lập trình",      "icon": "🟢"},
            {"id": "Oracle.JDK.21",             "name": "Java JDK 21",         "category": "Lập trình",      "icon": "☕"},
            {"id": "Postman.Postman",           "name": "Postman (API Test)",  "category": "Lập trình",      "icon": "📮"},
            {"id": "DBngin.DBngin",             "name": "HeidiSQL (Database)", "category": "Lập trình",      "icon": "🗄️"},
            {"id": "HeidiSQL.HeidiSQL",         "name": "HeidiSQL",            "category": "Lập trình",      "icon": "🗄️"},
            {"id": "Docker.DockerDesktop",      "name": "Docker Desktop",      "category": "Lập trình",      "icon": "🐳"},
            {"id": "Yarn.Yarn",                 "name": "Yarn",                "category": "Lập trình",      "icon": "🧶"},
            {"id": "GitHub.GitHubDesktop",      "name": "GitHub Desktop",      "category": "Lập trình",      "icon": "🐙"},
            {"id": "Insomnia.Insomnia",         "name": "Insomnia (REST API)", "category": "Lập trình",      "icon": "😴"},
            {"id": "WampServer.WampServer",     "name": "WampServer (PHP/MySQL)", "category": "Lập trình",   "icon": "⚙️"},

            # ── MẠNG XÃ HỘI & GIẢI TRÍ (7) ──────────────────────────────
            {"id": "Valve.Steam",               "name": "Steam",               "category": "Mạng xã hội",    "icon": "🎮"},
            {"id": "EpicGames.EpicGamesLauncher","name": "Epic Games Launcher", "category": "Mạng xã hội",    "icon": "🎮"},
            {"id": "Facebook.Messenger",        "name": "Facebook Messenger",  "category": "Mạng xã hội",    "icon": "💙"},
            {"id": "LINE.LINE",                 "name": "LINE",                "category": "Mạng xã hội",    "icon": "💬"},
            {"id": "TikTok.TikTok",             "name": "TikTok Desktop",      "category": "Mạng xã hội",    "icon": "🎵"},
            {"id": "Tencent.TencentMeeting",    "name": "Tencent Meeting",     "category": "Mạng xã hội",    "icon": "📹"},
            {"id": "NeteaseMusic.CloudMusic",   "name": "Zing MP3 / NetEase",  "category": "Mạng xã hội",    "icon": "🎶"},

            # ── ĐỒ HOẠ & THIẾT KẾ (8) ────────────────────────────────────
            {"id": "Canva.Canva",               "name": "Canva Desktop",       "category": "Đồ hoạ",         "icon": "🎨"},
            {"id": "Figma.Figma",               "name": "Figma",               "category": "Đồ hoạ",         "icon": "✏️"},
            {"id": "KritaFoundation.Krita",     "name": "Krita",               "category": "Đồ hoạ",         "icon": "🖌️"},
            {"id": "BlenderFoundation.Blender", "name": "Blender 3D",          "category": "Đồ hoạ",         "icon": "🌀"},
            {"id": "IrfanView.IrfanView",       "name": "IrfanView",           "category": "Đồ hoạ",         "icon": "🖼️"},
            {"id": "XnSoft.XnView",             "name": "XnView MP",           "category": "Đồ hoạ",         "icon": "🖼️"},
            {"id": "GIMP.GIMP",                 "name": "GIMP",                "category": "Đồ hoạ",         "icon": "🎨"},
            {"id": "Greenshot.Greenshot",       "name": "Greenshot Screen",    "category": "Đồ hoạ",         "icon": "📷"},

            # ── KẾ TOÁN & TÀI CHÍNH (5) ──────────────────────────────────
            {"id": "GnuCash.GnuCash",           "name": "GnuCash Kế Toán",    "category": "Kế toán",        "icon": "💰"},
            {"id": "MoneyManager-Ex.MoneyManagerEx", "name": "Money Manager Ex", "category": "Kế toán",     "icon": "💵"},
            {"id": "HomeBank.HomeBank",         "name": "HomeBank",            "category": "Kế toán",        "icon": "🏦"},
            {"id": "Firefly-III.Firefly-III",   "name": "Firefly III (Quản lý tiền)", "category": "Kế toán","icon": "🔥"},
            {"id": "Microsoft.PowerBI",         "name": "Power BI Desktop",    "category": "Kế toán",        "icon": "📊"},

            # ── CLOUD & LƯU TRỮ (7) ──────────────────────────────────────
            {"id": "Google.GoogleDrive",        "name": "Google Drive",        "category": "Cloud",          "icon": "☁️"},
            {"id": "Dropbox.Dropbox",           "name": "Dropbox",             "category": "Cloud",          "icon": "📦"},
            {"id": "Microsoft.OneDrive",        "name": "OneDrive",            "category": "Cloud",          "icon": "☁️"},
            {"id": "Mega.MEGASync",             "name": "MEGA Sync",           "category": "Cloud",          "icon": "🌊"},
            {"id": "pCloud.pCloud",             "name": "pCloud",              "category": "Cloud",          "icon": "☁️"},
            {"id": "Nextcloud.NextcloudDesktop","name": "Nextcloud Desktop",   "category": "Cloud",          "icon": "🌤️"},
            {"id": "Box.Box",                   "name": "Box Drive",           "category": "Cloud",          "icon": "📫"},

            # ── CÔNG CỤ MẠNG (8) ──────────────────────────────────────────
            {"id": "Wireshark.Wireshark",       "name": "Wireshark",           "category": "Công cụ mạng",   "icon": "🦈"},
            {"id": "OpenVPNTechnologies.OpenVPN","name": "OpenVPN",             "category": "Công cụ mạng",   "icon": "🔒"},
            {"id": "NetScanTools.BasicEdition", "name": "Angry IP Scanner",    "category": "Công cụ mạng",   "icon": "📡"},
            {"id": "Nmap.Nmap",                 "name": "Nmap",                "category": "Công cụ mạng",   "icon": "🔍"},
            {"id": "NordVPN.NordVPN",           "name": "NordVPN",             "category": "Công cụ mạng",   "icon": "🛡️"},
            {"id": "Ookla.Speedtest",           "name": "Speedtest by Ookla",  "category": "Công cụ mạng",   "icon": "⚡"},
            {"id": "Cloudflare.Warp",           "name": "Cloudflare WARP",     "category": "Công cụ mạng",   "icon": "🌐"},
            {"id": "mRemoteNG.mRemoteNG",       "name": "mRemoteNG (RDP/SSH)", "category": "Công cụ mạng",   "icon": "🖥️"},
        ]
        return catalog

    # ── Winget background session paths & helpers ───────────────────────
    def _is_pid_alive(self, pid):
        """Checks if a Windows process PID is currently running using kernel32."""
        if not pid or pid <= 0:
            return False
        try:
            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
            if not handle:
                return False
            exit_code = ctypes.c_ulong()
            res = kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            kernel32.CloseHandle(handle)
            return bool(res != 0 and exit_code.value == STILL_ACTIVE)
        except Exception:
            return False

    def _write_json_atomic(self, file_path, data):
        """Atomically writes JSON to file_path to prevent file locking & partial reads."""
        tmp_file = f"{file_path}.tmp"
        try:
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            if os.path.exists(file_path):
                os.replace(tmp_file, file_path)
            else:
                os.rename(tmp_file, file_path)
            return True
        except Exception as e:
            self.log("WARN", f"Không thể ghi atomic {file_path}: {e}")
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return True
            except Exception:
                return False

    def _get_winget_session_paths(self):
        """Returns paths for queue, status, and cancel files used by winget_runner.ps1."""
        tmp = os.environ.get("TEMP", os.environ.get("TMP", os.path.expanduser("~")))
        base = os.path.join(tmp, "bmat_winget")
        os.makedirs(base, exist_ok=True)
        return {
            "queue":  os.path.join(base, "queue.json"),
            "status": os.path.join(base, "status.json"),
            "cancel": os.path.join(base, "status.cancel"),
            "ps1":    os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules", "winget_runner.ps1")
        }

    def get_winget_install_status(self):
        """Returns real-time winget batch installation status with PID liveness validation."""
        paths = self._get_winget_session_paths()
        status_file = paths["status"]

        idle_status = {
            "state":                "idle",
            "pid":                  0,
            "is_running":           False,
            "finished":             True,
            "canceled":             False,
            "current_index":        0,
            "total":                0,
            "current_package_id":   "",
            "current_package_name": "",
            "success_count":        0,
            "error_count":          0,
            "status_text":          "Sẵn sàng",
            "percentage":           0,
            "log":                  []
        }

        if not os.path.exists(status_file):
            return idle_status

        data = None
        for _ in range(4):
            try:
                with open(status_file, "r", encoding="utf-8-sig") as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        break
            except Exception:
                time.sleep(0.04)

        if data is None:
            if self._last_winget_status is not None:
                return self._last_winget_status
            return idle_status

        is_running = bool(data.get("is_running", False))
        finished   = bool(data.get("finished", False))
        canceled   = bool(data.get("canceled", False))
        pid        = int(data.get("pid", 0)) or (self._current_winget_pid or 0)

        # DEAD PROCESS DETECTION: If marked running but PID is dead, finalize status
        if is_running and not finished:
            if pid > 0 and not self._is_pid_alive(pid):
                self.log("WARN", f"Tiến trình cài đặt nền (PID {pid}) đã kết thúc.")
                is_running = False
                finished = True
                data["is_running"] = False
                data["finished"] = True
                if not data.get("status_text") or "Đang" in str(data.get("status_text", "")):
                    data["status_text"] = "Tiến trình cài đặt nền đã hoàn tất hoặc kết thúc."
                self._write_json_atomic(status_file, data)

        state = "running" if (is_running and not finished) else ("canceled" if canceled else ("completed" if finished else "idle"))

        result = {
            "state":                state,
            "pid":                  pid,
            "is_running":           is_running,
            "current_index":        int(data.get("current_index", 0)),
            "total":                int(data.get("total", 0)),
            "current_package_id":   str(data.get("current_package_id", "")),
            "current_package_name": str(data.get("current_package_name", "")),
            "success_count":        int(data.get("success_count", 0)),
            "error_count":          int(data.get("error_count", 0)),
            "status_text":          str(data.get("status_text", "Đang xử lý...")),
            "percentage":           int(data.get("percentage", 0)),
            "finished":             finished,
            "canceled":             canceled,
            "log":                  list(data.get("log", []))
        }
        self._last_winget_status = result
        return result

    def check_bg_winget_session(self):
        """Checks whether a background winget installation session is already running."""
        st = self.get_winget_install_status()
        if st.get("is_running") and not st.get("finished"):
            return {
                "has_session": True,
                "total":       st.get("total", 0),
                "status_text": st.get("status_text", "Đang cài đặt nền...")
            }
        return {"has_session": False}

    def cancel_winget_batch(self):
        """Cancels the ongoing background winget installation."""
        paths = self._get_winget_session_paths()
        try:
            with open(paths["cancel"], "w", encoding="utf-8") as f:
                f.write("cancel")
            self.log("WARNING", "Đã gửi lệnh dừng quá trình cài đặt phần mềm nền.")
            if self._last_winget_status and self._last_winget_status.get("is_running"):
                self._last_winget_status["status_text"] = "Đang dừng... (sẽ kết thúc sau gói hiện tại)"
        except Exception as e:
            self.log("ERROR", f"Không thể ghi file cancel: {e}")
        return {"success": True, "message": "Đã gửi tín hiệu dừng cài đặt. Tiến trình sẽ dừng sau gói hiện tại."}

    def _append_to_winget_queue(self, package_ids):
        """Appends new package IDs to an actively running winget background queue."""
        paths = self._get_winget_session_paths()
        if not os.path.exists(paths["queue"]):
            return {"success": False, "message": "Không tìm thấy file hàng đợi hiện tại!"}

        try:
            with open(paths["queue"], "r", encoding="utf-8-sig") as f:
                queue_data = json.load(f)
        except Exception as e:
            return {"success": False, "message": f"Không thể đọc hàng đợi: {e}"}

        existing_ids = queue_data.get("package_ids", [])
        new_ids = [pid for pid in package_ids if pid not in existing_ids]

        if not new_ids:
            return {
                "success": True,
                "appended": 0,
                "message": "Các phần mềm được chọn đã có trong tiến trình cài đặt!"
            }

        # Update catalog map for new packages
        catalog_map = queue_data.get("catalog_map", {})
        all_catalog = {item["id"]: item["name"] for item in self.get_software_catalog()}
        for pid in new_ids:
            if pid in all_catalog:
                catalog_map[pid] = all_catalog[pid]

        existing_ids.extend(new_ids)
        queue_data["package_ids"] = existing_ids
        queue_data["catalog_map"] = catalog_map

        # Write updated queue atomically
        self._write_json_atomic(paths["queue"], queue_data)

        # Update status file with new total so progress displays correctly
        new_total = len(existing_ids)
        cur_status = self.get_winget_install_status()
        if cur_status:
            cur_status["total"] = new_total
            self._write_json_atomic(paths["status"], cur_status)

        names_list = [catalog_map.get(pid, pid) for pid in new_ids]
        names_str = ", ".join(names_list[:3])
        if len(names_list) > 3:
            names_str += f" và {len(names_list) - 3} phần mềm khác"

        self.log("INFO", f"Đã thêm {len(new_ids)} phần mềm ({names_str}) vào tiến trình cài đặt nền. Tổng cộng: {new_total} phần mềm.")

        return {
            "success": True,
            "appended": len(new_ids),
            "total": new_total,
            "message": f"Đã thêm {len(new_ids)} phần mềm ({names_str}) vào tiến trình cài đặt đang chạy!"
        }

    def install_winget_batch(self, package_ids):
        """Launches winget_runner.ps1 as a detached background process with real PID tracking.
        If a session is already running, seamlessly appends newly selected packages to the active queue."""
        if not package_ids:
            return {"success": False, "message": "Chưa chọn phần mềm nào để cài đặt!"}

        paths = self._get_winget_session_paths()

        # If a session is already actively running, seamlessly append to the queue!
        cur_status = self.get_winget_install_status()
        if cur_status.get("is_running") and not cur_status.get("finished"):
            return self._append_to_winget_queue(package_ids)

        # Clean up stale session files
        for fpath in [paths["cancel"], paths["queue"]]:
            try:
                if os.path.exists(fpath):
                    os.remove(fpath)
            except Exception:
                pass

        # Build catalog map for human-readable package names
        catalog_map = {item["id"]: item["name"] for item in self.get_software_catalog()}
        queue_payload = {
            "package_ids": package_ids,
            "catalog_map": catalog_map
        }
        if not self._write_json_atomic(paths["queue"], queue_payload):
            return {"success": False, "message": "Không thể tạo file hàng đợi cài đặt!"}

        # Launch detached PowerShell process directly (without shell=True to preserve exact PID & args)
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        CREATE_NO_WINDOW         = 0x08000000
        si = subprocess.STARTUPINFO()
        si.dwFlags     = subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE

        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-WindowStyle", "Hidden",
            "-File", paths["ps1"],
            "-QueueFile", paths["queue"],
            "-StatusFile", paths["status"]
        ]

        try:
            proc = subprocess.Popen(
                cmd,
                shell         = False,
                stdin         = subprocess.DEVNULL,
                stdout        = subprocess.DEVNULL,
                stderr        = subprocess.DEVNULL,
                startupinfo   = si,
                creationflags = CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
            )
            self._current_winget_pid = proc.pid

            # Write initial status immediately so any concurrent poll gets valid state
            initial_status = {
                "pid":                  proc.pid,
                "is_running":           True,
                "finished":             False,
                "canceled":             False,
                "status_text":          f"Đang chuẩn bị cài đặt {len(package_ids)} phần mềm...",
                "percentage":           2,
                "current_index":        0,
                "total":                len(package_ids),
                "current_package_id":   "",
                "current_package_name": "",
                "success_count":        0,
                "error_count":          0,
                "log":                  []
            }
            self._write_json_atomic(paths["status"], initial_status)
            self._last_winget_status = initial_status

            self.log("INFO", f"Đã khởi chạy cài đặt nền {len(package_ids)} phần mềm (PID: {proc.pid}).")
            return {
                "success": True,
                "message": f"Đã bắt đầu cài đặt nền {len(package_ids)} phần mềm. Quá trình vẫn tiếp tục kể cả khi đóng ứng dụng!"
            }
        except Exception as e:
            self.log("ERROR", f"Không thể khởi chạy winget_runner.ps1: {e}")
            return {"success": False, "message": f"Lỗi khởi động tiến trình nền: {e}"}


    # ── IP NETWORK SCANNER ───────────────────────────────────────────────
    def get_ip_scanner_default_range(self):
        try:
            import modules.ip_scanner as ip_scanner
            return ip_scanner.get_local_subnet_range()
        except Exception as e:
            self.log("ERROR", f"Lỗi lấy dải mạng mặc định: {e}")
            return {"local_ip": "192.168.1.100", "subnet": "192.168.1.0/24", "start_ip": "192.168.1.1", "end_ip": "192.168.1.254"}

    def scan_ip_range(self, subnet_str="", ip_start="", ip_end="", check_ping=True, check_hostname=True, check_mac=True, check_http_port=True, check_https_port=True, max_threads=50):
        try:
            import modules.ip_scanner as ip_scanner
            self.log("INFO", f"Đang bắt đầu quét dải IP LAN (Threads: {max_threads})...")
            res = ip_scanner.scan_lan_network(
                subnet_str=subnet_str,
                ip_start=ip_start,
                ip_end=ip_end,
                check_ping=check_ping,
                check_hostname=check_hostname,
                check_mac=check_mac,
                check_http_port=check_http_port,
                check_https_port=check_https_port,
                max_threads=max_threads
            )
            self.log("SUCCESS", f"Hoàn tất quét LAN! Tìm thấy {len(res)} thiết bị online.")
            return {"success": True, "results": res, "total": len(res)}
        except Exception as e:
            self.log("ERROR", f"Lỗi quét IP Scanner: {e}")
            return {"success": False, "message": str(e), "results": []}

    # ── CLASSIC CONTEXT MENU (WIN10 / WIN11 RIGHT-CLICK MENU) ──────────────
    def get_classic_menu_status(self):
        """Checks if Classic Win10 Right-Click Context Menu is enabled via HKCU Registry."""
        import winreg
        reg_path = r'Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32'
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path)
            winreg.CloseKey(key)
            return {
                "success": True,
                "enabled": True,
                "mode": "classic",
                "status_text": "BẬT: Menu Chuột Phải Classic Win 10",
                "badge_text": "🟢 Classic Win10 Active",
                "badge_color": "green",
                "description": "Hiện đang áp dụng giao diện Menu Chuột Phải kiểu Windows 10 cổ điển (hiển thị đầy đủ tất cả menu tác vụ ngay lần click đầu tiên mà không cần bấm 'Show more options')."
            }
        except Exception:
            return {
                "success": True,
                "enabled": False,
                "mode": "win11",
                "status_text": "TẮT: Menu Chuột Phải Win 11 Mặc Định",
                "badge_text": "⚪ Win11 Default Active",
                "badge_color": "slate",
                "description": "Hiện đang áp dụng giao diện Menu Chuột Phải Windows 11 mặc định (giao diện bo tròn, thu gọn bớt menu phụ vào nút 'Show more options' hoặc phím Shift+F10)."
            }

    def set_classic_menu_status(self, enable=True):
        """Enables or disables Classic Win10 Context Menu and restarts Windows Explorer."""
        try:
            reg_key_clsid = r'HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}'
            reg_key_inproc = rf'{reg_key_clsid}\InprocServer32'

            if enable:
                cmd = f'reg add "{reg_key_inproc}" /f /ve'
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if r.returncode == 0:
                    subprocess.run('taskkill /f /im explorer.exe & start explorer.exe', shell=True)
                    self.log("SUCCESS", "Đã bật Menu Chuột Phải Classic Win 10 và làm mới Windows Explorer!")
                    return {
                        "success": True,
                        "enabled": True,
                        "message": "Đã bật Menu Chuột Phải Classic Windows 10 thành công! Windows Explorer đã được làm mới."
                    }
                else:
                    return {"success": False, "message": f"Lỗi ghi Registry: {r.stderr.strip()}"}
            else:
                cmd = f'reg delete "{reg_key_clsid}" /f'
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                subprocess.run('taskkill /f /im explorer.exe & start explorer.exe', shell=True)
                self.log("SUCCESS", "Đã khôi phục Menu Chuột Phải Windows 11 mặc định và làm mới Windows Explorer!")
                return {
                    "success": True,
                    "enabled": False,
                    "message": "Đã khôi phục Menu Chuột Phải Windows 11 Mặc Định thành công! Windows Explorer đã được làm mới."
                }
        except Exception as e:
            self.log("ERROR", f"Lỗi cấu hình Classic Context Menu: {e}")
            return {"success": False, "message": str(e)}

    def restart_explorer_process(self):
        """Restarts Windows Explorer process."""
        try:
            subprocess.run('taskkill /f /im explorer.exe & start explorer.exe', shell=True)
            self.log("SUCCESS", "Đã khởi động lại Windows Explorer!")
            return {"success": True, "message": "Đã khởi động lại Windows Explorer thành công!"}
        except Exception as e:
            self.log("ERROR", f"Lỗi restart Explorer: {e}")
            return {"success": False, "message": str(e)}

    # ── SYSTEM DRIVER BACKUP & RESTORE ────────────────────────────────────
    def get_installed_drivers(self):
        """Fetches all installed OEM drivers via PowerShell Get-WindowsDriver."""
        try:
            cmd = ['powershell', '-Command', 'Get-WindowsDriver -Online | Select-Object ProviderName, Driver, ClassDescription, Version, Date | ConvertTo-Json']
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60, encoding='utf-8', errors='ignore')
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                if isinstance(data, dict):
                    data = [data]
                cleaned = []
                for d in data:
                    raw_date = d.get("Date", "")
                    clean_date = ""
                    if "/Date(" in str(raw_date):
                        try:
                            ts = int(str(raw_date).split("(")[1].split(")")[0]) / 1000
                            clean_date = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                        except Exception:
                            clean_date = str(raw_date)
                    else:
                        clean_date = str(raw_date)
                    cleaned.append({
                        "provider": d.get("ProviderName") or "Unknown",
                        "driver": d.get("Driver") or "-",
                        "class": d.get("ClassDescription") or "-",
                        "version": d.get("Version") or "-",
                        "date": clean_date
                    })
                return {"success": True, "drivers": cleaned, "total": len(cleaned)}
            return {"success": True, "drivers": [], "total": 0}
        except Exception as e:
            self.log("ERROR", f"Lỗi lấy danh sách Driver: {e}")
            return {"success": False, "message": str(e), "drivers": [], "total": 0}

    def select_folder_dialog(self, title="Chọn thư mục"):
        """Opens native Windows folder picker dialog."""
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            folder = filedialog.askdirectory(title=title)
            root.destroy()
            return {"success": True, "folder": folder}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_driver_progress(self):
        """Returns real-time progress of ongoing driver backup or restore task."""
        return getattr(self, "_driver_progress", {
            "active": False,
            "mode": "backup",
            "status": "idle",
            "current": 0,
            "total": 0,
            "percentage": 0,
            "message": "",
            "path": ""
        })

    def start_backup_drivers_async(self, target_dir=""):
        """Starts asynchronous background driver backup with real-time progress tracking."""
        if not target_dir:
            res_dlg = self.select_folder_dialog("Chọn thư mục lưu trữ Backup Driver")
            target_dir = res_dlg.get("folder")
            if not target_dir:
                return {"success": False, "message": "Bạn đã hủy chọn thư mục sao lưu."}

        os.makedirs(target_dir, exist_ok=True)
        
        drivers_res = self.get_installed_drivers()
        total_count = drivers_res.get("total", 30) or 30

        self._driver_progress = {
            "active": True,
            "mode": "backup",
            "status": "running",
            "current": 0,
            "total": total_count,
            "percentage": 0,
            "message": f"Đang chuẩn bị xuất {total_count} driver ra {target_dir}...",
            "path": target_dir
        }

        def worker():
            try:
                self.log("INFO", f"Đang tiến hành xuất toàn bộ Driver hệ thống ra: {target_dir}...")
                proc = subprocess.Popen(
                    f'dism /Online /Export-Driver /Destination:"{target_dir}"',
                    shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore'
                )

                while proc.poll() is None:
                    try:
                        curr_files = len(os.listdir(target_dir)) if os.path.exists(target_dir) else 0
                        pct = min(99, int((curr_files / max(1, total_count)) * 100))
                        self._driver_progress["current"] = curr_files
                        self._driver_progress["percentage"] = pct
                        self._driver_progress["message"] = f"Đã xuất {curr_files}/{total_count} thư mục driver vào {target_dir}..."
                    except Exception:
                        pass
                    import time
                    time.sleep(0.3)

                proc.wait()
                final_count = len(os.listdir(target_dir)) if os.path.exists(target_dir) else total_count
                self._driver_progress["current"] = final_count
                self._driver_progress["total"] = final_count
                self._driver_progress["percentage"] = 100
                self._driver_progress["status"] = "completed"
                self._driver_progress["message"] = f"Hoàn tất sao lưu toàn bộ {final_count} driver vào {target_dir}!"
                self.log("SUCCESS", f"Hoàn tất sao lưu driver ({final_count} mục) ra {target_dir}")
            except Exception as ex:
                self._driver_progress["status"] = "error"
                self._driver_progress["message"] = f"Lỗi sao lưu Driver: {ex}"
                self.log("ERROR", f"Lỗi sao lưu Driver async: {ex}")

        threading.Thread(target=worker, daemon=True).start()
        return {"success": True, "message": f"Đã bắt đầu sao lưu Driver vào:\n{target_dir}", "path": target_dir}

    def start_restore_drivers_async(self, src_dir=""):
        """Starts asynchronous background driver restore with real-time progress tracking."""
        if not src_dir:
            res_dlg = self.select_folder_dialog("Chọn thư mục chứa Driver đã Sao Lưu")
            src_dir = res_dlg.get("folder")
            if not src_dir:
                return {"success": False, "message": "Bạn đã hủy chọn thư mục phục hồi."}

        if not os.path.exists(src_dir):
            return {"success": False, "message": "Thư mục chọn không tồn tại!"}

        inf_files = []
        for root_path, dirs, files in os.walk(src_dir):
            for f in files:
                if f.lower().endswith('.inf'):
                    inf_files.append(os.path.join(root_path, f))

        total_inf_count = len(inf_files) or 1

        self._driver_progress = {
            "active": True,
            "mode": "restore",
            "status": "running",
            "current": 0,
            "total": total_inf_count,
            "percentage": 0,
            "message": f"Đang chuẩn bị nạp {total_inf_count} file driver từ {src_dir}...",
            "path": src_dir
        }

        def worker():
            try:
                self.log("INFO", f"Đang tiến hành nạp & cài đặt {total_inf_count} Driver từ: {src_dir}...")
                proc = subprocess.Popen(
                    f'pnputil /add-driver "{src_dir}\\*.inf" /subdirs /install',
                    shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='ignore'
                )

                count = 0
                for line in proc.stdout:
                    line_str = line.strip()
                    if line_str and ("Adding driver" in line_str or "Driver package" in line_str or ".inf" in line_str.lower()):
                        if ".inf" in line_str.lower():
                            count += 1
                        pct = min(99, int((count / max(1, total_inf_count)) * 100))
                        self._driver_progress["current"] = min(count, total_inf_count)
                        self._driver_progress["percentage"] = pct
                        self._driver_progress["message"] = f"Đang nạp & cài đặt: {line_str[:70]}..."

                proc.wait()
                self._driver_progress["current"] = total_inf_count
                self._driver_progress["percentage"] = 100
                self._driver_progress["status"] = "completed"
                self._driver_progress["message"] = f"Hoàn tất nạp & cài đặt thành công tất cả driver từ {src_dir}!"
                self.log("SUCCESS", f"Đã phục hồi xong driver từ {src_dir}")
            except Exception as ex:
                self._driver_progress["status"] = "error"
                self._driver_progress["message"] = f"Lỗi phục hồi Driver: {ex}"
                self.log("ERROR", f"Lỗi phục hồi Driver async: {ex}")

        threading.Thread(target=worker, daemon=True).start()
        return {"success": True, "message": f"Đã bắt đầu nạp Driver từ:\n{src_dir}", "path": src_dir}

    def backup_drivers(self, target_dir=""):
        return self.start_backup_drivers_async(target_dir)

    def restore_drivers(self, src_dir=""):
        return self.start_restore_drivers_async(src_dir)

    def open_folder_explorer(self, folder_path=""):
        try:
            path = folder_path or r"C:\Driver_Backup"
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
            subprocess.run(f'explorer.exe "{path}"', shell=True)
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}


    # ── WINDOWS SERVICES MANAGER ──────────────────────────────────────────
    def get_windows_services(self):
        """Fetches all Windows services via PowerShell Get-Service."""
        try:
            cmd = ['powershell', '-Command', 'Get-Service | Select-Object Name, DisplayName, Status, StartType | ConvertTo-Json']
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore')
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                if isinstance(data, dict):
                    data = [data]
                
                status_map = {4: "Running", 1: "Stopped", 2: "StartPending", 3: "StopPending", 7: "Paused"}
                start_type_map = {2: "Automatic", 3: "Manual", 4: "Disabled"}

                cleaned = []
                for s in data:
                    st_val = s.get("Status")
                    status_str = status_map.get(st_val, str(st_val)) if isinstance(st_val, int) else str(st_val)

                    sp_val = s.get("StartType")
                    start_str = start_type_map.get(sp_val, str(sp_val)) if isinstance(sp_val, int) else str(sp_val)

                    cleaned.append({
                        "name": s.get("Name") or "",
                        "display": s.get("DisplayName") or "",
                        "status": status_str,
                        "start_type": start_str
                    })

                cleaned.sort(key=lambda x: x["name"].lower())
                return {"success": True, "services": cleaned, "total": len(cleaned)}
            return {"success": True, "services": [], "total": 0}
        except Exception as e:
            self.log("ERROR", f"Lỗi lấy danh sách Windows Services: {e}")
            return {"success": False, "message": str(e), "services": [], "total": 0}

    def manage_windows_service(self, service_name, action):
        """Starts, Stops, or Restarts a Windows service."""
        if not service_name:
            return {"success": False, "message": "Chưa chọn dịch vụ!"}

        try:
            action_map = {
                "start": f'sc start "{service_name}"',
                "stop": f'sc stop "{service_name}"',
                "restart": f'sc stop "{service_name}" & timeout /t 2 & sc start "{service_name}"'
            }
            cmd = action_map.get(action.lower())
            if not cmd:
                return {"success": False, "message": "Thao tác không hợp lệ!"}

            self.log("INFO", f"Đang thực hiện {action} trên dịch vụ: {service_name}...")
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')

            if res.returncode == 0 or "SUCCESS" in res.stdout.upper() or "PENDING" in res.stdout.upper():
                self.log("SUCCESS", f"Đã thực hiện {action} thành công trên dịch vụ '{service_name}'!")
                return {"success": True, "message": f"Đã thực hiện {action} thành công trên dịch vụ '{service_name}'!"}
            else:
                alt_cmd = f'net {action} "{service_name}"' if action in ["start", "stop"] else None
                if alt_cmd:
                    r_alt = subprocess.run(alt_cmd, shell=True, capture_output=True, text=True)
                    if r_alt.returncode == 0:
                        self.log("SUCCESS", f"Đã {action} dịch vụ '{service_name}' thành công!")
                        return {"success": True, "message": f"Đã {action} dịch vụ '{service_name}' thành công!"}

                return {"success": False, "message": f"Lỗi thực thi dịch vụ {service_name}: {res.stderr.strip() or res.stdout.strip()}"}
        except Exception as e:
            self.log("ERROR", f"Lỗi quản lý dịch vụ {service_name}: {e}")
            return {"success": False, "message": str(e)}

    def set_service_startup_type(self, service_name, startup_type):
        """Sets startup type for a Windows service (auto, demand/manual, disabled)."""
        if not service_name or not startup_type:
            return {"success": False, "message": "Thông tin không đầy đủ!"}

        try:
            sc_type = "auto"
            if "manual" in startup_type.lower() or "demand" in startup_type.lower():
                sc_type = "demand"
            elif "disabled" in startup_type.lower():
                sc_type = "disabled"
            elif "auto" in startup_type.lower():
                sc_type = "auto"

            cmd = f'sc config "{service_name}" start= {sc_type}'
            self.log("INFO", f"Đang thay đổi kiểu khởi động {service_name} sang '{sc_type}'...")
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')

            if res.returncode == 0 or "SUCCESS" in res.stdout.upper():
                self.log("SUCCESS", f"Đã thay đổi kiểu khởi động dịch vụ '{service_name}' sang {sc_type} thành công!")
                return {"success": True, "message": f"Đã thay đổi kiểu khởi động dịch vụ '{service_name}' sang {sc_type} thành công!"}
            else:
                return {"success": False, "message": f"Lỗi đổi kiểu khởi động (cần quyền Admin): {res.stderr.strip() or res.stdout.strip()}"}
        except Exception as e:
            self.log("ERROR", f"Lỗi set startup type {service_name}: {e}")
            return {"success": False, "message": str(e)}

    def open_services_msc(self):
        """Opens native Windows Services MMC console."""
        try:
            subprocess.Popen("services.msc", shell=True)
            self.log("SUCCESS", "Đã mở trình quản lý Services.msc của Windows!")
            return {"success": True, "message": "Đã mở Services.msc thành công!"}
        except Exception as e:
            self.log("ERROR", f"Lỗi mở services.msc: {e}")
            return {"success": False, "message": str(e)}

    # ── SERVER TOOLS HANDLERS ─────────────────────────────────────────────
    def get_nic_teams(self):
        import modules.server_tools as st
        return st.get_nic_teams()

    def create_nic_team(self, name, adapters, mode="SwitchIndependent"):
        import modules.server_tools as st
        res = st.create_nic_team(name, adapters, mode)
        if res.get("success"):
            self.log("SUCCESS", res.get("message"))
        else:
            self.log("ERROR", res.get("message"))
        return res

    def remove_nic_team(self, name):
        import modules.server_tools as st
        res = st.remove_nic_team(name)
        if res.get("success"):
            self.log("SUCCESS", res.get("message"))
        else:
            self.log("ERROR", res.get("message"))
        return res

    def backup_dhcp_server(self, server="localhost", dest_path=""):
        import modules.server_tools as st
        res = st.backup_dhcp(server, dest_path)
        if res.get("success"):
            self.log("SUCCESS", res.get("message"))
        else:
            self.log("ERROR", res.get("message"))
        return res

    def restore_dhcp_server(self, server="localhost", source_path=""):
        import modules.server_tools as st
        res = st.restore_dhcp(server, source_path)
        if res.get("success"):
            self.log("SUCCESS", res.get("message"))
        else:
            self.log("ERROR", res.get("message"))
        return res

    def export_dhcp_leases(self, server="localhost", save_path=""):
        import modules.server_tools as st
        res = st.export_dhcp_leases(server, save_path)
        if res.get("success"):
            self.log("SUCCESS", res.get("message"))
        else:
            self.log("ERROR", res.get("message"))
        return res

    def get_ad_domain_info(self):
        import modules.server_tools as st
        return st.get_ad_info()

    def export_ad_users(self, save_path=""):
        import modules.server_tools as st
        res = st.export_ad_users(save_path)
        if res.get("success"):
            self.log("SUCCESS", res.get("message"))
        else:
            self.log("ERROR", res.get("message"))
        return res

    def connect_iscsi_target(self, ip, port="3260"):
        import modules.server_tools as st
        res = st.connect_iscsi_target(ip, port)
        if res.get("success"):
            self.log("SUCCESS", res.get("message"))
        else:
            self.log("ERROR", res.get("message"))
        return res

    def list_iscsi_targets(self):
        import modules.server_tools as st
        return st.list_iscsi_targets()

    def open_iscsi_cpl(self):
        import modules.server_tools as st
        res = st.open_iscsi_cpl()
        if res.get("success"):
            self.log("SUCCESS", res.get("message"))
        return res

    def open_server_tools_gui(self):
        import modules.server_tools as st
        res = st.open_server_tools_gui()
        if res.get("success"):
            self.log("SUCCESS", res.get("message"))
        return res

    # ── BOOT MANAGER HANDLERS ─────────────────────────────────────────────
    def get_boot_entries(self):
        import modules.boot_manager as bm
        entries, default_guid, timeout_val = bm.get_boot_entries()
        return {
            "success": True,
            "entries": entries,
            "default_guid": default_guid,
            "timeout": timeout_val
        }

    def add_wim_boot_entry(self, wim_path, boot_name="WinPE Boot"):
        import modules.boot_manager as bm
        res = bm.add_wim_boot_entry(wim_path, boot_name)
        if res.get("success"):
            self.log("SUCCESS", res.get("message"))
        else:
            self.log("ERROR", res.get("message"))
        return res

    def delete_boot_entry(self, guid):
        import modules.boot_manager as bm
        res = bm.delete_boot_entry(guid)
        if res.get("success"):
            self.log("SUCCESS", res.get("message"))
        else:
            self.log("ERROR", res.get("message"))
        return res

    def set_default_boot(self, guid):
        import modules.boot_manager as bm
        res = bm.set_default_boot(guid)
        if res.get("success"):
            self.log("SUCCESS", res.get("message"))
        else:
            self.log("ERROR", res.get("message"))
        return res

    def set_boot_timeout(self, seconds):
        import modules.boot_manager as bm
        res = bm.set_boot_timeout(seconds)
        if res.get("success"):
            self.log("SUCCESS", res.get("message"))
        else:
            self.log("ERROR", res.get("message"))
        return res

    def update_boot_name(self, guid, new_name):
        import modules.boot_manager as bm
        res = bm.update_boot_name(guid, new_name)
        if res.get("success"):
            self.log("SUCCESS", res.get("message"))
        else:
            self.log("ERROR", res.get("message"))
        return res

    def open_boot_manager_gui(self):
        import modules.boot_manager as bm
        res = bm.open_boot_manager_gui()
        if res.get("success"):
            self.log("SUCCESS", res.get("message"))
        return res

    def browse_wim_file(self):
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            file_path = filedialog.askopenfilename(
                title='Chọn file WinPE WIM (*.wim)',
                filetypes=[('WIM Files', '*.wim'), ('All Files', '*.*')]
            )
            root.destroy()
            if file_path:
                return {"success": True, "file_path": file_path}
            return {"success": False, "file_path": ""}
        except Exception as e:
            return {"success": False, "message": str(e), "file_path": ""}

    def open_external_url(self, url):
        """Opens specified web URL in user's default browser."""
        import webbrowser
        try:
            webbrowser.open(url)
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def open_website(self):
        """Opens the author's website in the default browser."""
        import webbrowser
        webbrowser.open(APP_WEBSITE)
        return {"success": True}

    def get_logs(self):
        return self._logs

    def clear_logs(self):
        self._logs = []
        return {"success": True}
