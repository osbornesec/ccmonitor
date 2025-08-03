"""
Intelligent PRP template selection based on todo characteristics
Multi-criteria analysis for optimal template matching and customization
"""
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TemplateSelector:
    """Intelligent PRP template selection engine"""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize template selector with template information
        
        Args:
            templates_dir: Path to templates directory (optional)
        """
        self.templates_dir = templates_dir or Path(__file__).parent.parent / "templates"
        
        # Template capability information
        self.template_info: Dict[str, Dict[str, Any]] = {
            'prp_tdd_base.md': {
                'complexity': 'high',
                'domains': ['backend', 'database', 'api', 'python', 'security'],
                'validation_levels': 4,
                'min_effort_hours': 4,
                'max_effort_hours': 20,
                'description': 'Comprehensive TDD-based PRP for complex backend systems',
                'best_for': ['authentication', 'api design', 'database systems', 'security features'],
                'keywords': ['system', 'architecture', 'database', 'api', 'security', 'authentication']
            },
            'prp_red_green_refactor.md': {
                'complexity': 'medium',
                'domains': ['refactoring', 'optimization', 'performance', 'backend', 'frontend'],
                'validation_levels': 3,
                'min_effort_hours': 2,
                'max_effort_hours': 8,
                'description': 'Red-Green-Refactor methodology for code improvements',
                'best_for': ['optimization', 'refactoring', 'performance', 'code cleanup'],
                'keywords': ['optimize', 'refactor', 'improve', 'performance', 'clean', 'fix']
            },
            'prp_bdd_specification.md': {
                'complexity': 'medium',
                'domains': ['frontend', 'user-facing', 'react', 'vue', 'ui', 'testing'],
                'validation_levels': 4,
                'min_effort_hours': 2,
                'max_effort_hours': 10,
                'description': 'Behavior-Driven Development for user-facing features',
                'best_for': ['ui components', 'user flows', 'frontend features', 'user stories'],
                'keywords': ['user', 'interface', 'component', 'page', 'form', 'ui', 'ux']
            },
            'prp_simple_task.md': {
                'complexity': 'low', 
                'domains': ['documentation', 'configuration', 'simple fixes', 'general'],
                'validation_levels': 2,
                'min_effort_hours': 0.5,
                'max_effort_hours': 3,
                'description': 'Simple task template for straightforward implementations',
                'best_for': ['bug fixes', 'documentation', 'configuration', 'simple features'],
                'keywords': ['fix', 'update', 'add', 'simple', 'config', 'documentation', 'typo']
            }
        }
        
        # Domain mapping for template selection
        self.domain_template_affinity = {
            'python': ['prp_tdd_base.md', 'prp_red_green_refactor.md'],
            'javascript': ['prp_bdd_specification.md', 'prp_red_green_refactor.md'],
            'react': ['prp_bdd_specification.md'],
            'vue': ['prp_bdd_specification.md'],
            'api': ['prp_tdd_base.md'],
            'database': ['prp_tdd_base.md', 'prp_red_green_refactor.md'],
            'security': ['prp_tdd_base.md'],
            'frontend': ['prp_bdd_specification.md'],
            'backend': ['prp_tdd_base.md', 'prp_red_green_refactor.md'],
            'testing': ['prp_bdd_specification.md', 'prp_tdd_base.md'],
            'performance': ['prp_red_green_refactor.md'],
            'refactoring': ['prp_red_green_refactor.md'],
            'documentation': ['prp_simple_task.md'],
            'configuration': ['prp_simple_task.md'],
            'infrastructure': ['prp_tdd_base.md'],
            'mobile': ['prp_bdd_specification.md']
        }
        
        # Complexity indicators
        self.complexity_keywords = {
            'high': ['system', 'architecture', 'authentication', 'security', 'integration', 
                    'microservice', 'distributed', 'scalable', 'enterprise'],
            'medium': ['component', 'feature', 'service', 'module', 'workflow', 'process'],
            'low': ['fix', 'update', 'add', 'change', 'simple', 'typo', 'config']
        }
    
    def select_optimal_template(self, todo, context) -> str:
        """
        Select the optimal PRP template based on todo characteristics and context
        
        Args:
            todo: TodoItem with requirements and metadata
            context: ContextPackage with project context
            
        Returns:
            Template filename that best matches the requirements
        """
        logger.info(f"Selecting template for todo: {todo.id}")
        
        # Score all available templates
        template_scores = {}
        
        for template_name in self.template_info.keys():
            score = self._score_template_fit(template_name, todo, context)
            template_scores[template_name] = score
            logger.debug(f"Template {template_name}: score {score}")
        
        # Select template with highest score
        best_template = max(template_scores.keys(), key=lambda k: template_scores[k])
        logger.info(f"Selected template: {best_template} (score: {template_scores[best_template]:.2f})")
        
        return best_template
    
    def _score_template_fit(self, template_name: str, todo, context) -> float:
        """
        Comprehensive scoring of template fitness for a todo
        
        Args:
            template_name: Name of template to score
            todo: TodoItem to match against  
            context: ContextPackage with additional context
            
        Returns:
            Fitness score (higher = better fit)
        """
        template_info = self.template_info[template_name]
        score = 0.0
        
        # 1. Complexity matching (30% weight)
        complexity_score = self._score_complexity_match(template_info, todo)
        score += complexity_score * 0.3
        
        # 2. Domain affinity (25% weight)
        domain_score = self._analyze_domain_fit(template_name, todo.domain_areas)
        score += domain_score * 0.25
        
        # 3. Effort estimation fit (20% weight)
        effort_score = self._score_effort_fit(template_info, todo)
        score += effort_score * 0.2
        
        # 4. Keyword matching (15% weight)
        keyword_score = self._score_keyword_match(template_info, todo)
        score += keyword_score * 0.15
        
        # 5. Context richness consideration (10% weight)
        context_score = self._score_context_fit(template_info, context)
        score += context_score * 0.1
        
        return score
    
    def _score_complexity_match(self, template_info: Dict[str, Any], todo) -> float:
        """Score how well template complexity matches todo complexity"""
        todo_complexity = self._calculate_complexity_score(todo)
        template_complexity = self._get_template_complexity_score(template_info)
        
        # Calculate match score (closer = better)
        complexity_diff = abs(todo_complexity - template_complexity)
        max_diff = 10.0  # Maximum possible difference
        
        # Invert so closer match = higher score
        match_score = max(0, (max_diff - complexity_diff) / max_diff)
        
        return match_score * 10.0  # Scale to 0-10
    
    def _calculate_complexity_score(self, todo) -> float:
        """
        Calculate complexity score for a todo based on multiple factors
        
        Args:
            todo: TodoItem to analyze
            
        Returns:
            Complexity score (0-10, higher = more complex)
        """
        score = 0.0
        
        # 1. Effort estimation (40% weight)
        effort_score = self._parse_effort_hours(todo.estimated_effort)
        # Scale hours to 0-10 (8+ hours = max complexity)
        effort_normalized = min(10.0, effort_score * 1.25)
        score += effort_normalized * 0.4
        
        # 2. Number of subtasks (25% weight)
        subtask_count = len(todo.subtasks)
        # Scale subtasks (6+ subtasks = high complexity)
        subtask_score = min(10.0, subtask_count * 1.67)
        score += subtask_score * 0.25
        
        # 3. Domain count and complexity (20% weight)
        domain_complexity = self._analyze_domain_complexity(todo.domain_areas)
        score += domain_complexity * 0.2
        
        # 4. Dependencies (10% weight)
        dependency_score = min(10.0, len(todo.dependencies) * 2.0)
        score += dependency_score * 0.1
        
        # 5. Priority influence (5% weight)
        priority_score = {'High': 8.0, 'Medium': 5.0, 'Low': 2.0}.get(todo.priority, 5.0)
        score += priority_score * 0.05
        
        return min(10.0, score)
    
    def _analyze_domain_fit(self, template_name: str, domains: List[str]) -> float:
        """
        Analyze how well a template fits the given domains
        
        Args:
            template_name: Template to analyze
            domains: List of domain areas
            
        Returns:
            Domain fit score (0-10)
        """
        template_info = self.template_info[template_name]
        template_domains = template_info['domains']
        
        if not domains:
            return 5.0  # Neutral score for no domains
        
        # Calculate overlap between todo domains and template domains
        domain_matches = 0.0
        for domain in domains:
            # Direct match in template domains
            if domain in template_domains:
                domain_matches += 2.0
            # Check affinity mapping
            elif domain in self.domain_template_affinity:
                if template_name in self.domain_template_affinity[domain]:
                    domain_matches += 1.5
            # Partial string matching
            elif any(td in domain or domain in td for td in template_domains):
                domain_matches += 0.5
        
        # Normalize score
        max_possible_score = len(domains) * 2.0
        if max_possible_score > 0:
            score = (domain_matches / max_possible_score) * 10.0
        else:
            score = 5.0
        
        return min(10.0, score)
    
    def _score_effort_fit(self, template_info: Dict[str, Any], todo) -> float:
        """Score how well template effort range matches todo effort"""
        todo_hours = self._parse_effort_hours(todo.estimated_effort)
        template_min = template_info['min_effort_hours']
        template_max = template_info['max_effort_hours']
        
        # Perfect fit if todo effort is within template range
        if template_min <= todo_hours <= template_max:
            return 10.0
        
        # Calculate distance from range
        if todo_hours < template_min:
            distance = template_min - todo_hours
        else:
            distance = todo_hours - template_max
        
        # Score decreases with distance
        max_distance = 10.0  # Maximum hours outside range to consider
        score = max(0, (max_distance - distance) / max_distance) * 10.0
        
        return score
    
    def _score_keyword_match(self, template_info: Dict[str, Any], todo) -> float:
        """Score keyword matching between template and todo"""
        template_keywords = template_info.get('keywords', [])
        
        # Combine todo text for analysis
        todo_text = (todo.title + ' ' + todo.description + ' ' + 
                    ' '.join(todo.subtasks)).lower()
        
        matches = 0
        for keyword in template_keywords:
            if keyword.lower() in todo_text:
                matches += 1
        
        # Normalize score
        if template_keywords:
            score = (matches / len(template_keywords)) * 10.0
        else:
            score = 5.0  # Neutral if no keywords
        
        return score
    
    def _score_context_fit(self, template_info: Dict[str, Any], context) -> float:
        """Score how well template fits the available context"""
        # Rich context suggests complex requirements
        context_richness = (
            len(context.code_examples) * 0.3 +
            len(context.documentation) * 0.2 +
            len(context.gotchas) * 0.2 +
            len(context.architectural_patterns) * 0.15 +
            len(context.integration_points) * 0.15
        )
        
        template_complexity = template_info.get('validation_levels', 2)
        
        # More complex templates benefit from richer context
        if template_complexity >= 4 and context_richness >= 3:
            return 8.0
        elif template_complexity >= 3 and context_richness >= 2:
            return 6.0
        elif template_complexity <= 2 and context_richness <= 1:
            return 7.0  # Simple templates don't need much context
        else:
            return 5.0  # Neutral score
    
    def _parse_effort_hours(self, effort_string: str) -> float:
        """Parse effort estimation string to extract hours"""
        if not effort_string:
            return 2.0  # Default
        
        # Extract numbers from effort string
        numbers = re.findall(r'\d+(?:\.\d+)?', effort_string)
        
        if not numbers:
            return 2.0
        
        # If range (e.g., "3-4 hours"), take average
        if len(numbers) >= 2:
            return (float(numbers[0]) + float(numbers[1])) / 2
        else:
            return float(numbers[0])
    
    def _analyze_domain_complexity(self, domains: List[str]) -> float:
        """Analyze complexity based on domain areas"""
        if not domains:
            return 2.0
        
        complexity_scores = {
            'security': 9.0,
            'architecture': 8.5,
            'database': 7.0,
            'api': 6.5,
            'backend': 6.0,
            'infrastructure': 7.5,
            'performance': 7.0,
            'testing': 5.0,
            'frontend': 4.0,
            'ui': 3.0,
            'documentation': 1.0,
            'configuration': 1.5
        }
        
        total_complexity = 0.0
        for domain in domains:
            domain_score = complexity_scores.get(domain, 4.0)  # Default medium
            total_complexity += domain_score
        
        # Average complexity, but cap at 10
        avg_complexity = total_complexity / len(domains)
        return min(10.0, avg_complexity)
    
    def _get_template_complexity_score(self, template_info: Dict[str, Any]) -> float:
        """Convert template complexity level to numeric score"""
        complexity_level = template_info.get('complexity', 'medium')
        complexity_scores = {
            'low': 2.0,
            'medium': 5.0,
            'high': 8.0
        }
        return complexity_scores.get(complexity_level, 5.0)
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """Get information about a specific template"""
        return self.template_info.get(template_name, {})
    
    def list_available_templates(self) -> List[str]:
        """List all available template names"""
        return list(self.template_info.keys())
    
    def get_templates_for_domain(self, domain: str) -> List[str]:
        """Get recommended templates for a specific domain"""
        return self.domain_template_affinity.get(domain, ['prp_tdd_base.md'])
    
    def explain_selection(self, template_name: str, todo, context) -> Dict[str, Any]:
        """
        Provide detailed explanation of why a template was selected
        
        Returns:
            Dictionary with selection reasoning
        """
        template_info = self.template_info[template_name]
        
        explanation = {
            'selected_template': template_name,
            'template_description': template_info['description'],
            'complexity_match': {
                'todo_complexity': self._calculate_complexity_score(todo),
                'template_complexity': self._get_template_complexity_score(template_info),
                'match_score': self._score_complexity_match(template_info, todo)
            },
            'domain_fit': {
                'todo_domains': todo.domain_areas,
                'template_domains': template_info['domains'],
                'fit_score': self._analyze_domain_fit(template_name, todo.domain_areas)
            },
            'effort_fit': {
                'todo_effort': todo.estimated_effort, 
                'template_range': f"{template_info['min_effort_hours']}-{template_info['max_effort_hours']} hours",
                'fit_score': self._score_effort_fit(template_info, todo)
            },
            'total_score': self._score_template_fit(template_name, todo, context)
        }
        
        return explanation


# Module-level convenience function
def select_optimal_template(todo, context, templates_dir: Optional[Path] = None) -> str:
    """
    Convenience function for template selection
    
    Args:
        todo: TodoItem to select template for
        context: ContextPackage with project context
        templates_dir: Optional path to templates directory
        
    Returns:
        Selected template filename
    """
    selector = TemplateSelector(templates_dir=templates_dir)
    return selector.select_optimal_template(todo, context)


if __name__ == "__main__":
    # CLI interface for testing
    import sys
    import os
    
    # Add project root to path for imports
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    
    from PRPs.scripts.todo_parser import parse_active_todos
    from PRPs.scripts.context_injector import inject_context_for_todo
    
    if len(sys.argv) < 2:
        print("Usage: python template_selector.py <todos_file> [todo_id]")
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
    
    print(f"Analyzing template selection for: {todo.id} - {todo.title}")
    print(f"Domains: {', '.join(todo.domain_areas)}")
    print(f"Effort: {todo.estimated_effort}")
    print(f"Priority: {todo.priority}")
    print()
    
    # Generate context
    context = inject_context_for_todo(todo)
    
    # Select template
    selector = TemplateSelector()
    template = selector.select_optimal_template(todo, context)
    
    print(f"Selected template: {template}")
    print()
    
    # Show detailed explanation
    explanation = selector.explain_selection(template, todo, context)
    print("Selection reasoning:")
    print(f"- Complexity match: {explanation['complexity_match']['match_score']:.1f}/10")
    print(f"- Domain fit: {explanation['domain_fit']['fit_score']:.1f}/10")
    print(f"- Effort fit: {explanation['effort_fit']['fit_score']:.1f}/10")
    print(f"- Total score: {explanation['total_score']:.1f}")
    print()
    print(f"Template description: {explanation['template_description']}")
    
    # Show alternatives
    print("\nAlternative templates:")
    for template_name in selector.list_available_templates():
        if template_name != template:
            score = selector._score_template_fit(template_name, todo, context)
            print(f"- {template_name}: {score:.1f}/10")