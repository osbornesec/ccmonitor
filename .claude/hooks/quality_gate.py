#!/usr/bin/env python3
"""
Claude Code Hook: Rust Quality Gate Checker
Runs comprehensive quality checks on Rust projects with enterprise-grade standards.
"""

import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Tuple


class QualityGateChecker:
    """Comprehensive quality gate checker for Python projects."""

    def __init__(self, project_dir: str = None):
        """Initialize the quality gate checker."""
        self.project_dir = project_dir or os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
        self.required_configs = ["pyproject.toml", "setup.cfg", "ruff.toml"]
        self.quality_checks = [
            ("format", ["black", "--check", "."]),
            ("lint", ["ruff", "check", "."]),
            ("typecheck", ["mypy", "."]),
        ]

    def change_to_project_dir(self) -> bool:
        """Change to project directory if it exists."""
        if os.path.exists(self.project_dir):
            os.chdir(self.project_dir)
            return True
        return False

    def check_configs_exist(self) -> Tuple[bool, Dict[str, bool]]:
        """Check if all required configuration files exist."""
        config_status = {}
        for config in self.required_configs:
            config_path = os.path.join(self.project_dir, config)
            config_status[config] = os.path.exists(config_path)

        all_exist = all(config_status.values())
        return all_exist, config_status

    def run_quality_check(self, name: str, command: List[str], timeout: int = 60) -> Dict[str, Any]:
        """Run a single quality check command."""
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            return {
                "name": name,
                "command": " ".join(command),
                "returncode": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "passed": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {
                "name": name,
                "command": " ".join(command),
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "passed": False,
            }
        except Exception as e:
            return {
                "name": name,
                "command": " ".join(command),
                "returncode": -2,
                "stdout": "",
                "stderr": f"Command failed: {str(e)}",
                "passed": False,
            }

    def run_all_checks(self) -> Tuple[bool, List[Dict[str, Any]]]:
        """Run all quality checks."""
        results = []
        for name, command in self.quality_checks:
            result = self.run_quality_check(name, command)
            results.append(result)

        all_passed = all(r["passed"] for r in results)
        return all_passed, results

    def format_status_line(self, overall_passed: bool, results: List[Dict[str, Any]]) -> str:
        """Format the status line for display."""
        gate_status = "[OK] PASSED" if overall_passed else "[FAIL] FAILED"

        status_parts = []
        for result in results:
            name = result["name"].title()
            status = "[OK]" if result["passed"] else "[FAIL]"
            status_parts.append(f"{name}: {status}")

        return f'Quality Gate: {gate_status} - {", ".join(status_parts)}'

    def create_hook_output(
        self, configs_exist: bool, overall_passed: bool, results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create the JSON output for Claude Code hook."""
        hook_data = {
            "hookEventName": "Stop",
            "qualityGateStatus": "passed" if overall_passed else "failed",
            "configsExist": configs_exist,
            "checksRun": len(results),
            "timestamp": time.time(),
        }

        # Add individual check statuses
        for result in results:
            status_key = f"{result['name']}Status"
            hook_data[status_key] = "passed" if result["passed"] else "failed"

        # Add detailed results for debugging
        hook_data["detailedResults"] = results

        return {"hookSpecificOutput": hook_data}

    def run(self) -> int:
        """Main execution method."""
        # Change to project directory
        if not self.change_to_project_dir():
            print(f"[WARN] Project directory not found: {self.project_dir}", file=sys.stderr)
            return 1

        # Check configuration files
        configs_exist, config_status = self.check_configs_exist()

        if not configs_exist:
            missing = [f for f, exists in config_status.items() if not exists]
            print(f'[WARN] Missing configuration files: {", ".join(missing)}', file=sys.stderr)
            print("Quality Gate: [SKIP] SKIPPED - Configuration files missing")

            # Output JSON for hook
            hook_output = self.create_hook_output(False, False, [])
            print(json.dumps(hook_output))
            return 0

        # Run quality checks
        overall_passed, results = self.run_all_checks()

        # Print status line
        status_line = self.format_status_line(overall_passed, results)
        print(status_line)

        # Print detailed errors if any checks failed
        for result in results:
            if not result["passed"] and result["stderr"]:
                print(
                    f'[ERROR] {result["name"].title()} failed: {result["stderr"]}', file=sys.stderr
                )

        # Output JSON for hook
        hook_output = self.create_hook_output(configs_exist, overall_passed, results)
        print(json.dumps(hook_output))

        return 0


def main():
    """Entry point for command line execution."""
    checker = QualityGateChecker()
    return checker.run()


if __name__ == "__main__":
    sys.exit(main())
