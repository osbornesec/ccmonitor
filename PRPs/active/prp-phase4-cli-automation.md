# PRP: CLI Tool & Automation System

## Objective
Develop a comprehensive command-line interface and automation system for intelligent JSONL pruning with batch processing, scheduling, and user-friendly operations.

## Success Criteria
- [ ] Create intuitive CLI with comprehensive options and help
- [ ] Implement batch processing for entire project directories
- [ ] Develop automated scheduling system with configurable policies
- [ ] Provide detailed statistics and reporting capabilities
- [ ] Enable dry-run mode and selective pruning operations

## Test-Driven Development Plan

### Phase 4.1: Command-Line Interface Development

#### Tests to Write First
```python
def test_cli_basic_operations():
    """Test basic CLI commands and argument parsing"""
    
def test_cli_help_and_documentation():
    """Test help text and usage documentation"""
    
def test_cli_error_handling():
    """Test CLI error handling and user feedback"""
    
def test_cli_configuration_options():
    """Test configuration file loading and validation"""
    
def test_cli_output_formatting():
    """Test output formatting and verbosity levels"""
```

#### Implementation Tasks
1. **Main CLI Interface**
   ```bash
   # Usage examples
   claude-prune --file session.jsonl --level medium --backup
   claude-prune --directory /home/michael/.claude/projects --level light --dry-run
   claude-prune --project ccobservatory --aggressive --stats
   claude-prune --restore backup.20240101.jsonl --target session.jsonl
   ```

2. **Argument Parsing and Validation**
   - Comprehensive argument validation and error messages
   - Support for both file and directory operations
   - Configuration file support for default settings
   - Environment variable integration

3. **User Experience Features**
   - Progress bars for long operations
   - Colorized output for better readability
   - Interactive confirmation for destructive operations
   - Verbose and quiet modes

4. **Help and Documentation**
   - Comprehensive help text with examples
   - Man page generation
   - Usage tips and best practices
   - Error code documentation

### Phase 4.2: Batch Processing System

#### Tests to Write First
```python
def test_directory_scanning():
    """Test recursive directory scanning for JSONL files"""
    
def test_batch_processing_pipeline():
    """Test batch processing with progress tracking"""
    
def test_parallel_processing():
    """Test concurrent processing of multiple files"""
    
def test_batch_error_handling():
    """Test error handling during batch operations"""
    
def test_batch_reporting():
    """Test comprehensive batch operation reporting"""
```

#### Implementation Tasks
1. **Directory Processing Engine**
   - Recursive JSONL file discovery
   - Intelligent file filtering (exclude backups, temp files)
   - Size-based processing prioritization
   - Pattern-based inclusion/exclusion rules

2. **Parallel Processing Framework**
   - Multi-threaded file processing
   - Resource-aware concurrent operations
   - Progress tracking across parallel jobs
   - Error isolation between concurrent operations

3. **Batch Operation Management**
   - Resume interrupted batch operations
   - Selective reprocessing of failed files
   - Dependency-aware processing order
   - Memory-efficient large dataset handling

### Phase 4.3: Automated Scheduling System

#### Tests to Write First
```python
def test_auto_pruner_initialization():
    """Test automated pruner configuration and setup"""
    
def test_scheduling_policies():
    """Test different pruning policies and schedules"""
    
def test_age_based_pruning():
    """Test pruning based on file age and access patterns"""
    
def test_scheduled_maintenance():
    """Test weekly maintenance and optimization runs"""
    
def test_scheduling_error_recovery():
    """Test error handling in automated operations"""
```

#### Implementation Tasks
1. **Auto-Pruning Scheduler**
   ```python
   class AutoPruner:
       def schedule_pruning(self):
           # Prune sessions older than 30 days (light)
           # Prune sessions older than 7 days (medium) 
           # Preserve recent sessions and frequently accessed files
           # Run weekly maintenance on entire projects directory
   ```

2. **Pruning Policies**
   - Age-based pruning with configurable thresholds
   - Access pattern analysis for frequently used files
   - Project-specific pruning configurations
   - User activity-aware scheduling

3. **Maintenance Operations**
   - Weekly maintenance runs with comprehensive reporting
   - Backup cleanup and archive management
   - Performance optimization and index rebuilding
   - Health checks and validation runs

4. **Configuration Management**
   - User-configurable pruning policies
   - Project-specific settings inheritance
   - Global defaults with local overrides
   - Dynamic policy adjustment based on usage patterns

### Phase 4.4: Statistics and Reporting

