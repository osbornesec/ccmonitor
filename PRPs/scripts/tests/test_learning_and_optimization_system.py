#!/usr/bin/env python3
"""
Tests for Learning and Optimization System

This test suite validates the machine learning capabilities, pattern recognition,
and optimization features of the learning and optimization system.
"""

import asyncio
import json
import tempfile
import pytest
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sqlite3

import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from PRPs.scripts.learning_and_optimization_system import (
    LearningAndOptimizationSystem,
    PerformanceMetric,
    OptimizationRecommendation, 
    LearningInsight,
    PerformancePredictor,
    AgentSelectionOptimizer,
    PatternRecognitionEngine,
    ResourceOptimizer
)


class TestPerformanceMetric:
    """Test performance metric data structure."""
    
    def test_performance_metric_creation(self):
        """Test creating performance metric."""
        metric = PerformanceMetric(
            agent_name="test-agent",
            task_type="implementation",
            execution_time=120.5,
            success_rate=0.95,
            resource_usage=0.6,
            complexity_score=0.7,
            timestamp=datetime.now()
        )
        
        assert metric.agent_name == "test-agent"
        assert metric.task_type == "implementation"
        assert metric.execution_time == 120.5
        assert metric.success_rate == 0.95
        assert metric.resource_usage == 0.6
        assert metric.complexity_score == 0.7
        assert metric.context == {}
    
    def test_performance_metric_with_context(self):
        """Test performance metric with context data."""
        context = {"concurrent_tasks": 3, "resource_availability": 0.8}
        metric = PerformanceMetric(
            agent_name="test-agent",
            task_type="testing",
            execution_time=60.0,
            success_rate=0.9,
            resource_usage=0.4,
            complexity_score=0.5,
            timestamp=datetime.now(),
            context=context
        )
        
        assert metric.context == context
        assert metric.context["concurrent_tasks"] == 3


class TestPerformancePredictor:
    """Test ML-based performance prediction."""
    
    @pytest.fixture
    def sample_metrics(self):
        """Create sample performance metrics for testing."""
        metrics = []
        base_time = datetime.now()
        
        for i in range(30):
            metric = PerformanceMetric(
                agent_name=f"agent-{i % 3}",
                task_type=f"task-{i % 4}",
                execution_time=60 + (i * 2),  # Increasing execution time
                success_rate=0.8 + (i % 3) * 0.05,
                resource_usage=0.3 + (i % 5) * 0.1,
                complexity_score=0.2 + (i % 6) * 0.1,
                timestamp=base_time - timedelta(hours=i),
                context={
                    "concurrent_tasks": 1 + (i % 4),
                    "resource_availability": 0.7 + (i % 3) * 0.1
                }
            )
            metrics.append(metric)
        
        return metrics
    
    def test_performance_predictor_initialization(self):
        """Test performance predictor initialization."""
        predictor = PerformancePredictor()
        
        assert predictor.is_trained is False
        assert len(predictor.feature_names) == 6
        assert "complexity_score" in predictor.feature_names
        assert "agent_experience" in predictor.feature_names
    
    def test_prepare_features(self, sample_metrics):
        """Test feature preparation for ML model."""
        predictor = PerformancePredictor()
        features = predictor.prepare_features(sample_metrics[:10])
        
        assert features.shape[0] == 10  # 10 samples
        assert features.shape[1] == 6   # 6 features
        assert np.all(features >= 0)    # All features should be non-negative
    
    def test_model_training(self, sample_metrics):
        """Test ML model training."""
        predictor = PerformancePredictor()
        results = predictor.train(sample_metrics)
        
        assert predictor.is_trained is True
        assert "mse" in results
        assert "rmse" in results
        assert "feature_importance" in results
        assert results["mse"] >= 0
        assert results["rmse"] >= 0
        assert len(results["feature_importance"]) == 6
    
    def test_insufficient_data_training(self):
        """Test training with insufficient data."""
        predictor = PerformancePredictor()
        few_metrics = [PerformanceMetric(
            agent_name="test",
            task_type="test",
            execution_time=60,
            success_rate=0.8,
            resource_usage=0.5,
            complexity_score=0.6,
            timestamp=datetime.now()
        ) for _ in range(5)]
        
        results = predictor.train(few_metrics)
        
        assert "error" in results
        assert predictor.is_trained is False
    
    def test_performance_prediction(self, sample_metrics):
        """Test performance prediction."""
        predictor = PerformancePredictor()
        predictor.train(sample_metrics)
        
        prediction = predictor.predict_performance(
            agent_name="test-agent",
            task_complexity=0.7,
            context={
                "agent_experience": 10,
                "resource_availability": 0.8,
                "concurrent_tasks": 2,
                "historical_success_rate": 0.9
            }
        )
        
        assert isinstance(prediction, float)
        assert prediction >= 5.0  # Minimum prediction
    
    def test_untrained_prediction(self):
        """Test prediction without training."""
        predictor = PerformancePredictor()
        
        prediction = predictor.predict_performance(
            agent_name="test-agent",
            task_complexity=0.5,
            context={}
        )
        
        assert prediction == 60.0  # Default prediction


