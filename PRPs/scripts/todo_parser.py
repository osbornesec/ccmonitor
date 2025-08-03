"""
ACTIVE_TODOS.md parser for todo-to-PRP orchestrator
Comprehensive parsing of project management todos with metadata extraction
"""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TodoItem:
    """Structured todo representation from ACTIVE_TODOS.md"""
    id: str
    title: str
    description: str
    priority: str  # High/Medium/Low
    status: str    # Not Started/In Progress/Completed
    dependencies: List[str]
    estimated_effort: str
    prp_reference: Optional[str]
    domain_areas: List[str]  # Extracted from content analysis
    subtasks: List[str]
    section: str  # Priority section it belongs to


class TodoParser:
    """ACTIVE_TODOS.md parsing engine with comprehensive metadata extraction"""
    
    def __init__(self):
        self.domain_keywords = {
            'python': ['python', 'py', 'django', 'flask', 'fastapi', 'pytest'],
            'javascript': ['javascript', 'js', 'node', 'npm', 'typescript', 'ts'],
            'react': ['react', 'jsx', 'component', 'hook', 'redux'],
            'vue': ['vue', 'vuejs', 'nuxt', 'pinia'],
            'api': ['api', 'endpoint', 'rest', 'graphql', 'swagger'],
            'database': ['database', 'db', 'sql', 'postgresql', 'mongodb', 'redis'],
            'testing': ['test', 'testing', 'cypress', 'jest', 'mocha', 'pytest'],
            'infrastructure': ['docker', 'kubernetes', 'aws', 'terraform', 'ansible'],
            'frontend': ['frontend', 'ui', 'css', 'html', 'sass', 'tailwind'],
            'backend': ['backend', 'server', 'microservice', 'service'],
            'security': ['security', 'auth', 'authentication', 'authorization', 'jwt'],
            'performance': ['performance', 'optimization', 'cache', 'speed', 'memory'],
            'mobile': ['mobile', 'flutter', 'android', 'ios', 'react-native']
        }
        
        self.priority_order = {'High': 1, 'Medium': 2, 'Low': 3}
    
    def parse_active_todos(self, todos_path: Path) -> List[TodoItem]:
        """
        Parse ACTIVE_TODOS.md and extract all todo items with metadata
        
        Args:
            todos_path: Path to ACTIVE_TODOS.md file
            
        Returns:
            List of TodoItem objects with comprehensive metadata
        """
        if not todos_path.exists():
            logger.warning(f"File not found: {todos_path}")
            return []
        
        try:
            content = todos_path.read_text(encoding='utf-8')
            if not content.strip():
                logger.info("Empty todos file")
                return []
            
            return self._parse_content(content)
        
        except Exception as e:
            logger.error(f"Error parsing todos file: {e}")
            return []
    
    def _parse_content(self, content: str) -> List[TodoItem]:
        """Parse content and convert to TodoItem objects"""
        todos = []
        current_section = ""
        current_priority = ""
        
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and main title
            if not line or line.startswith('# Active Development Todos'):
                i += 1
                continue
            
            # Parse section headers (priority levels)
            section_match = re.match(r'^## (.+)', line)
            if section_match:
                current_section = section_match.group(1)
                current_priority = self._extract_priority_from_section(current_section)
                i += 1
                continue
            
            # Parse todo items
            todo_match = re.match(r'^- \[ \] \*\*([^*]+)\*\*:(.+)', line)
            if todo_match:
                todo_id = todo_match.group(1)
                title_and_desc = todo_match.group(2).strip()
                
                # Parse the todo and its metadata
                todo_item, lines_consumed = self._parse_todo_item(
                    lines[i:], todo_id, title_and_desc, 
                    current_section, current_priority
                )
                
                if todo_item:
                    todos.append(todo_item)
                
                i += lines_consumed
                continue
            
            i += 1
        
        return todos
    
    def _parse_todo_item(self, lines: List[str], todo_id: str, 
                        title_and_desc: str, section: str, priority: str) -> tuple:
        """Parse individual todo item with all metadata and subtasks"""
        
        # Extract title and description
        parts = title_and_desc.split('(Est:', 1)
        description = parts[0].strip()
        
        # Extract effort estimation
        effort_match = re.search(r'\(Est:\s*([^)]+)\)', title_and_desc)
        estimated_effort = effort_match.group(1) if effort_match else "Unknown"
        
        # Initialize todo item
        subtasks = []
        status = "Not Started"
        dependencies = []
        prp_reference = None
        
        # Extract dependencies from section header if present
        section_deps_match = re.search(r'\(Dependencies:\s*([^)]+)\)', section)
        if section_deps_match:
            deps_text = section_deps_match.group(1)
            if deps_text != "None":
                dependencies = [dep.strip() for dep in deps_text.split(',')]
        
        # Parse following lines for metadata and subtasks
        line_index = 1
        while line_index < len(lines):
            line = lines[line_index].strip()
            
            # Stop if we hit another todo or section
            if (line.startswith('- [ ] **') or 
                line.startswith('##') or 
                line.startswith('# ') or
                (line.startswith('## ') and not line.startswith('## '))) :
                break
            
            # Parse subtasks
            subtask_match = re.match(r'^- \[ \] (.+)', line)
            if subtask_match:
                subtasks.append(subtask_match.group(1))
                line_index += 1
                continue
            
            # Parse status
            status_match = re.match(r'^- Status:\s*(.+)', line)
            if status_match:
                status = status_match.group(1)
                line_index += 1
                continue
            
            # Parse individual todo dependencies (override section dependencies)
            deps_match = re.match(r'^- Dependencies:\s*(.+)', line)
            if deps_match:
                deps_text = deps_match.group(1)
                if deps_text != "None":
                    dependencies = [dep.strip() for dep in deps_text.split(',')]
                else:
                    dependencies = []
                line_index += 1
                continue
            
            # Parse PRP reference
            prp_match = re.match(r'^- PRP:\s*`?([^`]+)`?', line)
            if prp_match:
                prp_reference = prp_match.group(1)
                line_index += 1
                continue
            
            # Empty line - continue
            if not line:
                line_index += 1
                continue
            
            # If we reach here, we might be at the end of this todo
            break
        
        # Extract domain areas from content analysis
        domain_areas = self._extract_domain_areas(description, subtasks)
        
        todo_item = TodoItem(
            id=todo_id,
            title=description,
            description=description,
            priority=priority,
            status=status,
            dependencies=dependencies,
            estimated_effort=estimated_effort,
            prp_reference=prp_reference,
            domain_areas=domain_areas,
            subtasks=subtasks,
            section=section
        )
        
        return todo_item, line_index
    
    def _extract_priority_from_section(self, section: str) -> str:
        """Extract priority level from section header"""
        section_lower = section.lower()
        if 'high' in section_lower:
            return 'High'
        elif 'medium' in section_lower:
            return 'Medium' 
        elif 'low' in section_lower:
            return 'Low'
        else:
            return 'Medium'  # Default
    
    def _extract_domain_areas(self, description: str, subtasks: List[str]) -> List[str]:
        """Extract technical domain areas from content analysis"""
        domains = set()
        
        # Combine all text for analysis
        all_text = (description + ' ' + ' '.join(subtasks)).lower()
        
        # Check for domain keywords
        for domain, keywords in self.domain_keywords.items():
            for keyword in keywords:
                if keyword in all_text:
                    domains.add(domain)
                    break
        
        return list(domains) if domains else ['general']


