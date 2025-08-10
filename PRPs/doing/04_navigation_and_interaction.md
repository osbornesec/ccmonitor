# PRP: Navigation and Interaction System

## Goal
Implement comprehensive keyboard navigation with focus management, visual indicators, and context-aware navigation patterns for intuitive user interaction.

## Why
Efficient keyboard navigation is essential for terminal applications. Users expect smooth focus transitions, clear visual feedback, and logical navigation patterns that match standard terminal application conventions.

## What
### Requirements
- Implement Tab/Shift+Tab navigation between panels
- Add arrow key navigation within panels
- Create visual focus indicators (border highlighting)
- Implement ESC key context navigation
- Create keyboard shortcut help overlay
- Add focus trap for modal dialogs
- Implement accelerator keys for common actions

### Success Criteria
- [ ] Tab cycles through all focusable widgets
- [ ] Arrow keys navigate within lists and content
- [ ] Focused elements have clear visual indicators
- [ ] ESC key returns to logical previous context
- [ ] Help overlay shows all available shortcuts
- [ ] Modal dialogs trap focus appropriately
- [ ] Navigation feels intuitive and responsive

## All Needed Context

### Textual Navigation & Interaction Patterns

#### Comprehensive Textual Focus Management Guide

From the official Textual library documentation, focus management follows these key principles:

**Focus Basics:**
- **Implicit Focus**: When an application starts, Textual tries to focus the first focusable widget in the DOM
- **Tab Navigation**: Pressing `Tab` moves focus to the *next* focusable widget in DOM order. `Shift+Tab` moves to the *previous*
- **Programmatic Focus**: Use `widget.focus()` or `app.action_focus()` for explicit control
- **Visual Indicators**: Use the `:focus` CSS pseudo-class for styling focused widgets

**Key Textual Navigation Methods:**
```python
# Built-in focus actions
app.action_focus_next()  # Tab navigation
app.action_focus_previous()  # Shift+Tab navigation
widget.focus()  # Direct focus setting
widget.can_focus = True/False  # Control focusability
```

**Essential CSS for Focus Indicators:**
```css
/* Standard focus styling */
*:focus {
    border: solid $warning;
    border-title-style: bold;
}

/* Panel-specific focus with stronger visual cues */
.panel:focus {
    border: thick $accent;
    background: $surface 95%;
}

/* Focus animation for enhanced visibility */
@keyframes focus-pulse {
    0% { border-color: $warning; }
    50% { border-color: $primary; }
    100% { border-color: $warning; }
}

.focused {
    animation: focus-pulse 2s infinite;
}
```

#### Advanced Focus Groups Pattern

For complex layouts, Textual supports focus groups to control navigation scope:

```python
class MainScreen(Screen):
    BINDINGS = [
        ("tab", "focus_next", "Next Panel"),
        ("ctrl+1", "focus_next(group='sidebar')", "Focus Sidebar"),
        ("ctrl+2", "focus_next(group='content')", "Focus Content"),
    ]
    
    def compose(self) -> ComposeResult:
        with Container(focus_group="sidebar"):
            # Sidebar widgets here
        with Container(focus_group="content"):
            # Content widgets here
```

#### Modal Dialog Best Practices

Textual's `ModalScreen` provides automatic focus trapping:

```python
class ConfirmModal(ModalScreen[bool]):
    BINDINGS = [
        ("escape", "dismiss(False)", "Cancel"),
        ("enter", "confirm", "Confirm"),
    ]
    
    def on_mount(self) -> None:
        # Focus the most important action button
        self.query_one("#confirm_button").focus()
    
    def dismiss(self, result: Any = None) -> None:
        # Automatically returns focus to previous screen
        super().dismiss(result)
```

#### Event Handling Hierarchy

Textual's event system follows a specific priority order:

1. **`key_<keyname>()` methods** - Most specific, highest priority
2. **`BINDINGS` on focused widget** - Widget-specific shortcuts
3. **`BINDINGS` on screen** - Screen-specific shortcuts  
4. **`BINDINGS` on app** - Global shortcuts
5. **`on_key()` methods** - Catch-all handlers

