import threading
import time
import platform
import os
import subprocess
from queue import Empty
from download_queue.download_queue import DownloadQueue
import utils.logger

class ThreadPoolManager:
    def __init__(self, worker, max_workers=4, controller=None): 
        self.queue = DownloadQueue(worker=worker, max_size=0)
        self.max_workers = max_workers
        self.logger = utils.logger.MyLogger(level=utils.logger.DEBUG) 
        self._thread_pool = []
        self._shutdown_event = threading.Event()
        self._metrics = {
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
                target=self._worker_loop, 
                args=(i,), 
                daemon=True # Ensures threads exit when the main app closes
            )
            t.start()
            self._thread_pool.append(t)
    def enqueue(self, url, folder, is_audio):
            """Packages UI data into a task dict and sends it to the queue."""
            task = {
                'url': url,
                'folder': folder,
                'is_audio': is_audio
            }
            self.logger.info(f"Task prepared for {url}")
            # This calls the enqueue method on your DownloadQueue instance
            self.queue.enqueue(task)

    def _notify_completion(self, task):
        """Handles post-download logic and UI notification."""
        self.logger.info(f"✅ Task Completed: {task}")
        if self.controller:
            # We pass the filename or URL to the controller for the popup
            filename = os.path.basename(task.get('url', 'Download'))
            self.controller.show_completion_popup(filename)

    def _notify_error(self, task, error_msg):
        """Handles failure logic and UI notification."""
        self.logger.error(f"Task Failed: {task} | Error: {error_msg}")
        if self.controller:
            # Add logic here to show error in UI via the controller
            pass


    def stop(self):
        """Graceful shutdown with Cross-Platform Cleanup"""
        self._shutdown_event.set()
        self.logger.info("Initiating universal shutdown...")

        # 1. Kill subprocesses based on OS (The Enforcer Layer)
        self._kill_binaries()

        # 2. Wait for threads to finish
        timeout = 10 # Reduced for better UX
        start_time = time.time()
        while len([t for t in self._thread_pool if t.is_alive()]) > 0:
            if time.time() - start_time > timeout:
                break
            time.sleep(0.1)
        
        self.logger.info("🏁 Thread pool stopped.")

    def _kill_binaries(self):
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

    def _worker_loop(self, worker_id):
        """Worker loop with robust error handling"""
        while not self._shutdown_event.is_set():
            try:
                task = self.queue.dequeue(timeout=1.0)
                if task:
                    try:
                        success = self.queue.execute_task(task)
                        if success:
                            self._metrics['downloads_completed'] += 1
                            self._notify_completion(task)
                        else:
                            self._metrics['downloads_failed'] += 1
                    except Exception as e:
                        self.logger.error(f"Worker {worker_id} error: {e}")
                        self._metrics['downloads_failed'] += 1
                        self._notify_error(task, str(e))
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Critical worker failure: {e}")