"""Comprehensive responsive terminal handling with dynamic sizing and layouts."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar, Protocol

from textual.geometry import Size

if TYPE_CHECKING:
    from textual.app import App


class ResponsiveWidget(Protocol):
    """Protocol for widgets that can respond to size changes."""

    def on_screen_size_change(
        self,
        size: ScreenSize,
        width: int,
        height: int,
    ) -> None:
        """Handle screen size change notification."""
        ...


class ScreenSize(Enum):
    """Terminal screen size categories with enhanced breakpoints."""

    TINY = "tiny"  # < 60 columns or < 16 rows
    SMALL = "small"  # 60-79 columns or 16-23 rows
    MEDIUM = "medium"  # 80-119 columns and 24-39 rows
    LARGE = "large"  # 120-159 columns and 40-59 rows
    XLARGE = "xlarge"  # 160+ columns and 60+ rows


class ResponsiveBreakpoints:
    """Configurable breakpoints for responsive design."""

    def __init__(
        self,
        tiny_max: int = 59,
        small_max: int = 79,
        medium_max: int = 119,
        large_max: int = 159,
    ) -> None:
        """Initialize responsive breakpoints.

        Args:
            tiny_max: Maximum width/height for tiny screens
            small_max: Maximum width/height for small screens
            medium_max: Maximum width/height for medium screens
            large_max: Maximum width/height for large screens

        """
        self.tiny_max = tiny_max
        self.small_max = small_max
        self.medium_max = medium_max
        self.large_max = large_max

    def get_screen_size(self, dimension: int) -> ScreenSize:
        """Get screen size category based on a dimension.

        Args:
            dimension: Width or height value

        Returns:
            ScreenSize enum value

        """
        if dimension <= self.tiny_max:
            return ScreenSize.TINY
        if dimension <= self.small_max:
            return ScreenSize.SMALL
        if dimension <= self.medium_max:
            return ScreenSize.MEDIUM
        if dimension <= self.large_max:
            return ScreenSize.LARGE
        return ScreenSize.XLARGE


@dataclass
class LayoutConfig:
    """Configuration for responsive layouts."""

    panel_widths: dict[ScreenSize, str | int] | None = None
    panel_heights: dict[ScreenSize, str | int] | None = None
    layout_modes: dict[ScreenSize, str] | None = None
    visibility: dict[ScreenSize, bool] | None = None

    def __post_init__(self) -> None:
        """Initialize default values if not provided."""
        if self.panel_widths is None:
            self.panel_widths = {
                ScreenSize.TINY: "100%",
                ScreenSize.SMALL: "30",
                ScreenSize.MEDIUM: "25%",
                ScreenSize.LARGE: "20%",
                ScreenSize.XLARGE: "300px",
            }

        if self.panel_heights is None:
            self.panel_heights = {
                ScreenSize.TINY: "8",
                ScreenSize.SMALL: "10",
                ScreenSize.MEDIUM: "1fr",
                ScreenSize.LARGE: "1fr",
                ScreenSize.XLARGE: "1fr",
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
                ScreenSize.TINY: True,
                ScreenSize.SMALL: True,
                ScreenSize.MEDIUM: True,
                ScreenSize.LARGE: True,
                ScreenSize.XLARGE: True,
            }


class ResponsiveManager:
    """Comprehensive terminal resize and responsive layout manager."""

    # Size breakpoints with both width and height constraints
    MINIMUM_SIZE: ClassVar[Size] = Size(80, 24)
    SMALL_SIZE: ClassVar[Size] = Size(100, 30)
    MEDIUM_SIZE: ClassVar[Size] = Size(120, 40)
    LARGE_SIZE: ClassVar[Size] = Size(150, 50)

    # Size thresholds
    TINY_WIDTH_THRESHOLD: ClassVar[int] = 60
    TINY_HEIGHT_THRESHOLD: ClassVar[int] = 16
    SMALL_WIDTH_THRESHOLD: ClassVar[int] = 80
    SMALL_HEIGHT_THRESHOLD: ClassVar[int] = 24
    MEDIUM_WIDTH_THRESHOLD: ClassVar[int] = 120
    MEDIUM_HEIGHT_THRESHOLD: ClassVar[int] = 40
    LARGE_WIDTH_THRESHOLD: ClassVar[int] = 160
    LARGE_HEIGHT_THRESHOLD: ClassVar[int] = 60

    # Panel size configurations for different screen categories
    PANEL_CONFIGS: ClassVar[dict[str, dict[str, Any]]] = {
        "tiny": {
            "sidebar_width": 18,
            "header_height": 2,
            "footer_height": 1,
            "content_padding": 0,
            "border_style": "none",
        },
        "small": {
            "sidebar_width": 22,
            "header_height": 2,
            "footer_height": 1,
            "content_padding": 0,
            "border_style": "solid",
        },
        "medium": {
            "sidebar_width": 28,
            "header_height": 3,
            "footer_height": 2,
            "content_padding": 1,
            "border_style": "solid",
        },
        "large": {
            "sidebar_width": 35,
            "header_height": 3,
            "footer_height": 2,
            "content_padding": 1,
            "border_style": "solid",
        },
        "xlarge": {
            "sidebar_width": 45,
            "header_height": 4,
            "footer_height": 3,
            "content_padding": 2,
            "border_style": "thick",
        },
    }

    def __init__(self, app: App[Any] | None = None) -> None:
        """Initialize responsive manager with optional app reference."""
        self.app = app
        self.current_size: Size | None = None
        self.size_category: str = "medium"
        self.registered_widgets: list[ResponsiveWidget] = []
        self.layout_configs: dict[str, LayoutConfig] = {}
        self.breakpoints = ResponsiveBreakpoints()
        self._logger = logging.getLogger(__name__)
        self._initialized = False

        # Set current screen size based on breakpoints
        self.current_screen_size: ScreenSize | None = None

    def get_size_category(self, size: Size) -> str:
        """Determine size category from terminal dimensions."""
        width, height = size.width, size.height

        # Check for tiny screens (very constrained)
        if (
            width < self.TINY_WIDTH_THRESHOLD
            or height < self.TINY_HEIGHT_THRESHOLD
        ):
            return "tiny"
        # Small screens
        if (
            width < self.SMALL_WIDTH_THRESHOLD
            or height < self.SMALL_HEIGHT_THRESHOLD
        ):
            return "small"
        # Medium screens (standard)
        if (
            width < self.MEDIUM_WIDTH_THRESHOLD
            or height < self.MEDIUM_HEIGHT_THRESHOLD
        ):
            return "medium"
        # Large screens
        if (
            width < self.LARGE_WIDTH_THRESHOLD
            or height < self.LARGE_HEIGHT_THRESHOLD
        ):
            return "large"
        # Extra large screens
        return "xlarge"

    def validate_minimum_size(self, size: Size) -> tuple[bool, str | None]:
        """Check if terminal meets minimum requirements with detailed feedback."""
        issues = []

        if size.width < self.MINIMUM_SIZE.width:
            issues.append(
                f"Width too narrow: {size.width} < {self.MINIMUM_SIZE.width}",
            )

        if size.height < self.MINIMUM_SIZE.height:
            issues.append(
                f"Height too short: {size.height} < {self.MINIMUM_SIZE.height}",
            )

        if issues:
            return False, "; ".join(issues)
        return True, None

    def calculate_panel_sizes(self, size: Size) -> dict[str, Any]:
        """Calculate optimal panel sizes for current terminal dimensions."""
        category = self.get_size_category(size)
        config = self.PANEL_CONFIGS[category]

        # Calculate sidebar width with constraints
        sidebar_width = min(
            config["sidebar_width"],
            int(size.width * 0.4),  # Max 40% of width
            size.width - 40,  # Leave at least 40 cols for content
        )
        sidebar_width = max(sidebar_width, 15)  # Minimum sidebar width

        # Calculate content dimensions
        content_width = size.width - sidebar_width - 2  # Account for borders
        content_height = (
            size.height
            - config["header_height"]
            - config["footer_height"]
            - 2  # Account for borders
        )

        # Ensure positive dimensions
        content_width = max(content_width, 20)
        content_height = max(content_height, 5)

        return {
            "category": category,
            "sidebar_width": sidebar_width,
            "content_width": content_width,
            "content_height": content_height,
            "header_height": config["header_height"],
            "footer_height": config["footer_height"],
            "content_padding": config["content_padding"],
            "border_style": config["border_style"],
            "total_width": size.width,
            "total_height": size.height,
        }

    async def handle_resize(self, size: Size) -> None:
        """Handle terminal resize event with comprehensive layout updates."""
        try:
            # Validate minimum size requirements
            valid, message = self.validate_minimum_size(size)
            if not valid and self.app is not None:
                self.app.notify(
                    f"Terminal size warning: {message}",
                    severity="warning",
                    timeout=5,
                )
                # Continue with degraded mode rather than blocking

            # Calculate new panel dimensions
            panel_sizes = self.calculate_panel_sizes(size)
            old_category = self.size_category
            self.size_category = panel_sizes["category"]

            # Apply sizing to UI components
            await self.apply_panel_sizes(panel_sizes)

            # Notify registered widgets of size change
            await self._notify_responsive_widgets(size)

            # Update current state
            self.current_size = size
            self._initialized = True

            # Log resize event for debugging
            self._logger.info(
                "Terminal resized: %sx%s (%s → %s)",
                size.width,
                size.height,
                old_category,
                self.size_category,
            )

            # Notify user of significant layout changes
            if (
                old_category != self.size_category
                and self._initialized
                and self.app is not None
            ):
                self.app.notify(
                    f"Layout adapted for {self.size_category} screen",
                    severity="information",
                    timeout=2,
                )

        except Exception:
            self._logger.exception("Error handling resize")
            # Don't re-raise to prevent app crash

    async def apply_panel_sizes(self, sizes: dict[str, Any]) -> None:
        """Apply calculated sizes to UI panels with error handling."""
        try:
            # Update sidebar (projects panel)
            await self._update_sidebar(sizes)

            # Update header
            await self._update_header(sizes)

            # Update footer
            await self._update_footer(sizes)

            # Update main content area styling
            await self._update_content_area()

        except Exception:
            self._logger.exception("Error applying panel sizes")

    async def _update_sidebar(self, sizes: dict[str, Any]) -> None:
        """Update sidebar with new dimensions."""
        try:
            if self.app is not None:
                sidebar = self.app.query_one("#projects-panel")
                sidebar.styles.width = sizes["sidebar_width"]
                if hasattr(sidebar, "on_responsive_update"):
                    await sidebar.on_responsive_update(sizes)
        except (ValueError, AttributeError):
            # Panel might not exist yet - this is expected during startup
            pass

    async def _update_header(self, sizes: dict[str, Any]) -> None:
        """Update header with new dimensions."""
        try:
            if self.app is not None:
                header = self.app.query_one("Header")
                header.styles.height = sizes["header_height"]
                if hasattr(header, "on_responsive_update"):
                    await header.on_responsive_update(sizes)
        except (ValueError, AttributeError):
            # Panel might not exist yet - this is expected during startup
            pass

    async def _update_footer(self, sizes: dict[str, Any]) -> None:
        """Update footer with new dimensions."""
        try:
            if self.app is not None:
                footer = self.app.query_one("Footer")
                footer.styles.height = sizes["footer_height"]
                if hasattr(footer, "on_responsive_update"):
                    await footer.on_responsive_update(sizes)
        except (ValueError, AttributeError):
            # Panel might not exist yet - this is expected during startup
            pass

    async def _update_content_area(self) -> None:
        """Update content area layout."""
        try:
            if self.app is not None:
                content_area = self.app.query_one("#content-area")
                if self.should_stack_vertically():
                    content_area.styles.layout = "vertical"
                else:
                    content_area.styles.layout = "horizontal"
        except (ValueError, AttributeError):
            # Content area might not exist yet - this is expected during startup
            pass

    async def _notify_responsive_widgets(self, size: Size) -> None:
        """Notify all registered responsive widgets of size changes."""
        screen_size = self._size_to_screen_size(size)

        for widget in self.registered_widgets:
            try:
                if hasattr(widget, "on_screen_size_change"):
                    widget.on_screen_size_change(
                        screen_size,
                        size.width,
                        size.height,
                    )
            except (AttributeError, TypeError, ValueError) as e:
                self._logger.warning("Widget responsive update failed: %s", e)

    def _size_to_screen_size(self, size: Size) -> ScreenSize:
        """Convert Size to ScreenSize enum."""
        category = self.get_size_category(size)
        return {
            "tiny": ScreenSize.TINY,
            "small": ScreenSize.SMALL,
            "medium": ScreenSize.MEDIUM,
            "large": ScreenSize.LARGE,
            "xlarge": ScreenSize.XLARGE,
        }[category]

    def register_widget(self, widget: ResponsiveWidget) -> None:
        """Register a widget for responsive updates."""
        if widget not in self.registered_widgets:
            self.registered_widgets.append(widget)

    def unregister_widget(self, widget: ResponsiveWidget) -> None:
        """Unregister a widget from responsive updates."""
        if widget in self.registered_widgets:
            self.registered_widgets.remove(widget)

    def get_adaptive_width(self, widget_type: str) -> str | int:
        """Get adaptive width for specific widget types."""
        config = self.PANEL_CONFIGS.get(
            self.size_category,
            self.PANEL_CONFIGS["medium"],
        )

        if widget_type == "sidebar":
            return int(config["sidebar_width"])
        if widget_type == "main":
            return "1fr"
        if widget_type == "panel":
            if self.size_category in ("tiny", "small"):
                return "100%"
            return "1fr"

        return "auto"

    def get_adaptive_padding(self) -> int:
        """Get adaptive padding based on current screen size."""
        config = self.PANEL_CONFIGS.get(
            self.size_category,
            self.PANEL_CONFIGS["medium"],
        )
        return int(config["content_padding"])

    def get_border_style(self) -> str:
        """Get appropriate border style for current screen size."""
        config = self.PANEL_CONFIGS.get(
            self.size_category,
            self.PANEL_CONFIGS["medium"],
        )
        return str(config["border_style"])

    def is_compact_mode(self) -> bool:
        """Check if UI should be in compact mode."""
        return self.size_category in ("tiny", "small")

    def set_layout_config(self, widget_id: str, config: LayoutConfig) -> None:
        """Set layout configuration for a specific widget."""
        self.layout_configs[widget_id] = config

    def get_adaptive_styles(
        self,
        widget_id: str,
        screen_size: ScreenSize,
    ) -> dict[str, Any]:
        """Get adaptive styles for a widget based on screen size."""
        config = self.layout_configs.get(widget_id)
        if not config:
            return {}

        styles = {}
        if config.panel_widths:
            styles["width"] = config.panel_widths.get(screen_size, "auto")
        if config.panel_heights:
            styles["height"] = config.panel_heights.get(screen_size, "auto")
        if config.visibility:
            display_value = (
                "block" if config.visibility.get(screen_size, True) else "none"
            )
            styles["display"] = display_value

        return styles

    def should_stack_vertically(
        self,
        screen_size: ScreenSize | None = None,
    ) -> bool:
        """Determine if panels should stack vertically based on screen size."""
        if screen_size is None:
            screen_size = self.current_screen_size
        return screen_size in (ScreenSize.TINY, ScreenSize.SMALL)

    def get_content_priority(self, screen_size: ScreenSize) -> list[str]:
        """Get content display priority for screen size."""
        if screen_size == ScreenSize.TINY:
            return ["main-content", "status", "navigation"]
        if screen_size == ScreenSize.SMALL:
            return ["main-content", "navigation", "status"]
        return ["navigation", "main-content", "status"]

    def handle_resize_sync(self, width: int, height: int) -> None:
        """Handle resize event (synchronous version for tests)."""
        # Update current screen size based on dimensions
        width_size = self.breakpoints.get_screen_size(width)
        height_size = self.breakpoints.get_screen_size(height)

        # Use the larger category between width and height for better UX
        new_size = max(
            width_size,
            height_size,
            key=lambda s: list(ScreenSize).index(s),
        )

        # Check if this is the first resize or if size category changed
        size_changed = new_size != self.current_screen_size
        is_first_resize = self.current_screen_size is None

        # Always update the current screen size
        self.current_screen_size = new_size

        # Notify widgets on first resize or when size category changes
        if is_first_resize or size_changed:
            # Notify registered widgets
            for widget in self.registered_widgets:
                try:
                    if hasattr(widget, "on_screen_size_change"):
                        widget.on_screen_size_change(new_size, width, height)
                except (
                    AttributeError,
                    TypeError,
                    ValueError,
                    RuntimeError,
                ) as e:
                    self._logger.warning("Widget update failed: %s", e)


def create_responsive_config(  # noqa: PLR0913
    tiny_width: str | int = "100%",
    small_width: str | int = "30",
    medium_width: str | int = "25%",
    large_width: str | int = "20%",
    xlarge_width: str | int = "300px",
    tiny_height: str | int = "8",
    small_height: str | int = "10",
    medium_height: str | int = "1fr",
    large_height: str | int = "1fr",
    xlarge_height: str | int = "1fr",
) -> LayoutConfig:
    """Create a responsive configuration with custom values.

    Args:
        tiny_width: Width for tiny screens
        small_width: Width for small screens
        medium_width: Width for medium screens
        large_width: Width for large screens
        xlarge_width: Width for xlarge screens
        tiny_height: Height for tiny screens
        small_height: Height for small screens
        medium_height: Height for medium screens
        large_height: Height for large screens
        xlarge_height: Height for xlarge screens

    Returns:
        LayoutConfig with specified dimensions

    """
    return LayoutConfig(
        panel_widths={
            ScreenSize.TINY: tiny_width,
            ScreenSize.SMALL: small_width,
            ScreenSize.MEDIUM: medium_width,
            ScreenSize.LARGE: large_width,
            ScreenSize.XLARGE: xlarge_width,
        },
        panel_heights={
            ScreenSize.TINY: tiny_height,
            ScreenSize.SMALL: small_height,
            ScreenSize.MEDIUM: medium_height,
            ScreenSize.LARGE: large_height,
            ScreenSize.XLARGE: xlarge_height,
        },
    )


# Global responsive manager instance
responsive_manager = ResponsiveManager()


def initialize_responsive_manager(app: App[Any]) -> ResponsiveManager:
    """Initialize the global responsive manager with app reference."""
    global responsive_manager  # noqa: PLW0603
    responsive_manager = ResponsiveManager(app)
    return responsive_manager


def get_responsive_manager() -> ResponsiveManager:
    """Get the global responsive manager instance."""
    return responsive_manager
