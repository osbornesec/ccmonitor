# Claude Agents Project - Advanced Development Environment

This project demonstrates the full power of Claude Code with advanced hooks, custom agents, and intelligent automation.

## Project Overview

This is a showcase environment for Claude Code's advanced features including:
- Intelligent hooks for workflow automation
- Custom agents for specialized tasks
- Context pruning and management
- Security and quality enforcement
- Automated testing and reviews

## Development Guidelines

### Code Quality Standards
- All code must pass linting (hooks will auto-run linters)
- Functions should be small and focused (< 50 lines)
- Clear, descriptive naming conventions
- Comprehensive error handling required
- No hardcoded credentials or secrets

### Testing Requirements
- Minimum 80% test coverage for new features
- Unit tests for all public functions
- Integration tests for API endpoints
- Performance tests for critical paths

### Security Policies
- Input validation on all user data
- No direct SQL queries (use parameterized queries)
- Authentication required for sensitive operations
- Regular security scans via security-analyst agent

## Available Custom Agents

### code-reviewer
Automatically reviews code changes for quality and security issues.
- Triggered after file modifications
- Provides prioritized feedback
- Checks for security vulnerabilities

### test-writer
Generates comprehensive test suites for new code.
- Creates unit and integration tests
- Includes edge cases
- Ensures tests pass before completing

### performance-optimizer
Analyzes and optimizes code performance.
- Identifies bottlenecks
- Suggests algorithmic improvements
- Implements caching strategies

### security-analyst
Performs security audits and vulnerability scanning.
- Checks for OWASP Top 10 issues
- Identifies exposed secrets
- Provides remediation steps

### refactoring-expert
Improves code structure and maintainability.
- Identifies code smells
- Implements clean code principles
- Preserves functionality

## Hooks Configuration

### PreToolUse
- **pre_tool_validator.py**: Blocks dangerous commands and sensitive file access

### PostToolUse
- **post_tool_logger.py**: Logs actions and optionally auto-commits changes

### UserPromptSubmit
- **prompt_enhancer.py**: Adds project context to prompts

### PreCompact
- **context_pruner.py**: Intelligently prunes conversation context

### Stop
- Notifies session completion and logs summary

## Workflow Patterns

### Feature Implementation
1. Describe the feature clearly
2. Let Claude plan the implementation
3. code-reviewer agent will automatically review
4. test-writer agent creates tests
5. All hooks ensure quality and security

### Bug Fixing
1. Describe the bug with error messages
2. Claude investigates using appropriate tools
3. Fix is implemented with tests
4. security-analyst checks for vulnerabilities

### Performance Optimization
1. Identify performance concerns
2. performance-optimizer agent analyzes
3. Implements optimizations
4. Measures improvements

## Best Practices

### Using Agents Effectively
- Let agents work automatically - they're configured to activate when needed
- Trust the specialized agents for their domains
- Review agent feedback and implement suggestions

### Context Management
- Use "mark key event" for important milestones
- Context automatically prunes less important information
- Session summaries available in .claude/session_summary.md

### Security First
- Never bypass security hooks
- Always validate user input
- Keep dependencies updated
- Regular security audits

## Quick Commands

### Core System Commands

#### Basic Application
```bash
# Start the main application
uv run python main.py

# Run the test suite
uv run python -m pytest tests/ -v

# Run tests with coverage
uv run pytest tests/ -v --cov=PRPs --cov-report=term-missing
```

#### PRP (Project Requirement Planning) System

##### Creating PRPs
```bash
# Initialize PRP infrastructure
uv run python PRPs/scripts/prp_creator.py --init

# Create a new PRP from template
uv run python PRPs/scripts/prp_creator.py --template tdd_base --name "my-feature"

# Create API-specific PRP
uv run python PRPs/scripts/prp_creator.py --template tdd_base --name "user-authentication" --output PRPs/active/

# Create refactoring PRP
uv run python PRPs/scripts/prp_creator.py --template red_green_refactor --target-file src/legacy_module.py --preserve-behavior --zero-regression
```

##### Todo-to-PRP Orchestrator
```bash
# Analyze todos from ACTIVE_TODOS.md
python PRPs/scripts/orchestrator_main.py ACTIVE_TODOS.md --analyze --verbose

# Process specific todo by ID
python PRPs/scripts/orchestrator_main.py ACTIVE_TODOS.md --todo-id ACTIVE-001

# Filter by priority and auto-select next
python PRPs/scripts/orchestrator_main.py ACTIVE_TODOS.md --priority High --select-next

# Analysis only (no PRP generation)
python PRPs/scripts/orchestrator_main.py ACTIVE_TODOS.md --analyze --no-generate --limit 5
```

