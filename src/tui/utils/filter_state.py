"""Filter state management for CCMonitor TUI application."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, validator

from src.services.models import JSONLEntry, MessageType

if TYPE_CHECKING:
    from typing import Any

# Constants
MAX_PRESET_NAME_LENGTH = 50
DEFAULT_SUMMARY_PARTS_LIMIT = 3


@dataclass(frozen=True)
class TimeRange:
    """Immutable time range for filtering."""

    start: datetime | None = None
    end: datetime | None = None
    relative: str | None = None  # "1h", "1d", "1w", "custom"

    @classmethod
    def last_hour(cls) -> TimeRange:
        """Create time range for last hour."""
        return cls(relative="1h")

    @classmethod
    def last_day(cls) -> TimeRange:
        """Create time range for last day."""
        return cls(relative="1d")

    @classmethod
    def last_week(cls) -> TimeRange:
        """Create time range for last week."""
        return cls(relative="1w")

    @classmethod
    def custom(cls, start: datetime | None, end: datetime | None) -> TimeRange:
        """Create custom time range."""
        return cls(start=start, end=end, relative="custom")

    def get_actual_range(self) -> tuple[datetime | None, datetime | None]:
        """Get actual start/end times based on relative or absolute values."""
        if self.relative == "1h":
            now = datetime.now(tz=UTC)
            return now - timedelta(hours=1), now
        if self.relative == "1d":
            now = datetime.now(tz=UTC)
            return now - timedelta(days=1), now
        if self.relative == "1w":
            now = datetime.now(tz=UTC)
            return now - timedelta(weeks=1), now
        return self.start, self.end


@dataclass(frozen=True)
class FilterCriteria:
    """Immutable filter criteria for message filtering."""

    # Message type filters
    message_types: frozenset[MessageType] = field(
        default_factory=lambda: frozenset(MessageType),
    )

    # Time range filter
    time_range: TimeRange = field(default_factory=TimeRange)

    # Content search
    search_query: str = ""
    search_regex: bool = False
    search_case_sensitive: bool = False

    # Project-specific filters
    project_path: str | None = None
    session_id: str | None = None
    git_branch: str | None = None

    # Advanced filters
    min_message_count: int = 0
    has_tool_usage: bool | None = None
    has_errors: bool | None = None

    def is_empty(self) -> bool:
        """Check if filter has any active criteria."""
        return (
            len(self.message_types) == len(MessageType)
            and self.time_range.relative is None
            and self.time_range.start is None
            and self.time_range.end is None
            and not self.search_query
            and self.project_path is None
            and self.session_id is None
            and self.git_branch is None
            and self.min_message_count == 0
            and self.has_tool_usage is None
            and self.has_errors is None
        )

    def get_summary(self) -> str:
        """Get human-readable filter summary."""
        if self.is_empty():
            return "No filters active"

        parts = []
        parts.extend(self._get_message_type_parts())
        parts.extend(self._get_time_range_parts())
        parts.extend(self._get_search_parts())
        parts.extend(self._get_project_parts())

        return " | ".join(parts[:DEFAULT_SUMMARY_PARTS_LIMIT])

    def _get_message_type_parts(self) -> list[str]:
        """Get message type summary parts."""
        if len(self.message_types) < len(MessageType):
            type_names = [t.value for t in self.message_types]
            return [f"Types: {', '.join(type_names)}"]
        return []

    def _get_time_range_parts(self) -> list[str]:
        """Get time range summary parts."""
        if self.time_range.relative:
            time_map = {"1h": "Last hour", "1d": "Last day", "1w": "Last week"}
            return [time_map.get(self.time_range.relative, "Custom time")]
        if self.time_range.start or self.time_range.end:
            return ["Custom time range"]
        return []

    def _get_search_parts(self) -> list[str]:
        """Get search summary parts."""
        if self.search_query:
            search_type = "Regex" if self.search_regex else "Text"
            return [f'{search_type}: "{self.search_query}"']
        return []

    def _get_project_parts(self) -> list[str]:
        """Get project filter summary parts."""
        parts = []
        if self.project_path:
            parts.append(f"Project: {self.project_path}")
        if self.session_id:
            parts.append(f"Session: {self.session_id[:8]}...")
        if self.git_branch:
            parts.append(f"Branch: {self.git_branch}")
        return parts


class FilterPreset(BaseModel):
    """Saved filter preset."""

    name: str
    description: str = ""
    criteria: FilterCriteria
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    last_used: datetime | None = None

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True

    @validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate preset name."""
        if not v.strip():
            msg = "Preset name cannot be empty"
            raise ValueError(msg)
        if len(v) > MAX_PRESET_NAME_LENGTH:
            msg = "Preset name too long"
            raise ValueError(msg)
        return v.strip()


