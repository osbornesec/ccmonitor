#!/usr/bin/env python3
"""
Interactive PRP Creation Wizard

Guides users through creating comprehensive PRPs with template selection,
context injection, and quality validation.
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re

try:
    import orjson as json_lib
    def json_loads(s): return json_lib.loads(s)
    def json_dumps(obj, **kwargs): return json_lib.dumps(obj).decode('utf-8')
except ImportError:
    import json as json_lib
    json_loads = json_lib.loads
    json_dumps = json_lib.dumps

@dataclass
class PRPTemplate:
    """PRP template metadata and content"""
    name: str
    path: Path
    description: str
    complexity: str  # simple, medium, high
    domains: List[str]
    use_cases: List[str]

@dataclass
class PRPRequirements:
    """Extracted requirements for PRP creation"""
    goal: str
    user_type: str
    complexity: str
    domains: List[str]
    tdd_level: str  # basic, standard, comprehensive
    context_needs: List[str]

class PRPCreator:
    """Interactive PRP creation and customization system"""
    
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.templates = self._load_templates()
        self.context_cache = {}
    
    def _load_templates(self) -> Dict[str, PRPTemplate]:
        """Load and analyze available PRP templates"""
        templates = {}
        
        for template_file in self.templates_dir.glob('*.md'):
            try:
                content = template_file.read_text(encoding='utf-8')
                metadata = self._extract_template_metadata(content)
                
                template = PRPTemplate(
                    name=template_file.stem,
                    path=template_file,
                    description=metadata.get('description', ''),
                    complexity=metadata.get('complexity', 'medium'),
                    domains=metadata.get('domains', []),
                    use_cases=metadata.get('use_cases', [])
                )
                
                templates[template.name] = template
                
            except Exception as e:
                print(f"Warning: Could not load template {template_file}: {e}")
        
        return templates
    
    def _extract_template_metadata(self, content: str) -> Dict:
        """Extract metadata from template content"""
        metadata = {}
        
        # Extract YAML frontmatter
        if content.startswith('name:'):
            lines = content.split('\n')
            for line in lines[:20]:  # Check first 20 lines
                if ':' in line and not line.startswith('#'):
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
                elif line.startswith('---'):
                    break
        
        # Analyze content for complexity and domain indicators
        content_lower = content.lower()
        
        # Determine complexity based on content
        if 'simple' in content_lower or 'straightforward' in content_lower:
            metadata['complexity'] = 'simple'
        elif 'comprehensive' in content_lower or 'complex' in content_lower:
            metadata['complexity'] = 'high'
        else:
            metadata['complexity'] = 'medium'
        
        # Extract domain indicators
        domains = []
        domain_keywords = {
            'python': ['python', 'django', 'flask', 'fastapi', 'pytest'],
            'javascript': ['javascript', 'js', 'node', 'npm', 'jest'],
            'react': ['react', 'jsx', 'component', 'hook'],
            'api': ['api', 'endpoint', 'rest', 'graphql'],
            'database': ['database', 'sql', 'postgres', 'mongo'],
            'testing': ['test', 'tdd', 'bdd', 'coverage'],
            'ui': ['ui', 'user interface', 'frontend', 'design'],
            'backend': ['backend', 'server', 'service'],
            'mobile': ['mobile', 'flutter', 'react native']
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                domains.append(domain)
        
        metadata['domains'] = domains
        
        return metadata
    
    def create_prp_interactive(self) -> Optional[Path]:
        """Interactive PRP creation workflow"""
        print("🚀 Interactive PRP Creator")
        print("=" * 50)
        
        # Gather requirements
        requirements = self._gather_requirements()
        if not requirements:
            return None
        
        # Select template
        template = self._select_template(requirements)
        if not template:
            return None
        
        # Customize PRP
        prp_content = self._customize_prp(template, requirements)
        if not prp_content:
            return None
        
        # Save PRP
        prp_path = self._save_prp(prp_content, requirements)
        
        print(f"\n✅ PRP created successfully: {prp_path}")
        return prp_path
    
    def _gather_requirements(self) -> Optional[PRPRequirements]:
        """Gather requirements through interactive prompts"""
        try:
            print("\n📋 Requirements Gathering")
            print("-" * 30)
            
            # Goal
            goal = input("What is the main goal/feature to implement? ")
            if not goal.strip():
                print("Goal is required. Exiting.")
                return None
            
            # User type
            print("\nWho is the primary user?")
            print("1. Developer/System")
            print("2. End User")
            print("3. Administrator")
            print("4. Other")
            user_choice = input("Choose (1-4): ").strip()
            user_types = {'1': 'developer', '2': 'end_user', '3': 'admin', '4': 'other'}
            user_type = user_types.get(user_choice, 'developer')
            
            # Complexity
            print("\nWhat is the complexity level?")
            print("1. Simple (single function/component)")
            print("2. Medium (multiple components/integration)")
            print("3. High (complex system/architecture)")
            complexity_choice = input("Choose (1-3): ").strip()
            complexities = {'1': 'simple', '2': 'medium', '3': 'high'}
            complexity = complexities.get(complexity_choice, 'medium')
            
            # Domains
            print("\nWhat domains/technologies are involved? (comma-separated)")
            print("Examples: python, react, api, database, testing, ui, mobile")
            domains_input = input("Domains: ").strip()
            domains = [d.strip().lower() for d in domains_input.split(',') if d.strip()]
            
            # TDD level
            print("\nWhat level of TDD methodology?")
            print("1. Basic (simple tests)")
            print("2. Standard (comprehensive testing)")
            print("3. Comprehensive (full TDD with BDD)")
            tdd_choice = input("Choose (1-3): ").strip()
            tdd_levels = {'1': 'basic', '2': 'standard', '3': 'comprehensive'}
            tdd_level = tdd_levels.get(tdd_choice, 'standard')
            
            # Context needs
            context_needs = []
            print("\nWhat context do you need? (press enter when done)")
            while True:
                context = input("Context (file paths, docs, examples): ").strip()
                if not context:
                    break
                context_needs.append(context)
            
            return PRPRequirements(
                goal=goal,
                user_type=user_type,
                complexity=complexity,
                domains=domains,
                tdd_level=tdd_level,
                context_needs=context_needs
            )
            
        except KeyboardInterrupt:
            print("\n\nCreation cancelled.")
            return None
    
    def _select_template(self, requirements: PRPRequirements) -> Optional[PRPTemplate]:
        """Select optimal template based on requirements"""
        print(f"\n🎯 Template Selection")
        print("-" * 30)
        
        # Score templates based on requirements
        template_scores = {}
        for name, template in self.templates.items():
            score = self._score_template_fit(template, requirements)
            template_scores[name] = score
        
        # Sort by score
        sorted_templates = sorted(template_scores.items(), 
                                key=lambda x: x[1], reverse=True)
        
        if not sorted_templates:
            print("No templates available. Please add templates to templates/ directory.")
            return None
        
        # Show recommendations
        print("Recommended templates:")
        for i, (name, score) in enumerate(sorted_templates[:3], 1):
            template = self.templates[name]
            print(f"{i}. {name} (Score: {score:.1f}/100)")
            print(f"   {template.description}")
        
        # Let user choose
        print(f"{len(sorted_templates) + 1}. Show all templates")
        choice = input(f"\nChoose template (1-{len(sorted_templates) + 1}): ").strip()
        
        try:
            choice_num = int(choice)
            if choice_num == len(sorted_templates) + 1:
                return self._show_all_templates()
            elif 1 <= choice_num <= len(sorted_templates):
                template_name = sorted_templates[choice_num - 1][0]
                return self.templates[template_name]
            else:
                print("Invalid choice.")
                return None
        except ValueError:
            print("Invalid choice.")
            return None
    
    def _score_template_fit(self, template: PRPTemplate, 
                           requirements: PRPRequirements) -> float:
        """Score how well a template fits the requirements"""
        score = 0.0
        
        # Complexity match (40 points)
        if template.complexity == requirements.complexity:
            score += 40
        elif (template.complexity == 'medium' and 
              requirements.complexity in ['simple', 'high']):
            score += 20  # Medium templates are adaptable
        
        # Domain match (30 points)
        if template.domains and requirements.domains:
            domain_overlap = set(template.domains) & set(requirements.domains)
            domain_score = (len(domain_overlap) / len(requirements.domains)) * 30
            score += domain_score
        
        # User type compatibility (20 points)
        user_type_compatibility = {
            'prp_bdd_specification': ['end_user'],
            'prp_tdd_base': ['developer'],
            'prp_simple_task': ['developer'],
            'prp_red_green_refactor': ['developer']
        }
        
        compatible_users = user_type_compatibility.get(template.name, ['developer'])
        if requirements.user_type in compatible_users:
            score += 20
        
        # TDD level compatibility (10 points)
        tdd_compatibility = {
            'prp_tdd_base': ['standard', 'comprehensive'],
            'prp_bdd_specification': ['comprehensive'],
            'prp_simple_task': ['basic', 'standard'],
            'prp_red_green_refactor': ['standard', 'comprehensive']
        }
        
        compatible_tdd = tdd_compatibility.get(template.name, ['standard'])
        if requirements.tdd_level in compatible_tdd:
            score += 10
        
        return score
    
    def _show_all_templates(self) -> Optional[PRPTemplate]:
        """Show all available templates for selection"""
        print("\nAll Available Templates:")
        template_list = list(self.templates.items())
        
        for i, (name, template) in enumerate(template_list, 1):
            print(f"{i}. {name}")
            print(f"   Complexity: {template.complexity}")
            print(f"   Domains: {', '.join(template.domains)}")
            print(f"   {template.description}")
            print()
        
        choice = input(f"Choose template (1-{len(template_list)}): ").strip()
        
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(template_list):
                return template_list[choice_num - 1][1]
            else:
                print("Invalid choice.")
                return None
        except ValueError:
            print("Invalid choice.")
            return None
    
    def _customize_prp(self, template: PRPTemplate, 
                      requirements: PRPRequirements) -> Optional[str]:
        """Customize template with requirements"""
        print(f"\n⚙️ Customizing PRP")
        print("-" * 30)
        
        try:
            content = template.path.read_text(encoding='utf-8')
            
            # Basic substitutions
            customizations = {
                '[Specific, measurable end state with testable outcomes]': requirements.goal,
                '[specific user type/role]': requirements.user_type,
                '[Clear, specific task to accomplish]': requirements.goal,
                '[User-facing behavior or capability being delivered]': requirements.goal
            }
            
            for placeholder, replacement in customizations.items():
                content = content.replace(placeholder, replacement)
            
            # Add domain-specific context
            if requirements.context_needs:
                context_section = self._generate_context_section(requirements)
                # Insert context into the "All Needed Context" section
                content = self._insert_context(content, context_section)
            
            # Add TDD customizations based on domains
            content = self._add_domain_specific_tdd(content, requirements.domains)
            
            return content
            
        except Exception as e:
            print(f"Error customizing PRP: {e}")
            return None
    
    def _generate_context_section(self, requirements: PRPRequirements) -> str:
        """Generate context section based on requirements"""
        context_lines = []
        
        for context_need in requirements.context_needs:
            # Try to determine if it's a file path, URL, or other reference
            if '/' in context_need or context_need.endswith(('.py', '.js', '.md')):
                context_lines.append(f"- file: {context_need}")
                context_lines.append(f"  why: [Specific pattern or information needed]")
            elif context_need.startswith('http'):
                context_lines.append(f"- url: {context_need}")
                context_lines.append(f"  why: [Key information from this resource]")
            else:
                context_lines.append(f"- reference: {context_need}")
                context_lines.append(f"  why: [How this relates to implementation]")
            context_lines.append("")
        
        return '\n'.join(context_lines)
    
    def _insert_context(self, content: str, context_section: str) -> str:
        """Insert generated context into PRP content"""
        # Find the context section and add generated content
        context_marker = "# MUST READ - Include these in your context window"
        if context_marker in content:
            insertion_point = content.find(context_marker)
            # Find the end of the yaml block
            yaml_end = content.find("```", insertion_point + len(context_marker))
            if yaml_end != -1:
                # Insert before the closing ```
                content = (content[:yaml_end] + 
                          context_section + "\n" + 
                          content[yaml_end:])
        
        return content
    
    def _add_domain_specific_tdd(self, content: str, domains: List[str]) -> str:
        """Add domain-specific TDD guidance"""
        tdd_additions = {
            'python': """
