"""Tests for message categorization system."""

from datetime import UTC, datetime

import pytest

from src.services.message_categorizer import (
    CategorizedMessage,
    MessageCategorizer,
    MessageCategory,
    MessagePriority,
    MessageThread,
    ToolCallGroup,
)
from src.services.models import (
    JSONLEntry,
    Message,
    MessageRole,
    MessageType,
    ToolUseResult,
)

# Test constants
MAX_DISPLAY_LENGTH = 100
EXPECTED_MESSAGE_COUNT = 2
EXPECTED_THREAD_MESSAGE_COUNT = 2
EXPECTED_TOTAL_STATS = 3
EXPECTED_HIGH_PRIORITY_COUNT = 2
EXPECTED_EXECUTION_TIME = 5.0
EXPECTED_THREAD_DURATION = 60.0


class TestMessageCategorizer:
    """Test cases for MessageCategorizer."""

    @pytest.fixture
    def categorizer(self) -> MessageCategorizer:
        """Create a MessageCategorizer instance."""
        return MessageCategorizer()

    @pytest.fixture
    def sample_user_entry(self) -> JSONLEntry:
        """Create a sample user message entry."""
        return JSONLEntry(
            uuid="user-123",
            type=MessageType.USER,
            timestamp="2024-01-01T10:00:00Z",
            sessionId="session-1",
            message=Message(
                role=MessageRole.USER,
                content="Can you help me write a Python function?",
            ),
        )

    @pytest.fixture
    def sample_assistant_entry(self) -> JSONLEntry:
        """Create a sample assistant message entry."""
        return JSONLEntry(
            uuid="assistant-123",
            type=MessageType.ASSISTANT,
            timestamp="2024-01-01T10:01:00Z",
            sessionId="session-1",
            parentUuid="user-123",
            message=Message(
                role=MessageRole.ASSISTANT,
                content=(
                    "I'll help you write a Python function. "
                    "Let me start by reading your code."
                ),
            ),
        )

    @pytest.fixture
    def sample_tool_call_entry(self) -> JSONLEntry:
        """Create a sample tool call entry."""
        return JSONLEntry(
            uuid="tool-call-123",
            type=MessageType.TOOL_USE,
            timestamp="2024-01-01T10:01:30Z",
            sessionId="session-1",
            parentUuid="assistant-123",
            message=Message(
                role=MessageRole.ASSISTANT,
                content="",
                tool="Read",
                parameters={"file_path": "/home/user/script.py"},
            ),
        )

    @pytest.fixture
    def sample_tool_result_entry(self) -> JSONLEntry:
        """Create a sample tool result entry."""
        return JSONLEntry(
            uuid="tool-result-123",
            type=MessageType.TOOL_USE_RESULT,
            timestamp="2024-01-01T10:01:35Z",
            sessionId="session-1",
            parentUuid="tool-call-123",
            toolUseID="tool-call-123",
            toolUseResult=ToolUseResult(
                tool_name="Read",
                input={"file_path": "/home/user/script.py"},
                output="def hello():\n    print('Hello, World!')",
            ),
        )

    def test_categorize_user_message(
        self,
        categorizer: MessageCategorizer,
        sample_user_entry: JSONLEntry,
    ) -> None:
        """Test categorization of user messages."""
        result = categorizer.categorize_message(sample_user_entry)

        assert result.category == MessageCategory.USER_INPUT
        assert result.priority == MessagePriority.HIGH
        assert result.summary == "User asks about writing a Python function"
        assert result.display_text.startswith("Can you help me")
        assert (
            len(result.display_text) <= MAX_DISPLAY_LENGTH
        )  # Should be truncated if too long

    def test_categorize_assistant_message(
        self,
        categorizer: MessageCategorizer,
        sample_assistant_entry: JSONLEntry,
    ) -> None:
        """Test categorization of assistant messages."""
        result = categorizer.categorize_message(sample_assistant_entry)

        assert result.category == MessageCategory.AI_RESPONSE
        assert result.priority == MessagePriority.HIGH
        assert result.summary.startswith("Claude responds")
        assert "help you write" in result.display_text

    def test_categorize_tool_call(
        self,
        categorizer: MessageCategorizer,
        sample_tool_call_entry: JSONLEntry,
    ) -> None:
        """Test categorization of tool calls."""
        result = categorizer.categorize_message(sample_tool_call_entry)

        assert result.category == MessageCategory.TOOL_CALL
        assert result.priority == MessagePriority.MEDIUM
        assert "Reading file" in result.summary
        assert "script.py" in result.display_text
        assert result.metadata["tool_name"] == "Read"
        assert result.metadata["file_path"] == "/home/user/script.py"

    def test_categorize_tool_result(
        self,
        categorizer: MessageCategorizer,
        sample_tool_result_entry: JSONLEntry,
    ) -> None:
        """Test categorization of tool results."""
        result = categorizer.categorize_message(sample_tool_result_entry)

        assert result.category == MessageCategory.TOOL_RESULT
        assert result.priority == MessagePriority.LOW
        assert "File read successfully" in result.summary
        assert "def hello()" in result.display_text
        assert not result.has_errors

    def test_group_tool_operations(
        self,
        categorizer: MessageCategorizer,
        sample_tool_call_entry: JSONLEntry,
        sample_tool_result_entry: JSONLEntry,
    ) -> None:
        """Test grouping of tool call and result pairs."""
        entries = [sample_tool_call_entry, sample_tool_result_entry]
        groups = categorizer.group_tool_operations(entries)

        assert len(groups) == 1
        group = groups[0]
        assert isinstance(group, ToolCallGroup)
        assert group.tool_call.uuid == "tool-call-123"
        assert group.tool_result is not None
        assert group.tool_result.uuid == "tool-result-123"
        assert group.tool_name == "Read"
        assert group.success is True

    def test_create_message_threads(
        self,
        categorizer: MessageCategorizer,
        sample_user_entry: JSONLEntry,
        sample_assistant_entry: JSONLEntry,
    ) -> None:
        """Test creation of message threads."""
        entries = [sample_user_entry, sample_assistant_entry]
        threads = categorizer.create_message_threads(entries)

        assert len(threads) == 1
        thread = threads[0]
        assert isinstance(thread, MessageThread)
        assert thread.session_id == "session-1"
        assert len(thread.messages) == EXPECTED_THREAD_MESSAGE_COUNT
        assert thread.user_message_count == 1
        assert thread.assistant_message_count == 1

    def test_extract_code_from_content(
        self,
        categorizer: MessageCategorizer,
    ) -> None:
        """Test code extraction from message content."""
        content_with_code = """
        Here's a Python function:

        ```python
        def greet(name):
            return f"Hello, {name}!"
        ```

        This function takes a name parameter.
        """

        code_blocks = categorizer.extract_code_blocks(content_with_code)
        assert len(code_blocks) == 1
        assert code_blocks[0]["language"] == "python"
        assert "def greet(name)" in code_blocks[0]["code"]

    def test_detect_file_operations(
        self,
        categorizer: MessageCategorizer,
    ) -> None:
        """Test detection of file operations from tool calls."""
        # Mock tool call for file read
        file_read_params = {"file_path": "/home/user/test.py"}
        result = categorizer.detect_file_operation("Read", file_read_params)

        assert result["operation_type"] == "read"
        assert result["file_path"] == "/home/user/test.py"
        assert result["file_name"] == "test.py"

    def test_calculate_conversation_metrics(
        self,
        categorizer: MessageCategorizer,
        sample_user_entry: JSONLEntry,
        sample_assistant_entry: JSONLEntry,
    ) -> None:
        """Test calculation of conversation metrics."""
        entries = [sample_user_entry, sample_assistant_entry]
        metrics = categorizer.calculate_conversation_metrics(entries)

        assert metrics["total_messages"] == EXPECTED_MESSAGE_COUNT
        assert metrics["user_messages"] == 1
        assert metrics["assistant_messages"] == 1
        assert metrics["tool_calls"] == 0
        assert "duration" in metrics
        assert "messages_per_minute" in metrics

    def test_categorize_system_message(
        self,
        categorizer: MessageCategorizer,
    ) -> None:
        """Test categorization of system messages."""
        system_entry = JSONLEntry(
            uuid="system-123",
            type=MessageType.SYSTEM,
            timestamp="2024-01-01T10:00:00Z",
            sessionId="session-1",
            message=Message(
                role=MessageRole.SYSTEM,
                content="Session started with Claude Code v1.2.3",
            ),
        )

        result = categorizer.categorize_message(system_entry)

        assert result.category == MessageCategory.SYSTEM_EVENT
        assert result.priority == MessagePriority.LOW
        assert "Session started" in result.summary

    def test_categorize_git_event(
        self,
        categorizer: MessageCategorizer,
    ) -> None:
        """Test categorization of git-related events."""
        git_entry = JSONLEntry(
            uuid="git-123",
            type=MessageType.META,
            timestamp="2024-01-01T10:00:00Z",
            sessionId="session-1",
            gitBranch="feature-branch",
            message=Message(
                role=MessageRole.SYSTEM,
                content="Changed to branch: feature-branch",
            ),
        )

        result = categorizer.categorize_message(git_entry)

        assert result.category == MessageCategory.META_INFORMATION
        assert "Git branch" in result.summary
        assert "feature-branch" in result.display_text

    def test_handle_malformed_message(
        self,
        categorizer: MessageCategorizer,
    ) -> None:
        """Test handling of malformed messages."""
        malformed_entry = JSONLEntry(
            uuid="malformed-123",
            type=MessageType.USER,
            timestamp="invalid-timestamp",
        )

        result = categorizer.categorize_message(malformed_entry)

        # Should still categorize but mark as having issues
        assert result.category == MessageCategory.USER_INPUT
        assert result.has_errors is True
        assert "malformed" in result.summary.lower()

    def test_batch_categorization(
        self,
        categorizer: MessageCategorizer,
        sample_user_entry: JSONLEntry,
        sample_assistant_entry: JSONLEntry,
    ) -> None:
        """Test batch categorization of multiple messages."""
        entries = [sample_user_entry, sample_assistant_entry]
        results = categorizer.categorize_batch(entries)

        assert len(results) == EXPECTED_MESSAGE_COUNT
        assert all(isinstance(r, CategorizedMessage) for r in results)
        assert results[0].category == MessageCategory.USER_INPUT
        assert results[1].category == MessageCategory.AI_RESPONSE

    def test_filter_by_category(
        self,
        categorizer: MessageCategorizer,
        sample_user_entry: JSONLEntry,
        sample_assistant_entry: JSONLEntry,
    ) -> None:
        """Test filtering messages by category."""
        entries = [sample_user_entry, sample_assistant_entry]
        categorized = categorizer.categorize_batch(entries)

        user_messages = categorizer.filter_by_category(
            categorized,
            MessageCategory.USER_INPUT,
        )
        assert len(user_messages) == 1
        assert user_messages[0].category == MessageCategory.USER_INPUT

    def test_search_within_messages(
        self,
        categorizer: MessageCategorizer,
        sample_user_entry: JSONLEntry,
    ) -> None:
        """Test searching within message content."""
        entries = [sample_user_entry]
        categorized = categorizer.categorize_batch(entries)

        results = categorizer.search_messages(categorized, "Python function")
        assert len(results) == 1
        assert "Python function" in results[0].display_text

    def test_get_statistics(
        self,
        categorizer: MessageCategorizer,
        sample_user_entry: JSONLEntry,
        sample_assistant_entry: JSONLEntry,
        sample_tool_call_entry: JSONLEntry,
    ) -> None:
        """Test getting categorization statistics."""
        entries = [
            sample_user_entry,
            sample_assistant_entry,
            sample_tool_call_entry,
        ]
        categorized = categorizer.categorize_batch(entries)

        stats = categorizer.get_statistics(categorized)

        assert stats["total_messages"] == EXPECTED_TOTAL_STATS
        assert stats["by_category"][MessageCategory.USER_INPUT] == 1
        assert stats["by_category"][MessageCategory.AI_RESPONSE] == 1
        assert stats["by_category"][MessageCategory.TOOL_CALL] == 1
        assert (
            stats["by_priority"][MessagePriority.HIGH]
            == EXPECTED_HIGH_PRIORITY_COUNT
        )
        assert stats["by_priority"][MessagePriority.MEDIUM] == 1


