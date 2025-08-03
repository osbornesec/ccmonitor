"""
Main CLI interface for claude-prune tool
Phase 4.1 - Professional command-line interface with Click framework
"""

import sys
import json
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any

import click
import colorama
from colorama import Fore, Style

from .config import ConfigManager
from .utils import setup_logging, format_size, format_duration, validate_file_access
from ..pruner.core import JSONLPruner
from ..pruner.safety import SafePruner
from ..utils.backup import BackupManager
from ..temporal.decay_engine import DecayMode
from ..config.temporal_config import get_preset_config


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
        self.dry_run = False
        self.config = {}


# Pass context between commands
pass_context = click.make_pass_decorator(CLIContext, ensure=True)


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version and exit')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config', type=click.Path(exists=True), help='Configuration file path')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.pass_context
def cli(click_ctx, version: bool, verbose: bool, config: Optional[str], dry_run: bool):
    """
    Claude-Prune: Intelligent JSONL conversation pruning tool
    
    A powerful CLI tool for pruning JSONL conversation files with intelligent
    content analysis, batch processing, and automated scheduling capabilities.
    
    Examples:
      claude-prune prune session.jsonl --level medium --backup
      claude-prune batch /projects --pattern "*.jsonl" --recursive
      claude-prune stats session.jsonl --format json --output report.json
    """
    if version:
        click.echo(f"claude-prune version {__version__}")
        sys.exit(0)
    
    # Setup context
    ctx = click_ctx.ensure_object(CLIContext)
    ctx.verbose = verbose
    ctx.config_file = config
    ctx.dry_run = dry_run
    
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
@click.option('--file', '-f', 'input_file', type=click.Path(exists=True, path_type=Path), 
              help='Input JSONL file to process')
@click.option('--output', '-o', type=click.Path(path_type=Path), 
              help='Output file path (default: overwrites input or adds .pruned suffix)')
@click.option('--level', '-l', type=click.Choice(['light', 'medium', 'aggressive', 'ultra']), 
              default='medium', help='Pruning aggressiveness level')
@click.option('--temporal-decay/--no-temporal-decay', default=False, 
              help='Enable temporal decay for time-based importance weighting')
@click.option('--decay-mode', type=click.Choice(['none', 'simple', 'multi_stage', 'content_aware', 'adaptive']),
              default='simple', help='Temporal decay mode')
@click.option('--decay-preset', type=click.Choice(['development', 'debugging', 'conversation', 'analysis', 'aggressive', 'conservative']),
              help='Use temporal decay preset configuration')
