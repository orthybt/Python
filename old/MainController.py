import tkinter as tk
import sys
from mouse_clicker_app import MouseClickerApp
from ImageOverlay import ImageOverlayApp


class MainController:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Main Controller")
        self.root.geometry('300x200')

        # Create buttons to launch each application
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(padx=10, pady=10, fill='both', expand=True)

        btn_mouse_clicker = tk.Button(btn_frame, text="Open Mouse Clicker", command=self.open_mouse_clicker)
        btn_mouse_clicker.pack(pady=10, fill='x')

        btn_image_overlay = tk.Button(btn_frame, text="Open Image Overlay", command=self.open_image_overlay)
        btn_image_overlay.pack(pady=10, fill='x')

        # Store references to the applications
        self.mouse_clicker_app = None
        self.image_overlay_app = None

        # Keep track of whether applications are open
        self.is_mouse_clicker_open = False
        self.is_image_overlay_open = False

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def open_mouse_clicker(self):
        if not self.is_mouse_clicker_open:
            self.mouse_clicker_app = MouseClickerApp(self.root)
            self.is_mouse_clicker_open = True
            self.mouse_clicker_app.root.protocol("WM_DELETE_WINDOW", self.on_mouse_clicker_close)
        else:
            # Bring the window to front
            self.mouse_clicker_app.root.deiconify()
            self.mouse_clicker_app.root.lift()

    def open_image_overlay(self):
        if not self.is_image_overlay_open:
            self.image_overlay_app = ImageOverlayApp(self.root)
            self.is_image_overlay_open = True
            self.image_overlay_app.root.protocol("WM_DELETE_WINDOW", self.on_image_overlay_close)
        else:
            # Bring the window to front
            self.image_overlay_app.root.deiconify()
            self.image_overlay_app.root.lift()

    def on_mouse_clicker_close(self):
        self.is_mouse_clicker_open = False
        self.mouse_clicker_app.root.destroy()

    def on_image_overlay_close(self):
        self.is_image_overlay_open = False
        self.image_overlay_app.root.destroy()

    def on_close(self):
        if self.is_mouse_clicker_open:
            self.mouse_clicker_app.root.destroy()
        if self.is_image_overlay_open:
            self.image_overlay_app.root.destroy()
        self.root.destroy()
        sys.exit(0)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    controller = MainController()
    controller.run()
