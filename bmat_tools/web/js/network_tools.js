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
        external_ip: "14.234.136.174",
        adapters: [
          { name: "Ethernet", ip: "192.168.1.100", prefix: "24", mask: "255.255.255.0", gateway: "192.168.1.1", dns: "8.8.8.8, 8.8.4.4", dns1: "8.8.8.8", dns2: "8.8.4.4", mac: "1C-1B-0D-59-2E-7D", status: "Up", dhcp: "Enabled" },
          { name: "Wi-Fi", ip: "-", prefix: "-", mask: "255.255.255.0", gateway: "-", dns: "-", dns1: "", dns2: "", mac: "A4-C3-F0-12-34-56", status: "Disconnected", dhcp: "Enabled" }
        ]
      };
      this.networkAdaptersData = data;
    }

    if (!data) return;

    if (localBadge) localBadge.innerText = data.local_ip || "N/A";
    if (extBadge) extBadge.innerText = data.external_ip || "N/A";

    const adapters = data.adapters || [];

    if (selectEl) {
      const prevVal = selectEl.value;
      selectEl.innerHTML = adapters.map(a => `<option value="${this.escapeHtml(a.name)}">${this.escapeHtml(a.name)} (${this.escapeHtml(a.ip)})</option>`).join("");
      if (prevVal && adapters.some(a => a.name === prevVal)) {
        selectEl.value = prevVal;
      }
    }

    this.onAdapterSelectChange();

    if (!tbody) return;

    if (adapters.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">Không tìm thấy card mạng nào.</td></tr>`;
      return;
    }

    tbody.innerHTML = adapters.map(a => {
      const isUp = (a.status || "").toLowerCase() === "up";
      const isDhcp = (a.dhcp || "").toLowerCase() === "enabled";
      const statusBadge = isUp 
        ? `<span style="background: #dcfce7; color: #15803d; font-weight: 700; padding: 2px 8px; border-radius: 10px; font-size: 11px;">🟢 Active ${isDhcp ? '(DHCP)' : '(Static)'}</span>`
        : `<span style="background: #f1f5f9; color: #64748b; font-weight: 600; padding: 2px 8px; border-radius: 10px; font-size: 11px;">⚪ ${this.escapeHtml(a.status)}</span>`;

      return `
        <tr style="border-bottom: 1px solid #f1f5f9;">
          <td style="padding: 10px;">
            <strong style="color: #1e293b; font-size: 13px;">${this.escapeHtml(a.name)}</strong>
          </td>
          <td style="padding: 10px; font-family: monospace; color: #0284c7; font-weight: 600;">${this.escapeHtml(a.ip)}</td>
          <td style="padding: 10px; text-align: center; color: #64748b;">${this.escapeHtml(a.mask || a.prefix)}</td>
          <td style="padding: 10px; font-family: monospace; color: #475569;">${this.escapeHtml(a.gateway)}</td>
          <td style="padding: 10px; font-family: monospace; color: #64748b; font-size: 12px;">${this.escapeHtml(a.mac)}</td>
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
    navigator.clipboard.writeText(text).then(() => {
      this.addLog("info", `Đã sao chép ${label ? label + ': ' : ''}${text}`);
      alert(`Đã sao chép ${label ? label + ': ' : ''}${text}`);
    }).catch(err => {
      alert(`Lỗi sao chép: ${err}`);
    });
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
      alert("Vui lòng chọn Card Mạng (Adapter)!");
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
      alert("Vui lòng nhập Địa Chỉ IP và Subnet Mask!");
      return;
    }

    this.addLog("info", `Đang cài đặt IP cho card mạng '${adapter}'...`);

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.apply_ip_settings(adapter, mode, ip, mask, gw, dns1, dns2);
        this.addLog(res.success ? "success" : "error", res.message);
        alert(res.message);
        this.loadNetworkAdapters();
      } catch (err) {
        console.error("Lỗi apply_ip_settings:", err);
        alert(`Lỗi: ${err.message}`);
      }
    } else {
      alert(`[MOCK] Đã áp dụng IP ${ip} cho ${adapter}!`);
    }
  },

  async setDhcpFromForm() {
    const adapterSelect = document.getElementById("ip-edit-adapter-select");
    const adapter = adapterSelect ? adapterSelect.value : "";
    if (!adapter) {
      alert("Vui lòng chọn Card Mạng (Adapter)!");
      return;
    }

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.apply_ip_settings(adapter, "dhcp");
        this.addLog(res.success ? "success" : "error", res.message);
        alert(res.message);
        this.loadNetworkAdapters();
      } catch (err) {
        alert(`Lỗi: ${err.message}`);
      }
    } else {
      alert(`[MOCK] Đã cài DHCP cho ${adapter}!`);
    }
  },

  async runSubnetCalculation() {
    const ipInput = document.getElementById("subnet-input-ip");
    const cidrSelect = document.getElementById("subnet-input-cidr");
    const outputEl = document.getElementById("subnet-result-output");

    const ip = ipInput ? ipInput.value.trim() : "";
    const cidr = cidrSelect ? cidrSelect.value : "24";

    if (!ip) {
      alert("Vui lòng nhập địa chỉ IP!");
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
    if (badge) badge.innerText = "Đang kiểm tra...";

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.get_ipv6_status();
        if (badge) {
          badge.innerText = res.text || (res.enabled ? "✅ IPv6 Đang Bật" : "🚫 IPv6 Đã Tắt");
          badge.style.color = res.enabled ? "#10b981" : "#ef4444";
        }
      } catch (err) {
        if (badge) badge.innerText = "Lỗi kiểm tra";
      }
    } else {
      if (badge) badge.innerText = "✅ IPv6 Đang Bật (MOCK)";
    }
  },

  async setIpv6Status(enable) {
    const badge = document.getElementById("ipv6-status-badge");
    if (badge) badge.innerText = `Đang ${enable ? 'bật' : 'tắt'} IPv6...`;

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.set_ipv6_status(enable);
        this.addLog(res.success ? "success" : "error", res.message);
        alert(res.message);
        this.loadIpv6Status();
      } catch (err) {
        alert(`Lỗi: ${err.message}`);
      }
    } else {
      alert(`[MOCK] Đã ${enable ? 'bật' : 'tắt'} IPv6!`);
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

  async startIpScanner() {
    const subEl = document.getElementById("ipscan-input-subnet");
    const startEl = document.getElementById("ipscan-input-start");
    const endEl = document.getElementById("ipscan-input-end");
    const threadsEl = document.getElementById("ipscan-input-threads");

    const chkPing = document.getElementById("ipscan-chk-ping");
    const chkHost = document.getElementById("ipscan-chk-hostname");
    const chkMac = document.getElementById("ipscan-chk-mac");
    const chkHttp = document.getElementById("ipscan-chk-http");
    const chkHttps = document.getElementById("ipscan-chk-https");

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
    const check_http_port = chkHttp ? chkHttp.checked : false;
    const check_https_port = chkHttps ? chkHttps.checked : false;

    if (btnStart) btnStart.disabled = true;
    if (spinner) spinner.style.display = "inline-block";
    if (statusText) statusText.innerText = `Đang quét dải IP (${max_threads} luồng)... Vui lòng chờ...`;
    if (bodyEl) {
      bodyEl.innerHTML = `
        <tr>
          <td colspan="8" class="text-center py-4 text-muted">
            <span class="spinner-border spinner-border-sm text-primary"></span>
            Đang tiến hành quét dải IP LAN...
          </td>
        </tr>
      `;
    }

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.scan_ip_range(
          subnet_str, ip_start, ip_end, check_ping, check_hostname, check_mac, check_http_port, check_https_port, max_threads
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
          { ip: "192.168.1.1", hostname: "Router-Gateway.home", mac: "FC:AA:14:88:99:AA", vendor: "TP-Link", latency_ms: "<1ms", http: true, https: true },
          { ip: "192.168.1.100", hostname: "PC-DESKTOP-LTT", mac: "00:E0:4C:12:34:56", vendor: "Realtek", latency_ms: "<1ms", http: false, https: false },
          { ip: "192.168.1.105", hostname: "iPhone-Tuans", mac: "AC:BC:32:44:55:66", vendor: "Apple", latency_ms: "12ms", http: false, https: false }
        ];
        this.lastScanResults = mockData;
        if (badgeCount) badgeCount.innerText = "3 Online";
        if (statusText) statusText.innerText = "Hoàn tất quét LAN (MOCK)! Tìm thấy 3 thiết bị online.";
        if (btnExport) btnExport.disabled = false;
        this.renderIpScanResults(mockData);
        if (btnStart) btnStart.disabled = false;
        if (spinner) spinner.style.display = "none";
      }, 1000);
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

    bodyEl.innerHTML = results.map((item, index) => {
      const pingText = item.latency_ms ? `(${item.latency_ms})` : '';
      const vendorBadge = item.vendor && item.vendor !== 'Unknown'
        ? `<span class="badge" style="background:#e0f2fe; color:#0369a1; font-weight:600; font-size:11px;">${item.vendor}</span>`
        : `<span class="badge" style="background:#f1f5f9; color:#94a3b8; font-size:11px;">Unknown</span>`;

      let webPorts = '';
      if (item.http) webPorts += `<span class="badge" style="background:#dcfce7; color:#166534; margin-right:3px; font-size:10px;">🌐 80</span>`;
      if (item.https) webPorts += `<span class="badge" style="background:#e0e7ff; color:#3730a3; font-size:10px;">🔒 443</span>`;
      if (!webPorts) webPorts = `<span style="color:#cbd5e1; font-size:11px;">-</span>`;

      return `
        <tr style="border-bottom: 1px solid #f1f5f9;">
          <td style="text-align: center; font-weight: 600; color: #64748b; padding: 8px;">${index + 1}</td>
          <td style="text-align: center; padding: 8px;">
            <span class="badge" style="background: #dcfce7; color: #15803d; font-weight: 700; font-size: 11px; padding: 3px 8px; border-radius: 12px;">
              🟢 Online ${pingText}
            </span>
          </td>
          <td style="padding: 8px;">
            <strong style="font-family: monospace; color: #0f172a; font-size: 13px;">${item.ip}</strong>
          </td>
          <td style="padding: 8px; color: #0369a1; font-weight: 600;">
            ${item.hostname || '<span style="color:#94a3b8; font-weight:400; font-style:italic;">(Unknown)</span>'}
          </td>
          <td style="padding: 8px; font-family: monospace; color: #475569; font-size: 12px;">
            ${item.mac || '-'}
          </td>
          <td style="padding: 8px;">${vendorBadge}</td>
          <td style="text-align: center; padding: 8px;">${webPorts}</td>
          <td style="text-align: right; padding: 8px;">
            <button class="btn btn-slate-light btn-sm" onclick="app.copyToClipboard('${item.ip}')" title="Sao chép IP" style="padding: 2px 6px; font-size: 11px;">
              📋
            </button>
            ${item.http || item.https ? `
              <button class="btn btn-sky-outline btn-sm" onclick="window.open('${item.https ? 'https' : 'http'}://${item.ip}', '_blank')" title="Mở Web Interface" style="padding: 2px 6px; font-size: 11px;">
                🌐
              </button>
            ` : ''}
          </td>
        </tr>
      `;
    }).join('');
  },

  exportIpScanCsv() {
    if (!this.lastScanResults || this.lastScanResults.length === 0) {
      alert("Không có kết quả quét để xuất CSV!");
      return;
    }

    let csvContent = "data:text/csv;charset=utf-8,Index,IP Address,Hostname,MAC Address,Vendor,Latency,HTTP (80),HTTPS (443)\n";
    this.lastScanResults.forEach((row, i) => {
      csvContent += `"${i + 1}","${row.ip || ''}","${row.hostname || ''}","${row.mac || ''}","${row.vendor || ''}","${row.latency_ms || ''}","${row.http ? 'YES' : 'NO'}","${row.https ? 'YES' : 'NO'}"\n`;
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `lan_ip_scan_results_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
});
