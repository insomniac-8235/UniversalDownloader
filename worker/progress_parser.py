import re
from functools import lru_cache

class ProgressParser:
    """Regex-based parser for yt-dlp/ffmpeg log lines"""
    
    MERGE_KEYWORDS = ["merging", "postprocessor", "finalising", "writing metadata"]
    DOWNLOAD_KEYWORDS = ["[download]", "downloading"]
    
    # Compile regex patterns at module load time for performance
    _MERGE_PATTERN = re.compile(
        r'(?:merging|postprocessor|finalising|writing metadata)', 
        re.IGNORECASE
    )
    _DOWNLOAD_PATTERN = re.compile(
        r'(?:(?:\[download\]|downloading))', 
        re.IGNORECASE
    )
    
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
        
        # Check merge keywords first (higher priority) - using compiled pattern
        if cls._MERGE_PATTERN.search(info_str):
            return "MERGING"
        
        # Default to downloading
        return "DOWNLOADING"
    
    @classmethod
    def is_downloading(cls, progress_info: str) -> bool:
        """Check if currently downloading"""
        return cls.detect_phase(progress_info) == "DOWNLOADING"
        
    @classmethod
    def is_merging(cls, progress_info: str) -> bool:
        """Check if currently merging/finalizing"""
        return cls.detect_phase(progress_info) == "MERGING"
        
    @classmethod
    def parse_progress_line(cls, line: str) -> dict:
        """Parse a single progress line for structured data"""
        result = {
            'phase': cls.detect_phase(line),
            'progress': None,
            'speed': None,
            'eta': None,
            'filename': None
        }
        
        # Extract progress percentage if present
        progress_match = re.search(r'(\d+)%', line)
        if progress_match:
            result['progress'] = int(progress_match.group(1))
            
        # Extract speed if present
        speed_match = re.search(r'(\d+\.\d+)\s*(?:MB|KB)/s', line)
        if speed_match:
            result['speed'] = float(speed_match.group(1))
            
        # Extract ETA if present
        eta_match = re.search(r'ETA:\s*(\d+)', line)
        if eta_match:
            result['eta'] = int(eta_match.group(1))
            
        # Extract filename if present
        filename_match = re.search(r'(\S+\.mp4|\S+\.m4a|\S+\.webm)', line)
        if filename_match:
            result['filename'] = filename_match.group(1)
            
        return result
    
    @classmethod
    def get_progress_percentage(cls, progress_info: str) -> float:
        """Extract progress percentage from progress info"""
        try:
            # Use compiled pattern for efficiency
            match = cls._DOWNLOAD_PATTERN.search(str(progress_info))
            if match:
                # Extract percentage from the matched string
                percent_match = re.search(r'(\d+)%', str(progress_info))
                if percent_match:
                    return float(percent_match.group(1))
        except Exception:
            pass
            
        return 0.0
    
    @classmethod
    def get_speed(cls, progress_info: str) -> float:
        """Extract download speed from progress info"""
        try:
            match = re.search(r'(\d+\.\d+)\s*(?:MB|KB)/s', str(progress_info))
            if match:
                return float(match.group(1))
        except Exception:
            pass
            
        return 0.0
    
    @classmethod
    def get_eta(cls, progress_info: str) -> int:
        """Extract ETA from progress info"""
        try:
            match = re.search(r'ETA:\s*(\d+)', str(progress_info))
            if match:
                return int(match.group(1))
        except Exception:
            pass
            
        return -1
