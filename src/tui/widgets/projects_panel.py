"""Projects panel widget for the CCMonitor TUI application."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import ListItem, ListView, Static

if TYPE_CHECKING:
    from textual.app import ComposeResult


class ProjectsPanel(Widget):
    """Left sidebar showing project list and statistics."""

    DEFAULT_CSS = """
    ProjectsPanel {
        width: 25%;
        min-width: 20;
        max-width: 40;
        background: $surface;
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

    #project-list {
        height: 1fr;
        scrollbar-size: 1 1;
    }

    #project-stats {
        height: 5;
        border-top: solid $secondary;
        padding-top: 1;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose projects panel elements."""
        with Vertical(classes="slide-in-left"):
            yield Static("📁 Projects", classes="panel-title")
            yield ListView(
                ListItem(Static("🔷 Project Alpha"), classes="fade-in"),
                ListItem(Static("🔶 Project Beta"), classes="fade-in"),
                ListItem(Static("🔵 Project Gamma"), classes="fade-in"),
                id="project-list",
            )
            yield Static(
                "📊 Stats:\nTotal: 3 projects\nActive: 2\nMessages: 1,234",
                id="project-stats",
                classes="text-center",
            )
