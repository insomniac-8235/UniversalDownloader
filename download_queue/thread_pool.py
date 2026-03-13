import threading
from download_queue import DownloadQueue
from utilities.logger import MyLogger
from queue import Queue, Empty
import time
import subprocess

class ThreadPoolManager:
    def __init__(self, max_workers=4):
        self.queue = DownloadQueue(max_workers)
        self.max_workers = max_workers
        self.logger = MyLogger()
        self._thread_pool = []
        self._shutdown_event = threading.Event()
        self._metrics = {
            'downloads_completed': 0,
            'downloads_failed': 0,
            'total_time': 0,
            'avg_download_speed': 0
        }
        
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
                        else:
                            self._metrics['downloads_failed'] += 1
                            
                    except Exception as e:
                        self.logger.error(f"Worker {worker_id} error: {e}")
                        self._metrics['downloads_failed'] += 1
                        
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Worker {worker_id} exception: {e}")
                
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
