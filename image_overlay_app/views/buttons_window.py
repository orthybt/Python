# views/buttons_window.py

import tkinter as tk
from tkinter import ttk
import logging

class ButtonsWindow:
    """
    Constructs the main control window with buttons and controls.
    """

    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.transparency_level = 1.0
        self.setup()

    def setup(self):
        """
        Sets up the buttons window.
        """
        self.root.title("Controls")
        self.transparency_level = 1.0
        self.image_window_visible = False

        # Keep the control window on top
        self.root.attributes('-topmost', True)
        self.root.protocol("WM_DELETE_WINDOW", self.app.on_close)

        # Create a frame to organize buttons
        self.btn_frame = tk.Frame(self.root)
        self.btn_frame.pack(padx=10, pady=10, fill='both', expand=True)

        # Initialize all control buttons
        self.create_transparency_controls()
        self.create_image_controls()
        self.create_flip_controls()
        self.create_rotation_point_control()
        self.create_zoom_controls()
        self.create_undo_redo_controls()
        self.create_active_image_control()
        self.create_visibility_controls()
        self.create_ruler_button()
        self.create_load_default_image_buttons()  # New method for default images
        self.create_hide_show_image_window_button()  # New method to create Hide/Show button

        # Configure grid weights for equal button sizes
        for i in range(2):
            self.btn_frame.columnconfigure(i, weight=1)

        # Define third_image_visibility_var for ruler visibility
        self.third_image_visibility_var = tk.IntVar()
        self.third_image_visibility_var.set(0)  # Initially hidden

        # Set the transparency of the buttons window
        self.root.attributes('-alpha', self.transparency_level)

    def create_transparency_controls(self):
        """
        Creates transparency control buttons.
        """
        btn_increase_transparency = tk.Button(
            self.btn_frame, text="Btns Transp+", command=self.app.image_manager.increase_buttons_transparency
        )
        btn_increase_transparency.grid(row=0, column=0, pady=5, sticky='ew')
        logging.info("Created 'Btns Transp+' button.")

        btn_decrease_transparency = tk.Button(
            self.btn_frame, text="Btns Transp-", command=self.app.image_manager.decrease_buttons_transparency
        )
        btn_decrease_transparency.grid(row=0, column=1, pady=5, sticky='ew')
        logging.info("Created 'Btns Transp-' button.")

        # Toggle transparency button
        self.btn_toggle_transparency = tk.Button(
            self.btn_frame, text="Toggle Transp", command=self.app.image_manager.toggle_transparency
        )
        self.btn_toggle_transparency.grid(row=1, column=0, columnspan=2, pady=5, sticky='ew')
        logging.info("Created 'Toggle Transp' button.")

    def create_image_controls(self):
        """
        Creates image loading and window toggling buttons.
        """
        # Existing load image buttons are replaced by load_default_image_buttons
        pass

    def create_flip_controls(self):
        """
        Creates image flip control buttons.
        """
        btn_flip_horizontal = tk.Button(
            self.btn_frame, text="Flip Horizontal", command=self.app.image_manager.flip_image_horizontal
        )
        btn_flip_horizontal.grid(row=2, column=0, pady=5, sticky='ew')
        logging.info("Created 'Flip Horizontal' button.")

        btn_flip_vertical = tk.Button(
            self.btn_frame, text="Flip Vertical", command=self.app.image_manager.flip_image_vertical
        )
        btn_flip_vertical.grid(row=2, column=1, pady=5, sticky='ew')
        logging.info("Created 'Flip Vertical' button.")

    def create_rotation_point_control(self):
        """
        Creates rotation point control buttons.
        """
        self.btn_set_rotation_point = tk.Button(
            self.btn_frame, text="Set Rot Pt", command=self.app.image_manager.toggle_rotation_point_mode
        )
        self.btn_set_rotation_point.grid(row=3, column=0, columnspan=2, pady=5, sticky='ew')
        logging.info("Created 'Set Rot Pt' button.")

    def create_zoom_controls(self):
        """
        Creates zoom control buttons.
        """
        btn_zoom_in = tk.Button(
            self.btn_frame, text="Zoom In", command=self.app.image_manager.zoom_in
        )
        btn_zoom_in.grid(row=4, column=0, pady=5, sticky='ew')
        logging.info("Created 'Zoom In' button.")

        btn_zoom_out = tk.Button(
            self.btn_frame, text="Zoom Out", command=self.app.image_manager.zoom_out
        )
        btn_zoom_out.grid(row=4, column=1, pady=5, sticky='ew')
        logging.info("Created 'Zoom Out' button.")

        btn_fine_zoom_in = tk.Button(
            self.btn_frame, text="Fine Zoom In", command=self.app.image_manager.fine_zoom_in
        )
        btn_fine_zoom_in.grid(row=5, column=0, pady=5, sticky='ew')
        logging.info("Created 'Fine Zoom In' button.")

        btn_fine_zoom_out = tk.Button(
            self.btn_frame, text="Fine Zoom Out", command=self.app.image_manager.fine_zoom_out
        )
        btn_fine_zoom_out.grid(row=5, column=1, pady=5, sticky='ew')
        logging.info("Created 'Fine Zoom Out' button.")

    def create_undo_redo_controls(self):
        """
        Creates undo and redo control buttons.
        """
        self.btn_undo_move = tk.Button(
            self.btn_frame, text="Undo Move", command=self.app.image_manager.undo_move, state='disabled'
        )
        self.btn_undo_move.grid(row=6, column=0, pady=5, sticky='ew')
        logging.info("Created 'Undo Move' button.")

        self.btn_redo_move = tk.Button(
            self.btn_frame, text="Redo Move", command=self.app.image_manager.redo_move, state='disabled'
        )
        self.btn_redo_move.grid(row=6, column=1, pady=5, sticky='ew')
        logging.info("Created 'Redo Move' button.")

    def create_active_image_control(self):
        """
        Creates a dropdown to select the active image.
        """
        active_images = list(self.app.image_manager.images.keys())
        if not active_images:
            active_images = ["No Images Loaded"]

        self.active_image_var = tk.StringVar()
        self.active_image_var.set(active_images[0])  # Set default value

        lbl_active_image = tk.Label(self.btn_frame, text="Active Image:")
        lbl_active_image.grid(row=7, column=0, pady=5, sticky='w')

        self.active_image_menu = ttk.OptionMenu(
            self.btn_frame,
            self.active_image_var,
            active_images[0],
            *active_images,
            command=self.app.image_manager.change_active_image  # Correct binding
        )
        self.active_image_menu.grid(row=7, column=1, pady=5, sticky='ew')
        logging.info("Created active image selection dropdown.")

    def create_visibility_controls(self):
        """
        Creates visibility control buttons.
        """
        # Example: Could add checkboxes to toggle visibility of each image
        # For simplicity, skip implementation unless specified
        pass

    def create_ruler_button(self):
        """
        Creates buttons to open and close the ruler.
        """
        self.btn_open_ruler = tk.Button(
            self.btn_frame, text="Open Ruler", command=self.app.image_manager.toggle_ruler
        )
        self.btn_open_ruler.grid(row=8, column=0, pady=5, sticky='ew')
        logging.info("Created 'Open Ruler' button.")

    def create_load_default_image_buttons(self):
        """
        Creates buttons to load default images: Normal, Tapered, Ovoide, NarrowTappered, NarrowOvoide.
        """
        # Define button names and corresponding filenames
        default_images = {
            "Normal": "Normal(medium).svg",
            "Tapered": "Tapered(medium).svg",
            "Ovoide": "Ovoide(medium).svg",
            "NarrowTappered": "NarrowTapered(medium).svg",
            "NarrowOvoide": "NarrowOvoide(medium).svg"
        }

        # Create buttons in rows 9-13
        row_num = 9
        for name, filename in default_images.items():
            btn = tk.Button(
                self.btn_frame, text=name, command=lambda n=name, f=filename: self.app.image_manager.load_default_image(n, f)
            )
            btn.grid(row=row_num, column=0, columnspan=2, pady=5, sticky='ew')
            logging.info(f"Created '{name}' button to load '{filename}'.")
            row_num += 1

    def create_hide_show_image_window_button(self):
        """
        Creates a button to hide or show the image window.
        """
        self.btn_hide_show_image = tk.Button(
            self.btn_frame, text="Hide Window", command=self.app.image_manager.toggle_image_window
        )
        self.btn_hide_show_image.grid(row=14, column=0, columnspan=2, pady=5, sticky='ew')
        logging.info("Created 'Hide Window' button.")

    def set_active_image(self, image_name: str):
        """
        Sets the active image in the dropdown menu.
        """
        self.active_image_var.set(image_name)

    def update_active_image_menu(self):
        """
        Updates the active image dropdown menu with current images.
        """
        menu = self.active_image_menu['menu']
        menu.delete(0, 'end')
        for image_name in self.app.image_manager.images.keys():
            menu.add_command(label=image_name, command=lambda n=image_name: self.app.image_manager.change_active_image(n))
        if not self.app.image_manager.images:
            menu.add_command(label="No Images Loaded", command=lambda: None)
