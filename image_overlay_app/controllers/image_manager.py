# controllers/image_manager.py

import logging
import math
from models.image_state import ImageState
from PIL import Image
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
        self.app = app
        self.images = {}  # Dictionary to hold ImageState objects
        self.active_image_name = None
        logging.info("ImageManager initialized.")

    def load_image(self, image_path: str):
        """
        Loads an image from the given path and centers it on the canvas.
        """
        image_name = os.path.basename(image_path)
        image_original = open_image_file(image_path)
        if image_original:
            # Optionally resize for performance
            scaling_factor = 1.0
            if image_original.width > 800 or image_original.height > 600:
                scaling_factor = min(800 / image_original.width, 600 / image_original.height)
                new_size = (int(image_original.width * scaling_factor), int(image_original.height * scaling_factor))
                image_original = image_original.resize(new_size, Image.LANCZOS)
                logging.info(f"Resized image to {new_size} for optimal performance.")

            # Create ImageState
            image_state = ImageState(image_original, image_name)

            # Get canvas size
            self.app.image_window.canvas.update_idletasks()  # Ensure the canvas size is updated
            canvas_width = self.app.image_window.canvas.winfo_width()
            canvas_height = self.app.image_window.canvas.winfo_height()

            if canvas_width <= 1 and canvas_height <= 1:
                # Fallback to requested size
                canvas_width = self.app.image_window.canvas.winfo_reqwidth()
                canvas_height = self.app.image_window.canvas.winfo_reqheight()
                logging.warning("Canvas size was not properly initialized. Using requested size.")

            # Set image position to center
            image_state.offset_x = canvas_width / 2
            image_state.offset_y = canvas_height / 2

            logging.info(f"Loaded '{image_name}' at position ({image_state.offset_x}, {image_state.offset_y})")

            # Add to images dictionary
            self.images[image_name] = image_state
            self.active_image_name = image_name
            self.app.buttons_window.update_active_image_menu()
            self.app.buttons_window.set_active_image(image_name)
            self.app.image_window.draw_images()
            if not self.app.image_window.is_visible:
                self.toggle_image_window()
        else:
            logging.error(f"Failed to open the image: {image_path}")
            messagebox.showerror("Image Load Error", f"Failed to open the image:\n{image_path}")
        """
        Loads an image file and creates an ImageState object.
        If filepath is provided, loads the image from that path directly.
        Otherwise, opens a file dialog to select the image.
        """
        if not filepath:
            filepath = filedialog.askopenfilename(
                title=f"Select {image_name}",
                filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.bmp;*.svg")]
            )
        if filepath:
            image_original = open_image_file(filepath)
            if image_original:
                # Optional: Resize if image is too large
                max_dimension = 1920  # Example max width or height
                if image_original.width > max_dimension or image_original.height > max_dimension:
                    scaling_factor = min(max_dimension / image_original.width, max_dimension / image_original.height)
                    new_size = (int(image_original.width * scaling_factor), int(image_original.height * scaling_factor))
                    image_original = image_original.resize(new_size, Image.LANCZOS)
                    logging.info(f"Resized image to {new_size} for optimal performance.")

                # Create ImageState
                image_state = ImageState(image_original, image_name)

                # Get canvas size
                self.app.image_window.canvas.update_idletasks()  # Ensure the canvas size is updated
                canvas_width = self.app.image_window.canvas.winfo_width()
                canvas_height = self.app.image_window.canvas.winfo_height()

                if canvas_width <= 1 and canvas_height <= 1:
                    # Fallback to requested size
                    canvas_width = self.app.image_window.canvas.winfo_reqwidth()
                    canvas_height = self.app.image_window.canvas.winfo_reqheight()
                    logging.warning("Canvas size was not properly initialized. Using requested size.")

                # Set image position to center
                image_state.offset_x = canvas_width / 2
                image_state.offset_y = canvas_height / 2

                logging.info(f"Loaded '{image_name}' at position ({image_state.offset_x}, {image_state.offset_y})")

                # Add to images dictionary
                self.images[image_name] = image_state
                self.active_image_name = image_name
                self.app.buttons_window.update_active_image_menu()
                self.app.buttons_window.set_active_image(image_name)
                self.app.image_window.draw_images()
                if not self.app.image_window.is_visible:
                    self.toggle_image_window()

    def load_default_image(self, image_name: str, filename: str):
        """
        Loads a default image from the Images folder and centers it on the canvas.
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_dir = os.path.join(script_dir, '..', 'Images')  # Adjust relative path as necessary
        filepath = os.path.join(image_dir, filename)

        if os.path.exists(filepath):
            image_original = open_image_file(filepath)
            if image_original:
                # Optionally resize for performance
                scaling_factor = 1.0
                if image_original.width > 800 or image_original.height > 600:
                    scaling_factor = min(800 / image_original.width, 600 / image_original.height)
                    new_size = (int(image_original.width * scaling_factor), int(image_original.height * scaling_factor))
                    image_original = image_original.resize(new_size, Image.LANCZOS)
                    logging.info(f"Resized default image to {new_size} for optimal performance.")

                image_state = ImageState(image_original, image_name)

                # Get canvas size
                self.app.image_window.canvas.update_idletasks()  # Ensure the canvas size is updated
                canvas_width = self.app.image_window.canvas.winfo_width()
                canvas_height = self.app.image_window.canvas.winfo_height()

                if canvas_width <= 1 and canvas_height <= 1:
                    # Fallback to requested size
                    canvas_width = self.app.image_window.canvas.winfo_reqwidth()
                    canvas_height = self.app.image_window.canvas.winfo_reqheight()
                    logging.warning("Canvas size was not properly initialized. Using requested size.")

                # Set image position to center
                image_state.offset_x = canvas_width / 2
                image_state.offset_y = canvas_height / 2

                logging.info(f"Loaded default image '{image_state.name}' at position ({image_state.offset_x}, {image_state.offset_y})")

                # Add to images dictionary
                self.images[image_name] = image_state
                self.app.buttons_window.update_active_image_menu()  # Ensure the dropdown is updated
                self.app.image_window.draw_images()

                if not self.app.image_window.is_visible:
                    self.toggle_image_window()

                logging.info(f"Default image '{image_state.name}' loaded successfully.")

                # Optionally, set the loaded image as active
                self.change_active_image(image_name)
            else:
                logging.error(f"Failed to open the default image: {filepath}")
                messagebox.showerror("Image Load Error", f"Failed to open the default image:\n{filepath}")
        else:
            logging.warning(f"'{filename}' not found in {image_dir}")
            messagebox.showwarning("Image Not Found", f"'{filename}' not found in {image_dir}")

    def on_image_window_resize(self, event):
        """
        Adjusts the canvas size when the image window is resized and recenters images.
        """
        # Re-center all images based on new window size
        new_width = event.width
        new_height = event.height
        for image_state in self.images.values():
            image_state.offset_x = new_width / 2
            image_state.offset_y = new_height / 2
        self.app.image_window.draw_images()
        logging.info(f"Image window resized to ({new_width}x{new_height}). Images re-centered.")
        # This block is redundant and has been removed.

    def toggle_image_window(self):
        """
        Toggles the visibility of the image window.
        """
        if self.app.image_window.is_visible:
            self.app.image_window.image_window.withdraw()
            self.app.image_window.is_visible = False
            if hasattr(self.app.buttons_window, 'btn_hide_show_image'):
                self.app.buttons_window.btn_hide_show_image.config(text="Show Window")
            logging.info("Image window hidden.")
        else:
            self.app.image_window.image_window.deiconify()
            self.app.image_window.is_visible = True
            if hasattr(self.app.buttons_window, 'btn_hide_show_image'):
                self.app.buttons_window.btn_hide_show_image.config(text="Hide Window")
            logging.info("Image window shown.")

    def on_image_window_resize(self, event):
        """
        Adjusts the canvas size when the image window is resized and recenters images.
        """
        # Re-center all images based on new window size
        new_width = event.width
        new_height = event.height
        for image_state in self.images.values():
            image_state.offset_x = new_width / 2
            image_state.offset_y = new_height / 2
        self.app.image_window.draw_images()

    def get_active_image(self) -> ImageState:
        """
        Retrieves the currently active image.
        """
        return self.images.get(self.active_image_name)

    def change_active_image(self, selected_image_name: str):
        """
        Changes the currently active image to the selected image.

        Parameters:
        - selected_image_name (str): The name of the image to activate.
        """
        if selected_image_name in self.images:
            self.active_image_name = selected_image_name
            logging.info(f"Active image changed to '{selected_image_name}'.")
            self.app.image_window.draw_images()  # Redraw images to reflect the active image
        else:
            logging.error(f"Attempted to change to non-existent image '{selected_image_name}'.")
            messagebox.showerror("Image Selection Error", f"The image '{selected_image_name}' does not exist.")

    def toggle_image_visibility(self, image_name: str):
        """
        Toggles the visibility of a specified image.
        """
        image_state = self.images.get(image_name)
        if image_state:
            image_state.visible = not image_state.visible
            self.app.image_window.draw_images()

    def toggle_ruler(self):
        """
        Toggles the visibility of the ruler image.
        """
        if not self.app.image_window.ruler_visible:
            # Load the ruler image if not already loaded
            if "Ruler" not in self.images:
                self.load_default_image("Ruler", "Ruler(medium).svg")  # Ensure this file exists in Images folder
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

        # Record the initial scale for undo
        active_image.position_history.append(active_image.scale_log)
        active_image.redo_stack.clear()
        self.app.buttons_window.update_undo_redo_buttons()

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

        # Record the initial scale for undo
        active_image.position_history.append(active_image.scale_log)
        active_image.redo_stack.clear()
        self.app.buttons_window.update_undo_redo_buttons()

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

        # Record the initial scale for undo
        active_image.position_history.append(active_image.scale_log)
        active_image.redo_stack.clear()
        self.app.buttons_window.update_undo_redo_buttons()

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

        # Record the initial scale for undo
        active_image.position_history.append(active_image.scale_log)
        active_image.redo_stack.clear()
        self.app.buttons_window.update_undo_redo_buttons()

        # Adjust scale_log with finer step
        active_image.scale_log -= 0.05
        active_image.scale = pow(2, active_image.scale_log)

        # Clamp scale
        active_image.scale = max(active_image.scale, 0.1)  # Min scale
        active_image.scale_log = math.log2(active_image.scale)

        # Redraw images
        self.app.image_window.draw_images()

    def on_mouse_wheel(self, event):
        """
        Handles the mouse wheel event for zooming in and out.

        Parameters:
        - event: The Tkinter event object containing event data.
        """
        logging.info(f"Mouse wheel event detected with delta={event.delta}")
        if event.delta > 0:
            self.zoom_in()
        elif event.delta < 0:
            self.zoom_out()

    def undo_move(self):
        """
        Undoes the last move operation.
        """
        active_image = self.get_active_image()
        if active_image and active_image.position_history:
            # Push the current scale_log onto the redo stack
            active_image.redo_stack.append(active_image.scale_log)
            # Pop the last scale_log from the undo stack
            last_scale_log = active_image.position_history.pop()
            active_image.scale_log = last_scale_log
            active_image.scale = pow(2, active_image.scale_log)
            self.app.image_window.draw_images()
            self.update_undo_redo_buttons()
            logging.info(f"Undo performed. New scale_log: {active_image.scale_log}")

    def redo_move(self):
        """
        Redoes the last undone move operation.
        """
        active_image = self.get_active_image()
        if active_image and active_image.redo_stack:
            # Push the current scale_log onto the undo stack
            active_image.position_history.append(active_image.scale_log)
            # Pop the last scale_log from the redo stack
            next_scale_log = active_image.redo_stack.pop()
            active_image.scale_log = next_scale_log
            active_image.scale = pow(2, active_image.scale_log)
            self.app.image_window.draw_images()
            self.update_undo_redo_buttons()
            logging.info(f"Redo performed. New scale_log: {active_image.scale_log}")

    def update_undo_redo_buttons(self):
        """
        Updates the state of the undo and redo buttons.
        """
        active_image = self.get_active_image()
        if active_image:
            self.app.buttons_window.btn_undo_move.config(state='normal' if active_image.position_history else 'disabled')
            self.app.buttons_window.btn_redo_move.config(state='normal' if active_image.redo_stack else 'disabled')
        else:
            self.app.buttons_window.btn_undo_move.config(state='disabled')
            self.app.buttons_window.btn_redo_move.config(state='disabled')

    def on_mouse_down(self, event):
        """
        Handles the mouse down event on the canvas.

        Parameters:
        - event: The Tkinter event object containing event data.
        """
        logging.info(f"Mouse down at ({event.x}, {event.y}) on canvas.")

        # Determine if an image is clicked
        clicked_image = self.get_image_at_position(event.x, event.y)
        if clicked_image:
            self.active_image_name = clicked_image.name
            logging.info(f"Image '{clicked_image.name}' selected.")
            self.app.buttons_window.set_active_image(clicked_image.name)

            # Record the starting position for dragging
            clicked_image.drag_start_x = event.x - clicked_image.offset_x
            clicked_image.drag_start_y = event.y - clicked_image.offset_y
        else:
            logging.info("No image clicked.")

    def get_image_at_position(self, x, y):
        """
        Determines if an image is at the given canvas position.

        Parameters:
        - x (int): The x-coordinate of the mouse event.
        - y (int): The y-coordinate of the mouse event.

        Returns:
        - ImageState or None: The image at the position or None if no image is found.
        """
        for image_state in self.images.values():
            if not image_state.visible:
                continue
            img_width, img_height = image_state.image_original.size
            # Apply scaling
            scaled_width = img_width * image_state.scale
            scaled_height = img_height * image_state.scale
            left = image_state.offset_x - (scaled_width) / 2
            right = image_state.offset_x + (scaled_width) / 2
            top = image_state.offset_y - (scaled_height) / 2
            bottom = image_state.offset_y + (scaled_height) / 2

            if left <= x <= right and top <= y <= bottom:
                return image_state
        return None

    def on_mouse_move(self, event):
        """
        Handles the mouse move event on the canvas.

        Parameters:
        - event: The Tkinter event object containing event data.
        """
        active_image = self.get_active_image()
        if active_image and hasattr(active_image, 'drag_start_x'):
            new_x = event.x - active_image.drag_start_x
            new_y = event.y - active_image.drag_start_y

            # Record the movement for undo functionality
            active_image.position_history.append((active_image.offset_x, active_image.offset_y))
            active_image.redo_stack.clear()
            self.app.buttons_window.update_undo_redo_buttons()

            active_image.offset_x = new_x
            active_image.offset_y = new_y
            self.app.image_window.draw_images()

    def on_mouse_up(self, event):
        """
        Handles the mouse up event on the canvas.

        Parameters:
        - event: The Tkinter event object containing event data.
        """
        active_image = self.get_active_image()
        if active_image and hasattr(active_image, 'drag_start_x'):
            del active_image.drag_start_x
            del active_image.drag_start_y
            self.app.image_window.draw_images()
            logging.info(f"Image '{active_image.name}' moved to ({active_image.offset_x}, {active_image.offset_y}).")

    def on_canvas_click(self, event):
        """
        Handles the canvas click event for setting the rotation point.

        Parameters:
        - event: The Tkinter event object containing event data.
        """
        active_image = self.get_active_image()
        if active_image and self.app.image_window.is_rotation_point_mode:
            # Set the rotation point
            active_image.rotation_point = (event.x, event.y)
            self.app.image_window.is_rotation_point_mode = False
            self.app.buttons_window.btn_set_rotation_point.config(text="Set Rot Pt")
            self.app.image_window.draw_images()
            logging.info(f"Rotation point set at ({event.x}, {event.y}) for image '{active_image.name}'.")

    def on_right_click(self, event):
        """
        Handles the right-click event on the canvas.

        Parameters:
        - event: The Tkinter event object containing event data.
        """
        logging.info(f"Right-click at ({event.x}, {event.y}) on canvas.")

        # Determine if an image is clicked
        clicked_image = self.get_image_at_position(event.x, event.y)
        if clicked_image:
            self.active_image_name = clicked_image.name
            logging.info(f"Image '{clicked_image.name}' right-clicked.")
            self.app.buttons_window.set_active_image(clicked_image.name)

            # Create a context menu
            menu = tk.Menu(self.app.image_window.canvas, tearoff=0)
            menu.add_command(label="Delete Image", command=lambda: self.delete_image(clicked_image.name))
            menu.add_command(label="Properties", command=lambda: self.show_properties(clicked_image))
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
        else:
            logging.info("No image right-clicked.")

    def delete_image(self, image_name: str):
        """
        Deletes the specified image from the application.

        Parameters:
        - image_name (str): The name of the image to delete.
        """
        if image_name in self.images:
            del self.images[image_name]
            logging.info(f"Image '{image_name}' deleted.")
            self.app.buttons_window.update_active_image_menu()
            self.app.image_window.draw_images()
            if self.active_image_name == image_name:
                self.active_image_name = None
                self.app.buttons_window.set_active_image("No Images Loaded")
        else:
            logging.error(f"Attempted to delete non-existent image '{image_name}'.")

    def show_properties(self, image_state: ImageState):
        """
        Displays properties of the specified image.

        Parameters:
        - image_state (ImageState): The image state whose properties are to be displayed.
        """
        properties = (
            f"Name: {image_state.name}\n"
            f"Scale: {image_state.scale:.2f}\n"
            f"Visibility: {'Visible' if image_state.visible else 'Hidden'}\n"
            f"Flipped Horizontally: {'Yes' if image_state.is_flipped_horizontally else 'No'}\n"
            f"Flipped Vertically: {'Yes' if image_state.is_flipped_vertically else 'No'}\n"
            f"Transparency Level: {image_state.image_transparency_level:.2f}"
        )
        messagebox.showinfo("Image Properties", properties)

    def increase_buttons_transparency(self):
        """
        Increases the transparency of the ButtonsWindow (makes it more transparent).
        """
        current_alpha = self.app.buttons_window.transparency_level
        new_alpha = max(0.1, current_alpha - 0.1)  # Decrease alpha (more transparent)
        self.app.buttons_window.transparency_level = new_alpha
        self.app.buttons_window.root.attributes('-alpha', new_alpha)
        logging.info(f"Buttons window transparency increased to {new_alpha:.1f}")

    def decrease_buttons_transparency(self):
        """
        Decreases the transparency of the ButtonsWindow (makes it less transparent).
        """
        current_alpha = self.app.buttons_window.transparency_level
        new_alpha = min(1.0, current_alpha + 0.1)  # Increase alpha (less transparent)
        self.app.buttons_window.transparency_level = new_alpha
        self.app.buttons_window.root.attributes('-alpha', new_alpha)
        logging.info(f"Buttons window transparency decreased to {new_alpha:.1f}")