##### PRP Validation and Execution
```bash
# Validate all PRPs in the system
uv run python PRPs/scripts/prp_validator.py --validate-all-prps

# Execute PRP with TDD validation
uv run python PRPs/scripts/prp_runner.py --prp PRPs/active/user-authentication.md --validate-tdd --parallel-agents

# Validate test creation phase
uv run python PRPs/scripts/prp_validator.py --validate-test-creation
```

#### Analysis and Intelligence

##### Project Analysis
```bash
# Comprehensive project analysis
uv run python PRPs/scripts/intelligent_project_analyzer.py --analyze-technical-debt --suggest-improvements

# Performance analysis
uv run python PRPs/scripts/performance_analyzer.py --profile-application --identify-bottlenecks --suggest-optimizations
```

##### Multi-Agent Orchestration
```bash
# Check agent status and capabilities
uv run python PRPs/scripts/multi_agent_orchestrator.py --list-agents

# Execute complex multi-agent task
uv run python PRPs/scripts/multi_agent_orchestrator.py --execute-complex-task "e-commerce-checkout-flow"
```

#### Quality Assurance and Testing

##### 4-Level Validation Framework
```bash
# Level 0: Test Creation Validation
uv run python PRPs/scripts/prp_validator.py --validate-test-creation

# Level 1: Syntax & Style Validation
uv run ruff check . --fix
uv run mypy PRPs/ tests/
uv run black . --check

# Level 2: Unit Test Validation
uv run pytest tests/unit/ -v --cov=PRPs --cov-fail-under=90

# Level 3: Integration Test Validation
uv run pytest tests/integration/ -v --slow

# Level 4: Creative & End-to-End Validation
uv run pytest tests/scenarios/ -v --e2e
```

##### Security Scanning
```bash
# Comprehensive security audit
uv run python PRPs/scripts/security_scanner.py --scan-dependencies --check-vulnerabilities --audit-permissions --validate-configurations

# Security scanning with specific focus
uv run python PRPs/scripts/security_scanner.py --comprehensive
```

#### Machine Learning and Optimization

##### Model Training
```bash
# Train pattern recognition models
uv run python PRPs/scripts/ml_trainer.py --model pattern_recognition --data-source .claude/memory.jsonl --output-dir models/

# Update agent effectiveness models
uv run python PRPs/scripts/ml_trainer.py --model agent_effectiveness --data-source .claude/metrics.db --validation-split 0.2

# Train performance prediction models
uv run python PRPs/scripts/ml_trainer.py --model performance_prediction --features task_complexity,agent_count,context_size --target completion_time
```

#### Development Environment

##### Environment Setup
```bash
# Install dependencies
uv sync

# Install development dependencies
uv sync --dev

# Install pre-commit hooks (for contributors)
uv run pre-commit install
```

##### Development Tools
```bash
# Run full test suite including integration tests
uv run pytest tests/ --integration -v

# Performance optimization with goals
uv run python PRPs/scripts/prp_creator.py --template performance_optimization --target-bottlenecks "database_queries,api_response_time" --performance-goals "response_time<100ms,throughput>1000rps"
```

### Legacy Commands (may need updating for this deployment)

#### Mark Important Events
```bash
python .claude/scripts/advanced_context_manager.py mark-key-event "Completed user authentication feature"
```

#### Generate Session Summary
```bash
python .claude/scripts/advanced_context_manager.py summarize
```

#### Review Hook Logs
```bash
cat .claude/tool_usage.log | jq '.'
```

## Environment Variables

- `AUTO_COMMIT=true` - Enable automatic git commits after file changes
- `CLAUDE_PROJECT_DIR` - Automatically set by Claude Code

## Tips for Maximum Productivity

1. **Trust the Automation**: Hooks and agents are configured to maintain quality
2. **Parallel Execution**: Claude uses multiple agents simultaneously for speed
3. **Context Awareness**: The system remembers important events and patterns
4. **Security by Default**: Dangerous operations are blocked automatically
5. **Continuous Improvement**: Agents learn from patterns in your codebase

## Troubleshooting

If hooks aren't working:
1. Check file permissions: `chmod +x .claude/hooks/*.py`
2. Verify Python is available: `which python3`
3. Check logs: `.claude/tool_usage.log`
4. Use `/hooks` command to verify configuration

Remember: This environment is designed to make you more productive while maintaining high code quality and security standards. Let the automation handle the routine tasks while you focus on creative problem-solving!