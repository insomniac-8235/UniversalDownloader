import threading
from download_queue import DownloadQueue
from utilities.logger import MyLogger

class ThreadPoolManager:
    def __init__(self, max_workers=4):
        self.queue = DownloadQueue(max_workers)
        self.max_workers = max_workers
        self.logger = MyLogger()
        
    def start(self):
        self.queue.start()
        
    def stop(self):
        self.queue.stop()
        
    def get_status(self):
        return {
            'queue_size': self.queue.size(),
            'workers': len(self.queue.workers),
            'is_running': not self.queue.is_empty()
        }
