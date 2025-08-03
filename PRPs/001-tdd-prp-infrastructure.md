name: "PRP-001: TDD-PRP Infrastructure Foundation"
description: |

---

## Goal

**Feature Goal**: Establish the foundational infrastructure for Test-Driven Development (TDD) enhanced Product Requirement Prompts (PRPs) within our Claude Code environment.

**Deliverable**: Complete PRP framework with TDD-first templates, validation systems, and directory structure that enables autonomous development workflows.

**Success Definition**: PRPs can be created, executed, and validated with enforced TDD methodology and comprehensive quality gates.

## User Persona

**Target User**: AI Development Agents and Human Developers
**Use Case**: Creating and executing development tasks with test-first methodology
**User Journey**: 
1. Agent identifies development need
2. Creates PRP using TDD-enhanced template
3. Executes PRP with automatic validation
4. Validates implementation through 4-level testing

**Pain Points Addressed**: 
- Lack of structured development approach for AI agents
- Inconsistent testing practices across implementations
- No systematic validation of AI-generated code

## Why

- Enable systematic, test-first development methodology for AI agents
- Provide structured templates that enforce quality and best practices  
- Create foundation for autonomous development workflows
- Ensure all AI-generated code meets production quality standards
- Establish repeatable patterns for complex feature development

## What

A comprehensive PRP infrastructure that combines traditional Product Requirements with Test-Driven Development methodology, providing:

- TDD-enhanced PRP templates with test-first validation
- Comprehensive validation framework with 4-level quality gates
- Directory structure supporting PRP lifecycle management
- Integration with existing Claude Code hooks and agents
- Context management for AI development workflows

### Success Criteria

- [ ] PRP directory structure created with proper organization
- [ ] TDD-enhanced PRP templates implemented and tested
- [ ] 4-level validation framework operational (Syntax, Unit, Integration, Creative)
- [ ] All templates include test-first methodology enforcement
- [ ] Integration with existing UV environment and tooling
- [ ] Documentation and examples for PRP creation and execution

## All Needed Context

### Context Completeness Check

_This PRP provides everything needed to implement TDD-PRP infrastructure from scratch in our existing Claude Code environment with advanced hooks and UV setup._

### Documentation & References

```yaml
# MUST READ - Include these in your context window
- file: /home/michael/dev/PRPs-agentic-eng/PRPs/templates/prp_base.md
  why: Comprehensive PRP template structure and validation approach
  critical: 4-level validation methodology and implementation patterns
  pattern: Template structure with Goal/Why/What/Context/Implementation/Validation sections

- file: /home/michael/dev/PRPs-agentic-eng/PRPs/README.md
  why: Core PRP philosophy and methodology understanding
  critical: "Context is non-negotiable" principle and PRD vs PRP differences
  pattern: Context engineering approach for AI development

- file: /home/michael/dev/PRPs-agentic-eng/PRPs/example-from-workshop-mcp-crawl4ai-refactor-1.md
  why: Real-world PRP implementation example with complex refactoring
  pattern: Foundation-first approach and progressive validation
  critical: Zero regression requirement and comprehensive testing strategy

- file: .claude/settings.json
  why: Current hook configuration and tool permissions
  pattern: UV runner integration and hook execution patterns
  gotcha: All scripts must use UV runner for virtual environment

- file: CLAUDE.md
  why: Project-specific development guidelines and constraints
  pattern: File size limits (<500 lines), testing requirements, code structure
  critical: Integration with existing hook system and agent architecture
```

### Current Codebase Tree

```bash
claude-agents/
├── .claude/
│   ├── agents/               # 24 specialized agents
│   │   ├── code-reviewer.md
│   │   ├── python-specialist.md
│   │   ├── react-specialist.md
│   │   └── ... (21 more agents)
│   ├── hooks/               # Advanced hook system
│   │   ├── precompact_pruner.py
│   │   ├── post_tool_monitor.py
│   │   ├── smart_prompt_enhancer.py
│   │   └── ... (5 hooks total)
│   ├── scripts/            # UV utilities and context management
│   │   ├── uv_runner.sh
│   │   ├── context_metrics.py
│   │   └── test_uv_setup.py
│   ├── settings.json       # Hook configurations with UV integration
│   └── requirements.txt    # UV environment dependencies
├── CLAUDE.md              # Project guidelines
├── README.md
└── ACTIVE_TODOS.md        # Project management todos
```

