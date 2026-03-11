import os
import shutil
import sys

def is_frozen():
    return getattr(sys, 'frozen', False)

def get_ffmpeg_path():
    if is_frozen():
        # Running as a bundled app
        app_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        ffmpeg_path = os.path.join(app_path, 'ffmpeg')
        if not os.path.exists(ffmpeg_path):
            # Copy FFmpeg from system to the app directory
            system_ffmpeg_path = shutil.which('ffmpeg')
            if system_ffmpeg_path:
                shutil.copy(system_ffmpeg_path, ffmpeg_path)
                os.chmod(ffmpeg_path, 0o755)
        return ffmpeg_path
    else:
        # Running as a script
        return shutil.which('ffmpeg')
