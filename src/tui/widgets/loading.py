"""Loading indicator widget for CCMonitor."""

from __future__ import annotations

from textual.widgets import Static


class LoadingIndicator(Static):
    """Loading indicator widget with animation."""

    def __init__(
        self,
        message: str = "Loading...",
        *,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialize loading indicator."""
        super().__init__(
            message,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.message = message

    def on_mount(self) -> None:
        """Start loading animation when mounted."""
        self.update(self.message)
