/**
 * IT-Tools 2026 - Boot Manager Module
 * BCD Boot Entries Manager & WinPE WIM Installer
 */
Object.assign(AppController.prototype, {

  /**
   * Global fallback for runModule('boot_manager', ...)
   */
  async runModuleBootManager(action) {
    if (action === 'open') {
      this.openBootManagerGui();
    } else {
      this.loadBootEntries();
    }
  },

  /**
   * Loads BCD Boot Entries into the UI table
   */
  async loadBootEntries() {
    this.addLog("info", "Đang tải danh sách menu Boot BCD...");
    const tbody = document.getElementById("boot-entries-body");
    const timeoutInput = document.getElementById("boot-timeout-input");

    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="4" class="text-center py-3 text-muted">🔄 Đang đọc cấu hình BCD system...</td></tr>`;
    }

    let res = null;
    if (window.pywebview && window.pywebview.api && window.pywebview.api.get_boot_entries) {
      res = await window.pywebview.api.get_boot_entries();
    } else {
      res = {
        success: true,
        timeout: "30",
        entries: [
          { name: "Windows 11", guid: "{eff11ca4-b3dc-11f0-a6a6-1c1b0d592e7d}", is_default: true, path: "\\WINDOWS\\system32\\winload.efi", raw: "identifier {eff11ca4-b3dc-11f0-a6a6-1c1b0d592e7d}\ndescription Windows 11" },
          { name: "Windows Recovery Environment", guid: "{eff11ca5-b3dc-11f0-a6a6-1c1b0d592e7d}", is_default: false, path: "\\Recovery\\WindowsRE\\Winre.wim", raw: "identifier {eff11ca5-b3dc-11f0-a6a6-1c1b0d592e7d}\ndescription Windows Recovery" }
        ]
      };
    }

    if (timeoutInput && res && res.timeout) {
      timeoutInput.value = res.timeout;
    }

    if (!res || !res.entries || res.entries.length === 0) {
      if (tbody) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center py-3 text-muted">Không tìm thấy mục boot nào (hoặc cần quyền Administrator).</td></tr>`;
      }
      return;
    }

    this.bootEntriesData = res.entries;

    if (tbody) {
      tbody.innerHTML = res.entries.map((item, index) => `
        <tr style="cursor: pointer;" onclick="app.selectBootEntry('${item.guid}')">
          <td style="font-weight: 600; color: #1e293b; padding: 10px;">
            ${item.is_default ? '⭐ ' : ''}${this.escapeHtml(item.name)}
          </td>
          <td style="font-family: monospace; font-size: 11px; color: #475569; padding: 10px;">
            ${this.escapeHtml(item.guid)}
          </td>
          <td style="text-align: center; padding: 10px;">
            ${item.is_default 
              ? '<span class="badge badge-success">Mặc định</span>' 
              : `<button class="btn btn-xs btn-sky-outline" onclick="event.stopPropagation(); app.setDefaultBoot('${item.guid}')">⭐ Chọn làm mặc định</button>`}
          </td>
          <td style="text-align: right; padding: 10px;">
            <button class="btn btn-xs btn-rose-outline" onclick="event.stopPropagation(); app.deleteBootEntry('${item.guid}', '${this.escapeHtml(item.name)}')">
              ❌ Xóa
            </button>
          </td>
        </tr>
      `).join("");
    }

    // Select first entry by default
    if (res.entries.length > 0) {
      this.selectBootEntry(res.entries[0].guid);
    }
  },

  /**
   * Selects a boot entry to view details
   */
  selectBootEntry(guid) {
    if (!this.bootEntriesData) return;
    const item = this.bootEntriesData.find(x => x.guid === guid);
    if (!item) return;

    this.selectedBootGuid = guid;

    const detailText = document.getElementById("boot-entry-detail");
    const nameInput = document.getElementById("boot-name-input");

    if (detailText) {
      detailText.value = item.raw || `Boot Name: ${item.name}\nGUID: ${item.guid}\nPath: ${item.path}\nDevice: ${item.device}`;
    }
    if (nameInput) {
      nameInput.value = item.name;
    }
  },

  /**
   * Browse WIM File
   */
  async browseWimFile() {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.browse_wim_file) {
      const res = await window.pywebview.api.browse_wim_file();
      if (res && res.success && res.file_path) {
        const wimInput = document.getElementById("winpe-path-input");
        const nameInput = document.getElementById("boot-name-input");
        if (wimInput) wimInput.value = res.file_path;
        if (nameInput && !nameInput.value) {
          const parts = res.file_path.split(/[\\/]/);
          const fileName = parts[parts.length - 1].replace(/\.wim$/i, "");
          nameInput.value = `WinPE - ${fileName}`;
        }
      }
    } else {
      const path = prompt("Nhập đường dẫn file WinPE .wim (Ví dụ: D:\\WinPE\\boot.wim):");
      if (path) {
        const wimInput = document.getElementById("winpe-path-input");
        if (wimInput) wimInput.value = path;
      }
    }
  },

  /**
   * Adds WinPE WIM Boot Entry
   */
  async addWimBootEntry() {
    const wimInput = document.getElementById("winpe-path-input");
    const nameInput = document.getElementById("boot-name-input");

    const wimPath = wimInput ? wimInput.value.trim() : "";
    const bootName = nameInput ? nameInput.value.trim() : "";

    if (!wimPath) {
      alert("Vui lòng chọn hoặc nhập đường dẫn file WinPE .wim!");
      return;
    }

    this.addLog("info", `Đang thêm menu boot WIM: ${wimPath}...`);
    if (window.pywebview && window.pywebview.api && window.pywebview.api.add_wim_boot_entry) {
      const res = await window.pywebview.api.add_wim_boot_entry(wimPath, bootName);
      alert(res.message);
      if (res.success) {
        if (wimInput) wimInput.value = "";
        if (nameInput) nameInput.value = "";
      }
    } else {
      alert(`[Mock] Đã thêm menu Boot WinPE '${bootName}' thành công!`);
    }

    this.loadBootEntries();
  },

  /**
   * Save / Update Boot Entry Name
   */
  async saveBootEntryName() {
    if (!this.selectedBootGuid) {
      alert("Vui lòng chọn mục Boot trong danh sách!");
      return;
    }
    const nameInput = document.getElementById("boot-name-input");
    const newName = nameInput ? nameInput.value.trim() : "";
    if (!newName) {
      alert("Vui lòng nhập tên mới cho mục Boot!");
      return;
    }

    this.addLog("info", `Đang đổi tên mục Boot (${this.selectedBootGuid}) sang '${newName}'...`);
    if (window.pywebview && window.pywebview.api && window.pywebview.api.update_boot_name) {
      const res = await window.pywebview.api.update_boot_name(this.selectedBootGuid, newName);
      alert(res.message);
    } else {
      alert(`[Mock] Đã đổi tên mục Boot sang '${newName}'!`);
    }

    this.loadBootEntries();
  },

  /**
   * Deletes a Boot Entry
   */
  async deleteBootEntry(guid, name) {
    if (!guid) guid = this.selectedBootGuid;
    if (!guid) {
      alert("Vui lòng chọn mục Boot cần xóa!");
      return;
    }

    if (!confirm(`Bạn có chắc chắn muốn xóa mục Boot:\n"${name || guid}"\n\n⚠️ Thao tác này không thể hoàn tác!`)) return;

    this.addLog("info", `Đang xóa mục Boot ${guid}...`);
    if (window.pywebview && window.pywebview.api && window.pywebview.api.delete_boot_entry) {
      const res = await window.pywebview.api.delete_boot_entry(guid);
      alert(res.message);
    } else {
      alert(`[Mock] Đã xóa mục Boot ${guid}!`);
    }

    this.loadBootEntries();
  },

  /**
   * Sets Entry as Default Boot
   */
  async setDefaultBoot(guid) {
    if (!guid) guid = this.selectedBootGuid;
    if (!guid) {
      alert("Vui lòng chọn mục Boot làm mặc định!");
      return;
    }

    this.addLog("info", `Đang đặt mục Boot ${guid} làm mặc định...`);
    if (window.pywebview && window.pywebview.api && window.pywebview.api.set_default_boot) {
      const res = await window.pywebview.api.set_default_boot(guid);
      alert(res.message);
    } else {
      alert(`[Mock] Đã đặt ${guid} làm mặc định!`);
    }

    this.loadBootEntries();
  },

  /**
   * Sets Boot Menu Timeout
   */
  async setBootTimeout() {
    const timeoutInput = document.getElementById("boot-timeout-input");
    const seconds = timeoutInput ? timeoutInput.value.trim() : "30";

    this.addLog("info", `Đang đặt thời gian chờ Boot menu: ${seconds}s...`);
    if (window.pywebview && window.pywebview.api && window.pywebview.api.set_boot_timeout) {
      const res = await window.pywebview.api.set_boot_timeout(seconds);
      alert(res.message);
    } else {
      alert(`[Mock] Đã đặt thời gian chờ Boot menu là ${seconds} giây!`);
    }
  },

  /**
   * Opens native Boot Manager Tkinter GUI
   */
  openBootManagerGui() {
    this.addLog("info", "Mở cửa sổ Boot Manager GUI (Tkinter)...");
    if (window.pywebview && window.pywebview.api && window.pywebview.api.open_boot_manager_gui) {
      window.pywebview.api.open_boot_manager_gui();
    }
  }

});
