"""Main CLI interface for ccmonitor tool."""

from __future__ import annotations

import sys
from pathlib import Path

import click
import colorama
from colorama import Fore, Style

from src.common.exceptions import ConfigurationError, IOOperationError

from .commands.api import api
from .commands.config import config
from .commands.export import export
from .commands.monitor import monitor
from .commands.tui import tui
from .config import ConfigManager
from .db_commands import db
from .types import CLIContext

colorama.init()
config_manager = ConfigManager()
__version__ = "0.1.0"


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
    """CCMonitor: Claude Code conversation monitoring tool."""
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
    # If no command is provided, show help
    if click_ctx.invoked_subcommand is None:
        click.echo(click_ctx.get_help())


# Add all commands
cli.add_command(monitor)
cli.add_command(tui)
cli.add_command(config)
cli.add_command(export)
cli.add_command(api)
cli.add_command(db)
# Stable public API - only CLI entry point
__all__ = [
    "cli",
]

if __name__ == "__main__":
    cli()
