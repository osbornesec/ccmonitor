#!/usr/bin/env python3
"""
Integration Tests for PRP-006 Phase 4: Advanced Monitoring and Analytics

This test suite validates the complete integration of advanced monitoring
and analytics capabilities with the multi-agent orchestration system.
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
from PRPs.scripts.advanced_monitoring_system import AdvancedMonitoringSystem, SystemMetric, MetricType


class TestPRP006Phase4Integration:
    """Integration tests for PRP-006 Phase 4 monitoring capabilities."""

    @pytest.fixture
    def temp_agents_dir(self):
        """Create temporary agents directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            agents_dir = Path(temp_dir) / "agents"
            agents_dir.mkdir()
            
            # Create test agent files
            test_agents = {
                "python-specialist": "Python development specialist",
                "react-specialist": "React frontend specialist", 
                "security-analyst": "Security analysis specialist",
                "performance-optimizer": "Performance optimization specialist"
            }
            
            for agent_name, description in test_agents.items():
                agent_file = agents_dir / f"{agent_name}.md"
                agent_file.write_text(f"""---
name: {agent_name}
description: {description}
---

# {agent_name}

{description} with PRP execution capabilities.

## PRP Execution Capabilities
This agent supports advanced PRP execution with TDD methodology.

### TDD Methodology Integration
- Red Phase: Create failing tests
- Green Phase: Implement minimal functionality  
- Refactor Phase: Optimize and improve

### Autonomous Workflow Integration
- ACTIVE_TODOS.md integration
- Multi-agent coordination
- Error handling and recovery
""")
            
            yield str(agents_dir)

    @pytest.fixture
    def sample_prp_file(self):
        """Create sample PRP file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# Sample PRP for Monitoring Test

## Goal
Create a simple web application with monitoring capabilities.

## Implementation Blueprint
- Set up Python Flask backend
- Create React frontend
- Add security measures
- Implement performance optimization
- Add comprehensive testing

## Validation Loop
### Level 0: Test Creation
- Unit tests for all components
- Integration tests

### Level 1: Syntax & Style  
- Code formatting and linting
- Security code scanning

### Level 2: Unit Tests
- >90% test coverage
- All tests passing

### Level 3: Integration Testing
- End-to-end functionality
- Performance benchmarks

### Level 4: Creative Validation
- User experience testing
- Security penetration testing
""")
            temp_path = f.name
        
        yield temp_path
        
        Path(temp_path).unlink()

    @pytest.fixture
    def orchestrator_with_monitoring(self, temp_agents_dir):
        """Create orchestrator with monitoring system."""
        return MultiAgentOrchestrator(agents_dir=temp_agents_dir, max_agents=4)

    def test_orchestrator_monitoring_integration(self, orchestrator_with_monitoring):
        """Test that orchestrator properly integrates monitoring system."""
        orchestrator = orchestrator_with_monitoring
        
        # Check monitoring system is initialized
        assert orchestrator.monitoring_system is not None
        assert isinstance(orchestrator.monitoring_system, AdvancedMonitoringSystem)
        
        # Check monitoring system components
        assert len(orchestrator.monitoring_system.alert_rules) > 0
        assert len(orchestrator.monitoring_system.recovery_strategies) > 0
        assert len(orchestrator.monitoring_system.metric_collectors) > 0

    def test_real_time_status_with_monitoring(self, orchestrator_with_monitoring):
        """Test real-time status includes monitoring data."""
        orchestrator = orchestrator_with_monitoring
        
        status = orchestrator.get_real_time_status()
        
        # Check basic orchestrator status
        assert "timestamp" in status
        assert "agent_status" in status
        assert "agent_performance" in status
        assert "system_metrics" in status
        
        # Check monitoring system integration
        assert "monitoring_system" in status
        monitoring_status = status["monitoring_system"]
        
        assert "active" in monitoring_status
        assert "system_health" in monitoring_status
        assert "monitoring_enabled" in monitoring_status
        assert monitoring_status["active"] is True
        assert monitoring_status["monitoring_enabled"] is True

    @pytest.mark.asyncio
    async def test_monitoring_during_orchestration(self, orchestrator_with_monitoring, sample_prp_file):
        """Test monitoring system activation during project orchestration."""
        orchestrator = orchestrator_with_monitoring
        
        # Mock the execution phases to avoid full orchestration
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
            
            # Verify monitoring was integrated
            assert execution.status == "completed"
            assert hasattr(execution, 'monitoring_report')
            assert execution.monitoring_report is not None
            
            # Verify monitoring system was used
            assert orchestrator.monitoring_system is not None

    @pytest.mark.asyncio
    async def test_monitoring_system_metrics_collection(self, orchestrator_with_monitoring, sample_prp_file):
        """Test that monitoring system collects metrics during execution."""
        orchestrator = orchestrator_with_monitoring
        monitoring_system = orchestrator.monitoring_system
        
        # Create sample execution for monitoring
        execution = OrchestrationExecution(
            execution_id="test_monitoring_001",
            project_name="Test Monitoring Project",
            prp_files=[sample_prp_file]
        )
        execution.total_tasks = 10
        execution.completed_tasks = 8
        execution.failed_tasks = 2
        execution.start_time = datetime.now()
        
        # Start monitoring
        await monitoring_system.start_monitoring(execution)
        
        # Wait for some metrics collection
        await asyncio.sleep(0.1)
        
        # Check that execution is being monitored
        assert execution.execution_id in monitoring_system.active_executions
        
        # Get dashboard metrics
        dashboard = monitoring_system.get_real_time_dashboard()
        
        assert dashboard is not None
        assert dashboard.active_executions >= 1
        assert dashboard.completed_tasks >= 0
        assert dashboard.failed_tasks >= 0
        assert dashboard.system_health >= 0.0
        
        # Stop monitoring
        monitoring_system.stop_monitoring(execution.execution_id)
        
        assert execution.execution_id not in monitoring_system.active_executions

    def test_monitoring_report_generation(self, orchestrator_with_monitoring):
        """Test monitoring report generation."""
        monitoring_system = orchestrator_with_monitoring.monitoring_system
        
        report = monitoring_system.get_monitoring_report()
        
        # Check report structure
        assert "Advanced Monitoring System Report" in report
        assert "System Overview" in report
        assert "Agent Status" in report
        assert "Performance Metrics" in report
        assert "Recent Alerts" in report
        assert "Recovery Actions" in report
        
        # Check report contains data
        assert "System Health:" in report
        assert "Active Executions:" in report
        assert "Success Rate:" in report

    @pytest.mark.asyncio
    async def test_monitoring_alert_system(self, orchestrator_with_monitoring):
        """Test monitoring alert system functionality."""
        monitoring_system = orchestrator_with_monitoring.monitoring_system
        
        # Check alert rules are configured
        assert len(monitoring_system.alert_rules) > 0
        
        # Check for expected alert rules
        rule_names = [rule['name'] for rule in monitoring_system.alert_rules]
        expected_rules = ['high_failure_rate', 'agent_overload', 'system_degradation']
        
        for expected_rule in expected_rules:
            assert expected_rule in rule_names
        
        # Check alert rule structure
        for rule in monitoring_system.alert_rules:
            assert 'condition' in rule
            assert callable(rule['condition'])
            assert 'severity' in rule
            assert 'description' in rule
            assert 'actions' in rule

    @pytest.mark.asyncio  
    async def test_monitoring_recovery_system(self, orchestrator_with_monitoring):
        """Test monitoring recovery system functionality."""
        monitoring_system = orchestrator_with_monitoring.monitoring_system
        
        # Check recovery strategies are configured
        assert len(monitoring_system.recovery_strategies) > 0
        
        # Check for expected recovery strategies
        expected_strategies = ['retry_task', 'reassign_agent', 'scale_up', 'graceful_degradation']
        
        for strategy in expected_strategies:
            assert strategy in monitoring_system.recovery_strategies
            assert callable(monitoring_system.recovery_strategies[strategy])
        
        # Test recovery strategy execution (they should return True in mock implementation)
        from PRPs.scripts.advanced_monitoring_system import RecoveryAction, RecoveryStrategy
        
        test_action = RecoveryAction(
            id="test_recovery",
            strategy=RecoveryStrategy.RETRY,
            target="test_target",
            description="Test recovery action",
            parameters={}
        )
        
        success = await monitoring_system._retry_failed_task(test_action)
        assert success is True

    def test_orchestrator_performance_tracking(self, orchestrator_with_monitoring):
        """Test orchestrator performance tracking integration."""
        orchestrator = orchestrator_with_monitoring
        
        # Check performance tracking is initialized
        assert hasattr(orchestrator, 'agent_performance')
        assert hasattr(orchestrator, 'agent_status')
        assert len(orchestrator.agent_performance) > 0
        assert len(orchestrator.agent_status) > 0
        
        # Check agent performance structure
        for agent_name, performance in orchestrator.agent_performance.items():
            assert hasattr(performance, 'tasks_completed')
            assert hasattr(performance, 'tasks_failed')
            assert hasattr(performance, 'success_rate')
            assert hasattr(performance, 'current_load')
            assert hasattr(performance, 'efficiency_rating')

    @pytest.mark.asyncio
    async def test_end_to_end_monitoring_workflow(self, orchestrator_with_monitoring, sample_prp_file):
        """Test complete end-to-end monitoring workflow."""
        orchestrator = orchestrator_with_monitoring
        
        # Mock the core orchestration to focus on monitoring
        with patch.object(orchestrator.base_coordinator, 'execute_prp') as mock_execute:
            mock_execute.return_value = {
                'status': 'completed',
                'completed_tasks': 5,
                'failed_tasks': 0,
                'execution_time': 120
            }
            
            # Get initial status
            initial_status = orchestrator.get_real_time_status()
            initial_monitoring = initial_status['monitoring_system']
            
            # Execute project with monitoring
            execution = await orchestrator.orchestrate_project(
                project_dir="/tmp/test_project",
                prp_files=[sample_prp_file]
            )
            
            # Get final status
            final_status = orchestrator.get_real_time_status()
            final_monitoring = final_status['monitoring_system']
            
            # Verify monitoring integration
            assert execution.status == "completed"
            assert hasattr(execution, 'monitoring_report')
            
            # Verify monitoring report structure
            if execution.monitoring_report != "Monitoring system not available":
                assert "Advanced Monitoring System Report" in execution.monitoring_report
                assert "System Overview" in execution.monitoring_report
            
            # Verify status includes monitoring data
            assert initial_monitoring['active'] is True
            assert final_monitoring['active'] is True

    def test_monitoring_system_configuration(self, orchestrator_with_monitoring):
        """Test monitoring system configuration and components."""
        monitoring_system = orchestrator_with_monitoring.monitoring_system
        
        # Check database initialization
        assert monitoring_system.db_path.exists()
        
        # Check metric collectors
        expected_collectors = [
            'system_health',
            'agent_performance', 
            'task_throughput',
            'resource_utilization',
            'error_rates'
        ]
        
        for collector in expected_collectors:
            assert collector in monitoring_system.metric_collectors
            assert callable(monitoring_system.metric_collectors[collector])
        
        # Check configuration flags
        assert monitoring_system.auto_recovery_enabled is True
        assert monitoring_system.collection_interval > 0
        assert monitoring_system.dashboard_cache_ttl > 0

    @pytest.mark.asyncio
    async def test_knowledge_sharing_monitoring_integration(self, orchestrator_with_monitoring):
        """Test integration between monitoring and knowledge sharing systems."""
        orchestrator = orchestrator_with_monitoring
        monitoring_system = orchestrator.monitoring_system
        knowledge_framework = orchestrator.knowledge_framework
        
        # Check both systems are available
        assert monitoring_system is not None
        assert knowledge_framework is not None
        
        # Check monitoring system uses knowledge framework
        assert monitoring_system.knowledge_framework is not None
        
        # Create test execution for monitoring knowledge sharing
        execution = OrchestrationExecution(
            execution_id="knowledge_test_001",
            project_name="Knowledge Integration Test",
            prp_files=[]
        )
        
        # Start monitoring (should share knowledge)
        await monitoring_system.start_monitoring(execution)
        
        # Check knowledge was shared (would be in actual knowledge graph)
        knowledge_stats = knowledge_framework.get_knowledge_statistics()
        assert knowledge_stats is not None
        
        # Stop monitoring
        monitoring_system.stop_monitoring(execution.execution_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])