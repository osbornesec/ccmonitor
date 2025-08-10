# PRP: Error Handling and Compatibility System

## Goal
Implement comprehensive error handling with graceful degradation, terminal compatibility checks, fallback modes, and detailed logging for debugging TUI-specific issues.

## Why
Robust error handling ensures the application remains usable even when issues occur. Terminal environments vary significantly, and the application must handle edge cases gracefully while providing clear feedback to users and developers.

## What
### Requirements
- Implement graceful startup failure handling
- Add terminal compatibility checks
- Create fallback modes for limited terminals
- Implement comprehensive error logging
- Add recovery mechanisms for common failures
- Create user-friendly error messages
- Implement crash reporting and diagnostics

### Success Criteria
- [ ] Application handles startup failures gracefully
- [ ] Terminal incompatibilities detected and handled
- [ ] Fallback modes activate automatically when needed
- [ ] Errors logged with sufficient detail for debugging
- [ ] Users receive clear, actionable error messages
- [ ] Application recovers from transient errors
- [ ] No uncaught exceptions reach the user

## All Needed Context

### Technical Specifications

#### Error Handling Architecture
```python
# src/tui/exceptions.py (enhanced)
import traceback
import sys
from typing import Optional, Any, Dict
from datetime import datetime
from pathlib import Path
import json

class TUIError(Exception):
    """Base exception for TUI-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging."""
        return {
            'type': self.__class__.__name__,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'traceback': self.traceback,
        }

class StartupError(TUIError):
    """Raised when application fails to start."""
    pass

class TerminalError(TUIError):
    """Raised when terminal is incompatible or inadequate."""
    pass

class RenderingError(TUIError):
    """Raised when widget rendering fails."""
    pass

class NavigationError(TUIError):
    """Raised when navigation encounters issues."""
    pass

class ThemeError(TUIError):
    """Raised when theme loading or switching fails."""
    pass

class ConfigurationError(TUIError):
    """Raised when configuration is invalid or missing."""
    pass

class RecoverableError(TUIError):
    """Base class for errors that can be recovered from."""
    
    def __init__(self, message: str, recovery_action: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.recovery_action = recovery_action
```

