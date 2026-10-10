"""
════════════════════════════════════════════════════════════════════════════════
 IT Tool LTT 2026 - Native Zoom Screen Controller
 100% Python Native Architecture (Zero External Binaries)
 Author: Lê Thế Tuấn | 0352 194 195 | https://lethetuanpc.blogspot.com
════════════════════════════════════════════════════════════════════════════════
 Features:
 1. Zoom (Ctrl+1): High-speed Python/PIL GDI screen magnification with mouse pan.
 2. LiveZoom (Ctrl+4): Windows Magnification API interactive desktop zoom.
 3. Draw (Ctrl+2): Freehand, straight line (Shift), rectangle (Ctrl),
    ellipse (Tab), arrow (Ctrl+Shift), colors (R, G, B, Y, O, P, W, K),
    Whiteboard (W), Blackboard (K), Undo (Ctrl+Z), Copy (Ctrl+C), Save (Ctrl+S).
 4. Type (T): Direct screen text typing with scalable font.
 5. Break Timer (Ctrl+3): Presentation countdown timer with opacity.
 6. Snip (Ctrl+6): Regional screen crop directly to Windows Clipboard.
 7. DemoType (Ctrl+7): Automated typing demo from script.
 8. Global Hotkeys: Safe Win32 RegisterHotKey listener without OS hook delays.
════════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import time
import json
import threading
import subprocess
import ctypes
from ctypes import wintypes, c_float, c_int, c_bool

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def _resolve_config_file():
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        p = os.path.join(appdata, "IT Tool LTT", "config", "zoom_screen.json")
        if os.path.exists(p):
            return os.path.dirname(p), p
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    bundled = os.path.join(base, "config", "zoom_screen.json")
    return os.path.dirname(bundled), bundled

CONFIG_DIR, CONFIG_FILE = _resolve_config_file()

DEFAULT_HOTKEYS = {
    "zoom": "Ctrl + 1",
    "draw": "Ctrl + 2",
    "break": "Ctrl + 3",
    "livezoom": "Ctrl + 4",
    "record": "Ctrl + 5",
    "snip": "Ctrl + 6",
    "demotype": "Ctrl + 7",
    "panorama": "Ctrl + 8",
    "mirror": "Ctrl + 9"
}

ACTION_NAMES = {
    "zoom": "Phóng to màn hình (Zoom)",
    "draw": "Vẽ trực tiếp (Draw)",
    "break": "Đồng hồ nghỉ (Break Timer)",
    "livezoom": "Phóng to tương tác (LiveZoom)",
    "record": "Quay phim / GIF (Record)",
    "snip": "Cắt chụp vùng (Snip)",
    "demotype": "Trình diễn gõ phím (DemoType)",
    "panorama": "Chụp cuộn trang (Panorama)",
    "mirror": "Chiếu nhân bản (DemoMirror)"
}

ZOOM_LEVEL_MAP = {
    1: 1.25,
    2: 1.50,
    3: 1.75,
    4: 2.00,
    5: 2.25,
    6: 2.50,
    7: 3.00,
    8: 4.00
}


def zoom_val_to_slider_level(z_val):
    try:
        val = float(z_val)
    except Exception:
        return 4
    best_k = 4
    min_d = 999.0
    for k, v in ZOOM_LEVEL_MAP.items():
        d = abs(v - val)
        if d < min_d:
            min_d = d
            best_k = k
    return best_k

DEFAULT_SETTINGS = {
    "zoom_level": 2.0,
    "animate_zoom": True,
    "smooth_image": True,
    "snap_to_grid": True,
    "pen_color": 255,          # Red default
    "pen_width": 5,
    "break_timeout": 10,
    "break_opacity": 100,
    "break_show_desktop": True,
    "break_lock_workstation": False,
    "recording_format": 1,     # MP4
    "capture_system_audio": True,
    "capture_audio": False,
    "noise_cancellation": True,
    "record_aspect_ratio": False,
    "webcam_overlay": False,
    "webcam_position": 3,
    "webcam_size": 1,
    "webcam_shape": 0,
    "webcam_background_mode": 0,
    "demotype_speed": 55,
    "demotype_user_mode": False,
    "demotype_text": "",
    "hotkeys_enabled": True,
    "custom_hotkeys": dict(DEFAULT_HOTKEYS)
}


def normalize_hotkey_string(hk_str):
    """Normalizes any hotkey string into standard order: Ctrl + Alt + Shift + Win + Key."""
    if not hk_str:
        return ""
    hk_str = str(hk_str).strip()

    is_plus_key = False
    if hk_str.endswith('++') or hk_str.endswith('+ +'):
        is_plus_key = True
        hk_str = hk_str[:-1].rstrip('+').strip()

    raw_parts = [p.strip() for p in hk_str.split('+') if p.strip()]
    has_ctrl = any(p.upper() in ('CTRL', 'CONTROL') for p in raw_parts)
    has_alt = any(p.upper() in ('ALT', 'MENU') for p in raw_parts)
    has_shift = any(p.upper() == 'SHIFT' for p in raw_parts)
    has_win = any(p.upper() in ('WIN', 'WINDOWS', 'SUPER', 'META') for p in raw_parts)

    key = ""
    if is_plus_key:
        key = "+"
    else:
        for p in raw_parts:
            if p.upper() not in ('CTRL', 'CONTROL', 'ALT', 'MENU', 'SHIFT', 'WIN', 'WINDOWS', 'SUPER', 'META'):
                key = p
                break

    if not key:
        return ""

    key_upper = key.upper()
    if key_upper.startswith('NUMPAD') or key_upper.startswith('NUM '):
        sub = key_upper.replace('NUMPAD', '').replace('NUM', '').strip()
        if sub in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'):
            key = f"Num {sub}"
        elif sub in ('+', 'ADD'):
            key = "Num +"
        elif sub in ('-', 'SUBTRACT'):
            key = "Num -"
        elif sub in ('*', 'MULTIPLY'):
            key = "Num *"
        elif sub in ('/', 'DIVIDE'):
            key = "Num /"
        elif sub in ('.', 'DECIMAL'):
            key = "Num ."
    elif len(key) == 1:
        key = key.upper()
    elif key_upper.startswith('F') and key_upper[1:].isdigit():
        key = key_upper
    else:
        special_names = {
            'SPACE': 'Space', 'TAB': 'Tab', 'ENTER': 'Enter', 'RETURN': 'Enter',
            'ESC': 'Esc', 'ESCAPE': 'Esc', 'INSERT': 'Insert', 'DELETE': 'Delete', 'DEL': 'Delete',
            'HOME': 'Home', 'END': 'End', 'PAGEUP': 'PageUp', 'PGUP': 'PageUp',
            'PAGEDOWN': 'PageDown', 'PGDN': 'PageDown',
            'UP': 'Up', 'DOWN': 'Down', 'LEFT': 'Left', 'RIGHT': 'Right',
            'BACKSPACE': 'Backspace', 'BACK': 'Backspace', 'PRINTSCREEN': 'PrintScreen', 'PAUSE': 'Pause'
        }
        key = special_names.get(key_upper, key.capitalize())

    mods = []
    if has_ctrl:
        mods.append("Ctrl")
    if has_alt:
        mods.append("Alt")
    if has_shift:
        mods.append("Shift")
    if has_win:
        mods.append("Win")

    return " + ".join(mods + [key]) if mods else key


def parse_hotkey_string(hk_str):
    """Converts normalized hotkey string into Win32 (modifiers_flag, virtual_key_code)."""
    norm = normalize_hotkey_string(hk_str)
    if not norm:
        return None, None

    if ' + ' in norm:
        parts = norm.split(' + ')
        key = parts[-1].strip()
        mod_parts = [p.upper() for p in parts[:-1]]
    else:
        key = norm.strip()
        mod_parts = []

    mod = 0
    if 'CTRL' in mod_parts:
        mod |= 0x0002
    if 'ALT' in mod_parts:
        mod |= 0x0001
    if 'SHIFT' in mod_parts:
        mod |= 0x0004
    if 'WIN' in mod_parts:
        mod |= 0x0008

    vk = None
    key_upper = key.upper()

    if key_upper.startswith('NUM ') or key_upper.startswith('NUMPAD '):
        sub = key_upper.split()[-1]
        numpad_map = {
            '0': 0x60, '1': 0x61, '2': 0x62, '3': 0x63, '4': 0x64,
            '5': 0x65, '6': 0x66, '7': 0x67, '8': 0x68, '9': 0x69,
            '*': 0x6A, '+': 0x6B, '-': 0x6D, '.': 0x6E, '/': 0x6F
        }
        vk = numpad_map.get(sub)
    elif key_upper.startswith('F') and key_upper[1:].isdigit():
        f_num = int(key_upper[1:])
        if 1 <= f_num <= 24:
            vk = 0x70 + (f_num - 1)
    elif len(key) == 1:
        if '0' <= key <= '9':
            vk = ord(key)
        elif 'A' <= key_upper <= 'Z':
            vk = ord(key_upper)
        else:
            OEM_MAP = {
                ';': 0xBA, ':': 0xBA,
                '=': 0xBB, '+': 0xBB,
                ',': 0xBC, '<': 0xBC,
                '-': 0xBD, '_': 0xBD,
                '.': 0xBE, '>': 0xBE,
                '/': 0xBF, '?': 0xBF,
                '`': 0xC0, '~': 0xC0,
                '[': 0xDB, '{': 0xDB,
                '\\': 0xDC, '|': 0xDC,
                ']': 0xDD, '}': 0xDD,
                "'": 0xDE, '"': 0xDE
            }
            vk = OEM_MAP.get(key)
    else:
        SPECIAL = {
            'SPACE': 0x20, 'TAB': 0x09, 'RETURN': 0x0D, 'ENTER': 0x0D, 'ESC': 0x1B, 'ESCAPE': 0x1B,
            'INSERT': 0x2D, 'DELETE': 0x2E, 'HOME': 0x24, 'END': 0x23,
            'PAGEUP': 0x21, 'PAGEDOWN': 0x22, 'UP': 0x26, 'DOWN': 0x28, 'LEFT': 0x25, 'RIGHT': 0x27,
            'BACKSPACE': 0x08, 'PRINTSCREEN': 0x2C, 'PAUSE': 0x13
        }
        vk = SPECIAL.get(key_upper)

    return mod, vk


def validate_hotkeys_dict(hotkeys_dict):
    """
    Validates that no two actions have identical hotkeys.
    Returns: (is_valid: bool, error_message: str or None)
    """
    seen = {}
    for action, raw in hotkeys_dict.items():
        norm = normalize_hotkey_string(raw)
        if not norm:
            continue
        if norm in seen:
            other = seen[norm]
            name1 = ACTION_NAMES.get(other, other)
            name2 = ACTION_NAMES.get(action, action)
            return False, f"Xung đột phím tắt: Tổ hợp '{norm}' bị trùng giữa [{name1}] và [{name2}]. Bắt buộc mỗi chức năng phải có một phím tắt riêng biệt!"
        seen[norm] = action
    return True, None


def load_settings():
    merged = dict(DEFAULT_SETTINGS)
    merged["custom_hotkeys"] = dict(DEFAULT_HOTKEYS)
    _, cfg_file = _resolve_config_file()
    if os.path.exists(cfg_file):
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged.update(data)
                if "custom_hotkeys" in data and isinstance(data["custom_hotkeys"], dict):
                    merged["custom_hotkeys"] = dict(DEFAULT_HOTKEYS)
                    merged["custom_hotkeys"].update(data["custom_hotkeys"])
                return merged
        except Exception:
            pass
    return merged


def save_settings(settings):
    try:
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            target_dir = os.path.join(appdata, "IT Tool LTT", "config")
        else:
            target_dir = CONFIG_DIR
        os.makedirs(target_dir, exist_ok=True)
        target_file = os.path.join(target_dir, "zoom_screen.json")

        merged = load_settings()
        merged.update(settings)
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
        return True
    except Exception as ex:
        print(f"[ZoomScreen] Save error: {ex}")
        return False


def attach_to_input_desktop():
    try:
        user32.SetProcessDPIAware()
        hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        pass


def launch_gui_process(mode='zoom'):
    """Launches the dedicated Zoom Screen GUI as an isolated Python subprocess."""
    try:
        mode = mode.lower()
        attach_to_input_desktop()
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        cx, cy = str(pt.x), str(pt.y)

        if getattr(sys, 'frozen', False):
            # In compiled PyInstaller executable
            cmd = [sys.executable, '--zoom-screen', mode, cx, cy]
        else:
            # In development python script
            script_path = os.path.join(os.path.dirname(__file__), "zoom_screen_gui.py")
            cmd = [sys.executable, script_path, mode, cx, cy]

        proc = subprocess.Popen(cmd)
        return proc
    except Exception as e:
        print(f"[ZoomScreen] Launch GUI error: {e}")
        return None


# ── LiveZoom Engine via Windows Magnification API ──────────────────────────────
class LiveZoomEngine:
    def __init__(self):
        self.is_active = False
        self.current_zoom = 2.0
        self.mag_dll = None
        self._tracking_thread = None
        self._stop_event = threading.Event()
        self._init_api()

    def _init_api(self):
        try:
            self.mag_dll = ctypes.windll.magnification
            self.mag_dll.MagInitialize.restype = c_bool
            self.mag_dll.MagUninitialize.restype = c_bool
            self.mag_dll.MagSetFullscreenTransform.argtypes = [c_float, c_int, c_int]
            self.mag_dll.MagSetFullscreenTransform.restype = c_bool
        except Exception as e:
            print(f"[ZoomScreen] Magnification API: {e}")

    def toggle(self, target_zoom=2.0):
        if self.is_active:
            return self.stop()
        else:
            return self.start(target_zoom)

    def start(self, target_zoom=2.0):
        if not self.mag_dll:
            return {"success": False, "message": "Thư viện Magnification.dll không khả dụng."}

        try:
            user32.SetProcessDPIAware()
            sw = user32.GetSystemMetrics(0)  # SM_CXSCREEN
            sh = user32.GetSystemMetrics(1)  # SM_CYSCREEN

            self.mag_dll.MagInitialize()
            self.current_zoom = max(1.25, min(8.0, float(target_zoom)))

            # Capture initial cursor position immediately
            pt = wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(pt))

            crop_w = sw / self.current_zoom
            crop_h = sh / self.current_zoom
            max_x = max(0.0, sw - crop_w)
            max_y = max(0.0, sh - crop_h)

            # ZoomIt exact proportional tracking formula:
            # Keeps the pixel under the cursor centered/proportional
            x_off = int(max(0.0, min(max_x, pt.x * (self.current_zoom - 1.0) / self.current_zoom)))
            y_off = int(max(0.0, min(max_y, pt.y * (self.current_zoom - 1.0) / self.current_zoom)))

            ok = self.mag_dll.MagSetFullscreenTransform(c_float(self.current_zoom), c_int(x_off), c_int(y_off))
            if ok:
                self.is_active = True
                self._stop_event.clear()
                self._tracking_thread = threading.Thread(
                    target=self._mouse_tracking_loop,
                    args=(sw, sh),
                    name="LiveZoomTracker",
                    daemon=True
                )
                self._tracking_thread.start()
                return {
                    "success": True,
                    "action": "livezoom",
                    "message": f"Đã bật LiveZoom {self.current_zoom:.2f}x theo vị trí con trỏ chuột. Di chuyển chuột để xem, nhấn phím tắt hoặc ESC để tắt."
                }
            return {"success": False, "message": "Không thể áp dụng tỷ lệ LiveZoom."}
        except Exception as ex:
            return {"success": False, "message": f"Lỗi LiveZoom: {str(ex)}"}

    def _mouse_tracking_loop(self, sw, sh):
        last_x, last_y = -1, -1
        last_zoom = -1.0
        pt = wintypes.POINT()

        VK_CONTROL = 0x11
        VK_UP = 0x26
        VK_DOWN = 0x28
        VK_ESCAPE = 0x1B
        last_zoom_change_time = 0.0

        while not self._stop_event.is_set():
            if not self.is_active:
                break
            try:
                # Check for ESC key to quickly exit LiveZoom
                if (user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000) != 0:
                    threading.Thread(target=self.stop, daemon=True).start()
                    break

                # Support Ctrl + Up / Ctrl + Down to adjust zoom level on the fly
                ctrl_down = (user32.GetAsyncKeyState(VK_CONTROL) & 0x8000) != 0
                now = time.time()
                if ctrl_down and (now - last_zoom_change_time > 0.18):
                    if (user32.GetAsyncKeyState(VK_UP) & 0x8000) != 0:
                        self.adjust_zoom(0.25)
                        last_zoom_change_time = now
                    elif (user32.GetAsyncKeyState(VK_DOWN) & 0x8000) != 0:
                        self.adjust_zoom(-0.25)
                        last_zoom_change_time = now

                user32.GetCursorPos(ctypes.byref(pt))
                zoom = self.current_zoom
                crop_w = sw / zoom
                crop_h = sh / zoom
                max_x = max(0.0, sw - crop_w)
                max_y = max(0.0, sh - crop_h)

                # ZoomIt exact proportional tracking formula:
                target_x = int(max(0.0, min(max_x, pt.x * (zoom - 1.0) / zoom)))
                target_y = int(max(0.0, min(max_y, pt.y * (zoom - 1.0) / zoom)))

                if target_x != last_x or target_y != last_y or zoom != last_zoom:
                    self.mag_dll.MagSetFullscreenTransform(c_float(zoom), c_int(target_x), c_int(target_y))
                    last_x, last_y, last_zoom = target_x, target_y, zoom
            except Exception:
                pass
            time.sleep(0.012)  # ~80 FPS smooth tracking loop

    def adjust_zoom(self, delta):
        if not self.is_active:
            return
        self.current_zoom = max(1.25, min(8.0, round(self.current_zoom + delta, 2)))

    def stop(self):
        if not self.mag_dll or not self.is_active:
            return {"success": True, "message": "LiveZoom đang tắt."}

        try:
            self.is_active = False
            self._stop_event.set()
            if self._tracking_thread and self._tracking_thread.is_alive():
                self._tracking_thread.join(timeout=0.3)
            self._tracking_thread = None

            self.mag_dll.MagSetFullscreenTransform(c_float(1.0), 0, 0)
            self.mag_dll.MagUninitialize()
            return {
                "success": True,
                "action": "livezoom",
                "toggled_off": True,
                "message": "Đã tắt LiveZoom, khôi phục màn hình bình thường."
            }
        except Exception as ex:
            return {"success": False, "message": f"Lỗi dừng LiveZoom: {str(ex)}"}



# ── DemoType Automated Typing Engine ───────────────────────────────────────────
from ctypes import wintypes

class _MOUSEINPUT(ctypes.Structure):
    _fields_ = (
        ('dx', wintypes.LONG),
        ('dy', wintypes.LONG),
        ('mouseData', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.c_size_t)
    )

class _KEYBDINPUT(ctypes.Structure):
    _fields_ = (
        ('wVk', wintypes.WORD),
        ('wScan', wintypes.WORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.c_size_t)
    )

class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = (
        ('uMsg', wintypes.DWORD),
        ('wParamL', wintypes.WORD),
        ('wParamH', wintypes.WORD)
    )

class _INPUTunion(ctypes.Union):
    _fields_ = (
        ('mi', _MOUSEINPUT),
        ('ki', _KEYBDINPUT),
        ('hi', _HARDWAREINPUT)
    )

class _INPUT(ctypes.Structure):
    _fields_ = (
        ('type', wintypes.DWORD),
        ('union', _INPUTunion)
    )

def _send_char_unicode(ch):
    if ch == '\r':
        return
    if ch == '\n':
        user32.keybd_event(0x0D, 0, 0, 0)
        time.sleep(0.003)
        user32.keybd_event(0x0D, 0, 0x0002, 0)
        return
    if ch == '\t':
        user32.keybd_event(0x09, 0, 0, 0)
        time.sleep(0.003)
        user32.keybd_event(0x09, 0, 0x0002, 0)
        return

    code = ord(ch)
    # SendInput preserves 16-bit Unicode without 8-bit truncation (handles all Vietnamese characters)
    ki_dn = _KEYBDINPUT(wVk=0, wScan=code, dwFlags=0x0004, time=0, dwExtraInfo=0) # KEYEVENTF_UNICODE
    ki_up = _KEYBDINPUT(wVk=0, wScan=code, dwFlags=0x0004 | 0x0002, time=0, dwExtraInfo=0)
    arr = (_INPUT * 2)(
        _INPUT(type=1, union=_INPUTunion(ki=ki_dn)),
        _INPUT(type=1, union=_INPUTunion(ki=ki_up))
    )
    ret = user32.SendInput(2, arr, ctypes.sizeof(_INPUT))
    if ret != 2:
        user32.keybd_event(0, code & 0xFF, 0x0004, 0)
        time.sleep(0.001)
        user32.keybd_event(0, code & 0xFF, 0x0004 | 0x0002, 0)

class DemoTypeEngine:
    def __init__(self):
        self.is_running = False
        self._stop_event = threading.Event()
        self._thread = None

    def stop(self):
        self.is_running = False
        self._stop_event.set()

    def trigger(self, text=None, speed=55):
        if self.is_running:
            self.stop()
            return {
                "success": True,
                "action": "demotype",
                "toggled_off": True,
                "message": "Đã dừng trình diễn gõ phím DemoType."
            }

        cfg = load_settings()
        default_script = (
            "# Kịch bản mẫu DemoType - IT Tool LTT 2026\n"
            "def welcome_presentation():\n"
            "    print('Xin chào quý vị khán giả!')\n"
            "    print('DemoType tự động gõ mã code chuẩn xác 100%.')\n"
            "\n"
            "welcome_presentation()\n"
        )
        type_text = text or cfg.get("demotype_text") or default_script
        speed_val = speed or cfg.get("demotype_speed", 55)
        # speed 10..100 -> delay 0.12s down to 0.015s
        delay = max(0.015, 0.12 - (float(speed_val) / 100.0 * 0.10))

        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_typing, args=(type_text, delay), daemon=True)
        self._thread.start()
        return {
            "success": True,
            "action": "demotype",
            "message": "DemoType đã kích hoạt! Hãy nhấp chuột vào cửa sổ cần gõ chữ (Notepad, VS Code...) trong 3 giây tới."
        }

    def _run_typing(self, text, delay):
        try:
            hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
            if hdesk:
                user32.SetThreadDesktop(hdesk)
        except Exception:
            pass

        hud = None
        hud_lbl = None
        container = None
        try:
            import tkinter as tk
            hud = tk.Tk()
            hud.overrideredirect(True)
            hud.attributes("-topmost", True)
            sw = user32.GetSystemMetrics(0)
            tw, th = 440, 52
            tx = (sw - tw) // 2
            ty = 24
            hud.geometry(f"{tw}x{th}+{tx}+{ty}")
            hud.configure(bg="#0f172a")

            container = tk.Frame(hud, bg="#0f172a", highlightbackground="#38bdf8", highlightcolor="#38bdf8", highlightthickness=2)
            container.pack(fill="both", expand=True)

            hud_lbl = tk.Label(container, text="⏳ DemoType: Hãy nhấp chuột vào nơi cần gõ chữ... (3s)", font=("Segoe UI", 9, "bold"), bg="#0f172a", fg="#38bdf8")
            hud_lbl.pack(expand=True, fill="both")
            hud.update()
        except Exception:
            hud = None

        try:
            # 3-second visual countdown
            for sec in (3, 2, 1):
                if self._stop_event.is_set():
                    return
                if hud and hud_lbl:
                    try:
                        hud_lbl.config(text=f"⏳ DemoType: Hãy nhấp chuột vào nơi cần gõ chữ... ({sec}s)")
                        hud.update()
                    except Exception:
                        pass
                for _ in range(10):
                    if self._stop_event.is_set() or (user32.GetAsyncKeyState(0x1B) & 0x8000) != 0:
                        return
                    time.sleep(0.1)

            # Beep gently to signal typing start
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_OK)
            except Exception:
                pass

            if hud and hud_lbl and container:
                try:
                    container.config(highlightbackground="#10b981", highlightcolor="#10b981")
                    hud_lbl.config(text="⌨️ DemoType đang gõ tự động... (Nhấn ESC hoặc Ctrl+7 để dừng)", fg="#10b981")
                    hud.update()
                except Exception:
                    pass

            VK_ESCAPE = 0x1B
            for ch in text:
                if self._stop_event.is_set() or not self.is_running:
                    break
                if (user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000) != 0:
                    break

                _send_char_unicode(ch)
                time.sleep(delay)

            if hud and hud_lbl and not self._stop_event.is_set():
                try:
                    hud_lbl.config(text="✅ DemoType đã gõ xong toàn bộ kịch bản!", fg="#f8fafc")
                    hud.update()
                    time.sleep(1.2)
                except Exception:
                    pass
        except Exception as e:
            print(f"[DemoType] Error: {e}")
        finally:
            if hud:
                try:
                    hud.destroy()
                except Exception:
                    pass
            self.is_running = False


# ── Global Hotkeys Listener via RegisterHotKey ─────────────────────────────────
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
WM_USER = 0x0400
WM_RELOAD = WM_USER + 101
WM_PAUSE = WM_USER + 102
WM_RESUME = WM_USER + 103

class GlobalHotkeysListener:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.is_running = False
        self.is_paused = False
        self._thread = None
        self._thread_id = None
        self._ready_event = threading.Event()
        self._ack_event = None
        self.registered_status = {}

    def start(self):
        if self.is_running and self._thread and self._thread.is_alive():
            return
        self.is_running = True
        self.is_paused = False
        self._ready_event.clear()
        self._thread = threading.Thread(target=self._loop, name="ZoomScreenHotkeysListener", daemon=True)
        self._thread.start()
        self._ready_event.wait(timeout=1.0)

    def reload(self):
        """Restarts/updates the hotkey bindings immediately inside the active message thread."""
        if not self.is_running or not self._thread_id or not self._thread or not self._thread.is_alive():
            self.start()
            return
        self._ack_event = threading.Event()
        user32.PostThreadMessageW(self._thread_id, WM_RELOAD, 0, 0)
        self._ack_event.wait(timeout=1.0)
        self._ack_event = None

    def pause(self):
        """Temporarily unregisters hotkeys (e.g. while recording hotkeys in modal)."""
        if not self.is_running or not self._thread_id:
            return {"success": True}
        self._ack_event = threading.Event()
        user32.PostThreadMessageW(self._thread_id, WM_PAUSE, 0, 0)
        self._ack_event.wait(timeout=0.8)
        self._ack_event = None
        return {"success": True}

    def resume(self):
        """Resumes registering hotkeys after modal closes."""
        if not self.is_running or not self._thread_id:
            self.start()
            return {"success": True}
        self._ack_event = threading.Event()
        user32.PostThreadMessageW(self._thread_id, WM_RESUME, 0, 0)
        self._ack_event.wait(timeout=0.8)
        self._ack_event = None
        return {"success": True}

    def stop(self):
        try:
            self.pause()
        except Exception:
            pass
        self.is_running = False
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=0.6)
        self._thread_id = None
        self._thread = None
        self.registered_status.clear()

    def _loop(self):
        self._thread_id = kernel32.GetCurrentThreadId()

        # Initialize thread message queue
        msg = wintypes.MSG()
        user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 0)

        MOD_NOREPEAT = 0x4000
        action_id_map = {}
        registered = []

        def _do_register_all():
            for hid in list(registered):
                try:
                    user32.UnregisterHotKey(None, hid)
                except Exception:
                    pass
            registered.clear()
            action_id_map.clear()
            self.registered_status.clear()

            if self.is_paused:
                return

            cfg = load_settings()
            hotkeys_cfg = cfg.get("custom_hotkeys") or DEFAULT_HOTKEYS
            action_list = ['zoom', 'draw', 'break', 'livezoom', 'record', 'snip', 'demotype', 'panorama', 'mirror']

            for idx, action in enumerate(action_list, start=1):
                hk_str = hotkeys_cfg.get(action) or DEFAULT_HOTKEYS.get(action)
                norm = normalize_hotkey_string(hk_str)
                mod, vk = parse_hotkey_string(norm)

                if mod is not None and vk is not None:
                    ret = user32.RegisterHotKey(None, idx, mod | MOD_NOREPEAT, vk)
                    if not ret:
                        ret = user32.RegisterHotKey(None, idx, mod, vk)

                    if ret:
                        registered.append(idx)
                        action_id_map[idx] = action
                        self.registered_status[action] = {
                            "registered": True,
                            "hotkey": norm,
                            "message": "Đang hoạt động"
                        }
                    else:
                        err = kernel32.GetLastError()
                        msg_txt = "Bị phần mềm khác trong Windows chiếm giữ" if err == 1409 else f"Lỗi Windows #{err}"
                        self.registered_status[action] = {
                            "registered": False,
                            "hotkey": norm,
                            "error": err,
                            "message": msg_txt
                        }
                else:
                    self.registered_status[action] = {
                        "registered": False,
                        "hotkey": norm or "Chưa cấu hình",
                        "message": "Phím tắt không hợp lệ"
                    }

        _do_register_all()
        self._ready_event.set()

        while self.is_running:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret == 0 or ret == -1:
                break
            if msg.message == WM_HOTKEY:
                hid = msg.wParam
                action = action_id_map.get(hid)
                m = get_master()
                if action and not self.is_paused and getattr(m, 'is_active', True):
                    try:
                        self.dispatcher(action)
                    except Exception as e:
                        print(f"[ZoomScreen] Hotkey dispatch error: {e}")
            elif msg.message == WM_RELOAD:
                self.is_paused = False
                _do_register_all()
                if self._ack_event:
                    self._ack_event.set()
            elif msg.message == WM_PAUSE:
                self.is_paused = True
                for hid in list(registered):
                    try:
                        user32.UnregisterHotKey(None, hid)
                    except Exception:
                        pass
                registered.clear()
                action_id_map.clear()
                if self._ack_event:
                    self._ack_event.set()
            elif msg.message == WM_RESUME:
                self.is_paused = False
                _do_register_all()
                if self._ack_event:
                    self._ack_event.set()

            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        for hid in registered:
            try:
                user32.UnregisterHotKey(None, hid)
            except Exception:
                pass
        registered.clear()
        action_id_map.clear()


# ── Master Controller ──────────────────────────────────────────────────────────
class ZoomScreenMaster:
    _instance = None

    def __init__(self):
        self.livezoom = LiveZoomEngine()
        self.demotype = DemoTypeEngine()
        self.current_gui_proc = None
        self.current_gui_action = None
        self.hotkeys = GlobalHotkeysListener(self.trigger_action)
        self.is_active = True
        self.hotkeys.start()

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = ZoomScreenMaster()
        return cls._instance

    def reload_hotkeys(self):
        """Reloads the global hotkeys listener with latest settings."""
        self.hotkeys.reload()

    def pause_hotkeys(self):
        return self.hotkeys.pause()

    def resume_hotkeys(self):
        return self.hotkeys.resume()

    def is_gui_running(self):
        if self.current_gui_proc is not None:
            if self.current_gui_proc.poll() is None:
                return True
            else:
                self.current_gui_proc = None
                self.current_gui_action = None
        return False

    def close_gui(self):
        if self.is_gui_running():
            try:
                self.current_gui_proc.terminate()
                try:
                    self.current_gui_proc.wait(timeout=0.4)
                except subprocess.TimeoutExpired:
                    self.current_gui_proc.kill()
            except Exception as e:
                print(f"[ZoomScreen] Error closing GUI process: {e}")
            self.current_gui_proc = None
            action = self.current_gui_action
            self.current_gui_action = None
            return action
        return None

    def trigger_action(self, action_name):
        action_name = (action_name or '').lower()
        cfg = load_settings()

        names = {
            'zoom': 'Phóng to (Zoom)',
            'livezoom': 'Phóng to tương tác (LiveZoom)',
            'draw': 'Vẽ chú thích (Draw)',
            'break': 'Đồng hồ đếm ngược (Break Timer)',
            'snip': 'Cắt chụp vùng (Snip)',
            'record': 'Ghi/Cắt hình',
            'mirror': 'Chiếu phản chiếu'
        }

        if not self.is_active:
            disp = names.get(action_name, action_name)
            return {
                "success": False,
                "message": f"Zoom Screen ngầm đang TẮT! Vui lòng bấm 'Bật Zoom Screen Ngầm' trước khi sử dụng chức năng '{disp}'."
            }

        # Check if an active GUI process exists
        if self.is_gui_running():
            # If the user triggers the EXACT SAME function (by hotkey or clicking UI button again):
            if self.current_gui_action == action_name:
                self.close_gui()
                disp = names.get(action_name, action_name)
                return {
                    "success": True,
                    "action": action_name,
                    "toggled_off": True,
                    "message": f"Đã tắt {disp} thành công."
                }
            else:
                # If switching from one GUI mode to another, terminate previous first
                self.close_gui()

        if action_name in ['zoom', 'livezoom', 'draw', 'break', 'snip']:
            proc = launch_gui_process(action_name)
            if proc:
                self.current_gui_proc = proc
                self.current_gui_action = action_name
                return {"success": True, "action": action_name, "message": f"Đã kích hoạt {names.get(action_name, action_name)} thành công."}
            return {"success": False, "message": "Không thể khởi động giao diện."}

        elif action_name == 'demotype':
            return self.demotype.trigger(speed=cfg.get("demotype_speed", 55))

        elif action_name == 'record':
            # Snip-based region capture
            if self.is_gui_running() and self.current_gui_action == 'snip':
                self.close_gui()
                return {"success": True, "action": "record", "toggled_off": True, "message": "Đã tắt chế độ chụp/ghi hình."}
            proc = launch_gui_process('snip')
            self.current_gui_proc = proc
            self.current_gui_action = 'snip'
            return {"success": True, "action": "record", "message": "Đã mở chế độ chụp ghi hình màn hình."}

        elif action_name == 'mirror':
            if self.is_gui_running() and self.current_gui_action == 'zoom':
                self.close_gui()
                return {"success": True, "action": "mirror", "toggled_off": True, "message": "Đã tắt chế độ chiếu phản chiếu."}
            proc = launch_gui_process('zoom')
            self.current_gui_proc = proc
            self.current_gui_action = 'zoom'
            return {"success": True, "action": "mirror", "message": "Đã mở chế độ chiếu phản chiếu màn hình."}

        return {"success": False, "message": f"Hành động không xác định: {action_name}"}


# ── Web API Adapters ───────────────────────────────────────────────────────────
_master = None

def get_master():
    global _master
    if _master is None:
        _master = ZoomScreenMaster.get()
    return _master


def get_status():
    m = get_master()
    cfg = load_settings()
    custom_hk = dict(DEFAULT_HOTKEYS)
    custom_hk.update(cfg.get("custom_hotkeys", {}))

    return {
        "running": m.is_active,
        "pid": os.getpid(),
        "binary_found": True,
        "binary_path": "Native Python Engine (100% Thuần Code Độc Lập)",
        "livezoom_active": (m.is_gui_running() and m.current_gui_action == 'livezoom') or m.livezoom.is_active,
        "gui_running": m.is_gui_running(),
        "active_action": m.current_gui_action,
        "custom_hotkeys": custom_hk,
        "hotkey_status": m.hotkeys.registered_status,
        "action_names": ACTION_NAMES,
        "settings": {
            "SliderZoomLevel": zoom_val_to_slider_level(cfg.get("zoom_level", 2.0)),
            "PenWidth": cfg.get("pen_width", 5),
            "PenColor": cfg.get("pen_color", 255),
            "BreakTimeout": cfg.get("break_timeout", 10),
            "BreakOpacity": cfg.get("break_opacity", 100),
            "RecordingFormat": cfg.get("recording_format", 1),
            "AnimnateZoom": 1 if cfg.get("animate_zoom", True) else 0,
            "SmoothImage": 1 if cfg.get("smooth_image", True) else 0,
            "SnapToGrid": 1 if cfg.get("snap_to_grid", True) else 0,
            "BreakShowDesktop": 1 if cfg.get("break_show_desktop", True) else 0,
            "BreakLockWorkstation": 1 if cfg.get("break_lock_workstation", False) else 0,
            "CaptureSystemAudio": 1 if cfg.get("capture_system_audio", True) else 0,
            "CaptureAudio": 1 if cfg.get("capture_audio", False) else 0,
            "NoiseCancellation": 1 if cfg.get("noise_cancellation", True) else 0,
            "RecordAspectRatio": 1 if cfg.get("record_aspect_ratio", False) else 0,
            "WebcamOverlay": 1 if cfg.get("webcam_overlay", False) else 0,
            "WebcamPosition": cfg.get("webcam_position", 3),
            "WebcamSize": cfg.get("webcam_size", 1),
            "WebcamShape": cfg.get("webcam_shape", 0),
            "WebcamBackgroundMode": cfg.get("webcam_background_mode", 0),
            "DemoTypeSpeedSlider": cfg.get("demotype_speed", 55),
            "DemoTypeUserDrivenMode": 1 if cfg.get("demotype_user_mode", False) else 0,
            "DemoTypeText": cfg.get("demotype_text", ""),
            "readable_hotkeys": {
                "ToggleKey_text": custom_hk.get("zoom", "Ctrl + 1"),
                "DrawToggleKey_text": custom_hk.get("draw", "Ctrl + 2"),
                "BreakTimerKey_text": custom_hk.get("break", "Ctrl + 3"),
                "LiveZoomToggleKey_text": custom_hk.get("livezoom", "Ctrl + 4"),
                "RecordToggleKey_text": custom_hk.get("record", "Ctrl + 5"),
                "SnipToggleKey_text": custom_hk.get("snip", "Ctrl + 6"),
                "DemoTypeToggleKey_text": custom_hk.get("demotype", "Ctrl + 7"),
                "SnipPanoramaToggleKey_text": custom_hk.get("panorama", "Ctrl + 8"),
                "MirrorToggleKey_text": custom_hk.get("mirror", "Ctrl + 9")
            }
        }
    }


def start_zoomit(silent=True):
    m = get_master()
    m.is_active = True
    m.hotkeys.start()
    m.resume_hotkeys()
    m.reload_hotkeys()
    return {"success": True, "message": "Đã bật Zoom Screen ngầm thành công. Phím tắt toàn cầu đã sẵn sàng!"}


def stop_zoomit():
    m = get_master()
    m.is_active = False
    m.hotkeys.stop()
    m.livezoom.stop()
    m.close_gui()
    return {"success": True, "message": "Đã tắt chế độ Zoom Screen ngầm. Toàn bộ phím tắt và tính năng đã dừng."}


def trigger_action(action_name):
    m = get_master()
    return m.trigger_action(action_name)


def update_hotkey(action_name, new_hotkey_str):
    """
    Updates hotkey for a specific action after strictly verifying no duplicates exist.
    """
    action_name = (action_name or '').lower()
    if action_name not in ACTION_NAMES:
        return {"success": False, "message": f"Chức năng '{action_name}' không tồn tại!"}

    norm = normalize_hotkey_string(new_hotkey_str)
    if not norm:
        return {"success": False, "message": "Phím tắt không hợp lệ hoặc thiếu phím chính!"}

    mod, vk = parse_hotkey_string(norm)
    if vk is None:
        return {"success": False, "message": f"Không nhận dạng được phím '{new_hotkey_str}'!"}

    cfg = load_settings()
    current_hotkeys = dict(DEFAULT_HOTKEYS)
    current_hotkeys.update(cfg.get("custom_hotkeys", {}))

    # STRICT CHECK: Check for duplicate with any other action
    for other_act, other_hk in current_hotkeys.items():
        if other_act != action_name:
            if normalize_hotkey_string(other_hk) == norm:
                other_name = ACTION_NAMES.get(other_act, other_act)
                return {
                    "success": False,
                    "conflict_action": other_act,
                    "message": f"Phím tắt '{norm}' đã được sử dụng cho [{other_name}]. Bắt buộc các phím tắt không được trùng nhau!"
                }

    current_hotkeys[action_name] = norm
    save_settings({"custom_hotkeys": current_hotkeys})

    # Reload hotkeys immediately in background listener
    m = get_master()
    m.reload_hotkeys()

    act_disp = ACTION_NAMES.get(action_name, action_name)
    status_info = m.hotkeys.registered_status.get(action_name, {})
    if status_info and not status_info.get("registered", False):
        err_msg = status_info.get("message", "Lỗi đăng ký Windows")
        return {
            "success": True,
            "action": action_name,
            "hotkey": norm,
            "warning": True,
            "message": f"Đã lưu phím tắt '{norm}' cho [{act_disp}], nhưng {err_msg}."
        }

    return {
        "success": True,
        "action": action_name,
        "hotkey": norm,
        "message": f"Đã đổi phím tắt cho [{act_disp}] thành '{norm}' thành công!"
    }


def reset_hotkeys_to_default():
    """Resets all hotkeys back to system factory defaults."""
    save_settings({"custom_hotkeys": dict(DEFAULT_HOTKEYS)})
    m = get_master()
    m.reload_hotkeys()
    return {"success": True, "message": "Đã khôi phục toàn bộ phím tắt Zoom Screen về mặc định ban đầu!"}


def pause_hotkeys():
    """Pauses background hotkeys listening temporarily."""
    m = get_master()
    return m.pause_hotkeys()


def resume_hotkeys():
    """Resumes background hotkeys listening."""
    m = get_master()
    return m.resume_hotkeys()


def save_zoomit_settings(settings):
    mapped = {}
    if "SliderZoomLevel" in settings:
        lvl = int(settings["SliderZoomLevel"])
        mapped["zoom_level"] = ZOOM_LEVEL_MAP.get(lvl, 2.0)
    if "PenWidth" in settings:
        mapped["pen_width"] = int(settings["PenWidth"])
    if "PenColor" in settings:
        mapped["pen_color"] = int(settings["PenColor"])
    if "BreakTimeout" in settings:
        mapped["break_timeout"] = int(settings["BreakTimeout"])
    if "BreakOpacity" in settings:
        mapped["break_opacity"] = int(settings["BreakOpacity"])
    if "RecordingFormat" in settings:
        mapped["recording_format"] = int(settings["RecordingFormat"])
    if "AnimnateZoom" in settings:
        mapped["animate_zoom"] = bool(settings["AnimnateZoom"])
    if "SmoothImage" in settings:
        mapped["smooth_image"] = bool(settings["SmoothImage"])
    if "SnapToGrid" in settings:
        mapped["snap_to_grid"] = bool(settings["SnapToGrid"])
    if "BreakShowDesktop" in settings:
        mapped["break_show_desktop"] = bool(settings["BreakShowDesktop"])
    if "BreakLockWorkstation" in settings:
        mapped["break_lock_workstation"] = bool(settings["BreakLockWorkstation"])
    if "DemoTypeSpeedSlider" in settings:
        mapped["demotype_speed"] = int(settings["DemoTypeSpeedSlider"])
    if "DemoTypeUserDrivenMode" in settings:
        mapped["demotype_user_mode"] = bool(settings["DemoTypeUserDrivenMode"])
    if "DemoTypeText" in settings:
        mapped["demotype_text"] = str(settings["DemoTypeText"])
    if "custom_hotkeys" in settings and isinstance(settings["custom_hotkeys"], dict):
        is_valid, err_msg = validate_hotkeys_dict(settings["custom_hotkeys"])
        if not is_valid:
            return {"success": False, "message": err_msg}
        mapped["custom_hotkeys"] = settings["custom_hotkeys"]

    ok = save_settings(mapped)
    if ok:
        m = get_master()
        m.reload_hotkeys()
        return {"success": True, "message": "Đã lưu toàn bộ cấu hình Zoom Screen vào file cấu hình JSON thành công!"}
    return {"success": False, "message": "Không thể lưu cấu hình."}


def open_zoomit_options():
    return {"success": True, "message": "Toàn bộ tùy chọn đã tích hợp trực tiếp trên giao diện của IT Tool LTT."}
