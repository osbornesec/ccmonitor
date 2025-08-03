name: "PRP-004: Todo-to-PRP Orchestrator Agent Implementation"
description: |

---

## Goal

**Feature Goal**: Create an intelligent orchestrator agent that reads ACTIVE_TODOS.md, analyzes the next priority todo item, and automatically generates appropriate PRPs with full context for seamless autonomous development workflows.

**Deliverable**: A `todo-to-prp-orchestrator` agent that can parse todo items, analyze their requirements, select appropriate PRP templates, inject relevant context, and create executable PRPs that integrate with our TDD-PRP methodology.

**Success Definition**: Agent can autonomously convert todo items into comprehensive, context-rich PRPs that enable immediate implementation by specialized agents, creating a self-perpetuating development cycle.

## User Persona

**Target User**: Autonomous Development System and AI Agents
**Use Case**: Converting project management todos into executable implementation specifications
**User Journey**:
1. Agent reads ACTIVE_TODOS.md and identifies next priority item
2. Agent analyzes todo requirements and technical context
3. Agent selects appropriate PRP template and specialist agents
4. Agent generates comprehensive PRP with context injection
5. Agent creates PRP file and updates todo with PRP reference
6. Development system executes PRP automatically

**Pain Points Addressed**:
- Manual conversion of todos into detailed implementation specifications
- Inconsistent context and requirements in ad-hoc development tasks
- Break in autonomous workflow between planning and implementation
- Lack of systematic approach to todo-driven development

## Why

- Enable seamless transition from project planning to implementation
- Automate the creation of comprehensive, context-rich PRPs from simple todos
- Create closed-loop autonomous development where todos self-execute
- Eliminate manual overhead in translating requirements to actionable PRPs
- Establish foundation for fully autonomous development environments

## What

An intelligent orchestration agent that bridges project management and implementation:

- ACTIVE_TODOS.md parsing and priority analysis
- Requirements extraction and context analysis from todo items
- Automatic PRP template selection based on todo characteristics
- Context injection with relevant documentation, code patterns, and examples
- PRP generation with full TDD methodology and validation loops
- Integration with existing 24 specialized agents for domain expertise

### Success Criteria

- [ ] Agent can parse ACTIVE_TODOS.md and extract actionable todo items
- [ ] Requirements analysis identifies technical domain and complexity
- [ ] Template selection matches todo characteristics to appropriate PRP formats
- [ ] Context injection includes relevant documentation and code examples
- [ ] Generated PRPs integrate with TDD methodology and validation loops
- [ ] Agent selection recommends appropriate specialist agents for implementation
- [ ] Self-updating workflow maintains ACTIVE_TODOS.md with PRP references

## All Needed Context

### Context Completeness Check

_This PRP provides everything needed to create a sophisticated orchestrator that converts todos into comprehensive, executable PRPs with full context awareness and specialist agent integration._

### Documentation & References

```yaml
# MUST READ - Include these in your context window
- file: ACTIVE_TODOS.md
  why: Complete understanding of todo format, priorities, and metadata structure
  critical: Priority levels, dependency tracking, PRP reference format, status management
  pattern: High/Medium/Low priority classification with dependency relationships

- file: PRPs/001-tdd-prp-infrastructure.md
  why: Understanding of PRP template structure and TDD methodology integration
  critical: 4-level validation approach, test-first requirements, template organization
  pattern: Template selection criteria and validation loop requirements

- file: PRPs/templates/
  why: Available PRP templates for automatic selection based on todo characteristics
  critical: Template capabilities, use cases, required context patterns
  pattern: prp_tdd_base.md, prp_red_green_refactor.md, prp_bdd_specification.md usage

- file: .claude/agents/
  why: Complete catalog of 24 specialized agents for automatic agent selection
  critical: Agent capabilities, domain expertise, invocation patterns
  pattern: Domain mapping from todo content to appropriate specialist agents

- file: /home/michael/dev/PRPs-agentic-eng/PRPs/example-from-workshop-mcp-crawl4ai-refactor-1.md
  why: Real-world example of comprehensive PRP with context injection
  pattern: Context completeness, implementation blueprint, validation approach
  critical: How to transform requirements into actionable implementation tasks

- file: .claude/memory.jsonl
  why: Understanding recent development context for PRP context injection
  critical: Recent file modifications, implementation patterns, discovered requirements
  pattern: Context extraction from development history for PRP enhancement
```

