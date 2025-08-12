"""Comprehensive tests for CLI main module.

This module provides complete test coverage for the CLI main functionality,
including command parsing, file monitoring, configuration management, and
all interactive features.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from src.cli.main import (
    CLIContext,
    FileMonitor,
    ModeFlags,
    MonitorConfig,
    MonitorSpec,
    _display_monitor_startup,
    _execute_monitor_command,
    _validate_monitor_directory,
    cli,
    config_manager,
)
from src.common.exceptions import CCMonitorError, ConfigurationError

# Test constants to avoid magic numbers
TEST_INTERVAL_FIVE = 5
TEST_INTERVAL_TEN = 10
TEST_INTERVAL_TWENTY = 20
TEST_SIZE_TWO = 2
TEST_SIZE_THREE = 3
TEST_COUNT_FIVE = 5
TEST_TIMESTAMP_123_456 = 123.456
TEST_SIZE_789 = 789
TEST_SIZE_1000 = 1000
TEST_SIZE_999 = 999


class TestCLIContext:
    """Test CLI context management."""

    def test_default_initialization(self) -> None:
        """Test CLI context default initialization."""
        ctx = CLIContext()

        assert ctx.verbose is False
        assert ctx.config_file is None
        assert ctx.config == {}

    def test_context_modification(self) -> None:
        """Test CLI context can be modified."""
        ctx = CLIContext()

        ctx.verbose = True
        ctx.config_file = "test.toml"
        ctx.config = {"key": "value"}

        assert ctx.verbose is True
        assert ctx.config_file == "test.toml"
        assert ctx.config == {"key": "value"}


class TestDataClasses:
    """Test dataclass definitions."""

    def test_monitor_config_creation(self) -> None:
        """Test MonitorConfig dataclass."""
        config = MonitorConfig(
            directory=Path("/test"),
            interval=5,
            output=Path("output.txt"),
            pattern="*.jsonl",
            since_last_run=True,
            process_all=False,
        )

        assert config.directory == Path("/test")
        assert config.interval == 5
        assert config.output == Path("output.txt")
        assert config.pattern == "*.jsonl"
        assert config.since_last_run is True
        assert config.process_all is False

    def test_monitor_spec_creation(self) -> None:
        """Test MonitorSpec dataclass."""
        spec = MonitorSpec(
            directory=Path("/test"),
            interval=10,
            pattern="*.jsonl",
        )

        assert spec.directory == Path("/test")
        assert spec.interval == 10
        assert spec.pattern == "*.jsonl"

    def test_mode_flags_creation(self) -> None:
        """Test ModeFlags dataclass."""
        flags = ModeFlags(since_last_run=True, process_all=False)

        assert flags.since_last_run is True
        assert flags.process_all is False

    def test_mode_flags_defaults(self) -> None:
        """Test ModeFlags default values."""
        flags = ModeFlags()

        assert flags.since_last_run is False
        assert flags.process_all is False


class TestCLIMainCommand:
    """Test main CLI command functionality."""

    def test_version_flag(self) -> None:
        """Test version flag display."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "ccmonitor version" in result.output

    def test_help_display(self) -> None:
        """Test help message display."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert (
            "CCMonitor: Claude Code conversation monitoring tool"
            in result.output
        )

    def test_no_command_shows_help(self) -> None:
        """Test that no command shows help."""
        runner = CliRunner()

        with patch.object(
            config_manager,
            "load_default_config",
            return_value={},
        ):
            result = runner.invoke(cli, [])

            assert result.exit_code == 0
            assert "Usage:" in result.output

    def test_verbose_flag(self) -> None:
        """Test verbose flag sets context."""
        runner = CliRunner()

        with (
            patch.object(
                config_manager,
                "load_default_config",
                return_value={},
            ),
            patch("src.cli.main.setup_logging") as mock_logging,
        ):

            result = runner.invoke(cli, ["--verbose"])

            assert result.exit_code == 0
            # Verbose should trigger DEBUG level logging
            mock_logging.assert_called_once()

    def test_config_file_loading(self) -> None:
        """Test configuration file loading."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".toml",
            delete=False,
        ) as f:
            f.write('[test]\nkey = "value"\n')
            config_file = f.name

        try:
            test_config = {"test": {"key": "value"}}
            with (
                patch.object(
                    config_manager,
                    "load_config",
                    return_value=test_config,
                ),
                patch("src.cli.main.setup_logging"),
            ):

                result = runner.invoke(cli, ["--config", config_file])

                assert result.exit_code == 0
        finally:
            os.unlink(config_file)

    def test_config_loading_error(self) -> None:
        """Test configuration loading error handling."""
        runner = CliRunner()

        with patch.object(
            config_manager,
            "load_default_config",
            side_effect=ConfigurationError("Config error"),
        ):

            result = runner.invoke(cli, [])

            assert result.exit_code == 1
            assert "Error loading configuration" in result.output


