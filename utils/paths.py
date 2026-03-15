import os
import sys
import shutil
from pathlib import Path
from typing import Optional

class PathCache:
    """Consolidated binary lookup for Unified /bin structure (Bundle & Dev aware)"""
    
    def __init__(self):
        self._cache = {}
        # 1. Determine the True Root
        # If bundled, use the temp extraction path; if dev, use project root
        if hasattr(sys, '_MEIPASS'):
            self.root = Path(sys._MEIPASS)
        else:
            # Go up one level from /utilities to reach project root
            self.root = Path(__file__).parent.parent.absolute()

    def _find_binary(self, name: str, env_var: Optional[str] = None) -> str:
        """Centralized logic to find a binary in the unified /bin or system."""
        if name in self._cache:
            return self._cache[name]

        # 2. Check the Unified /bin folder (The High-Priority "Gold" Source)
        # Check for extension-less (Mac) and .exe (Windows)
        suffixes = ("", ".exe") if os.name == "nt" else ("",)
        
        for suffix in suffixes:
            binary_name = f"{name}{suffix}"
            p = self.root / "bin" / binary_name
            if p.is_file():
                # On Mac/Linux, ensure the bundled binary is executable
                if os.name != "nt":
                    os.chmod(p, 0o755) 
                
                path_str = str(p)
                self._cache[name] = path_str
                return path_str

        # 3. Environment Override (Cyber Sec best practice for custom installs)
        if env_var and (env_path := os.getenv(env_var)):
            if os.path.isfile(env_path):
                self._cache[name] = env_path
                return env_path

        # 4. System PATH (shutil.which)
        if system_path := shutil.which(name):
            self._cache[name] = system_path
            return system_path

        # 5. Common Homebrew/Linux locations (Standard Mac Dev paths)
        search_dirs = ["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin"]
        for dir_ in search_dirs:
            p = Path(dir_) / name
            if p.is_file():
                path_str = str(p)
                self._cache[name] = path_str
                return path_str

        raise FileNotFoundError(f"Binary '{name}' not found in /bin or system PATH.")

    def get_deno_path(self) -> str:
        return self._find_binary("deno", "DENO_PATH")

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
get_ffmpeg_path = _path_cache.get_ffmpeg_path
get_aria2c_path = _path_cache.get_aria2c_path
get_yt_dlp_path = _path_cache.get_yt_dlp_path