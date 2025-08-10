"""Main CLI interface for ccmonitor tool - Live conversation monitoring."""

import json
import logging
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

import click
import colorama
from colorama import Fore, Style

from src.common.exceptions import (
    CCMonitorError,
    ConfigurationError,
    IOOperationError,
)

# Focus on live monitoring only
from .config import ConfigManager
from .constants import (
    DEFAULT_CHECK_INTERVAL,
    DEFAULT_FILE_PATTERN,
    DEFAULT_MONITOR_DIRECTORY,
    DEFAULT_OUTPUT_FILE,
)
from .utils import setup_logging

# Initialize colorama for cross-platform colored output
colorama.init()

# Global configuration manager
config_manager = ConfigManager()

# Version info
__version__ = "0.1.0"


@dataclass
class MonitorConfig:
    """Configuration for monitor command."""

    directory: Path
    interval: int
    output: Path
    pattern: str
    since_last_run: bool = False
    process_all: bool = False


# Configuration classes for monitoring functionality
@dataclass
class MonitorSpec:
    """Consolidated monitoring parameters."""

    directory: Path
    interval: int
    pattern: str


@dataclass
class ModeFlags:
    """Consolidated mode flags."""

    since_last_run: bool = False
    process_all: bool = False


class CLIContext:
    """Context object to pass CLI state between commands."""

    def __init__(self) -> None:
        """Initialize CLI context."""
        self.verbose = False
        self.config_file = None
        self.config: dict[str, Any] = {}


# Pass context between commands
pass_context = click.make_pass_decorator(CLIContext, ensure=True)


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version and exit")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Configuration file path",
)
@click.pass_context
def cli(
    click_ctx: click.Context,
    *,
    version: bool,
    verbose: bool,
    config: str | None,
) -> None:
    """CCMonitor: Claude Code conversation monitoring tool.

    A powerful CLI tool for real-time monitoring of JSONL conversation files
    with live change detection and comprehensive logging.

    Examples:
      ccmonitor monitor /projects --interval 5 --verbose
      ccmonitor monitor --since-last-run
      ccmonitor config show

    """
    if version:
        click.echo(f"ccmonitor version {__version__}")
        sys.exit(0)

    # Setup context
    ctx = click_ctx.ensure_object(CLIContext)
    ctx.verbose = verbose
    ctx.config_file = config

    # Load configuration
    try:
        if config:
            ctx.config = config_manager.load_config(Path(config))
        else:
            ctx.config = config_manager.load_default_config()
    except (ConfigurationError, IOOperationError) as e:
        click.echo(
            f"{Fore.RED}Error loading configuration: {e}{Style.RESET_ALL}",
            err=True,
        )
        sys.exit(1)

    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    setup_logging(log_level)

    # If no command is provided, show help
    if click_ctx.invoked_subcommand is None:
        click.echo(click_ctx.get_help())


@cli.command()
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=DEFAULT_MONITOR_DIRECTORY,
    help="Directory to monitor",
)
@click.option(
    "--interval",
    "-i",
    type=int,
    default=DEFAULT_CHECK_INTERVAL,
    help="Check interval in seconds",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=DEFAULT_OUTPUT_FILE,
    help="Output file for detected changes",
)
@click.option(
    "--pattern",
    "-p",
    default=DEFAULT_FILE_PATTERN,
    help="File pattern to monitor",
)
@click.option(
    "--since-last-run",
    is_flag=True,
    help="Process changes since last run",
)
@click.option(
    "--process-all",
    is_flag=True,
    help="Process all existing files once",
)
@pass_context
def monitor(  # noqa: PLR0913
    ctx: CLIContext,
    directory: Path = Path(DEFAULT_MONITOR_DIRECTORY),
    interval: int = DEFAULT_CHECK_INTERVAL,
    output: Path = Path(DEFAULT_OUTPUT_FILE),
    pattern: str = DEFAULT_FILE_PATTERN,
    since_last_run: bool = False,  # noqa: FBT001, FBT002
    process_all: bool = False,  # noqa: FBT001, FBT002
) -> None:
    """Monitor Claude Code conversations for changes.

    Real-time monitoring of JSONL files with change detection,
    logging, and analysis. Monitors for new files, modifications,
    and deletions without modifying any content.

    Examples:
      ccmonitor monitor --directory /projects --interval 10
      ccmonitor monitor --since-last-run
      ccmonitor monitor --process-all --output changes.txt

    """
    monitor_spec = MonitorSpec(
        directory=directory,
        interval=interval,
        pattern=pattern,
    )
    mode_flags = ModeFlags(
        since_last_run=since_last_run,
        process_all=process_all,
    )
    config = MonitorConfig(
        directory=monitor_spec.directory,
        interval=monitor_spec.interval,
        output=output,
        pattern=monitor_spec.pattern,
        since_last_run=mode_flags.since_last_run,
        process_all=mode_flags.process_all,
    )
    _execute_monitor_command(ctx, config)


