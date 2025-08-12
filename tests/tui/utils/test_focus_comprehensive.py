"""Comprehensive tests for focus management utilities.

This module provides complete test coverage for the focus management system,
including FocusManager, FocusGroup, FocusableWidget, and all navigation
and state management functionality.
"""

from __future__ import annotations

from unittest.mock import Mock

from src.tui.utils.focus import (
    FocusableWidget,
    FocusDirection,
    FocusGroup,
    FocusManager,
    FocusScope,
    create_panel_focus_group,
    focus_manager,
)


class TestFocusableWidget:
    """Test FocusableWidget dataclass functionality."""

    def test_default_initialization(self) -> None:
        """Test FocusableWidget with required parameters only."""
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

    def test_full_initialization(self) -> None:
        """Test FocusableWidget with all parameters."""
        shortcuts = ["ctrl+t", "f1"]
        widget = FocusableWidget(
            widget_id="full-widget",
            display_name="Full Widget",
            can_focus=False,
            focus_priority=5,
            focus_group="custom",
            tooltip="Test tooltip",
            keyboard_shortcuts=shortcuts,
        )

        assert widget.widget_id == "full-widget"
        assert widget.display_name == "Full Widget"
        assert widget.can_focus is False
        assert widget.focus_priority == 5
        assert widget.focus_group == "custom"
        assert widget.tooltip == "Test tooltip"
        assert widget.keyboard_shortcuts == shortcuts

    def test_post_init_with_none_shortcuts(self) -> None:
        """Test post_init handling of None shortcuts."""
        widget = FocusableWidget(
            widget_id="test",
            display_name="Test",
            keyboard_shortcuts=None,
        )

        assert widget.keyboard_shortcuts == []


class TestFocusGroup:
    """Test FocusGroup functionality."""

    def test_empty_group_initialization(self) -> None:
        """Test FocusGroup with minimal parameters."""
        group = FocusGroup(name="test-group", widgets=[])

        assert group.name == "test-group"
        assert group.widgets == []
        assert group.wrap_around is True
        assert group.default_focus is None
        assert group.description == ""

    def test_full_group_initialization(self) -> None:
        """Test FocusGroup with all parameters."""
        widgets = [
            FocusableWidget("widget1", "Widget 1"),
            FocusableWidget("widget2", "Widget 2"),
        ]

        group = FocusGroup(
            name="full-group",
            widgets=widgets,
            wrap_around=False,
            default_focus="widget1",
            description="Test group",
        )

        assert group.name == "full-group"
        assert group.widgets == widgets
        assert group.wrap_around is False
        assert group.default_focus == "widget1"
        assert group.description == "Test group"

    def test_get_widget_by_id_found(self) -> None:
        """Test finding widget by ID."""
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        group = FocusGroup("test", [widget1, widget2])

        found = group.get_widget_by_id("widget2")

        assert found == widget2

    def test_get_widget_by_id_not_found(self) -> None:
        """Test widget not found by ID."""
        widget1 = FocusableWidget("widget1", "Widget 1")
        group = FocusGroup("test", [widget1])

        found = group.get_widget_by_id("nonexistent")

        assert found is None

    def test_get_next_widget_normal_order(self) -> None:
        """Test getting next widget in normal order."""
        widgets = [
            FocusableWidget("widget1", "Widget 1"),
            FocusableWidget("widget2", "Widget 2"),
            FocusableWidget("widget3", "Widget 3"),
        ]
        group = FocusGroup("test", widgets)

        next_widget = group.get_next_widget("widget1")

        assert next_widget == widgets[1]

    def test_get_next_widget_wrap_around(self) -> None:
        """Test getting next widget with wrap around."""
        widgets = [
            FocusableWidget("widget1", "Widget 1"),
            FocusableWidget("widget2", "Widget 2"),
        ]
        group = FocusGroup("test", widgets, wrap_around=True)

        next_widget = group.get_next_widget("widget2")

        assert next_widget == widgets[0]

    def test_get_next_widget_no_wrap_around(self) -> None:
        """Test getting next widget without wrap around."""
        widgets = [
            FocusableWidget("widget1", "Widget 1"),
            FocusableWidget("widget2", "Widget 2"),
        ]
        group = FocusGroup("test", widgets, wrap_around=False)

        next_widget = group.get_next_widget("widget2")

        assert next_widget is None

    def test_get_next_widget_skip_unfocusable(self) -> None:
        """Test getting next widget skipping unfocusable widgets."""
        widgets = [
            FocusableWidget("widget1", "Widget 1"),
            FocusableWidget("widget2", "Widget 2", can_focus=False),
            FocusableWidget("widget3", "Widget 3"),
        ]
        group = FocusGroup("test", widgets)

        next_widget = group.get_next_widget("widget1")

        assert next_widget == widgets[2]

    def test_get_next_widget_nonexistent_current(self) -> None:
        """Test getting next widget with nonexistent current widget."""
        widgets = [FocusableWidget("widget1", "Widget 1")]
        group = FocusGroup("test", widgets)

        next_widget = group.get_next_widget("nonexistent")

        assert next_widget is None

    def test_get_previous_widget_normal_order(self) -> None:
        """Test getting previous widget in normal order."""
        widgets = [
            FocusableWidget("widget1", "Widget 1"),
            FocusableWidget("widget2", "Widget 2"),
            FocusableWidget("widget3", "Widget 3"),
        ]
        group = FocusGroup("test", widgets)

        prev_widget = group.get_previous_widget("widget2")

        assert prev_widget == widgets[0]

    def test_get_previous_widget_wrap_around(self) -> None:
        """Test getting previous widget with wrap around."""
        widgets = [
            FocusableWidget("widget1", "Widget 1"),
            FocusableWidget("widget2", "Widget 2"),
        ]
        group = FocusGroup("test", widgets, wrap_around=True)

        prev_widget = group.get_previous_widget("widget1")

        assert prev_widget == widgets[1]

    def test_get_previous_widget_no_wrap_around(self) -> None:
        """Test getting previous widget without wrap around."""
        widgets = [
            FocusableWidget("widget1", "Widget 1"),
            FocusableWidget("widget2", "Widget 2"),
        ]
        group = FocusGroup("test", widgets, wrap_around=False)

        prev_widget = group.get_previous_widget("widget1")

        assert prev_widget is None

    def test_get_previous_widget_skip_unfocusable(self) -> None:
        """Test getting previous widget skipping unfocusable widgets."""
        widgets = [
            FocusableWidget("widget1", "Widget 1"),
            FocusableWidget("widget2", "Widget 2", can_focus=False),
            FocusableWidget("widget3", "Widget 3"),
        ]
        group = FocusGroup("test", widgets)

        prev_widget = group.get_previous_widget("widget3")

        assert prev_widget == widgets[0]


