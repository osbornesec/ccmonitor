# PRP: Integration and CLI Compatibility

## Goal
Seamlessly integrate the TUI mode with the existing CLI structure, ensuring backward compatibility while providing a smooth transition between CLI and TUI modes.

## Why
The TUI must coexist with the existing CLI functionality, allowing users to choose their preferred interface mode while maintaining all existing features and configurations. This ensures a non-breaking upgrade path for current users.

## What
### Requirements
- Integrate TUI mode with existing CLI command structure
- Ensure `ccmonitor` command can launch either CLI or TUI
- Maintain compatibility with existing configuration system
- Add TUI-specific CLI flags and options
- Preserve all existing CLI functionality
- Create mode selection logic
- Add documentation and usage examples

### Success Criteria
- [ ] Existing CLI commands continue to work unchanged
- [ ] TUI launches with `ccmonitor` or `ccmonitor --tui`
- [ ] Configuration shared between CLI and TUI
- [ ] Smooth switching between modes
- [ ] No breaking changes to existing workflows
- [ ] Help text updated with TUI options
- [ ] Examples demonstrate both modes

## All Needed Context

### Technical Specifications

#### Enhanced CLI Entry Point
```python
# src/cli/main.py (enhanced)
import click
import sys
from typing import Optional
from pathlib import Path

@click.group(invoke_without_command=True)
@click.option('--tui/--no-tui', default=None, help='Launch TUI mode (default if no command given)')
@click.option('--config', '-c', type=click.Path(), help='Configuration file path')
@click.option('--verbose', '-v', count=True, help='Increase verbosity')
@click.option('--quiet', '-q', is_flag=True, help='Suppress output')
@click.option('--version', is_flag=True, help='Show version and exit')
@click.pass_context
def cli(ctx, tui, config, verbose, quiet, version):
    """
    CCMonitor - Claude Conversation Monitor
    
    Monitor and analyze Claude conversations across multiple projects.
    
    By default, launches the TUI interface. Use subcommands for CLI operations.
    
    Examples:
        ccmonitor              # Launch TUI
        ccmonitor --no-tui     # Show CLI help
        ccmonitor parse FILE   # Parse a conversation file (CLI)
        ccmonitor --tui        # Explicitly launch TUI
    """
    # Handle version flag
    if version:
        from src import __version__
        click.echo(f"CCMonitor version {__version__}")
        ctx.exit()
    
    # Store options in context
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet
    
    # Determine mode
    if ctx.invoked_subcommand is None:
        # No subcommand - decide between TUI and CLI help
        if tui is False:
            # Explicitly requested no TUI
            click.echo(ctx.get_help())
        else:
            # Default to TUI or explicitly requested
            launch_tui(ctx)
    elif tui is True:
        # TUI explicitly requested with subcommand - error
        click.echo("Error: Cannot use --tui with subcommands", err=True)
        ctx.exit(1)

def launch_tui(ctx):
    """Launch the TUI application."""
    try:
        # Check if TUI is available
        from src.tui.app import CCMonitorApp
        from src.tui.utils.startup import StartupValidator
        
        # Validate environment
        validator = StartupValidator()
        valid, error_message = validator.validate()
        
        if not valid:
            click.echo(f"Cannot launch TUI: {error_message}", err=True)
            click.echo("Use --no-tui to access CLI commands", err=True)
            ctx.exit(1)
        
        # Show any warnings
        for warning in validator.warnings:
            click.echo(f"Warning: {warning}", err=True)
        
        # Load configuration
        config_path = ctx.obj.get('config')
        if config_path:
            config = load_config(config_path)
        else:
            config = load_default_config()
        
        # Launch TUI
        app = CCMonitorApp(config=config)
        app.run()
        
    except ImportError as e:
        click.echo(f"TUI not available: {e}", err=True)
        click.echo("Install with: pip install ccmonitor[tui]", err=True)
        ctx.exit(1)
    except KeyboardInterrupt:
        # Clean exit on Ctrl+C
        click.echo("\nExiting...", err=True)
        ctx.exit(0)
    except Exception as e:
        click.echo(f"TUI failed to start: {e}", err=True)
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        ctx.exit(1)

# Existing CLI commands
@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file')
@click.option('--format', type=click.Choice(['json', 'yaml', 'csv']), default='json')
@click.pass_context
def parse(ctx, file, output, format):
    """Parse a conversation file."""
    # Existing parse implementation
    from src.cli.commands.parse import parse_conversation
    result = parse_conversation(file, format)
    
    if output:
        Path(output).write_text(result)
        click.echo(f"Parsed output saved to {output}")
    else:
        click.echo(result)

@cli.command()
@click.option('--project', '-p', help='Project to monitor')
@click.option('--tail', '-f', is_flag=True, help='Follow mode (like tail -f)')
@click.pass_context
def monitor(ctx, project, tail):
    """Monitor conversations (CLI mode)."""
    # CLI monitoring implementation
    from src.cli.commands.monitor import start_monitoring
    start_monitoring(project, tail)

@cli.command()
@click.option('--days', '-d', type=int, default=7, help='Number of days to analyze')
@click.pass_context
def stats(ctx, days):
    """Show conversation statistics."""
    from src.cli.commands.stats import show_statistics
    show_statistics(days)

@cli.command()
@click.pass_context
def config(ctx):
    """Manage configuration."""
    from src.cli.commands.config import manage_config
    manage_config()

# New TUI-specific command
@cli.command()
@click.option('--theme', type=click.Choice(['dark', 'light', 'monokai', 'solarized']))
@click.option('--size', help='Initial terminal size (WIDTHxHEIGHT)')
@click.pass_context
def tui(ctx, theme, size):
    """Launch TUI with specific options."""
    ctx.obj['tui_theme'] = theme
    ctx.obj['tui_size'] = size
    launch_tui(ctx)
```

