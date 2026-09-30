"""
Auto Shutdown Module
Supports: Shutdown, Restart, Hibernate, Logoff, Standby, Lock,
          Close App, Run App, Message
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import os
import sys
import threading
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS


class AutoShutdown:
    def __init__(self, parent):
        self.parent = parent
        self.parent.geometry('620x600')
        self.parent.configure(bg=COLORS['bg'])
        self.countdown_running = False
        self.countdown_thread = None
        self.remaining = 0
        self.setup_ui()

    def setup_ui(self):
        # Title bar
        title = tk.Label(self.parent, text='⏻  Auto Shutdown / Scheduler',
                          font=FONTS['large'], bg=COLORS['bg_header'],
                          fg=COLORS['white'], pady=10)
        title.pack(fill='x')

        main = tk.Frame(self.parent, bg=COLORS['bg'])
        main.pack(fill='both', expand=True, padx=15, pady=10)

        # ── Action Section ──────────────────────────────────────────────
        action_frame = tk.LabelFrame(main, text='  Action  ',
                                      font=FONTS['subtitle'],
                                      bg=COLORS['bg'], fg=COLORS['text'],
                                      relief='groove', bd=2)
        action_frame.pack(fill='x', pady=(0, 10))

        self.action_var = tk.StringVar(value='shutdown')
        actions = [
            ('⏻ Shutdown',   'shutdown'),
            ('🔄 Restart',    'restart'),
            ('💤 Hibernate',  'hibernate'),
            ('🚪 Logoff',     'logoff'),
            ('😴 Standby',    'standby'),
            ('🔒 Lock',       'lock'),
            ('❌ Close App',  'close_app'),
            ('▶️ Run App',   'run_app'),
            ('💬 Message',   'message'),
        ]
        row, col = 0, 0
        for text, val in actions:
            rb = tk.Radiobutton(action_frame, text=text, value=val,
                                 variable=self.action_var,
                                 font=FONTS['normal'],
                                 bg=COLORS['bg'], fg=COLORS['text'],
                                 selectcolor=COLORS['selected'],
                                 command=self.on_action_change,
                                 cursor='hand2')
            rb.grid(row=row, column=col, sticky='w', padx=10, pady=3)
            col += 1
            if col >= 3:
                col = 0
                row += 1

        # ── App / Message Config ────────────────────────────────────────
        self.extra_frame = tk.LabelFrame(main, text='  Configuration  ',
                                          font=FONTS['subtitle'],
                                          bg=COLORS['bg'], fg=COLORS['text'],
                                          relief='groove', bd=2)
        self.extra_frame.pack(fill='x', pady=(0, 10))

        tk.Label(self.extra_frame, text='App/Message:',
                  font=FONTS['normal'], bg=COLORS['bg']).grid(
            row=0, column=0, padx=8, pady=5, sticky='w')
        self.app_entry = tk.Entry(self.extra_frame, font=FONTS['normal'], width=40)
        self.app_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        tk.Button(self.extra_frame, text='Browse...', font=FONTS['small'],
                   bg=COLORS['info'], fg='white', relief='flat',
                   cursor='hand2',
                   command=self.browse_app).grid(row=0, column=2, padx=5, pady=5)
        self.extra_frame.columnconfigure(1, weight=1)

        # ── Timer Section ───────────────────────────────────────────────
        timer_frame = tk.LabelFrame(main, text='  Timer  ',
                                     font=FONTS['subtitle'],
                                     bg=COLORS['bg'], fg=COLORS['text'],
                                     relief='groove', bd=2)
        timer_frame.pack(fill='x', pady=(0, 10))

        inner = tk.Frame(timer_frame, bg=COLORS['bg'])
        inner.pack(padx=10, pady=8)

        # Mode: immediate vs scheduled
        self.timer_mode = tk.StringVar(value='countdown')
        tk.Radiobutton(inner, text='Ngay lập tức', value='immediate',
                        variable=self.timer_mode, font=FONTS['normal'],
                        bg=COLORS['bg'], fg=COLORS['text'],
                        selectcolor=COLORS['selected'],
                        command=self.toggle_timer).pack(side='left', padx=5)
        tk.Radiobutton(inner, text='Đếm ngược (phút):', value='countdown',
                        variable=self.timer_mode, font=FONTS['normal'],
                        bg=COLORS['bg'], fg=COLORS['text'],
                        selectcolor=COLORS['selected'],
                        command=self.toggle_timer).pack(side='left', padx=5)

        self.minutes_var = tk.StringVar(value='30')
        self.min_entry = tk.Spinbox(inner, from_=1, to=9999,
                                     textvariable=self.minutes_var,
                                     font=FONTS['normal'], width=6)
        self.min_entry.pack(side='left', padx=5)

        tk.Label(inner, text='phút', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left')

        # Specific time
        time_row = tk.Frame(timer_frame, bg=COLORS['bg'])
        time_row.pack(padx=10, pady=(0, 8))
        tk.Radiobutton(time_row, text='Lúc giờ cụ thể:', value='specific',
                        variable=self.timer_mode, font=FONTS['normal'],
                        bg=COLORS['bg'], fg=COLORS['text'],
                        selectcolor=COLORS['selected'],
                        command=self.toggle_timer).pack(side='left', padx=5)
        self.time_entry = tk.Entry(time_row, font=FONTS['normal'], width=8)
        self.time_entry.insert(0, '23:00')
        self.time_entry.pack(side='left', padx=5)
        tk.Label(time_row, text='(HH:MM)', font=FONTS['small'],
                  bg=COLORS['bg'], fg=COLORS['text_light']).pack(side='left')

        # ── Countdown Display ───────────────────────────────────────────
        self.countdown_label = tk.Label(main,
                                         text='⏱ 00:00:00',
                                         font=('Segoe UI', 22, 'bold'),
                                         bg=COLORS['bg'], fg=COLORS['accent'])
        self.countdown_label.pack(pady=5)

        # ── Control Buttons ─────────────────────────────────────────────
        btn_frame = tk.Frame(main, bg=COLORS['bg'])
        btn_frame.pack(pady=5)

        self.btn_start = tk.Button(btn_frame, text='▶ Start',
                                    font=FONTS['subtitle'],
                                    bg=COLORS['accent'], fg='white',
                                    relief='flat', width=12, height=2,
                                    cursor='hand2',
                                    command=self.start_action)
        self.btn_start.pack(side='left', padx=8)

        self.btn_cancel = tk.Button(btn_frame, text='⏹ Cancel',
                                     font=FONTS['subtitle'],
                                     bg=COLORS['danger'], fg='white',
                                     relief='flat', width=12, height=2,
                                     cursor='hand2',
                                     state='disabled',
                                     command=self.cancel_action)
        self.btn_cancel.pack(side='left', padx=8)

        btn_now = tk.Button(btn_frame, text='⚡ Ngay Bây Giờ',
                             font=FONTS['subtitle'],
                             bg=COLORS['warning'], fg='white',
                             relief='flat', width=14, height=2,
                             cursor='hand2',
                             command=self.do_action_now)
        btn_now.pack(side='left', padx=8)

    def on_action_change(self):
        pass

    def browse_app(self):
        path = filedialog.askopenfilename(
            title='Select Application',
            filetypes=[('Executables', '*.exe'), ('All files', '*.*')]
        )
        if path:
            self.app_entry.delete(0, 'end')
            self.app_entry.insert(0, path)

    def toggle_timer(self):
        mode = self.timer_mode.get()
        self.min_entry.configure(state='normal' if mode == 'countdown' else 'disabled')
        self.time_entry.configure(state='normal' if mode == 'specific' else 'disabled')

    def start_action(self):
        if self.countdown_running:
            return
        mode = self.timer_mode.get()
        if mode == 'immediate':
            self.do_action_now()
            return
        elif mode == 'countdown':
            try:
                mins = int(self.minutes_var.get())
                self.remaining = mins * 60
            except:
                messagebox.showerror('Error', 'Số phút không hợp lệ!')
                return
        elif mode == 'specific':
            import datetime
            try:
                t = self.time_entry.get().strip()
                h, m = map(int, t.split(':'))
                now = datetime.datetime.now()
                target = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if target <= now:
                    target += datetime.timedelta(days=1)
                self.remaining = int((target - now).total_seconds())
            except:
                messagebox.showerror('Error', 'Định dạng giờ không hợp lệ! Dùng HH:MM')
                return

        self.countdown_running = True
        self.btn_start.configure(state='disabled')
        self.btn_cancel.configure(state='normal')
        self.countdown_thread = threading.Thread(target=self.run_countdown, daemon=True)
        self.countdown_thread.start()

    def run_countdown(self):
        while self.remaining > 0 and self.countdown_running:
            h = self.remaining // 3600
            m = (self.remaining % 3600) // 60
            s = self.remaining % 60
            self.countdown_label.configure(
                text=f'⏱ {h:02d}:{m:02d}:{s:02d}',
                fg=COLORS['danger'] if self.remaining <= 60 else COLORS['accent']
            )
            time.sleep(1)
            self.remaining -= 1

        if self.countdown_running:
            self.do_action_now()
        self.countdown_running = False
        self.btn_start.configure(state='normal')
        self.btn_cancel.configure(state='disabled')
        self.countdown_label.configure(text='⏱ 00:00:00', fg=COLORS['accent'])

    def cancel_action(self):
        self.countdown_running = False
        self.btn_start.configure(state='normal')
        self.btn_cancel.configure(state='disabled')
        self.countdown_label.configure(text='⏱ 00:00:00', fg=COLORS['accent'])
        # Cancel Windows shutdown if scheduled
        subprocess.run(['shutdown', '/a'], capture_output=True)

    def do_action_now(self):
        action = self.action_var.get()
        try:
            if action == 'shutdown':
                subprocess.run(['shutdown', '/s', '/t', '0'])
            elif action == 'restart':
                subprocess.run(['shutdown', '/r', '/t', '0'])
            elif action == 'hibernate':
                subprocess.run(['shutdown', '/h'])
            elif action == 'logoff':
                subprocess.run(['shutdown', '/l'])
            elif action == 'standby':
                # Use SetSuspendState via powershell
                subprocess.run(['powershell', '-Command',
                                 'Add-Type -Assembly System.Windows.Forms; '
                                 '[System.Windows.Forms.Application]::SetSuspendState("Suspend",$false,$false)'])
            elif action == 'lock':
                import ctypes
                ctypes.windll.user32.LockWorkStation()
            elif action == 'close_app':
                app = self.app_entry.get().strip()
                if app:
                    subprocess.run(['taskkill', '/f', '/im', os.path.basename(app)])
                else:
                    messagebox.showwarning('Warning', 'Nhập tên ứng dụng cần đóng!')
            elif action == 'run_app':
                app = self.app_entry.get().strip()
                if app:
                    subprocess.Popen(app)
                else:
                    messagebox.showwarning('Warning', 'Chọn ứng dụng cần chạy!')
            elif action == 'message':
                msg = self.app_entry.get().strip() or 'IT Tool LTT Notification'
                messagebox.showinfo('Thông báo', msg)
        except Exception as e:
            messagebox.showerror('Error', f'Lỗi thực thi: {e}')


# ── STANDALONE TASK SCHEDULER BACKEND API FUNCTIONS ───────────────────────

import base64

def _run_ps(ps_script, timeout=10):
    """Executes PowerShell script via Base64 EncodedCommand to avoid escaping issues."""
    encoded = base64.b64encode(ps_script.encode('utf-16le')).decode('utf-8')
    return subprocess.run(["powershell", "-NoProfile", "-EncodedCommand", encoded], capture_output=True, text=True, timeout=timeout)


def execute_immediate_power(action):
    """Executes immediate system power operation (Shutdown, Restart, Sleep, Logoff, Lock)."""
    try:
        if action in ("shutdown", "shutdown_now"):
            cmd = "shutdown /s /f /t 0"
            msg = "Đã phát lệnh Tắt máy ngay lập tức."
        elif action in ("restart", "restart_now"):
            cmd = "shutdown /r /f /t 0"
            msg = "Đã phát lệnh Khởi động lại ngay lập tức."
        elif action in ("hibernate", "sleep"):
            cmd = 'powershell -Command "Add-Type -Assembly System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState(\'Suspend\', $false, $false)"'
            msg = "Đã chuyển hệ thống sang chế độ Sleep/Hibernate."
        elif action == "logoff":
            cmd = "shutdown /l"
            msg = "Đã đăng xuất tài khoản người dùng."
        elif action == "lock":
            cmd = "rundll32.exe user32.dll,LockWorkStation"
            msg = "Đã khóa màn hình máy tính."
        elif action == "cancel":
            cmd = "shutdown /a"
            msg = "Đã hủy lệnh hẹn giờ tắt máy hệ thống."
        else:
            return {"success": False, "message": f"Hành động không hợp lệ: {action}"}

        subprocess.run(cmd, shell=True)
        return {"success": True, "message": msg}
    except Exception as e:
        return {"success": False, "message": f"Lỗi thực thi: {str(e)}"}


def create_quick_timer_task(action, minutes, message=""):
    """Creates a one-time Windows Task Scheduler task for quick timer, ensuring execution even if app is closed."""
    import datetime
    try:
        sec = float(minutes) * 60
        if sec <= 0:
            return {"success": False, "message": "Số phút phải lớn hơn 0!"}
    except Exception as e:
        return {"success": False, "message": f"Số phút không hợp lệ: {e}"}

    target_dt = datetime.datetime.now() + datetime.timedelta(seconds=sec)
    dt_str = target_dt.strftime("%Y-%m-%d %H:%M:%S")

    # Sanitize message to prevent PowerShell injection
    safe_msg = (message.strip() or f"Tu dong {action} boi IT Tool LTT Quick Timer").replace('"', '').replace("'", "").replace("`", "")

    if action == "shutdown":
        exe = "shutdown.exe"
        args = f'/s /f /t 0 /c "{safe_msg}"'
    elif action == "restart":
        exe = "shutdown.exe"
        args = f'/r /f /t 0 /c "{safe_msg}"'
    elif action == "hibernate":
        exe = "powershell.exe"
        args = '-Command "Add-Type -Assembly System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState(\'Suspend\', $false, $false)"'
    elif action == "logoff":
        exe = "shutdown.exe"
        args = "/l"
    elif action == "lock":
        exe = "%windir%\\System32\\rundll32.exe"
        args = "user32.dll,LockWorkStation"
    else:
        exe = "shutdown.exe"
        args = f'/s /f /t 0 /c "{safe_msg}"'

    full_name = "ITTools_Shutdown_QuickTimer"

    ps_code = f"""
    $dt = [datetime]::ParseExact('{dt_str}', 'yyyy-MM-dd HH:mm:ss', $null)
    $trig = New-ScheduledTaskTrigger -Once -At $dt
    $act = New-ScheduledTaskAction -Execute "{exe}" -Argument '{args}'
    $princ = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName "{full_name}" -Trigger $trig -Action $act -Principal $princ -Settings $settings -Force
    """

    try:
        r = _run_ps(ps_code, timeout=10)
        if r.returncode == 0:
            action_names = {
                "shutdown": "Tắt máy",
                "restart": "Khởi động lại",
                "hibernate": "Sleep / Hibernate",
                "logoff": "Đăng xuất",
                "lock": "Khóa màn hình"
            }
            act_label = action_names.get(action, action)
            return {
                "success": True,
                "message": f"Đã lưu lịch {act_label} lúc {target_dt.strftime('%H:%M:%S')} vào Windows Task Scheduler. Dù bạn TẮT PHẦN MỀM thì máy vẫn sẽ tự động thực thi!",
                "target_time": dt_str
            }
        else:
            return {"success": False, "message": f"Lỗi tạo lịch Windows Task Scheduler: {r.stderr or r.stdout}"}
    except Exception as e:
        return {"success": False, "message": f"Lỗi ngoại lệ: {str(e)}"}


def cancel_quick_timer_task():
    """Cancels the quick timer Windows Task Scheduler task."""
    full_name = "ITTools_Shutdown_QuickTimer"
    ps_code = f'Unregister-ScheduledTask -TaskName "{full_name}" -Confirm:$false -ErrorAction SilentlyContinue'
    try:
        _run_ps(ps_code, timeout=8)
        subprocess.run("shutdown /a", shell=True, capture_output=True)
        return {"success": True, "message": "Đã hủy lịch đếm ngược Quick Timer trong Windows Task Scheduler!"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_scheduled_shutdown_tasks():
    """Returns all scheduled shutdown tasks created by IT Tool LTT."""
    ps_code = """
    $tasks = Get-ScheduledTask -TaskPath '\\' -ErrorAction SilentlyContinue | Where-Object { $_.TaskName -like 'ITTools_Shutdown_*' }
    if (-not $tasks) { Write-Output "[]"; exit }
    $res = @()
    foreach ($t in $tasks) {
        $info = Get-ScheduledTaskInfo -TaskName $t.TaskName -ErrorAction SilentlyContinue
        $res += [PSCustomObject]@{
            TaskName = $t.TaskName
            State = $t.State.ToString()
            NextRun = if ($info.NextRunTime) { $info.NextRunTime.ToString('yyyy-MM-dd HH:mm:ss') } else { '' }
            LastRun = if ($info.LastRunTime) { $info.LastRunTime.ToString('yyyy-MM-dd HH:mm:ss') } else { '' }
            Execute = $t.Actions.Execute
            Arguments = $t.Actions.Arguments
        }
    }
    @($res) | ConvertTo-Json -Depth 3
    """
    try:
        r = _run_ps(ps_code, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            data = json.loads(r.stdout)
            if not data:
                return {"success": True, "tasks": []}
            if isinstance(data, dict):
                data = [data]
            if not isinstance(data, list):
                return {"success": True, "tasks": []}
            parsed = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                tn = item.get("TaskName", "") or ""
                disp_name = tn.replace("ITTools_Shutdown_", "").replace("_", " ")
                args = item.get("Arguments", "") or ""
                
                action_type = "shutdown"
                if "/r" in args:
                    action_type = "restart"
                elif "/h" in args:
                    action_type = "hibernate"
                elif "/l" in args:
                    action_type = "logoff"
                elif "LockWorkStation" in args or "user32.dll" in args:
                    action_type = "lock"

                parsed.append({
                    "task_name": tn,
                    "display_name": disp_name,
                    "action": action_type,
                    "state": item.get("State", "Unknown"),
                    "enabled": (item.get("State", "") or "").lower() != "disabled",
                    "next_run": item.get("NextRun", "") or "N/A",
                    "last_run": item.get("LastRun", "") or "N/A",
                    "arguments": args
                })
            return {"success": True, "tasks": parsed}
    except Exception as e:
        print("Lỗi get_scheduled_shutdown_tasks:", e)
    return {"success": True, "tasks": []}


def create_scheduled_shutdown_task(name, action, freq, time_str, days=None, date_str="", message=""):
    """Creates a Windows Task Scheduler auto shutdown task."""
    import datetime as dt_module
    if not name or not name.strip():
        return {"success": False, "message": "Vui lòng nhập tên lịch hẹn giờ!"}
    
    clean_name = "".join(c for c in name.strip() if c.isalnum() or c in ("_", "-")).strip()
    if not clean_name:
        clean_name = "Task_" + dt_module.datetime.now().strftime("%Y%m%d%H%M%S")
    full_name = f"ITTools_Shutdown_{clean_name}"
    
    # Sanitize message to prevent PowerShell injection
    safe_msg = (message.strip() or f"Tu dong {action} boi IT Tool LTT").replace('"', '').replace("'", "").replace("`", "")

    if action == "shutdown":
        exe = "shutdown.exe"
        args = f'/s /f /t 60 /c "{safe_msg}"'
    elif action == "restart":
        exe = "shutdown.exe"
        args = f'/r /f /t 60 /c "{safe_msg}"'
    elif action == "hibernate":
        exe = "shutdown.exe"
        args = "/h"
    elif action == "logoff":
        exe = "shutdown.exe"
        args = "/l"
    elif action == "lock":
        exe = "%windir%\\System32\\rundll32.exe"
        args = "user32.dll,LockWorkStation"
    else:
        exe = "shutdown.exe"
        args = f'/s /f /t 60 /c "{safe_msg}"'

    time_val = time_str.strip() or "23:00"

    if freq == "daily":
        trig_cmd = f'New-ScheduledTaskTrigger -Daily -At "{time_val}"'
    elif freq == "weekly":
        if not days or len(days) == 0:
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        days_str = ",".join(days)
        trig_cmd = f'New-ScheduledTaskTrigger -Weekly -DaysOfWeek {days_str} -At "{time_val}"'
    elif freq == "once":
        today_str = dt_module.datetime.now().strftime('%Y-%m-%d')
        dt_val = f"{date_str.strip()} {time_val}" if date_str.strip() else f"{today_str} {time_val}"
        trig_cmd = f'New-ScheduledTaskTrigger -Once -At "{dt_val}"'
    else:
        trig_cmd = f'New-ScheduledTaskTrigger -Daily -At "{time_val}"'

    ps_code = f"""
    $trig = {trig_cmd}
    $act = New-ScheduledTaskAction -Execute "{exe}" -Argument '{args}'
    $princ = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun
    Register-ScheduledTask -TaskName "{full_name}" -Trigger $trig -Action $act -Principal $princ -Settings $settings -Force
    """
    try:
        r = _run_ps(ps_code, timeout=10)
        if r.returncode == 0:
            return {"success": True, "message": f"Đã tạo thành công lịch '{clean_name}' ({freq.upper()} lúc {time_val})!"}
        else:
            return {"success": False, "message": f"Lỗi PowerShell: {r.stderr or r.stdout}"}
    except Exception as e:
        return {"success": False, "message": f"Lỗi ngoại lệ: {str(e)}"}


def toggle_scheduled_shutdown_task(task_name, enable):
    """Enables or disables a scheduled shutdown task."""
    cmd_verb = "Enable-ScheduledTask" if enable else "Disable-ScheduledTask"
    ps_code = f'{cmd_verb} -TaskName "{task_name}"'
    try:
        r = _run_ps(ps_code, timeout=8)
        if r.returncode == 0:
            st = "bật" if enable else "tắt"
            return {"success": True, "message": f"Đã {st} lịch hẹn giờ '{task_name.replace('ITTools_Shutdown_', '')}' thành công!"}
        else:
            return {"success": False, "message": r.stderr or r.stdout}
    except Exception as e:
        return {"success": False, "message": str(e)}


def delete_scheduled_shutdown_task(task_name):
    """Deletes a scheduled shutdown task."""
    ps_code = f'Unregister-ScheduledTask -TaskName "{task_name}" -Confirm:$false'
    try:
        r = _run_ps(ps_code, timeout=8)
        if r.returncode == 0:
            return {"success": True, "message": f"Đã xóa lịch hẹn giờ '{task_name.replace('ITTools_Shutdown_', '')}'!"}
        else:
            return {"success": False, "message": r.stderr or r.stdout}
    except Exception as e:
        return {"success": False, "message": str(e)}


def run_scheduled_shutdown_task_now(task_name):
    """Executes a scheduled shutdown task immediately."""
    ps_code = f'Start-ScheduledTask -TaskName "{task_name}"'
    try:
        r = _run_ps(ps_code, timeout=8)
        if r.returncode == 0:
            return {"success": True, "message": f"Đã kích hoạt chạy ngay lịch '{task_name.replace('ITTools_Shutdown_', '')}'!"}
        else:
            return {"success": False, "message": r.stderr or r.stdout}
    except Exception as e:
        return {"success": False, "message": str(e)}


