# PRP: Core Application Framework

## Goal
Implement the main CCMonitorApp class with Textual framework, establishing the application lifecycle, global key bindings, and screen management system.

## Why
The application framework is the central orchestrator that manages all TUI components, handles user input, and coordinates state changes. A robust framework ensures smooth user experience and maintainable codebase for future features.

## What
### Requirements
- Implement CCMonitorApp class extending Textual's App
- Configure application metadata (title, version, CSS path)
- Set up global key bindings (quit, help, pause, filter)
- Implement graceful startup and shutdown sequences
- Add application-wide state management
- Create help overlay system

### Success Criteria
- [ ] Application launches without errors
- [ ] All global key bindings respond correctly
- [ ] Help overlay displays comprehensive shortcuts
- [ ] Application shuts down cleanly on quit
- [ ] State persists across screen transitions
- [ ] CSS styles load and apply correctly

## All Needed Context

### Textual Framework Documentation

The following comprehensive documentation for Textual framework has been automatically integrated from ContextS to provide complete implementation context:

#### Core Application Framework
- **App Class**: The heart of every Textual application, managing lifecycle, screens, events, and overall UI
- **Compose Method**: Defines the initial widget tree using `yield` statements
- **Event Handling**: Declarative system using `on_` prefixed methods and `BINDINGS`
- **CSS Integration**: Embedded or external CSS for styling with `CSS` or `CSS_PATH` class variables

#### Application Lifecycle Management
- **on_mount()**: Called once when app is mounted, ideal for initialization tasks
- **Startup Sequence**: Load configuration → Initialize logging → Check terminal → Load state → Initialize screens → Start monitoring
- **Shutdown Sequence**: Stop monitoring → Save state → Cleanup resources → Exit application
- **Error Handling**: Graceful startup/shutdown with try-catch blocks and proper error messaging

#### Global Key Bindings System
- **BINDINGS Format**: `[(key, action_string, description, show_in_footer)]`
- **Action Methods**: `action_` prefixed methods automatically callable via bindings
- **Key Methods**: `key_` prefixed methods for simple key handling (e.g., `key_space()`)
- **Event Precedence**: `key_` methods > `BINDINGS` > generic `on_key`
- **Footer Integration**: Automatically displays binding descriptions in Footer widget

#### Screen Management Architecture
- **Screen Definition**: Subclass `textual.screen.Screen` with own `compose` method
- **Static Registration**: `SCREENS = {"name": ScreenClass}` dictionary for pre-defined screens
- **Dynamic Installation**: `install_screen(instance, name)` for runtime screen creation
- **Navigation**: `push_screen()` adds to stack, `pop_screen()` returns to previous
- **Screen-Specific CSS**: Each screen can define unique styling and layout

#### State Management with Reactivity
- **Reactive Variables**: `var()` decorator creates reactive attributes that trigger `watch_` methods
- **Watch Methods**: `watch_<variable_name>()` automatically called on state changes
- **Global State**: App-level reactive variables accessible across all screens
- **State Persistence**: JSON-based state saving/loading with error handling for corrupted files

#### Help Overlay Implementation
- **Automatic Help**: Footer widget displays BINDINGS descriptions automatically
- **Custom Help Screen**: Dedicated screen using Markdown widget for comprehensive help
- **Rich Text Support**: Markdown enables headers, lists, bold/italic, and structured content
- **Navigation Integration**: Help screen accessible via global `h` key binding

#### Performance Optimization
- **Worker Threads**: `@work` decorator for long-running tasks to prevent UI blocking
- **Exclusive Tasks**: `@work(exclusive=True)` ensures single task execution
- **Async Patterns**: Proper async/await usage throughout application lifecycle
- **Resource Cleanup**: Systematic cleanup in shutdown sequence

#### CSS Layout System
- **Grid Layout**: `layout: grid` with `grid-size`, `grid-columns`, `grid-rows`
- **Dock System**: `dock: top/bottom/left/right` for fixed positioning
- **Flexbox**: `1fr` fractional units for flexible space distribution
- **Containers**: `Container`, `VerticalScroll`, `HorizontalScroll` for content organization
- **Responsive Design**: Percentage-based and fractional sizing for terminal adaptability

#### Error Handling Patterns
- **Startup Validation**: Terminal capability checking, environment validation
- **Input Validation**: Custom validators for form inputs with user feedback
- **Exception Hierarchy**: Custom exception classes for different error types
- **User Notifications**: `notify()` method for success/warning/error messages
- **Graceful Degradation**: Fallback modes for terminal incompatibility

#### Development Tools
- **Debug Mode**: `textual run --dev` enables developer tools and DOM inspector
- **Key Debugging**: `textual-keys` utility for understanding key interpretation
- **Console Logging**: `self.log()` for runtime debugging information
- **CSS Inspector**: Real-time style inspection and debugging

