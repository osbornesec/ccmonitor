"""Data models for JSONL parsing and conversation data."""

from __future__ import annotations

import re
from datetime import datetime  # noqa: TC003 - needed at runtime for Pydantic
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, validator


class MessageRole(str, Enum):
    """Message roles in Claude conversations."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    """Message types in JSONL logs."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL_CALL = "tool_call"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    TOOL_USE_RESULT = "tool_use_result"
    HOOK = "hook"
    META = "meta"
    SUMMARY = "summary"  # Summary entries at the start of conversations
    UNKNOWN = "unknown"  # Fallback for unrecognized types


class ContentType(str, Enum):
    """Content types within messages."""

    TEXT = "text"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    IMAGE = "image"
    DOCUMENT = "document"
    THINKING = "thinking"  # New thinking content type


class TextContent(BaseModel):
    """Text content within a message."""

    type: Literal["text"] = "text"
    text: str


class ToolUseContent(BaseModel):
    """Tool use content within a message."""

    type: Literal["tool_use"] = "tool_use"
    id: str
    name: str
    input: dict[str, Any]


class ToolResultContent(BaseModel):
    """Tool result content within a message."""

    type: Literal["tool_result"] = "tool_result"
    tool_use_id: str
    content: str | list[dict[str, Any]]
    is_error: bool = False


class ImageContent(BaseModel):
    """Image content within a message."""

    type: Literal["image"] = "image"
    source: dict[str, Any]


class ThinkingContent(BaseModel):
    """Thinking content within a message (Claude's internal reasoning)."""

    type: Literal["thinking"] = "thinking"
    thinking: str | None = None


# Union type for all content types
MessageContent = (
    TextContent
    | ToolUseContent
    | ToolResultContent
    | ImageContent
    | ThinkingContent
)


class Message(BaseModel):
    """Message structure within JSONL entries."""

    role: MessageRole | None = None
    content: str | list[MessageContent]
    tool: str | None = None  # For tool_call messages
    parameters: dict[str, Any] | None = None  # For tool_call messages
    result: str | dict[str, Any] | None = None  # For tool_call messages

    @validator("content", pre=True)
    @classmethod
    def validate_content(
        cls,
        v: object,
    ) -> str | list[MessageContent] | object:
        """Ensure content is properly formatted."""
        # Simple validation - let Pydantic handle most of the work
        if isinstance(v, (str, list)):
            return v
        if isinstance(v, dict):
            # Handle single content objects - let Pydantic validate the structure
            return [v]
        return str(v)


class ToolUseResult(BaseModel):
    """Tool use result structure."""

    tool_name: str
    input: dict[str, Any]
    output: str | dict[str, Any]
    is_error: bool = False
    execution_time: float | None = None


class JSONLEntry(BaseModel):
    """Base JSONL entry model."""

    # Make uuid optional for summary entries
    uuid: str | None = None
    type: MessageType
    # Make timestamp optional for summary entries
    timestamp: str | None = None
    session_id: str | None = Field(None, alias="sessionId")
    parent_uuid: str | None = Field(None, alias="parentUuid")
    message: Message | None = None
    # Handle both dict and string toolUseResult
    # Can be a ToolUseResult object, a string error, any dict from various tools, or a list
    tool_use_result: (
        ToolUseResult | str | dict[str, Any] | list[Any] | None
    ) = Field(
        None,
        alias="toolUseResult",
    )
    cwd: str | None = None
    git_branch: str | None = Field(None, alias="gitBranch")
    version: str | None = None
    is_meta: bool | None = Field(None, alias="isMeta")
    tool_use_id: str | None = Field(None, alias="toolUseID")
    # Fields for summary entries
    summary: str | None = None
    leaf_uuid: str | None = Field(None, alias="leafUuid")

    class Config:
        """Pydantic configuration."""

        allow_population_by_field_name = True
        extra = "allow"  # Allow extra fields for future compatibility

    @validator("timestamp")
    @classmethod
    def parse_timestamp(cls, v: object) -> str | None:
        """Parse and validate timestamp."""
        # Allow None for summary entries
        if v is None:
            return None

        if isinstance(v, str):
            # Basic ISO format check with regex
            iso_match = re.match(
                r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)",
                v,
            )
            if iso_match:
                return iso_match.group(1)
            # Return as-is if can't parse (will be handled downstream)
            return v
        return str(v)

    @validator("uuid")
    @classmethod
    def validate_uuid(cls, v: object) -> str | None:
        """Validate UUID format."""
        # Allow None for summary entries
        if v is None:
            return None

        if not isinstance(v, str):
            msg = "UUID must be a string or None"
            raise ValueError(msg)

        # Basic UUID format check (allow various formats)
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            msg = f"Invalid UUID format: {v}"
            raise ValueError(msg)

        return v


class ConversationThread(BaseModel):
    """A conversation thread with linked messages."""

    session_id: str
    messages: list[JSONLEntry]
    start_time: datetime
    end_time: datetime | None = None
    total_messages: int = 0
    user_messages: int = 0
    assistant_messages: int = 0
    tool_calls: int = 0
    tool_results: int = 0

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class ParseStatistics(BaseModel):
    """Statistics from JSONL parsing."""

    total_lines: int = 0
    valid_entries: int = 0
    invalid_entries: int = 0
    skipped_lines: int = 0
    parse_errors: int = 0
    validation_errors: int = 0
    processing_time: float = 0.0

    # Message type counts
    user_messages: int = 0
    assistant_messages: int = 0
    tool_calls: int = 0
    tool_results: int = 0
    system_messages: int = 0
    hook_messages: int = 0

    # Error details
    error_details: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate parsing success rate."""
        if self.total_lines == 0:
            return 0.0
        return (self.valid_entries / self.total_lines) * 100.0

    def add_error(
        self,
        line_number: int,
        error_type: str,
        error_message: str,
        raw_line: str | None = None,
    ) -> None:
        """Add error details."""
        self.error_details.append(
            {
                "line_number": line_number,
                "error_type": error_type,
                "error_message": error_message,
                "raw_line": (
                    raw_line[:100] if raw_line else None
                ),  # Truncate for storage
            },
        )


class ParseResult(BaseModel):
    """Result of JSONL parsing operation."""

    entries: list[JSONLEntry]
    statistics: ParseStatistics
    conversations: list[ConversationThread]
    file_path: str | None = None

    def get_conversation_by_session(
        self,
        session_id: str,
    ) -> ConversationThread | None:
        """Get conversation by session ID."""
        for conv in self.conversations:
            if conv.session_id == session_id:
                return conv
        return None

    def get_entries_by_type(
        self,
        message_type: MessageType,
    ) -> list[JSONLEntry]:
        """Get entries filtered by type."""
        return [entry for entry in self.entries if entry.type == message_type]

    def get_tool_usage_summary(self) -> dict[str, int]:
        """Get summary of tool usage."""
        tool_counts: dict[str, int] = {}

        for entry in self.entries:
            if entry.type in [MessageType.TOOL_CALL, MessageType.TOOL_USE]:
                if entry.message and entry.message.tool:
                    tool_name = entry.message.tool
                    tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
            elif entry.tool_use_result:
                # Handle both ToolUseResult objects and string errors
                if isinstance(entry.tool_use_result, ToolUseResult):
                    tool_name = entry.tool_use_result.tool_name
                    tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
                # String tool_use_result indicates an error, skip counting

        return tool_counts