# Python TDD Patterns
pytest [test_files] -v --cov=[module] --cov-report=term-missing
ruff check [files] --fix
mypy [files]""",
            
            'javascript': """
# JavaScript TDD Patterns  
npm test -- [test_files] --coverage
eslint [files] --fix
npm run type-check  # if using TypeScript""",
            
            'react': """
# React TDD Patterns
npm test -- --watchAll=false --coverage
npm run test:components  # Component testing
npm run lint:jsx""",
            
            'api': """
# API TDD Patterns
pytest tests/api/ -v
curl -X POST [endpoint] -H "Content-Type: application/json" -d '[test_data]'
postman run api_tests.json"""
        }
        
        # Add domain-specific TDD patterns to validation sections
        for domain in domains:
            if domain in tdd_additions:
                pattern = tdd_additions[domain]
                # Insert into Level 2 validation section
                level2_marker = "### Level 2: Unit Tests"
                if level2_marker in content:
                    insertion_point = content.find("```bash", content.find(level2_marker))
                    if insertion_point != -1:
                        bash_end = content.find("```", insertion_point + 7)
                        if bash_end != -1:
                            content = (content[:bash_end] + 
                                     pattern + "\n\n" + 
                                     content[bash_end:])
        
        return content
    
    def _save_prp(self, content: str, requirements: PRPRequirements) -> Path:
        """Save customized PRP to file"""
        # Generate filename from goal
        filename = re.sub(r'[^a-zA-Z0-9\s-]', '', requirements.goal)
        filename = re.sub(r'\s+', '-', filename.strip()).lower()
        filename = filename[:50]  # Limit length
        
        # Add timestamp to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        prp_filename = f"{filename}-{timestamp}.md"
        
        # Save to active PRPs directory
        active_dir = Path('PRPs/active')
        active_dir.mkdir(parents=True, exist_ok=True)
        prp_path = active_dir / prp_filename
        
        prp_path.write_text(content, encoding='utf-8')
        
        return prp_path

