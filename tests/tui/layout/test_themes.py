"""Tests for theme management system."""

from __future__ import annotations

from src.tui.utils.themes import ThemeManager

# Test constants
DARK_THEME = "dark"
LIGHT_THEME = "light"
INVALID_THEME = "invalid"
CUSTOM_THEME = "custom"

DARK_BACKGROUND = "#1e1e1e"
DARK_FOREGROUND = "#d4d4d4"
DARK_PRIMARY = "#007acc"

LIGHT_BACKGROUND = "#ffffff"
LIGHT_FOREGROUND = "#000000"
LIGHT_PRIMARY = "#0066cc"

DEFAULT_COLOR = "#000000"


class TestThemeManager:
    """Test ThemeManager functionality."""

    def test_initialization(self) -> None:
        """Test theme manager initialization."""
        manager = ThemeManager()

        # Test default theme
        assert manager.current_theme == DARK_THEME

        # Test themes dictionary structure
        assert isinstance(manager.themes, dict)
        assert DARK_THEME in manager.themes
        assert LIGHT_THEME in manager.themes

        # Test dark theme colors
        dark_theme = manager.themes[DARK_THEME]
        assert dark_theme["background"] == DARK_BACKGROUND
        assert dark_theme["foreground"] == DARK_FOREGROUND
        assert dark_theme["primary"] == DARK_PRIMARY

        # Test light theme colors
        light_theme = manager.themes[LIGHT_THEME]
        assert light_theme["background"] == LIGHT_BACKGROUND
        assert light_theme["foreground"] == LIGHT_FOREGROUND
        assert light_theme["primary"] == LIGHT_PRIMARY

    def test_set_theme_valid(self) -> None:
        """Test setting valid themes."""
        manager = ThemeManager()

        # Initially should be dark
        assert manager.current_theme == DARK_THEME

        # Switch to light theme
        manager.set_theme(LIGHT_THEME)
        assert manager.current_theme == LIGHT_THEME

        # Switch back to dark theme
        manager.set_theme(DARK_THEME)
        assert manager.current_theme == DARK_THEME

    def test_set_theme_invalid(self) -> None:
        """Test setting invalid theme name."""
        manager = ThemeManager()
        original_theme = manager.current_theme

        # Try to set invalid theme
        manager.set_theme(INVALID_THEME)

        # Should remain unchanged
        assert manager.current_theme == original_theme

    def test_get_color_existing(self) -> None:
        """Test getting existing colors from current theme."""
        manager = ThemeManager()

        # Test getting colors from dark theme (default)
        assert manager.get_color("background") == DARK_BACKGROUND
        assert manager.get_color("foreground") == DARK_FOREGROUND
        assert manager.get_color("primary") == DARK_PRIMARY

        # Switch to light theme
        manager.set_theme(LIGHT_THEME)
        assert manager.get_color("background") == LIGHT_BACKGROUND
        assert manager.get_color("foreground") == LIGHT_FOREGROUND
        assert manager.get_color("primary") == LIGHT_PRIMARY

    def test_get_color_nonexistent(self) -> None:
        """Test getting non-existent color from current theme."""
        manager = ThemeManager()

        # Should return default color for non-existent color names
        assert manager.get_color("nonexistent") == DEFAULT_COLOR
        assert manager.get_color("") == DEFAULT_COLOR
        assert manager.get_color("invalid_color") == DEFAULT_COLOR

    def test_theme_persistence_after_color_access(self) -> None:
        """Test that theme persists after getting colors."""
        manager = ThemeManager()

        # Set light theme
        manager.set_theme(LIGHT_THEME)
        assert manager.current_theme == LIGHT_THEME

        # Access colors
        background = manager.get_color("background")
        foreground = manager.get_color("foreground")

        # Theme should still be light
        assert manager.current_theme == LIGHT_THEME
        assert background == LIGHT_BACKGROUND
        assert foreground == LIGHT_FOREGROUND

    def test_case_sensitivity(self) -> None:
        """Test case sensitivity for theme and color names."""
        manager = ThemeManager()

        # Theme names should be case sensitive
        manager.set_theme("Dark")  # Invalid (case sensitive)
        assert manager.current_theme == DARK_THEME  # Should remain unchanged

        # Color names should be case sensitive
        assert manager.get_color("Background") == DEFAULT_COLOR  # Invalid case
        assert (
            manager.get_color("background") == DARK_BACKGROUND
        )  # Correct case


