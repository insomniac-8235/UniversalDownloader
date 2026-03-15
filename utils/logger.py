import time
import threading
from queue import Queue, Empty
import sys
import traceback # ADD THIS IMPORT

# Define logging levels for clarity and control
DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40

class MyLogger:
    def __init__(self, level=INFO):
        self._last_info_time = 0
        self._last_progress_time = 0 # This is for text-based progress messages, not the UI progress bar value
        self._info_lock = threading.Lock()
        self._progress_lock = threading.Lock()
        self._message_queue = Queue() # No maxsize; handle drops explicitly if needed, but for logs, let it grow or use proper handlers
        self._level = level # Set the initial logging level

        # Start the processing thread as a daemon so it doesn't prevent app exit
        self._processing_thread = threading.Thread(target=self._process_queue_loop, daemon=True)
        self._processing_thread.start()
        
    def set_level(self, level: int):
        """Set the current logging level."""
        self._level = level

    def _log_message(self, level: int, message: str, print_immediately: bool = False):
        """Internal method to queue a message with its level."""
        if level >= self._level:
            try:
                # Use put_nowait to avoid blocking if the queue gets full, though for logs, usually not an issue
                # If print_immediately is true, it means it's a critical error that shouldn't wait
                if print_immediately:
                    self._print_formatted_message(level, message)
                else:
                    self._message_queue.put_nowait((level, message))
            except Exception:
                # Fallback print if queueing fails (e.g., queue full, which shouldn't happen without maxsize)
                self._print_formatted_message(ERROR, f"Failed to queue log message: {message}")
                
    def debug(self, msg: str):
        self._log_message(DEBUG, f"DEBUG: {msg}")
            
    def warning(self, msg: str): 
        self._log_message(WARNING, f"WARNING: {msg}")
        
    def error(self, msg: str, exc_info=False): # MODIFIED: Default exc_info to False
        formatted_msg = f"ERROR: {msg}"
        if exc_info:
            if isinstance(exc_info, bool) and exc_info: # If exc_info is True, fetch current exception
                exc_type, exc_value, exc_traceback = sys.exc_info()
                if exc_type is not None:
                    formatted_msg += "\n" + "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            elif isinstance(exc_info, tuple) and len(exc_info) == 3: # If tuple (exc_type, exc_value, exc_traceback)
                formatted_msg += "\n" + "".join(traceback.format_exception(exc_info[0], exc_info[1], exc_info[2]))
            elif isinstance(exc_info, BaseException): # If an exception object
                formatted_msg += "\n" + "".join(traceback.format_exception(type(exc_info), exc_info, exc_info.__traceback__))
        self._log_message(ERROR, formatted_msg, print_immediately=True) # Errors often need immediate attention
        
    def info(self, msg: str):
        """Log informational messages with rate limiting."""
        current_time = time.time()
        with self._info_lock:
            if current_time - self._last_info_time >= 0.1:  # Max 10Hz
                self._log_message(INFO, f"INFO: {msg}")
                self._last_info_time = current_time
                
    def progress(self, msg: str):
        """Log text-based progress messages with strict rate limiting (max 10Hz).
           Note: UI progress bar updates are handled by the separate progress_hook callback."""
        current_time = time.time()
        with self._progress_lock:
            if current_time - self._last_progress_time >= 0.1:  # Max 10Hz
                # Progress messages are often info-level or debug-level
                self._log_message(INFO, f"PROGRESS: {msg}")
                self._last_progress_time = current_time
                
    def _process_queue_loop(self):
        """Processes queued messages in a background thread."""
        while True:
            try:
                level, message = self._message_queue.get(timeout=0.5) # Short timeout
                self._print_formatted_message(level, message)
                self._message_queue.task_done()
            except Empty:
                continue # Keep looping
            except Exception as e:
                # Log internal logger errors to stderr directly
                print(f"CRITICAL LOGGER ERROR: {e}", file=sys.stderr)
                time.sleep(1) # Prevent busy-waiting on repeated errors
                
    def _print_formatted_message(self, level: int, message: str):
        """Prints a message to stdout/stderr, respecting its level."""
        if level >= self._level:
            # For ERROR, print to stderr
            if level >= ERROR:
                print(message, file=sys.stderr)
            else:
                print(message, file=sys.stdout)

    def flush(self):
        """Wait for all queued messages to be processed."""
        self._message_queue.join()
                
    def reset_rate_limits(self):
        """Reset rate limiting timers (useful for testing)"""
        with self._info_lock:
            self._last_info_time = 0
        with self._progress_lock:
            self._last_progress_time = 0
