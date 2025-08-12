"""Tests for focus management system."""

from __future__ import annotations

from src.tui.utils.focus import (
    FocusableWidget,
    FocusDirection,
    FocusGroup,
    FocusManager,
    FocusScope,
    create_panel_focus_group,
    focus_manager,
)

# Test constants
MAX_FOCUS_HISTORY = 10
PROJECTS_PANEL_ID = "projects-panel"
FEED_PANEL_ID = "live-feed-panel"
TEST_WIDGET_ID = "test-widget"
TEST_GROUP_NAME = "test-group"
PROJECTS_PRIORITY = 10
FEED_PRIORITY = 9
TEST_PRIORITY = 5


class MockFocusHandler:
    """Mock focus handler for testing."""

    def __init__(self) -> None:
        """Initialize mock handler."""
        self.focus_gained_count = 0
        self.focus_lost_count = 0
        self.focus_enter_count = 0
        self.focus_enter_result = True
        self.can_focus = True

    def on_focus_gained(self) -> None:
        """Handle gaining focus."""
        self.focus_gained_count += 1

    def on_focus_lost(self) -> None:
        """Handle losing focus."""
        self.focus_lost_count += 1

    def on_focus_enter(self) -> bool:
        """Handle enter key when focused."""
        self.focus_enter_count += 1
        return self.focus_enter_result

    def can_receive_focus(self) -> bool:
        """Check if widget can currently receive focus."""
        return self.can_focus


class TestFocusDirection:
    """Test FocusDirection enum."""

    def test_direction_values(self) -> None:
        """Test direction enum values."""
        assert FocusDirection.UP.value == "up"
        assert FocusDirection.DOWN.value == "down"
        assert FocusDirection.LEFT.value == "left"
        assert FocusDirection.RIGHT.value == "right"
        assert FocusDirection.NEXT.value == "next"
        assert FocusDirection.PREVIOUS.value == "previous"
        assert FocusDirection.FIRST.value == "first"
        assert FocusDirection.LAST.value == "last"


class TestFocusScope:
    """Test FocusScope enum."""

    def test_scope_values(self) -> None:
        """Test scope enum values."""
        assert FocusScope.CURRENT_PANEL.value == "current_panel"
        assert FocusScope.ALL_PANELS.value == "all_panels"
        assert FocusScope.WITHIN_WIDGET.value == "within_widget"
        assert FocusScope.GLOBAL.value == "global"


class TestFocusableWidget:
    """Test FocusableWidget dataclass."""

    def test_default_widget(self) -> None:
        """Test widget with default values."""
        widget = FocusableWidget(
            widget_id=TEST_WIDGET_ID,
            display_name="Test Widget",
        )

        assert widget.widget_id == TEST_WIDGET_ID
        assert widget.display_name == "Test Widget"
        assert widget.can_focus is True
        assert widget.focus_priority == 0
        assert widget.focus_group == "default"
        assert widget.tooltip == ""
        assert widget.keyboard_shortcuts == []

    def test_custom_widget(self) -> None:
        """Test widget with custom values."""
        shortcuts = ["ctrl+t", "alt+t"]
        widget = FocusableWidget(
            widget_id=TEST_WIDGET_ID,
            display_name="Test Widget",
            can_focus=False,
            focus_priority=TEST_PRIORITY,
            focus_group="custom",
            tooltip="Test tooltip",
            keyboard_shortcuts=shortcuts,
        )

        assert widget.widget_id == TEST_WIDGET_ID
        assert widget.display_name == "Test Widget"
        assert widget.can_focus is False
        assert widget.focus_priority == TEST_PRIORITY
        assert widget.focus_group == "custom"
        assert widget.tooltip == "Test tooltip"
        assert widget.keyboard_shortcuts == shortcuts

    def test_post_init_shortcuts(self) -> None:
        """Test __post_init__ initializes shortcuts list."""
        widget = FocusableWidget(
            widget_id=TEST_WIDGET_ID,
            display_name="Test Widget",
            keyboard_shortcuts=None,
        )

        assert widget.keyboard_shortcuts == []


