"""Real-time file monitoring system for Claude JSONL activity files."""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver

from .jsonl_parser import JSONLEntry, StreamingJSONLParser

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from watchdog.observers.api import BaseObserver

# Configure logger
logger = logging.getLogger(__name__)

# Constants
MAX_RETRY_ATTEMPTS = 3
DEFAULT_DEBOUNCE_SECONDS = 0.1
DEFAULT_FILE_AGE_LIMIT_HOURS = 24


class FileMonitorError(Exception):
    """Custom exception for file monitoring errors."""

    def __init__(self, message: str, file_path: str | None = None) -> None:
        """Initialize monitor error.

        Args:
            message: Error message
            file_path: File path that caused the error

        """
        super().__init__(message)
        self.message = message
        self.file_path = file_path


class FileState:
    """Track the state of a monitored file."""

    def __init__(self, file_path: Path) -> None:
        """Initialize file state.

        Args:
            file_path: Path to the file being monitored

        """
        self.file_path = file_path
        self.last_position = 0
        self.last_size = 0
        self.last_modified = 0.0
        self.is_active = True
        self.lock = threading.Lock()

    def update_position(self, position: int) -> None:
        """Update the file read position.

        Args:
            position: New position in the file

        """
        with self.lock:
            self.last_position = position

    def update_stats(self) -> None:
        """Update file statistics from filesystem."""
        try:
            with self.lock:
                if self.file_path.exists():
                    stat = self.file_path.stat()
                    self.last_size = stat.st_size
                    self.last_modified = stat.st_mtime
                else:
                    self.is_active = False
        except OSError:
            logger.warning(
                "Failed to update stats for %s",
                self.file_path,
                exc_info=True,
            )
            self.is_active = False


