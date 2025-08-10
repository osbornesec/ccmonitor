"""CLI utility functions.

Phase 4.1 - Supporting utilities for the command-line interface.
"""

import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import TextIO

try:
    import click
except ImportError:
    click = None

from .constants import (
    BYTES_PER_KILOBYTE,
    JSONL_DETECTION_SAMPLE_LINES,
    SECONDS_PER_HOUR,
    SECONDS_PER_MINUTE,
)


def setup_logging(level: int = logging.INFO) -> None:
    """Set up logging configuration for CLI.

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
    """Format file size in human-readable format.

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

    while size_value >= BYTES_PER_KILOBYTE and size_index < len(size_names) - 1:
        size_value /= BYTES_PER_KILOBYTE
        size_index += 1

    if size_index == 0:
        return f"{int(size_value)} {size_names[size_index]}"
    return f"{size_value:.1f} {size_names[size_index]}"


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "1m 30s", "2.5s")

    """
    if seconds < 1:
        return f"{seconds:.3f}s"
    if seconds < SECONDS_PER_MINUTE:
        return f"{seconds:.1f}s"
    if seconds < SECONDS_PER_HOUR:
        minutes = int(seconds // SECONDS_PER_MINUTE)
        remaining_seconds = int(seconds % SECONDS_PER_MINUTE)
        return f"{minutes}m {remaining_seconds}s"
    hours = int(seconds // SECONDS_PER_HOUR)
    minutes = int((seconds % SECONDS_PER_HOUR) // SECONDS_PER_MINUTE)
    return f"{hours}h {minutes}m"


def validate_file_access(path: Path, mode: str = "read") -> bool:
    """Validate file access permissions.

    Args:
        path: File or directory path
        mode: Access mode ('read', 'write', 'execute')

    Returns:
        True if access is allowed, False otherwise

    """
    try:
        return _check_access_by_mode(path, mode)
    except (OSError, PermissionError, FileNotFoundError):
        return False


def _check_access_by_mode(path: Path, mode: str) -> bool:
    """Check access permissions based on mode."""
    if mode == "read":
        return _check_read_access(path)
    if mode == "write":
        return _check_write_access(path)
    if mode == "execute":
        return _check_execute_access(path)
    return False


def _check_read_access(path: Path) -> bool:
    """Check read access permissions."""
    return path.exists() and os.access(path, os.R_OK)


def _check_write_access(path: Path) -> bool:
    """Check write access permissions."""
    if path.exists():
        return os.access(path, os.W_OK)
    # Check parent directory write access
    parent = path.parent
    return parent.exists() and os.access(parent, os.W_OK)


def _check_execute_access(path: Path) -> bool:
    """Check execute access permissions."""
    return path.exists() and os.access(path, os.X_OK)


def ensure_directory(path: Path) -> bool:
    """Ensure directory exists, creating it if necessary.

    Args:
        path: Directory path

    Returns:
        True if directory exists or was created, False otherwise

    """
    try:
        path.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError):
        return False
    else:
        return True


def safe_filename(filename: str) -> str:
    """Create a safe filename by removing/replacing problematic characters.

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


def confirm_destructive_operation(message: str, *, default: bool = False) -> bool:
    """Prompt user for confirmation of potentially destructive operations.

    Args:
        message: Confirmation message
        default: Default response if user just presses Enter

    Returns:
        True if user confirms, False otherwise

    """
    if click is not None:
        return click.confirm(message, default=default)  # type: ignore[no-any-return]

    # Fallback for environments without click
    suffix = " (Y/n): " if default else " (y/N): "
    response = input(message + suffix).strip().lower()

    if not response:
        return default

    return response in ["y", "yes"]


def get_terminal_size() -> tuple[int, int]:
    """Get terminal size (width, height).

    Returns:
        Tuple of (width, height) in characters

    """
    try:
        size = shutil.get_terminal_size()
    except (OSError, AttributeError):
        # Fallback to default size
        return 80, 24
    else:
        return size.columns, size.lines


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length with suffix.

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
    """Parse size string (e.g., "1.5MB", "256KB") to bytes.

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
        "KB": BYTES_PER_KILOBYTE,
        "MB": BYTES_PER_KILOBYTE**2,
        "GB": BYTES_PER_KILOBYTE**3,
        "TB": BYTES_PER_KILOBYTE**4,
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
    except ValueError as e:
        msg = f"Invalid size string: {size_str}{unit}"
        raise ValueError(msg) from e


def find_config_file() -> Path | None:
    """Find configuration file in standard locations.

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
    """Check if file appears to be a JSONL file based on extension and content.

    Args:
        path: File path to check

    Returns:
        True if file appears to be JSONL, False otherwise

    """
    if not _has_jsonl_extension(path):
        return False

    return _validate_jsonl_content(path)


def _has_jsonl_extension(path: Path) -> bool:
    """Check if file has a JSONL extension."""
    return path.suffix.lower() in [".jsonl", ".ndjson"]


def _validate_jsonl_content(path: Path) -> bool:
    """Validate file content as JSONL format."""
    try:

        with path.open(encoding="utf-8") as f:
            return _check_sample_lines(f)
    except (OSError, UnicodeDecodeError):
        return False


def _check_sample_lines(file_handle: TextIO) -> bool:
    """Check first few lines for valid JSON."""
    for i, line in enumerate(file_handle):
        if i >= JSONL_DETECTION_SAMPLE_LINES:
            break

        stripped_line = line.strip()
        if not stripped_line:
            continue

        if not _is_valid_json_line(stripped_line):
            return False

    return True


def _is_valid_json_line(line: str) -> bool:
    """Check if a line contains valid JSON."""
    try:
        json.loads(line)
    except json.JSONDecodeError:
        return False
    else:
        return True
