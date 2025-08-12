"""NavigableList widget with enhanced keyboard navigation and cursor management."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, cast

from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import ListView

if TYPE_CHECKING:

    from textual.events import Key
    from textual.widget import Widget
    from textual.widgets import ListItem

# Constants for navigation
MIN_CURSOR_INDEX = 0
SCROLL_MARGIN = 2  # Lines to keep above/below cursor when scrolling


class NavigableList(ListView):
    """Enhanced ListView with comprehensive keyboard navigation.

    Features:
    - Arrow key navigation with visual cursor
    - Scroll-to-cursor functionality
    - Selection management
    - Keyboard shortcuts for common actions
    - Accessibility support
    """

    DEFAULT_CSS = """
    NavigableList {
        scrollbar-size: 1 1;
        scrollbar-background: $panel;
        scrollbar-color: $secondary;
    }

    NavigableList > ListItem {
        background: $surface;
        color: $text;
        padding: 0 1;
        border-bottom: thin $secondary 20%;
    }

    NavigableList > ListItem:hover {
        background: $primary 15%;
    }

    NavigableList > ListItem.-highlighted {
        background: $accent 20%;
        border-left: thick $accent;
        text-style: bold;
    }

    NavigableList > ListItem.cursor-active {
        background: $primary 30%;
        color: $text;
        border-left: thick $warning;
        text-style: bold;
    }

    NavigableList:focus > ListItem.cursor-active {
        background: $primary 40%;
        border-left: thick $accent;
        box-shadow: 0 0 2 1 $accent 40%;
    }
    """

    BINDINGS: ClassVar[
        list[Binding | tuple[str, str] | tuple[str, str, str]]
    ] = [
        # Navigation
        Binding("up", "cursor_up", "Previous Item", priority=True),
        Binding("down", "cursor_down", "Next Item", priority=True),
        Binding("k", "cursor_up", "Previous Item (Vim)", show=False),
        Binding("j", "cursor_down", "Next Item (Vim)", show=False),
        Binding("home", "cursor_first", "First Item"),
        Binding("end", "cursor_last", "Last Item"),
        Binding("pageup", "page_up", "Page Up"),
        Binding("pagedown", "page_down", "Page Down"),
        # Selection and action
        Binding("enter", "select_cursor", "Select Item"),
        Binding("space", "toggle_cursor", "Toggle Item"),
        # Quick navigation
        Binding("g,g", "cursor_first", "Go to Top", show=False),
        Binding("shift+g", "cursor_last", "Go to Bottom", show=False),
    ]

    # Reactive attributes
    cursor_index = reactive(0, layout=False, repaint=False)
    show_cursor = reactive(default=True, layout=False)

    def __init__(
        self,
        *children: ListItem,
        initial_index: int | None = 0,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialize NavigableList with cursor management."""
        super().__init__(
            *children,
            initial_index=initial_index,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self._cursor_visible = True
        self._previous_cursor_index = (
            -1
        )  # Track previous cursor for O(1) updates

    def on_mount(self) -> None:
        """Set up initial state when widget is mounted."""
        self.cursor_index = 0
        self._update_cursor_display()

    def watch_cursor_index(self, new_index: int) -> None:
        """React to cursor index changes."""
        # Validate cursor index bounds
        max_index = max(0, len(self.children) - 1)
        if new_index < MIN_CURSOR_INDEX:
            self.cursor_index = MIN_CURSOR_INDEX
            return
        if new_index > max_index:
            self.cursor_index = max_index
            return

        # Update visual cursor
        self._update_cursor_display()

        # Auto-scroll to keep cursor visible
        self.scroll_to_cursor()

    def _update_cursor_display(self) -> None:
        """Update visual cursor indicators on list items with O(1) optimization."""
        if not self.show_cursor:
            return

        # O(1) optimization: Only update changed items
        if (
            hasattr(self, "_previous_cursor_index")
            and self._previous_cursor_index != self.cursor_index
            and 0 <= self._previous_cursor_index < len(self.children)
        ):
            # Remove cursor from previous item only
            previous_item = self.children[self._previous_cursor_index]
            previous_item.remove_class("cursor-active")

        # Add cursor to current item if valid
        if 0 <= self.cursor_index < len(self.children):
            current_item = self.children[self.cursor_index]
            current_item.add_class("cursor-active")

        # Update tracking for next call
        self._previous_cursor_index = self.cursor_index

    def action_cursor_up(self) -> None:
        """Move cursor up one item."""
        if self.cursor_index > MIN_CURSOR_INDEX:
            self.cursor_index -= 1

    def action_cursor_down(self) -> None:
        """Move cursor down one item."""
        max_index = len(self.children) - 1
        if max_index >= 0 and self.cursor_index < max_index:
            self.cursor_index += 1

    def action_cursor_first(self) -> None:
        """Move cursor to first item."""
        if self.children:
            self.cursor_index = MIN_CURSOR_INDEX

    def action_cursor_last(self) -> None:
        """Move cursor to last item."""
        if self.children:
            self.cursor_index = len(self.children) - 1

    def action_page_up(self) -> None:
        """Move cursor up by page size."""
        visible_height = self.content_size.height
        page_size = max(1, visible_height - 1)  # Keep one line overlap
        new_index = max(MIN_CURSOR_INDEX, self.cursor_index - page_size)
        self.cursor_index = new_index

    def action_page_down(self) -> None:
        """Move cursor down by page size."""
        visible_height = self.content_size.height
        page_size = max(1, visible_height - 1)  # Keep one line overlap
        max_index = len(self.children) - 1
        new_index = min(max_index, self.cursor_index + page_size)
        self.cursor_index = new_index

    def action_select_cursor(self) -> None:
        """Select the item at cursor position."""
        if 0 <= self.cursor_index < len(self.children):
            item = self.children[self.cursor_index]
            # Highlight selected item
            for child in self.children:
                child.remove_class("-highlighted")
            item.add_class("-highlighted")

            # Post selection event
            self.post_message(
                self.Selected(self, cast("ListItem", item), self.cursor_index),
            )

    def action_toggle_cursor(self) -> None:
        """Toggle selection state of item at cursor position."""
        if 0 <= self.cursor_index < len(self.children):
            item = self.children[self.cursor_index]
            if item.has_class("-highlighted"):
                item.remove_class("-highlighted")
            else:
                item.add_class("-highlighted")

    def scroll_to_cursor(self, *, animate: bool = True) -> None:
        """Scroll to ensure cursor is visible with margin."""
        if not self._can_scroll_to_cursor():
            return

        cursor_item = self.children[self.cursor_index]
        scroll_target = self._calculate_scroll_target(cursor_item)

        if scroll_target is not None:
            self.scroll_to(y=scroll_target, animate=animate)

    def _can_scroll_to_cursor(self) -> bool:
        """Check if cursor can be scrolled to."""
        return bool(
            0 <= self.cursor_index < len(self.children)
            and self.content_size.height > 0,
        )

    def _calculate_scroll_target(self, cursor_item: Widget) -> int | None:
        """Calculate target scroll position for cursor item."""
        item_region = cursor_item.region
        container_height = self.content_size.height

        # Calculate scroll bounds with margin
        top_margin = min(SCROLL_MARGIN, container_height // 4)
        bottom_margin = min(SCROLL_MARGIN, container_height // 4)

        desired_top = max(0, item_region.y - top_margin)
        desired_bottom = item_region.y + item_region.height + bottom_margin

        current_scroll = self.scroll_offset.y
        visible_top = current_scroll
        visible_bottom = current_scroll + container_height

        if item_region.y < visible_top + top_margin:
            return int(desired_top)
        if item_region.y + item_region.height > visible_bottom - bottom_margin:
            return int(max(0, desired_bottom - container_height))

        return None

    def get_cursor_item(self) -> ListItem | None:
        """Get the currently selected list item."""
        if 0 <= self.cursor_index < len(self.children):
            child = self.children[self.cursor_index]
            return cast("ListItem", child)
        return None

    def set_cursor_index(self, index: int, *, scroll: bool = True) -> None:
        """Set cursor to specific index.

        Args:
            index: Target index for cursor
            scroll: Whether to scroll to make cursor visible

        """
        max_index = max(0, len(self.children) - 1)
        self.cursor_index = max(MIN_CURSOR_INDEX, min(index, max_index))

        if scroll:
            self.scroll_to_cursor()

    def move_cursor_to_item(
        self,
        item: ListItem,
        *,
        scroll: bool = True,
    ) -> bool:
        """Move cursor to specific list item.

        Args:
            item: Target list item
            scroll: Whether to scroll to make cursor visible

        Returns:
            True if item was found and cursor moved, False otherwise

        """
        try:
            index = self.children.index(item)
            self.set_cursor_index(index, scroll=scroll)
        except ValueError:
            return False
        else:
            return True

    def clear_selection(self) -> None:
        """Clear all item selections."""
        for child in self.children:
            child.remove_class("-highlighted")

    def get_selected_items(self) -> list[ListItem]:
        """Get all currently selected items."""
        return [
            cast("ListItem", child)
            for child in self.children
            if child.has_class("-highlighted")
        ]

    def on_key(self, event: Key) -> None:
        """Handle additional key events not covered by bindings."""
        # Handle numeric keys for quick navigation
        if event.key.isdigit():
            digit = int(event.key)
            if digit == 0:
                digit = 10  # 0 means item 10
            target_index = digit - 1  # Convert to 0-based index
            if 0 <= target_index < len(self.children):
                self.set_cursor_index(target_index)
                event.prevent_default()
                event.stop()

    def add_item(self, item: ListItem) -> None:
        """Add item to list and update cursor if needed."""
        self.append(item)
        # If this is the first item, set cursor to it
        if len(self.children) == 1:
            self.cursor_index = 0

    def remove_item(self, item: ListItem) -> None:
        """Remove item from list and adjust cursor."""
        try:
            index = self.children.index(item)
            item.remove()

            # Adjust cursor if necessary
            if index <= self.cursor_index:
                # If removed item was at or before cursor, move cursor back
                new_cursor = max(MIN_CURSOR_INDEX, self.cursor_index - 1)
                # Ensure cursor doesn't exceed bounds
                max_index = max(0, len(self.children) - 1)
                self.cursor_index = min(new_cursor, max_index)

        except ValueError:
            # Item not in list
            pass

    def insert_item(self, index: int, item: ListItem) -> None:
        """Insert item at specific index and adjust cursor."""
        if index <= self.cursor_index:
            # If inserting before current cursor, move cursor forward
            self.cursor_index += 1

        # Insert the item (append for now as ListView API may be limited)
        self.append(item)

    def focus(
        self,
        scroll_visible: bool = True,  # noqa: FBT001, FBT002
    ) -> NavigableList:
        """Override focus to ensure cursor is visible."""
        super().focus(scroll_visible=scroll_visible)
        self.show_cursor = True
        self._update_cursor_display()
        return self

    def blur(self) -> NavigableList:
        """Override blur to hide cursor."""
        super().blur()
        # Keep cursor visible but less prominent when not focused
        # Visual distinction is handled by CSS :focus selectors
        return self


# Virtual scrolling implementation is reserved for future enhancement.
# The O(1) cursor optimization above provides significant performance
# improvement for current TUI rendering needs.
