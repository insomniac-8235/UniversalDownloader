import re
from functools import lru_cache
from typing import Optional

class ProgressParser:
    """Regex-based parser for yt-dlp/ffmpeg log lines"""
    
    MERGE_KEYWORDS = ["merging", "postprocessor", "finalising", "writing metadata"]
    DOWNLOAD_KEYWORDS = ["[download]", "downloading"]
    
    # Compile regex patterns at module load time for performance
    # Compile regex patterns at module load time for performance
    _MERGE_PATTERN = re.compile(
        r'(?:merging|postprocessor|finalising|writing metadata)',
        re.IGNORECASE
    )
    _DOWNLOAD_PATTERN = re.compile(
        r'(?:(?:\[download\]|downloading))',
        re.IGNORECASE
    )
    # aria2c output pattern as per CONVENTIONS.md: [...] CN:X DL:Y
    _ARIA2C_PATTERN = re.compile(r'CN:\s*(\d+)\s+DL:\s*([\d.]+)\s*(?:M|K|G)iB/s', re.IGNORECASE)

    @classmethod
    def detect_phase(cls, progress_info: str) -> str:
        """
        Detect if we're downloading (yt-dlp or aria2c) or merging from log line.

        Args:
            progress_info: Raw progress string from yt-dlp/ffmpeg/aria2c

        Returns:
            "MERGING", "DOWNLOADING_YT_DLP", or "DOWNLOADING_ARIA2C"
        """
        info_str = str(progress_info)

        # Check for aria2c patterns first, as it's a specific download type
        if cls._ARIA2C_PATTERN.search(info_str):
            return "DOWNLOADING_ARIA2C"

        # Check merge keywords (higher priority for yt-dlp output)
        if cls._MERGE_PATTERN.search(info_str):
            return "MERGING"

        # Default to yt-dlp downloading if no other specific pattern matches
        if cls._DOWNLOAD_PATTERN.search(info_str):
            return "DOWNLOADING_YT_DLP"

        # Fallback for other lines, or if no specific download pattern is found
        return "UNKNOWN"

    @classmethod
    def is_downloading(cls, progress_info: str) -> bool:
        """Check if currently downloading (yt-dlp or aria2c)"""
        phase = cls.detect_phase(progress_info)
        return phase in ["DOWNLOADING_YT_DLP", "DOWNLOADING_ARIA2C"]

    @classmethod
    def is_merging(cls, progress_info: str) -> bool:
        """Check if currently merging/finalizing"""
        return cls.detect_phase(progress_info) == "MERGING"

    @classmethod
    def parse_progress_line(cls, line: str) -> dict:
        """Parse a single progress line for structured data, handling yt-dlp and aria2c."""
        result = {
            'phase': cls.detect_phase(line),
            'progress': None,  # Percentage (0-100)
            'speed': None,     # In MB/s or KB/s
            'eta': None,       # In seconds
            'filename': None,  # Filename being processed
            'connections': None # For aria2c
        }

        info_str = str(line)
        
        if result['phase'] == "DOWNLOADING_ARIA2C":
            # Example: CN:X DL:Y ETA:Z
            aria2c_match = cls._ARIA2C_PATTERN.search(info_str)
            if aria2c_match:
                result['connections'] = int(aria2c_match.group(1))
                speed_str = aria2c_match.group(2)
                # Convert speed to float, handling units (MiB/s, KiB/s, GiB/s)
                unit_match = re.search(r'([\d.]+)\s*(M|K|G)iB/s', info_str, re.IGNORECASE)
                if unit_match:
                    value = float(unit_match.group(1))
                    unit = unit_match.group(2).upper()
                    if unit == 'G':
                        result['speed'] = value * 1024 # Convert GiB/s to MiB/s for consistency
                    elif unit == 'K':
                        result['speed'] = value / 1024 # Convert KiB/s to MiB/s
                    else: # M
                        result['speed'] = value
                
            eta_match = re.search(r'ETA:\s*(\d+)s', info_str) # aria2c typically uses "s"
            if eta_match:
                result['eta'] = int(eta_match.group(1))
            
            # aria2c output as per conventions does not directly provide percentage for overall progress.
            # We'll rely on yt-dlp's overall progress if it wraps aria2c.
            # For now, if an aria2c line is detected, we can assume some progress is happening.
            # If `aria2c` line is active, ensure progress doesn't drop to 0.
            # A common strategy is to report a small non-zero progress if no specific percent is found.
            # However, the direct request is to parse DL/CN, not to invent progress.
            # The UI should handle `None` for progress for aria2c lines by retaining last known progress.

        elif result['phase'] in ["DOWNLOADING_YT_DLP", "MERGING"]:
            # Extract progress percentage if present (yt-dlp format)
            progress_match = re.search(r'(\d+)%', info_str)
            if progress_match:
                result['progress'] = int(progress_match.group(1))

            # Extract speed if present (yt-dlp format)
            speed_match = re.search(r'(\d+\.\d+)\s*(?:MB|KB)/s', info_str)
            if speed_match:
                result['speed'] = float(speed_match.group(1))

            # Extract ETA if present (yt-dlp format)
            eta_match = re.search(r'ETA:\s*(\d+)', info_str)
            if eta_match:
                result['eta'] = int(eta_match.group(1))

            # Extract filename if present (yt-dlp format)
            filename_match = re.search(r'(\S+\.mp4|\S+\.m4a|\S+\.webm)', info_str)
            if filename_match:
                result['filename'] = filename_match.group(1)

        return result

    @classmethod
    def get_progress_percentage(cls, progress_info: str) -> Optional[float]:
        """Extract progress percentage from progress info, handling both yt-dlp and aria2c."""
        parsed = cls.parse_progress_line(progress_info)
        return float(parsed['progress']) if parsed['progress'] is not None else None

    @classmethod
    def get_speed(cls, progress_info: str) -> Optional[float]:
        """Extract download speed from progress info, handling both yt-dlp and aria2c."""
        parsed = cls.parse_progress_line(progress_info)
        return float(parsed['speed']) if parsed['speed'] is not None else None

    @classmethod
    def get_eta(cls, progress_info: str) -> Optional[int]:
        """Extract ETA from progress info, handling both yt-dlp and aria2c."""
        parsed = cls.parse_progress_line(progress_info)
        return int(parsed['eta']) if parsed['eta'] is not None else None