class TestFocusManager:
    """Test FocusManager functionality."""

    def test_default_initialization(self) -> None:
        """Test FocusManager initialization without app."""
        manager = FocusManager()

        assert manager.app is None
        assert manager.focus_groups == {}
        assert manager.current_focus is None
        assert manager.focus_history == []
        assert manager.focus_stack == []
        assert manager.focus_observers == []

    def test_initialization_with_app(self) -> None:
        """Test FocusManager initialization with app."""
        mock_app = Mock()
        manager = FocusManager(app=mock_app)

        assert manager.app == mock_app

    def test_set_app(self) -> None:
        """Test setting app after initialization."""
        manager = FocusManager()
        mock_app = Mock()

        manager.set_app(mock_app)

        assert manager.app == mock_app

    def test_register_focus_group(self) -> None:
        """Test registering a focus group."""
        manager = FocusManager()
        group = FocusGroup("test-group", [])

        manager.register_focus_group(group)

        assert "test-group" in manager.focus_groups
        assert manager.focus_groups["test-group"] == group

    def test_register_focusable_new_group(self) -> None:
        """Test registering focusable widget to new group."""
        manager = FocusManager()
        widget = FocusableWidget("test-widget", "Test")

        manager.register_focusable("new-group", widget)

        assert "new-group" in manager.focus_groups
        assert widget in manager.focus_groups["new-group"].widgets

    def test_register_focusable_existing_group(self) -> None:
        """Test registering focusable widget to existing group."""
        manager = FocusManager()
        group = FocusGroup("test-group", [])
        manager.register_focus_group(group)
        widget = FocusableWidget("test-widget", "Test")

        manager.register_focusable("test-group", widget)

        assert widget in manager.focus_groups["test-group"].widgets

    def test_register_focusable_priority_sorting(self) -> None:
        """Test focusable widget priority sorting."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1", focus_priority=1)
        widget2 = FocusableWidget("widget2", "Widget 2", focus_priority=5)
        widget3 = FocusableWidget("widget3", "Widget 3", focus_priority=3)

        manager.register_focusable("test", widget1)
        manager.register_focusable("test", widget2)
        manager.register_focusable("test", widget3)

        widgets = manager.focus_groups["test"].widgets
        assert widgets[0] == widget2  # Highest priority first
        assert widgets[1] == widget3
        assert widgets[2] == widget1

    def test_register_focusable_replace_existing(self) -> None:
        """Test replacing existing widget with same ID."""
        manager = FocusManager()
        old_widget = FocusableWidget("test-id", "Old Widget")
        new_widget = FocusableWidget("test-id", "New Widget", focus_priority=5)

        manager.register_focusable("test", old_widget)
        manager.register_focusable("test", new_widget)

        widgets = manager.focus_groups["test"].widgets
        assert len(widgets) == 1
        assert widgets[0] == new_widget

    def test_unregister_focusable(self) -> None:
        """Test unregistering focusable widget."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")

        manager.register_focusable("group1", widget1)
        manager.register_focusable("group1", widget2)
        manager.register_focusable("group2", widget1)

        manager.unregister_focusable("widget1")

        # widget1 should be removed from all groups
        assert widget1 not in manager.focus_groups["group1"].widgets
        assert widget2 in manager.focus_groups["group1"].widgets
        assert widget1 not in manager.focus_groups["group2"].widgets

    def test_get_focusable_widgets_all(self) -> None:
        """Test getting all focusable widgets."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")

        manager.register_focusable("group1", widget1)
        manager.register_focusable("group2", widget2)

        all_widgets = manager.get_focusable_widgets()

        assert len(all_widgets) == 2
        assert widget1 in all_widgets
        assert widget2 in all_widgets

    def test_get_focusable_widgets_by_group(self) -> None:
        """Test getting focusable widgets by group."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")

        manager.register_focusable("group1", widget1)
        manager.register_focusable("group2", widget2)

        group1_widgets = manager.get_focusable_widgets("group1")

        assert len(group1_widgets) == 1
        assert widget1 in group1_widgets
        assert widget2 not in group1_widgets

    def test_get_focusable_widgets_nonexistent_group(self) -> None:
        """Test getting widgets from nonexistent group."""
        manager = FocusManager()

        widgets = manager.get_focusable_widgets("nonexistent")

        assert widgets == []

    def test_set_focus_success(self) -> None:
        """Test setting focus successfully."""
        manager = FocusManager()
        widget = FocusableWidget("test-widget", "Test")
        manager.register_focusable("test", widget)

        result = manager.set_focus("test-widget")

        assert result == "test-widget"
        assert manager.current_focus == "test-widget"

    def test_set_focus_nonexistent_widget(self) -> None:
        """Test setting focus to nonexistent widget."""
        manager = FocusManager()

        result = manager.set_focus("nonexistent")

        assert result is None
        assert manager.current_focus is None

    def test_set_focus_unfocusable_widget(self) -> None:
        """Test setting focus to unfocusable widget."""
        manager = FocusManager()
        widget = FocusableWidget("test-widget", "Test", can_focus=False)
        manager.register_focusable("test", widget)

        result = manager.set_focus("test-widget")

        assert result is None
        assert manager.current_focus is None

    def test_set_focus_updates_history(self) -> None:
        """Test that setting focus updates history."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        manager.register_focusable("test", widget1)
        manager.register_focusable("test", widget2)

        manager.set_focus("widget1")
        manager.set_focus("widget2")

        assert "widget1" in manager.focus_history
        assert manager.current_focus == "widget2"

    def test_set_focus_history_limit(self) -> None:
        """Test focus history size limit."""
        manager = FocusManager()

        # Create widgets exceeding history limit
        max_history_plus_extra = 12  # MAX_FOCUS_HISTORY is 10
        for i in range(max_history_plus_extra):
            widget = FocusableWidget(f"widget{i}", f"Widget {i}")
            manager.register_focusable("test", widget)

        # Focus all widgets sequentially
        for i in range(max_history_plus_extra):
            manager.set_focus(f"widget{i}")

        # History should be limited to MAX_FOCUS_HISTORY
        max_focus_history = 10
        assert len(manager.focus_history) <= max_focus_history
        # History contains previous focuses, so earliest ones should be removed
        # The last widget focused is not in history (it's current_focus)
        assert manager.current_focus == f"widget{max_history_plus_extra - 1}"

    def test_focus_first_available_success(self) -> None:
        """Test focusing first available widget."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1", focus_priority=1)
        widget2 = FocusableWidget("widget2", "Widget 2", focus_priority=5)
        manager.register_focusable("test", widget1)
        manager.register_focusable("test", widget2)

        result = manager.focus_first_available()

        assert result == "widget2"  # Higher priority
        assert manager.current_focus == "widget2"

    def test_focus_first_available_no_widgets(self) -> None:
        """Test focusing first available when no widgets exist."""
        manager = FocusManager()

        result = manager.focus_first_available()

        assert result is None
        assert manager.current_focus is None

    def test_focus_first_available_no_focusable(self) -> None:
        """Test focusing first available when no widgets are focusable."""
        manager = FocusManager()
        widget = FocusableWidget("widget1", "Widget 1", can_focus=False)
        manager.register_focusable("test", widget)

        result = manager.focus_first_available()

        assert result is None
        assert manager.current_focus is None

    def test_focus_last_available_success(self) -> None:
        """Test focusing last available widget."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1", focus_priority=1)
        widget2 = FocusableWidget("widget2", "Widget 2", focus_priority=5)
        manager.register_focusable("test", widget1)
        manager.register_focusable("test", widget2)

        result = manager.focus_last_available()

        assert result == "widget1"  # Last in priority-sorted list
        assert manager.current_focus == "widget1"

    def test_focus_previous_in_history_success(self) -> None:
        """Test focusing previous widget from history."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        widget3 = FocusableWidget("widget3", "Widget 3")
        manager.register_focusable("test", widget1)
        manager.register_focusable("test", widget2)
        manager.register_focusable("test", widget3)

        manager.set_focus("widget1")
        manager.set_focus("widget2")
        manager.set_focus("widget3")

        result = manager.focus_previous_in_history()

        assert result == "widget2"
        assert manager.current_focus == "widget2"

    def test_focus_previous_in_history_empty(self) -> None:
        """Test focusing previous with empty history."""
        manager = FocusManager()

        result = manager.focus_previous_in_history()

        assert result is None

    def test_focus_previous_in_history_unfocusable(self) -> None:
        """Test focusing previous when widget in history becomes unfocusable."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        manager.register_focusable("test", widget1)
        manager.register_focusable("test", widget2)

        manager.set_focus("widget1")
        manager.set_focus("widget2")

        # Make widget1 unfocusable
        widget1.can_focus = False

        result = manager.focus_previous_in_history()

        assert result is None  # No focusable widget in history

    def test_push_focus_context(self) -> None:
        """Test pushing focus context."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        manager.register_focusable("test", widget1)
        manager.register_focusable("test", widget2)

        manager.set_focus("widget1")
        manager.push_focus_context("widget2")

        assert manager.current_focus == "widget2"
        assert "widget1" in manager.focus_stack

    def test_push_focus_context_no_current_focus(self) -> None:
        """Test pushing focus context with no current focus."""
        manager = FocusManager()
        widget = FocusableWidget("widget1", "Widget 1")
        manager.register_focusable("test", widget)

        manager.push_focus_context("widget1")

        assert manager.current_focus == "widget1"
        assert len(manager.focus_stack) == 0

    def test_pop_focus_context_success(self) -> None:
        """Test popping focus context successfully."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        manager.register_focusable("test", widget1)
        manager.register_focusable("test", widget2)

        manager.set_focus("widget1")
        manager.push_focus_context("widget2")

        result = manager.pop_focus_context()

        assert result == "widget1"
        assert manager.current_focus == "widget1"
        assert len(manager.focus_stack) == 0

    def test_pop_focus_context_empty_stack(self) -> None:
        """Test popping focus context with empty stack."""
        manager = FocusManager()

        result = manager.pop_focus_context()

        assert result is None

    def test_move_focus_no_current_focus(self) -> None:
        """Test move focus when no current focus."""
        manager = FocusManager()
        widget = FocusableWidget("widget1", "Widget 1")
        manager.register_focusable("test", widget)

        result = manager.move_focus(FocusDirection.NEXT)

        assert result == "widget1"  # Should focus first available

    def test_move_focus_next_within_group(self) -> None:
        """Test move focus next within group."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        manager.register_focusable("test", widget1)
        manager.register_focusable("test", widget2)

        manager.set_focus("widget1")
        result = manager.move_focus(FocusDirection.NEXT)

        assert result == "widget2"

    def test_move_focus_next_cross_group(self) -> None:
        """Test move focus next across groups."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        manager.register_focusable("group1", widget1)
        manager.register_focusable("group2", widget2)

        manager.set_focus("widget1")
        result = manager.move_focus(
            FocusDirection.NEXT,
            FocusScope.ALL_PANELS,
        )

        assert result == "widget2"

    def test_move_focus_previous_within_group(self) -> None:
        """Test move focus previous within group."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        manager.register_focusable("test", widget1)
        manager.register_focusable("test", widget2)

        manager.set_focus("widget2")
        result = manager.move_focus(FocusDirection.PREVIOUS)

        assert result == "widget1"

    def test_move_focus_first(self) -> None:
        """Test move focus to first widget."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1", focus_priority=1)
        widget2 = FocusableWidget("widget2", "Widget 2", focus_priority=5)
        manager.register_focusable("test", widget1)
        manager.register_focusable("test", widget2)

        manager.set_focus("widget1")
        result = manager.move_focus(FocusDirection.FIRST)

        assert result == "widget2"  # Highest priority

    def test_move_focus_last(self) -> None:
        """Test move focus to last widget."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1", focus_priority=1)
        widget2 = FocusableWidget("widget2", "Widget 2", focus_priority=5)
        manager.register_focusable("test", widget1)
        manager.register_focusable("test", widget2)

        manager.set_focus("widget2")
        result = manager.move_focus(FocusDirection.LAST)

        assert result == "widget1"  # Last in sorted list

    def test_move_focus_directional_down_right(self) -> None:
        """Test directional focus movement (down/right -> next)."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        manager.register_focusable("test", widget1)
        manager.register_focusable("test", widget2)

        manager.set_focus("widget1")

        # Test down
        result_down = manager.move_focus(FocusDirection.DOWN)
        assert result_down == "widget2"

        manager.set_focus("widget1")
        # Test right
        result_right = manager.move_focus(FocusDirection.RIGHT)
        assert result_right == "widget2"

    def test_move_focus_directional_up_left(self) -> None:
        """Test directional focus movement (up/left -> previous)."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        manager.register_focusable("test", widget1)
        manager.register_focusable("test", widget2)

        manager.set_focus("widget2")

        # Test up
        result_up = manager.move_focus(FocusDirection.UP)
        assert result_up == "widget1"

        manager.set_focus("widget2")
        # Test left
        result_left = manager.move_focus(FocusDirection.LEFT)
        assert result_left == "widget1"

    def test_get_focus_info_current(self) -> None:
        """Test getting current focus info."""
        manager = FocusManager()
        widget = FocusableWidget("widget1", "Widget 1")
        manager.register_focusable("test", widget)
        manager.set_focus("widget1")

        info = manager.get_focus_info()

        assert info == widget

    def test_get_focus_info_specific(self) -> None:
        """Test getting specific widget focus info."""
        manager = FocusManager()
        widget = FocusableWidget("widget1", "Widget 1")
        manager.register_focusable("test", widget)

        info = manager.get_focus_info("widget1")

        assert info == widget

    def test_get_focus_info_no_focus(self) -> None:
        """Test getting focus info when no focus."""
        manager = FocusManager()

        info = manager.get_focus_info()

        assert info is None

    def test_get_keyboard_shortcuts(self) -> None:
        """Test getting keyboard shortcuts mapping."""
        manager = FocusManager()
        widget1 = FocusableWidget(
            "widget1",
            "Widget 1",
            keyboard_shortcuts=["ctrl+1", "f1"],
        )
        widget2 = FocusableWidget(
            "widget2",
            "Widget 2",
            keyboard_shortcuts=["ctrl+2"],
        )
        manager.register_focusable("test", widget1)
        manager.register_focusable("test", widget2)

        shortcuts = manager.get_keyboard_shortcuts()

        expected_shortcuts = {
            "ctrl+1": "widget1",
            "f1": "widget1",
            "ctrl+2": "widget2",
        }
        assert shortcuts == expected_shortcuts

    def test_get_keyboard_shortcuts_empty(self) -> None:
        """Test getting keyboard shortcuts when none exist."""
        manager = FocusManager()
        widget = FocusableWidget("widget1", "Widget 1")
        manager.register_focusable("test", widget)

        shortcuts = manager.get_keyboard_shortcuts()

        assert shortcuts == {}

    def test_add_focus_observer(self) -> None:
        """Test adding focus observer."""
        manager = FocusManager()
        observer = Mock()

        manager.add_focus_observer(observer)

        assert observer in manager.focus_observers

    def test_add_focus_observer_duplicate(self) -> None:
        """Test adding duplicate focus observer."""
        manager = FocusManager()
        observer = Mock()

        manager.add_focus_observer(observer)
        manager.add_focus_observer(observer)

        assert manager.focus_observers.count(observer) == 1

    def test_remove_focus_observer(self) -> None:
        """Test removing focus observer."""
        manager = FocusManager()
        observer = Mock()
        manager.add_focus_observer(observer)

        manager.remove_focus_observer(observer)

        assert observer not in manager.focus_observers

    def test_remove_focus_observer_not_present(self) -> None:
        """Test removing observer that's not present."""
        manager = FocusManager()
        observer = Mock()

        # Should not raise exception
        manager.remove_focus_observer(observer)

        assert observer not in manager.focus_observers

    def test_apply_visual_focus_no_app(self) -> None:
        """Test applying visual focus without app."""
        manager = FocusManager()

        # Should not raise exception
        manager.apply_visual_focus("widget1", focused=True)

    def test_apply_visual_focus_with_app(self) -> None:
        """Test applying visual focus with app."""
        manager = FocusManager()
        mock_app = Mock()
        mock_widget = Mock()
        mock_app.query_one.return_value = mock_widget
        manager.set_app(mock_app)

        manager.apply_visual_focus("widget1", focused=True)

        mock_app.query_one.assert_called_once_with("#widget1")
        mock_widget.add_class.assert_any_call("focused")
        mock_widget.add_class.assert_any_call("focus-active")

    def test_apply_visual_focus_remove_with_app(self) -> None:
        """Test removing visual focus with app."""
        manager = FocusManager()
        mock_app = Mock()
        mock_widget = Mock()
        mock_app.query_one.return_value = mock_widget
        manager.set_app(mock_app)

        manager.apply_visual_focus("widget1", focused=False)

        mock_app.query_one.assert_called_once_with("#widget1")
        mock_widget.remove_class.assert_any_call("focused")
        mock_widget.remove_class.assert_any_call("focus-active")

    def test_apply_visual_focus_widget_not_found(self) -> None:
        """Test applying visual focus when widget not found."""
        manager = FocusManager()
        mock_app = Mock()
        mock_app.query_one.side_effect = Exception("Not found")
        manager.set_app(mock_app)

        # Should not raise exception
        manager.apply_visual_focus("nonexistent", focused=True)

    def test_handle_escape_context_with_stack(self) -> None:
        """Test escape handling with focus stack."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        manager.register_focusable("test", widget1)
        manager.register_focusable("test", widget2)

        manager.set_focus("widget1")
        manager.push_focus_context("widget2")

        result = manager.handle_escape_context()

        assert result is True
        assert manager.current_focus == "widget1"

    def test_handle_escape_context_with_history(self) -> None:
        """Test escape handling with focus history."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        manager.register_focusable("test", widget1)
        manager.register_focusable("test", widget2)

        manager.set_focus("widget1")
        manager.set_focus("widget2")

        result = manager.handle_escape_context()

        assert result is True
        assert manager.current_focus == "widget1"

    def test_handle_escape_context_blur_current(self) -> None:
        """Test escape handling by blurring current widget."""
        manager = FocusManager()
        mock_app = Mock()
        mock_widget = Mock()
        mock_app.query_one.return_value = mock_widget
        manager.set_app(mock_app)

        widget = FocusableWidget("widget1", "Widget 1")
        manager.register_focusable("test", widget)
        manager.set_focus("widget1")

        result = manager.handle_escape_context()

        assert result is True
        assert manager.current_focus is None
        mock_widget.blur.assert_called_once()

    def test_handle_escape_context_pop_screen(self) -> None:
        """Test escape handling by popping modal screen."""
        manager = FocusManager()
        mock_app = Mock()
        mock_app.screen_stack = ["screen1", "screen2"]  # More than 1 screen
        manager.set_app(mock_app)

        result = manager.handle_escape_context()

        assert result is True
        mock_app.pop_screen.assert_called_once()

    def test_handle_escape_context_no_action(self) -> None:
        """Test escape handling when no action is possible."""
        manager = FocusManager()

        result = manager.handle_escape_context()

        assert result is False

    def test_clear_all(self) -> None:
        """Test clearing all focus state."""
        manager = FocusManager()
        widget = FocusableWidget("widget1", "Widget 1")
        manager.register_focusable("test", widget)
        manager.set_focus("widget1")
        manager.focus_history.append("widget0")
        manager.focus_stack.append("widget0")

        manager.clear_all()

        assert manager.focus_groups == {}
        assert manager.current_focus is None
        assert manager.focus_history == []
        assert manager.focus_stack == []

    def test_clear_all_with_visual_focus(self) -> None:
        """Test clearing all with visual focus cleanup."""
        manager = FocusManager()
        mock_app = Mock()
        mock_widget = Mock()
        mock_app.query_one.return_value = mock_widget
        manager.set_app(mock_app)

        widget = FocusableWidget("widget1", "Widget 1")
        manager.register_focusable("test", widget)
        manager.set_focus("widget1")

        manager.clear_all()

        mock_widget.remove_class.assert_any_call("focused")
        mock_widget.remove_class.assert_any_call("focus-active")