#### Error Handler System
```python
# src/tui/utils/error_handler.py
from typing import Optional, Callable, Any
from textual.app import App
from textual.widgets import Static
from textual.containers import Container
import logging
import sys

class ErrorHandler:
    """Centralized error handling for the TUI application."""
    
    def __init__(self, app: App):
        self.app = app
        self.error_log: List[TUIError] = []
        self.recovery_strategies: Dict[type, Callable] = {}
        self.setup_logging()
        self.register_recovery_strategies()
    
    def setup_logging(self) -> None:
        """Configure error logging."""
        log_dir = Path.home() / ".config" / "ccmonitor" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"tui_{datetime.now():%Y%m%d_%H%M%S}.log"
        
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stderr),
            ]
        )
        
        self.logger = logging.getLogger("ccmonitor.tui")
    
    def register_recovery_strategies(self) -> None:
        """Register automatic recovery strategies for known errors."""
        self.recovery_strategies = {
            TerminalError: self.recover_from_terminal_error,
            RenderingError: self.recover_from_rendering_error,
            ThemeError: self.recover_from_theme_error,
            ConfigurationError: self.recover_from_config_error,
        }
    
    def handle_error(self, error: Exception) -> bool:
        """Handle an error, attempting recovery if possible."""
        # Log the error
        self.log_error(error)
        
        # Check if it's a TUI error
        if not isinstance(error, TUIError):
            error = TUIError(
                f"Unexpected error: {str(error)}",
                details={'original_type': type(error).__name__}
            )
        
        # Add to error history
        self.error_log.append(error)
        
        # Attempt recovery
        if isinstance(error, RecoverableError):
            return self.attempt_recovery(error)
        
        # Show error to user
        self.show_error_dialog(error)
        
        # Fatal errors
        if isinstance(error, (StartupError, TerminalError)):
            self.handle_fatal_error(error)
            return False
        
        return True
    
    def attempt_recovery(self, error: RecoverableError) -> bool:
        """Attempt to recover from a recoverable error."""
        error_type = type(error)
        
        if error_type in self.recovery_strategies:
            try:
                self.recovery_strategies[error_type](error)
                self.logger.info(f"Recovered from {error_type.__name__}")
                return True
            except Exception as recovery_error:
                self.logger.error(f"Recovery failed: {recovery_error}")
                return False
        
        return False
    
    def recover_from_terminal_error(self, error: TerminalError) -> None:
        """Recover from terminal compatibility issues."""
        # Switch to fallback mode
        self.app.enter_fallback_mode()
        self.app.notify(
            "Terminal compatibility issue detected. "
            "Switched to fallback mode.",
            severity="warning"
        )
    
    def recover_from_rendering_error(self, error: RenderingError) -> None:
        """Recover from rendering errors."""
        # Refresh the screen
        self.app.refresh()
        # Reduce visual complexity if needed
        if len(self.error_log) > 3:
            self.app.reduce_visual_complexity()
    
    def recover_from_theme_error(self, error: ThemeError) -> None:
        """Recover from theme loading errors."""
        # Reset to default theme
        self.app.theme_manager.apply_theme('dark')
        self.app.notify(
            "Theme loading failed. Reverted to default theme.",
            severity="warning"
        )
    
    def recover_from_config_error(self, error: ConfigurationError) -> None:
        """Recover from configuration errors."""
        # Use default configuration
        self.app.load_default_config()
        self.app.notify(
            "Configuration error. Using default settings.",
            severity="warning"
        )
    
    def show_error_dialog(self, error: TUIError) -> None:
        """Display error dialog to user."""
        from ..widgets.error_dialog import ErrorDialog
        dialog = ErrorDialog(error)
        self.app.push_screen(dialog)
    
    def handle_fatal_error(self, error: TUIError) -> None:
        """Handle fatal errors that prevent continuation."""
        # Save crash report
        self.save_crash_report(error)
        
        # Show final error message
        print(f"\n{'='*60}")
        print("FATAL ERROR")
        print('='*60)
        print(f"Error: {error.message}")
        if error.details:
            print(f"Details: {error.details}")
        print(f"\nCrash report saved to: {self.get_crash_report_path()}")
        print("Please report this issue with the crash report.")
        print('='*60)
        
        # Exit application
        sys.exit(1)
    
    def save_crash_report(self, error: TUIError) -> Path:
        """Save detailed crash report for debugging."""
        crash_dir = Path.home() / ".config" / "ccmonitor" / "crash_reports"
        crash_dir.mkdir(parents=True, exist_ok=True)
        
        crash_file = crash_dir / f"crash_{datetime.now():%Y%m%d_%H%M%S}.json"
        
        report = {
            'error': error.to_dict(),
            'system_info': self.gather_system_info(),
            'error_history': [e.to_dict() for e in self.error_log[-10:]],
            'app_state': self.app.get_state_snapshot(),
        }
        
        with open(crash_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return crash_file
    
    def gather_system_info(self) -> Dict[str, Any]:
        """Gather system information for debugging."""
        import platform
        import os
        
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'terminal': os.environ.get('TERM', 'unknown'),
            'terminal_size': self.app.size,
            'color_support': os.environ.get('COLORTERM', 'unknown'),
            'encoding': sys.stdout.encoding,
        }
```

