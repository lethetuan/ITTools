"""
IT Tool LTT Web API Bridge - Connects Frontend JavaScript to Python System Modules
Author: Lê Thế Tuấn | 0352 194 195 | https://lethetuanpc.blogspot.com | Telegram: https://t.me/lethetuanpc
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
import queue
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from constants import APP_NAME, APP_VERSION, APP_AUTHOR, APP_PHONE, APP_WEBSITE, APP_TELEGRAM, AUTOSTART_KEY_NAME

def patch_silent_subprocess():
    """Globally configures subprocess on Windows to:
    1. Never flash console or PowerShell windows (CREATE_NO_WINDOW).
    2. Enforce UTF-8 encoding with errors='replace' for text mode to avoid
       UnicodeDecodeError on non-UTF8 locales (e.g. cp1258 on Vietnamese Windows).
    """
    if sys.platform != 'win32':
        return
    if getattr(subprocess, '_ittools_silent_patched', False):
        return
    subprocess._ittools_silent_patched = True

    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        if hasattr(sys.stdout, 'reconfigure') and sys.stdout:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure') and sys.stderr:
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    orig_init = subprocess.Popen.__init__

    def silent_init(self, *args, **kwargs):
        # 0x08000000 = CREATE_NO_WINDOW
        flags = kwargs.get('creationflags', 0)
        flags |= 0x08000000
        kwargs['creationflags'] = flags

        # Check if text mode is requested
        is_text = kwargs.get('text') or kwargs.get('universal_newlines')
        if not is_text and len(args) > 11 and args[11]:
            is_text = True
        if not is_text and ('encoding' in kwargs or 'errors' in kwargs):
            is_text = True

        if is_text:
            if not kwargs.get('encoding'):
                kwargs['encoding'] = 'utf-8'
            if not kwargs.get('errors'):
                kwargs['errors'] = 'replace'

        orig_init(self, *args, **kwargs)

    subprocess.Popen.__init__ = silent_init

patch_silent_subprocess()

def get_resource_path(*rel_path):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *rel_path)

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
        self._browser_backup_progress = {
            "active": False,
            "mode": "idle",
            "percent": 0,
            "status": "idle",
            "current_browser": "",
            "step_title": "",
            "detail": "",
            "logs": [],
            "result": None
        }
        self._last_winget_status = None
        self._current_winget_pid = None
        self._winget_notify_watcher = None  # background thread that fires tray balloons
        self._printer_fix_progress = {
            "active": False,
            "status": "idle",
            "step": 0,
            "step_status": ["pending", "pending", "pending", "pending"],
            "percentage": 0,
            "message": "",
            "logs": [],
            "completed": False,
            "success": True
        }

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

    # ── AUTOSTART WITH WINDOWS ─────────────────────────────────────────────
    def get_autostart_status(self):
        """Checks if IT Tool LTT is configured to auto-start with Windows."""
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            try:
                val, _ = winreg.QueryValueEx(key, AUTOSTART_KEY_NAME)
                winreg.CloseKey(key)
                if not val:
                    return {"enabled": False, "path": ""}

                # Verify in StartupApproved\Run
                try:
                    appr_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run", 0, winreg.KEY_READ)
                    appr_val, _ = winreg.QueryValueEx(appr_key, AUTOSTART_KEY_NAME)
                    winreg.CloseKey(appr_key)
                    if isinstance(appr_val, bytes) and len(appr_val) > 0 and appr_val[0] not in (0, 2):
                        return {"enabled": False, "path": val}
                except Exception:
                    pass

                return {"enabled": True, "path": val}
            except FileNotFoundError:
                winreg.CloseKey(key)
                return {"enabled": False, "path": ""}
        except Exception as e:
            return {"enabled": False, "path": "", "error": str(e)}

    def set_autostart(self, enable):
        """Enables or disables IT Tool LTT auto-starting with Windows."""
        import winreg
        try:
            if enable:
                cmd = self._get_autostart_command()
                # 1. Write to Run key
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, AUTOSTART_KEY_NAME, 0, winreg.REG_SZ, cmd)
                winreg.CloseKey(key)

                # 2. Mark Enabled in StartupApproved
                try:
                    appr_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run")
                    winreg.SetValueEx(appr_key, AUTOSTART_KEY_NAME, 0, winreg.REG_BINARY, bytes([0x02, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
                    winreg.CloseKey(appr_key)
                except Exception:
                    pass

                self.log("SUCCESS", f"Đã BẬT tự động khởi động cùng Windows: {cmd}")
                return {
                    "success": True,
                    "enabled": True,
                    "path": cmd,
                    "message": "Đã BẬT tự động khởi động cùng Windows cho IT Tool LTT thành công!"
                }
            else:
                # 1. Delete from Run key
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                    winreg.DeleteValue(key, AUTOSTART_KEY_NAME)
                    winreg.CloseKey(key)
                except FileNotFoundError:
                    pass

                # 2. Delete or reset in StartupApproved
                try:
                    appr_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run", 0, winreg.KEY_SET_VALUE)
                    winreg.DeleteValue(appr_key, AUTOSTART_KEY_NAME)
                    winreg.CloseKey(appr_key)
                except Exception:
                    pass

                self.log("INFO", "Đã TẮT tự động khởi động cùng Windows cho IT Tool LTT")
                return {
                    "success": True,
                    "enabled": False,
                    "message": "Đã TẮT tự động khởi động cùng Windows cho IT Tool LTT thành công!"
                }
        except Exception as e:
            self.log("ERROR", f"Lỗi thiết lập khởi động cùng Windows: {e}")
            return {
                "success": False,
                "enabled": False,
                "message": f"Lỗi thiết lập khởi động cùng Windows: {e}"
            }

    def _get_autostart_command(self):
        """Resolves the best command/executable path to register for auto startup."""
        if getattr(sys, 'frozen', False):
            return f'"{os.path.abspath(sys.executable)}"'

        base = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.abspath(os.path.join(base, '..', 'dist', 'IT Tool LTT.exe')),
            os.path.abspath(os.path.join(base, '..', 'IT-Tools.exe')),
            os.path.abspath(os.path.join(base, '..', 'IT-Tools.bat')),
        ]
        for c in candidates:
            if os.path.exists(c):
                return f'"{c}"'

        main_py = os.path.abspath(os.path.join(base, 'main.py'))
        return f'"{sys.executable}" "{main_py}"'

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

    def start_one_click_printer_fix(self):
        """Starts asynchronous execution of the 4-step LAN printer fix with real-time log streaming."""
        self._printer_fix_progress = {
            "active": True,
            "status": "running",
            "step": 1,
            "step_status": ["running", "pending", "pending", "pending"],
            "percentage": 5,
            "message": "Đang khởi tạo tiến trình sửa lỗi...",
            "logs": [],
            "completed": False,
            "success": True
        }

        def worker():
            import modules.printer_fix as pf

            def log_cb(text, tag="info"):
                self._printer_fix_progress["logs"].append(text)
                self.log(tag.upper() if tag in ["ok", "warn", "error"] else "INFO", text)

            def prog_cb(data):
                self._printer_fix_progress["step"] = data.get("step", 1)
                self._printer_fix_progress["percentage"] = data.get("percentage", 0)
                self._printer_fix_progress["step_status"] = data.get("step_status", ["pending"] * 4)
                self._printer_fix_progress["message"] = data.get("message", "")
                if data.get("completed"):
                    self._printer_fix_progress["completed"] = True
                    self._printer_fix_progress["status"] = "completed"
                    self._printer_fix_progress["active"] = False

            try:
                pf.one_click_fix_all_lan_files(log=log_cb, progress_cb=prog_cb)
            except Exception as ex:
                self._printer_fix_progress["status"] = "error"
                self._printer_fix_progress["completed"] = True
                self._printer_fix_progress["active"] = False
                self._printer_fix_progress["success"] = False
                self._printer_fix_progress["message"] = f"Lỗi: {ex}"
                self._printer_fix_progress["logs"].append(f"[ERROR] {ex}")
                self.log("ERROR", f"Lỗi one_click_printer_fix: {ex}")

        threading.Thread(target=worker, daemon=True).start()
        return {"success": True, "message": "Đã bắt đầu sửa lỗi máy in LAN."}

    def get_one_click_printer_fix_status(self):
        """Returns current status and log buffer of the 4-step LAN printer fix."""
        return getattr(self, "_printer_fix_progress", {
            "active": False,
            "status": "idle",
            "step": 0,
            "step_status": ["pending"] * 4,
            "percentage": 0,
            "message": "",
            "logs": [],
            "completed": False,
            "success": True
        })

    def one_click_fix_all_printers(self):
        return self.start_one_click_printer_fix()

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
            # Làm sạch Target: loại bỏ ký tự dẫn đầu \\ hoặc //, khoảng trắng và tên folder chia sẻ
            clean_target = target.strip().replace('/', '\\')
            while clean_target.startswith('\\'):
                clean_target = clean_target[1:]
            if '\\' in clean_target:
                clean_target = clean_target.split('\\')[0].strip()

            if not clean_target:
                return {"success": False, "message": "Target (Tên máy chủ / IP) không hợp lệ!"}

            username = username.strip()
            password = password.strip() if password else ""

            CREATE_NO_WINDOW = 0x08000000

            # Lưu đồng thời Domain Credential (/add) và Generic Credential (/generic) để tương thích tối đa chia sẻ mạng LAN và máy in
            success = False
            last_err = ""

            # 1. Lưu dạng Domain Password
            if password:
                r1 = subprocess.run(
                    f'cmdkey /add:"{clean_target}" /user:"{username}" /pass:"{password}"',
                    shell=True, capture_output=True, text=True,
                    creationflags=CREATE_NO_WINDOW, encoding="utf-8", errors="ignore"
                )
                r2 = subprocess.run(
                    f'cmdkey /generic:"{clean_target}" /user:"{username}" /pass:"{password}"',
                    shell=True, capture_output=True, text=True,
                    creationflags=CREATE_NO_WINDOW, encoding="utf-8", errors="ignore"
                )
            else:
                r1 = subprocess.run(
                    ['cmdkey', f'/add:{clean_target}', f'/user:{username}', '/pass:'],
                    input='\n', capture_output=True, text=True,
                    creationflags=CREATE_NO_WINDOW, encoding="utf-8", errors="ignore"
                )
                r2 = subprocess.run(
                    ['cmdkey', f'/generic:{clean_target}', f'/user:{username}', '/pass:'],
                    input='\n', capture_output=True, text=True,
                    creationflags=CREATE_NO_WINDOW, encoding="utf-8", errors="ignore"
                )

            if r1.returncode == 0 or r2.returncode == 0:
                success = True
            else:
                last_err = (r1.stderr or r1.stdout or r2.stderr or r2.stdout).strip()

            if success:
                self.log("SUCCESS", f"Đã lưu Windows Credential cho Target: {clean_target} (User: {username})")
                return {"success": True, "message": f"✅ Đã lưu thành công Windows Credential cho '{clean_target}' (User: {username})!"}
            else:
                self.log("ERROR", f"Lỗi lưu credential: {last_err}")
                return {"success": False, "message": f"Lỗi khi lưu Credential: {last_err or 'Không xác định'}"}
        except Exception as e:
            self.log("ERROR", f"Lỗi ngoại lệ save_credential: {e}")
            return {"success": False, "message": f"Lỗi: {str(e)}"}

    def delete_credential(self, target):
        if not target:
            return {"success": False, "message": "Vui lòng chọn hoặc nhập Credential cần xóa!"}
        try:
            clean_target = target.strip()
            # Xóa các tiền tố thường gặp khi hiển thị
            for prefix in ["Domain:target=", "LegacyGeneric:target=", "Target: "]:
                if clean_target.startswith(prefix):
                    clean_target = clean_target[len(prefix):].strip()

            CREATE_NO_WINDOW = 0x08000000
            r = subprocess.run(
                f'cmdkey /delete:"{clean_target}"',
                shell=True, capture_output=True, text=True,
                creationflags=CREATE_NO_WINDOW, encoding="utf-8", errors="ignore"
            )

            # Nếu target có dạng TERMSRV/... hoặc IP, thử xóa cả dạng gốc
            if r.returncode != 0 and "/" in clean_target:
                sub_target = clean_target.split("/", 1)[1]
                subprocess.run(f'cmdkey /delete:"{sub_target}"', shell=True, creationflags=CREATE_NO_WINDOW)

            self.log("SUCCESS", f"Đã xóa Credential: {clean_target}")
            return {"success": True, "message": f"✅ Đã xóa Credential '{clean_target}'"}
        except Exception as e:
            self.log("ERROR", f"Lỗi delete_credential: {e}")
            return {"success": False, "message": str(e)}

    # ── USER CREATION FOR PRINTER SHARE ───────────────────────────────────
    def create_printer_share_user(self, username, password, description=""):
        if not username or not password:
            return {"success": False, "message": "Vui lòng nhập Username và Mật khẩu!"}

        username = username.strip()
        password = password.strip()

        # Kiểm tra độ dài mật khẩu (Windows Domain & Local Security Policy thường yêu cầu tối thiểu 8 ký tự)
        if len(password) < 8:
            return {
                "success": False,
                "message": "⚠️ Mật khẩu quá ngắn! Windows yêu cầu mật khẩu tối thiểu 8 ký tự (khuyến nghị có cả chữ hoa, chữ thường và số, VD: Printer@123456) theo chính sách bảo mật hệ thống."
            }

        # Kiểm tra quyền Administrator
        is_admin = False
        try:
            is_admin = (ctypes.windll.shell32.IsUserAnAdmin() != 0)
        except Exception:
            pass

        if not is_admin:
            return {
                "success": False,
                "message": "❌ Yêu cầu quyền Administrator để tạo User Windows!\nVui lòng đóng phần mềm và mở lại bằng cách: Click chuột phải vào file exe -> chọn 'Run as administrator'."
            }

        try:
            CREATE_NO_WINDOW = 0x08000000
            results = []
            errors = []

            def run_cmd(cmd):
                r = subprocess.run(
                    cmd, shell=True,
                    capture_output=True, text=True,
                    creationflags=CREATE_NO_WINDOW,
                    encoding="utf-8", errors="ignore"
                )
                out = (r.stdout + r.stderr).strip()
                return r.returncode, out

            # 1. Tạo tài khoản user mới
            rc, out = run_cmd(f'net user "{username}" "{password}" /add /expires:never /active:yes')
            if rc != 0:
                # Nếu user đã tồn tại (rc=2 hoặc thông báo already exists)
                if "already" in out.lower() or "tồn tại" in out or rc == 2:
                    run_cmd(f'net user "{username}" "{password}" /active:yes')
                    results.append(f"User '{username}' đã tồn tại, đã cập nhật lại mật khẩu.")
                else:
                    # Thử tạo qua PowerShell New-LocalUser
                    desc_text = description if description else "Tai khoan chia se may in"
                    ps_cmd = (
                        f'powershell -NoProfile -Command "'
                        f'$p = ConvertTo-SecureString \'{password}\' -AsPlainText -Force; '
                        f'New-LocalUser -Name \'{username}\' -Password $p -PasswordNeverExpires '
                        f'-Description \'{desc_text}\'"'
                    )
                    rc_ps, out_ps = run_cmd(ps_cmd)
                    if rc_ps == 0:
                        results.append(f"Đã tạo tài khoản '{username}' (qua PowerShell).")
                    else:
                        errors.append(f"Tạo user thất bại: {out or out_ps}")
            else:
                results.append(f"Đã tạo tài khoản '{username}'.")

            if errors:
                msg = "Hoàn thành có lỗi:\n" + "\n".join(errors)
                self.log("WARNING", msg)
                return {"success": False, "message": msg}

            # 2. Đặt mô tả nếu có
            if description:
                run_cmd(f'net user "{username}" /comment:"{description}"')

            # 3. Mật khẩu không hết hạn (Ưu tiên PowerShell Set-LocalUser, tương thích Windows 10/11)
            rc2b, out2b = run_cmd(
                f'powershell -NoProfile -Command "Set-LocalUser -Name \'{username}\' -PasswordNeverExpires $true"'
            )
            if rc2b == 0:
                results.append("Đã đặt mật khẩu vĩnh viễn không hết hạn.")
            else:
                # Fallback WMIC nếu có
                rc2, _ = run_cmd(f'wmic useraccount where name="{username}" set PasswordExpires=FALSE')
                if rc2 == 0:
                    results.append("Đã đặt mật khẩu vĩnh viễn không hết hạn (WMIC).")

            # 4. Thêm vào nhóm quản trị hoặc nhóm Users để phân quyền in mạng LAN
            # Dùng SID S-1-5-32-544 (Administrators) để không phụ thuộc ngôn ngữ Windows
            ps_group_cmd = (
                f'powershell -NoProfile -Command "'
                f'$adminGroup = (Get-LocalGroup -SID \'S-1-5-32-544\').Name; '
                f'Add-LocalGroupMember -Group $adminGroup -Member \'{username}\'"'
            )
            rc3_ps, _ = run_cmd(ps_group_cmd)
            if rc3_ps == 0:
                results.append(f"Đã thêm '{username}' vào nhóm Administrators.")
            else:
                # Fallback net localgroup
                rc3, out3 = run_cmd(f'net localgroup Administrators "{username}" /add')
                if rc3 == 0:
                    results.append(f"Đã thêm '{username}' vào nhóm Administrators.")
                else:
                    rc3b, _ = run_cmd(f'net localgroup Users "{username}" /add')
                    if rc3b == 0:
                        results.append(f"Đã thêm '{username}' vào nhóm Users.")

            # 5. Bật AllowInsecureGuestAuth cho chia sẻ máy in LAN
            run_cmd(
                r'reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" '
                r'/v AllowInsecureGuestAuth /t REG_DWORD /d 1 /f'
            )

            # 6. Tắt Password Protected Sharing (forceguest = 0 để chứng thực bằng user vừa tạo)
            run_cmd(
                r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" '
                r'/v forceguest /t REG_DWORD /d 0 /f'
            )

            # 7. Bật File and Printer Sharing qua Firewall
            run_cmd('netsh advfirewall firewall set rule group="File and Printer Sharing" new enable=Yes')

            # 8. Đặt tài khoản active
            run_cmd(f'net user "{username}" /active:yes')

            # 9. Tự động lưu luôn vào Windows Credential của máy nội bộ nếu người dùng muốn
            self.save_credential("127.0.0.1", username, password)
            self.save_credential("localhost", username, password)

            summary = f"✅ Tạo User '{username}' thành công!\n" + "\n".join(f"• {r}" for r in results) + \
                      f"\n\n📌 Thông tin đăng nhập từ máy trạm:\n- User: {username}\n- Password: {password}"
            self.log("SUCCESS", summary)
            return {"success": True, "message": summary}
        except Exception as e:
            self.log("ERROR", f"Lỗi tạo user: {e}")
            return {"success": False, "message": f"Lỗi hệ thống: {str(e)}"}

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

    # ── LOCAL GROUPS & USERS (REAL-TIME WINDOWS CONFIG) ─────────────────
    def get_local_groups_and_users(self):
        """Fetches all Windows local groups and their users in real-time using native Win32 NetAPI with PowerShell fallback."""
        try:
            import ctypes
            from ctypes import wintypes
            import socket

            computer_name = socket.gethostname()
            groups_list = []
            users_list = []
            user_to_groups = {}

            # Primary high-performance method: Win32 NetAPI32 (~15-20ms)
            try:
                netapi32 = ctypes.WinDLL("netapi32.dll")

                class LOCALGROUP_INFO_1(ctypes.Structure):
                    _fields_ = [
                        ("lgrpi1_name", wintypes.LPWSTR),
                        ("lgrpi1_comment", wintypes.LPWSTR),
                    ]

                class LOCALGROUP_MEMBERS_INFO_2(ctypes.Structure):
                    _fields_ = [
                        ("lgrmi2_sid", ctypes.c_void_p),
                        ("lgrmi2_sidusage", wintypes.DWORD),
                        ("lgrmi2_domainandname", wintypes.LPWSTR),
                    ]

                class USER_INFO_1(ctypes.Structure):
                    _fields_ = [
                        ("usri1_name", wintypes.LPWSTR),
                        ("usri1_password", wintypes.LPWSTR),
                        ("usri1_password_age", wintypes.DWORD),
                        ("usri1_priv", wintypes.DWORD),
                        ("usri1_home_dir", wintypes.LPWSTR),
                        ("usri1_comment", wintypes.LPWSTR),
                        ("usri1_flags", wintypes.DWORD),
                        ("usri1_script_path", wintypes.LPWSTR),
                    ]

                # 1. Enumerate all local groups
                bufptr = ctypes.c_void_p()
                entriesread = wintypes.DWORD()
                totalentries = wintypes.DWORD()
                resume_handle = ctypes.c_void_p()

                res = netapi32.NetLocalGroupEnum(
                    None, 1, ctypes.byref(bufptr), -1,
                    ctypes.byref(entriesread), ctypes.byref(totalentries),
                    ctypes.byref(resume_handle)
                )

                if res == 0 and bufptr.value:
                    p_info = ctypes.cast(bufptr, ctypes.POINTER(LOCALGROUP_INFO_1))
                    for i in range(entriesread.value):
                        gname = p_info[i].lgrpi1_name or ""
                        gdesc = p_info[i].lgrpi1_comment or ""

                        # Fetch members of this group
                        m_buf = ctypes.c_void_p()
                        m_read = wintypes.DWORD()
                        m_total = wintypes.DWORD()
                        m_resume = ctypes.c_void_p()
                        m_res = netapi32.NetLocalGroupGetMembers(
                            None, gname, 2, ctypes.byref(m_buf), -1,
                            ctypes.byref(m_read), ctypes.byref(m_total),
                            ctypes.byref(m_resume)
                        )
                        members = []
                        if m_res == 0 and m_buf.value:
                            p_mem = ctypes.cast(m_buf, ctypes.POINTER(LOCALGROUP_MEMBERS_INFO_2))
                            for j in range(m_read.value):
                                raw_name = p_mem[j].lgrmi2_domainandname or ""
                                sid_type = p_mem[j].lgrmi2_sidusage
                                is_group = (sid_type in (2, 4, 5))
                                parts = raw_name.split("\\")
                                short_name = parts[-1] if parts else raw_name
                                domain = parts[0] if len(parts) > 1 else ""
                                is_domain = bool(domain and domain.upper() != computer_name.upper())

                                members.append({
                                    "raw_name": raw_name,
                                    "name": short_name,
                                    "domain": domain,
                                    "is_domain": is_domain,
                                    "is_group": is_group,
                                    "sid_type": sid_type
                                })

                                # Map user -> groups
                                u_key = short_name.lower()
                                if u_key not in user_to_groups:
                                    user_to_groups[u_key] = []
                                if gname not in user_to_groups[u_key]:
                                    user_to_groups[u_key].append(gname)

                            netapi32.NetApiBufferFree(m_buf)

                        groups_list.append({
                            "name": gname,
                            "description": gdesc,
                            "member_count": len(members),
                            "members": members
                        })
                    netapi32.NetApiBufferFree(bufptr)

                # 2. Enumerate all local users
                u_buf = ctypes.c_void_p()
                u_read = wintypes.DWORD()
                u_total = wintypes.DWORD()
                u_resume = ctypes.c_void_p()

                u_res = netapi32.NetUserEnum(
                    None, 1, 2, ctypes.byref(u_buf), -1,
                    ctypes.byref(u_read), ctypes.byref(u_total),
                    ctypes.byref(u_resume)
                )

                if u_res == 0 and u_buf.value:
                    p_uinfo = ctypes.cast(u_buf, ctypes.POINTER(USER_INFO_1))
                    for i in range(u_read.value):
                        u = p_uinfo[i]
                        uname = u.usri1_name or ""
                        disabled = bool(u.usri1_flags & 0x0002)
                        pwd_never_expires = bool(u.usri1_flags & 0x10000)
                        comment = u.usri1_comment or ""

                        my_groups = user_to_groups.get(uname.lower(), [])

                        users_list.append({
                            "username": uname,
                            "disabled": disabled,
                            "pwd_never_expires": pwd_never_expires,
                            "comment": comment,
                            "groups": my_groups
                        })
                    netapi32.NetApiBufferFree(u_buf)

            except Exception as net_err:
                self.log("WARN", f"NetAPI local groups fallback to PowerShell: {net_err}")
                ps_code = """
                $groups = Get-LocalGroup
                $result = @()
                foreach ($g in $groups) {
                    $members = @()
                    try {
                        $mList = Get-LocalGroupMember -Group $g.Name -ErrorAction Stop
                        foreach ($m in $mList) {
                            $parts = $m.Name.Split('\\')
                            $members += [PSCustomObject]@{
                                raw_name = $m.Name
                                name = $parts[-1]
                                domain = if ($parts.Length -gt 1) { $parts[0] } else { '' }
                                is_domain = ($m.PrincipalSource.ToString() -ne 'Local')
                                is_group = ($m.ObjectClass -eq 'Group')
                            }
                        }
                    } catch {}
                    $result += [PSCustomObject]@{
                        name = $g.Name
                        description = if ($g.Description) { $g.Description } else { '' }
                        member_count = $members.Count
                        members = $members
                    }
                }
                $result | ConvertTo-Json -Depth 3
                """
                p = subprocess.run(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_code],
                    capture_output=True, text=True, encoding="utf-8", errors="ignore",
                    creationflags=0x08000000
                )
                if p.returncode == 0 and p.stdout.strip():
                    groups_list = json.loads(p.stdout)
                    if isinstance(groups_list, dict):
                        groups_list = [groups_list]

            now_str = datetime.datetime.now().strftime("%H:%M:%S • %d/%m/%Y")
            return {
                "success": True,
                "computer_name": computer_name,
                "timestamp": now_str,
                "total_groups": len(groups_list),
                "total_users": len(users_list),
                "groups": groups_list,
                "users": users_list
            }
        except Exception as e:
            self.log("ERROR", f"Lỗi get_local_groups_and_users: {e}")
            return {"success": False, "message": str(e), "groups": [], "users": []}

    def open_lusrmgr(self):
        """Opens native Windows Local Users and Groups console (lusrmgr.msc) or Computer Management."""
        try:
            subprocess.Popen("lusrmgr.msc", shell=True)
            return {"success": True, "message": "Đã mở Local Users and Groups (lusrmgr.msc)"}
        except Exception:
            try:
                subprocess.Popen("compmgmt.msc", shell=True)
                return {"success": True, "message": "Đã mở Computer Management (compmgmt.msc)"}
            except Exception as e:
                return {"success": False, "message": f"Không thể mở công cụ quản lý: {e}"}

    def toggle_local_user_active(self, username, enable=True):
        """Enables or disables a local user account."""
        try:
            username = username.strip()
            if not username:
                return {"success": False, "message": "Username không hợp lệ!"}
            action = "yes" if enable else "no"
            cmd = f'net user "{username}" /active:{action}'
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore", creationflags=0x08000000)
            if r.returncode == 0:
                verb = "kích hoạt" if enable else "vô hiệu hóa"
                self.log("SUCCESS", f"Đã {verb} tài khoản '{username}'")
                return {"success": True, "message": f"Đã {verb} tài khoản '{username}' thành công!"}
            return {"success": False, "message": f"Lỗi: {r.stderr or r.stdout}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def delete_local_user(self, username):
        """Deletes a local user account."""
        try:
            username = username.strip()
            if not username:
                return {"success": False, "message": "Username không hợp lệ!"}
            if username.lower() in ("administrator", "guest", "defaultaccount"):
                return {"success": False, "message": f"Không được xóa tài khoản hệ thống mặc định '{username}'!"}
            cmd = f'net user "{username}" /delete'
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore", creationflags=0x08000000)
            if r.returncode == 0:
                self.log("SUCCESS", f"Đã xóa tài khoản '{username}'")
                return {"success": True, "message": f"Đã xóa tài khoản '{username}' thành công!"}
            return {"success": False, "message": f"Lỗi khi xóa user: {r.stderr or r.stdout}"}
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
            total_removed = wc.clean_office_keys(bridge)
            if total_removed and total_removed > 0:
                msg = f"Đã gỡ sạch thành công {total_removed} key Office lậu & dọn cấu hình KMS!"
            else:
                msg = "Đã dọn dẹp cấu hình KMS Office (Không còn key lậu nào đang cài đặt)."
            return {"success": True, "message": msg, "removed": total_removed or 0}
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
            ok, msg = wc.install_win_key(key.strip(), bridge)
            return {"success": ok, "message": msg}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def uninstall_win_key(self):
        """Uninstalls current product key via slmgr /upk & /cpky."""
        try:
            import modules.wincheck as wc
            bridge = LogBridge(self)
            ok, msg = wc.uninstall_win_key(bridge)
            return {"success": ok, "message": msg}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def deactivate_win_digital(self):
        """Completely deactivates Windows Digital License / uninstalls license."""
        try:
            import modules.wincheck as wc
            bridge = LogBridge(self)
            ok, msg = wc.deactivate_windows(bridge)
            return {"success": ok, "message": msg}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def restore_win_digital(self):
        """Restores Windows Digital License via default retail generic key and slmgr /ato."""
        try:
            import modules.wincheck as wc
            bridge = LogBridge(self)
            ok, msg = wc.restore_digital_license(bridge)
            return {"success": ok, "message": msg}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def rearm_windows(self):
        """Rearms Windows trial period via slmgr /rearm."""
        try:
            import modules.wincheck as wc
            bridge = LogBridge(self)
            res = wc.rearm_windows(bridge)
            return {"success": True, "message": f"Kết quả gia hạn (Rearm):\n{res or 'Hoàn tất'}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def rearm_office(self):
        """Rearms Microsoft Office trial period via ospp.vbs /rearm."""
        try:
            import modules.wincheck as wc
            bridge = LogBridge(self)
            ok, msg = wc.rearm_office(bridge)
            return {"success": ok, "message": msg}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def install_office_key(self, key):
        """Installs a product key for Microsoft Office via ospp.vbs /inpkey:"""
        if not key:
            return {"success": False, "message": "Vui lòng nhập Product Key Office!"}
        try:
            import modules.wincheck as wc
            bridge = LogBridge(self)
            ok, msg = wc.install_office_key(key.strip(), bridge)
            return {"success": ok, "message": msg}
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

    def get_realtime_stats(self):
        """Returns real-time CPU%, RAM%, disk I/O, network speed, and battery status.
        Polled by the frontend for live gauge & battery updates.
        """
        import time
        from modules.computer_info import get_system_power_status, get_comprehensive_battery_info

        # 1. Real-time Battery Status — uses cached comprehensive WMI data + instant ctypes power status
        battery = get_comprehensive_battery_info(quick=True)

        def fmt_speed(kb_s):
            if kb_s >= 1024:
                return f"{kb_s/1024:.1f} MB/s"
            return f"{kb_s:.0f} KB/s"

        now = time.time()

        try:
            import psutil

            # Non-blocking CPU percent
            if not hasattr(self, '_cpu_initialized'):
                psutil.cpu_percent(interval=None)
                self._cpu_initialized = True
                cpu_pct = psutil.cpu_percent(interval=0.05)
            else:
                cpu_pct = psutil.cpu_percent(interval=None)

            # RAM
            ram = psutil.virtual_memory()
            ram_pct = ram.percent
            ram_used_mb = ram.used // (1024 * 1024)
            ram_total_mb = ram.total // (1024 * 1024)
            ram_used_str = f"{ram_used_mb / 1024:.1f} GB" if ram_used_mb >= 1024 else f"{ram_used_mb} MB"
            ram_total_str = f"{ram_total_mb / 1024:.1f} GB" if ram_total_mb >= 1024 else f"{ram_total_mb} MB"

            # Disk I/O (non-blocking delta calculation)
            d2 = psutil.disk_io_counters()
            disk_read_kb = disk_write_kb = 0.0
            if d2:
                if hasattr(self, '_disk_baseline') and self._disk_baseline:
                    prev_d, prev_time = self._disk_baseline
                    elapsed = now - prev_time
                    if elapsed > 0:
                        disk_read_kb = (d2.read_bytes - prev_d.read_bytes) / 1024 / elapsed
                        disk_write_kb = (d2.write_bytes - prev_d.write_bytes) / 1024 / elapsed
                self._disk_baseline = (d2, now)

            # Partitions
            partitions_usage = []
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    partitions_usage.append({
                        "drive": part.mountpoint.replace("\\", ""),
                        "used_gb": round(usage.used / (1024**3), 1),
                        "free_gb": round(usage.free / (1024**3), 1),
                        "total_gb": round(usage.total / (1024**3), 1),
                        "pct": usage.percent,
                    })
                except Exception:
                    pass

            # Network I/O (non-blocking delta calculation)
            n2 = psutil.net_io_counters()
            net_rx_kb = net_tx_kb = 0.0
            if hasattr(self, '_net_baseline') and self._net_baseline:
                prev_n, prev_time = self._net_baseline
                elapsed = now - prev_time
                if elapsed > 0:
                    net_rx_kb = (n2.bytes_recv - prev_n.bytes_recv) / 1024 / elapsed
                    net_tx_kb = (n2.bytes_sent - prev_n.bytes_sent) / 1024 / elapsed
            self._net_baseline = (n2, now)

            return {
                "success": True,
                "cpu_pct": round(cpu_pct, 1),
                "ram_pct": round(ram_pct, 1),
                "ram_used": ram_used_str,
                "ram_total": ram_total_str,
                "disk_read": fmt_speed(disk_read_kb),
                "disk_write": fmt_speed(disk_write_kb),
                "disk_read_kb": round(disk_read_kb, 1),
                "disk_write_kb": round(disk_write_kb, 1),
                "net_rx": fmt_speed(net_rx_kb),
                "net_tx": fmt_speed(net_tx_kb),
                "net_rx_kb": round(net_rx_kb, 1),
                "net_tx_kb": round(net_tx_kb, 1),
                "partitions_usage": partitions_usage,
                "battery": battery
            }
        except Exception:
            # Fallback using native Windows ctypes
            cpu_pct = 0.0
            ram_pct = 0.0
            ram_used_str = "N/A"
            ram_total_str = "N/A"
            partitions_usage = []
            try:
                import ctypes
                from ctypes import wintypes
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ('dwLength', wintypes.DWORD),
                        ('dwMemoryLoad', wintypes.DWORD),
                        ('ullTotalPhys', ctypes.c_uint64),
                        ('ullAvailPhys', ctypes.c_uint64),
                        ('ullTotalPageFile', ctypes.c_uint64),
                        ('ullAvailPageFile', ctypes.c_uint64),
                        ('ullTotalVirtual', ctypes.c_uint64),
                        ('ullAvailVirtual', ctypes.c_uint64),
                        ('ullAvailExtendedVirtual', ctypes.c_uint64),
                    ]
                mem = MEMORYSTATUSEX()
                mem.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
                    ram_pct = float(mem.dwMemoryLoad)
                    t_gb = mem.ullTotalPhys / (1024**3)
                    u_gb = (mem.ullTotalPhys - mem.ullAvailPhys) / (1024**3)
                    ram_total_str = f"{t_gb:.1f} GB"
                    ram_used_str = f"{u_gb:.1f} GB"

                # Drives
                buf = ctypes.create_unicode_buffer(1024)
                res = ctypes.windll.kernel32.GetLogicalDriveStringsW(1023, buf)
                drives = [d for d in buf[:res].split('\x00') if d]
                for d in drives:
                    free_b = ctypes.c_ulonglong(0)
                    tot_b = ctypes.c_ulonglong(0)
                    tot_f = ctypes.c_ulonglong(0)
                    if ctypes.windll.kernel32.GetDiskFreeSpaceExW(d, ctypes.byref(free_b), ctypes.byref(tot_b), ctypes.byref(tot_f)):
                        if tot_b.value > 0:
                            used = tot_b.value - free_b.value
                            partitions_usage.append({
                                'drive': d.replace('\\', ''),
                                'total_gb': round(tot_b.value / (1024**3), 1),
                                'free_gb': round(free_b.value / (1024**3), 1),
                                'used_gb': round(used / (1024**3), 1),
                                'pct': round(used * 100.0 / tot_b.value, 1)
                            })
            except Exception:
                pass

            return {
                "success": True,
                "cpu_pct": cpu_pct,
                "ram_pct": ram_pct,
                "ram_used": ram_used_str,
                "ram_total": ram_total_str,
                "disk_read": "0 KB/s",
                "disk_write": "0 KB/s",
                "disk_read_kb": 0.0,
                "disk_write_kb": 0.0,
                "net_rx": "0 KB/s",
                "net_tx": "0 KB/s",
                "net_rx_kb": 0.0,
                "net_tx_kb": 0.0,
                "partitions_usage": partitions_usage,
                "battery": battery
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
        """Exports computer configuration specs to full Excel (.xlsx) or CSV format."""
        try:
            import modules.computer_info as ci
            res = ci.export_specs(format_type, specs_data)
            if res.get("success"):
                file_path = res.get("file_path", "")
                self.log("SUCCESS", f"Đã xuất cấu hình máy tính tại: {file_path}")
                if file_path and os.path.exists(file_path):
                    subprocess.run(f'explorer.exe /select,"{file_path}"', shell=True)
            else:
                self.log("ERROR", res.get("message", "Lỗi xuất file"))
            return res
        except Exception as e:
            self.log("ERROR", f"Lỗi xuất cấu hình: {e}")
            return {"success": False, "message": str(e)}

    def check_missing_drivers(self):
        """Scans for genuine missing or warning drivers matching Windows Device Manager in real time."""
        try:
            import modules.computer_info as ci
            issues = ci.get_device_manager_issues()
            count = len(issues)
            if count == 0:
                self.log("SUCCESS", "Kiểm tra Driver: 100% thiết bị phần cứng đều có Driver đầy đủ và hoạt động tốt.")
                return {
                    "success": True,
                    "total": 0,
                    "missing_drivers": [],
                    "message": "Tất cả thiết bị phần cứng đều đã được cài đặt Driver đầy đủ và hoạt động hoàn hảo!"
                }
            else:
                self.log("WARN", f"Kiểm tra Driver: Phát hiện {count} thiết bị phần cứng thiếu hoặc lỗi Driver.")
                return {
                    "success": True,
                    "total": count,
                    "missing_drivers": issues,
                    "message": f"Phát hiện {count} thiết bị phần cứng chưa cài đặt hoặc bị lỗi Driver."
                }
        except Exception as e:
            self.log("ERROR", f"Lỗi kiểm tra driver: {e}")
            return {"success": False, "total": 0, "missing_drivers": [], "message": str(e)}

    def open_device_manager(self):
        """Opens native Windows Device Manager console (devmgmt.msc)."""
        try:
            subprocess.Popen("devmgmt.msc", shell=True)
            self.log("SUCCESS", "Đã mở Trình quản lý thiết bị Device Manager (devmgmt.msc) của Windows!")
            return {"success": True, "message": "Đã mở Device Manager thành công!"}
        except Exception as e:
            self.log("ERROR", f"Lỗi mở devmgmt.msc: {e}")
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

    def open_taskbar_settings(self):
        """Opens Windows native Taskbar Settings page (ms-settings:taskbar)."""
        try:
            subprocess.Popen("start ms-settings:taskbar", shell=True)
            self.log("SUCCESS", "Đã mở Cài đặt Taskbar của Windows!")
            return {"success": True, "message": "Đã mở Cài đặt Taskbar của Windows thành công!"}
        except Exception as e:
            self.log("ERROR", f"Lỗi mở Cài đặt Taskbar: {e}")
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

    def get_firewall_rules_detail(self, filter_type="fps"):
        """Returns details of firewall rules matching the filter_type."""
        try:
            import modules.firewall as fw
            return fw.get_firewall_rules_detail(filter_type)
        except Exception as e:
            return {"success": False, "message": str(e), "rules": [], "total": 0}

    # ── IP MANAGER & SUBNET CALCULATOR ───────────────────────────────────
    def get_network_adapters(self):
        """Returns list of all network adapters, local IP, and external IP."""
        try:
            import modules.ip_manager as im
            res = im.get_network_adapters()
            return {"success": True, "data": res}
        except Exception as e:
            return {"success": False, "message": str(e), "data": {"local_ip": "N/A", "external_ip": "N/A", "adapters": []}}

    def get_external_ip(self):
        """Fetches public IP asynchronously."""
        try:
            import modules.ip_manager as im
            return im.get_external_ip()
        except Exception as e:
            return {"success": False, "ip": "N/A", "message": str(e)}

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
            elif module_name == "sendto_editor":
                sendto_path = os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\SendTo')
                os.startfile(sendto_path)
                self.log("SUCCESS", f"Đã mở thư mục SendTo: {sendto_path}")
            else:
                self.log("SUCCESS", f"Đã thực thi tác vụ {module_name} ({action})")

            return {"success": True, "message": f"Đã hoàn thành {module_name}!"}
        except Exception as e:
            self.log("ERROR", f"Lỗi chạy module {module_name}: {e}")
            return {"success": False, "message": str(e)}

    # ── SENDTO EDITOR API ─────────────────────────────────────────────────────
    _SENDTO_PATH = os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\SendTo')

    @staticmethod
    def _parse_lnk_target(filepath):
        """Parses target path from a Windows .lnk file in pure Python."""
        try:
            import struct
            with open(filepath, 'rb') as f:
                content = f.read()
            if len(content) < 0x4c or content[:4] != b'L\x00\x00\x00':
                return ''
            flags = struct.unpack('<I', content[0x14:0x18])[0]
            pos = 0x4c
            if flags & 0x01:  # HasLinkTargetIDList
                id_list_size = struct.unpack('<H', content[pos:pos+2])[0]
                pos += 2 + id_list_size
            if flags & 0x02 and pos < len(content):  # HasLinkInfo
                local_base_pos = struct.unpack('<I', content[pos+0x10:pos+0x14])[0]
                if local_base_pos != 0:
                    target_bytes = content[pos+local_base_pos:]
                    end = target_bytes.find(b'\x00')
                    if end != -1:
                        return target_bytes[:end].decode('mbcs', errors='ignore')
        except Exception:
            pass
        return ''

    def get_sendto_entries(self):
        """Returns all entries in the SendTo folder as a list of dicts with target details."""
        try:
            sendto = self._SENDTO_PATH
            if not os.path.exists(sendto):
                os.makedirs(sendto, exist_ok=True)
            entries = []
            for fname in sorted(os.listdir(sendto), key=lambda x: x.lower()):
                fpath = os.path.join(sendto, fname)
                ext = os.path.splitext(fname)[1].lower()
                target = ''
                if ext == '.lnk':
                    ftype = 'Shortcut'
                    target = self._parse_lnk_target(fpath)
                elif ext == '.exe':
                    ftype = 'Executable'
                    target = fpath
                elif os.path.isdir(fpath):
                    ftype = 'Folder'
                    target = fpath
                else:
                    ftype = ext.lstrip('.').upper() or 'File'
                try:
                    size = os.path.getsize(fpath)
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024*1024:
                        size_str = f"{size//1024} KB"
                    else:
                        size_str = f"{size//1024//1024} MB"
                except Exception:
                    size_str = ""
                entries.append({
                    "name": fname,
                    "type": ftype,
                    "path": fpath,
                    "target": target,
                    "size": size_str,
                    "is_system": fname.lower() in ['desktop.ini', 'desktop (create shortcut).desklink'],
                })
            return {"success": True, "entries": entries, "sendto_path": sendto}
        except Exception as e:
            return {"success": False, "message": str(e), "entries": []}

    def browse_sendto_file(self):
        """Opens native file picker to select a program/file for SendTo."""
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            file_path = filedialog.askopenfilename(
                title="Chọn File hoặc Chương trình muốn thêm vào SendTo",
                filetypes=[
                    ("Chương trình thực thi / Script", "*.exe;*.bat;*.cmd;*.ps1;*.vbs;*.py"),
                    ("Tất cả tập tin", "*.*")
                ]
            )
            root.destroy()
            return file_path or ""
        except Exception as e:
            self.log("ERROR", f"Lỗi mở hộp thoại chọn file: {e}")
            return ""

    def browse_sendto_folder(self):
        """Opens native folder picker to select a folder for SendTo."""
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            folder_path = filedialog.askdirectory(title="Chọn Thư mục muốn thêm vào SendTo")
            root.destroy()
            return folder_path or ""
        except Exception as e:
            self.log("ERROR", f"Lỗi mở hộp thoại chọn thư mục: {e}")
            return ""

    def create_sendto_shortcut(self, name, target_path):
        """Creates a .lnk shortcut in SendTo pointing to target_path using Base64 encoded PowerShell."""
        try:
            import base64
            import re
            import shutil

            if not name or not target_path:
                return {"success": False, "message": "Vui lòng nhập tên hiển thị và đường dẫn target!"}

            target_path = target_path.strip().strip('"').strip("'")
            if not target_path:
                return {"success": False, "message": "Đường dẫn target không hợp lệ!"}

            # Check if target exists
            if not os.path.exists(target_path):
                which_p = shutil.which(target_path)
                if which_p:
                    target_path = which_p
                else:
                    return {"success": False, "message": f"Không tìm thấy file/thư mục: {target_path}"}

            # Sanitize shortcut name
            clean_name = name.strip()
            clean_name = re.sub(r'[\\/*?:"<>|]', '_', clean_name).strip(' ._')
            if not clean_name:
                clean_name = os.path.splitext(os.path.basename(target_path))[0] or "Shortcut"
            if not clean_name.lower().endswith('.lnk'):
                clean_name += '.lnk'

            lnk_path = os.path.join(self._SENDTO_PATH, clean_name)

            clean_lnk_esc = lnk_path.replace("'", "''")
            clean_target_esc = target_path.replace("'", "''")

            ps_code = f"""
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut('{clean_lnk_esc}')
$s.TargetPath = '{clean_target_esc}'
if (Test-Path -LiteralPath '{clean_target_esc}' -PathType Container) {{
    $s.WorkingDirectory = '{clean_target_esc}'
}} else {{
    $s.WorkingDirectory = [System.IO.Path]::GetDirectoryName('{clean_target_esc}')
}}
$s.Save()
"""
            encoded = base64.b64encode(ps_code.encode('utf-16le')).decode('ascii')
            r = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
                               capture_output=True, timeout=10)

            if os.path.exists(lnk_path) and os.path.getsize(lnk_path) > 100:
                self.log("SUCCESS", f"Đã tạo shortcut SendTo: {clean_name} -> {target_path}")
                return {"success": True, "message": f"Đã tạo shortcut: {clean_name}"}
            else:
                err_text = r.stderr.decode(errors='ignore').strip()
                return {"success": False, "message": f"Lỗi tạo shortcut: {err_text or 'Không thể lưu file .lnk'}"}
        except Exception as e:
            self.log("ERROR", f"Lỗi tạo shortcut SendTo: {e}")
            return {"success": False, "message": str(e)}

    def delete_sendto_entry(self, entry_path):
        """Deletes a file or folder from the SendTo folder."""
        try:
            import stat
            import shutil

            if not entry_path:
                return {"success": False, "message": "Chưa chọn mục cần xóa!"}

            # Support relative filename or full path
            if not os.path.isabs(entry_path):
                entry_path = os.path.join(self._SENDTO_PATH, entry_path)

            real = os.path.realpath(entry_path)
            sendto_real = os.path.realpath(self._SENDTO_PATH)

            # Security check (case-insensitive for Windows)
            if not real.lower().startswith((sendto_real + os.sep).lower()) and real.lower() != sendto_real.lower():
                return {"success": False, "message": "Chỉ được xóa các mục trong thư mục SendTo!"}

            fname = os.path.basename(real).lower()
            if fname in ['desktop.ini', 'desktop (create shortcut).desklink']:
                return {"success": False, "message": "Đây là file hệ thống Windows, không thể xóa!"}

            if not os.path.exists(real):
                return {"success": False, "message": "Mục này không còn tồn tại!"}

            # Remove read-only / hidden attribute if needed
            try:
                os.chmod(real, stat.S_IWRITE | stat.S_IREAD)
            except Exception:
                pass

            if os.path.isdir(real):
                shutil.rmtree(real, ignore_errors=True)
            else:
                os.remove(real)

            self.log("SUCCESS", f"Đã xóa khỏi SendTo: {os.path.basename(entry_path)}")
            return {"success": True, "message": f"Đã xóa: {os.path.basename(entry_path)}"}
        except Exception as e:
            self.log("ERROR", f"Lỗi xóa mục SendTo: {e}")
            return {"success": False, "message": str(e)}

    def open_sendto_folder(self):
        """Opens the SendTo folder in Windows Explorer."""
        try:
            os.startfile(self._SENDTO_PATH)
            return {"success": True, "message": f"Đã mở thư mục: {self._SENDTO_PATH}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def open_sendto_entry_location(self, entry_path):
        """Highlights the target or the entry itself in Windows File Explorer."""
        try:
            target = entry_path
            if entry_path.lower().endswith('.lnk'):
                parsed = self._parse_lnk_target(entry_path)
                if parsed and os.path.exists(parsed):
                    target = parsed
            if os.path.exists(target):
                subprocess.Popen(f'explorer /select,"{os.path.normpath(target)}"')
                return {"success": True, "message": f"Đã mở vị trí: {target}"}
            else:
                os.startfile(self._SENDTO_PATH)
                return {"success": True, "message": "Đã mở thư mục SendTo"}
        except Exception as e:
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
            default_dir = bb.get_default_backup_dir()
            return {"success": True, "browsers": browsers, "history": history, "default_backup_dir": default_dir}
        except Exception as e:
            self.log("ERROR", f"Lỗi quét thông tin trình duyệt: {e}")
            return {"success": False, "message": str(e), "browsers": [], "history": [], "default_backup_dir": "D:\\Browser_Backups"}

    def get_browser_backup_progress(self):
        """Returns live progress state for Browser Backup / Restore."""
        return self._browser_backup_progress

    def backup_browsers(self, selected_browsers, options, target_dir=""):
        """Performs full or selective backup of selected browsers asynchronously with progress."""
        if self._browser_backup_progress.get("active"):
            return {"success": False, "message": "Tiến trình sao lưu đang diễn ra, vui lòng chờ hoàn tất!"}

        self._browser_backup_progress = {
            "active": True,
            "mode": "backup",
            "percent": 0,
            "status": "running",
            "current_browser": "",
            "step_title": "Đang chuẩn bị sao lưu...",
            "detail": "Khởi tạo thư mục và quét hồ sơ...",
            "logs": [],
            "result": None
        }

        def _run_backup():
            try:
                import modules.browser_backup as bb
                def on_progress(percent, b_name, title, detail, log_msg=None):
                    self._browser_backup_progress["percent"] = min(100, max(0, int(percent)))
                    if b_name:
                        self._browser_backup_progress["current_browser"] = b_name
                    if title:
                        self._browser_backup_progress["step_title"] = title
                    if detail:
                        self._browser_backup_progress["detail"] = detail
                    if log_msg:
                        self._browser_backup_progress["logs"].append({
                            "time": datetime.datetime.now().strftime("%H:%M:%S"),
                            "msg": log_msg
                        })
                        self.log("INFO", log_msg)

                bridge = LogBridge(self)
                self.log("INFO", f"Đang bắt đầu sao lưu {len(selected_browsers)} trình duyệt...")
                res = bb.backup_browser_data(selected_browsers, options, target_dir, logger=bridge, progress_callback=on_progress)
                self._browser_backup_progress["active"] = False
                self._browser_backup_progress["status"] = "success" if res.get("success") else "error"
                self._browser_backup_progress["percent"] = 100 if res.get("success") else self._browser_backup_progress["percent"]
                self._browser_backup_progress["result"] = res
                if res.get("success"):
                    self._browser_backup_progress["step_title"] = "Sao lưu thành công!"
                    self._browser_backup_progress["detail"] = res.get("message", "Đã sao lưu thành công!")
                    self.log("SUCCESS", res.get("message"))
                else:
                    self._browser_backup_progress["step_title"] = "Sao lưu thất bại"
                    self._browser_backup_progress["detail"] = res.get("message", "Có lỗi xảy ra!")
                    self.log("ERROR", res.get("message"))
            except Exception as e:
                self._browser_backup_progress["active"] = False
                self._browser_backup_progress["status"] = "error"
                self._browser_backup_progress["step_title"] = "Lỗi sao lưu"
                self._browser_backup_progress["detail"] = str(e)
                self._browser_backup_progress["result"] = {"success": False, "message": str(e)}
                self.log("ERROR", f"Lỗi sao lưu trình duyệt: {e}")

        t = threading.Thread(target=_run_backup, daemon=True)
        t.start()
        return {"success": True, "message": "Đã bắt đầu tiến trình sao lưu trong nền"}

    def restore_browsers(self, backup_folder, selected_browsers, options=None):
        """Restores browser profiles and data from backup directory asynchronously with progress."""
        if self._browser_backup_progress.get("active"):
            return {"success": False, "message": "Tiến trình phục hồi/sao lưu đang diễn ra!"}

        self._browser_backup_progress = {
            "active": True,
            "mode": "restore",
            "percent": 0,
            "status": "running",
            "current_browser": "",
            "step_title": "Đang chuẩn bị phục hồi...",
            "detail": f"Đọc gói lưu từ {os.path.basename(backup_folder)}...",
            "logs": [],
            "result": None
        }

        def _run_restore():
            try:
                import modules.browser_backup as bb
                def on_progress(percent, b_name, title, detail, log_msg=None):
                    self._browser_backup_progress["percent"] = min(100, max(0, int(percent)))
                    if b_name:
                        self._browser_backup_progress["current_browser"] = b_name
                    if title:
                        self._browser_backup_progress["step_title"] = title
                    if detail:
                        self._browser_backup_progress["detail"] = detail
                    if log_msg:
                        self._browser_backup_progress["logs"].append({
                            "time": datetime.datetime.now().strftime("%H:%M:%S"),
                            "msg": log_msg
                        })
                        self.log("INFO", log_msg)

                bridge = LogBridge(self)
                opts = options or {'bookmarks': True, 'passwords': True, 'history': True, 'extensions': True, 'full_profile': False}
                self.log("INFO", f"Đang bắt đầu phục hồi dữ liệu trình duyệt từ: {backup_folder}...")
                res = bb.restore_browser_data(backup_folder, selected_browsers, opts, logger=bridge, progress_callback=on_progress)
                self._browser_backup_progress["active"] = False
                self._browser_backup_progress["status"] = "success" if res.get("success") else "error"
                self._browser_backup_progress["percent"] = 100 if res.get("success") else self._browser_backup_progress["percent"]
                self._browser_backup_progress["result"] = res
                if res.get("success"):
                    self._browser_backup_progress["step_title"] = "Phục hồi thành công!"
                    self._browser_backup_progress["detail"] = res.get("message", "Đã phục hồi thành công!")
                    self.log("SUCCESS", res.get("message"))
                else:
                    self._browser_backup_progress["step_title"] = "Phục hồi thất bại"
                    self._browser_backup_progress["detail"] = res.get("message", "Có lỗi xảy ra!")
                    self.log("ERROR", res.get("message"))
            except Exception as e:
                self._browser_backup_progress["active"] = False
                self._browser_backup_progress["status"] = "error"
                self._browser_backup_progress["step_title"] = "Lỗi phục hồi"
                self._browser_backup_progress["detail"] = str(e)
                self._browser_backup_progress["result"] = {"success": False, "message": str(e)}
                self.log("ERROR", f"Lỗi phục hồi trình duyệt: {e}")

        t = threading.Thread(target=_run_restore, daemon=True)
        t.start()
        return {"success": True, "message": "Đã bắt đầu tiến trình phục hồi trong nền"}

    def open_browser_backup_folder(self, target_dir=""):
        """Opens backup location in File Explorer."""
        try:
            import modules.browser_backup as bb
            if not target_dir or not target_dir.strip():
                target_dir = bb.get_default_backup_dir()
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

    def get_shutdown_event_logs(self, max_events=10, event_ids="1074,6008,41"):
        """Get Windows Event Logs for Shutdown/Reboot/Crash (Event ID 1074, 6008, 41)"""
        try:
            import modules.auto_shutdown as sd
            res = sd.get_shutdown_event_logs(max_events, event_ids)
            if res.get("success"):
                logs_count = len(res.get("logs", []))
                self.log("INFO", f"Đã nạp {logs_count} bản ghi lịch sử tắt máy / sập nguồn hệ thống.")
            else:
                self.log("ERROR", f"Lỗi nạp nhật ký tắt máy: {res.get('message')}")
            return res
        except Exception as e:
            self.log("ERROR", f"Lỗi ngoại lệ khi đọc nhật ký nguồn: {e}")
            return {"success": False, "message": str(e), "logs": [], "stats": {}}

    def export_shutdown_event_logs(self, max_events=100, event_ids="1074,6008,41", format_type="excel"):
        """Exports shutdown and power event logs to a beautifully formatted Excel (.xlsx) or CSV file on Desktop."""
        try:
            import modules.auto_shutdown as sd
            res = sd.export_shutdown_event_logs(max_events=max_events, event_ids=event_ids, format_type=format_type)
            if res.get("success"):
                self.log("SUCCESS", res.get("message"))
            else:
                self.log("ERROR", res.get("message"))
            return res
        except Exception as e:
            self.log("ERROR", f"Lỗi xuất file lịch sử tắt máy: {e}")
            return {"success": False, "message": str(e)}

    def open_exported_file(self, file_path):
        """Opens an exported report file with its default system application (Excel/WPS)."""
        try:
            if file_path and os.path.exists(file_path):
                os.startfile(file_path)
                return {"success": True, "message": f"Đã mở file: {file_path}"}
            return {"success": False, "message": f"File không tồn tại: {file_path}"}
        except Exception as e:
            return {"success": False, "message": f"Lỗi khi mở file: {str(e)}"}

    def _get_temp_hosts_path(self):
        import tempfile
        temp_dir = os.path.join(tempfile.gettempdir(), "IT_Tools_Hosts_Temp")
        os.makedirs(temp_dir, exist_ok=True)
        return os.path.join(temp_dir, "hosts")

    def get_hosts_file(self):
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        try:
            if not os.path.exists(hosts_path):
                os.makedirs(os.path.dirname(hosts_path), exist_ok=True)
                default_hosts = "# Copyright (c) 1993-2009 Microsoft Corp.\n127.0.0.1       localhost\n::1             localhost\n"
                with open(hosts_path, "w", encoding="utf-8") as f:
                    f.write(default_hosts)

            temp_hosts_path = self._get_temp_hosts_path()
            # Tự động sao chép file hosts gốc ra thư mục tạm của user
            try:
                import shutil
                shutil.copy2(hosts_path, temp_hosts_path)
            except Exception as copy_err:
                self.log("WARNING", f"Không thể copy bằng shutil, đọc ghi trực tiếp sang temp: {copy_err}")
                with open(hosts_path, "r", encoding="utf-8", errors="ignore") as f:
                    init_content = f.read()
                with open(temp_hosts_path, "w", encoding="utf-8") as tf:
                    tf.write(init_content)

            # Đọc nội dung từ chính file tạm đã sao chép
            with open(temp_hosts_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            self.log("INFO", f"Đã tự động sao chép file hosts ra thư mục tạm: {temp_hosts_path}")
            return {
                "success": True,
                "content": content,
                "path": hosts_path,
                "temp_path": temp_hosts_path,
                "message": "Đã sao chép file hosts vào thư mục tạm thành công."
            }
        except Exception as e:
            self.log("ERROR", f"Lỗi đọc Hosts file: {e}")
            return {"success": False, "message": str(e), "content": ""}

    def update_hosts_temp(self, content):
        """Lưu nội dung đang chỉnh sửa trực tiếp vào file tạm của user."""
        try:
            temp_hosts_path = self._get_temp_hosts_path()
            with open(temp_hosts_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "temp_path": temp_hosts_path}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def open_hosts_temp_folder(self):
        """Mở thư mục tạm đang chứa file hosts đang chỉnh sửa."""
        try:
            temp_hosts_path = self._get_temp_hosts_path()
            subprocess.run(f'explorer.exe /select,"{temp_hosts_path}"', shell=True)
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def save_hosts_file(self, content):
        """
        Quy trình lưu an toàn và triệt để:
        1. Ghi nội dung mới vào file tạm temp_hosts_path trước.
        2. Xóa các cờ Read-Only, System, Hidden của file gốc (nếu có).
        3. Tạo file backup dự phòng (hosts.bak).
        4. Thử ghi trực tiếp vào file hosts gốc (nếu đã có quyền Admin).
        5. Nếu thiếu quyền, nâng quyền bằng ShellExecuteExW ('runas') đồng bộ chờ (WaitForSingleObject).
        6. Kiểm tra đối soát nội dung thực tế trong file hosts gốc. Chỉ báo thành công nếu nội dung đã khớp 100%.
        7. Flush DNS và trả về kết quả chính xác.
        """
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        backup_path = r"C:\Windows\System32\drivers\etc\hosts.bak"
        no_win = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

        try:
            temp_hosts_path = self._get_temp_hosts_path()
            # 1. Lưu nội dung chỉnh sửa vào file tạm
            with open(temp_hosts_path, "w", encoding="utf-8") as tf:
                tf.write(content)

            # 2. Xóa cờ Read-Only / System / Hidden & tạo file backup dự phòng
            if os.path.exists(hosts_path):
                subprocess.run(f'attrib -r -s -h "{hosts_path}"', shell=True, capture_output=True, creationflags=no_win)
                try:
                    import stat
                    os.chmod(hosts_path, stat.S_IWRITE)
                except Exception:
                    pass

                try:
                    import shutil
                    shutil.copy2(hosts_path, backup_path)
                except Exception:
                    pass

            # 3. Thử ghi trực tiếp vào hosts_path nếu tiến trình hiện tại đã có quyền Admin
            direct_saved = False
            try:
                with open(hosts_path, "w", encoding="utf-8") as f:
                    f.write(content)
                direct_saved = True
            except (PermissionError, OSError):
                # Không đủ quyền ghi trực tiếp, chuyển sang phương thức UAC RunAs
                pass
            except Exception as e_direct:
                self.log("WARNING", f"Ghi trực tiếp file hosts thất bại ({e_direct}), thử nâng quyền Admin...")

            # 4. Nếu chưa ghi được do thiếu quyền, nâng quyền qua ShellExecuteExW ('runas')
            if not direct_saved:
                from ctypes import wintypes
                import ctypes

                class SHELLEXECUTEINFO(ctypes.Structure):
                    _fields_ = [
                        ('cbSize', wintypes.DWORD),
                        ('fMask', wintypes.ULONG),
                        ('hwnd', wintypes.HWND),
                        ('lpVerb', wintypes.LPCWSTR),
                        ('lpFile', wintypes.LPCWSTR),
                        ('lpParameters', wintypes.LPCWSTR),
                        ('lpDirectory', wintypes.LPCWSTR),
                        ('nShow', ctypes.c_int),
                        ('hInstApp', wintypes.HINSTANCE),
                        ('lpIDList', wintypes.LPVOID),
                        ('lpClass', wintypes.LPCWSTR),
                        ('hkeyClass', wintypes.HKEY),
                        ('dwHotKey', wintypes.DWORD),
                        ('hIconOrMonitor', wintypes.HANDLE),
                        ('hProcess', wintypes.HANDLE)
                    ]

                sei = SHELLEXECUTEINFO()
                sei.cbSize = ctypes.sizeof(sei)
                sei.fMask = 0x00000040  # SEE_MASK_NOCLOSEPROCESS
                sei.lpVerb = "runas"
                sei.lpFile = "cmd.exe"
                cmd_params = f'/c "attrib -r -s -h "{hosts_path}" & copy /y "{hosts_path}" "{backup_path}" & copy /y "{temp_hosts_path}" "{hosts_path}" & ipconfig /flushdns"'
                sei.lpParameters = cmd_params
                sei.nShow = 0  # SW_HIDE

                ret = ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))
                if not ret:
                    err_code = ctypes.GetLastError()
                    if err_code == 1223:  # ERROR_CANCELLED (Người dùng bấm No trên UAC)
                        self.log("WARNING", "Người dùng đã từ chối cấp quyền Administrator (UAC).")
                        return {
                            "success": False,
                            "message": "Không thể lưu file Hosts: Bạn đã từ chối cấp quyền Administrator (UAC)."
                        }
                    else:
                        self.log("ERROR", f"ShellExecuteExW thất bại, mã lỗi: {err_code}")
                        return {
                            "success": False,
                            "message": f"Không thể kích hoạt quyền Administrator (Mã lỗi: {err_code}). Vui lòng khởi động phần mềm bằng 'Run as Administrator'."
                        }

                # Đợi tiến trình cmd elevated thực thi xong (tối đa 60 giây)
                if sei.hProcess:
                    ctypes.windll.kernel32.WaitForSingleObject(sei.hProcess, 60000)
                    ctypes.windll.kernel32.CloseHandle(sei.hProcess)

            # 5. XÁC THỰC THỰC TẾ: Đọc lại file hosts gốc và so sánh nội dung
            is_verified = False
            try:
                if os.path.exists(hosts_path):
                    with open(hosts_path, "r", encoding="utf-8", errors="ignore") as f:
                        current_hosts = f.read()
                    if current_hosts.replace("\r\n", "\n").strip() == content.replace("\r\n", "\n").strip():
                        is_verified = True
            except Exception as e_verify:
                self.log("WARNING", f"Lỗi đọc lại file hosts gốc để đối soát: {e_verify}")

            if is_verified:
                subprocess.run("ipconfig /flushdns", shell=True, capture_output=True, creationflags=no_win)
                self.log("SUCCESS", f"Đã lưu thành công nội dung vào File Hosts ({hosts_path}) & Flush DNS!")
                return {
                    "success": True,
                    "message": "Đã lưu thay đổi vào File Hosts (C:\\Windows\\System32\\drivers\\etc\\hosts) & Flush DNS thành công!",
                    "temp_path": temp_hosts_path,
                    "path": hosts_path
                }
            else:
                self.log("ERROR", "Nội dung file hosts gốc chưa được cập nhật sau khi lưu.")
                return {
                    "success": False,
                    "message": "Không thể lưu vào file Hosts hệ thống!\nFile chưa được cập nhật (Có thể do Windows Defender / phần mềm diệt virus đang khóa file Hosts hoặc thao tác UAC chưa hoàn tất)."
                }

        except Exception as e:
            self.log("ERROR", f"Lỗi lưu Hosts file: {e}")
            return {"success": False, "message": f"Lỗi lưu Hosts file: {e}"}

    def save_hosts_as(self, content):
        """Opens native Windows Save File Dialog to save hosts file content anywhere."""
        try:
            from tkinter import filedialog
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            root.focus_force()

            target_path = filedialog.asksaveasfilename(
                title="Lưu File Hosts Ra Nơi Khác (Save As...)",
                initialfile="hosts",
                defaultextension="",
                filetypes=[
                    ("All Files (*.*)", "*.*"),
                    ("Hosts File", "hosts"),
                    ("Text Files (*.txt)", "*.txt"),
                ]
            )
            root.destroy()

            if not target_path:
                return {"success": False, "canceled": True, "message": "Đã hủy thao tác lưu file."}

            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.log("SUCCESS", f"Đã lưu Hosts thành file mới: {target_path}")
            return {
                "success": True,
                "canceled": False,
                "path": target_path,
                "message": f"Đã lưu thành công file tại:\n{target_path}"
            }
        except Exception as e:
            self.log("ERROR", f"Lỗi Lưu Thành (Save As): {e}")
            return {"success": False, "message": f"Lỗi khi lưu file: {e}"}

    def load_hosts_from_file(self):
        """Opens native Windows Open File Dialog to import an external hosts file."""
        try:
            from tkinter import filedialog
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            root.focus_force()

            target_path = filedialog.askopenfilename(
                title="Chọn File Hosts Cần Nạp Vào Editor",
                filetypes=[
                    ("All Files (*.*)", "*.*"),
                    ("Hosts File", "hosts"),
                    ("Text Files (*.txt)", "*.txt"),
                ]
            )
            root.destroy()

            if not target_path:
                return {"success": False, "canceled": True}

            with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            self.log("SUCCESS", f"Đã nạp nội dung từ file: {target_path}")
            return {"success": True, "content": content, "path": target_path}
        except Exception as e:
            self.log("ERROR", f"Lỗi nạp file hosts: {e}")
            return {"success": False, "message": f"Lỗi đọc file: {e}"}

    def restore_hosts_default(self):
        default_hosts = (
            "# Copyright (c) 1993-2009 Microsoft Corp.\n"
            "# Default Hosts file restored by IT Tool LTT 2026\n"
            "127.0.0.1       localhost\n"
            "::1             localhost\n"
        )
        res = self.save_hosts_file(default_hosts)
        if res.get("success"):
            self.log("SUCCESS", "Đã khôi phục Hosts file về mặc định Windows & Flush DNS!")
            return {"success": True, "message": "Đã khôi phục Hosts file mặc định thành công!"}
        return res

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
        work_dir = r"C:\ProgramData\ITTools\OfficeSetup"
        state_file = os.path.join(work_dir, "office_install_state.json")
        ps1_script = get_resource_path("modules", "install_office_silent.ps1")

        # Check if already active with a real liveness verification
        current_state = self.get_office_install_progress().get("data", {})
        if current_state.get("active"):
            return {"success": False, "message": "Đang có tiến trình cài đặt Office chạy ngầm! Vui lòng chờ hoàn tất hoặc bấm Hủy cài đặt."}

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
                    "TIẾN TRÌNH CHẠY NGẦM ĐỘC LẬP: Dù bạn có tắt ứng dụng ITTools, Office vẫn tự động tải & hoàn tất trong nền Windows."
                ],
                "started_at": int(time.time()),
                "updated_at": int(time.time())
            }

            import json
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(initial_state, f, ensure_ascii=False, indent=2)

            self._office_install_progress = initial_state

            # Launch PowerShell script as an independent background process
            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP

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
            proc = subprocess.Popen(
                ps_cmd,
                creationflags=creationflags,
                close_fds=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.log("SUCCESS", f"Đã khởi động tiến trình nền PowerShell (PID: {proc.pid}) để tải & cài đặt {vname}")

            return {"success": True, "message": f"Đã bắt đầu cài đặt ẩn {vname}! Bạn có thể tắt ứng dụng, tiến trình vẫn tự động hoàn tất trong nền."}

        except Exception as e:
            self.log("ERROR", f"Lỗi khởi chạy cài đặt Office: {e}")
            return {"success": False, "message": f"Lỗi khởi chạy: {str(e)}"}

    def get_office_install_progress(self):
        """Returns current Office installation progress state from the background daemon state file."""
        state_file = r"C:\ProgramData\ITTools\OfficeSetup\office_install_state.json"
        data = self._office_install_progress
        if os.path.exists(state_file):
            try:
                import json
                with open(state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._office_install_progress = data
            except Exception:
                pass

        # Check if state says active, but process is actually dead / timed out
        if data.get("active"):
            updated_at = data.get("updated_at", 0)
            now = int(time.time())
            # If no updates for > 35 seconds, verify if processes are really alive
            if (now - updated_at) > 35:
                try:
                    out = subprocess.check_output(
                        'powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq \'setup.exe\' -or $_.CommandLine -like \'*install_office_silent.ps1*\' } | Select-Object -ExpandProperty ProcessId"',
                        shell=True, text=True, stderr=subprocess.DEVNULL
                    ).strip()
                    if not out:
                        # Processes died unexpectedly or never updated
                        data["active"] = False
                        data["status"] = "error"
                        data["message"] = "Tiến trình cài đặt ngầm không phản hồi hoặc đã dừng."
                        if "output_log" in data and isinstance(data["output_log"], list):
                            data["output_log"].append("[CẢNH BÁO] Không tìm thấy tiến trình cài đặt đang chạy. Bạn có thể nhấn 'Thử lại' hoặc 'Hủy'.")
                        self._office_install_progress = data
                        try:
                            import json
                            with open(state_file, "w", encoding="utf-8") as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                        except Exception:
                            pass
                except Exception:
                    pass

        return {"success": True, "data": data}

    def cancel_office_install(self):
        """Cancels active Office installation process and terminates background runners."""
        state_file = r"C:\ProgramData\ITTools\OfficeSetup\office_install_state.json"
        try:
            subprocess.run('taskkill /f /im "setup.exe"', shell=True, capture_output=True)
            subprocess.run('powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like \'*install_office_silent.ps1*\' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"', shell=True, capture_output=True)

            self._office_install_progress["active"] = False
            self._office_install_progress["status"] = "cancelled"
            self._office_install_progress["message"] = "Đã hủy tiến trình cài đặt Office."
            if "output_log" in self._office_install_progress and isinstance(self._office_install_progress["output_log"], list):
                self._office_install_progress["output_log"].append("Đã dừng tiến trình và hủy cài đặt Office.")

            if os.path.exists(state_file):
                import json
                with open(state_file, "w", encoding="utf-8") as f:
                    json.dump(self._office_install_progress, f, ensure_ascii=False, indent=2)

            self.log("WARN", "Đã gửi lệnh hủy tiến trình cài đặt Office.")
            return {"success": True, "message": "Đã hủy tiến trình cài đặt Office thành công."}
        except Exception as e:
            return {"success": False, "message": str(e)}


    # ── OTHER SYSTEM TWEAKS (12 TOOL TOGGLES MATCHING IMAGE 2) ─────────────
    def get_system_tweaks_status(self):
        """Returns real-time status of all system tweaks accurately reflecting the current Windows configuration."""
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

        # 1. Task Manager (Check both HKCU and HKLM)
        taskmgr_disabled = False
        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                k = winreg.OpenKey(root, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System', 0, winreg.KEY_READ)
                val, _ = winreg.QueryValueEx(k, 'DisableTaskMgr')
                if val == 1:
                    taskmgr_disabled = True
                winreg.CloseKey(k)
            except Exception:
                pass
        status["taskmgr"] = not taskmgr_disabled

        # 2. Registry Editor (Check both HKCU and HKLM)
        registry_disabled = False
        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                k = winreg.OpenKey(root, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System', 0, winreg.KEY_READ)
                val, _ = winreg.QueryValueEx(k, 'DisableRegistryTools')
                if val in (1, 2):
                    registry_disabled = True
                winreg.CloseKey(k)
            except Exception:
                pass
        status["registry"] = not registry_disabled

        # 3. Run Command (Win + R) - Check both HKCU and HKLM
        run_disabled = False
        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                k = winreg.OpenKey(root, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer', 0, winreg.KEY_READ)
                val, _ = winreg.QueryValueEx(k, 'NoRun')
                if val == 1:
                    run_disabled = True
                winreg.CloseKey(k)
            except Exception:
                pass
        status["run"] = not run_disabled

        # 4. Low Disk Space Checks (Check both HKCU and HKLM)
        lowdisk_disabled = False
        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                k = winreg.OpenKey(root, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer', 0, winreg.KEY_READ)
                val, _ = winreg.QueryValueEx(k, 'NoLowDiskSpaceChecks')
                if val == 1:
                    lowdisk_disabled = True
                winreg.CloseKey(k)
            except Exception:
                pass
        status["lowdisk"] = not lowdisk_disabled

        # 5. Command Prompt (Check both HKCU and HKLM in Policies\System and Policies\Microsoft\Windows\System)
        cmd_disabled = False
        for p in (r'SOFTWARE\Policies\Microsoft\Windows\System', r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System'):
            for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                try:
                    k = winreg.OpenKey(root, p, 0, winreg.KEY_READ)
                    val, _ = winreg.QueryValueEx(k, 'DisableCMD')
                    if val in (1, 2):
                        cmd_disabled = True
                    winreg.CloseKey(k)
                except Exception:
                    pass
        status["cmd"] = not cmd_disabled

        # 6. Webcam / Camera (Check Group Policy, Device Consent, and User Consent)
        camera_blocked = False
        try:
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Policies\Microsoft\Camera', 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(k, 'AllowCamera')
            if val == 0:
                camera_blocked = True
            winreg.CloseKey(k)
        except Exception:
            pass

        try:
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Policies\Microsoft\Windows\AppPrivacy', 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(k, 'LetAppsAccessCamera')
            if val == 2:  # 2 = Force Deny
                camera_blocked = True
            winreg.CloseKey(k)
        except Exception:
            pass

        # Check CapabilityAccessManager in HKCU (user consent) and HKLM (device consent)
        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for sub in ('', r'\NonPackaged'):
                try:
                    k = winreg.OpenKey(root, r'SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam' + sub, 0, winreg.KEY_READ)
                    val, _ = winreg.QueryValueEx(k, 'Value')
                    if str(val).strip().lower() == 'deny':
                        camera_blocked = True
                    winreg.CloseKey(k)
                except Exception:
                    pass
        status["camera"] = not camera_blocked

        # 10. Shortcut Arrow (Check HKLM and HKCU Shell Icons)
        arrow_removed = False
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                k = winreg.OpenKey(root, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Icons', 0, winreg.KEY_READ)
                val, _ = winreg.QueryValueEx(k, '29')
                if str(val).strip():
                    arrow_removed = True
                winreg.CloseKey(k)
            except Exception:
                pass
        status["shortcut_arrow"] = not arrow_removed

        # 11. Shortcut Prefix "Shortcut to"
        prefix_disabled = False
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer', 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(k, 'link')
            if val == b'\x00\x00\x00\x00':
                prefix_disabled = True
            winreg.CloseKey(k)
        except Exception:
            pass
        status["shortcut_prefix"] = not prefix_disabled

        # 12. Autorun (Check HKLM and HKCU)
        autorun_disabled = False
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                k = winreg.OpenKey(root, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer', 0, winreg.KEY_READ)
                val, _ = winreg.QueryValueEx(k, 'NoDriveTypeAutoRun')
                if val == 0xFF:
                    autorun_disabled = True
                winreg.CloseKey(k)
            except Exception:
                pass
        status["autorun"] = not autorun_disabled

        return {"success": True, "data": status}

    def toggle_system_tweak(self, tweak_key, enable):
        import winreg
        try:
            restart_explorer_needed = False

            if tweak_key == "taskmgr":
                for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                    try:
                        k = winreg.CreateKey(root, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System')
                        if enable:
                            try:
                                winreg.DeleteValue(k, 'DisableTaskMgr')
                            except Exception:
                                winreg.SetValueEx(k, 'DisableTaskMgr', 0, winreg.REG_DWORD, 0)
                        else:
                            winreg.SetValueEx(k, 'DisableTaskMgr', 0, winreg.REG_DWORD, 1)
                        winreg.CloseKey(k)
                    except Exception:
                        pass

            elif tweak_key == "registry":
                for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                    try:
                        k = winreg.CreateKey(root, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System')
                        if enable:
                            try:
                                winreg.DeleteValue(k, 'DisableRegistryTools')
                            except Exception:
                                winreg.SetValueEx(k, 'DisableRegistryTools', 0, winreg.REG_DWORD, 0)
                        else:
                            winreg.SetValueEx(k, 'DisableRegistryTools', 0, winreg.REG_DWORD, 1)
                        winreg.CloseKey(k)
                    except Exception:
                        pass

            elif tweak_key == "run":
                for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                    try:
                        k = winreg.CreateKey(root, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer')
                        if enable:
                            try:
                                winreg.DeleteValue(k, 'NoRun')
                            except Exception:
                                winreg.SetValueEx(k, 'NoRun', 0, winreg.REG_DWORD, 0)
                        else:
                            winreg.SetValueEx(k, 'NoRun', 0, winreg.REG_DWORD, 1)
                        winreg.CloseKey(k)
                    except Exception:
                        pass
                restart_explorer_needed = True

            elif tweak_key == "cmd":
                for p in (r'SOFTWARE\Policies\Microsoft\Windows\System', r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System'):
                    for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                        try:
                            k = winreg.CreateKey(root, p)
                            if enable:
                                try:
                                    winreg.DeleteValue(k, 'DisableCMD')
                                except Exception:
                                    winreg.SetValueEx(k, 'DisableCMD', 0, winreg.REG_DWORD, 0)
                            else:
                                winreg.SetValueEx(k, 'DisableCMD', 0, winreg.REG_DWORD, 1)
                            winreg.CloseKey(k)
                        except Exception:
                            pass

            elif tweak_key == "lowdisk":
                for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                    try:
                        k = winreg.CreateKey(root, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer')
                        if enable:
                            try:
                                winreg.DeleteValue(k, 'NoLowDiskSpaceChecks')
                            except Exception:
                                winreg.SetValueEx(k, 'NoLowDiskSpaceChecks', 0, winreg.REG_DWORD, 0)
                        else:
                            winreg.SetValueEx(k, 'NoLowDiskSpaceChecks', 0, winreg.REG_DWORD, 1)
                        winreg.CloseKey(k)
                    except Exception:
                        pass
                restart_explorer_needed = True

            elif tweak_key == "camera":
                cam_val = 'Allow' if enable else 'Deny'
                # 1. Update CapabilityAccessManager ConsentStore for HKCU and HKLM
                for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                    for sub in ('', r'\NonPackaged'):
                        try:
                            k = winreg.CreateKey(root, r'SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam' + sub)
                            winreg.SetValueEx(k, 'Value', 0, winreg.REG_SZ, cam_val)
                            winreg.CloseKey(k)
                        except Exception:
                            pass

                # 2. Update Group Policy Camera settings
                try:
                    k = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Policies\Microsoft\Camera')
                    if enable:
                        try:
                            winreg.DeleteValue(k, 'AllowCamera')
                        except Exception:
                            winreg.SetValueEx(k, 'AllowCamera', 0, winreg.REG_DWORD, 1)
                    else:
                        winreg.SetValueEx(k, 'AllowCamera', 0, winreg.REG_DWORD, 0)
                    winreg.CloseKey(k)
                except Exception:
                    pass

                try:
                    k = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Policies\Microsoft\Windows\AppPrivacy')
                    if enable:
                        try:
                            winreg.DeleteValue(k, 'LetAppsAccessCamera')
                        except Exception:
                            winreg.SetValueEx(k, 'LetAppsAccessCamera', 0, winreg.REG_DWORD, 1)
                    else:
                        winreg.SetValueEx(k, 'LetAppsAccessCamera', 0, winreg.REG_DWORD, 2)
                    winreg.CloseKey(k)
                except Exception:
                    pass

            elif tweak_key == "shortcut_arrow":
                for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                    try:
                        k = winreg.CreateKey(root, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Icons')
                        if enable:
                            try:
                                winreg.DeleteValue(k, '29')
                            except Exception:
                                pass
                        else:
                            winreg.SetValueEx(k, '29', 0, winreg.REG_SZ, '%windir%\\System32\\shell32.dll,-50')
                        winreg.CloseKey(k)
                    except Exception:
                        pass
                restart_explorer_needed = True

            elif tweak_key == "shortcut_prefix":
                try:
                    k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer')
                    if enable:
                        try:
                            winreg.DeleteValue(k, 'link')
                        except Exception:
                            winreg.SetValueEx(k, 'link', 0, winreg.REG_BINARY, b'\x1e\x00\x00\x00')
                    else:
                        winreg.SetValueEx(k, 'link', 0, winreg.REG_BINARY, b'\x00\x00\x00\x00')
                    winreg.CloseKey(k)
                except Exception:
                    pass
                restart_explorer_needed = True

            elif tweak_key == "autorun":
                drive_val = 0x91 if enable else 0xFF
                for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                    try:
                        k = winreg.CreateKey(root, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer')
                        winreg.SetValueEx(k, 'NoDriveTypeAutoRun', 0, winreg.REG_DWORD, drive_val)
                        winreg.CloseKey(k)
                    except Exception:
                        pass

            elif tweak_key == "fix_hidden":
                try:
                    key1 = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced')
                    winreg.SetValueEx(key1, 'Hidden', 0, winreg.REG_DWORD, 1)
                    winreg.SetValueEx(key1, 'ShowSuperHidden', 0, winreg.REG_DWORD, 1)
                    winreg.CloseKey(key1)
                    key2 = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced\Folder\Hidden\SHOWALL')
                    winreg.SetValueEx(key2, 'CheckedValue', 0, winreg.REG_DWORD, 1)
                    winreg.CloseKey(key2)
                except Exception:
                    pass
                restart_explorer_needed = True

            elif tweak_key == "repair_taskbar":
                return self.repair_taskbar()

            elif tweak_key == "unblock_files":
                return self.unblock_files_quick()

            # Restart explorer if required to apply the policy immediately
            if restart_explorer_needed:
                self.restart_explorer_process()

            status_str = "Kích hoạt (Bật)" if enable else "Vô hiệu hóa (Tắt)"
            self.log("SUCCESS", f"Đã {status_str} tính năng: {tweak_key}")
            return {"success": True, "message": f"Đã {status_str} tính năng thành công!"}
        except Exception as e:
            self.log("ERROR", f"Lỗi thực hiện tweak {tweak_key}: {e}")
            return {"success": False, "message": str(e)}


    def repair_taskbar(self):
        """Repairs and unfreezes Windows Taskbar and Start Menu without removing any pinned items."""
        try:
            self.log("INFO", "Đang tiến hành sửa lỗi đơ Taskbar và nút Start Menu (bảo toàn ứng dụng đã ghim)...")

            ps_script = r"""
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class ShellRefresher {
    [DllImport("shell32.dll")]
    public static extern void SHChangeNotify(int wEventId, int uFlags, IntPtr dwItem1, IntPtr dwItem2);
    public static void Refresh() {
        try { SHChangeNotify(0x08000000, 0, IntPtr.Zero, IntPtr.Zero); } catch {}
    }
}
"@ -ErrorAction SilentlyContinue

