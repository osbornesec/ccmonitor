"""Filter controls widgets for CCMonitor TUI application."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Checkbox, Input, Select, Static

from src.services.models import MessageType
from src.tui.utils.filter_state import FilterCriteria, TimeRange

if TYPE_CHECKING:
    from textual.app import ComposeResult


class FilterUpdated(Message):
    """Message emitted when filter criteria is updated."""

    def __init__(self, criteria: FilterCriteria) -> None:
        """Initialize the message."""
        super().__init__()
        self.criteria = criteria


class MessageTypeFilter(Widget):
    """Widget for selecting message types to filter."""

    DEFAULT_CSS = """
    MessageTypeFilter {
        height: auto;
        padding: 1;
        border: round $secondary;
    }

    .filter-section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .type-checkbox {
        margin: 0 1;
    }
    """

    selected_types = reactive(default=frozenset(MessageType))

    def __init__(self, *, widget_id: str | None = None) -> None:
        """Initialize message type filter."""
        super().__init__(id=widget_id)

    def compose(self) -> ComposeResult:
        """Compose the message type filter layout."""
        with Vertical():
            yield Static("Message Types", classes="filter-section-title")
            with Horizontal():
                yield Checkbox(
                    "User",
                    id="type-user",
                    value=True,
                    classes="type-checkbox",
                )
                yield Checkbox(
                    "Assistant",
                    id="type-assistant",
                    value=True,
                    classes="type-checkbox",
                )
                yield Checkbox(
                    "Tool Calls",
                    id="type-tool",
                    value=True,
                    classes="type-checkbox",
                )
                yield Checkbox(
                    "System",
                    id="type-system",
                    value=True,
                    classes="type-checkbox",
                )

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox state changes."""
        if event.checkbox.id is None:
            return

        # Get current selected types as a set for modification
        current_types = set(self.selected_types)
        self._update_types_for_checkbox(
            event.checkbox.id,
            event.value,
            current_types,
        )

        # Update reactive property
        self.selected_types = frozenset(current_types)
        self.post_message(
            FilterUpdated(FilterCriteria(message_types=self.selected_types)),
        )

    def _update_types_for_checkbox(
        self,
        checkbox_id: str,
        is_checked: bool,  # noqa: FBT001
        current_types: set[MessageType],
    ) -> None:
        """Update message types based on checkbox selection."""
        # Map checkbox IDs to message types
        type_mapping = {
            "type-user": MessageType.USER,
            "type-assistant": MessageType.ASSISTANT,
            "type-tool": {
                MessageType.TOOL_CALL,
                MessageType.TOOL_USE,
                MessageType.TOOL_RESULT,
            },
            "type-system": MessageType.SYSTEM,
        }

        if checkbox_id not in type_mapping:
            return

        mapped_types = type_mapping[checkbox_id]
        if isinstance(mapped_types, set):
            # Handle tool types (multiple message types)
            if is_checked:
                current_types.update(mapped_types)
            else:
                current_types.difference_update(mapped_types)
        elif is_checked:
            current_types.add(mapped_types)  # type: ignore[arg-type]
        else:
            current_types.discard(mapped_types)  # type: ignore[arg-type]

    def update_selection(self, message_types: frozenset[MessageType]) -> None:
        """Update checkbox states based on selected message types."""
        self.selected_types = message_types

        # Update checkbox states
        self.query_one("#type-user", Checkbox).value = (
            MessageType.USER in message_types
        )
        self.query_one("#type-assistant", Checkbox).value = (
            MessageType.ASSISTANT in message_types
        )

        # Tool types - check if any tool type is selected
        tool_types = {
            MessageType.TOOL_CALL,
            MessageType.TOOL_USE,
            MessageType.TOOL_RESULT,
        }
        self.query_one("#type-tool", Checkbox).value = bool(
            tool_types & message_types,
        )

        self.query_one("#type-system", Checkbox).value = (
            MessageType.SYSTEM in message_types
        )


