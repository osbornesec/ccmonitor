name: "PRP-003: Rate-Limited Todo Update Hook Implementation"
description: |

---

## Goal

**Feature Goal**: Create an intelligent hook that monitors subagent completion and reminds the AI system to update ACTIVE_TODOS.md with implemented work, using rate limiting to prevent spam and smart detection to only remind when actual implementation occurs.

**Deliverable**: A `subagentstop_todo_reminder.py` hook that integrates with our existing hook system to provide rate-limited reminders (4-minute intervals) and uses exit code 2 with stderr output to signal todo update requirements.

**Success Definition**: Hook automatically detects when subagents complete implementation work and reminds the system to update ACTIVE_TODOS.md without creating notification spam, enabling autonomous todo tracking.

## User Persona

**Target User**: AI Development Agents and Autonomous Development System
**Use Case**: Maintaining accurate project progress tracking during autonomous development
**User Journey**:
1. Subagent completes implementation work
2. Hook detects implementation activity and completion
3. Hook checks rate limiting to prevent spam
4. Hook outputs reminder to update todos if appropriate
5. Main system updates ACTIVE_TODOS.md with completed work
6. Development cycle continues with next todo

**Pain Points Addressed**:
- Manual todo tracking interrupts autonomous development flow
- Notification spam when hooks trigger too frequently
- Inconsistent progress tracking across development sessions
- No systematic way to detect when implementation is complete

## Why

- Enable autonomous progress tracking without manual intervention
- Prevent notification fatigue through intelligent rate limiting
- Maintain accurate project state for continued autonomous development
- Create feedback loop between implementation and project management
- Establish foundation for self-managing development environments

## What

An intelligent hook system that monitors subagent activity and provides contextual reminders for todo updates:

- Smart detection of actual implementation vs. research/analysis
- 4-minute rate limiting to prevent notification spam
- Exit code 2 with stderr output for clear system signaling
- Integration with existing hook system and memory tracking
- Context-aware reminders based on work completion significance

### Success Criteria

- [ ] Hook detects subagent completion events accurately
- [ ] Rate limiting prevents reminders more frequently than every 4 minutes
- [ ] Only reminds when actual implementation work (not just research) occurs
- [ ] Uses exit code 2 and stderr output for system integration
- [ ] Integrates with existing post_tool_monitor.py and memory system
- [ ] Provides clear, actionable reminder messages

## All Needed Context

### Context Completeness Check

_This PRP provides everything needed to implement a sophisticated todo update hook that integrates with our existing advanced hook system and provides intelligent, rate-limited reminders._

### Documentation & References

```yaml
# MUST READ - Include these in your context window
- file: .claude/hooks/post_tool_monitor.py
  why: Existing hook pattern for monitoring tool usage and events
  critical: Hook execution pattern, memory.jsonl integration, importance scoring
  pattern: Event detection, logging, and system integration approach

- file: .claude/settings.json
  why: Hook configuration pattern and execution requirements
  critical: Hook registration, tool permissions, UV runner integration
  pattern: PostToolUse hook configuration with script execution

- file: .claude/memory.jsonl
  why: Understanding event tracking format and importance scoring
  critical: Event structure, timestamp format, context metadata
  pattern: Tool usage logging with importance-based filtering

- file: ACTIVE_TODOS.md
  why: Todo format and update requirements for reminder content
  critical: Status tracking format, completion metadata, PRP integration
  pattern: Todo status transitions and completion tracking

- file: .claude/scripts/uv_runner.sh
  why: Script execution pattern for hook integration
  critical: Virtual environment isolation, consistent execution context
  pattern: All hooks must execute via UV runner for environment consistency
```

### Current Hook System Architecture

