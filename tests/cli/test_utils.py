"""Test suite for CLI utility functions.

Comprehensive testing of utility functions including logging, formatting,
file operations, and validation functions.
"""

import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.cli.utils import (
    confirm_destructive_operation,
    ensure_directory,
    find_config_file,
    format_duration,
    format_size,
    get_terminal_size,
    is_jsonl_file,
    parse_size_string,
    safe_filename,
    setup_logging,
    truncate_text,
    validate_file_access,
)


class TestLoggingSetup:
    """Test suite for logging configuration."""

    def test_setup_logging_default_level(self) -> None:
        """Test logging setup with default level."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_root_logger = Mock()
            mock_urllib3_logger = Mock()
            mock_requests_logger = Mock()

            # Mock return values for specific logger names
            def get_logger_side_effect(name: str = "") -> Mock:
                if name == "urllib3":
                    return mock_urllib3_logger
                if name == "requests":
                    return mock_requests_logger
                return mock_root_logger

            mock_get_logger.side_effect = get_logger_side_effect

            setup_logging()

            mock_root_logger.setLevel.assert_called_with(logging.INFO)
            mock_root_logger.addHandler.assert_called_once()

    def test_setup_logging_debug_level(self) -> None:
        """Test logging setup with debug level."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_root_logger = Mock()
            mock_urllib3_logger = Mock()
            mock_requests_logger = Mock()

            # Mock return values for specific logger names
            def get_logger_side_effect(name: str = "") -> Mock:
                if name == "urllib3":
                    return mock_urllib3_logger
                if name == "requests":
                    return mock_requests_logger
                return mock_root_logger

            mock_get_logger.side_effect = get_logger_side_effect

            setup_logging(logging.DEBUG)

            mock_root_logger.setLevel.assert_called_with(logging.DEBUG)

    def test_setup_logging_suppresses_third_party(self) -> None:
        """Test that third-party loggers are suppressed."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_root_logger = Mock()
            mock_urllib3_logger = Mock()
            mock_requests_logger = Mock()

            def get_logger_side_effect(name: str = "") -> Mock:
                if name == "urllib3":
                    return mock_urllib3_logger
                if name == "requests":
                    return mock_requests_logger
                return mock_root_logger

            mock_get_logger.side_effect = get_logger_side_effect

            setup_logging()

            mock_urllib3_logger.setLevel.assert_called_with(logging.WARNING)
            mock_requests_logger.setLevel.assert_called_with(logging.WARNING)


class TestFormatting:
    """Test suite for formatting utilities."""

    @pytest.mark.parametrize(
        "size_bytes,expected",
        [
            (0, "0 B"),
            (1023, "1023 B"),
            (1024, "1.0 KB"),
            (1536, "1.5 KB"),
            (1048576, "1.0 MB"),
            (1073741824, "1.0 GB"),
            (1099511627776, "1.0 TB"),
        ],
    )
    def test_format_size(self, size_bytes: int, expected: str) -> None:
        """Test file size formatting."""
        result = format_size(size_bytes)
        assert result == expected

    @pytest.mark.parametrize(
        "seconds,expected",
        [
            (0.001, "0.001s"),
            (0.5, "0.500s"),
            (1.0, "1.0s"),
            (59.9, "59.9s"),
            (60, "1m 0s"),
            (90, "1m 30s"),
            (3600, "1h 0m"),
            (3660, "1h 1m"),
            (7200, "2h 0m"),
        ],
    )
    def test_format_duration(self, seconds: float, expected: str) -> None:
        """Test duration formatting."""
        result = format_duration(seconds)
        assert result == expected

    @pytest.mark.parametrize(
        "text,max_length,suffix,expected",
        [
            ("short", 10, "...", "short"),
            ("this is a long text", 10, "...", "this is..."),
            ("exact", 5, "...", "exact"),
            ("toolong", 3, "...", "..."),
            ("test", 2, "..", ".."),
        ],
    )
    def test_truncate_text(
        self,
        text: str,
        max_length: int,
        suffix: str,
        expected: str,
    ) -> None:
        """Test text truncation."""
        result = truncate_text(text, max_length, suffix)
        assert result == expected

    def test_truncate_text_default_suffix(self) -> None:
        """Test text truncation with default suffix."""
        result = truncate_text("this is too long", 10)
        assert result == "this is..."


class TestFileOperations:
    """Test suite for file operation utilities."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())

    @pytest.mark.parametrize(
        "mode,expected_function",
        [
            ("read", "os.access"),
            ("write", "os.access"),
            ("execute", "os.access"),
        ],
    )
    def test_validate_file_access_modes(
        self,
        mode: str,
        expected_function: str,
    ) -> None:
        """Test file access validation for different modes."""
        test_file = self.temp_dir / "test.txt"
        test_file.write_text("test content")

        with patch("os.access", return_value=True):
            result = validate_file_access(test_file, mode)
            assert result is True

    def test_validate_file_access_permission_error(self) -> None:
        """Test file access validation with permission error."""
        test_file = self.temp_dir / "test.txt"
        test_file.write_text("test content")

        with patch("os.access", side_effect=PermissionError()):
            result = validate_file_access(test_file, "read")
            assert result is False

    def test_validate_file_access_nonexistent_file(self) -> None:
        """Test file access validation with non-existent file."""
        nonexistent = self.temp_dir / "nonexistent.txt"

        result = validate_file_access(nonexistent, "read")
        assert result is False

    def test_ensure_directory_creates_new(self) -> None:
        """Test directory creation for new directory."""
        new_dir = self.temp_dir / "new_subdir"
        assert not new_dir.exists()

        result = ensure_directory(new_dir)
        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_existing(self) -> None:
        """Test directory creation for existing directory."""
        result = ensure_directory(self.temp_dir)
        assert result is True

    def test_ensure_directory_nested_creation(self) -> None:
        """Test creating nested directories."""
        nested_dir = self.temp_dir / "level1" / "level2" / "level3"

        result = ensure_directory(nested_dir)
        assert result is True
        assert nested_dir.exists()
        assert nested_dir.is_dir()

    def test_ensure_directory_permission_error(self) -> None:
        """Test directory creation with permission error."""
        with patch.object(Path, "mkdir", side_effect=PermissionError()):
            result = ensure_directory(self.temp_dir / "no_permission")
            assert result is False

    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("normal.txt", "normal.txt"),
            ("file with spaces.txt", "file_with_spaces.txt"),
            ("file/with/slashes.txt", "file_with_slashes.txt"),
            ("file\\with\\backslashes.txt", "file_with_backslashes.txt"),
            ("file-with_dots.txt", "file-with_dots.txt"),
            ("123numbers", "123numbers"),
            ("", "file_"),
            (".hidden", "file_.hidden"),
            ("special!@#$%chars", "special_chars"),
        ],
    )
    def test_safe_filename(self, filename: str, expected: str) -> None:
        """Test safe filename generation."""
        result = safe_filename(filename)
        assert result == expected

    def test_safe_filename_unicode(self) -> None:
        """Test safe filename with unicode characters."""
        filename = "файл.txt"
        result = safe_filename(filename)
        assert result.startswith("file_")


