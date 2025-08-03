# PRP: Core Pruning Engine Development

## Objective
Build the central pruning engine that intelligently removes redundant content while preserving essential conversation context and maintaining conversation flow integrity.

## Success Criteria
- [ ] Implement message processing pipeline with configurable pruning levels
- [ ] Develop context-aware compression algorithms
- [ ] Create content filtering system with pattern-based rules
- [ ] Ensure conversation dependency chain preservation
- [ ] Achieve 50-80% file size reduction targets

## Test-Driven Development Plan

### Phase 2.1: Message Processing Pipeline

#### Tests to Write First
```python
def test_jsonl_pruner_initialization():
    """Test pruner initialization with different levels"""
    
def test_load_and_save_jsonl():
    """Test JSONL file I/O operations"""
    
def test_build_conversation_graph():
    """Test conversation dependency graph construction"""
    
def test_identify_important_messages():
    """Test important message identification using scoring"""
    
def test_prune_with_context_preservation():
    """Test pruning while maintaining context dependencies"""
```

#### Implementation Tasks
1. **Core Pruner Class**
   ```python
   class JSONLPruner:
       def __init__(self, pruning_level='medium'):
           self.pruning_level = pruning_level
           self.importance_threshold = {
               'light': 20,
               'medium': 40, 
               'aggressive': 60
           }[pruning_level]
       
       def process_file(self, input_path, output_path):
           messages = self.load_jsonl(input_path)
           conversation_graph = self.build_conversation_graph(messages)
           important_messages = self.identify_important_messages(messages)
           pruned_messages = self.prune_with_context_preservation(
               messages, important_messages, conversation_graph
           )
           self.save_jsonl(pruned_messages, output_path)
   ```

2. **Conversation Graph Builder**
   - Parse parentUuid relationships
   - Identify conversation branches and dependencies
   - Build directed graph of message relationships
   - Detect orphaned messages and circular references

### Phase 2.2: Context-Aware Compression

#### Tests to Write First
```python
def test_smart_truncation():
    """Test preservation of beginning/end of large outputs"""
    
def test_semantic_summarization():
    """Test verbose log replacement with summaries"""
    
def test_reference_preservation():
    """Test keeping content referenced by later messages"""
    
def test_chain_integrity():
    """Test conversation flow dependency maintenance"""
```

#### Implementation Tasks
1. **Smart Truncation Engine**
   - Preserve first and last N lines of large tool outputs
   - Detect and preserve error messages within large outputs
   - Maintain file path references and key identifiers
   - Add truncation markers for transparency

2. **Semantic Summarization**
   - Replace verbose hook logs with status summaries
   - Compress repetitive system validations
   - Summarize successful command outputs
   - Preserve failure details and error messages

3. **Reference Analysis**
   - Scan for cross-references between messages
   - Preserve content mentioned in later conversations
   - Maintain code snippets referenced multiple times
   - Keep file modification sequences intact

### Phase 2.3: Content Filtering System

#### Tests to Write First
```python
def test_removal_pattern_matching():
    """Test pattern-based content removal"""
    
def test_compression_rule_application():
    """Test content compression rules"""
    
def test_filter_system_messages():
    """Test system message filtering logic"""
    
def test_preserve_essential_content():
    """Test that essential content is never removed"""
```

#### Implementation Tasks
1. **Pattern-Based Filtering**
   ```python
   REMOVAL_PATTERNS = [
       r'\[/home/michael/\.claude/hooks/.*\] completed successfully',
       r'PreToolUse:.*Resource Governor.*',
       r'PostToolUse:.*observability.*',
       r'<local-command-stdout></local-command-stdout>',
       r'System reminder.*todo list.*'
   ]
   ```

2. **Compression Rules Engine**
   ```python
   COMPRESSION_RULES = {
       'large_file_reads': lambda content: compress_file_content(content, max_lines=20),
       'command_outputs': lambda content: summarize_command_result(content),
       'tool_validations': lambda content: extract_validation_result(content)
   }
   ```

