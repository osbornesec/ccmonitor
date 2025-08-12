"""Error dialog widget for displaying errors to users."""

try:
    import pyperclip  # type: ignore[import-not-found]
except ImportError:
    pyperclip = None

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from src.tui.exceptions import RecoverableError, TUIError


class ErrorDialog(ModalScreen[None]):
    """Modal dialog for displaying errors."""

    DEFAULT_CSS = """
    ErrorDialog {
        align: center middle;
    }

    .error-container {
        width: 60;
        min-height: 15;
        max-height: 30;
        background: $surface;
        border: thick $danger;
        padding: 2;
    }

    .error-title {
        text-style: bold;
        color: $danger;
        text-align: center;
        margin-bottom: 1;
    }

    .error-message {
        margin-bottom: 1;
    }

    .error-details {
        border: solid $secondary;
        padding: 1;
        margin-bottom: 1;
        max-height: 10;
        overflow-y: auto;
    }

    .error-buttons {
        align: center middle;
        margin-top: 1;
    }
    """

    def __init__(self, error: TUIError) -> None:
        """Initialize error dialog with error information."""
        super().__init__()
        self.error = error

    def compose(self) -> ComposeResult:
        """Compose error dialog."""
        with Container(classes="error-container"):
            yield Static("⚠️ Error Occurred", classes="error-title")
            yield Static(self.error.user_message, classes="error-message")

            if self.error.details:
                details_text = "\n".join(
                    f"{k}: {v}" for k, v in self.error.details.items()
                )
                yield Static(details_text, classes="error-details")

            with Horizontal(classes="error-buttons"):
                if isinstance(self.error, RecoverableError):
                    yield Button(
                        "Try Recovery",
                        id="recover",
                        variant="warning",
                    )
                yield Button("Copy Details", id="copy", variant="default")
                yield Button("Dismiss", id="dismiss", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "dismiss":
            self._dismiss_dialog()
        elif button_id == "recover":
            self._handle_recovery()
        elif button_id == "copy":
            self._copy_error_details()

    def _dismiss_dialog(self) -> None:
        """Dismiss the error dialog."""
        self.app.pop_screen()

    def _handle_recovery(self) -> None:
        """Handle recovery attempt."""
        if hasattr(
            self.app,
            "error_handler",
        ):
            if self.app.error_handler.attempt_recovery(self.error):
                self.app.pop_screen()
                self.app.notify("Recovery successful", severity="information")
            else:
                self.app.notify("Recovery failed", severity="error")

    def _copy_error_details(self) -> None:
        """Copy error details to clipboard."""
        if pyperclip is not None:
            pyperclip.copy(str(self.error.to_dict()))
            self.app.notify("Error details copied to clipboard")
        else:
            self.app.notify("Copy not available - pyperclip not installed")
