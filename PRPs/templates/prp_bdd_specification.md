name: "BDD Specification PRP Template v1.0"
description: |
  Behavior-Driven Development focused PRP template for user-facing features
  that emphasizes Given-When-Then specifications and acceptance testing.

---

## Goal

**Feature Goal**: [User-facing behavior or capability being delivered]

**User Value**: [Specific value this feature provides to users]

**Success Definition**: [How users and stakeholders will measure success]

## User Story

**As a** [specific user type/role]
**I want** [specific capability or functionality]
**So that** [specific benefit or value achieved]

### Acceptance Criteria (Given-When-Then Format)

```gherkin
Feature: [Feature name in business language]

Scenario: [Primary happy path scenario]
  Given [initial context and preconditions]
  When [user action or trigger event]
  Then [expected outcome and system response]
  And [additional expected outcomes]

Scenario: [Alternative path or edge case]
  Given [different initial context]
  When [user action in this context]
  Then [expected outcome for this scenario]

Scenario: [Error handling scenario]
  Given [error-prone context]
  When [action that might fail]
  Then [graceful error handling and user feedback]
```

## User Personas and Contexts

**Primary User**: [Detailed primary user persona]
- **Context**: [When and why they use this feature]
- **Goals**: [What they're trying to accomplish]
- **Pain Points**: [Current frustrations this addresses]

**Secondary Users**: [Other user types who interact with this feature]
- **Context**: [Their interaction context]
- **Requirements**: [Their specific needs and constraints]

## Why This Feature Now

- [Business value and user impact justification]
- [User research or feedback driving this feature]
- [Competitive analysis or market requirements]
- [Technical enablers or dependencies now available]

## What Users Will Experience

[Detailed user experience description with concrete examples]

### User Journey Flow

1. **Entry Point**: [How users discover and access this feature]
2. **Primary Actions**: [Main interactions users will perform]
3. **Feedback and Confirmation**: [How system responds to user actions]
4. **Completion and Follow-up**: [How users complete tasks and what happens next]

### User Interface Requirements

- [Specific UI elements and interactions required]
- [Accessibility requirements and considerations]
- [Mobile/responsive design requirements]
- [Performance requirements from user perspective]

## All Needed Context

### User Experience Context

```yaml
# MUST UNDERSTAND - User research and design requirements
- user_research: [Path to user interviews, surveys, or analytics]
  why: [How this informs feature design and priorities]
  insights: [Key user insights that drive requirements]

- design_mockups: [Path to wireframes, prototypes, or designs]
  why: [Visual representation of intended user experience]
  interactions: [Specific interaction patterns and flows]

- accessibility_requirements: [WCAG compliance level and specific needs]
  why: [Accessibility standards and user accommodations needed]
  testing: [How accessibility will be validated]
```

### Technical Implementation Context

```yaml
# MUST READ - Technical context for BDD implementation
- existing_ui_patterns: [Path to similar UI components or patterns]
  why: [Consistency with existing user experience]
  components: [Reusable components and interaction patterns]

- api_specifications: [API endpoints or services supporting this feature]
  why: [Backend services and data requirements]
  contracts: [API contracts and data formats]

- testing_frameworks: [BDD testing tools - Cucumber, Playwright, etc.]
  why: [How BDD scenarios will be automated and validated]
  patterns: [Existing BDD test patterns to follow]
```

### Current User Experience Analysis

```bash
# Current user journey or system state
[Describe current user experience or absence of feature]
```

### Desired User Experience

```bash
# Target user experience after implementation
[Describe ideal user experience and interaction flow]
```

### BDD Implementation Constraints

```python
# CRITICAL: User experience must be intuitive and accessible
# CRITICAL: Performance requirements for user-facing interactions
# CRITICAL: Cross-browser and device compatibility requirements
# CRITICAL: Integration with existing user authentication and authorization
```

## BDD Implementation Methodology

### Feature Specification Phase

**Objective**: Define clear, testable behavior specifications.

```gherkin
# BDD Specification Pattern
Feature: [Feature name in business language]
  In order to [business value]
  As a [user role]
  I want [capability]

  Background:
    Given [common preconditions for all scenarios]

  Scenario Outline: [Parameterized scenario for multiple test cases]
    Given [context with <parameter>]
    When [action with <parameter>]
    Then [outcome with <parameter>]
    
    Examples:
      | parameter | expected_result |
      | value1    | result1        |
      | value2    | result2        |
```

### Implementation Phase (Red-Green-Refactor)

**Red Phase**: Write failing BDD scenarios and step definitions
**Green Phase**: Implement minimal code to make scenarios pass
**Refactor Phase**: Improve user experience and code quality

### User Acceptance Testing

**Objective**: Validate feature meets user needs and business requirements.

## Implementation Blueprint

### Phase 1: Behavior Specification and Test Automation

```yaml
Task 1: DEFINE comprehensive BDD scenarios
  - IMPLEMENT: Gherkin scenarios covering all user paths
  - COVERAGE: Happy path, alternative flows, error scenarios
  - LANGUAGE: Business-readable scenario descriptions
  - VALIDATION: Stakeholder review and approval of scenarios

Task 2: CREATE automated BDD test framework integration
  - IMPLEMENT: Step definitions for scenario automation
  - FRAMEWORK: [Cucumber/Playwright/Cypress with BDD support]
  - INFRASTRUCTURE: Test data setup and teardown automation
  - DEPENDENCIES: Test environment and data management

Task 3: ESTABLISH user acceptance criteria validation
  - IMPLEMENT: Automated acceptance test execution
  - CRITERIA: All acceptance criteria must pass for feature completion
  - REPORTING: Clear pass/fail reporting for stakeholders
  - INTEGRATION: CI/CD pipeline integration for continuous validation
```

### Phase 2: User Interface Implementation

```yaml
Task 4: IMPLEMENT user interface components (TDD approach)
  - RED: Write component tests based on BDD scenarios
  - GREEN: Implement minimal UI to satisfy behavior requirements
  - REFACTOR: Enhance user experience and visual design
  - VALIDATION: BDD scenario execution against UI implementation

Task 5: INTEGRATE with backend services and data
  - IMPLEMENT: API integration for data requirements
  - TESTING: Mock services for UI development and testing
  - VALIDATION: End-to-end scenario testing with real services
  - ERROR_HANDLING: Graceful handling of service failures

Task 6: OPTIMIZE user experience and performance
  - IMPLEMENT: Performance optimization for user interactions
  - TESTING: User experience testing under various conditions
  - ACCESSIBILITY: Screen reader and keyboard navigation testing
  - VALIDATION: Performance benchmarks and user feedback
```

### Phase 3: User Acceptance and Production Readiness

```yaml
Task 7: CONDUCT user acceptance testing with real users
  - IMPLEMENT: User testing sessions with target personas
  - FEEDBACK: Collection and analysis of user feedback
  - ITERATION: Refinements based on user testing results
  - VALIDATION: User satisfaction and task completion metrics

Task 8: PREPARE for production deployment
  - IMPLEMENT: Production configuration and monitoring
  - TESTING: Production-like environment validation
  - DOCUMENTATION: User documentation and help resources
  - ROLLOUT: Gradual rollout strategy and rollback plan
```

## Validation Loop

### Level 0: Scenario Definition and Validation

```bash
# CRITICAL: All scenarios must be defined and validated before implementation

# Validate BDD scenario syntax and completeness
cucumber --dry-run features/  # Check scenario syntax
gherkin-lint features/*.feature  # Validate Gherkin quality

# Stakeholder review and approval
cucumber --format json features/ > scenario_report.json
# Review scenarios with product owner and users

# Expected: All scenarios syntactically correct and stakeholder-approved
```

### Level 1: Step Definition and Test Automation

```bash
# Implement and validate BDD step definitions

# BDD framework setup and validation
cucumber --format progress features/  # Run scenarios (should fail initially)
playwright test --config=bdd.config.js  # Alternative BDD framework

# Step definition coverage validation
cucumber --format usage features/  # Check step definition coverage

# Test data and environment setup
docker-compose -f test-env.yml up  # Start test environment
python setup_test_data.py  # Initialize test data

# Expected: All step definitions implemented, test environment ready
```

### Level 2: User Interface and Integration Testing

```bash
# Validate UI implementation against BDD scenarios

# Automated BDD scenario execution
cucumber features/ --format html --out reports/bdd_report.html
playwright test --config=bdd.config.js --reporter=html

# Cross-browser and device testing
playwright test --config=bdd.config.js --browser=chromium,firefox,webkit
# Mobile device testing with scenarios

# API integration validation
postman run api_integration_tests.json  # API integration tests
pytest tests/api/ -v  # Backend API tests supporting BDD scenarios

# Expected: All BDD scenarios pass across browsers and devices
```

### Level 3: User Acceptance and Performance Testing

```bash
# Validate user acceptance criteria and performance requirements

# Performance testing with user scenarios
artillery run load_test_scenarios.yml  # Load testing with user paths
lighthouse-ci --config=lighthouse.json  # Performance auditing

# Accessibility testing
pa11y-ci --sitemap http://localhost:3000/sitemap.xml
axe-cli --rules wcag2a,wcag2aa,wcag21aa http://localhost:3000

# User experience validation
percy exec -- cucumber features/  # Visual regression testing
# Manual user testing sessions with target personas

# Expected: Performance meets requirements, accessibility compliant, positive user feedback
```

### Level 4: Production Readiness and Monitoring

```bash
# Validate production readiness and establish monitoring

# Production environment BDD validation
cucumber features/ --profile production  # Production environment testing
k6 run production_load_test.js  # Production load testing

# Monitoring and alerting setup
# Setup user experience monitoring and alerting
# Configure error tracking and user feedback collection

# User documentation and help system validation
# Test user onboarding flow and help documentation
# Validate support ticket system integration

# Expected: Production-ready with monitoring, documentation complete, support ready
```

## Final BDD Validation Checklist

### Behavior Specification Validation

- [ ] All user scenarios defined in clear, business-readable language
- [ ] Acceptance criteria complete and testable
- [ ] Edge cases and error scenarios covered
- [ ] Stakeholder review and approval completed
- [ ] BDD scenarios executable and automated

### User Experience Validation

- [ ] User interface intuitive and accessible
- [ ] User journey smooth and efficient
- [ ] Performance meets user expectations
- [ ] Cross-browser and device compatibility validated
- [ ] User feedback positive and requirements met

### Technical Implementation Validation

- [ ] All BDD scenarios automated and passing
- [ ] Integration with backend services working correctly
- [ ] Error handling graceful and user-friendly
- [ ] Security and data privacy requirements met
- [ ] Code quality and maintainability standards satisfied

### Production Readiness Validation

- [ ] Production environment testing completed successfully
- [ ] Monitoring and alerting configured and tested
- [ ] User documentation comprehensive and accessible
- [ ] Support processes and escalation paths established
- [ ] Rollout plan tested and rollback procedures verified

---

## Anti-Patterns to Avoid

- ❌ Don't write scenarios in technical language - use business-readable descriptions
- ❌ Don't skip stakeholder review of scenarios - misaligned requirements waste effort
- ❌ Don't implement UI without BDD scenarios - leads to features that don't meet user needs
- ❌ Don't ignore accessibility requirements - excludes users and creates compliance issues
- ❌ Don't skip user testing - assumptions about user experience are often wrong
- ❌ Don't deploy without production BDD validation - production issues impact real users
- ❌ Don't forget user documentation - great features are useless if users can't understand them