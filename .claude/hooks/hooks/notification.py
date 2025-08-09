#!/usr/bin/env python3
"""
Notification hook for logging protection events.
"""

import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict


class NotificationHandler:
    """Handles Notification hook events."""

    def __init__(self):
        self.project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
        self.log_dir = self.project_dir / ".claude"
        self.log_file = self.log_dir / "protection.log"

    def ensure_log_dir(self) -> bool:
        """Ensure log directory exists."""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to create log directory: {e}", file=sys.stderr)
            return False

    def handle(self, data: Dict[str, Any]) -> int:
        """Main handler for Notification events."""
        # Ensure log directory exists
        if not self.ensure_log_dir():
            return 1

        # Get event information
        timestamp = datetime.datetime.now().isoformat()
        event_type = data.get("event_type", "unknown")

        # Create log entry
        log_entry = f"{timestamp} - {event_type} - Protection system active\n"

        # Append to log file
        try:
            with open(self.log_file, "a") as f:
                f.write(log_entry)
            return 0
        except Exception as e:
            print(f"[ERROR] Failed to write log: {e}", file=sys.stderr)
            return 1


def main():
    """Entry point for Notification hook."""
    try:
        data = json.load(sys.stdin)
        handler = NotificationHandler()
        return handler.handle(data)
    except Exception as e:
        print(f"ERROR: Notification hook failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
