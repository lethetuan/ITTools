/**
 * IT-Tools 2026 - System Drives, Folder Size Analyzer & Auto Shutdown Module
 */
Object.assign(AppController.prototype, {
  async loadSystemDrives() {
    const btnGroup = document.getElementById("drives-btn-group");
    if (!btnGroup) return;

    let drives = [];
    if (window.pywebview && window.pywebview.api) {
      drives = await window.pywebview.api.get_system_drives();
    } else {
      drives = [
        { drive: "C:\\", total: "256.0 GB", free: "120.5 GB", used: "135.5 GB", pct: 52.9 },
        { drive: "D:\\", total: "512.0 GB", free: "340.0 GB", used: "172.0 GB", pct: 33.6 }
      ];
    }

    if (drives && drives.length > 0) {
      let html = `<div style="width: 100%; font-size: 13px; font-weight: 700; color: #475569; margin-bottom: 8px;">💾 DANH SÁCH Ổ CỨNG HỆ THỐNG & TỔNG DUNG LƯỢNG:</div>
      <div style="display: flex; gap: 12px; flex-wrap: wrap; width: 100%;">`;

      drives.forEach(d => {
        const driveEscaped = d.drive.replace(/\\/g, '\\\\');
        const pct = d.pct || 0;
        const barColor = pct > 85 ? 'linear-gradient(90deg, #ef4444, #f97316)' : (pct > 70 ? 'linear-gradient(90deg, #f59e0b, #eab308)' : 'linear-gradient(90deg, #2563eb, #06b6d4)');

        html += `
          <div onclick="app.setFolderScanPath('${driveEscaped}')" style="cursor: pointer; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 12px 14px; flex: 1; min-width: 210px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: all 0.2s ease;" onmouseover="this.style.borderColor='#0284c7'; this.style.transform='translateY(-1px)';" onmouseout="this.style.borderColor='#cbd5e1'; this.style.transform='none';">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
              <span style="font-weight: 700; font-size: 15px; color: #0f172a; display: flex; align-items: center; gap: 6px;">
                <span>💾</span> Ổ ${d.drive}
              </span>
              <span class="badge" style="background: #eff6ff; color: #1d4ed8; font-size: 12px; font-weight: 700; padding: 3px 8px; border-radius: 6px;">
                Tổng ${d.total}
              </span>
            </div>
            <div style="font-size: 11.5px; color: #64748b; display: flex; justify-content: space-between; margin-bottom: 6px;">
              <span>Trống: <strong style="color: #16a34a;">${d.free}</strong></span>
              <span>Đã dùng: ${d.used} (${pct}%)</span>
            </div>
            <div style="width: 100%; background: #e2e8f0; height: 6px; border-radius: 3px; overflow: hidden;">
              <div style="width: ${pct}%; height: 100%; background: ${barColor}; border-radius: 3px;"></div>
            </div>
          </div>
        `;
      });
      html += `</div>`;
      btnGroup.innerHTML = html;
    }
  },

  setFolderScanPath(path) {
    const input = document.getElementById("folder-scan-input");
    if (input) input.value = path;
    this.runFolderSizeAnalysis(path);
  },

  async browseFolderForSize() {
    if (window.pywebview && window.pywebview.api) {
      const folderPath = await window.pywebview.api.browse_folder_for_size();
      if (folderPath) {
        const input = document.getElementById("folder-scan-input");
        if (input) input.value = folderPath;
        this.runFolderSizeAnalysis(folderPath);
      }
    } else {
      const path = prompt("Nhập đường dẫn thư mục cần quét:", "C:\\");
      if (path) this.setFolderScanPath(path);
    }
  },

  async runFolderSizeAnalysis(customPath) {
    const input = document.getElementById("folder-scan-input");
    const targetPath = customPath || (input ? input.value.trim() : "C:\\");
    if (!targetPath) {
      alert("Vui lòng nhập hoặc chọn đường dẫn thư mục!");
      return;
    }

    if (input && customPath) {
      input.value = customPath;
    }

    this.currentFolderScanPath = targetPath;
    this.addLog("info", `Đang phân tích dung lượng thư mục: ${targetPath}...`);

    const summaryCard = document.getElementById("folder-scan-summary");
    const progress = document.getElementById("folder-scan-progress");
    const tbody = document.getElementById("folder-size-list-body");
    const btnScan = document.getElementById("btn-run-folder-scan");

    const pathBadge = document.getElementById("folder-summary-path");
    const countsSpan = document.getElementById("folder-summary-counts");
    const totalSpan = document.getElementById("folder-summary-total");

    if (pathBadge) pathBadge.innerText = targetPath;
    if (countsSpan) countsSpan.innerText = "Đang quét các thư mục con & tập tin...";
    if (totalSpan) totalSpan.innerText = "Đang tính...";

    if (summaryCard) summaryCard.style.display = "block";
    if (progress) progress.style.display = "block";
    if (btnScan) btnScan.disabled = true;

    tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">
      <div>🔄 Đang quét dung lượng các thư mục con & tập tin tại <strong>${targetPath}</strong>...</div>
      <div class="text-xs text-muted mt-1">Quá trình này có thể mất vài giây tùy vào số lượng dữ liệu.</div>
    </td></tr>`;

    let data = null;
    if (window.pywebview && window.pywebview.api) {
      data = await window.pywebview.api.analyze_folder_size(targetPath);
    } else {
      data = {
        success: true,
        path: targetPath,
        total_size: "45.2 GB",
        total_bytes: 48534123456,
        item_count: 5,
        file_count: 1254,
        subfolder_count: 18,
        items: [
          { name: "Program Files", path: targetPath + "\\Program Files", is_dir: true, size_bytes: 21474836480, formatted_size: "20.0 GB", file_count: 450, pct: 44.2 },
          { name: "Windows", path: targetPath + "\\Windows", is_dir: true, size_bytes: 16106127360, formatted_size: "15.0 GB", file_count: 620, pct: 33.1 },
          { name: "Users", path: targetPath + "\\Users", is_dir: true, size_bytes: 8589934592, formatted_size: "8.0 GB", file_count: 180, pct: 17.6 },
          { name: "pagefile.sys", path: targetPath + "\\pagefile.sys", is_dir: false, size_bytes: 2147483648, formatted_size: "2.0 GB", file_count: 1, pct: 4.4 }
        ]
      };
    }

    if (progress) progress.style.display = "none";
    if (btnScan) btnScan.disabled = false;

    if (!data || !data.success) {
      const msg = data ? data.message : "Lỗi không xác định khi quét thư mục!";
      this.addLog("error", msg);
      tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-danger">⚠️ ${msg}</td></tr>`;
      return;
    }

    this.lastFolderScanData = data;
    if (!this.folderSortCol) this.folderSortCol = 'size_bytes';
    if (!this.folderSortOrder) this.folderSortOrder = 'desc';

    this.sortFolderSizeResults(this.folderSortCol, true);
  },

  sortFolderSizeResults(colName, forceResort = false) {
    if (!this.lastFolderScanData || !this.lastFolderScanData.items) return;

    if (!forceResort) {
      if (this.folderSortCol === colName) {
        this.folderSortOrder = (this.folderSortOrder === 'asc') ? 'desc' : 'asc';
      } else {
        this.folderSortCol = colName;
        this.folderSortOrder = (colName === 'name') ? 'asc' : 'desc';
      }
    }

    const order = this.folderSortOrder === 'asc' ? 1 : -1;
    this.lastFolderScanData.items.sort((a, b) => {
      if (colName === 'name') {
        return order * (a.name || '').localeCompare(b.name || '', undefined, { numeric: true, sensitivity: 'base' });
      } else if (colName === 'is_dir') {
        const valA = a.is_dir ? 1 : 0;
        const valB = b.is_dir ? 1 : 0;
        return order * (valA - valB);
      } else if (colName === 'size_bytes') {
        return order * ((a.size_bytes || 0) - (b.size_bytes || 0));
      } else if (colName === 'pct') {
        return order * ((a.pct || 0) - (b.pct || 0));
      }
      return 0;
    });

    this.updateSortHeaderIcons();
    this.renderFolderSizeResults(this.lastFolderScanData);
  },

  updateSortHeaderIcons() {
    const cols = ['name', 'is_dir', 'size_bytes', 'pct'];
    cols.forEach(col => {
      const el = document.getElementById(`sort-icon-${col}`);
      if (!el) return;
      if (col === this.folderSortCol) {
        el.innerText = this.folderSortOrder === 'asc' ? '🔺' : '🔻';
        el.style.color = 'var(--primary)';
        el.style.opacity = '1';
      } else {
        el.innerText = '⇅';
        el.style.color = 'inherit';
        el.style.opacity = '0.6';
      }
    });
  },

  toggleExpandAllTreeNodes() {
    if (!this.lastFolderScanData || !this.lastFolderScanData.items) return;
    if (!this.expandedNodeIds) this.expandedNodeIds = new Set();

    const allNodeIds = [];
    const collectIds = (items) => {
      items.forEach(item => {
        if (item.is_dir && item.id) {
          allNodeIds.push(item.id);
          if (item.children && item.children.length > 0) {
            collectIds(item.children);
          }
        }
      });
    };
    collectIds(this.lastFolderScanData.items);

    if (this.expandedNodeIds.size >= allNodeIds.length && allNodeIds.length > 0) {
      this.expandedNodeIds.clear();
    } else {
      allNodeIds.forEach(id => this.expandedNodeIds.add(id));
    }
    this.renderFolderSizeResults(this.lastFolderScanData);
  },

  async toggleFolderNode(nodeId, path) {
    if (!this.expandedNodeIds) this.expandedNodeIds = new Set();

    if (this.expandedNodeIds.has(nodeId)) {
      this.expandedNodeIds.delete(nodeId);
      this.renderFolderSizeResults(this.lastFolderScanData);
    } else {
      this.expandedNodeIds.add(nodeId);

      const node = this.findNodeInTree(this.lastFolderScanData?.items, nodeId);
      if (node && node.is_dir && (!node.children || node.children.length === 0)) {
        node.loading = true;
        this.renderFolderSizeResults(this.lastFolderScanData);

        if (window.pywebview && window.pywebview.api) {
          const res = await window.pywebview.api.analyze_folder_size(path);
          node.loading = false;
          if (res && res.success && res.items) {
            node.children = res.items;
          } else {
            node.children = [];
          }
        } else {
          node.loading = false;
          node.children = [];
        }
      }
      this.renderFolderSizeResults(this.lastFolderScanData);
    }
  },

  findNodeInTree(items, nodeId) {
    if (!items) return null;
    for (const item of items) {
      if (item.id === nodeId) return item;
      if (item.children && item.children.length > 0) {
        const found = this.findNodeInTree(item.children, nodeId);
        if (found) return found;
      }
    }
    return null;
  },

  collectTreeRows(items, level = 0, rows = []) {
    if (!items) return rows;
    items.forEach(item => {
      if (!item.id) item.id = 'node_' + Math.random().toString(36).substr(2, 9);
      rows.push({ item, level });

      if (item.is_dir && this.expandedNodeIds && this.expandedNodeIds.has(item.id)) {
        if (item.children && item.children.length > 0) {
          this.collectTreeRows(item.children, level + 1, rows);
        } else if (item.loading) {
          rows.push({ is_loading: true, path: item.path, level: level + 1 });
        } else {
          rows.push({ is_empty: true, level: level + 1 });
        }
      }
    });
    return rows;
  },

  renderFolderSizeResults(data) {
    const pathBadge = document.getElementById("folder-summary-path");
    const countsSpan = document.getElementById("folder-summary-counts");
    const totalSpan = document.getElementById("folder-summary-total");
    const tbody = document.getElementById("folder-size-list-body");
    const btnUp = document.getElementById("btn-folder-up");

    if (pathBadge) pathBadge.innerText = data.path;
    if (countsSpan) countsSpan.innerText = `${data.subfolder_count} thư mục • ${data.file_count} tập tin`;
    if (totalSpan) totalSpan.innerText = data.total_size;

    const hasParent = data.path.length > 3;
    if (btnUp) btnUp.disabled = !hasParent;

    if (!data.items || data.items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">Thư mục trống hoặc không chứa tập tin truy cập được.</td></tr>`;
      return;
    }

    if (!this.expandedNodeIds) this.expandedNodeIds = new Set();
    const rows = this.collectTreeRows(data.items, 0, []);

    let html = "";
    rows.forEach(row => {
      if (row.is_loading) {
        html += `<tr>
          <td colspan="5" style="padding-left: ${(row.level * 22) + 16}px;" class="py-2 text-muted text-xs">
            <span class="spinner-border spinner-border-sm me-1" role="status"></span> Đang tải thư mục con...
          </td>
        </tr>`;
        return;
      }
      if (row.is_empty) {
        html += `<tr>
          <td colspan="5" style="padding-left: ${(row.level * 22) + 16}px;" class="py-2 text-muted text-xs italic">
            └─ <em>(Thư mục trống)</em>
          </td>
        </tr>`;
        return;
      }

      const item = row.item;
      const level = row.level;
      const isExpanded = this.expandedNodeIds.has(item.id);
      const icon = item.is_dir ? (isExpanded ? "📂" : "📁") : "📄";
      const typeText = item.is_dir ? `<span class="badge" style="background:#e0f2fe; color:#0369a1; padding: 2px 6px; border-radius: 4px;">Thư Mục</span>` : `<span class="badge" style="background:#f1f5f9; color:#475569; padding: 2px 6px; border-radius: 4px;">Tập Tin</span>`;
      const pct = item.pct || 0;
      const pathEscaped = (item.path || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'");
      const itemIdEscaped = (item.id || '').replace(/'/g, "\\'");

      html += `<tr>
        <td>
          <div style="display:flex; align-items:center; gap:6px; padding-left: ${level * 22}px;">
            ${item.is_dir ? `
              <span onclick="app.toggleFolderNode('${itemIdEscaped}', '${pathEscaped}')" style="cursor: pointer; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: #0284c7; background: #e0f2fe; border-radius: 4px; flex-shrink: 0; user-select: none;" title="${isExpanded ? 'Gập gọn' : 'Mở rộng tree'}">
                ${isExpanded ? '▼' : '▶'}
              </span>
            ` : `
              <span style="width: 22px; flex-shrink: 0; text-align: center; color: #cbd5e1; font-size: 10px;">•</span>
            `}
            <span style="font-size: 16px; flex-shrink: 0;">${icon}</span>
            <div style="min-width: 0; overflow: hidden; text-overflow: ellipsis;">
              <strong style="color: var(--text-main); font-size:13px;">${item.name}</strong>
              ${item.is_dir ? `<span class="text-xs text-muted" style="margin-left: 4px;">(${item.file_count || 0})</span>` : ''}
            </div>
          </div>
        </td>
        <td>${typeText}</td>
        <td><strong style="color: var(--primary); font-size:13px;">${item.formatted_size}</strong></td>
        <td>
          <div style="display: flex; align-items: center; gap: 8px;">
            <div style="flex: 1; background: #e2e8f0; height: 10px; border-radius: 5px; overflow: hidden;">
              <div style="width: ${pct}%; height: 100%; background: linear-gradient(90deg, #0284c7, #06b6d4); border-radius: 5px;"></div>
            </div>
            <span style="font-weight: 600; font-size: 12px; min-width: 45px; text-align: right;">${pct}%</span>
          </div>
        </td>
        <td style="text-align: right;">
          <div style="display: flex; gap: 4px; justify-content: flex-end;">
            ${item.is_dir ? `<button class="btn btn-sky-outline btn-sm" onclick="app.setFolderScanPath('${pathEscaped}')" title="Mở thư mục này làm vị trí quét chính">🔍 Quét</button>` : ''}
            <button class="btn btn-slate-light btn-sm" onclick="app.openFolderInExplorer('${pathEscaped}')" title="Mở trong File Explorer">📂 Mở</button>
            <button class="btn btn-rose-light btn-sm" onclick="app.deleteFolderSizeItem('${pathEscaped}')" title="Xóa vĩnh viễn">🗑️ Xóa</button>
          </div>
        </td>
      </tr>`;
    });

    tbody.innerHTML = html;
  },

  scanParentFolder() {
    if (!this.currentFolderScanPath) return;
    let parts = this.currentFolderScanPath.replace(/\\$/, '').split('\\');
    if (parts.length > 1) {
      parts.pop();
      let parentPath = parts.join('\\');
      if (parts.length === 1) parentPath += '\\';
      this.setFolderScanPath(parentPath);
    }
  },

  async openFolderInExplorer(path) {
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.open_path_in_explorer(path);
    }
  },

  async deleteFolderSizeItem(path) {
    if (confirm(`⚠️ Bạn có chắc chắn muốn XÓA VĨNH VIỄN?\n\n${path}\n\nThao tác này KHÔNG THỂ HOÀN TÁC!`)) {
      this.addLog("info", `Đang xóa: ${path}...`);
      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.delete_folder_item(path);
        if (res.success) {
          this.addLog("success", res.message);
          this.runFolderSizeAnalysis(this.currentFolderScanPath);
        } else {
          this.addLog("error", res.message);
          alert(`Lỗi xóa: ${res.message}`);
        }
      }
    }
  }
});
