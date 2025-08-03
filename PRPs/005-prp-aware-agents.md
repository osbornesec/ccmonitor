name: "PRP-005: Convert Existing Agents to PRP-Aware Implementation"
description: |

---

## Goal

**Feature Goal**: Transform all 24 existing specialized agents into PRP-aware agents that understand TDD methodology, can execute PRPs autonomously, and integrate seamlessly with our todo-driven development workflow.

**Deliverable**: Enhanced versions of all existing agents (python-specialist, react-specialist, etc.) that include PRP execution capabilities, TDD validation enforcement, and autonomous workflow integration.

**Success Definition**: All agents can receive PRP specifications, execute them with test-first methodology, validate implementation through 4-level validation loops, and update project status autonomously.

## User Persona

**Target User**: Autonomous Development System and PRP Orchestrator
**Use Case**: Executing generated PRPs with domain-specific expertise and TDD methodology
**User Journey**:
1. Agent receives PRP from todo-to-prp-orchestrator
2. Agent analyzes PRP requirements and domain-specific context
3. Agent implements solution using TDD methodology (Red-Green-Refactor)
4. Agent validates implementation through 4-level validation loops
5. Agent updates project status and marks todo as completed
6. System proceeds to next todo in autonomous workflow

**Pain Points Addressed**:
- Agents lack understanding of PRP structure and TDD methodology
- No systematic approach to PRP execution across different domains
- Inconsistent validation and quality assurance across specialists
- No integration between agent completion and project management

## Why

- Enable all existing agents to participate in autonomous PRP-driven development
- Provide consistent TDD methodology across all domain specialists
- Create unified validation approach while maintaining domain expertise
- Integrate agent completion with project management and todo tracking
- Establish foundation for fully autonomous, self-managing development

## What

Comprehensive enhancement of all 24 existing specialized agents to include:

- PRP structure understanding and execution capabilities
- TDD methodology integration with Red-Green-Refactor cycles
- 4-level validation loop enforcement (Syntax, Unit, Integration, Creative)
- Autonomous workflow integration with status reporting
- Domain-specific PRP customization while maintaining core methodology
- Context-aware implementation with codebase pattern recognition

### Success Criteria

- [ ] All 24 existing agents enhanced with PRP execution capabilities
- [ ] TDD methodology enforced across all domain specialists
- [ ] 4-level validation loops implemented for each agent type
- [ ] Agents can autonomously execute PRPs without human intervention
- [ ] Status reporting integrates with ACTIVE_TODOS.md updates
- [ ] Domain-specific customization maintains specialist expertise
- [ ] Consistent quality standards across all agent implementations

## All Needed Context

### Context Completeness Check

_This PRP provides everything needed to systematically enhance all existing agents with PRP-aware capabilities while preserving their domain expertise and adding autonomous execution capabilities._

### Documentation & References

```yaml
# MUST READ - Include these in your context window
- file: .claude/agents/
  why: Complete catalog of all 24 existing specialized agents requiring enhancement
  critical: Agent capabilities, domain expertise, current structure and patterns
  pattern: Existing agent metadata, description format, proactive invocation triggers

- file: PRPs/001-tdd-prp-infrastructure.md
  why: TDD methodology and 4-level validation approach for agent integration
  critical: Red-Green-Refactor cycles, validation loop structure, test-first enforcement
  pattern: TDD integration patterns and validation level requirements

- file: PRPs/templates/prp_tdd_base.md
  why: PRP structure that agents must understand and execute
  critical: Section structure, context requirements, implementation blueprint format
  pattern: Goal/Why/What/Context/Implementation/Validation loop structure

- file: /home/michael/dev/PRPs-agentic-eng/PRPs/example-from-workshop-mcp-crawl4ai-refactor-1.md
  why: Real-world PRP execution example showing comprehensive implementation approach
  pattern: Domain-specific customization, progressive validation, comprehensive testing
  critical: How specialists should adapt general PRP methodology to domain expertise

- file: ACTIVE_TODOS.md
  why: Todo status format and project management integration requirements
  critical: Status transitions, completion tracking, PRP reference management
  pattern: Agent completion reporting and status update requirements
```

### Current Agent Architecture

