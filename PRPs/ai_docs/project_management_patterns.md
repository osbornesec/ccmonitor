# Project Management Patterns for TDD-PRP Development

## Overview

This document provides comprehensive patterns and best practices for project management within the TDD-PRP development methodology, specifically for the `project-manager-prp` agent.

## Core Principles

### 1. Feature Decomposition Strategy

**Hierarchical Breakdown**
- Complex features → Epic-level todos
- Epic todos → Feature-level todos  
- Feature todos → Implementation-level todos
- Implementation todos → Task-level todos

**Complexity Assessment**
```yaml
Simple (1-4 hours):
  characteristics:
    - Single component modification
    - Minimal dependencies
    - Well-understood requirements
  examples:
    - UI component styling updates
    - Configuration changes
    - Simple API endpoint additions

Medium (4-12 hours):
  characteristics:
    - Multiple component interaction
    - Some dependencies
    - Moderate complexity
  examples:
    - Authentication integration
    - Database schema changes
    - API endpoint with business logic

Complex (12+ hours):
  characteristics:
    - System-wide changes
    - Multiple dependencies
    - Architecture decisions required
  examples:
    - Microservices decomposition
    - Complete feature modules
    - Infrastructure overhauls
```

### 2. Dependency Analysis Patterns

**Sequential Dependencies**
```
A → B → C (B cannot start until A completes)
```

**Parallel Dependencies**
```
    → B
A ←     → D
    → C
```

**Diamond Dependencies**
```
A → B → D
  ↘ C ↗
```

**Critical Path Identification**
- Longest sequence of dependent tasks
- Determines minimum project completion time
- Guides resource allocation priorities

### 3. Time Estimation Guidelines

**Base Estimation Formula**
```
Estimate = (Optimistic + 4×Realistic + Pessimistic) / 6
```

**Complexity Multipliers**
- New technology: +50%
- External dependencies: +25%
- High uncertainty: +75%
- Critical path tasks: +25%

**Buffer Allocation**
- Simple tasks: 10-20% buffer
- Medium tasks: 25-35% buffer
- Complex tasks: 50-75% buffer

## ACTIVE_TODOS.md Format Patterns

### Standard Section Structure
```markdown
## [Priority Level] - [Functional Area] (Dependencies: [List or None])
- [ ] **PRP-XXX**: [Clear, actionable task description] (Est: X-Y hours)
  - [ ] [Specific subtask 1]
  - [ ] [Specific subtask 2]
  - [ ] [Specific subtask 3]
  - Status: [Not Started|In Progress|Completed]
  - Dependencies: [PRP-XXX, PRP-YYY or None]
  - PRP: `PRPs/XXX-descriptive-name.md` (for complex tasks)
```

### Priority Level Guidelines

**High Priority**
- Foundation tasks (setup, infrastructure)
- Critical path blockers
- Security-related tasks
- Core business logic

**Medium Priority**
- Feature enhancements
- Non-critical integrations
- Performance optimizations
- User experience improvements

**Low Priority**
- Nice-to-have features
- Documentation improvements
- Code cleanup tasks
- Future-proofing activities

### Dependency Format Patterns

**None Dependencies**
```markdown
Dependencies: None
```

**Single Dependency**
```markdown
Dependencies: PRP-001
```

**Multiple Dependencies**
```markdown
Dependencies: PRP-001, PRP-002, PRP-003
```

**External Dependencies**
```markdown
Dependencies: External-API-Setup, PRP-001
```

## PRP Recommendation Patterns

### Automatic PRP Suggestions

**Threshold Rules**
- Tasks >2 hours → Suggest PRP
- Architecture decisions → Always suggest PRP
- External integrations → Always suggest PRP
- Performance-critical code → Suggest PRP

**PRP Naming Conventions**
```
PRPs/[3-digit-number]-[descriptive-kebab-case].md

Examples:
- PRPs/001-user-authentication-system.md
- PRPs/015-payment-gateway-integration.md
- PRPs/042-performance-monitoring-dashboard.md
```

### PRP Template Selection Guide

**Use `prp_tdd_base.md` for:**
- General feature implementation
- New component development
- API endpoint creation
- Standard business logic

**Use `prp_bdd_specification.md` for:**
- User-facing features
- Complex user workflows
- Features requiring stakeholder validation
- Customer-centric functionality

**Use `prp_red_green_refactor.md` for:**
- Code refactoring tasks
- Performance optimization
- Technical debt reduction
- Architecture improvements

**Use `prp_simple_task.md` for:**
- Configuration changes
- Minor bug fixes
- Simple component updates
- Straightforward implementations

## Agent Communication Patterns

### Input Analysis Patterns

**Feature Description Processing**
1. Extract core functionality requirements
2. Identify technical components needed
3. Assess complexity and scope
4. Determine dependency relationships
5. Estimate effort requirements

**Keywords for Complexity Detection**
```yaml
High Complexity Indicators:
  - "distributed", "microservices", "architecture"
  - "real-time", "streaming", "websockets"
  - "machine learning", "AI", "analytics"
  - "multi-tenant", "scalable", "high-availability"

Medium Complexity Indicators:
  - "authentication", "authorization", "security"
  - "payment", "billing", "subscription"
  - "notification", "email", "messaging"
  - "search", "filtering", "pagination"

Simple Complexity Indicators:
  - "configuration", "settings", "preferences"
  - "styling", "layout", "responsive"
  - "validation", "formatting", "display"
  - "logging", "monitoring", "debugging"
```

