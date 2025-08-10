# PRP: Layout System Implementation

## Goal
Implement the responsive three-panel layout system with proper widget hierarchy, creating the foundation for all UI components with dynamic sizing and professional appearance.

## Why
A well-structured layout system is critical for information organization and user navigation. The three-panel design (sidebar, main content, status) provides optimal space utilization while maintaining clarity and allowing for future feature expansion.

## What
### Requirements
- Implement MainScreen with three-panel structure
- Create Header widget with title and navigation info
- Create Footer widget with status bar and shortcuts
- Implement ProjectsPanel for left sidebar (25% width, 20-40 char bounds)
- Implement LiveFeedPanel for main content area
- Add proper CSS styling for all components
- Ensure responsive behavior across terminal sizes

### Success Criteria
- [ ] Three-panel layout renders correctly
- [ ] Sidebar maintains 25% width with min/max constraints
- [ ] Header shows title and navigation breadcrumbs
- [ ] Footer displays status and keyboard shortcuts
- [ ] All panels have proper borders and spacing
- [ ] Layout adapts to terminal resize events
- [ ] Visual hierarchy is clear and professional

## All Needed Context

### Production-Ready Implementation Patterns

Additional implementation patterns from ContextS for production-quality code:

#### File Structure Best Practices
```
src/tui/
├── app.py              # Main application class
├── screens/            # Screen implementations
│   └── main.py
├── widgets/            # Custom widget implementations  
│   ├── header.py
│   ├── footer.py
│   ├── projects_panel.py
│   └── live_feed_panel.py
└── styles/             # CSS styling
    └── ccmonitor.css
```

#### Error Handling and Robustness
```python
# Error-resilient focus management
def action_focus(self, widget_id: str) -> None:
    """Action to focus a specific widget by ID with error handling."""
    try:
        self.query_one(f"#{widget_id}").focus()
    except Exception as e:
        self.app.bell()  # Audio feedback for failed action
        self.log(f"Failed to focus widget '{widget_id}': {e}")

# Robust initialization
def on_mount(self) -> None:
    """Set initial focus with fallback handling."""
    try:
        self.query_one("#projects-panel").focus()
    except Exception as e:
        self.log(f"Could not set initial focus: {e}")
        self.app.focus_next()  # Fallback to next focusable widget
```

#### Performance Optimization with Background Tasks
```python
from textual import work
import asyncio

class LiveFeedPanel(VerticalScroll):
    @work(exclusive=True, group="feed_updates")
    async def fetch_feed_updates(self) -> None:
        """Fetch updates without blocking the UI."""
        self.add_message("Fetching updates...")
        await asyncio.sleep(0.1)  # Simulate async operation
        self.add_message("Updates fetched successfully!")
```

#### Visual Regression Testing with pytest-textual-snapshot
```python
def test_layout_visual_regression(snap_compare):
    """Test for visual layout regressions."""
    app = TestApp()
    assert snap_compare(app, "main_layout")

def test_responsive_small_screen(snap_compare):
    """Test responsive behavior on small screens."""
    app = TestApp()
    async def resize_terminal(pilot):
        await pilot.app.set_size(80, 25)
        await pilot.pause()
    assert snap_compare(app, "small_screen_layout", run_before=resize_terminal)
```

#### Dynamic Layout Modification
```python
def action_toggle_sidebar(self) -> None:
    """Dynamically toggle sidebar visibility."""
    projects_panel = self.query_one("#projects-panel")
    app_grid = self.query_one("#app-grid")
    
    if projects_panel.display:
        projects_panel.display = False
        app_grid.styles.grid_template_columns = "1fr"
    else:
        projects_panel.display = True  
        app_grid.styles.grid_template_columns = "1fr 3fr"
    self.app.bell()
```

### Comprehensive Textual Framework Documentation

The following comprehensive documentation for Textual framework has been automatically integrated from ContextS to provide complete implementation context:

#### Core Concepts & Layout Foundation

**Widget Composition Patterns:**
Textual encourages using Python's `with` statement for composing widgets. This makes the parent-child relationship explicit and readable, mimicking HTML-like nesting.

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container, Vertical, Horizontal, VerticalScroll