#### Tests to Write First
```python
def test_statistics_collection():
    """Test comprehensive statistics gathering"""
    
def test_report_generation():
    """Test detailed report generation and formatting"""
    
def test_performance_tracking():
    """Test performance metrics tracking and analysis"""
    
def test_trend_analysis():
    """Test trend analysis and historical data processing"""
    
def test_export_capabilities():
    """Test data export in various formats (JSON, CSV, HTML)"""
```

#### Implementation Tasks
1. **Statistics Collection Engine**
   - File size reduction metrics
   - Processing performance data
   - Content preservation statistics
   - User satisfaction tracking

2. **Reporting Framework**
   - Detailed operation reports with visualizations
   - Historical trend analysis
   - Performance benchmarking
   - Cost-benefit analysis (storage vs. performance)

3. **Data Export and Integration**
   - JSON, CSV, and HTML report formats
   - Integration with monitoring systems
   - API endpoints for programmatic access
   - Dashboard integration capabilities

### Phase 4.5: Advanced Features

#### Tests to Write First
```python
def test_dry_run_simulation():
    """Test dry-run mode with accurate simulations"""
    
def test_selective_pruning():
    """Test date range and pattern-based selective pruning"""
    
def test_configuration_profiles():
    """Test named configuration profiles for different use cases"""
    
def test_integration_hooks():
    """Test integration with external tools and workflows"""
```

#### Implementation Tasks
1. **Dry-Run Mode**
   - Accurate simulation without file modification
   - Preview of changes with detailed impact analysis
   - What-if analysis for different pruning levels
   - Safe exploration of pruning effects

2. **Selective Operations**
   - Date range-based pruning
   - Pattern-based file selection
   - Project-specific operations
   - Custom filter expressions

3. **Integration Features**
   - Git integration for commit-aware pruning
   - CI/CD pipeline integration
   - IDE plugin support preparation
   - External tool compatibility

## Deliverables
1. **CLI Application** (`src/cli/main.py`)
2. **Batch Processing Engine** (`src/cli/batch.py`)
3. **Scheduling System** (`src/cli/scheduler.py`)
4. **Statistics and Reporting** (`src/cli/reporting.py`)
5. **Configuration Management** (`src/cli/config.py`)
6. **User Documentation** (`docs/cli_guide.md`)
7. **Installation Package** (`setup.py`, `pyproject.toml`)

## Dependencies
- Phase 3 completion (safety and validation systems)
- Python libraries: `argparse`, `configparser`, `rich`, `click`
- Optional dependencies: `psutil`, `schedule`, `jinja2`
- Testing framework: `pytest`, `pytest-mock`

## Context7 Documentation References

### Click Framework for Professional CLI Development
Using Click for robust command-line interface construction:

