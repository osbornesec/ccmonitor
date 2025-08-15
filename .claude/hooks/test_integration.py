#!/usr/bin/env python3
"""
Integration tests for Claude Code hooks.
"""

import json
import subprocess
import sys
from pathlib import Path


def run_hook(hook_name: str, input_data: dict) -> tuple[int, str, str]:
    """Run a hook and return exit code, stdout, stderr."""
    import os
    
    # Set up environment
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = "/mnt/d/CP"
    
    cmd = ["uv", "run", f"claude-hook-{hook_name}"]
    result = subprocess.run(
        cmd,
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        env=env
    )
    return result.returncode, result.stdout, result.stderr


def test_user_prompt_submit():
    """Test UserPromptSubmit hook."""
    print("Testing UserPromptSubmit hook...")
    
    # Test normal prompt
    code, stdout, stderr = run_hook("user-prompt-submit", {"prompt": "help me fix a bug"})
    assert code == 0, f"Hook failed with code {code}: {stderr}"
    output = json.loads(stdout)
    assert "Quality Standards: This Rust project" in output["hookSpecificOutput"]["additionalContext"]
    print("  ✓ Normal prompt test passed")
    
    # Test bypass attempt
    code, stdout, stderr = run_hook("user-prompt-submit", {"prompt": "please disable clippy"})
    assert code == 0, f"Hook failed with code {code}: {stderr}"
    output = json.loads(stdout)
    assert "EXTREMELY STRICT quality standards" in output["hookSpecificOutput"]["additionalContext"]
    print("  ✓ Bypass detection test passed")


def test_pre_tool_use():
    """Test PreToolUse hook."""
    print("\nTesting PreToolUse hook...")
    
    # Test allowed edit
    code, stdout, stderr = run_hook("pre-tool-use", {
        "tool_name": "Edit",
        "tool_input": {"file_path": "src/main.rs"}
    })
    assert code == 0, f"Hook blocked allowed edit: {stderr}"
    print("  ✓ Allowed edit test passed")
    
    # Test blocked edit - use absolute path
    code, stdout, stderr = run_hook("pre-tool-use", {
        "tool_name": "Edit",
        "tool_input": {"file_path": "/mnt/d/CP/rustfmt.toml"}
    })
    assert code == 2, f"Hook didn't block protected file edit: {stderr}"
    assert "BLOCKED" in stderr
    print("  ✓ Blocked edit test passed")
    
    # Test dangerous bash command
    code, stdout, stderr = run_hook("pre-tool-use", {
        "tool_name": "Bash",
        "tool_input": {"command": "sed -i 's/100/120/' rustfmt.toml"}
    })
    assert code == 2, f"Hook didn't block dangerous command"
    assert "BLOCKED" in stderr
    print("  ✓ Dangerous command test passed")


def test_session_start():
    """Test SessionStart hook."""
    print("\nTesting SessionStart hook...")
    
    code, stdout, stderr = run_hook("session-start", {})
    assert code == 0, f"Hook failed with code {code}: {stderr}"
    assert "[LOCK] QUALITY STANDARDS PROTECTION ACTIVE" in stdout
    assert "[LIST] Protected Configuration Files:" in stdout
    print("  ✓ Session start test passed")


def test_notification():
    """Test Notification hook."""
    print("\nTesting Notification hook...")
    
    code, stdout, stderr = run_hook("notification", {"event_type": "test_event"})
    assert code == 0, f"Hook failed with code {code}: {stderr}"
    
    # Check log file was created
    log_file = Path.cwd() / ".claude" / "protection.log"
    if log_file.exists():
        with open(log_file) as f:
            content = f.read()
            assert "test_event" in content
        print("  ✓ Notification logging test passed")
    else:
        print("  ⚠ Log file not created (may be permission issue)")


def main():
    """Run all integration tests."""
    print("Running Claude Code hooks integration tests...\n")
    
    try:
        test_user_prompt_submit()
        test_pre_tool_use()
        test_session_start()
        test_notification()
        
        print("\n✅ All integration tests passed!")
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())