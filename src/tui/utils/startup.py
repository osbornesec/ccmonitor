"""Application startup validation for CCMonitor TUI."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Any


class StartupValidator:
    """Validates environment before starting TUI."""

    def __init__(self) -> None:
        """Initialize startup validator."""
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate(self) -> tuple[bool, str | None]:
        """Perform all startup validations."""
        checks = [
            self.check_terminal_exists,
            self.check_terminal_size,
            self.check_color_support,
            self.check_unicode_support,
            self.check_dependencies,
            self.check_permissions,
            self.check_configuration,
        ]

        for check in checks:
            if not check() and self.errors:
                return False, "; ".join(self.errors)

        return True, None

    def check_terminal_exists(self) -> bool:
        """Check if running in a terminal."""
        if not sys.stdout.isatty():
            self.errors.append(
                "Not running in a terminal. Please run in a terminal emulator.",
            )
            return False
        return True

    def check_terminal_size(self) -> bool:
        """Check if terminal is large enough."""
        try:
            cols, rows = shutil.get_terminal_size()

            if cols < 80 or rows < 24:  # noqa: PLR2004
                self.warnings.append(
                    f"Terminal size ({cols}x{rows}) is below "
                    "recommended minimum (80x24)",
                )
                # Not a fatal error, just a warning
        except OSError:
            self.warnings.append("Could not determine terminal size")

        return True

    def check_color_support(self) -> bool:
        """Check terminal color capabilities."""
        term = os.environ.get("TERM", "")

        if "dumb" in term:
            self.warnings.append(
                "Terminal does not support colors. Using monochrome mode.",
            )

        return True

    def check_unicode_support(self) -> bool:
        """Check if terminal supports Unicode."""
        try:
            test_chars = "🖥️ ✓ ⌘"
            test_chars.encode(sys.stdout.encoding or "utf-8")
        except (UnicodeEncodeError, AttributeError):
            self.warnings.append(
                "Terminal may not support Unicode. Using ASCII fallback.",
            )

        return True

    def check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        try:
            import rich  # noqa: F401, PLC0415
            import textual  # noqa: F401, PLC0415
        except ImportError as e:
            self.errors.append(f"Missing required dependency: {e}")
            return False

        return True

    def check_permissions(self) -> bool:
        """Check file system permissions."""
        config_dir = Path.home() / ".config" / "ccmonitor"

        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            test_file = config_dir / ".test"
            test_file.touch()
            test_file.unlink()
        except PermissionError:
            self.errors.append(
                f"No write permission to config directory: {config_dir}",
            )
            return False
        except Exception as e:  # noqa: BLE001
            self.warnings.append(f"Permission check warning: {e}")

        return True

    def check_configuration(self) -> bool:
        """Check if configuration is valid."""
        config_file = Path.home() / ".config" / "ccmonitor" / "config.yaml"

        if config_file.exists():
            try:
                import yaml  # noqa: PLC0415

                with config_file.open() as f:
                    yaml.safe_load(f)
            except Exception as e:  # noqa: BLE001
                self.warnings.append(
                    f"Configuration file error: {e}. Using defaults.",
                )

        return True

    def get_validation_report(self) -> dict[str, Any]:
        """Get comprehensive validation report."""
        return {
            "errors": self.errors.copy(),
            "warnings": self.warnings.copy(),
            "has_errors": bool(self.errors),
            "has_warnings": bool(self.warnings),
        }

    # Legacy methods for backward compatibility
    def validate_terminal_capabilities(self) -> bool:
        """Validate terminal capabilities (legacy method)."""
        return self.check_terminal_size() and self.check_color_support()

    def validate_environment(self) -> bool:
        """Validate environment requirements (legacy method)."""
        return self.check_terminal_exists() and self.check_dependencies()

    def validate_all(self) -> bool:
        """Run all validation checks (legacy method)."""
        valid, _ = self.validate()
        return valid

    def get_errors(self) -> list[str]:
        """Get validation errors (legacy method)."""
        return self.errors.copy()
