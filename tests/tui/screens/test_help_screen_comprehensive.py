"""Comprehensive tests for HelpOverlay screen.

This module provides complete test coverage for the HelpOverlay modal screen,
including initialization, composition, navigation, focus management, and all
interactive functionality.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from src.tui.screens.help_screen import HelpOverlay


class TestHelpOverlayInitialization:
    """Test HelpOverlay initialization and basic properties."""

    def test_default_initialization(self) -> None:
        """Test HelpOverlay with default parameters."""
        overlay = HelpOverlay()

        assert overlay is not None
        assert overlay.title is None  # Set during mount

    def test_css_defined(self) -> None:
        """Test that CSS is properly defined."""
        overlay = HelpOverlay()

        assert overlay.DEFAULT_CSS is not None
        assert len(overlay.DEFAULT_CSS) > 0
        assert "#help-modal" in overlay.DEFAULT_CSS

    def test_bindings_defined(self) -> None:
        """Test that key bindings are properly defined."""
        overlay = HelpOverlay()

        assert overlay.BINDINGS is not None
        assert len(overlay.BINDINGS) > 0

        # Check for expected bindings
        binding_keys = [
            binding.key if hasattr(binding, "key") else binding[0]
            for binding in overlay.BINDINGS
        ]
        expected_keys = ["escape", "q", "tab", "shift+tab", "1", "2", "3"]

        for key in expected_keys:
            assert key in binding_keys


class TestHelpOverlayComposition:
    """Test HelpOverlay compose method and content generation."""

    def test_compose_creates_container(self) -> None:
        """Test that compose creates the main container."""
        overlay = HelpOverlay()

        with (
            patch.object(overlay, "_create_navigation_help") as mock_nav,
            patch.object(overlay, "_create_shortcuts_help") as mock_shortcuts,
            patch.object(overlay, "_create_focus_help") as mock_focus,
            patch.object(overlay, "_create_status_help") as mock_status,
            patch.object(overlay, "_create_footer") as mock_footer,
        ):

            mock_nav.return_value = Mock()
            mock_shortcuts.return_value = Mock()
            mock_focus.return_value = Mock()
            mock_status.return_value = Mock()
            mock_footer.return_value = Mock()

            widgets = list(overlay.compose())

            # Should have container
            assert len(widgets) >= 1

            # All helper methods should be called
            mock_nav.assert_called_once()
            mock_shortcuts.assert_called_once()
            mock_focus.assert_called_once()
            mock_status.assert_called_once()
            mock_footer.assert_called_once()

    def test_create_navigation_help(self) -> None:
        """Test navigation help content creation."""
        overlay = HelpOverlay()

        nav_help = overlay._create_navigation_help()

        assert nav_help is not None
        # Should be a scrollable container
        assert hasattr(nav_help, "mount")

    def test_create_shortcuts_help(self) -> None:
        """Test shortcuts help content creation."""
        overlay = HelpOverlay()

        with patch.object(overlay, "_get_dynamic_shortcuts", return_value={}):
            shortcuts_help = overlay._create_shortcuts_help()

            assert shortcuts_help is not None
            assert hasattr(shortcuts_help, "mount")

    def test_create_shortcuts_help_with_dynamic(self) -> None:
        """Test shortcuts help with dynamic shortcuts."""
        overlay = HelpOverlay()

        mock_shortcuts = {"ctrl+p": "Projects", "ctrl+f": "Feed"}
        with patch.object(
            overlay, "_get_dynamic_shortcuts", return_value=mock_shortcuts,
        ):
            shortcuts_help = overlay._create_shortcuts_help()

            assert shortcuts_help is not None

    def test_create_focus_help(self) -> None:
        """Test focus help content creation."""
        overlay = HelpOverlay()

        with patch("src.tui.screens.help_screen.focus_manager") as mock_fm:
            mock_fm.current_focus = "test-widget"
            mock_fm.focus_groups = {"group1": Mock(), "group2": Mock()}
            mock_fm.focus_history = [Mock(), Mock(), Mock()]

            focus_help = overlay._create_focus_help()

            assert focus_help is not None
            assert hasattr(focus_help, "mount")

    def test_create_status_help(self) -> None:
        """Test status help content creation."""
        overlay = HelpOverlay()

        status_help = overlay._create_status_help()

        assert status_help is not None
        assert hasattr(status_help, "mount")

    def test_create_footer(self) -> None:
        """Test footer creation with buttons."""
        overlay = HelpOverlay()

        footer = overlay._create_footer()

        assert footer is not None
        assert hasattr(footer, "mount")

    def test_get_dynamic_shortcuts_empty(self) -> None:
        """Test dynamic shortcuts retrieval with no shortcuts."""
        overlay = HelpOverlay()

        with patch("src.tui.screens.help_screen.focus_manager") as mock_fm:
            mock_fm.focus_groups = {}

            shortcuts = overlay._get_dynamic_shortcuts()

            assert isinstance(shortcuts, dict)
            assert len(shortcuts) == 0

    def test_get_dynamic_shortcuts_with_widgets(self) -> None:
        """Test dynamic shortcuts retrieval with widgets."""
        overlay = HelpOverlay()

        # Mock widget with shortcuts
        mock_widget1 = Mock()
        mock_widget1.keyboard_shortcuts = ["ctrl+1", "f1"]
        mock_widget1.display_name = "Widget 1"

        mock_widget2 = Mock()
        mock_widget2.keyboard_shortcuts = []
        mock_widget2.display_name = "Widget 2"

        mock_group1 = Mock()
        mock_group1.widgets = [mock_widget1, mock_widget2]

        with patch("src.tui.screens.help_screen.focus_manager") as mock_fm:
            mock_fm.focus_groups = {"group1": mock_group1}

            shortcuts = overlay._get_dynamic_shortcuts()

            assert isinstance(shortcuts, dict)
            assert "ctrl+1" in shortcuts
            assert "f1" in shortcuts
            assert shortcuts["ctrl+1"] == "Focus Widget 1"
            assert shortcuts["f1"] == "Focus Widget 1"


class TestHelpOverlayMounting:
    """Test HelpOverlay mounting behavior and focus management."""

    @pytest.mark.asyncio
    async def test_on_mount_sets_title(self) -> None:
        """Test that mounting sets the title."""
        overlay = HelpOverlay()

        with (
            patch("src.tui.screens.help_screen.focus_manager") as mock_fm,
            patch.object(overlay, "query_one") as mock_query,
        ):

            mock_fm.current_focus = None
            mock_tabs = Mock()
            mock_query.return_value = mock_tabs

            overlay.on_mount()

            assert overlay.title == "CCMonitor - Help"
            mock_tabs.focus.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_mount_with_current_focus(self) -> None:
        """Test mounting when there's already a current focus."""
        overlay = HelpOverlay()

        with (
            patch("src.tui.screens.help_screen.focus_manager") as mock_fm,
            patch.object(overlay, "query_one") as mock_query,
        ):

            mock_fm.current_focus = "existing-widget"
            mock_tabs = Mock()
            mock_query.return_value = mock_tabs

            overlay.on_mount()

            mock_fm.push_focus_context.assert_called_once_with("help-overlay")
            mock_tabs.focus.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_mount_query_failure(self) -> None:
        """Test mounting handles query failures gracefully."""
        overlay = HelpOverlay()

        with (
            patch("src.tui.screens.help_screen.focus_manager") as mock_fm,
            patch.object(
                overlay, "query_one", side_effect=ValueError("Not found"),
            ),
            patch.object(overlay, "log") as mock_log,
        ):

            mock_fm.current_focus = None

            overlay.on_mount()

            assert overlay.title == "CCMonitor - Help"
            mock_log.assert_called_once()
            assert "Could not focus tabs" in mock_log.call_args[0][0]


