"""Main CLI interface for ccmonitor tool - Conversation monitoring and analysis."""

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

from .batch import BatchAnalysisResult, BatchProcessor
from .config import ConfigManager
from .constants import (
    DEFAULT_CHECK_INTERVAL,
    DEFAULT_FILE_PATTERN,
    DEFAULT_MONITOR_DIRECTORY,
    DEFAULT_OUTPUT_FILE,
    DEFAULT_PARALLEL_WORKERS,
)
from .reporting import StatisticsGenerator
from .utils import format_size, setup_logging

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


@dataclass
class AnalyzeConfig:
    """Configuration for analyze command."""

    file: Path | None
    directory: Path | None
    output_format: str
    output: Path | None
    recursive: bool = False
    detailed: bool = False


@dataclass
class BatchConfig:
    """Configuration for batch command."""

    directory: Path
    pattern: str
    output_format: str
    output: Path | None
    recursive: bool = False
    parallel: int = 4


# Parameter consolidation classes for PLR0913 fix
@dataclass
class InputSpec:
    """Consolidated input parameters."""

    file: Path | None
    directory: Path | None
    recursive: bool = False


@dataclass
class OutputSpec:
    """Consolidated output parameters."""

    format: str
    path: Path | None


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


@dataclass
class BatchSpec:
    """Consolidated batch parameters."""

    directory: Path
    pattern: str
    parallel: int = 4


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
@click.option("--config", type=click.Path(exists=True), help="Configuration file path")
@click.pass_context
def cli(
    click_ctx: click.Context,
    *,
    version: bool,
    verbose: bool,
    config: str | None,
) -> None:
    """CCMonitor: Claude Code conversation monitoring and analysis tool.

    A powerful CLI tool for monitoring and analyzing JSONL conversation files
    with real-time monitoring, batch analysis, and comprehensive reporting.

    Examples:
      ccmonitor analyze session.jsonl --format json --output report.json
      ccmonitor monitor /projects --interval 5 --verbose
      ccmonitor batch /data --pattern "*.jsonl" --recursive

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
            f"{Fore.RED}Error loading configuration: {e}{Style.RESET_ALL}", err=True,
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
    "--file",
    "-f",
    type=click.Path(exists=True, path_type=Path),
    help="JSONL file to analyze",
)
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Directory to analyze",
)
@click.option("--recursive", "-r", is_flag=True, help="Analyze directories recursively")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "csv", "html"]),
    default="table",
    help="Output format",
)
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), help="Output file path",
)
@click.option("--detailed", is_flag=True, help="Include detailed analysis")
@pass_context
def analyze(  # noqa: PLR0913
    ctx: CLIContext,
    file: Path | None = None,
    directory: Path | None = None,
    recursive: bool = False,  # noqa: FBT001, FBT002
    output_format: str = "table",
    output: Path | None = None,
    detailed: bool = False,  # noqa: FBT001, FBT002
) -> None:
    """Analyze JSONL conversation files.

    Provides detailed analysis of conversation patterns, message types,
    structure, and statistics without modifying any files.

    Examples:
      ccmonitor analyze session.jsonl --format json --output report.json
      ccmonitor analyze --directory /projects --recursive --detailed
      ccmonitor analyze data.jsonl --format html --output report.html

    """
    input_spec = InputSpec(file=file, directory=directory, recursive=recursive)
    output_spec = OutputSpec(format=output_format, path=output)
    config = AnalyzeConfig(
        file=input_spec.file,
        directory=input_spec.directory,
        output_format=output_spec.format,
        output=output_spec.path,
        recursive=input_spec.recursive,
        detailed=detailed,
    )
    _execute_analyze_command(ctx, config)


def _execute_analyze_command(ctx: CLIContext, config: AnalyzeConfig) -> None:
    """Execute analyze command with configuration."""
    try:
        _validate_analyze_inputs(config.file, config.directory)
        stats_generator = _setup_statistics_generator(verbose=ctx.verbose)
        result = _perform_analysis(
            stats_generator,
            config.file,
            config.directory,
            recursive=config.recursive,
            detailed=config.detailed,
        )
        _output_analysis_results(
            stats_generator, result, config.output, config.output_format,
        )

    except ImportError:
        _handle_import_error()
    except CCMonitorError as e:
        _handle_analysis_error(e, verbose=ctx.verbose)


def _validate_analyze_inputs(file: Path | None, directory: Path | None) -> None:
    """Validate analyze command inputs."""
    if not file and not directory:
        error_msg = "Error: Must specify either --file or --directory"
        click.echo(f"{Fore.RED}{error_msg}{Style.RESET_ALL}", err=True)
        sys.exit(1)

def _setup_statistics_generator(*, verbose: bool) -> StatisticsGenerator:
    """Set up and return statistics generator."""
    return StatisticsGenerator(verbose=verbose)

def _perform_analysis(
    stats_generator: StatisticsGenerator,
    file: Path | None,
    directory: Path | None,
    *,
    recursive: bool,
    detailed: bool,
) -> dict[str, Any]:
    """Perform the actual analysis."""
    if file:
        return stats_generator.analyze_file(file, include_trends=detailed)
    if directory:
        return stats_generator.analyze_directory(
            directory, recursive=recursive, include_patterns=detailed,
        )
    msg = "No file or directory specified"
    raise ValueError(msg)

def _output_analysis_results(
    stats_generator: StatisticsGenerator,
    result: dict[str, Any],
    output: Path | None,
    output_format: str,
) -> None:
    """Output analysis results."""
    if output:
        stats_generator.export_report(result, output, output_format)
        click.echo(f"{Fore.GREEN}Report exported to {output}{Style.RESET_ALL}")
    else:
        stats_generator.display_report(result, output_format)

def _handle_import_error() -> None:
    """Handle import errors."""
    click.echo(
        f"{Fore.RED}Error: Statistics module not available{Style.RESET_ALL}",
        err=True,
    )
    sys.exit(1)

def _handle_analysis_error(error: Exception, *, verbose: bool) -> None:
    """Handle analysis errors."""
    click.echo(f"{Fore.RED}Analysis failed: {error}{Style.RESET_ALL}", err=True)
    if verbose:
        traceback.print_exc()
    sys.exit(1)


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
    "--pattern", "-p", default=DEFAULT_FILE_PATTERN, help="File pattern to monitor",
)
@click.option("--since-last-run", is_flag=True, help="Process changes since last run")
@click.option("--process-all", is_flag=True, help="Process all existing files once")
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
    monitor_spec = MonitorSpec(directory=directory, interval=interval, pattern=pattern)
    mode_flags = ModeFlags(since_last_run=since_last_run, process_all=process_all)
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

    def __init__(self, config: MonitorConfig, *, verbose: bool = False) -> None:
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
            click.echo(f"\n{Fore.YELLOW}Monitor stopped by user{Style.RESET_ALL}")
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

    def _handle_new_file(self, file_path: Path, mtime: float, size: int) -> None:
        """Handle detection of new file."""
        click.echo(f"New file detected: {file_path}")
        self.file_timestamps[file_path] = mtime
        self.file_sizes[file_path] = size

    def _handle_modified_file(self, file_path: Path, mtime: float, size: int) -> None:
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

    def _is_modified_file(self, file_path: Path, mtime: float, size: int) -> bool:
        """Check if file is modified."""
        return (
            mtime > self.file_timestamps.get(file_path, 0)
            or size != self.file_sizes.get(file_path, 0)
        )

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

    def _read_new_content(self, file_path: Path, old_size: int) -> list[dict[str, Any]]:
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

    def _write_changes(self, file_path: Path, changes: list[dict[str, Any]]) -> None:
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
            "file_timestamps": {str(k): v for k, v in self.file_timestamps.items()},
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
                    Path(k): v for k, v in state.get("file_timestamps", {}).items()
                }
                sizes = {Path(k): v for k, v in state.get("file_sizes", {}).items()}
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
        click.echo(f"{Fore.RED}Monitoring failed: {e}{Style.RESET_ALL}", err=True)
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


@cli.command()
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Directory to process",
)
@click.option(
    "--pattern",
    "-p",
    default=DEFAULT_FILE_PATTERN,
    help="File pattern to match (default: *.jsonl)",
)
@click.option("--recursive", "-r", is_flag=True, help="Process directories recursively")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), help="Output file for results",
)
@click.option(
    "--parallel",
    type=int,
    default=DEFAULT_PARALLEL_WORKERS,
    help="Number of parallel workers",
)
@pass_context
def batch(  # noqa: PLR0913
    ctx: CLIContext,
    directory: Path | None = None,
    pattern: str = DEFAULT_FILE_PATTERN,
    recursive: bool = False,  # noqa: FBT001, FBT002
    output_format: str = "table",
    output: Path | None = None,
    parallel: int = DEFAULT_PARALLEL_WORKERS,
) -> None:
    """Process multiple JSONL files in batch mode for analysis.

    Efficiently analyzes entire directories of JSONL files with parallel
    processing and comprehensive reporting.

    Examples:
      ccmonitor batch /projects --pattern "*.jsonl" --recursive
      ccmonitor batch /data --format json --output batch_report.json
      ccmonitor batch /work --parallel 8 --format csv

    """
    if directory is None:
        click.echo(
            f"{Fore.RED}Error: --directory is required{Style.RESET_ALL}",
            err=True,
        )
        sys.exit(1)

    batch_spec = BatchSpec(directory=directory, pattern=pattern, parallel=parallel)
    output_spec = OutputSpec(format=output_format, path=output)
    config = BatchConfig(
        directory=batch_spec.directory,
        pattern=batch_spec.pattern,
        output_format=output_spec.format,
        output=output_spec.path,
        recursive=recursive,
        parallel=batch_spec.parallel,
    )
    _execute_batch_command(ctx, config)


def _execute_batch_command(ctx: CLIContext, config: BatchConfig) -> None:
    """Execute batch command with configuration."""
    try:
        _display_batch_configuration(config, verbose=ctx.verbose)
        batch_processor = _setup_batch_processor(
            config.directory,
            config.pattern,
            recursive=config.recursive,
            parallel=config.parallel,
            verbose=ctx.verbose,
        )
        result = batch_processor.analyze_directory()
        _output_batch_results(
            batch_processor, result, config.output, config.output_format,
        )

    except ImportError:
        _handle_batch_import_error()
    except CCMonitorError as e:
        _handle_batch_error(e, verbose=ctx.verbose)


def _display_batch_configuration(config: BatchConfig, *, verbose: bool) -> None:
    """Display batch configuration if verbose mode is enabled."""
    if verbose:
        click.echo(f"{Fore.CYAN}Batch Analysis Configuration:{Style.RESET_ALL}")
        click.echo(f"  Directory: {config.directory}")
        click.echo(f"  Pattern: {config.pattern}")
        click.echo(f"  Recursive: {config.recursive}")
        click.echo(f"  Format: {config.output_format}")
        click.echo(f"  Parallel workers: {config.parallel}")
        click.echo()

def _setup_batch_processor(
    directory: Path,
    pattern: str,
    *,
    recursive: bool,
    parallel: int,
    verbose: bool,
) -> BatchProcessor:
    """Set up and return batch processor."""
    return BatchProcessor(
        directory=directory,
        pattern=pattern,
        recursive=recursive,
        parallel_workers=parallel,
        verbose=verbose,
    )

def _output_batch_results(
    batch_processor: BatchProcessor,
    result: BatchAnalysisResult,
    output: Path | None,
    output_format: str,
) -> None:
    """Output batch processing results."""
    if output:
        batch_processor.export_results(result, output, output_format)
        click.echo(f"{Fore.GREEN}Results exported to {output}{Style.RESET_ALL}")
    else:
        batch_processor.display_results(result, output_format)

def _handle_batch_import_error() -> None:
    """Handle batch import errors."""
    click.echo(
        f"{Fore.RED}Error: Batch processing module not available{Style.RESET_ALL}",
        err=True,
    )
    sys.exit(1)

def _handle_batch_error(error: Exception, *, verbose: bool) -> None:
    """Handle batch processing errors."""
    click.echo(f"{Fore.RED}Batch processing failed: {error}{Style.RESET_ALL}", err=True)
    if verbose:
        traceback.print_exc()
    sys.exit(1)


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
            f"{Fore.RED}Error reading configuration: {e}{Style.RESET_ALL}", err=True,
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
            f"{Fore.RED}Error updating configuration: {e}{Style.RESET_ALL}", err=True,
        )
        sys.exit(1)


# Helper functions for display


def _display_file_stats(file_path: Path, stats: dict[str, Any]) -> None:
    """Display file analysis statistics."""
    click.echo(f"\n{Fore.CYAN}Analysis Results for {file_path}:{Style.RESET_ALL}")
    click.echo(f"  Total messages: {stats.get('total_messages', 0):,}")
    click.echo(f"  Message types: {stats.get('message_types', {})}")
    click.echo(f"  Conversation depth: {stats.get('conversation_depth', 0)}")
    click.echo(f"  File size: {format_size(stats.get('file_size', 0))}")

    if stats.get("patterns"):
        click.echo(f"  Patterns found: {len(stats['patterns'])}")


if __name__ == "__main__":
    cli()
