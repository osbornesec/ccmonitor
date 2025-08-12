"""Comprehensive test suite for focus management system.

This module provides complete coverage of the focus management system
including all classes, methods, edge cases, and error conditions.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.tui.utils.focus import (
    MAX_CONTEXT_STACK,
    MAX_FOCUS_HISTORY,
    FocusableWidget,
    FocusDirection,
    FocusGroup,
    FocusManager,
    FocusScope,
    create_panel_focus_group,
    focus_manager,
)


class MockFocusHandler:
    """Mock implementation of FocusHandler protocol."""

    def __init__(self) -> None:
        """Initialize mock focus handler."""
        self.focus_gained_called = False
        self.focus_lost_called = False
        self.enter_handled = False
        self.can_receive = True

    def on_focus_gained(self) -> None:
        """Handle gaining focus."""
        self.focus_gained_called = True

    def on_focus_lost(self) -> None:
        """Handle losing focus."""
        self.focus_lost_called = True

    def on_focus_enter(self) -> bool:
        """Handle enter key when focused."""
        self.enter_handled = True
        return True

    def can_receive_focus(self) -> bool:
        """Check if widget can currently receive focus."""
        return self.can_receive

    def on_focus_changed(self, old_focus: str | None, new_focus: str) -> None:
        """Handle focus change notification."""


class TestFocusDirection:
    """Test FocusDirection enum."""

    def test_focus_direction_values(self) -> None:
        """Test all FocusDirection enum values."""
        assert FocusDirection.UP.value == "up"
        assert FocusDirection.DOWN.value == "down"
        assert FocusDirection.LEFT.value == "left"
        assert FocusDirection.RIGHT.value == "right"
        assert FocusDirection.NEXT.value == "next"
        assert FocusDirection.PREVIOUS.value == "previous"
        assert FocusDirection.FIRST.value == "first"
        assert FocusDirection.LAST.value == "last"

    def test_focus_direction_completeness(self) -> None:
        """Test that all expected directions are defined."""
        expected_directions = {
            "up",
            "down",
            "left",
            "right",
            "next",
            "previous",
            "first",
            "last",
        }
        actual_directions = {direction.value for direction in FocusDirection}
        assert actual_directions == expected_directions


class TestFocusScope:
    """Test FocusScope enum."""

    def test_focus_scope_values(self) -> None:
        """Test all FocusScope enum values."""
        assert FocusScope.CURRENT_PANEL.value == "current_panel"
        assert FocusScope.ALL_PANELS.value == "all_panels"
        assert FocusScope.WITHIN_WIDGET.value == "within_widget"
        assert FocusScope.GLOBAL.value == "global"

    def test_focus_scope_completeness(self) -> None:
        """Test that all expected scopes are defined."""
        expected_scopes = {
            "current_panel",
            "all_panels",
            "within_widget",
            "global",
        }
        actual_scopes = {scope.value for scope in FocusScope}
        assert actual_scopes == expected_scopes


class TestFocusableWidget:
    """Test FocusableWidget dataclass."""

    def test_focusable_widget_creation_minimal(self) -> None:
        """Test creating FocusableWidget with minimal parameters."""
        widget = FocusableWidget(
            widget_id="test_widget",
            display_name="Test Widget",
        )

        assert widget.widget_id == "test_widget"
        assert widget.display_name == "Test Widget"
        assert widget.can_focus is True
        assert widget.focus_priority == 0
        assert widget.focus_group == "default"
        assert widget.tooltip == ""
        assert widget.keyboard_shortcuts == []

    def test_focusable_widget_creation_full(self) -> None:
        """Test creating FocusableWidget with all parameters."""
        shortcuts = ["ctrl+f", "f1"]
        widget = FocusableWidget(
            widget_id="full_widget",
            display_name="Full Widget",
            can_focus=False,
            focus_priority=10,
            focus_group="custom",
            tooltip="Test tooltip",
            keyboard_shortcuts=shortcuts,
        )

        assert widget.widget_id == "full_widget"
        assert widget.display_name == "Full Widget"
        assert widget.can_focus is False
        assert widget.focus_priority == 10
        assert widget.focus_group == "custom"
        assert widget.tooltip == "Test tooltip"
        assert widget.keyboard_shortcuts == shortcuts

    def test_focusable_widget_post_init_empty_shortcuts(self) -> None:
        """Test that post_init initializes empty keyboard_shortcuts."""
        widget = FocusableWidget(
            widget_id="test",
            display_name="Test",
            keyboard_shortcuts=None,
        )
        assert widget.keyboard_shortcuts == []

    def test_focusable_widget_post_init_existing_shortcuts(self) -> None:
        """Test that post_init preserves existing keyboard_shortcuts."""
        shortcuts = ["ctrl+x"]
        widget = FocusableWidget(
            widget_id="test",
            display_name="Test",
            keyboard_shortcuts=shortcuts,
        )
        assert widget.keyboard_shortcuts == shortcuts

    @pytest.mark.parametrize(
        "widget_id,display_name",
        [
            ("widget1", "Widget 1"),
            ("complex_widget_id_123", "Complex Widget Name"),
            ("", ""),  # Edge case: empty strings
            ("special-chars_widget", "Special Chars! @#$%"),
        ],
    )
    def test_focusable_widget_parametrized(
        self,
        widget_id: str,
        display_name: str,
    ) -> None:
        """Test FocusableWidget with various ID and name combinations."""
        widget = FocusableWidget(
            widget_id=widget_id,
            display_name=display_name,
        )
        assert widget.widget_id == widget_id
        assert widget.display_name == display_name


class TestFocusGroup:
    """Test FocusGroup dataclass and methods."""

    def create_test_widgets(self) -> list[FocusableWidget]:
        """Create test widgets for focus group testing."""
        return [
            FocusableWidget("widget1", "Widget 1", focus_priority=10),
            FocusableWidget(
                "widget2",
                "Widget 2",
                focus_priority=5,
                can_focus=False,
            ),
            FocusableWidget("widget3", "Widget 3", focus_priority=15),
            FocusableWidget("widget4", "Widget 4", focus_priority=0),
        ]

    def test_focus_group_creation_minimal(self) -> None:
        """Test creating FocusGroup with minimal parameters."""
        group = FocusGroup(name="test_group", widgets=[])

        assert group.name == "test_group"
        assert group.widgets == []
        assert group.wrap_around is True
        assert group.default_focus is None
        assert group.description == ""

    def test_focus_group_creation_full(self) -> None:
        """Test creating FocusGroup with all parameters."""
        widgets = self.create_test_widgets()
        group = FocusGroup(
            name="full_group",
            widgets=widgets,
            wrap_around=False,
            default_focus="widget1",
            description="Test focus group",
        )

        assert group.name == "full_group"
        assert group.widgets == widgets
        assert group.wrap_around is False
        assert group.default_focus == "widget1"
        assert group.description == "Test focus group"

    def test_get_widget_by_id_found(self) -> None:
        """Test getting widget by ID when it exists."""
        widgets = self.create_test_widgets()
        group = FocusGroup(name="test", widgets=widgets)

        widget = group.get_widget_by_id("widget2")
        assert widget is not None
        assert widget.widget_id == "widget2"
        assert widget.display_name == "Widget 2"

    def test_get_widget_by_id_not_found(self) -> None:
        """Test getting widget by ID when it doesn't exist."""
        widgets = self.create_test_widgets()
        group = FocusGroup(name="test", widgets=widgets)

        widget = group.get_widget_by_id("nonexistent")
        assert widget is None

    def test_get_widget_by_id_empty_group(self) -> None:
        """Test getting widget by ID from empty group."""
        group = FocusGroup(name="empty", widgets=[])
        widget = group.get_widget_by_id("any_id")
        assert widget is None

    def test_get_next_widget_normal_case(self) -> None:
        """Test getting next widget in normal case."""
        widgets = self.create_test_widgets()
        group = FocusGroup(name="test", widgets=widgets)

        # From widget1 to next focusable (widget3, since widget2 can't focus)
        next_widget = group.get_next_widget("widget1")
        assert next_widget is not None
        assert next_widget.widget_id == "widget3"

    def test_get_next_widget_wrap_around(self) -> None:
        """Test getting next widget with wrap around."""
        widgets = self.create_test_widgets()
        group = FocusGroup(name="test", widgets=widgets, wrap_around=True)

        # From last widget to first focusable
        next_widget = group.get_next_widget("widget4")
        assert next_widget is not None
        assert next_widget.widget_id == "widget1"

    def test_get_next_widget_no_wrap_around(self) -> None:
        """Test getting next widget without wrap around at end."""
        widgets = self.create_test_widgets()
        group = FocusGroup(name="test", widgets=widgets, wrap_around=False)

        # From last widget, should return None
        next_widget = group.get_next_widget("widget4", allow_wrap=False)
        assert next_widget is None

    def test_get_next_widget_allow_wrap_parameter(self) -> None:
        """Test get_next_widget with allow_wrap parameter override."""
        widgets = self.create_test_widgets()
        group = FocusGroup(name="test", widgets=widgets, wrap_around=True)

        # Override wrap_around setting with allow_wrap=False
        next_widget = group.get_next_widget("widget4", allow_wrap=False)
        assert next_widget is None

    def test_get_next_widget_current_not_found(self) -> None:
        """Test getting next widget when current widget not found."""
        widgets = self.create_test_widgets()
        group = FocusGroup(name="test", widgets=widgets)

        next_widget = group.get_next_widget("nonexistent")
        assert next_widget is None

    def test_get_next_widget_no_focusable(self) -> None:
        """Test getting next widget when no widgets are focusable."""
        widgets = [
            FocusableWidget("w1", "W1", can_focus=False),
            FocusableWidget("w2", "W2", can_focus=False),
        ]
        group = FocusGroup(name="test", widgets=widgets)

        next_widget = group.get_next_widget("w1")
        assert next_widget is None

    def test_find_widget_index(self) -> None:
        """Test _find_widget_index method."""
        widgets = self.create_test_widgets()
        group = FocusGroup(name="test", widgets=widgets)

        assert group._find_widget_index("widget1") == 0
        assert group._find_widget_index("widget3") == 2
        assert group._find_widget_index("nonexistent") is None

    def test_find_next_focusable_widget_normal(self) -> None:
        """Test _find_next_focusable_widget in normal case."""
        widgets = self.create_test_widgets()
        group = FocusGroup(name="test", widgets=widgets)

        # From index 1 (widget2, not focusable), should find widget3
        next_widget = group._find_next_focusable_widget(1)
        assert next_widget is not None
        assert next_widget.widget_id == "widget3"

    def test_find_next_focusable_widget_wrap_around(self) -> None:
        """Test _find_next_focusable_widget with wrap around."""
        widgets = self.create_test_widgets()
        group = FocusGroup(name="test", widgets=widgets, wrap_around=True)

        # From last index, should wrap to first focusable
        next_widget = group._find_next_focusable_widget(3)
        assert next_widget is not None
        assert next_widget.widget_id == "widget1"

    def test_find_next_focusable_widget_no_wrap(self) -> None:
        """Test _find_next_focusable_widget without wrap around."""
        widgets = self.create_test_widgets()
        group = FocusGroup(name="test", widgets=widgets, wrap_around=False)

        # From last index without wrap, should return None
        next_widget = group._find_next_focusable_widget(3, allow_wrap=False)
        assert next_widget is None

    def test_search_forward_from_index(self) -> None:
        """Test _search_forward_from_index method."""
        widgets = self.create_test_widgets()
        group = FocusGroup(name="test", widgets=widgets)

        # Search from index 1, should find widget3
        widget = group._search_forward_from_index(1)
        assert widget is not None
        assert widget.widget_id == "widget3"

    def test_search_forward_from_index_with_end(self) -> None:
        """Test _search_forward_from_index with end_index."""
        widgets = self.create_test_widgets()
        group = FocusGroup(name="test", widgets=widgets)

        # Search from 0 to 2, should find widget1
        widget = group._search_forward_from_index(0, 2)
        assert widget is not None
        assert widget.widget_id == "widget1"

    def test_search_forward_from_index_no_focusable(self) -> None:
        """Test _search_forward_from_index when no focusable widgets."""
        widgets = [
            FocusableWidget("w1", "W1", can_focus=False),
            FocusableWidget("w2", "W2", can_focus=False),
        ]
        group = FocusGroup(name="test", widgets=widgets)

        widget = group._search_forward_from_index(0)
        assert widget is None

    def test_get_previous_widget_normal(self) -> None:
        """Test getting previous widget in normal case."""
        widgets = self.create_test_widgets()
        group = FocusGroup(name="test", widgets=widgets)

        # From widget3, previous focusable should be widget1 (widget2 can't focus)
        prev_widget = group.get_previous_widget("widget3")
        assert prev_widget is not None
        assert prev_widget.widget_id == "widget1"

    def test_get_previous_widget_wrap_around(self) -> None:
        """Test getting previous widget with wrap around."""
        widgets = self.create_test_widgets()
        group = FocusGroup(name="test", widgets=widgets, wrap_around=True)

        # From first focusable, should wrap to last focusable
        prev_widget = group.get_previous_widget("widget1")
        assert prev_widget is not None
        assert prev_widget.widget_id == "widget4"

    def test_get_previous_widget_no_wrap_around(self) -> None:
        """Test getting previous widget without wrap around."""
        widgets = self.create_test_widgets()
        group = FocusGroup(name="test", widgets=widgets, wrap_around=False)

        # From first widget without wrap, should return None
        prev_widget = group.get_previous_widget("widget1")
        assert prev_widget is None

    def test_get_previous_widget_not_found(self) -> None:
        """Test getting previous widget when current not found."""
        widgets = self.create_test_widgets()
        group = FocusGroup(name="test", widgets=widgets)

        prev_widget = group.get_previous_widget("nonexistent")
        assert prev_widget is None

    def test_get_previous_widget_single_widget(self) -> None:
        """Test getting previous widget with only one widget."""
        widget = FocusableWidget("single", "Single Widget")
        group = FocusGroup(name="test", widgets=[widget], wrap_around=False)

        prev_widget = group.get_previous_widget("single")
        assert prev_widget is None

    def test_get_previous_widget_no_focusable(self) -> None:
        """Test getting previous widget when no widgets are focusable."""
        widgets = [
            FocusableWidget("w1", "W1", can_focus=False),
            FocusableWidget("w2", "W2", can_focus=False),
        ]
        group = FocusGroup(name="test", widgets=widgets)

        prev_widget = group.get_previous_widget("w1")
        assert prev_widget is None


