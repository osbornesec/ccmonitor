"""Application startup validation for CCMonitor TUI."""

from __future__ import annotations

import os
import shutil


class StartupValidator:
    """Validator for application startup requirements."""

    MIN_TERMINAL_WIDTH = 80
    MIN_TERMINAL_HEIGHT = 24

    def __init__(self) -> None:
        """Initialize startup validator."""
        self.errors: list[str] = []

    def validate_terminal_capabilities(self) -> bool:
        """Validate terminal capabilities."""
        # Check terminal size
        try:
            size = shutil.get_terminal_size()
            if (
                size.columns < self.MIN_TERMINAL_WIDTH
                or size.lines < self.MIN_TERMINAL_HEIGHT
            ):
                error_msg = (
                    f"Terminal too small (minimum {self.MIN_TERMINAL_WIDTH}"
                    f"x{self.MIN_TERMINAL_HEIGHT})"
                )
                self.errors.append(error_msg)
                return False
        except OSError:
            self.errors.append("Unable to determine terminal size")
            return False

        return True

    def validate_environment(self) -> bool:
        """Validate environment requirements."""
        # Check for required environment variables or configurations
        if not os.environ.get("TERM"):
            self.errors.append("TERM environment variable not set")
            return False

        return True

    def validate_all(self) -> bool:
        """Run all validation checks."""
        self.errors.clear()
        terminal_ok = self.validate_terminal_capabilities()
        env_ok = self.validate_environment()
        return terminal_ok and env_ok

    def get_errors(self) -> list[str]:
        """Get validation errors."""
        return self.errors.copy()