class TestMonitorCommand:
    """Test monitor command functionality."""

    def test_monitor_command_defaults(self) -> None:
        """Test monitor command with default arguments."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch.object(
                    config_manager,
                    "load_default_config",
                    return_value={},
                ),
                patch("src.cli.main.setup_logging"),
                patch("src.cli.main._execute_monitor_command") as mock_execute,
            ):

                # Use a real temporary directory that exists
                result = runner.invoke(
                    cli, ["monitor", "--directory", temp_dir]
                )

                assert result.exit_code == 0
                mock_execute.assert_called_once()

    def test_monitor_with_custom_arguments(self) -> None:
        """Test monitor command with custom arguments."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch.object(
                    config_manager,
                    "load_default_config",
                    return_value={},
                ),
                patch("src.cli.main.setup_logging"),
                patch("src.cli.main._execute_monitor_command") as mock_execute,
            ):

                result = runner.invoke(
                    cli,
                    [
                        "monitor",
                        "--directory",
                        temp_dir,
                        "--interval",
                        "10",
                        "--output",
                        "custom_output.txt",
                        "--pattern",
                        "*.log",
                        "--since-last-run",
                        "--process-all",
                    ],
                )

                assert result.exit_code == 0
                mock_execute.assert_called_once()

                # Check the config passed to execute
                call_args = mock_execute.call_args[0]
                config = call_args[1]

                assert config.interval == 10
                assert config.output == Path("custom_output.txt")
                assert config.pattern == "*.log"
                assert config.since_last_run is True
                assert config.process_all is True

    def test_monitor_invalid_directory(self) -> None:
        """Test monitor command with invalid directory."""
        runner = CliRunner()

        with (
            patch.object(
                config_manager,
                "load_default_config",
                return_value={},
            ),
            patch("src.cli.main.setup_logging"),
        ):

            result = runner.invoke(
                cli,
                ["monitor", "--directory", "/nonexistent"],
            )

            # Should fail with directory validation error
            assert result.exit_code != 0


