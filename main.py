import customtkinter as ctk
from tkinter import filedialog
from yt_dlp import YoutubeDL
import threading
import os
import sys


def resource_path(relative_path, is_binary=False):
    """
    Ultimate Resource Path for v0.2.0
    - Handles PyInstaller temp folders
    - Handles Windows .exe extensions automatically
    - Anchors to script directory during development
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    # Clean up the path for the specific OS
    path_segments = relative_path.replace("\\", "/").split("/")

    # Handle the binary extension for Windows
    if is_binary and sys.platform == "win32":
        if not path_segments[-1].lower().endswith(".exe"):
            path_segments[-1] += ".exe"

    return os.path.join(base_path, *path_segments)

# --- PYINSTALLER NOCONSOLE FIX ---
# If the app is compiled without a console, route all print statements to a black hole
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

try:
    from ctypes import windll

    # Tells Windows to render the app at native resolution
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# Set Appearance
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")
ctk.set_widget_scaling(1)  # Forces widgets to render at 100% internal scale
ctk.set_window_scaling(1)  # Forces the window to render at 100% internal scale


class MyLogger:
    def debug(self, msg):
        # Only print if it's not a noisy progress message
        if not msg.startswith('[debug] '):
            print(f"DEBUG: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")


class UniversalDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- WINDOW CONFIG ---
        self.title("Universal Media Downloader")
        self.geometry("500x420")
        self.resizable(False, False)

        # Set Window Icon (Works in both development and PyInstaller)
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, "assets", "icon.ico")  # Fixed slash
        else:
            icon_path = os.path.join("assets", "icon.ico")  # Fixed slash

        # --- THEME CONSTANTS ---
        # Backgrounds & Tracks
        self.APP_BG = ("#ebebeb", "#242424")  # Matches System background
        self.ENTRY_BG = ("#fcfcfc", "#343434")  # Subtle fill for inputs

        # Borders & States
        self.BORDER_HIDDEN = self.APP_BG  # Disappears into background
        self.BORDER_DEFAULT = ("#999999", "#444444")  # Soft grey (idle)
        self.ENTRY_FOCUS = ("#1976D2", "#1976D2")  # Active glow (typing)

        # Buttons
        self.ACTION_BTN = ("#1976D2", "#1976D2")  # Primary action (Download Now)
        self.BTN_DISABLED = ("#FCFCFC", "#343434")  # Disabled state (greyed out)
        self.ACTION_HOVER = ("#448BD3", "#448BD3")  # Hover for active button, could add subtle effect if desire
        self.BTN_HOVER = ("#EBEBEB", "#555555")  # Soft hover for ghost buttons
        self.TEXT_DISABLED = ("#CECECE", "#666666")  # Disabled button text
        self.ACTION_TEXT = ("#EBEBEB", "#EBEBEB")  # Text on action button

        # Progress & Text   
        self.PROG_FILL = ("#1976D2", "#1976D2")  # Bouncing bar color
        self.TEXT_MAIN = ("#444444", "#D4D4D4")  # Main text color (labels, entries when filled)
        self.TEXT_GHOST = ("#666666", "#d4d4d4")  # Placeholder text color
        self.TEXT_VERSION = ("#888888", "#555555")  # Version and credits text

        # --- CROSS-PLATFORM FONT DETECTION ---
        if sys.platform == "darwin":  # macOS
            MAIN_FONT_FAMILY = ".AppleSystemUIFont"
            INPUT_FONT_FAMILY = "Menlo"  # Mac's version of Consolas
        else:  # Windows/Linux
            MAIN_FONT_FAMILY = "Segoe UI"
            INPUT_FONT_FAMILY = "Consolas"

        # --- APPLICATION OF FONTS ---
        self.FONT_MAIN = ctk.CTkFont(family=MAIN_FONT_FAMILY, size=14)
        self.FONT_BOLD = ctk.CTkFont(family=MAIN_FONT_FAMILY, size=14, weight="bold")
        self.FONT_SMALL = ctk.CTkFont(family=MAIN_FONT_FAMILY, size=10)
        self.FONT_LARGE = ctk.CTkFont(family=MAIN_FONT_FAMILY, size=24)
        self.FONT_ACTION_BTN = ctk.CTkFont(family=MAIN_FONT_FAMILY, size=18, weight="bold")

        # Tech font for the URL and Folder boxes
        self.FONT_INPUT = ctk.CTkFont(family=INPUT_FONT_FAMILY, size=13)

        # Version number for easy updates
        self.VERSION_NUMBER = "v0.2.0"

        # Build UI
        self.setup_ui()

    def setup_ui(self):
        # 1. The "Fake" Rounded Window Background
        self.bg_frame = ctk.CTkFrame(self, fg_color=self.APP_BG)
        self.bg_frame.pack(fill="both", expand=True)

        # 3. MAIN CONTAINER (Parent is also self.bg_frame!)
        self.content_frame = ctk.CTkFrame(self.bg_frame, fg_color="transparent")
        self.content_frame.pack(pady=(20, 20), padx=20, fill="both", expand=True)
        self.content_frame.grid_columnconfigure(0, weight=1)
        # # Main Container
        # self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        # self.content_frame.pack(pady=20, padx=20, fill="both", expand=True)
        # self.content_frame.grid_columnconfigure(0, weight=1)

        # --- 1. URL SECTION ---
        self.url_label = ctk.CTkLabel(self.content_frame, text="Media URL", font=self.FONT_BOLD)
        self.url_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        # Container for URL + Floating Paste button
        self.url_container = ctk.CTkFrame(self.content_frame, fg_color="transparent", border_width=2,
                                          border_color=self.BORDER_HIDDEN)
        self.url_container.grid(row=1, column=0, columnspan=2, sticky="we", pady=(0, 20))
        self.url_container.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            self.url_container, placeholder_text="Paste link here...",
            height=55, corner_radius=18, font=self.FONT_INPUT,
            fg_color=self.ENTRY_BG, text_color=self.TEXT_MAIN,
            border_width=1, border_color=self.BORDER_HIDDEN
        )
        self.url_entry.grid(row=0, column=0, sticky="we")
        self.url_entry.bind("<FocusIn>", lambda e: self.on_focus_in(self.url_entry))
        self.url_entry.bind("<FocusOut>", lambda e: self.on_focus_out(self.url_entry))
        self.url_entry.bind("<Enter>", lambda e: self.url_entry.configure(border_color=self.BORDER_DEFAULT))
        self.url_entry.bind("<Leave>", lambda e: self.on_focus_out(self.url_entry))
        self.url_entry.bind("<KeyRelease>", self.validate_inputs)

        self.paste_btn = ctk.CTkButton(
            self.url_container, text="Paste", width=50, height=36,
            corner_radius=18, bg_color=self.ENTRY_BG, fg_color=self.ACTION_BTN,
            text_color=self.ACTION_TEXT, font=self.FONT_BOLD,
            hover_color=self.ACTION_HOVER, command=self.paste_url_from_clipboard
        )
        self.paste_btn.place(relx=1.0, rely=0.49, x=-10, y=0, anchor="e")

        # --- 2. FOLDER SECTION ---
        self.folder_label = ctk.CTkLabel(self.content_frame, text="Download Location", font=self.FONT_BOLD)
        self.folder_label.grid(row=2, column=0, sticky="w", pady=(0, 5))

        self.folder_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent", border_width=2,
                                         border_color=self.BORDER_HIDDEN)
        self.folder_frame.grid(row=3, column=0, columnspan=2, sticky="we", pady=(0, 20))
        self.folder_frame.grid_columnconfigure(0, weight=1)

        self.folder_entry = ctk.CTkEntry(
            self.folder_frame, placeholder_text="Select download folder...",
            height=55, corner_radius=18, font=self.FONT_INPUT,
            fg_color=self.ENTRY_BG, text_color=self.TEXT_MAIN,
            border_width=1, border_color=self.BORDER_HIDDEN
        )
        self.folder_entry.grid(row=0, column=0, sticky="we")
        self.folder_entry.bind("<FocusIn>", lambda e: self.on_focus_in(self.folder_entry))
        self.folder_entry.bind("<FocusOut>", lambda e: self.on_focus_out(self.folder_entry))
        self.folder_entry.bind("<Enter>", lambda e: self.folder_entry.configure(border_color=self.BORDER_DEFAULT))
        self.folder_entry.bind("<Leave>", lambda e: self.on_focus_out(self.folder_entry))
        self.folder_entry.bind("<KeyRelease>", self.validate_inputs)

        self.folder_browse_btn = ctk.CTkButton(
            self.folder_frame, text="Browse", width=50, height=36,
            corner_radius=18, bg_color=self.ENTRY_BG, fg_color=self.ACTION_BTN,
            text_color=self.ACTION_TEXT, font=self.FONT_BOLD,
            hover_color=self.ACTION_HOVER, command=self.select_folder
        )
        self.folder_browse_btn.place(relx=1.0, rely=0.49, x=-10, y=0, anchor="e")

        # 3. OPTIONS (Audio Toggle)
        # We style the label text to match the text theme
        self.audio_label = ctk.CTkLabel(self.content_frame, text="Audio Only", font=self.FONT_BOLD,
                                        text_color=self.TEXT_MAIN)
        self.audio_label.grid(row=4, column=0, sticky="w", pady=(0, 20))

        self.audio_switch = ctk.CTkSwitch(
            self.content_frame,
            text="",
            switch_width=40,  # Slightly sleeker width
            switch_height=20,  # Slightly sleeker height
            fg_color=self.ENTRY_BG,  # Track color when OFF (grey)
            progress_color=self.ACTION_BTN,  # Track color when ON (bright blue)
            button_color=self.ACTION_BTN,  # The thumb (white in light mode, light grey in dark mode)
            button_hover_color=self.ACTION_HOVER,
            border_width=2,  # <--- The new border thickness
            border_color=self.ACTION_BTN,
        )
        self.audio_switch.grid(row=4, column=0, sticky="w", padx=(88, 20), pady=(0, 20))

        # 4. PROGRESS BAR
        self.progress_bar = ctk.CTkProgressBar(
            self.content_frame,
            height=16,
            fg_color=self.ENTRY_BG,
            progress_color=self.ENTRY_BG,
            corner_radius=8,
            mode="determinate"
        )
        self.progress_bar.set(0)
        self.progress_bar.grid(row=5, column=0, columnspan=2, sticky="we", pady=(0, 20))

        # 5. MAIN ACTION BUTTON
        self.download_btn = ctk.CTkButton(
            self.content_frame,
            text="Enter a URL & Location",
            height=50,
            width=300,
            corner_radius=25,
            font=self.FONT_ACTION_BTN,
            state="disabled",
            fg_color=self.BTN_DISABLED,
            text_color_disabled=self.TEXT_DISABLED
        )
        self.download_btn.configure(command=self.start_download_thread)
        self.download_btn.grid(row=6, column=0, columnspan=2, sticky="s")

        # 6. VERSION LABEL
        self.version_label = ctk.CTkLabel(
            self.bg_frame,  # <--- Changed from self to self.bg_frame
            text=self.VERSION_NUMBER,
            font=self.FONT_SMALL,
            text_color=self.TEXT_VERSION,
            bg_color="transparent"  # Forces it to blend seamlessly
        )
        # Pulled 20px in from the right, 14px up from the bottom
        self.version_label.place(relx=1.0, rely=1.0, x=-20, y=-5, anchor="se")

        # 6a. Powered By Label
        self.credit_label = ctk.CTkLabel(
            self.bg_frame,  # <--- Changed from self to self.bg_frame
            text="Powered by yt-dlp",
            font=self.FONT_SMALL,
            text_color=self.TEXT_VERSION,
            bg_color="transparent"
        )
        # Pulled 20px in from the left, 14px up from the bottom
        self.credit_label.place(x=20, rely=1.0, y=-5, anchor="sw")

    # --- LOGIC METHODS ---

    def on_focus_in(self, widget):
        widget.configure(border_color=self.ENTRY_FOCUS)

    def on_focus_out(self, widget):
        if not widget.get().strip():
            widget.configure(border_color=self.BORDER_HIDDEN)
        else:
            widget.configure(border_color=self.BORDER_DEFAULT)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            self.folder_entry.configure(text_color=self.TEXT_MAIN, border_color=self.BORDER_DEFAULT)
            self.validate_inputs()

    def validate_inputs(self, event=None):
        url = self.url_entry.get().strip()
        folder = self.folder_entry.get().strip()

        # If BOTH fields are filled out AND the folder exists
        if url and folder and os.path.isdir(folder):
            self.download_btn.configure(
                state="normal",
                text="Download Now",
                fg_color=self.ACTION_BTN,
                text_color=self.ACTION_TEXT
            )
        else:
            # If they delete the URL or Folder, turn it back to grey
            self.download_btn.configure(
                state="disabled",
                text="Enter a URL & Location",
                fg_color=self.BTN_DISABLED,
                text_color=self.TEXT_DISABLED
            )

    def show_popup(self, title, message, folder=None):
        self.update_idletasks()

        # 1. Match the popup background to the app background
        popup = ctk.CTkToplevel(self, fg_color=self.APP_BG)
        popup.title(title)
        p_width, p_height = 400, 200

        # Center Calculation
        center_x = self.winfo_x() + (self.winfo_width() // 2) - (p_width // 2)
        center_y = self.winfo_y() + (self.winfo_height() // 2) - (p_height // 2)
        popup.geometry(f"{p_width}x{p_height}+{center_x}+{center_y}")
        popup.attributes("-topmost", True)

        # 2. Style the text to match main UI text
        label = ctk.CTkLabel(
            popup,
            text=message,
            wraplength=350,
            font=self.FONT_MAIN,
            text_color=self.TEXT_MAIN
        )
        label.pack(pady=(40, 20))

        # Container for buttons
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=20)

        # 3. Primary "OK" Button (Solid Blue)
        btn = ctk.CTkButton(
            btn_frame,
            text="OK",
            font=self.FONT_BOLD,
            width=120,
            height=36,
            corner_radius=18,
            fg_color=self.ACTION_BTN,
            hover_color=self.ACTION_HOVER,
            text_color=self.ACTION_TEXT,
            command=popup.destroy
        )
        btn.pack(side="left", padx=10)

        # 4. Secondary "Open Folder" Button (Ghost Style)
        if folder and os.path.exists(folder):
            open_btn = ctk.CTkButton(
                btn_frame,
                text="Open Folder",
                font=self.FONT_BOLD,
                width=120,
                height=36,
                corner_radius=18,
                bg_color="transparent",
                fg_color=self.ENTRY_BG,
                text_color=self.TEXT_MAIN,
                hover_color=self.BTN_HOVER,
                border_width=2,
                border_color=self.BORDER_DEFAULT,
                command=lambda: os.startfile(folder)
            )
            open_btn.pack(side="left", padx=10)

        # Lock focus to the popup until closed
        popup.grab_set()

    def start_download_thread(self):
        self.download_btn.configure(state="disabled", text="Downloading...")

        # Disable inputs while downloading
        self.url_entry.configure(state="disabled")
        self.folder_entry.configure(state="disabled")
        self.folder_browse_btn.configure(state="disabled")
        self.paste_btn.configure(state="disabled")
        self.audio_switch.configure(state="disabled")

        # Turn the bar blue and set it to 0% (determinate mode)
        self.progress_bar.configure(mode="determinate", progress_color=self.PROG_FILL)
        self.progress_bar.set(0)

        threading.Thread(target=self.download_media, daemon=True).start()

    def download_media(self):
        url = self.url_entry.get()
        folder = self.folder_entry.get().strip()
        is_audio = self.audio_switch.get()
        # 1. Use your new ultimate path function!
        ffmpeg_path = resource_path("ffmpeg", is_binary=True)

        # --- DIAGNOSTIC X-RAY ---
        print(f"\n--- FFMPEG DIAGNOSTICS ---")
        print(f"Looking for FFmpeg at: {ffmpeg_path}")
        print(f"Does the file exist? {os.path.exists(ffmpeg_path)}")
        if os.path.exists(ffmpeg_path):
            print(f"Is it executable? {os.access(ffmpeg_path, os.X_OK)}")
        print(f"--------------------------\n")
        # ... (keep your chmod logic here) ...
        if sys.platform != "win32" and os.path.exists(ffmpeg_path):
            try:
                import stat
                os.chmod(ffmpeg_path, os.stat(ffmpeg_path).st_mode | stat.S_IEXEC)
            except Exception as e:
                print(f"Permission setup failed: {e}")

        ydl_opts = {
            'format': 'bestaudio/best' if is_audio else 'bestvideo+bestaudio/best',
            'restrictfilenames': True,
            'noplaylist': True,
            'ffmpeg_location': ffmpeg_path,
            'outtmpl': os.path.join(folder, '%(title)s [%(id)s].%(ext)s'),
            'logger': MyLogger(),
            'progress_hooks': [self.download_progress_hook],
        }

        if is_audio:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }]
        else:
            ydl_opts['merge_output_format'] = 'mp4'

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.after(0, lambda: self.show_popup("Success", "Download Complete!", folder=folder))
        except Exception as e:
            self.after(0, lambda: self.show_popup("Error", "Download Failed."))
        finally:
            self.after(0, self.progress_bar.stop)
            self.after(0, lambda: self.progress_bar.configure(mode="determinate"))
            self.after(0, lambda: self.progress_bar.set(0))

            # Re-enable inputs
            self.after(0, lambda: self.url_entry.configure(state="normal"))
            self.after(0, lambda: self.folder_entry.configure(state="normal"))
            self.after(0, lambda: self.folder_browse_btn.configure(state="normal"))
            self.after(0, lambda: self.paste_btn.configure(state="normal"))
            self.after(0, lambda: self.audio_switch.configure(state="normal"))
            self.after(0, self.validate_inputs)

    def download_progress_hook(self, d):
        if d['status'] == 'downloading':
            # 1. Improved size detection
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)

            if total:
                percent = downloaded / total
                self.after(0, lambda p=percent: self.progress_bar.set(p))
                # Update button text with download speed
                speed = d.get('_speed_str', 'N/A')
                self.after(0, lambda s=speed: self.download_btn.configure(text=f"Downloading... ({s})"))
            else:
                # Fallback: If size is unknown, use indeterminate mode (bouncing bar)
                if self.progress_bar.cget("mode") != "indeterminate":
                    self.after(0, lambda: self.progress_bar.configure(mode="indeterminate"))
                    self.after(0, self.progress_bar.start)

        elif d['status'] == 'finished':
            # 2. Specific 'Merging' feedback
            self.after(0, self.progress_bar.stop)
            self.after(0, lambda: self.progress_bar.configure(mode="indeterminate"))
            self.after(0, self.progress_bar.start)
            self.after(0, lambda: self.download_btn.configure(text="Finalising File..."))

    def paste_url_from_clipboard(self):
        try:
            text = self.clipboard_get().strip()
        except Exception:
            return
        if text:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, text)
            self.validate_inputs()

    # --- WINDOW MOVEMENT LOGIC ---
    def start_move(self, event):
        # Record the exact X/Y of the mouse when the user clicks
        self.click_x = event.x
        self.click_y = event.y

    def do_move(self, event):
        # Calculate how far the mouse has moved
        deltax = event.x - self.click_x
        deltay = event.y - self.click_y

        # Apply the movement to the window's position on the screen
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    app = UniversalDownloader()
    app.mainloop()
