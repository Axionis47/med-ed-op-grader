"""Timestamp parsing and formatting utilities."""

import re


def parse_timestamp(timestamp: str) -> tuple[int, int, int]:
    """
    Parse timestamp string into hours, minutes, seconds.
    
    Args:
        timestamp: Timestamp in format MM:SS or HH:MM:SS
    
    Returns:
        Tuple of (hours, minutes, seconds)
    
    Raises:
        ValueError: If timestamp format is invalid
    
    Example:
        >>> parse_timestamp("01:30")
        (0, 1, 30)
        >>> parse_timestamp("1:05:30")
        (1, 5, 30)
    """
    pattern = r"^(\d{1,2}:)?(\d{1,2}):(\d{2})$"
    match = re.match(pattern, timestamp)
    
    if not match:
        raise ValueError(f"Invalid timestamp format: {timestamp}. Expected MM:SS or HH:MM:SS")
    
    hours = 0
    if match.group(1):
        hours = int(match.group(1).rstrip(':'))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
    else:
        minutes = int(match.group(2))
        seconds = int(match.group(3))
    
    return hours, minutes, seconds


def timestamp_to_seconds(timestamp: str) -> float:
    """
    Convert timestamp to total seconds.
    
    Args:
        timestamp: Timestamp in format MM:SS or HH:MM:SS
    
    Returns:
        Total seconds as float
    
    Example:
        >>> timestamp_to_seconds("01:30")
        90.0
        >>> timestamp_to_seconds("1:05:30")
        3930.0
    """
    hours, minutes, seconds = parse_timestamp(timestamp)
    return hours * 3600 + minutes * 60 + seconds


def format_timestamp(seconds: float, include_hours: bool = False) -> str:
    """
    Format seconds into timestamp string.
    
    Args:
        seconds: Total seconds
        include_hours: Whether to include hours even if 0
    
    Returns:
        Formatted timestamp string
    
    Example:
        >>> format_timestamp(90)
        '01:30'
        >>> format_timestamp(3930)
        '1:05:30'
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0 or include_hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def calculate_duration(start: str, end: str) -> float:
    """
    Calculate duration between two timestamps in seconds.
    
    Args:
        start: Start timestamp
        end: End timestamp
    
    Returns:
        Duration in seconds
    
    Example:
        >>> calculate_duration("01:00", "01:30")
        30.0
    """
    start_seconds = timestamp_to_seconds(start)
    end_seconds = timestamp_to_seconds(end)
    return end_seconds - start_seconds

