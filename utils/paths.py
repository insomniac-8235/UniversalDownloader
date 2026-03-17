import os
import sys
import shutil
from pathlib import Path
from typing import Optional
print(f"--- LOADING MODULE: {__name__} ---")


"""Consolidated binary lookup for Unified /bin structure (Bundle & Dev aware)"""

class PathCache:
    def __init__(self):
        self.logger=None
        self._cache = {}
        
        # 1. Determine the True Root
        # If bundled, use the temp extraction path; if dev, use project root
        if hasattr(sys, '_MEIPASS'):
            self.root = Path(sys._MEIPASS)
        else:
            # Go up one level from /utilities to reach project root
            self.root = Path(__file__).parent.parent.absolute()

    def set_logger(self, logger):
        """Allows the main app to pass its logger instance here."""
        self.logger = logger

    def _find_binary(self, name: str, env_var: Optional[str] = None) -> str:
        """Centralized logic to find a binary and log the result."""
        if name in self._cache:
            return self._cache[name]

        found_path = None  # Placeholder to capture the find

        # 1. Check the Unified /bin folder
        suffixes = ("", ".exe") if os.name == "nt" else ("",)
        for suffix in suffixes:
            p = self.root / "bin" / f"{name}{suffix}"
            if p.is_file():
                if os.name != "nt":
                    os.chmod(p, 0o755) 
                found_path = str(p)
                break # Stop searching, we found it!

        # 2. Environment Override
        if not found_path and env_var:
            env_path = os.getenv(env_var)
            if env_path and os.path.isfile(env_path):
                found_path = env_path

        # 3. System PATH (shutil.which)
        if not found_path:
            found_path = shutil.which(name)

        # 4. Common Homebrew/Linux locations
        if not found_path:
            search_dirs = ["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin"]
            for dir_ in search_dirs:
                p = Path(dir_) / name
                if p.is_file():
                    found_path = str(p)
                    break

        # --- THE LOGGING JUNCTION ---
        if found_path:
            self._cache[name] = found_path
            # Use the MyLogger info method if provided
            if self.logger:
                self.logger.info(f"Found {name} at: {found_path}")
            return found_path
        
        # If we reach here, nothing was found
        error_msg = f"Binary '{name}' not found in /bin or system PATH."
        if self.logger:
            self.logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    def get_deno_path(self) -> str:
        return self._find_binary("deno", "DENO_PATH")
    
    def get_deno_service_path(self) -> str:
        # 1. Check the /services folder
        p = self.root / "services" / "downloader.ts"
        
        if p.is_file():
            return str(p)
            
        # 2. Fallback: Check project root if you didn't put it in a folder
        fallback = self.root / "downloader.ts"
        if fallback.is_file():
            return str(fallback)

        raise FileNotFoundError(f"Deno service script 'downloader.ts' not found at {p}")

    def get_ffmpeg_path(self) -> str:
        return self._find_binary("ffmpeg", "FFMPEG_PATH")

    def get_aria2c_path(self) -> str:
        # Changed to return str and raise error to keep Enforcer logic consistent
        return self._find_binary("aria2c", "ARIA2C_PATH")

    def get_yt_dlp_path(self) -> str:
        return self._find_binary("yt-dlp", "YTDLP_PATH")

_path_cache = PathCache()

# Exported helper functions
get_deno_path = _path_cache.get_deno_path
get_deno_service_path = _path_cache.get_deno_service_path
get_ffmpeg_path = _path_cache.get_ffmpeg_path
get_aria2c_path = _path_cache.get_aria2c_path
get_yt_dlp_path = _path_cache.get_yt_dlp_path