name: "Red-Green-Refactor PRP Template v1.0"
description: |
  Specialized PRP template for refactoring tasks that emphasizes the TDD cycle
  with explicit Red-Green-Refactor phases and comprehensive regression testing.

---

## Goal

**Refactoring Goal**: [Specific code quality improvement or architectural change]

**Target Code**: [Exact files, classes, or modules being refactored]

**Success Definition**: [Measurable improvement in code quality, performance, or maintainability]

## Current State Analysis

**Code Quality Issues**: [Specific problems with current implementation]

**Technical Debt**: [Accumulated technical debt being addressed]

**Performance Issues**: [Performance bottlenecks or inefficiencies]

**Maintainability Concerns**: [Code complexity, readability, or extensibility issues]

## Why Refactor Now

- [Business impact of current code issues]
- [Development velocity impact]
- [Risk mitigation and future-proofing]
- [Alignment with architectural standards]

## What Will Change

[Specific transformations and improvements with before/after examples]

### Refactoring Success Criteria

- [ ] [Specific quality metrics improved (complexity, coverage, performance)]
- [ ] [Maintainability improvements (readability, extensibility)]
- [ ] [All existing functionality preserved (zero regression)]
- [ ] [New capabilities enabled by refactoring]

## All Needed Context

### Current Implementation Analysis

```yaml
# MUST ANALYZE - Current code structure and patterns
- current_file: [path/to/existing/code.py]
  why: [What needs to be refactored and why]
  issues: [Specific code smells, complexity, or performance issues]
  dependencies: [What other code depends on this]

- test_coverage: [path/to/existing/tests/]
  why: [Current test coverage and gaps]
  quality: [Test quality and regression protection]
  gaps: [Areas needing additional test coverage]
```

### Refactoring Context & Patterns

```yaml
# MUST READ - Refactoring patterns and best practices
- pattern: [Specific refactoring pattern to apply - Extract Method, Strategy, etc.]
  why: [Why this pattern solves the identified problems]
  example: [Reference implementation or similar refactoring]

- architecture: [Target architectural pattern or principle]
  why: [How this improves system design]
  constraints: [Architectural constraints to maintain]
```

### Current Codebase Before Refactoring

```bash
# Current structure that needs refactoring
[Insert current problematic code structure]
```

### Desired Codebase After Refactoring

```bash
# Target structure after refactoring
[Insert improved code structure]
```

### Refactoring Risks & Constraints

```python
# CRITICAL: Preserve existing behavior - zero regression requirement
# CRITICAL: Maintain backward compatibility for public APIs
# CRITICAL: Performance must not degrade during refactoring
# CRITICAL: All existing tests must continue to pass
```

## Red-Green-Refactor Implementation Methodology

### RED PHASE: Comprehensive Test Coverage

**Objective**: Ensure complete test coverage before any code changes.

```python
# Test Coverage Analysis Pattern
def test_[existing_functionality]_[scenario]():
    """
    REGRESSION TEST: Validate current behavior before refactoring
    This test must pass both before and after refactoring
    """
    # Test current implementation behavior
    # Document expected outcomes
    # Include edge cases and error conditions
    pass
```

**Red Phase Checklist**:
- [ ] Identify all current functionality that must be preserved
- [ ] Write comprehensive regression tests for existing behavior
- [ ] Achieve 100% test coverage for code being refactored
- [ ] Validate all tests pass with current implementation
- [ ] Document any gaps in current functionality

### GREEN PHASE: Safe Incremental Refactoring

**Objective**: Refactor code incrementally while maintaining all tests.

```python
# Incremental Refactoring Pattern
class RefactoredComponent:
    """
    REFACTORING STEP: [Specific refactoring being applied]
    
    Maintains all existing behavior while improving:
    - Code structure and organization
    - Performance characteristics
    - Readability and maintainability
    """
    
    def refactored_method(self):
        # Improved implementation that passes all existing tests
        pass
```

**Green Phase Checklist**:
- [ ] Apply refactoring incrementally (small, safe steps)
- [ ] Run tests after each refactoring step
- [ ] Ensure all existing tests continue to pass
- [ ] Maintain backward compatibility for public interfaces
- [ ] Document any behavioral improvements

