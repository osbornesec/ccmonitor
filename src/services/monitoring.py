"""Abstract monitoring service used by both CLI and TUI."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from src.config.manager import ConfigManager


class MonitoringService(ABC):
    """Abstract monitoring service used by both CLI and TUI."""

    @abstractmethod
    def start(self) -> None:
        """Start monitoring."""

    @abstractmethod
    def stop(self) -> None:
        """Stop monitoring."""

    @abstractmethod
    def get_conversations(
        self,
        project: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get conversations for a project."""

    @abstractmethod
    def is_running(self) -> bool:
        """Check if monitoring is currently running."""


class ConversationMonitor(MonitoringService):
    """Concrete implementation of monitoring service."""

    def __init__(self, config: ConfigManager) -> None:
        """Initialize the conversation monitor."""
        self.config = config
        self._is_running = False
        self.watchers: list[dict[str, str]] = []

    def start(self) -> None:
        """Start monitoring conversations."""
        if self._is_running:
            return

        self._initialize_watchers()
        self._is_running = True

    def _initialize_watchers(self) -> None:
        """Initialize file watchers from config."""
        watch_paths = self.config.get("monitoring.watch_paths", [])
        if not isinstance(watch_paths, list):
            return

        for path in watch_paths:
            if isinstance(path, str):
                watcher = self.create_watcher(path)
                if watcher:
                    self.watchers.append(watcher)

    def stop(self) -> None:
        """Stop monitoring."""
        # For now, just clear the watchers list
        # Will be implemented with actual file watcher cleanup when needed
        self.watchers.clear()
        self._is_running = False

    def get_conversations(
        self,
        project: str | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """Get conversations from database."""
        # For now, return empty list - will be implemented when database layer is ready
        return []

    def is_running(self) -> bool:
        """Check if monitoring is currently running."""
        return self._is_running

    def create_watcher(self, path: str) -> dict[str, str] | None:
        """Create a file system watcher for the given path."""
        try:
            watch_path = Path(path)
            if not watch_path.exists():
                return None

            # For now, return a simple placeholder
            # Will be implemented with actual file watcher when needed
            return {"path": str(watch_path), "type": "placeholder"}

        except OSError:
            return None

    def on_file_change(self, event: dict[str, Any]) -> None:
        """Handle file change events."""
        # Process conversation file changes
        # Will be implemented when needed
        _ = event  # Acknowledge unused parameter
