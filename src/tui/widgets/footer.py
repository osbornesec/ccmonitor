"""CCMonitor footer widget."""

from __future__ import annotations

from textual.widgets import Footer


class CCMonitorFooter(Footer):
    """Custom footer widget for CCMonitor with enhanced styling."""

    DEFAULT_CSS = """
    CCMonitorFooter {
        background: $primary;
        color: $text;
        height: 3;
        dock: bottom;
        content-align: center middle;
        border-top: heavy $secondary;
    }

    CCMonitorFooter Key {
        background: $secondary;
        color: $text;
        text-style: bold;
        padding: 0 1;
        margin: 0 1;
    }
    """

    def __init__(self) -> None:
        """Initialize footer with fade-in animation."""
        super().__init__(classes="fade-in")
