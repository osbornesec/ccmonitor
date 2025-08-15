#!/usr/bin/env python3
"""
Stop hook for running final quality gate checks.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict


class StopHandler:
    """Handles Stop hook events - runs final quality gate check."""

    def __init__(self):
        self.project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
        self.quality_gate_script = self.project_dir / ".claude" / "hooks" / "quality_gate.py"

    def handle(self, data: Dict[str, Any]) -> int:  # noqa: ARG002
        """Main handler for Stop events."""
        # Check if quality gate script exists
        if not self.quality_gate_script.exists():
            print(
                f"[WARN] Quality gate script not found: {self.quality_gate_script}", file=sys.stderr
            )
            return 1

        # Run the quality gate check
        try:
            # Change to project directory
            os.chdir(self.project_dir)

            # Execute quality gate
            result = subprocess.run(
                [sys.executable, str(self.quality_gate_script)],
                capture_output=True,
                text=True,
                timeout=120,
            )

            # Output the results
            if result.stdout:
                print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, file=sys.stderr, end="")

            return result.returncode

        except subprocess.TimeoutExpired:
            print("[ERROR] Quality gate check timed out after 120 seconds", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"[ERROR] Quality gate check failed: {e}", file=sys.stderr)
            return 1


def main():
    """Entry point for Stop hook."""
    try:
        data = json.load(sys.stdin)
        handler = StopHandler()
        return handler.handle(data)
    except Exception as e:
        print(f"ERROR: Stop hook failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
