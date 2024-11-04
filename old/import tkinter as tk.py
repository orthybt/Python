import tkinter as tk
from PIL import Image, ImageTk

# Initialize the main window
root = tk.Tk()

# Load the image
image = Image.open('C:\Users\User\Desktop\Python\Images\WorkOrder.png')  # Replace with your image file
bg_image = ImageTk.PhotoImage(image)

# Create a canvas
canvas = tk.Canvas(root, width=image.width, height=image.height)
canvas.pack()

# Display the background image
canvas.create_image(0, 0, anchor='nw', image=bg_image)

# Function for button click
def on_button_click():
    print("Button clicked!")

# Add a button
button = tk.Button(root, text="Click Me", command=on_button_click)
canvas.create_window(100, 150, anchor='nw', window=button)

# Add more widgets as needed
# Example: Adding a label
label = tk.Label(root, text="Enter your name:")
canvas.create_window(100, 200, anchor='nw', window=label)

# Example: Adding an entry field
entry = tk.Entry(root)
canvas.create_window(220, 200, anchor='nw', window=entry)

# Run the application
root.mainloop()
