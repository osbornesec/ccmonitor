# PRP: Testing and Quality Assurance Infrastructure

## Goal
Establish comprehensive testing infrastructure for the TUI application with unit tests, integration tests, performance benchmarks, and cross-platform validation to ensure >95% code coverage and reliable operation.

## Why
Robust testing is essential for maintaining code quality, preventing regressions, and ensuring the TUI works correctly across different environments. A comprehensive test suite enables confident refactoring and feature additions.

## What
### Requirements
- Write unit tests for all TUI components (>95% coverage)
- Create integration tests for application lifecycle
- Add performance tests for startup time and memory usage
- Test cross-platform compatibility (Linux, macOS, Windows)
- Validate keyboard shortcuts across terminal emulators
- Implement automated test execution in CI/CD
- Create visual regression testing framework

### Success Criteria
- [ ] Unit test coverage exceeds 95%
- [ ] All integration tests pass consistently
- [ ] Startup time under 500ms verified by tests
- [ ] Memory usage under 10MB confirmed
- [ ] Tests pass on Linux, macOS, and Windows
- [ ] Keyboard shortcuts work in major terminals
- [ ] CI/CD pipeline runs all tests automatically
- [ ] Visual regression tests catch UI changes

## All Needed Context

### Technical Specifications

#### Test Infrastructure Setup
```python
# tests/tui/conftest.py
import pytest
from textual.pilot import Pilot
from textual.app import App
from unittest.mock import Mock, AsyncMock
from pathlib import Path
import tempfile
import asyncio

@pytest.fixture
def mock_app():
    """Create a mock application for testing."""
    app = Mock(spec=App)
    app.size = (120, 40)
    app.focused = None
    app.screen_stack = []
    app.notify = Mock()
    app.exit = Mock()
    return app

@pytest.fixture
async def test_app():
    """Create a real test application."""
    from src.tui.app import CCMonitorApp
    app = CCMonitorApp()
    app.run_test = AsyncMock()
    return app

@pytest.fixture
def temp_config_dir():
    """Create temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".config" / "ccmonitor"
        config_dir.mkdir(parents=True)
        yield config_dir

@pytest.fixture
async def app_pilot():
    """Create app with pilot for integration testing."""
    from src.tui.app import CCMonitorApp
    app = CCMonitorApp()
    async with app.run_test() as pilot:
        yield app, pilot

@pytest.fixture
def mock_terminal():
    """Mock terminal environment."""
    import os
    original_term = os.environ.get('TERM')
    original_colorterm = os.environ.get('COLORTERM')
    
    os.environ['TERM'] = 'xterm-256color'
    os.environ['COLORTERM'] = 'truecolor'
    
    yield
    
    # Restore original values
    if original_term:
        os.environ['TERM'] = original_term
    elif 'TERM' in os.environ:
        del os.environ['TERM']
        
    if original_colorterm:
        os.environ['COLORTERM'] = original_colorterm
    elif 'COLORTERM' in os.environ:
        del os.environ['COLORTERM']
```

#### Unit Test Suite
```python
# tests/tui/test_widgets.py
import pytest
from src.tui.widgets.header import Header
from src.tui.widgets.footer import Footer
from src.tui.widgets.projects_panel import ProjectsPanel
from src.tui.widgets.live_feed_panel import LiveFeedPanel

class TestHeader:
    """Test Header widget functionality."""
    
    def test_header_creation(self):
        """Test header can be created."""
        header = Header()
        assert header is not None
        assert header.styles.height == 3
    
    def test_header_composition(self):
        """Test header contains expected elements."""
        header = Header()
        components = list(header.compose())
        assert len(components) > 0
    
    @pytest.mark.asyncio
    async def test_header_status_update(self, mock_app):
        """Test header status updates."""
        header = Header()
        header.app = mock_app
        header.update_status()
        # Verify status was updated

class TestFooter:
    """Test Footer widget functionality."""
    
    def test_footer_creation(self):
        """Test footer can be created."""
        footer = Footer()
        assert footer is not None
        assert footer.styles.height == 1
    
    def test_footer_message_update(self):
        """Test footer message updates."""
        footer = Footer()
        footer.update_message("Test message")
        # Verify message displayed
    
    @pytest.mark.asyncio
    async def test_footer_message_reset(self):
        """Test footer message resets after timeout."""
        footer = Footer()
        footer.update_message("Temporary")
        await asyncio.sleep(3.1)
        # Verify message reset to shortcuts

class TestProjectsPanel:
    """Test ProjectsPanel widget functionality."""
    
    def test_panel_sizing(self):
        """Test panel respects size constraints."""
        panel = ProjectsPanel()
        assert panel.styles.width == "25%"
        assert panel.styles.min_width == 20
        assert panel.styles.max_width == 40
    
    def test_panel_composition(self):
        """Test panel contains expected elements."""
        panel = ProjectsPanel()
        components = list(panel.compose())
        # Verify title, list, and stats present
    
    @pytest.mark.asyncio
    async def test_panel_scrolling(self, app_pilot):
        """Test panel scrolling with many items."""
        app, pilot = app_pilot
        panel = app.query_one(ProjectsPanel)
        # Add many items
        # Test scrolling

class TestLiveFeedPanel:
    """Test LiveFeedPanel widget functionality."""
    
    def test_panel_creation(self):
        """Test live feed panel creation."""
        panel = LiveFeedPanel()
        assert panel is not None
        assert panel.styles.width == "1fr"
    
    @pytest.mark.asyncio
    async def test_message_display(self):
        """Test message display in feed."""
        panel = LiveFeedPanel()
        panel.add_message("user", "Test message")
        # Verify message displayed correctly
    
    @pytest.mark.asyncio
    async def test_message_filtering(self, app_pilot):
        """Test message filtering functionality."""
        app, pilot = app_pilot
        panel = app.query_one(LiveFeedPanel)
        await pilot.type("filter", "test")
        # Verify filtering applied
```