### Current System Architecture

```bash
claude-agents/
├── .claude/
│   ├── agents/               # 24 specialized agents + project-manager-prp
│   │   ├── todo-to-prp-orchestrator.md  # NEW - To be created
│   │   ├── project-manager-prp.md       # From PRP-002
│   │   └── ... (24 specialists)
│   └── hooks/               # Including todo reminder from PRP-003
├── PRPs/
│   ├── templates/           # TDD-enhanced templates from PRP-001
│   │   ├── prp_tdd_base.md
│   │   ├── prp_red_green_refactor.md
│   │   └── prp_bdd_specification.md
│   ├── scripts/            # Project management tools from PRP-002
│   │   ├── project_analyzer.py
│   │   └── dependency_resolver.py
│   └── active/             # Generated PRPs (to be created)
├── ACTIVE_TODOS.md         # Current todo list with priorities
└── COMPLETED_TODOS.md      # Historical tracking
```

### Desired Orchestrator Integration

```bash
claude-agents/
├── .claude/
│   ├── agents/
│   │   ├── todo-to-prp-orchestrator.md  # NEW - Intelligent orchestrator
├── PRPs/
│   ├── scripts/
│   │   ├── todo_parser.py              # NEW - ACTIVE_TODOS.md parsing
│   │   ├── context_injector.py         # NEW - Context analysis and injection
│   │   ├── template_selector.py        # NEW - Template selection logic
│   │   ├── prp_generator.py           # NEW - PRP creation and file management
│   │   └── orchestrator_main.py       # NEW - Main orchestration workflow
│   ├── active/                        # Generated PRPs ready for execution
│   │   ├── feature-auth-models.md     # Auto-generated from todo
│   │   └── api-login-endpoints.md     # Auto-generated from todo
│   └── context_cache/                 # Cached context for reuse
│       ├── codebase_patterns.json     # Common patterns and examples
│       └── documentation_index.json   # Relevant docs and references
```

### Known Integration Patterns & Constraints

```python
# CRITICAL: Todo parsing must handle existing ACTIVE_TODOS.md format exactly
# Pattern: Priority sections, dependency tracking, PRP references, status metadata

# CRITICAL: PRP generation must integrate with TDD methodology from PRP-001
# Pattern: Test-first validation, 4-level validation loops, comprehensive context

# CRITICAL: Agent selection must utilize existing 24 specialized agents
# Pattern: Domain analysis → Agent mapping → PRP customization for specialist

# CRITICAL: Context injection must be comprehensive for one-pass success
# Pattern: Code examples, gotchas, library documentation, architectural patterns

# CRITICAL: All orchestrator scripts must use UV runner
# Pattern: bash .claude/scripts/uv_runner.sh script.py for environment consistency

# CRITICAL: Generated PRPs must be immediately executable by agents
# Pattern: Complete context, clear success criteria, comprehensive validation loops
```

## Implementation Blueprint

### Implementation Tasks (ordered by dependencies)