```bash
.claude/agents/
├── api-design-specialist.md      # API and GraphQL design expert
├── aws-specialist.md             # Cloud infrastructure specialist
├── blockchain-specialist.md      # Smart contracts and Web3
├── code-reviewer.md             # Code quality and review
├── context-pruner.md            # Context optimization
├── cypress-testing-specialist.md # E2E testing framework
├── docker-kubernetes-specialist.md # Container orchestration
├── flutter-specialist.md        # Cross-platform mobile
├── go-specialist.md             # Go language and concurrency
├── java-specialist.md           # Enterprise Java development
├── javascript-typescript-specialist.md # Modern JS/TS ecosystem
├── machine-learning-specialist.md # ML/AI model development
├── meta-agent.md                # Agent generation
├── mongodb-specialist.md        # NoSQL database
├── nextjs-specialist.md         # React full-stack framework
├── performance-optimizer.md     # Code optimization
├── postgresql-specialist.md     # Relational database
├── project-manager-prp.md       # Project management (from PRP-002)
├── python-specialist.md         # Python ecosystem
├── react-specialist.md          # React component development
├── refactoring-expert.md        # Code structure improvement
├── rust-specialist.md           # Systems programming
├── security-analyst.md          # Security and vulnerability
├── test-writer.md               # Test generation
├── todo-to-prp-orchestrator.md  # PRP orchestration (from PRP-004)
└── vuejs-specialist.md          # Vue.js framework
```

### Desired PRP-Aware Agent Enhancement

Each agent will be enhanced with:

```markdown
## PRP Execution Capabilities
- PRP structure understanding and parsing
- TDD methodology integration
- 4-level validation loop enforcement
- Autonomous execution without human intervention

## TDD Integration Patterns
- Red Phase: Write failing tests first
- Green Phase: Minimal implementation to pass tests
- Refactor Phase: Code improvement while maintaining tests

## Validation Loop Implementation
- Level 0: Test Creation (Red Phase)
- Level 1: Syntax & Style (Green Phase setup)
- Level 2: Unit Tests (Green Phase validation)
- Level 3: Integration Testing (System validation)
- Level 4: Domain-Specific Creative Validation

## Autonomous Workflow Integration
- Status reporting to project management system
- Context-aware implementation using codebase patterns
- Error handling and recovery mechanisms
```

### Known Enhancement Patterns & Requirements

```python
# CRITICAL: Maintain existing agent expertise while adding PRP capabilities
# Pattern: Extend agent descriptions with PRP sections, don't replace domain knowledge

# CRITICAL: TDD methodology must be adapted to each domain
# Pattern: Python agents use pytest, React agents use Jest/RTL, etc.

# CRITICAL: Validation loops must be domain-specific
# Pattern: API specialists test endpoints, Database specialists test queries

# CRITICAL: All agents must integrate with UV runner environment
# Pattern: Domain-specific commands must work within UV virtual environment

# CRITICAL: Agent completion must trigger todo status updates
# Pattern: Agents report completion for todo-update-hook integration

# CRITICAL: Context awareness must leverage domain-specific patterns  
# Pattern: React agents understand component patterns, Python agents understand service patterns
```

## Implementation Blueprint

### Implementation Strategy: Systematic Agent Enhancement

```yaml
ENHANCEMENT_APPROACH:
  - Phase 1: Core Infrastructure Agents (5 agents)
  - Phase 2: Language Specialists (8 agents)  
  - Phase 3: Framework Specialists (6 agents)
  - Phase 4: Specialized Domain Experts (5 agents)

ENHANCEMENT_PATTERN:
  - Preserve existing domain expertise completely
  - Add PRP execution capabilities as new sections
  - Integrate TDD methodology with domain-specific tools
  - Implement 4-level validation with appropriate tooling
  - Add autonomous workflow and status reporting
```

### Implementation Tasks (ordered by dependencies and complexity)

