name: "Project Management Agent PRP v1.0"
description: |
  Implement an intelligent project management agent that can analyze complex features,
  break them down into actionable todo hierarchies, perform dependency analysis,
  and integrate with PRP workflow for autonomous development.

---

## Goal

**Feature Goal**: Create a specialized Claude Code agent that can analyze complex development requirements and automatically generate structured, hierarchical todo lists with dependency analysis and PRP integration.

**Deliverable**: A fully functional `project-manager-prp` agent with supporting validation tools and integration patterns.

**Success Definition**: Agent can take high-level feature descriptions and produce comprehensive, dependency-aware todo hierarchies that integrate seamlessly with the PRP workflow and ACTIVE_TODOS.md format.

## User Persona

**Target User**: Development teams and individual developers using Claude Code for complex feature implementation

**Use Case**: When faced with large, complex features that need to be broken down into manageable, trackable tasks with proper dependency management

**User Journey**: 
1. Developer describes a complex feature or requirement
2. project-manager-prp agent analyzes the requirement
3. Agent generates structured todo hierarchy with dependencies  
4. Agent estimates time/effort for each task
5. Agent integrates todos into ACTIVE_TODOS.md format
6. Agent suggests PRP creation for complex sub-tasks

**Pain Points Addressed**: 
- Manual breakdown of complex features is time-consuming and error-prone
- Dependency management between tasks is often overlooked
- Inconsistent todo formats across projects
- Lack of integration between planning and implementation workflows

## Why

- **Autonomous Development**: Enables self-perpetuating development workflow where complex features are automatically decomposed
- **Consistency**: Ensures all project todos follow the same structured format with proper dependency analysis
- **Efficiency**: Reduces time spent on project planning and task organization
- **PRP Integration**: Creates seamless workflow from high-level requirements to specific PRPs
- **Dependency Management**: Prevents implementation bottlenecks by identifying task dependencies upfront

## What

The project-manager-prp agent will provide intelligent project decomposition with the following capabilities:

### Success Criteria (Test-First Requirements)

- [ ] Agent can analyze complex feature descriptions and generate structured todo hierarchies
- [ ] Dependency analysis correctly identifies blocking relationships between tasks
- [ ] Time estimation provides realistic effort estimates based on task complexity
- [ ] ACTIVE_TODOS.md integration maintains consistent format and structure
- [ ] PRP recommendations suggest appropriate PRP creation for complex sub-tasks
- [ ] Agent validation ensures generated todos are actionable and complete

## All Needed Context

### Context Completeness Check

_Before implementing this PRP, validate: "If someone knew nothing about this codebase, would they have everything needed to implement this successfully with test-first methodology?"_

### Test-First Context Requirements

```yaml
# MUST INCLUDE - Test patterns and examples for TDD implementation
- test_pattern: .claude/agents/code-reviewer.md
  why: Reference agent structure and testing patterns
  framework: pytest with agent simulation
  coverage: 90%+ for core agent logic

- existing_tests: test/ (if exists)
  why: Integration testing patterns for agent testing
  fixtures: Mock Claude Code agent interactions
```

### Documentation & References

```yaml
# MUST READ - Include these in your context window
- file: .claude/agents/code-reviewer.md
  why: Understand existing agent structure and patterns
  pattern: Agent configuration format and behavior definition
  gotcha: Agent must integrate with Claude Code's Task tool properly

- file: ACTIVE_TODOS.md
  why: Current todo format and structure requirements
  pattern: Priority levels, dependencies, time estimates, PRP references
  gotcha: Must maintain backward compatibility with existing format

- docfile: PRPs/ai_docs/tdd_patterns.md
  why: TDD patterns for agent development and testing
  section: Agent Testing Patterns

- file: .claude/agents/
  why: Review existing agents for consistent patterns
  pattern: Configuration structure, behavior definitions, tool usage
  gotcha: Must follow established agent conventions
```

### Current Codebase Analysis

