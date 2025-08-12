"""Focus management and keyboard navigation utilities for TUI components."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable

    from textual.app import App

# Constants
MAX_FOCUS_HISTORY = 10
MAX_CONTEXT_STACK = 5


class FocusDirection(Enum):
    """Direction for focus movement."""

    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    NEXT = "next"
    PREVIOUS = "previous"
    FIRST = "first"
    LAST = "last"


class FocusScope(Enum):
    """Scope of focus operations."""

    CURRENT_PANEL = "current_panel"
    ALL_PANELS = "all_panels"
    WITHIN_WIDGET = "within_widget"
    GLOBAL = "global"


@dataclass
class FocusableWidget:
    """Information about a focusable widget."""

    widget_id: str
    display_name: str
    can_focus: bool = True
    focus_priority: int = 0  # Higher priority = focused first
    focus_group: str = "default"
    tooltip: str = ""
    keyboard_shortcuts: list[str] | None = None

    def __post_init__(self) -> None:
        """Initialize keyboard shortcuts if not provided."""
        if self.keyboard_shortcuts is None:
            self.keyboard_shortcuts = []


class FocusHandler(Protocol):
    """Protocol for widgets that handle focus events."""

    def on_focus_gained(self) -> None:
        """Handle gaining focus."""

    def on_focus_lost(self) -> None:
        """Handle losing focus."""

    def on_focus_enter(self) -> bool:
        """Handle enter key when focused.

        Returns:
            True if the event was handled, False to propagate.

        """

    def can_receive_focus(self) -> bool:
        """Check if widget can currently receive focus."""


@dataclass
class FocusGroup:
    """Group of related focusable widgets."""

    name: str
    widgets: list[FocusableWidget]
    wrap_around: bool = True
    default_focus: str | None = None
    description: str = ""

    def get_widget_by_id(self, widget_id: str) -> FocusableWidget | None:
        """Get widget by ID."""
        for widget in self.widgets:
            if widget.widget_id == widget_id:
                return widget
        return None

    def get_next_widget(
        self, current_id: str, *, allow_wrap: bool = True,
    ) -> FocusableWidget | None:
        """Get the next focusable widget in the group."""
        current_index = self._find_widget_index(current_id)
        if current_index is None:
            return None

        return self._find_next_focusable_widget(
            current_index, allow_wrap=allow_wrap,
        )

    def _find_widget_index(self, widget_id: str) -> int | None:
        """Find the index of a widget by ID."""
        for i, widget in enumerate(self.widgets):
            if widget.widget_id == widget_id:
                return i
        return None

    def _find_next_focusable_widget(
        self, current_index: int, *, allow_wrap: bool = True,
    ) -> FocusableWidget | None:
        """Find the next focusable widget from the current index."""
        # Try forward search first
        next_widget = self._search_forward_from_index(current_index + 1)
        if next_widget:
            return next_widget

        # Try wrap around search if enabled
        if self.wrap_around and allow_wrap:
            return self._search_forward_from_index(0, current_index)

        return None

    def _search_forward_from_index(
        self, start_index: int, end_index: int | None = None,
    ) -> FocusableWidget | None:
        """Search for focusable widget from start_index to end_index."""
        end = end_index if end_index is not None else len(self.widgets)
        for i in range(start_index, end):
            widget = self.widgets[i]
            if widget.can_focus:
                return widget
        return None

    def get_previous_widget(self, current_id: str) -> FocusableWidget | None:
        """Get the previous focusable widget in the group."""
        try:
            current_index = next(
                i
                for i, w in enumerate(self.widgets)
                if w.widget_id == current_id
            )

            # Find previous focusable widget
            for i in range(len(self.widgets)):
                prev_index = (current_index - i - 1) % len(self.widgets)
                if not self.wrap_around and prev_index >= current_index:
                    break

                prev_widget = self.widgets[prev_index]
                if prev_widget.can_focus:
                    return prev_widget

        except StopIteration:
            pass

        return None


class FocusManager:
    """Manages focus state and keyboard navigation across the application."""

    def __init__(self, app: App[Any] | None = None) -> None:
        """Initialize focus manager with app reference.

        Args:
            app: The Textual application instance for widget access

        """
        self.app = app
        self.focus_groups: dict[str, FocusGroup] = {}
        self.current_focus: str | None = None
        self.focus_history: list[str] = []
        self.focus_stack: list[str] = []  # For modal/temporary focus
        self.focus_observers: list[FocusHandler] = []
        self._focus_callbacks: dict[str, list[Callable[[], None]]] = {}

    def set_app(self, app: App[Any]) -> None:
        """Set the application instance after initialization.

        Args:
            app: The Textual application instance

        """
        self.app = app

    def register_focus_group(self, group: FocusGroup) -> None:
        """Register a focus group.

        Args:
            group: The focus group to register

        """
        self.focus_groups[group.name] = group

    def register_focusable(
        self,
        group_name: str,
        widget: FocusableWidget,
    ) -> None:
        """Register a focusable widget to a group."""
        if group_name not in self.focus_groups:
            self.focus_groups[group_name] = FocusGroup(
                name=group_name,
                widgets=[],
            )

        group = self.focus_groups[group_name]

        # Remove existing widget with same ID
        group.widgets = [
            w for w in group.widgets if w.widget_id != widget.widget_id
        ]

        # Add new widget in priority order
        group.widgets.append(widget)
        group.widgets.sort(key=lambda w: (-w.focus_priority, w.widget_id))

    def unregister_focusable(self, widget_id: str) -> None:
        """Remove a focusable widget from all groups."""
        for group in self.focus_groups.values():
            group.widgets = [
                w for w in group.widgets if w.widget_id != widget_id
            ]

    def get_focusable_widgets(
        self,
        group_name: str | None = None,
    ) -> list[FocusableWidget]:
        """Get all focusable widgets, optionally filtered by group."""
        if group_name:
            group = self.focus_groups.get(group_name)
            return group.widgets if group else []

        # Return all widgets from all groups
        all_widgets = []
        for group in self.focus_groups.values():
            all_widgets.extend(group.widgets)
        return all_widgets

    def move_focus(
        self,
        direction: FocusDirection,
        scope: FocusScope = FocusScope.ALL_PANELS,
    ) -> str | None:
        """Move focus in the specified direction.

        Returns:
            The ID of the newly focused widget, or None if no change.

        """
        if not self.current_focus:
            return self.focus_first_available()

        return self._handle_focus_direction(direction, scope)

    def _handle_focus_direction(
        self,
        direction: FocusDirection,
        scope: FocusScope,
    ) -> str | None:
        """Handle specific focus direction movement."""
        if direction == FocusDirection.NEXT:
            return self._move_to_next_widget(scope)
        if direction == FocusDirection.PREVIOUS:
            return self._move_to_previous_widget(scope)
        if direction == FocusDirection.FIRST:
            return self.focus_first_available()
        if direction == FocusDirection.LAST:
            return self.focus_last_available()

        # Directional movement (up, down, left, right)
        return self._move_directional(direction, scope)

    def _move_to_next_widget(self, scope: FocusScope) -> str | None:
        """Move to the next focusable widget."""
        if not self.current_focus:
            return None

        # Find current widget's group
        current_group = self._find_widget_group(self.current_focus)
        if not current_group:
            return None

        # Try to move within the same group first
        # Disable wrap-around if cross-group navigation is allowed
        allow_wrap = scope != FocusScope.ALL_PANELS
        next_widget = current_group.get_next_widget(
            self.current_focus, allow_wrap=allow_wrap,
        )
        if next_widget:
            return self.set_focus(next_widget.widget_id)

        # If at end of group and scope allows cross-group movement, move to next group
        if scope == FocusScope.ALL_PANELS:
            return self._move_to_next_group()

        return None

    def _move_to_previous_widget(self, scope: FocusScope) -> str | None:
        """Move to the previous focusable widget."""
        if not self.current_focus:
            return None

        current_group = self._find_widget_group(self.current_focus)
        if not current_group:
            return None

        prev_widget = current_group.get_previous_widget(self.current_focus)
        if prev_widget:
            return self.set_focus(prev_widget.widget_id)

        # If at beginning of group and scope allows cross-group movement
        # move to previous group
        if scope == FocusScope.ALL_PANELS:
            return self._move_to_previous_group()

        return None

    def _move_directional(
        self,
        direction: FocusDirection,
        scope: FocusScope,
    ) -> str | None:
        """Handle directional focus movement (up, down, left, right)."""
        # For now, map directional movements to next/previous
        # This can be enhanced with spatial awareness later
        if direction in (FocusDirection.DOWN, FocusDirection.RIGHT):
            return self._move_to_next_widget(scope)
        if direction in (FocusDirection.UP, FocusDirection.LEFT):
            return self._move_to_previous_widget(scope)
        return None

    def _move_to_next_group(self) -> str | None:
        """Move focus to the first widget in the next group."""
        if not self.current_focus:
            return None

        current_group = self._find_widget_group(self.current_focus)
        if not current_group:
            return None

        next_group = self._find_next_group(current_group.name)
        return self._focus_first_in_group(next_group) if next_group else None

    def _find_next_group(self, current_group_name: str) -> FocusGroup | None:
        """Find the next group in sequence."""
        group_names = list(self.focus_groups.keys())
        try:
            current_index = group_names.index(current_group_name)
            next_index = (current_index + 1) % len(group_names)
            return self.focus_groups[group_names[next_index]]
        except ValueError:
            return None

    def _focus_first_in_group(self, group: FocusGroup) -> str | None:
        """Focus the first focusable widget in a group."""
        for widget in group.widgets:
            if widget.can_focus:
                return self.set_focus(widget.widget_id)
        return None

    def _move_to_previous_group(self) -> str | None:
        """Move focus to the last widget in the previous group."""
        if not self.current_focus:
            return None

        current_group = self._find_widget_group(self.current_focus)
        if not current_group:
            return None

        prev_group = self._find_previous_group(current_group.name)
        return self._focus_last_in_group(prev_group) if prev_group else None

    def _find_previous_group(
        self,
        current_group_name: str,
    ) -> FocusGroup | None:
        """Find the previous group in sequence."""
        group_names = list(self.focus_groups.keys())
        try:
            current_index = group_names.index(current_group_name)
            prev_index = (current_index - 1) % len(group_names)
            return self.focus_groups[group_names[prev_index]]
        except ValueError:
            return None

    def _focus_last_in_group(self, group: FocusGroup) -> str | None:
        """Focus the last focusable widget in a group."""
        for widget in reversed(group.widgets):
            if widget.can_focus:
                return self.set_focus(widget.widget_id)
        return None

    def _find_widget_group(self, widget_id: str) -> FocusGroup | None:
        """Find the group containing the specified widget."""
        for group in self.focus_groups.values():
            if group.get_widget_by_id(widget_id):
                return group
        return None

    def set_focus(self, widget_id: str) -> str | None:
        """Set focus to a specific widget.

        Returns:
            The widget ID if focus was set successfully, None otherwise.

        """
        # Validate widget exists and can receive focus
        widget_info = self._find_widget_info(widget_id)
        if not widget_info or not widget_info.can_focus:
            return None

        # Update focus history
        if self.current_focus and self.current_focus != widget_id:
            self.focus_history.append(self.current_focus)
            # Limit history size
            if len(self.focus_history) > MAX_FOCUS_HISTORY:
                self.focus_history.pop(0)

        old_focus = self.current_focus
        self.current_focus = widget_id

        # Notify observers
        self._notify_focus_change(old_focus, widget_id)

        return widget_id

    def _find_widget_info(self, widget_id: str) -> FocusableWidget | None:
        """Find widget information by ID."""
        for group in self.focus_groups.values():
            widget = group.get_widget_by_id(widget_id)
            if widget:
                return widget
        return None

    def focus_first_available(self) -> str | None:
        """Focus the first available widget with highest priority."""
        all_widgets = self.get_focusable_widgets()
        focusable = [w for w in all_widgets if w.can_focus]

        if focusable:
            # Sort by priority (highest first), then by ID for stability
            focusable.sort(key=lambda w: (-w.focus_priority, w.widget_id))
            return self.set_focus(focusable[0].widget_id)

        return None

    def focus_last_available(self) -> str | None:
        """Focus the last available widget."""
        all_widgets = self.get_focusable_widgets()
        focusable = [w for w in all_widgets if w.can_focus]

        if focusable:
            focusable.sort(key=lambda w: (-w.focus_priority, w.widget_id))
            return self.set_focus(focusable[-1].widget_id)

        return None

    def focus_previous_in_history(self) -> str | None:
        """Focus the most recent widget from history."""
        while self.focus_history:
            prev_widget_id = self.focus_history.pop()
            widget_info = self._find_widget_info(prev_widget_id)
            if widget_info and widget_info.can_focus:
                return self.set_focus(prev_widget_id)
        return None

    def push_focus_context(self, widget_id: str) -> None:
        """Push current focus onto stack (for modals/temporary focus)."""
        if self.current_focus:
            self.focus_stack.append(self.current_focus)
        self.set_focus(widget_id)

    def pop_focus_context(self) -> str | None:
        """Restore focus from stack."""
        if self.focus_stack:
            prev_focus = self.focus_stack.pop()
            return self.set_focus(prev_focus)
        return None

    def get_focus_info(
        self,
        widget_id: str | None = None,
    ) -> FocusableWidget | None:
        """Get focus information for a widget (current focus if not specified)."""
        target_id = widget_id or self.current_focus
        if not target_id:
            return None
        return self._find_widget_info(target_id)

    def get_keyboard_shortcuts(self) -> dict[str, str]:
        """Get all registered keyboard shortcuts mapped to widget IDs."""
        shortcuts = {}
        for group in self.focus_groups.values():
            for widget in group.widgets:
                if widget.keyboard_shortcuts:
                    for shortcut in widget.keyboard_shortcuts:
                        shortcuts[shortcut] = widget.widget_id
        return shortcuts

    def add_focus_observer(self, observer: FocusHandler) -> None:
        """Add a focus change observer."""
        if observer not in self.focus_observers:
            self.focus_observers.append(observer)

    def remove_focus_observer(self, observer: FocusHandler) -> None:
        """Remove a focus change observer."""
        if observer in self.focus_observers:
            self.focus_observers.remove(observer)

    def apply_visual_focus(self, widget_id: str, *, focused: bool) -> None:
        """Apply or remove visual focus indicators.

        Args:
            widget_id: ID of widget to update
            focused: Whether widget should appear focused

        """
        if not self.app:
            return

        with contextlib.suppress(Exception):
            widget = self.app.query_one(f"#{widget_id}")
            if focused:
                widget.add_class("focused")
                widget.add_class("focus-active")
            else:
                widget.remove_class("focused")
                widget.remove_class("focus-active")

    def handle_escape_context(self) -> bool:
        """Handle ESC key context navigation with fallback logic.

        Returns:
            True if ESC was handled, False otherwise

        """
        # Try focus context stack first
        if self.focus_stack:
            self.pop_focus_context()
            return True

        # Try focus history
        if self.focus_history:
            self.focus_previous_in_history()
            return True

        # Try unfocus current widget
        if self.current_focus and self.app:
            with contextlib.suppress(Exception):
                current_widget = self.app.query_one(f"#{self.current_focus}")
                current_widget.blur()
                self.apply_visual_focus(self.current_focus, focused=False)
                self.current_focus = None
                return True

        # Try pop modal screen
        if self.app and len(self.app.screen_stack) > 1:
            self.app.pop_screen()
            return True

        return False

    def _notify_focus_change(
        self,
        old_focus: str | None,
        new_focus: str,
    ) -> None:
        """Notify observers of focus changes and apply visual indicators."""
        # Remove visual focus from old widget
        if old_focus:
            self.apply_visual_focus(old_focus, focused=False)

        # Apply visual focus to new widget
        self.apply_visual_focus(new_focus, focused=True)

        # Notify registered observers
        for observer in self.focus_observers:
            with contextlib.suppress(Exception):
                if hasattr(observer, "on_focus_changed"):
                    observer.on_focus_changed(old_focus, new_focus)

        # Execute focus callbacks
        callbacks = self._focus_callbacks.get(new_focus, [])
        for callback in callbacks:
            with contextlib.suppress(Exception):
                callback()

    def clear_all(self) -> None:
        """Clear all focus groups and reset state."""
        # Clear visual focus indicators
        if self.current_focus:
            self.apply_visual_focus(self.current_focus, focused=False)

        self.focus_groups.clear()
        self.current_focus = None
        self.focus_history.clear()
        self.focus_stack.clear()
        self._focus_callbacks.clear()


# Global focus manager instance (app will be set later)
focus_manager = FocusManager()


def create_panel_focus_group(
    panel_name: str,
    panel_id: str,
    *,
    priority: int = 0,
    shortcuts: list[str] | None = None,
) -> FocusGroup:
    """Create a standard focus group for a panel."""
    widget = FocusableWidget(
        widget_id=panel_id,
        display_name=panel_name,
        focus_priority=priority,
        keyboard_shortcuts=shortcuts or [],
    )

    return FocusGroup(
        name=panel_name.lower().replace(" ", "_"),
        widgets=[widget],
        description=f"{panel_name} panel focus group",
    )
