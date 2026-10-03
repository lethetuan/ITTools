import sys
import time
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
gdi32 = ctypes.windll.gdi32
mag = ctypes.windll.magnification

print("Magnification init:", mag.MagInitialize())

sw = user32.GetSystemMetrics(0)
sh = user32.GetSystemMetrics(1)

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

def _proc(hwnd, msg, wp, lp):
    if msg == 0x0084: # WM_NCHITTEST
        return -1 # HTTRANSPARENT
    elif msg == 0x0002:
        user32.PostQuitMessage(0)
        return 0
    return user32.DefWindowProcW(hwnd, msg, wp, lp)

cb = WNDPROC(_proc)
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

cls_name = "TestLiveZoomHost3"
wcls = WNDCLASSEXW()
wcls.cbSize = ctypes.sizeof(WNDCLASSEXW)
wcls.lpfnWndProc = cb
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

# Do NOT use WS_VISIBLE yet
hwnd_host = user32.CreateWindowExW(
    WS_EX_TOPMOST | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW,
    cls_name, "TestHost", WS_POPUP,
    0, 0, sw, sh, None, None, hinst, None
)

user32.SetLayeredWindowAttributes(hwnd_host, 0, 255, 0x02) # LWA_ALPHA
user32.EnableWindow(hwnd_host, False)

hwnd_mag = user32.CreateWindowExW(
    WS_EX_TRANSPARENT,
    "Magnifier", "TestMag",
    WS_CHILD | WS_VISIBLE | 0x0001,
    0, 0, sw, sh, hwnd_host, None, hinst, None
)

filter_hwnd = (wintypes.HWND * 1)(hwnd_host)
mag.MagSetWindowFilterList(hwnd_mag, 0, 1, filter_hwnd)

class MAGTRANSFORM(ctypes.Structure):
    _fields_ = [('v', ctypes.c_float * 3 * 3)]

zoom = 2.0
matrix = MAGTRANSFORM()
matrix.v[0][0] = zoom
matrix.v[1][1] = zoom
matrix.v[2][2] = 1.0
mag.MagSetWindowTransform(hwnd_mag, ctypes.byref(matrix))

# Initialize source rect to current cursor position before showing!
pt = wintypes.POINT()
user32.GetCursorPos(ctypes.byref(pt))
crop_w = int(sw / zoom)
crop_h = int(sh / zoom)
target_x = max(0, min(sw - crop_w, int(pt.x * (zoom - 1.0) / zoom)))
target_y = max(0, min(sh - crop_h, int(pt.y * (zoom - 1.0) / zoom)))
rc = wintypes.RECT(target_x, target_y, target_x + crop_w, target_y + crop_h)
mag.MagSetWindowSource(hwnd_mag, rc)

user32.InvalidateRect(hwnd_mag, None, True)
user32.ShowWindow(hwnd_host, 5) # SW_SHOW
user32.UpdateWindow(hwnd_host)
user32.RedrawWindow(hwnd_host, None, None, 0x0100 | 0x0080 | 0x0001)
user32.SetCursorPos(pt.x, pt.y)

print(f"Initialized smoothly at cursor ({pt.x}, {pt.y}) target ({target_x}, {target_y})")

start = time.time()
HWND_TOPMOST = wintypes.HWND(-1)
SWP_FLAGS = 0x0002 | 0x0001 | 0x0010
last_x, last_y = target_x, target_y

msg = wintypes.MSG()
while time.time() - start < 3:
    while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))

    user32.GetCursorPos(ctypes.byref(pt))
    tx = max(0, min(sw - crop_w, int(pt.x * (zoom - 1.0) / zoom)))
    ty = max(0, min(sh - crop_h, int(pt.y * (zoom - 1.0) / zoom)))
    if tx != last_x or ty != last_y:
        rc = wintypes.RECT(tx, ty, tx + crop_w, ty + crop_h)
        mag.MagSetWindowSource(hwnd_mag, rc)
        user32.InvalidateRect(hwnd_mag, None, False)
        last_x, last_y = tx, ty

    user32.SetWindowPos(hwnd_host, HWND_TOPMOST, 0, 0, 0, 0, SWP_FLAGS)
    time.sleep(0.012)

user32.DestroyWindow(hwnd_host)
mag.MagUninitialize()
print("Test completed successfully")