```bash
.claude/
├── hooks/
│   ├── precompact_pruner.py        # Context pruning on memory pressure
│   ├── post_tool_monitor.py        # Tool usage tracking and logging
│   ├── smart_prompt_enhancer.py    # Context injection on user prompts
│   ├── pre_tool_validator.py       # Security validation before tool execution
│   ├── post_tool_logger.py        # Comprehensive tool usage logging
│   └── subagentstop_todo_reminder.py  # NEW - Todo update reminders
├── settings.json                   # Hook configuration and permissions
└── scripts/
    ├── uv_runner.sh               # Hook execution wrapper
    └── context_metrics.py         # Hook performance monitoring
```

### Desired Hook Integration

```bash
.claude/
├── hooks/
│   ├── subagentstop_todo_reminder.py  # NEW - Intelligent todo reminders
│   │   ├── Rate limiting (4-minute intervals)
│   │   ├── Implementation detection logic
│   │   ├── Exit code 2 + stderr output
│   │   └── Integration with memory system
│   └── ... (existing 5 hooks)
├── settings.json                   # Updated with new hook configuration
└── state/                         # NEW - Hook state management
    ├── rate_limits.json           # Rate limiting state persistence
    └── activity_tracking.json     # Implementation activity analysis
```

### Known Hook System Patterns & Constraints

```python
# CRITICAL: All hooks must execute via UV runner
# Pattern: All hook scripts configured in settings.json with uv_runner.sh prefix

# CRITICAL: Exit codes have specific meanings in Claude Code
# Pattern: Exit 0 = success, Exit 2 = user reminder with stderr output

# CRITICAL: Hook output to stderr for user messages
# Pattern: print("message", file=sys.stderr) followed by sys.exit(2)

# CRITICAL: State persistence across hook executions
# Pattern: JSON files in .claude/state/ for maintaining rate limit data

# CRITICAL: Integration with existing memory system
# Pattern: Read memory.jsonl for activity analysis and importance scoring

# CRITICAL: Performance requirements for hook execution
# Pattern: Hooks must complete in <100ms to avoid workflow interruption
```

## Implementation Blueprint

### Implementation Tasks (ordered by dependencies)

```yaml
Task 1: CREATE .claude/state/ directory for hook state management
  - IMPLEMENT: State persistence directory for rate limiting and activity tracking
  - FOLLOW pattern: Existing .claude/ structure for organized state management
  - NAMING: .claude/state/ directory with JSON state files
  - PLACEMENT: .claude/state/ directory
  - DEPENDENCIES: None (foundation task)

Task 2: CREATE .claude/hooks/subagentstop_todo_reminder.py
  - IMPLEMENT: Core hook with rate limiting and implementation detection
  - FOLLOW pattern: Existing post_tool_monitor.py structure and execution
  - FUNCTIONALITY: Activity analysis, rate limiting, reminder generation
  - NAMING: subagentstop_todo_reminder.py following existing convention
  - DEPENDENCIES: Task 1 (state directory exists)
  - PLACEMENT: .claude/hooks/ directory

Task 3: CREATE .claude/hooks/utils/rate_limiter.py
  - IMPLEMENT: Reusable rate limiting utility for hook system
  - FOLLOW pattern: Modular utility design for hook ecosystem
  - FUNCTIONALITY: Time-based rate limiting with persistent state
  - NAMING: RateLimiter class with configurable intervals
  - DEPENDENCIES: Task 1 (state management established)
  - PLACEMENT: .claude/hooks/utils/ directory

Task 4: CREATE .claude/hooks/utils/activity_detector.py  
  - IMPLEMENT: Implementation activity detection and significance analysis
  - FOLLOW pattern: Existing memory.jsonl analysis in post_tool_monitor.py
  - FUNCTIONALITY: Distinguish implementation from research, assess significance
  - NAMING: ActivityDetector class with importance scoring
  - DEPENDENCIES: Task 3 (utilities foundation)
  - PLACEMENT: .claude/hooks/utils/ directory

Task 5: MODIFY .claude/settings.json  
  - INTEGRATE: Add subagentstop_todo_reminder hook to PostToolUse configuration
  - FOLLOW pattern: Existing hook configuration with UV runner integration
  - ADD: Hook registration with appropriate tool permissions
  - PRESERVE: All existing hook configurations and tool permissions
  - DEPENDENCIES: Task 2 (hook implementation complete)

Task 6: CREATE .claude/hooks/tests/test_todo_reminder.py
  - IMPLEMENT: Comprehensive test suite for todo reminder functionality
  - FOLLOW pattern: Existing testing patterns with pytest fixtures
  - COVERAGE: Rate limiting, activity detection, hook integration
  - NAMING: test_* functions for each component
  - DEPENDENCIES: Tasks 2-4 (all components implemented)
  - PLACEMENT: .claude/hooks/tests/ directory

Task 7: ENHANCE .claude/hooks/post_tool_monitor.py
  - INTEGRATE: Coordination with todo reminder to prevent duplicate logging
  - ADD: Activity significance scoring for todo reminder input
  - IMPLEMENT: Shared state management for hook coordination
  - DEPENDENCIES: Task 5 (hook integration complete)

Task 8: CREATE documentation for hook usage and debugging
  - IMPLEMENT: Hook debugging guide and troubleshooting documentation
  - FOLLOW pattern: Existing documentation structure
  - CONTENT: Rate limiting configuration, activity detection tuning
  - DEPENDENCIES: Task 6 (testing and validation complete)
  - PLACEMENT: .claude/docs/ or inline documentation
```

