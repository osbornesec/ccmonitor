# Intelligent JSONL Context Pruning System

## Executive Summary

This plan outlines the development of an intelligent context pruning system for Claude Code JSONL session files. Based on analysis of existing conversation histories, this system will reduce file sizes by 50-80% while preserving essential context, leading to faster startup times, reduced token usage, and improved development efficiency.

## Problem Analysis

### Current State
- JSONL files range from 4 lines to 4,000+ lines per session
- Files contain extensive hook system logs and observability data
- Redundant system messages and validation confirmations
- Large tool outputs that may not be referenced later
- Token overhead when loading project context

### JSONL Structure Patterns
Each JSONL record contains:
```json
{
  "parentUuid": "parent-message-id",
  "uuid": "unique-message-id", 
  "type": "user|assistant|system",
  "message": {...},
  "timestamp": "ISO-8601",
  "sessionId": "session-identifier",
  "cwd": "/working/directory",
  "version": "claude-code-version"
}
```

### Content Categories
1. **Essential Context** (preserve):
   - Code changes and implementations
   - Error solutions that worked
   - Architectural decisions and rationale
   - Test results and validation outcomes
   - File modification history

2. **Reducible Content** (compress/remove):
   - Hook system logs (`PreToolUse:*`, `PostToolUse:*`)
   - System validation messages
   - Repeated observability notifications
   - Verbose command outputs
   - Empty tool results

## Implementation Plan

### Phase 1: Analysis & Strategy (Week 1)

#### 1.1 JSONL Pattern Analysis
- Parse representative JSONL files from each project
- Identify message importance scoring criteria:
  - Code modification messages: HIGH priority
  - Error/solution pairs: HIGH priority
  - Decision explanations: MEDIUM priority
  - Hook logs: LOW priority
  - System confirmations: MINIMAL priority
- Map conversation flow dependencies via `parentUuid` chains
- Catalog tool usage patterns and result importance

#### 1.2 Pruning Algorithm Design
```python
def calculate_message_importance(message):
    """Score message importance (0-100)"""
    score = 0
    
    # High importance indicators
    if contains_code_changes(message): score += 40
    if contains_error_solution(message): score += 35
    if contains_architectural_decision(message): score += 30
    
    # Medium importance indicators  
    if contains_user_question(message): score += 20
    if contains_file_modification(message): score += 25
    
    # Low importance indicators
    if is_hook_log(message): score -= 30
    if is_system_validation(message): score -= 25
    if is_empty_output(message): score -= 20
    
    return max(0, min(100, score))
```

#### 1.3 Content Compression Strategies
- **Large File Reads**: Extract key excerpts, preserve context markers
- **Command Outputs**: Summarize success/failure, keep error details
- **Tool Chains**: Preserve final results, compress intermediate steps
- **Hook Messages**: Remove redundant logs, keep error notifications

### Phase 2: Core Pruning Engine (Week 2-3)

#### 2.1 Message Processing Pipeline
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

#### 2.2 Context-Aware Compression
- **Smart Truncation**: Preserve beginning/end of large outputs
- **Semantic Summarization**: Replace verbose logs with summaries
- **Reference Preservation**: Keep content referenced by later messages
- **Chain Integrity**: Maintain conversation flow dependencies

#### 2.3 Content Filtering Rules
```python
REMOVAL_PATTERNS = [
    r'\[/home/michael/\.claude/hooks/.*\] completed successfully',
    r'PreToolUse:.*Resource Governor.*',
    r'PostToolUse:.*observability.*',
    r'<local-command-stdout></local-command-stdout>',
    r'System reminder.*todo list.*'
]

COMPRESSION_RULES = {
    'large_file_reads': lambda content: compress_file_content(content, max_lines=20),
    'command_outputs': lambda content: summarize_command_result(content),
    'tool_validations': lambda content: extract_validation_result(content)
}
```

### Phase 3: Safety & Validation (Week 3-4)

#### 3.1 Backup and Recovery System
```python
class SafePruner:
    def prune_with_backup(self, file_path, pruning_level):
        # Create timestamped backup
        backup_path = f"{file_path}.backup.{int(time.time())}"
        shutil.copy2(file_path, backup_path)
        
        try:
            pruned_content = self.prune_file(file_path, pruning_level)
            self.validate_pruned_content(pruned_content)
            self.write_pruned_file(file_path, pruned_content)
            return {"success": True, "backup": backup_path}
        except Exception as e:
            self.restore_from_backup(file_path, backup_path)
            return {"success": False, "error": str(e)}
```

