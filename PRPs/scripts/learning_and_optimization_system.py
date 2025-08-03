#!/usr/bin/env python3
"""
Learning and Optimization System for Multi-Agent PRP Orchestration

This module implements machine learning capabilities, performance optimization,
and adaptive system behaviors for the autonomous TDD-PRP development system.

Features:
- ML-powered predictive analytics for performance optimization
- Adaptive agent selection based on historical performance
- Intelligent resource allocation and load balancing
- Pattern recognition for common development workflows
- Self-tuning system parameters
- Performance trend analysis and optimization recommendations
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import sqlite3
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
import joblib
import threading
import time

# Import knowledge sharing framework
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from PRPs.scripts.knowledge_sharing_framework import KnowledgeSharingFramework
except ImportError:
    # Fallback for testing
    class KnowledgeSharingFramework:
        def share_insight(self, *args, **kwargs): pass
        def get_insights(self, *args, **kwargs): return []


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    agent_name: str
    task_type: str
    execution_time: float
    success_rate: float
    resource_usage: float
    complexity_score: float
    timestamp: datetime
    context: Dict[str, Any] = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}


@dataclass
class OptimizationRecommendation:
    """Optimization recommendation data structure."""
    category: str  # 'agent_selection', 'resource_allocation', 'workflow'
    priority: str  # 'high', 'medium', 'low'
    description: str
    expected_improvement: float  # percentage
    implementation_effort: str  # 'low', 'medium', 'high'
    affected_components: List[str]
    confidence_score: float  # 0.0 to 1.0
    
    
@dataclass
class LearningInsight:
    """Learning insight from pattern analysis."""
    pattern_type: str
    description: str
    frequency: int
    confidence: float
    recommendations: List[str]
    evidence: Dict[str, Any]


class PerformancePredictor:
    """Machine learning model for performance prediction."""
    
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = [
            'complexity_score', 'agent_experience', 'resource_availability',
            'time_of_day', 'concurrent_tasks', 'historical_success_rate'
        ]
    
    def prepare_features(self, data: List[PerformanceMetric]) -> np.ndarray:
        """Prepare feature matrix from performance data."""
        features = []
        
        for metric in data:
            # Calculate agent experience (mock implementation)
            agent_experience = len([m for m in data if m.agent_name == metric.agent_name])
            
            # Time of day feature (0-23 hours)
            time_of_day = metric.timestamp.hour
            
            # Mock concurrent tasks and resource availability
            concurrent_tasks = metric.context.get('concurrent_tasks', 1)
            resource_availability = metric.context.get('resource_availability', 0.8)
            
            feature_row = [
                metric.complexity_score,
                agent_experience,
                resource_availability,
                time_of_day,
                concurrent_tasks,
                metric.success_rate
            ]
            features.append(feature_row)
        
        return np.array(features)
    
    def train(self, data: List[PerformanceMetric]) -> Dict[str, float]:
        """Train the performance prediction model."""
        if len(data) < 10:  # Need minimum data for training
            return {'error': 'Insufficient data for training'}
        
        X = self.prepare_features(data)
        y = np.array([metric.execution_time for metric in data])
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        
        return {
            'mse': mse,
            'rmse': np.sqrt(mse),
            'feature_importance': dict(zip(self.feature_names, self.model.feature_importances_))
        }
    
    def predict_performance(self, agent_name: str, task_complexity: float, 
                          context: Dict[str, Any]) -> float:
        """Predict execution time for a task."""
        if not self.is_trained:
            return 60.0  # Default prediction
        
        # Prepare features for prediction
        feature_row = [
            task_complexity,
            context.get('agent_experience', 5),
            context.get('resource_availability', 0.8),
            datetime.now().hour,
            context.get('concurrent_tasks', 1),
            context.get('historical_success_rate', 0.85)
        ]
        
        X_scaled = self.scaler.transform([feature_row])
        prediction = self.model.predict(X_scaled)[0]
        
        return max(prediction, 5.0)  # Minimum 5 seconds


class AgentSelectionOptimizer:
    """ML-based agent selection optimization."""
    
    def __init__(self):
        self.model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.agent_encodings = {}
        self.task_encodings = {}
    
    def encode_categorical(self, value: str, encodings: Dict[str, int]) -> int:
        """Encode categorical variables."""
        if value not in encodings:
            encodings[value] = len(encodings)
        return encodings[value]
    
    def prepare_features(self, agent_name: str, task_type: str, 
                        context: Dict[str, Any]) -> np.ndarray:
        """Prepare features for agent selection."""
        agent_encoded = self.encode_categorical(agent_name, self.agent_encodings)
        task_encoded = self.encode_categorical(task_type, self.task_encodings)
        
        features = [
            agent_encoded,
            task_encoded,
            context.get('complexity_score', 0.5),
            context.get('urgency', 0.5),
            context.get('resource_requirements', 0.5),
            context.get('agent_current_load', 0.3),
            context.get('agent_success_rate', 0.85)
        ]
        
        return np.array(features).reshape(1, -1)
    
    def train(self, performance_data: List[PerformanceMetric]) -> Dict[str, float]:
        """Train agent selection model."""
        if len(performance_data) < 20:
            return {'error': 'Insufficient data for training'}
        
        X = []
        y = []
        
        for metric in performance_data:
            agent_encoded = self.encode_categorical(metric.agent_name, self.agent_encodings)
            task_encoded = self.encode_categorical(metric.task_type, self.task_encodings)
            
            features = [
                agent_encoded,
                task_encoded,
                metric.complexity_score,
                metric.context.get('urgency', 0.5),
                metric.resource_usage,
                metric.context.get('agent_current_load', 0.3),
                metric.success_rate
            ]
            
            X.append(features)
            # Binary classification: 1 for good performance (>80% success), 0 otherwise
            y.append(1 if metric.success_rate > 0.8 else 0)
        
        X = np.array(X)
        y = np.array(y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        return {
            'accuracy': accuracy,
            'feature_importance': self.model.feature_importances_.tolist()
        }
    
    def recommend_agent(self, available_agents: List[str], task_type: str,
                       context: Dict[str, Any]) -> Tuple[str, float]:
        """Recommend best agent for a task."""
        if not self.is_trained or not available_agents:
            # Fallback to simple selection
            return available_agents[0], 0.5
        
        best_agent = None
        best_score = -1
        
        for agent in available_agents:
            features = self.prepare_features(agent, task_type, context)
            X_scaled = self.scaler.transform(features)
            
            # Get probability of success
            prob = self.model.predict_proba(X_scaled)[0][1]  # Probability of class 1 (success)
            
            if prob > best_score:
                best_score = prob
                best_agent = agent
        
        return best_agent or available_agents[0], best_score


class PatternRecognitionEngine:
    """Recognizes patterns in development workflows and performance."""
    
    def __init__(self):
        self.workflow_patterns = defaultdict(list)
        self.performance_patterns = defaultdict(list)
        self.temporal_patterns = defaultdict(list)
    
    def analyze_workflow_patterns(self, execution_history: List[Dict[str, Any]]) -> List[LearningInsight]:
        """Analyze workflow patterns from execution history."""
        insights = []
        
        # Pattern 1: Common task sequences
        task_sequences = []
        for execution in execution_history:
            if 'task_sequence' in execution:
                task_sequences.append(execution['task_sequence'])
        
        if task_sequences:
            # Find common subsequences (simplified implementation)
            sequence_counts = defaultdict(int)
            for sequence in task_sequences:
                for i in range(len(sequence) - 1):
                    subsequence = tuple(sequence[i:i+2])
                    sequence_counts[subsequence] += 1
            
            # Identify frequent patterns
            for pattern, count in sequence_counts.items():
                if count >= 3:  # Threshold for significance
                    insights.append(LearningInsight(
                        pattern_type="workflow_sequence",
                        description=f"Common task sequence: {' → '.join(pattern)}",
                        frequency=count,
                        confidence=min(count / len(task_sequences), 1.0),
                        recommendations=[f"Optimize transition from {pattern[0]} to {pattern[1]}"],
                        evidence={"pattern": pattern, "occurrences": count}
                    ))
        
        # Pattern 2: Agent specialization patterns
        agent_task_performance = defaultdict(lambda: defaultdict(list))
        for execution in execution_history:
            for task in execution.get('tasks', []):
                agent = task.get('assigned_agent')
                task_type = task.get('type')
                success_rate = task.get('success_rate', 0.8)
                
                if agent and task_type:
                    agent_task_performance[agent][task_type].append(success_rate)
        
        # Identify agent specializations
        for agent, task_types in agent_task_performance.items():
            for task_type, success_rates in task_types.items():
                if len(success_rates) >= 3:
                    avg_success = np.mean(success_rates)
                    if avg_success > 0.9:
                        insights.append(LearningInsight(
                            pattern_type="agent_specialization",
                            description=f"Agent {agent} excels at {task_type} tasks",
                            frequency=len(success_rates),
                            confidence=avg_success,
                            recommendations=[f"Prefer {agent} for {task_type} tasks"],
                            evidence={"agent": agent, "task_type": task_type, "success_rates": success_rates}
                        ))
        
        return insights
    
    def analyze_temporal_patterns(self, performance_data: List[PerformanceMetric]) -> List[LearningInsight]:
        """Analyze temporal performance patterns."""
        insights = []
        
        # Group by hour of day
        hourly_performance = defaultdict(list)
        for metric in performance_data:
            hour = metric.timestamp.hour
            hourly_performance[hour].append(metric.execution_time)
        
        # Find optimal hours
        best_hours = []
        for hour, times in hourly_performance.items():
            if len(times) >= 5:  # Minimum samples
                avg_time = np.mean(times)
                if avg_time < np.mean([t for times_list in hourly_performance.values() for t in times_list]) * 0.8:
                    best_hours.append((hour, avg_time))
        
        if best_hours:
            best_hours.sort(key=lambda x: x[1])
            best_hour = best_hours[0][0]
            
            insights.append(LearningInsight(
                pattern_type="temporal_optimization",
                description=f"Best performance observed during hour {best_hour}:00-{best_hour+1}:00",
                frequency=len(hourly_performance[best_hour]),
                confidence=0.8,
                recommendations=[f"Schedule critical tasks during hour {best_hour}"],
                evidence={"best_hours": best_hours}
            ))
        
        return insights


class ResourceOptimizer:
    """Optimizes resource allocation based on learning insights."""
    
    def __init__(self):
        self.resource_history = deque(maxlen=1000)
        self.optimization_rules = []
    
    def analyze_resource_usage(self, performance_data: List[PerformanceMetric]) -> List[OptimizationRecommendation]:
        """Analyze resource usage patterns and generate recommendations."""
        recommendations = []
        
        # Analyze agent load distribution
        agent_loads = defaultdict(list)
        for metric in performance_data:
            agent_loads[metric.agent_name].append(metric.resource_usage)
        
        # Check for load imbalances
        if len(agent_loads) > 1:
            load_means = {agent: np.mean(loads) for agent, loads in agent_loads.items()}
            max_load = max(load_means.values())
            min_load = min(load_means.values())
            
            if max_load > min_load * 1.5:  # Significant imbalance
                overloaded_agent = max(load_means, key=load_means.get)
                underloaded_agent = min(load_means, key=load_means.get)
                
                recommendations.append(OptimizationRecommendation(
                    category="resource_allocation",
                    priority="high",
                    description=f"Load imbalance detected: {overloaded_agent} overloaded, {underloaded_agent} underutilized",
                    expected_improvement=25.0,
                    implementation_effort="medium",
                    affected_components=[overloaded_agent, underloaded_agent],
                    confidence_score=0.85
                ))
        
        # Analyze task complexity vs resource allocation
        complexity_resource_pairs = [(m.complexity_score, m.resource_usage) for m in performance_data]
        if len(complexity_resource_pairs) > 10:
            complexities = [pair[0] for pair in complexity_resource_pairs]
            resources = [pair[1] for pair in complexity_resource_pairs]
            
            # Simple correlation analysis
            correlation = np.corrcoef(complexities, resources)[0, 1]
            
            if correlation < 0.5:  # Weak correlation suggests suboptimal allocation
                recommendations.append(OptimizationRecommendation(
                    category="resource_allocation",
                    priority="medium",
                    description="Resource allocation not well-correlated with task complexity",
                    expected_improvement=15.0,
                    implementation_effort="high",
                    affected_components=["resource_allocator"],
                    confidence_score=abs(correlation)
                ))
        
        return recommendations


class LearningAndOptimizationSystem:
    """
    Main learning and optimization system for multi-agent PRP orchestration.
    Implements ML-based performance optimization and adaptive behaviors.
    """
    
    def __init__(self, db_path: str = "PRPs/learning_optimization.db"):
        self.db_path = Path(db_path)
        self.logger = self._setup_logging()
        
        # Core components
        self.knowledge_framework = KnowledgeSharingFramework()
        self.performance_predictor = PerformancePredictor()
        self.agent_optimizer = AgentSelectionOptimizer()
        self.pattern_engine = PatternRecognitionEngine()
        self.resource_optimizer = ResourceOptimizer()
        
        # Learning state
        self.performance_history: List[PerformanceMetric] = []
        self.execution_history: List[Dict[str, Any]] = []
        self.optimization_recommendations: List[OptimizationRecommendation] = []
        self.learning_insights: List[LearningInsight] = []
        
        # Configuration
        self.learning_enabled = True
        self.auto_optimization_enabled = True
        self.min_data_for_learning = 20
        self.learning_interval = 300  # 5 minutes
        
        # Threading
        self.learning_thread: Optional[threading.Thread] = None
        self.learning_active = False
        
        # Initialize database
        self._init_database()
        self._load_historical_data()
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the learning system."""
        logger = logging.getLogger(f"learning_optimization_{id(self)}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _init_database(self):
        """Initialize SQLite database for learning data."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    execution_time REAL NOT NULL,
                    success_rate REAL NOT NULL,
                    resource_usage REAL NOT NULL,
                    complexity_score REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    context TEXT,
                    UNIQUE(agent_name, task_type, timestamp)
                );
                
                CREATE TABLE IF NOT EXISTS execution_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT UNIQUE NOT NULL,
                    project_name TEXT,
                    duration REAL,
                    success_rate REAL,
                    task_sequence TEXT,
                    agent_assignments TEXT,
                    timestamp TEXT NOT NULL,
                    metadata TEXT
                );
                
                CREATE TABLE IF NOT EXISTS optimization_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    description TEXT NOT NULL,
                    expected_improvement REAL,
                    implementation_effort TEXT,
                    affected_components TEXT,
                    confidence_score REAL,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    applied_at TEXT
                );
                
                CREATE TABLE IF NOT EXISTS learning_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    frequency INTEGER,
                    confidence REAL,
                    recommendations TEXT,
                    evidence TEXT,
                    created_at TEXT NOT NULL
                );
                
                CREATE INDEX IF NOT EXISTS idx_performance_agent_task 
                ON performance_metrics(agent_name, task_type);
                
                CREATE INDEX IF NOT EXISTS idx_performance_timestamp 
                ON performance_metrics(timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_execution_timestamp 
                ON execution_history(timestamp);
            """)
    
    def _load_historical_data(self):
        """Load historical data from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Load performance metrics
                cursor = conn.execute("""
                    SELECT agent_name, task_type, execution_time, success_rate,
                           resource_usage, complexity_score, timestamp, context
                    FROM performance_metrics
                    ORDER BY timestamp DESC
                    LIMIT 1000
                """)
                
                for row in cursor.fetchall():
                    context = json.loads(row[7]) if row[7] else {}
                    metric = PerformanceMetric(
                        agent_name=row[0],
                        task_type=row[1],
                        execution_time=row[2],
                        success_rate=row[3],
                        resource_usage=row[4],
                        complexity_score=row[5],
                        timestamp=datetime.fromisoformat(row[6]),
                        context=context
                    )
                    self.performance_history.append(metric)
                
                # Load execution history
                cursor = conn.execute("""
                    SELECT execution_id, project_name, duration, success_rate,
                           task_sequence, agent_assignments, timestamp, metadata
                    FROM execution_history
                    ORDER BY timestamp DESC
                    LIMIT 100
                """)
                
                for row in cursor.fetchall():
                    execution = {
                        'execution_id': row[0],
                        'project_name': row[1],
                        'duration': row[2],
                        'success_rate': row[3],
                        'task_sequence': json.loads(row[4]) if row[4] else [],
                        'agent_assignments': json.loads(row[5]) if row[5] else {},
                        'timestamp': row[6],
                        'metadata': json.loads(row[7]) if row[7] else {}
                    }
                    self.execution_history.append(execution)
                
                self.logger.info(f"Loaded {len(self.performance_history)} performance metrics and {len(self.execution_history)} execution records")
                
        except Exception as e:
            self.logger.error(f"Error loading historical data: {e}")
    
    def record_performance_metric(self, metric: PerformanceMetric):
        """Record a performance metric for learning."""
        self.performance_history.append(metric)
        
        # Persist to database
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO performance_metrics
                    (agent_name, task_type, execution_time, success_rate,
                     resource_usage, complexity_score, timestamp, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric.agent_name,
                    metric.task_type,
                    metric.execution_time,
                    metric.success_rate,
                    metric.resource_usage,
                    metric.complexity_score,
                    metric.timestamp.isoformat(),
                    json.dumps(metric.context)
                ))
                
        except Exception as e:
            self.logger.error(f"Error recording performance metric: {e}")
    
    def record_execution_history(self, execution_data: Dict[str, Any]):
        """Record execution history for pattern analysis."""
        self.execution_history.append(execution_data)
        
        # Persist to database
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO execution_history
                    (execution_id, project_name, duration, success_rate,
                     task_sequence, agent_assignments, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    execution_data.get('execution_id'),
                    execution_data.get('project_name'),
                    execution_data.get('duration'),
                    execution_data.get('success_rate'),
                    json.dumps(execution_data.get('task_sequence', [])),
                    json.dumps(execution_data.get('agent_assignments', {})),
                    execution_data.get('timestamp', datetime.now().isoformat()),
                    json.dumps(execution_data.get('metadata', {}))
                ))
                
        except Exception as e:
            self.logger.error(f"Error recording execution history: {e}")
    
    def start_learning(self):
        """Start the continuous learning process."""
        if self.learning_active:
            self.logger.warning("Learning system already active")
            return
        
        self.learning_active = True
        self.learning_thread = threading.Thread(target=self._learning_loop, daemon=True)
        self.learning_thread.start()
        self.logger.info("Learning and optimization system started")
    
    def stop_learning(self):
        """Stop the continuous learning process."""
        self.learning_active = False
        if self.learning_thread:
            self.learning_thread.join(timeout=5)
        self.logger.info("Learning and optimization system stopped")
    
    def _learning_loop(self):
        """Main learning loop that runs in background."""
        while self.learning_active:
            try:
                if len(self.performance_history) >= self.min_data_for_learning:
                    self._perform_learning_cycle()
                
                # Wait for next learning cycle
                time.sleep(self.learning_interval)
                
            except Exception as e:
                self.logger.error(f"Error in learning loop: {e}")
                time.sleep(30)  # Wait longer if there's an error
    
    def _perform_learning_cycle(self):
        """Perform a complete learning cycle."""
        self.logger.info("Starting learning cycle")
        
        # Train predictive models
        self._train_models()
        
        # Analyze patterns
        self._analyze_patterns()
        
        # Generate optimization recommendations
        self._generate_recommendations()
        
        # Share insights with knowledge framework
        self._share_learning_insights()
        
        self.logger.info("Learning cycle completed")
    
    def _train_models(self):
        """Train ML models with current data."""
        try:
            # Train performance predictor
            if len(self.performance_history) >= 10:
                predictor_results = self.performance_predictor.train(self.performance_history)
                self.logger.info(f"Performance predictor trained: {predictor_results}")
            
            # Train agent selection optimizer
            if len(self.performance_history) >= 20:
                optimizer_results = self.agent_optimizer.train(self.performance_history)
                self.logger.info(f"Agent optimizer trained: {optimizer_results}")
                
        except Exception as e:
            self.logger.error(f"Error training models: {e}")
    
    def _analyze_patterns(self):
        """Analyze patterns in historical data."""
        try:
            # Workflow pattern analysis
            workflow_insights = self.pattern_engine.analyze_workflow_patterns(self.execution_history)
            self.learning_insights.extend(workflow_insights)
            
            # Temporal pattern analysis
            temporal_insights = self.pattern_engine.analyze_temporal_patterns(self.performance_history)
            self.learning_insights.extend(temporal_insights)
            
            # Persist insights
            self._persist_learning_insights()
            
            self.logger.info(f"Generated {len(workflow_insights + temporal_insights)} new learning insights")
            
        except Exception as e:
            self.logger.error(f"Error analyzing patterns: {e}")
    
    def _generate_recommendations(self):
        """Generate optimization recommendations."""
        try:
            # Resource optimization recommendations
            resource_recommendations = self.resource_optimizer.analyze_resource_usage(self.performance_history)
            self.optimization_recommendations.extend(resource_recommendations)
            
            # Persist recommendations
            self._persist_recommendations()
            
            self.logger.info(f"Generated {len(resource_recommendations)} optimization recommendations")
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
    
    def _persist_learning_insights(self):
        """Persist learning insights to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for insight in self.learning_insights[-10:]:  # Persist recent insights
                    conn.execute("""
                        INSERT OR IGNORE INTO learning_insights
                        (pattern_type, description, frequency, confidence,
                         recommendations, evidence, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        insight.pattern_type,
                        insight.description,
                        insight.frequency,
                        insight.confidence,
                        json.dumps(insight.recommendations),
                        json.dumps(insight.evidence),
                        datetime.now().isoformat()
                    ))
                    
        except Exception as e:
            self.logger.error(f"Error persisting learning insights: {e}")
    
    def _persist_recommendations(self):
        """Persist optimization recommendations to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for rec in self.optimization_recommendations[-10:]:  # Persist recent recommendations
                    conn.execute("""
                        INSERT OR IGNORE INTO optimization_recommendations
                        (category, priority, description, expected_improvement,
                         implementation_effort, affected_components, confidence_score, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        rec.category,
                        rec.priority,
                        rec.description,
                        rec.expected_improvement,
                        rec.implementation_effort,
                        json.dumps(rec.affected_components),
                        rec.confidence_score,
                        datetime.now().isoformat()
                    ))
                    
        except Exception as e:
            self.logger.error(f"Error persisting recommendations: {e}")
    
    def _share_learning_insights(self):
        """Share learning insights with knowledge sharing framework."""
        try:
            for insight in self.learning_insights[-5:]:  # Share recent insights
                self.knowledge_framework.share_insight(
                    category="learning_optimization",
                    title=f"Learning Insight: {insight.pattern_type}",
                    content=insight.description,
                    metadata={
                        'confidence': insight.confidence,
                        'frequency': insight.frequency,
                        'recommendations': insight.recommendations
                    },
                    tags=['learning', 'optimization', insight.pattern_type]
                )
                
        except Exception as e:
            self.logger.error(f"Error sharing learning insights: {e}")
    
    def get_agent_recommendation(self, available_agents: List[str], task_type: str,
                               context: Dict[str, Any]) -> Tuple[str, float]:
        """Get ML-based agent recommendation for a task."""
        return self.agent_optimizer.recommend_agent(available_agents, task_type, context)
    
    def predict_task_performance(self, agent_name: str, task_complexity: float,
                                context: Dict[str, Any]) -> float:
        """Predict task execution time using ML model."""
        return self.performance_predictor.predict_performance(agent_name, task_complexity, context)
    
    def get_optimization_recommendations(self, category: Optional[str] = None,
                                       priority: Optional[str] = None) -> List[OptimizationRecommendation]:
        """Get current optimization recommendations."""
        recommendations = self.optimization_recommendations
        
        if category:
            recommendations = [r for r in recommendations if r.category == category]
        
        if priority:
            recommendations = [r for r in recommendations if r.priority == priority]
        
        return sorted(recommendations, key=lambda x: (
            {'high': 3, 'medium': 2, 'low': 1}.get(x.priority, 0),
            x.confidence_score
        ), reverse=True)
    
    def get_learning_insights(self, pattern_type: Optional[str] = None) -> List[LearningInsight]:
        """Get current learning insights."""
        insights = self.learning_insights
        
        if pattern_type:
            insights = [i for i in insights if i.pattern_type == pattern_type]
        
        return sorted(insights, key=lambda x: x.confidence, reverse=True)
    
    def get_system_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive system health and learning report."""
        recent_metrics = [m for m in self.performance_history if m.timestamp > datetime.now() - timedelta(hours=24)]
        
        # Performance statistics
        if recent_metrics:
            avg_execution_time = np.mean([m.execution_time for m in recent_metrics])
            avg_success_rate = np.mean([m.success_rate for m in recent_metrics])
            avg_resource_usage = np.mean([m.resource_usage for m in recent_metrics])
        else:
            avg_execution_time = avg_success_rate = avg_resource_usage = 0
        
        # Learning system status
        learning_status = {
            'performance_predictor_trained': self.performance_predictor.is_trained,
            'agent_optimizer_trained': self.agent_optimizer.is_trained,
            'total_performance_metrics': len(self.performance_history),
            'total_execution_history': len(self.execution_history),
            'recent_insights': len([i for i in self.learning_insights if hasattr(i, 'created_at')]),
            'pending_recommendations': len([r for r in self.optimization_recommendations if getattr(r, 'status', 'pending') == 'pending'])
        }
        
        # Top recommendations
        top_recommendations = self.get_optimization_recommendations()[:3]
        
        return {
            'system_overview': {
                'learning_active': self.learning_active,
                'auto_optimization_enabled': self.auto_optimization_enabled,
                'data_sufficiency': len(self.performance_history) >= self.min_data_for_learning
            },
            'performance_metrics': {
                'avg_execution_time': avg_execution_time,
                'avg_success_rate': avg_success_rate,
                'avg_resource_usage': avg_resource_usage,
                'metrics_count_24h': len(recent_metrics)
            },
            'learning_status': learning_status,
            'top_recommendations': [
                {
                    'category': r.category,
                    'description': r.description,
                    'expected_improvement': r.expected_improvement,
                    'confidence': r.confidence_score
                }
                for r in top_recommendations
            ],
            'recent_insights': [
                {
                    'pattern_type': i.pattern_type,
                    'description': i.description,
                    'confidence': i.confidence
                }
                for i in self.get_learning_insights()[:3]
            ]
        }
    
    def export_models(self, export_dir: str):
        """Export trained models for deployment."""
        export_path = Path(export_dir)
        export_path.mkdir(parents=True, exist_ok=True)
        
        try:
            if self.performance_predictor.is_trained:
                joblib.dump(self.performance_predictor.model, export_path / "performance_predictor.pkl")
                joblib.dump(self.performance_predictor.scaler, export_path / "performance_scaler.pkl")
            
            if self.agent_optimizer.is_trained:
                joblib.dump(self.agent_optimizer.model, export_path / "agent_optimizer.pkl")
                joblib.dump(self.agent_optimizer.scaler, export_path / "agent_scaler.pkl")
            
            # Export encodings and metadata
            metadata = {
                'agent_encodings': self.agent_optimizer.agent_encodings,
                'task_encodings': self.agent_optimizer.task_encodings,
                'feature_names': self.performance_predictor.feature_names,
                'export_timestamp': datetime.now().isoformat()
            }
            
            with open(export_path / "model_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Models exported to {export_path}")
            
        except Exception as e:
            self.logger.error(f"Error exporting models: {e}")
            raise


# Example usage and testing
if __name__ == "__main__":
    # Create learning system
    learning_system = LearningAndOptimizationSystem()
    
    # Start learning
    learning_system.start_learning()
    
    # Simulate some performance data
    import random
    agents = ["python-specialist", "react-specialist", "security-analyst"]
    task_types = ["implementation", "testing", "review", "optimization"]
    
    for i in range(50):
        metric = PerformanceMetric(
            agent_name=random.choice(agents),
            task_type=random.choice(task_types),
            execution_time=random.uniform(30, 300),
            success_rate=random.uniform(0.7, 1.0),
            resource_usage=random.uniform(0.2, 0.8),
            complexity_score=random.uniform(0.1, 1.0),
            timestamp=datetime.now() - timedelta(hours=random.randint(0, 168)),
            context={
                'concurrent_tasks': random.randint(1, 5),
                'resource_availability': random.uniform(0.6, 1.0)
            }
        )
        learning_system.record_performance_metric(metric)
    
    # Wait for learning
    time.sleep(2)
    
    # Get recommendations
    recommendations = learning_system.get_optimization_recommendations()
    print(f"Generated {len(recommendations)} optimization recommendations")
    
    # Get insights
    insights = learning_system.get_learning_insights()
    print(f"Generated {len(insights)} learning insights")
    
    # Get system health
    health_report = learning_system.get_system_health_report()
    print("System Health Report:")
    print(json.dumps(health_report, indent=2, default=str))
    
    # Stop learning
    learning_system.stop_learning()
    
    print("Learning and Optimization System demonstration completed")