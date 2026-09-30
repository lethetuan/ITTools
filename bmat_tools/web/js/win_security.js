/**
 * IT Tool LTT 2026 - Windows Security & Activation Audit Module
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

  async deactivateDigitalLicense() {
    const confirmMsg = "CẢNH BÁO HỦY KÍCH HOẠT DIGITAL LICENSE:\n\n" +
      "Hệ thống sẽ ngắt liên kết bản quyền kỹ thuật số (HWID), gỡ key và chuyển Windows về trạng thái 'Chưa Kích Hoạt' (Not Active).\n\n" +
      "Bạn có chắc chắn muốn thực hiện không?\n(Bạn có thể khôi phục lại bất kỳ lúc nào bằng nút 'Khôi Phục Digital License')";
    if (!confirm(confirmMsg)) return;
    this.addLog("warn", "Đang hủy kích hoạt Digital License và đưa Windows về trạng thái Chưa kích hoạt...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.deactivate_win_digital();
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
      this.runWinCheckAudit();
    }
  },

  async restoreDigitalLicense() {
    if (!confirm("Bạn muốn khôi phục lại kích hoạt Bản Quyền Kỹ Thuật Số (Digital License) theo máy tính?")) return;
    this.addLog("info", "Đang nạp lại khóa mặc định và kích hoạt Digital License (slmgr /ato)...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.restore_win_digital();
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
      this.runWinCheckAudit();
    }
  },

  async rearmWindows() {
    if (!confirm("Bạn CHẮC CHẮN muốn đặt lại thời gian dùng thử Windows (slmgr /rearm)?")) return;
    this.addLog("info", "Đang đặt lại thời gian dùng thử Windows (slmgr /rearm)...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.rearm_windows();
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
      this.runWinCheckAudit();
    }
  },

  async rearmOffice() {
    if (!confirm("Bạn CHẮC CHẮN muốn đặt lại thời gian dùng thử Microsoft Office (ospp.vbs /rearm)?")) return;
    this.addLog("info", "Đang đặt lại thời gian dùng thử Office...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.rearm_office();
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
    }
  },

  async installOfficeKeyPrompt() {
    const key = prompt("Nhập Product Key Microsoft Office mới (25 ký tự):", "XXXXX-XXXXX-XXXXX-XXXXX-XXXXX");
    if (!key) return;
    this.addLog("info", `Đang cài đặt Product Key Office: ${key}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.install_office_key(key);
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
      if (status.wu_badge === "⏸️ TẠM DỪNG" || (!status.wu_enabled && status.wu_status_text.includes("TẠM DỪNG"))) {
        wuBadge.innerText = status.wu_badge || "⏸️ TẠM DỪNG";
        wuBadge.style.background = "#fef3c7";
        wuBadge.style.color = "#b45309";
        if (wuCard) {
          wuCard.style.background = "#fffbeb";
          wuCard.style.borderColor = "#fde68a";
        }
      } else if (status.wu_enabled) {
        wuBadge.innerText = status.wu_badge || "🟢 ĐANG BẬT";
        wuBadge.style.background = "#dcfce7";
        wuBadge.style.color = "#15803d";
        if (wuCard) {
          wuCard.style.background = "#f0fdf4";
          wuCard.style.borderColor = "#bbf7d0";
        }
      } else {
        wuBadge.innerText = status.wu_badge || "🔴 ĐÃ TẮT";
        wuBadge.style.background = "#fee2e2";
        wuBadge.style.color = "#b91c1c";
        if (wuCard) {
          wuCard.style.background = "#fef2f2";
          wuCard.style.borderColor = "#fecaca";
        }
      }
    }

    // Defender / Antivirus Card
    const wdText = document.getElementById("wd-status-text");
    const wdBadge = document.getElementById("wd-status-badge");
    const wdCard = document.getElementById("wd-status-card");
    if (wdText) wdText.innerText = status.defender_status_text;
    if (wdBadge) {
      if (status.has_third_party) {
        wdBadge.innerText = status.defender_badge || "🟢 AN TOÀN";
        wdBadge.style.background = "#e0f2fe";
        wdBadge.style.color = "#0369a1";
        if (wdCard) {
          wdCard.style.background = "#f0f9ff";
          wdCard.style.borderColor = "#bae6fd";
        }
      } else if (status.defender_enabled) {
        wdBadge.innerText = status.defender_badge || "🟢 ĐANG BẬT";
        wdBadge.style.background = "#dcfce7";
        wdBadge.style.color = "#15803d";
        if (wdCard) {
          wdCard.style.background = "#f0fdf4";
          wdCard.style.borderColor = "#bbf7d0";
        }
      } else {
        wdBadge.innerText = status.defender_badge || "🔴 ĐÃ TẮT";
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
    this.addLog("info", "Đang kiểm tra trạng thái Windows Firewall các profile và quy tắc...");
    let st = null;
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_firewall_status === 'function') {
      st = await window.pywebview.api.get_firewall_status();
    } else {
      st = { success: true, domain: true, private: true, public: true, all_on: true, any_on: true, allow_inbound: false, file_sharing: true, file_sharing_count: 43, rdp: true, rdp_count: 3 };
    }

    if (!st) return;

    const domBadge = document.getElementById("fw-status-domain");
    const privBadge = document.getElementById("fw-status-private");
    const pubBadge = document.getElementById("fw-status-public");
    const inBadge = document.getElementById("fw-status-inbound");
    const sharingBadge = document.getElementById("fw-status-sharing");
    const rdpBadge = document.getElementById("fw-status-rdp");

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
    if (inBadge) {
      inBadge.className = st.allow_inbound ? "badge badge-danger" : "badge badge-success";
      inBadge.innerText = st.allow_inbound ? "🔓 Cho phép tất cả" : "🔒 Chặn (Mặc định)";
    }
    if (sharingBadge) {
      sharingBadge.className = st.file_sharing ? "badge badge-success" : "badge badge-danger";
      sharingBadge.innerText = st.file_sharing ? `🟢 ĐANG BẬT (${st.file_sharing_count || 'Active'} quy tắc)` : "🚫 ĐANG TẮT";
    }
    if (rdpBadge) {
      rdpBadge.className = st.rdp ? "badge badge-success" : "badge badge-danger";
      rdpBadge.innerText = st.rdp ? `🟢 ĐANG BẬT (${st.rdp_count || 'Active'} quy tắc)` : "🚫 ĐANG TẮT";
    }

    this.addLog("success", "Đã nạp trạng thái Windows Firewall thực tế!");
  },

  async setFirewallAction(action) {
    this.addLog("info", `Đang thực hiện lệnh Firewall: ${action}...`);
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.set_firewall_action === 'function') {
      const res = await window.pywebview.api.set_firewall_action(action);
      this.addLog(res.success ? "success" : "error", res.message);
      // Cập nhật ngay trạng thái trên giao diện trước khi alert
      await this.loadFirewallStatus();
      alert(res.message);
    } else {
      alert(`[MOCK] Đã thực hiện ${action} cho Firewall!`);
    }
  },

  currentFwRulesList: [],

  async showFirewallRulesDetail(type = 'fps') {
    const modal = document.getElementById("fw-rules-detail-modal");
    if (!modal) return;

    const titleElem = document.getElementById("fw-rules-modal-title");
    const subElem = document.getElementById("fw-rules-modal-subtitle");
    const tbody = document.getElementById("fw-rules-modal-tbody");
    const searchInput = document.getElementById("fw-rules-search-input");

    if (searchInput) searchInput.value = "";

    const typeName = type === 'fps' ? 'Chia Sẻ File & Máy In (LAN)' : 'Remote Desktop (RDP)';
    if (titleElem) titleElem.innerText = `Chi Tiết Quy Tắc Firewall: ${typeName}`;
    if (subElem) subElem.innerText = `Đang quét danh sách quy tắc thời gian thực từ Windows...`;

    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 20px; color: #64748b;">⏳ Đang tải dữ liệu quy tắc thời gian thực từ máy tính...</td></tr>`;
    modal.style.display = "flex";

    let res = null;
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_firewall_rules_detail === 'function') {
      res = await window.pywebview.api.get_firewall_rules_detail(type);
    } else {
      res = { success: true, rules: [] };
    }

    this.currentFwRulesList = (res && res.rules) ? res.rules : [];
    if (subElem) subElem.innerText = `Thời gian thực từ hệ thống (${this.currentFwRulesList.length} quy tắc được tìm thấy)`;

    this.renderFirewallRulesModal(this.currentFwRulesList);
  },

  renderFirewallRulesModal(rules) {
    const tbody = document.getElementById("fw-rules-modal-tbody");
    const countLabel = document.getElementById("fw-rules-count-label");
    const summaryBadges = document.getElementById("fw-rules-summary-badges");
    if (!tbody) return;

    if (!rules || rules.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 20px; color: #94a3b8;">Không có quy tắc nào phù hợp.</td></tr>`;
      if (countLabel) countLabel.innerText = "Hiển thị 0 quy tắc";
      return;
    }

    const enabledCount = rules.filter(r => (r.enabled || '').toLowerCase() === 'yes').length;
    if (summaryBadges) {
      summaryBadges.innerHTML = `
        <span class="badge badge-success" style="font-size: 11px;">🟢 Bật: ${enabledCount}</span>
        <span class="badge badge-danger" style="font-size: 11px;">🚫 Tắt: ${rules.length - enabledCount}</span>
      `;
    }
    if (countLabel) countLabel.innerText = `Đang hiển thị ${rules.length} quy tắc`;

    tbody.innerHTML = rules.map((r, idx) => {
      const isEn = (r.enabled || '').toLowerCase() === 'yes';
      const isOut = (r.direction || '').toLowerCase() === 'out';
      const port = r.local_port || r.remote_port || 'Tất cả';

      return `
        <tr style="border-bottom: 1px solid #f1f5f9; background: ${idx % 2 === 0 ? '#ffffff' : '#fafafa'};">
          <td style="padding: 6px 10px; color: #94a3b8; font-size: 11px;">${idx + 1}</td>
          <td style="padding: 6px 10px;">
            <span style="font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; background: ${isOut ? '#e0f2fe' : '#fef3c7'}; color: ${isOut ? '#0369a1' : '#b45309'};">
              ${isOut ? '📤 OUT' : '📥 IN'}
            </span>
          </td>
          <td style="padding: 6px 10px; font-weight: 600; color: #1e293b;">
            ${r.name || 'N/A'}
          </td>
          <td style="padding: 6px 10px; color: #475569; font-size: 11.5px;">
            ${r.category || 'Khác'}
          </td>
          <td style="padding: 6px 10px; color: #64748b; font-size: 11px;">
            ${r.profiles || 'All'}
          </td>
          <td style="padding: 6px 10px; font-family: monospace; font-size: 11.5px;">
            ${r.protocol || 'Any'}
          </td>
          <td style="padding: 6px 10px; font-family: monospace; font-size: 11.5px; color: #0284c7;">
            ${port}
          </td>
          <td style="padding: 6px 10px;">
            <span class="badge ${isEn ? 'badge-success' : 'badge-danger'}" style="font-size: 11px;">
              ${isEn ? 'BẬT' : 'TẮT'}
            </span>
          </td>
        </tr>
      `;
    }).join("");
  },

  filterFirewallRulesModal() {
    const q = (document.getElementById("fw-rules-search-input")?.value || "").toLowerCase().trim();
    if (!q) {
      this.renderFirewallRulesModal(this.currentFwRulesList);
      return;
    }
    const filtered = this.currentFwRulesList.filter(r => {
      const matchName = (r.name || '').toLowerCase().includes(q);
      const matchCat = (r.category || '').toLowerCase().includes(q);
      const matchPort = (r.local_port || '' + r.remote_port || '').toLowerCase().includes(q);
      const matchProto = (r.protocol || '').toLowerCase().includes(q);
      const matchDir = (r.direction || '').toLowerCase().includes(q);
      return matchName || matchCat || matchPort || matchProto || matchDir;
    });
    this.renderFirewallRulesModal(filtered);
  },

  closeFirewallRulesDetail() {
    const modal = document.getElementById("fw-rules-detail-modal");
    if (modal) modal.style.display = "none";
  }
});
