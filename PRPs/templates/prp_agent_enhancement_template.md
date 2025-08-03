# PRP-Aware Agent Enhancement Template

This template provides the standardized pattern for enhancing existing specialized agents with PRP execution capabilities, TDD methodology integration, and autonomous workflow coordination.

## Enhancement Pattern Structure

### 1. Preserve Existing Domain Expertise
- **MAINTAIN**: All existing domain-specific knowledge and capabilities
- **PRESERVE**: Specialized tool recommendations and best practices  
- **KEEP**: Domain-specific patterns and architectural guidance
- **RETAIN**: Proactive invocation triggers and use cases

### 2. Add PRP Execution Capabilities Section

```markdown
## PRP Execution Capabilities

When invoked with a PRP specification, this agent follows the structured TDD-PRP methodology:

### PRP Structure Understanding
- Parses Goal, Why, What, Context, Implementation Blueprint, and Validation Loop sections
- Extracts domain-specific requirements and constraints from All Needed Context
- Identifies success criteria and measurable outcomes
- Maps PRP requirements to {DOMAIN}-specific implementation patterns

### TDD Methodology Integration
- **Red Phase**: Creates failing tests based on PRP requirements using {DOMAIN_TEST_FRAMEWORK}
- **Green Phase**: Implements minimal {DOMAIN_LANGUAGE} code to make tests pass
- **Refactor Phase**: Improves code quality using {DOMAIN_BEST_PRACTICES} while maintaining test suite

### 4-Level Validation Loop
- **Level 0**: Test Creation - Write failing {DOMAIN_TEST_FRAMEWORK} tests first
- **Level 1**: Syntax & Style - {DOMAIN_LINTER} and {DOMAIN_FORMATTER} validation
- **Level 2**: Unit Tests - {DOMAIN_TEST_RUNNER} execution with coverage reporting
- **Level 3**: Integration Testing - {DOMAIN_INTEGRATION_APPROACH} validation
- **Level 4**: Creative Validation - {DOMAIN_SPECIFIC_ADVANCED_VALIDATION}

### Autonomous Execution Pattern
When executing a PRP autonomously:
1. Parse PRP requirements and extract implementation tasks
2. Analyze existing codebase patterns for {DOMAIN} consistency
3. Create comprehensive test suite following {DOMAIN} conventions (Red Phase)
4. Implement solution incrementally using {DOMAIN} best practices (Green Phase)
5. Refactor and optimize following {DOMAIN} performance patterns (Refactor Phase)
6. Execute complete validation loop with {DOMAIN} tooling
7. Report completion status for project management integration

### Context-Aware Implementation
- Analyzes existing {DOMAIN} codebase patterns and follows established conventions
- Leverages {DOMAIN}-specific libraries and frameworks appropriately
- Applies {DOMAIN} security and performance best practices
- Integrates with existing {DOMAIN} system architecture and constraints
- Uses {DOMAIN} ecosystem tools and package managers
```

### 3. Domain-Specific TDD Integration Examples

#### Python Specialist Enhancement
```markdown
### TDD Integration for Python Development
- **Test Framework**: pytest with fixtures, parametrization, and coverage
- **Red Phase**: Create failing pytest tests for all public functions and classes
- **Green Phase**: Implement minimal Python code following PEP 8 and type hints
- **Refactor Phase**: Apply pythonic patterns, performance optimization, and security best practices

### Validation Loop (Python-Specific)
- **Level 0**: pytest tests that fail initially (--tb=short for clarity)
- **Level 1**: ruff check/format, mypy type checking, black formatting
- **Level 2**: pytest execution with coverage reporting (>90% required)
- **Level 3**: Integration testing with requests, database connections, API endpoints
- **Level 4**: Performance profiling with cProfile, security scanning with bandit, dependency auditing with safety
```

#### React Specialist Enhancement
```markdown
### TDD Integration for React Development
- **Test Framework**: Jest with React Testing Library and user-event
- **Red Phase**: Create failing component and integration tests with accessibility checks
- **Green Phase**: Implement minimal React components with TypeScript and proper hooks usage
- **Refactor Phase**: Optimize for performance, accessibility, maintainability, and bundle size

### Validation Loop (React-Specific)
- **Level 0**: Jest/RTL tests that fail initially with clear assertions
- **Level 1**: ESLint with React rules, TypeScript checking, Prettier formatting
- **Level 2**: Jest test execution with coverage, component testing with RTL
- **Level 3**: Component integration, user interaction testing, routing validation
- **Level 4**: Visual regression testing, Lighthouse performance audits, accessibility testing with axe
```

