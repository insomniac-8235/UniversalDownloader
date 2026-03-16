import customtkinter as ctk
from tkinter import Tk, filedialog
import os
import sys
from utils.theme import THEME
from worker.download_worker import DownloadWorker



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
    def __init__(self, root, worker=None, queue_manager=None):
        self.root = root
        self.worker = worker
        self.progress_title = None  # Initialize progress_title attribute
        self.queue = queue_manager # Store queue_manager
        # Create the progress title widget
        # self.create_progress_title(1)

        # Bind the worker progress hook to the on_worker_progress method
        self.worker.set_progress_hook(self.on_worker_progress)

        # Copy module-level THEME to instance (avoid mutation issues)
        self.theme = THEME.copy()
        
        ctk.set_appearance_mode("system")  # Use system theme (light/dark)
        
        self.setup_ui()
        self.bind_events()
        self._debounce_timer = None

        self.downloading = False
        self.current_task = None

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
            mode="determinate"
        )
        self.progress_bar.set(0)
        self.progress_bar.grid(row=5, column=0, columnspan=2, sticky="we", pady=(0, 20))
        
        self.download_card = ctk.CTkFrame(
            self.content_frame,
            corner_radius=16,
            fg_color=self.theme["ENTRY_BG"]
        )

        self.download_card.grid(row=6, column=0, columnspan=2, sticky="we", pady=(10,20))
        self.download_card.grid_columnconfigure(0, weight=1)

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
        self.url_entry.bind("<KeyRelease>", self.debounced_validate_inputs)
        
        # Folder Entry Events - batch updates to respect 10Hz limit
        self.folder_entry.bind("<FocusIn>", lambda e: self.on_focus_in(self.folder_entry))
        self.folder_entry.bind("<FocusOut>", lambda e: self.on_focus_out(self.folder_entry))
        self.folder_entry.bind("<Enter>", lambda e: self.folder_entry.configure(border_color=self.theme["BORDER_HOVER"]))
        self.folder_entry.bind("<Leave>", lambda e: self.on_focus_out(self.folder_entry))
        self.folder_entry.bind("<KeyRelease>", self.debounced_validate_inputs)
        
        # Download Button - batch update on state change
        # UPDATE: Change the download_btn command to call start_download
        self.download_btn.configure(command=self.start_download)

    def update_status(self, message, success=True):
        """Update the status label with a message"""
        color = "green" if success else "red"
        self.status_label.config(text=message, fg=color)
        self.root.update_idletasks()

    def download_success(self, task_info):
        """Handle successful download"""
        message = f"Task Completed: {task_info}"
        self.update_status(message, success=True)

    def download_error(self, task_info):
        """Handle failed download"""
        message = f"ERROR: Worker {task_info['worker_id']} error: {task_info.get('error', 'Unknown error')}"
        self.update_status(message, success=False)
    
    def stop_progress(self):
        """Stop the progress bar and reset it"""
        self.progress_bar.config(value=0)
        self.progress_bar["state"] = "disabled"

    # def start_download(self):

    #     if self.downloading:
    #         # Cancel download
    #         if self.queue:
    #             self.queue.stop_current()
    #         self.set_downloading_state(False)
    #         return

    #     url = self.url_entry.get().strip()
    #     folder = self.folder_entry.get().strip()

    #     if not url.startswith("http"):
    #         self.on_invalid_url("URL must start with http:// or https://")
    #         return

    #     self.current_task = {
    #         "url": url,
    #         "folder": folder,
    #         "audio": self.audio_switch.get()
    #     }

    #     self.set_downloading_state(True)

    #     if self.queue:
    #         self.queue.enqueue(
    #             url,
    #             folder,
    #             self.audio_switch.get()
    #         )

    def on_invalid_url(self, error_msg: str):
        """Handle invalid URL errors"""
        self.root.after(0, lambda: ThemedDialog(self.root, "Invalid URL", f"Invalid URL provided:\n{error_msg}"))

    def get_build_info(self):
        """
        Automatically retrieves Version and Commit SHA from the baked-in 
        assets folder, ensuring the UI always matches the build metadata.
        """
        # Determine the base directory (Bundle vs. Local Dev)
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            # Assuming this script is in ui/ and assets/ is in project root
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        v_path = os.path.join(base_path, 'assets', 'version.txt')
        c_path = os.path.join(base_path, 'assets', 'commit.txt')

        try:
            with open(v_path, "r") as v_file, open(c_path, "r") as c_file:
                version = v_file.read().strip()
                commit = c_file.read().strip()
            return f"{version} ({commit})"
        except FileNotFoundError:

            return "v0.0.0-dev (local)"
        except Exception as e:
            return f"Error loading version: {str(e)}"

    def on_focus_in(self, widget):
        if widget == self.url_entry or widget == self.folder_entry:
            widget.configure(border_color=self.theme["ENTRY_FOCUS"])
            widget.configure(text_color=self.theme["TEXT_MAIN"])

    def on_focus_out(self, widget):
        if not widget.get().strip():
            widget.configure(border_color=self.theme["BORDER_DEFAULT"])
            widget.configure(text_color=self.theme["TEXT_GHOST"])
        else:
            widget.configure(border_color=self.theme["ENTRY_FOCUS"])
            widget.configure(text_color=self.theme["TEXT_ENTRY"])

    
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

    # def on_download_complete(self, url, folder, is_audio):
    #     """Handle download completion and show popup"""
    #     # Ensure UI updates are on the main thread
    #     self.root.after(0, lambda: self.progress_bar.stop())
    #     self.root.after(0, lambda: self.progress_bar.set(0)) 
        
    #     # Re-enable the button or set it to "Ready"
    #     self.root.after(0, lambda: self.download_btn.configure(
    #         state="normal", # Changed from 'disabled' so you can download again!
    #         text="Download Another",
    #         fg_color=self.theme["BTN_DISABLED"]
    #     ))
        
    #     # Show your custom ThemedDialog
    #     self.root.after(100, lambda: ThemedDialog(
    #         self.root, 
    #         "Download Complete", 
    #         f"Successfully saved to:\n{folder}"
    #     ))
        
    # def on_download_error(self, url, folder, error_msg):
    #     """Handle download errors"""
    #     # Ensure UI updates are on the main thread
    #     self.root.after(0, lambda: self.progress_bar.stop()) 
    #     self.root.after(0, lambda: self.progress_bar.set(0)) 
        
    #     self.root.after(0, lambda: self.download_btn.configure(
    #         state="disabled",
    #         text="Download Failed",
    #         fg_color=self.theme["BTN_DISABLED"],
    #         hover_color=self.theme["BTN_HOVER"],
    #         text_color_disabled=self.theme["TEXT_DISABLED"]
    #     ))
        
        # Show error popup
        self.root.after(100, lambda: ThemedDialog(self.root, "Download Error", f"Download failed:\n{error_msg}"))

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

    def debounced_validate_inputs(self, event):
        """Debounced input validation to respect 10Hz limit"""
        if self._debounce_timer is not None:
            self.root.after_cancel(self._debounce_timer)
        
        self._debounce_timer = self.root.after(100, self.validate_inputs)

    def set_downloading_state(self, active: bool):
        """Lock or unlock UI controls."""

        self.downloading = active
        entry_state = "disabled" if active else "normal"

        self.url_entry.configure(state=entry_state)
        self.folder_entry.configure(state=entry_state)
        self.audio_switch.configure(state=entry_state)
        self.paste_btn.configure(state=entry_state)
        self.folder_browse_btn.configure(state=entry_state)

        if active:
            self.download_btn.configure(
                text="Cancel",
                state="normal",
                fg_color="#d9534f"
            )
            self.progress_bar.start()
        else:
            self.download_btn.configure(
                text="Download",
                state="normal",
                fg_color=self.theme["BTN_ACTION"]
            )
            self.progress_bar.stop()
            self.progress_bar.set(0)

    # def on_worker_progress(self, d: Dict[str, Any]):

    #     status = d.get("status")

    #     if status == "downloading":

    #         percent_str = d.get("_percent_str", "0%")
    #         speed = d.get("_speed_str", "")
    #         eta = d.get("_eta_str", "")
    #         downloaded = d.get("_downloaded_bytes_str", "")
    #         total = d.get("_total_bytes_str", "")

    #         try:
    #             percent = float(percent_str.replace("%","")) / 100
    #         except Exception:
    #             percent = 0

    #         self.root.after(0, lambda: self.progress_bar.set(percent))

    #         self.root.after(0, lambda: self.metric_size.configure(
    #             text=f"{downloaded} / {total}"
    #         ))

    #         self.root.after(0, lambda: self.metric_speed.configure(
    #             text=speed
    #         ))

    #         self.root.after(0, lambda: self.metric_eta.configure(
    #             text=f"ETA {eta}"
    #         ))

    #         self.root.after(0, lambda: self.progress_title.configure(
    #             text=f"Downloading {percent_str}"
    #         ))

    #     elif status == "finished":

    #         self.root.after(0, lambda: self.progress_title.configure(
    #             text="Processing file..."
    #         ))

    def on_progress_update(self, progress_data: dict):
        """
        Receives download progress from the worker.
        Can forward it to the progress bar or a card.
        """
        status = progress_data.get('status')
        if status == 'downloading':
            percent_str = progress_data.get('_percent_str', '0%')
            # Convert to float
            try:
                value = float(percent_str.strip('%')) / 100
                self.progress_bar.set(value)
            except:
                self.progress_bar.start()  # fallback to indeterminate
        elif status in ['finished', 'error']:
            self.progress_bar.stop()

    def animate_progress(self):
        value = self.progress_bar.get()
        self.progress_bar.set(min(value + 0.002, 1))
        if self.downloading:
            self.root.after(50, self.animate_progress)

            self.animate_progress()

    def finish_download_ui(self, success=True):
            """Restore UI after download completes or is canceled"""
            self.url_entry.configure(state="normal")
            self.folder_entry.configure(state="normal")
            self.folder_browse_btn.configure(state="normal")
            self.paste_btn.configure(state="normal")
            self.audio_switch.configure(state="normal")

            self.download_btn.configure(
                text="Download",
                fg_color=self.theme["BTN_ACTION"]
            )

            self.downloading = False
            self.progress_bar.set(0)    

        # --- DOWNLOAD BUTTON ---
    def start_download(self):
        url = self.url_entry.get().strip()
        folder = self.folder_entry.get().strip()
        is_audio = self.audio_switch.get()

        if not url or not folder:
            return  # Maybe show a ThemedDialog warning

        # Disable fields & change button to Cancel
        self.url_entry.configure(state="disabled")
        self.folder_entry.configure(state="disabled")
        self.download_btn.configure(text="Cancel", command=self.cancel_download)

        # Start download in background
        self.worker.start_download_threaded(url, folder, is_audio)

    def lock_inputs(self):
        """Disable entries and switches while downloading"""
        self.url_entry.configure(state="disabled")
        self.folder_entry.configure(state="disabled")
        self.folder_browse_btn.configure(state="disabled")
        self.paste_btn.configure(state="disabled")
        self.audio_switch.configure(state="disabled")

    def unlock_inputs(self):
        """Re-enable entries and switches after download"""
        self.url_entry.configure(state="normal")
        self.folder_entry.configure(state="normal")
        self.folder_browse_btn.configure(state="normal")
        self.paste_btn.configure(state="normal")
        self.audio_switch.configure(state="normal")

    def cancel_download(self):
        self.worker.cancel()
        self.download_btn.configure(text="Download", command=self.start_download)
        self.url_entry.configure(state="normal")
        self.folder_entry.configure(state="normal")

    def create_progress_title(self):
        """Create and configure the progress title widget."""
        self.progress_title = ctk.CTkLabel(
            self.root, 
            text="Progress:", 
            font=("Helvetica", 12), 
            bg=self.root.THEME["APP_BG"],
            fg="#333"
        )
        self.progress_title.pack(side=ctk.TOP, fill=ctk.X, padx=10, pady=5)

    def on_worker_progress(self, progress):
        """Update the progress title based on worker progress."""
        if self.progress_title:
            self.progress_title.config(text=f"Progress: {progress}%")
        else:
            self.logger.error("UIController.progress_title is not initialized.")