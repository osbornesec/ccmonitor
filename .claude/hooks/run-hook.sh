#!/bin/bash
# Wrapper script to run Claude Code hooks through uv

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get the hook name from first argument
HOOK_NAME="$1"

if [ -z "$HOOK_NAME" ]; then
    echo "Usage: $0 <hook-name>" >&2
    exit 1
fi

# Map hook names to script commands
case "$HOOK_NAME" in
    "pre-tool-use")
        exec uv run claude-hook-pre-tool-use
        ;;
    "post-tool-use")
        exec uv run claude-hook-post-tool-use
        ;;
    "user-prompt-submit")
        exec uv run claude-hook-user-prompt-submit
        ;;
    "session-start")
        exec uv run claude-hook-session-start
        ;;
    "stop")
        exec uv run claude-hook-stop
        ;;
    "notification")
        exec uv run claude-hook-notification
        ;;
    "quality-gate")
        exec uv run claude-hook-quality-gate
        ;;
    *)
        echo "Unknown hook: $HOOK_NAME" >&2
        exit 1
        ;;
esac