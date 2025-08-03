"""
PRP file generation with template population and context injection
Template instantiation with comprehensive context substitution and file creation
"""
import re
from pathlib import Path
from typing import Dict, Any, Optional
from string import Template
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PRPGenerator:
    """PRP file generation engine with template processing"""
    
    def __init__(self, templates_dir: Optional[Path] = None, output_dir: Optional[Path] = None):
        """
        Initialize PRP generator
        
        Args:
            templates_dir: Path to PRP templates directory
            output_dir: Path for generated PRP files
        """
        self.templates_dir = templates_dir or Path(__file__).parent.parent / "templates"
        self.output_dir = output_dir or Path(__file__).parent.parent / "active"
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_prp_from_todo(self, todo, template_name: str, context) -> Path:
        """
        Generate PRP file from todo using specified template and context
        
        Args:
            todo: TodoItem with requirements
            template_name: Template filename to use
            context: ContextPackage with injected context
            
        Returns:
            Path to generated PRP file
        """
        logger.info(f"Generating PRP for {todo.id} using {template_name}")
        
        # Load template
        template_path = self.templates_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        template_content = template_path.read_text(encoding='utf-8')
        
        # Generate PRP content
        prp_content = self._populate_template(template_content, todo, context)
        
        # Create output filename
        output_filename = self._generate_filename(todo)
        output_path = self.output_dir / output_filename
        
        # Write PRP file
        output_path.write_text(prp_content, encoding='utf-8')
        logger.info(f"Generated PRP: {output_path}")
        
        return output_path
    
    def _populate_template(self, template_content: str, todo, context) -> str:
        """Populate template with todo and context data"""
        
        # Generate content sections
        substitutions = {
            'name': f'"{todo.id}: {todo.title}"',
            'goal': self._generate_goal_section(todo),
            'why': self._generate_why_section(todo, context),
            'what': self._generate_what_section(todo),
            'context': self._generate_context_section(context),
            'implementation': self._generate_implementation_blueprint(todo, context),
            'validation': self._generate_validation_loops(todo, context),
            'user_persona': self._generate_user_persona(todo),
            'success_criteria': self._generate_success_criteria(todo),
            'all_needed_context': self._generate_all_needed_context_section(context),
            'anti_patterns': self._generate_anti_patterns(todo),
            'agent_recommendations': self._generate_agent_recommendations(todo),
            'timestamp': datetime.now().isoformat(),
            'todo_id': todo.id,
            'todo_title': todo.title,
            'todo_description': todo.description,
            'domains': ', '.join(todo.domain_areas),
            'estimated_effort': todo.estimated_effort,
            'priority': todo.priority
        }
        
        # Use safe substitute to handle missing placeholders gracefully
        template = Template(template_content)
        try:
            populated_content = template.substitute(substitutions)
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}")
            populated_content = template.safe_substitute(substitutions)
        
        return populated_content
    
    def _generate_goal_section(self, todo) -> str:
        """Generate the Goal section"""
        return f"""**Feature Goal**: {todo.title}

**Deliverable**: {todo.description}

**Success Definition**: Successfully implement {todo.title} meeting all requirements with comprehensive testing and validation."""
    
    def _generate_why_section(self, todo, context) -> str:
        """Generate the Why section"""
        priority_reasons = {
            'High': 'Critical for system functionality and user experience',
            'Medium': 'Important for feature completeness and system efficiency',
            'Low': 'Beneficial for system improvement and future maintainability'
        }
        
        why_content = f"""- {priority_reasons.get(todo.priority, 'Important for system improvement')}
- Addresses core requirements: {todo.description}
- Enables future development and scalability"""
        
        if todo.dependencies:
            why_content += f"\n- Builds upon completed dependencies: {', '.join(todo.dependencies)}"
        
        if context.integration_points:
            why_content += f"\n- Integrates with: {', '.join(context.integration_points[:3])}"
        
        return why_content
    
    def _generate_what_section(self, todo) -> str:
        """Generate the What section"""
        what_content = f"""Implementation of {todo.title}:

"""
        
        if todo.subtasks:
            what_content += "**Core Components:**\n"
            for i, subtask in enumerate(todo.subtasks, 1):
                what_content += f"- {subtask}\n"
            what_content += "\n"
        
        what_content += f"""**Technical Requirements:**
- Domain areas: {', '.join(todo.domain_areas)}
- Estimated effort: {todo.estimated_effort}
- Priority level: {todo.priority}"""
        
        return what_content
    
    def _generate_context_section(self, context) -> str:
        """Generate comprehensive context section"""
        context_content = "## All Needed Context\n\n"
        
        if context.code_examples:
            context_content += "### Code Examples\n"
            for i, example in enumerate(context.code_examples[:3], 1):
                context_content += f"**Example {i}:**\n```\n{example[:500]}...\n```\n\n"
        
        if context.documentation:
            context_content += "### Documentation References\n"
            for doc in context.documentation[:3]:
                context_content += f"- {doc[:200]}...\n"
            context_content += "\n"
        
        if context.gotchas:
            context_content += "### Common Gotchas\n"
            for gotcha in context.gotchas[:3]:
                context_content += f"- ⚠️ {gotcha}\n"
            context_content += "\n"
        
        if context.best_practices:
            context_content += "### Best Practices\n"
            for practice in context.best_practices[:3]:
                context_content += f"- ✅ {practice}\n"
            context_content += "\n"
        
        if context.library_references:
            context_content += "### Library References\n"
            for lib in context.library_references[:5]:
                context_content += f"- {lib}\n"
            context_content += "\n"
        
        return context_content
    
    def _generate_implementation_blueprint(self, todo, context) -> str:
        """Generate implementation blueprint with tasks"""
        blueprint = "## Implementation Blueprint\n\n"
        
        if todo.subtasks:
            blueprint += "### Implementation Tasks (ordered by dependencies)\n\n"
            for i, subtask in enumerate(todo.subtasks, 1):
                task_id = f"Task {i}"
                blueprint += f"""```yaml
{task_id}: {subtask}
  - IMPLEMENT: {subtask}
  - FOLLOW pattern: Existing patterns in codebase
  - DEPENDENCIES: {"Previous tasks" if i > 1 else "None"}
  - PLACEMENT: Appropriate location in project structure
```

"""
        
        blueprint += "### Implementation Patterns & Key Details\n\n"
        
        if context.architectural_patterns:
            blueprint += "**Architectural Patterns:**\n"
            for pattern in context.architectural_patterns:
                blueprint += f"- {pattern}\n"
            blueprint += "\n"
        
        blueprint += f"""**Domain-Specific Implementation:**
- Primary domains: {', '.join(todo.domain_areas)}
- Integration requirements: {len(context.integration_points)} integration points
- Context complexity: {'High' if len(context.code_examples) > 3 else 'Medium' if len(context.code_examples) > 1 else 'Low'}
"""
        
        return blueprint
    
    def _generate_validation_loops(self, todo, context) -> str:
        """Generate 4-level validation loops"""
        validation = """## Validation Loop

### Level 0: Test Creation (TDD Red Phase)

```bash
# Create failing tests for the implementation
"""
        
        if 'python' in todo.domain_areas:
            validation += """pytest tests/test_feature.py -v
# Expected: Tests fail initially (Red phase)
"""
        elif 'javascript' in todo.domain_areas:
            validation += """npm test
# Expected: Tests fail initially (Red phase)  
"""
        else:
            validation += """# Run appropriate test command for the technology stack
# Expected: Tests fail initially (Red phase)
"""
        
        validation += """```

### Level 1: Syntax & Style (Implementation Phase)

```bash
# Run after implementation"""
        
        if 'python' in todo.domain_areas:
            validation += """
ruff check src/ --fix
mypy src/
"""
        elif 'javascript' in todo.domain_areas:
            validation += """
npm run lint
npm run type-check
"""
        
        validation += """# Expected: Zero errors, consistent formatting
```

### Level 2: Unit Tests (TDD Green Phase)

```bash
# Test implementation functionality"""
        
        if 'python' in todo.domain_areas:
            validation += """
pytest tests/ -v --cov=src
"""
        elif 'javascript' in todo.domain_areas:
            validation += """
npm test -- --coverage
"""
        
        validation += """# Expected: All tests pass, >90% code coverage
```

### Level 3: Integration Testing (System Validation)

```bash
# Test complete functionality and integration points"""
        
        if context.integration_points:
            validation += f"""
# Test integration with: {', '.join(context.integration_points[:3])}
"""
        
        validation += """# Run integration test suite
# Expected: All integrations work correctly
```"""
        
        return validation
    
    def _generate_user_persona(self, todo) -> str:
        """Generate user persona section"""
        persona_map = {
            'api': 'Backend Developer integrating with the API',
            'frontend': 'Frontend Developer building user interfaces', 
            'database': 'Data Administrator managing data systems',
            'security': 'Security Engineer implementing authentication',
            'testing': 'QA Engineer ensuring quality',
            'infrastructure': 'DevOps Engineer managing deployments'
        }
        
        primary_domain = todo.domain_areas[0] if todo.domain_areas else 'general'
        target_user = persona_map.get(primary_domain, 'Developer implementing the feature')
        
        return f"""**Target User**: {target_user}
**Use Case**: {todo.description}
**User Journey**: User needs to {todo.title.lower()} efficiently and reliably"""
    
    def _generate_success_criteria(self, todo) -> str:
        """Generate success criteria checklist"""
        criteria = [
            f"✅ {todo.title} implemented completely",
            "✅ All tests pass with >90% coverage",
            "✅ Code follows project style guidelines",
            "✅ Integration points work correctly"
        ]
        
        if todo.subtasks:
            for subtask in todo.subtasks[:3]:
                criteria.append(f"✅ {subtask}")
        
        return "\n".join(criteria)
    
    def _generate_all_needed_context_section(self, context) -> str:
        """Generate the All Needed Context section with file references"""
        context_section = """### Context Completeness Check

_This PRP provides comprehensive context for successful implementation._

### Documentation & References

```yaml
# MUST READ - Include these in your context window"""
        
        if context.code_examples:
            context_section += f"""
- patterns: Existing code patterns and examples
  critical: Implementation patterns, best practices, common approaches
  count: {len(context.code_examples)} examples available"""
        
        if context.documentation:
            context_section += f"""
- documentation: Project documentation and guides  
  critical: API references, architecture decisions, usage patterns
  count: {len(context.documentation)} documents available"""
        
        if context.gotchas:
            context_section += f"""
- gotchas: Common pitfalls and known issues
  critical: Error prevention, debugging guidance, limitations
  count: {len(context.gotchas)} gotchas identified"""
        
        context_section += """
```"""
        
        return context_section
    
    def _generate_anti_patterns(self, todo) -> str:
        """Generate anti-patterns section"""
        general_anti_patterns = [
            "❌ Don't skip testing - comprehensive tests prevent regressions",
            "❌ Don't ignore error handling - robust error handling is critical",
            "❌ Don't hardcode values - use configuration and environment variables",
            "❌ Don't skip documentation - document public interfaces and complex logic"
        ]
        
        domain_anti_patterns = {
            'security': ["❌ Don't store secrets in code - use secure secret management"],
            'database': ["❌ Don't use raw SQL without validation - prevent injection attacks"],
            'api': ["❌ Don't ignore rate limiting - protect against abuse"],
            'frontend': ["❌ Don't ignore accessibility - ensure inclusive user experience"]
        }
        
        anti_patterns = general_anti_patterns.copy()
        for domain in todo.domain_areas:
            if domain in domain_anti_patterns:
                anti_patterns.extend(domain_anti_patterns[domain])
        
        return "\n".join(anti_patterns[:6])  # Limit to 6 anti-patterns
    
    def _generate_agent_recommendations(self, todo) -> str:
        """Generate recommended specialist agents"""
        agent_mapping = {
            'python': 'python-specialist',
            'javascript': 'javascript-typescript-specialist', 
            'react': 'react-specialist',
            'vue': 'vuejs-specialist',
            'api': 'api-design-specialist',
            'database': 'postgresql-specialist',
            'security': 'security-analyst',
            'testing': 'test-writer',
            'frontend': 'react-specialist',
            'performance': 'performance-optimizer',
            'infrastructure': 'docker-kubernetes-specialist'
        }
        
        recommended_agents = []
        for domain in todo.domain_areas:
            if domain in agent_mapping:
                agent = agent_mapping[domain]
                if agent not in recommended_agents:
                    recommended_agents.append(agent)
        
        if not recommended_agents:
            recommended_agents = ['general-purpose']
        
        agent_text = "**Recommended Specialist Agents:**\n"
        for agent in recommended_agents[:3]:  # Limit to 3 agents
            agent_text += f"- {agent}: Primary implementation agent for {agent.replace('-', ' ')}\n"
        
        return agent_text
    
    def _generate_filename(self, todo) -> str:
        """Generate appropriate filename for the PRP"""
        # Clean title for filename
        clean_title = re.sub(r'[^\w\s-]', '', todo.title.lower())
        clean_title = re.sub(r'[-\s]+', '-', clean_title)
        
        return f"{todo.id.lower()}-{clean_title}.md"
    
    def validate_generated_prp(self, prp_path: Path) -> Dict[str, Any]:
        """Validate that generated PRP is complete and well-formed"""
        if not prp_path.exists():
            return {'valid': False, 'error': 'PRP file does not exist'}
        
        content = prp_path.read_text(encoding='utf-8')
        
        required_sections = [
            'Goal', 'Why', 'What', 'Implementation Blueprint', 
            'Validation Loop', 'All Needed Context'
        ]
        
        validation_results = {'valid': True, 'missing_sections': [], 'stats': {}}
        
        for section in required_sections:
            if section not in content:
                validation_results['missing_sections'].append(section)
        
        validation_results['valid'] = len(validation_results['missing_sections']) == 0
        validation_results['stats'] = {
            'word_count': len(content.split()),
            'line_count': len(content.split('\n')),
            'size_bytes': len(content.encode('utf-8'))
        }
        
        return validation_results