class TestTerminalUtilities:
    """Test suite for terminal utilities."""

    def test_get_terminal_size_normal(self) -> None:
        """Test getting terminal size normally."""
        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.return_value = Mock(columns=120, lines=30)

            width, height = get_terminal_size()
            assert width == 120
            assert height == 30

    def test_get_terminal_size_fallback(self) -> None:
        """Test terminal size fallback on error."""
        with patch("shutil.get_terminal_size", side_effect=OSError()):
            width, height = get_terminal_size()
            assert width == 80
            assert height == 24

    def test_confirm_destructive_operation_with_click(self) -> None:
        """Test confirmation dialog with click available."""
        with patch("click.confirm", return_value=True) as mock_confirm:
            result = confirm_destructive_operation("Delete files?")
            assert result is True
            mock_confirm.assert_called_once_with(
                "Delete files?",
                default=False,
            )

    def test_confirm_destructive_operation_fallback(self) -> None:
        """Test confirmation dialog without click."""
        with patch("src.cli.utils.click", None):
            with patch("builtins.input", return_value="y"):
                result = confirm_destructive_operation("Delete files?")
                assert result is True

    def test_confirm_destructive_operation_fallback_no(self) -> None:
        """Test confirmation dialog fallback with no response."""
        with patch("src.cli.utils.click", None):
            with patch("builtins.input", return_value="n"):
                result = confirm_destructive_operation("Delete files?")
                assert result is False

    def test_confirm_destructive_operation_fallback_default(self) -> None:
        """Test confirmation dialog fallback with default."""
        with patch("src.cli.utils.click", None):
            with patch("builtins.input", return_value=""):
                result = confirm_destructive_operation(
                    "Delete files?",
                    default=True,
                )
                assert result is True