#### Integration Test Suite
```python
# tests/tui/test_app_integration.py
import pytest
from src.tui.app import CCMonitorApp

class TestApplicationLifecycle:
    """Test application lifecycle management."""
    
    @pytest.mark.asyncio
    async def test_app_startup(self):
        """Test application starts correctly."""
        app = CCMonitorApp()
        async with app.run_test() as pilot:
            # Verify app started
            assert app.is_running
            # Verify main screen loaded
            assert app.screen is not None
    
    @pytest.mark.asyncio
    async def test_app_shutdown(self):
        """Test application shuts down cleanly."""
        app = CCMonitorApp()
        async with app.run_test() as pilot:
            await pilot.press("q")
            # Verify clean shutdown
    
    @pytest.mark.asyncio
    async def test_screen_navigation(self):
        """Test screen navigation."""
        app = CCMonitorApp()
        async with app.run_test() as pilot:
            # Test help screen
            await pilot.press("h")
            # Verify help displayed
            await pilot.press("escape")
            # Verify returned to main

class TestKeyboardNavigation:
    """Test keyboard navigation functionality."""
    
    @pytest.mark.asyncio
    async def test_tab_navigation(self):
        """Test Tab cycles through panels."""
        app = CCMonitorApp()
        async with app.run_test() as pilot:
            # Initial focus
            initial_focus = app.focused
            
            # Press Tab
            await pilot.press("tab")
            assert app.focused != initial_focus
            
            # Complete cycle
            for _ in range(10):  # More than panel count
                await pilot.press("tab")
            # Should cycle back
    
    @pytest.mark.asyncio
    async def test_arrow_navigation(self):
        """Test arrow key navigation."""
        app = CCMonitorApp()
        async with app.run_test() as pilot:
            # Focus list
            await pilot.press("ctrl+1")
            
            # Navigate with arrows
            await pilot.press("down")
            await pilot.press("up")
            # Verify cursor movement
    
    @pytest.mark.asyncio
    async def test_escape_navigation(self):
        """Test ESC key behavior."""
        app = CCMonitorApp()
        async with app.run_test() as pilot:
            # Open help
            await pilot.press("h")
            # Close with ESC
            await pilot.press("escape")
            # Verify closed

class TestResponsiveBehavior:
    """Test responsive layout behavior."""
    
    @pytest.mark.asyncio
    async def test_terminal_resize(self):
        """Test layout adapts to resize."""
        app = CCMonitorApp()
        async with app.run_test(size=(120, 40)) as pilot:
            # Initial size
            sidebar = app.query_one("#projects-panel")
            initial_width = sidebar.styles.width
            
            # Resize smaller
            await pilot.resize_terminal(80, 24)
            # Verify layout adjusted
            assert sidebar.styles.width != initial_width
    
    @pytest.mark.asyncio
    async def test_minimum_size_warning(self):
        """Test warning for small terminal."""
        app = CCMonitorApp()
        async with app.run_test(size=(60, 20)) as pilot:
            # Verify warning displayed
            notifications = app.query(".notification")
            assert len(notifications) > 0
```