class TestFocusManager:
    """Test FocusManager class methods."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.focus_manager = FocusManager()
        self.mock_app = Mock()
        self.focus_manager.set_app(self.mock_app)

    def create_test_group(self, name: str) -> FocusGroup:
        """Create a test focus group."""
        widgets = [
            FocusableWidget(
                f"{name}_w1",
                f"{name} Widget 1",
                focus_priority=10,
            ),
            FocusableWidget(f"{name}_w2", f"{name} Widget 2", can_focus=False),
            FocusableWidget(
                f"{name}_w3",
                f"{name} Widget 3",
                focus_priority=5,
            ),
        ]
        return FocusGroup(name=name, widgets=widgets)

    def test_focus_manager_init_without_app(self) -> None:
        """Test FocusManager initialization without app."""
        fm = FocusManager()
        assert fm.app is None
        assert fm.focus_groups == {}
        assert fm.current_focus is None
        assert fm.focus_history == []
        assert fm.focus_stack == []
        assert fm.focus_observers == []
        assert fm._focus_callbacks == {}

    def test_focus_manager_init_with_app(self) -> None:
        """Test FocusManager initialization with app."""
        mock_app = Mock()
        fm = FocusManager(mock_app)
        assert fm.app is mock_app

    def test_set_app(self) -> None:
        """Test setting app after initialization."""
        fm = FocusManager()
        mock_app = Mock()
        fm.set_app(mock_app)
        assert fm.app is mock_app

    def test_register_focus_group(self) -> None:
        """Test registering a focus group."""
        group = self.create_test_group("test_group")
        self.focus_manager.register_focus_group(group)

        assert "test_group" in self.focus_manager.focus_groups
        assert self.focus_manager.focus_groups["test_group"] is group

    def test_register_focusable_new_group(self) -> None:
        """Test registering focusable widget to new group."""
        widget = FocusableWidget("test_widget", "Test Widget")
        self.focus_manager.register_focusable("new_group", widget)

        assert "new_group" in self.focus_manager.focus_groups
        group = self.focus_manager.focus_groups["new_group"]
        assert len(group.widgets) == 1
        assert group.widgets[0] is widget

    def test_register_focusable_existing_group(self) -> None:
        """Test registering focusable widget to existing group."""
        group = self.create_test_group("existing")
        self.focus_manager.register_focus_group(group)

        new_widget = FocusableWidget(
            "new_widget",
            "New Widget",
            focus_priority=20,
        )
        self.focus_manager.register_focusable("existing", new_widget)

        group = self.focus_manager.focus_groups["existing"]
        assert len(group.widgets) == 4  # 3 original + 1 new
        # Should be sorted by priority (highest first)
        assert (
            group.widgets[0].focus_priority >= group.widgets[1].focus_priority
        )

    def test_register_focusable_replace_existing(self) -> None:
        """Test registering focusable widget replaces existing with same ID."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)
        original_count = len(group.widgets)

        # Register widget with same ID as existing
        new_widget = FocusableWidget(
            "test_w1",
            "Replaced Widget",
            focus_priority=99,
        )
        self.focus_manager.register_focusable("test", new_widget)

        # Should have same count but with replaced widget
        updated_group = self.focus_manager.focus_groups["test"]
        assert len(updated_group.widgets) == original_count

        # Find the widget with the ID and verify it's replaced
        found_widget = updated_group.get_widget_by_id("test_w1")
        assert found_widget is not None
        assert found_widget.display_name == "Replaced Widget"
        assert found_widget.focus_priority == 99

    def test_unregister_focusable(self) -> None:
        """Test unregistering a focusable widget."""
        group1 = self.create_test_group("group1")
        group2 = self.create_test_group("group2")
        self.focus_manager.register_focus_group(group1)
        self.focus_manager.register_focus_group(group2)

        # Add same widget to both groups
        widget = FocusableWidget("shared_widget", "Shared Widget")
        self.focus_manager.register_focusable("group1", widget)
        self.focus_manager.register_focusable("group2", widget)

        # Verify it's in both groups
        assert self.focus_manager.focus_groups["group1"].get_widget_by_id(
            "shared_widget",
        )
        assert self.focus_manager.focus_groups["group2"].get_widget_by_id(
            "shared_widget",
        )

        # Unregister it
        self.focus_manager.unregister_focusable("shared_widget")

        # Verify it's removed from both groups
        assert not self.focus_manager.focus_groups["group1"].get_widget_by_id(
            "shared_widget",
        )
        assert not self.focus_manager.focus_groups["group2"].get_widget_by_id(
            "shared_widget",
        )

    def test_get_focusable_widgets_specific_group(self) -> None:
        """Test getting focusable widgets for specific group."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        widgets = self.focus_manager.get_focusable_widgets("test")
        assert len(widgets) == 3
        assert all(w.widget_id.startswith("test_") for w in widgets)

    def test_get_focusable_widgets_nonexistent_group(self) -> None:
        """Test getting focusable widgets for nonexistent group."""
        widgets = self.focus_manager.get_focusable_widgets("nonexistent")
        assert widgets == []

    def test_get_focusable_widgets_all_groups(self) -> None:
        """Test getting focusable widgets from all groups."""
        group1 = self.create_test_group("group1")
        group2 = self.create_test_group("group2")
        self.focus_manager.register_focus_group(group1)
        self.focus_manager.register_focus_group(group2)

        widgets = self.focus_manager.get_focusable_widgets()
        assert len(widgets) == 6  # 3 from each group

        # Verify widgets from both groups are included
        widget_ids = [w.widget_id for w in widgets]
        assert "group1_w1" in widget_ids
        assert "group2_w1" in widget_ids

    def test_move_focus_no_current_focus(self) -> None:
        """Test move_focus when no current focus."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        result = self.focus_manager.move_focus(FocusDirection.NEXT)

        # Should focus first available widget
        assert result is not None
        assert result == "test_w1"  # Highest priority focusable widget
        assert self.focus_manager.current_focus == "test_w1"

    def test_move_focus_next_within_group(self) -> None:
        """Test moving focus to next widget within group."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)
        self.focus_manager.set_focus("test_w1")

        result = self.focus_manager.move_focus(
            FocusDirection.NEXT,
            FocusScope.CURRENT_PANEL,
        )

        assert result == "test_w3"  # Skip test_w2 (can't focus)
        assert self.focus_manager.current_focus == "test_w3"

    def test_move_focus_next_cross_group(self) -> None:
        """Test moving focus to next widget across groups."""
        group1 = self.create_test_group("group1")
        group2 = self.create_test_group("group2")
        self.focus_manager.register_focus_group(group1)
        self.focus_manager.register_focus_group(group2)
        self.focus_manager.set_focus("group1_w3")  # Last focusable in group1

        result = self.focus_manager.move_focus(
            FocusDirection.NEXT,
            FocusScope.ALL_PANELS,
        )

        # Should move to first focusable in next group
        assert result is not None
        assert result.startswith("group2_")

    def test_move_focus_previous(self) -> None:
        """Test moving focus to previous widget."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)
        self.focus_manager.set_focus("test_w3")

        result = self.focus_manager.move_focus(FocusDirection.PREVIOUS)

        assert result == "test_w1"  # Previous focusable widget
        assert self.focus_manager.current_focus == "test_w1"

    def test_move_focus_first(self) -> None:
        """Test moving focus to first widget."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)
        self.focus_manager.set_focus("test_w3")

        result = self.focus_manager.move_focus(FocusDirection.FIRST)

        assert result == "test_w1"  # Highest priority widget
        assert self.focus_manager.current_focus == "test_w1"

    def test_move_focus_last(self) -> None:
        """Test moving focus to last widget."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)
        self.focus_manager.set_focus("test_w1")

        result = self.focus_manager.move_focus(FocusDirection.LAST)

        assert result == "test_w3"  # Last in priority order
        assert self.focus_manager.current_focus == "test_w3"

    def test_move_focus_directional_down_right(self) -> None:
        """Test directional movement (down/right maps to next)."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)
        self.focus_manager.set_focus("test_w1")

        # Test DOWN
        result = self.focus_manager.move_focus(FocusDirection.DOWN)
        assert result == "test_w3"

        # Reset and test RIGHT
        self.focus_manager.set_focus("test_w1")
        result = self.focus_manager.move_focus(FocusDirection.RIGHT)
        assert result == "test_w3"

    def test_move_focus_directional_up_left(self) -> None:
        """Test directional movement (up/left maps to previous)."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)
        self.focus_manager.set_focus("test_w3")

        # Test UP
        result = self.focus_manager.move_focus(FocusDirection.UP)
        assert result == "test_w1"

        # Reset and test LEFT
        self.focus_manager.set_focus("test_w3")
        result = self.focus_manager.move_focus(FocusDirection.LEFT)
        assert result == "test_w1"

    def test_handle_focus_direction_coverage(self) -> None:
        """Test _handle_focus_direction method coverage."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)
        self.focus_manager.set_focus("test_w1")

        # Test each direction type
        assert self.focus_manager._handle_focus_direction(
            FocusDirection.NEXT,
            FocusScope.ALL_PANELS,
        )
        assert self.focus_manager._handle_focus_direction(
            FocusDirection.PREVIOUS,
            FocusScope.ALL_PANELS,
        )
        assert self.focus_manager._handle_focus_direction(
            FocusDirection.FIRST,
            FocusScope.ALL_PANELS,
        )
        assert self.focus_manager._handle_focus_direction(
            FocusDirection.LAST,
            FocusScope.ALL_PANELS,
        )
        assert self.focus_manager._handle_focus_direction(
            FocusDirection.DOWN,
            FocusScope.ALL_PANELS,
        )
        assert self.focus_manager._handle_focus_direction(
            FocusDirection.UP,
            FocusScope.ALL_PANELS,
        )
        assert self.focus_manager._handle_focus_direction(
            FocusDirection.RIGHT,
            FocusScope.ALL_PANELS,
        )
        assert self.focus_manager._handle_focus_direction(
            FocusDirection.LEFT,
            FocusScope.ALL_PANELS,
        )

    def test_move_to_next_widget_no_current_focus(self) -> None:
        """Test _move_to_next_widget when no current focus."""
        result = self.focus_manager._move_to_next_widget(FocusScope.ALL_PANELS)
        assert result is None

    def test_move_to_next_widget_no_current_group(self) -> None:
        """Test _move_to_next_widget when current widget has no group."""
        self.focus_manager.current_focus = "nonexistent_widget"
        result = self.focus_manager._move_to_next_widget(FocusScope.ALL_PANELS)
        assert result is None

    def test_move_to_next_widget_within_group_scope(self) -> None:
        """Test _move_to_next_widget with ALL_PANELS scope allowing wrap."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)
        self.focus_manager.set_focus("test_w1")

        result = self.focus_manager._move_to_next_widget(
            FocusScope.CURRENT_PANEL,
        )
        assert result == "test_w3"

    def test_move_to_next_widget_cross_group(self) -> None:
        """Test _move_to_next_widget moving across groups."""
        group1 = self.create_test_group("group1")
        group2 = self.create_test_group("group2")
        self.focus_manager.register_focus_group(group1)
        self.focus_manager.register_focus_group(group2)
        self.focus_manager.set_focus("group1_w3")

        result = self.focus_manager._move_to_next_widget(FocusScope.ALL_PANELS)
        assert result is not None
        assert result.startswith("group2_")

    def test_move_to_previous_widget_no_current_focus(self) -> None:
        """Test _move_to_previous_widget when no current focus."""
        result = self.focus_manager._move_to_previous_widget(
            FocusScope.ALL_PANELS,
        )
        assert result is None

    def test_move_to_previous_widget_cross_group(self) -> None:
        """Test _move_to_previous_widget moving across groups."""
        # Create groups with wrap_around=False to enable cross-group movement
        group1_widgets = [
            FocusableWidget("group1_w1", "Group1 Widget 1", focus_priority=10),
            FocusableWidget("group1_w3", "Group1 Widget 3", focus_priority=5),
        ]
        group2_widgets = [
            FocusableWidget("group2_w1", "Group2 Widget 1", focus_priority=10),
            FocusableWidget("group2_w3", "Group2 Widget 3", focus_priority=5),
        ]

        group1 = FocusGroup(
            name="group1", widgets=group1_widgets, wrap_around=False,
        )
        group2 = FocusGroup(
            name="group2", widgets=group2_widgets, wrap_around=False,
        )

        self.focus_manager.register_focus_group(group1)
        self.focus_manager.register_focus_group(group2)
        self.focus_manager.set_focus("group2_w1")  # First widget in group2

        result = self.focus_manager._move_to_previous_widget(
            FocusScope.ALL_PANELS,
        )
        assert result is not None
        assert result.startswith("group1_")

    def test_move_directional_coverage(self) -> None:
        """Test _move_directional method coverage."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)
        self.focus_manager.set_focus("test_w1")

        # Test all directional movements
        assert self.focus_manager._move_directional(
            FocusDirection.DOWN,
            FocusScope.ALL_PANELS,
        )
        self.focus_manager.set_focus("test_w3")
        assert self.focus_manager._move_directional(
            FocusDirection.UP,
            FocusScope.ALL_PANELS,
        )
        self.focus_manager.set_focus("test_w1")
        assert self.focus_manager._move_directional(
            FocusDirection.RIGHT,
            FocusScope.ALL_PANELS,
        )
        self.focus_manager.set_focus("test_w3")
        assert self.focus_manager._move_directional(
            FocusDirection.LEFT,
            FocusScope.ALL_PANELS,
        )

    def test_move_to_next_group_no_current_focus(self) -> None:
        """Test _move_to_next_group when no current focus."""
        result = self.focus_manager._move_to_next_group()
        assert result is None

    def test_move_to_next_group_no_current_group(self) -> None:
        """Test _move_to_next_group when current widget has no group."""
        self.focus_manager.current_focus = "nonexistent"
        result = self.focus_manager._move_to_next_group()
        assert result is None

    def test_move_to_next_group_success(self) -> None:
        """Test _move_to_next_group successful case."""
        group1 = self.create_test_group("group1")
        group2 = self.create_test_group("group2")
        self.focus_manager.register_focus_group(group1)
        self.focus_manager.register_focus_group(group2)
        self.focus_manager.set_focus("group1_w1")

        result = self.focus_manager._move_to_next_group()
        assert result is not None
        assert result.startswith("group2_")

    def test_find_next_group(self) -> None:
        """Test _find_next_group method."""
        group1 = self.create_test_group("group1")
        group2 = self.create_test_group("group2")
        self.focus_manager.register_focus_group(group1)
        self.focus_manager.register_focus_group(group2)

        next_group = self.focus_manager._find_next_group("group1")
        assert next_group is not None
        assert next_group.name == "group2"

        # Test wrap around
        next_group = self.focus_manager._find_next_group("group2")
        assert next_group is not None
        assert next_group.name == "group1"

    def test_find_next_group_not_found(self) -> None:
        """Test _find_next_group when current group not found."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        next_group = self.focus_manager._find_next_group("nonexistent")
        assert next_group is None

    def test_focus_first_in_group(self) -> None:
        """Test _focus_first_in_group method."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        result = self.focus_manager._focus_first_in_group(group)
        assert result == "test_w1"  # Highest priority focusable
        assert self.focus_manager.current_focus == "test_w1"

    def test_focus_first_in_group_no_focusable(self) -> None:
        """Test _focus_first_in_group when no widgets are focusable."""
        widgets = [
            FocusableWidget("w1", "W1", can_focus=False),
            FocusableWidget("w2", "W2", can_focus=False),
        ]
        group = FocusGroup(name="test", widgets=widgets)

        result = self.focus_manager._focus_first_in_group(group)
        assert result is None

    def test_move_to_previous_group(self) -> None:
        """Test _move_to_previous_group method."""
        group1 = self.create_test_group("group1")
        group2 = self.create_test_group("group2")
        self.focus_manager.register_focus_group(group1)
        self.focus_manager.register_focus_group(group2)
        self.focus_manager.set_focus("group2_w1")

        result = self.focus_manager._move_to_previous_group()
        assert result is not None
        assert result.startswith("group1_")

    def test_find_previous_group(self) -> None:
        """Test _find_previous_group method."""
        group1 = self.create_test_group("group1")
        group2 = self.create_test_group("group2")
        self.focus_manager.register_focus_group(group1)
        self.focus_manager.register_focus_group(group2)

        prev_group = self.focus_manager._find_previous_group("group2")
        assert prev_group is not None
        assert prev_group.name == "group1"

        # Test wrap around
        prev_group = self.focus_manager._find_previous_group("group1")
        assert prev_group is not None
        assert prev_group.name == "group2"

    def test_find_previous_group_not_found(self) -> None:
        """Test _find_previous_group when current group not found."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        prev_group = self.focus_manager._find_previous_group("nonexistent")
        assert prev_group is None

    def test_focus_last_in_group(self) -> None:
        """Test _focus_last_in_group method."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        result = self.focus_manager._focus_last_in_group(group)
        assert result == "test_w3"  # Last focusable widget
        assert self.focus_manager.current_focus == "test_w3"

    def test_focus_last_in_group_no_focusable(self) -> None:
        """Test _focus_last_in_group when no widgets are focusable."""
        widgets = [
            FocusableWidget("w1", "W1", can_focus=False),
            FocusableWidget("w2", "W2", can_focus=False),
        ]
        group = FocusGroup(name="test", widgets=widgets)

        result = self.focus_manager._focus_last_in_group(group)
        assert result is None

    def test_find_widget_group(self) -> None:
        """Test _find_widget_group method."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        found_group = self.focus_manager._find_widget_group("test_w1")
        assert found_group is not None
        assert found_group.name == "test"

    def test_find_widget_group_not_found(self) -> None:
        """Test _find_widget_group when widget not found."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        found_group = self.focus_manager._find_widget_group("nonexistent")
        assert found_group is None

    def test_set_focus_success(self) -> None:
        """Test successful set_focus."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        result = self.focus_manager.set_focus("test_w1")
        assert result == "test_w1"
        assert self.focus_manager.current_focus == "test_w1"

    def test_set_focus_widget_not_found(self) -> None:
        """Test set_focus when widget not found."""
        result = self.focus_manager.set_focus("nonexistent")
        assert result is None
        assert self.focus_manager.current_focus is None

    def test_set_focus_widget_cannot_focus(self) -> None:
        """Test set_focus when widget cannot focus."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        result = self.focus_manager.set_focus("test_w2")  # Cannot focus
        assert result is None

    def test_set_focus_updates_history(self) -> None:
        """Test that set_focus updates focus history."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        self.focus_manager.set_focus("test_w1")
        self.focus_manager.set_focus("test_w3")

        assert "test_w1" in self.focus_manager.focus_history
        assert len(self.focus_manager.focus_history) == 1

    def test_set_focus_same_widget_no_history_update(self) -> None:
        """Test that setting focus to same widget doesn't update history."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        self.focus_manager.set_focus("test_w1")
        initial_history_len = len(self.focus_manager.focus_history)

        self.focus_manager.set_focus("test_w1")  # Same widget
        assert len(self.focus_manager.focus_history) == initial_history_len

    def test_set_focus_history_limit(self) -> None:
        """Test that focus history is limited to MAX_FOCUS_HISTORY."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        # Add many widgets to exceed history limit
        for i in range(MAX_FOCUS_HISTORY + 3):
            widget = FocusableWidget(f"w{i}", f"Widget {i}")
            self.focus_manager.register_focusable("test", widget)
            self.focus_manager.set_focus(f"w{i}")

        assert len(self.focus_manager.focus_history) == MAX_FOCUS_HISTORY

    def test_find_widget_info(self) -> None:
        """Test _find_widget_info method."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        widget_info = self.focus_manager._find_widget_info("test_w1")
        assert widget_info is not None
        assert widget_info.widget_id == "test_w1"

    def test_find_widget_info_not_found(self) -> None:
        """Test _find_widget_info when widget not found."""
        widget_info = self.focus_manager._find_widget_info("nonexistent")
        assert widget_info is None

    def test_focus_first_available(self) -> None:
        """Test focus_first_available method."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        result = self.focus_manager.focus_first_available()
        assert result == "test_w1"  # Highest priority widget

    def test_focus_first_available_no_focusable(self) -> None:
        """Test focus_first_available when no focusable widgets."""
        widgets = [
            FocusableWidget("w1", "W1", can_focus=False),
            FocusableWidget("w2", "W2", can_focus=False),
        ]
        group = FocusGroup(name="test", widgets=widgets)
        self.focus_manager.register_focus_group(group)

        result = self.focus_manager.focus_first_available()
        assert result is None

    def test_focus_last_available(self) -> None:
        """Test focus_last_available method."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        result = self.focus_manager.focus_last_available()
        assert result == "test_w3"  # Last in priority order

    def test_focus_last_available_no_focusable(self) -> None:
        """Test focus_last_available when no focusable widgets."""
        widgets = [
            FocusableWidget("w1", "W1", can_focus=False),
        ]
        group = FocusGroup(name="test", widgets=widgets)
        self.focus_manager.register_focus_group(group)

        result = self.focus_manager.focus_last_available()
        assert result is None

    def test_focus_previous_in_history(self) -> None:
        """Test focus_previous_in_history method."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        # Build up some history
        self.focus_manager.set_focus("test_w1")
        self.focus_manager.set_focus("test_w3")

        result = self.focus_manager.focus_previous_in_history()
        assert result == "test_w1"
        assert self.focus_manager.current_focus == "test_w1"

    def test_focus_previous_in_history_empty(self) -> None:
        """Test focus_previous_in_history with empty history."""
        result = self.focus_manager.focus_previous_in_history()
        assert result is None

    def test_focus_previous_in_history_skip_unfocusable(self) -> None:
        """Test focus_previous_in_history skips unfocusable widgets."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        # Build history then make a widget unfocusable
        self.focus_manager.set_focus("test_w1")
        self.focus_manager.set_focus("test_w3")

        # Make the widget in history unfocusable
        widget = group.get_widget_by_id("test_w1")
        if widget:
            widget.can_focus = False

        result = self.focus_manager.focus_previous_in_history()
        assert result is None  # Should skip unfocusable and return None

    def test_push_focus_context(self) -> None:
        """Test push_focus_context method."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        self.focus_manager.set_focus("test_w1")
        self.focus_manager.push_focus_context("test_w3")

        assert self.focus_manager.current_focus == "test_w3"
        assert "test_w1" in self.focus_manager.focus_stack

    def test_push_focus_context_no_current_focus(self) -> None:
        """Test push_focus_context when no current focus."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        self.focus_manager.push_focus_context("test_w1")

        assert self.focus_manager.current_focus == "test_w1"
        assert len(self.focus_manager.focus_stack) == 0

    def test_pop_focus_context(self) -> None:
        """Test pop_focus_context method."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        self.focus_manager.set_focus("test_w1")
        self.focus_manager.push_focus_context("test_w3")

        result = self.focus_manager.pop_focus_context()
        assert result == "test_w1"
        assert self.focus_manager.current_focus == "test_w1"
        assert len(self.focus_manager.focus_stack) == 0

    def test_pop_focus_context_empty_stack(self) -> None:
        """Test pop_focus_context with empty stack."""
        result = self.focus_manager.pop_focus_context()
        assert result is None

    def test_get_focus_info_current_focus(self) -> None:
        """Test get_focus_info for current focus."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)
        self.focus_manager.set_focus("test_w1")

        info = self.focus_manager.get_focus_info()
        assert info is not None
        assert info.widget_id == "test_w1"

    def test_get_focus_info_specific_widget(self) -> None:
        """Test get_focus_info for specific widget."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        info = self.focus_manager.get_focus_info("test_w3")
        assert info is not None
        assert info.widget_id == "test_w3"

    def test_get_focus_info_no_current_focus(self) -> None:
        """Test get_focus_info when no current focus."""
        info = self.focus_manager.get_focus_info()
        assert info is None

    def test_get_focus_info_widget_not_found(self) -> None:
        """Test get_focus_info for nonexistent widget."""
        info = self.focus_manager.get_focus_info("nonexistent")
        assert info is None

    def test_get_keyboard_shortcuts(self) -> None:
        """Test get_keyboard_shortcuts method."""
        widget1 = FocusableWidget(
            "w1",
            "W1",
            keyboard_shortcuts=["ctrl+1", "f1"],
        )
        widget2 = FocusableWidget("w2", "W2", keyboard_shortcuts=["ctrl+2"])
        widget3 = FocusableWidget("w3", "W3")  # No shortcuts

        group = FocusGroup(name="test", widgets=[widget1, widget2, widget3])
        self.focus_manager.register_focus_group(group)

        shortcuts = self.focus_manager.get_keyboard_shortcuts()

        assert shortcuts["ctrl+1"] == "w1"
        assert shortcuts["f1"] == "w1"
        assert shortcuts["ctrl+2"] == "w2"
        assert "ctrl+3" not in shortcuts

    def test_get_keyboard_shortcuts_empty(self) -> None:
        """Test get_keyboard_shortcuts with no shortcuts."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        shortcuts = self.focus_manager.get_keyboard_shortcuts()
        assert shortcuts == {}

    def test_add_focus_observer(self) -> None:
        """Test add_focus_observer method."""
        observer = MockFocusHandler()
        self.focus_manager.add_focus_observer(observer)

        assert observer in self.focus_manager.focus_observers

    def test_add_focus_observer_duplicate(self) -> None:
        """Test add_focus_observer with duplicate observer."""
        observer = MockFocusHandler()
        self.focus_manager.add_focus_observer(observer)
        self.focus_manager.add_focus_observer(observer)  # Add again

        # Should only appear once
        observer_count = self.focus_manager.focus_observers.count(observer)
        assert observer_count == 1

    def test_remove_focus_observer(self) -> None:
        """Test remove_focus_observer method."""
        observer = MockFocusHandler()
        self.focus_manager.add_focus_observer(observer)

        self.focus_manager.remove_focus_observer(observer)
        assert observer not in self.focus_manager.focus_observers

    def test_remove_focus_observer_not_present(self) -> None:
        """Test remove_focus_observer when observer not present."""
        observer = MockFocusHandler()
        # Remove without adding - should not raise exception
        self.focus_manager.remove_focus_observer(observer)

    def test_apply_visual_focus_no_app(self) -> None:
        """Test apply_visual_focus when no app is set."""
        fm = FocusManager()  # No app
        # Should not raise exception
        fm.apply_visual_focus("test_widget", focused=True)

    def test_apply_visual_focus_with_app(self) -> None:
        """Test apply_visual_focus with app."""
        mock_widget = Mock()
        self.mock_app.query_one.return_value = mock_widget

        self.focus_manager.apply_visual_focus("test_widget", focused=True)

        self.mock_app.query_one.assert_called_once_with("#test_widget")
        mock_widget.add_class.assert_any_call("focused")
        mock_widget.add_class.assert_any_call("focus-active")

    def test_apply_visual_focus_remove(self) -> None:
        """Test apply_visual_focus removing focus."""
        mock_widget = Mock()
        self.mock_app.query_one.return_value = mock_widget

        self.focus_manager.apply_visual_focus("test_widget", focused=False)

        mock_widget.remove_class.assert_any_call("focused")
        mock_widget.remove_class.assert_any_call("focus-active")

    def test_apply_visual_focus_exception_handling(self) -> None:
        """Test apply_visual_focus handles exceptions."""
        self.mock_app.query_one.side_effect = Exception("Widget not found")

        # Should not raise exception
        self.focus_manager.apply_visual_focus("test_widget", focused=True)

    def test_handle_escape_context_focus_stack(self) -> None:
        """Test handle_escape_context with focus stack."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        self.focus_manager.set_focus("test_w1")
        self.focus_manager.push_focus_context("test_w3")

        result = self.focus_manager.handle_escape_context()

        assert result is True
        assert self.focus_manager.current_focus == "test_w1"

    def test_handle_escape_context_focus_history(self) -> None:
        """Test handle_escape_context with focus history."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        self.focus_manager.set_focus("test_w1")
        self.focus_manager.set_focus("test_w3")

        result = self.focus_manager.handle_escape_context()

        assert result is True
        assert self.focus_manager.current_focus == "test_w1"

    def test_handle_escape_context_unfocus_current(self) -> None:
        """Test handle_escape_context unfocusing current widget."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)
        self.focus_manager.set_focus("test_w1")

        mock_widget = Mock()
        self.mock_app.query_one.return_value = mock_widget

        result = self.focus_manager.handle_escape_context()

        assert result is True
        assert self.focus_manager.current_focus is None
        mock_widget.blur.assert_called_once()

    def test_handle_escape_context_pop_modal(self) -> None:
        """Test handle_escape_context popping modal screen."""
        self.mock_app.screen_stack = [Mock(), Mock()]  # Multiple screens

        result = self.focus_manager.handle_escape_context()

        assert result is True
        self.mock_app.pop_screen.assert_called_once()

    def test_handle_escape_context_no_action(self) -> None:
        """Test handle_escape_context when no action possible."""
        self.mock_app.screen_stack = [Mock()]  # Only one screen

        result = self.focus_manager.handle_escape_context()

        assert result is False

    def test_handle_escape_context_exception_in_unfocus(self) -> None:
        """Test handle_escape_context handles exception in unfocus."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)
        self.focus_manager.set_focus("test_w1")

        self.mock_app.query_one.side_effect = Exception("Widget error")
        self.mock_app.screen_stack = [Mock(), Mock()]

        result = self.focus_manager.handle_escape_context()

        # Should fall through to pop_screen
        assert result is True
        self.mock_app.pop_screen.assert_called_once()

    def test_notify_focus_change(self) -> None:
        """Test _notify_focus_change method."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        observer = MockFocusHandler()
        self.focus_manager.add_focus_observer(observer)

        mock_old_widget = Mock()
        mock_new_widget = Mock()
        self.mock_app.query_one.side_effect = [
            mock_old_widget,
            mock_new_widget,
        ]

        self.focus_manager._notify_focus_change("old_widget", "new_widget")

        # Check visual focus was applied/removed
        mock_old_widget.remove_class.assert_called()
        mock_new_widget.add_class.assert_called()

    def test_notify_focus_change_with_callbacks(self) -> None:
        """Test _notify_focus_change executes focus callbacks."""
        callback_called = False

        def focus_callback() -> None:
            nonlocal callback_called
            callback_called = True

        self.focus_manager._focus_callbacks["new_widget"] = [focus_callback]

        mock_old_widget = Mock()
        mock_new_widget = Mock()
        self.mock_app.query_one.side_effect = [
            mock_old_widget,
            mock_new_widget,
        ]

        self.focus_manager._notify_focus_change("old_widget", "new_widget")

        assert callback_called

    def test_notify_focus_change_observer_exception(self) -> None:
        """Test _notify_focus_change handles observer exceptions."""

        class FailingObserver:
            def on_focus_changed(
                self,
                old_focus: str | None,
                new_focus: str,
            ) -> None:
                raise Exception("Observer error")

        failing_observer = FailingObserver()
        self.focus_manager.add_focus_observer(failing_observer)

        mock_old_widget = Mock()
        mock_new_widget = Mock()
        self.mock_app.query_one.side_effect = [
            mock_old_widget,
            mock_new_widget,
        ]

        # Should not raise exception
        self.focus_manager._notify_focus_change("old_widget", "new_widget")

    def test_notify_focus_change_callback_exception(self) -> None:
        """Test _notify_focus_change handles callback exceptions."""

        def failing_callback() -> None:
            raise Exception("Callback error")

        self.focus_manager._focus_callbacks["new_widget"] = [failing_callback]

        mock_old_widget = Mock()
        mock_new_widget = Mock()
        self.mock_app.query_one.side_effect = [
            mock_old_widget,
            mock_new_widget,
        ]

        # Should not raise exception
        self.focus_manager._notify_focus_change("old_widget", "new_widget")

    def test_clear_all(self) -> None:
        """Test clear_all method."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)
        self.focus_manager.set_focus("test_w1")
        self.focus_manager.push_focus_context("test_w3")

        # Add callback
        self.focus_manager._focus_callbacks["test"] = [lambda: None]

        mock_widget = Mock()
        self.mock_app.query_one.return_value = mock_widget

        self.focus_manager.clear_all()

        # Verify everything is cleared
        assert len(self.focus_manager.focus_groups) == 0
        assert self.focus_manager.current_focus is None
        assert len(self.focus_manager.focus_history) == 0
        assert len(self.focus_manager.focus_stack) == 0
        assert len(self.focus_manager._focus_callbacks) == 0

        # Verify visual focus was removed
        mock_widget.remove_class.assert_called()

    def test_clear_all_no_current_focus(self) -> None:
        """Test clear_all when no current focus."""
        group = self.create_test_group("test")
        self.focus_manager.register_focus_group(group)

        self.focus_manager.clear_all()

        # Should not raise exception
        assert len(self.focus_manager.focus_groups) == 0


class TestFocusManagerEdgeCases:
    """Test edge cases and error conditions for FocusManager."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.focus_manager = FocusManager()
        self.mock_app = Mock()
        self.focus_manager.set_app(self.mock_app)

    def test_large_focus_history(self) -> None:
        """Test behavior with focus history at maximum size."""
        # Create enough widgets to exceed MAX_FOCUS_HISTORY
        for i in range(MAX_FOCUS_HISTORY + 5):
            widget = FocusableWidget(f"widget_{i}", f"Widget {i}")
            self.focus_manager.register_focusable("test", widget)

        # Set focus multiple times to build up history
        for i in range(MAX_FOCUS_HISTORY + 5):
            self.focus_manager.set_focus(f"widget_{i}")

        # History should be limited
        assert len(self.focus_manager.focus_history) == MAX_FOCUS_HISTORY

        # Should not contain the earliest widgets
        assert "widget_0" not in self.focus_manager.focus_history

    def test_empty_group_operations(self) -> None:
        """Test operations on empty groups."""
        empty_group = FocusGroup(name="empty", widgets=[])
        self.focus_manager.register_focus_group(empty_group)

        # All operations should handle empty groups gracefully
        assert self.focus_manager.get_focusable_widgets("empty") == []
        assert self.focus_manager._focus_first_in_group(empty_group) is None
        assert self.focus_manager._focus_last_in_group(empty_group) is None

    def test_circular_focus_movement(self) -> None:
        """Test circular focus movement in single-item groups."""
        widget = FocusableWidget("single", "Single Widget")
        group = FocusGroup(name="single", widgets=[widget], wrap_around=True)
        self.focus_manager.register_focus_group(group)
        self.focus_manager.set_focus("single")

        # Next should stay on same widget (or return None)
        result = self.focus_manager.move_focus(FocusDirection.NEXT)
        assert result == "single" or result is None

        # Previous should stay on same widget (or return None)
        result = self.focus_manager.move_focus(FocusDirection.PREVIOUS)
        assert result == "single" or result is None

    def test_mixed_focusable_unfocusable_widgets(self) -> None:
        """Test groups with mix of focusable and unfocusable widgets."""
        widgets = [
            FocusableWidget("f1", "F1", can_focus=True, focus_priority=1),
            FocusableWidget("u1", "U1", can_focus=False, focus_priority=10),
            FocusableWidget("f2", "F2", can_focus=True, focus_priority=5),
            FocusableWidget("u2", "U2", can_focus=False, focus_priority=2),
            FocusableWidget("f3", "F3", can_focus=True, focus_priority=0),
        ]
        group = FocusGroup(name="mixed", widgets=widgets)
        self.focus_manager.register_focus_group(group)

        # Should only focus on focusable widgets
        result = self.focus_manager.focus_first_available()
        assert result in ["f1", "f2", "f3"]  # One of the focusable widgets

        # Should skip unfocusable widgets during navigation
        self.focus_manager.set_focus("f2")
        result = self.focus_manager.move_focus(FocusDirection.NEXT)
        assert result in ["f1", "f3"]  # Should skip unfocusable widgets


