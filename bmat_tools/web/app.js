/**
 * IT-Tools 2026 Modern Application Logic - Core Controller
 * Author: Lê Thế Tuấn | 0352 194 195 | https://lethetuanpc.blogspot.com/
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
    if (typeof this.scanPrinters === 'function') this.scanPrinters();
    if (typeof this.scanCredentials === 'function') this.scanCredentials();
    if (typeof this.loadComputerInfo === 'function') this.loadComputerInfo();
    if (typeof this.loadSystemDrives === 'function') this.loadSystemDrives();
    if (typeof this.loadClassicMenuStatus === 'function') this.loadClassicMenuStatus();
    if (typeof this.loadHosts === 'function') this.loadHosts();
    if (typeof this.loadInstalledDrivers === 'function') this.loadInstalledDrivers();
    if (typeof this.loadServices === 'function') this.loadServices();
    if (typeof this.loadBrowserBackupInfo === 'function') this.loadBrowserBackupInfo();
    if (typeof this.loadDateTimeInfo === 'function') this.loadDateTimeInfo();
    if (typeof this.loadSoftwareCatalog === 'function') this.loadSoftwareCatalog();
    if (typeof this.loadFirewallStatus === 'function') this.loadFirewallStatus();
    if (typeof this.loadSystemTweaksStatus === 'function') this.loadSystemTweaksStatus();
    if (typeof this.runWinCheckAudit === 'function') this.runWinCheckAudit();
    if (typeof this.checkExistingOfficeInstall === 'function') this.checkExistingOfficeInstall();
    if (typeof this.loadScheduledShutdownTasks === 'function') this.loadScheduledShutdownTasks();
  }

  bindEvents() {
    // Navigation Tabs
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

          if (tabId === "tab-computer-info") {
            if (typeof this.loadComputerInfo === 'function') this.loadComputerInfo();
          } else if (tabId === "tab-auto-shutdown") {
            if (typeof this.loadScheduledShutdownTasks === 'function') this.loadScheduledShutdownTasks();
          } else if (tabId === "tab-folder-size") {
            if (typeof this.loadSystemDrives === 'function') this.loadSystemDrives();

          } else if (tabId === "tab-desktop-icon") {
            if (typeof this.loadDesktopIconSettings === 'function') this.loadDesktopIconSettings();
          } else if (tabId === "tab-startup") {
            if (typeof this.loadStartupEntries === 'function') this.loadStartupEntries();
          } else if (tabId === "tab-auto-win" || tabId === "tab-win-update") {
            if (typeof this.loadWinUpdateStatus === 'function') this.loadWinUpdateStatus();
          } else if (tabId === "tab-uninstall") {
            if (typeof this.loadInstalledApps === 'function') this.loadInstalledApps();
          } else if (tabId === "tab-bitlocker") {
            if (typeof this.loadBitlockerDrives === 'function') this.loadBitlockerDrives();
          } else if (tabId === "tab-ip-manager") {
            if (typeof this.loadNetworkAdapters === 'function') this.loadNetworkAdapters();
          } else if (tabId === "tab-ip-scanner") {
            if (typeof this.loadIpScannerDefaults === 'function') this.loadIpScannerDefaults();
          } else if (tabId === "tab-classic-menu") {
            if (typeof this.loadClassicMenuStatus === 'function') this.loadClassicMenuStatus();
          } else if (tabId === "tab-hosts") {
            if (typeof this.loadHosts === 'function') this.loadHosts();
          } else if (tabId === "tab-backup-driver") {
            if (typeof this.loadInstalledDrivers === 'function') this.loadInstalledDrivers();
          } else if (tabId === "tab-services") {
            if (typeof this.loadServices === 'function') this.loadServices();
          } else if (tabId === "tab-browser-backup") {
            if (typeof this.loadBrowserBackupInfo === 'function') this.loadBrowserBackupInfo();
          } else if (tabId === "tab-datetime") {
            if (typeof this.loadDateTimeInfo === 'function') this.loadDateTimeInfo();
          } else if (tabId === "tab-free-software") {
            if (typeof this.loadSoftwareCatalog === 'function') this.loadSoftwareCatalog();
          } else if (tabId === "tab-firewall") {
            if (typeof this.loadFirewallStatus === 'function') this.loadFirewallStatus();
          } else if (tabId === "tab-other-tweaks") {
            if (typeof this.loadSystemTweaksStatus === 'function') this.loadSystemTweaksStatus();
          } else if (tabId === "tab-server-tools") {
            if (typeof this.loadServerTools === 'function') this.loadServerTools();
          } else if (tabId === "tab-boot-manager") {
            if (typeof this.loadBootEntries === 'function') this.loadBootEntries();
          } else if (tabId === "tab-currency") {
            if (typeof this.loadCurrencyRates === 'function') this.loadCurrencyRates();
          } else if (tabId === "tab-office") {
            if (typeof this.checkExistingOfficeInstall === 'function') this.checkExistingOfficeInstall();
          }
        } catch (err) {
          console.error("Lỗi chuyển tab chính:", err);
        }
      });
    });

    // Sub-Tabs inside Printer Fix page
    const subtabBtns = document.querySelectorAll(".subtab-btn");
    subtabBtns.forEach(btn => {
      btn.addEventListener("click", (e) => {
        try {
          if (e) e.preventDefault();
          if (document.activeElement && typeof document.activeElement.blur === 'function') {
            document.activeElement.blur();
          }

          const subtabId = btn.getAttribute("data-subtab");

          subtabBtns.forEach(b => b.classList.remove("active"));
          btn.classList.add("active");

          document.querySelectorAll(".subtab-content").forEach(c => c.classList.remove("active"));
          const targetSubtab = document.getElementById(subtabId);
          if (targetSubtab) {
            targetSubtab.classList.add("active");
          }

          // Trigger subtab specific actions safely
          if (subtabId === "subtab-credentials") {
            if (typeof this.scanCredentials === 'function') this.scanCredentials();
          } else if (subtabId === "subtab-printer-lan") {
            if (typeof this.scanPrinters === 'function') this.scanPrinters();
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

  zoomIn() {
    if (this.currentZoom < 140) {
      this.currentZoom += 10;
      document.body.style.zoom = `${this.currentZoom}%`;
      const valEl = document.getElementById("zoom-value");
      if (valEl) valEl.innerText = `${this.currentZoom}%`;
    }
  }

  zoomOut() {
    if (this.currentZoom > 80) {
      this.currentZoom -= 10;
      document.body.style.zoom = `${this.currentZoom}%`;
      const valEl = document.getElementById("zoom-value");
      if (valEl) valEl.innerText = `${this.currentZoom}%`;
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
  }

  toggleLogDrawer() {
    const drawer = document.getElementById("log-drawer");
    const workspace = document.querySelector(".main-workspace");
    if (drawer) {
      drawer.classList.toggle("collapsed");
      if (workspace) {
        workspace.classList.toggle("log-expanded", !drawer.classList.contains("collapsed"));
      }
    }
  }

  clearLogs() {
    const logBody = document.getElementById("log-body");
    if (logBody) logBody.innerHTML = "";
    const countBadge = document.getElementById("log-count");
    if (countBadge) countBadge.innerText = "0 entries";
  }

  openWebsite() {
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.open_website();
    } else {
      window.open("https://lethetuanpc.blogspot.com/", "_blank");
    }
  }
}