```python
class NavigableWidget(Widget):
    BINDINGS = [
        ("up", "move_up", "Move Up"),
        ("down", "move_down", "Move Down"),
        ("enter", "select", "Select"),
    ]
    
    def key_escape(self) -> None:
        """Highest priority - always handles ESC"""
        self.app.pop_screen()
    
    def on_key(self, event: Key) -> None:
        """Fallback for unhandled keys"""
        if event.key in ("j", "k"):  # Vim-style navigation
            if event.key == "j":
                self.action_move_down()
            elif event.key == "k":
                self.action_move_up()
```

#### Context Navigation with Screen Stack

Textual's screen stack enables intuitive context navigation:

```python
class CCMonitorApp(App):
    SCREENS = {
        "main": MainScreen,
        "settings": SettingsScreen,
        "help": HelpOverlay,
    }
    
    def action_show_help(self) -> None:
        """Push help as modal - ESC returns to previous context"""
        self.push_screen("help")
    
    def action_back(self) -> None:
        """Standard back action - bound to ESC globally"""
        if len(self.screen_stack) > 1:
            self.pop_screen()
        else:
            self.set_focus(None)  # Unfocus if at root
```

### Technical Specifications

#### Focus Management System
```python
# src/tui/utils/focus.py
from textual.widget import Widget
from typing import Optional, List

class FocusManager:
    """Manages focus navigation and visual indicators."""
    
    def __init__(self, app):
        self.app = app
        self.focus_chain: List[Widget] = []
        self.focus_index: int = 0
        self.context_stack: List[Widget] = []
    
    def build_focus_chain(self, screen) -> None:
        """Build the focus chain for current screen."""
        self.focus_chain = []
        
        # Add focusable widgets in logical order
        self.focus_chain.extend(screen.query(".focusable").results())
        
        # Sort by tab order if specified
        self.focus_chain.sort(
            key=lambda w: getattr(w, 'tab_order', 999)
        )
    
    def focus_next(self) -> None:
        """Move focus to next widget in chain."""
        if not self.focus_chain:
            return
            
        # Remove focus from current
        if self.focus_index < len(self.focus_chain):
            current = self.focus_chain[self.focus_index]
            current.remove_class("focused")
        
        # Move to next
        self.focus_index = (self.focus_index + 1) % len(self.focus_chain)
        next_widget = self.focus_chain[self.focus_index]
        next_widget.add_class("focused")
        next_widget.focus()
    
    def focus_previous(self) -> None:
        """Move focus to previous widget in chain."""
        if not self.focus_chain:
            return
            
        # Remove focus from current
        if self.focus_index < len(self.focus_chain):
            current = self.focus_chain[self.focus_index]
            current.remove_class("focused")
        
        # Move to previous
        self.focus_index = (self.focus_index - 1) % len(self.focus_chain)
        prev_widget = self.focus_chain[self.focus_index]
        prev_widget.add_class("focused")
        prev_widget.focus()
    
    def push_context(self, widget: Widget) -> None:
        """Push current context to stack."""
        current = self.app.focused
        if current:
            self.context_stack.append(current)
    
    def pop_context(self) -> Optional[Widget]:
        """Return to previous context."""
        if self.context_stack:
            previous = self.context_stack.pop()
            previous.focus()
            return previous
        return None
```

#### Enhanced Navigation Bindings
```python
# src/tui/screens/main.py (updated)
from textual.binding import Binding

class MainScreen(Screen):
    """Main screen with enhanced navigation."""
    
    BINDINGS = [
        # Panel navigation
        Binding("tab", "focus_next", "Next Panel", priority=True),
        Binding("shift+tab", "focus_previous", "Previous Panel"),
        Binding("ctrl+1", "focus_projects", "Focus Projects"),
        Binding("ctrl+2", "focus_feed", "Focus Feed"),
        
        # Within panel navigation
        Binding("up", "navigate_up", "Up"),
        Binding("down", "navigate_down", "Down"),
        Binding("left", "navigate_left", "Left"),
        Binding("right", "navigate_right", "Right"),
        Binding("home", "navigate_home", "Start"),
        Binding("end", "navigate_end", "End"),
        Binding("pageup", "page_up", "Page Up"),
        Binding("pagedown", "page_down", "Page Down"),
        
        # Context navigation
        Binding("escape", "escape_context", "Back"),
        Binding("enter", "select_item", "Select"),
        Binding("space", "toggle_item", "Toggle"),
    ]
    
    def action_focus_next(self) -> None:
        """Move focus to next panel."""
        self.app.focus_manager.focus_next()
    
    def action_focus_previous(self) -> None:
        """Move focus to previous panel."""
        self.app.focus_manager.focus_previous()
    
    def action_focus_projects(self) -> None:
        """Direct focus to projects panel."""
        projects = self.query_one("#projects-panel")
        projects.focus()
    
    def action_focus_feed(self) -> None:
        """Direct focus to feed panel."""
        feed = self.query_one("#live-feed-panel")
        feed.focus()
    
    def action_escape_context(self) -> None:
        """Handle ESC key context navigation."""
        # If in modal, close it
        if self.app.screen_stack[-1] != self:
            self.app.pop_screen()
        # If in nested context, go back
        elif self.app.focus_manager.pop_context():
            pass
        # Otherwise, unfocus current widget
        else:
            self.app.set_focus(None)
```