class TestFocusManagerPrivateMethods:
    """Test private methods of FocusManager."""

    def test_find_widget_group(self) -> None:
        """Test finding widget group."""
        manager = FocusManager()
        widget = FocusableWidget("widget1", "Widget 1")
        group = FocusGroup("test-group", [widget])
        manager.register_focus_group(group)

        found_group = manager._find_widget_group("widget1")

        assert found_group == group

    def test_find_widget_group_not_found(self) -> None:
        """Test finding widget group when not found."""
        manager = FocusManager()

        found_group = manager._find_widget_group("nonexistent")

        assert found_group is None

    def test_find_widget_info(self) -> None:
        """Test finding widget info."""
        manager = FocusManager()
        widget = FocusableWidget("widget1", "Widget 1")
        manager.register_focusable("test", widget)

        found_info = manager._find_widget_info("widget1")

        assert found_info == widget

    def test_find_widget_info_not_found(self) -> None:
        """Test finding widget info when not found."""
        manager = FocusManager()

        found_info = manager._find_widget_info("nonexistent")

        assert found_info is None

    def test_notify_focus_change(self) -> None:
        """Test focus change notification."""
        manager = FocusManager()
        mock_app = Mock()
        old_widget = Mock()
        new_widget = Mock()
        mock_app.query_one.side_effect = [old_widget, new_widget]
        manager.set_app(mock_app)

        observer = Mock()
        observer.on_focus_changed = Mock()
        manager.add_focus_observer(observer)

        manager._notify_focus_change("old-widget", "new-widget")

        # Should remove focus from old widget
        old_widget.remove_class.assert_any_call("focused")
        old_widget.remove_class.assert_any_call("focus-active")

        # Should add focus to new widget
        new_widget.add_class.assert_any_call("focused")
        new_widget.add_class.assert_any_call("focus-active")

        # Should notify observer
        observer.on_focus_changed.assert_called_once_with(
            "old-widget",
            "new-widget",
        )

    def test_notify_focus_change_observer_exception(self) -> None:
        """Test focus change notification with observer exception."""
        manager = FocusManager()
        mock_app = Mock()
        mock_widget = Mock()
        mock_app.query_one.return_value = mock_widget
        manager.set_app(mock_app)

        observer = Mock()
        observer.on_focus_changed = Mock(
            side_effect=Exception("Observer error"),
        )
        manager.add_focus_observer(observer)

        # Should not raise exception
        manager._notify_focus_change(None, "new-widget")

    def test_move_to_next_group(self) -> None:
        """Test moving to next group."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        manager.register_focusable("group1", widget1)
        manager.register_focusable("group2", widget2)

        manager.set_focus("widget1")
        result = manager._move_to_next_group()

        assert result == "widget2"

    def test_move_to_next_group_wrap_around(self) -> None:
        """Test moving to next group with wrap around."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        manager.register_focusable("group1", widget1)
        manager.register_focusable("group2", widget2)

        manager.set_focus("widget2")  # Last group
        result = manager._move_to_next_group()

        assert result == "widget1"  # Wraps to first group

    def test_move_to_previous_group(self) -> None:
        """Test moving to previous group."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        manager.register_focusable("group1", widget1)
        manager.register_focusable("group2", widget2)

        manager.set_focus("widget2")
        result = manager._move_to_previous_group()

        assert result == "widget1"

    def test_move_to_previous_group_wrap_around(self) -> None:
        """Test moving to previous group with wrap around."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        manager.register_focusable("group1", widget1)
        manager.register_focusable("group2", widget2)

        manager.set_focus("widget1")  # First group
        result = manager._move_to_previous_group()

        assert result == "widget2"  # Wraps to last group


