"""Main filter panel widget for CCMonitor TUI application."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Collapsible, Static

from src.tui.utils.filter_state import FilterCriteria, FilterStateManager
from src.tui.widgets.filter_controls import (
    FilterActions,
    FilterApply,
    FilterClear,
    FilterLoadPreset,
    FilterSavePreset,
    FilterSummary,
    FilterUpdated,
    MessageTypeFilter,
    SearchFilter,
    TimeRangeFilter,
)

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from src.services.models import JSONLEntry


class FilterPanelToggled(Message):
    """Message emitted when filter panel is toggled."""

    def __init__(self, visible: bool) -> None:  # noqa: FBT001
        """Initialize the message."""
        super().__init__()
        self.visible = visible


class FilterApplied(Message):
    """Message emitted when filters are applied to data."""

    def __init__(self, filtered_entries: list[JSONLEntry]) -> None:
        """Initialize the message."""
        super().__init__()
        self.filtered_entries = filtered_entries


class FilterPanel(Widget):
    """Comprehensive filter panel for message filtering."""

    DEFAULT_CSS = """
    FilterPanel {
        width: 100%;
        height: auto;
        max-height: 50vh;
        background: $surface;
        border: round $primary;
        border-title-color: $primary;
        border-title-style: bold;
        padding: 1;
        margin-bottom: 1;
    }

    FilterPanel.collapsed {
        height: 3;
        overflow: hidden;
    }

    FilterPanel.expanded {
        height: auto;
        max-height: 50vh;
    }

    .filter-header {
        height: 3;
        padding: 0 1;
        border-bottom: solid $secondary;
        margin-bottom: 1;
    }

    .filter-title {
        text-style: bold;
        color: $primary;
        content-align: left middle;
    }

    .toggle-button {
        width: auto;
        height: 1;
        margin-left: 2;
    }

    .filter-content {
        height: auto;
        padding: 1;
        overflow: auto;
    }

    .filter-row {
        height: auto;
        margin-bottom: 1;
        layout: horizontal;
    }

    .filter-column {
        width: 1fr;
        height: auto;
        margin: 0 1;
    }

    .actions-row {
        height: auto;
        margin-top: 1;
        border-top: solid $secondary;
        padding-top: 1;
    }
    """

    BINDINGS: ClassVar[
        list[Binding | tuple[str, str] | tuple[str, str, str]]
    ] = [
        Binding("f", "toggle_filter_panel", "Toggle Filters", priority=True),
        Binding("ctrl+f", "focus_search", "Focus Search"),
        Binding("escape", "close_panel", "Close Panel"),
    ]

    # Reactive properties
    is_collapsed = reactive(default=True)

    def __init__(self, *, widget_id: str | None = None) -> None:
        """Initialize filter panel."""
        super().__init__(id=widget_id)
        self.filter_manager = FilterStateManager()
        self.message_type_filter: MessageTypeFilter | None = None
        self.time_range_filter: TimeRangeFilter | None = None
        self.search_filter: SearchFilter | None = None
        self.filter_summary: FilterSummary | None = None
        self.current_entries: list[JSONLEntry] = []

    def compose(self) -> ComposeResult:
        """Compose the filter panel layout."""
        with Vertical():
            # Filter header with toggle
            with Horizontal(classes="filter-header"):
                yield Static("🔍 Filters", classes="filter-title")
                yield Button(
                    "▼" if self.is_collapsed else "▲",
                    id="toggle-btn",
                    classes="toggle-button",
                )

            # Collapsible filter content
            with (
                Collapsible(
                    collapsed=self.is_collapsed,
                    id="filter-content",
                    classes="filter-content",
                ),
                ScrollableContainer(),
            ):
                # Filter summary
                self.filter_summary = FilterSummary(
                    widget_id="filter-summary",
                )
                yield self.filter_summary

                # Filter controls in rows
                with Horizontal(classes="filter-row"):
                    with Vertical(classes="filter-column"):
                        self.message_type_filter = MessageTypeFilter(
                            widget_id="message-type-filter",
                        )
                        yield self.message_type_filter

                    with Vertical(classes="filter-column"):
                        self.time_range_filter = TimeRangeFilter(
                            widget_id="time-range-filter",
                        )
                        yield self.time_range_filter

                # Search filter (full width)
                with Horizontal(classes="filter-row"):
                    self.search_filter = SearchFilter(
                        widget_id="search-filter",
                    )
                    yield self.search_filter

                # Action buttons
                with Horizontal(classes="actions-row"):
                    yield FilterActions(widget_id="filter-actions")

    def on_mount(self) -> None:
        """Initialize panel when mounted."""
        self._update_display()

    def watch_is_collapsed(
        self,
        _old_collapsed: bool,  # noqa: FBT001
        new_collapsed: bool,  # noqa: FBT001
    ) -> None:
        """React to collapse state changes."""
        self._update_collapse_state(new_collapsed)

    def _update_collapse_state(self, collapsed: bool) -> None:  # noqa: FBT001
        """Update panel display based on collapse state."""
        try:
            # Update toggle button text
            toggle_btn = self.query_one("#toggle-btn", Button)
            toggle_btn.label = "▼" if collapsed else "▲"

            # Update collapsible content
            content = self.query_one("#filter-content", Collapsible)
            content.collapsed = collapsed

            # Update panel classes
            if collapsed:
                self.add_class("collapsed")
                self.remove_class("expanded")
            else:
                self.add_class("expanded")
                self.remove_class("collapsed")

            # Emit toggle message
            self.post_message(FilterPanelToggled(not collapsed))

        except (ValueError, AttributeError) as e:
            self.log(f"Error updating collapse state: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "toggle-btn":
            self.action_toggle_filter_panel()

    def action_toggle_filter_panel(self) -> None:
        """Toggle filter panel visibility."""
        self.is_collapsed = not self.is_collapsed

    def action_focus_search(self) -> None:
        """Focus the search input."""
        if self.search_filter:
            try:
                search_input = self.search_filter.query_one("#search-input")
                search_input.focus()
            except (ValueError, AttributeError):
                pass

    def action_close_panel(self) -> None:
        """Close the filter panel."""
        if not self.is_collapsed:
            self.is_collapsed = True

    def on_filter_updated(self, event: FilterUpdated) -> None:
        """Handle filter criteria updates from child widgets."""
        # Update filter manager with new criteria
        self._merge_filter_criteria(event.criteria)
        self._update_display()
        self._apply_filters()

    def _merge_filter_criteria(self, new_criteria: FilterCriteria) -> None:
        """Merge new criteria with existing filters."""
        # Get current criteria
        current = self.filter_manager.current_criteria

        # Create merged criteria - use dict[str, Any] for proper typing
        merged_kwargs: dict[str, Any] = {}

        # Only update fields that are different from defaults in new_criteria
        if new_criteria.message_types != FilterCriteria().message_types:
            merged_kwargs["message_types"] = new_criteria.message_types
        else:
            merged_kwargs["message_types"] = current.message_types

        if new_criteria.time_range != FilterCriteria().time_range:
            merged_kwargs["time_range"] = new_criteria.time_range
        else:
            merged_kwargs["time_range"] = current.time_range

        if new_criteria.search_query != FilterCriteria().search_query:
            merged_kwargs["search_query"] = new_criteria.search_query
            merged_kwargs["search_regex"] = new_criteria.search_regex
            merged_kwargs["search_case_sensitive"] = (
                new_criteria.search_case_sensitive
            )
        else:
            merged_kwargs["search_query"] = current.search_query
            merged_kwargs["search_regex"] = current.search_regex
            merged_kwargs["search_case_sensitive"] = (
                current.search_case_sensitive
            )

        # Update filter manager
        self.filter_manager.update_criteria(**merged_kwargs)

    def _update_display(self) -> None:
        """Update all filter widget displays."""
        criteria = self.filter_manager.current_criteria

        # Update filter summary
        if self.filter_summary:
            self.filter_summary.update_summary(criteria)

        # Update individual filter widgets
        if self.message_type_filter:
            self.message_type_filter.update_selection(criteria.message_types)

        if self.time_range_filter:
            self.time_range_filter.update_selection(criteria.time_range)

        if self.search_filter:
            self.search_filter.update_search(
                criteria.search_query,
                criteria.search_regex,
                criteria.search_case_sensitive,
            )

    def _apply_filters(self) -> None:
        """Apply current filters to entries and emit results."""
        if not self.current_entries:
            return

        # Apply filters using filter manager
        filtered_entries = self.filter_manager.apply_filter(
            self.current_entries,
        )

        # Emit filtered results
        self.post_message(FilterApplied(filtered_entries))

    def on_filter_clear(self, _event: FilterClear) -> None:
        """Handle filter clear request."""
        self.filter_manager.clear_filters()
        self._update_display()
        self._apply_filters()

    def on_filter_apply(self, _event: FilterApply) -> None:
        """Handle filter apply request."""
        self._apply_filters()

    def on_filter_save_preset(self, _event: FilterSavePreset) -> None:
        """Handle save preset request."""
        # This would typically open a dialog to get preset name
        # For now, save with a default name
        preset_name = f"Custom Filter {len(self.filter_manager.presets) + 1}"
        success = self.filter_manager.save_preset(
            preset_name,
            "User-defined filter",
        )
        if success:
            self.notify(f"Preset '{preset_name}' saved")
        else:
            self.notify("Failed to save preset", severity="error")

    def on_filter_load_preset(self, _event: FilterLoadPreset) -> None:
        """Handle load preset request."""
        # This would typically open a dialog to select preset
        # For now, cycle through available presets
        preset_names = self.filter_manager.get_preset_names()
        if preset_names:
            # Simple cycling logic - in real implementation would use a selector
            preset_name = preset_names[0]  # Just use first preset for demo
            criteria = self.filter_manager.apply_preset(preset_name)
            if criteria:
                self._update_display()
                self._apply_filters()
                self.notify(f"Applied preset: {preset_name}")

    def update_entries(self, entries: list[JSONLEntry]) -> None:
        """Update the entries to be filtered."""
        self.current_entries = entries
        self._apply_filters()

    def get_current_criteria(self) -> FilterCriteria:
        """Get current filter criteria."""
        return self.filter_manager.current_criteria

    def set_filter_criteria(self, criteria: FilterCriteria) -> None:
        """Set filter criteria programmatically."""
        # Update filter manager
        self.filter_manager.current_criteria = criteria
        self._update_display()
        self._apply_filters()

    def get_filtered_entries(self) -> list[JSONLEntry]:
        """Get currently filtered entries."""
        if not self.current_entries:
            return []
        return self.filter_manager.apply_filter(self.current_entries)

    def reset_filters(self) -> None:
        """Reset all filters to default state."""
        self.filter_manager.clear_filters()
        self._update_display()
        self._apply_filters()