```yaml
Task 1: CREATE .claude/agents/todo-to-prp-orchestrator.md
  - IMPLEMENT: Agent configuration with orchestration capabilities
  - FOLLOW pattern: Existing agent structure in .claude/agents/
  - CAPABILITIES: Todo analysis, template selection, context injection, PRP generation
  - NAMING: todo-to-prp-orchestrator.md following existing convention
  - PLACEMENT: .claude/agents/ directory
  - DEPENDENCIES: Understanding of existing agent patterns and todo format

Task 2: CREATE PRPs/scripts/todo_parser.py
  - IMPLEMENT: ACTIVE_TODOS.md parsing with priority and dependency analysis
  - FOLLOW pattern: Structured parsing with comprehensive metadata extraction
  - FUNCTIONALITY: Extract todos, priorities, dependencies, status, PRP references
  - NAMING: parse_active_todos() main function with Todo data classes
  - DEPENDENCIES: Task 1 (agent definition)
  - PLACEMENT: PRPs/scripts/ directory

Task 3: CREATE PRPs/scripts/context_injector.py
  - IMPLEMENT: Intelligent context analysis and injection for PRP enhancement
  - FOLLOW pattern: Multi-source context gathering and relevance scoring
  - FUNCTIONALITY: Code pattern analysis, documentation extraction, example generation
  - NAMING: inject_context_for_todo() with comprehensive context analysis
  - DEPENDENCIES: Task 2 (todo parsing established)
  - PLACEMENT: PRPs/scripts/ directory

Task 4: CREATE PRPs/scripts/template_selector.py
  - IMPLEMENT: Intelligent PRP template selection based on todo characteristics
  - FOLLOW pattern: Multi-criteria analysis for optimal template matching
  - FUNCTIONALITY: Todo analysis, template capability matching, customization
  - NAMING: select_optimal_template() with template scoring and selection
  - DEPENDENCIES: Task 3 (context analysis available)
  - PLACEMENT: PRPs/scripts/ directory

Task 5: CREATE PRPs/scripts/prp_generator.py
  - IMPLEMENT: PRP file generation with template population and context injection
  - FOLLOW pattern: Template processing with comprehensive context substitution
  - FUNCTIONALITY: Template instantiation, context injection, file creation
  - NAMING: generate_prp_from_todo() with complete PRP creation workflow
  - DEPENDENCIES: Tasks 2-4 (all analysis components complete)
  - PLACEMENT: PRPs/scripts/ directory

Task 6: CREATE PRPs/scripts/orchestrator_main.py
  - IMPLEMENT: Main orchestration workflow coordinating all components
  - FOLLOW pattern: Pipeline processing with error handling and status updates
  - FUNCTIONALITY: Todo selection, PRP generation, status updates, workflow management
  - NAMING: orchestrate_todo_to_prp() main workflow function
  - DEPENDENCIES: Tasks 2-5 (all components implemented)
  - PLACEMENT: PRPs/scripts/ directory

Task 7: CREATE PRPs/context_cache/ directory and caching system
  - IMPLEMENT: Context caching for performance and consistency
  - FOLLOW pattern: JSON-based caching with invalidation and updates
  - FUNCTIONALITY: Codebase pattern caching, documentation indexing, example storage
  - NAMING: ContextCache class with intelligent cache management
  - DEPENDENCIES: Task 3 (context injection patterns established)
  - PLACEMENT: PRPs/context_cache/ directory

Task 8: CREATE comprehensive test suite for orchestrator functionality
  - IMPLEMENT: End-to-end testing for complete todo-to-PRP workflow
  - FOLLOW pattern: Integration testing with mock todos and validation
  - COVERAGE: Parsing, context injection, template selection, PRP generation
  - NAMING: test_orchestrator_*.py with comprehensive scenario coverage
  - DEPENDENCIES: Tasks 1-6 (complete orchestrator implementation)
  - PLACEMENT: PRPs/scripts/tests/ directory
```

### Implementation Patterns & Key Details

