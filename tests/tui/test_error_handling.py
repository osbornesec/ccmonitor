"""Comprehensive tests for error handling system."""

from pathlib import Path
from typing import Any, NamedTuple
from unittest.mock import Mock, patch

import pytest
from textual.app import App
from textual.screen import Screen

from src.tui.exceptions import (
    ConfigurationError,
    NavigationError,
    RecoverableError,
    RenderingError,
    StartupError,
    TerminalError,
    ThemeError,
    TUIError,
)
from src.tui.utils.error_handler import ErrorHandler
from src.tui.utils.fallback import FallbackMode
from src.tui.utils.startup import StartupValidator
from src.tui.widgets.error_dialog import ErrorDialog

# Test constants
EXPECTED_RECOVERY_STRATEGIES = 4
EXPECTED_MULTIPLE_ERRORS = 4
EXPECTED_ERROR_STATS_TOTAL = 3
EXPECTED_ERROR_STATS_TUI = 2
EXPECTED_ERROR_STATS_RENDERING = 1
EXPECTED_ERROR_STATS_RECENT = 3


class TestTUIExceptions:
    """Test TUI exception hierarchy."""

    def test_tui_error_creation(self) -> None:
        """Test TUIError basic functionality."""
        error = TUIError("Test error", details={"code": 123})
        assert error.message == "Test error"
        assert error.details == {"code": 123}
        assert error.user_message == "Test error"
        assert error.timestamp is not None

    def test_tui_error_to_dict(self) -> None:
        """Test TUIError dictionary conversion."""
        error = TUIError("Test error", details={"code": 123})
        error_dict = error.to_dict()

        assert error_dict["type"] == "TUIError"
        assert error_dict["message"] == "Test error"
        assert error_dict["details"] == {"code": 123}
        assert "timestamp" in error_dict
        assert "traceback" in error_dict

    def test_specialized_exceptions(self) -> None:
        """Test specialized exception types."""
        startup_error = StartupError("Startup failed")
        assert isinstance(startup_error, TUIError)

        terminal_error = TerminalError(
            "Terminal incompatible",
            terminal_info={"term": "dumb"},
        )
        assert isinstance(terminal_error, TUIError)
        assert terminal_error.terminal_info == {"term": "dumb"}

        rendering_error = RenderingError(
            "widget1",
            "compose",
            details={"line": 42},
        )
        assert isinstance(rendering_error, TUIError)
        assert rendering_error.widget_id == "widget1"
        assert rendering_error.render_stage == "compose"

    def test_recoverable_error(self) -> None:
        """Test recoverable error functionality."""
        error = RecoverableError(
            "Recoverable issue",
            recovery_action="restart",
        )
        assert isinstance(error, TUIError)
        assert error.recovery_action == "restart"


