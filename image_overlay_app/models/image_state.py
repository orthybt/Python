# models/image_state.py

from PIL import Image

class ImageState:
    """
    Represents the state of an individual image.
    """
    def __init__(self, image: Image.Image, name: str):
        self.image_original = image  # Original PIL Image
        self.name = name  # Name identifier
        self.scale = 1.0  # Scale factor
        self.scale_log = 0  # Logarithmic scale for smooth zoom
        self.angle = 0.0  # Rotation angle
        self.is_flipped_horizontally = False  # Flip status
        self.is_flipped_vertically = False  # Flip status
        self.offset_x = 0  # X offset on canvas
        self.offset_y = 0  # Y offset on canvas
        self.visible = True  # Visibility status
        self.rotation_point = None  # (x, y) tuple
        self.image_transparency_level = 1.0  # Transparency (1.0 = opaque)
        self.position_history = []  # Stack for undo
        self.redo_stack = []  # Stack for redo
        self.photo_image = None  # Reference to ImageTk.PhotoImage to prevent garbage collection
        # Attributes for dragging
        self.drag_start_x = None
        self.drag_start_y = None