#### Performance Test Suite
```python
# tests/tui/test_performance.py
import pytest
import time
import psutil
import asyncio
from src.tui.app import CCMonitorApp

class TestPerformance:
    """Test application performance metrics."""
    
    @pytest.mark.asyncio
    async def test_startup_time(self):
        """Test application startup time."""
        start_time = time.perf_counter()
        
        app = CCMonitorApp()
        async with app.run_test() as pilot:
            startup_time = time.perf_counter() - start_time
            
            # Should start in under 500ms
            assert startup_time < 0.5, f"Startup took {startup_time:.2f}s"
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Test application memory usage."""
        app = CCMonitorApp()
        async with app.run_test() as pilot:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            # Should use less than 10MB for basic UI
            assert memory_mb < 10, f"Memory usage: {memory_mb:.2f}MB"
    
    @pytest.mark.asyncio
    async def test_resize_performance(self):
        """Test performance during resize."""
        app = CCMonitorApp()
        async with app.run_test(size=(120, 40)) as pilot:
            resize_times = []
            
            for size in [(100, 30), (150, 50), (80, 24)]:
                start = time.perf_counter()
                await pilot.resize_terminal(*size)
                resize_times.append(time.perf_counter() - start)
            
            # Average resize should be fast
            avg_time = sum(resize_times) / len(resize_times)
            assert avg_time < 0.1, f"Avg resize: {avg_time:.3f}s"
    
    @pytest.mark.asyncio
    async def test_rendering_performance(self):
        """Test rendering performance with many widgets."""
        app = CCMonitorApp()
        async with app.run_test() as pilot:
            # Add many messages
            panel = app.query_one("#live-feed-panel")
            
            start = time.perf_counter()
            for i in range(100):
                panel.add_message("user", f"Message {i}")
            render_time = time.perf_counter() - start
            
            # Should handle 100 messages quickly
            assert render_time < 1.0
```

#### Cross-Platform Test Suite
```python
# tests/tui/test_cross_platform.py
import pytest
import sys
import platform
from src.tui.app import CCMonitorApp

class TestCrossPlatform:
    """Test cross-platform compatibility."""
    
    @pytest.mark.skipif(platform.system() != "Linux", reason="Linux only")
    @pytest.mark.asyncio
    async def test_linux_compatibility(self):
        """Test Linux-specific functionality."""
        app = CCMonitorApp()
        async with app.run_test() as pilot:
            # Test Linux-specific features
            assert app.is_running
    
    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only")
    @pytest.mark.asyncio
    async def test_macos_compatibility(self):
        """Test macOS-specific functionality."""
        app = CCMonitorApp()
        async with app.run_test() as pilot:
            # Test macOS-specific features
            assert app.is_running
    
    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
    @pytest.mark.asyncio
    async def test_windows_compatibility(self):
        """Test Windows-specific functionality."""
        app = CCMonitorApp()
        async with app.run_test() as pilot:
            # Test Windows-specific features
            assert app.is_running
    
    @pytest.mark.asyncio
    async def test_terminal_emulators(self, mock_terminal):
        """Test different terminal emulators."""
        terminals = [
            ('xterm', 'xterm-256color'),
            ('gnome', 'gnome-256color'),
            ('iterm2', 'xterm-256color'),
            ('windows-terminal', 'xterm-256color'),
        ]
        
        for name, term_var in terminals:
            import os
            os.environ['TERM'] = term_var
            
            app = CCMonitorApp()
            async with app.run_test() as pilot:
                # Basic functionality should work
                assert app.is_running
```

#### Visual Regression Testing
```python
# tests/tui/test_visual_regression.py
import pytest
from pathlib import Path
from src.tui.app import CCMonitorApp

class TestVisualRegression:
    """Test visual appearance consistency."""
    
    SNAPSHOT_DIR = Path("tests/tui/snapshots")
    
    @pytest.mark.asyncio
    async def test_main_screen_appearance(self):
        """Test main screen visual appearance."""
        app = CCMonitorApp()
        async with app.run_test(size=(120, 40)) as pilot:
            # Take screenshot
            screenshot = await pilot.screenshot()
            
            # Compare with baseline
            baseline = self.SNAPSHOT_DIR / "main_screen.svg"
            if baseline.exists():
                # Compare screenshots
                assert self.compare_screenshots(screenshot, baseline)
            else:
                # Save as new baseline
                baseline.parent.mkdir(parents=True, exist_ok=True)
                baseline.write_text(screenshot)
    
    @pytest.mark.asyncio
    async def test_help_overlay_appearance(self):
        """Test help overlay visual appearance."""
        app = CCMonitorApp()
        async with app.run_test() as pilot:
            await pilot.press("h")
            
            screenshot = await pilot.screenshot()
            baseline = self.SNAPSHOT_DIR / "help_overlay.svg"
            
            if baseline.exists():
                assert self.compare_screenshots(screenshot, baseline)
            else:
                baseline.write_text(screenshot)
    
    def compare_screenshots(self, current: str, baseline: Path) -> bool:
        """Compare two screenshots for visual differences."""
        baseline_content = baseline.read_text()
        
        # Simple comparison - could be enhanced with image diff
        return current == baseline_content
```

