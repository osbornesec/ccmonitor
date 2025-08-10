# PRP: Project Setup and Structure for TUI Foundation

## Goal
Establish the foundational package structure and configuration for the CCMonitor TUI application, ensuring clean architecture and proper dependency management.

## Why
The current CLI-based structure needs to be extended with a well-organized TUI package that maintains separation of concerns while enabling rich terminal user interface capabilities. Proper setup now prevents technical debt and enables parallel development of components.

## What
### Requirements
- Create `src/tui/` package with proper Python module structure
- Remove unnecessary dependencies (fastapi, uvicorn, scikit-learn, numpy)
- Configure Textual CSS styling system
- Set up base exception classes for TUI-specific errors
- Establish logging configuration for TUI debugging

### Success Criteria
- [ ] TUI package structure follows Python best practices
- [ ] All __init__.py files properly export public interfaces
- [ ] Dependencies cleaned up with no unused packages
- [ ] CSS styling system configured and loadable
- [ ] Base exceptions provide clear error context
- [ ] Logging captures TUI events without cluttering output

## All Needed Context

### Technical Specifications

#### Complete Package Structure
```python
# Recommended Production-Ready Structure
src/
├── tui/
│   ├── __init__.py          # Export CCMonitorApp class
│   ├── app.py               # Main Textual App class
│   ├── config.py            # Configuration management
│   │
│   ├── screens/             # Screen management
│   │   ├── __init__.py
│   │   ├── main_screen.py   # Primary dashboard screen
│   │   ├── help_screen.py   # Help and keybindings
│   │   └── error_screen.py  # Global error handler screen
│   │
│   ├── widgets/             # Custom widget components
│   │   ├── __init__.py
│   │   ├── base.py          # Base widget classes
│   │   ├── header.py        # Application header widget
│   │   ├── footer.py        # Status and shortcuts footer
│   │   ├── projects_panel.py # Project list sidebar
│   │   ├── live_feed_panel.py # Message feed display
│   │   └── loading.py       # Loading indicators
│   │
│   ├── styles/              # CSS styling system
│   │   ├── __init__.py
│   │   └── ccmonitor.tcss   # Main Textual CSS file
│   │
│   ├── utils/               # Utility modules
│   │   ├── __init__.py
│   │   ├── keybindings.py   # Global key binding management
│   │   ├── themes.py        # Color scheme management
│   │   ├── startup.py       # Application startup validation
│   │   └── transitions.py   # UI transition animations
│   │
│   └── exceptions.py        # TUI-specific exception hierarchy
```

### Dependencies to Remove
```toml
# From pyproject.toml, remove:
"fastapi>=0.104.0",      # Web framework not needed for TUI
"uvicorn>=0.24.0",       # ASGI server not needed
"scikit-learn>=1.3.0",   # ML library not needed for monitoring
"numpy>=1.24.0",         # Numerical computing not needed
```

### Dependencies to Keep/Already Added
```toml
"textual>=5.3.0",        # Modern TUI framework (already added)
"rich>=14.1.0",          # Rich text rendering (already added)
```

#### Textual CSS Configuration System
```css
/* src/tui/styles/ccmonitor.tcss */
/* Textual CSS with Theme Variables */

/* Color Variables - Using Textual's built-in theme system */
Screen {
    background: $surface;
    color: $text;
    layout: grid;
    grid-size: 1 3;
    grid-template-rows: auto 1fr auto;
}

/* Header styling with dock positioning */
Header {
    dock: top;
    height: 3;
    background: $primary;
    color: $text;
    content-align: center middle;
    text-style: bold;
}

/* Footer with key binding display */
Footer {
    dock: bottom;
    height: 3;
    background: $primary;
    color: $text;
    content-align: center middle;
}

/* Main layout grid system */
.main-layout {
    layout: grid;
    grid-size: 3 1;
    grid-template-columns: 1fr 3fr;
    grid-gutter: 1;
    height: 1fr;
    background: $panel;
}

/* Project panel sidebar */
.projects-panel {
    width: 25%;
    min-width: 20;
    max-width: 40;
    background: $surface;
    border: round $primary;
    padding: 1;
}

/* Live feed main content area */
.live-feed-panel {
    width: 1fr;
    background: $panel;
    border: round $secondary;
    padding: 1;
    overflow-y: auto;
}

/* Responsive design for small terminals */
@media (max-width: 80) {
    .main-layout {
        grid-template-columns: 1fr;
        grid-size: 1 2;
    }
    .projects-panel {
        width: 100%;
        height: 10;
    }
}

/* Loading and transition animations */
@keyframes fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
}

.fade-in {
    animation: fade-in 0.3s ease-in;
}

/* Focus states for accessibility */
*:focus {
    border: thick $warning;
    box-shadow: 0 0 0 1px $warning;
}
```

