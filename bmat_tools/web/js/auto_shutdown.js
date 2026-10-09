/**
 * IT Tool LTT 2026 - Auto Shutdown & Task Scheduler Module
 * Author: Lê Thế Tuấn | 0352 194 195 | https://lethetuanpc.blogspot.com | Telegram: https://t.me/lethetuanpc
 */

Object.assign(AppController.prototype, {
  shutdownInterval: null,
  shutdownMode: 'countdown',

  // Initialize or load scheduled shutdown tasks table
  async loadScheduledShutdownTasks() {
    const tbody = document.getElementById("scheduled-tasks-tbody");
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">Đang tải danh sách lịch hệ thống...</td></tr>`;

    let tasks = [];
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.get_scheduled_shutdown_tasks();
      if (res && res.success) {
        tasks = res.tasks || [];
      }
    } else {
      tasks = [];
    }

    if (!tasks || tasks.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">Chưa có lịch hẹn giờ tự động nào được tạo trong Task Scheduler.</td></tr>`;
      return;
    }

    const actionBadge = (act) => {
      switch (act) {
        case 'shutdown': return '<span class="badge bg-danger-subtle text-danger font-semibold">⏻ Tắt Máy</span>';
        case 'restart': return '<span class="badge bg-warning-subtle text-warning font-semibold">🔄 Restart</span>';
        case 'hibernate': return '<span class="badge bg-indigo-subtle text-indigo font-semibold">💤 Sleep</span>';
        case 'logoff': return '<span class="badge bg-slate-subtle text-slate font-semibold">🚪 Logoff</span>';
        case 'lock': return '<span class="badge bg-info-subtle text-info font-semibold">🔒 Lock</span>';
        default: return `<span class="badge bg-secondary">${act}</span>`;
      }
    };

    tbody.innerHTML = "";
    tasks.forEach(t => {
      const tr = document.createElement("tr");
      const safeTaskName = t.task_name.replace(/"/g, '&quot;');
      tr.innerHTML = `
        <td><strong style="color: #0f172a; font-size: 13px;">${t.display_name}</strong></td>
        <td>${actionBadge(t.action)}</td>
        <td><span class="text-muted" style="font-family: monospace; font-size: 11.5px;">${t.next_run || 'N/A'}</span></td>
        <td><span class="text-muted" style="font-family: monospace; font-size: 11.5px;">${t.last_run || 'N/A'}</span></td>
        <td>
          <span class="badge ${t.enabled ? 'bg-success-subtle text-success' : 'bg-secondary-subtle text-secondary'}" style="font-size: 11px; padding: 4px 8px;">
            ${t.enabled ? '🟢 Đang Bật' : '⚪ Đã Tắt'}
          </span>
        </td>
        <td style="text-align: center;">
          <div class="table-btn-group">
            <button class="btn ${t.enabled ? 'btn-slate-outline' : 'btn-emerald-outline'} btn-sm" onclick="app.toggleScheduledTask('${safeTaskName}', ${!t.enabled})" title="${t.enabled ? 'Tắt lịch' : 'Bật lịch'}">
              ${t.enabled ? '⏸️ Tắt' : '▶️ Bật'}
            </button>
            <button class="btn btn-sky-outline btn-sm" onclick="app.runScheduledTaskNow('${safeTaskName}')" title="Kích hoạt chạy ngay">
              ⚡ Chạy Ngay
            </button>
            <button class="btn btn-rose-outline btn-sm" onclick="app.deleteScheduledTask('${safeTaskName}')" title="Xóa lịch trình này">
              🗑️ Xóa
            </button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  },

  // Switch Quick Shutdown Mode (Countdown vs Specific Time)
  switchShutdownMode(mode) {
    const countdownGroup = document.getElementById("shutdown-countdown-group");
    const specificGroup = document.getElementById("shutdown-specific-group");
    const modeCountdownBtn = document.getElementById("btn-mode-countdown");
    const modeSpecificBtn = document.getElementById("btn-mode-specific");

    if (mode === "countdown") {
      if (countdownGroup) countdownGroup.style.display = "block";
      if (specificGroup) specificGroup.style.display = "none";
      if (modeCountdownBtn) {
        modeCountdownBtn.classList.add("btn-primary-gradient");
        modeCountdownBtn.classList.remove("btn-slate-light");
      }
      if (modeSpecificBtn) {
        modeSpecificBtn.classList.remove("btn-primary-gradient");
        modeSpecificBtn.classList.add("btn-slate-light");
      }
      this.shutdownMode = "countdown";
    } else {
      if (countdownGroup) countdownGroup.style.display = "none";
      if (specificGroup) specificGroup.style.display = "block";
      if (modeSpecificBtn) {
        modeSpecificBtn.classList.add("btn-primary-gradient");
        modeSpecificBtn.classList.remove("btn-slate-light");
      }
      if (modeCountdownBtn) {
        modeCountdownBtn.classList.remove("btn-primary-gradient");
        modeCountdownBtn.classList.add("btn-slate-light");
      }
      this.shutdownMode = "specific";
    }
  },

  // Toggle Weekly Days Container based on Frequency Selection
  onFreqChange() {
    const freq = document.getElementById("task-freq-select")?.value;
    const weeklyContainer = document.getElementById("task-weekly-days-container");
    const dateContainer = document.getElementById("task-date-container");
    if (weeklyContainer) {
      weeklyContainer.style.display = (freq === "weekly") ? "flex" : "none";
    }
    if (dateContainer) {
      dateContainer.style.display = (freq === "once") ? "block" : "none";
    }
  },

  // Set Preset Minutes
  setShutdownPreset(minutes) {
    const timerInput = document.getElementById("shutdown-timer-page");
    if (timerInput) {
      timerInput.value = minutes;
    }
    this.switchShutdownMode("countdown");
  },

  // Immediate Power Executions
  async executeImmediatePower(action) {
    const actionNames = {
      shutdown_now: 'Tắt máy ngay lập tức',
      restart_now: 'Khởi động lại ngay lập tức',
      sleep: 'Hibernate / Sleep máy',
      lock: 'Khóa màn hình (Lock)',
      logoff: 'Đăng xuất tài khoản (Logoff)'
    };

    const confirmMsg = `Bạn có chắc chắn muốn ${actionNames[action] || action}?`;
    if (action === 'shutdown_now' || action === 'restart_now') {
      if (!confirm(confirmMsg)) return;
    }

    this.addLog("info", `Đang thực thi: ${actionNames[action] || action}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.execute_immediate_power(action);
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
    } else {
      alert(`[Mock Mode] Executed ${action}`);
    }
  },

  // Run Quick Scheduled Timer
  async runAutoShutdown() {
    const action = document.getElementById("shutdown-action-page")?.value || "shutdown";
    const message = document.getElementById("shutdown-message-page")?.value || "";
    let minutes = 30;

    if (this.shutdownMode === "specific") {
      const timeVal = document.getElementById("shutdown-specific-time")?.value;
      if (!timeVal) {
        alert("Vui lòng chọn mốc giờ cụ thể (HH:MM)!");
        return;
      }
      const [h, m] = timeVal.split(":").map(Number);
      const now = new Date();
      let target = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m, 0);
      if (target <= now) {
        target.setDate(target.getDate() + 1); // Tomorrow
      }
      minutes = Math.round((target - now) / 60000);
      if (minutes < 1) minutes = 1;
    } else {
      const inputVal = document.getElementById("shutdown-timer-page")?.value;
      minutes = parseFloat(inputVal);
      if (isNaN(minutes) || minutes <= 0) {
        alert("Vui lòng nhập số phút đếm ngược hợp lệ (lớn hơn 0)!");
        return;
      }
    }

    this.addLog("info", `Đang đặt lịch Auto Shutdown: ${action} sau ${minutes} phút...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.set_auto_shutdown(action, minutes, message);
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
      if (res.success) {
        this.startFrontendCountdown(minutes, action);
      }
    } else {
      alert(`[Mock Mode] Đặt lịch ${action} sau ${minutes} phút`);
      this.startFrontendCountdown(minutes, action);
    }
  },

  // Cancel Quick Scheduled Timer
  async cancelAutoShutdown() {
    this.addLog("info", "Đang hủy lịch Auto Shutdown...");
    if (this.shutdownInterval) {
      clearInterval(this.shutdownInterval);
      this.shutdownInterval = null;
    }
    const timerWidget = document.getElementById("shutdown-timer-widget");
    if (timerWidget) timerWidget.style.display = "none";

    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.set_auto_shutdown("cancel", 0);
      this.addLog(res.success ? "success" : "error", res.message);
      alert("Đã hủy lịch Auto Shutdown!");
    } else {
      alert("[Mock Mode] Đã hủy lịch!");
    }
  },

  // Frontend Live Countdown Animation
  startFrontendCountdown(minutes, action) {
    if (this.shutdownInterval) clearInterval(this.shutdownInterval);
    const targetMs = Date.now() + minutes * 60 * 1000;
    const totalSecs = minutes * 60;

    const widget = document.getElementById("shutdown-timer-widget");
    const display = document.getElementById("shutdown-timer-display");
    const progressBar = document.getElementById("shutdown-timer-progress");
    const actionLabel = document.getElementById("shutdown-action-label");

    const labelMap = {
      shutdown: "TẮT MÁY (SHUTDOWN)",
      restart: "KHỞI ĐỘNG LẠI (RESTART)",
      hibernate: "SLEEP / HIBERNATE",
      logoff: "ĐĂNG XUẤT (LOGOFF)",
      lock: "KHÓA MÀN HÌNH (LOCK)"
    };

    if (widget) widget.style.display = "block";
    if (actionLabel) actionLabel.innerText = labelMap[action] || action.toUpperCase();

    const updateTimer = () => {
      const remainingMs = targetMs - Date.now();
      if (remainingMs <= 0) {
        if (display) display.innerText = "00:00:00";
        if (progressBar) progressBar.style.width = "0%";
        clearInterval(this.shutdownInterval);
        this.shutdownInterval = null;
        this.addLog("info", `Thời gian đếm ngược kết thúc! Hệ thống đã thực thi: ${action}`);
        return;
      }
      const remSecs = Math.floor(remainingMs / 1000);
      const h = Math.floor(remSecs / 3600);
      const m = Math.floor((remSecs % 3600) / 60);
      const s = remSecs % 60;
      const fmt = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;

      if (display) display.innerText = fmt;
      if (progressBar) {
        const pct = Math.max(0, Math.min(100, (remSecs / totalSecs) * 100));
        progressBar.style.width = `${pct}%`;
      }
    };

    updateTimer();
    this.shutdownInterval = setInterval(updateTimer, 1000);
  },

  // Task Scheduler Creation
  async createScheduledTask() {
    const name = document.getElementById("task-name-input")?.value;
    const action = document.getElementById("task-action-select")?.value;
    const freq = document.getElementById("task-freq-select")?.value;
    const timeStr = document.getElementById("task-time-input")?.value;
    const dateStr = document.getElementById("task-date-input")?.value || "";
    const message = document.getElementById("task-message-input")?.value || "";

    let days = [];
    if (freq === "weekly") {
      document.querySelectorAll(".task-day-checkbox:checked").forEach(cb => {
        days.push(cb.value);
      });
    }

    if (!name || !name.trim()) {
      alert("Vui lòng nhập tên lịch trình!");
      return;
    }
    if (!timeStr) {
      alert("Vui lòng nhập giờ chạy!");
      return;
    }

    this.addLog("info", `Đang tạo lịch trình mới: ${name}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.create_scheduled_shutdown_task(name, action, freq, timeStr, days, dateStr, message);
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
      if (res.success) {
        this.loadScheduledShutdownTasks();
        const nameInput = document.getElementById("task-name-input");
        if (nameInput) nameInput.value = "";
      }
    } else {
      alert(`[Mock Mode] Created task ${name}`);
      this.loadScheduledShutdownTasks();
    }
  },

  // Toggle Task (Enable / Disable)
  async toggleScheduledTask(taskName, enable) {
    this.addLog("info", `Đang ${enable ? 'bật' : 'tắt'} lịch: ${taskName}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.toggle_scheduled_shutdown_task(taskName, enable);
      this.addLog(res.success ? "success" : "error", res.message);
      this.loadScheduledShutdownTasks();
    }
  },

  // Run Task Now
  async runScheduledTaskNow(taskName) {
    if (!confirm(`Bạn có muốn kích hoạt chạy ngay lịch '${taskName.replace('ITTools_Shutdown_', '')}'?`)) return;
    this.addLog("info", `Đang kích hoạt lịch: ${taskName}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.run_scheduled_shutdown_task_now(taskName);
      this.addLog(res.success ? "success" : "error", res.message);
      this.loadScheduledShutdownTasks();
    }
  },

  // Delete Task
  async deleteScheduledTask(taskName) {
    if (!confirm(`Bạn có chắc muốn xóa lịch '${taskName.replace('ITTools_Shutdown_', '')}' khỏi hệ thống?`)) return;
    this.addLog("info", `Đang xóa lịch: ${taskName}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.delete_scheduled_shutdown_task(taskName);
      this.addLog(res.success ? "success" : "error", res.message);
      this.loadScheduledShutdownTasks();
    }
  },

  // ── SUBTAB SWITCHER ────────────────────────────────────────────────────────
  shutdownSubtab: 'scheduler',
  shutdownLogsCache: [],
  shutdownLogsFilter: 'all',
  shutdownLogsSearchQuery: '',
  shutdownLogsLimit: 10,
  shutdownLogsAutoRefreshTimer: null,
  shutdownLogsIsAutoRefreshing: false,

  switchShutdownSubtab(tab) {
    this.shutdownSubtab = tab;
    const btnScheduler = document.getElementById("btn-subtab-shutdown-scheduler");
    const btnLogs = document.getElementById("btn-subtab-shutdown-logs");
    const contentScheduler = document.getElementById("subtab-shutdown-scheduler-content");
    const contentLogs = document.getElementById("subtab-shutdown-logs-content");

    if (tab === 'scheduler') {
      if (btnScheduler) {
        btnScheduler.classList.add("btn-primary-gradient");
        btnScheduler.classList.remove("btn-slate-light");
      }
      if (btnLogs) {
        btnLogs.classList.remove("btn-primary-gradient");
        btnLogs.classList.add("btn-slate-light");
      }
      if (contentScheduler) contentScheduler.style.display = "block";
      if (contentLogs) contentLogs.style.display = "none";
    } else {
      if (btnScheduler) {
        btnScheduler.classList.remove("btn-primary-gradient");
        btnScheduler.classList.add("btn-slate-light");
      }
      if (btnLogs) {
        btnLogs.classList.add("btn-primary-gradient");
        btnLogs.classList.remove("btn-slate-light");
      }
      if (contentScheduler) contentScheduler.style.display = "none";
      if (contentLogs) contentLogs.style.display = "block";

      // Always trigger load when opening logs subtab
      this.loadShutdownLogs(!this.shutdownLogsCache || this.shutdownLogsCache.length === 0);
    }
  },

  // ── LOAD WINDOWS SHUTDOWN & CRASH EVENT LOGS (REAL-TIME) ────────────────────
  async loadShutdownLogs(showLoading = true) {
    const tbody = document.getElementById("shutdown-logs-tbody");
    if (showLoading && tbody) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" class="text-center py-5 text-muted">
            <div style="display: flex; flex-direction: column; align-items: center; gap: 8px;">
              <span style="font-size: 24px; animation: spin 1s linear infinite;">🔄</span>
              <span>Đang truy vấn nhật ký Windows Event Log thời gian thực (1074, 6008, 41)...</span>
            </div>
          </td>
        </tr>
      `;
    }

    const refreshBtn = document.getElementById("btn-refresh-shutdown-logs");
    if (refreshBtn) refreshBtn.disabled = true;

    try {
      let res = null;
      if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_shutdown_event_logs === 'function') {
        res = await window.pywebview.api.get_shutdown_event_logs(this.shutdownLogsLimit, "1074,6008,41");
      } else {
        // Fallback / mock data for browser preview
        res = {
          success: true,
          logs: [
            { id: 1074, time: '2026-10-09 13:28:36', friendly_time: '09/10/2026 13:28:36', relative_time: '15 phút trước', action_type: 'shutdown', action_label: 'Tắt máy (Shutdown)', user: 'BHBITIS\\thetuan.le', process: 'D:\\WinPE_Workspace\\Mount\\Windows\\System32\\Pecmd.exe', process_name: 'Pecmd.exe', reason: 'Legacy API shutdown', reason_code: '0x80070000', shutdown_type: 'shutdown', comment: '', machine: 'DNI-CNTT-PC005', level: 'Information', provider: 'User32', summary: 'BHBITIS\\thetuan.le (Pecmd.exe) - Legacy API shutdown', expert_note: 'Lệnh tắt máy chủ động bởi Pecmd.exe dưới quyền BHBITIS\\thetuan.le.', raw_message: 'The process D:\\WinPE_Workspace\\Mount\\Windows\\System32\\Pecmd.exe (DNI-CNTT-PC005) has initiated the shutdown of computer DNI-CNTT-PC005 on behalf of user BHBITIS\\thetuan.le for the following reason: Legacy API shutdown\r\n Reason Code: 0x80070000\r\n Shutdown Type: shutdown' },
            { id: 1074, time: '2026-10-08 14:30:00', friendly_time: '08/10/2026 14:30:00', relative_time: '1 ngày trước', action_type: 'restart', action_label: 'Khởi động lại (Restart)', user: 'BHBITIS\\thetuan.le', process: 'C:\\Windows\\SystemApps\\Microsoft.Windows.StartMenuExperienceHost_cw5n1h2txyewy\\StartMenuExperienceHost.exe', process_name: 'StartMenuExperienceHost.exe', reason: 'Other (Unplanned)', reason_code: '0x0', shutdown_type: 'restart', comment: '', machine: 'DNI-CNTT-PC005', level: 'Information', provider: 'User32', summary: 'BHBITIS\\thetuan.le (StartMenuExperienceHost.exe) - Other (Unplanned)', expert_note: 'Người dùng chọn Khởi động lại máy từ Menu Start của Windows.', raw_message: 'The process C:\\Windows\\SystemApps\\... has initiated the restart of computer on behalf of user BHBITIS\\thetuan.le...' },
            { id: 6008, time: '2026-09-10 07:24:36', friendly_time: '10/09/2026 07:24:36', relative_time: '29 ngày trước', action_type: 'unexpected_shutdown', action_label: 'Sập nguồn đột ngột', user: 'Hệ thống (System)', process: '', process_name: 'Phần cứng / Nguồn', reason: 'Thời điểm sập nguồn: 4:07:14 PM on 9/9/2026', reason_code: 'N/A', shutdown_type: 'unexpected', comment: '', machine: 'DNI-CNTT-PC005', level: 'Warning', provider: 'EventLog', summary: 'Hệ thống bị ngắt nguồn đột ngột (mất điện, rút phích cắm hoặc bấm giữ nút nguồn)', expert_note: 'Hệ điều hành bị ngắt điện đột ngột hoặc người dùng ấn giữ nút Power cưỡng bức.', raw_message: 'The previous system shutdown at 4:07:14 PM on 9/9/2026 was unexpected.' },
            { id: 41, time: '2026-09-10 07:22:28', friendly_time: '10/09/2026 07:22:28', relative_time: '29 ngày trước', action_type: 'kernel_power', action_label: 'Kernel-Power (Crash / Tắt máy không sạch)', user: 'Hệ thống (System)', process: '', process_name: 'Kernel-Power', reason: 'Reboot không qua quy trình tắt sạch', reason_code: '0x0', shutdown_type: 'crash', comment: '', machine: 'DNI-CNTT-PC005', level: 'Critical', provider: 'Microsoft-Windows-Kernel-Power', summary: 'Hệ thống khởi động lại sau khi bị mất nguồn hoặc crash BSOD', expert_note: 'Windows ghi nhận lỗi Kernel-Power nghiêm trọng do mất nguồn hoặc crash.', raw_message: 'The system has rebooted without cleanly shutting down first. This error could be caused if the system stopped responding, crashed, or lost power unexpectedly.' }
          ],
          stats: { total: 4, shutdown_count: 1, restart_count: 1, unexpected_count: 1, kernel_power_count: 1, last_event_time: '09/10/2026 13:28:36', last_event_label: 'Tắt máy (Shutdown)', query_time: new Date().toLocaleTimeString('vi-VN') }
        };
      }

      if (res && res.success) {
        this.shutdownLogsCache = res.logs || [];
        const stats = res.stats || {};

        // Update KPI Cards
        const lastActionEl = document.getElementById("stat-last-action");
        const lastTimeEl = document.getElementById("stat-last-time");
        if (lastActionEl) {
          lastActionEl.innerText = stats.last_event_label || (this.shutdownLogsCache[0] ? this.shutdownLogsCache[0].action_label : '--');
          lastActionEl.title = lastActionEl.innerText;
        }
        if (lastTimeEl) {
          lastTimeEl.innerText = stats.last_event_time || (this.shutdownLogsCache[0] ? this.shutdownLogsCache[0].friendly_time : '--');
        }

        const countShutdown = this.shutdownLogsCache.filter(x => x.action_type === 'shutdown' || x.action_type === 'poweroff').length;
        const countRestart = this.shutdownLogsCache.filter(x => x.action_type === 'restart').length;
        const countUnexpected = this.shutdownLogsCache.filter(x => x.id === 6008).length;
        const countKernel = this.shutdownLogsCache.filter(x => x.id === 41).length;

        const elShutdown = document.getElementById("stat-shutdown-count");
        if (elShutdown) elShutdown.innerText = countShutdown;
        const elRestart = document.getElementById("stat-restart-count");
        if (elRestart) elRestart.innerText = countRestart;
        const elUnexpected = document.getElementById("stat-unexpected-count");
        if (elUnexpected) elUnexpected.innerText = countUnexpected;
        const elKernel = document.getElementById("stat-kernel-power-count");
        if (elKernel) elKernel.innerText = countKernel;

        // Update Filter Count Badges
        const fcAll = document.getElementById("filter-count-all");
        if (fcAll) fcAll.innerText = this.shutdownLogsCache.length;
        const fcSd = document.getElementById("filter-count-shutdown");
        if (fcSd) fcSd.innerText = countShutdown;
        const fcRs = document.getElementById("filter-count-restart");
        if (fcRs) fcRs.innerText = countRestart;
        const fcUn = document.getElementById("filter-count-unexpected");
        if (fcUn) fcUn.innerText = countUnexpected;
        const fcKp = document.getElementById("filter-count-kernel");
        if (fcKp) fcKp.innerText = countKernel;

        // Update Real-Time Status Banner
        const now = new Date();
        const timeFmt = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')} - ${String(now.getDate()).padStart(2, '0')}/${String(now.getMonth()+1).padStart(2, '0')}/${now.getFullYear()}`;
        const updatedEl = document.getElementById("shutdown-logs-last-updated");
        if (updatedEl) updatedEl.innerText = stats.query_time || timeFmt;

        const totalEl = document.getElementById("shutdown-logs-total-count");
        if (totalEl) totalEl.innerText = this.shutdownLogsCache.length;

        this.renderShutdownLogsTable();
      } else {
        if (tbody) {
          tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger">Lỗi khi đọc nhật ký: ${res ? res.message : 'Không nhận được dữ liệu'}</td></tr>`;
        }
      }
    } catch (err) {
      console.error("loadShutdownLogs error:", err);
      if (tbody) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger">Lỗi ngoại lệ: ${err.message || err}</td></tr>`;
      }
    } finally {
      if (refreshBtn) refreshBtn.disabled = false;
    }
  },

  // ── RENDER FILTERED TABLE ──────────────────────────────────────────────────
  renderShutdownLogsTable() {
    const tbody = document.getElementById("shutdown-logs-tbody");
    if (!tbody) return;

    if (!this.shutdownLogsCache || this.shutdownLogsCache.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-5 text-muted">Không tìm thấy bản ghi sự kiện tắt máy hoặc sập nguồn nào trong hệ thống.</td></tr>`;
      const dispCountEl = document.getElementById("shutdown-logs-displayed-count");
      if (dispCountEl) dispCountEl.innerText = "0";
      return;
    }

    const filter = this.shutdownLogsFilter || 'all';
    const query = (this.shutdownLogsSearchQuery || '').toLowerCase().trim();

    let filtered = this.shutdownLogsCache.filter((item) => {
      // Filter by type
      if (filter === 'shutdown' && !(item.action_type === 'shutdown' || item.action_type === 'poweroff')) return false;
      if (filter === 'restart' && item.action_type !== 'restart') return false;
      if (filter === 'unexpected' && item.id !== 6008) return false;
      if (filter === 'kernel_power' && item.id !== 41) return false;

      // Filter by search query
      if (query) {
        const fullSearch = `${item.id} ${item.time} ${item.friendly_time} ${item.action_label} ${item.user} ${item.process} ${item.process_name} ${item.reason} ${item.reason_code} ${item.machine} ${item.expert_note}`.toLowerCase();
        if (!fullSearch.includes(query)) return false;
      }
      return true;
    });

    const dispCountEl = document.getElementById("shutdown-logs-displayed-count");
    if (dispCountEl) dispCountEl.innerText = filtered.length;

    if (filtered.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-5 text-muted">Không có bản ghi nào phù hợp với bộ lọc và từ khóa tìm kiếm "${query || filter}".</td></tr>`;
      return;
    }

    const getActionBadge = (item) => {
      if (item.id === 6008) {
        return `<span class="badge" style="background: #fef3c7; color: #b45309; border: 1px solid #fde68a; font-weight: 700; font-size: 11px; padding: 4px 8px; border-radius: 6px;">⚠️ Sập Nguồn [6008]</span>`;
      }
      if (item.id === 41) {
        return `<span class="badge" style="background: #ffe4e6; color: #be123c; border: 1px solid #fecdd3; font-weight: 700; font-size: 11px; padding: 4px 8px; border-radius: 6px;">🔴 Kernel-Power [41]</span>`;
      }
      if (item.action_type === 'restart') {
        return `<span class="badge" style="background: #dbeafe; color: #1d4ed8; border: 1px solid #bfdbfe; font-weight: 700; font-size: 11px; padding: 4px 8px; border-radius: 6px;">🔄 Khởi Động [1074]</span>`;
      }
      if (item.action_type === 'poweroff') {
        return `<span class="badge" style="background: #e0e7ff; color: #4338ca; border: 1px solid #c7d2fe; font-weight: 700; font-size: 11px; padding: 4px 8px; border-radius: 6px;">🔌 Tắt Nguồn [1074]</span>`;
      }
      return `<span class="badge" style="background: #d1fae5; color: #047857; border: 1px solid #a7f3d0; font-weight: 700; font-size: 11px; padding: 4px 8px; border-radius: 6px;">⏻ Tắt Máy [1074]</span>`;
    };

    tbody.innerHTML = "";
    filtered.forEach((item, index) => {
      const originalIndex = this.shutdownLogsCache.indexOf(item);
      const tr = document.createElement("tr");
      tr.style.transition = "background-color 0.15s";

      const procDisplay = item.process_name || (item.process ? item.process.split('\\').pop() : (item.id === 41 ? 'Kernel-Power' : (item.id === 6008 ? 'Phần cứng / Nguồn' : 'Hệ thống')));
      const userDisplay = item.user || (item.id === 1074 ? 'System' : 'Hệ thống');

      tr.innerHTML = `
        <td style="text-align: center; color: #94a3b8; font-weight: 600; font-size: 11.5px;">${index + 1}</td>
        <td>
          <div style="font-weight: 700; color: #0f172a; font-family: 'Consolas', monospace; font-size: 12px; letter-spacing: 0.3px;">
            ${item.friendly_time || item.time}
          </div>
          <div style="font-size: 11px; color: #64748b; margin-top: 2px;">
            🕒 ${item.relative_time || 'N/A'}
          </div>
        </td>
        <td>
          ${getActionBadge(item)}
        </td>
        <td>
          <div style="display: flex; align-items: center; gap: 6px;">
            <span style="font-size: 13px;">👤</span>
            <span style="font-weight: 600; color: #1e293b; font-size: 12px; word-break: break-all;">${userDisplay}</span>
          </div>
        </td>
        <td>
          <div style="display: inline-flex; align-items: center; gap: 5px; background: #f1f5f9; padding: 3px 8px; border-radius: 5px; border: 1px solid #e2e8f0; font-size: 11.5px; font-family: monospace; color: #334155;" title="${item.process || procDisplay}">
            <span>⚙️</span>
            <span style="max-width: 130px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${procDisplay}</span>
          </div>
        </td>
        <td>
          <div style="font-size: 12px; color: #1e293b; line-height: 1.4; max-width: 320px;">
            ${item.summary || item.reason || 'Bình thường'}
          </div>
        </td>
        <td style="text-align: center;">
          <button class="btn btn-sky-outline btn-sm" onclick="app.showShutdownLogDetail(${originalIndex})" style="padding: 4px 10px; font-size: 11.5px; white-space: nowrap;" title="Xem đầy đủ toàn văn log & phân tích">
            👁️ Chi Tiết
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  },

  // ── FILTER PILLS SWITCH ───────────────────────────────────────────────────
  filterShutdownLogs(type) {
    this.shutdownLogsFilter = type;
    const buttons = {
      'all': 'btn-filter-log-all',
      'shutdown': 'btn-filter-log-shutdown',
      'restart': 'btn-filter-log-restart',
      'unexpected': 'btn-filter-log-unexpected',
      'kernel_power': 'btn-filter-log-kernel'
    };

    Object.keys(buttons).forEach(k => {
      const btn = document.getElementById(buttons[k]);
      if (!btn) return;
      if (k === type) {
        btn.classList.add("btn-primary-gradient");
        btn.classList.remove("btn-slate-light");
      } else {
        btn.classList.remove("btn-primary-gradient");
        btn.classList.add("btn-slate-light");
      }
    });

    this.renderShutdownLogsTable();
  },

  // ── SEARCH LOGS ───────────────────────────────────────────────────────────
  onShutdownLogsSearch(query) {
    this.shutdownLogsSearchQuery = query;
    this.renderShutdownLogsTable();
  },

  // ── LIMIT CHANGE ──────────────────────────────────────────────────────────
  onShutdownLogsLimitChange(limit) {
    this.shutdownLogsLimit = parseInt(limit) || 10;
    this.loadShutdownLogs(true);
  },

  // ── AUTO REFRESH TOGGLE ───────────────────────────────────────────────────
  toggleShutdownLogsAutoRefresh() {
    const label = document.getElementById("autorefresh-status-label");
    const btn = document.getElementById("btn-autorefresh-shutdown-logs");

    if (this.shutdownLogsIsAutoRefreshing) {
      if (this.shutdownLogsAutoRefreshTimer) {
        clearInterval(this.shutdownLogsAutoRefreshTimer);
        this.shutdownLogsAutoRefreshTimer = null;
      }
      this.shutdownLogsIsAutoRefreshing = false;
      if (label) {
        label.innerText = "TẮT";
        label.style.color = "#64748b";
      }
      if (btn) {
        btn.classList.remove("btn-emerald-outline");
        btn.classList.add("btn-slate-light");
      }
      if (typeof this.showToast === 'function') this.showToast("info", "Đã tắt tự động cập nhật nhật ký.");
    } else {
      this.shutdownLogsIsAutoRefreshing = true;
      if (label) {
        label.innerText = "BẬT (30s)";
        label.style.color = "#10b981";
      }
      if (btn) {
        btn.classList.remove("btn-slate-light");
        btn.classList.add("btn-emerald-outline");
      }
      this.shutdownLogsAutoRefreshTimer = setInterval(() => {
        if (this.shutdownSubtab === 'logs') {
          this.loadShutdownLogs(false);
        }
      }, 30000);
      if (typeof this.showToast === 'function') this.showToast("success", "Đã bật tự động cập nhật nhật ký thời gian thực mỗi 30 giây.");
    }
  },

  // ── SHOW DETAIL MODAL ─────────────────────────────────────────────────────
  showShutdownLogDetail(index) {
    const item = this.shutdownLogsCache[index];
    if (!item) return;

    const modal = document.getElementById("shutdown-log-modal");
    if (!modal) return;

    // Set Header
    const iconEl = document.getElementById("modal-log-icon");
    const titleEl = document.getElementById("modal-log-title");
    const subEl = document.getElementById("modal-log-subtitle");

    if (item.id === 6008) {
      if (iconEl) iconEl.innerText = "⚠️";
      if (titleEl) titleEl.innerText = "Sự Kiện Sập Nguồn Đột Ngột (Dirty Shutdown)";
    } else if (item.id === 41) {
      if (iconEl) iconEl.innerText = "🔴";
      if (titleEl) titleEl.innerText = "Sự Kiện Kernel-Power Crash (Khởi Động Lại Không Sạch)";
    } else if (item.action_type === 'restart') {
      if (iconEl) iconEl.innerText = "🔄";
      if (titleEl) titleEl.innerText = "Sự Kiện Khởi Động Lại Hệ Thống (Clean Restart)";
    } else {
      if (iconEl) iconEl.innerText = "⏻";
      if (titleEl) titleEl.innerText = "Sự Kiện Tắt Máy Chủ Động (Clean Shutdown)";
    }
    if (subEl) subEl.innerText = `Event ID: ${item.id} | Nguồn: ${item.provider || 'System'}`;

    // Set Metadata
    const timeEl = document.getElementById("modal-log-time");
    if (timeEl) timeEl.innerText = item.friendly_time || item.time;

    const relEl = document.getElementById("modal-log-reltime");
    if (relEl) relEl.innerText = item.relative_time || 'N/A';

    const eidEl = document.getElementById("modal-log-eid");
    if (eidEl) {
      const levelColor = item.level === 'Critical' ? '#e11d48' : (item.level === 'Warning' ? '#d97706' : '#059669');
      eidEl.innerHTML = `<strong>${item.id}</strong> <span class="badge" style="background: #f1f5f9; color: ${levelColor}; border: 1px solid #cbd5e1; font-size: 11px; margin-left: 6px; padding: 2px 6px;">${item.level || 'Information'}</span>`;
    }

    const provEl = document.getElementById("modal-log-provider");
    if (provEl) provEl.innerText = item.provider || 'N/A';

    const userEl = document.getElementById("modal-log-user");
    if (userEl) userEl.innerText = item.user || (item.id === 1074 ? 'System' : 'Hệ thống');

    const machEl = document.getElementById("modal-log-machine");
    if (machEl) machEl.innerText = item.machine || window.location.hostname || 'Local PC';

    const procEl = document.getElementById("modal-log-process");
    if (procEl) procEl.innerText = item.process || item.process_name || 'Không có đường dẫn tiến trình (Kernel/Hardware/Power Loss)';

    const reasonEl = document.getElementById("modal-log-reason");
    if (reasonEl) reasonEl.innerText = item.reason || 'Bình thường';

    const codeEl = document.getElementById("modal-log-reasoncode");
    if (codeEl) codeEl.innerText = item.reason_code || (item.id === 6008 ? '0x6008 (Dirty)' : (item.id === 41 ? '0x0041 (Kernel Power)' : 'N/A'));

    const expertBox = document.getElementById("modal-log-expert-box");
    const expertNote = document.getElementById("modal-log-expert-note");
    if (expertNote) expertNote.innerText = item.expert_note || item.summary || 'Không có ghi chú thêm.';

    if (expertBox) {
      if (item.id === 41) {
        expertBox.style.background = "#fff1f2";
        expertBox.style.borderLeftColor = "#e11d48";
      } else if (item.id === 6008) {
        expertBox.style.background = "#fffbeb";
        expertBox.style.borderLeftColor = "#d97706";
      } else {
        expertBox.style.background = "#eff6ff";
        expertBox.style.borderLeftColor = "#3b82f6";
      }
    }

    const rawEl = document.getElementById("modal-log-rawmessage");
    if (rawEl) rawEl.value = item.raw_message || item.summary || '';

    modal.style.display = "flex";
  },

  // ── CLOSE DETAIL MODAL ────────────────────────────────────────────────────
  closeShutdownLogDetailModal() {
    const modal = document.getElementById("shutdown-log-modal");
    if (modal) modal.style.display = "none";
  },

  // ── COPY DETAIL RAW MESSAGE ───────────────────────────────────────────────
  copyShutdownLogDetail() {
    const rawEl = document.getElementById("modal-log-rawmessage");
    if (!rawEl || !rawEl.value) return;
    navigator.clipboard.writeText(rawEl.value).then(() => {
      if (typeof this.showToast === 'function') this.showToast("success", "Đã sao chép toàn văn thông điệp Windows Event Log vào Clipboard!");
      else alert("Đã sao chép vào Clipboard!");
    }).catch(err => {
      alert("Không thể sao chép: " + err);
    });
  },

  // ── COPY TABLE ────────────────────────────────────────────────────────────
  copyShutdownLogsTable() {
    if (!this.shutdownLogsCache || this.shutdownLogsCache.length === 0) {
      alert("Chưa có bản ghi nào để sao chép!");
      return;
    }

    let tsv = "STT\tThời Gian\tEvent ID\tHành Động\tNgười Dùng\tTiến Trình\tLý Do\tMã Reason Code\n";
    this.shutdownLogsCache.forEach((item, idx) => {
      tsv += `${idx + 1}\t${item.friendly_time || item.time}\t${item.id}\t${item.action_label}\t${item.user || ''}\t${item.process_name || ''}\t${item.reason || ''}\t${item.reason_code || ''}\n`;
    });

    navigator.clipboard.writeText(tsv).then(() => {
      if (typeof this.showToast === 'function') this.showToast("success", `Đã sao chép ${this.shutdownLogsCache.length} bản ghi nhật ký (dạng bảng Excel) vào Clipboard!`);
      else alert("Đã sao chép danh sách vào Clipboard!");
    }).catch(err => {
      alert("Lỗi sao chép: " + err);
    });
  },

  // ── EXPORT EXCEL / CSV FILE (DESKTOP OR BROWSER DOWNLOAD) ──────────────────
  async exportShutdownLogsFile(format = 'excel') {
    if (typeof this.showToast === 'function') {
      this.showToast("info", `Đang kết xuất báo cáo lịch sử tắt máy dạng ${format.toUpperCase()}...`);
    }

    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.export_shutdown_event_logs === 'function') {
      try {
        const res = await window.pywebview.api.export_shutdown_event_logs(this.shutdownLogsLimit || 100, "1074,6008,41", format);
        if (res && res.success) {
          if (typeof this.showToast === 'function') this.showToast("success", res.message);
          
          // Ask if user wants to open the file right away in Excel / WPS Office
          const openNow = confirm(`${res.message}\n\nBạn có muốn mở file báo cáo ngay bây giờ không?`);
          if (openNow && res.file_path && typeof window.pywebview.api.open_exported_file === 'function') {
            await window.pywebview.api.open_exported_file(res.file_path);
          }
        } else {
          alert("Lỗi xuất file: " + (res ? res.message : "Thất bại"));
        }
      } catch (err) {
        alert("Lỗi khi gọi API xuất file: " + err);
      }
    } else {
      // Fallback download for browser environment
      if (!this.shutdownLogsCache || this.shutdownLogsCache.length === 0) {
        alert("Chưa có dữ liệu để xuất file! Vui lòng bấm 'Làm Mới (Real-Time)' để tải dữ liệu trước.");
        return;
      }

      const ts = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);

      if (format === 'excel') {
        const html = this._generateExcelHtmlReport();
        const blob = new Blob([html], { type: 'application/vnd.ms-excel;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `Lich_Su_Tat_May_${ts}.xls`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        if (typeof this.showToast === 'function') this.showToast("success", "Đã tải file Excel báo cáo lịch sử tắt máy!");
      } else {
        let csvContent = "\uFEFFsep=,\r\n";
        csvContent += "STT,Thời Gian Ghi Nhận,Event ID,Mức Độ,Loại Hành Động,Người Dùng / Quyền,Tiến Trình Phát Lệnh,Lý Do Tắt Máy / Sự Cố,Mã Reason Code,Tên Máy Tính,Chẩn Đoán Kỹ Thuật (Ghi Chú IT),Chi Tiết Nhật Ký Gốc\r\n";
        this.shutdownLogsCache.forEach((item, idx) => {
          const cleanReason = (item.reason || '').replace(/[\r\n]+/g, ' | ').replace(/"/g, '""');
          const cleanNote = (item.expert_note || '').replace(/[\r\n]+/g, ' | ').replace(/"/g, '""');
          const cleanMsg = (item.raw_message || '').replace(/[\r\n]+/g, ' | ').replace(/"/g, '""');
          const row = [
            idx + 1,
            `"${item.friendly_time || item.time || ''}"`,
            item.id,
            `"${item.level || ''}"`,
            `"${(item.action_label || '').replace(/"/g, '""')}"`,
            `"${(item.user || 'Hệ thống (SYSTEM)').replace(/"/g, '""')}"`,
            `"${(item.process_name || item.process || '-').replace(/"/g, '""')}"`,
            `"${cleanReason}"`,
            `"${item.reason_code || '-'}"`,
            `"${item.machine || ''}"`,
            `"${cleanNote}"`,
            `"${cleanMsg}"`
          ];
          csvContent += row.join(",") + "\r\n";
        });

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `Lich_Su_Tat_May_${ts}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        if (typeof this.showToast === 'function') this.showToast("success", "Đã tải file CSV lịch sử tắt máy!");
      }
    }
  },

  _generateExcelHtmlReport() {
    const list = this.shutdownLogsCache || [];
    const now = new Date().toLocaleString('vi-VN');
    const comp = (list[0] && list[0].machine) ? list[0].machine : (navigator.userAgent || 'Local PC');
    const total = list.length;
    const shutdownCnt = list.filter(x => x.action_type === 'shutdown' || x.action_type === 'poweroff').length;
    const restartCnt = list.filter(x => x.action_type === 'restart').length;
    const unexpCnt = list.filter(x => x.id === 6008).length;
    const kpCnt = list.filter(x => x.id === 41).length;

    let rowsHtml = '';
    list.forEach((item, idx) => {
      const isCritical = (item.id === 41 || (item.level && item.level.includes('Critical')));
      const isWarning = (item.id === 6008 || (item.level && (item.level.includes('Warning') || item.level.includes('Error'))));
      const isRestart = (item.action_type === 'restart');

      const idBg = isCritical ? '#fee2e2' : (isWarning ? '#fef3c7' : (isRestart ? '#eff6ff' : '#ecfdf5'));
      const idColor = isCritical ? '#b91c1c' : (isWarning ? '#b45309' : (isRestart ? '#1d4ed8' : '#047857'));
      const rowBg = idx % 2 === 0 ? '#ffffff' : '#f8fafc';

      const cleanReason = (item.reason || '-').replace(/[\r\n]+/g, ' | ');
      const cleanNote = (item.expert_note || '-').replace(/[\r\n]+/g, ' | ');
      const cleanMsg = (item.raw_message || '-').replace(/[\r\n]+/g, ' | ');

      rowsHtml += `
        <tr style="background-color: ${rowBg};">
          <td style="text-align: center; border: 1px solid #cbd5e1; padding: 6px;">${idx + 1}</td>
          <td style="text-align: center; border: 1px solid #cbd5e1; padding: 6px;">${item.friendly_time || item.time || ''}</td>
          <td style="text-align: center; font-weight: bold; background-color: ${idBg}; color: ${idColor}; border: 1px solid #cbd5e1; padding: 6px;">${item.id}</td>
          <td style="text-align: center; font-weight: bold; background-color: ${idBg}; color: ${idColor}; border: 1px solid #cbd5e1; padding: 6px;">${item.level || ''}</td>
          <td style="font-weight: ${isCritical || isWarning ? 'bold' : 'normal'}; color: ${isCritical ? '#b91c1c' : (isWarning ? '#b45309' : '#0f172a')}; border: 1px solid #cbd5e1; padding: 6px;">${item.action_label || ''}</td>
          <td style="border: 1px solid #cbd5e1; padding: 6px;">${item.user || 'Hệ thống (SYSTEM)'}</td>
          <td style="border: 1px solid #cbd5e1; padding: 6px;">${item.process_name || item.process || '-'}</td>
          <td style="border: 1px solid #cbd5e1; padding: 6px;">${cleanReason}</td>
          <td style="text-align: center; border: 1px solid #cbd5e1; padding: 6px;">${item.reason_code || '-'}</td>
          <td style="border: 1px solid #cbd5e1; padding: 6px;">${item.machine || comp}</td>
          <td style="border: 1px solid #cbd5e1; padding: 6px;">${cleanNote}</td>
          <td style="border: 1px solid #cbd5e1; padding: 6px; font-size: 11px; color: #475569;">${cleanMsg}</td>
        </tr>
      `;
    });

    return `
      <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
      <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet><x:Name>Lịch Sử Tắt Máy</x:Name><x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions></x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]-->
        <style>
          table { border-collapse: collapse; width: 100%; font-family: 'Segoe UI', Arial, sans-serif; }
          th { background-color: #1d4ed8; color: #ffffff; font-weight: bold; border: 1px solid #cbd5e1; padding: 8px; font-size: 13px; text-align: center; }
          td { font-size: 12px; }
        </style>
      </head>
      <body>
        <table>
          <tr>
            <td colspan="12" style="background-color: #1e3a8a; color: #ffffff; font-size: 18px; font-weight: bold; text-align: center; padding: 14px;">
              BÁO CÁO CHI TIẾT LỊCH SỬ TẮT MÁY & KHỞI ĐỘNG HỆ THỐNG
            </td>
          </tr>
          <tr>
            <td colspan="12" style="background-color: #f1f5f9; color: #475569; font-size: 11.5px; text-align: center; font-style: italic; padding: 8px;">
              🖥️ Máy tính: ${comp} &nbsp;|&nbsp; ⏰ Thời gian xuất: ${now} &nbsp;|&nbsp; 📊 Tổng sự kiện: ${total} &nbsp;|&nbsp; 🛠️ IT Tool LTT - Biti's BMAT (Lê Thế Tuấn - 0352 194 195)
            </td>
          </tr>
          <tr><td colspan="12" style="height: 10px;"></td></tr>
          <tr style="background-color: #e2e8f0; font-weight: bold;">
            <td colspan="12" style="padding: 8px; border: 1px solid #cbd5e1; font-size: 13px; color: #0f172a;">
              📌 BẢNG TỔNG HỢP TRẠNG THÁI & CHỈ SỐ HOẠT ĐỘNG NGUỒN ĐIỆN
            </td>
          </tr>
          <tr style="text-align: center; font-weight: bold; font-size: 12px;">
            <td colspan="2" style="background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 8px;">Tổng sự kiện: ${total}</td>
            <td colspan="2" style="background-color: #ecfdf5; color: #065f46; border: 1px solid #cbd5e1; padding: 8px;">Tắt máy chủ động: ${shutdownCnt}</td>
            <td colspan="2" style="background-color: #eff6ff; color: #1d4ed8; border: 1px solid #cbd5e1; padding: 8px;">Khởi động lại: ${restartCnt}</td>
            <td colspan="3" style="background-color: ${unexpCnt > 0 ? '#fef3c7' : '#f8fafc'}; color: ${unexpCnt > 0 ? '#b45309' : '#475569'}; border: 1px solid #cbd5e1; padding: 8px;">Sập nguồn đột ngột (ID 6008): ${unexpCnt}</td>
            <td colspan="3" style="background-color: ${kpCnt > 0 ? '#fee2e2' : '#f8fafc'}; color: ${kpCnt > 0 ? '#b91c1c' : '#475569'}; border: 1px solid #cbd5e1; padding: 8px;">BSOD / Treo sập (ID 41): ${kpCnt}</td>
          </tr>
          <tr><td colspan="12" style="height: 10px;"></td></tr>
          <tr>
            <th style="width: 50px;">STT</th>
            <th style="width: 140px;">Thời Gian Ghi Nhận</th>
            <th style="width: 80px;">Event ID</th>
            <th style="width: 90px;">Mức Độ</th>
            <th style="width: 180px;">Loại Hành Động</th>
            <th style="width: 160px;">Người Dùng / Quyền</th>
            <th style="width: 150px;">Tiến Trình Phát Lệnh</th>
            <th style="width: 200px;">Lý Do Tắt Máy / Sự Cố</th>
            <th style="width: 110px;">Mã Reason Code</th>
            <th style="width: 150px;">Tên Máy Tính</th>
            <th style="width: 320px;">Chẩn Đoán Kỹ Thuật (Ghi Chú IT)</th>
            <th style="width: 380px;">Chi Tiết Nhật Ký Gốc</th>
          </tr>
          ${rowsHtml}
        </table>
      </body>
      </html>
    `;
  }
});