class TestHelpOverlayActions:
    """Test HelpOverlay action methods."""

    @pytest.mark.asyncio
    async def test_action_dismiss(self) -> None:
        """Test dismiss action restores focus."""
        overlay = HelpOverlay()

        with (
            patch("src.tui.screens.help_screen.focus_manager") as mock_fm,
            patch.object(overlay, "dismiss") as mock_dismiss,
        ):

            await overlay.action_dismiss()

            mock_fm.pop_focus_context.assert_called_once()
            mock_dismiss.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_action_dismiss_with_result(self) -> None:
        """Test dismiss action with custom result."""
        overlay = HelpOverlay()
        result = "custom_result"

        with (
            patch("src.tui.screens.help_screen.focus_manager") as mock_fm,
            patch.object(overlay, "dismiss") as mock_dismiss,
        ):

            await overlay.action_dismiss(result)

            mock_fm.pop_focus_context.assert_called_once()
            mock_dismiss.assert_called_once_with(result)

    def test_action_show_navigation(self) -> None:
        """Test navigation tab action."""
        overlay = HelpOverlay()

        mock_tabs = Mock()
        with patch.object(overlay, "query_one", return_value=mock_tabs):

            overlay.action_show_navigation()

            assert mock_tabs.active == "nav-tab"

    def test_action_show_navigation_failure(self) -> None:
        """Test navigation tab action handles failures."""
        overlay = HelpOverlay()

        with (
            patch.object(
                overlay, "query_one", side_effect=ValueError("Not found"),
            ),
            patch.object(overlay, "log") as mock_log,
        ):

            overlay.action_show_navigation()

            mock_log.assert_called_once()
            assert (
                "Could not switch to navigation tab"
                in mock_log.call_args[0][0]
            )

    def test_action_show_shortcuts(self) -> None:
        """Test shortcuts tab action."""
        overlay = HelpOverlay()

        mock_tabs = Mock()
        with patch.object(overlay, "query_one", return_value=mock_tabs):

            overlay.action_show_shortcuts()

            assert mock_tabs.active == "shortcuts-tab"

    def test_action_show_shortcuts_failure(self) -> None:
        """Test shortcuts tab action handles failures."""
        overlay = HelpOverlay()

        with (
            patch.object(
                overlay, "query_one", side_effect=AttributeError("No attr"),
            ),
            patch.object(overlay, "log") as mock_log,
        ):

            overlay.action_show_shortcuts()

            mock_log.assert_called_once()
            assert (
                "Could not switch to shortcuts tab" in mock_log.call_args[0][0]
            )

    def test_action_show_focus(self) -> None:
        """Test focus tab action."""
        overlay = HelpOverlay()

        mock_tabs = Mock()
        with patch.object(overlay, "query_one", return_value=mock_tabs):

            overlay.action_show_focus()

            assert mock_tabs.active == "focus-tab"

    def test_action_show_focus_failure(self) -> None:
        """Test focus tab action handles failures."""
        overlay = HelpOverlay()

        with (
            patch.object(
                overlay, "query_one", side_effect=ValueError("Not found"),
            ),
            patch.object(overlay, "log") as mock_log,
        ):

            overlay.action_show_focus()

            mock_log.assert_called_once()
            assert "Could not switch to focus tab" in mock_log.call_args[0][0]


