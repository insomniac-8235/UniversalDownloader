import os
import sys
import shutil

class Utilities:
    @staticmethod
    def get_ffmpeg_path():
        if getattr(sys, 'frozen', False):
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            ffmpeg_path = os.path.join(base_path, 'ffmpeg')
            if not os.path.exists(ffmpeg_path):
                ffmpeg_path = os.path.join(base_path, 'ffmpeg.exe')  # For Windows
            return ffmpeg_path
        else:
            ffmpeg_path = shutil.which('ffmpeg')
            if ffmpeg_path is None:
                raise FileNotFoundError("ffmpeg not found in PATH")
            return ffmpeg_path
            
    @staticmethod
    def get_resource_path(relative_path: str):
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)


main.py