### REFACTOR PHASE: Quality and Performance Enhancement

**Objective**: Optimize and enhance while maintaining test suite integrity.

```python
# Enhancement Pattern
class OptimizedComponent:
    """
    OPTIMIZATION PHASE: Enhanced version with quality improvements
    
    Enhancements while maintaining compatibility:
    - Performance optimization
    - Error handling improvement
    - Documentation and type hints
    - Code organization and clarity
    """
    
    def optimized_method(self) -> ReturnType:
        # Enhanced implementation with better performance/quality
        pass
```

**Refactor Phase Checklist**:
- [ ] Optimize performance without changing behavior
- [ ] Improve error handling and edge case management
- [ ] Enhance documentation and type annotations
- [ ] Extract reusable patterns and components
- [ ] Validate all optimizations through testing

## Implementation Blueprint

### Phase 1: RED - Test Coverage and Analysis

```yaml
Task 1: ANALYZE current implementation thoroughly
  - DOCUMENT: Current behavior and edge cases
  - IDENTIFY: Code smells, performance issues, complexity
  - MAP: Dependencies and integration points
  - MEASURE: Current performance and quality metrics

Task 2: CREATE comprehensive regression test suite
  - IMPLEMENT: Tests for all existing functionality
  - COVERAGE: 100% of code being refactored
  - SCENARIOS: Happy path, edge cases, error conditions
  - VALIDATE: All tests pass with current implementation

Task 3: ESTABLISH quality and performance baselines
  - MEASURE: Current performance metrics
  - DOCUMENT: Code complexity and maintainability scores
  - BASELINE: Test execution time and coverage
  - BENCHMARK: Memory usage and execution efficiency
```

### Phase 2: GREEN - Safe Incremental Refactoring

```yaml
Task 4: REFACTOR incrementally with continuous validation
  - STEP_1: Extract methods and reduce complexity
  - STEP_2: Improve naming and code organization  
  - STEP_3: Consolidate duplicate code and patterns
  - STEP_4: Enhance error handling and edge cases
  - VALIDATE: Run tests after each step

Task 5: MAINTAIN backward compatibility
  - PRESERVE: All public interfaces and contracts
  - ENSURE: Existing integrations continue working
  - TEST: Integration points and external dependencies
  - DOCUMENT: Any interface changes or deprecations

Task 6: OPTIMIZE data structures and algorithms
  - IMPROVE: Algorithm efficiency where beneficial
  - OPTIMIZE: Data structure choices for performance
  - REDUCE: Memory footprint and resource usage
  - VALIDATE: Performance improvements through testing
```

### Phase 3: REFACTOR - Enhancement and Optimization

```yaml
Task 7: ENHANCE code quality and maintainability
  - IMPROVE: Code readability and documentation
  - ADD: Comprehensive type hints and annotations
  - EXTRACT: Reusable patterns into utilities
  - ORGANIZE: Code structure for better maintainability

Task 8: OPTIMIZE performance and resource usage
  - PROFILE: Performance bottlenecks and inefficiencies
  - OPTIMIZE: Critical performance paths
  - CACHE: Expensive operations where appropriate
  - VALIDATE: Performance improvements meet requirements

Task 9: FINALIZE and validate complete refactoring
  - VERIFY: All success criteria met
  - MEASURE: Quality and performance improvements
  - DOCUMENT: Changes and improvement achieved
  - CELEBRATE: Successful refactoring completion
```

## Validation Loop

### Level 0: Pre-Refactoring Validation (RED Phase)

```bash
# CRITICAL: Establish comprehensive test coverage before refactoring

# Run existing test suite and measure coverage
pytest tests/ --cov=[module] --cov-report=html --cov-fail-under=100

# Identify and test current behavior patterns
python -m pytest tests/ -v --tb=short

# Performance baseline measurement
python -m pytest tests/ --benchmark-only --benchmark-save=before_refactor

# Expected: 100% test coverage, all tests pass, performance baseline established
```

