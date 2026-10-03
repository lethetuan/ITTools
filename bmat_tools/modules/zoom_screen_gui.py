"""
════════════════════════════════════════════════════════════════════════════════
 IT Tool LTT 2026 - Native Zoom Screen GUI Engine
 100% Python Implementation (No External Binaries)
 Author: Lê Thế Tuấn | 0352 194 195 | https://lethetuanpc.blogspot.com
════════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import io
import time
import math
import json
import ctypes
from ctypes import wintypes, c_void_p, c_size_t, c_uint
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageEnhance

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

# Configure 64-bit Windows API signatures
kernel32.GlobalAlloc.argtypes = [c_uint, c_size_t]
kernel32.GlobalAlloc.restype = c_void_p
kernel32.GlobalLock.argtypes = [c_void_p]
kernel32.GlobalLock.restype = c_void_p
kernel32.GlobalUnlock.argtypes = [c_void_p]
kernel32.GlobalUnlock.restype = wintypes.BOOL
user32.OpenClipboard.argtypes = [c_void_p]
user32.OpenClipboard.restype = wintypes.BOOL
user32.SetClipboardData.argtypes = [c_uint, c_void_p]
user32.SetClipboardData.restype = c_void_p

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "zoom_screen.json")


def attach_to_input_desktop():
    """Attaches current thread to the active user input desktop and sets DPI awareness."""
    try:
        user32.SetProcessDPIAware()
        hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        pass


def load_config():
    defaults = {
        "zoom_level": 2.0,
        "animate_zoom": True,
        "smooth_image": True,
        "snap_to_grid": True,
        "pen_color": "#ef4444",
        "pen_width": 5,
        "break_timeout": 10,
        "break_opacity": 100,
        "break_show_desktop": True,
        "break_lock_workstation": False,
        "custom_hotkeys": {
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
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults.update(data)
                if "custom_hotkeys" in data and isinstance(data["custom_hotkeys"], dict):
                    defaults["custom_hotkeys"].update(data["custom_hotkeys"])
        except Exception:
            pass
    return defaults


def capture_screen_gdi():
    """Captures the full primary desktop in ~15ms using pure Win32 GDI BitBlt + GetDIBits."""
    user32.SetProcessDPIAware()
    w = user32.GetSystemMetrics(0)  # SM_CXSCREEN
    h = user32.GetSystemMetrics(1)  # SM_CYSCREEN

    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    hbm = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
    old_bm = gdi32.SelectObject(hdc_mem, hbm)

    SRCCOPY = 0x00CC0020
    CAPTUREBLT = 0x40000000
    gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_screen, 0, 0, SRCCOPY | CAPTUREBLT)

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ('biSize', wintypes.DWORD),
            ('biWidth', wintypes.LONG),
            ('biHeight', wintypes.LONG),
            ('biPlanes', wintypes.WORD),
            ('biBitCount', wintypes.WORD),
            ('biCompression', wintypes.DWORD),
            ('biSizeImage', wintypes.DWORD),
            ('biXPelsPerMeter', wintypes.LONG),
            ('biYPelsPerMeter', wintypes.LONG),
            ('biClrUsed', wintypes.DWORD),
            ('biClrImportant', wintypes.DWORD)
        ]

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h  # top-down DIB
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    buf_size = w * h * 4
    buffer = ctypes.create_string_buffer(buf_size)
    gdi32.GetDIBits(hdc_mem, hbm, 0, h, buffer, ctypes.byref(bmi), 0)

    img = Image.frombuffer('RGBA', (w, h), buffer, 'raw', 'BGRA', 0, 1)

    gdi32.SelectObject(hdc_mem, old_bm)
    gdi32.DeleteObject(hbm)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc_screen)

    return img.convert('RGB'), w, h


def copy_image_to_clipboard(pil_img):
    """Puts a PIL Image into Windows Clipboard as CF_DIB."""
    try:
        output = io.BytesIO()
        pil_img.convert('RGB').save(output, 'BMP')
        data = output.getvalue()[14:]  # Skip 14-byte BMP header
        output.close()

        GMEM_MOVEABLE = 0x0002
        CF_DIB = 8

        h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        p_mem = kernel32.GlobalLock(h_mem)
        ctypes.memmove(p_mem, data, len(data))
        kernel32.GlobalUnlock(h_mem)

        if user32.OpenClipboard(None):
            user32.EmptyClipboard()
            user32.SetClipboardData(CF_DIB, h_mem)
            user32.CloseClipboard()
            return True
    except Exception as e:
        print(f"[ZoomScreen] Clipboard error: {e}")
    return False


def key_event_matches_hotkey(e, hotkey_str):
    """Checks if a Tkinter Key event matches a user configured hotkey string."""
    if not hotkey_str:
        return False
    # If the key event itself is just a modifier key being pressed down (Control, Shift, Alt), it is NOT a hotkey combination!
    if e.keysym in ('Control_L', 'Control_R', 'Shift_L', 'Shift_R', 'Alt_L', 'Alt_R', 'Meta_L', 'Meta_R', 'ISO_Level3_Shift'):
        return False
    ctrl = (e.state & 0x0004) != 0
    alt = (e.state & 0x131072) != 0 or (e.state & 0x0008) != 0 or (e.state & 0x0080) != 0
    shift = (e.state & 0x0001) != 0

    parts = []
    if ctrl: parts.append("CTRL")
    if alt: parts.append("ALT")
    if shift: parts.append("SHIFT")

    k = e.keysym
    if k.startswith("KP_"):
        k = k[3:]
    elif k in ('exclam', '1'):
        if ctrl or alt: k = '1'
    elif k in ('at', '2'):
        if ctrl or alt: k = '2'
    elif k in ('numbersign', '3'):
        if ctrl or alt: k = '3'
    elif k in ('dollar', '4'):
        if ctrl or alt: k = '4'
    elif k in ('percent', '5'):
        if ctrl or alt: k = '5'
    elif k in ('asciicircum', '6'):
        if ctrl or alt: k = '6'
    elif k in ('ampersand', '7'):
        if ctrl or alt: k = '7'
    elif k in ('asterisk', '8'):
        if ctrl or alt: k = '8'
    elif k in ('parenleft', '9'):
        if ctrl or alt: k = '9'

    if len(k) == 1:
        k = k.upper()

    parts.append(k.upper())

    target_tokens = set([x.strip().upper() for x in hotkey_str.split('+') if x.strip()])
    pressed_tokens = set(parts)
    return target_tokens == pressed_tokens


# ════════════════════════════════════════════════════════════════════════════════
# 1. ZOOM APPLICATION
# ════════════════════════════════════════════════════════════════════════════════
class ZoomApp:
    def __init__(self, initial_zoom=2.0, init_x=None, init_y=None):
        attach_to_input_desktop()
        self.screenshot, self.sw, self.sh = capture_screen_gdi()
        self.target_zoom = max(1.25, min(8.0, float(initial_zoom)))

        self.cfg = load_config()
        self.animate_zoom = bool(self.cfg.get("animate_zoom", True))
        self.smooth_image = bool(self.cfg.get("smooth_image", True))
        self.snap_to_grid = bool(self.cfg.get("snap_to_grid", True))

        self.zoom_factor = 1.0 if self.animate_zoom else self.target_zoom
        self.is_animating = False

        # Get initial physical cursor position at the exact moment of launch
        if init_x is not None and init_y is not None:
            self.cursor_x = max(0, min(self.sw - 1, int(init_x)))
            self.cursor_y = max(0, min(self.sh - 1, int(init_y)))
        else:
            pt = wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            self.cursor_x = max(0, min(self.sw - 1, pt.x))
            self.cursor_y = max(0, min(self.sh - 1, pt.y))

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.geometry(f"{self.sw}x{self.sh}+0+0")
        self.root.attributes("-topmost", True)
        self.root.config(cursor="cross")

        self.canvas = tk.Canvas(self.root, width=self.sw, height=self.sh, highlightthickness=0, bg='black')
        self.canvas.pack(fill='both', expand=True)

        self.tk_img = None
        self.img_id = None
        self.last_render_time = 0
        self.render_pending = False

        self.cfg = load_config()
        self.hk_zoom = self.cfg.get("custom_hotkeys", {}).get("zoom", "Ctrl + 1")
        self.hk_draw = self.cfg.get("custom_hotkeys", {}).get("draw", "Ctrl + 2")

        # Drawing state & tools
        self.drawing_mode = False  # False = Panning mode, True = Drawing mode
        self.pen_color = parse_pen_color(self.cfg.get("pen_color", "#ef4444"))
        try:
            self.pen_width = max(1, min(50, int(float(self.cfg.get("pen_width", 5)))))
        except Exception:
            self.pen_width = 5

        self.board_mode = 'normal'  # 'normal', 'whiteboard', 'blackboard'
        self.start_x = 0
        self.start_y = 0
        self.current_shape_id = None
        self.current_stroke_items = []
        self.strokes_history = []  # History for Ctrl+Z undo
        self.text_mode = False
        self.text_font_size = 20
        self.tab_pressed = False

        # Bindings
        self.root.bind("<Escape>", lambda e: self.close())
        self.root.bind("<Button-3>", self.on_right_click)      # Right click: toggle draw off, or exit

        # Mouse bindings (including Ctrl/Shift modifiers so drawing shapes works smoothly without conflicts)
        for seq in ("<Button-1>", "<Control-Button-1>", "<Shift-Button-1>", "<Control-Shift-Button-1>"):
            self.root.bind(seq, self.on_mouse_down)
        for seq in ("<B1-Motion>", "<Control-B1-Motion>", "<Shift-B1-Motion>", "<Control-Shift-B1-Motion>"):
            self.root.bind(seq, self.on_mouse_drag)
        for seq in ("<ButtonRelease-1>", "<Control-ButtonRelease-1>", "<Shift-ButtonRelease-1>", "<Control-Shift-ButtonRelease-1>"):
            self.root.bind(seq, self.on_mouse_up)

        self.root.bind("<Motion>", self.on_mouse_move)          # Mouse move: pans when not drawing
        self.root.bind("<MouseWheel>", self.on_mouse_wheel)     # Wheel: zooms when panning, sizes pen when drawing
        self.root.bind("<Up>", self.on_up_key)
        self.root.bind("<Down>", self.on_down_key)

        # Tab key for Circle / Oval drawing
        self.root.bind("<KeyPress-Tab>", self.on_tab_press)
        self.root.bind("<KeyRelease-Tab>", self.on_tab_release)

        # Global Hotkeys / shortcuts
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-Z>", lambda e: self.undo())
        self.root.bind("<Control-c>", lambda e: self.copy_to_clipboard())
        self.root.bind("<Control-C>", lambda e: self.copy_to_clipboard())
        self.root.bind("<Control-s>", lambda e: self.save_to_file())
        self.root.bind("<Control-S>", lambda e: self.save_to_file())

        for evt in ("<Control-Key-1>", "<Control-KeyPress-1>", "<Control-Key-exclam>", "<Control-KP_1>"):
            try:
                self.root.bind(evt, lambda e: self.close())
            except Exception:
                pass

        self.root.bind("<Key>", self.on_key)
        self.render()

        # Smooth intro zoom transition if Animate Zoom is enabled
        if self.animate_zoom and self.target_zoom > 1.05:
            self.root.after(10, lambda: self.start_intro_animation(self.target_zoom))

    def start_intro_animation(self, target):
        self.is_animating = True
        steps = 7
        start = 1.0
        for i in range(1, steps + 1):
            t = i / steps
            ease = 1.0 - (1.0 - t) ** 2  # Ease-out quadratic
            z = start + (target - start) * ease
            delay = i * 14
            self.root.after(delay, lambda val=z, last=(i == steps): self._step_zoom(val, last))

    def _step_zoom(self, val, is_last=False):
        self.zoom_factor = val
        self.render()
        if is_last:
            self.is_animating = False

    def on_up_key(self, e):
        if self.drawing_mode:
            self.pen_width = min(30, self.pen_width + 1)
            self.render_hud()
        else:
            self.adjust_zoom(0.25)

    def on_down_key(self, e):
        if self.drawing_mode:
            self.pen_width = max(1, self.pen_width - 1)
            self.render_hud()
        else:
            self.adjust_zoom(-0.25)

    def on_mouse_wheel(self, e):
        if self.drawing_mode:
            delta = 1 if e.delta > 0 else -1
            self.pen_width = max(1, min(30, self.pen_width + delta))
            self.render_hud()
        else:
            delta = 0.25 if e.delta > 0 else -0.25
            self.adjust_zoom(delta)

    def on_mouse_move(self, e):
        if self.drawing_mode:
            return
        self.cursor_x = max(0, min(self.sw - 1, e.x_root))
        self.cursor_y = max(0, min(self.sh - 1, e.y_root))
        now = time.time()
        if now - self.last_render_time > 0.012:
            self.last_render_time = now
            self.render()
        elif not self.render_pending:
            self.render_pending = True
            self.root.after(14, self._delayed_render)

    def _delayed_render(self):
        self.render_pending = False
        self.render()

    def adjust_zoom(self, delta):
        target = max(1.25, min(8.0, round(self.zoom_factor + delta, 2)))
        if not self.animate_zoom:
            self.zoom_factor = target
            self.render()
            return

        start = self.zoom_factor
        steps = 5
        for i in range(1, steps + 1):
            t = i / steps
            ease = 1.0 - (1.0 - t) ** 2
            z = start + (target - start) * ease
            self.root.after(i * 12, lambda val=z: self._step_zoom(val))

    def render(self):
        if self.drawing_mode:
            return  # Lock current zoomed view while drawing

        crop_w = self.sw / self.zoom_factor
        crop_h = self.sh / self.zoom_factor

        crop_x = self.cursor_x * (self.zoom_factor - 1.0) / self.zoom_factor
        crop_y = self.cursor_y * (self.zoom_factor - 1.0) / self.zoom_factor

        left = max(0.0, min(float(self.sw - crop_w), crop_x))
        top = max(0.0, min(float(self.sh - crop_h), crop_y))
        right = left + crop_w
        bottom = top + crop_h

        cropped = self.screenshot.crop((int(left), int(top), int(right), int(bottom)))
        resample_filter = Image.Resampling.BILINEAR if self.smooth_image else Image.Resampling.NEAREST
        zoomed = cropped.resize((self.sw, self.sh), resample_filter)

        self.tk_img = ImageTk.PhotoImage(zoomed)
        if self.img_id is None:
            self.img_id = self.canvas.create_image(0, 0, image=self.tk_img, anchor="nw", tags="bg_tag")
        else:
            self.canvas.itemconfig(self.img_id, image=self.tk_img)

        self.render_hud()

    def render_hud(self):
        self.canvas.delete("hud_tag")
        if not self.drawing_mode:
            hud = f"🔍 Zoom: {self.zoom_factor:.2f}x | Di chuột: Xem | Cuộn chuột: Phóng to/Thu nhỏ | Kéo chuột trái: VẼ NGAY | Ctrl+C: Copy | {self.hk_zoom} / ESC / Chuột phải: Thoát"
            self.canvas.create_rectangle(self.sw//2 - 470, self.sh - 42, self.sw//2 + 470, self.sh - 12, fill="#0f172a", outline="#38bdf8", width=1.5, tags="hud_tag")
            self.canvas.create_text(self.sw//2, self.sh - 27, text=hud, fill="#f8fafc", font=("Segoe UI", 9, "bold"), tags="hud_tag")
        else:
            color_name = "Tùy chỉnh"
            cur_color = str(self.pen_color).lower()
            for k, v in COLOR_PALETTE.items():
                if str(v).lower() == cur_color:
                    names = {'r': 'Đỏ', 'g': 'Xanh lá', 'b': 'Xanh dương', 'y': 'Vàng', 'o': 'Cam', 'p': 'Hồng', 'w': 'Trắng', 'k': 'Đen'}
                    color_name = names.get(k, k.upper())
                    break
            else:
                if cur_color in ["#ff0000", "#ef4444"]:
                    color_name = "Đỏ"

            hud = f"🎨 Đang Vẽ ({color_name}, {self.pen_width}px) | Shift: Thẳng | Ctrl: Khung | Tab: Tròn | Ctrl+Shift: Mũi tên | T: Chữ | Ctrl+Z: Hoàn tác | Ctrl+C: Copy | Ctrl+S: Lưu | Chuột phải: Quay lại Zoom"
            self.canvas.create_rectangle(self.sw//2 - 530, self.sh - 42, self.sw//2 + 530, self.sh - 12, fill="#0f172a", outline="#f59e0b", width=1.5, tags="hud_tag")
            self.canvas.create_text(self.sw//2, self.sh - 27, text=hud, fill="#f8fafc", font=("Segoe UI", 9, "bold"), tags="hud_tag")

    def on_mouse_down(self, e):
        if not self.drawing_mode:
            # Switch to drawing mode immediately on mouse down!
            self.drawing_mode = True
            self.render_hud()

        if self.text_mode:
            self.show_text_dialog(e.x, e.y)
            return

        self.start_x = e.x
        self.start_y = e.y
        self.current_stroke_items = []
        self.current_shape_id = None

    def on_tab_press(self, e):
        self.tab_pressed = True
        return "break"

    def on_tab_release(self, e):
        self.tab_pressed = False
        return "break"

    def on_mouse_drag(self, e):
        if not self.drawing_mode or self.text_mode:
            return

        shift_pressed = ((e.state & 0x0001) != 0) or ((user32.GetAsyncKeyState(0x10) & 0x8000) != 0)
        ctrl_pressed = ((e.state & 0x0004) != 0) or ((user32.GetAsyncKeyState(0x11) & 0x8000) != 0)
        tab_pressed = getattr(self, 'tab_pressed', False) or ((user32.GetAsyncKeyState(0x09) & 0x8000) != 0)

        cur_x, cur_y = e.x, e.y
        if self.snap_to_grid and (shift_pressed or ctrl_pressed or tab_pressed):
            grid = 10
            cur_x = round(cur_x / grid) * grid
            cur_y = round(cur_y / grid) * grid

        if ctrl_pressed and shift_pressed:
            # Arrow
            if self.current_shape_id:
                self.canvas.delete(self.current_shape_id)
            self.current_shape_id = self.canvas.create_line(
                self.start_x, self.start_y, cur_x, cur_y,
                fill=self.pen_color, width=self.pen_width,
                arrow=tk.LAST, arrowshape=(16, 20, 6), capstyle=tk.ROUND, tags="draw_item"
            )
        elif tab_pressed:
            # Ellipse / Circle
            if self.current_shape_id:
                self.canvas.delete(self.current_shape_id)
            self.current_shape_id = self.canvas.create_oval(
                self.start_x, self.start_y, cur_x, cur_y,
                outline=self.pen_color, width=self.pen_width, tags="draw_item"
            )
        elif shift_pressed:
            # Straight Line
            if self.current_shape_id:
                self.canvas.delete(self.current_shape_id)
            self.current_shape_id = self.canvas.create_line(
                self.start_x, self.start_y, cur_x, cur_y,
                fill=self.pen_color, width=self.pen_width, capstyle=tk.ROUND, tags="draw_item"
            )
        elif ctrl_pressed:
            # Rectangle
            if self.current_shape_id:
                self.canvas.delete(self.current_shape_id)
            self.current_shape_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, cur_x, cur_y,
                outline=self.pen_color, width=self.pen_width, tags="draw_item"
            )
        else:
            # Freehand drawing
            item = self.canvas.create_line(
                self.start_x, self.start_y, e.x, e.y,
                fill=self.pen_color, width=self.pen_width,
                capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True, tags="draw_item"
            )
            self.current_stroke_items.append(item)
            self.start_x = e.x
            self.start_y = e.y

    def on_mouse_up(self, e):
        if not self.drawing_mode or self.text_mode:
            return
        if self.current_shape_id:
            self.strokes_history.append([self.current_shape_id])
            self.current_shape_id = None
        elif self.current_stroke_items:
            self.strokes_history.append(self.current_stroke_items)
            self.current_stroke_items = []

    def on_right_click(self, e):
        if self.drawing_mode:
            # Return to panning mode
            self.drawing_mode = False
            self.render_hud()
        else:
            self.close()

    def undo(self):
        if self.strokes_history:
            items = self.strokes_history.pop()
            for it in items:
                self.canvas.delete(it)

    def set_background(self):
        if self.board_mode == 'whiteboard':
            self.canvas.config(bg='white')
            self.canvas.delete("bg_tag")
        elif self.board_mode == 'blackboard':
            self.canvas.config(bg='#0f172a')
            self.canvas.delete("bg_tag")
        else:
            self.canvas.delete("bg_tag")
            if self.tk_img:
                self.img_id = self.canvas.create_image(0, 0, image=self.tk_img, anchor="nw", tags="bg_tag")
                self.canvas.tag_lower("bg_tag")

    def on_key(self, e):
        if e.keysym == 'Escape':
            self.close()
            return
        if key_event_matches_hotkey(e, self.hk_zoom) or key_event_matches_hotkey(e, self.hk_draw):
            self.close()
            return
        ctrl = (e.state & 0x0004) != 0
        if ctrl and e.keysym in ('1', 'KP_1', 'exclam', '2', 'KP_2', 'at'):
            self.close()
            return
        if self.drawing_mode:
            k = e.char.lower()
            if k in COLOR_PALETTE:
                if k == 'w':
                    self.board_mode = 'normal' if self.board_mode == 'whiteboard' else 'whiteboard'
                    self.set_background()
                elif k == 'k':
                    self.board_mode = 'normal' if self.board_mode == 'blackboard' else 'blackboard'
                    self.set_background()
                else:
                    self.pen_color = COLOR_PALETTE[k]
                self.render_hud()
            elif k == 'e':
                self.canvas.delete("draw_item")
                self.strokes_history.clear()
                self.board_mode = 'normal'
                self.set_background()
                self.render_hud()
            elif k == 't':
                self.text_mode = not self.text_mode
                self.render_hud()

    def show_text_dialog(self, x, y):
        txt_win = tk.Toplevel(self.root)
        txt_win.overrideredirect(True)
        txt_win.geometry(f"300x40+{x}+{y}")
        txt_win.attributes("-topmost", True)
        entry = tk.Entry(txt_win, font=("Segoe UI", 12, "bold"), fg=self.pen_color, bg="#1e293b", insertbackground="white")
        entry.pack(fill='both', expand=True)
        entry.focus_set()

        def commit(e=None):
            val = entry.get()
            if val:
                item = self.canvas.create_text(x, y, text=val, fill=self.pen_color, font=("Segoe UI", self.text_font_size, "bold"), anchor="nw", tags="draw_item")
                self.strokes_history.append([item])
            txt_win.destroy()
            self.text_mode = False

        entry.bind("<Return>", commit)
        entry.bind("<Escape>", lambda e: txt_win.destroy())

    def get_flattened_image(self):
        self.canvas.itemconfigure("hud_tag", state='hidden')
        self.canvas.itemconfigure("toast", state='hidden')
        self.root.update_idletasks()
        self.root.update()
        time.sleep(0.02)
        img, _, _ = capture_screen_gdi()
        self.canvas.itemconfigure("hud_tag", state='normal')
        return img

    def copy_to_clipboard(self):
        img = self.get_flattened_image()
        copy_image_to_clipboard(img)
        self.canvas.delete("toast")
        self.canvas.create_rectangle(self.sw//2 - 160, 40, self.sw//2 + 160, 80, fill="#10b981", outline="white", width=2, tags="toast")
        self.canvas.create_text(self.sw//2, 60, text="✅ Đã sao chép hình vẽ vào Clipboard!", fill="white", font=("Segoe UI", 11, "bold"), tags="toast")
        self.root.after(1500, lambda: self.canvas.delete("toast"))

    def save_to_file(self):
        try:
            pic_dir = os.path.join(os.environ.get("USERPROFILE", ""), "Pictures", "Screenshots")
            os.makedirs(pic_dir, exist_ok=True)
            filename = f"ZoomScreen_{time.strftime('%Y%m%d_%H%M%S')}.png"
            path = os.path.join(pic_dir, filename)
            img = self.get_flattened_image()
            img.save(path)
            self.canvas.delete("toast")
            self.canvas.create_rectangle(self.sw//2 - 200, 40, self.sw//2 + 200, 80, fill="#0284c7", outline="white", width=2, tags="toast")
            self.canvas.create_text(self.sw//2, 60, text=f"💾 Đã lưu: Pictures/Screenshots/{filename}", fill="white", font=("Segoe UI", 10, "bold"), tags="toast")
            self.root.after(2000, lambda: self.canvas.delete("toast"))
        except Exception as e:
            print(f"[ZoomScreen] Save error: {e}")

    def close(self):
        if getattr(self, '_closing', False):
            return
        if self.animate_zoom and self.zoom_factor > 1.05 and not self.drawing_mode:
            self._closing = True
            start = self.zoom_factor
            steps = 4
            for i in range(1, steps + 1):
                t = i / steps
                ease = t * t
                z = start - (start - 1.0) * ease
                self.root.after(i * 10, lambda val=z: self._step_zoom(val))
            self.root.after(steps * 10 + 10, self._do_destroy)
        else:
            self._do_destroy()

    def _do_destroy(self):
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)

    def run(self):
        self.root.mainloop()


# ════════════════════════════════════════════════════════════════════════════════
# 2. DRAW APPLICATION
# ════════════════════════════════════════════════════════════════════════════════
COLOR_PALETTE = {
    'r': "#ef4444",  # Red
    'g': "#22c55e",  # Green
    'b': "#3b82f6",  # Blue
    'y': "#eab308",  # Yellow
    'o': "#f97316",  # Orange
    'p': "#ec4899",  # Pink
    'w': "#ffffff",  # White
    'k': "#0f172a",  # Black / Slate
}


def parse_pen_color(val):
    if isinstance(val, int):
        r = val & 0xFF
        g = (val >> 8) & 0xFF
        b = (val >> 16) & 0xFF
        return f"#{r:02x}{g:02x}{b:02x}"
    if isinstance(val, str):
        val = val.strip()
        if val.startswith("#"):
            return val
        try:
            int_val = int(val)
            r = int_val & 0xFF
            g = (int_val >> 8) & 0xFF
            b = (int_val >> 16) & 0xFF
            return f"#{r:02x}{g:02x}{b:02x}"
        except ValueError:
            return val
    return "#ef4444"


class DrawApp:
    def __init__(self, background_img=None):
        if background_img:
            self.background_img = background_img
            self.sw, self.sh = background_img.size
        else:
            self.background_img, self.sw, self.sh = capture_screen_gdi()

        cfg = load_config()
        self.cfg = cfg
        self.pen_color = parse_pen_color(cfg.get("pen_color", "#ef4444"))
        try:
            self.pen_width = max(1, min(50, int(float(cfg.get("pen_width", 5)))))
        except Exception:
            self.pen_width = 5
        self.hk_draw = cfg.get("custom_hotkeys", {}).get("draw", "Ctrl + 2")
        self.snap_to_grid = bool(cfg.get("snap_to_grid", True))

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.geometry(f"{self.sw}x{self.sh}+0+0")
        self.root.attributes("-topmost", True)
        self.root.config(cursor="cross")

        self.canvas = tk.Canvas(self.root, width=self.sw, height=self.sh, highlightthickness=0, bg='black')
        self.canvas.pack(fill='both', expand=True)

        self.board_mode = 'normal'  # 'normal', 'whiteboard', 'blackboard'
        self.bg_photo = None
        self.set_background()

        self.start_x = 0
        self.start_y = 0
        self.current_shape_id = None
        self.strokes_history = []  # List of list of canvas item IDs for Undo

        self.text_mode = False
        self.text_font_size = 20
        self.tab_pressed = False

        # Bindings
        self.root.bind("<Escape>", self.on_escape)
        self.root.bind("<Button-3>", self.on_escape)  # Right click to exit

        # Mouse bindings with modifiers
        for seq in ("<Button-1>", "<Control-Button-1>", "<Shift-Button-1>", "<Control-Shift-Button-1>"):
            self.root.bind(seq, self.on_mouse_down)
        for seq in ("<B1-Motion>", "<Control-B1-Motion>", "<Shift-B1-Motion>", "<Control-Shift-B1-Motion>"):
            self.root.bind(seq, self.on_mouse_drag)
        for seq in ("<ButtonRelease-1>", "<Control-ButtonRelease-1>", "<Shift-ButtonRelease-1>", "<Control-Shift-ButtonRelease-1>"):
            self.root.bind(seq, self.on_mouse_up)

        self.root.bind("<MouseWheel>", self.on_wheel)

        # Tab key for Circle / Oval drawing
        self.root.bind("<KeyPress-Tab>", self.on_tab_press)
        self.root.bind("<KeyRelease-Tab>", self.on_tab_release)

        # Hotkey bindings to toggle off: Ctrl + 2
        for evt in ("<Control-Key-2>", "<Control-KeyPress-2>", "<Control-Key-at>", "<Control-KP_2>"):
            try:
                self.root.bind(evt, lambda e: self.close())
            except Exception:
                pass

        # Global Key handlers
        self.root.bind("<Key>", self.on_key)
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-Z>", lambda e: self.undo())
        self.root.bind("<Control-c>", lambda e: self.copy_to_clipboard())
        self.root.bind("<Control-C>", lambda e: self.copy_to_clipboard())
        self.root.bind("<Control-s>", lambda e: self.save_to_file())
        self.root.bind("<Control-S>", lambda e: self.save_to_file())

        self.render_hud()

    def set_background(self):
        if self.board_mode == 'whiteboard':
            self.canvas.config(bg='white')
            self.canvas.delete("bg_tag")
        elif self.board_mode == 'blackboard':
            self.canvas.config(bg='#0f172a')
            self.canvas.delete("bg_tag")
        else:
            self.bg_photo = ImageTk.PhotoImage(self.background_img)
            self.canvas.delete("bg_tag")
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw", tags="bg_tag")
            self.canvas.tag_lower("bg_tag")

    def render_hud(self):
        self.canvas.delete("hud_tag")
        color_name = "Tùy chỉnh"
        cur_color = str(self.pen_color).lower()
        for k, v in COLOR_PALETTE.items():
            if str(v).lower() == cur_color:
                names = {'r': 'Đỏ', 'g': 'Xanh lá', 'b': 'Xanh dương', 'y': 'Vàng', 'o': 'Cam', 'p': 'Hồng', 'w': 'Trắng', 'k': 'Đen'}
                color_name = names.get(k, k.upper())
                break
        else:
            if cur_color in ["#ff0000", "#ef4444"]:
                color_name = "Đỏ"

        hud = f"🎨 Màu: {color_name} | Bút: {self.pen_width}px | Shift: Thẳng | Ctrl: Khung | Tab: Tròn | Ctrl+Shift: Mũi tên | W: Bảng trắng | K: Bảng đen | T: Chữ | Ctrl+Z: Hoàn tác | Ctrl+C: Copy | Ctrl+S: Lưu | {self.hk_draw} / ESC: Thoát"
        self.canvas.create_rectangle(15, self.sh - 42, 1070, self.sh - 12, fill="#0f172a", outline="#38bdf8", width=1.5, tags="hud_tag")
        self.canvas.create_text(542, self.sh - 27, text=hud, fill="#f8fafc", font=("Segoe UI", 9, "bold"), tags="hud_tag")

    def on_mouse_down(self, e):
        if self.text_mode:
            self.show_text_dialog(e.x, e.y)
            return

        self.start_x = e.x
        self.start_y = e.y
        self.current_stroke_items = []
        self.current_shape_id = None

    def on_tab_press(self, e):
        self.tab_pressed = True
        return "break"

    def on_tab_release(self, e):
        self.tab_pressed = False
        return "break"

    def on_mouse_drag(self, e):
        if self.text_mode:
            return

        shift_pressed = ((e.state & 0x0001) != 0) or ((user32.GetAsyncKeyState(0x10) & 0x8000) != 0)
        ctrl_pressed = ((e.state & 0x0004) != 0) or ((user32.GetAsyncKeyState(0x11) & 0x8000) != 0)
        tab_pressed = getattr(self, 'tab_pressed', False) or ((user32.GetAsyncKeyState(0x09) & 0x8000) != 0)

        cur_x, cur_y = e.x, e.y
        if self.snap_to_grid and (shift_pressed or ctrl_pressed or tab_pressed):
            grid = 10
            cur_x = round(cur_x / grid) * grid
            cur_y = round(cur_y / grid) * grid

        if ctrl_pressed and shift_pressed:
            # Arrow
            if self.current_shape_id:
                self.canvas.delete(self.current_shape_id)
            self.current_shape_id = self.canvas.create_line(
                self.start_x, self.start_y, cur_x, cur_y,
                fill=self.pen_color, width=self.pen_width,
                arrow=tk.LAST, arrowshape=(16, 20, 6), capstyle=tk.ROUND, tags="draw_item"
            )
        elif tab_pressed:
            # Ellipse / Circle
            if self.current_shape_id:
                self.canvas.delete(self.current_shape_id)
            self.current_shape_id = self.canvas.create_oval(
                self.start_x, self.start_y, cur_x, cur_y,
                outline=self.pen_color, width=self.pen_width, tags="draw_item"
            )
        elif shift_pressed:
            # Straight Line
            if self.current_shape_id:
                self.canvas.delete(self.current_shape_id)
            self.current_shape_id = self.canvas.create_line(
                self.start_x, self.start_y, cur_x, cur_y,
                fill=self.pen_color, width=self.pen_width, capstyle=tk.ROUND, tags="draw_item"
            )
        elif ctrl_pressed:
            # Rectangle
            if self.current_shape_id:
                self.canvas.delete(self.current_shape_id)
            self.current_shape_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, cur_x, cur_y,
                outline=self.pen_color, width=self.pen_width, tags="draw_item"
            )
        else:
            # Freehand drawing
            item = self.canvas.create_line(
                self.start_x, self.start_y, e.x, e.y,
                fill=self.pen_color, width=self.pen_width,
                capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True, tags="draw_item"
            )
            self.current_stroke_items.append(item)
            self.start_x = e.x
            self.start_y = e.y

    def on_mouse_up(self, e):
        if self.text_mode:
            return

        if self.current_shape_id:
            self.strokes_history.append([self.current_shape_id])
            self.current_shape_id = None
        elif hasattr(self, 'current_stroke_items') and self.current_stroke_items:
            self.strokes_history.append(self.current_stroke_items)
            self.current_stroke_items = []

    def on_wheel(self, e):
        delta = 1 if e.delta > 0 else -1
        self.pen_width = max(1, min(30, self.pen_width + delta))
        self.render_hud()

    def on_key(self, e):
        if e.keysym == 'Escape':
            self.close()
            return
        if key_event_matches_hotkey(e, self.hk_draw):
            self.close()
            return
        ctrl = (e.state & 0x0004) != 0
        if ctrl and e.keysym in ('2', 'KP_2', 'at'):
            self.close()
            return
        k = e.char.lower()
        if k in COLOR_PALETTE:
            if k == 'w':
                self.board_mode = 'normal' if self.board_mode == 'whiteboard' else 'whiteboard'
                self.set_background()
            elif k == 'k':
                self.board_mode = 'normal' if self.board_mode == 'blackboard' else 'blackboard'
                self.set_background()
            else:
                self.pen_color = COLOR_PALETTE[k]
            self.render_hud()
        elif k == 'e':
            # Erase all
            self.canvas.delete("draw_item")
            self.strokes_history.clear()
            self.board_mode = 'normal'
            self.set_background()
            self.render_hud()
        elif k == 't':
            # Toggle text mode
            self.text_mode = not self.text_mode
            self.render_hud()

    def show_text_dialog(self, x, y):
        txt_win = tk.Toplevel(self.root)
        txt_win.overrideredirect(True)
        txt_win.geometry(f"300x40+{x}+{y}")
        txt_win.attributes("-topmost", True)
        entry = tk.Entry(txt_win, font=("Segoe UI", 12, "bold"), fg=self.pen_color, bg="#1e293b", insertbackground="white")
        entry.pack(fill='both', expand=True)
        entry.focus_set()

        def commit(e=None):
            val = entry.get()
            if val:
                item = self.canvas.create_text(x, y, text=val, fill=self.pen_color, font=("Segoe UI", self.text_font_size, "bold"), anchor="nw", tags="draw_item")
                self.strokes_history.append([item])
            txt_win.destroy()
            self.text_mode = False

        entry.bind("<Return>", commit)
        entry.bind("<Escape>", lambda e: txt_win.destroy())

    def undo(self):
        if self.strokes_history:
            items = self.strokes_history.pop()
            for it in items:
                self.canvas.delete(it)

    def get_flattened_image(self):
        # Hide HUD and toasts before capture
        self.canvas.itemconfigure("hud_tag", state='hidden')
        self.canvas.itemconfigure("toast", state='hidden')
        self.root.update_idletasks()
        self.root.update()
        time.sleep(0.02)
        img, _, _ = capture_screen_gdi()
        self.canvas.itemconfigure("hud_tag", state='normal')
        return img

    def copy_to_clipboard(self):
        img = self.get_flattened_image()
        copy_image_to_clipboard(img)
        # Toast feedback
        self.canvas.create_rectangle(self.sw//2 - 150, 40, self.sw//2 + 150, 80, fill="#10b981", outline="white", width=2, tags="toast")
        self.canvas.create_text(self.sw//2, 60, text="✅ Đã sao chép hình vẽ vào Clipboard!", fill="white", font=("Segoe UI", 11, "bold"), tags="toast")
        self.root.after(1500, lambda: self.canvas.delete("toast"))

    def save_to_file(self):
        try:
            pic_dir = os.path.join(os.environ.get("USERPROFILE", ""), "Pictures", "Screenshots")
            os.makedirs(pic_dir, exist_ok=True)
            filename = f"ZoomScreen_{time.strftime('%Y%m%d_%H%M%S')}.png"
            path = os.path.join(pic_dir, filename)
            img = self.get_flattened_image()
            img.save(path)
            self.canvas.create_rectangle(self.sw//2 - 200, 40, self.sw//2 + 200, 80, fill="#0284c7", outline="white", width=2, tags="toast")
            self.canvas.create_text(self.sw//2, 60, text=f"💾 Đã lưu: Pictures/Screenshots/{filename}", fill="white", font=("Segoe UI", 10, "bold"), tags="toast")
            self.root.after(2000, lambda: self.canvas.delete("toast"))
        except Exception as e:
            print(f"[ZoomScreen] Save error: {e}")

    def on_escape(self, e=None):
        self.root.destroy()
        sys.exit(0)

    def run(self):
        self.root.mainloop()


# ════════════════════════════════════════════════════════════════════════════════
# 3. BREAK TIMER APPLICATION
# ════════════════════════════════════════════════════════════════════════════════
class BreakTimerApp:
    def __init__(self, minutes=10, opacity=100, lock_workstation=False):
        self.screenshot, self.sw, self.sh = capture_screen_gdi()
        self.remaining_seconds = int(minutes * 60)
        self.lock_workstation = lock_workstation
        self.bg_mode = 'desktop'
        self.show_clock = True

        cfg = load_config()
        self.hk_break = cfg.get("custom_hotkeys", {}).get("break", "Ctrl + 3")

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.geometry(f"{self.sw}x{self.sh}+0+0")
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", max(0.2, min(1.0, float(opacity) / 100.0)))

        self.canvas = tk.Canvas(self.root, width=self.sw, height=self.sh, highlightthickness=0, bg='#0f172a')
        self.canvas.pack(fill='both', expand=True)

        self.bg_photo = ImageTk.PhotoImage(self.screenshot)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw", tags="bg")
        # Scrim
        self.scrim_id = self.canvas.create_rectangle(0, 0, self.sw, self.sh, fill="#0f172a", stipple="gray75", tags="scrim")

        self.root.bind("<Escape>", lambda e: self.close())
        self.root.bind("<Up>", lambda e: self.adjust_time(60))
        self.root.bind("<Down>", lambda e: self.adjust_time(-60))
        self.root.bind("<MouseWheel>", self.on_wheel)
        self.root.bind("<w>", lambda e: self.set_mode('white'))
        self.root.bind("<k>", lambda e: self.set_mode('black'))

        # Hotkey bindings to toggle off: Ctrl + 3
        for evt in ("<Control-Key-3>", "<Control-KeyPress-3>", "<Control-Key-numbersign>", "<Control-KP_3>"):
            try:
                self.root.bind(evt, lambda e: self.close())
            except Exception:
                pass
        self.root.bind("<Key>", self.on_key)

        self.update_clock()
        self.tick()

    def on_key(self, e):
        if e.keysym == 'Escape':
            self.close()
            return
        if key_event_matches_hotkey(e, self.hk_break):
            self.close()
            return
        ctrl = (e.state & 0x0004) != 0
        if ctrl and e.keysym in ('3', 'KP_3', 'numbersign'):
            self.close()

    def set_mode(self, mode):
        self.bg_mode = mode
        if mode == 'white':
            self.canvas.delete("bg")
            self.canvas.config(bg='white')
        else:
            self.canvas.delete("bg")
            self.canvas.config(bg='#0f172a')
        self.update_clock()

    def adjust_time(self, delta):
        self.remaining_seconds = max(10, min(120 * 60, self.remaining_seconds + delta))
        self.update_clock()

    def on_wheel(self, e):
        delta = 60 if e.delta > 0 else -60
        self.adjust_time(delta)

    def tick(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.update_clock()
            self.root.after(1000, self.tick)
        else:
            user32.MessageBeep(0x00000040)
            if self.lock_workstation:
                user32.LockWorkStation()
            self.close()

    def update_clock(self):
        self.canvas.delete("clock_tag")
        mins = self.remaining_seconds // 60
        secs = self.remaining_seconds % 60
        time_str = f"{mins:02d}:{secs:02d}"

        fg = "#f8fafc" if self.bg_mode != 'white' else "#0f172a"
        sub_fg = "#38bdf8" if self.bg_mode != 'white' else "#0284c7"

        cx = self.sw // 2
        cy = self.sh // 2 - 20

        self.canvas.create_text(cx, cy - 90, text="⏱️ THỜI GIAN GIẢI LAO — BREAK TIMER", fill=sub_fg, font=("Segoe UI", 18, "bold"), tags="clock_tag")
        self.canvas.create_text(cx, cy, text=time_str, fill=fg, font=("Segoe UI", 90, "bold"), tags="clock_tag")
        self.canvas.create_text(cx, cy + 95, text=f"Cuộn chuột / Phím Mũi tên: Tăng/Giảm phút  |  W: Nền trắng  |  K: Nền đen  |  {self.hk_break} / ESC: Thoát", fill="#94a3b8", font=("Segoe UI", 11, "normal"), tags="clock_tag")

    def close(self):
        self.root.destroy()
        sys.exit(0)

    def run(self):
        self.root.mainloop()


# ════════════════════════════════════════════════════════════════════════════════
# 4. SNIP APPLICATION
# ════════════════════════════════════════════════════════════════════════════════
class SnipApp:
    def __init__(self):
        self.screenshot, self.sw, self.sh = capture_screen_gdi()
        self.start_x = 0
        self.start_y = 0
        self.is_dragging = False
        self.crop_photo = None

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.geometry(f"{self.sw}x{self.sh}+0+0")
        self.root.attributes("-topmost", True)
        self.root.config(cursor="cross")

        self.canvas = tk.Canvas(self.root, width=self.sw, height=self.sh, highlightthickness=0, bg='black')
        self.canvas.pack(fill='both', expand=True)

        # Màn hình nền hơi tối 1 xíu mượt mà (không dùng stipple rỗ chấm), sáng rõ các cửa sổ
        enhancer = ImageEnhance.Brightness(self.screenshot)
        self.dimmed_img = enhancer.enhance(0.58)
        self.dimmed_photo = ImageTk.PhotoImage(self.dimmed_img)
        self.canvas.create_image(0, 0, image=self.dimmed_photo, anchor="nw")

        # Thanh hướng dẫn phía trên
        hw, hh = 460, 32
        hx = (self.sw - hw) // 2
        hy = 20
        self.canvas.create_rectangle(hx, hy, hx + hw, hy + hh, fill="#0f172a", outline="#38bdf8", width=1, tags="hint_tag")
        self.canvas.create_text(hx + hw // 2, hy + hh // 2,
                                text="✂️ Kéo chuột để chọn vùng chụp ảnh • Phím ESC hoặc Chuột phải để hủy",
                                fill="#f1f5f9", font=("Segoe UI", 9, "bold"), tags="hint_tag")

        self.root.bind("<Escape>", lambda e: self.close())
        self.root.bind("<Button-3>", lambda e: self.close())
        self.root.bind("<Button-1>", self.on_down)
        self.root.bind("<B1-Motion>", self.on_drag)
        self.root.bind("<ButtonRelease-1>", self.on_up)

        # Hotkey bindings to toggle off: Ctrl + 6
        for evt in ("<Control-Key-6>", "<Control-KeyPress-6>", "<Control-Key-asciicircum>", "<Control-KP_6>"):
            try:
                self.root.bind(evt, lambda e: self.close())
            except Exception:
                pass
        self.root.bind("<Key>", self.on_key)

    def on_key(self, e):
        ctrl = (e.state & 0x0004) != 0
        if e.keysym == 'Escape':
            self.close()
        elif ctrl and e.keysym in ('6', 'KP_6', 'asciicircum'):
            self.close()

    def on_down(self, e):
        self.canvas.delete("hint_tag")
        self.start_x = e.x
        self.start_y = e.y
        self.is_dragging = True

    def on_drag(self, e):
        if not self.is_dragging:
            return
        self.canvas.delete("crop_preview")

        rx1 = max(0, min(self.start_x, e.x))
        ry1 = max(0, min(self.start_y, e.y))
        rx2 = min(self.sw, max(self.start_x, e.x))
        ry2 = min(self.sh, max(self.start_y, e.y))
        rw, rh = rx2 - rx1, ry2 - ry1

        if rw > 0 and rh > 0:
            # Vùng được kéo chọn sẽ sáng lên rõ nét (lấy từ ảnh gốc không làm tối)
            crop_img = self.screenshot.crop((rx1, ry1, rx2, ry2))
            self.crop_photo = ImageTk.PhotoImage(crop_img)
            self.canvas.create_image(rx1, ry1, image=self.crop_photo, anchor="nw", tags="crop_preview")

            # Viền dạ quang xanh sáng bao quanh vùng chọn
            self.canvas.create_rectangle(rx1, ry1, rx2, ry2, outline="#0ea5e9", width=2, tags="crop_preview")

            # Nhãn kích thước pixel nổi bật
            badge_txt = f"📐 {rw} × {rh} px"
            bw, bh = 114, 24
            bx = rx1
            by = ry1 - bh - 6 if ry1 >= bh + 8 else ry2 + 6
            if bx + bw > self.sw:
                bx = self.sw - bw - 4
            if by + bh > self.sh:
                by = self.sh - bh - 4

            self.canvas.create_rectangle(bx, by, bx + bw, by + bh, fill="#0f172a", outline="#0ea5e9", width=1, tags="crop_preview")
            self.canvas.create_text(bx + bw // 2, by + bh // 2, text=badge_txt, fill="#38bdf8", font=("Segoe UI", 9, "bold"), tags="crop_preview")

    def on_up(self, e):
        if not self.is_dragging:
            return
        self.is_dragging = False

        rx1 = max(0, min(self.start_x, e.x))
        ry1 = max(0, min(self.start_y, e.y))
        rx2 = min(self.sw, max(self.start_x, e.x))
        ry2 = min(self.sh, max(self.start_y, e.y))
        rw, rh = rx2 - rx1, ry2 - ry1

        if rw > 5 and rh > 5:
            cropped = self.screenshot.crop((rx1, ry1, rx2, ry2))
            copy_image_to_clipboard(cropped)
            self.show_toast_and_exit(rw, rh)
        else:
            self.close()

    def show_toast_and_exit(self, rw, rh):
        # Ẩn overlay toàn màn hình ngay lập tức để desktop trở lại bình thường
        self.root.withdraw()

        # Âm thanh thông báo nhẹ
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_OK)
        except Exception:
            pass

        # Cửa sổ thông báo Toast nổi hiện đại
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)

        tw, th = 390, 68
        tx = (self.sw - tw) // 2
        ty = 36
        toast.geometry(f"{tw}x{th}+{tx}+{ty}")
        toast.configure(bg="#0f172a")

        container = tk.Frame(toast, bg="#0f172a", highlightbackground="#10b981", highlightcolor="#10b981", highlightthickness=2)
        container.pack(fill="both", expand=True)

        icon_lbl = tk.Label(container, text="📸", font=("Segoe UI Emoji", 20), bg="#0f172a", fg="#10b981")
        icon_lbl.pack(side="left", padx=(14, 10))

        txt_frame = tk.Frame(container, bg="#0f172a")
        txt_frame.pack(side="left", fill="both", expand=True, pady=10)

        t1 = tk.Label(txt_frame, text="Đã lưu ảnh chụp vùng vào Clipboard!", font=("Segoe UI", 10, "bold"), bg="#0f172a", fg="#f8fafc", anchor="w")
        t1.pack(anchor="w")

        t2 = tk.Label(txt_frame, text=f"Kích thước: {rw} × {rh} px • Nhấn Ctrl + V để dán ngay", font=("Segoe UI", 9), bg="#0f172a", fg="#94a3b8", anchor="w")
        t2.pack(anchor="w")

        # Bấm chuột vào bất kỳ đâu trên thông báo để đóng ngay lập tức
        for w in (toast, container, icon_lbl, txt_frame, t1, t2):
            w.bind("<Button-1>", lambda e: self.close())

        # Tự động đóng sau 1.6 giây và kết thúc tiến trình
        self.root.after(1600, self.close)

    def close(self):
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)

    def run(self):
        self.root.mainloop()


# ════════════════════════════════════════════════════════════════════════════════
# 5. LIVEZOOM APPLICATION (WC_MAGNIFIER with Real-time Mouse Tracking)
# ════════════════════════════════════════════════════════════════════════════════
class MAGTRANSFORM(ctypes.Structure):
    _fields_ = [('v', (ctypes.c_float * 3) * 3)]


class LiveZoomApp:
    def __init__(self, initial_zoom=2.0, init_x=None, init_y=None):
        attach_to_input_desktop()
        self.target_zoom = max(1.25, min(8.0, float(initial_zoom)))
        self.sw = user32.GetSystemMetrics(0)
        self.sh = user32.GetSystemMetrics(1)
        self.init_x = int(init_x) if init_x is not None else None
        self.init_y = int(init_y) if init_y is not None else None
        self.cfg = load_config()
        self.animate_zoom = bool(self.cfg.get("animate_zoom", True))
        self.zoom = 1.0 if self.animate_zoom else self.target_zoom

        self.mag = ctypes.windll.magnification
        self.mag.MagInitialize.restype = ctypes.c_bool
        self.mag.MagUninitialize.restype = ctypes.c_bool
        self.mag.MagSetWindowTransform.argtypes = [wintypes.HWND, ctypes.POINTER(MAGTRANSFORM)]
        self.mag.MagSetWindowTransform.restype = ctypes.c_bool
        self.mag.MagSetWindowSource.argtypes = [wintypes.HWND, wintypes.RECT]
        self.mag.MagSetWindowSource.restype = ctypes.c_bool
        self.mag.MagSetWindowFilterList.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_int, ctypes.POINTER(wintypes.HWND)]
        self.mag.MagSetWindowFilterList.restype = ctypes.c_bool
        self.mag.MagShowSystemCursor.argtypes = [wintypes.BOOL]
        self.mag.MagShowSystemCursor.restype = ctypes.c_bool

        self.hwnd_host = None
        self.hwnd_mag = None
        self.is_running = False

    def run(self):
        if not self.mag.MagInitialize():
            return

        WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, wintypes.HWND, wintypes.UINT, ctypes.c_size_t, ctypes.c_ssize_t)
        user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, ctypes.c_size_t, ctypes.c_ssize_t]
        user32.DefWindowProcW.restype = ctypes.c_longlong

        user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
        user32.SetWindowPos.restype = wintypes.BOOL

        user32.InvalidateRect.argtypes = [wintypes.HWND, ctypes.c_void_p, wintypes.BOOL]
        user32.InvalidateRect.restype = wintypes.BOOL

        user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.ShowWindow.restype = wintypes.BOOL

        user32.UpdateWindow.argtypes = [wintypes.HWND]
        user32.UpdateWindow.restype = wintypes.BOOL

        user32.RedrawWindow.argtypes = [wintypes.HWND, ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT]
        user32.RedrawWindow.restype = wintypes.BOOL

        user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
        user32.SetCursorPos.restype = wintypes.BOOL

        def _wnd_proc(hwnd, msg, wp, lp):
            if msg == 0x0084:  # WM_NCHITTEST: pass mouse clicks through transparently
                return -1      # HTTRANSPARENT
            elif msg == 0x0010:  # WM_CLOSE
                user32.DestroyWindow(hwnd)
                return 0
            elif msg == 0x0002:  # WM_DESTROY
                user32.PostQuitMessage(0)
                return 0
            return user32.DefWindowProcW(hwnd, msg, wp, lp)

        self._proc_cb = WNDPROC(_wnd_proc)
        hinst = kernel32.GetModuleHandleW(None)

        class WNDCLASSEXW(ctypes.Structure):
            _fields_ = [
                ('cbSize', wintypes.UINT),
                ('style', wintypes.UINT),
                ('lpfnWndProc', WNDPROC),
                ('cbClsExtra', ctypes.c_int),
                ('cbWndExtra', ctypes.c_int),
                ('hInstance', wintypes.HINSTANCE),
                ('hIcon', wintypes.HICON),
                ('hCursor', wintypes.HICON),
                ('hbrBackground', wintypes.HBRUSH),
                ('lpszMenuName', wintypes.LPCWSTR),
                ('lpszClassName', wintypes.LPCWSTR),
                ('hIconSm', wintypes.HICON)
            ]

        cls_name = "BMAT_LiveZoomHost"
        wcls = WNDCLASSEXW()
        wcls.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wcls.lpfnWndProc = self._proc_cb
        wcls.hInstance = hinst
        wcls.lpszClassName = cls_name
        wcls.hbrBackground = gdi32.GetStockObject(0)

        user32.RegisterClassExW(ctypes.byref(wcls))

        WS_EX_TOPMOST = 0x00000008
        WS_EX_LAYERED = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020
        WS_EX_TOOLWINDOW = 0x00000080
        WS_POPUP = 0x80000000
        WS_VISIBLE = 0x10000000
        WS_CHILD = 0x40000000

        # Create host window initially hidden so it only shows AFTER viewport is positioned at mouse
        self.hwnd_host = user32.CreateWindowExW(
            WS_EX_TOPMOST | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW,
            cls_name,
            "LiveZoomHostWindow",
            WS_POPUP,
            0, 0, self.sw, self.sh,
            None, None, hinst, None
        )

        user32.SetLayeredWindowAttributes(self.hwnd_host, 0, 255, 0x02)  # LWA_ALPHA
        user32.EnableWindow(self.hwnd_host, False)

        # Child Magnifier window
        self.hwnd_mag = user32.CreateWindowExW(
            WS_EX_TRANSPARENT,
            "Magnifier",
            "LiveZoomMag",
            WS_CHILD | WS_VISIBLE | 0x0001,  # MS_SHOWMAGNIFIEDCURSOR
            0, 0, self.sw, self.sh,
            self.hwnd_host, None, hinst, None
        )

        # Exclude host window so it doesn't magnify itself
        filter_hwnd = (wintypes.HWND * 1)(self.hwnd_host)
        self.mag.MagSetWindowFilterList(self.hwnd_mag, 0, 1, filter_hwnd)

        # 1. Reveal and update host window FIRST so the magnifier control surface is fully realized by DWM
        user32.ShowWindow(self.hwnd_host, 5)  # SW_SHOW
        user32.UpdateWindow(self.hwnd_host)
        user32.RedrawWindow(self.hwnd_host, None, None, 0x0100 | 0x0080 | 0x0001)  # RDW_UPDATENOW | RDW_ALLCHILDREN | RDW_INVALIDATE

        # 2. Get accurate cursor position immediately
        pt = wintypes.POINT()
        if self.init_x is not None and self.init_y is not None:
            pt.x, pt.y = self.init_x, self.init_y
        else:
            user32.GetCursorPos(ctypes.byref(pt))

        # 3. Smooth zoom animation if Animate Zoom is enabled
        if self.animate_zoom and self.zoom < self.target_zoom:
            steps = 6
            for i in range(1, steps + 1):
                t = i / steps
                ease = 1.0 - (1.0 - t) ** 2
                self.zoom = 1.0 + (self.target_zoom - 1.0) * ease
                self.apply_transform()
                crop_w = int(self.sw / self.zoom)
                crop_h = int(self.sh / self.zoom)
                target_x = max(0, min(self.sw - crop_w, int(pt.x * (self.zoom - 1.0) / self.zoom)))
                target_y = max(0, min(self.sh - crop_h, int(pt.y * (self.zoom - 1.0) / self.zoom)))
                rc = wintypes.RECT(target_x, target_y, target_x + crop_w, target_y + crop_h)
                self.mag.MagSetWindowSource(self.hwnd_mag, rc)
                user32.InvalidateRect(self.hwnd_mag, None, False)
                time.sleep(0.012)
        else:
            self.zoom = self.target_zoom
            self.apply_transform()
            crop_w = int(self.sw / self.zoom)
            crop_h = int(self.sh / self.zoom)
            target_x = max(0, min(self.sw - crop_w, int(pt.x * (self.zoom - 1.0) / self.zoom)))
            target_y = max(0, min(self.sh - crop_h, int(pt.y * (self.zoom - 1.0) / self.zoom)))
            rc = wintypes.RECT(target_x, target_y, target_x + crop_w, target_y + crop_h)
            self.mag.MagSetWindowSource(self.hwnd_mag, rc)
            user32.InvalidateRect(self.hwnd_mag, None, False)

        # Initialize last_x, last_y to -9999 so the tracking loop immediately reinforces the position from frame 1
        last_x, last_y = -9999, -9999

        # 4. Hide unmagnified hardware system cursor so ONLY the sharp magnified cursor is visible
        try:
            self.mag.MagShowSystemCursor(False)
        except Exception:
            pass

        self.is_running = True
        msg = wintypes.MSG()
        last_zoom_change = 0.0

        VK_CONTROL = 0x11
        VK_UP = 0x26
        VK_DOWN = 0x28
        VK_ESCAPE = 0x1B
        HWND_TOPMOST = wintypes.HWND(-1)
        SWP_FLAGS = 0x0002 | 0x0001 | 0x0010  # SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE

        try:
            while self.is_running:
                # Process window messages
                while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                    if msg.message == 0x0012:  # WM_QUIT
                        self.is_running = False
                        break
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))

                if not self.is_running:
                    break

                # 1. ESC key to exit (smooth zoom-out if animate_zoom is active)
                if (user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000) != 0:
                    if self.animate_zoom and self.zoom > 1.05:
                        start_z = self.zoom
                        steps = 4
                        for i in range(1, steps + 1):
                            t = i / steps
                            self.zoom = start_z - (start_z - 1.0) * (t * t)
                            self.apply_transform()
                            time.sleep(0.010)
                    break

                # 2. Ctrl + Up / Ctrl + Down to adjust zoom level smoothly
                ctrl_down = (user32.GetAsyncKeyState(VK_CONTROL) & 0x8000) != 0
                now = time.time()
                if ctrl_down and (now - last_zoom_change > 0.18):
                    user32.GetCursorPos(ctypes.byref(pt))
                    if (user32.GetAsyncKeyState(VK_UP) & 0x8000) != 0:
                        new_target = min(8.0, round(self.zoom + 0.25, 2))
                        if self.animate_zoom:
                            self.smooth_step_to(new_target, pt)
                        else:
                            self.zoom = new_target
                            self.apply_transform()
                        last_zoom_change = now
                    elif (user32.GetAsyncKeyState(VK_DOWN) & 0x8000) != 0:
                        new_target = max(1.25, round(self.zoom - 0.25, 2))
                        if self.animate_zoom:
                            self.smooth_step_to(new_target, pt)
                        else:
                            self.zoom = new_target
                            self.apply_transform()
                        last_zoom_change = now

                # 3. Track mouse cursor position and update source rect
                user32.GetCursorPos(ctypes.byref(pt))
                crop_w = int(self.sw / self.zoom)
                crop_h = int(self.sh / self.zoom)
                target_x = max(0, min(self.sw - crop_w, int(pt.x * (self.zoom - 1.0) / self.zoom)))
                target_y = max(0, min(self.sh - crop_h, int(pt.y * (self.zoom - 1.0) / self.zoom)))

                if target_x != last_x or target_y != last_y:
                    rc = wintypes.RECT(target_x, target_y, target_x + crop_w, target_y + crop_h)
                    self.mag.MagSetWindowSource(self.hwnd_mag, rc)
                    user32.InvalidateRect(self.hwnd_mag, None, False)
                    last_x, last_y = target_x, target_y

                # 4. Guarantee hwnd_host is at the very top of Z-order (reclaim topmost like ZoomIt)
                user32.SetWindowPos(self.hwnd_host, HWND_TOPMOST, 0, 0, 0, 0, SWP_FLAGS)

                time.sleep(0.012)  # ~80 FPS smooth tracking loop
        finally:
            self.cleanup()

    def smooth_step_to(self, target_z, pt):
        start_z = self.zoom
        steps = 4
        for i in range(1, steps + 1):
            t = i / steps
            ease = 1.0 - (1.0 - t) ** 2
            self.zoom = start_z + (target_z - start_z) * ease
            self.apply_transform()
            crop_w = int(self.sw / self.zoom)
            crop_h = int(self.sh / self.zoom)
            target_x = max(0, min(self.sw - crop_w, int(pt.x * (self.zoom - 1.0) / self.zoom)))
            target_y = max(0, min(self.sh - crop_h, int(pt.y * (self.zoom - 1.0) / self.zoom)))
            rc = wintypes.RECT(target_x, target_y, target_x + crop_w, target_y + crop_h)
            self.mag.MagSetWindowSource(self.hwnd_mag, rc)
            user32.InvalidateRect(self.hwnd_mag, None, False)
            time.sleep(0.010)
        self.zoom = target_z

    def apply_transform(self):
        if not self.hwnd_mag:
            return
        matrix = MAGTRANSFORM()
        matrix.v[0][0] = self.zoom
        matrix.v[1][1] = self.zoom
        matrix.v[2][2] = 1.0
        self.mag.MagSetWindowTransform(self.hwnd_mag, ctypes.byref(matrix))

    def cleanup(self):
        try:
            self.mag.MagShowSystemCursor(True)
        except Exception:
            pass
        if self.hwnd_host:
            try:
                user32.DestroyWindow(self.hwnd_host)
            except Exception:
                pass
            self.hwnd_host = None
        try:
            self.mag.MagUninitialize()
        except Exception:
            pass


# ════════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════════
def main(mode='zoom', cx=None, cy=None):
    attach_to_input_desktop()
    cfg = load_config()
    mode = mode.lower()

    init_x = int(cx) if cx is not None and str(cx).lstrip('-').isdigit() else None
    init_y = int(cy) if cy is not None and str(cy).lstrip('-').isdigit() else None

    if mode == 'zoom':
        app = ZoomApp(initial_zoom=cfg.get("zoom_level", 2.0), init_x=init_x, init_y=init_y)
        app.run()
    elif mode == 'livezoom':
        app = LiveZoomApp(initial_zoom=cfg.get("zoom_level", 2.0), init_x=init_x, init_y=init_y)
        app.run()
    elif mode == 'draw':
        app = DrawApp()
        app.run()
    elif mode == 'break':
        app = BreakTimerApp(
            minutes=cfg.get("break_timeout", 10),
            opacity=cfg.get("break_opacity", 100),
            lock_workstation=cfg.get("break_lock_workstation", False)
        )
        app.run()
    elif mode == 'snip':
        app = SnipApp()
        app.run()
    else:
        app = ZoomApp(initial_zoom=cfg.get("zoom_level", 2.0), init_x=init_x, init_y=init_y)
        app.run()


if __name__ == '__main__':
    target_mode = sys.argv[1] if len(sys.argv) > 1 else 'zoom'
    c_x = sys.argv[2] if len(sys.argv) > 2 else None
    c_y = sys.argv[3] if len(sys.argv) > 3 else None
    main(target_mode, c_x, c_y)