#### 3.2 Validation Procedures
- **JSONL Format Validation**: Ensure each line is valid JSON
- **Conversation Flow Integrity**: Verify parentUuid chains remain intact
- **Essential Content Preservation**: Check that code changes are retained
- **Size Reduction Metrics**: Measure compression ratios and token savings

#### 3.3 Quality Assurance Tests
```python
def validate_pruned_session(original_path, pruned_path):
    tests = [
        test_jsonl_format_valid(pruned_path),
        test_conversation_chains_intact(original_path, pruned_path),
        test_code_changes_preserved(original_path, pruned_path),
        test_error_solutions_retained(original_path, pruned_path),
        test_file_size_reduction(original_path, pruned_path)
    ]
    return all(tests)
```

### Phase 4: Automation & Integration (Week 4-5)

#### 4.1 CLI Tool Development
```bash
# Usage examples
claude-prune --file session.jsonl --level medium --backup
claude-prune --directory /home/michael/.claude/projects --level light --dry-run
claude-prune --project ccobservatory --aggressive --stats
```

#### 4.2 Integration Features
- **Batch Processing**: Handle entire project directories
- **Dry Run Mode**: Preview changes without modification
- **Statistics Reporting**: Show space savings and retention rates
- **Selective Pruning**: Target specific sessions or date ranges

#### 4.3 Automated Scheduling
```python
class AutoPruner:
    def schedule_pruning(self):
        # Prune sessions older than 30 days (light)
        # Prune sessions older than 7 days (medium) 
        # Preserve recent sessions and frequently accessed files
        # Run weekly maintenance on entire projects directory
```

## Technical Specifications

### Dependencies
- Python 3.8+
- Standard library: `json`, `datetime`, `argparse`, `pathlib`
- Optional: `rich` for CLI output formatting

### Performance Targets
- Process 1000-line JSONL file in <1 second
- Achieve 50-80% size reduction
- Maintain <1% false positive rate for important content removal
- Memory usage <100MB for largest session files

### File Structure
```
claude-code-pruner/
├── src/
│   ├── pruner/
│   │   ├── __init__.py
│   │   ├── core.py          # Main pruning logic
│   │   ├── analyzer.py      # Content analysis
│   │   ├── compressor.py    # Content compression
│   │   └── validator.py     # Safety validation
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py          # Command-line interface
│   └── utils/
│       ├── __init__.py
│       ├── jsonl.py         # JSONL utilities
│       └── backup.py        # Backup management
├── tests/
├── docs/
└── README.md
```

## Expected Benefits

### Quantitative Improvements
- **File Size Reduction**: 50-80% smaller JSONL files
- **Token Usage**: 40-70% reduction in context loading tokens
- **Startup Time**: 30-50% faster session initialization
- **Storage Savings**: Significant disk space recovery

### Qualitative Improvements
- **Cleaner Context**: Focus on relevant conversation history
- **Better Performance**: Reduced memory usage and processing time
- **Improved Workflow**: Faster project switching and context loading
- **Maintainable History**: Essential information preserved long-term

## Risk Mitigation

### Data Safety
- Mandatory backup creation before any modification
- Validation checks at every step
- Rollback capabilities for failed operations
- Conservative pruning defaults

### Context Preservation
- Whitelist approach: remove only known-safe content
- Dependency analysis: preserve referenced content
- User review: optional manual approval for aggressive pruning
- Incremental testing: start with least important sessions

## Success Metrics

### Technical Metrics
- Average file size reduction percentage
- Token count reduction in typical Claude Code sessions
- Processing speed (files per second)
- False positive rate for important content removal

### User Experience Metrics
- Claude Code startup time improvement
- User satisfaction with preserved context quality
- Error rate in development workflows
- Time saved in project context loading

## Implementation Timeline

| Week | Phase | Deliverables |
|------|-------|-------------|
| 1 | Analysis | JSONL patterns documented, algorithms designed |
| 2 | Core Engine | Basic pruning functionality working |
| 3 | Safety Systems | Backup, validation, and recovery implemented |
| 4 | CLI Tool | Command-line interface and batch processing |
| 5 | Integration | Automated scheduling and performance optimization |

## Next Steps

1. **Begin Phase 1**: Analyze representative JSONL files from different projects
2. **Prototype Core Algorithm**: Build basic message importance scoring
3. **Test on Sample Data**: Validate approach with small dataset
4. **Iterate and Refine**: Improve based on initial results
5. **Scale to Full Implementation**: Apply to entire projects directory

This plan provides a comprehensive approach to optimizing Claude Code usage through intelligent context pruning while maintaining the essential conversational context that makes the tool effective.