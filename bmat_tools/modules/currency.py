"""
Currency Converter Module
VND, USD, JPY, CNY, Silver, Gold, Bitcoin
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from constants import COLORS, FONTS


class Currency:
    def __init__(self, parent):
        self.parent = parent
        self.parent.geometry('700x580')
        self.parent.configure(bg=COLORS['bg'])
        self.rates = {}
        self.setup_ui()
        threading.Thread(target=self.fetch_rates, daemon=True).start()

    def setup_ui(self):
        hdr = tk.Frame(self.parent, bg=COLORS['bg_header'])
        hdr.pack(fill='x')
        tk.Label(hdr, text='💰  Currency Converter', font=FONTS['large'],
                  bg=COLORS['bg_header'], fg='white', pady=10).pack(side='left', padx=15)
        tk.Button(hdr, text='🔄 Refresh Rates', font=FONTS['small'],
                   bg=COLORS['accent'], fg='white', relief='flat',
                   padx=8, pady=4, cursor='hand2',
                   command=lambda: threading.Thread(
                       target=self.fetch_rates, daemon=True).start()
                   ).pack(side='right', padx=15, pady=8)

        # Rate display panel
        rates_frame = tk.LabelFrame(self.parent, text='  Live Rates (Base: 1 USD)  ',
                                     font=FONTS['subtitle'], bg=COLORS['bg'],
                                     relief='groove')
        rates_frame.pack(fill='x', padx=15, pady=10)

        self.rate_vars = {}
        currencies = [
            ('VND 🇻🇳', 'VND', '#27AE60'),
            ('JPY 🇯🇵', 'JPY', '#E74C3C'),
            ('CNY 🇨🇳', 'CNY', '#F39C12'),
            ('EUR 🇪🇺', 'EUR', '#3498DB'),
            ('GBP 🇬🇧', 'GBP', '#9B59B6'),
            ('SGD 🇸🇬', 'SGD', '#1ABC9C'),
            ('Gold 🥇', 'XAU', '#F1C40F'),
            ('Silver 🥈', 'XAG', '#95A5A6'),
            ('BTC ₿', 'BTC', '#E67E22'),
        ]
        row, col = 0, 0
        for i, (label, code, color) in enumerate(currencies):
            frame = tk.Frame(rates_frame, bg=COLORS['bg'], relief='groove',
                              bd=1, padx=10, pady=5)
            frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')

            tk.Label(frame, text=label, font=FONTS['subtitle'],
                      bg=COLORS['bg'], fg=color).pack(anchor='w')
            var = tk.StringVar(value='Loading...')
            self.rate_vars[code] = var
            tk.Label(frame, textvariable=var, font=('Consolas', 11),
                      bg=COLORS['bg'], fg=COLORS['text']).pack(anchor='w')

            col += 1
            if col >= 3:
                col = 0
                row += 1

        for c in range(3):
            rates_frame.columnconfigure(c, weight=1)

        # Converter
        conv_frame = tk.LabelFrame(self.parent, text='  Converter  ',
                                    font=FONTS['subtitle'], bg=COLORS['bg'],
                                    relief='groove')
        conv_frame.pack(fill='x', padx=15, pady=5)

        inner = tk.Frame(conv_frame, bg=COLORS['bg'])
        inner.pack(padx=15, pady=10)

        tk.Label(inner, text='Amount:', font=FONTS['normal'],
                  bg=COLORS['bg']).grid(row=0, column=0, padx=5, pady=5)
        self.amount_var = tk.StringVar(value='1')
        tk.Entry(inner, textvariable=self.amount_var, font=FONTS['subtitle'],
                  width=15).grid(row=0, column=1, padx=5)

        tk.Label(inner, text='From:', font=FONTS['normal'],
                  bg=COLORS['bg']).grid(row=0, column=2, padx=10)
        currency_codes = ['USD', 'VND', 'JPY', 'CNY', 'EUR', 'GBP',
                           'SGD', 'XAU', 'XAG', 'BTC']
        self.from_currency = ttk.Combobox(inner, values=currency_codes,
                                           width=8, state='readonly',
                                           font=FONTS['normal'])
        self.from_currency.set('USD')
        self.from_currency.grid(row=0, column=3, padx=5)

        tk.Label(inner, text='To:', font=FONTS['normal'],
                  bg=COLORS['bg']).grid(row=0, column=4, padx=10)
        self.to_currency = ttk.Combobox(inner, values=currency_codes,
                                         width=8, state='readonly',
                                         font=FONTS['normal'])
        self.to_currency.set('VND')
        self.to_currency.grid(row=0, column=5, padx=5)

        tk.Button(inner, text='🔄 Convert', font=FONTS['subtitle'],
                   bg=COLORS['accent'], fg='white', relief='flat',
                   padx=15, pady=5, cursor='hand2',
                   command=self.convert).grid(row=0, column=6, padx=10)

        # Result
        self.result_var = tk.StringVar(value='= ?')
        tk.Label(conv_frame, textvariable=self.result_var,
                  font=('Segoe UI', 16, 'bold'), bg=COLORS['bg'],
                  fg=COLORS['accent']).pack(pady=8)

        # Quick convert VND
        vnd_frame = tk.LabelFrame(self.parent, text='  VND Quick Table  ',
                                   font=FONTS['subtitle'], bg=COLORS['bg'])
        vnd_frame.pack(fill='x', padx=15, pady=5)

        self.vnd_table = tk.Text(vnd_frame, font=FONTS['mono'],
                                  bg='#1E1E1E', fg='#D4D4D4',
                                  height=5, relief='flat', padx=10, pady=5)
        self.vnd_table.pack(fill='x', padx=5, pady=5)

        # Status
        self.status_var = tk.StringVar(value='Fetching rates...')
        tk.Label(self.parent, textvariable=self.status_var,
                  font=FONTS['small'], bg=COLORS['bg'],
                  fg=COLORS['text_light']).pack(pady=3)

    def fetch_rates(self):
        self.status_var.set('⏳ Fetching live rates...')
        try:
            import urllib.request
            import json

            # Free currency API
            url = 'https://api.exchangerate-api.com/v4/latest/USD'
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
                self.rates = data.get('rates', {})

            # Try to get gold/silver/BTC prices
            try:
                btc_url = 'https://api.coindesk.com/v1/bpi/currentprice.json'
                with urllib.request.urlopen(btc_url, timeout=5) as resp:
                    btc_data = json.loads(resp.read())
                    btc_usd = float(btc_data['bpi']['USD']['rate'].replace(',', ''))
                    self.rates['BTC'] = 1 / btc_usd
            except:
                pass

            # Update display
            display_map = {
                'VND': lambda r: f'{r:,.0f} ₫',
                'JPY': lambda r: f'{r:,.0f} ¥',
                'CNY': lambda r: f'{r:,.2f} ¥',
                'EUR': lambda r: f'{r:.4f} €',
                'GBP': lambda r: f'{r:.4f} £',
                'SGD': lambda r: f'{r:.4f} S$',
                'XAU': lambda r: f'{1/r:,.2f} $/oz' if r else 'N/A',
                'XAG': lambda r: f'{1/r:,.2f} $/oz' if r else 'N/A',
                'BTC': lambda r: f'{1/r:,.2f} $' if r else 'N/A',
            }
            for code, fmt in display_map.items():
                rate = self.rates.get(code)
                if rate and code in self.rate_vars:
                    self.rate_vars[code].set(fmt(rate))

            self._update_vnd_table()
            self.status_var.set(f'✅ Rates updated at {data.get("date", "N/A")}')
        except Exception as e:
            self.status_var.set(f'❌ Cannot fetch rates: {e}')
            # Use fallback rates
            fallback = {'VND': 24500, 'JPY': 149.5, 'CNY': 7.24,
                         'EUR': 0.92, 'GBP': 0.79, 'SGD': 1.34}
            self.rates.update(fallback)
            for code, rate in fallback.items():
                if code in self.rate_vars:
                    self.rate_vars[code].set(f'{rate:,.2f}')

    def _update_vnd_table(self):
        vnd = self.rates.get('VND', 24500)
        usd = self.rates.get('USD', 1)

        self.vnd_table.configure(state='normal')
        self.vnd_table.delete('1.0', 'end')
        rows = [
            ('1 USD', f'{vnd:,.0f} VND'),
            ('100 USD', f'{100*vnd:,.0f} VND'),
            ('1,000 USD', f'{1000*vnd:,.0f} VND'),
            ('100,000 VND', f'{100000/vnd:.2f} USD'),
            ('1,000,000 VND', f'{1000000/vnd:.2f} USD'),
        ]
        for k, v in rows:
            self.vnd_table.insert('end', f'  {k:<18} = {v}\n')
        self.vnd_table.configure(state='disabled')

    def convert(self):
        try:
            amount = float(self.amount_var.get().replace(',', ''))
            from_c = self.from_currency.get()
            to_c = self.to_currency.get()

            if not self.rates:
                messagebox.showwarning('Warning', 'Chưa có tỷ giá! Bấm Refresh.')
                return

            # Convert to USD first, then to target
            from_rate = self.rates.get(from_c, 1)
            to_rate = self.rates.get(to_c, 1)

            if from_c == 'USD':
                usd_amount = amount
            else:
                usd_amount = amount / from_rate

            result = usd_amount * to_rate

            # Format
            if result > 1000:
                formatted = f'{result:,.2f}'
            elif result > 0.01:
                formatted = f'{result:.4f}'
            else:
                formatted = f'{result:.8f}'

            self.result_var.set(
                f'{amount:,g} {from_c} = {formatted} {to_c}'
            )
        except ValueError:
            messagebox.showerror('Error', 'Số tiền không hợp lệ!')
        except Exception as e:
            messagebox.showerror('Error', str(e))
