# main.py

import tkinter as tk
from controllers.image_manager import ImageManager
from views.buttons_window import ButtonsWindow
from views.image_window import ImageWindow
import logging
from logging.handlers import RotatingFileHandler
import sys

class ImageOverlayApp:
    """
    Main application class that initializes and coordinates all components.
    """

    def __init__(self, root):
        self.root = root

        # Configure logging with rotation
        self.setup_logging()

        # Initialize Controllers as Attributes
        self.image_manager = ImageManager(self)

        # Initialize Views as Attributes
        self.buttons_window = ButtonsWindow(self)
        self.image_window = ImageWindow(self)

        # Bind mouse wheel events to canvas
        self.image_window.bind_events()

        logging.info("Image Overlay Application started.")

    def setup_logging(self):
        """
        Sets up the logging configuration.
        """
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)  # Change to DEBUG for more detailed logs

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # File handler with rotation
        file_handler = RotatingFileHandler("app.log", maxBytes=5*1024*1024, backupCount=2)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Stream handler for console output
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    def on_close(self):
        """
        Handles the closing of the application.
        """
        logging.info("Application is closing.")
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageOverlayApp(root)
    root.mainloop()
