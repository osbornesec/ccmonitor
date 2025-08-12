#!/usr/bin/env python3
"""Test CCMonitor with actual Claude conversation data."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.display_formatter import DisplayFormatter
from src.services.file_monitor import FileMonitor
from src.services.jsonl_parser import JSONLParser
from src.services.message_categorizer import MessageCategorizer


def print_header(title: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def test_jsonl_parsing():
    """Test parsing actual Claude JSONL files."""
    print_header("Testing JSONL Parser with Claude Data")

    # Find Claude project directories
    claude_projects_dir = Path.home() / ".claude" / "projects"

    if not claude_projects_dir.exists():
        print(f"❌ Claude projects directory not found: {claude_projects_dir}")
        return

    # Find recent JSONL files
    jsonl_files = list(claude_projects_dir.glob("*/*.jsonl"))

    if not jsonl_files:
        print("❌ No JSONL files found in Claude projects")
        return

    # Sort by modification time and get most recent
    recent_files = sorted(
        jsonl_files, key=lambda f: f.stat().st_mtime, reverse=True
    )[:3]

    print(f"📁 Found {len(jsonl_files)} JSONL files in Claude projects")
    print(f"📊 Testing with {len(recent_files)} most recent files\n")

    parser = JSONLParser(file_age_limit_hours=48)  # Look at last 48 hours
    categorizer = MessageCategorizer()
    formatter = DisplayFormatter()

    for file_path in recent_files:
        print(f"\n📄 File: {file_path.name}")
        print(f"   Project: {file_path.parent.name}")
        print(f"   Size: {file_path.stat().st_size / 1024:.1f} KB")
        print(
            f"   Modified: {datetime.fromtimestamp(file_path.stat().st_mtime):%Y-%m-%d %H:%M:%S}"
        )

        try:
            # Parse the file
            result = parser.parse_file(file_path)

            print(f"\n   ✅ Parsed successfully!")
            print(f"   • Messages: {len(result.entries)}")
            print(f"   • Success rate: {result.statistics.success_rate:.1f}%")
            print(f"   • Conversations: {len(result.conversations)}")
            print(f"   • Errors: {result.statistics.error_details}")

            # Show message type breakdown
            type_counts = {}
            tool_counts = {}

            for entry in result.entries[:100]:  # Analyze first 100 entries
                # Count message types
                msg_type = entry.type
                type_counts[msg_type] = type_counts.get(msg_type, 0) + 1

                # Count tool usage
                if hasattr(entry, "message") and entry.message:
                    if (
                        hasattr(entry.message, "content")
                        and entry.message.content
                    ):
                        for content_item in entry.message.content:
                            if hasattr(content_item, "type"):
                                if content_item.type == "tool_use":
                                    tool_name = getattr(
                                        content_item, "name", "unknown"
                                    )
                                    tool_counts[tool_name] = (
                                        tool_counts.get(tool_name, 0) + 1
                                    )

            print("\n   📊 Message Types:")
            for msg_type, count in sorted(
                type_counts.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"      • {msg_type}: {count}")

            if tool_counts:
                print("\n   🔧 Tool Usage:")
                for tool, count in sorted(
                    tool_counts.items(), key=lambda x: x[1], reverse=True
                )[:10]:
                    print(f"      • {tool}: {count}")

            # Show sample messages with categorization
            print("\n   💬 Sample Messages (first 5):")
            for i, entry in enumerate(result.entries[:5], 1):
                category = categorizer.categorize_message(entry)
                formatted = formatter.format_message(category)

                # Extract key info
                timestamp = (
                    category.timestamp.strftime("%H:%M:%S")
                    if category.timestamp
                    else "unknown"
                )
                summary = (
                    category.summary[:50] + "..."
                    if len(category.summary) > 50
                    else category.summary
                )

                print(f"\n      [{i}] {timestamp} - {category.category.value}")
                print(f"          {summary}")

        except Exception as e:
            print(f"   ❌ Error parsing file: {e}")


async def test_real_time_monitoring():
    """Test real-time monitoring of Claude activity."""
    print_header("Testing Real-Time Monitoring")

    print("🔍 Setting up file monitor for Claude projects...")

    # Create monitor
    monitor = FileMonitor(
        watch_directories=[Path.home() / ".claude" / "projects"],
        file_age_limit_hours=1,  # Only monitor files updated in last hour
        debounce_seconds=0.5,
    )

    # Track new messages
    message_count = 0

    def on_new_message(entry):
        nonlocal message_count
        message_count += 1

        categorizer = MessageCategorizer()
        formatter = DisplayFormatter()

        category = categorizer.categorize_message(entry)
        formatted = formatter.format_message(
            category, max_width=80, compact=True
        )

        print(f"\n🔔 New Message #{message_count}:")
        print(formatted)

    def on_error(error):
        print(f"❌ Monitor Error: {error}")

    # Add callbacks
    monitor.add_message_callback(on_new_message)
    monitor.add_error_callback(on_error)

    # Discover existing files
    files = monitor.discover_jsonl_files()
    print(f"📁 Discovered {len(files)} JSONL files to monitor")

    if files:
        print("\n📄 Monitoring files:")
        for f in files[:5]:  # Show first 5
            print(f"   • {f.name} ({f.parent.name})")
        if len(files) > 5:
            print(f"   ... and {len(files) - 5} more")

    # Start monitoring
    monitor.start()
    print("\n✅ Monitoring started! Watching for new Claude activity...")
    print("   (Make some actions in Claude Code to see real-time updates)")
    print("   Press Ctrl+C to stop monitoring\n")

    try:
        # Run for 30 seconds or until interrupted
        await asyncio.sleep(30)
    except KeyboardInterrupt:
        print("\n⏹️  Stopping monitor...")
    finally:
        monitor.stop()
        print(f"\n📊 Total messages received: {message_count}")


def test_conversation_analysis():
    """Analyze conversations from Claude data."""
    print_header("Testing Conversation Analysis")

    # Find a recent JSONL file
    claude_projects_dir = Path.home() / ".claude" / "projects"
    jsonl_files = list(claude_projects_dir.glob("*/*.jsonl"))

    if not jsonl_files:
        print("❌ No JSONL files found")
        return

    # Get most recent file
    recent_file = max(jsonl_files, key=lambda f: f.stat().st_mtime)

    print(f"📄 Analyzing: {recent_file.name}")
    print(f"   Project: {recent_file.parent.name}\n")

    parser = JSONLParser()
    result = parser.parse_file(recent_file)

    if not result.conversations:
        print("❌ No conversations found")
        return

    categorizer = MessageCategorizer()

    # Analyze each conversation (conversations is a list of ConversationThread objects)
    for conv in result.conversations[:3]:  # First 3 conversations
        session_id = conv.session_id
        entries = conv.messages
        print(f"\n🗨️  Conversation: {session_id[:8]}...")
        print(f"   Messages: {len(entries)}")

        # Get time range from conversation object
        if conv.start_time and conv.end_time:
            duration = conv.end_time - conv.start_time
            print(f"   Duration: {duration}")
            print(f"   Start: {conv.start_time:%Y-%m-%d %H:%M:%S}")

        # Analyze message flow
        user_count = 0
        assistant_count = 0
        tool_count = 0

        for entry in entries:
            if entry.type == "user":
                user_count += 1
            elif entry.type == "assistant":
                assistant_count += 1

            # Check for tools
            if hasattr(entry, "message") and entry.message:
                if hasattr(entry.message, "content") and entry.message.content:
                    for content in entry.message.content:
                        if (
                            hasattr(content, "type")
                            and content.type == "tool_use"
                        ):
                            tool_count += 1

        print(f"\n   📊 Message Breakdown:")
        print(f"      • User messages: {user_count}")
        print(f"      • Assistant messages: {assistant_count}")
        print(f"      • Tool calls: {tool_count}")

        # Show conversation summary
        print(f"\n   📝 Conversation Flow (first 10 messages):")
        for i, entry in enumerate(entries[:10], 1):
            category = categorizer.categorize_message(entry)
            icon = {
                "USER_INPUT": "👤",
                "AI_RESPONSE": "🤖",
                "TOOL_CALL": "🔧",
                "TOOL_RESULT": "📊",
                "SYSTEM_EVENT": "⚙️",
                "META_INFORMATION": "ℹ️",
            }.get(category.category.value, "❓")

            summary = (
                category.summary[:60] + "..."
                if len(category.summary) > 60
                else category.summary
            )
            print(f"      {i:2}. {icon} {summary}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  CCMonitor - Claude Activity Monitor Test Suite")
    print("=" * 60)

    # Test JSONL parsing with real data
    test_jsonl_parsing()

    # Test conversation analysis
    test_conversation_analysis()

    # Test real-time monitoring (async)
    print("\n" + "=" * 60)
    print("  Starting Real-Time Monitoring Test")
    print("  (This will run for 30 seconds or until Ctrl+C)")
    print("=" * 60)

    try:
        asyncio.run(test_real_time_monitoring())
    except KeyboardInterrupt:
        print("\n✅ Test suite completed!")


if __name__ == "__main__":
    main()