### Output Generation Patterns

**Todo Generation Algorithm**
1. Identify main functional areas
2. Break down each area into specific tasks
3. Estimate effort for each task
4. Determine dependencies between tasks
5. Assign priority levels based on criticality
6. Generate PRP suggestions for complex tasks
7. Format in ACTIVE_TODOS.md structure

**Dependency Resolution**
```python
def resolve_dependencies(tasks):
    """
    Resolve task dependencies and detect conflicts
    """
    dependency_graph = build_graph(tasks)
    
    # Check for circular dependencies
    cycles = detect_cycles(dependency_graph)
    if cycles:
        suggest_cycle_resolution(cycles)
    
    # Calculate critical path
    critical_path = find_critical_path(dependency_graph)
    
    # Suggest parallel execution opportunities
    parallel_groups = find_parallel_tasks(dependency_graph)
    
    return {
        'dependency_graph': dependency_graph,
        'critical_path': critical_path,
        'parallel_opportunities': parallel_groups,
        'total_estimated_time': calculate_total_time(critical_path)
    }
```

## Integration Patterns

### With PRP Infrastructure

**PRP Creation Workflow**
1. Agent identifies complex task (>2 hours or architectural)
2. Suggests appropriate PRP template based on task type
3. Generates PRP filename following naming convention
4. References PRP in todo item
5. PRP-aware agents can later implement using the PRP

**Validation Integration**
1. Generated todos must pass format validation
2. Dependencies must be resolvable
3. Time estimates must be realistic
4. PRP suggestions must follow conventions

### With Other Agents

**Handoff Patterns**
```markdown
To Specialist Agents:
- Complex todos → domain specialist agents
- Architecture decisions → software architect agent
- Security tasks → security specialist agent
- Performance issues → performance optimizer agent

From Other Agents:
- Receive complex feature requests
- Process architecture recommendations
- Integrate security requirements
- Incorporate performance constraints
```

## Best Practices

### Do's
- ✅ Break complex features into 2-4 hour tasks
- ✅ Clearly define dependencies between tasks
- ✅ Use consistent estimation methodology
- ✅ Suggest PRPs for complex tasks
- ✅ Maintain ACTIVE_TODOS.md format compliance
- ✅ Consider parallel execution opportunities
- ✅ Account for integration and testing time

### Don'ts
- ❌ Create tasks larger than 8 hours without PRPs
- ❌ Ignore dependency relationships
- ❌ Use vague or non-actionable task descriptions
- ❌ Skip time estimation or use arbitrary estimates
- ❌ Break format compatibility with existing tools
- ❌ Forget to consider testing and deployment tasks
- ❌ Overlook external dependencies and constraints

## Troubleshooting Guide

### Common Issues

**Issue: Tasks too granular**
- Symptom: Many 30-minute tasks
- Solution: Combine related micro-tasks into 2-3 hour chunks

**Issue: Missing dependencies**
- Symptom: Tasks seem independent but require coordination
- Solution: Review integration points and add missing dependencies

**Issue: Unrealistic estimates**
- Symptom: Consistent over/under estimation
- Solution: Review historical data and adjust estimation factors

**Issue: Poor priority assignment**
- Symptom: Low-priority tasks blocking high-priority ones
- Solution: Re-analyze critical path and adjust priorities

### Validation Checklist

- [ ] All tasks have clear, actionable descriptions
- [ ] Time estimates are realistic and include buffers
- [ ] Dependencies are correctly identified and resolvable
- [ ] Priority levels align with business needs and critical path
- [ ] Complex tasks (>2 hours) have PRP suggestions
- [ ] Format complies with ACTIVE_TODOS.md standard
- [ ] Total project time is reasonable for scope
- [ ] Parallel execution opportunities are identified

## Example Patterns

### E-commerce Platform Breakdown
```markdown
## High Priority - Foundation (Dependencies: None)
- [ ] **PRP-001**: Project Setup and Architecture (Est: 3-4 hours)
  - [ ] Initialize project structure
  - [ ] Configure build system and tooling
  - [ ] Setup development environment
  - Status: Not Started
  - Dependencies: None
  - PRP: `PRPs/001-project-architecture.md`

## High Priority - Core Systems (Dependencies: PRP-001)
- [ ] **PRP-002**: User Authentication System (Est: 6-8 hours)
  - [ ] Design authentication architecture
  - [ ] Implement OAuth2 integration
  - [ ] Add role-based permissions
  - [ ] Create user session management
  - Status: Not Started
  - Dependencies: PRP-001
  - PRP: `PRPs/002-authentication-system.md`

- [ ] **PRP-003**: Product Catalog System (Est: 8-10 hours)
  - [ ] Design product data schema
  - [ ] Implement catalog API endpoints
  - [ ] Add search and filtering capabilities
  - [ ] Create admin management interface
  - Status: Not Started
  - Dependencies: PRP-001
  - PRP: `PRPs/003-product-catalog.md`
```

This pattern demonstrates proper hierarchical breakdown, realistic estimates, clear dependencies, and appropriate PRP suggestions for complex tasks.