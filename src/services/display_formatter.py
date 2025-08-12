"""Display formatting system for message categorization."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.text import Text

from .message_categorizer import CategorizedMessage, MessageCategory


class DisplayFormatter:
    """Formats categorized messages for terminal display."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize the display formatter.

        Args:
            console: Rich Console instance for formatting

        """
        self.console = console or Console()

        # Color scheme for message types
        self.color_scheme = {
            MessageCategory.USER_INPUT: "blue",
            MessageCategory.AI_RESPONSE: "green",
            MessageCategory.TOOL_CALL: "orange3",
            MessageCategory.TOOL_RESULT: "cyan",
            MessageCategory.SYSTEM_EVENT: "yellow",
            MessageCategory.META_INFORMATION: "magenta",
        }

        # Icons for message types
        self.icons = {
            MessageCategory.USER_INPUT: "👤",
            MessageCategory.AI_RESPONSE: "🤖",
            MessageCategory.TOOL_CALL: "🔧",
            MessageCategory.TOOL_RESULT: "📋",
            MessageCategory.SYSTEM_EVENT: "⚙️",
            MessageCategory.META_INFORMATION: "📊",
        }

    def format_message(
        self,
        categorized_msg: CategorizedMessage,
        *,
        show_metadata: bool = False,
        compact: bool = False,
    ) -> Text:
        """Format a single categorized message for display.

        Args:
            categorized_msg: The categorized message to format
            show_metadata: Whether to show metadata
            compact: Whether to use compact formatting

        Returns:
            Rich Text object with formatted message

        """
        # Get color for message type
        color = self.color_scheme.get(categorized_msg.category, "white")
        icon = self.icons.get(categorized_msg.category, "")

        if compact:
            return self._format_compact(categorized_msg, color, icon)

        return self._format_full(
            categorized_msg,
            color,
            icon,
            show_metadata=show_metadata,
        )

    def _format_compact(
        self,
        msg: CategorizedMessage,
        color: str,
        icon: str,
    ) -> Text:
        """Format message in compact mode."""
        text = Text()
        text.append(f"{icon} ", style=color)
        text.append(f"{msg.timestamp_relative} | ", style="dim")
        text.append(msg.summary, style=color)
        return text

    def _format_full(
        self,
        msg: CategorizedMessage,
        color: str,
        icon: str,
        *,
        show_metadata: bool,
    ) -> Text:
        """Format message in full mode."""
        text = Text()
        text.append(f"{icon} ", style=color)
        text.append(msg.summary, style=f"bold {color}")
        text.append(f" ({msg.timestamp_relative})", style="dim")
        text.append("\n")

        # Content with syntax highlighting if applicable
        display_content = self._format_content(msg)
        text.append(display_content)

        if show_metadata and msg.metadata:
            text.append("\n")
            text.append(self._format_metadata(msg.metadata))

        return text

    def _format_content(self, categorized_msg: CategorizedMessage) -> Text:
        """Format the message content."""
        content = categorized_msg.display_text
        text = Text()

        # Apply appropriate styling based on content type
        if self._looks_like_code(content):
            text.append(content, style="bright_white on default")
        else:
            text.append(content, style="dim")

        # Add status indicators
        return self._add_status_indicators(text, categorized_msg)

    def _add_status_indicators(
        self,
        text: Text,
        msg: CategorizedMessage,
    ) -> Text:
        """Add status indicators to text."""
        if msg.is_truncated:
            text.append(" [truncated]", style="red dim")

        if msg.has_errors:
            text.append(" ⚠️", style="red")

        return text

    def _looks_like_code(self, content: str) -> bool:
        """Detect if content looks like code."""
        code_indicators = [
            r"\bdef\s+\w+\(",  # Python function
            r"\bfunction\s+\w+\(",  # JavaScript function
            r"\bclass\s+\w+",  # Class definition
            r"import\s+\w+",  # Import statement
            r"from\s+\w+\s+import",  # Python import
            r"{\s*\n.*}",  # JSON/object literal
            r"<\w+[^>]*>",  # HTML/XML tags
        ]

        return any(re.search(pattern, content) for pattern in code_indicators)

    def _detect_language(self, content: str, metadata: dict[str, Any]) -> str:
        """Detect programming language from content and metadata."""
        # Check metadata for file extensions first
        if "file_path" in metadata:
            file_path = Path(metadata["file_path"])
            language = self._get_language_from_extension(file_path.suffix)
            if language != "text":
                return language

        # Content-based detection
        return self._detect_language_from_content(content)

    def _get_language_from_extension(self, suffix: str) -> str:
        """Get language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "jsx",
            ".tsx": "tsx",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".md": "markdown",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".sh": "bash",
            ".sql": "sql",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
        }
        return ext_map.get(suffix, "text")

    def _detect_language_from_content(self, content: str) -> str:
        """Detect language from content patterns."""
        if re.search(r"\bdef\s+\w+\(", content):
            return "python"
        if re.search(r"\bfunction\s+\w+\(", content):
            return "javascript"
        if re.search(r"<\w+[^>]*>", content):
            return "html"
        if re.search(r'{\s*".*":', content):
            return "json"
        return "text"

    def _format_metadata(self, metadata: dict[str, Any]) -> Text:
        """Format metadata for display."""
        text = Text()
        text.append("Metadata: ", style="bold dim")

        items = []
        for key, value in metadata.items():
            if key == "file_path":
                file_name = Path(value).name
                items.append(f"file: {file_name}")
            elif key == "tool_name":
                items.append(f"tool: {value}")
            elif key == "session_id":
                items.append(f"session: {value[:8]}...")
            else:
                items.append(f"{key}: {value}")

        text.append(" | ".join(items), style="dim cyan")
        return text

    def format_conversation_summary(
        self,
        messages: list[CategorizedMessage],
    ) -> Text:
        """Format a conversation summary."""
        text = Text()

        if not messages:
            text.append("No messages", style="dim")
            return text

        # Count message types and errors
        type_counts, error_count = self._count_message_types(messages)

        # Format summary header
        text.append("Conversation Summary:\n", style="bold")

        # Add type counts
        self._add_type_counts(text, type_counts)

        # Add error information
        if error_count > 0:
            text.append(f"⚠️  Errors: {error_count}\n", style="red")

        # Add time range if we have enough messages
        self._add_time_range(text, messages)

        return text

    def _count_message_types(
        self,
        messages: list[CategorizedMessage],
    ) -> tuple[dict[MessageCategory, int], int]:
        """Count message types and errors."""
        type_counts: dict[MessageCategory, int] = {}
        error_count = 0

        for msg in messages:
            type_counts[msg.category] = type_counts.get(msg.category, 0) + 1
            if msg.has_errors:
                error_count += 1

        return type_counts, error_count

    def _add_type_counts(
        self,
        text: Text,
        type_counts: dict[MessageCategory, int],
    ) -> None:
        """Add message type counts to text."""
        for category, count in type_counts.items():
            icon = self.icons.get(category, "")
            color = self.color_scheme.get(category, "white")
            text.append(f"{icon} {category.value}: {count}\n", style=color)

    def _add_time_range(
        self,
        text: Text,
        messages: list[CategorizedMessage],
    ) -> None:
        """Add time range information to text."""
        min_messages_for_time_range = 2
        if len(messages) >= min_messages_for_time_range:
            start_time = messages[0].timestamp_relative
            end_time = messages[-1].timestamp_relative
            text.append(f"📅 From {start_time} to {end_time}\n", style="dim")

    def format_tool_operation_summary(
        self,
        tool_calls: list[CategorizedMessage],
    ) -> Text:
        """Format a summary of tool operations."""
        text = Text()

        if not tool_calls:
            text.append("No tool operations", style="dim")
            return text

        text.append("Tool Operations:\n", style="bold")

        # Group by tool type
        tool_counts: dict[str, int] = {}
        for msg in tool_calls:
            if "tool_name" in msg.metadata:
                tool_name = msg.metadata["tool_name"]
                tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1

        for tool_name, count in sorted(tool_counts.items()):
            text.append(f"🔧 {tool_name}: {count} calls\n", style="orange3")

        return text

    def create_progress_indicator(
        self,
        current: int,
        total: int,
        message: str = "",
    ) -> Text:
        """Create a progress indicator for message processing."""
        text = Text()

        # Progress bar
        bar_length = 20
        filled_length = int(bar_length * current / total) if total > 0 else 0
        bar = "█" * filled_length + "░" * (bar_length - filled_length)

        percentage = (current / total * 100) if total > 0 else 0

        text.append(
            f"[{bar}] {percentage:.1f}% ({current}/{total})",
            style="blue",
        )

        if message:
            text.append(f" - {message}", style="dim")

        return text

    def format_error_message(self, error: str, context: str = "") -> Text:
        """Format an error message."""
        text = Text()
        text.append("❌ Error: ", style="bold red")
        text.append(error, style="red")

        if context:
            text.append(f"\nContext: {context}", style="dim red")

        return text

    def format_statistics(self, stats: dict[str, Any]) -> Text:
        """Format categorization statistics."""
        text = Text()
        text.append("📊 Statistics\n", style="bold cyan")

        # Total messages
        total = stats.get("total_messages", 0)
        text.append(f"Total Messages: {total}\n", style="white")

        # Add category and priority breakdowns
        self._add_category_breakdown(text, stats)
        self._add_priority_breakdown(text, stats)
        self._add_error_summary(text, stats)

        return text

    def _add_category_breakdown(
        self,
        text: Text,
        stats: dict[str, Any],
    ) -> None:
        """Add category breakdown to statistics."""
        if "by_category" not in stats:
            return

        text.append("\nBy Category:\n", style="bold dim")
        for category, count in stats["by_category"].items():
            category_name = (
                category.value if hasattr(category, "value") else str(category)
            )
            icon = self.icons.get(category, "")
            color = self.color_scheme.get(category, "white")
            text.append(f"  {icon} {category_name}: {count}\n", style=color)

    def _add_priority_breakdown(
        self,
        text: Text,
        stats: dict[str, Any],
    ) -> None:
        """Add priority breakdown to statistics."""
        if "by_priority" not in stats:
            return

        text.append("\nBy Priority:\n", style="bold dim")
        priority_colors = {
            "critical": "red",
            "high": "orange3",
            "medium": "yellow",
            "low": "green",
        }

        for priority, count in stats["by_priority"].items():
            priority_name = (
                priority.value if hasattr(priority, "value") else str(priority)
            )
            color = priority_colors.get(priority_name, "white")
            text.append(f"  {priority_name}: {count}\n", style=color)

    def _add_error_summary(self, text: Text, stats: dict[str, Any]) -> None:
        """Add error summary to statistics."""
        error_count = stats.get("error_count", 0)
        truncated_count = stats.get("truncated_count", 0)

        if error_count > 0:
            text.append(
                f"\n⚠️  Messages with errors: {error_count}\n",
                style="red",
            )
        if truncated_count > 0:
            text.append(
                f"✂️  Truncated messages: {truncated_count}\n",
                style="yellow",
            )

    def _extract_code_blocks(self, content: str) -> list[dict[str, str]]:
        """Extract markdown code blocks from content."""
        code_blocks = []
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

    def _format_content_with_code_blocks(
        self,
        content: str,
        code_blocks: list[dict[str, str]],  # noqa: ARG002
        categorized_msg: CategorizedMessage,
    ) -> Text:
        """Format content that contains code blocks."""
        text = Text()

        # For now, just highlight the whole content as code if it has code blocks
        text.append(content, style="bright_white on default")

        return self._add_status_indicators(text, categorized_msg)
