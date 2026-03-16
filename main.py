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
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")

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

        ctk.set_appearance_mode("system")
        self.configure(bg=THEME["APP_BG"])
        self.title("Universal Downloader")

        # Dynamic scaling
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = int(screen_width * 0.2)
        height = int(screen_height * 0.3)
        self.geometry(f"{width}x{height}")
        self.minsize(500, 500)

        # Logger
        self.logger = MyLogger(level=DEBUG)

        # Icon & binary checks
        self.setup_icons()
        self.check_binary_integrity()

        # --- CORE STACK ---
        # 1. Worker
        self.worker = DownloadWorker(self.logger)

        # 2. Controller (pass worker so it can start/cancel downloads)
        self.controller = UIController(self, worker=self.worker)

        # 3. Queue manager
        self.queue_manager = ThreadPoolManager(
            worker=self.worker,
            max_workers=4,
            controller=self.controller
        )
        self.controller.queue = self.queue_manager
        self.queue_manager.start()

        # Hook worker progress to UIController
        self.worker.set_progress_hook(self.controller.on_worker_progress)

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
        """The Master Janitor sequence."""
        self.logger.info("Closing the application...")
        if hasattr(self, 'queue_manager'):
            self.queue_manager.stop()
        self.destroy()

if __name__ == "__main__":
    app = UniversalDownloader()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()