```bash
# Current agent structure
.claude/agents/
├── api-design-specialist.md
├── aws-specialist.md
├── blockchain-specialist.md
├── code-reviewer.md
├── context-pruner.md
├── cypress-testing-specialist.md
├── deep-research-specialist.md
├── docker-kubernetes-specialist.md
├── flutter-specialist.md
├── go-specialist.md
├── java-specialist.md
├── javascript-typescript-specialist.md
├── machine-learning-specialist.md
├── meta-agent.md
├── mongodb-specialist.md
├── nextjs-specialist.md
├── performance-optimizer.md
├── postgresql-specialist.md
├── python-specialist.md
├── react-specialist.md
├── refactoring-expert.md
├── rust-specialist.md
├── security-analyst.md
├── test-writer.md
└── vuejs-specialist.md
```

### Desired Codebase Changes

```bash
# New files to be added
.claude/agents/project-manager-prp.md       # Main agent definition
tests/agents/test_project_manager_prp.py    # Agent testing suite
PRPs/ai_docs/project_management_patterns.md # Project management guidance
utils/todo_parser.py                        # Todo parsing utilities
utils/dependency_analyzer.py                # Dependency analysis tools
```

### Known Gotchas & TDD Considerations

```python
# CRITICAL: Claude Code agent testing patterns
# Agents are configuration files, not executable code - testing requires simulation
# Must test agent behavior through Claude Code Task tool integration

# CRITICAL: ACTIVE_TODOS.md format requirements
# Must maintain exact format compatibility for existing todo parsing
# Priority levels: high, medium, low
# Status tracking: pending, in_progress, completed
# Dependency format: "Dependencies: PRP-001, PRP-002"

# CRITICAL: PRP integration requirements  
# Must suggest PRP creation for tasks >2 hour estimates
# PRP references must follow format: "PRP: PRPs/XXX-description.md"
```

## TDD Implementation Methodology

### Red Phase: Test Creation First

**Requirements**: Create comprehensive tests for agent behavior before implementation.

```python
# Agent Behavior Test Pattern
def test_project_manager_analyzes_complex_feature():
    """
    Test Description: Agent can analyze complex feature and generate todos
    Expected Outcome: Structured todo hierarchy with dependencies
    Failure Conditions: Missing todos, incorrect dependencies, wrong format
    """
    # Arrange: Mock complex feature description
    feature_description = "Implement user authentication with OAuth, email verification, and role-based access control"
    
    # Act: Simulate agent analysis
    result = simulate_agent_response("project-manager-prp", feature_description)
    
    # Assert: Verify structured output with dependencies
    assert result.has_todo_hierarchy()
    assert result.has_dependency_analysis()
    assert result.follows_active_todos_format()
```

### Green Phase: Minimal Implementation

**Requirements**: Create minimal agent configuration that passes tests.

```yaml
# Minimal Agent Configuration Pattern
name: "project-manager-prp"
description: "Analyzes complex features and generates structured todo hierarchies"
tools: ["*"]
behavior: |
  Minimal behavior to pass tests - analyze requirements and generate basic todos
```

### Refactor Phase: Code Improvement

**Requirements**: Enhance agent capabilities while maintaining test suite.

```yaml
# Enhanced agent with comprehensive project management capabilities
# Sophisticated analysis algorithms, dependency detection, PRP integration
```

## Implementation Blueprint

### TDD Task Breakdown (Red-Green-Refactor for each)

