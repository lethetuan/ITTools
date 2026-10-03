/**
 * IT Tool LTT 2026 Modern Application Logic - Core Controller
 * Author: Lê Thế Tuấn | 0352 194 195 | https://lethetuanpc.blogspot.com | Telegram: https://t.me/lethetuanpc
 */

class AppController {
  constructor() {
    this.currentZoom = 100;
    this.selectedPrinter = null;
    this.selectedCredTarget = null;
    this.installedApps = [];
    this.filteredInstalledApps = [];
    this.currentUninstallCategory = 'all';
    this.currentWizApp = null;
    this.bitlockerDrives = [];
    this.blPollInterval = null;
    this.activeBLDrive = null;
    this.networkAdaptersData = null;
    this.lastScanResults = [];
    this.init();
  }

  init() {
    this.bindEvents();
    this.startClock();
    this.updateZoomUI();
    this.checkPyWebViewApi();
  }

  checkPyWebViewApi() {
    let checkCount = 0;
    const interval = setInterval(() => {
      checkCount++;
      if (window.pywebview && window.pywebview.api) {
        clearInterval(interval);
        this.onApiReady();
      } else if (checkCount > 10) {
        clearInterval(interval);
        console.warn("PyWebView API not detected, running in mock/web mode.");
        if (typeof this.scanPrinters === 'function') this.scanPrinters();
        if (typeof this.scanCredentials === 'function') this.scanCredentials();
      }
    }, 200);
  }

  onApiReady() {
    this.addLog("info", "Đã kết nối thành công với Python Backend API.");
    // Auto-detect currently active tab and refresh its live data immediately
    const activeNav = document.querySelector(".nav-item.active");
    const activeTabId = activeNav ? activeNav.getAttribute("data-tab") : "tab-printer-fix";
    this.currentActiveTabId = activeTabId;
    this.refreshTabData(activeTabId);
    this.loadAutostartStatus();
  }

