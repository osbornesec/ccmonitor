"""Message categorization system for Claude Code activity logs."""

from __future__ import annotations

import contextlib
import re
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .models import JSONLEntry, MessageType

# Time constants
SECONDS_IN_HOUR = 3600
SECONDS_IN_MINUTE = 60
MIN_TIMESTAMPS_FOR_DURATION = 2


class MessageCategory(str, Enum):
    """Categories for different types of messages."""

    USER_INPUT = "user_input"
    AI_RESPONSE = "ai_response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    SYSTEM_EVENT = "system_event"
    META_INFORMATION = "meta_information"


class MessagePriority(str, Enum):
    """Priority levels for messages."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CategorizedMessage(BaseModel):
    """A categorized message with display information."""

    # Original entry
    entry: JSONLEntry

    # Categorization
    category: MessageCategory
    priority: MessagePriority

    # Display information
    summary: str
    display_text: str
    timestamp_relative: str

    # Metadata
    metadata: dict[str, Any]
    has_errors: bool = False
    is_truncated: bool = False

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class ToolCallGroup(BaseModel):
    """A grouped tool call with its result."""

    tool_call: JSONLEntry
    tool_result: JSONLEntry | None = None
    tool_name: str
    success: bool = True
    execution_time: float = 0.0
    summary: str = ""

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class MessageThread(BaseModel):
    """A thread of related messages."""

    session_id: str
    messages: list[JSONLEntry]
    start_time: datetime
    end_time: datetime | None = None

    # Computed properties
    user_message_count: int = 0
    assistant_message_count: int = 0
    tool_call_count: int = 0
    duration: float = 0.0

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class MessageCategorizer:
    """Categorizes and formats messages for display."""

    def __init__(self, max_display_length: int = 100) -> None:
        """Initialize the message categorizer.

        Args:
            max_display_length: Maximum length for display text

        """
        self.max_display_length = max_display_length

        # Tool operation mappings with enhanced descriptions
        self.tool_operation_map = {
            "Read": {"operation": "read", "description": "Reading file"},
            "Write": {"operation": "write", "description": "Writing file"},
            "Edit": {"operation": "edit", "description": "Editing file"},
            "MultiEdit": {
                "operation": "multi_edit",
                "description": "Making multiple edits",
            },
            "Bash": {"operation": "bash", "description": "Running command"},
            "Grep": {"operation": "grep", "description": "Searching content"},
            "Glob": {"operation": "glob", "description": "Finding files"},
            "LS": {"operation": "list", "description": "Listing directory"},
            "WebSearch": {
                "operation": "web_search",
                "description": "Searching web",
            },
            "WebFetch": {
                "operation": "web_fetch",
                "description": "Fetching web page",
            },
            "NotebookEdit": {
                "operation": "notebook_edit",
                "description": "Editing notebook",
            },
            "TodoWrite": {
                "operation": "todo_write",
                "description": "Updating todo list",
            },
            "Task": {
                "operation": "task",
                "description": "Running automated task",
            },
            "KillBash": {
                "operation": "kill_bash",
                "description": "Stopping command",
            },
            "BashOutput": {
                "operation": "bash_output",
                "description": "Reading command output",
            },
        }

    def categorize_message(self, entry: JSONLEntry) -> CategorizedMessage:
        """Categorize a single message entry.

        Args:
            entry: The JSONL entry to categorize

        Returns:
            CategorizedMessage with categorization and display info

        """
        # Determine category and priority
        category = self._determine_category(entry)
        priority = self._determine_priority(entry, category)

        # Generate summary and display text
        summary = self._generate_summary(entry, category)
        display_text = self._generate_display_text(entry)

        # Format relative timestamp
        timestamp_relative = self._format_relative_timestamp(
            entry.timestamp or "",
        )

        # Extract metadata
        metadata = self._extract_metadata(entry)

        # Check for errors
        has_errors = self._check_for_errors(entry)

        # Check if display text was truncated
        is_truncated = len(display_text) > self.max_display_length
        if is_truncated:
            display_text = display_text[: self.max_display_length] + "..."

        return CategorizedMessage(
            entry=entry,
            category=category,
            priority=priority,
            summary=summary,
            display_text=display_text,
            timestamp_relative=timestamp_relative,
            metadata=metadata,
            has_errors=has_errors,
            is_truncated=is_truncated,
        )

    def _determine_category(self, entry: JSONLEntry) -> MessageCategory:
        """Determine the category of a message."""
        # Use a mapping for cleaner logic
        type_mapping = {
            MessageType.USER: MessageCategory.USER_INPUT,
            MessageType.ASSISTANT: MessageCategory.AI_RESPONSE,
            MessageType.SYSTEM: MessageCategory.SYSTEM_EVENT,
        }

        # Check direct mappings first
        if entry.type in type_mapping:
            return type_mapping[entry.type]

        # Check tool-related types
        if entry.type in [MessageType.TOOL_CALL, MessageType.TOOL_USE]:
            return MessageCategory.TOOL_CALL
        if entry.type in [
            MessageType.TOOL_RESULT,
            MessageType.TOOL_USE_RESULT,
        ]:
            return MessageCategory.TOOL_RESULT

        # Check meta information
        if entry.type == MessageType.META or entry.git_branch:
            return MessageCategory.META_INFORMATION

        # Default fallback
        return MessageCategory.SYSTEM_EVENT

    def _determine_priority(
        self,
        entry: JSONLEntry,
        category: MessageCategory,
    ) -> MessagePriority:
        """Determine the priority of a message."""
        if category in [
            MessageCategory.USER_INPUT,
            MessageCategory.AI_RESPONSE,
        ]:
            return MessagePriority.HIGH
        if category == MessageCategory.TOOL_CALL:
            return MessagePriority.MEDIUM
        if category == MessageCategory.TOOL_RESULT:
            # Higher priority if there's an error
            if (
                entry.tool_use_result
                and hasattr(entry.tool_use_result, "is_error")
                and entry.tool_use_result.is_error
            ):
                return MessagePriority.HIGH
            return MessagePriority.LOW
        return MessagePriority.LOW

    def _generate_summary(
        self,
        entry: JSONLEntry,
        category: MessageCategory,
    ) -> str:
        """Generate a plain English summary of the message."""
        summary_generators = {
            MessageCategory.USER_INPUT: self._generate_user_input_summary,
            MessageCategory.AI_RESPONSE: self._generate_ai_response_summary,
            MessageCategory.TOOL_CALL: self._generate_tool_call_summary,
            MessageCategory.TOOL_RESULT: self._generate_tool_result_summary,
            MessageCategory.SYSTEM_EVENT: self._generate_system_event_summary,
            MessageCategory.META_INFORMATION: self._generate_meta_info_summary,
        }

        generator = summary_generators.get(category)
        if generator:
            return generator(entry)
        return "Malformed message"

    def _generate_user_input_summary(self, entry: JSONLEntry) -> str:
        """Generate summary for user input messages."""
        if not (entry.message and isinstance(entry.message.content, str)):
            return "User input"

        content = entry.message.content.lower()

        # Define keyword patterns for different intents
        intent_patterns = {
            "User asks for help": ["help", "can you", "please"],
            "User requests creation": ["create", "write", "make"],
            "User reports issue": ["fix", "error", "bug"],
            "User asks for explanation": ["explain", "what", "how"],
        }

        # Check each intent pattern
        for summary, keywords in intent_patterns.items():
            if any(word in content for word in keywords):
                return summary

        return "User message"

    def _generate_ai_response_summary(
        self,
        entry: JSONLEntry,  # noqa: ARG002
    ) -> str:
        """Generate summary for AI response messages."""
        return "Claude responds"

    def _generate_tool_call_summary(self, entry: JSONLEntry) -> str:
        """Generate summary for tool call messages."""
        if not (entry.message and entry.message.tool):
            return "Tool operation"

        tool_name = entry.message.tool
        if tool_name in self.tool_operation_map:
            return self.tool_operation_map[tool_name]["description"]
        return f"Tool call: {tool_name}"

    def _generate_tool_result_summary(self, entry: JSONLEntry) -> str:
        """Generate summary for tool result messages."""
        if not entry.tool_use_result:
            return "Tool result"

        # Check for error first
        if (
            hasattr(entry.tool_use_result, "is_error")
            and entry.tool_use_result.is_error
        ):
            return "Tool operation failed"

        # Get tool name and generate success message
        tool_name = "Unknown"
        if hasattr(entry.tool_use_result, "tool_name"):
            tool_name = entry.tool_use_result.tool_name

        # Map tool names to success messages
        success_messages = {
            "Read": "File read successfully",
            "Write": "File written successfully",
            "Edit": "File edited successfully",
            "Bash": "Command completed",
        }

        return success_messages.get(tool_name, f"{tool_name} completed")

    def _generate_system_event_summary(self, entry: JSONLEntry) -> str:
        """Generate summary for system event messages."""
        if not (entry.message and isinstance(entry.message.content, str)):
            return "System message"

        content = entry.message.content.lower()
        if "session" in content:
            return "Session started"
        if "error" in content:
            return "System error"
        return "System event"

    def _generate_meta_info_summary(self, entry: JSONLEntry) -> str:
        """Generate summary for meta information messages."""
        if entry.git_branch:
            return f"Git branch: {entry.git_branch}"
        if entry.cwd:
            return f"Directory: {Path(entry.cwd).name}"
        return "Metadata update"

    def _generate_display_text(self, entry: JSONLEntry) -> str:
        """Generate display text for the message."""
        # Try message content first
        message_text = self._extract_message_content(entry)
        if message_text:
            return message_text

        # Try tool result output
        tool_output = self._extract_tool_output(entry)
        if tool_output:
            return tool_output

        # Try tool parameters
        tool_params = self._extract_tool_parameters(entry)
        if tool_params:
            return tool_params

        # Default fallback
        return f"[{entry.type}] message"

    def _extract_message_content(self, entry: JSONLEntry) -> str | None:
        """Extract text content from message."""
        if not entry.message:
            return None

        if isinstance(entry.message.content, str):
            return entry.message.content

        if isinstance(entry.message.content, list):
            return self._extract_text_from_content_list(entry.message.content)

        return None

    def _extract_text_from_content_list(self, content_list: list) -> str:
        """Extract text from a list of content items."""
        text_parts = []
        for item in content_list:
            if hasattr(item, "text"):
                text_parts.append(item.text)
            elif isinstance(item, dict) and "text" in item:
                text_parts.append(item["text"])
            else:
                text_parts.append(str(item))
        return " ".join(text_parts)

    def _extract_tool_output(self, entry: JSONLEntry) -> str | None:
        """Extract output from tool use result."""
        if not (
            entry.tool_use_result
            and hasattr(entry.tool_use_result, "output")
            and entry.tool_use_result.output
        ):
            return None

        output = entry.tool_use_result.output
        if isinstance(output, str):
            return output
        return str(output)

    def _extract_tool_parameters(self, entry: JSONLEntry) -> str | None:
        """Extract parameters from tool call message."""
        if not (entry.message and entry.message.parameters):
            return None

        params = [
            f"{key}={value}" for key, value in entry.message.parameters.items()
        ]
        return f"Parameters: {', '.join(params)}"

    def _format_relative_timestamp(self, timestamp: str) -> str:
        """Format timestamp as relative time."""
        try:
            dt = datetime.fromisoformat(timestamp)
            now = datetime.now(UTC)
            diff = now - dt
        except (ValueError, TypeError):
            return timestamp
        else:
            return self._format_time_difference(diff)

    def _format_time_difference(self, diff: timedelta) -> str:
        """Format time difference as relative string."""
        if diff.days > 0:
            return f"{diff.days} days ago"
        if diff.seconds > SECONDS_IN_HOUR:
            hours = diff.seconds // SECONDS_IN_HOUR
            return f"{hours} hours ago"
        if diff.seconds > SECONDS_IN_MINUTE:
            minutes = diff.seconds // SECONDS_IN_MINUTE
            return f"{minutes} minutes ago"
        return "Just now"

    def _extract_metadata(self, entry: JSONLEntry) -> dict[str, Any]:
        """Extract metadata from the entry."""
        metadata: dict[str, Any] = {}

        # Extract different types of metadata
        self._add_basic_metadata(metadata, entry)
        self._add_tool_metadata(metadata, entry)
        self._add_context_metadata(metadata, entry)

        return metadata

    def _add_basic_metadata(
        self,
        metadata: dict[str, Any],
        entry: JSONLEntry,
    ) -> None:
        """Add basic metadata like session and UUID info."""
        if entry.session_id:
            metadata["session_id"] = entry.session_id
        if entry.parent_uuid:
            metadata["parent_uuid"] = entry.parent_uuid

    def _add_tool_metadata(
        self,
        metadata: dict[str, Any],
        entry: JSONLEntry,
    ) -> None:
        """Add tool-related metadata."""
        if not (entry.message and entry.message.tool):
            return

        metadata["tool_name"] = entry.message.tool

        if entry.message.parameters:
            self._extract_tool_parameters_metadata(
                metadata,
                entry.message.parameters,
            )

    def _extract_tool_parameters_metadata(
        self,
        metadata: dict[str, Any],
        parameters: dict[str, Any],
    ) -> None:
        """Extract specific parameters from tool calls."""
        # Extract file paths for easy access
        if "file_path" in parameters:
            metadata["file_path"] = parameters["file_path"]
        if "query" in parameters:
            metadata["search_query"] = parameters["query"]

    def _add_context_metadata(
        self,
        metadata: dict[str, Any],
        entry: JSONLEntry,
    ) -> None:
        """Add contextual metadata like working directory and git info."""
        if entry.cwd:
            metadata["working_directory"] = entry.cwd
        if entry.git_branch:
            metadata["git_branch"] = entry.git_branch
        if entry.version:
            metadata["version"] = entry.version

    def _check_for_errors(self, entry: JSONLEntry) -> bool:
        """Check if the entry represents an error condition."""
        # Tool result errors
        if (
            entry.tool_use_result
            and hasattr(entry.tool_use_result, "is_error")
            and entry.tool_use_result.is_error
        ):
            return True

        # Malformed entries
        if not entry.message and entry.type in [
            MessageType.USER,
            MessageType.ASSISTANT,
            MessageType.SYSTEM,
        ]:
            return True

        # Invalid timestamps
        if entry.timestamp:
            try:
                datetime.fromisoformat(entry.timestamp)
            except (ValueError, TypeError):
                return True

        return False

    def categorize_batch(
        self,
        entries: list[JSONLEntry],
    ) -> list[CategorizedMessage]:
        """Categorize a batch of messages."""
        return [self.categorize_message(entry) for entry in entries]

    def group_tool_operations(
        self,
        entries: list[JSONLEntry],
    ) -> list[ToolCallGroup]:
        """Group tool calls with their results."""
        # Collect tool calls first
        tool_calls = self._collect_tool_calls(entries)

        # Match tool calls with their results
        return self._match_calls_with_results(entries, tool_calls)

    def _collect_tool_calls(
        self,
        entries: list[JSONLEntry],
    ) -> dict[str, JSONLEntry]:
        """Collect all tool call entries indexed by UUID."""
        tool_calls = {}
        for entry in entries:
            if (
                entry.type in [MessageType.TOOL_CALL, MessageType.TOOL_USE]
                and entry.uuid  # Ensure UUID exists
            ):
                tool_calls[entry.uuid] = entry
        return tool_calls

    def _match_calls_with_results(
        self,
        entries: list[JSONLEntry],
        tool_calls: dict[str, JSONLEntry],
    ) -> list[ToolCallGroup]:
        """Match tool results with their corresponding calls."""
        groups = []

        for entry in entries:
            if self._is_tool_result_entry(entry):
                group = self._create_tool_group(
                    entry,
                    tool_calls,
                )
                if group:
                    groups.append(group)

        return groups

    def _is_tool_result_entry(self, entry: JSONLEntry) -> bool:
        """Check if entry is a tool result."""
        return entry.type in [
            MessageType.TOOL_RESULT,
            MessageType.TOOL_USE_RESULT,
        ]

    def _create_tool_group(
        self,
        result_entry: JSONLEntry,
        tool_calls: dict[str, JSONLEntry],
    ) -> ToolCallGroup | None:
        """Create a tool call group from result entry and matching call."""
        call_id = result_entry.parent_uuid or result_entry.tool_use_id
        if not call_id or call_id not in tool_calls:
            return None

        tool_call = tool_calls[call_id]

        # Calculate execution metrics
        exec_time = self._calculate_execution_time(tool_call, result_entry)
        tool_name = self._determine_tool_name(tool_call, result_entry)
        success = self._check_tool_success(result_entry)

        # Generate summary
        summary = self._generate_tool_group_summary(
            tool_call,
            tool_name,
            success=success,
        )

        return ToolCallGroup(
            tool_call=tool_call,
            tool_result=result_entry,
            tool_name=tool_name,
            success=success,
            execution_time=exec_time,
            summary=summary,
        )

    def _calculate_execution_time(
        self,
        tool_call: JSONLEntry,
        result_entry: JSONLEntry,
    ) -> float:
        """Calculate execution time between tool call and result."""
        try:
            if not (tool_call.timestamp and result_entry.timestamp):
                return 0.0

            call_time = datetime.fromisoformat(tool_call.timestamp)
            result_time = datetime.fromisoformat(result_entry.timestamp)
            return (result_time - call_time).total_seconds()
        except (ValueError, TypeError):
            return 0.0

    def _determine_tool_name(
        self,
        tool_call: JSONLEntry,
        result_entry: JSONLEntry,
    ) -> str:
        """Determine the tool name from call or result entry."""
        # Try tool call message first
        if tool_call.message and tool_call.message.tool:
            return tool_call.message.tool

        # Try result entry tool name
        if result_entry.tool_use_result and hasattr(
            result_entry.tool_use_result,
            "tool_name",
        ):
            return result_entry.tool_use_result.tool_name

        return "Unknown"

    def _check_tool_success(self, result_entry: JSONLEntry) -> bool:
        """Check if tool execution was successful."""
        if not result_entry.tool_use_result:
            return True

        return not (
            hasattr(result_entry.tool_use_result, "is_error")
            and result_entry.tool_use_result.is_error
        )

    def _generate_tool_group_summary(
        self,
        tool_call: JSONLEntry,
        tool_name: str,
        *,
        success: bool,
    ) -> str:
        """Generate summary for a tool call group."""
        if not success:
            return f"{tool_name} operation failed"

        # Generate operation-specific summaries
        return self._generate_success_summary(tool_call, tool_name)

    def _generate_success_summary(
        self,
        tool_call: JSONLEntry,
        tool_name: str,
    ) -> str:
        """Generate summary for successful tool operations."""
        # File operation tools
        file_tools = {"Read": "Reading", "Write": "Writing", "Edit": "Editing"}
        if tool_name in file_tools:
            return self._generate_file_operation_summary(
                tool_call,
                file_tools[tool_name],
            )

        # Special cases
        if tool_name == "Bash":
            return "Command execution"

        # Default fallback
        return f"{tool_name} operation"

    def _generate_file_operation_summary(
        self,
        tool_call: JSONLEntry,
        operation: str,
    ) -> str:
        """Generate summary for file operations."""
        if not (tool_call.message and tool_call.message.parameters):
            return f"{operation} file"

        file_path = tool_call.message.parameters.get("file_path", "")
        file_name = Path(file_path).name if file_path else "file"
        return f"{operation} {file_name}"

    def create_message_threads(
        self,
        entries: list[JSONLEntry],
    ) -> list[MessageThread]:
        """Create message threads from entries."""
        # Group entries by session ID
        sessions = self._group_entries_by_session(entries)

        # Create thread objects from grouped sessions
        return self._build_threads_from_sessions(sessions)

    def _group_entries_by_session(
        self,
        entries: list[JSONLEntry],
    ) -> dict[str, list[JSONLEntry]]:
        """Group entries by session ID."""
        sessions: dict[str, list[JSONLEntry]] = {}

        for entry in entries:
            session_id = entry.session_id or "default"
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(entry)

        return sessions

    def _build_threads_from_sessions(
        self,
        sessions: dict[str, list[JSONLEntry]],
    ) -> list[MessageThread]:
        """Build MessageThread objects from session groups."""
        threads = []

        for session_id, session_entries in sessions.items():
            if not session_entries:
                continue

            # Sort entries by timestamp
            self._sort_entries_by_timestamp(session_entries)

            # Calculate thread metrics
            metrics = self._calculate_thread_metrics(session_entries)

            # Create thread object
            thread = MessageThread(
                session_id=session_id,
                messages=session_entries,
                start_time=metrics["start_time"],
                end_time=metrics["end_time"],
                user_message_count=metrics["user_count"],
                assistant_message_count=metrics["assistant_count"],
                tool_call_count=metrics["tool_count"],
                duration=metrics["duration"],
            )
            threads.append(thread)

        return threads

    def _sort_entries_by_timestamp(self, entries: list[JSONLEntry]) -> None:
        """Sort entries by timestamp in place."""
        with contextlib.suppress(ValueError, TypeError):
            entries.sort(
                key=lambda e: datetime.fromisoformat(
                    (
                        e.timestamp
                        if e.timestamp
                        else "1970-01-01T00:00:00+00:00"
                    ),
                ),
            )

    def _calculate_thread_metrics(
        self,
        entries: list[JSONLEntry],
    ) -> dict[str, Any]:
        """Calculate metrics for a thread."""
        # Count message types
        user_count = sum(1 for e in entries if e.type == MessageType.USER)
        assistant_count = sum(
            1 for e in entries if e.type == MessageType.ASSISTANT
        )
        tool_count = sum(
            1
            for e in entries
            if e.type in [MessageType.TOOL_CALL, MessageType.TOOL_USE]
        )

        # Calculate duration and timestamps
        duration = 0.0
        start_time = datetime.now(UTC)
        end_time: datetime | None = None

        try:
            timestamps = [
                datetime.fromisoformat(e.timestamp)
                for e in entries
                if e.timestamp
            ]
            if timestamps:
                start_time = min(timestamps)
                end_time = max(timestamps)
                duration = (end_time - start_time).total_seconds()
        except (ValueError, TypeError):
            pass

        return {
            "user_count": user_count,
            "assistant_count": assistant_count,
            "tool_count": tool_count,
            "duration": duration,
            "start_time": start_time,
            "end_time": end_time,
        }

    def extract_code_blocks(self, content: str) -> list[dict[str, str]]:
        """Extract code blocks from message content."""
        code_blocks = []

        # Find markdown code blocks
        pattern = r"```(\w+)?\n(.*?)\n```"
        matches = re.findall(pattern, content, re.DOTALL)

        for language, code in matches:
            code_blocks.append(
                {
                    "language": language or "text",
                    "code": code.strip(),
                },
            )

        return code_blocks

    def detect_file_operation(
        self,
        tool_name: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Detect file operations and extract relevant information."""
        tool_info = self.tool_operation_map.get(
            tool_name,
            {"operation": "unknown"},
        )
        operation_info = {
            "operation_type": tool_info["operation"],
            "tool_name": tool_name,
        }

        # Extract file information
        if "file_path" in parameters:
            file_path = parameters["file_path"]
            operation_info["file_path"] = file_path
            operation_info["file_name"] = Path(file_path).name
            operation_info["file_extension"] = Path(file_path).suffix

        return operation_info

    def calculate_conversation_metrics(
        self,
        entries: list[JSONLEntry],
    ) -> dict[str, Any]:
        """Calculate metrics for a conversation."""
        total_messages = len(entries)
        user_messages = sum(1 for e in entries if e.type == MessageType.USER)
        assistant_messages = sum(
            1 for e in entries if e.type == MessageType.ASSISTANT
        )
        tool_calls = sum(
            1
            for e in entries
            if e.type in [MessageType.TOOL_CALL, MessageType.TOOL_USE]
        )

        # Calculate duration
        duration = 0.0
        messages_per_minute = 0.0

        try:
            timestamps = [
                datetime.fromisoformat(e.timestamp)
                for e in entries
                if e.timestamp
            ]
            if len(timestamps) >= MIN_TIMESTAMPS_FOR_DURATION:
                start_time = min(timestamps)
                end_time = max(timestamps)
                duration = (end_time - start_time).total_seconds()
                if duration > 0:
                    messages_per_minute = (total_messages / duration) * 60
        except (ValueError, TypeError):
            pass

        return {
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "tool_calls": tool_calls,
            "duration": duration,
            "messages_per_minute": messages_per_minute,
        }

    def filter_by_category(
        self,
        categorized: list[CategorizedMessage],
        category: MessageCategory,
    ) -> list[CategorizedMessage]:
        """Filter messages by category."""
        return [msg for msg in categorized if msg.category == category]

    def search_messages(
        self,
        categorized: list[CategorizedMessage],
        query: str,
    ) -> list[CategorizedMessage]:
        """Search within message content."""
        query_lower = query.lower()
        return [
            msg
            for msg in categorized
            if (
                query_lower in msg.display_text.lower()
                or query_lower in msg.summary.lower()
            )
        ]

    def get_statistics(
        self,
        categorized: list[CategorizedMessage],
    ) -> dict[str, Any]:
        """Get categorization statistics."""
        total = len(categorized)

        # Count by category
        by_category: dict[MessageCategory, int] = {}
        for msg in categorized:
            by_category[msg.category] = by_category.get(msg.category, 0) + 1

        # Count by priority
        by_priority: dict[MessagePriority, int] = {}
        for msg in categorized:
            by_priority[msg.priority] = by_priority.get(msg.priority, 0) + 1

        # Error count
        error_count = sum(1 for msg in categorized if msg.has_errors)

        # Truncated count
        truncated_count = sum(1 for msg in categorized if msg.is_truncated)

        return {
            "total_messages": total,
            "by_category": by_category,
            "by_priority": by_priority,
            "error_count": error_count,
            "truncated_count": truncated_count,
        }
