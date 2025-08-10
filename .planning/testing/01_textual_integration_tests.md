# Textual Integration Testing Framework

## Overview

This document outlines the implementation of comprehensive Textual integration tests using the `run_test()` framework and `Pilot` simulation. These tests will verify real keyboard navigation, focus management, and user interaction flows.

## Testing Framework Setup

### Dependencies
```toml
[tool.uv.dev-dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.1"
pytest-textual-snapshot = "^0.4.0"
pytest-mock = "^3.11.1"
```

### Base Test Structure
```python
# tests/tui/integration/conftest.py
import pytest
from src.tui.app import CCMonitorApp

@pytest.fixture
async def app():
    """Create a test CCMonitor app instance."""
    app = CCMonitorApp()
    return app

@pytest.fixture
async def app_with_data():
    """Create app with sample data loaded."""
    app = CCMonitorApp()
    # Load sample data for testing
    await app.load_sample_data()
    return app

class NavigationTestBase:
    """Base class for navigation integration tests."""
    
    @staticmethod
    async def wait_for_focus(pilot, expected_widget_id: str, timeout: float = 2.0):
        """Wait for specific widget to receive focus."""
        import asyncio
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if pilot.app.focused and pilot.app.focused.id == expected_widget_id:
                return True
            
            if asyncio.get_event_loop().time() - start_time > timeout:
                return False
                
            await asyncio.sleep(0.1)
    
    @staticmethod
    async def verify_focus_indicator(pilot, widget_id: str):
        """Verify focus indicator is visible on widget."""
        widget = pilot.app.query_one(f"#{widget_id}")
        # Check if widget has focus styling applied
        return widget.has_class("focused") or widget == pilot.app.focused
```

## 1. Core Navigation Flow Tests

### Tab Navigation Between Panels
```python
# tests/tui/integration/test_navigation_flow.py
import pytest
from tests.tui.integration.conftest import NavigationTestBase

class TestTabNavigation(NavigationTestBase):
    
    @pytest.mark.asyncio
    async def test_tab_cycles_through_panels(self, app):
        """Test Tab key cycles through all main panels."""
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Start with projects panel focused
            projects_panel = pilot.app.query_one("#projects-panel")
            feed_panel = pilot.app.query_one("#live-feed-panel")
            
            # Initial focus should be on projects panel
            assert pilot.app.focused == projects_panel
            await self.verify_focus_indicator(pilot, "projects-panel")
            
            # Press Tab to move to feed panel
            await pilot.press("tab")
            await pilot.wait_for_animation()
            assert pilot.app.focused == feed_panel
            await self.verify_focus_indicator(pilot, "live-feed-panel")
            
            # Press Tab again to cycle back to projects
            await pilot.press("tab")
            await pilot.wait_for_animation()
            assert pilot.app.focused == projects_panel
    
    @pytest.mark.asyncio  
    async def test_shift_tab_reverse_navigation(self, app):
        """Test Shift+Tab navigates in reverse order."""
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            projects_panel = pilot.app.query_one("#projects-panel")
            feed_panel = pilot.app.query_one("#live-feed-panel")
            
            # Start at projects panel, go to feed with Tab
            await pilot.press("tab")
            await pilot.wait_for_animation()
            assert pilot.app.focused == feed_panel
            
            # Use Shift+Tab to go back to projects
            await pilot.press("shift+tab")
            await pilot.wait_for_animation()
            assert pilot.app.focused == projects_panel
    
    @pytest.mark.asyncio
    async def test_direct_panel_shortcuts(self, app):
        """Test Ctrl+1 and Ctrl+2 direct panel navigation."""
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            projects_panel = pilot.app.query_one("#projects-panel")
            feed_panel = pilot.app.query_one("#live-feed-panel")
            
            # Use Ctrl+2 to jump directly to feed panel
            await pilot.press("ctrl+2")
            await pilot.wait_for_animation()
            assert pilot.app.focused == feed_panel
            
            # Use Ctrl+1 to jump directly to projects panel  
            await pilot.press("ctrl+1")
            await pilot.wait_for_animation()
            assert pilot.app.focused == projects_panel
```