class TestFocusHandler:
    """Test FocusHandler protocol."""

    def test_mock_handler(self) -> None:
        """Test mock handler implements protocol correctly."""
        handler = MockFocusHandler()

        # Test initial state
        assert handler.focus_gained_count == 0
        assert handler.focus_lost_count == 0
        assert handler.focus_enter_count == 0
        assert handler.can_receive_focus() is True

        # Test method calls
        handler.on_focus_gained()
        assert handler.focus_gained_count == 1

        handler.on_focus_lost()
        assert handler.focus_lost_count == 1

        result = handler.on_focus_enter()
        assert result is True
        assert handler.focus_enter_count == 1


class TestFocusGroup:
    """Test FocusGroup functionality."""

    def test_empty_group(self) -> None:
        """Test empty focus group."""
        group = FocusGroup(name=TEST_GROUP_NAME, widgets=[])

        assert group.name == TEST_GROUP_NAME
        assert group.widgets == []
        assert group.wrap_around is True
        assert group.default_focus is None
        assert group.description == ""

    def test_custom_group(self) -> None:
        """Test focus group with custom settings."""
        widget = FocusableWidget(TEST_WIDGET_ID, "Test")
        group = FocusGroup(
            name=TEST_GROUP_NAME,
            widgets=[widget],
            wrap_around=False,
            default_focus=TEST_WIDGET_ID,
            description="Test group",
        )

        assert group.name == TEST_GROUP_NAME
        assert len(group.widgets) == 1
        assert group.wrap_around is False
        assert group.default_focus == TEST_WIDGET_ID
        assert group.description == "Test group"

    def test_get_widget_by_id(self) -> None:
        """Test getting widget by ID."""
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        group = FocusGroup(TEST_GROUP_NAME, [widget1, widget2])

        found = group.get_widget_by_id("widget1")
        assert found is widget1

        found = group.get_widget_by_id("widget2")
        assert found is widget2

        found = group.get_widget_by_id("nonexistent")
        assert found is None

    def test_get_next_widget(self) -> None:
        """Test getting next focusable widget."""
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        widget3 = FocusableWidget("widget3", "Widget 3", can_focus=False)
        group = FocusGroup(TEST_GROUP_NAME, [widget1, widget2, widget3])

        # Next after widget1 should be widget2 (skipping unfocusable widget3)
        next_widget = group.get_next_widget("widget1")
        assert next_widget is widget2

        # Next after widget2 should wrap to widget1
        next_widget = group.get_next_widget("widget2")
        assert next_widget is widget1

        # Non-existent widget should return None
        next_widget = group.get_next_widget("nonexistent")
        assert next_widget is None

    def test_get_next_widget_no_wrap(self) -> None:
        """Test getting next widget without wrap-around."""
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        group = FocusGroup(
            TEST_GROUP_NAME,
            [widget1, widget2],
            wrap_around=False,
        )

        # Next after widget1 should be widget2
        next_widget = group.get_next_widget("widget1")
        assert next_widget is widget2

        # Next after widget2 should be None (no wrap)
        next_widget = group.get_next_widget("widget2")
        assert next_widget is None

    def test_get_previous_widget(self) -> None:
        """Test getting previous focusable widget."""
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        widget3 = FocusableWidget("widget3", "Widget 3", can_focus=False)
        group = FocusGroup(TEST_GROUP_NAME, [widget1, widget2, widget3])

        # Previous before widget2 should be widget1 (skipping unfocusable widget3)
        prev_widget = group.get_previous_widget("widget2")
        assert prev_widget is widget1

        # Previous before widget1 should wrap to widget2
        prev_widget = group.get_previous_widget("widget1")
        assert prev_widget is widget2

    def test_get_previous_widget_no_wrap(self) -> None:
        """Test getting previous widget without wrap-around."""
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        group = FocusGroup(
            TEST_GROUP_NAME,
            [widget1, widget2],
            wrap_around=False,
        )

        # Previous before widget2 should be widget1
        prev_widget = group.get_previous_widget("widget2")
        assert prev_widget is widget1

        # Previous before widget1 should be None (no wrap)
        prev_widget = group.get_previous_widget("widget1")
        assert prev_widget is None


