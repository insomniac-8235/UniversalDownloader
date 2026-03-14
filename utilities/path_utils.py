import os
import sys
import shutil
from typing import Optional

class PathCache:
    """Simple cache for binary paths to avoid repeated lookups"""
    
    def __init__(self):
        self._deno_path = None
        self._ffmpeg_path = None
        self._aria2c_path: Optional[str] = None
    
    def get_deno_path(self) -> str:
        """Return the absolute path to the Deno binary."""
        
        if self._deno_path is not None:
            return self._deno_path

        # 0. Portable‐app root – look in `deno_bin/` relative to this file
        for root_dir in (
            # If the code is frozen (PyInstaller) – use the temporary folder
            getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))),
            os.path.dirname(os.path.abspath(__file__)),
        ):
            for name in ("deno", "deno.exe"):
                p = os.path.join(root_dir, "deno_bin", name)
                if os.path.isfile(p):
                    self._deno_path = p
                    return p

        # 1. Bundled binary (PyInstaller) – look in the temporary _MEIPASS folder
        if getattr(sys, 'frozen', False):
            base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            for name in ("deno", "deno.exe"):
                p = os.path.join(base, name)
                if os.path.isfile(p):
                    self._deno_path = p
                    return p

        # 2. Portable‐app root – look in the directory that contains the executable
        #    (or the script when not frozen). This allows a bundled `deno` next to
        #    the application binary.
        if getattr(sys, 'frozen', False):
            root_dir = os.path.dirname(sys.executable)
        else:
            root_dir = os.path.dirname(os.path.abspath(__file__))
        for name in ("deno", "deno.exe"):
            p = os.path.join(root_dir, name)
            if os.path.isfile(p):
                self._deno_path = p
                return p

        # 3. Environment override
        env_path = os.getenv("DENO_PATH")
        if env_path and os.path.isfile(env_path):
            self._deno_path = env_path
            return self._deno_path

        if p := shutil.which("deno"):
            self._deno_path = p
            return self._deno_path

        # 5. Common Homebrew locations
        for dir_ in ("/opt/homebrew/bin", "/usr/local/bin"):
            p = os.path.join(dir_, "deno")
            if os.path.isfile(p):
                self._deno_path = p
                return self._deno_path

        raise FileNotFoundError("Deno not found in PATH or common locations")
    
    def get_ffmpeg_path(self) -> str:
        """Return the absolute path to the ffmpeg executable."""
        
        if self._ffmpeg_path is not None:
            return self._ffmpeg_path

        # 0. Portable‐app root – look in `ffmpeg_bin/` relative to this file
        for root_dir in (
            getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))),
            os.path.dirname(os.path.abspath(__file__)),
        ):
            for name in ("ffmpeg", "ffmpeg.exe"):
                p = os.path.join(root_dir, "ffmpeg_bin", name)
                if os.path.isfile(p):
                    self._ffmpeg_path = p
                    return p

        # 1. Bundled binary (PyInstaller) – look in the temporary _MEIPASS folder
        if getattr(sys, 'frozen', False):
            base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            for name in ("ffmpeg", "ffmpeg.exe"):
                p = os.path.join(base, name)
                if os.path.isfile(p):
                    self._ffmpeg_path = p
                    return p

        # 2. Portable‐app root – look in the directory that contains the executable
        if getattr(sys, 'frozen', False):
            root_dir = os.path.dirname(sys.executable)
        else:
            root_dir = os.path.dirname(os.path.abspath(__file__))
        for name in ("ffmpeg", "ffmpeg.exe"):
            p = os.path.join(root_dir, name)
            if os.path.isfile(p):
                self._ffmpeg_path = p
                return p

        # 3. Environment override
        env_path = os.getenv("FFMPEG_PATH")
        if env_path and os.path.isfile(env_path):
            self._ffmpeg_path = env_path
            return self._ffmpeg_path

        if p := shutil.which("ffmpeg"):
            self._ffmpeg_path = p
            return self._ffmpeg_path

        # 5. Common Homebrew locations
        for dir_ in ("/opt/homebrew/bin", "/usr/local/bin"):
            p = os.path.join(dir_, "ffmpeg")
            if os.path.isfile(p):
                self._ffmpeg_path = p
                return self._ffmpeg_path

        raise FileNotFoundError("FFmpeg not found in PATH or common locations")
    
    def get_aria2c_path(self) -> Optional[str]:
        """Return the absolute path to the aria2c binary, or None if not found."""
        if self._aria2c_path is None:
            if path := shutil.which("aria2c"):
                self._aria2c_path = path
        return self._aria2c_path


def get_deno_path() -> str:
    """Return the absolute path to the Deno binary."""
    return _path_cache.get_deno_path()


def get_ffmpeg_path() -> str:
    """Return the absolute path to the ffmpeg executable."""
    return _path_cache.get_ffmpeg_path()


def get_aria2c_path() -> Optional[str]:
    """Return the absolute path to the aria2c executable."""
    return _path_cache.get_aria2c_path()

_path_cache = PathCache()
