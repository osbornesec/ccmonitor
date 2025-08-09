#!/usr/bin/env python3
"""
PreToolUse hooks for protecting configuration files and blocking dangerous commands.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class PreToolUseHandler:
    """Handles PreToolUse hook events."""

    def __init__(self):
        self.project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
        self.protected_files = ["pyproject.toml", "setup.cfg", ".flake8", "ruff.toml", "mypy.ini"]

    def check_protected_file_modification(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Check if the tool is trying to modify protected configuration files."""
        tool_name = data.get("tool_name", "")
        if tool_name not in ["Edit", "MultiEdit", "Write"]:
            return True, None

        file_path = data.get("tool_input", {}).get("file_path", "")
        if not file_path:
            return True, None

        # Convert to absolute path for comparison
        abs_file_path = Path(file_path).resolve()

        # Check if it's a protected file
        for protected_file in self.protected_files:
            protected_path = (self.project_dir / protected_file).resolve()
            if protected_path.exists() and abs_file_path == protected_path:
                return False, (
                    "BLOCKED: Modification of protected configuration files is not allowed. "
                    "These files maintain strict quality standards that cannot be relaxed."
                )

        return True, None

    def check_dangerous_bash_commands(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Check if Bash commands could modify protected configurations."""
        tool_name = data.get("tool_name", "")
        if tool_name != "Bash":
            return True, None

        command = data.get("tool_input", {}).get("command", "")
        if not command:
            return True, None

        # Build dangerous patterns
        dangerous_patterns = []

        # File modification commands
        for protected_file in self.protected_files:
            escaped_file = re.escape(protected_file)
            dangerous_patterns.extend(
                [
                    rf"\bsed\b.*{escaped_file}",
                    rf"\bawk\b.*{escaped_file}",
                    rf"\bperl\b.*{escaped_file}",
                    rf"\bpython\b.*{escaped_file}",
                    rf"\becho\b.*>.*{escaped_file}",
                    rf"\bcat\b.*>.*{escaped_file}",
                    rf"\btee\b.*{escaped_file}",
                    rf"\bmv\b.*{escaped_file}",
                    rf"\bcp\b.*{escaped_file}",
                    rf"\bln\b.*{escaped_file}",
                    rf"\brm\b.*{escaped_file}",
                    rf"\bchmod\b.*{escaped_file}",
                    rf"\btouch\b.*{escaped_file}",
                ]
            )

        # Python configuration commands
        dangerous_patterns.extend(
            [
                r"pip\s+install\s+.*--config-settings",
                r"python\s+-m\s+pip\s+config",
                r"PYTHONPATH\s*=",
                r"PIP_CONFIG_FILE\s*=", 
                r"export\s+(PYTHONPATH|PIP_CONFIG_FILE|PYTHON_*)",
                r"poetry\s+config",
                r"pipenv\s+--.*",
            ]
        )

        # Check for dangerous patterns
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False, (
                    "BLOCKED: Command could modify protected configuration files. "
                    "Quality standards must be maintained."
                )

        return True, None

    def handle(self, data: Dict[str, Any]) -> int:
        """Main handler for PreToolUse events."""
        # Check protected file modifications
        allowed, message = self.check_protected_file_modification(data)
        if not allowed:
            print(message, file=sys.stderr)
            return 2

        # Check dangerous bash commands
        allowed, message = self.check_dangerous_bash_commands(data)
        if not allowed:
            print(message, file=sys.stderr)
            return 2

        return 0


def main():
    """Entry point for PreToolUse hook."""
    try:
        data = json.load(sys.stdin)
        handler = PreToolUseHandler()
        return handler.handle(data)
    except Exception as e:
        print(f"ERROR: PreToolUse hook failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
