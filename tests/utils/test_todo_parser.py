#!/usr/bin/env python3
"""
Test suite for todo parsing utilities

Tests ACTIVE_TODOS.md format parsing and generation with comprehensive
validation of format compatibility and edge cases.
"""

import pytest
from pathlib import Path
from typing import List, Dict, Any
import textwrap

# Import will fail initially (RED phase) - utils don't exist yet
try:
    from utils.todo_parser import (
        parse_active_todos,
        generate_todo_section, 
        validate_todo_format,
        TodoItem,
        TodoSection
    )
except ImportError:
    # Define placeholder classes for RED phase testing
    class TodoItem:
        def __init__(self, task: str, priority: str, estimate: str, dependencies: List[str] = None, prp: str = None):
            self.task = task
            self.priority = priority  
            self.estimate = estimate
            self.dependencies = dependencies or []
            self.prp = prp
    
    class TodoSection:
        def __init__(self, title: str, priority: str, todos: List[TodoItem]):
            self.title = title
            self.priority = priority
            self.todos = todos
    
    def parse_active_todos(content: str) -> List[TodoSection]:
        raise NotImplementedError("parse_active_todos not implemented yet")
    
    def generate_todo_section(section: TodoSection) -> str:
        raise NotImplementedError("generate_todo_section not implemented yet")
    
    def validate_todo_format(todo_content: str) -> bool:
        raise NotImplementedError("validate_todo_format not implemented yet")

class TestTodoFormatParsing:
    """Test suite for ACTIVE_TODOS.md format parsing"""
    
    def test_parse_basic_todo_section(self):
        """
        Test Description: Parse basic todo section with standard format
        Expected Outcome: TodoSection object with correct todos and metadata
        Failure Conditions: Parsing errors or missing data
        """
        # Arrange: Basic todo section content
        content = textwrap.dedent("""
        ## High Priority - Foundation (Dependencies: None)
        - [ ] **PRP-001**: Create TDD-PRP Infrastructure (Est: 2-3 hours)
          - [ ] Create PRP directory structure
          - [ ] Implement TDD-enhanced PRP templates
          - [ ] Set up PRP validation framework
          - Status: Not Started
          - PRP: `PRPs/001-tdd-prp-infrastructure.md`
        """).strip()
        
        # Act: Parse content (GREEN phase - now implemented)
        sections = parse_active_todos(content)
            
        # GREEN phase assertions now enabled
        assert len(sections) == 1
        assert "High Priority - Foundation" in sections[0].title
        assert len(sections[0].todos) == 1
        assert "Create TDD-PRP Infrastructure" in sections[0].todos[0].task

    def test_parse_todo_with_dependencies(self):
        """
        Test Description: Parse todo section with dependency relationships
        Expected Outcome: Dependencies correctly extracted and linked
        Failure Conditions: Missing or incorrect dependency parsing
        """
        # Arrange: Todo with explicit dependencies
        content = textwrap.dedent("""
        ## Medium Priority - Core Workflow (Dependencies: PRP-001)
        - [ ] **PRP-003**: Create Rate-Limited Todo Update Hook (Est: 2 hours)
          - [ ] Implement subagentstop_todo_reminder.py hook
          - [ ] Add 4-minute rate limiting mechanism
          - [ ] Configure exit code 2 with stderr output
          - Status: Not Started
          - Dependencies: PRP-001
          - PRP: `PRPs/003-todo-update-hook.md`
        """).strip()
        
        # Act: Parse content (will fail in RED phase)  
        with pytest.raises(NotImplementedError):
            sections = parse_active_todos(content)
            
        # GREEN phase assertions:
        # assert sections[0].todos[0].dependencies == ["PRP-001"]

    def test_parse_multiple_priority_sections(self):
        """
        Test Description: Parse multiple sections with different priorities
        Expected Outcome: All sections parsed with correct priority levels
        Failure Conditions: Missing sections or incorrect priority assignment
        """
        # Arrange: Multiple priority sections
        content = textwrap.dedent("""
        ## High Priority - Foundation (Dependencies: None)
        - [ ] **PRP-001**: Create Infrastructure (Est: 2-3 hours)
          - Status: Not Started
          
        ## Medium Priority - Core Features (Dependencies: PRP-001)
        - [ ] **PRP-002**: Build Agent System (Est: 3-4 hours)
          - Status: Not Started
          - Dependencies: PRP-001
          
        ## Low Priority - Enhancements (Dependencies: PRP-002)
        - [ ] **PRP-003**: Add Advanced Features (Est: 1-2 hours)
          - Status: Not Started
          - Dependencies: PRP-002
        """).strip()
        
        # Act: Parse content (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            sections = parse_active_todos(content)
        
        # GREEN phase assertions:
        # assert len(sections) == 3
        # priorities = [section.priority for section in sections]
        # assert "High" in priorities[0] and "Medium" in priorities[1] and "Low" in priorities[2]

    def test_parse_todo_with_prp_reference(self):
        """
        Test Description: Parse todo with PRP file reference
        Expected Outcome: PRP reference correctly extracted and validated
        Failure Conditions: Missing or incorrect PRP reference format
        """
        # Arrange: Todo with PRP reference
        content = textwrap.dedent("""
        ## High Priority - Implementation
        - [ ] **PRP-005**: Complex Feature Implementation (Est: 5-6 hours)
          - [ ] Design system architecture
          - [ ] Implement core functionality  
          - [ ] Add comprehensive testing
          - Status: In Progress
          - PRP: `PRPs/005-complex-feature.md`
        """).strip()
        
        # Act: Parse content (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            sections = parse_active_todos(content)
        
        # GREEN phase assertions:
        # assert sections[0].todos[0].prp == "PRPs/005-complex-feature.md"

