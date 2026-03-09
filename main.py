import customtkinter as ctk
from tkinter import filedialog
from yt_dlp import YoutubeDL
import threading
import os
import sys

# Set Appearance
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class UniversalDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- WINDOW CONFIG ---
        self.title("Universal Media Downloader")
        self.geometry("500x400")
        self.resizable(False, False)
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, "assets/icon.ico")
        else:
            icon_path = "assets/icon.ico"

        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        # --- THEME CONSTANTS ---
        # Backgrounds & Tracks
        self.APP_BG = ("#ebebeb", "#242424")  # Matches System background
        self.ENTRY_BG = ("#F0F8FF", "#343638")  # Subtle fill for inputs

        # Borders & States
        self.BORDER_HIDDEN = self.APP_BG  # Disappears into background
        self.BORDER_DEFAULT = ("#90CAF9", "#5a5a5a")  # Soft blue/grey (idle)
        self.ENTRY_FOCUS = ("#1565C0", "#1976D2")  # Active glow (typing)

        # Buttons
        self.ACTION_BTN = ("#1976D2", "#1E88E5")  # Main Blue
        self.ACTION_HOVER = ("#1565C0", "#1976D2")
        self.BTN_HOVER = ("#BBDEFB", "#2c2c2c")  # Soft hover for ghost buttons
        self.ACTION_TEXT = "white"

        # Progress & Text
        self.PROG_FILL = ("#90CAF9", "#1976D2")  # Bouncing bar color
        self.TEXT_MAIN = ("black", "white")
        self.TEXT_GHOST = ("#666666", "#A0A0A0")  # Placeholder text color
        self.TEXT_DISABLED = ("#90CAF9", "gray")
        self.TEXT_VERSION = ("#555555", "#888888")

        # Fonts (System Native)
        self.FONT_MAIN = (None, 13)
        self.FONT_BOLD = (None, 13, "bold")
        self.FONT_SMALL = (None, 11)

        # Build UI
        self.setup_ui()

    def setup_ui(self):
        # Main Container
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(pady=30, padx=40, fill="both", expand=True)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # 1. URL ENTRY (The Ghost Field)
        self.url_label = ctk.CTkLabel(self.content_frame, text="Media URL", font=self.FONT_BOLD)
        self.url_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.url_entry = ctk.CTkEntry(
            self.content_frame,
            placeholder_text="Paste link here...",
            height=40,
            font=self.FONT_MAIN,
            fg_color=self.ENTRY_BG,
            border_width=1,
            border_color=self.BORDER_HIDDEN
        )
        self.url_entry.grid(row=1, column=0, columnspan=2, sticky="we", pady=(0, 20))
        self.url_entry.bind("<KeyRelease>", self.validate_inputs)
        self.url_entry.bind("<FocusIn>", lambda e: self.on_focus_in(self.url_entry))
        self.url_entry.bind("<FocusOut>", lambda e: self.on_focus_out(self.url_entry))

        # 2. FOLDER SELECTION BUTTON (The Ghost Selection Bar)
        self.folder_label = ctk.CTkLabel(self.content_frame, text="Download Location", font=self.FONT_BOLD)
        self.folder_label.grid(row=2, column=0, sticky="w", pady=(0, 5))

        self.folder_selection_btn = ctk.CTkButton(
            self.content_frame,
            text="Select Download Folder...",
            anchor="w",
            height=40,
            fg_color=self.ENTRY_BG,
            text_color=self.TEXT_GHOST,
            border_width=1,
            border_color=self.BORDER_HIDDEN,
            font=self.FONT_MAIN,
            hover_color=self.BTN_HOVER,
            command=self.select_folder
        )
        self.folder_selection_btn.grid(row=3, column=0, columnspan=2, sticky="we", pady=(0, 20))
        self.folder_selection_btn.bind("<Enter>",
                                       lambda e: self.folder_selection_btn.configure(border_color=self.BORDER_DEFAULT))
        self.folder_selection_btn.bind("<Leave>", lambda e: self.on_folder_btn_leave())

        # 3. OPTIONS (Audio Toggle)
        self.audio_switch = ctk.CTkSwitch(self.content_frame, text="Audio Only", font=self.FONT_BOLD)
        self.audio_switch.grid(row=4, column=0, sticky="w", pady=(0, 20))

        # 4. PROGRESS BAR (Hidden by default)
        self.progress_bar = ctk.CTkProgressBar(
            self.content_frame,
            height=12,
            fg_color=self.APP_BG,
            progress_color=self.APP_BG,
            corner_radius=6
        )
        self.progress_bar.set(0)
        self.progress_bar.grid(row=5, column=0, columnspan=2, sticky="we", pady=(0, 20))

        # 5. MAIN ACTION BUTTON
        self.download_btn = ctk.CTkButton(
            self.content_frame,
            text="Enter a URL & Location",
            height=50,
            font=self.FONT_BOLD,
            state="disabled",
            fg_color=self.ACTION_BTN,
            hover_color=self.ACTION_HOVER,
            text_color_disabled=self.TEXT_DISABLED
        )
        self.download_btn.configure(command=self.start_download_thread)
        self.download_btn.grid(row=6, column=0, columnspan=2, sticky="we")

        # 6. VERSION LABEL
        self.version_label = ctk.CTkLabel(self, text="v0.1-beta", font=self.FONT_SMALL, text_color=self.TEXT_VERSION)
        self.version_label.place(relx=0.98, rely=0.98, anchor="se")

        # Powered By Label (Bottom Left Corner)
        self.credit_label = ctk.CTkLabel(
            self,
            text="Powered by yt-dlp",
            font=self.FONT_SMALL,
            text_color=self.TEXT_VERSION
        )
        # Position it 2% from the left and 2% from the bottom
        self.credit_label.place(relx=0.02, rely=0.98, anchor="sw")

    # --- LOGIC METHODS ---

    def on_focus_in(self, widget):
        widget.configure(border_color=self.ENTRY_FOCUS)

    def on_focus_out(self, widget):
        if not widget.get().strip():
            widget.configure(border_color=self.BORDER_HIDDEN)
        else:
            widget.configure(border_color=self.BORDER_DEFAULT)

    def on_folder_btn_leave(self):
        if self.folder_selection_btn.cget("text") == "Select Download Folder...":
            self.folder_selection_btn.configure(border_color=self.BORDER_HIDDEN)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_selection_btn.configure(text=folder, text_color=self.TEXT_MAIN,
                                                border_color=self.BORDER_DEFAULT)
            self.validate_inputs()

    def validate_inputs(self, event=None):
        url = self.url_entry.get().strip()
        folder = self.folder_selection_btn.cget("text")

        if url and folder != "Select Download Folder...":
            self.download_btn.configure(state="normal", text="Download Now", text_color=self.ACTION_TEXT)
        else:
            self.download_btn.configure(state="disabled", text="Enter URL & Folder")

    def show_popup(self, title, message):
        self.update_idletasks()
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        p_width, p_height = 400, 200

        # Center Calculation
        center_x = self.winfo_x() + (self.winfo_width() // 2) - (p_width // 2)
        center_y = self.winfo_y() + (self.winfo_height() // 2) - (p_height // 2)

        popup.geometry(f"{p_width}x{p_height}+{center_x}+{center_y}")
        popup.attributes("-topmost", True)

        label = ctk.CTkLabel(popup, text=message, wraplength=350, font=self.FONT_MAIN)
        label.pack(pady=40)

        btn = ctk.CTkButton(popup, text="OK", font=self.FONT_BOLD, width=100, command=popup.destroy)
        btn.pack(side="bottom", pady=20)
        popup.grab_set()

    def start_download_thread(self):
        self.download_btn.configure(state="disabled", text="Connecting...")
        self.progress_bar.configure(progress_color=self.PROG_FILL, mode="indeterminate")
        self.progress_bar.start()
        threading.Thread(target=self.download_media, daemon=True).start()

    def download_media(self):
        url = self.url_entry.get()
        folder = self.folder_selection_btn.cget("text")
        is_audio = self.audio_switch.get()

        ydl_opts = {
            'format': 'bestaudio/best' if is_audio else 'best',
            'outtmpl': f'{folder}/%(title)s.%(ext)s',
            'quiet': True
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.after(0, lambda: self.show_popup("Success", "Download Complete!"))
        except Exception as e:
            self.after(0, lambda: self.show_popup("Error", "Download Failed. Check the URL."))
        finally:
            self.after(0, self.progress_bar.stop)
            self.after(0, lambda: self.progress_bar.configure(progress_color=self.APP_BG))
            self.after(0, self.validate_inputs)


if __name__ == "__main__":
    app = UniversalDownloader()
    app.mainloop()