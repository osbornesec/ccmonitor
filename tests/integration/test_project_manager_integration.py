#!/usr/bin/env python3
"""
Integration tests for project-manager-prp agent

Tests complete workflow from complex feature analysis to 
todo generation and ACTIVE_TODOS.md integration.
"""

import pytest
from pathlib import Path
import tempfile
import os

from utils.todo_parser import parse_active_todos, generate_todo_section, TodoItem, TodoSection
from utils.dependency_analyzer import analyze_dependencies, TaskNode, calculate_critical_path


class TestProjectManagerIntegration:
    """Integration tests for complete project management workflow"""
    
    def test_agent_exists_and_accessible(self):
        """
        Test Description: Verify agent is properly configured and accessible
        Expected Outcome: Agent file exists with valid configuration
        Failure Conditions: Missing agent or invalid configuration
        """
        agent_path = Path(".claude/agents/project-manager-prp.md")
        assert agent_path.exists(), "project-manager-prp agent must exist"
        
        # Verify agent has required content
        with open(agent_path, 'r') as f:
            content = f.read()
        
        assert "project-manager-prp" in content, "Agent must be named project-manager-prp"
        assert "dependency analysis" in content.lower(), "Agent must mention dependency analysis"
        assert "ACTIVE_TODOS.md" in content, "Agent must reference ACTIVE_TODOS.md format"

    def test_todo_parsing_and_generation_roundtrip(self):
        """
        Test Description: Parse and regenerate ACTIVE_TODOS.md format
        Expected Outcome: Content preserved through parse/generate cycle
        Failure Conditions: Data loss or format corruption
        """
        # Create sample todo content
        original_content = """## High Priority - Core Features (Dependencies: None)
- [ ] **PRP-001**: Implement Authentication System (Est: 4-5 hours)
  - [ ] Setup OAuth provider integration
  - [ ] Create user session management
  - [ ] Add role-based access control
  - Status: Not Started
  - Dependencies: None
  - PRP: `PRPs/001-auth-system.md`

## Medium Priority - Data Layer (Dependencies: PRP-001)
- [ ] **PRP-002**: Build Database Integration (Est: 3-4 hours)
  - [ ] Design database schema
  - [ ] Implement data access layer
  - [ ] Add migration system
  - Status: Not Started
  - Dependencies: PRP-001
  - PRP: `PRPs/002-database-layer.md`"""
        
        # Parse content
        sections = parse_active_todos(original_content)
        
        # Verify parsing
        assert len(sections) == 2
        assert "High Priority" in sections[0].title
        assert "Medium Priority" in sections[1].title
        assert len(sections[0].todos) == 1
        assert len(sections[1].todos) == 1
        
        # Verify first todo
        auth_todo = sections[0].todos[0]
        assert "Authentication System" in auth_todo.task
        assert "4-5 hours" in auth_todo.estimate
        assert len(auth_todo.subtasks) == 3
        assert "PRPs/001-auth-system.md" in auth_todo.prp
        
        # Verify second todo with dependencies
        db_todo = sections[1].todos[0]
        assert "Database Integration" in db_todo.task
        assert "PRP-001" in db_todo.dependencies

    def test_dependency_analysis_with_real_tasks(self):
        """
        Test Description: Analyze dependencies in realistic project scenario
        Expected Outcome: Correct dependency relationships and critical path
        Failure Conditions: Incorrect dependency analysis or missing relationships
        """
        # Create realistic task set
        tasks = [
            TaskNode("SETUP", "Project Setup", 1.0, [], "high"),
            TaskNode("AUTH", "Authentication System", 4.0, ["SETUP"], "high"),
            TaskNode("DATABASE", "Database Layer", 3.0, ["SETUP"], "high"),
            TaskNode("API", "REST API Layer", 5.0, ["AUTH", "DATABASE"], "high"),
            TaskNode("FRONTEND", "Frontend Application", 8.0, ["API"], "medium"),
            TaskNode("TESTING", "Test Suite", 4.0, ["API"], "medium"),
            TaskNode("DEPLOYMENT", "Production Deployment", 2.0, ["FRONTEND", "TESTING"], "low")
        ]
        
        # Analyze dependencies
        graph = analyze_dependencies(tasks)
        
        # Verify graph structure
        assert len(graph.nodes) == 7
        assert "AUTH" in graph.get_dependents("SETUP")
        assert "DATABASE" in graph.get_dependents("SETUP")
        assert "API" in graph.get_dependents("AUTH")
        assert "API" in graph.get_dependents("DATABASE")
        
        # Calculate critical path
        critical_path, duration = calculate_critical_path(graph)
        
        # Verify critical path includes longest sequence
        assert "SETUP" in critical_path
        assert "FRONTEND" in critical_path  # Longest branch
        assert "DEPLOYMENT" in critical_path
        
        # Verify total duration
        expected_duration = 1 + 4 + 5 + 8 + 2  # SETUP -> AUTH -> API -> FRONTEND -> DEPLOYMENT
        assert duration == expected_duration

    def test_active_todos_file_integration(self):
        """
        Test Description: Read, modify, and save ACTIVE_TODOS.md file
        Expected Outcome: File operations preserve format and data integrity
        Failure Conditions: File corruption or data loss
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp_file:
            # Create test ACTIVE_TODOS.md content
            test_content = """# Active Development Todos

