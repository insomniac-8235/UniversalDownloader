import threading
import time
import platform
import os
import subprocess
from urllib.parse import urlparse
from queue import Empty
from download_queue.download_queue import DownloadQueue
from utils.logger import UDLogger, DEBUG
print(f"--- LOADING MODULE: {__name__} ---")

class ThreadPoolManager:
    def __init__(self, worker, max_workers=4, controller=None): 
        self.queue = DownloadQueue(worker=worker, max_size=0)
        self.max_workers = max_workers
        self.logger = UDLogger(level=DEBUG)
        self._thread_pool = []
        self._shutdown_event = threading.Event()
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
                        self.notify_completion(task)
                    except Exception as e:
                        self.logger.error(f"Worker {worker_id} error: {e}")
                        self.notify_error(task, str(e))
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Critical worker failure: {e}", exc_info=True)
                self.stop()  # Stop the thread pool if a critical error occurs

    def run_with_ffmpeg(self, task):
        """Run the task using FFmpeg"""
        filename = os.path.basename(urlparse(task['url']).path)
        output_file = os.path.join(task['folder'], f"{filename}.mp4")

        command = [
            'ffmpeg',
            '-i', task['url'],
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-y',  # overwrite output if exists
            output_file
        ]
        
        try:
            result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.logger.info(result.stdout)
            self.logger.warning(result.stderr)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg failed: {e.stderr}")
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
        """Ensures the UI knows the task is dead, even if the worker failed to report it."""
        self.logger.error(f"Queue Error: {error_msg}")
        
        if self.controller:
            # 1. Update the UI Log/Toast
            self.controller.on_download_error(task.get('url'), task.get('folder'), error_msg)
            
            # 2. IMPORTANT: Reset the button so the user can try again!
            self.controller.root.after(0, lambda: self.controller.set_downloading_state(False))

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
    
    def _task_complete_callback(self, future):
        """Internal callback for the ThreadPoolExecutor."""
        try:
            result = future.result() 
        except Exception as e:
            # This is where notify_error saves the day
            self.notify_error(self.current_task, str(e))

    def stop(self):
        """Initiating universal shutdown..."""
        self._shutdown_event.set()
        self.logger.info("Stopping all workers...")

        # 1. Tell the worker to stop its specific active process
        if hasattr(self.queue, 'worker'):
            self.queue.worker.cancel()

        # 2. Wait for threads to finish gracefully
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
                if current_os == "nt":
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