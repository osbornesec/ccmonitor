"""Main screen for the CCMonitor TUI application."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen

from src.tui.screens.help_screen import HelpOverlay
from src.tui.utils.focus import (
    FocusDirection,
    FocusScope,
    create_panel_focus_group,
    focus_manager,
)
from src.tui.utils.responsive import ScreenSize, responsive_manager
from src.tui.widgets.footer import CCMonitorFooter
from src.tui.widgets.header import CCMonitorHeader
from src.tui.widgets.live_feed_panel import LiveFeedPanel
from src.tui.widgets.projects_panel import ProjectsPanel

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.events import Resize
    from textual.widget import Widget

# Terminal size constants
MIN_TERMINAL_WIDTH = 80
MIN_TERMINAL_HEIGHT = 24
SMALL_TERMINAL_WIDTH = 100
LARGE_TERMINAL_WIDTH = 150


class MainScreen(Screen[None]):
    """Main application screen with responsive three-panel layout."""

    DEFAULT_CSS = """
    MainScreen {
        background: $background;
    }

    #main-container {
        width: 100%;
        height: 100%;
    }

    #content-area {
        width: 100%;
        height: 1fr;
    }
    """

    BINDINGS: ClassVar[
        list[Binding | tuple[str, str] | tuple[str, str, str]]
    ] = [
        # Panel navigation
        Binding("tab", "focus_next_panel", "Next Panel", priority=True),
        Binding(
            "shift+tab",
            "focus_previous_panel",
            "Previous Panel",
            priority=True,
        ),
        Binding("ctrl+tab", "focus_next_panel", "Next Panel", show=False),
        Binding(
            "ctrl+shift+tab",
            "focus_previous_panel",
            "Previous Panel",
            show=False,
        ),
        # Arrow key navigation within panels
        Binding("up", "navigate_up", "Navigate Up", priority=True),
        Binding("down", "navigate_down", "Navigate Down", priority=True),
        Binding("left", "navigate_left", "Navigate Left"),
        Binding("right", "navigate_right", "Navigate Right"),
        # Direct panel focus shortcuts
        Binding("ctrl+1", "focus_projects_panel", "Focus Projects"),
        Binding("ctrl+2", "focus_feed_panel", "Focus Feed"),
        Binding("f1", "focus_projects_panel", "Focus Projects", show=False),
        Binding("f2", "focus_feed_panel", "Focus Feed", show=False),
        # Quick navigation
        Binding("home", "focus_first_panel", "First Panel"),
        Binding("end", "focus_last_panel", "Last Panel"),
        Binding("pageup", "page_up", "Page Up"),
        Binding("pagedown", "page_down", "Page Down"),
        # Selection and action
        Binding("enter", "select_item", "Select Item"),
        Binding("space", "toggle_item", "Toggle Item"),
        # Context navigation
        Binding("escape", "handle_escape", "Back/Cancel", priority=True),
        Binding("backspace", "navigate_back", "Go Back", show=False),
        # Application controls
        Binding("ctrl+h", "show_help", "Show Help"),
        Binding("?", "show_help", "Show Help", show=False),
        Binding("ctrl+r", "refresh_view", "Refresh"),
        Binding("f5", "refresh_view", "Refresh", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Compose the main screen layout with enhanced animations."""
        with Vertical(id="main-container", classes="fade-in"):
            yield CCMonitorHeader()
            with Horizontal(id="content-area"):
                yield ProjectsPanel(
                    id="projects-panel",
                    classes="slide-in-left",
                )
                yield LiveFeedPanel(
                    id="live-feed-panel",
                    classes="slide-in-right",
                )
            yield CCMonitorFooter()

    def on_mount(self) -> None:
        """Set initial focus and initialize responsive behavior."""
        self.title = "CCMonitor - Live Monitoring"

        # Initialize responsive behavior
        self._setup_responsive_behavior()

        # Initialize focus management
        self._setup_focus_management()

        # Set initial focus with enhanced handling
        self._initialize_focus()

    def _setup_focus_management(self) -> None:
        """Set up focus groups and management."""
        # Register focus groups for main panels
        projects_group = create_panel_focus_group(
            "Projects",
            "projects-panel",
            priority=10,
            shortcuts=["ctrl+p", "1"],
        )
        focus_manager.register_focus_group(projects_group)

        feed_group = create_panel_focus_group(
            "Live Feed",
            "live-feed-panel",
            priority=9,
            shortcuts=["ctrl+f", "2"],
        )
        focus_manager.register_focus_group(feed_group)

    def _initialize_focus(self) -> None:
        """Initialize focus with enhanced fallback handling."""
        # Set up the focus manager with app reference
        focus_manager.set_app(self.app)

        # Try to set initial focus to first available widget
        focused_widget = focus_manager.focus_first_available()
        if focused_widget:
            try:
                widget = self.query_one(f"#{focused_widget}")
                widget.focus()
                focus_manager.apply_visual_focus(focused_widget, focused=True)
            except (ValueError, AttributeError) as e:
                self.log(f"Could not focus widget '{focused_widget}': {e}")
                self._fallback_focus()
        else:
            self._fallback_focus()

    def _fallback_focus(self) -> None:
        """Fallback focus initialization."""
        try:
            projects_panel = self.query_one("#projects-panel")
            projects_panel.focus()
            focus_manager.set_focus("projects-panel")
        except (ValueError, AttributeError) as e:
            self.log(f"Could not set fallback focus: {e}")
            # Last resort - use Textual's default focus
            self.focus_next()

    def _setup_responsive_behavior(self) -> None:
        """Configure responsive layout behavior."""
        # Configure responsive breakpoints for the projects panel
        # Note: Configuration could be added here if needed

        # Trigger initial responsive layout
        width, height = self.size
        if width > 0 and height > 0:
            responsive_manager.handle_resize(width, height)

    def action_focus_projects_panel(self) -> None:
        """Focus the projects panel."""
        self._focus_panel_safely("projects-panel")

    def action_focus_feed_panel(self) -> None:
        """Focus the live feed panel."""
        self._focus_panel_safely("live-feed-panel")

    def _focus_panel_safely(self, panel_id: str) -> None:
        """Safely focus a panel with error handling."""
        try:
            widget = self.query_one(f"#{panel_id}")
            widget.focus()
            focus_manager.set_focus(panel_id)
        except (ValueError, AttributeError) as e:
            self.app.bell()
            self.log(f"Failed to focus panel '{panel_id}': {e}")

    def action_refresh_view(self) -> None:
        """Refresh the current view."""
        self.notify("Refreshing main screen...")
        # Refresh all panels
        try:
            for panel_id in ["projects-panel", "live-feed-panel"]:
                panel = self.query_one(f"#{panel_id}")
                if hasattr(panel, "refresh"):
                    panel.refresh()
        except (ValueError, AttributeError) as e:
            self.log(f"Error during refresh: {e}")

    def action_show_help(self) -> None:
        """Show help overlay."""
        # Save current focus for restoration
        current_focus = focus_manager.current_focus
        if current_focus:
            focus_manager.push_focus_context("help-overlay")

        # Show the enhanced help overlay
        help_screen = HelpOverlay()
        self.app.push_screen(help_screen)

    def action_focus_next_panel(self) -> None:
        """Move focus to next panel using focus manager."""
        next_widget = focus_manager.move_focus(
            FocusDirection.NEXT,
            FocusScope.ALL_PANELS,
        )
        if next_widget:
            self._focus_widget_safely(next_widget)
        else:
            # Fallback to Textual's built-in navigation
            self.focus_next()

    def action_focus_previous_panel(self) -> None:
        """Move focus to previous panel using focus manager."""
        prev_widget = focus_manager.move_focus(
            FocusDirection.PREVIOUS,
            FocusScope.ALL_PANELS,
        )
        if prev_widget:
            self._focus_widget_safely(prev_widget)
        else:
            # Fallback to Textual's built-in navigation
            self.focus_previous()

    def action_focus_first_panel(self) -> None:
        """Focus first available panel."""
        first_widget = focus_manager.move_focus(FocusDirection.FIRST)
        if first_widget:
            self._focus_widget_safely(first_widget)

    def action_focus_last_panel(self) -> None:
        """Focus last available panel."""
        last_widget = focus_manager.move_focus(FocusDirection.LAST)
        if last_widget:
            self._focus_widget_safely(last_widget)

    def action_navigate_up(self) -> None:
        """Navigate up within current panel."""
        current_focus = self.focused
        if current_focus and hasattr(current_focus, "action_cursor_up"):
            current_focus.action_cursor_up()
        else:
            # Try to move focus up using focus manager
            next_widget = focus_manager.move_focus(
                FocusDirection.UP,
                FocusScope.CURRENT_PANEL,
            )
            if next_widget:
                self._focus_widget_safely(next_widget)

    def action_navigate_down(self) -> None:
        """Navigate down within current panel."""
        current_focus = self.focused
        if current_focus and hasattr(current_focus, "action_cursor_down"):
            current_focus.action_cursor_down()
        else:
            # Try to move focus down using focus manager
            next_widget = focus_manager.move_focus(
                FocusDirection.DOWN,
                FocusScope.CURRENT_PANEL,
            )
            if next_widget:
                self._focus_widget_safely(next_widget)

    def action_navigate_left(self) -> None:
        """Navigate left (typically previous panel)."""
        self.action_focus_previous_panel()

    def action_navigate_right(self) -> None:
        """Navigate right (typically next panel)."""
        self.action_focus_next_panel()

    def action_page_up(self) -> None:
        """Page up in current panel."""
        current_focus = self.focused
        if current_focus and hasattr(current_focus, "action_page_up"):
            current_focus.action_page_up()
        else:
            self.scroll_up(animate=False)

    def action_page_down(self) -> None:
        """Page down in current panel."""
        current_focus = self.focused
        if current_focus and hasattr(current_focus, "action_page_down"):
            current_focus.action_page_down()
        else:
            self.scroll_down(animate=False)

    def action_select_item(self) -> None:
        """Select current item."""
        current_focus = self.focused
        if current_focus and hasattr(current_focus, "action_select_cursor"):
            current_focus.action_select_cursor()
        # Try to trigger enter on current widget
        elif current_focus:
            # Just pass - let the widget handle it naturally
            pass

    def action_toggle_item(self) -> None:
        """Toggle current item selection."""
        current_focus = self.focused
        if current_focus and hasattr(current_focus, "action_toggle_cursor"):
            current_focus.action_toggle_cursor()

    def action_handle_escape(self) -> None:
        """Handle ESC key with comprehensive fallback logic."""
        if focus_manager.handle_escape_context():
            return  # ESC was handled by focus manager

        # If no specific handling, unfocus current widget
        current_focus = self.focused
        if current_focus:
            current_focus.blur()
        else:
            # Last resort - let the app handle it
            self.app.bell()

    def action_navigate_back(self) -> None:
        """Navigate back using focus history."""
        prev_widget = focus_manager.focus_previous_in_history()
        if prev_widget:
            self._focus_widget_safely(prev_widget)
        else:
            self.action_handle_escape()

    def _focus_widget_safely(self, widget_id: str) -> None:
        """Safely focus a widget with error handling."""
        try:
            widget = self.query_one(f"#{widget_id}")
            widget.focus()
        except (ValueError, AttributeError) as e:
            self.log(f"Failed to focus widget '{widget_id}': {e}")
            self.app.bell()

    async def on_resize(self, event: Resize) -> None:
        """Handle terminal resize events with responsive behavior."""
        width, height = event.size

        # Minimum size warnings
        if width < MIN_TERMINAL_WIDTH or height < MIN_TERMINAL_HEIGHT:
            min_size = f"{MIN_TERMINAL_WIDTH}x{MIN_TERMINAL_HEIGHT}"
            self.notify(
                f"Terminal size: {width}x{height} (min: {min_size})",
                severity="warning",
            )

        # Update responsive manager with new size
        responsive_manager.handle_resize(width, height)

        # Get current screen size category for adaptive behavior
        current_screen_size = responsive_manager.breakpoints.get_screen_size(
            width,
        )

        # Apply responsive layout changes
        await self._apply_responsive_layout(current_screen_size, width, height)

    async def _apply_responsive_layout(
        self,
        screen_size: ScreenSize,
        width: int,
        height: int,
    ) -> None:
        """Apply responsive layout changes based on screen size."""
        try:
            content_area = self.query_one("#content-area")
            projects_panel = self.query_one("#projects-panel")
            live_feed_panel = self.query_one("#live-feed-panel")

            if responsive_manager.should_stack_vertically(screen_size):
                self._apply_vertical_layout(
                    screen_size,
                    projects_panel,
                    live_feed_panel,
                )
                content_area.styles.layout = "vertical"
            else:
                self._apply_horizontal_layout(
                    screen_size,
                    projects_panel,
                    live_feed_panel,
                )
                content_area.styles.layout = "horizontal"

            self._notify_layout_change(screen_size, width, height)

        except (ValueError, AttributeError) as e:
            self.log(f"Error applying responsive layout: {e}")

    def on_unmount(self) -> None:
        """Clean up when screen is unmounted."""
        # Clear focus manager state
        focus_manager.clear_all()

    def _apply_vertical_layout(
        self,
        screen_size: ScreenSize,
        projects_panel: Widget,
        live_feed_panel: Widget,
    ) -> None:
        """Configure vertical layout for small screens."""
        projects_panel.styles.width = "100%"
        projects_panel.styles.height = (
            "8" if screen_size == ScreenSize.TINY else "12"
        )
        live_feed_panel.styles.width = "100%"
        live_feed_panel.styles.height = "1fr"

    def _apply_horizontal_layout(
        self,
        screen_size: ScreenSize,
        projects_panel: Widget,
        live_feed_panel: Widget,
    ) -> None:
        """Configure horizontal layout for larger screens."""
        live_feed_panel.styles.height = "1fr"
        projects_panel.styles.height = "1fr"
        live_feed_panel.styles.width = "1fr"

        if screen_size == ScreenSize.MEDIUM:
            projects_panel.styles.width = "25%"
        elif screen_size == ScreenSize.LARGE:
            projects_panel.styles.width = "20%"
        else:  # XLARGE
            projects_panel.styles.width = "300px"

    def _notify_layout_change(
        self,
        screen_size: ScreenSize,
        width: int,
        height: int,
    ) -> None:
        """Notify user of significant layout changes."""
        if screen_size in (ScreenSize.TINY, ScreenSize.SMALL):
            self.notify(
                f"Layout: Vertical mode ({width}x{height})",
                severity="information",
            )

        # Layout change complete - focus manager will handle focus updates as needed

    def on_focus(self, event: object) -> None:
        """Handle focus events for the main screen."""
        # Ensure focus manager is aware of focus changes
        if hasattr(event, "widget") and hasattr(event.widget, "id"):
            widget_id = event.widget.id
            if widget_id:
                focus_manager.set_focus(widget_id)

    def on_blur(self, event: object) -> None:
        """Handle blur events for the main screen."""
        # Clean up visual focus indicators when losing focus
        if hasattr(event, "widget") and hasattr(event.widget, "id"):
            widget_id = event.widget.id
            if widget_id:
                focus_manager.apply_visual_focus(widget_id, focused=False)