class TestSizeParsing:
    """Test suite for size string parsing."""

    @pytest.mark.parametrize(
        "size_str,expected",
        [
            ("100", 100),
            ("100B", 100),
            ("1KB", 1024),
            ("1.5KB", 1536),
            ("1MB", 1024 * 1024),
            ("2.5MB", int(2.5 * 1024 * 1024)),
            ("1GB", 1024 * 1024 * 1024),
            ("1TB", 1024 * 1024 * 1024 * 1024),
        ],
    )
    def test_parse_size_string_valid(
        self,
        size_str: str,
        expected: int,
    ) -> None:
        """Test parsing valid size strings."""
        result = parse_size_string(size_str)
        assert result == expected

    @pytest.mark.parametrize(
        "size_str,expected",
        [
            ("  100 KB  ", 100 * 1024),
            ("1kb", 1024),  # lowercase
            ("1.0MB", 1024 * 1024),
        ],
    )
    def test_parse_size_string_normalization(
        self,
        size_str: str,
        expected: int,
    ) -> None:
        """Test size string normalization."""
        result = parse_size_string(size_str)
        assert result == expected

    @pytest.mark.parametrize(
        "invalid_size",
        [
            "invalid",
            "1XX",
            "not_a_number_KB",
            "",
            "1.2.3MB",
        ],
    )
    def test_parse_size_string_invalid(self, invalid_size: str) -> None:
        """Test parsing invalid size strings."""
        with pytest.raises(ValueError, match="Invalid size string"):
            parse_size_string(invalid_size)