```python
# Todo Parsing Pattern
@dataclass
class TodoItem:
    """
    PATTERN: Structured todo representation
    - Complete metadata extraction from ACTIVE_TODOS.md
    - Priority classification and dependency tracking
    - Status management and progress monitoring
    """
    id: str
    title: str
    description: str
    priority: str  # High/Medium/Low
    status: str    # Not Started/In Progress/Completed
    dependencies: List[str]
    estimated_effort: str
    prp_reference: Optional[str]
    domain_areas: List[str]  # Extracted from content analysis
    
def parse_active_todos(todos_path: Path) -> List[TodoItem]:
    """
    PATTERN: Comprehensive todo parsing
    - Extract all metadata from markdown structure
    - Identify domain areas for agent selection
    - Validate dependency relationships
    - Prioritize todos for execution order
    """

# Context Injection Pattern
class ContextInjector:
    """
    PATTERN: Multi-source context gathering
    - Analyze codebase for relevant patterns and examples
    - Extract documentation and API references
    - Include gotchas and known limitations
    - Score context relevance for inclusion
    """
    
    def inject_context_for_todo(self, todo: TodoItem) -> ContextPackage:
        context = ContextPackage()
        
        # Code pattern analysis
        if 'python' in todo.domain_areas:
            context.code_examples.extend(self.find_python_patterns())
        
        # Documentation extraction
        context.documentation.extend(
            self.find_relevant_docs(todo.domain_areas)
        )
        
        # Gotcha identification
        context.gotchas.extend(
            self.identify_common_pitfalls(todo.domain_areas)
        )
        
        return context

# Template Selection Pattern
def select_optimal_template(todo: TodoItem, context: ContextPackage) -> str:
    """
    PATTERN: Multi-criteria template selection
    - Analyze todo complexity and requirements
    - Match to template capabilities and structure
    - Consider domain-specific requirements
    - Score templates for optimal fit
    """
    templates = {
        'prp_tdd_base.md': {
            'complexity': 'high',
            'domains': ['backend', 'database', 'api'],
            'validation_levels': 4
        },
        'prp_red_green_refactor.md': {
            'complexity': 'medium', 
            'domains': ['refactoring', 'optimization'],
            'validation_levels': 3
        },
        'prp_bdd_specification.md': {
            'complexity': 'medium',
            'domains': ['frontend', 'user-facing'],
            'validation_levels': 4
        }
    }
    
    # Score templates based on todo characteristics
    scores = {}
    for template, capabilities in templates.items():
        score = calculate_template_fit(todo, capabilities)
        scores[template] = score
    
    return max(scores, key=scores.get)

# PRP Generation Pattern
def generate_prp_from_todo(todo: TodoItem, 
                          template_path: str, 
                          context: ContextPackage) -> Path:
    """
    PATTERN: Template instantiation with context injection
    - Load template and parse structure
    - Substitute placeholders with todo-specific content
    - Inject comprehensive context and examples
    - Validate generated PRP completeness
    """
    
    # Load template
    template = load_template(template_path)
    
    # Substitute core content
    prp_content = template.substitute(
        goal=generate_goal_section(todo),
        why=generate_why_section(todo, context),
        what=generate_what_section(todo),
        context=generate_context_section(context),
        implementation=generate_implementation_blueprint(todo, context),
        validation=generate_validation_loops(todo, context)
    )
    
    # Write PRP file
    prp_path = Path(f"PRPs/active/{todo.id}-{slugify(todo.title)}.md")
    prp_path.write_text(prp_content)
    
    return prp_path
```

### Agent Integration and Selection

```yaml
DOMAIN_MAPPING:
  - python: python-specialist
  - react: react-specialist  
  - api: api-design-specialist
  - database: postgresql-specialist, mongodb-specialist
  - testing: cypress-testing-specialist
  - infrastructure: docker-kubernetes-specialist, aws-specialist
  - frontend: react-specialist, vuejs-specialist
  - mobile: flutter-specialist

AGENT_SELECTION_LOGIC:
  - analyze todo content for domain keywords
  - map to appropriate specialist agents
  - include agent recommendations in generated PRP
  - configure PRP for optimal agent execution

MULTI_AGENT_COORDINATION:
  - identify todos requiring multiple specialists
  - create coordination sections in PRP
  - specify agent interaction patterns
  - manage cross-agent dependencies
```

## Validation Loop

