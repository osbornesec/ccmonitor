# CCMonitor JSONL Parser

A comprehensive JSONL parsing engine for Claude Code activity logs with error recovery, streaming support, and advanced filtering capabilities.

## Features

### 🚀 Core Parsing
- **High-performance JSONL parsing** with streaming support
- **Error recovery** - continues parsing after malformed lines
- **Memory-efficient** processing for large files
- **Type-safe validation** using Pydantic models
- **File age filtering** - skip files older than configured limit (respects user requirement)

### 📊 Message Types Supported
- `user` - User messages and inputs
- `assistant` - Claude's responses
- `tool_use`/`tool_call` - Tool invocations
- `tool_use_result`/`tool_result` - Tool outputs
- `system` - System messages and hooks
- `hook` - Hook system outputs
- `meta` - Metadata entries

### 🔧 Advanced Features
- **Streaming parser** for real-time processing
- **Conversation threading** - groups messages by session
- **Tool usage tracking** - summarizes tool calls and results
- **Comprehensive statistics** - success rates, error counts, timing
- **Async/await support** for non-blocking processing
- **Batch file processing** - parse multiple files efficiently

## Quick Start

### Basic Usage

```python
from src.services.jsonl_parser import parse_jsonl_file

# Parse a single JSONL file
result = parse_jsonl_file("path/to/claude_activity.jsonl")

print(f"Parsed {len(result.entries)} entries")
print(f"Success rate: {result.statistics.success_rate:.1f}%")

# Access conversation threads
for conversation in result.conversations:
    print(f"Session {conversation.session_id}: {conversation.total_messages} messages")
```

### Streaming Parser

```python
from src.services.jsonl_parser import StreamingJSONLParser

parser = StreamingJSONLParser(buffer_size=8192)

# Feed data chunks
for chunk in data_stream:
    entries = list(parser.feed_data(chunk))
    for entry in entries:
        print(f"Processed: {entry.uuid}")

# Process remaining data
final_entries = list(parser.finalize())
```

### Advanced Configuration

```python
from src.services.jsonl_parser import JSONLParser

parser = JSONLParser(
    skip_validation=True,           # Skip validation for performance
    max_line_length=2_000_000,     # Maximum line length
    encoding="utf-8",               # File encoding
    file_age_limit_hours=24,        # Skip files older than 24 hours
)

result = parser.parse_file("activity.jsonl")
```

## Data Models

### JSONLEntry
Main entry model representing a single JSONL line:

```python
class JSONLEntry(BaseModel):
    uuid: str                           # Unique message ID
    type: MessageType                   # Message type (user/assistant/tool_use/etc.)
    timestamp: str                      # ISO timestamp
    session_id: str | None             # Session identifier
    parent_uuid: str | None            # Parent message for threading
    message: Message | None            # Message content
    tool_use_result: ToolUseResult | None  # Tool result data
    cwd: str | None                    # Working directory
    git_branch: str | None             # Git branch
    version: str | None                # Claude Code version
    is_meta: bool | None               # Metadata flag
    tool_use_id: str | None            # Tool use identifier
```

### Message Content Types
- **TextContent** - Plain text messages
- **ToolUseContent** - Tool invocation with parameters
- **ToolResultContent** - Tool execution results
- **ImageContent** - Image attachments

### ParseResult
Complete parsing result with statistics:

```python
class ParseResult(BaseModel):
    entries: list[JSONLEntry]          # Parsed entries
    statistics: ParseStatistics        # Parsing statistics
    conversations: list[ConversationThread]  # Grouped conversations
    file_path: str | None              # Source file path
```

## Error Handling

The parser provides robust error handling:

### Error Recovery
- **Malformed JSON** - Logs error, skips line, continues parsing
- **Missing fields** - Uses defaults where possible
- **Invalid data types** - Attempts type coercion
- **Encoding issues** - Handles different character encodings
- **Large files** - Memory-efficient streaming processing

### Error Statistics
```python
result = parser.parse_file("file.jsonl")
stats = result.statistics

print(f"Total lines: {stats.total_lines}")
print(f"Valid entries: {stats.valid_entries}")
print(f"Parse errors: {stats.parse_errors}")
print(f"Success rate: {stats.success_rate:.1f}%")

# Detailed error information
for error in stats.error_details:
    print(f"Line {error['line_number']}: {error['error_type']}")
    print(f"  Message: {error['error_message']}")
```

