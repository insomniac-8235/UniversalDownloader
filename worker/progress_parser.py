import re
from typing import Optional

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
    # UPDATED: aria2c pattern to accurately capture percentage, connections, speed, and optional ETA
    # This pattern matches the provided console output:
    # [#044aa5 19MiB/805MiB(2%) CN:16 DL:21MiB ETA:36s]
    # It accounts for the optional downloaded/total size before the percentage.
    _ARIA2C_PATTERN = re.compile(
        r'\[#\w+\s+(?:[\d\.]+[KMGT]?i?B/[\d\.]+[KMGT]?i?B)?\((?P<percentage>\d{1,3}(?:\.\d{1,2})?)%\)\s+CN:(?P<connections>\d+)\s+DL:(?P<speed>[\d\.]+(?:[KMGT]?i?)B)(?:\s+ETA:(?P<eta>[\dsmh:]+))?',
        re.IGNORECASE
    )

    @classmethod
    def detect_phase(cls, progress_info: str) -> str:
        """
        Detect if we're downloading (yt-dlp or aria2c) or merging from log line.

        Args:
            progress_info: Raw progress string from yt-dlp/ffmpeg/aria2c

        Returns:
            "MERGING", "DOWNLOADING_YT_DLP", or "DOWNLOADING_ARIA2C"
        """
        info_str = progress_info

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
            'speed': None,     # In MiB/s (float)
            'eta': None,       # In seconds (int)
            'filename': None,  # Filename being processed
            'connections': None # For aria2c (int)
        }

        info_str = line

        if result['phase'] == "DOWNLOADING_ARIA2C":
            aria2c_match = cls._ARIA2C_PATTERN.search(info_str)
            if aria2c_match:
                # Extract percentage
                percentage_str = aria2c_match.group('percentage')
                if percentage_str:
                    result['progress'] = float(percentage_str)

                # Extract connections
                connections_str = aria2c_match.group('connections')
                if connections_str:
                    result['connections'] = int(connections_str)

                # Extract speed (DL:XMiB, where XMiB is the speed, no /s in the log itself)
                speed_str = aria2c_match.group('speed')
                if speed_str:
                    result['speed'] = cls._convert_speed_to_mbps(speed_str)

                # Extract ETA
                eta_str = aria2c_match.group('eta')
                if eta_str:
                    result['eta'] = cls._convert_eta_to_seconds(eta_str)

        elif result['phase'] in ["DOWNLOADING_YT_DLP", "MERGING"]:
            # Extract progress percentage if present (yt-dlp format)
            progress_match = re.search(r'(\d+)%', info_str)
            if progress_match:
                result['progress'] = int(progress_match.group(1))

            # Extract speed if present (yt-dlp format) - convert to MiB/s
            speed_match = re.search(r'(\d+\.\d+)\s*(?:M|K)B/s', info_str) # Adjusted to handle KB/s
            if speed_match:
                value = float(speed_match.group(1))
                unit = speed_match.group(0)[-4:-2] # Get 'MB' or 'KB'
                if unit == 'KB':
                    result['speed'] = value / 1024 # Convert KB/s to MiB/s
                else: # MB/s
                    result['speed'] = value # yt-dlp reports in MB/s, keep as MiB/s roughly

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

    @staticmethod
    def _convert_speed_to_mbps(speed_str: str) -> Optional[float]:
        """Converts a speed string (e.g., "1.2MiB/s", "10KB/s", "21MiB") to a float in MiB/s."""
        if not speed_str:
            return None
        # Modified regex to make "/s" optional
        match = re.match(r'([\d\.]+)([KMGT]?i?)B(?:/s)?', speed_str, re.IGNORECASE)
        if not match:
            return None
        value = float(match[1])
        unit = match[2].upper()

        if unit in ['K', 'KI']:
            return value / 1024 # Convert KiB/s to MiB/s
        elif unit in ['M', 'MI']:
            return value
        elif unit in ['G', 'GI']:
            return value * 1024
        elif unit in ['T', 'TI']:
            return value * 1024 * 1024
        elif not unit: # Bytes/s
            return value / (1024 * 1024)
        return value

    @staticmethod
    def _convert_eta_to_seconds(eta_str: str) -> Optional[int]:
        """Converts an ETA string (e.g., "00:00", "1m", "0s") to total seconds."""
        if not eta_str:
            return None

        total_seconds = 0

        # Handle HH:MM:SS or MM:SS format
        if ':' in eta_str:
            parts = eta_str.split(':')
            try:
                if len(parts) == 2: # MM:SS
                    total_seconds += int(parts[0]) * 60
                    total_seconds += int(parts[1])
                elif len(parts) == 3: # HH:MM:SS
                    total_seconds += int(parts[0]) * 3600
                    total_seconds += int(parts[1]) * 60
                    total_seconds += int(parts[2])
            except ValueError:
                return None # Invalid format
        else: # Handle formats like "1h23m45s", "1m", "0s"
            if hours_match := re.search(r'(\d+)h', eta_str):
                total_seconds += int(hours_match.group(1)) * 3600

            if minutes_match := re.search(r'(\d+)m', eta_str):
                total_seconds += int(minutes_match.group(1)) * 60

            if seconds_match := re.search(r'(\d+)s', eta_str):
                total_seconds += int(seconds_match[1])

        return total_seconds