### Technical Specifications
```python
# src/tui/app.py
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from pathlib import Path
import sys

class CCMonitorApp(App):
    """Main TUI application for CCMonitor."""
    
    # Application metadata
    TITLE = "CCMonitor - Multi-Project Monitoring"
    SUB_TITLE = "Real-time Claude conversation tracker"
    VERSION = "0.1.0"
    
    # CSS configuration
    CSS_PATH = "styles/ccmonitor.css"
    
    # Global key bindings
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("ctrl+c", "quit", "Quit", priority=True, show=False),
        Binding("h", "toggle_help", "Help"),
        Binding("p", "toggle_pause", "Pause/Resume"),
        Binding("f", "show_filter", "Filter"),
        Binding("r", "refresh", "Refresh", show=False),
        Binding("d", "toggle_dark", "Dark Mode", show=False),
    ]
    
    # Application state
    def __init__(self):
        super().__init__()
        self.is_paused = False
        self.dark_mode = True
        self.projects = []
        self.active_project = None
        
    async def on_mount(self) -> None:
        """Called when app is mounted to the terminal."""
        await self.load_configuration()
        await self.initialize_screens()
        
    def compose(self) -> ComposeResult:
        """Create the application layout."""
        from .screens.main import MainScreen
        yield MainScreen()
```

### Screen Management System
```python
# src/tui/screens/__init__.py
from textual.screen import Screen
from textual.app import ComposeResult

class BaseScreen(Screen):
    """Base class for all screens."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_instance = None
        
    async def on_screen_mount(self) -> None:
        """Called when screen is mounted."""
        self.app_instance = self.app
        await self.initialize()
        
    async def initialize(self) -> None:
        """Override in subclasses for initialization."""
        pass
```

### Help Overlay Implementation
```python
# src/tui/widgets/help_overlay.py
from textual.containers import Container
from textual.widgets import Static
from rich.table import Table

class HelpOverlay(Container):
    """Modal overlay showing keyboard shortcuts."""
    
    DEFAULT_CSS = """
    HelpOverlay {
        layer: overlay;
        background: $surface 90%;
        border: solid $primary;
        padding: 1 2;
        width: 60;
        height: 20;
        align: center middle;
    }
    """
    
    def compose(self) -> ComposeResult:
        table = Table(title="Keyboard Shortcuts")
        table.add_column("Key", style="cyan")
        table.add_column("Action", style="white")
        
        shortcuts = [
            ("Q", "Quit application"),
            ("H", "Toggle this help"),
            ("P", "Pause/Resume monitoring"),
            ("F", "Open filter dialog"),
            ("Tab", "Navigate between panels"),
            ("↑↓", "Navigate within panel"),
            ("Enter", "Select item"),
            ("Esc", "Cancel/Back"),
        ]
        
        for key, action in shortcuts:
            table.add_row(key, action)
            
        yield Static(table)
```

### Application Lifecycle Management
```python
# Startup sequence
async def on_mount(self) -> None:
    """Application startup sequence."""
    try:
        # 1. Load configuration
        await self.load_configuration()
        
        # 2. Initialize logging
        self.setup_logging()
        
        # 3. Check terminal capabilities
        await self.check_terminal()
        
        # 4. Load saved state
        await self.load_state()
        
        # 5. Initialize screens
        await self.initialize_screens()
        
        # 6. Start monitoring (if not paused)
        if not self.is_paused:
            await self.start_monitoring()
            
    except Exception as e:
        self.exit(message=f"Startup failed: {e}")

# Shutdown sequence  
async def action_quit(self) -> None:
    """Graceful shutdown sequence."""
    try:
        # 1. Stop monitoring
        await self.stop_monitoring()
        
        # 2. Save application state
        await self.save_state()
        
        # 3. Cleanup resources
        await self.cleanup()
        
        # 4. Exit application
        self.exit()
        
    except Exception as e:
        self.exit(message=f"Shutdown error: {e}")
```

### State Management
```python
# src/tui/utils/state.py
from pathlib import Path
import json

class AppState:
    """Manages persistent application state."""
    
    STATE_FILE = Path.home() / ".config" / "ccmonitor" / "state.json"
    
    def __init__(self):
        self.state = {
            "dark_mode": True,
            "is_paused": False,
            "active_project": None,
            "filter_settings": {},
            "window_size": None,
        }
    
    async def load(self) -> dict:
        """Load saved state from disk."""
        if self.STATE_FILE.exists():
            with open(self.STATE_FILE) as f:
                self.state.update(json.load(f))
        return self.state
    
    async def save(self) -> None:
        """Save current state to disk."""
        self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
```