#### Configuration Integration
```python
# src/config/manager.py
from pathlib import Path
import yaml
from typing import Dict, Any, Optional

class ConfigManager:
    """Unified configuration management for CLI and TUI."""
    
    DEFAULT_CONFIG_PATH = Path.home() / ".config" / "ccmonitor" / "config.yaml"
    
    DEFAULT_CONFIG = {
        'general': {
            'default_mode': 'tui',  # 'tui' or 'cli'
            'verbose': False,
            'log_level': 'INFO',
        },
        'cli': {
            'output_format': 'json',
            'color_output': True,
            'pager': 'less',
        },
        'tui': {
            'theme': 'dark',
            'start_maximized': False,
            'show_help_on_start': False,
            'animation_level': 'full',  # 'full', 'reduced', 'none'
            'autosave_state': True,
        },
        'monitoring': {
            'watch_paths': [],
            'poll_interval': 1.0,
            'max_history': 1000,
        },
        'database': {
            'path': '~/.config/ccmonitor/conversations.db',
            'auto_vacuum': True,
        },
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    user_config = yaml.safe_load(f) or {}
                
                # Merge with defaults
                config = self.DEFAULT_CONFIG.copy()
                self.deep_merge(config, user_config)
                return config
                
            except Exception as e:
                print(f"Warning: Failed to load config: {e}", file=sys.stderr)
                return self.DEFAULT_CONFIG.copy()
        else:
            return self.DEFAULT_CONFIG.copy()
    
    def save_config(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            yaml.safe_dump(self.config, f, default_flow_style=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    @staticmethod
    def deep_merge(base: dict, override: dict) -> None:
        """Deep merge override into base."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ConfigManager.deep_merge(base[key], value)
            else:
                base[key] = value
```

#### Mode Detection and Switching
```python
# src/cli/utils.py
import os
import sys
from typing import Optional

class ModeDetector:
    """Detect and manage UI mode selection."""
    
    @staticmethod
    def should_use_tui() -> bool:
        """Determine if TUI should be used by default."""
        # Check if running in a terminal
        if not sys.stdout.isatty():
            return False
        
        # Check if explicitly disabled
        if os.environ.get('CCMONITOR_NO_TUI'):
            return False
        
        # Check if running in CI/CD
        if os.environ.get('CI') or os.environ.get('CONTINUOUS_INTEGRATION'):
            return False
        
        # Check if piped or redirected
        if not sys.stdin.isatty():
            return False
        
        # Check terminal capabilities
        term = os.environ.get('TERM', '')
        if term == 'dumb' or not term:
            return False
        
        return True
    
    @staticmethod
    def can_use_tui() -> Tuple[bool, Optional[str]]:
        """Check if TUI can be used in current environment."""
        try:
            # Check textual availability
            import textual
            
            # Check terminal
            if not sys.stdout.isatty():
                return False, "Not running in a terminal"
            
            # Check size
            import shutil
            cols, rows = shutil.get_terminal_size()
            if cols < 80 or rows < 24:
                return False, f"Terminal too small ({cols}x{rows}). Minimum: 80x24"
            
            return True, None
            
        except ImportError:
            return False, "TUI dependencies not installed"
        except Exception as e:
            return False, str(e)
```

