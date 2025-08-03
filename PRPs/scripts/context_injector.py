"""
Intelligent context analysis and injection for PRP enhancement
Multi-source context gathering and relevance scoring for comprehensive PRPs
"""
import re
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Set, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ContextPackage:
    """Context package with all needed information for PRP generation"""
    code_examples: List[str] = field(default_factory=list)
    documentation: List[str] = field(default_factory=list)
    gotchas: List[str] = field(default_factory=list)
    architectural_patterns: List[str] = field(default_factory=list)
    integration_points: List[str] = field(default_factory=list)
    library_references: List[str] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)
    similar_implementations: List[str] = field(default_factory=list)


class ContextInjector:
    """Intelligent context analysis and injection engine"""
    
    def __init__(self, project_root: Path, use_cache: bool = False, max_context_size: int = 10000):
        self.project_root = Path(project_root)
        self.use_cache = use_cache
        self.max_context_size = max_context_size
        self.cache: Dict[str, ContextPackage] = {}
        
        # File extensions to analyze
        self.code_extensions = {
            '.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.rs', '.java', 
            '.c', '.cpp', '.h', '.hpp', '.cs', '.php', '.rb', '.swift', '.kt'
        }
        
        self.doc_extensions = {
            '.md', '.rst', '.txt', '.adoc', '.org'
        }
        
        self.config_extensions = {
            '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf'
        }
        
        # Domain-specific keywords for relevance scoring
        self.domain_keywords = {
            'python': ['def ', 'class ', 'import ', 'from ', '__init__', 'self.', 'django', 'flask', 'fastapi'],
            'javascript': ['function', 'const ', 'let ', 'var ', 'class ', 'import ', 'export', 'async', 'await'],
            'api': ['endpoint', 'route', 'request', 'response', 'http', 'rest', 'graphql', 'swagger'],
            'database': ['model', 'schema', 'query', 'table', 'db', 'sql', 'mongodb', 'postgresql'],
            'security': ['auth', 'token', 'jwt', 'password', 'hash', 'encrypt', 'permission', 'session'],
            'testing': ['test', 'assert', 'mock', 'fixture', 'pytest', 'jest', 'spec', 'describe'],
            'frontend': ['component', 'render', 'state', 'props', 'css', 'html', 'dom', 'react'],
            'backend': ['server', 'service', 'handler', 'middleware', 'controller', 'model'],
            'infrastructure': ['docker', 'kubernetes', 'deploy', 'config', 'env', 'container'],
            'performance': ['cache', 'optimize', 'async', 'parallel', 'memory', 'cpu', 'benchmark']
        }
        
        # Common gotcha patterns
        self.gotcha_patterns = [
            r'(?i)gotcha|pitfall|warning|caution|note|important',
            r'(?i)don\'t|avoid|never|always',
            r'(?i)common mistake|common error|frequently|often',
            r'(?i)be careful|make sure|ensure|remember',
            r'(?i)watch out|look out|beware'
        ]
        
        # Best practices patterns
        self.best_practice_patterns = [
            r'(?i)best practice|recommended|should|guideline',
            r'(?i)good practice|convention|standard',
            r'(?i)tip|hint|suggestion|advice',
            r'(?i)optimize|improve|enhance|better'
        ]
    
    def inject_context_for_todo(self, todo) -> ContextPackage:
        """
        Main context injection method - analyzes todo and injects comprehensive context
        
        Args:
            todo: TodoItem with domain areas and requirements
            
        Returns:
            ContextPackage with all relevant context
        """
        # Generate cache key
        cache_key = self._generate_cache_key(todo)
        
        # Check cache first
        if self.use_cache and cache_key in self.cache:
            logger.info(f"Using cached context for {todo.id}")
            return self.cache[cache_key]
        
        logger.info(f"Generating context for todo: {todo.id}")
        
        # Initialize context package
        context = ContextPackage()
        
        # Analyze project structure
        self._analyze_code_examples(todo, context)
        self._extract_documentation(todo, context)
        self._identify_gotchas(context)
        self._find_architectural_patterns(todo, context)
        self._identify_integration_points(todo, context)
        self._extract_library_references(context)
        self._include_best_practices(context)
        self._find_similar_implementations(todo, context)
        
        # Apply size limits
        context = self._apply_size_limits(context)
        
        # Cache result
        if self.use_cache:
            self.cache[cache_key] = context
        
        return context
    
    def _generate_cache_key(self, todo) -> str:
        """Generate cache key based on todo characteristics"""
        key_data = f"{todo.id}:{','.join(todo.domain_areas)}:{todo.title}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _analyze_code_examples(self, todo, context: ContextPackage):
        """Find and analyze relevant code examples"""
        if not self.project_root.exists():
            return
        
        relevant_files = self._find_relevant_files(todo.domain_areas, self.code_extensions)
        
        for file_path in relevant_files[:10]:  # Limit to top 10 most relevant
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                # Extract relevant code snippets
                snippets = self._extract_code_snippets(content, todo.domain_areas)
                context.code_examples.extend(snippets)
                
            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")
    
    def _extract_documentation(self, todo, context: ContextPackage):
        """Extract relevant documentation"""
        if not self.project_root.exists():
            return
        
        doc_files = self._find_relevant_files(todo.domain_areas, self.doc_extensions)
        
        for file_path in doc_files[:5]:  # Limit documentation files
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                # Extract relevant sections
                doc_sections = self._extract_doc_sections(content, todo.domain_areas)
                context.documentation.extend(doc_sections)
                
            except Exception as e:
                logger.warning(f"Error reading doc {file_path}: {e}")
    
    def _identify_gotchas(self, context: ContextPackage):
        """Identify gotchas and pitfalls from documentation"""
        for doc in context.documentation[:]:  # Copy to avoid modification during iteration
            gotchas = self._extract_gotchas_from_text(doc)
            context.gotchas.extend(gotchas)
    
    def _find_architectural_patterns(self, todo, context: ContextPackage):
        """Identify architectural patterns in the codebase"""
        patterns = set()
        
        # Analyze code examples for patterns
        for code in context.code_examples:
            detected_patterns = self._detect_patterns_in_code(code)
            patterns.update(detected_patterns)
        
        context.architectural_patterns = list(patterns)
    
    def _identify_integration_points(self, todo, context: ContextPackage):
        """Identify integration points relevant to the todo"""
        integration_points = set()
        
        # Based on domain areas, identify likely integration points
        domain_integrations = {
            'api': ['Database', 'Authentication', 'Caching', 'External APIs'],
            'database': ['ORM/ODM', 'Connection pooling', 'Migrations', 'Backup systems'],
            'security': ['Authentication service', 'Authorization middleware', 'Token storage'],
            'frontend': ['Backend API', 'State management', 'Routing', 'Asset pipeline'],
            'testing': ['Test database', 'Mock services', 'CI/CD pipeline'],
            'infrastructure': ['Load balancer', 'Container orchestration', 'Monitoring']
        }
        
        for domain in todo.domain_areas:
            if domain in domain_integrations:
                integration_points.update(domain_integrations[domain])
        
        context.integration_points = list(integration_points)
    
    def _extract_library_references(self, context: ContextPackage):
        """Extract library and framework references from code examples"""
        libraries = set()
        
        for code in context.code_examples:
            # Python imports
            python_imports = re.findall(r'(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_]*)', code)
            libraries.update(python_imports)
            
            # JavaScript/TypeScript imports  
            js_imports = re.findall(r'import.*?from\s+[\'"]([^\'\"]+)[\'"]', code)
            libraries.update(js_imports)
            
            # Other common patterns
            # Package.json, requirements.txt references could be added here
        
        # Filter to common libraries
        common_libraries = {
            'django', 'flask', 'fastapi', 'express', 'react', 'vue', 'angular',
            'pytorch', 'tensorflow', 'numpy', 'pandas', 'requests', 'axios',
            'jest', 'pytest', 'mocha', 'cypress', 'selenium'
        }
        
        relevant_libraries = libraries.intersection(common_libraries)
        context.library_references = [f"{lib} - {self._get_library_description(lib)}" 
                                    for lib in relevant_libraries]
    
    def _include_best_practices(self, context: ContextPackage):
        """Extract best practices from documentation"""
        for doc in context.documentation:
            practices = self._extract_best_practices_from_text(doc)
            context.best_practices.extend(practices)
    
    def _find_similar_implementations(self, todo, context: ContextPackage):
        """Find similar implementations in the codebase"""
        # This could be enhanced with ML-based similarity matching
        # For now, use keyword-based matching
        
        similar_files = []
        keywords = todo.title.lower().split() + [word.lower() for word in todo.subtasks]
        
        if self.project_root.exists():
            for file_path in self.project_root.rglob('*'):
                if (file_path.suffix in self.code_extensions and 
                    self._calculate_similarity_score(file_path, keywords) > 0.3):
                    similar_files.append(file_path)
        
        # Extract relevant snippets from similar files
        for file_path in similar_files[:3]:  # Limit to top 3
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                snippet = content[:500] + "..." if len(content) > 500 else content
                context.similar_implementations.append(f"From {file_path.name}:\n{snippet}")
            except Exception as e:
                logger.warning(f"Error reading similar file {file_path}: {e}")
    
    def _find_relevant_files(self, domains: List[str], extensions: Set[str]) -> List[Path]:
        """Find files relevant to the given domains"""
        relevant_files: List[tuple[Path, float]] = []
        
        if not self.project_root.exists():
            return []
        
        for file_path in self.project_root.rglob('*'):
            if file_path.suffix in extensions:
                relevance_score = self._calculate_file_relevance(file_path, domains)
                if relevance_score > 0:
                    relevant_files.append((file_path, relevance_score))
        
        # Sort by relevance score
        relevant_files.sort(key=lambda x: x[1], reverse=True)
        return [f[0] for f in relevant_files]
    
    def _calculate_file_relevance(self, file_path: Path, domains: List[str]) -> float:
        """Calculate relevance score for a file based on domains"""
        score = 0.0
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            content_lower = content.lower()
            
            for domain in domains:
                if domain in self.domain_keywords:
                    for keyword in self.domain_keywords[domain]:
                        score += content_lower.count(keyword.lower()) * 0.1
            
            # Bonus for file name relevance
            file_name_lower = file_path.name.lower()
            for domain in domains:
                if domain in file_name_lower:
                    score += 1.0
            
        except Exception:
            pass
        
        return score
    
    def _extract_code_snippets(self, content: str, domains: List[str]) -> List[str]:
        """Extract relevant code snippets from file content"""
        snippets = []
        lines = content.split('\n')
        
        # Find functions, classes, and other relevant blocks
        current_snippet = []
        in_relevant_block = False
        
        for i, line in enumerate(lines):
            # Check if line is relevant to domains
            line_lower = line.lower()
            is_relevant = any(
                any(keyword.lower() in line_lower for keyword in self.domain_keywords.get(domain, []))
                for domain in domains
            )
            
            if is_relevant:
                in_relevant_block = True
                current_snippet = [line]
            elif in_relevant_block:
                current_snippet.append(line)
                
                # End snippet at natural boundaries
                if (len(current_snippet) > 20 or 
                    line.strip() == '' and len(current_snippet) > 5):
                    snippets.append('\n'.join(current_snippet))
                    current_snippet = []
                    in_relevant_block = False
        
        # Add final snippet if exists
        if current_snippet:
            snippets.append('\n'.join(current_snippet))
        
        return snippets[:5]  # Limit snippets per file
    
    def _extract_doc_sections(self, content: str, domains: List[str]) -> List[str]:
        """Extract relevant documentation sections"""
        sections = []
        
        # Split by markdown headers
        sections_raw = re.split(r'\n(?=#{1,6}\s)', content)
        
        for section in sections_raw:
            section_lower = section.lower()
            is_relevant = any(
                domain.lower() in section_lower for domain in domains
            )
            
            if is_relevant and len(section.strip()) > 50:
                sections.append(section.strip())
        
        return sections[:3]  # Limit sections
    
    def _extract_gotchas_from_text(self, text: str) -> List[str]:
        """Extract gotchas and pitfalls from text"""
        gotchas = []
        lines = text.split('\n')
        
        for line in lines:
            for pattern in self.gotcha_patterns:
                if re.search(pattern, line):
                    gotchas.append(line.strip())
                    break
        
        return gotchas[:3]  # Limit gotchas per document
    
    def _extract_best_practices_from_text(self, text: str) -> List[str]:
        """Extract best practices from text"""
        practices = []
        lines = text.split('\n')
        
        for line in lines:
            for pattern in self.best_practice_patterns:
                if re.search(pattern, line):
                    practices.append(line.strip())
                    break
        
        return practices[:3]  # Limit practices per document
    
    def _detect_patterns_in_code(self, code: str) -> List[str]:
        """Detect architectural patterns in code"""
        patterns = []
        code_lower = code.lower()
        
        pattern_indicators = {
            'MVC': ['model', 'view', 'controller'],
            'Repository Pattern': ['repository', 'interface'],
            'Factory Pattern': ['factory', 'create'],
            'Singleton Pattern': ['singleton', 'instance'],
            'Observer Pattern': ['observer', 'notify', 'subscribe'],
            'Decorator Pattern': ['decorator', '@'],
            'Middleware Pattern': ['middleware', 'next', 'request'],
            'Service Layer': ['service', 'business logic'],
            'Data Transfer Object': ['dto', 'data transfer'],
            'Active Record': ['active record', 'model']
        }
        
        for pattern, indicators in pattern_indicators.items():
            if any(indicator in code_lower for indicator in indicators):
                patterns.append(pattern)
        
        return patterns
    
    def _calculate_similarity_score(self, file_path: Path, keywords: List[str]) -> float:
        """Calculate similarity score between file and keywords"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore').lower()
            
            matches = sum(1 for keyword in keywords if keyword in content)
            return matches / len(keywords) if keywords else 0.0
            
        except Exception:
            return 0.0
    
    def _get_library_description(self, library: str) -> str:
        """Get brief description of library"""
        descriptions = {
            'django': 'Python web framework',
            'flask': 'Python microframework', 
            'fastapi': 'Modern Python API framework',
            'express': 'Node.js web framework',
            'react': 'JavaScript UI library',
            'vue': 'Progressive JavaScript framework',
            'pytest': 'Python testing framework',
            'jest': 'JavaScript testing framework',
            'requests': 'Python HTTP library',
            'axios': 'JavaScript HTTP client'
        }
        return descriptions.get(library, 'Popular library')
    
    def _apply_size_limits(self, context: ContextPackage) -> ContextPackage:
        """Apply size limits to prevent token overflow"""
        def truncate_list(items: List[str], max_total_length: int) -> List[str]:
            truncated = []
            current_length = 0
            
            for item in items:
                if current_length + len(item) <= max_total_length:
                    truncated.append(item)
                    current_length += len(item)
                else:
                    break
            
            return truncated
        
        # Distribute size budget across context types
        budget_per_type = self.max_context_size // 8
        
        context.code_examples = truncate_list(context.code_examples, budget_per_type)
        context.documentation = truncate_list(context.documentation, budget_per_type)
        context.gotchas = truncate_list(context.gotchas, budget_per_type // 2)
        context.architectural_patterns = truncate_list(context.architectural_patterns, budget_per_type // 4)
        context.integration_points = truncate_list(context.integration_points, budget_per_type // 4)
        context.library_references = truncate_list(context.library_references, budget_per_type // 2)
        context.best_practices = truncate_list(context.best_practices, budget_per_type // 2)
        context.similar_implementations = truncate_list(context.similar_implementations, budget_per_type)
        
        return context


# Module-level convenience function
def inject_context_for_todo(todo, project_root: Optional[Path] = None, **kwargs) -> ContextPackage:
    """Convenience function for context injection"""
    if project_root is None:
        project_root = Path.cwd()
    
    injector = ContextInjector(project_root=project_root, **kwargs)
    return injector.inject_context_for_todo(todo)


if __name__ == "__main__":
    # CLI interface for testing
    import sys
    import os
    
    # Add project root to path for imports
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    
    from PRPs.scripts.todo_parser import parse_active_todos
    
    if len(sys.argv) < 2:
        print("Usage: python context_injector.py <todos_file> [todo_id]")
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
    
    print(f"Injecting context for: {todo.id} - {todo.title}")
    print(f"Domains: {', '.join(todo.domain_areas)}")
    print()
    
    injector = ContextInjector(project_root=Path.cwd())
    context = injector.inject_context_for_todo(todo)
    
    print(f"Code examples: {len(context.code_examples)}")
    print(f"Documentation: {len(context.documentation)}")
    print(f"Gotchas: {len(context.gotchas)}")
    print(f"Patterns: {len(context.architectural_patterns)}")
    print(f"Integration points: {len(context.integration_points)}")
    print(f"Libraries: {len(context.library_references)}")
    print(f"Best practices: {len(context.best_practices)}")
    print(f"Similar implementations: {len(context.similar_implementations)}")