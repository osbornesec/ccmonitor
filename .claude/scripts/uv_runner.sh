#!/bin/bash
#
# UV Runner Script for Claude Code Hooks
# Provides consistent Python environment for hook execution
#

set -euo pipefail

# Check if script path is provided
if [ $# -eq 0 ]; then
    echo "Error: No script path provided" >&2
    echo "Usage: $0 <script_path> [args...]" >&2
    exit 1
fi

SCRIPT_PATH="$1"
shift  # Remove script path from arguments

# Validate script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: Script not found: $SCRIPT_PATH" >&2
    exit 1
fi

# Get project directory - handle both relative and absolute paths
if [[ "$SCRIPT_PATH" = /* ]]; then
    # Absolute path - use as-is
    FULL_SCRIPT_PATH="$SCRIPT_PATH"
    PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(dirname "$(dirname "$(dirname "$SCRIPT_PATH")")")}"
else
    # Relative path - resolve from current directory
    PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
    FULL_SCRIPT_PATH="$PROJECT_DIR/$SCRIPT_PATH"
fi

# Validate resolved script path
if [ ! -f "$FULL_SCRIPT_PATH" ]; then
    echo "Error: Resolved script not found: $FULL_SCRIPT_PATH" >&2
    exit 1
fi

# Change to project directory for consistent execution context
cd "$PROJECT_DIR"

# Execute script with UV in virtual environment
# Pass remaining arguments and stdin to the script
exec uv run python "$FULL_SCRIPT_PATH" "$@"