#### Visual Focus Indicators
```css
/* src/tui/styles/ccmonitor.css (focus styles) */

/* Default focus style */
*:focus {
    border: solid $warning;
    border-title-style: bold;
}

/* Panel-specific focus */
ProjectsPanel:focus {
    border: thick $warning;
    background: $surface 95%;
}

LiveFeedPanel:focus {
    border: thick $warning;
    background: $background 95%;
}

/* List item focus */
ListItem:focus {
    background: $primary 20%;
    text-style: bold;
}

/* Input focus */
Input:focus {
    border: double $warning;
    background: $surface;
}

/* Button focus */
Button:focus {
    background: $primary;
    color: white;
    text-style: bold;
}

/* Focus animation */
@keyframes focus-pulse {
    0% { border-color: $warning; }
    50% { border-color: $primary; }
    100% { border-color: $warning; }
}

.focused {
    animation: focus-pulse 2s infinite;
}
```

#### Arrow Key Navigation
```python
# src/tui/widgets/navigable_list.py
from textual.widgets import ListView
from textual.binding import Binding

class NavigableList(ListView):
    """ListView with arrow key navigation."""
    
    BINDINGS = [
        Binding("up", "cursor_up", "Previous Item"),
        Binding("down", "cursor_down", "Next Item"),
        Binding("enter", "select_cursor", "Select"),
        Binding("space", "toggle_cursor", "Toggle"),
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cursor_index = 0
    
    def action_cursor_up(self) -> None:
        """Move cursor up."""
        if self.cursor_index > 0:
            self.cursor_index -= 1
            self.refresh_cursor()
            self.scroll_to_cursor()
    
    def action_cursor_down(self) -> None:
        """Move cursor down."""
        if self.cursor_index < len(self.children) - 1:
            self.cursor_index += 1
            self.refresh_cursor()
            self.scroll_to_cursor()
    
    def refresh_cursor(self) -> None:
        """Update visual cursor indicator."""
        for i, child in enumerate(self.children):
            if i == self.cursor_index:
                child.add_class("cursor-active")
            else:
                child.remove_class("cursor-active")
    
    def scroll_to_cursor(self) -> None:
        """Ensure cursor is visible."""
        if self.cursor_index < len(self.children):
            self.scroll_to_widget(self.children[self.cursor_index])
```