#### Enhanced Exception Hierarchy
```python
# src/tui/exceptions.py
"""TUI-specific exception hierarchy with contextual error handling."""

import traceback
from typing import Optional, Dict, Any
from datetime import datetime


class TUIError(Exception):
    """Base exception for TUI-related errors with contextual information."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.user_message = user_message or message
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging."""
        return {
            'type': self.__class__.__name__,
            'message': self.message,
            'user_message': self.user_message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'traceback': self.traceback,
        }


class StartupError(TUIError):
    """Raised when application fails to start properly."""
    pass


class TerminalError(TUIError):
    """Raised when terminal capabilities are inadequate."""
    
    def __init__(self, message: str, terminal_info: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.terminal_info = terminal_info or {}


class RenderingError(TUIError):
    """Raised when widget rendering encounters issues."""
    
    def __init__(self, widget_id: str, render_stage: str, **kwargs):
        message = f"Rendering failed for widget '{widget_id}' at stage '{render_stage}'"
        super().__init__(message, **kwargs)
        self.widget_id = widget_id
        self.render_stage = render_stage


class NavigationError(TUIError):
    """Raised when screen/widget navigation fails."""
    
    def __init__(self, from_screen: str, to_screen: str, **kwargs):
        message = f"Navigation failed from '{from_screen}' to '{to_screen}'"
        super().__init__(message, **kwargs)
        self.from_screen = from_screen
        self.to_screen = to_screen


class ConfigurationError(TUIError):
    """Raised when configuration is invalid or missing."""
    pass


class ThemeError(TUIError):
    """Raised when theme loading or application fails."""
    
    def __init__(self, theme_name: str, **kwargs):
        message = f"Theme '{theme_name}' could not be loaded or applied"
        super().__init__(message, **kwargs)
        self.theme_name = theme_name


class RecoverableError(TUIError):
    """Base for errors that allow automatic recovery."""
    
    def __init__(self, message: str, recovery_action: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.recovery_action = recovery_action
```

#### Configuration Management System
```python
# src/tui/config.py
"""Centralized configuration management for the TUI application."""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import yaml


@dataclass
class TUIConfig:
    """Configuration settings for the TUI application."""
    
    # Application metadata
    app_name: str = "CCMonitor"
    app_version: str = "0.1.0"
    
    # UI settings
    default_theme: str = "dark"
    animation_level: str = "full"  # "full", "reduced", "none"
    auto_refresh_interval: float = 1.0
    
    # Terminal settings
    min_terminal_width: int = 80
    min_terminal_height: int = 24
    enable_mouse: bool = True
    enable_unicode: bool = True
    
    # Performance settings
    max_history_lines: int = 1000
    batch_update_threshold: int = 10
    async_worker_threads: int = 4
    
    # Logging configuration
    log_level: str = "INFO"
    log_file: Optional[str] = None
    log_to_console: bool = False
    
    # Feature flags
    enable_help_overlay: bool = True
    enable_command_palette: bool = True
    enable_shortcuts_footer: bool = True
    
    def __post_init__(self):
        """Set up derived configuration values."""
        if self.log_file is None:
            config_dir = Path.home() / ".config" / "ccmonitor"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = str(config_dir / "tui.log")


def load_config(config_path: Optional[Path] = None) -> TUIConfig:
    """Load configuration from file or create defaults."""
    if config_path is None:
        config_path = Path.home() / ".config" / "ccmonitor" / "tui_config.yaml"
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
            return TUIConfig(**config_data)
        except Exception as e:
            logging.warning(f"Failed to load config from {config_path}: {e}")
    
    return TUIConfig()


def save_config(config: TUIConfig, config_path: Optional[Path] = None) -> None:
    """Save configuration to file."""
    if config_path is None:
        config_path = Path.home() / ".config" / "ccmonitor" / "tui_config.yaml"
    
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    config_dict = {
        field.name: getattr(config, field.name) 
        for field in config.__dataclass_fields__.values()
    }
    
    with open(config_path, 'w') as f:
        yaml.safe_dump(config_dict, f, default_flow_style=False)


# Global configuration instance
_config: Optional[TUIConfig] = None

def get_config() -> TUIConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
```

### Gotchas and Considerations