### Arrow Key Navigation Within Panels
```python
class TestArrowNavigation(NavigationTestBase):
    
    @pytest.mark.asyncio
    async def test_arrow_keys_in_projects_panel(self, app_with_data):
        """Test arrow key navigation within projects list."""
        async with app_with_data.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Focus projects panel
            await pilot.press("ctrl+1")
            await pilot.wait_for_animation()
            
            projects_list = pilot.app.query_one("#projects-list")
            initial_cursor = projects_list.cursor_index
            
            # Press down arrow to move cursor
            await pilot.press("down")
            await pilot.wait_for_animation()
            assert projects_list.cursor_index == initial_cursor + 1
            
            # Press up arrow to move cursor back
            await pilot.press("up")  
            await pilot.wait_for_animation()
            assert projects_list.cursor_index == initial_cursor
    
    @pytest.mark.asyncio
    async def test_arrow_keys_in_feed_panel(self, app_with_data):
        """Test arrow key navigation within live feed."""
        async with app_with_data.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Focus feed panel
            await pilot.press("ctrl+2")
            await pilot.wait_for_animation()
            
            feed_list = pilot.app.query_one("#live-feed-list")
            
            # Test down arrow navigation
            await pilot.press("down", "down")
            await pilot.wait_for_animation()
            assert feed_list.cursor_index >= 2
            
            # Test page down navigation
            await pilot.press("pagedown")
            await pilot.wait_for_animation()
            # Verify cursor moved by page size
```

## 2. Modal Focus Trapping Tests

### Help Overlay Modal Tests
```python
# tests/tui/integration/test_modal_focus.py
class TestModalFocusTrapping(NavigationTestBase):
    
    @pytest.mark.asyncio
    async def test_help_overlay_focus_trap(self, app):
        """Test help overlay traps focus within modal."""
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Store initial focus
            initial_focused = pilot.app.focused
            
            # Open help overlay
            await pilot.press("h")
            await pilot.wait_for_screen("help")
            
            # Verify help modal is active
            assert pilot.app.screen.name == "help"
            
            # Test Tab navigation stays within modal
            help_buttons = pilot.app.query(".help-tab-button")
            assert len(help_buttons) > 0
            
            # Tab through help modal elements
            for _ in range(len(help_buttons) + 2):
                await pilot.press("tab")
                await pilot.wait_for_animation()
                # Focus should remain within help modal
                assert pilot.app.focused != initial_focused
            
            # Close help modal and verify focus restoration
            await pilot.press("escape")
            await pilot.wait_for_animation()
            assert pilot.app.screen.name == "main"
            # Focus should be restored to original element or logical fallback
    
    @pytest.mark.asyncio
    async def test_help_overlay_multiple_close_methods(self, app):
        """Test help overlay can be closed with ESC, H, or Q."""
        async with app.run_test() as pilot:
            # Test ESC close
            await pilot.press("h")  # Open help
            await pilot.wait_for_screen("help")
            await pilot.press("escape")  # Close help
            await pilot.wait_for_animation()
            assert pilot.app.screen.name == "main"
            
            # Test H toggle close
            await pilot.press("h")  # Open help
            await pilot.wait_for_screen("help") 
            await pilot.press("h")  # Close help
            await pilot.wait_for_animation()
            assert pilot.app.screen.name == "main"
            
            # Test Q close
            await pilot.press("h")  # Open help
            await pilot.wait_for_screen("help")
            await pilot.press("q")  # Close help
            await pilot.wait_for_animation() 
            assert pilot.app.screen.name == "main"
    
    @pytest.mark.asyncio
    async def test_help_tab_navigation(self, app):
        """Test navigation between help overlay tabs."""
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Open help overlay
            await pilot.press("h")
            await pilot.wait_for_screen("help")
            
            # Test tab switching with number keys
            await pilot.press("1")  # Navigation tab
            await pilot.wait_for_animation()
            nav_tab = pilot.app.query_one("#navigation-tab")
            assert nav_tab.has_class("active")
            
            await pilot.press("2")  # Shortcuts tab
            await pilot.wait_for_animation()
            shortcuts_tab = pilot.app.query_one("#shortcuts-tab")
            assert shortcuts_tab.has_class("active")
            
            await pilot.press("3")  # Focus system tab
            await pilot.wait_for_animation()
            focus_tab = pilot.app.query_one("#focus-system-tab")
            assert focus_tab.has_class("active")
```

## 3. ESC Context Navigation Tests

