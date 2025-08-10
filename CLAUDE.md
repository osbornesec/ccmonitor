# CCMonitor Project - Claude Code Orchestrator

## PRP-Based Development Workflow

### Overview
CCMonitor uses a Product Requirements and Planning (PRP) based development workflow that breaks complex features into autonomous, self-contained implementation packages.

### PRP Structure
```
PRPs/
├── todo/           # PRPs waiting to be implemented
├── doing/          # PRPs currently being worked on  
├── done/           # Completed PRPs
└── templates/      # PRP templates for new features
```

### PRP Lifecycle
1. **Todo Creation**: Convert ACTIVE_TODOS.md items into detailed PRPs using @prp-todo-to-prp-orchestrator
2. **PRP Selection**: Move PRP from `todo/` to `doing/` when ready to implement
3. **Implementation**: Execute PRP using recommended specialist agents
4. **Completion**: Move completed PRP to `done/` after validation

### Key Agents for PRP Workflow

#### @prp-todo-to-prp-orchestrator
- **Purpose**: Converts ACTIVE_TODOS.md into comprehensive PRPs
- **Input**: Active todos and project context
- **Output**: Detailed PRPs in `PRPs/todo/` directory
- **Usage**: Automatically triggered when ACTIVE_TODOS.md is updated

#### @prp-specification-writer  
- **Purpose**: Creates detailed PRP specifications for complex features
- **Usage**: When existing PRPs need more detail or new features require planning
- **Output**: High-quality PRPs with complete context for implementation success

#### @prp-execution-orchestrator
- **Purpose**: Executes PRPs against the codebase with validation loops
- **Usage**: When implementing PRPs with monitoring and quality gates
- **Features**: Orchestrates implementation flow, manages validation, ensures success

#### @prp-quality-assurance-specialist
- **Purpose**: Validates PRP implementation against success criteria
- **Usage**: During and after PRP implementation for quality verification
- **Output**: Comprehensive validation reports and success confirmation

### Current Active PRPs (in PRPs/todo/)
1. **01_core_data_models.md** - Foundation Pydantic models and type system
2. **02_jsonl_parsing_engine.md** - High-performance JSONL parsing with error recovery  
3. **03_database_layer.md** - SQLite/SQLAlchemy storage system
4. **04_tui_framework.md** - Textual-based UI framework and application shell
5. **05_conversation_list_view.md** - DataTable view with filtering and real-time updates
6. **06_conversation_detail_view.md** - Message rendering with syntax highlighting
7. **07_live_monitoring.md** - File watching and real-time monitoring system
8. **08_statistics_dashboard.md** - Analytics and cost tracking dashboard
9. **09_search_and_filter.md** - Full-text search and advanced filtering
10. **10_configuration_management.md** - Settings and configuration system
11. **11_error_handling_recovery.md** - Comprehensive error handling framework
12. **12_testing_infrastructure.md** - Complete testing setup with CI/CD

### PRP Implementation Order
See `PRPs/todo/00_implementation_order.md` for detailed dependency analysis and parallel development opportunities.

### PRP Best Practices
- Each PRP is self-contained with clear success criteria
- Use TDD approach - write tests first (4-level validation loop)
- Maintain backward compatibility during implementation
- Document API changes and update related PRPs
- Regular integration testing between components
- Move PRPs through lifecycle stages systematically



### Delegation Rules

#### ALWAYS delegate when:
- Task matches specialist's exact expertise
- Multiple complex subtasks can run in parallel
- Deep domain knowledge required
- User mentions specific technology

#### NEVER delegate when:
- Simple file read/write operations
- Quick bash commands
- Straightforward answers from context
- Task is already 90% complete

### Agent Communication Protocol

When delegating, provide:
```
Task: [Specific task description]
Context: [Files, paths, dependencies]
Constraints: [Requirements, standards]
Expected Output: [Deliverables]
Do NOT: [Actions to avoid]
```

### Performance Optimizations

#### Tool Priority:
1. File ops: Read/Write/Edit > Bash
2. Search: Grep/Glob > find/grep
3. Web: Firecrawl > WebFetch > WebSearch
4. Docs: Context7 > Perplexity > general web

#### Efficiency Tips:
- Batch parallel tool calls
- Use caching (maxAge parameter)
- Prefer specialized tools
- Delegate complex searches

## Environment Setup

This project uses **uv** for Python package management.

### Package Installation
- Use `uv pip install <package>` to install packages
- Use `uv run <command>` to run commands in the virtual environment
- The virtual environment is located at `.venv/`

### Running Tools
- Linting: `uv run ruff check src/`
- Type checking: `uv run --with mypy mypy src/`
- Tests: `uv run pytest`

## Quality Gates
Always run before marking task complete:
- `uv run ruff check src/` - Linting
- `uv run --with mypy mypy src/` - Type checking
- `uv run pytest` - Tests (if applicable)

## Comprehensive Linting Analysis

### lint_by_file.sh Script
A comprehensive Python linting analysis script that provides detailed, organized reporting of code quality issues.

**Location**: `/home/michael/dev/ccmonitor/lint_by_file.sh`

**Usage**: 
```bash
./lint_by_file.sh
```

**Features**:
- **Comprehensive Analysis**: Runs both `ruff` linting and `mypy` type checking
- **Organized Reports**: Creates structured output in `lint_report/` directory
- **Priority-Based Categorization**: Issues sorted by security, performance, quality, style
- **Fix Difficulty Assessment**: Separates auto-fixable vs manual intervention required
- **Multiple Report Views**:
  - By file: Individual reports for each source file
  - By severity: Groups warnings, errors, notes
  - By error code: Individual files for each lint rule
  - By category: Security, errors, performance, imports, quality, documentation, style
  - By fix difficulty: Auto-fixable vs manual fixes
  - By priority: Critical to low priority systematic fixing order