#### Textual-Specific Patterns
- **Import Order**: App must be imported before widgets to avoid circular imports
- **CSS Path Resolution**: CSS_PATH is relative to the Python file containing the App class
- **Async Context**: All UI updates must happen on the main event loop thread
- **Terminal Capabilities**: Use feature detection and graceful fallbacks for terminal limitations
- **Widget Lifecycle**: Always `await` mount operations before querying widgets

#### Performance Considerations  
- **Batch Updates**: Use `with self.app.batch_update():` for multiple UI changes
- **Worker Threads**: Use `@work` decorator for I/O-bound operations
- **Memory Management**: Limit history size and clean up unused widgets
- **CSS Optimization**: Avoid complex selectors and excessive nesting

#### Development Best Practices
- **Package Exports**: Define `__all__` in `__init__.py` files for clean public APIs
- **Error Handling**: Implement comprehensive error recovery with user feedback
- **Testing Strategy**: Use snapshot testing for UI components
- **Logging**: Separate debug logs from user notifications
- **Configuration**: Externalize settings and provide sensible defaults

## Implementation Blueprint

### Phase 1: Clean Dependencies (30 min)
1. Update pyproject.toml to remove unnecessary packages
2. Run `uv pip sync` to update virtual environment
3. Verify remaining dependencies with `uv pip list`
4. Run existing tests to ensure no breakage

### Phase 2: Create Package Structure (1 hour)
1. Create src/tui/ directory hierarchy
2. Add __init__.py files with proper exports
3. Create placeholder classes in each module
4. Set up exception hierarchy
5. Configure logging for TUI namespace

### Phase 3: CSS Setup (30 min)
1. Create ccmonitor.css with color variables
2. Add panel sizing rules
3. Configure widget-specific styles
4. Test CSS loading in minimal app

### Phase 4: Integration Points (1 hour)
1. Create main App class with proper Screen management
2. Set up configuration system and logging
3. Ensure clean separation between CLI and TUI packages
4. Create startup validation and error handling
5. Test basic application lifecycle

## Validation Loop

### Level 0: Test Creation
```python
# tests/tui/test_structure.py
"""Tests for TUI package structure and basic functionality."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_tui_package_imports():
    """Verify all TUI modules are importable."""
    from src.tui import CCMonitorApp
    from src.tui.config import TUIConfig, get_config
    from src.tui.exceptions import TUIError, StartupError
    
    assert CCMonitorApp is not None
    assert TUIConfig is not None
    assert issubclass(StartupError, TUIError)


def test_css_file_exists():
    """Verify CSS file is present and has valid Textual CSS syntax."""
    css_path = Path("src/tui/styles/ccmonitor.tcss")
    assert css_path.exists(), f"CSS file not found at {css_path}"
    
    content = css_path.read_text()
    assert len(content) > 0, "CSS file is empty"
    
    # Check for essential Textual CSS patterns
    assert "Screen {" in content, "Missing Screen root selector"
    assert "$primary" in content or "$surface" in content, "Missing theme variables"


def test_exception_hierarchy():
    """Verify exception classes are properly structured."""
    from src.tui.exceptions import (
        TUIError, StartupError, TerminalError, 
        RenderingError, NavigationError, RecoverableError
    )
    
    # Test inheritance hierarchy
    assert issubclass(StartupError, TUIError)
    assert issubclass(TerminalError, TUIError)
    assert issubclass(RenderingError, TUIError)
    assert issubclass(NavigationError, TUIError)
    assert issubclass(RecoverableError, TUIError)
    
    # Test enhanced exception features
    error = TUIError("test message", details={"key": "value"})
    error_dict = error.to_dict()
    assert error_dict["message"] == "test message"
    assert error_dict["details"]["key"] == "value"
    assert "timestamp" in error_dict


def test_configuration_system():
    """Test configuration loading and defaults."""
    from src.tui.config import TUIConfig, load_config
    
    # Test default configuration
    config = TUIConfig()
    assert config.app_name == "CCMonitor"
    assert config.default_theme == "dark"
    assert config.min_terminal_width == 80
    
    # Test configuration loading with non-existent file
    config_loaded = load_config(Path("/non/existent/path"))
    assert config_loaded.app_name == "CCMonitor"  # Should use defaults


@pytest.mark.asyncio
async def test_app_basic_lifecycle():
    """Test basic App class lifecycle without full UI."""
    from src.tui.app import CCMonitorApp
    
    app = CCMonitorApp()
    assert app.title is not None
    assert hasattr(app, 'CSS_PATH')
    
    # Test app can be created without errors
    assert app.dark in (True, False)  # Should have a boolean theme state
    

def test_package_structure():
    """Verify the expected package structure exists."""
    base_path = Path("src/tui")
    
    # Check main package files
    assert (base_path / "__init__.py").exists()
    assert (base_path / "app.py").exists()
    assert (base_path / "config.py").exists()
    assert (base_path / "exceptions.py").exists()
    
    # Check subdirectories
    assert (base_path / "screens" / "__init__.py").exists()
    assert (base_path / "widgets" / "__init__.py").exists()
    assert (base_path / "styles" / "__init__.py").exists()
    assert (base_path / "utils" / "__init__.py").exists()
    
    # Check CSS file
    assert (base_path / "styles" / "ccmonitor.tcss").exists()
```

