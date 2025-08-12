"""Comprehensive tests for the focus management system."""

from __future__ import annotations

import time
from unittest.mock import Mock

import pytest

from src.tui.utils.focus import (
    FocusableWidget,
    FocusDirection,
    FocusGroup,
    FocusManager,
    create_panel_focus_group,
    focus_manager,
)

# Constants for test values
CUSTOM_PRIORITY = 5
WIDGET_COUNT = 3
PERF_TIME_LIMIT_MS = 0.01
PERF_TIME_LIMIT_MICRO = 0.001
FOCUS_HISTORY_LIMIT = 10
LARGE_WIDGET_COUNT = 1000
FOCUS_HISTORY_TEST_COUNT = 15


class TestFocusableWidget:
    """Test FocusableWidget dataclass."""

    def test_focusable_widget_initialization(self) -> None:
        """Test basic FocusableWidget initialization."""
        widget = FocusableWidget(
            widget_id="test-widget",
            display_name="Test Widget",
        )

        assert widget.widget_id == "test-widget"
        assert widget.display_name == "Test Widget"
        assert widget.can_focus is True
        assert widget.focus_priority == 0
        assert widget.focus_group == "default"
        assert widget.tooltip == ""
        assert widget.keyboard_shortcuts == []

    def test_focusable_widget_with_custom_values(self) -> None:
        """Test FocusableWidget with custom values."""
        shortcuts = ["ctrl+p", "f1"]
        widget = FocusableWidget(
            widget_id="custom-widget",
            display_name="Custom Widget",
            can_focus=False,
            focus_priority=5,
            focus_group="panel",
            tooltip="Custom tooltip",
            keyboard_shortcuts=shortcuts,
        )

        assert widget.widget_id == "custom-widget"
        assert widget.display_name == "Custom Widget"
        assert widget.can_focus is False
        assert widget.focus_priority == CUSTOM_PRIORITY
        assert widget.focus_group == "panel"
        assert widget.tooltip == "Custom tooltip"
        assert widget.keyboard_shortcuts == shortcuts

    def test_focusable_widget_post_init(self) -> None:
        """Test __post_init__ behavior."""
        widget = FocusableWidget(
            widget_id="test",
            display_name="Test",
            keyboard_shortcuts=None,
        )

        assert widget.keyboard_shortcuts == []


class TestFocusGroup:
    """Test FocusGroup functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.widgets = [
            FocusableWidget("widget1", "Widget 1", focus_priority=1),
            FocusableWidget("widget2", "Widget 2", can_focus=False),
            FocusableWidget("widget3", "Widget 3", focus_priority=2),
        ]
        self.group = FocusGroup(
            name="test_group",
            widgets=self.widgets,
            wrap_around=True,
        )

    def test_focus_group_initialization(self) -> None:
        """Test FocusGroup initialization."""
        assert self.group.name == "test_group"
        assert len(self.group.widgets) == WIDGET_COUNT
        assert self.group.wrap_around is True
        assert self.group.default_focus is None
        assert self.group.description == ""

    def test_get_widget_by_id_found(self) -> None:
        """Test getting widget by ID when it exists."""
        widget = self.group.get_widget_by_id("widget2")
        assert widget is not None
        assert widget.widget_id == "widget2"
        assert widget.display_name == "Widget 2"

    def test_get_widget_by_id_not_found(self) -> None:
        """Test getting widget by ID when it doesn't exist."""
        widget = self.group.get_widget_by_id("nonexistent")
        assert widget is None

    def test_get_next_widget_success(self) -> None:
        """Test getting next focusable widget."""
        # From widget1 -> widget3 (skip widget2 as it can't focus)
        next_widget = self.group.get_next_widget("widget1")
        assert next_widget is not None
        assert next_widget.widget_id == "widget3"

    def test_get_next_widget_wrap_around(self) -> None:
        """Test wrap around to first widget."""
        next_widget = self.group.get_next_widget("widget3")
        assert next_widget is not None
        assert next_widget.widget_id == "widget1"

    def test_get_next_widget_no_wrap_around(self) -> None:
        """Test behavior when wrap_around is disabled."""
        self.group.wrap_around = False
        next_widget = self.group.get_next_widget("widget3")
        assert next_widget is None

    def test_get_previous_widget_success(self) -> None:
        """Test getting previous focusable widget."""
        # From widget3 -> widget1 (skip widget2 as it can't focus)
        prev_widget = self.group.get_previous_widget("widget3")
        assert prev_widget is not None
        assert prev_widget.widget_id == "widget1"

    def test_get_previous_widget_wrap_around(self) -> None:
        """Test wrap around to last widget."""
        prev_widget = self.group.get_previous_widget("widget1")
        assert prev_widget is not None
        assert prev_widget.widget_id == "widget3"

    def test_get_previous_widget_no_wrap_around(self) -> None:
        """Test behavior when wrap_around is disabled."""
        self.group.wrap_around = False
        prev_widget = self.group.get_previous_widget("widget1")
        assert prev_widget is None

    def test_get_next_widget_invalid_id(self) -> None:
        """Test getting next widget with invalid current ID."""
        next_widget = self.group.get_next_widget("invalid")
        assert next_widget is None

    def test_get_previous_widget_invalid_id(self) -> None:
        """Test getting previous widget with invalid current ID."""
        prev_widget = self.group.get_previous_widget("invalid")
        assert prev_widget is None