class FileMonitor:
    """Handles file monitoring operations with state management."""

    def __init__(
        self,
        config: MonitorConfig,
        *,
        verbose: bool = False,
    ) -> None:
        """Initialize file monitor with configuration."""
        self.config = config
        self.verbose = verbose
        self.state_file = Path(".ccmonitor_state.pkl")
        self.file_timestamps: dict[Path, float] = {}
        self.file_sizes: dict[Path, int] = {}

    def execute_monitoring(self) -> None:
        """Execute monitoring based on configuration."""
        try:
            monitor_dir = _validate_monitor_directory(self.config.directory)
            _display_monitor_startup(
                monitor_dir,
                self.config.output,
                self.config.pattern,
                process_all=self.config.process_all,
                since_last_run=self.config.since_last_run,
            )

            if self.config.since_last_run:
                self._load_previous_state()

            if self.config.process_all or self.config.since_last_run:
                self._process_existing_files(monitor_dir)
            else:
                self._start_realtime_monitoring(monitor_dir)

        except KeyboardInterrupt:
            click.echo(
                f"\n{Fore.YELLOW}Monitor stopped by user{Style.RESET_ALL}",
            )
            self._save_state()

    def _load_previous_state(self) -> None:
        """Load previous monitoring state."""
        self.file_timestamps, self.file_sizes = self._load_state()
        if not self.file_timestamps:
            click.echo(
                f"{Fore.YELLOW}No previous state found. "
                f"Use --process-all for initial run.{Style.RESET_ALL}",
            )

    def _process_existing_files(self, monitor_dir: Path) -> None:
        """Process existing files once."""
        current_files = self._scan_files(monitor_dir)

        for file_path in current_files:
            mtime, size = self._get_file_info(file_path)

            if self.config.process_all:
                self._process_entire_file(file_path)
            elif self._is_new_file(file_path):
                self._process_new_file(file_path)
            elif self._is_modified_file(file_path, mtime, size):
                self._process_modified_file(file_path, size)

            self.file_timestamps[file_path] = mtime
            self.file_sizes[file_path] = size

        self._save_state()
        click.echo(f"{Fore.GREEN}Processing complete{Style.RESET_ALL}")

    def _start_realtime_monitoring(self, monitor_dir: Path) -> None:
        """Start real-time monitoring loop."""
        while True:
            current_files = self._scan_files(monitor_dir)
            self._check_for_changes(current_files)
            self._check_for_deleted_files(current_files)
            self._save_state()
            time.sleep(self.config.interval)

    def _check_for_changes(self, current_files: set[Path]) -> None:
        """Check for file changes."""
        for file_path in current_files:
            mtime, size = self._get_file_info(file_path)

            if self._is_new_file(file_path):
                self._handle_new_file(file_path, mtime, size)
            elif self._is_modified_file(file_path, mtime, size):
                self._handle_modified_file(file_path, mtime, size)

    def _handle_new_file(
        self,
        file_path: Path,
        mtime: float,
        size: int,
    ) -> None:
        """Handle detection of new file."""
        click.echo(f"New file detected: {file_path}")
        self.file_timestamps[file_path] = mtime
        self.file_sizes[file_path] = size

    def _handle_modified_file(
        self,
        file_path: Path,
        mtime: float,
        size: int,
    ) -> None:
        """Handle detection of modified file."""
        click.echo(f"File modified: {file_path}")
        old_size = self.file_sizes.get(file_path, 0)

        if size > old_size:
            changes = self._read_new_content(file_path, old_size)
            if changes:
                self._write_changes(file_path, changes)
                click.echo(f"  Added {len(changes)} new entries")

        self.file_timestamps[file_path] = mtime
        self.file_sizes[file_path] = size

    def _check_for_deleted_files(self, current_files: set[Path]) -> None:
        """Check for deleted files."""
        tracked_files = set(self.file_timestamps.keys())
        deleted_files = tracked_files - current_files
        for deleted_file in deleted_files:
            click.echo(f"File deleted: {deleted_file}")
            del self.file_timestamps[deleted_file]
            if deleted_file in self.file_sizes:
                del self.file_sizes[deleted_file]

    def _process_entire_file(self, file_path: Path) -> None:
        """Process entire file."""
        changes = self._read_new_content(file_path, 0)
        if changes:
            self._write_changes(file_path, changes)
        click.echo(f"Processed: {file_path}")

    def _process_new_file(self, file_path: Path) -> None:
        """Process new file since last run."""
        changes = self._read_new_content(file_path, 0)
        if changes:
            self._write_changes(file_path, changes)
        click.echo(f"New file: {file_path}")

    def _process_modified_file(self, file_path: Path, size: int) -> None:
        """Process modified file."""
        old_size = self.file_sizes.get(file_path, 0)
        if size > old_size:
            changes = self._read_new_content(file_path, old_size)
            if changes:
                self._write_changes(file_path, changes)
        click.echo(f"Modified: {file_path}")

    def _is_new_file(self, file_path: Path) -> bool:
        """Check if file is new."""
        return file_path not in self.file_timestamps

    def _is_modified_file(
        self,
        file_path: Path,
        mtime: float,
        size: int,
    ) -> bool:
        """Check if file is modified."""
        return mtime > self.file_timestamps.get(
            file_path,
            0,
        ) or size != self.file_sizes.get(file_path, 0)

    def _scan_files(self, monitor_dir: Path) -> set[Path]:
        """Scan for files matching pattern."""
        files = set()
        for file_path in monitor_dir.rglob(self.config.pattern):
            if file_path.is_file():
                files.add(file_path)
        return files

    def _get_file_info(self, file_path: Path) -> tuple[float, int]:
        """Get file modification time and size."""
        try:
            stat = file_path.stat()
        except OSError:
            return 0, 0
        else:
            return stat.st_mtime, stat.st_size

    def _read_new_content(
        self,
        file_path: Path,
        old_size: int,
    ) -> list[dict[str, Any]]:
        """Read new content from file."""
        try:
            with file_path.open(encoding="utf-8") as f:
                f.seek(old_size)
                return self._parse_file_lines(f)
        except OSError as e:
            if self.verbose:
                click.echo(f"Warning: Failed to read file content: {e}")
            return []

    def _parse_file_lines(self, file_handle: TextIO) -> list[dict[str, Any]]:
        """Parse lines from file handle."""
        new_lines = []
        for file_line in file_handle:
            stripped_line = file_line.strip()
            if stripped_line:
                parsed_line = self._parse_json_line(stripped_line)
                new_lines.append(parsed_line)
        return new_lines

    def _parse_json_line(self, line: str) -> dict[str, Any]:
        """Parse single JSON line."""
        try:
            parsed_data: dict[str, Any] = json.loads(line)
        except json.JSONDecodeError:
            return {"raw_line": line}
        else:
            return parsed_data

    def _write_changes(
        self,
        file_path: Path,
        changes: list[dict[str, Any]],
    ) -> None:
        """Write changes to output file."""
        if not changes:
            return

        with self.config.output.open("a", encoding="utf-8") as f:
            f.write(f"\n{'=' * 80}\n")
            f.write(f"CHANGES DETECTED: {datetime.now(UTC).isoformat()}\n")
            f.write(f"FILE: {file_path}\n")
            f.write(f"NEW ENTRIES: {len(changes)}\n")
            f.write(f"{'=' * 80}\n")

            for i, change in enumerate(changes, 1):
                f.write(f"\n--- Entry {i} ---\n")
                f.write(
                    f"JSON Data: "
                    f"{json.dumps(change, indent=2, ensure_ascii=False)}\n",
                )

            f.write(f"\n{'=' * 80}\n\n")

    def _save_state(self) -> None:
        """Save monitoring state."""
        state = {
            "file_timestamps": {
                str(k): v for k, v in self.file_timestamps.items()
            },
            "file_sizes": {str(k): v for k, v in self.file_sizes.items()},
            "last_run": datetime.now(UTC).isoformat(),
        }
        try:
            with self.state_file.open("w") as f:
                json.dump(state, f)
        except (OSError, json.JSONDecodeError) as e:
            if self.verbose:
                click.echo(f"Warning: Failed to save state: {e}")

    def _load_state(self) -> tuple[dict[Path, float], dict[Path, int]]:
        """Load monitoring state."""
        try:
            if self.state_file.exists():
                with self.state_file.open() as f:
                    state = json.load(f)
                timestamps = {
                    Path(k): v
                    for k, v in state.get("file_timestamps", {}).items()
                }
                sizes = {
                    Path(k): v for k, v in state.get("file_sizes", {}).items()
                }
                return timestamps, sizes
        except (OSError, json.JSONDecodeError) as e:
            if self.verbose:
                click.echo(f"Warning: Failed to load state: {e}")
        return {}, {}