```yaml
Task 1: CREATE agent enhancement template and patterns
  - IMPLEMENT: Standard PRP-aware agent enhancement template
  - DEFINE: Common sections and patterns for all agent enhancements
  - ESTABLISH: TDD integration patterns for different domains
  - NAMING: prp_agent_enhancement_template.md
  - PLACEMENT: PRPs/templates/ directory
  - DEPENDENCIES: Understanding of all existing agents

Task 2: ENHANCE Core Infrastructure Agents (Phase 1)
  - AGENTS: code-reviewer.md, performance-optimizer.md, refactoring-expert.md, security-analyst.md, test-writer.md
  - IMPLEMENT: PRP execution with quality assurance focus
  - TDD_APPROACH: Existing testing expertise enhanced with systematic validation
  - VALIDATION: Code quality metrics, security scans, performance benchmarks
  - DEPENDENCIES: Task 1 (enhancement template)

Task 3: ENHANCE Language Specialists (Phase 2)  
  - AGENTS: python-specialist.md, javascript-typescript-specialist.md, go-specialist.md, rust-specialist.md, java-specialist.md
  - IMPLEMENT: Language-specific TDD with appropriate testing frameworks
  - TDD_APPROACH: pytest (Python), Jest (JS/TS), go test (Go), cargo test (Rust), JUnit (Java)
  - VALIDATION: Language-specific linting, type checking, package management
  - DEPENDENCIES: Task 2 (infrastructure patterns established)

Task 4: ENHANCE Framework Specialists (Phase 3)
  - AGENTS: react-specialist.md, nextjs-specialist.md, vuejs-specialist.md, flutter-specialist.md, docker-kubernetes-specialist.md, aws-specialist.md
  - IMPLEMENT: Framework-specific testing and deployment validation
  - TDD_APPROACH: Component testing, integration testing, deployment validation
  - VALIDATION: Framework-specific testing tools and deployment verification
  - DEPENDENCIES: Task 3 (language foundation established)

Task 5: ENHANCE Database and Specialized Agents (Phase 4)
  - AGENTS: postgresql-specialist.md, mongodb-specialist.md, api-design-specialist.md, machine-learning-specialist.md, blockchain-specialist.md, cypress-testing-specialist.md
  - IMPLEMENT: Domain-specific testing and validation approaches
  - TDD_APPROACH: Schema testing, API testing, model validation, contract testing
  - VALIDATION: Domain-specific tooling and validation frameworks
  - DEPENDENCIES: Task 4 (framework patterns established)

Task 6: CREATE PRP execution coordination system
  - IMPLEMENT: Agent coordination for complex PRPs requiring multiple specialists
  - FUNCTIONALITY: Multi-agent PRP execution, result aggregation, status coordination
  - NAMING: prp_agent_coordinator.py in PRPs/scripts/
  - DEPENDENCIES: Tasks 2-5 (all agents enhanced)

Task 7: IMPLEMENT comprehensive testing for enhanced agents
  - IMPLEMENT: Test suite validating PRP execution across all enhanced agents
  - COVERAGE: TDD integration, validation loops, autonomous execution, status reporting
  - NAMING: test_prp_aware_agents.py with comprehensive agent validation
  - DEPENDENCIES: Task 6 (complete agent enhancement)

Task 8: CREATE documentation and usage guide for PRP-aware agents
  - IMPLEMENT: Comprehensive guide for using enhanced agents with PRPs
  - CONTENT: Agent selection, PRP customization, troubleshooting, best practices
  - DEPENDENCIES: Task 7 (testing and validation complete)
```

### Agent Enhancement Patterns

```python
# Standard PRP-Aware Agent Enhancement Template
"""
## PRP Execution Capabilities

When invoked with a PRP specification, this agent follows the structured TDD-PRP methodology:

### PRP Structure Understanding
- Parses Goal, Why, What, Context, Implementation Blueprint, and Validation Loop sections
- Extracts domain-specific requirements and constraints
- Identifies success criteria and measurable outcomes

### TDD Methodology Integration
- **Red Phase**: Creates failing tests based on PRP requirements
- **Green Phase**: Implements minimal code to make tests pass
- **Refactor Phase**: Improves code quality while maintaining test suite

### 4-Level Validation Loop
- **Level 0**: Test Creation - Write failing tests first (domain-specific)
- **Level 1**: Syntax & Style - {domain-specific linting and formatting}
- **Level 2**: Unit Tests - {domain-specific testing framework}
- **Level 3**: Integration Testing - {domain-specific integration approach}
- **Level 4**: Creative Validation - {domain-specific advanced validation}

### Autonomous Execution Pattern
When executing a PRP autonomously:
1. Parse PRP requirements and extract implementation tasks
2. Create comprehensive test suite (Red Phase)
3. Implement solution incrementally (Green Phase)
4. Refactor and optimize (Refactor Phase)
5. Execute complete validation loop
6. Report completion status for project management integration

### Context-Aware Implementation
- Analyzes existing codebase patterns and follows established conventions
- Leverages domain-specific libraries and frameworks appropriately
- Applies security and performance best practices for the domain
- Integrates with existing system architecture and constraints
"""

# Domain-Specific TDD Integration Examples

# Python Specialist Enhancement
"""
### TDD Integration for Python Development
- **Test Framework**: pytest with fixtures and parametrization
- **Red Phase**: Create failing pytest tests for all public functions
- **Green Phase**: Implement minimal Python code to pass tests
- **Refactor Phase**: Apply pythonic patterns, type hints, and optimization

### Validation Loop (Python-Specific)
- Level 0: pytest tests that fail initially
- Level 1: ruff check/format, mypy type checking
- Level 2: pytest execution with coverage reporting
- Level 3: Integration testing with requests, database connections
- Level 4: Performance testing, security scanning with bandit
"""

# React Specialist Enhancement  
"""
### TDD Integration for React Development
- **Test Framework**: Jest with React Testing Library
- **Red Phase**: Create failing component and integration tests
- **Green Phase**: Implement minimal React components to pass tests
- **Refactor Phase**: Optimize for performance, accessibility, and maintainability

### Validation Loop (React-Specific)
- Level 0: Jest/RTL tests that fail initially
- Level 1: ESLint, TypeScript checking, Prettier formatting
- Level 2: Jest test execution with coverage
- Level 3: Component integration and user interaction testing
- Level 4: Visual regression testing, performance profiling, accessibility audits
"""
```

