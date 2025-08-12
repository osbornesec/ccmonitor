"""Export manager widget for exporting conversation data and statistics."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, TextIO

from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.validation import ValidationResult, Validator
from textual.widgets import Button, Checkbox, Input, Label, Select, Static

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from src.services.models import JSONLEntry


@dataclass
class ExportConfig:
    """Configuration for export operation."""

    include_metadata: bool = True
    threading_enabled: bool = False
    statistics_metrics: dict[str, Any] | None = None


class PathValidator(Validator):
    """Validator for file paths."""

    def validate(self, value: str) -> ValidationResult:
        """Validate file path."""
        if not value.strip():
            return self.failure("Path cannot be empty")

        try:
            path = Path(value)
            # Check if parent directory exists or can be created
            if not path.parent.exists():
                try:
                    path.parent.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    return self.failure(f"Cannot create directory: {e}")
            return self.success()
        except (ValueError, OSError) as e:
            return self.failure(f"Invalid path: {e}")


class ExportFormat:
    """Export format configuration."""

    def __init__(
        self,
        name: str,
        extension: str,
        description: str,
        *,
        supports_filtering: bool = True,
        supports_threading: bool = False,
    ) -> None:
        """Initialize export format."""
        self.name = name
        self.extension = extension
        self.description = description
        self.supports_filtering = supports_filtering
        self.supports_threading = supports_threading


# Available export formats
EXPORT_FORMATS = [
    ExportFormat("JSON", ".json", "Complete conversation data in JSON format"),
    ExportFormat("CSV", ".csv", "Tabular data suitable for spreadsheets"),
    ExportFormat(
        "Markdown",
        ".md",
        "Readable conversation format",
        supports_threading=True,
    ),
    ExportFormat(
        "Plain Text",
        ".txt",
        "Simple text format",
        supports_threading=True,
    ),
    ExportFormat(
        "Statistics Report",
        ".json",
        "Analytics and metrics summary",
        supports_filtering=False,
    ),
]


class ExportConfirmed(Message):
    """Message sent when export is confirmed."""

    def __init__(
        self,
        file_path: Path,
        export_format: ExportFormat,
        *,
        include_metadata: bool,
        filter_applied: bool,
        threading_enabled: bool,
    ) -> None:
        """Initialize export confirmation message."""
        super().__init__()
        self.file_path = file_path
        self.export_format = export_format
        self.include_metadata = include_metadata
        self.filter_applied = filter_applied
        self.threading_enabled = threading_enabled


class ExportManager(ModalScreen[bool]):
    """Export manager for conversation data and statistics."""

    DEFAULT_CSS = """
    ExportManager {
        align: center middle;
    }

    #export-dialog {
        width: 80%;
        max-width: 100;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 2;
    }

    #export-title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .export-section {
        margin: 1 0;
        padding: 1;
        border: solid $secondary;
    }

    .section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    #format-selector {
        width: 100%;
        margin-bottom: 1;
    }

    #path-input {
        width: 100%;
        margin-bottom: 1;
    }

    .option-row {
        layout: horizontal;
        height: 3;
        align: left middle;
    }

    .option-label {
        min-width: 20;
        padding-right: 2;
    }

    #button-row {
        layout: horizontal;
        height: 3;
        align: center middle;
        margin-top: 1;
    }

    #button-row Button {
        margin: 0 1;
        min-width: 12;
    }
    """

    BINDINGS: ClassVar[
        list[Binding | tuple[str, str] | tuple[str, str, str]]
    ] = [
        Binding("escape", "cancel_export", "Cancel"),
        Binding("ctrl+s", "confirm_export", "Export"),
        Binding("enter", "confirm_export", "Export"),
    ]

    # Reactive properties
    selected_format = reactive("JSON")
    export_path = reactive("")
    include_metadata = reactive(default=True)
    threading_enabled = reactive(default=False)

    def __init__(
        self,
        entries: list[JSONLEntry],
        statistics_metrics: dict[str, Any] | None = None,
        *,
        filtered_entries: list[JSONLEntry] | None = None,
    ) -> None:
        """Initialize export manager."""
        super().__init__()
        self.entries = entries
        self.filtered_entries = filtered_entries or entries
        self.statistics_metrics = statistics_metrics
        self.has_filters = len(self.filtered_entries) < len(self.entries)

    def compose(self) -> ComposeResult:
        """Compose the export manager layout."""
        with Vertical(id="export-dialog"):
            yield Static("📊 Export Conversation Data", id="export-title")

            # Export format selection
            with Vertical(classes="export-section"):
                yield Static("Export Format", classes="section-title")
                format_options = [
                    (fmt.name, fmt.name) for fmt in EXPORT_FORMATS
                ]
                yield Select(
                    options=format_options,
                    value="JSON",
                    id="format-selector",
                )
                yield Static(
                    EXPORT_FORMATS[0].description,
                    id="format-description",
                )

            # File path configuration
            with Vertical(classes="export-section"):
                yield Static("Export Location", classes="section-title")
                default_path = self._generate_default_path()
                yield Input(
                    value=str(default_path),
                    placeholder="Enter file path...",
                    validators=[PathValidator()],
                    id="path-input",
                )

            # Export options
            with Vertical(classes="export-section"):
                yield Static("Export Options", classes="section-title")

                with Horizontal(classes="option-row"):
                    yield Label("Include metadata", classes="option-label")
                    yield Checkbox(
                        value=True,
                        id="metadata-checkbox",
                    )

                if self.has_filters:
                    with Horizontal(classes="option-row"):
                        yield Label(
                            "Use filtered data",
                            classes="option-label",
                        )
                        yield Checkbox(
                            value=True,
                            id="filter-checkbox",
                        )
                        yield Label(
                            f"({len(self.filtered_entries)}/"
                            f"{len(self.entries)} entries)",
                            classes="option-help",
                        )

                with Horizontal(classes="option-row"):
                    yield Label("Thread conversations", classes="option-label")
                    yield Checkbox(
                        value=False,
                        id="threading-checkbox",
                    )

            # Action buttons
            with Horizontal(id="button-row"):
                yield Button("Export", variant="primary", id="export-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def _generate_default_path(self) -> Path:
        """Generate default export file path."""
        timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"ccmonitor_export_{timestamp}.json"
        return Path.home() / "Downloads" / filename

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle format selection change."""
        if event.select.id == "format-selector":
            self.selected_format = str(event.value)
            # Update description and path extension
            selected_fmt = next(
                fmt
                for fmt in EXPORT_FORMATS
                if fmt.name == self.selected_format
            )

            # Update description
            description = self.query_one("#format-description", Static)
            description.update(selected_fmt.description)

            # Update path extension
            path_input = self.query_one("#path-input", Input)
            current_path = Path(str(path_input.value))
            new_path = current_path.with_suffix(selected_fmt.extension)
            path_input.value = str(new_path)

            # Update threading checkbox state
            threading_checkbox = self.query_one(
                "#threading-checkbox",
                Checkbox,
            )
            threading_checkbox.disabled = not selected_fmt.supports_threading

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "export-btn":
            self.action_confirm_export()
        elif event.button.id == "cancel-btn":
            self.action_cancel_export()

    def action_confirm_export(self) -> None:
        """Confirm and start export."""
        # Validate inputs
        path_input = self.query_one("#path-input", Input)
        if not path_input.is_valid:
            self.notify("Please enter a valid file path", severity="error")
            path_input.focus()
            return

        # Get export configuration
        file_path = Path(str(path_input.value))
        selected_fmt = next(
            fmt for fmt in EXPORT_FORMATS if fmt.name == self.selected_format
        )

        # Get option states
        include_metadata = self.query_one("#metadata-checkbox", Checkbox).value

        filter_applied = False
        if self.has_filters:
            filter_checkbox = self.query_one("#filter-checkbox", Checkbox)
            filter_applied = filter_checkbox.value

        threading_enabled = False
        if selected_fmt.supports_threading:
            threading_checkbox = self.query_one(
                "#threading-checkbox",
                Checkbox,
            )
            threading_enabled = (
                threading_checkbox.value and not threading_checkbox.disabled
            )

        # Send confirmation message
        self.post_message(
            ExportConfirmed(
                file_path=file_path,
                export_format=selected_fmt,
                include_metadata=include_metadata,
                filter_applied=filter_applied,
                threading_enabled=threading_enabled,
            ),
        )

        self.dismiss(result=True)

    def action_cancel_export(self) -> None:
        """Cancel export operation."""
        self.dismiss(result=False)


