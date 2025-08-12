#!/usr/bin/env python3
"""Demo script for message categorization and display system."""


from rich.console import Console
from rich.panel import Panel

from src.services.display_formatter import DisplayFormatter
from src.services.message_categorizer import (
    MessageCategorizer,
    MessageCategory,
    MessagePriority,
)
from src.services.models import (
    JSONLEntry,
    Message,
    MessageRole,
    MessageType,
    ToolUseResult,
)


def create_sample_messages() -> list[JSONLEntry]:
    """Create sample messages for demonstration."""
    messages = []

    # User message
    user_msg = JSONLEntry(
        uuid="user-001",
        type=MessageType.USER,
        timestamp="2024-08-12T10:00:00Z",
        sessionId="demo-session",
        message=Message(
            role=MessageRole.USER,
            content="Can you help me create a Python script to analyze some data?",
        ),
    )
    messages.append(user_msg)

    # Assistant response
    assistant_msg = JSONLEntry(
        uuid="assistant-001",
        type=MessageType.ASSISTANT,
        timestamp="2024-08-12T10:00:30Z",
        sessionId="demo-session",
        parentUuid="user-001",
        message=Message(
            role=MessageRole.ASSISTANT,
            content="I'll help you create a Python script for data analysis. Let me first check if you have any existing data files.",
        ),
    )
    messages.append(assistant_msg)

    # Tool call
    tool_call_msg = JSONLEntry(
        uuid="tool-call-001",
        type=MessageType.TOOL_USE,
        timestamp="2024-08-12T10:01:00Z",
        sessionId="demo-session",
        parentUuid="assistant-001",
        message=Message(
            role=MessageRole.ASSISTANT,
            content="",
            tool="Read",
            parameters={"file_path": "/home/user/data.csv"},
        ),
    )
    messages.append(tool_call_msg)

    # Tool result
    tool_result_msg = JSONLEntry(
        uuid="tool-result-001",
        type=MessageType.TOOL_USE_RESULT,
        timestamp="2024-08-12T10:01:05Z",
        sessionId="demo-session",
        parentUuid="tool-call-001",
        toolUseID="tool-call-001",
        toolUseResult=ToolUseResult(
            tool_name="Read",
            input={"file_path": "/home/user/data.csv"},
            output="id,name,value\n1,Alice,100\n2,Bob,150\n3,Charlie,200",
            execution_time=5.2,
        ),
    )
    messages.append(tool_result_msg)

    # System event
    system_msg = JSONLEntry(
        uuid="system-001",
        type=MessageType.SYSTEM,
        timestamp="2024-08-12T10:02:00Z",
        sessionId="demo-session",
        message=Message(
            role=MessageRole.SYSTEM,
            content="Session statistics: 2 user messages, 1 assistant message, 1 tool call",
        ),
    )
    messages.append(system_msg)

    # Git metadata
    git_msg = JSONLEntry(
        uuid="git-001",
        type=MessageType.META,
        timestamp="2024-08-12T10:02:30Z",
        sessionId="demo-session",
        gitBranch="feature-data-analysis",
        cwd="/home/user/projects/analysis",
        message=Message(
            role=MessageRole.SYSTEM,
            content="Working directory changed to /home/user/projects/analysis",
        ),
    )
    messages.append(git_msg)

    return messages


def demo_categorization():
    """Demonstrate message categorization."""
    console = Console()
    console.print("\n[bold blue]🚀 Message Categorization Demo[/bold blue]\n")

    # Create sample messages
    messages = create_sample_messages()
    console.print(f"📝 Created {len(messages)} sample messages\n")

    # Initialize categorizer
    categorizer = MessageCategorizer(max_display_length=200)

    # Categorize messages
    console.print("[bold]📊 Categorizing messages...[/bold]")
    categorized_messages = categorizer.categorize_batch(messages)

    # Display categorization results
    for i, categorized in enumerate(categorized_messages, 1):
        console.print(f"\n[dim]Message {i}:[/dim]")

        # Create info panel
        info_lines = []
        info_lines.append(f"UUID: {categorized.entry.uuid}")
        info_lines.append(f"Type: {categorized.entry.type.value}")
        info_lines.append(f"Category: {categorized.category.value}")
        info_lines.append(f"Priority: {categorized.priority.value}")
        info_lines.append(f"Timestamp: {categorized.timestamp_relative}")

        info_text = "\n".join(info_lines)

        # Color based on category
        category_colors = {
            MessageCategory.USER_INPUT: "blue",
            MessageCategory.AI_RESPONSE: "green",
            MessageCategory.TOOL_CALL: "orange3",
            MessageCategory.TOOL_RESULT: "cyan",
            MessageCategory.SYSTEM_EVENT: "yellow",
            MessageCategory.META_INFORMATION: "magenta",
        }

        color = category_colors.get(categorized.category, "white")

        console.print(
            Panel(
                f"[bold]{categorized.summary}[/bold]\n\n{categorized.display_text}\n\n[dim]{info_text}[/dim]",
                border_style=color,
                title=f"[{color}]{categorized.category.value.upper()}[/{color}]",
            ),
        )

    # Show statistics
    console.print("\n[bold green]📈 Statistics[/bold green]")
    stats = categorizer.get_statistics(categorized_messages)

    console.print(f"Total messages: {stats['total_messages']}")
    console.print(f"Messages with errors: {stats['error_count']}")
    console.print(f"Truncated messages: {stats['truncated_count']}")

    # Category breakdown
    console.print("\n[bold]By Category:[/bold]")
    for category, count in stats["by_category"].items():
        color = category_colors.get(category, "white")
        console.print(f"  [{color}]• {category.value}: {count}[/{color}]")

    # Priority breakdown
    console.print("\n[bold]By Priority:[/bold]")
    priority_colors = {
        MessagePriority.CRITICAL: "red",
        MessagePriority.HIGH: "orange3",
        MessagePriority.MEDIUM: "yellow",
        MessagePriority.LOW: "green",
    }

    for priority, count in stats["by_priority"].items():
        color = priority_colors.get(priority, "white")
        console.print(f"  [{color}]• {priority.value}: {count}[/{color}]")