class TestTodoFormatGeneration:
    """Test suite for ACTIVE_TODOS.md format generation"""
    
    def test_generate_basic_todo_section(self):
        """
        Test Description: Generate properly formatted todo section
        Expected Outcome: String matches ACTIVE_TODOS.md format exactly
        Failure Conditions: Format deviations or missing elements
        """
        # Arrange: TodoSection object
        todo_item = TodoItem(
            task="Create Authentication System",
            priority="high", 
            estimate="3-4 hours",
            dependencies=["PRP-001"],
            prp="PRPs/002-auth-system.md"
        )
        section = TodoSection("High Priority - Core Features", "high", [todo_item])
        
        # Act: Generate formatted section (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            formatted = generate_todo_section(section)
        
        # GREEN phase assertions:
        # assert "## High Priority - Core Features" in formatted
        # assert "**PRP-002**:" in formatted  
        # assert "(Est: 3-4 hours)" in formatted
        # assert "Dependencies: PRP-001" in formatted
        # assert "PRP: `PRPs/002-auth-system.md`" in formatted

    def test_generate_todo_without_dependencies(self):
        """
        Test Description: Generate todo section without dependencies
        Expected Outcome: Dependencies line omitted or shows "None"
        Failure Conditions: Incorrect dependency handling
        """
        # Arrange: TodoItem without dependencies
        todo_item = TodoItem(
            task="Setup Development Environment",
            priority="high",
            estimate="1-2 hours"
        )
        section = TodoSection("High Priority - Setup", "high", [todo_item])
        
        # Act: Generate formatted section (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            formatted = generate_todo_section(section)
        
        # GREEN phase assertions:
        # assert "Dependencies: None" in formatted or "Dependencies:" not in formatted

    def test_generate_multiple_todos_in_section(self):
        """
        Test Description: Generate section with multiple todo items
        Expected Outcome: All todos properly formatted and ordered
        Failure Conditions: Missing todos or incorrect ordering
        """
        # Arrange: Multiple TodoItems
        todos = [
            TodoItem("Task 1", "high", "2 hours", prp="PRPs/001-task1.md"),
            TodoItem("Task 2", "high", "3 hours", dependencies=["PRP-001"], prp="PRPs/002-task2.md"),
            TodoItem("Task 3", "high", "1 hour", dependencies=["PRP-001", "PRP-002"])
        ]
        section = TodoSection("High Priority - Multiple Tasks", "high", todos)
        
        # Act: Generate formatted section (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            formatted = generate_todo_section(section)
        
        # GREEN phase assertions:
        # assert "**PRP-001**:" in formatted
        # assert "**PRP-002**:" in formatted  
        # assert "**PRP-003**:" in formatted
        