### Context Stack Management
```python
class TestContextNavigation(NavigationTestBase):
    
    @pytest.mark.asyncio
    async def test_esc_context_stack(self, app):
        """Test ESC key manages context stack correctly."""
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Start at projects panel
            projects_panel = pilot.app.query_one("#projects-panel")
            projects_panel.focus()
            
            # Navigate to feed panel
            await pilot.press("ctrl+2")
            await pilot.wait_for_animation()
            feed_panel = pilot.app.query_one("#live-feed-panel")
            assert pilot.app.focused == feed_panel
            
            # Open help modal (pushes context)
            await pilot.press("h")
            await pilot.wait_for_screen("help")
            
            # ESC should close modal and return to feed panel
            await pilot.press("escape")
            await pilot.wait_for_animation()
            assert pilot.app.screen.name == "main"
            assert pilot.app.focused == feed_panel
    
    @pytest.mark.asyncio
    async def test_esc_unfocus_at_root(self, app):
        """Test ESC unfocuses when at root context."""
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Focus a panel
            projects_panel = pilot.app.query_one("#projects-panel")
            projects_panel.focus()
            assert pilot.app.focused == projects_panel
            
            # ESC should unfocus the panel
            await pilot.press("escape")
            await pilot.wait_for_animation()
            assert pilot.app.focused != projects_panel or pilot.app.focused is None
```

## 4. Performance Integration Tests

### Focus Change Performance
```python
# tests/tui/integration/test_performance.py
import time
import pytest

class TestNavigationPerformance:
    
    @pytest.mark.asyncio
    async def test_tab_navigation_speed(self, app_with_data):
        """Test Tab navigation response time is under 50ms."""
        async with app_with_data.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Measure Tab navigation time
            start_time = time.perf_counter()
            await pilot.press("tab")
            await pilot.wait_for_animation()
            end_time = time.perf_counter()
            
            navigation_time = (end_time - start_time) * 1000  # Convert to ms
            assert navigation_time < 50, f"Tab navigation took {navigation_time}ms (limit: 50ms)"
    
    @pytest.mark.asyncio
    async def test_focus_chain_rebuild_performance(self, app):
        """Test focus chain rebuilding after layout changes."""
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Trigger layout change (e.g., terminal resize)
            start_time = time.perf_counter()
            # Simulate terminal resize
            pilot.app._handle_resize()
            await pilot.wait_for_animation()
            end_time = time.perf_counter()
            
            rebuild_time = (end_time - start_time) * 1000
            assert rebuild_time < 100, f"Focus chain rebuild took {rebuild_time}ms (limit: 100ms)"
```

## 5. Error Handling Integration Tests

### Robustness Testing
```python
class TestNavigationErrorHandling(NavigationTestBase):
    
    @pytest.mark.asyncio
    async def test_navigation_with_missing_widgets(self, app):
        """Test navigation gracefully handles missing widgets."""
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Simulate widget removal
            projects_panel = pilot.app.query_one("#projects-panel")
            projects_panel.remove()
            
            # Navigation should still work
            await pilot.press("tab")
            await pilot.wait_for_animation()
            # Should focus next available widget without error
            assert pilot.app.focused is not None
    
    @pytest.mark.asyncio
    async def test_focus_restoration_after_error(self, app):
        """Test focus restoration after focus-related errors."""
        async with app.run_test() as pilot:
            await pilot.wait_for_animation()
            
            # Focus a widget
            feed_panel = pilot.app.query_one("#live-feed-panel")
            feed_panel.focus()
            
            # Simulate error in focus system
            with pytest.raises(Exception):
                # Force an error in focus system
                pilot.app.focus_manager.set_focus("nonexistent-widget")
            
            # Navigation should recover
            await pilot.press("tab")
            await pilot.wait_for_animation()
            assert pilot.app.focused is not None
```

## Test Execution Guidelines

### Running Integration Tests
```bash
# Run all integration tests
pytest tests/tui/integration/ -v

# Run specific test categories
pytest tests/tui/integration/test_navigation_flow.py -v
pytest tests/tui/integration/test_modal_focus.py -v

# Run with coverage
pytest tests/tui/integration/ --cov=src.tui --cov-report=html

# Run performance tests only  
pytest tests/tui/integration/test_performance.py -v -m performance
```

### Test Configuration
```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers = 
    slow: marks tests as slow
    integration: integration tests
    performance: performance tests
    accessibility: accessibility tests
```

## Continuous Integration Integration

### GitHub Actions Workflow
```yaml
# .github/workflows/test-navigation.yml
name: Navigation Integration Tests

on: [push, pull_request]

jobs:
  test-navigation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync --dev
      - name: Run integration tests
        run: |
          uv run pytest tests/tui/integration/ -v --junit-xml=junit.xml
      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: junit.xml
```

This comprehensive integration testing framework will ensure that CCMonitor's navigation system works flawlessly in real-world usage scenarios, providing confidence in the user experience quality.