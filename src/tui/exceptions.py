"""TUI-specific exception hierarchy with contextual error handling."""

import traceback
from datetime import UTC, datetime
from typing import Any


class TUIError(Exception):
    """Base exception for TUI-related errors with contextual information."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
    ) -> None:
        """Initialize TUI error with contextual information."""
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.user_message = user_message or message
        self.timestamp = datetime.now(UTC)
        self.traceback = traceback.format_exc()

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for logging."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "user_message": self.user_message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "traceback": self.traceback,
        }


class StartupError(TUIError):
    """Raised when application fails to start properly."""


class TerminalError(TUIError):
    """Raised when terminal capabilities are inadequate."""

    def __init__(
        self,
        message: str,
        terminal_info: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
    ) -> None:
        """Initialize terminal error with terminal capability information."""
        super().__init__(message, details=details, user_message=user_message)
        self.terminal_info = terminal_info or {}


class RenderingError(TUIError):
    """Raised when widget rendering encounters issues."""

    def __init__(
        self,
        widget_id: str,
        render_stage: str,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
    ) -> None:
        """Initialize rendering error with widget and stage information."""
        message = f"Rendering failed for widget '{widget_id}' at stage '{render_stage}'"
        super().__init__(message, details=details, user_message=user_message)
        self.widget_id = widget_id
        self.render_stage = render_stage


class NavigationError(TUIError):
    """Raised when screen/widget navigation fails."""

    def __init__(
        self,
        from_screen: str,
        to_screen: str,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
    ) -> None:
        """Initialize navigation error with screen transition information."""
        message = f"Navigation failed from '{from_screen}' to '{to_screen}'"
        super().__init__(message, details=details, user_message=user_message)
        self.from_screen = from_screen
        self.to_screen = to_screen


class ConfigurationError(TUIError):
    """Raised when configuration is invalid or missing."""


class ThemeError(TUIError):
    """Raised when theme loading or application fails."""

    def __init__(
        self,
        theme_name: str,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
    ) -> None:
        """Initialize theme error with theme name information."""
        message = f"Theme '{theme_name}' could not be loaded or applied"
        super().__init__(message, details=details, user_message=user_message)
        self.theme_name = theme_name


class RecoverableError(TUIError):
    """Base for errors that allow automatic recovery."""

    def __init__(
        self,
        message: str,
        recovery_action: str | None = None,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
    ) -> None:
        """Initialize recoverable error with recovery action information."""
        super().__init__(message, details=details, user_message=user_message)
        self.recovery_action = recovery_action
