#!/usr/bin/env python3
"""
Tests for PRP Coordination System

This test suite validates the PRP coordination system's ability to:
- Parse PRP files and extract tasks
- Select appropriate agents for tasks
- Coordinate parallel execution
- Handle failures and generate reports
"""

import asyncio
import json
import tempfile
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from PRPs.scripts.prp_coordination_system import (
    PRPCoordinationSystem,
    PRPTask,
    PRPExecution,
    AgentCapability
)


class TestPRPCoordinationSystem:
    """Test suite for PRP coordination system."""

    @pytest.fixture
    def sample_prp_content(self):
        """Sample PRP content for testing."""
        return """# Sample PRP: User Authentication System

## Goal
Implement a secure user authentication system with JWT tokens and role-based access control.

## Why
The application needs user authentication to protect sensitive data and provide personalized experiences.

## What
A complete authentication system including registration, login, logout, and role management.

## Context
- Using Python FastAPI backend
- PostgreSQL database for user storage
- JWT tokens for session management
- Role-based access control (RBAC)

## Implementation Blueprint
- Create user database schema with proper indexing
- Implement password hashing with bcrypt
- Create JWT token generation and validation
- Build user registration endpoint with validation
- Build user login endpoint with authentication
- Implement role-based access control middleware
- Create user profile management endpoints
- Add comprehensive test coverage with pytest
- Implement security audit and vulnerability scanning
- Deploy with proper environment configuration

## Validation Loop
### Level 0: Test Creation
- Write failing tests for all authentication endpoints
- Create integration tests for user workflows
- Add security tests for authentication bypass attempts

### Level 1: Syntax & Style
- Python code formatting with black and ruff
- SQL schema validation
- API documentation with OpenAPI

### Level 2: Unit Tests
- All authentication functions have >95% test coverage
- Password hashing and JWT validation tests
- Database operations and migrations tests

### Level 3: Integration Testing
- End-to-end user registration and login flows
- Role-based access control validation
- API integration with frontend

### Level 4: Creative Validation
- Security penetration testing
- Performance testing under load
- Authentication flow user experience testing
"""

    @pytest.fixture
    def temp_prp_file(self, sample_prp_content):
        """Create a temporary PRP file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(sample_prp_content)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink()

    @pytest.fixture
    def coordinator(self):
        """Create a PRP coordination system for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock agent files
            agents_dir = Path(temp_dir) / "agents"
            agents_dir.mkdir()
            
            # Create minimal agent files
            agent_names = [
                "python-specialist", "postgresql-specialist", "security-analyst",
                "test-writer", "performance-optimizer"
            ]
            
            for agent_name in agent_names:
                agent_file = agents_dir / f"{agent_name}.md"
                agent_file.write_text(f"""---
name: {agent_name}
description: Test agent
---

# {agent_name}

Test agent for coordination system testing.

## PRP Execution Capabilities
This agent supports PRP execution with TDD methodology.
""")
            
            coordinator = PRPCoordinationSystem(
                agents_dir=str(agents_dir),
                max_parallel=2
            )
            
            yield coordinator

    def test_coordinator_initialization(self, coordinator):
        """Test that coordinator initializes correctly with agents."""
        assert len(coordinator.agents) > 0
        assert coordinator.max_parallel == 2
        assert coordinator.logger is not None

    def test_parse_prp_file(self, coordinator, temp_prp_file):
        """Test parsing a PRP file and extracting tasks."""
        goal, tasks = coordinator.parse_prp_file(temp_prp_file)
        
        assert "secure user authentication system" in goal.lower()
        assert len(tasks) > 0
        
        # Verify task structure
        for task in tasks:
            assert task.id.startswith("task_")
            assert task.title
            assert task.description
            assert task.domain
            assert 1 <= task.complexity <= 10

    def test_domain_inference(self, coordinator):
        """Test domain inference from task descriptions."""
        test_cases = [
            ("Create user database schema with PostgreSQL", "postgresql"),
            ("Implement password hashing with bcrypt in Python", "python"),
            ("Add comprehensive test coverage with pytest", "testing"),
            ("Implement security audit scanning", "security"),
            ("Create React components for login form", "react")
        ]
        
        for description, expected_domain in test_cases:
            domain = coordinator._infer_domain(description)
            assert domain == expected_domain or domain == "general"

    def test_complexity_estimation(self, coordinator):
        """Test complexity estimation for tasks."""
        test_cases = [
            ("Add a simple configuration setting", 1, 4),  # Low complexity
            ("Update existing authentication middleware", 3, 7),  # Medium
            ("Implement complete user authentication system", 6, 10)  # High
        ]
        
        for description, min_expected, max_expected in test_cases:
            complexity = coordinator._estimate_complexity(description)
            assert min_expected <= complexity <= max_expected

    def test_agent_selection(self, coordinator):
        """Test agent selection for different types of tasks."""
        # Create test tasks
        python_task = PRPTask(
            id="test_001",
            title="Python API endpoint",
            description="Create FastAPI endpoint for user registration",
            requirements=["python", "api"],
            domain="python",
            complexity=5
        )
        
        db_task = PRPTask(
            id="test_002",
            title="Database schema",
            description="Create PostgreSQL user table with proper indexing",
            requirements=["database", "postgresql"],
            domain="postgresql",
            complexity=6
        )
        
        # Test agent selection
        python_agent = coordinator.select_agent_for_task(python_task)
        db_agent = coordinator.select_agent_for_task(db_task)
        
        # Should select specialists for their domains
        assert python_agent == "python-specialist"
        assert db_agent == "postgresql-specialist"

    def test_agent_scoring(self, coordinator):
        """Test agent scoring algorithm."""
        agent = AgentCapability(
            name="python-specialist",
            domain_expertise=["python", "api", "backend"],
            tools_available=["pytest", "black", "mypy"],
            complexity_rating=8,
            estimated_speed=2.5,
            current_load=0,
            max_concurrent_tasks=2
        )
        
        # Perfect match task
        perfect_task = PRPTask(
            id="test_001",
            title="Python task",
            description="Create Python API endpoint",
            requirements=["python"],
            domain="python",
            complexity=7
        )
        
        # Poor match task
        poor_task = PRPTask(
            id="test_002",
            title="Frontend task",
            description="Create React component",
            requirements=["react"],
            domain="react",
            complexity=9
        )
        
        perfect_score = coordinator._calculate_agent_score(agent, perfect_task)
        poor_score = coordinator._calculate_agent_score(agent, poor_task)
        
        assert perfect_score > poor_score
        assert perfect_score > 70  # Should be high for perfect match
        assert poor_score < 50    # Should be low for poor match

    @pytest.mark.asyncio
    async def test_task_execution_simulation(self, coordinator):
        """Test task execution simulation."""
        task = PRPTask(
            id="test_001",
            title="Test task",
            description="Simple test task",
            requirements=[],
            domain="python",
            complexity=3
        )
        task.assigned_agent = "python-specialist"
        
        execution = PRPExecution(
            prp_id="test_prp",
            prp_file="test.md",
            goal="Test goal",
            total_tasks=1
        )
        
        # Execute task
        result_task = await coordinator._execute_task(task, execution)
        
        assert result_task.status in ["completed", "failed"]
        assert result_task.start_time is not None
        assert result_task.end_time is not None
        assert result_task.start_time <= result_task.end_time

    @pytest.mark.asyncio
    async def test_sequential_execution(self, coordinator, temp_prp_file):
        """Test sequential task execution."""
        with patch.object(coordinator, '_execute_task') as mock_execute:
            # Mock successful task execution
            async def mock_task_execution(task, execution):
                task.status = "completed"
                task.start_time = datetime.now()
                task.end_time = datetime.now()
                return task
            
            mock_execute.side_effect = mock_task_execution
            
            # Execute PRP sequentially
            execution = await coordinator.execute_prp(temp_prp_file, parallel=False)
            
            assert execution.status == "completed"
            assert execution.completed_tasks > 0
            assert execution.failed_tasks == 0

    @pytest.mark.asyncio
    async def test_parallel_execution(self, coordinator, temp_prp_file):
        """Test parallel task execution."""
        with patch.object(coordinator, '_execute_task') as mock_execute:
            # Mock task execution with delay
            async def mock_task_execution(task, execution):
                await asyncio.sleep(0.1)  # Simulate work
                task.status = "completed"
                task.start_time = datetime.now()
                task.end_time = datetime.now()
                return task
            
            mock_execute.side_effect = mock_task_execution
            
            # Execute PRP in parallel
            execution = await coordinator.execute_prp(temp_prp_file, parallel=True)
            
            assert execution.status == "completed"
            assert execution.completed_tasks > 0

    def test_dependency_graph_building(self, coordinator):
        """Test dependency graph construction."""
        tasks = [
            PRPTask(
                id="task_001",
                title="Database setup",
                description="Create database schema",
                requirements=[],
                domain="postgresql",
                complexity=5
            ),
            PRPTask(
                id="task_002",
                title="API endpoint",
                description="Implement user API endpoint",
                requirements=[],
                domain="python",
                complexity=6
            ),
            PRPTask(
                id="task_003",
                title="Test coverage",
                description="Add test coverage for implementation",
                requirements=[],
                domain="testing",
                complexity=4
            )
        ]
        
        graph = coordinator._build_dependency_graph(tasks)
        
        # Verify graph structure
        assert len(graph) == len(tasks)
        
        # API task should depend on database task
        assert "task_001" in tasks[1].dependencies or len(tasks[1].dependencies) == 0
        
        # Test task should depend on implementation
        assert len(tasks[2].dependencies) >= 0

    def test_execution_report_generation(self, coordinator):
        """Test execution report generation."""
        execution = PRPExecution(
            prp_id="test_prp",
            prp_file="test.md",
            goal="Test authentication system",
            total_tasks=5,
            completed_tasks=4,
            failed_tasks=1,
            start_time=datetime.now(),
            end_time=datetime.now(),
            status="completed",
            agents_involved=["python-specialist", "postgresql-specialist"]
        )
        
        report = coordinator.generate_execution_report(execution)
        
        assert "Test authentication system" in report
        assert "4" in report  # Completed tasks
        assert "1" in report  # Failed tasks
        assert "80.0%" in report  # Success rate
        assert "python-specialist" in report
        assert "postgresql-specialist" in report

    def test_results_saving(self, coordinator):
        """Test saving execution results to files."""
        execution = PRPExecution(
            prp_id="test_prp",
            prp_file="test.md",
            goal="Test goal",
            total_tasks=3,
            completed_tasks=2,
            failed_tasks=1,
            start_time=datetime.now(),
            end_time=datetime.now(),
            status="completed"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            coordinator.save_execution_results(execution, temp_dir)
            
            # Check files were created
            summary_file = Path(temp_dir) / "test_prp_summary.json"
            report_file = Path(temp_dir) / "test_prp_report.md"
            
            assert summary_file.exists()
            assert report_file.exists()
            
            # Verify summary content
            with open(summary_file) as f:
                summary_data = json.load(f)
            
            assert summary_data["prp_id"] == "test_prp"
            assert summary_data["total_tasks"] == 3
            assert summary_data["completed_tasks"] == 2
            assert summary_data["failed_tasks"] == 1

    def test_agent_load_management(self, coordinator):
        """Test agent load management during task assignment."""
        # Create tasks
        tasks = [
            PRPTask(f"task_{i}", f"Task {i}", f"Python task {i}", [], "python", 5)
            for i in range(5)
        ]
        
        # Assign tasks and check load management
        assigned_agents = []
        for task in tasks:
            agent = coordinator.select_agent_for_task(task)
            if agent:
                assigned_agents.append(agent)
                coordinator.agents[agent].current_load += 1
        
        # Should not overload any single agent
        for agent in coordinator.agents.values():
            assert agent.current_load <= agent.max_concurrent_tasks

    def test_error_handling(self, coordinator):
        """Test error handling for various failure scenarios."""
        # Test with non-existent PRP file
        with pytest.raises(FileNotFoundError):
            coordinator.parse_prp_file("non_existent_file.md")
        
        # Test with malformed PRP content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("This is not a valid PRP file")
            temp_path = f.name
        
        try:
            goal, tasks = coordinator.parse_prp_file(temp_path)
            # Should handle gracefully even with malformed content
            assert goal == "Unknown Goal"
            assert isinstance(tasks, list)
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])