#### Help Overlay with Navigation
```python
# src/tui/widgets/help_overlay.py (enhanced)
from textual.screen import ModalScreen
from textual.widgets import Static, DataTable
from textual.binding import Binding

class HelpOverlay(ModalScreen):
    """Modal help overlay with navigation info."""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Close Help"),
        Binding("h", "dismiss", "Close Help"),
    ]
    
    DEFAULT_CSS = """
    HelpOverlay {
        align: center middle;
    }
    
    HelpOverlay > Container {
        width: 70;
        height: 80%;
        background: $surface 95%;
        border: thick $primary;
        padding: 1 2;
    }
    
    .help-title {
        text-style: bold;
        color: $primary;
        text-align: center;
        padding-bottom: 1;
        border-bottom: solid $secondary;
    }
    
    #help-table {
        margin-top: 1;
        height: 1fr;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose help content."""
        with Container():
            yield Static("⌨️  Keyboard Shortcuts", classes="help-title")
            
            table = DataTable(id="help-table")
            table.add_columns("Category", "Key", "Action")
            
            # Add shortcuts by category
            shortcuts = [
                ("Navigation", "Tab", "Next panel"),
                ("Navigation", "Shift+Tab", "Previous panel"),
                ("Navigation", "↑/↓", "Navigate items"),
                ("Navigation", "Enter", "Select item"),
                ("Navigation", "Escape", "Back/Cancel"),
                ("Navigation", "Ctrl+1", "Focus projects"),
                ("Navigation", "Ctrl+2", "Focus feed"),
                
                ("Application", "Q", "Quit"),
                ("Application", "H", "Toggle help"),
                ("Application", "P", "Pause monitoring"),
                ("Application", "F", "Filter messages"),
                ("Application", "R", "Refresh"),
                
                ("Editing", "Ctrl+A", "Select all"),
                ("Editing", "Ctrl+C", "Copy"),
                ("Editing", "Ctrl+V", "Paste"),
                ("Editing", "Ctrl+X", "Cut"),
            ]
            
            for category, key, action in shortcuts:
                table.add_row(category, key, action)
            
            yield table
    
    def action_dismiss(self) -> None:
        """Close the help overlay."""
        self.app.pop_screen()
```

#### Focus Trap for Modals
```python
# src/tui/utils/modal.py
from textual.screen import ModalScreen

class FocusTrappedModal(ModalScreen):
    """Modal that traps focus within itself."""
    
    def on_mount(self) -> None:
        """Set up focus trap on mount."""
        # Save previous focus
        self.previous_focus = self.app.focused
        
        # Build focus chain for modal only
        self.modal_focus_chain = list(self.query(".focusable").results())
        
        # Focus first element
        if self.modal_focus_chain:
            self.modal_focus_chain[0].focus()
    
    def on_key(self, event) -> None:
        """Handle key events with focus trap."""
        if event.key == "tab":
            event.stop()
            self.focus_next_in_modal()
        elif event.key == "shift+tab":
            event.stop()
            self.focus_previous_in_modal()
    
    def focus_next_in_modal(self) -> None:
        """Cycle focus within modal."""
        current = self.app.focused
        if current in self.modal_focus_chain:
            idx = self.modal_focus_chain.index(current)
            next_idx = (idx + 1) % len(self.modal_focus_chain)
            self.modal_focus_chain[next_idx].focus()
    
    def on_unmount(self) -> None:
        """Restore focus on unmount."""
        if self.previous_focus:
            self.previous_focus.focus()
```

### Gotchas and Considerations

#### Common Textual Navigation Pitfalls

**Focus Chain Issues:**
- **Focus Chain Order**: Must be logical and predictable - follows `compose()` order by default
- **Invisible Widgets**: Widgets with `display: none` or `visibility: hidden` cannot be focused
- **Widget Focusability**: Not all widgets are focusable by default (`Static` needs `can_focus = True`)
- **Async Focus Changes**: Focus changes are async, always `await pilot.wait_for_animation()` in tests

**Modal and Screen Management:**
- **Modal Focus Trap**: `ModalScreen` automatically prevents Tab from escaping modal
- **Screen Stack Depth**: Deep modal stacking can confuse users - limit to 2-3 levels
- **ESC Key Consistency**: Always bind ESC to logical back/cancel action
- **Return Focus**: When closing modals, focus should return to logical previous element

**Platform and Accessibility:**
- **Platform Differences**: Some keys behave differently across OS (test on target platforms)
- **Screen Readers**: Focus changes should be announced (use semantic widgets)
- **Color Contrast**: Ensure focus indicators have sufficient contrast for accessibility
- **Keyboard-Only Navigation**: All functionality must be accessible without mouse

#### Textual-Specific Gotchas

**Event Handling Priority:**
```python
# Event handling order matters - most specific wins
class MyWidget(Widget):
    def key_escape(self) -> None:
        # Highest priority - always handles ESC first
        pass
    
    BINDINGS = [
        ("escape", "my_escape", "Custom ESC")  # Lower priority
    ]
    
    def on_key(self, event: Key) -> None:
        # Lowest priority - only if unhandled
        if event.key == "escape":
            pass  # This won't run due to key_escape above
```

