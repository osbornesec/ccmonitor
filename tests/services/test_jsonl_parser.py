"""Comprehensive tests for JSONL parser functionality."""

import json
import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from src.services.jsonl_parser import (
    JSONLParseError,
    JSONLParser,
    StreamingJSONLParser,
    find_claude_activity_files,
    parse_jsonl_file,
    parse_multiple_jsonl_files,
)
from src.services.models import MessageType, ParseStatistics


class TestJSONLParser:
    """Test cases for JSONLParser class."""

    def test_parser_initialization(self) -> None:
        """Test parser initialization with default parameters."""
        parser = JSONLParser()

        assert not parser.skip_validation
        assert parser.max_line_length == 1_000_000
        assert parser.encoding == "utf-8"
        assert parser.file_age_limit_hours == 24
        assert isinstance(parser.statistics, ParseStatistics)

    def test_parser_initialization_with_custom_params(self) -> None:
        """Test parser initialization with custom parameters."""
        parser = JSONLParser(
            skip_validation=True,
            max_line_length=500000,
            encoding="utf-16",
            file_age_limit_hours=48,
        )

        assert parser.skip_validation
        assert parser.max_line_length == 500000
        assert parser.encoding == "utf-16"
        assert parser.file_age_limit_hours == 48

    def test_parse_valid_jsonl_line(self) -> None:
        """Test parsing a valid JSONL line."""
        parser = JSONLParser()

        line = json.dumps(
            {
                "uuid": "msg-001",
                "type": "user",
                "timestamp": "2025-08-01T10:00:00Z",
                "message": {"content": "Hello world"},
            },
        )

        entry = parser._parse_line(line, 1)

        assert entry is not None
        assert entry.uuid == "msg-001"
        assert entry.type == MessageType.USER
        assert entry.timestamp == "2025-08-01T10:00:00Z"
        assert parser.statistics.valid_entries == 1

    def test_parse_invalid_json_line(self) -> None:
        """Test parsing an invalid JSON line."""
        parser = JSONLParser()

        line = '{"uuid": "msg-001", "type": "user", "timestamp": "2025-08-01T10:00:00Z"'  # Missing closing brace

        entry = parser._parse_line(line, 1)

        assert entry is None
        assert parser.statistics.parse_errors == 1
        assert len(parser.statistics.error_details) == 1

    def test_parse_empty_line(self) -> None:
        """Test parsing empty lines."""
        parser = JSONLParser()

        entry = parser._parse_line("", 1)
        assert entry is None
        assert parser.statistics.skipped_lines == 1

        entry = parser._parse_line("   \n", 2)
        assert entry is None
        assert parser.statistics.skipped_lines == 2

    def test_parse_line_too_long(self) -> None:
        """Test parsing a line that exceeds maximum length."""
        parser = JSONLParser(max_line_length=100)

        long_line = json.dumps(
            {
                "uuid": "msg-001",
                "type": "user",
                "timestamp": "2025-08-01T10:00:00Z",
                "message": {"content": "x" * 200},  # Very long content
            },
        )

        entry = parser._parse_line(long_line, 1)

        assert entry is None
        assert parser.statistics.parse_errors == 1

    def test_parse_file_with_mixed_content(self) -> None:
        """Test parsing a file with mixed valid and invalid lines."""
        parser = JSONLParser()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False,
        ) as f:
            # Valid line
            f.write(
                json.dumps(
                    {
                        "uuid": "msg-001",
                        "type": "user",
                        "timestamp": "2025-08-01T10:00:00Z",
                        "message": {"content": "Hello"},
                    },
                )
                + "\n",
            )

            # Invalid JSON line
            f.write(
                '{"uuid": "msg-002", "type": "user"}\n',
            )  # Missing required fields

            # Empty line
            f.write("\n")

            # Another valid line
            f.write(
                json.dumps(
                    {
                        "uuid": "msg-003",
                        "type": "assistant",
                        "timestamp": "2025-08-01T10:01:00Z",
                        "message": {"content": "Hi there!"},
                    },
                )
                + "\n",
            )

            temp_file = Path(f.name)

        try:
            result = parser.parse_file(temp_file)

            assert result.file_path == str(temp_file)
            assert len(result.entries) >= 2  # At least 2 valid entries
            assert result.statistics.total_lines == 4
            assert result.statistics.valid_entries >= 2
            assert result.statistics.skipped_lines == 1  # Empty line
            assert result.statistics.success_rate > 0

        finally:
            temp_file.unlink()

    def test_parse_file_not_found(self) -> None:
        """Test parsing a non-existent file."""
        parser = JSONLParser()

        result = parser.parse_file("/nonexistent/file.jsonl")

        assert len(result.entries) == 0
        assert result.statistics.total_lines == 0
        assert len(result.statistics.error_details) == 1
        assert (
            result.statistics.error_details[0]["error_type"]
            == "file_not_found"
        )

    def test_file_age_filtering(self) -> None:
        """Test that files older than the age limit are skipped."""
        parser = JSONLParser(file_age_limit_hours=1)  # 1 hour limit

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False,
        ) as f:
            f.write(
                json.dumps(
                    {
                        "uuid": "msg-001",
                        "type": "user",
                        "timestamp": "2025-08-01T10:00:00Z",
                        "message": {"content": "Hello"},
                    },
                )
                + "\n",
            )

            temp_file = Path(f.name)

        try:
            # Modify file timestamp to be older than 1 hour
            old_time = datetime.now(UTC) - timedelta(hours=2)
            os.utime(temp_file, (old_time.timestamp(), old_time.timestamp()))

            result = parser.parse_file(temp_file)

            # File should be skipped due to age
            assert len(result.entries) == 0
            assert len(result.statistics.error_details) == 1
            assert (
                result.statistics.error_details[0]["error_type"]
                == "file_too_old"
            )

        finally:
            temp_file.unlink()

    def test_conversation_threading(self) -> None:
        """Test conversation thread building from entries."""
        parser = JSONLParser()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False,
        ) as f:
            # Session 1 entries
            f.write(
                json.dumps(
                    {
                        "uuid": "msg-001",
                        "type": "user",
                        "sessionId": "session-1",
                        "timestamp": "2025-08-01T10:00:00Z",
                        "message": {"content": "Hello"},
                    },
                )
                + "\n",
            )

            f.write(
                json.dumps(
                    {
                        "uuid": "msg-002",
                        "type": "assistant",
                        "sessionId": "session-1",
                        "parentUuid": "msg-001",
                        "timestamp": "2025-08-01T10:00:30Z",
                        "message": {"content": "Hi there!"},
                    },
                )
                + "\n",
            )

            # Session 2 entries
            f.write(
                json.dumps(
                    {
                        "uuid": "msg-003",
                        "type": "user",
                        "sessionId": "session-2",
                        "timestamp": "2025-08-01T11:00:00Z",
                        "message": {"content": "Different session"},
                    },
                )
                + "\n",
            )

            temp_file = Path(f.name)

        try:
            result = parser.parse_file(temp_file)

            assert len(result.conversations) == 2

            # Find session-1 conversation
            session1 = next(
                c for c in result.conversations if c.session_id == "session-1"
            )
            assert len(session1.messages) == 2
            assert session1.user_messages == 1
            assert session1.assistant_messages == 1

            # Find session-2 conversation
            session2 = next(
                c for c in result.conversations if c.session_id == "session-2"
            )
            assert len(session2.messages) == 1
            assert session2.user_messages == 1

        finally:
            temp_file.unlink()

    def test_message_type_statistics(self) -> None:
        """Test accurate counting of different message types."""
        parser = JSONLParser()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False,
        ) as f:
            # User message
            f.write(
                json.dumps(
                    {
                        "uuid": "msg-001",
                        "type": "user",
                        "timestamp": "2025-08-01T10:00:00Z",
                        "message": {"content": "Hello"},
                    },
                )
                + "\n",
            )

            # Assistant message
            f.write(
                json.dumps(
                    {
                        "uuid": "msg-002",
                        "type": "assistant",
                        "timestamp": "2025-08-01T10:00:30Z",
                        "message": {"content": "Hi!"},
                    },
                )
                + "\n",
            )

            # Tool call
            f.write(
                json.dumps(
                    {
                        "uuid": "msg-003",
                        "type": "tool_call",
                        "timestamp": "2025-08-01T10:01:00Z",
                        "message": {
                            "content": "",  # Required field that was missing
                            "tool": "Read",
                            "parameters": {"file_path": "test.txt"},
                        },
                    },
                )
                + "\n",
            )

            # Tool result
            f.write(
                json.dumps(
                    {
                        "uuid": "msg-004",
                        "type": "tool_use_result",
                        "timestamp": "2025-08-01T10:01:30Z",
                        "toolUseResult": {
                            "tool_name": "Read",
                            "input": {},
                            "output": "content",
                        },
                    },
                )
                + "\n",
            )

            temp_file = Path(f.name)

        try:
            result = parser.parse_file(temp_file)

            assert result.statistics.user_messages == 1
            assert result.statistics.assistant_messages == 1
            assert result.statistics.tool_calls == 1
            assert result.statistics.tool_results == 1

        finally:
            temp_file.unlink()

    def test_skip_validation_mode(self) -> None:
        """Test parser with validation skipped for performance."""
        parser = JSONLParser(skip_validation=True)

        line = json.dumps(
            {
                "uuid": "msg-001",
                "type": "user",
                "timestamp": "2025-08-01T10:00:00Z",
            },
        )

        entry = parser._parse_line(line, 1)

        assert entry is not None
        assert entry.uuid == "msg-001"
        assert parser.statistics.valid_entries == 1

    def test_multiple_file_parsing(self) -> None:
        """Test parsing multiple JSONL files at once."""
        parser = JSONLParser()

        files = []
        try:
            # Create multiple temp files
            for i in range(3):
                f = tempfile.NamedTemporaryFile(
                    mode="w", suffix=".jsonl", delete=False,
                )
                f.write(
                    json.dumps(
                        {
                            "uuid": f"msg-{i:03d}",
                            "type": "user",
                            "timestamp": f"2025-08-01T10:{i:02d}:00Z",
                            "message": {"content": f"Message {i}"},
                        },
                    )
                    + "\n",
                )
                f.close()
                files.append(Path(f.name))

            results = parser.parse_multiple_files(files)

            assert len(results) == 3
            for result in results:
                assert len(result.entries) == 1
                assert result.statistics.valid_entries == 1

        finally:
            for f in files:
                f.unlink()