class TestAgentSelectionOptimizer:
    """Test ML-based agent selection optimization."""
    
    @pytest.fixture
    def optimizer_metrics(self):
        """Create metrics for agent optimizer testing."""
        metrics = []
        agents = ["python-specialist", "react-specialist", "security-analyst"]
        tasks = ["implementation", "testing", "review"]
        
        for i in range(40):
            # Create realistic performance patterns
            agent = agents[i % 3]
            task = tasks[i % 3]
            
            # Specialist agents perform better on matching tasks
            if agent == "python-specialist" and task == "implementation":
                success_rate = 0.95
            elif agent == "react-specialist" and task == "implementation":
                success_rate = 0.85
            elif agent == "security-analyst" and task == "review":
                success_rate = 0.9
            else:
                success_rate = 0.75
            
            metric = PerformanceMetric(
                agent_name=agent,
                task_type=task,
                execution_time=60 + (i * 2),
                success_rate=success_rate,
                resource_usage=0.4 + (i % 4) * 0.1,
                complexity_score=0.3 + (i % 5) * 0.1,
                timestamp=datetime.now() - timedelta(hours=i),
                context={
                    "urgency": 0.3 + (i % 3) * 0.2,
                    "agent_current_load": 0.2 + (i % 4) * 0.1
                }
            )
            metrics.append(metric)
        
        return metrics
    
    def test_agent_optimizer_initialization(self):
        """Test agent optimizer initialization."""
        optimizer = AgentSelectionOptimizer()
        
        assert optimizer.is_trained is False
        assert len(optimizer.agent_encodings) == 0
        assert len(optimizer.task_encodings) == 0
    
    def test_categorical_encoding(self):
        """Test categorical variable encoding."""
        optimizer = AgentSelectionOptimizer()
        
        # Test agent encoding
        agent1_code = optimizer.encode_categorical("python-specialist", optimizer.agent_encodings)
        agent2_code = optimizer.encode_categorical("react-specialist", optimizer.agent_encodings)
        agent1_code_again = optimizer.encode_categorical("python-specialist", optimizer.agent_encodings)
        
        assert agent1_code != agent2_code
        assert agent1_code == agent1_code_again
        assert len(optimizer.agent_encodings) == 2
    
    def test_feature_preparation(self):
        """Test feature preparation for agent selection."""
        optimizer = AgentSelectionOptimizer()
        
        features = optimizer.prepare_features(
            agent_name="python-specialist",
            task_type="implementation",
            context={
                "complexity_score": 0.7,
                "urgency": 0.5,
                "resource_requirements": 0.6,
                "agent_current_load": 0.3,
                "agent_success_rate": 0.9
            }
        )
        
        assert features.shape == (1, 7)  # 1 sample, 7 features
        assert np.all(features >= 0)
    
    def test_optimizer_training(self, optimizer_metrics):
        """Test agent optimizer training."""
        optimizer = AgentSelectionOptimizer()
        results = optimizer.train(optimizer_metrics)
        
        assert optimizer.is_trained is True
        assert "accuracy" in results
        assert "feature_importance" in results
        assert 0 <= results["accuracy"] <= 1
        assert len(results["feature_importance"]) == 7
    
    def test_agent_recommendation(self, optimizer_metrics):
        """Test agent recommendation."""
        optimizer = AgentSelectionOptimizer()
        optimizer.train(optimizer_metrics)
        
        available_agents = ["python-specialist", "react-specialist", "security-analyst"]
        recommended_agent, confidence = optimizer.recommend_agent(
            available_agents=available_agents,
            task_type="implementation",
            context={
                "complexity_score": 0.8,
                "urgency": 0.6,
                "resource_requirements": 0.7,
                "agent_current_load": 0.2,
                "agent_success_rate": 0.85
            }
        )
        
        assert recommended_agent in available_agents
        assert 0 <= confidence <= 1
    
    def test_untrained_recommendation(self):
        """Test recommendation without training."""
        optimizer = AgentSelectionOptimizer()
        available_agents = ["agent1", "agent2"]
        
        recommended_agent, confidence = optimizer.recommend_agent(
            available_agents=available_agents,
            task_type="test",
            context={}
        )
        
        assert recommended_agent == "agent1"  # First agent as fallback
        assert confidence == 0.5


