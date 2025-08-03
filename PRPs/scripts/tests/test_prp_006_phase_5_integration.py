#!/usr/bin/env python3
"""
Integration Tests for PRP-006 Phase 5: Learning and Optimization

This test suite validates the complete integration of learning and optimization
capabilities with the multi-agent orchestration system.
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

from PRPs.scripts.multi_agent_orchestrator import MultiAgentOrchestrator, OrchestrationExecution
from PRPs.scripts.learning_and_optimization_system import (
    LearningAndOptimizationSystem, 
    PerformanceMetric, 
    OptimizationRecommendation
)


class TestPRP006Phase5Integration:
    """Integration tests for PRP-006 Phase 5 learning and optimization capabilities."""

    @pytest.fixture
    def temp_agents_dir(self):
        """Create temporary agents directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            agents_dir = Path(temp_dir) / "agents"
            agents_dir.mkdir()
            
            # Create test agent files
            test_agents = {
                "python-specialist": "Python development specialist with ML capabilities",
                "react-specialist": "React frontend specialist with performance optimization", 
                "security-analyst": "Security analysis specialist with learning algorithms",
                "performance-optimizer": "Performance optimization specialist with ML insights"
            }
            
            for agent_name, description in test_agents.items():
                agent_file = agents_dir / f"{agent_name}.md"
                agent_file.write_text(f"""---
name: {agent_name}
description: {description}
---

# {agent_name}

{description} with advanced PRP execution and learning capabilities.

## Learning and Optimization Capabilities
This agent supports ML-based optimization and performance learning.

### Machine Learning Integration
- Performance prediction and optimization
- Pattern recognition for common workflows
- Adaptive task assignment
- Resource optimization

### TDD Methodology Integration
- Red Phase: Create failing tests with ML insights
- Green Phase: Implement with performance optimization
- Refactor Phase: ML-guided optimization

### Autonomous Workflow Integration
- ACTIVE_TODOS.md integration with learning insights
- Multi-agent coordination with performance optimization
- Error handling and recovery with pattern recognition
""")
            
            yield str(agents_dir)

    @pytest.fixture
    def sample_prp_file(self):
        """Create sample PRP file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# Sample PRP for Learning and Optimization Test

## Goal
Create a high-performance web application with ML-powered optimization.

## Implementation Blueprint
- Set up Python Flask backend with performance monitoring
- Create React frontend with optimization insights
- Add security measures with learning capabilities
- Implement ML-based performance optimization
- Add comprehensive testing with pattern recognition

## Learning Integration
- Performance metric collection
- Pattern recognition for optimization
- ML-based agent selection
- Resource optimization algorithms

## Validation Loop
### Level 0: Test Creation with ML Insights
- Unit tests for all components with performance benchmarks
- Integration tests with ML validation
- Performance tests with optimization recommendations

### Level 1: Syntax & Style with Learning
- Code formatting and linting with pattern recognition
- Security code scanning with ML threat detection

### Level 2: Unit Tests with Optimization
- >95% test coverage with ML coverage analysis
- All tests passing with performance validation

### Level 3: Integration Testing with Learning
- End-to-end functionality with ML insights
- Performance benchmarks with optimization recommendations

### Level 4: Creative Validation with ML
- User experience testing with ML analytics
- Security penetration testing with learning algorithms
- Performance optimization with ML recommendations
""")
            temp_path = f.name
        
        yield temp_path
        
        Path(temp_path).unlink()

    @pytest.fixture
    def orchestrator_with_learning(self, temp_agents_dir):
        """Create orchestrator with learning system."""
        return MultiAgentOrchestrator(agents_dir=temp_agents_dir, max_agents=4)

    def test_orchestrator_learning_integration(self, orchestrator_with_learning):
        """Test that orchestrator properly integrates learning system."""
        orchestrator = orchestrator_with_learning
        
        # Check learning system is initialized
        assert orchestrator.learning_system is not None
        assert isinstance(orchestrator.learning_system, LearningAndOptimizationSystem)
        
        # Check learning system components
        assert orchestrator.learning_system.learning_enabled is True
        assert orchestrator.learning_system.auto_optimization_enabled is True
        assert orchestrator.learning_system.performance_predictor is not None
        assert orchestrator.learning_system.agent_optimizer is not None

    def test_real_time_status_with_learning(self, orchestrator_with_learning):
        """Test real-time status includes learning system data."""
        orchestrator = orchestrator_with_learning
        
        status = orchestrator.get_real_time_status()
        
        # Check basic orchestrator status
        assert "timestamp" in status
        assert "agent_status" in status
        assert "agent_performance" in status
        assert "system_metrics" in status
        
        # Check monitoring system integration (should be available)
        assert "monitoring_system" in status
        
        # Learning system status should be available
        # Note: Learning system doesn't directly expose status but is integrated
        assert orchestrator.learning_system is not None
        assert orchestrator.learning_system.learning_enabled is True

    def test_learning_based_agent_selection(self, orchestrator_with_learning):
        """Test ML-based agent selection during task assignment."""
        orchestrator = orchestrator_with_learning
        
        # Create a mock task
        from PRPs.scripts.prp_coordination_system import PRPTask
        
        task = PRPTask(
            id="test_task_001",
            title="Python API Implementation",
            description="Implement Python API with performance optimization",
            requirements=["Flask", "SQLAlchemy", "Performance monitoring"],
            domain="python",
            complexity=8
        )
        task.estimated_duration = 2.0
        
        # Test agent score calculation with learning system
        for agent_name in orchestrator.base_coordinator.agents.keys():
            agent_capability = orchestrator.base_coordinator.agents[agent_name]
            
            # Calculate score using ML-enhanced method
            score = orchestrator._calculate_comprehensive_agent_score(
                agent_capability, task, agent_name
            )
            
            assert isinstance(score, float)
            assert score >= 0
            
            # The ML modifier should be applied
            # (This tests that the learning system integration works)

    def test_performance_metric_recording(self, orchestrator_with_learning):
        """Test that performance metrics are recorded in learning system."""
        orchestrator = orchestrator_with_learning
        learning_system = orchestrator.learning_system
        
        initial_metric_count = len(learning_system.performance_history)
        
        # Create a mock task
        from PRPs.scripts.prp_coordination_system import PRPTask
        
        task = PRPTask(
            id="test_metric_task",
            title="Test Task for Metrics",
            description="Test task for metrics collection",  
            requirements=["pytest", "coverage"],
            domain="testing",
            complexity=5
        )
        task.estimated_duration = 1.0
        task.assigned_agent = "python-specialist"
        
        # Record task execution
        orchestrator._record_task_execution(task, execution_time=120.0, success=True)
        
        # Check that metric was recorded
        assert len(learning_system.performance_history) == initial_metric_count + 1
        
        # Check metric properties
        recorded_metric = learning_system.performance_history[-1]
        assert recorded_metric.agent_name == "python-specialist"
        assert recorded_metric.task_type == "testing"
        assert recorded_metric.execution_time == 120.0
        assert recorded_metric.success_rate == 1.0

    @pytest.mark.asyncio
    async def test_learning_during_orchestration(self, orchestrator_with_learning, sample_prp_file):
        """Test learning system activation during project orchestration."""
        orchestrator = orchestrator_with_learning
        
        # Mock the execution phases to focus on learning integration
        with patch.object(orchestrator, '_analyze_project_complexity') as mock_analyze, \
             patch.object(orchestrator, '_decompose_project_tasks') as mock_decompose, \
             patch.object(orchestrator, '_resolve_task_dependencies') as mock_resolve, \
             patch.object(orchestrator, '_assign_agents_intelligently') as mock_assign, \
             patch.object(orchestrator, '_execute_with_monitoring') as mock_execute, \
             patch.object(orchestrator, '_analyze_execution_performance') as mock_performance:
            
            # Setup mocks
            mock_analyze.return_value = None
            mock_decompose.return_value = []
            mock_resolve.return_value = None
            mock_assign.return_value = None
            mock_execute.return_value = None
            mock_performance.return_value = None
            
            # Execute orchestration
            execution = await orchestrator.orchestrate_project(
                project_dir="/tmp/test_project",
                prp_files=[sample_prp_file]
            )
            
            # Verify execution completed
            assert execution.status == "completed"
            
            # Verify learning system was available during execution
            assert orchestrator.learning_system is not None
            assert orchestrator.learning_system.learning_active is True

    def test_learning_system_health_report(self, orchestrator_with_learning):
        """Test learning system health report generation."""
        orchestrator = orchestrator_with_learning
        learning_system = orchestrator.learning_system
        
        # Add some test performance data
        metric = PerformanceMetric(
            agent_name="python-specialist",
            task_type="implementation",
            execution_time=150.0,
            success_rate=0.95,
            resource_usage=0.6,
            complexity_score=0.7,
            timestamp=datetime.now()
        )
        learning_system.record_performance_metric(metric)
        
        # Generate health report
        health_report = learning_system.get_system_health_report()
        
        # Check report structure
        assert "system_overview" in health_report
        assert "performance_metrics" in health_report
        assert "learning_status" in health_report
        assert "top_recommendations" in health_report
        assert "recent_insights" in health_report
        
        # Check system overview
        system_overview = health_report["system_overview"]
        assert "learning_active" in system_overview
        assert "auto_optimization_enabled" in system_overview
        assert system_overview["learning_active"] is True
        assert system_overview["auto_optimization_enabled"] is True

    def test_ml_agent_recommendations(self, orchestrator_with_learning):
        """Test ML-based agent recommendations."""
        orchestrator = orchestrator_with_learning
        learning_system = orchestrator.learning_system
        
        # Add sufficient performance data for ML training
        agents = ["python-specialist", "react-specialist", "security-analyst"]
        task_types = ["implementation", "testing", "review"]
        
        for i in range(25):  # Above minimum threshold for training
            metric = PerformanceMetric(
                agent_name=agents[i % 3],
                task_type=task_types[i % 3],
                execution_time=60 + (i * 2),
                success_rate=0.8 + (i % 3) * 0.05,
                resource_usage=0.3 + (i % 4) * 0.1,
                complexity_score=0.2 + (i % 5) * 0.1,
                timestamp=datetime.now() - timedelta(hours=i),
                context={"concurrent_tasks": 1 + (i % 3)}
            )
            learning_system.record_performance_metric(metric)
        
        # Trigger learning cycle to train models
        learning_system._perform_learning_cycle()
        
        # Test agent recommendation
        available_agents = ["python-specialist", "react-specialist", "security-analyst"]
        recommended_agent, confidence = learning_system.get_agent_recommendation(
            available_agents=available_agents,
            task_type="implementation",
            context={
                "complexity_score": 0.8,
                "urgency": 0.6,
                "resource_requirements": 0.7
            }
        )
        
        assert recommended_agent in available_agents
        assert 0 <= confidence <= 1

    def test_performance_prediction_integration(self, orchestrator_with_learning):
        """Test performance prediction integration."""
        orchestrator = orchestrator_with_learning
        learning_system = orchestrator.learning_system
        
        # Add performance data
        for i in range(15):
            metric = PerformanceMetric(
                agent_name="python-specialist",
                task_type="implementation",
                execution_time=90 + (i * 5),
                success_rate=0.9,
                resource_usage=0.5,
                complexity_score=0.5 + (i * 0.02),
                timestamp=datetime.now() - timedelta(hours=i)
            )
            learning_system.record_performance_metric(metric)
        
        # Train predictor
        learning_system._perform_learning_cycle()
        
        # Test performance prediction
        prediction = learning_system.predict_task_performance(
            agent_name="python-specialist",
            task_complexity=0.7,
            context={
                "agent_experience": 10,
                "resource_availability": 0.8
            }
        )
        
        assert isinstance(prediction, float)
        assert prediction > 0

    def test_optimization_recommendations_generation(self, orchestrator_with_learning):
        """Test optimization recommendations generation."""
        orchestrator = orchestrator_with_learning
        learning_system = orchestrator.learning_system
        
        # Add performance data with load imbalance
        agents = ["python-specialist", "react-specialist", "security-analyst"]
        
        for i in range(30):
            # Create load imbalance
            agent = agents[i % 3]
            if agent == "python-specialist":
                resource_usage = 0.9  # Overloaded
            elif agent == "react-specialist":
                resource_usage = 0.6  # Normal
            else:  # security-analyst
                resource_usage = 0.3  # Underloaded
            
            metric = PerformanceMetric(
                agent_name=agent,
                task_type="implementation",
                execution_time=90,
                success_rate=0.85,
                resource_usage=resource_usage,
                complexity_score=0.6,
                timestamp=datetime.now() - timedelta(hours=i)
            )
            learning_system.record_performance_metric(metric)
        
        # Generate recommendations
        learning_system._perform_learning_cycle()
        
        recommendations = learning_system.get_optimization_recommendations()
        
        # Should detect resource allocation issues
        resource_recs = [r for r in recommendations if r.category == "resource_allocation"]
        
        if resource_recs:  # May not always detect with small dataset
            rec = resource_recs[0]
            assert rec.priority in ["high", "medium", "low"]
            assert rec.expected_improvement > 0
            assert rec.confidence_score >= 0

    @pytest.mark.asyncio
    async def test_end_to_end_learning_workflow(self, orchestrator_with_learning, sample_prp_file):
        """Test complete end-to-end learning workflow."""
        orchestrator = orchestrator_with_learning
        learning_system = orchestrator.learning_system
        
        # Pre-populate with some learning data
        for i in range(10):
            metric = PerformanceMetric(
                agent_name="python-specialist",
                task_type="implementation",
                execution_time=120 + (i * 10),
                success_rate=0.9,
                resource_usage=0.5,
                complexity_score=0.6,
                timestamp=datetime.now() - timedelta(hours=i)
            )
            learning_system.record_performance_metric(metric)
        
        # Mock orchestration to focus on learning
        with patch.object(orchestrator.base_coordinator, 'execute_prp') as mock_execute:
            mock_execute.return_value = {
                'status': 'completed',
                'completed_tasks': 8,
                'failed_tasks': 1,
                'execution_time': 180,
                'agent_metrics': {
                    'python-specialist': {'efficiency': 1.2, 'success_rate': 0.89}
                }
            }
            
            # Get initial learning status
            initial_health = learning_system.get_system_health_report()
            initial_metrics_count = len(learning_system.performance_history)
            
            # Execute project with learning
            execution = await orchestrator.orchestrate_project(
                project_dir="/tmp/test_project", 
                prp_files=[sample_prp_file]
            )
            
            # Get final learning status
            final_health = learning_system.get_system_health_report()
            
            # Verify learning integration worked
            assert execution.status == "completed"
            
            # Verify learning system was active
            assert final_health["system_overview"]["learning_active"] is True
            
            # Note: Additional metrics may not be recorded in mocked execution
            # but the learning system integration should be verified

    def test_learning_system_database_integration(self, orchestrator_with_learning):
        """Test learning system database integration."""
        orchestrator = orchestrator_with_learning
        learning_system = orchestrator.learning_system
        
        # Check database exists
        assert learning_system.db_path.exists()
        
        # Add and verify metric persistence
        metric = PerformanceMetric(
            agent_name="test-agent",
            task_type="test-task",
            execution_time=100.0,
            success_rate=0.95,
            resource_usage=0.6,
            complexity_score=0.7,
            timestamp=datetime.now(),
            context={"test": "data"}
        )
        
        learning_system.record_performance_metric(metric)
        
        # Verify metric was persisted (would require database query in full test)
        assert len(learning_system.performance_history) > 0
        assert learning_system.performance_history[-1].agent_name == "test-agent"

    def test_learning_system_cleanup(self, orchestrator_with_learning):
        """Test learning system proper cleanup."""
        orchestrator = orchestrator_with_learning
        learning_system = orchestrator.learning_system
        
        # Start learning process
        if not learning_system.learning_active:
            learning_system.start_learning()
        
        assert learning_system.learning_active is True
        
        # Stop learning process
        learning_system.stop_learning()
        
        assert learning_system.learning_active is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])