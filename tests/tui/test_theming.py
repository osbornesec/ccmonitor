"""Comprehensive tests for the theme system and color scheme management."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from src.tui.utils.themes import ColorScheme, ThemeManager

if TYPE_CHECKING:
    from collections.abc import Generator

# Test constants
EPSILON = 0.01  # For floating-point comparisons
HIGH_CONTRAST_THRESHOLD = 15.0  # Expected high contrast ratio


class TestColorScheme:
    """Test suite for ColorScheme dataclass with comprehensive coverage."""

    def test_color_scheme_initialization_default_values(self) -> None:
        """Test ColorScheme initialization with default values."""
        scheme = ColorScheme()

        # Test base semantic colors
        assert scheme.primary == "#0066CC"
        assert scheme.secondary == "#6C757D"
        assert scheme.success == "#28A745"
        assert scheme.warning == "#FFC107"
        assert scheme.danger == "#DC3545"
        assert scheme.info == "#17A2B8"

        # Test UI foundation colors
        assert scheme.background == "#1E1E1E"
        assert scheme.surface == "#2D2D30"
        assert scheme.panel == "#252526"
        assert scheme.border == "#3E3E42"
        assert scheme.accent == "#007ACC"

        # Test text colors
        assert scheme.text == "#CCCCCC"
        assert scheme.text_muted == "#858585"
        assert scheme.foreground_muted == "#9D9D9D"

    def test_color_scheme_initialization_custom_values(self) -> None:
        """Test ColorScheme initialization with custom values."""
        custom_scheme = ColorScheme(
            primary="#FF0000",
            background="#000000",
            text="#FFFFFF",
            user_message="#00FF00",
            assistant_message="#0000FF",
        )

        assert custom_scheme.primary == "#FF0000"
        assert custom_scheme.background == "#000000"
        assert custom_scheme.text == "#FFFFFF"
        assert custom_scheme.user_message == "#00FF00"
        assert custom_scheme.assistant_message == "#0000FF"

        # Ensure other values remain default
        assert custom_scheme.secondary == "#6C757D"
        assert custom_scheme.success == "#28A745"

    def test_color_scheme_message_type_colors(self) -> None:
        """Test message type color assignments."""
        scheme = ColorScheme()

        assert scheme.user_message == "#0066CC"
        assert scheme.assistant_message == "#28A745"
        assert scheme.system_message == "#FFC107"
        assert scheme.tool_message == "#FF6B35"
        assert scheme.error_message == "#DC3545"

    def test_color_scheme_syntax_highlighting_colors(self) -> None:
        """Test syntax highlighting color assignments."""
        scheme = ColorScheme()

        assert scheme.syntax_keyword == "#569CD6"
        assert scheme.syntax_string == "#CE9178"
        assert scheme.syntax_number == "#B5CEA8"
        assert scheme.syntax_comment == "#6A9955"
        assert scheme.syntax_function == "#DCDCAA"
        assert scheme.syntax_type == "#4EC9B0"
        assert scheme.syntax_operator == "#D4D4D4"

    def test_color_scheme_status_colors(self) -> None:
        """Test status indicator color assignments."""
        scheme = ColorScheme()

        assert scheme.status_online == "#28A745"
        assert scheme.status_offline == "#DC3545"
        assert scheme.status_loading == "#17A2B8"
        assert scheme.status_paused == "#FFC107"

    @pytest.mark.parametrize(
        ("color", "expected"),
        [
            ("#FF0000", True),  # Valid 6-char hex
            ("#F00", True),  # Valid 3-char hex
            ("#123ABC", True),  # Valid mixed case
            ("#abc", True),  # Valid lowercase
            ("FF0000", False),  # Missing #
            ("#GGGGGG", False),  # Invalid hex characters
            ("#FF00", False),  # Invalid length (5)
            ("", False),  # Empty string
            (None, False),  # None value
            ("#", False),  # Only hash
        ],
    )
    def test_is_valid_color(
        self,
        color: str | None,
        *,
        expected: bool,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test color validation with various input formats."""
        # Test the static method via public interface (validation during init)
        if expected:
            # Should not raise or warn
            scheme = ColorScheme(primary=color or "#000000")
            assert isinstance(scheme, ColorScheme)
        elif color is not None:
            # Invalid colors should trigger log warning (not Python warning)
            with caplog.at_level("WARNING"):
                ColorScheme(primary=color)
            # Check that a warning was logged
            assert "Invalid color format" in caplog.text
            assert str(color) in caplog.text

    def test_color_validation_on_initialization(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that invalid colors trigger warning during initialization."""
        with caplog.at_level("WARNING"):
            ColorScheme(primary="invalid_color", background="#000000")

        assert "Invalid color format for primary: invalid_color" in caplog.text

    def test_get_luminance_valid_hex_colors(self) -> None:
        """Test luminance calculation for valid hex colors."""
        scheme = ColorScheme()

        # Test via contrast ratio calculation (public interface)
        white_black_ratio = scheme.get_contrast_ratio("#FFFFFF", "#000000")

        # White/black should have very high contrast
        assert white_black_ratio > HIGH_CONTRAST_THRESHOLD

        # Test same colors have 1:1 ratio
        same_ratio = scheme.get_contrast_ratio("#FF0000", "#FF0000")
        assert abs(same_ratio - 1.0) < EPSILON

    def test_get_luminance_short_hex_format(self) -> None:
        """Test luminance calculation for 3-character hex colors."""
        scheme = ColorScheme()

        # #F00 should be equivalent to #FF0000
        short_ratio = scheme.get_contrast_ratio("#F00", "#000000")
        full_ratio = scheme.get_contrast_ratio("#FF0000", "#000000")

        assert abs(short_ratio - full_ratio) < EPSILON

    def test_get_contrast_ratio_known_combinations(self) -> None:
        """Test contrast ratio calculation for known color combinations."""
        scheme = ColorScheme()

        # Black on white should have high contrast
        black_white_ratio = scheme.get_contrast_ratio("#000000", "#FFFFFF")
        assert black_white_ratio > HIGH_CONTRAST_THRESHOLD

        # Same colors should have 1:1 ratio
        same_color_ratio = scheme.get_contrast_ratio("#FF0000", "#FF0000")
        assert abs(same_color_ratio - 1.0) < EPSILON

    def test_get_contrast_ratio_invalid_colors(self) -> None:
        """Test contrast ratio calculation handles invalid colors gracefully."""
        scheme = ColorScheme()

        # Should return 1.0 for invalid colors
        invalid_ratio = scheme.get_contrast_ratio("invalid", "#FFFFFF")
        assert invalid_ratio == 1.0

        both_invalid_ratio = scheme.get_contrast_ratio("invalid1", "invalid2")
        assert both_invalid_ratio == 1.0

    def test_validate_accessibility_wcag_compliance(self) -> None:
        """Test WCAG AA accessibility validation."""
        scheme = ColorScheme(
            text="#000000",  # Black text
            background="#FFFFFF",  # White background
            text_muted="#666666",  # Dark gray
            primary="#0000FF",  # Blue
            error_message="#FF0000",  # Red
        )

        validation_results = scheme.validate_accessibility()

        # Check that results are boolean values
        assert isinstance(validation_results, dict)
        for value in validation_results.values():
            assert isinstance(value, bool)

        # Black on white should pass WCAG AA
        assert validation_results.get("text_on_background", False)

    def test_validate_accessibility_failing_combinations(self) -> None:
        """Test accessibility validation with poor contrast combinations."""
        scheme = ColorScheme(
            text="#CCCCCC",  # Light gray
            background="#DDDDDD",  # Slightly darker gray - poor contrast
        )

        validation_results = scheme.validate_accessibility()

        # Should fail WCAG AA for poor contrast
        assert not validation_results.get("text_on_background", True)

    def test_validate_accessibility_all_combinations_tested(self) -> None:
        """Test that accessibility validation covers all expected combinations."""
        scheme = ColorScheme()
        validation_results = scheme.validate_accessibility()

        expected_combinations = [
            "text_on_background",
            "text_on_surface",
            "text_on_panel",
            "text_muted_on_background",
            "primary_on_background",
            "error_message_on_background",
        ]

        for combination in expected_combinations:
            assert combination in validation_results


class TestThemeManager:
    """Test suite for ThemeManager with comprehensive coverage."""

    @pytest.fixture
    def temp_config_dir(self) -> Generator[Path, None, None]:
        """Create a temporary configuration directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_theme_manager_initialization_default(self) -> None:
        """Test ThemeManager initialization with default settings."""
        manager = ThemeManager()

        assert manager.current_theme == "dark"
        assert isinstance(manager.custom_themes, dict)
        assert len(manager.custom_themes) == 0
        assert isinstance(manager.terminal_colors, dict)

        # Verify built-in themes are available
        available_themes = manager.get_available_themes()
        expected_builtin = ["dark", "light", "monokai", "solarized"]
        for theme in expected_builtin:
            assert theme in available_themes

    def test_theme_manager_initialization_custom_config_dir(
        self,
        temp_config_dir: Path,
    ) -> None:
        """Test ThemeManager initialization with custom config directory."""
        manager = ThemeManager(config_dir=temp_config_dir)

        assert manager.config_dir == temp_config_dir
        assert manager.current_theme == "dark"

    def test_detect_terminal_capabilities_environment_vars(self) -> None:
        """Test terminal capabilities detection from environment variables."""
        with patch("os.environ.get") as mock_get:
            # Test 24-bit color detection
            mock_get.side_effect = lambda key, default="": {
                "COLORTERM": "truecolor",
                "TERM": "xterm",
                "WT_SESSION": "",
            }.get(key, default)

            manager = ThemeManager()
            capabilities = manager.terminal_colors

            assert capabilities["24bit"] is True
            assert capabilities["256color"] is True
            assert capabilities["16color"] is True

    def test_detect_terminal_capabilities_256_color(self) -> None:
        """Test 256-color terminal detection."""
        with patch("os.environ.get") as mock_get:
            mock_get.side_effect = lambda key, default="": {
                "COLORTERM": "",
                "TERM": "xterm-256color",
                "WT_SESSION": "",
            }.get(key, default)

            manager = ThemeManager()
            capabilities = manager.terminal_colors

            assert capabilities["24bit"] is False
            assert capabilities["256color"] is True
            assert capabilities["16color"] is True

    def test_detect_terminal_capabilities_windows_terminal(self) -> None:
        """Test Windows Terminal detection."""
        with patch("os.environ.get") as mock_get:
            mock_get.side_effect = lambda key, default="": {
                "COLORTERM": "",
                "TERM": "",
                "WT_SESSION": "12345",
            }.get(key, default)

            manager = ThemeManager()
            capabilities = manager.terminal_colors

            assert capabilities["24bit"] is True
            assert capabilities["256color"] is True
            assert capabilities["16color"] is True

    def test_get_available_themes_built_in_only(self) -> None:
        """Test getting available themes with built-in themes only."""
        manager = ThemeManager()
        themes = manager.get_available_themes()

        expected_themes = ["dark", "light", "monokai", "solarized"]
        assert len(themes) >= len(expected_themes)
        for theme in expected_themes:
            assert theme in themes

    def test_get_theme_built_in_themes(self) -> None:
        """Test retrieving built-in themes."""
        manager = ThemeManager()

        # Test each built-in theme
        for theme_name in ["dark", "light", "monokai", "solarized"]:
            theme = manager.get_theme(theme_name)
            assert isinstance(theme, ColorScheme)

        # Test dark theme specifically
        dark_theme = manager.get_theme("dark")
        assert dark_theme.background == "#1E1E1E"
        assert dark_theme.text == "#CCCCCC"

    def test_get_theme_nonexistent_fallback(self) -> None:
        """Test getting non-existent theme falls back to dark theme."""
        manager = ThemeManager()

        with patch("src.tui.utils.themes.logger.warning") as mock_warning:
            theme = manager.get_theme("nonexistent_theme")

            assert isinstance(theme, ColorScheme)
            assert theme == manager.get_theme("dark")
            mock_warning.assert_called_once()

    def test_set_theme_valid_theme(self) -> None:
        """Test setting a valid theme."""
        manager = ThemeManager()

        result = manager.set_theme("light")
        assert result is True
        assert manager.current_theme == "light"

    def test_set_theme_invalid_theme(self) -> None:
        """Test setting an invalid theme."""
        manager = ThemeManager()
        original_theme = manager.current_theme

        with patch("src.tui.utils.themes.logger.error") as mock_error:
            result = manager.set_theme("invalid_theme")

            assert result is False
            assert manager.current_theme == original_theme
            mock_error.assert_called_once()

    def test_load_custom_themes_no_file(self, temp_config_dir: Path) -> None:
        """Test loading custom themes when no themes file exists."""
        manager = ThemeManager(config_dir=temp_config_dir)

        assert len(manager.custom_themes) == 0

    def test_load_custom_themes_valid_file(
        self,
        temp_config_dir: Path,
    ) -> None:
        """Test loading custom themes from valid JSON file."""
        themes_file = temp_config_dir / "themes.json"
        custom_theme_data = {
            "my_custom_theme": {
                "primary": "#FF0000",
                "background": "#000000",
                "text": "#FFFFFF",
            },
        }

        themes_file.write_text(json.dumps(custom_theme_data))

        manager = ThemeManager(config_dir=temp_config_dir)

        assert "my_custom_theme" in manager.custom_themes
        custom_theme = manager.get_theme("my_custom_theme")
        assert custom_theme.primary == "#FF0000"
        assert custom_theme.background == "#000000"
        assert custom_theme.text == "#FFFFFF"

    def test_load_custom_themes_invalid_json(
        self,
        temp_config_dir: Path,
    ) -> None:
        """Test loading custom themes with invalid JSON."""
        themes_file = temp_config_dir / "themes.json"
        themes_file.write_text("invalid json content")

        with patch("src.tui.utils.themes.logger.exception") as mock_exception:
            manager = ThemeManager(config_dir=temp_config_dir)

            assert len(manager.custom_themes) == 0
            mock_exception.assert_called_once()

    def test_load_custom_themes_invalid_theme_data(
        self,
        temp_config_dir: Path,
    ) -> None:
        """Test loading custom themes with invalid theme data structure."""
        themes_file = temp_config_dir / "themes.json"
        invalid_theme_data = {
            "invalid_theme": "not_a_dict",
            "another_invalid": {"invalid_field": "value"},
        }

        themes_file.write_text(json.dumps(invalid_theme_data))

        with patch("src.tui.utils.themes.logger.warning") as mock_warning:
            manager = ThemeManager(config_dir=temp_config_dir)

            assert len(manager.custom_themes) == 0
            assert mock_warning.call_count >= 1

    def test_generate_css_default_theme(self) -> None:
        """Test CSS generation for default theme."""
        manager = ThemeManager()

        css = manager.generate_css()

        assert isinstance(css, str)
        assert "Auto-generated theme CSS for 'dark'" in css
        assert "CSS VARIABLES" in css
        assert "MESSAGE TYPE CLASSES" in css
        assert "SCREEN BASE STYLES" in css
        assert "STATUS INDICATOR CLASSES" in css

        # Check for specific color variables
        assert "--primary:" in css
        assert "--background:" in css
        assert "--text:" in css

    def test_generate_css_specific_theme(self) -> None:
        """Test CSS generation for specific theme."""
        manager = ThemeManager()

        css = manager.generate_css("light")

        assert "Auto-generated theme CSS for 'light'" in css
        # Light theme should have different background color
        light_theme = manager.get_theme("light")
        assert light_theme.background in css

    def test_generate_css_variables(self) -> None:
        """Test CSS variable generation via public interface."""
        manager = ThemeManager()

        css = manager.generate_css("dark")

        assert "--primary: #0066CC;" in css
        assert "--background: #1E1E1E;" in css
        assert "--text: #CCCCCC;" in css
        assert "--user-message: #0066CC;" in css

    def test_generate_css_classes(self) -> None:
        """Test CSS class generation via public interface."""
        manager = ThemeManager()

        css = manager.generate_css("dark")

        assert ".message-user" in css
        assert ".message-assistant" in css
        assert ".syntax-keyword" in css

        theme = manager.get_theme("dark")
        assert theme.user_message in css
        assert theme.syntax_keyword in css

    def test_validate_theme_accessibility_current_theme(self) -> None:
        """Test accessibility validation for current theme."""
        manager = ThemeManager()

        validation = manager.validate_theme_accessibility()

        assert isinstance(validation, dict)
        for value in validation.values():
            assert isinstance(value, bool)

    def test_validate_theme_accessibility_specific_theme(self) -> None:
        """Test accessibility validation for specific theme."""
        manager = ThemeManager()

        validation = manager.validate_theme_accessibility("light")

        assert isinstance(validation, dict)
        # Light theme should generally have better accessibility
        # (but this depends on specific color choices)

    def test_get_fallback_colors_16_color_terminal(self) -> None:
        """Test fallback colors for 16-color terminals."""
        with patch("os.environ.get", return_value=""):
            manager = ThemeManager()
            manager.terminal_colors = {
                "24bit": False,
                "256color": False,
                "16color": True,
            }

            colors = manager.get_fallback_colors()

            expected_keys = [
                "primary",
                "secondary",
                "success",
                "warning",
                "danger",
                "info",
                "text",
                "background",
            ]
            for key in expected_keys:
                assert key in colors
                assert isinstance(colors[key], str)

    def test_get_fallback_colors_full_color_terminal(self) -> None:
        """Test fallback colors for full-color terminals."""
        manager = ThemeManager()
        manager.terminal_colors = {
            "24bit": True,
            "256color": True,
            "16color": True,
        }

        colors = manager.get_fallback_colors()

        # Should return full color scheme
        theme = manager.get_theme(manager.current_theme)
        assert colors["primary"] == theme.primary
        assert colors["background"] == theme.background

    def test_save_custom_theme_success(self, temp_config_dir: Path) -> None:
        """Test successful custom theme saving."""
        manager = ThemeManager(config_dir=temp_config_dir)

        custom_theme = ColorScheme(
            primary="#FF0000",
            background="#000000",
            text="#FFFFFF",
        )

        result = manager.save_custom_theme("my_theme", custom_theme)

        assert result is True
        assert "my_theme" in manager.custom_themes

        # Verify file was created
        themes_file = temp_config_dir / "themes.json"
        assert themes_file.exists()

        # Verify file content
        with themes_file.open() as f:
            data = json.load(f)

        assert "my_theme" in data
        assert data["my_theme"]["primary"] == "#FF0000"

    def test_save_custom_theme_update_existing(
        self,
        temp_config_dir: Path,
    ) -> None:
        """Test updating existing custom theme."""
        manager = ThemeManager(config_dir=temp_config_dir)

        # Create initial theme
        theme1 = ColorScheme(primary="#FF0000")
        manager.save_custom_theme("test_theme", theme1)

        # Update theme
        theme2 = ColorScheme(primary="#00FF00")
        result = manager.save_custom_theme("test_theme", theme2)

        assert result is True
        updated_theme = manager.get_theme("test_theme")
        assert updated_theme.primary == "#00FF00"

    def test_save_custom_theme_failure(self) -> None:
        """Test custom theme saving failure scenarios."""
        # Create manager with invalid config directory
        invalid_path = Path("/invalid/path/that/does/not/exist")
        manager = ThemeManager(config_dir=invalid_path)

        custom_theme = ColorScheme(primary="#FF0000")

        with patch("src.tui.utils.themes.logger.exception") as mock_exception:
            result = manager.save_custom_theme("test_theme", custom_theme)

            assert result is False
            mock_exception.assert_called_once()

    def test_delete_custom_theme_success(self, temp_config_dir: Path) -> None:
        """Test successful custom theme deletion."""
        manager = ThemeManager(config_dir=temp_config_dir)

        # Create a theme first
        custom_theme = ColorScheme(primary="#FF0000")
        manager.save_custom_theme("delete_me", custom_theme)

        # Verify it exists
        assert "delete_me" in manager.custom_themes

        # Delete it
        result = manager.delete_custom_theme("delete_me")

        assert result is True
        assert "delete_me" not in manager.custom_themes

    def test_delete_custom_theme_nonexistent(self) -> None:
        """Test deleting non-existent custom theme."""
        manager = ThemeManager()

        with patch("src.tui.utils.themes.logger.warning") as mock_warning:
            result = manager.delete_custom_theme("nonexistent")

            assert result is False
            mock_warning.assert_called_once()

    def test_delete_custom_theme_failure(self, temp_config_dir: Path) -> None:
        """Test custom theme deletion failure scenarios."""
        manager = ThemeManager(config_dir=temp_config_dir)

        # Create a theme first to ensure the file exists
        custom_theme = ColorScheme(primary="#FF0000")
        manager.save_custom_theme("test_theme", custom_theme)

        # Verify it exists
        assert "test_theme" in manager.custom_themes

        # Now patch the file operations to simulate failure during deletion
        with (
            patch(
                "src.tui.utils.themes.ThemeManager._delete_theme_from_file",
                side_effect=OSError("File error"),
            ),
            patch("src.tui.utils.themes.logger.exception") as mock_exception,
        ):
            result = manager.delete_custom_theme("test_theme")

            assert result is False
            mock_exception.assert_called_once()

    def test_get_current_theme(self) -> None:
        """Test getting current theme."""
        manager = ThemeManager()

        current_theme = manager.get_current_theme()
        assert isinstance(current_theme, ColorScheme)
        assert current_theme == manager.get_theme(manager.current_theme)

        # Change theme and test again
        manager.set_theme("light")
        new_current_theme = manager.get_current_theme()
        assert new_current_theme == manager.get_theme("light")

    def test_generate_theme_preview(self) -> None:
        """Test theme preview generation."""
        manager = ThemeManager()

        preview = manager.generate_theme_preview("dark")

        assert isinstance(preview, str)
        assert "Theme: dark" in preview
        assert "Primary:" in preview
        assert "Background:" in preview
        assert "Message Colors:" in preview
        assert "User:" in preview
        assert "Assistant:" in preview

        # Check for actual color values
        dark_theme = manager.get_theme("dark")
        assert dark_theme.primary in preview
        assert dark_theme.background in preview

    def test_built_in_themes_structure(self) -> None:
        """Test that all built-in themes have proper structure."""
        manager = ThemeManager()

        for theme_name in ["dark", "light", "monokai", "solarized"]:
            theme = manager.get_theme(theme_name)

            # Test essential properties exist
            assert hasattr(theme, "primary")
            assert hasattr(theme, "background")
            assert hasattr(theme, "text")
            assert hasattr(theme, "user_message")
            assert hasattr(theme, "assistant_message")
            assert hasattr(theme, "syntax_keyword")
            assert hasattr(theme, "syntax_string")

            # Test colors are valid using public interface
            # Use contrast ratio calculation to test color validity
            ratio = theme.get_contrast_ratio(theme.primary, theme.background)
            assert ratio > 0  # Valid colors should return positive ratio

    def test_theme_manager_logging(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that ThemeManager produces appropriate log messages."""
        with caplog.at_level("INFO"):
            manager = ThemeManager()

            # Should log initialization
            assert any(
                "ThemeManager initialized" in record.message
                for record in caplog.records
            )

        # Clear logs and test theme change logging
        caplog.clear()

        with caplog.at_level("INFO"):
            manager.set_theme("light")

            assert any(
                "Theme changed from" in record.message
                for record in caplog.records
            )

    @pytest.mark.parametrize(
        "theme_name",
        ["dark", "light", "monokai", "solarized"],
    )
    def test_all_builtin_themes_accessibility(self, theme_name: str) -> None:
        """Test that all built-in themes have accessibility validation."""
        manager = ThemeManager()

        validation = manager.validate_theme_accessibility(theme_name)

        # Should have validation results for all expected combinations
        assert isinstance(validation, dict)
        assert len(validation) > 0

        # At least some combinations should pass (themes should be usable)
        passing_combinations = sum(
            1 for passed in validation.values() if passed
        )
        assert passing_combinations > 0

    def test_custom_themes_priority_over_builtin(
        self,
        temp_config_dir: Path,
    ) -> None:
        """Test that custom themes take priority over built-in themes with same name."""
        manager = ThemeManager(config_dir=temp_config_dir)

        # Create custom theme with same name as built-in
        custom_dark = ColorScheme(
            primary="#FF0000",
        )  # Different from built-in dark
        manager.save_custom_theme("dark", custom_dark)

        # Recreate manager to test loading
        manager2 = ThemeManager(config_dir=temp_config_dir)

        retrieved_theme = manager2.get_theme("dark")
        assert (
            retrieved_theme.primary == "#FF0000"
        )  # Should get custom, not built-in
