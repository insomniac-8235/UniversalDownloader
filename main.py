import sys
import ctk
import ffmpeg_handler

# ... existing code ...

class UniversalDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()
        # ... existing code ...

    def download_media(self):
        ffmpeg_path = ffmpeg_handler.get_ffmpeg_path()
        if not ffmpeg_path:
            self.show_popup("FFmpeg not found", success=False)
            return

        # ... existing code using ffmpeg_path ...

# ... existing code ...