3. **Content Classification**
   - Identify hook system logs vs. essential notifications
   - Distinguish between informational and actionable content
   - Classify tool outputs by importance and reusability
   - Preserve debugging information and error traces

### Phase 2.4: Integration and Optimization

#### Tests to Write First
```python
def test_end_to_end_pruning():
    """Test complete pruning pipeline on sample files"""
    
def test_performance_benchmarks():
    """Test processing speed and memory usage"""
    
def test_compression_ratios():
    """Test achieved file size reduction ratios"""
    
def test_content_quality_preservation():
    """Test that pruned files maintain conversational coherence"""
```

#### Implementation Tasks
1. **Pipeline Optimization**
   - Optimize conversation graph construction
   - Implement streaming processing for large files
   - Add progress tracking for batch operations
   - Memory-efficient message processing

2. **Quality Assurance**
   - Verify conversation flow remains coherent
   - Ensure important decisions are preserved
   - Validate that code changes are fully retained
   - Check that error solutions remain accessible

## Deliverables
1. **Core Pruning Engine** (`src/pruner/core.py`)
2. **Content Compression Module** (`src/pruner/compressor.py`)
3. **Filtering Rules Engine** (`src/pruner/filters.py`)
4. **Conversation Graph Builder** (`src/pruner/graph.py`)
5. **Integration Test Suite** (`tests/test_pruning.py`)
6. **Performance Benchmarks** (`tests/test_performance.py`)

## Dependencies
- Phase 1 completion (analysis and scoring algorithms)
- Python libraries: `json`, `re`, `pathlib`, `collections`
- Testing framework: `pytest`
- Sample JSONL files for validation

## Context7 Documentation References

### JSON Module Patterns for File Processing
Using Python's robust JSON handling for JSONL operations:

```python
import json
from pathlib import Path

class JSONLProcessor:
    def load_jsonl(self, file_path: Path) -> List[Dict]:
        """Load JSONL with streaming for memory efficiency"""
        entries = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line.strip())
                    entries.append(entry)
                except json.JSONDecodeError as e:
                    # Log malformed entries but continue processing
                    print(f"Warning: Invalid JSON at line {line_num}: {e}")
        return entries
    
    def save_jsonl(self, entries: List[Dict], file_path: Path) -> None:
        """Save entries to JSONL format"""
        with open(file_path, 'w', encoding='utf-8') as f:
            for entry in entries:
                # Ensure compact JSON output
                json.dump(entry, f, separators=(',', ':'), ensure_ascii=False)
                f.write('\n')

# Handle infinite/NaN values in JSONL data
def sanitize_entry(entry: Dict) -> Dict:
    """Handle special float values that might be in JSONL"""
    json_str = json.dumps(entry, allow_nan=False)  # Strict JSON compliance
    return json.loads(json_str)
```

### Pytest Testing Patterns for File Processing
Comprehensive testing patterns for data processing pipelines:

