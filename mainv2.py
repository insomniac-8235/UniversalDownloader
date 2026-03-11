import customtkinter as ctk
from tkinter import filedialog
import threading
import os
import sys
import shutil

def get_ffmpeg_path():
    if getattr(sys, 'frozen', False):
        # The application is frozen (i.e., running as a bundled app)
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        ffmpeg_path = os.path.join(base_path, 'ffmpeg')
        if not os.path.exists(ffmpeg_path):
            ffmpeg_path = os.path.join(base_path, 'ffmpeg.exe')  # For Windows
        return ffmpeg_path
    else:
        # The application is not frozen (i.e., running in development mode)
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path is None:
            raise FileNotFoundError("ffmpeg not found in PATH")
        return ffmpeg_path

def get_resource_path(relative_path: str):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)


def set_app_icon(window):
    if sys.platform == "win32":
        # Windows already embedded via --icon, runtime call optional
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
        if os.path.exists(icon_path):
            window.iconbitmap(icon_path)
    elif sys.platform.startswith("linux"):
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
        if os.path.exists(icon_path):
            try:
                from tkinter import PhotoImage
                window.iconphoto(True, PhotoImage(file=icon_path))
            except Exception:
                pass
    # macOS: no runtime icon call needed


# --- PYINSTALLER NOCONSOLE FIX ---
# If the app is compiled without a console, route all print statements to a black hole
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

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
        if sys.platform == "win32":
            self.ICON_FONT_NAME = "Segoe Fluent Icons"
            self.CLOSE_ICON = "\uE8BB"
            self.MIN_ICON = "\uE921"
            self.ICON_SIZE = 10
        else:
            self.ICON_FONT_NAME = "Arial"
            self.CLOSE_ICON = "✕"
            self.MIN_ICON = "—"
            self.ICON_SIZE = 14

        # Now create the actual Font object using those constants
        self.ICON_FONT = ctk.CTkFont(family=self.ICON_FONT_NAME, size=self.ICON_SIZE)

        # --- APPLICATION OF FONTS ---
        self.FONT_MAIN = ctk.CTkFont(family=MAIN_FONT_FAMILY, size=14)
        self.FONT_BOLD = ctk.CTkFont(family=MAIN_FONT_FAMILY, size=14, weight="bold")
        self.FONT_SMALL = ctk.CTkFont(family=MAIN_FONT_FAMILY, size=10)
        self.FONT_LARGE = ctk.CTkFont(family=MAIN_FONT_FAMILY, size=24)
        self.FONT_ACTION_BTN = ctk.CTkFont(family=MAIN_FONT_FAMILY, size=18, weight="bold")

        # Tech font for the URL and Folder boxes
        self.FONT_INPUT = ctk.CTkFont(family=INPUT_FONT_FAMILY, size=14)

        # Tracks active download
        self.downloading = False

        # Version number for easy updates
        self.VERSION_NUMBER = "v0.2.0"

        # 1. Window Setup
        self.geometry("500x420")

        if sys.platform == "win32":
            self.overrideredirect(True)
            self.after(100, self.apply_windows_fixes)
        elif sys.platform == "darwin":
            # This keeps the Traffic Lights but makes the background of the bar
            # match your APP_BG. It's the "Modern Mac" look.
            self.configure(background=self.APP_BG[1] if ctk.get_appearance_mode() == "Dark" else self.APP_BG[0])
            self.title("")  # Hides the text so it doesn't look cluttered

        # 2. Build the UI first! (This fills the 'empty' window)
        self.setup_ui()

        # 3. Call your icon logic
        set_app_icon(self)

    def apply_windows_fixes(self):
        """The Master Boot Sequence for a titleless Windows 11 App"""
        if sys.platform != "win32": return
        try:
            from ctypes import windll, c_int, byref, sizeof
            hwnd = windll.user32.GetParent(self.winfo_id())

            # A. Taskbar & Alt+Tab Fix
            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
            windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

            # B. Native Windows 11 Rounding
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWMWCP_ROUND = c_int(2)
            windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, byref(DWMWCP_ROUND), sizeof(DWMWCP_ROUND))

            # C. Mica Effect (Windows 11 22H2+)
            DWMWA_SYSTEMBACKDROP_TYPE = 38
            DWMSBT_MAINWINDOW = 2 # Mica effect
            windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_SYSTEMBACKDROP_TYPE, byref(c_int(DWMSBT_MAINWINDOW)), sizeof(c_int(DWMSBT_MAINWINDOW)))

            # D. Force Update
            self.withdraw()
            self.deiconify()
        except Exception as e:
            print(f"Windows Polish Failed: {e}")

    # --- DRAGGING LOGIC ---
    def start_move(self, event):
        # Because this is bound to title_bar, 'event.x/y' are
        # relative to the BAR, not the window.
        self._drag_data = {"x": event.x, "y": event.y}

    def do_move(self, event):
        if self._drag_data:
            deltax = event.x - self._drag_data["x"]
            deltay = event.y - self._drag_data["y"]

            new_x = self.winfo_x() + deltax
            new_y = self.winfo_y() + deltay

            self.geometry(f"+{new_x}+{new_y}")

    def set_appwindow(self):
        """ This allows the titleless window to show up in the Taskbar and Alt+Tab. """
        from ctypes import windll
        # Windows Extended Style flags
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080

        # 1. Find the window's handle (ID)
        hwnd = windll.user32.GetParent(self.winfo_id())

        # 2. Update the style to act like a 'top-level' app window
        style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
        windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

        # 3. Briefly hide and show to force Windows to update the taskbar icon
        self.withdraw()
        self.after(10, self.deiconify)
        
        self.enable_mica()
        
    def set_native_rounding(self):
        """ Tells Windows 11 to apply native rounded corners. """
        if sys.platform == "win32":
            try:
                from ctypes import windll, c_int, byref, sizeof

                # Attribute 33 = Corner Preference in Win11
                DWMWA_WINDOW_CORNER_PREFERENCE = 33
                DWMWCP_ROUND = c_int(2)  # 2 = Standard Rounding

                hwnd = windll.user32.GetParent(self.winfo_id())
                windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    DWMWA_WINDOW_CORNER_PREFERENCE,
                    byref(DWMWCP_ROUND),
                    sizeof(DWMWCP_ROUND)
                )
            except Exception:
                pass  # Silently fail on Windows 10

    def setup_ui(self):
        # 1. Main Background
        self.bg_frame = ctk.CTkFrame(self, fg_color=self.APP_BG, corner_radius=0)
        self.bg_frame.pack(fill="both", expand=True)

        # 2. THE DRAG SLITHER (Sized to 32px standard)
        self.title_bar = ctk.CTkFrame(self.bg_frame, fg_color="transparent", height=32)
        self.title_bar.pack(fill="x", side="top")
        self.title_bar.pack_propagate(False)

        self.title_bar.bind("<ButtonPress-1>", self.start_move)
        self.title_bar.bind("<B1-Motion>", self.do_move)

        # 3. THE EXIT BUTTON (Windows ONLY)
        if sys.platform == "win32":
            self.exit_btn = ctk.CTkButton(
                self.title_bar,
                text=self.CLOSE_ICON,
                font=self.ICON_FONT,
                width=46, height=32,
                corner_radius=0,
                fg_color="transparent",
                hover_color="#c42b1c",
                text_color=("#333333", "#ffffff"),
                command=self.destroy
            )
            self.exit_btn.place(relx=1.0, x=0, y=0, anchor="ne")

        # 4. CONTENT AREA ---
        self.content_frame = ctk.CTkFrame(self.bg_frame, fg_color="transparent")
        self.content_frame.pack(pady=(0, 20), padx=20, fill="both", expand=True)
        self.content_frame.grid_columnconfigure(0, weight=1)

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
        self.audio_label = ctk.CTkLabel(self.content_frame, text="Audio Only", font=self.FONT_BOLD,
                                        text_color=self.TEXT_MAIN)
        self.audio_label.grid(row=4, column=0, sticky="w", pady=(0, 20))

        self.audio_switch = ctk.CTkSwitch(
            self.content_frame,
            text="",
            switch_width=40,
            switch_height=20,
            fg_color=self.ENTRY_BG,
            progress_color=self.ACTION_BTN,
            button_color=self.ACTION_BTN,
            button_hover_color=self.ACTION_HOVER,
            border_width=2,
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
            self.bg_frame,
            font=self.FONT_SMALL,
            text_color=self.TEXT_VERSION,
            bg_color="transparent"
        )
        self.version_label.place(relx=1.0, rely=1.0, x=-20, y=-5, anchor="se")
        self.version_label.configure(text=self.get_build_info())

        # 6a. Powered By LABEL
        self.credit_label = ctk.CTkLabel(
            self.bg_frame,
            text="Powered by yt-dlp",
            font=self.FONT_SMALL,
            text_color=self.TEXT_VERSION,
            bg_color="transparent"
        )
        self.credit_label.place(x=20, rely=1.0, y=-5, anchor="sw")

    # --- LOGIC METHODS ---
    def minimize_window(self):
        self.overrideredirect(False)
        self.state('iconic')
        self.bind("<Map>", self.restore_window)

    def restore_window(self, event=None):
        if self.state() == 'normal':
            self.overrideredirect(True)
            self.after(10, self.set_appwindow)
            self.unbind("<Map>")

    def download_media(self):
        from yt_dlp import YoutubeDL
        url = self.url_entry.get().strip()
        folder = self.folder_entry.get().strip()
        is_audio = self.audio_switch.get()

        ffmpeg_path = get_ffmpeg_path()

        if sys.platform != "win32":
            if ffmpeg_path and os.path.exists(ffmpeg_path):
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

            self.after(0, lambda: self.show_popup("Download Complete!", folder=folder, success=True))
        except Exception as e:
            self.after(0, lambda e=e: self.show_popup(
                "Download Failed!",
                folder=None,
                success=False,
                error_detail=str(e)
            ))
        finally:
            self.after(0, lambda: self.progress_bar.stop())
            self.after(0, lambda: self.progress_bar.set(0))
            self.after(0, self.unlock_ui)

    def validate_inputs(self, event=None):
        url = self.url_entry.get().strip()
        folder = self.folder_entry.get().strip()

        if url and folder and os.path.isdir(folder):
            if self.download_btn.cget("text") not in ("Downloading...", "Finalising File..."):
                self.download_btn.configure(
                    state="normal",
                    text="Download Now",
                    fg_color=self.ACTION_BTN,
                    hover_color="#448BD3",
                    text_color=self.ACTION_TEXT
                )
        else:
            if self.download_btn.cget("text") not in ("Downloading...", "Finalising File..."):
                self.download_btn.configure(
                    state="disabled",
                    text="Enter a URL & Location",
                    fg_color=self.BTN_DISABLED,
                    hover_color=self.BTN_HOVER,
                    text_color_disabled=self.TEXT_DISABLED
                )

    def start_download_thread(self):
        if self.downloading:
            return

        self.downloading = True
        self.lock_ui("Downloading...")

        self.progress_bar.configure(mode="determinate", progress_color=self.PROG_FILL)
        self.progress_bar.set(0)

        threading.Thread(target=self.download_media, daemon=True).start()

    def lock_ui(self, button_text):
        self.url_entry.configure(state="disabled")
        self.folder_entry.configure(state="disabled")

        for btn in (self.folder_browse_btn, self.paste_btn):
            btn.configure(state="disabled", fg_color=self.BTN_DISABLED, hover_color=self.BTN_DISABLED)

        self.audio_switch.configure(
            state="disabled",
            progress_color=self.BTN_DISABLED,
            fg_color=self.BTN_DISABLED,
            button_color=self.BTN_DISABLED
        )

        self.download_btn.configure(
            state="disabled",
            text=button_text,
            fg_color=self.BTN_DISABLED,
            hover_color=self.BTN_HOVER,
            text_color=self.TEXT_DISABLED
        )

    def unlock_ui(self):
        self.url_entry.configure(state="normal")
        self.folder_entry.configure(state="normal")

        self.folder_browse_btn.configure(
            state="normal",
            fg_color=self.ACTION_BTN,
            hover_color=self.ACTION_HOVER
        )

        self.paste_btn.configure(
            state="normal",
            fg_color=self.ACTION_BTN,
            hover_color=self.ACTION_HOVER
        )

        self.audio_switch.configure(
            state="normal",
            progress_color=self.ACTION_BTN,
            fg_color=self.ENTRY_BG,
            button_color=self.ACTION_BTN
        )

        self.download_btn.configure(
            text="Enter a URL & Location",
            state="disabled",
            fg_color=self.BTN_DISABLED
        )

        self.downloading = False
        self.validate_inputs()

    def download_progress_hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                percent = downloaded / total
                self.after(0, lambda p=percent: self.progress_bar.set(p))
            else:
                self.after(0, lambda: self.progress_bar.configure(mode="indeterminate"))
                self.after(0, self.progress_bar.start)

        elif d['status'] == 'finished':
            self.after(0, lambda: self.download_btn.configure(text="Finalising File..."))
            self.after(0, lambda: self.progress_bar.configure(mode="indeterminate"))
            self.after(0, self.progress_bar.start)

    def show_popup(self, message, folder=None, success=True, error_detail=None):
        self.update_idletasks()
        popup = ctk.CTkToplevel(self, fg_color=self.APP_BG)
        popup.overrideredirect(True)
        popup.resizable(False, False)

        popup.grab_set()

        width, height = 350, 160 if error_detail else 140
        center_x = self.winfo_x() + (self.winfo_width() // 2) - (width // 2)
        center_y = self.winfo_y() + (self.winfo_height() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{center_x}+{center_y}")

        if sys.platform == "win32":
            try:
                from ctypes import windll, byref, sizeof, c_int
                hwnd = windll.user32.GetParent(popup.winfo_id())
                DWMWA_WINDOW_CORNER_PREFERENCE = 33
                DWMWCP_ROUND = c_int(2)
                windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE,
                                                    byref(DWMWCP_ROUND), sizeof(DWMWCP_ROUND))
            except Exception:
                pass

        full_message = str(message)
        if error_detail:
            full_message += "\n\n" + str(error_detail)[:150] + "..."

        label = ctk.CTkLabel(
            popup,
            text=full_message,
            wraplength=300,
            font=self.FONT_BOLD,
            text_color=self.TEXT_MAIN
        )
        label.pack(expand=True, pady=(20, 10))

        btn_color = self.ACTION_BTN if success else self.BTN_DISABLED
        btn_hover = self.ACTION_HOVER if success else self.BTN_DISABLED
        btn_text_color = self.ACTION_TEXT if success else self.TEXT_DISABLED

        btn = ctk.CTkButton(
            popup,
            text="Close",
            font=self.FONT_BOLD,
            width=120,
            height=36,
            corner_radius=25,
            fg_color=btn_color,
            hover_color=btn_hover,
            text_color=btn_text_color,
            command=lambda: (popup.grab_release(), popup.destroy())
        )
        btn.pack(pady=(0, 20))

    def on_focus_in(self, widget):
        widget.configure(border_color=self.ENTRY_FOCUS)
        widget.configure(text_color=("#000000", "#ffffff"))

    def on_focus_out(self, widget):
        if not widget.get().strip():
            widget.configure(border_color=self.BORDER_HIDDEN)
            widget.configure(text_color=self.TEXT_GHOST)
        else:
            widget.configure(border_color=self.BORDER_DEFAULT)
            widget.configure(text_color=self.TEXT_MAIN)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            self.folder_entry.configure(text_color=self.TEXT_MAIN, border_color=self.BORDER_DEFAULT)
            self.validate_inputs()

    def paste_url_from_clipboard(self):
        try:
            text = self.clipboard_get().strip()
        except Exception:
            return
        if text:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, text)
            self.validate_inputs()

    def enable_mica(self):
        if sys.platform != "win32":
            return

        try:
            from ctypes import windll, byref, sizeof, c_int

            hwnd = windll.user32.GetParent(self.winfo_id())

            DWMWA_SYSTEMBACKDROP_TYPE = 38
            DWMSBT_MAINWINDOW = 2

            value = c_int(DWMSBT_MAINWINDOW)

            windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_SYSTEMBACKDROP_TYPE,
                byref(value),
                sizeof(value)
            )

        except Exception as e:
            print("Mica failed:", e)

    def get_build_info(self):
        version = "v0.2.1"
        try:
            path = get_resource_path("assets/commit.txt")
            with open(path, "r") as f:
                commit = f.read().strip()
            return f"{version} ({commit})"
        except Exception:
            return f"{version} (Dev)"

if __name__ == "__main__":
    app = UniversalDownloader()
    app.mainloop()
