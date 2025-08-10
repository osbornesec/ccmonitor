"""UI transition animations for CCMonitor TUI."""

from __future__ import annotations


class TransitionManager:
    """Manager for UI transition animations."""

    def __init__(self) -> None:
        """Initialize transition manager."""
        self.animation_enabled = True

    def set_animation_enabled(self, *, enabled: bool) -> None:
        """Enable or disable animations."""
        self.animation_enabled = enabled

    def fade_in(self, widget_id: str, duration: float = 0.3) -> None:
        """Apply fade-in animation to widget."""
        if not self.animation_enabled:
            return
        # Placeholder implementation - would integrate with Textual animation system
        _ = widget_id, duration

    def fade_out(self, widget_id: str, duration: float = 0.3) -> None:
        """Apply fade-out animation to widget."""
        if not self.animation_enabled:
            return
        # Placeholder implementation - would integrate with Textual animation system
        _ = widget_id, duration