class TimeRangeFilter(Widget):
    """Widget for selecting time range filters."""

    DEFAULT_CSS = """
    TimeRangeFilter {
        height: auto;
        padding: 1;
        border: round $secondary;
    }

    .filter-section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .time-select {
        margin-bottom: 1;
    }
    """

    selected_range = reactive(default=TimeRange())

    def __init__(self, *, widget_id: str | None = None) -> None:
        """Initialize time range filter."""
        super().__init__(id=widget_id)

    def compose(self) -> ComposeResult:
        """Compose the time range filter layout."""
        with Vertical():
            yield Static("Time Range", classes="filter-section-title")
            yield Select(
                [
                    ("All time", "all"),
                    ("Last hour", "1h"),
                    ("Last day", "1d"),
                    ("Last week", "1w"),
                ],
                prompt="Select time range",
                id="time-range-select",
                classes="time-select",
            )

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle time range selection changes."""
        if event.value == "all":
            self.selected_range = TimeRange()
        elif event.value == "1h":
            self.selected_range = TimeRange.last_hour()
        elif event.value == "1d":
            self.selected_range = TimeRange.last_day()
        elif event.value == "1w":
            self.selected_range = TimeRange.last_week()

        self.post_message(
            FilterUpdated(FilterCriteria(time_range=self.selected_range)),
        )

    def update_selection(self, time_range: TimeRange) -> None:
        """Update time range selection."""
        self.selected_range = time_range

        # Map time range to select value
        select_widget = self.query_one("#time-range-select", Select)
        if time_range.relative == "1h":
            select_widget.value = "1h"
        elif time_range.relative == "1d":
            select_widget.value = "1d"
        elif time_range.relative == "1w":
            select_widget.value = "1w"
        else:
            select_widget.value = "all"


class SearchFilter(Widget):
    """Widget for content search filtering."""

    DEFAULT_CSS = """
    SearchFilter {
        height: auto;
        padding: 1;
        border: round $secondary;
    }

    .filter-section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .search-input {
        margin-bottom: 1;
    }

    .search-options {
        margin-bottom: 1;
    }
    """

    search_query = reactive(default="")
    search_regex = reactive(default=False)
    search_case_sensitive = reactive(default=False)

    def __init__(self, *, widget_id: str | None = None) -> None:
        """Initialize search filter."""
        super().__init__(id=widget_id)

    def compose(self) -> ComposeResult:
        """Compose the search filter layout."""
        with Vertical():
            yield Static("Content Search", classes="filter-section-title")
            yield Input(
                placeholder="Enter search query...",
                id="search-input",
                classes="search-input",
            )
            with Horizontal(classes="search-options"):
                yield Checkbox("Regex", id="search-regex")
                yield Checkbox("Case sensitive", id="search-case")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self.search_query = event.value
            self._emit_filter_update()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle search option checkbox changes."""
        if event.checkbox.id == "search-regex":
            self.search_regex = event.value
        elif event.checkbox.id == "search-case":
            self.search_case_sensitive = event.value

        self._emit_filter_update()

    def _emit_filter_update(self) -> None:
        """Emit filter update message."""
        criteria = FilterCriteria(
            search_query=self.search_query,
            search_regex=self.search_regex,
            search_case_sensitive=self.search_case_sensitive,
        )
        self.post_message(FilterUpdated(criteria))

    def update_search(
        self,
        query: str,
        regex: bool,  # noqa: FBT001
        case_sensitive: bool,  # noqa: FBT001
    ) -> None:
        """Update search criteria."""
        self.search_query = query
        self.search_regex = regex
        self.search_case_sensitive = case_sensitive

        # Update widgets
        self.query_one("#search-input", Input).value = query
        self.query_one("#search-regex", Checkbox).value = regex
        self.query_one("#search-case", Checkbox).value = case_sensitive


class FilterActions(Widget):
    """Widget for filter action buttons."""

    DEFAULT_CSS = """
    FilterActions {
        height: auto;
        padding: 1;
        layout: horizontal;
    }

    .action-button {
        margin: 0 1;
    }
    """

    BINDINGS: ClassVar[
        list[Binding | tuple[str, str] | tuple[str, str, str]]
    ] = [
        Binding("ctrl+c", "clear_filters", "Clear"),
        Binding("ctrl+s", "save_preset", "Save"),
        Binding("ctrl+l", "load_preset", "Load"),
    ]

    def __init__(self, *, widget_id: str | None = None) -> None:
        """Initialize filter actions."""
        super().__init__(id=widget_id)

    def compose(self) -> ComposeResult:
        """Compose the filter actions layout."""
        with Horizontal():
            yield Button("Clear", id="clear-btn", classes="action-button")
            yield Button("Save Preset", id="save-btn", classes="action-button")
            yield Button("Load Preset", id="load-btn", classes="action-button")
            yield Button(
                "Apply",
                id="apply-btn",
                classes="action-button",
                variant="primary",
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "clear-btn":
            self.action_clear_filters()
        elif event.button.id == "save-btn":
            self.action_save_preset()
        elif event.button.id == "load-btn":
            self.action_load_preset()
        elif event.button.id == "apply-btn":
            self.post_message(FilterApply())

    def action_clear_filters(self) -> None:
        """Clear all filters."""
        self.post_message(FilterClear())

    def action_save_preset(self) -> None:
        """Save current filter as preset."""
        self.post_message(FilterSavePreset())

    def action_load_preset(self) -> None:
        """Load a filter preset."""
        self.post_message(FilterLoadPreset())


class FilterClear(Message):
    """Message to clear all filters."""


class FilterApply(Message):
    """Message to apply current filters."""


class FilterSavePreset(Message):
    """Message to save current filter as preset."""


class FilterLoadPreset(Message):
    """Message to load a filter preset."""


class FilterSummary(Widget):
    """Widget displaying current filter summary."""

    DEFAULT_CSS = """
    FilterSummary {
        height: 3;
        padding: 1;
        border: round $primary;
        background: $primary 10%;
    }

    .summary-title {
        text-style: bold;
        color: $primary;
    }

    .summary-text {
        color: $text;
        text-style: italic;
    }
    """

    filter_summary = reactive(default="No filters active")

    def __init__(self, *, widget_id: str | None = None) -> None:
        """Initialize filter summary."""
        super().__init__(id=widget_id)

    def compose(self) -> ComposeResult:
        """Compose the filter summary layout."""
        with Vertical():
            yield Static("Active Filters:", classes="summary-title")
            yield Static(
                self.filter_summary,
                id="summary-text",
                classes="summary-text",
            )

    def watch_filter_summary(
        self,
        _old_summary: str,
        new_summary: str,
    ) -> None:
        """Update summary display when filter summary changes."""
        self.query_one("#summary-text", Static).update(new_summary)

    def update_summary(self, criteria: FilterCriteria) -> None:
        """Update filter summary from criteria."""
        self.filter_summary = criteria.get_summary()
