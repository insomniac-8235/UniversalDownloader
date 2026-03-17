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
    print("WORKER DEBUG: Thread starting...") # <--- PING 2
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
    def start_download_threaded(self, url, folder, is_audio, progress_hook):
        
        t = threading.Thread(
            target=self.run_worker,
            args=(url, folder, is_audio), 
            daemon=True
        )
        t.start()

    def run_worker(self, url, folder, is_audio):
        self.logger.info("WORKER DEBUG: Inside run_worker thread")
        try:
            # 1. Start the UI downloading state
            self.app.after(0, lambda: self.app.controller.set_downloading_state(True))

            # 2. Run the actual process
            success = self.execute_download(url, folder, is_audio)

            if success:
                self.logger.info("✅ Download and Processing Complete.")
            else:
                self.logger.error("❌ Download failed or was cancelled.")

        except Exception as e:
            self.logger.error(f"Worker Error: {e}")
        
        finally:
            # 3. CRITICAL: Always reset the UI, even if it crashed!
            self.app.after(0, lambda: self.app.controller.set_downloading_state(False))


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
        """
        Launches the Deno process and streams output character-by-character 
        to ensure real-time UI updates and progress tracking.
        """
        # 1. Initialize process state
        self.current_process = None
        cmd = []

        try:
            # 2. Gather paths from your utility functions
            deno_path = get_deno_path()
            service_script = get_deno_service_path()
            ytdlp_path = get_yt_dlp_path()
            aria_path = get_aria2c_path()

            # 3. Build the Command
            cmd = [
                deno_path, "run", "-A", service_script,
                url, folder, str(is_audio).lower(), ytdlp_path, aria_path
            ]

            self.logger.debug(f"Launching Deno Process: {' '.join(cmd)}")

            # 4. Spawn the subprocess with line buffering
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # --- THE FIREHOSE LOOP ---
            # We read character-by-character to catch \r updates (aria2c style)
            partial_line = ""
            while True:
                char = self.current_process.stdout.read(1)
                
                # Exit condition: no more output and process has exited
                if not char and self.current_process.poll() is not None:
                    break
                
                if char:
                    if char in ('\n', '\r'):
                        # We hit a line break or carriage return
                        clean_line = partial_line.strip()
                        if clean_line:
                            # Log to console for debugging
                            self.logger.debug(f"DENO: {clean_line}")
                            # Pass to the parser for UI updates
                            self._handle_worker_output(clean_line)
                        
                        partial_line = "" # Reset buffer for next line
                    else:
                        partial_line += char

            return self.current_process.returncode == 0

        except Exception as e:
            self.logger.error(f"DENO: FATAL ERROR in execute_download: {e}")
            return False

    def _handle_worker_output(self, clean_line):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        decolorized = ansi_escape.sub('', clean_line)

        # --- 1. EXTRACT SPEED ---
        if "DL:" in decolorized:
            # Matches numbers like 25.5 and units like MiB or KiB
            if speed_match := re.search(r"DL:(\d+(?:\.\d+)?)([KkMmGg]iB)", decolorized):
                num = speed_match[1]
                # Convert 'MiB' to 'MB' for a cleaner look
                unit = speed_match[2].replace('iB', 'B') 
                speed_str = f"{num}{unit}/s"
                
                if hasattr(self.app.controller, 'update_speed_hook'):
                    self.app.after(0, lambda: self.app.controller.update_speed_hook(speed_str))

        # --- 2. THE BOUNCER (Silence the noise) ---
        trash = ["[NOTICE]", "Summary", "====", "----", "FILE:", "[#"]
        if any(m in decolorized for m in trash):
            if "%" in decolorized: self._parse_and_update_progress(decolorized)
            return 

        # --- 3. LOGGING & STATUS ---
        self.logger.debug(f"DENO: {decolorized}")
        self._update_status_labels(decolorized)

    def _update_status_labels(self, text):
        """Helper to update the 'Analyzing/Merging' label."""
        status = None
        if "[youtube]" in text: status = "Analyzing YouTube..."
        elif "[info]" in text: status = "Gathering Formats..."
        elif "[Merger]" in text or "ffmpeg" in text.lower():
            status = "Merging Files..."
            if hasattr(self.app.controller, 'set_processing_state'):
                self.app.after(0, self.app.controller.set_processing_state)

        if status and hasattr(self.app.controller, 'update_status_hook'):
            self.app.after(0, lambda s=status: self.app.controller.update_status_hook(s))

    def _handle_worker_output(self, clean_line):
        """The Bouncer: Updates UI and silences the Aria2c summary flood."""
        # 1. Strip ANSI colors
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        decolorized = ansi_escape.sub('', clean_line)

        # --- 2. SPEED SNIFFER ---
        # Look for the speed (e.g., DL:15MiB)
        if "DL:" in decolorized:
            if speed_match := re.search(r"DL:(\d+(?:\.\d+)?)([KkMmGg]iB)", decolorized):
                num = speed_match[1]
                unit = speed_match[2].replace('iB', 'B') # MiB -> MB
                speed_str = f"{num}{unit}/s"
                
                # Push speed to the Controller
                if hasattr(self.app.controller, 'update_speed_hook'):
                    self.app.after(0, lambda: self.app.controller.update_speed_hook(speed_str))

        # --- 3. THE TRASH FILTER ---
        # If it's aria2c fragment spam, we check for progress and then KILL the line
        trash = ["[NOTICE]", "Summary", "====", "----", "FILE:", "[#"]
        if any(marker in decolorized for marker in trash):
            if "%" in decolorized: 
                self._parse_and_update_progress(decolorized)
            return 

        # --- 4. PROGRESS CHECK ---
        if "%" in decolorized:
            self._parse_and_update_progress(decolorized)
            # If it's a standard download line, don't log it to keep the console clean
            if "[download]" in decolorized:
                return

        # --- 5. LOG THE IMPORTANT STUFF ---
        # Only major events (Analyzing, Merging, Errors) reach the console
        self.logger.debug(f"DENO: {decolorized}")
        self._update_status_labels(decolorized)

    # --- THE MISSING HELPER FUNCTIONS ---

    def _parse_and_update_progress(self, text):
        """Extracts % from any string and updates the UI progress bar."""
        if match := re.search(r"(\d+(?:\.\d+)?)%", text):
            try:
                # Convert 45.2 to 0.452 for the CTkProgressBar
                val = float(match[1]) / 100.0
                self.app.after(0, lambda: self.app.controller.on_progress_update(val))
            except Exception:
                pass

    def _update_status_labels(self, text):
        """Updates the internal state of the status label (Analyzing/Merging)."""
        status = None
        if "[youtube]" in text: status = "Analyzing YouTube..."
        elif "[info]" in text: status = "Gathering Formats..."
        elif "[Merger]" in text or "ffmpeg" in text.lower():
            status = "Merging Files..."
            if hasattr(self.app.controller, 'set_processing_state'):
                self.app.after(0, self.app.controller.set_processing_state)

        if status and hasattr(self.app.controller, 'update_status_hook'):
            self.app.after(0, lambda s=status: self.app.controller.update_status_hook(s))