def main():
    """Main CLI interface for PRP creation"""
    parser = argparse.ArgumentParser(description="Create comprehensive PRPs interactively")
    parser.add_argument('--templates-dir', type=Path, default=Path('PRPs/templates'),
                       help="Directory containing PRP templates")
    parser.add_argument('--goal', type=str, help="PRP goal (non-interactive mode)")
    parser.add_argument('--template', type=str, help="Template to use (non-interactive)")
    parser.add_argument('--output-dir', type=Path, default=Path('PRPs/active'),
                       help="Output directory for created PRPs")
    
    args = parser.parse_args()
    
    if not args.templates_dir.exists():
        print(f"Templates directory not found: {args.templates_dir}")
        return 1
    
    creator = PRPCreator(args.templates_dir)
    
    if not creator.templates:
        print("No templates found. Please add templates to templates/ directory.")
        return 1
    
    if args.goal and args.template:
        # Non-interactive mode (for automation)
        print("Non-interactive mode not yet implemented")
        return 1
    else:
        # Interactive mode
        prp_path = creator.create_prp_interactive()
        if prp_path:
            print(f"\n🎉 PRP created: {prp_path}")
            print("You can now execute this PRP or edit it further.")
            return 0
        else:
            print("PRP creation cancelled or failed.")
            return 1

if __name__ == '__main__':
    sys.exit(main())