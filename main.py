import sys
import ctk
import utils

# ... existing code ...

class UniversalDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()
        # ... existing code ...

    def download_media(self):
        ffmpeg_path = utils.get_ffmpeg_path()
        if not ffmpeg_path:
            self.show_popup("FFmpeg not found", success=False)
            return

        utils.download_media(ffmpeg_path)

# ... existing code ...
