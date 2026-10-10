/**
 * SendTo Editor Module for IT Tool LTT 2026
 * Quản lý menu chuột phải "Gửi đến" (Send To) trong Windows
 */
Object.assign(AppController.prototype, {

  _sendToEscapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  },

  async loadSendToEntries() {
    this.addLog("info", "Đang tải danh sách SendTo...");
    const tbody = document.getElementById("sendto-entries-tbody");
    const badge = document.getElementById("sendto-count-badge");
    const pathEl = document.getElementById("sendto-path-display");
    const deleteBtn = document.getElementById("sendto-delete-btn");

    this._selectedSendToPath = null;
    if (deleteBtn) {
      deleteBtn.disabled = true;
      deleteBtn.title = "Chọn một mục trong danh sách rồi bấm xóa";
    }

    if (!window.pywebview?.api) {
      if (tbody) {
        tbody.innerHTML = `<tr><td colspan="6" style="padding:24px;text-align:center;color:#94a3b8;">Chế độ trình duyệt (Web Demo) - pywebview API chưa kết nối</td></tr>`;
      }
      return;
    }

    try {
      const res = await window.pywebview.api.get_sendto_entries();
      if (!res || !res.success) {
        this.addLog("error", res?.message || "Lỗi tải danh sách SendTo");
        if (tbody) {
          tbody.innerHTML = `<tr><td colspan="6" style="padding:24px;text-align:center;color:#ef4444;">❌ Lỗi: ${res?.message || 'Không thể đọc thư mục SendTo'}</td></tr>`;
        }
        return;
      }

      if (pathEl) pathEl.innerText = res.sendto_path || "";
      const entries = res.entries || [];
      if (badge) badge.innerText = `${entries.length} mục`;

      if (!tbody) return;

      if (entries.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="padding:24px;text-align:center;color:#94a3b8;">Thư mục SendTo trống</td></tr>`;
        return;
      }

      tbody.innerHTML = entries.map((e, idx) => {
        let icon = "📄";
        if (e.type === "Shortcut") icon = "🔗";
        else if (e.type === "Executable") icon = "⚙️";
        else if (e.type === "Folder") icon = "📁";
        else if (e.name.toLowerCase().endsWith(".zip") || e.name.toLowerCase().includes("compressed")) icon = "📦";
        else if (e.name.toLowerCase().includes("mail")) icon = "✉️";

        const sysStyle = e.is_system ? "color:#94a3b8; font-style:italic;" : "";
        const badgeSys = e.is_system ? `<span style="font-size:10px; background:#f1f5f9; color:#94a3b8; padding:1px 6px; border-radius:4px; margin-left:6px;">Hệ thống</span>` : "";

        const safePath = this._sendToEscapeHtml(e.path || "");
        const safeName = this._sendToEscapeHtml(e.name || "");
        const safeTarget = this._sendToEscapeHtml(e.target || "");
        const displayTarget = e.target 
          ? `<span style="font-family:monospace; font-size:11px; color:#0369a1;" title="${safeTarget}">${safeTarget}</span>` 
          : `<span style="color:#cbd5e1; font-size:11px;">(Mặc định Windows)</span>`;

        const actionButtons = e.is_system
          ? `<span style="color:#cbd5e1; font-size:11px;">Được bảo vệ</span>`
          : `
            <div style="display:inline-flex; gap:4px; align-items:center;">
              <button class="btn btn-xs btn-sky-outline" onclick="event.stopPropagation(); app.openSendToLocation('${safePath}')" title="Mở vị trí trong File Explorer" style="padding:2px 6px; font-size:11px;">
                📂
              </button>
              <button class="btn btn-xs btn-rose-outline" onclick="event.stopPropagation(); app.deleteSendToEntry('${safePath}')" title="Xóa lối tắt này" style="padding:2px 6px; font-size:11px;">
                🗑
              </button>
            </div>
          `;

        return `
          <tr id="sendto-row-${idx}" 
              data-path="${safePath}" 
              data-system="${e.is_system}" 
              onclick="app._selectSendToRow(this, '${safePath}', ${e.is_system})"
              style="cursor:pointer; border-bottom:1px solid #f1f5f9; transition:background 0.15s; ${sysStyle}"
              onmouseover="if(!this.classList.contains('selected'))this.style.background='#f8fafc'"
              onmouseout="if(!this.classList.contains('selected'))this.style.background=''">
            <td style="padding:8px 10px; text-align:center; font-size:14px;">${icon}</td>
            <td style="padding:8px 12px; font-weight:600; color:#1e293b;">
              ${safeName}${badgeSys}
            </td>
            <td style="padding:8px 10px; word-break:break-all; max-width:280px;">
              ${displayTarget}
            </td>
            <td style="padding:8px 10px; color:#64748b;">${e.type}</td>
            <td style="padding:8px 10px; text-align:right; color:#94a3b8;">${e.size || '-'}</td>
            <td style="padding:8px 12px; text-align:center;" onclick="event.stopPropagation()">
              ${actionButtons}
            </td>
          </tr>
        `;
      }).join("");

      this.addLog("success", `Đã tải ${entries.length} mục trong SendTo.`);
    } catch (err) {
      this.addLog("error", `Lỗi tải danh sách SendTo: ${err.message || err}`);
    }
  },

  _selectSendToRow(row, path, isSystem) {
    document.querySelectorAll("#sendto-entries-tbody tr").forEach(r => {
      r.classList.remove("selected");
      r.style.background = "";
    });

    row.classList.add("selected");
    row.style.background = "#eff6ff";
    this._selectedSendToPath = path;

    const btn = document.getElementById("sendto-delete-btn");
    if (btn) {
      if (isSystem) {
        btn.disabled = true;
        btn.title = "Không thể xóa mục hệ thống của Windows";
      } else {
        btn.disabled = false;
        btn.title = "Xóa mục đang chọn khỏi SendTo";
      }
    }
  },

  async browseSendToFile() {
    if (!window.pywebview?.api?.browse_sendto_file) return;
    try {
      const filePath = await window.pywebview.api.browse_sendto_file();
      if (!filePath) return;

      const targetInput = document.getElementById("sendto-new-target");
      const nameInput = document.getElementById("sendto-new-name");

      if (targetInput) targetInput.value = filePath;

      // Extract base filename without extension for friendly display name
      const fileName = filePath.split(/[\/\\]/).pop();
      const baseName = fileName.replace(/\.[^/.]+$/, "");
      if (nameInput && (!nameInput.value || nameInput.value.trim() === "")) {
        nameInput.value = baseName;
      }
    } catch (err) {
      this.addLog("error", `Lỗi chọn file: ${err.message || err}`);
    }
  },

  async browseSendToFolder() {
    if (!window.pywebview?.api?.browse_sendto_folder) return;
    try {
      const folderPath = await window.pywebview.api.browse_sendto_folder();
      if (!folderPath) return;

      const targetInput = document.getElementById("sendto-new-target");
      const nameInput = document.getElementById("sendto-new-name");

      if (targetInput) targetInput.value = folderPath;

      // Extract folder name
      const folderName = folderPath.replace(/[\/\\]$/, "").split(/[\/\\]/).pop();
      if (nameInput && (!nameInput.value || nameInput.value.trim() === "")) {
        nameInput.value = folderName;
      }
    } catch (err) {
      this.addLog("error", `Lỗi chọn thư mục: ${err.message || err}`);
    }
  },

  async createSendToShortcut() {
    const nameInput = document.getElementById("sendto-new-name");
    const targetInput = document.getElementById("sendto-new-target");
    let name = nameInput?.value?.trim() || "";
    let target = targetInput?.value?.trim() || "";

    // Strip accidental wrapping quotes
    name = name.replace(/^["']|["']$/g, "").trim();
    target = target.replace(/^["']|["']$/g, "").trim();

    if (!target) {
      alert("Vui lòng nhập hoặc bấm 'Chọn File'/'Chọn Thư Mục' để chọn đường dẫn đích!");
      targetInput?.focus();
      return;
    }

    if (!name) {
      // Auto deduce from target
      const base = target.replace(/[\/\\]$/, "").split(/[\/\\]/).pop();
      name = base.replace(/\.[^/.]+$/, "") || "Shortcut";
    }

    this.addLog("info", `Đang tạo shortcut "${name}" trỏ tới "${target}"...`);
    try {
      const res = await window.pywebview.api.create_sendto_shortcut(name, target);
      if (res && res.success) {
        this.addLog("success", res.message);
        if (nameInput) nameInput.value = "";
        if (targetInput) targetInput.value = "";
        await this.loadSendToEntries();
      } else {
        this.addLog("error", res?.message || "Không thể tạo shortcut");
        alert("Lỗi tạo shortcut: " + (res?.message || "Không xác định"));
      }
    } catch (err) {
      this.addLog("error", `Lỗi tạo shortcut SendTo: ${err.message || err}`);
    }
  },

  async deleteSendToEntry(targetPath) {
    const pathToDel = targetPath || this._selectedSendToPath;
    if (!pathToDel) {
      alert("Vui lòng chọn một mục trong danh sách để xóa!");
      return;
    }

    const name = pathToDel.split(/[\/\\]/).pop();
    if (!confirm(`Bạn có chắc chắn muốn xóa "${name}" khỏi SendTo?`)) {
      return;
    }

    this.addLog("info", `Đang xóa ${name}...`);
    try {
      const res = await window.pywebview.api.delete_sendto_entry(pathToDel);
      if (res && res.success) {
        this.addLog("success", res.message);
        this._selectedSendToPath = null;
        await this.loadSendToEntries();
      } else {
        this.addLog("error", res?.message || "Lỗi xóa mục");
        alert("Lỗi: " + (res?.message || "Không thể xóa"));
      }
    } catch (err) {
      this.addLog("error", `Lỗi xóa mục SendTo: ${err.message || err}`);
    }
  },

  async openSendToLocation(entryPath) {
    if (!window.pywebview?.api?.open_sendto_entry_location) return;
    try {
      const res = await window.pywebview.api.open_sendto_entry_location(entryPath);
      if (res && !res.success) {
        this.addLog("warning", res.message);
      }
    } catch (err) {
      this.addLog("error", `Lỗi mở vị trí: ${err.message || err}`);
    }
  },

  async openSendToFolder() {
    if (window.pywebview?.api?.open_sendto_folder) {
      try {
        const res = await window.pywebview.api.open_sendto_folder();
        this.addLog(res.success ? "success" : "error", res.message);
      } catch (err) {
        this.addLog("error", `Lỗi mở thư mục SendTo: ${err.message || err}`);
      }
    }
  }
});
