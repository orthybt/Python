import subprocess
import tkinter as tk
from tkinter import Button, Toplevel, Scale, filedialog, HORIZONTAL
from PIL import Image, ImageTk
import os

# Define paths to the uploaded scripts
script1_path = "C:/Users/User/Desktop/Python/maestro6.py"
script2_path = "C:/Users/User/Desktop/Python/ImageOverlayWork.py"


# Main application class
class OverlayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Script Launcher with Overlay")
        self.root.geometry("600x400")

        # Button to open the first script (maestro6.py)
        self.button1 = Button(root, text="Run Maestro6 Script", command=self.run_script1)
        self.button1.pack(pady=20)

        # Button to open the second script (ImageOverlayWork.py)
        self.button2 = Button(root, text="Run ImageOverlayWork Script", command=self.run_script2)
        self.button2.pack(pady=20)

        # Button to load an image as overlay
        self.overlay_button = Button(root, text="Load Overlay Image", command=self.load_overlay)
        self.overlay_button.pack(pady=20)

        # Placeholder for overlay image
        self.overlay_image = None
        self.overlay_label = None

        # Transparency control for overlay image
        self.transparency_scale = Scale(root, from_=0, to=100, orient=HORIZONTAL, label="Transparency")
        self.transparency_scale.pack(pady=10)
        self.transparency_scale.set(100)
        self.transparency_scale.bind("<Motion>", self.update_transparency)

    def run_script1(self):
        # Run the maestro6.py script in a subprocess
        subprocess.Popen(["python3", script1_path])

    def run_script2(self):
        # Run the ImageOverlayWork.py script in a subprocess
        subprocess.Popen(["python3", script2_path])

    def load_overlay(self):
        # Open file dialog to select an image for overlay
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if file_path:
            # Load and display the overlay image
            img = Image.open(file_path)
            img = img.resize((self.root.winfo_width(), self.root.winfo_height()))
            self.overlay_image = ImageTk.PhotoImage(img)
            if not self.overlay_label:
                self.overlay_label = Toplevel(self.root)
                self.overlay_label.wm_attributes("-topmost", True)
                self.overlay_label.overrideredirect(1)
            label = tk.Label(self.overlay_label, image=self.overlay_image)
            label.pack()
            self.update_transparency(None)  # Initialize transparency

    def update_transparency(self, event):
        # Adjust transparency of overlay
        if self.overlay_label:
            alpha = self.transparency_scale.get() / 100
            self.overlay_label.attributes("-alpha", alpha)

# Create and run the application
root = tk.Tk()
app = OverlayApp(root)
root.mainloop()
