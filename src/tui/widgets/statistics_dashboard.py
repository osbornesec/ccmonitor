"""Statistics dashboard widget for detailed analytics and metrics."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, ClassVar

from textual.binding import Binding
from textual.containers import Grid, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, DataTable, Label, Static

from src.services.models import JSONLEntry, MessageType
from src.tui.widgets.export_manager import (
    ConversationExporter,
    ExportConfig,
    ExportConfirmed,
    ExportManager,
)
from src.tui.widgets.filter_panel import FilterApplied, FilterPanel

if TYPE_CHECKING:
    from textual.app import ComposeResult


class StatisticsMetrics:
    """Container for statistics calculations."""

    def __init__(self, entries: list[JSONLEntry]) -> None:
        """Initialize metrics from entries."""
        self.entries = entries
        self.total_messages = len(entries)
        self.message_counts = self._calculate_message_counts()
        self.hourly_distribution = self._calculate_hourly_distribution()
        self.daily_activity = self._calculate_daily_activity()
        self.tool_usage = self._calculate_tool_usage()
        self.session_stats = self._calculate_session_stats()
        self.performance_metrics = self._calculate_performance_metrics()

    def _calculate_message_counts(self) -> dict[MessageType, int]:
        """Calculate counts by message type."""
        counts: dict[MessageType, int] = defaultdict(int)
        for entry in self.entries:
            counts[entry.type] += 1
        return dict(counts)

    def _calculate_hourly_distribution(self) -> dict[int, int]:
        """Calculate message distribution by hour of day."""
        hourly: dict[int, int] = defaultdict(int)
        for entry in self.entries:
            if entry.timestamp:
                try:
                    ts = datetime.fromisoformat(entry.timestamp)
                    hourly[ts.hour] += 1
                except (ValueError, AttributeError):
                    pass
        return dict(hourly)

    def _calculate_daily_activity(self) -> dict[str, int]:
        """Calculate daily activity over last 7 days."""
        daily: dict[str, int] = defaultdict(int)
        cutoff = datetime.now(tz=UTC) - timedelta(days=7)

        for entry in self.entries:
            if entry.timestamp:
                try:
                    ts = datetime.fromisoformat(entry.timestamp)
                    if ts > cutoff:
                        day_key = ts.strftime("%Y-%m-%d")
                        daily[day_key] += 1
                except (ValueError, AttributeError):
                    pass
        return dict(daily)

    def _calculate_tool_usage(self) -> dict[str, int]:
        """Calculate tool usage statistics."""
        tool_counts: dict[str, int] = defaultdict(int)
        for entry in self.entries:
            if (
                entry.type in [MessageType.TOOL_CALL, MessageType.TOOL_USE]
                and entry.message
                and entry.message.tool
            ):
                tool_counts[entry.message.tool] += 1
        return dict(tool_counts)

    def _calculate_session_stats(self) -> dict[str, Any]:
        """Calculate session-based statistics."""
        sessions = defaultdict(list)
        for entry in self.entries:
            if entry.session_id:
                sessions[entry.session_id].append(entry)

        return {
            "total_sessions": len(sessions),
            "avg_messages_per_session": (
                sum(len(msgs) for msgs in sessions.values()) / len(sessions)
                if sessions
                else 0
            ),
            "longest_session": max(
                (len(msgs) for msgs in sessions.values()),
                default=0,
            ),
            "active_sessions": len(
                [
                    session_id
                    for session_id, msgs in sessions.items()
                    if self._is_recent_session(msgs)
                ],
            ),
        }

    def _is_recent_session(self, messages: list[JSONLEntry]) -> bool:
        """Check if session has recent activity."""
        cutoff = datetime.now(tz=UTC) - timedelta(hours=1)
        for msg in messages:
            if msg.timestamp:
                try:
                    ts = datetime.fromisoformat(msg.timestamp)
                    if ts > cutoff:
                        return True
                except (ValueError, AttributeError):
                    pass
        return False

    def _calculate_performance_metrics(self) -> dict[str, Any]:
        """Calculate performance-related metrics."""
        error_count = 0
        tool_errors = 0

        for entry in self.entries:
            if entry.tool_use_result:
                if isinstance(
                    entry.tool_use_result,
                    dict,
                ) and entry.tool_use_result.get("is_error", False):
                    tool_errors += 1
                elif (
                    isinstance(entry.tool_use_result, str)
                    and "error" in entry.tool_use_result.lower()
                ):
                    error_count += 1

        return {
            "error_rate": (
                (error_count / self.total_messages * 100)
                if self.total_messages
                else 0
            ),
            "tool_error_rate": (
                (tool_errors / self.total_messages * 100)
                if self.total_messages
                else 0
            ),
            "total_errors": error_count + tool_errors,
        }


class StatisticsCard(Widget):
    """Individual statistics card widget."""

    DEFAULT_CSS = """
    StatisticsCard {
        width: 1fr;
        height: 8;
        border: solid $primary;
        padding: 1;
        margin: 0 1;
    }

    StatisticsCard .card-title {
        text-style: bold;
        color: $primary;
        height: 1;
    }

    StatisticsCard .card-value {
        text-style: bold;
        color: $success;
        height: 2;
        content-align: center middle;
    }

    StatisticsCard .card-description {
        color: $text-muted;
        height: 2;
        text-align: center;
    }
    """

    def __init__(
        self,
        title: str,
        value: str,
        description: str = "",
        *,
        widget_id: str | None = None,
    ) -> None:
        """Initialize statistics card."""
        super().__init__(id=widget_id)
        self.card_title = title
        self.card_value = value
        self.card_description = description

    def compose(self) -> ComposeResult:
        """Compose the statistics card layout."""
        yield Static(self.card_title, classes="card-title")
        yield Static(self.card_value, classes="card-value")
        yield Static(self.card_description, classes="card-description")

    def update_card(self, value: str, description: str = "") -> None:
        """Update card value and description."""
        self.card_value = value
        self.card_description = description
        self.query_one(".card-value", Static).update(value)
        self.query_one(".card-description", Static).update(description)


class HourlyActivityChart(Widget):
    """Simple ASCII chart for hourly activity."""

    DEFAULT_CSS = """
    HourlyActivityChart {
        height: 12;
        border: solid $secondary;
        padding: 1;
    }

    .chart-title {
        text-style: bold;
        color: $primary;
        height: 1;
        text-align: center;
    }

    .chart-content {
        height: 1fr;
    }
    """

    def __init__(self, *, widget_id: str | None = None) -> None:
        """Initialize hourly activity chart."""
        super().__init__(id=widget_id)
        self.hourly_data: dict[int, int] = {}

    def compose(self) -> ComposeResult:
        """Compose the chart layout."""
        yield Static("📊 Activity by Hour", classes="chart-title")
        yield Static("", id="chart-display", classes="chart-content")

    def update_data(self, hourly_data: dict[int, int]) -> None:
        """Update chart with new data."""
        self.hourly_data = hourly_data
        chart_text = self._generate_ascii_chart()
        self.query_one("#chart-display", Static).update(chart_text)

    def _generate_ascii_chart(self) -> str:
        """Generate ASCII bar chart for hourly data."""
        if not self.hourly_data:
            return "No data available"

        max_count = max(self.hourly_data.values()) if self.hourly_data else 1
        chart_lines = []

        # Create chart with hours 0-23
        for hour in range(24):
            count = self.hourly_data.get(hour, 0)
            bar_length = int((count / max_count) * 20) if max_count > 0 else 0
            bar = "█" * bar_length + "░" * (20 - bar_length)
            chart_lines.append(f"{hour:2d}h |{bar}| {count:3d}")

        return "\n".join(chart_lines)


class ToolUsageTable(Widget):
    """Table showing tool usage statistics."""

    DEFAULT_CSS = """
    ToolUsageTable {
        height: 15;
        border: solid $secondary;
    }

    .table-title {
        height: 3;
        background: $primary-background;
        padding: 1;
        border-bottom: solid $primary;
    }

    .table-title-text {
        text-style: bold;
        color: $primary;
    }

    #tool-table {
        height: 1fr;
        scrollbar-size: 1 1;
    }
    """

    def __init__(self, *, widget_id: str | None = None) -> None:
        """Initialize tool usage table."""
        super().__init__(id=widget_id)

    def compose(self) -> ComposeResult:
        """Compose the tool usage table layout."""
        with Vertical():
            with Horizontal(classes="table-title"):
                yield Static(
                    "🔧 Tool Usage Statistics",
                    classes="table-title-text",
                )

            table: DataTable = DataTable(
                id="tool-table",
                cursor_type="row",
                zebra_stripes=True,
            )
            table.add_columns("Tool Name", "Usage Count", "Percentage")
            yield table

    def update_data(self, tool_data: dict[str, int]) -> None:
        """Update table with tool usage data."""
        table: DataTable = self.query_one("#tool-table", DataTable)
        table.clear()

        if not tool_data:
            table.add_row("No tools used", "0", "0.0%")
            return

        total_usage = sum(tool_data.values())
        sorted_tools = sorted(
            tool_data.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        for tool_name, count in sorted_tools:
            percentage = (count / total_usage * 100) if total_usage else 0
            table.add_row(
                tool_name,
                str(count),
                f"{percentage:.1f}%",
            )


class StatisticsDashboard(ModalScreen[None]):
    """Main statistics dashboard modal screen."""

    DEFAULT_CSS = """
    StatisticsDashboard {
        width: 100%;
        height: 100%;
        background: $surface;
    }

    #stats-header {
        height: 3;
        background: $primary-background;
        padding: 1;
        border-bottom: solid $primary;
    }

    #stats-title {
        text-style: bold;
        color: $primary;
    }

    #stats-subtitle {
        color: $text-muted;
    }

    #stats-content {
        height: 1fr;
        layout: grid;
        grid-size: 2 3;
        grid-gutter: 1;
        padding: 1;
    }

    #stats-cards {
        height: 10;
        column-span: 2;
    }

    #cards-container {
        layout: horizontal;
    }

    #hourly-chart {
        row-span: 2;
    }

    #tool-usage {
        row-span: 2;
    }

    #stats-actions {
        height: 3;
        border-top: solid $secondary;
        padding: 1;
        background: $panel;
    }
    """

    BINDINGS: ClassVar[
        list[Binding | tuple[str, str] | tuple[str, str, str]]
    ] = [
        Binding("r", "refresh_stats", "Refresh"),
        Binding("e", "export_stats", "Export"),
        Binding("f", "toggle_filter", "Filter"),
    ]

    # Reactive properties
    auto_refresh = reactive(default=True)
    refresh_interval = reactive(default=30)  # seconds

    def __init__(self, *, widget_id: str | None = None) -> None:
        """Initialize statistics dashboard."""
        super().__init__(id=widget_id)
        self.entries: list[JSONLEntry] = []
        self.filtered_entries: list[JSONLEntry] = []
        self.metrics: StatisticsMetrics | None = None
        self.filter_panel: FilterPanel | None = None
        self._refresh_task: asyncio.Task[None] | None = None

    def compose(self) -> ComposeResult:
        """Compose the dashboard layout."""
        with Vertical():
            # Header
            with Horizontal(id="stats-header"):
                yield Static("📈 Statistics Dashboard", id="stats-title")
                yield Static(
                    "Real-time analytics and insights",
                    id="stats-subtitle",
                )

            # Main content grid
            with Grid(id="stats-content"):
                # Statistics cards row
                with (
                    Horizontal(id="stats-cards"),
                    Horizontal(id="cards-container"),
                ):
                    yield StatisticsCard(
                        "Total Messages",
                        "0",
                        "All message types",
                        widget_id="card-total",
                    )
                    yield StatisticsCard(
                        "Active Sessions",
                        "0",
                        "Recent activity",
                        widget_id="card-sessions",
                    )
                    yield StatisticsCard(
                        "Tool Calls",
                        "0",
                        "Tool interactions",
                        widget_id="card-tools",
                    )
                    yield StatisticsCard(
                        "Error Rate",
                        "0.0%",
                        "System reliability",
                        widget_id="card-errors",
                    )

                # Charts and tables
                yield HourlyActivityChart(widget_id="hourly-chart")
                yield ToolUsageTable(widget_id="tool-usage")

            # Filter panel (initially hidden)
            self.filter_panel = FilterPanel(widget_id="stats-filter-panel")
            self.filter_panel.display = False
            yield self.filter_panel

            # Actions bar
            with Horizontal(id="stats-actions"):
                yield Button("🔄 Refresh", id="btn-refresh")
                yield Button("📊 Export", id="btn-export")
                yield Button("🔍 Filter", id="btn-filter")
                yield Label("Auto-refresh: ON", id="auto-refresh-status")

    async def on_mount(self) -> None:
        """Initialize dashboard when mounted."""
        # Start auto-refresh if enabled
        if self.auto_refresh:
            self._refresh_task = asyncio.create_task(self._auto_refresh_loop())

    def update_data(self, entries: list[JSONLEntry]) -> None:
        """Update dashboard with new data."""
        self.entries = entries
        self.filtered_entries = entries  # Initially unfiltered

        # Update filter panel
        if self.filter_panel:
            self.filter_panel.update_entries(entries)

        self._recalculate_and_display()

    def _recalculate_and_display(self) -> None:
        """Recalculate metrics and update display."""
        # Use filtered entries for calculations
        data_to_analyze = (
            self.filtered_entries if self.filtered_entries else self.entries
        )

        self.metrics = StatisticsMetrics(data_to_analyze)
        self._update_statistics_cards()
        self._update_charts_and_tables()

    def _update_statistics_cards(self) -> None:
        """Update the statistics cards."""
        if not self.metrics:
            return

        # Total messages card
        total_card = self.query_one("#card-total", StatisticsCard)
        total_card.update_card(
            str(self.metrics.total_messages),
            f"Across {self.metrics.session_stats['total_sessions']} sessions",
        )

        # Active sessions card
        sessions_card = self.query_one("#card-sessions", StatisticsCard)
        sessions_card.update_card(
            str(self.metrics.session_stats["active_sessions"]),
            (
                f"Avg {self.metrics.session_stats['avg_messages_per_session']:.1f} "
                "msgs/session"
            ),
        )

        # Tool calls card
        tool_count = sum(
            count
            for msg_type, count in self.metrics.message_counts.items()
            if msg_type in [MessageType.TOOL_CALL, MessageType.TOOL_USE]
        )
        tools_card = self.query_one("#card-tools", StatisticsCard)
        tools_card.update_card(
            str(tool_count),
            f"{len(self.metrics.tool_usage)} unique tools",
        )

        # Error rate card
        errors_card = self.query_one("#card-errors", StatisticsCard)
        errors_card.update_card(
            f"{self.metrics.performance_metrics['error_rate']:.1f}%",
            f"{self.metrics.performance_metrics['total_errors']} total errors",
        )

    def _update_charts_and_tables(self) -> None:
        """Update charts and tables."""
        if not self.metrics:
            return

        # Update hourly activity chart
        hourly_chart = self.query_one("#hourly-chart", HourlyActivityChart)
        hourly_chart.update_data(self.metrics.hourly_distribution)

        # Update tool usage table
        tool_table = self.query_one("#tool-usage", ToolUsageTable)
        tool_table.update_data(self.metrics.tool_usage)

    def on_filter_applied(self, message: FilterApplied) -> None:
        """Handle filtered entries from filter panel."""
        self.filtered_entries = message.filtered_entries
        self._recalculate_and_display()

        # Show filter status
        total_count = len(self.entries)
        filter_count = len(message.filtered_entries)
        if filter_count < total_count:
            self.notify(f"Filtered: {filter_count}/{total_count} entries")

    def action_refresh_stats(self) -> None:
        """Manually refresh statistics."""
        self._recalculate_and_display()
        self.notify("Statistics refreshed")

    def action_export_stats(self) -> None:
        """Export statistics data."""
        if not self.metrics:
            self.notify("No data to export", severity="warning")
            return

        # Create export manager with current data
        export_manager = ExportManager(
            self.entries,
            statistics_metrics=self._get_statistics_dict(),
            filtered_entries=(
                self.filtered_entries if self.filtered_entries else None
            ),
        )

        # Show export dialog
        self.app.push_screen(export_manager)

    def _get_statistics_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary for export."""
        if not self.metrics:
            return {}

        return {
            "total_messages": self.metrics.total_messages,
            "message_counts": {
                k.value: v for k, v in self.metrics.message_counts.items()
            },
            "hourly_distribution": self.metrics.hourly_distribution,
            "daily_activity": self.metrics.daily_activity,
            "tool_usage": self.metrics.tool_usage,
            "session_stats": self.metrics.session_stats,
            "performance_metrics": self.metrics.performance_metrics,
        }

    def action_toggle_filter(self) -> None:
        """Toggle filter panel visibility."""
        if self.filter_panel:
            self.filter_panel.display = not self.filter_panel.display
            status = "shown" if self.filter_panel.display else "hidden"
            self.notify(f"Filter panel {status}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "btn-refresh":
            self.action_refresh_stats()
        elif event.button.id == "btn-export":
            self.action_export_stats()
        elif event.button.id == "btn-filter":
            self.action_toggle_filter()

    def on_export_confirmed(self, message: ExportConfirmed) -> None:
        """Handle export confirmation and perform actual export."""
        # Create exporter and export data
        exporter = ConversationExporter()

        # Use filtered entries if filter was applied, otherwise use all entries
        entries_to_export = (
            self.filtered_entries if message.filter_applied else self.entries
        )

        # Create export config
        export_config = ExportConfig(
            include_metadata=message.include_metadata,
            threading_enabled=message.threading_enabled,
            statistics_metrics=(
                self._get_statistics_dict() if self.metrics else None
            ),
        )

        success = exporter.export_data(
            entries_to_export,
            message.file_path,
            message.export_format,
            export_config,
        )

        if success:
            self.notify(
                f"✅ Exported to {message.file_path}",
                severity="information",
            )
        else:
            self.notify(
                f"❌ Export failed: {message.file_path}",
                severity="error",
            )

    async def _auto_refresh_loop(self) -> None:
        """Auto-refresh loop for real-time updates."""
        while self.auto_refresh:
            await asyncio.sleep(self.refresh_interval)
            if self.auto_refresh:  # Check again in case it was disabled
                self._recalculate_and_display()

    def toggle_auto_refresh(self) -> None:
        """Toggle auto-refresh on/off."""
        self.auto_refresh = not self.auto_refresh
        status_label = self.query_one("#auto-refresh-status", Label)

        if self.auto_refresh:
            status_label.update("Auto-refresh: ON")
            if not self._refresh_task:
                self._refresh_task = asyncio.create_task(
                    self._auto_refresh_loop(),
                )
        else:
            status_label.update("Auto-refresh: OFF")
            if self._refresh_task:
                self._refresh_task.cancel()
                self._refresh_task = None

    def on_unmount(self) -> None:
        """Clean up when widget is unmounted."""
        if self._refresh_task:
            self._refresh_task.cancel()
