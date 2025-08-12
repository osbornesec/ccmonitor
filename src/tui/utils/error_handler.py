"""Centralized error handling system for the TUI application."""

import json
import logging
import os
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from textual.app import App

from src.tui.exceptions import (
    ConfigurationError,
    RecoverableError,
    RenderingError,
    StartupError,
    TerminalError,
    ThemeError,
    TUIError,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.tui.widgets.error_dialog import ErrorDialog
else:
    # Import error dialog at runtime with fallback
    try:
        from src.tui.widgets.error_dialog import ErrorDialog
    except ImportError:
        ErrorDialog = None

# Constants
MAX_ERROR_THRESHOLD = 3
RECENT_ERROR_COUNT = 5


class ErrorHandler:
    """Centralized error handling for the TUI application."""

    def __init__(self, app: App) -> None:
        """Initialize error handler with app reference."""
        self.app = app
        self.error_log: list[TUIError] = []
        self.recovery_strategies: dict[type, Callable[[Any], None]] = {}
        self.setup_logging()
        self.register_recovery_strategies()

    def setup_logging(self) -> None:
        """Configure error logging."""
        log_dir = Path.home() / ".config" / "ccmonitor" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"tui_{datetime.now(UTC):%Y%m%d_%H%M%S}.log"

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stderr),
            ],
        )

        self.logger = logging.getLogger("ccmonitor.tui")

    def register_recovery_strategies(self) -> None:
        """Register automatic recovery strategies for known errors."""
        self.recovery_strategies = {
            TerminalError: self.recover_from_terminal_error,
            RenderingError: self.recover_from_rendering_error,
            ThemeError: self.recover_from_theme_error,
            ConfigurationError: self.recover_from_config_error,
        }

    def handle_error(self, error: Exception) -> bool:
        """Handle an error, attempting recovery if possible."""
        # Log the error
        self.log_error(error)

        # Check if it's a TUI error
        if not isinstance(error, TUIError):
            error = TUIError(
                f"Unexpected error: {error!s}",
                details={"original_type": type(error).__name__},
            )

        # Add to error history
        self.error_log.append(error)

        # Attempt recovery
        if isinstance(error, RecoverableError):
            return self.attempt_recovery(error)

        # Show error to user
        self.show_error_dialog(error)

        # Fatal errors
        if isinstance(error, (StartupError, TerminalError)):
            self.handle_fatal_error(error)
            return False

        return True

    def log_error(self, error: Exception) -> None:
        """Log error with full context."""
        if isinstance(error, TUIError):
            self.logger.error(
                "TUI Error: %s",
                error.message,
                extra={"error_dict": error.to_dict()},
            )
        else:
            self.logger.error("Unexpected error: %s", error)

    def attempt_recovery(self, error: RecoverableError) -> bool:
        """Attempt to recover from a recoverable error."""
        error_type = type(error)

        if error_type in self.recovery_strategies:
            try:
                self.recovery_strategies[error_type](error)
            except Exception:
                self.logger.exception(
                    "Recovery failed for %s",
                    error_type.__name__,
                )
                return False
            else:
                self.logger.info("Recovered from %s", error_type.__name__)
                return True

        return False

    def recover_from_terminal_error(self, _error: TerminalError) -> None:
        """Recover from terminal compatibility issues."""
        # Switch to fallback mode
        if hasattr(self.app, "enter_fallback_mode"):
            self.app.enter_fallback_mode()
            self.app.notify(
                "Terminal compatibility issue detected. Switched to fallback mode.",
                severity="warning",
            )

    def recover_from_rendering_error(self, _error: RenderingError) -> None:
        """Recover from rendering errors."""
        # Refresh the screen
        self.app.refresh()
        # Reduce visual complexity if needed
        if len(self.error_log) > MAX_ERROR_THRESHOLD and hasattr(
            self.app,
            "reduce_visual_complexity",
        ):
            self.app.reduce_visual_complexity()

    def recover_from_theme_error(self, _error: ThemeError) -> None:
        """Recover from theme loading errors."""
        # Reset to default theme
        if hasattr(self.app, "theme_manager"):
            self.app.theme_manager.apply_theme("dark")
            self.app.notify(
                "Theme loading failed. Reverted to default theme.",
                severity="warning",
            )

    def recover_from_config_error(self, _error: ConfigurationError) -> None:
        """Recover from configuration errors."""
        # Use default configuration
        if hasattr(self.app, "load_default_config"):
            self.app.load_default_config()
            self.app.notify(
                "Configuration error. Using default settings.",
                severity="warning",
            )

    def show_error_dialog(self, error: TUIError) -> None:
        """Display error dialog to user."""
        if ErrorDialog is not None:
            dialog = ErrorDialog(error)
            self.app.push_screen(dialog)
        else:
            # Fallback: use notification if dialog fails
            self.app.notify(f"Error: {error.user_message}", severity="error")

    def handle_fatal_error(self, error: TUIError) -> None:
        """Handle fatal errors that prevent continuation."""
        # Save crash report
        crash_file = self.save_crash_report(error)

        # Show final error message to stderr
        error_msg = [
            f"\n{'='*60}",
            "FATAL ERROR",
            "=" * 60,
            f"Error: {error.message}",
        ]

        if error.details:
            error_msg.append(f"Details: {error.details}")

        error_msg.extend(
            [
                f"\nCrash report saved to: {crash_file}",
                "Please report this issue with the crash report.",
                "=" * 60,
            ],
        )

        # Write to stderr instead of print
        sys.stderr.write("\n".join(error_msg) + "\n")

        # Exit application
        sys.exit(1)

    def save_crash_report(self, error: TUIError) -> Path:
        """Save detailed crash report for debugging."""
        crash_dir = Path.home() / ".config" / "ccmonitor" / "crash_reports"
        crash_dir.mkdir(parents=True, exist_ok=True)

        crash_file = (
            crash_dir / f"crash_{datetime.now(UTC):%Y%m%d_%H%M%S}.json"
        )

        report = {
            "error": error.to_dict(),
            "system_info": self.gather_system_info(),
            "error_history": [e.to_dict() for e in self.error_log[-10:]],
            "app_state": self.get_app_state_snapshot(),
        }

        with crash_file.open("w") as f:
            json.dump(report, f, indent=2, default=str)

        return crash_file

    def gather_system_info(self) -> dict[str, Any]:
        """Gather system information for debugging."""
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "terminal": os.environ.get("TERM", "unknown"),
            "terminal_size": getattr(self.app, "size", None),
            "color_support": os.environ.get("COLORTERM", "unknown"),
            "encoding": sys.stdout.encoding,
        }

    def get_app_state_snapshot(self) -> dict[str, Any]:
        """Get application state snapshot for debugging."""
        try:
            return {
                "screen_stack": [
                    screen.__class__.__name__
                    for screen in getattr(self.app, "screen_stack", [])
                ],
                "current_screen": getattr(
                    self.app.screen,
                    "__class__.__name__",
                    "unknown",
                ),
                "focused_widget": (
                    getattr(self.app.focused, "__class__.__name__", "none")
                    if self.app.focused
                    else "none"
                ),
                "theme": getattr(self.app, "current_theme", "unknown"),
            }
        except Exception:  # noqa: BLE001
            return {"error": "Could not capture app state"}

    def get_error_stats(self) -> dict[str, Any]:
        """Get error statistics for monitoring."""
        if not self.error_log:
            return {"total_errors": 0}

        error_types: dict[str, int] = {}
        for error in self.error_log:
            error_type = type(error).__name__
            error_types[error_type] = error_types.get(error_type, 0) + 1

        return {
            "total_errors": len(self.error_log),
            "error_types": error_types,
            "recent_errors": len(self.error_log[-RECENT_ERROR_COUNT:]),
        }