@click.option('--backup/--no-backup', default=True, help='Create backup before processing')
@click.option('--stats/--no-stats', default=False, help='Display processing statistics')
@click.option('--progress/--no-progress', default=True, help='Show progress bar')
@pass_context
def prune(ctx: CLIContext, input_file: Path, output: Optional[Path], level: str,
          temporal_decay: bool, decay_mode: str, decay_preset: Optional[str],
          backup: bool, stats: bool, progress: bool):
    """
    Prune a single JSONL conversation file
    
    Intelligently removes redundant content while preserving conversation
    context and maintaining conversation flow integrity.
    
    Examples:
      claude-prune prune session.jsonl --level light --backup
      claude-prune prune data.jsonl --output pruned.jsonl --stats
      claude-prune prune conversation.jsonl --level aggressive --no-backup
    """
    try:
        # Validate input file
        if not validate_file_access(input_file, 'read'):
            click.echo(f"{Fore.RED}Error: Cannot read input file {input_file}{Style.RESET_ALL}", err=True)
            sys.exit(1)
        
        # Determine output file
        if not output:
            if ctx.dry_run:
                output = input_file.with_suffix('.pruned.jsonl')
            else:
                output = input_file  # Overwrite input
        
        # Validate output path
        if not ctx.dry_run and not validate_file_access(output.parent, 'write'):
            click.echo(f"{Fore.RED}Error: Cannot write to output directory {output.parent}{Style.RESET_ALL}", err=True)
            sys.exit(1)
        
        # Display operation info
        if ctx.verbose or ctx.dry_run:
            click.echo(f"{Fore.CYAN}Operation Details:{Style.RESET_ALL}")
            click.echo(f"  Input file: {input_file}")
            click.echo(f"  Output file: {output}")
            click.echo(f"  Pruning level: {level}")
            click.echo(f"  Backup: {backup}")
            if ctx.dry_run:
                click.echo(f"  {Fore.YELLOW}DRY RUN - No files will be modified{Style.RESET_ALL}")
            click.echo()
        
        if ctx.dry_run:
            # Perform dry run analysis
            _perform_dry_run_analysis(input_file, level, stats)
            return
        
        # Create backup if requested
        backup_manager = BackupManager()
        backup_path = None
        
        if backup:
            try:
                backup_path = backup_manager.create_backup(input_file)
                if ctx.verbose:
                    click.echo(f"{Fore.GREEN}Backup created: {backup_path}{Style.RESET_ALL}")
            except Exception as e:
                click.echo(f"{Fore.RED}Warning: Failed to create backup: {e}{Style.RESET_ALL}", err=True)
                if not click.confirm("Continue without backup?"):
                    sys.exit(1)
        
        # Initialize pruner
        try:
            if backup:
                pruner = SafePruner(
                    pruning_level=level,
                    enable_compression=True,
                    backup_retention_days=7
                )
            else:
                # Use basic pruner without safety features
                from ..pruner.core import JSONLPruner
                pruner = JSONLPruner(pruning_level=level)
        except Exception as e:
            click.echo(f"{Fore.RED}Error initializing pruner: {e}{Style.RESET_ALL}", err=True)
            sys.exit(1)
        
        # Process file with progress tracking
        start_time = time.time()
        
        try:
            if progress and not ctx.verbose:
                with click.progressbar(length=100, label='Processing file') as bar:
                    # Process file with appropriate method
                    if hasattr(pruner, 'safe_process_file'):
                        result = pruner.safe_process_file(input_file, output)
                    else:
                        result = pruner.process_file(input_file, output)
                    bar.update(100)
            else:
                # Process file with appropriate method
                if hasattr(pruner, 'safe_process_file'):
                    result = pruner.safe_process_file(input_file, output)
                else:
                    result = pruner.process_file(input_file, output)
            
            processing_time = time.time() - start_time
            
        except Exception as e:
            click.echo(f"{Fore.RED}Error processing file: {e}{Style.RESET_ALL}", err=True)
            
            # Restore backup if processing failed
            if backup_path and backup_path.exists():
                try:
                    backup_manager.restore_backup(backup_path, input_file)
                    click.echo(f"{Fore.YELLOW}Restored original file from backup{Style.RESET_ALL}")
                except Exception as restore_e:
                    click.echo(f"{Fore.RED}Failed to restore backup: {restore_e}{Style.RESET_ALL}", err=True)
            
            sys.exit(1)
        
        # Display success message
        click.echo(f"{Fore.GREEN}✓ Processing complete{Style.RESET_ALL}")
        
        # Display statistics if requested
        if stats or ctx.verbose:
            _display_processing_stats(result, processing_time, input_file, output)
            
    except KeyboardInterrupt:
        click.echo(f"\n{Fore.YELLOW}Operation cancelled by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}", err=True)
        if ctx.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--directory', '-d', type=click.Path(exists=True, file_okay=False, path_type=Path),
              help='Directory to process')
@click.option('--pattern', '-p', default='*.jsonl', help='File pattern to match (default: *.jsonl)')
@click.option('--recursive', '-r', is_flag=True, help='Process directories recursively')
@click.option('--level', '-l', type=click.Choice(['light', 'medium', 'aggressive', 'ultra']), 
              default='medium', help='Pruning aggressiveness level')
@click.option('--temporal-decay/--no-temporal-decay', default=False, 
              help='Enable temporal decay for time-based importance weighting')
@click.option('--decay-mode', type=click.Choice(['none', 'simple', 'multi_stage', 'content_aware', 'adaptive']),
              default='simple', help='Temporal decay mode')
@click.option('--decay-preset', type=click.Choice(['development', 'debugging', 'conversation', 'analysis', 'aggressive', 'conservative']),
              help='Use temporal decay preset configuration')
@click.option('--parallel', type=int, default=4, help='Number of parallel workers')
@click.option('--resume', is_flag=True, help='Resume interrupted batch operation')
@click.option('--backup/--no-backup', default=True, help='Create backups before processing')
@pass_context
def batch(ctx: CLIContext, directory: Path, pattern: str, recursive: bool, level: str,
          temporal_decay: bool, decay_mode: str, decay_preset: Optional[str],
          parallel: int, resume: bool, backup: bool):
    """
    Process multiple JSONL files in batch mode
    
    Efficiently processes entire directories of JSONL files with parallel
    processing and resume capability for interrupted operations.
    
    Examples:
      claude-prune batch /projects --pattern "*.jsonl" --recursive
      claude-prune batch /data --level aggressive --parallel 8
      claude-prune batch /work --resume
    """
    try:
        from .batch import BatchProcessor
        
        if ctx.verbose:
            click.echo(f"{Fore.CYAN}Batch Processing Configuration:{Style.RESET_ALL}")
            click.echo(f"  Directory: {directory}")
            click.echo(f"  Pattern: {pattern}")
            click.echo(f"  Recursive: {recursive}")
            click.echo(f"  Level: {level}")
            click.echo(f"  Parallel workers: {parallel}")
            click.echo(f"  Resume: {resume}")
            click.echo()
        
        # Initialize batch processor
        batch_processor = BatchProcessor(
            directory=directory,
            pattern=pattern,
            recursive=recursive,
            level=level,
            parallel_workers=parallel,
            enable_backup=backup,
            dry_run=ctx.dry_run,
            verbose=ctx.verbose
        )
        
        # Process with resume capability
        if resume:
            result = batch_processor.resume_processing()
        else:
            result = batch_processor.process_directory()
        
        # Display results
        _display_batch_results(result, ctx.verbose)
        
    except ImportError:
        click.echo(f"{Fore.RED}Error: Batch processing module not available{Style.RESET_ALL}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"{Fore.RED}Batch processing failed: {e}{Style.RESET_ALL}", err=True)
        if ctx.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--file', '-f', type=click.Path(exists=True, path_type=Path), 
              help='JSONL file to analyze')
