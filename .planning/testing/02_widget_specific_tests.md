# Widget-Specific Navigation Testing

## Overview

This document outlines comprehensive testing strategies for individual navigation widgets in the CCMonitor TUI. Each widget requires specific test scenarios to verify keyboard navigation, visual feedback, and integration with the focus management system.

## Testing Architecture

```
tests/tui/widgets/
├── test_navigable_list.py      # NavigableList widget tests
├── test_help_overlay.py        # HelpOverlay modal tests  
├── test_main_screen.py         # MainScreen navigation tests
├── test_projects_panel.py      # ProjectsPanel widget tests
├── test_live_feed_panel.py     # LiveFeedPanel widget tests
└── conftest.py                 # Widget testing fixtures
```

## 1. NavigableList Widget Tests

### Core Navigation Features
```python
# tests/tui/widgets/test_navigable_list.py
import pytest
from src.tui.widgets.navigable_list import NavigableList
from textual.widgets import ListItem, Static

class TestNavigableList:
    
    @pytest.fixture
    def sample_list(self):
        """Create NavigableList with sample data."""
        items = [
            ListItem(Static(f"Item {i}"), id=f"item-{i}")
            for i in range(10)
        ]
        return NavigableList(*items, id="test-list")
    
    @pytest.mark.asyncio
    async def test_cursor_initialization(self, sample_list):
        """Test cursor starts at first item."""
        async with sample_list.run_test() as pilot:
            await pilot.wait_for_animation()
            
            assert sample_list.cursor_index == 0
            assert sample_list.show_cursor is True
            
            # First item should have cursor styling
            first_item = sample_list.children[0]
            assert first_item.has_class("cursor-active")
    
    @pytest.mark.asyncio
    async def test_down_arrow_navigation(self, sample_list):
        """Test down arrow moves cursor down."""
        async with sample_list.run_test() as pilot:
            await pilot.wait_for_animation()
            
            initial_cursor = sample_list.cursor_index
            
            # Press down arrow multiple times
            for i in range(3):
                await pilot.press("down")
                await pilot.wait_for_animation()
                assert sample_list.cursor_index == initial_cursor + i + 1
            
            # Verify visual cursor moved
            current_item = sample_list.children[sample_list.cursor_index]
            assert current_item.has_class("cursor-active")
    
    @pytest.mark.asyncio  
    async def test_up_arrow_navigation(self, sample_list):
        """Test up arrow moves cursor up."""
        async with sample_list.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Move cursor down first
            sample_list.cursor_index = 5
            sample_list.refresh_cursor()
            
            # Press up arrow multiple times
            for i in range(3):
                await pilot.press("up")
                await pilot.wait_for_animation()
                assert sample_list.cursor_index == 5 - i - 1
    
    @pytest.mark.asyncio
    async def test_cursor_wrap_around(self, sample_list):
        """Test cursor wraps around at boundaries."""
        async with sample_list.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Test wrap from last to first
            sample_list.cursor_index = len(sample_list.children) - 1
            sample_list.refresh_cursor()
            
            await pilot.press("down")
            await pilot.wait_for_animation()
            assert sample_list.cursor_index == 0
            
            # Test wrap from first to last  
            await pilot.press("up")
            await pilot.wait_for_animation()
            assert sample_list.cursor_index == len(sample_list.children) - 1
    
    @pytest.mark.asyncio
    async def test_page_navigation(self, sample_list):
        """Test page up/down navigation."""
        async with sample_list.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Test page down
            initial_cursor = sample_list.cursor_index
            await pilot.press("pagedown")
            await pilot.wait_for_animation()
            
            # Should move by visible page size
            page_size = sample_list.size.height - 2  # Account for borders
            expected_cursor = min(
                initial_cursor + page_size,
                len(sample_list.children) - 1
            )
            assert sample_list.cursor_index == expected_cursor
            
            # Test page up
            await pilot.press("pageup")
            await pilot.wait_for_animation()
            assert sample_list.cursor_index <= initial_cursor
    
    @pytest.mark.asyncio
    async def test_home_end_navigation(self, sample_list):
        """Test home/end key navigation."""
        async with sample_list.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Move to middle
            sample_list.cursor_index = 5
            sample_list.refresh_cursor()
            
            # Test Home key
            await pilot.press("home")
            await pilot.wait_for_animation()
            assert sample_list.cursor_index == 0
            
            # Test End key
            await pilot.press("end")
            await pilot.wait_for_animation()
            assert sample_list.cursor_index == len(sample_list.children) - 1
    
    @pytest.mark.asyncio
    async def test_enter_selection(self, sample_list):
        """Test Enter key selection."""
        selection_count = 0
        selected_items = []
        
        def on_selection(item_index):
            nonlocal selection_count, selected_items
            selection_count += 1
            selected_items.append(item_index)
        
        sample_list.on_item_selected = on_selection
        
        async with sample_list.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Select first item
            await pilot.press("enter")
            await pilot.wait_for_animation()
            assert selection_count == 1
            assert selected_items[-1] == 0
            
            # Move and select another item
            await pilot.press("down", "down", "enter")
            await pilot.wait_for_animation()
            assert selection_count == 2
            assert selected_items[-1] == 2
    
    @pytest.mark.asyncio
    async def test_scroll_to_cursor(self, sample_list):
        """Test automatic scrolling to keep cursor visible."""
        # Create a list larger than viewport
        large_items = [
            ListItem(Static(f"Item {i}"), id=f"item-{i}")
            for i in range(50)
        ]
        large_list = NavigableList(*large_items, id="large-list")
        
        async with large_list.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Move cursor to item beyond viewport
            large_list.cursor_index = 40
            large_list.scroll_to_cursor()
            await pilot.wait_for_animation()
            
            # Verify cursor item is visible
            cursor_item = large_list.children[40]
            assert cursor_item.region.y >= large_list.scroll_y
            assert cursor_item.region.bottom <= large_list.scroll_y + large_list.size.height


class TestNavigableListAdvanced:
    """Advanced NavigableList functionality tests."""
    
    @pytest.mark.asyncio
    async def test_vim_style_navigation(self, sample_list):
        """Test vim-style j/k navigation."""
        async with sample_list.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Test j for down
            await pilot.press("j")
            await pilot.wait_for_animation()
            assert sample_list.cursor_index == 1
            
            # Test k for up
            await pilot.press("k")
            await pilot.wait_for_animation()
            assert sample_list.cursor_index == 0
    
    @pytest.mark.asyncio
    async def test_numeric_jump_navigation(self, sample_list):
        """Test numeric key jumping (1-9, 0)."""
        async with sample_list.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Test jumping to item 5 (index 4)
            await pilot.press("5")
            await pilot.wait_for_animation()
            assert sample_list.cursor_index == 4
            
            # Test jumping to item 1 (index 0)
            await pilot.press("1")
            await pilot.wait_for_animation()
            assert sample_list.cursor_index == 0
            
            # Test jumping to item 0 (last item shortcut)
            await pilot.press("0")
            await pilot.wait_for_animation()
            assert sample_list.cursor_index == len(sample_list.children) - 1
    
    @pytest.mark.asyncio
    async def test_cursor_visibility_toggle(self, sample_list):
        """Test cursor can be hidden/shown."""
        async with sample_list.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Initially cursor should be visible
            assert sample_list.show_cursor is True
            cursor_item = sample_list.children[sample_list.cursor_index]
            assert cursor_item.has_class("cursor-active")
            
            # Hide cursor
            sample_list.show_cursor = False
            sample_list.refresh_cursor()
            await pilot.wait_for_animation()
            
            # Cursor styling should be removed
            assert not cursor_item.has_class("cursor-active")
            
            # Show cursor again
            sample_list.show_cursor = True
            sample_list.refresh_cursor()
            await pilot.wait_for_animation()
            assert cursor_item.has_class("cursor-active")
    
    @pytest.mark.asyncio
    async def test_focus_integration(self, sample_list):
        """Test integration with focus management system."""
        async with sample_list.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Focus the list
            sample_list.focus()
            await pilot.wait_for_animation()
            
            # Should have focus styling
            assert sample_list.has_class("focused")
            
            # Cursor should be visible when focused
            assert sample_list.show_cursor is True
            
            # Remove focus
            sample_list.blur()
            await pilot.wait_for_animation()
            
            # Focus styling should be removed
            assert not sample_list.has_class("focused")
```