#### Startup Validation
```python
# src/tui/utils/startup.py
from typing import Tuple, Optional
import sys
import os
from pathlib import Path

class StartupValidator:
    """Validates environment before starting TUI."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """Perform all startup validations."""
        checks = [
            self.check_terminal_exists,
            self.check_terminal_size,
            self.check_color_support,
            self.check_unicode_support,
            self.check_dependencies,
            self.check_permissions,
            self.check_configuration,
        ]
        
        for check in checks:
            if not check():
                if self.errors:
                    return False, "; ".join(self.errors)
        
        return True, None
    
    def check_terminal_exists(self) -> bool:
        """Check if running in a terminal."""
        if not sys.stdout.isatty():
            self.errors.append("Not running in a terminal. Please run in a terminal emulator.")
            return False
        return True
    
    def check_terminal_size(self) -> bool:
        """Check if terminal is large enough."""
        try:
            import shutil
            cols, rows = shutil.get_terminal_size()
            
            if cols < 80 or rows < 24:
                self.warnings.append(
                    f"Terminal size ({cols}x{rows}) is below recommended minimum (80x24)"
                )
                # Not a fatal error, just a warning
        except:
            self.warnings.append("Could not determine terminal size")
        
        return True
    
    def check_color_support(self) -> bool:
        """Check terminal color capabilities."""
        term = os.environ.get('TERM', '')
        
        if 'dumb' in term:
            self.warnings.append("Terminal does not support colors. Using monochrome mode.")
        
        return True
    
    def check_unicode_support(self) -> bool:
        """Check if terminal supports Unicode."""
        try:
            test_chars = '🖥️ ✓ ⌘'
            test_chars.encode(sys.stdout.encoding or 'utf-8')
        except (UnicodeEncodeError, AttributeError):
            self.warnings.append("Terminal may not support Unicode. Using ASCII fallback.")
        
        return True
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        try:
            import textual
            import rich
        except ImportError as e:
            self.errors.append(f"Missing required dependency: {e}")
            return False
        
        return True
    
    def check_permissions(self) -> bool:
        """Check file system permissions."""
        config_dir = Path.home() / ".config" / "ccmonitor"
        
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            test_file = config_dir / ".test"
            test_file.touch()
            test_file.unlink()
        except PermissionError:
            self.errors.append(f"No write permission to config directory: {config_dir}")
            return False
        except Exception as e:
            self.warnings.append(f"Permission check warning: {e}")
        
        return True
    
    def check_configuration(self) -> bool:
        """Check if configuration is valid."""
        config_file = Path.home() / ".config" / "ccmonitor" / "config.yaml"
        
        if config_file.exists():
            try:
                import yaml
                with open(config_file) as f:
                    yaml.safe_load(f)
            except Exception as e:
                self.warnings.append(f"Configuration file error: {e}. Using defaults.")
        
        return True
```

#### Fallback Mode Implementation
```python
# src/tui/utils/fallback.py
from textual.app import App
from textual.widgets import Static, Button
from textual.containers import Container, Vertical

class FallbackMode:
    """Simplified UI for limited terminals."""
    
    def __init__(self, app: App):
        self.app = app
        self.original_css = app.CSS
    
    def activate(self) -> None:
        """Switch to fallback mode."""
        # Simplify CSS
        self.app.CSS = """
        Screen {
            background: black;
            color: white;
        }
        
        Container {
            border: solid white;
            padding: 1;
        }
        
        Button {
            background: white;
            color: black;
        }
        
        Button:focus {
            background: black;
            color: white;
            border: solid white;
        }
        """
        
        # Replace complex widgets with simple ones
        self.simplify_ui()
        
        # Disable animations
        self.app.animation_level = "none"
        
        # Use ASCII characters only
        self.use_ascii_only()
    
    def simplify_ui(self) -> None:
        """Replace complex UI elements with simple ones."""
        # Remove fancy borders
        for widget in self.app.query("*"):
            if hasattr(widget, 'border'):
                widget.border = "solid"
        
        # Replace icons with ASCII
        self.replace_icons()
        
        # Reduce color usage
        self.reduce_colors()
    
    def replace_icons(self) -> None:
        """Replace Unicode icons with ASCII alternatives."""
        replacements = {
            '🖥️': '[M]',
            '📁': '[F]',
            '📨': '[MSG]',
            '👤': '[U]',
            '🤖': '[A]',
            '⚙️': '[S]',
            '🔧': '[T]',
            '✓': '[OK]',
            '✗': '[X]',
            '⌘': 'Cmd',
            '⏰': 'Time:',
        }
        
        for widget in self.app.query(Static):
            content = widget.renderable
            if isinstance(content, str):
                for unicode_char, ascii_char in replacements.items():
                    content = content.replace(unicode_char, ascii_char)
                widget.update(content)
    
    def reduce_colors(self) -> None:
        """Reduce to basic color scheme."""
        # Use only 8 basic colors
        basic_colors = {
            'black': 0,
            'red': 1,
            'green': 2,
            'yellow': 3,
            'blue': 4,
            'magenta': 5,
            'cyan': 6,
            'white': 7,
        }
        
        # Map complex colors to basic ones
        for widget in self.app.query("*"):
            widget.styles.color = "white"
            widget.styles.background = "black"
    
    def use_ascii_only(self) -> None:
        """Ensure only ASCII characters are used."""
        # Set ASCII-only rendering mode
        self.app.ascii_mode = True
```