```yaml
Task 1: [RED] CREATE tests for project analysis functionality
  - IMPLEMENT: Test suite for feature analysis and todo generation
  - TEST_FRAMEWORK: pytest with agent simulation utilities
  - COVERAGE: 95%+ for analysis logic and todo generation
  - PATTERNS: Mock agent responses and validate output format
  - DEPENDENCIES: None

Task 2: [GREEN] IMPLEMENT minimal project-manager-prp agent
  - IMPLEMENT: Basic agent configuration with core analysis capability
  - FOLLOW pattern: .claude/agents/code-reviewer.md structure
  - NAMING: project-manager-prp.md following established conventions
  - PLACEMENT: .claude/agents/project-manager-prp.md
  - DEPENDENCIES: Task 1 completion (tests exist and fail)

Task 3: [REFACTOR] ENHANCE agent with advanced capabilities
  - IMPLEMENT: Sophisticated analysis, dependency detection, PRP integration
  - OPTIMIZE: Analysis accuracy, todo quality, dependency detection
  - ENHANCE: Time estimation, priority assignment, PRP recommendations
  - VALIDATE: All tests pass with enhanced functionality
  - DEPENDENCIES: Task 2 completion (basic agent works)

Task 4: [RED] CREATE tests for todo parsing utilities
  - IMPLEMENT: Test suite for ACTIVE_TODOS.md format parsing and generation
  - TEST_FRAMEWORK: pytest with todo format validation
  - COVERAGE: 100% for parsing and format generation
  - PATTERNS: Test various todo formats and edge cases
  - DEPENDENCIES: Task 3 completion (agent enhanced)

Task 5: [GREEN] IMPLEMENT todo parsing utilities
  - IMPLEMENT: todo_parser.py with ACTIVE_TODOS.md format support
  - FOLLOW pattern: Existing utility patterns in project
  - NAMING: Clear, descriptive function names for parsing operations
  - PLACEMENT: utils/todo_parser.py
  - DEPENDENCIES: Task 4 completion (parsing tests exist)

Task 6: [REFACTOR] OPTIMIZE todo parsing and generation
  - IMPLEMENT: Enhanced parsing with validation and error handling
  - OPTIMIZE: Performance and reliability of parsing operations
  - ENHANCE: Format validation, edge case handling, extensibility
  - VALIDATE: All parsing tests pass with robust error handling
  - DEPENDENCIES: Task 5 completion (basic parsing works)

Task 7: [RED] CREATE tests for dependency analysis system
  - IMPLEMENT: Test suite for task dependency detection and analysis
  - TEST_FRAMEWORK: pytest with dependency graph testing
  - COVERAGE: 95%+ for dependency detection algorithms
  - PATTERNS: Test complex dependency scenarios and circular detection
  - DEPENDENCIES: Task 6 completion (parsing enhanced)

Task 8: [GREEN] IMPLEMENT dependency analysis utilities
  - IMPLEMENT: dependency_analyzer.py with graph analysis capability
  - FOLLOW pattern: Clean architecture with separation of concerns
  - NAMING: Clear function names for dependency operations
  - PLACEMENT: utils/dependency_analyzer.py
  - DEPENDENCIES: Task 7 completion (dependency tests exist)

Task 9: [REFACTOR] ENHANCE dependency analysis with advanced features
  - IMPLEMENT: Circular dependency detection, critical path analysis
  - OPTIMIZE: Analysis performance and accuracy
  - ENHANCE: Dependency visualization, conflict resolution suggestions
  - VALIDATE: All dependency tests pass with advanced features
  - DEPENDENCIES: Task 8 completion (basic dependency analysis works)
```

### Implementation Patterns & Key Details

```python
# Agent Configuration Pattern for Project Management
agent_config = {
    "name": "project-manager-prp",
    "description": "Intelligent project analysis and todo hierarchy generation",
    "tools": ["*"],  # Full tool access for analysis
    "proactive_triggers": [
        "complex feature requests",
        "project planning requests", 
        "todo organization needs"
    ],
    "behavior": """
    TDD Approach:
    - Analyze feature complexity and break down into manageable tasks
    - Generate dependency graphs with clear blocking relationships
    - Estimate effort and assign priorities based on impact and dependencies
    - Suggest PRP creation for tasks requiring detailed specification
    - Maintain ACTIVE_TODOS.md format compatibility
    - Integrate with existing PRP workflow and validation systems
    """
}
```

### Integration Points

```yaml
ACTIVE_TODOS_INTEGRATION:
  - format: "Maintain exact format compatibility with existing todos"
  - parsing: "Robust parsing of existing todos and dependencies"
  - generation: "Generate new todos in consistent format"

PRP_WORKFLOW_INTEGRATION:
  - detection: "Identify tasks requiring PRP creation (>2 hour estimates)"
  - suggestion: "Recommend appropriate PRP templates based on task type"
  - reference: "Generate proper PRP references in PRPs/XXX-description.md format"

AGENT_ECOSYSTEM_INTEGRATION:
  - coordination: "Work with other agents through proper tool usage"
  - handoff: "Pass complex tasks to appropriate specialist agents"
  - validation: "Use existing validation agents for quality assurance"
```

## Validation Loop

### Level 0: Test Creation (TDD Red Phase)

