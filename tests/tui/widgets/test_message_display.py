"""Comprehensive tests for MessageDisplay widget with rich formatting."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from rich.panel import Panel
from rich.text import Text

from src.tui.utils.themes import ColorScheme, ThemeManager
from src.tui.widgets.message_display import MessageDisplay

if TYPE_CHECKING:
    from src.utils.type_definitions import MessageDict

# Test constants
EXPECTED_INLINE_CODE_COUNT = 2


class TestMessageDisplay:
    """Comprehensive test suite for MessageDisplay widget."""

    @pytest.fixture
    def theme_manager(self) -> ThemeManager:
        """Create a theme manager for testing."""
        return ThemeManager()

    @pytest.fixture
    def basic_message(self) -> MessageDict:
        """Create a basic message for testing."""
        return {
            "uuid": "test-123",
            "type": "user",
            "message": {"content": "Hello, world!"},
            "parentUuid": None,
            "timestamp": "2024-01-01T10:00:00Z",
        }

    @pytest.fixture
    def code_message(self) -> MessageDict:
        """Create a message with code blocks for testing."""
        content = """Here's some Python code:

```python
def hello_world():
    print("Hello, world!")
    return True
```

And some inline `code` here."""
        return {
            "uuid": "code-123",
            "type": "assistant",
            "message": {"content": content},
            "parentUuid": None,
            "timestamp": "2024-01-01T10:30:00Z",
        }

    @pytest.fixture
    def system_message(self) -> MessageDict:
        """Create a system message for testing."""
        return {
            "uuid": "sys-123",
            "type": "system",
            "message": {"content": "System initialized successfully"},
            "parentUuid": None,
            "timestamp": "2024-01-01T09:00:00Z",
        }

    def test_message_display_initialization(
        self,
        basic_message: MessageDict,
        theme_manager: ThemeManager,
    ) -> None:
        """Test MessageDisplay widget initialization."""
        display = MessageDisplay(
            basic_message,
            theme_manager=theme_manager,
            name="test_display",
            id="msg-display",
        )

        assert display.message == basic_message
        assert display.theme_manager == theme_manager
        assert display.name == "test_display"
        assert display.id == "msg-display"

    def test_message_display_initialization_default_theme(
        self,
        basic_message: MessageDict,
    ) -> None:
        """Test MessageDisplay initialization with default theme manager."""
        display = MessageDisplay(basic_message)

        assert display.message == basic_message
        assert isinstance(display.theme_manager, ThemeManager)

    def test_message_display_css_class_assignment(
        self,
        basic_message: MessageDict,
        system_message: MessageDict,
    ) -> None:
        """Test that appropriate CSS classes are assigned based on message type."""
        user_display = MessageDisplay(basic_message)
        system_display = MessageDisplay(system_message)

        # Check CSS classes were added during initialization
        assert "message-user" in user_display.classes
        assert "message-system" in system_display.classes

    def test_message_type_configuration(self) -> None:
        """Test message type configuration constants."""
        config = MessageDisplay.MESSAGE_CONFIG

        assert "user" in config
        assert "assistant" in config
        assert "system" in config
        assert "tool_call" in config

        # Check each config has required fields
        for type_config in config.values():
            assert "icon" in type_config
            assert "title" in type_config
            assert "css_class" in type_config
            assert "border_style" in type_config

    def test_error_message_configuration(self) -> None:
        """Test error message configuration."""
        error_config = MessageDisplay.ERROR_MESSAGE_CONFIG

        assert "icon" in error_config
        assert "title" in error_config
        assert "css_class" in error_config
        assert "border_style" in error_config
        assert error_config["title"] == "Error"

    def test_code_block_pattern(self) -> None:
        """Test code block regex pattern."""
        pattern = MessageDisplay.CODE_BLOCK_PATTERN

        # Test basic code block
        text1 = "```python\nprint('hello')\n```"
        match1 = pattern.search(text1)
        assert match1 is not None
        assert match1.group(1) == "python"
        assert "print('hello')" in match1.group(2)

        # Test code block without language
        text2 = "```\necho hello\n```"
        match2 = pattern.search(text2)
        assert match2 is not None
        assert match2.group(1) is None
        assert "echo hello" in match2.group(2)

    def test_inline_code_pattern(self) -> None:
        """Test inline code regex pattern."""
        pattern = MessageDisplay.INLINE_CODE_PATTERN

        text = "This is `inline code` in text"
        match = pattern.search(text)
        assert match is not None
        assert match.group(1) == "inline code"

        # Test multiple inline code blocks
        text2 = "Use `pip install` and `python -m` commands"
        matches = pattern.findall(text2)
        assert len(matches) == EXPECTED_INLINE_CODE_COUNT
        assert "pip install" in matches
        assert "python -m" in matches

    @pytest.mark.asyncio
    async def test_message_display_mount_rendering(
        self,
        basic_message: MessageDict,
    ) -> None:
        """Test that mounting triggers message rendering."""
        display = MessageDisplay(basic_message)

        # Mock the rendering method to verify it's called
        with patch.object(display, "_render_message") as mock_render:
            display.on_mount()
            mock_render.assert_called_once()

    def test_update_message(
        self,
        basic_message: MessageDict,
        system_message: MessageDict,
    ) -> None:
        """Test updating displayed message."""
        display = MessageDisplay(basic_message)

        # Initially should have user message class
        assert "message-user" in display.classes

        # Mock rendering to avoid actual UI updates during test
        with patch.object(display, "_render_message") as mock_render:
            display.update_message(system_message)

            # Message should be updated
            assert display.message == system_message
            mock_render.assert_called_once()

            # CSS classes should be updated
            assert "message-user" not in display.classes
            assert "message-system" in display.classes

    def test_set_theme(
        self,
        basic_message: MessageDict,
    ) -> None:
        """Test setting new theme manager."""
        display = MessageDisplay(basic_message)
        new_theme_manager = ThemeManager()

        with patch.object(display, "_render_message") as mock_render:
            display.set_theme(new_theme_manager)

            assert display.theme_manager == new_theme_manager
            mock_render.assert_called_once()

    def test_get_message_type(
        self,
        basic_message: MessageDict,
    ) -> None:
        """Test getting message type."""
        display = MessageDisplay(basic_message)
        assert display.get_message_type() == "user"

        # Test with message without type - use dict instead of TypedDict
        message_no_type = {
            "uuid": "test-123",
            "message": {"content": "Hello, world!"},
            "parentUuid": None,
            "timestamp": "2024-01-01T10:00:00Z",
        }
        display2 = MessageDisplay(message_no_type)  # type: ignore[arg-type]
        assert display2.get_message_type() == "system"  # Default

    def test_get_message_id(
        self,
        basic_message: MessageDict,
    ) -> None:
        """Test getting message ID."""
        display = MessageDisplay(basic_message)
        assert display.get_message_id() == "test-123"

        # Test with message without uuid - use dict instead of TypedDict
        message_no_id = {
            "type": "user",
            "message": {"content": "Hello, world!"},
            "parentUuid": None,
            "timestamp": "2024-01-01T10:00:00Z",
        }
        display2 = MessageDisplay(message_no_id)  # type: ignore[arg-type]
        assert display2.get_message_id() == "unknown"

    def test_is_error_message(
        self,
        basic_message: MessageDict,
    ) -> None:
        """Test error message detection."""
        display = MessageDisplay(basic_message)
        assert not display.is_error_message()  # user message is valid

        # Test with unknown message type - use dict instead of TypedDict
        unknown_message = {
            "uuid": "test-123",
            "type": "unknown_type",
            "message": {"content": "Hello, world!"},
            "parentUuid": None,
            "timestamp": "2024-01-01T10:00:00Z",
        }
        display2 = MessageDisplay(unknown_message)  # type: ignore[arg-type]
        assert display2.is_error_message()

    def test_rendering_error_handling(
        self,
        basic_message: MessageDict,
    ) -> None:
        """Test error handling during message rendering."""
        display = MessageDisplay(basic_message)

        # Mock _create_rich_content to raise an exception
        with (
            patch.object(
                display,
                "_create_rich_content",
                side_effect=ValueError("Test error"),
            ),
            patch.object(
                display,
                "_handle_rendering_error",
            ) as mock_error_handler,
        ):
            display._render_message()  # noqa: SLF001
            mock_error_handler.assert_called_once()

    def test_handle_rendering_error(
        self,
        basic_message: MessageDict,
    ) -> None:
        """Test rendering error handling."""
        display = MessageDisplay(basic_message)

        test_error = ValueError("Test rendering error")

        with patch.object(display, "update") as mock_update:
            display._handle_rendering_error(test_error)  # noqa: SLF001
            mock_update.assert_called_once()

            # Check that error panel was created
            call_args = mock_update.call_args[0][0]
            assert isinstance(call_args, Panel)

    def test_handle_unexpected_error(
        self,
        basic_message: MessageDict,
    ) -> None:
        """Test unexpected error handling."""
        display = MessageDisplay(basic_message)

        test_error = RuntimeError("Unexpected error")

        with patch.object(display, "update") as mock_update:
            display._handle_unexpected_error(test_error)  # noqa: SLF001
            mock_update.assert_called_once()

            # Check that error text was created
            call_args = mock_update.call_args[0][0]
            assert isinstance(call_args, Text)

    def test_theme_integration(
        self,
        basic_message: MessageDict,
    ) -> None:
        """Test theme integration in message display."""
        # Create custom theme
        custom_theme = ColorScheme(
            user_message="#FF0000",
            syntax_keyword="#00FF00",
            text="#0000FF",
        )

        theme_manager = ThemeManager()
        theme_manager.custom_themes["test_theme"] = custom_theme
        theme_manager.set_theme("test_theme")

        display = MessageDisplay(basic_message, theme_manager=theme_manager)

        # Verify theme is being used
        current_theme = display.theme_manager.get_current_theme()
        assert current_theme.user_message == "#FF0000"

    def test_message_display_with_tool_call(self) -> None:
        """Test message display with tool call message type."""
        tool_message: MessageDict = {
            "uuid": "tool-123",
            "type": "tool_call",
            "message": {
                "content": "Calling external API...",
            },
            "parentUuid": None,
            "timestamp": "2024-01-01T11:00:00Z",
        }

        display = MessageDisplay(tool_message)

        assert display.get_message_type() == "tool_call"
        assert "message-tool" in display.classes

    def test_css_classes_update_on_message_change(
        self,
        basic_message: MessageDict,
    ) -> None:
        """Test that CSS classes are properly updated when message changes."""
        display = MessageDisplay(basic_message)

        # Start with user message
        assert "message-user" in display.classes
        assert "message-system" not in display.classes

        # Change to system message
        system_msg: MessageDict = {
            "uuid": "sys-456",
            "type": "system",
            "message": {"content": "System message"},
            "parentUuid": None,
            "timestamp": None,
        }

        with patch.object(display, "_render_message"):
            display.update_message(system_msg)

        # Classes should be updated
        assert "message-user" not in display.classes
        assert "message-system" in display.classes

    @pytest.mark.parametrize(
        ("message_type", "expected_class"),
        [
            ("user", "message-user"),
            ("assistant", "message-assistant"),
            ("system", "message-system"),
            ("tool_call", "message-tool"),
        ],
    )
    def test_message_type_css_classes(
        self,
        message_type: str,
        expected_class: str,
    ) -> None:
        """Test CSS class assignment for different message types."""
        message = {
            "uuid": "test-456",
            "type": message_type,
            "message": {"content": "Test message"},
            "parentUuid": None,
            "timestamp": None,
        }

        display = MessageDisplay(message)  # type: ignore[arg-type]
        assert expected_class in display.classes

    def test_empty_message_content_handling(self) -> None:
        """Test handling of empty message content."""
        empty_message: MessageDict = {
            "uuid": "empty-123",
            "type": "user",
            "message": {},
            "parentUuid": None,
            "timestamp": None,
        }

        # Should not raise an exception
        display = MessageDisplay(empty_message)
        assert display.get_message_id() == "empty-123"

    def test_malformed_message_handling(self) -> None:
        """Test handling of malformed message structure."""
        # Message with string content instead of dict
        malformed_message = {
            "uuid": "malformed-123",
            "type": "user",
            "message": "Direct string content",
            "parentUuid": None,
            "timestamp": None,
        }

        # Should handle gracefully
        display = MessageDisplay(malformed_message)  # type: ignore[arg-type]
        assert display.get_message_type() == "user"

    def test_default_message_config(self) -> None:
        """Test default message configuration for unknown types."""
        default_config = MessageDisplay.DEFAULT_MESSAGE_CONFIG

        assert "icon" in default_config
        assert "title" in default_config
        assert "css_class" in default_config
        assert "border_style" in default_config
        assert default_config["title"] == "Unknown"

    def test_min_lines_constant(self) -> None:
        """Test minimum lines constant for code blocks."""
        min_lines = MessageDisplay.MIN_LINES_FOR_LINE_NUMBERS
        assert isinstance(min_lines, int)
        assert min_lines > 0

    def test_message_content_processing_integration(
        self,
        code_message: MessageDict,
    ) -> None:
        """Test integration of message content processing."""
        display = MessageDisplay(code_message)

        # Should handle code blocks and inline code without exceptions
        assert display.get_message_type() == "assistant"
        assert display.get_message_id() == "code-123"

        # Verify message content is accessible
        content = code_message["message"]["content"]
        assert "python" in content.lower()
        assert "```" in content

    def test_timestamp_formatting_edge_cases(self) -> None:
        """Test edge cases in timestamp handling."""
        # Message with None timestamp
        no_timestamp_msg: MessageDict = {
            "uuid": "no-time-123",
            "type": "user",
            "message": {"content": "No timestamp"},
            "parentUuid": None,
            "timestamp": None,
        }

        display = MessageDisplay(no_timestamp_msg)
        assert display.get_message_id() == "no-time-123"

        # Message with empty string timestamp
        empty_timestamp_msg: MessageDict = {
            "uuid": "empty-time-123",
            "type": "user",
            "message": {"content": "Empty timestamp"},
            "parentUuid": None,
            "timestamp": "",
        }

        display2 = MessageDisplay(empty_timestamp_msg)
        assert display2.get_message_id() == "empty-time-123"
