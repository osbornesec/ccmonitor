"""Adaptive panel base class with responsive display modes."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.reactive import reactive
from textual.widget import Widget

from src.tui.utils.responsive import ScreenSize, get_responsive_manager
from src.tui.utils.terminal import get_terminal_capabilities

if TYPE_CHECKING:
    from textual.app import ComposeResult


class AdaptivePanel(Widget):
    """Panel that adapts to available space with multiple display modes."""

    # Size thresholds as class constants
    TINY_WIDTH_THRESHOLD: ClassVar[int] = 60
    TINY_HEIGHT_THRESHOLD: ClassVar[int] = 16
    COMPACT_WIDTH_THRESHOLD: ClassVar[int] = 30
    COMPACT_HEIGHT_THRESHOLD: ClassVar[int] = 10
    SPACIOUS_WIDTH_THRESHOLD: ClassVar[int] = 160
    SPACIOUS_HEIGHT_THRESHOLD: ClassVar[int] = 50
    MEDIUM_WIDTH_THRESHOLD: ClassVar[int] = 120
    MEDIUM_HEIGHT_THRESHOLD: ClassVar[int] = 40
    HEADER_FOOTER_HEIGHT: ClassVar[int] = 6
    MIN_PANEL_HEIGHT: ClassVar[int] = 5

    DEFAULT_CSS = """
    AdaptivePanel {
        layout: vertical;
        overflow: hidden;
    }

    .panel-content {
        height: 1fr;
        overflow-y: auto;
    }

    /* Compact mode - minimal space usage */
    .panel-compact {
        padding: 0;
        border: none;
    }

    .panel-compact .optional {
        display: none;
    }

    .panel-compact .panel-title {
        text-style: normal;
        padding: 0;
    }

    /* Normal mode - balanced display */
    .panel-normal {
        padding: 1;
        border: solid $primary;
    }

    .panel-normal .optional {
        display: block;
    }

    .panel-normal .panel-title {
        text-style: bold;
        padding: 0 1;
    }

    /* Spacious mode - enhanced display */
    .panel-spacious {
        padding: 2;
        border: thick $primary;
    }

    .panel-spacious .optional {
        display: block;
    }

    .panel-spacious .panel-title {
        text-style: bold;
        padding: 1 2;
    }

    /* Accessibility adjustments */
    .panel-high-contrast {
        color: $text;
        background: $background;
        border-color: $accent;
    }

    .panel-monochrome {
        color: $text;
        background: $background;
        border: solid;
    }
    """

    # Reactive properties for responsive behavior
    display_mode: reactive[str] = reactive("normal")
    compact_mode: reactive[bool] = reactive(init=False, default=False)
    screen_size: reactive[ScreenSize] = reactive(ScreenSize.MEDIUM)
    terminal_capabilities: reactive[dict[str, bool | str | int]] = reactive(
        dict,
    )

    def __init__(
        self,
        *,
        name: str | None = None,
        widget_id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialize adaptive panel with responsive capabilities."""
        super().__init__(
            name=name,
            id=widget_id,
            classes=classes,
            disabled=disabled,
        )

        # Initialize capabilities detection
        caps = get_terminal_capabilities()
        self.terminal_capabilities = caps.get_optimal_settings()

    def on_mount(self) -> None:
        """Initialize responsive behavior when panel is mounted."""
        # Register with responsive manager for updates
        responsive_manager = get_responsive_manager()
        if responsive_manager:
            responsive_manager.register_widget(self)

        # Apply initial display mode based on current conditions
        self._apply_initial_mode()

    def on_unmount(self) -> None:
        """Clean up when panel is unmounted."""
        # Unregister from responsive manager
        responsive_manager = get_responsive_manager()
        if responsive_manager:
            responsive_manager.unregister_widget(self)

    def on_screen_size_change(
        self,
        size: ScreenSize,
        width: int,
        height: int,
    ) -> None:
        """Handle screen size changes from responsive manager."""
        self.screen_size = size
        self._adapt_to_screen_size(width, height)

    def _apply_initial_mode(self) -> None:
        """Apply initial display mode based on current conditions."""
        # Get current terminal size
        responsive_manager = get_responsive_manager()
        if responsive_manager and responsive_manager.current_size:
            size = responsive_manager.current_size
            self._adapt_to_screen_size(size.width, size.height)
        else:
            # Fallback to normal mode
            self.enter_normal_mode()

    def _adapt_to_screen_size(self, width: int, height: int) -> None:
        """Adapt panel based on available screen space."""
        # Determine mode based on terminal size and capabilities
        if self._should_use_compact_mode(width, height):
            self.enter_compact_mode()
        elif self._should_use_spacious_mode(width, height):
            self.enter_spacious_mode()
        else:
            self.enter_normal_mode()

        # Apply terminal capability adaptations
        self._apply_capability_adaptations()

    def _should_use_compact_mode(self, width: int, height: int) -> bool:
        """Determine if compact mode should be used."""
        # Use compact mode for very small terminals
        if (
            width < self.TINY_WIDTH_THRESHOLD
            or height < self.TINY_HEIGHT_THRESHOLD
        ):
            return True

        # Consider panel-specific size constraints
        available_width = self._get_available_width(width)
        available_height = self._get_available_height(height)

        return (
            available_width < self.COMPACT_WIDTH_THRESHOLD
            or available_height < self.COMPACT_HEIGHT_THRESHOLD
        )

    def _should_use_spacious_mode(self, width: int, height: int) -> bool:
        """Determine if spacious mode should be used."""
        # Use spacious mode for large terminals with good capabilities
        if (
            width >= self.SPACIOUS_WIDTH_THRESHOLD
            and height >= self.SPACIOUS_HEIGHT_THRESHOLD
        ):
            return True

        # Consider terminal capabilities
        caps = self.terminal_capabilities
        if caps.get("use_colors", False) and caps.get("use_unicode", False):
            return (
                width >= self.MEDIUM_WIDTH_THRESHOLD
                and height >= self.MEDIUM_HEIGHT_THRESHOLD
            )

        return False

    def _get_available_width(self, terminal_width: int) -> int:
        """Calculate available width for this panel."""
        responsive_manager = get_responsive_manager()
        if responsive_manager:
            width = responsive_manager.get_adaptive_width("panel")
            # Handle the case where get_adaptive_width returns a string
            if isinstance(width, str):
                if width == "100%":
                    return terminal_width
                if width == "1fr":
                    return terminal_width // 2  # Reasonable fraction
                return terminal_width // 2  # Fallback for other string values
            return int(width)
        return terminal_width // 2  # Reasonable default

    def _get_available_height(self, terminal_height: int) -> int:
        """Calculate available height for this panel."""
        # Account for header, footer, and borders
        return max(
            terminal_height - self.HEADER_FOOTER_HEIGHT,
            self.MIN_PANEL_HEIGHT,
        )

    def enter_compact_mode(self) -> None:
        """Switch to compact display mode."""
        self.display_mode = "compact"
        self.compact_mode = True

        # Update CSS classes
        self.remove_class("panel-normal", "panel-spacious")
        self.add_class("panel-compact")

        # Hide optional elements
        for element in self.query(".optional"):
            element.display = False

        self.log("Entered compact mode")

    def enter_normal_mode(self) -> None:
        """Switch to normal display mode."""
        self.display_mode = "normal"
        self.compact_mode = False

        # Update CSS classes
        self.remove_class("panel-compact", "panel-spacious")
        self.add_class("panel-normal")

        # Show essential elements
        for element in self.query(".essential, .important"):
            element.display = True

        # Show optional elements conditionally
        for element in self.query(".optional"):
            element.display = True

        self.log("Entered normal mode")

    def enter_spacious_mode(self) -> None:
        """Switch to spacious display mode."""
        self.display_mode = "spacious"
        self.compact_mode = False

        # Update CSS classes
        self.remove_class("panel-compact", "panel-normal")
        self.add_class("panel-spacious")

        # Show all elements with enhanced styling
        for element in self.query(".optional, .decorative"):
            element.display = True

        self.log("Entered spacious mode")

    def _apply_capability_adaptations(self) -> None:
        """Apply adaptations based on terminal capabilities."""
        caps = self.terminal_capabilities

        # Handle monochrome terminals
        if not caps.get("use_colors", True):
            self.add_class("panel-monochrome")
        else:
            self.remove_class("panel-monochrome")

        # Handle high contrast needs
        if caps.get("fallback_mode") == "limited_color":
            self.add_class("panel-high-contrast")
        else:
            self.remove_class("panel-high-contrast")

    def watch_display_mode(self, old_mode: str, new_mode: str) -> None:
        """React to display mode changes."""
        if old_mode != new_mode:
            self.log(f"Display mode changed: {old_mode} → {new_mode}")
            self._update_content_for_mode(new_mode)

    def watch_compact_mode(
        self,
        *,
        old_compact: bool,
        new_compact: bool,
    ) -> None:
        """React to compact mode changes."""
        if old_compact != new_compact:
            self._adjust_content_visibility(compact_mode=new_compact)

    def _update_content_for_mode(self, mode: str) -> None:
        """Update content visibility and styling for current mode."""
        # Subclasses can override this to customize behavior

    def _adjust_content_visibility(self, *, compact_mode: bool) -> None:
        """Adjust content visibility based on compact mode."""
        if compact_mode:
            # Hide non-essential elements in compact mode
            for element in self.query(".optional, .decorative"):
                element.display = False
        else:
            # Show elements in normal/spacious modes
            for element in self.query(".optional"):
                element.display = True

    def is_compact_mode(self) -> bool:
        """Check if panel is currently in compact mode."""
        return bool(self.compact_mode)

    def get_display_mode(self) -> str:
        """Get current display mode."""
        return str(self.display_mode)

    def set_display_mode(self, mode: str) -> None:
        """Manually set display mode."""
        if mode == "compact":
            self.enter_compact_mode()
        elif mode == "spacious":
            self.enter_spacious_mode()
        else:
            self.enter_normal_mode()

    def refresh_adaptive_state(self) -> None:
        """Refresh adaptive state based on current conditions."""
        responsive_manager = get_responsive_manager()
        if responsive_manager and responsive_manager.current_size:
            size = responsive_manager.current_size
            self._adapt_to_screen_size(size.width, size.height)

    def compose(self) -> ComposeResult:
        """Compose the adaptive panel content.

        Subclasses should override this method to provide panel content.
        """
        # Base implementation provides empty content
        # Subclasses should implement their specific content
        yield from []
