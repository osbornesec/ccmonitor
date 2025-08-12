"""Test suite for CCMonitor CLI main interface.

Comprehensive testing of CLI commands, file monitoring, and real-time functionality.
"""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

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
    config_set,
    config_show,
)
from src.common.exceptions import CCMonitorError, ConfigurationError


class TestCLIMainInterface:
    """Test suite for main CLI interface and commands."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.runner = CliRunner()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_jsonl_file = self.temp_dir / "conversation.jsonl"

        # Create sample JSONL content
        test_data = [
            {
                "type": "user",
                "content": "Hello Claude",
                "timestamp": "2024-01-01T10:00:00Z",
            },
            {
                "type": "assistant",
                "content": "Hello! How can I help?",
                "timestamp": "2024-01-01T10:00:01Z",
            },
        ]

        with self.test_jsonl_file.open("w") as f:
            for entry in test_data:
                f.write(json.dumps(entry) + "\n")

    def test_cli_version_flag(self) -> None:
        """Test --version flag displays version and exits."""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "ccmonitor version" in result.output

    def test_cli_help_display(self) -> None:
        """Test help message is displayed correctly."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert (
            "CCMonitor: Claude Code conversation monitoring tool"
            in result.output
        )
        assert "monitor" in result.output
        assert "config" in result.output

    def test_cli_no_command_shows_help(self) -> None:
        """Test CLI shows help when no command is provided."""
        with patch("src.cli.main.config_manager"):
            result = self.runner.invoke(cli, [])
            assert result.exit_code == 0
            assert (
                "CCMonitor: Claude Code conversation monitoring tool"
                in result.output
            )

    @patch("src.cli.main.config_manager")
    def test_cli_verbose_flag(self, mock_config_manager: Mock) -> None:
        """Test --verbose flag enables verbose logging."""
        mock_config_manager.load_default_config.return_value = {}

        with patch("src.cli.main.setup_logging") as mock_logging:
            result = self.runner.invoke(cli, ["--verbose"])
            assert result.exit_code == 0
            mock_logging.assert_called_once()

    @patch("src.cli.main.config_manager")
    def test_cli_config_file_loading(self, mock_config_manager: Mock) -> None:
        """Test loading configuration from file."""
        config_file = self.temp_dir / "config.yaml"
        config_file.write_text("test: value")

        mock_config_manager.load_config.return_value = {"test": "value"}
        mock_config_manager.load_default_config.return_value = {
            "test": "value",
        }

        result = self.runner.invoke(cli, ["--config", str(config_file)])
        assert result.exit_code == 0
        mock_config_manager.load_config.assert_called_once_with(config_file)

    @patch("src.cli.main.config_manager")
    def test_cli_config_error_handling(
        self,
        mock_config_manager: Mock,
    ) -> None:
        """Test error handling for invalid configuration."""
        mock_config_manager.load_default_config.side_effect = (
            ConfigurationError("Invalid config")
        )

        result = self.runner.invoke(cli, [])
        assert result.exit_code == 1
        assert "Error loading configuration" in result.output