### Desired Codebase Tree with PRP Infrastructure

```bash
claude-agents/
├── .claude/               # Existing advanced hook system
├── PRPs/                  # NEW - PRP infrastructure
│   ├── templates/         # TDD-enhanced PRP templates
│   │   ├── prp_tdd_base.md
│   │   ├── prp_red_green_refactor.md
│   │   ├── prp_bdd_specification.md
│   │   └── prp_simple_task.md
│   ├── active/            # Currently executing PRPs
│   ├── completed/         # Historical PRP archive
│   ├── scripts/           # PRP execution and validation tools
│   │   ├── prp_runner.py
│   │   ├── prp_validator.py
│   │   └── prp_creator.py
│   └── ai_docs/           # Context documentation for PRP creation
│       ├── tdd_patterns.md
│       ├── validation_guide.md
│       └── context_engineering.md
├── ACTIVE_TODOS.md        # Enhanced with PRP integration
└── COMPLETED_TODOS.md     # NEW - Historical todo tracking
```

### Known Gotchas & Library Quirks

```python
# CRITICAL: All PRP scripts must use UV runner for virtual environment isolation
# Pattern: bash .claude/scripts/uv_runner.sh script.py

# CRITICAL: Hook system requires specific exit codes and output formats
# Pattern: Exit code 0 for success, exit code 2 with stderr for user reminders

# CRITICAL: File size limits from CLAUDE.md - all files must be <500 lines
# Pattern: Break large templates into composable sections

# CRITICAL: Integration with existing 24 specialized agents
# Pattern: PRPs should trigger appropriate specialist agents based on content

# CRITICAL: orjson performance optimization already implemented
# Pattern: Use json_loads/json_dumps wrapper functions in hooks
```

## Implementation Blueprint

### Implementation Tasks (ordered by dependencies)

```yaml
Task 1: CREATE PRPs/templates/prp_tdd_base.md
  - IMPLEMENT: Comprehensive TDD-first PRP template
  - FOLLOW pattern: /home/michael/dev/PRPs-agentic-eng/PRPs/templates/prp_base.md structure
  - ENHANCE: Add explicit TDD methodology sections (Red-Green-Refactor)
  - NAMING: Clear section headers with TDD validation requirements
  - PLACEMENT: PRPs/templates/ directory
  - DEPENDENCIES: None

Task 2: CREATE PRPs/templates/prp_red_green_refactor.md  
  - IMPLEMENT: TDD cycle-specific template for refactoring tasks
  - FOLLOW pattern: Red-Green-Refactor methodology with explicit phases
  - NAMING: Clear phase delineation (Red: Write Tests, Green: Make Pass, Refactor: Improve)
  - PLACEMENT: PRPs/templates/ directory
  - DEPENDENCIES: Task 1 completion

Task 3: CREATE PRPs/templates/prp_bdd_specification.md
  - IMPLEMENT: Behavior-Driven Development template for user-facing features
  - FOLLOW pattern: Given-When-Then specification format
  - NAMING: BDD scenario structure with acceptance criteria
  - PLACEMENT: PRPs/templates/ directory
  - DEPENDENCIES: Task 1 completion

Task 4: CREATE PRPs/scripts/prp_validator.py
  - IMPLEMENT: PRP quality validation with 4-level checking
  - FOLLOW pattern: Existing context_metrics.py for validation approach
  - NAMING: validate_prp_quality() function with comprehensive checks
  - DEPENDENCIES: UV runner integration (existing .claude/scripts/uv_runner.sh)
  - PLACEMENT: PRPs/scripts/ directory

Task 5: CREATE PRPs/scripts/prp_creator.py
  - IMPLEMENT: Interactive PRP creation wizard
  - FOLLOW pattern: Template selection and guided completion
  - NAMING: create_prp_interactive() with template selection
  - DEPENDENCIES: Task 1-3 completion (templates must exist)
  - PLACEMENT: PRPs/scripts/ directory

Task 6: CREATE PRPs/ai_docs/tdd_patterns.md
  - IMPLEMENT: TDD best practices and patterns for AI development
  - FOLLOW pattern: Existing documentation structure in .claude/
  - CONTENT: Red-Green-Refactor cycles, test patterns, AI-specific considerations
  - PLACEMENT: PRPs/ai_docs/ directory
  - DEPENDENCIES: Task 1-2 completion

Task 7: MODIFY ACTIVE_TODOS.md
  - ENHANCE: Add PRP-specific metadata and tracking
  - FOLLOW pattern: Existing structure with PRP integration fields
  - ADD: PRP file references, status tracking, dependency management
  - PRESERVE: Existing todo structure and priorities
  - DEPENDENCIES: Tasks 1-6 completion

Task 8: CREATE PRPs/scripts/prp_runner.py
  - IMPLEMENT: PRP execution engine with TDD validation
  - FOLLOW pattern: /home/michael/dev/PRPs-agentic-eng/PRPs/scripts/prp_runner.py
  - ADAPT: Integration with our UV environment and hook system
  - NAMING: execute_prp_with_validation() main function
  - DEPENDENCIES: All previous tasks (full infrastructure)
  - PLACEMENT: PRPs/scripts/ directory
```