class TestPatternRecognitionEngine:
    """Test pattern recognition capabilities."""
    
    @pytest.fixture
    def execution_history(self):
        """Create sample execution history."""
        history = []
        
        for i in range(10):
            execution = {
                "execution_id": f"exec_{i}",
                "project_name": f"project_{i % 3}",
                "task_sequence": ["setup", "implementation", "testing", "review"],
                "tasks": [
                    {
                        "assigned_agent": "python-specialist" if i % 2 == 0 else "react-specialist",
                        "type": "implementation",
                        "success_rate": 0.9 if i % 2 == 0 else 0.7
                    },
                    {
                        "assigned_agent": "security-analyst",
                        "type": "review",
                        "success_rate": 0.95
                    }
                ]
            }
            history.append(execution)
        
        return history
    
    @pytest.fixture
    def performance_data(self):
        """Create performance data for temporal analysis."""
        data = []
        base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for hour in range(24):
            for _ in range(3):  # 3 samples per hour
                # Simulate better performance during business hours
                if 9 <= hour <= 17:
                    execution_time = 45 + (hour - 12) ** 2  # Parabolic pattern
                else:
                    execution_time = 80 + abs(hour - 12) * 2
                
                metric = PerformanceMetric(
                    agent_name="test-agent",
                    task_type="test-task",
                    execution_time=execution_time,
                    success_rate=0.85,
                    resource_usage=0.5,
                    complexity_score=0.6,
                    timestamp=base_time + timedelta(hours=hour, minutes=np.random.randint(0, 60))
                )
                data.append(metric)
        
        return data
    
    def test_pattern_engine_initialization(self):
        """Test pattern recognition engine initialization."""
        engine = PatternRecognitionEngine()
        
        assert len(engine.workflow_patterns) == 0
        assert len(engine.performance_patterns) == 0
        assert len(engine.temporal_patterns) == 0
    
    def test_workflow_pattern_analysis(self, execution_history):
        """Test workflow pattern analysis."""
        engine = PatternRecognitionEngine()
        insights = engine.analyze_workflow_patterns(execution_history)
        
        # Should find common task sequences
        sequence_insights = [i for i in insights if i.pattern_type == "workflow_sequence"]
        assert len(sequence_insights) > 0
        
        # Should find agent specializations
        specialization_insights = [i for i in insights if i.pattern_type == "agent_specialization"]
        assert len(specialization_insights) > 0
        
        # Check insight structure
        for insight in insights:
            assert hasattr(insight, 'pattern_type')
            assert hasattr(insight, 'description')
            assert hasattr(insight, 'frequency')
            assert hasattr(insight, 'confidence')
            assert hasattr(insight, 'recommendations')
            assert hasattr(insight, 'evidence')
    
    def test_temporal_pattern_analysis(self, performance_data):
        """Test temporal pattern analysis."""
        engine = PatternRecognitionEngine()
        insights = engine.analyze_temporal_patterns(performance_data)
        
        # Should find optimal time patterns
        temporal_insights = [i for i in insights if i.pattern_type == "temporal_optimization"]
        
        if temporal_insights:  # May not always find patterns with mock data
            insight = temporal_insights[0]
            assert "Best performance observed during hour" in insight.description
            assert insight.confidence > 0
            assert len(insight.recommendations) > 0


