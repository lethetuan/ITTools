import tkinter as tk
import time
from bmat_tools.modules.zoom_screen_gui import capture_screen_gdi, copy_image_to_clipboard

root = tk.Tk()
root.overrideredirect(True)
root.geometry("400x300+100+100")
root.attributes("-topmost", True)

canvas = tk.Canvas(root, width=400, height=300, bg='yellow', highlightthickness=0)
canvas.pack(fill='both', expand=True)

canvas.create_line(10, 10, 390, 290, fill='red', width=5)
canvas.create_text(200, 150, text="TEST DRAWING", font=("Arial", 20, "bold"), fill='blue')
canvas.create_rectangle(50, 20, 350, 60, fill='black', tags="hud_tag")

root.update()
time.sleep(0.1)

# Hide HUD
canvas.itemconfigure("hud_tag", state='hidden')
root.update()

img, w, h = capture_screen_gdi()
crop = img.crop((100, 100, 500, 400))
print("Captured crop size:", crop.size)
copy_image_to_clipboard(crop)
print("Copied to clipboard successfully!")

root.destroy()