### Implementation Patterns & Key Details

```python
# TDD-Enhanced PRP Template Structure
"""
## Goal & Success Criteria (Traditional PRP)
## TDD Methodology Section (NEW)
- Red Phase: Test specifications that must fail initially
- Green Phase: Minimal implementation to make tests pass  
- Refactor Phase: Code improvement while maintaining tests

## Test-First Validation Loop (ENHANCED)
Level 0: Test Creation (NEW)
  - Write failing tests before any implementation
  - Validate test coverage requirements
  - Ensure tests actually fail initially

Level 1: Syntax & Style (Red Phase)
  - Run linting and type checking
  - Ensure clean code before implementation

Level 2: Unit Tests (Green Phase)  
  - Make failing tests pass with minimal code
  - Achieve required test coverage
  
Level 3: Integration Testing (Green Phase)
  - End-to-end validation of feature
  - Integration with existing systems

Level 4: Refactor & Optimize (Refactor Phase)
  - Code improvement while maintaining test suite
  - Performance and maintainability enhancements
"""

# PRP Validator Pattern
def validate_prp_quality(prp_path: Path) -> ValidationResult:
    """
    PATTERN: Multi-level PRP validation
    - Template compliance checking
    - TDD methodology validation  
    - Context completeness verification
    - Success criteria measurability
    """
    
# UV Integration Pattern (CRITICAL)
"""
All PRP scripts must use:
bash .claude/scripts/uv_runner.sh PRPs/scripts/script_name.py

This ensures:
- Virtual environment isolation
- Consistent dependency access
- Integration with existing hook system
"""
```

### Integration Points

```yaml
HOOKS:
  - integrate with: .claude/hooks/post_tool_monitor.py
  - pattern: "Log PRP creation and execution events to memory.jsonl"
  - add: PRP-specific event tracking with importance scoring

AGENTS:
  - integrate with: All 24 existing specialized agents  
  - pattern: "PRPs should automatically invoke appropriate specialist agents"
  - add: PRP-aware agent selection based on content analysis

UV_ENVIRONMENT:
  - integrate with: .claude/scripts/uv_runner.sh
  - pattern: "All PRP scripts execute within UV virtual environment"
  - ensure: Consistent dependency access and isolation

SETTINGS:
  - modify: .claude/settings.json
  - pattern: "Add PRP script permissions and tool access"
  - add: Bash permissions for PRP execution scripts
```

## Validation Loop

### Level 0: Test Creation (TDD Red Phase)

```bash
# Validate PRP templates require test-first approach
grep -q "## Test-First Requirements" PRPs/templates/*.md || echo "ERROR: Templates missing TDD requirements"

# Ensure all templates include failing test specifications
grep -q "Red Phase:" PRPs/templates/*.md || echo "ERROR: Templates missing Red Phase guidance"

# Validate template structure completeness
python .claude/scripts/uv_runner.sh PRPs/scripts/prp_validator.py --validate-templates

# Expected: All templates enforce test-first methodology
```

### Level 1: Syntax & Style (Immediate Feedback)

