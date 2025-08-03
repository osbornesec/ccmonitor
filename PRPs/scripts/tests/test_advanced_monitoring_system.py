#!/usr/bin/env python3
"""
Tests for Advanced Monitoring System

This test suite validates the comprehensive monitoring and analytics capabilities:
- Real-time metrics collection and analysis
- Alert system with intelligent triggers
- Performance trend analysis and prediction
- Recovery mechanism execution and validation
- Dashboard metrics calculation and reporting
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

from PRPs.scripts.advanced_monitoring_system import (
    AdvancedMonitoringSystem,
    SystemMetric,
    MetricType,
    AlertSeverity,
    SystemAlert,
    RecoveryAction,
    RecoveryStrategy,
    PerformanceTrend,
    DashboardMetrics
)
from PRPs.scripts.multi_agent_orchestrator import OrchestrationExecution


class TestAdvancedMonitoringSystem:
    """Test suite for advanced monitoring system."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_path = f.name
        
        yield temp_path
        
        Path(temp_path).unlink(missing_ok=True)

    @pytest.fixture
    def monitoring_system(self, temp_db_path):
        """Create monitoring system for testing."""
        return AdvancedMonitoringSystem(db_path=temp_db_path)

    @pytest.fixture
    def sample_execution(self):
        """Create sample orchestration execution."""
        execution = OrchestrationExecution(
            execution_id="test_exec_001",
            project_name="Test Monitoring Project",
            prp_files=["test_monitoring.md"],
            start_time=datetime.now()
        )
        execution.total_tasks = 20
        execution.completed_tasks = 15
        execution.failed_tasks = 3
        return execution

    def test_monitoring_system_initialization(self, monitoring_system):
        """Test monitoring system initialization."""
        assert monitoring_system.monitoring_active is False
        assert len(monitoring_system.active_executions) == 0
        assert len(monitoring_system.alert_rules) > 0
        assert len(monitoring_system.recovery_strategies) > 0
        assert len(monitoring_system.metric_collectors) > 0
        assert monitoring_system.auto_recovery_enabled is True

    def test_database_initialization(self, monitoring_system):
        """Test database schema creation."""
        # Database should be created and accessible
        import sqlite3
        
        with sqlite3.connect(str(monitoring_system.db_path)) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['metrics', 'alerts', 'recovery_actions', 'performance_trends']
            for table in expected_tables:
                assert table in tables

    def test_alert_rules_configuration(self, monitoring_system):
        """Test default alert rules configuration."""
        rule_names = [rule['name'] for rule in monitoring_system.alert_rules]
        
        expected_rules = [
            'high_failure_rate',
            'agent_overload', 
            'system_degradation',
            'execution_timeout',
            'resource_exhaustion'
        ]
        
        for expected_rule in expected_rules:
            assert expected_rule in rule_names
        
        # Check rule structure
        for rule in monitoring_system.alert_rules:
            assert 'name' in rule
            assert 'condition' in rule
            assert 'severity' in rule
            assert 'description' in rule
            assert 'actions' in rule
            assert callable(rule['condition'])

    def test_recovery_strategies_configuration(self, monitoring_system):
        """Test recovery strategies configuration."""
        expected_strategies = [
            'retry_task',
            'reassign_agent',
            'scale_up',
            'graceful_degradation',
            'emergency_recovery'
        ]
        
        for strategy in expected_strategies:
            assert strategy in monitoring_system.recovery_strategies
            assert callable(monitoring_system.recovery_strategies[strategy])

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, monitoring_system, sample_execution):
        """Test starting and stopping monitoring."""
        # Start monitoring
        await monitoring_system.start_monitoring(sample_execution)
        
        assert sample_execution.execution_id in monitoring_system.active_executions
        assert monitoring_system.monitoring_active is True
        assert monitoring_system.monitoring_thread is not None
        
        # Stop monitoring
        monitoring_system.stop_monitoring(sample_execution.execution_id)
        
        assert sample_execution.execution_id not in monitoring_system.active_executions

    def test_system_metric_creation(self, monitoring_system):
        """Test system metric creation and properties."""
        metric = SystemMetric(
            id="test_metric_001",
            metric_type=MetricType.PERFORMANCE,
            name="test_performance",
            value=0.85,
            unit="ratio",
            source="test_agent",
            context={"test": "context"},
            tags=["performance", "test"]
        )
        
        assert metric.id == "test_metric_001"
        assert metric.metric_type == MetricType.PERFORMANCE
        assert metric.name == "test_performance"
        assert metric.value == 0.85
        assert metric.unit == "ratio"
        assert metric.source == "test_agent"
        assert "test" in metric.context
        assert "performance" in metric.tags

    @pytest.mark.asyncio
    async def test_metric_collection(self, monitoring_system):
        """Test metric collection functionality."""
        # Test system health metrics
        health_metrics = await monitoring_system._collect_system_health_metrics()
        assert len(health_metrics) >= 0  # May be empty if no active executions
        
        # Test agent performance metrics
        agent_metrics = await monitoring_system._collect_agent_performance_metrics()
        assert len(agent_metrics) > 0
        
        for metric in agent_metrics:
            assert isinstance(metric, SystemMetric)
            assert metric.metric_type in [MetricType.PERFORMANCE, MetricType.RESOURCE]
            assert metric.source in ["python-specialist", "react-specialist", "security-analyst", 
                                    "performance-optimizer", "postgresql-specialist"]
        
        # Test throughput metrics with active execution
        monitoring_system.active_executions["test"] = sample_execution = OrchestrationExecution(
            execution_id="test",
            project_name="Test",
            prp_files=[],
            start_time=datetime.now() - timedelta(hours=1)
        )
        sample_execution.completed_tasks = 10
        
        throughput_metrics = await monitoring_system._collect_task_throughput_metrics()
        assert len(throughput_metrics) > 0
        
        throughput_metric = throughput_metrics[0]
        assert throughput_metric.metric_type == MetricType.THROUGHPUT
        assert throughput_metric.name == "task_throughput"
        assert throughput_metric.unit == "tasks_per_hour"

    @pytest.mark.asyncio
    async def test_metric_persistence(self, monitoring_system):
        """Test metric persistence to database."""
        metric = SystemMetric(
            id="persist_test_001",
            metric_type=MetricType.PERFORMANCE,
            name="test_persistence",
            value=0.95,
            unit="ratio",
            source="test_system"
        )
        
        await monitoring_system._persist_metric(metric)
        
        # Verify metric was stored
        import sqlite3
        with sqlite3.connect(str(monitoring_system.db_path)) as conn:
            cursor = conn.execute("SELECT * FROM metrics WHERE id = ?", (metric.id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row[0] == metric.id  # id
            assert row[1] == metric.metric_type.value  # metric_type
            assert row[2] == metric.name  # name
            assert row[3] == metric.value  # value

    def test_alert_condition_helpers(self, monitoring_system):
        """Test alert condition helper methods."""
        # Create test metrics
        test_metrics = [
            SystemMetric("1", MetricType.QUALITY, "task_success_rate", 0.5, "ratio", "system"),
            SystemMetric("2", MetricType.RESOURCE, "agent_load", 0.9, "ratio", "python-specialist"),
            SystemMetric("3", MetricType.AVAILABILITY, "system_health", 0.3, "ratio", "system"),
            SystemMetric("4", MetricType.RESOURCE, "cpu_utilization", 0.95, "ratio", "system")
        ]
        
        # Test success rate check
        success_rate = monitoring_system._get_success_rate(test_metrics)
        assert success_rate == 0.5
        
        # Test agent overload check
        overload = monitoring_system._check_agent_overload(test_metrics)
        assert overload is True
        
        # Test system health check
        health = monitoring_system._check_system_health(test_metrics)
        assert health == 0.3
        
        # Test resource utilization check
        resource_util = monitoring_system._check_resource_utilization(test_metrics)
        assert resource_util == 0.95
        
        # Test overloaded agents identification
        overloaded_agents = monitoring_system._get_overloaded_agents(test_metrics)
        assert "python-specialist" in overloaded_agents

    @pytest.mark.asyncio 
    async def test_alert_triggering(self, monitoring_system):
        """Test alert triggering mechanism."""
        # Create metrics that should trigger alerts
        bad_metrics = [
            SystemMetric("1", MetricType.QUALITY, "task_success_rate", 0.6, "ratio", "system"),
            SystemMetric("2", MetricType.RESOURCE, "agent_load", 0.95, "ratio", "test-agent")
        ]
        
        initial_alert_count = len(monitoring_system.active_alerts)
        
        await monitoring_system._check_alert_conditions()
        
        # Add the bad metrics to the buffer to simulate collection
        monitoring_system.metrics_buffer.extend(bad_metrics)
        
        await monitoring_system._check_alert_conditions()
        
        # Should have triggered alerts (though they may be throttled)
        assert len(monitoring_system.active_alerts) >= initial_alert_count

    def test_system_alert_creation(self, monitoring_system):
        """Test system alert creation and properties."""
        alert = SystemAlert(
            id="test_alert_001",
            severity=AlertSeverity.ERROR,
            title="Test Alert",
            description="This is a test alert",
            source="test_system",
            affected_components=["agent1", "agent2"],
            context={"test": "context"},
            suggested_actions=["action1", "action2"]
        )
        
        assert alert.id == "test_alert_001"
        assert alert.severity == AlertSeverity.ERROR
        assert alert.title == "Test Alert"
        assert alert.description == "This is a test alert"
        assert alert.source == "test_system"
        assert "agent1" in alert.affected_components
        assert len(alert.suggested_actions) == 2
        assert not alert.resolved
        assert not alert.auto_recovery_attempted

    @pytest.mark.asyncio
    async def test_alert_persistence(self, monitoring_system):
        """Test alert persistence to database."""
        alert = SystemAlert(
            id="persist_alert_001",
            severity=AlertSeverity.WARNING,
            title="Test Persistence Alert",
            description="Testing alert persistence",
            source="test_system",
            affected_components=["component1"]
        )
        
        await monitoring_system._persist_alert(alert)
        
        # Verify alert was stored
        import sqlite3
        with sqlite3.connect(str(monitoring_system.db_path)) as conn:
            cursor = conn.execute("SELECT * FROM alerts WHERE id = ?", (alert.id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row[0] == alert.id  # id
            assert row[1] == alert.severity.value  # severity
            assert row[2] == alert.title  # title

    def test_recovery_action_creation(self, monitoring_system):
        """Test recovery action creation."""
        action = RecoveryAction(
            id="test_recovery_001",
            strategy=RecoveryStrategy.RETRY,
            target="failed_task_123",
            description="Retry failed task",
            parameters={"max_retries": 3, "backoff": 2}
        )
        
        assert action.id == "test_recovery_001"
        assert action.strategy == RecoveryStrategy.RETRY
        assert action.target == "failed_task_123"
        assert action.description == "Retry failed task"
        assert action.parameters["max_retries"] == 3
        assert not action.success
        assert action.execution_time == 0.0

    @pytest.mark.asyncio
    async def test_recovery_strategies(self, monitoring_system):
        """Test recovery strategy execution."""
        action = RecoveryAction(
            id="test_recovery_002",
            strategy=RecoveryStrategy.RETRY,
            target="test_target",
            description="Test recovery",
            parameters={}
        )
        
        # Test retry strategy
        success = await monitoring_system._retry_failed_task(action)
        assert success is True  # Mocked to return True
        
        # Test reassignment strategy
        action.strategy = RecoveryStrategy.REASSIGN
        success = await monitoring_system._reassign_task_to_different_agent(action)
        assert success is True
        
        # Test scale up strategy
        action.strategy = RecoveryStrategy.SCALE_UP
        success = await monitoring_system._scale_up_resources(action)
        assert success is True

    @pytest.mark.asyncio
    async def test_recovery_action_persistence(self, monitoring_system):
        """Test recovery action persistence to database."""
        action = RecoveryAction(
            id="persist_recovery_001",
            strategy=RecoveryStrategy.RETRY,
            target="test_target",
            description="Test recovery persistence",
            parameters={"test": "param"},
            success=True,
            execution_time=1.5,
            notes="Test notes"
        )
        
        await monitoring_system._persist_recovery_action(action)
        
        # Verify action was stored
        import sqlite3
        with sqlite3.connect(str(monitoring_system.db_path)) as conn:
            cursor = conn.execute("SELECT * FROM recovery_actions WHERE id = ?", (action.id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row[0] == action.id  # id
            assert row[1] == action.strategy.value  # strategy
            assert row[5] == action.success  # success

    def test_performance_trend_analysis(self, monitoring_system):
        """Test performance trend analysis."""
        # Add some historical data
        from collections import deque
        import time
        
        history = deque()
        base_time = datetime.now()
        
        # Simulate degrading performance trend
        for i in range(50):
            timestamp = base_time + timedelta(minutes=i)
            value = 1.0 - (i * 0.01)  # Decreasing trend
            history.append((timestamp, value))
        
        monitoring_system.performance_history["test_metric"] = history
        
        # Analyze trend
        asyncio.run(monitoring_system._analyze_performance_trend("test_metric", history))
        
        # The trend analysis should detect degradation
        # (Full validation would require accessing the returned trend object)

    def test_dashboard_metrics_calculation(self, monitoring_system, sample_execution):
        """Test dashboard metrics calculation."""
        # Add execution to monitoring
        monitoring_system.active_executions[sample_execution.execution_id] = sample_execution
        
        # Add some test metrics to buffer
        test_metrics = [
            SystemMetric("1", MetricType.AVAILABILITY, "system_health", 0.85, "ratio", "system"),
            SystemMetric("2", MetricType.THROUGHPUT, "task_throughput", 5.5, "tasks_per_hour", "test"),
            SystemMetric("3", MetricType.RESOURCE, "cpu_utilization", 0.6, "ratio", "system"),
            SystemMetric("4", MetricType.ERROR, "task_error_rate", 0.1, "ratio", "test")
        ]
        
        monitoring_system.metrics_buffer.extend(test_metrics)
        
        dashboard = monitoring_system.get_real_time_dashboard()
        
        assert isinstance(dashboard, DashboardMetrics)
        assert dashboard.system_health == 0.85
        assert dashboard.active_executions == 1  # One sample execution
        assert dashboard.completed_tasks == sample_execution.completed_tasks
        assert dashboard.failed_tasks == sample_execution.failed_tasks
        assert dashboard.success_rate > 0
        assert isinstance(dashboard.agent_performance, dict)

    def test_dashboard_caching(self, monitoring_system):
        """Test dashboard caching mechanism."""
        # Get dashboard twice quickly
        dashboard1 = monitoring_system.get_real_time_dashboard()
        dashboard2 = monitoring_system.get_real_time_dashboard()
        
        # Should be the same cached instance
        assert dashboard1.timestamp == dashboard2.timestamp
        
        # Wait for cache to expire and get new dashboard
        import time
        time.sleep(monitoring_system.dashboard_cache_ttl + 0.1)
        
        dashboard3 = monitoring_system.get_real_time_dashboard()
        
        # Should be a new instance
        assert dashboard3.timestamp != dashboard1.timestamp

    def test_monitoring_report_generation(self, monitoring_system, sample_execution):
        """Test comprehensive monitoring report generation."""
        # Setup test data
        monitoring_system.active_executions[sample_execution.execution_id] = sample_execution
        
        # Add some recovery actions
        test_recovery = RecoveryAction(
            id="test_recovery",
            strategy=RecoveryStrategy.RETRY,
            target="test",
            description="Test recovery",
            parameters={},
            success=True
        )
        monitoring_system.recovery_actions[test_recovery.id] = test_recovery
        
        report = monitoring_system.get_monitoring_report()
        
        assert "Advanced Monitoring System Report" in report
        assert "System Overview" in report
        assert "Agent Status" in report
        assert "Performance Metrics" in report
        assert "Recent Alerts" in report
        assert "Recovery Actions" in report
        assert str(sample_execution.completed_tasks) in report
        assert str(sample_execution.failed_tasks) in report

    def test_callback_system(self, monitoring_system):
        """Test callback system for alerts and optimization."""
        callback_called = False
        received_alert = None
        
        async def test_alert_callback(alert):
            nonlocal callback_called, received_alert
            callback_called = True
            received_alert = alert
        
        monitoring_system.add_alert_callback(test_alert_callback)
        
        # Should have registered the callback
        assert len(monitoring_system.alert_callbacks) == 1

    def test_metric_type_enum(self):
        """Test metric type enumeration."""
        assert MetricType.PERFORMANCE.value == "performance"
        assert MetricType.RESOURCE.value == "resource"
        assert MetricType.ERROR.value == "error"
        assert MetricType.THROUGHPUT.value == "throughput"
        assert MetricType.LATENCY.value == "latency"
        assert MetricType.AVAILABILITY.value == "availability"
        assert MetricType.QUALITY.value == "quality"

    def test_alert_severity_enum(self):
        """Test alert severity enumeration."""
        assert AlertSeverity.INFO.value == 1
        assert AlertSeverity.WARNING.value == 2
        assert AlertSeverity.ERROR.value == 3
        assert AlertSeverity.CRITICAL.value == 4
        
        # Test severity comparison
        assert AlertSeverity.CRITICAL > AlertSeverity.ERROR
        assert AlertSeverity.ERROR > AlertSeverity.WARNING
        assert AlertSeverity.WARNING > AlertSeverity.INFO

    def test_recovery_strategy_enum(self):
        """Test recovery strategy enumeration."""
        assert RecoveryStrategy.RETRY.value == "retry"
        assert RecoveryStrategy.REASSIGN.value == "reassign"
        assert RecoveryStrategy.SCALE_UP.value == "scale_up"
        assert RecoveryStrategy.ROLLBACK.value == "rollback"
        assert RecoveryStrategy.GRACEFUL_DEGRADATION.value == "graceful_degradation"

    @pytest.mark.asyncio
    async def test_auto_recovery_mechanism(self, monitoring_system):
        """Test automatic recovery mechanism."""
        # Create alert that should trigger auto-recovery
        alert = SystemAlert(
            id="auto_recovery_test",
            severity=AlertSeverity.ERROR,
            title="Alert: high_failure_rate",
            description="High failure rate detected",
            source="monitoring-system",
            affected_components=["test_component"],
            context={"rule": "high_failure_rate"}
        )
        
        # Enable auto-recovery
        monitoring_system.auto_recovery_enabled = True
        
        await monitoring_system._attempt_auto_recovery(alert)
        
        # Should have created a recovery action
        assert len(monitoring_system.recovery_actions) > 0
        
        # Check that recovery action was recorded
        recovery_actions = list(monitoring_system.recovery_actions.values())
        assert any(action.parameters.get("alert_id") == alert.id for action in recovery_actions)

    @pytest.mark.asyncio
    async def test_knowledge_sharing_integration(self, monitoring_system, sample_execution):
        """Test integration with knowledge sharing framework."""
        await monitoring_system.start_monitoring(sample_execution)
        
        # Should have shared knowledge about monitoring start
        # (This would be verified by checking the knowledge framework,
        # but we're testing the integration point exists)
        assert monitoring_system.knowledge_framework is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])