import customtkinter as ctk
from downloader import DownloadManager
from ui_controller import UIController
from utilities import MyLogger
import os
import sys
from PIL import Image, ImageTk

class UniversalDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Universal Downloader")
        self.geometry("500x420")
        self.resizable(False, False)
        
        # macOS-specific icon setup (only runs on macOS)
        if sys.platform == "darwin":
            # Try .png first (most compatible), then .icns, then .ico as fallback
            for icon_ext in [".png", ".icns", ".ico"]:
                icon_path = os.path.join(os.path.dirname(__file__), 'assets', f'icon{icon_ext}')
                if os.path.exists(icon_path):
                    try:
                        img = Image.open(icon_path)
                        photo = ImageTk.PhotoImage(img)
                        self.iconphoto(False, photo)
                        # Keep reference to prevent garbage collection
                        self._icon_reference = photo
                        break  # Stop after first valid icon
                    except Exception as e:
                        print(f"Icon failed to load: {e}")
        
        # Initialize UI controller
        self.controller = UIController(self, DownloadManager(), MyLogger())

    def show_popup(self, title, success, error_detail=None):
        self.controller.show_popup(title, success, error_detail)

if __name__ == "__main__":
    app = UniversalDownloader()
    app.mainloop()
