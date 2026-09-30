/**
 * IT Tool LTT 2026 - Boot Manager Module
 * BCD Boot Entries Manager & WinPE (ISO / WIM) Onboard Hard Drive Installer
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
   * Loads BCD Boot Entries into the UI table and updates available disk partitions
   */
  async loadBootEntries() {
    this.addLog("info", "Đang tải danh sách menu Boot BCD...");
    const tbody = document.getElementById("boot-entries-body");
    const timeoutInput = document.getElementById("boot-timeout-input");

    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="4" class="text-center py-3 text-muted">🔄 Đang đọc cấu hình BCD system...</td></tr>`;
    }

    // Also load available partitions for target selection
    this.loadPartitions();

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

    // Detect duplicate GUIDs in current BCD
    const guidCounts = {};
    res.entries.forEach(e => {
      const g = (e.guid || '').trim().toLowerCase();
      if (g) guidCounts[g] = (guidCounts[g] || 0) + 1;
    });

    if (tbody) {
      tbody.innerHTML = res.entries.map((item) => {
        const isDup = guidCounts[(item.guid || '').trim().toLowerCase()] > 1;
        const isSelected = this.selectedBootGuid && (item.guid === this.selectedBootGuid);
        return `
        <tr class="${isSelected ? 'selected-boot-row' : ''}" style="cursor: pointer; ${isDup ? 'background-color: #fff1f2;' : ''}" onclick="app.selectBootEntry('${item.guid}')">
          <td style="font-weight: 600; color: #1e293b; padding: 10px;">
            ${item.is_default ? '⭐ ' : ''}${this.escapeHtml(item.name)}
            ${isDup ? '<span class="badge badge-danger" style="margin-left: 6px; font-size: 10px; background-color: #e11d48; color: white;" title="Cảnh báo: Phát hiện mục khác trong BCD có cùng GUID!">⚠️ Trùng GUID</span>' : ''}
          </td>
          <td style="font-family: monospace; font-size: 11px; color: ${isDup ? '#be123c' : '#475569'}; padding: 10px; font-weight: ${isDup ? '700' : 'normal'};">
            ${this.escapeHtml(item.guid)}
          </td>
          <td style="text-align: center; padding: 10px;">
            ${item.is_default 
              ? '<span class="badge badge-success" style="font-size: 11px; padding: 3px 8px;">⭐ Mặc định</span>' 
              : `<button class="btn btn-xs btn-amber-outline" onclick="event.stopPropagation(); app.setDefaultBoot('${item.guid}')">⭐ Chọn làm mặc định</button>`}
          </td>
          <td style="text-align: right; padding: 10px;">
            <button class="btn btn-xs btn-rose-outline" onclick="event.stopPropagation(); app.deleteBootEntry('${item.guid}', '${this.escapeHtml(item.name)}')">
              ❌ Xóa
            </button>
          </td>
        </tr>
      `;
      }).join("");
    }

    // Select default entry or first entry by default
    if (res.entries.length > 0) {
      const defaultEntry = res.entries.find(e => e.is_default) || res.entries[0];
      this.selectBootEntry(defaultEntry.guid);
    }
  },

  /**
   * Loads fixed hard drive partitions into target drive select dropdown
   */
  async loadPartitions() {
    const driveSelect = document.getElementById("winpe-target-drive");
    if (!driveSelect) return;

    let res = null;
    if (window.pywebview && window.pywebview.api && window.pywebview.api.get_available_partitions) {
      res = await window.pywebview.api.get_available_partitions();
    }

    if (res && res.success && res.partitions && res.partitions.length > 0) {
      this.availablePartitions = res.partitions;
      driveSelect.innerHTML = res.partitions.map(p => `
        <option value="${p.drive}" ${(!p.is_system && p.free_gb >= 5) ? 'selected' : ''}>
          ${this.escapeHtml(p.display)}
        </option>
      `).join("");
    } else {
      driveSelect.innerHTML = `
        <option value="C:">C: [Hệ thống Windows] (Mặc định)</option>
        <option value="D:" selected>D: [Ổ cứng Dữ liệu / Cứu hộ]</option>
      `;
    }
  },

  /**
   * Selects a boot entry to view details and perform actions
   */
  selectBootEntry(guid) {
    if (!this.bootEntriesData) return;
    const item = this.bootEntriesData.find(x => x.guid === guid);
    if (!item) return;

    this.selectedBootGuid = guid;

    // Update active highlight on table rows
    const tbody = document.getElementById("boot-entries-body");
    if (tbody) {
      const rows = tbody.querySelectorAll("tr");
      rows.forEach(r => {
        r.classList.remove("selected-boot-row");
        if (r.innerText.includes(guid)) {
          r.classList.add("selected-boot-row");
        }
      });
    }

    // Update dedicated selected entry toolbar
    const displayName = document.getElementById("selected-boot-display-name");
    const displayGuid = document.getElementById("selected-boot-display-guid");
    const editNameInput = document.getElementById("edit-boot-name-input");
    const detailText = document.getElementById("boot-entry-detail");
    const btnSetDefault = document.getElementById("btn-set-default-selected");

    if (displayName) displayName.innerText = item.name;
    if (displayGuid) displayGuid.innerText = item.guid;
    if (editNameInput) editNameInput.value = item.name;

    // Fallback for legacy input if edit-boot-name-input not present
    const legacyNameInput = document.getElementById("boot-name-input");
    if (legacyNameInput && !document.getElementById("winpe-boot-name-input")) {
      legacyNameInput.value = item.name;
    }

    if (btnSetDefault) {
      if (item.is_default) {
        btnSetDefault.innerText = "⭐ Đang Là Mặc Định";
        btnSetDefault.disabled = true;
        btnSetDefault.style.opacity = "0.7";
      } else {
        btnSetDefault.innerText = "⭐ Đặt Làm Mặc Định";
        btnSetDefault.disabled = false;
        btnSetDefault.style.opacity = "1";
      }
    }

    if (detailText) {
      detailText.value = item.raw || `Boot Name: ${item.name}\nGUID: ${item.guid}\nPath: ${item.path}\nDevice: ${item.device}`;
    }
  },

  /**
   * Toggle raw BCD detail viewer
   */
  toggleRawBcdDetail() {
    const rawContainer = document.getElementById("raw-bcd-container");
    const btnToggle = document.getElementById("btn-toggle-raw-bcd");
    if (!rawContainer) return;
    const isHidden = (rawContainer.style.display === "none" || !rawContainer.style.display);
    rawContainer.style.display = isHidden ? "block" : "none";
    if (btnToggle) {
      btnToggle.innerText = isHidden ? "📋 Ẩn Raw BCD ▲" : "📋 Chi Tiết Raw BCD ▼";
    }
  },

  /**
   * Copy BCD detail to clipboard
   */
  copyBootEntryDetail() {
    const detailText = document.getElementById("boot-entry-detail");
    if (!detailText || !detailText.value) {
      alert("Không có nội dung chi tiết để sao chép!");
      return;
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(detailText.value).then(() => {
        alert("Đã sao chép chi tiết BCDEDIT vào Clipboard!");
      }).catch(() => {
        detailText.select();
        document.execCommand("copy");
        alert("Đã sao chép chi tiết BCDEDIT vào Clipboard!");
      });
    } else {
      detailText.select();
      document.execCommand("copy");
      alert("Đã sao chép chi tiết BCDEDIT vào Clipboard!");
    }
  },

  /**
   * Browse WinPE File (.iso or .wim)
   */
  async browseWinpeFile() {
    let filePath = "";
    if (window.pywebview && window.pywebview.api && window.pywebview.api.browse_winpe_file) {
      const res = await window.pywebview.api.browse_winpe_file();
      if (res && res.success && res.file_path) {
        filePath = res.file_path;
      }
    } else {
      filePath = prompt("Nhập đường dẫn file WinPE (.iso hoặc .wim):", "D:\\WinPE\\boot.wim");
    }

    if (filePath) {
      const pathInput = document.getElementById("winpe-path-input");
      if (pathInput) pathInput.value = filePath;
      await this.inspectWinpeSource(filePath);
    }
  },

  browseWimFile() {
    return this.browseWinpeFile();
  },

  /**
   * Handles manual path input change
   */
  async onWinpePathChange(filePath) {
    if (filePath && filePath.trim()) {
      await this.inspectWinpeSource(filePath.trim());
    }
  },

  /**
   * Inspects WinPE source file (.iso or .wim) and populates options
   */
  async inspectWinpeSource(filePath) {
    const statusDiv = document.getElementById("winpe-inspect-status");
    const subwimContainer = document.getElementById("winpe-subwim-container");
    const subwimSelect = document.getElementById("winpe-subwim-select");
    const nameInput = document.getElementById("winpe-boot-name-input") || document.getElementById("boot-name-input");
    const appsCheckbox = document.getElementById("winpe-copy-apps");
    const appsContainer = document.getElementById("winpe-copy-apps-container");

    if (statusDiv) statusDiv.innerHTML = `<span style="color: #0284c7;">🔍 Đang quét cấu trúc file...</span>`;

    let res = null;
    if (window.pywebview && window.pywebview.api && window.pywebview.api.inspect_winpe_source) {
      res = await window.pywebview.api.inspect_winpe_source(filePath);
    } else {
      const isIso = filePath.toLowerCase().endsWith(".iso");
      res = {
        success: true,
        is_iso: isIso,
        filename: filePath.split(/[\\/]/).pop(),
        default_name: `WinPE Rescue - ${filePath.split(/[\\/]/).pop().replace(/\.(iso|wim)$/i, '')}`,
        wims: [
          { name: "w11pe64.wim", rel_path: "WIM/w11pe64.wim", size_mb: 420, is_recommended: true, description: "w11pe64.wim (420 MB)" }
        ],
        has_apps: isIso
      };
    }

    if (!res || !res.success) {
      if (statusDiv) statusDiv.innerHTML = `<span style="color: #ef4444;">⚠️ ${res ? res.message : 'Không thể đọc file'}</span>`;
      return;
    }

    if (nameInput && res.default_name) {
      nameInput.value = res.default_name;
    }

    if (res.is_iso) {
      if (statusDiv) {
        statusDiv.innerHTML = `<span style="color: #16a34a;">✅ Đã nhận diện ISO WinPE: Tìm thấy ${res.wims.length} file WIM bên trong.</span>`;
      }

      // Show sub-wim selector if multiple WIMs or at least 1
      if (subwimContainer && subwimSelect && res.wims && res.wims.length > 0) {
        subwimSelect.innerHTML = res.wims.map(w => `
          <option value="${w.rel_path}" ${w.is_recommended ? 'selected' : ''}>
            ${this.escapeHtml(w.description)}${w.is_recommended ? ' ⭐ [Khuyên dùng]' : ''}
          </option>
        `).join("");
        subwimContainer.style.display = (res.wims.length > 1) ? "block" : "none";
      }

      // Show/hide apps container
      if (appsContainer && appsCheckbox) {
        appsContainer.style.display = "flex";
        appsCheckbox.checked = res.has_apps;
      }
    } else {
      if (statusDiv) {
        statusDiv.innerHTML = `<span style="color: #16a34a;">✅ Đã nhận diện file WinPE WIM trực tiếp.</span>`;
      }
      if (subwimContainer) subwimContainer.style.display = "none";
      if (appsContainer) appsContainer.style.display = "none";
    }
  },

  /**
   * Sub-WIM selection change
   */
  onSubWimChange(relPath) {
    const nameInput = document.getElementById("winpe-boot-name-input") || document.getElementById("boot-name-input");
    const pathInput = document.getElementById("winpe-path-input");
    if (!nameInput || !pathInput) return;

    const baseFile = pathInput.value.split(/[\\/]/).pop().replace(/\.(iso|wim)$/i, '');
    const wimName = relPath.split(/[\\/]/).pop().replace(/\.wim$/i, '');
    nameInput.value = `WinPE - ${baseFile} (${wimName})`;
  },

  /**
   * Integrates WinPE (.iso / .wim) onto selected hard drive partition
   */
  async integrateWinpeBoot() {
    const pathInput = document.getElementById("winpe-path-input");
    const driveSelect = document.getElementById("winpe-target-drive");
    const nameInput = document.getElementById("winpe-boot-name-input") || document.getElementById("boot-name-input");
    const subwimSelect = document.getElementById("winpe-subwim-select");
    const appsCheckbox = document.getElementById("winpe-copy-apps");
    const progressBanner = document.getElementById("winpe-progress-banner");
    const btnIntegrate = document.getElementById("btn-integrate-winpe");

    const sourcePath = pathInput ? pathInput.value.trim() : "";
    const targetDrive = driveSelect ? driveSelect.value.trim() : "C:";
    const bootName = nameInput ? nameInput.value.trim() : "";
    const selectedWimRel = subwimSelect ? subwimSelect.value.trim() : "";
    const copyApps = appsCheckbox ? appsCheckbox.checked : false;

    if (!sourcePath) {
      alert("Vui lòng chọn hoặc nhập đường dẫn file WinPE (.iso hoặc .wim) cần tích hợp!");
      return;
    }

    const confirmMsg = `Bạn có chắc chắn muốn tích hợp WinPE vào phân vùng [${targetDrive}]?\n\n` +
      `- File nguồn: ${sourcePath}\n` +
      `- Vị trí lưu trên ổ cứng: ${targetDrive}\\WinPE\\boot.wim\n` +
      `- Tên menu boot: ${bootName || 'WinPE Rescue'}\n` +
      `- Sao chép Apps cứu hộ: ${copyApps ? 'Có' : 'Không'}\n\n` +
      `Sau khi hoàn tất, máy tính có thể boot trực tiếp vào WinPE cứu hộ từ ổ cứng mà KHÔNG CẦN CẮM USB!`;

    if (!confirm(confirmMsg)) return;

    // Show progress banner and disable button
    if (progressBanner) progressBanner.style.display = "flex";
    if (btnIntegrate) {
      btnIntegrate.disabled = true;
      btnIntegrate.innerHTML = `⏳ Đang xử lý...`;
    }

    this.addLog("info", `Đang bắt đầu tích hợp WinPE từ "${sourcePath}" vào ổ cứng [${targetDrive}]...`);

    try {
      let res = null;
      if (window.pywebview && window.pywebview.api && window.pywebview.api.integrate_winpe_boot) {
        res = await window.pywebview.api.integrate_winpe_boot(sourcePath, targetDrive, bootName, selectedWimRel, copyApps);
      } else {
        res = {
          success: true,
          message: `[Mock] Đã tích hợp thành công WinPE vào ${targetDrive}\\WinPE\\boot.wim! Menu boot: '${bootName}'`
        };
      }

      if (res && res.success) {
        alert(res.message);
        this.addLog("success", res.message);
        if (pathInput) pathInput.value = "";
        const statusDiv = document.getElementById("winpe-inspect-status");
        if (statusDiv) statusDiv.innerHTML = "";
      } else {
        alert(res ? res.message : "Đã xảy ra lỗi không xác định trong quá trình tích hợp!");
        this.addLog("error", res ? res.message : "Lỗi tích hợp WinPE");
      }
    } catch (err) {
      alert("Lỗi thực thi: " + err);
      this.addLog("error", "Lỗi: " + err);
    } finally {
      if (progressBanner) progressBanner.style.display = "none";
      if (btnIntegrate) {
        btnIntegrate.disabled = false;
        btnIntegrate.innerHTML = `➕ Tích Hợp WinPE Vào Ổ Cứng`;
      }
      this.loadBootEntries();
    }
  },

  addWimBootEntry() {
    return this.integrateWinpeBoot();
  },

  /**
   * Save / Update Boot Entry Name
   */
  async saveBootEntryName() {
    if (!this.selectedBootGuid) {
      alert("Vui lòng chọn mục Boot trong danh sách ở trên!");
      return;
    }
    const nameInput = document.getElementById("edit-boot-name-input") || document.getElementById("boot-name-input");
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
