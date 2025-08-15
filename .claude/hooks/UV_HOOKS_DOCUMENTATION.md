# UV-Based Claude Code Hooks Documentation

## Overview

This directory contains the uv-managed Python scripts for Claude Code hooks that enforce strict Rust code quality standards. The hooks system has been converted from inline Python commands to a proper Python package managed by uv.

## Architecture

### Directory Structure
```
.claude/hooks/
├── pyproject.toml        # Package configuration with uv settings
├── run-hook.sh          # Shell wrapper for running hooks
├── quality_gate.py      # Main quality gate checker
├── test_hooks.py        # Hook testing utilities
├── hooks/               # Package directory
│   ├── __init__.py
│   ├── pre_tool_use.py     # PreToolUse hook implementation
│   ├── post_tool_use.py    # PostToolUse hook implementation
│   ├── user_prompt_submit.py # UserPromptSubmit hook
│   ├── session_start.py    # SessionStart hook
│   ├── stop.py            # Stop hook (runs quality gate)
│   └── notification.py    # Notification hook
├── .venv/               # uv-managed virtual environment
└── UV_HOOKS_DOCUMENTATION.md # This file
```

### Hook Types and Functions

1. **PreToolUse**: Blocks modifications to protected config files and dangerous commands
2. **PostToolUse**: Auto-formats Rust code, runs clippy, checks compilation, verifies config integrity
3. **UserPromptSubmit**: Detects bypass attempts and injects quality standards context
4. **SessionStart**: Initializes session with quality standards reminder
5. **Stop**: Runs comprehensive quality gate check
6. **Notification**: Logs protection events

## Installation

The hooks are already installed in the virtual environment. To reinstall or update:

```bash
cd .claude/hooks
uv pip install -e .
```

## Usage

### Manual Testing

Test individual hooks:

```bash
# Test user prompt submit
echo '{"prompt": "test prompt"}' | uv run claude-hook-user-prompt-submit

# Test pre-tool-use with file edit
echo '{"tool_name": "Edit", "tool_input": {"file_path": "rustfmt.toml"}}' | uv run claude-hook-pre-tool-use

# Test post-tool-use
echo '{"tool_name": "Edit", "tool_input": {"file_path": "src/main.rs"}}' | uv run claude-hook-post-tool-use

# Test session start
echo '{}' | uv run claude-hook-session-start

# Test quality gate
uv run claude-hook-quality-gate
```

### Integration with Claude Code

To use these hooks, update your `.claude/settings.json` file to use the uv-based commands. See `settings_uv.json` for the complete configuration.

Example hook configuration:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "description": "Block modifications to protected configuration files",
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "cd \"$CLAUDE_PROJECT_DIR/.claude/hooks\" && uv run claude-hook-pre-tool-use",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## Development

### Adding New Hooks

1. Create a new Python file in the `hooks/` directory
2. Implement a handler class with a `handle(data: Dict[str, Any]) -> int` method
3. Add a `main()` function that reads from stdin and calls the handler
4. Add an entry point in `pyproject.toml` under `[project.scripts]`
5. Update the documentation

### Code Quality

The hooks themselves follow Python best practices:
- Type hints for all functions
- Comprehensive error handling
- Clear logging and error messages
- Modular design with handler classes

Run quality checks on the hooks:
```bash
# Format with black
uv run black hooks/ quality_gate.py

# Lint with ruff
uv run ruff check hooks/ quality_gate.py

# Type check with mypy
uv run mypy hooks/ quality_gate.py
```

## Protected Files

The hooks protect the following configuration files from modification:
- `rustfmt.toml` - Rust formatting configuration
- `Cargo.toml` - Cargo configuration with linting rules
- `.cargo/config.toml` - Build configuration with warning flags

## Security Features

1. **Input Validation**: All inputs are validated and sanitized
2. **Path Security**: Absolute path comparisons prevent traversal attacks
3. **Command Filtering**: Dangerous bash commands that could modify configs are blocked
4. **Timeout Protection**: All hooks have timeouts to prevent hanging
5. **Error Isolation**: Errors in hooks don't crash Claude Code

## Troubleshooting

### Common Issues

1. **Hook not found**: Ensure you're in the correct directory and uv is installed
2. **Permission denied**: Make sure `run-hook.sh` is executable
3. **Import errors**: Reinstall with `uv pip install -e .`
4. **Timeout errors**: Increase timeout in settings.json if needed

### Debug Mode

To debug a hook, run it directly with Python:
```bash
cd .claude/hooks
python -m hooks.pre_tool_use < test_input.json
```

### Logs

- Protection events are logged to `.claude/protection.log`
- Hook errors appear in Claude Code's stderr output
- Quality gate results include detailed JSON output

## Maintenance

### Updating Dependencies

```bash
# Update all dependencies
uv pip install --upgrade -e .

# Update specific tools
uv pip install --upgrade black ruff mypy
```

### Version Management

The package version is defined in `pyproject.toml`. Update it when making significant changes.

## Integration with Rust Quality Standards

These hooks work in conjunction with:
- **rustfmt.toml**: Enforces consistent formatting (max width 100, no heuristics)
- **Cargo.toml**: 60+ clippy rules including pedantic and restriction lints
- **.cargo/config.toml**: Build flags treating all warnings as errors

The hooks ensure these configurations cannot be weakened or bypassed, maintaining enterprise-grade code quality standards throughout the development process.