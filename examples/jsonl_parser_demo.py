#!/usr/bin/env python3
"""Example demonstration of the JSONL parser for Claude Code activity logs."""

import json
import tempfile
from pathlib import Path

from src.services.jsonl_parser import (
    JSONLParser,
    StreamingJSONLParser,
    find_claude_activity_files,
    parse_jsonl_file,
)


def create_sample_jsonl_file() -> Path:
    """Create a sample JSONL file for demonstration."""
    sample_entries = [
        {
            "uuid": "msg-001",
            "type": "user",
            "timestamp": "2025-08-12T10:00:00Z",
            "sessionId": "demo-session-1",
            "message": {
                "role": "user",
                "content": (
                    "Help me create a Python script to parse JSON files"
                ),
            },
            "cwd": "/home/user/projects/demo",
            "version": "0.1.0",
        },
        {
            "uuid": "msg-002",
            "type": "assistant",
            "timestamp": "2025-08-12T10:00:30Z",
            "sessionId": "demo-session-1",
            "parentUuid": "msg-001",
            "message": {
                "role": "assistant",
                "content": (
                    "I'll help you create a Python script for parsing JSON files. Let me start by creating a basic structure."
                ),
            },
        },
        {
            "uuid": "msg-003",
            "type": "tool_use",
            "timestamp": "2025-08-12T10:00:45Z",
            "sessionId": "demo-session-1",
            "parentUuid": "msg-002",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "tool-001",
                        "name": "Write",
                        "input": {
                            "file_path": "json_parser.py",
                            "content": (
                                "import json\n\ndef parse_json_file(file_path):\n    with open(file_path, 'r') as f:\n        return json.load(f)\n"
                            ),
                        },
                    }
                ],
            },
        },
        {
            "uuid": "msg-004",
            "type": "tool_use_result",
            "timestamp": "2025-08-12T10:00:50Z",
            "sessionId": "demo-session-1",
            "toolUseResult": {
                "tool_name": "Write",
                "input": {
                    "file_path": "json_parser.py",
                    "content": (
                        "import json\n\ndef parse_json_file(file_path):\n    with open(file_path, 'r') as f:\n        return json.load(f)\n"
                    ),
                },
                "output": "File created successfully",
                "is_error": False,
                "execution_time": 0.05,
            },
        },
        {
            "uuid": "msg-005",
            "type": "user",
            "timestamp": "2025-08-12T10:01:00Z",
            "sessionId": "demo-session-1",
            "parentUuid": "msg-004",
            "message": {
                "role": "user",
                "content": "Great! Can you also add error handling?",
            },
        },
        {
            "uuid": "msg-006",
            "type": "assistant",
            "timestamp": "2025-08-12T10:01:15Z",
            "sessionId": "demo-session-1",
            "parentUuid": "msg-005",
            "message": {
                "role": "assistant",
                "content": (
                    "Absolutely! Let me enhance the script with proper error handling."
                ),
            },
        },
    ]

    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".jsonl",
        delete=False,
        prefix="claude_activity_demo_",
    )

    # Write sample entries
    for entry in sample_entries:
        temp_file.write(json.dumps(entry) + "\n")

    temp_file.close()
    return Path(temp_file.name)


def demo_basic_parsing() -> None:
    """Demonstrate basic JSONL parsing functionality."""
    print("🔍 Creating sample JSONL file...")
    sample_file = create_sample_jsonl_file()

    try:
        print(f"📁 Sample file created: {sample_file}")
        print(f"📊 File size: {sample_file.stat().st_size} bytes")

        # Parse using convenience function
        print("\n🚀 Parsing with convenience function...")
        result = parse_jsonl_file(sample_file)

        print(f"✅ Successfully parsed {len(result.entries)} entries")
        print(f"📈 Success rate: {result.statistics.success_rate:.1f}%")
        print(f"⏱️ Processing time: {result.statistics.processing_time:.3f}s")

        # Show statistics
        stats = result.statistics
        print(f"\n📊 Message type breakdown:")
        print(f"  👤 User messages: {stats.user_messages}")
        print(f"  🤖 Assistant messages: {stats.assistant_messages}")
        print(f"  🔧 Tool calls: {stats.tool_calls}")
        print(f"  📋 Tool results: {stats.tool_results}")

        # Show conversation threads
        print(f"\n💬 Found {len(result.conversations)} conversation(s):")
        for conv in result.conversations:
            print(f"  Session: {conv.session_id}")
            print(f"    📝 Total messages: {conv.total_messages}")
            print(
                f"    👤 User: {conv.user_messages}, 🤖 Assistant: {conv.assistant_messages}"
            )
            print(f"    🕐 Duration: {conv.start_time} to {conv.end_time}")

        # Show first few entries
        print(f"\n📄 First few entries:")
        for i, entry in enumerate(result.entries[:3]):
            print(f"  {i+1}. [{entry.type}] {entry.uuid} - {entry.timestamp}")
            if hasattr(entry.message, "content") and entry.message:
                content = entry.message.content
                if isinstance(content, str):
                    preview = (
                        content[:60] + "..." if len(content) > 60 else content
                    )
                    print(f"     Content: {preview}")

        # Show tool usage summary
        tool_usage = result.get_tool_usage_summary()
        if tool_usage:
            print(f"\n🔨 Tool usage summary:")
            for tool, count in tool_usage.items():
                print(f"  {tool}: {count} uses")

    finally:
        # Cleanup
        sample_file.unlink()
        print(f"\n🧹 Cleaned up sample file")