#### Error Dialog Widget
```python
# src/tui/widgets/error_dialog.py
from textual.screen import ModalScreen
from textual.widgets import Static, Button
from textual.containers import Container, Vertical, Horizontal
from textual.app import ComposeResult

class ErrorDialog(ModalScreen):
    """Modal dialog for displaying errors."""
    
    DEFAULT_CSS = """
    ErrorDialog {
        align: center middle;
    }
    
    .error-container {
        width: 60;
        min-height: 15;
        max-height: 30;
        background: $surface;
        border: thick $danger;
        padding: 2;
    }
    
    .error-title {
        text-style: bold;
        color: $danger;
        text-align: center;
        margin-bottom: 1;
    }
    
    .error-message {
        margin-bottom: 1;
    }
    
    .error-details {
        border: solid $secondary;
        padding: 1;
        margin-bottom: 1;
        max-height: 10;
        overflow-y: auto;
    }
    
    .error-buttons {
        align: center middle;
        margin-top: 1;
    }
    """
    
    def __init__(self, error: TUIError):
        super().__init__()
        self.error = error
    
    def compose(self) -> ComposeResult:
        """Compose error dialog."""
        with Container(classes="error-container"):
            yield Static("⚠️ Error Occurred", classes="error-title")
            yield Static(self.error.message, classes="error-message")
            
            if self.error.details:
                details_text = "\n".join(
                    f"{k}: {v}" for k, v in self.error.details.items()
                )
                yield Static(details_text, classes="error-details")
            
            with Horizontal(classes="error-buttons"):
                if isinstance(self.error, RecoverableError):
                    yield Button("Try Recovery", id="recover", variant="warning")
                yield Button("Copy Details", id="copy", variant="secondary")
                yield Button("Dismiss", id="dismiss", variant="primary")
    
    def on_button_pressed(self, event) -> None:
        """Handle button presses."""
        if event.button.id == "dismiss":
            self.app.pop_screen()
        elif event.button.id == "recover":
            if self.app.error_handler.attempt_recovery(self.error):
                self.app.pop_screen()
                self.app.notify("Recovery successful", severity="success")
            else:
                self.app.notify("Recovery failed", severity="error")
        elif event.button.id == "copy":
            import pyperclip
            pyperclip.copy(str(self.error.to_dict()))
            self.app.notify("Error details copied to clipboard")
```

### Gotchas and Considerations
- **Exception Context**: Preserve full stack traces for debugging
- **Async Error Handling**: Handle errors in async contexts properly
- **Terminal State**: Terminal may be in inconsistent state after error
- **Logging Performance**: Don't let logging slow down the app
- **User Privacy**: Don't log sensitive information
- **Recovery Loops**: Prevent infinite recovery attempts

## Implementation Blueprint

### Phase 1: Error Architecture (1 hour)
1. Create enhanced exception hierarchy
2. Implement error handler system
3. Add logging configuration
4. Create error history tracking
5. Test basic error handling

### Phase 2: Startup Validation (45 min)
1. Create StartupValidator class
2. Implement all validation checks
3. Add warning/error collection
4. Create startup report
5. Test various environments

### Phase 3: Fallback Mode (45 min)
1. Create FallbackMode class
2. Implement UI simplification
3. Add ASCII-only mode
4. Create color reduction
5. Test in limited terminals

