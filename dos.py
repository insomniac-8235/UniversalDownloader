import sys
import os
import threading
from yt_dlp import YoutubeDL
from .main import UniversalDownloader, MyLogger

def download_media(url, folder, is_audio):
    try:
        ffmpeg_path = get_ffmpeg_path()
        ydl_opts = {
            'format': 'bestaudio/best' if is_audio else 'bestvideo+bestaudio/best',
            'restrictfilenames': True,
            'noplaylist': True,
            'ffmpeg_location': ffmpeg_path,
            'outtmpl': os.path.join(folder, '%(title)s [%(id)s].%(ext)s'),
            'logger': MyLogger(),
            'progress_hooks': [download_progress_hook],
        }

        if is_audio:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }]
        else:
            ydl_opts['merge_output_format'] = 'mp4'

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return True, None
    except Exception as e:
        return False, str(e)

def download_thread(url, folder, is_audio):
    if not os.path.isdir(folder):
        return False, "Invalid folder path"

    threading.Thread(target=lambda: download_media(url, folder, is_audio)).start()
    return True, None

def download_progress_hook(d):
    try:
        total_bytes = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
        downloaded = d.get('downloaded_bytes', 0)
        progress_percent = (downloaded / total_bytes) * 100 if total_bytes > 0 else 0
        print(f"Download progress: {progress_percent:.2f}%")
    except Exception as e:
        print(f"Progress hook error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python dos.py <url> <folder> <is_audio>")
        sys.exit(1)

    url = sys.argv[1]
    folder = sys.argv[2]
    is_audio = sys.argv[3].lower() == 'true'

    success, error_detail = download_thread(url, folder, is_audio)
    if not success:
        print(f"Download failed: {error_detail}")
        sys.exit(1)
