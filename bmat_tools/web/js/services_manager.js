/**
 * IT-Tools 2026 - Windows Services Manager Module
 */
Object.assign(AppController.prototype, {
  async loadServices() {
    const badgeEl = document.getElementById("services-count-badge");
    const bodyEl = document.getElementById("services-list-body");

    if (bodyEl) {
      bodyEl.innerHTML = `
        <tr>
          <td colspan="6" class="text-center py-4 text-muted">
            <span class="spinner-border spinner-border-sm text-primary"></span>
            Đang quét danh sách các dịch vụ Windows...
          </td>
        </tr>
      `;
    }

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.get_windows_services();
        if (res && res.success) {
          this.allServices = res.services || [];
          if (badgeEl) badgeEl.innerText = `${res.total} Services`;
          this.renderServicesList(this.allServices);
        } else {
          if (bodyEl) {
            bodyEl.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-danger">Lỗi quét Services: ${res ? res.message : 'Unknown'}</td></tr>`;
          }
        }
      } catch (err) {
        console.error("Lỗi get_windows_services:", err);
      }
    } else {
      const mockServices = [
        { name: "Spooler", display: "Print Spooler", status: "Running", start_type: "Automatic" },
        { name: "wuauserv", display: "Windows Update", status: "Stopped", start_type: "Manual" },
        { name: "WinDefend", display: "Microsoft Defender Antivirus Service", status: "Running", start_type: "Automatic" },
        { name: "LanmanServer", display: "Server", status: "Running", start_type: "Automatic" },
        { name: "RemoteRegistry", display: "Remote Registry", status: "Stopped", start_type: "Disabled" }
      ];
      this.allServices = mockServices;
      if (badgeEl) badgeEl.innerText = "5 Services (MOCK)";
      this.renderServicesList(mockServices);
    }
  },

  renderServicesList(services) {
    const bodyEl = document.getElementById("services-list-body");
    if (!bodyEl) return;

    if (!services || services.length === 0) {
      bodyEl.innerHTML = `
        <tr>
          <td colspan="6" class="text-center py-4 text-muted">
            Không tìm thấy dịch vụ nào phù hợp với bộ lọc.
          </td>
        </tr>
      `;
      return;
    }

    bodyEl.innerHTML = services.map((item, index) => {
      const isRunning = (item.status && item.status.toLowerCase() === 'running');
      const statusBadge = isRunning
        ? `<span class="badge" style="background:#dcfce7; color:#15803d; font-weight:700; font-size:11px; padding:3px 8px; border-radius:12px;">🟢 Running</span>`
        : `<span class="badge" style="background:#fef2f2; color:#b91c1c; font-size:11px; padding:3px 8px; border-radius:12px;">🔴 Stopped</span>`;

      const startType = item.start_type || 'Manual';

      return `
        <tr style="border-bottom: 1px solid #f1f5f9;">
          <td style="text-align: center; font-weight: 600; color: #64748b; padding: 8px;">${index + 1}</td>
          <td style="padding: 8px;">
            <strong style="font-family: monospace; color: #0284c7; font-size: 12.5px;">${item.name}</strong>
          </td>
          <td style="padding: 8px; color: #1e293b; font-weight: 600; font-size: 13px;">
            ${item.display || item.name}
          </td>
          <td style="text-align: center; padding: 8px;">
            ${statusBadge}
          </td>
          <td style="text-align: center; padding: 8px;">
            <select class="form-control" onchange="app.changeServiceStartup('${item.name}', this)" style="padding: 3px 6px; font-size: 12px; border-radius: 6px; border: 1px solid #cbd5e1; width: 130px; margin: 0 auto; display: inline-block;">
              <option value="Automatic" ${startType.toLowerCase().includes('auto') ? 'selected' : ''}>⚡ Automatic</option>
              <option value="Manual" ${startType.toLowerCase().includes('manual') || startType.toLowerCase().includes('demand') ? 'selected' : ''}>✋ Manual</option>
              <option value="Disabled" ${startType.toLowerCase().includes('disabled') ? 'selected' : ''}>🚫 Disabled</option>
            </select>
          </td>
          <td style="text-align: right; padding: 8px;">
            <div style="display: flex; gap: 4px; justify-content: flex-end;">
              ${!isRunning ? `
                <button class="btn btn-success-solid btn-sm" onclick="app.manageService('${item.name}', 'start')" title="Bật dịch vụ" style="padding: 2px 8px; font-size: 11px;">
                  ▶ Start
                </button>
              ` : `
                <button class="btn btn-danger-solid btn-sm" onclick="app.manageService('${item.name}', 'stop')" title="Tắt dịch vụ" style="padding: 2px 8px; font-size: 11px;">
                  ⏹ Stop
                </button>
              `}
              <button class="btn btn-sky-outline btn-sm" onclick="app.manageService('${item.name}', 'restart')" title="Restart dịch vụ" style="padding: 2px 8px; font-size: 11px;">
                🔄 Restart
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  },

  searchServices() {
    const query = document.getElementById("services-search-input")?.value.toLowerCase().trim() || "";
    if (!this.allServices) return;

    if (!query) {
      this.renderServicesList(this.allServices);
      return;
    }

    const filtered = this.allServices.filter(s =>
      (s.name && s.name.toLowerCase().includes(query)) ||
      (s.display && s.display.toLowerCase().includes(query)) ||
      (s.status && s.status.toLowerCase().includes(query)) ||
      (s.start_type && s.start_type.toLowerCase().includes(query))
    );
    this.renderServicesList(filtered);
  },

  filterServicesCategory(category, btnEl) {
    if (btnEl) {
      btnEl.parentElement.querySelectorAll(".btn").forEach(b => {
        b.classList.remove("btn-primary");
        b.classList.add("btn-slate-light");
      });
      btnEl.classList.remove("btn-slate-light");
      btnEl.classList.add("btn-primary");
    }

    if (!this.allServices) return;

    if (category === 'all') {
      this.renderServicesList(this.allServices);
    } else if (category === 'running') {
      this.renderServicesList(this.allServices.filter(s => s.status && s.status.toLowerCase() === 'running'));
    } else if (category === 'stopped') {
      this.renderServicesList(this.allServices.filter(s => !s.status || s.status.toLowerCase() !== 'running'));
    } else if (category === 'auto') {
      this.renderServicesList(this.allServices.filter(s => s.start_type && s.start_type.toLowerCase().includes('auto')));
    }
  },

  async manageService(serviceName, action) {
    this.addLog("info", `Đang thực hiện ${action} trên dịch vụ '${serviceName}'...`);

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.manage_windows_service(serviceName, action);
        this.addLog(res.success ? "success" : "error", res.message);
        alert(res.message);
        this.loadServices();
      } catch (err) {
        alert(`Lỗi quản lý dịch vụ: ${err.message}`);
      }
    } else {
      alert(`[MOCK] Đã thực hiện ${action} trên dịch vụ '${serviceName}'!`);
      this.loadServices();
    }
  },

  async changeServiceStartup(serviceName, selectEl) {
    const startupType = selectEl.value;
    this.addLog("info", `Đang đổi kiểu khởi động '${serviceName}' sang ${startupType}...`);

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.set_service_startup_type(serviceName, startupType);
        this.addLog(res.success ? "success" : "error", res.message);
        alert(res.message);
        this.loadServices();
      } catch (err) {
        alert(`Lỗi đổi kiểu khởi động: ${err.message}`);
      }
    } else {
      alert(`[MOCK] Đã đổi kiểu khởi động '${serviceName}' sang ${startupType}!`);
    }
  },

  async openServicesMsc() {
    if (window.pywebview && window.pywebview.api) {
      try {
        await window.pywebview.api.open_services_msc();
      } catch (err) {
        console.error("Lỗi mở services.msc:", err);
      }
    } else {
      alert("[MOCK] Đã mở Services.msc!");
    }
  }
});