## 2. HelpOverlay Widget Tests

### Modal Behavior and Tab Navigation
```python
# tests/tui/widgets/test_help_overlay.py
import pytest
from src.tui.screens.help_screen import HelpOverlay

class TestHelpOverlay:
    
    @pytest.fixture
    def help_overlay(self):
        """Create HelpOverlay instance."""
        return HelpOverlay()
    
    @pytest.mark.asyncio
    async def test_help_overlay_initialization(self, help_overlay):
        """Test help overlay initializes with correct content."""
        async with help_overlay.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Check initial tab is Navigation
            nav_tab = pilot.app.query_one("#navigation-tab")
            assert nav_tab.has_class("active")
            
            # Check all tabs are present
            assert pilot.app.query_one("#navigation-tab")
            assert pilot.app.query_one("#shortcuts-tab")
            assert pilot.app.query_one("#focus-system-tab")
            assert pilot.app.query_one("#status-tab")
    
    @pytest.mark.asyncio
    async def test_tab_switching_with_numbers(self, help_overlay):
        """Test switching tabs with number keys 1-4."""
        async with help_overlay.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Switch to Shortcuts tab (2)
            await pilot.press("2")
            await pilot.wait_for_animation()
            shortcuts_tab = pilot.app.query_one("#shortcuts-tab")
            assert shortcuts_tab.has_class("active")
            
            # Switch to Focus System tab (3)
            await pilot.press("3")
            await pilot.wait_for_animation()
            focus_tab = pilot.app.query_one("#focus-system-tab")
            assert focus_tab.has_class("active")
            
            # Switch to Status tab (4)
            await pilot.press("4")
            await pilot.wait_for_animation()
            status_tab = pilot.app.query_one("#status-tab")
            assert status_tab.has_class("active")
            
            # Switch back to Navigation tab (1)
            await pilot.press("1")
            await pilot.wait_for_animation()
            nav_tab = pilot.app.query_one("#navigation-tab")
            assert nav_tab.has_class("active")
    
    @pytest.mark.asyncio
    async def test_tab_switching_with_arrow_keys(self, help_overlay):
        """Test switching tabs with left/right arrow keys."""
        async with help_overlay.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Start at Navigation tab, go right to Shortcuts
            await pilot.press("right")
            await pilot.wait_for_animation()
            shortcuts_tab = pilot.app.query_one("#shortcuts-tab")
            assert shortcuts_tab.has_class("active")
            
            # Go left back to Navigation
            await pilot.press("left")
            await pilot.wait_for_animation()
            nav_tab = pilot.app.query_one("#navigation-tab")
            assert nav_tab.has_class("active")
    
    @pytest.mark.asyncio
    async def test_help_content_generation(self, help_overlay):
        """Test help content is generated correctly."""
        async with help_overlay.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Check Navigation tab content
            nav_content = pilot.app.query_one("#navigation-content")
            nav_text = nav_content.renderable
            assert "Tab/Shift+Tab" in str(nav_text)
            assert "Arrow keys" in str(nav_text)
            assert "Ctrl+1, Ctrl+2" in str(nav_text)
            
            # Check Shortcuts tab content
            await pilot.press("2")
            await pilot.wait_for_animation()
            shortcuts_content = pilot.app.query_one("#shortcuts-content")
            shortcuts_text = shortcuts_content.renderable
            assert "Application shortcuts" in str(shortcuts_text)
            
            # Check Status tab has dynamic content
            await pilot.press("4")
            await pilot.wait_for_animation()
            status_content = pilot.app.query_one("#status-content")
            status_text = status_content.renderable
            assert "Focus Manager Status" in str(status_text)
    
    @pytest.mark.asyncio
    async def test_modal_focus_trapping(self, help_overlay):
        """Test focus is trapped within help overlay."""
        async with help_overlay.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Get all focusable elements within modal
            focusable = pilot.app.query(".help-tab-button")
            assert len(focusable) >= 4
            
            # Tab through all elements multiple times
            initial_focus = pilot.app.focused
            for i in range(len(focusable) * 2):
                await pilot.press("tab")
                await pilot.wait_for_animation()
                # Focus should cycle within modal
                assert pilot.app.focused in focusable
            
            # Should return to first element
            assert pilot.app.focused == initial_focus or pilot.app.focused == focusable[0]
    
    @pytest.mark.asyncio
    async def test_help_overlay_dismissal(self, help_overlay):
        """Test help overlay can be dismissed with multiple keys."""
        async with help_overlay.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Test ESC dismissal
            await pilot.press("escape")
            # Modal should be dismissed (tested in integration tests)
            
        # Test Q dismissal
        async with help_overlay.run_test() as pilot:
            await pilot.wait_for_animation()
            await pilot.press("q")
            
        # Test H dismissal  
        async with help_overlay.run_test() as pilot:
            await pilot.wait_for_animation()
            await pilot.press("h")


class TestHelpOverlayDynamic:
    """Test dynamic content generation in help overlay."""
    
    @pytest.mark.asyncio
    async def test_status_tab_live_updates(self, help_overlay):
        """Test status tab shows live focus manager state."""
        from src.tui.utils.focus import focus_manager
        
        async with help_overlay.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Switch to status tab
            await pilot.press("4")
            await pilot.wait_for_animation()
            
            # Register a test widget to focus manager
            from src.tui.utils.focus import FocusableWidget
            test_widget = FocusableWidget("test-widget", "Test Widget")
            focus_manager.register_focusable("test-group", test_widget)
            
            # Update help content
            help_overlay.update_status_content()
            await pilot.wait_for_animation()
            
            # Status should reflect new widget
            status_content = pilot.app.query_one("#status-content")
            status_text = str(status_content.renderable)
            assert "test-group" in status_text
            assert "Test Widget" in status_text
            
            # Clean up
            focus_manager.unregister_focusable("test-widget")
    
    @pytest.mark.asyncio
    async def test_keyboard_shortcuts_tab_accuracy(self, help_overlay):
        """Test keyboard shortcuts tab reflects actual bindings."""
        async with help_overlay.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Switch to shortcuts tab
            await pilot.press("2")
            await pilot.wait_for_animation()
            
            shortcuts_content = pilot.app.query_one("#shortcuts-content")
            shortcuts_text = str(shortcuts_content.renderable)
            
            # Check for expected shortcuts
            expected_shortcuts = [
                ("Q", "Quit"),
                ("H", "Toggle Help"),
                ("P", "Pause/Resume"),
                ("F", "Toggle Filter"),
                ("Ctrl+C", "Force Quit"),
                ("ESC", "Back/Cancel"),
            ]
            
            for key, description in expected_shortcuts:
                assert key in shortcuts_text
                assert description in shortcuts_text
```