## Validation Loop

### Level 0: Test Creation (TDD Red Phase)

```bash
# Create template for agent enhancement validation
cat > PRPs/scripts/tests/test_agent_enhancement.py << 'EOF'
def test_agent_prp_execution_capability():
    # Test that agents understand PRP structure
    agent_content = read_agent_file("python-specialist.md")
    assert "PRP Execution Capabilities" in agent_content
    assert "TDD Methodology Integration" in agent_content
    assert "4-Level Validation Loop" in agent_content

def test_domain_specific_tdd_integration():
    # Test that TDD is properly integrated for each domain
    python_agent = read_agent_file("python-specialist.md")
    assert "pytest" in python_agent
    
    react_agent = read_agent_file("react-specialist.md")
    assert "Jest" in react_agent or "React Testing Library" in react_agent
EOF

# Run failing tests to establish baseline
uv run pytest PRPs/scripts/tests/test_agent_enhancement.py -v
# Expected: Tests fail initially before agent enhancement
```

### Level 1: Syntax & Style (Implementation Phase)

```bash
# Validate agent file format during enhancement
for agent_file in .claude/agents/*.md; do
    echo "Validating $agent_file"
    # Check for required PRP sections
    grep -q "PRP Execution Capabilities" "$agent_file" || echo "WARNING: Missing PRP section in $agent_file"
    grep -q "TDD Methodology Integration" "$agent_file" || echo "WARNING: Missing TDD section in $agent_file"
    grep -q "4-Level Validation Loop" "$agent_file" || echo "WARNING: Missing validation section in $agent_file"
done

# Validate markdown formatting
markdownlint .claude/agents/*.md || echo "Install markdownlint if needed"

# Check for consistent enhancement patterns
python PRPs/scripts/validate_agent_enhancements.py --check-consistency

# Expected: All agents follow consistent enhancement patterns
```

### Level 2: Unit Tests (TDD Green Phase)

```bash
# Test agent enhancement functionality
uv run pytest PRPs/scripts/tests/test_prp_aware_agents.py -v

# Test TDD integration for each domain
uv run pytest PRPs/scripts/tests/test_tdd_integration.py -v

# Test validation loop implementation
uv run pytest PRPs/scripts/tests/test_validation_loops.py -v

# Test autonomous execution capabilities
uv run pytest PRPs/scripts/tests/test_autonomous_execution.py -v

# Coverage validation for agent enhancement system
uv run pytest PRPs/scripts/tests/ --cov=PRPs.scripts --cov-report=term-missing

# Expected: All tests pass, >90% coverage, agents properly enhanced
```

### Level 3: Integration Testing (System Validation)

```bash
# Test complete PRP execution with enhanced agents
echo "Testing enhanced agent PRP execution"

# Create test PRP for Python specialist
cat > test_python_prp.md << 'EOF'
## Goal
Create a simple user model class with validation

## Implementation Blueprint
Task 1: CREATE src/models/user.py
- IMPLEMENT: User class with email validation
- FOLLOW pattern: Pydantic models for validation
EOF

# Test Python specialist with PRP
echo "Testing python-specialist with PRP execution"
claude --agent python-specialist < test_python_prp.md

# Test React specialist with component PRP
cat > test_react_prp.md << 'EOF'
## Goal  
Create a LoginForm component with validation

## Implementation Blueprint
Task 1: CREATE src/components/LoginForm.tsx
- IMPLEMENT: Form with email/password validation
- FOLLOW pattern: React Hook Form with TypeScript
EOF

# Test React specialist with PRP
echo "Testing react-specialist with PRP execution"
claude --agent react-specialist < test_react_prp.md

# Validate that agents follow TDD methodology
echo "Validating TDD compliance across agents"
grep -r "Red Phase" .claude/agents/ || echo "ERROR: TDD Red Phase not documented"
grep -r "Green Phase" .claude/agents/ || echo "ERROR: TDD Green Phase not documented"
grep -r "Refactor Phase" .claude/agents/ || echo "ERROR: TDD Refactor Phase not documented"

# Expected: All agents execute PRPs with TDD methodology
```

