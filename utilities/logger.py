import time
import threading

class MyLogger:
    def __init__(self):
        self._last_info_time = 0
        self._last_progress_time = 0
        self._info_lock = threading.Lock()
        self._progress_lock = threading.Lock()
    
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
