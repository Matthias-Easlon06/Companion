import tkinter as tk
import random
import time

# ASCII faces
normal_face = r"""
   (^_^)
"""
blink_face = r"""
   (-_-)
"""
happy_face = r"""
   (^-^)
"""

class DesktopCompanion:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)     # no title bar
        self.root.attributes('-topmost', True)  # always on top
        self.root.config(bg='black')

        # Label for the ASCII face
        self.label = tk.Label(
            root,
            text=normal_face,
            font=('Courier', 14),
            fg='lime',
            bg='black',
            justify='center'
        )
        self.label.pack(padx=10, pady=10)

        # Track dragging
        self.offset_x = 0
        self.offset_y = 0
        self.label.bind("<Button-1>", self.start_drag)
        self.label.bind("<B1-Motion>", self.do_drag)

        # Events
        self.label.bind("<Enter>", self.smile)
        self.label.bind("<Leave>", self.normal)

        # Start blinking
        self.is_blinking = True
        self.blink_loop()

    def start_drag(self, event):
        self.offset_x = event.x
        self.offset_y = event.y

    def do_drag(self, event):
        x = event.x_root - self.offset_x
        y = event.y_root - self.offset_y
        self.root.geometry(f'+{x}+{y}')

    def smile(self, event=None):
        self.label.config(text=happy_face)

    def normal(self, event=None):
        self.label.config(text=normal_face)

    def blink_loop(self):
        # Randomly blink every 3–7 seconds
        self.label.config(text=blink_face)
        self.root.after(200, lambda: self.label.config(text=normal_face))
        next_blink = random.randint(3000, 7000)
        self.root.after(next_blink, self.blink_loop)

def main():
    root = tk.Tk()
    app = DesktopCompanion(root)
    root.mainloop()

if __name__ == "__main__":
    main()
q