class TestErrorHandler:
    """Test centralized error handler."""

    @pytest.fixture
    def mock_app(self) -> Mock:
        """Create a mock app for testing."""
        app = Mock(spec=App)
        app.size = (80, 24)
        app.screen = Mock(spec=Screen)
        app.focused = None
        return app

    @pytest.fixture
    def error_handler(self, mock_app: Mock) -> ErrorHandler:
        """Create error handler instance."""
        with patch("logging.basicConfig"):
            return ErrorHandler(mock_app)

    def test_error_handler_initialization(self, mock_app: Mock) -> None:
        """Test error handler initialization."""
        with patch("logging.basicConfig"):
            handler = ErrorHandler(mock_app)

        assert handler.app == mock_app
        assert len(handler.error_log) == 0
        assert len(handler.recovery_strategies) == EXPECTED_RECOVERY_STRATEGIES

    def test_handle_tui_error(self, error_handler: ErrorHandler) -> None:
        """Test handling of TUI errors."""
        error = TUIError("Test error")

        with patch.object(error_handler, "show_error_dialog") as mock_show:
            result = error_handler.handle_error(error)

        assert result is True
        assert len(error_handler.error_log) == 1
        mock_show.assert_called_once_with(error)

    def test_handle_generic_error(self, error_handler: ErrorHandler) -> None:
        """Test handling of generic Python errors."""
        error = ValueError("Generic error")

        with patch.object(error_handler, "show_error_dialog"):
            result = error_handler.handle_error(error)

        assert result is True
        assert len(error_handler.error_log) == 1
        assert isinstance(error_handler.error_log[0], TUIError)
        assert "Generic error" in error_handler.error_log[0].message

    def test_handle_fatal_error(self, error_handler: ErrorHandler) -> None:
        """Test handling of fatal errors."""
        error = StartupError("Fatal startup error")

        with patch.object(error_handler, "handle_fatal_error") as mock_fatal:
            result = error_handler.handle_error(error)

        assert result is False
        mock_fatal.assert_called_once_with(error)

    def test_recovery_attempt(
        self,
        error_handler: ErrorHandler,
    ) -> None:
        """Test error recovery attempts."""
        # Create a recoverable terminal error for testing
        recoverable_error = RecoverableError("Test recoverable error")

        # Mock the recovery strategy to simulate successful recovery
        with patch.object(
            error_handler,
            "recovery_strategies",
        ) as mock_strategies:
            mock_recovery = Mock(return_value=None)
            mock_strategies.__contains__ = Mock(return_value=True)
            mock_strategies.__getitem__ = Mock(return_value=mock_recovery)

            result = error_handler.attempt_recovery(recoverable_error)

            assert result is True
            mock_recovery.assert_called_once_with(recoverable_error)

    def test_crash_report_generation(
        self,
        error_handler: ErrorHandler,
        tmp_path: Path,
    ) -> None:
        """Test crash report generation."""
        error = StartupError("Fatal error")

        with patch("pathlib.Path.home", return_value=tmp_path):
            crash_file = error_handler.save_crash_report(error)

        assert crash_file.exists()
        assert crash_file.suffix == ".json"

    def test_error_statistics(self, error_handler: ErrorHandler) -> None:
        """Test error statistics generation."""
        # Add some errors
        error1 = TUIError("Error 1")
        error2 = RenderingError("widget", "stage")
        error3 = TUIError("Error 3")

        error_handler.error_log.extend([error1, error2, error3])

        stats = error_handler.get_error_stats()

        assert stats["total_errors"] == EXPECTED_ERROR_STATS_TOTAL
        assert stats["error_types"]["TUIError"] == EXPECTED_ERROR_STATS_TUI
        assert (
            stats["error_types"]["RenderingError"]
            == EXPECTED_ERROR_STATS_RENDERING
        )
        assert stats["recent_errors"] == EXPECTED_ERROR_STATS_RECENT