class ConversationExporter:
    """Handles the actual export of conversation data."""

    def __init__(self) -> None:
        """Initialize conversation exporter."""

    def export_data(
        self,
        entries: list[JSONLEntry],
        file_path: Path,
        export_format: ExportFormat,
        config: ExportConfig,
    ) -> bool:
        """Export conversation data to specified format."""
        try:
            return self._dispatch_export(
                entries, file_path, export_format, config,
            )
        except (OSError, ValueError):
            # Log error but don't raise - return False to indicate failure
            return False

    def _dispatch_export(
        self,
        entries: list[JSONLEntry],
        file_path: Path,
        export_format: ExportFormat,
        config: ExportConfig,
    ) -> bool:
        """Dispatch export to appropriate format handler."""
        format_handlers = {
            "JSON": lambda: self._export_json(
                entries,
                file_path,
                include_metadata=config.include_metadata,
                statistics_metrics=config.statistics_metrics,
            ),
            "CSV": lambda: self._export_csv(
                entries,
                file_path,
                include_metadata=config.include_metadata,
            ),
            "Markdown": lambda: self._export_markdown(
                entries,
                file_path,
                threading_enabled=config.threading_enabled,
            ),
            "Plain Text": lambda: self._export_text(entries, file_path),
            "Statistics Report": lambda: self._export_statistics(
                config.statistics_metrics or {},
                file_path,
            ),
        }

        handler = format_handlers.get(export_format.name)
        if handler:
            return handler()
        return False

    def _export_json(
        self,
        entries: list[JSONLEntry],
        file_path: Path,
        *,
        include_metadata: bool,
        statistics_metrics: dict[str, Any] | None,
    ) -> bool:
        """Export as JSON format."""
        data = {
            "export_info": {
                "timestamp": datetime.now(tz=UTC).isoformat(),
                "total_entries": len(entries),
                "format": "ccmonitor_export_v1",
            },
            "entries": [entry.model_dump() for entry in entries],
        }

        if include_metadata and statistics_metrics:
            data["statistics"] = statistics_metrics

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True

    def _export_csv(
        self,
        entries: list[JSONLEntry],
        file_path: Path,
        *,
        include_metadata: bool,
    ) -> bool:
        """Export as CSV format."""
        with file_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header
            headers = ["timestamp", "type", "session_id", "content"]
            if include_metadata:
                headers.extend(["git_branch", "tool_name", "cwd"])
            writer.writerow(headers)

            # Write data
            for entry in entries:
                content = self._extract_content_for_csv(entry)
                row = [
                    entry.timestamp or "",
                    entry.type.value,
                    entry.session_id or "",
                    content,
                ]

                if include_metadata:
                    tool_name = ""
                    if entry.message and entry.message.tool:
                        tool_name = entry.message.tool

                    row.extend(
                        [
                            entry.git_branch or "",
                            tool_name,
                            entry.cwd or "",
                        ],
                    )

                writer.writerow(row)
        return True

    def _extract_content_for_csv(self, entry: JSONLEntry) -> str:
        """Extract readable content from entry for CSV."""
        # Try message content first
        message_content = self._extract_message_content(entry)
        if message_content:
            return message_content

        # Try tool use result
        tool_content = self._extract_tool_result_content(entry)
        if tool_content:
            return tool_content

        return ""

    def _extract_message_content(self, entry: JSONLEntry) -> str:
        """Extract content from message field."""
        if not (entry.message and entry.message.content):
            return ""

        if isinstance(entry.message.content, str):
            return entry.message.content

        if isinstance(entry.message.content, list):
            # Extract text from content list using list comprehension
            text_parts = [
                str(getattr(item, "text", ""))
                for item in entry.message.content
                if hasattr(item, "text")
            ]
            return " ".join(text_parts)

        return ""

    def _extract_tool_result_content(self, entry: JSONLEntry) -> str:
        """Extract content from tool use result."""
        if not entry.tool_use_result:
            return ""

        if isinstance(entry.tool_use_result, str):
            return entry.tool_use_result

        if isinstance(entry.tool_use_result, dict):
            return str(entry.tool_use_result)

        return ""

    def _export_markdown(
        self,
        entries: list[JSONLEntry],
        file_path: Path,
        *,
        threading_enabled: bool,
    ) -> bool:
        """Export as Markdown format."""
        with file_path.open("w", encoding="utf-8") as f:
            f.write("# CCMonitor Conversation Export\n\n")
            f.write(
                f"**Export Date:** "
                f"{datetime.now(tz=UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n",
            )
            f.write(f"**Total Messages:** {len(entries)}\n\n")
            f.write("---\n\n")

            if threading_enabled:
                self._write_threaded_markdown(entries, f)
            else:
                self._write_linear_markdown(entries, f)

        return True

    def _write_linear_markdown(
        self,
        entries: list[JSONLEntry],
        file_handle: TextIO,
    ) -> None:
        """Write entries in linear order."""
        for i, entry in enumerate(entries, 1):
            timestamp = entry.timestamp or "Unknown"
            msg_type = entry.type.value.title()

            file_handle.write(f"## {i}. {msg_type} Message\n\n")
            file_handle.write(f"**Time:** {timestamp}\n\n")

            if entry.session_id:
                file_handle.write(f"**Session:** {entry.session_id}\n\n")

            content = self._extract_content_for_csv(entry)
            if content:
                file_handle.write(f"{content}\n\n")

            file_handle.write("---\n\n")

    def _write_threaded_markdown(
        self,
        entries: list[JSONLEntry],
        file_handle: TextIO,
    ) -> None:
        """Write entries grouped by session/thread."""
        sessions = self._group_entries_by_session(entries)
        self._write_session_groups(sessions, file_handle)

    def _group_entries_by_session(
        self,
        entries: list[JSONLEntry],
    ) -> dict[str, list[JSONLEntry]]:
        """Group entries by session ID."""
        sessions: dict[str, list[JSONLEntry]] = {}
        for entry in entries:
            session_id = entry.session_id or "unknown"
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(entry)
        return sessions

    def _write_session_groups(
        self,
        sessions: dict[str, list[JSONLEntry]],
        file_handle: TextIO,
    ) -> None:
        """Write grouped sessions to markdown file."""
        for session_id, session_entries in sessions.items():
            file_handle.write(f"## Session: {session_id}\n\n")
            self._write_session_entries(session_entries, file_handle)
            file_handle.write("---\n\n")

    def _write_session_entries(
        self,
        session_entries: list[JSONLEntry],
        file_handle: TextIO,
    ) -> None:
        """Write entries for a single session."""
        for entry in session_entries:
            msg_type = entry.type.value.title()
            timestamp = entry.timestamp or "Unknown"

            file_handle.write(f"### {msg_type} ({timestamp})\n\n")

            content = self._extract_content_for_csv(entry)
            if content:
                file_handle.write(f"{content}\n\n")

    def _export_text(
        self,
        entries: list[JSONLEntry],
        file_path: Path,
    ) -> bool:
        """Export as plain text format."""
        with file_path.open("w", encoding="utf-8") as f:
            f.write("CCMonitor Conversation Export\n")
            f.write("=" * 40 + "\n\n")
            f.write(
                f"Export Date: "
                f"{datetime.now(tz=UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}\n",
            )
            f.write(f"Total Messages: {len(entries)}\n\n")

            for i, entry in enumerate(entries, 1):
                timestamp = entry.timestamp or "Unknown"
                msg_type = entry.type.value.upper()

                f.write(f"[{i}] {msg_type} - {timestamp}\n")
                if entry.session_id:
                    f.write(f"Session: {entry.session_id}\n")

                content = self._extract_content_for_csv(entry)
                if content:
                    f.write(f"{content}\n")

                f.write("-" * 40 + "\n\n")

        return True

    def _export_statistics(
        self,
        statistics_metrics: dict[str, Any],
        file_path: Path,
    ) -> bool:
        """Export statistics report as JSON."""
        report = {
            "export_info": {
                "timestamp": datetime.now(tz=UTC).isoformat(),
                "report_type": "statistics_summary",
                "version": "1.0",
            },
            "statistics": statistics_metrics,
        }

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        return True
