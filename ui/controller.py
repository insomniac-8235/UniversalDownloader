import customtkinter as ctk
from tkinter import filedialog
import os
import sys
from typing import Dict, Any 
from utilities.theme import THEME
# No need to import ThreadPoolManager here specifically, type hints handle it

class ThemedDialog(ctk.CTkToplevel):
    def __init__(self, master, title, message):
        super().__init__(master)
        self.title(title)
        self.geometry("300x150")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        
        # Center the dialog relative to the main window
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - 150
        y = master.winfo_y() + (master.winfo_height() // 2) - 75
        self.geometry(f"+{x}+{y}")

        self.label = ctk.CTkLabel(self, text=message, wraplength=250)
        self.label.pack(pady=20, padx=20)
        
        self.btn = ctk.CTkButton(self, text="OK", command=self.destroy)
        self.btn.pack(pady=10)
        self.grab_set()

class UIController:
    # MODIFIED: queue_manager can be None initially to handle circular dependency
    def __init__(self, root, queue_manager=None):
        self.root = root
        self.queue = queue_manager # Store queue_manager
        
        # Copy module-level THEME to instance (avoid mutation issues)
        self.theme = THEME.copy()
        
        ctk.set_appearance_mode("system")  # Use system theme (light/dark)
        
        self.setup_ui()
        self.bind_events()
        self._debounce_timer = None
        
        # REMOVED: No longer needs to establish progress callback here.
        # This is now handled when ThreadPoolManager is initialized in main.py
        # because ThreadPoolManager stores a reference to this UIController.
        # self.queue.set_progress_callback(self.on_progress_update)
        
    def setup_ui(self):
        # Initialize fonts
        if sys.platform == "darwin":
            self.main_font = ctk.CTkFont(family=".AppleSystemUIFont", size=13, weight="bold")
            self.input_font = ctk.CTkFont(family="Menlo", size=14)
            self.version_font = ctk.CTkFont(family=".AppleSystemUIFont", size=10)
            self.button_font = ctk.CTkFont(family=".AppleSystemUIFont", size=15, weight="bold")
        else:
            self.main_font = ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
            self.input_font = ctk.CTkFont(family="Consolas", size=14)
            self.version_font = ctk.CTkFont(family="Segoe UI", size=10)
            self.button_font = ctk.CTkFont(family="Segoe UI", size=15, weight="bold")
    
    # Create outer frame FIRST (covers entire window area)
        self.outer_frame = ctk.CTkFrame(
            self.root, 
            corner_radius=0,
            fg_color=self.theme["APP_BG"],
            # border_width=0
        )
        self.outer_frame.pack(fill="both", expand=True)
        
        # Create content frame inside outer frame
        self.content_frame = ctk.CTkFrame(
            self.outer_frame, 
            fg_color=self.theme["APP_BG"],
            # border_width=0,
        )
        self.content_frame.pack(pady=(0, 0), padx=20, fill="both", expand=False)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # URL Section
        self.url_label = ctk.CTkLabel(
            self.content_frame,
            text="Media URL",
            # fg_color=self.theme["APP_BG"],
            font=self.main_font,
            text_color=self.theme["TEXT_MAIN"]
        )
        self.url_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.url_container = ctk.CTkFrame(
            self.content_frame,
            #fg_color=self.theme["APP_BG"],
            # border_width=0,
        )
        self.url_container.grid(row=1, column=0, columnspan=2, sticky="we", pady=(0, 20))
        self.url_container.grid_columnconfigure(0, weight=1)
        
        # URL Entry
        self.url_entry = ctk.CTkEntry(
            self.url_container,
            placeholder_text="Paste link here...",
            height=55,
            corner_radius=18,
            font=self.input_font,
            bg_color=self.theme["APP_BG"],
            fg_color=self.theme["ENTRY_BG"],
            text_color=self.theme["TEXT_ENTRY"],
            border_width=1,
        )
        self.url_entry.grid(row=0, column=0, sticky="we")
        
        self.paste_btn = ctk.CTkButton(
            self.url_container,
            text="Paste",
            width=50,
            height=36,
            corner_radius=18,
            font=self.button_font,
            bg_color=self.theme["ENTRY_BG"],
            fg_color=self.theme["BTN_ACTION"],  
            text_color=self.theme["TEXT_ACTION_BTN"],
            hover_color=self.theme["BTN_HOVER"],
            command=self.paste_url_from_clipboard
        )
        self.paste_btn.place(relx=1.0, rely=0.49, x=-10, y=0, anchor="e")
        
        # Folder Section
        self.folder_label = ctk.CTkLabel(
            self.content_frame,
            text="Download Location",
            font=self.main_font,
            text_color=self.theme["TEXT_MAIN"]
        )
        self.folder_label.grid(row=2, column=0, sticky="w", pady=(0, 5))
        
        self.folder_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color=self.theme["APP_BG"],
            border_width=0,
            # border_color=self.theme["BORDER_DEFAULT"]
        )
        self.folder_frame.grid(row=3, column=0, columnspan=2, sticky="we", pady=(0, 20))
        self.folder_frame.grid_columnconfigure(0, weight=1)
        
        # Folder Entry
        self.folder_entry = ctk.CTkEntry(
            self.folder_frame,
            placeholder_text="Select download folder...",
            height=55,
            corner_radius=18,
            font=self.input_font,
            text_color=self.theme["TEXT_GHOST"],
            border_width=1,
            fg_color=self.theme["ENTRY_BG"],
            border_color=self.theme["BORDER_DEFAULT"]
        )
        self.folder_entry.grid(row=0, column=0, sticky="we")
        
        self.folder_browse_btn = ctk.CTkButton(
            self.folder_frame,
            text="Browse",
            width=50,
            height=36,
            corner_radius=18,
            font=self.button_font,
            bg_color=self.theme["ENTRY_BG"],
            fg_color=self.theme["BTN_ACTION"],
            text_color=self.theme["TEXT_ACTION_BTN"],
            hover_color=self.theme["BTN_HOVER"],
            command=self.select_folder
        )
        self.folder_browse_btn.place(relx=1.0, rely=0.49, x=-10, y=0, anchor="e")
        
        # Audio Switch
        self.audio_label = ctk.CTkLabel(
            self.content_frame,
            text="Audio Only",
            font=self.main_font,
            text_color=self.theme["TEXT_MAIN"]
        )
        self.audio_label.grid(row=4, column=0, sticky="w", pady=(0, 20))
        
        self.audio_switch = ctk.CTkSwitch(
            self.content_frame,
            text="",
            switch_width=40,
            switch_height=20,
            fg_color=self.theme["ENTRY_BG"],
            progress_color=self.theme["PROG_FILL"],
            button_color=self.theme["SWITCH_BTN"],
            button_hover_color=self.theme["BTN_HOVER"],
            border_width=2,
            # border_color=self.theme["BORDER_DEFAULT"]
        )
        self.audio_switch.grid(row=4, column=0, sticky="w", padx=(88, 20), pady=(0, 20))
        
        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(
            self.content_frame,
            height=16,
            fg_color=self.theme["PROG_BG"],
            progress_color=self.theme["PROG_FILL"],
            corner_radius=8,
            mode="indeterminate" # CHANGED: Set to indeterminate mode
        )
        # REMOVED: self.progress_bar.set(0) # Not needed for indeterminate mode
        self.progress_bar.grid(row=5, column=0, columnspan=2, sticky="we", pady=(0, 20))
        
        # Download Button
        self.download_btn = ctk.CTkButton(
            self.content_frame,
            text="Enter a URL & Location",
            height=50,
            width=300,
            corner_radius=25,
            state="disabled",
            font=self.button_font,
            fg_color=self.theme["BTN_DISABLED"],
            text_color_disabled=self.theme["TEXT_DISABLED"]
        )
        self.download_btn.grid(row=7, column=0, sticky="s")
        
        # Version Labels
        self.version_label = ctk.CTkLabel(
            self.outer_frame,
            text=self.get_build_info(),
            font=self.version_font,
            text_color=self.theme["TEXT_VERSION"],
            bg_color="transparent"
        )
        self.version_label.place(relx=1.0, rely=1.0, x=-20, y=-5, anchor="se")
        
        self.credit_label = ctk.CTkLabel(
            self.outer_frame,
            text="Powered by yt-dlp",
            font=self.version_font,
            text_color=self.theme["TEXT_VERSION"],
            bg_color="transparent"
        )
        self.credit_label.place(x=20, rely=1.0, y=-5, anchor="sw")
        
    def bind_events(self):
        # URL Entry Events - batch updates to respect 10Hz limit
        self.url_entry.bind("<FocusIn>", lambda e: self.on_focus_in(self.url_entry))
        self.url_entry.bind("<FocusOut>", lambda e: self.on_focus_out(self.url_entry))
        self.url_entry.bind("<Enter>", lambda e: self.url_entry.configure(border_color=self.theme["BORDER_HOVER"]))
        self.url_entry.bind("<Leave>", lambda e: self.on_focus_out(self.url_entry))
        self.url_entry.bind("<KeyRelease>", self._debounced_validate_inputs)
        
        # Folder Entry Events - batch updates to respect 10Hz limit
        self.folder_entry.bind("<FocusIn>", lambda e: self.on_focus_in(self.folder_entry))
        self.folder_entry.bind("<FocusOut>", lambda e: self.on_focus_out(self.folder_entry))
        self.folder_entry.bind("<Enter>", lambda e: self.folder_entry.configure(border_color=self.theme["BORDER_HOVER"]))
        self.folder_entry.bind("<Leave>", lambda e: self.on_focus_out(self.folder_entry))
        self.folder_entry.bind("<KeyRelease>", self._debounced_validate_inputs)
        
        # Download Button - batch update on state change
        # UPDATE: Change the download_btn command to call start_download
        self.download_btn.configure(command=self.start_download)

    def start_download(self):
        """Validate inputs and trigger the queue if valid"""
        url = self.url_entry.get().strip()
        folder = self.folder_entry.get().strip()
        
        # Basic URL validation
        if not url.startswith("http"):
            self.on_invalid_url("URL must start with http:// or https://")
            return
            
        # If valid, proceed to queue
        if self.queue:
            self.queue(url, folder, self.audio_switch.get())

    def on_invalid_url(self, error_msg: str):
        """Handle invalid URL errors"""
        self.root.after(0, lambda: ThemedDialog(self.root, "Invalid URL", f"Invalid URL provided:\n{error_msg}"))

    def get_build_info(self):
        """Combines Version Number and Git Commit for the UI."""
        version = "v0.2.1"  # Manually update this here for each release
        try:
            # Path to assets/ is relative to the project root, not the ui/ directory.
            # We go up one level from this file's directory to get the project root.
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            commit_file_path = os.path.join(project_root, 'assets', 'commit.txt')
            with open(commit_file_path, "r") as f:
                commit = f.read().strip()
            return f"{version} ({commit})"
        except Exception:
            # Fallback for local development
            return f"{version} (Dev)"

    # REMOVED: set_progress_callback is no longer needed in UIController
    # def set_progress_callback(self, callback):
    #     """Set the progress callback to be called when download progress updates"""
    #     self._progress_callback = callback
        
    def on_focus_in(self, widget):
        widget.configure(border_color=self.theme["ENTRY_FOCUS"])
        widget.configure(text_color=(self.theme["TEXT_MAIN"]))
        widget.configure(border_color=self.theme["ENTRY_FOCUS"])
        
    def on_focus_out(self, widget):
        if not widget.get().strip():
            widget.configure(border_color=self.theme["BORDER_DEFAULT"])
        else:
            widget.configure(border_color=self.theme["BORDER_DEFAULT"])
            widget.configure(text_color=self.theme["TEXT_MAIN"])
    
    def select_folder(self):
        if folder := filedialog.askdirectory():
            self.folder_entry.delete(0, "end")  
            self.folder_entry.insert(0, folder)
            self.folder_entry.configure(text_color=self.theme["TEXT_ENTRY"])
            self.validate_inputs()
        
    def paste_url_from_clipboard(self):
        try:
            text = self.root.clipboard_get().strip()
        except Exception:
            return
        if text:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, text)
            self.validate_inputs()

    def on_download_complete(self, url, folder, is_audio):
        """Handle download completion and show popup"""
        # Ensure UI updates are on the main thread
        self.root.after(0, lambda: self.progress_bar.stop()) 
        self.root.after(0, lambda: self.progress_bar.set(0)) 
        
        self.root.after(0, lambda: self.download_btn.configure(
            state="disabled",
            text="Download Complete",
            fg_color=self.theme["BTN_DISABLED"],
            hover_color=self.theme["BTN_HOVER"],
            text_color=self.theme["TEXT_ACTION_BTN"]
        ))
        
        # Show completion popup after a short delay
        self.root.after(100, lambda: ThemedDialog(self.root, "Download Complete", f"Download completed successfully!\nLocation: {folder}"))
        
    def on_download_error(self, error_msg):
        """Handle download errors"""
        # Ensure UI updates are on the main thread
        self.root.after(0, lambda: self.progress_bar.stop()) 
        self.root.after(0, lambda: self.progress_bar.set(0)) 
        
        self.root.after(0, lambda: self.download_btn.configure(
            state="disabled",
            text="Download Failed",
            fg_color=self.theme["BTN_DISABLED"],
            hover_color=self.theme["BTN_HOVER"],
            text_color_disabled=self.theme["TEXT_DISABLED"]
        ))
        
        # Show error popup
        self.root.after(100, lambda: ThemedDialog(self.root, "Download Error", f"Download failed:\n{error_msg}"))

    def on_progress_update(self, d: Dict[str, Any]): 
        """Handle progress updates from the download worker to control indeterminate bar"""
        status = d.get('status')
        # Schedule the UI update on the main thread to prevent errors
        if status == 'downloading':
            self.root.after(0, self.progress_bar.start) # Start indeterminate bar
        elif status in ['finished', 'error']:
            self.root.after(0, self.progress_bar.stop)  # Stop indeterminate bar
            self.root.after(0, lambda: self.progress_bar.set(0)) # Reset to empty
        # If 'status' is not downloading, finished, or error, the bar remains in its current state
        # (e.g., pre-processing state, where it might be stopped initially or awaiting status).

    def validate_inputs(self):
        """Validate inputs and enable/disable download button based on validity"""
        url = self.url_entry.get().strip()
        folder = self.folder_entry.get().strip()

        if url and folder:
            self.download_btn.configure(
                state="normal",
                text="Download",
                fg_color=self.theme["BTN_ACTION"],
                hover_color=self.theme["BTN_HOVER"],
                text_color=self.theme["TEXT_ACTION_BTN"]
            )
        else:
            self.download_btn.configure(
                state="disabled",
                text="Enter a URL & Location",
                fg_color=self.theme["BTN_DISABLED"],
                text_color_disabled=self.theme["TEXT_DISABLED"]
            )

    def _debounced_validate_inputs(self, event):
        """Debounced input validation to respect 10Hz limit"""
        if self._debounce_timer is not None:
            self.root.after_cancel(self._debounce_timer)
        
        self._debounce_timer = self.root.after(100, self.validate_inputs)