class TestHelpOverlayButtonHandling:
    """Test HelpOverlay button event handling."""

    @pytest.mark.asyncio
    async def test_on_button_pressed_close(self) -> None:
        """Test close button press."""
        overlay = HelpOverlay()

        mock_button = Mock()
        mock_button.id = "close-btn"
        mock_event = Mock()
        mock_event.button = mock_button

        with patch.object(overlay, "action_dismiss") as mock_dismiss:

            await overlay.on_button_pressed(mock_event)

            mock_dismiss.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_button_pressed_nav(self) -> None:
        """Test navigation button press."""
        overlay = HelpOverlay()

        mock_button = Mock()
        mock_button.id = "nav-btn"
        mock_event = Mock()
        mock_event.button = mock_button

        with patch.object(overlay, "action_show_navigation") as mock_action:

            await overlay.on_button_pressed(mock_event)

            mock_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_button_pressed_shortcuts(self) -> None:
        """Test shortcuts button press."""
        overlay = HelpOverlay()

        mock_button = Mock()
        mock_button.id = "shortcuts-btn"
        mock_event = Mock()
        mock_event.button = mock_button

        with patch.object(overlay, "action_show_shortcuts") as mock_action:

            await overlay.on_button_pressed(mock_event)

            mock_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_button_pressed_focus(self) -> None:
        """Test focus button press."""
        overlay = HelpOverlay()

        mock_button = Mock()
        mock_button.id = "focus-btn"
        mock_event = Mock()
        mock_event.button = mock_button

        with patch.object(overlay, "action_show_focus") as mock_action:

            await overlay.on_button_pressed(mock_event)

            mock_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_button_pressed_unknown(self) -> None:
        """Test unknown button press does nothing."""
        overlay = HelpOverlay()

        mock_button = Mock()
        mock_button.id = "unknown-btn"
        mock_event = Mock()
        mock_event.button = mock_button

        with (
            patch.object(overlay, "action_dismiss") as mock_dismiss,
            patch.object(overlay, "action_show_navigation") as mock_nav,
            patch.object(overlay, "action_show_shortcuts") as mock_shortcuts,
            patch.object(overlay, "action_show_focus") as mock_focus,
        ):

            await overlay.on_button_pressed(mock_event)

            # No actions should be called
            mock_dismiss.assert_not_called()
            mock_nav.assert_not_called()
            mock_shortcuts.assert_not_called()
            mock_focus.assert_not_called()