def demo_streaming_parsing() -> None:
    """Demonstrate streaming JSONL parsing."""
    print("\n" + "=" * 60)
    print("🌊 STREAMING PARSING DEMO")
    print("=" * 60)

    # Create streaming parser
    parser = StreamingJSONLParser(buffer_size=1024)

    # Simulate streaming data
    jsonl_lines = [
        json.dumps(
            {
                "uuid": f"stream-{i:03d}",
                "type": "user",
                "timestamp": f"2025-08-12T10:{i:02d}:00Z",
                "message": {"content": f"Streaming message {i}"},
            }
        )
        + "\n"
        for i in range(5)
    ]

    print("📡 Simulating streaming data...")

    all_entries = []

    # Feed data in chunks
    for i, line in enumerate(jsonl_lines):
        print(f"  📨 Feeding chunk {i+1}: {len(line)} bytes")

        # Split line into smaller chunks to simulate real streaming
        chunk_size = len(line) // 3 + 1
        for j in range(0, len(line), chunk_size):
            chunk = line[j : j + chunk_size]
            entries = list(parser.feed_data(chunk))
            all_entries.extend(entries)

            if entries:
                print(f"    ✨ Parsed {len(entries)} complete entries")

    # Process any remaining data
    final_entries = list(parser.finalize())
    all_entries.extend(final_entries)

    if final_entries:
        print(f"  🏁 Finalized {len(final_entries)} remaining entries")

    print(f"\n📊 Streaming results:")
    print(f"  Total entries parsed: {len(all_entries)}")
    print(f"  Parser statistics:")
    print(f"    Total lines: {parser.statistics.total_lines}")
    print(f"    Valid entries: {parser.statistics.valid_entries}")

    for entry in all_entries[:3]:  # Show first 3
        print(
            f"    📄 {entry.uuid}: {entry.message.content if entry.message else 'No content'}"
        )


def demo_advanced_features() -> None:
    """Demonstrate advanced parser features."""
    print("\n" + "=" * 60)
    print("⚡ ADVANCED FEATURES DEMO")
    print("=" * 60)

    # Test with validation disabled for performance
    print("🚀 Testing high-performance mode (validation disabled)...")
    sample_file = create_sample_jsonl_file()

    try:
        # Parse with validation disabled
        fast_parser = JSONLParser(skip_validation=True)
        result = fast_parser.parse_file(sample_file)

        print(
            f"⚡ Fast parsing completed in {result.statistics.processing_time:.4f}s"
        )
        print(f"📊 Processed {result.statistics.valid_entries} entries")

        # Test file age filtering
        print(f"\n📅 Testing file age filtering...")
        old_parser = JSONLParser(file_age_limit_hours=0)  # Skip all files
        old_result = old_parser.parse_file(sample_file)

        print(f"⏰ Age-limited parser result:")
        print(f"  Entries parsed: {len(old_result.entries)}")
        print(f"  Errors: {len(old_result.statistics.error_details)}")
        if old_result.statistics.error_details:
            error = old_result.statistics.error_details[0]
            print(f"  Error type: {error['error_type']}")
            print(f"  Error message: {error['error_message']}")

    finally:
        sample_file.unlink()


