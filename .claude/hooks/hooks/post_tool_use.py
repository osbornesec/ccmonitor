#!/usr/bin/env python3
"""PostToolUse hooks for auto-formatting, linting, and config integrity checks."""
# ruff: noqa: TRY300
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


class PostToolUseHandler:
    """Handles PostToolUse hook events."""

    def __init__(self) -> None:
        """Initialize the PostToolUse handler."""
        self.project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", str(Path.cwd())))
        self.config_files = {"pyproject.toml": 50, "setup.cfg": 30, "ruff.toml": 20}
        self.enable_auto_commit = (
            os.environ.get("CLAUDE_AUTO_COMMIT", "false").lower() == "true"
        )

    def is_file_edit(self, data: dict[str, Any]) -> str | None:
        """Check if this is a file edit and return the file path."""
        tool_name = data.get("tool_name", "")
        if tool_name not in ["Edit", "MultiEdit", "Write"]:
            return None

        file_path = data.get("tool_input", {}).get("file_path", "")
        return file_path if isinstance(file_path, str) else None

    def is_python_file_edit(self, data: dict[str, Any]) -> str | None:
        """Check if this is a Python file edit and return the file path."""
        file_path = self.is_file_edit(data)
        if file_path and file_path.endswith(".py"):
            return file_path
        return None

    def change_to_project_dir(self) -> bool:
        """Change to project directory if it exists."""
        if self.project_dir.exists():
            os.chdir(self.project_dir)
            return True
        return False

    def run_black_format(self, file_path: str) -> tuple[bool, str | None]:
        """Run black formatting on Python files."""
        if not Path(file_path).exists():
            return True, None

        try:
            fmt_check = subprocess.run(
                ["black", "--check", file_path],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            if fmt_check.returncode != 0:
                return self._apply_black_formatting(file_path)

            print(f"[OK] {Path(file_path).name} already properly formatted")
            return True, None

        except subprocess.TimeoutExpired:
            return False, "[WARN] FORMATTING TIMEOUT: black took too long"
        except (subprocess.SubprocessError, OSError) as e:
            return False, f"[WARN] FORMATTING ERROR: {e}"

    def _apply_black_formatting(self, file_path: str) -> tuple[bool, str | None]:
        """Apply black formatting to a file."""
        fmt_result = subprocess.run(
            ["black", file_path],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        if fmt_result.returncode == 0:
            print(f"[OK] Formatted {Path(file_path).name} with black")
            return True, None

        return False, f"[WARN] FORMATTING FAILED: {fmt_result.stderr}"

    def run_ruff_lint(self, file_path: str) -> tuple[bool, str | None]:
        """Run ruff linting on Python files."""
        if not Path(file_path).exists():
            return True, None

        try:
            result = subprocess.run(
                ["ruff", "check", file_path],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
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
        except (subprocess.SubprocessError, OSError) as e:
            return False, f"[WARN] RUFF ERROR: {e}"

    def run_mypy_check(self, file_path: str) -> tuple[bool, str | None]:
        """Run mypy type checking on Python files."""
        if not Path(file_path).exists():
            return True, None

        try:
            result = subprocess.run(
                ["uv", "run", "--with", "mypy", "mypy", file_path],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

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
        except (subprocess.SubprocessError, OSError) as e:
            return False, f"[WARN] MYPY ERROR: {e}"

    def _check_pyproject_integrity(self, content: str) -> list[str]:
        """Check pyproject.toml integrity."""
        required_patterns = ["[tool.ruff]", "[tool.black]", "[tool.mypy]"]
        return [
            f"missing {pattern}"
            for pattern in required_patterns
            if pattern not in content
        ]

    def _check_setup_cfg_integrity(self, content: str) -> list[str]:
        """Check setup.cfg integrity."""
        required_patterns = ["[flake8]", "[mypy"]
        return [
            f"missing {pattern}"
            for pattern in required_patterns
            if pattern not in content
        ]

    def _check_ruff_toml_integrity(self, content: str) -> list[str]:
        """Check ruff.toml integrity."""
        required_patterns = ["line-length", "select"]
        return [
            f"missing {pattern}"
            for pattern in required_patterns
            if pattern not in content
        ]

    def verify_config_integrity(self) -> tuple[bool, str | None]:
        """Verify configuration file integrity."""
        integrity_ok = True
        messages = []

        checkers = {
            "pyproject.toml": self._check_pyproject_integrity,
            "setup.cfg": self._check_setup_cfg_integrity,
            "ruff.toml": self._check_ruff_toml_integrity,
        }

        for file in self.config_files:
            filepath = self.project_dir / file
            if not filepath.exists():
                continue

            try:
                content = filepath.read_text()
                checker = checkers.get(file)
                if checker:
                    issues = checker(content)
                    if issues:
                        integrity_ok = False
                        issues_str = ", ".join(issues)
                        messages.append(
                            f"[WARN] INTEGRITY VIOLATION: {file} {issues_str}",
                        )

            except (OSError, UnicodeDecodeError) as e:
                integrity_ok = False
                messages.append(f"[WARN] INTEGRITY CHECK ERROR for {file}: {e}")

        if integrity_ok:
            print("[OK] Configuration integrity verified")
            return True, None

        combined_message = "\n".join(messages)
        combined_message += (
            "\n[WARN] Configuration integrity compromised - "
            "quality standards may be at risk!"
        )
        return False, combined_message

    def auto_commit_changes(self, file_path: str) -> tuple[bool, str | None]:
        """Auto-commit changes if enabled."""
        if not self.enable_auto_commit:
            return True, None

        try:
            return self._execute_git_commit(file_path)
        except subprocess.TimeoutExpired:
            return False, "[WARN] Auto-commit timeout"
        except (subprocess.SubprocessError, OSError) as e:
            return False, f"[WARN] Auto-commit error: {e}"

    def _execute_git_commit(self, file_path: str) -> tuple[bool, str | None]:
        """Execute git commit operations."""
        # Check if we're in a git repository
        git_check = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            timeout=10,
            check=False,
        )
        if git_check.returncode != 0:
            return True, "[INFO] Not in a git repository, skipping auto-commit"

        # Add the specific file
        add_result = subprocess.run(
            ["git", "add", file_path],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if add_result.returncode != 0:
            return False, f"[WARN] Failed to add {file_path}: {add_result.stderr}"

        # Check if there are staged changes
        status_result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            capture_output=True,
            timeout=10,
            check=False,
        )

        # If no staged changes (returncode 0), skip commit
        if status_result.returncode == 0:
            return True, None

        # Create and execute commit
        return self._create_commit(file_path)

    def _create_commit(self, file_path: str) -> tuple[bool, str | None]:
        """Create git commit for the file."""
        file_name = Path(file_path).name
        commit_msg = (
            f"Auto-commit: Update {file_name}\n\n"
            f"🤖 Generated with [Claude Code](https://claude.ai/code)\n\n"
            f"Co-Authored-By: Claude <noreply@anthropic.com>"
        )

        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        if commit_result.returncode == 0:
            print(f"[OK] Auto-committed changes to {file_name}")
            return True, None

        return False, f"[WARN] Auto-commit failed: {commit_result.stderr}"

    def handle(self, data: dict[str, Any]) -> int:
        """Handle PostToolUse events."""
        # Change to project directory
        if not self.change_to_project_dir():
            print(
                f"[WARN] Could not change to project directory: {self.project_dir}",
                file=sys.stderr,
            )

        # Check if this is a file edit (for auto-commit)
        edited_file = self.is_file_edit(data)

        # Check if this is a Python file edit (for linting/formatting)
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

        # Auto-commit if enabled and file was edited
        if edited_file:
            success, message = self.auto_commit_changes(edited_file)
            if not success and message:
                print(message, file=sys.stderr)
                # Don't fail on auto-commit issues, just warn

        # Always verify config integrity
        success, message = self.verify_config_integrity()
        if not success and message:
            print(message, file=sys.stderr)
            # Don't fail on integrity check, just warn

        return 0


def main() -> int:
    """Entry point for PostToolUse hook."""
    try:
        data = json.load(sys.stdin)
        handler = PostToolUseHandler()
        return handler.handle(data)
    except (json.JSONDecodeError, KeyError, OSError) as e:
        print(f"ERROR: PostToolUse hook failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
