"""Monitor command implementation."""

from __future__ import annotations

import sys
import traceback
from dataclasses import dataclass
from pathlib import Path

import click
from colorama import Fore, Style

from src.cli.commands._monitor_utils import (
    _display_monitor_startup,
    _validate_monitor_directory,
)
from src.cli.constants import (
    DEFAULT_CHECK_INTERVAL,
    DEFAULT_FILE_PATTERN,
    DEFAULT_MONITOR_DIRECTORY,
    DEFAULT_OUTPUT_FILE,
)
from src.cli.handlers.file_handler import FileMonitor
from src.cli.types import CLIContext, MonitorConfig, pass_context
from src.common.exceptions import CCMonitorError


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


@click.command()
@click.option(
    "--directory",
    "-d",
    type=click.Path(file_okay=False),
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
    type=click.Path(),
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
    directory: str = DEFAULT_MONITOR_DIRECTORY,
    interval: int = DEFAULT_CHECK_INTERVAL,
    output: str = DEFAULT_OUTPUT_FILE,
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
        directory=Path(directory),
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
        output=Path(output),
        pattern=monitor_spec.pattern,
        since_last_run=mode_flags.since_last_run,
        process_all=mode_flags.process_all,
    )
    _execute_monitor_command(ctx, config)


def _create_output_directory(output_dir: Path) -> None:
    """Create output directory with specific error handling."""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except FileNotFoundError:
        error_msg = (
            f"Cannot create output directory - parent path not found: "
            f"{output_dir}. Check if the drive/mount exists."
        )
        click.echo(f"{Fore.RED}{error_msg}{Style.RESET_ALL}", err=True)
        sys.exit(1)
    except PermissionError:
        error_msg = (
            f"Permission denied creating output directory: "
            f"{output_dir}. Check directory permissions."
        )
        click.echo(f"{Fore.RED}{error_msg}{Style.RESET_ALL}", err=True)
        sys.exit(1)


def _test_directory_writability(output_dir: Path) -> None:
    """Test if directory is writable."""
    try:
        test_file = output_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
    except FileNotFoundError:
        error_msg = f"Output directory path invalid: {output_dir}"
        click.echo(f"{Fore.RED}{error_msg}{Style.RESET_ALL}", err=True)
        sys.exit(1)
    except PermissionError:
        error_msg = (
            f"Output directory not writable: {output_dir}. "
            f"Check write permissions."
        )
        click.echo(f"{Fore.RED}{error_msg}{Style.RESET_ALL}", err=True)
        sys.exit(1)
    except OSError as e:
        error_msg = f"Output directory error: {output_dir} - {e}"
        click.echo(f"{Fore.RED}{error_msg}{Style.RESET_ALL}", err=True)
        sys.exit(1)


def _validate_output_directory(output_path: Path) -> None:
    """Validate and create output directory."""
    # Check if output path exists as a directory (collision)
    if output_path.exists() and output_path.is_dir():
        error_msg = (
            f"Output path is a directory: {output_path}. "
            f"Please specify a file path, not a directory."
        )
        click.echo(f"{Fore.RED}{error_msg}{Style.RESET_ALL}", err=True)
        sys.exit(1)

    output_dir = output_path.parent
    _create_output_directory(output_dir)
    _test_directory_writability(output_dir)


def _execute_monitor_command(ctx: CLIContext, config: MonitorConfig) -> None:
    """Execute monitor command with configuration."""
    try:
        # Validate directory and display startup information
        monitor_dir = _validate_monitor_directory(config.directory)
        _validate_output_directory(config.output)

        _display_monitor_startup(
            monitor_dir,
            config.output,
            config.pattern,
            process_all=config.process_all,
            since_last_run=config.since_last_run,
        )

        # Execute monitoring with validated directory
        monitor = FileMonitor(config, verbose=ctx.verbose)
        monitor.execute_monitoring(monitor_dir)
    except CCMonitorError as e:
        click.echo(
            f"{Fore.RED}Monitoring failed: {e}{Style.RESET_ALL}",
            err=True,
        )
        if ctx.verbose:
            traceback.print_exc()
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        click.echo(
            f"{Fore.RED}Unexpected error during monitoring: {e}{Style.RESET_ALL}",
            err=True,
        )
        if ctx.verbose:
            traceback.print_exc()
        sys.exit(1)