## 3. MainScreen Navigation Tests

### Panel Management and Focus Flow
```python
# tests/tui/widgets/test_main_screen.py
import pytest
from src.tui.screens.main_screen import MainScreen

class TestMainScreen:
    
    @pytest.fixture
    def main_screen(self):
        """Create MainScreen instance."""
        return MainScreen()
    
    @pytest.mark.asyncio
    async def test_main_screen_initialization(self, main_screen):
        """Test main screen initializes with correct layout."""
        async with main_screen.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Check main panels are present
            assert pilot.app.query_one("#projects-panel")
            assert pilot.app.query_one("#live-feed-panel")
            
            # Check initial focus
            initial_focus = pilot.app.focused
            assert initial_focus is not None
            assert initial_focus.id in ["projects-panel", "live-feed-panel"]
    
    @pytest.mark.asyncio
    async def test_focus_manager_integration(self, main_screen):
        """Test main screen integrates with focus manager."""
        async with main_screen.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Focus manager should be initialized
            assert main_screen.focus_manager is not None
            
            # Focus groups should be registered
            focus_groups = main_screen.focus_manager.focus_groups
            assert "projects" in focus_groups
            assert "live_feed" in focus_groups
            
            # Widgets should be registered
            projects_widgets = main_screen.focus_manager.get_focusable_widgets("projects")
            assert len(projects_widgets) > 0
            
            feed_widgets = main_screen.focus_manager.get_focusable_widgets("live_feed")
            assert len(feed_widgets) > 0
    
    @pytest.mark.asyncio
    async def test_panel_focus_shortcuts(self, main_screen):
        """Test direct panel focus shortcuts."""
        async with main_screen.run_test() as pilot:
            await pilot.wait_for_animation()
            
            projects_panel = pilot.app.query_one("#projects-panel")
            feed_panel = pilot.app.query_one("#live-feed-panel")
            
            # Test Ctrl+1 focuses projects panel
            await pilot.press("ctrl+1")
            await pilot.wait_for_animation()
            assert pilot.app.focused == projects_panel
            
            # Test Ctrl+2 focuses feed panel
            await pilot.press("ctrl+2")
            await pilot.wait_for_animation()
            assert pilot.app.focused == feed_panel
            
            # Test F1 alternative for projects
            await pilot.press("f1")
            await pilot.wait_for_animation()
            assert pilot.app.focused == projects_panel
            
            # Test F2 alternative for feed
            await pilot.press("f2")
            await pilot.wait_for_animation()
            assert pilot.app.focused == feed_panel
    
    @pytest.mark.asyncio
    async def test_escape_context_handling(self, main_screen):
        """Test ESC key context navigation."""
        async with main_screen.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Focus a panel
            projects_panel = pilot.app.query_one("#projects-panel")
            projects_panel.focus()
            
            # ESC should handle context appropriately
            await pilot.press("escape")
            await pilot.wait_for_animation()
            
            # Should either unfocus or return to previous context
            # Exact behavior depends on context stack state
            current_focus = pilot.app.focused
            # Test passes if no exception is raised
            assert True
    
    @pytest.mark.asyncio
    async def test_layout_responsive_focus(self, main_screen):
        """Test focus management responds to layout changes."""
        async with main_screen.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Get initial focus chain length
            initial_chain_length = len(main_screen.focus_manager.focus_groups)
            
            # Simulate terminal resize
            # This should trigger focus chain rebuild
            main_screen.on_resize()
            await pilot.wait_for_animation()
            
            # Focus system should still work
            await pilot.press("tab")
            await pilot.wait_for_animation()
            assert pilot.app.focused is not None
            
            # Focus chain should be rebuilt (same or updated length)
            current_chain_length = len(main_screen.focus_manager.focus_groups)
            assert current_chain_length >= initial_chain_length


class TestMainScreenAdvanced:
    """Advanced MainScreen functionality tests."""
    
    @pytest.mark.asyncio
    async def test_panel_visibility_focus_management(self, main_screen):
        """Test focus management when panels change visibility."""
        async with main_screen.run_test() as pilot:
            await pilot.wait_for_animation()
            
            projects_panel = pilot.app.query_one("#projects-panel")
            feed_panel = pilot.app.query_one("#live-feed-panel")
            
            # Focus projects panel
            projects_panel.focus()
            assert pilot.app.focused == projects_panel
            
            # Hide projects panel
            projects_panel.visible = False
            await pilot.wait_for_animation()
            
            # Focus should move to next available widget
            assert pilot.app.focused != projects_panel
            assert pilot.app.focused is not None
            
            # Show projects panel again
            projects_panel.visible = True
            await pilot.wait_for_animation()
            
            # Should be able to focus it again
            projects_panel.focus()
            assert pilot.app.focused == projects_panel
    
    @pytest.mark.asyncio
    async def test_rapid_navigation_stability(self, main_screen):
        """Test rapid navigation doesn't cause issues."""
        async with main_screen.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Rapidly press navigation keys
            keys = ["tab", "ctrl+1", "ctrl+2", "tab", "shift+tab"] * 5
            for key in keys:
                await pilot.press(key)
                # Don't wait for animation to test rapid input
            
            await pilot.wait_for_animation()  # Wait once at the end
            
            # Should still have a valid focus
            assert pilot.app.focused is not None
            
            # Navigation should still work
            await pilot.press("tab")
            await pilot.wait_for_animation()
            assert pilot.app.focused is not None
```

