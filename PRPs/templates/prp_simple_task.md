name: "Simple Task PRP Template v1.0"
description: |
  Streamlined PRP template for straightforward tasks that still enforces
  TDD methodology but with simplified structure for quick implementation.

---

## Goal

**Task Goal**: [Clear, specific task to accomplish]

**Deliverable**: [Concrete output - file, function, component, configuration]

**Success Definition**: [How you'll know this is complete and working]

## Why This Task

- [Immediate value or problem this solves]
- [Context within larger feature or project]
- [Technical necessity or improvement]

## What Will Be Implemented

[Specific functionality or changes with clear scope]

### Success Criteria

- [ ] [Specific, testable outcome]
- [ ] [Integration or compatibility requirement]
- [ ] [Quality or performance standard]

## All Needed Context

### Context Completeness Check

_This simple task provides the essential context needed for straightforward implementation._

### Documentation & References

```yaml
# Essential context for implementation
- pattern: [Path to similar implementation in codebase]
  why: [How to follow existing patterns]

- docs: [Relevant documentation or API reference]
  why: [Key information needed for implementation]
```

### Current State

```bash
# What exists now (if anything)
[Brief description of current state]
```

### Desired State

```bash
# What should exist after completion
[Brief description of target state]
```

### Known Constraints

- [Technical constraints or limitations]
- [Integration requirements or dependencies]
- [Performance or quality requirements]

## TDD Implementation

### Red Phase: Write Failing Test

```python
# Test specification for this task
def test_[task_functionality]():
    """Test that [specific behavior] works correctly"""
    # Arrange: Set up test conditions
    # Act: Execute the functionality
    # Assert: Verify expected outcome
    pass
```

### Green Phase: Minimal Implementation

```python
# Minimal code to make test pass
def [task_function]():
    """[Brief description of what this does]"""
    # Simplest implementation that satisfies test
    pass
```

### Refactor Phase: Improve Quality

```python
# Enhanced implementation with proper error handling
def [task_function]():
    """[Comprehensive description with examples]"""
    # Improved implementation with:
    # - Error handling
    # - Type hints
    # - Documentation
    # - Performance optimization
    pass
```

## Implementation Blueprint

### Simple Task Implementation (TDD Approach)

```yaml
Task 1: CREATE failing test for [functionality]
  - IMPLEMENT: Test that defines expected behavior
  - FRAMEWORK: [pytest/Jest/appropriate testing framework]
  - VALIDATION: Test should fail initially
  - DEPENDENCIES: Test environment setup

Task 2: IMPLEMENT minimal solution
  - IMPLEMENT: Minimal code to make test pass
  - FOLLOW pattern: [Path to similar implementation]
  - NAMING: [Clear, descriptive naming]
  - PLACEMENT: [Exact file location]
  - DEPENDENCIES: Task 1 completion (failing test exists)

Task 3: REFACTOR and enhance
  - IMPLEMENT: Code quality improvements
  - ENHANCE: Error handling, documentation, type hints
  - OPTIMIZE: Performance if needed
  - VALIDATE: All tests still pass
  - DEPENDENCIES: Task 2 completion (basic implementation works)
```

### Integration Points

```yaml
CONFIGURATION:
  - add to: [config file if needed]
  - pattern: [configuration pattern to follow]

IMPORTS:
  - add to: [files that need to import this functionality]
  - pattern: [import pattern to follow]
```

## Validation Loop

### Level 0: Test Creation (TDD Red Phase)

```bash
# Create failing test first
[Test framework command] [test_file] -v
# Expected: Test fails because implementation doesn't exist yet
```

### Level 1: Syntax & Style (Implementation Phase)

```bash
# Code quality validation
[Linting command] [implementation_file] --fix
[Type checking command] [implementation_file]
[Formatting command] [implementation_file]

# Expected: Clean, well-formatted code
```

### Level 2: Unit Tests (TDD Green Phase)

```bash
# Test execution after implementation
[Test framework command] [test_file] -v
[Coverage command] [test_file] --coverage

# Expected: All tests pass with adequate coverage
```

### Level 3: Integration Testing (System Validation)

```bash
# Integration validation
[Integration test or manual verification command]
[System test command if applicable]

# Expected: Integration with existing system works correctly
```

### Level 4: Simple Task Validation

```bash
# Task-specific validation
[Domain-specific validation command]
[Performance check if needed]

# Expected: Task meets specific requirements and constraints
```

### Completion Checklist

- [ ] Test written and initially fails
- [ ] Implementation makes test pass
- [ ] Code quality meets standards (linting, typing)
- [ ] Integration with existing system works
- [ ] Documentation updated if needed

---

## Anti-Patterns to Avoid

- ❌ Don't skip writing the test first - even simple tasks benefit from TDD
- ❌ Don't over-engineer simple tasks - keep implementation minimal initially
- ❌ Don't ignore existing patterns - consistency is important even for small tasks
- ❌ Don't skip validation - simple tasks can still break existing functionality