#### Shared Services
```python
# src/services/monitoring.py
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class MonitoringService(ABC):
    """Abstract monitoring service used by both CLI and TUI."""
    
    @abstractmethod
    def start(self) -> None:
        """Start monitoring."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop monitoring."""
        pass
    
    @abstractmethod
    def get_conversations(self, project: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get conversations for a project."""
        pass

class ConversationMonitor(MonitoringService):
    """Concrete implementation of monitoring service."""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.is_running = False
        self.watchers = []
    
    def start(self) -> None:
        """Start monitoring conversations."""
        watch_paths = self.config.get('monitoring.watch_paths', [])
        for path in watch_paths:
            watcher = self.create_watcher(path)
            self.watchers.append(watcher)
        self.is_running = True
    
    def stop(self) -> None:
        """Stop monitoring."""
        for watcher in self.watchers:
            watcher.stop()
        self.watchers.clear()
        self.is_running = False
    
    def get_conversations(self, project: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get conversations from database."""
        from src.database import get_conversations
        return get_conversations(project)
    
    def create_watcher(self, path: str):
        """Create a file system watcher."""
        from src.utils.watcher import FileWatcher
        return FileWatcher(path, self.on_file_change)
    
    def on_file_change(self, event):
        """Handle file change events."""
        # Process conversation file changes
        pass
```

#### Documentation Integration
```python
# src/cli/help.py
HELP_TEXT = """
CCMonitor - Claude Conversation Monitor

USAGE:
    ccmonitor [OPTIONS] [COMMAND]

MODES:
    TUI Mode (default):
        ccmonitor                    # Launch interactive TUI
        ccmonitor --tui              # Explicitly request TUI
        ccmonitor tui --theme dark   # Launch with specific theme
    
    CLI Mode:
        ccmonitor --no-tui           # Show CLI help
        ccmonitor parse FILE         # Parse conversation file
        ccmonitor monitor -f         # Monitor in follow mode
        ccmonitor stats              # Show statistics

OPTIONS:
    --tui/--no-tui      Launch TUI or CLI mode
    --config PATH       Configuration file path
    --verbose, -v       Increase verbosity
    --quiet, -q         Suppress output
    --version          Show version and exit
    --help             Show this help message

COMMANDS:
    parse      Parse conversation files
    monitor    Monitor conversations (CLI mode)
    stats      Show conversation statistics
    config     Manage configuration
    tui        Launch TUI with options

EXAMPLES:
    # Launch TUI interface
    ccmonitor
    
    # Parse a conversation file (CLI)
    ccmonitor parse conversation.json -o parsed.yaml
    
    # Monitor in CLI follow mode
    ccmonitor monitor --tail
    
    # Show last 30 days of statistics
    ccmonitor stats --days 30
    
    # Launch TUI with light theme
    ccmonitor tui --theme light
    
    # Use custom configuration
    ccmonitor --config ~/.myconfig.yaml

CONFIGURATION:
    Config file: ~/.config/ccmonitor/config.yaml
    
    The configuration file controls both CLI and TUI behavior.
    See documentation for configuration options.

ENVIRONMENT VARIABLES:
    CCMONITOR_NO_TUI    Disable TUI mode
    CCMONITOR_CONFIG    Configuration file path
    CCMONITOR_THEME     Default TUI theme

For more information, visit: https://github.com/yourusername/ccmonitor
"""

def show_help():
    """Display comprehensive help."""
    print(HELP_TEXT)
```

#### Backward Compatibility Tests
```python
# tests/test_cli_compatibility.py
import pytest
from click.testing import CliRunner
from src.cli.main import cli

class TestCLICompatibility:
    """Test CLI backward compatibility."""
    
    def test_existing_parse_command(self):
        """Test parse command still works."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create test file
            with open('test.json', 'w') as f:
                f.write('{"test": "data"}')
            
            result = runner.invoke(cli, ['parse', 'test.json'])
            assert result.exit_code == 0
    
    def test_existing_monitor_command(self):
        """Test monitor command still works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['monitor', '--help'])
        assert result.exit_code == 0
        assert 'monitor' in result.output.lower()
    
    def test_no_tui_flag(self):
        """Test --no-tui shows CLI help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--no-tui'])
        assert result.exit_code == 0
        assert 'CCMonitor' in result.output
    
    def test_config_shared(self):
        """Test configuration is shared between modes."""
        from src.config.manager import ConfigManager
        
        config = ConfigManager()
        config.set('test.value', 'shared')
        config.save_config()
        
        # Load in different instance
        config2 = ConfigManager()
        assert config2.get('test.value') == 'shared'
```