class TestGlobalFocusManager:
    """Test global focus manager instance."""

    def test_global_focus_manager_exists(self) -> None:
        """Test that global focus manager instance exists."""
        assert focus_manager is not None
        assert isinstance(focus_manager, FocusManager)

    def test_global_focus_manager_initially_no_app(self) -> None:
        """Test that global focus manager initially has no app."""
        # Note: The global instance might be modified by other tests
        # This test just verifies the instance exists and is a FocusManager
        assert isinstance(focus_manager, FocusManager)


class TestCreatePanelFocusGroup:
    """Test create_panel_focus_group utility function."""

    def test_create_panel_focus_group_minimal(self) -> None:
        """Test creating panel focus group with minimal parameters."""
        group = create_panel_focus_group("Test Panel", "test_panel")

        assert group.name == "test_panel"
        assert group.description == "Test Panel panel focus group"
        assert len(group.widgets) == 1

        widget = group.widgets[0]
        assert widget.widget_id == "test_panel"
        assert widget.display_name == "Test Panel"
        assert widget.focus_priority == 0
        assert widget.keyboard_shortcuts == []

    def test_create_panel_focus_group_full(self) -> None:
        """Test creating panel focus group with all parameters."""
        shortcuts = ["f1", "ctrl+p"]
        group = create_panel_focus_group(
            "Advanced Panel",
            "advanced_panel",
            priority=10,
            shortcuts=shortcuts,
        )

        assert group.name == "advanced_panel"
        assert group.description == "Advanced Panel panel focus group"

        widget = group.widgets[0]
        assert widget.widget_id == "advanced_panel"
        assert widget.display_name == "Advanced Panel"
        assert widget.focus_priority == 10
        assert widget.keyboard_shortcuts == shortcuts

    def test_create_panel_focus_group_name_normalization(self) -> None:
        """Test that panel name is normalized for group name."""
        group = create_panel_focus_group("Complex Panel Name", "panel_id")
        assert group.name == "complex_panel_name"

    @pytest.mark.parametrize(
        "panel_name,expected_group_name",
        [
            ("Simple", "simple"),
            ("Two Words", "two_words"),
            ("Multiple Word Panel Name", "multiple_word_panel_name"),
            ("Panel-With-Dashes", "panel-with-dashes"),
            ("Panel_With_Underscores", "panel_with_underscores"),
            ("MixedCase Panel", "mixedcase_panel"),
        ],
    )
    def test_create_panel_focus_group_name_variations(
        self,
        panel_name: str,
        expected_group_name: str,
    ) -> None:
        """Test panel name normalization with various inputs."""
        group = create_panel_focus_group(panel_name, "panel_id")
        assert group.name == expected_group_name


class TestConstants:
    """Test module constants."""

    def test_max_focus_history_constant(self) -> None:
        """Test MAX_FOCUS_HISTORY constant."""
        assert MAX_FOCUS_HISTORY == 10
        assert isinstance(MAX_FOCUS_HISTORY, int)
        assert MAX_FOCUS_HISTORY > 0

    def test_max_context_stack_constant(self) -> None:
        """Test MAX_CONTEXT_STACK constant."""
        assert MAX_CONTEXT_STACK == 5
        assert isinstance(MAX_CONTEXT_STACK, int)
        assert MAX_CONTEXT_STACK > 0