class FilterEngine:
    """Engine for applying filters to message entries."""

    def __init__(self) -> None:
        """Initialize filter engine."""
        self._compiled_regex: re.Pattern[str] | None = None
        self._last_search_query = ""
        self._last_search_regex = False

    def apply_filter(
        self,
        entries: list[JSONLEntry],
        criteria: FilterCriteria,
    ) -> list[JSONLEntry]:
        """Apply filter criteria to entries."""
        if criteria.is_empty():
            return entries

        filtered = entries
        filtered = self._filter_by_message_types(filtered, criteria)
        filtered = self._filter_by_time_range(filtered, criteria)
        filtered = self._filter_by_content_search(filtered, criteria)
        filtered = self._filter_by_project_criteria(filtered, criteria)
        return self._filter_by_advanced_criteria(filtered, criteria)

    def _filter_by_message_types(
        self,
        entries: list[JSONLEntry],
        criteria: FilterCriteria,
    ) -> list[JSONLEntry]:
        """Filter entries by message types."""
        if len(criteria.message_types) < len(MessageType):
            return [e for e in entries if e.type in criteria.message_types]
        return entries

    def _filter_by_time_range(
        self,
        entries: list[JSONLEntry],
        criteria: FilterCriteria,
    ) -> list[JSONLEntry]:
        """Filter entries by time range."""
        start_time, end_time = criteria.time_range.get_actual_range()
        if not start_time and not end_time:
            return entries

        return [
            entry
            for entry in entries
            if self._entry_matches_time_range(entry, start_time, end_time)
        ]

    def _entry_matches_time_range(
        self,
        entry: JSONLEntry,
        start_time: datetime | None,
        end_time: datetime | None,
    ) -> bool:
        """Check if entry matches time range criteria."""
        if not entry.timestamp:
            return (
                not start_time
            )  # Include entries with no timestamp if no start constraint

        try:
            entry_time = datetime.fromisoformat(entry.timestamp)
            if start_time and entry_time < start_time:
                return False
        except (ValueError, AttributeError):
            return not start_time
        else:
            return not (end_time and entry_time > end_time)

    def _filter_by_content_search(
        self,
        entries: list[JSONLEntry],
        criteria: FilterCriteria,
    ) -> list[JSONLEntry]:
        """Filter entries by content search."""
        if not criteria.search_query:
            return entries

        search_config = SearchConfig(
            query=criteria.search_query,
            use_regex=criteria.search_regex,
            case_sensitive=criteria.search_case_sensitive,
        )

        if not self._prepare_regex_if_needed(search_config):
            return []  # Invalid regex

        return [
            entry
            for entry in entries
            if self._entry_matches_search(entry, search_config)
        ]

    def _prepare_regex_if_needed(self, config: SearchConfig) -> bool:
        """Prepare regex pattern if needed. Returns False for invalid regex."""
        if not config.use_regex:
            return True

        if (
            self._compiled_regex is None
            or config.query != self._last_search_query
            or config.use_regex != self._last_search_regex
        ):
            try:
                flags = 0 if config.case_sensitive else re.IGNORECASE
                self._compiled_regex = re.compile(config.query, flags)
                self._last_search_query = config.query
                self._last_search_regex = config.use_regex
            except re.error:
                return False
        return True

    def _entry_matches_search(
        self,
        entry: JSONLEntry,
        config: SearchConfig,
    ) -> bool:
        """Check if entry matches search criteria."""
        content = self._extract_searchable_content(entry)
        return self._content_matches_search(content, config)

    def _extract_searchable_content(self, entry: JSONLEntry) -> str:
        """Extract all searchable content from an entry."""
        content_parts = []
        content_parts.extend(self._extract_message_content(entry))
        content_parts.extend(self._extract_tool_content(entry))
        content_parts.extend(self._extract_metadata(entry))
        return " ".join(content_parts)

    def _extract_message_content(self, entry: JSONLEntry) -> list[str]:
        """Extract content from message field."""
        if not entry.message:
            return []

        parts = []
        if isinstance(entry.message.content, str):
            parts.append(entry.message.content)
        elif isinstance(entry.message.content, list):
            parts.extend(
                self._extract_from_content_list(entry.message.content),
            )

        if entry.message.tool:
            parts.append(entry.message.tool)

        return parts

    def _extract_from_content_list(self, content_list: list[Any]) -> list[str]:
        """Extract text from content list."""
        return [
            str(getattr(item, "text", ""))
            for item in content_list
            if hasattr(item, "text")
        ]

    def _extract_tool_content(self, entry: JSONLEntry) -> list[str]:
        """Extract content from tool results."""
        if not entry.tool_use_result:
            return []

        if isinstance(entry.tool_use_result, str):
            return [entry.tool_use_result]
        if isinstance(entry.tool_use_result, dict):
            return [str(entry.tool_use_result)]
        return []

    def _extract_metadata(self, entry: JSONLEntry) -> list[str]:
        """Extract metadata fields."""
        parts = []
        if entry.session_id:
            parts.append(entry.session_id)
        if entry.git_branch:
            parts.append(entry.git_branch)
        return parts

    def _content_matches_search(
        self,
        content: str,
        config: SearchConfig,
    ) -> bool:
        """Check if content matches search configuration."""
        if config.use_regex and self._compiled_regex:
            return bool(self._compiled_regex.search(content))

        search_content = content if config.case_sensitive else content.lower()
        search_query = (
            config.query if config.case_sensitive else config.query.lower()
        )
        return search_query in search_content

    def _filter_by_project_criteria(
        self,
        entries: list[JSONLEntry],
        criteria: FilterCriteria,
    ) -> list[JSONLEntry]:
        """Filter entries by project-specific criteria."""
        filtered = entries

        if criteria.session_id:
            filtered = [
                e for e in filtered if e.session_id == criteria.session_id
            ]

        if criteria.git_branch:
            filtered = [
                e for e in filtered if e.git_branch == criteria.git_branch
            ]

        return filtered

    def _filter_by_advanced_criteria(
        self,
        entries: list[JSONLEntry],
        criteria: FilterCriteria,
    ) -> list[JSONLEntry]:
        """Filter entries by advanced criteria."""
        filtered = entries

        if criteria.has_tool_usage is not None:
            filtered = self._filter_by_tool_usage(
                filtered,
                criteria.has_tool_usage,
            )

        if criteria.has_errors is not None:
            filtered = self._filter_by_errors(filtered, criteria.has_errors)

        return filtered

    def _filter_by_tool_usage(
        self,
        entries: list[JSONLEntry],
        has_tool_usage: bool,  # noqa: FBT001
    ) -> list[JSONLEntry]:
        """Filter entries based on tool usage."""
        if has_tool_usage:
            return [
                e
                for e in entries
                if e.type in [MessageType.TOOL_CALL, MessageType.TOOL_USE]
                or e.tool_use_result is not None
            ]
        return [
            e
            for e in entries
            if e.type not in [MessageType.TOOL_CALL, MessageType.TOOL_USE]
            and e.tool_use_result is None
        ]

    def _filter_by_errors(
        self,
        entries: list[JSONLEntry],
        has_errors: bool,  # noqa: FBT001
    ) -> list[JSONLEntry]:
        """Filter entries based on error presence."""
        if has_errors:
            return [e for e in entries if self._entry_has_error(e)]
        return [e for e in entries if not self._entry_has_error(e)]

    def _entry_has_error(self, entry: JSONLEntry) -> bool:
        """Check if entry has error information."""
        if isinstance(entry.tool_use_result, dict):
            is_error = entry.tool_use_result.get("is_error", False)
            return bool(is_error)
        if isinstance(entry.tool_use_result, str):
            return "error" in entry.tool_use_result.lower()
        return False