```bash
# CRITICAL: Create comprehensive test suite before implementation
# Tests must validate agent behavior through simulation

# Create agent behavior tests
pytest tests/agents/test_project_manager_prp.py -v --tb=short
# Expected: All tests fail initially, proving test correctness

# Create utility function tests  
pytest tests/utils/test_todo_parser.py -v --tb=short
pytest tests/utils/test_dependency_analyzer.py -v --tb=short
# Expected: Utility tests fail, validating test logic
```

### Level 1: Syntax & Style (TDD Green Phase Setup)

```bash
# Validate agent configuration syntax
# Agent files are YAML/Markdown - validate format

# YAML syntax validation for agent config
python -c "import yaml; yaml.safe_load(open('.claude/agents/project-manager-prp.md').read())"

# Python syntax validation for utilities
python -m py_compile utils/todo_parser.py
python -m py_compile utils/dependency_analyzer.py

# Code formatting
ruff check utils/ --fix
mypy utils/ --strict

# Expected: Clean, well-formatted code with proper types
```

### Level 2: Unit Tests (TDD Green Phase Validation)

```bash
# Execute test suite after minimal implementation

# Agent behavior testing through simulation
pytest tests/agents/test_project_manager_prp.py -v --cov=utils

# Utility function testing  
pytest tests/utils/ -v --cov=utils --cov-report=term-missing

# Integration testing with ACTIVE_TODOS.md format
pytest tests/integration/test_todo_integration.py -v

# Expected: All tests pass with 95%+ coverage
```

### Level 3: Integration Testing (System Validation)

```bash
# Test integration with Claude Code agent system

# Agent invocation testing (requires Claude Code environment)
# Test through actual Claude Code Task tool if available

# ACTIVE_TODOS.md integration testing
python tests/integration/test_active_todos_integration.py

# PRP workflow integration testing
python tests/integration/test_prp_workflow.py

# Dependency analysis system testing
python tests/integration/test_dependency_system.py

# Expected: All integrations work correctly with existing systems
```

### Level 4: Creative & Domain-Specific Validation (TDD Refactor Phase)

```bash
# Domain-specific validation for project management functionality

# Complex project analysis testing
python tests/performance/test_complex_project_analysis.py

# Dependency graph performance testing  
python tests/performance/test_dependency_performance.py

# Agent behavior validation with real-world scenarios
python tests/scenarios/test_real_world_projects.py

# Todo format compliance validation
python tests/compliance/test_todo_format_compliance.py

# Expected: Performance meets requirements, handles complex scenarios correctly
```

## Final Validation Checklist

### TDD Methodology Validation

- [ ] All tests written before implementation (Red Phase complete)
- [ ] Minimal implementation passes all tests (Green Phase complete)  
- [ ] Enhanced functionality maintains test suite (Refactor Phase complete)
- [ ] Test coverage exceeds 95% for core functionality
- [ ] Integration tests validate system interactions

### Agent Functionality Validation

- [ ] Agent can analyze complex features and generate structured todos
- [ ] Dependency analysis correctly identifies blocking relationships
- [ ] Time estimation provides realistic effort assessments
- [ ] ACTIVE_TODOS.md format maintained perfectly
- [ ] PRP integration suggests appropriate PRP creation

### Technical Implementation Validation

- [ ] Agent configuration follows established patterns
- [ ] Utility functions are robust with comprehensive error handling
- [ ] Integration with existing systems works seamlessly
- [ ] Performance requirements met for complex project analysis
- [ ] Code quality meets project standards

### Workflow Integration Validation

- [ ] Agent integrates properly with Claude Code Task tool
- [ ] ACTIVE_TODOS.md parsing and generation works correctly
- [ ] PRP workflow integration enables autonomous development
- [ ] Dependency management prevents implementation bottlenecks
- [ ] Agent coordination with other specialists functions properly

---

## Anti-Patterns to Avoid

- ❌ Don't create agent without comprehensive testing - agent behavior must be validated
- ❌ Don't break ACTIVE_TODOS.md format compatibility - existing workflows depend on it
- ❌ Don't ignore dependency analysis - leads to implementation bottlenecks
- ❌ Don't skip PRP integration - breaks autonomous development workflow
- ❌ Don't over-complicate initial implementation - follow TDD minimal approach
- ❌ Don't bypass integration testing - agent must work with existing systems
- ❌ Don't ignore time estimation accuracy - unrealistic estimates harm planning