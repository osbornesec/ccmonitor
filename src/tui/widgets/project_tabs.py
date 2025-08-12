"""Tab management system for individual project views."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path  # noqa: TC003
from typing import TYPE_CHECKING, ClassVar

from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DataTable, Label, TabbedContent, TabPane

from src.services.jsonl_parser import JSONLParser
from src.services.models import JSONLEntry, MessageType
from src.tui.utils.search_highlighting import highlight_search_in_content
from src.tui.widgets.filter_panel import FilterApplied, FilterPanel

if TYPE_CHECKING:
    from textual.app import ComposeResult


class ProjectTab(TabPane):
    """Individual project tab showing detailed activity."""

    DEFAULT_CSS = """
    ProjectTab {
        padding: 1;
    }

    #project-header {
        height: 3;
        border-bottom: solid $primary;
        padding: 0 1;
    }

    #message-table {
        height: 1fr;
        scrollbar-size: 1 1;
    }

    #project-stats {
        height: 3;
        border-top: solid $secondary;
        padding: 1;
        background: $panel;
    }

    .message-user {
        color: $success;
    }

    .message-assistant {
        color: $primary;
    }

    .message-tool {
        color: $warning;
    }
    """

    BINDINGS: ClassVar[
        list[Binding | tuple[str, str] | tuple[str, str, str]]
    ] = [
        Binding("f", "toggle_filter", "Toggle Filter", priority=True),
        Binding("ctrl+f", "focus_search", "Search"),
        Binding("r", "refresh_messages", "Refresh"),
    ]

    def __init__(
        self,
        title: str,
        project_path: Path,
        *,
        widget_id: str | None = None,
    ) -> None:
        """Initialize project tab."""
        super().__init__(title, id=widget_id)
        self.project_path = project_path
        self.project_name = project_path.parent.name
        self.parser = JSONLParser(file_age_limit_hours=24)
        self.messages: list[JSONLEntry] = []
        self.filtered_messages: list[JSONLEntry] = []
        self.filter_panel: FilterPanel | None = None
        self._refresh_task: asyncio.Task[None] | None = None
        self._auto_refresh_interval = 5  # seconds

    def compose(self) -> ComposeResult:
        """Compose the project tab layout."""
        with Vertical():
            # Filter panel for message filtering
            self.filter_panel = FilterPanel(widget_id="project-filter-panel")
            yield self.filter_panel

            # Project header
            with Horizontal(id="project-header"):
                yield Label(
                    f"📁 {self.project_name}",
                    id="project-title",
                )
                yield Label(
                    f"File: {self.project_path.name}",
                    id="project-file",
                )

            # Message table
            table: DataTable = DataTable(
                id="message-table",
                cursor_type="row",
                zebra_stripes=True,
            )
            table.add_columns(
                "Time",
                "Type",
                "Content",
                "Details",
            )
            yield table

            # Project statistics
            with Horizontal(id="project-stats"):
                yield Label("Messages: 0", id="stat-messages")
                yield Label("User: 0", id="stat-user")
                yield Label("AI: 0", id="stat-ai")
                yield Label("Tools: 0", id="stat-tools")
                yield Label("Updated: Never", id="stat-updated")

    async def on_mount(self) -> None:
        """Initialize tab when mounted."""
        # Load initial messages
        await self.load_messages()

        # Start auto-refresh
        self._refresh_task = asyncio.create_task(self._auto_refresh_loop())

    async def load_messages(self) -> None:
        """Load messages from JSONL file."""
        try:
            result = self.parser.parse_file(self.project_path)
            if result.entries:
                self.messages = result.entries
                self.filtered_messages = result.entries  # Initially unfiltered

                # Update filter panel with messages
                if self.filter_panel:
                    self.filter_panel.update_entries(result.entries)

                self.refresh_display()
        except (OSError, ValueError) as e:
            self.log(f"Error loading messages from {self.project_path}: {e}")

    def refresh_display(self) -> None:
        """Refresh the message table and statistics."""
        table = self.query_one("#message-table", DataTable)
        table.clear()

        # Add filtered messages to table
        messages_to_show = (
            self.filtered_messages if self.filtered_messages else self.messages
        )
        for msg in messages_to_show:
            self._add_message_row(table, msg)

        # Update statistics based on filtered messages
        self.update_statistics()

    def _add_message_row(self, table: DataTable, msg: JSONLEntry) -> None:
        """Add a message row to the table."""
        time_str = self._format_timestamp(msg.timestamp)
        type_str = self._format_message_type(msg.type)
        content = self._get_highlighted_content(msg)
        details = self._get_message_details(msg)

        table.add_row(
            time_str,
            type_str,
            content,
            details,
        )

    def _get_highlighted_content(self, msg: JSONLEntry) -> str:
        """Get content with search highlighting if active."""
        raw_content = self._extract_message_content(msg)

        # Check if we have active search filters
        if self.filter_panel:
            criteria = self.filter_panel.get_current_criteria()
            if criteria.search_query:
                # Use highlighting with current search criteria
                highlighted_text = highlight_search_in_content(
                    raw_content,
                    search_query=criteria.search_query,
                    use_regex=criteria.search_regex,
                    case_sensitive=criteria.search_case_sensitive,
                    max_length=80,
                )
                return highlighted_text.plain  # Get plain text for DataTable

        # No search active, use regular truncation
        return self._truncate_content(raw_content)

    def _format_timestamp(self, timestamp: str | None) -> str:
        """Format timestamp for display."""
        if not timestamp:
            return "-"

        try:
            ts = datetime.fromisoformat(timestamp)
            return ts.strftime("%H:%M:%S")
        except (ValueError, AttributeError):
            max_length = 8
            return (
                timestamp[:max_length]
                if len(timestamp) > max_length
                else timestamp
            )

    def _format_message_type(self, msg_type: MessageType) -> str:
        """Format message type with emoji."""
        type_map = {
            MessageType.USER: "👤 User",
            MessageType.ASSISTANT: "🤖 AI",
            MessageType.TOOL_CALL: "🔧 Tool Call",
            MessageType.TOOL_USE: "⚙️ Tool Use",
            MessageType.TOOL_RESULT: "📊 Result",
            MessageType.SYSTEM: "⚠️ System",
            MessageType.UNKNOWN: "❓ Unknown",
        }
        return type_map.get(msg_type, str(msg_type))

    def _truncate_content(self, content: str, max_length: int = 80) -> str:
        """Truncate content for table display."""
        if len(content) <= max_length:
            return content
        return content[: max_length - 3] + "..."

    def _extract_message_content(self, msg: JSONLEntry) -> str:
        """Extract content from message."""
        # Try to get content from message
        content = self._extract_from_message(msg)
        if content:
            return content

        # Try to get content from tool result
        content = self._extract_from_tool_result(msg)
        if content:
            return content

        return ""

    def _extract_from_message(self, msg: JSONLEntry) -> str:
        """Extract content from message field."""
        if not msg.message:
            return ""

        if isinstance(msg.message.content, str):
            return msg.message.content

        if isinstance(msg.message.content, list):
            return self._extract_from_content_list(msg.message.content)

        return ""

    def _extract_from_content_list(self, content_list: list) -> str:
        """Extract text from content list."""
        for item in content_list:
            if hasattr(item, "text"):
                return str(getattr(item, "text", ""))
            if hasattr(item, "name"):
                name = getattr(item, "name", "unknown")
                return f"Tool: {name}"
        return ""

    def _extract_from_tool_result(self, msg: JSONLEntry) -> str:
        """Extract content from tool result."""
        if not msg.tool_use_result:
            return ""

        if isinstance(msg.tool_use_result, str):
            return msg.tool_use_result

        if isinstance(msg.tool_use_result, dict):
            return str(msg.tool_use_result)

        return ""

    def _get_message_details(self, msg: JSONLEntry) -> str:
        """Get additional message details."""
        details = []

        # Extract tool info from message content
        if msg.message and msg.message.tool:
            details.append(f"Tool: {msg.message.tool}")

        # Add git branch if present
        if msg.git_branch:
            details.append(f"Branch: {msg.git_branch}")

        return " | ".join(details) if details else "-"

    def update_statistics(self) -> None:
        """Update the statistics display."""
        # Use filtered messages for statistics
        messages_for_stats = (
            self.filtered_messages if self.filtered_messages else self.messages
        )

        user_count = sum(
            1 for m in messages_for_stats if m.type == MessageType.USER
        )
        ai_count = sum(
            1 for m in messages_for_stats if m.type == MessageType.ASSISTANT
        )
        tool_count = sum(
            1
            for m in messages_for_stats
            if m.type in [MessageType.TOOL_CALL, MessageType.TOOL_USE]
        )

        # Show both filtered and total counts if filtering is active
        total_messages = len(self.messages)
        filtered_count = len(messages_for_stats)

        if filtered_count < total_messages:
            message_text = f"Messages: {filtered_count}/{total_messages}"
        else:
            message_text = f"Messages: {total_messages}"

        self.query_one("#stat-messages", Label).update(message_text)
        self.query_one("#stat-user", Label).update(f"User: {user_count}")
        self.query_one("#stat-ai", Label).update(f"AI: {ai_count}")
        self.query_one("#stat-tools", Label).update(f"Tools: {tool_count}")
        self.query_one("#stat-updated", Label).update(
            f"Updated: {datetime.now(tz=UTC).strftime('%H:%M:%S')}",
        )

    def on_filter_applied(self, message: FilterApplied) -> None:
        """Handle filtered entries from filter panel."""
        self.filtered_messages = message.filtered_entries
        self.refresh_display()

        # Show filter status
        total_count = len(self.messages)
        filter_count = len(message.filtered_entries)
        if filter_count < total_count:
            self.notify(f"Filtered: {filter_count}/{total_count} messages")

    async def _auto_refresh_loop(self) -> None:
        """Auto-refresh the tab periodically."""
        while True:
            await asyncio.sleep(self._auto_refresh_interval)
            await self.load_messages()

    def on_unmount(self) -> None:
        """Clean up when tab is unmounted."""
        if self._refresh_task:
            self._refresh_task.cancel()


class ProjectTabManager(Widget):
    """Manager widget for project tabs."""

    DEFAULT_CSS = """
    ProjectTabManager {
        height: 100%;
        width: 100%;
    }

    #tab-container {
        height: 100%;
        width: 100%;
    }

    TabbedContent {
        height: 100%;
    }

    TabbedContent ContentSwitcher {
        height: 1fr;
    }
    """

    BINDINGS: ClassVar[
        list[Binding | tuple[str, str] | tuple[str, str, str]]
    ] = [
        Binding("ctrl+w", "close_tab", "Close Tab"),
        Binding("ctrl+tab", "next_tab", "Next Tab"),
        Binding("ctrl+shift+tab", "prev_tab", "Previous Tab"),
        Binding("alt+1", "goto_tab_1", "Tab 1"),
        Binding("alt+2", "goto_tab_2", "Tab 2"),
        Binding("alt+3", "goto_tab_3", "Tab 3"),
        Binding("alt+4", "goto_tab_4", "Tab 4"),
        Binding("alt+5", "goto_tab_5", "Tab 5"),
    ]

    def __init__(self, *, widget_id: str | None = None) -> None:
        """Initialize tab manager."""
        super().__init__(id=widget_id)
        self.open_tabs: dict[str, ProjectTab] = {}
        self.tab_content: TabbedContent | None = None

    def compose(self) -> ComposeResult:
        """Compose the tab manager layout."""
        with TabbedContent(id="tab-container") as tabs:
            self.tab_content = tabs
            # Start with an overview tab
            with TabPane("Overview", id="overview-tab"):
                yield Label(
                    "Select a project from the dashboard to open it in a tab",
                    id="overview-message",
                )

    def open_project_tab(self, project_path: Path, project_name: str) -> None:
        """Open a new tab for a project."""
        if not self.tab_content:
            return

        tab_key = str(project_path)

        # Check if tab already exists
        if tab_key in self.open_tabs:
            # Switch to existing tab
            tab = self.open_tabs[tab_key]
            self.tab_content.active = tab.id or tab_key
            self.notify(f"Switched to {project_name}")
            return

        # Create new tab
        tab_id = f"tab-{len(self.open_tabs)}"
        tab = ProjectTab(
            title=project_name[:20],  # Truncate long names
            project_path=project_path,
            widget_id=tab_id,
        )

        # Add to tabs
        self.open_tabs[tab_key] = tab
        self.tab_content.add_pane(tab)
        self.tab_content.active = tab_id

        self.notify(f"Opened {project_name}")

    def action_close_tab(self) -> None:
        """Close the current tab."""
        if not self.tab_content:
            return

        active_tab = self.tab_content.active_pane
        if not active_tab or active_tab.id == "overview-tab":
            return

        # Find and remove from open_tabs
        tab_key = self._find_tab_key(active_tab.id)
        if tab_key:
            del self.open_tabs[tab_key]
            if active_tab.id:
                self.tab_content.remove_pane(active_tab.id)
            self.notify("Tab closed")

    def _find_tab_key(self, tab_id: str | None) -> str | None:
        """Find the key for a tab by its ID."""
        for key, tab in self.open_tabs.items():
            if tab.id == tab_id:
                return key
        return None

    def action_next_tab(self) -> None:
        """Switch to next tab."""
        if not self.tab_content:
            return

        next_tab = self._get_next_tab()
        if next_tab and next_tab.id:
            self.tab_content.active = next_tab.id

    def _get_next_tab(self) -> TabPane | None:
        """Get the next tab in sequence."""
        if not self.tab_content:
            return None

        tabs = list(self.tab_content.children)
        if not tabs:
            return None

        current_idx = self._get_current_tab_index(tabs)
        next_idx = (current_idx + 1) % len(tabs)
        tab = tabs[next_idx]
        if isinstance(tab, TabPane):
            return tab
        return None

    def _get_current_tab_index(self, tabs: list) -> int:
        """Get the index of the current tab."""
        if not self.tab_content:
            return 0
        for i, tab in enumerate(tabs):
            if tab.id == self.tab_content.active:
                return i
        return 0

    def action_prev_tab(self) -> None:
        """Switch to previous tab."""
        if not self.tab_content:
            return

        prev_tab = self._get_prev_tab()
        if prev_tab and prev_tab.id:
            self.tab_content.active = prev_tab.id

    def _get_prev_tab(self) -> TabPane | None:
        """Get the previous tab in sequence."""
        if not self.tab_content:
            return None

        tabs = list(self.tab_content.children)
        if not tabs:
            return None

        current_idx = self._get_current_tab_index(tabs)
        prev_idx = (current_idx - 1) % len(tabs)
        tab = tabs[prev_idx]
        if isinstance(tab, TabPane):
            return tab
        return None

    def _goto_tab_n(self, n: int) -> None:
        """Go to tab number n (1-indexed)."""
        if self.tab_content:
            tabs = list(self.tab_content.children)
            if 0 < n <= len(tabs):
                tab_id = tabs[n - 1].id
                if tab_id:
                    self.tab_content.active = tab_id

    def action_goto_tab_1(self) -> None:
        """Go to tab 1."""
        self._goto_tab_n(1)

    def action_goto_tab_2(self) -> None:
        """Go to tab 2."""
        self._goto_tab_n(2)

    def action_goto_tab_3(self) -> None:
        """Go to tab 3."""
        self._goto_tab_n(3)

    def action_goto_tab_4(self) -> None:
        """Go to tab 4."""
        self._goto_tab_n(4)

    def action_goto_tab_5(self) -> None:
        """Go to tab 5."""
        self._goto_tab_n(5)


class CloseProjectTab(Message):
    """Message to request closing a project tab."""

    def __init__(self, path: Path) -> None:
        """Initialize the message."""
        super().__init__()
        self.path = path
