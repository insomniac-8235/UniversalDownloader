import contextlib
from yt_dlp import YoutubeDL
from typing import Optional, Dict, Any, Callable
import os
from utilities.logger import MyLogger
from utilities.path_utils import get_deno_path, get_ffmpeg_path, get_aria2c_path
# REMOVED: from worker.progress_parser import ProgressParser (no longer needed for UI bar)

class DownloadWorker:
    def __init__(self, logger=None):
        self.logger = logger or MyLogger()
        self.progress_hook = None
        
        # Cache the Deno path once we discover it
        try:
            self._deno_path = get_deno_path()
        except FileNotFoundError:
            # Keep None – download_media will raise a friendly error
            self._deno_path = None
            
        # Discover and cache the aria2c path
        self._aria2c_path: Optional[str] = None
        try:
            self._aria2c_path = get_aria2c_path()
            if self._aria2c_path:
                self.logger.info(f"Found aria2c at: {self._aria2c_path}")
            else:
                self.logger.info("aria2c not found. Falling back to default downloader.")
        except Exception as e:
            self.logger.warning(f"Could not check for aria2c: {e}", exc_info=True)
            
    def download(self, url: str, folder: str, is_audio: bool) -> bool:
        """Handle the actual media download process"""
        try:
            # REMOVED: _total_bytes is no longer needed for indeterminate progress
            # self._total_bytes = 0 
            
            # Ensure ffmpeg is properly configured
            ffmpeg_path = get_ffmpeg_path()
            if not ffmpeg_path:
                raise FileNotFoundError("FFmpeg not found in PATH")
            
            # Make sure we have a Deno binary before proceeding
            if not self._deno_path:
                raise FileNotFoundError(
                    "Deno binary not found. Please install Deno or set DENO_PATH."
                )

            ydl_opts = {
                'format': 'bestaudio/best' if is_audio else 'bestvideo+bestaudio/best',
                'restrictfilenames': True,
                'noplaylist': True,
                'ffmpeg_location': ffmpeg_path,
                'outtmpl': os.path.join(folder, '%(title)s [%(id)s].%(ext)s'),
                'logger': self.logger,
                'progress_hooks': [self],
                
                # Correctly-structured js_runtimes:
                #   runtime name → config dict (executable_path + options list)
                'js_runtimes': {
                    'deno': {
                        'executable_path': self._deno_path,
                        'options': []          # ← leave empty unless extra flags are needed
                    }
                },
            }
            
            if self._aria2c_path:
                self.logger.info("Using aria2c for multi-threaded downloading.")
                ydl_opts['external_downloader'] = self._aria2c_path
                ydl_opts['external_downloader_args'] = [
                    '--summary-interval=1',  # Force progress updates every second
                    '-x', '16',              # Max 16 connections per server
                    '-s', '16',              # Split file into 16 parts
                    '-k', '1M',              # Minimum split size of 1MB
                    '-c'                     # ADDED: Ensure continue/resume functionality per CONVENTIONS.md
                ]
            
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            return True
            
        except Exception as e:
            error_msg = str(e)
            
            # Handle specific errors per CONVENTIONS.md
            if "Sign-in required" in error_msg or "sign in" in error_msg.lower():
                self.logger.error("Sign-in required for this URL")
            elif "Codec not found" in error_msg:
                self.logger.error("Codec not found. Please install ffmpeg.")
            else:
                self.logger.error(f"Download failed: {error_msg}")
            
            raise
            
    def download_progress_hook(self, d: Dict[str, Any]) -> None:
        """Progress hook for yt-dlp to update download progress"""
        # Simply pass the entire progress dictionary 'd' to the external hook.
        # The UIController will interpret the 'status' key for indeterminate progress.
        if self.progress_hook:
            try:
                self.progress_hook(d)
            except Exception as e:
                self.logger.error(f"Error in DownloadWorker progress_hook callback: {e}", exc_info=True)
            
    def __call__(self, d: Dict[str, Any]) -> None:
        """Handle progress updates (this is called by yt-dlp)"""
        self.download_progress_hook(d)
        
    def set_progress_hook(self, callback: Callable[[Dict[str, Any]], None]) -> None: # MODIFIED type hint
        """Set a progress update callback"""
        self.progress_hook = callback
        
    # def get_ffmpeg_path(self) -> str:
    #     """Get the path to the ffmpeg executable"""
    #     return get_ffmpeg_path()

    # def get_deno_path(self) -> str:
    #     """Get the path to the deno executable"""
    #     return self._deno_path
    
    def stop(self):
        """Stop the download process"""
        if hasattr(self, 'ydl'):
            with contextlib.suppress(Exception):
                # Cancel current download by setting a flag
                if hasattr(self.ydl, '_downloader'):
                    self.ydl._downloader.params['cancel'] = True
