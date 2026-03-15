import os
import sys

# Ensure project root is in sys.path for module resolution
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import customtkinter as ctk
from ui.controller import UIController
from download_queue.thread_pool import ThreadPoolManager
from worker.download_worker import DownloadWorker
from utilities.logger import MyLogger, DEBUG 
from utilities.theme import THEME
from PIL import Image, ImageTk

class UniversalDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("")
    
        self.geometry("500x400")
        self.resizable(False, False)
        self.configure(bg=THEME["APP_BG"])
        
        # macOS-specific icon setup
        # if sys.platform == "darwin":
        #     for icon_ext in [".png", ".icns", ".ico"]:
        #         icon_path = os.path.join(os.path.dirname(__file__), 'assets', f'icon{icon_ext}')
        #         if os.path.exists(icon_path):
        #             try:
        #                 img = Image.open(icon_path)
        #                 photo = ImageTk.PhotoImage(img)
        #                 self.iconphoto(False, photo)
        #                 self._icon_reference = photo
        #                 break
        #             except Exception as e:
        #                 print(f"Icon failed to load: {e}")
        
        # Initialize a shared logger instance for the application
        self.logger = MyLogger(level=DEBUG) 
        
        # Initialize shared worker instance (single instance for all threads)
        self.worker = DownloadWorker(self.logger) 
        
        # Initialize UI controller BEFORE ThreadPoolManager to pass it
        self.controller = UIController(self, None) # Pass self, but None for queue_manager initially
        # We'll set the queue_manager reference after it's created
        
        # Initialize queue manager with shared worker and the controller instance
        # MODIFIED: Pass self.controller to ThreadPoolManager
        self.queue_manager = ThreadPoolManager(worker=self.worker, max_workers=4, controller=self.controller)
        
        # NOW set the queue_manager on the controller (circular reference, but necessary)
        self.controller.queue = self.queue_manager
        
        # Start thread pool before showing window
        self.queue_manager.start()

    def on_closing(self):
        """Handle window close - cleanup all resources."""
        self.queue_manager.stop()
        self.destroy()

if __name__ == "__main__":
    app = UniversalDownloader()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
