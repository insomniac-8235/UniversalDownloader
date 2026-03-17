import os
import sys
import platform
import customtkinter as ctk
from PIL import Image, ImageTk
print(f"--- LOADING MODULE: {__name__} ---")

# --- 1. THE BUNDLE GATEKEEPER ---
# Logic to find the true root whether running locally or as a bundle
if hasattr(sys, '_MEIPASS'):
    BASE_DIR = sys._MEIPASS # type: ignore
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
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")

setup_env()

# Now we import our custom modules
from ui.controller import UIController
from download_queue.thread_pool import ThreadPoolManager
from worker.download_worker import DownloadWorker
from utils.logger import UDLogger, DEBUG
from utils.theme import THEME
from utils.paths import _path_cache


class UniversalDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("system")
        self.configure(bg=THEME["APP_BG"])
        self.title("Universal Downloader")

        # Logger First
        self.logger = UDLogger(level=DEBUG)
        _path_cache.set_logger(self.logger)
        self.logger.set_level(DEBUG)

        # Setup Worker (Inject Logger, but don't pass controller yet)
        # Pass 'self' (the app) as the bridge instead of a specific controller class
        self.worker = DownloadWorker(self, self.logger)

        # Setup UI Controller
        # Pass 'self' so the controller can access self.worker later
        self.controller = UIController(self)

        # Connect the dots (Wiring)
        # Now that both exist, link the worker's hooks to the controller's methods
        self.worker.set_progress_hook(self.controller.on_progress_update)

        # Initialize Queue manager
        self.queue_manager = ThreadPoolManager(self, self.worker, max_workers=4)
        self.queue_manager.start()

        # UI and Dynamic scaling
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = int(screen_width * 0.15)
        height = int(screen_height * 0.3)
        self.geometry(f"{width}x{height}")
        self.minsize(500,400)

        # Icon & binary checks
        self.setup_icons()
        self.check_binary_integrity()

    def load_metadata(self):
        """Pulls the version and commit baked in during the build."""
        try:
            v_path = os.path.join(BASE_DIR, 'assets', 'version.txt')
            c_path = os.path.join(BASE_DIR, 'assets', 'commit.txt')
            with open(v_path, 'r') as v, open(c_path, 'r') as c:
                version = v.read().strip()
                commit = c.read().strip()
        except FileNotFoundError:
            self.logger.error("Version or commit file not found.")
            return "v0.0.0-dev (Local)"
        except Exception as e:
            self.logger.error(f"Error reading metadata: {e}")
            return "v0.0.0-dev (Local)"
        
        return f"{version} ({commit})"

    def setup_icons(self):
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

    def check_binary_integrity(self):
        """Layer 2 Enforcer: Verify tools are present in the environment."""
        from shutil import which
        tools = ["ffmpeg", "deno", "aria2c"]
        for tool in tools:
            if not which(tool):
                self.logger.warning(f"{tool} not found in PATH. Downloads may fail.")

    def on_closing(self):
        self.logger.info("Closing the application...")
        if hasattr(self, 'queue_manager'):
            self.queue_manager.stop()
        self.destroy()

if __name__ == "__main__":
    app = UniversalDownloader()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()