### Phase 4: Recovery Mechanisms (45 min)
1. Implement recovery strategies
2. Add automatic recovery attempts
3. Create recovery action system
4. Test recovery scenarios
5. Add recovery metrics

### Phase 5: User Interface (45 min)
1. Create error dialog widget
2. Add error notification system
3. Implement crash reporting
4. Add user feedback options
5. Test error display

## Validation Loop

### Level 0: Test Creation
```python
# tests/tui/test_error_handling.py
import pytest
from src.tui.exceptions import TUIError, RecoverableError
from src.tui.utils.error_handler import ErrorHandler

def test_error_logging():
    """Test errors are logged correctly."""
    handler = ErrorHandler(mock_app)
    error = TUIError("Test error", details={'code': 123})
    handler.handle_error(error)
    assert error in handler.error_log

def test_recovery_attempt():
    """Test recovery mechanism."""
    handler = ErrorHandler(mock_app)
    error = RecoverableError("Test", recovery_action="restart")
    result = handler.attempt_recovery(error)
    # Verify recovery attempted

def test_startup_validation():
    """Test startup checks."""
    from src.tui.utils.startup import StartupValidator
    validator = StartupValidator()
    valid, message = validator.validate()
    assert valid or message is not None

def test_fallback_mode():
    """Test fallback mode activation."""
    from src.tui.utils.fallback import FallbackMode
    fallback = FallbackMode(mock_app)
    fallback.activate()
    assert mock_app.animation_level == "none"
```

### Level 1: Syntax & Style
```bash
uv run ruff check src/tui/exceptions.py src/tui/utils/
uv run ruff format src/tui/exceptions.py src/tui/utils/
```

### Level 2: Type Checking
```bash
uv run mypy src/tui/exceptions.py src/tui/utils/
```

### Level 3: Integration Testing
```python
# tests/tui/test_error_integration.py
@pytest.mark.asyncio
async def test_error_recovery_flow():
    """Test complete error recovery flow."""
    from src.tui.app import CCMonitorApp
    app = CCMonitorApp()
    
    # Simulate error
    error = ThemeError("Theme not found")
    app.error_handler.handle_error(error)
    
    # Verify recovery
    assert app.theme_manager.current_theme == 'dark'
```

### Level 4: Failure Scenario Testing
- [ ] Test with no terminal (pipe to file)
- [ ] Test with tiny terminal (40x10)
- [ ] Test with no color support
- [ ] Test with no Unicode support
- [ ] Test with missing config file
- [ ] Test with corrupted state file
- [ ] Test crash report generation
- [ ] Test recovery mechanisms

## Dependencies
- PRP 01: Project Setup and Structure (must be complete)
- PRP 02: Application Framework (must be complete)

## Estimated Effort
4 hours total:
- 1 hour: Error architecture
- 45 minutes: Startup validation
- 45 minutes: Fallback mode
- 45 minutes: Recovery mechanisms
- 45 minutes: User interface

## Agent Recommendations
- **python-specialist**: For exception handling and error architecture
- **logging-specialist**: For comprehensive logging setup
- **test-writer**: For failure scenario testing
- **ui-ux-designer**: For error dialog design

## Risk Mitigation
- **Risk**: Error handler crashes
  - **Mitigation**: Wrap error handler in try/except, have fallback
- **Risk**: Infinite recovery loops
  - **Mitigation**: Track recovery attempts, set limits
- **Risk**: Log file grows too large
  - **Mitigation**: Implement log rotation, size limits
- **Risk**: Sensitive data in crash reports
  - **Mitigation**: Sanitize data before logging

## Definition of Done
- [ ] Complete error handling architecture implemented
- [ ] Startup validation catches all issues
- [ ] Fallback mode works in limited terminals
- [ ] Recovery mechanisms functional
- [ ] Error dialogs display correctly
- [ ] Crash reports generated with useful info
- [ ] All error scenarios tested
- [ ] Logging provides debugging information
- [ ] No uncaught exceptions in normal operation
- [ ] User experience remains smooth despite errors