### Level 1: Syntax & Style
```bash
uv run ruff check src/tui/
uv run ruff format src/tui/
```

### Level 2: Type Checking
```bash
uv run mypy src/tui/
```

### Level 3: Integration Testing
```python
# tests/tui/test_integration.py
"""Integration tests for TUI application components."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


@pytest.mark.asyncio
async def test_app_creation_and_mounting():
    """Test that TUI app can be created and mounted properly."""
    from src.tui.app import CCMonitorApp
    
    app = CCMonitorApp()
    
    # Test basic app properties
    assert app.title is not None
    assert hasattr(app, 'CSS_PATH')
    assert hasattr(app, 'BINDINGS')
    assert hasattr(app, 'SCREENS')
    
    # Test CSS path resolution
    css_path = Path(app.CSS_PATH)
    if not css_path.is_absolute():
        # Should resolve relative to app.py
        app_dir = Path(__file__).parent / "../../src/tui"
        full_css_path = app_dir / app.CSS_PATH
        assert full_css_path.exists(), f"CSS file not found: {full_css_path}"


@pytest.mark.asyncio 
async def test_configuration_integration():
    """Test configuration system integrates with app."""
    from src.tui.app import CCMonitorApp
    from src.tui.config import TUIConfig
    
    # Test with custom config
    config = TUIConfig(
        app_name="Test App",
        default_theme="light",
        min_terminal_width=100
    )
    
    with patch('src.tui.config.get_config', return_value=config):
        app = CCMonitorApp()
        # App should use configuration values
        assert hasattr(app, 'config') or config.app_name == "Test App"


def test_exception_handling_integration():
    """Test exception handling integrates properly."""
    from src.tui.exceptions import TUIError, StartupError, ConfigurationError
    
    # Test exception can be created with full context
    try:
        raise StartupError(
            "Test startup failure", 
            details={"terminal_size": "too_small"},
            user_message="Please resize your terminal"
        )
    except StartupError as e:
        assert e.message == "Test startup failure"
        assert e.details["terminal_size"] == "too_small"
        assert e.user_message == "Please resize your terminal"
        assert e.timestamp is not None
        
        # Test serialization
        error_dict = e.to_dict()
        assert error_dict["type"] == "StartupError"
        assert "timestamp" in error_dict


@pytest.mark.asyncio
async def test_screen_registration():
    """Test screen registration and navigation setup."""
    from src.tui.app import CCMonitorApp
    
    app = CCMonitorApp()
    
    # Test screens are registered
    assert hasattr(app, 'SCREENS')
    assert isinstance(app.SCREENS, dict)
    
    # Test key bindings are defined
    assert hasattr(app, 'BINDINGS')
    assert len(app.BINDINGS) > 0
    
    # Each binding should be a tuple with key and action
    for binding in app.BINDINGS:
        assert isinstance(binding, tuple)
        assert len(binding) >= 2  # key, action, optional description
```

### Level 4: Manual Validation
- Verify package structure matches specification
- Confirm no import errors when running `python -c "from src.tui import CCMonitorApp"`
- Check that CSS file loads without parse errors
- Ensure clean separation from CLI code

## Dependencies
None - this is the foundational PRP

## Estimated Effort
3 hours total:
- 30 minutes: Dependency cleanup
- 1 hour: Package structure creation
- 30 minutes: CSS setup
- 1 hour: Integration and testing

#### Implementation Examples

