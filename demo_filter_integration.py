#!/usr/bin/env python3
"""Filter UI Integration Guide for CCMonitor TUI.

This demonstrates how to integrate the comprehensive filter system with widgets.

USAGE:
1. Import the filter components:
   from src.tui.widgets.filter_panel import FilterPanel, FilterApplied

2. Add FilterPanel to your widget hierarchy

3. Listen for FilterApplied messages to update your data displays

4. Use the FilterStateManager for programmatic filter control

COMPONENTS PROVIDED:
- FilterPanel: Main collapsible filter UI
- FilterControls: Individual filter widgets (MessageType, TimeRange, Search)
- FilterStateManager: State management and filtering engine
- FilterCriteria: Immutable filter configuration

FEATURES:
- Message type filtering (User, Assistant, Tool calls, System)
- Time range filtering (Last hour, day, week, custom)
- Content search with regex support
- Filter presets (save/load common filters)
- Collapsible UI that saves space
- Keyboard shortcuts (F to toggle, Ctrl+F to focus search)
- Real-time filtering with reactive updates
- Professional styling integrated with existing theme

INTEGRATION EXAMPLE:

```python
from textual.app import App
from src.tui.widgets.filter_panel import FilterPanel, FilterApplied

class MyApp(App):
    def compose(self):
        yield FilterPanel(widget_id="filters")
        yield MyDataTable(id="data-table")

    def on_filter_applied(self, event: FilterApplied):
        # Update your data display with filtered results
        table = self.query_one("#data-table")
        table.clear()
        for entry in event.filtered_entries:
            table.add_row(entry.type.value, entry.timestamp, ...)
```

The filter system is now fully integrated and ready for use in Phase 2!
"""

# This file serves as documentation and integration guide.
# For a working demo, see the actual integration in:
# - src/tui/widgets/project_dashboard.py (with filtering support)
# - src/tui/widgets/project_tabs.py (tab-level filtering)

if __name__ == "__main__":
    import sys

    sys.stdout.write(__doc__ or "")
