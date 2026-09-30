/**
 * IT Tool LTT 2026 - Currency Converter Module - Realtime Exchange Rates & Calculator
 * Author: Lê Thế Tuấn | 0352 194 195 | https://lethetuanpc.blogspot.com | Telegram: https://t.me/lethetuanpc
 */

Object.assign(AppController.prototype, {
  currencyRates: {
    USD: 1.0,
    VND: 25450.0,
    EUR: 0.92,
    JPY: 152.5,
    GBP: 0.78,
    CNY: 7.24,
    SGD: 1.34,
    AUD: 1.51,
    CAD: 1.37,
    CHF: 0.88,
    KRW: 1380.0,
    THB: 36.5,
    BTC: 0.000015,
    XAU: 0.000366
  },
  currencyUpdatedAt: "",

  async loadCurrencyRates() {
    const grid = document.getElementById("currency-rates-grid");
    const timeSpan = document.getElementById("currency-updated-time");

    if (grid) {
      grid.innerHTML = `<div class="text-center py-3 text-muted" style="grid-column: 1 / -1;">🔄 Đang tải tỷ giá ngoại tệ mới nhất...</div>`;
    }

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.get_currency_rates();
        if (res && res.success && res.rates) {
          this.currencyRates = res.rates;
          this.currencyUpdatedAt = res.updated_at || new Date().toLocaleTimeString();
        }
      } catch (err) {
        console.warn("Lỗi API get_currency_rates, dùng tỷ giá dự phòng:", err);
      }
    } else {
      try {
        const resp = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
        const data = await resp.json();
        if (data && data.rates) {
          this.currencyRates = { ...this.currencyRates, ...data.rates };
          this.currencyUpdatedAt = data.date || new Date().toLocaleTimeString();
        }
      } catch (e) {
        this.currencyUpdatedAt = "Tỷ giá tham khảo";
      }
    }

    if (timeSpan) {
      timeSpan.textContent = `⏰ Cập nhật: ${this.currencyUpdatedAt}`;
    }

    this.renderCurrencyRatesGrid();
    this.calculateCurrencyConvert();
    this.renderVndQuickTable();
  },

  renderCurrencyRatesGrid() {
    const grid = document.getElementById("currency-rates-grid");
    if (!grid) return;

    const currenciesToDisplay = [
      { code: "VND", name: "Việt Nam", flag: "🇻🇳", format: (r) => `${Math.round(r).toLocaleString()} ₫` },
      { code: "EUR", name: "Châu Âu", flag: "🇪🇺", format: (r) => `${r.toFixed(4)} €` },
      { code: "JPY", name: "Nhật Bản", flag: "🇯🇵", format: (r) => `${r.toFixed(2)} ¥` },
      { code: "GBP", name: "Nước Anh", flag: "🇬🇧", format: (r) => `${r.toFixed(4)} £` },
      { code: "CNY", name: "Trung Quốc", flag: "🇨🇳", format: (r) => `${r.toFixed(2)} ¥` },
      { code: "SGD", name: "Singapore", flag: "🇸🇬", format: (r) => `${r.toFixed(4)} S$` },
      { code: "AUD", name: "Nước Úc", flag: "🇦🇺", format: (r) => `${r.toFixed(4)} A$` },
      { code: "BTC", name: "Bitcoin", flag: "₿", format: (r) => `$${(1 / r).toLocaleString(undefined, { maximumFractionDigits: 0 })}` },
      { code: "XAU", name: "Vàng SJC", flag: "🥇", format: (r) => `${Math.round(1 / r * 25450 / 0.83).toLocaleString()} ₫/lượng` }
    ];

    grid.innerHTML = currenciesToDisplay.map(c => {
      const rate = this.currencyRates[c.code] || 0;
      const displayVal = rate > 0 ? c.format(rate) : "N/A";

      return `
        <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); display: flex; align-items: center; justify-content: space-between;">
          <div>
            <div style="font-size: 11px; color: #64748b; font-weight: 600;">${c.flag} ${c.code} (${c.name})</div>
            <div style="font-size: 14px; font-weight: 700; color: #0f172a; margin-top: 2px;">${displayVal}</div>
          </div>
        </div>
      `;
    }).join("");
  },

  calculateCurrencyConvert() {
    const amountInput = document.getElementById("currency-amount");
    const fromSelect = document.getElementById("currency-from");
    const toSelect = document.getElementById("currency-to");
    const resultText = document.getElementById("currency-result-text");
    const unitRateText = document.getElementById("currency-unit-rate");

    if (!amountInput || !fromSelect || !toSelect || !resultText) return;

    const amount = parseFloat(amountInput.value) || 0;
    const fromCode = fromSelect.value;
    const toCode = toSelect.value;

    const fromRate = this.currencyRates[fromCode] || 1;
    const toRate = this.currencyRates[toCode] || 1;

    // Convert to USD base first
    const usdAmount = fromCode === "USD" ? amount : amount / fromRate;
    const convertedValue = toCode === "USD" ? usdAmount : usdAmount * toRate;

    // Unit rate (1 From = ? To)
    const unitUsd = fromCode === "USD" ? 1 : 1 / fromRate;
    const unitConverted = toCode === "USD" ? unitUsd : unitUsd * toRate;

    let formattedValue = "";
    if (convertedValue >= 1000) {
      formattedValue = convertedValue.toLocaleString(undefined, { maximumFractionDigits: 2 });
    } else if (convertedValue >= 0.01) {
      formattedValue = convertedValue.toFixed(4);
    } else {
      formattedValue = convertedValue.toFixed(8);
    }

    let unitFormatted = "";
    if (unitConverted >= 1000) {
      unitFormatted = unitConverted.toLocaleString(undefined, { maximumFractionDigits: 2 });
    } else {
      unitFormatted = unitConverted.toFixed(4);
    }

    resultText.innerHTML = `<strong>${amount.toLocaleString()} ${fromCode}</strong> = <span style="color: #0284c7;">${formattedValue} ${toCode}</span>`;
    
    if (unitRateText) {
      unitRateText.textContent = `Tỷ giá tham khảo: 1 ${fromCode} ≈ ${unitFormatted} ${toCode}`;
    }
  },

  swapCurrencies() {
    const fromSelect = document.getElementById("currency-from");
    const toSelect = document.getElementById("currency-to");
    if (fromSelect && toSelect) {
      const temp = fromSelect.value;
      fromSelect.value = toSelect.value;
      toSelect.value = temp;
      this.calculateCurrencyConvert();
    }
  },

  setQuickCurrency(amount, fromCode, toCode) {
    const amountInput = document.getElementById("currency-amount");
    const fromSelect = document.getElementById("currency-from");
    const toSelect = document.getElementById("currency-to");

    if (amountInput) amountInput.value = amount;
    if (fromSelect) fromSelect.value = fromCode;
    if (toSelect) toSelect.value = toCode;

    this.calculateCurrencyConvert();
  },

  renderVndQuickTable() {
    const container = document.getElementById("currency-quick-table");
    if (!container) return;

    const usdRate = this.currencyRates["VND"] || 25450;
    const eurRate = (this.currencyRates["VND"] || 25450) / (this.currencyRates["EUR"] || 0.92);
    const jpyRate = (this.currencyRates["VND"] || 25450) / (this.currencyRates["JPY"] || 152.5);

    const rows = [
      { label: "1 USD", val: `${Math.round(usdRate).toLocaleString()} VNĐ` },
      { label: "100 USD", val: `${Math.round(100 * usdRate).toLocaleString()} VNĐ` },
      { label: "1,000 USD", val: `${Math.round(1000 * usdRate).toLocaleString()} VNĐ` },
      { label: "100 EUR", val: `${Math.round(100 * eurRate).toLocaleString()} VNĐ` },
      { label: "10,000 JPY", val: `${Math.round(10000 * jpyRate).toLocaleString()} VNĐ` },
      { label: "100,000 VNĐ", val: `${(100000 / usdRate).toFixed(2)} USD` },
      { label: "1,000,000 VNĐ", val: `${(1000000 / usdRate).toFixed(2)} USD` },
      { label: "10,000,000 VNĐ", val: `${(10000000 / usdRate).toFixed(2)} USD` }
    ];

    container.innerHTML = rows.map(r => `
      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 12px; display: flex; justify-content: space-between; font-size: 13px;">
        <span style="font-weight: 600; color: #475569;">${r.label}</span>
        <strong style="color: #0369a1;">${r.val}</strong>
      </div>
    `).join("");
  }
});
