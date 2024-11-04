import tkinter as tk
from tkinter import messagebox
from pynput import keyboard, mouse
import threading
import ctypes
import time

# Global variables to store coordinates
tor_plus_coords = None
tor_minus_coords = None
listener_active = True  # To control the keyboard listener

# Constants for mouse event types
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

def prompt_for_location(button_name):
    messagebox.showinfo("Prompt", f"Please click on the screen to set location for {button_name}")

    # Variable to store coordinates
    coords = None

    # Function to capture mouse click
    def on_click(x, y, button, pressed):
        nonlocal coords
        if pressed:
            coords = (x, y)
            return False  # Stop listener

    # Hide the root window temporarily
    root.withdraw()
    # Start a mouse listener
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()
    # Show the root window again
    root.deiconify()

    # After the listener has stopped, update the coordinates and show confirmation in the main thread
    if coords:
        if button_name == 'Tor+':
            global tor_plus_coords
            tor_plus_coords = coords
        elif button_name == 'Tor-':
            global tor_minus_coords
            tor_minus_coords = coords
        messagebox.showinfo("Confirmation", f"{button_name} coordinates set to: {coords}")
        print(f"{button_name} coordinates set to: {coords}")
    else:
        messagebox.showerror("Error", "No coordinates captured.")

def tor_plus_action():
    prompt_for_location('Tor+')

def tor_minus_action():
    prompt_for_location('Tor-')

def suspend_action():
    global listener_active
    listener_active = not listener_active
    status = "Suspended" if not listener_active else "Active"
    suspend_button.config(text=f"Resume" if not listener_active else "Suspend")
    print(f"Listener {status}")

def perform_phantom_click(x, y):
    # Get screen size
    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)

    # Convert coordinates to absolute values
    abs_x = int(x * 65536 / screen_width)
    abs_y = int(y * 65536 / screen_height)

    # Create INPUT structure
    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_long),
                    ("dy", ctypes.c_long),
                    ("mouseData", ctypes.c_ulong),
                    ("dwFlags", ctypes.c_ulong),
                    ("time", ctypes.c_ulong),
                    ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

    class INPUT(ctypes.Structure):
        class _INPUT(ctypes.Union):
            _fields_ = [("mi", MOUSEINPUT)]
        _anonymous_ = ("_input",)
        _fields_ = [("type", ctypes.c_ulong),
                    ("_input", _INPUT)]

    # Simulate mouse down and up at the given coordinates without moving the cursor
    inputs = []

    # Mouse down event
    mi_down = MOUSEINPUT(dx=abs_x, dy=abs_y, mouseData=0,
                         dwFlags=MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_LEFTDOWN,
                         time=0, dwExtraInfo=None)
    inputs.append(INPUT(type=0, mi=mi_down))

    # Mouse up event
    mi_up = MOUSEINPUT(dx=abs_x, dy=abs_y, mouseData=0,
                       dwFlags=MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_LEFTUP,
                       time=0, dwExtraInfo=None)
    inputs.append(INPUT(type=0, mi=mi_up))

    # Send input
    nInputs = len(inputs)
    LPINPUT = INPUT * nInputs
    pInputs = LPINPUT(*inputs)
    ctypes.windll.user32.SendInput(nInputs, pInputs, ctypes.sizeof(INPUT))

def perform_click(button_name):
    if button_name == 'Tor+' and tor_plus_coords:
        coords = tor_plus_coords
    elif button_name == 'Tor-' and tor_minus_coords:
        coords = tor_minus_coords
    else:
        print(f"No coordinates set for {button_name}.")
        return

    # Perform phantom click without moving the cursor
    perform_phantom_click(coords[0], coords[1])
    print(f"Phantom click at {coords} ({button_name})")

def start_keyboard_listener():
    def on_activate_tor_plus():
        if listener_active:
            perform_click('Tor+')

    def on_activate_tor_minus():
        if listener_active:
            perform_click('Tor-')

    # Define hotkeys
    hotkeys = keyboard.GlobalHotKeys({
        '<ctrl>+<shift>+e': on_activate_tor_plus,
        '<ctrl>+<shift>+q': on_activate_tor_minus
    })

    def run_hotkeys():
        with hotkeys:
            hotkeys.join()
    threading.Thread(target=run_hotkeys, daemon=True).start()

# Set up the GUI
root = tk.Tk()
root.title("Mouse Clicker")

# Set the window size (e.g., 300x200) and make it resizable
root.geometry('300x200')
root.resizable(True, True)

# Center the window on the screen
root.update_idletasks()
width = root.winfo_width()
height = root.winfo_height()
x = (root.winfo_screenwidth() // 2) - (width // 2)
y = (root.winfo_screenheight() // 2) - (height // 2)
root.geometry(f'{width}x{height}+{x}+{y}')

# Create buttons with some padding
tor_plus_button = tk.Button(root, text="Tor+", command=tor_plus_action, width=15, height=2)
tor_plus_button.pack(pady=10)

tor_minus_button = tk.Button(root, text="Tor-", command=tor_minus_action, width=15, height=2)
tor_minus_button.pack(pady=10)

suspend_button = tk.Button(root, text="Suspend", command=suspend_action, width=15, height=2)
suspend_button.pack(pady=10)

# Start the keyboard listener in a separate thread
start_keyboard_listener()

root.mainloop()