**CSS Focus Styling:**
```css
/* Common mistake - forgetting :focus-within for containers */
.panel:focus {
    border: thick $accent;  /* Only when panel itself focused */
}

.panel:focus-within {
    border: thick $accent;  /* When ANY child is focused */
}

/* Animation performance consideration */
*:focus {
    /* Avoid expensive animations on every focus change */
    border: solid $accent;  /* Simple, performant */
}
```

**Widget Lifecycle Issues:**
```python
def on_mount(self) -> None:
    # Safe - widget is fully mounted
    self.query_one("#input").focus()

def compose(self) -> ComposeResult:
    input_widget = Input()
    yield input_widget
    # Unsafe - widget not mounted yet
    # input_widget.focus()  # Won't work!
```

## Implementation Blueprint

### Phase 1: Focus Management (1 hour)
1. Create FocusManager class
2. Implement focus chain building
3. Add focus_next/previous methods
4. Integrate with main app
5. Test basic Tab navigation

### Phase 2: Visual Indicators (45 min)
1. Add focus CSS styles
2. Create focus animation
3. Implement focused class toggling
4. Style different widget types
5. Test visual feedback

### Phase 3: Arrow Navigation (1 hour)
1. Create NavigableList widget
2. Implement cursor movement
3. Add scroll-to-cursor logic
4. Style cursor indicators
5. Test in panels

### Phase 4: Context Navigation (45 min)
1. Implement context stack
2. Add ESC key handling
3. Create push/pop context methods
4. Test nested contexts
5. Handle edge cases

### Phase 5: Help System (30 min)
1. Create comprehensive help overlay
2. Add categorized shortcuts
3. Implement modal focus trap
4. Style help display
5. Test overlay behavior

## Validation Loop

### Level 0: Test Creation
```python
# tests/tui/test_navigation.py
import pytest
from src.tui.utils.focus import FocusManager

def test_focus_chain_building():
    """Test focus chain is built correctly."""
    manager = FocusManager(mock_app)
    manager.build_focus_chain(mock_screen)
    assert len(manager.focus_chain) > 0
    assert all(w.focusable for w in manager.focus_chain)

def test_tab_navigation():
    """Test Tab cycles through widgets."""
    manager = FocusManager(mock_app)
    initial = manager.focus_index
    manager.focus_next()
    assert manager.focus_index == (initial + 1) % len(manager.focus_chain)

def test_context_stack():
    """Test ESC navigation context."""
    manager = FocusManager(mock_app)
    widget = Mock()
    manager.push_context(widget)
    popped = manager.pop_context()
    assert popped == widget

@pytest.mark.asyncio
async def test_modal_focus_trap():
    """Test focus stays within modal."""
    modal = FocusTrappedModal()
    # Test Tab doesn't escape modal
```

### Level 1: Syntax & Style
```bash
uv run ruff check src/tui/utils/ src/tui/widgets/
uv run ruff format src/tui/utils/ src/tui/widgets/
```

### Level 2: Type Checking
```bash
uv run mypy src/tui/utils/ src/tui/widgets/
```

