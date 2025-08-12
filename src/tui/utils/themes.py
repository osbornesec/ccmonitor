"""Advanced theme management system for CCMonitor TUI.

This module provides a comprehensive theming system with:
- ColorScheme dataclass defining all color properties
- Built-in professional themes (dark, light, monokai, solarized)
- Custom theme loading from user configuration
- CSS generation for Textual integration
- Color accessibility validation
- Terminal capability detection
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import ClassVar

logger = logging.getLogger(__name__)

# Constants for accessibility and color validation
WCAG_AA_RATIO = 4.5
GAMMA_CORRECTION_THRESHOLD = 0.03928
GAMMA_DIVISOR = 12.92
GAMMA_OFFSET = 0.055
GAMMA_SCALE = 1.055
GAMMA_POWER = 2.4
RGB_SHORT_HEX_LENGTH = 3
LUMINANCE_RED_WEIGHT = 0.2126
LUMINANCE_GREEN_WEIGHT = 0.7152
LUMINANCE_BLUE_WEIGHT = 0.0722


@dataclass
class ColorScheme:
    """Comprehensive color scheme definition for the application.

    Defines all colors used throughout the CCMonitor TUI with proper
    categorization for maintainable theming.
    """

    # Base semantic colors
    primary: str = "#0066CC"
    secondary: str = "#6C757D"
    success: str = "#28A745"
    warning: str = "#FFC107"
    danger: str = "#DC3545"
    info: str = "#17A2B8"

    # UI foundation colors
    background: str = "#1E1E1E"
    surface: str = "#2D2D30"
    panel: str = "#252526"
    border: str = "#3E3E42"
    accent: str = "#007ACC"

    # Text colors
    text: str = "#CCCCCC"
    text_muted: str = "#858585"
    foreground_muted: str = "#9D9D9D"

    # Message type colors for conversation display
    user_message: str = "#0066CC"
    assistant_message: str = "#28A745"
    system_message: str = "#FFC107"
    tool_message: str = "#FF6B35"
    error_message: str = "#DC3545"

    # Syntax highlighting colors
    syntax_keyword: str = "#569CD6"
    syntax_string: str = "#CE9178"
    syntax_number: str = "#B5CEA8"
    syntax_comment: str = "#6A9955"
    syntax_function: str = "#DCDCAA"
    syntax_type: str = "#4EC9B0"
    syntax_operator: str = "#D4D4D4"

    # Status and state colors
    status_online: str = "#28A745"
    status_offline: str = "#DC3545"
    status_loading: str = "#17A2B8"
    status_paused: str = "#FFC107"

    # Enhanced focus and interaction colors
    focus_primary: str = "#007ACC"
    focus_secondary: str = "#FF6B35"
    hover_background: str = "#2D2D30"

    # Additional utility colors
    error: str = "#DC3545"
    primary_lighten_1: str = "#1976D2"

    def __post_init__(self) -> None:
        """Validate color format after initialization."""
        for field_name, color_value in asdict(self).items():
            if not self._is_valid_color(color_value):
                logger.warning(
                    "Invalid color format for %s: %s",
                    field_name,
                    color_value,
                )

    @staticmethod
    def _is_valid_color(color: str) -> bool:
        """Validate hex color format."""
        if not isinstance(color, str):
            return False
        return bool(
            color.startswith("#")
            and len(color) in (4, 7)
            and all(c in "0123456789ABCDEFabcdef" for c in color[1:]),
        )

    def get_contrast_ratio(self, color1: str, color2: str) -> float:
        """Calculate WCAG contrast ratio between two colors."""
        try:
            lum1 = self._get_luminance(color1)
            lum2 = self._get_luminance(color2)
            return (max(lum1, lum2) + 0.05) / (min(lum1, lum2) + 0.05)
        except (ValueError, ZeroDivisionError):
            return 1.0

    def _get_luminance(self, hex_color: str) -> float:
        """Calculate relative luminance of a color."""
        # Remove # and convert to RGB
        rgb_hex = hex_color.lstrip("#")
        if len(rgb_hex) == RGB_SHORT_HEX_LENGTH:
            rgb_hex = "".join(c * 2 for c in rgb_hex)

        rgb = [int(rgb_hex[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]

        # Apply gamma correction
        rgb_linear = [
            (
                val / GAMMA_DIVISOR
                if val <= GAMMA_CORRECTION_THRESHOLD
                else ((val + GAMMA_OFFSET) / GAMMA_SCALE) ** GAMMA_POWER
            )
            for val in rgb
        ]

        # Calculate luminance
        return (
            LUMINANCE_RED_WEIGHT * rgb_linear[0]
            + LUMINANCE_GREEN_WEIGHT * rgb_linear[1]
            + LUMINANCE_BLUE_WEIGHT * rgb_linear[2]
        )

    def validate_accessibility(self) -> dict[str, bool]:
        """Validate WCAG AA compliance for text/background combinations."""
        validations = {}

        # Key text/background combinations
        combinations = [
            ("text", "background"),
            ("text", "surface"),
            ("text", "panel"),
            ("text_muted", "background"),
            ("primary", "background"),
            ("error_message", "background"),
        ]

        for text_color, bg_color in combinations:
            text_val = getattr(self, text_color, "#000000")
            bg_val = getattr(self, bg_color, "#FFFFFF")
            ratio = self.get_contrast_ratio(text_val, bg_val)
            validations[f"{text_color}_on_{bg_color}"] = ratio >= WCAG_AA_RATIO

        return validations


class ThemeManager:
    """Advanced theme manager with comprehensive color scheme support.

    Manages built-in and custom themes, provides CSS generation,
    validates accessibility, and handles terminal capabilities.
    """

    # Built-in professional themes
    THEMES: ClassVar[dict[str, ColorScheme]] = {
        "dark": ColorScheme(),  # Default dark theme
        "light": ColorScheme(
            # Light theme with inverted colors
            background="#FFFFFF",
            surface="#F8F9FA",
            panel="#F5F5F5",
            border="#DEE2E6",
            text="#212529",
            text_muted="#6C757D",
            foreground_muted="#495057",
            primary="#0D6EFD",
            secondary="#6C757D",
            accent="#0B5ED7",
            user_message="#0D6EFD",
            assistant_message="#198754",
            system_message="#FFC107",
            tool_message="#FD7E14",
            error_message="#DC3545",
            hover_background="#E9ECEF",
            focus_primary="#0D6EFD",
            primary_lighten_1="#0B5ED7",
        ),
        "monokai": ColorScheme(
            # Popular Monokai theme
            background="#272822",
            surface="#3E3D32",
            panel="#49483E",
            border="#75715E",
            text="#F8F8F2",
            text_muted="#75715E",
            foreground_muted="#8F908A",
            primary="#66D9EF",
            secondary="#75715E",
            accent="#A6E22E",
            user_message="#66D9EF",
            assistant_message="#A6E22E",
            system_message="#E6DB74",
            tool_message="#FD971F",
            error_message="#F92672",
            success="#A6E22E",
            warning="#E6DB74",
            danger="#F92672",
            info="#66D9EF",
            syntax_keyword="#F92672",
            syntax_string="#E6DB74",
            syntax_number="#AE81FF",
            syntax_comment="#75715E",
            syntax_function="#A6E22E",
            syntax_type="#66D9EF",
            hover_background="#49483E",
            focus_primary="#66D9EF",
            primary_lighten_1="#75D7F0",
        ),
        "solarized": ColorScheme(
            # Solarized dark theme
            background="#002B36",
            surface="#073642",
            panel="#0B404C",
            border="#586E75",
            text="#839496",
            text_muted="#657B83",
            foreground_muted="#586E75",
            primary="#268BD2",
            secondary="#586E75",
            accent="#2AA198",
            user_message="#268BD2",
            assistant_message="#859900",
            system_message="#B58900",
            tool_message="#CB4B16",
            error_message="#DC322F",
            success="#859900",
            warning="#B58900",
            danger="#DC322F",
            info="#268BD2",
            syntax_keyword="#719E07",
            syntax_string="#2AA198",
            syntax_number="#D33682",
            syntax_comment="#586E75",
            syntax_function="#B58900",
            syntax_type="#268BD2",
            hover_background="#0B404C",
            focus_primary="#268BD2",
            primary_lighten_1="#3294DC",
        ),
    }

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize theme manager.

        Args:
            config_dir: Optional custom config directory path

        """
        self.current_theme = "dark"
        self.config_dir = config_dir or Path.home() / ".config" / "ccmonitor"
        self.custom_themes: dict[str, ColorScheme] = {}
        self.terminal_colors = self._detect_terminal_capabilities()

        # Load custom themes
        self._load_custom_themes()

        logger.info(
            "ThemeManager initialized with %d built-in and %d custom themes",
            len(self.THEMES),
            len(self.custom_themes),
        )

    def _detect_terminal_capabilities(self) -> dict[str, bool]:
        """Detect terminal color capabilities."""
        capabilities = {
            "24bit": False,
            "256color": False,
            "16color": True,  # Assume basic color support
        }

        # Check environment variables
        colorterm = os.environ.get("COLORTERM", "").lower()
        term = os.environ.get("TERM", "").lower()

        # 24-bit color support
        if colorterm in ("truecolor", "24bit") or "24bit" in term:
            capabilities["24bit"] = True
            capabilities["256color"] = True
        elif "256" in term or colorterm == "256":
            capabilities["256color"] = True

        # Windows Terminal detection
        if os.environ.get("WT_SESSION"):
            capabilities["24bit"] = True
            capabilities["256color"] = True

        logger.debug("Detected terminal capabilities: %s", capabilities)
        return capabilities

    def _load_custom_themes(self) -> None:
        """Load user-defined custom themes from configuration."""
        themes_file = self.config_dir / "themes.json"

        if not themes_file.exists():
            logger.debug("No custom themes file found")
            return

        try:
            with themes_file.open(encoding="utf-8") as f:
                data = json.load(f)

            self._process_theme_data(data)

        except (json.JSONDecodeError, OSError):
            logger.exception("Failed to load custom themes")

    def _process_theme_data(self, data: dict) -> None:
        """Process theme data and load valid themes."""
        for name, theme_data in data.items():
            if not isinstance(theme_data, dict):
                logger.warning("Invalid theme data for '%s': not a dict", name)
                continue

            try:
                self.custom_themes[name] = ColorScheme(**theme_data)
                logger.debug("Loaded custom theme: %s", name)
            except (TypeError, ValueError):
                logger.exception("Failed to load custom theme '%s'", name)

    def get_available_themes(self) -> list[str]:
        """Get list of all available theme names."""
        return list(self.THEMES.keys()) + list(self.custom_themes.keys())

    def get_theme(self, name: str) -> ColorScheme:
        """Get theme by name.

        Args:
            name: Theme name to retrieve

        Returns:
            ColorScheme instance, defaults to 'dark' if not found

        """
        # Check custom themes first
        if name in self.custom_themes:
            return self.custom_themes[name]

        # Fall back to built-in themes
        theme = self.THEMES.get(name)
        if theme is None:
            logger.warning("Theme '%s' not found, using default 'dark'", name)
            return self.THEMES["dark"]

        return theme

    def set_theme(self, name: str) -> bool:
        """Set the current active theme.

        Args:
            name: Theme name to activate

        Returns:
            True if theme was set successfully

        """
        if name not in self.get_available_themes():
            logger.error("Theme '%s' not available", name)
            return False

        old_theme = self.current_theme
        self.current_theme = name

        logger.info("Theme changed from '%s' to '%s'", old_theme, name)
        return True

    def generate_css(self, theme_name: str | None = None) -> str:
        """Generate complete CSS for a theme.

        Args:
            theme_name: Theme to generate CSS for, uses current if None

        Returns:
            Complete CSS string with CSS variables and styles

        """
        name = theme_name or self.current_theme
        theme = self.get_theme(name)

        css_vars = self._generate_css_variables(theme)
        css_classes = self._generate_css_classes(theme)

        return f"""/* Auto-generated theme CSS for '{name}' */
/* Generated by CCMonitor ThemeManager */

/* ================================
   CSS VARIABLES
   ================================ */
:root {{
{css_vars}
}}

/* ================================
   MESSAGE TYPE CLASSES
   ================================ */
{css_classes}

/* ================================
   SCREEN BASE STYLES
   ================================ */
Screen {{
    background: {theme.background};
    color: {theme.text};
}}

/* ================================
   STATUS INDICATOR CLASSES
   ================================ */
.status-online {{
    color: {theme.status_online};
}}

.status-offline {{
    color: {theme.status_offline};
}}

.status-loading {{
    color: {theme.status_loading};
}}

.status-paused {{
    color: {theme.status_paused};
}}
"""

    def _generate_css_variables(self, theme: ColorScheme) -> str:
        """Generate CSS custom properties from theme colors."""
        vars_lines = []

        # Convert all theme colors to CSS variables
        for field_name, color_value in asdict(theme).items():
            css_var_name = field_name.replace("_", "-")
            vars_lines.append(f"    --{css_var_name}: {color_value};")

        return "\n".join(vars_lines)

    def _generate_css_classes(self, theme: ColorScheme) -> str:
        """Generate CSS classes for message types and utilities."""
        classes = [
            # Message type classes
            f".message-user {{ color: {theme.user_message}; }}",
            f".message-assistant {{ color: {theme.assistant_message}; }}",
            f".message-system {{ color: {theme.system_message}; }}",
            f".message-tool {{ color: {theme.tool_message}; }}",
            f".message-error {{ color: {theme.error_message}; }}",
            "",
            # Syntax highlighting classes
            f".syntax-keyword {{ color: {theme.syntax_keyword}; }}",
            f".syntax-string {{ color: {theme.syntax_string}; }}",
            f".syntax-number {{ color: {theme.syntax_number}; }}",
            f".syntax-comment {{ color: {theme.syntax_comment}; }}",
            f".syntax-function {{ color: {theme.syntax_function}; }}",
            f".syntax-type {{ color: {theme.syntax_type}; }}",
        ]

        return "\n".join(classes)

    def validate_theme_accessibility(
        self,
        theme_name: str | None = None,
    ) -> dict[str, bool]:
        """Validate theme accessibility compliance.

        Args:
            theme_name: Theme to validate, uses current if None

        Returns:
            Dict of validation results for different text/background combinations

        """
        name = theme_name or self.current_theme
        theme = self.get_theme(name)

        return theme.validate_accessibility()

    def get_fallback_colors(self) -> dict[str, str]:
        """Get fallback colors for limited terminal capabilities."""
        if not self.terminal_colors["256color"]:
            # 16-color fallback
            return {
                "primary": "blue",
                "secondary": "white",
                "success": "green",
                "warning": "yellow",
                "danger": "red",
                "info": "cyan",
                "text": "white",
                "background": "black",
            }

        # Use full color scheme for capable terminals
        theme = self.get_theme(self.current_theme)
        return asdict(theme)

    def save_custom_theme(self, name: str, theme: ColorScheme) -> bool:
        """Save a custom theme to user configuration.

        Args:
            name: Theme name to save
            theme: ColorScheme instance to save

        Returns:
            True if saved successfully

        """
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)

            themes_file = self.config_dir / "themes.json"

            # Load existing themes
            existing_themes = {}
            if themes_file.exists():
                with themes_file.open(encoding="utf-8") as f:
                    existing_themes = json.load(f)

            # Add new theme
            existing_themes[name] = asdict(theme)

            # Save updated themes
            with themes_file.open("w", encoding="utf-8") as f:
                json.dump(existing_themes, f, indent=2)

            # Update in-memory cache
            self.custom_themes[name] = theme

        except (OSError, json.JSONDecodeError):
            logger.exception("Failed to save custom theme '%s'", name)
            return False
        else:
            logger.info("Custom theme '%s' saved successfully", name)
            return True

    def delete_custom_theme(self, name: str) -> bool:
        """Delete a custom theme.

        Args:
            name: Theme name to delete

        Returns:
            True if deleted successfully

        """
        if name not in self.custom_themes:
            logger.warning("Custom theme '%s' not found", name)
            return False

        try:
            self._delete_theme_from_file(name)
            del self.custom_themes[name]

        except (OSError, json.JSONDecodeError):
            logger.exception("Failed to delete custom theme '%s'", name)
            return False
        else:
            logger.info("Custom theme '%s' deleted successfully", name)
            return True

    def _delete_theme_from_file(self, name: str) -> None:
        """Delete theme from themes.json file."""
        themes_file = self.config_dir / "themes.json"

        if not themes_file.exists():
            return

        with themes_file.open(encoding="utf-8") as f:
            existing_themes = json.load(f)

        if name in existing_themes:
            del existing_themes[name]

            with themes_file.open("w", encoding="utf-8") as f:
                json.dump(existing_themes, f, indent=2)

    def get_current_theme(self) -> ColorScheme:
        """Get the currently active theme."""
        return self.get_theme(self.current_theme)

    def generate_theme_preview(self, theme_name: str) -> str:
        """Generate a text preview of a theme's colors.

        Args:
            theme_name: Theme to preview

        Returns:
            Formatted string showing theme colors

        """
        theme = self.get_theme(theme_name)

        lines = [
            f"Theme: {theme_name}",
            "=" * 40,
            f"Primary:      {theme.primary}",
            f"Secondary:    {theme.secondary}",
            f"Background:   {theme.background}",
            f"Surface:      {theme.surface}",
            f"Text:         {theme.text}",
            "",
            "Message Colors:",
            f"  User:       {theme.user_message}",
            f"  Assistant:  {theme.assistant_message}",
            f"  System:     {theme.system_message}",
            f"  Tool:       {theme.tool_message}",
            f"  Error:      {theme.error_message}",
        ]

        return "\n".join(lines)