##### Main App Class Structure
```python
# src/tui/app.py
"""Main CCMonitor TUI application using Textual framework."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container

from .config import get_config
from .exceptions import StartupError, ConfigurationError
from .screens.main_screen import MainScreen
from .screens.help_screen import HelpScreen
from .screens.error_screen import ErrorScreen


class CCMonitorApp(App[None]):
    """CCMonitor Terminal User Interface Application."""
    
    # Application metadata
    TITLE = "CCMonitor"
    SUB_TITLE = "Claude Code Conversation Monitor"
    
    # Textual configuration
    CSS_PATH = "styles/ccmonitor.tcss"
    ENABLE_COMMAND_PALETTE = True
    
    # Key bindings
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode"),
        ("h", "show_help", "Show help"),
        ("ctrl+r", "refresh", "Refresh"),
        ("escape", "pop_screen", "Go back"),
    ]
    
    # Screen registry
    SCREENS = {
        "main": MainScreen,
        "help": HelpScreen,
        "error": ErrorScreen,
    }
    
    def __init__(self, **kwargs):
        """Initialize the application with configuration."""
        super().__init__(**kwargs)
        self.config = get_config()
        self.setup_logging()
    
    def setup_logging(self) -> None:
        """Configure application logging."""
        import logging
        
        logging.basicConfig(
            filename=self.config.log_file,
            level=getattr(logging, self.config.log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger("ccmonitor.tui")
        self.logger.info(f"CCMonitor TUI v{self.config.app_version} starting")
    
    def compose(self) -> ComposeResult:
        """Create the initial UI layout."""
        yield Header()
        yield Container(
            Static("Welcome to CCMonitor TUI", id="welcome"),
            Static("Press 'h' for help, 'q' to quit", id="instructions"),
            id="main_container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when the app is mounted and ready."""
        self.dark = self.config.default_theme == "dark"
        self.push_screen("main")
        self.logger.info("Application mounted successfully")
    
    def action_toggle_dark(self) -> None:
        """Toggle between dark and light themes."""
        self.dark = not self.dark
        theme = "dark" if self.dark else "light"
        self.notify(f"Switched to {theme} theme")
        self.logger.debug(f"Theme changed to {theme}")
    
    def action_show_help(self) -> None:
        """Show the help screen."""
        self.push_screen("help")
    
    def action_refresh(self) -> None:
        """Refresh the current view."""
        self.notify("Refreshing...")
        # Implement refresh logic here
    
    def on_exception(self, exception: Exception) -> None:
        """Handle unhandled exceptions gracefully."""
        self.logger.critical(f"Unhandled exception: {exception}", exc_info=True)
        
        if isinstance(exception, (StartupError, ConfigurationError)):
            self.push_screen("error", callback=lambda _: self.exit(1))
        else:
            self.notify(f"Error: {exception}", severity="error")
```

##### Package Init Files
```python
# src/tui/__init__.py
"""CCMonitor Terminal User Interface package."""

from .app import CCMonitorApp
from .config import TUIConfig, get_config
from .exceptions import TUIError, StartupError

__version__ = "0.1.0"
__all__ = [
    "CCMonitorApp",
    "TUIConfig", 
    "get_config",
    "TUIError",
    "StartupError",
]


# src/tui/screens/__init__.py
"""TUI screen components."""

from .main_screen import MainScreen
from .help_screen import HelpScreen
from .error_screen import ErrorScreen

__all__ = [
    "MainScreen",
    "HelpScreen", 
    "ErrorScreen",
]


# src/tui/widgets/__init__.py
"""TUI widget components."""

from .base import BaseWidget
from .header import CCMonitorHeader
from .footer import CCMonitorFooter
from .loading import LoadingIndicator

__all__ = [
    "BaseWidget",
    "CCMonitorHeader",
    "CCMonitorFooter",
    "LoadingIndicator",
]


# src/tui/utils/__init__.py
"""TUI utility modules."""

from .themes import ThemeManager
from .keybindings import KeyBindingManager
from .startup import StartupValidator
from .transitions import TransitionManager

__all__ = [
    "ThemeManager",
    "KeyBindingManager", 
    "StartupValidator",
    "TransitionManager",
]
```

## Agent Recommendations
- **textual-tui-specialist**: For Textual framework implementation and best practices
- **python-specialist**: For package structure and Python architectural patterns
- **test-automation-engineer**: For comprehensive test suite creation with pytest-textual-snapshot
- **config-validation-specialist**: For configuration management and validation systems

## Risk Mitigation
- **Risk**: Breaking existing CLI functionality
  - **Mitigation**: Keep TUI completely separate, test CLI after changes
- **Risk**: CSS parsing errors
  - **Mitigation**: Start with minimal CSS, validate with Textual's parser
- **Risk**: Import cycles
  - **Mitigation**: Use careful import ordering, lazy imports where needed

## Definition of Done
- [ ] All unnecessary dependencies removed from pyproject.toml
- [ ] Complete src/tui/ package structure created
- [ ] All __init__.py files have proper exports
- [ ] CSS file created and validates
- [ ] Exception hierarchy implemented
- [ ] All tests pass (syntax, types, unit, integration)
- [ ] No regression in existing CLI functionality
- [ ] Package can be imported without errors