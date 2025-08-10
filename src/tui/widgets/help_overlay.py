"""Help overlay widget for displaying keyboard shortcuts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.table import Table
from textual.containers import Container
from textual.widgets import Static

if TYPE_CHECKING:
    from textual.app import ComposeResult


class HelpOverlay(Container):
    """Modal overlay showing comprehensive keyboard shortcuts."""

    DEFAULT_CSS = """
    HelpOverlay {
        layer: overlay;
        background: $surface 90%;
        border: solid $primary;
        padding: 1 2;
        width: 70;
        height: 25;
        align: center middle;
    }

    HelpOverlay > Static {
        text-align: center;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Create the help overlay content."""
        table = Table(title="CCMonitor - Keyboard Shortcuts", show_header=True)
        table.add_column("Key", style="cyan", width=12)
        table.add_column("Action", style="white", width=30)
        table.add_column("Description", style="dim", width=20)

        shortcuts = [
            ("Q", "Quit application", "Exit CCMonitor"),
            ("Ctrl+C", "Force quit", "Emergency exit"),
            ("H", "Toggle this help", "Show/hide help overlay"),
            ("P", "Pause/Resume", "Toggle monitoring"),
            ("F", "Open filter dialog", "Filter conversations"),
            ("R", "Refresh", "Reload current view"),
            ("D", "Toggle dark mode", "Switch theme"),
            ("Tab", "Navigate panels", "Move focus"),
            ("↑↓", "Navigate items", "Select within panel"),
            ("Enter", "Select/Open", "Activate selected item"),
            ("Esc", "Cancel/Back", "Close dialog/go back"),
            ("Space", "Quick action", "Context-specific action"),
            ("1-9", "Switch tabs", "Jump to tab number"),
            ("/", "Quick search", "Search conversations"),
            ("?", "Context help", "Help for current view"),
        ]

        for key, action, description in shortcuts:
            table.add_row(key, action, description)

        yield Static(table, id="shortcuts_table")
        yield Static(
            "\n[dim]Press [cyan]H[/cyan] or [cyan]Esc[/cyan] to close this help[/dim]",
            id="help_footer",
        )

    def key_escape(self) -> None:
        """Close help overlay on escape."""
        self.app.pop_screen()

    def key_h(self) -> None:
        """Close help overlay on 'h' key."""
        self.app.pop_screen()