class ContainerShowcaseApp(App):
    CSS_PATH = "container_showcase.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

        # A Horizontal container to divide the main screen into two vertical halves
        with Horizontal(id="main-layout"):
            # Left panel: A VerticalScroll for a list of items
            with VerticalScroll(id="projects-panel"):
                yield Static("[b]Projects[/b]", classes="panel-title")
                for i in range(1, 15):
                    yield Static(f"Project {i}", classes="project-item")

            # Right panel: A Vertical container for main content
            with Vertical(id="live-feed-panel"):
                yield Static("[b]Live Feed[/b]", classes="panel-title")
                # Simulate a long feed
                for i in range(1, 30):
                    yield Static(f"Feed Update {i}: Lorem ipsum...", classes="feed-item")
```

**Layout Containers - The Building Blocks:**
- **`Container`**: The most generic container. By default, arranges children vertically and expands to fill available space
- **`Vertical`**: Specialized container that always arranges children vertically. Expands to fill available horizontal space
- **`Horizontal`**: Specialized container that always arranges children horizontally. Expands to fill available vertical space
- **`VerticalScroll` / `HorizontalScroll`**: Like Vertical/Horizontal but automatically add scrollbars if content overflows
- **`Grid`**: The most flexible and powerful layout system, allowing you to define rows and columns like a spreadsheet

#### Responsive Design with Grid Layout

For the three-panel layout, `grid` is the most robust choice. It allows us to define distinct areas for header, footer, sidebar, and main content, and manage their sizing responsively.

```python
class MainScreen(Container):
    """The main screen with a three-panel layout."""
    def compose(self) -> ComposeResult:
        # The main screen itself will be a grid
        # The grid layout is defined in CSS
        yield Header()
        yield Footer()
        yield ProjectsPanel(id="projects-panel")
        yield LiveFeedPanel(id="live-feed-panel")
```

**Grid Layout CSS:**
```css
/* Define the overall screen layout as a grid */
Screen {
    layout: grid;
    /* Define 2 rows: Header (fixed), Main Content (1fr), Footer (fixed) */
    grid-rows: auto 1fr auto;
    /* Define 2 columns: Projects Panel (constrained), Live Feed (1fr) */
    grid-columns: auto 1fr; /* 'auto' for the first column allows it to size based on content/constraints */
    background: $surface;
}

/* Header and Footer are docked, so they span all columns */
Header {
    height: 3;
    dock: top;
    grid-column-span: 2; /* Span both columns of the grid */
}

Footer {
    height: 3;
    dock: bottom;
    grid-column-span: 2; /* Span both columns of the grid */
}

/* Projects Panel (Sidebar) */
#projects-panel {
    grid-row: 2; /* Place in the second row (main content row) */
    grid-column: 1; /* Place in the first column */
    width: auto; /* Allow grid to manage width, but apply constraints below */
    min-width: 20; /* Minimum width of 20 characters */
    max-width: 40; /* Maximum width of 40 characters */
    background: $panel;
    border: round $primary;
    padding: 1;
    overflow-y: auto; /* Enable vertical scrolling */
    margin: 1; /* Add some margin around the panel */
}

/* Live Feed Panel (Main Content) */
#live-feed-panel {
    grid-row: 2; /* Place in the second row (main content row) */
    grid-column: 2; /* Place in the second column */
    width: 1fr; /* Take all remaining horizontal space */
    background: $surface-darken-1;
    border: round $secondary;
    padding: 1;
    overflow-y: auto; /* Enable vertical scrolling */
    margin: 1; /* Add some margin around the panel */
}
```

#### Focus Management and Navigation

**Key Bindings System:**
```python
class ThreePanelApp(App):
    BINDINGS = [
        ("tab", "focus_next", "Focus Next"),
        ("shift+tab", "focus_previous", "Focus Previous"),
        ("ctrl+p", "focus('projects-panel')", "Focus Projects"),
        ("ctrl+f", "focus('live-feed-panel')", "Focus Feed"),
        ("q", "quit", "Quit"),
    ]
    # Set the initial focus to the projects panel
    AUTO_FOCUS = "#projects-panel"
```

**Focus Styling:**
```css
/* General focus style for any focused widget */
:focus {
    border: thick $accent; /* Default focus border */
}

