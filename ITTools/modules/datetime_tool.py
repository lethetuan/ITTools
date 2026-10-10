"""
DateTime Tool Module - +7 Timezone, Calendar display
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import datetime
import threading
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS


class DateTimeTool:
    def __init__(self, parent):
        self.parent = parent
        self.parent.geometry('600x560')
        self.parent.configure(bg=COLORS['bg'])
        self.running = True
        self.setup_ui()
        self.update_clock()

    def setup_ui(self):
        hdr = tk.Frame(self.parent, bg=COLORS['bg_header'])
        hdr.pack(fill='x')
        tk.Label(hdr, text='🕐  Date & Time Manager', font=FONTS['large'],
                  bg=COLORS['bg_header'], fg='white', pady=10).pack(side='left', padx=15)

        self.parent.protocol('WM_DELETE_WINDOW', self.on_close)

        # Live clock
        clock_frame = tk.Frame(self.parent, bg='#1E1E1E', pady=20)
        clock_frame.pack(fill='x')

        self.time_var = tk.StringVar()
        tk.Label(clock_frame, textvariable=self.time_var,
                  font=('Consolas', 36, 'bold'),
                  bg='#1E1E1E', fg='#00FF41').pack()

        self.date_var = tk.StringVar()
        tk.Label(clock_frame, textvariable=self.date_var,
                  font=('Segoe UI', 14), bg='#1E1E1E', fg='#BDC3C7').pack()

        self.week_var = tk.StringVar()
        tk.Label(clock_frame, textvariable=self.week_var,
                  font=('Segoe UI', 11), bg='#1E1E1E', fg='#7F8C8D').pack()

        # World clock
        world_frame = tk.LabelFrame(self.parent, text='  World Clock  ',
                                     font=FONTS['subtitle'], bg=COLORS['bg'])
        world_frame.pack(fill='x', padx=15, pady=8)

        zones = [
            ('🇻🇳 Vietnam (UTC+7)', 7, '#27AE60'),
            ('🇺🇸 New York (UTC-4)', -4, '#2980B9'),
            ('🇬🇧 London (UTC+1)', 1, '#8E44AD'),
            ('🇯🇵 Tokyo (UTC+9)', 9, '#E74C3C'),
            ('🇸🇬 Singapore (UTC+8)', 8, '#F39C12'),
            ('🇦🇺 Sydney (UTC+10)', 10, '#16A085'),
        ]
        self.tz_vars = {}
        for i, (name, offset, color) in enumerate(zones):
            frame = tk.Frame(world_frame, bg=COLORS['bg'])
            frame.grid(row=i // 3, column=i % 3, padx=5, pady=4, sticky='w')
            tk.Label(frame, text=name, font=FONTS['small'],
                      bg=COLORS['bg'], fg=color, width=22).pack(side='left')
            var = tk.StringVar(value='--:--:--')
            self.tz_vars[offset] = var
            tk.Label(frame, textvariable=var, font=('Consolas', 10, 'bold'),
                      bg=COLORS['bg'], fg=COLORS['text']).pack(side='left')

        for c in range(3):
            world_frame.columnconfigure(c, weight=1)

        # Set Date/Time
        set_frame = tk.LabelFrame(self.parent, text='  Set Date & Time  ',
                                   font=FONTS['subtitle'], bg=COLORS['bg'],
                                   relief='groove')
        set_frame.pack(fill='x', padx=15, pady=5)

        row = tk.Frame(set_frame, bg=COLORS['bg'])
        row.pack(padx=10, pady=8, fill='x')

        now = datetime.datetime.now()
        tk.Label(row, text='Date:', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left', padx=5)
        self.date_day = tk.Spinbox(row, from_=1, to=31, width=4,
                                    font=FONTS['normal'])
        self.date_day.delete(0, 'end')
        self.date_day.insert(0, str(now.day))
        self.date_day.pack(side='left', padx=2)
        tk.Label(row, text='/', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left')
        self.date_month = tk.Spinbox(row, from_=1, to=12, width=4,
                                      font=FONTS['normal'])
        self.date_month.delete(0, 'end')
        self.date_month.insert(0, str(now.month))
        self.date_month.pack(side='left', padx=2)
        tk.Label(row, text='/', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left')
        self.date_year = tk.Spinbox(row, from_=2000, to=2099, width=6,
                                     font=FONTS['normal'])
        self.date_year.delete(0, 'end')
        self.date_year.insert(0, str(now.year))
        self.date_year.pack(side='left', padx=2)

        tk.Label(row, text='  Time:', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left', padx=10)
        self.time_hour = tk.Spinbox(row, from_=0, to=23, width=4,
                                     font=FONTS['normal'])
        self.time_hour.delete(0, 'end')
        self.time_hour.insert(0, str(now.hour))
        self.time_hour.pack(side='left', padx=2)
        tk.Label(row, text=':', font=FONTS['normal'],
                  bg=COLORS['bg']).pack(side='left')
        self.time_min = tk.Spinbox(row, from_=0, to=59, width=4,
                                    font=FONTS['normal'])
        self.time_min.delete(0, 'end')
        self.time_min.insert(0, str(now.minute))
        self.time_min.pack(side='left', padx=2)

        btn_row = tk.Frame(set_frame, bg=COLORS['bg'])
        btn_row.pack(pady=5)
        tk.Button(btn_row, text='✅ Set Date/Time', font=FONTS['subtitle'],
                   bg=COLORS['accent'], fg='white', relief='flat',
                   padx=15, pady=6, cursor='hand2',
                   command=self.set_datetime).pack(side='left', padx=5)
        tk.Button(btn_row, text='🌐 Sync with Internet', font=FONTS['subtitle'],
                   bg=COLORS['info'], fg='white', relief='flat',
                   padx=15, pady=6, cursor='hand2',
                   command=self.sync_internet_time).pack(side='left', padx=5)
        tk.Button(btn_row, text='⚙️ Time Settings', font=FONTS['subtitle'],
                   bg='#8E44AD', fg='white', relief='flat',
                   padx=15, pady=6, cursor='hand2',
                   command=lambda: subprocess.Popen(
                       'start ms-settings:dateandtime', shell=True)
                   ).pack(side='left', padx=5)

        # Timezone
        tz_frame = tk.LabelFrame(self.parent, text='  Timezone (+7 Vietnam)  ',
                                  font=FONTS['subtitle'], bg=COLORS['bg'])
        tz_frame.pack(fill='x', padx=15, pady=5)

        tz_row = tk.Frame(tz_frame, bg=COLORS['bg'])
        tz_row.pack(padx=10, pady=5)
        tk.Button(tz_row, text='🇻🇳 Set to UTC+7 (Vietnam)',
                   font=FONTS['subtitle'], bg='#E74C3C', fg='white',
                   relief='flat', padx=15, pady=6, cursor='hand2',
                   command=self.set_vietnam_timezone).pack(side='left', padx=5)
        tk.Button(tz_row, text='⚙️ Timezone Settings',
                   font=FONTS['subtitle'], bg=COLORS['info'], fg='white',
                   relief='flat', padx=15, pady=6, cursor='hand2',
                   command=lambda: subprocess.Popen(
                       ['control', 'timedate.cpl,@0,/Z', 'TimeZone'])
                   ).pack(side='left', padx=5)

    def update_clock(self):
        if not self.running:
            return
        utc_now = datetime.datetime.utcnow()
        local_now = datetime.datetime.now()

        day_names = ['Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm',
                      'Thứ Sáu', 'Thứ Bảy', 'Chủ Nhật']
        month_names = ['Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4',
                        'Tháng 5', 'Tháng 6', 'Tháng 7', 'Tháng 8',
                        'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12']

        self.time_var.set(local_now.strftime('%H:%M:%S'))
        self.date_var.set(
            f'Ngày {local_now.day:02d} {month_names[local_now.month-1]} {local_now.year}')
        self.week_var.set(day_names[local_now.weekday()])

        # World clocks
        for offset, var in self.tz_vars.items():
            tz_time = utc_now + datetime.timedelta(hours=offset)
            var.set(tz_time.strftime('%H:%M:%S'))

        self.parent.after(1000, self.update_clock)

    def set_datetime(self):
        try:
            day = self.date_day.get()
            month = self.date_month.get()
            year = self.date_year.get()
            hour = self.time_hour.get()
            minute = self.time_min.get()

            # Set date
            subprocess.run(['cmd', '/c', f'date {day}/{month}/{year}'], shell=True)
            # Set time
            subprocess.run(['cmd', '/c', f'time {hour}:{minute}:00'], shell=True)
            messagebox.showinfo('Success', '✅ Đã cài ngày giờ!')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def sync_internet_time(self):
        subprocess.run(['w32tm', '/resync', '/force'], capture_output=True)
        subprocess.run(['net', 'start', 'w32tm'], capture_output=True)
        messagebox.showinfo('Sync', '✅ Đã đồng bộ thời gian Internet!')

    def set_vietnam_timezone(self):
        result = subprocess.run(
            ['tzutil', '/s', 'SE Asia Standard Time'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            messagebox.showinfo('Timezone', '✅ Đã cài Vietnam timezone (UTC+7)!')
        else:
            messagebox.showerror('Error', result.stderr)

    def on_close(self):
        self.running = False
        self.parent.destroy()