class TestTodoFormatValidation:
    """Test suite for todo format validation and compliance"""
    
    def test_validate_correct_todo_format(self):
        """
        Test Description: Validate correctly formatted todo content
        Expected Outcome: Validation passes without errors
        Failure Conditions: Valid format rejected
        """
        # Arrange: Correctly formatted todo content
        valid_content = textwrap.dedent("""
        ## High Priority - Foundation (Dependencies: None)
        - [ ] **PRP-001**: Create TDD-PRP Infrastructure (Est: 2-3 hours) 
          - [ ] Create PRP directory structure
          - [ ] Implement TDD-enhanced PRP templates
          - Status: Not Started
          - PRP: `PRPs/001-tdd-prp-infrastructure.md`
        """).strip()
        
        # Act: Validate format (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            is_valid = validate_todo_format(valid_content)
        
        # GREEN phase assertions:
        # assert is_valid == True

    def test_validate_incorrect_todo_format(self):
        """
        Test Description: Detect incorrectly formatted todo content
        Expected Outcome: Validation fails with specific error messages
        Failure Conditions: Invalid format accepted
        """
        # Arrange: Incorrectly formatted todo content (missing required elements)
        invalid_content = textwrap.dedent("""
        ## Some Section
        - [ ] Task without estimate or PRP reference
          - Status: Unknown
        """).strip()
        
        # Act: Validate format (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            is_valid = validate_todo_format(invalid_content)
        
        # GREEN phase assertions:
        # assert is_valid == False

    def test_validate_priority_levels(self):
        """
        Test Description: Validate priority level compliance
        Expected Outcome: Only high/medium/low priorities accepted
        Failure Conditions: Invalid priority levels accepted
        """
        # Arrange: Content with invalid priority
        invalid_priority_content = textwrap.dedent("""
        ## Super Critical Priority - Emergency Tasks
        - [ ] **PRP-001**: Emergency Fix (Est: 1 hour)
          - Status: Not Started
        """).strip()
        
        # Act: Validate format (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            is_valid = validate_todo_format(invalid_priority_content)
        
        # GREEN phase assertions:
        # assert is_valid == False  # Should reject non-standard priority levels

class TestTodoFormatEdgeCases:
    """Test suite for edge cases and error handling"""
    
    def test_parse_empty_todo_file(self):
        """
        Test Description: Handle empty ACTIVE_TODOS.md file gracefully
        Expected Outcome: Empty list returned without errors
        Failure Conditions: Parsing errors on empty input
        """
        # Arrange: Empty content
        empty_content = ""
        
        # Act: Parse empty content (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            sections = parse_active_todos(empty_content)
        
        # GREEN phase assertions:
        # assert sections == []

    def test_parse_malformed_todo_content(self):
        """
        Test Description: Handle malformed todo content gracefully
        Expected Outcome: Appropriate error handling or partial parsing
        Failure Conditions: Unhandled exceptions or crashes
        """
        # Arrange: Malformed content with mixed formatting
        malformed_content = textwrap.dedent("""
        ## High Priority
        - [ ] **PRP-001**: Task 1 (Est: 2 hours
          - Missing closing parenthesis
          - Status: Started
        
        ## Medium Priority - Missing Dependencies Info
        - [ ] Task without PRP reference
          - Status: Unknown
        """).strip()
        
        # Act: Parse malformed content (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            sections = parse_active_todos(malformed_content)
        
        # GREEN phase assertions will validate error handling

    def test_generate_todo_with_special_characters(self):
        """
        Test Description: Handle special characters in todo descriptions
        Expected Outcome: Special characters properly escaped or handled
        Failure Conditions: Formatting corruption or invalid output
        """
        # Arrange: TodoItem with special characters
        special_todo = TodoItem(
            task="Implement OAuth 2.0 & JWT authentication with rate-limiting (>100 req/min)",
            priority="high",
            estimate="4-5 hours",
            prp="PRPs/003-oauth-jwt-system.md"
        )
        section = TodoSection("Special Characters Test", "high", [special_todo])
        
        # Act: Generate formatted section (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            formatted = generate_todo_section(section)
        
        # GREEN phase assertions will validate special character handling

if __name__ == "__main__":
    # Run tests to demonstrate RED phase failures
    pytest.main([__file__, '-v', '--tb=short'])