/**
 * IT-Tools 2026 - Hardware Driver Backup & Restore Module
 */
Object.assign(AppController.prototype, {
  async loadInstalledDrivers() {
    const badgeEl = document.getElementById("driver-count-badge");
    const bodyEl = document.getElementById("driver-list-body");

    if (bodyEl) {
      bodyEl.innerHTML = `
        <tr>
          <td colspan="6" class="text-center py-4 text-muted">
            <span class="spinner-border spinner-border-sm text-primary"></span>
            Đang quét danh sách driver phần cứng trên máy tính...
          </td>
        </tr>
      `;
    }

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.get_installed_drivers();
        if (res && res.success) {
          this.allInstalledDrivers = res.drivers || [];
          if (badgeEl) badgeEl.innerText = `${res.total} Driver`;
          this.renderDriverList(this.allInstalledDrivers);
        } else {
          if (bodyEl) {
            bodyEl.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-danger">Lỗi quét Driver: ${res ? res.message : 'Unknown'}</td></tr>`;
          }
        }
      } catch (err) {
        console.error("Lỗi get_installed_drivers:", err);
      }
    } else {
      const mockDrivers = [
        { provider: "Intel", driver: "oem1.inf", class: "System devices", version: "1914.12.0.1256", date: "2024-05-10" },
        { provider: "Realtek", driver: "oem10.inf", class: "Network adapters", version: "10.60.615.2023", date: "2024-06-15" },
        { provider: "NVIDIA", driver: "oem15.inf", class: "Display adapters", version: "555.99", date: "2024-07-01" },
        { provider: "Realtek", driver: "oem12.inf", class: "Sound, video and game controllers", version: "6.0.9600.1", date: "2024-04-20" }
      ];
      this.allInstalledDrivers = mockDrivers;
      if (badgeEl) badgeEl.innerText = "4 Driver (MOCK)";
      this.renderDriverList(mockDrivers);
    }
  },

  renderDriverList(drivers) {
    const bodyEl = document.getElementById("driver-list-body");
    if (!bodyEl) return;

    if (!drivers || drivers.length === 0) {
      bodyEl.innerHTML = `
        <tr>
          <td colspan="6" class="text-center py-4 text-muted">
            Không tìm thấy file driver OEM nào trên hệ thống.
          </td>
        </tr>
      `;
      return;
    }

    bodyEl.innerHTML = drivers.map((item, index) => {
      const providerColor = item.provider && item.provider.toLowerCase().includes('intel') ? '#0284c7'
        : item.provider && item.provider.toLowerCase().includes('realtek') ? '#10b981'
        : item.provider && item.provider.toLowerCase().includes('nvidia') ? '#16a34a'
        : '#475569';

      return `
        <tr style="border-bottom: 1px solid #f1f5f9;">
          <td style="text-align: center; font-weight: 600; color: #64748b; padding: 8px;">${index + 1}</td>
          <td style="padding: 8px;">
            <strong style="color: ${providerColor}; font-size: 13px;">${item.provider}</strong>
          </td>
          <td style="padding: 8px; font-family: monospace; color: #0f172a; font-weight: 600;">
            ${item.driver}
          </td>
          <td style="padding: 8px; color: #334155;">
            <span class="badge" style="background: #f1f5f9; color: #475569; font-size: 11px;">${item.class}</span>
          </td>
          <td style="padding: 8px; font-family: monospace; color: #64748b; font-size: 12px;">
            ${item.version}
          </td>
          <td style="text-align: center; padding: 8px; color: #64748b; font-size: 12px;">
            ${item.date || '-'}
          </td>
        </tr>
      `;
    }).join('');
  },

  filterDriverList() {
    const query = document.getElementById("driver-search-input")?.value.toLowerCase().trim() || "";
    if (!this.allInstalledDrivers) return;

    if (!query) {
      this.renderDriverList(this.allInstalledDrivers);
      return;
    }

    const filtered = this.allInstalledDrivers.filter(item => 
      (item.provider && item.provider.toLowerCase().includes(query)) ||
      (item.driver && item.driver.toLowerCase().includes(query)) ||
      (item.class && item.class.toLowerCase().includes(query))
    );
    this.renderDriverList(filtered);
  },

  async backupDrivers() {
    this.addLog("info", "Đang mở hộp thoại chọn thư mục sao lưu Driver...");

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.start_backup_drivers_async();
        if (!res || !res.success) {
          if (res && res.message) this.addLog("warning", res.message);
          return;
        }
        this.addLog("info", res.message);
        if (res.path) {
          this.lastBackupDriverPath = res.path;
        }
        this.showDriverProgressDrawer("backup");
        this.startDriverProgressPolling();
      } catch (err) {
        alert(`Lỗi khởi tạo sao lưu Driver: ${err.message}`);
      }
    } else {
      alert("[MOCK] Đã sao lưu thành công toàn bộ Driver hệ thống!");
    }
  },

  async restoreDrivers() {
    this.addLog("info", "Đang mở hộp thoại chọn thư mục phục hồi Driver...");

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.start_restore_drivers_async();
        if (!res || !res.success) {
          if (res && res.message) this.addLog("warning", res.message);
          return;
        }
        this.addLog("info", res.message);
        this.showDriverProgressDrawer("restore");
        this.startDriverProgressPolling();
      } catch (err) {
        alert(`Lỗi khởi tạo phục hồi Driver: ${err.message}`);
      }
    } else {
      alert("[MOCK] Đã nạp & phục hồi thành công toàn bộ Driver!");
    }
  },

  showDriverProgressDrawer(mode) {
    const drawer = document.getElementById("driver-progress-drawer");
    const titleEl = document.getElementById("driver-drawer-title");
    const badgeEl = document.getElementById("driver-drawer-badge");
    const msgEl = document.getElementById("driver-drawer-msg");
    const countEl = document.getElementById("driver-drawer-count");
    const barEl = document.getElementById("driver-drawer-bar");
    const detailsEl = document.getElementById("driver-drawer-details");
    const closeBtn = document.getElementById("driver-drawer-close");
    const btnBackup = document.getElementById("btn-backup-drivers");
    const btnRestore = document.getElementById("btn-restore-drivers");

    if (drawer) drawer.style.display = "block";
    if (closeBtn) closeBtn.style.display = "none";
    if (btnBackup) btnBackup.disabled = true;
    if (btnRestore) btnRestore.disabled = true;

    if (mode === "backup") {
      if (titleEl) titleEl.innerHTML = `<span class="spinner-border spinner-border-sm" style="width: 16px; height: 16px; border: 2px solid #0284c7; border-right-color: transparent; border-radius: 50%; display: inline-block; animation: spin 0.75s linear infinite;"></span> ⚡ Đang sao lưu Driver hệ thống...`;
      if (badgeEl) { badgeEl.innerText = "Đang Sao Lưu"; badgeEl.style.background = "#e0f2fe"; badgeEl.style.color = "#0369a1"; }
      if (msgEl) msgEl.innerText = "Đang trích xuất toàn bộ driver thiết bị ra thư mục...";
    } else {
      if (titleEl) titleEl.innerHTML = `<span class="spinner-border spinner-border-sm" style="width: 16px; height: 16px; border: 2px solid #16a34a; border-right-color: transparent; border-radius: 50%; display: inline-block; animation: spin 0.75s linear infinite;"></span> ⚡ Đang phục hồi & nạp Driver...`;
      if (badgeEl) { badgeEl.innerText = "Đang Nạp Driver"; badgeEl.style.background = "#dcfce7"; badgeEl.style.color = "#15803d"; }
      if (msgEl) msgEl.innerText = "Đang nạp bộ cài driver vào Windows mới...";
    }

    if (barEl) barEl.style.width = "0%";
    if (countEl) countEl.innerText = "0 / 0 Driver (0%)";
    if (detailsEl) detailsEl.innerText = "Vui lòng chờ trong giây lát, tiến trình đang chạy...";
  },

  startDriverProgressPolling() {
    if (this._driverProgressTimer) {
      clearInterval(this._driverProgressTimer);
    }

    this._driverProgressTimer = setInterval(async () => {
      if (!window.pywebview || !window.pywebview.api) return;

      try {
        const prog = await window.pywebview.api.get_driver_progress();
        if (!prog) return;

        const titleEl = document.getElementById("driver-drawer-title");
        const badgeEl = document.getElementById("driver-drawer-badge");
        const msgEl = document.getElementById("driver-drawer-msg");
        const countEl = document.getElementById("driver-drawer-count");
        const barEl = document.getElementById("driver-drawer-bar");
        const detailsEl = document.getElementById("driver-drawer-details");
        const closeBtn = document.getElementById("driver-drawer-close");
        const btnBackup = document.getElementById("btn-backup-drivers");
        const btnRestore = document.getElementById("btn-restore-drivers");

        const pct = prog.percentage || 0;
        const curr = prog.current || 0;
        const total = prog.total || 0;
        const modeLabel = prog.mode === "backup" ? "Sao lưu" : "Phục hồi";

        if (barEl) barEl.style.width = `${pct}%`;
        if (badgeEl) badgeEl.innerText = `${pct}%`;
        if (countEl) countEl.innerText = `${curr} / ${total} Driver (${pct}%)`;
        if (msgEl && prog.message) msgEl.innerText = prog.message;
        if (detailsEl) detailsEl.innerText = `Thư mục làm việc: ${prog.path || 'Đang xử lý...'}`;

        if (prog.status === "completed") {
          clearInterval(this._driverProgressTimer);
          this._driverProgressTimer = null;

          if (barEl) barEl.style.width = "100%";
          if (badgeEl) { badgeEl.innerText = "Hoàn Tất 100%"; badgeEl.style.background = "#dcfce7"; badgeEl.style.color = "#15803d"; }
          if (titleEl) titleEl.innerHTML = `✅ Quy trình ${modeLabel} Driver Đã Hoàn Thành!`;
          if (closeBtn) closeBtn.style.display = "inline-block";
          if (btnBackup) btnBackup.disabled = false;
          if (btnRestore) btnRestore.disabled = false;

          this.addLog("success", prog.message || `Hoàn thành quy trình ${modeLabel} driver!`);
          alert(prog.message || `Hoàn tất ${modeLabel} Driver!`);
        } else if (prog.status === "error") {
          clearInterval(this._driverProgressTimer);
          this._driverProgressTimer = null;

          if (badgeEl) { badgeEl.innerText = "Lỗi!"; badgeEl.style.background = "#fee2e2"; badgeEl.style.color = "#b91c1c"; }
          if (titleEl) titleEl.innerHTML = `❌ Lỗi trong quy trình ${modeLabel} Driver`;
          if (closeBtn) closeBtn.style.display = "inline-block";
          if (btnBackup) btnBackup.disabled = false;
          if (btnRestore) btnRestore.disabled = false;

          this.addLog("error", prog.message || "Đã xảy ra lỗi trong quá trình thực thi driver.");
          alert(prog.message || "Đã xảy ra lỗi trong quá trình thực thi driver.");
        }
      } catch (err) {
        console.error("Lỗi polling driver progress:", err);
      }
    }, 400);
  },

  closeDriverProgressDrawer() {
    const drawer = document.getElementById("driver-progress-drawer");
    if (drawer) drawer.style.display = "none";
    if (this._driverProgressTimer) {
      clearInterval(this._driverProgressTimer);
      this._driverProgressTimer = null;
    }
  },

  async openDriverFolder() {
    if (window.pywebview && window.pywebview.api) {
      try {
        await window.pywebview.api.open_folder_explorer(this.lastBackupDriverPath || "C:\\Driver_Backup");
      } catch (err) {
        console.error("Lỗi mở thư mục:", err);
      }
    }
  }
});