@click.option('--directory', '-d', type=click.Path(exists=True, file_okay=False, path_type=Path),
              help='Directory to analyze')
@click.option('--recursive', '-r', is_flag=True, help='Analyze directories recursively')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json', 'csv', 'html']),
              default='table', help='Output format')
@click.option('--output', '-o', type=click.Path(path_type=Path), help='Output file path')
@click.option('--trend', is_flag=True, help='Include trend analysis')
@pass_context
def stats(ctx: CLIContext, file: Optional[Path], directory: Optional[Path], recursive: bool,
          output_format: str, output: Optional[Path], trend: bool):
    """
    Generate statistics and analysis reports
    
    Analyzes JSONL files to provide detailed statistics about conversation
    patterns, message types, and compression opportunities.
    
    Examples:
      claude-prune stats session.jsonl --format json --output report.json
      claude-prune stats --directory /projects --recursive --trend
      claude-prune stats data.jsonl --format html --output report.html
    """
    try:
        from .reporting import StatisticsGenerator
        
        if not file and not directory:
            click.echo(f"{Fore.RED}Error: Must specify either --file or --directory{Style.RESET_ALL}", err=True)
            sys.exit(1)
        
        # Initialize statistics generator
        stats_generator = StatisticsGenerator(verbose=ctx.verbose)
        
        # Generate analysis
        if file:
            result = stats_generator.analyze_file(file, include_trends=trend)
        else:
            result = stats_generator.analyze_directory(directory, recursive=recursive, include_trends=trend)
        
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
        click.echo(f"{Fore.RED}Statistics generation failed: {e}{Style.RESET_ALL}", err=True)
        if ctx.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--enable/--disable', default=False, help='Enable or disable automatic scheduling')
@click.option('--policy', type=click.Choice(['daily', 'weekly', 'monthly']), 
              default='weekly', help='Scheduling policy')
@click.option('--level', type=click.Choice(['light', 'medium', 'aggressive', 'ultra']), 
              default='light', help='Default pruning level for scheduled operations')
@click.option('--temporal-decay/--no-temporal-decay', default=False, 
              help='Enable temporal decay for scheduled operations')
@click.option('--decay-preset', type=click.Choice(['development', 'debugging', 'conversation', 'analysis', 'aggressive', 'conservative']),
              default='development', help='Temporal decay preset for scheduled operations')
