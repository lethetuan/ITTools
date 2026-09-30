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
  }
});