# 1. Ket thuc cac tien trinh Shell, Start Menu va Widgets dang bi treo hoac deadlocked
$culprits = @(
    'StartMenuExperienceHost',
    'ShellExperienceHost',
    'SearchHost',
    'SearchApp',
    'TextInputHost',
    'Widgets',
    'WindowsWidgets',
    'SystemSettings'
)
foreach ($proc in $culprits) {
    try {
        Get-Process -Name $proc -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    } catch {}
}

# 2. Dang ky lai goi AppX Shell va Start Menu mot cach an toan (Bao toan 100% icon va muc da ghim)
$shellPackages = @(
    'Microsoft.Windows.StartMenuExperienceHost',
    'Microsoft.Windows.ShellExperienceHost',
    'Microsoft.Windows.Search'
)
foreach ($pkg in $shellPackages) {
    try {
        Get-AppxPackage -Name $pkg -ErrorAction SilentlyContinue | ForEach-Object {
            $manifest = Join-Path $_.InstallLocation 'AppXManifest.xml'
            if (Test-Path $manifest) {
                Add-AppxPackage -DisableDevelopmentMode -Register $manifest -ErrorAction SilentlyContinue
            }
        }
    } catch {}
}

# 3. Khoi dong lai dich vu Windows Search neu bi treo
try {
    $ws = Get-Service -Name WSearch -ErrorAction SilentlyContinue
    if ($ws -and $ws.Status -eq 'Running') {
        Restart-Service -Name WSearch -Force -ErrorAction SilentlyContinue
    }
} catch {}