### Implementation Patterns & Key Details

```python
# Rate Limiting Pattern
class RateLimiter:
    """
    PATTERN: Time-based rate limiting with persistent state
    - Store last execution time in JSON file
    - Check elapsed time before allowing action
    - Configurable interval (default 4 minutes = 240 seconds)
    - Thread-safe file operations for concurrent hook execution
    """
    
    def __init__(self, interval_seconds: int = 240):
        self.interval = interval_seconds
        self.state_file = Path(".claude/state/rate_limits.json")
    
    def can_execute(self, action_key: str) -> bool:
        # Check if enough time has elapsed since last execution
        pass
    
    def record_execution(self, action_key: str):
        # Update state file with current timestamp
        pass

# Activity Detection Pattern
class ActivityDetector:
    """
    PATTERN: Implementation significance analysis
    - Analyze memory.jsonl for recent tool usage
    - Distinguish file creation/modification from reading
    - Score activity importance based on tool types and outcomes
    - Filter out low-significance activities (searches, reads)
    """
    
    def analyze_recent_activity(self, memory_entries: List[dict]) -> ActivityAnalysis:
        # Analyze last N memory entries for implementation patterns
        implementation_tools = ['Write', 'Edit', 'MultiEdit', 'Bash']
        research_tools = ['Read', 'Grep', 'Glob', 'WebFetch', 'WebSearch']
        
        # Score based on tool usage patterns and outcomes
        pass

# Hook Integration Pattern
def main():
    """
    PATTERN: Claude Code hook execution
    - Read from stdin for hook input data
    - Perform analysis and rate limiting checks
    - Output to stderr with exit code 2 for user reminders
    - Exit 0 for no action needed
    """
    try:
        # Read hook input data
        input_data = json.load(sys.stdin)
        
        # Initialize components
        rate_limiter = RateLimiter(interval_seconds=240)  # 4 minutes
        activity_detector = ActivityDetector()
        
        # Check if reminder is needed
        if should_remind_todo_update(input_data, rate_limiter, activity_detector):
            rate_limiter.record_execution("todo_reminder")
            print("Update ACTIVE_TODOS.md with what you have implemented.", 
                  file=sys.stderr)
            sys.exit(2)
        
        # No reminder needed
        sys.exit(0)
        
    except Exception as e:
        # Log error but don't interrupt workflow
        logging.error(f"Todo reminder hook error: {e}")
        sys.exit(0)
```

### Hook System Integration