class TestStreamingJSONLParser:
    """Test cases for StreamingJSONLParser class."""

    def test_streaming_parser_initialization(self) -> None:
        """Test streaming parser initialization."""
        parser = StreamingJSONLParser(buffer_size=4096)

        assert parser.buffer_size == 4096
        assert parser._buffer == ""
        assert parser._line_number == 0

    def test_feed_complete_lines(self) -> None:
        """Test feeding complete JSONL lines to streaming parser."""
        parser = StreamingJSONLParser()

        data = (
            json.dumps(
                {
                    "uuid": "msg-001",
                    "type": "user",
                    "timestamp": "2025-08-01T10:00:00Z",
                    "message": {"content": "Hello"},
                },
            )
            + "\n"
            + json.dumps(
                {
                    "uuid": "msg-002",
                    "type": "assistant",
                    "timestamp": "2025-08-01T10:00:30Z",
                    "message": {"content": "Hi!"},
                },
            )
            + "\n"
        )

        entries = list(parser.feed_data(data))

        assert len(entries) == 2
        assert entries[0].uuid == "msg-001"
        assert entries[1].uuid == "msg-002"

    def test_feed_partial_lines(self) -> None:
        """Test feeding partial JSONL lines to streaming parser."""
        parser = StreamingJSONLParser()

        line = (
            json.dumps(
                {
                    "uuid": "msg-001",
                    "type": "user",
                    "timestamp": "2025-08-01T10:00:00Z",
                    "message": {"content": "Hello"},
                },
            )
            + "\n"
        )

        # Feed line in chunks
        chunk1 = line[: len(line) // 2]
        chunk2 = line[len(line) // 2 :]

        entries1 = list(parser.feed_data(chunk1))
        assert len(entries1) == 0  # No complete lines yet

        entries2 = list(parser.feed_data(chunk2))
        assert len(entries2) == 1
        assert entries2[0].uuid == "msg-001"

    def test_finalize_remaining_buffer(self) -> None:
        """Test finalizing any remaining data in buffer."""
        parser = StreamingJSONLParser()

        # Feed data without newline
        data = json.dumps(
            {
                "uuid": "msg-001",
                "type": "user",
                "timestamp": "2025-08-01T10:00:00Z",
                "message": {"content": "Hello"},
            },
        )

        entries1 = list(parser.feed_data(data))
        assert len(entries1) == 0

        entries2 = list(parser.finalize())
        assert len(entries2) == 1
        assert entries2[0].uuid == "msg-001"


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    def test_parse_jsonl_file_function(self) -> None:
        """Test parse_jsonl_file convenience function."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False,
        ) as f:
            f.write(
                json.dumps(
                    {
                        "uuid": "msg-001",
                        "type": "user",
                        "timestamp": "2025-08-01T10:00:00Z",
                        "message": {"content": "Hello"},
                    },
                )
                + "\n",
            )

            temp_file = Path(f.name)

        try:
            result = parse_jsonl_file(temp_file)

            assert len(result.entries) == 1
            assert result.entries[0].uuid == "msg-001"
            assert result.statistics.valid_entries == 1

        finally:
            temp_file.unlink()

    def test_parse_multiple_jsonl_files_function(self) -> None:
        """Test parse_multiple_jsonl_files convenience function."""
        files = []

        try:
            for i in range(2):
                f = tempfile.NamedTemporaryFile(
                    mode="w", suffix=".jsonl", delete=False,
                )
                f.write(
                    json.dumps(
                        {
                            "uuid": f"msg-{i:03d}",
                            "type": "user",
                            "timestamp": f"2025-08-01T10:{i:02d}:00Z",
                            "message": {"content": f"Message {i}"},
                        },
                    )
                    + "\n",
                )
                f.close()
                files.append(Path(f.name))

            results = parse_multiple_jsonl_files(files)

            assert len(results) == 2
            for i, result in enumerate(results):
                assert len(result.entries) == 1
                assert result.entries[0].uuid == f"msg-{i:03d}"

        finally:
            for f in files:
                f.unlink()

    def test_find_claude_activity_files(self) -> None:
        """Test finding Claude activity files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create mock directory structure
            projects_dir = temp_path / "projects"
            projects_dir.mkdir()

            # Create some JSONL files
            (projects_dir / "project1.jsonl").write_text('{"test": true}\n')
            (projects_dir / "project2.jsonl").write_text('{"test": true}\n')
            (projects_dir / "not_jsonl.txt").write_text("not a jsonl file\n")

            # Create subdirectory with JSONL files
            sub_dir = projects_dir / "subdir"
            sub_dir.mkdir()
            (sub_dir / "project3.jsonl").write_text('{"test": true}\n')

            files = find_claude_activity_files(projects_dir)

            # Should find 3 JSONL files, sorted by name
            assert len(files) == 3
            assert all(f.suffix == ".jsonl" for f in files)
            assert files == sorted(files)  # Should be sorted


class TestJSONLParseError:
    """Test cases for JSONLParseError class."""

    def test_parse_error_initialization(self) -> None:
        """Test JSONLParseError initialization."""
        error = JSONLParseError("Test error", 42, "raw line content")

        assert str(error) == "Line 42: Test error"
        assert error.message == "Test error"
        assert error.line_number == 42
        assert error.raw_line == "raw line content"

    def test_parse_error_without_raw_line(self) -> None:
        """Test JSONLParseError without raw line content."""
        error = JSONLParseError("Test error", 42)

        assert str(error) == "Line 42: Test error"
        assert error.raw_line is None


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_malformed_unicode(self) -> None:
        """Test handling of malformed Unicode in JSONL files."""
        parser = JSONLParser()

        # Test with invalid UTF-8 bytes
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".jsonl", delete=False,
        ) as f:
            f.write(b'{"uuid": "msg-001", "type": "user"}\n')
            f.write(b"\xff\xfe\x00\x00")  # Invalid UTF-8 sequence
            temp_file = Path(f.name)

        try:
            result = parser.parse_file(temp_file)

            # Should handle encoding error gracefully
            assert len(result.statistics.error_details) >= 1
            error_types = [
                e["error_type"] for e in result.statistics.error_details
            ]
            assert "encoding_error" in error_types

        finally:
            temp_file.unlink()

    def test_very_large_file(self) -> None:
        """Test parsing a file with many entries."""
        parser = JSONLParser()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False,
        ) as f:
            # Generate 1000 entries
            for i in range(1000):
                entry = {
                    "uuid": f"msg-{i:04d}",
                    "type": "user",
                    "timestamp": f"2025-08-01T{i//60:02d}:{i%60:02d}:00Z",
                    "message": {"content": f"Message {i}"},
                }
                f.write(json.dumps(entry) + "\n")

            temp_file = Path(f.name)

        try:
            result = parser.parse_file(temp_file)

            assert len(result.entries) == 1000
            assert result.statistics.valid_entries == 1000
            assert result.statistics.total_lines == 1000
            assert result.statistics.success_rate == 100.0

        finally:
            temp_file.unlink()

    def test_timestamp_parsing_edge_cases(self) -> None:
        """Test various timestamp formats."""
        parser = JSONLParser()

        timestamps = [
            "2025-08-01T10:00:00Z",
            "2025-08-01T10:00:00.123Z",
            "2025-08-01T10:00:00.123456Z",
            "2025-08-01T10:00:00+00:00",
            "2025-08-01T10:00:00-05:00",
            "2025-08-01T10:00:00",
            "invalid-timestamp",
        ]

        valid_count = 0
        for i, timestamp in enumerate(timestamps):
            line = json.dumps(
                {
                    "uuid": f"msg-{i:03d}",
                    "type": "user",
                    "timestamp": timestamp,
                    "message": {"content": "Hello"},
                },
            )

            entry = parser._parse_line(line, i + 1)
            if entry is not None:
                valid_count += 1

        # Most timestamps should be valid (even invalid ones are accepted as strings)
        assert valid_count >= len(timestamps) - 1