```bash
# Run after each PRP script creation
ruff check PRPs/scripts/*.py --fix
mypy PRPs/scripts/*.py
ruff format PRPs/scripts/*.py

# Validate markdown templates format correctly
markdownlint PRPs/templates/*.md || echo "Install markdownlint if needed"

# Project-wide validation
ruff check .claude/ PRPs/ --fix
mypy .claude/scripts/ PRPs/scripts/

# Expected: Zero errors before proceeding to implementation
```

### Level 2: Unit Tests (TDD Green Phase)

```bash
# Test PRP validation functionality
uv run pytest PRPs/scripts/tests/test_prp_validator.py -v

# Test PRP creation tools
uv run pytest PRPs/scripts/tests/test_prp_creator.py -v

# Test template parsing and validation
uv run pytest PRPs/scripts/tests/test_template_validation.py -v

# Coverage validation for core PRP functionality
uv run pytest PRPs/ --cov=PRPs --cov-report=term-missing

# Expected: All tests pass with >90% coverage
```

### Level 3: Integration Testing (System Validation)

```bash
# Test complete PRP creation workflow
bash .claude/scripts/uv_runner.sh PRPs/scripts/prp_creator.py --template tdd_base --output test_prp.md

# Validate created PRP passes quality checks
bash .claude/scripts/uv_runner.sh PRPs/scripts/prp_validator.py --prp test_prp.md

# Test PRP execution integration
bash .claude/scripts/uv_runner.sh PRPs/scripts/prp_runner.py --prp test_prp.md --validate-only

# Verify integration with existing hook system
python .claude/scripts/context_metrics.py report | grep -q "PRP" || echo "Hook integration needed"

# Expected: End-to-end PRP workflow functions correctly
```

### Level 4: Creative & TDD-Specific Validation

```bash
# Test Red-Green-Refactor cycle enforcement
# Create a sample PRP that violates TDD principles
echo "## Implementation without tests" > invalid_prp.md
bash .claude/scripts/uv_runner.sh PRPs/scripts/prp_validator.py --prp invalid_prp.md --strict-tdd

# Should fail with TDD validation errors
[ $? -eq 1 ] || echo "ERROR: TDD validation not working"

# Test template completeness for various scenarios
for template in PRPs/templates/*.md; do
    bash .claude/scripts/uv_runner.sh PRPs/scripts/prp_validator.py --validate-template "$template"
done

# Validate context engineering effectiveness
# Test PRP creation with minimal context vs comprehensive context
bash .claude/scripts/uv_runner.sh PRPs/scripts/prp_creator.py --test-context-completeness

# Expected: TDD methodology enforced, templates comprehensive, context validation works
```

## Final Validation Checklist

### Technical Validation

- [ ] All 4 validation levels completed successfully
- [ ] PRP templates enforce test-first methodology
- [ ] Scripts integrate with UV virtual environment
- [ ] Hook system integration functional
- [ ] No linting errors: `uv run ruff check PRPs/`
- [ ] No type errors: `uv run mypy PRPs/scripts/`
- [ ] All tests pass: `uv run pytest PRPs/ -v`

### TDD-PRP Validation

- [ ] Templates require test creation before implementation
- [ ] Red-Green-Refactor cycle clearly defined
- [ ] Validation loops enforce TDD discipline
- [ ] Test coverage requirements specified
- [ ] Refactoring phase includes test preservation

### Integration Validation

- [ ] PRP scripts execute via UV runner
- [ ] Hook system captures PRP events
- [ ] Agent integration pathways established
- [ ] ACTIVE_TODOS.md updated with PRP references
- [ ] Documentation supports PRP creation workflow

### Foundation Validation

- [ ] Directory structure supports PRP lifecycle
- [ ] Templates cover major development scenarios
- [ ] Validation tools ensure quality compliance
- [ ] Context engineering guidelines established
- [ ] Integration with existing 24 agents confirmed

---

## Anti-Patterns to Avoid

- ❌ Don't create PRPs without enforcing test-first methodology
- ❌ Don't skip TDD validation phases - they prevent regressions
- ❌ Don't ignore context completeness - it determines AI success
- ❌ Don't bypass UV runner - environment consistency is critical
- ❌ Don't create templates without real-world validation examples
- ❌ Don't implement without comprehensive test coverage
- ❌ Don't skip integration testing - hooks and agents must work together