def _execute_monitor_command(ctx: CLIContext, config: MonitorConfig) -> None:
    """Execute monitor command with configuration."""
    try:
        monitor = FileMonitor(config, verbose=ctx.verbose)
        monitor.execute_monitoring()
    except CCMonitorError as e:
        click.echo(
            f"{Fore.RED}Monitoring failed: {e}{Style.RESET_ALL}",
            err=True,
        )
        if ctx.verbose:
            traceback.print_exc()
        sys.exit(1)


def _validate_monitor_directory(directory: Path) -> Path:
    """Validate and expand monitor directory path."""
    monitor_dir = Path(str(directory)).expanduser()
    if not monitor_dir.exists():
        click.echo(
            f"{Fore.RED}Error: Directory {monitor_dir} does not exist"
            f"{Style.RESET_ALL}",
            err=True,
        )
        sys.exit(1)
    return monitor_dir


def _display_monitor_startup(
    monitor_dir: Path,
    output: Path,
    pattern: str,
    *,
    process_all: bool,
    since_last_run: bool,
) -> None:
    """Display monitor startup information."""
    click.echo(
        f"{Fore.CYAN}Starting CCMonitor - Conversation Monitoring{Style.RESET_ALL}",
    )
    click.echo(f"Monitoring directory: {monitor_dir}")
    click.echo(f"Output file: {output}")
    click.echo(f"File pattern: {pattern}")

    if process_all:
        click.echo("Mode: Processing ALL existing JSONL files")
    elif since_last_run:
        click.echo("Mode: Processing changes since last run")
    else:
        click.echo("Mode: Real-time monitoring (only NEW changes)")
        click.echo("Press Ctrl+C to stop")


@cli.group()
def config() -> None:
    """Manage configuration settings."""


@config.command("show")
def config_show() -> None:
    """Show current configuration."""
    try:
        current_config = config_manager.get_current_config()

        click.echo(f"{Fore.CYAN}Current Configuration:{Style.RESET_ALL}")
        for key, value in current_config.items():
            click.echo(f"  {key}: {value}")

    except (ConfigurationError, IOOperationError) as e:
        click.echo(
            f"{Fore.RED}Error reading configuration: {e}{Style.RESET_ALL}",
            err=True,
        )
        sys.exit(1)


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set configuration value."""
    try:
        config_manager.set_config_value(key, value=value)
        click.echo(
            f"{Fore.GREEN}Configuration updated: {key} = {value}{Style.RESET_ALL}",
        )

    except (ConfigurationError, IOOperationError) as e:
        click.echo(
            f"{Fore.RED}Error updating configuration: {e}{Style.RESET_ALL}",
            err=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    cli()
