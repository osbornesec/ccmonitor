#!/usr/bin/env python3
"""
SessionStart hook for initializing session with quality standards reminder.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict


class SessionStartHandler:
    """Handles SessionStart hook events."""

    def __init__(self):
        self.project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
        self.config_files = ["pyproject.toml", "setup.cfg", ".flake8", "ruff.toml", "mypy.ini"]

    def check_config_status(self) -> Dict[str, bool]:
        """Check which configuration files exist."""
        status = {}
        for config_file in self.config_files:
            config_path = self.project_dir / config_file
            status[config_file] = config_path.exists()
        return status

    def handle(self, data: Dict[str, Any]) -> int:  # noqa: ARG002
        """Main handler for SessionStart events."""
        # Check configuration status
        config_status = self.check_config_status()
        all_present = all(config_status.values())

        # Print initialization messages
        print("[LOCK] QUALITY STANDARDS PROTECTION ACTIVE")
        print("[LIST] Protected Configuration Files:")

        for config_file, exists in config_status.items():
            status = "[OK]" if exists else "[MISSING]"
            print(f"  - {config_file}: {status}")

        print("[WARN] Modifications to these files are BLOCKED")
        print("[TARGET] Auto-quality checks: black, ruff, mypy enabled")

        if all_present:
            print("[SHIELD] Enterprise-grade Python standards enforced")
        else:
            print("[WARN] Some configuration files missing - protection may be incomplete")

        return 0


def main():
    """Entry point for SessionStart hook."""
    try:
        data = json.load(sys.stdin)
        handler = SessionStartHandler()
        return handler.handle(data)
    except Exception as e:
        print(f"ERROR: SessionStart hook failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