class TestCreatePanelFocusGroup:
    """Test create_panel_focus_group helper function."""

    def test_create_panel_focus_group_minimal(self) -> None:
        """Test creating panel focus group with minimal parameters."""
        group = create_panel_focus_group("Test Panel", "test-panel")

        assert group.name == "test_panel"
        assert len(group.widgets) == 1

        widget = group.widgets[0]
        assert widget.widget_id == "test-panel"
        assert widget.display_name == "Test Panel"
        assert widget.focus_priority == 0
        assert widget.keyboard_shortcuts == []

        assert group.description == "Test Panel panel focus group"

    def test_create_panel_focus_group_with_options(self) -> None:
        """Test creating panel focus group with all options."""
        shortcuts = ["ctrl+p", "f1"]
        priority_value = 5

        group = create_panel_focus_group(
            "Projects Panel",
            "projects-panel",
            priority=priority_value,
            shortcuts=shortcuts,
        )

        assert group.name == "projects_panel"

        widget = group.widgets[0]
        assert widget.widget_id == "projects-panel"
        assert widget.display_name == "Projects Panel"
        assert widget.focus_priority == priority_value
        assert widget.keyboard_shortcuts == shortcuts


class TestGlobalFocusManager:
    """Test global focus manager instance."""

    def test_global_focus_manager_exists(self) -> None:
        """Test that global focus_manager instance exists."""
        assert focus_manager is not None
        assert isinstance(focus_manager, FocusManager)

    def test_global_focus_manager_initially_empty(self) -> None:
        """Test that global focus manager starts empty."""
        # Clear any existing state
        focus_manager.clear_all()

        assert focus_manager.focus_groups == {}
        assert focus_manager.current_focus is None
        assert focus_manager.focus_history == []