class TestFocusManager:
    """Test FocusManager functionality."""

    def test_initialization(self) -> None:
        """Test focus manager initialization."""
        manager = FocusManager()

        assert isinstance(manager.focus_groups, dict)
        assert len(manager.focus_groups) == 0
        assert manager.current_focus is None
        assert isinstance(manager.focus_history, list)
        assert len(manager.focus_history) == 0
        assert isinstance(manager.focus_stack, list)
        assert len(manager.focus_stack) == 0
        assert isinstance(manager.focus_observers, list)
        assert len(manager.focus_observers) == 0

    def test_register_focus_group(self) -> None:
        """Test registering focus groups."""
        manager = FocusManager()
        widget = FocusableWidget(TEST_WIDGET_ID, "Test")
        group = FocusGroup(TEST_GROUP_NAME, [widget])

        manager.register_focus_group(group)
        assert TEST_GROUP_NAME in manager.focus_groups
        assert manager.focus_groups[TEST_GROUP_NAME] is group

    def test_register_focusable(self) -> None:
        """Test registering focusable widgets."""
        manager = FocusManager()
        widget1 = FocusableWidget(
            "widget1",
            "Widget 1",
            focus_priority=PROJECTS_PRIORITY,
        )
        widget2 = FocusableWidget(
            "widget2",
            "Widget 2",
            focus_priority=FEED_PRIORITY,
        )

        # Register widgets to same group
        manager.register_focusable(TEST_GROUP_NAME, widget1)
        manager.register_focusable(TEST_GROUP_NAME, widget2)

        # Group should be created automatically
        assert TEST_GROUP_NAME in manager.focus_groups
        group = manager.focus_groups[TEST_GROUP_NAME]
        expected_widget_count = 2
        assert len(group.widgets) == expected_widget_count

        # Widgets should be sorted by priority (highest first)
        assert group.widgets[0].widget_id == "widget1"  # Higher priority
        assert group.widgets[1].widget_id == "widget2"  # Lower priority

    def test_register_focusable_replaces_duplicate(self) -> None:
        """Test that registering same widget ID replaces the old one."""
        manager = FocusManager()
        widget1 = FocusableWidget(TEST_WIDGET_ID, "Widget 1")
        widget2 = FocusableWidget(TEST_WIDGET_ID, "Widget 2")

        manager.register_focusable(TEST_GROUP_NAME, widget1)
        manager.register_focusable(TEST_GROUP_NAME, widget2)

        group = manager.focus_groups[TEST_GROUP_NAME]
        assert len(group.widgets) == 1
        assert group.widgets[0].display_name == "Widget 2"

    def test_unregister_focusable(self) -> None:
        """Test unregistering focusable widgets."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")

        manager.register_focusable(TEST_GROUP_NAME, widget1)
        manager.register_focusable("other_group", widget2)

        # Remove widget1 from all groups
        manager.unregister_focusable("widget1")

        group = manager.focus_groups[TEST_GROUP_NAME]
        assert len(group.widgets) == 0

        other_group = manager.focus_groups["other_group"]
        assert len(other_group.widgets) == 1  # widget2 should still be there

    def test_get_focusable_widgets(self) -> None:
        """Test getting focusable widgets."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")

        manager.register_focusable("group1", widget1)
        manager.register_focusable("group2", widget2)

        # Get all widgets
        all_widgets = manager.get_focusable_widgets()
        expected_total_widgets = 2
        assert len(all_widgets) == expected_total_widgets

        # Get widgets from specific group
        group1_widgets = manager.get_focusable_widgets("group1")
        assert len(group1_widgets) == 1
        assert group1_widgets[0].widget_id == "widget1"

        # Get widgets from non-existent group
        empty_widgets = manager.get_focusable_widgets("nonexistent")
        assert len(empty_widgets) == 0

    def test_focus_first_available(self) -> None:
        """Test focusing first available widget."""
        manager = FocusManager()
        widget1 = FocusableWidget(
            "widget1",
            "Widget 1",
            focus_priority=TEST_PRIORITY,
        )
        widget2 = FocusableWidget(
            "widget2",
            "Widget 2",
            focus_priority=PROJECTS_PRIORITY,
        )

        manager.register_focusable(TEST_GROUP_NAME, widget1)
        manager.register_focusable(TEST_GROUP_NAME, widget2)

        # Should focus highest priority widget
        focused = manager.focus_first_available()
        assert focused == "widget2"  # Higher priority
        assert manager.current_focus == "widget2"

    def test_focus_first_available_no_widgets(self) -> None:
        """Test focusing first available with no widgets."""
        manager = FocusManager()

        focused = manager.focus_first_available()
        assert focused is None
        assert manager.current_focus is None

    def test_focus_last_available(self) -> None:
        """Test focusing last available widget."""
        manager = FocusManager()
        widget1 = FocusableWidget(
            "widget1",
            "Widget 1",
            focus_priority=TEST_PRIORITY,
        )
        widget2 = FocusableWidget(
            "widget2",
            "Widget 2",
            focus_priority=PROJECTS_PRIORITY,
        )

        manager.register_focusable(TEST_GROUP_NAME, widget1)
        manager.register_focusable(TEST_GROUP_NAME, widget2)

        # Should focus last widget in priority order
        focused = manager.focus_last_available()
        assert focused == "widget1"  # Lower priority, so last
        assert manager.current_focus == "widget1"

    def test_set_focus(self) -> None:
        """Test setting focus to specific widget."""
        manager = FocusManager()
        widget = FocusableWidget(TEST_WIDGET_ID, "Test Widget")
        manager.register_focusable(TEST_GROUP_NAME, widget)

        # Set focus to existing widget
        result = manager.set_focus(TEST_WIDGET_ID)
        assert result == TEST_WIDGET_ID
        assert manager.current_focus == TEST_WIDGET_ID

        # Try to set focus to non-existent widget
        result = manager.set_focus("nonexistent")
        assert result is None
        assert (
            manager.current_focus == TEST_WIDGET_ID
        )  # Should remain unchanged

    def test_set_focus_updates_history(self) -> None:
        """Test that setting focus updates history."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")

        manager.register_focusable(TEST_GROUP_NAME, widget1)
        manager.register_focusable(TEST_GROUP_NAME, widget2)

        # Focus first widget
        manager.set_focus("widget1")
        assert len(manager.focus_history) == 0  # No previous focus

        # Focus second widget
        manager.set_focus("widget2")
        assert len(manager.focus_history) == 1
        assert manager.focus_history[0] == "widget1"

    def test_focus_history_limit(self) -> None:
        """Test that focus history is limited."""
        manager = FocusManager()

        # Register many widgets
        for i in range(MAX_FOCUS_HISTORY + 5):
            widget = FocusableWidget(f"widget{i}", f"Widget {i}")
            manager.register_focusable(TEST_GROUP_NAME, widget)

        # Focus them in sequence
        for i in range(MAX_FOCUS_HISTORY + 5):
            manager.set_focus(f"widget{i}")

        # History should be limited to MAX_FOCUS_HISTORY
        assert len(manager.focus_history) == MAX_FOCUS_HISTORY

    def test_focus_previous_in_history(self) -> None:
        """Test focusing previous widget from history."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")

        manager.register_focusable(TEST_GROUP_NAME, widget1)
        manager.register_focusable(TEST_GROUP_NAME, widget2)

        # Build some history
        manager.set_focus("widget1")
        manager.set_focus("widget2")

        # Go back to previous
        prev_focus = manager.focus_previous_in_history()
        assert prev_focus == "widget1"
        assert manager.current_focus == "widget1"

    def test_focus_previous_in_history_empty(self) -> None:
        """Test focusing previous with empty history."""
        manager = FocusManager()

        result = manager.focus_previous_in_history()
        assert result is None

    def test_push_pop_focus_context(self) -> None:
        """Test focus stack for modal contexts."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")

        manager.register_focusable(TEST_GROUP_NAME, widget1)
        manager.register_focusable(TEST_GROUP_NAME, widget2)

        # Set initial focus
        manager.set_focus("widget1")

        # Push modal focus
        manager.push_focus_context("widget2")
        assert manager.current_focus == "widget2"
        assert len(manager.focus_stack) == 1
        assert manager.focus_stack[0] == "widget1"

        # Pop focus context
        restored = manager.pop_focus_context()
        assert restored == "widget1"
        assert manager.current_focus == "widget1"
        assert len(manager.focus_stack) == 0

    def test_pop_focus_context_empty_stack(self) -> None:
        """Test popping focus with empty stack."""
        manager = FocusManager()

        result = manager.pop_focus_context()
        assert result is None

    def test_get_focus_info(self) -> None:
        """Test getting focus information."""
        manager = FocusManager()
        widget = FocusableWidget(TEST_WIDGET_ID, "Test Widget")
        manager.register_focusable(TEST_GROUP_NAME, widget)

        # Get info for specific widget
        info = manager.get_focus_info(TEST_WIDGET_ID)
        assert info is widget

        # Get info for current focus
        manager.set_focus(TEST_WIDGET_ID)
        info = manager.get_focus_info()
        assert info is widget

        # Get info for non-existent widget
        info = manager.get_focus_info("nonexistent")
        assert info is None

    def test_get_keyboard_shortcuts(self) -> None:
        """Test getting keyboard shortcuts mapping."""
        manager = FocusManager()
        widget1 = FocusableWidget(
            "widget1",
            "Widget 1",
            keyboard_shortcuts=["ctrl+1"],
        )
        widget2 = FocusableWidget(
            "widget2",
            "Widget 2",
            keyboard_shortcuts=["ctrl+2", "alt+2"],
        )

        manager.register_focusable(TEST_GROUP_NAME, widget1)
        manager.register_focusable(TEST_GROUP_NAME, widget2)

        shortcuts = manager.get_keyboard_shortcuts()
        assert shortcuts["ctrl+1"] == "widget1"
        assert shortcuts["ctrl+2"] == "widget2"
        assert shortcuts["alt+2"] == "widget2"

    def test_focus_observers(self) -> None:
        """Test focus change observers."""
        manager = FocusManager()
        observer = MockFocusHandler()

        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")
        manager.register_focusable(TEST_GROUP_NAME, widget1)
        manager.register_focusable(TEST_GROUP_NAME, widget2)

        # Add observer
        manager.add_focus_observer(observer)
        assert observer in manager.focus_observers

        # Focus changes should notify observers
        # (though our mock doesn't have on_focus_changed)
        manager.set_focus("widget1")
        manager.set_focus("widget2")

        # Remove observer
        manager.remove_focus_observer(observer)
        assert observer not in manager.focus_observers

    def test_clear_all(self) -> None:
        """Test clearing all focus state."""
        manager = FocusManager()
        widget = FocusableWidget(TEST_WIDGET_ID, "Test Widget")
        manager.register_focusable(TEST_GROUP_NAME, widget)
        manager.set_focus(TEST_WIDGET_ID)

        # Clear everything
        manager.clear_all()

        assert len(manager.focus_groups) == 0
        assert manager.current_focus is None
        assert len(manager.focus_history) == 0
        assert len(manager.focus_stack) == 0


class TestFocusMovement:
    """Test focus movement methods."""

    def test_move_focus_no_current_focus(self) -> None:
        """Test move focus with no current focus."""
        manager = FocusManager()
        widget = FocusableWidget(TEST_WIDGET_ID, "Test Widget")
        manager.register_focusable(TEST_GROUP_NAME, widget)

        # Should focus first available
        result = manager.move_focus(FocusDirection.NEXT)
        assert result == TEST_WIDGET_ID

    def test_move_focus_first_last(self) -> None:
        """Test moving to first and last widgets."""
        manager = FocusManager()
        widget1 = FocusableWidget(
            "widget1",
            "Widget 1",
            focus_priority=PROJECTS_PRIORITY,
        )
        widget2 = FocusableWidget(
            "widget2",
            "Widget 2",
            focus_priority=TEST_PRIORITY,
        )

        manager.register_focusable(TEST_GROUP_NAME, widget1)
        manager.register_focusable(TEST_GROUP_NAME, widget2)
        manager.set_focus("widget2")  # Start with lower priority widget

        # Move to first (highest priority)
        result = manager.move_focus(FocusDirection.FIRST)
        assert result == "widget1"

        # Move to last (lowest priority)
        result = manager.move_focus(FocusDirection.LAST)
        assert result == "widget2"

    def test_move_focus_directional(self) -> None:
        """Test directional focus movement."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1")
        widget2 = FocusableWidget("widget2", "Widget 2")

        manager.register_focusable(TEST_GROUP_NAME, widget1)
        manager.register_focusable(TEST_GROUP_NAME, widget2)
        manager.set_focus("widget1")

        # Down/Right should move to next
        result = manager.move_focus(FocusDirection.DOWN)
        assert result == "widget2"

        # Up/Left should move to previous
        result = manager.move_focus(FocusDirection.UP)
        assert result == "widget1"


