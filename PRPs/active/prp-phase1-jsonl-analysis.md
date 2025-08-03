# PRP: JSONL Pattern Analysis and Algorithm Design

## Objective
Develop the foundation for intelligent JSONL context pruning by analyzing conversation patterns and designing importance scoring algorithms.

## Success Criteria
- [ ] Complete analysis of representative JSONL files from different projects
- [ ] Document message importance scoring criteria with weights
- [ ] Create conversation flow dependency mapping system
- [ ] Design and prototype core pruning algorithm
- [ ] Validate algorithm with sample dataset

## Test-Driven Development Plan

### Phase 1.1: JSONL Pattern Analysis Engine

#### Tests to Write First
```python
def test_parse_jsonl_file():
    """Test basic JSONL file parsing and structure validation"""
    
def test_identify_message_types():
    """Test categorization of user/assistant/system messages"""
    
def test_extract_tool_usage_patterns():
    """Test identification and categorization of tool calls"""
    
def test_map_conversation_dependencies():
    """Test parentUuid chain mapping and flow analysis"""
    
def test_calculate_message_importance():
    """Test importance scoring algorithm with known examples"""
```

#### Implementation Tasks
1. **JSONL Parser Module**
   - Parse and validate JSONL structure
   - Extract message metadata (type, timestamp, uuid, parentUuid)
   - Handle malformed entries gracefully

2. **Message Categorization System**
   - Identify code modification messages
   - Detect error/solution pairs
   - Classify tool usage patterns
   - Recognize hook system logs

3. **Conversation Flow Analyzer**
   - Build dependency graphs from parentUuid chains
   - Identify conversation branches and merges
   - Map tool call sequences

### Phase 1.2: Importance Scoring Algorithm

#### Tests to Write First
```python
def test_code_change_scoring():
    """Test high importance scoring for code modifications"""
    
def test_error_solution_scoring():
    """Test high importance scoring for error/solution pairs"""
    
def test_hook_log_penalty():
    """Test low importance scoring for hook system logs"""
    
def test_edge_case_scoring():
    """Test scoring for empty messages, system validations"""
```

#### Implementation Tasks
1. **Content Analysis Engine**
   ```python
   def calculate_message_importance(message):
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

2. **Pattern Recognition Functions**
   - `contains_code_changes()`: Detect file modifications
   - `contains_error_solution()`: Identify problem-solution pairs
   - `contains_architectural_decision()`: Find design decisions
   - `is_hook_log()`: Filter hook system messages
   - `is_system_validation()`: Identify confirmation messages

### Phase 1.3: Data Collection and Validation

#### Tests to Write First
```python
def test_sample_data_analysis():
    """Test analysis results on known sample files"""
    
def test_importance_distribution():
    """Test that importance scores follow expected distribution"""
    
def test_pruning_simulation():
    """Test simulated pruning with different thresholds"""
```

#### Implementation Tasks
1. **Sample Data Collection**
   - Gather representative JSONL files from different projects
   - Include various conversation types (debugging, feature development, analysis)
   - Ensure samples include both verbose and concise sessions

2. **Analysis Validation**
   - Manually score sample messages for ground truth
   - Compare algorithm results with human judgment
   - Iterate on scoring weights based on validation results

## Deliverables
1. **JSONL Analysis Library** (`src/analyzer.py`)
2. **Importance Scoring Engine** (`src/scoring.py`)
3. **Pattern Recognition Module** (`src/patterns.py`)
4. **Validation Test Suite** (`tests/test_analysis.py`)
5. **Sample Data Analysis Report** (`docs/analysis_report.md`)

## Dependencies
- Standard Python libraries: `json`, `datetime`, `pathlib`
- Testing framework: `pytest`
- Sample JSONL files from existing projects

## Context7 Documentation References

### JSON Processing Patterns
Using Python's built-in JSON module for robust JSONL parsing and validation:

```python
import json
from pathlib import Path

# Load and validate JSONL entries
def load_jsonl_entries(file_path: Path):
    """Load JSONL file with proper error handling"""
    entries = []
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line.strip())
                entries.append(entry)
            except json.JSONDecodeError as e:
                # Handle malformed JSON gracefully
                print(f"Invalid JSON at line {line_num}: {e}")
                continue
    return entries

# Pattern for handling repeated keys (JSONL may have duplicate message IDs)
# Python's json.loads() retains last occurrence of duplicate keys
weird_json = '{"uuid": "123", "uuid": "456", "message": "test"}'
parsed = json.loads(weird_json)  # {'uuid': '456', 'message': 'test'}
```

### Testing Patterns with Pytest
Implementing comprehensive test suites using pytest best practices:

```python
import pytest
from pathlib import Path

# Factory fixture pattern for creating test data
@pytest.fixture
def make_jsonl_entry():
    def _make_entry(message_type="user", content="test", uuid=None):
        return {
            "uuid": uuid or f"test-{id(object())}",
            "type": message_type,
            "message": {"content": content},
            "timestamp": "2025-08-01T19:51:21.024033"
        }
    return _make_entry

# Test pattern for JSONL analysis
def test_importance_scoring(make_jsonl_entry):
    # Arrange
    code_entry = make_jsonl_entry("assistant", "Creating new function")
    research_entry = make_jsonl_entry("assistant", "Reading documentation")
    
    # Act & Assert
    assert calculate_importance(code_entry) > calculate_importance(research_entry)

# Parametrized testing for multiple scenarios
@pytest.mark.parametrize(
    "message_content,expected_score",
    [
        ("Edit file main.py", 40),  # Code modification
        ("Read README.md", 10),     # Research activity
        ("Fix critical bug", 35),   # Error solution
    ],
)
def test_scoring_scenarios(message_content, expected_score):
    entry = {"message": {"content": message_content}}
    assert calculate_importance(entry) >= expected_score
```

### Pattern Recognition Best Practices
Based on Python standard library patterns for text analysis:

```python
import re
from typing import Dict, List, Pattern

# Compile regex patterns for efficiency (from Python docs)
class PatternAnalyzer:
    def __init__(self):
        # Pre-compile patterns for performance
        self.code_patterns = [
            re.compile(r'\b(write|edit|create|implement)\b', re.IGNORECASE),
            re.compile(r'\.(py|js|ts|rs|go|java)[\s\']'),
            re.compile(r'function|class|def\s+\w+')
        ]
        
        self.error_patterns = [
            re.compile(r'\b(error|exception|failed|fix)\b', re.IGNORECASE),
            re.compile(r'traceback|stack trace', re.IGNORECASE)
        ]
    
    def analyze_content(self, content: str) -> Dict[str, int]:
        """Analyze content patterns using compiled regex"""
        scores = {"code": 0, "error": 0}
        
        # Use pre-compiled patterns for efficiency
        for pattern in self.code_patterns:
            scores["code"] += len(pattern.findall(content))
            
        for pattern in self.error_patterns:
            scores["error"] += len(pattern.findall(content))
            
        return scores
```

## Acceptance Criteria
- All tests pass with >95% coverage
- Algorithm correctly identifies important vs. redundant content
- Validation against manual scoring shows >90% agreement
- Processing speed: <1 second for 1000-line JSONL file
- Memory usage: <50MB for largest sample files

## Risk Mitigation
- Start with conservative importance thresholds
- Validate on small datasets before scaling
- Maintain backup of all analyzed files
- Document all pattern recognition decisions

## Next Steps
Upon completion, this PRP enables Phase 2 (Core Pruning Engine) development with validated algorithms and proven pattern recognition capabilities.