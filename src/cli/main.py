"""
Main CLI interface for ccmonitor tool - Conversation monitoring and analysis
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import click
import colorama
from colorama import Fore, Style

from ..jsonl_analysis.analyzer import JSONLAnalyzer
from .config import ConfigManager
from .utils import format_duration, format_size, setup_logging, validate_file_access

# Initialize colorama for cross-platform colored output
colorama.init()

# Global configuration manager
config_manager = ConfigManager()

# Version info
__version__ = "0.1.0"


class CLIContext:
    """Context object to pass CLI state between commands"""

    def __init__(self):
        self.verbose = False
        self.config_file = None
        self.config = {}


# Pass context between commands
pass_context = click.make_pass_decorator(CLIContext, ensure=True)


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version and exit")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--config", type=click.Path(exists=True), help="Configuration file path")
@click.pass_context
def cli(click_ctx, version: bool, verbose: bool, config: str | None):
    """
    CCMonitor: Claude Code conversation monitoring and analysis tool

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
    except Exception as e:
        click.echo(f"{Fore.RED}Error loading configuration: {e}{Style.RESET_ALL}", err=True)
        sys.exit(1)

    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    setup_logging(log_level)

    # If no command is provided, show help
    if click_ctx.invoked_subcommand is None:
        click.echo(click_ctx.get_help())


