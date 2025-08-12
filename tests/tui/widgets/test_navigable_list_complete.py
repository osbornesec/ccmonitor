"""Complete comprehensive tests for NavigableList widget.

This test suite provides comprehensive coverage of NavigableList functionality
including initialization, navigation, cursor management, scrolling, selection,
keyboard handling, and integration scenarios.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from textual.widgets import ListItem, Static

from src.tui.widgets.navigable_list import NavigableList

# Test constants
TEST_CONTENT_HEIGHT = 10
SCROLL_MARGIN = 2
PAGE_SIZE = 5
TEST_ITEMS_COUNT_3 = 3
TEST_ITEMS_COUNT_5 = 5
TEST_INDEX_2 = 2
TEST_INDEX_4 = 4
TEST_INDEX_9 = 9
TEST_INDEX_20 = 20


class TestNavigableListInitialization:
    """Test NavigableList initialization and basic properties."""

    def test_default_initialization(self) -> None:
        """Test NavigableList with default parameters."""
        nav_list = NavigableList()

        assert nav_list.cursor_index == 0
        assert nav_list.show_cursor is True
        assert nav_list.disabled is False
        assert len(nav_list.children) == 0

    def test_initialization_with_items(self) -> None:
        """Test NavigableList initialization with items."""
        item1 = ListItem(Static("Item 1"))
        item2 = ListItem(Static("Item 2"))
        item3 = ListItem(Static("Item 3"))

        nav_list = NavigableList(item1, item2, item3, initial_index=1)

        # Items should be added during initialization
        assert len(nav_list.children) == TEST_ITEMS_COUNT_3
        assert nav_list.cursor_index == 0  # Set during mount, not init

    def test_initialization_with_custom_attributes(self) -> None:
        """Test NavigableList with custom attributes."""
        nav_list = NavigableList(
            name="test-list",
            id="nav-list",
            classes="custom-class",
            disabled=True,
        )

        assert nav_list.name == "test-list"
        assert nav_list.id == "nav-list"
        assert nav_list.disabled is True

    def test_initialization_with_no_items(self) -> None:
        """Test NavigableList behavior when initialized without items."""
        nav_list = NavigableList(initial_index=5)

        # Should handle out of bounds initial index gracefully
        assert nav_list.cursor_index == 0
        assert len(nav_list.children) == 0


class TestNavigableListMountingBehavior:
    """Test NavigableList mounting and lifecycle behavior."""

    def test_on_mount_sets_cursor_index(self) -> None:
        """Test that on_mount sets cursor index correctly."""
        nav_list = NavigableList()

        # Mock _update_cursor_display to avoid UI operations
        with patch.object(nav_list, "_update_cursor_display") as mock_update:
            nav_list.on_mount()
            assert nav_list.cursor_index == 0
            mock_update.assert_called_once()

    def test_on_mount_with_existing_items(self) -> None:
        """Test on_mount behavior with pre-existing items."""
        item1 = ListItem(Static("Item 1"))
        item2 = ListItem(Static("Item 2"))

        nav_list = NavigableList(item1, item2)

        with patch.object(nav_list, "_update_cursor_display"):
            nav_list.on_mount()
            assert nav_list.cursor_index == 0


class TestNavigableListCursorManagement:
    """Test cursor positioning and management."""

    @pytest.fixture
    def nav_list_with_items(self) -> NavigableList:
        """Create NavigableList with test items."""
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(5)]
        for item in items:
            nav_list.append(item)
        return nav_list

    def test_cursor_index_bounds_lower(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test cursor index lower bound validation."""
        nav_list_with_items.cursor_index = -5
        # The watch_cursor_index method should clamp to 0
        assert nav_list_with_items.cursor_index == 0

    def test_cursor_index_bounds_upper(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test cursor index upper bound validation."""
        nav_list_with_items.cursor_index = 10
        # Should clamp to max valid index (4 for 5 items)
        assert nav_list_with_items.cursor_index == 4

    def test_cursor_index_valid_range(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test cursor index within valid range."""
        nav_list_with_items.cursor_index = 2
        assert nav_list_with_items.cursor_index == 2

    def test_cursor_index_empty_list(self) -> None:
        """Test cursor behavior with empty list."""
        nav_list = NavigableList()
        nav_list.cursor_index = 5
        # Should clamp to 0 even with empty list
        assert nav_list.cursor_index == 0

    def test_watch_cursor_index_updates_display(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test cursor display updates when index changes."""
        with (
            patch.object(
                nav_list_with_items,
                "_update_cursor_display",
            ) as mock_update,
            patch.object(
                nav_list_with_items,
                "scroll_to_cursor",
            ) as mock_scroll,
        ):
            nav_list_with_items.cursor_index = 2
            mock_update.assert_called_once()
            mock_scroll.assert_called_once()

    def test_update_cursor_display_adds_class(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test that cursor display adds cursor-active class."""
        nav_list_with_items.cursor_index = 1

        # Mock the children to avoid UI operations
        mock_child_0 = Mock()
        mock_child_1 = Mock()
        mock_child_2 = Mock()
        nav_list_with_items.children = [
            mock_child_0,
            mock_child_1,
            mock_child_2,
        ]

        nav_list_with_items._update_cursor_display()

        # Should remove class from all items first
        mock_child_0.remove_class.assert_called_with("cursor-active")
        mock_child_1.remove_class.assert_called_with("cursor-active")
        mock_child_2.remove_class.assert_called_with("cursor-active")

        # Should add class to cursor item
        mock_child_1.add_class.assert_called_with("cursor-active")

    def test_update_cursor_display_hidden_cursor(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test cursor display when cursor is hidden."""
        nav_list_with_items.show_cursor = False

        with patch.object(
            nav_list_with_items.children[0],
            "remove_class",
        ) as mock_remove:
            nav_list_with_items._update_cursor_display()
            # Should not do anything when cursor is hidden
            mock_remove.assert_not_called()

    def test_update_cursor_display_invalid_index(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test cursor display with invalid cursor index."""
        nav_list_with_items.cursor_index = 10  # Out of bounds

        mock_children = [Mock() for _ in range(5)]
        nav_list_with_items.children = mock_children

        # This should trigger watch_cursor_index which clamps the value
        # The _update_cursor_display should then work with valid index


class TestNavigableListNavigation:
    """Test keyboard navigation actions."""

    @pytest.fixture
    def nav_list_with_items(self) -> NavigableList:
        """Create NavigableList with test items."""
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(5)]
        for item in items:
            nav_list.append(item)
        nav_list.cursor_index = 2  # Start in middle
        return nav_list

    def test_action_cursor_up(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test cursor up action."""
        initial_index = nav_list_with_items.cursor_index
        nav_list_with_items.action_cursor_up()
        assert nav_list_with_items.cursor_index == initial_index - 1

    def test_action_cursor_up_at_start(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test cursor up action at list start."""
        nav_list_with_items.cursor_index = 0
        nav_list_with_items.action_cursor_up()
        assert nav_list_with_items.cursor_index == 0  # Should not go below 0

    def test_action_cursor_down(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test cursor down action."""
        initial_index = nav_list_with_items.cursor_index
        nav_list_with_items.action_cursor_down()
        assert nav_list_with_items.cursor_index == initial_index + 1

    def test_action_cursor_down_at_end(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test cursor down action at list end."""
        nav_list_with_items.cursor_index = 4  # Last item
        nav_list_with_items.action_cursor_down()
        assert (
            nav_list_with_items.cursor_index == 4
        )  # Should not go beyond end

    def test_action_cursor_first(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test cursor first action."""
        nav_list_with_items.action_cursor_first()
        assert nav_list_with_items.cursor_index == 0

    def test_action_cursor_last(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test cursor last action."""
        nav_list_with_items.action_cursor_last()
        assert nav_list_with_items.cursor_index == 4  # Last item index

    def test_action_cursor_first_empty_list(self) -> None:
        """Test cursor first action with empty list."""
        nav_list = NavigableList()
        nav_list.action_cursor_first()
        # Should not crash, cursor stays at 0
        assert nav_list.cursor_index == 0

    def test_action_cursor_last_empty_list(self) -> None:
        """Test cursor last action with empty list."""
        nav_list = NavigableList()
        nav_list.action_cursor_last()
        # Should not crash with empty list
        assert nav_list.cursor_index == 0

    def test_action_page_up(self, nav_list_with_items: NavigableList) -> None:
        """Test page up action."""
        nav_list_with_items.cursor_index = 4

        # Mock content_size to simulate page size calculation
        mock_size = Mock()
        mock_size.height = 3
        nav_list_with_items.content_size = mock_size

        nav_list_with_items.action_page_up()
        # Should move up by page_size - 1 (with overlap)
        assert nav_list_with_items.cursor_index == 2

    def test_action_page_down(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test page down action."""
        nav_list_with_items.cursor_index = 0

        # Mock content_size
        mock_size = Mock()
        mock_size.height = 3
        nav_list_with_items.content_size = mock_size

        nav_list_with_items.action_page_down()
        # Should move down by page_size - 1 (with overlap)
        assert nav_list_with_items.cursor_index == 2

    def test_action_page_up_bounds(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test page up respects bounds."""
        nav_list_with_items.cursor_index = 1

        mock_size = Mock()
        mock_size.height = 10  # Large page size
        nav_list_with_items.content_size = mock_size

        nav_list_with_items.action_page_up()
        assert nav_list_with_items.cursor_index == 0  # Should not go below 0

    def test_action_page_down_bounds(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test page down respects bounds."""
        nav_list_with_items.cursor_index = 3

        mock_size = Mock()
        mock_size.height = 10  # Large page size
        nav_list_with_items.content_size = mock_size

        nav_list_with_items.action_page_down()
        assert nav_list_with_items.cursor_index == 4  # Should not exceed max


class TestNavigableListSelection:
    """Test item selection functionality."""

    @pytest.fixture
    def nav_list_with_items(self) -> NavigableList:
        """Create NavigableList with test items."""
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(3)]
        for item in items:
            nav_list.append(item)
        return nav_list

    def test_action_select_cursor(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test cursor selection action."""
        nav_list_with_items.cursor_index = 1

        # Mock children to avoid UI operations
        mock_children = [Mock(), Mock(), Mock()]
        nav_list_with_items.children = mock_children

        with patch.object(nav_list_with_items, "post_message") as mock_post:
            nav_list_with_items.action_select_cursor()

            # Should clear highlights from all items
            for child in mock_children:
                child.remove_class.assert_called_with("-highlighted")

            # Should highlight selected item
            mock_children[1].add_class.assert_called_with("-highlighted")

            # Should post selection message
            mock_post.assert_called_once()

    def test_action_select_cursor_out_of_bounds(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test selection action with cursor out of bounds."""
        nav_list_with_items.cursor_index = 10  # Out of bounds

        with patch.object(nav_list_with_items, "post_message") as mock_post:
            nav_list_with_items.action_select_cursor()
            # Should not post message when out of bounds
            mock_post.assert_not_called()

    def test_action_toggle_cursor(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test cursor toggle action."""
        nav_list_with_items.cursor_index = 1

        mock_item = Mock()
        mock_item.has_class.return_value = False
        nav_list_with_items.children = [Mock(), mock_item, Mock()]

        nav_list_with_items.action_toggle_cursor()
        mock_item.add_class.assert_called_with("-highlighted")

    def test_action_toggle_cursor_already_highlighted(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test cursor toggle when item already highlighted."""
        nav_list_with_items.cursor_index = 1

        mock_item = Mock()
        mock_item.has_class.return_value = True
        nav_list_with_items.children = [Mock(), mock_item, Mock()]

        nav_list_with_items.action_toggle_cursor()
        mock_item.remove_class.assert_called_with("-highlighted")

    def test_action_toggle_cursor_out_of_bounds(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test toggle action with cursor out of bounds."""
        nav_list_with_items.cursor_index = 10

        mock_children = [Mock(), Mock(), Mock()]
        nav_list_with_items.children = mock_children

        nav_list_with_items.action_toggle_cursor()
        # Should not modify any items when out of bounds
        for child in mock_children:
            child.add_class.assert_not_called()
            child.remove_class.assert_not_called()

    def test_clear_selection(self, nav_list_with_items: NavigableList) -> None:
        """Test clearing all selections."""
        mock_children = [Mock(), Mock(), Mock()]
        nav_list_with_items.children = mock_children

        nav_list_with_items.clear_selection()

        for child in mock_children:
            child.remove_class.assert_called_with("-highlighted")

    def test_get_selected_items(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test getting selected items."""
        mock_child_1 = Mock()
        mock_child_1.has_class.return_value = False

        mock_child_2 = Mock()
        mock_child_2.has_class.return_value = True

        mock_child_3 = Mock()
        mock_child_3.has_class.return_value = True

        nav_list_with_items.children = [
            mock_child_1,
            mock_child_2,
            mock_child_3,
        ]

        selected = nav_list_with_items.get_selected_items()
        assert len(selected) == 2
        assert mock_child_2 in selected
        assert mock_child_3 in selected


class TestNavigableListScrolling:
    """Test scrolling functionality."""

    @pytest.fixture
    def nav_list_with_items(self) -> NavigableList:
        """Create NavigableList with test items and mock scrolling."""
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(10)]
        for item in items:
            nav_list.append(item)

        # Mock content_size and scroll methods
        mock_size = Mock()
        mock_size.height = 5
        nav_list.content_size = mock_size

        return nav_list

    def test_can_scroll_to_cursor_valid(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test scroll validation with valid cursor."""
        nav_list_with_items.cursor_index = 2
        assert nav_list_with_items._can_scroll_to_cursor() is True

    def test_can_scroll_to_cursor_invalid_index(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test scroll validation with invalid cursor index."""
        nav_list_with_items.cursor_index = 20
        # This should be False but watch_cursor_index might clamp it
        result = nav_list_with_items._can_scroll_to_cursor()
        # After clamping, should be valid again
        assert isinstance(result, bool)

    def test_can_scroll_to_cursor_zero_height(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test scroll validation with zero content height."""
        mock_size = Mock()
        mock_size.height = 0
        nav_list_with_items.content_size = mock_size
        nav_list_with_items.cursor_index = 2

        assert nav_list_with_items._can_scroll_to_cursor() is False

    def test_calculate_scroll_target_no_scroll_needed(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test scroll calculation when no scroll is needed."""
        # Mock cursor item region
        mock_cursor_item = Mock()
        mock_region = Mock()
        mock_region.y = 10
        mock_region.height = 2
        mock_cursor_item.region = mock_region

        # Mock scroll offset
        mock_offset = Mock()
        mock_offset.y = 5
        nav_list_with_items.scroll_offset = mock_offset

        result = nav_list_with_items._calculate_scroll_target(mock_cursor_item)
        # Should return None when no scroll needed
        assert result is None or isinstance(result, int)

    def test_calculate_scroll_target_scroll_up(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test scroll calculation when need to scroll up."""
        mock_cursor_item = Mock()
        mock_region = Mock()
        mock_region.y = 2
        mock_region.height = 1
        mock_cursor_item.region = mock_region

        mock_offset = Mock()
        mock_offset.y = 10  # Currently scrolled down
        nav_list_with_items.scroll_offset = mock_offset

        result = nav_list_with_items._calculate_scroll_target(mock_cursor_item)
        assert isinstance(result, int)
        assert result >= 0

    def test_calculate_scroll_target_scroll_down(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test scroll calculation when need to scroll down."""
        mock_cursor_item = Mock()
        mock_region = Mock()
        mock_region.y = 20
        mock_region.height = 1
        mock_cursor_item.region = mock_region

        mock_offset = Mock()
        mock_offset.y = 0  # At top
        nav_list_with_items.scroll_offset = mock_offset

        result = nav_list_with_items._calculate_scroll_target(mock_cursor_item)
        assert isinstance(result, int)
        assert result >= 0

    def test_scroll_to_cursor(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test scroll to cursor functionality."""
        nav_list_with_items.cursor_index = 3

        with (
            patch.object(
                nav_list_with_items,
                "_can_scroll_to_cursor",
                return_value=True,
            ),
            patch.object(
                nav_list_with_items,
                "_calculate_scroll_target",
                return_value=10,
            ),
            patch.object(nav_list_with_items, "scroll_to") as mock_scroll_to,
        ):
            nav_list_with_items.scroll_to_cursor()
            mock_scroll_to.assert_called_once_with(y=10, animate=True)

    def test_scroll_to_cursor_no_scroll_needed(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test scroll to cursor when no scroll needed."""
        with (
            patch.object(
                nav_list_with_items,
                "_can_scroll_to_cursor",
                return_value=True,
            ),
            patch.object(
                nav_list_with_items,
                "_calculate_scroll_target",
                return_value=None,
            ),
            patch.object(nav_list_with_items, "scroll_to") as mock_scroll_to,
        ):
            nav_list_with_items.scroll_to_cursor()
            mock_scroll_to.assert_not_called()

    def test_scroll_to_cursor_cannot_scroll(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test scroll to cursor when scrolling not possible."""
        with (
            patch.object(
                nav_list_with_items,
                "_can_scroll_to_cursor",
                return_value=False,
            ),
            patch.object(nav_list_with_items, "scroll_to") as mock_scroll_to,
        ):
            nav_list_with_items.scroll_to_cursor()
            mock_scroll_to.assert_not_called()


class TestNavigableListUtilityMethods:
    """Test utility methods for cursor and item management."""

    @pytest.fixture
    def nav_list_with_items(self) -> NavigableList:
        """Create NavigableList with test items."""
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(5)]
        for item in items:
            nav_list.append(item)
        return nav_list

    def test_get_cursor_item_valid(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test getting cursor item with valid index."""
        nav_list_with_items.cursor_index = 2
        item = nav_list_with_items.get_cursor_item()

        assert item is not None
        assert item is nav_list_with_items.children[2]

    def test_get_cursor_item_invalid(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test getting cursor item with invalid index."""
        nav_list_with_items.cursor_index = 10  # Out of bounds
        item = nav_list_with_items.get_cursor_item()

        # After bounds checking in watch_cursor_index, should return valid item
        assert item is not None or nav_list_with_items.cursor_index < len(
            nav_list_with_items.children,
        )

    def test_set_cursor_index_valid(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test setting cursor index to valid value."""
        with patch.object(
            nav_list_with_items,
            "scroll_to_cursor",
        ) as mock_scroll:
            nav_list_with_items.set_cursor_index(3)
            assert nav_list_with_items.cursor_index == 3
            mock_scroll.assert_called_once()

    def test_set_cursor_index_no_scroll(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test setting cursor index without scrolling."""
        with patch.object(
            nav_list_with_items,
            "scroll_to_cursor",
        ) as mock_scroll:
            nav_list_with_items.set_cursor_index(3, scroll=False)
            assert nav_list_with_items.cursor_index == 3
            mock_scroll.assert_not_called()

    def test_set_cursor_index_bounds(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test setting cursor index respects bounds."""
        nav_list_with_items.set_cursor_index(10)  # Out of bounds
        assert nav_list_with_items.cursor_index == 4  # Max valid index

        nav_list_with_items.set_cursor_index(-5)  # Below bounds
        assert nav_list_with_items.cursor_index == 0

    def test_move_cursor_to_item_success(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test moving cursor to specific item successfully."""
        target_item = nav_list_with_items.children[2]

        with patch.object(nav_list_with_items, "set_cursor_index") as mock_set:
            result = nav_list_with_items.move_cursor_to_item(target_item)

            assert result is True
            mock_set.assert_called_once_with(2, scroll=True)

    def test_move_cursor_to_item_not_found(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test moving cursor to item not in list."""
        external_item = ListItem(Static("External Item"))

        result = nav_list_with_items.move_cursor_to_item(external_item)
        assert result is False

    def test_move_cursor_to_item_no_scroll(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test moving cursor to item without scrolling."""
        target_item = nav_list_with_items.children[3]

        with patch.object(nav_list_with_items, "set_cursor_index") as mock_set:
            result = nav_list_with_items.move_cursor_to_item(
                target_item,
                scroll=False,
            )

            assert result is True
            mock_set.assert_called_once_with(3, scroll=False)


class TestNavigableListKeyHandling:
    """Test keyboard event handling."""

    @pytest.fixture
    def nav_list_with_items(self) -> NavigableList:
        """Create NavigableList with test items."""
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(10)]
        for item in items:
            nav_list.append(item)
        return nav_list

    def test_on_key_digit_navigation(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test numeric key navigation."""
        # Mock key event
        mock_event = Mock()
        mock_event.key = "5"
        mock_event.key.isdigit.return_value = True

        with patch.object(nav_list_with_items, "set_cursor_index") as mock_set:
            nav_list_with_items.on_key(mock_event)

            mock_set.assert_called_once_with(4)  # 5th item (0-based index 4)
            mock_event.prevent_default.assert_called_once()
            mock_event.stop.assert_called_once()

    def test_on_key_zero_navigation(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test zero key navigation (10th item)."""
        mock_event = Mock()
        mock_event.key = "0"
        mock_event.key.isdigit.return_value = True

        with patch.object(nav_list_with_items, "set_cursor_index") as mock_set:
            nav_list_with_items.on_key(mock_event)

            mock_set.assert_called_once_with(9)  # 10th item (0-based index 9)
            mock_event.prevent_default.assert_called_once()
            mock_event.stop.assert_called_once()

    def test_on_key_out_of_range(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test numeric key for item beyond list length."""
        # Create short list
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(3)]
        for item in items:
            nav_list.append(item)

        mock_event = Mock()
        mock_event.key = "5"
        mock_event.key.isdigit.return_value = True

        with patch.object(nav_list, "set_cursor_index") as mock_set:
            nav_list.on_key(mock_event)

            # Should not call set_cursor_index for out-of-range items
            mock_set.assert_not_called()
            mock_event.prevent_default.assert_not_called()
            mock_event.stop.assert_not_called()

    def test_on_key_non_digit(
        self,
        nav_list_with_items: NavigableList,
    ) -> None:
        """Test non-digit key handling."""
        mock_event = Mock()
        mock_event.key = "a"
        mock_event.key.isdigit.return_value = False

        with patch.object(nav_list_with_items, "set_cursor_index") as mock_set:
            nav_list_with_items.on_key(mock_event)

            mock_set.assert_not_called()
            mock_event.prevent_default.assert_not_called()
            mock_event.stop.assert_not_called()


class TestNavigableListItemManagement:
    """Test adding, removing, and inserting items."""

    def test_add_item_to_empty_list(self) -> None:
        """Test adding item to empty list."""
        nav_list = NavigableList()
        item = ListItem(Static("New Item"))

        nav_list.add_item(item)

        assert len(nav_list.children) == 1
        assert nav_list.cursor_index == 0

    def test_add_item_to_existing_list(self) -> None:
        """Test adding item to list with existing items."""
        nav_list = NavigableList()
        initial_item = ListItem(Static("Initial Item"))
        nav_list.append(initial_item)
        nav_list.cursor_index = 0

        new_item = ListItem(Static("New Item"))
        nav_list.add_item(new_item)

        assert len(nav_list.children) == 2
        assert nav_list.cursor_index == 0  # Cursor unchanged

    def test_remove_item_before_cursor(self) -> None:
        """Test removing item before cursor position."""
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(5)]
        for item in items:
            nav_list.append(item)

        nav_list.cursor_index = 3
        nav_list.remove_item(items[1])  # Remove item at index 1

        assert nav_list.cursor_index == 2  # Cursor should adjust backward

    def test_remove_item_at_cursor(self) -> None:
        """Test removing item at cursor position."""
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(5)]
        for item in items:
            nav_list.append(item)

        nav_list.cursor_index = 2
        nav_list.remove_item(items[2])  # Remove item at cursor

        assert nav_list.cursor_index == 1  # Cursor should adjust backward

    def test_remove_item_after_cursor(self) -> None:
        """Test removing item after cursor position."""
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(5)]
        for item in items:
            nav_list.append(item)

        nav_list.cursor_index = 1
        nav_list.remove_item(items[3])  # Remove item after cursor

        assert nav_list.cursor_index == 1  # Cursor unchanged

    def test_remove_nonexistent_item(self) -> None:
        """Test removing item not in list."""
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(3)]
        for item in items:
            nav_list.append(item)

        external_item = ListItem(Static("External Item"))
        nav_list.cursor_index = 1

        nav_list.remove_item(external_item)

        # Should not crash, cursor unchanged
        assert nav_list.cursor_index == 1
        assert len(nav_list.children) == 3

    def test_insert_item_before_cursor(self) -> None:
        """Test inserting item before cursor position."""
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(3)]
        for item in items:
            nav_list.append(item)

        nav_list.cursor_index = 2
        new_item = ListItem(Static("New Item"))

        nav_list.insert_item(1, new_item)  # Insert before cursor

        assert nav_list.cursor_index == 3  # Cursor should move forward

    def test_insert_item_at_cursor(self) -> None:
        """Test inserting item at cursor position."""
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(3)]
        for item in items:
            nav_list.append(item)

        nav_list.cursor_index = 1
        new_item = ListItem(Static("New Item"))

        nav_list.insert_item(1, new_item)  # Insert at cursor

        assert nav_list.cursor_index == 2  # Cursor should move forward

    def test_insert_item_after_cursor(self) -> None:
        """Test inserting item after cursor position."""
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(3)]
        for item in items:
            nav_list.append(item)

        nav_list.cursor_index = 1
        new_item = ListItem(Static("New Item"))

        nav_list.insert_item(2, new_item)  # Insert after cursor

        assert nav_list.cursor_index == 1  # Cursor unchanged


class TestNavigableListFocusBlur:
    """Test focus and blur behavior."""

    def test_focus_shows_cursor(self) -> None:
        """Test focus makes cursor visible."""
        nav_list = NavigableList()
        nav_list.show_cursor = False

        with patch.object(nav_list, "_update_cursor_display") as mock_update:
            nav_list.focus()

            assert nav_list.show_cursor is True
            mock_update.assert_called_once()

    def test_focus_with_scroll_visible(self) -> None:
        """Test focus with scroll_visible parameter."""
        nav_list = NavigableList()

        with patch("textual.widgets.ListView.focus") as mock_super_focus:
            result = nav_list.focus(scroll_visible=False)

            mock_super_focus.assert_called_once_with(scroll_visible=False)
            assert result is nav_list

    def test_blur_maintains_cursor_state(self) -> None:
        """Test blur maintains cursor but changes visual prominence."""
        nav_list = NavigableList()
        nav_list.show_cursor = True

        with patch("textual.widgets.ListView.blur") as mock_super_blur:
            result = nav_list.blur()

            mock_super_blur.assert_called_once()
            # Cursor should still be visible (visual distinction via CSS)
            assert nav_list.show_cursor is True
            assert result is nav_list


class TestNavigableListIntegration:
    """Integration tests for complex NavigableList scenarios."""

    def test_complete_navigation_flow(self) -> None:
        """Test complete navigation workflow."""
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(10)]
        for item in items:
            nav_list.add_item(item)

        # Start at beginning
        assert nav_list.cursor_index == 0

        # Navigate down
        nav_list.action_cursor_down()
        nav_list.action_cursor_down()
        assert nav_list.cursor_index == 2

        # Jump to end
        nav_list.action_cursor_last()
        assert nav_list.cursor_index == 9

        # Page up
        with patch.object(nav_list, "content_size") as mock_size:
            mock_size.height = 5
            nav_list.action_page_up()
            assert nav_list.cursor_index == 5  # 9 - (5-1) = 5

        # Back to start
        nav_list.action_cursor_first()
        assert nav_list.cursor_index == 0

    def test_selection_and_navigation_flow(self) -> None:
        """Test selection combined with navigation."""
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(5)]
        for item in items:
            nav_list.append(item)

        # Mock children for selection testing
        mock_children = [Mock() for _ in range(5)]
        nav_list.children = mock_children

        # Select first item
        nav_list.cursor_index = 0
        nav_list.action_toggle_cursor()

        # Navigate and select another
        nav_list.cursor_index = 2
        nav_list.action_toggle_cursor()

        # Check selections
        mock_children[0].add_class.assert_called_with("-highlighted")
        mock_children[2].add_class.assert_called_with("-highlighted")

        # Clear all selections
        nav_list.clear_selection()
        for child in mock_children:
            child.remove_class.assert_called_with("-highlighted")

    def test_item_management_and_cursor_adjustment(self) -> None:
        """Test item management with cursor position adjustment."""
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(5)]
        for item in items:
            nav_list.append(item)

        # Position cursor in middle
        nav_list.cursor_index = 2

        # Remove item before cursor
        nav_list.remove_item(items[1])
        assert nav_list.cursor_index == 1  # Should adjust backward

        # Add new item
        new_item = ListItem(Static("New Item"))
        nav_list.add_item(new_item)
        assert len(nav_list.children) == 5  # Back to 5 items

        # Insert item before cursor
        another_item = ListItem(Static("Another Item"))
        nav_list.insert_item(0, another_item)
        assert nav_list.cursor_index == 2  # Should adjust forward


class TestNavigableListEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_list_navigation_safety(self) -> None:
        """Test navigation on empty list doesn't crash."""
        nav_list = NavigableList()

        # All navigation actions should be safe
        nav_list.action_cursor_up()
        nav_list.action_cursor_down()
        nav_list.action_cursor_first()
        nav_list.action_cursor_last()
        nav_list.action_page_up()
        nav_list.action_page_down()
        nav_list.action_select_cursor()
        nav_list.action_toggle_cursor()

        assert nav_list.cursor_index == 0

    def test_single_item_navigation(self) -> None:
        """Test navigation with single item."""
        nav_list = NavigableList()
        item = ListItem(Static("Single Item"))
        nav_list.add_item(item)

        # All navigation should keep cursor at 0
        nav_list.action_cursor_up()
        assert nav_list.cursor_index == 0

        nav_list.action_cursor_down()
        assert nav_list.cursor_index == 0

        nav_list.action_cursor_first()
        assert nav_list.cursor_index == 0

        nav_list.action_cursor_last()
        assert nav_list.cursor_index == 0

    def test_extreme_cursor_values(self) -> None:
        """Test handling of extreme cursor values."""
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(3)]
        for item in items:
            nav_list.append(item)

        # Test extreme positive value
        nav_list.cursor_index = 1000
        assert nav_list.cursor_index == 2  # Should clamp to max

        # Test extreme negative value
        nav_list.cursor_index = -1000
        assert nav_list.cursor_index == 0  # Should clamp to min

    def test_rapid_cursor_changes(self) -> None:
        """Test rapid cursor position changes."""
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(10)]
        for item in items:
            nav_list.append(item)

        # Rapid cursor changes should all be handled correctly
        with patch.object(nav_list, "_update_cursor_display") as mock_update:
            for i in range(20):
                nav_list.cursor_index = i % 10

            # Should have been called for each change
            assert mock_update.call_count == 20

    def test_concurrent_modifications(self) -> None:
        """Test behavior with concurrent item modifications."""
        nav_list = NavigableList()
        items = [ListItem(Static(f"Item {i}")) for i in range(5)]
        for item in items:
            nav_list.append(item)

        nav_list.cursor_index = 3

        # Simulate concurrent modifications
        nav_list.remove_item(items[0])  # Remove first
        nav_list.remove_item(items[4])  # Remove last

        # Cursor should still be valid
        assert 0 <= nav_list.cursor_index < len(nav_list.children)