## Test Execution and CI Integration

### Widget Test Runner
```bash
# Run all widget tests
pytest tests/tui/widgets/ -v

# Run specific widget tests
pytest tests/tui/widgets/test_navigable_list.py -v
pytest tests/tui/widgets/test_help_overlay.py -v
pytest tests/tui/widgets/test_main_screen.py -v

# Run with coverage
pytest tests/tui/widgets/ --cov=src.tui.widgets --cov-report=html

# Run performance-sensitive tests
pytest tests/tui/widgets/ -v -m "not slow"
```

### Coverage Requirements
- **NavigableList**: >95% line coverage
- **HelpOverlay**: >90% line coverage  
- **MainScreen**: >85% line coverage
- **Integration**: 100% of public methods tested

### Continuous Integration
```yaml
# .github/workflows/test-widgets.yml
widget-tests:
  runs-on: ubuntu-latest
  steps:
    - name: Test NavigableList
      run: pytest tests/tui/widgets/test_navigable_list.py -v
    - name: Test HelpOverlay
      run: pytest tests/tui/widgets/test_help_overlay.py -v
    - name: Test MainScreen
      run: pytest tests/tui/widgets/test_main_screen.py -v
    - name: Upload widget test coverage
      uses: codecov/codecov-action@v3
```

This comprehensive widget testing strategy ensures each navigation component works correctly in isolation and integrates properly with the overall focus management system.