```yaml
SETTINGS_JSON_INTEGRATION:
  - add to: .claude/settings.json
  - section: "hooks.PostToolUse"
  - pattern: "bash $CLAUDE_PROJECT_DIR/.claude/scripts/uv_runner.sh $CLAUDE_PROJECT_DIR/.claude/hooks/subagentstop_todo_reminder.py"
  - permissions: Add "Bash(uv *)" for UV runner execution

MEMORY_SYSTEM_INTEGRATION:
  - read from: .claude/memory.jsonl
  - pattern: "Analyze recent entries for implementation vs research activity"
  - integrate with: post_tool_monitor.py importance scoring

STATE_PERSISTENCE:
  - store in: .claude/state/rate_limits.json
  - format: {"todo_reminder": {"last_execution": "2025-08-01T19:51:21.024033"}}
  - pattern: Thread-safe JSON file operations

PERFORMANCE_REQUIREMENTS:
  - execution time: <100ms for hook execution
  - file operations: Minimal file I/O for state management
  - error handling: Graceful degradation without workflow interruption
```

## Validation Loop

### Level 0: Test Creation (TDD Red Phase)

```bash
# Create failing tests for hook functionality
cat > .claude/hooks/tests/test_todo_reminder.py << 'EOF'
def test_rate_limiting_prevents_spam():
    # This should fail until rate limiting is implemented
    limiter = RateLimiter(interval_seconds=240)
    assert limiter.can_execute("test") == True
    limiter.record_execution("test")
    assert limiter.can_execute("test") == False  # Should be rate limited
EOF

# Run failing tests to establish TDD baseline
uv run pytest .claude/hooks/tests/test_todo_reminder.py -v
# Expected: Tests fail initially (Red phase)
```

### Level 1: Syntax & Style (Implementation Phase)

```bash
# Run after each component creation
ruff check .claude/hooks/subagentstop_todo_reminder.py --fix
ruff check .claude/hooks/utils/*.py --fix
mypy .claude/hooks/subagentstop_todo_reminder.py
mypy .claude/hooks/utils/*.py

# Validate hook integration with settings
python -c "
import json
settings = json.load(open('.claude/settings.json'))
assert 'subagentstop_todo_reminder.py' in str(settings['hooks']['PostToolUse'])
"

# Project-wide validation  
ruff check .claude/hooks/ --fix
mypy .claude/hooks/

# Expected: Zero errors, clean formatting, proper type hints
```

### Level 2: Unit Tests (TDD Green Phase)

```bash
# Test rate limiting functionality
uv run pytest .claude/hooks/tests/test_rate_limiter.py -v

# Test activity detection and significance scoring
uv run pytest .claude/hooks/tests/test_activity_detector.py -v

# Test complete hook integration
uv run pytest .claude/hooks/tests/test_todo_reminder.py -v

# Test hook utilities
uv run pytest .claude/hooks/utils/tests/ -v

# Coverage validation
uv run pytest .claude/hooks/tests/ --cov=.claude.hooks --cov-report=term-missing

# Expected: All tests pass, >90% code coverage
```

### Level 3: Integration Testing (System Validation)

```bash
# Test hook execution through UV runner
echo '{"tool": "Write", "file": "test.py", "status": "success"}' | \
  bash .claude/scripts/uv_runner.sh .claude/hooks/subagentstop_todo_reminder.py

# Should output reminder to stderr and exit with code 2
[ $? -eq 2 ] || echo "ERROR: Hook should exit with code 2 for reminders"

# Test rate limiting prevents spam
for i in {1..3}; do
  echo '{"tool": "Write", "file": "test'$i'.py", "status": "success"}' | \
    bash .claude/scripts/uv_runner.sh .claude/hooks/subagentstop_todo_reminder.py
  sleep 1
done
# Only first execution should produce reminder

# Test hook integration with existing system
echo "Testing hook system integration"
python .claude/scripts/context_metrics.py report | grep -q "subagentstop" || echo "Hook not integrated"

# Expected: Hook executes correctly, rate limiting works, system integration functional
```

