"""Tests for TUI styles module initialization."""

from __future__ import annotations

import src.tui.styles
from src.tui.styles import __all__


def test_styles_module_imports() -> None:
    """Test that styles module can be imported successfully."""
    # This covers the basic import and __all__ definition

    # Verify the module has the expected __all__ attribute
    assert hasattr(src.tui.styles, "__all__")
    assert isinstance(src.tui.styles.__all__, list)


def test_styles_init_structure() -> None:
    """Test that styles __init__.py has correct structure."""
    # Verify __all__ is properly defined as empty list for now
    assert __all__ == []
    assert isinstance(__all__, list)


def test_styles_module_docstring() -> None:
    """Test that styles module has proper documentation."""
    # Verify module docstring exists
    assert src.tui.styles.__doc__ is not None
    assert "TUI styling system" in src.tui.styles.__doc__
