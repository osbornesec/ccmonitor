#!/usr/bin/env python3
"""
Dependency analysis utilities for project management

Provides dependency graph construction, cycle detection, critical path
analysis, and parallel task suggestions for project planning.
"""

import re
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque


@dataclass
class TaskNode:
    """Represents a task node in the dependency graph"""
    id: str
    name: str
    estimate_hours: float
    dependencies: List[str] = field(default_factory=list)
    priority: str = "medium"
    
    def __post_init__(self):
        if not self.dependencies:
            self.dependencies = []


class DependencyGraph:
    """Graph structure for analyzing task dependencies"""
    
    def __init__(self, tasks: List[TaskNode]):
        self.tasks = tasks
        self.nodes = {task.id: task for task in tasks}
        self.edges = []  # List of (from_id, to_id) tuples
        self._build_edges()
    
    def _build_edges(self):
        """Build edge list from task dependencies"""
        for task in self.tasks:
            for dep_id in task.dependencies:
                if dep_id in self.nodes:
                    self.edges.append((dep_id, task.id))
    
    def add_dependency(self, from_task: str, to_task: str):
        """Add dependency relationship between tasks"""
        if from_task in self.nodes and to_task in self.nodes:
            self.edges.append((from_task, to_task))
            if from_task not in self.nodes[to_task].dependencies:
                self.nodes[to_task].dependencies.append(from_task)
    
    def get_dependencies(self, task_id: str) -> List[str]:
        """Get list of task IDs that the given task depends on"""
        if task_id not in self.nodes:
            return []
        return self.nodes[task_id].dependencies.copy()
    
    def get_dependents(self, task_id: str) -> List[str]:
        """Get list of task IDs that depend on the given task"""
        dependents = []
        for from_id, to_id in self.edges:
            if from_id == task_id:
                dependents.append(to_id)
        return dependents
    
    def get_topological_order(self) -> List[str]:
        """Get topological ordering of tasks (dependencies first)"""
        # Kahn's algorithm for topological sorting
        in_degree = defaultdict(int)
        adj_list = defaultdict(list)
        
        # Build adjacency list and calculate in-degrees
        for task_id in self.nodes:
            in_degree[task_id] = 0
        
        for from_id, to_id in self.edges:
            adj_list[from_id].append(to_id)
            in_degree[to_id] += 1
        
        # Find tasks with no dependencies
        queue = deque([task_id for task_id in self.nodes if in_degree[task_id] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            # Remove edges and update in-degrees
            for neighbor in adj_list[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result


def analyze_dependencies(tasks: List[TaskNode]) -> DependencyGraph:
    """
    Create dependency graph from task list
    
    Args:
        tasks: List of TaskNode objects with dependency information
        
    Returns:
        DependencyGraph object for analysis
    """
    return DependencyGraph(tasks)


def detect_circular_dependencies(graph: DependencyGraph) -> List[List[str]]:
    """
    Detect circular dependencies in the task graph
    
    Args:
        graph: DependencyGraph to analyze
        
    Returns:
        List of cycles, where each cycle is a list of task IDs
    """
    cycles = []
    visited = set()
    rec_stack = set()
    
    def dfs(node_id: str, path: List[str]) -> bool:
        """DFS to detect cycles"""
        visited.add(node_id)
        rec_stack.add(node_id)
        current_path = path + [node_id]
        
        # Check all dependent tasks
        for dependent in graph.get_dependents(node_id):
            if dependent not in visited:
                if dfs(dependent, current_path):
                    return True
            elif dependent in rec_stack:
                # Found cycle - extract the cycle
                cycle_start = current_path.index(dependent)
                cycle = current_path[cycle_start:] + [dependent]
                cycles.append(cycle)
                return True
        
        rec_stack.remove(node_id)
        return False
    
    # Check each unvisited node
    for task_id in graph.nodes:
        if task_id not in visited:
            dfs(task_id, [])
    
    return cycles


def calculate_critical_path(graph: DependencyGraph) -> Tuple[List[str], float]:
    """
    Calculate the critical path (longest path) through the dependency graph
    
    Args:
        graph: DependencyGraph to analyze
        
    Returns:
        Tuple of (critical_path_task_ids, total_duration)
    """
    # Calculate earliest start times using topological order
    topo_order = graph.get_topological_order()
    earliest_start = {}
    earliest_finish = {}
    
    # Initialize start times
    for task_id in topo_order:
        task = graph.nodes[task_id]
        
        # Calculate earliest start (max of dependency finish times)
        deps = graph.get_dependencies(task_id)
        if not deps:
            earliest_start[task_id] = 0.0
        else:
            earliest_start[task_id] = max(
                earliest_finish.get(dep_id, 0.0) for dep_id in deps
            )
        
        # Calculate earliest finish
        earliest_finish[task_id] = earliest_start[task_id] + task.estimate_hours
    
    # Find the task with the latest finish time
    max_finish_time = max(earliest_finish.values()) if earliest_finish else 0.0
    end_tasks = [task_id for task_id, finish in earliest_finish.items() 
                 if finish == max_finish_time]
    
    # Backtrack to find critical path
    def find_critical_path(task_id: str) -> List[str]:
        """Backtrack to find critical path"""
        deps = graph.get_dependencies(task_id)
        if not deps:
            return [task_id]
        
        # Find the dependency that determines the earliest start
        critical_dep = None
        target_time = earliest_start[task_id]
        
        for dep_id in deps:
            if earliest_finish.get(dep_id, 0.0) == target_time:
                critical_dep = dep_id
                break
        
        if critical_dep:
            return find_critical_path(critical_dep) + [task_id]
        else:
            return [task_id]
    
    # Get critical path from one of the end tasks
    if end_tasks:
        critical_path = find_critical_path(end_tasks[0])
        return critical_path, max_finish_time
    else:
        return [], 0.0


def suggest_parallel_tasks(graph: DependencyGraph) -> Dict[str, List[str]]:
    """
    Suggest tasks that can be executed in parallel
    
    Args:
        graph: DependencyGraph to analyze
        
    Returns:
        Dictionary mapping task IDs to lists of tasks that can run in parallel
    """
    parallel_groups = {}
    topo_order = graph.get_topological_order()
    
    # Group tasks by their level in the dependency hierarchy
    levels = {}
    for task_id in topo_order:
        deps = graph.get_dependencies(task_id)
        if not deps:
            levels[task_id] = 0
        else:
            levels[task_id] = max(levels.get(dep_id, 0) for dep_id in deps) + 1
    
    # Group tasks by level - tasks at the same level can potentially run in parallel
    level_groups = defaultdict(list)
    for task_id, level in levels.items():
        level_groups[level].append(task_id)
    
    # For each task, find others at the same level that don't depend on each other
    for task_id in graph.nodes:
        task_level = levels[task_id]
        parallel_candidates = []
        
        for other_id in level_groups[task_level]:
            if other_id != task_id:
                # Check if there's any dependency relationship
                task_deps = set(graph.get_dependencies(task_id))
                other_deps = set(graph.get_dependencies(other_id))
                
                # Can run in parallel if no direct dependency relationship
                if (other_id not in task_deps and task_id not in other_deps):
                    parallel_candidates.append(other_id)
        
        if parallel_candidates:
            parallel_groups[task_id] = parallel_candidates
    
    return parallel_groups


def estimate_total_time(graph: DependencyGraph) -> float:
    """
    Estimate total project completion time considering parallelization
    
    Args:
        graph: DependencyGraph to analyze
        
    Returns:
        Estimated total time in hours
    """
    _, duration = calculate_critical_path(graph)
    return duration


def validate_dependencies(graph: DependencyGraph) -> Dict[str, List[str]]:
    """
    Validate dependency graph and return issues found
    
    Args:
        graph: DependencyGraph to validate
        
    Returns:
        Dictionary of validation issues keyed by issue type
    """
    issues = {
        'missing_dependencies': [],
        'circular_dependencies': [],
        'self_dependencies': [],
        'orphaned_tasks': []
    }
    
    # Check for missing dependency references
    for task in graph.tasks:
        for dep_id in task.dependencies:
            if dep_id not in graph.nodes:
                issues['missing_dependencies'].append(f"{task.id} -> {dep_id}")
    
    # Check for circular dependencies
    cycles = detect_circular_dependencies(graph)
    for cycle in cycles:
        issues['circular_dependencies'].append(" -> ".join(cycle))
    
    # Check for self-dependencies
    for task in graph.tasks:
        if task.id in task.dependencies:
            issues['self_dependencies'].append(task.id)
    
    # Check for orphaned tasks (no dependencies and no dependents)
    for task_id in graph.nodes:
        deps = graph.get_dependencies(task_id)
        dependents = graph.get_dependents(task_id)
        if not deps and not dependents and len(graph.nodes) > 1:
            issues['orphaned_tasks'].append(task_id)
    
    return issues


def optimize_task_order(graph: DependencyGraph, priority_weights: Dict[str, float] = None) -> List[str]:
    """
    Optimize task execution order considering dependencies and priorities
    
    Args:
        graph: DependencyGraph to optimize
        priority_weights: Optional priority weights {'high': 3.0, 'medium': 2.0, 'low': 1.0}
        
    Returns:
        Optimized list of task IDs in execution order
    """
    if priority_weights is None:
        priority_weights = {'high': 3.0, 'medium': 2.0, 'low': 1.0}
    
    # Get basic topological order
    topo_order = graph.get_topological_order()
    
    # Group tasks by dependency level
    levels = {}
    for task_id in topo_order:
        deps = graph.get_dependencies(task_id)
        if not deps:
            levels[task_id] = 0
        else:
            levels[task_id] = max(levels.get(dep_id, 0) for dep_id in deps) + 1
    
    # Within each level, sort by priority and impact
    level_groups = defaultdict(list)
    for task_id, level in levels.items():
        level_groups[level].append(task_id)
    
    optimized_order = []
    for level in sorted(level_groups.keys()):
        # Sort tasks within level by priority weight (high priority first)
        level_tasks = level_groups[level]
        level_tasks.sort(key=lambda tid: (
            -priority_weights.get(graph.nodes[tid].priority, 1.0),  # Higher priority first
            -graph.nodes[tid].estimate_hours,  # Longer tasks first (if same priority)
            tid  # Stable sort by ID
        ))
        optimized_order.extend(level_tasks)
    
    return optimized_order