**Report Structure**:
```
lint_report/
├── by_file/           # Issues organized by file
├── by_severity/       # Issues by severity (warnings, errors)  
├── by_error_code/     # Each ruff/mypy rule in separate file
├── by_category/       # Security, performance, style, etc.
├── by_fix_difficulty/ # Auto-fixable vs manual fixes
├── by_priority/       # Critical to low priority
├── raw_ruff_output.txt
├── raw_mypy_output.txt
├── ruff_output.json
├── summary.txt        # Comprehensive overview
└── statistics.txt     # Detailed metrics
```

**Lint Categories & Priorities**:
1. **Critical (Priority 1)**: Security vulnerabilities (S*), syntax errors (E*, F*)
2. **High (Priority 2)**: Performance issues (PERF*, FURB*)
3. **Medium-High (Priority 3)**: Import organization (I*, TID*)
4. **Medium (Priority 4)**: Code quality (C90, N*, A*, B*, C4*, etc.)
5. **Medium (Priority 5)**: Documentation (D*)
6. **Low (Priority 6)**: Style and formatting (W*, UP*, Q*, COM*, etc.)

**Quick Fix Commands**:
- Auto-fix issues: `uv run ruff check --fix src/`
- Format code: `uv run ruff format src/`
- Type check: `uv run mypy src/`

**Workflow Integration**:
- Run `./lint_by_file.sh` for comprehensive analysis
- Review `lint_report/summary.txt` for overview
- Use auto-fix for simple style issues: `uv run ruff check --fix src/`
- **IMPORTANT**: Re-run `./lint_by_file.sh` after applying auto-fixes to get updated analysis
- Tackle remaining issues by priority starting with `lint_report/by_priority/critical_security_errors.txt`
- Address manual fixes systematically using the organized reports

## Complete File Fixing Strategy

## 🚨 MANDATORY RULE: COMPLETE EVERY FILE TO ZERO ISSUES 🚨

**ABSOLUTE REQUIREMENT**: When fixing linting issues in a file, you MUST fix **EVERY SINGLE ISSUE** in that file before moving to any other file. This is **NON-NEGOTIABLE**.

**CRITICAL PRINCIPLE**: When fixing linting issues in a file, **fix ALL issues in that file, not just a subset**. We want to be completely finished with each file and never have to circle back to it later.

### 🔒 ZERO TOLERANCE POLICY:
- **NO PARTIAL FIXES**: A file with 1 remaining issue is NOT complete
- **NO EXCEPTIONS**: Every ruff and mypy issue must be resolved
- **NO MOVING ON**: Do not proceed to another file until current file shows "All checks passed!"
- **VERIFICATION REQUIRED**: Run `uv run ruff check <file>` AND `uv run mypy <file>` to confirm ZERO issues

### File-by-File Completion Approach
1. **Select Target File**: Choose highest-priority file from lint report
2. **Apply Auto-fixes**: Run `uv run ruff check --fix <file>` first
3. **Manual Fix ALL Remaining**: Fix every single remaining issue in the file
4. **Verify Completion**: Confirm file has 0 issues before moving to next file
5. **Update Progress**: Mark file as 100% complete in todo tracking

### Benefits of Complete File Fixing:
- **No Rework**: Never revisit the same file multiple times
- **Clear Progress**: Binary state - file is either done or not done
- **Efficiency**: Focused attention eliminates context switching
- **Quality**: Ensures comprehensive improvement rather than partial fixes
- **Maintainability**: Files remain clean and don't regress

### Systematic Implementation:
```
For each file in priority order:
1. Auto-fix: `uv run ruff check --fix src/path/file.py`
2. Manual fix: Address ALL remaining issues (line length, type annotations, etc.)
3. Verify: `uv run ruff check src/path/file.py` returns 0 issues
4. Confirm: `uv run mypy src/path/file.py` passes type checking
5. Complete: Mark file as 100% finished and move to next file
```

**Never leave a file partially fixed - complete each file entirely before proceeding to the next one.**

The script automatically cleans up the previous `lint_report/` directory on each run to keep the repository tidy while providing comprehensive analysis for systematic code quality improvement.

Remember: You are the conductor of a 200+ member specialized orchestra. Your value lies in knowing exactly which expert(s) to engage for optimal results.

## Configuration File Management

### Protected Configuration Files
This project has protected configuration files that maintain strict quality standards:
- `pyproject.toml` - Main project configuration with linting, formatting, and type checking rules
- `mypy.ini` - Type checking configuration
- Other quality control configuration files

### Configuration Change Policy
**IMPORTANT**: Configuration files are protected by hooks and cannot be modified directly by Claude Code.

If changes to configuration files are needed (such as adding new mypy overrides, changing linting rules, or modifying package dependencies), you must:

1. **Request user approval** - Ask the user to make the specific changes needed
2. **Provide exact changes** - Specify exactly what needs to be added, modified, or removed
3. **Explain reasoning** - Clearly explain why the configuration change is necessary
4. **Wait for user action** - Do not attempt to modify protected files directly

### Example Request Format
```
CONFIGURATION CHANGE NEEDED:

File: pyproject.toml
Section: [[tool.mypy.overrides]]
Change: Add "textual" and "textual.*" to the ignore_missing_imports module list
Reason: To resolve mypy type checking errors with the Textual TUI library

Please add these lines to the mypy overrides section:
    "textual",
    "textual.*"
```

This ensures configuration changes are intentional, reviewed, and maintain the project's quality standards.