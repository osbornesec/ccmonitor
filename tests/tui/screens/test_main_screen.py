"""Tests for MainScreen."""

from __future__ import annotations

from unittest.mock import Mock, patch

from src.tui.screens.main_screen import MainScreen


class TestMainScreen:
    """Test MainScreen functionality."""

    def test_main_screen_initialization(self) -> None:
        """Test MainScreen initialization."""
        main_screen = MainScreen()

        # Test basic attributes exist
        assert hasattr(main_screen, "DEFAULT_CSS")
        assert hasattr(main_screen, "BINDINGS")
        assert len(main_screen.BINDINGS) > 0

    def test_main_screen_compose(self) -> None:
        """Test main screen composition."""
        main_screen = MainScreen()

        # Test that compose method exists and returns content
        compose_result = main_screen.compose()

        # Should yield widgets
        widgets = list(compose_result)
        assert len(widgets) >= 1

    def test_main_screen_bindings(self) -> None:
        """Test main screen has expected bindings."""
        main_screen = MainScreen()

        # Check for key bindings
        bindings = main_screen.BINDINGS
        binding_keys = []

        for binding in bindings:
            if hasattr(binding, "key"):
                binding_keys.append(binding.key)
            elif isinstance(binding, tuple) and len(binding) >= 1:
                binding_keys.append(binding[0])

        # Should have navigation bindings
        assert "tab" in binding_keys
        assert "up" in binding_keys
        assert "down" in binding_keys

    def test_action_refresh_view(self) -> None:
        """Test refresh action."""
        main_screen = MainScreen()

        # Mock notify method
        with patch.object(main_screen, "notify") as mock_notify:
            main_screen.action_refresh_view()
            mock_notify.assert_called_once()

    def test_action_show_help(self) -> None:
        """Test show help action."""
        main_screen = MainScreen()

        # Mock app
        mock_app = Mock()
        with patch.object(main_screen, "app", mock_app):
            main_screen.action_show_help()

            # Should push help screen
            mock_app.push_screen.assert_called_once()
