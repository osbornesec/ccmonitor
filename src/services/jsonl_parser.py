"""High-performance JSONL parser for Claude Code activity logs."""

import asyncio
import contextlib
import json
import time
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import TextIO

from .models import (
    ConversationThread,
    JSONLEntry,
    MessageType,
    ParseResult,
    ParseStatistics,
)


class JSONLParseError(Exception):
    """Custom exception for JSONL parsing errors."""

    def __init__(
        self,
        message: str,
        line_number: int,
        raw_line: str | None = None,
    ) -> None:
        """Initialize parse error.

        Args:
            message: Error message
            line_number: Line number where error occurred
            raw_line: Raw line content that caused the error

        """
        super().__init__(message)
        self.message = message
        self.line_number = line_number
        self.raw_line = raw_line

    def __str__(self) -> str:
        """Return string representation of the error."""
        return f"Line {self.line_number}: {self.message}"


class JSONLParser:
    """High-performance JSONL parser with error recovery and streaming support."""

    def __init__(
        self,
        *,
        skip_validation: bool = False,
        max_line_length: int = 1_000_000,
        encoding: str = "utf-8",
        file_age_limit_hours: int = 24,
    ) -> None:
        """Initialize the JSONL parser.

        Args:
            skip_validation: Skip Pydantic validation for speed
            max_line_length: Maximum line length to process
            encoding: File encoding
            file_age_limit_hours: Skip files older than this many hours

        """
        self.skip_validation = skip_validation
        self.max_line_length = max_line_length
        self.encoding = encoding
        self.file_age_limit_hours = file_age_limit_hours

        # Statistics tracking
        self.reset_statistics()

    def reset_statistics(self) -> None:
        """Reset parsing statistics."""
        self.statistics = ParseStatistics()

    def _is_file_too_old(self, file_path: str | Path) -> bool:
        """Check if file is older than the configured limit.

        Args:
            file_path: Path to the file to check

        Returns:
            True if file is too old and should be skipped

        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return False  # Let file processing handle missing files

            file_mtime = datetime.fromtimestamp(
                file_path.stat().st_mtime,
                tz=UTC,
            )
            age_limit = datetime.now(tz=UTC) - timedelta(
                hours=self.file_age_limit_hours,
            )
        except (OSError, ValueError):
            return False
        else:
            return file_mtime < age_limit

    def _check_line_validity(self, line: str, line_number: int) -> str | None:
        """Check if line is valid for processing.

        Args:
            line: Raw line content
            line_number: Line number for error reporting

        Returns:
            Stripped line if valid, None if should be skipped

        """
        line = line.strip()
        if not line:
            self.statistics.skipped_lines += 1
            return None

        if len(line) > self.max_line_length:
            self.statistics.parse_errors += 1
            self.statistics.add_error(
                line_number,
                "line_too_long",
                f"Line exceeds maximum length of {self.max_line_length}",
                line,
            )
            return None

        return line

    def _parse_json_data(self, line: str, line_number: int) -> dict | None:
        """Parse JSON data from line.

        Args:
            line: JSON line to parse
            line_number: Line number for error reporting

        Returns:
            Parsed dict or None if parsing failed

        """
        try:
            raw_data = json.loads(line)
        except json.JSONDecodeError as e:
            self.statistics.parse_errors += 1
            self.statistics.add_error(
                line_number,
                "json_decode_error",
                str(e),
                line,
            )
            return None

        if not isinstance(raw_data, dict):
            self.statistics.parse_errors += 1
            self.statistics.add_error(
                line_number,
                "invalid_json_structure",
                "Expected JSON object, got " + type(raw_data).__name__,
                line,
            )
            return None

        return raw_data

    def _create_entry_from_data(
        self,
        raw_data: dict,
        line: str,
        line_number: int,
    ) -> JSONLEntry | None:
        """Create JSONLEntry from parsed data.

        Args:
            raw_data: Parsed JSON data
            line: Original line for error reporting
            line_number: Line number for error reporting

        Returns:
            JSONLEntry or None if creation failed

        """
        try:
            if self.skip_validation:
                entry = self._create_entry_basic(raw_data)
            else:
                entry = JSONLEntry.parse_obj(raw_data)
        except (ValueError, TypeError) as e:
            self.statistics.validation_errors += 1
            self.statistics.add_error(
                line_number,
                "validation_error",
                str(e),
                line,
            )
            return None

        return entry

    def _parse_line(self, line: str, line_number: int) -> JSONLEntry | None:
        """Parse a single JSONL line.

        Args:
            line: Raw line content
            line_number: Line number for error reporting

        Returns:
            Parsed JSONLEntry or None if parsing failed

        """
        # Check line validity
        clean_line = self._check_line_validity(line, line_number)
        if clean_line is None:
            return None

        # Parse JSON data
        raw_data = self._parse_json_data(clean_line, line_number)
        if raw_data is None:
            return None

        # Create entry from data
        entry = self._create_entry_from_data(raw_data, clean_line, line_number)
        if entry is None:
            return None

        # Update statistics and return
        self._update_type_statistics(entry.type)
        self.statistics.valid_entries += 1
        return entry

    def _create_entry_basic(self, raw_data: dict) -> JSONLEntry:
        """Create JSONLEntry with basic validation (no Pydantic).

        Args:
            raw_data: Raw dictionary data

        Returns:
            JSONLEntry instance

        """
        # Extract required fields with defaults
        entry_data = {
            "uuid": raw_data.get("uuid", ""),
            "type": raw_data.get("type", "user"),
            "timestamp": raw_data.get("timestamp", ""),
            "session_id": raw_data.get("sessionId"),
            "parent_uuid": raw_data.get("parentUuid"),
            "message": raw_data.get("message"),
            "tool_use_result": raw_data.get("toolUseResult"),
            "cwd": raw_data.get("cwd"),
            "git_branch": raw_data.get("gitBranch"),
            "version": raw_data.get("version"),
            "is_meta": raw_data.get("isMeta"),
            "tool_use_id": raw_data.get("toolUseID"),
        }

        # Create entry directly without validation
        return JSONLEntry(
            **{k: v for k, v in entry_data.items() if v is not None},
        )

    def _update_type_statistics(
        self,
        message_type: str | MessageType,
    ) -> None:
        """Update statistics based on message type.

        Args:
            message_type: The message type to count

        """
        if isinstance(message_type, str):
            try:
                message_type = MessageType(message_type)
            except ValueError:
                return

        type_mapping = {
            MessageType.USER: "user_messages",
            MessageType.ASSISTANT: "assistant_messages",
            MessageType.TOOL_CALL: "tool_calls",
            MessageType.TOOL_USE: "tool_calls",
            MessageType.TOOL_RESULT: "tool_results",
            MessageType.TOOL_USE_RESULT: "tool_results",
            MessageType.SYSTEM: "system_messages",
            MessageType.HOOK: "hook_messages",
            MessageType.META: "system_messages",
        }

        attr_name = type_mapping.get(message_type)
        if attr_name:
            current_value = getattr(self.statistics, attr_name, 0)
            setattr(self.statistics, attr_name, current_value + 1)

    def _handle_file_age_check(self, file_path: Path) -> ParseResult | None:
        """Handle file age checking and return early result if needed.

        Args:
            file_path: Path to check

        Returns:
            ParseResult if file is too old, None if should continue processing

        """
        if self._is_file_too_old(file_path):
            empty_result = ParseResult(
                entries=[],
                statistics=ParseStatistics(),
                conversations=[],
                file_path=str(file_path),
            )
            empty_result.statistics.add_error(
                0,
                "file_too_old",
                f"File is older than {self.file_age_limit_hours} hours",
            )
            return empty_result
        return None

    def _process_file_lines(self, file_path: Path) -> list[JSONLEntry]:
        """Process all lines in a file and return parsed entries.

        Args:
            file_path: Path to the file to process

        Returns:
            List of successfully parsed entries

        """
        entries: list[JSONLEntry] = []

        try:
            entries = self._read_file_lines(file_path)
        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            self._handle_file_processing_error(e, file_path)

        return entries

    def _read_file_lines(self, file_path: Path) -> list[JSONLEntry]:
        """Read and parse all lines from a file.

        Args:
            file_path: Path to the file to read

        Returns:
            List of successfully parsed entries


        """
        entries: list[JSONLEntry] = []

        with file_path.open(encoding=self.encoding) as f:
            for line_number, line in enumerate(f, 1):
                self.statistics.total_lines += 1

                entry = self._parse_line(line, line_number)
                if entry:
                    entries.append(entry)

        return entries

    def _handle_file_processing_error(
        self,
        error: Exception,
        file_path: Path,
    ) -> None:
        """Handle file processing errors and add to statistics.

        Args:
            error: The exception that occurred
            file_path: Path to the file being processed


        """
        if isinstance(error, FileNotFoundError):
            self.statistics.add_error(
                0,
                "file_not_found",
                f"File not found: {file_path}",
            )
        elif isinstance(error, PermissionError):
            self.statistics.add_error(
                0,
                "permission_error",
                f"Permission denied: {file_path}",
            )
        elif isinstance(error, UnicodeDecodeError):
            self.statistics.add_error(
                0,
                "encoding_error",
                f"Encoding error: {error}",
            )

    def parse_file(self, file_path: str | Path) -> ParseResult:
        """Parse a complete JSONL file.

        Args:
            file_path: Path to the JSONL file

        Returns:
            ParseResult with entries, statistics, and conversations

        """
        file_path = Path(file_path)

        # Check if file should be skipped due to age
        age_check_result = self._handle_file_age_check(file_path)
        if age_check_result is not None:
            return age_check_result

        start_time = time.time()
        self.reset_statistics()

        # Process file lines
        entries = self._process_file_lines(file_path)

        # Calculate processing time
        self.statistics.processing_time = time.time() - start_time

        # Build conversations
        conversations = self._build_conversations(entries)

        return ParseResult(
            entries=entries,
            statistics=self.statistics,
            conversations=conversations,
            file_path=str(file_path),
        )

    def parse_stream(self, stream: TextIO) -> Iterator[JSONLEntry]:
        """Parse JSONL from a stream (for real-time processing).

        Args:
            stream: Text stream to read from

        Yields:
            JSONLEntry instances as they are parsed

        """
        for line_number, line in enumerate(stream, 1):
            self.statistics.total_lines += 1

            entry = self._parse_line(line, line_number)
            if entry:
                yield entry

    def _read_lines_chunk(
        self,
        file_obj: TextIO,
        chunk_size: int,
    ) -> list[str]:
        """Read a chunk of lines from file object.

        Args:
            file_obj: Open file object
            chunk_size: Number of lines to read

        Returns:
            List of lines read from file

        """
        lines = []
        for _ in range(chunk_size):
            line = file_obj.readline()
            if not line:
                break
            lines.append(line)
        return lines

    async def _process_chunk_async(
        self,
        lines: list[str],
        start_line_number: int,
    ) -> AsyncIterator[JSONLEntry]:
        """Process a chunk of lines asynchronously.

        Args:
            lines: List of lines to process
            start_line_number: Starting line number for this chunk

        Yields:
            JSONLEntry instances as they are parsed

        """
        for i, line in enumerate(lines, start_line_number):
            self.statistics.total_lines += 1

            entry = self._parse_line(line, i)
            if entry:
                yield entry

    async def _process_file_async(
        self,
        file_path: Path,
    ) -> AsyncIterator[JSONLEntry]:
        """Process file asynchronously with proper yielding.

        Args:
            file_path: Path to the file to process

        Yields:
            JSONLEntry instances as they are parsed

        """
        try:
            # Use asyncio thread pool for file I/O to avoid blocking
            loop = asyncio.get_running_loop()

            with file_path.open(encoding=self.encoding) as f:
                # Process in chunks to reduce memory usage
                chunk_size = 1000
                line_number = 0

                while True:
                    # Read chunk of lines in executor
                    lines = await loop.run_in_executor(
                        None,
                        self._read_lines_chunk,
                        f,
                        chunk_size,
                    )

                    if not lines:
                        break

                    # Process chunk using helper
                    async for entry in self._process_chunk_async(
                        lines,
                        line_number + 1,
                    ):
                        yield entry

                    line_number += len(lines)
                    await asyncio.sleep(0)

        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            self.statistics.add_error(0, type(e).__name__, str(e))

    async def parse_file_async(
        self,
        file_path: str | Path,
    ) -> AsyncIterator[JSONLEntry]:
        """Asynchronously parse a JSONL file.

        Args:
            file_path: Path to the JSONL file

        Yields:
            JSONLEntry instances as they are parsed

        """
        file_path = Path(file_path)

        # Check if file should be skipped due to age
        if self._is_file_too_old(file_path):
            return

        async for entry in self._process_file_async(file_path):
            yield entry

    def _group_entries_by_session(
        self,
        entries: list[JSONLEntry],
    ) -> dict[str, list[JSONLEntry]]:
        """Group entries by session ID.

        Args:
            entries: List of entries to group

        Returns:
            Dictionary mapping session IDs to entry lists

        """
        sessions: dict[str, list[JSONLEntry]] = {}

        for entry in entries:
            session_id = entry.session_id or "default"
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(entry)

        return sessions

    def _sort_session_entries(self, session_entries: list[JSONLEntry]) -> None:
        """Sort session entries by timestamp.

        Args:
            session_entries: List of entries to sort in-place

        """

        def timestamp_key(entry: JSONLEntry) -> datetime:
            if entry.timestamp:
                return datetime.fromisoformat(entry.timestamp)
            return datetime.min.replace(tzinfo=UTC)

        with contextlib.suppress(ValueError, AttributeError):
            session_entries.sort(key=timestamp_key)

    def _calculate_session_statistics(
        self,
        session_entries: list[JSONLEntry],
    ) -> tuple[int, int, int, int, int]:
        """Calculate statistics for a session.

        Args:
            session_entries: List of entries in the session

        Returns:
            Tuple of (total, user, assistant, tool_calls, tool_results)

        """
        total_messages = len(session_entries)
        user_messages = sum(
            1 for e in session_entries if e.type == MessageType.USER
        )
        assistant_messages = sum(
            1 for e in session_entries if e.type == MessageType.ASSISTANT
        )
        tool_calls = sum(
            1
            for e in session_entries
            if e.type in [MessageType.TOOL_CALL, MessageType.TOOL_USE]
        )
        tool_results = sum(
            1
            for e in session_entries
            if e.type in [MessageType.TOOL_RESULT, MessageType.TOOL_USE_RESULT]
        )

        return (
            total_messages,
            user_messages,
            assistant_messages,
            tool_calls,
            tool_results,
        )

    def _determine_session_timespan(
        self,
        session_entries: list[JSONLEntry],
    ) -> tuple[datetime, datetime | None]:
        """Determine start and end times for a session.

        Args:
            session_entries: List of entries in the session

        Returns:
            Tuple of (start_time, end_time)

        """
        start_time = datetime.now(tz=UTC)
        end_time = None

        try:
            timestamps = [
                datetime.fromisoformat(e.timestamp)
                for e in session_entries
                if e.timestamp
            ]
            if timestamps:
                start_time = min(timestamps)
                end_time = max(timestamps)
        except (ValueError, AttributeError):
            pass

        return start_time, end_time

    def _build_conversations(
        self,
        entries: list[JSONLEntry],
    ) -> list[ConversationThread]:
        """Build conversation threads from entries.

        Args:
            entries: List of parsed entries

        Returns:
            List of conversation threads

        """
        # Group entries by session_id
        sessions = self._group_entries_by_session(entries)
        conversations = []

        for session_id, session_entries in sessions.items():
            if not session_entries:
                continue

            # Sort by timestamp
            self._sort_session_entries(session_entries)

            # Calculate statistics
            stats = self._calculate_session_statistics(session_entries)
            (
                total_messages,
                user_messages,
                assistant_messages,
                tool_calls,
                tool_results,
            ) = stats

            # Determine start and end times
            start_time, end_time = self._determine_session_timespan(
                session_entries,
            )

            conversation = ConversationThread(
                session_id=session_id,
                messages=session_entries,
                start_time=start_time,
                end_time=end_time,
                total_messages=total_messages,
                user_messages=user_messages,
                assistant_messages=assistant_messages,
                tool_calls=tool_calls,
                tool_results=tool_results,
            )

            conversations.append(conversation)

        return conversations

    def parse_multiple_files(
        self,
        file_paths: list[str | Path],
    ) -> list[ParseResult]:
        """Parse multiple JSONL files.

        Args:
            file_paths: List of file paths to parse

        Returns:
            List of ParseResult instances

        """
        results = []

        for file_path in file_paths:
            try:
                result = self.parse_file(file_path)
                results.append(result)
            except (OSError, ValueError, TypeError) as e:
                # Create error result
                error_result = ParseResult(
                    entries=[],
                    statistics=ParseStatistics(),
                    conversations=[],
                    file_path=str(file_path),
                )
                error_result.statistics.add_error(
                    0,
                    "file_parse_error",
                    str(e),
                )
                results.append(error_result)

        return results


class StreamingJSONLParser(JSONLParser):
    """Streaming JSONL parser for real-time processing."""

    def __init__(
        self,
        buffer_size: int = 8192,
        *,
        skip_validation: bool = False,
        max_line_length: int = 1_000_000,
        encoding: str = "utf-8",
        file_age_limit_hours: int = 24,
    ) -> None:
        """Initialize streaming parser.

        Args:
            buffer_size: Buffer size for streaming
            skip_validation: Skip Pydantic validation for speed
            max_line_length: Maximum line length to process
            encoding: File encoding
            file_age_limit_hours: Skip files older than this many hours

        """
        super().__init__(
            skip_validation=skip_validation,
            max_line_length=max_line_length,
            encoding=encoding,
            file_age_limit_hours=file_age_limit_hours,
        )
        self.buffer_size = buffer_size
        self._buffer = ""
        self._line_number = 0

    def feed_data(self, data: str) -> Iterator[JSONLEntry]:
        """Feed data to the streaming parser.

        Args:
            data: New data chunk to process

        Yields:
            JSONLEntry instances as complete lines are parsed

        """
        self._buffer += data

        # Process complete lines
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self._line_number += 1
            self.statistics.total_lines += 1

            entry = self._parse_line(line, self._line_number)
            if entry:
                yield entry

    def finalize(self) -> Iterator[JSONLEntry]:
        """Process any remaining data in the buffer.

        Yields:
            Final JSONLEntry instances

        """
        if self._buffer.strip():
            self._line_number += 1
            self.statistics.total_lines += 1

            entry = self._parse_line(self._buffer, self._line_number)
            if entry:
                yield entry

        self._buffer = ""


# Convenience functions
def parse_jsonl_file(
    file_path: str | Path,
    *,
    skip_validation: bool = False,
    file_age_limit_hours: int = 24,
) -> ParseResult:
    """Parse a single JSONL file.

    Args:
        file_path: Path to the JSONL file
        skip_validation: Skip Pydantic validation for speed
        file_age_limit_hours: Skip files older than this many hours

    Returns:
        ParseResult with entries, statistics, and conversations

    """
    parser = JSONLParser(
        skip_validation=skip_validation,
        file_age_limit_hours=file_age_limit_hours,
    )
    return parser.parse_file(file_path)


def parse_multiple_jsonl_files(
    file_paths: list[str | Path],
    *,
    skip_validation: bool = False,
    file_age_limit_hours: int = 24,
) -> list[ParseResult]:
    """Parse multiple JSONL files.

    Args:
        file_paths: List of file paths to parse
        skip_validation: Skip Pydantic validation for speed
        file_age_limit_hours: Skip files older than this many hours

    Returns:
        List of ParseResult instances

    """
    parser = JSONLParser(
        skip_validation=skip_validation,
        file_age_limit_hours=file_age_limit_hours,
    )
    return parser.parse_multiple_files(file_paths)


def find_claude_activity_files(
    claude_projects_dir: str | Path = "~/.claude/projects",
    file_pattern: str = "*.jsonl",
) -> list[Path]:
    """Find Claude activity JSONL files.

    Args:
        claude_projects_dir: Directory containing Claude projects
        file_pattern: File pattern to match

    Returns:
        List of JSONL file paths

    """
    claude_dir = Path(claude_projects_dir).expanduser()

    if not claude_dir.exists():
        return []

    # Use list comprehension for performance
    jsonl_files = [
        file_path
        for file_path in claude_dir.rglob(file_pattern)
        if file_path.is_file()
    ]

    return sorted(jsonl_files)


@lru_cache(maxsize=128)
def get_file_metadata_cached(file_path: str) -> tuple[float, int]:
    """Get cached file metadata for performance optimization.

    Args:
        file_path: Path to the file

    Returns:
        Tuple of (modification_time, file_size)

    """
    try:
        stat = Path(file_path).stat()
    except (OSError, ValueError):
        return (0.0, 0)
    else:
        return (stat.st_mtime, stat.st_size)
