import threading
import time
import platform
import os
import subprocess
from queue import Empty, Queue
from download_queue.download_queue import DownloadQueue
from utils.logger import MyLogger, DEBUG

class ThreadPoolManager:
    def __init__(self, worker, max_workers=4, controller=None): 
        self.queue = DownloadQueue(worker=worker, max_size=0)
        self.max_workers = max_workers
        self.logger = MyLogger(level=DEBUG)
        self._thread_pool = []
        self._shutdown_event = threading.Event()
        self.metrics = {
            'downloads_completed': 0,
            'downloads_failed': 0,
            'total_time': 0,
            'avg_download_speed': 0
        }
        self.controller = controller
        if self.controller:
            self.queue.worker.set_progress_hook(self.controller.on_progress_update)
    def start(self):
        """Initializes and starts the worker thread pool."""
        if self._thread_pool:
            self.logger.warning("⚠️ Thread pool is already running.")
            return
        self.logger.info(f"🚀 Starting thread pool with {self.max_workers} workers...")
        self._shutdown_event.clear()
        
        # Create and start worker threads
        for i in range(self.max_workers):
            t = threading.Thread(
                target=self.worker_loop, 
                args=(i,), 
                daemon=True  # Ensures threads exit when the main app closes
            )
            t.start()
            self._thread_pool.append(t)
    def worker_loop(self, worker_id):
        """Worker loop with robust error handling"""
        while not self._shutdown_event.is_set():
            try:
                if task := self.queue.dequeue(timeout=1.0):
                    start_time = time.time()
                    try:
                        if task['use_ffmpeg']:
                            # Run the task using FFmpeg
                            success = self.run_with_ffmpeg(task)
                        else:
                            success = self.queue.execute_task(task)
                        end_time = time.time()
                        download_time = end_time - start_time
                        download_speed = (len(task['url']) / 1024) / download_time if download_time > 0 else 0
                        self.metrics['total_time'] += download_time
                        self.metrics['avg_download_speed'] += download_speed
                        self.notify_completion(task)
                    except Exception as e:
                        self.logger.error(f"Worker {worker_id} error: {e}")
                        self.metrics['downloads_failed'] += 1
                        self.notify_error(task, str(e))
            except Empty:
                continue
            except Exception as e:
                self.logger.critical(f"Critical worker failure: {e}", exc_info=True)
                self.stop()  # Stop the thread pool if a critical error occurs
    def run_with_ffmpeg(self, task):
        """Run the task using FFmpeg"""
        command = [
            'ffmpeg',
            '-i', task['url'],
            os.path.join(task['folder'], f"{os.path.basename(task['url'])}.mp4")  # Example output file
        ]
        
        try:
            result = subprocess.run(command, check=True)
            return True
        except Exception as e:
            self.logger.error(f"Error running FFmpeg: {e}")
            return False
    def notify_completion(self, task):
        """Handles post-download logic and UI notification."""
        self.logger.info(f"✅ Task Completed: {task}")
        if self.controller:
            # We must pass the exact 3 arguments your UI function expects
            self.controller.on_download_complete(
                task['url'], 
                task['folder'], 
                task['is_audio']
            )
    def notify_error(self, task, error_msg):
        """Handles failure logic and UI notification."""
        self.logger.error(f"Task Failed: {task} | Error: {error_msg}")
        if self.controller:
            self.controller.on_download_error(task['url'], task['folder'], error_msg)

    def stop(self):
        """Graceful shutdown with Cross-Platform Cleanup"""
        self._shutdown_event.set()
        self.logger.info("Initiating universal shutdown...")
        # 1. Kill subprocesses based on OS (The Enforcer Layer)
        self.kill_binaries()
        # 2. Wait for threads to finish
        timeout = 10  # Reduced for better UX
        start_time = time.time()
        while [
            t for t in self._thread_pool if t.is_alive()
        ] and time.time() - start_time <= timeout:
            time.sleep(0.1)
        self.logger.info("🏁 Thread pool stopped.")

    def kill_binaries(self):
        """Cross-platform binary termination for aria2c, ffmpeg, and deno."""
        current_os = platform.system()
        # List of binary names to target
        binaries = ["ffmpeg", "aria2c", "deno", "yt-dlp"]
        for bin_name in binaries:
            try:
                if current_os == "Windows":
                    # Windows: use taskkill with /T (tree) to catch child processes
                    subprocess.run(
                        ['taskkill', '/F', '/IM', f"{bin_name}.exe", '/T'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                else:
                    # Mac/Linux: use pkill
                    subprocess.run(
                        ['pkill', '-9', bin_name],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
            except Exception as e:
                self.logger.debug(f"Could not kill {bin_name}: {e}")

    def enqueue(self, url, folder, is_audio, use_ffmpeg=False):
        """Packages UI data into a task dict and sends it to the queue."""
        task = {
            'url': url,
            'folder': folder,
            'is_audio': is_audio,
            'use_ffmpeg': use_ffmpeg
        }
        self.logger.info(f"Task prepared for {url}")
        # This calls the enqueue method on your DownloadQueue instance
        self.queue.enqueue(task)

    def get_metrics(self):
        """Returns the current metrics."""
        return {
            'downloads_completed': self.metrics['downloads_completed'],
            'downloads_failed': self.metrics['downloads_failed'],
            'total_time': self.metrics['total_time'],
            'avg_download_speed': self.metrics['avg_download_speed']
        }