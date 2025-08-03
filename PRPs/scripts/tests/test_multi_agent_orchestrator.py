#!/usr/bin/env python3
"""
Tests for Multi-Agent Orchestrator

This test suite validates the advanced orchestration capabilities including:
- Intelligent agent assignment and load balancing
- Real-time performance monitoring and optimization
- Dynamic task reallocation and dependency resolution
- Cross-agent knowledge sharing and collaboration
"""

import asyncio
import json
import tempfile
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from PRPs.scripts.multi_agent_orchestrator import (
    MultiAgentOrchestrator,
    OrchestrationExecution,
    AgentPerformanceMetrics,
    AgentStatus,
    TaskPriority,
    TaskDependency,
    AgentCommunicationMessage
)
from PRPs.scripts.prp_coordination_system import PRPTask


class TestMultiAgentOrchestrator:
    """Test suite for multi-agent orchestrator."""

    @pytest.fixture
    def sample_complex_prp_content(self):
        """Complex PRP content for advanced orchestration testing."""
        return """# Complex E-commerce Platform PRP

## Goal
Build a complete e-commerce platform with microservices architecture, real-time features, and comprehensive testing.

## Why
Demonstrate advanced multi-agent orchestration capabilities with complex interdependencies.

## What
A full-stack e-commerce platform with authentication, product management, shopping cart, payment processing, and analytics.

## Context
- Microservices architecture with Docker and Kubernetes
- PostgreSQL for primary data, Redis for caching
- React frontend with real-time WebSocket features
- Payment integration with Stripe
- Comprehensive security and performance testing

## Implementation Blueprint
- Set up PostgreSQL database with product and user schemas
- Create authentication service with JWT tokens and role-based access
- Implement product catalog service with search and filtering
- Build shopping cart service with Redis for session management
- Create payment processing service with Stripe integration
- Develop order management service with workflow orchestration
- Build user profile service with preferences and history
- Create inventory management service with real-time updates
- Implement notification service with WebSocket real-time updates
- Build analytics service with data aggregation and reporting
- Create React frontend with responsive design and real-time features
- Implement comprehensive API testing with contract validation
- Add security testing with penetration testing and vulnerability scanning
- Create performance testing with load testing and optimization
- Set up monitoring and logging with centralized observability
- Deploy with Kubernetes and implement CI/CD pipeline
- Add end-to-end testing with user journey validation
- Implement data backup and disaster recovery procedures

## Validation Loop
### Level 0: Test Creation
- Comprehensive unit tests for all services
- Integration tests for service communication
- End-to-end tests for complete user workflows
- Performance tests for scalability validation

### Level 1: Syntax & Style
- Code formatting and linting for all services
- API documentation with OpenAPI specifications
- Database schema validation and migrations
- Security code scanning and vulnerability assessment

### Level 2: Unit Tests
- >95% test coverage for all microservices
- Database operations and transaction testing
- Authentication and authorization validation
- Payment processing and error handling

### Level 3: Integration Testing
- Service-to-service communication validation
- Database integration and data consistency
- External API integration (Stripe, notifications)
- Real-time WebSocket functionality

### Level 4: Creative Validation
- Chaos engineering with service failure simulation
- Performance testing under realistic load
- Security penetration testing
- User experience and accessibility testing
"""

    @pytest.fixture
    def temp_complex_prp_file(self, sample_complex_prp_content):
        """Create a temporary complex PRP file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(sample_complex_prp_content)
            temp_path = f.name
        
        yield temp_path
        
        Path(temp_path).unlink()

    @pytest.fixture
    def orchestrator(self):
        """Create a multi-agent orchestrator for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create comprehensive agent files
            agents_dir = Path(temp_dir) / "agents"
            agents_dir.mkdir()
            
            # Create realistic agent set
            agent_configs = {
                "postgresql-specialist": "PostgreSQL specialist",
                "python-specialist": "Python specialist", 
                "react-specialist": "React specialist",
                "security-analyst": "Security specialist",
                "performance-optimizer": "Performance specialist",
                "docker-kubernetes-specialist": "DevOps specialist",
                "test-writer": "Testing specialist",
                "api-design-specialist": "API specialist"
            }
            
            for agent_name, description in agent_configs.items():
                agent_file = agents_dir / f"{agent_name}.md"
                agent_file.write_text(f"""---
name: {agent_name}
description: {description}
---

# {agent_name}

{description} for orchestration testing.

## PRP Execution Capabilities
This agent supports PRP execution with TDD methodology and autonomous workflow integration.

### TDD Methodology Integration
- Red Phase: Create failing tests
- Green Phase: Implement minimal functionality
- Refactor Phase: Optimize and improve

### Autonomous Workflow Integration
- ACTIVE_TODOS.md integration
- Multi-agent coordination
- Error handling and recovery
""")
            
            orchestrator = MultiAgentOrchestrator(
                agents_dir=str(agents_dir),
                max_agents=6
            )
            
            yield orchestrator

    def test_orchestrator_initialization(self, orchestrator):
        """Test advanced orchestrator initialization."""
        assert len(orchestrator.base_coordinator.agents) > 0
        assert orchestrator.max_agents == 6
        assert len(orchestrator.agent_performance) == len(orchestrator.base_coordinator.agents)
        assert len(orchestrator.agent_status) == len(orchestrator.base_coordinator.agents)
        
        # Check that all agents start with idle status
        for status in orchestrator.agent_status.values():
            assert status == AgentStatus.IDLE

    def test_performance_metrics_initialization(self, orchestrator):
        """Test agent performance metrics initialization."""
        for agent_name in orchestrator.base_coordinator.agents.keys():
            performance = orchestrator.agent_performance[agent_name]
            assert performance.agent_name == agent_name
            assert performance.tasks_completed == 0
            assert performance.tasks_failed == 0
            assert performance.success_rate == 1.0
            assert performance.current_load == 0

    @pytest.mark.asyncio
    async def test_project_complexity_analysis(self, orchestrator, temp_complex_prp_file):
        """Test project complexity analysis."""
        execution = OrchestrationExecution(
            execution_id="test_001",
            project_name="test_project",
            prp_files=[temp_complex_prp_file]
        )
        
        await orchestrator._analyze_project_complexity(
            execution, "/tmp", [temp_complex_prp_file]
        )
        
        assert "complexity_analysis" in execution.knowledge_graph
        complexity = execution.knowledge_graph["complexity_analysis"]
        
        assert complexity["total_prp_files"] == 1
        assert complexity["estimated_tasks"] > 10  # Complex project should have many tasks
        assert complexity["complexity_score"] > 0
        assert complexity["recommended_agents"] > 2

    @pytest.mark.asyncio
    async def test_task_decomposition(self, orchestrator, temp_complex_prp_file):
        """Test intelligent task decomposition."""
        execution = OrchestrationExecution(
            execution_id="test_002",
            project_name="test_project",
            prp_files=[temp_complex_prp_file]
        )
        
        tasks = await orchestrator._decompose_project_tasks(
            execution, [temp_complex_prp_file]
        )
        
        assert len(tasks) > 15  # Complex project should generate many tasks
        
        # Verify task enhancement
        for task in tasks:
            assert hasattr(task, 'priority')
            assert hasattr(task, 'estimated_duration')
            assert hasattr(task, 'resource_requirements')
            assert task.id.startswith("task_")
            assert task.estimated_duration > 0

    def test_task_priority_calculation(self, orchestrator):
        """Test task priority calculation logic."""
        # Critical priority tasks
        critical_task = PRPTask(
            id="test_001",
            title="Setup database",
            description="Initialize PostgreSQL database setup",
            requirements=[],
            domain="database",
            complexity=5
        )
        priority = orchestrator._calculate_task_priority(critical_task)
        assert priority in [TaskPriority.CRITICAL, TaskPriority.HIGH]
        
        # Security task should be high priority
        security_task = PRPTask(
            id="test_002",
            title="Authentication",
            description="Implement security authentication system",
            requirements=[],
            domain="security",
            complexity=6
        )
        priority = orchestrator._calculate_task_priority(security_task)
        assert priority == TaskPriority.HIGH
        
        # Regular task should be medium/low priority
        regular_task = PRPTask(
            id="test_003",
            title="UI component",
            description="Create basic UI component",
            requirements=[],
            domain="frontend",
            complexity=3
        )
        priority = orchestrator._calculate_task_priority(regular_task)
        assert priority in [TaskPriority.MEDIUM, TaskPriority.LOW]

    def test_duration_estimation(self, orchestrator):
        """Test task duration estimation."""
        # Simple task
        simple_task = PRPTask(
            id="test_001",
            title="Simple task",
            description="Simple implementation task",
            requirements=[],
            domain="general",
            complexity=2
        )
        duration = orchestrator._estimate_task_duration(simple_task)
        assert 0.25 <= duration <= 1.0  # Should be relatively quick
        
        # Security task (should take longer)
        security_task = PRPTask(
            id="test_002",
            title="Security task",
            description="Implement security measures",
            requirements=[],
            domain="security",
            complexity=7
        )
        duration = orchestrator._estimate_task_duration(security_task)
        assert duration > 1.5  # Security tasks should take longer

    @pytest.mark.asyncio
    async def test_dependency_resolution(self, orchestrator):
        """Test advanced dependency resolution."""
        # Create tasks with implicit dependencies
        tasks = [
            PRPTask("task_001", "Database setup", "Set up PostgreSQL database", [], "postgresql", 6),
            PRPTask("task_002", "API endpoint", "Create user API endpoint", [], "python", 5),
            PRPTask("task_003", "Authentication", "Implement auth system", [], "security", 7),
            PRPTask("task_004", "Protected route", "Create authenticated user route", [], "python", 5),
            PRPTask("task_005", "Test coverage", "Add comprehensive test coverage", [], "testing", 4)
        ]
        
        execution = OrchestrationExecution(
            execution_id="test_003",
            project_name="test_project",
            prp_files=[]
        )
        
        await orchestrator._resolve_task_dependencies(execution, tasks)
        
        # Verify dependencies were created
        assert len(orchestrator.task_dependencies) > 0
        
        # API should depend on database
        api_task = next(t for t in tasks if "API" in t.title)
        db_task = next(t for t in tasks if "Database" in t.title)
        assert db_task.id in api_task.dependencies or len(api_task.dependencies) == 0
        
        # Protected route should depend on authentication
        protected_task = next(t for t in tasks if "Protected" in t.title)
        auth_task = next(t for t in tasks if "Authentication" in t.title)
        assert auth_task.id in protected_task.dependencies

    def test_circular_dependency_detection(self, orchestrator):
        """Test circular dependency detection."""
        # Create artificial dependency graph with cycles
        dependency_graph = {
            "task_001": [TaskDependency("task_001", "task_002", "sequential")],
            "task_002": [TaskDependency("task_002", "task_003", "sequential")],
            "task_003": [TaskDependency("task_003", "task_001", "sequential")]
        }
        
        cycles = orchestrator._detect_circular_dependencies(dependency_graph)
        assert len(cycles) > 0
        assert "task_001" in cycles[0]
        assert "task_002" in cycles[0]
        assert "task_003" in cycles[0]

    @pytest.mark.asyncio
    async def test_intelligent_agent_assignment(self, orchestrator):
        """Test intelligent agent assignment."""
        tasks = [
            PRPTask("task_001", "Database task", "PostgreSQL optimization", [], "postgresql", 6),
            PRPTask("task_002", "Python API", "FastAPI endpoint", [], "python", 5),
            PRPTask("task_003", "React component", "Frontend component", [], "react", 4),
            PRPTask("task_004", "Security audit", "Security testing", [], "security", 8)
        ]
        
        execution = OrchestrationExecution(
            execution_id="test_004",
            project_name="test_project",
            prp_files=[]
        )
        
        await orchestrator._assign_agents_intelligently(execution, tasks)
        
        # Verify assignments
        db_task = next(t for t in tasks if "Database" in t.title)
        python_task = next(t for t in tasks if "Python" in t.title)
        react_task = next(t for t in tasks if "React" in t.title)
        security_task = next(t for t in tasks if "Security" in t.title)
        
        assert db_task.assigned_agent == "postgresql-specialist"
        assert python_task.assigned_agent == "python-specialist"
        assert react_task.assigned_agent == "react-specialist"
        assert security_task.assigned_agent == "security-analyst"
        
        # Verify execution metrics updated
        assert execution.total_agents > 0
        assert "agent_assignments" in execution.knowledge_graph

    def test_comprehensive_agent_scoring(self, orchestrator):
        """Test comprehensive agent scoring algorithm."""
        # Create a task
        task = PRPTask(
            id="test_001",
            title="Python task",
            description="Python development task",
            requirements=["python"],
            domain="python",
            complexity=5
        )
        task.priority = TaskPriority.HIGH
        
        # Get agent capability
        agent_capability = orchestrator.base_coordinator.agents["python-specialist"]
        
        # Test scoring with different performance states
        # High performance agent
        orchestrator.agent_performance["python-specialist"].success_rate = 0.95
        orchestrator.agent_performance["python-specialist"].efficiency_rating = 1.3
        orchestrator.agent_performance["python-specialist"].specialization_score = 0.9
        
        high_score = orchestrator._calculate_comprehensive_agent_score(
            agent_capability, task, "python-specialist"
        )
        
        # Low performance agent
        orchestrator.agent_performance["python-specialist"].success_rate = 0.6
        orchestrator.agent_performance["python-specialist"].efficiency_rating = 0.8
        orchestrator.agent_performance["python-specialist"].specialization_score = 0.3
        
        low_score = orchestrator._calculate_comprehensive_agent_score(
            agent_capability, task, "python-specialist"
        )
        
        assert high_score > low_score

    def test_assignment_reasoning(self, orchestrator):
        """Test assignment reasoning generation."""
        task = PRPTask("test_001", "Test task", "Test task description", [], "python", 5)
        
        # Set high performance metrics
        performance = orchestrator.agent_performance["python-specialist"]
        performance.success_rate = 0.95
        performance.efficiency_rating = 1.25
        performance.current_load = 0
        performance.specialization_score = 0.85
        
        reasoning = orchestrator._get_assignment_reasoning(task, "python-specialist")
        
        assert "high success rate" in reasoning
        assert "above-average efficiency" in reasoning
        assert "currently available" in reasoning
        assert "domain expertise match" in reasoning

    @pytest.mark.asyncio
    async def test_task_execution_monitoring(self, orchestrator):
        """Test monitored task execution."""
        task = PRPTask(
            id="test_001",
            title="Test task",
            description="Monitored execution test",
            requirements=[],
            domain="python",
            complexity=3
        )
        task.assigned_agent = "python-specialist"
        task.estimated_duration = 0.5  # 30 minutes
        
        execution = OrchestrationExecution(
            execution_id="test_005",
            project_name="test_project",
            prp_files=[]
        )
        
        # Mock the base task execution
        with patch.object(orchestrator.base_coordinator, '_execute_task') as mock_execute:
            async def mock_task_execution(task, execution):
                await asyncio.sleep(0.1)  # Simulate work
                task.status = "completed"
                task.start_time = datetime.now()
                task.end_time = datetime.now()
                return task
            
            mock_execute.side_effect = mock_task_execution
            
            result_task = await orchestrator._execute_monitored_task(task, execution)
            
            assert result_task.status == "completed"
            
            # Verify performance metrics were updated
            performance = orchestrator.agent_performance["python-specialist"]
            assert performance.tasks_completed > 0
            assert performance.average_execution_time > 0

    def test_performance_recording(self, orchestrator):
        """Test task execution performance recording."""
        task = PRPTask("test_001", "Test task", "Test description", [], "python", 5)
        task.assigned_agent = "python-specialist"
        task.estimated_duration = 1.0  # 1 hour
        
        # Record successful execution
        orchestrator._record_task_execution(task, 1800, True)  # 30 minutes
        
        performance = orchestrator.agent_performance["python-specialist"]
        assert performance.tasks_completed == 1
        assert performance.tasks_failed == 0
        assert performance.success_rate == 1.0
        assert performance.average_execution_time == 1800
        assert performance.efficiency_rating > 1.0  # Faster than estimated

    def test_real_time_status(self, orchestrator):
        """Test real-time status reporting."""
        # Update some agent statuses and performance
        orchestrator.agent_status["python-specialist"] = AgentStatus.BUSY
        orchestrator.agent_performance["python-specialist"].tasks_completed = 3
        orchestrator.agent_performance["python-specialist"].current_load = 1
        
        status = orchestrator.get_real_time_status()
        
        assert "timestamp" in status
        assert "agent_status" in status
        assert "agent_performance" in status
        assert "system_metrics" in status
        
        assert status["agent_status"]["python-specialist"] == "busy"
        assert status["agent_performance"]["python-specialist"]["tasks_completed"] == 3
        assert status["system_metrics"]["active_agents"] == 1

    def test_optimization_callbacks(self, orchestrator):
        """Test optimization callback system."""
        callback_called = False
        callback_metrics = None
        
        async def test_callback(metrics, execution):
            nonlocal callback_called, callback_metrics
            callback_called = True
            callback_metrics = metrics
        
        orchestrator.add_optimization_callback(test_callback)
        assert len(orchestrator.optimization_callbacks) == 1

    @pytest.mark.asyncio
    async def test_performance_issue_detection(self, orchestrator):
        """Test performance issue detection and optimization triggers."""
        execution = OrchestrationExecution(
            execution_id="test_006",
            project_name="test_project",
            prp_files=[]
        )
        
        # Simulate failing agent
        orchestrator.agent_performance["python-specialist"].success_rate = 0.4
        orchestrator.agent_performance["python-specialist"].tasks_completed = 5
        
        await orchestrator._check_performance_issues(execution)
        
        # Agent should be marked as recovering
        assert orchestrator.agent_status["python-specialist"] == AgentStatus.RECOVERING

    def test_performance_insights_generation(self, orchestrator):
        """Test performance insights generation."""
        execution = OrchestrationExecution(
            execution_id="test_007",
            project_name="test_project",
            prp_files=[]
        )
        
        # Mock agent analysis data
        agent_analysis = {
            "python-specialist": {
                "tasks_completed": 5,
                "tasks_failed": 0,
                "success_rate": 1.0,
                "efficiency_rating": 1.5
            },
            "react-specialist": {
                "tasks_completed": 3,
                "tasks_failed": 2,
                "success_rate": 0.6,
                "efficiency_rating": 0.9
            }
        }
        
        insights = orchestrator._generate_performance_insights(execution, agent_analysis)
        
        assert len(insights) > 0
        assert any("python-specialist" in insight for insight in insights)  # Top performer
        assert any("react-specialist" in insight for insight in insights)  # High failure rate

    def test_orchestration_report_generation(self, orchestrator):
        """Test comprehensive orchestration report generation."""
        execution = OrchestrationExecution(
            execution_id="test_008",
            project_name="E-commerce Platform",
            prp_files=["ecommerce.md"],
            total_tasks=20,
            completed_tasks=18,
            failed_tasks=2,
            start_time=datetime.now() - timedelta(hours=2),
            end_time=datetime.now(),
            status="completed"
        )
        
        # Add some performance data
        orchestrator.agent_performance["python-specialist"].tasks_completed = 8
        orchestrator.agent_performance["python-specialist"].tasks_failed = 1
        orchestrator.agent_performance["python-specialist"].success_rate = 0.89
        
        execution.knowledge_graph["performance_insights"] = [
            "Project completed faster than estimated",
            "python-specialist showed excellent performance"
        ]
        
        execution.optimization_history = [
            {
                "timestamp": datetime.now().isoformat(),
                "actions": ["Reduced load for underperforming agents"]
            }
        ]
        
        report = orchestrator.generate_orchestration_report(execution)
        
        assert "E-commerce Platform" in report
        assert "90.0%" in report  # Success rate
        assert "python-specialist" in report
        assert "Performance Insights" in report
        assert "Optimization History" in report

    @pytest.mark.asyncio
    async def test_full_orchestration_flow(self, orchestrator, temp_complex_prp_file):
        """Test complete orchestration flow with mocked execution."""
        with patch.object(orchestrator, '_execute_with_monitoring') as mock_execute:
            async def mock_execution(execution, tasks):
                # Simulate successful execution
                execution.completed_tasks = len(tasks)
                execution.failed_tasks = 0
                
                # Update agent performance
                for task in tasks:
                    if task.assigned_agent:
                        perf = orchestrator.agent_performance[task.assigned_agent]
                        perf.tasks_completed += 1
                        perf.success_rate = 1.0
            
            mock_execute.side_effect = mock_execution
            
            execution = await orchestrator.orchestrate_project(
                project_dir="/tmp/test_project",
                prp_files=[temp_complex_prp_file]
            )
            
            assert execution.status == "completed"
            assert execution.completed_tasks > 0
            assert execution.total_agents > 0
            assert "complexity_analysis" in execution.knowledge_graph
            assert "agent_assignments" in execution.knowledge_graph

    def test_error_handling_in_orchestration(self, orchestrator):
        """Test error handling in various orchestration scenarios."""
        # Test with non-existent PRP file
        with pytest.raises(FileNotFoundError):
            asyncio.run(orchestrator.orchestrate_project(
                project_dir="/tmp",
                prp_files=["non_existent.md"]
            ))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])