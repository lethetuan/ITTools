/**
 * IT-Tools 2026 - Browser Backup & Restore Module
 */
Object.assign(AppController.prototype, {
  async loadBrowserBackupInfo() {
    const listEl = document.getElementById("bb-browsers-list");

    if (listEl) {
      listEl.innerHTML = `<div class="text-center py-4 text-muted">🔄 Đang kiểm tra danh sách trình duyệt web...</div>`;
    }

    let res = null;
    if (window.pywebview && window.pywebview.api) {
      try {
        res = await window.pywebview.api.get_browser_backup_info();
      } catch (err) {
        console.error("Lỗi get_browser_backup_info:", err);
      }
    }

    if (!res || !res.success) {
      res = {
        success: true,
        browsers: [
          { key: "Chrome", name: "Google Chrome", is_installed: true, size: "249.1 MB", profile_root: "C:\\Users\\Mock\\AppData\\Local\\Google\\Chrome\\User Data", profiles_count: 1 },
          { key: "Edge", name: "Microsoft Edge", is_installed: true, size: "99.7 MB", profile_root: "C:\\Users\\Mock\\AppData\\Local\\Microsoft\\Edge\\User Data", profiles_count: 2 },
          { key: "Brave", name: "Brave Browser", is_installed: true, size: "586.4 MB", profile_root: "C:\\Users\\Mock\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data", profiles_count: 1 },
          { key: "CocCoc", name: "Cốc Cốc Browser", is_installed: false, size: "0 B", profile_root: "", profiles_count: 0 },
          { key: "Firefox", name: "Mozilla Firefox", is_installed: false, size: "0 B", profile_root: "", profiles_count: 0 },
          { key: "Opera", name: "Opera Stable", is_installed: false, size: "0 B", profile_root: "", profiles_count: 0 },
          { key: "OperaGX", name: "Opera GX", is_installed: false, size: "0 B", profile_root: "", profiles_count: 0 }
        ],
        history: []
      };
    }

    this.allDetectedBrowsers = res.browsers || [];
    this.allBackupHistory = res.history || [];

    this.renderBrowsersList();
    this.renderBackupHistoryTable();
  },

  renderBrowsersList() {
    const detectedCountEl = document.getElementById("bb-detected-count");
    const listEl = document.getElementById("bb-browsers-list");
    const showUninstalled = document.getElementById("bb-show-uninstalled-toggle")?.checked ?? false;

    if (!this.allDetectedBrowsers) return;

    const svgMap = {
      Chrome: `<svg width="24" height="24" viewBox="0 0 48 48"><circle cx="24" cy="24" r="20" fill="#fff"/><path fill="#EA4335" d="M24 4c7.7 0 14.4 4.4 17.7 10.8L24 24V4z"/><path fill="#4285F4" d="M41.7 14.8C43.2 17.6 44 20.7 44 24c0 11-9 20-20 20-4.3 0-8.3-1.4-11.5-3.7L24 24l17.7-9.2z"/><path fill="#FBBC05" d="M12.5 40.3C7.3 36.5 4 30.6 4 24c0-6.8 3.4-12.8 8.7-16.5L24 24 12.5 40.3z"/><path fill="#34A853" d="M12.7 7.5C15.9 5.3 19.8 4 24 4l17.7 10.8L24 24 12.7 7.5z"/><circle cx="24" cy="24" r="9" fill="#fff"/><circle cx="24" cy="24" r="7" fill="#1A73E8"/></svg>`,

      Edge: `<svg width="24" height="24" viewBox="0 0 100 100"><path fill="#0078D4" d="M86 58c-1-16-12.6-29-28.5-31.3 14.3 2.9 24.8 15.3 24.8 30.5 0 17-13.8 30.8-30.8 30.8-10.5 0-19.7-5.2-25.4-13.2 6.5 10.1 18.1 16.8 31.1 16.8 20.6 0 37.2-16.6 37.2-37.2 0-4.8-.9-9.5-2.4-13.7l-6 17.3z"/><path fill="#00BCF2" d="M51.5 8.4C27.4 8.4 7.8 28 7.8 52.1c0 8.8 2.5 17 7.1 23.9C10.3 68.8 7.8 60.9 7.8 52.3c0-22.2 18-40.2 40.2-40.2 16.1 0 30 9.4 36.3 23.1-6.3-15.9-21.8-26.8-40.1-26.8z"/><path fill="#00D26A" d="M47 29.4c17.4 0 31.4 14 31.4 31.4 0 4.6-1 9-2.9 13 4.4-5.2 7.1-11.9 7.1-19.3 0-16.1-13.2-29.3-29.3-29.3-9.6 0-18.2 4.6-23.7 11.9 5.7-4.8 13-7.7 21.1-7.7z"/><path fill="#107C41" d="M50.2 29.4c-12.8 0-23 10.3-23 23 0 5.2 1.7 10 4.6 14-3.1-4.2-4.9-9.4-4.9-15 0-13.8 11.3-25.1 25.1-25.1 6.5 0 12.4 2.5 16.8 6.5-4.6-2.7-10.1-4.4-16.1-4.4z"/></svg>`,

      Brave: `<svg width="24" height="24" viewBox="0 0 512 512"><path fill="#FB542B" d="M405.3 133.3L288 64l-32-21.3L224 64 106.7 133.3 42.7 176l37.3 149.3L256 469.3l176-144 37.3-149.3z"/><path fill="#FFF" d="M256 106.7l96 58.7v117.3L256 373.3l-96-90.7V165.3z"/><path fill="#FB542B" d="M256 160l64 37.3v74.7L256 320l-64-48V197.3z"/></svg>`,

      CocCoc: `<svg width="24" height="24" viewBox="0 0 48 48"><circle cx="24" cy="24" r="20" fill="#2E7D32"/><path fill="#FFF" d="M24 8c-8.8 0-16 7.2-16 16s7.2 16 16 16 16-7.2 16-16S32.8 8 24 8zm0 25c-5 0-9-4-9-9s4-9 9-9 9 4 9 9-4 9-9 9z"/><polygon fill="#FFEB3B" points="24,13 26.5,20.5 34,20.5 28,25 30,32.5 24,27.5 18,32.5 20,25 14,20.5 21.5,20.5"/></svg>`,

      Firefox: `<svg width="24" height="24" viewBox="0 0 48 48"><circle cx="24" cy="24" r="19" fill="#1C1E24"/><path fill="#E66000" d="M41 18c0 10.5-8.5 19-19 19S3 28.5 3 18 18.5 3 24 3c3 0 17 3 17 15z"/><path fill="#FF9500" d="M37 21c0 8.3-6.7 15-15 15S7 29.3 7 21s6.7-15 15-15c2.2 0 15 2.2 15 15z"/><path fill="#FFD400" d="M24 11c-5.5 0-10 4.5-10 10s4.5 10 10 10 10-4.5 10-10-4.5-10-10-10z"/><circle cx="24" cy="24" r="7.5" fill="#0060DF"/></svg>`,

      Opera: `<svg width="24" height="24" viewBox="0 0 48 48"><path fill="#FF1B2D" d="M24 4C13 4 4 13 4 24s9 20 20 20 20-9 20-20S35 4 24 4zm0 32c-5.5 0-10-5.4-10-12s4.5-12 10-12 10 5.4 10 12-4.5 12-10 12z"/></svg>`,

      OperaGX: `<svg width="24" height="24" viewBox="0 0 48 48"><path fill="#FA1E4E" d="M24 4L4 24l20 20 20-20L24 4zm0 10l10 10-10 10-10-10 10-10z"/></svg>`
    };

    const installedCount = this.allDetectedBrowsers.filter(b => b.is_installed).length;
    const totalCount = this.allDetectedBrowsers.length;

    if (detectedCountEl) {
      detectedCountEl.innerText = `${installedCount}/${totalCount} trình duyệt`;
    }

    const displayList = showUninstalled 
      ? this.allDetectedBrowsers 
      : this.allDetectedBrowsers.filter(b => b.is_installed);

    if (listEl) {
      if (displayList.length === 0) {
        listEl.innerHTML = `
          <div class="text-center py-4 text-muted" style="background: #f8fafc; border-radius: 8px; border: 1px dashed #cbd5e1;">
            <div style="font-size: 24px; margin-bottom: 4px;">🔍</div>
            <div style="font-size: 13px; font-weight: 600; color: #475569;">Không có trình duyệt nào được cài đặt trên máy.</div>
            <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">Tích chọn "Hiện chưa cài" để xem danh sách đầy đủ.</div>
          </div>
        `;
      } else {
        listEl.innerHTML = displayList.map(b => {
          const isIns = b.is_installed;
          const iconMarkup = b.real_icon
            ? `<img src="${b.real_icon}" width="24" height="24" style="object-fit: contain; display: block;" alt="${b.name}">`
            : (svgMap[b.key] || `<span style="font-size: 20px;">🌐</span>`);

          const statusBadge = isIns 
            ? `<span class="badge bg-success-subtle text-success" style="padding: 4px 10px; border-radius: 6px; font-size: 11.5px; font-weight: 600;">✅ Tìm thấy (${b.size})</span>`
            : `<span class="badge bg-secondary-subtle text-muted" style="padding: 4px 10px; border-radius: 6px; font-size: 11px;">❌ Chưa cài đặt</span>`;

          return `
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: ${isIns ? '#ffffff' : '#f8fafc'}; border: 1px solid ${isIns ? '#cbd5e1' : '#e2e8f0'}; border-radius: 8px; box-shadow: ${isIns ? '0 1px 3px rgba(0,0,0,0.04)' : 'none'}; opacity: ${isIns ? '1' : '0.65'};">
              <label style="display: flex; align-items: center; gap: 12px; cursor: ${isIns ? 'pointer' : 'default'}; margin: 0; flex: 1;">
                <input type="checkbox" class="bb-browser-checkbox" data-key="${b.key}" ${isIns ? 'checked' : 'disabled'} style="accent-color: #2563eb; width: 18px; height: 18px;">
                <div style="display: flex; align-items: center; justify-content: center; width: 26px; height: 26px;">
                  ${iconMarkup}
                </div>
                <div>
                  <div style="font-weight: 700; font-size: 13.5px; color: #1e293b;">${b.name}</div>
                  <div style="font-size: 11.5px; color: #64748b; text-overflow: ellipsis; overflow: hidden; max-width: 360px;" title="${b.profile_root || ''}">
                    ${isIns ? (b.profile_root || 'Standard Profile Path') : 'Chưa được khởi tạo hoặc không tồn tại'}
                  </div>
                </div>
              </label>
              <div>${statusBadge}</div>
            </div>
          `;
        }).join('');
      }
    }
  },

  renderBackupHistoryTable() {
    const historyBodyEl = document.getElementById("bb-history-body");
    if (!historyBodyEl) return;

    const history = this.allBackupHistory || [];
    if (history.length === 0) {
      historyBodyEl.innerHTML = `
        <tr>
          <td colspan="5" class="text-center py-3 text-muted">Chưa có bản sao lưu nào được lưu trữ trên Desktop/Browser_Backups. Bấm "Bắt Đầu Sao Lưu" ở trên.</td>
        </tr>
      `;
    } else {
      historyBodyEl.innerHTML = history.map(item => {
        const bList = Object.keys(item.browsers || {}).join(", ") || "Hợp lệ";
        const safePath = (item.path || '').replace(/\\/g, '\\\\');
        return `
          <tr>
            <td style="padding: 8px; font-family: monospace; font-weight: 600; color: #0284c7;">
              📂 ${item.folder_name}
            </td>
            <td style="padding: 8px; text-align: center; color: #475569;">${item.created_at || item.timestamp}</td>
            <td style="padding: 8px; text-align: center; font-weight: 600; color: #166534;">${item.size || 'N/A'}</td>
            <td style="padding: 8px; color: #334155;">${bList}</td>
            <td style="padding: 8px; text-align: center;">
              <button class="btn btn-success-solid btn-sm py-1 px-2" onclick="app.startBrowserRestore('${safePath}')">
                📥 Phục Hồi
              </button>
            </td>
          </tr>
        `;
      }).join('');
    }
  },

  getBrowserBackupOptions() {
    return {
      bookmarks: document.getElementById("bb-opt-bookmarks")?.checked ?? true,
      passwords: document.getElementById("bb-opt-passwords")?.checked ?? true,
      history: document.getElementById("bb-opt-history")?.checked ?? true,
      extensions: document.getElementById("bb-opt-extensions")?.checked ?? false,
      full_profile: document.getElementById("bb-opt-full-profile")?.checked ?? false
    };
  },

  getSelectedBrowsers() {
    const checkboxes = document.querySelectorAll(".bb-browser-checkbox:checked");
    const selected = [];
    checkboxes.forEach(cb => {
      const key = cb.getAttribute("data-key");
      if (key) selected.push(key);
    });
    return selected;
  },

  async startBrowserBackup() {
    const selected = this.getSelectedBrowsers();
    if (selected.length === 0) {
      alert("Vui lòng chọn ít nhất 1 trình duyệt để sao lưu!");
      return;
    }

    const options = this.getBrowserBackupOptions();
    const targetDir = document.getElementById("bb-target-dir-input")?.value?.trim() || "";

    this.addLog("info", `Đang tiến hành sao lưu ${selected.join(', ')}...`);

    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.backup_browsers(selected, options, targetDir);
      if (res && res.success) {
        this.addLog("success", res.message);
        alert(res.message);
        this.loadBrowserBackupInfo();
      } else {
        this.addLog("error", res ? res.message : "Lỗi sao lưu trình duyệt!");
        alert(res ? res.message : "Lỗi sao lưu!");
      }
    } else {
      alert("[MOCK] Đã hoàn tất sao lưu trình duyệt!");
    }
  },

  async startBrowserRestore(backupDirInput = null) {
    let backupDir = backupDirInput;
    if (!backupDir) {
      if (window.pywebview && window.pywebview.api) {
        const dlg = await window.pywebview.api.select_folder_dialog("Chọn thư mục chứa bản sao lưu BrowserBackup");
        if (dlg && dlg.folder) {
          backupDir = dlg.folder;
        }
      }
    }

    if (!backupDir) {
      alert("Chưa chọn thư mục bản sao lưu để phục hồi!");
      return;
    }

    const selected = this.getSelectedBrowsers();
    if (selected.length === 0) {
      alert("Vui lòng tích chọn trình duyệt cần phục hồi!");
      return;
    }

    const confirmRestore = confirm(`Bạn có chắc chắn muốn PHỤC HỒI dữ liệu trình duyệt từ thư mục:\n${backupDir}\n\n(Lưu ý: Các trình duyệt đang mở sẽ tự động đóng lại để chép đè dữ liệu).`);
    if (!confirmRestore) return;

    const options = this.getBrowserBackupOptions();
    this.addLog("info", `Đang phục hồi ${selected.join(', ')} từ: ${backupDir}...`);

    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.restore_browsers(backupDir, selected, options);
      if (res && res.success) {
        this.addLog("success", res.message);
        alert(res.message);
      } else {
        this.addLog("error", res ? res.message : "Lỗi phục hồi trình duyệt!");
        alert(res ? res.message : "Lỗi phục hồi!");
      }
    } else {
      alert("[MOCK] Đã hoàn tất phục hồi trình duyệt từ:\n" + backupDir);
    }
  },

  async browseBrowserBackupDir() {
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.select_folder_dialog("Chọn thư mục lưu trữ Sao Lưu Trình Duyệt");
      if (res && res.folder) {
        const inputEl = document.getElementById("bb-target-dir-input");
        if (inputEl) inputEl.value = res.folder;
      }
    }
  },

  async openBrowserBackupFolder() {
    const targetDir = document.getElementById("bb-target-dir-input")?.value?.trim() || "";
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.open_browser_backup_folder(targetDir);
    }
  }
});