class TestResourceOptimizer:
    """Test resource optimization capabilities."""
    
    @pytest.fixture
    def resource_metrics(self):
        """Create metrics for resource optimization testing."""
        metrics = []
        agents = ["agent1", "agent2", "agent3"]
        
        for i in range(30):
            # Create load imbalance - agent1 overloaded, agent3 underloaded
            agent = agents[i % 3]
            if agent == "agent1":
                resource_usage = 0.9  # Overloaded
            elif agent == "agent2":
                resource_usage = 0.6  # Normal
            else:  # agent3
                resource_usage = 0.3  # Underloaded
            
            metric = PerformanceMetric(
                agent_name=agent,
                task_type="test-task",
                execution_time=60,
                success_rate=0.8,
                resource_usage=resource_usage,
                complexity_score=0.3 + (i % 5) * 0.1,
                timestamp=datetime.now() - timedelta(hours=i)
            )
            metrics.append(metric)
        
        return metrics
    
    def test_resource_optimizer_initialization(self):
        """Test resource optimizer initialization."""
        optimizer = ResourceOptimizer()
        
        assert len(optimizer.resource_history) == 0
        assert len(optimizer.optimization_rules) == 0
    
    def test_resource_usage_analysis(self, resource_metrics):
        """Test resource usage analysis."""
        optimizer = ResourceOptimizer()
        recommendations = optimizer.analyze_resource_usage(resource_metrics)
        
        # Should detect load imbalance
        load_recommendations = [r for r in recommendations if r.category == "resource_allocation"]
        assert len(load_recommendations) > 0
        
        # Check recommendation structure
        for rec in recommendations:
            assert hasattr(rec, 'category')
            assert hasattr(rec, 'priority')
            assert hasattr(rec, 'description')
            assert hasattr(rec, 'expected_improvement')
            assert hasattr(rec, 'implementation_effort')
            assert hasattr(rec, 'affected_components')
            assert hasattr(rec, 'confidence_score')
            assert 0 <= rec.confidence_score <= 1


