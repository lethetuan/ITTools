/**
 * ════════════════════════════════════════════════════════════════════════════
 *  IT Tool LTT 2026 - Zoom Screen Frontend Controller (ZoomIt Native Engine)
 *  Author: Lê Thế Tuấn | 0352 194 195 | https://lethetuanpc.blogspot.com
 * ════════════════════════════════════════════════════════════════════════════
 */

(function () {
  'use strict';

  class ZoomScreenController {
    constructor() {
      this.initialized = false;
      this.currentSubTab = 'subtab-zs-zoom';
      this.status = {
        running: false,
        pid: null,
        binary_found: false,
        binary_path: '',
        custom_hotkeys: {},
        hotkey_status: {},
        action_names: {},
        settings: {}
      };
      this.defaultHotkeys = {
        zoom: "Ctrl + 1",
        draw: "Ctrl + 2",
        break: "Ctrl + 3",
        livezoom: "Ctrl + 4",
        record: "Ctrl + 5",
        snip: "Ctrl + 6",
        demotype: "Ctrl + 7",
        panorama: "Ctrl + 8",
        mirror: "Ctrl + 9"
      };
      this.actionDescriptions = {
        zoom: "Phóng to sắc nét theo con trỏ chuột, cuộn chuột phóng to/thu nhỏ",
        draw: "Vẽ bút màu, mũi tên, hình hộp, elip trực tiếp lên màn hình",
        break: "Đồng hồ đếm ngược giải lao toàn màn hình kèm chuông báo",
        livezoom: "Phóng to màn hình vẫn thao tác chuột & gõ phím bình thường",
        record: "Quay video bài giảng MP4 hoặc ảnh động GIF màn hình",
        snip: "Cắt chụp một vùng màn hình và tự động sao chép Clipboard",
        demotype: "Tự động gõ từng ký tự mượt mà khi trình diễn demo",
        panorama: "Chụp ảnh cuộn trang dài (tự động ghép ảnh khi cuộn)",
        mirror: "Chiếu nhân bản phóng to sang máy chiếu / màn hình ngoài thứ 2"
      };
      this.editingAction = null;
      this.recordedHotkey = '';
      this.statusPollInterval = null;
    }

    init() {
      if (this.initialized) return;
      this.initialized = true;

      this.bindEvents();
      this.loadStatus();
    }

    bindEvents() {
      // Subtab switching
      const subtabBtns = document.querySelectorAll('#tab-zoom-screen .subtab-btn');
      subtabBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          const targetSubtab = btn.getAttribute('data-subtab');
          if (!targetSubtab) return;

          subtabBtns.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');

          const parent = document.getElementById('tab-zoom-screen');
          if (parent) {
            parent.querySelectorAll('.subtab-content').forEach(c => c.classList.remove('active'));
            const targetContent = document.getElementById(targetSubtab);
            if (targetContent) targetContent.classList.add('active');
          }
          this.currentSubTab = targetSubtab;
        });
      });

      // Pen width slider feedback
      const penSlider = document.getElementById('zs-pen-width-slider');
      if (penSlider) {
        penSlider.addEventListener('input', () => {
          const valEl = document.getElementById('zs-pen-width-val');
          if (valEl) valEl.textContent = penSlider.value + ' px';
          const preview = document.getElementById('zs-pen-preview');
          if (preview) preview.style.height = penSlider.value + 'px';
        });
      }

      // Break timer slider feedback
      const breakSlider = document.getElementById('zs-break-time-slider');
      if (breakSlider) {
        breakSlider.addEventListener('input', () => {
          const valEl = document.getElementById('zs-break-time-val');
          if (valEl) valEl.textContent = breakSlider.value + ' phút';
        });
      }

      // Break opacity slider feedback
      const opacitySlider = document.getElementById('zs-break-opacity-slider');
      if (opacitySlider) {
        opacitySlider.addEventListener('input', () => {
          const valEl = document.getElementById('zs-break-opacity-val');
          if (valEl) valEl.textContent = opacitySlider.value + '%';
        });
      }

      // DemoType speed slider feedback
      const dtSpeedSlider = document.getElementById('zs-demotype-speed');
      if (dtSpeedSlider) {
        dtSpeedSlider.addEventListener('input', () => {
          const valEl = document.getElementById('zs-demotype-speed-val');
          if (valEl) {
            const v = parseInt(dtSpeedSlider.value, 10);
            let label = 'Vừa phải';
            if (v < 35) label = 'Chậm rãi';
            else if (v > 75) label = 'Rất nhanh';
            else if (v > 55) label = 'Nhanh';
            valEl.textContent = `${v} (${label})`;
          }
        });
      }

      // Color swatch selection
      document.querySelectorAll('.zs-color-swatch').forEach(swatch => {
        swatch.addEventListener('click', () => {
          document.querySelectorAll('.zs-color-swatch').forEach(s => s.classList.remove('selected'));
          swatch.classList.add('selected');
          const preview = document.getElementById('zs-pen-preview');
          if (preview) preview.style.background = swatch.getAttribute('data-color');
        });
      });

      // Hotkey Recorder Box events
      const recorderBox = document.getElementById('zs-recorder-box');
      if (recorderBox) {
        recorderBox.addEventListener('click', () => {
          recorderBox.focus();
        });
      }

      // Close modal on backdrop click
      const modal = document.getElementById('zs-hotkey-modal');
      if (modal) {
        modal.addEventListener('click', (e) => {
          if (e.target === modal) this.closeHotkeyModal();
        });
      }
    }

    getKeyFromEvent(e) {
      const code = e.code || '';

      // Skip lone modifier keys
      if (['ControlLeft', 'ControlRight', 'AltLeft', 'AltRight', 'ShiftLeft', 'ShiftRight', 'MetaLeft', 'MetaRight'].includes(code)) {
        return null;
      }

      if (code.startsWith('Key')) {
        return code.slice(3).toUpperCase();
      }
      if (code.startsWith('Digit')) {
        return code.slice(5);
      }
      if (code.startsWith('Numpad')) {
        const sub = code.slice(6);
        if (/^\d$/.test(sub)) return 'Num ' + sub;
        const numMap = {
          'Add': '+',
          'Subtract': '-',
          'Multiply': '*',
          'Divide': '/',
          'Decimal': '.',
          'Enter': 'Enter'
        };
        return numMap[sub] || sub;
      }
      if (/^F([1-9]|1[0-9]|2[0-4])$/.test(code)) {
        return code;
      }

      const specialMap = {
        'Space': 'Space',
        'Tab': 'Tab',
        'Enter': 'Enter',
        'Escape': 'Esc',
        'Backspace': 'Backspace',
        'Delete': 'Delete',
        'Insert': 'Insert',
        'Home': 'Home',
        'End': 'End',
        'PageUp': 'PageUp',
        'PageDown': 'PageDown',
        'ArrowUp': 'Up',
        'ArrowDown': 'Down',
        'ArrowLeft': 'Left',
        'ArrowRight': 'Right',
        'Minus': '-',
        'Equal': '=',
        'BracketLeft': '[',
        'BracketRight': ']',
        'Backslash': '\\',
        'Semicolon': ';',
        'Quote': "'",
        'Backquote': '`',
        'Comma': ',',
        'Period': '.',
        'Slash': '/'
      };

      if (specialMap[code]) {
        return specialMap[code];
      }

      if (e.key && e.key.length === 1) {
        return e.key.toUpperCase();
      }

      return e.key || code;
    }

    normalizeHotkey(str) {
      if (!str) return '';
      let s = String(str).trim();
      let isPlusKey = false;
      if (s.endsWith('++') || s.endsWith('+ +')) {
        isPlusKey = true;
        s = s.slice(0, -1).replace(/\++$/, '').trim();
      }

      const parts = s.split('+').map(p => p.trim()).filter(Boolean);
      let ctrl = false, alt = false, shift = false, win = false;
      let key = '';

      for (const p of parts) {
        const lp = p.toLowerCase();
        if (lp === 'ctrl' || lp === 'control') ctrl = true;
        else if (lp === 'alt' || lp === 'menu') alt = true;
        else if (lp === 'shift') shift = true;
        else if (lp === 'win' || lp === 'windows' || lp === 'meta' || lp === 'super') win = true;
        else if (!key) key = p;
      }

      if (isPlusKey) key = '+';
      if (!key) return '';

      const keyUpper = key.toUpperCase();
      if (keyUpper.startsWith('NUMPAD') || keyUpper.startsWith('NUM ')) {
        const sub = keyUpper.replace('NUMPAD', '').replace('NUM', '').trim();
        if (/^\d$/.test(sub)) key = 'Num ' + sub;
      } else if (key.length === 1) {
        key = key.toUpperCase();
      } else if (/^F\d{1,2}$/i.test(key)) {
        key = key.toUpperCase();
      } else {
        const specMap = {
          'SPACE': 'Space', 'TAB': 'Tab', 'ENTER': 'Enter', 'RETURN': 'Enter',
          'ESC': 'Esc', 'ESCAPE': 'Esc', 'INSERT': 'Insert', 'DELETE': 'Delete',
          'HOME': 'Home', 'END': 'End', 'PAGEUP': 'PageUp', 'PAGEDOWN': 'PageDown',
          'UP': 'Up', 'DOWN': 'Down', 'LEFT': 'Left', 'RIGHT': 'Right',
          'BACKSPACE': 'Backspace', 'PRINTSCREEN': 'PrintScreen', 'PAUSE': 'Pause'
        };
        key = specMap[keyUpper] || (key.charAt(0).toUpperCase() + key.slice(1).toLowerCase());
      }

      const res = [];
      if (ctrl) res.push('Ctrl');
      if (alt) res.push('Alt');
      if (shift) res.push('Shift');
      if (win) res.push('Win');
      res.push(key);
      return res.join(' + ');
    }

    handleRecorderKeyDown(e) {
      // If modal is not open, ignore
      const modal = document.getElementById('zs-hotkey-modal');
      if (!modal || modal.style.display === 'none') return;

      e.preventDefault();
      e.stopPropagation();

      // Lone Escape closes modal
      if (e.key === 'Escape' && !e.ctrlKey && !e.altKey && !e.shiftKey && !e.metaKey) {
        this.closeHotkeyModal();
        return;
      }

      // Lone Enter saves if valid
      if (e.key === 'Enter' && !e.ctrlKey && !e.altKey && !e.shiftKey && !e.metaKey) {
        const btnSave = document.getElementById('zs-btn-save-modal-hk');
        if (btnSave && !btnSave.disabled) {
          this.saveModalHotkey();
          return;
        }
      }

      // Lone Backspace or Delete resets to prompt
      if ((e.key === 'Backspace' || e.key === 'Delete') && !e.ctrlKey && !e.altKey && !e.shiftKey && !e.metaKey) {
        this.recordedHotkey = '';
        const txtEl = document.getElementById('zs-recorder-text');
        if (txtEl) txtEl.textContent = 'Nhấn tổ hợp phím mới...';
        const box = document.getElementById('zs-recorder-box');
        if (box) box.className = 'zs-recorder-box focus-pulse';
        const fb = document.getElementById('zs-recorder-feedback');
        if (fb) fb.innerHTML = '<span style="color: var(--text-muted);">Đã xóa. Hãy nhấn tổ hợp phím bạn muốn gán.</span>';
        const btnSave = document.getElementById('zs-btn-save-modal-hk');
        if (btnSave) btnSave.disabled = true;
        return;
      }

      const mainKey = this.getKeyFromEvent(e);

      // Handle intermediate lone modifier keydown (Ctrl, Alt, Shift, Win alone)
      if (!mainKey) {
        const mods = [];
        if (e.ctrlKey) mods.push('Ctrl');
        if (e.altKey) mods.push('Alt');
        if (e.shiftKey) mods.push('Shift');
        if (e.metaKey) mods.push('Win');
        const txtEl = document.getElementById('zs-recorder-text');
        if (txtEl) txtEl.textContent = mods.length > 0 ? (mods.join(' + ') + ' + ...') : 'Nhấn phím...';
        const box = document.getElementById('zs-recorder-box');
        if (box) box.className = 'zs-recorder-box focus-pulse';
        const fb = document.getElementById('zs-recorder-feedback');
        if (fb) fb.innerHTML = '<span style="color: #38bdf8;">Đang giữ phím bổ trợ, hãy nhấn thêm một phím chính (A-Z, 0-9, F1-F12...)...</span>';
        const btnSave = document.getElementById('zs-btn-save-modal-hk');
        if (btnSave) btnSave.disabled = true;
        return;
      }

      // Build complete hotkey combination
      const parts = [];
      if (e.ctrlKey) parts.push('Ctrl');
      if (e.altKey) parts.push('Alt');
      if (e.shiftKey) parts.push('Shift');
      if (e.metaKey) parts.push('Win');
      parts.push(mainKey);

      const formatted = parts.join(' + ');
      this.recordedHotkey = formatted;

      const txtEl = document.getElementById('zs-recorder-text');
      if (txtEl) txtEl.textContent = formatted;

      this.syncManualPicker(formatted);
      this.validateRecordedHotkey(formatted);
    }

    applySuggestedHotkey(hk) {
      this.recordedHotkey = hk;
      const txtEl = document.getElementById('zs-recorder-text');
      if (txtEl) txtEl.textContent = hk;
      this.syncManualPicker(hk);
      this.validateRecordedHotkey(hk);
    }

    syncManualPicker(formatted) {
      if (!formatted) return;
      const norm = this.normalizeHotkey(formatted);
      const parts = norm.split(' + ');
      const key = parts[parts.length - 1];
      const hasCtrl = parts.includes('Ctrl');
      const hasAlt = parts.includes('Alt');
      const hasShift = parts.includes('Shift');
      const hasWin = parts.includes('Win');

      const cCtrl = document.getElementById('zs-mod-ctrl');
      const cAlt = document.getElementById('zs-mod-alt');
      const cShift = document.getElementById('zs-mod-shift');
      const cWin = document.getElementById('zs-mod-win');
      const sKey = document.getElementById('zs-select-key');

      if (cCtrl) cCtrl.checked = hasCtrl;
      if (cAlt) cAlt.checked = hasAlt;
      if (cShift) cShift.checked = hasShift;
      if (cWin) cWin.checked = hasWin;
      if (sKey && key) {
        for (let i = 0; i < sKey.options.length; i++) {
          if (sKey.options[i].value.toUpperCase() === key.toUpperCase()) {
            sKey.selectedIndex = i;
            break;
          }
        }
      }
    }

    updateFromManualPicker() {
      const ctrl = document.getElementById('zs-mod-ctrl')?.checked;
      const alt = document.getElementById('zs-mod-alt')?.checked;
      const shift = document.getElementById('zs-mod-shift')?.checked;
      const win = document.getElementById('zs-mod-win')?.checked;
      const key = document.getElementById('zs-select-key')?.value;

      const parts = [];
      if (ctrl) parts.push('Ctrl');
      if (alt) parts.push('Alt');
      if (shift) parts.push('Shift');
      if (win) parts.push('Win');
      if (key) parts.push(key);

      const formatted = parts.join(' + ');
      this.recordedHotkey = formatted;
      const txtEl = document.getElementById('zs-recorder-text');
      if (txtEl) txtEl.textContent = formatted || 'Chọn phím...';
      this.validateRecordedHotkey(formatted);
    }

    validateRecordedHotkey(formatted) {
      const norm = this.normalizeHotkey(formatted);
      const box = document.getElementById('zs-recorder-box');
      const fb = document.getElementById('zs-recorder-feedback');
      const btnSave = document.getElementById('zs-btn-save-modal-hk');

      if (!norm || norm.endsWith('+')) {
        if (box) box.className = 'zs-recorder-box focus-pulse';
        if (fb) fb.innerHTML = '<span style="color: var(--text-muted);">Vui lòng nhấn tổ hợp phím hoàn chỉnh.</span>';
        if (btnSave) btnSave.disabled = true;
        return false;
      }

      // Check if lone key without modifier is a single character letter or number
      const parts = norm.split(' + ');
      const hasModifiers = parts.length > 1;
      const lastKey = parts[parts.length - 1];

      // Single alphanumeric key MUST have at least one modifier
      if (!hasModifiers && /^[A-Z0-9]$/i.test(lastKey)) {
        if (box) box.className = 'zs-recorder-box conflict';
        if (fb) {
          fb.innerHTML = '<span style="color: #f59e0b; font-weight: 700;">⚠️ Phím chữ/số cần kết hợp thêm Ctrl hoặc Alt để tránh cản trở gõ văn bản!</span>';
        }
        if (btnSave) btnSave.disabled = true;
        return false;
      }

      // Check duplicate against other actions
      const currentHotkeys = Object.assign({}, this.defaultHotkeys, this.status.custom_hotkeys || {});
      let conflictAction = null;

      for (const [act, hk] of Object.entries(currentHotkeys)) {
        if (act === this.editingAction) continue;
        if (this.normalizeHotkey(hk) === norm) {
          conflictAction = act;
          break;
        }
      }

      if (conflictAction) {
        const actName = this.status.action_names?.[conflictAction] || conflictAction;
        if (box) box.className = 'zs-recorder-box conflict';
        if (fb) {
          fb.innerHTML = `<span style="color: #ef4444; font-weight: 700;">❌ Bị trùng với: <strong>${actName}</strong> (${currentHotkeys[conflictAction]})! Hãy chọn phím khác.</span>`;
        }
        if (btnSave) btnSave.disabled = true;
        return false;
      }

      // Valid & no conflict
      if (box) box.className = 'zs-recorder-box valid';
      if (fb) {
        fb.innerHTML = '<span style="color: #10b981; font-weight: 700;">✅ Phím tắt hợp lệ, không bị trùng lặp với chức năng khác!</span>';
      }
      if (btnSave) btnSave.disabled = false;
      return true;
    }

    async openHotkeyModal(actionName) {
      this.editingAction = actionName;
      const hotkeys = Object.assign({}, this.defaultHotkeys, this.status.custom_hotkeys || {});
      const currentHk = hotkeys[actionName] || this.defaultHotkeys[actionName] || '';
      this.recordedHotkey = currentHk;

      // Temporarily pause background hotkeys so user can press any key freely
      try {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.pause_zoom_screen_hotkeys) {
          await window.pywebview.api.pause_zoom_screen_hotkeys();
        }
      } catch (e) {
        console.warn("Pause hotkeys notice:", e);
      }

      const actTitle = this.status.action_names?.[actionName] || actionName;
      const titleEl = document.getElementById('zs-modal-title');
      if (titleEl) {
        titleEl.textContent = `⌨️ Đổi Phím Tắt: ${actTitle}`;
      }

      const txtEl = document.getElementById('zs-recorder-text');
      if (txtEl) txtEl.textContent = currentHk || 'Nhấn tổ hợp phím mới...';

      const modal = document.getElementById('zs-hotkey-modal');
      if (modal) modal.style.display = 'flex';

      this.validateRecordedHotkey(currentHk);
      this.syncManualPicker(currentHk);

      // Attach global capture-phase listener so keystrokes anywhere in modal are recorded
      if (this._globalKeyHandler) {
        window.removeEventListener('keydown', this._globalKeyHandler, true);
      }
      this._globalKeyHandler = (e) => this.handleRecorderKeyDown(e);
      window.addEventListener('keydown', this._globalKeyHandler, true);

      const box = document.getElementById('zs-recorder-box');
      if (box) {
        box.classList.add('focus-pulse');
        setTimeout(() => box.focus(), 60);
      }
    }

    async closeHotkeyModal() {
      // Remove global keydown handler
      if (this._globalKeyHandler) {
        window.removeEventListener('keydown', this._globalKeyHandler, true);
        this._globalKeyHandler = null;
      }

      const modal = document.getElementById('zs-hotkey-modal');
      if (modal) modal.style.display = 'none';
      this.editingAction = null;

      // Resume background hotkeys
      try {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.resume_zoom_screen_hotkeys) {
          await window.pywebview.api.resume_zoom_screen_hotkeys();
        }
      } catch (e) {
        console.warn("Resume hotkeys notice:", e);
      }
    }

    resetCurrentModalHotkey() {
      if (!this.editingAction) return;
      const defHk = this.defaultHotkeys[this.editingAction] || 'Ctrl + 1';
      this.recordedHotkey = defHk;
      const txtEl = document.getElementById('zs-recorder-text');
      if (txtEl) txtEl.textContent = defHk;
      this.syncManualPicker(defHk);
      this.validateRecordedHotkey(defHk);
    }

    showToast(type, message) {
      if (window.app && typeof window.app.showToast === 'function') {
        window.app.showToast(type, message);
        return;
      }
      let container = document.getElementById('zs-toast-container');
      if (!container) {
        container = document.createElement('div');
        container.id = 'zs-toast-container';
        container.style.cssText = 'position: fixed; top: 24px; right: 24px; z-index: 9999999; display: flex; flex-direction: column; gap: 8px; pointer-events: none;';
        document.body.appendChild(container);
      }
      // Giới hạn tối đa 2 thông báo cùng lúc để tránh xếp tầng màn hình
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
      }, 4000);
    }

    async saveModalHotkey() {
      if (!this.editingAction || !this.recordedHotkey) return;
      const actionName = this.editingAction;
      const hotkeyStr = this.recordedHotkey;

      try {
        if (!window.pywebview || !window.pywebview.api) {
          await this.closeHotkeyModal();
          return;
        }

        const res = await window.pywebview.api.update_zoom_screen_hotkey(actionName, hotkeyStr);
        await this.closeHotkeyModal();

        if (res && res.success) {
          this.showToast(res.warning ? "warning" : "success", res.message || "Đã lưu phím tắt thành công!");
          await this.loadStatus();
        } else {
          const errMsg = (res && res.message) ? res.message : "Không thể lưu phím tắt!";
          this.showToast("error", errMsg);
        }
      } catch (err) {
        console.error("Lỗi cập nhật phím tắt:", err);
        await this.closeHotkeyModal();
        this.showToast("error", "Lỗi: " + err);
      }
    }

    async resetAllHotkeys() {
      if (!confirm('Bạn có chắc chắn muốn khôi phục toàn bộ phím tắt Zoom Screen về mặc định ban đầu không?')) {
        return;
      }
      try {
        if (!window.pywebview || !window.pywebview.api) return;
        const res = await window.pywebview.api.reset_zoom_screen_hotkeys();
        if (res && res.message) {
          this.showToast(res.success ? "success" : "error", res.message);
        }
        await this.loadStatus();
      } catch (err) {
        console.error("Lỗi khôi phục phím tắt:", err);
      }
    }

    renderHotkeyTable() {
      const tbody = document.getElementById('zs-hotkey-tbody');
      if (!tbody) return;

      const hotkeys = this.status.custom_hotkeys || this.defaultHotkeys;
      const statusMap = this.status.hotkey_status || {};
      const actionNames = this.status.action_names || {};
      const isRunning = this.status.running;

      const actionOrder = ['zoom', 'draw', 'break', 'livezoom', 'record', 'snip', 'demotype', 'panorama', 'mirror'];

      let html = '';
      for (const act of actionOrder) {
        const name = actionNames[act] || act;
        const hk = hotkeys[act] || this.defaultHotkeys[act] || '';
        const desc = this.actionDescriptions[act] || '';
        const st = statusMap[act];

        let statusBadge = '';
        if (!isRunning) {
          statusBadge = '<span class="badge bg-secondary" style="font-size: 11px;">⚪ Chờ kích hoạt</span>';
        } else if (st && st.registered) {
          statusBadge = '<span class="badge bg-success" style="font-size: 11px;">🟢 Đã đăng ký Windows</span>';
        } else if (st && st.error === 1409) {
          statusBadge = '<span class="badge bg-danger" style="font-size: 11px;" title="Phím tắt này đang bị ứng dụng khác trong Windows chiếm giữ!">⚠️ Bị ứng dụng khác chiếm</span>';
        } else {
          statusBadge = '<span class="badge bg-warning" style="font-size: 11px;" title="Đăng ký thất bại với Windows API">⚠️ Lỗi đăng ký</span>';
        }

        html += `
          <tr>
            <td>
              <div style="font-weight: 700; color: var(--text-main);">${name}</div>
            </td>
            <td>
              <kbd class="zs-kbd editable" onclick="zoomScreen.openHotkeyModal('${act}')" title="Bấm vào để đổi phím tắt">${hk}</kbd>
            </td>
            <td>${statusBadge}</td>
            <td style="color: var(--text-muted); font-size: 12px;">${desc}</td>
            <td style="text-align: center;">
              <button class="btn btn-sm btn-sky-outline" onclick="zoomScreen.openHotkeyModal('${act}')" style="font-size: 11px; padding: 2px 8px; font-weight: 600;">
                ✏️ Đổi phím
              </button>
            </td>
          </tr>
        `;
      }

      tbody.innerHTML = html;

      // Update quick buttons labels and disabled state in Quick Action Strip
      const quickBtns = document.querySelectorAll('.zs-quick-btns button');
      if (quickBtns && quickBtns.length > 0) {
        const map = {
          zoom: '🔍 Phóng to',
          livezoom: '⚡ LiveZoom',
          draw: '✏️ Vẽ',
          break: '⏳ Đếm ngược',
          record: '🎥 Quay video',
          snip: '✂️ Chụp ảnh',
          demotype: '⌨️ DemoType',
          mirror: '🪞 Chiếu Mirror'
        };
        quickBtns.forEach(btn => {
          const onclickStr = btn.getAttribute('onclick') || '';
          for (const [k, title] of Object.entries(map)) {
            if (onclickStr.includes(`'${k}'`)) {
              const hk = hotkeys[k] || this.defaultHotkeys[k] || '';
              btn.innerHTML = `${title} (<kbd>${hk}</kbd>)`;
              if (!isRunning) {
                btn.style.opacity = '0.55';
                btn.style.filter = 'grayscale(60%)';
                btn.title = `Zoom Screen ngầm đang TẮT! Bấm "▶️ Bật Zoom Screen Ngầm" trước khi sử dụng ${title} (${hk})`;
              } else {
                btn.style.opacity = '1';
                btn.style.filter = 'none';
                btn.title = `Kích hoạt ngay: ${title} (${hk})`;
              }
              break;
            }
          }
        });
      }
    }

    async loadStatus() {
      try {
        if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.get_zoom_screen_status) {
          return;
        }

        const res = await window.pywebview.api.get_zoom_screen_status();
        if (res) {
          this.status = res;
          this.updateUI();
        }
      } catch (err) {
        console.error("Lỗi lấy trạng thái Zoom Screen:", err);
      }
    }

    updateUI() {
      const running = this.status.running;
      const settings = this.status.settings || {};

      // Status Badge & Text
      const badge = document.getElementById('zs-status-badge');
      const text = document.getElementById('zs-status-text');
      const startBtn = document.getElementById('zs-btn-start');
      const stopBtn = document.getElementById('zs-btn-stop');

      if (badge && text) {
        if (running) {
          badge.className = 'badge bg-success';
          badge.textContent = 'ĐANG CHẠY';
          text.innerHTML = `<span style="color:#10b981; font-weight:700;">🟢 Đang hoạt động ngầm</span> (PID: <strong>${this.status.pid || 'Active'}</strong>) — Phím tắt toàn cầu luôn sẵn sàng mọi lúc!`;
          if (startBtn) startBtn.style.display = 'none';
          if (stopBtn) stopBtn.style.display = 'inline-flex';
        } else {
          badge.className = 'badge bg-secondary';
          badge.textContent = 'ĐANG TẮT';
          text.innerHTML = `<span style="color:#64748b;">⚪ Đang tạm tắt</span> — Bấm nút bên phải để bật chế độ phóng to & phím tắt toàn cầu.`;
          if (startBtn) startBtn.style.display = 'inline-flex';
          if (stopBtn) stopBtn.style.display = 'none';
        }
      }

      // Binary status
      const pathEl = document.getElementById('zs-binary-path');
      if (pathEl) {
        pathEl.textContent = this.status.binary_path || 'Native Python Engine (100% Độc lập)';
      }

      // Render Dynamic Hotkey Table
      this.renderHotkeyTable();

      // Populate Settings into inputs
      // 1. Zoom Slider Level
      const zoomLevel = settings.SliderZoomLevel ?? 3;
      const zoomRadio = document.querySelector(`input[name="zs_zoom_level"][value="${zoomLevel}"]`);
      if (zoomRadio) zoomRadio.checked = true;

      // 2. Animate Zoom & Smooth Image
      const animZoom = document.getElementById('zs-opt-animate-zoom');
      if (animZoom) animZoom.checked = Boolean(settings.AnimnateZoom ?? 1);

      const smoothImg = document.getElementById('zs-opt-smooth-image');
      if (smoothImg) smoothImg.checked = Boolean(settings.SmoothImage ?? 1);

      const snapGrid = document.getElementById('zs-opt-snap-grid');
      if (snapGrid) snapGrid.checked = Boolean(settings.SnapToGrid ?? 1);

      // 3. Pen Width & Color
      const penWidth = settings.PenWidth ?? 5;
      const penSlider = document.getElementById('zs-pen-width-slider');
      if (penSlider) {
        penSlider.value = penWidth;
        const valEl = document.getElementById('zs-pen-width-val');
        if (valEl) valEl.textContent = penWidth + ' px';
      }

      // 4. Break Timer
      const breakTime = settings.BreakTimeout ?? 10;
      const breakSlider = document.getElementById('zs-break-time-slider');
      if (breakSlider) {
        breakSlider.value = breakTime;
        const valEl = document.getElementById('zs-break-time-val');
        if (valEl) valEl.textContent = breakTime + ' phút';
      }

      const breakOpacity = settings.BreakOpacity ?? 100;
      const opacitySlider = document.getElementById('zs-break-opacity-slider');
      if (opacitySlider) {
        opacitySlider.value = breakOpacity;
        const valEl = document.getElementById('zs-break-opacity-val');
        if (valEl) valEl.textContent = breakOpacity + '%';
      }

      const showDesktop = document.getElementById('zs-opt-break-show-desktop');
      if (showDesktop) showDesktop.checked = Boolean(settings.BreakShowDesktop ?? 1);

      const lockStation = document.getElementById('zs-opt-break-lock');
      if (lockStation) lockStation.checked = Boolean(settings.BreakLockWorkstation ?? 0);

      // 5. Recording
      const recFormat = settings.RecordingFormat ?? 1;
      const recRadio = document.querySelector(`input[name="zs_rec_format"][value="${recFormat}"]`);
      if (recRadio) recRadio.checked = true;

      const recSysAudio = document.getElementById('zs-opt-rec-sys-audio');
      if (recSysAudio) recSysAudio.checked = Boolean(settings.CaptureSystemAudio ?? 1);

      const recMic = document.getElementById('zs-opt-rec-mic');
      if (recMic) recMic.checked = Boolean(settings.CaptureAudio ?? 0);

      const recNoise = document.getElementById('zs-opt-rec-noise');
      if (recNoise) recNoise.checked = Boolean(settings.NoiseCancellation ?? 1);

      const recAspect = document.getElementById('zs-opt-rec-aspect');
      if (recAspect) recAspect.checked = Boolean(settings.RecordAspectRatio ?? 0);

      // 6. Webcam Overlay
      const camOverlay = document.getElementById('zs-opt-cam-overlay');
      if (camOverlay) camOverlay.checked = Boolean(settings.WebcamOverlay ?? 0);

      const camPos = document.getElementById('zs-select-cam-pos');
      if (camPos) camPos.value = settings.WebcamPosition ?? 3;

      const camSize = document.getElementById('zs-select-cam-size');
      if (camSize) camSize.value = settings.WebcamSize ?? 1;

      const camShape = document.getElementById('zs-select-cam-shape');
      if (camShape) camShape.value = settings.WebcamShape ?? 0;

      const camBg = document.getElementById('zs-select-cam-bg');
      if (camBg) camBg.value = settings.WebcamBackgroundMode ?? 0;

      // 7. DemoType
      const dtSpeed = document.getElementById('zs-demotype-speed');
      if (dtSpeed) {
        dtSpeed.value = settings.DemoTypeSpeedSlider ?? 55;
        const dtVal = document.getElementById('zs-demotype-speed-val');
        if (dtVal) {
          const v = parseInt(dtSpeed.value, 10);
          let label = 'Vừa phải';
          if (v < 35) label = 'Chậm rãi';
          else if (v > 75) label = 'Rất nhanh';
          else if (v > 55) label = 'Nhanh';
          dtVal.textContent = `${v} (${label})`;
        }
      }

      const dtUserMode = document.getElementById('zs-opt-dt-user-mode');
      if (dtUserMode) dtUserMode.checked = Boolean(settings.DemoTypeUserDrivenMode ?? 0);

      const dtText = document.getElementById('zs-demotype-text');
      if (dtText && settings.DemoTypeText !== undefined && dtText.value === '') {
        dtText.value = settings.DemoTypeText;
      }

      // 8. Hotkeys display labels in subtab headers
      const hotkeys = this.status.custom_hotkeys || this.defaultHotkeys;
      const hkMap = {
        'zs-hk-zoom': hotkeys.zoom || 'Ctrl + 1',
        'zs-hk-draw': hotkeys.draw || 'Ctrl + 2',
        'zs-hk-break': hotkeys.break || 'Ctrl + 3',
        'zs-hk-livezoom': hotkeys.livezoom || 'Ctrl + 4',
        'zs-hk-record': hotkeys.record || 'Ctrl + 5',
        'zs-hk-snip': hotkeys.snip || 'Ctrl + 6',
        'zs-hk-demotype': hotkeys.demotype || 'Ctrl + 7',
        'zs-hk-panorama': hotkeys.panorama || 'Ctrl + 8',
        'zs-hk-mirror': hotkeys.mirror || 'Ctrl + 9',
      };
      Object.keys(hkMap).forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = hkMap[id];
      });
    }

    async start() {
      try {
        if (!window.pywebview || !window.pywebview.api) return;
        const res = await window.pywebview.api.start_zoom_screen();
        if (res && res.message) {
          this.showToast(res.success ? "success" : "error", res.message);
        }
        await this.loadStatus();
      } catch (err) {
        console.error("Lỗi khởi động Zoom Screen:", err);
      }
    }

    async stop() {
      try {
        if (!window.pywebview || !window.pywebview.api) return;
        const res = await window.pywebview.api.stop_zoom_screen();
        if (res && res.message) {
          this.showToast(res.success ? "info" : "error", res.message);
        }
        await this.loadStatus();
      } catch (err) {
        console.error("Lỗi dừng Zoom Screen:", err);
      }
    }

    async trigger(actionName) {
      if (!this.status || !this.status.running) {
        this.showToast("warning", "⚠️ Zoom Screen ngầm đang TẮT! Vui lòng bấm '▶️ Bật Zoom Screen Ngầm' trước khi sử dụng các tính năng.");
        return;
      }
      try {
        if (actionName === 'demotype') {
          // Lưu kịch bản và tốc độ trước khi gõ phím
          await this.saveSettings();
        }
        if (!window.pywebview || !window.pywebview.api) return;
        const res = await window.pywebview.api.trigger_zoom_action(actionName);
        if (res) {
          if (!res.success) {
            this.showToast("warning", res.message || "Không thể kích hoạt tính năng.");
          } else {
            this.showToast("success", res.message || "Đã kích hoạt thành công!");
          }
        }
        await this.loadStatus();
      } catch (err) {
        console.error(`Lỗi kích hoạt ${actionName}:`, err);
      }
    }

    async openNativeOptions() {
      try {
        if (!window.pywebview || !window.pywebview.api) return;
        const res = await window.pywebview.api.open_zoom_screen_native_options();
        if (res && res.message) {
          this.showToast("info", res.message);
        }
      } catch (err) {
        console.error("Lỗi mở cài đặt ZoomIt:", err);
      }
    }

    async saveSettings() {
      try {
        if (!window.pywebview || !window.pywebview.api) return;

        // Collect zoom level
        const zoomLevelChecked = document.querySelector('input[name="zs_zoom_level"]:checked');
        const zoomLevel = zoomLevelChecked ? parseInt(zoomLevelChecked.value, 10) : 3;

        // Collect pen width
        const penSlider = document.getElementById('zs-pen-width-slider');
        const penWidth = penSlider ? parseInt(penSlider.value, 10) : 5;

        // Collect break timer
        const breakSlider = document.getElementById('zs-break-time-slider');
        const breakTime = breakSlider ? parseInt(breakSlider.value, 10) : 10;

        const opacitySlider = document.getElementById('zs-break-opacity-slider');
        const breakOpacity = opacitySlider ? parseInt(opacitySlider.value, 10) : 100;

        // Recording
        const recFormatChecked = document.querySelector('input[name="zs_rec_format"]:checked');
        const recFormat = recFormatChecked ? parseInt(recFormatChecked.value, 10) : 1;

        // Checkboxes
        const animZoom = document.getElementById('zs-opt-animate-zoom')?.checked ? 1 : 0;
        const smoothImg = document.getElementById('zs-opt-smooth-image')?.checked ? 1 : 0;
        const snapGrid = document.getElementById('zs-opt-snap-grid')?.checked ? 1 : 0;
        const showDesktop = document.getElementById('zs-opt-break-show-desktop')?.checked ? 1 : 0;
        const lockStation = document.getElementById('zs-opt-break-lock')?.checked ? 1 : 0;
        const recSysAudio = document.getElementById('zs-opt-rec-sys-audio')?.checked ? 1 : 0;
        const recMic = document.getElementById('zs-opt-rec-mic')?.checked ? 1 : 0;
        const recNoise = document.getElementById('zs-opt-rec-noise')?.checked ? 1 : 0;
        const recAspect = document.getElementById('zs-opt-rec-aspect')?.checked ? 1 : 0;
        const camOverlay = document.getElementById('zs-opt-cam-overlay')?.checked ? 1 : 0;
        const dtUserMode = document.getElementById('zs-opt-dt-user-mode')?.checked ? 1 : 0;

        // Selects
        const camPos = parseInt(document.getElementById('zs-select-cam-pos')?.value || '3', 10);
        const camSize = parseInt(document.getElementById('zs-select-cam-size')?.value || '1', 10);
        const camShape = parseInt(document.getElementById('zs-select-cam-shape')?.value || '0', 10);
        const camBg = parseInt(document.getElementById('zs-select-cam-bg')?.value || '0', 10);
        const dtSpeed = parseInt(document.getElementById('zs-demotype-speed')?.value || '55', 10);
        const dtText = document.getElementById('zs-demotype-text')?.value ?? '';

        // Selected color swatch
        let penColor = 255;
        const selectedSwatch = document.querySelector('.zs-color-swatch.selected');
        if (selectedSwatch) {
          const colorCode = selectedSwatch.getAttribute('data-code');
          if (colorCode) penColor = parseInt(colorCode, 10);
        }

        const settings = {
          SliderZoomLevel: zoomLevel,
          PenWidth: penWidth,
          PenColor: penColor,
          BreakTimeout: breakTime,
          BreakOpacity: breakOpacity,
          RecordingFormat: recFormat,
          AnimnateZoom: animZoom,
          SmoothImage: smoothImg,
          SnapToGrid: snapGrid,
          BreakShowDesktop: showDesktop,
          BreakLockWorkstation: lockStation,
          CaptureSystemAudio: recSysAudio,
          CaptureAudio: recMic,
          NoiseCancellation: recNoise,
          RecordAspectRatio: recAspect,
          WebcamOverlay: camOverlay,
          WebcamPosition: camPos,
          WebcamSize: camSize,
          WebcamShape: camShape,
          WebcamBackgroundMode: camBg,
          DemoTypeSpeedSlider: dtSpeed,
          DemoTypeUserDrivenMode: dtUserMode,
          DemoTypeText: dtText,
        };

        const res = await window.pywebview.api.save_zoom_screen_settings(settings);
        if (res && res.message) {
          this.showToast(res.success ? "success" : "error", res.message);
        }
        await this.loadStatus();
      } catch (err) {
        console.error("Lỗi lưu cấu hình Zoom Screen:", err);
      }
    }

    async pasteDemoTypeText() {
      try {
        const text = await navigator.clipboard.readText();
        const el = document.getElementById('zs-demotype-text');
        if (el) {
          el.value = text;
          this.showToast('info', 'Đã dán nội dung từ Clipboard vào kịch bản DemoType!');
          this.saveSettings();
        }
      } catch (err) {
        this.showToast('warning', 'Không thể đọc Clipboard tự động. Bạn có thể nhấn Ctrl + V để dán trực tiếp vào ô.');
      }
    }

    loadSampleDemoText() {
      const el = document.getElementById('zs-demotype-text');
      if (el && el.value.trim().length > 0) {
        if (!confirm('Khung kịch bản đang có sẵn nội dung. Bạn có chắc chắn muốn thay thế bằng kịch bản mẫu không?')) {
          return;
        }
      }
      const sample = `# Kịch bản DemoType - Trình diễn tự động\n` +
        `def chao_mung():\n` +
        `    print("Xin chào! Chào mừng quý khách đến với IT Tool LTT.")\n` +
        `    print("DemoType tự động gõ mã lệnh chuẩn xác 100% không lo bấm nhầm phím.")\n\n` +
        `chao_mung()`;
      if (el) {
        el.value = sample;
        this.showToast('success', 'Đã nạp kịch bản mẫu cho DemoType!');
        this.saveSettings();
      }
    }

    clearDemoText() {
      const el = document.getElementById('zs-demotype-text');
      if (el) {
        el.value = '';
        this.showToast('info', 'Đã xóa trắng kịch bản DemoType.');
        this.saveSettings();
      }
    }
  }

  // Register on window
  window.zoomScreen = new ZoomScreenController();

  // Attach loader to AppController
  if (window.AppController) {
    AppController.prototype.loadZoomScreenStatus = function () {
      if (window.zoomScreen) {
        window.zoomScreen.init();
        window.zoomScreen.loadStatus();
      }
    };
  }

  document.addEventListener('DOMContentLoaded', () => {
    window.zoomScreen.init();
  });

  window.addEventListener('pywebviewready', () => {
    window.zoomScreen.init();
    window.zoomScreen.loadStatus();
  });

})();
