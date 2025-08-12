"""Tests for CCMonitorApp core functionality."""

from __future__ import annotations

from src.tui.app import CCMonitorApp


class TestCCMonitorApp:
    """Test CCMonitorApp core functionality."""

    def test_app_initialization(self) -> None:
        """Test app initialization."""
        app = CCMonitorApp()

        # Test basic attributes exist
        assert hasattr(app, "TITLE")
        assert hasattr(app, "SUB_TITLE")
        assert hasattr(app, "VERSION")
        assert hasattr(app, "BINDINGS")

        # Check values
        assert app.TITLE is not None
        assert app.SUB_TITLE is not None
        assert app.VERSION is not None
        assert len(app.BINDINGS) > 0

    def test_app_bindings(self) -> None:
        """Test app has expected bindings."""
        app = CCMonitorApp()

        # Check for key bindings
        bindings = app.BINDINGS
        binding_keys = []

        for binding in bindings:
            if hasattr(binding, "key"):
                binding_keys.append(binding.key)
            elif isinstance(binding, tuple) and len(binding) >= 1:
                binding_keys.append(binding[0])

        # Should have quit binding
        assert "q" in binding_keys

    def test_app_metadata(self) -> None:
        """Test app metadata."""
        app = CCMonitorApp()

        assert app.TITLE == "CCMonitor - Multi-Project Monitoring"
        assert app.SUB_TITLE == "Real-time Claude conversation tracker"
        assert app.VERSION == "0.1.0"
