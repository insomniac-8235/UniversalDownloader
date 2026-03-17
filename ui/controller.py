import customtkinter as ctk
from tkinter import Tk, filedialog, messagebox
import os
import sys
from utils.theme import THEME, FONTS
print(f"--- LOADING MODULE: {__name__} ---")

class UIController:
    def __init__(self, app, queue_manager=None):
        # The Guard: If this instance already has a root, it's already setup!
        if hasattr(self, "_already_setup"):
            return
        self._already_setup = True
        self.app = app
        self.queue_manager = queue_manager
        self.progress_title = None  # Initialize progress_title attribute

        # Copy module-level THEME to instance (avoid mutation issues)
        self.theme = THEME.copy()
        
        ctk.set_appearance_mode("system")  # Use system theme (light/dark)
        # Initialize fonts using the centralized theme
        self.main_font = ctk.CTkFont(family=FONTS["MAIN"][0], size=FONTS["MAIN"][1], weight=FONTS["MAIN"][2] if len(FONTS["MAIN"]) > 2 else "normal")
        self.input_font = ctk.CTkFont(family=FONTS["INPUT"][0], size=FONTS["INPUT"][1])
        self.version_font = ctk.CTkFont(family=FONTS["VERSION"][0], size=FONTS["VERSION"][1])
        self.button_font = ctk.CTkFont(family=FONTS["BUTTON"][0], size=FONTS["BUTTON"][1], weight=FONTS["BUTTON"][2])

        self.setup_ui()
        self.bind_events()
        self._debounce_timer = None

        self.downloading = False
        self.current_task = None

    def setup_ui(self):
        print("\n🚨 SETUP UI IS RUNNING! 🚨")

        # Create outer frame FIRST...
        self.outer_frame = ctk.CTkFrame(
            self.app, 
            corner_radius=0,
            fg_color=self.theme["APP_BG"],
        )
        self.outer_frame.pack(fill="both", expand=True)
        
        # Create content frame inside outer frame
        self.content_frame = ctk.CTkFrame(
            self.outer_frame, 
            fg_color=self.theme["APP_BG"],
        )
        self.content_frame.pack(pady=(20), padx=20, fill="both", expand=False)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # URL Section
        self.url_label = ctk.CTkLabel(
            self.content_frame,
            text="Media URL",
            font=self.main_font,
            text_color=self.theme["TEXT_MAIN"]
        )
        self.url_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.url_container = ctk.CTkFrame(
            self.content_frame,
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
            text_color=self.theme["TEXT_MAIN"],
            placeholder_text_color=self.theme["TEXT_GHOST"],
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
            text_color=self.theme["TEXT_MAIN"],
            placeholder_text_color=self.theme["TEXT_GHOST"],
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
        
        # Audio Switch Label
        self.audio_label = ctk.CTkLabel(
            self.content_frame,
            text="Audio Only",
            font=self.main_font,
            text_color=self.theme["TEXT_MAIN"]
        )
        self.audio_label.grid(row=4, column=0, sticky="w", pady=(0, 20))
        
        # Audio Switch
        self.audio_switch = ctk.CTkSwitch(
            self.content_frame,
            text="",
            switch_width=50,
            switch_height=20,
            fg_color=self.theme["ENTRY_BG"],
            progress_color=self.theme["PROG_FILL"],
            button_color=self.theme["SWITCH_BTN"],
            button_hover_color=self.theme["BTN_HOVER"],
            border_width=1,
            button_length=8
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
        
        # self.download_card = ctk.CTkFrame(
        #     self.content_frame,
        #     corner_radius=16,
        #     fg_color=self.theme["ENTRY_BG"]
        # )

        # self.download_card.grid(row=6, column=0, columnspan=2, sticky="we", pady=(10,20))
        # self.download_card.grid_columnconfigure(0, weight=1)

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
            text_color_disabled=self.theme["TEXT_DISABLED"],
            command=self.initiate_download
        )
        self.download_btn.grid(row=6, column=0, sticky="s")
        

        # Version Labels
        self.version_label = ctk.CTkLabel(
            self.outer_frame,
            text=self.get_build_info(),
            font=self.version_font,
            text_color=self.theme["TEXT_VERSION"],
            bg_color="transparent"
        )
        self.version_label.place(relx=1.0, rely=1.0, x=-20, y=-5, anchor="se")
        
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

    def set_downloading_state(self, is_downloading):
        if is_downloading:
            # We only update the button because status_label doesn't exist
            self.download_btn.configure(text="Cancel", fg_color="#c0392b")
        else:
            self.download_btn.configure(text="Download", fg_color=["#1976d2", "#1976d2"])

    def set_processing_state(self):
        """Transition UI from 'Downloading' to 'Merging/Finalizing'."""
        # 1. Update Progress Bar to 100% (Indeterminate can also work here)
        self.progress_bar.set(1.0)
        self.progress_bar.configure(mode="indeterminate")
        self.download_btn.configure(text="Finalising...")
        
        # 2. Lock the button so they can't interrupt the FFmpeg merge
        self.download_btn.configure(
            text="Merging...",
            state="disabled",
            fg_color="#e67e22"  # A distinct 'processing' orange
        )

    def initiate_download(self):
        # 1. Grab values from your UI entry fields
        url = self.url_entry.get()
        folder = self.folder_entry.get()
        is_audio = self.audio_switch.get()

        # 2. Reset the progress bar for a clean start
        self.progress_bar.set(0)

        self.app.worker.start_download_threaded(
            url, 
            folder, 
            is_audio, 
            self.progress_bar.set  # This is the 'progress_hook'
)

    def download_success(self, task_info):
            """Handle successful download"""
            message = f"Download Completed: {task_info}"
            messagebox.showinfo(message)

    def download_error(self, task_info):
        """Handle failed download"""
        message = f"ERROR: Worker {task_info['worker_id']} error: {task_info.get('error', 'Unknown error')}"
        messagebox.showerror("Download Error", message)      

    def toggle_download(self):
        print("UI DEBUG: Download button clicked!")
        if self.downloading:
            self.app.worker.cancel()
            return

        url = self.url_entry.get().strip()
        folder = self.folder_entry.get().strip()
        is_audio = self.audio_switch.get()

        if not url or not folder:
            self.on_invalid_url("Please provide both a URL and a download location.")
            return

    # def set_downloading_state(self, is_downloading):
    #     if is_downloading:
    #         self.download_btn.configure(text="Cancel", fg_color="#c0392b")
    #         # Start the bouncing animation
    #         self.progress_bar.configure(mode="indeterminate")
    #         self.progress_bar.start()
    #     else:
    #         # Stop animation and reset
    #         self.progress_bar.stop()
    #         self.progress_bar.configure(mode="determinate")
    #         self.progress_bar.set(0)
    #         self.download_btn.configure(text="Download", fg_color=["#197cd2", "#197cd2"])

    def on_invalid_url(self, error_msg: str):
        """Handle invalid URL errors"""
        messagebox.showwarning("Invalid URL", f"Invalid URL provided:\n{error_msg}")

    def on_focus_in(self, widget):
        if self.downloading:
            return  # ignore focus changes while downloading
        if widget in [self.url_entry, self.folder_entry]:
            widget.configure(border_color=self.theme["BORDER_FOCUS"])
            widget.configure(text_color=self.theme["TEXT_MAIN"])

    def on_focus_out(self, widget):
        if self.downloading:
            return  # ignore focus changes while downloading
        if not widget.get().strip():
            widget.configure(border_color=self.theme["BORDER_DEFAULT"])
        else:
            widget.configure(border_color=self.theme["BORDER_FOCUS"])
        widget.configure(text_color=self.theme["TEXT_MAIN"])
    
    def select_folder(self):
        if folder := filedialog.askdirectory():
            self.folder_entry.delete(0, "end")  
            self.folder_entry.insert(0, folder)
            self.folder_entry.configure(text_color=self.theme["TEXT_MAIN"])
            self.validate_inputs()
        
    def paste_url_from_clipboard(self):
        try:
            text = self.app.clipboard_get().strip()
        except Exception:
            return
        if text:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, text)
            self.validate_inputs()

    def on_download_complete(self, url, folder, is_audio):
        # Ensure we reset the UI state first
        self.app.after(0, lambda: self.set_downloading_state(False))
        
        # Then show the success dialog
        messagebox.showinfo("Download Complete", 
            f"Successfully saved to:\n{folder}"
        )

    def on_download_error(self, url, folder, error):
        # This keeps the UI thread safe!
        self.app.after(0, lambda: messagebox.showerror("Error", error))

        # 2. Pop the custom error message
        messagebox.showerror(
            title="Download Failed", message="Could not download the file"
        )

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
            self.app.after_cancel(self._debounce_timer)
        
        self._debounce_timer = self.app.after(100, self.validate_inputs)

    def update_status_hook(self, text):
        """Updates the UI with the current step of the process."""
        # Option A: If you have a status label
        if hasattr(self, 'status_label'):
            self.download_btn.configure(text=text)
        
        # Option B: Always update the button text so the user sees it
        self.download_btn.configure(text=text)
        
        # Optional: Print to console for verification
        print(f"UI STATUS UPDATE: {text}")

    def _update_ui_elements(self, progress_data):
        status = progress_data.get('status')
        
        if status == 'downloading':
            value = None  # Start with no value
            
            # --- NET 1: Try Raw Bytes Math ---
            downloaded = progress_data.get('downloaded_bytes')
            total = progress_data.get('total_bytes') or progress_data.get('total_bytes_estimate')
            
            if total and downloaded is not None and total > 0:
                value = downloaded / total
                
            # --- NET 2: Try String Parsing (If math failed) ---
            elif '_percent_str' in progress_data:
                percent_str = progress_data.get('_percent_str', '')
                if '%' in percent_str:
                    try:
                        # Clean hidden ANSI color codes and the % sign
                        clean_percent = percent_str.replace('%', '').replace('\x1b[0;94m', '').replace('\x1b[0m', '').strip()
                        value = float(clean_percent) / 100
                    except (ValueError, TypeError):
                        pass # String was too messy, leave value as None

            # --- APPLY THE RESULT ---
            if value is not None:
                # We got a valid number! Fill the bar.
                if self.progress_bar.cget("mode") == "indeterminate":
                    self.progress_bar.stop()
                    self.progress_bar.configure(mode="determinate")
                self.progress_bar.set(value)
            else:
                # Both nets failed (size truly unknown). Pulse the bar.
                self._switch_to_indeterminate()

            # --- Update Button Text ---
            speed = progress_data.get('_speed_str', '~')
            if isinstance(speed, str):
                speed = speed.replace('\x1b[0;94m', '').replace('\x1b[0m', '').strip()
            self.download_btn.configure(text=f"Downloading... {speed}")

        elif status == 'finished':
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(1.0)
            self.download_btn.configure(text="Finalising...")

        elif status == 'error':
            self.progress_bar.stop()
            self.progress_bar.set(0)
            self.download_btn.configure(text="Error!")

    def _switch_to_indeterminate(self):
        """Safely toggles the bar to pulse mode."""
        if self.progress_bar.cget("mode") == "determinate":
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()

    def on_progress_update(self, float_val):
        """Receives 0.0-1.0 and updates the UI thread."""
        # float_val is already between 0 and 1 from the worker
        self.app.after(0, lambda: self.progress_bar.set(float_val))

        current_val = self.progress_bar.get()
        new_val = min(current_val + 0.01, 1.0)
        self.progress_bar.set(new_val)

        # Schedule the NEXT frame (50ms = 20fps)
        if new_val < 1.0:
            self.app.after(50, self.root.animate_progress) 

    def cancel_download(self):
        self.app.worker.cancel()
        self.download_btn.configure(text="Download")
        self.url_entry.configure(state="normal")
        self.folder_entry.configure(state="normal")
        self.validate_inputs()

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