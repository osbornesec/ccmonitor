#!/usr/bin/env python3
"""
Multi-Agent PRP Orchestration System - Advanced Orchestration Engine

This system provides advanced multi-agent orchestration capabilities including:
- Intelligent agent scheduling and load balancing
- Real-time performance monitoring and optimization
- Dynamic task reallocation based on agent performance
- Advanced dependency resolution with circular dependency detection
- Cross-agent knowledge sharing and collaboration protocols

Usage:
    python multi_agent_orchestrator.py --project-dir /path/to/project
    python multi_agent_orchestrator.py --prp-files prp1.md prp2.md --parallel --max-agents 10
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from enum import Enum
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PRPs.scripts.prp_coordination_system import (
    PRPCoordinationSystem, PRPTask, PRPExecution, AgentCapability
)
from PRPs.scripts.knowledge_sharing_framework import (
    KnowledgeSharingFramework, KnowledgeType, KnowledgeQuery
)
from PRPs.scripts.intelligent_project_analyzer import (
    IntelligentProjectAnalyzer, ProjectAnalysis
)
# Advanced monitoring system imported conditionally to avoid circular imports


class AgentStatus(Enum):
    """Agent status enumeration."""
    IDLE = "idle"
    BUSY = "busy"
    FAILED = "failed"
    RECOVERING = "recovering"
    OFFLINE = "offline"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class AgentPerformanceMetrics:
    """Real-time performance metrics for an agent."""
    agent_name: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_execution_time: float = 0.0
    success_rate: float = 1.0
    current_load: int = 0
    last_activity: datetime = field(default_factory=datetime.now)
    specialization_score: float = 0.0  # How well the agent matches its assigned tasks
    efficiency_rating: float = 1.0  # Performance relative to expected baseline


@dataclass
class TaskDependency:
    """Represents a dependency relationship between tasks."""
    dependent_task_id: str
    dependency_task_id: str
    dependency_type: str  # "sequential", "resource", "data"
    strength: float = 1.0  # Strength of dependency (0.0 to 1.0)


@dataclass
class AgentCommunicationMessage:
    """Message for inter-agent communication."""
    message_id: str
    sender_agent: str
    recipient_agent: Optional[str]  # None for broadcast
    message_type: str  # "knowledge_share", "resource_request", "completion_notification"
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    priority: TaskPriority = TaskPriority.MEDIUM


@dataclass
class OrchestrationExecution:
    """Extended execution record for advanced orchestration."""
    execution_id: str
    project_name: str
    prp_files: List[str]
    total_agents: int = 0
    active_agents: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: str = "initializing"
    agent_metrics: Dict[str, AgentPerformanceMetrics] = field(default_factory=dict)
    knowledge_graph: Dict[str, Any] = field(default_factory=dict)
    optimization_history: List[Dict[str, Any]] = field(default_factory=list)


class MultiAgentOrchestrator:
    """
    Advanced multi-agent orchestration system that extends the basic coordination
    system with intelligent scheduling, real-time monitoring, and cross-agent
    knowledge sharing capabilities.
    """

    def __init__(self, agents_dir: str = ".claude/agents", max_agents: int = 10):
        self.agents_dir = Path(agents_dir)
        self.max_agents = max_agents
        self.logger = self._setup_logging()
        
        # Initialize base coordination system
        self.base_coordinator = PRPCoordinationSystem(agents_dir, max_agents)
        
        # Initialize knowledge sharing framework
        self.knowledge_framework = KnowledgeSharingFramework()
        
        # Initialize intelligent project analyzer
        self.project_analyzer = IntelligentProjectAnalyzer(self.knowledge_framework)
        
        # Initialize advanced monitoring system (imported here to avoid circular imports)
        try:
            from PRPs.scripts.advanced_monitoring_system import AdvancedMonitoringSystem
            self.monitoring_system = AdvancedMonitoringSystem()
        except ImportError:
            self.monitoring_system = None
            self.logger.warning("Advanced monitoring system not available")
        
        # Initialize learning and optimization system
        try:
            from PRPs.scripts.learning_and_optimization_system import LearningAndOptimizationSystem
            self.learning_system = LearningAndOptimizationSystem()
            self.learning_system.start_learning()
        except ImportError:
            self.learning_system = None
            self.logger.warning("Learning and optimization system not available")
        
        # Advanced orchestration state
        self.agent_performance: Dict[str, AgentPerformanceMetrics] = {}
        self.agent_status: Dict[str, AgentStatus] = {}
        self.task_dependencies: List[TaskDependency] = []
        self.message_queue: List[AgentCommunicationMessage] = []
        self.knowledge_graph: Dict[str, Any] = {"patterns": {}, "solutions": {}, "performance": {}}
        
        # Performance monitoring
        self.performance_history: List[Dict[str, Any]] = []
        self.optimization_callbacks: List[Callable] = []
        
        # Initialize agent performance tracking
        self._initialize_agent_metrics()
        
        self.logger.info(f"Multi-Agent Orchestrator initialized with {len(self.base_coordinator.agents)} agents")

    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging for orchestration system."""
        logger = logging.getLogger("MultiAgentOrchestrator")
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _initialize_agent_metrics(self):
        """Initialize performance metrics for all available agents."""
        for agent_name in self.base_coordinator.agents.keys():
            self.agent_performance[agent_name] = AgentPerformanceMetrics(agent_name=agent_name)
            self.agent_status[agent_name] = AgentStatus.IDLE

    async def orchestrate_project(self, project_dir: str, prp_files: List[str]) -> OrchestrationExecution:
        """
        Orchestrate a complete project with multiple PRPs using advanced
        multi-agent coordination, real-time monitoring, and optimization.
        
        Args:
            project_dir: Directory containing the project
            prp_files: List of PRP files to execute
            
        Returns:
            OrchestrationExecution with detailed results and metrics
        """
        execution = OrchestrationExecution(
            execution_id=f"orch_{int(time.time())}",
            project_name=Path(project_dir).name,
            prp_files=prp_files
        )
        
        try:
            self.logger.info(f"🚀 Starting advanced orchestration for project: {execution.project_name}")
            
            # Start monitoring if available
            if self.monitoring_system:
                await self.monitoring_system.start_monitoring(execution)
            
            # Phase 1: Project Analysis and Planning
            await self._analyze_project_complexity(execution, project_dir, prp_files)
            
            # Phase 2: Intelligent Task Decomposition
            all_tasks = await self._decompose_project_tasks(execution, prp_files)
            
            # Phase 3: Advanced Dependency Resolution
            await self._resolve_task_dependencies(execution, all_tasks)
            
            # Phase 4: Optimal Agent Assignment
            await self._assign_agents_intelligently(execution, all_tasks)
            
            # Phase 5: Execute with Real-time Monitoring
            await self._execute_with_monitoring(execution, all_tasks)
            
            # Phase 6: Performance Analysis and Learning
            await self._analyze_execution_performance(execution)
            
            execution.status = "completed"
            execution.end_time = datetime.now()
            
            # Stop monitoring and generate final report if available
            if self.monitoring_system:
                self.monitoring_system.stop_monitoring(execution.execution_id)
                execution.monitoring_report = self.monitoring_system.get_monitoring_report()
            else:
                execution.monitoring_report = "Monitoring system not available"
            
            self.logger.info(f"✅ Project orchestration completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Project orchestration failed: {e}")
            execution.status = "failed"
            execution.end_time = datetime.now()
            raise
        
        return execution

    async def _analyze_project_complexity(self, execution: OrchestrationExecution, 
                                        project_dir: str, prp_files: List[str], 
                                        tasks: List[PRPTask] = None):
        """Analyze project complexity using intelligent project analyzer."""
        self.logger.info("🧠 Running intelligent project analysis...")
        
        try:
            # Use intelligent project analyzer for comprehensive analysis
            project_analysis = await self.project_analyzer.analyze_project(
                project_dir, prp_files, tasks
            )
            
            # Extract key metrics for orchestration
            complexity_metrics = {
                "project_type": project_analysis.project_type.value,
                "complexity_level": project_analysis.complexity.name,
                "total_estimated_hours": project_analysis.total_estimated_hours,
                "confidence_interval": project_analysis.confidence_interval,
                "total_tasks": project_analysis.complexity_metrics.total_tasks,
                "unique_domains": project_analysis.complexity_metrics.unique_domains,
                "integration_points": project_analysis.complexity_metrics.integration_points,
                "overall_complexity_score": project_analysis.complexity_metrics.overall_score,
                "recommended_agents": len(project_analysis.resource_requirements),
                "risk_level": self._extract_overall_risk_level(project_analysis.risk_assessments),
                "optimization_opportunities": len(project_analysis.optimization_opportunities)
            }
            
            # Store full analysis in execution context
            execution.knowledge_graph["intelligent_analysis"] = {
                "project_analysis": project_analysis,
                "analysis_summary": self.project_analyzer.get_analysis_summary(project_analysis),
                "recommended_scenario": project_analysis.recommended_scenario
            }
            
            # Update execution with intelligent insights
            execution.total_tasks = project_analysis.complexity_metrics.total_tasks
            execution.knowledge_graph["complexity_analysis"] = complexity_metrics
            
            self.logger.info(f"✅ Intelligent analysis complete: {project_analysis.complexity.name} "
                           f"complexity, {project_analysis.total_estimated_hours:.1f}h estimated")
            
        except Exception as e:
            self.logger.error(f"Intelligent analysis failed, falling back to basic analysis: {e}")
            # Fallback to basic analysis
            await self._basic_complexity_analysis(execution, project_dir, prp_files)

    async def _basic_complexity_analysis(self, execution: OrchestrationExecution, 
                                       project_dir: str, prp_files: List[str]):
        """Fallback basic complexity analysis."""
        complexity_metrics = {
            "total_prp_files": len(prp_files),
            "estimated_tasks": 0,
            "complexity_score": 0.0,
            "estimated_duration": 0.0,
            "recommended_agents": 0
        }
        
        for prp_file in prp_files:
            try:
                goal, tasks = self.base_coordinator.parse_prp_file(prp_file)
                complexity_metrics["estimated_tasks"] += len(tasks)
                
                # Calculate complexity score based on task complexity
                file_complexity = sum(task.complexity for task in tasks) / len(tasks) if tasks else 0
                complexity_metrics["complexity_score"] += file_complexity
                
            except Exception as e:
                self.logger.warning(f"Could not analyze PRP file {prp_file}: {e}")
        
        # Calculate overall metrics
        complexity_metrics["complexity_score"] /= len(prp_files) if prp_files else 1
        complexity_metrics["estimated_duration"] = complexity_metrics["estimated_tasks"] * 0.5  # hours
        complexity_metrics["recommended_agents"] = min(
            self.max_agents, 
            max(2, complexity_metrics["estimated_tasks"] // 3)
        )
        
        execution.total_tasks = complexity_metrics["estimated_tasks"]
        execution.knowledge_graph["complexity_analysis"] = complexity_metrics
        
        self.logger.info(f"Basic complexity analysis: {complexity_metrics}")

    def _extract_overall_risk_level(self, risk_assessments) -> str:
        """Extract overall risk level from risk assessments."""
        if not risk_assessments:
            return "LOW"
        
        risk_levels = [risk.level.name for risk in risk_assessments]
        if "CRITICAL" in risk_levels:
            return "CRITICAL"
        elif "HIGH" in risk_levels:
            return "HIGH"
        elif "MEDIUM" in risk_levels:
            return "MEDIUM"
        else:
            return "LOW"

    async def _decompose_project_tasks(self, execution: OrchestrationExecution, 
                                     prp_files: List[str]) -> List[PRPTask]:
        """Decompose project into optimally sized tasks for agent execution."""
        self.logger.info("🔧 Decomposing project into executable tasks...")
        
        all_tasks = []
        task_counter = 1
        
        for prp_file in prp_files:
            try:
                goal, prp_tasks = self.base_coordinator.parse_prp_file(prp_file)
                
                # Enhance tasks with advanced metadata
                for task in prp_tasks:
                    # Add orchestration-specific metadata
                    task.priority = self._calculate_task_priority(task)
                    task.estimated_duration = self._estimate_task_duration(task)
                    task.resource_requirements = self._analyze_resource_requirements(task)
                    
                    # Update task ID for global uniqueness
                    task.id = f"task_{task_counter:04d}_{task.domain}"
                    task_counter += 1
                    
                    all_tasks.append(task)
                    
            except Exception as e:
                self.logger.error(f"Failed to decompose PRP file {prp_file}: {e}")
        
        self.logger.info(f"Decomposed project into {len(all_tasks)} executable tasks")
        return all_tasks

    def _calculate_task_priority(self, task: PRPTask) -> TaskPriority:
        """Calculate priority for a task based on complexity and dependencies."""
        # High priority for infrastructure and security tasks
        if any(keyword in task.description.lower() for keyword in 
               ["security", "authentication", "database", "infrastructure"]):
            return TaskPriority.HIGH
        
        # Critical priority for blocking tasks
        if any(keyword in task.description.lower() for keyword in 
               ["setup", "configure", "initialize"]):
            return TaskPriority.CRITICAL
        
        # Medium priority based on complexity
        if task.complexity >= 7:
            return TaskPriority.HIGH
        elif task.complexity >= 4:
            return TaskPriority.MEDIUM
        else:
            return TaskPriority.LOW

    def _estimate_task_duration(self, task: PRPTask) -> float:
        """Estimate task duration in hours based on complexity and domain."""
        base_duration = task.complexity * 0.25  # Base: 15 minutes per complexity point
        
        # Domain-specific adjustments
        domain_multipliers = {
            "security": 1.5,  # Security tasks take longer
            "database": 1.3,  # Database tasks require careful planning
            "performance": 1.4,  # Performance optimization is iterative
            "testing": 0.8,  # Testing is often more straightforward
            "documentation": 0.6  # Documentation is usually faster
        }
        
        multiplier = domain_multipliers.get(task.domain, 1.0)
        return base_duration * multiplier

    def _analyze_resource_requirements(self, task: PRPTask) -> Dict[str, Any]:
        """Analyze resource requirements for a task."""
        return {
            "cpu_intensive": task.complexity >= 8,
            "memory_intensive": "database" in task.domain or "performance" in task.domain,
            "network_intensive": "api" in task.description.lower() or "integration" in task.description.lower(),
            "requires_external_services": any(service in task.description.lower() 
                                           for service in ["database", "redis", "elasticsearch"])
        }

    async def _resolve_task_dependencies(self, execution: OrchestrationExecution, 
                                       tasks: List[PRPTask]):
        """Advanced dependency resolution including circular dependency detection."""
        self.logger.info("🔗 Resolving task dependencies...")
        
        # Build dependency graph
        dependency_graph = {}
        
        for i, task in enumerate(tasks):
            dependencies = []
            
            # Infrastructure dependencies (database before API)
            if task.domain in ["api", "backend", "frontend"]:
                for j in range(i):
                    if tasks[j].domain in ["database", "postgresql", "mongodb"]:
                        dependencies.append(TaskDependency(
                            dependent_task_id=task.id,
                            dependency_task_id=tasks[j].id,
                            dependency_type="sequential",
                            strength=0.9
                        ))
            
            # Security dependencies (authentication before protected features)
            if "protected" in task.description.lower() or "authenticated" in task.description.lower():
                for j in range(i):
                    if "auth" in tasks[j].description.lower() or "security" in tasks[j].domain:
                        dependencies.append(TaskDependency(
                            dependent_task_id=task.id,
                            dependency_task_id=tasks[j].id,
                            dependency_type="sequential",
                            strength=1.0
                        ))
            
            # Testing dependencies (implementation before tests)
            if "test" in task.description.lower():
                for j in range(i):
                    if ("implement" in tasks[j].description.lower() and 
                        task.domain == tasks[j].domain):
                        dependencies.append(TaskDependency(
                            dependent_task_id=task.id,
                            dependency_task_id=tasks[j].id,
                            dependency_type="sequential",
                            strength=0.8
                        ))
            
            dependency_graph[task.id] = dependencies
            task.dependencies = [dep.dependency_task_id for dep in dependencies]
        
        # Detect circular dependencies
        circular_deps = self._detect_circular_dependencies(dependency_graph)
        if circular_deps:
            self.logger.warning(f"⚠️ Circular dependencies detected: {circular_deps}")
            await self._resolve_circular_dependencies(circular_deps, tasks)
        
        self.task_dependencies = [dep for deps in dependency_graph.values() for dep in deps]
        self.logger.info(f"Resolved {len(self.task_dependencies)} task dependencies")

    def _detect_circular_dependencies(self, dependency_graph: Dict[str, List[TaskDependency]]) -> List[List[str]]:
        """Detect circular dependencies using depth-first search."""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(task_id: str, path: List[str]) -> bool:
            if task_id in rec_stack:
                cycle_start = path.index(task_id)
                cycles.append(path[cycle_start:] + [task_id])
                return True
            
            if task_id in visited:
                return False
            
            visited.add(task_id)
            rec_stack.add(task_id)
            
            for dep in dependency_graph.get(task_id, []):
                if dfs(dep.dependency_task_id, path + [task_id]):
                    return True
            
            rec_stack.remove(task_id)
            return False
        
        for task_id in dependency_graph:
            if task_id not in visited:
                dfs(task_id, [])
        
        return cycles

    async def _resolve_circular_dependencies(self, circular_deps: List[List[str]], 
                                           tasks: List[PRPTask]):
        """Resolve circular dependencies by breaking the weakest links."""
        for cycle in circular_deps:
            self.logger.info(f"Resolving circular dependency: {' -> '.join(cycle)}")
            
            # Find the weakest dependency in the cycle
            weakest_dep = None
            min_strength = float('inf')
            
            for dep in self.task_dependencies:
                if (dep.dependent_task_id in cycle and 
                    dep.dependency_task_id in cycle and 
                    dep.strength < min_strength):
                    weakest_dep = dep
                    min_strength = dep.strength
            
            if weakest_dep:
                # Remove the weakest dependency
                self.task_dependencies.remove(weakest_dep)
                
                # Update task dependencies
                for task in tasks:
                    if task.id == weakest_dep.dependent_task_id:
                        if weakest_dep.dependency_task_id in task.dependencies:
                            task.dependencies.remove(weakest_dep.dependency_task_id)
                
                self.logger.info(f"Broke circular dependency by removing: {weakest_dep.dependent_task_id} -> {weakest_dep.dependency_task_id}")

    async def _assign_agents_intelligently(self, execution: OrchestrationExecution, 
                                         tasks: List[PRPTask]):
        """Intelligent agent assignment based on performance history and specialization."""
        self.logger.info("🎯 Assigning agents intelligently...")
        
        # Create agent assignment optimization
        assignment_scores = {}
        
        for task in tasks:
            best_agent = None
            best_score = 0
            
            for agent_name, agent_capability in self.base_coordinator.agents.items():
                if self.agent_status[agent_name] == AgentStatus.OFFLINE:
                    continue
                
                # Calculate comprehensive assignment score
                score = self._calculate_comprehensive_agent_score(
                    agent_capability, task, agent_name
                )
                
                if score > best_score:
                    best_score = score
                    best_agent = agent_name
            
            if best_agent:
                task.assigned_agent = best_agent
                assignment_scores[task.id] = {
                    "agent": best_agent,
                    "score": best_score,
                    "reasoning": self._get_assignment_reasoning(task, best_agent)
                }
        
        # Update execution metrics
        execution.knowledge_graph["agent_assignments"] = assignment_scores
        execution.total_agents = len(set(task.assigned_agent for task in tasks if task.assigned_agent))
        
        self.logger.info(f"Assigned {len(assignment_scores)} tasks to {execution.total_agents} agents")

    def _calculate_comprehensive_agent_score(self, agent_capability: AgentCapability, 
                                           task: PRPTask, agent_name: str) -> float:
        """Calculate comprehensive agent assignment score including performance history."""
        # Base score from coordination system
        base_score = self.base_coordinator._calculate_agent_score(agent_capability, task)
        
        # Use learning system for ML-based recommendation if available
        if self.learning_system:
            try:
                ml_agent, ml_confidence = self.learning_system.get_agent_recommendation(
                    available_agents=[agent_name],
                    task_type=task.domain,
                    context={
                        'complexity_score': task.complexity / 10.0,
                        'urgency': 0.7 if hasattr(task, 'priority') and task.priority.name in ['HIGH', 'CRITICAL'] else 0.5,
                        'resource_requirements': 0.8 if task.complexity >= 7 else 0.5,
                        'agent_current_load': self.agent_performance[agent_name].current_load / agent_capability.max_concurrent_tasks,
                        'agent_success_rate': self.agent_performance[agent_name].success_rate
                    }
                )
                
                # Use ML confidence as a modifier
                ml_modifier = ml_confidence
                
            except Exception as e:
                self.logger.debug(f"ML recommendation failed: {e}")
                ml_modifier = 1.0
        else:
            ml_modifier = 1.0
        
        # Performance history adjustment
        performance = self.agent_performance[agent_name]
        performance_modifier = (
            performance.success_rate * 0.3 +
            min(performance.efficiency_rating, 2.0) * 0.2 +
            (1.0 - performance.current_load / agent_capability.max_concurrent_tasks) * 0.3 +
            performance.specialization_score * 0.2
        )
        
        # Task priority adjustment
        priority_multiplier = {
            TaskPriority.CRITICAL: 1.2,
            TaskPriority.HIGH: 1.1,
            TaskPriority.MEDIUM: 1.0,
            TaskPriority.LOW: 0.9
        }.get(getattr(task, 'priority', TaskPriority.MEDIUM), 1.0)
        
        final_score = base_score * performance_modifier * priority_multiplier * ml_modifier
        
        return final_score

    def _get_assignment_reasoning(self, task: PRPTask, agent_name: str) -> str:
        """Generate human-readable reasoning for agent assignment."""
        performance = self.agent_performance[agent_name]
        
        reasons = []
        
        if performance.success_rate > 0.9:
            reasons.append("high success rate")
        
        if performance.efficiency_rating > 1.2:
            reasons.append("above-average efficiency")
        
        if performance.current_load == 0:
            reasons.append("currently available")
        
        if performance.specialization_score > 0.8:
            reasons.append("domain expertise match")
        
        return f"Selected for {task.domain} task due to: {', '.join(reasons)}"

    async def _execute_with_monitoring(self, execution: OrchestrationExecution, 
                                     tasks: List[PRPTask]):
        """Execute tasks with real-time monitoring and dynamic optimization."""
        self.logger.info("🚀 Executing tasks with real-time monitoring...")
        
        # Start performance monitoring
        monitoring_task = asyncio.create_task(self._monitor_execution_performance(execution))
        
        try:
            # Use enhanced parallel execution from base coordinator
            await self._enhanced_parallel_execution(execution, tasks)
            
        finally:
            # Stop monitoring
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass

    async def _enhanced_parallel_execution(self, execution: OrchestrationExecution, 
                                         tasks: List[PRPTask]):
        """Enhanced parallel execution with dynamic reallocation."""
        running_tasks = {}
        completed = set()
        failed = set()
        
        while len(completed) + len(failed) < len(tasks):
            # Find ready tasks
            ready_tasks = [
                task for task in tasks
                if (task.id not in completed and 
                    task.id not in failed and
                    task.id not in running_tasks and
                    all(dep in completed for dep in task.dependencies))
            ]
            
            # Start new tasks
            while (len(running_tasks) < self.max_agents and ready_tasks):
                task = ready_tasks.pop(0)
                
                if task.assigned_agent and self.agent_status[task.assigned_agent] != AgentStatus.OFFLINE:
                    # Update agent status
                    self.agent_status[task.assigned_agent] = AgentStatus.BUSY
                    self.agent_performance[task.assigned_agent].current_load += 1
                    
                    # Start task execution
                    running_task = asyncio.create_task(self._execute_monitored_task(task, execution))
                    running_tasks[task.id] = running_task
                    
                    self.logger.info(f"Started task {task.id} with {task.assigned_agent}")
            
            # Wait for task completion
            if running_tasks:
                done, pending = await asyncio.wait(
                    running_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                for completed_task in done:
                    # Find task ID
                    task_id = None
                    for tid, t in running_tasks.items():
                        if t == completed_task:
                            task_id = tid
                            break
                    
                    if task_id:
                        task = next(t for t in tasks if t.id == task_id)
                        
                        # Update agent status
                        if task.assigned_agent:
                            self.agent_status[task.assigned_agent] = AgentStatus.IDLE
                            self.agent_performance[task.assigned_agent].current_load -= 1
                        
                        # Update execution status
                        if task.status == "completed":
                            completed.add(task_id)
                            execution.completed_tasks += 1
                            self._update_agent_performance_success(task)
                        else:
                            failed.add(task_id)
                            execution.failed_tasks += 1
                            self._update_agent_performance_failure(task)
                        
                        del running_tasks[task_id]
            
            await asyncio.sleep(0.1)

    async def _execute_monitored_task(self, task: PRPTask, execution: OrchestrationExecution) -> PRPTask:
        """Execute a single task with comprehensive monitoring and knowledge sharing."""
        start_time = datetime.now()
        
        try:
            # Query for relevant knowledge before execution
            await self._apply_relevant_knowledge(task)
            
            # Execute task using base coordinator
            result_task = await self.base_coordinator._execute_task(task, execution)
            
            # Record execution metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_task_execution(task, execution_time, True)
            
            # Share knowledge gained from successful execution
            await self._share_task_knowledge(task, execution_time, True)
            
            return result_task
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_task_execution(task, execution_time, False)
            
            # Share knowledge about failures too
            await self._share_task_knowledge(task, execution_time, False, str(e))
            
            task.status = "failed"
            task.error_message = str(e)
            raise

    def _record_task_execution(self, task: PRPTask, execution_time: float, success: bool):
        """Record task execution metrics for performance analysis."""
        if task.assigned_agent:
            performance = self.agent_performance[task.assigned_agent]
            
            # Update task counts
            if success:
                performance.tasks_completed += 1
            else:
                performance.tasks_failed += 1
            
            # Update success rate
            total_tasks = performance.tasks_completed + performance.tasks_failed
            performance.success_rate = performance.tasks_completed / total_tasks
            
            # Update average execution time
            if performance.average_execution_time == 0:
                performance.average_execution_time = execution_time
            else:
                performance.average_execution_time = (
                    performance.average_execution_time * 0.8 + execution_time * 0.2
                )
            
            # Update efficiency rating (compared to estimated duration)
            estimated_duration = getattr(task, 'estimated_duration', execution_time) * 3600  # Convert to seconds
            if estimated_duration > 0:
                efficiency = estimated_duration / execution_time
                performance.efficiency_rating = (
                    performance.efficiency_rating * 0.8 + efficiency * 0.2
                )
            
            # Record for learning system
            if self.learning_system:
                try:
                    from PRPs.scripts.learning_and_optimization_system import PerformanceMetric
                    
                    metric = PerformanceMetric(
                        agent_name=task.assigned_agent,
                        task_type=task.domain,
                        execution_time=execution_time,
                        success_rate=1.0 if success else 0.0,
                        resource_usage=performance.current_load / self.base_coordinator.agents[task.assigned_agent].max_concurrent_tasks,
                        complexity_score=task.complexity / 10.0,
                        timestamp=datetime.now(),
                        context={
                            'task_description': task.description[:100],
                            'concurrent_tasks': performance.current_load,
                            'agent_experience': performance.tasks_completed + performance.tasks_failed
                        }
                    )
                    
                    self.learning_system.record_performance_metric(metric)
                    
                except Exception as e:
                    self.logger.debug(f"Failed to record learning metric: {e}")
            
            performance.last_activity = datetime.now()

    def _update_agent_performance_success(self, task: PRPTask):
        """Update agent performance metrics after successful task completion."""
        if task.assigned_agent:
            performance = self.agent_performance[task.assigned_agent]
            
            # Increase specialization score for matching domain
            agent = self.base_coordinator.agents[task.assigned_agent]
            if task.domain in agent.domain_expertise:
                performance.specialization_score = min(1.0, performance.specialization_score + 0.1)

    def _update_agent_performance_failure(self, task: PRPTask):
        """Update agent performance metrics after task failure."""
        if task.assigned_agent:
            performance = self.agent_performance[task.assigned_agent]
            
            # Decrease specialization score slightly
            performance.specialization_score = max(0.0, performance.specialization_score - 0.05)
            
            # Mark agent as recovering if failure rate is high
            if performance.success_rate < 0.7:
                self.agent_status[task.assigned_agent] = AgentStatus.RECOVERING

    async def _monitor_execution_performance(self, execution: OrchestrationExecution):
        """Continuously monitor execution performance and optimize."""
        while True:
            try:
                # Collect current performance metrics
                current_metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "active_agents": sum(1 for status in self.agent_status.values() 
                                       if status == AgentStatus.BUSY),
                    "completed_tasks": execution.completed_tasks,
                    "failed_tasks": execution.failed_tasks,
                    "agent_performance": {
                        name: {
                            "success_rate": perf.success_rate,
                            "efficiency_rating": perf.efficiency_rating,
                            "current_load": perf.current_load
                        }
                        for name, perf in self.agent_performance.items()
                    }
                }
                
                self.performance_history.append(current_metrics)
                
                # Trigger optimization callbacks
                for callback in self.optimization_callbacks:
                    try:
                        await callback(current_metrics, execution)
                    except Exception as e:
                        self.logger.error(f"Optimization callback failed: {e}")
                
                # Monitor for performance issues and trigger optimizations
                await self._check_performance_issues(execution)
                
                # Wait before next monitoring cycle
                await asyncio.sleep(5)  # Monitor every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(10)  # Wait longer on error

    async def _check_performance_issues(self, execution: OrchestrationExecution):
        """Check for performance issues and trigger optimizations."""
        # Check for failing agents
        for agent_name, performance in self.agent_performance.items():
            if performance.success_rate < 0.5 and performance.tasks_completed > 2:
                self.logger.warning(f"⚠️ Agent {agent_name} has low success rate: {performance.success_rate:.2f}")
                self.agent_status[agent_name] = AgentStatus.RECOVERING
        
        # Check for overall execution performance
        if execution.failed_tasks > execution.completed_tasks * 0.2:
            self.logger.warning("⚠️ High failure rate detected - triggering optimization")
            await self._trigger_execution_optimization(execution)

    async def _trigger_execution_optimization(self, execution: OrchestrationExecution):
        """Trigger execution optimization based on performance issues."""
        optimization_actions = []
        
        # Identify underperforming agents
        underperforming_agents = [
            name for name, perf in self.agent_performance.items()
            if perf.success_rate < 0.7 and perf.tasks_completed > 1
        ]
        
        if underperforming_agents:
            optimization_actions.append(f"Reducing load for agents: {underperforming_agents}")
            for agent_name in underperforming_agents:
                self.base_coordinator.agents[agent_name].max_concurrent_tasks = max(
                    1, self.base_coordinator.agents[agent_name].max_concurrent_tasks - 1
                )
        
        # Record optimization
        optimization_record = {
            "timestamp": datetime.now().isoformat(),
            "trigger": "high_failure_rate",
            "actions": optimization_actions,
            "execution_id": execution.execution_id
        }
        
        execution.optimization_history.append(optimization_record)
        self.logger.info(f"🔧 Applied optimizations: {optimization_actions}")

    async def _analyze_execution_performance(self, execution: OrchestrationExecution):
        """Analyze execution performance and generate insights."""
        self.logger.info("📈 Analyzing execution performance...")
        
        # Calculate performance metrics
        total_duration = (execution.end_time - execution.start_time).total_seconds()
        success_rate = execution.completed_tasks / (execution.completed_tasks + execution.failed_tasks)
        
        # Analyze agent performance
        agent_analysis = {}
        for agent_name, performance in self.agent_performance.items():
            if performance.tasks_completed > 0 or performance.tasks_failed > 0:
                agent_analysis[agent_name] = {
                    "tasks_completed": performance.tasks_completed,
                    "tasks_failed": performance.tasks_failed,
                    "success_rate": performance.success_rate,
                    "efficiency_rating": performance.efficiency_rating,
                    "average_execution_time": performance.average_execution_time
                }
        
        # Generate performance insights
        insights = self._generate_performance_insights(execution, agent_analysis)
        
        # Update knowledge graph
        execution.knowledge_graph.update({
            "performance_metrics": {
                "total_duration": total_duration,
                "success_rate": success_rate,
                "agent_utilization": len(agent_analysis) / len(self.agent_performance),
                "optimization_count": len(execution.optimization_history)
            },
            "agent_analysis": agent_analysis,
            "performance_insights": insights
        })
        
        self.logger.info(f"Performance analysis complete: {len(insights)} insights generated")

    def _generate_performance_insights(self, execution: OrchestrationExecution, 
                                     agent_analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable performance insights from execution data."""
        insights = []
        
        # Agent performance insights
        top_performers = sorted(
            agent_analysis.items(),
            key=lambda x: x[1]["success_rate"] * x[1]["efficiency_rating"],
            reverse=True
        )[:3]
        
        if top_performers:
            insights.append(f"Top performing agents: {', '.join([name for name, _ in top_performers])}")
        
        # Efficiency insights
        avg_efficiency = sum(data["efficiency_rating"] for data in agent_analysis.values()) / len(agent_analysis)
        if avg_efficiency > 1.2:
            insights.append("Project completed faster than estimated - consider more aggressive scheduling")
        elif avg_efficiency < 0.8:
            insights.append("Project took longer than estimated - consider more realistic time estimates")
        
        # Failure pattern insights
        high_failure_agents = [
            name for name, data in agent_analysis.items()
            if data["success_rate"] < 0.8 and data["tasks_completed"] + data["tasks_failed"] > 2
        ]
        
        if high_failure_agents:
            insights.append(f"Agents with high failure rates need attention: {', '.join(high_failure_agents)}")
        
        # Optimization insights
        if len(execution.optimization_history) > 0:
            insights.append(f"Applied {len(execution.optimization_history)} performance optimizations during execution")
        
        return insights

    async def _apply_relevant_knowledge(self, task: PRPTask):
        """Query and apply relevant knowledge before task execution."""
        if not task.assigned_agent:
            return
        
        # Create knowledge query
        query = KnowledgeQuery(
            requesting_agent=task.assigned_agent,
            task_domain=task.domain,
            task_description=task.description,
            context={
                "complexity": task.complexity,
                "requirements": task.requirements,
                "task_id": task.id
            },
            knowledge_types=[KnowledgeType.SOLUTION, KnowledgeType.PATTERN, 
                           KnowledgeType.BEST_PRACTICE, KnowledgeType.OPTIMIZATION],
            max_results=5,
            min_relevance=0.4
        )
        
        # Get relevant knowledge
        relevant_knowledge = await self.knowledge_framework.query_knowledge(query)
        
        if relevant_knowledge:
            self.logger.info(f"🧠 Applied {len(relevant_knowledge)} knowledge items to task {task.id}")
            
            # Store knowledge context for potential reuse
            task.knowledge_context = {
                "applied_knowledge": [item.id for item in relevant_knowledge],
                "knowledge_sources": [item.source_agent for item in relevant_knowledge]
            }

    async def _share_task_knowledge(self, task: PRPTask, execution_time: float, 
                                  success: bool, error_message: str = None):
        """Share knowledge gained from task execution."""
        if not task.assigned_agent:
            return
        
        # Determine knowledge type based on outcome
        if success:
            if execution_time < getattr(task, 'estimated_duration', 3600) * 0.8:
                knowledge_type = KnowledgeType.OPTIMIZATION
                title = f"Efficient {task.domain} implementation"
            else:
                knowledge_type = KnowledgeType.SOLUTION
                title = f"Successful {task.domain} solution"
        else:
            knowledge_type = KnowledgeType.ERROR
            title = f"Common {task.domain} error pattern"
        
        # Prepare knowledge content
        content = {
            "task_complexity": task.complexity,
            "execution_time": execution_time,
            "approach": "TDD methodology with automated validation",
            "domain_specific_notes": f"Applied {task.domain} best practices"
        }
        
        if success:
            content["success_factors"] = [
                "Comprehensive test coverage",
                "Iterative development approach",
                "Domain expertise application"
            ]
        else:
            content["error_details"] = error_message
            content["potential_solutions"] = [
                "Review task complexity estimation",
                "Check dependency requirements",
                "Validate agent domain expertise match"
            ]
        
        # Prepare context
        context = {
            "project_phase": "implementation",
            "task_priority": getattr(task, 'priority', 'medium').name if hasattr(getattr(task, 'priority', None), 'name') else 'medium',
            "dependencies_count": len(task.dependencies),
            "agent_specialization": task.assigned_agent
        }
        
        # Add knowledge to the graph
        await self.knowledge_framework.share_knowledge(
            agent_name=task.assigned_agent,
            knowledge_type=knowledge_type,
            domain=task.domain,
            title=title,
            content=content,
            context=context,
            tags=[task.domain, "orchestration", "tdd", knowledge_type.value]
        )

    def get_real_time_status(self) -> Dict[str, Any]:
        """Get real-time status of the orchestration system with monitoring data."""
        # Get knowledge statistics
        knowledge_stats = self.knowledge_framework.get_knowledge_statistics()
        
        # Get monitoring dashboard if available
        monitoring_dashboard = None
        if self.monitoring_system:
            monitoring_dashboard = self.monitoring_system.get_real_time_dashboard()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "agent_status": {name: status.value for name, status in self.agent_status.items()},
            "agent_performance": {
                name: {
                    "tasks_completed": perf.tasks_completed,
                    "success_rate": perf.success_rate,
                    "current_load": perf.current_load,
                    "efficiency_rating": perf.efficiency_rating
                }
                for name, perf in self.agent_performance.items()
                if perf.tasks_completed > 0 or perf.tasks_failed > 0 or perf.current_load > 0
            },
            "system_metrics": {
                "total_agents": len(self.base_coordinator.agents),
                "active_agents": sum(1 for status in self.agent_status.values() 
                                   if status == AgentStatus.BUSY),
                "performance_history_size": len(self.performance_history)
            },
            "knowledge_graph": {
                "total_knowledge_items": knowledge_stats.get("total_items", 0),
                "knowledge_reuse_rate": knowledge_stats.get("usage_stats", {}).get("reuse_rate", 0.0),
                "top_knowledge_domains": list(knowledge_stats.get("domains", {}).keys())[:5]
            },
            "intelligent_analysis": {
                "analyzer_ready": self.project_analyzer is not None,
                "historical_projects": len(self.project_analyzer.historical_projects) if self.project_analyzer else 0,
                "complexity_patterns": len(self.project_analyzer.complexity_patterns) if self.project_analyzer else 0
            },
            "monitoring_system": {
                "active": self.monitoring_system is not None,
                "system_health": monitoring_dashboard.system_health if monitoring_dashboard else 1.0,
                "active_executions": monitoring_dashboard.active_executions if monitoring_dashboard else 0,
                "active_alerts": len(monitoring_dashboard.recent_alerts) if monitoring_dashboard else 0,
                "monitoring_enabled": True
            }
        }

    def add_optimization_callback(self, callback: Callable):
        """Add a callback function for performance optimization."""
        self.optimization_callbacks.append(callback)

    def generate_orchestration_report(self, execution: OrchestrationExecution) -> str:
        """Generate comprehensive orchestration report."""
        duration = execution.end_time - execution.start_time if execution.end_time else None
        
        report = f"""
# Multi-Agent Orchestration Report

## Executive Summary
- **Project**: {execution.project_name}
- **Execution ID**: {execution.execution_id}
- **Status**: {execution.status}
- **Duration**: {duration}
- **Total Tasks**: {execution.total_tasks}
- **Completed**: {execution.completed_tasks}
- **Failed**: {execution.failed_tasks}
- **Success Rate**: {execution.completed_tasks / (execution.completed_tasks + execution.failed_tasks) * 100:.1f}%

## Agent Performance
"""
        
        for agent_name, performance in self.agent_performance.items():
            if performance.tasks_completed > 0 or performance.tasks_failed > 0:
                report += f"""
### {agent_name}
- Tasks Completed: {performance.tasks_completed}
- Tasks Failed: {performance.tasks_failed}
- Success Rate: {performance.success_rate:.1%}
- Efficiency Rating: {performance.efficiency_rating:.2f}
- Average Execution Time: {performance.average_execution_time:.1f}s
"""
        
        # Add performance insights
        if "performance_insights" in execution.knowledge_graph:
            report += "\n## Performance Insights\n"
            for insight in execution.knowledge_graph["performance_insights"]:
                report += f"- {insight}\n"
        
        # Add optimization history
        if execution.optimization_history:
            report += "\n## Optimization History\n"
            for opt in execution.optimization_history:
                report += f"- {opt['timestamp']}: {', '.join(opt['actions'])}\n"
        
        return report


# Example usage and testing
async def main():
    """Example usage of the Multi-Agent Orchestrator."""
    orchestrator = MultiAgentOrchestrator(max_agents=5)
    
    # Add optimization callback
    async def sample_optimization_callback(metrics, execution):
        print(f"⚡ Performance update: {metrics['active_agents']} agents active, "
              f"{metrics['completed_tasks']} tasks completed")
    
    orchestrator.add_optimization_callback(sample_optimization_callback)
    
    # Example orchestration (would need actual PRP files)
    # execution = await orchestrator.orchestrate_project(
    #     project_dir="/path/to/project",
    #     prp_files=["prp1.md", "prp2.md"]
    # )
    
    # Get real-time status
    status = orchestrator.get_real_time_status()
    print(f"🔍 System Status: {json.dumps(status, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())