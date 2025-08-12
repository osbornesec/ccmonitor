"""High-performance JSONL parser for Claude Code activity logs."""

import json
import time
from collections.abc import AsyncIterator, Iterator
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, TextIO

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
        """String representation of the error."""
        return f"Line {self.line_number}: {self.message}"


class JSONLParser:
    """High-performance JSONL parser with error recovery and streaming support."""

    def __init__(
        self,
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
                return True

            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            age_limit = datetime.now() - timedelta(
                hours=self.file_age_limit_hours,
            )

            return file_mtime < age_limit

        except (OSError, ValueError):
            # If we can't determine file age, don't skip it
            return False

    def _parse_line(self, line: str, line_number: int) -> JSONLEntry | None:
        """Parse a single JSONL line.

        Args:
            line: Raw line content
            line_number: Line number for error reporting

        Returns:
            Parsed JSONLEntry or None if parsing failed

        """
        # Skip empty lines
        line = line.strip()
        if not line:
            self.statistics.skipped_lines += 1
            return None

        # Check line length
        if len(line) > self.max_line_length:
            self.statistics.parse_errors += 1
            self.statistics.add_error(
                line_number,
                "line_too_long",
                f"Line exceeds maximum length of {self.max_line_length}",
                line,
            )
            return None

        try:
            # Parse JSON
            raw_data = json.loads(line)

            if not isinstance(raw_data, dict):
                self.statistics.parse_errors += 1
                self.statistics.add_error(
                    line_number,
                    "invalid_json_structure",
                    "Expected JSON object, got " + type(raw_data).__name__,
                    line,
                )
                return None

            # Convert to JSONLEntry
            if self.skip_validation:
                # Basic validation without Pydantic
                entry = self._create_entry_basic(raw_data)
            else:
                entry = JSONLEntry.parse_obj(raw_data)

            # Update type-specific statistics
            self._update_type_statistics(entry.type)

            self.statistics.valid_entries += 1
            return entry

        except json.JSONDecodeError as e:
            self.statistics.parse_errors += 1
            self.statistics.add_error(
                line_number,
                "json_decode_error",
                str(e),
                line,
            )
            return None

        except Exception as e:
            self.statistics.validation_errors += 1
            self.statistics.add_error(
                line_number,
                "validation_error",
                str(e),
                line,
            )
            return None

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

    def parse_file(self, file_path: str | Path) -> ParseResult:
        """Parse a complete JSONL file.

        Args:
            file_path: Path to the JSONL file

        Returns:
            ParseResult with entries, statistics, and conversations

        """
        file_path = Path(file_path)

        # Check if file should be skipped due to age
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

        start_time = time.time()
        self.reset_statistics()

        entries: list[JSONLEntry] = []

        try:
            with open(file_path, encoding=self.encoding) as f:
                for line_number, line in enumerate(f, 1):
                    self.statistics.total_lines += 1

                    entry = self._parse_line(line, line_number)
                    if entry:
                        entries.append(entry)

        except FileNotFoundError:
            self.statistics.add_error(
                0,
                "file_not_found",
                f"File not found: {file_path}",
            )
        except PermissionError:
            self.statistics.add_error(
                0,
                "permission_error",
                f"Permission denied: {file_path}",
            )
        except UnicodeDecodeError as e:
            self.statistics.add_error(
                0,
                "encoding_error",
                f"Encoding error: {e}",
            )

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
        line_number = 0

        for line in stream:
            line_number += 1
            self.statistics.total_lines += 1

            entry = self._parse_line(line, line_number)
            if entry:
                yield entry

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
        import asyncio

        file_path = Path(file_path)

        # Check if file should be skipped due to age
        if self._is_file_too_old(file_path):
            return

        try:
            with open(file_path, encoding=self.encoding) as f:
                line_number = 0

                for line in f:
                    line_number += 1
                    self.statistics.total_lines += 1

                    entry = self._parse_line(line, line_number)
                    if entry:
                        yield entry

                    # Yield control periodically for async processing
                    if line_number % 100 == 0:
                        await asyncio.sleep(0)

        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            self.statistics.add_error(0, type(e).__name__, str(e))

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
        sessions: dict[str, list[JSONLEntry]] = {}

        for entry in entries:
            session_id = entry.session_id or "default"
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(entry)

        conversations = []

        for session_id, session_entries in sessions.items():
            if not session_entries:
                continue

            # Sort by timestamp
            try:
                session_entries.sort(
                    key=lambda e: (
                        datetime.fromisoformat(
                            e.timestamp.replace("Z", "+00:00"),
                        )
                        if e.timestamp
                        else datetime.min
                    ),
                )
            except (ValueError, AttributeError):
                # If timestamp parsing fails, use original order
                pass

            # Calculate statistics
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
                if e.type
                in [MessageType.TOOL_RESULT, MessageType.TOOL_USE_RESULT]
            )

            # Determine start and end times
            start_time = datetime.now()
            end_time = None

            try:
                timestamps = [
                    (
                        datetime.fromisoformat(
                            e.timestamp.replace("Z", "+00:00"),
                        )
                        if e.timestamp
                        else datetime.min
                    )
                    for e in session_entries
                    if e.timestamp
                ]
                if timestamps:
                    start_time = min(timestamps)
                    end_time = max(timestamps)
            except (ValueError, AttributeError):
                pass

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
            except Exception as e:
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

    def __init__(self, buffer_size: int = 8192, **kwargs: Any) -> None:
        """Initialize streaming parser.

        Args:
            buffer_size: Buffer size for streaming
            **kwargs: Arguments passed to JSONLParser

        """
        super().__init__(**kwargs)
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

    jsonl_files = []

    # Search recursively for JSONL files
    for file_path in claude_dir.rglob(file_pattern):
        if file_path.is_file():
            jsonl_files.append(file_path)

    return sorted(jsonl_files)
