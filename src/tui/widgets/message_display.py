"""MessageDisplay widget for CCMonitor TUI with rich formatting and syntax highlighting.

This module provides comprehensive message rendering for the CCMonitor TUI application,
supporting various message types with rich formatting, syntax highlighting for code
blocks, and proper theme integration.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING, ClassVar

from rich.panel import Panel
from rich.text import Text
from textual.widgets import Static

from src.tui.utils.themes import ThemeManager

if TYPE_CHECKING:
    from src.utils.type_definitions import MessageDict, MessageType


class MessageDisplay(Static):
    """Advanced message display widget with rich formatting and syntax highlighting.

    Features:
    - Message type differentiation with icons and colors
    - Syntax highlighting for code blocks
    - Rich formatting with panels and borders
    - Theme integration for consistent styling
    - Timestamp display with proper formatting
    - Markdown-like text formatting
    """

    # Message type configuration with icons and styling
    MESSAGE_CONFIG: ClassVar[dict[MessageType, dict[str, str]]] = {
        "user": {
            "icon": "👤",
            "title": "User",
            "css_class": "message-user",
            "border_style": "solid",
        },
        "assistant": {
            "icon": "🤖",
            "title": "Assistant",
            "css_class": "message-assistant",
            "border_style": "double",
        },
        "system": {
            "icon": "⚙️",
            "title": "System",
            "css_class": "message-system",
            "border_style": "heavy",
        },
        "tool_call": {
            "icon": "🔧",
            "title": "Tool",
            "css_class": "message-tool",
            "border_style": "dashed",
        },
    }

    # Additional message type for error handling
    ERROR_MESSAGE_CONFIG: ClassVar[dict[str, str]] = {
        "icon": "❌",
        "title": "Error",
        "css_class": "message-error",
        "border_style": "solid",
    }

    # Default configuration for unknown message types
    DEFAULT_MESSAGE_CONFIG: ClassVar[dict[str, str]] = {
        "icon": "❓",
        "title": "Unknown",
        "css_class": "message-error",
        "border_style": "solid",
    }

    # Constants for code block formatting
    MIN_LINES_FOR_LINE_NUMBERS = 5

    # Code block detection regex
    CODE_BLOCK_PATTERN = re.compile(
        r"```(\w+)?\n(.*?)\n```",
        re.DOTALL | re.MULTILINE,
    )

    # Inline code detection regex
    INLINE_CODE_PATTERN = re.compile(r"`([^`]+)`")

    DEFAULT_CSS = """
    MessageDisplay {
        margin: 1;
        padding: 0;
        border: none;
        background: transparent;
        text-wrap: auto;
        overflow: hidden auto;
    }

    MessageDisplay .message-user {
        border: solid $user-message;
        background: $surface;
        color: $text;
        box-shadow: 0 1 2 0 $user-message 20%;
    }

    MessageDisplay .message-assistant {
        border: double $assistant-message;
        background: $surface;
        color: $text;
        box-shadow: 0 1 2 0 $assistant-message 20%;
    }

    MessageDisplay .message-system {
        border: heavy $system-message;
        background: $panel;
        color: $text;
        box-shadow: 0 1 2 0 $system-message 20%;
    }

    MessageDisplay .message-tool {
        border: dashed $tool-message;
        background: $panel;
        color: $text;
        box-shadow: 0 1 2 0 $tool-message 20%;
    }

    MessageDisplay .message-error {
        border: solid $error-message;
        background: $error-message 5%;
        color: $text;
        box-shadow: 0 1 3 0 $error-message 30%;
    }

    MessageDisplay .message-timestamp {
        color: $text-muted;
        text-style: italic;
        background: transparent;
    }

    MessageDisplay .message-content {
        margin: 1;
        padding: 1;
        text-wrap: auto;
        overflow: hidden auto;
    }

    MessageDisplay .message-header {
        text-style: bold;
        padding: 0 1;
        background: transparent;
        border-bottom: thin $border;
        margin-bottom: 1;
    }

    MessageDisplay .code-block {
        background: $panel;
        border: thin $border;
        padding: 1;
        margin: 1 0;
        text-wrap: none;
        scrollbar-size: 1 0;
        scrollbar-background: $surface;
        scrollbar-color: $border;
    }

    MessageDisplay .inline-code {
        background: $panel;
        color: $syntax-string;
        padding: 0 1;
        border: thin $border 50%;
    }

    MessageDisplay .language-indicator {
        color: $text-muted;
        text-style: italic;
        background: $border 20%;
        padding: 0 1;
        margin-bottom: 1;
    }
    """

    def __init__(  # noqa: PLR0913
        self,
        message: MessageDict,
        *,
        theme_manager: ThemeManager | None = None,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialize MessageDisplay widget.

        Args:
            message: Message data to display
            theme_manager: Theme manager for styling (optional)
            name: Widget name
            id: Widget ID
            classes: CSS classes
            disabled: Widget disabled state

        """
        super().__init__(
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )

        self.message = message
        self.theme_manager = theme_manager or ThemeManager()

        # Set CSS class based on message type
        message_type = message.get("type", "system")
        config = self.MESSAGE_CONFIG.get(
            message_type,
            self.DEFAULT_MESSAGE_CONFIG,
        )
        self.add_class(config["css_class"])

    def on_mount(self) -> None:
        """Handle widget mounting and render initial content."""
        self._render_message()

    def _render_message(self) -> None:
        """Render the message with rich formatting and comprehensive error handling."""
        try:
            rich_content = self._create_rich_content()
            self.update(rich_content)
        except (ValueError, TypeError, KeyError) as e:
            # Handle specific formatting errors gracefully
            self._handle_rendering_error(e)
        except (AttributeError, ImportError, RuntimeError) as e:
            # Handle other potential errors during rendering
            self._handle_unexpected_error(e)

    def _handle_rendering_error(self, error: Exception) -> None:
        """Handle rendering errors with user-friendly fallback display.

        Args:
            error: The exception that occurred during rendering

        """
        error_config = self.ERROR_MESSAGE_CONFIG
        error_panel = Panel(
            f"Message rendering failed: {error}",
            title=f"{error_config['icon']} {error_config['title']}",
            title_align="left",
            border_style=error_config["border_style"],
            style="red on black",
            padding=(1, 2),
        )
        self.update(error_panel)

    def _handle_unexpected_error(self, error: Exception) -> None:
        """Handle unexpected errors with minimal fallback display.

        Args:
            error: The unexpected exception that occurred

        """
        fallback_text = Text()
        fallback_text.append("❌ Unexpected Error\n", style="red bold")
        fallback_text.append(
            f"Failed to render message: {type(error).__name__}", style="red",
        )
        if str(error):
            fallback_text.append(f"\nDetails: {error}", style="red dim")
        self.update(fallback_text)

    def _create_rich_content(self) -> Panel:
        """Create rich-formatted content panel for the message.

        Returns:
            Rich Panel with formatted message content

        """
        message_type = self.message.get("type", "system")
        config = self.MESSAGE_CONFIG.get(
            message_type,
            self.DEFAULT_MESSAGE_CONFIG,
        )

        # Get theme colors
        theme = self.theme_manager.get_current_theme()

        # Create header with icon, type, and timestamp
        header = self._create_header(config, theme)

        # Process message content
        content = self._process_message_content()

        # Create panel with proper styling
        return Panel(
            content,
            title=header,
            title_align="left",
            border_style=config["border_style"],
            style=f"on {theme.surface}",
            padding=(1, 2),
        )

    def _create_header(
        self,
        config: dict[str, str],
        theme: object,
    ) -> Text:
        """Create message header with icon, type, and timestamp.

        Args:
            config: Message configuration
            theme: Current theme

        Returns:
            Rich Text object with formatted header

        """
        header = Text()

        # Add icon and message type
        header.append(f"{config['icon']} {config['title']}", style="bold")

        # Add timestamp if available
        timestamp = self.message.get("timestamp")
        if timestamp:
            formatted_time = self._format_timestamp(timestamp)
            header.append(" • ", style=getattr(theme, "text_muted", "gray"))
            header.append(
                formatted_time,
                style=getattr(theme, "text_muted", "gray"),
            )

        return header

    def _format_timestamp(self, timestamp: str) -> str:
        """Format timestamp for display.

        Args:
            timestamp: ISO format timestamp string

        Returns:
            Human-readable timestamp

        """
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00", 1))
            return dt.strftime("%H:%M:%S")
        except (ValueError, AttributeError):
            return str(timestamp)

    def _process_message_content(self) -> Text:
        """Process and format message content with syntax highlighting.

        Returns:
            Rich Text object with processed content

        """
        message_content = self.message.get("message", {})

        if isinstance(message_content, dict):
            # Handle structured message content
            content_text = message_content.get("content", "")
            if not content_text:
                # Fallback to string representation of the entire message
                content_text = str(message_content)
        else:
            content_text = str(message_content)

        return self._format_text_content(content_text)

    def _format_text_content(self, content: str) -> Text:
        """Format text content with code block and inline code highlighting.

        Args:
            content: Raw text content

        Returns:
            Rich Text object with formatted content

        """
        if not content:
            return Text("(empty message)", style="italic")

        return self._process_code_blocks(content)

    def _process_code_blocks(self, content: str) -> Text:
        """Process code blocks in content.

        Args:
            content: Text content to process

        Returns:
            Rich Text with code blocks processed

        """
        formatted_text = Text()
        last_end = 0

        for match in self.CODE_BLOCK_PATTERN.finditer(content):
            # Add text before code block
            if match.start() > last_end:
                pre_text = content[last_end : match.start()]
                formatted_text.append(self._format_inline_elements(pre_text))

            # Add processed code block
            formatted_text.append(self._create_code_block(match))
            last_end = match.end()

        # Add remaining text
        self._add_remaining_text(formatted_text, content, last_end)
        return formatted_text

    def _create_code_block(self, match: object) -> Text:
        """Create formatted code block from regex match with theme-based highlighting.

        Args:
            match: Regex match object

        Returns:
            Rich Text with formatted code block using theme colors

        """
        # Use getattr to safely access match methods
        language = getattr(match, "group", lambda _: "text")(1) or "text"
        code_content = getattr(match, "group", lambda _: "")(2)

        # Get current theme for consistent styling
        theme = self.theme_manager.get_current_theme()

        code_block = Text()
        try:
            # Add language indicator with theme colors
            code_block.append(
                f"\n[{language.upper()}]\n",
                style=f"{getattr(theme, 'syntax_comment', '#6A9955')}",
            )

            # Apply basic theme-based syntax highlighting
            code_lines = code_content.split("\n")
            for line in code_lines:
                style = self._get_line_style(line, theme)
                code_block.append(line + "\n", style=style)

            code_block.append("\n")

        except (ImportError, ValueError, AttributeError):
            # Fallback to simple themed styling
            code_block.append(f"\n[{language}]\n")
            fallback_style = (
                f"{getattr(theme, 'syntax_string', 'cyan')} "
                f"on {getattr(theme, 'panel', 'black')}"
            )
            code_block.append(code_content, style=fallback_style)
            code_block.append("\n")

        return code_block

    def _get_line_style(self, line: str, theme: object) -> str:
        """Get appropriate style for a code line based on content.

        Args:
            line: Code line to analyze
            theme: Current theme object

        Returns:
            Style string for the line

        """
        line_stripped = line.strip()

        # Comments
        if line_stripped.startswith(("#", "//")):
            return f"{getattr(theme, 'syntax_comment', '#6A9955')}"
        # Strings
        if '"' in line or "'" in line:
            return f"{getattr(theme, 'syntax_string', '#CE9178')}"
        # Keywords
        keywords = [
            "def ",
            "class ",
            "function ",
            "import ",
            "from ",
            "return ",
        ]
        if any(keyword in line for keyword in keywords):
            return f"{getattr(theme, 'syntax_keyword', '#569CD6')}"
        # Numbers
        if any(char.isdigit() for char in line_stripped):
            return f"{getattr(theme, 'syntax_number', '#B5CEA8')}"
        # Default text
        return f"{getattr(theme, 'text', '#CCCCCC')}"

    def _add_remaining_text(
        self,
        formatted_text: Text,
        content: str,
        last_end: int,
    ) -> Text | None:
        """Add remaining text after code blocks.

        Args:
            formatted_text: Text object to append to
            content: Original content
            last_end: Position after last code block

        Returns:
            Text object if no code blocks found, None otherwise

        """
        if last_end < len(content):
            remaining_text = content[last_end:]
            formatted_text.append(self._format_inline_elements(remaining_text))
            return None
        if last_end == 0:
            # No code blocks found, format entire content
            return self._format_inline_elements(content)
        return None

    def _format_inline_elements(self, text: str) -> Text:
        """Format inline elements like inline code.

        Args:
            text: Text to format

        Returns:
            Rich Text object with inline formatting

        """
        if not text:
            return Text("")

        return self._process_inline_code(text)

    def _process_inline_code(self, text: str) -> Text:
        """Process inline code in text with theme-based styling.

        Args:
            text: Text to process

        Returns:
            Rich Text with inline code processed using theme colors

        """
        formatted_text = Text()
        last_end = 0

        # Get theme colors for consistent styling
        theme = self.theme_manager.get_current_theme()
        inline_code_style = (
            f"{getattr(theme, 'syntax_string', 'cyan')} "
            f"on {getattr(theme, 'panel', 'black')}"
        )

        for match in self.INLINE_CODE_PATTERN.finditer(text):
            # Add text before inline code
            if match.start() > last_end:
                formatted_text.append(text[last_end : match.start()])

            # Add inline code with theme-based highlighting
            code_content = match.group(1)
            formatted_text.append(code_content, style=inline_code_style)
            last_end = match.end()

        # Add remaining text or original if no matches
        if last_end < len(text):
            formatted_text.append(text[last_end:])
        elif last_end == 0:
            formatted_text.append(text)

        return formatted_text

    def _get_border_color(
        self,
        message_type: MessageType,
        theme: object,
    ) -> str:
        """Get border color based on message type and theme.

        Args:
            message_type: Type of message
            theme: Current theme

        Returns:
            Color string for border

        """
        color_mapping = {
            "user": getattr(theme, "user_message", "#0066CC"),
            "assistant": getattr(theme, "assistant_message", "#28A745"),
            "system": getattr(theme, "system_message", "#FFC107"),
            "tool_call": getattr(theme, "tool_message", "#FF6B35"),
        }

        return color_mapping.get(
            message_type,
            getattr(theme, "error_message", "#DC3545"),
        )

    def update_message(self, message: MessageDict) -> None:
        """Update the displayed message.

        Args:
            message: New message data to display

        """
        self.message = message

        # Update CSS class for new message type
        # Remove old message classes
        for msg_type in self.MESSAGE_CONFIG:
            config = self.MESSAGE_CONFIG[msg_type]
            self.remove_class(config["css_class"])
        self.remove_class(self.DEFAULT_MESSAGE_CONFIG["css_class"])

        # Add new message class
        message_type = message.get("type", "system")
        config = self.MESSAGE_CONFIG.get(
            message_type,
            self.DEFAULT_MESSAGE_CONFIG,
        )
        self.add_class(config["css_class"])

        # Re-render the message
        self._render_message()

    def set_theme(self, theme_manager: ThemeManager) -> None:
        """Update theme manager and re-render message.

        Args:
            theme_manager: New theme manager instance

        """
        self.theme_manager = theme_manager
        self._render_message()

    def get_message_type(self) -> MessageType:
        """Get the type of the currently displayed message.

        Returns:
            Message type

        """
        return self.message.get("type", "system")

    def get_message_id(self) -> str:
        """Get the ID of the currently displayed message.

        Returns:
            Message UUID

        """
        return self.message.get("uuid", "unknown")

    def is_error_message(self) -> bool:
        """Check if this message represents an error.

        Returns:
            True if message is an error type

        """
        return self.get_message_type() not in self.MESSAGE_CONFIG
