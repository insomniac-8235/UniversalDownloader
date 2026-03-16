import contextlib
import threading
import os
from typing import Optional, Dict, Any, Callable
from yt_dlp import YoutubeDL
from utils.logger import MyLogger
from utils.paths import get_deno_path, get_ffmpeg_path, get_aria2c_path


class DownloadWorker:
    def __init__(self, logger=None):
        self.logger = logger or MyLogger()
        self.progress_hook: Optional[Callable[[Dict[str, Any]], None]] = None
        self.ydl: Optional[YoutubeDL] = None
        self.cancel_event = threading.Event()

        # Discover Deno
        try:
            self._deno_path = get_deno_path()
        except FileNotFoundError:
            self._deno_path = None

        # Discover aria2c
        self._aria2c_path: Optional[str] = None
        try:
            self._aria2c_path = get_aria2c_path()
            if self._aria2c_path:
                self.logger.info(f"Found aria2c at: {self._aria2c_path}")
            else:
                self.logger.info("aria2c not found. Using default downloader.")
        except Exception as e:
            self.logger.warning(f"Could not check for aria2c: {e}", exc_info=True)

    def start_download_threaded(self, url: str, folder: str, is_audio: bool):
        """Start download in a background thread"""
        t = threading.Thread(target=self.download, args=(url, folder, is_audio), daemon=True)
        t.start()

    def download(self, url: str, folder: str, is_audio: bool):
        """Main download entry point (blocking)"""
        self.cancel_event.clear()
        try:
            return self.execute_download(is_audio, folder, url)
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            raise

    def execute_download(self, is_audio: bool, folder: str, url: str) -> bool:
        # Validate ffmpeg
        ffmpeg_path = get_ffmpeg_path()
        if not ffmpeg_path:
            raise FileNotFoundError("FFmpeg not found in PATH")

        # Validate deno
        if not self._deno_path:
            raise FileNotFoundError("Deno binary not found. Install or set DENO_PATH.")

        ydl_opts = {
            'format': 'bestaudio/best' if is_audio else 'bestvideo+bestaudio/best',
            'restrictfilenames': True,
            'noplaylist': True,
            'ffmpeg_location': ffmpeg_path,
            'outtmpl': os.path.join(folder, '%(title)s [%(id)s].%(ext)s'),
            'logger': self.logger,
            'progress_hooks': [self],
            'js_runtimes': {
                'deno': {
                    'executable_path': self._deno_path,
                    'options': []
                }
            }
        }

        if self._aria2c_path:
            ydl_opts['external_downloader'] = self._aria2c_path
            ydl_opts['external_downloader_args'] = [
                '--summary-interval=1',
                '-x', '8',
                '-s', '8',
                '-k', '1M',
                '-c'
            ]
            self.logger.info("Using aria2c for multi-threaded downloads.")

        self.ydl = YoutubeDL(ydl_opts)
        try:
            with self.ydl as ydl:
                ydl.download([url])
        finally:
            self.ydl = None

        return True

    def __call__(self, d: Dict[str, Any]):
        """yt-dlp calls this for progress updates"""
        if self.cancel_event.is_set():
            raise Exception("Download cancelled")

        if self.progress_hook:
            try:
                self.progress_hook(d)
            except Exception as e:
                self.logger.error(f"Error in progress_hook: {e}", exc_info=True)

    def set_progress_hook(self, callback: Callable[[Dict[str, Any]], None]):
        """Attach a UI progress callback"""
        self.progress_hook = callback

    def cancel(self):
        """Cancel current download"""
        self.cancel_event.set()
        if self.ydl and hasattr(self.ydl, "_downloader"):
            with contextlib.suppress(Exception):
                self.ydl._downloader.params["cancel"] = True