## Performance Optimization

### High-Performance Mode
```python
# Disable Pydantic validation for speed
parser = JSONLParser(skip_validation=True)
result = parser.parse_file("large_file.jsonl")
```

### Memory Efficiency
```python
# Stream large files without loading into memory
parser = JSONLParser()
for entry in parser.parse_stream(open("large_file.jsonl")):
    process_entry(entry)
```

### File Age Filtering
```python
# Skip files older than specified limit (addresses user requirement)
parser = JSONLParser(file_age_limit_hours=24)  # Only process recent files
result = parser.parse_file("old_file.jsonl")   # Will be skipped if too old
```

## API Reference

### JSONLParser Class

#### Constructor
```python
JSONLParser(
    skip_validation: bool = False,      # Skip Pydantic validation
    max_line_length: int = 1_000_000,   # Maximum line length
    encoding: str = "utf-8",            # File encoding  
    file_age_limit_hours: int = 24,     # File age limit in hours
)
```

#### Methods
- `parse_file(file_path)` - Parse complete JSONL file
- `parse_stream(stream)` - Parse from text stream
- `parse_multiple_files(file_paths)` - Parse multiple files
- `parse_file_async(file_path)` - Async file parsing

### Convenience Functions
- `parse_jsonl_file(file_path, **kwargs)` - Quick single file parsing
- `parse_multiple_jsonl_files(file_paths, **kwargs)` - Batch processing
- `find_claude_activity_files(claude_dir, pattern)` - Find JSONL files

## Examples

### Find and Parse Claude Activity Files
```python
from src.services.jsonl_parser import find_claude_activity_files, parse_jsonl_file

# Find all JSONL files in Claude projects directory
files = find_claude_activity_files("~/.claude/projects")

for file_path in files:
    result = parse_jsonl_file(file_path, file_age_limit_hours=168)  # 1 week
    
    if result.entries:  # Skip files that were too old
        print(f"File: {file_path.name}")
        print(f"  Entries: {len(result.entries)}")
        print(f"  Conversations: {len(result.conversations)}")
```

### Tool Usage Analysis
```python
result = parse_jsonl_file("activity.jsonl")
tool_usage = result.get_tool_usage_summary()

print("Tool usage summary:")
for tool_name, count in tool_usage.items():
    print(f"  {tool_name}: {count} uses")
```

### Conversation Analysis
```python
result = parse_jsonl_file("activity.jsonl")

for conversation in result.conversations:
    duration = conversation.end_time - conversation.start_time if conversation.end_time else None
    
    print(f"Session: {conversation.session_id}")
    print(f"  Messages: {conversation.total_messages}")
    print(f"  Duration: {duration}")
    print(f"  Tool calls: {conversation.tool_calls}")
```

## Testing

The parser includes comprehensive tests covering:

- Basic parsing functionality
- Error handling and recovery
- Streaming processing
- File age filtering
- Edge cases (encoding, large files, malformed data)
- Performance validation

Run tests:
```bash
uv run pytest tests/services/test_jsonl_parser.py -v
```

## Integration with CCMonitor

The JSONL parser integrates seamlessly with CCMonitor's architecture:

```python
from src.services import JSONLParser, ConversationMonitor

# Initialize parser with CCMonitor settings
parser = JSONLParser(
    file_age_limit_hours=24,  # Only process recent files
    skip_validation=False,    # Full validation for reliability
)

# Parse activity logs
result = parser.parse_file("~/.claude/projects/ccmonitor/activity.jsonl")

# Feed into monitoring system
monitor = ConversationMonitor()
for conversation in result.conversations:
    monitor.add_conversation(conversation)
```

## File Age Filtering Implementation

As requested, the parser **will not parse files older than a day** (24 hours by default):

```python
# Files older than the configured limit are automatically skipped
parser = JSONLParser(file_age_limit_hours=24)
result = parser.parse_file("old_file.jsonl")

# Check if file was skipped due to age
if result.statistics.error_details:
    for error in result.statistics.error_details:
        if error['error_type'] == 'file_too_old':
            print(f"File skipped: {error['error_message']}")
```

The age limit is configurable and can be adjusted based on monitoring needs.

## Dependencies

- **Pydantic** - Data validation and serialization
- **Python 3.12+** - Modern Python features and type hints
- **Standard library** - JSON, pathlib, datetime, asyncio

No external parsing libraries required - built for performance and reliability.