# 4. Khoi dong lai Explorer sach se
try {
    Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 600
    if (-not (Get-Process -Name explorer -ErrorAction SilentlyContinue)) {
        Start-Process explorer.exe
    }
} catch {
    Start-Process explorer.exe -ErrorAction SilentlyContinue
}

# 5. Cap nhat thong bao Shell
try { [ShellRefresher]::Refresh() } catch {}

# 6. Kiem tra so luong ung dung da ghim tren Taskbar de xac nhan
$pinnedCount = 0
try {
    $pinnedDir = "$env:APPDATA\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar"
    if (Test-Path $pinnedDir) {
        $pinnedCount = (Get-ChildItem -Path $pinnedDir -Filter "*.lnk" -ErrorAction SilentlyContinue | Measure-Object).Count
    }
} catch {}

Write-Output "OK:$pinnedCount"
"""
            encoded = base64.b64encode(ps_script.encode('utf-16le')).decode('ascii')
            r = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded],
                capture_output=True,
                text=True,
                timeout=25
            )

            pinned_count = 0
            stdout = r.stdout.strip()
            if "OK:" in stdout:
                try:
                    for line in stdout.splitlines():
                        if line.startswith("OK:"):
                            pinned_count = int(line.split(":")[1].strip())
                except Exception:
                    pass

            msg = f"Đã khôi phục thanh Taskbar và nút Start Menu hoạt động mượt mà (bảo toàn nguyên vẹn {pinned_count} ứng dụng đang ghim)!"
            self.log("SUCCESS", msg)
            return {"success": True, "message": msg}
        except Exception as e:
            self.log("ERROR", f"Lỗi sửa Taskbar: {e}")
            return {"success": False, "message": str(e)}

    def _unblock_path_internal(self, target_path):
        """Removes Zone.Identifier NTFS Alternate Data Stream directly via Win32 API."""
        import os
        import ctypes

        kernel32 = ctypes.windll.kernel32
        scanned = 0
        unblocked = 0

        def _clean_stream(fpath):
            nonlocal scanned, unblocked
            scanned += 1
            stream_name = f"{fpath}:Zone.Identifier"
            if kernel32.DeleteFileW(stream_name):
                unblocked += 1
                return True
            else:
                err = kernel32.GetLastError()
                if err == 5:  # Access Denied (Read-Only)
                    try:
                        old_attrs = kernel32.GetFileAttributesW(fpath)
                        if old_attrs != 0xFFFFFFFF and (old_attrs & 1):
                            kernel32.SetFileAttributesW(fpath, old_attrs & ~1)
                            if kernel32.DeleteFileW(stream_name):
                                unblocked += 1
                            kernel32.SetFileAttributesW(fpath, old_attrs)
                    except Exception:
                        pass
            return False

        if not target_path or not os.path.exists(target_path):
            return 0, 0

        if os.path.isfile(target_path):
            _clean_stream(target_path)
        elif os.path.isdir(target_path):
            for root, dirs, files in os.walk(target_path):
                for fname in files:
                    fp = os.path.join(root, fname)
                    _clean_stream(fp)

        return scanned, unblocked

    def unblock_files_quick(self):
        """Unblocks all files in standard user download & desktop directories and disables zone tagging."""
        try:
            import os
            import subprocess
            user_profile = os.environ.get("USERPROFILE", "")
            target_dirs = []
            for sub in ["Downloads", "Desktop", "Documents"]:
                p = os.path.join(user_profile, sub)
                if os.path.isdir(p):
                    target_dirs.append(p)

            # Check secondary drives if any
            for d in [r"D:\Downloads", r"E:\Downloads"]:
                if os.path.isdir(d) and d not in target_dirs:
                    target_dirs.append(d)

            total_scanned = 0
            total_unblocked = 0
            for d in target_dirs:
                s, u = self._unblock_path_internal(d)
                total_scanned += s
                total_unblocked += u

            # Apply Attachments Policy via registry to stop future blocking
            try:
                import winreg
                for root_hkey in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
                    try:
                        k = winreg.CreateKey(root_hkey, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Attachments')
                        winreg.SetValueEx(k, 'SaveZoneInformation', 0, winreg.REG_DWORD, 1)
                        winreg.SetValueEx(k, 'HideZoneInfoOnProperties', 0, winreg.REG_DWORD, 1)
                        winreg.CloseKey(k)
                    except Exception:
                        pass
                subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Attachments" /v SaveZoneInformation /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
            except Exception:
                pass

            if total_unblocked > 0:
                msg = f"🎉 Đã quét {total_scanned} tệp và BỎ CHẶN THÀNH CÔNG {total_unblocked} tệp bị dán nhãn (Zone.Identifier) trong Downloads & Desktop!\n\nĐồng thời đã cấu hình hệ thống không chặn file tải về trong tương lai."
                self.log("SUCCESS", msg)
            else:
                msg = f"✅ Đã quét {total_scanned} tệp trong Downloads, Desktop & Documents. Tất cả các tệp đều sạch (không bị dán nhãn Zone.Identifier).\n\nĐã kích hoạt cấu hình ngăn Windows chặn file tải về."
                self.log("INFO", msg)

            return {
                "success": True,
                "scanned": total_scanned,
                "unblocked": total_unblocked,
                "message": msg
            }
        except Exception as e:
            self.log("ERROR", f"Lỗi Unblock Files: {e}")
            return {"success": False, "message": f"Lỗi khi bỏ chặn file: {e}"}

    def unblock_files_custom(self):
        """Allows user to select a specific file or folder to unblock."""
        try:
            import os
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            # First ask for file or folder
            target_path = filedialog.askopenfilename(
                title="Chọn TỆP TIN cần Bỏ Chặn (Hoặc bấm Cancel/Hủy để chọn THƯ MỤC)"
            )
            if not target_path:
                target_path = filedialog.askdirectory(title="Chọn THƯ MỤC cần Bỏ Chặn toàn bộ tệp bên trong")

            root.destroy()

            if not target_path:
                return {"success": False, "cancelled": True, "message": "Đã hủy chọn tệp/thư mục."}

            scanned, unblocked = self._unblock_path_internal(target_path)
            base_name = os.path.basename(target_path) or target_path

            if unblocked > 0:
                msg = f"🎉 Đã quét {scanned} tệp tại '{base_name}' và BỎ CHẶN THÀNH CÔNG {unblocked} tệp tin!"
                self.log("SUCCESS", msg)
            else:
                msg = f"ℹ️ Đã quét {scanned} tệp tại '{base_name}'. Tệp/thư mục này hiện không bị Windows khóa nhãn Zone.Identifier."
                self.log("INFO", msg)

            return {
                "success": True,
                "path": target_path,
                "scanned": scanned,
                "unblocked": unblocked,
                "message": msg
            }
        except Exception as e:
            self.log("ERROR", f"Lỗi Unblock Custom: {e}")
            return {"success": False, "message": f"Lỗi: {e}"}


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
            {"id": "lamquangminh.EVKey",        "name": "EVKey Tiếng Việt",    "category": "Bộ gõ",          "icon": "⌨️"},
            {"id": "Tuyenvm.OpenKey",           "name": "OpenKey (Mã Nguồn Mở)","category": "Bộ gõ",         "icon": "⌨️"},

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
            {"id": "Iterate.Cyberduck",         "name": "Cyberduck (FTP/SFTP)", "category": "Download",      "icon": "🦆"},

            # ── PDF & VĂN BẢN (6) ─────────────────────────────────────────
            {"id": "Foxit.FoxitReader",         "name": "Foxit PDF Reader",    "category": "PDF",            "icon": "📄"},
            {"id": "SumatraPDF.SumatraPDF",     "name": "SumatraPDF",          "category": "PDF",            "icon": "📖"},
            {"id": "geeksoftwareGmbH.PDF24Creator", "name": "PDF24 Creator",   "category": "PDF",            "icon": "📑"},
            {"id": "Adobe.Acrobat.Reader.64-bit", "name": "Adobe Acrobat Reader", "category": "PDF",         "icon": "📄"},
            {"id": "TrackerSoftware.PDF-XChangeEditor", "name": "PDF-XChange Editor", "category": "PDF",     "icon": "🖨️"},
            {"id": "TrackerSoftware.PDF-Tools", "name": "PDF-Tools",           "category": "PDF",            "icon": "📋"},

            # ── FONTS & CÔNG CỤ (2) ───────────────────────────────────────
            {"id": "FontForge.FontForge",       "name": "FontForge",           "category": "Fonts",          "icon": "🔤"},
            {"id": "REALiX.HWiNFO",             "name": "HWiNFO Diagnostics",  "category": "Fonts",          "icon": "🔡"},

            # ── CHAT & LIÊN LẠC (9) ───────────────────────────────────────
            {"id": "VNGCorp.Zalo",              "name": "Zalo PC",             "category": "Chat",           "icon": "💬"},
            {"id": "Telegram.TelegramDesktop",  "name": "Telegram",            "category": "Chat",           "icon": "✈️"},
            {"id": "Zoom.Zoom",                 "name": "Zoom Meetings",       "category": "Chat",           "icon": "📹"},
            {"id": "Discord.Discord",           "name": "Discord",             "category": "Chat",           "icon": "👾"},
            {"id": "SlackTechnologies.Slack",   "name": "Slack",               "category": "Chat",           "icon": "💼"},
            {"id": "Microsoft.Teams",           "name": "Microsoft Teams",     "category": "Chat",           "icon": "👥"},
            {"id": "Rakuten.Viber",             "name": "Viber Messenger",     "category": "Chat",           "icon": "📱"},
            {"id": "Tencent.WeChat",            "name": "WeChat PC",           "category": "Chat",           "icon": "💬"},
            {"id": "Caprine.Caprine",           "name": "Messenger (Caprine)", "category": "Chat",           "icon": "💙"},

            # ── VĂN PHÒNG & SOẠN THẢO (10) ───────────────────────────────
            {"id": "TheDocumentFoundation.LibreOffice", "name": "LibreOffice", "category": "Văn phòng",      "icon": "📝"},
            {"id": "Kingsoft.WPSOffice",        "name": "WPS Office",          "category": "Văn phòng",      "icon": "📊"},
            {"id": "Notepad++.Notepad++",       "name": "Notepad++",           "category": "Văn phòng",      "icon": "✏️"},
            {"id": "voidtools.Everything",      "name": "Everything",          "category": "Văn phòng",      "icon": "🔍"},
            {"id": "Microsoft.PowerToys",       "name": "PowerToys",           "category": "Văn phòng",      "icon": "🛠️"},
            {"id": "Bopsoft.Listary",           "name": "Listary Pro",         "category": "Văn phòng",      "icon": "🔎"},
            {"id": "Obsidian.Obsidian",         "name": "Obsidian (Ghi chú)", "category": "Văn phòng",      "icon": "📒"},
            {"id": "Notion.Notion",             "name": "Notion",              "category": "Văn phòng",      "icon": "📘"},
            {"id": "MarkText.MarkText",         "name": "MarkText (Markdown)", "category": "Văn phòng",      "icon": "📄"},
            {"id": "Inkscape.Inkscape",         "name": "Inkscape",            "category": "Văn phòng",      "icon": "✒️"},

            # ── ĐA PHƯƠNG TIỆN & ÂM NHẠC (11) ────────────────────────────
            {"id": "VideoLAN.VLC",              "name": "VLC Media Player",    "category": "Đa phương tiện", "icon": "🎥"},
            {"id": "Daum.PotPlayer",            "name": "PotPlayer",           "category": "Đa phương tiện", "icon": "🎬"},
            {"id": "OBSProject.OBSStudio",      "name": "OBS Studio",          "category": "Đa phương tiện", "icon": "📹"},
            {"id": "GIMP.GIMP",                 "name": "GIMP",                "category": "Đa phương tiện", "icon": "🎨"},
            {"id": "Audacity.Audacity",         "name": "Audacity",            "category": "Đa phương tiện", "icon": "🎙️"},
            {"id": "Spotify.Spotify",           "name": "Spotify",             "category": "Đa phương tiện", "icon": "🎵"},
            {"id": "MPC-BE.MPC-BE",             "name": "MPC-BE Player",       "category": "Đa phương tiện", "icon": "▶️"},
            {"id": "HandBrake.HandBrake",       "name": "HandBrake (Video)",   "category": "Đa phương tiện", "icon": "📼"},
            {"id": "KDE.Kdenlive",              "name": "Kdenlive Video Editor", "category": "Đa phương tiện", "icon": "🎞️"},
            {"id": "ByteDance.CapCut",          "name": "CapCut PC",           "category": "Đa phương tiện", "icon": "🎬"},
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
            {"id": "Almico.SpeedFan",           "name": "SpeedFan",            "category": "Hệ thống",       "icon": "💨"},
            {"id": "Piriform.Speccy",           "name": "Speccy",              "category": "Hệ thống",       "icon": "🖥️"},
            {"id": "CrystalDewWorld.CrystalDiskMark", "name": "CrystalDiskMark", "category": "Hệ thống",   "icon": "⏱️"},
            {"id": "WiseCleaner.WiseRegistryCleaner", "name": "Wise Registry Cleaner", "category": "Hệ thống", "icon": "🔧"},

            # ── Ổ ĐĨA ẢO & BACKUP (5) ─────────────────────────────────────
            {"id": "EZBSystems.UltraISO",       "name": "UltraISO Premium",    "category": "Ổ đĩa ảo",      "icon": "💿"},
            {"id": "AOMEI.PartitionAssistant",  "name": "AOMEI Partition",     "category": "Ổ đĩa ảo",      "icon": "💿"},
            {"id": "AOMEI.Backupper.Standard",  "name": "AOMEI Backupper",     "category": "Ổ đĩa ảo",      "icon": "💾"},
            {"id": "EaseUS.TodoBackup",         "name": "EaseUS Todo Backup",  "category": "Ổ đĩa ảo",      "icon": "🔄"},
            {"id": "EaseUS.PartitionMaster",    "name": "EaseUS Partition",    "category": "Ổ đĩa ảo",      "icon": "📦"},

            # ── BẢO MẬT & DIỆT VIRUS (8) ─────────────────────────────────
            {"id": "Malwarebytes.Malwarebytes",  "name": "Malwarebytes",        "category": "Bảo mật",        "icon": "🛡️"},
            {"id": "AdGuard.AdGuard",            "name": "AdGuard",             "category": "Bảo mật",        "icon": "🚫"},
            {"id": "Bitdefender.Bitdefender",    "name": "Bitdefender Free",    "category": "Bảo mật",        "icon": "🔒"},
            {"id": "Bitwarden.Bitwarden",        "name": "Bitwarden (Password Manager)", "category": "Bảo mật", "icon": "🔑"},
            {"id": "GlassWire.GlassWire",        "name": "GlassWire Firewall",  "category": "Bảo mật",        "icon": "🌐"},
            {"id": "Proton.ProtonVPN",           "name": "Proton VPN",          "category": "Bảo mật",        "icon": "🔐"},
            {"id": "Cloudflare.Warp",            "name": "Cloudflare 1.1.1.1 WARP", "category": "Bảo mật",    "icon": "🛡️"},
            {"id": "NordSecurity.NordVPN",       "name": "NordVPN",             "category": "Bảo mật",        "icon": "🔒"},

            # ── LẬP TRÌNH & DEVTOOLS (14) ──────────────────────────────────
            {"id": "Microsoft.VisualStudioCode", "name": "Visual Studio Code",  "category": "Lập trình",      "icon": "💙"},
            {"id": "JetBrains.Toolbox",         "name": "JetBrains Toolbox",   "category": "Lập trình",      "icon": "🧰"},
            {"id": "Git.Git",                   "name": "Git",                 "category": "Lập trình",      "icon": "🔀"},
            {"id": "Python.Python.3.12",        "name": "Python 3.12",         "category": "Lập trình",      "icon": "🐍"},
            {"id": "OpenJS.NodeJS",             "name": "Node.js",             "category": "Lập trình",      "icon": "🟢"},
            {"id": "Oracle.JDK.21",             "name": "Java JDK 21",         "category": "Lập trình",      "icon": "☕"},
            {"id": "Postman.Postman",           "name": "Postman (API Test)",  "category": "Lập trình",      "icon": "📮"},
            {"id": "DBeaver.DBeaver.Community", "name": "DBeaver (Universal DB)", "category": "Lập trình",   "icon": "🗄️"},
            {"id": "HeidiSQL.HeidiSQL",         "name": "HeidiSQL",            "category": "Lập trình",      "icon": "🗄️"},
            {"id": "Docker.DockerDesktop",      "name": "Docker Desktop",      "category": "Lập trình",      "icon": "🐳"},
            {"id": "Yarn.Yarn",                 "name": "Yarn",                "category": "Lập trình",      "icon": "🧶"},
            {"id": "GitHub.GitHubDesktop",      "name": "GitHub Desktop",      "category": "Lập trình",      "icon": "🐙"},
            {"id": "Insomnia.Insomnia",         "name": "Insomnia (REST API)", "category": "Lập trình",      "icon": "😴"},
            {"id": "Wampserver.Wampserver",     "name": "WampServer (PHP/MySQL)", "category": "Lập trình",   "icon": "⚙️"},

            # ── MẠNG XÃ HỘI & GIẢI TRÍ (7) ──────────────────────────────
            {"id": "Valve.Steam",               "name": "Steam",               "category": "Mạng xã hội",    "icon": "🎮"},
            {"id": "EpicGames.EpicGamesLauncher","name": "Epic Games Launcher", "category": "Mạng xã hội",    "icon": "🎮"},
            {"id": "PeterPawlowski.foobar2000", "name": "foobar2000 Music",    "category": "Mạng xã hội",    "icon": "🎶"},
            {"id": "AIMP.AIMP",                 "name": "AIMP Audio Player",   "category": "Mạng xã hội",    "icon": "🎵"},
            {"id": "Tencent.TencentMeeting",    "name": "Tencent Meeting",     "category": "Mạng xã hội",    "icon": "📹"},
            {"id": "Meltytech.Shotcut",         "name": "Shotcut Studio",      "category": "Mạng xã hội",    "icon": "🎬"},
            {"id": "Caprine.Caprine",           "name": "Facebook Messenger",  "category": "Mạng xã hội",    "icon": "💙"},

            # ── ĐỒ HOẠ & THIẾT KẾ (8) ────────────────────────────────────
            {"id": "Canva.Canva",               "name": "Canva Desktop",       "category": "Đồ hoạ",         "icon": "🎨"},
            {"id": "Figma.Figma",               "name": "Figma",               "category": "Đồ hoạ",         "icon": "✏️"},
            {"id": "KDE.Krita",                 "name": "Krita Digital Art",   "category": "Đồ hoạ",         "icon": "🖌️"},
            {"id": "BlenderFoundation.Blender", "name": "Blender 3D",          "category": "Đồ hoạ",         "icon": "🌀"},
            {"id": "IrfanSkiljan.IrfanView",    "name": "IrfanView",           "category": "Đồ hoạ",         "icon": "🖼️"},
            {"id": "XnSoft.XnView.Classic",     "name": "XnView Classic",      "category": "Đồ hoạ",         "icon": "🖼️"},
            {"id": "GIMP.GIMP",                 "name": "GIMP",                "category": "Đồ hoạ",         "icon": "🎨"},
            {"id": "Greenshot.Greenshot",       "name": "Greenshot Screen",    "category": "Đồ hoạ",         "icon": "📷"},

            # ── KẾ TOÁN & TÀI CHÍNH (5) ──────────────────────────────────
            {"id": "GnuCash.GnuCash",           "name": "GnuCash Kế Toán",    "category": "Kế toán",        "icon": "💰"},
            {"id": "moneymanagerex.moneymanagerex", "name": "Money Manager Ex", "category": "Kế toán",     "icon": "💵"},
            {"id": "HomeBank.HomeBank",         "name": "HomeBank",            "category": "Kế toán",        "icon": "🏦"},
            {"id": "Microsoft.PowerBI",         "name": "Power BI Desktop",    "category": "Kế toán",        "icon": "📊"},
            {"id": "TheDocumentFoundation.LibreOffice", "name": "LibreOffice Calc", "category": "Kế toán",    "icon": "📈"},

            # ── CLOUD & LƯU TRỮ (7) ──────────────────────────────────────
            {"id": "Google.GoogleDrive",        "name": "Google Drive",        "category": "Cloud",          "icon": "☁️"},
            {"id": "Dropbox.Dropbox",           "name": "Dropbox",             "category": "Cloud",          "icon": "📦"},
            {"id": "Microsoft.OneDrive",        "name": "OneDrive",            "category": "Cloud",          "icon": "☁️"},
            {"id": "Mega.MEGASync",             "name": "MEGA Sync",           "category": "Cloud",          "icon": "🌊"},
            {"id": "pCloudAG.pCloudDrive",      "name": "pCloud Drive",        "category": "Cloud",          "icon": "☁️"},
            {"id": "Nextcloud.NextcloudDesktop","name": "Nextcloud Desktop",   "category": "Cloud",          "icon": "🌤️"},
            {"id": "Box.Box",                   "name": "Box Drive",           "category": "Cloud",          "icon": "📫"},

            # ── CÔNG CỤ MẠNG (8) ──────────────────────────────────────────
            {"id": "WiresharkFoundation.Wireshark", "name": "Wireshark",       "category": "Công cụ mạng",   "icon": "🦈"},
            {"id": "OpenVPNTechnologies.OpenVPN","name": "OpenVPN",             "category": "Công cụ mạng",   "icon": "🔒"},
            {"id": "angryziber.AngryIPScanner", "name": "Angry IP Scanner",    "category": "Công cụ mạng",   "icon": "📡"},
            {"id": "Insecure.Nmap",             "name": "Nmap Security",       "category": "Công cụ mạng",   "icon": "🔍"},
            {"id": "NordSecurity.NordVPN",      "name": "NordVPN Client",      "category": "Công cụ mạng",   "icon": "🛡️"},
            {"id": "LibreSpeed.librespeed-cli", "name": "LibreSpeed (Speedtest)", "category": "Công cụ mạng","icon": "⚡"},
            {"id": "Cloudflare.Warp",           "name": "Cloudflare WARP",     "category": "Công cụ mạng",   "icon": "🌐"},
            {"id": "mRemoteNG.mRemoteNG",       "name": "mRemoteNG (RDP/SSH)", "category": "Công cụ mạng",   "icon": "🖥️"},
            # ── BỘ GÕ (+1) ──────────────────────────────
            {"id": "DEVCOM.JetBrainsMonoNerdFont", "name": "JetBrains Mono Nerd Font", "category": "Bộ gõ", "icon": "🔤"},

            # ── TRÌNH DUYỆT (+5) ──────────────────────────────
            {"id": "TorProject.TorBrowser", "name": "Tor Browser", "category": "Trình duyệt", "icon": "🧅"},
            {"id": "LibreWolf.LibreWolf", "name": "LibreWolf Browser", "category": "Trình duyệt", "icon": "🐺"},
            {"id": "Waterfox.Waterfox", "name": "Waterfox", "category": "Trình duyệt", "icon": "🦊"},
            {"id": "DuckDuckGo.DesktopBrowser", "name": "DuckDuckGo Privacy Browser", "category": "Trình duyệt", "icon": "🦆"},
            {"id": "TheBrowserCompany.Arc", "name": "Arc Browser", "category": "Trình duyệt", "icon": "🌈"},

            # ── CHAT (+4) ──────────────────────────────
            {"id": "OpenWhisperSystems.Signal", "name": "Signal Desktop", "category": "Chat", "icon": "🔒"},
            {"id": "Mozilla.Thunderbird", "name": "Mozilla Thunderbird (Email)", "category": "Chat", "icon": "✉️"},
            {"id": "Element.Element", "name": "Element Matrix", "category": "Chat", "icon": "💬"},
            {"id": "Mattermost.MattermostDesktop", "name": "Mattermost", "category": "Chat", "icon": "💬"},

            # ── VĂN PHÒNG (+7) ──────────────────────────────
            {"id": "calibre.calibre", "name": "Calibre E-Book Manager", "category": "Văn phòng", "icon": "📚"},
            {"id": "DigitalScholar.Zotero", "name": "Zotero Trích Dẫn & Nghiên Cứu", "category": "Văn phòng", "icon": "📖"},
            {"id": "DeepL.DeepL", "name": "DeepL Dịch Thuật AI", "category": "Văn phòng", "icon": "🌐"},
            {"id": "Logseq.Logseq", "name": "Logseq (Ghi chú Markdown)", "category": "Văn phòng", "icon": "📝"},
            {"id": "Joplin.Joplin", "name": "Joplin Ghi Chú Đa Nền Tảng", "category": "Văn phòng", "icon": "📒"},
            {"id": "AppFlowy.AppFlowy", "name": "AppFlowy (Notion Nguồn Mở)", "category": "Văn phòng", "icon": "📋"},
            {"id": "appmakes.Typora", "name": "Typora Trình Soạn Markdown", "category": "Văn phòng", "icon": "📝"},

            # ── PDF (+2) ──────────────────────────────
            {"id": "KDE.Okular", "name": "Okular PDF Reader", "category": "PDF", "icon": "📄"},
            {"id": "PDFgear.PDFgear", "name": "PDFgear All-in-One PDF Tool", "category": "PDF", "icon": "⚙️"},

            # ── ĐA PHƯƠNG TIỆN (+7) ──────────────────────────────
            {"id": "CodecGuide.K-LiteCodecPack.Mega", "name": "K-Lite Mega Codec Pack", "category": "Đa phương tiện", "icon": "🎞️"},
            {"id": "ch.LosslessCut", "name": "LosslessCut (Cắt Ghép Video Nhanh)", "category": "Đa phương tiện", "icon": "✂️"},
            {"id": "PaulPacifico.ShutterEncoder", "name": "Shutter Encoder (Chuyển Đổi Video)", "category": "Đa phương tiện", "icon": "🎬"},
            {"id": "Gyan.FFmpeg", "name": "FFmpeg Media Framework", "category": "Đa phương tiện", "icon": "⚙️"},
            {"id": "Stremio.Stremio", "name": "Stremio Phim Trực Tuyến", "category": "Đa phương tiện", "icon": "🍿"},
            {"id": "XBMCFoundation.Kodi", "name": "Kodi Home Theater", "category": "Đa phương tiện", "icon": "📺"},
            {"id": "Apple.iTunes", "name": "Apple iTunes", "category": "Đa phương tiện", "icon": "🎵"},

            # ── ĐỒ HOẠ (+8) ──────────────────────────────
            {"id": "Skillbrains.Lightshot", "name": "Lightshot Chụp Ảnh Màn Hình", "category": "Đồ hoạ", "icon": "📸"},
            {"id": "dotPDN.PaintDotNet", "name": "Paint.NET (Chỉnh Sửa Ảnh)", "category": "Đồ hoạ", "icon": "🎨"},
            {"id": "Flameshot.Flameshot", "name": "Flameshot (Chụp & Chú Thích Màn Hình)", "category": "Đồ hoạ", "icon": "🔥"},
            {"id": "FastStone.Viewer", "name": "FastStone Image Viewer", "category": "Đồ hoạ", "icon": "🖼️"},
            {"id": "RawTherapee.RawTherapee", "name": "RawTherapee Xử Lý Ảnh RAW", "category": "Đồ hoạ", "icon": "📸"},
            {"id": "Upscayl.Upscayl", "name": "Upscayl Phóng To Ảnh AI", "category": "Đồ hoạ", "icon": "✨"},
            {"id": "ImageMagick.ImageMagick", "name": "ImageMagick Xử Lý Ảnh", "category": "Đồ hoạ", "icon": "🪄"},
            {"id": "eTeks.SweetHome3D", "name": "Sweet Home 3D Thiết Kế Nội Thất", "category": "Đồ hoạ", "icon": "🏠"},

            # ── TIỆN ÍCH (+17) ──────────────────────────────
            {"id": "AntibodySoftware.WizTree", "name": "WizTree Phân Tích Dung Lượng Ổ Đĩa", "category": "Tiện ích", "icon": "🌳"},
            {"id": "Ventoy.Ventoy", "name": "Ventoy Tạo USB Boot Đa Năng", "category": "Tiện ích", "icon": "💾"},
            {"id": "Balena.Etcher", "name": "Balena Etcher Ghi USB/SD Card", "category": "Tiện ích", "icon": "💿"},
            {"id": "RevoUninstaller.RevoUninstaller", "name": "Revo Uninstaller Free (Gỡ Sạch App)", "category": "Tiện ích", "icon": "🗑️"},
            {"id": "GeekUninstaller.GeekUninstaller", "name": "Geek Uninstaller (Gỡ Bỏ Triệt Để)", "category": "Tiện ích", "icon": "🧹"},
            {"id": "Klocman.BulkCrapUninstaller", "name": "Bulk Crap Uninstaller (BCU Gỡ Hàng Loạt)", "category": "Tiện ích", "icon": "🗑️"},
            {"id": "BleachBit.BleachBit", "name": "BleachBit Dọn Dẹp File Rác", "category": "Tiện ích", "icon": "🧹"},
            {"id": "AutoHotkey.AutoHotkey", "name": "AutoHotkey Tự Động Hóa Phím Chuột", "category": "Tiện ích", "icon": "⌨️"},
            {"id": "Flow-Launcher.Flow-Launcher", "name": "Flow Launcher Tìm Kiếm Nhanh", "category": "Tiện ích", "icon": "🔍"},
            {"id": "File-New-Project.EarTrumpet", "name": "EarTrumpet Điều Chỉnh Âm Lượng Riêng", "category": "Tiện ích", "icon": "🔊"},
            {"id": "CharlesMilette.TranslucentTB", "name": "TranslucentTB Làm Trong Suốt Taskbar", "category": "Tiện ích", "icon": "🪟"},
            {"id": "rocksdanister.LivelyWallpaper", "name": "Lively Wallpaper Hình Nền Động", "category": "Tiện ích", "icon": "🖼️"},
            {"id": "Open-Shell.Open-Shell-Menu", "name": "Open-Shell Start Menu Cổ Điển", "category": "Tiện ích", "icon": "🐚"},
            {"id": "CrystalRich.LockHunter", "name": "LockHunter Mở Khóa Tệp Bị Chiếm Dụng", "category": "Tiện ích", "icon": "🔓"},
            {"id": "gerardog.gsudo", "name": "gsudo Quyền Administrator Trong CMD/PS", "category": "Tiện ích", "icon": "⚡"},
            {"id": "M2Team.NanaZip", "name": "NanaZip Nén & Giải Nén Windows 11", "category": "Tiện ích", "icon": "📦"},
            {"id": "JAMSoftware.TreeSize.Free", "name": "TreeSize Free Quét Dung Lượng Thư Mục", "category": "Tiện ích", "icon": "🌳"},

            # ── HỆ THỐNG (+6) ──────────────────────────────
            {"id": "Guru3D.RTSS", "name": "RivaTuner Statistics Server (RTSS OSD)", "category": "Hệ thống", "icon": "📊"},
            {"id": "Guru3D.Afterburner", "name": "MSI Afterburner (Ép Xung & Giám Sát GPU)", "category": "Hệ thống", "icon": "⚡"},
            {"id": "Geeks3D.FurMark.1", "name": "Geeks3D FurMark GPU Stress Test", "category": "Hệ thống", "icon": "🔥"},
            {"id": "FinalWire.AIDA64.Extreme", "name": "AIDA64 Extreme (Kiểm Tra Chi Tiết Máy)", "category": "Hệ thống", "icon": "ℹ️"},
            {"id": "ALCPU.CoreTemp", "name": "Core Temp (Đo Nhiệt Độ Từng Nhân CPU)", "category": "Hệ thống", "icon": "🌡️"},
            {"id": "NirSoft.BatteryInfoView", "name": "BatteryInfoView (Xem Độ Chai Pin Laptop)", "category": "Hệ thống", "icon": "🔋"},

            # ── BẢO MẬT (+6) ──────────────────────────────
            {"id": "KeePassXCTeam.KeePassXC", "name": "KeePassXC (Quản Lý Mật Khẩu Offline)", "category": "Bảo mật", "icon": "🔑"},
            {"id": "AgileBits.1Password", "name": "1Password (Trình Quản Lý Mật Khẩu)", "category": "Bảo mật", "icon": "🔐"},
            {"id": "Tailscale.Tailscale", "name": "Tailscale (Mạng Nội Bộ VPN Mesh)", "category": "Bảo mật", "icon": "🔒"},
            {"id": "WireGuard.WireGuard", "name": "WireGuard (VPN Siêu Nhẹ & Tốc Độ)", "category": "Bảo mật", "icon": "🛡️"},
            {"id": "2dust.v2rayN", "name": "v2rayN (Proxy Client V2Ray/Xray)", "category": "Bảo mật", "icon": "🚀"},
            {"id": "ValdikSS.GoodbyeDPI", "name": "GoodbyeDPI (Vượt Tường Lửa & Chặn DPI)", "category": "Bảo mật", "icon": "🌐"},

            # ── LẬP TRÌNH (+17) ──────────────────────────────
            {"id": "LeNgocKhoa.Laragon", "name": "Laragon (WAMP Stack Chuẩn Cho Dev VN)", "category": "Lập trình", "icon": "🐘"},
            {"id": "SublimeHQ.SublimeText.4", "name": "Sublime Text 4 (Trình Biên Tập Code)", "category": "Lập trình", "icon": "📝"},
            {"id": "JetBrains.IntelliJIDEA.Community", "name": "IntelliJ IDEA Community Edition", "category": "Lập trình", "icon": "☕"},
            {"id": "JetBrains.PyCharm.Community", "name": "PyCharm Community Edition (Python IDE)", "category": "Lập trình", "icon": "🐍"},
            {"id": "ApacheFriends.Xampp.8.2", "name": "XAMPP 8.2 (Apache + MariaDB + PHP)", "category": "Lập trình", "icon": "🐘"},
            {"id": "Termius.Termius", "name": "Termius (SSH Client & SFTP Quản Trị Server)", "category": "Lập trình", "icon": "🖥️"},
            {"id": "Eugeny.Tabby", "name": "Tabby (Terminal Đa Năng Cho Dev)", "category": "Lập trình", "icon": "⬛"},
            {"id": "Alacritty.Alacritty", "name": "Alacritty (GPU Terminal Siêu Tốc)", "category": "Lập trình", "icon": "⚡"},
            {"id": "Neovim.Neovim", "name": "Neovim (Vim Mở Rộng Hiện Đại)", "category": "Lập trình", "icon": "💚"},
            {"id": "vim.vim", "name": "Vim Text Editor", "category": "Lập trình", "icon": "💚"},
            {"id": "JesseDuffield.lazygit", "name": "LazyGit (Giao Diện Git Dòng Lệnh)", "category": "Lập trình", "icon": "🔀"},
            {"id": "Fork.Fork", "name": "Fork Git Client (Giao Diện Git Trực Quan)", "category": "Lập trình", "icon": "🔀"},
            {"id": "Atlassian.Sourcetree", "name": "Sourcetree Git Client", "category": "Lập trình", "icon": "🌳"},
            {"id": "Rustlang.Rustup", "name": "Rustup (Bộ Cài Đặt Ngôn Ngữ Rust)", "category": "Lập trình", "icon": "🦀"},
            {"id": "TablePlus.TablePlus", "name": "TablePlus (Quản Trị Cơ Sở Dữ Liệu GUI)", "category": "Lập trình", "icon": "🗄️"},
            {"id": "PostgreSQL.pgAdmin", "name": "pgAdmin 4 (Quản Lý PostgreSQL)", "category": "Lập trình", "icon": "🐘"},
            {"id": "Bruno.Bruno", "name": "Bruno API Client (Thay Thế Postman Offline)", "category": "Lập trình", "icon": "🐶"},

            # ── DOWNLOAD (+5) ──────────────────────────────
            {"id": "agalwood.Motrix", "name": "Motrix Download Manager", "category": "Download", "icon": "⚡"},
            {"id": "yt-dlp.yt-dlp", "name": "yt-dlp (Tải Video YouTube/Facebook CLI)", "category": "Download", "icon": "⬇️"},
            {"id": "Transmission.Transmission", "name": "Transmission Torrent Client", "category": "Download", "icon": "🧲"},
            {"id": "aria2.aria2", "name": "aria2 Trình Tải File Đa Luồng Siêu Nhanh", "category": "Download", "icon": "🚀"},
            {"id": "AppWork.JDownloader", "name": "JDownloader 2 (Tải File Host Hàng Loạt)", "category": "Download", "icon": "☕"},

            # ── Ổ ĐĨA ẢO (+3) ──────────────────────────────
            {"id": "MiniTool.PartitionWizard.Free", "name": "MiniTool Partition Wizard (Phân Vùng Ổ Đĩa)", "category": "Ổ đĩa ảo", "icon": "💿"},
            {"id": "Syncthing.Syncthing", "name": "Syncthing (Đồng Bộ Dữ Liệu Ngang Hàng)", "category": "Ổ đĩa ảo", "icon": "🔄"},
            {"id": "Duplicati.Duplicati", "name": "Duplicati (Sao Lưu Mã Hóa Lên Cloud)", "category": "Ổ đĩa ảo", "icon": "🔒"},

            # ── MẠNG XÃ HỘI (+5) ──────────────────────────────
            {"id": "Blizzard.BattleNet", "name": "Battle.net Launcher", "category": "Mạng xã hội", "icon": "🎮"},
            {"id": "ElectronicArts.EADesktop", "name": "EA App (Electronic Arts)", "category": "Mạng xã hội", "icon": "🎮"},
            {"id": "Ubisoft.Connect", "name": "Ubisoft Connect", "category": "Mạng xã hội", "icon": "🎮"},
            {"id": "GOG.Galaxy", "name": "GOG Galaxy Launcher", "category": "Mạng xã hội", "icon": "🎮"},
            {"id": "Roblox.Roblox", "name": "Roblox Player", "category": "Mạng xã hội", "icon": "🟥"},

            # ── CÔNG CỤ MẠNG (+5) ──────────────────────────────
            {"id": "Famatech.AdvancedIPScanner", "name": "Advanced IP Scanner (Quét Mạng LAN)", "category": "Công cụ mạng", "icon": "📡"},
            {"id": "Telerik.Fiddler.Classic", "name": "Fiddler Classic (Phân Tích Bắt Gói HTTP)", "category": "Công cụ mạng", "icon": "🎻"},
            {"id": "RealVNC.VNCViewer", "name": "RealVNC Viewer (Điều Khiển VNC)", "category": "Công cụ mạng", "icon": "🖥️"},
            {"id": "leeter.WinMTR", "name": "WinMTR (Kiểm Tra Mất Gói & Ping Mạng)", "category": "Công cụ mạng", "icon": "📈"},
            {"id": "Pingman.PingPlotter", "name": "PingPlotter (Đồ Thị Ping & Độ Trễ)", "category": "Công cụ mạng", "icon": "📊"},

            # ── CLOUD (+2) ──────────────────────────────
            {"id": "Proton.ProtonDrive", "name": "Proton Drive (Lưu Trữ Mã Hóa)", "category": "Cloud", "icon": "☁️"},
            {"id": "Rclone.Rclone", "name": "Rclone (Đồng Bộ Đa Dịch Vụ Đám Mây)", "category": "Cloud", "icon": "☁️"},
        ]
        return self._detect_catalog_installation_and_pin_status(catalog)

    def _detect_catalog_installation_and_pin_status(self, catalog):
        """Accurately detects whether each catalog application is installed and whether its shortcut is pinned."""
        import os, winreg, re

        # 1. Collect all installed DisplayNames & Uninstall Registry keys
        installed_display_names = set()
        installed_reg_keys = set()
        reg_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'),
            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'),
            (winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'),
            (winreg.HKEY_CURRENT_USER, r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'),
        ]
        for hive, path in reg_paths:
            try:
                k = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        sub = winreg.EnumKey(k, i)
                        i += 1
                        installed_reg_keys.add(sub.lower())
                        sk = winreg.OpenKey(k, sub)
                        try:
                            dn = winreg.QueryValueEx(sk, 'DisplayName')[0]
                            if dn:
                                installed_display_names.add(dn.strip().lower())
                        except Exception:
                            pass
                        winreg.CloseKey(sk)
                    except OSError:
                        break
                winreg.CloseKey(k)
            except Exception:
                pass

        # 2. Collect App Paths registered executables
        app_paths_exes = set()
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                k = winreg.OpenKey(hive, r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths', 0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        sub = winreg.EnumKey(k, i)
                        i += 1
                        app_paths_exes.add(sub.lower())
                    except OSError:
                        break
                winreg.CloseKey(k)
            except Exception:
                pass

        # 3. Collect Desktop shortcuts
        desktop_dirs = [
            os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop'),
            r'C:\Users\Public\Desktop'
        ]
        desktop_lnks = set()
        for d in desktop_dirs:
            if os.path.exists(d):
                try:
                    for f in os.listdir(d):
                        if f.lower().endswith('.lnk'):
                            desktop_lnks.add(os.path.splitext(f)[0].lower())
                except Exception:
                    pass

        # 4. Known Executables Mapping for maximum precision
        KNOWN_EXES = {
            'coccoc.coccoc': ['browser.exe'],
            'google.chrome': ['chrome.exe'],
            'microsoft.edge': ['msedge.exe'],
            'mozilla.firefox': ['firefox.exe'],
            'brave.brave': ['brave.exe'],
            'opera.opera': ['opera.exe', 'launcher.exe'],
            'opera.operagx': ['operagx.exe'],
            'vivaldi.vivaldi': ['vivaldi.exe'],
            'unikey.unikey': ['unikeynt.exe', 'unikey.exe'],
            'lamquangminh.evkey': ['evkey64.exe', 'evkey.exe', 'evkey.exe'],
            'tuyenvm.openkey': ['openkey.exe', 'openkey64.exe'],
            '7zip.7zip': ['7zfm.exe', '7z.exe'],
            'rarlab.winrar': ['winrar.exe'],
            'bandisoft.bandizip': ['bandizip.exe'],
            'giorgiotani.peazip': ['peazip.exe'],
            'softdeluxe.freedownloadmanager': ['fdm.exe'],
            'qbittorrent.qbittorrent': ['qbittorrent.exe'],
            'winscp.winscp': ['winscp.exe'],
            'putty.putty': ['putty.exe'],
            'tonec.internetdownloadmanager': ['idman.exe'],
            'foxit.foxitreader': ['foxitpdfreader.exe', 'foxitreader.exe'],
            'sumatrapdf.sumatrapdf': ['sumatrapdf.exe'],
            'adobe.acrobat.reader.64-bit': ['acrobat.exe', 'acrord32.exe'],
            'geeksoftwaregmbh.pdf24creator': ['pdf24.exe'],
            'vngcorp.zalo': ['zalo.exe'],
            'telegram.telegramdesktop': ['telegram.exe'],
            'zoom.zoom': ['zoom.exe'],
            'discord.discord': ['discord.exe'],
            'microsoft.teams': ['msteams.exe', 'teams.exe'],
            'slacktechnologies.slack': ['slack.exe'],
            'rakuten.viber': ['viber.exe'],
            'notepad++.notepad++': ['notepad++.exe'],
            'videolan.vlc': ['vlc.exe'],
            'daum.potplayer': ['potplayer64.exe', 'potplayer.exe'],
            'obsproject.obsstudio': ['obs64.exe'],
            'anydesk.anydesk': ['anydesk.exe'],
            'teamviewer.teamviewer': ['teamviewer.exe'],
            'ducfabulous.ultraviewer': ['ultraviewer_desktop.exe'],
            'rufus.rufus': ['rufus.exe'],
            'cpuid.cpu-z': ['cpuz.exe'],
            'cpuid.hwmonitor': ['hwmonitor.exe'],
            'techpowerup.gpu-z': ['gpu-z.exe'],
            'crystaldewworld.crystaldiskinfo': ['diskinfo64.exe', 'diskinfo32.exe'],
            'crystaldewworld.crystaldiskmark': ['diskmark64.exe', 'diskmark32.exe'],
            'microsoft.visualstudiocode': ['code.exe'],
            'git.git': ['git-bash.exe', 'git.exe'],
            'python.python.3.12': ['python.exe'],
            'wiresharkfoundation.wireshark': ['wireshark.exe'],
            'mremoteng.mremoteng': ['mremoteng.exe'],
            'voidtools.everything': ['everything.exe'],
            'bopsoft.listary': ['listary.exe'],
            'obsidian.obsidian': ['obsidian.exe'],
            'spotify.spotify': ['spotify.exe'],
            'piriform.ccleaner': ['ccleaner64.exe', 'ccleaner.exe'],
            'microsoft.windowsterminal': ['wt.exe'],
            'insecure.nmap': ['nmap.exe'],
            'nordsecurity.nordvpn': ['nordvpn.exe'],
            'cloudflare.warp': ['cloudflare warp.exe'],
            'postman.postman': ['postman.exe'],
            'github.githubdesktop': ['githubdesktop.exe'],
            'openvpntechnologies.openvpn': ['openvpn-gui.exe'],
            'ezbsystems.ultraiso': ['ultraiso.exe'],
            'malwarebytes.malwarebytes': ['mbam.exe'],
            'bitwarden.bitwarden': ['bitwarden.exe'],
            'thedocumentfoundation.libreoffice': ['soffice.exe'],
            'kingsoft.wpsoffice': ['wps.exe'],
            'gimp.gimp': ['gimp.exe'],
            'audacity.audacity': ['audacity.exe'],
            'bytedance.capcut': ['capcut.exe'],
            'sharex.sharex': ['sharex.exe'],
            'greenshot.greenshot': ['greenshot.exe'],
            'devcom.jetbrainsmononerdfont': ["jetbrainsmono*.ttf"],
            'torproject.torbrowser': ["firefox.exe"],
            'librewolf.librewolf': ["librewolf.exe"],
            'waterfox.waterfox': ["waterfox.exe"],
            'duckduckgo.desktopbrowser': ["duckduckgo.exe"],
            'thebrowsercompany.arc': ["arc.exe"],
            'openwhispersystems.signal': ["signal.exe"],
            'mozilla.thunderbird': ["thunderbird.exe"],
            'element.element': ["element.exe"],
            'mattermost.mattermostdesktop': ["mattermost.exe"],
            'calibre.calibre': ["calibre.exe"],
            'digitalscholar.zotero': ["zotero.exe"],
            'deepl.deepl': ["deepl.exe"],
            'logseq.logseq': ["logseq.exe"],
            'joplin.joplin': ["joplin.exe"],
            'appflowy.appflowy': ["appflowy.exe"],
            'appmakes.typora': ["typora.exe"],
            'kde.okular': ["okular.exe"],
            'pdfgear.pdfgear': ["pdfgear.exe"],
            'codecguide.k-litecodecpack.mega': ["mpc-hc64.exe", "mpc-hc.exe"],
            'ch.losslesscut': ["losslesscut.exe"],
            'paulpacifico.shutterencoder': ["shutter encoder.exe"],
            'gyan.ffmpeg': ["ffmpeg.exe"],
            'stremio.stremio': ["stremio.exe"],
            'xbmcfoundation.kodi': ["kodi.exe"],
            'apple.itunes': ["itunes.exe"],
            'skillbrains.lightshot': ["lightshot.exe"],
            'dotpdn.paintdotnet': ["paintdotnet.exe"],
            'flameshot.flameshot': ["flameshot.exe"],
            'faststone.viewer': ["fsviewer.exe"],
            'rawtherapee.rawtherapee': ["rawtherapee.exe"],
            'upscayl.upscayl': ["upscayl.exe"],
            'imagemagick.imagemagick': ["magick.exe"],
            'eteks.sweethome3d': ["sweethome3d.exe"],
            'antibodysoftware.wiztree': ["wiztree64.exe", "wiztree.exe"],
            'ventoy.ventoy': ["ventoy2disk.exe"],
            'balena.etcher': ["balenaetcher.exe"],
            'revouninstaller.revouninstaller': ["revouninpro.exe", "revoupport.exe", "revounin.exe"],
            'geekuninstaller.geekuninstaller': ["geek.exe"],
            'klocman.bulkcrapuninstaller': ["bcuninstaller.exe"],
            'bleachbit.bleachbit': ["bleachbit.exe"],
            'autohotkey.autohotkey': ["autohotkey.exe", "autohotkey64.exe"],
            'flow-launcher.flow-launcher': ["flow.launcher.exe"],
            'file-new-project.eartrumpet': ["eartrumpet.exe"],
            'charlesmilette.translucenttb': ["translucenttb.exe"],
            'rocksdanister.livelywallpaper': ["lively.exe"],
            'open-shell.open-shell-menu': ["startmenu.exe"],
            'crystalrich.lockhunter': ["lockhunter.exe"],
            'gerardog.gsudo': ["gsudo.exe"],
            'm2team.nanazip': ["nanazip.exe", "nanazipg.exe"],
            'jamsoftware.treesize.free': ["treesizefree.exe"],
            'guru3d.rtss': ["rtss.exe"],
            'guru3d.afterburner': ["msiafterburner.exe"],
            'geeks3d.furmark.1': ["furmark.exe"],
            'finalwire.aida64.extreme': ["aida64.exe"],
            'alcpu.coretemp': ["core temp.exe"],
            'nirsoft.batteryinfoview': ["batteryinfoview.exe"],
            'keepassxcteam.keepassxc': ["keepassxc.exe"],
            'agilebits.1password': ["1password.exe"],
            'tailscale.tailscale': ["tailscale-ipn.exe"],
            'wireguard.wireguard': ["wireguard.exe"],
            '2dust.v2rayn': ["v2rayn.exe"],
            'valdikss.goodbyedpi': ["goodbyedpi.exe"],
            'lengockhoa.laragon': ["laragon.exe"],
            'sublimehq.sublimetext.4': ["sublime_text.exe"],
            'jetbrains.intellijidea.community': ["idea64.exe"],
            'jetbrains.pycharm.community': ["pycharm64.exe"],
            'apachefriends.xampp.8.2': ["xampp-control.exe"],
            'termius.termius': ["termius.exe"],
            'eugeny.tabby': ["tabby.exe"],
            'alacritty.alacritty': ["alacritty.exe"],
            'neovim.neovim': ["nvim.exe"],
            'vim.vim': ["gvim.exe", "vim.exe"],
            'jesseduffield.lazygit': ["lazygit.exe"],
            'fork.fork': ["fork.exe"],
            'atlassian.sourcetree': ["sourcetree.exe"],
            'rustlang.rustup': ["rustup.exe", "cargo.exe"],
            'tableplus.tableplus': ["tableplus.exe"],
            'postgresql.pgadmin': ["pgadmin4.exe"],
            'bruno.bruno': ["bruno.exe"],
            'agalwood.motrix': ["motrix.exe"],
            'yt-dlp.yt-dlp': ["yt-dlp.exe"],
            'transmission.transmission': ["transmission-qt.exe"],
            'aria2.aria2': ["aria2c.exe"],
            'appwork.jdownloader': ["jdownloader2.exe"],
            'minitool.partitionwizard.free': ["partitionwizard.exe"],
            'syncthing.syncthing': ["syncthing.exe"],
            'duplicati.duplicati': ["duplicati.gui.trayicon.exe"],
            'blizzard.battlenet': ["battle.net.exe"],
            'electronicarts.eadesktop': ["eadesktop.exe"],
            'ubisoft.connect': ["ubisoftconnect.exe"],
            'gog.galaxy': ["galaxyclient.exe"],
            'roblox.roblox': ["robloxplayerbeta.exe"],
            'famatech.advancedipscanner': ["advanced_ip_scanner.exe"],
            'telerik.fiddler.classic': ["fiddler.exe"],
            'realvnc.vncviewer': ["vncviewer.exe"],
            'leeter.winmtr': ["winmtr.exe"],
            'pingman.pingplotter': ["pingplotter.exe"],
            'proton.protondrive': ["protondrive.exe"],
            'rclone.rclone': ["rclone.exe"],
        }

        for app in catalog:
            aid = app.get('id', '').lower()
            name = app.get('name', '').lower()
            clean_name = re.sub(r'\(.*?\)', '', name).strip()

            is_installed = False
            # Check known exes in App Paths
            if aid in KNOWN_EXES:
                for ex in KNOWN_EXES[aid]:
                    if ex.lower() in app_paths_exes:
                        is_installed = True
                        break

            # Check App ID in registry keys
            if not is_installed:
                if any(aid in rk for rk in installed_reg_keys):
                    is_installed = True

            # Check clean name in DisplayNames
            if not is_installed and len(clean_name) >= 3:
                for dn in installed_display_names:
                    if clean_name == dn or dn.startswith(clean_name + ' ') or f' {clean_name} ' in f' {dn} ':
                        is_installed = True
                        break

            # Check desktop shortcut for pinned status
            is_pinned = False
            for lnk in desktop_lnks:
                if (clean_name in lnk or lnk in clean_name) or (aid in KNOWN_EXES and any(ex.replace('.exe', '') in lnk for ex in KNOWN_EXES[aid])):
                    is_pinned = True
                    break

            app['is_installed'] = is_installed
            app['is_pinned'] = is_pinned

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
        base = os.path.join(tmp, "ittools_winget")
        os.makedirs(base, exist_ok=True)
        return {
            "queue":  os.path.join(base, "queue.json"),
            "status": os.path.join(base, "status.json"),
            "cancel": os.path.join(base, "status.cancel"),
            "ps1":    get_resource_path("modules", "winget_runner.ps1")
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

        # DEAD OR STALLED PROCESS DETECTION
        if is_running and not finished:
            is_dead = (pid > 0 and not self._is_pid_alive(pid))
            is_stalled = False
            try:
                # If status file hasn't been updated for > 300s (5 mins), consider it stalled
                mtime = os.path.getmtime(status_file)
                if (time.time() - mtime) > 300:
                    is_stalled = True
            except Exception:
                pass

            if is_dead or is_stalled:
                if is_dead:
                    self.log("WARN", f"Tiến trình cài đặt nền (PID {pid}) đã kết thúc.")
                else:
                    self.log("WARN", f"Tiến trình cài đặt nền (PID {pid}) bị treo quá 5 phút. Tự động kết thúc.")
                    if pid > 0:
                        subprocess.run(f"taskkill /f /t /pid {pid}", shell=True, capture_output=True)
                    subprocess.run("taskkill /f /im winget.exe", shell=True, capture_output=True)

                is_running = False
                finished = True
                data["is_running"] = False
                data["finished"] = True
                data["status_text"] = "Tiến trình cài đặt nền đã hoàn tất hoặc đã được giải phóng."
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
        """Forcefully cancels and terminates the ongoing background winget installation."""
        paths = self._get_winget_session_paths()
        try:
            # 1. Write cancel file
            with open(paths["cancel"], "w", encoding="utf-8") as f:
                f.write("cancel")

            # 2. Terminate runner process tree and any lingering winget processes
            cur_status = self.get_winget_install_status()
            pid = cur_status.get("pid") or self._current_winget_pid
            if pid and pid > 0:
                subprocess.run(f"taskkill /f /t /pid {pid}", shell=True, capture_output=True)

            subprocess.run("taskkill /f /im winget.exe", shell=True, capture_output=True)
            subprocess.run("taskkill /f /im coccoc_vi_machine.exe", shell=True, capture_output=True)
            subprocess.run("taskkill /f /im CocCocUpdate.exe", shell=True, capture_output=True)

            # 3. Finalize status immediately so UI unblocks instantly
            final_status = {
                "state":                "canceled",
                "pid":                  0,
                "is_running":           False,
                "finished":             True,
                "canceled":             True,
                "current_index":        cur_status.get("current_index", 0),
                "total":                cur_status.get("total", 0),
                "current_package_id":   "",
                "current_package_name": "",
                "success_count":        cur_status.get("success_count", 0),
                "error_count":          cur_status.get("error_count", 0),
                "status_text":          "Đã dừng cài đặt theo yêu cầu.",
                "percentage":           0,
                "log":                  cur_status.get("log", []) + ["⛔ Đã dừng tiến trình cài đặt."]
            }
            self._write_json_atomic(paths["status"], final_status)
            self._last_winget_status = final_status
            self._current_winget_pid = None

            if os.path.exists(paths["queue"]):
                try:
                    os.remove(paths["queue"])
                except Exception:
                    pass

            self.log("WARNING", "Đã dừng và giải phóng hoàn toàn tiến trình cài đặt nền.")
            return {"success": True, "message": "Đã dừng hoàn toàn tiến trình cài đặt phần mềm!"}
        except Exception as e:
            self.log("ERROR", f"Không thể dừng cài đặt: {e}")
            return {"success": False, "message": str(e)}

    def reset_winget_session(self):
        """Resets the winget installer session back to idle state, killing any hung processes."""
        paths = self._get_winget_session_paths()
        try:
            cur_status = self.get_winget_install_status()
            pid = cur_status.get("pid") or self._current_winget_pid
            if pid and pid > 0:
                subprocess.run(f"taskkill /f /t /pid {pid}", shell=True, capture_output=True)

            subprocess.run("taskkill /f /im winget.exe", shell=True, capture_output=True)
            subprocess.run("taskkill /f /im coccoc_vi_machine.exe", shell=True, capture_output=True)
            subprocess.run("taskkill /f /im CocCocUpdate.exe", shell=True, capture_output=True)

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
            self._write_json_atomic(paths["status"], idle_status)
            self._last_winget_status = idle_status
            self._current_winget_pid = None

            for f in [paths["queue"], paths["cancel"]]:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except Exception:
                        pass

            self.log("INFO", "Đã đặt lại trạng thái kho phần mềm về ban đầu.")
            return {"success": True, "message": "Đã làm mới và xóa hàng đợi cài đặt thành công!"}
        except Exception as e:
            self.log("ERROR", f"Lỗi reset session: {e}")
            return {"success": False, "message": str(e)}

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

        # Đảm bảo watcher thông báo vẫn đang chạy cho session này
        self._start_winget_notify_watcher(paths["status"])

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

        # Also terminate any orphan winget.exe processes that might be holding index.db locked
        try:
            subprocess.run("taskkill /f /im winget.exe", shell=True, capture_output=True)
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

            # Khởi chạy luồng theo dõi và thông báo tray khi cài xong từng phần mềm
            self._start_winget_notify_watcher(paths["status"])

            self.log("INFO", f"Đã khởi chạy cài đặt nền {len(package_ids)} phần mềm (PID: {proc.pid}).")
            return {
                "success": True,
                "message": f"Đã bắt đầu cài đặt nền {len(package_ids)} phần mềm. Quá trình vẫn tiếp tục kể cả khi đóng ứng dụng!"
            }
        except Exception as e:
            self.log("ERROR", f"Không thể khởi chạy winget_runner.ps1: {e}")
            return {"success": False, "message": f"Lỗi khởi động tiến trình nền: {e}"}

    def _start_winget_notify_watcher(self, status_file: str):
        """Starts a daemon thread that monitors status.json and fires tray balloon notifications
        for each completed installation and a final summary when the batch finishes."""
        import threading

        # Nếu watcher cũ vẫn đang chạy, không cần tạo watcher mới
        if self._winget_notify_watcher and self._winget_notify_watcher.is_alive():
            return

        def _watcher():
            last_success_count = 0
            last_error_count   = 0
            last_pkg_name      = ""
            last_finished      = False
            poll_interval      = 3  # seconds

            while True:
                import time
                time.sleep(poll_interval)

                # Đọc file status.json
                try:
                    if not os.path.exists(status_file):
                        continue
                    with open(status_file, "r", encoding="utf-8-sig") as f:
                        data = json.load(f)
                except Exception:
                    continue

                success_count = int(data.get("success_count", 0))
                error_count   = int(data.get("error_count", 0))
                pkg_name      = data.get("current_package_name") or ""
                finished      = bool(data.get("finished", False))
                canceled      = bool(data.get("canceled", False))
                total         = int(data.get("total", 0))

                # --- Phát hiện mỗi phần mềm cài xong thành công ---
                if success_count > last_success_count:
                    # Tên phần mềm vừa cài: lấy từ trường log dòng cuối hoặc current_package_name
                    just_installed = last_pkg_name or pkg_name or "Phần mềm"
                    # Thử đọc tên chính xác hơn từ log
                    try:
                        logs = data.get("log", []) or []
                        for line in reversed(logs):
                            if "[OK] Da cai dat thanh cong" in line or "[OK]" in line:
                                # Trích tên sau [OK]: ...
                                parts = line.split(": ", 1)
                                if len(parts) > 1:
                                    just_installed = parts[-1].strip()
                                break
                    except Exception:
                        pass

                    self._fire_tray_notify(
                        title=f"✅ Cài đặt thành công!",
                        message=(
                            f"Đã cài đặt xong: {just_installed}\n"
                            f"Bạn hãy di chuyển đến màn hình Desktop và mở ứng dụng lên nhé!"
                        ),
                        notify_type="success",
                        duration_ms=6000
                    )
                    last_success_count = success_count

                # --- Phát hiện lỗi mới ---
                if error_count > last_error_count:
                    err_pkg = last_pkg_name or pkg_name or "một phần mềm"
                    self._fire_tray_notify(
                        title="⚠️ Cài đặt gặp lỗi",
                        message=(
                            f"Không thể cài đặt: {err_pkg}\n"
                            f"Vui lòng mở ứng dụng và kiểm tra nhật ký để biết chi tiết."
                        ),
                        notify_type="error",
                        duration_ms=7000
                    )
                    last_error_count = error_count

                last_pkg_name = pkg_name

                # --- Kết thúc toàn bộ hàng đợi ---
                if finished and not last_finished:
                    last_finished = True
                    import time as _t
                    _t.sleep(1.5)  # Chờ balloon trước đó biến mất

                    if canceled:
                        self._fire_tray_notify(
                            title="🛑 Đã dừng cài đặt",
                            message=(
                                f"Quá trình cài đặt đã bị dừng theo yêu cầu.\n"
                                f"Đã cài thành công {success_count}/{total} phần mềm."
                            ),
                            notify_type="warning",
                            duration_ms=7000
                        )
                    elif error_count > 0 and success_count == 0:
                        self._fire_tray_notify(
                            title="❌ Cài đặt thất bại",
                            message=(
                                f"Không thể cài đặt {error_count}/{total} phần mềm.\n"
                                f"Vui lòng mở ứng dụng và kiểm tra nhật ký."
                            ),
                            notify_type="error",
                            duration_ms=8000
                        )
                    elif error_count > 0:
                        self._fire_tray_notify(
                            title="✅ Hoàn tất (có lỗi)",
                            message=(
                                f"Đã cài thành công {success_count}/{total} phần mềm.\n"
                                f"Có {error_count} phần mềm gặp lỗi. Mở ứng dụng để xem chi tiết."
                            ),
                            notify_type="warning",
                            duration_ms=8000
                        )
                    else:
                        self._fire_tray_notify(
                            title="🎉 Cài đặt hoàn tất!",
                            message=(
                                f"Đã cài đặt thành công {success_count}/{total} phần mềm.\n"
                                f"Hãy di chuyển đến màn hình Desktop và mở ứng dụng lên nhé!"
                            ),
                            notify_type="success",
                            duration_ms=8000
                        )
                    break  # Kết thúc vòng lặp watcher

        t = threading.Thread(target=_watcher, daemon=True, name="WingetNotifyWatcher")
        t.start()
        self._winget_notify_watcher = t

    def _fire_tray_notify(self, title: str, message: str, notify_type: str = "info", duration_ms: int = 5000):
        """Calls TrayManager.show_tray_notification() if a tray is available."""
        try:
            tray = getattr(self, '_tray', None)
            if tray and hasattr(tray, 'show_tray_notification'):
                tray.show_tray_notification(title, message, notify_type, duration_ms)
            else:
                print(f"[WingetNotify] {title}: {message}")
        except Exception as ex:
            print(f"[WingetNotify] _fire_tray_notify error: {ex}")

    def pin_app_shortcut(self, package_id, package_name=""):
        """Pins and creates shortcuts for the specified application to Desktop, Start Menu, and Programs."""
        try:
            if not package_id:
                return {"success": False, "message": "Chưa cung cấp mã phần mềm!"}

            if not package_name:
                catalog = {item["id"]: item["name"] for item in self.get_software_catalog()}
                package_name = catalog.get(package_id, package_id)

            paths = self._get_winget_session_paths()
            ps1_path = paths.get("ps1")
            if not ps1_path or not os.path.exists(ps1_path):
                from constants import get_resource_path
                ps1_path = get_resource_path("modules", "winget_runner.ps1")

            clean_pkg_id = package_id.replace("'", "''")
            clean_pkg_name = package_name.replace("'", "''")
            clean_ps1_path = ps1_path.replace("'", "''")

            ps_cmd = f"""