#### Test Coverage Configuration
```ini
# .coveragerc
[run]
source = src/tui
omit = 
    */tests/*
    */conftest.py
    */__init__.py

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov

[xml]
output = coverage.xml
```

#### CI/CD Integration
```yaml
# .github/workflows/tui-tests.yml
name: TUI Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.11', '3.12']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install uv
        uv pip install -e .[dev]
    
    - name: Run linting
      run: |
        uv run ruff check src/tui/
        uv run mypy src/tui/
    
    - name: Run tests with coverage
      run: |
        uv run pytest tests/tui/ --cov=src/tui --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: tui
        name: tui-coverage
    
    - name: Performance tests
      if: matrix.os == 'ubuntu-latest'
      run: |
        uv run pytest tests/tui/test_performance.py -v
```

### Gotchas and Considerations
- **Async Testing**: Textual uses async extensively - use pytest-asyncio
- **Terminal Mocking**: Must mock terminal environment variables
- **Visual Testing**: Screenshots may vary slightly between platforms
- **Performance Variance**: CI/CD performance differs from local
- **Focus Testing**: Focus behavior can be tricky to test
- **Coverage Gaps**: Some error paths hard to test

## Implementation Blueprint

### Phase 1: Test Infrastructure (1 hour)
1. Set up pytest configuration
2. Create test fixtures
3. Configure coverage reporting
4. Set up mock helpers
5. Test basic setup

### Phase 2: Unit Tests (2 hours)
1. Test all widgets individually
2. Test utility functions
3. Test error handling
4. Test theme system
5. Achieve >95% coverage

### Phase 3: Integration Tests (1.5 hours)
1. Test application lifecycle
2. Test navigation flows
3. Test screen transitions
4. Test resize behavior
5. Test error scenarios

### Phase 4: Performance Tests (1 hour)
1. Test startup time
2. Test memory usage
3. Test resize performance
4. Test rendering speed
5. Create benchmarks

### Phase 5: Cross-Platform Tests (1 hour)
1. Test on Linux
2. Test on macOS
3. Test on Windows
4. Test terminal emulators
5. Document compatibility

### Phase 6: CI/CD Setup (30 min)
1. Create GitHub workflow
2. Configure test matrix
3. Set up coverage reporting
4. Add performance checks
5. Test pipeline

## Validation Loop

### Level 0: Test Execution
```bash
# Run all tests
uv run pytest tests/tui/ -v

# Run with coverage
uv run pytest tests/tui/ --cov=src/tui --cov-report=html

# Run specific test categories
uv run pytest tests/tui/test_widgets.py -v
uv run pytest tests/tui/test_performance.py -v
```

### Level 1: Coverage Analysis
```bash
# Generate coverage report
uv run coverage report

# Check coverage threshold
uv run coverage report --fail-under=95
```

### Level 2: Performance Validation
```bash
# Run performance tests
uv run pytest tests/tui/test_performance.py --benchmark
```

### Level 3: Cross-Platform Testing
```bash
# Test on different platforms (in CI/CD)
# Linux, macOS, Windows via GitHub Actions
```

### Level 4: Visual Regression
```bash
# Run visual tests
uv run pytest tests/tui/test_visual_regression.py

# Update snapshots
uv run pytest tests/tui/test_visual_regression.py --snapshot-update
```

## Dependencies
- All previous PRPs must be complete
- Testing should be done after implementation

## Estimated Effort
7 hours total:
- 1 hour: Test infrastructure
- 2 hours: Unit tests
- 1.5 hours: Integration tests
- 1 hour: Performance tests
- 1 hour: Cross-platform tests
- 30 minutes: CI/CD setup

## Agent Recommendations
- **test-writer**: For comprehensive test creation
- **performance-optimizer**: For performance test design
- **ci-cd-specialist**: For pipeline configuration
- **python-specialist**: For async test patterns

## Risk Mitigation
- **Risk**: Flaky async tests
  - **Mitigation**: Use proper async fixtures, add retries
- **Risk**: Platform-specific failures
  - **Mitigation**: Skip tests appropriately, document requirements
- **Risk**: Performance regression
  - **Mitigation**: Set baseline metrics, monitor trends
- **Risk**: Coverage gaps
  - **Mitigation**: Use mutation testing, review uncovered lines

## Definition of Done
- [ ] Test infrastructure configured
- [ ] Unit test coverage >95%
- [ ] All integration tests pass
- [ ] Performance benchmarks met
- [ ] Cross-platform tests pass
- [ ] CI/CD pipeline functional
- [ ] Visual regression tests set up
- [ ] Coverage reports generated
- [ ] Test documentation complete
- [ ] All tests run in under 2 minutes