"""CCMonitor header widget."""

from __future__ import annotations

from textual.widgets import Header


class CCMonitorHeader(Header):
    """Custom header widget for CCMonitor with enhanced styling."""

    DEFAULT_CSS = """
    CCMonitorHeader {
        background: $primary;
        color: $text;
        height: 3;
        dock: top;
        text-style: bold;
        content-align: center middle;
        border-bottom: heavy $secondary;
        box-shadow: 0 1 3 0 $primary 30%;
    }
    """

    def __init__(self) -> None:
        """Initialize header with fade-in animation."""
        super().__init__(classes="fade-in")