class TestConfigurationFile:
    """Test suite for configuration file utilities."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        # Store original values
        self.original_cwd = Path.cwd()
        self.original_home = Path.home()

    def test_find_config_file_current_dir(self) -> None:
        """Test finding config file in current directory."""
        config_file = self.temp_dir / ".ccmonitor.yaml"
        config_file.write_text("test: value")

        with patch("pathlib.Path.cwd", return_value=self.temp_dir):
            result = find_config_file()
            assert result == config_file

    def test_find_config_file_home_dir(self) -> None:
        """Test finding config file in home directory."""
        config_file = self.temp_dir / ".ccmonitor.yml"
        config_file.write_text("test: value")

        with patch("pathlib.Path.home", return_value=self.temp_dir):
            with patch("pathlib.Path.cwd", return_value=Path("/tmp")):
                result = find_config_file()
                assert result == config_file

    def test_find_config_file_config_dir(self) -> None:
        """Test finding config file in .config directory."""
        config_dir = self.temp_dir / ".config" / "ccmonitor"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.yaml"
        config_file.write_text("test: value")

        with patch("pathlib.Path.home", return_value=self.temp_dir):
            with patch("pathlib.Path.cwd", return_value=Path("/tmp")):
                result = find_config_file()
                assert result == config_file

    def test_find_config_file_not_found(self) -> None:
        """Test when no config file is found."""
        with patch("pathlib.Path.home", return_value=self.temp_dir):
            with patch("pathlib.Path.cwd", return_value=Path("/tmp")):
                result = find_config_file()
                assert result is None


class TestJSONLValidation:
    """Test suite for JSONL file validation."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def test_is_jsonl_file_valid_extension_and_content(self) -> None:
        """Test JSONL validation with valid extension and content."""
        jsonl_file = self.temp_dir / "test.jsonl"
        with jsonl_file.open("w") as f:
            f.write('{"type": "user", "content": "hello"}\n')
            f.write('{"type": "assistant", "content": "hi there"}\n')

        result = is_jsonl_file(jsonl_file)
        assert result is True

    def test_is_jsonl_file_ndjson_extension(self) -> None:
        """Test JSONL validation with .ndjson extension."""
        ndjson_file = self.temp_dir / "test.ndjson"
        with ndjson_file.open("w") as f:
            f.write('{"valid": "json"}\n')

        result = is_jsonl_file(ndjson_file)
        assert result is True

    def test_is_jsonl_file_wrong_extension(self) -> None:
        """Test JSONL validation with wrong extension."""
        txt_file = self.temp_dir / "test.txt"
        with txt_file.open("w") as f:
            f.write('{"type": "user", "content": "hello"}\n')

        result = is_jsonl_file(txt_file)
        assert result is False

    def test_is_jsonl_file_invalid_content(self) -> None:
        """Test JSONL validation with invalid JSON content."""
        jsonl_file = self.temp_dir / "test.jsonl"
        with jsonl_file.open("w") as f:
            f.write("not valid json\n")
            f.write("also not valid json\n")

        result = is_jsonl_file(jsonl_file)
        assert result is False

    def test_is_jsonl_file_mixed_content(self) -> None:
        """Test JSONL validation with mixed valid/invalid content."""
        jsonl_file = self.temp_dir / "test.jsonl"
        with jsonl_file.open("w") as f:
            f.write('{"valid": "json"}\n')
            f.write("invalid json line\n")

        result = is_jsonl_file(jsonl_file)
        assert result is False

    def test_is_jsonl_file_empty_lines(self) -> None:
        """Test JSONL validation with empty lines (should be ignored)."""
        jsonl_file = self.temp_dir / "test.jsonl"
        with jsonl_file.open("w") as f:
            f.write('{"valid": "json"}\n')
            f.write("\n")  # Empty line
            f.write('{"also": "valid"}\n')

        result = is_jsonl_file(jsonl_file)
        assert result is True

    def test_is_jsonl_file_nonexistent(self) -> None:
        """Test JSONL validation with non-existent file."""
        nonexistent = self.temp_dir / "nonexistent.jsonl"

        result = is_jsonl_file(nonexistent)
        assert result is False

    def test_is_jsonl_file_unicode_error(self) -> None:
        """Test JSONL validation with unicode decode error."""
        jsonl_file = self.temp_dir / "test.jsonl"
        # Write some binary data that will cause UnicodeDecodeError
        with jsonl_file.open("wb") as f:
            f.write(b"\xff\xfe\x00\x00")

        result = is_jsonl_file(jsonl_file)
        assert result is False

    def test_is_jsonl_file_sample_limit(self) -> None:
        """Test JSONL validation respects sample line limit."""
        jsonl_file = self.temp_dir / "test.jsonl"
        with jsonl_file.open("w") as f:
            # Write valid JSON lines up to the sample limit
            for i in range(5):  # More than JSONL_DETECTION_SAMPLE_LINES
                f.write(f'{{"line": {i}}}\n')

        # Patch the constant to test the limit
        with patch("src.cli.utils.JSONL_DETECTION_SAMPLE_LINES", 3):
            with patch("src.cli.utils._is_valid_json_line") as mock_valid:
                mock_valid.return_value = True

                is_jsonl_file(jsonl_file)

                # Should only check the first 3 lines
                assert mock_valid.call_count == 3


