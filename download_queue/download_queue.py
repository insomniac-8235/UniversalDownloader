from queue import Queue
from worker import DownloadWorker
from typing import Dict, Any

class DownloadQueue:
    def __init__(self, worker: DownloadWorker, max_size=0):
        self._queue = Queue(max_size)
        self.worker = worker

    def enqueue(self, task: Dict[str, Any]):
        """Add a download task to the queue."""
        # Task should be a dict like {'url': '...', 'folder': '...', 'is_audio': True/False}
        self._queue.put(task)

    def dequeue(self, block=True, timeout=None):
        """Remove and return a task from the queue."""
        return self._queue.get(block=block, timeout=timeout)

    def execute_task(self, task: Dict[str, Any]) -> bool:
        """Execute a download task using the worker."""
        try:
            url = task['url']
            folder = task['folder']
            is_audio = task['is_audio']
            
            # Use the worker to download the media
            success = self.worker.download(url, folder, is_audio)
            return success
        except KeyError as e:
            # Log missing key in task
            self.worker.logger.error(f"Task missing required key: {e}", exc_info=True)
            return False
        except Exception as e:
            # Log any other exception during download
            self.worker.logger.error(f"Error executing task {task.get('url', '')}: {e}", exc_info=True)
            return False

    def size(self) -> int:
        """Return the current size of the queue."""
        return self._queue.qsize()

    def is_empty(self) -> bool:
        """Return True if the queue is empty, False otherwise."""
        return self._queue.empty()