```python
import pytest
import tempfile
from pathlib import Path

# Factory fixture for test data generation
@pytest.fixture
def make_test_jsonl():
    def _make_jsonl(entries_count=10, message_types=None):
        """Generate test JSONL data with configurable patterns"""
        if message_types is None:
            message_types = ["user", "assistant", "system"]
        
        entries = []
        for i in range(entries_count):
            entry = {
                "uuid": f"test-{i}",
                "type": message_types[i % len(message_types)],
                "message": {"content": f"Test message {i}"},
                "timestamp": f"2025-08-01T19:5{i:02d}:21.024033"
            }
            entries.append(entry)
        return entries
    return _make_jsonl

# Parametrized testing for pruning levels
@pytest.mark.parametrize(
    "pruning_level,expected_reduction",
    [
        ("light", (20, 40)),      # 20-40% reduction
        ("medium", (40, 60)),     # 40-60% reduction  
        ("aggressive", (60, 80)), # 60-80% reduction
    ],
)
def test_pruning_reduction_targets(make_test_jsonl, pruning_level, expected_reduction):
    """Test that pruning achieves expected reduction ratios"""
    original_entries = make_test_jsonl(100)
    pruner = JSONLPruner(pruning_level)
    
    pruned_entries = pruner.prune_entries(original_entries)
    reduction_percent = (1 - len(pruned_entries) / len(original_entries)) * 100
    
    min_reduction, max_reduction = expected_reduction
    assert min_reduction <= reduction_percent <= max_reduction

# File-based testing with temporary files
def test_end_to_end_file_processing(tmp_path):
    """Test complete file processing pipeline"""
    # Arrange: Create test JSONL file
    input_file = tmp_path / "input.jsonl"
    output_file = tmp_path / "output.jsonl"
    
    test_data = [
        {"uuid": "1", "type": "user", "message": {"content": "Hello"}},
        {"uuid": "2", "type": "assistant", "message": {"content": "Hi there!"}},
    ]
    
    with open(input_file, 'w') as f:
        for entry in test_data:
            json.dump(entry, f)
            f.write('\n')
    
    # Act: Process file
    pruner = JSONLPruner("medium")
    pruner.process_file(input_file, output_file)
    
    # Assert: Verify output file
    assert output_file.exists()
    with open(output_file, 'r') as f:
        output_lines = f.readlines()
    assert len(output_lines) > 0
```

### Click CLI Framework for Phase 4 Integration
Preparing for CLI tool development using Click patterns:

```python
import click
from pathlib import Path

# Command group with context for state management
@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config', type=click.Path(), help='Configuration file path')
@click.pass_context
def cli(ctx, verbose, config):
    """JSONL Context Pruning Tool"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config'] = config

# Pruning command with multiple options
@cli.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.argument('output_file', type=click.Path(path_type=Path))
@click.option('--level', type=click.Choice(['light', 'medium', 'aggressive']), 
              default='medium', help='Pruning intensity level')
@click.option('--dry-run', is_flag=True, help='Preview changes without modifying files')
@click.option('--backup/--no-backup', default=True, help='Create backup before pruning')
@click.pass_context
def prune(ctx, input_file, output_file, level, dry_run, backup):
    """Prune JSONL conversation files intelligently"""
    if ctx.obj['verbose']:
        click.echo(f"Pruning {input_file} with level: {level}")
    
    if dry_run:
        click.echo("DRY RUN: No files will be modified")
        # Show preview of changes
        return
    
    if backup:
        backup_path = input_file.with_suffix(f"{input_file.suffix}.backup")
        click.echo(f"Creating backup: {backup_path}")

# Progress indication for long operations
@click.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option('--recursive', '-r', is_flag=True, help='Process subdirectories')
def batch_prune(directory, recursive):
    """Batch process JSONL files in directory"""
    pattern = "**/*.jsonl" if recursive else "*.jsonl"
    files = list(directory.glob(pattern))
    
    with click.progressbar(files, label='Processing files') as bar:
        for file_path in bar:
            # Process each file
            process_single_file(file_path)

cli.add_command(batch_prune)
```

## Performance Targets
- Process 1000-line JSONL file in <1 second
- Achieve 50-80% size reduction
- Maintain <1% false positive rate for important content removal
- Memory usage <100MB for largest session files

## Acceptance Criteria
- All tests pass with >95% coverage
- Performance targets met on representative datasets
- Conversation integrity maintained in all test cases
- Size reduction targets achieved without data loss
- Edge cases handled gracefully (malformed JSON, circular refs)

## Risk Mitigation
- Conservative default pruning levels
- Extensive validation against manual review
- Rollback capabilities for failed operations
- Incremental testing on small datasets first

## Next Steps
Upon completion, this PRP enables Phase 3 (Safety & Validation) development with a working pruning engine ready for production safety measures.