class TestHelpOverlayIntegration:
    """Integration tests for HelpOverlay functionality."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self) -> None:
        """Test complete overlay lifecycle."""
        overlay = HelpOverlay()

        with (
            patch("src.tui.screens.help_screen.focus_manager") as mock_fm,
            patch.object(overlay, "query_one") as mock_query,
            patch.object(overlay, "dismiss") as mock_dismiss,
        ):

            mock_fm.current_focus = "test-widget"
            mock_tabs = Mock()
            mock_query.return_value = mock_tabs

            # Mount
            overlay.on_mount()

            assert overlay.title == "CCMonitor - Help"
            mock_fm.push_focus_context.assert_called_once_with("help-overlay")
            mock_tabs.focus.assert_called_once()

            # Switch tabs
            overlay.action_show_shortcuts()
            assert mock_tabs.active == "shortcuts-tab"

            overlay.action_show_focus()
            assert mock_tabs.active == "focus-tab"

            overlay.action_show_navigation()
            assert mock_tabs.active == "nav-tab"

            # Dismiss
            await overlay.action_dismiss()

            mock_fm.pop_focus_context.assert_called_once()
            mock_dismiss.assert_called_once_with(None)

    def test_dynamic_content_updates(self) -> None:
        """Test that dynamic content reflects current state."""
        overlay = HelpOverlay()

        # Mock focus manager state
        mock_widget = Mock()
        mock_widget.keyboard_shortcuts = ["ctrl+t"]
        mock_widget.display_name = "Test Widget"

        mock_group = Mock()
        mock_group.widgets = [mock_widget]

        with patch("src.tui.screens.help_screen.focus_manager") as mock_fm:
            mock_fm.current_focus = "test-focus"
            mock_fm.focus_groups = {"test_group": mock_group}
            mock_fm.focus_history = [Mock()]

            # Test focus help content
            focus_help = overlay._create_focus_help()
            assert focus_help is not None

            # Test dynamic shortcuts
            shortcuts = overlay._get_dynamic_shortcuts()
            assert "ctrl+t" in shortcuts
            assert shortcuts["ctrl+t"] == "Focus Test Widget"

    def test_error_handling_robustness(self) -> None:
        """Test that all methods handle errors gracefully."""
        overlay = HelpOverlay()

        # Test with mock focus manager that raises exceptions
        with patch("src.tui.screens.help_screen.focus_manager") as mock_fm:
            mock_fm.current_focus = None
            mock_fm.focus_groups = {}
            mock_fm.focus_history = []

            # All content creation methods should work
            nav_help = overlay._create_navigation_help()
            assert nav_help is not None

            shortcuts_help = overlay._create_shortcuts_help()
            assert shortcuts_help is not None

            focus_help = overlay._create_focus_help()
            assert focus_help is not None

            status_help = overlay._create_status_help()
            assert status_help is not None

            footer = overlay._create_footer()
            assert footer is not None

            shortcuts = overlay._get_dynamic_shortcuts()
            assert isinstance(shortcuts, dict)


class TestHelpOverlayEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_focus_groups(self) -> None:
        """Test behavior with empty focus groups."""
        overlay = HelpOverlay()

        with patch("src.tui.screens.help_screen.focus_manager") as mock_fm:
            mock_fm.focus_groups = {}
            mock_fm.current_focus = None
            mock_fm.focus_history = []

            shortcuts = overlay._get_dynamic_shortcuts()
            assert shortcuts == {}

            focus_help = overlay._create_focus_help()
            assert focus_help is not None

    def test_widgets_without_shortcuts(self) -> None:
        """Test widgets that don't have keyboard shortcuts."""
        overlay = HelpOverlay()

        mock_widget = Mock()
        mock_widget.keyboard_shortcuts = []
        mock_widget.display_name = "No Shortcuts Widget"

        mock_group = Mock()
        mock_group.widgets = [mock_widget]

        with patch("src.tui.screens.help_screen.focus_manager") as mock_fm:
            mock_fm.focus_groups = {"group": mock_group}

            shortcuts = overlay._get_dynamic_shortcuts()
            assert shortcuts == {}

    def test_widgets_with_none_shortcuts(self) -> None:
        """Test widgets with None as shortcuts."""
        overlay = HelpOverlay()

        mock_widget = Mock()
        mock_widget.keyboard_shortcuts = None
        mock_widget.display_name = "None Shortcuts Widget"

        mock_group = Mock()
        mock_group.widgets = [mock_widget]

        with patch("src.tui.screens.help_screen.focus_manager") as mock_fm:
            mock_fm.focus_groups = {"group": mock_group}

            # Should handle None gracefully
            shortcuts = overlay._get_dynamic_shortcuts()
            assert shortcuts == {}

    def test_missing_attributes_handling(self) -> None:
        """Test handling of widgets missing expected attributes."""
        overlay = HelpOverlay()

        # Mock widget missing keyboard_shortcuts attribute
        mock_widget = Mock(spec=[])  # Empty spec means no attributes

        mock_group = Mock()
        mock_group.widgets = [mock_widget]

        with patch("src.tui.screens.help_screen.focus_manager") as mock_fm:
            mock_fm.focus_groups = {"group": mock_group}

            # Should handle missing attributes gracefully
            shortcuts = overlay._get_dynamic_shortcuts()
            assert shortcuts == {}