class TestFileAccessUtilities:
    """Test suite for file access utility functions."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test.txt"
        self.test_file.write_text("test content")

    def test_check_read_access_existing_file(self) -> None:
        """Test read access check for existing readable file."""
        from src.cli.utils import _check_read_access

        result = _check_read_access(self.test_file)
        assert result is True

    def test_check_write_access_existing_file(self) -> None:
        """Test write access check for existing writable file."""
        from src.cli.utils import _check_write_access

        result = _check_write_access(self.test_file)
        assert result is True

    def test_check_write_access_new_file(self) -> None:
        """Test write access check for new file in writable directory."""
        from src.cli.utils import _check_write_access

        new_file = self.temp_dir / "new_file.txt"
        result = _check_write_access(new_file)
        assert result is True

    def test_check_execute_access(self) -> None:
        """Test execute access check."""
        from src.cli.utils import _check_execute_access

        # Create an executable file
        if os.name != "nt":  # Skip on Windows
            executable = self.temp_dir / "script.sh"
            executable.write_text("#!/bin/bash\necho 'test'")
            executable.chmod(0o755)

            result = _check_execute_access(executable)
            assert result is True

    def test_check_access_by_mode_invalid(self) -> None:
        """Test access check with invalid mode."""
        from src.cli.utils import _check_access_by_mode

        result = _check_access_by_mode(self.test_file, "invalid_mode")
        assert result is False


class TestPrivateFunctions:
    """Test suite for private helper functions."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def test_has_jsonl_extension_valid(self) -> None:
        """Test JSONL extension detection."""
        from src.cli.utils import _has_jsonl_extension

        assert _has_jsonl_extension(Path("test.jsonl")) is True
        assert _has_jsonl_extension(Path("test.ndjson")) is True
        assert (
            _has_jsonl_extension(Path("test.JSONL")) is True
        )  # Case insensitive

    def test_has_jsonl_extension_invalid(self) -> None:
        """Test non-JSONL extension detection."""
        from src.cli.utils import _has_jsonl_extension

        assert _has_jsonl_extension(Path("test.txt")) is False
        assert _has_jsonl_extension(Path("test.json")) is False
        assert _has_jsonl_extension(Path("test")) is False

    def test_is_valid_json_line_valid(self) -> None:
        """Test valid JSON line detection."""
        from src.cli.utils import _is_valid_json_line

        assert _is_valid_json_line('{"valid": "json"}') is True
        assert _is_valid_json_line("[]") is True
        assert _is_valid_json_line("null") is True
        assert _is_valid_json_line("42") is True

    def test_is_valid_json_line_invalid(self) -> None:
        """Test invalid JSON line detection."""
        from src.cli.utils import _is_valid_json_line

        assert _is_valid_json_line("invalid json") is False
        assert _is_valid_json_line('{"incomplete": ') is False
        assert _is_valid_json_line("") is False

    def test_validate_jsonl_content_file_error(self) -> None:
        """Test JSONL content validation with file errors."""
        from src.cli.utils import _validate_jsonl_content

        nonexistent = Path("/nonexistent/file.jsonl")
        result = _validate_jsonl_content(nonexistent)
        assert result is False

    def test_check_sample_lines_with_mock(self) -> None:
        """Test sample line checking with mocked file handle."""
        from src.cli.utils import _check_sample_lines

        # Create a mock file handle
        mock_lines = [
            '{"line": 1}\n',
            '{"line": 2}\n',
            "invalid json\n",  # This should cause failure
        ]

        class MockFileHandle:
            def __init__(self, lines: list[str]) -> None:
                self.lines = lines
                self.index = 0

            def __iter__(self) -> "MockFileHandle":
                return self

            def __next__(self) -> str:
                if self.index >= len(self.lines):
                    raise StopIteration
                line = self.lines[self.index]
                self.index += 1
                return line

        mock_handle = MockFileHandle(mock_lines)
        result = _check_sample_lines(mock_handle)
        assert result is False  # Should fail due to invalid JSON line