class TestFocusManager:
    """Test FocusManager functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.app_mock = Mock()
        self.app_mock.query_one = Mock()
        self.app_mock.screen_stack = [Mock()]  # Simulate one screen

        self.focus_manager = FocusManager(self.app_mock)

        # Create test widgets and groups
        self.widget1 = FocusableWidget("widget1", "Widget 1", focus_priority=1)
        self.widget2 = FocusableWidget("widget2", "Widget 2", focus_priority=2)
        self.widget3 = FocusableWidget("widget3", "Widget 3", can_focus=False)

        self.group1 = FocusGroup(
            name="group1",
            widgets=[self.widget1, self.widget3],
        )
        self.group2 = FocusGroup(
            name="group2",
            widgets=[self.widget2],
        )

        self.focus_manager.register_focus_group(self.group1)
        self.focus_manager.register_focus_group(self.group2)

    def test_focus_manager_initialization(self) -> None:
        """Test FocusManager initialization."""
        manager = FocusManager()
        assert manager.app is None
        assert manager.focus_groups == {}
        assert manager.current_focus is None
        assert manager.focus_history == []
        assert manager.focus_stack == []
        assert manager.focus_observers == []

    def test_set_app(self) -> None:
        """Test setting app reference."""
        manager = FocusManager()
        app_mock = Mock()
        manager.set_app(app_mock)
        assert manager.app is app_mock

    def test_register_focus_group(self) -> None:
        """Test registering focus groups."""
        assert "group1" in self.focus_manager.focus_groups
        assert "group2" in self.focus_manager.focus_groups
        assert self.focus_manager.focus_groups["group1"] is self.group1

    def test_register_focusable_new_group(self) -> None:
        """Test registering focusable to new group."""
        new_widget = FocusableWidget("new_widget", "New Widget")
        self.focus_manager.register_focusable("new_group", new_widget)

        assert "new_group" in self.focus_manager.focus_groups
        new_group = self.focus_manager.focus_groups["new_group"]
        assert new_widget in new_group.widgets

    def test_register_focusable_existing_group(self) -> None:
        """Test registering focusable to existing group."""
        new_widget = FocusableWidget(
            "new_widget",
            "New Widget",
            focus_priority=10,
        )
        self.focus_manager.register_focusable("group1", new_widget)

        group = self.focus_manager.focus_groups["group1"]
        assert new_widget in group.widgets
        # Should be sorted by priority (highest first)
        assert group.widgets[0] is new_widget

    def test_register_focusable_replace_existing(self) -> None:
        """Test replacing existing widget with same ID."""
        updated_widget = FocusableWidget(
            "widget1",
            "Updated Widget 1",
            focus_priority=CUSTOM_PRIORITY,
        )
        self.focus_manager.register_focusable("group1", updated_widget)

        group = self.focus_manager.focus_groups["group1"]
        widget_ids = [w.widget_id for w in group.widgets]

        # Should only have one widget1
        assert widget_ids.count("widget1") == 1
        widget1 = next(w for w in group.widgets if w.widget_id == "widget1")
        assert widget1.display_name == "Updated Widget 1"

    def test_unregister_focusable(self) -> None:
        """Test unregistering focusable widget."""
        self.focus_manager.unregister_focusable("widget1")

        group = self.focus_manager.focus_groups["group1"]
        widget_ids = [w.widget_id for w in group.widgets]
        assert "widget1" not in widget_ids

    def test_get_focusable_widgets_all(self) -> None:
        """Test getting all focusable widgets."""
        widgets = self.focus_manager.get_focusable_widgets()
        widget_ids = [w.widget_id for w in widgets]

        assert "widget1" in widget_ids
        assert "widget2" in widget_ids
        assert "widget3" in widget_ids

    def test_get_focusable_widgets_by_group(self) -> None:
        """Test getting focusable widgets by group."""
        widgets = self.focus_manager.get_focusable_widgets("group1")
        widget_ids = [w.widget_id for w in widgets]

        assert "widget1" in widget_ids
        assert "widget3" in widget_ids
        assert "widget2" not in widget_ids

    def test_get_focusable_widgets_nonexistent_group(self) -> None:
        """Test getting widgets from nonexistent group."""
        widgets = self.focus_manager.get_focusable_widgets("nonexistent")
        assert widgets == []

    def test_set_focus_success(self) -> None:
        """Test setting focus successfully."""
        # Mock the widget query
        mock_widget = Mock()
        self.app_mock.query_one.return_value = mock_widget

        result = self.focus_manager.set_focus("widget1")

        assert result == "widget1"
        assert self.focus_manager.current_focus == "widget1"
        assert mock_widget.add_class.called

    def test_set_focus_unfocusable_widget(self) -> None:
        """Test setting focus to unfocusable widget."""
        result = self.focus_manager.set_focus("widget3")
        assert result is None
        assert self.focus_manager.current_focus is None

    def test_set_focus_nonexistent_widget(self) -> None:
        """Test setting focus to nonexistent widget."""
        result = self.focus_manager.set_focus("nonexistent")
        assert result is None

    def test_set_focus_updates_history(self) -> None:
        """Test focus history is updated."""
        # Mock the widget query
        mock_widget = Mock()
        self.app_mock.query_one.return_value = mock_widget

        # Set initial focus
        self.focus_manager.set_focus("widget1")
        assert len(self.focus_manager.focus_history) == 0

        # Change focus
        self.focus_manager.set_focus("widget2")
        assert len(self.focus_manager.focus_history) == 1
        assert self.focus_manager.focus_history[0] == "widget1"

    def test_focus_first_available(self) -> None:
        """Test focusing first available widget."""
        # Mock the widget query
        mock_widget = Mock()
        self.app_mock.query_one.return_value = mock_widget

        result = self.focus_manager.focus_first_available()

        # Should focus widget2 (highest priority)
        assert result == "widget2"
        assert self.focus_manager.current_focus == "widget2"

    def test_focus_last_available(self) -> None:
        """Test focusing last available widget."""
        # Mock the widget query
        mock_widget = Mock()
        self.app_mock.query_one.return_value = mock_widget

        result = self.focus_manager.focus_last_available()

        # Should focus widget1 (lowest priority)
        assert result == "widget1"

    def test_move_focus_no_current_focus(self) -> None:
        """Test moving focus when no current focus."""
        # Mock the widget query
        mock_widget = Mock()
        self.app_mock.query_one.return_value = mock_widget

        result = self.focus_manager.move_focus(FocusDirection.NEXT)

        # Should focus first available
        assert result == "widget2"

    def test_move_focus_next(self) -> None:
        """Test moving focus to next widget."""
        # Mock the widget query
        mock_widget = Mock()
        self.app_mock.query_one.return_value = mock_widget

        # Set initial focus
        self.focus_manager.set_focus("widget1")

        result = self.focus_manager.move_focus(FocusDirection.NEXT)

        # Should move to widget2 (next group)
        assert result == "widget2"

    def test_move_focus_previous(self) -> None:
        """Test moving focus to previous widget."""
        # Mock the widget query
        mock_widget = Mock()
        self.app_mock.query_one.return_value = mock_widget

        # Set initial focus
        self.focus_manager.set_focus("widget2")

        result = self.focus_manager.move_focus(FocusDirection.PREVIOUS)

        # Should move to widget1 (previous group)
        assert result == "widget1"

    def test_move_focus_first(self) -> None:
        """Test moving focus to first widget."""
        # Mock the widget query
        mock_widget = Mock()
        self.app_mock.query_one.return_value = mock_widget

        result = self.focus_manager.move_focus(FocusDirection.FIRST)
        assert result == "widget2"

    def test_move_focus_last(self) -> None:
        """Test moving focus to last widget."""
        # Mock the widget query
        mock_widget = Mock()
        self.app_mock.query_one.return_value = mock_widget

        result = self.focus_manager.move_focus(FocusDirection.LAST)
        assert result == "widget1"

    def test_move_focus_directional_down(self) -> None:
        """Test directional movement down."""
        # Mock the widget query
        mock_widget = Mock()
        self.app_mock.query_one.return_value = mock_widget

        # Set initial focus
        self.focus_manager.set_focus("widget1")

        result = self.focus_manager.move_focus(FocusDirection.DOWN)
        assert result == "widget2"

    def test_move_focus_directional_up(self) -> None:
        """Test directional movement up."""
        # Mock the widget query
        mock_widget = Mock()
        self.app_mock.query_one.return_value = mock_widget

        # Set initial focus
        self.focus_manager.set_focus("widget2")

        result = self.focus_manager.move_focus(FocusDirection.UP)
        assert result == "widget1"

    def test_push_and_pop_focus_context(self) -> None:
        """Test focus context stack operations."""
        # Mock the widget query
        mock_widget = Mock()
        self.app_mock.query_one.return_value = mock_widget

        # Set initial focus
        self.focus_manager.set_focus("widget1")

        # Push context
        self.focus_manager.push_focus_context("widget2")
        assert self.focus_manager.focus_stack == ["widget1"]
        assert self.focus_manager.current_focus == "widget2"

        # Pop context
        result = self.focus_manager.pop_focus_context()
        assert result == "widget1"
        assert self.focus_manager.focus_stack == []

    def test_focus_previous_in_history(self) -> None:
        """Test focusing previous widget from history."""
        # Mock the widget query
        mock_widget = Mock()
        self.app_mock.query_one.return_value = mock_widget

        # Build history
        self.focus_manager.set_focus("widget1")
        self.focus_manager.set_focus("widget2")

        # Focus previous
        result = self.focus_manager.focus_previous_in_history()
        assert result == "widget1"
        assert len(self.focus_manager.focus_history) == 0

    def test_get_keyboard_shortcuts(self) -> None:
        """Test getting keyboard shortcuts."""
        # Add shortcuts to widgets
        self.widget1.keyboard_shortcuts = ["ctrl+1", "f1"]
        self.widget2.keyboard_shortcuts = ["ctrl+2"]

        shortcuts = self.focus_manager.get_keyboard_shortcuts()

        assert shortcuts["ctrl+1"] == "widget1"
        assert shortcuts["f1"] == "widget1"
        assert shortcuts["ctrl+2"] == "widget2"

    def test_add_remove_focus_observer(self) -> None:
        """Test managing focus observers."""
        observer = Mock()

        self.focus_manager.add_focus_observer(observer)
        assert observer in self.focus_manager.focus_observers

        # Adding same observer again should not duplicate
        self.focus_manager.add_focus_observer(observer)
        assert self.focus_manager.focus_observers.count(observer) == 1

        self.focus_manager.remove_focus_observer(observer)
        assert observer not in self.focus_manager.focus_observers

    def test_handle_escape_context_stack_first(self) -> None:
        """Test ESC handling with focus context stack."""
        # Mock the widget query
        mock_widget = Mock()
        self.app_mock.query_one.return_value = mock_widget

        # Set up context stack
        self.focus_manager.set_focus("widget1")
        self.focus_manager.push_focus_context("widget2")

        result = self.focus_manager.handle_escape_context()
        assert result is True
        assert self.focus_manager.current_focus == "widget1"

    def test_handle_escape_context_history_second(self) -> None:
        """Test ESC handling with focus history."""
        # Mock the widget query
        mock_widget = Mock()
        self.app_mock.query_one.return_value = mock_widget

        # Set up history
        self.focus_manager.set_focus("widget1")
        self.focus_manager.set_focus("widget2")

        result = self.focus_manager.handle_escape_context()
        assert result is True
        assert self.focus_manager.current_focus == "widget1"

    def test_handle_escape_context_unfocus_third(self) -> None:
        """Test ESC handling by unfocusing current widget."""
        # Mock the widget query
        mock_widget = Mock()
        self.app_mock.query_one.return_value = mock_widget

        self.focus_manager.set_focus("widget1")

        result = self.focus_manager.handle_escape_context()
        assert result is True
        assert self.focus_manager.current_focus is None
        assert mock_widget.blur.called

    def test_handle_escape_context_pop_modal_screen(self) -> None:
        """Test ESC handling by popping modal screen."""
        # Set up multiple screens
        self.app_mock.screen_stack = [Mock(), Mock()]
        self.app_mock.pop_screen = Mock()

        result = self.focus_manager.handle_escape_context()
        assert result is True
        assert self.app_mock.pop_screen.called

    def test_handle_escape_context_no_handling(self) -> None:
        """Test ESC handling when no context available."""
        # Empty state
        result = self.focus_manager.handle_escape_context()
        assert result is False

    def test_clear_all(self) -> None:
        """Test clearing all focus state."""
        # Mock the widget query
        mock_widget = Mock()
        self.app_mock.query_one.return_value = mock_widget

        # Set up state
        self.focus_manager.set_focus("widget1")
        self.focus_manager.focus_history.append("old")
        self.focus_manager.focus_stack.append("stack")

        self.focus_manager.clear_all()

        assert self.focus_manager.focus_groups == {}
        assert self.focus_manager.current_focus is None
        assert self.focus_manager.focus_history == []
        assert self.focus_manager.focus_stack == []
        assert mock_widget.remove_class.called


class TestCreatePanelFocusGroup:
    """Test create_panel_focus_group utility function."""

    def test_create_panel_focus_group_basic(self) -> None:
        """Test creating basic panel focus group."""
        group = create_panel_focus_group("Test Panel", "test-panel")

        assert group.name == "test_panel"
        assert len(group.widgets) == 1

        widget = group.widgets[0]
        assert widget.widget_id == "test-panel"
        assert widget.display_name == "Test Panel"
        assert widget.focus_priority == 0
        assert widget.keyboard_shortcuts == []

    def test_create_panel_focus_group_with_options(self) -> None:
        """Test creating panel focus group with custom options."""
        shortcuts = ["ctrl+p", "f1"]
        group = create_panel_focus_group(
            "Custom Panel",
            "custom-panel",
            priority=5,
            shortcuts=shortcuts,
        )

        assert group.name == "custom_panel"
        widget = group.widgets[0]
        assert widget.focus_priority == CUSTOM_PRIORITY
        assert widget.keyboard_shortcuts == shortcuts


class TestGlobalFocusManager:
    """Test global focus manager instance."""

    def test_global_focus_manager_exists(self) -> None:
        """Test that global focus manager instance exists."""
        assert focus_manager is not None
        assert isinstance(focus_manager, FocusManager)

    def test_global_focus_manager_initially_empty(self) -> None:
        """Test that global focus manager starts empty."""
        # Note: This test might fail if other tests have modified the global state
        # In a real scenario, we'd want to reset the global state in setup
        original_groups = focus_manager.focus_groups.copy()
        focus_manager.clear_all()

        assert focus_manager.app is None
        assert focus_manager.focus_groups == {}
        assert focus_manager.current_focus is None

        # Restore original state
        focus_manager.focus_groups = original_groups


@pytest.mark.performance
class TestFocusManagerPerformance:
    """Performance tests for focus manager."""

    def test_large_focus_group_performance(self) -> None:
        """Test performance with large focus groups."""
        # Create large focus group
        widgets = [
            FocusableWidget(f"widget{i}", f"Widget {i}")
            for i in range(LARGE_WIDGET_COUNT)
        ]
        large_group = FocusGroup("large_group", widgets)

        manager = FocusManager()
        manager.register_focus_group(large_group)

        # Test that basic operations complete quickly

        start = time.perf_counter()
        manager.get_focusable_widgets("large_group")
        elapsed = time.perf_counter() - start
        assert elapsed < PERF_TIME_LIMIT_MS  # Should complete in under 10ms

        start = time.perf_counter()
        large_group.get_next_widget("widget500")
        elapsed = time.perf_counter() - start
        assert elapsed < PERF_TIME_LIMIT_MICRO  # Should complete in under 1ms

    def test_focus_history_memory_limit(self) -> None:
        """Test that focus history respects memory limits."""
        app_mock = Mock()
        app_mock.query_one = Mock(return_value=Mock())

        manager = FocusManager(app_mock)

        # Create widgets
        for i in range(
            FOCUS_HISTORY_TEST_COUNT,
        ):  # More than MAX_FOCUS_HISTORY (10)
            widget = FocusableWidget(f"widget{i}", f"Widget {i}")
            manager.register_focusable("group", widget)
            manager.set_focus(f"widget{i}")

        # History should be limited
        assert len(manager.focus_history) <= FOCUS_HISTORY_LIMIT


@pytest.mark.integration
class TestFocusManagerIntegration:
    """Integration tests for focus manager with mocked Textual app."""

    @pytest.fixture
    def mock_app(self) -> Mock:
        """Create a mock Textual app."""
        app_mock = Mock()
        app_mock.query_one = Mock()
        app_mock.screen_stack = [Mock()]
        return app_mock

    @pytest.fixture
    def integrated_focus_manager(self, mock_app: Mock) -> FocusManager:
        """Create focus manager with mock app integration."""
        manager = FocusManager(mock_app)

        # Set up test groups
        widget1 = FocusableWidget("panel1", "Panel 1", shortcuts=["ctrl+1"])
        widget2 = FocusableWidget("panel2", "Panel 2", shortcuts=["ctrl+2"])

        group1 = FocusGroup("panels", [widget1, widget2])
        manager.register_focus_group(group1)

        return manager

    def test_integrated_focus_flow(
        self,
        integrated_focus_manager: FocusManager,
        mock_app: Mock,
    ) -> None:
        """Test complete focus flow with app integration."""
        # Mock widget elements
        mock_widget1 = Mock()
        mock_widget2 = Mock()
        mock_app.query_one.side_effect = lambda selector: (
            mock_widget1 if "panel1" in selector else mock_widget2
        )

        # Test focus flow
        result1 = integrated_focus_manager.focus_first_available()
        assert result1 == "panel1"
        assert mock_widget1.add_class.called

        result2 = integrated_focus_manager.move_focus(FocusDirection.NEXT)
        assert result2 == "panel2"
        assert mock_widget1.remove_class.called
        assert mock_widget2.add_class.called

        # Test shortcuts
        shortcuts = integrated_focus_manager.get_keyboard_shortcuts()
        assert "ctrl+1" in shortcuts
        assert shortcuts["ctrl+1"] == "panel1"

    def test_visual_focus_application(
        self,
        integrated_focus_manager: FocusManager,
        mock_app: Mock,
    ) -> None:
        """Test visual focus indicators are applied correctly."""
        mock_widget = Mock()
        mock_app.query_one.return_value = mock_widget

        # Test applying focus
        integrated_focus_manager.apply_visual_focus("panel1", focused=True)
        mock_widget.add_class.assert_any_call("focused")
        mock_widget.add_class.assert_any_call("focus-active")

        # Test removing focus
        integrated_focus_manager.apply_visual_focus("panel1", focused=False)
        mock_widget.remove_class.assert_any_call("focused")
        mock_widget.remove_class.assert_any_call("focus-active")

    def test_error_handling_in_visual_focus(
        self,
        integrated_focus_manager: FocusManager,
        mock_app: Mock,
    ) -> None:
        """Test error handling in visual focus operations."""
        # Mock query_one to raise an exception
        mock_app.query_one.side_effect = ValueError("Widget not found")

        # Should not raise exception
        integrated_focus_manager.apply_visual_focus(
            "nonexistent",
            focused=True,
        )
        # Test passes if no exception is raised