### Level 0: Test Creation (TDD Red Phase)

```bash
# Create failing tests for orchestrator functionality
cat > PRPs/scripts/tests/test_orchestrator.py << 'EOF'
def test_todo_parsing_extracts_metadata():
    # This should fail until todo parsing is implemented
    todos = parse_active_todos(Path("test_todos.md"))
    assert len(todos) > 0
    assert todos[0].priority in ['High', 'Medium', 'Low']
    assert todos[0].domain_areas is not None

def test_context_injection_includes_examples():
    # This should fail until context injection is implemented
    todo = TodoItem(title="Create user model", domain_areas=["python", "database"])
    context = inject_context_for_todo(todo)
    assert len(context.code_examples) > 0
    assert len(context.documentation) > 0
EOF

# Run failing tests to establish TDD baseline
uv run pytest PRPs/scripts/tests/test_orchestrator.py -v
# Expected: Tests fail initially (Red phase)
```

### Level 1: Syntax & Style (Implementation Phase)

```bash
# Run after each component creation
ruff check PRPs/scripts/todo_parser.py --fix
ruff check PRPs/scripts/context_injector.py --fix
ruff check PRPs/scripts/template_selector.py --fix
ruff check PRPs/scripts/prp_generator.py --fix
ruff check PRPs/scripts/orchestrator_main.py --fix
mypy PRPs/scripts/*.py

# Validate agent configuration format
python -c "
import yaml
content = open('.claude/agents/todo-to-prp-orchestrator.md').read()
# Basic structure validation for agent file
assert 'name: todo-to-prp-orchestrator' in content
"

# Project-wide validation
ruff check PRPs/ --fix
mypy PRPs/scripts/

# Expected: Zero errors, consistent formatting, proper type hints
```

### Level 2: Unit Tests (TDD Green Phase)

```bash
# Test todo parsing functionality
uv run pytest PRPs/scripts/tests/test_todo_parser.py -v

# Test context injection and analysis
uv run pytest PRPs/scripts/tests/test_context_injector.py -v

# Test template selection logic
uv run pytest PRPs/scripts/tests/test_template_selector.py -v

# Test PRP generation and file creation
uv run pytest PRPs/scripts/tests/test_prp_generator.py -v

# Test complete orchestrator workflow
uv run pytest PRPs/scripts/tests/test_orchestrator.py -v

# Coverage validation
uv run pytest PRPs/scripts/tests/ --cov=PRPs.scripts --cov-report=term-missing

# Expected: All tests pass, >90% code coverage
```

### Level 3: Integration Testing (System Validation)

```bash
# Test complete todo-to-PRP workflow
echo "Testing end-to-end orchestrator workflow"
bash .claude/scripts/uv_runner.sh PRPs/scripts/orchestrator_main.py \
  --todos-file ACTIVE_TODOS.md --select-next --generate-prp

# Validate generated PRP file quality
if [ -f "PRPs/active/"*.md ]; then
  bash .claude/scripts/uv_runner.sh PRPs/scripts/prp_validator.py \
    --prp PRPs/active/*.md --validate-completeness
else
  echo "ERROR: No PRP files generated"
fi

# Test ACTIVE_TODOS.md update with PRP references
grep -q "PRP:" ACTIVE_TODOS.md || echo "ERROR: PRP references not updated"

# Test agent selection recommendations
generated_prp=$(ls PRPs/active/*.md | head -1)
grep -q "specialist" "$generated_prp" || echo "ERROR: Agent recommendations missing"

# Test context injection quality
grep -q "## All Needed Context" "$generated_prp" || echo "ERROR: Context section missing"
grep -q "file:" "$generated_prp" || echo "ERROR: Context references missing"

# Expected: Complete workflow generates valid PRPs with comprehensive context
```

### Level 4: Creative & Real-World Validation