@click.option('--directories', multiple=True, help='Directories to include in scheduled pruning')
@click.option('--show', is_flag=True, help='Show current scheduling configuration')
@pass_context
def schedule(ctx: CLIContext, enable: bool, policy: str, level: str, temporal_decay: bool, 
             decay_preset: str, directories: tuple, show: bool):
    """
    Configure automatic pruning schedules
    
    Sets up automated pruning schedules for regular maintenance of JSONL files
    with configurable policies and directory targets.
    
    Examples:
      claude-prune schedule --enable --policy weekly --level light
      claude-prune schedule --show
      claude-prune schedule --directories /projects /data --policy daily
    """
    try:
        from .scheduler import ScheduleManager
        
        schedule_manager = ScheduleManager(verbose=ctx.verbose)
        
        if show:
            config = schedule_manager.get_current_config()
            _display_schedule_config(config)
            return
        
        if enable:
            schedule_manager.setup_schedule(
                policy=policy,
                level=level,
                directories=list(directories) if directories else None
            )
            click.echo(f"{Fore.GREEN}Automatic scheduling enabled with {policy} policy{Style.RESET_ALL}")
        else:
            schedule_manager.disable_schedule()
            click.echo(f"{Fore.YELLOW}Automatic scheduling disabled{Style.RESET_ALL}")
            
    except ImportError:
        click.echo(f"{Fore.RED}Error: Scheduling module not available{Style.RESET_ALL}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"{Fore.RED}Scheduling configuration failed: {e}{Style.RESET_ALL}", err=True)
        if ctx.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.group()
def config():
    """Configuration management commands"""
    pass


@config.command('show')
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


@config.command('set')
@click.argument('key')
@click.argument('value')
@pass_context
def config_set(ctx: CLIContext, key: str, value: str):
    """Set configuration value"""
    try:
        config_manager.set_config_value(key, value)
        click.echo(f"{Fore.GREEN}Configuration updated: {key} = {value}{Style.RESET_ALL}")
        
    except Exception as e:
        click.echo(f"{Fore.RED}Error updating configuration: {e}{Style.RESET_ALL}", err=True)
        sys.exit(1)


# Helper functions

def _perform_dry_run_analysis(input_file: Path, level: str, show_stats: bool):
    """Perform dry-run analysis without modifying files"""
    try:
        from ..jsonl_analysis.analyzer import JSONLAnalyzer
        from ..jsonl_analysis.scoring import ImportanceScorer
        
        analyzer = JSONLAnalyzer()
        scorer = ImportanceScorer()
        
        click.echo(f"{Fore.YELLOW}DRY RUN ANALYSIS{Style.RESET_ALL}")
        click.echo(f"File: {input_file}")
        click.echo(f"Pruning level: {level}")
        click.echo()
        
        # Load and analyze messages
        messages = analyzer.parse_jsonl_file(input_file)
        
        # Calculate importance scores
        threshold = {'light': 20, 'medium': 40, 'aggressive': 60}[level]
        preserved_count = 0
        
        for message in messages:
            score = scorer.calculate_message_importance(message)
            if score >= threshold:
                preserved_count += 1
        
        removed_count = len(messages) - preserved_count
        compression_ratio = removed_count / len(messages) if messages else 0
        
        click.echo(f"Total messages: {len(messages)}")
        click.echo(f"Would preserve: {preserved_count}")
        click.echo(f"Would remove: {removed_count}")
        click.echo(f"Compression ratio: {compression_ratio:.2%}")
        
        if show_stats:
            click.echo(f"\n{Fore.CYAN}Detailed Analysis:{Style.RESET_ALL}")
            # Add more detailed dry-run analysis here
            
    except Exception as e:
        click.echo(f"{Fore.RED}Dry run analysis failed: {e}{Style.RESET_ALL}", err=True)


def _display_processing_stats(result: Dict[str, Any], processing_time: float, 
                            input_file: Path, output_file: Path):
    """Display processing statistics in a formatted table"""
    click.echo(f"\n{Fore.CYAN}Processing Statistics:{Style.RESET_ALL}")
    click.echo(f"  Messages processed: {result.get('messages_processed', 0):,}")
    click.echo(f"  Messages preserved: {result.get('messages_preserved', 0):,}")
    click.echo(f"  Messages removed: {result.get('messages_removed', 0):,}")
    click.echo(f"  Compression ratio: {result.get('compression_ratio', 0):.2%}")
    click.echo(f"  Processing time: {format_duration(processing_time)}")
    
    # File size information
    if input_file.exists() and output_file.exists():
        input_size = input_file.stat().st_size
        output_size = output_file.stat().st_size
        size_reduction = (input_size - output_size) / input_size if input_size > 0 else 0
        
        click.echo(f"  Original size: {format_size(input_size)}")
        click.echo(f"  Final size: {format_size(output_size)}")
        click.echo(f"  Size reduction: {size_reduction:.2%}")


def _display_batch_results(result: Dict[str, Any], verbose: bool):
    """Display batch processing results"""
    click.echo(f"\n{Fore.GREEN}Batch Processing Complete{Style.RESET_ALL}")
    click.echo(f"  Files processed: {result.get('files_processed', 0):,}")
    click.echo(f"  Files successful: {result.get('files_successful', 0):,}")
    click.echo(f"  Files failed: {result.get('files_failed', 0):,}")
    click.echo(f"  Total processing time: {format_duration(result.get('total_time', 0))}")
    
    if verbose and result.get('detailed_results'):
        click.echo(f"\n{Fore.CYAN}Detailed Results:{Style.RESET_ALL}")
        for file_result in result['detailed_results']:
            status = "✓" if file_result.get('success') else "✗"
            click.echo(f"  {status} {file_result.get('file', 'Unknown')}")


def _display_schedule_config(config: Dict[str, Any]):
    """Display current scheduling configuration"""
    click.echo(f"{Fore.CYAN}Scheduling Configuration:{Style.RESET_ALL}")
    click.echo(f"  Enabled: {config.get('enabled', False)}")
    click.echo(f"  Policy: {config.get('policy', 'None')}")
    click.echo(f"  Level: {config.get('level', 'None')}")
    click.echo(f"  Directories: {', '.join(config.get('directories', []))}")
    click.echo(f"  Last run: {config.get('last_run', 'Never')}")
    click.echo(f"  Next run: {config.get('next_run', 'Not scheduled')}")


if __name__ == '__main__':
    cli()