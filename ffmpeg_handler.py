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