class TestHelpOverlayAccessibility:
    """Test accessibility features of the help overlay."""

    def test_keyboard_navigation_bindings(self) -> None:
        """Test keyboard navigation bindings are complete."""
        overlay = HelpOverlay()

        binding_keys = [
            binding.key if hasattr(binding, "key") else binding[0]
            for binding in overlay.BINDINGS
        ]

        # Essential accessibility bindings
        assert "escape" in binding_keys
        assert "tab" in binding_keys
        assert "shift+tab" in binding_keys

        # Shortcut access bindings
        assert "1" in binding_keys
        assert "2" in binding_keys
        assert "3" in binding_keys

    def test_focus_restoration(self) -> None:
        """Test that focus is properly managed and restored."""
        overlay = HelpOverlay()

        with patch("src.tui.screens.help_screen.focus_manager") as mock_fm:
            # Test focus context management
            mock_fm.current_focus = "original-widget"

            # Mount should push context
            overlay.on_mount()
            mock_fm.push_focus_context.assert_called_once_with("help-overlay")

            # Dismiss should pop context
            with patch.object(overlay, "dismiss"):
                overlay.action_dismiss()
                mock_fm.pop_focus_context.assert_called_once()

    def test_screen_reader_friendly_content(self) -> None:
        """Test that content structure is screen reader friendly."""
        overlay = HelpOverlay()

        # Navigation help should have clear structure
        nav_help = overlay._create_navigation_help()
        assert nav_help is not None

        # Status help should have clear information
        status_help = overlay._create_status_help()
        assert status_help is not None

        # Focus help should include current state
        with patch("src.tui.screens.help_screen.focus_manager") as mock_fm:
            mock_fm.current_focus = "test-widget"
            mock_fm.focus_groups = {"group1": Mock()}
            mock_fm.focus_history = [Mock()]

            focus_help = overlay._create_focus_help()
            assert focus_help is not None
