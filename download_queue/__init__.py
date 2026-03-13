import queue as stdlib_queue
import threading
from download_worker import DownloadWorker
from utilities.logger import MyLogger

class DownloadQueue:
    def __init__(self, max_workers=4):
        self.queue = stdlib_queue.Queue()
        self.workers = []
        self.max_workers = max_workers
        self.logger = MyLogger()
        self.stop_event = threading.Event()
        
    def enqueue(self, url, folder, is_audio):
        self.queue.put((url, folder, is_audio))
        return self.queue.qsize()
    
    def dequeue(self):
        try:
            return self.queue.get(timeout=1)
        except stdlib_queue.Empty:
            return None
    
    def is_empty(self):
        return self.queue.empty()
    
    def size(self):
        return self.queue.qsize()
    
    def start(self):
        for _ in range(self.max_workers):
            try:
                worker = DownloadWorker(self.logger)
                thread = threading.Thread(target=worker, daemon=True)
                thread.start()
                self.workers.append((worker, thread))
            except Exception as e:
                self.logger.error(f"Failed to start worker: {e}")
    
    def stop(self):
        for worker, thread in self.workers:
            try:
                worker.stop()
            except Exception:
                pass
            try:
                thread.join(timeout=2)
            except Exception:
                pass
        self.workers = []
