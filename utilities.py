import os
import sys
import shutil


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

    # 2. Portable‑app root – look in the directory that contains the executable
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

    # 4. Normal PATH lookup
    p = shutil.which("deno")
    if p:
        return p

    # 5. Common Homebrew locations
    for dir_ in ("/opt/homebrew/bin", "/usr/local/bin"):
        p = os.path.join(dir_, "deno")
        if os.path.isfile(p):
            return p

    raise FileNotFoundError("Deno not found in PATH or common locations")


class MyLogger:
    def debug(self, msg):
        # Only print if it's not a noisy progress message
        if not msg.startswith('[debug] '):
            print(f"DEBUG: {msg}")
    
    def warning(self, msg): 
        print(f"WARNING: {msg}")
    
    def error(self, msg): 
        print(f"ERROR: {msg}")
