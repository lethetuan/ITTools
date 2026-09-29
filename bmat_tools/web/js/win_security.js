/**
 * IT-Tools 2026 - Windows Security & Activation Audit Module
 */
Object.assign(AppController.prototype, {
  async runWinCheckAudit() {
    this.addLog("info", "Đang chạy quét WinCheck bản quyền 10 lớp...");
    const summaryBox = document.getElementById("wincheck-summary-box");
    const keysBox = document.getElementById("wincheck-keys-box");
    const tbody = document.getElementById("wincheck-checks-body");

    if (summaryBox) {
      summaryBox.innerHTML = `<div class="text-primary py-2">⚡ Đang kiểm tra bản quyền, KMS host, IFEO hook, tiến trình crack...</div>`;
    }

    let result = null;
    if (window.pywebview && window.pywebview.api) {
      result = await window.pywebview.api.get_wincheck_audit();
    } else {
      result = {
        level: "clean",
        title: "HỆ THỐNG SẠCH - KÍCH HOẠT HỢP LỆ (MOCK)",
        summary: "Không phát hiện công cụ crack hay giả lập KMS.",
        typeLabel: "Phương Thức:",
        typeValue: "Digital License",
        indicators: [],
        checks: [
          { name: "Máy Chủ KMS", status: "ok", statusText: "Sạch", detail: "Không có máy chủ ngoài." },
          { name: "Cổng KMS 1688", status: "ok", statusText: "Sạch", detail: "Cổng 1688 không mở." }
        ],
        keys: [
          { label: "Key Đang Cài Đặt", value: "XXXXX-XXXXX-XXXXX-XXXXX-3V66T", note: "Windows Pro", tone: "ok" }
        ]
      };
    }

    if (!result) return;

    if (summaryBox) {
      const levelClass = result.level === "critical" ? "text-danger" : (result.level === "suspicious" ? "text-warning" : "text-success");
      const bgClass = result.level === "critical" ? "bg-rose-light" : (result.level === "suspicious" ? "bg-gold-light" : "bg-light-blue");
      
      let indHtml = "";
      if (result.indicators && result.indicators.length > 0) {
        indHtml = `
          <div class="mt-2 text-danger">
            <strong>⚠️ Dấu Hiệu Lậu Phát Hiện Được (${result.indicators.length}):</strong>
            <ul class="mb-0 mt-1 pl-3">
              ${result.indicators.map(i => `<li>${i.text}</li>`).join("")}
            </ul>
          </div>
        `;
      }

      summaryBox.innerHTML = `
        <div class="ui-card ${bgClass}">
          <h4 class="${levelClass} font-bold text-lg mb-1">${result.title || 'Kết Quả Kiểm Tra'}</h4>
          <p class="mb-1">${result.summary || ''}</p>
          <p class="mb-0"><strong>${result.typeLabel || 'Phân Loại:'}</strong> <code class="code-badge">${result.typeValue || 'N/A'}</code></p>
          ${indHtml}
        </div>
      `;
    }

    if (keysBox && result.keys) {
      keysBox.innerHTML = `
        <h4 class="text-sm font-bold text-muted mb-2">🔑 KHÓA BẢN QUYỀN TRÊN MÁY:</h4>
        <div class="grid-buttons-2col gap-2">
          ${result.keys.map(k => `
            <div class="ui-card border bg-white">
              <span class="text-xs text-muted font-bold">${k.label}:</span>
              <p class="font-mono text-sm text-primary font-bold my-1">${k.value}</p>
              <span class="badge ${k.tone === 'ok' ? 'text-primary' : (k.tone === 'warn' ? 'text-gold' : 'text-danger')}">${k.note}</span>
            </div>
          `).join("")}
        </div>
      `;
    }

    if (tbody && result.checks) {
      tbody.innerHTML = "";
      result.checks.forEach(c => {
        const tr = document.createElement("tr");
        const statusBadge = c.status === "ok" ? "text-primary" : (c.status === "detected" ? "text-danger" : "text-warning");
        tr.innerHTML = `
          <td><strong>${c.name}</strong></td>
          <td><span class="badge ${statusBadge}">${c.statusText || c.status}</span></td>
          <td>${c.detail || ''}</td>
        `;
        tbody.appendChild(tr);
      });
    }

    this.addLog(result.level === "critical" ? "warn" : "success", `Hoàn tất WinCheck Audit: ${result.title}`);
  },

  async cleanWinCrack() {
    if (!confirm("Bạn CHẮC CHẮN muốn dọn sạch toàn bộ công cụ crack và gỡ bỏ KMS lậu khỏi Windows?")) return;
    this.addLog("info", "Đang dọn sạch crack & KMS lậu (Clean Crack)...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.clean_win_crack();
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
      this.runWinCheckAudit();
    }
  },

  async cleanOfficeKeys() {
    if (!confirm("Bạn CHẮC CHẮN muốn gỡ sạch toàn bộ key Office lậu & dọn máy chủ KMS Office?")) return;
    this.addLog("info", "Đang dọn sạch key Office lậu...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.clean_office_keys();
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
    }
  },

  async installKeyPrompt() {
    const key = prompt("Nhập Product Key bản quyền mới (25 ký tự):", "XXXXX-XXXXX-XXXXX-XXXXX-XXXXX");
    if (!key) return;
    this.addLog("info", `Đang cài Product Key: ${key}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.install_win_key(key);
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
      this.runWinCheckAudit();
    }
  },

  async uninstallWinKey() {
    if (!confirm("Bạn CHẮC CHẮN muốn gỡ bỏ Product Key bản quyền hiện tại khỏi Windows?")) return;
    this.addLog("info", "Đang gỡ bỏ Product Key hiện tại (slmgr /upk)...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.uninstall_win_key();
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
      this.runWinCheckAudit();
    }
  },

  async rearmWindows() {
    if (!confirm("Bạn CHẮC CHẮN muốn đặt lại thời gian dùng thử (slmgr /rearm)?")) return;
    this.addLog("info", "Đang đặt lại thời gian dùng thử (slmgr /rearm)...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.rearm_windows();
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
    }
  },

  async loadWinUpdateStatus() {
    this.addLog("info", "Đang kiểm tra trạng thái Windows Update & Security...");
    let status = null;
    if (window.pywebview && window.pywebview.api) {
      status = await window.pywebview.api.get_win_update_status();
    } else {
      status = {
        success: true,
        wu_enabled: true,
        wu_status_text: "🟢 Đang BẬT (Tự động cập nhật)",
        defender_enabled: true,
        defender_status_text: "🟢 Đang BẬT (Real-Time Protection)",
        uac_enabled: false,
        uac_status_text: "🔴 Đã TẮT (EnableLUA = 0)",
        smartscreen_enabled: true,
        smartscreen_status_text: "🟢 Đang BẬT"
      };
    }

    if (!status || !status.success) return;

    // Windows Update Card
    const wuText = document.getElementById("wu-status-text");
    const wuBadge = document.getElementById("wu-status-badge");
    const wuCard = document.getElementById("wu-status-card");
    if (wuText) wuText.innerText = status.wu_status_text;
    if (wuBadge) {
      if (status.wu_enabled) {
        wuBadge.innerText = "🟢 ĐANG BẬT";
        wuBadge.style.background = "#dcfce7";
        wuBadge.style.color = "#15803d";
        if (wuCard) {
          wuCard.style.background = "#f0fdf4";
          wuCard.style.borderColor = "#bbf7d0";
        }
      } else {
        wuBadge.innerText = "🔴 ĐÃ TẮT";
        wuBadge.style.background = "#fee2e2";
        wuBadge.style.color = "#b91c1c";
        if (wuCard) {
          wuCard.style.background = "#fef2f2";
          wuCard.style.borderColor = "#fecaca";
        }
      }
    }

    // Defender Card
    const wdText = document.getElementById("wd-status-text");
    const wdBadge = document.getElementById("wd-status-badge");
    const wdCard = document.getElementById("wd-status-card");
    if (wdText) wdText.innerText = status.defender_status_text;
    if (wdBadge) {
      if (status.defender_enabled) {
        wdBadge.innerText = "🟢 ĐANG BẬT";
        wdBadge.style.background = "#dcfce7";
        wdBadge.style.color = "#15803d";
        if (wdCard) {
          wdCard.style.background = "#f0fdf4";
          wdCard.style.borderColor = "#bbf7d0";
        }
      } else {
        wdBadge.innerText = "🔴 ĐÃ TẮT";
        wdBadge.style.background = "#fee2e2";
        wdBadge.style.color = "#b91c1c";
        if (wdCard) {
          wdCard.style.background = "#fef2f2";
          wdCard.style.borderColor = "#fecaca";
        }
      }
    }

    // UAC Badge
    const uacBadge = document.getElementById("uac-status-badge");
    if (uacBadge) {
      if (status.uac_enabled) {
        uacBadge.innerText = "🟢 ĐANG BẬT";
        uacBadge.style.background = "#dcfce7";
        uacBadge.style.color = "#15803d";
      } else {
        uacBadge.innerText = "🔴 ĐÃ TẮT";
        uacBadge.style.background = "#fee2e2";
        uacBadge.style.color = "#b91c1c";
      }
    }

    // SmartScreen Badge
    const ssBadge = document.getElementById("ss-status-badge");
    if (ssBadge) {
      if (status.smartscreen_enabled) {
        ssBadge.innerText = "🟢 ĐANG BẬT";
        ssBadge.style.background = "#dcfce7";
        ssBadge.style.color = "#15803d";
      } else {
        ssBadge.innerText = "🔴 ĐÃ TẮT";
        ssBadge.style.background = "#fee2e2";
        ssBadge.style.color = "#b91c1c";
      }
    }

    this.addLog("success", "Đã đọc trạng thái Windows Update & Security!");
  },

  async setWinUpdateStatus(enable) {
    this.addLog("info", `Đang ${enable ? 'bật' : 'tắt vĩnh viễn'} Windows Update...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.set_windows_update(enable);
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
      this.loadWinUpdateStatus();
    } else {
      alert(`[MOCK] Đã ${enable ? 'bật' : 'tắt vĩnh viễn'} Windows Update!`);
    }
  },

  async pauseWinUpdate7Days() {
    this.addLog("info", "Đang tạm dừng Windows Update 7 ngày...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.pause_windows_update_7days();
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
      this.loadWinUpdateStatus();
    } else {
      alert("[MOCK] Đã tạm dừng Windows Update 7 ngày!");
    }
  },

  async checkWinUpdateNow() {
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.check_windows_update_now();
    } else {
      alert("[MOCK] Mở cửa sổ Windows Update!");
    }
  },

  async setDefenderStatus(enable) {
    this.addLog("info", `Đang ${enable ? 'bật' : 'tắt'} Windows Defender...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.set_defender_status(enable);
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
      this.loadWinUpdateStatus();
    } else {
      alert(`[MOCK] Đã ${enable ? 'bật' : 'tắt'} Windows Defender!`);
    }
  },

  async runDefenderScan(scanType) {
    this.addLog("info", `Đang kích hoạt ${scanType === 'quick' ? 'Quét nhanh' : 'Quét toàn bộ'} Windows Defender...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.run_defender_scan(scanType);
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
    } else {
      alert(`[MOCK] Đã bắt đầu ${scanType} scan!`);
    }
  },

  async setUacStatus(enable) {
    this.addLog("info", `Đang ${enable ? 'bật' : 'tắt'} UAC...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.set_uac_status(enable);
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
      this.loadWinUpdateStatus();
    } else {
      alert(`[MOCK] Đã ${enable ? 'bật' : 'tắt'} UAC!`);
    }
  },

  async setSmartScreenStatus(enable) {
    this.addLog("info", `Đang ${enable ? 'bật' : 'tắt'} SmartScreen...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.set_smartscreen_status(enable);
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
      this.loadWinUpdateStatus();
    } else {
      alert(`[MOCK] Đã ${enable ? 'bật' : 'tắt'} SmartScreen!`);
    }
  },

  async openSecurityShortcut(target) {
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.open_security_shortcut(target);
    } else {
      alert(`[MOCK] Mở shortcut ${target}`);
    }
  },

  // ── FIREWALL MANAGER DASHBOARD ─────────────────────────────────────────
  async loadFirewallStatus() {
    this.addLog("info", "Đang kiểm tra trạng thái Windows Firewall các profile...");
    let st = null;
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_firewall_status === 'function') {
      st = await window.pywebview.api.get_firewall_status();
    } else {
      st = { success: true, domain: true, private: true, public: false, all_on: false, any_on: true };
    }

    if (!st) return;

    const domBadge = document.getElementById("fw-status-domain");
    const privBadge = document.getElementById("fw-status-private");
    const pubBadge = document.getElementById("fw-status-public");

    if (domBadge) {
      domBadge.className = st.domain ? "badge badge-success" : "badge badge-danger";
      domBadge.innerText = st.domain ? "🛡️ BẬT (Active)" : "🚫 TẮT (Disabled)";
    }
    if (privBadge) {
      privBadge.className = st.private ? "badge badge-success" : "badge badge-danger";
      privBadge.innerText = st.private ? "🛡️ BẬT (Active)" : "🚫 TẮT (Disabled)";
    }
    if (pubBadge) {
      pubBadge.className = st.public ? "badge badge-success" : "badge badge-danger";
      pubBadge.innerText = st.public ? "🛡️ BẬT (Active)" : "🚫 TẮT (Disabled)";
    }

    this.addLog("success", "Đã nạp trạng thái Windows Firewall!");
  },

  async setFirewallAction(action) {
    this.addLog("info", `Đang thực hiện lệnh Firewall: ${action}...`);
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.set_firewall_action === 'function') {
      const res = await window.pywebview.api.set_firewall_action(action);
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
      this.loadFirewallStatus();
    } else {
      alert(`[MOCK] Đã thực hiện ${action} cho Firewall!`);
    }
  }
});
