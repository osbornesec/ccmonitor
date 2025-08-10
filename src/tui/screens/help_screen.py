"""Enhanced Help overlay screen with focus trapping and dynamic content."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.binding import Binding
from textual.containers import (
    Container,
    Horizontal,
    ScrollableContainer,
)
from textual.screen import ModalScreen
from textual.widgets import Button, Static, TabbedContent, TabPane

from src.tui.utils.focus import focus_manager

if TYPE_CHECKING:
    from textual.app import ComposeResult


class HelpOverlay(ModalScreen[None]):
    """Comprehensive help overlay with focus trapping and dynamic shortcuts."""

    DEFAULT_CSS = """
    HelpOverlay {
        align: center middle;
        background: $surface 90%;
    }

    #help-modal {
        width: 90%;
        max-width: 80;
        height: 90%;
        max-height: 30;
        background: $panel;
        border: thick $accent;
        border-title-align: center;
        border-title-color: $accent;
        border-title-background: $panel;
        border-title-style: bold;
        padding: 1;
        box-shadow: 0 4 8 2 $accent 30%;
    }

    .help-header {
        height: 3;
        text-align: center;
        text-style: bold;
        color: $accent;
        background: $surface;
        border-bottom: heavy $secondary;
        content-align: center middle;
    }

    .help-tabs {
        height: 1fr;
        margin-top: 1;
    }

    .help-footer {
        height: 3;
        border-top: heavy $secondary;
        padding-top: 1;
        text-align: center;
        color: $text-muted;
    }

    .shortcut-grid {
        layout: grid;
        grid-size: 2 1;
        grid-gutter: 1 1;
        height: auto;
    }

    .shortcut-category {
        margin-bottom: 1;
        padding: 1;
        background: $surface;
        border: solid $secondary;
    }

    .category-title {
        text-style: bold;
        color: $primary;
        text-align: center;
        background: $panel;
        padding: 0 1;
        margin-bottom: 1;
        border-bottom: thin $secondary;
    }

    .shortcut-item {
        padding: 0 1;
        margin-bottom: 0;
        color: $text;
    }

    .key-combo {
        text-style: bold;
        color: $accent;
        background: $secondary 20%;
        padding: 0 1;
        border-radius: 1;
    }

    .dynamic-shortcuts {
        background: $accent 10%;
        border: solid $accent 50%;
        padding: 1;
        margin-top: 1;
    }

    .focus-info {
        background: $primary 10%;
        border: solid $primary 50%;
        padding: 1;
        color: $text;
        text-align: center;
    }
    """

    BINDINGS: ClassVar[
        list[Binding | tuple[str, str] | tuple[str, str, str]]
    ] = [
        Binding("escape", "dismiss", "Close Help", priority=True),
        Binding("q", "dismiss", "Close Help", show=False),
        Binding("tab", "focus_next", "Next", priority=True),
        Binding("shift+tab", "focus_previous", "Previous", priority=True),
        Binding("1", "show_navigation", "Navigation", show=False),
        Binding("2", "show_shortcuts", "Shortcuts", show=False),
        Binding("3", "show_focus", "Focus System", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Compose the comprehensive help overlay."""
        with Container(id="help-modal", classes="slide-in-right"):
            yield Static(
                "📖 CCMonitor Help & Navigation Guide",
                classes="help-header",
            )
            with TabbedContent(classes="help-tabs", id="help-tabs"):
                with TabPane("🧭 Navigation", id="nav-tab"):
                    yield self._create_navigation_help()
                with TabPane("⌨️  Shortcuts", id="shortcuts-tab"):
                    yield self._create_shortcuts_help()
                with TabPane("🎯 Focus System", id="focus-tab"):
                    yield self._create_focus_help()
                with TabPane("📊 Status", id="status-tab"):
                    yield self._create_status_help()
            yield self._create_footer()

    def _create_navigation_help(self) -> ScrollableContainer:
        """Create navigation help content."""
        return ScrollableContainer(
            Static("Navigation Controls", classes="category-title"),
            Static("🔄 Panel Navigation:", classes="section-header"),
            Static("  Tab, Ctrl+Tab - Next panel", classes="shortcut-item"),
            Static(
                "  Shift+Tab, Ctrl+Shift+Tab - Previous panel",
                classes="shortcut-item",
            ),
            Static("  ↑↓←→ - Navigate within panels", classes="shortcut-item"),
            Static("  Home - Jump to first panel", classes="shortcut-item"),
            Static("  End - Jump to last panel", classes="shortcut-item"),
            Static(""),
            Static("🎯 Direct Panel Access:", classes="section-header"),
            Static(
                "  Ctrl+1, F1 - Focus Projects panel",
                classes="shortcut-item",
            ),
            Static(
                "  Ctrl+2, F2 - Focus Live Feed panel",
                classes="shortcut-item",
            ),
            Static(""),
            Static(
                "📋 List Navigation (NavigableList):",
                classes="section-header",
            ),
            Static("  ↑/k - Previous item", classes="shortcut-item"),
            Static("  ↓/j - Next item (Vim-style)", classes="shortcut-item"),
            Static("  Home, g,g - First item", classes="shortcut-item"),
            Static("  End, Shift+G - Last item", classes="shortcut-item"),
            Static(
                "  PageUp/PageDown - Page navigation",
                classes="shortcut-item",
            ),
            Static("  Enter - Select current item", classes="shortcut-item"),
            Static("  Space - Toggle item selection", classes="shortcut-item"),
            Static(
                "  1-9,0 - Quick jump to item number",
                classes="shortcut-item",
            ),
        )

    def _create_shortcuts_help(self) -> ScrollableContainer:
        """Create shortcuts help with dynamic content."""
        shortcuts_content = ScrollableContainer()

        # Add static application shortcuts
        shortcuts_content.mount(
            Static("Application Shortcuts", classes="category-title"),
        )
        shortcuts_content.mount(
            Static("🔧 System Controls:", classes="section-header"),
        )
        shortcuts_content.mount(
            Static("  Ctrl+H, ? - Show/hide help", classes="shortcut-item"),
        )
        shortcuts_content.mount(
            Static("  Ctrl+R, F5 - Refresh view", classes="shortcut-item"),
        )
        shortcuts_content.mount(
            Static("  Escape - Back/Cancel context", classes="shortcut-item"),
        )
        shortcuts_content.mount(
            Static("  Backspace - Navigate back", classes="shortcut-item"),
        )
        shortcuts_content.mount(Static(""))

        # Add dynamic shortcuts from focus manager
        dynamic_shortcuts = self._get_dynamic_shortcuts()
        if dynamic_shortcuts:
            shortcuts_content.mount(
                Container(
                    Static(
                        "🎯 Dynamic Panel Shortcuts:",
                        classes="category-title",
                    ),
                    *[
                        Static(
                            f"  {shortcut} - {desc}",
                            classes="shortcut-item",
                        )
                        for shortcut, desc in dynamic_shortcuts.items()
                    ],
                    classes="dynamic-shortcuts",
                ),
            )

        return shortcuts_content

    def _create_focus_help(self) -> ScrollableContainer:
        """Create focus system help content."""
        current_focus = focus_manager.current_focus
        focus_groups = list(focus_manager.focus_groups.keys())
        focus_history = len(focus_manager.focus_history)

        return ScrollableContainer(
            Static("Focus Management System", classes="category-title"),
            Static("🔍 Current Status:", classes="section-header"),
            Container(
                Static(
                    f"Active Focus: {current_focus or 'None'}",
                    classes="shortcut-item",
                ),
                Static(
                    (
                        f"Registered Groups: "
                        f"{', '.join(focus_groups) if focus_groups else 'None'}"
                    ),
                    classes="shortcut-item",
                ),
                Static(
                    f"History Length: {focus_history}",
                    classes="shortcut-item",
                ),
                classes="focus-info",
            ),
            Static(""),
            Static("🎛️  Focus Controls:", classes="section-header"),
            Static(
                "  Tab - Move to next focusable element",
                classes="shortcut-item",
            ),
            Static(
                "  Shift+Tab - Move to previous focusable element",
                classes="shortcut-item",
            ),
            Static(
                "  Escape - Navigate focus context stack",
                classes="shortcut-item",
            ),
            Static(
                "  Backspace - Go back in focus history",
                classes="shortcut-item",
            ),
            Static(""),
            Static("💡 Visual Indicators:", classes="section-header"),
            Static(
                "  • Thick accent border - Active focus",
                classes="shortcut-item",
            ),
            Static(
                "  • Glowing animation - Focus manager control",
                classes="shortcut-item",
            ),
            Static(
                "  • Cursor highlighting - NavigableList selection",
                classes="shortcut-item",
            ),
            Static(
                "  • Panel background tint - Panel-level focus",
                classes="shortcut-item",
            ),
        )

    def _create_status_help(self) -> ScrollableContainer:
        """Create status and information help content."""
        return ScrollableContainer(
            Static("Application Status & Info", classes="category-title"),
            Static("📊 Current State:", classes="section-header"),
            Static("  Navigation System: ✓ Active", classes="shortcut-item"),
            Static("  Focus Management: ✓ Enhanced", classes="shortcut-item"),
            Static("  Visual Indicators: ✓ Animated", classes="shortcut-item"),
            Static(
                "  Keyboard Navigation: ✓ Full Support",
                classes="shortcut-item",
            ),
            Static(""),
            Static("🛠️  Features:", classes="section-header"),
            Static(
                "  • Multi-panel layout with responsive design",
                classes="shortcut-item",
            ),
            Static(
                "  • Advanced keyboard navigation",
                classes="shortcut-item",
            ),
            Static(
                "  • Focus management with visual feedback",
                classes="shortcut-item",
            ),
            Static("  • Context-aware help system", classes="shortcut-item"),
            Static(
                "  • Smooth animations and transitions",
                classes="shortcut-item",
            ),
            Static(""),
            Static("⚡ Performance:", classes="section-header"),
            Static(
                "  • Optimized rendering with targeted updates",
                classes="shortcut-item",
            ),
            Static("  • Efficient event handling", classes="shortcut-item"),
            Static(
                "  • Memory-conscious widget management",
                classes="shortcut-item",
            ),
        )

    def _create_footer(self) -> Container:
        """Create help footer with action buttons."""
        return Container(
            Horizontal(
                Button("Navigation [1]", id="nav-btn", classes="-secondary"),
                Button(
                    "Shortcuts [2]",
                    id="shortcuts-btn",
                    classes="-secondary",
                ),
                Button("Focus [3]", id="focus-btn", classes="-secondary"),
                Button("Close [ESC]", id="close-btn", classes="-primary"),
                classes="button-group",
            ),
            classes="help-footer",
        )

    def _get_dynamic_shortcuts(self) -> dict[str, str]:
        """Get dynamic shortcuts from focus manager."""
        shortcuts = {}

        # Get shortcuts from registered focus groups
        for group in focus_manager.focus_groups.values():
            for widget in group.widgets:
                if widget.keyboard_shortcuts:
                    for shortcut in widget.keyboard_shortcuts:
                        shortcuts[shortcut] = f"Focus {widget.display_name}"

        return shortcuts

    def on_mount(self) -> None:
        """Set up focus trapping and initial state."""
        self.title = "CCMonitor - Help"

        # Save focus state for restoration
        if focus_manager.current_focus:
            focus_manager.push_focus_context("help-overlay")

        # Set initial tab focus
        try:
            tabs = self.query_one("#help-tabs")
            tabs.focus()
        except (ValueError, AttributeError) as e:
            self.log(f"Could not focus tabs: {e}")

    async def action_dismiss(self, result: None = None) -> None:
        """Dismiss help and restore focus."""
        # Restore previous focus context
        focus_manager.pop_focus_context()
        self.dismiss(result)

    def action_show_navigation(self) -> None:
        """Show navigation tab."""
        try:
            tabs = self.query_one(TabbedContent)
            tabs.active = "nav-tab"
        except (ValueError, AttributeError) as e:
            self.log(f"Could not switch to navigation tab: {e}")

    def action_show_shortcuts(self) -> None:
        """Show shortcuts tab."""
        try:
            tabs = self.query_one(TabbedContent)
            tabs.active = "shortcuts-tab"
        except (ValueError, AttributeError) as e:
            self.log(f"Could not switch to shortcuts tab: {e}")

    def action_show_focus(self) -> None:
        """Show focus system tab."""
        try:
            tabs = self.query_one(TabbedContent)
            tabs.active = "focus-tab"
        except (ValueError, AttributeError) as e:
            self.log(f"Could not switch to focus tab: {e}")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close-btn":
            await self.action_dismiss()
        elif event.button.id == "nav-btn":
            self.action_show_navigation()
        elif event.button.id == "shortcuts-btn":
            self.action_show_shortcuts()
        elif event.button.id == "focus-btn":
            self.action_show_focus()
