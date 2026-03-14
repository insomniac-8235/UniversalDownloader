import threading
from queue import Queue, Empty
import time
import subprocess
from typing import Callable, Dict, Any, Optional 

from .download_queue import DownloadQueue
from utilities.logger import MyLogger, DEBUG

class ThreadPoolManager:
    # ADDED: controller parameter
    def __init__(self, worker, max_workers=4, controller=None): 
        self.queue = DownloadQueue(worker=worker, max_size=0)
        self.max_workers = max_workers
        self.logger = MyLogger(level=DEBUG) 
        self._thread_pool = []
        self._shutdown_event = threading.Event()
        self._metrics = {
            'downloads_completed': 0,
            'downloads_failed': 0,
            'total_time': 0,
            'avg_download_speed': 0
        }
        # ADDED: Store controller and connect progress hook
        self.controller = controller 
        if self.controller:
            # CORRECTED LINE: Set the progress hook on the worker itself
            self.queue.worker.set_progress_hook(self.controller.on_progress_update)
        
    # REMOVED: set_progress_callback method, as it's no longer used
    # def set_progress_callback(self, callback: Callable[[Dict[str, Any]], None]):
    #     """Set the UI progress callback for the thread pool manager.
    #        This callback will be passed to the worker's progress hook."""
    #     self._ui_progress_callback = callback
    #     if self.queue.worker:
    #         self.queue.worker.set_progress_hook(callback)

    def start(self):
        """Start the thread pool with proper lifecycle management"""
        self._shutdown_event.clear()
        for i in range(self.max_workers):
            thread = threading.Thread(
                target=self._worker_loop,
                args=(i,),
                daemon=True
            )
            thread.start()
            self._thread_pool.append(thread)
            
    def stop(self):
        """Graceful shutdown with proper cleanup"""
        self._shutdown_event.set()
        
        # Wait for threads to finish (max 30 seconds)
        timeout = 30
        start_time = time.time()
        
        while len([t for t in self._thread_pool if t.is_alive()]) > 0:
            if time.time() - start_time > timeout:
                # Force kill remaining threads
                for thread in self._thread_pool:
                    thread.join(timeout=1)
                break
            time.sleep(0.1)
            
        # Ensure ffmpeg processes are killed immediately (per CONVENTIONS.md)
        try:
            subprocess.Popen(['taskkill', '/F', '/IM', 'ffmpeg.exe'], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
            
    def _worker_loop(self, worker_id):
        """Worker loop with connection pooling and error handling"""
        while not self._shutdown_event.is_set():
            try:
                # Non-blocking queue get with timeout
                task = self.queue.dequeue(timeout=1.0)
                
                if task:
                    start_time = time.time()
                    
                    try:
                        success = self.queue.execute_task(task)
                        
                        if success:
                            self._metrics['downloads_completed'] += 1
                            # Notify UI of completion
                            self._notify_completion(task)
                        else:
                            self._metrics['downloads_failed'] += 1
                    
                    except Exception as e:
                        self.logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
                        self._metrics['downloads_failed'] += 1
                        # Notify UI of error
                        self._notify_error(task, str(e))
                        
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Worker {worker_id} exception: {e}", exc_info=True)
                
    def _notify_completion(self, task):
        """Notify UI controller of download completion"""
        # MODIFIED: No longer needs hasattr check, controller is guaranteed if set
        if self.controller and callable(getattr(self.controller, 'on_download_complete')):
            try:
                self.controller.on_download_complete(
                    task['url'], 
                    task['folder'], 
                    task['is_audio']
                )
            except Exception as e:
                self.logger.error(f"Failed to notify completion: {e}", exc_info=True)
                
    def _notify_error(self, task, error_msg):
        """Notify UI controller of download error"""
        # MODIFIED: No longer needs hasattr check, controller is guaranteed if set
        if self.controller and callable(getattr(self.controller, 'on_download_error')):
            try:
                self.controller.on_download_error(error_msg)
            except Exception as e:
                self.logger.error(f"Failed to notify error: {e}", exc_info=True)
                
    def get_status(self):
        """Get comprehensive status with metrics"""
        return {
            'queue_size': self.queue.size(),
            'workers': len([t for t in self._thread_pool if t.is_alive()]),
            'is_running': not self.queue.is_empty(),
            'metrics': self._metrics.copy()
        }
    
    def get_metrics(self):
        """Get download metrics"""
        return self._metrics.copy()

    def __call__(self, url: str, folder: str, is_audio: bool):
        """Create a task and add it to the download queue."""
        task = {'url': url, 'folder': folder, 'is_audio': is_audio}
        self.queue.enqueue(task)
