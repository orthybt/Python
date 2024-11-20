# controllers/image_manager.py

import logging
import math
from models.image_state import ImageState
from utils.image_utils import open_image_file
from tkinter import messagebox, filedialog
import os

class ImageManager:
    """
    Handles image loading, transformations, and state management.
    """

    def __init__(self, app):
        self.app = app
        self.images = {}  # Dictionary to hold ImageState objects
        self.active_image_name = None
        logging.info("ImageManager initialized.")

    def get_active_image(self) -> ImageState:
        """
        Retrieves the currently active image.
        """
        return self.images.get(self.active_image_name)

    def toggle_image_visibility(self, image_name: str, filename: str):
        """
        Toggles the visibility of the specified image.
        If the image is not loaded, it loads and shows it.
        If the image is loaded and visible, it hides it.
        If the image is loaded and hidden, it shows it and sets it as active.
        """
        if image_name in self.images:
            image_state = self.images[image_name]
            if image_state.visible:
                # Hide the image
                image_state.visible = False
                logging.info(f"Hid image '{image_name}'.")

                # Update button text to show the image can be hidden
                self.update_button_text(image_name, hide=False)

                # If it was the active image, unset active image or set to another
                if self.active_image_name == image_name:
                    self.active_image_name = None
                    # Optionally, set to another visible image
                    for img_name, img_state in self.images.items():
                        if img_state.visible:
                            self.active_image_name = img_name
                            break
                    self.app.buttons_window.update_active_image_menu()
                    self.app.buttons_window.set_active_image(
                        self.active_image_name if self.active_image_name else "No Images Loaded"
                    )

                # Redraw images
                self.app.image_window.draw_images()
            else:
                # Show the image
                image_state.visible = True
                logging.info(f"Shown image '{image_name}'.")

                # Set as active image
                self.active_image_name = image_name
                self.app.buttons_window.update_active_image_menu()
                self.app.buttons_window.set_active_image(image_name)

                # Ensure image is centered
                self.center_image(image_state)

                # Update button text to indicate the image can be hidden
                self.update_button_text(image_name, hide=True)

                # Redraw images
                self.app.image_window.draw_images()

                # Ensure image window is visible
                if not self.app.image_window.is_visible:
                    self.toggle_image_window()
        else:
            # Load the image and show it
            self.load_default_image(image_name, filename)
            logging.info(f"Loaded and shown image '{image_name}'.")

    def update_button_text(self, image_name: str, hide: bool):
        """
        Updates the text of the image button based on visibility.
        If hide is True, set text to "Hide <ImageName>"
        If hide is False, set text to "<ImageName>"
        """
        button = self.app.buttons_window.image_buttons.get(image_name)
        if button:
            new_text = f"Hide {image_name}" if hide else f"{image_name}"
            button.config(text=new_text)
            logging.info(f"Updated button text for '{image_name}' to '{new_text}'.")

    def load_default_image(self, image_name: str, filename: str):
        """
        Loads a default image from the Images folder, centers it on the canvas,
        sets it as visible, and makes it the active image.
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_dir = os.path.join(script_dir, '..', 'Images')  # Adjust relative path as necessary
        filepath = os.path.join(image_dir, filename)

        if os.path.exists(filepath):
            image_original = open_image_file(filepath)
            if image_original:
                # Optionally resize for performance
                scaling_factor = 1.0
                canvas_width, canvas_height = self.get_canvas_size()

                max_width = canvas_width * 0.8  # 80% of canvas width
                max_height = canvas_height * 0.8  # 80% of canvas height

                if image_original.width > max_width or image_original.height > max_height:
                    scaling_factor = min(
                        max_width / image_original.width, max_height / image_original.height
                    )
                    new_size = (
                        int(image_original.width * scaling_factor),
                        int(image_original.height * scaling_factor),
                    )
                    image_original = image_original.resize(new_size, Image.LANCZOS)
                    logging.info(
                        f"Resized default image '{image_name}' to {new_size} for optimal performance."
                    )

                # Create ImageState
                image_state = ImageState(image_original, image_name)
                image_state.visible = True

                # Set image position to center
                image_state.offset_x = canvas_width / 2
                image_state.offset_y = canvas_height / 2

                logging.info(
                    f"Loaded default image '{image_name}' at position ({image_state.offset_x}, {image_state.offset_y})"
                )

                # Add to images dictionary
                self.images[image_name] = image_state
                self.active_image_name = image_name

                # Update UI
                self.app.buttons_window.update_active_image_menu()
                self.app.buttons_window.set_active_image(image_name)

                # Update button text to indicate the image can be hidden
                self.update_button_text(image_name, hide=True)

                # Draw images
                self.app.image_window.draw_images()

                # Ensure image window is visible
                if not self.app.image_window.is_visible:
                    self.toggle_image_window()

                logging.info(f"Default image '{image_name}' loaded and set as active.")
            else:
                logging.error(f"Failed to open the default image: {filepath}")
                messagebox.showerror(
                    "Image Load Error", f"Failed to open the default image:\n{filepath}"
                )
        else:
            logging.warning(f"'{filename}' not found in {image_dir}")
            messagebox.showwarning("Image Not Found", f"'{filename}' not found in {image_dir}")

    def center_image(self, image_state: ImageState):
        """
        Centers the given image on the canvas.
        """
        canvas_width, canvas_height = self.get_canvas_size()
        image_state.offset_x = canvas_width / 2
        image_state.offset_y = canvas_height / 2
        logging.info(
            f"Centered image '{image_state.name}' at ({image_state.offset_x}, {image_state.offset_y})."
        )

    def get_canvas_size(self):
        """
        Retrieves the current size of the canvas.
        """
        self.app.image_window.canvas.update_idletasks()
        canvas_width = self.app.image_window.canvas.winfo_width()
        canvas_height = self.app.image_window.canvas.winfo_height()

        # Fallback to requested size if necessary
        if canvas_width <= 1 and canvas_height <= 1:
            canvas_width = self.app.image_window.canvas.winfo_reqwidth()
            canvas_height = self.app.image_window.canvas.winfo_reqheight()
            logging.warning("Canvas size was not properly initialized. Using requested size.")

        return canvas_width, canvas_height

    def on_image_window_resize(self, event):
        """
        Adjusts the canvas size when the image window is resized and recenters images.
        """
        # Re-center all visible images based on new window size
        new_width = event.width
        new_height = event.height
        for image_state in self.images.values():
            if image_state.visible:
                image_state.offset_x = new_width / 2
                image_state.offset_y = new_height / 2
        self.app.image_window.draw_images()
        logging.info(
            f"Image window resized to ({new_width}x{new_height}). Visible images re-centered."
        )

    def toggle_image_window(self):
        """
        Toggles the visibility of the image window.
        """
        if self.app.image_window.is_visible:
            self.app.image_window.hide_window()
            self.app.buttons_window.btn_hide_show_image.config(text="Show Window")
            logging.info("Image window hidden.")
        else:
            self.app.image_window.show_window()
            self.app.buttons_window.btn_hide_show_image.config(text="Hide Window")
            logging.info("Image window shown.")

    def change_active_image(self, image_name: str):
        """
        Changes the active image to the specified image.
        """
        if image_name in self.images and self.images[image_name].visible:
            self.active_image_name = image_name
            self.app.buttons_window.set_active_image(image_name)
            self.app.image_window.draw_images()
            logging.info(f"Active image changed to '{image_name}'.")
        else:
            logging.warning(
                f"Attempted to set active image to '{image_name}', but it's not visible."
            )
            self.active_image_name = None
            self.app.buttons_window.set_active_image("No Images Loaded")

    def toggle_ruler(self):
        """
        Toggles the visibility of the ruler image.
        """
        if not self.app.image_window.ruler_visible:
            # Load the ruler image if not already loaded
            if "Ruler" not in self.images:
                self.load_default_image("Ruler", "Ruler(medium).svg")  # Ensure this file exists
            else:
                # If already loaded, make it visible
                self.images["Ruler"].visible = True
                self.app.image_window.draw_images()
            self.app.image_window.ruler_visible = True
            self.app.buttons_window.btn_open_ruler.config(text="Hide Ruler")
            # Update the visibility checkbox
            self.app.buttons_window.third_image_visibility_var.set(1)
        else:
            # Hide the ruler
            if "Ruler" in self.images:
                self.images["Ruler"].visible = False
                self.app.image_window.draw_images()
            self.app.image_window.ruler_visible = False
            self.app.buttons_window.btn_open_ruler.config(text="Open Ruler")
            # Update the visibility checkbox
            self.app.buttons_window.third_image_visibility_var.set(0)

    def toggle_transparency(self):
        """
        Toggles the transparency level of the active image.
        """
        active_image = self.get_active_image()
        if not active_image:
            return

        if active_image.image_transparency_level > 0.2:
            active_image.image_transparency_level = 0.2
            self.app.buttons_window.btn_toggle_transparency.config(text="Max Transp")
        else:
            active_image.image_transparency_level = 1.0
            self.app.buttons_window.btn_toggle_transparency.config(text="Min Transp")
        self.app.image_window.draw_images()

    def flip_image_horizontal(self):
        """
        Flips the active image horizontally.
        """
        active_image = self.get_active_image()
        if not active_image:
            return
        active_image.is_flipped_horizontally = not active_image.is_flipped_horizontally
        self.app.image_window.draw_images()

    def flip_image_vertical(self):
        """
        Flips the active image vertically.
        """
        active_image = self.get_active_image()
        if not active_image:
            return
        active_image.is_flipped_vertically = not active_image.is_flipped_vertically
        self.app.image_window.draw_images()

    def toggle_rotation_point_mode(self):
        """
        Toggles the mode for setting the rotation point.
        """
        active_image = self.get_active_image()
        if not active_image:
            return
        if not self.app.image_window.is_rotation_point_mode:
            self.app.image_window.is_rotation_point_mode = True
            self.app.buttons_window.btn_set_rotation_point.config(text="Cancel Rot Pt")
            logging.info("Rotation point mode enabled.")
        else:
            self.app.image_window.is_rotation_point_mode = False
            self.app.buttons_window.btn_set_rotation_point.config(text="Set Rot Pt")
            active_image.rotation_point = None
            self.app.image_window.draw_images()
            logging.info("Rotation point mode disabled and rotation point reset.")

    def zoom_in(self):
        """
        Zooms in the active image.
        """
        active_image = self.get_active_image()
        if not active_image:
            return

        # Adjust scale_log
        active_image.scale_log += 0.1  # Adjust step as needed
        active_image.scale = pow(2, active_image.scale_log)

        # Clamp scale
        active_image.scale = min(active_image.scale, 10.0)  # Max scale
        active_image.scale_log = math.log2(active_image.scale)

        # Redraw images
        self.app.image_window.draw_images()

    def zoom_out(self):
        """
        Zooms out the active image.
        """
        active_image = self.get_active_image()
        if not active_image:
            return

        # Adjust scale_log
        active_image.scale_log -= 0.1  # Adjust step as needed
        active_image.scale = pow(2, active_image.scale_log)

        # Clamp scale
        active_image.scale = max(active_image.scale, 0.1)  # Min scale
        active_image.scale_log = math.log2(active_image.scale)

        # Redraw images
        self.app.image_window.draw_images()

    def fine_zoom_in(self):
        """
        Performs a fine zoom in on the active image.
        """
        active_image = self.get_active_image()
        if not active_image:
            return

        # Adjust scale_log with finer step
        active_image.scale_log += 0.05
        active_image.scale = pow(2, active_image.scale_log)

        # Clamp scale
        active_image.scale = min(active_image.scale, 10.0)  # Max scale
        active_image.scale_log = math.log2(active_image.scale)

        # Redraw images
        self.app.image_window.draw_images()

    def fine_zoom_out(self):
        """
        Performs a fine zoom out on the active image.
        """
        active_image = self.get_active_image()
        if not active_image:
            return

        # Adjust scale_log with finer step
        active_image.scale_log -= 0.05
        active_image.scale = pow(2, active_image.scale_log)

        # Clamp scale
        active_image.scale = max(active_image.scale, 0.1)  # Min scale
        active_image.scale_log = math.log2(active_image.scale)

        # Redraw images
        self.app.image_window.draw_images()

    def on_mouse_move(self, event):
        """
        Handles mouse movement events.
        """
        # Existing mouse move handling code

        # Removed the following line to eliminate undo/redo functionality
        # self.app.buttons_window.update_undo_redo_buttons()

        # Continue with the rest of the mouse move logic
        # Example:
        # self.current_mouse_position = (event.x, event.y)
        # self.app.image_window.update_cursor_position(event.x, event.y)