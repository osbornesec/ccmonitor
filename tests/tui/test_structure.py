"""Tests for TUI package structure and basic functionality."""

from pathlib import Path
from unittest.mock import patch

import pytest

# Import all TUI modules that we want to test
from src.tui import CCMonitorApp
from src.tui.app import CCMonitorApp as AppClass
from src.tui.config import TUIConfig, load_config
from src.tui.exceptions import (
    NavigationError,
    RecoverableError,
    RenderingError,
    StartupError,
    TerminalError,
    TUIError,
)
from src.tui.screens import ErrorScreen, HelpOverlay, MainScreen
from src.tui.utils import (
    KeyBindingManager,
    StartupValidator,
    ThemeManager,
    TransitionManager,
)
from src.tui.widgets import (
    BaseWidget,
    CCMonitorFooter,
    CCMonitorHeader,
    LoadingIndicator,
)

# Constants
MIN_TERMINAL_WIDTH = 80


def test_tui_package_imports() -> None:
    """Verify all TUI modules are importable."""
    assert CCMonitorApp is not None
    assert TUIConfig is not None
    assert issubclass(StartupError, TUIError)


def test_css_file_exists() -> None:
    """Verify CSS file is present and has valid Textual CSS syntax."""
    css_path = Path("src/tui/styles/ccmonitor.tcss")
    assert css_path.exists(), f"CSS file not found at {css_path}"

    content = css_path.read_text()
    assert len(content) > 0, "CSS file is empty"

    # Check for essential Textual CSS patterns
    assert "Screen {" in content, "Missing Screen root selector"
    assert (
        "$primary" in content or "$surface" in content
    ), "Missing theme variables"


def test_exception_hierarchy() -> None:
    """Verify exception classes are properly structured."""
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


def test_configuration_system() -> None:
    """Test configuration loading and defaults."""
    # Test default configuration
    config = TUIConfig()
    assert config.app_name == "CCMonitor"
    assert config.default_theme == "dark"
    assert config.min_terminal_width == MIN_TERMINAL_WIDTH

    # Test configuration loading with non-existent file
    config_loaded = load_config(Path("/non/existent/path"))
    assert config_loaded.app_name == "CCMonitor"  # Should use defaults


@pytest.mark.asyncio
async def test_app_basic_lifecycle() -> None:
    """Test basic App class lifecycle without full UI."""
    with patch("src.tui.app.logging"):
        app = AppClass()
        assert app.title is not None
        assert hasattr(app, "CSS_PATH")

        # Test app can be created without errors
        assert app.dark in (True, False)  # Should have a boolean theme state


def test_package_structure() -> None:
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


def test_screen_classes() -> None:
    """Test screen classes are properly defined."""
    assert MainScreen is not None
    assert HelpOverlay is not None
    assert ErrorScreen is not None

    # Test that they have required attributes
    assert hasattr(MainScreen, "BINDINGS")
    assert hasattr(HelpOverlay, "BINDINGS")
    assert hasattr(ErrorScreen, "BINDINGS")


def test_widget_classes() -> None:
    """Test widget classes are properly defined."""
    assert BaseWidget is not None
    assert CCMonitorHeader is not None
    assert CCMonitorFooter is not None
    assert LoadingIndicator is not None


def test_utility_classes() -> None:
    """Test utility classes are properly defined."""
    assert KeyBindingManager is not None
    assert ThemeManager is not None
    assert StartupValidator is not None
    assert TransitionManager is not None

    # Test basic functionality
    theme_manager = ThemeManager()
    assert theme_manager.current_theme == "dark"

    startup_validator = StartupValidator()
    assert isinstance(startup_validator.errors, list)

    key_manager = KeyBindingManager()
    key_manager.register_binding("q", "quit")
    assert key_manager.get_action("q") == "quit"

    transition_manager = TransitionManager()
    assert transition_manager.animation_enabled is True