def demo_error_handling() -> None:
    """Demonstrate error handling capabilities."""
    print("\n" + "=" * 60)
    print("🛡️ ERROR HANDLING DEMO")
    print("=" * 60)

    # Create file with mixed valid and invalid content
    mixed_content = [
        '{"uuid": "good-001", "type": "user", "timestamp": "2025-08-12T10:00:00Z", "message": {"content": "Valid entry"}}',
        '{"uuid": "bad-001", "type": "user", "timestamp": "invalid-json"',  # Missing closing brace
        "",  # Empty line
        '{"uuid": "good-002", "type": "assistant", "timestamp": "2025-08-12T10:01:00Z", "message": {"content": "Another valid entry"}}',
        '{"invalid": "json", "structure": "but valid json"}',  # Valid JSON but invalid structure
        "not json at all",  # Not JSON
    ]

    temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".jsonl",
        delete=False,
    )

    try:
        # Write mixed content
        for line in mixed_content:
            temp_file.write(line + "\n")
        temp_file.close()

        print(
            f"📝 Created test file with {len(mixed_content)} lines (mixed valid/invalid)"
        )

        # Parse with error recovery
        parser = JSONLParser()
        result = parser.parse_file(temp_file.name)

        print(f"\n📊 Error recovery results:")
        print(f"  📥 Total lines processed: {result.statistics.total_lines}")
        print(f"  ✅ Valid entries: {result.statistics.valid_entries}")
        print(f"  ❌ Parse errors: {result.statistics.parse_errors}")
        print(f"  ⚠️ Validation errors: {result.statistics.validation_errors}")
        print(f"  ⏭️ Skipped lines: {result.statistics.skipped_lines}")
        print(f"  📈 Success rate: {result.statistics.success_rate:.1f}%")

        print(f"\n🔍 Error details:")
        for i, error in enumerate(
            result.statistics.error_details[:3], 1
        ):  # Show first 3 errors
            print(f"  {i}. Line {error['line_number']}: {error['error_type']}")
            print(f"     Message: {error['error_message']}")
            if error["raw_line"]:
                preview = (
                    error["raw_line"][:50] + "..."
                    if len(error["raw_line"]) > 50
                    else error["raw_line"]
                )
                print(f"     Raw line: {preview}")

        print(
            f"\n✨ Successfully recovered and parsed {len(result.entries)} valid entries:"
        )
        for entry in result.entries:
            print(f"  📄 {entry.uuid}: {entry.type}")

    finally:
        Path(temp_file.name).unlink()


def demo_file_discovery() -> None:
    """Demonstrate finding Claude activity files."""
    print("\n" + "=" * 60)
    print("🔍 FILE DISCOVERY DEMO")
    print("=" * 60)

    # Check if real Claude directory exists
    claude_dir = Path("~/.claude/projects").expanduser()

    if claude_dir.exists():
        print(f"📁 Found Claude projects directory: {claude_dir}")
        files = find_claude_activity_files()

        if files:
            print(f"🎯 Found {len(files)} JSONL files:")
            for file_path in files[:5]:  # Show first 5
                size = file_path.stat().st_size
                print(f"  📄 {file_path.name} ({size:,} bytes)")

            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more files")

            # Try parsing the first file (if it exists and is recent)
            if files:
                first_file = files[0]
                print(f"\n🔬 Analyzing first file: {first_file.name}")

                try:
                    result = parse_jsonl_file(
                        first_file, file_age_limit_hours=168
                    )  # 1 week

                    if result.statistics.error_details and any(
                        e["error_type"] == "file_too_old"
                        for e in result.statistics.error_details
                    ):
                        print("⏰ File is older than 1 week, skipped for demo")
                    else:
                        print(f"  📊 Entries: {len(result.entries)}")
                        print(
                            f"  💬 Conversations: {len(result.conversations)}"
                        )
                        print(
                            f"  📈 Success rate: {result.statistics.success_rate:.1f}%"
                        )

                        if result.conversations:
                            latest = max(
                                result.conversations,
                                key=lambda c: c.start_time,
                            )
                            print(
                                f"  🕐 Latest conversation: {latest.session_id}"
                            )
                            print(f"     Start: {latest.start_time}")
                            print(f"     Messages: {latest.total_messages}")

                except Exception as e:
                    print(f"  ⚠️ Could not parse file: {e}")
        else:
            print("📭 No JSONL files found in Claude projects directory")
    else:
        print(f"📂 Claude projects directory not found: {claude_dir}")
        print("💡 This is normal if you haven't used Claude Code yet")


def main() -> None:
    """Run all demonstrations."""
    print("🎯 CCMonitor JSONL Parser Demonstration")
    print("=" * 60)

    try:
        demo_basic_parsing()
        demo_streaming_parsing()
        demo_advanced_features()
        demo_error_handling()
        demo_file_discovery()

        print("\n" + "=" * 60)
        print("🎉 All demonstrations completed successfully!")
        print("💡 The JSONL parser is ready for use in CCMonitor")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Demo failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
