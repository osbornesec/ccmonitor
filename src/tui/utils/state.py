"""Application state management for CCMonitor."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any


class AppState:
    """Manages persistent application state."""

    def __init__(self) -> None:
        """Initialize state manager."""
        self.state_file = Path.home() / ".config" / "ccmonitor" / "state.json"
        self.logger = logging.getLogger("ccmonitor.state")
        self.state: dict[str, Any] = {
            "dark_mode": True,
            "is_paused": False,
            "active_project": None,
            "filter_settings": {},
            "window_size": None,
        }

    async def load(self) -> dict[str, Any]:
        """Load saved state from disk."""
        if not self.state_file.exists():
            self.logger.debug("No state file found, using defaults")
            return self.state

        try:
            with self.state_file.open() as f:
                loaded_state = json.load(f)
                self.state.update(loaded_state)
                self.logger.debug(
                    "Application state loaded from %s",
                    self.state_file,
                )
        except (json.JSONDecodeError, OSError) as e:
            self.logger.warning("Failed to load state: %s", e)

        return self.state

    async def save(self) -> None:
        """Save current state to disk."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with self.state_file.open("w") as f:
                json.dump(self.state, f, indent=2)
                self.logger.debug(
                    "Application state saved to %s",
                    self.state_file,
                )
        except OSError as e:
            self.logger.warning("Failed to save state: %s", e)
            raise
