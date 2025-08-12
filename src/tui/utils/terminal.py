"""Terminal capability detection and fallback mode handling."""

from __future__ import annotations

import os
import shutil
import sys
from typing import Any


class TerminalCapabilities:
    """Detect and handle terminal capabilities with comprehensive fallback modes."""

    # Color depth constants
    TRUECOLOR_DEPTH = 16777216  # 24-bit color (2^24)
    COLOR_256_DEPTH = 256
    COLOR_16_DEPTH = 16
    COLOR_8_DEPTH = 8
    MONOCHROME_DEPTH = 1

    def __init__(self) -> None:
        """Initialize terminal capabilities detector."""
        self.capabilities = self.detect_capabilities()

    def detect_capabilities(self) -> dict[str, Any]:
        """Detect current terminal capabilities comprehensively."""
        return {
            "colors": self.detect_color_support(),
            "unicode": self.detect_unicode_support(),
            "mouse": self.detect_mouse_support(),
            "size": self.get_terminal_size(),
            "term_type": os.environ.get("TERM", "unknown"),
            "is_tty": sys.stdout.isatty(),
            "colorterm": os.environ.get("COLORTERM", ""),
            "supports_truecolor": self._supports_truecolor(),
            "supports_256_color": self._supports_256_color(),
            "terminal_program": self._detect_terminal_program(),
        }

    def detect_color_support(self) -> int:
        """Detect number of colors supported by terminal."""
        term = os.environ.get("TERM", "").lower()

        # Check for truecolor support first
        if self._supports_truecolor():
            return self.TRUECOLOR_DEPTH

        # Check for 256 color support
        if self._supports_256_color():
            return self.COLOR_256_DEPTH

        # Check for 16 color support
        if any(
            indicator in term for indicator in ["color", "xterm", "screen"]
        ):
            return self.COLOR_16_DEPTH

        # Basic 8 color support
        if term and not term.startswith(("dumb", "unknown")):
            return self.COLOR_8_DEPTH

        # Monochrome fallback
        return self.MONOCHROME_DEPTH

    def _supports_truecolor(self) -> bool:
        """Check if terminal supports 24-bit truecolor."""
        colorterm = os.environ.get("COLORTERM", "").lower()
        term_program = os.environ.get("TERM_PROGRAM", "").lower()

        # Explicit truecolor indicators
        if any(indicator in colorterm for indicator in ["truecolor", "24bit"]):
            return True

        # Known truecolor supporting terminals
        truecolor_terminals = {
            "iterm.app",
            "hyper",
            "mintty",
            "konsole",
            "gnome-terminal",
        }

        return term_program in truecolor_terminals

    def _supports_256_color(self) -> bool:
        """Check if terminal supports 256 colors."""
        term = os.environ.get("TERM", "").lower()

        # Explicit 256 color indicators
        if "256" in term or "256color" in term:
            return True

        # Terminals that typically support 256 colors
        color_256_terms = {
            "xterm-256color",
            "screen-256color",
            "tmux-256color",
        }

        return term in color_256_terms or any(
            indicator in term for indicator in ["xterm", "screen", "tmux"]
        )

    def detect_unicode_support(self) -> bool:
        """Check if terminal supports Unicode characters."""
        try:
            # Try to encode common Unicode characters
            test_chars = ["🖥️", "→", "←", "↑", "↓", "★", "●", "◆"]
            encoding = sys.stdout.encoding or "utf-8"

            for char in test_chars:
                char.encode(encoding)

            # Check locale settings
            locale_vars = ["LC_ALL", "LC_CTYPE", "LANG"]
            for var in locale_vars:
                locale_val = os.environ.get(var, "").upper()
                if "UTF-8" in locale_val or "UTF8" in locale_val:
                    return True

        except (UnicodeEncodeError, AttributeError):
            return False

        return True

    def detect_mouse_support(self) -> bool:
        """Check if terminal supports mouse input."""
        term = os.environ.get("TERM", "").lower()
        term_program = os.environ.get("TERM_PROGRAM", "").lower()

        # Terminals known to support mouse input
        mouse_support_terms = {
            "xterm",
            "screen",
            "tmux",
            "alacritty",
            "kitty",
            "iterm",
            "gnome",
            "konsole",
            "terminal",
        }

        return any(
            term_type in term for term_type in mouse_support_terms
        ) or any(program in term_program for program in mouse_support_terms)

    def get_terminal_size(self) -> tuple[int, int]:
        """Get current terminal size with robust fallback."""
        try:
            # Try shutil first (most reliable)
            size = shutil.get_terminal_size()
        except (OSError, AttributeError):
            pass
        else:
            return (size.columns, size.lines)

        try:
            # Try os environment variables
            cols = int(os.environ.get("COLUMNS", "0"))
            lines = int(os.environ.get("LINES", "0"))
            if cols > 0 and lines > 0:
                return (cols, lines)
        except (ValueError, TypeError):
            pass

        # Standard fallback size
        return (80, 24)

    def _detect_terminal_program(self) -> str:
        """Detect the terminal program being used."""
        # Check various environment variables
        env_vars = ["TERM_PROGRAM", "TERMINAL_EMULATOR", "COLORTERM"]

        for var in env_vars:
            value = os.environ.get(var, "")
            if value:
                return value.lower()

        # Try to infer from TERM
        return self._infer_from_term_variable()

    def _infer_from_term_variable(self) -> str:
        """Infer terminal program from TERM environment variable."""
        term = os.environ.get("TERM", "").lower()

        term_mapping = {
            "iterm": "iterm2",
            "alacritty": "alacritty",
            "kitty": "kitty",
        }

        for term_indicator, program_name in term_mapping.items():
            if term_indicator in term:
                return program_name

        return "unknown"

    def get_fallback_mode(self) -> str:
        """Determine appropriate fallback mode based on capabilities."""
        caps = self.capabilities

        # Headless mode (no TTY)
        if not caps["is_tty"]:
            return "headless"

        # Very limited terminals
        if caps["colors"] <= self.MONOCHROME_DEPTH:
            return "monochrome"

        # No Unicode support
        if not caps["unicode"]:
            return "ascii"

        # Limited color support
        if caps["colors"] < self.COLOR_16_DEPTH:
            return "limited_color"

        # Normal mode
        return "normal"

    def get_optimal_settings(self) -> dict[str, Any]:
        """Get optimal settings based on terminal capabilities."""
        caps = self.capabilities
        fallback_mode = self.get_fallback_mode()

        settings = {
            "use_colors": caps["colors"] > self.MONOCHROME_DEPTH,
            "use_unicode": caps["unicode"],
            "use_mouse": caps["mouse"],
            "color_depth": caps["colors"],
            "fallback_mode": fallback_mode,
        }

        # Adjust settings based on fallback mode
        if fallback_mode == "headless":
            settings.update(
                {
                    "use_colors": False,
                    "use_unicode": False,
                    "use_mouse": False,
                },
            )
        elif fallback_mode == "monochrome":
            settings.update(
                {
                    "use_colors": False,
                    "use_unicode": caps[
                        "unicode"
                    ],  # Keep Unicode if supported
                },
            )
        elif fallback_mode == "ascii":
            settings.update(
                {
                    "use_unicode": False,
                    "use_colors": caps["colors"] > self.MONOCHROME_DEPTH,
                },
            )
        elif fallback_mode == "limited_color":
            settings.update(
                {
                    "color_depth": min(caps["colors"], self.COLOR_16_DEPTH),
                },
            )

        return settings

    def supports_feature(self, feature: str) -> bool:
        """Check if terminal supports a specific feature."""
        feature_map = {
            "colors": self.capabilities["colors"] > self.MONOCHROME_DEPTH,
            "truecolor": self.capabilities["colors"] >= self.TRUECOLOR_DEPTH,
            "256color": self.capabilities["colors"] >= self.COLOR_256_DEPTH,
            "unicode": self.capabilities["unicode"],
            "mouse": self.capabilities["mouse"],
            "tty": self.capabilities["is_tty"],
        }

        return bool(feature_map.get(feature.lower(), False))

    def _get_color_description(self, color_count: int) -> str:
        """Get human-readable color capability description."""
        if color_count >= self.TRUECOLOR_DEPTH:
            return "24-bit truecolor"
        if color_count >= self.COLOR_256_DEPTH:
            return "256 colors"
        if color_count >= self.COLOR_16_DEPTH:
            return "16 colors"
        if color_count >= self.COLOR_8_DEPTH:
            return "8 colors"
        return "monochrome"

    def get_capability_summary(self) -> str:
        """Get a human-readable summary of terminal capabilities."""
        caps = self.capabilities

        color_desc = self._get_color_description(caps["colors"])

        features = []
        if caps["unicode"]:
            features.append("Unicode")
        if caps["mouse"]:
            features.append("Mouse")
        if caps["is_tty"]:
            features.append("TTY")

        feature_str = ", ".join(features) if features else "Basic"

        return (
            f"Terminal: {caps['terminal_program']} ({caps['term_type']}) - "
            f"{color_desc}, {feature_str} - "
            f"Size: {caps['size'][0]}x{caps['size'][1]}"
        )


# Global terminal capabilities instance
terminal_capabilities = TerminalCapabilities()


def get_terminal_capabilities() -> TerminalCapabilities:
    """Get the global terminal capabilities instance."""
    return terminal_capabilities


def refresh_terminal_capabilities() -> TerminalCapabilities:
    """Refresh terminal capabilities detection (useful after environment changes)."""
    global terminal_capabilities  # noqa: PLW0603
    terminal_capabilities = TerminalCapabilities()
    return terminal_capabilities