class DebouncedJSONLHandler(FileSystemEventHandler):
    """File system event handler with debouncing for JSONL files."""

    def __init__(
        self,
        processor: FileMonitor,
        debounce_seconds: float = DEFAULT_DEBOUNCE_SECONDS,
    ) -> None:
        """Initialize the handler.

        Args:
            processor: FileMonitor instance to handle events
            debounce_seconds: Debounce delay in seconds

        """
        self.processor = processor
        self.debounce_seconds = debounce_seconds
        self.pending_files: dict[str, threading.Timer] = {}
        self.lock = threading.Lock()

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events.

        Args:
            event: File system event

        """
        if event.is_directory:
            return

        file_path = Path(str(event.src_path))

        # Only process JSONL files
        if file_path.suffix.lower() != ".jsonl":
            return

        # Only process files we're monitoring
        if not self.processor.is_monitored(file_path):
            return

        logger.debug("File modified: %s", file_path)
        self._schedule_processing(str(file_path))

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events.

        Args:
            event: File system event

        """
        if event.is_directory:
            return

        file_path = Path(str(event.src_path))

        # Only process JSONL files
        if file_path.suffix.lower() != ".jsonl":
            return

        # Check if this is in our watch directories
        if any(
            file_path.is_relative_to(watch_dir)
            for watch_dir in self.processor.watch_directories
        ):
            logger.info("New JSONL file created: %s", file_path)
            self.processor.add_file(file_path)
            self._schedule_processing(str(file_path))

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events.

        Args:
            event: File system event

        """
        if event.is_directory:
            return

        file_path = Path(str(event.src_path))
        if file_path.suffix.lower() == ".jsonl":
            logger.info("JSONL file deleted: %s", file_path)
            self.processor.remove_file(file_path)

    def _schedule_processing(self, file_path: str) -> None:
        """Schedule file processing with debouncing.

        Args:
            file_path: Path to the file to process

        """
        with self.lock:
            # Cancel previous timer for this file
            if file_path in self.pending_files:
                self.pending_files[file_path].cancel()

            # Schedule new processing
            timer = threading.Timer(
                self.debounce_seconds,
                self._process_file_safe,
                [file_path],
            )
            self.pending_files[file_path] = timer
            timer.start()

    def _process_file_safe(self, file_path: str) -> None:
        """Process file with error recovery.

        Args:
            file_path: Path to the file to process

        """
        try:
            with self.lock:
                self.pending_files.pop(file_path, None)

            self._attempt_file_processing(file_path)

        except Exception:
            logger.exception("Critical error in file processing")

    def _attempt_file_processing(self, file_path: str) -> None:
        """Attempt to process file with retries.

        Args:
            file_path: Path to the file to process

        """
        for attempt in range(MAX_RETRY_ATTEMPTS):
            if self._try_process_file(file_path, attempt):
                return

    def _try_process_file(self, file_path: str, attempt: int) -> bool:
        """Try to process a file once.

        Args:
            file_path: Path to the file to process
            attempt: Current attempt number

        Returns:
            True if processing succeeded

        """
        try:
            self.processor.process_file_changes(Path(file_path))
        except OSError:
            return self._handle_os_error(file_path, attempt)
        except Exception:
            logger.exception("Unexpected error processing %s", file_path)
            return True  # Don't retry on unexpected errors
        else:
            return True

    def _handle_os_error(self, file_path: str, attempt: int) -> bool:
        """Handle OS error during file processing.

        Args:
            file_path: Path to the file being processed
            attempt: Current attempt number

        Returns:
            True if should stop retrying

        """
        if attempt < MAX_RETRY_ATTEMPTS - 1:
            time.sleep(0.1 * (2**attempt))
            return False  # Continue retrying
        logger.exception("Failed to process %s after retries", file_path)
        return True  # Stop retrying

    def cleanup(self) -> None:
        """Cancel all pending timers."""
        with self.lock:
            for timer in self.pending_files.values():
                timer.cancel()
            self.pending_files.clear()


class FileMonitor:
    """Real-time file monitoring system for JSONL activity files."""

    def __init__(
        self,
        watch_directories: list[str | Path] | None = None,
        *,
        debounce_seconds: float = DEFAULT_DEBOUNCE_SECONDS,
        file_age_limit_hours: int = DEFAULT_FILE_AGE_LIMIT_HOURS,
        use_polling: bool = False,
    ) -> None:
        """Initialize the file monitor.

        Args:
            watch_directories: Directories to monitor for JSONL files
            debounce_seconds: Debounce delay for file changes
            file_age_limit_hours: Skip files older than this many hours
            use_polling: Force use of polling observer (for CIFS, etc.)

        """
        self.watch_directories = [
            Path(d).expanduser().resolve() for d in (watch_directories or [])
        ]
        self.debounce_seconds = debounce_seconds
        self.file_age_limit_hours = file_age_limit_hours
        self.use_polling = use_polling

        # File state tracking
        self.file_states: dict[Path, FileState] = {}
        self.file_states_lock = threading.Lock()

        # Observer and handler
        self.observer: BaseObserver | None = None
        self.handler: DebouncedJSONLHandler | None = None

        # Parser
        self.parser = StreamingJSONLParser(
            skip_validation=False,
            file_age_limit_hours=file_age_limit_hours,
        )

        # Callbacks for new messages
        self.message_callbacks: list[Callable[[JSONLEntry, Path], None]] = []
        self.error_callbacks: list[Callable[[Exception, Path], None]] = []

        # Statistics
        self.stats: dict[str, int | float | None] = {
            "files_monitored": 0,
            "messages_processed": 0,
            "errors_encountered": 0,
            "start_time": None,
        }

        # Control flags
        self._is_running = False
        self._shutdown_event = threading.Event()

        # Set default watch directory if none provided
        self._setup_default_watch_directories()

    def _setup_default_watch_directories(self) -> None:
        """Set up default watch directories if none provided."""
        if not self.watch_directories:
            default_claude_dir = Path("~/.claude/projects").expanduser()
            if default_claude_dir.exists():
                self.watch_directories = [default_claude_dir]
            else:
                logger.warning(
                    "No watch directories specified and ~/.claude/projects not found",
                )

    def add_message_callback(
        self,
        callback: Callable[[JSONLEntry, Path], None],
    ) -> None:
        """Add a callback for new messages.

        Args:
            callback: Callback function that takes (message, file_path)

        """
        self.message_callbacks.append(callback)

    def add_error_callback(
        self,
        callback: Callable[[Exception, Path], None],
    ) -> None:
        """Add a callback for errors.

        Args:
            callback: Callback function that takes (error, file_path)

        """
        self.error_callbacks.append(callback)

    def discover_jsonl_files(self) -> list[Path]:
        """Discover existing JSONL files in watch directories.

        Returns:
            List of JSONL file paths

        """
        jsonl_files = []

        for watch_dir in self.watch_directories:
            jsonl_files.extend(self._discover_files_in_directory(watch_dir))

        logger.info("Discovered %d JSONL files", len(jsonl_files))
        return jsonl_files

    def _discover_files_in_directory(self, watch_dir: Path) -> list[Path]:
        """Discover JSONL files in a specific directory.

        Args:
            watch_dir: Directory to search

        Returns:
            List of JSONL file paths in the directory

        """
        if not watch_dir.exists():
            logger.warning("Watch directory does not exist: %s", watch_dir)
            return []

        return self._scan_directory_for_jsonl_files(watch_dir)

    def _scan_directory_for_jsonl_files(self, watch_dir: Path) -> list[Path]:
        """Scan directory for JSONL files.

        Args:
            watch_dir: Directory to scan

        Returns:
            List of valid JSONL files

        """
        try:
            return [
                file_path
                for file_path in watch_dir.rglob("*.jsonl")
                if self._is_valid_jsonl_file(file_path)
            ]
        except (OSError, PermissionError):
            logger.exception("Error discovering files in %s", watch_dir)
            return []

    def _is_valid_jsonl_file(self, file_path: Path) -> bool:
        """Check if a file is a valid JSONL file to monitor.

        Args:
            file_path: Path to check

        Returns:
            True if file should be monitored

        """
        if not file_path.is_file():
            return False

        if self._is_file_too_old(file_path):
            logger.debug("Skipping old file: %s", file_path)
            return False

        return True

    def _is_file_too_old(self, file_path: Path) -> bool:
        """Check if file is older than the age limit.

        Args:
            file_path: Path to check

        Returns:
            True if file is too old

        """
        try:
            file_mtime = file_path.stat().st_mtime
            age_limit_seconds = self.file_age_limit_hours * 3600
            return (time.time() - file_mtime) > age_limit_seconds
        except (OSError, ValueError):
            return False

    def add_file(self, file_path: Path) -> None:
        """Add a file to monitoring.

        Args:
            file_path: Path to the file to monitor

        """
        with self.file_states_lock:
            if file_path not in self.file_states:
                file_state = FileState(file_path)
                file_state.update_stats()
                self.file_states[file_path] = file_state
                self.stats["files_monitored"] = len(self.file_states)
                logger.debug("Added file to monitoring: %s", file_path)

    def remove_file(self, file_path: Path) -> None:
        """Remove a file from monitoring.

        Args:
            file_path: Path to the file to remove

        """
        with self.file_states_lock:
            if file_path in self.file_states:
                del self.file_states[file_path]
                self.stats["files_monitored"] = len(self.file_states)
                logger.debug("Removed file from monitoring: %s", file_path)

    def is_monitored(self, file_path: Path) -> bool:
        """Check if a file is being monitored.

        Args:
            file_path: Path to check

        Returns:
            True if file is monitored

        """
        with self.file_states_lock:
            return file_path in self.file_states

    def process_file_changes(self, file_path: Path) -> None:
        """Process new changes in a file.

        Args:
            file_path: Path to the file to process

        """
        file_state = self._get_file_state(file_path)
        if not file_state or not self._validate_file_exists(file_path):
            return

        try:
            self._process_file_content_changes(file_path, file_state)
        except (OSError, ValueError, TypeError):
            logger.exception(
                "Specific error processing file changes for %s",
                file_path,
            )
            self._handle_file_processing_error(file_path)
        except Exception:
            logger.exception(
                "Unexpected error processing file changes for %s",
                file_path,
            )
            self._handle_file_processing_error(file_path)

    def _process_file_content_changes(
        self,
        file_path: Path,
        file_state: FileState,
    ) -> None:
        """Process content changes in a file.

        Args:
            file_path: Path to the file
            file_state: Current file state

        """
        new_content, new_position = self._read_new_content(
            file_path,
            file_state,
        )
        if not new_content:
            return

        messages_count = self._process_new_content(new_content, file_path)

        # Update file position and stats
        file_state.update_position(new_position)
        file_state.update_stats()

        self._log_processing_result(messages_count, file_path)

    def _handle_file_processing_error(self, file_path: Path) -> None:
        """Handle errors during file processing.

        Args:
            file_path: Path to the file that failed

        """
        logger.exception("Error processing file changes for %s", file_path)
        errors_encountered = self.stats.get("errors_encountered", 0)
        if isinstance(errors_encountered, int):
            self.stats["errors_encountered"] = errors_encountered + 1
        self._call_error_callbacks(
            Exception("File processing failed"),
            file_path,
        )

    def _log_processing_result(
        self,
        messages_count: int,
        file_path: Path,
    ) -> None:
        """Log the result of file processing.

        Args:
            messages_count: Number of messages processed
            file_path: Path to the processed file

        """
        if messages_count > 0:
            logger.debug(
                "Processed %d new messages from %s",
                messages_count,
                file_path,
            )

    def _get_file_state(self, file_path: Path) -> FileState | None:
        """Get file state for a path.

        Args:
            file_path: File path to get state for

        Returns:
            FileState or None if not monitored

        """
        with self.file_states_lock:
            file_state = self.file_states.get(file_path)

        if not file_state:
            logger.warning("File not in monitoring state: %s", file_path)

        return file_state

    def _validate_file_exists(self, file_path: Path) -> bool:
        """Validate that file still exists.

        Args:
            file_path: File path to validate

        Returns:
            True if file exists

        """
        if not file_path.exists():
            logger.info("File no longer exists: %s", file_path)
            self.remove_file(file_path)
            return False
        return True

    def _read_new_content(
        self,
        file_path: Path,
        file_state: FileState,
    ) -> tuple[str, int]:
        """Read new content from file.

        Args:
            file_path: Path to file
            file_state: Current file state

        Returns:
            Tuple of (new_content, new_position)

        """
        current_size = file_path.stat().st_size

        # Skip if file hasn't grown
        if current_size <= file_state.last_position:
            return "", file_state.last_position

        # Read new content from last position
        with file_path.open(encoding="utf-8") as f:
            f.seek(file_state.last_position)
            new_content = f.read()
            new_position = f.tell()

        return new_content, new_position

    def _process_new_content(self, new_content: str, file_path: Path) -> int:
        """Process new content and call callbacks.

        Args:
            new_content: New file content to process
            file_path: Source file path

        Returns:
            Number of messages processed

        """
        messages_count = 0
        for entry in self.parser.feed_data(new_content):
            messages_count += 1
            messages_processed = self.stats.get("messages_processed", 0)
            if isinstance(messages_processed, int):
                self.stats["messages_processed"] = messages_processed + 1

            # Call message callbacks
            self._call_message_callbacks(entry, file_path)

        return messages_count

    def _call_message_callbacks(
        self,
        entry: JSONLEntry,
        file_path: Path,
    ) -> None:
        """Call message callbacks safely.

        Args:
            entry: JSONL entry
            file_path: Source file path

        """
        for callback in self.message_callbacks:
            try:
                callback(entry, file_path)
            except Exception:
                logger.exception("Error in message callback")

    def _call_error_callbacks(self, error: Exception, file_path: Path) -> None:
        """Call error callbacks safely.

        Args:
            error: Exception that occurred
            file_path: Source file path

        """
        for callback in self.error_callbacks:
            try:
                callback(error, file_path)
            except Exception:
                logger.exception("Error in error callback")

    def start(self) -> None:
        """Start the file monitoring system."""
        if self._is_running:
            logger.warning("File monitor is already running")
            return

        logger.info("Starting file monitor...")

        try:
            self._discover_and_add_files()
            self._setup_observer()
            self._schedule_watching()
            self._start_observer()

            logger.info("File monitor started successfully")

        except Exception as e:
            logger.exception("Failed to start file monitor")
            self.stop()
            error_msg = f"Failed to start monitoring: {e}"
            raise FileMonitorError(error_msg) from e

    def _discover_and_add_files(self) -> None:
        """Discover and add existing files to monitoring."""
        existing_files = self.discover_jsonl_files()
        for file_path in existing_files:
            self.add_file(file_path)

    def _setup_observer(self) -> None:
        """Set up the file system observer."""
        if self.use_polling:
            self.observer = PollingObserver()
            logger.info("Using polling observer")
        else:
            try:
                self.observer = Observer()
                logger.info("Using native observer")
            except (OSError, ImportError, RuntimeError):
                logger.warning(
                    "Native observer failed, using polling",
                    exc_info=True,
                )
                self.observer = PollingObserver()

        # Create handler
        self.handler = DebouncedJSONLHandler(self, self.debounce_seconds)

    def _schedule_watching(self) -> None:
        """Schedule watching for each directory."""
        if not self.observer:
            msg = "Observer not initialized"
            raise FileMonitorError(msg)

        for watch_dir in self.watch_directories:
            if watch_dir.exists() and self.handler is not None:
                self.observer.schedule(
                    self.handler,
                    str(watch_dir),
                    recursive=True,
                )
                logger.info("Watching directory: %s", watch_dir)
            else:
                logger.warning(
                    "Watch directory does not exist: %s",
                    watch_dir,
                )

    def _start_observer(self) -> None:
        """Start the observer and update state."""
        if not self.observer:
            msg = "Observer not initialized"
            raise FileMonitorError(msg)

        self.observer.start()
        self._is_running = True
        self.stats["start_time"] = time.time()

    def stop(self) -> None:
        """Stop the file monitoring system."""
        if not self._is_running:
            return

        logger.info("Stopping file monitor...")

        try:
            # Signal shutdown
            self._shutdown_event.set()

            # Stop observer
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5.0)
                self.observer = None

            # Cleanup handler
            if self.handler:
                self.handler.cleanup()
                self.handler = None

            self._is_running = False
            logger.info("File monitor stopped")

        except Exception:
            logger.exception("Error stopping file monitor")

    def is_running(self) -> bool:
        """Check if the monitor is running.

        Returns:
            True if monitoring is active

        """
        return self._is_running

    def get_statistics(self) -> dict[str, Any]:
        """Get monitoring statistics.

        Returns:
            Dictionary containing statistics

        """
        stats = self.stats.copy()
        if stats["start_time"]:
            stats["uptime_seconds"] = time.time() - stats["start_time"]
        else:
            stats["uptime_seconds"] = 0
        return stats

    def get_monitored_files(self) -> list[Path]:
        """Get list of currently monitored files.

        Returns:
            List of monitored file paths

        """
        with self.file_states_lock:
            return list(self.file_states.keys())

    def health_check(self) -> dict[str, Any]:
        """Perform health check on the monitoring system.

        Returns:
            Health status information

        """
        health: dict[str, Any] = {
            "is_running": self.is_running(),
            "observer_alive": False,
            "files_monitored": 0,
            "directories_watched": len(self.watch_directories),
            "last_activity": None,
            "errors": [],
        }

        try:
            if self.observer:
                health["observer_alive"] = self.observer.is_alive()

            with self.file_states_lock:
                health["files_monitored"] = len(self.file_states)

                # Check for inactive files
                inactive_files = [
                    str(path)
                    for path, state in self.file_states.items()
                    if not state.is_active
                ]
                if inactive_files:
                    health["errors"].append(
                        f"Inactive files: {inactive_files}",
                    )

        except (OSError, AttributeError, KeyError, ValueError) as e:
            health["errors"].append(f"Health check error: {e}")

        return health


# Async wrapper for file monitoring
class AsyncFileMonitor:
    """Async wrapper for the FileMonitor class."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize async wrapper.

        Args:
            *args: Arguments passed to FileMonitor
            **kwargs: Keyword arguments passed to FileMonitor

        """
        self.monitor = FileMonitor(*args, **kwargs)
        self._message_queue: asyncio.Queue[tuple[JSONLEntry, Path]] = (
            asyncio.Queue()
        )
        self._error_queue: asyncio.Queue[tuple[Exception, Path]] = (
            asyncio.Queue()
        )

        # Add callbacks to feed queues
        self.monitor.add_message_callback(self._queue_message)
        self.monitor.add_error_callback(self._queue_error)

    def _queue_message(self, entry: JSONLEntry, file_path: Path) -> None:
        """Queue a new message.

        Args:
            entry: JSONL entry
            file_path: Source file path

        """
        try:
            self._message_queue.put_nowait((entry, file_path))
        except asyncio.QueueFull:
            logger.warning("Message queue full, dropping message")

    def _queue_error(self, error: Exception, file_path: Path) -> None:
        """Queue an error.

        Args:
            error: Exception that occurred
            file_path: Source file path

        """
        try:
            self._error_queue.put_nowait((error, file_path))
        except asyncio.QueueFull:
            logger.warning("Error queue full, dropping error")

    async def start(self) -> None:
        """Start monitoring in a thread."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.monitor.start)

    async def stop(self) -> None:
        """Stop monitoring."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.monitor.stop)

    async def get_message(self) -> tuple[JSONLEntry, Path]:
        """Get the next message.

        Returns:
            Tuple of (entry, file_path)

        """
        return await self._message_queue.get()

    async def get_error(self) -> tuple[Exception, Path]:
        """Get the next error.

        Returns:
            Tuple of (error, file_path)

        """
        return await self._error_queue.get()

    def __getattr__(self, name: str) -> Any:  # noqa: ANN401
        """Delegate attribute access to the underlying monitor."""
        return getattr(self.monitor, name)


# Convenience functions
def create_file_monitor(
    watch_directories: list[str | Path] | None = None,
    **kwargs: Any,  # noqa: ANN401
) -> FileMonitor:
    """Create a file monitor with default settings.

    Args:
        watch_directories: Directories to monitor
        **kwargs: Additional arguments for FileMonitor

    Returns:
        Configured FileMonitor instance

    """
    return FileMonitor(watch_directories=watch_directories, **kwargs)


def create_async_file_monitor(
    watch_directories: list[str | Path] | None = None,
    **kwargs: Any,  # noqa: ANN401
) -> AsyncFileMonitor:
    """Create an async file monitor with default settings.

    Args:
        watch_directories: Directories to monitor
        **kwargs: Additional arguments for FileMonitor

    Returns:
        Configured AsyncFileMonitor instance

    """
    return AsyncFileMonitor(watch_directories=watch_directories, **kwargs)
