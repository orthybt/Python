# views/image_window.py

import tkinter as tk
from PIL import ImageTk, Image
import logging
import sys

# Import ctypes only if on Windows
if sys.platform.startswith('win'):
    import ctypes
    from ctypes import wintypes

class ImageWindow:
    """
    Represents the window displaying images.
    """
    def __init__(self, app):
        self.app = app
        self.image_window = tk.Toplevel(app.root)
        self.image_window.title("Image Window")
        self.is_visible = True
        self.ruler_visible = False
        self.is_rotation_point_mode = False

        # Get screen dimensions
        screen_width = self.image_window.winfo_screenwidth()
        screen_height = self.image_window.winfo_screenheight()

        # Set the window to match screen size
        self.image_window.geometry(f"{screen_width}x{screen_height}+0+0")

        # Allow window resizing
        self.image_window.resizable(True, True)

        # Remove window decorations and make background transparent
        self.image_window.overrideredirect(True)
        self.image_window.attributes('-transparentcolor', 'grey')

        # Make the window always on top
        self.image_window.attributes('-topmost', True)

        # Handle window close event
        self.image_window.protocol("WM_DELETE_WINDOW", self.app.on_close)

        # Create the canvas with grey background
        self.canvas = tk.Canvas(self.image_window, bg='grey', highlightthickness=0, borderwidth=0)
        self.canvas.pack(fill='both', expand=True)

        # Bind mouse events
        self.bind_events()

        # Update canvas size on window resize
        self.image_window.bind('<Configure>', self.on_image_window_resize)

        logging.info("Image window initialized and configured.")

    def bind_events(self):
        """
        Binds mouse and keyboard events to the canvas.
        """
        self.canvas.bind("<ButtonPress-1>", self.app.image_manager.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.app.image_manager.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.app.image_manager.on_mouse_up)
        self.canvas.bind("<ButtonRelease-1>", self.app.image_manager.on_canvas_click)
        self.canvas.bind("<Button-3>", self.app.image_manager.on_right_click)

        # Mouse wheel support across platforms
        if sys.platform.startswith('win') or sys.platform == 'darwin':
            self.canvas.bind("<MouseWheel>", self.app.image_manager.on_mouse_wheel)
        else:
            # For Linux systems
            self.canvas.bind("<Button-4>", lambda event: self.app.image_manager.on_mouse_wheel(event))
            self.canvas.bind("<Button-5>", lambda event: self.app.image_manager.on_mouse_wheel(event))

    def draw_images(self):
        """
        Draws all visible images on the canvas.
        """
        self.canvas.delete("all")  # Clear the canvas
        for image_state in self.app.image_manager.images.values():
            if image_state.visible:
                self.draw_image(image_state)

        # Draw rotation points if any
        for image_state in self.app.image_manager.images.values():
            if image_state.rotation_point and image_state.visible:
                self.show_rotation_point(*image_state.rotation_point)

        self.image_window.update_idletasks()

    def draw_image(self, image_state):
        """
        Applies transformations to an image and draws it on the canvas.
        """
        # Apply transformations
        img = image_state.image_original.copy()

        # Apply transparency
        if image_state.image_transparency_level < 1.0:
            alpha = img.getchannel('A')
            alpha = alpha.point(lambda p: int(p * image_state.image_transparency_level))
            img.putalpha(alpha)

        # Apply flipping
        if image_state.is_flipped_horizontally:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        if image_state.is_flipped_vertically:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)

        # Apply scaling
        img = img.resize(
            (int(img.width * image_state.scale), int(img.height * image_state.scale)),
            Image.LANCZOS
        )

        # Apply rotation around the rotation point if set
        if image_state.rotation_point:
            rotation_center = (
                image_state.rotation_point[0] - (image_state.offset_x - img.width / 2),
                image_state.rotation_point[1] - (image_state.offset_y - img.height / 2)
            )
            img = img.rotate(image_state.angle, expand=True, center=rotation_center)
        else:
            img = img.rotate(image_state.angle, expand=True)

        # Convert to ImageTk.PhotoImage
        photo = ImageTk.PhotoImage(img)
        image_state.photo_image = photo  # Keep a reference to prevent garbage collection

        # Draw the image on the canvas
        self.canvas.create_image(
            image_state.offset_x, image_state.offset_y, image=photo
        )

    def show_rotation_point(self, x, y):
        """
        Displays the rotation point on the canvas.
        """
        radius = 5  # Size of the rotation point marker
        self.canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            fill="red", outline="black", tags="rotation_point"
        )

    def hide_rotation_point(self):
        """
        Hides the rotation point from the canvas.
        """
        self.canvas.delete("rotation_point")

    def on_image_window_resize(self, event):
        """
        Adjusts the canvas size when the image window is resized and recenters images.
        """
        new_width = event.width
        new_height = event.height
        for image_state in self.app.image_manager.images.values():
            image_state.offset_x = new_width / 2
            image_state.offset_y = new_height / 2
        self.draw_images()
        logging.info(f"Image window resized to ({new_width}x{new_height}). Images re-centered.")
