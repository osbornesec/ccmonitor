"""Tests for HelpOverlay widget."""

from __future__ import annotations

from unittest.mock import Mock, PropertyMock, patch

from src.tui.widgets.help_overlay import HelpOverlay

# Constants
MIN_WIDGETS_COUNT = 2


class TestHelpOverlay:
    """Test HelpOverlay widget functionality."""

    def test_help_overlay_initialization(self) -> None:
        """Test HelpOverlay initialization."""
        help_overlay = HelpOverlay()

        # Test basic attributes exist
        assert hasattr(help_overlay, "DEFAULT_CSS")
        assert help_overlay.DEFAULT_CSS is not None
        assert len(help_overlay.DEFAULT_CSS) > 0

    def test_help_overlay_compose(self) -> None:
        """Test help overlay composition."""
        help_overlay = HelpOverlay()

        # Test that compose method exists and returns content
        compose_result = help_overlay.compose()

        # Should yield widgets
        widgets = list(compose_result)
        assert len(widgets) >= 1

    def test_help_overlay_key_escape(self) -> None:
        """Test escape key handling."""
        help_overlay = HelpOverlay()

        # Mock the app property
        mock_app = Mock()
        with patch.object(
            type(help_overlay), "app", new_callable=PropertyMock,
        ) as mock_app_prop:
            mock_app_prop.return_value = mock_app

            # Test escape key
            help_overlay.key_escape()

            # Should call pop_screen
            mock_app.pop_screen.assert_called_once()

    def test_help_overlay_key_h(self) -> None:
        """Test 'h' key handling."""
        help_overlay = HelpOverlay()

        # Mock the app property
        mock_app = Mock()
        with patch.object(
            type(help_overlay), "app", new_callable=PropertyMock,
        ) as mock_app_prop:
            mock_app_prop.return_value = mock_app

            # Test 'h' key
            help_overlay.key_h()

            # Should call pop_screen
            mock_app.pop_screen.assert_called_once()

    def test_help_overlay_css_styling(self) -> None:
        """Test CSS styling contains expected properties."""
        help_overlay = HelpOverlay()

        css = help_overlay.DEFAULT_CSS

        # Check for key styling properties
        assert "HelpOverlay" in css
        assert "layer: overlay" in css
        assert "background:" in css
        assert "border:" in css
        assert "padding:" in css
        assert "align: center middle" in css

    def test_help_overlay_content_structure(self) -> None:
        """Test help content structure."""
        help_overlay = HelpOverlay()

        # Get composed widgets
        widgets = list(help_overlay.compose())

        # Should have table and footer
        assert len(widgets) >= MIN_WIDGETS_COUNT

        # Check that widgets have expected IDs
        widget_ids = [getattr(w, "id", None) for w in widgets]
        assert "shortcuts_table" in widget_ids
        assert "help_footer" in widget_ids
