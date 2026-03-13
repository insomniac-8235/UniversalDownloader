import customtkinter as ctk
from downloader import DownloadManager
from ui_controller import UIController
from utilities import MyLogger, THEME
import os
import sys
from PIL import Image, ImageTk

class UniversalDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("")
        self.geometry("500x400")
        self.resizable(False, False)
        self.configure(bg=THEME["APP_BG"])
        
        # macOS-specific icon setup (only runs on macOS)
        if sys.platform == "darwin":
            for icon_ext in [".png", ".icns", ".ico"]:
                icon_path = os.path.join(os.path.dirname(__file__), 'assets', f'icon{icon_ext}')
                if os.path.exists(icon_path):
                    try:
                        img = Image.open(icon_path)
                        photo = ImageTk.PhotoImage(img)
                        self.iconphoto(False, photo)
                        self._icon_reference = photo
                        break
                    except Exception as e:
                        print(f"Icon failed to load: {e}")
        
        # Initialize UI controller
        self.controller = UIController(self, DownloadManager(), MyLogger())

if __name__ == "__main__":
    app = UniversalDownloader()
    app.mainloop()
