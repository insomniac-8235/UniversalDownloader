import sys
import customtkinter as ctk
print(f"--- LOADING MODULE: {__name__} ---")

# Colour dictionary
THEME = {
    "APP_BG": ("#ffffff", "#1e1e1e"),
    "BG_FRAME": ("#ffffff", "#1e1e1e"),
    "BORDER_DEFAULT": ("#ffffff", "#1e1e1e"),
    "BORDER_HOVER": ("#dedede", "#6b6b6b"),
    "BORDER_FOCUS": ("#1976D2", "#1976d2"),
    "ENTRY_BG": ("#f8f8f8", "#353638"),
    "BTN_ACTION": ("#1976D2", "#1976d2"),
    "BTN_DISABLED": ("#f8f8f8", "#353638"),
    "BTN_HOVER": ("#448BD3", "#448BD3"),
    "PROG_FILL": ("#1976D2", "#1976D2"),
    "PROG_BG": ("#f8f8f8", "#353638"),
    "SWITCH_BTN": ("#1976D2", "#1976D2"),   
    "TEXT_ACTION_BTN": ("#ffffff", "#ffffff"),
    "TEXT_DISABLED": ("#dedede", "#676767"),    
    "TEXT_ENTRY": ("#444444", "#353638"),
    "TEXT_MAIN": ("#444444", "#a7a8ab"),
    "TEXT_GHOST": ("#999999", "#676767"),
    "TEXT_VERSION": ("#dedede","#353638")
}

# Font definitions
if sys.platform == "darwin":  # macOS
    FONTS = {
        "MAIN": (".AppleSystemUIFont", 13, "bold"),
        "INPUT": ("Menlo", 13),
        "VERSION": (".AppleSystemUIFont", 10),
        "BUTTON": (".AppleSystemUIFont", 15, "bold")
    }
else:  # Windows / Linux
    FONTS = {
        "MAIN": ("Segoe UI", 13, "bold"),
        "INPUT": ("Consolas", 13),
        "VERSION": ("Segoe UI", 10),
        "BUTTON": ("Segoe UI", 15, "bold")
    }