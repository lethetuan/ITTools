/**
 * ════════════════════════════════════════════════════════════════════════════
 *  IT Tool LTT 2026 - Test Computer Hardware Diagnostics Suite
 *  Author: Lê Thế Tuấn | 0352 194 195 | https://lethetuanpc.blogspot.com
 *  Features:
 *    1. Keyboard Diagnostics (100%, 80%, 60%, Win/Mac, Key history, APM/CPS)
 *    2. Mouse & Switch Double-Click Detector (Debounce threshold, Hold test, History)
 *    3. Screen Dead / Stuck Pixel Checker (5 pure colors + Brightness + Fullscreen)
 *    4. Webcam Device Scanner & Live Stream Preview
 *    5. Microphone Audio Level Analyzer, Gain Control & Recorder Playback
 *    6. Speaker Synthesizer (Bass 80Hz, Mid 1Khz, Treble 8Khz, Sweep, Stereo Pan)
 *    7. Battery State & Health (Web Battery API + PowerShell Health Reporter)
 *    8. Display FPS & Refresh Rate Benchmark (Vue 3 Engine: Framerate, Jank, Scroll, Ghosting)
 * ════════════════════════════════════════════════════════════════════════════
 */

(function () {
  'use strict';

  // ── Keyboard Layout Definitions ──────────────────────────────────────────
  const ROW_FUNCTION = [
    { code: 'Escape', label: 'Esc' },
    { code: 'GAP_1', label: '', w: '44' },
    { code: 'F1', label: 'F1' }, { code: 'F2', label: 'F2' },
    { code: 'F3', label: 'F3' }, { code: 'F4', label: 'F4' },
    { code: 'GAP_2', label: '', w: '20' },
    { code: 'F5', label: 'F5' }, { code: 'F6', label: 'F6' },
    { code: 'F7', label: 'F7' }, { code: 'F8', label: 'F8' },
    { code: 'GAP_3', label: '', w: '20' },
    { code: 'F9', label: 'F9' }, { code: 'F10', label: 'F10' },
    { code: 'F11', label: 'F11' }, { code: 'F12', label: 'F12' },
    { code: 'GAP_4', label: '', w: '24' },
    { code: 'PrintScreen', label: 'PrtSc', small: true },
    { code: 'ScrollLock', label: 'ScLk', small: true },
    { code: 'Pause', label: 'Pause', small: true },
  ];

  const ROW_1 = [
    { code: 'Backquote', label: '`', shift: '~' },
    { code: 'Digit1', label: '1', shift: '!' }, { code: 'Digit2', label: '2', shift: '@' },
    { code: 'Digit3', label: '3', shift: '#' }, { code: 'Digit4', label: '4', shift: '$' },
    { code: 'Digit5', label: '5', shift: '%' }, { code: 'Digit6', label: '6', shift: '^' },
    { code: 'Digit7', label: '7', shift: '&' }, { code: 'Digit8', label: '8', shift: '*' },
    { code: 'Digit9', label: '9', shift: '(' }, { code: 'Digit0', label: '0', shift: ')' },
    { code: 'Minus', label: '-', shift: '_' }, { code: 'Equal', label: '=', shift: '+' },
    { code: 'Backspace', label: 'Backspace', w: '100', small: true },
  ];

  const ROW_2 = [
    { code: 'Tab', label: 'Tab', w: '68', small: true },
    { code: 'KeyQ', label: 'Q' }, { code: 'KeyW', label: 'W' }, { code: 'KeyE', label: 'E' },
    { code: 'KeyR', label: 'R' }, { code: 'KeyT', label: 'T' }, { code: 'KeyY', label: 'Y' },
    { code: 'KeyU', label: 'U' }, { code: 'KeyI', label: 'I' }, { code: 'KeyO', label: 'O' },
    { code: 'KeyP', label: 'P' }, { code: 'BracketLeft', label: '[', shift: '{' },
    { code: 'BracketRight', label: ']', shift: '}' },
    { code: 'Backslash', label: '\\', shift: '|', w: '72' },
  ];

  const ROW_3 = [
    { code: 'CapsLock', label: 'Caps', w: '84', small: true },
    { code: 'KeyA', label: 'A' }, { code: 'KeyS', label: 'S' }, { code: 'KeyD', label: 'D' },
    { code: 'KeyF', label: 'F' }, { code: 'KeyG', label: 'G' }, { code: 'KeyH', label: 'H' },
    { code: 'KeyJ', label: 'J' }, { code: 'KeyK', label: 'K' }, { code: 'KeyL', label: 'L' },
    { code: 'Semicolon', label: ';', shift: ':' }, { code: 'Quote', label: "'", shift: '"' },
    { code: 'Enter', label: 'Enter', w: '105', small: true },
  ];

  const ROW_4 = [
    { code: 'ShiftLeft', label: 'Shift', w: '102', small: true },
    { code: 'KeyZ', label: 'Z' }, { code: 'KeyX', label: 'X' }, { code: 'KeyC', label: 'C' },
    { code: 'KeyV', label: 'V' }, { code: 'KeyB', label: 'B' }, { code: 'KeyN', label: 'N' },
    { code: 'KeyM', label: 'M' }, { code: 'Comma', label: ',', shift: '<' },
    { code: 'Period', label: '.', shift: '>' }, { code: 'Slash', label: '/', shift: '?' },
    { code: 'ShiftRight', label: 'Shift', w: '136', small: true },
  ];

  const ROW_5_WIN = [
    { code: 'ControlLeft', label: 'Ctrl', w: '64', small: true },
    { code: 'MetaLeft', label: 'Win', w: '64', small: true },
    { code: 'AltLeft', label: 'Alt', w: '64', small: true },
    { code: 'Space', label: '', w: 'flex1' },
    { code: 'AltRight', label: 'Alt', w: '64', small: true },
    { code: 'MetaRight', label: 'Win', w: '64', small: true },
    { code: 'ContextMenu', label: 'Menu', w: '64', small: true },
    { code: 'ControlRight', label: 'Ctrl', w: '64', small: true },
  ];

  const ROW_5_MAC = [
    { code: 'ControlLeft', label: 'Ctrl', w: '64', small: true },
    { code: 'MetaLeft', label: 'Cmd', w: '64', small: true },
    { code: 'AltLeft', label: 'Opt', w: '64', small: true },
    { code: 'Space', label: '', w: 'flex1' },
    { code: 'AltRight', label: 'Opt', w: '64', small: true },
    { code: 'MetaRight', label: 'Cmd', w: '64', small: true },
    { code: 'ContextMenu', label: 'Menu', w: '64', small: true },
    { code: 'ControlRight', label: 'Ctrl', w: '64', small: true },
  ];

  const ROW_NAV = [
    { code: 'Insert', label: 'Ins', small: true }, { code: 'Home', label: 'Home', small: true }, { code: 'PageUp', label: 'PgUp', small: true },
    { code: 'Delete', label: 'Del', small: true }, { code: 'End', label: 'End', small: true }, { code: 'PageDown', label: 'PgDn', small: true },
  ];

  const ARROWS = [
    { code: 'ArrowUp', label: '↑' },
    { code: 'ArrowLeft', label: '←' }, { code: 'ArrowDown', label: '↓' }, { code: 'ArrowRight', label: '→' },
  ];

  const NUMPAD = [
    { code: 'NumLock', label: 'Num', ga: '1/1' },
    { code: 'NumpadDivide', label: '/', ga: '1/2' },
    { code: 'NumpadMultiply', label: '*', ga: '1/3' },
    { code: 'NumpadSubtract', label: '-', ga: '1/4' },
    { code: 'Numpad7', label: '7', ga: '2/1' }, { code: 'Numpad8', label: '8', ga: '2/2' }, { code: 'Numpad9', label: '9', ga: '2/3' },
    { code: 'NumpadAdd', label: '+', ga: '2/4/4/5', spanV: true },
    { code: 'Numpad4', label: '4', ga: '3/1' }, { code: 'Numpad5', label: '5', ga: '3/2' }, { code: 'Numpad6', label: '6', ga: '3/3' },
    { code: 'Numpad1', label: '1', ga: '4/1' }, { code: 'Numpad2', label: '2', ga: '4/2' }, { code: 'Numpad3', label: '3', ga: '4/3' },
    { code: 'NumpadEnter', label: 'Ent', ga: '4/4/6/5', spanV: true },
    { code: 'Numpad0', label: '0', ga: '5/1/6/3', spanH: true }, { code: 'NumpadDecimal', label: '.', ga: '5/3' },
  ];

  // ── Test Computer Master Controller ──────────────────────────────────────
  class TestComputerController {
    constructor() {
      this.initialized = false;
      this.currentSubTab = 'keyboard';

      // Keyboard State
      this.keyStates = {};
      this.mouseStates = { Left: 'idle', Middle: 'idle', Right: 'idle' };
      this.pressCount = 0;
      this.activeKeys = [];
      this.lastKeyCode = '';
      this.mostPressed = { code: '', label: '', count: 0 };
      this.pressFrequency = {};
      this.keyHistory = [];
      this.historyId = 0;
      this.kbSoundEnabled = true;
      this.osType = 'Win';
      this.layoutSize = '100';
      this.kbAudioCtx = null;
      this.pressesInCurrentSecond = 0;
      this.currentCps = 0;
      this.lastPressTime = 0;
      this.lastInterval = 0;
      this.performanceInterval = null;

      // Mouse Double-Click State
      this.mouseInitialized = false;
      this.mouseThreshold = 80;
      this.mouseSoundEnabled = true;
      this.lastDownTime = { 0: 0, 1: 0, 2: 0 };
      this.clickCounts = { 0: 0, 1: 0, 2: 0 };
      this.doubleClickCounts = { 0: 0, 1: 0, 2: 0 };
      this.scrollCount = 0;
      this.fastestInterval = Infinity;
      this.lastIntervalRecord = 0;
      this.mouseHistory = [];
      this.holdTimer = null;
      this.isHolding = false;
      this.holdButton = null;
      this.holdStartTime = 0;
      this.btnNames = { 0: 'Chuột trái (Left)', 1: 'Chuột giữa (Middle)', 2: 'Chuột phải (Right)' };

      // Screen Test State
      this.screenColors = [
        { name: 'Đen', value: '#000000' },
        { name: 'Trắng', value: '#ffffff' },
        { name: 'Đỏ', value: '#ff0000' },
        { name: 'Xanh lá', value: '#00ff00' },
        { name: 'Xanh dương', value: '#0000ff' },
      ];
      this.screenIdx = 0;
      this.screenBrightness = 100;
      this.screenActive = false;

      // Webcam State
      this.camInitialized = false;
      this.camStream = null;
      this.camList = [];
      this.camRequestId = 0;
      this.camMounted = true;

      // Mic State
      this.micInitialized = false;
      this.micStream = null;
      this.micList = [];
      this.micRequestId = 0;
      this.micMounted = true;
      this.micAudioCtx = null;
      this.micGainNode = null;
      this.micAnalyser = null;
      this.micAnimId = null;
      this.micRecorder = null;
      this.micChunks = [];
      this.micRecording = false;

      // Speaker State
      this.tracks = [
        { key: 'bass', label: 'Âm trầm (Bass)', description: '80 Hz — thử loa sub hoặc âm trầm', emoji: '🔉' },
        { key: 'mid', label: 'Âm trung (Mid)', description: '1000 Hz — thử dải trung, giọng nói', emoji: '🔊' },
        { key: 'high', label: 'Âm cao (Treble)', description: '8000 Hz — thử độ chi tiết âm thanh', emoji: '🎵' },
        { key: 'sweep', label: 'Quét tần số (Sweep)', description: '80→8000 Hz — quét toàn dải để nghe tổng thể', emoji: '📡' },
        { key: 'left', label: 'Kênh trái (Left)', description: '1000 Hz chỉ phát qua loa trái', emoji: '◀️' },
        { key: 'right', label: 'Kênh phải (Right)', description: '1000 Hz chỉ phát qua loa phải', emoji: '▶️' },
      ];
      this.playingKey = null;
      this.spkAudioCtx = null;
      this.spkOsc = null;
      this.spkGain = null;
      this.spkPan = null;
      this.spkSweep = null;
      this.tracksBuilt = false;

      // Battery State
      this.battInitialized = false;
      this.battMgr = null;

      // FPS State
      this.fpsInitialized = false;
      this.fpsVueApp = null;
    }

    init() {
      if (this.initialized) return;
      this.initialized = true;

      this.bindNavigation();
      this.initKeyboard();
      this.initMouse();
      this.initScreen();
      this.initWebcamUI();
      this.initMicUI();
      this.initSpeakerUI();
      this.initBatteryUIEvents();
      this.initFullscreenToggle();

      // Window resize handler
      window.addEventListener('resize', () => {
        if (this.isTabVisible() && this.currentSubTab === 'keyboard') {
          this.fitKeyboard();
        }
      });
    }

    isTabVisible() {
      const sec = document.getElementById('tab-test-computer');
      return sec && sec.classList.contains('active');
    }

    onTabActivated() {
      this.init();
      if (this.currentSubTab === 'keyboard') {
        requestAnimationFrame(() => this.fitKeyboard());
      } else if (this.currentSubTab === 'fps' && !this.fpsInitialized) {
        this.initFpsApp();
      }
    }

    onTabDeactivated() {
      this.stopCam();
      this.stopMic();
      this.stopSpk();
      if (this.screenActive) this.exitScreen();
    }

    // ── Navigation & Subtab Switching ──────────────────────────────────────
    bindNavigation() {
      const nav = document.getElementById('tc-tab-nav');
      if (nav) {
        nav.addEventListener('click', (e) => {
          const btn = e.target.closest('button');
          if (btn && btn.dataset.tab) {
            this.switchSubTab(btn.dataset.tab);
          }
        });
      }

      const btnGotoMouse = document.getElementById('tc-btn-goto-mouse-tab');
      if (btnGotoMouse) {
        btnGotoMouse.addEventListener('click', () => this.switchSubTab('mouse'));
      }
    }

    switchSubTab(tabName) {
      if (this.currentSubTab === 'webcam' && tabName !== 'webcam') this.stopCam();
      if (this.currentSubTab === 'micro' && tabName !== 'micro') this.stopMic();
      if (this.currentSubTab === 'speaker' && tabName !== 'speaker') this.stopSpk();

      this.currentSubTab = tabName;

      // Panels
      document.querySelectorAll('.tc-tab-panel').forEach(p => p.classList.remove('active'));
      const targetPanel = document.getElementById('tc-panel-' + tabName);
      if (targetPanel) targetPanel.classList.add('active');

      // Buttons
      document.querySelectorAll('#tc-tab-nav button').forEach(b => {
        b.classList.toggle('active', b.dataset.tab === tabName);
      });

      // Footers
      document.querySelectorAll('.tc-tab-footer').forEach(f => f.style.display = 'none');
      const targetFooter = document.getElementById('tc-footer-' + tabName);
      if (targetFooter) targetFooter.style.display = 'grid';

      // Lazy load subtab modules
      if (tabName === 'keyboard') requestAnimationFrame(() => this.fitKeyboard());
      if (tabName === 'mouse' && !this.mouseInitialized) { this.mouseInitialized = true; this.bindMouseEvents(); }
      if (tabName === 'webcam' && !this.camInitialized) { this.camInitialized = true; this.initCam(); }
      if (tabName === 'micro' && !this.micInitialized) { this.micInitialized = true; this.initMic(); }
      if (tabName === 'battery' && !this.battInitialized) { this.battInitialized = true; this.initBattery(); }
      if (tabName === 'speaker') this.buildTracks();
      if (tabName === 'fps' && !this.fpsInitialized) { this.fpsInitialized = true; this.initFpsApp(); }
    }

    // ── Fullscreen Functional Area ─────────────────────────────────────────
    initFullscreenToggle() {
      const fsBtn = document.getElementById('tc-fs-func-btn');
      const funcArea = document.getElementById('tab-test-computer');
      if (!fsBtn || !funcArea) return;

      const fsText = fsBtn.querySelector('.fs-text');
      const fsIcon = fsBtn.querySelector('.fs-icon');

      fsBtn.addEventListener('click', () => {
        if (!document.fullscreenElement && !document.webkitFullscreenElement) {
          if (funcArea.requestFullscreen) {
            funcArea.requestFullscreen();
          } else if (funcArea.webkitRequestFullscreen) {
            funcArea.webkitRequestFullscreen();
          }
        } else {
          if (document.exitFullscreen) {
            document.exitFullscreen();
          } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
          }
        }
      });

      const updateFsBtn = () => {
        const isFs = document.fullscreenElement === funcArea || document.webkitFullscreenElement === funcArea;
        if (fsText) fsText.textContent = isFs ? 'Thu nhỏ' : 'Phóng to khu vực Test';
        if (fsIcon) fsIcon.textContent = isFs ? '🗕' : '⛶';
        fsBtn.classList.toggle('tc-btn-coral', isFs);
        fsBtn.classList.toggle('tc-btn-outline-coral', !isFs);
        setTimeout(() => this.fitKeyboard(), 100);
      };

      document.addEventListener('fullscreenchange', updateFsBtn);
      document.addEventListener('webkitfullscreenchange', updateFsBtn);
    }

    // ── 1. KEYBOARD DIAGNOSTICS ────────────────────────────────────────────
    initKeyboard() {
      this.buildKeyboard();

      // Toolbars
      const layoutBtns = document.getElementById('tc-layout-btns');
      if (layoutBtns) {
        layoutBtns.addEventListener('click', (e) => {
          const btn = e.target.closest('button');
          if (!btn) return;
          this.layoutSize = btn.dataset.layout;
          layoutBtns.querySelectorAll('button').forEach(b => b.classList.toggle('active', b === btn));
          this.buildKeyboard();
        });
      }

      const osBtns = document.getElementById('tc-os-btns');
      if (osBtns) {
        osBtns.addEventListener('click', (e) => {
          const btn = e.target.closest('button');
          if (!btn) return;
          this.osType = btn.dataset.os;
          osBtns.querySelectorAll('button').forEach(b => b.classList.toggle('active', b === btn));
          this.buildKeyboard();
        });
      }

      const soundBtn = document.getElementById('tc-sound-btn');
      if (soundBtn) {
        soundBtn.addEventListener('click', () => {
          this.kbSoundEnabled = !this.kbSoundEnabled;
          soundBtn.textContent = this.kbSoundEnabled ? 'BẬT' : 'TẮT';
          soundBtn.className = this.kbSoundEnabled ? 'tc-btn tc-btn-green' : 'tc-btn tc-btn-outline';
        });
      }

      const resetBtn = document.getElementById('tc-reset-btn');
      if (resetBtn) {
        resetBtn.addEventListener('click', () => this.resetKeyboard());
      }

      // Keyboard listeners (carefully scoped so typing in inputs is NOT intercepted)
      window.addEventListener('keydown', (e) => this.handleKeyDown(e));
      window.addEventListener('keyup', (e) => this.handleKeyUp(e));

      // Global window mouse for keyboard mouse-indicator row
      window.addEventListener('mousedown', (e) => {
        if (!this.isTabVisible() || this.currentSubTab !== 'keyboard') return;
        if (e.target.closest('button, nav, a, input, select, .tc-kb-toolbar, .top-header, .sidebar')) return;
        const btn = e.button === 0 ? 'Left' : e.button === 1 ? 'Middle' : 'Right';
        this.mouseStates[btn] = 'active';
        const el = document.getElementById('tc-mouse-' + btn.toLowerCase());
        if (el) { el.classList.remove('key-active', 'key-pressed'); el.classList.add('key-active'); }
      });

      window.addEventListener('mouseup', (e) => {
        if (!this.isTabVisible() || this.currentSubTab !== 'keyboard') return;
        if (e.target.closest('button, nav, a, input, select, .tc-kb-toolbar, .top-header, .sidebar')) return;
        const btn = e.button === 0 ? 'Left' : e.button === 1 ? 'Middle' : 'Right';
        this.mouseStates[btn] = 'pressed';
        const el = document.getElementById('tc-mouse-' + btn.toLowerCase());
        if (el) { el.classList.remove('key-active', 'key-pressed'); el.classList.add('key-pressed'); }
      });

      window.addEventListener('blur', () => {
        this.activeKeys.forEach(code => { this.keyStates[code] = 'pressed'; });
        this.activeKeys = [];
        this.updateAllKeyStyles();
        this.updateStats();
      });

      // CPS timer
      this.performanceInterval = setInterval(() => {
        this.currentCps = this.pressesInCurrentSecond;
        this.pressesInCurrentSecond = 0;
        this.updateStats();
      }, 1000);

      // Auto resize observer on kb-container
      if (window.ResizeObserver) {
        const kbCont = document.getElementById('tc-kb-container');
        if (kbCont) {
          const ro = new ResizeObserver(() => this.fitKeyboard());
          ro.observe(kbCont);
        }
      }
    }

    makeKeyEl(code, label, shift, small, w, spanH, spanV, ga) {
      if (code.startsWith('GAP')) {
        const g = document.createElement('div');
        g.className = 'tc-key tc-key-gap';
        g.style.width = w + 'px';
        return g;
      }
      const el = document.createElement('div');
      el.className = 'tc-key' + (small ? ' key-small' : '');
      el.dataset.code = code;

      if (w === 'flex1') {
        el.style.flex = '1';
      } else if (w) {
        el.style.width = w + 'px';
      } else {
        el.style.width = '3rem';
      }

      if (spanV) {
        el.classList.add('key-span-v');
        el.style.height = '100%';
        el.style.minHeight = '6.125rem';
      } else {
        el.style.height = '3rem';
      }

      if (spanH) {
        el.classList.add('key-span-h');
        el.style.gridColumn = 'span 2';
        el.style.width = '100%';
        el.style.minWidth = '6.125rem';
      }

      if (ga) {
        const parts = ga.split('/');
        if (parts.length === 4) {
          el.style.gridArea = `${parts[0]} / ${parts[1]} / ${parts[2]} / ${parts[3]}`;
        } else {
          el.style.gridRowStart = parts[0];
          el.style.gridColumnStart = parts[1];
        }
      }

      if (shift) {
        const s = document.createElement('span');
        s.className = 'shift-label';
        s.textContent = shift;
        const m = document.createElement('span');
        m.className = 'main-label';
        m.textContent = label;
        el.appendChild(s);
        el.appendChild(m);
      } else {
        const span = document.createElement('span');
        span.textContent = label;
        el.appendChild(span);
      }
      return el;
    }

    buildRow(keys) {
      const row = document.createElement('div');
      row.className = 'tc-kb-row';
      keys.forEach(k => {
        row.appendChild(this.makeKeyEl(k.code, k.label, k.shift, k.small, k.w, k.spanH, k.spanV, k.ga));
      });
      return row;
    }

    buildKeyboard() {
      const layout = document.getElementById('tc-keyboard-layout');
      if (!layout) return;
      layout.innerHTML = '';

      const rows = document.createElement('div');
      rows.className = 'tc-kb-rows';

      // Function Row
      const fnRow = this.buildRow(ROW_FUNCTION);
      fnRow.style.marginBottom = '8px';
      fnRow.dataset.section = 'fn';
      rows.appendChild(fnRow);

      const sections = document.createElement('div');
      sections.className = 'tc-kb-sections';

      // Main Section
      const main = document.createElement('div');
      main.className = 'tc-kb-main-section';

      const row1El = document.createElement('div');
      row1El.className = 'tc-kb-row';
      ROW_1.forEach((k, i) => {
        let code = k.code, label = k.label;
        if (i === 0 && this.layoutSize === '60') { code = 'Escape'; label = 'Esc'; }
        row1El.appendChild(this.makeKeyEl(code, label, i === 0 && this.layoutSize === '60' ? undefined : k.shift, k.small, k.w));
      });
      main.appendChild(row1El);
      main.appendChild(this.buildRow(ROW_2));
      main.appendChild(this.buildRow(ROW_3));
      main.appendChild(this.buildRow(ROW_4));

      const row5 = this.osType === 'Mac' ? ROW_5_MAC : ROW_5_WIN;
      main.appendChild(this.buildRow(row5));
      sections.appendChild(main);

      // Nav Section
      const navSection = document.createElement('div');
      navSection.className = 'tc-kb-nav-section';
      navSection.dataset.section = 'nav';

      const navGrid = document.createElement('div');
      navGrid.className = 'tc-kb-nav-grid';
      ROW_NAV.forEach(k => navGrid.appendChild(this.makeKeyEl(k.code, k.label, null, k.small)));
      navSection.appendChild(navGrid);

      const arrowsWrap = document.createElement('div');
      arrowsWrap.className = 'tc-kb-arrows';
      arrowsWrap.appendChild(this.makeKeyEl(ARROWS[0].code, ARROWS[0].label));
      const arrowRow = document.createElement('div');
      arrowRow.className = 'tc-kb-arrows-row';
      ARROWS.slice(1).forEach(k => arrowRow.appendChild(this.makeKeyEl(k.code, k.label)));
      arrowsWrap.appendChild(arrowRow);
      navSection.appendChild(arrowsWrap);
      sections.appendChild(navSection);

      // Numpad
      const numpad = document.createElement('div');
      numpad.className = 'tc-kb-numpad';
      numpad.dataset.section = 'numpad';
      NUMPAD.forEach(k => {
        numpad.appendChild(this.makeKeyEl(k.code, k.label, null, false, null, k.spanH, k.spanV, k.ga));
      });
      sections.appendChild(numpad);

      rows.appendChild(sections);
      layout.appendChild(rows);

      // Visibility toggles
      if (fnRow) fnRow.style.display = this.layoutSize === '60' ? 'none' : 'flex';
      if (navSection) navSection.style.display = this.layoutSize === '60' ? 'none' : 'flex';
      if (numpad) numpad.style.display = this.layoutSize === '100' ? 'grid' : 'none';

      this.updateAllKeyStyles();
      this.fitKeyboard();
    }

    fitKeyboard() {
      const container = document.getElementById('tc-kb-container');
      const inner = document.getElementById('tc-kb-inner');
      const wrapper = document.getElementById('tc-kb-scale-wrapper');
      if (!container || !inner || !wrapper) return;

      wrapper.style.transform = 'none';
      wrapper.style.width = 'fit-content';
      wrapper.style.height = 'auto';

      const style = window.getComputedStyle(container);
      const padLeft = parseFloat(style.paddingLeft) || 16;
      const padRight = parseFloat(style.paddingRight) || 16;
      const availWidth = Math.max(0, container.clientWidth - padLeft - padRight);

      const naturalWidth = inner.offsetWidth;
      const naturalHeight = inner.offsetHeight;

      if (naturalWidth > 0 && availWidth > 0) {
        if (availWidth < naturalWidth) {
          const scale = Math.max(0.38, Math.min(1, (availWidth - 4) / naturalWidth));
          wrapper.style.transform = `scale(${scale})`;
          wrapper.style.transformOrigin = 'top center';
          wrapper.style.width = `${naturalWidth}px`;
          wrapper.style.height = `${Math.ceil(naturalHeight * scale)}px`;
        } else {
          wrapper.style.transform = 'none';
          wrapper.style.width = 'auto';
          wrapper.style.height = 'auto';
        }
      }
    }

    playClickSound() {
      if (!this.kbSoundEnabled) return;
      try {
        if (!this.kbAudioCtx) {
          const ACtx = window.AudioContext || window.webkitAudioContext;
          this.kbAudioCtx = new ACtx();
        }
        if (this.kbAudioCtx.state === 'suspended') this.kbAudioCtx.resume();
        const osc = this.kbAudioCtx.createOscillator();
        const gain = this.kbAudioCtx.createGain();
        const filter = this.kbAudioCtx.createBiquadFilter();
        osc.type = 'square';
        osc.frequency.setValueAtTime(150, this.kbAudioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(40, this.kbAudioCtx.currentTime + 0.03);
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(1000, this.kbAudioCtx.currentTime);
        gain.gain.setValueAtTime(0.5, this.kbAudioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, this.kbAudioCtx.currentTime + 0.03);
        osc.connect(filter);
        filter.connect(gain);
        gain.connect(this.kbAudioCtx.destination);
        osc.start();
        osc.stop(this.kbAudioCtx.currentTime + 0.03);
      } catch (e) { }
    }

    handleKeyDown(e) {
      if (!this.isTabVisible() || this.currentSubTab !== 'keyboard') return;

      // Do NOT intercept if user is typing in form inputs, textareas, or selects
      const act = document.activeElement;
      if (act && (act.tagName === 'INPUT' || act.tagName === 'TEXTAREA' || act.tagName === 'SELECT')) {
        return;
      }

      if (this.screenActive) return;

      e.preventDefault();
      e.stopPropagation();
      const code = e.code;
      this.lastKeyCode = code;

      if (this.keyStates[code] !== 'active') {
        this.playClickSound();
        this.keyStates[code] = 'active';
        if (!this.activeKeys.includes(code)) this.activeKeys.push(code);

        const label = e.key === ' ' ? 'Space' : e.key;
        this.keyHistory.unshift({ code, label, id: this.historyId++ });
        if (this.keyHistory.length > 25) this.keyHistory.pop();

        this.pressesInCurrentSecond++;
        this.pressCount++;
        this.pressFrequency[code] = (this.pressFrequency[code] || 0) + 1;

        if (this.pressFrequency[code] > this.mostPressed.count) {
          this.mostPressed = { code, label, count: this.pressFrequency[code] };
        }

        const now = performance.now();
        if (this.lastPressTime > 0) this.lastInterval = +(now - this.lastPressTime).toFixed(1);
        this.lastPressTime = now;

        this.updateKeyStyle(code);
        this.updateHistory();
        this.updateStats();
      }
    }

    handleKeyUp(e) {
      if (!this.isTabVisible() || this.currentSubTab !== 'keyboard') return;
      const act = document.activeElement;
      if (act && (act.tagName === 'INPUT' || act.tagName === 'TEXTAREA' || act.tagName === 'SELECT')) return;
      if (this.screenActive) return;

      const code = e.code;
      this.keyStates[code] = 'pressed';
      this.activeKeys = this.activeKeys.filter(k => k !== code);
      this.updateKeyStyle(code);
      this.updateStats();
    }

    updateKeyStyle(code) {
      document.querySelectorAll(`#tc-keyboard-layout .tc-key[data-code="${code}"]`).forEach(el => {
        el.classList.remove('key-active', 'key-pressed');
        const state = this.keyStates[code] || 'idle';
        if (state === 'active') el.classList.add('key-active');
        else if (state === 'pressed') el.classList.add('key-pressed');
      });
    }

    updateAllKeyStyles() {
      document.querySelectorAll('#tc-keyboard-layout .tc-key[data-code]').forEach(el => {
        const code = el.dataset.code;
        const state = this.keyStates[code] || 'idle';
        el.classList.remove('key-active', 'key-pressed');
        if (state === 'active') el.classList.add('key-active');
        else if (state === 'pressed') el.classList.add('key-pressed');
      });

      ['Left', 'Middle', 'Right'].forEach(btn => {
        const el = document.getElementById('tc-mouse-' + btn.toLowerCase());
        if (!el) return;
        el.classList.remove('key-active', 'key-pressed');
        const s = this.mouseStates[btn];
        if (s === 'active') el.classList.add('key-active');
        else if (s === 'pressed') el.classList.add('key-pressed');
      });
    }

    updateHistory() {
      const placeholder = document.getElementById('tc-history-placeholder');
      const items = document.getElementById('tc-history-items');
      const count = document.getElementById('tc-history-count');
      if (count) count.textContent = this.pressCount + ' phím';

      if (!placeholder || !items) return;
      if (this.keyHistory.length === 0) {
        placeholder.style.display = '';
        items.style.display = 'none';
        return;
      }
      placeholder.style.display = 'none';
      items.style.display = 'flex';
      items.innerHTML = '';
      this.keyHistory.forEach(k => {
        const chip = document.createElement('div');
        chip.className = 'tc-history-chip';
        chip.textContent = k.label;
        items.appendChild(chip);
      });
    }

    updateStats() {
      const act = document.getElementById('tc-stat-active');
      if (act) act.textContent = this.activeKeys.length;
      const tot = document.getElementById('tc-stat-total');
      if (tot) tot.textContent = this.pressCount;
      const most = document.getElementById('tc-stat-most');
      if (most) {
        most.textContent = this.mostPressed.code ? `${this.mostPressed.label || this.mostPressed.code} (${this.mostPressed.count})` : '-';
      }
      const last = document.getElementById('tc-stat-last');
      if (last) last.textContent = this.lastKeyCode || '-';
      const scan = document.getElementById('tc-stat-scan');
      if (scan) {
        const hz = this.lastInterval ? Math.round(1000 / this.lastInterval) : 0;
        scan.textContent = hz + ' Hz';
      }
      const interval = document.getElementById('tc-stat-interval');
      if (interval) interval.textContent = this.lastInterval + ' ms';
      const cps = document.getElementById('tc-stat-cps');
      if (cps) cps.textContent = this.currentCps;
      const apm = document.getElementById('tc-stat-apm');
      if (apm) apm.textContent = this.currentCps * 60;
    }

    resetKeyboard() {
      Object.keys(this.keyStates).forEach(k => { this.keyStates[k] = 'idle'; });
      this.mouseStates.Left = this.mouseStates.Middle = this.mouseStates.Right = 'idle';
      this.pressCount = 0;
      this.activeKeys = [];
      this.lastKeyCode = '';
      this.mostPressed = { code: '', label: '', count: 0 };
      Object.keys(this.pressFrequency).forEach(k => { delete this.pressFrequency[k]; });
      this.keyHistory.length = 0;
      this.historyId = 0;
      this.pressesInCurrentSecond = 0;
      this.currentCps = 0;
      this.lastInterval = 0;
      this.lastPressTime = 0;
      this.updateAllKeyStyles();
      this.updateHistory();
      this.updateStats();
    }

    // ── 2. MOUSE & DOUBLE-CLICK TESTER ─────────────────────────────────────
    initMouse() {
      // Setup thresholds & buttons
      const threshBtns = document.getElementById('tc-mouse-threshold-btns');
      if (threshBtns) {
        threshBtns.addEventListener('click', (e) => {
          const btn = e.target.closest('button');
          if (!btn) return;
          this.mouseThreshold = parseInt(btn.dataset.threshold, 10) || 80;
          threshBtns.querySelectorAll('button').forEach(b => b.classList.toggle('active', b === btn));
          const liveStatus = document.getElementById('tc-mouse-pad-live-status');
          if (liveStatus) liveStatus.innerHTML = `<span style="color:var(--accent-amber)">Đã đổi ngưỡng phát hiện sang: ${this.mouseThreshold} ms</span>`;
        });
      }

      const soundBtn = document.getElementById('tc-mouse-sound-btn');
      if (soundBtn) {
        soundBtn.addEventListener('click', () => {
          this.mouseSoundEnabled = !this.mouseSoundEnabled;
          soundBtn.textContent = this.mouseSoundEnabled ? 'BẬT' : 'TẮT';
          soundBtn.className = this.mouseSoundEnabled ? 'tc-btn tc-btn-green' : 'tc-btn tc-btn-outline';
        });
      }

      const resetBtn = document.getElementById('tc-mouse-reset-btn');
      if (resetBtn) {
        resetBtn.addEventListener('click', () => this.resetMouseTest());
      }
    }

    bindMouseEvents() {
      const pad = document.getElementById('tc-mouse-click-pad');
      if (pad) {
        pad.addEventListener('mousedown', (e) => this.processMouseClick(e, null));
        pad.addEventListener('mouseup', (e) => this.handleMousePadUp(e));
        pad.addEventListener('wheel', (e) => this.handleMousePadWheel(e), { passive: false });
        pad.addEventListener('contextmenu', e => e.preventDefault());
        pad.addEventListener('auxclick', e => e.preventDefault());
      }

      const cardConfigs = [
        { id: 'tc-mcb-left', expected: 0 },
        { id: 'tc-mcb-middle', expected: 1 },
        { id: 'tc-mcb-right', expected: 2 }
      ];
      cardConfigs.forEach(cfg => {
        const el = document.getElementById(cfg.id);
        if (el) {
          el.addEventListener('mousedown', (e) => this.processMouseClick(e, cfg.expected));
          el.addEventListener('mouseup', (e) => this.handleMousePadUp(e));
          el.addEventListener('wheel', (e) => this.handleMousePadWheel(e), { passive: false });
          el.addEventListener('contextmenu', e => e.preventDefault());
          el.addEventListener('auxclick', e => e.preventDefault());
        }
      });
    }

    playMouseSound(isDouble) {
      if (!this.mouseSoundEnabled) return;
      try {
        if (!this.kbAudioCtx) {
          const ACtx = window.AudioContext || window.webkitAudioContext;
          this.kbAudioCtx = new ACtx();
        }
        if (this.kbAudioCtx.state === 'suspended') this.kbAudioCtx.resume();
        const osc = this.kbAudioCtx.createOscillator();
        const gain = this.kbAudioCtx.createGain();

        if (isDouble) {
          osc.type = 'sawtooth';
          osc.frequency.setValueAtTime(920, this.kbAudioCtx.currentTime);
          osc.frequency.setValueAtTime(460, this.kbAudioCtx.currentTime + 0.07);
          gain.gain.setValueAtTime(0.35, this.kbAudioCtx.currentTime);
          gain.gain.exponentialRampToValueAtTime(0.01, this.kbAudioCtx.currentTime + 0.18);
          osc.connect(gain);
          gain.connect(this.kbAudioCtx.destination);
          osc.start();
          osc.stop(this.kbAudioCtx.currentTime + 0.18);
        } else {
          osc.type = 'triangle';
          osc.frequency.setValueAtTime(320, this.kbAudioCtx.currentTime);
          osc.frequency.exponentialRampToValueAtTime(80, this.kbAudioCtx.currentTime + 0.025);
          gain.gain.setValueAtTime(0.25, this.kbAudioCtx.currentTime);
          gain.gain.exponentialRampToValueAtTime(0.01, this.kbAudioCtx.currentTime + 0.025);
          osc.connect(gain);
          gain.connect(this.kbAudioCtx.destination);
          osc.start();
          osc.stop(this.kbAudioCtx.currentTime + 0.025);
        }
      } catch (e) { }
    }

    processMouseClick(e, expectedBtn) {
      e.preventDefault();
      e.stopPropagation();

      const btn = e.button; // 0: Left, 1: Middle, 2: Right
      if (btn !== 0 && btn !== 1 && btn !== 2) return;

      const now = performance.now();

      // Guard against synthetic duplicate events < 10ms
      if (this.lastDownTime[btn] > 0 && (now - this.lastDownTime[btn]) < 10) return;

      const liveStatus = document.getElementById('tc-mouse-pad-live-status');

      // Mismatched button on card click
      if (expectedBtn !== null && expectedBtn !== btn) {
        const cardEl = document.getElementById(expectedBtn === 0 ? 'tc-mcb-left' : expectedBtn === 1 ? 'tc-mcb-middle' : 'tc-mcb-right');
        if (cardEl) {
          cardEl.classList.add('card-warning-nudge');
          setTimeout(() => cardEl.classList.remove('card-warning-nudge'), 450);
        }
        if (liveStatus) {
          if (expectedBtn === 1) {
            liveStatus.innerHTML = `<span style="color:var(--accent-amber); font-weight:600;">💡 Bạn đang click ${this.btnNames[btn]} vào ô Chuột giữa. Hãy <u>NHẤN BÁNH XE CON LĂN XUỐNG</u> (Middle Click) hoặc cuộn bánh xe để kiểm tra ô này.</span>`;
          } else {
            liveStatus.innerHTML = `<span style="color:var(--accent-amber); font-weight:600;">💡 Bạn đang click ${this.btnNames[btn]} vào ô ${this.btnNames[expectedBtn]}. Vui lòng click đúng phím tương ứng.</span>`;
          }
        }
        return;
      }

      this.clickCounts[btn]++;
      let interval = 0;
      let isDouble = false;

      if (this.lastDownTime[btn] > 0) {
        interval = +(now - this.lastDownTime[btn]).toFixed(1);
        this.lastIntervalRecord = interval;
        if (interval < this.fastestInterval && interval >= 10) this.fastestInterval = interval;

        if (interval >= 10 && interval <= this.mouseThreshold) {
          isDouble = true;
          this.doubleClickCounts[btn]++;
        }
      }
      this.lastDownTime[btn] = now;

      this.playMouseSound(isDouble);

      // Visual updates
      const pad = document.getElementById('tc-mouse-click-pad');
      const cardBtn = document.getElementById(btn === 0 ? 'tc-mcb-left' : btn === 1 ? 'tc-mcb-middle' : 'tc-mcb-right');

      if (pad) {
        pad.classList.remove('active-btn-0', 'active-btn-1', 'active-btn-2', 'has-error');
        pad.classList.add('active-btn-' + btn);
        if (isDouble) {
          pad.classList.add('has-error');
          setTimeout(() => pad.classList.remove('has-error'), 400);
        }
      }

      if (cardBtn) {
        cardBtn.classList.add('active');
        if (isDouble) {
          cardBtn.classList.add('has-error');
          setTimeout(() => cardBtn.classList.remove('has-error'), 600);
        }
        setTimeout(() => cardBtn.classList.remove('active'), 120);
      }

      if (liveStatus) {
        if (isDouble) {
          liveStatus.innerHTML = `<span style="color:var(--red-500)">⚠️ PHÁT HIỆN LỖI DOUBLE CLICK! ${this.btnNames[btn]}: ${interval} ms (&le; ${this.mouseThreshold} ms)</span>`;
        } else if (interval > 0) {
          const intervalText = interval > 2000 ? '> 2000 ms' : interval + ' ms';
          liveStatus.innerHTML = `<span style="color:var(--green-500)">✓ Click hợp lệ: ${intervalText} (${this.btnNames[btn]})</span>`;
        } else {
          liveStatus.innerHTML = `<span style="color:var(--text-secondary)">Click đầu tiên (${this.btnNames[btn]})</span>`;
        }
      }

      // Hold test
      this.isHolding = true;
      this.holdButton = btn;
      this.holdStartTime = now;
      clearInterval(this.holdTimer);
      this.holdTimer = setInterval(() => {
        if (this.isHolding && liveStatus) {
          const holdDuration = ((performance.now() - this.holdStartTime) / 1000).toFixed(1);
          liveStatus.innerHTML = `<span style="color:var(--accent-sky)">Đang giữ ${this.btnNames[btn]}... (${holdDuration}s) - Tiếp tục giữ để thử nghiệm tuột click</span>`;
        }
      }, 100);

      // History
      const nowObj = new Date();
      const timeStr = `${String(nowObj.getHours()).padStart(2, '0')}:${String(nowObj.getMinutes()).padStart(2, '0')}:${String(nowObj.getSeconds()).padStart(2, '0')}.${String(Math.floor(nowObj.getMilliseconds() / 10)).padStart(2, '0')}`;
      const intervalDisplay = interval > 0 ? (interval > 2000 ? '> 2000 ms' : interval + ' ms') : 'Click đầu';
      this.mouseHistory.unshift({
        btnName: this.btnNames[btn],
        interval: intervalDisplay,
        isDouble,
        time: timeStr
      });
      if (this.mouseHistory.length > 30) this.mouseHistory.pop();

      this.updateMouseUI(isDouble, btn, interval);
    }

    handleMousePadUp(e) {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }
      this.isHolding = false;
      clearInterval(this.holdTimer);
      const pad = document.getElementById('tc-mouse-click-pad');
      if (pad) {
        pad.classList.remove('active-btn-0', 'active-btn-1', 'active-btn-2');
      }
      ['tc-mcb-left', 'tc-mcb-middle', 'tc-mcb-right'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.remove('active');
      });
    }

    handleMousePadWheel(e) {
      e.preventDefault();
      this.scrollCount++;
      const wheelText = document.getElementById('tc-m-stat-wheel-text');
      if (wheelText) {
        const dir = e.deltaY < 0 ? 'Lên ↑' : 'Xuống ↓';
        wheelText.textContent = `Cuộn: ${this.scrollCount} (${dir})`;
      }
      const mcb = document.getElementById('tc-mcb-middle');
      if (mcb) {
        mcb.classList.add('active');
        setTimeout(() => mcb.classList.remove('active'), 120);
      }
    }

    updateMouseUI(lastWasDouble, btn, interval) {
      const lEl = document.getElementById('tc-m-stat-l-clicks');
      if (lEl) lEl.textContent = this.clickCounts[0];
      const mEl = document.getElementById('tc-m-stat-m-clicks');
      if (mEl) mEl.textContent = this.clickCounts[1];
      const rEl = document.getElementById('tc-m-stat-r-clicks');
      if (rEl) rEl.textContent = this.clickCounts[2];

      const totalClicks = this.clickCounts[0] + this.clickCounts[1] + this.clickCounts[2];
      const totalErrors = this.doubleClickCounts[0] + this.doubleClickCounts[1] + this.doubleClickCounts[2];

      const totEl = document.getElementById('tc-m-stat-total-clicks');
      if (totEl) totEl.textContent = totalClicks;
      const totalErrEl = document.getElementById('tc-m-stat-total-errors');
      if (totalErrEl) {
        totalErrEl.textContent = totalErrors;
        totalErrEl.style.color = totalErrors > 0 ? 'var(--red-500)' : 'var(--green-500)';
      }

      const lastIntEl = document.getElementById('tc-m-stat-last-interval');
      if (lastIntEl) {
        lastIntEl.textContent = this.lastIntervalRecord > 0 ? (this.lastIntervalRecord > 2000 ? '> 2000 ms' : this.lastIntervalRecord + ' ms') : '-';
      }
      const minIntEl = document.getElementById('tc-m-stat-min-interval');
      if (minIntEl) {
        minIntEl.textContent = (this.fastestInterval < Infinity && this.fastestInterval >= 10) ? this.fastestInterval + ' ms' : '-';
      }

      // Badges
      const errL = document.getElementById('tc-m-err-badge-l');
      if (errL) {
        errL.style.display = this.doubleClickCounts[0] > 0 ? 'inline-block' : 'none';
        errL.textContent = `⚠️ ${this.doubleClickCounts[0]} lỗi Double Click`;
      }
      const errM = document.getElementById('tc-m-err-badge-m');
      if (errM) {
        errM.style.display = this.doubleClickCounts[1] > 0 ? 'inline-block' : 'none';
        errM.textContent = `⚠️ ${this.doubleClickCounts[1]} lỗi Double Click`;
      }
      const errR = document.getElementById('tc-m-err-badge-r');
      if (errR) {
        errR.style.display = this.doubleClickCounts[2] > 0 ? 'inline-block' : 'none';
        errR.textContent = `⚠️ ${this.doubleClickCounts[2]} lỗi Double Click`;
      }

      // Banner
      const banner = document.getElementById('tc-mouse-status-banner');
      const bannerText = document.getElementById('tc-mouse-status-text');
      if (banner && bannerText) {
        if (totalErrors > 0) {
          banner.className = 'tc-mouse-alert-box error';
          bannerText.innerHTML = `<strong>⚠️ CẢNH BÁO LỖI:</strong> Phát hiện tổng cộng <strong>${totalErrors} lần Double Click</strong>! Lần gần nhất trên <strong>${this.btnNames[btn]}</strong> với khoảng cách chỉ <strong>${interval} ms</strong> (&le; ${this.mouseThreshold} ms). Switch có khả năng cao đã bị nảy tiếp điểm.`;
        } else {
          banner.className = 'tc-mouse-alert-box normal';
          bannerText.innerHTML = `<strong>✅ Bình thường:</strong> Đã kiểm tra ${totalClicks} lần click mà chưa phát hiện lỗi double click nào (ngưỡng: &le; ${this.mouseThreshold} ms).`;
        }
      }

      // Table
      const tbody = document.getElementById('tc-mouse-history-tbody');
      const histCount = document.getElementById('tc-m-history-count');
      if (tbody) {
        if (this.mouseHistory.length === 0) {
          tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-dim); padding: 1.5rem;">Chưa có dữ liệu click. Hãy click vào ô kiểm tra bên trên.</td></tr>';
        } else {
          tbody.innerHTML = this.mouseHistory.map(item => `
            <tr class="${item.isDouble ? 'error-row' : ''}">
              <td>${item.time}</td>
              <td>${item.btnName}</td>
              <td>${item.interval}</td>
              <td>${item.isDouble ? '<span style="color:var(--red-500); font-weight:700;">❌ LỖI DOUBLE CLICK</span>' : '<span style="color:var(--green-500)">✅ Hợp lệ</span>'}</td>
            </tr>
          `).join('');
        }
      }
      if (histCount) histCount.textContent = `${this.mouseHistory.length} sự kiện`;
    }

    resetMouseTest() {
      this.lastDownTime[0] = this.lastDownTime[1] = this.lastDownTime[2] = 0;
      this.clickCounts[0] = this.clickCounts[1] = this.clickCounts[2] = 0;
      this.doubleClickCounts[0] = this.doubleClickCounts[1] = this.doubleClickCounts[2] = 0;
      this.scrollCount = 0;
      this.fastestInterval = Infinity;
      this.lastIntervalRecord = 0;
      this.mouseHistory.length = 0;
      this.isHolding = false;
      clearInterval(this.holdTimer);

      const liveStatus = document.getElementById('tc-mouse-pad-live-status');
      if (liveStatus) liveStatus.textContent = '';
      const wheelText = document.getElementById('tc-m-stat-wheel-text');
      if (wheelText) wheelText.textContent = 'Cuộn: 0';

      const banner = document.getElementById('tc-mouse-status-banner');
      const bannerText = document.getElementById('tc-mouse-status-text');
      if (banner && bannerText) {
        banner.className = 'tc-mouse-alert-box normal';
        bannerText.textContent = 'Chưa phát hiện lỗi double click. Hãy click nhiều lần với tốc độ thông thường vào vùng kiểm tra bên dưới.';
      }

      this.updateMouseUI(false, 0, 0);
    }

    // ── 3. SCREEN TEST ─────────────────────────────────────────────────────
    initScreen() {
      const colorGrid = document.getElementById('tc-color-grid');
      if (colorGrid) {
        colorGrid.innerHTML = '';
        this.screenColors.forEach((c, i) => {
          const wrap = document.createElement('div');
          wrap.className = 'tc-color-swatch-wrap';
          const swatch = document.createElement('div');
          swatch.className = 'tc-color-swatch' + (i === 0 ? ' selected' : '');
          swatch.style.backgroundColor = c.value;
          const name = document.createElement('span');
          name.className = 'tc-color-name' + (i === 0 ? ' selected' : '');
          name.textContent = c.name;
          wrap.appendChild(swatch);
          wrap.appendChild(name);
          wrap.addEventListener('click', () => {
            this.screenIdx = i;
            document.querySelectorAll('.tc-color-swatch').forEach((s, j) => s.classList.toggle('selected', j === i));
            document.querySelectorAll('.tc-color-name').forEach((n, j) => n.classList.toggle('selected', j === i));
            if (this.screenActive) this.applyScreenColor();
          });
          colorGrid.appendChild(wrap);
        });
      }

      const brightnessSlider = document.getElementById('tc-brightness-slider');
      if (brightnessSlider) {
        brightnessSlider.addEventListener('input', () => {
          this.screenBrightness = +brightnessSlider.value;
          const valEl = document.getElementById('tc-brightness-val');
          if (valEl) valEl.textContent = this.screenBrightness + '%';
          if (this.screenActive) this.applyScreenColor();
        });
      }

      const startBtn = document.getElementById('tc-start-screen-btn');
      if (startBtn) {
        startBtn.addEventListener('click', () => this.startScreen());
      }

      const overlay = document.getElementById('tc-screen-overlay');
      if (overlay) {
        overlay.addEventListener('click', () => {
          this.screenIdx = (this.screenIdx + 1) % this.screenColors.length;
          this.applyScreenColor();
          document.querySelectorAll('.tc-color-swatch').forEach((s, j) => s.classList.toggle('selected', j === this.screenIdx));
          document.querySelectorAll('.tc-color-name').forEach((n, j) => n.classList.toggle('selected', j === this.screenIdx));
        });
      }

      window.addEventListener('keydown', (e) => {
        if (!this.screenActive) return;
        if (e.key === 'ArrowRight') {
          this.screenIdx = (this.screenIdx + 1) % this.screenColors.length;
          this.applyScreenColor();
        }
        if (e.key === 'ArrowLeft') {
          this.screenIdx = (this.screenIdx - 1 + this.screenColors.length) % this.screenColors.length;
          this.applyScreenColor();
        }
        if (e.key === 'Escape') this.exitScreen();
      }, true);

      document.addEventListener('fullscreenchange', () => {
        if (!document.fullscreenElement && this.screenActive) this.exitScreen();
      });
    }

    applyScreenColor() {
      const overlay = document.getElementById('tc-screen-overlay');
      if (!overlay) return;
      const c = this.screenColors[this.screenIdx];
      overlay.style.backgroundColor = c.value;
      overlay.style.filter = `brightness(${this.screenBrightness / 100})`;
    }

    startScreen() {
      this.screenActive = true;
      const overlay = document.getElementById('tc-screen-overlay');
      if (!overlay) return;
      this.applyScreenColor();
      overlay.classList.add('active');
      document.body.style.overflow = 'hidden';
      if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen().catch(() => {});
      }
    }

    exitScreen() {
      this.screenActive = false;
      const overlay = document.getElementById('tc-screen-overlay');
      if (overlay) overlay.classList.remove('active');
      document.body.style.overflow = '';
      if (document.fullscreenElement) {
        document.exitFullscreen().catch(() => {});
      }
    }

    // ── 4. WEBCAM TEST ─────────────────────────────────────────────────────
    initWebcamUI() {
      const sel = document.getElementById('tc-cam-select');
      if (sel) sel.addEventListener('change', (e) => this.openCam(e.target.value));

      const rescanBtn = document.getElementById('tc-cam-rescan-btn');
      if (rescanBtn) rescanBtn.addEventListener('click', () => { this.stopCam(); this.initCam(); });

      const retryBtn = document.getElementById('tc-cam-retry-btn');
      if (retryBtn) retryBtn.addEventListener('click', () => this.initCam());
    }

    showCamState(state, msg) {
      const loading = document.getElementById('tc-cam-loading');
      const errorBox = document.getElementById('tc-cam-error-box');
      const content = document.getElementById('tc-cam-content');
      const errMsg = document.getElementById('tc-cam-error-msg');

      if (loading) loading.style.display = state === 'loading' ? 'flex' : 'none';
      if (errorBox) errorBox.style.display = state === 'error' ? 'flex' : 'none';
      if (content) content.style.display = state === 'content' ? 'block' : 'none';
      if (errMsg && msg) errMsg.textContent = msg;
    }

    setCamDot(on) {
      const dot = document.getElementById('tc-cam-dot');
      if (dot) dot.className = 'tc-status-dot ' + (on ? 'on' : 'off');
      const text = document.getElementById('tc-cam-status-text');
      if (text) text.textContent = on ? 'Đang hoạt động' : 'Lỗi / Tắt';
    }

    async initCam() {
      this.showCamState('loading');
      try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          this.showCamState('error', 'Trình duyệt không hỗ trợ truy cập Webcam MediaDevices.');
          return;
        }
        const initStream = await navigator.mediaDevices.getUserMedia({ video: true });
        initStream.getTracks().forEach(t => t.stop());

        const devices = await navigator.mediaDevices.enumerateDevices();
        const vids = devices.filter(d => d.kind === 'videoinput');
        if (vids.length === 0) {
          this.showCamState('error', 'Không tìm thấy camera nào trên thiết bị này');
          return;
        }

        this.camList = vids.map((d, i) => ({ deviceId: d.deviceId, label: d.label || `Camera ${i + 1}` }));
        const sel = document.getElementById('tc-cam-select');
        if (sel) {
          sel.innerHTML = '';
          this.camList.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.deviceId;
            opt.textContent = c.label;
            sel.appendChild(opt);
          });
        }

        this.showCamState('content');
        this.openCam(this.camList[0].deviceId);
      } catch (err) {
        this.showCamState('error', 'Không thể truy cập camera. Vui lòng cấp quyền camera trong trình duyệt hoặc kiểm tra nút gạt camera vật lý.');
      }
    }

    async openCam(deviceId) {
      const rId = ++this.camRequestId;
      this.stopCam();
      try {
        const s = await navigator.mediaDevices.getUserMedia({ video: { deviceId: { exact: deviceId } } });
        if (rId !== this.camRequestId || !this.camMounted) {
          s.getTracks().forEach(t => t.stop());
          return;
        }
        this.camStream = s;
        const vid = document.getElementById('tc-cam-video');
        if (vid) {
          vid.srcObject = s;
          vid.style.display = 'block';
        }
        const noVid = document.getElementById('tc-cam-no-video');
        if (noVid) noVid.style.display = 'none';

        this.setCamDot(true);
        const label = this.camList.find(c => c.deviceId === deviceId)?.label || 'Camera';
        const lblEl = document.getElementById('tc-cam-label');
        if (lblEl) lblEl.textContent = label;
      } catch (e) {
        if (rId === this.camRequestId) {
          this.setCamDot(false);
          const noVid = document.getElementById('tc-cam-no-video');
          if (noVid) {
            noVid.style.display = '';
            noVid.textContent = 'Không thể mở camera này';
          }
        }
      }
    }

    stopCam() {
      if (this.camStream) {
        this.camStream.getTracks().forEach(t => t.stop());
        this.camStream = null;
      }
      const vid = document.getElementById('tc-cam-video');
      if (vid) {
        vid.srcObject = null;
        vid.style.display = 'none';
      }
      const noVid = document.getElementById('tc-cam-no-video');
      if (noVid) {
        noVid.style.display = '';
        noVid.textContent = 'Camera đang tắt';
      }
      this.setCamDot(false);
    }

    // ── 5. MICROPHONE TEST ─────────────────────────────────────────────────
    initMicUI() {
      const sel = document.getElementById('tc-mic-select');
      if (sel) sel.addEventListener('change', (e) => this.openMic(e.target.value));

      const retryBtn = document.getElementById('tc-mic-retry-btn');
      if (retryBtn) retryBtn.addEventListener('click', () => this.initMic());

      const gainSlider = document.getElementById('tc-mic-gain-slider');
      if (gainSlider) {
        gainSlider.addEventListener('input', (e) => {
          const val = +e.target.value;
          const pct = document.getElementById('tc-mic-gain-pct');
          if (pct) pct.textContent = val + '%';
          if (this.micGainNode) this.micGainNode.gain.value = val / 100;
        });
      }

      const recordBtn = document.getElementById('tc-mic-record-btn');
      if (recordBtn) {
        recordBtn.addEventListener('click', () => this.toggleMicRecording());
      }
    }

    showMicState(state, msg) {
      const loading = document.getElementById('tc-mic-loading');
      const errorBox = document.getElementById('tc-mic-error-box');
      const content = document.getElementById('tc-mic-content');
      const errMsg = document.getElementById('tc-mic-error-msg');

      if (loading) loading.style.display = state === 'loading' ? 'flex' : 'none';
      if (errorBox) errorBox.style.display = state === 'error' ? 'flex' : 'none';
      if (content) content.style.display = state === 'content' ? 'block' : 'none';
      if (errMsg && msg) errMsg.textContent = msg;
    }

    setMicDot(on) {
      const dot = document.getElementById('tc-mic-dot');
      if (dot) dot.className = 'tc-status-dot ' + (on ? 'on' : 'off');
      const text = document.getElementById('tc-mic-status-text');
      if (text) text.textContent = on ? 'Đang hoạt động' : 'Lỗi / Tắt';
    }

    async initMic() {
      this.showMicState('loading');
      try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          this.showMicState('error', 'Trình duyệt không hỗ trợ Audio Input API.');
          return;
        }
        const initStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        initStream.getTracks().forEach(t => t.stop());

        const devices = await navigator.mediaDevices.enumerateDevices();
        const auds = devices.filter(d => d.kind === 'audioinput');
        if (auds.length === 0) {
          this.showMicState('error', 'Không tìm thấy micro nào trên thiết bị này');
          return;
        }

        this.micList = auds.map((d, i) => ({ deviceId: d.deviceId, label: d.label || `Micro ${i + 1}` }));
        const sel = document.getElementById('tc-mic-select');
        if (sel) {
          sel.innerHTML = '';
          this.micList.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.deviceId;
            opt.textContent = m.label;
            sel.appendChild(opt);
          });
        }

        this.showMicState('content');
        const def = this.micList.find(m => m.label.toLowerCase().includes('default') || m.deviceId === 'default') || this.micList[0];
        if (sel) sel.value = def.deviceId;
        this.openMic(def.deviceId);
      } catch (err) {
        this.showMicState('error', 'Không thể truy cập micro. Vui lòng cấp quyền micro trong trình duyệt.');
      }
    }

    async openMic(deviceId) {
      const rId = ++this.micRequestId;
      this.stopMic();
      try {
        const s = await navigator.mediaDevices.getUserMedia({ audio: { deviceId: { exact: deviceId } } });
        if (rId !== this.micRequestId || !this.micMounted) {
          s.getTracks().forEach(t => t.stop());
          return;
        }
        this.micStream = s;
        const ACtx = window.AudioContext || window.webkitAudioContext;
        this.micAudioCtx = new ACtx();
        const source = this.micAudioCtx.createMediaStreamSource(s);
        this.micGainNode = this.micAudioCtx.createGain();

        const slider = document.getElementById('tc-mic-gain-slider');
        const sliderVal = slider ? +slider.value : 100;
        this.micGainNode.gain.value = sliderVal / 100;

        const analyser = this.micAudioCtx.createAnalyser();
        analyser.fftSize = 256;
        source.connect(this.micGainNode);
        this.micGainNode.connect(analyser);
        this.micAnalyser = analyser;

        this.setMicDot(true);
        const label = this.micList.find(m => m.deviceId === deviceId)?.label || 'Micro';
        const lblEl = document.getElementById('tc-mic-label');
        if (lblEl) lblEl.textContent = label;

        const inlineErr = document.getElementById('tc-mic-error-inline');
        if (inlineErr) inlineErr.style.display = 'none';

        const activeContent = document.getElementById('tc-mic-active-content');
        if (activeContent) activeContent.style.display = 'block';

        this.startVolMonitor();
      } catch (e) {
        if (rId === this.micRequestId) {
          this.setMicDot(false);
          const inlineErr = document.getElementById('tc-mic-error-inline');
          if (inlineErr) inlineErr.style.display = 'block';
        }
      }
    }

    startVolMonitor() {
      if (!this.micAnalyser) return;
      const data = new Uint8Array(this.micAnalyser.frequencyBinCount);
      const update = () => {
        if (!this.micAnalyser) return;
        this.micAnalyser.getByteFrequencyData(data);
        let sum = 0;
        for (let i = 0; i < data.length; i++) sum += data[i];
        const vol = Math.round((sum / data.length / 255) * 100);

        const pct = document.getElementById('tc-mic-vol-pct');
        if (pct) pct.textContent = vol + '%';
        const bar = document.getElementById('tc-mic-vol-bar');
        if (bar) {
          bar.style.width = vol + '%';
          bar.className = 'tc-vol-fill ' + (vol > 70 ? 'tc-vol-red' : vol > 40 ? 'tc-vol-amber' : 'tc-vol-green');
        }
        this.micAnimId = requestAnimationFrame(update);
      };
      update();
    }

    toggleMicRecording() {
      const recBtn = document.getElementById('tc-mic-record-btn');
      if (!this.micRecording) {
        if (!this.micStream) return;
        const playBox = document.getElementById('tc-mic-playback');
        if (playBox) playBox.style.display = 'none';

        this.micChunks = [];
        this.micRecorder = new MediaRecorder(this.micStream);
        this.micRecorder.ondataavailable = e => {
          if (e.data.size > 0) this.micChunks.push(e.data);
        };
        this.micRecorder.onstop = () => {
          const blob = new Blob(this.micChunks, { type: 'audio/webm' });
          const url = URL.createObjectURL(blob);
          const audioEl = document.getElementById('tc-mic-audio');
          if (audioEl) audioEl.src = url;
          if (playBox) playBox.style.display = 'block';
        };
        this.micRecorder.start();
        this.micRecording = true;
        if (recBtn) {
          recBtn.textContent = '⏹ Dừng thu';
          recBtn.className = 'tc-btn tc-btn-red';
        }
      } else {
        if (this.micRecorder && this.micRecorder.state !== 'inactive') {
          this.micRecorder.stop();
        }
        this.micRecording = false;
        if (recBtn) {
          recBtn.textContent = '🎙 Thu âm';
          recBtn.className = 'tc-btn tc-btn-coral';
        }
      }
    }

    stopMic() {
      if (this.micAnimId) { cancelAnimationFrame(this.micAnimId); this.micAnimId = null; }
      if (this.micRecorder && this.micRecorder.state !== 'inactive') this.micRecorder.stop();
      this.micRecorder = null;
      this.micRecording = false;

      if (this.micStream) {
        this.micStream.getTracks().forEach(t => t.stop());
        this.micStream = null;
      }
      if (this.micAudioCtx) {
        this.micAudioCtx.close().catch(() => {});
        this.micAudioCtx = null;
      }
      this.micGainNode = null;
      this.micAnalyser = null;

      const bar = document.getElementById('tc-mic-vol-bar');
      if (bar) bar.style.width = '0%';
      const pct = document.getElementById('tc-mic-vol-pct');
      if (pct) pct.textContent = '0%';
      const recBtn = document.getElementById('tc-mic-record-btn');
      if (recBtn) {
        recBtn.textContent = '🎙 Thu âm';
        recBtn.className = 'tc-btn tc-btn-coral';
      }
      this.setMicDot(false);
    }

    // ── 6. SPEAKER TEST ────────────────────────────────────────────────────
    initSpeakerUI() {
      const volSlider = document.getElementById('tc-speaker-vol-slider');
      if (volSlider) {
        volSlider.addEventListener('input', (e) => {
          const val = +e.target.value;
          const valEl = document.getElementById('tc-speaker-vol-val');
          if (valEl) valEl.textContent = val + '%';
          if (this.spkGain) this.spkGain.gain.value = val / 100;
        });
      }
      this.buildTracks();
    }

    buildTracks() {
      if (this.tracksBuilt) return;
      this.tracksBuilt = true;
      const grid = document.getElementById('tc-tracks-grid');
      if (!grid) return;
      grid.innerHTML = '';
      this.tracks.forEach(t => {
        const card = document.createElement('div');
        card.className = 'tc-track-card';
        card.dataset.key = t.key;

        const body = document.createElement('div');
        body.className = 'tc-track-body';
        body.innerHTML = `
          <div class="tc-track-icon">${t.emoji}</div>
          <div class="tc-track-info">
            <p class="tc-track-name">${t.label}</p>
            <p class="tc-track-desc">${t.description}</p>
          </div>
          <div class="tc-track-btn">▶ Phát</div>
        `;
        card.appendChild(body);
        card.addEventListener('click', () => this.playTrack(t.key));
        grid.appendChild(card);
      });
    }

    getSpkCtx() {
      if (!this.spkAudioCtx || this.spkAudioCtx.state === 'closed') {
        const ACtx = window.AudioContext || window.webkitAudioContext;
        this.spkAudioCtx = new ACtx();
      }
      if (this.spkAudioCtx.state === 'suspended') {
        this.spkAudioCtx.resume();
      }
      return this.spkAudioCtx;
    }

    stopSpk() {
      if (this.spkSweep) { clearInterval(this.spkSweep); this.spkSweep = null; }
      if (this.spkOsc) {
        try { this.spkOsc.stop(); } catch (e) {}
        this.spkOsc.disconnect();
        this.spkOsc = null;
      }
      if (this.spkGain) { this.spkGain.disconnect(); this.spkGain = null; }
      if (this.spkPan) { this.spkPan.disconnect(); this.spkPan = null; }
      this.playingKey = null;
      this.updateTrackCards();
    }

    playTrack(key) {
      if (this.playingKey === key) {
        this.stopSpk();
        return;
      }
      this.stopSpk();
      const volSlider = document.getElementById('tc-speaker-vol-slider');
      const vol = volSlider ? (+volSlider.value / 100) : 0.7;

      const ctx = this.getSpkCtx();
      this.spkGain = ctx.createGain();
      this.spkGain.gain.value = vol;

      if (key === 'left' || key === 'right') {
        this.spkOsc = ctx.createOscillator();
        this.spkOsc.type = 'sine';
        this.spkOsc.frequency.value = 1000;
        this.spkPan = ctx.createStereoPanner();
        this.spkPan.pan.value = key === 'left' ? -1 : 1;
        this.spkOsc.connect(this.spkPan);
        this.spkPan.connect(this.spkGain);
        this.spkGain.connect(ctx.destination);
        this.spkOsc.start();
      } else if (key === 'sweep') {
        this.spkOsc = ctx.createOscillator();
        this.spkOsc.type = 'sine';
        this.spkOsc.frequency.value = 80;
        this.spkOsc.connect(this.spkGain);
        this.spkGain.connect(ctx.destination);
        this.spkOsc.start();
        let freq = 80;
        const step = (8000 - 80) / 80;
        this.spkSweep = setInterval(() => {
          if (!this.spkOsc) return;
          freq += step;
          if (freq > 8000) freq = 80;
          this.spkOsc.frequency.value = freq;
        }, 50);
      } else {
        const freqMap = { bass: 80, mid: 1000, high: 8000 };
        this.spkOsc = ctx.createOscillator();
        this.spkOsc.type = 'sine';
        this.spkOsc.frequency.value = freqMap[key] ?? 1000;
        this.spkOsc.connect(this.spkGain);
        this.spkGain.connect(ctx.destination);
        this.spkOsc.start();
      }

      this.playingKey = key;
      this.updateTrackCards();
    }

    updateTrackCards() {
      document.querySelectorAll('.tc-track-card').forEach(card => {
        const key = card.dataset.key;
        const isPlaying = key === this.playingKey;
        card.classList.toggle('playing', isPlaying);
        const btn = card.querySelector('.tc-track-btn');
        if (btn) btn.textContent = isPlaying ? '⏹ Dừng' : '▶ Phát';

        let wf = card.querySelector('.tc-waveform');
        if (isPlaying && !wf) {
          wf = document.createElement('div');
          wf.className = 'tc-waveform';
          for (let i = 0; i < 24; i++) {
            const bar = document.createElement('div');
            bar.className = 'tc-wave-bar';
            bar.style.height = Math.abs(Math.sin(i * 0.6)) * 100 + '%';
            bar.style.animationDelay = i * 40 + 'ms';
            wf.appendChild(bar);
          }
          card.appendChild(wf);
        } else if (!isPlaying && wf) {
          wf.remove();
        }
      });
    }

    // ── 7. BATTERY TEST ────────────────────────────────────────────────────
    initBatteryUIEvents() {
      this.setupCopyBtn('tc-copy-cmd-btn', 'irm j2c.cc/batterycheck | iex');
      this.setupCopyBtn('tc-copy-trouble1-btn', 'iex (curl.exe -s --doh-url https://1.1.1.1/dns-query j2c.cc/batterycheck | Out-String)');
      this.setupCopyBtn('tc-copy-trouble2-btn', '[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12');

      const troubleBtn = document.getElementById('tc-trouble-btn');
      if (troubleBtn) {
        troubleBtn.addEventListener('click', () => {
          const content = document.getElementById('tc-trouble-content');
          const icon = document.getElementById('tc-trouble-icon');
          if (content) {
            content.classList.toggle('open');
            if (icon) icon.textContent = content.classList.contains('open') ? '▼' : '▶';
          }
        });
      }
    }

    setupCopyBtn(id, text) {
      const btn = document.getElementById(id);
      if (!btn) return;
      btn.addEventListener('click', async () => {
        try {
          await navigator.clipboard.writeText(text);
          const orig = btn.textContent;
          btn.textContent = '✓ Đã sao chép';
          btn.style.color = 'var(--green-500)';
          setTimeout(() => {
            btn.textContent = orig;
            btn.style.color = '';
          }, 2000);
        } catch (e) { }
      });
    }

    formatBatTime(s) {
      if (!isFinite(s)) return '—';
      const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
      return h > 0 ? `${h}h ${m}m` : `${m} phút`;
    }

    battColor(level, charging) {
      if (charging) return 'charging';
      if (level > 0.5) return 'high';
      if (level > 0.2) return 'mid';
      return 'low';
    }

    updateBatteryUI(b) {
      const noBat = b.level === 1 && b.charging && !isFinite(b.dischargingTime) && !isFinite(b.chargingTime);
      const noBatBox = document.getElementById('tc-battery-no-battery');
      const mainBox = document.getElementById('tc-battery-main');

      if (noBatBox) noBatBox.style.display = noBat ? 'block' : 'none';
      if (mainBox) mainBox.style.display = noBat ? 'none' : 'block';

      if (!noBat) {
        const pct = Math.round(b.level * 100);
        const pctEl = document.getElementById('tc-bat-pct');
        if (pctEl) pctEl.textContent = pct + '%';
        const pctLbl = document.getElementById('tc-bat-pct-label');
        if (pctLbl) {
          pctLbl.textContent = pct + '%';
          pctLbl.style.color = b.level > 0.15 ? 'var(--bg-deep)' : 'var(--text-primary)';
        }

        const fill = document.getElementById('tc-bat-fill');
        if (fill) {
          fill.style.width = (b.level * 100) + '%';
          fill.className = 'tc-battery-fill ' + this.battColor(b.level, b.charging);
        }

        const charLabel = document.getElementById('tc-bat-charging-label');
        if (charLabel) charLabel.textContent = b.charging ? '⚡ Đang sạc' : '';

        const charRow = document.getElementById('tc-bat-charging-row');
        if (charRow) {
          charRow.style.display = b.charging ? 'flex' : 'none';
          const txt = isFinite(b.chargingTime) ? `Đang sạc — đầy sau ${this.formatBatTime(b.chargingTime)}` : 'Đang sạc';
          const charTxt = document.getElementById('tc-bat-charging-text');
          if (charTxt) charTxt.textContent = txt;
        }

        const disRow = document.getElementById('tc-bat-discharging-row');
        if (disRow) {
          disRow.style.display = (!b.charging && isFinite(b.dischargingTime)) ? 'block' : 'none';
          const disTxt = document.getElementById('tc-bat-discharging-text');
          if (disTxt && !b.charging && isFinite(b.dischargingTime)) {
            disTxt.textContent = `Còn khoảng ${this.formatBatTime(b.dischargingTime)} sử dụng`;
          }
        }

        const stateEl = document.getElementById('tc-bat-state');
        if (stateEl) {
          stateEl.textContent = b.charging ? '⚡ Sạc' : '🔋 Xả';
          stateEl.style.color = b.charging ? 'var(--accent-sky)' : 'var(--green-500)';
        }

        const lvlEl = document.getElementById('tc-bat-level');
        if (lvlEl) lvlEl.textContent = pct + '%';

        const timeEl = document.getElementById('tc-bat-time');
        if (timeEl) timeEl.textContent = this.formatBatTime(b.dischargingTime);

        const warn = document.getElementById('tc-bat-warn');
        if (warn) {
          if (!b.charging && b.level <= 0.2) {
            warn.style.display = 'block';
            const warnTxt = document.getElementById('tc-bat-warn-text');
            if (warnTxt) warnTxt.textContent = `⚠️ Pin yếu (${pct}%) — cắm sạc ngay!`;
          } else {
            warn.style.display = 'none';
          }
        }
      }
    }

    async initBattery() {
      if (!('getBattery' in navigator)) {
        const noSupport = document.getElementById('tc-battery-no-support');
        if (noSupport) noSupport.style.display = 'block';
        return;
      }
      try {
        this.battMgr = await navigator.getBattery();
        this.updateBatteryUI(this.battMgr);
        const upd = () => this.updateBatteryUI(this.battMgr);
        this.battMgr.addEventListener('levelchange', upd);
        this.battMgr.addEventListener('chargingchange', upd);
        this.battMgr.addEventListener('chargingtimechange', upd);
        this.battMgr.addEventListener('dischargingtimechange', upd);
      } catch (e) {
        const noSupport = document.getElementById('tc-battery-no-support');
        if (noSupport) noSupport.style.display = 'block';
      }
    }

    // ── 8. FPS BENCHMARK (VUE 3 APP) ───────────────────────────────────────
    initFpsApp() {
      if (!window.Vue) {
        console.warn('Vue 3 is not loaded yet');
        return;
      }
      const { createApp, ref, reactive, computed, onMounted, onUnmounted } = Vue;

      const app = createApp({
        setup() {
          const fps = ref(0);
          const frameTime = ref(0);
          const frameTimeHistory = ref([]);
          const maxHistoryLength = 120;
          let lastTimestamp = 0, frameCount = 0, fpsAccumulator = 0, animationId = 0;

          const presets = [
            { name: '15 vs 30 vs 60', rates: [15, 30, 60] },
            { name: '30 vs 60', rates: [30, 60] },
            { name: '30 vs 60 vs 120', rates: [30, 60, 120] },
            { name: '60 vs 120 vs 144', rates: [60, 120, 144] },
            { name: '60 vs 144 vs 240', rates: [60, 144, 240] },
            { name: 'Tuỳ chỉnh', rates: [] },
          ];
          const selectedPresetIndex = ref(0);
          const laneColors = [
            { color: '#FF6B4A', glow: 'rgba(255,107,74,0.3)' },
            { color: '#38BDF8', glow: 'rgba(56,189,248,0.3)' },
            { color: '#FFB830', glow: 'rgba(255,184,48,0.3)' },
            { color: '#fb7185', glow: 'rgba(251,113,133,0.3)' },
            { color: '#34d399', glow: 'rgba(52,211,153,0.3)' },
          ];
          const lanes = reactive([]);

          function buildLanes(rates) {
            lanes.length = 0;
            rates.forEach((targetFps, i) => {
              const idx = i % laneColors.length;
              lanes.push({
                label: `${targetFps} FPS`,
                targetFps,
                color: laneColors[idx].color,
                glow: laneColors[idx].glow,
                position: 0,
                lastDrawTime: 0
              });
            });
          }

          function applyPreset(index) {
            selectedPresetIndex.value = index;
            const preset = presets[index];
            if (preset && preset.rates.length > 0) buildLanes(preset.rates);
          }

          const customFpsInput = ref('60');

          function addCustomLane() {
            const val = parseInt(customFpsInput.value, 10);
            if (val > 0 && val <= 1000 && lanes.length < 5) {
              const idx = lanes.length % laneColors.length;
              lanes.push({
                label: `${val} FPS`,
                targetFps: val,
                color: laneColors[idx].color,
                glow: laneColors[idx].glow,
                position: 0,
                lastDrawTime: 0
              });
              selectedPresetIndex.value = presets.length - 1;
            }
          }

          function removeLane(index) {
            lanes.splice(index, 1);
            selectedPresetIndex.value = presets.length - 1;
          }

          const speeds = [480, 960, 1920, 3840];
          const selectedSpeedIndex = ref(1);
          const speed = computed(() => speeds[selectedSpeedIndex.value] ?? 960);
          const isPaused = ref(false);
          const showGraph = ref(true);
          const showSettings = ref(false);
          const testMode = ref('bars');
          const activeTab = ref('framerate');

          const detectedHz = ref(0);

          function detectRefreshRate() {
            let hzFrames = 0, hzStart = 0, hzId = 0;
            function hzLoop(ts) {
              if (hzStart === 0) { hzStart = ts; hzFrames = 0; }
              hzFrames++;
              if (ts - hzStart >= 1000) {
                detectedHz.value = Math.round(hzFrames / ((ts - hzStart) / 1000));
              } else {
                hzId = requestAnimationFrame(hzLoop);
              }
            }
            hzId = requestAnimationFrame(hzLoop);
            setTimeout(() => cancelAnimationFrame(hzId), 1500);
          }

          // Jank Detector
          const jankEvents = ref([]);
          const jankTimelineLength = 300;
          const jankFrameTimes = ref([]);
          const jankScore = ref(100);
          const jankTotalDropped = ref(0);
          const jankRecording = ref(true);
          const jankStartTime = ref(0);
          const jankThreshold = 25;

          function updateJank(delta, timestamp) {
            if (activeTab.value !== 'jank' || !jankRecording.value) return;
            if (jankStartTime.value === 0) jankStartTime.value = timestamp;
            jankFrameTimes.value.push(delta);
            if (jankFrameTimes.value.length > jankTimelineLength) jankFrameTimes.value.shift();
            if (delta > jankThreshold) {
              jankTotalDropped.value++;
              jankEvents.value.push({ timestamp: timestamp - jankStartTime.value, frameDuration: Math.round(delta) });
              if (jankEvents.value.length > 200) jankEvents.value.shift();
            }
            const recent = jankFrameTimes.value.slice(-120);
            const goodFrames = recent.filter(t => t <= jankThreshold).length;
            jankScore.value = recent.length > 0 ? Math.round((goodFrames / recent.length) * 100) : 100;
          }

          function resetJank() {
            jankEvents.value = [];
            jankFrameTimes.value = [];
            jankScore.value = 100;
            jankTotalDropped.value = 0;
            jankStartTime.value = 0;
          }

          const jankTimelinePoints = computed(() => {
            const history = jankFrameTimes.value;
            if (history.length < 2) return '';
            const w = 360, h = 80, maxMs = 60;
            const step = w / (jankTimelineLength - 1);
            return history.map((ms, i) => `${i * step},${h - Math.min(ms / maxMs, 1) * h}`).join(' ');
          });

          const jankTimelineFill = computed(() => {
            const pts = jankTimelinePoints.value;
            if (!pts) return '';
            const lastX = ((jankFrameTimes.value.length - 1) / (jankTimelineLength - 1)) * 360;
            return `0,80 ${pts} ${lastX},80`;
          });

          function jankScoreColor(score) {
            if (score >= 95) return 'tc-fps-color-green';
            if (score >= 80) return 'tc-fps-color-amber';
            return 'tc-fps-color-red';
          }

          function jankScoreLabel(score) {
            if (score >= 98) return 'Hoàn hảo';
            if (score >= 95) return 'Rất mượt';
            if (score >= 85) return 'Ổn';
            if (score >= 70) return 'Hơi trễ';
            return 'Trễ nhiều';
          }

          // Scroll Jank
          const scrollJankScore = ref(100);
          const scrollFrameTimes = ref([]);
          const scrollDroppedFrames = ref(0);
          const scrollIsMonitoring = ref(false);
          const scrollTotalFrames = ref(0);
          let scrollRafId = 0, scrollLastTs = 0, scrolling = false, scrollTimeout = 0;

          function onScroll() {
            scrolling = true;
            clearTimeout(scrollTimeout);
            scrollTimeout = window.setTimeout(() => { scrolling = false; }, 150);
          }

          function scrollMonitorLoop(ts) {
            if (!scrollIsMonitoring.value) return;
            if (scrollLastTs > 0 && scrolling) {
              const delta = ts - scrollLastTs;
              scrollTotalFrames.value++;
              scrollFrameTimes.value.push(delta);
              if (scrollFrameTimes.value.length > 300) scrollFrameTimes.value.shift();
              if (delta > jankThreshold) scrollDroppedFrames.value++;
              const recent = scrollFrameTimes.value.slice(-120);
              const good = recent.filter(t => t <= jankThreshold).length;
              scrollJankScore.value = recent.length > 0 ? Math.round((good / recent.length) * 100) : 100;
            }
            scrollLastTs = ts;
            scrollRafId = requestAnimationFrame(scrollMonitorLoop);
          }

          function startScrollMonitor() {
            if (scrollIsMonitoring.value) return;
            scrollIsMonitoring.value = true;
            scrollLastTs = 0;
            scrollRafId = requestAnimationFrame(scrollMonitorLoop);
          }

          function stopScrollMonitor() {
            scrollIsMonitoring.value = false;
            cancelAnimationFrame(scrollRafId);
          }

          function resetScrollJank() {
            scrollJankScore.value = 100;
            scrollFrameTimes.value = [];
            scrollDroppedFrames.value = 0;
            scrollTotalFrames.value = 0;
          }

          const scrollTimelinePoints = computed(() => {
            const history = scrollFrameTimes.value;
            if (history.length < 2) return '';
            const w = 360, h = 50, maxMs = 60;
            const step = w / 299;
            return history.map((ms, i) => `${i * step},${h - Math.min(ms / maxMs, 1) * h}`).join(' ');
          });

          // Ghosting
          const ghostingSpeed = ref(2);
          const ghostingPosition = ref(0);
          const ghostingTileWidth = 384;

          const trackContainer = ref(null);
          const containerWidth = ref(800);
          const isFullscreen = ref(false);

          function toggleFullscreen() {
            const elem = trackContainer.value;
            if (!elem) return;
            if (!document.fullscreenElement) {
              (elem.requestFullscreen || elem.webkitRequestFullscreen || function () { }).call(elem);
            } else {
              (document.exitFullscreen || document.webkitExitFullscreen || function () { }).call(document);
            }
          }

          function onFullscreenChange() {
            isFullscreen.value = !!(document.fullscreenElement || document.webkitFullscreenElement);
            setTimeout(updateContainerWidth, 100);
          }

          const laneHeight = computed(() => {
            if (lanes.length === 0) return 80;
            const availableHeight = isFullscreen.value && trackContainer.value ? trackContainer.value.clientHeight : 300;
            return Math.max(40, Math.floor(availableHeight / lanes.length) - 8);
          });

          function updateGhosting(delta) {
            if (activeTab.value !== 'ghosting' || isPaused.value) return;
            const pxPerMs = (ghostingSpeed.value * 200) / 1000;
            ghostingPosition.value = (ghostingPosition.value + pxPerMs * delta) % ghostingTileWidth;
          }

          const minFps = ref(Infinity);
          const maxFps = ref(0);
          const avgFps = ref(0);
          const fpsSum = ref(0);
          const fpsSamples = ref(0);
          const droppedFrames = ref(0);

          function resetStats() {
            minFps.value = Infinity;
            maxFps.value = 0;
            avgFps.value = 0;
            fpsSum.value = 0;
            fpsSamples.value = 0;
            droppedFrames.value = 0;
            frameTimeHistory.value = [];
            lanes.forEach(lane => { lane.position = 0; lane.lastDrawTime = 0; });
          }

          const graphPoints = computed(() => {
            const history = frameTimeHistory.value;
            if (history.length < 2) return '';
            const w = 360, h = 70, maxMs = 50;
            const step = w / (maxHistoryLength - 1);
            return history.map((ms, i) => `${i * step},${h - Math.min(ms / maxMs, 1) * h}`).join(' ');
          });

          const graphFill = computed(() => {
            const pts = graphPoints.value;
            return pts ? `0,70 ${pts} 360,70` : '';
          });

          const targetY = computed(() => 70 - (16.67 / 50) * 70);

          function animate(timestamp) {
            if (lastTimestamp === 0) {
              lastTimestamp = timestamp;
              lanes.forEach(lane => lane.lastDrawTime = timestamp);
              animationId = requestAnimationFrame(animate);
              return;
            }
            const delta = timestamp - lastTimestamp;
            lastTimestamp = timestamp;
            frameTime.value = delta;
            frameTimeHistory.value.push(delta);
            if (frameTimeHistory.value.length > maxHistoryLength) frameTimeHistory.value.shift();
            if (delta > 20) droppedFrames.value++;

            frameCount++;
            fpsAccumulator += delta;
            if (fpsAccumulator >= 500) {
              const currentFps = Math.round((frameCount / fpsAccumulator) * 1000);
              fps.value = currentFps;
              frameCount = 0;
              fpsAccumulator = 0;
              if (currentFps > 0 && currentFps < 1000) {
                if (currentFps < minFps.value) minFps.value = currentFps;
                if (currentFps > maxFps.value) maxFps.value = currentFps;
                fpsSum.value += currentFps;
                fpsSamples.value++;
                avgFps.value = Math.round(fpsSum.value / fpsSamples.value);
              }
            }

            if (!isPaused.value) {
              const pxPerMs = speed.value / 1000;
              const w = containerWidth.value;
              for (const lane of lanes) {
                const interval = 1000 / lane.targetFps;
                const elapsed = timestamp - lane.lastDrawTime;
                if (elapsed >= interval) {
                  const steps = Math.floor(elapsed / interval);
                  const dx = pxPerMs * interval * steps;
                  lane.position = (lane.position + dx) % (w + 80);
                  lane.lastDrawTime = timestamp - (elapsed % interval);
                }
              }
            }

            updateGhosting(delta);
            updateJank(delta, timestamp);
            animationId = requestAnimationFrame(animate);
          }

          function updateContainerWidth() {
            if (trackContainer.value) containerWidth.value = trackContainer.value.clientWidth;
          }

          function fpsColorClass(value) {
            if (value >= 55) return 'tc-fps-color-green';
            if (value >= 30) return 'tc-fps-color-amber';
            return 'tc-fps-color-red';
          }

          function frameTimeColorClass(ms) {
            if (ms <= 17) return 'tc-fps-color-green';
            if (ms <= 33) return 'tc-fps-color-amber';
            return 'tc-fps-color-red';
          }

          onMounted(() => {
            applyPreset(0);
            updateContainerWidth();
            detectRefreshRate();
            window.addEventListener('resize', updateContainerWidth);
            document.addEventListener('fullscreenchange', onFullscreenChange);
            document.addEventListener('webkitfullscreenchange', onFullscreenChange);
            animationId = requestAnimationFrame(animate);
          });

          onUnmounted(() => {
            cancelAnimationFrame(animationId);
            stopScrollMonitor();
            window.removeEventListener('resize', updateContainerWidth);
            document.removeEventListener('fullscreenchange', onFullscreenChange);
            document.removeEventListener('webkitfullscreenchange', onFullscreenChange);
          });

          return {
            fps, frameTime, minFps, maxFps, avgFps, droppedFrames, fpsColorClass, frameTimeColorClass, resetStats,
            lanes, laneHeight, laneColors, presets, selectedPresetIndex, applyPreset,
            customFpsInput, addCustomLane, removeLane,
            speeds, selectedSpeedIndex, speed, isPaused, showGraph, showSettings, testMode, activeTab,
            detectedHz,
            jankScore, jankTotalDropped, jankThreshold, jankRecording, resetJank,
            jankTimelineFill, jankTimelinePoints, jankFrameTimes, jankEvents, jankTimelineLength,
            jankScoreColor, jankScoreLabel,
            scrollJankScore, scrollDroppedFrames, scrollTotalFrames, resetScrollJank,
            scrollTimelinePoints, scrollFrameTimes, onScroll, startScrollMonitor,
            ghostingSpeed, ghostingTileWidth, ghostingPosition,
            graphFill, graphPoints, targetY,
            trackContainer, containerWidth,
            isFullscreen, toggleFullscreen,
            Math,
          };
        }
      });

      const mountEl = document.getElementById('tc-fps-app');
      if (mountEl) {
        app.mount('#tc-fps-app');
        this.fpsVueApp = app;
      }
    }
  }

  // Register on window
  window.testComputer = new TestComputerController();

  document.addEventListener('DOMContentLoaded', () => {
    // If initially on tab-test-computer, init immediately
    const sec = document.getElementById('tab-test-computer');
    if (sec && sec.classList.contains('active')) {
      window.testComputer.onTabActivated();
    }
  });

})();