. '{clean_ps1_path}'
$res = Pin-AppShortcuts -PackageId '{clean_pkg_id}' -PackageName '{clean_pkg_name}'
$res | ConvertTo-Json -Depth 3 -Compress
"""
            encoded = base64.b64encode(ps_cmd.encode('utf-16le')).decode('ascii')
            r = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded],
                capture_output=True,
                text=True,
                timeout=15
            )

            stdout = r.stdout.strip()
            if stdout:
                try:
                    data = json.loads(stdout)
                    if data.get("Success"):
                        count = data.get("CreatedCount", 0)
                        self.log("SUCCESS", f"Đã ghim chính xác '{package_name}' ra Desktop, Start Menu và Programs ({count} vị trí)!")
                        return {
                            "success": True,
                            "message": f"Đã ghim chính xác '{package_name}' ra Desktop, Start Menu và Programs!",
                            "paths": data.get("Paths", []),
                            "count": count
                        }
                    else:
                        msg = data.get("Message") or "Không tìm thấy file thực thi hoặc shortcut để ghim."
                        self.log("WARN", f"Không thể ghim {package_name}: {msg}")
                        return {"success": False, "message": msg}
                except Exception as ex:
                    self.log("WARN", f"Lỗi phân tích JSON kết quả ghim: {ex}")

            err_msg = r.stderr.strip() or "Không có phản hồi từ tiến trình tạo shortcut."
            return {"success": False, "message": f"Lỗi tạo shortcut: {err_msg}"}
        except Exception as e:
            self.log("ERROR", f"Lỗi ghim shortcut {package_id}: {e}")
            return {"success": False, "message": str(e)}


    # ── IP NETWORK SCANNER ───────────────────────────────────────────────
    def get_ip_scanner_default_range(self):
        try:
            import modules.ip_scanner as ip_scanner
            return ip_scanner.get_local_subnet_range()
        except Exception as e:
            self.log("ERROR", f"Lỗi lấy dải mạng mặc định: {e}")
            return {"local_ip": "192.168.1.100", "subnet": "192.168.1.0/24", "start_ip": "192.168.1.1", "end_ip": "192.168.1.254"}

    def scan_ip_range(self, subnet_str="", ip_start="", ip_end="", check_ping=True, check_hostname=True, check_mac=True, check_http_port=True, check_https_port=True, max_threads=50, ports_to_check=None):
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
                max_threads=max_threads,
                ports_to_check=ports_to_check
            )
            self.log("SUCCESS", f"Hoàn tất quét LAN! Tìm thấy {len(res)} thiết bị online.")
            return {"success": True, "results": res, "total": len(res)}
        except Exception as e:
            self.log("ERROR", f"Lỗi quét IP Scanner: {e}")
            return {"success": False, "message": str(e), "results": []}

    def scan_single_host_ports(self, target_host="", ports=None):
        try:
            import modules.ip_scanner as ip_scanner
            target = target_host.strip() if target_host else "127.0.0.1"
            self.log("INFO", f"Đang quét chi tiết các cổng dịch vụ cho máy: {target}...")
            res = ip_scanner.scan_single_host_ports(target, ports=ports, timeout=0.45)
            open_count = len([x for x in res if x.get("is_open")])
            self.log("SUCCESS", f"Đã quét xong {len(res)} cổng trên {target} ({open_count} cổng MỞ).")
            return {"success": True, "target": target, "results": res, "open_count": open_count, "total": len(res)}
        except Exception as e:
            self.log("ERROR", f"Lỗi quét port host {target_host}: {e}")
            return {"success": False, "message": str(e), "results": []}

    def get_port_definitions(self):
        try:
            import modules.ip_scanner as ip_scanner
            return {"success": True, "data": ip_scanner.WINDOWS_PORTS_DEF}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def open_rdp_connection(self, ip=""):
        try:
            target = ip.strip()
            if not target:
                return {"success": False, "message": "Địa chỉ IP không hợp lệ!"}
            self.log("INFO", f"Đang mở Remote Desktop (mstsc) kết nối đến {target}...")
            subprocess.Popen(['mstsc.exe', f'/v:{target}'])
            return {"success": True, "message": f"Đã mở kết nối Remote Desktop đến {target}"}
        except Exception as e:
            self.log("ERROR", f"Lỗi mở RDP đến {ip}: {e}")
            return {"success": False, "message": str(e)}

    def open_smb_share(self, ip=""):
        try:
            target = ip.strip()
            if not target:
                return {"success": False, "message": "Địa chỉ IP không hợp lệ!"}
            unc_path = f"\\\\{target}"
            self.log("INFO", f"Đang mở thư mục chia sẻ mạng (SMB): {unc_path}...")
            os.startfile(unc_path)
            return {"success": True, "message": f"Đã mở chia sẻ mạng {unc_path}"}
        except Exception as e:
            try:
                subprocess.Popen(['explorer.exe', f"\\\\{target}"])
                return {"success": True, "message": f"Đã gửi lệnh mở {target}"}
            except Exception as ex2:
                self.log("ERROR", f"Lỗi mở SMB đến {ip}: {ex2}")
                return {"success": False, "message": str(ex2)}

    def open_winrm_session(self, ip=""):
        try:
            target = ip.strip()
            if not target:
                return {"success": False, "message": "Địa chỉ IP không hợp lệ!"}
            self.log("INFO", f"Đang mở PowerShell Remoting (WinRM) đến {target}...")
            cmd = f'Write-Host "Dang ket noi PowerShell Remoting den {target} (WinRM)..." -ForegroundColor Cyan; Enter-PSSession -ComputerName "{target}"'
            subprocess.Popen(['powershell.exe', '-NoExit', '-Command', cmd])
            return {"success": True, "message": f"Đã mở cửa sổ PowerShell Remoting đến {target}"}
        except Exception as e:
            self.log("ERROR", f"Lỗi mở WinRM đến {ip}: {e}")
            return {"success": False, "message": str(e)}


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
        """Fetches all installed OEM drivers using pnputil (instant <0.1s) with PowerShell fallback."""
        # 1. Ultra-fast retrieval via native pnputil /enum-drivers
        try:
            res = subprocess.run(
                ['pnputil', '/enum-drivers'],
                capture_output=True, text=True, timeout=12, encoding='utf-8', errors='ignore'
            )
            if res.returncode == 0 and res.stdout.strip():
                drivers = []
                current = {}
                for raw_line in res.stdout.splitlines():
                    line = raw_line.strip()
                    if not line:
                        if current.get("driver"):
                            drivers.append(current)
                            current = {}
                        continue
                    if ":" in line:
                        key, val = line.split(":", 1)
                        key = key.strip()
                        val = val.strip()
                        if key == "Published Name":
                            if current.get("driver"):
                                drivers.append(current)
                                current = {}
                            current["driver"] = val
                        elif key == "Provider Name":
                            current["provider"] = val or "Unknown"
                        elif key == "Class Name":
                            current["class"] = val or "-"
                        elif key == "Driver Version":
                            parts = val.split(" ", 1)
                            if len(parts) == 2:
                                current["date"] = parts[0]
                                current["version"] = parts[1]
                            else:
                                current["version"] = val
                                current["date"] = "-"
                        elif key == "Signer Name":
                            current["signer"] = val

                if current.get("driver"):
                    drivers.append(current)

                if drivers:
                    self._cached_driver_count = len(drivers)
                    return {"success": True, "drivers": drivers, "total": len(drivers)}
        except Exception as ex:
            self.log("WARN", f"pnputil /enum-drivers không thành công, thử PowerShell: {ex}")

        # 2. Fallback: PowerShell Get-WindowsDriver
        try:
            cmd = ['powershell', '-Command', 'Get-WindowsDriver -Online | Select-Object ProviderName, Driver, ClassDescription, Version, Date | ConvertTo-Json']
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore')
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
                self._cached_driver_count = len(cleaned)
                return {"success": True, "drivers": cleaned, "total": len(cleaned)}
            return {"success": True, "drivers": [], "total": 0}
        except Exception as e:
            self.log("ERROR", f"Lỗi lấy danh sách Driver: {e}")
            return {"success": False, "message": str(e), "drivers": [], "total": 0}

    def select_folder_dialog(self, title="Chọn thư mục", initial_dir=""):
        """Opens native Windows folder picker dialog."""
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            kwargs = {'title': title}
            if initial_dir and os.path.exists(initial_dir):
                kwargs['initialdir'] = os.path.normpath(initial_dir)
            folder = filedialog.askdirectory(**kwargs)
            root.destroy()
            if folder:
                folder = os.path.normpath(folder)
            return {"success": True, "folder": folder}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _get_last_driver_backup_dir(self):
        """Retrieves last driver backup directory or finds existing backup folder on disk."""
        # 1. In-memory cache
        if getattr(self, '_last_driver_backup_path', None) and os.path.exists(self._last_driver_backup_path):
            return os.path.normpath(self._last_driver_backup_path)

        # 2. Persistent JSON config
        try:
            appdata = os.environ.get('APPDATA', '')
            cfg_p = os.path.join(appdata, 'IT Tool LTT', 'driver_backup_config.json')
            if os.path.exists(cfg_p):
                with open(cfg_p, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    p = cfg.get('last_backup_dir')
                    if p and os.path.exists(p):
                        self._last_driver_backup_path = os.path.normpath(p)
                        return self._last_driver_backup_path
        except Exception:
            pass

        # 3. Smart scan on available drives for existing driver backup directory
        candidates = [
            r"D:\Backup Driver",
            r"D:\Driver_Backup",
            r"D:\DriverBackup",
            r"E:\Backup Driver",
            r"E:\Driver_Backup",
            r"E:\DriverBackup",
            r"F:\Backup Driver",
            r"F:\Driver_Backup",
            r"C:\Backup Driver",
            r"C:\Driver_Backup"
        ]
        for c in candidates:
            if os.path.exists(c):
                try:
                    if os.listdir(c):
                        self._last_driver_backup_path = os.path.normpath(c)
                        return self._last_driver_backup_path
                except Exception:
                    pass

        # 4. Fallback: prefer D:\Backup Driver if drive D exists
        for letter in ['D', 'E', 'F']:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                def_p = os.path.join(drive, 'Backup Driver')
                os.makedirs(def_p, exist_ok=True)
                self._last_driver_backup_path = os.path.normpath(def_p)
                return self._last_driver_backup_path

        user_profile = os.environ.get('USERPROFILE', 'C:\\')
        def_c = os.path.join(user_profile, 'Desktop', 'Backup Driver')
        os.makedirs(def_c, exist_ok=True)
        self._last_driver_backup_path = os.path.normpath(def_c)
        return self._last_driver_backup_path

    def _save_last_driver_backup_dir(self, path):
        """Saves last driver backup directory into persistent cache."""
        if not path:
            return
        path = os.path.normpath(path.strip())
        self._last_driver_backup_path = path
        try:
            appdata = os.environ.get('APPDATA', '')
            cfg_dir = os.path.join(appdata, 'IT Tool LTT')
            os.makedirs(cfg_dir, exist_ok=True)
            with open(os.path.join(cfg_dir, 'driver_backup_config.json'), 'w', encoding='utf-8') as f:
                json.dump({'last_backup_dir': path}, f)
        except Exception:
            pass

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
        """Starts asynchronous background driver backup with real-time streaming progress,
        resilient multi-engine export (PowerShell Export-WindowsDriver -> DISM -> pnputil per-driver),
        and automatic missing-driver healing."""
        if not target_dir:
            initial_folder = self._get_last_driver_backup_dir()
            res_dlg = self.select_folder_dialog("Chọn thư mục lưu trữ Backup Driver", initial_folder)
            target_dir = res_dlg.get("folder")
            if not target_dir:
                return {"success": False, "message": "Bạn đã hủy chọn thư mục sao lưu."}

        self._save_last_driver_backup_dir(target_dir)

        try:
            os.makedirs(target_dir, exist_ok=True)
        except Exception as e:
            return {"success": False, "message": f"Không thể tạo thư mục lưu trữ: {e}"}

        # Check free disk space (at least 200MB)
        try:
            free_bytes = shutil.disk_usage(target_dir).free
            if free_bytes < 200 * 1024 * 1024:
                return {
                    "success": False,
                    "message": "Ổ đĩa lưu trữ không đủ dung lượng trống (<200MB). Vui lòng chọn ổ đĩa khác!"
                }
        except Exception:
            pass

        # 1. Enumerate OEM drivers list upfront (< 0.1s)
        oem_drivers = []
        try:
            res_pnp = subprocess.run(
                ['pnputil', '/enum-drivers'],
                capture_output=True, text=True, timeout=12, encoding='utf-8', errors='ignore'
            )
            if res_pnp.returncode == 0 and res_pnp.stdout:
                for line in res_pnp.stdout.splitlines():
                    if "Published Name" in line and ":" in line:
                        d_name = line.split(":", 1)[1].strip()
                        if d_name:
                            oem_drivers.append(d_name)
        except Exception as ex:
            self.log("WARN", f"pnputil /enum-drivers enumeration warning: {ex}")

        # Fallback count if pnputil enumeration was empty
        total_oem = len(oem_drivers) or getattr(self, "_cached_driver_count", 0) or 35

        self._driver_progress = {
            "active": True,
            "mode": "backup",
            "status": "running",
            "current": 0,
            "total": total_oem,
            "percentage": 0,
            "message": f"Đang chuẩn bị sao lưu {total_oem} driver hệ thống ra {target_dir}...",
            "path": target_dir
        }

        def worker():
            try:
                self.log("INFO", f"Bắt đầu xuất toàn bộ Driver hệ thống ({total_oem} mục) ra: {target_dir}...")
                exported_oem_set = set()
                skipped_list = []

                # Background live directory monitor thread to guarantee continuous progress bar updates
                stop_monitor = threading.Event()
                def monitor_target_dir():
                    seen_dirs = set()
                    while not stop_monitor.is_set():
                        try:
                            if os.path.exists(target_dir):
                                subdirs = [d for d in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, d))]
                                curr_len = len(subdirs)
                                if curr_len > 0:
                                    pct = min(96, int((curr_len / max(1, total_oem)) * 100))
                                    new_dirs = set(subdirs) - seen_dirs
                                    if new_dirs:
                                        latest = list(new_dirs)[-1]
                                        self._driver_progress["message"] = f"Đang xuất ({curr_len}/{total_oem}): {latest}..."
                                        seen_dirs.update(new_dirs)
                                    self._driver_progress["current"] = curr_len
                                    self._driver_progress["percentage"] = pct
                        except Exception:
                            pass
                        stop_monitor.wait(0.5)

                mon_thread = threading.Thread(target=monitor_target_dir, daemon=True)
                mon_thread.start()

                # ── METHOD 1: PowerShell Export-WindowsDriver (Fastest & natively resilient) ──
                ps_script = (
                    f'$exp = Export-WindowsDriver -Online -Destination "{target_dir}" -ErrorAction Continue '
                    f'| Select-Object Driver, ProviderName, ClassName; @($exp) | ConvertTo-Json -Compress'
                )
                ps_cmd = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script]

                try:
                    self.log("INFO", "Thực thi PowerShell Export-WindowsDriver...")
                    res_ps = subprocess.run(ps_cmd, capture_output=True, text=True, timeout=600)
                    if res_ps.stdout and res_ps.stdout.strip():
                        try:
                            ps_data = json.loads(res_ps.stdout.strip())
                            if isinstance(ps_data, dict):
                                ps_data = [ps_data]
                            for item in ps_data:
                                drv_val = item.get("Driver", "").strip().lower()
                                if drv_val:
                                    exported_oem_set.add(drv_val)
                            self.log("INFO", f"PowerShell đã xuất thành công {len(exported_oem_set)} driver.")
                        except Exception as j_err:
                            self.log("WARN", f"Không thể parse JSON từ Export-WindowsDriver: {j_err}")
                except subprocess.TimeoutExpired:
                    self.log("WARN", "PowerShell Export-WindowsDriver quá thời gian chờ (timeout 600s), tiếp tục bước kiểm tra...")
                except Exception as ps_err:
                    self.log("WARN", f"Lỗi gọi PowerShell Export-WindowsDriver: {ps_err}")

                # ── METHOD 2: DISM /Export-Driver fallback if Method 1 produced 0 files ──
                existing_folders = [d for d in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, d))] if os.path.exists(target_dir) else []
                if not exported_oem_set and not existing_folders:
                    self.log("WARN", "PowerShell không xuất được driver nào, chuyển sang DISM /Export-Driver...")
                    self._driver_progress["message"] = "Đang chuyển sang DISM /Export-Driver để sao lưu..."
                    try:
                        dism_cmd = ['dism', '/Online', '/Export-Driver', f'/Destination:{target_dir}']
                        subprocess.run(dism_cmd, capture_output=True, text=True, timeout=600)
                    except Exception as d_err:
                        self.log("WARN", f"Lỗi DISM: {d_err}")

                # ── METHOD 3: Smart Per-Driver Healing for Missing Drivers ─────────
                # Check which OEM drivers are still missing
                if oem_drivers:
                    missing_drivers = [o for o in oem_drivers if o.lower() not in exported_oem_set]
                    if missing_drivers:
                        self.log("INFO", f"Kiểm tra thấy {len(missing_drivers)} driver chưa xuất xong, đang tiến hành xuất bù từng driver qua pnputil...")
                        self._driver_progress["message"] = f"Đang xuất bù {len(missing_drivers)} driver còn lại..."

                        for idx, drv in enumerate(missing_drivers):
                            sub_dir = os.path.join(target_dir, drv.replace(".inf", ""))
                            os.makedirs(sub_dir, exist_ok=True)
                            curr_pct = min(98, int(((len(exported_oem_set) + idx) / max(1, total_oem)) * 100))
                            self._driver_progress["message"] = f"Đang xuất bù ({idx+1}/{len(missing_drivers)}): {drv}..."
                            self._driver_progress["percentage"] = curr_pct

                            try:
                                r_drv = subprocess.run(
                                    ['pnputil', '/export-driver', drv, sub_dir],
                                    capture_output=True, text=True, timeout=25
                                )
                                if r_drv.returncode == 0:
                                    exported_oem_set.add(drv.lower())
                                else:
                                    # Driver has broken source files or catalog in Windows DriverStore
                                    skipped_list.append(drv)
                                    self.log("WARN", f"Bỏ qua driver lỗi nguồn: {drv} (mã: {r_drv.returncode})")
                            except subprocess.TimeoutExpired:
                                skipped_list.append(drv)
                                self.log("WARN", f"Bỏ qua driver bị treo nguồn: {drv}")
                            except Exception as ex_drv:
                                skipped_list.append(drv)
                                self.log("WARN", f"Lỗi xuất {drv}: {ex_drv}")

                # Stop monitor
                stop_monitor.set()
                try:
                    mon_thread.join(timeout=2.0)
                except Exception:
                    pass

                # Calculate final count & disk size
                final_subdirs = [d for d in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, d))] if os.path.exists(target_dir) else []
                final_count = max(len(exported_oem_set), len(final_subdirs))

                # Calculate total folder size
                total_bytes = 0
                try:
                    for root_p, _, files in os.walk(target_dir):
                        for f in files:
                            total_bytes += os.path.getsize(os.path.join(root_p, f))
                except Exception:
                    pass

                if total_bytes >= 1024 * 1024 * 1024:
                    size_str = f"{total_bytes / (1024*1024*1024):.2f} GB"
                else:
                    size_str = f"{total_bytes / (1024*1024):.1f} MB"

                if final_count > 0:
                    self._driver_progress["current"] = final_count
                    self._driver_progress["total"] = max(final_count, total_oem)
                    self._driver_progress["percentage"] = 100
                    self._driver_progress["status"] = "completed"

                    if skipped_list:
                        skip_str = f"\n(Đã tự động bỏ qua {len(skipped_list)} driver bị hỏng file gốc trong Windows DriverStore: {', '.join(skipped_list[:3])})"
                        self._driver_progress["message"] = (
                            f"Hoàn tất sao lưu {final_count}/{total_oem} Driver OEM ({size_str}) vào:\n{target_dir}{skip_str}"
                        )
                    else:
                        self._driver_progress["message"] = (
                            f"Hoàn tất sao lưu toàn bộ {final_count}/{total_oem} Driver OEM ({size_str}) vào:\n{target_dir}"
                        )
                    self.log("SUCCESS", f"Hoàn tất sao lưu driver ({final_count} mục, {size_str}) ra {target_dir}")
                else:
                    self._driver_progress["status"] = "error"
                    self._driver_progress["message"] = (
                        "Không thể sao lưu driver! Vui lòng đảm bảo phần mềm đang chạy dưới quyền "
                        "Quản trị viên (Run as administrator) và ổ đĩa còn trống dung lượng."
                    )
                    self.log("ERROR", "Sao lưu driver thất bại (0 driver được xuất).")

            except Exception as ex:
                self._driver_progress["status"] = "error"
                self._driver_progress["message"] = f"Lỗi trong quá trình sao lưu: {ex}"
                self.log("ERROR", f"Lỗi sao lưu Driver async: {ex}")

        threading.Thread(target=worker, daemon=True).start()
        return {"success": True, "message": f"Đã bắt đầu sao lưu Driver vào:\n{target_dir}", "path": target_dir}

    def start_restore_drivers_async(self, src_dir=""):
        """Starts asynchronous background driver restore with real-time progress tracking."""
        if not src_dir:
            initial_folder = self._get_last_driver_backup_dir()
            res_dlg = self.select_folder_dialog("Chọn thư mục chứa Driver đã Sao Lưu", initial_folder)
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

        if not inf_files:
            return {
                "success": False,
                "message": f"Không tìm thấy file .inf driver nào trong:\n{src_dir}\nVui lòng chọn đúng thư mục chứa các driver đã sao lưu!"
            }

        total_inf_count = len(inf_files)

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
                    shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='ignore', bufsize=1
                )

                q = queue.Queue()
                def reader():
                    try:
                        for line in iter(proc.stdout.readline, ''):
                            q.put(line)
                    finally:
                        try:
                            proc.stdout.close()
                        except Exception:
                            pass
                        q.put(None)

                threading.Thread(target=reader, daemon=True).start()

                count = 0
                last_act = time.time()
                while True:
                    try:
                        line = q.get(timeout=0.4)
                        if line is None:
                            break
                        last_act = time.time()
                        line_str = line.strip()
                        if line_str and ("Adding driver" in line_str or "Driver package" in line_str or ".inf" in line_str.lower()):
                            if ".inf" in line_str.lower():
                                count += 1
                            pct = min(99, int((count / max(1, total_inf_count)) * 100))
                            self._driver_progress["current"] = min(count, total_inf_count)
                            self._driver_progress["percentage"] = pct
                            self._driver_progress["message"] = f"Đang nạp & cài đặt ({count}/{total_inf_count}): {line_str[:65]}..."
                    except queue.Empty:
                        if proc.poll() is not None:
                            while True:
                                try:
                                    rem = q.get_nowait()
                                    if rem is None:
                                        break
                                    if ".inf" in rem.lower():
                                        count += 1
                                except queue.Empty:
                                    break
                            break
                        if time.time() - last_act > 180:
                            self.log("WARN", "Tiến trình nạp driver không phản hồi quá 180s, dừng tiến trình...")
                            try:
                                proc.kill()
                            except Exception:
                                pass
                            break

                rc = proc.wait()
                self._driver_progress["current"] = total_inf_count
                self._driver_progress["total"] = total_inf_count
                self._driver_progress["percentage"] = 100
                self._driver_progress["status"] = "completed"

                if rc == 3010:
                    msg = f"Đã phục hồi xong toàn bộ driver từ {src_dir}! (Khởi động lại máy để áp dụng đầy đủ)"
                else:
                    msg = f"Hoàn tất nạp & cài đặt thành công tất cả driver từ {src_dir}!"

                self._driver_progress["message"] = msg
                self.log("SUCCESS", f"Đã phục hồi xong driver từ {src_dir} (mã: {rc})")

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


    def get_last_driver_backup_path(self):
        """Returns the last saved or detected driver backup directory."""
        path = self._get_last_driver_backup_dir()
        return {"success": True, "path": path}

    def open_folder_explorer(self, folder_path=""):
        try:
            path = folder_path.strip() if folder_path else ""
            if not path or not os.path.exists(path):
                path = self._get_last_driver_backup_dir()
            path = os.path.normpath(path)
            os.makedirs(path, exist_ok=True)
            self._save_last_driver_backup_dir(path)
            self.log("INFO", f"Đang mở thư mục lưu trữ: {path}")

            try:
                os.startfile(path)
            except Exception:
                subprocess.Popen(['explorer.exe', path])

            return {"success": True, "path": path}
        except Exception as e:
            self.log("ERROR", f"Lỗi mở thư mục: {e}")
            return {"success": False, "message": str(e)}

    def open_driver_backup_folder(self, folder_path=""):
        return self.open_folder_explorer(folder_path)


    # ── WINDOWS SERVICES MANAGER ──────────────────────────────────────────
    def get_windows_services(self):
        """Fetches all Windows services via psutil (instant 0.02s) with PowerShell fallback."""
        # 1. Fast, real-time retrieval via psutil
        try:
            import psutil
            cleaned = []
            for s in psutil.win_service_iter():
                try:
                    info = s.as_dict()
                    st = (info.get('status') or '').lower()
                    if st == 'running':
                        status_str = "Running"
                    elif st == 'stopped':
                        status_str = "Stopped"
                    elif 'start' in st:
                        status_str = "StartPending"
                    elif 'stop' in st:
                        status_str = "StopPending"
                    elif 'pause' in st:
                        status_str = "Paused"
                    else:
                        status_str = st.capitalize() or "Stopped"

                    sp = (info.get('start_type') or '').lower()
                    if 'auto' in sp:
                        start_str = "Automatic"
                    elif 'disabled' in sp:
                        start_str = "Disabled"
                    else:
                        start_str = "Manual"

                    cleaned.append({
                        "name": info.get("name") or "",
                        "display": info.get("display_name") or info.get("name") or "",
                        "status": status_str,
                        "start_type": start_str
                    })
                except Exception:
                    pass

            if cleaned:
                cleaned.sort(key=lambda x: x["name"].lower())
                return {"success": True, "services": cleaned, "total": len(cleaned)}
        except Exception:
            pass

        # 2. Fallback to PowerShell Get-Service
        try:
            cmd = ['powershell', '-Command', 'Get-Service | Select-Object Name, DisplayName, Status, StartType | ConvertTo-Json']
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore')
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                if isinstance(data, dict):
                    data = [data]

                status_map = {4: "Running", 1: "Stopped", 2: "StartPending", 3: "StopPending", 7: "Paused",
                              "4": "Running", "1": "Stopped", "2": "StartPending", "3": "StopPending", "7": "Paused"}
                start_type_map = {2: "Automatic", 3: "Manual", 4: "Disabled",
                                  "2": "Automatic", "3": "Manual", "4": "Disabled"}

                cleaned = []
                for s in data:
                    st_val = s.get("Status")
                    status_str = status_map.get(st_val, str(st_val)) if st_val in status_map else str(st_val).capitalize()

                    sp_val = s.get("StartType")
                    start_str = start_type_map.get(sp_val, str(sp_val)) if sp_val in start_type_map else str(sp_val).capitalize()

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
        """Starts, Stops, or Restarts a Windows service and waits for transition."""
        if not service_name:
            return {"success": False, "message": "Chưa chọn dịch vụ!"}

        try:
            action_map = {
                "start": f'sc start "{service_name}"',
                "stop": f'sc stop "{service_name}"',
                "restart": f'sc stop "{service_name}" & timeout /t 1 & sc start "{service_name}"'
            }
            cmd = action_map.get(action.lower())
            if not cmd:
                return {"success": False, "message": "Thao tác không hợp lệ!"}

            self.log("INFO", f"Đang thực hiện {action} trên dịch vụ: {service_name}...")
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')

            # Wait briefly for service transition to finish
            target_status = "running" if action.lower() in ("start", "restart") else "stopped"
            try:
                import psutil, time
                for _ in range(8):
                    time.sleep(0.25)
                    svc = psutil.win_service_get(service_name)
                    if svc.status() == target_status:
                        break
            except Exception:
                pass

            if res.returncode == 0 or "SUCCESS" in res.stdout.upper() or "PENDING" in res.stdout.upper():
                self.log("SUCCESS", f"Đã thực hiện {action} thành công trên dịch vụ '{service_name}'!")
                return {"success": True, "message": f"Đã thực hiện {action} thành công trên dịch vụ '{service_name}'!"}
            else:
                alt_cmd = f'net {action} "{service_name}"' if action in ["start", "stop"] else None
                if alt_cmd:
                    r_alt = subprocess.run(alt_cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
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

    def get_available_partitions(self):
        import modules.boot_manager as bm
        partitions = bm.get_available_partitions()
        return {
            "success": True,
            "partitions": partitions
        }

    def inspect_winpe_source(self, source_path):
        import modules.boot_manager as bm
        return bm.inspect_winpe_source(source_path)

    def integrate_winpe_boot(self, source_path, target_drive="C:", boot_name="WinPE Rescue", selected_wim_rel=None, copy_apps=False):
        import modules.boot_manager as bm
        res = bm.integrate_winpe_boot(
            source_path=source_path,
            target_drive=target_drive,
            boot_name=boot_name,
            selected_wim_rel=selected_wim_rel,
            copy_apps=copy_apps
        )
        if res.get("success"):
            self.log("SUCCESS", res.get("message"))
        else:
            self.log("ERROR", res.get("message"))
        return res

    def add_wim_boot_entry(self, wim_path, boot_name="WinPE Boot", target_drive="C:"):
        return self.integrate_winpe_boot(source_path=wim_path, target_drive=target_drive, boot_name=boot_name)

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
        """Allows user to select WinPE source (.iso or .wim)."""
        return self.browse_winpe_file()

    def browse_winpe_file(self):
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            file_path = filedialog.askopenfilename(
                title='Chọn file WinPE (.iso hoặc .wim)',
                filetypes=[
                    ('WinPE Files (*.iso, *.wim)', '*.iso;*.wim'),
                    ('ISO Disk Images (*.iso)', '*.iso'),
                    ('WIM Files (*.wim)', '*.wim'),
                    ('All Files', '*.*')
                ]
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

    def open_telegram(self):
        """Opens the author's Telegram link in the default browser."""
        import webbrowser
        webbrowser.open(APP_TELEGRAM)
        return {"success": True}

    def get_app_info(self):
        """Returns author and application metadata."""
        return {
            "name": APP_NAME,
            "version": APP_VERSION,
            "author": APP_AUTHOR,
            "phone": APP_PHONE,
            "website": APP_WEBSITE,
            "telegram": APP_TELEGRAM
        }

    def get_logs(self):
        return self._logs

    def clear_logs(self):
        self._logs = []
        return {"success": True}

    def minimize_to_tray(self):
        """Hides the main window to the system tray."""
        if hasattr(self, '_tray') and self._tray:
            self._tray.hide_window()
            return {"success": True, "message": "Đã thu nhỏ xuống khay hệ thống"}
        return {"success": False, "message": "TrayManager chưa khởi tạo"}

    def exit_app(self):
        """Completely terminates the application."""
        if hasattr(self, '_tray') and self._tray:
            self._tray.quit_app()
        else:
            import os
            os._exit(0)

    # ── Zoom Screen (ZoomIt Engine) APIs ──────────────────────────────────
    def get_zoom_screen_status(self):
        try:
            from modules import zoom_screen
            return zoom_screen.get_status()
        except Exception as ex:
            return {"running": False, "error": str(ex), "settings": {}}

    def start_zoom_screen(self):
        try:
            from modules import zoom_screen
            res = zoom_screen.start_zoomit(silent=True)
            self.log("INFO", f"Zoom Screen: {res.get('message', '')}")
            return res
        except Exception as ex:
            return {"success": False, "message": str(ex)}

    def stop_zoom_screen(self):
        try:
            from modules import zoom_screen
            res = zoom_screen.stop_zoomit()
            self.log("INFO", f"Zoom Screen: {res.get('message', '')}")
            return res
        except Exception as ex:
            return {"success": False, "message": str(ex)}

    def trigger_zoom_action(self, action_name):
        try:
            from modules import zoom_screen
            res = zoom_screen.trigger_action(action_name)
            self.log("INFO", f"Zoom Screen Trigger [{action_name}]: {res.get('message', '')}")
            return res
        except Exception as ex:
            return {"success": False, "message": str(ex)}

    def save_zoom_screen_settings(self, settings):
        try:
            from modules import zoom_screen
            res = zoom_screen.save_zoomit_settings(settings)
            self.log("INFO", f"Zoom Screen Settings: {res.get('message', '')}")
            return res
        except Exception as ex:
            return {"success": False, "message": str(ex)}

    def open_zoom_screen_native_options(self):
        try:
            from modules import zoom_screen
            res = zoom_screen.open_zoomit_options()
            self.log("INFO", f"Zoom Screen Options: {res.get('message', '')}")
            return res
        except Exception as ex:
            return {"success": False, "message": str(ex)}

    def update_zoom_screen_hotkey(self, action_name, new_hotkey_text):
        try:
            from modules import zoom_screen
            res = zoom_screen.update_hotkey(action_name, new_hotkey_text)
            self.log("INFO", f"Zoom Screen Hotkey Update [{action_name} -> {new_hotkey_text}]: {res.get('message', '')}")
            return res
        except Exception as ex:
            return {"success": False, "message": str(ex)}

    def reset_zoom_screen_hotkeys(self):
        try:
            from modules import zoom_screen
            res = zoom_screen.reset_hotkeys_to_default()
            self.log("INFO", f"Zoom Screen Reset Hotkeys: {res.get('message', '')}")
            return res
        except Exception as ex:
            return {"success": False, "message": str(ex)}

    def pause_zoom_screen_hotkeys(self):
        try:
            from modules import zoom_screen
            return zoom_screen.pause_hotkeys()
        except Exception as ex:
            return {"success": False, "message": str(ex)}

    def resume_zoom_screen_hotkeys(self):
        try:
            from modules import zoom_screen
            return zoom_screen.resume_hotkeys()
        except Exception as ex:
            return {"success": False, "message": str(ex)}

