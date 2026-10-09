/**
 * IT Tool LTT 2026 - Hosts File Editor, IP Manager & IP Scanner Module
 */
Object.assign(AppController.prototype, {
  async loadHosts() {
    const txt = document.getElementById("hosts-textarea") || document.getElementById("hosts-textarea-page");
    const infoEl = document.getElementById("hosts-status-info");
    if (!txt) return;

    // Tự động đồng bộ các chỉnh sửa của người dùng vào file tạm
    if (!txt.dataset.tempSyncAttached) {
      txt.dataset.tempSyncAttached = "true";
      let syncTimer = null;
      txt.addEventListener("input", () => {
        clearTimeout(syncTimer);
        syncTimer = setTimeout(async () => {
          if (window.pywebview && window.pywebview.api && window.pywebview.api.update_hosts_temp) {
            try {
              await window.pywebview.api.update_hosts_temp(txt.value);
            } catch (e) {
              console.error("Lỗi đồng bộ file tạm:", e);
            }
          }
        }, 300);
      });
    }

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.get_hosts_file();
        if (res && res.success) {
          txt.value = res.content || "";
          const lines = (res.content || "").split('\n').length;
          if (infoEl) {
            infoEl.innerHTML = `
              <div style="display: flex; flex-direction: column; gap: 3px;">
                <div>📝 <span style="font-weight:600; color:#0284c7;">File tạm đang sửa:</span> <code style="color: #0284c7; background: #f0f9ff; padding: 2px 6px; border-radius: 4px; border: 1px solid #bae6fd;">${res.temp_path || 'Thư mục tạm'}</code> (${lines} dòng)</div>
                <div style="color: #64748b; font-size: 11px;">📍 Nguồn gốc hệ thống: <code>${res.path || 'C:\\Windows\\System32\\drivers\\etc\\hosts'}</code> <span style="color:#10b981; font-weight:600;">(Đã copy tự động ra file tạm)</span></div>
              </div>
            `;
          }
        } else {
          if (infoEl) infoEl.innerHTML = `<span style="color:#ef4444">❌ Lỗi đọc Hosts: ${res ? res.message : 'Unknown'}</span>`;
        }
      } catch (err) {
        console.error("Lỗi get_hosts_file:", err);
      }
    } else {
      txt.value = "# Copyright (c) 1993-2006 Microsoft Corp.\n127.0.0.1       localhost\n::1             localhost\n# Demo Mock Hosts File\n127.0.0.1       dev.local\n";
      if (infoEl) infoEl.innerHTML = `📍 File tạm: <code>%TEMP%\\IT_Tools_Hosts_Temp\\hosts</code> (MOCK mode)`;
    }
  },

  async saveHosts() {
    const txt = document.getElementById("hosts-textarea") || document.getElementById("hosts-textarea-page");
    if (!txt) return;
    const content = txt.value;
    this.addLog("info", "Đang lưu thay đổi vào File Hosts hệ thống & Flush DNS...");

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.save_hosts_file(content);
        if (res && res.success) {
          this.addLog("success", res.message);
          alert(res.message);
          this.loadHosts();
        } else {
          this.addLog("error", res ? res.message : "Lỗi lưu file Hosts");
          alert(res ? res.message : "Lỗi lưu file Hosts");
        }
      } catch (err) {
        alert(`Lỗi lưu Hosts file: ${err.message}`);
      }
    } else {
      alert("[MOCK] Đã lưu thay đổi vào File Hosts & Flush DNS!");
    }
  },

  async saveHostsAs() {
    const txt = document.getElementById("hosts-textarea") || document.getElementById("hosts-textarea-page");
    if (!txt) return;
    const content = txt.value;

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.save_hosts_as(content);
        if (res && res.success) {
          this.addLog("success", `Đã lưu file hosts ra: ${res.path}`);
          alert(res.message);
        } else if (res && !res.canceled) {
          alert(res.message || "Lỗi khi lưu file!");
        }
      } catch (err) {
        alert(`Lỗi khi lưu file: ${err.message}`);
      }
    } else {
      const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "hosts";
      a.click();
      alert("[MOCK] Đã kích hoạt tải file hosts về máy!");
    }
  },

  async loadHostsFromFile() {
    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.load_hosts_from_file();
        if (res && res.success) {
          const txt = document.getElementById("hosts-textarea") || document.getElementById("hosts-textarea-page");
          if (txt) {
            txt.value = res.content || "";
            // Đồng bộ ngay nội dung mới nạp vào file tạm
            if (window.pywebview.api.update_hosts_temp) {
              await window.pywebview.api.update_hosts_temp(txt.value);
            }
            const lines = (res.content || "").split('\n').length;
            const infoEl = document.getElementById("hosts-status-info");
            if (infoEl) infoEl.innerHTML = `📍 Đã nạp từ: <code style="color: #10b981;">${res.path}</code> (${lines} dòng) - Đã đồng bộ sang file tạm`;
            this.addLog("success", `Đã nạp file từ: ${res.path}`);
          }
        }
      } catch (err) {
        console.error("Lỗi nạp file:", err);
      }
    }
  },

  async restoreHosts() {
    if (confirm("Bạn có chắc chắn muốn khôi phục File Hosts về mặc định ban đầu của Windows?\nThao tác này sẽ ghi đè nội dung file hosts gốc bằng mẫu chuẩn của Windows.")) {
      this.addLog("info", "Đang khôi phục File Hosts mặc định...");
      if (window.pywebview && window.pywebview.api) {
        try {
          const res = await window.pywebview.api.restore_hosts_default();
          if (res && res.success) {
            this.addLog("success", res.message);
            alert(res.message);
            this.loadHosts();
          } else {
            this.addLog("error", res ? res.message : "Khôi phục thất bại");
            alert(res ? res.message : "Khôi phục thất bại");
          }
        } catch (err) {
          alert(`Lỗi: ${err.message}`);
        }
      } else {
        alert("[MOCK] Đã khôi phục File Hosts mặc định!");
        this.loadHosts();
      }
    }
  },

  async openHostsFolder() {
    if (window.pywebview && window.pywebview.api) {
      try {
        await window.pywebview.api.open_hosts_folder();
      } catch (err) {
        console.error("Lỗi mở thư mục Hosts gốc:", err);
      }
    }
  },

  async openHostsTempFolder() {
    if (window.pywebview && window.pywebview.api) {
      try {
        await window.pywebview.api.open_hosts_temp_folder();
      } catch (err) {
        console.error("Lỗi mở thư mục tạm Hosts:", err);
      }
    }
  },

  appendHostsPreset(preset) {
    const txt = document.getElementById("hosts-textarea") || document.getElementById("hosts-textarea-page");
    if (!txt) return;

    let textToAdd = "";
    if (preset === 'localhost') {
      textToAdd = "\n# Localhost Mappings\n127.0.0.1       dev.local\n127.0.0.1       test.local\n";
    } else if (preset === 'block_ads') {
      textToAdd = "\n# Block Tracking & Ad Servers\n0.0.0.0         telemetry.microsoft.com\n0.0.0.0         v10.events.data.microsoft.com\n";
    } else if (preset === 'custom') {
      textToAdd = "\n# Custom Domain Block / Mapping\n127.0.0.1       example.com\n127.0.0.1       www.example.com\n";
    }

    if (textToAdd) {
      txt.value = txt.value.trimEnd() + "\n" + textToAdd;
      txt.scrollTop = txt.scrollHeight;
    }
  },

  switchIpSubtab(subtabName, btnEl) {
    if (btnEl && btnEl.parentElement) {
      const btns = btnEl.parentElement.querySelectorAll("button");
      btns.forEach(b => b.className = "btn btn-slate-light btn-sm");
      btnEl.className = "btn btn-primary btn-sm";
    }

    const panes = ["adapters", "edit", "subnet", "ipv6"];
    panes.forEach(p => {
      const pane = document.getElementById(`ip-pane-${p}`);
      if (pane) {
        pane.style.display = (p === subtabName) ? "block" : "none";
      }
    });

    if (subtabName === "adapters" || subtabName === "edit") {
      this.loadNetworkAdapters();
    } else if (subtabName === "ipv6") {
      this.loadIpv6Status();
    }
  },

  generateRandomMac(separator = ":") {
    const hex = "0123456789ABCDEF";
    const bytes = [];
    for (let i = 0; i < 6; i++) {
      let b = "";
      if (i === 0) {
        const secondChar = ["2", "6", "A", "E"][Math.floor(Math.random() * 4)];
        b = hex[Math.floor(Math.random() * 16)] + secondChar;
      } else {
        b = hex[Math.floor(Math.random() * 16)] + hex[Math.floor(Math.random() * 16)];
      }
      bytes.push(b);
    }
    return bytes.join(separator);
  },

  async loadNetworkAdapters() {
    const tbody = document.getElementById("ip-adapters-body");
    const localBadge = document.getElementById("ip-local-badge");
    const extBadge = document.getElementById("ip-ext-badge");
    const selectEl = document.getElementById("ip-edit-adapter-select");

    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">🔄 Đang quét danh sách card mạng hệ thống...</td></tr>`;
    }

    this.addLog("info", "Đang quét danh sách card mạng (Network Adapters)...");

    let data = null;
    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.get_network_adapters();
        if (res && res.success) {
          data = res.data;
          this.networkAdaptersData = data;
        } else {
          this.addLog("error", "Không thể lấy danh sách card mạng.");
        }
      } catch (err) {
        console.error("Lỗi get_network_adapters:", err);
        this.addLog("error", `Lỗi quét card mạng: ${err.message}`);
      }
    } else {
      data = {
        local_ip: "192.168.1.100",
        external_ip: "203.0.113.1",
        adapters: [
          { name: "Ethernet", ip: "192.168.1.100", prefix: "24", mask: "255.255.255.0", gateway: "192.168.1.1", dns: "8.8.8.8, 8.8.4.4", dns1: "8.8.8.8", dns2: "8.8.4.4", mac: this.generateRandomMac("-"), status: "Up", dhcp: "Enabled" },
          { name: "Wi-Fi", ip: "-", prefix: "-", mask: "255.255.255.0", gateway: "-", dns: "-", dns1: "", dns2: "", mac: this.generateRandomMac("-"), status: "Disconnected", dhcp: "Enabled" }
        ]
      };
      this.networkAdaptersData = data;
    }

    if (!data) {
      if (tbody) tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger">❌ Không thể nạp thông tin card mạng. Vui lòng bấm nút 🔄 để thử lại.</td></tr>`;
      return;
    }

    if (localBadge) localBadge.innerText = data.local_ip || "N/A";
    if (extBadge) {
      extBadge.innerText = data.external_ip || "Đang lấy...";
      if (!data.external_ip || data.external_ip === "Đang lấy..." || data.external_ip === "N/A") {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.get_external_ip) {
          window.pywebview.api.get_external_ip().then(r => {
            const publicIp = (r && r.ip && typeof r.ip === 'object') ? r.ip.ip : (r ? r.ip : null);
            if (publicIp && publicIp !== "N/A" && publicIp !== "Đang lấy...") {
              extBadge.innerText = publicIp;
              if (this.networkAdaptersData) this.networkAdaptersData.external_ip = publicIp;
            }
          }).catch(e => console.log("Lỗi lấy Public IP:", e));
        }
      }
    }

    const adapters = data.adapters || [];

    if (selectEl) {
      const prevVal = selectEl.value;
      if (adapters.length > 0) {
        selectEl.innerHTML = adapters.map(a => `<option value="${this.escapeHtml(a.name)}">${this.escapeHtml(a.name)} (${this.escapeHtml(a.ip)})</option>`).join("");
        if (prevVal && adapters.some(a => a.name === prevVal)) {
          selectEl.value = prevVal;
        } else {
          // Ưu tiên chọn card mạng đang Active có IP
          const activeAdp = adapters.find(a => (a.status || '').toLowerCase() === 'up' && a.ip && a.ip !== '-');
          if (activeAdp) {
            selectEl.value = activeAdp.name;
          }
        }
      } else {
        selectEl.innerHTML = `<option value="">-- Không tìm thấy card mạng --</option>`;
      }
    }

    this.onAdapterSelectChange();

    if (!tbody) return;

    if (adapters.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">Không tìm thấy card mạng nào trong hệ thống.</td></tr>`;
      return;
    }

    tbody.innerHTML = adapters.map(a => {
      const isUp = (a.status || "").toLowerCase() === "up";
      const isDhcp = (a.dhcp || "").toLowerCase() === "enabled";
      const statusBadge = isUp 
        ? `<span class="badge badge-status-enable">🟢 Active ${isDhcp ? '(DHCP)' : '(Static)'}</span>`
        : `<span class="badge badge-status-disabled">⚪ ${this.escapeHtml(a.status)}</span>`;

      return `
        <tr>
          <td style="padding: 10px;">
            <strong style="color: var(--text-main); font-size: 13px;">${this.escapeHtml(a.name)}</strong>
          </td>
          <td style="padding: 10px; font-family: monospace; color: #0284c7; font-weight: 600;">${this.escapeHtml(a.ip)}</td>
          <td style="padding: 10px; text-align: center; color: var(--text-muted);">${this.escapeHtml(a.mask || a.prefix)}</td>
          <td style="padding: 10px; font-family: monospace; color: var(--text-main);">${this.escapeHtml(a.gateway)}</td>
          <td style="padding: 10px; font-family: monospace; color: var(--text-muted); font-size: 12px;">${this.escapeHtml(a.mac)}</td>
          <td style="padding: 10px; text-align: center;">${statusBadge}</td>
          <td style="padding: 10px; text-align: right; white-space: nowrap;">
            <button class="btn btn-slate-light btn-sm" onclick="app.copyToClipboard('${this.escapeHtml(a.ip)}', 'IP')" title="Copy IP" style="padding: 2px 6px; font-size: 11px;">📋 IP</button>
            <button class="btn btn-slate-light btn-sm ml-1" onclick="app.copyToClipboard('${this.escapeHtml(a.mac)}', 'MAC')" title="Copy MAC" style="padding: 2px 6px; font-size: 11px;">📋 MAC</button>
            <button class="btn btn-slate-light btn-sm ml-1" onclick="app.copyToClipboard('${this.escapeHtml(a.name)}', 'Tên Card')" title="Copy Name" style="padding: 2px 6px; font-size: 11px;">📋 Tên</button>
          </td>
        </tr>
      `;
    }).join("");

    this.addLog("success", `Đã hiển thị ${adapters.length} card mạng.`);
  },

  onAdapterSelectChange() {
    const selectEl = document.getElementById("ip-edit-adapter-select");
    if (!selectEl) return;
    const adapterName = selectEl.value;
    if (!adapterName || !this.networkAdaptersData || !this.networkAdaptersData.adapters) return;

    const adapter = this.networkAdaptersData.adapters.find(a => a.name === adapterName);
    if (!adapter) return;

    const isDhcp = (adapter.dhcp || "").toLowerCase() === "enabled";

    const radioDhcp = document.querySelector('input[name="ip-mode-radio"][value="dhcp"]');
    const radioStatic = document.querySelector('input[name="ip-mode-radio"][value="static"]');

    if (isDhcp && radioDhcp) {
      radioDhcp.checked = true;
    } else if (!isDhcp && radioStatic) {
      radioStatic.checked = true;
    }

    this.toggleIpModeForm(isDhcp ? "dhcp" : "static");

    const inputAddr = document.getElementById("ip-input-address");
    const inputMask = document.getElementById("ip-input-mask");
    const inputGw = document.getElementById("ip-input-gateway");
    const inputDns1 = document.getElementById("ip-input-dns1");
    const inputDns2 = document.getElementById("ip-input-dns2");

    if (inputAddr) inputAddr.value = (adapter.ip && adapter.ip !== "-") ? adapter.ip : "";
    if (inputMask) inputMask.value = adapter.mask || (adapter.prefix && adapter.prefix !== "-" ? this.prefixToMask(adapter.prefix) : "255.255.255.0");
    if (inputGw) inputGw.value = (adapter.gateway && adapter.gateway !== "-") ? adapter.gateway : "";

    let d1 = adapter.dns1 || "";
    let d2 = adapter.dns2 || "";
    if (!d1 && adapter.dns && adapter.dns !== "-") {
      const parts = adapter.dns.split(',').map(s => s.trim()).filter(Boolean);
      d1 = parts[0] || "";
      d2 = parts[1] || "";
    }
    if (inputDns1) inputDns1.value = d1;
    if (inputDns2) inputDns2.value = d2;
  },

  prefixToMask(prefix) {
    const p = parseInt(prefix, 10);
    if (isNaN(p) || p < 0 || p > 32) return "255.255.255.0";
    let mask = [];
    for (let i = 0; i < 4; i++) {
      const n = Math.min(Math.max(p - i * 8, 0), 8);
      mask.push(256 - Math.pow(2, 8 - n));
    }
    return mask.join(".");
  },

  copyToClipboard(text, label = "") {
    if (!text || text === "-") return;
    const msg = `Đã sao chép ${label ? label + ': ' : ''}${text}`;
    const copyFallback = () => {
      try {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
        this.addLog("info", msg);
        if (typeof this.showToast === "function") this.showToast("info", msg);
      } catch (e) {
        if (typeof this.showToast === "function") this.showToast("error", `Lỗi sao chép: ${e.message}`);
      }
    };

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        this.addLog("info", msg);
        if (typeof this.showToast === "function") this.showToast("info", msg);
      }).catch(() => copyFallback());
    } else {
      copyFallback();
    }
  },

  toggleIpModeForm(mode) {
    const fieldsGroup = document.getElementById("ip-static-fields-group");
    if (fieldsGroup) {
      fieldsGroup.style.opacity = (mode === "dhcp") ? "0.4" : "1.0";
      fieldsGroup.style.pointerEvents = (mode === "dhcp") ? "none" : "auto";
    }
  },

  applyIpPreset(type) {
    const radioStatic = document.querySelector('input[name="ip-mode-radio"][value="static"]');
    if (radioStatic) { radioStatic.checked = true; this.toggleIpModeForm('static'); }

    const inputAddr = document.getElementById("ip-input-address");
    const inputMask = document.getElementById("ip-input-mask");
    const inputGw = document.getElementById("ip-input-gateway");
    const inputDns1 = document.getElementById("ip-input-dns1");
    const inputDns2 = document.getElementById("ip-input-dns2");

    if (type === "home") {
      if (inputAddr && !inputAddr.value) inputAddr.value = "192.168.1.100";
      if (inputMask) inputMask.value = "255.255.255.0";
      if (inputGw) inputGw.value = "192.168.1.1";
      if (inputDns1) inputDns1.value = "8.8.8.8";
      if (inputDns2) inputDns2.value = "8.8.4.4";
    } else if (type === "office") {
      if (inputAddr && !inputAddr.value) inputAddr.value = "192.168.0.100";
      if (inputMask) inputMask.value = "255.255.255.0";
      if (inputGw) inputGw.value = "192.168.0.1";
      if (inputDns1) inputDns1.value = "8.8.8.8";
      if (inputDns2) inputDns2.value = "8.8.4.4";
    } else if (type === "google") {
      if (inputDns1) inputDns1.value = "8.8.8.8";
      if (inputDns2) inputDns2.value = "8.8.4.4";
    } else if (type === "cloudflare") {
      if (inputDns1) inputDns1.value = "1.1.1.1";
      if (inputDns2) inputDns2.value = "1.0.0.1";
    }
  },

  async applyIpSettingsFromForm() {
    const adapterSelect = document.getElementById("ip-edit-adapter-select");
    const adapter = adapterSelect ? adapterSelect.value : "";
    if (!adapter) {
      if (typeof this.showToast === 'function') this.showToast("warning", "Vui lòng chọn Card Mạng (Adapter)!");
      else alert("Vui lòng chọn Card Mạng (Adapter)!");
      return;
    }

    const modeRadio = document.querySelector('input[name="ip-mode-radio"]:checked');
    const mode = modeRadio ? modeRadio.value : "static";

    const ip = document.getElementById("ip-input-address")?.value.trim() || "";
    const mask = document.getElementById("ip-input-mask")?.value.trim() || "255.255.255.0";
    const gw = document.getElementById("ip-input-gateway")?.value.trim() || "";
    const dns1 = document.getElementById("ip-input-dns1")?.value.trim() || "";
    const dns2 = document.getElementById("ip-input-dns2")?.value.trim() || "";

    if (mode === "static" && (!ip || !mask)) {
      if (typeof this.showToast === 'function') this.showToast("warning", "Vui lòng nhập Địa Chỉ IP và Subnet Mask!");
      else alert("Vui lòng nhập Địa Chỉ IP và Subnet Mask!");
      return;
    }

    this.addLog("info", `Đang cài đặt IP cho card mạng '${adapter}'...`);
    if (typeof this.showToast === 'function') this.showToast("info", `Đang áp dụng cấu hình cho '${adapter}'...`);

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.apply_ip_settings(adapter, mode, ip, mask, gw, dns1, dns2);
        this.addLog(res.success ? "success" : "error", res.message);
        if (typeof this.showToast === 'function') this.showToast(res.success ? "success" : "error", res.message);
        else alert(res.message);
        this.loadNetworkAdapters();
      } catch (err) {
        console.error("Lỗi apply_ip_settings:", err);
        if (typeof this.showToast === 'function') this.showToast("error", `Lỗi: ${err.message}`);
        else alert(`Lỗi: ${err.message}`);
      }
    } else {
      if (typeof this.showToast === 'function') this.showToast("info", `[MOCK] Đã áp dụng IP ${ip} cho ${adapter}!`);
      else alert(`[MOCK] Đã áp dụng IP ${ip} cho ${adapter}!`);
    }
  },

  async setDhcpFromForm() {
    const adapterSelect = document.getElementById("ip-edit-adapter-select");
    const adapter = adapterSelect ? adapterSelect.value : "";
    if (!adapter) {
      if (typeof this.showToast === 'function') this.showToast("warning", "Vui lòng chọn Card Mạng (Adapter)!");
      else alert("Vui lòng chọn Card Mạng (Adapter)!");
      return;
    }

    this.addLog("info", `Đang chuyển '${adapter}' sang chế độ DHCP...`);
    if (typeof this.showToast === 'function') this.showToast("info", `Đang cấu hình DHCP cho '${adapter}'...`);

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.apply_ip_settings(adapter, "dhcp");
        this.addLog(res.success ? "success" : "error", res.message);
        if (typeof this.showToast === 'function') this.showToast(res.success ? "success" : "error", res.message);
        else alert(res.message);
        this.loadNetworkAdapters();
      } catch (err) {
        if (typeof this.showToast === 'function') this.showToast("error", `Lỗi: ${err.message}`);
        else alert(`Lỗi: ${err.message}`);
      }
    } else {
      if (typeof this.showToast === 'function') this.showToast("info", `[MOCK] Đã cài DHCP cho ${adapter}!`);
      else alert(`[MOCK] Đã cài DHCP cho ${adapter}!`);
    }
  },

  async runSubnetCalculation() {
    const ipInput = document.getElementById("subnet-input-ip");
    const cidrSelect = document.getElementById("subnet-input-cidr");
    const outputEl = document.getElementById("subnet-result-output");

    const ip = ipInput ? ipInput.value.trim() : "";
    const cidr = cidrSelect ? cidrSelect.value : "24";

    if (!ip) {
      if (typeof this.showToast === 'function') this.showToast("warning", "Vui lòng nhập địa chỉ IP!");
      else alert("Vui lòng nhập địa chỉ IP!");
      return;
    }

    if (outputEl) outputEl.innerHTML = "🔄 Đang tính toán thông số subnet...";

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.calculate_subnet(ip, cidr);
        if (res && res.success && res.data) {
          const d = res.data;
          outputEl.innerHTML = `
            <div>• Network Address   : <strong style="color:#38bdf8">${d.network_address}</strong></div>
            <div>• Broadcast Address : <strong style="color:#f43f5e">${d.broadcast_address}</strong></div>
            <div>• Subnet Mask       : <strong style="color:#34d399">${d.subnet_mask}</strong></div>
            <div>• Wildcard Mask     : <strong style="color:#fbbf24">${d.wildcard_mask}</strong></div>
            <div>• CIDR Notation     : <strong>${d.cidr_notation}</strong></div>
            <div>• Host Đầu (First)  : <strong style="color:#a7f3d0">${d.first_host}</strong></div>
            <div>• Host Cuối (Last)  : <strong style="color:#a7f3d0">${d.last_host}</strong></div>
            <div>• Tổng Số Hosts     : <strong>${d.total_hosts}</strong></div>
            <div>• Usable Hosts      : <strong style="color:#38bdf8">${d.usable_hosts}</strong></div>
            <div>• Lớp IP (Class)    : <strong>${d.ip_class}</strong> (${d.type})</div>
          `;
        } else {
          outputEl.innerHTML = `<span style="color:#f87171">❌ ${res ? res.message : 'Lỗi tính toán'}</span>`;
        }
      } catch (err) {
        outputEl.innerHTML = `<span style="color:#f87171">❌ Lỗi: ${err.message}</span>`;
      }
    } else {
      outputEl.innerHTML = `[MOCK] Subnet result for ${ip}/${cidr}`;
    }
  },

  async loadIpv6Status() {
    const badge = document.getElementById("ipv6-status-badge");
    const btnToggle = document.getElementById("ipv6-btn-toggle");
    if (badge) badge.innerText = "Đang kiểm tra...";

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.get_ipv6_status();
        this.ipv6Enabled = !!(res && res.enabled);
        if (badge) {
          badge.innerText = res.text || (res.enabled ? "✅ IPv6 Đang Bật" : "🚫 IPv6 Đã Tắt");
          badge.style.color = res.enabled ? "#10b981" : "#ef4444";
        }
        if (btnToggle) {
          btnToggle.disabled = false;
          if (this.ipv6Enabled) {
            btnToggle.className = "btn btn-danger-solid px-4 py-2.5 font-semibold";
            btnToggle.innerHTML = "<span>🚫</span> Tắt IPv6 (Disable)";
            btnToggle.title = "IPv6 đang BẬT. Nhấp để Tắt trên tất cả card mạng";
          } else {
            btnToggle.className = "btn btn-success-solid px-4 py-2.5 font-semibold";
            btnToggle.innerHTML = "<span>✅</span> Bật IPv6 (Enable)";
            btnToggle.title = "IPv6 đang TẮT. Nhấp để Bật trên tất cả card mạng";
          }
        }
      } catch (err) {
        if (badge) badge.innerText = "Lỗi kiểm tra";
      }
    } else {
      this.ipv6Enabled = true;
      if (badge) badge.innerText = "✅ IPv6 Đang Bật (MOCK)";
      if (btnToggle) {
        btnToggle.className = "btn btn-danger-solid px-4 py-2.5 font-semibold";
        btnToggle.innerHTML = "<span>🚫</span> Tắt IPv6 (Disable)";
      }
    }
  },

  async toggleIpv6Status() {
    const isEnabled = (this.ipv6Enabled !== undefined) ? this.ipv6Enabled : true;
    await this.setIpv6Status(!isEnabled);
  },

  async setIpv6Status(enable) {
    const badge = document.getElementById("ipv6-status-badge");
    const btnToggle = document.getElementById("ipv6-btn-toggle");
    if (badge) badge.innerText = `Đang ${enable ? 'bật' : 'tắt'} IPv6...`;
    if (btnToggle) btnToggle.disabled = true;

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.set_ipv6_status(enable);
        this.addLog(res.success ? "success" : "error", res.message);
        if (typeof this.showToast === 'function') this.showToast(res.success ? "success" : "error", res.message);
        else alert(res.message);
        this.loadIpv6Status();
      } catch (err) {
        if (typeof this.showToast === 'function') this.showToast("error", `Lỗi: ${err.message}`);
        else alert(`Lỗi: ${err.message}`);
        if (btnToggle) btnToggle.disabled = false;
      }
    } else {
      if (typeof this.showToast === 'function') this.showToast("info", `[MOCK] Đã ${enable ? 'bật' : 'tắt'} IPv6!`);
      else alert(`[MOCK] Đã ${enable ? 'bật' : 'tắt'} IPv6!`);
      this.ipv6Enabled = enable;
      this.loadIpv6Status();
    }
  },

  async loadIpScannerDefaults() {
    const subEl = document.getElementById("ipscan-input-subnet");
    const startEl = document.getElementById("ipscan-input-start");
    const endEl = document.getElementById("ipscan-input-end");

    if (window.pywebview && window.pywebview.api) {
      try {
        const d = await window.pywebview.api.get_ip_scanner_default_range();
        if (d) {
          if (subEl && !subEl.value) subEl.value = d.subnet || "";
          if (startEl && !startEl.value) startEl.value = d.start_ip || "";
          if (endEl && !endEl.value) endEl.value = d.end_ip || "";
        }
      } catch (err) {
        console.error("Lỗi lấy IP scan defaults:", err);
      }
    } else {
      if (subEl && !subEl.value) subEl.value = "192.168.1.0/24";
      if (startEl && !startEl.value) startEl.value = "192.168.1.1";
      if (endEl && !endEl.value) endEl.value = "192.168.1.254";
    }
  },

  applyIpScanPreset(preset) {
    const subEl = document.getElementById("ipscan-input-subnet");
    const startEl = document.getElementById("ipscan-input-start");
    const endEl = document.getElementById("ipscan-input-end");

    if (preset === 'local') {
      if (subEl) subEl.value = "";
      if (startEl) startEl.value = "";
      if (endEl) endEl.value = "";
      this.loadIpScannerDefaults();
    } else if (preset === '192.168.1') {
      if (subEl) subEl.value = "192.168.1.0/24";
      if (startEl) startEl.value = "192.168.1.1";
      if (endEl) endEl.value = "192.168.1.254";
    } else if (preset === '192.168.0') {
      if (subEl) subEl.value = "192.168.0.0/24";
      if (startEl) startEl.value = "192.168.0.1";
      if (endEl) endEl.value = "192.168.0.254";
    } else if (preset === '10.0.0') {
      if (subEl) subEl.value = "10.0.0.0/24";
      if (startEl) startEl.value = "10.0.0.1";
      if (endEl) endEl.value = "10.0.0.254";
    }
  },

  applyPortPreset(type) {
    const portDefs = [
      { id: 'ipscan-chk-port-80', port: 80 },
      { id: 'ipscan-chk-port-443', port: 443 },
      { id: 'ipscan-chk-port-3389', port: 3389 },
      { id: 'ipscan-chk-port-445', port: 445 },
      { id: 'ipscan-chk-port-135', port: 135 },
      { id: 'ipscan-chk-port-1433', port: 1433 },
      { id: 'ipscan-chk-port-389', port: 389 },
      { id: 'ipscan-chk-port-53', port: 53 },
      { id: 'ipscan-chk-port-5985', port: 5985 },
      { id: 'ipscan-chk-port-22', port: 22 },
      { id: 'ipscan-chk-port-88', port: 88 },
      { id: 'ipscan-chk-port-21', port: 21 },
    ];

    let targetPorts = [];
    if (type === 'web') {
      targetPorts = [80, 443];
    } else if (type === 'client') {
      targetPorts = [3389, 445, 135];
    } else if (type === 'server') {
      targetPorts = [445, 3389, 135, 53, 88, 389, 1433, 5985];
    } else if (type === 'db') {
      targetPorts = [1433, 22, 5985];
    } else if (type === 'all') {
      targetPorts = portDefs.map(p => p.port);
    } else if (type === 'none') {
      targetPorts = [];
    }

    portDefs.forEach(p => {
      const el = document.getElementById(p.id);
      if (el) el.checked = targetPorts.includes(p.port);
    });
  },

  async startIpScanner() {
    const subEl = document.getElementById("ipscan-input-subnet");
    const startEl = document.getElementById("ipscan-input-start");
    const endEl = document.getElementById("ipscan-input-end");
    const threadsEl = document.getElementById("ipscan-input-threads");

    const chkPing = document.getElementById("ipscan-chk-ping");
    const chkHost = document.getElementById("ipscan-chk-hostname");
    const chkMac = document.getElementById("ipscan-chk-mac");

    const btnStart = document.getElementById("ipscan-btn-start");
    const btnExport = document.getElementById("ipscan-btn-export");
    const spinner = document.getElementById("ipscan-spinner");
    const statusText = document.getElementById("ipscan-status-text");
    const badgeCount = document.getElementById("ipscan-count-badge");
    const bodyEl = document.getElementById("ipscan-results-body");

    const subnet_str = subEl ? subEl.value.trim() : "";
    const ip_start = startEl ? startEl.value.trim() : "";
    const ip_end = endEl ? endEl.value.trim() : "";
    const max_threads = threadsEl ? parseInt(threadsEl.value) || 50 : 50;

    const check_ping = chkPing ? chkPing.checked : true;
    const check_hostname = chkHost ? chkHost.checked : true;
    const check_mac = chkMac ? chkMac.checked : true;

    // Collect port list to scan
    const portDefs = [
      { id: 'ipscan-chk-port-80', port: 80 },
      { id: 'ipscan-chk-port-443', port: 443 },
      { id: 'ipscan-chk-port-3389', port: 3389 },
      { id: 'ipscan-chk-port-445', port: 445 },
      { id: 'ipscan-chk-port-135', port: 135 },
      { id: 'ipscan-chk-port-1433', port: 1433 },
      { id: 'ipscan-chk-port-389', port: 389 },
      { id: 'ipscan-chk-port-53', port: 53 },
      { id: 'ipscan-chk-port-5985', port: 5985 },
      { id: 'ipscan-chk-port-22', port: 22 },
      { id: 'ipscan-chk-port-88', port: 88 },
      { id: 'ipscan-chk-port-21', port: 21 },
    ];
    const ports_to_check = [];
    portDefs.forEach(p => {
      const el = document.getElementById(p.id);
      if (el && el.checked) ports_to_check.push(p.port);
    });

    const customPortsEl = document.getElementById('ipscan-input-custom-ports');
    if (customPortsEl && customPortsEl.value) {
      customPortsEl.value.replace(/,/g, ' ').split(/\s+/).forEach(val => {
        const num = parseInt(val.trim());
        if (num > 0 && num <= 65535 && !ports_to_check.includes(num)) {
          ports_to_check.push(num);
        }
      });
    }

    const check_http_port = ports_to_check.includes(80);
    const check_https_port = ports_to_check.includes(443);

    if (btnStart) btnStart.disabled = true;
    if (spinner) spinner.style.display = "inline-block";
    if (statusText) statusText.innerText = `Đang quét dải IP (${max_threads} luồng, ${ports_to_check.length} cổng dịch vụ)... Vui lòng chờ...`;
    if (bodyEl) {
      bodyEl.innerHTML = `
        <tr>
          <td colspan="8" class="text-center py-4 text-muted">
            <span class="spinner-border spinner-border-sm text-primary"></span>
            Đang tiến hành quét thiết bị và cổng dịch vụ trong mạng LAN...
          </td>
        </tr>
      `;
    }

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.scan_ip_range(
          subnet_str, ip_start, ip_end, check_ping, check_hostname, check_mac, check_http_port, check_https_port, max_threads, ports_to_check
        );

        if (res && res.success) {
          this.lastScanResults = res.results || [];
          if (badgeCount) badgeCount.innerText = `${res.total} Online`;
          if (statusText) statusText.innerText = `Hoàn tất quét LAN! Tìm thấy ${res.total} thiết bị online.`;
          if (btnExport) btnExport.disabled = (res.total === 0);
          this.renderIpScanResults(res.results || []);
        } else {
          if (statusText) statusText.innerText = `Lỗi quét IP: ${res ? res.message : 'Unknown'}`;
          if (bodyEl) {
            bodyEl.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-danger">Lỗi: ${res ? res.message : 'Không quét được'}</td></tr>`;
          }
        }
      } catch (err) {
        if (statusText) statusText.innerText = `Lỗi ngoại lệ: ${err.message}`;
        if (bodyEl) {
          bodyEl.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-danger">Lỗi kết nối API: ${err.message}</td></tr>`;
        }
      } finally {
        if (btnStart) btnStart.disabled = false;
        if (spinner) spinner.style.display = "none";
      }
    } else {
      setTimeout(() => {
        const mockData = [
          { ip: "192.168.1.1", hostname: "Router-Gateway.home", mac: this.generateRandomMac(":"), vendor: "TP-Link", device_type: "Router", latency_ms: "<1ms", open_ports: [80, 443, 53] },
          { ip: "192.168.1.100", hostname: "PC-DESKTOP-LTT", mac: this.generateRandomMac(":"), vendor: "Realtek", device_type: "PC", latency_ms: "<1ms", open_ports: [445, 135, 3389, 5985] },
          { ip: "192.168.1.200", hostname: "WIN-SERVER-2025", mac: this.generateRandomMac(":"), vendor: "Dell", device_type: "Server", latency_ms: "<1ms", open_ports: [53, 88, 135, 389, 445, 1433, 3389, 5985] },
          { ip: "192.168.1.105", hostname: "iPhone-Guest", mac: this.generateRandomMac(":"), vendor: "Apple", device_type: "iPhone", latency_ms: "12ms", open_ports: [] }
        ];
        this.lastScanResults = mockData;
        if (badgeCount) badgeCount.innerText = "4 Online";
        if (statusText) statusText.innerText = "Hoàn tất quét LAN (MOCK)! Tìm thấy 4 thiết bị online.";
        if (btnExport) btnExport.disabled = false;
        this.renderIpScanResults(mockData);
        if (btnStart) btnStart.disabled = false;
        if (spinner) spinner.style.display = "none";
      }, 800);
    }
  },

  renderIpScanResults(results) {
    const bodyEl = document.getElementById("ipscan-results-body");
    if (!bodyEl) return;

    if (!results || results.length === 0) {
      bodyEl.innerHTML = `
        <tr>
          <td colspan="8" class="text-center py-4 text-muted">
            Không tìm thấy thiết bị nào phản hồi trong dải IP đã quét.
          </td>
        </tr>
      `;
      return;
    }

    const deviceIcons = {
      'Router': '🌐', 'Switch': '🔀', 'AP': '📡', 'PC': '🖥️',
      'Laptop': '💻', 'Phone': '📱', 'iPhone': '📱', 'iPad': '📱',
      'Tablet': '📱', 'Printer': '🖨️', 'Camera': '📷', 'TV': '📺',
      'IoT': '🔌', 'NAS': '💾', 'VM': '☁️', 'Server': '🖧', 'Mac': '💻',
      'Unknown': '❓'
    };

    const portBadgesMap = {
      80: { label: '🌐 80', bg: '#dcfce7', color: '#166534', title: 'HTTP Web Server' },
      443: { label: '🔒 443', bg: '#e0e7ff', color: '#3730a3', title: 'HTTPS Web Server' },
      3389: { label: '🖥️ 3389', bg: '#dbeafe', color: '#1e40af', title: 'Remote Desktop (RDP)' },
      445: { label: '📁 445', bg: '#ffedd5', color: '#9a3412', title: 'SMB File & Printer Sharing' },
      139: { label: '📁 139', bg: '#fef3c7', color: '#854d0e', title: 'NetBIOS' },
      135: { label: '⚙️ 135', bg: '#f1f5f9', color: '#334155', title: 'RPC / WMI Hệ Thống' },
      1433: { label: '🗄️ 1433', bg: '#fae8ff', color: '#86198f', title: 'MSSQL Database' },
      389: { label: '🏢 389', bg: '#ccfbf1', color: '#115e59', title: 'Active Directory LDAP' },
      636: { label: '🏢 636', bg: '#ccfbf1', color: '#115e59', title: 'LDAPS Secure' },
      53: { label: '🔀 53', bg: '#cffafe', color: '#155e75', title: 'DNS Server' },
      88: { label: '🛡️ 88', bg: '#fef9c3', color: '#713f12', title: 'Kerberos AD' },
      5985: { label: '⚡ 5985', bg: '#ffe4e6', color: '#9f1239', title: 'WinRM HTTP (PowerShell)' },
      5986: { label: '⚡ 5986', bg: '#ffe4e6', color: '#9f1239', title: 'WinRM HTTPS' },
      22: { label: '🔑 22', bg: '#e2e8f0', color: '#1e293b', title: 'SSH Admin' },
      21: { label: '🗂️ 21', bg: '#f1f5f9', color: '#475569', title: 'FTP Server' }
    };

    const copyStyle = `cursor:pointer; user-select:none; transition: background 0.15s;`;
    const copyCellStyle = `padding: 8px; ${copyStyle}`;

    bodyEl.innerHTML = results.map((item, index) => {
      const latency = item.latency_ms || item.ping || '<1ms';
      const pingText = latency ? `(${latency})` : '';
      const vendor = item.vendor || item.brand || 'Unknown';
      const deviceType = item.device_type || 'Unknown';
      const deviceIcon = deviceIcons[deviceType] || '❓';
      const isRandomMac = vendor === 'Randomized MAC';

      // Vendor badge
      let vendorBadge;
      if (isRandomMac) {
        vendorBadge = `<span class="badge" style="background:#fef3c7; color:#92400e; font-size:11px; font-weight:600;" title="Thiết bị dùng MAC ngẫu nhiên để bảo vệ quyền riêng tư (Android/iOS)">🔀 MAC Ngẫu Nhiên</span><span class="badge" style="background:#fef9ee; color:#b45309; font-size:10px; margin-left:3px;">📱 Điện thoại/Laptop</span>`;
      } else if (vendor !== 'Unknown') {
        vendorBadge = `<span class="badge" style="background:#dbeafe; color:#1d4ed8; font-weight:600; font-size:11px; margin-right:4px;" title="Nhà sản xuất">${vendor}</span><span class="badge" style="background:#f0fdf4; color:#16a34a; font-size:11px;" title="Loại thiết bị">${deviceIcon} ${deviceType}</span>`;
      } else {
        const macPrefix = item.mac && item.mac.length >= 8 ? item.mac.substring(0, 8).toUpperCase() : '';
        vendorBadge = `<span class="badge" style="background:#f1f5f9; color:#64748b; font-size:11px;" title="Không tìm thấy nhà sản xuất trong cơ sở dữ liệu OUI${macPrefix ? ' — OUI: ' + macPrefix : ''}">❓ Chưa xác định${macPrefix ? `<span style='color:#94a3b8; font-size:10px; display:block;'>${macPrefix}</span>` : ''}</span>`;
      }

      // Open Ports Badges
      let openPortsList = item.open_ports || [];
      if (openPortsList.length === 0) {
        if (item.http) openPortsList.push(80);
        if (item.https) openPortsList.push(443);
      }

      let openPortsBadges = '';
      if (openPortsList.length > 0) {
        openPortsBadges = openPortsList.map(p => {
          const badgeDef = portBadgesMap[p] || { label: `Port ${p}`, bg: '#f1f5f9', color: '#475569', title: `Cổng ${p}` };
          return `<span class="badge" style="background:${badgeDef.bg}; color:${badgeDef.color}; margin-right:3px; margin-bottom:2px; font-size:10.5px; font-weight:600; display:inline-block;" title="${badgeDef.title}">${badgeDef.label}</span>`;
        }).join('');
      } else {
        openPortsBadges = `<span style="color:#cbd5e1; font-size:11px;">-</span>`;
      }

      const esc = (s) => String(s || '').replace(/'/g, "\\'");

      const hostnameDisplay = (item.hostname && item.hostname !== '' && item.hostname !== '-')
        ? `${item.hostname}<span style="font-size:10px; color:#94a3b8; display:block; margin-top:2px;">📋 Click để chép</span>`
        : `<span style="color:#94a3b8; font-weight:400; font-style:italic; font-size:11px;">Không tìm được tên</span>`;

      const macDisplay = (item.mac && item.mac !== '' && item.mac !== '-')
        ? `${item.mac}<span style="font-size:10px; color:#94a3b8; display:block; margin-top:2px;">📋 Click để chép</span>`
        : `<span style="color:#cbd5e1; font-size:11px;">Không có MAC</span>`;

      return `
        <tr style="transition:background 0.15s;" onmouseover="this.style.background='var(--bg-hover,rgba(99,102,241,0.06))'" onmouseout="this.style.background=''">
          <td style="text-align:center; font-weight:600; color:var(--text-muted); padding:8px;">${index + 1}</td>
          <td style="text-align:center; padding:8px;">
            <span class="badge badge-status-enable">🟢 Online ${pingText}</span>
          </td>
          <td style="${copyCellStyle}" onclick="app.copyToClipboard('${esc(item.ip)}','IP')" title="Click để chép IP: ${esc(item.ip)}">
            <strong style="font-family:monospace; color:var(--text-main); font-size:13px;">${item.ip}</strong>
            <span style="font-size:10px; color:#94a3b8; display:block; margin-top:2px;">📋 Click để chép</span>
          </td>
          <td style="${copyCellStyle} color:#0284c7; font-weight:600;" onclick="app.copyToClipboard('${esc(item.hostname || '')}','Hostname')" title="Click để chép hostname">
            ${hostnameDisplay}
          </td>
          <td style="${copyCellStyle} font-family:monospace; color:var(--text-muted); font-size:12px;" onclick="app.copyToClipboard('${esc(item.mac || '')}','MAC')" title="Click để chép MAC: ${esc(item.mac)}">
            ${macDisplay}
          </td>
          <td style="${copyCellStyle}" onclick="app.copyToClipboard('${esc(vendor)} ${esc(deviceType)}','Vendor')" title="Click để chép thông tin nhà sản xuất">
            ${vendorBadge}
          </td>
          <td style="padding:8px; text-align:left;">
            <div style="display:flex; flex-wrap:wrap; align-items:center; gap:2px;">
              ${openPortsBadges}
            </div>
          </td>
          <td style="padding:8px; text-align:right; white-space:nowrap;">
            <div style="display:flex; flex-direction:column; align-items:flex-end; gap:3px;">
              <div style="display:flex; gap:4px;">
                <button class="btn btn-primary-gradient btn-sm" onclick="app.openHostPortScanModal('${esc(item.ip)}')" title="Quét chi tiết tất cả các cổng của máy ${esc(item.ip)}" style="padding:2px 7px; font-size:11px; font-weight:700;">⚡ Quét Port</button>
                <button class="btn btn-slate-light btn-sm" onclick="app.copyToClipboard('${esc(item.ip)}','IP')" title="Copy IP" style="padding:2px 6px; font-size:11px;">📋 IP</button>
              </div>
              <div style="display:flex; gap:3px; flex-wrap:wrap; justify-content:flex-end;">
                ${openPortsList.includes(3389) ? `<button class="btn btn-sm" style="background:#dbeafe; color:#1e40af; border:1px solid #bfdbfe; padding:2px 6px; font-size:10.5px; font-weight:600;" onclick="app.connectRdp('${esc(item.ip)}')" title="Kết nối Remote Desktop (mstsc /v:${esc(item.ip)})">🖥️ RDP</button>` : ''}
                ${openPortsList.includes(445) ? `<button class="btn btn-sm" style="background:#ffedd5; color:#9a3412; border:1px solid #fed7aa; padding:2px 6px; font-size:10.5px; font-weight:600;" onclick="app.openSmbShare('${esc(item.ip)}')" title="Mở chia sẻ mạng (\\\\${esc(item.ip)})">📁 Share</button>` : ''}
                ${openPortsList.includes(80) || openPortsList.includes(443) ? `<button class="btn btn-sm" style="background:#dcfce7; color:#166534; border:1px solid #bbf7d0; padding:2px 6px; font-size:10.5px; font-weight:600;" onclick="app.openWebBrowser('${openPortsList.includes(443) ? 'https' : 'http'}://${esc(item.ip)}')" title="Mở trình duyệt Web">🌐 Web</button>` : ''}
                ${openPortsList.includes(5985) ? `<button class="btn btn-sm" style="background:#ffe4e6; color:#9f1239; border:1px solid #fecdd3; padding:2px 6px; font-size:10.5px; font-weight:600;" onclick="app.openWinRmSession('${esc(item.ip)}')" title="Mở PowerShell Remoting">⚡ WinRM</button>` : ''}
              </div>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  },

  exportIpScanCsv() {
    if (!this.lastScanResults || this.lastScanResults.length === 0) {
      if (typeof this.showToast === 'function') this.showToast("warning", "Không có kết quả quét để xuất CSV!");
      else alert("Không có kết quả quét để xuất CSV!");
      return;
    }

    let csvContent = "data:text/csv;charset=utf-8,Index,IP Address,Hostname,MAC Address,Vendor,Device Type,Latency,Open Ports,HTTP (80),HTTPS (443),RDP (3389),SMB (445)\n";
    this.lastScanResults.forEach((row, i) => {
      const vendor = row.vendor || row.brand || '';
      const deviceType = row.device_type || '';
      const latency = row.latency_ms || row.ping || '';
      const openPorts = (row.open_ports || []).join('; ');
      csvContent += `"${i + 1}","${row.ip || ''}","${row.hostname || ''}","${row.mac || ''}","${vendor}","${deviceType}","${latency}","${openPorts}","${row.http ? 'YES' : 'NO'}","${row.https ? 'YES' : 'NO'}","${row.rdp ? 'YES' : 'NO'}","${row.smb ? 'YES' : 'NO'}"\n`;
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `lan_ip_scan_results_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },

  exportIpScanResultsCsv() {
    return this.exportIpScanCsv();
  },

  // ── HOST PORT SCANNER MODAL CONTROLLERS ─────────────────────────────────
  openHostPortScanModal(ip = '') {
    const modal = document.getElementById('host-port-scan-modal');
    if (!modal) return;
    modal.style.display = 'flex';
    const ipInput = document.getElementById('hostport-input-ip');
    if (ipInput) {
      if (ip) ipInput.value = ip;
      else if (!ipInput.value) ipInput.value = '127.0.0.1';
    }
    if (ip) {
      this.runHostPortScan();
    }
  },

  closeHostPortScanModal() {
    const modal = document.getElementById('host-port-scan-modal');
    if (modal) modal.style.display = 'none';
  },

  onHostPortProfileChange() {
    const select = document.getElementById('hostport-select-profile');
    const customRow = document.getElementById('hostport-custom-row');
    if (select && customRow) {
      customRow.style.display = (select.value === 'custom') ? 'block' : 'none';
    }
  },

  async runHostPortScan() {
    const ipInput = document.getElementById('hostport-input-ip');
    const target = ipInput ? ipInput.value.trim() : '127.0.0.1';
    if (!target) {
      alert("Vui lòng nhập IP hoặc Hostname mục tiêu cần quét!");
      return;
    }

    const select = document.getElementById('hostport-select-profile');
    const profile = select ? select.value : 'all_windows';

    let ports = null;
    if (profile === 'win_client') {
      ports = [135, 139, 445, 3389, 80, 443];
    } else if (profile === 'win_server') {
      ports = [53, 88, 135, 139, 389, 445, 636, 1433, 3268, 3389, 5985, 5986];
    } else if (profile === 'db_web') {
      ports = [80, 443, 8080, 8443, 1433, 3306, 5432, 22, 21];
    } else if (profile === 'custom') {
      const customInput = document.getElementById('hostport-input-custom-ports');
      if (customInput && customInput.value) {
        ports = customInput.value.replace(/,/g, ' ').split(/\s+/).map(p => parseInt(p)).filter(p => !isNaN(p) && p > 0);
      }
    }

    const btnScan = document.getElementById('hostport-btn-scan');
    const statusText = document.getElementById('hostport-status-text');
    const badgeOpen = document.getElementById('hostport-badge-open');
    const badgeTotal = document.getElementById('hostport-badge-total');
    const btnExport = document.getElementById('hostport-btn-export');
    const bodyEl = document.getElementById('hostport-results-body');

    if (btnScan) btnScan.disabled = true;
    if (statusText) statusText.innerText = `Đang quét cổng dịch vụ trên ${target}... Vui lòng chờ...`;
    if (bodyEl) {
      bodyEl.innerHTML = `
        <tr>
          <td colspan="6" class="text-center py-4 text-muted">
            <span class="spinner-border spinner-border-sm text-primary"></span>
            Đang quét các cổng dịch vụ trên máy đích (${target})...
          </td>
        </tr>
      `;
    }

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.scan_single_host_ports(target, ports);
        if (res && res.success) {
          this.lastHostPortResults = res.results || [];
          this.lastHostPortTarget = target;
          if (badgeOpen) badgeOpen.innerText = `${res.open_count} Cổng Mở`;
          if (badgeTotal) badgeTotal.innerText = `${res.total} Tổng Quét`;
          if (statusText) statusText.innerText = `Hoàn tất! Tìm thấy ${res.open_count} cổng MỞ trên ${target}.`;
          if (btnExport) btnExport.disabled = (res.results.length === 0);
          this.renderHostPortScanResults(res.results || [], target);
        } else {
          if (statusText) statusText.innerText = `Lỗi: ${res ? res.message : 'Không quét được'}`;
          if (bodyEl) bodyEl.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-danger">Lỗi: ${res ? res.message : 'Thất bại'}</td></tr>`;
        }
      } catch (e) {
        if (statusText) statusText.innerText = `Lỗi kết nối: ${e.message}`;
        if (bodyEl) bodyEl.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-danger">Lỗi: ${e.message}</td></tr>`;
      } finally {
        if (btnScan) btnScan.disabled = false;
      }
    } else {
      setTimeout(() => {
        const mockPorts = [
          { port: 80, name: "HTTP", desc: "Web Server / Router Web Admin", category: "Web", status: "OPEN", is_open: true, latency_ms: "2ms" },
          { port: 443, name: "HTTPS", desc: "Secure Web / SSL Server", category: "Web", status: "OPEN", is_open: true, latency_ms: "2ms" },
          { port: 3389, name: "RDP", desc: "Remote Desktop Protocol (Điều khiển từ xa)", category: "Windows Client/Server", status: "OPEN", is_open: true, latency_ms: "3ms" },
          { port: 445, name: "SMB", desc: "Server Message Block (Chia sẻ File & Máy in)", category: "Windows File Sharing", status: "OPEN", is_open: true, latency_ms: "1ms" },
          { port: 135, name: "RPC", desc: "RPC Endpoint Mapper & WMI (Quản trị hệ thống)", category: "Windows System", status: "OPEN", is_open: true, latency_ms: "1ms" },
          { port: 1433, name: "MSSQL", desc: "Microsoft SQL Server Database Engine", category: "Database", status: "CLOSED", is_open: false, latency_ms: "4ms" },
          { port: 5985, name: "WinRM HTTP", desc: "Windows Remote Management (PowerShell Remoting)", category: "Remote Admin", status: "OPEN", is_open: true, latency_ms: "2ms" }
        ];
        this.lastHostPortResults = mockPorts;
        this.lastHostPortTarget = target;
        if (badgeOpen) badgeOpen.innerText = "6 Cổng Mở";
        if (badgeTotal) badgeTotal.innerText = "7 Tổng Quét";
        if (statusText) statusText.innerText = `Hoàn tất (MOCK)! Tìm thấy 6 cổng MỞ trên ${target}.`;
        if (btnExport) btnExport.disabled = false;
        this.renderHostPortScanResults(mockPorts, target);
        if (btnScan) btnScan.disabled = false;
      }, 500);
    }
  },

  renderHostPortScanResults(results, target) {
    const bodyEl = document.getElementById('hostport-results-body');
    if (!bodyEl) return;
    if (!results || results.length === 0) {
      bodyEl.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">Không có dữ liệu cổng nào.</td></tr>`;
      return;
    }

    const esc = (s) => String(s || '').replace(/'/g, "\\'");
    bodyEl.innerHTML = results.map(row => {
      const isOpen = row.is_open;
      const statusBadge = isOpen
        ? `<span class="badge" style="background:#dcfce7; color:#166534; font-weight:700; font-size:11px; padding:3px 8px;">🟢 MỞ (OPEN)</span>`
        : `<span class="badge" style="background:#f1f5f9; color:#94a3b8; font-size:11px; padding:3px 8px;">🔴 ĐÓNG</span>`;

      let actionBtn = '-';
      if (isOpen) {
        if (row.port === 3389) {
          actionBtn = `<button class="btn btn-sm" style="background:#dbeafe; color:#1e40af; border:1px solid #bfdbfe; padding:2px 8px; font-size:11px; font-weight:600;" onclick="app.connectRdp('${esc(target)}')">🖥️ Kết Nối RDP</button>`;
        } else if (row.port === 445 || row.port === 139) {
          actionBtn = `<button class="btn btn-sm" style="background:#ffedd5; color:#9a3412; border:1px solid #fed7aa; padding:2px 8px; font-size:11px; font-weight:600;" onclick="app.openSmbShare('${esc(target)}')">📁 Mở Share \\\\</button>`;
        } else if (row.port === 80 || row.port === 8080) {
          actionBtn = `<button class="btn btn-sm" style="background:#dcfce7; color:#166534; border:1px solid #bbf7d0; padding:2px 8px; font-size:11px; font-weight:600;" onclick="app.openWebBrowser('http://${esc(target)}:${row.port}')">🌐 Mở Web</button>`;
        } else if (row.port === 443 || row.port === 8443) {
          actionBtn = `<button class="btn btn-sm" style="background:#e0e7ff; color:#3730a3; border:1px solid #c7d2fe; padding:2px 8px; font-size:11px; font-weight:600;" onclick="app.openWebBrowser('https://${esc(target)}:${row.port}')">🔒 Mở HTTPS</button>`;
        } else if (row.port === 5985 || row.port === 5986) {
          actionBtn = `<button class="btn btn-sm" style="background:#ffe4e6; color:#9f1239; border:1px solid #fecdd3; padding:2px 8px; font-size:11px; font-weight:600;" onclick="app.openWinRmSession('${esc(target)}')">⚡ WinRM PS</button>`;
        } else {
          actionBtn = `<button class="btn btn-slate-light btn-sm" style="padding:2px 8px; font-size:11px;" onclick="app.copyToClipboard('${esc(target)}:${row.port}','Port')">📋 Chép</button>`;
        }
      }

      return `
        <tr style="background:${isOpen ? 'rgba(34, 197, 94, 0.04)' : ''}; transition:background 0.15s;">
          <td style="text-align:center; font-family:monospace; font-weight:700; color:${isOpen ? '#166534' : '#64748b'}; padding:8px;">${row.port}</td>
          <td style="font-weight:600; color:#1e293b; padding:8px;">${row.name || ''}</td>
          <td style="color:#475569; font-size:12px; padding:8px;">${row.desc || ''}</td>
          <td style="padding:8px;"><span class="badge" style="background:#f1f5f9; color:#475569; font-size:10.5px;">${row.category || ''}</span></td>
          <td style="text-align:center; padding:8px;">${statusBadge}</td>
          <td style="text-align:right; padding:8px;">${actionBtn}</td>
        </tr>
      `;
    }).join('');
  },

  exportHostPortScanCsv() {
    if (!this.lastHostPortResults || this.lastHostPortResults.length === 0) {
      alert("Không có kết quả quét cổng để xuất CSV!");
      return;
    }
    const target = this.lastHostPortTarget || 'host';
    let csvContent = "data:text/csv;charset=utf-8,Port,Service Name,Description,Category,Status,Latency\n";
    this.lastHostPortResults.forEach(r => {
      csvContent += `"${r.port}","${r.name || ''}","${r.desc || ''}","${r.category || ''}","${r.status || ''}","${r.latency_ms || ''}"\n`;
    });
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `port_scan_${target.replace(/[^a-zA-Z0-9_.-]/g, '_')}_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },

  async connectRdp(ip) {
    if (!ip) return;
    this.addLog("info", `Đang mở kết nối Remote Desktop đến ${ip}...`);
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.open_rdp_connection === 'function') {
      const res = await window.pywebview.api.open_rdp_connection(ip);
      this.addLog(res.success ? "success" : "error", res.message);
    } else {
      alert(`[MOCK] Mở mstsc.exe /v:${ip}`);
    }
  },

  async openSmbShare(ip) {
    if (!ip) return;
    this.addLog("info", `Đang mở chia sẻ mạng (SMB) \\\\${ip}...`);
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.open_smb_share === 'function') {
      const res = await window.pywebview.api.open_smb_share(ip);
      this.addLog(res.success ? "success" : "error", res.message);
    } else {
      alert(`[MOCK] Mở explorer.exe \\\\${ip}`);
    }
  },

  async openWinRmSession(ip) {
    if (!ip) return;
    this.addLog("info", `Đang mở phiên PowerShell Remoting (WinRM) đến ${ip}...`);
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.open_winrm_session === 'function') {
      const res = await window.pywebview.api.open_winrm_session(ip);
      this.addLog(res.success ? "success" : "error", res.message);
    } else {
      alert(`[MOCK] Enter-PSSession -ComputerName ${ip}`);
    }
  },

  openWebBrowser(url) {
    if (!url) return;
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.open_external_url === 'function') {
      window.pywebview.api.open_external_url(url);
    } else {
      window.open(url, '_blank');
    }
  }
});

