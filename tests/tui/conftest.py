"""TUI-specific pytest configuration and fixtures for CCMonitor testing."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock

import pytest
from textual.app import App

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def mock_app() -> Mock:
    """Create a mock application for testing."""
    app = Mock(spec=App)
    app.size = (120, 40)
    app.focused = None
    app.screen_stack = []
    app.notify = Mock()
    app.exit = Mock()
    app.is_running = True
    app.screen = Mock()
    app.query = Mock()
    app.query_one = Mock()
    return app


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """Create temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".config" / "ccmonitor"
        config_dir.mkdir(parents=True)
        yield config_dir


@pytest.fixture
def mock_terminal() -> Generator[None, None, None]:
    """Mock terminal environment."""
    original_term = os.environ.get("TERM")
    original_colorterm = os.environ.get("COLORTERM")

    os.environ["TERM"] = "xterm-256color"
    os.environ["COLORTERM"] = "truecolor"

    yield

    # Restore original values
    if original_term:
        os.environ["TERM"] = original_term
    elif "TERM" in os.environ:
        del os.environ["TERM"]

    if original_colorterm:
        os.environ["COLORTERM"] = original_colorterm
    elif "COLORTERM" in os.environ:
        del os.environ["COLORTERM"]


@pytest.fixture
def mock_widgets() -> dict[str, Mock]:
    """Create mock widgets for testing."""
    return {
        "header": Mock(),
        "footer": Mock(),
        "projects_panel": Mock(),
        "live_feed_panel": Mock(),
        "help_overlay": Mock(),
    }


@pytest.fixture
def performance_metrics() -> dict[str, float]:
    """Define performance thresholds for TUI testing."""
    return {
        "startup_time_ms": 500.0,  # Target from PRP
        "memory_usage_mb": 10.0,  # Target from PRP
        "resize_time_ms": 100.0,
        "render_time_ms": 16.67,  # 60fps
        "navigation_response_ms": 50.0,
    }


@pytest.fixture
def widget_test_data() -> dict[str, Any]:
    """Provide test data for widget testing."""
    return {
        "projects": [
            {
                "name": "Project Alpha",
                "path": "/path/to/alpha",
                "active": True,
            },
            {"name": "Project Beta", "path": "/path/to/beta", "active": False},
            {
                "name": "Project Gamma",
                "path": "/path/to/gamma",
                "active": True,
            },
        ],
        "conversations": [
            {
                "id": "conv_1",
                "project": "alpha",
                "timestamp": "2024-01-01T10:00:00Z",
                "message_count": 15,
            },
            {
                "id": "conv_2",
                "project": "beta",
                "timestamp": "2024-01-01T11:00:00Z",
                "message_count": 8,
            },
        ],
        "messages": [
            {
                "role": "user",
                "content": "Test message from user",
                "timestamp": "2024-01-01T10:00:00Z",
            },
            {
                "role": "assistant",
                "content": "Test response from assistant",
                "timestamp": "2024-01-01T10:00:05Z",
            },
        ],
        "status_updates": [
            {"type": "info", "message": "System initialized"},
            {"type": "warning", "message": "High memory usage"},
            {"type": "error", "message": "Connection failed"},
        ],
    }


@pytest.fixture
def keyboard_test_sequences() -> dict[str, list[str]]:
    """Provide keyboard test sequences for navigation testing."""
    return {
        "basic_navigation": ["tab", "tab", "tab"],
        "help_flow": ["h", "escape"],
        "quit_flow": ["q"],
        "panel_navigation": ["ctrl+1", "ctrl+2", "ctrl+3"],
        "arrow_navigation": ["down", "down", "up"],
        "escape_sequence": ["h", "escape", "tab", "escape"],
    }


@pytest.fixture
def terminal_sizes() -> list[tuple[int, int]]:
    """Provide test terminal sizes for responsive testing."""
    return [
        (80, 24),  # Minimum size
        (120, 40),  # Standard size
        (150, 50),  # Large size
        (60, 20),  # Below minimum (should show warning)
        (200, 60),  # Very large size
    ]


@pytest.fixture
def mock_file_content() -> dict[str, str]:
    """Mock file content for testing file operations."""
    return {
        "conversation.jsonl": (
            """{"role": "user", "content": "Hello"}
{"role": "assistant", "content": "Hi there!"}"""
        ),
        "config.yaml": (
            """theme: dark
terminal:
  width: 120
  height: 40"""
        ),
        "empty_file": "",
        "invalid_json": '{"invalid": json}',
    }
