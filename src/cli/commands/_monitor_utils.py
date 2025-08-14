"""Shared monitor utility functions."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from colorama import Fore, Style


def _validate_monitor_directory(directory: Path) -> Path:
    """Validate and expand monitor directory path."""
    monitor_dir = Path(str(directory)).expanduser().resolve()
    if not monitor_dir.exists():
        click.echo(
            f"{Fore.RED}Error: Directory {monitor_dir} does not exist{Style.RESET_ALL}",
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