### Level 3: Integration Testing
```python
# tests/tui/test_navigation_integration.py
import pytest
from textual.app import App
from textual.widgets import DirectoryTree, TextArea, Button
from src.tui.app import CCMonitorApp

@pytest.mark.asyncio
async def test_complete_navigation():
    """Test navigation across entire app using Textual testing patterns."""
    app = CCMonitorApp()
    
    async with app.run_test() as pilot:
        # Wait for initial mount
        await pilot.wait_for_animation()
        
        # Test Tab navigation between panels
        projects_panel = app.query_one("#projects-panel")
        feed_panel = app.query_one("#live-feed-panel")
        
        # Initial focus should be on projects panel
        assert app.focused == projects_panel
        
        # Press Tab to move to feed panel
        await pilot.press("tab")
        await pilot.wait_for_animation()
        assert app.focused == feed_panel
        
        # Test Shift+Tab to go back
        await pilot.press("shift+tab")
        await pilot.wait_for_animation()
        assert app.focused == projects_panel
        
        # Test direct focus shortcuts
        await pilot.press("ctrl+2")  # Focus feed directly
        await pilot.wait_for_animation()
        assert app.focused == feed_panel
        
        # Test arrow navigation within panels
        await pilot.press("down")
        await pilot.wait_for_animation()
        # Verify cursor moved within the focused panel
        
        # Test ESC context navigation
        await pilot.press("escape")
        await pilot.wait_for_animation()
        # Should unfocus current widget or handle context appropriately

@pytest.mark.asyncio
async def test_modal_focus_trapping():
    """Test that modal dialogs properly trap focus."""
    app = CCMonitorApp()
    
    async with app.run_test() as pilot:
        # Open help modal
        await pilot.press("h")
        await pilot.wait_for_screen("help_overlay")
        
        # Verify modal is active
        assert isinstance(app.screen, type(app.SCREENS["help_overlay"]))
        
        # Test Tab navigation within modal stays trapped
        initial_focused = app.focused
        await pilot.press("tab")
        await pilot.wait_for_animation()
        
        # Focus should cycle within modal, not escape to main screen
        assert app.screen == app.screen  # Still on modal
        
        # Test ESC closes modal and returns focus
        await pilot.press("escape")
        await pilot.wait_for_animation()
        
        # Should be back on main screen
        assert app.screen != app.SCREENS["help_overlay"]

@pytest.mark.asyncio  
async def test_help_overlay_navigation():
    """Test help overlay keyboard navigation."""
    app = CCMonitorApp()
    
    async with app.run_test() as pilot:
        # Open help overlay
        await pilot.press("h")
        await pilot.wait_for_screen("help_overlay")
        
        # Test help content is visible
        help_content = app.query_one(".help-content")
        assert help_content is not None
        
        # Test multiple ways to close help
        await pilot.press("escape")
        await pilot.wait_for_animation()
        assert not isinstance(app.screen, type(app.SCREENS["help_overlay"]))
        
        # Reopen and test 'q' to close
        await pilot.press("h") 
        await pilot.wait_for_screen("help_overlay")
        await pilot.press("q")
        await pilot.wait_for_animation()
        assert not isinstance(app.screen, type(app.SCREENS["help_overlay"]))

@pytest.mark.asyncio
async def test_focus_indicators_visible():
    """Test that focus indicators are properly applied."""
    app = CCMonitorApp()
    
    async with app.run_test() as pilot:
        projects_panel = app.query_one("#projects-panel")
        
        # Focus the panel and verify CSS classes
        projects_panel.focus()
        await pilot.wait_for_animation()
        
        # Check that focused styling is applied
        # This tests the CSS :focus pseudo-class application
        assert app.focused == projects_panel
        
        # Test focus moves correctly
        await pilot.press("tab")
        await pilot.wait_for_animation()
        assert app.focused != projects_panel

def test_snapshot_focused_panels(snap_compare):
    """Snapshot test showing visual focus indicators."""
    async def run_before_snapshot(pilot):
        # Focus different panels to show visual indicators
        await pilot.press("tab")  # Focus first panel
        await pilot.wait_for_animation()
        
    assert snap_compare(CCMonitorApp, run_before=run_before_snapshot)

def test_snapshot_help_overlay(snap_compare):
    """Snapshot test of help overlay appearance."""
    async def run_before_snapshot(pilot):
        await pilot.press("h")  # Open help
        await pilot.wait_for_screen("help_overlay")
        
    assert snap_compare(CCMonitorApp, run_before=run_before_snapshot)
```

#### Textual Testing Best Practices

**Essential Testing Utilities:**
```python
# Install testing dependencies
# pip install pytest pytest-textual-snapshot

# Key testing methods from Textual:
async def test_navigation_example():
    async with app.run_test() as pilot:
        # Wait for UI to stabilize
        await pilot.wait_for_animation()
        
        # Wait for specific screen
        await pilot.wait_for_screen(ScreenClass)
        
        # Simulate key presses
        await pilot.press("tab", "escape", "enter")
        
        # Simulate typing
        await pilot.enter_text(input_widget, "test text")
        
        # Click elements
        await pilot.click("#button-id")
        
        # Verify UI state
        assert app.focused == expected_widget
        assert isinstance(app.screen, ExpectedScreenClass)
```

