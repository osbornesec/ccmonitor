"""Global key binding management for CCMonitor TUI."""

from __future__ import annotations


class KeyBindingManager:
    """Manager for global key bindings and shortcuts."""

    def __init__(self) -> None:
        """Initialize key binding manager."""
        self.bindings: dict[str, str] = {}

    def register_binding(self, key: str, action: str) -> None:
        """Register a key binding."""
        self.bindings[key] = action

    def get_action(self, key: str) -> str | None:
        """Get action for a key binding."""
        return self.bindings.get(key)