```bash
# Test with complex, multi-domain todo
cat > complex_todo_test.md << 'EOF'
## High Priority
- [ ] **Build Real-time Chat System** (Est: 8-10 hours)
  - [ ] WebSocket backend with authentication
  - [ ] React frontend with real-time message display
  - [ ] PostgreSQL message persistence
  - [ ] Redis for session management
  - Status: Not Started
  - Domains: python, react, postgresql, redis, websockets
EOF

# Test orchestrator with complex requirements
bash .claude/scripts/uv_runner.sh PRPs/scripts/orchestrator_main.py \
  --todos-file complex_todo_test.md --generate-prp --detailed-analysis

# Should generate comprehensive PRP with multi-agent coordination
generated_prp=$(ls PRPs/active/*chat-system*.md)
echo "Validating complex PRP generation:"

# Validate multi-domain context injection
grep -q "python-specialist" "$generated_prp" || echo "ERROR: Python specialist not recommended"
grep -q "react-specialist" "$generated_prp" || echo "ERROR: React specialist not recommended"
grep -q "postgresql-specialist" "$generated_prp" || echo "ERROR: Database specialist not recommended"

# Test context cache performance
time bash .claude/scripts/uv_runner.sh PRPs/scripts/context_injector.py \
  --domain python --use-cache
# Should complete in <2 seconds with caching

# Test template selection accuracy
bash .claude/scripts/uv_runner.sh PRPs/scripts/template_selector.py \
  --todo-complexity high --domains "python,react,database" --recommend

# Should recommend prp_tdd_base.md for high complexity multi-domain project

# Test orchestrator with realistic development workflow
for priority in "High" "Medium" "Low"; do
  echo "Testing $priority priority todo processing"
  bash .claude/scripts/uv_runner.sh PRPs/scripts/orchestrator_main.py \
    --priority "$priority" --limit 1 --generate-prp
done

# Expected: Complex todos handled correctly, appropriate templates selected, comprehensive context injected
```

## Final Validation Checklist

### Technical Validation

- [ ] All 4 validation levels completed successfully
- [ ] Todo parsing handles ACTIVE_TODOS.md format completely
- [ ] Context injection provides comprehensive, relevant information
- [ ] Template selection matches todo characteristics accurately
- [ ] PRP generation creates immediately executable specifications
- [ ] Agent selection recommends appropriate specialists
- [ ] All scripts execute via UV runner with proper environment

### Orchestrator Validation

- [ ] Autonomous todo-to-PRP conversion without human intervention
- [ ] Generated PRPs include complete context for one-pass success
- [ ] Multi-domain todos handled with appropriate agent coordination
- [ ] Context caching improves performance and consistency
- [ ] Template selection optimizes for todo complexity and domain
- [ ] Status updates maintain ACTIVE_TODOS.md accuracy

### Integration Validation

- [ ] Agent integrates with existing 24 specialists seamlessly
- [ ] TDD methodology enforced in generated PRPs
- [ ] Validation loops appropriate for todo complexity
- [ ] Context injection leverages existing codebase patterns
- [ ] Generated PRPs immediately executable by specialist agents
- [ ] Workflow enables continuous autonomous development

### Autonomous Workflow Validation

- [ ] System can process entire ACTIVE_TODOS.md autonomously
- [ ] Generated PRPs enable immediate implementation start
- [ ] Context quality supports production-ready code generation
- [ ] Agent recommendations optimize implementation efficiency
- [ ] Self-updating workflow maintains project management accuracy
- [ ] Error handling prevents workflow interruption

---

## Anti-Patterns to Avoid

- ❌ Don't generate PRPs without comprehensive context - causes implementation failures
- ❌ Don't skip domain analysis - incorrect agent selection reduces effectiveness
- ❌ Don't use generic templates - todo-specific template selection is critical
- ❌ Don't ignore todo dependencies - execution order affects success rates
- ❌ Don't create PRPs that aren't immediately executable - breaks autonomous flow
- ❌ Don't skip validation loop customization - validation must match complexity
- ❌ Don't generate incomplete context - one-pass success requires everything upfront