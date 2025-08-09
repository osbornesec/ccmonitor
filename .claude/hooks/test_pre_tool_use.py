#!/usr/bin/env python3
"""Test PreToolUse hook directly."""

import json
import subprocess

# Test data
test_data = {
    "tool_name": "Edit",
    "tool_input": {"file_path": "/mnt/d/CP/rustfmt.toml"}
}

# Set environment for the hook
import os
env = os.environ.copy()
env["CLAUDE_PROJECT_DIR"] = "/mnt/d/CP"

# Run the hook
proc = subprocess.run(
    ["uv", "run", "claude-hook-pre-tool-use"],
    input=json.dumps(test_data),
    capture_output=True,
    text=True,
    env=env
)

print(f"Exit code: {proc.returncode}")
print(f"Stdout: {proc.stdout}")
print(f"Stderr: {proc.stderr}")

if proc.returncode == 2 and "BLOCKED" in proc.stderr:
    print("✓ Test passed: Protected file edit was blocked")
else:
    print("✗ Test failed: Protected file edit was NOT blocked")