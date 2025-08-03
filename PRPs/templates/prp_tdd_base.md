name: "TDD-Enhanced PRP Base Template v1.0"
description: |
  Comprehensive Test-Driven Development enhanced Product Requirement Prompt template
  that enforces test-first methodology with 4-level validation loops.

---

## Goal

**Feature Goal**: [Specific, measurable end state with testable outcomes]

**Deliverable**: [Concrete artifact - service, component, API, integration, etc.]

**Success Definition**: [How you'll know this is complete and working correctly]

## User Persona (if applicable)

**Target User**: [Specific user type - developer, end user, admin, system, etc.]

**Use Case**: [Primary scenario when this feature will be used]

**User Journey**: [Step-by-step flow of interaction with this feature]

**Pain Points Addressed**: [Specific problems this feature solves]

## Why

- [Business value and user impact]
- [Integration with existing features and systems]
- [Problems this solves and for whom]
- [Technical debt reduction or architectural improvement]

## What

[User-visible behavior and technical requirements with specific acceptance criteria]

### Success Criteria (Test-First Requirements)

- [ ] [Specific, testable outcomes that can be validated]
- [ ] [Measurable performance or quality requirements]
- [ ] [Integration requirements with existing systems]
- [ ] [Security and compliance requirements]

## All Needed Context

### Context Completeness Check

_Before implementing this PRP, validate: "If someone knew nothing about this codebase, would they have everything needed to implement this successfully with test-first methodology?"_

### Test-First Context Requirements

```yaml
# MUST INCLUDE - Test patterns and examples for TDD implementation
- test_pattern: [Path to similar test files in codebase]
  why: [Testing approach and patterns to follow]
  framework: [pytest, Jest, go test, etc.]
  coverage: [Required test coverage percentage]

- existing_tests: [Path to related test suites]
  why: [Integration testing patterns and mock usage]
  fixtures: [Test data and setup patterns to reuse]
```

### Documentation & References

```yaml
# MUST READ - Include these in your context window
- url: [Complete URL with section anchor]
  why: [Specific methods/concepts needed for implementation]
  critical: [Key insights that prevent implementation errors]

- file: [exact/path/to/pattern/file.py]
  why: [Specific pattern to follow - class structure, error handling, etc.]
  pattern: [Brief description of what pattern to extract]
  gotcha: [Known constraints or limitations to avoid]

- docfile: [PRPs/ai_docs/domain_specific.md]
  why: [Custom documentation for complex patterns]
  section: [Specific section if document is large]
```

### Current Codebase Analysis

```bash
# Run `tree -L 3` to understand project structure
[Insert current codebase tree structure here]
```

### Desired Codebase Changes

```bash
# Show exactly what files will be added/modified
[Insert desired codebase structure with new files]
```

### Known Gotchas & TDD Considerations

```python
# CRITICAL: [Library/Framework] TDD patterns and requirements
# Example: FastAPI requires async test patterns with pytest-asyncio
# Example: React components need proper mocking for external dependencies

# CRITICAL: Test environment setup requirements
# Example: Database test isolation, mock configuration, fixture management

# CRITICAL: Performance testing considerations
# Example: Load testing requirements, benchmark thresholds
```

## TDD Implementation Methodology

### Red Phase: Test Creation First

**Requirements**: All tests must be written before any implementation code.

```python
# Test Specification Pattern
def test_[feature]_[scenario]():
    """
    Test Description: [What behavior is being tested]
    Expected Outcome: [What should happen]
    Failure Conditions: [What would indicate failure]
    """
    # Arrange: Set up test data and mocks
    # Act: Execute the functionality being tested
    # Assert: Verify expected outcomes
    pass
```

### Green Phase: Minimal Implementation

**Requirements**: Write only enough code to make tests pass, no more.

```python
# Implementation Pattern
def [feature_function]():
    """
    Minimal implementation to satisfy test requirements.
    Focus on making tests pass, not on optimization or completeness.
    """
    pass
```

### Refactor Phase: Code Improvement

**Requirements**: Improve code quality while maintaining all tests.

```python
# Refactoring Checklist:
# - Extract common patterns into reusable functions
# - Improve naming and code clarity
# - Optimize performance where needed
# - Add comprehensive error handling
# - Enhance documentation and type hints
```

## Implementation Blueprint

### TDD Task Breakdown (Red-Green-Refactor for each)

```yaml
Task 1: [RED] CREATE tests for [component/feature]
  - IMPLEMENT: Comprehensive test suite that initially fails
  - TEST_FRAMEWORK: [pytest/Jest/go test/etc.]
  - COVERAGE: [Required test coverage percentage]
  - PATTERNS: [Specific test patterns and fixtures]
  - DEPENDENCIES: Test environment setup

Task 2: [GREEN] IMPLEMENT minimal [component/feature]
  - IMPLEMENT: Minimal code to make tests pass
  - FOLLOW pattern: [Path to similar implementation]
  - NAMING: [Specific naming conventions]
  - PLACEMENT: [Exact file locations]
  - DEPENDENCIES: Task 1 completion (tests exist and fail)

Task 3: [REFACTOR] OPTIMIZE and enhance [component/feature]
  - IMPLEMENT: Code quality improvements while maintaining tests
  - OPTIMIZE: Performance, readability, maintainability
  - ENHANCE: Error handling, documentation, type safety
  - VALIDATE: All tests still pass after changes
  - DEPENDENCIES: Task 2 completion (basic implementation works)

[Repeat for each major component...]
```

### Implementation Patterns & Key Details

```python
# TDD Implementation Pattern for this domain
class [FeatureClass]:
    """
    PATTERN: [Specific pattern to follow from existing codebase]
    
    Red Phase:
    - Write comprehensive test suite first
    - Include edge cases and error conditions
    - Validate test failures before implementation
    
    Green Phase:
    - Minimal implementation to pass tests
    - Focus on correctness, not optimization
    - Follow existing code patterns and conventions
    
    Refactor Phase:
    - Improve code structure and performance
    - Add comprehensive error handling
    - Enhance documentation and type hints
    """
    
    def [method](self, [parameters]) -> [return_type]:
        # Implementation details with TDD considerations
        pass
```

### Integration Points

```yaml
DATABASE:
  - migration: "[Specific database changes required]"
  - tests: "Test database integration with fixtures and rollback"
  - pattern: "[Database testing pattern to follow]"

CONFIGURATION:
  - add to: [config file path]
  - pattern: "[Configuration pattern and validation]"
  - tests: "Configuration validation tests"

API_ENDPOINTS:
  - add to: [API route file]
  - pattern: "[API testing pattern with requests/responses]"
  - tests: "Endpoint integration tests with authentication/authorization"

EXTERNAL_SERVICES:
  - integration: "[External service integration requirements]"
  - mocking: "[How to mock external services in tests]"
  - tests: "Mock external services and test error handling"
```

## Validation Loop

### Level 0: Test Creation (TDD Red Phase)

```bash
# CRITICAL: Write all tests first before any implementation
# All tests must fail initially - this validates test correctness

# Create comprehensive test suite
[Test creation commands specific to domain/framework]

# Validate tests fail as expected
[Test execution commands that should show failures]

# Expected: All tests fail initially, proving test correctness
```

### Level 1: Syntax & Style (TDD Green Phase Setup)

```bash
# Run after minimal implementation to pass tests

# Linting and formatting (adapt to technology stack)
ruff check [new_files] --fix     # Python
eslint [new_files] --fix         # JavaScript/TypeScript  
go fmt [new_files]               # Go
cargo fmt                       # Rust

# Type checking (where applicable)
mypy [new_files]                 # Python
tsc --noEmit                     # TypeScript

# Expected: Clean code that passes tests with proper formatting
```

### Level 2: Unit Tests (TDD Green Phase Validation)

```bash
# Execute test suite after minimal implementation

# Framework-specific test execution
pytest [test_files] -v                    # Python
npm test -- [test_files]                 # JavaScript/React
go test [package]                        # Go
cargo test                              # Rust

# Coverage validation
pytest --cov=[module] --cov-report=term-missing  # Python
npm test -- --coverage                          # JavaScript

# Expected: All tests pass with required coverage percentage
```

### Level 3: Integration Testing (System Validation)

```bash
# Test integration with existing systems and dependencies

# API integration testing
curl -X POST [endpoint] -H "Content-Type: application/json" -d '[test_data]'

# Database integration testing
[Database connection and query tests]

# Service integration testing
[External service integration validation]

# End-to-end workflow testing
[Complete user workflow validation commands]

# Expected: All integrations work correctly, proper error handling
```

### Level 4: Creative & Domain-Specific Validation (TDD Refactor Phase)

```bash
# Domain-specific validation and creative testing approaches

# Performance testing (if applicable)
[Performance benchmarking commands]

# Security testing (if applicable)
[Security scanning and vulnerability testing]

# Load testing (if applicable)
[Load testing commands and thresholds]

# Business logic validation
[Domain-specific validation commands]

# Expected: Performance meets requirements, security validated, business logic correct
```

## Final Validation Checklist

### TDD Methodology Validation

- [ ] All tests written before implementation (Red Phase complete)
- [ ] Minimal implementation passes all tests (Green Phase complete)
- [ ] Code quality improved without breaking tests (Refactor Phase complete)
- [ ] Test coverage meets or exceeds required percentage
- [ ] All edge cases and error conditions tested

### Technical Validation

- [ ] All 4 validation levels completed successfully
- [ ] Integration with existing systems validated
- [ ] Performance requirements met
- [ ] Security requirements satisfied
- [ ] Error handling comprehensive and tested

### Implementation Validation

- [ ] All success criteria from "What" section met
- [ ] User persona requirements satisfied (if applicable)
- [ ] Business value delivered as specified
- [ ] Technical debt reduced or architectural improvements made
- [ ] Documentation updated and comprehensive

### Quality Assurance

- [ ] Code follows existing patterns and conventions
- [ ] All dependencies properly managed
- [ ] Configuration changes properly integrated
- [ ] Deployment considerations addressed
- [ ] Monitoring and observability implemented

---

## Anti-Patterns to Avoid

- ❌ Don't write implementation before tests - violates TDD fundamentals
- ❌ Don't skip test failures in Red Phase - proves tests work correctly
- ❌ Don't over-implement in Green Phase - minimal code to pass tests
- ❌ Don't refactor without running tests - breaks TDD safety net
- ❌ Don't skip edge cases in testing - leads to production failures
- ❌ Don't ignore performance testing - optimization must be validated
- ❌ Don't bypass integration testing - system interactions must work