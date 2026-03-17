import contextlib
import os
import re
import threading
import subprocess
from typing import Optional, Dict, Callable
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
from utils.paths import get_aria2c_path, get_deno_path, get_deno_service_path, get_ffmpeg_path, get_yt_dlp_path
print(f"--- LOADING MODULE: {__name__} ---")



class DownloadWorker:
    def __init__(self, app, logger):
        super().__init__()
        self.app = app
        self.progress_hook = None
        self.logger = logger
        self.ydl: Optional[YoutubeDL] = None
        self.cancel_event = threading.Event()
        self.current_process = None
        self.current_output = None      
        self.logger.info("DownloadWorker initialised with app and logger") 

    def _internal_progress_handler(self, d):
        """Bridge between yt-dlp's data and your UI hook."""
        # 1. Run your existing cancel check logic
        self.check_cancel_hook(d)
        
        # 2. Forward the data to the UI if a hook is registered
        if self.progress_hook:
            self.progress_hook(d)

    # --------------------- Threaded download --------------------- #
    # Inside DownloadWorker
    def start_download_threaded(self, url, folder, is_audio, progress_hook):
        print("WORKER DEBUG: Thread starting...") # <--- PING 2
        t = threading.Thread(
            target=self.run_worker,
            args=(url, folder, is_audio), 
            daemon=True
        )
        t.start()

    def run_worker(self, url, folder, is_audio):
        self.logger.info("WORKER DEBUG: Inside run_worker thread")
        try:
            # 1. TELL UI WE STARTED
            self.app.after(0, lambda: self.app.set_downloading_state(True))
            
            self.execute_download(url, folder, is_audio)
            
        except Exception as e:
            self.logger.error(f"Download Error: {e}")
        finally:
            # 2. TELL UI WE FINISHED
            self.app.after(0, lambda: self.app.set_downloading_state(False))

    # --------------------- URL Validation --------------------- #
    def is_valid_url(self, url: str) -> bool:
        """Simple URL validation."""
        return bool(url.startswith("http://") or url.startswith("https://"))

    def _on_yt_dlp_progress(self, d):
        """The single source of truth for every progress pulse."""
        # 1. Check for Cancel first!
        self.check_cancel_hook(d)
        
        # 2. Convert to float and send to UI
        if d['status'] == 'downloading':
            p_str = d.get('_percent_str', '0%').strip().replace('%','')
            try:
                float_val = float(p_str) / 100.0
                if self.progress_hook:
                    self.progress_hook(float_val)
            except (ValueError, TypeError):
                pass

    # --------------------- YoutubeDL options --------------------- #
    def get_ydl_opts(self, is_audio: bool, folder: str) -> Dict:
        """Return YoutubeDL options."""
        ffmpeg_path = get_ffmpeg_path()
        deno_path = get_deno_path()
        aria2c_path = get_aria2c_path
        if not ffmpeg_path: 
            raise FileNotFoundError("FFmpeg not found in PATH")

        if not deno_path:
            raise FileNotFoundError("Deno binary not found. Install or set DENO_PATH.")

        ydl_opts = {
            'format': self.get_format(is_audio),
            'restrictfilenames': True,
            'noplaylist': True,
            'ffmpeg_location': ffmpeg_path,
            'outtmpl': os.path.join(folder, '%(title)s [%(id)s].%(ext)s'),
            'logger': self.logger,
            'progress_hooks': [self.check_cancel_hook, self._send_progress_to_ui],
        }

        # Use aria2c if available
        if aria2c_path:
            ydl_opts['external_downloader'] = aria2c_path
            ydl_opts['external_downloader_args'] = [
                # --- Speed & Connections ---
                '--max-connection-per-server=16', # Maximize parallel chunks
                '--split=16',                    # Split the file into 16 pieces
                '--min-split-size=1M',           # Don't split tiny files (prevents overhead)
                
                # --- Stability & Reliability ---
                '--max-tries=10',                # Retry on flaky connections
                '--retry-wait=5',                # Wait 5 seconds before retrying
                '--timeout=30',                  # Drop dead connections after 30s
                '--connect-timeout=30',
                
                # --- UI & Performance ---
                '--summary-interval=1',          # Frequency of progress updates
                '--newline',                     # Essential for your yt-dlp parser
                '--file-allocation=falloc',      # Prevents disk fragmentation (Fast on Linux/Windows)
                '--console-log-level=warn',      # Keep console clean from thread spam
            ]

        return ydl_opts


    # --------------------- Format selection --------------------- #
    def get_format(self, is_audio: bool) -> str:
        return "bestaudio/best" if is_audio else "bestvideo+bestaudio/best"

    # --------------------- Cancellation hook --------------------- #

    def _stop_subprocess(self):
        """Safely stops the currently running external process (yt-dlp, ffmpeg, etc.)"""
        if self.current_process:
            self.logger.info(f"Terminating process {self.current_process.pid}...")
            try:
                self.current_process.terminate()
                # Give it 5 seconds to close gracefully
                self.current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.logger.warning("Process did not exit; force killing...")
                self.current_process.kill()
            except Exception as e:
                self.logger.error(f"Error during process termination: {e}")
            finally:
                self.current_process = None


    def _send_progress_to_ui(self, d):
        """Simple linear bridge: converts 0-100 string to 0.0-1.0 float."""
        if d['status'] == 'downloading':
            # Clean ' 45.2%' -> 45.2
            raw_p = d.get('_percent_str', '0%').strip().replace('%','')
            try:
                # Division by 100 converts to the 0.0-1.0 scale
                percentage = float(raw_p) / 100.0
                
                if self.progress_hook:
                    self.progress_hook(percentage)
            except ValueError:
                pass
    
        # Optional: Force completion when status flips to finished
        elif d['status'] == 'finished':
            if self.progress_hook:
                self.progress_hook(1.0)

    def set_progress_hook(self, callback: Callable[[float], None]):
        """Allows the UI to register a function to receive progress floats."""
        self.progress_hook = callback

    def check_cancel_hook(self, d):
        """Progress hook to check for cancellation."""
        if self.cancel_event.is_set():
            self._stop_subprocess() # Cleaned up
            raise DownloadError("Download cancelled by user")

    def cancel(self):
        """Cancel the current download."""
        self.logger.info("Cancelling download...")
        self.cancel_event.set()
        self._stop_subprocess() # Cleaned up


    def execute_download(self, url, folder, is_audio):
        # 1. Initialize variables to avoid UnboundLocalError
        cmd = []
        self.current_process = None

        try:
            # 2. Gather paths
            deno_path = get_deno_path()
            service_script = get_deno_service_path()
            ytdlp_path = get_yt_dlp_path()
            aria_path = get_aria2c_path()

            # 3. Build the Command list
            cmd = [
                deno_path, "run", "-A", service_script,
                url, folder, str(is_audio).lower(), ytdlp_path, aria_path
            ]

            print(f"DEBUG: Launching Process -> {' '.join(cmd)}", flush=True)

            # 4. Spawn the subprocess
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            while self.current_process is not None:
                line = self.current_process.stdout.readline()

                # Check if process is still running
                is_alive = self.current_process.poll() is None
                if not line and not is_alive:
                    break

                if line:
                    clean_line = line.strip()
                    print(f"DENO_VERBOSE: {clean_line}", flush=True)

                    # --- VERBOSE STATUS LOGIC ---
                    status_text = None
                    if "[youtube]" in clean_line:
                        status_text = "Analyzing YouTube..."
                    elif "[info]" in clean_line:
                        status_text = "Gathering Formats..."
                    elif "[download] Destination" in clean_line:
                        status_text = "Starting Download..."
                    elif "[download]" in clean_line and "%" not in clean_line:
                        status_text = "Downloading Fragments..."
                    elif "[Merger]" in clean_line:
                        status_text = "Merging Files..."
                    elif "DRM protected" in clean_line:
                        status_text = "ERROR: DRM Protected"

                    # Update status text in UI
                    if status_text and hasattr(self.app, 'update_status_hook'):
                        self.app.root.after(0, lambda s=status_text: self.app.update_status_hook(s))

                    if progress_match := re.search(
                        r"(?:\(| )(\d+(?:\.\d+)?)%", clean_line
                    ):
                        with contextlib.suppress(ValueError):
                            if self.progress_hook:
                                percent = float(progress_match[1])
                                normalized_progress = percent / 100.0

                                self.app.root.after(0, lambda p=normalized_progress: self.app.progress_hook(p))
            return self.current_process.returncode == 0

        except Exception as e:
            print(f"FATAL ERROR in execute_download: {e}", flush=True)
            return False