class TestFileMonitor:
    """Test FileMonitor class functionality."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def monitor_config(self, temp_dir: Path) -> MonitorConfig:
        """Create test monitor configuration."""
        return MonitorConfig(
            directory=temp_dir,
            interval=1,
            output=temp_dir / "output.txt",
            pattern="*.jsonl",
        )

    def test_file_monitor_initialization(
        self,
        monitor_config: MonitorConfig,
    ) -> None:
        """Test FileMonitor initialization."""
        monitor = FileMonitor(monitor_config, verbose=True)

        assert monitor.config == monitor_config
        assert monitor.verbose is True
        assert monitor.state_file.name == ".ccmonitor_state.pkl"
        assert monitor.file_timestamps == {}
        assert monitor.file_sizes == {}

    def test_execute_monitoring_process_all(
        self,
        monitor_config: MonitorConfig,
        temp_dir: Path,
    ) -> None:
        """Test execute monitoring with process all flag."""
        monitor_config.process_all = True
        monitor = FileMonitor(monitor_config, verbose=True)

        # Create test file
        test_file = temp_dir / "test.jsonl"
        test_file.write_text('{"test": "data"}\n')

        with (
            patch.object(monitor, "_save_state"),
            patch("src.cli.main._display_monitor_startup"),
            patch.object(monitor, "_process_existing_files") as mock_process,
        ):

            # Mock keyboard interrupt to stop execution
            mock_process.side_effect = KeyboardInterrupt()

            monitor.execute_monitoring()

            mock_process.assert_called_once()

    def test_execute_monitoring_since_last_run(
        self,
        monitor_config: MonitorConfig,
    ) -> None:
        """Test execute monitoring with since last run flag."""
        monitor_config.since_last_run = True
        monitor = FileMonitor(monitor_config)

        with (
            patch.object(monitor, "_load_previous_state"),
            patch.object(monitor, "_save_state"),
            patch("src.cli.main._display_monitor_startup"),
            patch.object(monitor, "_process_existing_files") as mock_process,
        ):

            mock_process.side_effect = KeyboardInterrupt()

            monitor.execute_monitoring()

            mock_process.assert_called_once()

    def test_execute_monitoring_realtime(
        self,
        monitor_config: MonitorConfig,
    ) -> None:
        """Test execute monitoring realtime mode."""
        monitor = FileMonitor(monitor_config)

        with (
            patch.object(monitor, "_save_state"),
            patch("src.cli.main._display_monitor_startup"),
            patch.object(
                monitor,
                "_start_realtime_monitoring",
            ) as mock_realtime,
        ):

            mock_realtime.side_effect = KeyboardInterrupt()

            monitor.execute_monitoring()

            mock_realtime.assert_called_once()

    def test_scan_files(
        self,
        monitor_config: MonitorConfig,
        temp_dir: Path,
    ) -> None:
        """Test file scanning functionality."""
        monitor = FileMonitor(monitor_config)

        # Create test files
        (temp_dir / "test1.jsonl").write_text('{"test": 1}')
        (temp_dir / "test2.jsonl").write_text('{"test": 2}')
        (temp_dir / "test3.txt").write_text("not jsonl")  # Should be ignored

        files = monitor._scan_files(temp_dir)

        assert len(files) == 2
        jsonl_files = {f.name for f in files}
        assert "test1.jsonl" in jsonl_files
        assert "test2.jsonl" in jsonl_files
        assert "test3.txt" not in jsonl_files

    def test_get_file_info(
        self,
        monitor_config: MonitorConfig,
        temp_dir: Path,
    ) -> None:
        """Test getting file information."""
        monitor = FileMonitor(monitor_config)

        test_file = temp_dir / "test.jsonl"
        test_content = '{"test": "data"}\n'
        test_file.write_text(test_content)

        mtime, size = monitor._get_file_info(test_file)

        assert mtime > 0
        assert size == len(test_content)

    def test_get_file_info_nonexistent(
        self,
        monitor_config: MonitorConfig,
        temp_dir: Path,
    ) -> None:
        """Test getting file info for nonexistent file."""
        monitor = FileMonitor(monitor_config)

        nonexistent_file = temp_dir / "nonexistent.jsonl"
        mtime, size = monitor._get_file_info(nonexistent_file)

        assert mtime == 0
        assert size == 0

    def test_is_new_file(
        self,
        monitor_config: MonitorConfig,
        temp_dir: Path,
    ) -> None:
        """Test new file detection."""
        monitor = FileMonitor(monitor_config)

        test_file = temp_dir / "test.jsonl"
        test_file.write_text('{"test": "data"}')

        # Initially new
        assert monitor._is_new_file(test_file) is True

        # Add to tracking
        monitor.file_timestamps[test_file] = 123.0
        assert monitor._is_new_file(test_file) is False

    def test_is_modified_file(
        self,
        monitor_config: MonitorConfig,
        temp_dir: Path,
    ) -> None:
        """Test modified file detection."""
        monitor = FileMonitor(monitor_config)

        test_file = temp_dir / "test.jsonl"
        test_file.write_text('{"test": "data"}')

        # Set initial state
        monitor.file_timestamps[test_file] = 100.0
        monitor.file_sizes[test_file] = 10

        # Test with newer mtime
        assert monitor._is_modified_file(test_file, 200.0, 10) is True

        # Test with different size
        assert monitor._is_modified_file(test_file, 100.0, 20) is True

        # Test with same values
        assert monitor._is_modified_file(test_file, 100.0, 10) is False

    def test_read_new_content(
        self,
        monitor_config: MonitorConfig,
        temp_dir: Path,
    ) -> None:
        """Test reading new content from file."""
        monitor = FileMonitor(monitor_config)

        test_file = temp_dir / "test.jsonl"
        content = '{"test": 1}\n{"test": 2}\n{"test": 3}\n'
        test_file.write_text(content)

        # Read from beginning
        result = monitor._read_new_content(test_file, 0)
        assert len(result) == 3
        assert result[0]["test"] == 1
        assert result[1]["test"] == 2
        assert result[2]["test"] == 3

        # Read from middle
        result = monitor._read_new_content(test_file, len('{"test": 1}\n'))
        assert len(result) == 2
        assert result[0]["test"] == 2
        assert result[1]["test"] == 3

    def test_read_new_content_invalid_json(
        self,
        monitor_config: MonitorConfig,
        temp_dir: Path,
    ) -> None:
        """Test reading content with invalid JSON."""
        monitor = FileMonitor(monitor_config)

        test_file = temp_dir / "test.jsonl"
        content = '{"test": 1}\ninvalid json\n{"test": 2}\n'
        test_file.write_text(content)

        result = monitor._read_new_content(test_file, 0)
        assert len(result) == 3
        assert result[0]["test"] == 1
        assert result[1]["raw_line"] == "invalid json"
        assert result[2]["test"] == 2

    def test_write_changes(
        self,
        monitor_config: MonitorConfig,
        temp_dir: Path,
    ) -> None:
        """Test writing changes to output file."""
        monitor = FileMonitor(monitor_config)

        changes = [
            {"test": "data1"},
            {"test": "data2"},
        ]

        test_file = temp_dir / "source.jsonl"
        monitor._write_changes(test_file, changes)

        # Check output file was created and contains expected content
        assert monitor_config.output.exists()
        content = monitor_config.output.read_text()

        assert "CHANGES DETECTED" in content
        assert str(test_file) in content
        assert "NEW ENTRIES: 2" in content
        assert '"test": "data1"' in content
        assert '"test": "data2"' in content

    def test_write_changes_empty_list(
        self,
        monitor_config: MonitorConfig,
        temp_dir: Path,
    ) -> None:
        """Test writing empty changes list."""
        monitor = FileMonitor(monitor_config)

        test_file = temp_dir / "source.jsonl"
        monitor._write_changes(test_file, [])

        # Output file should not be created for empty changes
        assert not monitor_config.output.exists()

    def test_save_and_load_state(
        self,
        monitor_config: MonitorConfig,
        temp_dir: Path,
    ) -> None:
        """Test state saving and loading."""
        monitor = FileMonitor(monitor_config)

        # Set up some state
        test_file = temp_dir / "test.jsonl"
        monitor.file_timestamps[test_file] = 123.456
        monitor.file_sizes[test_file] = 789

        # Save state
        monitor._save_state()

        # Create new monitor and load state
        new_monitor = FileMonitor(monitor_config)
        timestamps, sizes = new_monitor._load_state()

        assert len(timestamps) == 1
        assert len(sizes) == 1
        assert timestamps[test_file] == 123.456
        assert sizes[test_file] == 789

    def test_load_state_no_file(self, monitor_config: MonitorConfig) -> None:
        """Test loading state when no state file exists."""
        monitor = FileMonitor(monitor_config)

        timestamps, sizes = monitor._load_state()

        assert timestamps == {}
        assert sizes == {}

    def test_handle_new_file(
        self,
        monitor_config: MonitorConfig,
        temp_dir: Path,
    ) -> None:
        """Test handling new file detection."""
        monitor = FileMonitor(monitor_config)

        test_file = temp_dir / "test.jsonl"
        mtime, size = 123.456, 789

        monitor._handle_new_file(test_file, mtime, size)

        assert monitor.file_timestamps[test_file] == mtime
        assert monitor.file_sizes[test_file] == size

    def test_handle_modified_file(
        self,
        monitor_config: MonitorConfig,
        temp_dir: Path,
    ) -> None:
        """Test handling modified file detection."""
        monitor = FileMonitor(monitor_config, verbose=True)

        test_file = temp_dir / "test.jsonl"
        test_file.write_text('{"test": "new_data"}')

        # Set old size
        monitor.file_sizes[test_file] = 10

        with (
            patch.object(
                monitor,
                "_read_new_content",
                return_value=[{"test": "data"}],
            ),
            patch.object(monitor, "_write_changes") as mock_write,
        ):

            monitor._handle_modified_file(test_file, 123.456, 20)

            mock_write.assert_called_once()
            assert monitor.file_timestamps[test_file] == 123.456
            assert monitor.file_sizes[test_file] == 20

    def test_check_for_deleted_files(
        self,
        monitor_config: MonitorConfig,
        temp_dir: Path,
    ) -> None:
        """Test checking for deleted files."""
        monitor = FileMonitor(monitor_config)

        # Set up tracked files
        file1 = temp_dir / "file1.jsonl"
        file2 = temp_dir / "file2.jsonl"
        file3 = temp_dir / "file3.jsonl"

        monitor.file_timestamps[file1] = 123.0
        monitor.file_timestamps[file2] = 124.0
        monitor.file_timestamps[file3] = 125.0
        monitor.file_sizes[file1] = 100
        monitor.file_sizes[file2] = 200
        monitor.file_sizes[file3] = 300

        # Only file1 and file3 exist now
        current_files = {file1, file3}

        monitor._check_for_deleted_files(current_files)

        # file2 should be removed from tracking
        assert file1 in monitor.file_timestamps
        assert file2 not in monitor.file_timestamps
        assert file3 in monitor.file_timestamps

        assert file1 in monitor.file_sizes
        assert file2 not in monitor.file_sizes
        assert file3 in monitor.file_sizes


class TestConfigCommands:
    """Test configuration management commands."""

    def test_config_show_command(self) -> None:
        """Test config show command."""
        runner = CliRunner()

        test_config = {
            "monitor_directory": "/test/path",
            "check_interval": 5,
            "file_pattern": "*.jsonl",
        }

        with patch.object(
            config_manager,
            "get_current_config",
            return_value=test_config,
        ):
            result = runner.invoke(cli, ["config", "show"])

            assert result.exit_code == 0
            assert "Current Configuration:" in result.output
            assert "monitor_directory: /test/path" in result.output
            assert "check_interval: 5" in result.output
            assert "file_pattern: *.jsonl" in result.output

    def test_config_show_error(self) -> None:
        """Test config show command with error."""
        runner = CliRunner()

        with patch.object(
            config_manager,
            "get_current_config",
            side_effect=ConfigurationError("Config error"),
        ):
            result = runner.invoke(cli, ["config", "show"])

            assert result.exit_code == 1
            assert "Error reading configuration" in result.output

    def test_config_set_command(self) -> None:
        """Test config set command."""
        runner = CliRunner()

        with patch.object(config_manager, "set_config_value") as mock_set:
            result = runner.invoke(
                cli,
                ["config", "set", "test_key", "test_value"],
            )

            assert result.exit_code == 0
            assert (
                "Configuration updated: test_key = test_value" in result.output
            )
            mock_set.assert_called_once_with("test_key", value="test_value")

    def test_config_set_error(self) -> None:
        """Test config set command with error."""
        runner = CliRunner()

        with patch.object(
            config_manager,
            "set_config_value",
            side_effect=ConfigurationError("Config error"),
        ):
            result = runner.invoke(
                cli,
                ["config", "set", "test_key", "test_value"],
            )

            assert result.exit_code == 1
            assert "Error updating configuration" in result.output


class TestHelperFunctions:
    """Test helper functions."""

    def test_validate_monitor_directory_exists(self) -> None:
        """Test directory validation with existing directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            from src.cli.main import _validate_monitor_directory

            result = _validate_monitor_directory(Path(temp_dir))

            assert result == Path(temp_dir)

    def test_validate_monitor_directory_not_exists(self) -> None:
        """Test directory validation with non-existent directory."""
        from src.cli.main import _validate_monitor_directory

        with pytest.raises(SystemExit):
            _validate_monitor_directory(Path("/nonexistent/directory"))

    def test_display_monitor_startup(self) -> None:
        """Test monitor startup display."""
        from src.cli.main import _display_monitor_startup

        with patch("click.echo") as mock_echo:
            _display_monitor_startup(
                Path("/test/path"),
                Path("output.txt"),
                "*.jsonl",
                process_all=True,
                since_last_run=False,
            )

            # Should have multiple echo calls for different lines
            assert mock_echo.call_count >= 5

            # Check some expected content
            calls = [str(call) for call in mock_echo.call_args_list]
            call_content = " ".join(calls)

            assert "/test/path" in call_content
            assert "output.txt" in call_content
            assert "*.jsonl" in call_content
            assert "Processing ALL existing" in call_content


