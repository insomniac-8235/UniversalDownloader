import re

class ProgressParser:
    """Regex-based parser for yt-dlp/ffmpeg log lines"""
    
    MERGE_KEYWORDS = ["merging", "postprocessor", "finalising", "writing metadata"]
    DOWNLOAD_KEYWORDS = ["[download]", "downloading"]
    
    @classmethod
    def detect_phase(cls, progress_info: str) -> str:
        """
        Detect if we're downloading or merging from yt-dlp log line.
        
        Args:
            progress_info: Raw progress string from yt-dlp/ffmpeg
            
        Returns:
            "MERGING" or "DOWNLOADING"
        """
        info_str = str(progress_info).lower()
        
        # Check merge keywords first (higher priority)
        for keyword in cls.MERGE_KEYWORDS:
            if keyword in info_str:
                return "MERGING"
        
        # Default to downloading
        return "DOWNLOADING"
