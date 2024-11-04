import tkinter as tk
from tkinter import messagebox
import threading
import ctypes
import keyboard  # For global keyboard events

# Global variables to store coordinates
tor_plus_coords = None
tor_minus_coords = None
listener_active = True  # To control the keyboard listener
click_mode = 'phantom'   # 'phantom' or 'mouse'

# Constants for mouse event types
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

def make_click_through(hwnd):
    # Make the window transparent and click-through
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x80000
    WS_EX_TRANSPARENT = 0x20
    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
    # Set window transparency to fully transparent
    LWA_ALPHA = 0x2
    ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 0, LWA_ALPHA)

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

    # Hide the control window temporarily
    control_window.withdraw()
    # Start a mouse listener
    from pynput import mouse
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()
    # Show the control window again
    control_window.deiconify()

    # After the listener has stopped, update the coordinates and show confirmation
    if coords:
        global tor_plus_coords, tor_minus_coords
        if button_name == 'Tor+':
            tor_plus_coords = coords
        elif button_name == 'Tor-':
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

def toggle_mode():
    global click_mode
    if click_mode == 'phantom':
        click_mode = 'mouse'
    else:
        click_mode = 'phantom'
    mode_button.config(text=f"Mode: {click_mode.capitalize()}")
    print(f"Click mode set to {click_mode}")

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
                    ("dwExtraInfo", ctypes.c_void_p)]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", ctypes.c_ulong),
                    ("mi", MOUSEINPUT)]

    # Mouse down event
    mi_down = MOUSEINPUT(dx=abs_x, dy=abs_y, mouseData=0,
                         dwFlags=MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_LEFTDOWN,
                         time=0, dwExtraInfo=None)
    input_down = INPUT(type=ctypes.c_ulong(0), mi=mi_down)

    # Mouse up event
    mi_up = MOUSEINPUT(dx=abs_x, dy=abs_y, mouseData=0,
                       dwFlags=MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_LEFTUP,
                       time=0, dwExtraInfo=None)
    input_up = INPUT(type=ctypes.c_ulong(0), mi=mi_up)

    # Send inputs
    inputs = [input_down, input_up]
    nInputs = len(inputs)
    LPINPUT = INPUT * nInputs
    pInputs = LPINPUT(*inputs)
    ctypes.windll.user32.SendInput(nInputs, pInputs, ctypes.sizeof(INPUT))

    print(f"Phantom click at ({x}, {y})")

def perform_mouse_click(x, y):
    # Move cursor
    ctypes.windll.user32.SetCursorPos(int(x), int(y))

    # Mouse down
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    # Mouse up
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    print(f"Mouse moved and clicked at ({x}, {y})")

def perform_click(button_name):
    global tor_plus_coords, tor_minus_coords
    if button_name == 'Tor+' and tor_plus_coords:
        coords = tor_plus_coords
    elif button_name == 'Tor-' and tor_minus_coords:
        coords = tor_minus_coords
    else:
        print(f"No coordinates set for {button_name}.")
        return

    if click_mode == 'phantom':
        # Perform phantom click without moving the cursor
        perform_phantom_click(coords[0], coords[1])
    elif click_mode == 'mouse':
        # Move mouse and click
        perform_mouse_click(coords[0], coords[1])
    else:
        print(f"Unknown click mode: {click_mode}")

def start_keyboard_listener():
    def on_key_event(event):
        if listener_active:
            if event.name == '1' and keyboard.is_pressed('ctrl'):
                perform_click('Tor+')
            elif event.name == '2' and keyboard.is_pressed('ctrl'):
                perform_click('Tor-')
    # Start listening for key events
    threading.Thread(target=lambda: keyboard.on_press(on_key_event), daemon=True).start()

# Create the transparent, click-through overlay window
overlay = tk.Tk()
overlay.attributes('-fullscreen', True)
overlay.attributes('-topmost', True)
overlay.overrideredirect(True)  # Remove title bar
overlay.configure(bg='black')
overlay.wm_attributes('-alpha', 0.0)  # Fully transparent

hwnd_overlay = overlay.winfo_id()
make_click_through(hwnd_overlay)

# Create the control window
control_window = tk.Toplevel()
control_window.title("Mouse Clicker")
control_window.attributes('-topmost', True)

# Set the window size and position
control_window.geometry('300x250+50+50')  # You can adjust the position as needed
control_window.resizable(False, False)

# Create buttons with some padding
tor_plus_button = tk.Button(control_window, text="Tor+", command=tor_plus_action, width=15, height=2)
tor_plus_button.pack(pady=5)

tor_minus_button = tk.Button(control_window, text="Tor-", command=tor_minus_action, width=15, height=2)
tor_minus_button.pack(pady=5)

suspend_button = tk.Button(control_window, text="Suspend", command=suspend_action, width=15, height=2)
suspend_button.pack(pady=5)

mode_button = tk.Button(control_window, text=f"Mode: {click_mode.capitalize()}", command=toggle_mode, width=15, height=2)
mode_button.pack(pady=5)

# Start the keyboard listener in a separate thread
start_keyboard_listener()

# Start the Tkinter event loop in a separate thread
def run_tk():
    overlay.mainloop()

threading.Thread(target=run_tk, daemon=True).start()

control_window.mainloop()
