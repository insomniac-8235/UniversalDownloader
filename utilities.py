import os
import sys
import shutil

class MyLogger:
    def debug(self, msg):
        # Only print if it's not a noisy progress message
        if not msg.startswith('[debug] '):
            print(f"DEBUG: {msg}")
    
    def warning(self, msg): 
        print(f"WARNING: {msg}")
    
    def error(self, msg): 
        print(f"ERROR: {msg}")
