import sys
import math
import io
import os
import tkinter as tk
from tkinter import filedialog, colorchooser, simpledialog, messagebox
from PIL import Image, ImageTk, ImageFont, ImageDraw
import cairosvg  # For SVG support


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
        self.image_transparency_level = 1.0

        # Undo/Redo stacks for position
        self.position_history = []
        self.redo_stack = []


class ImageOverlayApp:
    """
    Main application class that handles image loading, transformations,
    and user interactions through the GUI.
    """

    def __init__(self, parent):
        self.root = tk.Toplevel(parent)
        self.root.title("Controls")
        self.transparency_level = 1.0  # Fully opaque (buttons window)
        self.image_window_visible = False  # Start with the image window hidden

        # Dictionary to store ImageState objects
        self.images = {}
        self.active_image_name = None  # Name of the active image

        # Mouse event variables
        self.start_x = 0
        self.start_y = 0
        self.is_dragging = False
        self.is_rotation_point_mode = False  # Rotation point selection mode

        # Additional windows
        self.additional_windows = []
        self.brainstorm_window = None  # Track the brainstorm window

        # Initialize the GUI
        self.setup_buttons_window()
        self.setup_image_window()
        self.update_transparency_button()
        self.load_default_brainstorm_image()

        # Hide the image window by default
        self.image_window.withdraw()
        self.btn_hide_show_image.config(text="Show Window")

        # Initialize ruler visibility
        self.ruler_visible = False  # Track the visibility of the ruler (third image)

    ############################################
    ### --- Setup Methods --- ###
    ############################################

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

        # Undo/Redo buttons
        self.create_undo_redo_controls(btn_frame)

        # Active image selection
        self.create_active_image_control(btn_frame)

        # Image visibility checkboxes
        self.create_visibility_controls(btn_frame)

        # Button to open/hide brainstorm window
        self.create_brainstorm_window_button(btn_frame)

        # Button to toggle ruler (load/hide default third image)
        self.create_ruler_button(btn_frame)

        # Configure grid weights for equal button sizes
        for i in range(2):
            btn_frame.columnconfigure(i, weight=1)

        # Set the transparency of the buttons window
        self.root.attributes('-alpha', self.transparency_level)

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

        # Bind mouse events
        self.bind_canvas_events()

        # Update canvas size on window resize
        self.image_window.bind('<Configure>', self.on_image_window_resize)

    ############################################
    ### --- Control Creation Methods --- ###
    ############################################

    def create_transparency_controls(self, parent):
        """
        Creates transparency control buttons.
        """
        btn_increase_transparency = tk.Button(
            parent, text="Btns Transp+", command=self.increase_buttons_transparency)
        btn_increase_transparency.grid(row=0, column=0, pady=5, sticky='ew')

        btn_decrease_transparency = tk.Button(
            parent, text="Btns Transp-", command=self.decrease_buttons_transparency)
        btn_decrease_transparency.grid(row=0, column=1, pady=5, sticky='ew')

        # Toggle transparency button
        self.btn_toggle_transparency = tk.Button(
            parent, text="Toggle Transp", command=self.toggle_transparency)
        self.btn_toggle_transparency.grid(row=1, column=0, columnspan=2, pady=5, sticky='ew')

    def create_image_controls(self, parent):
        """
        Creates image loading and window toggling buttons.
        """
        btn_load_image = tk.Button(
            parent, text="Load 1st Img", command=lambda: self.load_image("First Image"))
        btn_load_image.grid(row=2, column=0, pady=5, sticky='ew')

        btn_load_second_image = tk.Button(
            parent, text="Add 2nd Img", command=lambda: self.load_image("Second Image"))
        btn_load_second_image.grid(row=2, column=1, pady=5, sticky='ew')

        self.btn_hide_show_image = tk.Button(
            parent, text="Hide Window", command=self.toggle_image_window)
        self.btn_hide_show_image.grid(row=3, column=0, columnspan=2, pady=5, sticky='ew')

    def create_flip_controls(self, parent):
        """
        Creates flip control buttons.
        """
        btn_flip_horizontal = tk.Button(
            parent, text="Flip H", command=self.flip_image_horizontal)
        btn_flip_horizontal.grid(row=4, column=0, pady=5, sticky='ew')

        btn_flip_vertical = tk.Button(
            parent, text="Flip V", command=self.flip_image_vertical)
        btn_flip_vertical.grid(row=4, column=1, pady=5, sticky='ew')

    def create_rotation_point_control(self, parent):
        """
        Creates rotation point control button.
        """
        self.btn_set_rotation_point = tk.Button(
            parent, text="Set Rot Pt", command=self.toggle_rotation_point_mode)
        self.btn_set_rotation_point.grid(row=5, column=0, columnspan=2, pady=5, sticky='ew')

    def create_zoom_controls(self, parent):
        """
        Creates zoom control buttons.
        """
        btn_zoom_in = tk.Button(
            parent, text="+", command=self.zoom_in)
        btn_zoom_in.grid(row=6, column=0, pady=5, sticky='ew')

        btn_zoom_out = tk.Button(
            parent, text="-", command=self.zoom_out)
        btn_zoom_out.grid(row=6, column=1, pady=5, sticky='ew')

        btn_fine_zoom_in = tk.Button(
            parent, text="+ Fine", command=self.fine_zoom_in)
        btn_fine_zoom_in.grid(row=7, column=0, pady=5, sticky='ew')

        btn_fine_zoom_out = tk.Button(
            parent, text="- Fine", command=self.fine_zoom_out)
        btn_fine_zoom_out.grid(row=7, column=1, pady=5, sticky='ew')

        btn_fine_rotate_clockwise = tk.Button(
            parent, text="Rot +0.5°", command=self.fine_rotate_clockwise)
        btn_fine_rotate_clockwise.grid(row=8, column=0, pady=5, sticky='ew')

        btn_fine_rotate_counterclockwise = tk.Button(
            parent, text="Rot -0.5°", command=self.fine_rotate_counterclockwise)
        btn_fine_rotate_counterclockwise.grid(row=8, column=1, pady=5, sticky='ew')

    def create_undo_redo_controls(self, parent):
        """
        Creates undo and redo buttons.
        """
        self.btn_undo_move = tk.Button(
            parent, text="Undo", command=self.undo_move, state='disabled')
        self.btn_undo_move.grid(row=9, column=0, pady=5, sticky='ew')

        self.btn_redo_move = tk.Button(
            parent, text="Redo", command=self.redo_move, state='disabled')
        self.btn_redo_move.grid(row=9, column=1, pady=5, sticky='ew')

    def create_active_image_control(self, parent):
        """
        Creates active image selection controls.
        """
        tk.Label(parent, text="Active Image:").grid(row=10, column=0, pady=5, sticky='e')

        self.active_image_var = tk.StringVar(value="")
        self.active_image_menu = tk.OptionMenu(
            parent, self.active_image_var, "", command=self.change_active_image)
        self.active_image_menu.grid(row=10, column=1, pady=5, sticky='ew')

    def create_visibility_controls(self, parent):
        """
        Creates image visibility checkboxes.
        """
        self.first_image_visibility_var = tk.IntVar(value=1)
        self.second_image_visibility_var = tk.IntVar(value=1)
        self.third_image_visibility_var = tk.IntVar(value=1)  # Added for third image

        self.chk_first_image_visibility = tk.Checkbutton(
            parent, text="Show 1st", variable=self.first_image_visibility_var,
            command=lambda: self.toggle_image_visibility("First Image")
        )
        self.chk_first_image_visibility.grid(row=11, column=0, pady=5, sticky='w')

        self.chk_second_image_visibility = tk.Checkbutton(
            parent, text="Show 2nd", variable=self.second_image_visibility_var,
            command=lambda: self.toggle_image_visibility("Second Image")
        )
        self.chk_second_image_visibility.grid(row=11, column=1, pady=5, sticky='w')

        self.chk_third_image_visibility = tk.Checkbutton(
            parent, text="Show 3rd", variable=self.third_image_visibility_var,
            command=lambda: self.toggle_image_visibility("Third Image")
        )
        self.chk_third_image_visibility.grid(row=12, column=0, pady=5, sticky='w')

    def create_brainstorm_window_button(self, parent):
        """
        Creates a button to open/hide the brainstorm window.
        """
        self.btn_toggle_brainstorm_window = tk.Button(
            parent, text="Open Brainstorm Window", command=self.toggle_brainstorm_window)
        self.btn_toggle_brainstorm_window.grid(row=13, column=0, columnspan=2, pady=5, sticky='ew')

    def create_ruler_button(self, parent):
        """
        Creates a button to toggle the ruler (load/hide default third image).
        """
        self.btn_open_ruler = tk.Button(
            parent, text="Open Ruler", command=self.toggle_ruler)
        self.btn_open_ruler.grid(row=14, column=0, columnspan=2, pady=5, sticky='ew')

    ############################################
    ### --- Binding Methods --- ###
    ############################################

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

    ############################################
    ### --- Transparency Control Methods --- ###
    ############################################

    def increase_buttons_transparency(self):
        """
        Increases the transparency of the buttons window.
        """
        if self.transparency_level > 0.2:
            self.transparency_level -= 0.1
            self.root.attributes('-alpha', self.transparency_level)

    def decrease_buttons_transparency(self):
        """
        Decreases the transparency of the buttons window.
        """
        if self.transparency_level < 1.0:
            self.transparency_level += 0.1
            self.root.attributes('-alpha', self.transparency_level)

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
        else:
            active_image.image_transparency_level = 1.0
            self.btn_toggle_transparency.config(text="Min Transp")
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

    #############################################
    ### --- Image Loading and Management --- ###
    #############################################

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
            print(f"Error loading image: {e}")
            return None

    def load_default_brainstorm_image(self):
        """
        Loads 'WorkOrder.png' as the default image in the brainstorm window.
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        images_dir = os.path.join(script_dir, 'Images')
        filepath = os.path.join(images_dir, 'WorkOrder.png')
        if os.path.exists(filepath):
            self.default_brainstorm_image_path = filepath
        else:
            print(f"'WorkOrder.png' not found in {images_dir}")
            self.default_brainstorm_image_path = None

    def load_default_third_image(self):
        """
        Loads 'liniar_new_n2.svg' as the third image from the specified directory.
        """
        image_dir = r'C:\Users\User\Desktop\Python\Images'  # Update this path as needed
        filepath = os.path.join(image_dir, 'liniar_new_n2.svg')
        if os.path.exists(filepath):
            image_original = self.open_image_file(filepath)
            if image_original:
                image_state = ImageState(image_original, "Third Image")
                self.images["Third Image"] = image_state
                # Do not change the active image when loading the ruler
                self.update_active_image_menu()
                self.draw_images()

                if not self.image_window_visible:
                    self.toggle_image_window()
        else:
            print(f"'liniar_new_n2.svg' not found in {image_dir}")

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
        self.update_undo_redo_buttons()

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
        self.update_undo_redo_buttons()

    def toggle_image_visibility(self, image_name):
        """
        Toggles the visibility of a specified image.
        """
        image_state = self.images.get(image_name)
        if image_state:
            if image_name == "First Image":
                image_state.visible = bool(self.first_image_visibility_var.get())
            elif image_name == "Second Image":
                image_state.visible = bool(self.second_image_visibility_var.get())
            elif image_name == "Third Image":
                image_state.visible = bool(self.third_image_visibility_var.get())
            self.draw_images()

    def toggle_image_window(self):
        """
        Shows or hides the image window.
        """
        if self.image_window_visible:
            self.image_window.withdraw()
            self.image_window_visible = False
            self.btn_hide_show_image.config(text="Show Window")
        else:
            self.image_window.deiconify()
            self.image_window_visible = True
            self.btn_hide_show_image.config(text="Hide Window")

    def toggle_ruler(self):
        """
        Toggles the visibility of the ruler image.
        """
        if not self.ruler_visible:
            # Load the ruler image if not already loaded
            if "Third Image" not in self.images:
                self.load_default_third_image()
            else:
                # If already loaded, make it visible
                self.images["Third Image"].visible = True
                self.draw_images()
            self.ruler_visible = True
            self.btn_open_ruler.config(text="Hide Ruler")
            # Update the visibility checkbox
            self.third_image_visibility_var.set(1)
        else:
            # Hide the ruler
            if "Third Image" in self.images:
                self.images["Third Image"].visible = False
                self.draw_images()
            self.ruler_visible = False
            self.btn_open_ruler.config(text="Open Ruler")
            # Update the visibility checkbox
            self.third_image_visibility_var.set(0)

    #####################################
    ### --- Image Drawing Methods --- ###
    #####################################

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

    ############################################
    ### --- Mouse and Keyboard Handlers --- ###
    ############################################

    def on_mouse_down(self, event):
        """
        Handles the event when the left mouse button is pressed.
        """
        if not self.is_rotation_point_mode:
            self.is_dragging = True
            self.start_x = event.x_root
            self.start_y = event.y_root

            # Record the initial position for undo
            active_image = self.get_active_image()
            if active_image:
                active_image.position_history.append((active_image.offset_x, active_image.offset_y))
                active_image.redo_stack.clear()
                self.update_undo_redo_buttons()

    def on_mouse_up(self, event):
        """
        Handles the event when the left mouse button is released.
        """
        self.is_dragging = False

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
            else:
                active_image.offset_x += dx
                active_image.offset_y += dy

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

        # Clear undo/redo stacks
        active_image.position_history.clear()
        active_image.redo_stack.clear()
        self.update_undo_redo_buttons()

        self.draw_images()

    #######################################
    ### --- Image Transformation --- ###
    #######################################

    def zoom_in(self):
        """
        Zooms in the active image.
        """
        active_image = self.get_active_image()
        if not active_image:
            return
        active_image.scale = min(active_image.scale + 0.05, 10.0)
        active_image.scale_log = math.log2(active_image.scale)
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
        self.draw_images()

    def flip_image_horizontal(self):
        """
        Flips the active image horizontally.
        """
        active_image = self.get_active_image()
        if not active_image:
            return
        active_image.is_flipped_horizontally = not active_image.is_flipped_horizontally
        self.draw_images()

    def flip_image_vertical(self):
        """
        Flips the active image vertically.
        """
        active_image = self.get_active_image()
        if not active_image:
            return
        active_image.is_flipped_vertically = not active_image.is_flipped_vertically
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
        else:
            self.is_rotation_point_mode = False
            self.btn_set_rotation_point.config(text="Set Rot Pt")
            active_image.rotation_point = None
            self.draw_images()

    ##############################################
    ### --- Fine Rotation Control Methods --- ###
    ##############################################

    def fine_rotate_clockwise(self):
        """
        Rotates the active image clockwise by 0.5 degrees.
        """
        active_image = self.get_active_image()
        if not active_image:
            return
        active_image.angle = (active_image.angle + 0.5) % 360
        self.draw_images()

    def fine_rotate_counterclockwise(self):
        """
        Rotates the active image counterclockwise by 0.5 degrees.
        """
        active_image = self.get_active_image()
        if not active_image:
            return
        active_image.angle = (active_image.angle - 0.5) % 360
        self.draw_images()

    ##################################
    ### --- Undo/Redo Methods --- ###
    ##################################

    def undo_move(self):
        """
        Undoes the last move operation.
        """
        active_image = self.get_active_image()
        if active_image and active_image.position_history:
            # Push the current position onto the redo stack
            active_image.redo_stack.append((active_image.offset_x, active_image.offset_y))
            # Pop the last position from the undo stack
            last_position = active_image.position_history.pop()
            active_image.offset_x, active_image.offset_y = last_position
            self.draw_images()
            self.update_undo_redo_buttons()

    def redo_move(self):
        """
        Redoes the last undone move operation.
        """
        active_image = self.get_active_image()
        if active_image and active_image.redo_stack:
            # Push the current position onto the undo stack
            active_image.position_history.append((active_image.offset_x, active_image.offset_y))
            # Pop the last position from the redo stack
            next_position = active_image.redo_stack.pop()
            active_image.offset_x, active_image.offset_y = next_position
            self.draw_images()
            self.update_undo_redo_buttons()

    def update_undo_redo_buttons(self):
        """
        Updates the state of the undo and redo buttons.
        """
        active_image = self.get_active_image()
        if active_image:
            self.btn_undo_move.config(state='normal' if active_image.position_history else 'disabled')
            self.btn_redo_move.config(state='normal' if active_image.redo_stack else 'disabled')
        else:
            self.btn_undo_move.config(state='disabled')
            self.btn_redo_move.config(state='disabled')

    #########################################
    ### --- Brainstorm Window Methods --- ###
    #########################################

    # You can add the brainstorm window methods here if needed

    #########################################
    ### --- Application Exit Method --- ###
    #########################################

    def on_close(self):
        """
        Handles the closing of the application.
        """
        # Close all additional windows
        for window in self.additional_windows:
            window.destroy()
        self.root.destroy()
