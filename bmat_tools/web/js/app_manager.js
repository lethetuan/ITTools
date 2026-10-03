/**
 * IT Tool LTT 2026 - Free Software Store, App Uninstall, Startup & Desktop Icon Manager Module
 */
Object.assign(AppController.prototype, {
  // ── FREE SOFTWARE STORE (WINGET SILENT INSTALLER) ──────────────────────
  async loadSoftwareCatalog() {
    let catalog = [];
    if (window.pywebview && window.pywebview.api) {
      catalog = await window.pywebview.api.get_software_catalog();
    } else {
      // Mock data fallback with representative apps from all categories
      catalog = [
        // Trình duyệt
        { id: "CocCoc.CocCoc", name: "Cốc Cốc", category: "Trình duyệt", icon: "🌐" },
        { id: "Google.Chrome", name: "Google Chrome", category: "Trình duyệt", icon: "🌐" },
        { id: "Microsoft.Edge", name: "Microsoft Edge", category: "Trình duyệt", icon: "🌐" },
        { id: "Mozilla.Firefox", name: "Mozilla Firefox", category: "Trình duyệt", icon: "🦊" },
        { id: "Brave.Brave", name: "Brave Browser", category: "Trình duyệt", icon: "🦁" },
        { id: "Opera.Opera", name: "Opera", category: "Trình duyệt", icon: "🔴" },
        { id: "Opera.OperaGX", name: "Opera GX", category: "Trình duyệt", icon: "🎮" },
        { id: "Vivaldi.Vivaldi", name: "Vivaldi", category: "Trình duyệt", icon: "🔴" },
        // Bộ gõ
        { id: "UniKey.UniKey", name: "UniKey", category: "Bộ gõ", icon: "⌨️" },
        { id: "EVKeyVN.EVKey", name: "EVKey", category: "Bộ gõ", icon: "⌨️" },
        // Giải nén
        { id: "7zip.7zip", name: "7-Zip", category: "Giải nén", icon: "📦" },
        { id: "RARLab.WinRAR", name: "WinRAR", category: "Giải nén", icon: "📚" },
        { id: "Bandisoft.Bandizip", name: "Bandizip", category: "Giải nén", icon: "📦" },
        // Download
        { id: "SoftDeluxe.FreeDownloadManager", name: "Free Download Manager", category: "Download", icon: "⬇️" },
        { id: "qBittorrent.qBittorrent", name: "qBittorrent", category: "Download", icon: "🧲" },
        { id: "Tonec.InternetDownloadManager", name: "IDM", category: "Download", icon: "⬇️" },
        // PDF
        { id: "Foxit.FoxitReader", name: "Foxit PDF Reader", category: "PDF", icon: "📄" },
        { id: "SumatraPDF.SumatraPDF", name: "SumatraPDF", category: "PDF", icon: "📖" },
        { id: "Adobe.Acrobat.Reader.64-bit", name: "Adobe Acrobat Reader", category: "PDF", icon: "📄" },
        // Chat
        { id: "Telegram.TelegramDesktop", name: "Telegram", category: "Chat", icon: "✈️" },
        { id: "Zoom.Zoom", name: "Zoom Meetings", category: "Chat", icon: "📹" },
        { id: "Discord.Discord", name: "Discord", category: "Chat", icon: "👾" },
        { id: "Microsoft.Teams", name: "Microsoft Teams", category: "Chat", icon: "👥" },
        { id: "Viber.Viber", name: "Viber", category: "Chat", icon: "📱" },
        // Văn phòng
        { id: "TheDocumentFoundation.LibreOffice", name: "LibreOffice", category: "Văn phòng", icon: "📝" },
        { id: "Kingsoft.WPSOffice", name: "WPS Office", category: "Văn phòng", icon: "📊" },
        { id: "Notepad++.Notepad++", name: "Notepad++", category: "Văn phòng", icon: "✏️" },
        { id: "Microsoft.PowerToys", name: "PowerToys", category: "Văn phòng", icon: "🛠️" },
        { id: "Obsidian.Obsidian", name: "Obsidian", category: "Văn phòng", icon: "📒" },
        // Đa phương tiện
        { id: "VideoLAN.VLC", name: "VLC Media Player", category: "Đa phương tiện", icon: "🎥" },
        { id: "Kakao.PotPlayer", name: "PotPlayer", category: "Đa phương tiện", icon: "🎬" },
        { id: "OBSProject.OBSStudio", name: "OBS Studio", category: "Đa phương tiện", icon: "📹" },
        { id: "Spotify.Spotify", name: "Spotify", category: "Đa phương tiện", icon: "🎵" },
        { id: "ShareX.ShareX", name: "ShareX", category: "Đa phương tiện", icon: "📸" },
        // Tiện ích
        { id: "AnyDesk.AnyDesk", name: "AnyDesk", category: "Tiện ích", icon: "💻" },
        { id: "TeamViewer.TeamViewer", name: "TeamViewer", category: "Tiện ích", icon: "🔗" },
        { id: "DucFabulous.UltraViewer", name: "UltraViewer", category: "Tiện ích", icon: "🖥️" },
        { id: "Rufus.Rufus", name: "Rufus", category: "Tiện ích", icon: "💾" },
        { id: "Microsoft.WindowsTerminal", name: "Windows Terminal", category: "Tiện ích", icon: "⬛" },
        // Hệ thống
        { id: "CPUID.CPU-Z", name: "CPU-Z", category: "Hệ thống", icon: "⚡" },
        { id: "TechPowerUp.GPU-Z", name: "GPU-Z", category: "Hệ thống", icon: "🎮" },
        { id: "CrystalDewWorld.CrystalDiskInfo", name: "CrystalDiskInfo", category: "Hệ thống", icon: "💽" },
        { id: "REALiX.HWiNFO", name: "HWiNFO", category: "Hệ thống", icon: "ℹ️" },
        // Bảo mật
        { id: "Malwarebytes.Malwarebytes", name: "Malwarebytes", category: "Bảo mật", icon: "🛡️" },
        { id: "Bitwarden.Bitwarden", name: "Bitwarden", category: "Bảo mật", icon: "🔑" },
        { id: "ProtonVPN.ProtonVPN", name: "ProtonVPN", category: "Bảo mật", icon: "🔐" },
        // Lập trình
        { id: "Microsoft.VisualStudioCode", name: "Visual Studio Code", category: "Lập trình", icon: "💙" },
        { id: "Git.Git", name: "Git", category: "Lập trình", icon: "🔀" },
        { id: "Python.Python.3.12", name: "Python 3.12", category: "Lập trình", icon: "🐍" },
        { id: "Docker.DockerDesktop", name: "Docker Desktop", category: "Lập trình", icon: "🐳" },
        // Mạng xã hội
        { id: "Valve.Steam", name: "Steam", category: "Mạng xã hội", icon: "🎮" },
        { id: "Facebook.Messenger", name: "Facebook Messenger", category: "Mạng xã hội", icon: "💙" },
        // Đồ hoạ
        { id: "Canva.Canva", name: "Canva Desktop", category: "Đồ hoạ", icon: "🎨" },
        { id: "Figma.Figma", name: "Figma", category: "Đồ hoạ", icon: "✏️" },
        { id: "BlenderFoundation.Blender", name: "Blender 3D", category: "Đồ hoạ", icon: "🌀" },
        // Kế toán
        { id: "GnuCash.GnuCash", name: "GnuCash", category: "Kế toán", icon: "💰" },
        { id: "Microsoft.PowerBI", name: "Power BI Desktop", category: "Kế toán", icon: "📊" },
        // Cloud
        { id: "Google.GoogleDrive", name: "Google Drive", category: "Cloud", icon: "☁️" },
        { id: "Mega.MEGASync", name: "MEGA Sync", category: "Cloud", icon: "🌊" },
        // Công cụ mạng
        { id: "Wireshark.Wireshark", name: "Wireshark", category: "Công cụ mạng", icon: "🦈" },
        { id: "Cloudflare.Warp", name: "Cloudflare WARP", category: "Công cụ mạng", icon: "🌐" },
      ];
    }

    if (!this.selectedSoftwareIds) {
      this.selectedSoftwareIds = new Set();
    }
    this.softwareCatalog = catalog;
    const countAll = document.getElementById("count-all");
    if (countAll) countAll.innerText = catalog.length;

    this.renderSoftwareGrid(catalog);
    this.bindCategoryEvents();

    // Khi mở lại app, kiểm tra xem có tiến trình cài đặt nền đang chạy không
    this.resumeBgWingetSession();
  },

  bindCategoryEvents() {
    if (this._categoryEventsBound) return;
    this._categoryEventsBound = true;
    const catItems = document.querySelectorAll(".cat-item");
    catItems.forEach(item => {
      item.addEventListener("click", () => {
        catItems.forEach(c => c.classList.remove("active"));
        item.classList.add("active");

        const cat = item.getAttribute("data-cat");
        if (cat === "all") {
          this.renderSoftwareGrid(this.softwareCatalog);
        } else {
          const filtered = this.softwareCatalog.filter(s => s.category === cat);
          this.renderSoftwareGrid(filtered);
        }
      });
    });
  },

  renderSoftwareGrid(items) {
    if (!this.selectedSoftwareIds) {
      this.selectedSoftwareIds = new Set();
    }
    const grid = document.getElementById("software-grid");
    if (!grid) return;
    grid.innerHTML = "";

    if (!items || items.length === 0) {
      grid.innerHTML = `<div class="text-muted text-center py-4 grid-col-span-2">Không tìm thấy phần mềm phù hợp.</div>`;
      return;
    }

    items.forEach(app => {
      const card = document.createElement("div");
      const isChecked = this.selectedSoftwareIds.has(app.id);
      const isInstalled = Boolean(app.is_installed);
      const isPinned = Boolean(app.is_pinned);

      card.className = "software-card" + (isChecked ? " selected" : "") + (isInstalled ? " app-installed" : "");
      card.setAttribute("data-id", app.id);

      // Dùng getAppIconHtml nếu có, fallback về emoji từ catalog
      const iconHtml = (typeof window.getAppIconHtml === "function")
        ? window.getAppIconHtml(app.id, 32)
        : `<span class="software-icon">${app.icon}</span>`;

      // Nút Ghim / Đã ghim đẹp mắt
      const pinBtnHtml = isPinned
        ? `<button type="button" class="btn-pin-single pinned" onclick="app.pinSingleApp('${app.id}', '${app.name.replace(/'/g, "\\'")}', event)" title="Đã có shortcut trên Desktop / Start Menu (Bấm để ghim lại)"><span>📌</span> Đã ghim</button>`
        : `<button type="button" class="btn-pin-single" onclick="app.pinSingleApp('${app.id}', '${app.name.replace(/'/g, "\\'")}', event)" title="Ghim ứng dụng này ra Desktop & Start Menu"><span>📌</span> Ghim</button>`;

      // Nút Cài đặt / Đã cài đặt
      const installBtnHtml = isInstalled
        ? `<button type="button" class="btn-install-single installed" onclick="app.installSingleApp('${app.id}', event)" title="Đã cài đặt trên máy tính (Bấm để cài lại/nâng cấp)"><span>✓</span> Đã cài đặt</button>`
        : `<button type="button" class="btn-install-single" onclick="app.installSingleApp('${app.id}', event)" title="Cài đặt nhanh ứng dụng này"><span>⚡</span> Cài đặt</button>`;

      card.innerHTML = `
        <input type="checkbox" class="soft-checkbox" value="${app.id}" ${isChecked ? "checked" : ""} onchange="app.toggleSoftwareSelect('${app.id}', this.checked)">
        <span class="software-icon-wrap">${iconHtml}</span>
        <div class="software-info">
          <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
            <span class="software-name">${app.name}</span>
            ${isInstalled ? '<span class="badge" style="background: #ecfdf5; color: #15803d; border: 1px solid #a7f3d0; border-radius: 4px; font-size: 9.5px; font-weight: 700; padding: 1px 5px; line-height: 1.2;">ĐÃ CÀI</span>' : ''}
          </div>
          <span class="software-id">${app.id}</span>
        </div>
        <div class="software-card-actions">
          ${pinBtnHtml}
          ${installBtnHtml}
        </div>
      `;

      card.addEventListener("click", (e) => {
        if (e.target.tagName !== "INPUT" && !e.target.closest(".software-card-actions") && !e.target.closest(".btn-install-single") && !e.target.closest(".btn-pin-single")) {
          const willBeChecked = !this.selectedSoftwareIds.has(app.id);
          this.toggleSoftwareSelect(app.id, willBeChecked);
        }
      });

      grid.appendChild(card);
    });

    this.updateSelectedCounter();
  },

  toggleSoftwareSelect(appId, isChecked) {
    if (!this.selectedSoftwareIds) {
      this.selectedSoftwareIds = new Set();
    }
    if (isChecked) {
      this.selectedSoftwareIds.add(appId);
    } else {
      this.selectedSoftwareIds.delete(appId);
    }
    const card = document.querySelector(`.software-card[data-id="${appId}"]`);
    if (card) {
      card.classList.toggle("selected", isChecked);
      const chk = card.querySelector(".soft-checkbox");
      if (chk) chk.checked = isChecked;
    }
    this.updateSelectedCounter();
  },

  filterSoftware() {
    const query = document.getElementById("software-search").value.toLowerCase().trim();
    if (!query) {
      const activeCat = document.querySelector(".cat-item.active")?.getAttribute("data-cat") || "all";
      if (activeCat === "all") {
        this.renderSoftwareGrid(this.softwareCatalog);
      } else {
        this.renderSoftwareGrid(this.softwareCatalog.filter(s => s.category === activeCat));
      }
      return;
    }

    const filtered = this.softwareCatalog.filter(s =>
      s.name.toLowerCase().includes(query) ||
      s.id.toLowerCase().includes(query) ||
      s.category.toLowerCase().includes(query)
    );
    this.renderSoftwareGrid(filtered);
  },

  selectAllSoftware(selectBool) {
    if (!this.selectedSoftwareIds) {
      this.selectedSoftwareIds = new Set();
    }
    if (!selectBool) {
      this.selectedSoftwareIds.clear();
      document.querySelectorAll(".software-card").forEach(card => {
        card.classList.remove("selected");
        const chk = card.querySelector(".soft-checkbox");
        if (chk) chk.checked = false;
      });
    } else {
      document.querySelectorAll(".software-card").forEach(card => {
        const appId = card.getAttribute("data-id");
        if (appId) this.selectedSoftwareIds.add(appId);
        card.classList.add("selected");
        const chk = card.querySelector(".soft-checkbox");
        if (chk) chk.checked = true;
      });
    }
    this.updateSelectedCounter();
  },

  updateSelectedCounter() {
    const count = this.selectedSoftwareIds ? this.selectedSoftwareIds.size : 0;
    const total = this.softwareCatalog ? this.softwareCatalog.length : 0;
    const badge = document.getElementById("selected-counter");
    if (badge) {
      badge.innerText = `Đã chọn ${count}/${total} mục (${count} tổng)`;
    }
    this._updateBatchInstallButton();
  },

  // ── HELPER: Cập nhật trạng thái nút RUN linh hoạt theo ngữ cảnh ────────
  _updateBatchInstallButton() {
    const btn = document.getElementById("btn-batch-install");
    if (!btn) return;
    const count = this.selectedSoftwareIds ? this.selectedSoftwareIds.size : 0;

    if (this._isBatchInstalling) {
      if (count > 0) {
        btn.disabled = false;
        btn.className = "btn btn-primary-gradient w-100 py-2.5 font-bold";
        btn.innerHTML = `<span>➕</span> CÀI ĐẶT THÊM (${count} MỤC VÀO TIẾN TRÌNH)`;
      } else {
        btn.disabled = true;
        btn.className = "btn btn-slate-light w-100 py-2.5 font-bold opacity-80 cursor-not-allowed";
        btn.innerHTML = `<span>⚙️</span> Đang cài đặt nền (Chọn thêm để cộng dồn)`;
      }
    } else {
      btn.disabled = false;
      btn.className = "btn btn-success-gradient w-100 py-2.5 font-bold";
      if (count > 0) {
        btn.innerHTML = `<span>🚀</span> BẮT ĐẦU CÀI ĐẶT (${count} MỤC)`;
      } else {
        btn.innerHTML = `<span>🚀</span> BẮT ĐẦU CÀI ĐẶT (RUN)`;
      }
    }
  },

  // ── GHIM NHANH 1 ỨNG DỤNG RA START MENU, DESKTOP, PROGRAMS ──────────
  async pinSingleApp(appId, appName, event) {
    if (event) event.stopPropagation();
    const btn = event ? event.currentTarget : null;
    const originalHtml = btn ? btn.innerHTML : "<span>📌</span> Ghim";
    if (btn) {
      btn.innerHTML = `<span>⏳</span> Đang ghim...`;
      btn.disabled = true;
    }

    this.addLog("info", `📌 Đang xử lý ghim ứng dụng: ${appName || appId}...`);

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.pin_app_shortcut(appId, appName);
        if (res.success) {
          this.addLog("success", `📌 ${res.message}`);
          const appItem = (this.softwareCatalog || []).find(s => s.id === appId);
          if (appItem) {
            appItem.is_pinned = true;
          }
          if (btn) {
            btn.className = "btn-pin-single pinned";
            btn.innerHTML = `<span>📌</span> Đã ghim`;
            btn.title = "Đã có shortcut trên Desktop / Start Menu (Bấm để ghim lại)";
            btn.disabled = false;
          }
        } else {
          this.addLog("warning", `⚠️ ${res.message}`);
          if (btn) {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
          }
          alert(res.message);
        }
      } catch (err) {
        if (btn) {
          btn.innerHTML = originalHtml;
          btn.disabled = false;
        }
        this.addLog("error", `Lỗi ghim shortcut: ${err}`);
      }
    } else {
      alert(`[MOCK] Đã ghim ${appName || appId} ra Desktop, Start Menu và Programs!`);
      const appItem = (this.softwareCatalog || []).find(s => s.id === appId);
      if (appItem) {
        appItem.is_pinned = true;
      }
      if (btn) {
        btn.className = "btn-pin-single pinned";
        btn.innerHTML = `<span>📌</span> Đã ghim`;
        btn.title = "Đã có shortcut trên Desktop / Start Menu (Bấm để ghim lại)";
        btn.disabled = false;
      }
    }
  },

  // ── CÀI ĐẶT NHANH 1 ỨNG DỤNG (Hỗ trợ thêm trực tiếp khi đang chạy nền) ──
  async installSingleApp(appId, event) {
    if (event) event.stopPropagation();
    const btn = event ? event.currentTarget : null;
    if (btn) {
      btn.innerHTML = `<span>⏳</span> Đang thêm...`;
      btn.disabled = true;
    }

    this.addLog("info", `⚡ Đang gửi yêu cầu cài đặt phần mềm: ${appId}...`);

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.install_winget_batch([appId]);
        this.addLog(res.success ? "success" : "error", res.message);
        if (res.success) {
          const bgBanner = document.getElementById("bg-install-banner");
          if (bgBanner) bgBanner.style.display = "flex";
          if (!this._wingetPollInterval) {
            this._startWingetPoll();
          }
          if (btn) {
            btn.innerHTML = `<span>⏳</span> Trong hàng đợi`;
            btn.classList.add("queued");
          }
        } else {
          if (btn) {
            btn.innerHTML = `<span>⚡</span> Cài đặt`;
            btn.disabled = false;
          }
          alert(res.message);
        }
      } catch (err) {
        if (btn) {
          btn.innerHTML = `<span>⚡</span> Cài đặt`;
          btn.disabled = false;
        }
        this.addLog("error", `Lỗi cài đặt ${appId}: ${err}`);
      }
    } else {
      alert(`[MOCK] Đã thêm ${appId} vào hàng đợi cài đặt!`);
      if (btn) {
        btn.innerHTML = `<span>⏳</span> Trong hàng đợi`;
        btn.classList.add("queued");
      }
    }
  },

  // ── TIẾP TỤC PHIÊN CÀI ĐẶT NỀN (khởi động lại app) ──────────────────
  async resumeBgWingetSession() {
    if (!window.pywebview || !window.pywebview.api) return;
    try {
      const info = await window.pywebview.api.check_bg_winget_session();
      if (!info || !info.has_session) return;

      const statusText   = document.getElementById("install-status-text");
      const progressBar  = document.getElementById("install-progress-bar");
      const progressText = document.getElementById("install-progress-text");
      const bgBanner     = document.getElementById("bg-install-banner");

      if (statusText)   statusText.innerText  = info.status_text || "Đang cài đặt nền...";
      if (progressBar)  progressBar.style.width = "5%";
      if (progressText) progressText.innerText = `Đang chạy nền • 0 / ${info.total || '?'} phần mềm`;
      if (bgBanner)     bgBanner.style.display = "flex";

      this.addLog("info", `🔄 Phát hiện tiến trình cài đặt nền đang chạy (${info.total} phần mềm). Đang kết nối lại theo dõi tiến trình...`);
      this._startWingetPoll(info.total);
    } catch (e) {
      console.warn("resumeBgWingetSession error:", e);
    }
  },

  // ── POLLING TIẾN TRÌNH CÀI ĐẶT ──────────────────────────────────────
  _startWingetPoll(totalHint) {
    if (this._wingetPollInterval) {
      clearInterval(this._wingetPollInterval);
      this._wingetPollInterval = null;
    }

    this._isBatchInstalling = true;
    this._updateBatchInstallButton();

    const statusText   = document.getElementById("install-status-text");
    const progressBar  = document.getElementById("install-progress-bar");
    const progressText = document.getElementById("install-progress-text");
    const bgBanner     = document.getElementById("bg-install-banner");

    let deadCounter = 0;

    this._wingetPollInterval = setInterval(async () => {
      try {
        if (!window.pywebview || !window.pywebview.api) return;
        const st = await window.pywebview.api.get_winget_install_status();
        if (!st) return;

        const total = st.total || totalHint || 1;

        // Đẩy nhật ký thời gian thực sang bảng thông báo người dùng
        if (st.log && Array.isArray(st.log)) {
          if (!this._lastLoggedWingetIdx) this._lastLoggedWingetIdx = 0;
          for (let i = this._lastLoggedWingetIdx; i < st.log.length; i++) {
            const line = st.log[i];
            if (line.includes("[OK]")) {
              this.addLog("success", line);
            } else if (line.includes("[GHIM]")) {
              this.addLog("success", `📌 ${line}`);
            } else if (line.includes("[CANH BAO]")) {
              this.addLog("warning", `⚠️ ${line}`);
            } else if (line.includes("[LOI]") || line.includes("[EXCEPTION]")) {
              this.addLog("error", line);
            } else if (line.includes("[HUY]") || line.includes("[QUA THOI GIAN]") || line.includes("Thu lai")) {
              this.addLog("warning", line);
            } else if (line.includes("Bat dau")) {
              this.addLog("info", line);
            }
          }
          this._lastLoggedWingetIdx = st.log.length;
        }

        // Cập nhật UI thời gian thực
        if (statusText && st.status_text) {
          statusText.innerText = st.status_text;
        }
        if (progressBar) {
          const pct = Math.min(100, Math.max(0, st.percentage || 0));
          progressBar.style.width = `${pct}%`;
          if (st.error_count > 0 && st.success_count === 0) {
            progressBar.style.background = "#ef4444";
          } else if (st.error_count > 0) {
            progressBar.style.background = "#f59e0b";
          } else {
            progressBar.style.background = "linear-gradient(90deg, #10b981 0%, #059669 100%)";
          }
        }
        if (progressText) {
          const nameInfo = st.current_package_name ? ` — ${st.current_package_name}` : '';
          progressText.innerText = `${st.percentage || 0}% • ${st.current_index || 0} / ${total} phần mềm${nameInfo}`;
        }

        // ✅ KẾT THÚC: Khi finished=true hoặc state hoàn tất / đã dừng
        if (st.finished || st.state === "completed" || st.state === "canceled") {
          clearInterval(this._wingetPollInterval);
          this._wingetPollInterval = null;
          this._isBatchInstalling = false;
          this._lastLoggedWingetIdx = 0;
          this._updateBatchInstallButton();
          if (bgBanner) bgBanner.style.display = "none";

          if (st.canceled) {
            if (statusText) statusText.innerText = "⛔ Đã dừng";
            if (progressBar) progressBar.style.background = "#94a3b8";
            this.addLog("warning", "⛔ Quá trình cài đặt phần mềm nền đã bị dừng.");
          } else if (st.error_count > 0 && st.success_count === 0) {
            if (statusText) statusText.innerText = `❌ Thất bại (${st.error_count} lỗi)`;
            if (progressBar) progressBar.style.background = "#ef4444";
            this.addLog("error", `❌ Quá trình cài đặt thất bại: Không thể cài đặt ${st.error_count} phần mềm.`);
          } else if (st.error_count > 0) {
            if (statusText) statusText.innerText = `⚠️ Hoàn tất một phần (${st.success_count}/${total} thành công, ${st.error_count} lỗi)`;
            if (progressBar) {
              progressBar.style.width = "100%";
              progressBar.style.background = "#f59e0b";
            }
            this.addLog("warning", `⚠️ Hoàn tất một phần: ${st.success_count} thành công, ${st.error_count} lỗi.`);
            setTimeout(() => this.loadSoftwareCatalog(), 1500);
          } else {
            if (statusText) statusText.innerText = `✅ Hoàn tất (${st.success_count || total}/${total} thành công)`;
            if (progressBar) {
              progressBar.style.width = "100%";
              progressBar.style.background = "linear-gradient(90deg, #10b981 0%, #059669 100%)";
            }
            if (progressText) progressText.innerText = `100% • ${total} / ${total} phần mềm`;
            this.addLog("success", `🎉 ${st.status_text || "Đã hoàn tất cài đặt tất cả phần mềm!"}`);
            setTimeout(() => this.loadSoftwareCatalog(), 1500);
          }
          return;
        }

        // ⏱ Safety check: nếu cả is_running=false và finished=false kéo dài quá 10 giây
        if (!st.is_running) {
          deadCounter++;
          if (deadCounter >= 10) {
            clearInterval(this._wingetPollInterval);
            this._wingetPollInterval = null;
            this._isBatchInstalling = false;
            this._updateBatchInstallButton();
            if (bgBanner) bgBanner.style.display = "none";
            if (statusText) statusText.innerText = "⚠️ Tiến trình đã kết thúc";
            this.addLog("warning", "⚠️ Không phát hiện tiến trình cài đặt đang chạy.");
          }
        } else {
          deadCounter = 0;
        }
      } catch (e) {
        console.error("Lỗi cập nhật tiến trình cài đặt:", e);
      }
    }, 1000);
  },

  async startBatchInstall() {
    const checked = document.querySelectorAll(".soft-checkbox:checked");
    const selectedIds = Array.from(checked).map(c => c.value);

    if (selectedIds.length === 0) {
      alert("Vui lòng chọn ít nhất 1 phần mềm để cài đặt!");
      return;
    }

    const statusText   = document.getElementById("install-status-text");
    const progressBar  = document.getElementById("install-progress-bar");
    const progressText = document.getElementById("install-progress-text");
    const bgBanner     = document.getElementById("bg-install-banner");

    this.addLog("info", `🚀 Đang xử lý yêu cầu cài đặt ${selectedIds.length} phần mềm...`);
    this.addLog("info", `💡 Quá trình cài đặt chạy nền hoàn toàn — bạn có thể đóng app bất cứ lúc nào!`);

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.install_winget_batch(selectedIds);
        this.addLog(res.success ? "success" : "error", res.message);

        if (res.success) {
          // Bỏ chọn các checkbox đã được gửi vào hàng đợi thành công
          checked.forEach(chk => {
            chk.checked = false;
            chk.closest(".software-card")?.classList.remove("selected");
          });
          this.updateSelectedCounter();

          if (bgBanner) bgBanner.style.display = "flex";
          if (!this._wingetPollInterval) {
            this._startWingetPoll(res.total || selectedIds.length);
          }
        } else {
          alert(res.message);
        }
      } catch (err) {
        this.addLog("error", `Lỗi khởi chạy cài đặt: ${err}`);
      }
    } else {
      alert(`[MOCK] Đã bắt đầu cài đặt ẩn ${selectedIds.length} phần mềm qua Winget!`);
      checked.forEach(chk => {
        chk.checked = false;
        chk.closest(".software-card")?.classList.remove("selected");
      });
      this.updateSelectedCounter();
    }
  },

  async cancelBatchInstall() {
    this.addLog("warning", "⛔ Đang gửi yêu cầu dừng quá trình cài đặt phần mềm nền...");
    const statusText = document.getElementById("install-status-text");
    const bgBanner = document.getElementById("bg-install-banner");
    const progressBar = document.getElementById("install-progress-bar");
    const progressText = document.getElementById("install-progress-text");

    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.cancel_winget_batch === 'function') {
      try {
        const res = await window.pywebview.api.cancel_winget_batch();
        this.addLog("warning", res.message || "Đã dừng tiến trình cài đặt.");
      } catch (e) {
        console.error("Lỗi cancel:", e);
      }
    }

    if (this._wingetPollInterval) {
      clearInterval(this._wingetPollInterval);
      this._wingetPollInterval = null;
    }
    this._isBatchInstalling = false;
    this._updateBatchInstallButton();

    if (bgBanner) bgBanner.style.display = "none";
    if (statusText) statusText.innerText = "⛔ Đã dừng";
    if (progressBar) progressBar.style.width = "0%";
    if (progressText) progressText.innerText = "0% • Đã dừng tiến trình cài đặt";

    document.querySelectorAll(".software-card button.queued").forEach(b => {
      b.innerHTML = "<span>⚡</span> Cài đặt";
      b.classList.remove("queued");
      b.disabled = false;
    });

    this.loadSoftwareCatalog();
  },

  async resetWingetSession() {
    if (!confirm("Bạn có muốn đặt lại toàn bộ hàng đợi cài đặt về trạng thái ban đầu?")) return;
    this.addLog("info", "🔄 Đang đặt lại trạng thái kho phần mềm...");
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.reset_winget_session === 'function') {
      try {
        const res = await window.pywebview.api.reset_winget_session();
        this.addLog("success", res.message);
      } catch (e) {
        console.error("Lỗi reset:", e);
      }
    }
    if (this._wingetPollInterval) {
      clearInterval(this._wingetPollInterval);
      this._wingetPollInterval = null;
    }
    this._isBatchInstalling = false;
    this._updateBatchInstallButton();

    const bgBanner = document.getElementById("bg-install-banner");
    const statusText = document.getElementById("install-status-text");
    const progressBar = document.getElementById("install-progress-bar");
    const progressText = document.getElementById("install-progress-text");

    if (bgBanner) bgBanner.style.display = "none";
    if (statusText) statusText.innerText = "Sẵn sàng";
    if (progressBar) progressBar.style.width = "0%";
    if (progressText) progressText.innerText = "0% • 0 / 0 phần mềm";

    document.querySelectorAll(".software-card button.queued").forEach(b => {
      b.innerHTML = "<span>⚡</span> Cài đặt";
      b.classList.remove("queued");
      b.disabled = false;
    });

    this.loadSoftwareCatalog();
  },

  // ── DESKTOP ICON & TASKBAR MANAGER ────────────────────────────────────
  async loadDesktopIconSettings() {
    this.addLog("info", "Đang đọc trạng thái cài đặt Desktop Icon & Taskbar...");
    let settings = null;
    if (window.pywebview && window.pywebview.api) {
      settings = await window.pywebview.api.get_desktop_icon_settings();
    } else {
      settings = {
        computer: true,
        user_files: true,
        network: true,
        control_panel: true,
        taskbar_left: true,
        search_icon: false,
        weather_off: true,
        recycle_bin: true
      };
    }

    if (!settings) return;

    if (document.getElementById("chk-desktop-computer")) document.getElementById("chk-desktop-computer").checked = !!settings.computer;
    if (document.getElementById("chk-desktop-user")) document.getElementById("chk-desktop-user").checked = !!settings.user_files;
    if (document.getElementById("chk-desktop-network")) document.getElementById("chk-desktop-network").checked = !!settings.network;
    if (document.getElementById("chk-desktop-cpanel")) document.getElementById("chk-desktop-cpanel").checked = !!settings.control_panel;
    if (document.getElementById("chk-desktop-taskbar-left")) document.getElementById("chk-desktop-taskbar-left").checked = !!settings.taskbar_left;
    if (document.getElementById("chk-desktop-search")) document.getElementById("chk-desktop-search").checked = !!settings.search_icon;
    if (document.getElementById("chk-desktop-weather-off")) document.getElementById("chk-desktop-weather-off").checked = !!settings.weather_off;
    if (document.getElementById("chk-desktop-recycle")) document.getElementById("chk-desktop-recycle").checked = !!settings.recycle_bin;

    this.addLog("success", "Đã đọc trạng thái Desktop Icon thành công!");
  },

  selectAllDesktopIcons(checked) {
    const ids = [
      "chk-desktop-computer",
      "chk-desktop-user",
      "chk-desktop-network",
      "chk-desktop-cpanel",
      "chk-desktop-taskbar-left",
      "chk-desktop-search",
      "chk-desktop-weather-off",
      "chk-desktop-recycle"
    ];
    ids.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.checked = checked;
    });
  },

  async saveDesktopIconSettings() {
    const settings = {
      computer: document.getElementById("chk-desktop-computer")?.checked || false,
      user_files: document.getElementById("chk-desktop-user")?.checked || false,
      network: document.getElementById("chk-desktop-network")?.checked || false,
      control_panel: document.getElementById("chk-desktop-cpanel")?.checked || false,
      taskbar_left: document.getElementById("chk-desktop-taskbar-left")?.checked || false,
      search_icon: document.getElementById("chk-desktop-search")?.checked || false,
      weather_off: document.getElementById("chk-desktop-weather-off")?.checked || false,
      recycle_bin: document.getElementById("chk-desktop-recycle")?.checked || false
    };

    this.addLog("info", "Đang áp dụng thay đổi cài đặt Desktop Icon & Taskbar...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.save_desktop_icon_settings(settings);
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
    } else {
      alert("[MOCK] Đã áp dụng cài đặt Desktop Icon & Taskbar!");
    }
  },

  // ── STARTUP MANAGER ───────────────────────────────────────────────────
  async loadStartupEntries() {
    this.addLog("info", "Đang quét danh sách ứng dụng khởi động...");
    const tbody = document.getElementById("startup-list-body");
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">🔄 Đang quét các mục khởi động từ Registry & Startup folders...</td></tr>`;
    }

    let entries = [];
    if (window.pywebview && window.pywebview.api) {
      entries = await window.pywebview.api.get_startup_entries();
    } else {
      entries = [
        { name: "UniKey", path: "D:\\Desktop\\UniKeyNT.exe", location: "HKCU\\Run", is_enabled: false, status: "Disabled" },
        { name: "Listary", path: "\"C:\\Program Files\\Listary\\Listary.exe\" --startup", location: "HKCU\\Run", is_enabled: true, status: "V" },
        { name: "IDMan", path: "\"C:\\Program Files (x86)\\Internet Download Manager\\IDMan.exe\" /onboot", location: "HKCU\\Run", is_enabled: true, status: "V" },
        { name: "Zalo", path: "C:\\Users\\thetuan.le\\AppData\\Local\\Programs\\Zalo\\Zalo.exe", location: "HKCU\\Run", is_enabled: true, status: "V" }
      ];
    }

    this.rawStartupEntries = entries || [];
    this.currentStartupFilter = "all";
    this.renderStartupTable(this.rawStartupEntries);
    this.addLog("success", `Đã quét thành công ${this.rawStartupEntries.length} khoản khởi động!`);
  },

  filterStartupList(filter, btnElement) {
    this.currentStartupFilter = filter;
    
    if (btnElement && btnElement.parentNode) {
      btnElement.parentNode.querySelectorAll(".btn").forEach(b => {
        b.classList.remove("btn-primary");
        b.classList.add("btn-slate-light");
      });
      btnElement.classList.remove("btn-slate-light");
      btnElement.classList.add("btn-primary");
    }

    let filtered = this.rawStartupEntries || [];
    if (filter !== "all") {
      filtered = filtered.filter(item => (item.location || "").toLowerCase().includes(filter.toLowerCase()));
    }
    this.renderStartupTable(filtered);
  },

  renderStartupTable(entries) {
    this.currentRenderedEntries = entries || [];
    const tbody = document.getElementById("startup-list-body");
    if (!tbody) return;

    if (!entries || entries.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">Không tìm thấy mục khởi động nào trong nhóm này.</td></tr>`;
      return;
    }

    let html = "";
    entries.forEach((item, idx) => {
      const isChecked = item.is_enabled;
      const statusBadge = isChecked 
        ? `<span class="badge badge-status-enable">Enable</span>` 
        : `<span class="badge badge-status-disabled">Disabled</span>`;

      let iconHtml = "";
      if (item.icon && item.icon.startsWith("data:image/")) {
        iconHtml = `<img src="${item.icon}" style="width: 20px; height: 20px; object-fit: contain; vertical-align: middle;">`;
      } else {
        let icon = "🚀";
        const nameLower = (item.name || "").toLowerCase();
        if (nameLower.includes("unikey")) icon = "⌨️";
        else if (nameLower.includes("listary")) icon = "🔍";
        else if (nameLower.includes("idm") || nameLower.includes("download")) icon = "⬇️";
        else if (nameLower.includes("zalo")) icon = "💬";
        else if (nameLower.includes("chrome")) icon = "🌐";
        iconHtml = `<span style="font-size: 16px;">${icon}</span>`;
      }

      const escapedPath = (item.path || "").replace(/"/g, '&quot;');
      html += `<tr>
        <td style="text-align: center;">
          <input type="checkbox" ${isChecked ? 'checked' : ''} onchange="app.toggleStartupStatusByIndex(${idx}, this.checked)" style="width: 18px; height: 18px; cursor: pointer; accent-color: var(--primary);">
        </td>
        <td>
          <div style="display: flex; align-items: center; gap: 8px;">
            ${iconHtml}
            <strong class="startup-item-name">${item.name}</strong>
          </div>
        </td>
        <td>
          <code class="code-badge startup-path-code" title="${escapedPath}">${item.path}</code>
        </td>
        <td>
          <span class="badge badge-location-subtle">${item.location}</span>
        </td>
        <td style="text-align: center;">${statusBadge}</td>
        <td style="text-align: right;">
          <div style="display: flex; gap: 4px; justify-content: flex-end;">
            <button class="btn btn-slate-light btn-sm" onclick="app.openStartupModalByIndex(${idx})" title="Sửa Startup">✏️ Sửa</button>
            <button class="btn btn-sky-outline btn-sm" onclick="app.runStartupEntryByIndex(${idx})" title="Chạy ngay">▶️ Chạy</button>
            <button class="btn btn-rose-light btn-sm" onclick="app.deleteStartupEntryByIndex(${idx})" title="Xóa">🗑️ Xóa</button>
          </div>
        </td>
      </tr>`;
    });

    tbody.innerHTML = html;
  },

  toggleStartupStatusByIndex(idx, enable) {
    const item = (this.currentRenderedEntries || [])[idx];
    if (item) {
      this.toggleStartupStatus(item.name, item.location, enable);
    }
  },

  openStartupModalByIndex(idx) {
    const item = (this.currentRenderedEntries || [])[idx];
    if (item) {
      this.openStartupModal(item.name, item.path, item.location);
    } else {
      this.openStartupModal("", "", "HKCU\\Run");
    }
  },

  runStartupEntryByIndex(idx) {
    const item = (this.currentRenderedEntries || [])[idx];
    if (item) {
      this.runStartupEntry(item.path);
    }
  },

  deleteStartupEntryByIndex(idx) {
    const item = (this.currentRenderedEntries || [])[idx];
    if (item) {
      this.deleteStartupEntry(item.name, item.location, item.path);
    }
  },

  async toggleStartupStatus(name, location, enable) {
    this.addLog("info", `Đang ${enable ? 'bật' : 'tắt'} ứng dụng ${name} khởi động...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.toggle_startup_status(name, location, enable);
      this.addLog(res.success ? "success" : "error", res.message);
      this.loadStartupEntries();
    } else {
      alert(`[MOCK] Đã ${enable ? 'bật' : 'tắt'} ứng dụng ${name}!`);
    }
  },

  openStartupModal(name = "", path = "", location = "HKCU\\Run") {
    const modal = document.getElementById("startup-editor-modal");
    if (!modal) return;

    document.getElementById("startup-modal-title").innerText = name ? "Startup Editor (Chỉnh Sửa Startup)" : "Startup Editor (Thêm Mới Startup)";
    document.getElementById("startup-old-name").value = name;
    if (document.getElementById("startup-old-location")) {
      document.getElementById("startup-old-location").value = location;
    }
    document.getElementById("startup-input-name").value = name;
    document.getElementById("startup-input-path").value = path;
    
    const locSelect = document.getElementById("startup-input-location");
    if (locSelect) {
      let found = false;
      for (let opt of locSelect.options) {
        if (opt.value === location) {
          locSelect.value = location;
          found = true;
          break;
        }
      }
      if (!found && location) {
        const newOpt = document.createElement("option");
        newOpt.value = location;
        newOpt.innerText = location;
        locSelect.appendChild(newOpt);
        locSelect.value = location;
      }
    }

    modal.style.display = "flex";
  },

  closeStartupModal() {
    const modal = document.getElementById("startup-editor-modal");
    if (modal) modal.style.display = "none";
  },

  async browseStartupFile() {
    if (window.pywebview && window.pywebview.api) {
      const filePath = await window.pywebview.api.browse_startup_file();
      if (filePath) {
        document.getElementById("startup-input-path").value = filePath;
      }
    } else {
      const path = prompt("Nhập đường dẫn file thực thi (*.exe):", "C:\\Program Files\\Example\\app.exe");
      if (path) document.getElementById("startup-input-path").value = path;
    }
  },

  async saveStartupFromModal() {
    const oldName = document.getElementById("startup-old-name").value;
    const oldLocation = document.getElementById("startup-old-location")?.value || "";
    const name = document.getElementById("startup-input-name").value.trim();
    const path = document.getElementById("startup-input-path").value.trim();
    const location = document.getElementById("startup-input-location").value;

    if (!name || !path) {
      alert("Vui lòng nhập đầy đủ Value Name và Value Data!");
      return;
    }

    this.addLog("info", `Đang lưu khoản khởi động: ${name}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.save_startup_entry(name, path, location, oldName, oldLocation);
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
      this.closeStartupModal();
      this.loadStartupEntries();
    } else {
      alert(`[MOCK] Đã lưu khoản khởi động ${name}!`);
      this.closeStartupModal();
    }
  },

  async deleteStartupEntry(name, location, path) {
    if (confirm(`⚠️ Bạn có chắc chắn muốn XÓA khoản khởi động:\n\n${name} (${location})?\n\nThao tác này KHÔNG THỂ HOÀN TÁC!`)) {
      this.addLog("info", `Đang xóa khoản khởi động ${name}...`);
      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.delete_startup_entry(name, location, path);
        this.addLog(res.success ? "success" : "error", res.message);
        this.loadStartupEntries();
      } else {
        alert(`[MOCK] Đã xóa ${name}!`);
      }
    }
  },

  async runStartupEntry(path) {
    this.addLog("info", `Đang thực thi file: ${path}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.run_startup_entry(path);
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
    }
  },

  async loadInstalledApps(category = null) {
    if (category) {
      this.currentUninstallCategory = category;
    } else if (!this.currentUninstallCategory) {
      this.currentUninstallCategory = 'all';
    }

    // Default sort: install_date descending (newest first)
    if (!this.uninstallSortCol) {
      this.uninstallSortCol = 'install_date';
      this.uninstallSortDir = 'desc';
    }

    const catName = String(this.currentUninstallCategory || 'all').toUpperCase();
    const tbody = document.getElementById("uninstall-list-body");
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">🔄 Đang quét danh sách phần mềm đã cài đặt (${catName})...</td></tr>`;
    }

    this.addLog("info", `Đang quét phần mềm (${this.currentUninstallCategory})...`);

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.get_installed_apps(this.currentUninstallCategory);
        if (Array.isArray(res)) {
          this.installedApps = res;
          this.addLog("success", `Đã tìm thấy ${this.installedApps.length} phần mềm đã cài đặt.`);
          this.renderUninstallAppsTable();
        } else if (res && res.success) {
          this.installedApps = res.data || [];
          this.addLog("success", `Đã tìm thấy ${this.installedApps.length} phần mềm đã cài đặt.`);
          this.renderUninstallAppsTable();
        } else {
          this.addLog("error", "Không thể lấy danh sách phần mềm.");
          if (tbody) tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">❌ Lỗi: ${res ? (res.message || res.summary || JSON.stringify(res)) : 'Unknown'}</td></tr>`;
        }
      } catch (err) {
        console.error("Lỗi get_installed_apps:", err);
        this.addLog("error", `Lỗi quét phần mềm: ${err.message}`);
        if (tbody) tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">❌ Lỗi quét phần mềm: ${err.message}</td></tr>`;
      }
    } else {
      this.installedApps = [
        { display_name: "UltraViewer", publisher: "DucFPT", install_date: "20260115", display_version: "6.6", estimated_size: 15360, uninstall_cmd: '"C:\\Program Files (x86)\\UltraViewer\\unins000.exe"', install_location: "C:\\Program Files (x86)\\UltraViewer", reg_key_name: "UltraViewer", icon_b64: "", is_store: false }
      ];
      this.renderUninstallAppsTable();
    }
  },

  sortUninstallBy(col) {
    if (this.uninstallSortCol === col) {
      // Toggle direction
      this.uninstallSortDir = (this.uninstallSortDir === 'asc') ? 'desc' : 'asc';
    } else {
      this.uninstallSortCol = col;
      // Default direction per column type
      this.uninstallSortDir = (col === 'install_date' || col === 'estimated_size') ? 'desc' : 'asc';
    }
    this.renderUninstallAppsTable();
  },

  filterUninstallCategory(category, btnEl) {
    if (btnEl && btnEl.parentElement) {
      const btns = btnEl.parentElement.querySelectorAll("button");
      btns.forEach(b => {
        b.className = "btn btn-slate-light btn-sm";
      });
      btnEl.className = "btn btn-primary btn-sm";
    }
    this.loadInstalledApps(category);
  },

  searchUninstallApps() {
    this.renderUninstallAppsTable();
  },

  renderUninstallAppsTable() {
    const tbody = document.getElementById("uninstall-list-body");
    const badge = document.getElementById("uninstall-count-badge");
    const searchInput = document.getElementById("uninstall-search-input");
    const query = searchInput ? searchInput.value.toLowerCase().trim() : "";

    if (!tbody) return;

    this.filteredInstalledApps = this.installedApps.filter(app => {
      if (!query) return true;
      const nameMatch = (app.display_name || "").toLowerCase().includes(query);
      const pubMatch = (app.publisher || "").toLowerCase().includes(query);
      return nameMatch || pubMatch;
    });

    // ── Apply sorting ──────────────────────────────────────────────────────
    const col = this.uninstallSortCol || 'install_date';
    const dir = this.uninstallSortDir || 'desc';
    this.filteredInstalledApps = [...this.filteredInstalledApps].sort((a, b) => {
      let va = a[col];
      let vb = b[col];
      if (col === 'estimated_size') {
        va = Number(va) || 0;
        vb = Number(vb) || 0;
      } else if (col === 'install_date') {
        // Normalize to comparable string: YYYYMMDD or YYYY-MM-DD → strip dashes
        va = String(va || '').replace(/-/g, '') || '00000000';
        vb = String(vb || '').replace(/-/g, '') || '00000000';
      } else {
        va = String(va || '').toLowerCase();
        vb = String(vb || '').toLowerCase();
      }
      if (va < vb) return dir === 'asc' ? -1 : 1;
      if (va > vb) return dir === 'asc' ? 1 : -1;
      return 0;
    });

    // ── Update sort arrows in header ───────────────────────────────────────
    const sortCols = ['display_name', 'publisher', 'install_date', 'estimated_size', 'display_version'];
    sortCols.forEach(c => {
      const th = document.querySelector(`.sort-col[data-col="${c}"]`);
      const arrow = document.getElementById(`sort-arrow-${c}`);
      if (th) th.classList.remove('sort-active');
      if (arrow) arrow.textContent = '';
      if (c === col) {
        if (th) th.classList.add('sort-active');
        if (arrow) arrow.textContent = dir === 'asc' ? ' ▲' : ' ▼';
      }
    });

    if (badge) {
      badge.innerText = `${this.filteredInstalledApps.length} phần mềm`;
    }

    if (this.filteredInstalledApps.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">Không tìm thấy phần mềm phù hợp.</td></tr>`;
      return;
    }

    tbody.innerHTML = this.filteredInstalledApps.map((app, idx) => {
      let iconHtml = app.is_store ? '📱' : '📦';
      let iconData = app.icon_b64 || app.icon;
      if (iconData) {
        let imgSrc = iconData.startsWith("data:") ? iconData : `data:image/png;base64,${iconData}`;
        iconHtml = `<img src="${imgSrc}" style="width: 22px; height: 22px; object-fit: contain; vertical-align: middle; border-radius: 3px;" alt="icon">`;
      }

      const sizeMB = app.estimated_size ? (app.estimated_size / 1024).toFixed(1) + " MB" : "-";
      let formattedDate = app.install_date || "-";
      if (app.install_date && app.install_date.length === 8) {
        formattedDate = `${app.install_date.substring(6,8)}/${app.install_date.substring(4,6)}/${app.install_date.substring(0,4)}`;
      }

      const pub = app.publisher || '<span style="color:#94a3b8; font-style: italic;">Không rõ</span>';
      const ver = app.display_version || '<span style="color:#94a3b8;">-</span>';

      return `
        <tr style="border-bottom: 1px solid #f1f5f9; transition: background 0.15s;" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='transparent'">
          <td style="text-align: center; color: #64748b; padding: 8px;">${idx + 1}</td>
          <td style="padding: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span>${iconHtml}</span>
              <strong style="color: #1e293b; font-size: 13px;">${this.escapeHtml(app.display_name)}</strong>
              ${app.is_store ? '<span style="background:#e0f2fe; color:#0369a1; font-size:10px; padding:1px 5px; border-radius:4px; font-weight:600;">Store App</span>' : ''}
            </div>
          </td>
          <td style="padding: 8px; color: #475569;">${pub}</td>
          <td style="text-align: center; padding: 8px; color: #64748b; font-size: 12px;">${formattedDate}</td>
          <td style="text-align: center; padding: 8px; color: #64748b; font-size: 12px; font-weight: 500;">${sizeMB}</td>
          <td style="text-align: center; padding: 8px; color: #64748b; font-size: 12px;">${ver}</td>
          <td style="text-align: right; padding: 8px; white-space: nowrap;">
            <button class="btn btn-danger-gradient btn-sm" onclick="app.openUninstallWizard(${idx})" style="padding: 4px 10px; font-size: 12px; font-weight: 600;" title="Gỡ cài đặt siêu sạch - Your Uninstaller!">
              <span>🗑️</span> Gỡ Siêu Sạch
            </button>
            <button class="btn btn-slate-light btn-sm" onclick="app.openAppFolderByIndex(${idx})" style="padding: 4px 8px; font-size: 12px; margin-left: 4px;" title="Mở thư mục cài đặt">
              📂 Thư Mục
            </button>
          </td>
        </tr>
      `;
    }).join("");
  },

  openAppFolderByIndex(idx) {
    const item = this.filteredInstalledApps[idx];
    if (!item) return;
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.open_app_folder(item.install_location, item.display_name);
    } else {
      alert(`[MOCK] Mở thư mục: ${item.install_location || item.display_name}`);
    }
  },

  openUninstallWizard(idx) {
    const item = this.filteredInstalledApps[idx];
    if (!item) return;

    this.currentWizApp = item;

    const nameEl = document.getElementById("wiz-app-name");
    if (nameEl) nameEl.innerText = item.display_name;

    const iconImg = document.getElementById("wiz-app-icon") || document.getElementById("wiz-app-icon-img");
    const iconFallback = document.getElementById("wiz-app-icon-fallback");

    let wizIconData = item.icon_b64 || item.icon;
    if (wizIconData && iconImg && iconFallback) {
      let wizImgSrc = wizIconData.startsWith("data:") ? wizIconData : `data:image/png;base64,${wizIconData}`;
      iconImg.src = wizImgSrc;
      iconImg.style.display = "block";
      iconFallback.style.display = "none";
    } else if (iconImg && iconFallback) {
      iconImg.style.display = "none";
      iconFallback.style.display = "inline-block";
      iconFallback.innerText = item.is_store ? "📱" : "Yu";
    }

    const step1 = document.getElementById("wiz-step-1");
    const step1Badge = document.getElementById("wiz-step-1-badge");
    const step1Status = document.getElementById("wiz-step-1-status");

    const step2 = document.getElementById("wiz-step-2");
    const step2Badge = document.getElementById("wiz-step-2-badge");
    const step2Status = document.getElementById("wiz-step-2-status");
    const step2Details = document.getElementById("wiz-step-2-details");

    const step3 = document.getElementById("wiz-step-3");
    const step3Badge = document.getElementById("wiz-step-3-badge");
    const step3Status = document.getElementById("wiz-step-3-status");
    const step3Details = document.getElementById("wiz-step-3-details");

    if (step1) step1.style.opacity = "1";
    if (step1Badge) { step1Badge.style.background = "#f59e0b"; step1Badge.innerText = "1"; }
    if (step1Status) { step1Status.style.background = "#fef3c7"; step1Status.style.color = "#d97706"; step1Status.innerText = "Sẵn sàng"; }

    if (step2) step2.style.opacity = "0.6";
    if (step2Badge) { step2Badge.style.background = "#94a3b8"; step2Badge.innerText = "2"; }
    if (step2Status) { step2Status.style.background = "#f1f5f9"; step2Status.style.color = "#64748b"; step2Status.innerText = "Chờ bước 1"; }
    if (step2Details) { step2Details.style.display = "none"; step2Details.innerHTML = ""; }

    if (step3) step3.style.opacity = "0.6";
    if (step3Badge) { step3Badge.style.background = "#94a3b8"; step3Badge.innerText = "3"; }
    if (step3Status) { step3Status.style.background = "#f1f5f9"; step3Status.style.color = "#64748b"; step3Status.innerText = "Chờ bước 2"; }
    if (step3Details) { step3Details.style.display = "none"; step3Details.innerHTML = ""; }

    const summaryMsg = document.getElementById("wiz-summary-msg");
    if (summaryMsg) {
      summaryMsg.style.color = "#0284c7";
      summaryMsg.style.background = "#f0f9ff";
      summaryMsg.style.border = "1px solid #bae6fd";
      summaryMsg.innerText = 'Nhấn "Bắt Đầu Gỡ Sạch" để tiến hành quy trình 3 bước gỡ cài đặt.';
    }

    const btnStart = document.getElementById("wiz-btn-start");
    const btnCancel = document.getElementById("wiz-btn-cancel");
    const btnSkip = document.getElementById("wiz-btn-skip");
    if (btnStart) { btnStart.style.display = "inline-flex"; btnStart.disabled = false; }
    if (btnCancel) {
      btnCancel.innerText = "Hủy Bỏ";
      btnCancel.className = "btn btn-slate-light";
      btnCancel.style.padding = "7px 18px";
      btnCancel.disabled = false;
    }
    if (btnSkip) {
      btnSkip.style.display = "none";
      btnSkip.disabled = false;
      btnSkip.innerHTML = "<span>⏭️</span> Đã Gỡ Xong - Quét Sạch Ngay";
    }

    const modal = document.getElementById("uninstall-wizard-modal");
    if (modal) modal.style.display = "flex";
  },

  closeUninstallWizard() {
    const modal = document.getElementById("uninstall-wizard-modal");
    if (modal) modal.style.display = "none";
    this.currentWizApp = null;
  },

  async skipUninstallStep1() {
    const btnSkip = document.getElementById("wiz-btn-skip");
    if (btnSkip) {
      btnSkip.disabled = true;
      btnSkip.innerHTML = "<span>⏳</span> Đang chuyển sang Quét Dọn...";
    }
    const summaryMsg = document.getElementById("wiz-summary-msg");
    if (summaryMsg) {
      summaryMsg.style.color = "#0284c7";
      summaryMsg.innerText = "Đang chuyển ngay sang Bước 2 & 3: Quét sạch Registry & Thư mục rác...";
    }
    this.addLog("info", "Đã nhận lệnh bỏ qua chờ uninstaller. Đang tiến hành quét sạch...");
    if (window.pywebview && window.pywebview.api && window.pywebview.api.skip_uninstall_step1) {
      try {
        await window.pywebview.api.skip_uninstall_step1();
      } catch (err) {
        console.error("Lỗi skip_uninstall_step1:", err);
      }
    }
  },

  async executeDeepCleanStep() {
    if (!this.currentWizApp) return;

    const appItem = this.currentWizApp;
    const btnStart = document.getElementById("wiz-btn-start");
    const btnCancel = document.getElementById("wiz-btn-cancel");
    const btnSkip = document.getElementById("wiz-btn-skip");
    const summaryMsg = document.getElementById("wiz-summary-msg");

    if (btnStart) btnStart.style.display = "none";
    if (btnCancel) {
      btnCancel.disabled = false; // Always allow user to cancel or close
    }
    if (btnSkip) {
      btnSkip.style.display = "inline-flex";
      btnSkip.disabled = false;
      btnSkip.innerHTML = "<span>⏭️</span> Đã Gỡ Xong - Quét Sạch Ngay";
    }

    const step1Badge = document.getElementById("wiz-step-1-badge");
    const step1Status = document.getElementById("wiz-step-1-status");
    if (step1Status) {
      step1Status.style.background = "#fef3c7";
      step1Status.style.color = "#d97706";
      step1Status.innerText = "⚡ Đang chạy Uninstaller...";
    }
    if (summaryMsg) {
      summaryMsg.style.color = "#d97706";
      summaryMsg.innerText = "Đang mở trình gỡ cài đặt gốc... Hãy hoàn tất cửa sổ gỡ cài đặt nếu nó hiện ra. Bấm nút 'Đã Gỡ Xong - Quét Sạch Ngay' nếu trình gỡ đã đóng.";
    }

    this.addLog("info", `Bắt đầu gỡ cài đặt 3 bước cho '${appItem.display_name}'...`);

    let res = null;
    if (window.pywebview && window.pywebview.api) {
      try {
        res = await window.pywebview.api.run_deep_clean_uninstall(
          appItem.display_name,
          appItem.uninstall_cmd,
          appItem.install_location,
          appItem.reg_key_name,
          appItem.is_store
        );
      } catch (err) {
        console.error("Lỗi run_deep_clean_uninstall:", err);
        res = { success: false, step1_success: false, step1_msg: err.message, registry_cleaned: [], folders_cleaned: [] };
      }
    } else {
      await new Promise(r => setTimeout(r, 1500));
      res = {
        success: true,
        step1_success: true,
        registry_cleaned: ["HKCU\\SOFTWARE\\" + appItem.display_name, "HKLM\\SOFTWARE\\" + appItem.display_name],
        folders_cleaned: [appItem.install_location || "C:\\Program Files\\" + appItem.display_name, "AppData\\Roaming\\" + appItem.display_name]
      };
    }

    if (btnSkip) btnSkip.style.display = "none";

    // ── STEP 1 STATUS ─────────────────────────────────────────────────────
    const step1Success = res && res.step1_success === true;
    if (step1Badge) {
      step1Badge.style.background = step1Success ? "#10b981" : "#f59e0b";
      step1Badge.innerText = step1Success ? "✓" : "⚠";
    }
    if (step1Status) {
      if (step1Success) {
        step1Status.style.background = "#dcfce7"; step1Status.style.color = "#15803d"; step1Status.innerText = "Đã gỡ xong!";
      } else {
        step1Status.style.background = "#fef3c7"; step1Status.style.color = "#d97706"; step1Status.innerText = "⚠ Chưa gỡ hoàn toàn";
      }
    }

    const step2 = document.getElementById("wiz-step-2");
    const step2Badge = document.getElementById("wiz-step-2-badge");
    const step2Status = document.getElementById("wiz-step-2-status");
    const step2Details = document.getElementById("wiz-step-2-details");

    const regCount = (res.registry_cleaned || []).length;
    if (step2) step2.style.opacity = "1";
    if (step2Badge) { step2Badge.style.background = "#10b981"; step2Badge.innerText = "✓"; }
    if (step2Status) {
      step2Status.style.background = "#dcfce7";
      step2Status.style.color = "#15803d";
      step2Status.innerText = regCount > 0 ? `Đã dọn ${regCount} key` : "Sạch (0 key)";
    }
    if (step2Details && regCount > 0) {
      step2Details.style.display = "block";
      step2Details.innerHTML = "<strong>🔑 Registry keys đã dọn:</strong><br>" + res.registry_cleaned.map(k => `• ${this.escapeHtml(k)}`).join("<br>");
    } else if (step2Details) {
      step2Details.style.display = "block";
      step2Details.innerHTML = "<em>Không phát hiện Registry rác còn sót.</em>";
    }

    const step3 = document.getElementById("wiz-step-3");
    const step3Badge = document.getElementById("wiz-step-3-badge");
    const step3Status = document.getElementById("wiz-step-3-status");
    const step3Details = document.getElementById("wiz-step-3-details");

    const folderCount = (res.folders_cleaned || []).length;
    if (step3) step3.style.opacity = "1";
    if (step3Badge) { step3Badge.style.background = "#10b981"; step3Badge.innerText = "✓"; }
    if (step3Status) {
      step3Status.style.background = "#dcfce7";
      step3Status.style.color = "#15803d";
      step3Status.innerText = folderCount > 0 ? `Đã dọn ${folderCount} mục` : "Sạch (0 mục)";
    }
    if (step3Details && folderCount > 0) {
      step3Details.style.display = "block";
      step3Details.innerHTML = "<strong>📁 Thư mục dư thừa đã dọn:</strong><br>" + res.folders_cleaned.map(f => `• ${this.escapeHtml(f)}`).join("<br>");
    } else if (step3Details) {
      step3Details.style.display = "block";
      step3Details.innerHTML = "<em>Thư mục cài đặt gốc đã được dọn sạch hoàn toàn.</em>";
    }

    // ── SUMMARY ────────────────────────────────────────────────────────────
    if (summaryMsg) {
      if (step1Success) {
        summaryMsg.style.color = "#15803d";
        summaryMsg.style.background = "#dcfce7";
        summaryMsg.style.border = "1px solid #bbf7d0";
        summaryMsg.innerText = `🎉 Hoàn tất gỡ sạch 100%! Đã xóa triệt để phần mềm, ${regCount} Registry keys và ${folderCount} Thư mục rác.`;
      } else {
        summaryMsg.style.color = "#b45309";
        summaryMsg.style.background = "#fffbeb";
        summaryMsg.style.border = "1px solid #fde68a";
        summaryMsg.innerText = `⚠️ Phần mềm có thể chưa được gỡ hoàn toàn. Đã dọn ${regCount} Registry keys & ${folderCount} Thư mục rác phụ.`;
      }
    }

    if (btnStart) btnStart.style.display = "none";
    if (btnCancel) {
      btnCancel.innerText = "Đóng";
      btnCancel.className = "btn btn-primary-gradient";
      btnCancel.style.padding = "7px 24px";
      btnCancel.style.fontWeight = "700";
      btnCancel.disabled = false;
    }

    if (step1Success) {
      this.addLog("success", `Đã gỡ siêu sạch '${appItem.display_name}'. Cleaned: ${regCount} Reg Keys, ${folderCount} Thư mục.`);
    } else {
      this.addLog("warn", `Gỡ cài đặt '${appItem.display_name}' có thể chưa hoàn tất. Dọn: ${regCount} Reg Keys, ${folderCount} Thư mục rác.`);
    }
    this.loadInstalledApps();
  },


  escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  },

  // ── BITLOCKER DRIVE MANAGER ───────────────────────────────────────────
  async loadBitlockerDrives() {
    const grid = document.getElementById("bitlocker-drives-grid");
    if (grid) {
      grid.innerHTML = `<div class="text-center py-4 text-muted" style="grid-column: 1 / -1;">🔄 Đang kiểm tra trạng thái BitLocker trên các ổ cứng...</div>`;
    }

    this.addLog("info", "Đang quét trạng thái mã hóa BitLocker tất cả ổ đĩa...");

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.get_bitlocker_drives();
        if (res && res.success) {
          this.bitlockerDrives = res.data || [];
          this.addLog("success", `Đã tìm thấy ${this.bitlockerDrives.length} phân vùng ổ đĩa.`);
          this.renderBitlockerDrivesGrid();
        } else {
          this.addLog("error", "Không thể lấy trạng thái BitLocker.");
          if (grid) grid.innerHTML = `<div class="text-center text-danger py-4" style="grid-column: 1 / -1;">❌ Lỗi: ${res ? res.message : 'Unknown'}</div>`;
        }
      } catch (err) {
        console.error("Lỗi get_bitlocker_drives:", err);
        this.addLog("error", `Lỗi quét BitLocker: ${err.message}`);
        if (grid) grid.innerHTML = `<div class="text-center text-danger py-4" style="grid-column: 1 / -1;">❌ Lỗi: ${err.message}</div>`;
      }
    } else {
      this.bitlockerDrives = [
        { drive: "C:", label: "System OS", size: "237.4 GB", free_space: "24.4 GB", protection_status: "OFF", protection_text: "🔓 Đã Tắt BitLocker", encryption_pct: 0, conversion_status: "Fully Decrypted", encryption_method: "None", lock_status: "Unlocked" },
        { drive: "D:", label: "DATA", size: "931.5 GB", free_space: "173.3 GB", protection_status: "OFF", protection_text: "🔓 Đã Tắt BitLocker", encryption_pct: 0, conversion_status: "Fully Decrypted", encryption_method: "None", lock_status: "Unlocked" }
      ];
      this.renderBitlockerDrivesGrid();
    }
  },

  renderBitlockerDrivesGrid() {
    const grid = document.getElementById("bitlocker-drives-grid");
    if (!grid) return;

    if (!this.bitlockerDrives || this.bitlockerDrives.length === 0) {
      grid.innerHTML = `<div class="text-center py-4 text-muted" style="grid-column: 1 / -1;">Không tìm thấy ổ đĩa nào.</div>`;
      return;
    }

    grid.innerHTML = this.bitlockerDrives.map(d => {
      let statusBadge = "";
      let actionBtn = "";

      if (d.protection_status === "ON") {
        statusBadge = `<span style="background: #dcfce7; color: #15803d; font-weight: 700; padding: 4px 10px; border-radius: 12px; font-size: 11px;">🔒 ĐÃ BẬT (Protected)</span>`;
        actionBtn = `
          <button class="btn btn-danger-solid w-100 py-2 font-semibold text-xs mt-3" onclick="app.setBitlocker('${d.drive}', 'disable')">
            <span>🔓</span> Tắt BitLocker (manage-bde -off)
          </button>
        `;
      } else if (d.protection_status === "TRANSITION") {
        const isDecryp = d.conversion_status.toLowerCase().includes("decryp");
        const actionType = isDecryp ? "disable" : "enable";
        const btnText = isDecryp ? "⚡ Theo Dõi Tiến Độ Giải Mã" : "⚡ Theo Dõi Tiến Độ Mã Hóa";
        statusBadge = `<span style="background: #fef3c7; color: #d97706; font-weight: 700; padding: 4px 10px; border-radius: 12px; font-size: 11px;">⚡ ${d.conversion_status} (${d.encryption_pct}%)</span>`;
        actionBtn = `
          <button class="btn btn-warning-solid w-100 py-2 font-semibold text-xs mt-3" onclick="app.startBitlockerPolling('${d.drive}', '${actionType}')">
            <span>⚡</span> ${btnText}
          </button>
        `;
      } else {
        statusBadge = `<span style="background: #f1f5f9; color: #64748b; font-weight: 700; padding: 4px 10px; border-radius: 12px; font-size: 11px;">🔓 ĐÃ TẮT (Unprotected)</span>`;
        actionBtn = `
          <button class="btn btn-primary-gradient w-100 py-2 font-semibold text-xs mt-3" onclick="app.setBitlocker('${d.drive}', 'enable')">
            <span>🔒</span> Bật BitLocker (manage-bde -on)
          </button>
        `;
      }

      let keyBtn = "";
      if (d.protection_status === "ON" || d.protection_status === "TRANSITION" || d.encryption_pct > 0) {
        keyBtn = `
          <button class="btn btn-sky-outline w-100 py-2 font-semibold text-xs mt-2" onclick="app.getBitlockerRecoveryKey('${d.drive}')">
            <span>🔑</span> Lấy Recovery Key Khôi Phục
          </button>
        `;
      }

      return `
        <div class="ui-card shadow-sm" style="background: white; border-radius: 10px; padding: 16px; border: 1px solid #e2e8f0; display: flex; flex-direction: column; justify-content: space-between;">
          <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 24px;">💾</span>
                <div>
                  <strong style="font-size: 16px; color: #1e293b;">Ổ ${d.drive} ${d.label ? '[' + this.escapeHtml(d.label) + ']' : ''}</strong>
                  <div style="font-size: 12px; color: #64748b;">${d.free_space} trống / ${d.size}</div>
                </div>
              </div>
              <div>${statusBadge}</div>
            </div>

            <div style="font-size: 12px; color: #475569; background: #f8fafc; padding: 8px 12px; border-radius: 6px; margin-top: 8px;">
              <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span>Trạng thái chuyển đổi:</span>
                <strong style="color: #0369a1;">${this.escapeHtml(d.conversion_status)}</strong>
              </div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span>Tỷ lệ mã hóa:</span>
                <strong>${d.encryption_pct}%</strong>
              </div>
              <div style="display: flex; justify-content: space-between;">
                <span>Thuật toán mã hóa:</span>
                <span style="color: #64748b;">${this.escapeHtml(d.encryption_method)}</span>
              </div>
            </div>
          </div>

          <div>
            ${actionBtn}
            ${keyBtn}
          </div>
        </div>
      `;
    }).join("");
  },

  currentKeyDrive: null,
  currentRecoveryKeys: [],

  async getBitlockerRecoveryKey(drive) {
    this.currentKeyDrive = drive;
    this.currentRecoveryKeys = [];

    const modal = document.getElementById("bitlocker-key-modal");
    const driveSpan = document.getElementById("bl-key-modal-drive");
    const listContainer = document.getElementById("bl-key-modal-keys-list");

    if (driveSpan) driveSpan.textContent = drive;
    if (listContainer) {
      listContainer.innerHTML = `<div style="text-align: center; padding: 20px; color: #64748b;">🔄 Đang kiểm tra và lấy Recovery Key cho ổ ${drive}...</div>`;
    }
    if (modal) modal.style.display = "flex";

    this.addLog("info", `Đang truy vấn Recovery Key cho ổ ${drive}...`);

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.get_bitlocker_recovery_key(drive);
        if (res && res.success && res.keys && res.keys.length > 0) {
          this.currentRecoveryKeys = res.keys;
          this.addLog("success", `Đã lấy thành công ${res.keys.length} Recovery Key cho ổ ${drive}.`);
          this.renderRecoveryKeysList(res.keys);
        } else {
          this.addLog("warn", res ? res.message : "Không tìm thấy Key.");
          if (listContainer) {
            listContainer.innerHTML = `
              <div style="background: #fff1f2; border: 1px solid #fecdd3; border-radius: 8px; padding: 14px; text-align: center; color: #e11d48; font-size: 13px;">
                ⚠️ ${res ? res.message : 'Không tìm thấy Recovery Key cho ổ đĩa này.'}
              </div>
            `;
          }
        }
      } catch (err) {
        console.error("Lỗi get_bitlocker_recovery_key:", err);
        this.addLog("error", `Lỗi lấy Recovery Key: ${err.message}`);
        if (listContainer) {
          listContainer.innerHTML = `<div style="color: #ef4444; padding: 14px; text-align: center;">❌ Lỗi: ${err.message}</div>`;
        }
      }
    } else {
      this.currentRecoveryKeys = ["123456-789012-345678-901234-567890-123456-789012-345678"];
      this.renderRecoveryKeysList(this.currentRecoveryKeys);
    }
  },

  renderRecoveryKeysList(keys) {
    const listContainer = document.getElementById("bl-key-modal-keys-list");
    if (!listContainer) return;

    listContainer.innerHTML = keys.map((key, idx) => `
      <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; display: flex; align-items: center; justify-content: space-between; gap: 8px;">
        <div style="font-family: 'Consolas', 'Courier New', monospace; font-size: 14px; font-weight: 700; color: #0284c7; letter-spacing: 0.5px; word-break: break-all;">
          ${this.escapeHtml(key)}
        </div>
        <button class="btn btn-sky-outline btn-sm" onclick="app.copyBitlockerRecoveryKey('${key}', this)" style="white-space: nowrap; padding: 4px 10px; font-size: 12px;">
          <span>📋</span> Sao Chép
        </button>
      </div>
    `).join("");
  },

  copyBitlockerRecoveryKey(key, btnElem) {
    if (!key) return;
    navigator.clipboard.writeText(key).then(() => {
      this.addLog("success", `Đã sao chép Recovery Key: ${key}`);
      if (btnElem) {
        const oldText = btnElem.innerHTML;
        btnElem.innerHTML = `<span>✅</span> Đã Chép!`;
        btnElem.style.background = "#10b981";
        btnElem.style.color = "#ffffff";
        btnElem.style.borderColor = "#10b981";
        setTimeout(() => {
          btnElem.innerHTML = oldText;
          btnElem.style.background = "";
          btnElem.style.color = "";
          btnElem.style.borderColor = "";
        }, 2000);
      } else {
        alert("Đã sao chép Recovery Key vào bộ nhớ tạm (Clipboard)!");
      }
    }).catch(err => {
      prompt("Vui lòng sao chép thủ công:", key);
    });
  },

  async exportBitlockerRecoveryKeyFile() {
    if (!this.currentKeyDrive) {
      alert("Vui lòng chọn ổ đĩa!");
      return;
    }
    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.export_bitlocker_recovery_key(this.currentKeyDrive);
        this.addLog(res.success ? "success" : "error", res.message);
        alert(res.message);
      } catch (err) {
        alert(`Lỗi xuất file: ${err.message}`);
      }
    } else {
      alert(`[MOCK] Đã xuất Recovery Key của ổ ${this.currentKeyDrive} ra Desktop!`);
    }
  },

  closeBitlockerKeyModal() {
    const modal = document.getElementById("bitlocker-key-modal");
    if (modal) modal.style.display = "none";
  },


  async setBitlocker(drive, action) {
    const actionText = action === "disable" ? "TẮT" : "BẬT";
    const cmdText = action === "disable" ? `manage-bde -off ${drive}` : `manage-bde -on ${drive} -used`;

    if (!confirm(`Bạn có chắc chắn muốn ${actionText} BitLocker trên ổ ${drive}?\nLệnh thực hiện: ${cmdText}\n\n⚠️ Lưu ý: Cần chạy phần mềm với quyền Administrator!`)) {
      return;
    }

    const drawer = document.getElementById("bitlocker-progress-drawer");
    const title = document.getElementById("bl-drawer-title");
    const badge = document.getElementById("bl-drawer-badge");
    const msg = document.getElementById("bl-drawer-msg");
    const bar = document.getElementById("bl-drawer-bar");
    const pct = document.getElementById("bl-drawer-pct");
    const btnClose = document.getElementById("bl-drawer-close");

    if (drawer) drawer.style.display = "block";
    if (title) title.innerText = `⏳ Đang gửi lệnh ${actionText} BitLocker trên ổ ${drive}...`;
    if (badge) {
      badge.style.background = "#fef3c7";
      badge.style.color = "#d97706";
      badge.innerText = "Đang xử lý...";
    }
    if (msg) msg.innerText = `Đang chạy: ${cmdText}\nVui lòng chờ (tối đa 30 giây)...`;
    if (bar) bar.style.width = "10%";
    if (pct) pct.innerText = "Đang gửi lệnh...";
    if (btnClose) btnClose.style.display = "none";

    this.addLog("info", `Đang chạy lệnh ${cmdText}...`);

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.set_bitlocker(drive, action);
        if (res && res.success) {
          this.addLog("success", res.message);
          if (title) title.innerText = `⚡ Đang theo dõi tiến độ BitLocker trên ổ ${drive}...`;
          if (badge) {
            badge.style.background = "#fef3c7";
            badge.style.color = "#d97706";
            badge.innerText = action === "disable" ? "Đang giải mã" : "Đang mã hóa";
          }
          if (msg) msg.innerText = `⚡ ${res.message}\nĐang theo dõi tiến độ thời gian thực...`;
          if (bar) bar.style.width = "15%";
          this.startBitlockerPolling(drive, action);
        } else {
          // Lỗi thực sự — hiển thị ngay
          const errMsg = res ? res.message : "Không thể thực hiện lệnh BitLocker.";
          this.addLog("error", `Lỗi ${actionText} BitLocker ổ ${drive}: ${errMsg}`);
          if (title) title.innerText = `❌ Thất bại: ${actionText} BitLocker ổ ${drive}`;
          if (badge) { badge.style.background = "#fee2e2"; badge.style.color = "#991b1b"; badge.innerText = "Thất bại"; }
          if (msg) msg.innerText = errMsg;
          if (bar) bar.style.width = "0%";
          if (pct) pct.innerText = "Thất bại";
          if (btnClose) btnClose.style.display = "inline-block";
          alert(`❌ Lỗi ${actionText} BitLocker:\n\n${errMsg}`);
        }
      } catch (err) {
        console.error("Lỗi set_bitlocker:", err);
        const errMsg = `Lỗi kết nối API: ${err.message || err}`;
        this.addLog("error", errMsg);
        if (title) title.innerText = `❌ Lỗi API`;
        if (badge) { badge.style.background = "#fee2e2"; badge.style.color = "#991b1b"; badge.innerText = "Lỗi"; }
        if (msg) msg.innerText = errMsg;
        if (btnClose) btnClose.style.display = "inline-block";
        alert(`❌ ${errMsg}`);
      }
    } else {
      // Mock mode (không có pywebview)
      if (msg) msg.innerText = `[MOCK] Đã phát lệnh ${cmdText}! Đang tiến hành...`;
      this.startBitlockerPolling(drive, action);
    }
  },


  startBitlockerPolling(drive, action) {
    if (this.blPollInterval) {
      clearInterval(this.blPollInterval);
      this.blPollInterval = null;
    }

    this.activeBLDrive = drive;
    const drawer = document.getElementById("bitlocker-progress-drawer");
    const title = document.getElementById("bl-drawer-title");
    const badge = document.getElementById("bl-drawer-badge");
    const msg = document.getElementById("bl-drawer-msg");
    const bar = document.getElementById("bl-drawer-bar");
    const pct = document.getElementById("bl-drawer-pct");
    const btnClose = document.getElementById("bl-drawer-close");

    const isDisable = action === "disable";

    if (drawer) drawer.style.display = "block";
    if (title) title.innerText = `⚡ Đang theo dõi tiến độ BitLocker trên ổ ${drive}...`;
    if (badge) {
      badge.style.background = "#fef3c7";
      badge.style.color = "#d97706";
      badge.innerText = isDisable ? "Đang giải mã" : "Đang mã hóa";
    }
    if (msg) msg.innerText = `Đang theo dõi tiến độ thời gian thực trên ổ ${drive}... Vui lòng chờ...`;
    if (bar) bar.style.width = "5%";
    if (pct) pct.innerText = "Đang kiểm tra tiến độ...";
    if (btnClose) btnClose.style.display = "inline-block";

    const poll = async () => {
      if (window.pywebview && window.pywebview.api) {
        try {
          const res = await window.pywebview.api.get_bitlocker_drive_status(drive);
          if (res && res.success && res.data) {
            const d = res.data;
            const encPct = parseFloat(d.encryption_pct) || 0;
            const convStatus = d.conversion_status || "";
            const protStatus = d.protection_status || "";

            let displayProgress = isDisable ? (100 - encPct) : encPct;
            displayProgress = Math.max(0, Math.min(100, displayProgress));

            if (bar) bar.style.width = `${displayProgress}%`;
            if (pct) pct.innerText = `${displayProgress.toFixed(1)}% hoàn tất (Mức mã hóa: ${encPct}%)`;
            if (msg) msg.innerText = `Đang ${isDisable ? 'giải mã dữ liệu' : 'mã hóa dữ liệu'} ổ ${drive}... Trạng thái: ${convStatus} (${encPct}%)`;

            const isCompleted = isDisable 
              ? (convStatus.toLowerCase().includes("decrypted") || encPct === 0) 
              : (protStatus === "ON" || encPct === 100);

            if (isCompleted) {
              if (this.blPollInterval) {
                clearInterval(this.blPollInterval);
                this.blPollInterval = null;
              }

              if (bar) bar.style.width = "100%";
              if (pct) pct.innerText = "100% HOÀN TẤT";
              if (badge) {
                badge.style.background = "#dcfce7";
                badge.style.color = "#15803d";
                badge.innerText = isDisable ? "Đã Tắt 100%" : "Đã Bật 100%";
              }
              const finishMsg = isDisable 
                ? `🎉 Đã giải mã hoàn tất 100%! BitLocker trên ổ ${drive} đã được TẮT hoàn toàn!`
                : `🎉 Đã mã hóa hoàn tất 100%! BitLocker trên ổ ${drive} đã được BẬT thành công!`;

              if (msg) msg.innerText = finishMsg;
              if (btnClose) btnClose.style.display = "inline-block";

              this.addLog("success", finishMsg);
              this.loadBitlockerDrives();
            }
          }
        } catch (err) {
          console.error("Lỗi polling BitLocker status:", err);
        }
      } else {
        let currentPct = parseFloat(pct.innerText) || 20;
        currentPct += 20;
        if (currentPct >= 100) {
          if (this.blPollInterval) {
            clearInterval(this.blPollInterval);
            this.blPollInterval = null;
          }
          if (bar) bar.style.width = "100%";
          if (pct) pct.innerText = "100% HOÀN TẤT";
          if (msg) msg.innerText = `[MOCK] 🎉 Đã ${isDisable ? 'tắt' : 'bật'} BitLocker hoàn tất 100% trên ổ ${drive}!`;
          if (btnClose) btnClose.style.display = "inline-block";
        } else {
          if (bar) bar.style.width = `${currentPct}%`;
          if (pct) pct.innerText = `${currentPct}% hoàn tất`;
        }
      }
    };

    // Trigger immediate poll
    poll();
    // Then poll every 2s
    this.blPollInterval = setInterval(poll, 2000);
  },

  closeBitlockerProgressDrawer() {
    if (this.blPollInterval) {
      clearInterval(this.blPollInterval);
      this.blPollInterval = null;
    }
    const drawer = document.getElementById("bitlocker-progress-drawer");
    if (drawer) drawer.style.display = "none";
  },

  // ── CLASSIC CONTEXT MENU CONTROLLER ────────────────────────────────────
  async loadClassicMenuStatus() {
    const cardEl = document.getElementById("classic-menu-status-card");
    const textEl = document.getElementById("classic-menu-status-text");
    const descEl = document.getElementById("classic-menu-status-desc");
    const badgeEl = document.getElementById("classic-menu-status-badge");

    if (textEl) textEl.innerText = "🔄 Đang kiểm tra Registry...";

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.get_classic_menu_status();
        if (res && res.success) {
          if (textEl) textEl.innerText = res.status_text;
          if (descEl) descEl.innerText = res.description;
          if (badgeEl) {
            badgeEl.innerText = res.badge_text;
            if (res.enabled) {
              badgeEl.style.background = "#dcfce7";
              badgeEl.style.color = "#15803d";
              if (cardEl) {
                cardEl.style.background = "#f0fdf4";
                cardEl.style.borderColor = "#bbf7d0";
              }
            } else {
              badgeEl.style.background = "#e2e8f0";
              badgeEl.style.color = "#475569";
              if (cardEl) {
                cardEl.style.background = "#f8fafc";
                cardEl.style.borderColor = "#cbd5e1";
              }
            }
          }
        }
      } catch (err) {
        if (textEl) textEl.innerText = "Lỗi kiểm tra trạng thái Registry";
        console.error("Lỗi get_classic_menu_status:", err);
      }
    } else {
      if (textEl) textEl.innerText = "TẮT: Menu Chuột Phải Win 11 Mặc Định (MOCK)";
      if (descEl) descEl.innerText = "Hiện đang dùng giao diện Win11 Mặc định (Mock mode).";
      if (badgeEl) {
        badgeEl.innerText = "⚪ Win11 Default (Mock)";
        badgeEl.style.background = "#e2e8f0";
        badgeEl.style.color = "#475569";
      }
    }
  },

  async setClassicMenuStatus(enable) {
    const actionText = enable ? "Bật Menu Classic Win 10" : "Khôi phục Menu Win 11 Mặc định";
    const textEl = document.getElementById("classic-menu-status-text");
    if (textEl) textEl.innerText = `Đang ${actionText.toLowerCase()}... Vui lòng chờ Windows Explorer làm mới...`;

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.set_classic_menu_status(enable);
        this.addLog(res.success ? "success" : "error", res.message);
        alert(res.message);
        this.loadClassicMenuStatus();
      } catch (err) {
        alert(`Lỗi: ${err.message}`);
        this.loadClassicMenuStatus();
      }
    } else {
      alert(`[MOCK] Đã ${actionText}! Windows Explorer đã được làm mới.`);
      this.loadClassicMenuStatus();
    }
  },

  async restartExplorerProcess() {
    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.restart_explorer_process();
        this.addLog(res.success ? "success" : "error", res.message);
        alert(res.message);
      } catch (err) {
        alert(`Lỗi: ${err.message}`);
      }
    } else {
      alert("[MOCK] Đã khởi động lại Windows Explorer!");
    }
  },

  async optimizeOffice() {
    this.addLog("info", "Đang tối ưu hóa Office (Tắt Spell Check & Protected View)...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.optimize_office();
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
    }
  },

  selectedOfficeVersion: "office365",
  officeInstallPollingTimer: null,

  selectOfficeVersion(code, elem) {
    this.selectedOfficeVersion = code;
    document.querySelectorAll(".office-version-card").forEach(c => {
      c.style.borderColor = "#cbd5e1";
      c.style.background = "#ffffff";
    });
    if (elem) {
      elem.style.borderColor = "#0284c7";
      elem.style.background = "#f0f9ff";
    }
  },

  async startOfficeInstall() {
    const version = this.selectedOfficeVersion || "office365";
    const arch = document.getElementById("office-arch")?.value || "x64";
    const lang = document.getElementById("office-lang")?.value || "vi-vn";

    const versionNames = {
      office365: "Microsoft 365 Apps",
      office2024: "Office 2024 Professional Plus",
      office2021: "Office 2021 Professional Plus",
      office2019: "Office 2019 Professional Plus",
      office2016: "Office 2016 Professional Plus",
      visio: "Visio Professional 2021",
      project: "Project Professional 2021"
    };
    const vname = versionNames[version] || version;

    if (!confirm(`Bạn có chắc chắn muốn cài đặt ẩn ${vname} (${arch}, ${lang}) từ Microsoft CDN?\n\nTIẾN TRÌNH CHẠY NGẦM ĐỘC LẬP: Sau khi bấm bắt đầu, dù bạn có tắt ứng dụng BMAT Tools thì Office vẫn tự động tải & hoàn tất trong nền Windows.`)) {
      return;
    }

    const drawer = document.getElementById("office-install-drawer");
    const bar = document.getElementById("office-install-bar");
    const pct = document.getElementById("office-install-pct");
    const msg = document.getElementById("office-install-msg");
    const badge = document.getElementById("office-install-badge");
    const logBox = document.getElementById("office-install-log");
    const cancelBtn = document.getElementById("office-install-cancel");
    const closeBtn = document.getElementById("office-install-close");

    if (drawer) drawer.style.display = "block";
    if (bar) bar.style.width = "5%";
    if (pct) pct.textContent = "5%";
    if (msg) msg.textContent = `Đang khởi tạo lệnh tải ${vname}...`;
    if (badge) {
      badge.textContent = "ĐANG XỬ LÝ";
      badge.style.background = "#e0f2fe";
      badge.style.color = "#0369a1";
    }
    if (cancelBtn) cancelBtn.style.display = "inline-block";
    if (closeBtn) closeBtn.style.display = "none";
    if (logBox) logBox.innerHTML = `<div>[SYS] Khởi động tiến trình cài đặt ẩn ${vname}...</div>`;

    this.addLog("info", `Đang khởi chạy tiến trình cài đặt ${vname} (${arch})...`);

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.install_office_version(version, arch, lang);
        if (res && res.success) {
          this.addLog("success", res.message);
          this.startOfficeInstallPolling();
        } else {
          const errMsg = res ? res.message : "Không thể khởi chạy cài đặt Office.";
          alert(errMsg);
          if (cancelBtn) cancelBtn.style.display = "inline-block";
          if (closeBtn) closeBtn.style.display = "inline-block";
          this.startOfficeInstallPolling();
        }
      } catch (err) {
        alert(`Lỗi cài đặt Office: ${err.message}`);
        if (closeBtn) closeBtn.style.display = "inline-block";
      }
    } else {
      let mockPct = 10;
      const timer = setInterval(() => {
        mockPct += 15;
        if (bar) bar.style.width = `${mockPct}%`;
        if (pct) pct.textContent = `${mockPct}%`;
        if (msg) msg.textContent = `[MOCK] Đang tải ${vname}... (${mockPct}%)`;
        if (logBox) logBox.innerHTML += `<div>[MOCK] Downloading package ${mockPct}%...</div>`;
        if (mockPct >= 100) {
          clearInterval(timer);
          if (msg) msg.textContent = `[MOCK] Hoàn tất cài đặt ${vname}!`;
          if (cancelBtn) cancelBtn.style.display = "none";
          if (closeBtn) closeBtn.style.display = "inline-block";
        }
      }, 1000);
    }
  },

  async cancelOfficeInstall() {
    if (!confirm("Bạn có chắc chắn muốn hủy tiến trình tải & cài đặt Office đang chạy?")) return;
    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.cancel_office_install();
        this.addLog("warn", res.message || "Đã gửi lệnh hủy cài đặt Office.");
        const badge = document.getElementById("office-install-badge");
        const cancelBtn = document.getElementById("office-install-cancel");
        const closeBtn = document.getElementById("office-install-close");
        const msg = document.getElementById("office-install-msg");
        if (badge) {
          badge.textContent = "ĐÃ HỦY";
          badge.style.background = "#fee2e2";
          badge.style.color = "#dc2626";
        }
        if (msg) msg.textContent = "Đã hủy tiến trình cài đặt Office.";
        if (cancelBtn) cancelBtn.style.display = "none";
        if (closeBtn) closeBtn.style.display = "inline-block";
      } catch (err) {
        alert(`Lỗi khi hủy: ${err.message}`);
      }
    }
  },

  startOfficeInstallPolling() {
    if (this.officeInstallPollingTimer) {
      clearInterval(this.officeInstallPollingTimer);
    }

    this.officeInstallPollingTimer = setInterval(async () => {
      if (window.pywebview && window.pywebview.api) {
        try {
          const res = await window.pywebview.api.get_office_install_progress();
          if (res && res.success && res.data) {
            const data = res.data;
            const bar = document.getElementById("office-install-bar");
            const pct = document.getElementById("office-install-pct");
            const msg = document.getElementById("office-install-msg");
            const badge = document.getElementById("office-install-badge");
            const logBox = document.getElementById("office-install-log");
            const cancelBtn = document.getElementById("office-install-cancel");
            const closeBtn = document.getElementById("office-install-close");

            const pVal = data.percentage || 0;
            if (bar) bar.style.width = `${pVal}%`;
            if (pct) pct.textContent = `${pVal}% hoàn tất`;
            if (msg) msg.textContent = data.message || "Đang xử lý...";
            if (badge) {
              const statusUpper = (data.status || "processing").toUpperCase();
              badge.textContent = statusUpper;
              if (data.status === "completed") {
                badge.style.background = "#dcfce7";
                badge.style.color = "#16a34a";
              } else if (data.status === "error" || data.status === "cancelled") {
                badge.style.background = "#fee2e2";
                badge.style.color = "#dc2626";
              } else {
                badge.style.background = "#e0f2fe";
                badge.style.color = "#0369a1";
              }
            }

            if (logBox && data.output_log && data.output_log.length > 0) {
              logBox.innerHTML = data.output_log.map(l => `<div>${this.escapeHtml(l)}</div>`).join("");
              logBox.scrollTop = logBox.scrollHeight;
            }

            if (data.active) {
              if (cancelBtn) cancelBtn.style.display = "inline-block";
              if (closeBtn) closeBtn.style.display = "none";
            } else {
              if (cancelBtn) cancelBtn.style.display = "none";
              if (closeBtn) closeBtn.style.display = "inline-block";
            }

            if (!data.active || data.status === "completed" || data.status === "error" || data.status === "cancelled") {
              clearInterval(this.officeInstallPollingTimer);
              this.officeInstallPollingTimer = null;
              if (cancelBtn) cancelBtn.style.display = "none";
              if (closeBtn) closeBtn.style.display = "inline-block";
              if (data.status === "completed") {
                this.addLog("success", `Đã hoàn tất cài đặt Office!`);
              } else if (data.status === "error") {
                this.addLog("error", `Tiến trình cài đặt Office kết thúc với lỗi!`);
              }
            }
          }
        } catch (err) {
          console.error("Lỗi poll office install:", err);
        }
      }
    }, 1200);
  },

  closeOfficeInstallDrawer() {
    if (this.officeInstallPollingTimer) {
      clearInterval(this.officeInstallPollingTimer);
      this.officeInstallPollingTimer = null;
    }
    const drawer = document.getElementById("office-install-drawer");
    if (drawer) drawer.style.display = "none";
  },

  async checkExistingOfficeInstall() {
    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.get_office_install_progress();
        if (res && res.success && res.data) {
          const data = res.data;
          const drawer = document.getElementById("office-install-drawer");
          const cancelBtn = document.getElementById("office-install-cancel");
          const closeBtn = document.getElementById("office-install-close");

          if (data.active) {
            if (drawer) drawer.style.display = "block";
            if (cancelBtn) cancelBtn.style.display = "inline-block";
            if (closeBtn) closeBtn.style.display = "none";
            this.startOfficeInstallPolling();
          } else if (data.status && data.status !== "ready") {
            // Previously finished or error
            if (drawer) drawer.style.display = "block";
            if (cancelBtn) cancelBtn.style.display = "none";
            if (closeBtn) closeBtn.style.display = "inline-block";
            
            const bar = document.getElementById("office-install-bar");
            const pct = document.getElementById("office-install-pct");
            const msg = document.getElementById("office-install-msg");
            const badge = document.getElementById("office-install-badge");
            const logBox = document.getElementById("office-install-log");
            if (bar) bar.style.width = `${data.percentage || 0}%`;
            if (pct) pct.textContent = `${data.percentage || 0}% hoàn tất`;
            if (msg) msg.textContent = data.message || "";
            if (badge) badge.textContent = (data.status || "").toUpperCase();
            if (logBox && data.output_log) {
              logBox.innerHTML = data.output_log.map(l => `<div>${this.escapeHtml(l)}</div>`).join("");
            }
          }
        }
      } catch (e) {
        console.error("Lỗi checkExistingOfficeInstall:", e);
      }
    }
  },


  async loadSystemTweaksStatus() {
    if (!window.pywebview || !window.pywebview.api) return;
    try {
      const res = await window.pywebview.api.get_system_tweaks_status();
      if (res && res.success && res.data) {
        this.renderSystemTweaksGrid(res.data);
      }
    } catch (err) {
      console.error("Lỗi lấy trạng thái system tweaks:", err);
    }
  },

  renderSystemTweaksGrid(statusMap = {}) {
    const container = document.getElementById("system-tweaks-grid");
    if (!container) return;

    const tweakItems = [
      { key: 'taskmgr', title: 'Enable Task Manager', icon: '📊', desc: 'Mở trình quản lý tác vụ Task Manager' },
      { key: 'registry', title: 'Enable Registry Editor', icon: '🛠️', desc: 'Mở trình chỉnh sửa Registry (regedit)' },
      { key: 'run', title: 'Enable Run... Command', icon: '🏃', desc: 'Mở hộp thoại Run (Win + R)' },
      { key: 'lowdisk', title: 'Enable LowDisk Notify', icon: '💽', desc: 'Cảnh báo dung lượng ổ đĩa thấp' },
      { key: 'cmd', title: 'Enable CommandPrompt', icon: '💻', desc: 'Mở cửa sổ dòng lệnh CMD' },
      { key: 'camera', title: 'Enable Webcam', icon: '📷', desc: 'Cho phép ứng dụng dùng Webcam' },
      { key: 'fix_hidden', title: 'Fix Hidden Folder', icon: '📁', desc: 'Sửa lỗi file/thư mục bị ẩn hệ thống', actionOnly: true, btnText: 'Sửa Ẩn File' },
      { key: 'repair_taskbar', title: 'Repair TaskBar', icon: '📌', desc: 'Sửa lỗi Taskbar/Start bị đơ lag (Giữ nguyên toàn bộ icon đã ghim)', actionOnly: true, btnText: 'Sửa Taskbar' },
      { key: 'unblock_files', title: 'Unblock Files', icon: '🏷️', desc: 'Bỏ chặn các file tải về bị dán nhãn', actionOnly: true, btnText: 'Bỏ Chặn Files' },
      { key: 'shortcut_arrow', title: 'Enable Shortcut Arrow', icon: '↗️', desc: 'Mũi tên trên icon Shortcut Desktop' },
      { key: 'shortcut_prefix', title: 'Enable "Shortcut to"', icon: '✂️', desc: 'Tiền tố "Shortcut to" khi tạo shortcut' },
      { key: 'autorun', title: 'Enable Autorun All Drives', icon: '▶️', desc: 'Tự động chạy USB & ổ đĩa (Autorun)' }
    ];

    let html = '';
    tweakItems.forEach(item => {
      const isEnabled = statusMap[item.key] !== false;
      html += `
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px 16px; display: flex; align-items: center; justify-content: space-between; gap: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
          <div style="display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0;">
            <div style="width: 38px; height: 38px; border-radius: 8px; background: #eff6ff; color: #2563eb; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0;">
              ${item.icon}
            </div>
            <div style="min-width: 0;">
              <div style="font-weight: 600; font-size: 13.5px; color: #0f172a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                ${item.title}
              </div>
              <div style="font-size: 11.5px; color: #64748b; margin-top: 2px;">
                ${item.desc}
              </div>
            </div>
          </div>
          <div style="flex-shrink: 0; display: flex; align-items: center; gap: 8px;">
            ${item.key === 'unblock_files' ? `
              <button class="btn btn-action-card" style="padding: 6px 12px; font-size: 12px; font-weight: 600; border-radius: 6px;" onclick="app.unblockFilesQuick()" title="Bỏ chặn toàn bộ file trong thư mục Downloads, Desktop & cấu hình Registry">
                ⚡ Bỏ Chặn Nhanh
              </button>
              <button class="btn btn-slate-light" style="padding: 6px 12px; font-size: 12px; font-weight: 600; border-radius: 6px;" onclick="app.unblockFilesCustom()" title="Chọn tệp tin hoặc thư mục cụ thể cần bỏ chặn">
                📂 Chọn File/Folder
              </button>
            ` : item.actionOnly ? `
              <button class="btn btn-action-card" style="padding: 6px 12px; font-size: 12px; font-weight: 600; border-radius: 6px;" onclick="app.toggleTweak('${item.key}', true)">
                ⚡ ${item.btnText}
              </button>
            ` : `
              <span class="badge ${isEnabled ? 'badge-success' : 'badge-danger'}" style="padding: 4px 8px; font-size: 10.5px; border-radius: 4px;">
                ${isEnabled ? 'ĐANG BẬT' : 'ĐANG TẮT'}
              </span>
              <button class="btn ${isEnabled ? 'btn-danger' : 'btn-primary'}" style="padding: 5px 12px; font-size: 12px; font-weight: 600; border-radius: 6px;" onclick="app.toggleTweak('${item.key}', ${!isEnabled})">
                ${isEnabled ? 'Tắt' : 'Bật'}
              </button>
            `}
          </div>
        </div>
      `;
    });

    container.innerHTML = html;
  },

  async unblockFilesQuick() {
    this.addLog("info", "Đang quét và bỏ chặn (Unblock) toàn bộ file trong Downloads, Desktop & Documents...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.unblock_files_quick();
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
    }
  },

  async unblockFilesCustom() {
    this.addLog("info", "Đang mở hộp thoại chọn tệp tin hoặc thư mục cần bỏ chặn...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.unblock_files_custom();
      if (res && res.cancelled) return;
      this.addLog(res.success ? "success" : "error", res.message);
      if (res.message) alert(res.message);
    }
  },

  async toggleTweak(tweakKey, enable) {
    this.addLog("info", `Đang thay đổi thiết lập hệ thống (${tweakKey})...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.toggle_system_tweak(tweakKey, enable);
      this.addLog(res.success ? "success" : "error", res.message);
      if (tweakKey === 'unblock_files' && res && res.message) {
        alert(res.message);
      }
      if (typeof this.loadSystemTweaksStatus === 'function') {
        this.loadSystemTweaksStatus();
      }
    }
  },

  openExternalUrl(url) {
    if (!url) return;
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.open_external_url(url);
    } else {
      window.open(url, '_blank');
    }
  }
});
