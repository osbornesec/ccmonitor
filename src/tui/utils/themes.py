"""Color scheme management for CCMonitor TUI."""

from __future__ import annotations


class ThemeManager:
    """Manager for color themes and schemes."""

    def __init__(self) -> None:
        """Initialize theme manager."""
        self.current_theme = "dark"
        self.themes: dict[str, dict[str, str]] = {
            "dark": {
                "background": "#1e1e1e",
                "foreground": "#d4d4d4",
                "primary": "#007acc",
            },
            "light": {
                "background": "#ffffff",
                "foreground": "#000000",
                "primary": "#0066cc",
            },
        }

    def set_theme(self, theme_name: str) -> None:
        """Set the current theme."""
        if theme_name in self.themes:
            self.current_theme = theme_name

    def get_color(self, color_name: str) -> str:
        """Get color value from current theme."""
        return self.themes[self.current_theme].get(color_name, "#000000")