class TestExecuteMonitorCommand:
    """Test monitor command execution."""

    def test_execute_monitor_command_success(self) -> None:
        """Test successful monitor command execution."""
        from src.cli.main import _execute_monitor_command

        ctx = CLIContext()
        ctx.verbose = True

        config = MonitorConfig(
            directory=Path("/test"),
            interval=5,
            output=Path("output.txt"),
            pattern="*.jsonl",
        )

        with patch("src.cli.main.FileMonitor") as mock_monitor_class:
            mock_monitor = Mock()
            mock_monitor_class.return_value = mock_monitor

            _execute_monitor_command(ctx, config)

            mock_monitor_class.assert_called_once_with(config, verbose=True)
            mock_monitor.execute_monitoring.assert_called_once()

    def test_execute_monitor_command_error(self) -> None:
        """Test monitor command execution with error."""
        from src.cli.main import _execute_monitor_command

        ctx = CLIContext()
        ctx.verbose = False

        config = MonitorConfig(
            directory=Path("/test"),
            interval=5,
            output=Path("output.txt"),
            pattern="*.jsonl",
        )

        with patch("src.cli.main.FileMonitor") as mock_monitor_class:
            mock_monitor = Mock()
            mock_monitor.execute_monitoring.side_effect = CCMonitorError(
                "Test error",
            )
            mock_monitor_class.return_value = mock_monitor

            with pytest.raises(SystemExit) as exc_info:
                _execute_monitor_command(ctx, config)

            assert exc_info.value.code == 1

    def test_execute_monitor_command_verbose_error(self) -> None:
        """Test monitor command execution with verbose error."""
        from src.cli.main import _execute_monitor_command

        ctx = CLIContext()
        ctx.verbose = True

        config = MonitorConfig(
            directory=Path("/test"),
            interval=5,
            output=Path("output.txt"),
            pattern="*.jsonl",
        )

        with (
            patch("src.cli.main.FileMonitor") as mock_monitor_class,
            patch("traceback.print_exc") as mock_traceback,
        ):

            mock_monitor = Mock()
            mock_monitor.execute_monitoring.side_effect = CCMonitorError(
                "Test error",
            )
            mock_monitor_class.return_value = mock_monitor

            with pytest.raises(SystemExit):
                _execute_monitor_command(ctx, config)

            mock_traceback.assert_called_once()


