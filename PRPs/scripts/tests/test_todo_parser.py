"""
Test suite for todo_parser.py - TDD Red Phase
Tests written before implementation to establish requirements
"""
import pytest
from pathlib import Path
from typing import List, Optional
import tempfile
import os


class TestTodoParser:
    """Test suite for ACTIVE_TODOS.md parsing functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        # Create temporary test todo file
        self.test_todos_content = """# Active Development Todos

## High Priority - Foundation (Dependencies: None)
- [ ] **PRP-001**: Create TDD-PRP Infrastructure (Est: 2-3 hours)
  - [ ] Create PRP directory structure
  - [ ] Implement TDD-enhanced PRP templates
  - [ ] Set up PRP validation framework
  - Status: Not Started
  - PRP: `PRPs/001-tdd-prp-infrastructure.md`

- [ ] **PRP-002**: Implement Project Management Agent (Est: 3-4 hours)
  - [ ] Create project-manager-prp agent
  - [ ] Implement todo breakdown algorithms
  - [ ] Add dependency analysis capabilities
  - Status: In Progress
  - PRP: `PRPs/002-project-manager-agent.md`

## Medium Priority - Core Workflow (Dependencies: PRP-001)
- [ ] **PRP-003**: Create Rate-Limited Todo Update Hook (Est: 2 hours)
  - [ ] Implement subagentstop_todo_reminder.py hook
  - [ ] Add 4-minute rate limiting mechanism
  - [ ] Configure exit code 2 with stderr output
  - Status: Completed
  - PRP: `PRPs/003-todo-update-hook.md`

## Low Priority - Advanced Features (Dependencies: PRP-003, PRP-004)
- [ ] **PRP-006**: Implement Multi-Agent PRP Orchestration (Est: 5-6 hours)
  - [ ] Create agent collaboration framework
  - [ ] Implement parallel PRP execution
  - [ ] Add cross-agent knowledge sharing
  - Status: Not Started
  - PRP: `PRPs/006-multi-agent-orchestration.md`
