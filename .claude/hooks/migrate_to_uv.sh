#!/bin/bash
# Migration script to switch from inline Python hooks to uv-managed hooks

set -e

echo "=== Claude Code Hooks Migration to UV ==="
echo

# Check if we're in the right directory
if [ ! -f ".claude/settings.json" ]; then
    echo "ERROR: This script must be run from the project root directory"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "ERROR: uv is not installed. Please install it first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Backup current settings
echo "1. Backing up current settings.json..."
cp .claude/settings.json .claude/settings_backup_$(date +%Y%m%d_%H%M%S).json
echo "   ✓ Backup created"

# Set up hooks environment
echo
echo "2. Setting up uv environment for hooks..."
cd .claude/hooks

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    uv venv
    echo "   ✓ Virtual environment created"
else
    echo "   ✓ Virtual environment already exists"
fi

# Install hooks package
echo
echo "3. Installing hooks package..."
uv pip install -e .
echo "   ✓ Hooks package installed"

# Test hooks
echo
echo "4. Testing hooks..."
echo '{"prompt": "test"}' | uv run claude-hook-user-prompt-submit > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ UserPromptSubmit hook working"
else
    echo "   ✗ UserPromptSubmit hook failed"
    exit 1
fi

echo '{"tool_name": "Edit", "tool_input": {"file_path": "test.rs"}}' | uv run claude-hook-pre-tool-use > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ PreToolUse hook working"
else
    echo "   ✗ PreToolUse hook failed"
    exit 1
fi

# Copy new settings
cd ../..
echo
echo "5. Installing new uv-based settings..."
cp .claude/settings_uv.json .claude/settings.json
echo "   ✓ New settings.json installed"

echo
echo "=== Migration Complete ==="
echo
echo "The hooks system has been successfully migrated to use uv-managed Python scripts."
echo
echo "What's changed:"
echo "- Inline Python commands replaced with proper Python modules"
echo "- Virtual environment managed by uv"
echo "- Cleaner, more maintainable code structure"
echo "- Better error handling and logging"
echo
echo "To revert if needed:"
echo "  cp .claude/settings_backup_*.json .claude/settings.json"
echo
echo "For more information, see: .claude/hooks/UV_HOOKS_DOCUMENTATION.md"