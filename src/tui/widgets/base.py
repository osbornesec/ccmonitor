"""Base widget classes for CCMonitor TUI."""

from __future__ import annotations

from textual.widget import Widget


class BaseWidget(Widget):
    """Base widget class with common functionality."""

    def on_mount(self) -> None:
        """Handle widget mounting."""
