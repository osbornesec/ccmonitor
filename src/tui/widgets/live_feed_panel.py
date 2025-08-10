"""Live feed panel widget for the CCMonitor TUI application."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import Vertical
from textual.scroll_view import ScrollView
from textual.widget import Widget
from textual.widgets import Input, Static

if TYPE_CHECKING:
    from textual.app import ComposeResult


class LiveFeedPanel(Widget):
    """Main content area for live message feed."""

    DEFAULT_CSS = """
    LiveFeedPanel {
        width: 1fr;
        background: $background;
        border: solid $primary;
        padding: 1;
    }

    .panel-title {
        text-style: bold;
        color: $primary;
        padding-bottom: 1;
        border-bottom: solid $secondary;
        margin-bottom: 1;
    }

    #message-scroll {
        height: 1fr;
        scrollbar-size: 1 1;
        border: solid $secondary;
        padding: 1;
    }

    #message-input {
        height: 3;
        margin-top: 1;
        border: solid $primary;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose live feed panel elements."""
        with Vertical(classes="slide-in-right"):
            yield Static("📨 Live Feed", classes="panel-title")

            with ScrollView(id="message-scroll", classes="fade-in"):
                yield Static(
                    "[10:23:45] 👤 User: How do I implement a parser?\n"
                    "[10:23:47] 🤖 Assistant: I'll help you implement...\n"
                    "[10:23:50] 🔧 Tool: Analyzing code structure...\n"
                    "[10:23:52] ✅ Status: Analysis complete\n"
                    "[10:23:53] 📝 Note: Ready for next query...\n",
                    id="message-content",
                )

            yield Input(
                placeholder="🔍 Filter messages (regex supported)...",
                id="message-input",
            )
