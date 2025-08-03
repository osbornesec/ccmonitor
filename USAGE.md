# Claude Code Monitor - Usage Guide

Claude Code Monitor is a Python utility that monitors your Claude Code project files for changes and extracts session data in a readable format.

## Quick Start

```bash
# Install dependencies
uv sync

# Start real-time monitoring (recommended for first-time users)
uv run python main.py

# Process all existing files once and exit
uv run python main.py --process-all

# Check only changes since last run
uv run python main.py --since-last-run
```

## Operating Modes

### 1. Real-Time Monitoring (Default)
```bash
uv run python main.py
```
- Monitors `~/.claude/projects/` continuously
- Only captures NEW changes after the monitor starts
- Updates every 5 seconds (configurable)
- Press Ctrl+C to stop
- Best for: Ongoing development sessions

### 2. Process All Files
```bash
uv run python main.py --process-all
```
- Processes ALL existing JSONL files once
- Extracts complete content from all files
- Exits after processing
- Best for: Initial setup or full session analysis

### 3. Since Last Run
```bash
uv run python main.py --since-last-run
```
- Only processes changes since the program last ran
- Uses saved state from previous runs
- Exits after processing
- Best for: Periodic checks or scheduled runs

## Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--interval` | `-i` | Check interval in seconds | 5 |
| `--process-all` | `-a` | Process all files and exit | False |
| `--since-last-run` | `-s` | Process changes since last run | False |
| `--output` | `-o` | Output file path | `claude_session_changes.txt` |
| `--verbose` | `-v` | Enable debug logging | False |

## Examples

### Basic Usage
```bash
# Monitor with default settings
uv run python main.py

# Monitor with 2-second intervals
uv run python main.py --interval 2

# Custom output file
uv run python main.py --output my_sessions.txt
```

### Advanced Usage
```bash
# Verbose logging for troubleshooting
uv run python main.py --verbose

# One-time analysis of all sessions
uv run python main.py --process-all --output full_analysis.txt

# Daily check for changes (good for cron jobs)
uv run python main.py --since-last-run --output daily_changes.txt
```

### Automation Examples

#### Cron Job (Daily Summary)
```bash
# Add to crontab for daily session summaries
0 9 * * * cd /path/to/ccmonitor && uv run python main.py --since-last-run --output daily_$(date +\%Y\%m\%d).txt
```

#### Development Workflow
```bash
# Start monitoring before a coding session
uv run python main.py --output today_session.txt &

# Work with Claude Code...

# Stop monitoring and review changes
kill %1
cat today_session.txt
```

## Output Format

The monitor creates a text file with the following format:

```
================================================================================
CHANGES DETECTED: 2024-01-15T14:30:45
FILE: /home/user/.claude/projects/my-project/conversation_123.jsonl
NEW ENTRIES: 3
================================================================================

--- Entry 1 ---
JSON Data: {
  "role": "user",
  "content": "Help me debug this function",
  "timestamp": "2024-01-15T14:30:42.123Z"
}

--- Entry 2 ---
JSON Data: {
  "role": "assistant", 
  "content": "I'll help you debug that function...",
  "timestamp": "2024-01-15T14:30:44.456Z"
}

--- Entry 3 ---
JSON Data: {
  "tool_call": "read_file",
  "parameters": {"file_path": "/path/to/file.py"},
  "timestamp": "2024-01-15T14:30:45.789Z"
}

================================================================================
```

## What Gets Monitored

### File Locations
- Primary: `~/.claude/projects/`
- All subdirectories containing JSONL files
- Automatically discovers new project directories

### File Types
- `.jsonl` files (JSON Lines format)
- Contains Claude Code conversation history
- Tool usage logs and results
- Session metadata

### Change Detection
- **New files**: Automatically detected and tracked
- **File modifications**: Only new content is extracted
- **File deletions**: Logged and removed from tracking
- **Size changes**: Handles both growth and shrinkage

## Troubleshooting

### Common Issues

#### No Changes Detected
```bash
# Check if Claude Code is actually writing files
ls -la ~/.claude/projects/

# Enable verbose logging to see what's happening
uv run python main.py --verbose
```

#### Permission Errors
```bash
# Ensure you have read access to Claude Code directories
ls -la ~/.claude/projects/

# Check file permissions
chmod +r ~/.claude/projects/*/*.jsonl
```

#### Large Output Files
```bash
# Rotate output files periodically
mv claude_session_changes.txt archive_$(date +%Y%m%d).txt
touch claude_session_changes.txt
```

#### State File Issues
```bash
# Reset state if having issues with --since-last-run
rm .ccmonitor_state.pkl
uv run python main.py --process-all  # Rebuild state
```

### Debug Mode

```bash
# Enable verbose logging for detailed troubleshooting
uv run python main.py --verbose

# This will show:
# - Files being scanned
# - Change detection details
# - JSON parsing issues
# - File system operations
```

### Log Analysis

The verbose output includes:
- File discovery and tracking
- Modification time changes
- File size changes
- JSON parsing results
- Error messages and warnings

## Tips and Best Practices

### Performance Optimization
- Use longer intervals (`--interval 10`) for less active monitoring
- Use `--since-last-run` for periodic checks instead of continuous monitoring
- Rotate output files to prevent them from becoming too large

### Workflow Integration
- Start monitoring before beginning coding sessions
- Use different output files for different projects
- Combine with text processing tools for analysis

### Analysis Workflows
```bash
# Extract only user messages
grep -A 10 '"role": "user"' claude_session_changes.txt

# Find tool usage patterns
grep -B 2 -A 5 '"tool_call"' claude_session_changes.txt

# Count session activity
grep "CHANGES DETECTED" claude_session_changes.txt | wc -l
```

### Automation Ideas
- Integrate with Git hooks to capture session data with commits
- Use with `jq` for advanced JSON analysis
- Create dashboards by parsing the output files
- Set up alerts for unusual activity patterns

## Safety Notes

- The monitor only reads files, never modifies them
- State files are stored locally (`.ccmonitor_state.pkl`)
- No network access required
- Respects file permissions and handles errors gracefully
- Safe to run alongside Claude Code sessions

## Getting Help

If you encounter issues:

1. Try running with `--verbose` flag first
2. Check the Prerequisites section in README.md
3. Verify Claude Code is properly installed and configured
4. Check file permissions in `~/.claude/projects/`

For questions about the output format or analysis techniques, refer to the Claude Code documentation.