### Gotchas and Considerations
- **Import Order**: TUI imports must be conditional to avoid forcing dependencies
- **Exit Codes**: Maintain consistent exit codes across modes
- **Signal Handling**: Handle Ctrl+C gracefully in both modes
- **Config Migration**: Handle old config formats gracefully
- **Mode Detection**: Terminal detection can be unreliable
- **Pipe Support**: CLI must work when piped

## Implementation Blueprint

### Phase 1: CLI Enhancement (1 hour)
1. Update main CLI entry point
2. Add TUI/CLI mode selection
3. Implement launch_tui function
4. Add TUI-specific options
5. Test mode selection

### Phase 2: Configuration Integration (45 min)
1. Create unified ConfigManager
2. Merge CLI and TUI configs
3. Add config migration logic
4. Test configuration sharing
5. Document config options

### Phase 3: Mode Detection (30 min)
1. Implement ModeDetector
2. Add environment checks
3. Create capability detection
4. Test in various environments
5. Add fallback logic

### Phase 4: Service Layer (45 min)
1. Create shared services
2. Abstract monitoring logic
3. Share database access
4. Test service integration
5. Document service API

### Phase 5: Documentation (30 min)
1. Update help text
2. Add mode examples
3. Document environment variables
4. Create migration guide
5. Update README

### Phase 6: Compatibility Testing (30 min)
1. Test all existing commands
2. Verify no breaking changes
3. Test configuration migration
4. Test in CI/CD environment
5. Document any limitations

## Validation Loop

### Level 0: Test Creation
```python
# tests/test_integration.py
def test_cli_tui_integration():
    """Test CLI and TUI integration."""
    runner = CliRunner()
    
    # Test default launches TUI
    result = runner.invoke(cli, [], catch_exceptions=False)
    # Would launch TUI if in terminal
    
    # Test explicit CLI mode
    result = runner.invoke(cli, ['--no-tui'])
    assert 'CCMonitor' in result.output
    
    # Test CLI commands work
    result = runner.invoke(cli, ['parse', '--help'])
    assert result.exit_code == 0
```

### Level 1: Syntax & Style
```bash
uv run ruff check src/cli/ src/config/
uv run ruff format src/cli/ src/config/
```

### Level 2: Type Checking
```bash
uv run mypy src/cli/ src/config/
```

### Level 3: Integration Testing
```bash
# Test CLI commands
ccmonitor --no-tui
ccmonitor parse --help
ccmonitor monitor --help

# Test TUI launch
ccmonitor --tui

# Test with config
ccmonitor --config test.yaml
```

### Level 4: Manual Testing Checklist
- [ ] All existing CLI commands work
- [ ] TUI launches by default
- [ ] --no-tui flag works
- [ ] Configuration shared between modes
- [ ] Help text shows both modes
- [ ] Examples are clear
- [ ] No breaking changes
- [ ] Mode detection works correctly

## Dependencies
- All TUI PRPs must be complete
- Existing CLI must be functional

## Estimated Effort
4 hours total:
- 1 hour: CLI enhancement
- 45 minutes: Configuration integration
- 30 minutes: Mode detection
- 45 minutes: Service layer
- 30 minutes: Documentation
- 30 minutes: Compatibility testing

## Agent Recommendations
- **python-specialist**: For CLI/TUI integration
- **test-writer**: For compatibility testing
- **documentation-writer**: For help text and examples
- **refactoring-expert**: For service abstraction

## Risk Mitigation
- **Risk**: Breaking existing workflows
  - **Mitigation**: Comprehensive compatibility tests, no default changes
- **Risk**: Forced TUI dependencies
  - **Mitigation**: Conditional imports, optional dependencies
- **Risk**: Configuration conflicts
  - **Mitigation**: Separate namespaces, careful merging
- **Risk**: Mode detection failures
  - **Mitigation**: Multiple detection methods, clear overrides

## Definition of Done
- [ ] CLI commands work unchanged
- [ ] TUI launches appropriately
- [ ] Configuration shared properly
- [ ] Mode selection logic correct
- [ ] Documentation updated
- [ ] All compatibility tests pass
- [ ] No breaking changes introduced
- [ ] Help text comprehensive
- [ ] Examples demonstrate both modes
- [ ] Integration smooth and intuitive