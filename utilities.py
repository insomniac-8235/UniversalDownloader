import os
import sys
import shutil
from PIL import Image, ImageTk

THEME = {
    "APP_BG": ("#ffffff", "#1e1e1e"),
    "BG_FRAME": ("#ffffff", "#1e1e1e"),
    "BORDER_DEFAULT": ("#ffffff", "#1e1e1e"),
    "BORDER_HOVER": ("#dedede", "#6b6b6b"),
    "ENTRY_BG": ("#f8f8f8", "#353638"),
    "ENTRY_HOVER": ("#d4d4d4", "#353638"),
    "ENTRY_FOCUS": ("#1976D2", "#1976d2"),
    "BTN_ACTION": ("#1976D2", "#1976d2"),
    "BTN_DISABLED": ("#f8f8f8", "#353638"),
    "BTN_HOVER": ("#448BD3", "#448BD3"),
    "PROG_FILL": ("#1976D2", "#1976D2"),
    "PROG_BG": ("#f8f8f8", "#353638"),
    "SWITCH_BTN": ("#dedede", "#999999"),   
    "TEXT_ACTION_BTN": ("#ffffff", "#ffffff"),
    "TEXT_DISABLED": ("#dedede", "#4e4f52"),    
    "TEXT_ENTRY": ("#444444", "#353638"),
    "TEXT_MAIN": ("#444444", "#a7a8ab"),
    "TEXT_GHOST": ("#999999", "#4e4e53"),
    "TEXT_VERSION": ("#dedede","#353638")
}
# THEME = {
#     "APP_BG": ("#ffffff", "#1e1e1e"),
#     "BG_FRAME": ("#ffffff", "#1e1e1e"),
#     "BORDER_DEFAULT": ("#999999", "#4e4f52"),
#     "BORDER_HOVER": ("#1976D2", "#6b6b6b"),
#     "ENTRY_BG": ("#cecece", "#353638"),
#     "ENTRY_HOVER": ("#d4d4d4", "#353638"),
#     "ENTRY_FOCUS": ("#1976D2", "#1976D2"),
#     "BTN_ACTION": ("#1976D2", "#1976d2"),
#     "BTN_DISABLED": ("#d4d4d4", "#353638"),
#     "BTN_HOVER": ("#448BD3", "#448BD3"),
#     "PROG_FILL": ("#1976D2", "#1976D2"),
#     "PROG_BG": ("#d4d4d4", "#353638"),
#     "TEXT_ACTION": ("#EBEBEB", "#c4c4c4"),
#     "TEXT_DISABLED": ("#CECECE", "#4e4f52"),
#     "TEXT_ENTRY": ("#000000", "#353638"),
#     "TEXT_MAIN": ("#444444", "#a7a8ab"),
#     "TEXT_GHOST": ("#666666", "#67676d"),
#     "TEXT_VERSION": ("#888888","#353638")
# }

def get_deno_path() -> str:
    """Return the absolute path to the Deno binary."""
    
    # 0. Portable‐app root – look in `deno_bin/` relative to this file
    # (works for a normal dev run and for a frozen app)
    for root_dir in (
        # If the code is frozen (PyInstaller) – use the temporary folder
        getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))),
        # Otherwise, use the directory that contains the script
        os.path.dirname(os.path.abspath(__file__)),
    ):
        for name in ("deno", "deno.exe"):
            p = os.path.join(root_dir, "deno_bin", name)
            if os.path.isfile(p):
                return p

    # 1. Bundled binary (PyInstaller) – look in the temporary _MEIPASS folder
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        for name in ("deno", "deno.exe"):
            p = os.path.join(base, name)
            if os.path.isfile(p):
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
            return p

    # 3. Environment override
    env_path = os.getenv("DENO_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    if p := shutil.which("deno"):
        return p

    # 5. Common Homebrew locations
    for dir_ in ("/opt/homebrew/bin", "/usr/local/bin"):
        p = os.path.join(dir_, "deno")
        if os.path.isfile(p):
            return p

    raise FileNotFoundError("Deno not found in PATH or common locations")


def get_ffmpeg_path() -> str:
    """Return the absolute path to the ffmpeg executable."""
    
    # 0. Portable‐app root – look in `ffmpeg_bin/` relative to this file
    for root_dir in (
        getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))),
        os.path.dirname(os.path.abspath(__file__)),
    ):
        for name in ("ffmpeg", "ffmpeg.exe"):
            p = os.path.join(root_dir, "ffmpeg_bin", name)
            if os.path.isfile(p):
                return p

    # 1. Bundled binary (PyInstaller) – look in the temporary _MEIPASS folder
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        for name in ("ffmpeg", "ffmpeg.exe"):
            p = os.path.join(base, name)
            if os.path.isfile(p):
                return p

    # 2. Portable‐app root – look in the directory that contains the executable
    if getattr(sys, 'frozen', False):
        root_dir = os.path.dirname(sys.executable)
    else:
        root_dir = os.path.dirname(os.path.abspath(__file__))
    for name in ("ffmpeg", "ffmpeg.exe"):
        p = os.path.join(root_dir, name)
        if os.path.isfile(p):
            return p

    # 3. Environment override
    env_path = os.getenv("FFMPEG_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    if p := shutil.which("ffmpeg"):
        return p

    raise FileNotFoundError("FFmpeg not found in PATH or common locations")


class MyLogger:
    def debug(self, msg):
        # Only print if it's not a noisy progress message
        if not msg.startswith('[debug] '):
            print(f"DEBUG: {msg}")
    
    def warning(self, msg): 
        print(f"WARNING: {msg}")
    
    def error(self, msg): 
        print(f"ERROR: {msg}")

class ProgressParser:
    """Regex-based parser for yt-dlp/ffmpeg log lines"""
    
    MERGE_KEYWORDS = ["merging", "postprocessor", "finalising", "writing metadata"]
    DOWNLOAD_KEYWORDS = ["[download]", "downloading"]
    
    @classmethod
    def detect_phase(cls, progress_info: str) -> str:
        """
        Detect if we're downloading or merging from yt-dlp log line.
        
        Args:
            progress_info: Raw progress string from yt-dlp/ffmpeg
            
        Returns:
            "MERGING" or "DOWNLOADING"
        """
        info_str = progress_info.lower()

        # Check merge keywords first (higher priority)
        return next(
            ("MERGING" for keyword in cls.MERGE_KEYWORDS if keyword in info_str),
            "DOWNLOADING",
        )