class TestStartupValidator:
    """Test startup validation system."""

    @pytest.fixture
    def validator(self) -> StartupValidator:
        """Create startup validator instance."""
        return StartupValidator()

    def test_terminal_existence_check(
        self,
        validator: StartupValidator,
    ) -> None:
        """Test terminal existence validation."""
        with patch("sys.stdout.isatty", return_value=True):
            result = validator.check_terminal_exists()
            assert result is True

        with patch("sys.stdout.isatty", return_value=False):
            result = validator.check_terminal_exists()
            assert result is False
            assert len(validator.errors) == 1

    def test_terminal_size_check(self, validator: StartupValidator) -> None:
        """Test terminal size validation."""
        with patch("shutil.get_terminal_size") as mock_size:
            # Create a proper mock terminal size with both the attributes and unpacking
            class TerminalSize(NamedTuple):
                columns: int
                lines: int

            # Test adequate size
            mock_size.return_value = TerminalSize(columns=100, lines=30)
            result = validator.check_terminal_size()
            assert result is True

            # Test inadequate size
            validator.warnings.clear()
            mock_size.return_value = TerminalSize(columns=50, lines=20)
            result = validator.check_terminal_size()
            assert result is True  # Warning, not error
            assert len(validator.warnings) == 1

    def test_dependencies_check(self, validator: StartupValidator) -> None:
        """Test dependency validation."""
        result = validator.check_dependencies()
        assert result is True  # Should pass in test environment

    def test_permissions_check(
        self,
        validator: StartupValidator,
        tmp_path: Path,
    ) -> None:
        """Test file system permissions validation."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            result = validator.check_permissions()
            assert result is True

    def test_comprehensive_validation(
        self,
        validator: StartupValidator,
    ) -> None:
        """Test complete validation workflow."""
        with patch("sys.stdout.isatty", return_value=True):
            valid, message = validator.validate()

        # Should be valid in test environment
        assert valid is True
        assert message is None

    def test_validation_report(self, validator: StartupValidator) -> None:
        """Test validation report generation."""
        validator.errors.append("Test error")
        validator.warnings.append("Test warning")

        report = validator.get_validation_report()

        assert report["has_errors"] is True
        assert report["has_warnings"] is True
        assert "Test error" in report["errors"]
        assert "Test warning" in report["warnings"]


class TestFallbackMode:
    """Test fallback mode functionality."""

    @pytest.fixture
    def mock_app(self) -> Mock:
        """Create mock app for fallback testing."""
        app = Mock(spec=App)
        app.CSS = "original css"
        app.query = Mock(return_value=[])
        return app

    @pytest.fixture
    def fallback_mode(self, mock_app: Mock) -> FallbackMode:
        """Create fallback mode instance."""
        return FallbackMode(mock_app)

    def test_fallback_mode_initialization(
        self,
        fallback_mode: FallbackMode,
        mock_app: Mock,
    ) -> None:
        """Test fallback mode initialization."""
        assert fallback_mode.app == mock_app
        assert fallback_mode.original_css == "original css"

    def test_fallback_mode_activation(
        self,
        fallback_mode: FallbackMode,
        mock_app: Mock,
    ) -> None:
        """Test fallback mode activation."""
        mock_app.stylesheet = Mock()
        mock_app.stylesheet.add_source = Mock()

        fallback_mode.activate()

        # Should attempt to apply fallback CSS
        mock_app.stylesheet.add_source.assert_called()

    def test_icon_replacement(
        self,
        fallback_mode: FallbackMode,
        mock_app: Mock,
    ) -> None:
        """Test Unicode icon replacement."""
        mock_widget = Mock()
        mock_widget.renderable = "🖥️ Test ✓"
        mock_widget.update = Mock()

        mock_app.query.return_value = [mock_widget]

        fallback_mode.replace_icons()

        mock_widget.update.assert_called_with("[M] Test [OK]")

    def test_status_reporting(self, fallback_mode: FallbackMode) -> None:
        """Test fallback mode status reporting."""
        status = fallback_mode.get_status()

        assert "active" in status
        assert "original_css_length" in status
        assert "current_css_length" in status
        assert "ascii_mode" in status

    def test_restoration(
        self,
        fallback_mode: FallbackMode,
        mock_app: Mock,
    ) -> None:
        """Test restoration of original settings."""
        mock_app.stylesheet = Mock()
        mock_app.stylesheet.add_source = Mock()
        mock_app.animation_level = "none"
        mock_app.ascii_mode = True

        fallback_mode.restore_original()

        assert mock_app.animation_level == "basic"
        assert mock_app.ascii_mode is False


class TestErrorDialog:
    """Test error dialog widget."""

    @pytest.fixture
    def mock_app(self) -> Mock:
        """Create mock app for dialog testing."""
        app = Mock(spec=App)
        app.pop_screen = Mock()
        app.notify = Mock()
        return app

    def test_error_dialog_creation(self) -> None:
        """Test error dialog creation."""
        error = TUIError("Test error", details={"code": 123})
        dialog = ErrorDialog(error)

        assert dialog.error == error

    @patch("src.tui.widgets.error_dialog.pyperclip")
    def test_copy_functionality(self, mock_pyperclip: Mock) -> None:
        """Test error details copying."""
        error = TUIError("Test error")
        dialog = ErrorDialog(error)

        # Mock the app property
        mock_app = Mock()
        with patch.object(ErrorDialog, "app", mock_app):
            dialog._copy_error_details()  # noqa: SLF001

            mock_pyperclip.copy.assert_called_once()
            mock_app.notify.assert_called_with(
                "Error details copied to clipboard",
            )

    def test_recovery_attempt(self, mock_app: Mock) -> None:
        """Test recovery attempt from dialog."""
        error = RecoverableError("Recoverable error")
        dialog = ErrorDialog(error)

        # Mock the app property instead of setting it directly
        with patch.object(ErrorDialog, "app", mock_app, create=True):
            mock_error_handler = Mock()
            mock_error_handler.attempt_recovery.return_value = True
            mock_app.error_handler = mock_error_handler

            dialog._handle_recovery()  # noqa: SLF001

            mock_error_handler.attempt_recovery.assert_called_with(error)
            mock_app.pop_screen.assert_called_once()
            mock_app.notify.assert_called_with(
                "Recovery successful",
                severity="information",
            )


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases."""

    @pytest.fixture
    def integrated_system(self) -> dict[str, Any]:
        """Create integrated error handling system."""
        app = Mock(spec=App)
        app.size = (80, 24)
        app.screen = Mock()
        app.focused = None

        with patch("logging.basicConfig"):
            error_handler = ErrorHandler(app)

        fallback_mode = FallbackMode(app)
        validator = StartupValidator()

        return {
            "app": app,
            "error_handler": error_handler,
            "fallback_mode": fallback_mode,
            "validator": validator,
        }

    def test_startup_failure_handling(
        self,
        integrated_system: dict[str, Any],
    ) -> None:
        """Test complete startup failure scenario."""
        validator = integrated_system["validator"]
        error_handler = integrated_system["error_handler"]

        # Simulate startup failure
        with patch("sys.stdout.isatty", return_value=False):
            valid, message = validator.validate()

        assert valid is False
        assert message is not None

        # Create startup error and handle it
        startup_error = StartupError(message)

        with patch.object(error_handler, "handle_fatal_error") as mock_fatal:
            result = error_handler.handle_error(startup_error)

        assert result is False
        mock_fatal.assert_called_once()

    def test_terminal_fallback_workflow(
        self,
        integrated_system: dict[str, Any],
    ) -> None:
        """Test terminal compatibility fallback workflow."""
        error_handler = integrated_system["error_handler"]
        app = integrated_system["app"]

        # Mock app methods for fallback
        app.enter_fallback_mode = Mock()
        app.notify = Mock()

        # Create terminal error
        terminal_error = TerminalError("Terminal not compatible")

        # Handle error (should trigger fallback) - mock sys.exit to prevent termination
        with (
            patch.object(error_handler, "show_error_dialog"),
            patch("sys.exit"),
        ):
            error_handler.handle_error(terminal_error)

        # Verify error was logged
        assert len(error_handler.error_log) == 1

    def test_error_recovery_chain(
        self,
        integrated_system: dict[str, Any],
    ) -> None:
        """Test chained error recovery."""
        error_handler = integrated_system["error_handler"]
        app = integrated_system["app"]

        # Mock recovery methods
        app.theme_manager = Mock()
        app.theme_manager.apply_theme = Mock()
        app.notify = Mock()

        # Create theme error
        theme_error = ThemeError("default")

        result = error_handler.attempt_recovery(theme_error)

        assert result is True
        app.theme_manager.apply_theme.assert_called_with("dark")

    def test_multiple_error_handling(
        self,
        integrated_system: dict[str, Any],
    ) -> None:
        """Test handling multiple errors in sequence."""
        error_handler = integrated_system["error_handler"]

        errors = [
            TUIError("Error 1"),
            RenderingError("widget", "stage"),
            NavigationError("screen1", "screen2"),
            ConfigurationError("Config invalid"),
        ]

        with patch.object(error_handler, "show_error_dialog"):
            for error in errors:
                error_handler.handle_error(error)

        assert len(error_handler.error_log) == EXPECTED_MULTIPLE_ERRORS

        stats = error_handler.get_error_stats()
        assert stats["total_errors"] == EXPECTED_MULTIPLE_ERRORS


