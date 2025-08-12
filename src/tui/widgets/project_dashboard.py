"""Enhanced project dashboard widget for multi-project monitoring."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import DataTable, Label, Static

from src.services.file_monitor import FileMonitor
from src.services.jsonl_parser import JSONLParser, find_claude_activity_files
from src.services.models import JSONLEntry, MessageType
from src.tui.widgets.filter_panel import FilterApplied, FilterPanel

if TYPE_CHECKING:
    from textual.app import ComposeResult

# Time constants
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600


class ProjectInfo:
    """Information about a monitored project."""

    def __init__(self, path: Path) -> None:
        """Initialize project info."""
        self.path = path
        self.name = path.parent.name
        self.file_name = path.name
        self.last_activity: datetime | None = None
        self.message_count = 0
        self.user_messages = 0
        self.assistant_messages = 0
        self.tool_calls = 0
        self.is_active = False
        self.activity_rate = 0.0  # messages per minute

    def update_from_entries(self, entries: list[JSONLEntry]) -> None:
        """Update project info from parsed entries."""
        if not entries:
            return

        self._count_message_types(entries)
        self.message_count = len(entries)
        timestamps = self._extract_timestamps(entries)
        self._update_activity_metrics(timestamps)

    def _count_message_types(self, entries: list[JSONLEntry]) -> None:
        """Count different message types."""
        for entry in entries:
            if entry.type == MessageType.USER:
                self.user_messages += 1
            elif entry.type == MessageType.ASSISTANT:
                self.assistant_messages += 1
            elif entry.type in [MessageType.TOOL_CALL, MessageType.TOOL_USE]:
                self.tool_calls += 1

    def _extract_timestamps(self, entries: list[JSONLEntry]) -> list[datetime]:
        """Extract valid timestamps from entries."""
        timestamps = []
        for entry in entries:
            if entry.timestamp:
                try:
                    ts = datetime.fromisoformat(entry.timestamp)
                    timestamps.append(ts)
                except (ValueError, AttributeError):
                    pass
        return timestamps

    def _update_activity_metrics(self, timestamps: list[datetime]) -> None:
        """Update activity rate and status based on timestamps."""
        if not timestamps:
            return

        self.last_activity = max(timestamps)
        time_span = max(timestamps) - min(timestamps)
        if time_span.total_seconds() > 0:
            self.activity_rate = self.message_count / (
                time_span.total_seconds() / SECONDS_PER_MINUTE
            )

        # Mark as active if activity in last 5 minutes
        if self.last_activity:
            now = datetime.now(self.last_activity.tzinfo or UTC)
            self.is_active = (now - self.last_activity) < timedelta(minutes=5)


class ProjectDashboard(Widget):
    """Enhanced dashboard showing all active projects with statistics."""

    DEFAULT_CSS = """
    ProjectDashboard {
        width: 100%;
        height: 100%;
        background: $surface;
    }

    #dashboard-header {
        height: 3;
        background: $primary-background;
        padding: 1;
        border-bottom: solid $primary;
    }

    #dashboard-title {
        text-style: bold;
        color: $primary;
    }

    #dashboard-stats {
        color: $text-muted;
    }

    #projects-container {
        height: 1fr;
        layout: vertical;
    }

    #project-table {
        height: 1fr;
        scrollbar-size: 1 1;
    }

    #quick-stats {
        height: 3;
        border-top: solid $secondary;
        padding: 1;
        background: $panel;
    }

    .active-project {
        color: $success;
    }

    .idle-project {
        color: $warning;
    }

    .inactive-project {
        color: $text-muted;
    }
    """

    BINDINGS: ClassVar[
        list[Binding | tuple[str, str] | tuple[str, str, str]]
    ] = [
        Binding("r", "refresh", "Refresh"),
        Binding("enter", "open_project", "Open Project"),
        Binding("s", "sort_projects", "Sort"),
        Binding("f", "filter_active", "Filter Active"),
    ]

    # Reactive properties
    selected_project = reactive[str | None](None)
    show_only_active = reactive(default=False)
    sort_by = reactive("last_activity")  # "name", "last_activity", "messages"

    def __init__(self, *, widget_id: str | None = None) -> None:
        """Initialize the project dashboard."""
        super().__init__(id=widget_id)
        self.projects: dict[str, ProjectInfo] = {}
        self.file_monitor: FileMonitor | None = None
        self.parser = JSONLParser(file_age_limit_hours=1)
        self._refresh_task: asyncio.Task[None] | None = None
        self._auto_refresh_interval = 10  # seconds
        self.filter_panel: FilterPanel | None = None
        self.filtered_projects: dict[str, ProjectInfo] = {}
        self.all_entries: list[JSONLEntry] = []

    def compose(self) -> ComposeResult:
        """Compose the dashboard layout."""
        with Vertical(id="projects-container"):
            # Filter panel for project filtering
            self.filter_panel = FilterPanel(widget_id="dashboard-filter-panel")
            yield self.filter_panel

            # Header with title and global stats
            with Horizontal(id="dashboard-header"):
                yield Static("📊 Project Dashboard", id="dashboard-title")
                yield Static("Loading...", id="dashboard-stats")

            # Main project table
            table: DataTable = DataTable(
                id="project-table",
                cursor_type="row",
                zebra_stripes=True,
            )
            table.add_columns(
                "Status",
                "Project",
                "Last Activity",
                "Messages",
                "User",
                "AI",
                "Tools",
                "Rate",
            )
            yield table

            # Quick stats bar
            with Horizontal(id="quick-stats"):
                yield Label("Total: 0 projects", id="stat-total")
                yield Label("Active: 0", id="stat-active")
                yield Label("Messages: 0", id="stat-messages")
                yield Label("Last refresh: Never", id="stat-refresh")

    async def on_mount(self) -> None:
        """Initialize dashboard when mounted."""
        # Start file monitoring
        self.setup_file_monitor()

        # Initial project discovery
        await self.discover_projects()

        # Start auto-refresh
        self._refresh_task = asyncio.create_task(self._auto_refresh_loop())

    def setup_file_monitor(self) -> None:
        """Set up the file monitoring system."""
        claude_dir = Path.home() / ".claude" / "projects"

        if not claude_dir.exists():
            self.notify(
                "Claude projects directory not found",
                severity="warning",
            )
            return

        self.file_monitor = FileMonitor(
            watch_directories=[claude_dir],
            file_age_limit_hours=1,
            debounce_seconds=0.5,
        )

        # Add callbacks for real-time updates
        self.file_monitor.add_message_callback(self._on_new_message)
        self.file_monitor.add_error_callback(self._on_monitor_error)

        # Start monitoring
        self.file_monitor.start()

    def _on_new_message(self, entry: JSONLEntry, file_path: Path) -> None:
        """Handle new message from file monitor."""
        project = self._get_or_create_project(file_path)
        self._update_project_from_entry(project, entry)
        self.refresh_table()

    def _get_or_create_project(self, file_path: Path) -> ProjectInfo:
        """Get existing project or create new one."""
        project_key = str(file_path)
        if project_key not in self.projects:
            self.projects[project_key] = ProjectInfo(file_path)
        return self.projects[project_key]

    def _update_project_from_entry(
        self,
        project: ProjectInfo,
        entry: JSONLEntry,
    ) -> None:
        """Update project info from a single entry."""
        project.message_count += 1
        self._increment_message_type_count(project, entry.type)
        self._update_project_activity(project, entry.timestamp)

    def _increment_message_type_count(
        self,
        project: ProjectInfo,
        msg_type: MessageType,
    ) -> None:
        """Increment the appropriate message type counter."""
        if msg_type == MessageType.USER:
            project.user_messages += 1
        elif msg_type == MessageType.ASSISTANT:
            project.assistant_messages += 1
        elif msg_type in [MessageType.TOOL_CALL, MessageType.TOOL_USE]:
            project.tool_calls += 1

    def _update_project_activity(
        self,
        project: ProjectInfo,
        timestamp: str | None,
    ) -> None:
        """Update project activity from timestamp."""
        if not timestamp:
            return
        try:
            ts = datetime.fromisoformat(timestamp)
            project.last_activity = ts
            project.is_active = True
        except (ValueError, AttributeError):
            pass

    def _on_monitor_error(self, error: Exception, file_path: Path) -> None:
        """Handle monitoring error."""
        self.log(f"Monitor error for {file_path}: {error}")

    async def discover_projects(self) -> None:
        """Discover all JSONL files in Claude projects directory."""
        self.notify("Discovering projects...")

        recent_files = self._find_recent_jsonl_files()
        all_entries = await self._parse_project_files(recent_files)
        self._update_dashboard_with_entries(all_entries)

        self.notify(f"Found {len(self.projects)} active projects")

    def _find_recent_jsonl_files(self) -> list[Path]:
        """Find recent JSONL files for processing."""
        jsonl_files = find_claude_activity_files(
            claude_projects_dir=Path.home() / ".claude" / "projects",
            file_pattern="*.jsonl",
        )

        recent_files = []
        cutoff_time = datetime.now(tz=UTC) - timedelta(hours=1)

        for file_path in jsonl_files:
            try:
                mtime = datetime.fromtimestamp(
                    file_path.stat().st_mtime, tz=UTC,
                )
                if mtime > cutoff_time:
                    recent_files.append(file_path)
            except OSError:
                pass

        return recent_files

    async def _parse_project_files(
        self, file_paths: list[Path],
    ) -> list[JSONLEntry]:
        """Parse all project files and collect entries."""
        all_entries = []
        for file_path in file_paths:
            entries = await self._analyze_project_file(file_path)
            all_entries.extend(entries)
        return all_entries

    def _update_dashboard_with_entries(
        self, all_entries: list[JSONLEntry],
    ) -> None:
        """Update dashboard with collected entries."""
        self.all_entries = all_entries
        self._total_entries = len(all_entries)

        if self.filter_panel:
            self.filter_panel.update_entries(all_entries)

        self.refresh_table()
        self.update_stats()

    async def _analyze_project_file(self, file_path: Path) -> list[JSONLEntry]:
        """Analyze a single project file and return entries."""
        project_key = str(file_path)

        if project_key not in self.projects:
            self.projects[project_key] = ProjectInfo(file_path)

        project = self.projects[project_key]

        # Parse file to get messages
        try:
            result = self.parser.parse_file(file_path)
            if result.entries:
                project.update_from_entries(result.entries)
                return result.entries
        except (OSError, ValueError) as e:
            self.log(f"Error parsing {file_path}: {e}")

        return []

    def refresh_table(self) -> None:
        """Refresh the project table display."""
        table = self.query_one("#project-table", DataTable)
        table.clear()

        projects_to_show = self._get_filtered_projects()
        projects_to_show = self._sort_projects(projects_to_show)

        for project in projects_to_show:
            self._add_project_row(table, project)

    def _get_filtered_projects(self) -> list[ProjectInfo]:
        """Get filtered list of projects."""
        projects = list(self.projects.values())
        if self.show_only_active:
            projects = [p for p in projects if p.is_active]
        return projects

    def _sort_projects(self, projects: list[ProjectInfo]) -> list[ProjectInfo]:
        """Sort projects based on current sort criteria."""
        if self.sort_by == "name":
            return sorted(projects, key=lambda p: p.name)
        if self.sort_by == "messages":
            return sorted(
                projects,
                key=lambda p: p.message_count,
                reverse=True,
            )
        # Default: sort by last_activity
        return sorted(
            projects,
            key=lambda p: p.last_activity or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )

    def _add_project_row(self, table: DataTable, project: ProjectInfo) -> None:
        """Add a single project row to the table."""
        status = self._get_project_status(project)
        last_activity = self._format_last_activity(project)
        rate = (
            f"{project.activity_rate:.1f}/min"
            if project.activity_rate > 0
            else "-"
        )

        table.add_row(
            status,
            project.name,
            last_activity,
            str(project.message_count),
            str(project.user_messages),
            str(project.assistant_messages),
            str(project.tool_calls),
            rate,
            key=str(project.path),
        )

    def _get_project_status(self, project: ProjectInfo) -> str:
        """Get status emoji for project."""
        if project.is_active:
            return "🟢"
        if project.message_count > 0:
            return "🟡"
        return "⚫"

    def _format_last_activity(self, project: ProjectInfo) -> str:
        """Format last activity time as relative string."""
        if not project.last_activity:
            return "Never"

        now = datetime.now(project.last_activity.tzinfo or UTC)
        delta = now - project.last_activity
        delta_seconds = delta.total_seconds()

        if delta_seconds < SECONDS_PER_MINUTE:
            return "Just now"
        if delta_seconds < SECONDS_PER_HOUR:
            return f"{int(delta_seconds / SECONDS_PER_MINUTE)}m ago"
        return project.last_activity.strftime("%H:%M")

    def update_stats(self) -> None:
        """Update the statistics display."""
        total = len(self.projects)
        active = sum(1 for p in self.projects.values() if p.is_active)
        messages = sum(p.message_count for p in self.projects.values())

        # Update header stats
        stats = self.query_one("#dashboard-stats", Static)
        stats.update(f"Active: {active}/{total} | Messages: {messages:,}")

        # Update quick stats bar
        self.query_one("#stat-total", Label).update(f"Total: {total} projects")
        self.query_one("#stat-active", Label).update(f"Active: {active}")
        self.query_one("#stat-messages", Label).update(
            f"Messages: {messages:,}",
        )
        self.query_one("#stat-refresh", Label).update(
            f"Last refresh: {datetime.now(tz=UTC):%H:%M:%S}",
        )

    async def _auto_refresh_loop(self) -> None:
        """Auto-refresh the dashboard periodically."""
        while True:
            await asyncio.sleep(self._auto_refresh_interval)
            await self.action_refresh()

    async def action_refresh(self) -> None:
        """Manually refresh the dashboard."""
        await self.discover_projects()

    def action_open_project(self) -> None:
        """Open the selected project in a new tab."""
        table = self.query_one("#project-table", DataTable)
        if table.cursor_row is not None:
            row_key = table.get_row_at(table.cursor_row)[0]  # Get the key
            if row_key:
                # Get project info
                project = self.projects.get(str(row_key))
                if project:
                    # Emit event to open project tab
                    self.post_message(
                        OpenProjectTab(project.path, project.name),
                    )

    def action_sort_projects(self) -> None:
        """Cycle through sort options."""
        sort_options = ["last_activity", "name", "messages"]
        current_index = sort_options.index(self.sort_by)
        self.sort_by = sort_options[(current_index + 1) % len(sort_options)]
        self.refresh_table()
        self.notify(f"Sorted by: {self.sort_by.replace('_', ' ').title()}")

    def action_filter_active(self) -> None:
        """Toggle showing only active projects."""
        self.show_only_active = not self.show_only_active
        self.refresh_table()
        filter_state = "active only" if self.show_only_active else "all"
        self.notify(f"Showing: {filter_state}")

    def on_filter_applied(self, message: FilterApplied) -> None:
        """Handle filtered entries from filter panel."""
        # Update all_entries with filtered data
        self.all_entries = message.filtered_entries

        # Rebuild projects from filtered entries
        self._rebuild_projects_from_entries(message.filtered_entries)

        # Refresh display
        self.refresh_table()
        self.update_stats()

        # Show filter status
        filter_count = len(message.filtered_entries)
        total_count = (
            len(self.all_entries)
            if hasattr(self, "_total_entries")
            else filter_count
        )
        if filter_count < total_count:
            self.notify(f"Filtered: {filter_count}/{total_count} entries")

    def _rebuild_projects_from_entries(
        self,
        entries: list[JSONLEntry],
    ) -> None:
        """Rebuild project information from filtered entries."""
        self.projects.clear()
        project_entries = self._group_entries_by_project(entries)
        self._create_projects_from_grouped_entries(project_entries)

    def _group_entries_by_project(
        self,
        entries: list[JSONLEntry],
    ) -> dict[str, list[JSONLEntry]]:
        """Group entries by project key."""
        project_entries: dict[str, list[JSONLEntry]] = {}
        for entry in entries:
            project_key = self._get_project_key_from_entry(entry)
            if project_key:
                if project_key not in project_entries:
                    project_entries[project_key] = []
                project_entries[project_key].append(entry)
        return project_entries

    def _create_projects_from_grouped_entries(
        self,
        project_entries: dict[str, list[JSONLEntry]],
    ) -> None:
        """Create project info objects from grouped entries."""
        for project_key, project_entry_list in project_entries.items():
            project_path = Path(project_key)
            if project_path.exists():
                project_info = ProjectInfo(project_path)
                project_info.update_from_entries(project_entry_list)
                self.projects[project_key] = project_info

    def _get_project_key_from_entry(self, entry: JSONLEntry) -> str | None:
        """Extract project key from entry metadata."""
        # For now, we'll use session_id as a proxy for project
        # In a real implementation, we'd need better project identification
        if entry.session_id:
            # Use a safe temporary path for session-based projects
            temp_dir = Path.home() / ".cache" / "ccmonitor"
            temp_dir.mkdir(parents=True, exist_ok=True)
            return str(temp_dir / f"session_{entry.session_id[:8]}.jsonl")
        return None

    def on_unmount(self) -> None:
        """Clean up when widget is unmounted."""
        # Stop monitoring
        if self.file_monitor:
            self.file_monitor.stop()

        # Cancel refresh task
        if self._refresh_task:
            self._refresh_task.cancel()


class OpenProjectTab(Message):
    """Message to request opening a project in a new tab."""

    def __init__(self, path: Path, name: str) -> None:
        """Initialize the message."""
        self.path = path
        self.name = name