# Module-level convenience function
def generate_prp_from_todo(todo, template_name: str, context, 
                          templates_dir: Optional[Path] = None,
                          output_dir: Optional[Path] = None) -> Path:
    """
    Convenience function for PRP generation
    
    Args:
        todo: TodoItem to generate PRP for
        template_name: Template to use
        context: ContextPackage with context
        templates_dir: Optional templates directory
        output_dir: Optional output directory
        
    Returns:
        Path to generated PRP file
    """
    generator = PRPGenerator(templates_dir=templates_dir, output_dir=output_dir)
    return generator.generate_prp_from_todo(todo, template_name, context)


if __name__ == "__main__":
    # CLI interface for testing
    import sys
    import os
    
    # Add project root to path for imports
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    
    from PRPs.scripts.todo_parser import parse_active_todos
    from PRPs.scripts.context_injector import inject_context_for_todo
    from PRPs.scripts.template_selector import select_optimal_template
    
    if len(sys.argv) < 2:
        print("Usage: python prp_generator.py <todos_file> [todo_id] [template_name]")
        sys.exit(1)
    
    todos_file = Path(sys.argv[1])
    todos = parse_active_todos(todos_file)
    
    if len(sys.argv) >= 3:
        todo_id = sys.argv[2]
        todo = next((t for t in todos if t.id == todo_id), None)
        if not todo:
            print(f"Todo {todo_id} not found")
            sys.exit(1)
    else:
        todo = todos[0] if todos else None
        if not todo:
            print("No todos found")
            sys.exit(1)
    
    print(f"Generating PRP for: {todo.id} - {todo.title}")
    
    # Generate context
    context = inject_context_for_todo(todo)
    
    # Select or use provided template
    if len(sys.argv) >= 4:
        template_name = sys.argv[3]
    else:
        template_name = select_optimal_template(todo, context)
        print(f"Selected template: {template_name}")
    
    # Generate PRP
    generator = PRPGenerator()
    try:
        prp_path = generator.generate_prp_from_todo(todo, template_name, context)
        print(f"Generated PRP: {prp_path}")
        
        # Validate result
        validation = generator.validate_generated_prp(prp_path)
        print(f"Validation: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
        if not validation['valid']:
            print(f"Missing sections: {validation['missing_sections']}")
        print(f"Stats: {validation['stats']['word_count']} words, {validation['stats']['line_count']} lines")
        
    except Exception as e:
        print(f"Error generating PRP: {e}")
        sys.exit(1)