class TestLearningAndOptimizationSystem:
    """Test the main learning and optimization system."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_db_path = f.name
        
        yield temp_db_path
        
        # Cleanup
        Path(temp_db_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def learning_system(self, temp_db):
        """Create learning system with temporary database."""
        system = LearningAndOptimizationSystem(db_path=temp_db)
        yield system
        system.stop_learning()
    
    def test_system_initialization(self, learning_system):
        """Test learning system initialization."""
        assert learning_system.learning_enabled is True
        assert learning_system.auto_optimization_enabled is True
        assert learning_system.min_data_for_learning == 20
        assert learning_system.learning_active is False
        assert learning_system.db_path.exists()
    
    def test_database_initialization(self, temp_db):
        """Test database schema creation."""
        system = LearningAndOptimizationSystem(db_path=temp_db)
        
        # Check tables exist
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'performance_metrics',
                'execution_history', 
                'optimization_recommendations',
                'learning_insights'
            ]
            
            for table in expected_tables:
                assert table in tables
    
    def test_performance_metric_recording(self, learning_system):
        """Test recording performance metrics."""
        initial_count = len(learning_system.performance_history)
        
        metric = PerformanceMetric(
            agent_name="test-agent",
            task_type="test-task",
            execution_time=120,
            success_rate=0.9,
            resource_usage=0.5,
            complexity_score=0.6,
            timestamp=datetime.now()
        )
        
        learning_system.record_performance_metric(metric)
        
        assert len(learning_system.performance_history) == initial_count + 1
        assert learning_system.performance_history[-1] == metric
    
    def test_execution_history_recording(self, learning_system):
        """Test recording execution history."""
        initial_count = len(learning_system.execution_history)
        
        execution_data = {
            "execution_id": "test_exec_001",
            "project_name": "Test Project",
            "duration": 300,
            "success_rate": 0.95,
            "task_sequence": ["setup", "implementation", "testing"],
            "agent_assignments": {"setup": "general", "implementation": "python-specialist"},
            "timestamp": datetime.now().isoformat()
        }
        
        learning_system.record_execution_history(execution_data)
        
        assert len(learning_system.execution_history) == initial_count + 1
        assert learning_system.execution_history[-1]["execution_id"] == "test_exec_001"
    
    def test_agent_recommendation(self, learning_system):
        """Test agent recommendation functionality."""
        available_agents = ["python-specialist", "react-specialist", "security-analyst"]
        
        recommended_agent, confidence = learning_system.get_agent_recommendation(
            available_agents=available_agents,
            task_type="implementation",
            context={"complexity_score": 0.7, "urgency": 0.5}
        )
        
        assert recommended_agent in available_agents
        assert 0 <= confidence <= 1
    
    def test_performance_prediction(self, learning_system):
        """Test performance prediction functionality."""
        prediction = learning_system.predict_task_performance(
            agent_name="test-agent",
            task_complexity=0.6,
            context={"agent_experience": 5, "resource_availability": 0.8}
        )
        
        assert isinstance(prediction, float)
        assert prediction > 0
    
    def test_learning_cycle_with_data(self, learning_system):
        """Test learning cycle with sufficient data."""
        # Add sufficient performance data
        agents = ["python-specialist", "react-specialist", "security-analyst"]
        task_types = ["implementation", "testing", "review"]
        
        for i in range(25):  # Above minimum threshold
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
        
        # Perform learning cycle
        learning_system._perform_learning_cycle()
        
        # Check that models were trained
        assert learning_system.performance_predictor.is_trained
        assert learning_system.agent_optimizer.is_trained
    
    def test_optimization_recommendations(self, learning_system):
        """Test getting optimization recommendations."""
        # Add some test recommendations
        rec = OptimizationRecommendation(
            category="resource_allocation",
            priority="high",
            description="Test recommendation",
            expected_improvement=20.0,
            implementation_effort="medium",
            affected_components=["test-component"],
            confidence_score=0.8
        )
        learning_system.optimization_recommendations.append(rec)
        
        # Test getting all recommendations
        all_recs = learning_system.get_optimization_recommendations()
        assert len(all_recs) >= 1
        
        # Test filtering by category
        resource_recs = learning_system.get_optimization_recommendations(category="resource_allocation")
        assert len(resource_recs) >= 1
        assert all(r.category == "resource_allocation" for r in resource_recs)
        
        # Test filtering by priority
        high_recs = learning_system.get_optimization_recommendations(priority="high")
        assert len(high_recs) >= 1
        assert all(r.priority == "high" for r in high_recs)
    
    def test_learning_insights(self, learning_system):
        """Test getting learning insights."""
        # Add test insight
        insight = LearningInsight(
            pattern_type="test_pattern",
            description="Test insight",
            frequency=5,
            confidence=0.9,
            recommendations=["Test recommendation"],
            evidence={"test": "data"}
        )
        learning_system.learning_insights.append(insight)
        
        # Test getting all insights
        all_insights = learning_system.get_learning_insights()
        assert len(all_insights) >= 1
        
        # Test filtering by pattern type
        test_insights = learning_system.get_learning_insights(pattern_type="test_pattern")
        assert len(test_insights) >= 1
        assert all(i.pattern_type == "test_pattern" for i in test_insights)
    
    def test_system_health_report(self, learning_system):
        """Test system health report generation."""
        # Add some test data
        metric = PerformanceMetric(
            agent_name="test-agent",
            task_type="test-task",
            execution_time=120,
            success_rate=0.9,
            resource_usage=0.5,
            complexity_score=0.6,
            timestamp=datetime.now()
        )
        learning_system.record_performance_metric(metric)
        
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
        assert "data_sufficiency" in system_overview
        
        # Check performance metrics
        perf_metrics = health_report["performance_metrics"]
        assert "avg_execution_time" in perf_metrics
        assert "avg_success_rate" in perf_metrics
        assert "avg_resource_usage" in perf_metrics
        assert "metrics_count_24h" in perf_metrics
    
    def test_learning_start_stop(self, learning_system):
        """Test starting and stopping learning process."""
        assert learning_system.learning_active is False
        
        # Start learning
        learning_system.start_learning()
        assert learning_system.learning_active is True
        assert learning_system.learning_thread is not None
        
        # Stop learning
        learning_system.stop_learning()
        assert learning_system.learning_active is False
    
    @patch('joblib.dump')
    def test_model_export(self, mock_dump, learning_system):
        """Test model export functionality."""
        # Mock trained models
        learning_system.performance_predictor.is_trained = True
        learning_system.agent_optimizer.is_trained = True
        
        with tempfile.TemporaryDirectory() as temp_dir:
            learning_system.export_models(temp_dir)
            
            # Check that joblib.dump was called for models
            assert mock_dump.call_count >= 4  # 2 models + 2 scalers
            
            # Check metadata file was created
            metadata_file = Path(temp_dir) / "model_metadata.json"
            assert metadata_file.exists()
            
            with open(metadata_file) as f:
                metadata = json.load(f)
                assert "export_timestamp" in metadata
                assert "feature_names" in metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])