## High Priority - Foundation (Dependencies: None)
- [ ] **PRP-001**: Setup Development Environment (Est: 2-3 hours)
  - [ ] Configure build system
  - [ ] Setup testing framework
  - [ ] Initialize documentation
  - Status: In Progress
  - Dependencies: None
  - PRP: `PRPs/001-dev-environment.md`

## Medium Priority - Core Features (Dependencies: PRP-001)
- [ ] **PRP-002**: Implement Core Logic (Est: 5-6 hours)
  - [ ] Design system architecture
  - [ ] Implement business logic
  - [ ] Add error handling
  - Status: Not Started
  - Dependencies: PRP-001
  - PRP: `PRPs/002-core-logic.md`"""
            
            tmp_file.write(test_content)
            tmp_file_path = tmp_file.name

        try:
            # Parse the file
            with open(tmp_file_path, 'r') as f:
                content = f.read()
            
            sections = parse_active_todos(content)
            
            # Verify parsing
            assert len(sections) == 2
            assert sections[0].todos[0].status == "In Progress"
            assert sections[1].todos[0].status == "Not Started"
            
            # Modify status
            sections[1].todos[0].status = "In Progress"
            
            # Add new todo to first section
            new_todo = TodoItem(
                task="Add Continuous Integration",
                priority="high",
                estimate="2-3 hours",
                dependencies=["PRP-001"],
                prp="PRPs/003-ci-setup.md"
            )
            sections[0].todos.append(new_todo)
            
            # Generate new content
            output_lines = ["# Active Development Todos", ""]
            for section in sections:
                output_lines.append(generate_todo_section(section))
                output_lines.append("")
            
            modified_content = "\n".join(output_lines)
            
            # Verify modifications
            assert "In Progress" in modified_content.count("In Progress") >= 2
            assert "Add Continuous Integration" in modified_content
            assert "PRPs/003-ci-setup.md" in modified_content
            
        finally:
            # Cleanup
            os.unlink(tmp_file_path)

    def test_complex_project_analysis_simulation(self):
        """
        Test Description: Simulate complex project analysis workflow
        Expected Outcome: Complete workflow from requirements to structured todos
        Failure Conditions: Incomplete analysis or incorrect task breakdown
        """
        # Simulate complex project requirements
        project_description = """
        Build a comprehensive e-commerce platform with the following features:
        - User authentication and profile management
        - Product catalog with search and filtering
        - Shopping cart and checkout process
        - Payment processing integration
        - Order management system
        - Admin dashboard for inventory management
        - Real-time notifications and email alerts
        - Analytics and reporting dashboard
        - Mobile-responsive design
        - Comprehensive test coverage
        """
        
        # Simulate what the project-manager-prp agent would generate
        # (In real usage, this would be generated by the agent)
        simulated_tasks = [
            TaskNode("PROJECT_SETUP", "Project Setup and Configuration", 2.0, [], "high"),
            TaskNode("AUTH_SYSTEM", "User Authentication System", 6.0, ["PROJECT_SETUP"], "high"),
            TaskNode("USER_PROFILES", "User Profile Management", 4.0, ["AUTH_SYSTEM"], "high"),
            TaskNode("PRODUCT_CATALOG", "Product Catalog System", 8.0, ["PROJECT_SETUP"], "high"),
            TaskNode("SEARCH_FILTER", "Search and Filtering", 6.0, ["PRODUCT_CATALOG"], "medium"),
            TaskNode("SHOPPING_CART", "Shopping Cart System", 5.0, ["AUTH_SYSTEM", "PRODUCT_CATALOG"], "high"),
            TaskNode("CHECKOUT", "Checkout Process", 7.0, ["SHOPPING_CART"], "high"),
            TaskNode("PAYMENT", "Payment Processing", 8.0, ["CHECKOUT"], "high"),
            TaskNode("ORDER_MGMT", "Order Management", 6.0, ["PAYMENT"], "high"),
            TaskNode("ADMIN_DASHBOARD", "Admin Dashboard", 10.0, ["ORDER_MGMT", "PRODUCT_CATALOG"], "medium"),
            TaskNode("NOTIFICATIONS", "Real-time Notifications", 5.0, ["ORDER_MGMT"], "medium"),
            TaskNode("EMAIL_ALERTS", "Email Alert System", 4.0, ["NOTIFICATIONS"], "medium"),
            TaskNode("ANALYTICS", "Analytics Dashboard", 8.0, ["ORDER_MGMT"], "low"),
            TaskNode("MOBILE_RESPONSIVE", "Mobile Responsive Design", 6.0, ["CHECKOUT", "ADMIN_DASHBOARD"], "medium"),
            TaskNode("TESTING", "Comprehensive Test Suite", 12.0, ["MOBILE_RESPONSIVE"], "high"),
            TaskNode("DEPLOYMENT", "Production Deployment", 4.0, ["TESTING"], "high")
        ]
        
        # Analyze the complex project
        graph = analyze_dependencies(simulated_tasks)
        
        # Verify comprehensive analysis
        assert len(graph.nodes) == 16
        
        # Calculate project metrics
        critical_path, total_duration = calculate_critical_path(graph)
        
        # Verify realistic project timeline
        assert total_duration > 50.0  # Complex project should take significant time
        assert "PROJECT_SETUP" in critical_path  # Should start with setup
        assert "DEPLOYMENT" in critical_path  # Should end with deployment
        
        # Verify critical path logic
        assert critical_path.index("PROJECT_SETUP") < critical_path.index("AUTH_SYSTEM")
        assert critical_path.index("CHECKOUT") < critical_path.index("PAYMENT")
        assert critical_path.index("TESTING") < critical_path.index("DEPLOYMENT")

    def test_prp_infrastructure_integration(self):
        """
        Test Description: Verify integration with PRP infrastructure
        Expected Outcome: Generated todos reference appropriate PRPs
        Failure Conditions: Missing or incorrect PRP references
        """
        # Test PRP suggestion logic
        complex_tasks = [
            ("Simple Configuration", 1.5, False),  # Should not suggest PRP
            ("Basic Component", 2.5, True),       # Should suggest PRP (>2 hours)
            ("Complex Integration", 6.0, True),   # Should definitely suggest PRP
            ("Architecture Design", 8.0, True)    # Should suggest PRP
        ]
        
        prp_suggestions = []
        for task_name, hours, should_suggest in complex_tasks:
            if hours > 2.0:  # PRP recommendation threshold
                prp_file = f"PRPs/{len(prp_suggestions)+1:03d}-{task_name.lower().replace(' ', '-')}.md"
                prp_suggestions.append(prp_file)
                assert should_suggest, f"Task '{task_name}' should suggest PRP"
            else:
                assert not should_suggest, f"Task '{task_name}' should not suggest PRP"
        
        # Verify PRP file name format
        for prp_file in prp_suggestions:
            assert prp_file.startswith("PRPs/")
            assert prp_file.endswith(".md")
            assert re.match(r'PRPs/\d{3}-[\w-]+\.md', prp_file), f"Invalid PRP format: {prp_file}"

if __name__ == "__main__":
    pytest.main([__file__, '-v'])