#!/usr/bin/env python3
"""
PRP Execution Coordination System

This system coordinates PRP execution across multiple agents, managing:
- Agent selection and assignment
- Parallel execution coordination
- Context sharing between agents
- Progress tracking and reporting
- Error handling and recovery

Usage:
    python prp_coordination_system.py --prp-file prp-example.md
    python prp_coordination_system.py --prp-file prp-example.md --parallel --max-agents 3
"""

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PRPs.scripts.todo_parser import TodoParser
from PRPs.scripts.context_injector import ContextInjector


@dataclass
class AgentCapability:
    """Represents an agent's capabilities and expertise areas."""
    name: str
    domain_expertise: List[str]
    tools_available: List[str]
    complexity_rating: int  # 1-10 scale
    estimated_speed: float  # tasks per hour
    current_load: int = 0
    max_concurrent_tasks: int = 1


@dataclass
class PRPTask:
    """Represents a task extracted from a PRP that can be assigned to an agent."""
    id: str
    title: str
    description: str
    requirements: List[str]
    domain: str
    complexity: int
    dependencies: List[str] = field(default_factory=list)
    assigned_agent: Optional[str] = None
    status: str = "pending"  # pending, assigned, in_progress, completed, failed
    result: Optional[Dict[str, Any]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class PRPExecution:
    """Represents a complete PRP execution with all tasks and coordination."""
    prp_id: str
    prp_file: str
    goal: str
    total_tasks: int
    completed_tasks: int = 0
    failed_tasks: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, cancelled
    agents_involved: List[str] = field(default_factory=list)
    context_shared: Dict[str, Any] = field(default_factory=dict)


class PRPCoordinationSystem:
    """
    Coordinates PRP execution across multiple specialized agents.
    
    This system acts as a centralized coordinator that:
    1. Parses PRP files and extracts executable tasks
    2. Analyzes agent capabilities and selects optimal assignments
    3. Manages parallel execution and context sharing
    4. Tracks progress and handles errors
    5. Reports completion and generates summaries
    """

    def __init__(self, agents_dir: str = ".claude/agents", max_parallel: int = 3):
        self.agents_dir = Path(agents_dir)
        self.max_parallel = max_parallel
        self.logger = self._setup_logging()
        
        # Load agent capabilities
        self.agents = self._load_agent_capabilities()
        self.active_executions: Dict[str, PRPExecution] = {}
        self.task_queue: List[PRPTask] = []
        self.completed_tasks: List[PRPTask] = []
        
        # Context management
        self.context_injector = ContextInjector(str(project_root))
        self.shared_context: Dict[str, Any] = {}

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the coordination system."""
        logger = logging.getLogger("PRPCoordination")
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _load_agent_capabilities(self) -> Dict[str, AgentCapability]:
        """Load all enhanced agents and analyze their capabilities."""
        agents = {}
        
        # Define agent capabilities based on their domains
        agent_configs = {
            "python-specialist": {
                "domain_expertise": ["python", "backend", "api", "data"],
                "tools_available": ["pytest", "mypy", "ruff", "black"],
                "complexity_rating": 8,
                "estimated_speed": 2.5
            },
            "javascript-typescript-specialist": {
                "domain_expertise": ["javascript", "typescript", "nodejs", "frontend"],
                "tools_available": ["jest", "eslint", "prettier", "typescript"],
                "complexity_rating": 8,
                "estimated_speed": 2.5
            },
            "react-specialist": {
                "domain_expertise": ["react", "frontend", "ui", "components"],
                "tools_available": ["jest", "rtl", "storybook", "cypress"],
                "complexity_rating": 7,
                "estimated_speed": 2.0
            },
            "nextjs-specialist": {
                "domain_expertise": ["nextjs", "react", "ssr", "fullstack"],
                "tools_available": ["jest", "cypress", "playwright", "vercel"],
                "complexity_rating": 8,
                "estimated_speed": 2.0
            },
            "go-specialist": {
                "domain_expertise": ["go", "backend", "microservices", "performance"],
                "tools_available": ["go test", "golangci-lint", "bench"],
                "complexity_rating": 7,
                "estimated_speed": 3.0
            },
            "rust-specialist": {
                "domain_expertise": ["rust", "systems", "performance", "safety"],
                "tools_available": ["cargo test", "clippy", "rustfmt"],
                "complexity_rating": 9,
                "estimated_speed": 2.0
            },
            "postgresql-specialist": {
                "domain_expertise": ["postgresql", "database", "sql", "performance"],
                "tools_available": ["pgTAP", "pg_format", "explain"],
                "complexity_rating": 8,
                "estimated_speed": 2.5
            },
            "mongodb-specialist": {
                "domain_expertise": ["mongodb", "nosql", "aggregation", "scaling"],
                "tools_available": ["jest", "mongodb-memory-server", "compass"],
                "complexity_rating": 7,
                "estimated_speed": 2.5
            },
            "docker-kubernetes-specialist": {
                "domain_expertise": ["docker", "kubernetes", "devops", "deployment"],
                "tools_available": ["docker", "kubectl", "helm", "kind"],
                "complexity_rating": 8,
                "estimated_speed": 2.0
            },
            "security-analyst": {
                "domain_expertise": ["security", "audit", "vulnerability", "compliance"],
                "tools_available": ["bandit", "semgrep", "trivy", "owasp"],
                "complexity_rating": 9,
                "estimated_speed": 1.5
            },
            "performance-optimizer": {
                "domain_expertise": ["performance", "optimization", "profiling", "scaling"],
                "tools_available": ["profiler", "benchmark", "load-test"],
                "complexity_rating": 9,
                "estimated_speed": 1.5
            },
            "test-writer": {
                "domain_expertise": ["testing", "quality", "automation", "coverage"],
                "tools_available": ["pytest", "jest", "cypress", "coverage"],
                "complexity_rating": 6,
                "estimated_speed": 3.0
            }
        }
        
        for agent_name, config in agent_configs.items():
            agent_file = self.agents_dir / f"{agent_name}.md"
            if agent_file.exists():
                agents[agent_name] = AgentCapability(
                    name=agent_name,
                    **config
                )
        
        self.logger.info(f"Loaded {len(agents)} enhanced agents")
        return agents

    def parse_prp_file(self, prp_file: str) -> Tuple[str, List[PRPTask]]:
        """
        Parse a PRP file and extract executable tasks.
        
        Returns:
            Tuple of (goal, list of tasks)
        """
        prp_path = Path(prp_file)
        if not prp_path.exists():
            raise FileNotFoundError(f"PRP file not found: {prp_file}")
        
        content = prp_path.read_text()
        
        # Extract goal from PRP
        goal = self._extract_goal(content)
        
        # Extract tasks from implementation blueprint
        tasks = self._extract_tasks(content)
        
        self.logger.info(f"Parsed PRP: {goal}")
        self.logger.info(f"Extracted {len(tasks)} tasks")
        
        return goal, tasks

    def _extract_goal(self, content: str) -> str:
        """Extract the goal from PRP content."""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '## Goal' in line:
                # Get the next non-empty line
                for j in range(i + 1, len(lines)):
                    if lines[j].strip():
                        return lines[j].strip()
        return "Unknown Goal"

    def _extract_tasks(self, content: str) -> List[PRPTask]:
        """Extract tasks from the implementation blueprint section."""
        tasks = []
        lines = content.split('\n')
        
        in_blueprint = False
        task_counter = 1
        
        for line in lines:
            if '## Implementation Blueprint' in line:
                in_blueprint = True
                continue
            elif line.startswith('## ') and in_blueprint:
                break
            elif in_blueprint and line.strip().startswith('- '):
                # Extract task from bullet point
                task_desc = line.strip()[2:].strip()
                if task_desc:
                    domain = self._infer_domain(task_desc)
                    complexity = self._estimate_complexity(task_desc)
                    
                    task = PRPTask(
                        id=f"task_{task_counter:03d}",
                        title=task_desc[:50] + "..." if len(task_desc) > 50 else task_desc,
                        description=task_desc,
                        requirements=self._extract_requirements(task_desc),
                        domain=domain,
                        complexity=complexity
                    )
                    tasks.append(task)
                    task_counter += 1
        
        return tasks

    def _infer_domain(self, task_description: str) -> str:
        """Infer the domain/specialty for a task based on keywords."""
        desc_lower = task_description.lower()
        
        domain_keywords = {
            "python": ["python", "django", "flask", "fastapi", "pytest"],
            "javascript": ["javascript", "nodejs", "npm", "jest"],
            "typescript": ["typescript", "ts", "type"],
            "react": ["react", "jsx", "component", "hooks"],
            "nextjs": ["nextjs", "next.js", "ssr", "static"],
            "go": ["go", "golang", "goroutine"],
            "rust": ["rust", "cargo", "crate"],
            "database": ["database", "sql", "query", "schema", "migration"],
            "postgresql": ["postgresql", "postgres", "pgTAP"],
            "mongodb": ["mongodb", "mongo", "nosql", "aggregation"],
            "docker": ["docker", "container", "dockerfile"],
            "kubernetes": ["kubernetes", "k8s", "kubectl", "helm"],
            "security": ["security", "auth", "vulnerability", "audit"],
            "performance": ["performance", "optimize", "benchmark", "profile"],
            "testing": ["test", "testing", "coverage", "e2e", "unit"]
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in desc_lower for keyword in keywords):
                return domain
        
        return "general"

    def _estimate_complexity(self, task_description: str) -> int:
        """Estimate task complexity on a scale of 1-10."""
        desc_lower = task_description.lower()
        
        complexity_indicators = {
            "high": ["implement", "create", "build", "develop", "design", "architect"],
            "medium": ["update", "modify", "enhance", "refactor", "optimize"],
            "low": ["add", "fix", "remove", "configure", "setup"]
        }
        
        for level, keywords in complexity_indicators.items():
            if any(keyword in desc_lower for keyword in keywords):
                if level == "high":
                    return 7 + min(len([k for k in keywords if k in desc_lower]), 3)
                elif level == "medium":
                    return 4 + min(len([k for k in keywords if k in desc_lower]), 3)
                else:
                    return 1 + min(len([k for k in keywords if k in desc_lower]), 3)
        
        return 5  # Default medium complexity

    def _extract_requirements(self, task_description: str) -> List[str]:
        """Extract requirements from task description."""
        # Simple extraction - could be enhanced with NLP
        requirements = []
        desc_lower = task_description.lower()
        
        if "test" in desc_lower:
            requirements.append("testing")
        if "security" in desc_lower:
            requirements.append("security")
        if "performance" in desc_lower:
            requirements.append("performance")
        if "database" in desc_lower:
            requirements.append("database")
        
        return requirements

    def select_agent_for_task(self, task: PRPTask) -> Optional[str]:
        """
        Select the best agent for a given task based on:
        - Domain expertise match
        - Current workload
        - Complexity handling capability
        """
        best_agent = None
        best_score = 0
        
        for agent_name, agent in self.agents.items():
            if agent.current_load >= agent.max_concurrent_tasks:
                continue
            
            score = self._calculate_agent_score(agent, task)
            
            if score > best_score:
                best_score = score
                best_agent = agent_name
        
        if best_agent:
            self.logger.info(f"Selected {best_agent} for task {task.id} (score: {best_score:.2f})")
        
        return best_agent

    def _calculate_agent_score(self, agent: AgentCapability, task: PRPTask) -> float:
        """Calculate how well an agent matches a task."""
        score = 0.0
        
        # Domain expertise match (40% of score)
        domain_match = 0
        if task.domain in agent.domain_expertise:
            domain_match = 1.0
        elif any(domain in task.description.lower() for domain in agent.domain_expertise):
            domain_match = 0.5
        score += domain_match * 40
        
        # Complexity handling (30% of score)
        if agent.complexity_rating >= task.complexity:
            complexity_score = 1.0 - (task.complexity - agent.complexity_rating) / 10
        else:
            complexity_score = max(0, 0.5 - (task.complexity - agent.complexity_rating) * 0.1)
        score += complexity_score * 30
        
        # Availability/load (20% of score)
        availability = 1.0 - (agent.current_load / agent.max_concurrent_tasks)
        score += availability * 20
        
        # Speed (10% of score)
        speed_score = min(agent.estimated_speed / 3.0, 1.0)
        score += speed_score * 10
        
        return score

    async def execute_prp(self, prp_file: str, parallel: bool = True) -> PRPExecution:
        """
        Execute a complete PRP with task coordination.
        
        Args:
            prp_file: Path to the PRP file
            parallel: Whether to execute tasks in parallel
        
        Returns:
            PRPExecution with results
        """
        goal, tasks = self.parse_prp_file(prp_file)
        
        # Create execution record
        execution = PRPExecution(
            prp_id=f"prp_{int(time.time())}",
            prp_file=prp_file,
            goal=goal,
            total_tasks=len(tasks)
        )
        
        self.active_executions[execution.prp_id] = execution
        
        try:
            if parallel:
                await self._execute_parallel(execution, tasks)
            else:
                await self._execute_sequential(execution, tasks)
            
            execution.status = "completed"
            execution.end_time = datetime.now()
            
        except Exception as e:
            self.logger.error(f"PRP execution failed: {e}")
            execution.status = "failed"
            execution.end_time = datetime.now()
            raise
        
        return execution

    async def _execute_parallel(self, execution: PRPExecution, tasks: List[PRPTask]):
        """Execute tasks in parallel with coordination."""
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(tasks)
        
        # Track running tasks
        running_tasks: Dict[str, asyncio.Task] = {}
        completed: Set[str] = set()
        
        while len(completed) < len(tasks):
            # Find tasks ready to run
            ready_tasks = [
                task for task in tasks
                if (task.id not in completed and 
                    task.id not in running_tasks and
                    all(dep in completed for dep in task.dependencies))
            ]
            
            # Start new tasks up to parallel limit
            while (len(running_tasks) < self.max_parallel and 
                   ready_tasks and 
                   len(running_tasks) < len(ready_tasks)):
                
                task = ready_tasks.pop(0)
                agent_name = self.select_agent_for_task(task)
                
                if agent_name:
                    task.assigned_agent = agent_name
                    task.status = "assigned"
                    self.agents[agent_name].current_load += 1
                    
                    # Start task execution
                    running_task = asyncio.create_task(
                        self._execute_task(task, execution)
                    )
                    running_tasks[task.id] = running_task
                    
                    self.logger.info(f"Started task {task.id} with {agent_name}")
            
            # Wait for any task to complete
            if running_tasks:
                done, pending = await asyncio.wait(
                    running_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process completed tasks
                for task_result in done:
                    task_id = None
                    for tid, t in running_tasks.items():
                        if t == task_result:
                            task_id = tid
                            break
                    
                    if task_id:
                        completed.add(task_id)
                        del running_tasks[task_id]
                        
                        # Find the task and update execution
                        task = next(t for t in tasks if t.id == task_id)
                        if task.assigned_agent:
                            self.agents[task.assigned_agent].current_load -= 1
                        
                        if task.status == "completed":
                            execution.completed_tasks += 1
                        else:
                            execution.failed_tasks += 1
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.1)

    async def _execute_sequential(self, execution: PRPExecution, tasks: List[PRPTask]):
        """Execute tasks sequentially."""
        for task in tasks:
            agent_name = self.select_agent_for_task(task)
            
            if agent_name:
                task.assigned_agent = agent_name
                task.status = "assigned"
                
                await self._execute_task(task, execution)
                
                if task.status == "completed":
                    execution.completed_tasks += 1
                else:
                    execution.failed_tasks += 1

    async def _execute_task(self, task: PRPTask, execution: PRPExecution) -> PRPTask:
        """
        Execute a single task with an assigned agent.
        
        This is a simulation - in a real implementation, this would
        invoke the actual Claude Code agent with the task specification.
        """
        task.status = "in_progress"
        task.start_time = datetime.now()
        
        try:
            # Simulate task execution
            execution_time = max(0.5, task.complexity * 0.5)  # Simulate work
            await asyncio.sleep(execution_time)
            
            # Simulate success/failure based on complexity and agent capability
            agent = self.agents[task.assigned_agent]
            success_probability = min(0.95, agent.complexity_rating / task.complexity)
            
            import random
            if random.random() < success_probability:
                task.status = "completed"
                task.result = {
                    "success": True,
                    "files_modified": [f"src/{task.domain}/{task.id}.py"],
                    "tests_created": [f"tests/test_{task.id}.py"],
                    "execution_time": execution_time
                }
                self.logger.info(f"Task {task.id} completed successfully")
            else:
                task.status = "failed"
                task.error_message = f"Task complexity exceeded agent capability"
                self.logger.error(f"Task {task.id} failed: {task.error_message}")
                
        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            self.logger.error(f"Task {task.id} failed with exception: {e}")
        
        finally:
            task.end_time = datetime.now()
        
        return task

    def _build_dependency_graph(self, tasks: List[PRPTask]) -> Dict[str, List[str]]:
        """Build a dependency graph for tasks."""
        # For now, simple dependency inference based on task order and domain
        graph = {}
        
        for i, task in enumerate(tasks):
            dependencies = []
            
            # Simple rule: database tasks should come before API tasks
            if task.domain in ["api", "backend"] and i > 0:
                for j in range(i):
                    if tasks[j].domain in ["database", "postgresql", "mongodb"]:
                        dependencies.append(tasks[j].id)
            
            # Testing tasks depend on implementation tasks
            if "test" in task.description.lower() and i > 0:
                for j in range(i):
                    if "implement" in tasks[j].description.lower():
                        dependencies.append(tasks[j].id)
                        break
            
            task.dependencies = dependencies
            graph[task.id] = dependencies
        
        return graph

    def generate_execution_report(self, execution: PRPExecution) -> str:
        """Generate a detailed execution report."""
        duration = execution.end_time - execution.start_time if execution.end_time else None
        
        report = f"""
# PRP Execution Report

## Summary
- **PRP File**: {execution.prp_file}
- **Goal**: {execution.goal}
- **Status**: {execution.status}
- **Duration**: {duration}
- **Total Tasks**: {execution.total_tasks}
- **Completed**: {execution.completed_tasks}
- **Failed**: {execution.failed_tasks}
- **Success Rate**: {execution.completed_tasks / execution.total_tasks * 100:.1f}%

## Agents Involved
{', '.join(execution.agents_involved)}

## Task Details
"""
        # Add task details from completed_tasks list
        for task in self.completed_tasks:
            status_icon = "✅" if task.status == "completed" else "❌"
            report += f"- {status_icon} **{task.title}** ({task.assigned_agent})\n"
            if task.error_message:
                report += f"  - Error: {task.error_message}\n"
        
        return report

    def save_execution_results(self, execution: PRPExecution, output_dir: str = "PRPs/results"):
        """Save execution results to files."""
        results_dir = Path(output_dir)
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Save execution summary
        summary_file = results_dir / f"{execution.prp_id}_summary.json"
        summary_data = {
            "prp_id": execution.prp_id,
            "prp_file": execution.prp_file,
            "goal": execution.goal,
            "status": execution.status,
            "total_tasks": execution.total_tasks,
            "completed_tasks": execution.completed_tasks,
            "failed_tasks": execution.failed_tasks,
            "start_time": execution.start_time.isoformat(),
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "agents_involved": execution.agents_involved
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        # Save detailed report
        report_file = results_dir / f"{execution.prp_id}_report.md"
        with open(report_file, 'w') as f:
            f.write(self.generate_execution_report(execution))
        
        self.logger.info(f"Results saved to {results_dir}")


async def main():
    """Main entry point for the PRP coordination system."""
    parser = argparse.ArgumentParser(description="PRP Execution Coordination System")
    parser.add_argument("--prp-file", required=True, help="Path to PRP file to execute")
    parser.add_argument("--parallel", action="store_true", help="Execute tasks in parallel")
    parser.add_argument("--max-agents", type=int, default=3, help="Maximum parallel agents")
    parser.add_argument("--agents-dir", default=".claude/agents", help="Directory containing agent files")
    parser.add_argument("--output-dir", default="PRPs/results", help="Output directory for results")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize coordination system
    coordinator = PRPCoordinationSystem(
        agents_dir=args.agents_dir,
        max_parallel=args.max_agents
    )
    
    try:
        # Execute PRP
        print(f"🚀 Starting PRP execution: {args.prp_file}")
        execution = await coordinator.execute_prp(args.prp_file, parallel=args.parallel)
        
        # Save results
        coordinator.save_execution_results(execution, args.output_dir)
        
        # Print summary
        print(f"\n✅ PRP Execution Complete!")
        print(f"Status: {execution.status}")
        print(f"Tasks: {execution.completed_tasks}/{execution.total_tasks} completed")
        print(f"Success Rate: {execution.completed_tasks / execution.total_tasks * 100:.1f}%")
        
        if execution.failed_tasks > 0:
            print(f"⚠️  {execution.failed_tasks} tasks failed")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ PRP execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))