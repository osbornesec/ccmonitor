"""
CLI utility functions
Phase 4.1 - Supporting utilities for the command-line interface
"""

import logging
import os
import sys
from pathlib import Path
from typing import Union


def setup_logging(level: int = logging.INFO):
    """
    Setup logging configuration for CLI

    Args:
        level: Logging level (logging.DEBUG, logging.INFO, etc.)
    """
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)

    # Suppress verbose third-party logging
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB", "256 KB")
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    size_index = 0
    size_value = float(size_bytes)

    while size_value >= 1024 and size_index < len(size_names) - 1:
        size_value /= 1024
        size_index += 1

    if size_index == 0:
        return f"{int(size_value)} {size_names[size_index]}"
    else:
        return f"{size_value:.1f} {size_names[size_index]}"


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "1m 30s", "2.5s")
    """
    if seconds < 1:
        return f"{seconds:.3f}s"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def validate_file_access(path: Path, mode: str = "read") -> bool:
    """
    Validate file access permissions

    Args:
        path: File or directory path
        mode: Access mode ('read', 'write', 'execute')

    Returns:
        True if access is allowed, False otherwise
    """
    try:
        if mode == "read":
            return path.exists() and os.access(path, os.R_OK)
        elif mode == "write":
            if path.exists():
                return os.access(path, os.W_OK)
            else:
                # Check parent directory write access
                parent = path.parent
                return parent.exists() and os.access(parent, os.W_OK)
        elif mode == "execute":
            return path.exists() and os.access(path, os.X_OK)
        else:
            return False
    except Exception:
        return False


def ensure_directory(path: Path) -> bool:
    """
    Ensure directory exists, creating it if necessary

    Args:
        path: Directory path

    Returns:
        True if directory exists or was created, False otherwise
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def safe_filename(filename: str) -> str:
    """
    Create a safe filename by removing/replacing problematic characters

    Args:
        filename: Original filename

    Returns:
        Safe filename string
    """
    # Replace problematic characters
    safe_chars = []
    for char in filename:
        if char.isalnum() or char in "-_.":
            safe_chars.append(char)
        elif char in " /\\":
            safe_chars.append("_")

    result = "".join(safe_chars)

    # Ensure it's not empty and doesn't start with a dot
    if not result or result.startswith("."):
        result = f"file_{result}"

    return result


def confirm_destructive_operation(message: str, default: bool = False) -> bool:
    """
    Prompt user for confirmation of potentially destructive operations

    Args:
        message: Confirmation message
        default: Default response if user just presses Enter

    Returns:
        True if user confirms, False otherwise
    """
    try:
        import click

        return click.confirm(message, default=default)
    except ImportError:
        # Fallback for environments without click
        suffix = " (Y/n): " if default else " (y/N): "
        response = input(message + suffix).strip().lower()

        if not response:
            return default

        return response in ["y", "yes"]


def get_terminal_size() -> tuple[int, int]:
    """
    Get terminal size (width, height)

    Returns:
        Tuple of (width, height) in characters
    """
    try:
        import shutil

        size = shutil.get_terminal_size()
        return size.columns, size.lines
    except Exception:
        # Fallback to default size
        return 80, 24


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix

    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncating

    Returns:
        Truncated text string
    """
    if len(text) <= max_length:
        return text

    if max_length <= len(suffix):
        return suffix[:max_length]

    return text[: max_length - len(suffix)] + suffix


def parse_size_string(size_str: str) -> int:
    """
    Parse size string (e.g., "1.5MB", "256KB") to bytes

    Args:
        size_str: Size string with optional unit

    Returns:
        Size in bytes

    Raises:
        ValueError: If size string is invalid
    """
    size_str = size_str.upper().strip()

    # Extract number and unit
    size_multipliers = {
        "B": 1,
        "KB": 1024,
        "MB": 1024**2,
        "GB": 1024**3,
        "TB": 1024**4,
    }

    # Find unit suffix
    unit = "B"
    for suffix in size_multipliers:
        if size_str.endswith(suffix):
            unit = suffix
            size_str = size_str[: -len(suffix)]
            break

    try:
        size_value = float(size_str)
        return int(size_value * size_multipliers[unit])
    except ValueError:
        raise ValueError(f"Invalid size string: {size_str}{unit}")


def find_config_file() -> Union[Path, None]:
    """
    Find configuration file in standard locations

    Returns:
        Path to configuration file or None if not found
    """
    config_locations = [
        Path.cwd() / ".ccmonitor.yaml",
        Path.cwd() / ".ccmonitor.yml",
        Path.home() / ".ccmonitor.yaml",
        Path.home() / ".ccmonitor.yml",
        Path.home() / ".config" / "ccmonitor" / "config.yaml",
        Path.home() / ".config" / "ccmonitor" / "config.yml",
    ]

    for config_path in config_locations:
        if config_path.exists() and config_path.is_file():
            return config_path

    return None


def is_jsonl_file(path: Path) -> bool:
    """
    Check if file appears to be a JSONL file based on extension and content

    Args:
        path: File path to check

    Returns:
        True if file appears to be JSONL, False otherwise
    """
    # Check extension
    if path.suffix.lower() not in [".jsonl", ".ndjson"]:
        return False

    # Quick content check (first few lines)
    try:
        import json

        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 3:  # Check first 3 lines
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    json.loads(line)
                except json.JSONDecodeError:
                    return False

        return True
    except Exception:
        return False