### Level 4: Creative & Real-World Validation

```bash
# Test with realistic development workflow
# Simulate subagent completing actual implementation work
cat > simulate_development.sh << 'EOF'
#!/bin/bash
# Simulate a development session with multiple activities

# Research phase (should not trigger reminder)
echo '{"tool": "Read", "file": "docs.md", "status": "success"}' | \
  bash .claude/scripts/uv_runner.sh .claude/hooks/subagentstop_todo_reminder.py

# Implementation phase (should trigger reminder)
echo '{"tool": "Write", "file": "feature.py", "status": "success"}' | \
  bash .claude/scripts/uv_runner.sh .claude/hooks/subagentstop_todo_reminder.py

# More implementation (should be rate limited)
echo '{"tool": "Edit", "file": "feature.py", "status": "success"}' | \
  bash .claude/scripts/uv_runner.sh .claude/hooks/subagentstop_todo_reminder.py
EOF

chmod +x simulate_development.sh
./simulate_development.sh

# Test activity significance detection
# Low significance activities should not trigger reminders
echo '{"tool": "Grep", "pattern": "test", "status": "success"}' | \
  bash .claude/scripts/uv_runner.sh .claude/hooks/subagentstop_todo_reminder.py
[ $? -eq 0 ] || echo "ERROR: Low significance activity should not trigger reminder"

# Test state persistence across hook executions
# Rate limiting state should persist between executions
ls -la .claude/state/rate_limits.json || echo "ERROR: State file not created"

# Performance testing
time (for i in {1..10}; do
  echo '{"tool": "Read", "file": "test.md", "status": "success"}' | \
    bash .claude/scripts/uv_runner.sh .claude/hooks/subagentstop_todo_reminder.py
done)
# Should complete in <1 second total (10 executions)

# Expected: Realistic workflows handled correctly, performance acceptable, state persists
```

## Final Validation Checklist

### Technical Validation

- [ ] All 4 validation levels completed successfully
- [ ] Hook executes via UV runner with proper environment isolation
- [ ] Rate limiting prevents reminders more frequently than 4 minutes
- [ ] Exit code 2 and stderr output work correctly for system integration
- [ ] State persistence maintains rate limiting across hook executions
- [ ] Performance meets <100ms per execution requirement

### Functional Validation

- [ ] Implementation activities trigger reminders appropriately
- [ ] Research/analysis activities do not trigger unnecessary reminders
- [ ] Activity significance scoring distinguishes meaningful work
- [ ] Hook integrates with existing memory system and importance tracking
- [ ] Error handling prevents workflow interruption
- [ ] Clear, actionable reminder messages provided

### Integration Validation

- [ ] Hook registered correctly in .claude/settings.json
- [ ] Coordination with existing post_tool_monitor.py functional
- [ ] Memory system integration provides activity context
- [ ] State management directory and files created properly
- [ ] UV runner integration maintains environment consistency
- [ ] No conflicts with existing 5 hooks in the system

### Autonomous Workflow Validation

- [ ] Hook enables autonomous todo tracking without interruption
- [ ] Rate limiting prevents notification fatigue during development
- [ ] Activity detection accurately identifies completion events
- [ ] System can continue autonomous development after todo updates
- [ ] Hook contributes to self-managing development environment
- [ ] Debugging and troubleshooting capabilities available

---

## Anti-Patterns to Avoid

- ❌ Don't trigger reminders for every tool usage - causes notification spam
- ❌ Don't bypass rate limiting - users will disable annoying hooks
- ❌ Don't ignore activity significance - research activities shouldn't trigger reminders
- ❌ Don't use blocking file operations - hooks must complete quickly
- ❌ Don't fail hook execution on errors - graceful degradation is essential
- ❌ Don't hardcode file paths - use configurable, environment-aware paths
- ❌ Don't skip state persistence - rate limiting requires memory across executions