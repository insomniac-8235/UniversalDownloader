from yt_dlp import YoutubeDL
from typing import Dict, Any, Callable
import os
import re
from utilities import get_deno_path, get_ffmpeg_path


class DownloadManager:
    def __init__(self, logger):
        self.logger = logger
        self.progress_hook = None
        self._cancel_requested = False
        self._total_bytes = 0
        self._primary_finished = False # Tracks if we finished the first file
        self._deno_path = get_deno_path()
        self._ffmpeg_path = get_ffmpeg_path()
        if self._deno_path:
            self.logger.info(f"Deno runtime detected: {self._deno_path}")
        else:
            self.logger.warning("Deno not found in bin/. Downloads may be slower on some sites.")
        # Cache the Deno path once we discover it
        try:
            self._deno_path = get_deno_path()
        except FileNotFoundError:
            # Keep None – download_media will raise a friendly error
            self._deno_path = None
            
    def download_media(self, url: str, folder: str, is_audio: bool) -> bool:
        self._cancel_requested = False
        self._primary_finished = False
        
        try:
            ydl_opts = {
                'ffmpeg_location': self._ffmpeg_path,
                'format': 'bestvideo+bestaudio/best' if not is_audio else 'bestaudio/best',
                'outtmpl': os.path.join(folder, '%(title)s [%(id)s].%(ext)s'),
                'progress_hooks': [self.download_progress_hook],
                'postprocessor_hooks': [self.post_process_hook],
                
                # 1. The correct dictionary syntax for 2026
                'js_runtimes': {
                    'deno': {'path': self._deno_path}
                } if self._deno_path else {},

                # 2. Enabling the automatic remote solver fetch
                'remote_components': ['ejs:github'],
                
                # 3. Use the plugin for easier management
                'allow_unsecure_tools': False,
            }
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            return True
            
        except Exception as e:
            self.logger.error(f"Download failed: {str(e)}")
            raise

    def post_process_hook(self, d: Dict[str, Any]) -> None:
        """Called when yt-dlp starts merging, converting, or fixing up."""
        if d.get('status') == 'started':
            if self.progress_hook:
                # We send 100% progress and a special 'FINALIZING' speed tag
                self.progress_hook(100.0, "FINALISING")

    def download_progress_hook(self, d: Dict[str, Any]) -> None:
        if getattr(self, '_cancel_requested', False):
            raise Exception("DOWNLOAD_CANCELLED")

        status = d.get('status')
        
        # 1. Detect when the FIRST download finishes
        if status == 'finished' and not self._primary_finished:
            self._primary_finished = True

        # 2. If we are in the 'second' download (Audio track for DASH/HLS)
        # or if it's already finished the first file, just say 'FINALISING'
        if self._primary_finished:
            if self.progress_hook:
                self.progress_hook(100, "FINALISING")
            return

        # 3. Standard Primary Download Progress
        try:
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            
            if total > 0 and self._total_bytes == 0:
                self._total_bytes = total
            
            progress = (downloaded / self._total_bytes * 100) if self._total_bytes > 0 else 0
            
            # Clean the speed string
            raw_speed = d.get('_speed_str', '0B/s')
            clean_speed = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', raw_speed).strip()
            
            if self.progress_hook:
                self.progress_hook(progress, clean_speed)
                
        except Exception as e:
            print(f"Hook Error: {e}")
            
    def __call__(self, d: Dict[str, Any]) -> None:
        """Handle progress updates"""
        self.download_progress_hook(d)
        
    def set_progress_hook(self, callback: Callable[[float], None]) -> None:
        """Set a progress update callback"""
        self.progress_hook = callback
        
    def get_ffmpeg_path(self) -> str:
        """Get the path to the ffmpeg executable"""
        return self.get_ffmpeg_path()

    def get_deno_path(self) -> str:
        """Get the path to the deno executable"""
        return self.get_deno_path()
    
    def cancel(self):
        """Signal the downloader to stop."""
        self._cancel_requested = True