# Module-level functions for easy import
_parser = TodoParser()

def parse_active_todos(todos_path: Path) -> List[TodoItem]:
    """Parse ACTIVE_TODOS.md file and return TodoItem list"""
    return _parser.parse_active_todos(todos_path)

def filter_todos_by_priority(todos: List[TodoItem], priority: str) -> List[TodoItem]:
    """Filter todos by priority level"""
    return [todo for todo in todos if todo.priority == priority]

def filter_todos_by_status(todos: List[TodoItem], status: str) -> List[TodoItem]:
    """Filter todos by status"""
    return [todo for todo in todos if todo.status == status]

def get_next_priority_todo(todos: List[TodoItem]) -> Optional[TodoItem]:
    """Get the next highest priority todo ready for implementation"""
    
    # Filter out completed todos
    available_todos = [todo for todo in todos if todo.status != 'Completed']
    
    if not available_todos:
        return None
    
    # Sort by priority, then check dependencies
    priority_sorted = sorted(available_todos, 
                           key=lambda t: _parser.priority_order.get(t.priority, 99))
    
    # Find first todo with satisfied dependencies
    for todo in priority_sorted:
        if validate_dependencies(todo, todos):
            return todo
    
    # If no todo has satisfied dependencies, return highest priority
    return priority_sorted[0] if priority_sorted else None

def validate_dependencies(todo: TodoItem, all_todos: List[TodoItem]) -> bool:
    """Validate that todo dependencies are satisfied"""
    if not todo.dependencies:
        return True
    
    # Create lookup of completed todos
    completed_todo_ids = {t.id for t in all_todos if t.status == 'Completed'}
    
    # Check if all dependencies are completed
    for dep in todo.dependencies:
        if dep not in completed_todo_ids:
            return False
    
    return True

def get_todos_by_section(todos: List[TodoItem], section: str) -> List[TodoItem]:
    """Get all todos from a specific section"""
    return [todo for todo in todos if todo.section == section]

def get_ready_todos(todos: List[TodoItem]) -> List[TodoItem]:
    """Get all todos that are ready for implementation (dependencies satisfied)"""
    return [todo for todo in todos 
            if todo.status != 'Completed' and validate_dependencies(todo, todos)]

def analyze_todo_domains(todos: List[TodoItem]) -> Dict[str, int]:
    """Analyze domain distribution across todos"""
    domain_counts: Dict[str, int] = {}
    
    for todo in todos:
        for domain in todo.domain_areas:
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    return domain_counts

def get_todos_requiring_prp(todos: List[TodoItem]) -> List[TodoItem]:
    """Get todos that need PRP generation (complex, no existing PRP)"""
    return [todo for todo in todos 
            if not todo.prp_reference and 
               todo.status != 'Completed' and
               ('hour' in todo.estimated_effort and 
                any(char.isdigit() for char in todo.estimated_effort))]


if __name__ == "__main__":
    # CLI interface for testing
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python todo_parser.py <path_to_active_todos.md>")
        sys.exit(1)
    
    todos_file = Path(sys.argv[1])
    todos = parse_active_todos(todos_file)
    
    print(f"Parsed {len(todos)} todos:")
    for todo in todos:
        print(f"- {todo.id}: {todo.title} [{todo.priority}] ({todo.status})")
        if todo.domain_areas:
            print(f"  Domains: {', '.join(todo.domain_areas)}")
        if todo.dependencies:
            print(f"  Dependencies: {', '.join(todo.dependencies)}")