@cli.command()
@click.option(
    "--file", "-f", type=click.Path(exists=True, path_type=Path), help="JSONL file to analyze",
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
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file path")
@click.option("--detailed", is_flag=True, help="Include detailed analysis")
@pass_context
def analyze(
    ctx: CLIContext,
    file: Path | None,
    directory: Path | None,
    recursive: bool,
    output_format: str,
    output: Path | None,
    detailed: bool,
):
    """
    Analyze JSONL conversation files

    Provides detailed analysis of conversation patterns, message types,
    structure, and statistics without modifying any files.

    Examples:
      ccmonitor analyze session.jsonl --format json --output report.json
      ccmonitor analyze --directory /projects --recursive --detailed
      ccmonitor analyze data.jsonl --format html --output report.html
    """
    try:
        from .reporting import StatisticsGenerator

        if not file and not directory:
            click.echo(
                f"{Fore.RED}Error: Must specify either --file or --directory{Style.RESET_ALL}",
                err=True,
            )
            sys.exit(1)

        # Initialize statistics generator
        stats_generator = StatisticsGenerator(verbose=ctx.verbose)

        # Generate analysis
        if file:
            result = stats_generator.analyze_file(file, detailed=detailed)
        else:
            result = stats_generator.analyze_directory(
                directory, recursive=recursive, detailed=detailed,
            )

        # Output results
        if output:
            stats_generator.export_report(result, output, output_format)
            click.echo(f"{Fore.GREEN}Report exported to {output}{Style.RESET_ALL}")
        else:
            stats_generator.display_report(result, output_format)

    except ImportError:
        click.echo(f"{Fore.RED}Error: Statistics module not available{Style.RESET_ALL}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"{Fore.RED}Analysis failed: {e}{Style.RESET_ALL}", err=True)
        if ctx.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default="~/.claude/projects",
    help="Directory to monitor",
)
@click.option("--interval", "-i", type=int, default=5, help="Check interval in seconds")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="conversation_changes.txt",
    help="Output file for detected changes",
)
@click.option("--pattern", "-p", default="*.jsonl", help="File pattern to monitor")
@click.option("--since-last-run", is_flag=True, help="Process changes since last run")
@click.option("--process-all", is_flag=True, help="Process all existing files once")
@pass_context
def monitor(
    ctx: CLIContext,
    directory: Path,
    interval: int,
    output: Path,
    pattern: str,
    since_last_run: bool,
    process_all: bool,
):
    """
    Monitor Claude Code conversations for changes

    Real-time monitoring of JSONL files with change detection,
    logging, and analysis. Monitors for new files, modifications,
    and deletions without modifying any content.

    Examples:
      ccmonitor monitor --directory /projects --interval 10
      ccmonitor monitor --since-last-run
      ccmonitor monitor --process-all --output changes.txt
    """
    try:
        # Import the basic monitoring functionality from main.py
        import os
        import pickle
        from datetime import datetime

        from ..jsonl_analysis.analyzer import JSONLAnalyzer

        # Expand the directory path
        monitor_dir = Path(os.path.expanduser(str(directory)))

        if not monitor_dir.exists():
            click.echo(
                f"{Fore.RED}Error: Directory {monitor_dir} does not exist{Style.RESET_ALL}",
                err=True,
            )
            sys.exit(1)

        click.echo(f"{Fore.CYAN}Starting CCMonitor - Conversation Monitoring{Style.RESET_ALL}")
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

        # Initialize monitoring system
        state_file = Path(".ccmonitor_state.pkl")
        file_timestamps = {}
        file_sizes = {}

        def save_state():
            state = {
                "file_timestamps": file_timestamps,
                "file_sizes": file_sizes,
                "last_run": datetime.now().isoformat(),
            }
            try:
                with open(state_file, "wb") as f:
                    pickle.dump(state, f)
            except Exception as e:
                if ctx.verbose:
                    click.echo(f"Warning: Failed to save state: {e}")

        def load_state():
            try:
                if state_file.exists():
                    with open(state_file, "rb") as f:
                        state = pickle.load(f)
                    return state.get("file_timestamps", {}), state.get("file_sizes", {})
            except Exception as e:
                if ctx.verbose:
                    click.echo(f"Warning: Failed to load state: {e}")
            return {}, {}

        def scan_files():
            files = set()
            for file_path in monitor_dir.rglob(pattern):
                if file_path.is_file():
                    files.add(str(file_path))
            return files

        def get_file_info(file_path):
            try:
                stat = os.stat(file_path)
                return stat.st_mtime, stat.st_size
            except OSError:
                return 0, 0

        def write_changes(file_path, changes):
            if not changes:
                return

            with open(output, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"CHANGES DETECTED: {datetime.now().isoformat()}\n")
                f.write(f"FILE: {file_path}\n")
                f.write(f"NEW ENTRIES: {len(changes)}\n")
                f.write(f"{'='*80}\n")

                for i, change in enumerate(changes, 1):
                    f.write(f"\n--- Entry {i} ---\n")
                    f.write(f"JSON Data: {json.dumps(change, indent=2, ensure_ascii=False)}\n")

                f.write(f"\n{'='*80}\n\n")

        def read_new_content(file_path, old_size):
            try:
                with open(file_path, encoding="utf-8") as f:
                    f.seek(old_size)
                    new_lines = []
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                new_lines.append(data)
                            except json.JSONDecodeError:
                                new_lines.append({"raw_line": line})
                    return new_lines
            except Exception:
                return []

        # Load previous state if needed
        if since_last_run:
            file_timestamps, file_sizes = load_state()
            if not file_timestamps:
                click.echo(
                    f"{Fore.YELLOW}No previous state found. Use --process-all for initial run.{Style.RESET_ALL}",
                )
                return

        # Main monitoring loop
        try:
            if process_all or since_last_run:
                # One-time processing
                current_files = scan_files()

                for file_path in current_files:
                    mtime, size = get_file_info(file_path)

                    if process_all:
                        # Read entire file
                        changes = read_new_content(file_path, 0)
                        if changes:
                            write_changes(file_path, changes)
                        click.echo(f"Processed: {file_path}")
                    elif file_path not in file_timestamps:
                        # New file since last run
                        changes = read_new_content(file_path, 0)
                        if changes:
                            write_changes(file_path, changes)
                        click.echo(f"New file: {file_path}")
                    elif mtime > file_timestamps.get(file_path, 0) or size != file_sizes.get(
                        file_path, 0,
                    ):
                        # Modified file
                        old_size = file_sizes.get(file_path, 0)
                        if size > old_size:
                            changes = read_new_content(file_path, old_size)
                            if changes:
                                write_changes(file_path, changes)
                        click.echo(f"Modified: {file_path}")

                    file_timestamps[file_path] = mtime
                    file_sizes[file_path] = size

                save_state()
                click.echo(f"{Fore.GREEN}Processing complete{Style.RESET_ALL}")

            else:
                # Real-time monitoring
                while True:
                    current_files = scan_files()

                    for file_path in current_files:
                        mtime, size = get_file_info(file_path)

                        if file_path not in file_timestamps:
                            # New file
                            click.echo(f"New file detected: {file_path}")
                            file_timestamps[file_path] = mtime
                            file_sizes[file_path] = size
                        elif mtime > file_timestamps[file_path] or size != file_sizes.get(
                            file_path, 0,
                        ):
                            # Modified file
                            old_size = file_sizes.get(file_path, 0)
                            click.echo(f"File modified: {file_path}")

                            if size > old_size:
                                changes = read_new_content(file_path, old_size)
                                if changes:
                                    write_changes(file_path, changes)
                                    click.echo(f"  Added {len(changes)} new entries")

                            file_timestamps[file_path] = mtime
                            file_sizes[file_path] = size

                    # Check for deleted files
                    tracked_files = set(file_timestamps.keys())
                    deleted_files = tracked_files - current_files
                    for deleted_file in deleted_files:
                        click.echo(f"File deleted: {deleted_file}")
                        del file_timestamps[deleted_file]
                        if deleted_file in file_sizes:
                            del file_sizes[deleted_file]

                    save_state()
                    time.sleep(interval)

        except KeyboardInterrupt:
            click.echo(f"\n{Fore.YELLOW}Monitor stopped by user{Style.RESET_ALL}")
            save_state()

    except Exception as e:
        click.echo(f"{Fore.RED}Monitoring failed: {e}{Style.RESET_ALL}", err=True)
        if ctx.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Directory to process",
)
@click.option("--pattern", "-p", default="*.jsonl", help="File pattern to match (default: *.jsonl)")
@click.option("--recursive", "-r", is_flag=True, help="Process directories recursively")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file for results")
@click.option("--parallel", type=int, default=4, help="Number of parallel workers")
@pass_context
def batch(
    ctx: CLIContext,
    directory: Path,
    pattern: str,
    recursive: bool,
    output_format: str,
    output: Path | None,
    parallel: int,
):
    """
    Process multiple JSONL files in batch mode for analysis

    Efficiently analyzes entire directories of JSONL files with parallel
    processing and comprehensive reporting.

    Examples:
      ccmonitor batch /projects --pattern "*.jsonl" --recursive
      ccmonitor batch /data --format json --output batch_report.json
      ccmonitor batch /work --parallel 8 --format csv
    """
    try:
        from .batch import BatchProcessor

        if ctx.verbose:
            click.echo(f"{Fore.CYAN}Batch Analysis Configuration:{Style.RESET_ALL}")
            click.echo(f"  Directory: {directory}")
            click.echo(f"  Pattern: {pattern}")
            click.echo(f"  Recursive: {recursive}")
            click.echo(f"  Format: {output_format}")
            click.echo(f"  Parallel workers: {parallel}")
            click.echo()

        # Initialize batch processor
        batch_processor = BatchProcessor(
            directory=directory,
            pattern=pattern,
            recursive=recursive,
            parallel_workers=parallel,
            verbose=ctx.verbose,
        )

        # Process directory for analysis only
        result = batch_processor.analyze_directory()

        # Output results
        if output:
            batch_processor.export_results(result, output, output_format)
            click.echo(f"{Fore.GREEN}Results exported to {output}{Style.RESET_ALL}")
        else:
            batch_processor.display_results(result, output_format)

    except ImportError:
        click.echo(
            f"{Fore.RED}Error: Batch processing module not available{Style.RESET_ALL}", err=True,
        )
        sys.exit(1)
    except Exception as e:
        click.echo(f"{Fore.RED}Batch processing failed: {e}{Style.RESET_ALL}", err=True)
        if ctx.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


