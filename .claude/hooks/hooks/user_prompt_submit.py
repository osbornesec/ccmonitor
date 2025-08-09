#!/usr/bin/env python3
"""
UserPromptSubmit hook for injecting quality standards context and detecting bypass attempts.
"""

import json
import re
import sys
from typing import Any, Dict


class UserPromptSubmitHandler:
    """Handles UserPromptSubmit hook events."""

    def __init__(self):
        self.bypass_patterns = [
            r"ignore.*lint",
            r"disable.*clippy",
            r"relax.*standard",
            r"less.*strict",
            r"remove.*rule",
            r"allow.*unwrap",
            r"bypass.*hook",
            r"--allow.*dirty",
            r"skip.*format",
            r"temporary.*change",
            r"quick.*fix",
            r"just.*this.*once",
        ]

        self.reminder_context = (
            "REMINDER: This project maintains EXTREMELY STRICT quality standards with "
            "comprehensive linting rules, zero-tolerance formatting, and type checking. "
            "Any attempt to relax these standards will be blocked by hooks. "
            "The current configuration represents the minimum acceptable quality level."
        )

        self.standard_context = (
            "Quality Standards: This Python project enforces enterprise-grade code quality "
            "with strict linting, formatting, and type checking rules."
        )

    def check_bypass_attempt(self, prompt: str) -> bool:
        """Check if the prompt contains bypass attempts."""
        return any(re.search(pattern, prompt, re.IGNORECASE) for pattern in self.bypass_patterns)

    def handle(self, data: Dict[str, Any]) -> int:
        """Main handler for UserPromptSubmit events."""
        prompt = data.get("prompt", "")

        # Check for bypass attempts
        bypass_detected = self.check_bypass_attempt(prompt)

        # Select appropriate context
        context = self.reminder_context if bypass_detected else self.standard_context

        # Create hook output
        hook_output = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context,
            }
        }

        # Output JSON
        print(json.dumps(hook_output))

        return 0


def main():
    """Entry point for UserPromptSubmit hook."""
    try:
        data = json.load(sys.stdin)
        handler = UserPromptSubmitHandler()
        return handler.handle(data)
    except Exception as e:
        print(f"ERROR: UserPromptSubmit hook failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