**Focus Testing Patterns:**
```python
def test_focus_chain_building():
    """Verify focus chain is built correctly."""
    app = CCMonitorApp()
    
    # Test that all expected focusable widgets are included
    with app.run_test() as pilot:
        focusable_widgets = [w for w in app.query("*") if w.can_focus]
        assert len(focusable_widgets) > 0
        
        # Test focus moves through all widgets
        for i in range(len(focusable_widgets)):
            initial_focus = app.focused
            app.action_focus_next()
            assert app.focused != initial_focus  # Focus should change

def test_focus_groups():
    """Test focus group navigation."""
    app = CCMonitorApp()
    
    with app.run_test() as pilot:
        # Test group-specific focus navigation
        sidebar_widgets = app.query(".sidebar-widget")
        if sidebar_widgets:
            sidebar_widgets[0].focus()
            app.action_focus_next(group="sidebar")
            assert app.focused in sidebar_widgets
```

### Level 4: Manual Testing Checklist
- [ ] Tab cycles through all panels
- [ ] Shift+Tab goes backwards
- [ ] Arrow keys work in lists
- [ ] Focus indicators are visible
- [ ] ESC returns to previous context
- [ ] Help overlay shows and dismisses
- [ ] Ctrl+1/2 direct navigation works
- [ ] Modal dialogs trap focus
- [ ] No focus gets "lost"

## Dependencies
- PRP 01: Project Setup and Structure (must be complete)
- PRP 02: Application Framework (must be complete)
- PRP 03: Layout System (must be complete)

## Estimated Effort
4 hours total:
- 1 hour: Focus management system
- 45 minutes: Visual indicators
- 1 hour: Arrow navigation
- 45 minutes: Context navigation
- 30 minutes: Help system

## Agent Recommendations

### Primary Implementation Agents

- **@tui-textual-tui-specialist**: Core Textual framework implementation for navigation system, focus management, and keyboard interaction patterns
- **@python-specialist**: Focus management system implementation and event handling logic
- **@ui-ux-specialist**: Navigation patterns, visual feedback design, and user experience optimization for terminal applications

### Supporting Specialist Agents

- **@testing-specialist**: Comprehensive navigation testing with Textual's `run_test()` framework and snapshot testing
- **@accessibility-specialist**: Screen reader compatibility, keyboard-only navigation, and WCAG compliance patterns
- **@css-architect**: Advanced CSS styling for focus indicators, animations, and responsive design in terminal UI
- **@performance-optimizer**: Focus chain optimization, event handling efficiency, and large-scale UI performance

### Quality Assurance Agents

- **@test-automation-tester**: Automated testing setup with `pytest-textual-snapshot` and integration test patterns
- **@security-specialist**: Input validation, key binding security, and user interaction safety patterns
- **@ui-accessibility-specialist**: Terminal UI accessibility compliance and assistive technology compatibility

### Textual-Specific Recommendations

**For Navigation System Implementation:**
- Use **@tui-textual-tui-specialist** for core Textual patterns and framework integration
- Leverage **@ui-ux-specialist** for intuitive navigation flow design
- Engage **@testing-specialist** for comprehensive test coverage with Textual testing tools

**For Focus Management:**
- **@tui-textual-tui-specialist** understands Textual's focus system, event bubbling, and screen management
- **@python-specialist** can implement complex focus chain logic and event handling
- **@accessibility-specialist** ensures keyboard navigation meets accessibility standards

**For Visual Feedback:**
- **@css-architect** specializes in Textual CSS patterns, focus indicators, and terminal styling
- **@ui-ux-specialist** designs effective visual cues for focus states and navigation feedback
- **@accessibility-specialist** validates color contrast and visual accessibility requirements

## Risk Mitigation
- **Risk**: Platform-specific key codes
  - **Mitigation**: Test on multiple platforms, use Textual's key abstraction
- **Risk**: Focus getting "lost"
  - **Mitigation**: Always have fallback focus target
- **Risk**: Complex modal stacking
  - **Mitigation**: Limit modal depth, clear focus management
- **Risk**: Performance with many focusable widgets
  - **Mitigation**: Optimize focus chain building, cache when possible

## Definition of Done
- [ ] Tab navigation cycles through all panels
- [ ] Arrow keys navigate within panels
- [ ] Visual focus indicators clear and consistent
- [ ] ESC key provides logical back navigation
- [ ] Help overlay displays all shortcuts
- [ ] Modal dialogs properly trap focus
- [ ] All navigation tests pass
- [ ] Navigation feels intuitive in manual testing
- [ ] No focus-related bugs or glitches
- [ ] Accessibility considerations addressed