class TestThemeEdgeCases:
    """Test edge cases and error conditions."""

    def test_multiple_managers_independence(self) -> None:
        """Test that multiple managers are independent."""
        manager1 = ThemeManager()
        manager2 = ThemeManager()

        # Both should start with dark theme
        assert manager1.current_theme == DARK_THEME
        assert manager2.current_theme == DARK_THEME

        # Change first manager to light
        manager1.set_theme(LIGHT_THEME)

        # Should be independent
        assert manager1.current_theme == LIGHT_THEME
        assert manager2.current_theme == DARK_THEME

    def test_theme_modification(self) -> None:
        """Test modifying theme colors after creation."""
        manager = ThemeManager()

        # Modify dark theme colors
        custom_color = "#ff0000"
        manager.themes[DARK_THEME]["custom"] = custom_color

        # Should be able to retrieve custom color
        assert manager.get_color("custom") == custom_color

        # Original colors should still work
        assert manager.get_color("background") == DARK_BACKGROUND

    def test_add_custom_theme(self) -> None:
        """Test adding custom theme after initialization."""
        manager = ThemeManager()

        # Add custom theme
        custom_colors = {
            "background": "#2d2d2d",
            "foreground": "#f0f0f0",
            "primary": "#ff6600",
        }
        manager.themes[CUSTOM_THEME] = custom_colors

        # Switch to custom theme
        manager.set_theme(CUSTOM_THEME)
        assert manager.current_theme == CUSTOM_THEME

        # Should get custom colors
        assert manager.get_color("background") == custom_colors["background"]
        assert manager.get_color("foreground") == custom_colors["foreground"]
        assert manager.get_color("primary") == custom_colors["primary"]

    def test_empty_theme(self) -> None:
        """Test behavior with empty theme colors."""
        manager = ThemeManager()

        # Add empty theme
        empty_theme = "empty"
        manager.themes[empty_theme] = {}

        # Switch to empty theme
        manager.set_theme(empty_theme)
        assert manager.current_theme == empty_theme

        # Should return default for all colors
        assert manager.get_color("background") == DEFAULT_COLOR
        assert manager.get_color("foreground") == DEFAULT_COLOR
        assert manager.get_color("primary") == DEFAULT_COLOR

    def test_unicode_theme_names_and_colors(self) -> None:
        """Test themes with Unicode names and colors."""
        manager = ThemeManager()

        # Add Unicode theme
        unicode_theme = "тёмная_тема"  # Russian for "dark theme"
        unicode_colors = {
            "фон": "#000000",  # Russian for "background"
            "текст": "#ffffff",  # Russian for "text"
        }
        manager.themes[unicode_theme] = unicode_colors

        # Should work with Unicode
        manager.set_theme(unicode_theme)
        assert manager.current_theme == unicode_theme

        assert manager.get_color("фон") == "#000000"
        assert manager.get_color("текст") == "#ffffff"

    def test_very_long_theme_and_color_names(self) -> None:
        """Test with very long theme and color names."""
        manager = ThemeManager()

        long_theme_name = "very_long_theme_name_" + "x" * 100
        long_color_name = "very_long_color_name_" + "y" * 100
        test_color_value = "#abcdef"

        # Add theme with long names
        manager.themes[long_theme_name] = {
            long_color_name: test_color_value,
        }

        # Should work with long names
        manager.set_theme(long_theme_name)
        assert manager.current_theme == long_theme_name
        assert manager.get_color(long_color_name) == test_color_value

    def test_special_characters_in_names(self) -> None:
        """Test themes with special characters."""
        manager = ThemeManager()

        # Add theme with special characters
        special_theme = "theme-with.special_chars@2024!"
        special_color = "color/with\\special:chars"
        test_color_value = "#123456"

        manager.themes[special_theme] = {
            special_color: test_color_value,
        }

        # Should handle special characters
        manager.set_theme(special_theme)
        assert manager.current_theme == special_theme
        assert manager.get_color(special_color) == test_color_value

    def test_theme_switching_preserves_themes_dict(self) -> None:
        """Test that switching themes doesn't modify the themes dictionary."""
        manager = ThemeManager()

        # Get original themes
        original_dark = manager.themes[DARK_THEME].copy()
        original_light = manager.themes[LIGHT_THEME].copy()

        # Switch themes multiple times
        manager.set_theme(LIGHT_THEME)
        manager.set_theme(DARK_THEME)
        manager.set_theme(LIGHT_THEME)

        # Themes should be unchanged
        assert manager.themes[DARK_THEME] == original_dark
        assert manager.themes[LIGHT_THEME] == original_light

    def test_simultaneous_color_access(self) -> None:
        """Test accessing multiple colors simultaneously."""
        manager = ThemeManager()

        # Get multiple colors at once
        colors = {
            "background": manager.get_color("background"),
            "foreground": manager.get_color("foreground"),
            "primary": manager.get_color("primary"),
            "nonexistent": manager.get_color("nonexistent"),
        }

        # Should get expected values
        assert colors["background"] == DARK_BACKGROUND
        assert colors["foreground"] == DARK_FOREGROUND
        assert colors["primary"] == DARK_PRIMARY
        assert colors["nonexistent"] == DEFAULT_COLOR