### Level 1: Refactoring Safety Validation (GREEN Phase)

```bash
# Run after each incremental refactoring step

# Immediate test validation
pytest tests/ -x --tb=short  # Stop on first failure

# Code quality validation  
ruff check [refactored_files] --fix
mypy [refactored_files]
complexity [refactored_files]  # Measure complexity reduction

# Continuous integration validation
pytest tests/ --cov=[module] --cov-report=term-missing

# Expected: All tests pass, code quality improves, coverage maintained
```

### Level 2: Regression and Integration Testing (GREEN Phase)

```bash
# Comprehensive regression testing after refactoring

# Full test suite execution
pytest tests/ -v --tb=long

# Integration testing with dependent systems
pytest tests/integration/ -v

# Performance regression testing
python -m pytest tests/ --benchmark-only --benchmark-compare=0001_before_refactor

# API compatibility testing (if applicable)
pytest tests/api/ -v --tb=short

# Expected: No regressions, integrations work, performance maintained or improved
```

### Level 3: Quality and Performance Validation (REFACTOR Phase)

```bash
# Validate quality improvements and optimizations

# Code quality metrics comparison
sonarqube-cli --compare-baseline  # Or similar quality tool
radon cc [refactored_files] --average  # Cyclomatic complexity
radon mi [refactored_files]  # Maintainability index

# Performance improvement validation
python -m pytest tests/ --benchmark-only --benchmark-save=after_refactor
python benchmark_comparison.py  # Compare before/after performance

# Memory usage and efficiency testing
python -m memory_profiler [performance_tests]
pytest tests/performance/ -v

# Load testing (if applicable)
locust -f load_tests.py --headless -u 100 -r 10 -t 60s

# Expected: Quality metrics improved, performance optimized, efficiency gains demonstrated
```

### Level 4: Comprehensive Refactoring Validation

```bash
# Final validation of complete refactoring success

# End-to-end functionality testing
pytest tests/e2e/ -v --tb=short

# Stress testing with edge cases
pytest tests/stress/ -v

# Long-running stability testing
python stability_test.py --duration=3600  # 1 hour stability test

# Production-like environment testing
docker-compose -f docker-compose.test.yml up --build
pytest tests/integration/ --env=production-like

# Documentation and maintainability validation
sphinx-build -b html docs/ docs/_build/
codespell [refactored_files]  # Documentation spell checking

# Expected: System stable under load, documentation updated, production-ready
```

## Final Refactoring Validation Checklist

### Technical Validation

- [ ] All existing functionality preserved (zero regression)
- [ ] Test coverage maintained at 100% for refactored code
- [ ] Performance metrics improved or maintained
- [ ] Code complexity reduced measurably
- [ ] All integration points continue working correctly

### Quality Improvements

- [ ] Code readability and maintainability significantly improved
- [ ] Technical debt reduced measurably
- [ ] Error handling enhanced and tested
- [ ] Documentation updated and comprehensive
- [ ] Type safety improved with comprehensive annotations

### Red-Green-Refactor Methodology

- [ ] Comprehensive tests written before refactoring (Red Phase)
- [ ] Incremental refactoring with continuous test validation (Green Phase)
- [ ] Quality and performance optimization completed (Refactor Phase)
- [ ] All phases completed with proper validation
- [ ] Refactoring benefits clearly demonstrated and measured

### Maintainability and Future-Proofing

- [ ] Code structure improved for future modifications
- [ ] Reusable patterns extracted and documented
- [ ] Dependencies properly managed and minimized
- [ ] Architecture improved and constraints satisfied
- [ ] Team knowledge transfer completed

---

## Anti-Patterns to Avoid

- ❌ Don't refactor without comprehensive test coverage - leads to regressions
- ❌ Don't make large changes without incremental validation - high risk approach  
- ❌ Don't optimize without measuring - premature optimization waste
- ❌ Don't change behavior during refactoring - breaks zero-regression rule
- ❌ Don't skip integration testing - refactoring can break system interactions
- ❌ Don't ignore performance impact - refactoring should improve, not degrade
- ❌ Don't forget to update documentation - maintainability requires good docs