class TestCreatePanelFocusGroup:
    """Test panel focus group creation helper."""

    def test_create_panel_focus_group(self) -> None:
        """Test creating panel focus group."""
        shortcuts = ["ctrl+p", "1"]
        group = create_panel_focus_group(
            "Projects",
            PROJECTS_PANEL_ID,
            priority=PROJECTS_PRIORITY,
            shortcuts=shortcuts,
        )

        assert group.name == "projects"
        assert len(group.widgets) == 1

        widget = group.widgets[0]
        assert widget.widget_id == PROJECTS_PANEL_ID
        assert widget.display_name == "Projects"
        assert widget.focus_priority == PROJECTS_PRIORITY
        assert widget.keyboard_shortcuts == shortcuts
        assert group.description == "Projects panel focus group"

    def test_create_panel_focus_group_defaults(self) -> None:
        """Test creating panel focus group with defaults."""
        group = create_panel_focus_group("Live Feed", FEED_PANEL_ID)

        assert group.name == "live_feed"
        widget = group.widgets[0]
        assert widget.focus_priority == 0
        assert widget.keyboard_shortcuts == []


class TestGlobalFocusManager:
    """Test global focus manager instance."""

    def test_global_manager_exists(self) -> None:
        """Test that global focus manager exists."""
        assert focus_manager is not None
        assert isinstance(focus_manager, FocusManager)

    def test_global_manager_isolation(self) -> None:
        """Test that global manager doesn't affect local instances."""
        local_manager = FocusManager()
        widget = FocusableWidget(TEST_WIDGET_ID, "Test Widget")

        # Register widget only to local manager
        local_manager.register_focusable(TEST_GROUP_NAME, widget)

        # Global manager should not have the widget
        local_widgets = local_manager.get_focusable_widgets()
        global_widgets = focus_manager.get_focusable_widgets()

        assert len(local_widgets) == 1
        assert len(global_widgets) == 0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_unfocusable_widget(self) -> None:
        """Test handling unfocusable widgets."""
        manager = FocusManager()
        widget = FocusableWidget(
            TEST_WIDGET_ID,
            "Test Widget",
            can_focus=False,
        )
        manager.register_focusable(TEST_GROUP_NAME, widget)

        # Should not be able to focus unfocusable widget
        result = manager.set_focus(TEST_WIDGET_ID)
        assert result is None
        assert manager.current_focus is None

    def test_empty_groups(self) -> None:
        """Test handling empty focus groups."""
        manager = FocusManager()
        empty_group = FocusGroup("empty", [])
        manager.register_focus_group(empty_group)

        # Should handle empty groups gracefully
        result = manager.focus_first_available()
        assert result is None

    def test_all_widgets_unfocusable(self) -> None:
        """Test when all widgets are unfocusable."""
        manager = FocusManager()
        widget1 = FocusableWidget("widget1", "Widget 1", can_focus=False)
        widget2 = FocusableWidget("widget2", "Widget 2", can_focus=False)

        manager.register_focusable(TEST_GROUP_NAME, widget1)
        manager.register_focusable(TEST_GROUP_NAME, widget2)

        # Should not focus any widget
        result = manager.focus_first_available()
        assert result is None

    def test_focus_nonexistent_widget(self) -> None:
        """Test focusing non-existent widget."""
        manager = FocusManager()

        result = manager.set_focus("nonexistent")
        assert result is None
        assert manager.current_focus is None

    def test_move_focus_empty_manager(self) -> None:
        """Test moving focus with no widgets registered."""
        manager = FocusManager()

        result = manager.move_focus(FocusDirection.NEXT)
        assert result is None

    def test_observer_error_handling(self) -> None:
        """Test that observer errors don't break focus management."""
        manager = FocusManager()
        widget = FocusableWidget(TEST_WIDGET_ID, "Test Widget")
        manager.register_focusable(TEST_GROUP_NAME, widget)

        class FailingObserver:
            def on_focus_changed(
                self,
                _old_focus: str | None,
                _new_focus: str,
            ) -> None:
                msg = "Observer failed"
                raise RuntimeError(msg)

        failing_observer = FailingObserver()
        manager.add_focus_observer(failing_observer)  # type: ignore[arg-type]

        # Should not raise exception despite observer error
        result = manager.set_focus(TEST_WIDGET_ID)
        assert result == TEST_WIDGET_ID