### Level 4: Creative & Real-World Validation

```bash
# Test complex, multi-domain PRP execution
cat > complex_feature_prp.md << 'EOF'
## Goal
Build a complete user authentication system with:
- Python FastAPI backend with JWT authentication
- React frontend with login/register forms
- PostgreSQL database with user management
- Docker containerization for deployment

## Implementation Blueprint
This PRP requires coordination between multiple specialists:
- python-specialist: API endpoints and JWT handling
- react-specialist: Frontend components and state management
- postgresql-specialist: Database schema and queries
- docker-kubernetes-specialist: Containerization setup
EOF

# Test multi-agent coordination
echo "Testing multi-agent PRP coordination"
bash .claude/scripts/uv_runner.sh PRPs/scripts/prp_agent_coordinator.py \
  --prp complex_feature_prp.md --coordinate-agents

# Should identify and coordinate: python-specialist, react-specialist, postgresql-specialist, docker-kubernetes-specialist

# Test domain-specific validation capabilities
for domain in "python" "react" "postgresql" "docker"; do
    echo "Testing $domain specialist domain-specific validation"
    # Each agent should have Level 4 validation appropriate to their domain
    agent_file=".claude/agents/${domain}-specialist.md"
    if [ -f "$agent_file" ]; then
        grep -q "Level 4.*Creative" "$agent_file" || echo "WARNING: Missing creative validation for $domain"
    fi
done

# Performance testing for agent enhancement
time python PRPs/scripts/validate_all_agents.py --performance-test
# Should complete validation of all 24 agents in <30 seconds

# Test autonomous execution with real codebase
echo "Testing autonomous execution on real development tasks"
# This should work without human intervention
bash .claude/scripts/uv_runner.sh PRPs/scripts/orchestrator_main.py \
  --execute-next-todo --autonomous --validate-completion

# Expected: Complex PRPs handled with multi-agent coordination, performance acceptable, autonomous execution successful
```

## Final Validation Checklist

### Technical Validation

- [ ] All 24 existing agents enhanced with PRP capabilities
- [ ] TDD methodology properly integrated for each domain
- [ ] 4-level validation loops implemented with domain-specific tooling
- [ ] Agent enhancement follows consistent patterns across all specialists
- [ ] UV runner integration works for all domain-specific commands
- [ ] All tests pass with comprehensive coverage

### PRP Integration Validation

- [ ] Agents understand and parse PRP structure correctly
- [ ] Implementation blueprints executed with appropriate domain expertise
- [ ] Context sections utilized for codebase-aware implementation
- [ ] Validation loops customized for domain-specific requirements
- [ ] Success criteria properly interpreted and validated
- [ ] Error handling prevents workflow interruption

### TDD Methodology Validation

- [ ] Red-Green-Refactor cycles enforced across all domains
- [ ] Test creation precedes implementation in all cases
- [ ] Domain-specific testing frameworks properly integrated
- [ ] Test coverage requirements met for all implementations
- [ ] Refactoring maintains test suite integrity
- [ ] TDD discipline maintained throughout autonomous execution

### Autonomous Workflow Validation

- [ ] Agents execute PRPs without human intervention
- [ ] Status reporting integrates with project management system
- [ ] Multi-agent coordination works for complex PRPs
- [ ] Context-aware implementation follows existing patterns
- [ ] Error recovery mechanisms prevent workflow failures
- [ ] Performance meets requirements for autonomous development

---

## Anti-Patterns to Avoid

- ❌ Don't replace existing domain expertise - enhance it with PRP capabilities
- ❌ Don't use generic TDD approaches - customize for each domain's tools and practices
- ❌ Don't skip domain-specific validation - Level 4 must be meaningful for each specialty
- ❌ Don't ignore existing codebase patterns - context awareness is critical
- ❌ Don't create agents that can't work autonomously - human intervention breaks workflow
- ❌ Don't skip error handling - autonomous systems must be resilient
- ❌ Don't compromise on test-first discipline - TDD is non-negotiable for quality