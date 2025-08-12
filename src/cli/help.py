"""Comprehensive help text for CCMonitor CLI."""

import click

HELP_TEXT = """
CCMonitor - Claude Conversation Monitor

USAGE:
    ccmonitor [OPTIONS] [COMMAND]

DESCRIPTION:
    CCMonitor is a powerful tool for monitoring Claude conversation files in real-time.
    It provides both CLI and TUI interfaces for different use cases.

MODES:
    CLI Mode (Current):
        ccmonitor monitor [OPTIONS]      # Monitor conversations in CLI mode
        ccmonitor parse FILE             # Parse conversation file
        ccmonitor stats                  # Show statistics
        ccmonitor config show           # Show configuration

    TUI Mode (Future):
        ccmonitor tui                   # Launch TUI interface (placeholder)

OPTIONS:
    --version          Show version and exit
    --verbose, -v      Enable verbose output
    --config PATH      Configuration file path
    --help             Show this help message

COMMANDS:
    monitor      Monitor conversations for changes
    tui          Launch TUI interface (placeholder)
    config       Manage configuration settings

MONITORING OPTIONS:
    --directory, -d DIR    Directory to monitor (default: current directory)
    --interval, -i SECS    Check interval in seconds (default: 5)
    --output, -o FILE      Output file for changes
    --pattern, -p PATTERN  File pattern to monitor (default: *.jsonl)
    --since-last-run       Process changes since last run
    --process-all          Process all existing files once

EXAMPLES:
    # Basic monitoring
    ccmonitor monitor

    # Monitor specific directory with custom interval
    ccmonitor monitor --directory /projects --interval 10

    # Process changes since last run
    ccmonitor monitor --since-last-run

    # Process all existing files
    ccmonitor monitor --process-all --output changes.txt

    # Show configuration
    ccmonitor config show

    # Set configuration value
    ccmonitor config set colorize_output true

CONFIGURATION:
    Config file: ~/.config/ccmonitor/config.yaml

    The configuration file controls monitoring behavior, output formats,
    and other preferences. See documentation for configuration options.

ENVIRONMENT VARIABLES:
    CCMONITOR_NO_TUI      Disable TUI mode (future)
    CCMONITOR_CONFIG      Configuration file path
    CCMONITOR_LEVEL       Default analysis level
    CCMONITOR_VERBOSE     Enable verbose output
    CCMONITOR_PATTERN     Default file pattern

FILES:
    ~/.config/ccmonitor/config.yaml    Configuration file
    .ccmonitor_state.pkl              Monitoring state file

EXIT CODES:
    0    Success
    1    General error
    2    Configuration error

For more information and documentation:
    https://github.com/yourusername/ccmonitor
"""


def show_help() -> None:
    """Display comprehensive help."""
    click.echo(HELP_TEXT)


def show_monitoring_help() -> None:
    """Show monitoring-specific help."""
    help_text = """
CCMonitor - Monitoring Command Help

USAGE:
    ccmonitor monitor [OPTIONS]

DESCRIPTION:
    Monitor Claude conversation files for changes in real-time.
    Detects new files, modifications, and deletions without modifying content.

MONITORING MODES:
    Real-time:     Continuously monitor for new changes (default)
    Since last:    Process changes since last monitoring session
    Process all:   Process all existing files once and exit

OPTIONS:
    --directory, -d DIR     Directory to monitor
                           (default: current directory)

    --interval, -i SECS     Check interval in seconds
                           (default: 5)

    --output, -o FILE       Output file for detected changes
                           (default: ccmonitor_changes.txt)

    --pattern, -p PATTERN   File pattern to monitor
                           (default: *.jsonl)

    --since-last-run        Process changes since last monitoring session
                           Uses saved state from .ccmonitor_state.pkl

    --process-all          Process all existing files once
                          Useful for initial analysis

    --verbose, -v          Enable verbose output
                          Shows detailed monitoring information

EXAMPLES:
    # Monitor current directory with default settings
    ccmonitor monitor

    # Monitor specific directory
    ccmonitor monitor --directory /path/to/conversations

    # Custom check interval and output
    ccmonitor monitor --interval 10 --output my_changes.txt

    # Process changes since last run (incremental)
    ccmonitor monitor --since-last-run

    # Process all existing files once
    ccmonitor monitor --process-all

    # Verbose monitoring with custom pattern
    ccmonitor monitor --verbose --pattern "conversation_*.jsonl"

OUTPUT FORMAT:
    The output file contains timestamped entries for each detected change:

    ================================================================================
    CHANGES DETECTED: 2023-12-07T10:30:45.123456+00:00
    FILE: /path/to/conversation.jsonl
    NEW ENTRIES: 3
    ================================================================================

    --- Entry 1 ---
    JSON Data: {
        "timestamp": "2023-12-07T10:30:42Z",
        "content": "conversation data...",
        ...
    }

    --- Entry 2 ---
    JSON Data: {...}

MONITORING STATE:
    The monitoring system maintains state in .ccmonitor_state.pkl to enable
    incremental processing with --since-last-run.

    State includes:
    - File modification timestamps
    - File sizes
    - Last monitoring session time

TIPS:
    - Use --since-last-run for efficient incremental monitoring
    - Use --process-all for initial setup or comprehensive analysis
    - Monitor output file size in long-running sessions
    - Press Ctrl+C to stop monitoring gracefully

TROUBLESHOOTING:
    - Ensure directory exists and is readable
    - Check file permissions for output directory
    - Verify JSONL files are valid JSON format
    - Use --verbose for detailed diagnostic information
"""
    click.echo(help_text)


