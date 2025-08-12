"""Message categorization system for Claude Code activity logs."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .models import JSONLEntry, MessageType


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
        timestamp_relative = self._format_relative_timestamp(entry.timestamp)

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
        if entry.type == MessageType.USER:
            return MessageCategory.USER_INPUT
        if entry.type == MessageType.ASSISTANT:
            return MessageCategory.AI_RESPONSE
        if entry.type in [MessageType.TOOL_CALL, MessageType.TOOL_USE]:
            return MessageCategory.TOOL_CALL
        if entry.type in [
            MessageType.TOOL_RESULT,
            MessageType.TOOL_USE_RESULT,
        ]:
            return MessageCategory.TOOL_RESULT
        if entry.type == MessageType.SYSTEM:
            return MessageCategory.SYSTEM_EVENT
        if entry.type == MessageType.META or entry.git_branch:
            return MessageCategory.META_INFORMATION
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
            if entry.tool_use_result and entry.tool_use_result.is_error:
                return MessagePriority.HIGH
            return MessagePriority.LOW
        return MessagePriority.LOW

    def _generate_summary(
        self,
        entry: JSONLEntry,
        category: MessageCategory,
    ) -> str:
        """Generate a plain English summary of the message."""
        if category == MessageCategory.USER_INPUT:
            if entry.message and isinstance(entry.message.content, str):
                # Extract key intent from user message
                content = entry.message.content.lower()
                if any(
                    word in content for word in ["help", "can you", "please"]
                ):
                    return "User asks for help"
                if any(
                    word in content for word in ["create", "write", "make"]
                ):
                    return "User requests creation"
                if any(word in content for word in ["fix", "error", "bug"]):
                    return "User reports issue"
                if any(word in content for word in ["explain", "what", "how"]):
                    return "User asks for explanation"
                return "User message"
            return "User input"

        if category == MessageCategory.AI_RESPONSE:
            return "Claude responds"

        if category == MessageCategory.TOOL_CALL:
            if entry.message and entry.message.tool:
                tool_name = entry.message.tool
                if tool_name in self.tool_operation_map:
                    return self.tool_operation_map[tool_name]["description"]
                return f"Tool call: {tool_name}"
            return "Tool operation"

        if category == MessageCategory.TOOL_RESULT:
            if entry.tool_use_result:
                if entry.tool_use_result.is_error:
                    return "Tool operation failed"
                tool_name = entry.tool_use_result.tool_name
                if tool_name == "Read":
                    return "File read successfully"
                if tool_name == "Write":
                    return "File written successfully"
                if tool_name == "Edit":
                    return "File edited successfully"
                if tool_name == "Bash":
                    return "Command completed"
                return f"{tool_name} completed"
            return "Tool result"

        if category == MessageCategory.SYSTEM_EVENT:
            if entry.message and isinstance(entry.message.content, str):
                content = entry.message.content
                if "session" in content.lower():
                    return "Session started"
                if "error" in content.lower():
                    return "System error"
                return "System event"
            return "System message"

        if category == MessageCategory.META_INFORMATION:
            if entry.git_branch:
                return f"Git branch: {entry.git_branch}"
            if entry.cwd:
                return f"Directory: {Path(entry.cwd).name}"
            return "Metadata update"

        # Handle malformed messages
        return "Malformed message"

    def _generate_display_text(self, entry: JSONLEntry) -> str:
        """Generate display text for the message."""
        if entry.message:
            if isinstance(entry.message.content, str):
                return entry.message.content
            if isinstance(entry.message.content, list):
                # Extract text from content list
                text_parts = []
                for item in entry.message.content:
                    if hasattr(item, "text"):
                        text_parts.append(item.text)
                    elif isinstance(item, dict) and "text" in item:
                        text_parts.append(item["text"])
                    else:
                        text_parts.append(str(item))
                return " ".join(text_parts)

        # For tool results, show the output
        if entry.tool_use_result and entry.tool_use_result.output:
            output = entry.tool_use_result.output
            if isinstance(output, str):
                return output
            return str(output)

        # For tool calls, show parameters
        if entry.message and entry.message.parameters:
            params = []
            for key, value in entry.message.parameters.items():
                params.append(f"{key}={value}")
            return f"Parameters: {', '.join(params)}"

        return f"[{entry.type}] message"

    def _format_relative_timestamp(self, timestamp: str) -> str:
        """Format timestamp as relative time."""
        try:
            # Parse timestamp
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            now = datetime.now(UTC)
            diff = now - dt

            # Format as relative time
            if diff.days > 0:
                return f"{diff.days} days ago"
            if diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hours ago"
            if diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minutes ago"
            return "Just now"

        except (ValueError, TypeError):
            return timestamp

    def _extract_metadata(self, entry: JSONLEntry) -> dict[str, Any]:
        """Extract metadata from the entry."""
        metadata: dict[str, Any] = {}

        # Basic info
        if entry.session_id:
            metadata["session_id"] = entry.session_id
        if entry.parent_uuid:
            metadata["parent_uuid"] = entry.parent_uuid

        # Tool information
        if entry.message and entry.message.tool:
            metadata["tool_name"] = entry.message.tool
            if entry.message.parameters:
                # Extract file paths for easy access
                if "file_path" in entry.message.parameters:
                    metadata["file_path"] = entry.message.parameters[
                        "file_path"
                    ]
                if "query" in entry.message.parameters:
                    metadata["search_query"] = entry.message.parameters[
                        "query"
                    ]

        # Context information
        if entry.cwd:
            metadata["working_directory"] = entry.cwd
        if entry.git_branch:
            metadata["git_branch"] = entry.git_branch
        if entry.version:
            metadata["version"] = entry.version

        return metadata

    def _check_for_errors(self, entry: JSONLEntry) -> bool:
        """Check if the entry represents an error condition."""
        # Tool result errors
        if entry.tool_use_result and entry.tool_use_result.is_error:
            return True

        # Malformed entries
        if not entry.message and entry.type in [
            MessageType.USER,
            MessageType.ASSISTANT,
            MessageType.SYSTEM,
        ]:
            return True

        # Invalid timestamps
        try:
            datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))
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
        groups = []
        tool_calls = {}

        # First pass: collect tool calls
        for entry in entries:
            if entry.type in [MessageType.TOOL_CALL, MessageType.TOOL_USE]:
                tool_calls[entry.uuid] = entry

        # Second pass: match with results
        for entry in entries:
            if entry.type in [
                MessageType.TOOL_RESULT,
                MessageType.TOOL_USE_RESULT,
            ]:
                call_id = entry.parent_uuid or entry.tool_use_id
                if call_id and call_id in tool_calls:
                    tool_call = tool_calls[call_id]

                    # Calculate execution time
                    exec_time = 0.0
                    try:
                        call_time = datetime.fromisoformat(
                            tool_call.timestamp.replace("Z", "+00:00"),
                        )
                        result_time = datetime.fromisoformat(
                            entry.timestamp.replace("Z", "+00:00"),
                        )
                        exec_time = (result_time - call_time).total_seconds()
                    except (ValueError, TypeError):
                        pass

                    # Determine tool name
                    tool_name = "Unknown"
                    if tool_call.message and tool_call.message.tool:
                        tool_name = tool_call.message.tool
                    elif entry.tool_use_result:
                        tool_name = entry.tool_use_result.tool_name

                    # Check success
                    success = True
                    if (
                        entry.tool_use_result
                        and entry.tool_use_result.is_error
                    ):
                        success = False

                    # Generate summary
                    summary = self._generate_tool_group_summary(
                        tool_call,
                        entry,
                        tool_name,
                        success,
                    )

                    group = ToolCallGroup(
                        tool_call=tool_call,
                        tool_result=entry,
                        tool_name=tool_name,
                        success=success,
                        execution_time=exec_time,
                        summary=summary,
                    )
                    groups.append(group)

        return groups

    def _generate_tool_group_summary(
        self,
        tool_call: JSONLEntry,
        tool_result: JSONLEntry,
        tool_name: str,
        success: bool,
    ) -> str:
        """Generate summary for a tool call group."""
        if not success:
            return f"{tool_name} operation failed"

        # Generate operation-specific summaries
        if (
            tool_name == "Read"
            and tool_call.message
            and tool_call.message.parameters
        ):
            file_path = tool_call.message.parameters.get("file_path", "")
            file_name = Path(file_path).name if file_path else "file"
            return f"Reading {file_name}"
        if (
            tool_name == "Write"
            and tool_call.message
            and tool_call.message.parameters
        ):
            file_path = tool_call.message.parameters.get("file_path", "")
            file_name = Path(file_path).name if file_path else "file"
            return f"Writing {file_name}"
        if (
            tool_name == "Edit"
            and tool_call.message
            and tool_call.message.parameters
        ):
            file_path = tool_call.message.parameters.get("file_path", "")
            file_name = Path(file_path).name if file_path else "file"
            return f"Editing {file_name}"
        if tool_name == "Bash":
            return "Command execution"
        return f"{tool_name} operation"

    def create_message_threads(
        self,
        entries: list[JSONLEntry],
    ) -> list[MessageThread]:
        """Create message threads from entries."""
        threads = []
        sessions: dict[str, list[JSONLEntry]] = {}

        # Group by session
        for entry in entries:
            session_id = entry.session_id or "default"
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(entry)

        # Create threads
        for session_id, session_entries in sessions.items():
            if not session_entries:
                continue

            # Sort by timestamp
            try:
                session_entries.sort(
                    key=lambda e: datetime.fromisoformat(
                        e.timestamp.replace("Z", "+00:00"),
                    ),
                )
            except (ValueError, TypeError):
                pass

            # Calculate metrics
            user_count = sum(
                1 for e in session_entries if e.type == MessageType.USER
            )
            assistant_count = sum(
                1 for e in session_entries if e.type == MessageType.ASSISTANT
            )
            tool_count = sum(
                1
                for e in session_entries
                if e.type in [MessageType.TOOL_CALL, MessageType.TOOL_USE]
            )

            # Calculate duration
            duration = 0.0
            start_time = datetime.now(UTC)
            end_time = None

            try:
                timestamps = [
                    datetime.fromisoformat(e.timestamp.replace("Z", "+00:00"))
                    for e in session_entries
                    if e.timestamp
                ]
                if timestamps:
                    start_time = min(timestamps)
                    end_time = max(timestamps)
                    duration = (end_time - start_time).total_seconds()
            except (ValueError, TypeError):
                pass

            thread = MessageThread(
                session_id=session_id,
                messages=session_entries,
                start_time=start_time,
                end_time=end_time,
                user_message_count=user_count,
                assistant_message_count=assistant_count,
                tool_call_count=tool_count,
                duration=duration,
            )
            threads.append(thread)

        return threads

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
                datetime.fromisoformat(e.timestamp.replace("Z", "+00:00"))
                for e in entries
                if e.timestamp
            ]
            if len(timestamps) >= 2:
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
        results = []

        for msg in categorized:
            if (
                query_lower in msg.display_text.lower()
                or query_lower in msg.summary.lower()
            ):
                results.append(msg)

        return results

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