@dataclass
class SearchConfig:
    """Configuration for content search."""

    query: str
    use_regex: bool
    case_sensitive: bool


class FilterStateManager:
    """Manager for filter state and presets."""

    def __init__(self) -> None:
        """Initialize filter state manager."""
        self.current_criteria = FilterCriteria()
        self.presets: list[FilterPreset] = []
        self.filter_engine = FilterEngine()
        self._load_default_presets()

    def _load_default_presets(self) -> None:
        """Load default filter presets."""
        default_presets = [
            {
                "name": "Recent Activity",
                "description": "Messages from the last hour",
                "criteria": FilterCriteria(time_range=TimeRange.last_hour()),
            },
            {
                "name": "User Messages",
                "description": "Only user messages",
                "criteria": FilterCriteria(
                    message_types=frozenset([MessageType.USER]),
                ),
            },
            {
                "name": "Tool Usage",
                "description": "Tool calls and results",
                "criteria": FilterCriteria(
                    message_types=frozenset(
                        [
                            MessageType.TOOL_CALL,
                            MessageType.TOOL_USE,
                            MessageType.TOOL_RESULT,
                        ],
                    ),
                ),
            },
            {
                "name": "Errors Only",
                "description": "Messages with errors",
                "criteria": FilterCriteria(has_errors=True),
            },
        ]

        for preset_data in default_presets:
            preset = FilterPreset(
                name=str(preset_data["name"]),
                description=str(preset_data["description"]),
                criteria=preset_data["criteria"],  # type: ignore[arg-type]
            )
            self.presets.append(preset)

    def update_criteria(self, **kwargs: dict[str, Any]) -> FilterCriteria:
        """Update current filter criteria."""
        current_dict = {
            "message_types": self.current_criteria.message_types,
            "time_range": self.current_criteria.time_range,
            "search_query": self.current_criteria.search_query,
            "search_regex": self.current_criteria.search_regex,
            "search_case_sensitive": (
                self.current_criteria.search_case_sensitive
            ),
            "project_path": self.current_criteria.project_path,
            "session_id": self.current_criteria.session_id,
            "git_branch": self.current_criteria.git_branch,
            "min_message_count": self.current_criteria.min_message_count,
            "has_tool_usage": self.current_criteria.has_tool_usage,
            "has_errors": self.current_criteria.has_errors,
        }
        current_dict.update(kwargs)
        self.current_criteria = FilterCriteria(**current_dict)  # type: ignore[arg-type]
        return self.current_criteria

    def clear_filters(self) -> FilterCriteria:
        """Clear all filters."""
        self.current_criteria = FilterCriteria()
        return self.current_criteria

    def apply_preset(self, preset_name: str) -> FilterCriteria | None:
        """Apply a named preset."""
        for preset in self.presets:
            if preset.name == preset_name:
                self.current_criteria = preset.criteria
                preset.last_used = datetime.now(tz=UTC)
                return self.current_criteria
        return None

    def save_preset(self, name: str, description: str = "") -> bool:
        """Save current criteria as a preset."""
        try:
            preset = FilterPreset(
                name=name,
                description=description,
                criteria=self.current_criteria,
            )
            # Remove existing preset with same name
            self.presets = [p for p in self.presets if p.name != name]
            self.presets.append(preset)
        except ValueError:
            return False
        else:
            return True

    def delete_preset(self, name: str) -> bool:
        """Delete a preset by name."""
        original_count = len(self.presets)
        self.presets = [p for p in self.presets if p.name != name]
        return len(self.presets) < original_count

    def get_preset_names(self) -> list[str]:
        """Get list of all preset names."""
        return [p.name for p in self.presets]

    def apply_filter(self, entries: list[JSONLEntry]) -> list[JSONLEntry]:
        """Apply current filter criteria to entries."""
        return self.filter_engine.apply_filter(entries, self.current_criteria)