  /**
   * Refreshes real-time system data automatically for whichever tab the user enters.
   * No manual "Refresh" button needed.
   */
  async refreshTabData(tabId) {
    if (!tabId) return;

    try {
      switch (tabId) {
        case "tab-computer-info":
          if (typeof this.startRealtimeMonitoring === 'function') this.startRealtimeMonitoring();
          if (typeof this.loadComputerInfo === 'function') this.loadComputerInfo();
          break;

        case "tab-test-computer":
          if (window.testComputer && typeof window.testComputer.onTabActivated === 'function') {
            window.testComputer.onTabActivated();
          }
          break;

        case "tab-auto-win":
        case "tab-win-update":
          if (typeof this.loadWinUpdateStatus === 'function') await this.loadWinUpdateStatus();
          break;

        case "tab-startup":
          if (typeof this.loadStartupEntries === 'function') await this.loadStartupEntries();
          if (typeof this.loadAutostartStatus === 'function') await this.loadAutostartStatus();
          break;

        case "tab-uninstall":
          if (typeof this.loadInstalledApps === 'function') await this.loadInstalledApps();
          break;

        case "tab-bitlocker":
          if (typeof this.loadBitlockerDrives === 'function') await this.loadBitlockerDrives();
          break;

        case "tab-printer-fix":
          // Refresh printer list, credentials, and local groups & users automatically
          if (typeof this.scanPrinters === 'function') await this.scanPrinters();
          if (typeof this.scanCredentials === 'function') await this.scanCredentials();
          if (typeof this.loadLocalGroupsAndUsers === 'function') await this.loadLocalGroupsAndUsers();
          break;

        case "tab-ip-manager":
          if (typeof this.loadNetworkAdapters === 'function') await this.loadNetworkAdapters();
          if (typeof this.loadIpv6Status === 'function') await this.loadIpv6Status();
          break;

        case "tab-ip-scanner":
          if (typeof this.loadIpScannerDefaults === 'function') await this.loadIpScannerDefaults();
          break;

        case "tab-firewall":
          if (typeof this.loadFirewallStatus === 'function') await this.loadFirewallStatus();
          break;

        case "tab-server-tools":
          if (typeof this.loadServerTools === 'function') await this.loadServerTools();
          if (typeof this.loadNicTeams === 'function') await this.loadNicTeams();
          break;

        case "tab-zoom-screen":
          if (window.zoomScreen && typeof window.zoomScreen.loadStatus === 'function') {
            await window.zoomScreen.loadStatus();
          } else if (typeof this.loadZoomScreenStatus === 'function') {
            await this.loadZoomScreenStatus();
          }
          break;

        case "tab-auto-shutdown":
          if (typeof this.loadScheduledShutdownTasks === 'function') await this.loadScheduledShutdownTasks();
          break;

        case "tab-hosts":
          if (typeof this.loadHosts === 'function') await this.loadHosts();
          break;

        case "tab-sendto":
          if (typeof this.loadSendToEntries === 'function') await this.loadSendToEntries();
          break;

        case "tab-classic-menu":
          if (typeof this.loadClassicMenuStatus === 'function') await this.loadClassicMenuStatus();
          break;

        case "tab-desktop-icon":
          if (typeof this.loadDesktopIconSettings === 'function') await this.loadDesktopIconSettings();
          break;

        case "tab-datetime":
          if (typeof this.loadDateTimeInfo === 'function') await this.loadDateTimeInfo();
          break;

        case "tab-boot-manager":
          if (typeof this.loadBootEntries === 'function') await this.loadBootEntries();
          break;

        case "tab-services":
          if (typeof this.loadServices === 'function') await this.loadServices();
          if (typeof this.startServicesRealtimeMonitor === 'function') this.startServicesRealtimeMonitor();
          break;

        case "tab-folder-size":
          if (typeof this.loadSystemDrives === 'function') await this.loadSystemDrives();
          break;

        case "tab-currency":
          if (typeof this.loadCurrencyRates === 'function') await this.loadCurrencyRates();
          break;

        case "tab-other-tweaks":
          if (typeof this.loadSystemTweaksStatus === 'function') await this.loadSystemTweaksStatus();
          break;

        case "tab-office":
          if (typeof this.checkExistingOfficeInstall === 'function') await this.checkExistingOfficeInstall();
          break;

        case "tab-activation":
          if (typeof this.runWinCheckAudit === 'function') await this.runWinCheckAudit();
          break;

        case "tab-backup-driver":
          if (typeof this.loadInstalledDrivers === 'function') await this.loadInstalledDrivers();
          break;

        case "tab-browser-backup":
          if (typeof this.loadBrowserBackupInfo === 'function') await this.loadBrowserBackupInfo();
          break;

        case "tab-free-software":
          if (typeof this.loadSoftwareCatalog === 'function') await this.loadSoftwareCatalog();
          break;

        default:
          break;
      }
    } catch (tabErr) {
      console.error(`Lỗi cập nhật thời gian thực cho tab ${tabId}:`, tabErr);
    }
  }