### Gotchas and Considerations
- **Async Context**: All Textual methods are async - use await properly
- **Screen Stack**: Pushing/popping screens must be done carefully to avoid stack corruption
- **Event Loop**: Don't block the event loop with synchronous I/O
- **CSS Path**: Relative to the Python file, not working directory
- **Terminal Detection**: Some terminals don't support all Textual features
- **State Persistence**: Handle missing/corrupted state files gracefully

## Implementation Blueprint

### Phase 1: Basic App Structure (1 hour)
1. Create CCMonitorApp class with metadata
2. Implement basic compose() method
3. Add global key bindings
4. Create minimal main screen placeholder
5. Test basic launch and quit

### Phase 2: Screen Management (1 hour)
1. Implement BaseScreen class
2. Create screen navigation methods
3. Add screen stack management
4. Implement screen transition animations
5. Test screen switching

### Phase 3: Help System (45 min)
1. Create HelpOverlay widget
2. Implement toggle_help action
3. Style help overlay with CSS
4. Add comprehensive shortcut list
5. Test overlay display/hide

### Phase 4: State Management (45 min)
1. Create AppState class
2. Implement load/save methods
3. Integrate with app lifecycle
4. Add error handling for corrupted state
5. Test state persistence

### Phase 5: Lifecycle Management (30 min)
1. Implement startup sequence
2. Add shutdown sequence
3. Handle errors gracefully
4. Add logging throughout
5. Test various failure scenarios

## Validation Loop

### Level 0: Test Creation
```python
# tests/tui/test_app.py
import pytest
from src.tui.app import CCMonitorApp

@pytest.mark.asyncio
async def test_app_creation():
    """Test app can be instantiated."""
    app = CCMonitorApp()
    assert app.TITLE == "CCMonitor - Multi-Project Monitoring"
    assert app.VERSION == "0.1.0"

@pytest.mark.asyncio
async def test_key_bindings():
    """Test all key bindings are registered."""
    app = CCMonitorApp()
    bindings = {b.key for b in app.BINDINGS}
    assert "q" in bindings
    assert "h" in bindings
    assert "p" in bindings

@pytest.mark.asyncio
async def test_state_management():
    """Test state can be saved and loaded."""
    from src.tui.utils.state import AppState
    state = AppState()
    state.state["test_value"] = "test"
    await state.save()
    
    new_state = AppState()
    loaded = await new_state.load()
    assert loaded["test_value"] == "test"
```

### Level 1: Syntax & Style
```bash
uv run ruff check src/tui/app.py src/tui/screens/ src/tui/utils/
uv run ruff format src/tui/app.py src/tui/screens/ src/tui/utils/
```

### Level 2: Type Checking
```bash
uv run mypy src/tui/app.py src/tui/screens/ src/tui/utils/
```

### Level 3: Integration Testing
```python
# tests/tui/test_app_integration.py
@pytest.mark.asyncio
async def test_app_lifecycle():
    """Test complete app lifecycle."""
    app = CCMonitorApp()
    
    # Simulate mount
    await app.on_mount()
    assert app.is_mounted
    
    # Test action
    await app.action_toggle_pause()
    assert app.is_paused
    
    # Simulate quit
    await app.action_quit()
```

### Level 4: Manual Testing
- Launch app with `ccmonitor`
- Press 'h' to show help overlay
- Press 'p' to pause/resume
- Press 'q' to quit
- Verify state persists across launches

## Dependencies
- PRP 01: Project Setup and Structure (must be complete)

## Estimated Effort
4 hours total:
- 1 hour: Basic app structure
- 1 hour: Screen management
- 45 minutes: Help system
- 45 minutes: State management
- 30 minutes: Lifecycle management

## Agent Recommendations
- **python-specialist**: For async patterns and Textual framework usage
- **test-writer**: For comprehensive async test creation
- **ui-ux-designer**: For help overlay and user interaction patterns

## Risk Mitigation
- **Risk**: Terminal incompatibility
  - **Mitigation**: Add capability detection and fallback modes
- **Risk**: State file corruption
  - **Mitigation**: Validate JSON, provide reset option
- **Risk**: Screen stack corruption
  - **Mitigation**: Implement stack guards and validation
- **Risk**: Event loop blocking
  - **Mitigation**: Use async I/O throughout, add timeouts

## Definition of Done
- [ ] CCMonitorApp class fully implemented
- [ ] All key bindings functional
- [ ] Help overlay displays correctly
- [ ] State persists between sessions
- [ ] Startup/shutdown sequences work smoothly
- [ ] All tests pass (unit, integration, manual)
- [ ] No type errors or lint violations
- [ ] CSS styles apply correctly
- [ ] Application handles errors gracefully