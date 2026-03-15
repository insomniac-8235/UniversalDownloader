import os
import sys
import platform
import customtkinter as ctk
from PIL import Image, ImageTk

# --- 1. THE BUNDLE GATEKEEPER ---
# Logic to find the true root whether running locally or as a bundle
if hasattr(sys, '_MEIPASS'):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add the project root to sys.path so we can find our 'utils' and 'ui' folders
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# --- 2. PATH INJECTION ---
def setup_env():
    """Injects /bin into the system PATH so yt-dlp finds deno/ffmpeg/aria2c."""
    bin_dir = os.path.join(BASE_DIR, "bin")
    if os.path.exists(bin_dir):
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ["PATH"]

setup_env()

# Now we import our custom modules
from ui.controller import UIController
from download_queue.thread_pool import ThreadPoolManager
from worker.download_worker import DownloadWorker
from utils.logger import MyLogger, DEBUG 
from utils.theme import THEME

class UniversalDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Load Metadata (Single Source of Truth from GitHub Action)
        self.version_info = self._load_metadata()
        
        self.title(f"Universal Downloader")
        self.geometry("500x400")
        self.resizable(False, False)
        self.configure(bg=THEME["APP_BG"])
        
        self.logger = MyLogger(level=DEBUG) 
        
        # Icon & Binary Checks
        self._setup_icons()
        self._check_binary_integrity()
        
        # Core Stack Initialization
        self.worker = DownloadWorker(self.logger) 
        self.controller = UIController(self, None) 
        self.queue_manager = ThreadPoolManager(
            worker=self.worker, 
            max_workers=4, 
            controller=self.controller
        )
        self.controller.queue = self.queue_manager
        self.queue_manager.start()

    def _load_metadata(self):
        """Pulls the version and commit baked in during the build."""
        try:
            v_path = os.path.join(BASE_DIR, 'assets', 'version.txt')
            c_path = os.path.join(BASE_DIR, 'assets', 'commit.txt')
            with open(v_path, 'r') as v, open(c_path, 'r') as c:
                return f"{v.read().strip()} ({c.read().strip()})"
        except:
            return "v0.0.0-dev (Local)"

    def _setup_icons(self):
        """Cross-platform icon handling using BASE_DIR."""
        assets_dir = os.path.join(BASE_DIR, 'assets')
        
        if platform.system() == "Windows":
            icon_path = os.path.join(assets_dir, 'icon.ico')
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        else:
            # Mac Logic: iconphoto handles high-res PNGs better
            icon_path = os.path.join(assets_dir, 'icon.png')
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                photo = ImageTk.PhotoImage(img)
                self.iconphoto(False, photo)
                self._icon_ref = photo # Crucial to prevent garbage collection

    def _check_binary_integrity(self):
        """Layer 2 Enforcer: Verify tools are present in the environment."""
        from shutil import which
        tools = ["ffmpeg", "deno", "aria2c"]
        for tool in tools:
            if not which(tool):
                self.logger.warning(f"{tool} not found in PATH. Downloads may fail.")

    def on_closing(self):
        """The Master Janitor sequence."""
        self.logger.info("Closing the application...")
        if hasattr(self, 'queue_manager'):
            self.queue_manager.stop()
        self.destroy()

if __name__ == "__main__":
    app = UniversalDownloader()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()