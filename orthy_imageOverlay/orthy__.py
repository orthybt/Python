import sys
import math
import io
import os
import threading
import tkinter as tk
from tkinter import filedialog, colorchooser, simpledialog, messagebox
from PIL import Image, ImageTk, ImageFont, ImageDraw
import cairosvg  # For SVG support
from pynput import keyboard  # For global keyboard events
import logging   # For logging

# Configure the logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class ImageState:
    """
    Represents the state of an individual image, including its transformations
    and visibility settings.
    """

    def __init__(self, image_original, name):
        self.image_original = image_original
        self.image_display = None
        self.name = name
        self.visible = True

        # Transformation properties
        self.angle = 0
        self.scale = 1.0
        self.scale_log = 0
        self.offset_x = 512
        self.offset_y = 512
        self.rotation_point = None

        # Flip properties
        self.is_flipped_horizontally = False
        self.is_flipped_vertically = False

        # Transparency
        self.image_transparency_level = 0.2  # Set to minimum transparency by default


class ImageOverlayApp:
    """
    Main application class that handles image loading, transformations,
    and user interactions through the GUI.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Controls")
        self.image_window_visible = False  # Start with the image window hidden

        # Set the default size and position of the root window
        self.set_root_window_geometry()

        # Determine the base directory (where the .py file is located)
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # Path to the Images directory
        self.images_dir = resource_path("Images")

        # Dictionary to store ImageState objects
        self.images = {}
        self.active_image_name = None  # Name of the active image
        self.previous_active_image_name = None  # To keep track of the previous active image

        # Mouse event variables
        self.start_x = 0
        self.start_y = 0
        self.is_dragging = False
        self.is_rotation_point_mode = False  # Rotation point selection mode

        # Additional windows
        self.additional_windows = []

        # Control mode variables
        self.control_mode = False  # Flag to track if control mode is active
        self.keyboard_listener = None

        self.alt_pressed = False  # To track the Alt key state

        # Initialize the GUI
        self.setup_buttons_window()
        self.setup_image_window()
        self.update_transparency_button()

        # Hide the image window by default
        self.image_window.withdraw()
        self.btn_hide_show_image.config(text="Show Window")

        # Initialize visibility trackers for additional images
        self.ruler_visible = False           # For "Ruler" image
        self.normal_visible = False          # For "Normal" image
        self.tapered_visible = False         # For "Tapered" image
        self.ovoide_visible = False          # For "Ovoide" image
        self.narrow_tapered_visible = False  # For "Narrow Tapered" image
        self.narrow_ovoide_visible = False   # For "Narrow Ovoide" image
        self.angulation_visible = False      # For "Angulation" image

        # Set up global hotkeys
        self.setup_global_hotkeys()

    def set_root_window_geometry(self):
        """
        Sets the default size and position of the root window.
        """
        # Desired size of the root window
        window_width = 185
        window_height = 650

        # Margins from the screen edges
        margin_right = 81
        margin_top = 315
        margin_bottom = 162  # This is for validation; not directly used

        # Get the screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Calculate x and y positions
        x_position = screen_width - window_width - margin_right
        y_position = margin_top

        # Set the geometry of the root window
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    def setup_global_hotkeys(self):
        """
        Sets up global keyboard shortcuts using pynput.
        """
        # Ctrl + Alt + 1 to start/stop Control Mode
        def toggle_control_mode_hotkey():
            self.root.after(0, self.toggle_control_mode)
            logging.info("Global hotkey 'Ctrl+Alt+1' pressed for toggling control mode.")

        def toggle_image_window_hotkey():
            self.root.after(0, self.toggle_image_window)
            logging.info("Global hotkey 'Ctrl+Alt+2' pressed for toggling image window.")

        self.global_hotkey_listener = keyboard.GlobalHotKeys({
            '<ctrl>+<alt>+1': toggle_control_mode_hotkey,
            '<ctrl>+<alt>+2': toggle_image_window_hotkey,
        })
        self.global_hotkey_listener.start()

    ####################################################################################################################################################################################
    ###                                                             --- Setup Methods ---                                                                                           ###
    ####################################################################################################################################################################################
    def setup_buttons_window(self):
        """
        Sets up the main control window with all the buttons and controls.
        """
        # Keep the control window on top
        self.root.attributes('-topmost', True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Create a frame to organize buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(padx=10, pady=10, fill='both', expand=True)

        # Buttons for controlling transparency
        self.create_transparency_controls(btn_frame)

        # Load and hide/show image buttons
        self.create_image_controls(btn_frame)

        # Flip buttons
        self.create_flip_controls(btn_frame)

        # Rotation point button
        self.create_rotation_point_control(btn_frame)

        # Zoom buttons
        self.create_zoom_controls(btn_frame)

        # Active image selection
        self.create_active_image_control(btn_frame)

        # Control button
        self.create_control_button(btn_frame)

        # **New Angulation Button**
        self.create_angulation_button(btn_frame)
        
        # Load Image button
        btn_load_image = tk.Button(
            btn_frame, text="Load Image", command=self.log_button_press(self.load_user_image)
        )
        btn_load_image.grid(row=17, column=0, columnspan=2, pady=5, sticky='ew')

        # Buttons to toggle additional images
        self.create_ruler_button(btn_frame)
        self.create_normal_button(btn_frame)
        self.create_tapered_button(btn_frame)
        self.create_ovoide_button(btn_frame)
        self.create_narrow_tapered_button(btn_frame)
        self.create_narrow_ovoide_button(btn_frame)

         # Configure grid weights for equal button sizes
        for i in range(2):
            btn_frame.columnconfigure(i, weight=1)
            btn_frame.columnconfigure(i, weight=1)

        # Set the transparency of the buttons window directly to fully opaque
        self.root.attributes('-alpha', 1.0)

    def setup_image_window(self):
        """
        Sets up the image display window where images are shown and manipulated.
        """
        self.image_window = tk.Toplevel(self.root)
        self.image_window.title("Image Window")

        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Set the window to match screen size
        self.image_window.geometry(f"{screen_width}x{screen_height}+0+0")

        # Allow window resizing
        self.image_window.resizable(True, True)

        # Remove window decorations and make background transparent
        self.image_window.overrideredirect(True)
        self.image_window.attributes('-transparentcolor', 'grey')

        self.image_window.attributes('-topmost', True)
        self.image_window.protocol("WM_DELETE_WINDOW", self.on_close)

        # Create the canvas with grey background
        self.canvas = tk.Canvas(self.image_window, bg='grey', highlightthickness=0, borderwidth=0)
        self.canvas.pack(fill='both', expand=True)

        # Force update to get accurate canvas size
        self.image_window.update_idletasks()

        # Bind mouse events
        self.bind_canvas_events()

        # Update canvas size on window resize
        self.image_window.bind('<Configure>', self.on_image_window_resize)

    ####################################################################################################################################################################################
    ###                                                             --- Control Creation Methods ---                                                                                ###
    ####################################################################################################################################################################################
    def create_transparency_controls(self, parent):
        """
        Creates transparency control buttons.
        """
        # Toggle transparency button
        self.btn_toggle_transparency = tk.Button(
            parent, text="Toggle Transp", command=self.log_button_press(self.toggle_transparency)
        )
        self.btn_toggle_transparency.grid(row=0, column=0, columnspan=2, pady=5, sticky='ew')

    def create_image_controls(self, parent):
        """
        Creates image loading and window toggling buttons.
        """
        # Hide/Show Window button
        self.btn_hide_show_image = tk.Button(
            parent, text="Hide Window", command=self.log_button_press(self.toggle_image_window)
        )
        self.btn_hide_show_image.grid(row=1, column=0, columnspan=2, pady=5, sticky='ew')

    def create_flip_controls(self, parent):
        """
        Creates flip control buttons.
        """
        btn_flip_horizontal = tk.Button(
            parent, text="Flip H", command=self.log_button_press(self.flip_image_horizontal)
        )
        btn_flip_horizontal.grid(row=2, column=0, pady=5, sticky='ew')

        btn_flip_vertical = tk.Button(
            parent, text="Flip V", command=self.log_button_press(self.flip_image_vertical)
        )
        btn_flip_vertical.grid(row=2, column=1, pady=5, sticky='ew')

    def create_rotation_point_control(self, parent):
        """
        Creates rotation point control button.
        """
        self.btn_set_rotation_point = tk.Button(
            parent, text="Set Rot Pt", command=self.log_button_press(self.toggle_rotation_point_mode)
        )
        self.btn_set_rotation_point.grid(row=3, column=0, columnspan=2, pady=5, sticky='ew')

    def create_zoom_controls(self, parent):
        """
        Creates zoom control buttons.
        """
        btn_zoom_in = tk.Button(
            parent, text="+", command=self.log_button_press(self.zoom_in)
        )
        btn_zoom_in.grid(row=4, column=0, pady=5, sticky='ew')

        btn_zoom_out = tk.Button(
            parent, text="-", command=self.log_button_press(self.zoom_out)
        )
        btn_zoom_out.grid(row=4, column=1, pady=5, sticky='ew')

        btn_fine_zoom_in = tk.Button(
            parent, text="+ Fine", command=self.log_button_press(self.fine_zoom_in)
        )
        btn_fine_zoom_in.grid(row=5, column=0, pady=5, sticky='ew')

        btn_fine_zoom_out = tk.Button(
            parent, text="- Fine", command=self.log_button_press(self.fine_zoom_out)
        )
        btn_fine_zoom_out.grid(row=5, column=1, pady=5, sticky='ew')

        btn_fine_rotate_clockwise = tk.Button(
            parent, text="Rot +0.5°", command=self.log_button_press(self.fine_rotate_clockwise)
        )
        btn_fine_rotate_clockwise.grid(row=6, column=0, pady=5, sticky='ew')

        btn_fine_rotate_counterclockwise = tk.Button(
            parent, text="Rot -0.5°", command=self.log_button_press(self.fine_rotate_counterclockwise)
        )
        btn_fine_rotate_counterclockwise.grid(row=6, column=1, pady=5, sticky='ew')

    def create_active_image_control(self, parent):
        """
        Creates active image selection controls.
        """
        tk.Label(parent, text="Active Image:").grid(row=8, column=0, pady=5, sticky='e')

        self.active_image_var = tk.StringVar(value="")
        self.active_image_menu = tk.OptionMenu(
            parent, self.active_image_var, "", command=self.change_active_image
        )
        self.active_image_menu.grid(row=8, column=1, pady=5, sticky='ew')

    def create_control_button(self, parent):
        """
        Creates a button to toggle control mode.
        """
        self.btn_control_mode = tk.Button(
            parent, text="Control Mode", command=self.log_button_press(self.toggle_control_mode)
        )
        self.btn_control_mode.grid(row=9, column=0, columnspan=2, pady=5, sticky='ew')

    def create_angulation_button(self, parent):
        """
        Creates a button renamed to "Angulation" and places it below the "Ruler" button.
        """
        self.btn_angulation = tk.Button(
            parent, text="Angulation", command=self.log_button_press(self.toggle_angulation)
        )
        self.btn_angulation.grid(row=11, column=0, columnspan=2, pady=5, sticky='ew')

    def create_ruler_button(self, parent):
        """
        Creates a button to toggle the Ruler image.
        """
        self.btn_open_ruler = tk.Button(
            parent, text="Ruler", command=self.log_button_press(self.toggle_ruler)
        )
        self.btn_open_ruler.grid(row=10, column=0, columnspan=2, pady=5, sticky='ew')

    def create_normal_button(self, parent):
        """
        Creates a button to toggle the Normal image.
        """
        self.btn_open_normal = tk.Button(
            parent, text="Normal", command=self.log_button_press(self.toggle_normal)
        )
        self.btn_open_normal.grid(row=12, column=0, columnspan=2, pady=5, sticky='ew')

    def create_tapered_button(self, parent):
        """
        Creates a button to toggle the Tapered image.
        """
        self.btn_open_tapered = tk.Button(
            parent, text="Tapered", command=self.log_button_press(self.toggle_tapered)
        )
        self.btn_open_tapered.grid(row=13, column=0, columnspan=2, pady=5, sticky='ew')

    def create_ovoide_button(self, parent):
        """
        Creates a button to toggle the Ovoide image.
        """
        self.btn_open_ovoide = tk.Button(
            parent, text="Ovoide", command=self.log_button_press(self.toggle_ovoide)
        )
        self.btn_open_ovoide.grid(row=14, column=0, columnspan=2, pady=5, sticky='ew')

    def create_narrow_tapered_button(self, parent):
        """
        Creates a button to toggle the Narrow Tapered image.
        """
        self.btn_open_narrow_tapered = tk.Button(
            parent, text="Narrow Tapered", command=self.log_button_press(self.toggle_narrow_tapered)
        )
        self.btn_open_narrow_tapered.grid(row=15, column=0, columnspan=2, pady=5, sticky='ew')

    def create_narrow_ovoide_button(self, parent):
        """
        Creates a button to toggle the Narrow Ovoide image.
        """
        self.btn_open_narrow_ovoide = tk.Button(
            parent, text="Narrow Ovoide", command=self.log_button_press(self.toggle_narrow_ovoide)
        )
        self.btn_open_narrow_ovoide.grid(row=16, column=0, columnspan=2, pady=5, sticky='ew')

    def log_button_press(self, func):
        """
        Decorator to log button presses.
        """
        def wrapper(*args, **kwargs):
            logging.info(f"Button pressed: {func.__name__}")
            return func(*args, **kwargs)
        return wrapper

    ####################################################################################################################################################################################
    ###                                                             --- Binding Methods ---                                                                                         ###
    ####################################################################################################################################################################################

    def bind_canvas_events(self):
        """
        Binds mouse and keyboard events to the canvas for user interaction.
        """
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.on_right_click)

        # Mouse wheel support across platforms
        if sys.platform.startswith('win'):
            self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        elif sys.platform == 'darwin':
            self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        else:
            self.canvas.bind("<Button-4>", lambda event: self.on_mouse_wheel(event))
            self.canvas.bind("<Button-5>", lambda event: self.on_mouse_wheel(event))

    def on_image_window_resize(self, event):
        """
        Adjusts the canvas size when the image window is resized.
        """
        self.canvas.config(width=event.width, height=event.height)
        self.draw_images()

    ####################################################################################################################################################################################
    ###                                                             --- Transparency Control Methods ---                                                                            ###
    ####################################################################################################################################################################################
    def toggle_transparency(self):
        """
        Toggles the transparency level of the active image.
        """
        active_image = self.get_active_image()
        if not active_image:
            return

        if active_image.image_transparency_level > 0.2:
            active_image.image_transparency_level = 0.2
            self.btn_toggle_transparency.config(text="Max Transp")
            logging.info(f"Transparency of image '{active_image.name}' set to minimum.")
        else:
            active_image.image_transparency_level = 1.0
            self.btn_toggle_transparency.config(text="Min Transp")
            logging.info(f"Transparency of image '{active_image.name}' set to maximum.")
        self.draw_images()

    def update_transparency_button(self):
        """
        Updates the transparency toggle button text based on the current state.
        """
        active_image = self.get_active_image()
        if active_image and active_image.image_transparency_level <= 0.2:
            self.btn_toggle_transparency.config(text="Max Transp")
        else:
            self.btn_toggle_transparency.config(text="Min Transp")

    ####################################################################################################################################################################################
    ###                                                             --- Image Loading and Management ---                                                                             ###
    ####################################################################################################################################################################################
    def load_image(self, image_name):
        """
        Loads an image file and creates an ImageState object.
        """
        filepath = filedialog.askopenfilename(
            title=f"Select {image_name}",
            filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.bmp;*.svg")]
        )
        if filepath:
            image_original = self.open_image_file(filepath)
            if image_original:
                image_state = ImageState(image_original, image_name)
                self.images[image_name] = image_state
                self.active_image_name = image_name
                self.update_active_image_menu()
                self.active_image_var.set(image_name)
                self.draw_images()

                logging.info(f"Image '{image_name}' loaded from '{filepath}'.")

                if not self.image_window_visible:
                    self.toggle_image_window()

    def open_image_file(self, filepath):
        """
        Opens an image file, handling SVG files separately.
        """
        try:
            if filepath.lower().endswith('.svg'):
                # Convert SVG to PNG using cairosvg
                png_data = cairosvg.svg2png(url=filepath)
                image_original = Image.open(io.BytesIO(png_data)).convert("RGBA")
            else:
                image_original = Image.open(filepath).convert("RGBA")
            return image_original
        except Exception as e:
            logging.error(f"Error loading image: {e}")
            return None

    # Updated method names and image keys to reflect actual image names

    def load_default_ruler_image(self):
        """
        Loads 'liniar_new_n2.svg' as the Ruler image.
        """
        filepath = os.path.join(self.images_dir, 'liniar_new_n2.svg')
        if os.path.exists(filepath):
            image_original = self.open_image_file(filepath)
            if image_original:
                image_state = ImageState(image_original, "Ruler")
                self.images["Ruler"] = image_state

                # Center the Ruler image
                self.center_ruler_image()

                # Do not change the active image when loading the Ruler image
                self.update_active_image_menu()
                self.draw_images()

                logging.info("Default 'Ruler' image loaded.")

                if not self.image_window_visible:
                    self.toggle_image_window()
        else:
            logging.error(f"'liniar_new_n2.svg' not found at {filepath}")

    def load_default_normal_image(self):
        """
        Loads 'Normal(medium).svg' as the Normal image.
        """
        filepath = os.path.join(self.images_dir, 'Normal(medium).svg')
        if os.path.exists(filepath):
            image_original = self.open_image_file(filepath)
            if image_original:
                image_state = ImageState(image_original, "Normal")
                self.images["Normal"] = image_state

                # Center the Normal image
                self.center_normal_image()

                # Do not change the active image when loading the Normal image
                self.update_active_image_menu()
                self.draw_images()

                logging.info("Default 'Normal' image loaded.")

                if not self.image_window_visible:
                    self.toggle_image_window()
        else:
            logging.error(f"'Normal(medium).svg' not found at {filepath}")

    def load_default_tapered_image(self):
        """
        Loads 'Tapered.svg' as the Tapered image.
        """
        filepath = os.path.join(self.images_dir, 'Tapered.svg')
        if os.path.exists(filepath):
            image_original = self.open_image_file(filepath)
            if image_original:
                image_state = ImageState(image_original, "Tapered")
                self.images["Tapered"] = image_state

                # Center the Tapered image
                self.center_tapered_image()

                # Do not change the active image when loading the Tapered image
                self.update_active_image_menu()
                self.draw_images()

                logging.info("Default 'Tapered' image loaded.")

                if not self.image_window_visible:
                    self.toggle_image_window()
        else:
            logging.error(f"'Tapered.svg' not found at {filepath}")

    def load_default_ovoide_image(self):
        """
        Loads 'Ovoide.svg' as the Ovoide image.
        """
        filepath = os.path.join(self.images_dir, 'Ovoide.svg')
        if os.path.exists(filepath):
            image_original = self.open_image_file(filepath)
            if image_original:
                image_state = ImageState(image_original, "Ovoide")
                self.images["Ovoide"] = image_state

                # Center the Ovoide image
                self.center_ovoide_image()

                # Do not change the active image when loading the Ovoide image
                self.update_active_image_menu()
                self.draw_images()

                logging.info("Default 'Ovoide' image loaded.")

                if not self.image_window_visible:
                    self.toggle_image_window()
        else:
            logging.error(f"'Ovoide.svg' not found at {filepath}")

    def load_default_narrow_tapered_image(self):
        """
        Loads 'NarrowTapered.svg' as the Narrow Tapered image.
        """
        filepath = os.path.join(self.images_dir, 'NarrowTapered.svg')
        if os.path.exists(filepath):
            image_original = self.open_image_file(filepath)
            if image_original:
                image_state = ImageState(image_original, "Narrow Tapered")
                self.images["Narrow Tapered"] = image_state

                # Center the Narrow Tapered image
                self.center_narrow_tapered_image()

                # Do not change the active image when loading the Narrow Tapered image
                self.update_active_image_menu()
                self.draw_images()

                logging.info("Default 'Narrow Tapered' image loaded.")

                if not self.image_window_visible:
                    self.toggle_image_window()
        else:
            logging.error(f"'NarrowTapered.svg' not found at {filepath}")

    def load_default_narrow_ovoide_image(self):
        """
        Loads 'NarrowOvoide.svg' as the Narrow Ovoide image.
        """
        filepath = os.path.join(self.images_dir, 'NarrowOvoide.svg')
        if os.path.exists(filepath):
            image_original = self.open_image_file(filepath)
            if image_original:
                image_state = ImageState(image_original, "Narrow Ovoide")
                self.images["Narrow Ovoide"] = image_state

                # Center the Narrow Ovoide image
                self.center_narrow_ovoide_image()

                # Do not change the active image when loading the Narrow Ovoide image
                self.update_active_image_menu()
                self.draw_images()

                logging.info("Default 'Narrow Ovoide' image loaded.")

                if not self.image_window_visible:
                    self.toggle_image_window()
        else:
            logging.error(f"'NarrowOvoide.svg' not found at {filepath}")

    def load_default_angulation_image(self):
        """
        Loads 'angulation.svg' as the Angulation image.
        """
        filepath = os.path.join(self.images_dir, 'angulation.svg')
        if os.path.exists(filepath):
            image_original = self.open_image_file(filepath)
            if image_original:
                image_state = ImageState(image_original, "Angulation")
                self.images["Angulation"] = image_state

                # Center the Angulation image
                self.center_angulation_image()

                # Do not change the active image when loading the Angulation image
                self.update_active_image_menu()
                self.draw_images()

                logging.info("Default 'Angulation' image loaded.")

                if not self.image_window_visible:
                    self.toggle_image_window()
        else:
            logging.error(f"'angulation.svg' not found at {filepath}")

    def update_active_image_menu(self):
        """
        Updates the dropdown menu for selecting the active image.
        """
        menu = self.active_image_menu['menu']
        menu.delete(0, 'end')
        for image_name in self.images.keys():
            menu.add_command(
                label=image_name,
                command=tk._setit(self.active_image_var, image_name, self.change_active_image)
            )
        if not self.images:
            self.active_image_var.set("")
        else:
            if self.active_image_name not in self.images:
                self.active_image_name = list(self.images.keys())[0]
                self.active_image_var.set(self.active_image_name)

    def get_active_image(self):
        """
        Retrieves the currently active image.
        """
        return self.images.get(self.active_image_name)

    def change_active_image(self, value):
        """
        Changes the active image based on user selection.
        """
        self.active_image_name = value
        self.update_transparency_button()
        logging.info(f"Active image changed to '{value}'.")

    def toggle_image_window(self):
        """
        Shows or hides the image window.
        """
        if self.image_window_visible:
            self.image_window.withdraw()
            self.image_window_visible = False
            self.btn_hide_show_image.config(text="Show Window")
            logging.info("Image window hidden.")
        else:
            self.image_window.deiconify()
            self.image_window_visible = True
            self.btn_hide_show_image.config(text="Hide Window")
            logging.info("Image window shown.")

    ####################################################################################################################################################################################
    ###                                                             --- Toggle Methods for Images ---                                                                                ###
    ####################################################################################################################################################################################

    def toggle_ruler(self):
        """
        Toggles the visibility of the Ruler image.
        """
        if not self.ruler_visible:
            # Load the Ruler image if not already loaded
            if "Ruler" not in self.images:
                self.load_default_ruler_image()
            else:
                # If already loaded, make it visible
                self.images["Ruler"].visible = True
                # Center the image
                self.center_ruler_image()
                self.draw_images()
            self.ruler_visible = True
            self.btn_open_ruler.config(text="Hide Ruler")
            logging.info("Ruler image made visible.")

            # Store the previous active image and set the active image to "Ruler"
            self.previous_active_image_name = self.active_image_name
            self.active_image_name = "Ruler"
            self.update_active_image_menu()
            self.active_image_var.set(self.active_image_name)

            if not self.image_window_visible:
                self.toggle_image_window()
        else:
            # Hide the Ruler image
            if "Ruler" in self.images:
                self.images["Ruler"].visible = False
                self.draw_images()
            self.ruler_visible = False
            self.btn_open_ruler.config(text="Ruler")
            logging.info("Ruler image hidden.")

            # If the active image is "Ruler", revert to the previous active image
            if self.active_image_name == "Ruler":
                self.active_image_name = self.previous_active_image_name
                self.update_active_image_menu()
                self.active_image_var.set(self.active_image_name)
                self.previous_active_image_name = None

    def toggle_normal(self):
        """
        Toggles the visibility of the Normal image.
        """
        if not self.normal_visible:
            # Load the Normal image if not already loaded
            if "Normal" not in self.images:
                self.load_default_normal_image()
            else:
                # If already loaded, make it visible
                self.images["Normal"].visible = True
                # Center the image
                self.center_normal_image()
                self.draw_images()
            self.normal_visible = True
            self.btn_open_normal.config(text="Hide Normal")
            logging.info("Normal image made visible.")

            # Store the previous active image and set the active image to "Normal"
            self.previous_active_image_name = self.active_image_name
            self.active_image_name = "Normal"
            self.update_active_image_menu()
            self.active_image_var.set(self.active_image_name)

            if not self.image_window_visible:
                self.toggle_image_window()
        else:
            # Hide the Normal image
            if "Normal" in self.images:
                self.images["Normal"].visible = False
                self.draw_images()
            self.normal_visible = False
            self.btn_open_normal.config(text="Normal")
            logging.info("Normal image hidden.")

            # If the active image is "Normal", revert to the previous active image
            if self.active_image_name == "Normal":
                self.active_image_name = self.previous_active_image_name
                self.update_active_image_menu()
                self.active_image_var.set(self.active_image_name)
                self.previous_active_image_name = None

    def toggle_tapered(self):
        """
        Toggles the visibility of the Tapered image.
        """
        if not self.tapered_visible:
            # Load the Tapered image if not already loaded
            if "Tapered" not in self.images:
                self.load_default_tapered_image()
            else:
                # If already loaded, make it visible
                self.images["Tapered"].visible = True
                # Center the image
                self.center_tapered_image()
                self.draw_images()
            self.tapered_visible = True
            self.btn_open_tapered.config(text="Hide Tapered")
            logging.info("Tapered image made visible.")

            # Store the previous active image and set the active image to "Tapered"
            self.previous_active_image_name = self.active_image_name
            self.active_image_name = "Tapered"
            self.update_active_image_menu()
            self.active_image_var.set(self.active_image_name)

            if not self.image_window_visible:
                self.toggle_image_window()
        else:
            # Hide the Tapered image
            if "Tapered" in self.images:
                self.images["Tapered"].visible = False
                self.draw_images()
            self.tapered_visible = False
            self.btn_open_tapered.config(text="Tapered")
            logging.info("Tapered image hidden.")

            # If the active image is "Tapered", revert to the previous active image
            if self.active_image_name == "Tapered":
                self.active_image_name = self.previous_active_image_name
                self.update_active_image_menu()
                self.active_image_var.set(self.active_image_name)
                self.previous_active_image_name = None

    def toggle_ovoide(self):
        """
        Toggles the visibility of the Ovoide image.
        """
        if not self.ovoide_visible:
            # Load the Ovoide image if not already loaded
            if "Ovoide" not in self.images:
                self.load_default_ovoide_image()
            else:
                # If already loaded, make it visible
                self.images["Ovoide"].visible = True
                # Center the image
                self.center_ovoide_image()
                self.draw_images()
            self.ovoide_visible = True
            self.btn_open_ovoide.config(text="Hide Ovoide")
            logging.info("Ovoide image made visible.")

            # Store the previous active image and set the active image to "Ovoide"
            self.previous_active_image_name = self.active_image_name
            self.active_image_name = "Ovoide"
            self.update_active_image_menu()
            self.active_image_var.set(self.active_image_name)

            if not self.image_window_visible:
                self.toggle_image_window()
        else:
            # Hide the Ovoide image
            if "Ovoide" in self.images:
                self.images["Ovoide"].visible = False
                self.draw_images()
            self.ovoide_visible = False
            self.btn_open_ovoide.config(text="Ovoide")
            logging.info("Ovoide image hidden.")

            # If the active image is "Ovoide", revert to the previous active image
            if self.active_image_name == "Ovoide":
                self.active_image_name = self.previous_active_image_name
                self.update_active_image_menu()
                self.active_image_var.set(self.active_image_name)
                self.previous_active_image_name = None

    def toggle_narrow_tapered(self):
        """
        Toggles the visibility of the Narrow Tapered image.
        """
        if not self.narrow_tapered_visible:
            # Load the Narrow Tapered image if not already loaded
            if "Narrow Tapered" not in self.images:
                self.load_default_narrow_tapered_image()
            else:
                # If already loaded, make it visible
                self.images["Narrow Tapered"].visible = True
                # Center the image
                self.center_narrow_tapered_image()
                self.draw_images()
            self.narrow_tapered_visible = True
            self.btn_open_narrow_tapered.config(text="Hide Narrow Tapered")
            logging.info("Narrow Tapered image made visible.")

            # Store the previous active image and set the active image to "Narrow Tapered"
            self.previous_active_image_name = self.active_image_name
            self.active_image_name = "Narrow Tapered"
            self.update_active_image_menu()
            self.active_image_var.set(self.active_image_name)

            if not self.image_window_visible:
                self.toggle_image_window()
        else:
            # Hide the Narrow Tapered image
            if "Narrow Tapered" in self.images:
                self.images["Narrow Tapered"].visible = False
                self.draw_images()
            self.narrow_tapered_visible = False
            self.btn_open_narrow_tapered.config(text="Narrow Tapered")
            logging.info("Narrow Tapered image hidden.")

            # If the active image is "Narrow Tapered", revert to the previous active image
            if self.active_image_name == "Narrow Tapered":
                self.active_image_name = self.previous_active_image_name
                self.update_active_image_menu()
                self.active_image_var.set(self.active_image_name)
                self.previous_active_image_name = None

    def toggle_narrow_ovoide(self):
        """
        Toggles the visibility of the Narrow Ovoide image.
        """
        if not self.narrow_ovoide_visible:
            # Load the Narrow Ovoide image if not already loaded
            if "Narrow Ovoide" not in self.images:
                self.load_default_narrow_ovoide_image()
            else:
                # If already loaded, make it visible
                self.images["Narrow Ovoide"].visible = True
                # Center the image
                self.center_narrow_ovoide_image()
                self.draw_images()
            self.narrow_ovoide_visible = True
            self.btn_open_narrow_ovoide.config(text="Hide Narrow Ovoide")
            logging.info("Narrow Ovoide image made visible.")

            # Store the previous active image and set the active image to "Narrow Ovoide"
            self.previous_active_image_name = self.active_image_name
            self.active_image_name = "Narrow Ovoide"
            self.update_active_image_menu()
            self.active_image_var.set(self.active_image_name)

            if not self.image_window_visible:
                self.toggle_image_window()
        else:
            # Hide the Narrow Ovoide image
            if "Narrow Ovoide" in self.images:
                self.images["Narrow Ovoide"].visible = False
                self.draw_images()
            self.narrow_ovoide_visible = False
            self.btn_open_narrow_ovoide.config(text="Narrow Ovoide")
            logging.info("Narrow Ovoide image hidden.")

            # If the active image is "Narrow Ovoide", revert to the previous active image
            if self.active_image_name == "Narrow Ovoide":
                self.active_image_name = self.previous_active_image_name
                self.update_active_image_menu()
                self.active_image_var.set(self.active_image_name)
                self.previous_active_image_name = None

    def toggle_angulation(self):
        """
        Toggles the visibility of the Angulation image.
        """
        if not self.angulation_visible:
            # Load the Angulation image if not already loaded
            if "Angulation" not in self.images:
                self.load_default_angulation_image()
            else:
                # If already loaded, make it visible
                self.images["Angulation"].visible = True
                # Center the image
                self.center_angulation_image()
                self.draw_images()
            self.angulation_visible = True
            self.btn_angulation.config(text="Hide Angulation")
            logging.info("Angulation image made visible.")

            # Store the previous active image and set the active image to "Angulation"
            self.previous_active_image_name = self.active_image_name
            self.active_image_name = "Angulation"
            self.update_active_image_menu()
            self.active_image_var.set(self.active_image_name)

            if not self.image_window_visible:
                self.toggle_image_window()
        else:
            # Hide the Angulation image
            if "Angulation" in self.images:
                self.images["Angulation"].visible = False
                self.draw_images()
            self.angulation_visible = False
            self.btn_angulation.config(text="Angulation")
            logging.info("Angulation image hidden.")

            # If the active image is "Angulation", revert to the previous active image
            if self.active_image_name == "Angulation":
                self.active_image_name = self.previous_active_image_name
                self.update_active_image_menu()
                self.active_image_var.set(self.active_image_name)
                self.previous_active_image_name = None

    ####################################################################################################################################################################################
    ###                                                             --- Image Drawing Methods ---                                                                                   ###
    ####################################################################################################################################################################################
    def draw_images(self):
        """
        Clears the canvas and redraws all visible images.
        """
        self.canvas.delete("all")
        for image_state in self.images.values():
            if image_state.visible:
                self.draw_image(image_state)
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

        # Resize
        img = img.resize(
            (int(img.width * image_state.scale), int(img.height * image_state.scale)),
            Image.LANCZOS
        )

        # Apply flips
        if image_state.is_flipped_horizontally:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        if image_state.is_flipped_vertically:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)

        # Rotate around the rotation point if set
        if image_state.rotation_point:
            rotation_center = (
                image_state.rotation_point[0] - (image_state.offset_x - img.width / 2),
                image_state.rotation_point[1] - (image_state.offset_y - img.height / 2)
            )
            img = img.rotate(image_state.angle, expand=True, center=rotation_center)
        else:
            img = img.rotate(image_state.angle, expand=True)

        image_state.image_display = ImageTk.PhotoImage(img)

        # Draw the image at the offset position
        self.canvas.create_image(
            image_state.offset_x, image_state.offset_y, image=image_state.image_display
        )

        # Draw a marker at the rotation point if set
        if image_state.rotation_point:
            radius = 1.5  # Marker size
            self.canvas.create_oval(
                image_state.rotation_point[0] - radius, image_state.rotation_point[1] - radius,
                image_state.rotation_point[0] + radius, image_state.rotation_point[1] + radius,
                fill='red', outline=''
            )

    ####################################################################################################################################################################################
    ###                                                             --- Mouse and Keyboard Handlers ---                                                                             ###
    ####################################################################################################################################################################################
    def on_mouse_down(self, event):
        """
        Handles the event when the left mouse button is pressed.
        """
        if not self.is_rotation_point_mode:
            self.is_dragging = True
            self.start_x = event.x_root
            self.start_y = event.y_root
            logging.debug(f"Mouse down at ({self.start_x}, {self.start_y}).")

    def on_mouse_up(self, event):
        """
        Handles the event when the left mouse button is released.
        """
        self.is_dragging = False
        logging.debug(f"Mouse up at ({event.x_root}, {event.y_root}).")

    def on_mouse_move(self, event):
        """
        Handles the event when the mouse is moved while a button is pressed.
        """
        active_image = self.get_active_image()
        if self.is_dragging and active_image:
            dx = event.x_root - self.start_x
            dy = event.y_root - self.start_y

            if event.state & 0x0004:  # If Ctrl key is held down
                active_image.angle += dx * 0.1  # Reduced rotation sensitivity
                active_image.angle %= 360  # Keep angle within 0-360 degrees
                logging.debug(f"Rotating image '{active_image.name}' by {dx * 0.1} degrees.")
            else:
                active_image.offset_x += dx
                active_image.offset_y += dy
                logging.debug(f"Moving image '{active_image.name}' by ({dx}, {dy}).")

            self.start_x = event.x_root
            self.start_y = event.y_root
            self.draw_images()

    def on_canvas_click(self, event):
        """
        Handles the event when the canvas is clicked.
        """
        active_image = self.get_active_image()
        if active_image and self.is_rotation_point_mode:
            # Set the rotation point
            active_image.rotation_point = (event.x, event.y)
            self.is_rotation_point_mode = False
            self.btn_set_rotation_point.config(text="Set Rot Pt")
            self.draw_images()
            logging.info(f"Rotation point set for image '{active_image.name}' at ({event.x}, {event.y}).")

    def on_mouse_wheel(self, event):
        """
        Handles the mouse wheel event for zooming.
        """
        active_image = self.get_active_image()
        if not active_image:
            return

        delta = self.get_mouse_wheel_delta(event)
        old_scale = active_image.scale
        active_image.scale_log += delta * 0.05  # Reduce sensitivity
        active_image.scale = pow(2, active_image.scale_log)

        # Limit scale
        active_image.scale = max(0.1, min(active_image.scale, 10.0))
        active_image.scale_log = math.log2(active_image.scale)

        logging.debug(f"Zooming image '{active_image.name}' to scale {active_image.scale}.")

        self.draw_images()

    def get_mouse_wheel_delta(self, event):
        """
        Normalizes the mouse wheel delta across different platforms.
        """
        if sys.platform.startswith('win') or sys.platform == 'darwin':
            return event.delta / 120
        else:
            if event.num == 4:  # Scroll up
                return 1
            elif event.num == 5:  # Scroll down
                return -1
            else:
                return 0

    def on_right_click(self, event=None):
        """
        Handles the event when the right mouse button is clicked (resets transformations).
        """
        active_image = self.get_active_image()
        if not active_image:
            return

        # Reset transformations
        active_image.angle = 0
        active_image.scale = 1.0
        active_image.scale_log = 0
        active_image.offset_x = self.canvas.winfo_width() / 2
        active_image.offset_y = self.canvas.winfo_height() / 2

        # Reset transparency
        active_image.image_transparency_level = 1.0
        self.btn_toggle_transparency.config(text="Toggle Transp")

        # Reset flips
        active_image.is_flipped_horizontally = False
        active_image.is_flipped_vertically = False

        # Reset rotation point
        active_image.rotation_point = None
        self.is_rotation_point_mode = False
        self.btn_set_rotation_point.config(text="Set Rot Pt")

        self.draw_images()

        logging.info(f"Reset transformations for image '{active_image.name}'.")

    ####################################################################################################################################################################################
    ###                                                             --- Image Transformation ---                                                                                    ###
    ####################################################################################################################################################################################
    def zoom_in(self):
        """
        Zooms in the active image.
        """
        active_image = self.get_active_image()
        if not active_image:
            return
        active_image.scale = min(active_image.scale + 0.05, 10.0)
        active_image.scale_log = math.log2(active_image.scale)
        logging.info(f"Zoomed in on image '{active_image.name}' to scale {active_image.scale}.")
        self.draw_images()

    def zoom_out(self):
        """
        Zooms out the active image.
        """
        active_image = self.get_active_image()
        if not active_image:
            return
        active_image.scale = max(active_image.scale - 0.05, 0.1)
        active_image.scale_log = math.log2(active_image.scale)
        logging.info(f"Zoomed out on image '{active_image.name}' to scale {active_image.scale}.")
        self.draw_images()

    def fine_zoom_in(self):
        """
        Fine zooms in the active image.
        """
        active_image = self.get_active_image()
        if not active_image:
            return
        active_image.scale = min(active_image.scale + 0.01, 10.0)
        active_image.scale_log = math.log2(active_image.scale)
        logging.info(f"Fine zoomed in on image '{active_image.name}' to scale {active_image.scale}.")
        self.draw_images()

    def fine_zoom_out(self):
        """
        Fine zooms out the active image.
        """
        active_image = self.get_active_image()
        if not active_image:
            return
        active_image.scale = max(active_image.scale - 0.01, 0.1)
        active_image.scale_log = math.log2(active_image.scale)
        logging.info(f"Fine zoomed out on image '{active_image.name}' to scale {active_image.scale}.")
        self.draw_images()

    def flip_image_horizontal(self):
        """
        Flips the active image horizontally.
        """
        active_image = self.get_active_image()
        if not active_image:
            return
        active_image.is_flipped_horizontally = not active_image.is_flipped_horizontally
        logging.info(f"Image '{active_image.name}' flipped horizontally.")
        self.draw_images()

    def flip_image_vertical(self):
        """
        Flips the active image vertically.
        """
        active_image = self.get_active_image()
        if not active_image:
            return
        active_image.is_flipped_vertically = not active_image.is_flipped_vertically
        logging.info(f"Image '{active_image.name}' flipped vertically.")
        self.draw_images()

    def toggle_rotation_point_mode(self):
        """
        Toggles the mode for setting the rotation point.
        """
        active_image = self.get_active_image()
        if not active_image:
            return
        if not self.is_rotation_point_mode:
            self.is_rotation_point_mode = True
            self.btn_set_rotation_point.config(text="Cancel Rot Pt")
            logging.info("Rotation point mode enabled.")
        else:
            self.is_rotation_point_mode = False
            self.btn_set_rotation_point.config(text="Set Rot Pt")
            active_image.rotation_point = None
            logging.info("Rotation point mode disabled and rotation point reset.")
            self.draw_images()

    ####################################################################################################################################################################################
    ###                                                             --- Fine Rotation Control Methods ---                                                                            ###
    ####################################################################################################################################################################################
    def fine_rotate_clockwise(self):
        """
        Rotates the active image clockwise by 0.5 degrees.
        """
        active_image = self.get_active_image()
        if not active_image:
            return
        active_image.angle = (active_image.angle + 0.5) % 360
        logging.info(f"Rotated image '{active_image.name}' clockwise by 0.5 degrees.")
        self.draw_images()

    def fine_rotate_counterclockwise(self):
        """
        Rotates the active image counterclockwise by 0.5 degrees.
        """
        active_image = self.get_active_image()
        if not active_image:
            return
        active_image.angle = (active_image.angle - 0.5) % 360
        logging.info(f"Rotated image '{active_image.name}' counterclockwise by 0.5 degrees.")
        self.draw_images()

    ####################################################################################################################################################################################
    ###                                                             --- Centering Methods ---                                                                                       ###
    ####################################################################################################################################################################################
    def center_ruler_image(self):
        """
        Centers the Ruler image on the canvas, shifted 156 pixels to the right and 100 pixels down.
        """
        if "Ruler" in self.images:
            self.image_window.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            ruler_image = self.images["Ruler"]
            ruler_image.offset_x = (canvas_width / 2) + 156  # Shift 156 pixels to the right
            ruler_image.offset_y = (canvas_height / 2) + 100  # Shift 100 pixels down

    def center_normal_image(self):
        """
        Centers the Normal image on the canvas, shifted 156 pixels to the right and 100 pixels down.
        """
        if "Normal" in self.images:
            self.image_window.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            normal_image = self.images["Normal"]
            normal_image.offset_x = (canvas_width / 2) + 156  # Shift 156 pixels to the right
            normal_image.offset_y = (canvas_height / 2) + 100  # Shift 100 pixels down

    def center_tapered_image(self):
        """
        Centers the Tapered image on the canvas, shifted 156 pixels to the right and 100 pixels down.
        """
        if "Tapered" in self.images:
            self.image_window.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            tapered_image = self.images["Tapered"]
            tapered_image.offset_x = (canvas_width / 2) + 156  # Shift 156 pixels to the right
            tapered_image.offset_y = (canvas_height / 2) + 100  # Shift 100 pixels down

    def center_ovoide_image(self):
        """
        Centers the Ovoide image on the canvas, shifted 156 pixels to the right and 100 pixels down.
        """
        if "Ovoide" in self.images:
            self.image_window.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            ovoide_image = self.images["Ovoide"]
            ovoide_image.offset_x = (canvas_width / 2) + 156  # Shift 156 pixels to the right
            ovoide_image.offset_y = (canvas_height / 2) + 100  # Shift 100 pixels down

    def center_narrow_tapered_image(self):
        """
        Centers the Narrow Tapered image on the canvas, shifted 156 pixels to the right and 100 pixels down.
        """
        if "Narrow Tapered" in self.images:
            self.image_window.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            narrow_tapered_image = self.images["Narrow Tapered"]
            narrow_tapered_image.offset_x = (canvas_width / 2) + 156  # Shift 156 pixels to the right
            narrow_tapered_image.offset_y = (canvas_height / 2) + 100  # Shift 100 pixels down

    def center_narrow_ovoide_image(self):
        """
        Centers the Narrow Ovoide image on the canvas, shifted 156 pixels to the right and 100 pixels down.
        """
        if "Narrow Ovoide" in self.images:
            self.image_window.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            narrow_ovoide_image = self.images["Narrow Ovoide"]
            narrow_ovoide_image.offset_x = (canvas_width / 2) + 156  # Shift 156 pixels to the right
            narrow_ovoide_image.offset_y = (canvas_height / 2) + 100  # Shift 100 pixels down

    def center_angulation_image(self):
        """
        Centers the Angulation image on the canvas, shifted 156 pixels to the right and 100 pixels down.
        """
        if "Angulation" in self.images:
            self.image_window.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            angulation_image = self.images["Angulation"]
            angulation_image.offset_x = (canvas_width / 2) + 156  # Shift 156 pixels to the right
            angulation_image.offset_y = (canvas_height / 2) + 100  # Shift 100 pixels down

    ####################################################################################################################################################################################
    ###                                                             --- Control Mode Methods ---                                                                                    ###
    ####################################################################################################################################################################################
    def resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)
    
    def toggle_control_mode(self):
        """
        Toggles the control mode, enabling or disabling global WASD keys to move the image.
        """
        if not self.control_mode:
            # Activate control mode
            if self.get_active_image():
                self.control_mode = True
                self.btn_control_mode.config(text="Disable Control")
                self.start_global_key_capture()
                logging.info("Control Mode Enabled.")
            else:
                messagebox.showwarning("No Active Image", "Please select an active image to control.")
        else:
            # Deactivate control mode
            self.control_mode = False
            self.btn_control_mode.config(text="Control Mode")
            self.stop_global_key_capture()
            logging.info("Control Mode Disabled.")

    def start_global_key_capture(self):
        """
        Starts capturing global keyboard inputs to control the active image.
        """
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_global_key_press,
            on_release=self.on_global_key_release
        )
        self.keyboard_listener.start()
        logging.info("Global key capture started without suppression.")

    def stop_global_key_capture(self):
        """
        Stops capturing global keyboard events.
        """
        if hasattr(self, 'keyboard_listener') and self.keyboard_listener is not None:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
            logging.info("Global key capture stopped.")

    def on_global_key_press(self, key):
        """
        Handles global key press events.
        """
        try:
            if key.char == 'w':
                self.move_image('up')
            elif key.char == 's':
                self.move_image('down')
            elif key.char == 'a':
                self.move_image('left')
            elif key.char == 'd':
                self.move_image('right')
            elif key.char == 'c':
                self.rotate_image(-0.5)
            elif key.char == 'z':
                self.rotate_image(0.5)
            elif key.char == 'x':
                self.toggle_rotation_point_mode_thread_safe()
            elif key.char == 'q':
                self.fine_zoom_out_thread_safe()
            elif key.char == 'e' and self.alt_pressed:
                self.fine_zoom_in_thread_safe()
        except AttributeError:
            # Handle special keys
            if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                self.alt_pressed = True

    def on_global_key_release(self, key):
        """
        Handles global key release events.
        """
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            self.alt_pressed = False

    def rotate_image(self, angle_increment):
        """
        Rotates the active image by the given angle increment.
        """
        self.canvas.after(0, self._rotate_image_main_thread, angle_increment)

    def _rotate_image_main_thread(self, angle_increment):
        active_image = self.get_active_image()
        if not active_image:
            return
        active_image.angle = (active_image.angle + angle_increment) % 360
        logging.info(f"Rotated image '{active_image.name}' by {angle_increment} degrees.")
        self.draw_images()

    def fine_zoom_in_thread_safe(self):
        self.canvas.after(0, self.fine_zoom_in)

    def fine_zoom_out_thread_safe(self):
        self.canvas.after(0, self.fine_zoom_out)

    def toggle_rotation_point_mode_thread_safe(self):
        self.canvas.after(0, self.toggle_rotation_point_mode)

    def move_image(self, direction):
        """
        Moves the active image in the specified direction.
        """
        self.canvas.after(0, self._move_image_main_thread, direction)

    def _move_image_main_thread(self, direction):
        active_image = self.get_active_image()
        if not active_image:
            return

        move_amount = 3  # Pixels to move per key press

        if direction == 'up':
            active_image.offset_y -= move_amount
        elif direction == 'down':
            active_image.offset_y += move_amount
        elif direction == 'left':
            active_image.offset_x -= move_amount
        elif direction == 'right':
            active_image.offset_x += move_amount

        logging.info(f"Moved image '{active_image.name}' {direction} by {move_amount} pixels.")

        self.draw_images()

    ####################################################################################################################################################################################
    ###                                                             --- Application Exit Method ---                                                                                  ###
    ####################################################################################################################################################################################
    def on_close(self):
        """
        Handles the closing of the application.
        """
        # Close all additional windows
        for window in self.additional_windows:
            window.destroy()
        # Stop control mode if active
        if self.control_mode:
            self.stop_global_key_capture()
        # Stop global hotkey listener
        if hasattr(self, 'global_hotkey_listener'):
            self.global_hotkey_listener.stop()
        self.root.destroy()
        sys.exit(0)

    ####################################################################################################################################################################################
    ###                                                             --- User Image Loading Method ---                                                                              ###
    ####################################################################################################################################################################################
    def load_user_image(self):
        """
        Loads a user-selected image and adds it to the application.
        Prompts the user to enter a unique name for the image.
        """
        filepath = filedialog.askopenfilename(
            initialdir=self.images_dir,
            title="Select Image",
            filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.bmp;*.svg")]
        )
        if filepath:
            image_original = self.open_image_file(filepath)
            if image_original:
                # Prompt user for a unique image name
                default_name = os.path.splitext(os.path.basename(filepath))[0]
                image_name = simpledialog.askstring("Image Name", "Enter a unique name for the image:", initialvalue=default_name)
                if image_name:
                    # Ensure the name is unique
                    original_name = image_name
                    counter = 1
                    while image_name in self.images:
                        image_name = f"{original_name}_{counter}"
                        counter += 1
                    # Create and store the image state
                    image_state = ImageState(image_original, image_name)
                    self.images[image_name] = image_state
                    self.active_image_name = image_name
                    self.update_active_image_menu()
                    self.active_image_var.set(image_name)
                    self.draw_images()

                    logging.info(f"User-loaded image '{image_name}' loaded from '{filepath}'.")

                    if not self.image_window_visible:
                        self.toggle_image_window()
                else:
                    messagebox.showwarning("Name Required", "Image name is required to load the image.")
            else:
                messagebox.showerror("Load Failed", "Failed to load the selected image.")

    ####################################################################################################################################################################################
    ###                                                             --- Additional Image Loading Methods ---                                                                         ###
    ####################################################################################################################################################################################
    # You can add methods to load other default images similarly, if needed.

    ####################################################################################################################################################################################
    ###                                                             --- Run Method ---                                                                                               ###
    ####################################################################################################################################################################################

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageOverlayApp(root)
    root.mainloop()
