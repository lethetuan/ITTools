import os
import sys
import clr
import ctypes

user32 = ctypes.windll.user32
hDesk = user32.OpenDesktopW('default', 0, False, 0x10000000)
if hDesk:
    user32.SetThreadDesktop(hDesk)

clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')
from System.Windows.Forms import Screen, Form, FormBorderStyle, FormWindowState
from System.Drawing import Bitmap, Graphics, Point, Color

print("Testing Form creation...")
bounds = Screen.PrimaryScreen.Bounds
bmp = Bitmap(bounds.Width, bounds.Height)
g = Graphics.FromImage(bmp)
g.CopyFromScreen(Point(0, 0), Point(0, 0), bounds.Size)
g.Dispose()
print(f"Captured screenshot {bmp.Width}x{bmp.Height}")

class TestForm(Form):
    def __init__(self):
        super().__init__()
        self.FormBorderStyle = getattr(FormBorderStyle, 'None')
        self.Bounds = bounds
        self.TopMost = True
        self.DoubleBuffered = True

form = TestForm()
print("TestForm created successfully, bounds:", form.Bounds.Width, "x", form.Bounds.Height)
form.Dispose()
bmp.Dispose()
print("ALL TESTS PASSED!")
