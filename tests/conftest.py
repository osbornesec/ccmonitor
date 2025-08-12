"""Global pytest configuration and fixtures for CCMonitor testing."""

from __future__ import annotations

import asyncio
import contextlib
import gc
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable, Generator

    from textual.app import App
    from textual.pilot import Pilot

# Import for cleanup - avoiding PLC0415 error
try:
    from src.tui.utils.focus import focus_manager
except ImportError:
    focus_manager = None  # type: ignore[assignment]

# Test configuration constants
TEST_TERMINAL_SIZE = (120, 40)
TEST_TIMEOUT = 30.0


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    yield loop

    # Clean up
    with contextlib.suppress(RuntimeError):
        loop.close()


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for config files during testing."""
    with tempfile.TemporaryDirectory(prefix="ccmonitor_test_") as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_data_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for data files during testing."""
    with tempfile.TemporaryDirectory(prefix="ccmonitor_data_") as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_file_system() -> Generator[Mock, None, None]:
    """Mock file system operations for testing."""
    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("pathlib.Path.is_file") as mock_is_file,
        patch("pathlib.Path.is_dir") as mock_is_dir,
    ):
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_is_dir.return_value = True

        yield mock_exists


@pytest.fixture
def mock_config() -> dict[str, dict[str, str | int | bool | float]]:
    """Provide mock configuration for testing."""
    return {
        "terminal": {
            "width": TEST_TERMINAL_SIZE[0],
            "height": TEST_TERMINAL_SIZE[1],
            "refresh_rate": 60,
        },
        "theme": {
            "name": "dark",
            "accent_color": "blue",
        },
        "performance": {
            "animation_duration": 0.1,  # Faster for tests
            "debounce_delay": 0.01,
        },
        "accessibility": {
            "focus_visible": True,
            "keyboard_only": False,
            "screen_reader": False,
        },
    }


@pytest.fixture
def textual_pilot_factory() -> (
    Callable[[type[App]], AsyncGenerator[Pilot, None]]
):
    """Create factory for Textual app pilots with standard config."""

    async def create_pilot(
        app_class: type[App],
    ) -> AsyncGenerator[Pilot, None]:
        """Create a pilot for the given app class with test configuration."""
        app = app_class()

        # Configure app for testing
        app.test_mode = True  # type: ignore[attr-defined]

        async with app.run_test(
            size=TEST_TERMINAL_SIZE,
            headless=True,
        ) as pilot:
            # Wait for app to fully initialize
            await pilot.pause(0.1)
            yield pilot

    return create_pilot


@pytest.fixture
def mock_focus_manager() -> Generator[Mock, None, None]:
    """Mock the global focus manager for testing."""
    with patch("src.tui.utils.focus.focus_manager") as mock_manager:
        mock_manager.current_focus = None
        mock_manager.focus_groups = {}
        mock_manager.focus_chain = []
        mock_manager.is_modal_active = False
        yield mock_manager


@pytest.fixture
def capture_logs(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Configure logging capture for tests."""
    caplog.set_level("DEBUG")
    return caplog


@pytest.fixture
def performance_threshold() -> dict[str, float]:
    """Define performance thresholds for testing."""
    return {
        "navigation_response_ms": 50.0,
        "startup_time_ms": 200.0,
        "memory_usage_mb": 100.0,
        "animation_frame_ms": 16.67,  # 60fps
    }


@pytest.fixture(autouse=True)
def cleanup_globals() -> Generator[None, None, None]:
    """Clean up global state after each test."""
    yield

    # Reset any global managers or singletons
    if focus_manager is not None:
        with contextlib.suppress(AttributeError):
            focus_manager.reset()  # type: ignore[attr-defined]

    # Clear any cached data
    gc.collect()


@pytest.fixture
def widget_test_data() -> dict[str, Any]:
    """Provide test data for widget testing."""
    return {
        "projects": [
            {"id": "proj1", "name": "Project 1", "status": "active"},
            {"id": "proj2", "name": "Project 2", "status": "inactive"},
            {"id": "proj3", "name": "Project 3", "status": "active"},
        ],
        "conversations": [
            {
                "id": "conv1",
                "project": "proj1",
                "timestamp": "2024-01-01T10:00:00Z",
            },
            {
                "id": "conv2",
                "project": "proj1",
                "timestamp": "2024-01-01T11:00:00Z",
            },
            {
                "id": "conv3",
                "project": "proj2",
                "timestamp": "2024-01-01T12:00:00Z",
            },
        ],
        "feed_items": [
            {"type": "conversation", "data": {"message": "Hello world"}},
            {"type": "error", "data": {"error": "Connection failed"}},
            {"type": "status", "data": {"status": "Processing"}},
        ],
    }


# Pytest markers for test categorization
pytest_markers = [
    "unit: Unit tests that test individual functions or methods",
    "integration: Integration tests that test component interactions",
    "ui: UI tests that test Textual interface interactions",
    "accessibility: Tests for WCAG 2.1 AA compliance",
    "performance: Performance benchmark tests",
    "visual: Visual regression snapshot tests",
    "cli: Command-line interface tests",
    "slow: Tests that take longer than 5 seconds",
    "network: Tests that require network access",
    "filesystem: Tests that interact with the file system",
]


def _add_location_markers(item: pytest.Item) -> None:
    """Add markers based on test file location."""
    location_markers = [
        ("integration", pytest.mark.integration),
        ("accessibility", pytest.mark.accessibility),
        ("performance", pytest.mark.performance),
        ("visual", pytest.mark.visual),
        ("cli", pytest.mark.cli),
    ]

    for location, marker in location_markers:
        if location in str(item.fspath):
            item.add_marker(marker)


def _add_name_markers(item: pytest.Item) -> None:
    """Add markers based on test name patterns."""
    name_lower = item.name.lower()
    if "slow" in name_lower or "benchmark" in name_lower:
        item.add_marker(pytest.mark.slow)


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with custom markers and settings."""
    # Register custom markers
    for marker in pytest_markers:
        config.addinivalue_line("markers", marker)

    # Set test discovery patterns
    config.option.testmon_noselect = True


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Modify collected test items to add automatic markers."""
    _ = config  # Unused parameter
    for item in items:
        _add_location_markers(item)
        _add_name_markers(item)


# Test environment setup
os.environ["TEXTUAL_LOG"] = ""  # Disable Textual logging during tests
os.environ["CCMONITOR_TEST_MODE"] = "true"