class TestToolCallGroup:
    """Test cases for ToolCallGroup functionality."""

    def test_tool_call_group_creation(self) -> None:
        """Test creation of tool call groups."""
        tool_call = JSONLEntry(
            uuid="call-123",
            type=MessageType.TOOL_USE,
            timestamp="2024-01-01T10:00:00Z",
            sessionId="session-1",
            message=Message(
                content="",
                tool="Read",
                parameters={"file_path": "test.py"},
            ),
        )

        tool_result = JSONLEntry(
            uuid="result-123",
            type=MessageType.TOOL_USE_RESULT,
            timestamp="2024-01-01T10:00:05Z",
            sessionId="session-1",
            toolUseID="call-123",
            toolUseResult=ToolUseResult(
                tool_name="Read",
                input={"file_path": "test.py"},
                output="print('hello')",
            ),
        )

        group = ToolCallGroup(
            tool_call=tool_call,
            tool_result=tool_result,
            tool_name="Read",
        )

        assert group.tool_name == "Read"
        assert group.success is True
        assert group.execution_time == EXPECTED_EXECUTION_TIME
        assert "Reading test.py" in group.summary


class TestMessageThread:
    """Test cases for MessageThread functionality."""

    def test_message_thread_creation(self) -> None:
        """Test creation of message threads."""
        messages = [
            JSONLEntry(
                uuid="user-1",
                type=MessageType.USER,
                timestamp="2024-01-01T10:00:00Z",
                sessionId="session-1",
                message=Message(role=MessageRole.USER, content="Hello"),
            ),
            JSONLEntry(
                uuid="assistant-1",
                type=MessageType.ASSISTANT,
                timestamp="2024-01-01T10:01:00Z",
                sessionId="session-1",
                parentUuid="user-1",
                message=Message(
                    role=MessageRole.ASSISTANT,
                    content="Hi there!",
                ),
            ),
        ]

        thread = MessageThread(
            session_id="session-1",
            messages=messages,
            start_time=datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
            end_time=datetime(2024, 1, 1, 10, 1, 0, tzinfo=UTC),
        )

        assert thread.session_id == "session-1"
        assert len(thread.messages) == EXPECTED_THREAD_MESSAGE_COUNT
        assert thread.user_message_count == 1
        assert thread.assistant_message_count == 1
        assert thread.duration == EXPECTED_THREAD_DURATION