```python
import click
from pathlib import Path
from typing import Optional

# Main CLI group with global options
@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config', type=click.Path(path_type=Path), 
              help='Configuration file path')
@click.option('--dry-run', is_flag=True, help='Preview operations without executing')
@click.pass_context
def cli(ctx, verbose: bool, config: Optional[Path], dry_run: bool):
    """JSONL Context Pruning Tool - Intelligent conversation file optimization"""
    ctx.ensure_object(dict)
    ctx.obj.update({
        'verbose': verbose,
        'config': config,
        'dry_run': dry_run
    })

# Single file pruning command
@cli.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path),
              help='Output file (default: overwrite input)')
@click.option('--level', type=click.Choice(['light', 'medium', 'aggressive']), 
              default='medium', help='Pruning intensity level')
@click.option('--backup/--no-backup', default=True, 
              help='Create backup before pruning')
@click.option('--stats', is_flag=True, help='Show detailed statistics')
@click.pass_context
def prune(ctx, input_file: Path, output: Optional[Path], level: str, 
          backup: bool, stats: bool):
    """Prune a single JSONL conversation file"""
    if ctx.obj['verbose']:
        click.echo(f"Pruning {input_file} with {level} intensity")
    
    if ctx.obj['dry_run']:
        click.echo("🔍 DRY RUN: Showing what would be done...")
        # Preview logic here
        return
    
    # Actual pruning logic
    output_file = output or input_file
    
    if backup and not ctx.obj['dry_run']:
        backup_path = input_file.with_suffix(f"{input_file.suffix}.backup")
        click.echo(f"📁 Creating backup: {backup_path}")
    
    # Progress indication for large files
    with click.progressbar(length=100, label='Processing') as bar:
        # Simulate processing steps
        for i in range(100):
            # Actual processing logic here
            bar.update(1)
    
    if stats:
        click.echo(f"✅ Completed: {level} pruning on {input_file}")

# Batch processing command
@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option('--pattern', default='*.jsonl', help='File pattern to match')
@click.option('--recursive', '-r', is_flag=True, help='Process subdirectories')
@click.option('--level', type=click.Choice(['light', 'medium', 'aggressive']), 
              default='medium')
@click.option('--parallel', '-p', type=int, default=1, 
              help='Number of parallel workers')
@click.pass_context
def batch(ctx, directory: Path, pattern: str, recursive: bool, 
          level: str, parallel: int):
    """Batch process JSONL files in directory"""
    search_pattern = f"**/{pattern}" if recursive else pattern
    files = list(directory.glob(search_pattern))
    
    if not files:
        click.echo("⚠️  No matching files found")
        return
    
    click.echo(f"📂 Found {len(files)} files to process")
    
    # Process with progress bar
    with click.progressbar(files, label='Processing files') as bar:
        for file_path in bar:
            if ctx.obj['verbose']:
                click.echo(f"Processing: {file_path}")
            # Process individual file

# Statistics and reporting command
@cli.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option('--format', type=click.Choice(['text', 'json', 'csv']), 
              default='text', help='Output format')
@click.option('--output', '-o', type=click.File('w'), default='-',
              help='Output file (default: stdout)')
def stats(files, format: str, output):
    """Generate statistics for JSONL files"""
    if not files:
        click.echo("⚠️  No files specified", err=True)
        return
    
    stats_data = {}
    for file_path in files:
        # Analyze file and collect stats
        file_stats = analyze_jsonl_file(file_path)
        stats_data[str(file_path)] = file_stats
    
    # Format output based on user preference
    if format == 'json':
        import json
        json.dump(stats_data, output, indent=2)
    elif format == 'text':
        for file_path, stats in stats_data.items():
            click.echo(f"\n📄 {file_path}:", file=output)
            click.echo(f"  Messages: {stats['message_count']}", file=output)
            click.echo(f"  Size: {stats['file_size_mb']:.2f} MB", file=output)

# Configuration management
@cli.command()
@click.option('--show', is_flag=True, help='Show current configuration')
@click.option('--set', 'set_option', nargs=2, multiple=True,
              help='Set configuration option (key value)')
@click.option('--reset', is_flag=True, help='Reset to defaults')
def config(show: bool, set_option, reset: bool):
    """Manage configuration settings"""
    config_file = Path.home() / '.claude-prune.conf'
    
    if reset:
        if config_file.exists():
            config_file.unlink()
        click.echo("✅ Configuration reset to defaults")
        return
    
    if show:
        if config_file.exists():
            click.echo(f"📋 Configuration from {config_file}:")
            click.echo(config_file.read_text())
        else:
            click.echo("📋 Using default configuration (no config file)")
        return
    
    # Handle setting options
    for key, value in set_option:
        click.echo(f"Setting {key} = {value}")
        # Update configuration logic

# Version and help enhancement
@cli.command()
def version():
    """Show version information"""
    click.echo("claude-prune version 1.0.0")
    click.echo("JSONL Context Pruning Tool")

if __name__ == '__main__':
    cli()
```

### Click Testing Patterns
Comprehensive CLI testing using Click's testing utilities:

```python
import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile

def test_basic_cli_invocation():
    """Test basic CLI command execution"""
    runner = CliRunner()
    
    # Test help command
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'JSONL Context Pruning Tool' in result.output

def test_prune_command_with_options():
    """Test prune command with various options"""
    runner = CliRunner()
    
    with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
        test_file = Path(f.name)
        f.write(b'{"test": "data"}\n')
    
    try:
        # Test dry run
        result = runner.invoke(cli, [
            '--dry-run', 'prune', str(test_file), '--level', 'medium'
        ])
        assert result.exit_code == 0
        assert 'DRY RUN' in result.output
        
        # Test with verbose flag
        result = runner.invoke(cli, [
            '--verbose', 'prune', str(test_file), '--no-backup'
        ])
        assert result.exit_code == 0
        
    finally:
        test_file.unlink()

def test_batch_command():
    """Test batch processing command"""
    runner = CliRunner()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files
        for i in range(3):
            test_file = temp_path / f"test_{i}.jsonl"
            test_file.write_text(f'{{"test": "data_{i}"}}\n')
        
        result = runner.invoke(cli, [
            'batch', str(temp_path), '--level', 'light', '--dry-run'
        ])
        assert result.exit_code == 0

def test_error_handling():
    """Test CLI error handling"""
    runner = CliRunner()
    
    # Test non-existent file
    result = runner.invoke(cli, ['prune', 'nonexistent.jsonl'])
    assert result.exit_code != 0
    assert 'does not exist' in result.output.lower()

# Mock testing for complex operations
@pytest.fixture
def mock_pruner():
    """Mock pruner for testing without actual file operations"""
    with pytest.mock.patch('claude_prune.core.JSONLPruner') as mock:
        mock.return_value.prune_file.return_value = {
            'original_size': 1000,
            'pruned_size': 600,
            'reduction_percent': 40
        }
        yield mock

def test_cli_with_mocked_pruner(mock_pruner):
    """Test CLI with mocked underlying operations"""
    runner = CliRunner()
    
    with tempfile.NamedTemporaryFile(suffix='.jsonl') as f:
        result = runner.invoke(cli, ['prune', f.name, '--stats'])
        assert result.exit_code == 0
        mock_pruner.return_value.prune_file.assert_called_once()
```

