"""Comprehensive tests for MainScreen TUI component.

This module provides complete test coverage for the MainScreen class,
including composition, mounting, focus management, responsive behavior,
keyboard actions, and integration with the focus management system.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from src.tui.screens.main_screen import MainScreen
from src.tui.utils.responsive import ScreenSize


class TestMainScreenInitialization:
    """Test MainScreen initialization and basic properties."""

    def test_default_initialization(self) -> None:
        """Test MainScreen with default parameters."""
        screen = MainScreen()

        assert screen is not None
        assert screen.title is None  # Set during mount

    def test_css_defined(self) -> None:
        """Test that CSS is properly defined."""
        screen = MainScreen()

        assert screen.DEFAULT_CSS is not None
        assert len(screen.DEFAULT_CSS) > 0
        assert "MainScreen" in screen.DEFAULT_CSS
        assert "#main-container" in screen.DEFAULT_CSS

    def test_bindings_defined(self) -> None:
        """Test that key bindings are properly defined."""
        screen = MainScreen()

        assert screen.BINDINGS is not None
        assert len(screen.BINDINGS) > 0

        # Check for expected bindings
        binding_keys = [
            binding.key if hasattr(binding, "key") else binding[0]
            for binding in screen.BINDINGS
        ]
        expected_keys = [
            "tab",
            "shift+tab",
            "ctrl+1",
            "ctrl+2",
            "f1",
            "f2",
            "escape",
            "ctrl+h",
            "?",
            "ctrl+r",
            "f5",
            "enter",
            "space",
        ]

        for key in expected_keys:
            assert key in binding_keys


class TestMainScreenComposition:
    """Test MainScreen compose method and layout structure."""

    def test_compose_creates_layout(self) -> None:
        """Test that compose creates the expected layout structure."""
        screen = MainScreen()

        widgets = list(screen.compose())

        # Should have the main vertical container
        assert len(widgets) >= 1

        # Test that compose doesn't raise exceptions
        assert widgets is not None

    def test_layout_structure(self) -> None:
        """Test the layout structure is properly composed."""
        screen = MainScreen()

        # Mock the widget classes to avoid Textual dependencies
        with (
            patch(
                "src.tui.screens.main_screen.CCMonitorHeader",
            ) as mock_header,
            patch(
                "src.tui.screens.main_screen.CCMonitorFooter",
            ) as mock_footer,
            patch(
                "src.tui.screens.main_screen.ProjectsPanel",
            ) as mock_projects,
            patch("src.tui.screens.main_screen.LiveFeedPanel") as mock_feed,
        ):

            mock_header.return_value = Mock()
            mock_footer.return_value = Mock()
            mock_projects.return_value = Mock()
            mock_feed.return_value = Mock()

            list(screen.compose())

            # Should have created the required widgets
            mock_header.assert_called_once()
            mock_footer.assert_called_once()
            mock_projects.assert_called_once()
            mock_feed.assert_called_once()

            # Check widget configuration
            projects_call = mock_projects.call_args
            assert projects_call[1]["id"] == "projects-panel"
            assert projects_call[1]["classes"] == "slide-in-left"

            feed_call = mock_feed.call_args
            assert feed_call[1]["id"] == "live-feed-panel"
            assert feed_call[1]["classes"] == "slide-in-right"


class TestMainScreenMounting:
    """Test MainScreen mounting behavior and initialization."""

    def test_on_mount_sets_title(self) -> None:
        """Test that mounting sets the screen title."""
        screen = MainScreen()

        with (
            patch.object(
                screen,
                "_setup_responsive_behavior",
            ) as mock_responsive,
            patch.object(
                screen,
                "_setup_focus_management",
            ) as mock_focus_setup,
            patch.object(screen, "_initialize_focus") as mock_init_focus,
        ):

            screen.on_mount()

            assert screen.title == "CCMonitor - Live Monitoring"
            mock_responsive.assert_called_once()
            mock_focus_setup.assert_called_once()
            mock_init_focus.assert_called_once()

    def test_setup_focus_management(self) -> None:
        """Test focus management setup."""
        screen = MainScreen()

        with (
            patch(
                "src.tui.screens.main_screen.create_panel_focus_group",
            ) as mock_create,
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
        ):

            mock_projects_group = Mock()
            mock_feed_group = Mock()
            mock_create.side_effect = [mock_projects_group, mock_feed_group]

            screen._setup_focus_management()

            # Should create two focus groups
            expected_group_count = 2
            assert mock_create.call_count == expected_group_count

            # Check projects group creation
            projects_call = mock_create.call_args_list[0]
            assert projects_call[0] == ("Projects", "projects-panel")
            expected_projects_priority = 10
            assert projects_call[1]["priority"] == expected_projects_priority
            assert projects_call[1]["shortcuts"] == ["ctrl+p", "1"]

            # Check feed group creation
            feed_call = mock_create.call_args_list[1]
            assert feed_call[0] == ("Live Feed", "live-feed-panel")
            expected_feed_priority = 9
            assert feed_call[1]["priority"] == expected_feed_priority
            assert feed_call[1]["shortcuts"] == ["ctrl+f", "2"]

            # Should register both groups
            mock_fm.register_focus_group.assert_any_call(mock_projects_group)
            mock_fm.register_focus_group.assert_any_call(mock_feed_group)

    def test_initialize_focus_success(self) -> None:
        """Test successful focus initialization."""
        screen = MainScreen()

        mock_app = Mock()
        screen.app = mock_app

        with (
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
            patch.object(screen, "query_one") as mock_query,
        ):

            mock_fm.focus_first_available.return_value = "projects-panel"
            mock_widget = Mock()
            mock_query.return_value = mock_widget

            screen._initialize_focus()

            mock_fm.set_app.assert_called_once_with(mock_app)
            mock_fm.focus_first_available.assert_called_once()
            mock_query.assert_called_once_with("#projects-panel")
            mock_widget.focus.assert_called_once()
            mock_fm.apply_visual_focus.assert_called_once_with(
                "projects-panel",
                focused=True,
            )

    def test_initialize_focus_fallback(self) -> None:
        """Test focus initialization fallback behavior."""
        screen = MainScreen()

        mock_app = Mock()
        screen.app = mock_app

        with (
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
            patch.object(screen, "_fallback_focus") as mock_fallback,
        ):

            mock_fm.focus_first_available.return_value = None

            screen._initialize_focus()

            mock_fallback.assert_called_once()

    def test_fallback_focus_success(self) -> None:
        """Test fallback focus mechanism."""
        screen = MainScreen()

        with (
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
            patch.object(screen, "query_one") as mock_query,
        ):

            mock_panel = Mock()
            mock_query.return_value = mock_panel

            screen._fallback_focus()

            mock_query.assert_called_once_with("#projects-panel")
            mock_panel.focus.assert_called_once()
            mock_fm.set_focus.assert_called_once_with("projects-panel")

    def test_fallback_focus_ultimate_fallback(self) -> None:
        """Test ultimate fallback when all else fails."""
        screen = MainScreen()

        with (
            patch.object(
                screen,
                "query_one",
                side_effect=ValueError("Not found"),
            ),
            patch.object(screen, "focus_next") as mock_focus_next,
            patch.object(screen, "log") as mock_log,
        ):

            screen._fallback_focus()

            mock_log.assert_called_once()
            mock_focus_next.assert_called_once()

    def test_setup_responsive_behavior(self) -> None:
        """Test responsive behavior setup."""
        screen = MainScreen()
        screen.size = (120, 30)  # Mock terminal size

        with patch(
            "src.tui.screens.main_screen.responsive_manager",
        ) as mock_rm:

            screen._setup_responsive_behavior()

            mock_rm.handle_resize.assert_called_once_with(120, 30)


class TestMainScreenPanelActions:
    """Test panel focus and action methods."""

    def test_focus_projects_panel(self) -> None:
        """Test focusing projects panel."""
        screen = MainScreen()

        with patch.object(screen, "_focus_panel_safely") as mock_focus:

            screen.action_focus_projects_panel()

            mock_focus.assert_called_once_with("projects-panel")

    def test_focus_feed_panel(self) -> None:
        """Test focusing feed panel."""
        screen = MainScreen()

        with patch.object(screen, "_focus_panel_safely") as mock_focus:

            screen.action_focus_feed_panel()

            mock_focus.assert_called_once_with("live-feed-panel")

    def test_focus_panel_safely_success(self) -> None:
        """Test successful panel focusing."""
        screen = MainScreen()

        with (
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
            patch.object(screen, "query_one") as mock_query,
        ):

            mock_widget = Mock()
            mock_query.return_value = mock_widget

            screen._focus_panel_safely("test-panel")

            mock_query.assert_called_once_with("#test-panel")
            mock_widget.focus.assert_called_once()
            mock_fm.set_focus.assert_called_once_with("test-panel")

    def test_focus_panel_safely_error_handling(self) -> None:
        """Test panel focusing error handling."""
        screen = MainScreen()
        screen.app = Mock()

        with (
            patch.object(
                screen,
                "query_one",
                side_effect=ValueError("Not found"),
            ),
            patch.object(screen, "log") as mock_log,
        ):

            screen._focus_panel_safely("invalid-panel")

            screen.app.bell.assert_called_once()
            mock_log.assert_called_once()

    def test_refresh_view(self) -> None:
        """Test view refresh functionality."""
        screen = MainScreen()

        mock_projects_panel = Mock()
        mock_feed_panel = Mock()
        mock_projects_panel.refresh = Mock()
        mock_feed_panel.refresh = Mock()

        with (
            patch.object(screen, "query_one") as mock_query,
            patch.object(screen, "notify") as mock_notify,
        ):

            mock_query.side_effect = [mock_projects_panel, mock_feed_panel]

            screen.action_refresh_view()

            mock_notify.assert_called_once_with("Refreshing main screen...")
            mock_projects_panel.refresh.assert_called_once()
            mock_feed_panel.refresh.assert_called_once()

    def test_refresh_view_error_handling(self) -> None:
        """Test refresh view error handling."""
        screen = MainScreen()

        with (
            patch.object(
                screen,
                "query_one",
                side_effect=ValueError("Not found"),
            ),
            patch.object(screen, "notify") as mock_notify,
            patch.object(screen, "log") as mock_log,
        ):

            screen.action_refresh_view()

            mock_notify.assert_called_once()
            mock_log.assert_called_once()

    def test_show_help(self) -> None:
        """Test help screen display."""
        screen = MainScreen()
        screen.app = Mock()

        with (
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
            patch("src.tui.screens.main_screen.HelpOverlay") as mock_help,
        ):

            mock_fm.current_focus = "test-widget"
            mock_help_screen = Mock()
            mock_help.return_value = mock_help_screen

            screen.action_show_help()

            mock_fm.push_focus_context.assert_called_once_with("help-overlay")
            mock_help.assert_called_once()
            screen.app.push_screen.assert_called_once_with(mock_help_screen)

    def test_show_help_no_current_focus(self) -> None:
        """Test help screen display with no current focus."""
        screen = MainScreen()
        screen.app = Mock()

        with (
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
            patch("src.tui.screens.main_screen.HelpOverlay") as mock_help,
        ):

            mock_fm.current_focus = None
            mock_help_screen = Mock()
            mock_help.return_value = mock_help_screen

            screen.action_show_help()

            mock_fm.push_focus_context.assert_not_called()
            screen.app.push_screen.assert_called_once_with(mock_help_screen)


class TestMainScreenFocusActions:
    """Test focus-related action methods."""

    def test_focus_next_panel(self) -> None:
        """Test focusing next panel."""
        screen = MainScreen()

        with (
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
            patch.object(screen, "_focus_widget_safely") as mock_focus,
        ):

            mock_fm.move_focus.return_value = "next-widget"

            screen.action_focus_next_panel()

            mock_fm.move_focus.assert_called_once()
            mock_focus.assert_called_once_with("next-widget")

    def test_focus_next_panel_fallback(self) -> None:
        """Test focusing next panel fallback."""
        screen = MainScreen()

        with (
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
            patch.object(screen, "focus_next") as mock_focus_next,
        ):

            mock_fm.move_focus.return_value = None

            screen.action_focus_next_panel()

            mock_focus_next.assert_called_once()

    def test_focus_previous_panel(self) -> None:
        """Test focusing previous panel."""
        screen = MainScreen()

        with (
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
            patch.object(screen, "_focus_widget_safely") as mock_focus,
        ):

            mock_fm.move_focus.return_value = "prev-widget"

            screen.action_focus_previous_panel()

            mock_fm.move_focus.assert_called_once()
            mock_focus.assert_called_once_with("prev-widget")

    def test_focus_previous_panel_fallback(self) -> None:
        """Test focusing previous panel fallback."""
        screen = MainScreen()

        with (
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
            patch.object(screen, "focus_previous") as mock_focus_prev,
        ):

            mock_fm.move_focus.return_value = None

            screen.action_focus_previous_panel()

            mock_focus_prev.assert_called_once()

    def test_focus_first_panel(self) -> None:
        """Test focusing first panel."""
        screen = MainScreen()

        with (
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
            patch.object(screen, "_focus_widget_safely") as mock_focus,
        ):

            mock_fm.move_focus.return_value = "first-widget"

            screen.action_focus_first_panel()

            mock_focus.assert_called_once_with("first-widget")

    def test_focus_last_panel(self) -> None:
        """Test focusing last panel."""
        screen = MainScreen()

        with (
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
            patch.object(screen, "_focus_widget_safely") as mock_focus,
        ):

            mock_fm.move_focus.return_value = "last-widget"

            screen.action_focus_last_panel()

            mock_focus.assert_called_once_with("last-widget")

    def test_focus_widget_safely_success(self) -> None:
        """Test successful widget focusing."""
        screen = MainScreen()

        with patch.object(screen, "query_one") as mock_query:

            mock_widget = Mock()
            mock_query.return_value = mock_widget

            screen._focus_widget_safely("test-widget")

            mock_query.assert_called_once_with("#test-widget")
            mock_widget.focus.assert_called_once()

    def test_focus_widget_safely_error(self) -> None:
        """Test widget focusing error handling."""
        screen = MainScreen()
        screen.app = Mock()

        with (
            patch.object(
                screen,
                "query_one",
                side_effect=ValueError("Not found"),
            ),
            patch.object(screen, "log") as mock_log,
        ):

            screen._focus_widget_safely("invalid-widget")

            mock_log.assert_called_once()
            screen.app.bell.assert_called_once()


class TestMainScreenNavigationActions:
    """Test navigation action methods."""

    def test_navigate_up_with_cursor_action(self) -> None:
        """Test navigate up with cursor action support."""
        screen = MainScreen()

        mock_focused = Mock()
        mock_focused.action_cursor_up = Mock()
        screen.focused = mock_focused

        screen.action_navigate_up()

        mock_focused.action_cursor_up.assert_called_once()

    def test_navigate_up_with_focus_manager(self) -> None:
        """Test navigate up using focus manager."""
        screen = MainScreen()
        screen.focused = Mock()  # Mock focused widget without cursor action

        with (
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
            patch.object(screen, "_focus_widget_safely") as mock_focus,
        ):

            mock_fm.move_focus.return_value = "up-widget"

            screen.action_navigate_up()

            mock_focus.assert_called_once_with("up-widget")

    def test_navigate_down_with_cursor_action(self) -> None:
        """Test navigate down with cursor action support."""
        screen = MainScreen()

        mock_focused = Mock()
        mock_focused.action_cursor_down = Mock()
        screen.focused = mock_focused

        screen.action_navigate_down()

        mock_focused.action_cursor_down.assert_called_once()

    def test_navigate_down_with_focus_manager(self) -> None:
        """Test navigate down using focus manager."""
        screen = MainScreen()
        screen.focused = Mock()  # Mock focused widget without cursor action

        with (
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
            patch.object(screen, "_focus_widget_safely") as mock_focus,
        ):

            mock_fm.move_focus.return_value = "down-widget"

            screen.action_navigate_down()

            mock_focus.assert_called_once_with("down-widget")

    def test_navigate_left(self) -> None:
        """Test navigate left action."""
        screen = MainScreen()

        with patch.object(screen, "action_focus_previous_panel") as mock_prev:

            screen.action_navigate_left()

            mock_prev.assert_called_once()

    def test_navigate_right(self) -> None:
        """Test navigate right action."""
        screen = MainScreen()

        with patch.object(screen, "action_focus_next_panel") as mock_next:

            screen.action_navigate_right()

            mock_next.assert_called_once()

    def test_page_up_with_action(self) -> None:
        """Test page up with action support."""
        screen = MainScreen()

        mock_focused = Mock()
        mock_focused.action_page_up = Mock()
        screen.focused = mock_focused

        screen.action_page_up()

        mock_focused.action_page_up.assert_called_once()

    def test_page_up_fallback(self) -> None:
        """Test page up fallback behavior."""
        screen = MainScreen()
        screen.focused = Mock()  # Mock without page_up action

        with patch.object(screen, "scroll_up") as mock_scroll:

            screen.action_page_up()

            mock_scroll.assert_called_once_with(animate=False)

    def test_page_down_with_action(self) -> None:
        """Test page down with action support."""
        screen = MainScreen()

        mock_focused = Mock()
        mock_focused.action_page_down = Mock()
        screen.focused = mock_focused

        screen.action_page_down()

        mock_focused.action_page_down.assert_called_once()

    def test_page_down_fallback(self) -> None:
        """Test page down fallback behavior."""
        screen = MainScreen()
        screen.focused = Mock()  # Mock without page_down action

        with patch.object(screen, "scroll_down") as mock_scroll:

            screen.action_page_down()

            mock_scroll.assert_called_once_with(animate=False)


class TestMainScreenSelectionActions:
    """Test selection and item interaction actions."""

    def test_select_item_with_action(self) -> None:
        """Test select item with action support."""
        screen = MainScreen()

        mock_focused = Mock()
        mock_focused.action_select_cursor = Mock()
        screen.focused = mock_focused

        screen.action_select_item()

        mock_focused.action_select_cursor.assert_called_once()

    def test_select_item_without_action(self) -> None:
        """Test select item without specific action."""
        screen = MainScreen()
        screen.focused = Mock()  # Mock without select action

        # Should not raise exception
        screen.action_select_item()

    def test_toggle_item_with_action(self) -> None:
        """Test toggle item with action support."""
        screen = MainScreen()

        mock_focused = Mock()
        mock_focused.action_toggle_cursor = Mock()
        screen.focused = mock_focused

        screen.action_toggle_item()

        mock_focused.action_toggle_cursor.assert_called_once()

    def test_toggle_item_without_action(self) -> None:
        """Test toggle item without specific action."""
        screen = MainScreen()
        screen.focused = Mock()  # Mock without toggle action

        # Should not raise exception
        screen.action_toggle_item()


class TestMainScreenEscapeHandling:
    """Test escape key and navigation back handling."""

    def test_handle_escape_with_focus_manager(self) -> None:
        """Test escape handling via focus manager."""
        screen = MainScreen()

        with patch("src.tui.screens.main_screen.focus_manager") as mock_fm:

            mock_fm.handle_escape_context.return_value = True

            screen.action_handle_escape()

            mock_fm.handle_escape_context.assert_called_once()

    def test_handle_escape_fallback_blur(self) -> None:
        """Test escape handling fallback behavior."""
        screen = MainScreen()

        mock_focused = Mock()
        screen.focused = mock_focused

        with patch("src.tui.screens.main_screen.focus_manager") as mock_fm:

            mock_fm.handle_escape_context.return_value = False

            screen.action_handle_escape()

            mock_focused.blur.assert_called_once()

    def test_handle_escape_ultimate_fallback(self) -> None:
        """Test escape handling ultimate fallback."""
        screen = MainScreen()
        screen.app = Mock()
        screen.focused = None

        with patch("src.tui.screens.main_screen.focus_manager") as mock_fm:

            mock_fm.handle_escape_context.return_value = False

            screen.action_handle_escape()

            screen.app.bell.assert_called_once()

    def test_navigate_back_success(self) -> None:
        """Test navigate back with history."""
        screen = MainScreen()

        with (
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
            patch.object(screen, "_focus_widget_safely") as mock_focus,
        ):

            mock_fm.focus_previous_in_history.return_value = "prev-widget"

            screen.action_navigate_back()

            mock_focus.assert_called_once_with("prev-widget")

    def test_navigate_back_fallback(self) -> None:
        """Test navigate back fallback to escape."""
        screen = MainScreen()

        with (
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
            patch.object(screen, "action_handle_escape") as mock_escape,
        ):

            mock_fm.focus_previous_in_history.return_value = None

            screen.action_navigate_back()

            mock_escape.assert_called_once()


class TestMainScreenResponsiveLayout:
    """Test responsive layout functionality."""

    @pytest.mark.asyncio
    async def test_on_resize_basic(self) -> None:
        """Test basic resize event handling."""
        screen = MainScreen()

        mock_event = Mock()
        mock_event.size = (120, 30)

        with (
            patch("src.tui.screens.main_screen.responsive_manager") as mock_rm,
            patch.object(screen, "_apply_responsive_layout") as mock_apply,
            patch.object(screen, "notify") as mock_notify,
        ):

            mock_rm.breakpoints.get_screen_size.return_value = (
                ScreenSize.MEDIUM
            )

            await screen.on_resize(mock_event)

            mock_rm.handle_resize.assert_called_once_with(120, 30)
            mock_rm.breakpoints.get_screen_size.assert_called_once_with(120)
            mock_apply.assert_called_once_with(ScreenSize.MEDIUM, 120, 30)
            mock_notify.assert_not_called()  # No warning for adequate size

    @pytest.mark.asyncio
    async def test_on_resize_small_terminal_warning(self) -> None:
        """Test resize handling with small terminal warning."""
        screen = MainScreen()

        mock_event = Mock()
        mock_event.size = (60, 20)  # Below minimum

        with (
            patch("src.tui.screens.main_screen.responsive_manager") as mock_rm,
            patch.object(screen, "_apply_responsive_layout") as mock_apply,
            patch.object(screen, "notify") as mock_notify,
        ):

            mock_rm.breakpoints.get_screen_size.return_value = ScreenSize.TINY

            await screen.on_resize(mock_event)

            # Should show size warning
            mock_notify.assert_called_once()
            assert "Terminal size: 60x20" in mock_notify.call_args[0][0]
            assert mock_notify.call_args[1]["severity"] == "warning"

    @pytest.mark.asyncio
    async def test_apply_responsive_layout_vertical(self) -> None:
        """Test applying vertical responsive layout."""
        screen = MainScreen()

        mock_content = Mock()
        mock_projects = Mock()
        mock_feed = Mock()

        with (
            patch.object(screen, "query_one") as mock_query,
            patch("src.tui.screens.main_screen.responsive_manager") as mock_rm,
            patch.object(screen, "_apply_vertical_layout") as mock_vert,
            patch.object(screen, "_notify_layout_change") as mock_notify,
        ):

            mock_query.side_effect = [mock_content, mock_projects, mock_feed]
            mock_rm.should_stack_vertically.return_value = True

            await screen._apply_responsive_layout(ScreenSize.SMALL, 80, 24)

            mock_vert.assert_called_once_with(
                ScreenSize.SMALL,
                mock_projects,
                mock_feed,
            )
            mock_content.styles.layout = "vertical"
            mock_notify.assert_called_once_with(ScreenSize.SMALL, 80, 24)

    @pytest.mark.asyncio
    async def test_apply_responsive_layout_horizontal(self) -> None:
        """Test applying horizontal responsive layout."""
        screen = MainScreen()

        mock_content = Mock()
        mock_projects = Mock()
        mock_feed = Mock()

        with (
            patch.object(screen, "query_one") as mock_query,
            patch("src.tui.screens.main_screen.responsive_manager") as mock_rm,
            patch.object(screen, "_apply_horizontal_layout") as mock_horiz,
            patch.object(screen, "_notify_layout_change") as mock_notify,
        ):

            mock_query.side_effect = [mock_content, mock_projects, mock_feed]
            mock_rm.should_stack_vertically.return_value = False

            await screen._apply_responsive_layout(ScreenSize.LARGE, 150, 40)

            mock_horiz.assert_called_once_with(
                ScreenSize.LARGE,
                mock_projects,
                mock_feed,
            )
            mock_content.styles.layout = "horizontal"
            mock_notify.assert_called_once_with(ScreenSize.LARGE, 150, 40)

    @pytest.mark.asyncio
    async def test_apply_responsive_layout_error_handling(self) -> None:
        """Test responsive layout error handling."""
        screen = MainScreen()

        with (
            patch.object(
                screen,
                "query_one",
                side_effect=ValueError("Not found"),
            ),
            patch.object(screen, "log") as mock_log,
        ):

            await screen._apply_responsive_layout(ScreenSize.MEDIUM, 120, 30)

            mock_log.assert_called_once()

    def test_apply_vertical_layout_tiny(self) -> None:
        """Test vertical layout configuration for tiny screens."""
        screen = MainScreen()

        mock_projects = Mock()
        mock_feed = Mock()

        screen._apply_vertical_layout(
            ScreenSize.TINY,
            mock_projects,
            mock_feed,
        )

        mock_projects.styles.width = "100%"
        mock_projects.styles.height = "8"
        mock_feed.styles.width = "100%"
        mock_feed.styles.height = "1fr"

    def test_apply_vertical_layout_small(self) -> None:
        """Test vertical layout configuration for small screens."""
        screen = MainScreen()

        mock_projects = Mock()
        mock_feed = Mock()

        screen._apply_vertical_layout(
            ScreenSize.SMALL,
            mock_projects,
            mock_feed,
        )

        mock_projects.styles.width = "100%"
        mock_projects.styles.height = "12"
        mock_feed.styles.width = "100%"
        mock_feed.styles.height = "1fr"

    def test_apply_horizontal_layout_medium(self) -> None:
        """Test horizontal layout configuration for medium screens."""
        screen = MainScreen()

        mock_projects = Mock()
        mock_feed = Mock()

        screen._apply_horizontal_layout(
            ScreenSize.MEDIUM,
            mock_projects,
            mock_feed,
        )

        mock_feed.styles.height = "1fr"
        mock_projects.styles.height = "1fr"
        mock_feed.styles.width = "1fr"
        mock_projects.styles.width = "25%"

    def test_apply_horizontal_layout_large(self) -> None:
        """Test horizontal layout configuration for large screens."""
        screen = MainScreen()

        mock_projects = Mock()
        mock_feed = Mock()

        screen._apply_horizontal_layout(
            ScreenSize.LARGE,
            mock_projects,
            mock_feed,
        )

        mock_feed.styles.height = "1fr"
        mock_projects.styles.height = "1fr"
        mock_feed.styles.width = "1fr"
        mock_projects.styles.width = "20%"

    def test_apply_horizontal_layout_xlarge(self) -> None:
        """Test horizontal layout configuration for xlarge screens."""
        screen = MainScreen()

        mock_projects = Mock()
        mock_feed = Mock()

        # Test with xlarge (anything not MEDIUM or LARGE)
        screen._apply_horizontal_layout(
            ScreenSize.XLARGE,
            mock_projects,
            mock_feed,
        )

        mock_projects.styles.width = "300px"

    def test_notify_layout_change_vertical_modes(self) -> None:
        """Test layout change notifications for vertical modes."""
        screen = MainScreen()

        with patch.object(screen, "notify") as mock_notify:

            # Test tiny screen notification
            screen._notify_layout_change(ScreenSize.TINY, 60, 20)
            mock_notify.assert_called_once()
            assert (
                "Layout: Vertical mode (60x20)" in mock_notify.call_args[0][0]
            )
            assert mock_notify.call_args[1]["severity"] == "information"

            mock_notify.reset_mock()

            # Test small screen notification
            screen._notify_layout_change(ScreenSize.SMALL, 80, 24)
            mock_notify.assert_called_once()

    def test_notify_layout_change_no_notification(self) -> None:
        """Test no notification for larger screens."""
        screen = MainScreen()

        with patch.object(screen, "notify") as mock_notify:

            screen._notify_layout_change(ScreenSize.LARGE, 150, 40)
            mock_notify.assert_not_called()


class TestMainScreenFocusEvents:
    """Test focus and blur event handling."""

    def test_on_focus_with_widget_id(self) -> None:
        """Test focus event handling with widget ID."""
        screen = MainScreen()

        mock_event = Mock()
        mock_widget = Mock()
        mock_widget.id = "test-widget"
        mock_event.widget = mock_widget

        with patch("src.tui.screens.main_screen.focus_manager") as mock_fm:

            screen.on_focus(mock_event)

            mock_fm.set_focus.assert_called_once_with("test-widget")

    def test_on_focus_without_widget_id(self) -> None:
        """Test focus event handling without widget ID."""
        screen = MainScreen()

        mock_event = Mock()
        mock_widget = Mock()
        mock_widget.id = None
        mock_event.widget = mock_widget

        with patch("src.tui.screens.main_screen.focus_manager") as mock_fm:

            screen.on_focus(mock_event)

            mock_fm.set_focus.assert_not_called()

    def test_on_focus_missing_attributes(self) -> None:
        """Test focus event handling with missing attributes."""
        screen = MainScreen()

        mock_event = Mock(spec=[])  # No attributes

        with patch("src.tui.screens.main_screen.focus_manager") as mock_fm:

            # Should not raise exception
            screen.on_focus(mock_event)

            mock_fm.set_focus.assert_not_called()

    def test_on_blur_with_widget_id(self) -> None:
        """Test blur event handling with widget ID."""
        screen = MainScreen()

        mock_event = Mock()
        mock_widget = Mock()
        mock_widget.id = "test-widget"
        mock_event.widget = mock_widget

        with patch("src.tui.screens.main_screen.focus_manager") as mock_fm:

            screen.on_blur(mock_event)

            mock_fm.apply_visual_focus.assert_called_once_with(
                "test-widget",
                focused=False,
            )

    def test_on_blur_without_widget_id(self) -> None:
        """Test blur event handling without widget ID."""
        screen = MainScreen()

        mock_event = Mock()
        mock_widget = Mock()
        mock_widget.id = None
        mock_event.widget = mock_widget

        with patch("src.tui.screens.main_screen.focus_manager") as mock_fm:

            screen.on_blur(mock_event)

            mock_fm.apply_visual_focus.assert_not_called()

    def test_on_unmount_cleanup(self) -> None:
        """Test cleanup when screen is unmounted."""
        screen = MainScreen()

        with patch("src.tui.screens.main_screen.focus_manager") as mock_fm:

            screen.on_unmount()

            mock_fm.clear_all.assert_called_once()


class TestMainScreenIntegration:
    """Integration tests for MainScreen functionality."""

    def test_complete_initialization_flow(self) -> None:
        """Test complete initialization workflow."""
        screen = MainScreen()
        screen.app = Mock()
        screen.size = (120, 30)

        with (
            patch(
                "src.tui.screens.main_screen.create_panel_focus_group",
            ) as mock_create,
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
            patch("src.tui.screens.main_screen.responsive_manager") as mock_rm,
            patch.object(screen, "query_one") as mock_query,
        ):

            # Setup mocks
            mock_create.side_effect = [Mock(), Mock()]
            mock_fm.focus_first_available.return_value = "projects-panel"
            mock_widget = Mock()
            mock_query.return_value = mock_widget

            # Run complete initialization
            screen.on_mount()

            # Verify initialization steps
            assert screen.title == "CCMonitor - Live Monitoring"
            mock_rm.handle_resize.assert_called_once_with(120, 30)
            expected_group_count = 2
            assert (
                mock_fm.register_focus_group.call_count == expected_group_count
            )
            mock_fm.set_app.assert_called_once()
            mock_widget.focus.assert_called_once()

    def test_comprehensive_action_flow(self) -> None:
        """Test comprehensive action workflow."""
        screen = MainScreen()
        screen.app = Mock()

        with (
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
            patch.object(screen, "query_one") as mock_query,
        ):

            mock_widget = Mock()
            mock_query.return_value = mock_widget
            mock_fm.move_focus.return_value = "next-panel"

            # Test action sequence
            screen.action_focus_next_panel()
            screen.action_refresh_view()
            screen.action_show_help()

            # Verify actions executed
            mock_fm.move_focus.assert_called()
            mock_query.assert_called()
            screen.app.push_screen.assert_called_once()

    @pytest.mark.asyncio
    async def test_responsive_behavior_integration(self) -> None:
        """Test responsive behavior integration."""
        screen = MainScreen()

        mock_event = Mock()
        mock_event.size = (60, 20)  # Small size

        with (
            patch("src.tui.screens.main_screen.responsive_manager") as mock_rm,
            patch.object(screen, "query_one") as mock_query,
            patch.object(screen, "notify") as mock_notify,
        ):

            mock_rm.breakpoints.get_screen_size.return_value = ScreenSize.TINY
            mock_rm.should_stack_vertically.return_value = True
            mock_content = Mock()
            mock_projects = Mock()
            mock_feed = Mock()
            mock_query.side_effect = [mock_content, mock_projects, mock_feed]

            await screen.on_resize(mock_event)

            # Should handle small screen appropriately
            mock_notify.assert_called()
            mock_rm.handle_resize.assert_called_with(60, 20)


class TestMainScreenEdgeCases:
    """Test edge cases and error conditions."""

    def test_initialization_with_missing_widgets(self) -> None:
        """Test initialization when required widgets are missing."""
        screen = MainScreen()
        screen.app = Mock()

        with (
            patch("src.tui.screens.main_screen.focus_manager") as mock_fm,
            patch.object(
                screen,
                "query_one",
                side_effect=ValueError("Not found"),
            ),
            patch.object(screen, "focus_next") as mock_focus_next,
        ):

            mock_fm.focus_first_available.return_value = "projects-panel"

            screen._initialize_focus()

            # Should fall back to ultimate fallback
            mock_focus_next.assert_called_once()

    def test_action_methods_with_no_focused_widget(self) -> None:
        """Test action methods when no widget is focused."""
        screen = MainScreen()
        screen.focused = None

        # Should not raise exceptions
        screen.action_navigate_up()
        screen.action_navigate_down()
        screen.action_page_up()
        screen.action_page_down()
        screen.action_select_item()
        screen.action_toggle_item()

    def test_panel_focusing_with_malformed_ids(self) -> None:
        """Test panel focusing with malformed widget IDs."""
        screen = MainScreen()
        screen.app = Mock()

        with (
            patch.object(
                screen,
                "query_one",
                side_effect=ValueError("Invalid selector"),
            ),
            patch.object(screen, "log") as mock_log,
        ):

            screen._focus_panel_safely("invalid-panel-id")

            mock_log.assert_called_once()
            screen.app.bell.assert_called_once()

    @pytest.mark.asyncio
    async def test_resize_with_extreme_dimensions(self) -> None:
        """Test resize handling with extreme dimensions."""
        screen = MainScreen()

        mock_event = Mock()
        mock_event.size = (10, 5)  # Extremely small

        with (
            patch("src.tui.screens.main_screen.responsive_manager") as mock_rm,
            patch.object(screen, "notify") as mock_notify,
        ):

            mock_rm.breakpoints.get_screen_size.return_value = ScreenSize.TINY

            await screen.on_resize(mock_event)

            # Should handle extreme size gracefully
            mock_notify.assert_called()
            assert "10x5" in mock_notify.call_args[0][0]

    def test_focus_events_with_none_values(self) -> None:
        """Test focus event handling with None values."""
        screen = MainScreen()

        mock_event = Mock()
        mock_event.widget = None

        with patch("src.tui.screens.main_screen.focus_manager") as mock_fm:

            # Should not raise exception
            screen.on_focus(mock_event)
            screen.on_blur(mock_event)

            mock_fm.set_focus.assert_not_called()
            mock_fm.apply_visual_focus.assert_not_called()
