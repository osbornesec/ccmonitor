#!/usr/bin/env python3
"""
PostToolUse hooks for auto-formatting, linting, and configuration integrity checks.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class PostToolUseHandler:
    """Handles PostToolUse hook events."""

    def __init__(self):
        self.project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
        self.config_files = {"pyproject.toml": 50, "setup.cfg": 30, "ruff.toml": 20}

    def is_python_file_edit(self, data: Dict[str, Any]) -> Optional[str]:
        """Check if this is a Python file edit and return the file path."""
        tool_name = data.get("tool_name", "")
        if tool_name not in ["Edit", "MultiEdit", "Write"]:
            return None

        file_path = data.get("tool_input", {}).get("file_path", "")
        if file_path and file_path.endswith(".py"):
            return file_path

        return None

    def change_to_project_dir(self) -> bool:
        """Change to project directory if it exists."""
        if self.project_dir.exists():
            os.chdir(self.project_dir)
            return True
        return False

    def run_black_format(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Run black formatting on Python files."""
        if not Path(file_path).exists():
            return True, None

        # First check if formatting is needed
        try:
            fmt_check = subprocess.run(
                ["black", "--check", file_path], capture_output=True, text=True, timeout=30
            )

            if fmt_check.returncode != 0:
                # Run actual formatting
                fmt_result = subprocess.run(
                    ["black", file_path], capture_output=True, text=True, timeout=30
                )

                if fmt_result.returncode == 0:
                    print(f"[OK] Formatted {Path(file_path).name} with black")
                    return True, None
                message = f"[WARN] FORMATTING FAILED: {fmt_result.stderr}"
                return False, message
            else:
                print(f"[OK] {Path(file_path).name} already properly formatted")
                return True, None

        except subprocess.TimeoutExpired:
            return False, "[WARN] FORMATTING TIMEOUT: black took too long"
        except Exception as e:
            return False, f"[WARN] FORMATTING ERROR: {e}"

    def run_ruff_lint(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Run ruff linting on Python files."""
        if not Path(file_path).exists():
            return True, None

        try:
            result = subprocess.run(
                ["ruff", "check", file_path],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                print(f"[OK] Ruff linting passed for {Path(file_path).name}")
                return True, None
            message = (
                "[WARN] RUFF VIOLATIONS DETECTED: "
                "File operation blocked due to linting failures!\n"
                f"{result.stderr}\n{result.stdout}"
            )
            return False, message

        except subprocess.TimeoutExpired:
            return False, "[WARN] RUFF TIMEOUT: ruff took too long"
        except Exception as e:
            return False, f"[WARN] RUFF ERROR: {e}"

    def run_mypy_check(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Run mypy type checking on Python files."""
        if not Path(file_path).exists():
            return True, None

        try:
            result = subprocess.run(["mypy", file_path], capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                print(f"[OK] MyPy type check passed for {Path(file_path).name}")
                return True, None
            message = (
                "[WARN] TYPE ERRORS DETECTED: "
                "File operation blocked due to type check failures!\n"
                f"{result.stderr}\n{result.stdout}"
            )
            return False, message

        except subprocess.TimeoutExpired:
            return False, "[WARN] MYPY TIMEOUT: mypy took too long"
        except Exception as e:
            return False, f"[WARN] MYPY ERROR: {e}"

    def verify_config_integrity(self) -> Tuple[bool, Optional[str]]:
        """Verify configuration file integrity."""
        integrity_ok = True
        messages = []

        for file, _expected_lines in self.config_files.items():
            filepath = self.project_dir / file
            if not filepath.exists():
                continue

            # Read file content
            try:
                content = filepath.read_text()

                # Check specific patterns based on file
                if file == "pyproject.toml":
                    required_patterns = [
                        "[tool.ruff]",
                        "[tool.black]",
                        "[tool.mypy]",
                    ]
                    if not all(pattern in content for pattern in required_patterns):
                        integrity_ok = False
                        messages.append(
                            f"[WARN] INTEGRITY VIOLATION: {file} "
                            "missing critical tool configuration!"
                        )

                elif file == "setup.cfg":
                    required_patterns = ["[flake8]", "[mypy"]
                    if not all(pattern in content for pattern in required_patterns):
                        integrity_ok = False
                        messages.append(
                            f"[WARN] INTEGRITY VIOLATION: {file} missing critical linting config!"
                        )

                elif file == "ruff.toml":
                    required_patterns = ["line-length", "select"]
                    if not all(pattern in content for pattern in required_patterns):
                        integrity_ok = False
                        messages.append(
                            f"[WARN] INTEGRITY VIOLATION: {file} missing critical ruff rules!"
                        )

            except Exception as e:
                integrity_ok = False
                messages.append(f"[WARN] INTEGRITY CHECK ERROR for {file}: {e}")

        if integrity_ok:
            print("[OK] Configuration integrity verified")
            return True, None
        combined_message = "\n".join(messages)
        combined_message += (
            "\n[WARN] Configuration integrity compromised - quality standards may be at risk!"
        )
        return False, combined_message

    def handle(self, data: Dict[str, Any]) -> int:
        """Main handler for PostToolUse events."""
        # Change to project directory
        if not self.change_to_project_dir():
            print(
                f"[WARN] Could not change to project directory: {self.project_dir}", file=sys.stderr
            )

        # Check if this is a Python file edit
        python_file = self.is_python_file_edit(data)

        if python_file:
            # Run formatting
            success, message = self.run_black_format(python_file)
            if not success and message:
                print(message, file=sys.stderr)
                return 2

            # Run linting
            success, message = self.run_ruff_lint(python_file)
            if not success and message:
                print(message, file=sys.stderr)
                return 2

            # Run type checking
            success, message = self.run_mypy_check(python_file)
            if not success and message:
                print(message, file=sys.stderr)
                return 2

        # Always verify config integrity
        success, message = self.verify_config_integrity()
        if not success and message:
            print(message, file=sys.stderr)
            # Don't fail on integrity check, just warn

        return 0


def main():
    """Entry point for PostToolUse hook."""
    try:
        data = json.load(sys.stdin)
        handler = PostToolUseHandler()
        return handler.handle(data)
    except Exception as e:
        print(f"ERROR: PostToolUse hook failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