class TestIntegrationScenarios:
    """Test integration scenarios."""

    def test_full_monitor_workflow(self) -> None:
        """Test complete monitor workflow integration."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_file = temp_path / "output.txt"

            # Create test JSONL file
            test_file = temp_path / "test.jsonl"
            test_file.write_text('{"message": "test data"}\n')

            with (
                patch.object(
                    config_manager,
                    "load_default_config",
                    return_value={},
                ),
                patch("src.cli.main.setup_logging"),
                patch("time.sleep", side_effect=KeyboardInterrupt()),
            ):  # Stop after first iteration

                result = runner.invoke(
                    cli,
                    [
                        "monitor",
                        "--directory",
                        str(temp_path),
                        "--output",
                        str(output_file),
                        "--process-all",
                        "--verbose",
                    ],
                )

                # Should exit cleanly with keyboard interrupt
                assert result.exit_code == 0

    def test_config_workflow(self) -> None:
        """Test configuration management workflow."""
        runner = CliRunner()

        test_config = {"key1": "value1", "key2": "value2"}

        with (
            patch.object(
                config_manager,
                "get_current_config",
                return_value=test_config,
            ),
            patch.object(config_manager, "set_config_value") as mock_set,
        ):

            # Show config
            result = runner.invoke(cli, ["config", "show"])
            assert result.exit_code == 0
            assert "key1: value1" in result.output

            # Set config
            result = runner.invoke(cli, ["config", "set", "key3", "value3"])
            assert result.exit_code == 0
            assert "key3 = value3" in result.output
            mock_set.assert_called_once_with("key3", value="value3")

    def test_error_handling_integration(self) -> None:
        """Test error handling across command flow."""
        runner = CliRunner()

        # Test configuration error
        with patch.object(
            config_manager,
            "load_default_config",
            side_effect=ConfigurationError("Config error"),
        ):
            result = runner.invoke(cli, ["monitor"])

            assert result.exit_code == 1
            assert "Error loading configuration" in result.output

        # Test monitor error
        with (
            patch.object(
                config_manager,
                "load_default_config",
                return_value={},
            ),
            patch("src.cli.main.setup_logging"),
            patch("src.cli.main.FileMonitor") as mock_monitor_class,
        ):

            mock_monitor = Mock()
            mock_monitor.execute_monitoring.side_effect = CCMonitorError(
                "Monitor error",
            )
            mock_monitor_class.return_value = mock_monitor

            result = runner.invoke(cli, ["monitor"])

            assert result.exit_code == 1
            assert "Monitoring failed" in result.output


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_jsonl_file_processing(self) -> None:
        """Test processing of empty JSONL files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config = MonitorConfig(
                directory=temp_path,
                interval=1,
                output=temp_path / "output.txt",
                pattern="*.jsonl",
            )

            monitor = FileMonitor(config)

            # Create empty file
            empty_file = temp_path / "empty.jsonl"
            empty_file.write_text("")

            changes = monitor._read_new_content(empty_file, 0)
            assert changes == []

    def test_large_file_handling(self) -> None:
        """Test handling of large files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config = MonitorConfig(
                directory=temp_path,
                interval=1,
                output=temp_path / "output.txt",
                pattern="*.jsonl",
            )

            monitor = FileMonitor(config)

            # Create file with many entries
            large_file = temp_path / "large.jsonl"
            lines = []
            for i in range(1000):
                lines.append(f'{{"id": {i}, "data": "test_data_{i}"}}\n')

            large_file.write_text("".join(lines))

            changes = monitor._read_new_content(large_file, 0)
            assert len(changes) == 1000
            assert changes[0]["id"] == 0
            assert changes[999]["id"] == 999

    def test_file_permission_errors(self) -> None:
        """Test handling of file permission errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config = MonitorConfig(
                directory=temp_path,
                interval=1,
                output=temp_path / "output.txt",
                pattern="*.jsonl",
            )

            monitor = FileMonitor(config, verbose=True)

            # Mock file that raises permission error
            with patch(
                "pathlib.Path.open",
                side_effect=OSError("Permission denied"),
            ):
                changes = monitor._read_new_content(
                    temp_path / "test.jsonl",
                    0,
                )
                assert changes == []

    def test_malformed_state_file(self) -> None:
        """Test handling of malformed state file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config = MonitorConfig(
                directory=temp_path,
                interval=1,
                output=temp_path / "output.txt",
                pattern="*.jsonl",
            )

            monitor = FileMonitor(config, verbose=True)

            # Create malformed state file
            monitor.state_file.write_text("invalid json content")

            timestamps, sizes = monitor._load_state()

            # Should return empty dicts for malformed file
            assert timestamps == {}
            assert sizes == {}