# Failure scenario tests
class TestFailureScenarios:
    """Test various failure scenarios."""

    def test_no_terminal_scenario(self) -> None:
        """Test behavior when not running in terminal."""
        validator = StartupValidator()

        with patch("sys.stdout.isatty", return_value=False):
            result = validator.check_terminal_exists()

        assert result is False
        assert "Not running in a terminal" in validator.errors[0]

    def test_tiny_terminal_scenario(self) -> None:
        """Test behavior with very small terminal."""
        validator = StartupValidator()

        with patch("shutil.get_terminal_size") as mock_size:
            # Create a proper namedtuple mock that can be unpacked
            class TerminalSize(NamedTuple):
                columns: int
                lines: int

            mock_size.return_value = TerminalSize(columns=40, lines=10)
            result = validator.check_terminal_size()

        assert result is True  # Just a warning
        assert len(validator.warnings) > 0

    def test_no_color_support_scenario(self) -> None:
        """Test behavior with no color support."""
        validator = StartupValidator()

        with patch.dict("os.environ", {"TERM": "dumb"}):
            result = validator.check_color_support()

        assert result is True
        assert len(validator.warnings) > 0

    def test_missing_dependencies_scenario(self) -> None:
        """Test behavior with missing dependencies."""
        validator = StartupValidator()

        with patch(
            "builtins.__import__",
            side_effect=ImportError("textual not found"),
        ):
            result = validator.check_dependencies()

        assert result is False
        assert "Missing required dependency" in validator.errors[0]

    def test_permission_denied_scenario(self, tmp_path: Path) -> None:
        """Test behavior with permission issues."""
        validator = StartupValidator()

        # Make directory read-only
        restricted_dir = tmp_path / "restricted"
        restricted_dir.mkdir(mode=0o444)

        with patch("pathlib.Path.home", return_value=restricted_dir):
            result = validator.check_permissions()

        # Should handle gracefully
        assert result is False or len(validator.warnings) > 0
