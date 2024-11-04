import sys
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import io
import cairosvg  # For SVG support
import math

class ImageState:
    def __init__(self, image_original, name):
        self.image_original = image_original
        self.image_display = None
        self.name = name
        self.visible = True
        self.angle = 0
        self.scale = 1.0
        self.scale_log = 0
        self.offset_x = 512
        self.offset_y = 512
        self.is_flipped_horizontally = False
        self.is_flipped_vertically = False
        self.rotation_point = None
        self.image_transparency_level = 1.0

        # Undo/Redo stacks for position
        self.position_history = []
        self.redo_stack = []

class ImageOverlayApp:
    def __init__(self, root):
        # Initialize the main window and set attributes
        self.root = root
        self.root.title("Controls")
        self.transparency_level = 1.0  # Fully opaque (buttons window)
        self.image_window_visible = True

        self.images = {}  # Store ImageState objects
        self.active_image_name = None  # Name of the active image

        self.start_x = 0
        self.start_y = 0
        self.is_dragging = False
        self.is_rotation_point_mode = False  # Rotation point selection mode

        # Setup main window (buttons window)
        self.setup_buttons_window()

        # Setup image window
        self.setup_image_window()

        # Initialize transparency button
        self.update_transparency_button()

    def setup_buttons_window(self):
        # Remove the fixed position to allow moving the window freely
        self.root.attributes('-topmost', True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Create a frame to organize buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(padx=10, pady=10, fill='both', expand=True)

        # Buttons for controlling buttons window transparency
        btn_increase_buttons_transparency = tk.Button(
            btn_frame, text="Increase Buttons Transparency", command=self.increase_buttons_transparency)
        btn_increase_buttons_transparency.grid(row=0, column=0, pady=5, sticky='ew')

        btn_decrease_buttons_transparency = tk.Button(
            btn_frame, text="Decrease Buttons Transparency", command=self.decrease_buttons_transparency)
        btn_decrease_buttons_transparency.grid(row=0, column=1, pady=5, sticky='ew')

        # Toggle transparency button
        self.btn_toggle_transparency = tk.Button(
            btn_frame, text="Set Transparency to Min", command=self.toggle_transparency)
        self.btn_toggle_transparency.grid(row=1, column=0, columnspan=2, pady=5, sticky='ew')

        # Other control buttons
        load_hide_row = 2

        btn_load_image = tk.Button(
            btn_frame, text="Load 1st Image", command=lambda: self.load_image("First Image"))
        btn_load_image.grid(row=load_hide_row, column=0, pady=5, sticky='ew')

        btn_load_second_image = tk.Button(
            btn_frame, text="Add 2nd Image", command=lambda: self.load_image("Second Image"))
        btn_load_second_image.grid(row=load_hide_row, column=1, pady=5, sticky='ew')

        self.btn_hide_show_image = tk.Button(
            btn_frame, text="Hide Image Window", command=self.toggle_image_window)
        self.btn_hide_show_image.grid(row=load_hide_row + 1, column=0, columnspan=2, pady=5, sticky='ew')

        # Flip buttons
        flip_row = load_hide_row + 2

        btn_flip_horizontal = tk.Button(
            btn_frame, text="Flip Horizontal", command=self.flip_image_horizontal)
        btn_flip_horizontal.grid(row=flip_row, column=0, pady=5, sticky='ew')

        btn_flip_vertical = tk.Button(
            btn_frame, text="Flip Vertical", command=self.flip_image_vertical)
        btn_flip_vertical.grid(row=flip_row, column=1, pady=5, sticky='ew')

        # Set Rotation Point button
        set_rotation_point_row = flip_row + 1

        self.btn_set_rotation_point = tk.Button(
            btn_frame, text="Set Rotation Point", command=self.toggle_rotation_point_mode)
        self.btn_set_rotation_point.grid(row=set_rotation_point_row, column=0, columnspan=2, pady=5, sticky='ew')

        # Zoom Level buttons
        zoom_buttons_row = set_rotation_point_row + 1

        btn_zoom_in = tk.Button(
            btn_frame, text="+", command=self.zoom_in)
        btn_zoom_in.grid(row=zoom_buttons_row, column=0, pady=5, sticky='ew')

        btn_zoom_out = tk.Button(
            btn_frame, text="-", command=self.zoom_out)
        btn_zoom_out.grid(row=zoom_buttons_row, column=1, pady=5, sticky='ew')

        # New High-Sensitivity Zoom Buttons
        high_zoom_buttons_row = zoom_buttons_row + 1

        btn_zoom_in_more = tk.Button(
            btn_frame, text="++", command=self.zoom_in_more)
        btn_zoom_in_more.grid(row=high_zoom_buttons_row, column=0, pady=5, sticky='ew')

        btn_zoom_out_more = tk.Button(
            btn_frame, text="--", command=self.zoom_out_more)
        btn_zoom_out_more.grid(row=high_zoom_buttons_row, column=1, pady=5, sticky='ew')

        # Undo/Redo buttons
        undo_redo_row = high_zoom_buttons_row + 1

        self.btn_undo_move = tk.Button(
            btn_frame, text="Undo Move", command=self.undo_move, state='disabled')
        self.btn_undo_move.grid(row=undo_redo_row, column=0, pady=5, sticky='ew')

        self.btn_redo_move = tk.Button(
            btn_frame, text="Redo Move", command=self.redo_move, state='disabled')
        self.btn_redo_move.grid(row=undo_redo_row, column=1, pady=5, sticky='ew')

        # Active Image Selection
        active_image_row = undo_redo_row + 1

        tk.Label(btn_frame, text="Select Active Image:").grid(row=active_image_row, column=0, pady=5, sticky='e')

        self.active_image_var = tk.StringVar(value="")
        self.active_image_menu = tk.OptionMenu(
            btn_frame, self.active_image_var, "", command=self.change_active_image)
        self.active_image_menu.grid(row=active_image_row, column=1, pady=5, sticky='ew')

        # Image Visibility Checkboxes
        visibility_row = active_image_row + 1

        self.first_image_visibility_var = tk.IntVar(value=1)
        self.second_image_visibility_var = tk.IntVar(value=1)

        self.chk_first_image_visibility = tk.Checkbutton(
            btn_frame, text="Show 1st Image", variable=self.first_image_visibility_var,
            command=lambda: self.toggle_image_visibility("First Image"))
        self.chk_first_image_visibility.grid(row=visibility_row, column=0, pady=5, sticky='w')

        self.chk_second_image_visibility = tk.Checkbutton(
            btn_frame, text="Show 2nd Image", variable=self.second_image_visibility_var,
            command=lambda: self.toggle_image_visibility("Second Image"))
        self.chk_second_image_visibility.grid(row=visibility_row, column=1, pady=5, sticky='w')

        # Configure grid weights for equal button sizes
        for i in range(2):
            btn_frame.columnconfigure(i, weight=1)

        # Calculate total number of rows
        total_rows = visibility_row + 1  # Adjust based on the last row used

        # Configure row weights
        for i in range(total_rows):
            btn_frame.rowconfigure(i, weight=1)

        # Set the transparency of the buttons window
        self.root.attributes('-alpha', self.transparency_level)

    def setup_image_window(self):
        self.image_window = tk.Toplevel(self.root)
        self.image_window.title("Image Window")
        self.image_window.geometry("1600x1024")
        # Remove window decorations
        self.image_window.overrideredirect(True)
        # Set window to be transparent using grey
        self.image_window.attributes('-transparentcolor', 'grey')

        # Center the window on the screen
        screen_width = self.image_window.winfo_screenwidth()
        screen_height = self.image_window.winfo_screenheight()
        x = (screen_width // 2) - (1600 // 2)
        y = (screen_height // 2) - (1024 // 2)
        self.image_window.geometry(f"+{x}+{y}")
        self.image_window.attributes('-topmost', True)
        self.image_window.protocol("WM_DELETE_WINDOW", self.on_close)

        # Create the canvas with grey background
        self.canvas = tk.Canvas(self.image_window, width=1600, height=1024,
                                bg='grey', highlightthickness=0, borderwidth=0)
        self.canvas.pack()

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_click)
        if sys.platform.startswith('win'):
            self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        elif sys.platform == 'darwin':
            self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        else:
            self.canvas.bind("<Button-4>", lambda event: self.on_mouse_wheel(event))
            self.canvas.bind("<Button-5>", lambda event: self.on_mouse_wheel(event))
        self.canvas.bind("<Button-3>", self.on_right_click)

    def zoom_in(self):
        active_image = self.get_active_image()
        if not active_image:
            return
        active_image.scale += 0.05
        active_image.scale = min(active_image.scale, 10.0)
        active_image.scale_log = math.log2(active_image.scale)
        self.draw_images()

    def zoom_out(self):
        active_image = self.get_active_image()
        if not active_image:
            return
        active_image.scale -= 0.05
        active_image.scale = max(active_image.scale, 0.1)
        active_image.scale_log = math.log2(active_image.scale)
        self.draw_images()

    def zoom_in_more(self):
        active_image = self.get_active_image()
        if not active_image:
            return
        # Increase the scale by a larger amount
        active_image.scale += 0.2
        active_image.scale = min(active_image.scale, 10.0)
        active_image.scale_log = math.log2(active_image.scale)
        self.draw_images()

    def zoom_out_more(self):
        active_image = self.get_active_image()
        if not active_image:
            return
        # Decrease the scale by a larger amount
        active_image.scale -= 0.2
        active_image.scale = max(active_image.scale, 0.1)
        active_image.scale_log = math.log2(active_image.scale)
        self.draw_images()

    # ... [Remaining methods remain unchanged]

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageOverlayApp(root)
    root.mainloop()