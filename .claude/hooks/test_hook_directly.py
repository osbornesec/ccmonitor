#!/usr/bin/env python3
"""Direct test of PreToolUse hook."""

import json
import sys
import os

# Set the project directory
os.environ["CLAUDE_PROJECT_DIR"] = "/mnt/d/CP"

# Import the handler
from hooks.pre_tool_use import PreToolUseHandler

# Test data
test_data = {
    "tool_name": "Edit",
    "tool_input": {"file_path": "rustfmt.toml"}
}

# Create handler and test
handler = PreToolUseHandler()
print(f"Project dir: {handler.project_dir}")
print(f"Protected files: {handler.protected_files}")

# Check what's happening
from pathlib import Path

file_path = test_data.get('tool_input', {}).get('file_path', '')
abs_file_path = Path(file_path).resolve()
print(f"Input file path: {file_path}")
print(f"Resolved path: {abs_file_path}")

for protected_file in handler.protected_files:
    protected_path = (handler.project_dir / protected_file).resolve()
    print(f"Protected: {protected_file} -> {protected_path} (exists: {protected_path.exists()})")
    if protected_path.exists() and abs_file_path == protected_path:
        print(f"MATCH! {abs_file_path} == {protected_path}")

allowed, message = handler.check_protected_file_modification(test_data)
print(f"Allowed: {allowed}, Message: {message}")

result = handler.handle(test_data)

print(f"Exit code: {result}")
if result == 2:
    print("✓ Successfully blocked protected file edit")
else:
    print("✗ Failed to block protected file edit")