### Advanced Click Patterns for CLI Enhancement
Professional CLI features using Click's advanced capabilities:

```python
# Custom parameter types for validation
class JSONLPath(click.Path):
    """Custom path type that validates JSONL files"""
    
    def convert(self, value, param, ctx):
        path = super().convert(value, param, ctx)
        
        if not str(path).endswith('.jsonl'):
            self.fail(f'{path} is not a .jsonl file', param, ctx)
        
        return Path(path)

# Context settings for better UX
CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help'],
    max_content_width=120,
    token_normalize_func=lambda token: token.lower()
)

@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    """Professional CLI with enhanced UX"""
    pass

# Command chaining for pipeline operations
@cli.group(chain=True)
def pipeline():
    """Chain multiple operations in sequence"""
    pass

@pipeline.command()
def analyze():
    """Analyze JSONL files"""
    click.echo("📊 Analyzing...")
    return "analysis_result"

@pipeline.command()
def optimize():
    """Optimize based on analysis"""
    click.echo("⚡ Optimizing...")
    return "optimization_result"

@pipeline.result_callback()
def process_pipeline(results):
    """Process the pipeline results"""
    click.echo(f"🎯 Pipeline completed with {len(results)} steps")

# Environment variable integration
@click.command()
@click.option('--api-key', envvar='CLAUDE_API_KEY', 
              help='API key (or set CLAUDE_API_KEY env var)')
@click.option('--config-dir', envvar='CLAUDE_CONFIG_DIR',
              type=click.Path(path_type=Path),
              default=lambda: Path.home() / '.claude',
              help='Configuration directory')
def advanced_command(api_key: str, config_dir: Path):
    """Command with environment variable integration"""
    if not api_key:
        click.echo("⚠️  API key required", err=True)
        raise click.Abort()
    
    click.echo(f"📁 Using config directory: {config_dir}")

# Shell completion support
def get_available_projects(ctx, param, incomplete):
    """Provide completion for project names"""
    projects_dir = Path.home() / '.claude' / 'projects'
    if projects_dir.exists():
        return [p.name for p in projects_dir.iterdir() 
                if p.is_dir() and p.name.startswith(incomplete)]
    return []

@click.command()
@click.option('--project', shell_complete=get_available_projects,
              help='Project name (with shell completion)')
def project_command(project: str):
    """Command with shell completion"""
    click.echo(f"🎯 Working on project: {project}")
```

## User Experience Requirements
- Intuitive command structure following Unix conventions
- Clear error messages with actionable suggestions
- Progress indication for long-running operations
- Comprehensive help and documentation
- Safe defaults with easy customization

## Performance Requirements
- CLI startup time <500ms
- Batch processing throughput >10 files/second
- Memory usage scales linearly with file size
- Responsive progress updates every 2 seconds
- Efficient handling of 1000+ file directories

## Acceptance Criteria
- All tests pass with >95% coverage
- CLI follows standard Unix conventions and best practices
- User acceptance testing with 90% satisfaction rating
- Performance requirements met on target hardware
- Comprehensive documentation with examples

## Risk Mitigation
- Extensive user testing before release
- Safe defaults to prevent accidental data loss
- Comprehensive error handling and recovery
- Backward compatibility with existing workflows
- Gradual feature rollout with user feedback

## Integration Points
- Claude Code hooks system compatibility
- Project configuration file integration
- Version control system awareness
- IDE and editor plugin preparation
- Monitoring and observability tool integration

## Next Steps
Upon completion, this PRP delivers a production-ready CLI tool for intelligent JSONL pruning with full automation capabilities, making the system accessible to all Claude Code users.