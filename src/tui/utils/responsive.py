"""Responsive design utilities for adaptive TUI layouts."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class ScreenSize(Enum):
    """Terminal screen size categories."""

    TINY = "tiny"  # < 60 columns
    SMALL = "small"  # 60-79 columns
    MEDIUM = "medium"  # 80-119 columns
    LARGE = "large"  # 120-159 columns
    XLARGE = "xlarge"  # 160+ columns


@dataclass
class ResponsiveBreakpoints:
    """Responsive design breakpoints for different screen sizes."""

    tiny_max: int = 59
    small_max: int = 79
    medium_max: int = 119
    large_max: int = 159

    def get_screen_size(self, width: int) -> ScreenSize:
        """Determine screen size category from width."""
        if width <= self.tiny_max:
            return ScreenSize.TINY
        if width <= self.small_max:
            return ScreenSize.SMALL
        if width <= self.medium_max:
            return ScreenSize.MEDIUM
        if width <= self.large_max:
            return ScreenSize.LARGE
        return ScreenSize.XLARGE


@dataclass
class LayoutConfig:
    """Configuration for responsive layout behavior."""

    # Panel width configurations by screen size
    panel_widths: dict[ScreenSize, str | int] | None = None
    # Height configurations
    panel_heights: dict[ScreenSize, str | int] | None = None
    # Layout mode (horizontal vs vertical)
    layout_modes: dict[ScreenSize, str] | None = None
    # Visibility settings
    visibility: dict[ScreenSize, bool] | None = None

    def __post_init__(self) -> None:
        """Set default configurations."""
        if self.panel_widths is None:
            self.panel_widths = {
                ScreenSize.TINY: "100%",  # Full width, stacked
                ScreenSize.SMALL: "30",  # Fixed width
                ScreenSize.MEDIUM: "25%",  # Percentage
                ScreenSize.LARGE: "20%",  # Smaller percentage
                ScreenSize.XLARGE: "300px",  # Fixed large width
            }

        if self.panel_heights is None:
            self.panel_heights = {
                ScreenSize.TINY: "8",  # Collapsed height
                ScreenSize.SMALL: "10",  # Small height
                ScreenSize.MEDIUM: "1fr",  # Full height
                ScreenSize.LARGE: "1fr",  # Full height
                ScreenSize.XLARGE: "1fr",  # Full height
            }

        if self.layout_modes is None:
            self.layout_modes = {
                ScreenSize.TINY: "vertical",
                ScreenSize.SMALL: "vertical",
                ScreenSize.MEDIUM: "horizontal",
                ScreenSize.LARGE: "horizontal",
                ScreenSize.XLARGE: "horizontal",
            }

        if self.visibility is None:
            self.visibility = {
                ScreenSize.TINY: True,  # Always visible but collapsed
                ScreenSize.SMALL: True,
                ScreenSize.MEDIUM: True,
                ScreenSize.LARGE: True,
                ScreenSize.XLARGE: True,
            }


class ResponsiveWidget(Protocol):
    """Protocol for widgets that support responsive behavior."""

    def on_screen_size_change(
        self,
        size: ScreenSize,
        width: int,
        height: int,
    ) -> None:
        """Handle screen size changes."""


class ResponsiveManager:
    """Manages responsive behavior across the application."""

    def __init__(self) -> None:
        """Initialize responsive manager."""
        self.breakpoints = ResponsiveBreakpoints()
        self.current_size = ScreenSize.MEDIUM
        self.registered_widgets: list[ResponsiveWidget] = []
        self.layout_configs: dict[str, LayoutConfig] = {}
        self._initialized = False

    def register_widget(self, widget: ResponsiveWidget) -> None:
        """Register a widget for responsive updates."""
        if widget not in self.registered_widgets:
            self.registered_widgets.append(widget)

    def unregister_widget(self, widget: ResponsiveWidget) -> None:
        """Unregister a widget from responsive updates."""
        if widget in self.registered_widgets:
            self.registered_widgets.remove(widget)

    def set_layout_config(self, widget_id: str, config: LayoutConfig) -> None:
        """Set layout configuration for a specific widget."""
        self.layout_configs[widget_id] = config

    def handle_resize(self, width: int, height: int) -> None:
        """Handle terminal resize events."""
        new_size = self.breakpoints.get_screen_size(width)

        # Update if size category changed or first time
        if new_size != self.current_size or not self._initialized:
            self.current_size = new_size
            self._initialized = True
            self._notify_widgets(new_size, width, height)

    def _notify_widgets(
        self,
        size: ScreenSize,
        width: int,
        height: int,
    ) -> None:
        """Notify all registered widgets of size change."""
        for widget in self.registered_widgets:
            # Silently ignore widget update failures to prevent
            # one broken widget from affecting others
            with contextlib.suppress(Exception):
                widget.on_screen_size_change(size, width, height)

    def get_adaptive_styles(
        self,
        widget_id: str,
        size: ScreenSize,
    ) -> dict[str, str | int]:
        """Get adaptive styles for a widget based on current screen size."""
        config = self.layout_configs.get(widget_id)
        if not config:
            return {}

        styles = {}

        # Apply width if configured
        if config.panel_widths and size in config.panel_widths:
            styles["width"] = config.panel_widths[size]

        # Apply height if configured
        if config.panel_heights and size in config.panel_heights:
            styles["height"] = config.panel_heights[size]

        # Apply visibility
        if config.visibility and size in config.visibility:
            styles["display"] = "block" if config.visibility[size] else "none"

        return styles

    def should_stack_vertically(self, size: ScreenSize) -> bool:
        """Determine if layout should stack vertically for given size."""
        return size in (ScreenSize.TINY, ScreenSize.SMALL)

    def get_content_priority(self, size: ScreenSize) -> list[str]:
        """Get content priority order for different screen sizes."""
        if size == ScreenSize.TINY:
            return ["main-content", "status", "navigation"]
        if size == ScreenSize.SMALL:
            return ["main-content", "navigation", "status"]
        return ["navigation", "main-content", "status"]


def create_responsive_config(
    *,
    tiny_width: str | int = "100%",
    small_width: str | int = "30",
    medium_width: str | int = "25%",
    large_width: str | int = "20%",
    xlarge_width: str | int = "300px",
) -> LayoutConfig:
    """Create a responsive configuration with custom widths."""
    return LayoutConfig(
        panel_widths={
            ScreenSize.TINY: tiny_width,
            ScreenSize.SMALL: small_width,
            ScreenSize.MEDIUM: medium_width,
            ScreenSize.LARGE: large_width,
            ScreenSize.XLARGE: xlarge_width,
        },
    )


# Global responsive manager instance
responsive_manager = ResponsiveManager()