class TestFocusManagerIntegration:
    """Integration tests for focus management system."""

    def test_complete_focus_workflow(self) -> None:
        """Test complete focus management workflow."""
        manager = FocusManager()

        # Create widgets with different priorities
        high_priority = FocusableWidget(
            "high",
            "High Priority",
            focus_priority=10,
        )
        medium_priority = FocusableWidget(
            "medium",
            "Medium Priority",
            focus_priority=5,
        )
        low_priority = FocusableWidget(
            "low",
            "Low Priority",
            focus_priority=1,
        )

        # Register widgets
        manager.register_focusable("group1", high_priority)
        manager.register_focusable("group1", medium_priority)
        manager.register_focusable("group2", low_priority)

        # Test focus first available (should be highest priority)
        result = manager.focus_first_available()
        assert result == "high"

        # Test navigation within group
        next_result = manager.move_focus(FocusDirection.NEXT)
        assert next_result == "medium"

        # Test cross-group navigation
        next_result = manager.move_focus(
            FocusDirection.NEXT,
            FocusScope.ALL_PANELS,
        )
        assert next_result == "low"

        # Test context switching
        manager.push_focus_context("high")
        assert manager.current_focus == "high"

        # Test context restoration
        manager.pop_focus_context()
        assert manager.current_focus == "low"

        # Test escape handling
        result = manager.handle_escape_context()
        assert result is True

    def test_focus_with_unfocusable_widgets(self) -> None:
        """Test focus management with mix of focusable and unfocusable widgets."""
        manager = FocusManager()

        widgets = [
            FocusableWidget("widget1", "Widget 1", can_focus=True),
            FocusableWidget("widget2", "Widget 2", can_focus=False),
            FocusableWidget("widget3", "Widget 3", can_focus=True),
            FocusableWidget("widget4", "Widget 4", can_focus=False),
            FocusableWidget("widget5", "Widget 5", can_focus=True),
        ]

        for widget in widgets:
            manager.register_focusable("test", widget)

        # Should focus first focusable widget
        result = manager.focus_first_available()
        assert result == "widget1"

        # Should skip unfocusable widgets
        next_result = manager.move_focus(FocusDirection.NEXT)
        assert next_result == "widget3"

        next_result = manager.move_focus(FocusDirection.NEXT)
        assert next_result == "widget5"

    def test_complex_group_navigation(self) -> None:
        """Test navigation across multiple groups."""
        manager = FocusManager()

        # Create multiple groups
        for group_num in range(1, 4):
            for widget_num in range(1, 3):
                widget_id = f"g{group_num}w{widget_num}"
                widget = FocusableWidget(
                    widget_id,
                    f"Group {group_num} Widget {widget_num}",
                    focus_priority=widget_num,
                )
                manager.register_focusable(f"group{group_num}", widget)

        # Start at first widget of first group
        manager.set_focus("g1w2")  # Higher priority widget

        # Navigate through groups
        current = "g1w2"
        expected_path = ["g1w1", "g2w2", "g2w1", "g3w2", "g3w1", "g1w2"]

        for expected in expected_path:
            current = manager.move_focus(
                FocusDirection.NEXT,
                FocusScope.ALL_PANELS,
            )
            assert current == expected

    def test_keyboard_shortcuts_integration(self) -> None:
        """Test keyboard shortcuts integration."""
        manager = FocusManager()

        widgets = [
            FocusableWidget(
                "projects",
                "Projects",
                keyboard_shortcuts=["ctrl+1", "f1"],
            ),
            FocusableWidget(
                "feed",
                "Feed",
                keyboard_shortcuts=["ctrl+2", "f2"],
            ),
            FocusableWidget("search", "Search"),  # No shortcuts
        ]

        for widget in widgets:
            manager.register_focusable("test", widget)

        shortcuts = manager.get_keyboard_shortcuts()

        expected = {
            "ctrl+1": "projects",
            "f1": "projects",
            "ctrl+2": "feed",
            "f2": "feed",
        }

        assert shortcuts == expected
