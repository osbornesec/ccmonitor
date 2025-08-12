"""Smart scrolling widget with responsive behavior and performance optimization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import ScrollableContainer
from textual.reactive import reactive

from src.tui.utils.responsive import ScreenSize

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.widget import Widget


class SmartScrollView(ScrollableContainer):
    """Intelligent scrolling widget that adapts to screen size and content."""

    # Reactive properties for responsive behavior
    current_screen_size: reactive[ScreenSize] = reactive(ScreenSize.MEDIUM)
    auto_scroll_enabled: reactive[bool] = reactive(default=True)

    # Performance thresholds
    LARGE_CONTENT_THRESHOLD = 1000  # Lines of content
    SCROLL_DEBOUNCE_MS = 50  # Milliseconds to debounce scroll events

    def __init__(
        self,
        *children: Widget,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
        disabled: bool = False,
        auto_scroll: bool = True,
    ) -> None:
        """Initialize smart scroll view.

        Args:
            *children: Child widgets to add to the scroll view
            name: Name of the widget
            id: ID of the widget
            classes: CSS classes for the widget
            disabled: Whether the widget is disabled
            auto_scroll: Whether to enable automatic scrolling behavior

        """
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.auto_scroll_enabled = auto_scroll
        self._last_scroll_time = 0
        self._content_size_cache = 0

    def on_screen_size_change(
        self,
        size: ScreenSize,
        width: int,  # noqa: ARG002
        height: int,  # noqa: ARG002
    ) -> None:
        """Handle screen size changes for responsive behavior.

        Args:
            size: New screen size category
            width: New screen width
            height: New screen height

        """
        self.current_screen_size = size

        # Adjust scrolling behavior based on screen size
        self._update_scroll_settings()

        # Refresh display if needed
        self.refresh()

    def _update_scroll_settings(self) -> None:
        """Update scroll settings based on current screen size."""
        if self.current_screen_size == ScreenSize.TINY:
            # Minimal scrolling features for tiny screens
            self.show_vertical_scrollbar = False
            self.show_horizontal_scrollbar = False
        elif self.current_screen_size == ScreenSize.SMALL:
            # Basic scrolling for small screens
            self.show_vertical_scrollbar = True
            self.show_horizontal_scrollbar = False
        else:
            # Full scrolling features for medium+ screens
            self.show_vertical_scrollbar = True
            self.show_horizontal_scrollbar = True

    def watch_auto_scroll_enabled(self, enabled: bool) -> None:  # noqa: FBT001
        """React to changes in auto-scroll setting."""
        if enabled:
            self.scroll_end(animate=False)

    def scroll_to_bottom(
        self,
        animate: bool = True,  # noqa: FBT001, FBT002
    ) -> None:
        """Scroll to the bottom of the content.

        Args:
            animate: Whether to animate the scroll

        """
        if self.auto_scroll_enabled:
            self.scroll_end(animate=animate)

    def scroll_to_top(
        self,
        animate: bool = True,  # noqa: FBT001, FBT002
    ) -> None:
        """Scroll to the top of the content.

        Args:
            animate: Whether to animate the scroll

        """
        self.scroll_home(animate=animate)

    def is_at_bottom(self) -> bool:
        """Check if the scroll view is at the bottom.

        Returns:
            True if at bottom, False otherwise

        """
        # Basic implementation - can be enhanced based on container properties
        try:
            return bool(self.scroll_y >= self.max_scroll_y)
        except AttributeError:
            return True

    def is_at_top(self) -> bool:
        """Check if the scroll view is at the top.

        Returns:
            True if at top, False otherwise

        """
        return bool(self.scroll_y == 0)

    def get_content_size(self) -> int:
        """Get the current content size for performance monitoring.

        Returns:
            Number of content lines/items

        """
        # This would need to be implemented based on specific content type
        # For now, return a basic estimate
        return len(self.children)

    def is_large_content(self) -> bool:
        """Check if content exceeds performance thresholds.

        Returns:
            True if content is large and might need optimization

        """
        return self.get_content_size() > self.LARGE_CONTENT_THRESHOLD

    def compose(self) -> ComposeResult:
        """Compose the scroll view with its children."""
        yield from super().compose()

    def on_mount(self) -> None:
        """Handle mount event to set up initial state."""
        self._update_scroll_settings()

    def on_unmount(self) -> None:
        """Handle unmount event for cleanup."""
