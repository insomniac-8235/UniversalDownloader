import customtkinter as ctk
from tkinter import filedialog
import os
import sys
import threading
from typing import Callable, Optional
from downloader import DownloadManager
from utilities import MyLogger, THEME, set_app_icon
from yt_dlp import YoutubeDL

class UIController:
    def __init__(self, root, download_manager, logger):
        self.root = root
        self.download_manager = download_manager
        self.logger = logger
        
        # Copy module-level THEME to instance (avoid mutation issues)
        self.theme = THEME.copy()
        
        # Get current mode
        ctk.set_appearance_mode("system")
        
        # Set app icon BEFORE UI setup
        set_app_icon(self.root)
        
        self.setup_ui()
        self.bind_events()

    def setup_ui(self):
        # Initialize fonts
        if sys.platform == "darwin":
            self.main_font = ctk.CTkFont(family=".AppleSystemUIFont", size=14)
            self.input_font = ctk.CTkFont(family="Menlo", size=14)
            self.version_font = ctk.CTkFont(family=".AppleSystemUIFont", size=10)
            self.button_font = ctk.CTkFont(family=".AppleSystemUIFont", size=15, weight="bold")
        else:
            self.main_font = ctk.CTkFont(family="Segoe UI", size=14)
            self.input_font = ctk.CTkFont(family="Consolas", size=14)
            self.version_font = ctk.CTkFont(family="Segoe UI", size=10)
            self.button_font = ctk.CTkFont(family="Segoe UI", size=15, weight="bold")
    
        # Create outer frame FIRST (covers entire window area)
        self.outer_frame = ctk.CTkFrame(
            self.root, 
            corner_radius=0,
            fg_color=self.theme["APP_BG"],
            border_width=0
        )
        self.outer_frame.pack(fill="both", expand=True)
        
        # Create content frame inside outer frame
        self.content_frame = ctk.CTkFrame(
            self.outer_frame, 
            fg_color=self.theme["APP_BG"],
            border_width=0,
        )
        self.content_frame.pack(pady=(0, 0), padx=20, fill="both", expand=False)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # URL Section
        self.url_label = ctk.CTkLabel(
            self.content_frame,
            text="Media URL",
            fg_color=self.theme["APP_BG"],
            font=self.main_font,
            text_color=self.theme["TEXT_MAIN"]
        )
        self.url_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.url_container = ctk.CTkFrame(
            self.content_frame,
            fg_color=self.theme["APP_BG"],
            border_width=0,
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
            text_color=self.theme["TEXT_MAIN"],
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
            text_color=self.theme["TEXT_ACTION"],
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
            border_color=self.theme["BORDER_DEFAULT"]
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
            bg_color=self.theme["APP_BG"],
            text_color=self.theme["TEXT_GHOST"],
            border_width=1,
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
            text_color=self.theme["TEXT_ACTION"],
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
            progress_color=self.theme["BTN_ACTION"],
            button_color="#808080",
            button_hover_color=self.theme["BTN_HOVER"],
            border_width=2,
            border_color=self.theme["BORDER_DEFAULT"]
        )
        self.audio_switch.grid(row=4, column=0, sticky="w", padx=(88, 20), pady=(0, 20))
        
        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(
            self.content_frame,
            height=16,
            fg_color=self.theme["PROG_BG"],
            progress_color=self.theme["PROG_FILL"],
            corner_radius=8,
            mode="determinate"
        )
        self.progress_bar.set(0)
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
        # URL Entry Events
        self.url_entry.bind("<FocusIn>", lambda e: self.on_focus_in(self.url_entry))
        self.url_entry.bind("<FocusOut>", lambda e: self.on_focus_out(self.url_entry))
        self.url_entry.bind("<Enter>", lambda e: self.url_entry.configure(border_color=self.theme["BORDER_HOVER"]))
        self.url_entry.bind("<Leave>", lambda e: self.on_focus_out(self.url_entry))
        self.url_entry.bind("<KeyRelease>", self.validate_inputs)
        
        # Folder Entry Events
        self.folder_entry.bind("<FocusIn>", lambda e: self.on_focus_in(self.folder_entry))
        self.folder_entry.bind("<FocusOut>", lambda e: self.on_focus_out(self.folder_entry))
        self.folder_entry.bind("<Enter>", lambda e: self.folder_entry.configure(border_color=self.theme["BORDER_HOVER"]))
        self.folder_entry.bind("<Leave>", lambda e: self.on_focus_out(self.folder_entry))
        self.folder_entry.bind("<KeyRelease>", self.validate_inputs)
        
        # Download Button
        self.download_btn.configure(command=lambda: self.on_download_button_click())
        
    def validate_inputs(self, event=None):
        url = self.url_entry.get().strip()
        folder = self.folder_entry.get().strip()

        if url and folder and os.path.isdir(folder):
            if self.download_btn.cget("text") not in ("Downloading...", "Finalising..."):
                self.download_btn.configure(
                    state="normal",
                    text="Download Now",
                    fg_color=self.theme["BTN_ACTION"],
                    hover_color=self.theme["BTN_HOVER"],
                    text_color=self.theme["TEXT_ACTION"]
                )
        elif self.download_btn.cget("text") not in ("Downloading...", "Finalising..."):
            self.download_btn.configure(
                state="disabled",
                text="Enter a URL & Location",
                fg_color=self.theme["BTN_DISABLED"],
                hover_color=self.theme["BTN_HOVER"],
                text_color_disabled=self.theme["TEXT_DISABLED"]
            )
        
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
            self.folder_entry.configure(text_color=self.theme["TEXT_MAIN"])
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
            
    def on_download_button_click(self):
        url = self.url_entry.get().strip()
        folder = self.folder_entry.get().strip()
        is_audio = self.audio_switch.get()

        # NEW: validate the URL before starting the download
        if url and folder and os.path.isdir(folder):
            try:
                # yt‑dlp will raise an exception if the URL is bad
                YoutubeDL({'quiet': True}).extract_info(url, download=False)
            except Exception as e:
                # Show an ERROR popup and stop
                self.show_popup("Error", False, str(e))
                return
        # ────────────

        if url and folder and os.path.isdir(folder):
            self.lock_ui("Downloading...")
            self.download_manager.set_progress_hook(self.download_progress_hook)

            # Run the download in a background thread so the UI stays responsive
            t = threading.Thread(
                target=self._download_thread,
                args=(url, folder, is_audio),
                daemon=True
            )
            t.start()
        elif self.download_btn.cget("text") not in ("Downloading...", "Finalising..."):
            self.download_btn.configure(
                state="disabled",
                text="Enter a URL & Location",
                fg_color=self.theme["BTN_DISABLED"],
                hover_color=self.theme["BTN_HOVER"],
                text_color_disabled=self.theme["TEXT_DISABLED"]
            )
    
    def download_progress_hook(self, progress):
        """
        Convert the 0-100 percentage from DownloadManager into the 0-1
        range that CTkProgressBar expects.
        """
        # Ensure we only update the progress bar on the main thread
        self.root.after(0, lambda p=progress: self.progress_bar.set(p / 100))
        
    # New helper method to run the download in a background thread
    def _download_thread(self, url: str, folder: str, is_audio: bool):
        try:
            success = self.download_manager.download_media(url, folder, is_audio)
            # Schedule the completion callback on the main thread
            self.root.after(0, self.download_complete, success, None)
        except Exception as exc:
            self.logger.error(f"Download failed: {exc}")
            self.root.after(0, self.download_complete, False, str(exc))

    def download_complete(self, success, error_detail=None):
        """Handle download completion or failure"""
        self.unlock_ui()
        self.show_popup("Download Complete!" if success else "Download Failed!", success, error_detail)
    
    def lock_ui(self, button_text="Downloading..."):
        """Lock all UI elements during download"""
        self.url_entry.configure(state="disabled")
        self.folder_entry.configure(state="disabled")
        
        for btn in (self.folder_browse_btn, self.paste_btn):
            btn.configure(state="disabled", fg_color=self.theme["BTN_DISABLED"], hover_color=self.theme["BTN_HOVER"])
        
        self.audio_switch.configure(state="disabled")
        
        self.download_btn.configure(
            state="disabled",
            text=button_text,
            fg_color=self.theme["BTN_DISABLED"],
            hover_color=self.theme["BTN_ACTION"],
            text_color_disabled=self.theme["TEXT_DISABLED"]
        )
    
    def unlock_ui(self):
        """Unlock all UI elements after download"""
        self.url_entry.configure(state="normal")
        self.folder_entry.configure(state="normal")
        
        self.folder_browse_btn.configure(
            state="normal",
            fg_color=self.theme["BTN_ACTION"],
            hover_color=self.theme["BTN_HOVER"]
        )
        
        self.paste_btn.configure(
            state="normal",
            fg_color=self.theme["BTN_ACTION"],
            hover_color=self.theme["BTN_HOVER"]
        )
        
        self.audio_switch.configure(
            state="normal",
            progress_color=self.theme["BTN_ACTION"],
            fg_color=self.theme["ENTRY_BG"],
            button_color=self.theme["BTN_ACTION"],
            border_color=self.theme["BORDER_DEFAULT"]
        )
        
        self.download_btn.configure(
            text="Enter a URL & Location",
            state="disabled",
            fg_color=self.theme["BTN_DISABLED"]
        )
        
        self.progress_bar.stop()
        self.progress_bar.set(0)
        
        self.validate_inputs()
    
    def show_popup(self, title: str, success: bool, error_detail: Optional[str] = None):
        """Show a popup dialog for download completion/failure or error."""
        popup = ctk.CTkToplevel(self.root)
        popup.resizable(True, True)
        popup.title(title)          # use the supplied title
        
        popup.grab_set()  # Make the popup modal
        
        width, height = 350, 140
        center_x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        center_y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{center_x}+{center_y}")
        
        # Main message – use the title
        label = ctk.CTkLabel(
            popup,
            text=title,
            wraplength=300,
            font=self.main_font,
            text_color=self.theme["TEXT_MAIN"]
        )
        label.pack(expand=True, pady=(20, 10))
        
        # Error details removed - only show title and close button
        
        btn = ctk.CTkButton(
            popup,
            text="Close",
            font=self.main_font,
            width=120,
            height=36,
            corner_radius=25,
            fg_color=self.theme["BTN_ACTION"],
            hover_color=self.theme["BTN_HOVER"],
            text_color=self.theme["TEXT_ACTION"],
            command=lambda: (popup.grab_release(), popup.destroy())
        )
        btn.pack(pady=(0, 20))

    def get_build_info(self):                                                                                 
        """Combines Version Number and Git Commit for the UI."""                                              
        version = "v0.2.1"  # Manually update this here for each release                                      
        try:                                                                                                  
            base_path = os.path.dirname(os.path.abspath(__file__))                                            
            commit_file_path = os.path.join(base_path, 'assets', 'commit.txt')                                
            with open(commit_file_path, "r") as f:                                                            
                commit = f.read().strip()                                                                     
            return f"{version} ({commit})"                                                                    
        except Exception:                                                                                     
            # Fallback for local development                                                                  
            return f"{version} (Dev)"
