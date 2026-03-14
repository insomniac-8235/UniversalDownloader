from yt_dlp import YoutubeDL
from typing import Optional, Dict, Any, Callable
import os
import sys
import shutil
from utilities import MyLogger, get_deno_path, get_ffmpeg_path


class DownloadManager:
    def __init__(self, logger=None):
        self.logger = logger or MyLogger()
        self.progress_hook = None
        
        # Cache the Deno path once we discover it
        try:
            self._deno_path = get_deno_path()
        except FileNotFoundError:
            # Keep None – download_media will raise a friendly error
            self._deno_path = None
            
    def download_media(self, url: str, folder: str, is_audio: bool) -> bool:
        """Handle the actual media download process"""
        try:
            # Store the total bytes before starting the download
            self._total_bytes = 0
            
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
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            return True
            
        except Exception as e:
            self.logger.error(f"Download failed: {str(e)}")
            raise
            
    def download_progress_hook(self, d: Dict[str, Any]) -> None:
        """Progress hook for yt-dlp to update download progress"""
        try:
            # Get total bytes or estimate
            total = d.get('total_bytes', 0)
            if total == 0:
                total = d.get('total_bytes_estimate', 0)
            
            # Store the total bytes when we first know them (use value check, not hasattr)
            if total > 0 and self._total_bytes == 0:
                self._total_bytes = total
            
            # Calculate progress based on stored total
            if self._total_bytes > 0:
                downloaded = d.get('downloaded_bytes', 0)
                progress = (downloaded / self._total_bytes) * 100
                
                # Call the progress hook if it's been set
                if self.progress_hook:
                    self.progress_hook(progress)
            else:
                # If no total available, keep in indeterminate mode
                pass
            
        except Exception as e:
            print(f"Progress hook error: {e}")
            
    def __call__(self, d: Dict[str, Any]) -> None:
        """Handle progress updates"""
        self.download_progress_hook(d)
        
    def set_progress_hook(self, callback: Callable[[float], None]) -> None:
        """Set a progress update callback"""
        self.progress_hook = callback
        
    def get_ffmpeg_path(self) -> str:
        """Get the path to the ffmpeg executable"""
        return get_ffmpeg_path()

    def get_deno_path(self) -> str:
        """Get the path to the deno executable"""
        return self._deno_path
