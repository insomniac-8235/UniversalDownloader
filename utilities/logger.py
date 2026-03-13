import time
import threading
from queue import Queue, Empty
import sys

class MyLogger:
    def __init__(self):
        self._last_info_time = 0
        self._last_progress_time = 0
        self._info_lock = threading.Lock()
        self._progress_lock = threading.Lock()
        self._message_queue = Queue(maxsize=100)
        
    def debug(self, msg):
        # Only print if it's not a noisy progress message
        if not msg.startswith('[debug] '):
            print(f"DEBUG: {msg}")
            
    def warning(self, msg): 
        print(f"WARNING: {msg}")
        
    def error(self, msg): 
        print(f"ERROR: {msg}")
        
    def info(self, msg):
        """Log informational messages with rate limiting"""
        # Prevent UI saturation from too many progress updates
        current_time = time.time()
        
        with self._info_lock:
            if current_time - self._last_info_time >= 0.1:  # Max 10Hz
                print(f"INFO: {msg}")
                self._last_info_time = current_time
                
    def progress(self, msg):
        """Log progress messages with strict rate limiting (max 10Hz)"""
        current_time = time.time()
        
        with self._progress_lock:
            if current_time - self._last_progress_time >= 0.1:  # Max 10Hz
                print(f"PROGRESS: {msg}")
                self._last_progress_time = current_time
                
    def queue_message(self, msg_type, message):
        """Queue a message for async logging (non-blocking)"""
        try:
            self._message_queue.put_nowait((msg_type, message))
        except Exception:
            # Queue is full, drop the message
            pass
            
    def process_queue(self):
        """Process queued messages in background thread"""
        while True:
            try:
                msg_type, message = self._message_queue.get(timeout=0.1)
                
                if msg_type == 'info':
                    self.info(message)
                elif msg_type == 'progress':
                    self.progress(message)
                    
            except Empty:
                continue
            except Exception:
                time.sleep(0.1)
                continue
                
    def flush(self):
        """Flush all queued messages immediately"""
        while not self._message_queue.empty():
            try:
                msg_type, message = self._message_queue.get_nowait()
                
                if msg_type == 'info':
                    self.info(message)
                elif msg_type == 'progress':
                    self.progress(message)
                    
            except Exception:
                break
                
    def reset_rate_limits(self):
        """Reset rate limiting timers (useful for testing)"""
        self._last_info_time = 0
        self._last_progress_time = 0