/* Specific focus style for the main panels */
#projects-panel:focus,
#live-feed-panel:focus {
    border: thick $warning; /* Highlight focused panels with a warning color */
}
```

#### Advanced CSS Styling System

**CSS Selectors:**
- **Type Selector**: `Header { ... }` (applies to all Header widgets)
- **ID Selector**: `#projects-panel { ... }` (applies to specific widget with id="projects-panel")
- **Class Selector**: `.panel-title { ... }` (applies to all widgets with classes="panel-title")
- **Descendant Selector**: `#projects-panel Static { ... }` (applies to Static widgets inside #projects-panel)
- **Pseudo-classes**: `:hover`, `:focus`, `:disabled`, `:active`, `:dark`, `:light`

**Critical Layout Properties:**
- **`layout`**: Defines how children are arranged (`vertical`, `horizontal`, `grid`)
- **`dock`**: Positions a widget at an edge (`top`, `bottom`, `left`, `right`)
- **`grid-size`, `grid-columns`, `grid-rows`**: Used with `layout: grid` to define grid structure
- **`align` / `content-align`**: Controls how content is aligned within bounds
- **`1fr` units**: "Fractional units" are key to responsive design. `1fr` means "take 1 fraction of the available space"

#### Performance Optimization

**Background Tasks with `@work`:**
For any long-running operations (network requests, heavy computation), use Textual's `@work` decorator:

```python
from textual.worker import work

@work(thread=True, exclusive=True) # Run in a separate thread, only one at a time
async def action_load_data_worker(self) -> None:
    """Simulates a non-blocking operation using a worker."""
    status_display = self.query_one("#status-display", Static)
    # Update UI from the main thread (call_from_thread)
    self.call_from_thread(status_display.update, "Status: Loading... (Worker)")
    time.sleep(3) # Simulate a long operation in the background thread
    self.call_from_thread(status_display.update, "Status: Data Loaded! (Worker)")
```

**Key Performance Patterns:**
- **`RichLog` for Live Feed**: Optimized for appending new lines efficiently without re-rendering entire content
- **`set_interval`**: Used for periodic updates without blocking the main event loop
- **`overflow-y: auto`**: Ensures scrollbars appear when content exceeds available space
- **Virtual Scrolling**: For large datasets, consider implementing virtual scrolling patterns

#### Dynamic Layout Changes

You can change a widget's layout properties at runtime for adaptive UIs:

```python
def action_toggle_layout(self) -> None:
    """Toggle the layout of the main container between horizontal and vertical."""
    main_container = self.query_one("#main-container")
    if main_container.styles.layout == "horizontal":
        main_container.styles.layout = "vertical"
        self.bell("Switched to Vertical Layout")
    else:
        main_container.styles.layout = "horizontal"
        self.bell("Switched to Horizontal Layout")
```

#### Responsive Behavior Implementation

**Terminal Size Handling:**
```python
async def on_resize(self, event) -> None:
    """Handle terminal resize events."""
    width, height = self.size
    
    # Minimum size check
    if width < 80 or height < 24:
        self.notify("Terminal too small! Min: 80x24", severity="warning")
    
    # Adjust panel widths
    projects_panel = self.query_one("#projects-panel")
    if width < 100:
        projects_panel.styles.width = "20"
    elif width > 150:
        projects_panel.styles.width = "40"
    else:
        projects_panel.styles.width = "25%"
```

#### Production-Ready Best Practices

**Widget Queries and Communication:**
```python
# Getting references to specific widgets
projects_panel = self.query_one("#projects-panel")
all_buttons = self.query_all("Button")

# Widget-to-widget communication
def on_button_pressed(self, event: Button.Pressed) -> None:
    """Handle button presses in the projects panel."""
    self.app.query_one(LiveFeedPanel).write(f"Selected: {event.button.label}")
    # Switch focus to the live feed panel after selection
    self.app.query_one(LiveFeedPanel).focus()
```

**Error Handling and Edge Cases:**
- **Overflow Handling**: `overflow-y: auto` on panels ensures scrollbars appear when content exceeds space
- **`min-width`/`max-width`**: Prevents panels from becoming unusable at extreme terminal sizes
- **Robust Queries**: Using `query_one` and `query_all` helps prevent runtime errors when interacting with widgets

**Common Issues & Solutions:**
1. **Widgets not aligning/sizing correctly**: Add temporary borders (`border: solid red;`) to visualize boundaries
2. **App unresponsive on button clicks**: Use `@work` decorator for long-running operations
3. **CSS not applying**: Check `CSS_PATH`, use `textual run --dev` for live reloading
4. **Data passing between widgets**: Use reactive attributes, messages, or direct queries

### Technical Specifications

#### Main Screen Layout
```python
# src/tui/screens/main.py
from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.binding import Binding

class MainScreen(Screen):
    """Main application screen with three-panel layout."""
    
    DEFAULT_CSS = """
    MainScreen {
        background: $background;
    }
    
    #main-container {
        width: 100%;
        height: 100%;
    }
    
    #content-area {
        width: 100%;
        height: 1fr;
    }
    """
    
    BINDINGS = [
        Binding("tab", "focus_next", "Next Panel"),
        Binding("shift+tab", "focus_previous", "Previous Panel"),
    ]
    
    def compose(self) -> ComposeResult:
        """Compose the main screen layout."""
        from ..widgets.header import Header
        from ..widgets.footer import Footer
        from ..widgets.projects_panel import ProjectsPanel
        from ..widgets.live_feed_panel import LiveFeedPanel
        
        with Vertical(id="main-container"):
            yield Header()
            with Horizontal(id="content-area"):
                yield ProjectsPanel(id="projects-panel")
                yield LiveFeedPanel(id="live-feed-panel")
            yield Footer()
```

#### Header Widget
```python
# src/tui/widgets/header.py
from textual.widgets import Static
from textual.app import ComposeResult
from textual.containers import Horizontal
from datetime import datetime

class Header(Static):
    """Application header with title and status."""
    
    DEFAULT_CSS = """
    Header {
        height: 3;
        background: $primary;
        color: white;
        padding: 0 1;
        dock: top;
    }
    
    .header-title {
        text-style: bold;
        content-align: left middle;
    }
    
    .header-status {
        content-align: right middle;
        color: $secondary;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose header elements."""
        with Horizontal():
            yield Static("🖥️  CCMonitor", classes="header-title")
            yield Static("", id="header-breadcrumb")
            yield Static("", id="header-status", classes="header-status")
    
    def on_mount(self) -> None:
        """Initialize header on mount."""
        self.update_status()
        self.set_interval(1.0, self.update_status)
    
    def update_status(self) -> None:
        """Update status display."""
        status = self.query_one("#header-status", Static)
        time_str = datetime.now().strftime("%H:%M:%S")
        status.update(f"⏰ {time_str}")
```

#### Footer Widget
```python
# src/tui/widgets/footer.py
from textual.widgets import Static
from textual.app import ComposeResult

class Footer(Static):
    """Application footer with shortcuts and status."""
    
    DEFAULT_CSS = """
    Footer {
        height: 1;
        background: $surface;
        color: $secondary;
        dock: bottom;
    }
    
    Footer > .footer-content {
        content-align: center middle;
        text-style: dim;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose footer elements."""
        shortcuts = "Q:Quit  H:Help  P:Pause  F:Filter  Tab:Navigate"
        yield Static(shortcuts, classes="footer-content")
    
    def update_message(self, message: str) -> None:
        """Update footer message temporarily."""
        content = self.query_one(".footer-content", Static)
        content.update(message)
        self.set_timer(3.0, lambda: self.reset_message())
    
    def reset_message(self) -> None:
        """Reset to default shortcuts display."""
        shortcuts = "Q:Quit  H:Help  P:Pause  F:Filter  Tab:Navigate"
        content = self.query_one(".footer-content", Static)
        content.update(shortcuts)
```

#### Projects Panel (Sidebar)
```python
# src/tui/widgets/projects_panel.py
from textual.widget import Widget
from textual.widgets import Static, ListView, ListItem
from textual.app import ComposeResult
from textual.containers import Vertical

class ProjectsPanel(Widget):
    """Left sidebar showing project list and statistics."""
    
    DEFAULT_CSS = """
    ProjectsPanel {
        width: 25%;
        min-width: 20;
        max-width: 40;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    .panel-title {
        text-style: bold;
        color: $primary;
        padding-bottom: 1;
        border-bottom: solid $secondary;
        margin-bottom: 1;
    }
    
    #project-list {
        height: 1fr;
        scrollbar-size: 1 1;
    }
    
    #project-stats {
        height: 5;
        border-top: solid $secondary;
        padding-top: 1;
        margin-top: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose projects panel elements."""
        with Vertical():
            yield Static("📁 Projects", classes="panel-title")
            yield ListView(
                ListItem(Static("🔷 Project Alpha")),
                ListItem(Static("🔶 Project Beta")),
                ListItem(Static("🔵 Project Gamma")),
                id="project-list"
            )
            yield Static(
                "Total: 3 projects\n"
                "Active: 2\n"
                "Messages: 1,234",
                id="project-stats"
            )
```

#### Live Feed Panel (Main Content)
```python
# src/tui/widgets/live_feed_panel.py
from textual.widget import Widget
from textual.widgets import Static, ScrollView, Input
from textual.app import ComposeResult
from textual.containers import Vertical

class LiveFeedPanel(Widget):
    """Main content area for live message feed."""
    
    DEFAULT_CSS = """
    LiveFeedPanel {
        width: 1fr;
        background: $background;
        border: solid $primary;
        padding: 1;
    }
    
    .panel-title {
        text-style: bold;
        color: $primary;
        padding-bottom: 1;
        border-bottom: solid $secondary;
        margin-bottom: 1;
    }
    
    #message-scroll {
        height: 1fr;
        scrollbar-size: 1 1;
        border: solid $secondary;
        padding: 1;
    }
    
    #message-input {
        height: 3;
        margin-top: 1;
        border: solid $primary;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose live feed panel elements."""
        with Vertical():
            yield Static("📨 Live Feed", classes="panel-title")
            
            with ScrollView(id="message-scroll"):
                yield Static(
                    "[10:23:45] 👤 User: How do I implement a parser?\n"
                    "[10:23:47] 🤖 Assistant: I'll help you implement...\n"
                    "[10:23:50] 🔧 Tool: Analyzing code structure...\n",
                    id="message-content"
                )
            
            yield Input(
                placeholder="Filter messages (regex supported)...",
                id="message-input"
            )
```

### CSS Styling System
```css
/* src/tui/styles/ccmonitor.css */

/* Color scheme variables */
$primary: #0066CC;
$secondary: #6C757D;
$success: #28A745;
$warning: #FFC107;
$danger: #DC3545;
$background: #1E1E1E;
$surface: #2D2D30;
$text: #CCCCCC;

/* Message type colors */
.message-user { color: #0066CC; }
.message-assistant { color: #28A745; }
.message-system { color: #FFC107; }
.message-tool { color: #FF6B35; }

/* Layout rules */
Screen {
    layers: base overlay;
    overflow: hidden;
}

/* Panel borders and shadows */
Widget {
    border-title-align: center;
    border-title-style: bold;
}

/* Scrollbar styling */
ScrollView {
    scrollbar-background: $surface;
    scrollbar-color: $primary;
    scrollbar-corner-color: $surface;
}

/* Focus indicators */
*:focus {
    border: solid $warning;
}

/* Responsive breakpoints */
@media (max-width: 100) {
    ProjectsPanel {
        width: 20;
    }
}

@media (max-width: 80) {
    .panel-title {
        text-style: normal;
    }
}
```

### Responsive Behavior
```python
# Terminal size handling
async def on_resize(self, event) -> None:
    """Handle terminal resize events."""
    width, height = self.size
    
    # Minimum size check
    if width < 80 or height < 24:
        self.notify("Terminal too small! Min: 80x24", severity="warning")
    
    # Adjust panel widths
    projects_panel = self.query_one("#projects-panel")
    if width < 100:
        projects_panel.styles.width = "20"
    elif width > 150:
        projects_panel.styles.width = "40"
    else:
        projects_panel.styles.width = "25%"
```

### Gotchas and Considerations
- **CSS Units**: Textual uses its own unit system - percentages and fr units work differently than web CSS
- **Widget Focus**: Only focusable widgets can receive keyboard input
- **Dock vs Grid**: Use dock for fixed position elements, grid for flexible layouts
- **Border Rendering**: Some terminals render borders differently - test across terminals
- **Scrollbar Space**: Account for scrollbar width in layout calculations
- **Update Performance**: Batch updates to avoid flicker

## Implementation Blueprint

### Phase 1: Main Screen Structure (1 hour)
1. Create MainScreen class with layout
2. Implement basic container structure
3. Add focus management bindings
4. Test basic rendering
5. Verify panel arrangement

### Phase 2: Header and Footer (45 min)
1. Create Header widget with status
2. Implement Footer with shortcuts
3. Add update methods for dynamic content
4. Style with CSS
5. Test docking behavior

### Phase 3: Projects Panel (1 hour)
1. Create ProjectsPanel widget
2. Implement ListView for projects
3. Add statistics section
4. Configure width constraints
5. Test scrolling and selection

### Phase 4: Live Feed Panel (1 hour)
1. Create LiveFeedPanel widget
2. Implement ScrollView for messages
3. Add input field for filtering
4. Style message types
5. Test overflow handling

### Phase 5: Responsive Behavior (45 min)
1. Implement resize event handler
2. Add minimum size checks
3. Configure adaptive layouts
4. Test across terminal sizes
5. Add warning notifications

## Validation Loop

### Level 0: Test Creation
```python
# tests/tui/test_layout.py
import pytest
from src.tui.screens.main import MainScreen
from src.tui.widgets.header import Header
from src.tui.widgets.footer import Footer

def test_main_screen_composition():
    """Test main screen creates all components."""
    screen = MainScreen()
    components = list(screen.compose())
    assert any(isinstance(c, Header) for c in components)
    assert any(isinstance(c, Footer) for c in components)

def test_panel_sizing():
    """Test panel width constraints."""
    from src.tui.widgets.projects_panel import ProjectsPanel
    panel = ProjectsPanel()
    css = panel.DEFAULT_CSS
    assert "width: 25%" in css
    assert "min-width: 20" in css
    assert "max-width: 40" in css

@pytest.mark.asyncio
async def test_responsive_resize():
    """Test layout responds to terminal resize."""
    screen = MainScreen()
    # Simulate resize event
    await screen.on_resize(Mock(size=(100, 30)))
    # Verify adjustments
```

### Level 1: Syntax & Style
```bash
uv run ruff check src/tui/screens/ src/tui/widgets/
uv run ruff format src/tui/screens/ src/tui/widgets/
```

### Level 2: Type Checking
```bash
uv run mypy src/tui/screens/ src/tui/widgets/
```

### Level 3: Integration Testing
```python
# tests/tui/test_layout_integration.py
@pytest.mark.asyncio
async def test_complete_layout():
    """Test complete layout renders correctly."""
    from src.tui.app import CCMonitorApp
    app = CCMonitorApp()
    async with app.run_test() as pilot:
        # Verify all panels present
        assert app.query_one("#projects-panel")
        assert app.query_one("#live-feed-panel")
        assert app.query_one(Header)
        assert app.query_one(Footer)
```

### Level 4: Visual Testing
- Launch app and verify three-panel layout
- Test Tab navigation between panels
- Resize terminal and verify adaptation
- Check borders and spacing consistency
- Verify color scheme application

## Dependencies
- PRP 01: Project Setup and Structure (must be complete)
- PRP 02: Application Framework (must be complete)

## Estimated Effort
4.5 hours total:
- 1 hour: Main screen structure
- 45 minutes: Header and footer
- 1 hour: Projects panel
- 1 hour: Live feed panel
- 45 minutes: Responsive behavior

## Agent Recommendations
- **python-specialist**: For Textual widget implementation
- **css-specialist**: For advanced CSS styling and responsive design
- **ui-ux-designer**: For layout optimization and visual hierarchy
- **test-writer**: For comprehensive widget testing

## Risk Mitigation
- **Risk**: CSS parsing failures
  - **Mitigation**: Validate CSS incrementally, use Textual's CSS validator
- **Risk**: Focus management issues
  - **Mitigation**: Test Tab navigation thoroughly, add focus indicators
- **Risk**: Performance with many widgets
  - **Mitigation**: Use virtual scrolling, lazy loading
- **Risk**: Terminal compatibility
  - **Mitigation**: Test on multiple terminals, provide fallbacks

## Definition of Done
- [ ] MainScreen renders three-panel layout
- [ ] Header displays title and status
- [ ] Footer shows shortcuts
- [ ] Projects panel has correct width constraints
- [ ] Live feed panel fills remaining space
- [ ] All widgets styled consistently
- [ ] Layout adapts to terminal resize
- [ ] Tab navigation works between panels
- [ ] All tests pass
- [ ] No visual glitches or rendering issues