def demo_display_formatting():
    """Demonstrate display formatting."""
    console = Console()
    console.print("\n[bold blue]🎨 Display Formatting Demo[/bold blue]\n")

    # Create sample messages and categorize them
    messages = create_sample_messages()
    categorizer = MessageCategorizer()
    categorized_messages = categorizer.categorize_batch(messages)

    # Initialize display formatter
    formatter = DisplayFormatter(console)

    # Show compact format
    console.print("[bold]Compact Format:[/bold]\n")
    for msg in categorized_messages[:3]:  # Show first 3
        formatted = formatter.format_message(msg, compact=True)
        console.print(formatted)

    console.print("\n" + "=" * 50 + "\n")

    # Show full format
    console.print("[bold]Full Format:[/bold]\n")
    for msg in categorized_messages[3:4]:  # Show 1 detailed
        formatted = formatter.format_message(msg, show_metadata=True)
        console.print(formatted)
        console.print()

    # Show conversation summary
    console.print("=" * 50 + "\n")
    summary = formatter.format_conversation_summary(categorized_messages)
    console.print(
        Panel(summary, title="[bold cyan]Conversation Summary[/bold cyan]"),
    )

    # Show statistics
    stats = categorizer.get_statistics(categorized_messages)
    stats_display = formatter.format_statistics(stats)
    console.print(
        Panel(stats_display, title="[bold magenta]Statistics[/bold magenta]"),
    )


def demo_tool_operations():
    """Demonstrate tool operation grouping."""
    console = Console()
    console.print("\n[bold blue]🔧 Tool Operations Demo[/bold blue]\n")

    # Create sample messages with tool operations
    messages = create_sample_messages()
    categorizer = MessageCategorizer()

    # Group tool operations
    tool_groups = categorizer.group_tool_operations(messages)
    console.print(f"Found {len(tool_groups)} tool operation groups\n")

    for i, group in enumerate(tool_groups, 1):
        console.print(f"[bold]Group {i}: {group.summary}[/bold]")
        console.print(f"  Tool: {group.tool_name}")
        console.print(f"  Success: {'✅' if group.success else '❌'}")
        console.print(f"  Execution time: {group.execution_time:.1f}s")
        console.print(f"  Call UUID: {group.tool_call.uuid}")
        if group.tool_result:
            console.print(f"  Result UUID: {group.tool_result.uuid}")
        console.print()


def demo_message_threads():
    """Demonstrate message threading."""
    console = Console()
    console.print("\n[bold blue]🧵 Message Threading Demo[/bold blue]\n")

    # Create sample messages
    messages = create_sample_messages()
    categorizer = MessageCategorizer()

    # Create message threads
    threads = categorizer.create_message_threads(messages)
    console.print(f"Found {len(threads)} conversation threads\n")

    for i, thread in enumerate(threads, 1):
        console.print(f"[bold]Thread {i}: {thread.session_id}[/bold]")
        console.print(f"  Messages: {len(thread.messages)}")
        console.print(f"  User messages: {thread.user_message_count}")
        console.print(
            f"  Assistant messages: {thread.assistant_message_count}",
        )
        console.print(f"  Tool calls: {thread.tool_call_count}")
        console.print(f"  Duration: {thread.duration:.1f}s")
        console.print(f"  Start: {thread.start_time}")
        if thread.end_time:
            console.print(f"  End: {thread.end_time}")
        console.print()


def main():
    """Run all demos."""
    console = Console()
    console.print(
        "[bold green]🎯 CCMonitor Message Categorization System Demo[/bold green]",
    )
    console.print("=" * 60)

    try:
        demo_categorization()
        demo_display_formatting()
        demo_tool_operations()
        demo_message_threads()

        console.print(
            "\n[bold green]✅ Demo completed successfully![/bold green]",
        )
        console.print(
            "\n[dim]The message categorization system is working correctly.[/dim]",
        )

    except Exception as e:
        console.print(f"\n[bold red]❌ Demo failed: {e}[/bold red]")
        raise


if __name__ == "__main__":
    main()
