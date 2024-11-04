# utils/image_utils.py

import os
from PIL import Image
import cairosvg
import logging
from tkinter import messagebox
from io import BytesIO

def open_image_file(filepath):
    """
    Opens an image file and returns a PIL Image object.
    Supports SVG by converting it to PNG in memory.
    """
    try:
        file_ext = os.path.splitext(filepath)[1].lower()
        if file_ext == '.svg':
            # Convert SVG to PNG using cairosvg and load into PIL from memory
            png_data = cairosvg.svg2png(url=filepath)
            image = Image.open(BytesIO(png_data)).convert("RGBA")
            image.load()  # Ensure the image is fully loaded
            logging.info(f"Converted SVG to PNG: {filepath}")
            return image
        else:
            # Open other image formats directly
            image = Image.open(filepath).convert("RGBA")
            image.load()  # Ensure the image is fully loaded
            logging.info(f"Opened image file: {filepath}")
            return image
    except cairosvg.CairoSVGError as e:
        logging.error(f"CairoSVG error while converting '{filepath}': {e}")
        messagebox.showerror(
            "SVG Conversion Error",
            f"Failed to convert SVG to PNG:\n{filepath}\n\nError: {e}"
        )
    except FileNotFoundError:
        logging.error(f"File not found: '{filepath}'")
        messagebox.showerror(
            "File Not Found",
            f"The file '{filepath}' does not exist."
        )
    except PermissionError:
        logging.error(f"Permission denied when accessing '{filepath}'")
        messagebox.showerror(
            "Permission Denied",
            f"Permission denied when accessing '{filepath}'."
        )
    except Exception as e:
        logging.error(f"Unexpected error opening image file '{filepath}': {e}")
        messagebox.showerror(
            "Image Load Error",
            f"Failed to open image:\n{filepath}\n\nError: {e}"
        )
    return None