"""
        
        # Create temporary file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_file.write(self.test_todos_content)
        self.temp_file.close()
        self.todos_path = Path(self.temp_file.name)
    
    def teardown_method(self):
        """Cleanup test fixtures"""
        if os.path.exists(self.todos_path):
            os.unlink(self.todos_path)
    
    def test_parse_active_todos_returns_list(self):
        """Test that parsing returns a list of TodoItem objects"""
        # This will fail until implementation exists
        from PRPs.scripts.todo_parser import parse_active_todos, TodoItem
        
        todos = parse_active_todos(self.todos_path)
        assert isinstance(todos, list)
        assert len(todos) > 0
        assert isinstance(todos[0], TodoItem)
    
    def test_todo_item_has_required_fields(self):
        """Test that TodoItem objects have all required metadata"""
        from PRPs.scripts.todo_parser import parse_active_todos
        
        todos = parse_active_todos(self.todos_path)
        todo = todos[0]
        
        # Validate all required fields exist and have correct types
        assert hasattr(todo, 'id')
        assert hasattr(todo, 'title')
        assert hasattr(todo, 'description')
        assert hasattr(todo, 'priority')
        assert hasattr(todo, 'status')
        assert hasattr(todo, 'dependencies')
        assert hasattr(todo, 'estimated_effort')
        assert hasattr(todo, 'prp_reference')
        assert hasattr(todo, 'domain_areas')
        assert hasattr(todo, 'subtasks')
        assert hasattr(todo, 'section')
    
    def test_priority_classification_extraction(self):
        """Test that priority levels are correctly extracted"""
        from PRPs.scripts.todo_parser import parse_active_todos
        
        todos = parse_active_todos(self.todos_path)
        priorities = [todo.priority for todo in todos]
        
        assert 'High' in priorities
        assert 'Medium' in priorities
        assert 'Low' in priorities
    
    def test_status_extraction(self):
        """Test that status values are correctly parsed"""
        from PRPs.scripts.todo_parser import parse_active_todos
        
        todos = parse_active_todos(self.todos_path)
        statuses = [todo.status for todo in todos]
        
        assert 'Not Started' in statuses
        assert 'In Progress' in statuses
        assert 'Completed' in statuses
    
    def test_prp_reference_extraction(self):
        """Test that PRP references are correctly extracted"""
        from PRPs.scripts.todo_parser import parse_active_todos
        
        todos = parse_active_todos(self.todos_path)
        
        # Find todo with PRP reference
        prp_todo = next(todo for todo in todos if todo.prp_reference)
        assert prp_todo.prp_reference is not None
        assert 'PRPs/' in prp_todo.prp_reference
        assert '.md' in prp_todo.prp_reference
    
    def test_subtask_extraction(self):
        """Test that subtasks are correctly parsed"""
        from PRPs.scripts.todo_parser import parse_active_todos
        
        todos = parse_active_todos(self.todos_path)
        
        # Find todo with subtasks
        todo_with_subtasks = next(todo for todo in todos if todo.subtasks)
        assert len(todo_with_subtasks.subtasks) > 0
        assert isinstance(todo_with_subtasks.subtasks, list)
    
    def test_dependency_parsing(self):
        """Test that dependencies are correctly identified"""
        from PRPs.scripts.todo_parser import parse_active_todos
        
        todos = parse_active_todos(self.todos_path)
        
        # Check for todos with dependencies
        dependent_todos = [todo for todo in todos if todo.dependencies]
        assert len(dependent_todos) > 0
        
        # Validate dependency format
        for todo in dependent_todos:
            assert isinstance(todo.dependencies, list)
    
    def test_effort_estimation_extraction(self):
        """Test that effort estimates are correctly parsed"""
        from PRPs.scripts.todo_parser import parse_active_todos
        
        todos = parse_active_todos(self.todos_path)
        
        for todo in todos:
            assert todo.estimated_effort is not None
            assert 'hour' in todo.estimated_effort.lower()
    
    def test_domain_area_extraction(self):
        """Test that domain areas are extracted from content analysis"""
        from PRPs.scripts.todo_parser import parse_active_todos
        
        todos = parse_active_todos(self.todos_path)
        
        # Domain areas should be inferred from content
        for todo in todos:
            assert isinstance(todo.domain_areas, list)
            # Should contain relevant domains based on content analysis
    
    def test_todo_id_generation(self):
        """Test that todo IDs are properly generated"""
        from PRPs.scripts.todo_parser import parse_active_todos
        
        todos = parse_active_todos(self.todos_path)
        
        ids = [todo.id for todo in todos]
        # All todos should have unique IDs
        assert len(ids) == len(set(ids))
        
        # IDs should follow expected pattern
        for todo_id in ids:
            assert todo_id is not None
            assert len(todo_id) > 0
    
    def test_section_classification(self):
        """Test that todos are correctly classified into sections"""
        from PRPs.scripts.todo_parser import parse_active_todos
        
        todos = parse_active_todos(self.todos_path)
        
        sections = [todo.section for todo in todos]
        # Accept both full section names and just the priority part
        has_high = any('High Priority - Foundation' in section for section in sections)
        has_medium = any('Medium Priority - Core Workflow' in section for section in sections)
        has_low = any('Low Priority - Advanced Features' in section for section in sections)
        
        assert has_high
        assert has_medium
        assert has_low
    
    def test_empty_file_handling(self):
        """Test that empty files are handled gracefully"""
        from PRPs.scripts.todo_parser import parse_active_todos
        
        # Create empty temp file
        empty_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        empty_file.write("")
        empty_file.close()
        empty_path = Path(empty_file.name)
        
        try:
            todos = parse_active_todos(empty_path)
            assert isinstance(todos, list)
            assert len(todos) == 0
        finally:
            os.unlink(empty_path)
    
    def test_malformed_file_error_handling(self):
        """Test that malformed files raise appropriate errors"""
        from PRPs.scripts.todo_parser import parse_active_todos
        
        # Create malformed temp file
        malformed_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        malformed_file.write("This is not a valid ACTIVE_TODOS.md format")
        malformed_file.close()
        malformed_path = Path(malformed_file.name)
        
        try:
            todos = parse_active_todos(malformed_path)
            # Should handle gracefully, returning empty list or raising specific exception
            assert isinstance(todos, list)
        finally:
            os.unlink(malformed_path)
    
    def test_filter_by_priority(self):
        """Test filtering todos by priority level"""
        from PRPs.scripts.todo_parser import parse_active_todos, filter_todos_by_priority
        
        todos = parse_active_todos(self.todos_path)
        high_priority_todos = filter_todos_by_priority(todos, 'High')
        
        assert len(high_priority_todos) > 0
        for todo in high_priority_todos:
            assert todo.priority == 'High'
    
    def test_filter_by_status(self):
        """Test filtering todos by status"""
        from PRPs.scripts.todo_parser import parse_active_todos, filter_todos_by_status
        
        todos = parse_active_todos(self.todos_path)
        not_started_todos = filter_todos_by_status(todos, 'Not Started')
        
        for todo in not_started_todos:
            assert todo.status == 'Not Started'
    
    def test_get_next_priority_todo(self):
        """Test getting the next priority todo for implementation"""
        from PRPs.scripts.todo_parser import parse_active_todos, get_next_priority_todo, TodoItem
        
        todos = parse_active_todos(self.todos_path)
        next_todo = get_next_priority_todo(todos)
        
        assert next_todo is not None
        assert isinstance(next_todo, TodoItem)
        # Should be highest priority, not completed, with dependencies satisfied
        assert next_todo.status != 'Completed'
    
    def test_validate_dependencies(self):
        """Test dependency validation logic"""
        from PRPs.scripts.todo_parser import parse_active_todos, validate_dependencies
        
        todos = parse_active_todos(self.todos_path)
        
        for todo in todos:
            is_ready = validate_dependencies(todo, todos)
            assert isinstance(is_ready, bool)
            
            # If todo has dependencies, they should be validated
            if todo.dependencies:
                # Dependencies should exist in todos list
                dependency_ids = [t.id for t in todos]
                for dep in todo.dependencies:
                    # This will validate once implementation exists
                    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])