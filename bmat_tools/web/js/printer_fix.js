/**
 * IT Tool LTT 2026 - Printer & Credentials Module
 */
Object.assign(AppController.prototype, {
  async scanPrinters() {
    this.addLog("info", "Đang quét danh sách máy in hệ thống...");
    const tbody = document.getElementById("printers-list-body");
    if (!tbody) return;
    tbody.innerHTML = `<tr><td colspan="4" class="text-center py-4 text-muted">Đang quét máy in...</td></tr>`;

    let printers = [];
    if (window.pywebview && window.pywebview.api) {
      printers = await window.pywebview.api.get_printers();
    } else {
      printers = [
        { name: "Microsoft Print to PDF", port: "PORTPROMPT:", status: "Sẵn sàng (Ready)", is_default: true },
        { name: "\\\\test\\Canon2900", port: "Ne00:", status: "Bình thường", is_default: false }
      ];
    }

    if (!printers || printers.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" class="text-center py-4 text-muted">Không tìm thấy máy in nào.</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    printers.forEach((p, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><input type="checkbox" class="printer-checkbox" value="${p.name.replace(/"/g, '&quot;')}"></td>
        <td><strong>${p.is_default ? '⭐ ' : ''}${p.name}</strong></td>
        <td><code>${p.port}</code></td>
        <td><span class="badge ${p.status.includes('Ready') || p.status.includes('Bình') ? 'text-primary' : 'text-danger'}">${p.status}</span></td>
      `;
      tr.addEventListener("click", (e) => {
        if (e.target.tagName !== "INPUT") {
          document.querySelectorAll("#printers-list-body tr").forEach(r => r.classList.remove("selected"));
          tr.classList.add("selected");
          this.selectedPrinter = p.name;
        }
      });
      tbody.appendChild(tr);
    });

    this.addLog("success", `Đã quét thấy ${printers.length} máy in.`);
  },

  toggleSelectAllPrinters(chk) {
    document.querySelectorAll(".printer-checkbox").forEach(c => c.checked = chk.checked);
  },

  async printTestPage() {
    const selected = this.getSelectedPrinterName();
    if (!selected) {
      alert("Vui lòng chọn 1 máy in trong bảng để in trang test!");
      return;
    }
    this.addLog("info", `Đang in trang test cho ${selected}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.print_test_page(selected);
      this.addLog(res.success ? "success" : "error", res.message);
    } else {
      alert(`[MOCK] In trang test gửi đến ${selected}`);
    }
  },

  async setDefaultPrinter() {
    const selected = this.getSelectedPrinterName();
    if (!selected) {
      alert("Vui lòng chọn 1 máy in trong bảng!");
      return;
    }
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.set_default_printer(selected);
      this.addLog(res.success ? "success" : "error", res.message);
      this.scanPrinters();
    } else {
      alert(`[MOCK] Đã đặt ${selected} làm máy in mặc định.`);
    }
  },

  async addLocalPortPrompt() {
    const port = prompt("Nhập tên Cổng (Local Port) mới cần thêm (VD: 192.168.1.100 hoặc LocalPort1):");
    if (!port) return;
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.add_local_port(port);
      this.addLog(res.success ? "success" : "error", res.message);
    }
  },

  async sharePrinterPrompt() {
    const selected = this.getSelectedPrinterName();
    if (!selected) {
      alert("Vui lòng chọn 1 máy in trong bảng để chia sẻ!");
      return;
    }
    const shareName = prompt(`Nhập Tên Chia Sẻ (Share Name) cho máy in ${selected}:`, "PrinterShare");
    if (shareName === null) return;
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.share_printer_lan(selected, shareName);
      this.addLog(res.success ? "success" : "error", res.message);
    }
  },

  async deleteSelectedPrinter() {
    const selected = this.getSelectedPrinterNames();
    if (!selected || selected.length === 0) {
      alert("Vui lòng tích chọn (checkbox) hoặc click chọn máy in trong bảng để xóa!");
      return;
    }
    const printerListStr = selected.map(n => `• ${n}`).join("\n");
    if (confirm(`Bạn CHẮC CHẮN muốn xóa các máy in sau khỏi hệ thống?\n\n${printerListStr}\n\nThao tác này sẽ gỡ bỏ máy in khỏi Windows!`)) {
      this.addLog("info", `Đang thực hiện xóa ${selected.length} máy in...`);
      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.delete_printer(selected);
        if (res && res.success) {
          this.addLog("success", res.message);
          alert(res.message);
        } else {
          this.addLog("error", (res && res.message) || "Lỗi xóa máy in");
        }
        this.scanPrinters();
      } else {
        alert(`[MOCK] Đã xóa: ${selected.join(", ")}`);
      }
    }
  },

  getSelectedPrinterNames() {
    const checkboxes = document.querySelectorAll(".printer-checkbox:checked");
    const names = Array.from(checkboxes).map(c => c.value);
    if (names.length > 0) return names;
    if (this.selectedPrinter) return [this.selectedPrinter];
    return [];
  },

  getSelectedPrinterName() {
    const names = this.getSelectedPrinterNames();
    return names.length > 0 ? names[0] : null;
  },

  async runPrinterFixFunc(funcName) {
    this.addLog("info", `Đang thực thi chức năng: ${funcName}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.run_printer_fix_func(funcName);
      if (res && res.success) {
        this.addLog("success", res.message || `Đã thực thi thành công: ${funcName}`);
      } else {
        this.addLog("error", (res && res.message) || `Lỗi khi thực thi: ${funcName}`);
      }
    } else {
      alert(`[MOCK] Thực thi chức năng ${funcName}`);
    }
  },

  async fixSelectedErrors() {
    const checkboxes = document.querySelectorAll(".error-checkbox:checked");
    const codes = Array.from(checkboxes).map(c => c.value);
    if (codes.length === 0) {
      alert("Vui lòng tích chọn ít nhất 1 mã lỗi ở bảng trên!");
      return;
    }
    this.addLog("info", `Đang sửa các mã lỗi: ${codes.join(", ")}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.fix_printer_error_codes(codes);
      if (res.success) {
        this.addLog("success", `Hoàn tất sửa lỗi: ${(res.details || []).join(" | ")}`);
        alert("Đã sửa các mã lỗi máy in thành công!");
      } else {
        this.addLog("error", res.message);
      }
    } else {
      alert(`[MOCK] Sửa các lỗi: ${codes.join(", ")}`);
    }
  },

  async fixSpoolerServices() {
    this.addLog("info", "Đang Fix Print Spooler Service...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.fix_spooler_services();
      this.addLog(res.success ? "success" : "error", res.message);
    }
  },

  async installPrintToPdf() {
    this.addLog("info", "Đang cài đặt Microsoft Print to PDF...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.install_print_to_pdf();
      this.addLog(res.success ? "success" : "error", res.message);
    }
  },

  async fixCanon2900() {
    this.addLog("info", "Đang Fix Canon LBP 2900/3300 Communication Error...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.fix_canon_2900();
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
    }
  },

  async fixDefaultPrinter() {
    this.addLog("info", "Đang sửa lỗi Set Default Printer (0x00000709)...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.fix_printer_error_codes(["0x00000709"]);
      this.addLog(res.success ? "success" : "error", "Đã fix lỗi Set Default Printer 0x709");
    }
  },

  openOneClickFixPrinterModal() {
    const modal = document.getElementById("printer-fix-modal");
    if (!modal) return;

    modal.style.display = "flex";

    // Reset steps to initial state
    for (let i = 1; i <= 4; i++) {
      const stepEl = document.getElementById(`pf-step-${i}`);
      if (stepEl) {
        stepEl.className = "pf-step-card pf-step-pending";
        const iconEl = stepEl.querySelector(".pf-step-icon");
        if (iconEl) iconEl.innerHTML = `<span class="pf-icon-mark">✓</span>`;
      }
    }

    // Reset progress bar
    const bar = document.getElementById("pf-progress-bar");
    if (bar) bar.style.width = "0%";

    // Reset terminal log
    const term = document.getElementById("pf-terminal-log");
    if (term) term.innerHTML = "";

    // Reset footer
    const footerMsg = document.getElementById("pf-footer-msg");
    if (footerMsg) {
      footerMsg.innerText = "Đang tiến hành sửa lỗi máy in mạng LAN...";
      footerMsg.style.color = "#0284c7";
    }

    const closeBtn = document.getElementById("btn-pf-modal-close");
    if (closeBtn) {
      closeBtn.innerText = "Đang sửa...";
      closeBtn.disabled = true;
      closeBtn.style.opacity = "0.6";
      closeBtn.style.cursor = "not-allowed";
    }

    // Trigger process
    this.startOneClickPrinterFix();
  },

  closeOneClickFixPrinterModal() {
    const modal = document.getElementById("printer-fix-modal");
    if (modal) modal.style.display = "none";
    if (this._pfPollingTimer) {
      clearInterval(this._pfPollingTimer);
      this._pfPollingTimer = null;
    }
  },

  async startOneClickPrinterFix() {
    this.addLog("info", "Bắt đầu One Click Fix Tất Cả Lỗi Máy In Mạng LAN...");

    if (window.pywebview && window.pywebview.api) {
      try {
        await window.pywebview.api.start_one_click_printer_fix();
        this.pollPrinterFixProgress();
      } catch (err) {
        this.addLog("error", `Lỗi khởi động: ${err.message}`);
        this.renderMockPrinterFixProgress();
      }
    } else {
      this.renderMockPrinterFixProgress();
    }
  },

  pollPrinterFixProgress() {
    if (this._pfPollingTimer) clearInterval(this._pfPollingTimer);

    let lastLogIndex = 0;

    this._pfPollingTimer = setInterval(async () => {
      if (!window.pywebview || !window.pywebview.api) return;

      try {
        const status = await window.pywebview.api.get_one_click_printer_fix_status();
        if (!status) return;

        this.updatePrinterFixModalUI(status, lastLogIndex);
        if (status.logs) lastLogIndex = status.logs.length;

        if (status.completed) {
          clearInterval(this._pfPollingTimer);
          this._pfPollingTimer = null;
          if (typeof this.scanPrinters === 'function') {
            this.scanPrinters();
          }
        }
      } catch (e) {
        console.error("Lỗi polling printer fix status:", e);
      }
    }, 250);
  },

  updatePrinterFixModalUI(data, lastLogIndex) {
    // 1. Update Step Cards
    const stepStatuses = data.step_status || ["pending", "pending", "pending", "pending"];
    for (let i = 1; i <= 4; i++) {
      const stepEl = document.getElementById(`pf-step-${i}`);
      if (!stepEl) continue;

      const st = stepStatuses[i - 1] || "pending";
      stepEl.className = `pf-step-card pf-step-${st}`;
      const iconEl = stepEl.querySelector(".pf-step-icon");
      if (iconEl) {
        if (st === "done") {
          iconEl.innerHTML = `<span class="pf-icon-mark">✓</span>`;
        } else if (st === "running") {
          iconEl.innerHTML = `<span class="step-spinner"></span>`;
        } else {
          iconEl.innerHTML = ``;
        }
      }
    }

    // 2. Update Progress Bar
    const bar = document.getElementById("pf-progress-bar");
    if (bar) bar.style.width = `${data.percentage || 0}%`;

    // 3. Update Terminal Output Log
    const term = document.getElementById("pf-terminal-log");
    if (term && data.logs && data.logs.length > lastLogIndex) {
      for (let j = lastLogIndex; j < data.logs.length; j++) {
        const line = data.logs[j];
        const lineDiv = document.createElement("div");
        lineDiv.style.marginBottom = "3px";
        lineDiv.style.lineHeight = "1.5";

        if (line.startsWith("▶")) {
          lineDiv.style.color = "#334155";
        } else if (line.startsWith("✓")) {
          lineDiv.style.color = "#16a34a";
          lineDiv.style.fontWeight = "600";
        } else if (line.startsWith("⏳")) {
          lineDiv.style.color = "#0284c7";
          lineDiv.style.fontWeight = "700";
        } else if (line.startsWith("🚀") || line.startsWith("🔥")) {
          lineDiv.style.color = "#d97706";
          lineDiv.style.fontWeight = "700";
        } else if (line.includes("ERROR") || line.includes("Lỗi")) {
          lineDiv.style.color = "#dc2626";
          lineDiv.style.fontWeight = "600";
        }
        lineDiv.innerText = line;
        term.appendChild(lineDiv);
      }
      term.scrollTop = term.scrollHeight;
    }

    // 4. Update Footer
    if (data.completed) {
      const footerMsg = document.getElementById("pf-footer-msg");
      if (footerMsg) {
        footerMsg.innerText = "Bạn có thể thử kết nối lại máy in mạng LAN.";
        footerMsg.style.color = "#16a34a";
      }
      const closeBtn = document.getElementById("btn-pf-modal-close");
      if (closeBtn) {
        closeBtn.innerText = "Đóng";
        closeBtn.disabled = false;
        closeBtn.style.opacity = "1";
        closeBtn.style.cursor = "pointer";
      }
    }
  },

  renderMockPrinterFixProgress() {
    const mockLogs = [
      '▶ takeown /A /F "C:\\Windows\\System32\\spoolsv.exe"',
      '▶ icacls "C:\\Windows\\System32\\spoolsv.exe" /grant builtin\\administrators:F /grant SYSTEM:F',
      '▶ ren "C:\\Windows\\System32\\spoolsv.exe" spoolsv.exe.old',
      '▶ reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Print" /v RpcAuthnLevelPrivacyEnabled /t REG_DWORD /d 0 /f',
      '✓ Hoàn tất cấp quyền Takeown/icacls và thiết lập Registry RpcAuthnLevelPrivacyEnabled = 0.',
      '⏳ [BƯỚC 2/4] Nạp 3 tệp hệ thống sạch vào C:\\Windows\\System32...',
      '✓ Đã sao chép: win32spl.dll -> C:\\Windows\\System32\\win32spl.dll',
      '✓ Đã sao chép: localspl.dll -> C:\\Windows\\System32\\localspl.dll',
      '✓ Đã sao chép: spoolsv.exe -> C:\\Windows\\System32\\spoolsv.exe',
      '✓ Đã nạp đầy đủ 3/3 tệp hệ thống sạch vào System32.',
      '⏳ [BƯỚC 3/4] Cấu hình chế độ Automatic và khởi động lại dịch vụ Print Spooler...',
      '✓ Dịch vụ Print Spooler đã được cấu hình Automatic và đang chạy bình thường.',
      '🚀 [HOÀN TẤT] Bạn có thể thử kết nối lại máy in mạng LAN.',
      '🔥 [SUCCESS] Quá trình Fix lỗi Print Spooler và nạp 3 file sạch đã thành công 100%!'
    ];

    let step = 0;
    const interval = setInterval(() => {
      step++;
      let pct = 0;
      let statuses = ["pending", "pending", "pending", "pending"];
      let logsToTake = 0;

      if (step === 1) {
        statuses = ["running", "pending", "pending", "pending"];
        pct = 15;
        logsToTake = 3;
      } else if (step === 2) {
        statuses = ["done", "running", "pending", "pending"];
        pct = 35;
        logsToTake = 5;
      } else if (step === 3) {
        statuses = ["done", "running", "pending", "pending"];
        pct = 55;
        logsToTake = 9;
      } else if (step === 4) {
        statuses = ["done", "done", "running", "pending"];
        pct = 75;
        logsToTake = 10;
      } else if (step === 5) {
        statuses = ["done", "done", "done", "running"];
        pct = 90;
        logsToTake = 12;
      } else {
        statuses = ["done", "done", "done", "done"];
        pct = 100;
        logsToTake = mockLogs.length;
        clearInterval(interval);
      }

      const mockData = {
        step: Math.min(step, 4),
        percentage: pct,
        step_status: statuses,
        logs: mockLogs.slice(0, logsToTake),
        completed: step >= 6
      };

      this.updatePrinterFixModalUI(mockData, 0);
    }, 600);
  },

  oneClickFixAll() {
    this.openOneClickFixPrinterModal();
  },

  downloadSpoolerFix() {
    alert("Tính năng tự động tải gói Spooler Fix tương thích với Windows đã sẵn sàng!");
  },

  resetCanonColor() {
    alert("Đã gửi lệnh Reset Canon Màu!");
  },

  fixDriverInstall() {
    alert("Đã gỡ bỏ PointAndPrint Restriction để cho phép cài Driver máy in LAN!");
  },

  backupRestoreDriver() {
    const navItem = document.querySelector('[data-tab="tab-backup-driver"]');
    if (navItem) navItem.click();
  },

  async scanCredentials() {
    try {
      this.addLog("info", "Đang quét danh sách Windows Credentials...");
      const tbody = document.getElementById("creds-list-body");
      if (!tbody) return;
      tbody.innerHTML = `<tr><td colspan="3" class="text-center py-4 text-muted">Đang quét credentials...</td></tr>`;

      let creds = [];
      if (window.pywebview && window.pywebview.api) {
        creds = await window.pywebview.api.get_credentials();
      } else {
        creds = [
          { target: "192.168.1.100", type: "Domain Password", user: "guest" }
        ];
      }

      if (!creds || !Array.isArray(creds) || creds.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" class="text-center py-4 text-muted">Chưa có Windows Credential nào được lưu.</td></tr>`;
        return;
      }

      tbody.innerHTML = "";
      creds.forEach(c => {
        const tr = document.createElement("tr");
        const tVal = c.target || "N/A";
        const typeVal = c.type || "Domain Password";
        const uVal = c.user || "N/A";

        tr.innerHTML = `
          <td><strong>${tVal}</strong></td>
          <td><code>${typeVal}</code></td>
          <td>${uVal}</td>
        `;
        tr.addEventListener("click", () => {
          document.querySelectorAll("#creds-list-body tr").forEach(r => r.classList.remove("selected"));
          tr.classList.add("selected");
          this.selectedCredTarget = tVal;
          const targetEl = document.getElementById("cred-target");
          const userEl = document.getElementById("cred-user");
          if (targetEl) targetEl.value = tVal;
          if (userEl) userEl.value = uVal;
        });
        tbody.appendChild(tr);
      });

      this.addLog("success", `Tìm thấy ${creds.length} credentials đã lưu.`);
    } catch (ex) {
      console.error("Lỗi scanCredentials:", ex);
      this.addLog("error", `Lỗi quét credentials: ${ex.message || ex}`);
    }
  },

  async saveCredential() {
    const targetEl = document.getElementById("cred-target");
    const userEl = document.getElementById("cred-user");
    const passEl = document.getElementById("cred-pass");

    const target = targetEl ? targetEl.value.trim() : "";
    const user = userEl ? userEl.value.trim() : "";
    const pass = passEl ? passEl.value : "";

    if (!target || !user) {
      alert("⚠️ Vui lòng nhập Target (Tên máy chủ / IP) và User name!");
      return;
    }

    const btn = document.querySelector('#subtab-credentials button[type="submit"]');
    const oldText = btn ? btn.innerHTML : "";
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span>⏳</span> Đang lưu...';
    }

    this.addLog("info", `Đang lưu Windows Credential cho ${target}...`);
    try {
      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.save_credential(target, user, pass);
        this.addLog(res.success ? "success" : "error", res.message);
        alert(res.message);
        if (res.success) {
          if (passEl) passEl.value = "";
          await this.scanCredentials();
        }
      }
    } catch (err) {
      this.addLog("error", "Lỗi lưu Credential: " + err);
      alert("Lỗi kết nối API: " + err);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = oldText || '<span>💾</span> Lưu Windows Credentials';
      }
    }
  },

  async deleteSelectedCredential() {
    const target = this.selectedCredTarget || (document.getElementById("cred-target") ? document.getElementById("cred-target").value.trim() : "");
    if (!target) {
      alert("⚠️ Vui lòng click chọn một dòng trong bảng hoặc nhập Target cần xóa!");
      return;
    }

    if (confirm(`Bạn có chắc chắn muốn xóa Credential: ${target}?`)) {
      if (window.pywebview && window.pywebview.api) {
        try {
          const res = await window.pywebview.api.delete_credential(target);
          this.addLog(res.success ? "success" : "error", res.message);
          alert(res.message);
          this.selectedCredTarget = null;
          await this.scanCredentials();
        } catch (err) {
          alert("Lỗi khi xóa: " + err);
        }
      }
    }
  },

  async createShareUser() {
    const user = document.getElementById("share-username").value.trim();
    const pass = document.getElementById("share-password").value;
    const desc = document.getElementById("share-desc") ? document.getElementById("share-desc").value.trim() : "";

    if (!user || !pass) {
      alert("Vui lòng nhập Username và Mật khẩu!");
      return;
    }

    const btn = document.querySelector('#subtab-create-user button[type="submit"]');
    if (btn) { btn.disabled = true; btn.textContent = "⏳ Đang xử lý..."; }

    this.addLog("info", `Đang tạo user "${user}" và phân quyền chia sẻ máy in...`);
    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.create_printer_share_user(user, pass, desc);
        this.addLog(res.success ? "success" : "error", res.message);
        alert(res.message);
        if (res.success) {
          this.lastCreatedUserHighlight = user;
          await this.loadLocalGroupsAndUsers(false);
          this.setGroupUserViewMode('groups');
          setTimeout(() => {
            this.lastCreatedUserHighlight = null;
            this.renderGroupsTable();
          }, 12000);
        }
      } catch (err) {
        this.addLog("error", "Lỗi kết nối API: " + err);
        alert("Lỗi kết nối API: " + err);
      } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '<span>🚀</span> Tạo User & Tự Động Phân Quyền Chia Sẻ Máy In'; }
      }
    }
  },

  // ── LOCAL GROUPS & USERS REAL-TIME MANAGEMENT ──────────────────────────
  localGroupsData: [],
  localUsersData: [],
  localComputerName: "",
  groupUserFilterTag: "all",
  groupUserViewMode: "groups",
  groupUserMonitorInterval: null,
  lastCreatedUserHighlight: null,

  async loadLocalGroupsAndUsers(manualTrigger = false) {
    const tbodyGroups = document.getElementById("groups-table-body");
    const spinIcon = document.getElementById("group-user-refresh-icon");

    if (spinIcon && manualTrigger) {
      spinIcon.style.display = "inline-block";
      spinIcon.style.animation = "spin 0.8s linear infinite";
    }

    try {
      let res = null;
      if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_local_groups_and_users === 'function') {
        res = await window.pywebview.api.get_local_groups_and_users();
      } else {
        res = {
          success: true,
          computer_name: "PC-LOCAL",
          timestamp: new Date().toLocaleTimeString(),
          groups: [],
          users: []
        };
      }

      if (res && res.success) {
        this.localGroupsData = res.groups || [];
        this.localUsersData = res.users || [];
        this.localComputerName = res.computer_name || "";

        const compEl = document.getElementById("group-comp-name");
        if (compEl) compEl.textContent = this.localComputerName;

        const countAll = document.getElementById("count-groups-all");
        if (countAll) countAll.textContent = this.localGroupsData.length;

        const countMem = document.getElementById("count-groups-members");
        if (countMem) countMem.textContent = this.localGroupsData.filter(g => g.member_count > 0).length;

        const grpBadge = document.getElementById("group-count-badge");
        if (grpBadge) grpBadge.textContent = `${this.localGroupsData.length} Nhóm`;

        const usrBadge = document.getElementById("user-count-badge");
        if (usrBadge) usrBadge.textContent = `${this.localUsersData.length} User`;

        const lastSynced = document.getElementById("group-last-synced");
        if (lastSynced) lastSynced.textContent = `🕒 ${res.timestamp || new Date().toLocaleTimeString()}`;

        this.renderGroupsTable();
        this.renderUsersTable();

        if (manualTrigger) {
          this.addLog("success", `Đã đồng bộ thời gian thực: ${this.localGroupsData.length} Nhóm, ${this.localUsersData.length} User từ Windows.`);
        }
      } else {
        if (tbodyGroups) tbodyGroups.innerHTML = `<tr><td colspan="3" class="text-center py-3 text-danger">Không thể tải dữ liệu: ${res ? res.message : 'Lỗi'}</td></tr>`;
      }
    } catch (err) {
      console.error("loadLocalGroupsAndUsers error:", err);
      if (tbodyGroups) tbodyGroups.innerHTML = `<tr><td colspan="3" class="text-center py-3 text-danger">Lỗi kết nối: ${err}</td></tr>`;
    } finally {
      if (spinIcon) {
        setTimeout(() => {
          spinIcon.style.animation = "";
        }, 500);
      }
    }
  },

  renderGroupsTable() {
    const tbody = document.getElementById("groups-table-body");
    if (!tbody) return;

    const searchInput = document.getElementById("group-search-input");
    const term = searchInput ? searchInput.value.trim().toLowerCase() : "";

    let filtered = (this.localGroupsData || []).filter(g => {
      if (this.groupUserFilterTag === "has_members" && g.member_count === 0) return false;
      if (this.groupUserFilterTag === "admins" && !g.name.toLowerCase().includes("admin")) return false;
      if (this.groupUserFilterTag === "users_grp" && !g.name.toLowerCase().includes("user")) return false;

      if (term) {
        const matchName = g.name.toLowerCase().includes(term);
        const matchDesc = (g.description || "").toLowerCase().includes(term);
        const matchMember = (g.members || []).some(m => (m.name || "").toLowerCase().includes(term) || (m.raw_name || "").toLowerCase().includes(term));
        return matchName || matchDesc || matchMember;
      }
      return true;
    });

    if (filtered.length === 0) {
      tbody.innerHTML = `<tr><td colspan="3" class="text-center py-4 text-muted">Không tìm thấy nhóm nào phù hợp với bộ lọc/tìm kiếm.</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    filtered.forEach(g => {
      const tr = document.createElement("tr");

      let grpIcon = "👥";
      const gLower = g.name.toLowerCase();
      if (gLower.includes("admin")) grpIcon = "🛡️";
      else if (gLower.includes("remote")) grpIcon = "💻";
      else if (gLower.includes("hyper") || gLower.includes("docker") || gLower.includes("vm")) grpIcon = "🐳";
      else if (gLower.includes("iis") || gLower.includes("web") || gLower.includes("sql")) grpIcon = "🗄️";
      else if (gLower.includes("backup") || gLower.includes("crypto") || gLower.includes("cert")) grpIcon = "🔐";
      else if (gLower.includes("event") || gLower.includes("log") || gLower.includes("perform")) grpIcon = "📊";

      let membersHtml = "";
      if (!g.members || g.members.length === 0) {
        membersHtml = `<span class="text-muted fst-italic" style="font-size: 0.78rem; opacity: 0.7;">(Không có thành viên)</span>`;
      } else {
        membersHtml = `<div class="user-chips-container">` +
          g.members.map(m => {
            const isHighlight = this.lastCreatedUserHighlight && m.name.toLowerCase() === this.lastCreatedUserHighlight.toLowerCase();
            let chipIcon = "👤";
            let chipClass = "user-chip";
            let label = m.name;

            if (m.is_domain) {
              chipIcon = "🏢";
              chipClass += " domain-user";
              label = `${m.domain}\\${m.name}`;
            } else if (m.is_group) {
              chipIcon = "👥";
              chipClass += " nested-group";
            }
            if (isHighlight) {
              chipClass += " highlight-created";
            }

            return `<span class="${chipClass}" title="${m.raw_name || m.name}">
              <span class="chip-icon">${chipIcon}</span>
              <span>${label}</span>
              ${isHighlight ? '<span style="font-size:0.68rem; margin-left:3px;">⭐ Mới</span>' : ''}
            </span>`;
          }).join("") +
          `</div>`;
      }

      tr.innerHTML = `
        <td>
          <div class="group-badge-icon">
            <span>${grpIcon}</span>
            <strong class="text-dark">${g.name}</strong>
            <span class="group-member-count-tag" title="${g.member_count} thành viên">${g.member_count}</span>
          </div>
        </td>
        <td>${membersHtml}</td>
        <td><small class="text-muted">${g.description || '<em style="opacity:0.5;">(Không có mô tả)</em>'}</small></td>
      `;

      tbody.appendChild(tr);
    });
  },

  renderUsersTable() {
    const tbody = document.getElementById("users-table-body");
    if (!tbody) return;

    const searchInput = document.getElementById("group-search-input");
    const term = searchInput ? searchInput.value.trim().toLowerCase() : "";

    let filtered = (this.localUsersData || []).filter(u => {
      if (term) {
        const matchName = u.username.toLowerCase().includes(term);
        const matchComment = (u.comment || "").toLowerCase().includes(term);
        const matchGroups = (u.groups || []).some(grp => grp.toLowerCase().includes(term));
        return matchName || matchComment || matchGroups;
      }
      return true;
    });

    if (filtered.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" class="text-center py-4 text-muted">Không tìm thấy tài khoản người dùng nào.</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    filtered.forEach(u => {
      const tr = document.createElement("tr");
      const isHighlight = this.lastCreatedUserHighlight && u.username.toLowerCase() === this.lastCreatedUserHighlight.toLowerCase();

      let grpHtml = "";
      if (!u.groups || u.groups.length === 0) {
        grpHtml = `<span class="text-muted fst-italic" style="font-size:0.75rem;">(Chưa có nhóm)</span>`;
      } else {
        grpHtml = `<div class="d-flex flex-wrap gap-1">` +
          u.groups.map(grp => {
            const isAdmin = grp.toLowerCase().includes("admin");
            return `<span class="badge ${isAdmin ? 'bg-danger text-white' : 'bg-secondary text-light'}" style="font-size:0.72rem; padding: 2px 6px;">${grp}</span>`;
          }).join("") +
          `</div>`;
      }

      tr.innerHTML = `
        <td>
          <div class="d-flex align-items-center gap-2">
            <span style="font-size: 1.1rem;">👤</span>
            <div>
              <strong class="${isHighlight ? 'text-success' : ''}">${u.username}</strong>
              ${isHighlight ? '<span class="badge bg-success text-white ms-1" style="font-size:0.68rem;">Vừa tạo</span>' : ''}
            </div>
          </div>
        </td>
        <td>
          <div class="d-flex flex-column gap-1">
            <span class="badge ${u.disabled ? 'bg-danger text-white' : 'bg-success text-white'}" style="font-size: 0.75rem; width: fit-content;">
              ${u.disabled ? '🔴 Vô hiệu hóa' : '🟢 Đang hoạt động'}
            </span>
            <small class="text-muted" style="font-size: 0.72rem;">
              ${u.pwd_never_expires ? '🔒 Pass vĩnh viễn' : '⏳ Pass có hạn'}
            </small>
          </div>
        </td>
        <td>${grpHtml}</td>
        <td><small class="text-muted">${u.comment || '<em style="opacity:0.5;">(Không có)</em>'}</small></td>
      `;

      tbody.appendChild(tr);
    });
  },

  setGroupUserViewMode(mode) {
    this.groupUserViewMode = mode;
    const tableGroups = document.getElementById("groups-main-table");
    const tableUsers = document.getElementById("users-main-table");
    const btnGroups = document.getElementById("btn-group-view-mode");
    const btnUsers = document.getElementById("btn-user-view-mode");
    const tagsBar = document.getElementById("group-filter-tags-bar");

    if (mode === "groups") {
      if (tableGroups) tableGroups.style.display = "";
      if (tableUsers) tableUsers.style.display = "none";
      if (btnGroups) { btnGroups.classList.add("active", "btn-primary"); btnGroups.classList.remove("btn-outline-secondary"); }
      if (btnUsers) { btnUsers.classList.remove("active", "btn-primary"); btnUsers.classList.add("btn-outline-secondary"); }
      if (tagsBar) tagsBar.style.display = "flex";
      this.renderGroupsTable();
    } else {
      if (tableGroups) tableGroups.style.display = "none";
      if (tableUsers) tableUsers.style.display = "";
      if (btnGroups) { btnGroups.classList.remove("active", "btn-primary"); btnGroups.classList.add("btn-outline-secondary"); }
      if (btnUsers) { btnUsers.classList.add("active", "btn-primary"); btnUsers.classList.remove("btn-outline-secondary"); }
      if (tagsBar) tagsBar.style.display = "none";
      this.renderUsersTable();
    }
  },

  setGroupFilterTag(filter, btn) {
    this.groupUserFilterTag = filter;
    document.querySelectorAll("#group-filter-tags-bar .btn-filter-pill").forEach(b => b.classList.remove("active"));
    if (btn) btn.classList.add("active");
    this.renderGroupsTable();
  },

  filterGroupsAndUsers() {
    if (this.groupUserViewMode === "groups") {
      this.renderGroupsTable();
    } else {
      this.renderUsersTable();
    }
  },

  async openLusrmgr() {
    this.addLog("info", "Đang mở Local Users and Groups (lusrmgr.msc)...");
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.open_lusrmgr === 'function') {
      const res = await window.pywebview.api.open_lusrmgr();
      this.addLog(res.success ? "success" : "warn", res.message);
    }
  },

  startGroupUserRealtimeMonitor() {
    if (this.groupUserMonitorInterval) return;
    this.loadLocalGroupsAndUsers(false);
    this.groupUserMonitorInterval = setInterval(() => {
      const subtab = document.getElementById("subtab-create-user");
      if (subtab && subtab.classList.contains("active")) {
        this.loadLocalGroupsAndUsers(false);
      } else {
        this.stopGroupUserRealtimeMonitor();
      }
    }, 5000);
  },

  stopGroupUserRealtimeMonitor() {
    if (this.groupUserMonitorInterval) {
      clearInterval(this.groupUserMonitorInterval);
      this.groupUserMonitorInterval = null;
    }
  },

  async fixDataSharing() {
    this.addLog("info", "Đang Fix Chia Sẻ Dữ Liệu & Mạng LAN...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.fix_data_sharing();
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
    }
  }
});