  bindEvents() {
    // Navigation Tabs - Automatic Real-Time Data Refresh on Tab Access
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
      item.addEventListener("click", (e) => {
        try {
          if (e) e.preventDefault();
          if (document.activeElement && typeof document.activeElement.blur === 'function') {
            document.activeElement.blur();
          }

          const tabId = item.getAttribute("data-tab");
          const icon = item.querySelector(".nav-icon")?.innerText || "";
          const label = item.querySelector(".nav-label")?.innerText || "";

          // Clean up previous tab if switching away
          if (this.currentActiveTabId && this.currentActiveTabId !== tabId) {
            if (this.currentActiveTabId === "tab-computer-info" && typeof this.stopRealtimeMonitoring === 'function') {
              this.stopRealtimeMonitoring();
            }
            if (this.currentActiveTabId === "tab-test-computer" && window.testComputer && typeof window.testComputer.onTabDeactivated === 'function') {
              window.testComputer.onTabDeactivated();
            }
            if (this.currentActiveTabId === "tab-printer-fix" && typeof this.stopGroupUserRealtimeMonitor === 'function') {
              this.stopGroupUserRealtimeMonitor();
            }
            if (this.currentActiveTabId === "tab-services" && typeof this.stopServicesRealtimeMonitor === 'function') {
              this.stopServicesRealtimeMonitor();
            }
          }
          this.currentActiveTabId = tabId;

          navItems.forEach(n => n.classList.remove("active"));
          item.classList.add("active");

          document.querySelectorAll(".page-section").forEach(sec => sec.classList.remove("active"));
          const targetPage = document.getElementById(tabId);
          if (targetPage) {
            targetPage.classList.add("active");
          }

          const iconEl = document.getElementById("current-tab-icon");
          const titleEl = document.getElementById("current-tab-title");
          if (iconEl) iconEl.innerText = icon;
          if (titleEl) titleEl.innerText = label;

          // Automatically load and reflect accurate real-time PC state
          this.refreshTabData(tabId);
        } catch (err) {
          console.error("Lỗi chuyển tab chính:", err);
        }
      });
    });

    // Auto-refresh the active tab when the window regains focus from other applications
    window.addEventListener("focus", () => {
      if (this.currentActiveTabId) {
        this.refreshTabData(this.currentActiveTabId);
      }
    });

    // Sub-Tabs handler (scoped per parent section)
    const subtabBtns = document.querySelectorAll(".subtab-btn");
    subtabBtns.forEach(btn => {
      btn.addEventListener("click", (e) => {
        try {
          if (e) e.preventDefault();
          if (document.activeElement && typeof document.activeElement.blur === 'function') {
            document.activeElement.blur();
          }

          const subtabId = btn.getAttribute("data-subtab");
          const section = btn.closest(".page-section") || document;

          section.querySelectorAll(".subtab-btn").forEach(b => b.classList.remove("active"));
          btn.classList.add("active");

          section.querySelectorAll(".subtab-content").forEach(c => c.classList.remove("active"));
          const targetSubtab = document.getElementById(subtabId);
          if (targetSubtab) {
            targetSubtab.classList.add("active");
          }

          // Trigger subtab specific actions safely
          if (subtabId === "subtab-credentials") {
            if (typeof this.scanCredentials === 'function') this.scanCredentials();
          } else if (subtabId === "subtab-printer-lan") {
            if (typeof this.scanPrinters === 'function') this.scanPrinters();
          } else if (subtabId === "subtab-create-user") {
            if (typeof this.loadLocalGroupsAndUsers === 'function') this.loadLocalGroupsAndUsers();
            if (typeof this.startGroupUserRealtimeMonitor === 'function') this.startGroupUserRealtimeMonitor();
          } else if (subtabId === "subtab-boot-bcd") {
            if (typeof this.loadBootEntries === 'function') this.loadBootEntries();
          } else if (subtabId === "subtab-boot-winpe") {
            if (typeof this.loadPartitions === 'function') this.loadPartitions();
          }

          if (subtabId !== "subtab-create-user" && typeof this.stopGroupUserRealtimeMonitor === 'function') {
            this.stopGroupUserRealtimeMonitor();
          }
        } catch (err) {
          console.error("Lỗi chuyển subtab:", err);
        }
      });
    });

    // Theme Toggle
    document.getElementById("theme-toggle")?.addEventListener("click", () => {
      document.body.classList.toggle("dark-mode");
    });

    // Support F5 and Ctrl + R to refresh application UI
    window.addEventListener("keydown", (e) => {
      if (e.key === "F5" || (e.ctrlKey && (e.key === "r" || e.key === "R"))) {
        e.preventDefault();
        window.location.reload();
      }
    });
  }

  startClock() {
    const update = () => {
      const now = new Date();
      const days = ["Chủ Nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy"];
      const dayName = days[now.getDay()];
      const timeStr = now.toTimeString().split(" ")[0];
      const dateStr = `${String(now.getDate()).padStart(2, "0")}/${String(now.getMonth() + 1).padStart(2, "0")}/${now.getFullYear()}`;
      const clockEl = document.getElementById("clock-display");
      if (clockEl) clockEl.innerText = `${dayName}, ${timeStr} • ${dateStr}`;
    };
    update();
    setInterval(update, 1000);
  }

  updateZoomUI() {
    if (this.currentZoom > 100) this.currentZoom = 100;
    if (this.currentZoom < 70) this.currentZoom = 70;
    document.body.style.zoom = `${this.currentZoom}%`;
    const valEl = document.getElementById("zoom-value");
    if (valEl) valEl.innerText = `${this.currentZoom}%`;

    const btnIn = document.getElementById("btn-zoom-in");
    const btnOut = document.getElementById("btn-zoom-out");
    if (btnIn) {
      const isMax = this.currentZoom >= 100;
      btnIn.disabled = isMax;
      btnIn.style.opacity = isMax ? "0.35" : "1";
      btnIn.style.cursor = isMax ? "not-allowed" : "pointer";
    }
    if (btnOut) {
      const isMin = this.currentZoom <= 70;
      btnOut.disabled = isMin;
      btnOut.style.opacity = isMin ? "0.35" : "1";
      btnOut.style.cursor = isMin ? "not-allowed" : "pointer";
    }
  }

  zoomIn() {
    if (this.currentZoom < 100) {
      this.currentZoom += 10;
      this.updateZoomUI();
    }
  }

  zoomOut() {
    if (this.currentZoom > 70) {
      this.currentZoom -= 10;
      this.updateZoomUI();
    }
  }

  addLog(level, message) {
    const logBody = document.getElementById("log-body");
    if (!logBody) return;
    const time = new Date().toTimeString().split(" ")[0];
    const div = document.createElement("div");
    div.className = `log-line ${level}`;
    div.innerText = `[${time}] [${level.toUpperCase()}] ${message}`;
    logBody.appendChild(div);
    logBody.scrollTop = logBody.scrollHeight;

    const countBadge = document.getElementById("log-count");
    if (countBadge) {
      const current = logBody.children.length;
      countBadge.innerText = `${current} entries`;
    }
    const headerLogCount = document.getElementById("header-log-count");
    if (headerLogCount) {
      headerLogCount.innerText = logBody.children.length;
    }
  }

  toggleLogDrawer(forceState) {
    const drawer = document.getElementById("log-drawer");
    const workspace = document.querySelector(".main-workspace");
    const toggleBtn = document.getElementById("btn-toggle-log-drawer");
    if (!drawer) return;

    if (drawer.classList.contains("hidden")) {
      drawer.classList.remove("hidden");
      if (workspace) workspace.classList.remove("log-hidden");
    }

    if (forceState === "expand") {
      drawer.classList.remove("collapsed");
    } else if (forceState === "collapse") {
      drawer.classList.add("collapsed");
    } else {
      drawer.classList.toggle("collapsed");
    }

    const isCollapsed = drawer.classList.contains("collapsed");
    if (workspace) {
      workspace.classList.toggle("log-expanded", !isCollapsed);
    }
    if (toggleBtn) {
      toggleBtn.innerText = isCollapsed ? "▲ Mở rộng" : "▼ Thu gọn";
    }
  }

  hideLogDrawer() {
    const drawer = document.getElementById("log-drawer");
    const workspace = document.querySelector(".main-workspace");
    if (drawer) {
      drawer.classList.add("hidden");
    }
    if (workspace) {
      workspace.classList.remove("log-expanded");
      workspace.classList.add("log-hidden");
    }
  }

  showLogDrawer() {
    const drawer = document.getElementById("log-drawer");
    const workspace = document.querySelector(".main-workspace");
    const toggleBtn = document.getElementById("btn-toggle-log-drawer");
    if (drawer) {
      drawer.classList.remove("hidden");
      drawer.classList.remove("collapsed");
    }
    if (workspace) {
      workspace.classList.remove("log-hidden");
      workspace.classList.add("log-expanded");
    }
    if (toggleBtn) {
      toggleBtn.innerText = "▼ Thu gọn";
    }
  }

  toggleLogVisibility() {
    const drawer = document.getElementById("log-drawer");
    if (!drawer) return;
    if (drawer.classList.contains("hidden")) {
      this.showLogDrawer();
    } else if (!drawer.classList.contains("collapsed")) {
      this.toggleLogDrawer("collapse");
    } else {
      this.hideLogDrawer();
    }
  }

  clearLogs() {
    const logBody = document.getElementById("log-body");
    if (logBody) logBody.innerHTML = "";
    const countBadge = document.getElementById("log-count");
    if (countBadge) countBadge.innerText = "0 entries";
    const headerLogCount = document.getElementById("header-log-count");
    if (headerLogCount) headerLogCount.innerText = "0";
  }

  openWebsite() {
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.open_website();
    } else {
      window.open("https://lethetuanpc.blogspot.com", "_blank");
    }
  }

  openTelegram() {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.open_telegram) {
      window.pywebview.api.open_telegram();
    } else {
      window.open("https://t.me/lethetuanpc", "_blank");
    }
  }

  async loadAutostartStatus() {
    try {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.get_autostart_status) {
        const res = await window.pywebview.api.get_autostart_status();
        this.updateAutostartUI(res && res.enabled);
      }
    } catch (e) {
      console.error("Lỗi lấy trạng thái autostart:", e);
    }
  }

  updateAutostartUI(enabled) {
    const isEn = !!enabled;
    const headerToggle = document.getElementById("header-autostart-checkbox");
    const headerBadge = document.getElementById("autostart-status-badge");
    const startupToggle = document.getElementById("tab-startup-autostart-checkbox");
    const startupBadge = document.getElementById("tab-startup-autostart-badge");
    const sidebarBadge = document.getElementById("sidebar-autostart-badge");

    if (headerToggle) headerToggle.checked = isEn;
    if (startupToggle) startupToggle.checked = isEn;

    const labelText = isEn ? "BẬT" : "TẮT";
    const clsName = "autostart-badge " + (isEn ? "on" : "off");

    if (headerBadge) {
      headerBadge.textContent = labelText;
      headerBadge.className = clsName;
    }
    if (startupBadge) {
      startupBadge.textContent = labelText;
      startupBadge.className = clsName;
    }
    if (sidebarBadge) {
      sidebarBadge.textContent = labelText;
      sidebarBadge.className = clsName;
    }
  }

  async setAutostart(enable) {
    try {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.set_autostart) {
        const res = await window.pywebview.api.set_autostart(enable);
        this.updateAutostartUI(res && res.enabled);
        if (res && res.success) {
          this.addLog("ok", res.message || (enable ? "Đã bật khởi động cùng Windows" : "Đã tắt khởi động cùng Windows"));
        } else {
          this.addLog("error", (res && res.message) || "Lỗi cài đặt khởi động cùng Windows");
        }
      } else {
        this.updateAutostartUI(enable);
        this.addLog("info", `Khởi động cùng Windows: ${enable ? "BẬT" : "TẮT"}`);
      }
    } catch (e) {
      console.error("Lỗi đặt autostart:", e);
      this.addLog("error", "Lỗi cài đặt khởi động: " + e);
    }
  }

  showToast(type, message) {
    let container = document.getElementById('app-toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'app-toast-container';
      container.style.cssText = 'position: fixed; top: 20px; right: 24px; z-index: 9999999; display: flex; flex-direction: column; gap: 8px; pointer-events: none;';
      document.body.appendChild(container);
    }
    while (container.children.length >= 2) {
      container.removeChild(container.firstChild);
    }
    const toast = document.createElement('div');
    const colors = {
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#38bdf8'
    };
    const borderColor = colors[type] || '#38bdf8';
    toast.style.cssText = `background: #1e293b; border-left: 4px solid ${borderColor}; color: #f8fafc; padding: 12px 18px; border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); font-size: 13px; font-weight: 700; pointer-events: auto; display: flex; align-items: center; gap: 10px; transition: all 0.3s ease;`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(20px)';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }
}