@cli.group()
def config():
    """Configuration management commands"""


@config.command("show")
@pass_context
def config_show(ctx: CLIContext):
    """Show current configuration"""
    try:
        current_config = config_manager.get_current_config()

        click.echo(f"{Fore.CYAN}Current Configuration:{Style.RESET_ALL}")
        for key, value in current_config.items():
            click.echo(f"  {key}: {value}")

    except Exception as e:
        click.echo(f"{Fore.RED}Error reading configuration: {e}{Style.RESET_ALL}", err=True)
        sys.exit(1)


@config.command("set")
@click.argument("key")
@click.argument("value")
@pass_context
def config_set(ctx: CLIContext, key: str, value: str):
    """Set configuration value"""
    try:
        config_manager.set_config_value(key, value)
        click.echo(f"{Fore.GREEN}Configuration updated: {key} = {value}{Style.RESET_ALL}")

    except Exception as e:
        click.echo(f"{Fore.RED}Error updating configuration: {e}{Style.RESET_ALL}", err=True)
        sys.exit(1)


# Helper functions for display


def _display_file_stats(file_path: Path, stats: dict[str, Any]):
    """Display file analysis statistics"""
    click.echo(f"\n{Fore.CYAN}Analysis Results for {file_path}:{Style.RESET_ALL}")
    click.echo(f"  Total messages: {stats.get('total_messages', 0):,}")
    click.echo(f"  Message types: {stats.get('message_types', {})}")
    click.echo(f"  Conversation depth: {stats.get('conversation_depth', 0)}")
    click.echo(f"  File size: {format_size(stats.get('file_size', 0))}")

    if stats.get("patterns"):
        click.echo(f"  Patterns found: {len(stats['patterns'])}")


if __name__ == "__main__":
    cli()