def show_config_help() -> None:
    """Show configuration help."""
    help_text = """
CCMonitor - Configuration Help

USAGE:
    ccmonitor config [COMMAND]

COMMANDS:
    show              Show current configuration
    set KEY VALUE     Set configuration value

CONFIGURATION FILE:
    Location: ~/.config/ccmonitor/config.yaml
    Format: YAML

    The configuration file is automatically created with defaults if it doesn't exist.

CONFIGURATION SECTIONS:

general:
    default_mode: tui|cli           # Default interface mode (future)
    verbose: true|false             # Enable verbose output
    log_level: DEBUG|INFO|WARNING   # Logging level

cli:
    output_format: json|yaml|csv    # Default output format
    color_output: true|false        # Enable colored output
    pager: less|more|none          # Pager for long output
    default_level: light|medium|aggressive  # Analysis level
    default_backup: true|false      # Create backups
    default_progress: true|false    # Show progress bars
    default_parallel_workers: 4     # Parallel processing workers
    default_pattern: "*.jsonl"     # Default file pattern
    default_recursive: true|false   # Recursive directory search
    colorize_output: true|false     # Colorize terminal output
    show_warnings: true|false       # Show warning messages
    chunk_size: 1000               # Processing chunk size
    memory_limit_mb: 512           # Memory limit in MB
    require_confirmation: true|false # Require confirmation for destructive ops
    max_file_size_mb: 100          # Maximum file size to process
    backup_retention_days: 30      # Backup retention period

tui:
    theme: dark|light|monokai|solarized  # TUI theme (future)
    start_maximized: true|false     # Start in maximized mode
    show_help_on_start: true|false  # Show help on startup
    animation_level: full|reduced|none  # Animation level
    autosave_state: true|false      # Auto-save application state

monitoring:
    watch_paths: []                # Paths to monitor
    poll_interval: 1.0            # Polling interval in seconds
    max_history: 1000             # Maximum history entries

database:
    path: "~/.config/ccmonitor/conversations.db"  # Database file path
    auto_vacuum: true|false        # Enable database auto-vacuum

EXAMPLES:
    # Show current configuration
    ccmonitor config show

    # Set verbose output
    ccmonitor config set default_verbose true

    # Set output format
    ccmonitor config set default_output_format yaml

    # Set monitoring interval
    ccmonitor config set poll_interval 2.0

    # Set color output
    ccmonitor config set colorize_output false

ENVIRONMENT VARIABLES:
    Configuration can be overridden with environment variables:

    CCMONITOR_LEVEL           -> default_level
    CCMONITOR_BACKUP          -> default_backup
    CCMONITOR_VERBOSE         -> default_verbose
    CCMONITOR_PARALLEL        -> default_parallel_workers
    CCMONITOR_PATTERN         -> default_pattern
    CCMONITOR_RECURSIVE       -> default_recursive
    CCMONITOR_FORMAT          -> default_output_format
    CCMONITOR_COLORIZE        -> colorize_output

VALIDATION:
    Configuration values are validated when loaded. Invalid values will be
    reported as warnings and defaults will be used.

PROFILES:
    Future versions will support configuration profiles for different
    monitoring scenarios.
"""
    click.echo(help_text)