class TestMonitorCommand:
    """Test suite for monitor command functionality."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.runner = CliRunner()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_jsonl_file = self.temp_dir / "conversation.jsonl"

        # Create sample data
        with self.test_jsonl_file.open("w") as f:
            f.write(json.dumps({"type": "user", "content": "test"}) + "\n")

    @patch("src.cli.main.config_manager")
    @patch("src.cli.main.FileMonitor")
    def test_monitor_command_basic(
        self,
        mock_file_monitor: Mock,
        mock_config_manager: Mock,
    ) -> None:
        """Test basic monitor command execution."""
        mock_config_manager.load_default_config.return_value = {}
        mock_monitor_instance = Mock()
        mock_file_monitor.return_value = mock_monitor_instance

        result = self.runner.invoke(
            cli,
            ["monitor", "--directory", str(self.temp_dir), "--interval", "1"],
        )

        assert result.exit_code == 0
        mock_file_monitor.assert_called_once()
        mock_monitor_instance.execute_monitoring.assert_called_once()

    @patch("src.cli.main.config_manager")
    def test_monitor_invalid_directory(
        self,
        mock_config_manager: Mock,
    ) -> None:
        """Test monitor command with non-existent directory."""
        mock_config_manager.load_default_config.return_value = {}

        result = self.runner.invoke(
            cli,
            ["monitor", "--directory", "/nonexistent/path"],
        )

        assert result.exit_code == 2
        assert "does not exist" in result.output

    @patch("src.cli.main.config_manager")
    def test_monitor_with_options(self, mock_config_manager: Mock) -> None:
        """Test monitor command with various options."""
        mock_config_manager.load_default_config.return_value = {}

        with patch("src.cli.main.FileMonitor") as mock_file_monitor:
            mock_monitor_instance = Mock()
            mock_file_monitor.return_value = mock_monitor_instance

            result = self.runner.invoke(
                cli,
                [
                    "monitor",
                    "--directory",
                    str(self.temp_dir),
                    "--interval",
                    "2",
                    "--pattern",
                    "*.jsonl",
                    "--since-last-run",
                    "--process-all",
                ],
            )

            assert result.exit_code == 0

            # Verify FileMonitor was called with correct config
            args, kwargs = mock_file_monitor.call_args
            config = args[0]
            assert config.interval == 2
            assert config.pattern == "*.jsonl"
            assert config.since_last_run is True
            assert config.process_all is True


class TestFileMonitor:
    """Test suite for FileMonitor class."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test.jsonl"
        self.output_file = self.temp_dir / "output.txt"

        # Create sample JSONL file
        with self.test_file.open("w") as f:
            f.write(json.dumps({"type": "user", "content": "hello"}) + "\n")

        self.config = MonitorConfig(
            directory=self.temp_dir,
            interval=1,
            output=self.output_file,
            pattern="*.jsonl",
        )

    def test_file_monitor_initialization(self) -> None:
        """Test FileMonitor initialization."""
        monitor = FileMonitor(self.config, verbose=True)

        assert monitor.config == self.config
        assert monitor.verbose is True
        assert monitor.file_timestamps == {}
        assert monitor.file_sizes == {}

    @patch("src.cli.main._validate_monitor_directory")
    @patch("src.cli.main._display_monitor_startup")
    def test_file_monitor_execute_basic(
        self,
        mock_display: Mock,
        mock_validate: Mock,
    ) -> None:
        """Test basic monitoring execution."""
        mock_validate.return_value = self.temp_dir

        monitor = FileMonitor(self.config)

        with patch.object(monitor, "_process_existing_files") as mock_process:
            with patch.object(monitor, "_save_state") as mock_save:
                monitor.config.process_all = True
                monitor.execute_monitoring()

                mock_validate.assert_called_once_with(self.config.directory)
                mock_display.assert_called_once()
                mock_process.assert_called_once()

    def test_file_monitor_scan_files(self) -> None:
        """Test file scanning functionality."""
        monitor = FileMonitor(self.config)

        files = monitor._scan_files(self.temp_dir)
        assert len(files) == 1
        assert self.test_file in files

    def test_file_monitor_get_file_info(self) -> None:
        """Test file info retrieval."""
        monitor = FileMonitor(self.config)

        mtime, size = monitor._get_file_info(self.test_file)
        assert mtime > 0
        assert size > 0

    def test_file_monitor_is_new_file(self) -> None:
        """Test new file detection."""
        monitor = FileMonitor(self.config)

        # File should be new initially
        assert monitor._is_new_file(self.test_file) is True

        # After adding to timestamps, should not be new
        monitor.file_timestamps[self.test_file] = time.time()
        assert monitor._is_new_file(self.test_file) is False

    def test_file_monitor_is_modified_file(self) -> None:
        """Test modified file detection."""
        monitor = FileMonitor(self.config)

        mtime, size = monitor._get_file_info(self.test_file)

        # File should be modified if not in timestamps
        assert monitor._is_modified_file(self.test_file, mtime, size) is True

        # After setting timestamps, should not be modified with same values
        monitor.file_timestamps[self.test_file] = mtime
        monitor.file_sizes[self.test_file] = size
        assert monitor._is_modified_file(self.test_file, mtime, size) is False

    def test_file_monitor_parse_json_line_valid(self) -> None:
        """Test JSON line parsing with valid JSON."""
        monitor = FileMonitor(self.config)

        valid_json = '{"type": "user", "content": "test"}'
        result = monitor._parse_json_line(valid_json)

        assert result == {"type": "user", "content": "test"}

    def test_file_monitor_parse_json_line_invalid(self) -> None:
        """Test JSON line parsing with invalid JSON."""
        monitor = FileMonitor(self.config)

        invalid_json = "not valid json"
        result = monitor._parse_json_line(invalid_json)

        assert result == {"raw_line": "not valid json"}

    def test_file_monitor_read_new_content(self) -> None:
        """Test reading new content from file."""
        monitor = FileMonitor(self.config)

        # Add more content to file
        with self.test_file.open("a") as f:
            f.write(
                json.dumps({"type": "assistant", "content": "response"})
                + "\n",
            )

        # Read from beginning
        content = monitor._read_new_content(self.test_file, 0)
        assert len(content) == 2
        assert content[0]["type"] == "user"
        assert content[1]["type"] == "assistant"

    def test_file_monitor_write_changes(self) -> None:
        """Test writing changes to output file."""
        monitor = FileMonitor(self.config)

        changes = [
            {"type": "user", "content": "test message 1"},
            {"type": "assistant", "content": "test response 1"},
        ]

        monitor._write_changes(self.test_file, changes)

        assert self.output_file.exists()
        content = self.output_file.read_text()
        assert "CHANGES DETECTED" in content
        assert "test message 1" in content
        assert "test response 1" in content

    def test_file_monitor_save_load_state(self) -> None:
        """Test state saving and loading."""
        monitor = FileMonitor(self.config)

        # Set up some state
        monitor.file_timestamps[self.test_file] = 12345.0
        monitor.file_sizes[self.test_file] = 100

        # Save state
        monitor._save_state()
        assert monitor.state_file.exists()

        # Load state in new monitor
        new_monitor = FileMonitor(self.config)
        timestamps, sizes = new_monitor._load_state()

        assert timestamps[self.test_file] == 12345.0
        assert sizes[self.test_file] == 100

    def test_file_monitor_keyboard_interrupt(self) -> None:
        """Test handling of KeyboardInterrupt."""
        monitor = FileMonitor(self.config)

        with patch.object(
            monitor,
            "_start_realtime_monitoring",
        ) as mock_monitor:
            mock_monitor.side_effect = KeyboardInterrupt()

            with patch("click.echo") as mock_echo:
                with patch.object(monitor, "_save_state") as mock_save:
                    monitor.execute_monitoring()

                    # Verify graceful shutdown
                    mock_save.assert_called_once()
                    mock_echo.assert_called()


