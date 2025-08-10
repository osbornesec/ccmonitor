"""Error screen for the CCMonitor TUI application."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Static

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.binding import Binding


class ErrorScreen(Screen[None]):
    """Global error handler screen for CCMonitor."""

    BINDINGS: ClassVar[
        list[Binding | tuple[str, str] | tuple[str, str, str]]
    ] = [
        ("q", "quit", "Quit"),
        ("escape", "pop_screen", "Go back"),
        ("enter", "acknowledge", "Acknowledge"),
    ]

    def __init__(
        self,
        error_message: str = "An error occurred",
        *,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
    ) -> None:
        """Initialize error screen with error message."""
        super().__init__(name=name, id=id, classes=classes)
        self.error_message = error_message

    def compose(self) -> ComposeResult:
        """Compose the error screen layout."""
        yield Container(
            Vertical(
                Static("⚠️ Critical Error", classes="error-title fade-in"),
                Static(self.error_message, classes="error-message fade-in"),
                Static(""),
                Static(
                    "💡 Actions Available:",
                    classes="section-header",
                ),
                Static("  Enter - Acknowledge error", classes="help-item"),
                Static(
                    "  Escape - Return to previous screen", classes="help-item",
                ),
                Static("  Q - Quit application", classes="help-item"),
                classes="error-content fade-in",
            ),
            id="error-container",
            classes="slide-in-right",
        )

    def on_mount(self) -> None:
        """Handle screen mounting."""
        self.title = "CCMonitor - Error"

    def action_acknowledge(self) -> None:
        """Acknowledge the error and return to previous screen."""
        self.app.pop_screen()
