import os
import sys
import customtkinter as ctk

# Create the main window
root = ctk.CTk()
root.title("Universal Downloader")

# Determine icon path for both dev and PyInstaller
if hasattr(sys, '_MEIPASS'):
    # Running as PyInstaller bundle
    icon_path = os.path.join(sys._MEIPASS, "assets", "icon.ico")
else:
    # Running in normal Python environment
    icon_path = os.path.join("assets", "icon.ico")

# Set the window icon (Windows only)
try:
    root.iconbitmap(icon_path)
except Exception as e:
    print(f"[WARNING] Could not set icon: {e}")

# Example window size
root.geometry("600x400")

# Start the GUI loop
root.mainloop()