class TestConfigCommands:
    """Test suite for configuration commands."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.runner = CliRunner()

    @patch("src.cli.main.config_manager")
    def test_config_show_command(self, mock_config_manager: Mock) -> None:
        """Test config show command."""
        mock_config_manager.get_current_config.return_value = {
            "setting1": "value1",
            "setting2": "value2",
        }

        result = self.runner.invoke(config_show)

        assert result.exit_code == 0
        assert "Current Configuration" in result.output
        assert "setting1: value1" in result.output
        assert "setting2: value2" in result.output

    @patch("src.cli.main.config_manager")
    def test_config_show_error(self, mock_config_manager: Mock) -> None:
        """Test config show with error."""
        mock_config_manager.get_current_config.side_effect = (
            ConfigurationError("Config error")
        )

        result = self.runner.invoke(config_show)

        assert result.exit_code == 1
        assert "Error reading configuration" in result.output

    @patch("src.cli.main.config_manager")
    def test_config_set_command(self, mock_config_manager: Mock) -> None:
        """Test config set command."""
        result = self.runner.invoke(config_set, ["test_key", "test_value"])

        assert result.exit_code == 0
        assert "Configuration updated" in result.output
        mock_config_manager.set_config_value.assert_called_once_with(
            "test_key",
            value="test_value",
        )

    @patch("src.cli.main.config_manager")
    def test_config_set_error(self, mock_config_manager: Mock) -> None:
        """Test config set with error."""
        mock_config_manager.set_config_value.side_effect = ConfigurationError(
            "Invalid key",
        )

        result = self.runner.invoke(config_set, ["invalid_key", "value"])

        assert result.exit_code == 1
        assert "Error updating configuration" in result.output


class TestDataClasses:
    """Test suite for CLI data classes."""

    def test_monitor_config_initialization(self) -> None:
        """Test MonitorConfig initialization."""
        config = MonitorConfig(
            directory=Path("/test"),
            interval=5,
            output=Path("/output"),
            pattern="*.jsonl",
            since_last_run=True,
            process_all=False,
        )

        assert config.directory == Path("/test")
        assert config.interval == 5
        assert config.output == Path("/output")
        assert config.pattern == "*.jsonl"
        assert config.since_last_run is True
        assert config.process_all is False

    def test_monitor_spec_initialization(self) -> None:
        """Test MonitorSpec initialization."""
        spec = MonitorSpec(
            directory=Path("/test"),
            interval=10,
            pattern="*.json",
        )

        assert spec.directory == Path("/test")
        assert spec.interval == 10
        assert spec.pattern == "*.json"

    def test_mode_flags_initialization(self) -> None:
        """Test ModeFlags initialization."""
        flags = ModeFlags(since_last_run=True, process_all=False)

        assert flags.since_last_run is True
        assert flags.process_all is False

    def test_cli_context_initialization(self) -> None:
        """Test CLIContext initialization."""
        context = CLIContext()

        assert context.verbose is False
        assert context.config_file is None
        assert context.config == {}


class TestUtilityFunctions:
    """Test suite for CLI utility functions."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def test_validate_monitor_directory_valid(self) -> None:
        """Test directory validation with valid directory."""
        result = _validate_monitor_directory(self.temp_dir)
        assert result == self.temp_dir

    def test_validate_monitor_directory_nonexistent(self) -> None:
        """Test directory validation with non-existent directory."""
        nonexistent = Path("/nonexistent/path")

        with patch("click.echo") as mock_echo:
            with patch("sys.exit") as mock_exit:
                _validate_monitor_directory(nonexistent)

                mock_echo.assert_called()
                mock_exit.assert_called_with(1)

    def test_display_monitor_startup(self) -> None:
        """Test monitor startup display."""
        with patch("click.echo") as mock_echo:
            _display_monitor_startup(
                monitor_dir=Path("/test"),
                output=Path("/output.txt"),
                pattern="*.jsonl",
                process_all=True,
                since_last_run=False,
            )

            # Verify multiple echo calls were made
            assert mock_echo.call_count >= 4

            # Check for key messages
            calls = [call[0][0] for call in mock_echo.call_args_list]
            assert any("Starting CCMonitor" in call for call in calls)
            assert any("Processing ALL existing" in call for call in calls)

    def test_execute_monitor_command_success(self) -> None:
        """Test successful monitor command execution."""
        context = CLIContext()
        context.verbose = True

        config = MonitorConfig(
            directory=self.temp_dir,
            interval=1,
            output=Path("/output.txt"),
            pattern="*.jsonl",
        )

        with patch("src.cli.main.FileMonitor") as mock_file_monitor:
            mock_monitor_instance = Mock()
            mock_file_monitor.return_value = mock_monitor_instance

            _execute_monitor_command(context, config)

            mock_file_monitor.assert_called_once_with(config, verbose=True)
            mock_monitor_instance.execute_monitoring.assert_called_once()

    def test_execute_monitor_command_error(self) -> None:
        """Test monitor command execution with error."""
        context = CLIContext()
        config = MonitorConfig(
            directory=self.temp_dir,
            interval=1,
            output=Path("/output.txt"),
            pattern="*.jsonl",
        )

        with patch("src.cli.main.FileMonitor") as mock_file_monitor:
            mock_monitor_instance = Mock()
            mock_monitor_instance.execute_monitoring.side_effect = (
                CCMonitorError("Test error")
            )
            mock_file_monitor.return_value = mock_monitor_instance

            with patch("click.echo") as mock_echo:
                with patch("sys.exit") as mock_exit:
                    _execute_monitor_command(context, config)

                    mock_echo.assert_called()
                    mock_exit.assert_called_with(1)