#### API Design Specialist Enhancement
```markdown
### TDD Integration for API Development
- **Test Framework**: Domain-appropriate testing (pytest for Python APIs, Jest for Node APIs)
- **Red Phase**: Create failing API endpoint tests with request/response validation
- **Green Phase**: Implement minimal API endpoints with proper HTTP status codes
- **Refactor Phase**: Add authentication, rate limiting, documentation, error handling

### Validation Loop (API-Specific)
- **Level 0**: API integration tests that fail initially
- **Level 1**: OpenAPI schema validation, linting, code formatting
- **Level 2**: Unit tests for business logic, endpoint testing with coverage
- **Level 3**: Full API integration testing, authentication flows, error scenarios
- **Level 4**: Load testing, security scanning, API documentation validation, contract testing
```

### 4. Autonomous Workflow Integration Section

```markdown
## Autonomous Workflow Integration

### Status Reporting
- Integrates with ACTIVE_TODOS.md for completion tracking
- Reports implementation progress and validation results
- Updates PRP references with completion status
- Provides detailed error reports for debugging

### Multi-Agent Coordination
- Identifies when PRP requires multiple specialist agents
- Coordinates with project-manager-prp for task breakdown
- Communicates with other specialists for integration requirements
- Ensures consistent coding standards across agent implementations

### Error Handling and Recovery
- Graceful handling of test failures and implementation errors
- Automatic retry mechanisms for transient failures
- Clear error reporting with actionable resolution steps
- Fallback to human intervention when autonomous resolution fails

### Performance and Efficiency
- Optimizes for fast execution while maintaining quality
- Caches context analysis results for similar PRPs
- Reuses existing code patterns and components when appropriate
- Balances thoroughness with autonomous development speed
```

## Domain-Specific Customization Guidelines

### Language Specialists
- **Testing**: Use language-native testing frameworks (pytest, Jest, go test, cargo test, JUnit)
- **Validation**: Language-specific linting, type checking, and formatting tools
- **Integration**: Package managers, dependency resolution, version compatibility
- **Advanced**: Performance profiling, security scanning, ecosystem-specific tools

### Framework Specialists  
- **Testing**: Framework-specific testing approaches (component testing, E2E testing)
- **Validation**: Framework conventions, build systems, deployment verification
- **Integration**: Framework ecosystem integration, plugin compatibility
- **Advanced**: Framework-specific performance optimization, security considerations

### Infrastructure Specialists
- **Testing**: Infrastructure as code testing, deployment validation
- **Validation**: Configuration validation, security compliance, resource optimization
- **Integration**: Multi-service coordination, environment consistency
- **Advanced**: Monitoring setup, disaster recovery, scalability testing

### Database Specialists
- **Testing**: Schema testing, query validation, data integrity checks
- **Validation**: Migration safety, performance optimization, backup verification
- **Integration**: Application data layer integration, replication setup
- **Advanced**: Performance tuning, security auditing, disaster recovery testing

## Enhancement Implementation Checklist

### Pre-Enhancement Analysis
- [ ] Read and understand existing agent capabilities and domain expertise
- [ ] Identify domain-specific testing frameworks and tooling
- [ ] Map domain patterns to TDD methodology requirements
- [ ] Determine appropriate validation approaches for the domain

### Enhancement Implementation
- [ ] Add PRP Execution Capabilities section with domain customization
- [ ] Integrate TDD methodology with domain-specific tooling
- [ ] Implement 4-level validation loop with appropriate tools
- [ ] Add autonomous workflow integration capabilities
- [ ] Preserve all existing domain expertise and patterns

### Post-Enhancement Validation
- [ ] Verify enhanced agent maintains all original capabilities
- [ ] Test PRP execution with domain-specific requirements
- [ ] Validate TDD integration works with domain tooling
- [ ] Confirm autonomous execution and status reporting
- [ ] Ensure consistent enhancement patterns across agents

## Quality Standards

### Code Quality
- All enhanced agents must maintain existing quality standards
- TDD integration must not compromise domain expertise
- Validation loops must be meaningful and executable
- Error handling must be comprehensive and actionable

### Documentation Quality
- Clear documentation of PRP execution capabilities
- Comprehensive examples of TDD integration
- Detailed validation loop explanations
- Practical autonomous execution guidance

### Integration Quality
- Seamless integration with existing Claude Code workflow
- Consistent behavior across all enhanced agents
- Reliable autonomous execution without human intervention
- Effective multi-agent coordination for complex PRPs

---

This template ensures consistent, high-quality enhancement of all specialist agents while preserving their unique domain expertise and adding powerful autonomous PRP execution capabilities.