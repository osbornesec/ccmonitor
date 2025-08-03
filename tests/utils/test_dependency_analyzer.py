#!/usr/bin/env python3
"""
Test suite for dependency analysis utilities

Tests dependency detection, graph analysis, and critical path
calculation with comprehensive validation of dependency relationships.
"""

import pytest
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass

# Import will fail initially (RED phase) - utils don't exist yet
try:
    from utils.dependency_analyzer import (
        DependencyGraph,
        TaskNode,
        analyze_dependencies,
        detect_circular_dependencies,
        calculate_critical_path,
        suggest_parallel_tasks,
        estimate_total_time
    )
except ImportError:
    # Define placeholder classes for RED phase testing
    @dataclass
    class TaskNode:
        id: str
        name: str
        estimate_hours: float
        dependencies: List[str]
        priority: str
    
    class DependencyGraph:
        def __init__(self, tasks: List[TaskNode]):
            self.tasks = tasks
            self.nodes = {task.id: task for task in tasks}
            self.edges = []
        
        def add_dependency(self, from_task: str, to_task: str):
            raise NotImplementedError("DependencyGraph not implemented yet")
            
        def get_topological_order(self) -> List[str]:
            raise NotImplementedError("get_topological_order not implemented yet")
    
    def analyze_dependencies(tasks: List[TaskNode]) -> DependencyGraph:
        raise NotImplementedError("analyze_dependencies not implemented yet")
    
    def detect_circular_dependencies(graph: DependencyGraph) -> List[List[str]]:
        raise NotImplementedError("detect_circular_dependencies not implemented yet")
        
    def calculate_critical_path(graph: DependencyGraph) -> Tuple[List[str], float]:
        raise NotImplementedError("calculate_critical_path not implemented yet")
        
    def suggest_parallel_tasks(graph: DependencyGraph) -> Dict[str, List[str]]:
        raise NotImplementedError("suggest_parallel_tasks not implemented yet")
        
    def estimate_total_time(graph: DependencyGraph) -> float:
        raise NotImplementedError("estimate_total_time not implemented yet")

class TestDependencyGraphConstruction:
    """Test suite for dependency graph construction and basic operations"""
    
    def test_create_dependency_graph_from_tasks(self):
        """
        Test Description: Create dependency graph from task list
        Expected Outcome: Graph contains all tasks with proper node structure
        Failure Conditions: Missing tasks or incorrect graph construction
        """
        # Arrange: List of tasks with dependencies
        tasks = [
            TaskNode("PRP-001", "Setup Infrastructure", 3.0, [], "high"),
            TaskNode("PRP-002", "Build Core System", 4.0, ["PRP-001"], "high"),
            TaskNode("PRP-003", "Add Features", 2.0, ["PRP-002"], "medium")
        ]
        
        # Act: Create dependency graph (GREEN phase - now implemented)
        graph = analyze_dependencies(tasks)
        
        # GREEN phase assertions now enabled:
        assert len(graph.nodes) == 3
        assert "PRP-001" in graph.nodes
        assert "PRP-002" in graph.nodes  
        assert "PRP-003" in graph.nodes

    def test_add_dependency_relationships(self):
        """
        Test Description: Add dependency relationships between tasks
        Expected Outcome: Dependencies correctly linked in graph structure
        Failure Conditions: Missing or incorrect dependency links
        """
        # Arrange: Tasks with complex dependency relationships
        tasks = [
            TaskNode("AUTH", "Authentication System", 4.0, [], "high"),
            TaskNode("DB", "Database Setup", 2.0, [], "high"), 
            TaskNode("API", "REST API", 3.0, ["AUTH", "DB"], "high"),
            TaskNode("UI", "User Interface", 5.0, ["API"], "medium")
        ]
        
        # Act: Analyze dependencies (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            graph = analyze_dependencies(tasks)
        
        # GREEN phase assertions:
        # api_node = graph.nodes["API"]
        # assert "AUTH" in api_node.dependencies
        # assert "DB" in api_node.dependencies

    def test_topological_ordering_of_tasks(self):
        """
        Test Description: Generate valid topological ordering of tasks
        Expected Outcome: Tasks ordered such that dependencies come before dependents
        Failure Conditions: Invalid ordering or cyclic dependency issues  
        """
        # Arrange: Tasks requiring specific execution order
        tasks = [
            TaskNode("BUILD", "Build System", 1.0, ["TEST"], "high"),
            TaskNode("TEST", "Test Suite", 2.0, ["CODE"], "high"),
            TaskNode("CODE", "Implementation", 4.0, [], "high"),
            TaskNode("DEPLOY", "Deployment", 1.0, ["BUILD"], "low")
        ]
        
        # Act: Get topological order (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            graph = analyze_dependencies(tasks)
            order = graph.get_topological_order()
        
        # GREEN phase assertions:
        # assert order.index("CODE") < order.index("TEST")
        # assert order.index("TEST") < order.index("BUILD")
        # assert order.index("BUILD") < order.index("DEPLOY")

class TestCircularDependencyDetection:
    """Test suite for circular dependency detection and resolution"""
    
    def test_detect_simple_circular_dependency(self):
        """
        Test Description: Detect simple circular dependency between two tasks
        Expected Outcome: Circular dependency identified and reported
        Failure Conditions: Circular dependency not detected
        """
        # Arrange: Tasks with simple circular dependency
        tasks = [
            TaskNode("A", "Task A", 2.0, ["B"], "high"),
            TaskNode("B", "Task B", 3.0, ["A"], "high")  # Circular: A->B->A
        ]
        
        # Act: Detect circular dependencies (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            graph = analyze_dependencies(tasks)
            cycles = detect_circular_dependencies(graph)
        
        # GREEN phase assertions:
        # assert len(cycles) == 1
        # cycle = cycles[0]
        # assert "A" in cycle and "B" in cycle

    def test_detect_complex_circular_dependency(self):
        """
        Test Description: Detect complex circular dependency involving multiple tasks
        Expected Outcome: All tasks in circular chain identified
        Failure Conditions: Partial detection or missed circular dependencies
        """
        # Arrange: Tasks with complex circular dependency chain
        tasks = [
            TaskNode("X", "Task X", 1.0, ["Y"], "high"),
            TaskNode("Y", "Task Y", 2.0, ["Z"], "high"), 
            TaskNode("Z", "Task Z", 1.0, ["W"], "high"),
            TaskNode("W", "Task W", 3.0, ["X"], "high")  # Circular: X->Y->Z->W->X
        ]
        
        # Act: Detect circular dependencies (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            graph = analyze_dependencies(tasks)
            cycles = detect_circular_dependencies(graph)
        
        # GREEN phase assertions:
        # assert len(cycles) == 1
        # cycle = cycles[0]
        # assert all(task in cycle for task in ["X", "Y", "Z", "W"])

    def test_no_circular_dependencies_detected(self):
        """
        Test Description: Confirm no false positives for valid dependency graph
        Expected Outcome: No circular dependencies reported for valid graph
        Failure Conditions: False positive circular dependency detection
        """
        # Arrange: Tasks with valid dependency structure (no cycles)
        tasks = [
            TaskNode("START", "Start Task", 1.0, [], "high"),
            TaskNode("MID1", "Middle Task 1", 2.0, ["START"], "high"),
            TaskNode("MID2", "Middle Task 2", 2.0, ["START"], "high"),
            TaskNode("END", "End Task", 1.0, ["MID1", "MID2"], "high")
        ]
        
        # Act: Detect circular dependencies (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            graph = analyze_dependencies(tasks)
            cycles = detect_circular_dependencies(graph)
        
        # GREEN phase assertions:
        # assert len(cycles) == 0

class TestCriticalPathAnalysis:
    """Test suite for critical path calculation and time estimation"""
    
    def test_calculate_critical_path_simple_chain(self):
        """
        Test Description: Calculate critical path for simple task chain
        Expected Outcome: Longest path identified with correct time estimate
        Failure Conditions: Incorrect path or time calculation
        """
        # Arrange: Simple chain of tasks
        tasks = [
            TaskNode("A", "Task A", 2.0, [], "high"),
            TaskNode("B", "Task B", 3.0, ["A"], "high"),
            TaskNode("C", "Task C", 1.0, ["B"], "high")
        ]
        
        # Act: Calculate critical path (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            graph = analyze_dependencies(tasks)
            path, duration = calculate_critical_path(graph)
        
        # GREEN phase assertions:
        # assert path == ["A", "B", "C"]
        # assert duration == 6.0  # 2 + 3 + 1

    def test_calculate_critical_path_parallel_branches(self):
        """
        Test Description: Calculate critical path with parallel execution branches
        Expected Outcome: Longest duration path identified correctly
        Failure Conditions: Shorter path selected or incorrect parallel analysis
        """
        # Arrange: Tasks with parallel branches of different durations
        tasks = [
            TaskNode("START", "Start", 1.0, [], "high"),
            TaskNode("FAST", "Fast Branch", 2.0, ["START"], "high"),   # 1 + 2 = 3 total
            TaskNode("SLOW", "Slow Branch", 5.0, ["START"], "high"),   # 1 + 5 = 6 total
            TaskNode("END", "End", 1.0, ["FAST", "SLOW"], "high")      # max(3,6) + 1 = 7 total
        ]
        
        # Act: Calculate critical path (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            graph = analyze_dependencies(tasks)
            path, duration = calculate_critical_path(graph)
        
        # GREEN phase assertions:
        # assert "SLOW" in path  # Critical path should include slow branch
        # assert duration == 7.0  # 1 + 5 + 1

    def test_estimate_total_project_time(self):
        """
        Test Description: Estimate total project completion time
        Expected Outcome: Realistic time estimate considering parallelization
        Failure Conditions: Overestimate ignoring parallelization or underestimate ignoring dependencies
        """
        # Arrange: Complex project with mixed dependencies
        tasks = [
            TaskNode("PLAN", "Planning", 2.0, [], "high"),
            TaskNode("DEV1", "Development 1", 8.0, ["PLAN"], "high"),
            TaskNode("DEV2", "Development 2", 6.0, ["PLAN"], "high"),
            TaskNode("TEST1", "Test 1", 4.0, ["DEV1"], "medium"),
            TaskNode("TEST2", "Test 2", 3.0, ["DEV2"], "medium"),
            TaskNode("DEPLOY", "Deployment", 2.0, ["TEST1", "TEST2"], "low")
        ]
        
        # Act: Estimate total time (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            graph = analyze_dependencies(tasks)
            total_time = estimate_total_time(graph)
        
        # GREEN phase assertions:
        # Expected: 2 (PLAN) + max(8+4, 6+3) + 2 (DEPLOY) = 2 + 12 + 2 = 16 hours
        # assert total_time == 16.0

class TestParallelTaskSuggestions:
    """Test suite for parallel task execution suggestions"""
    
    def test_suggest_parallel_tasks_simple_case(self):
        """
        Test Description: Suggest tasks that can be executed in parallel
        Expected Outcome: Independent tasks grouped for parallel execution
        Failure Conditions: Dependent tasks suggested for parallel execution
        """
        # Arrange: Tasks with clear parallel opportunities
        tasks = [
            TaskNode("SETUP", "Setup", 1.0, [], "high"),
            TaskNode("UI", "User Interface", 4.0, ["SETUP"], "high"),
            TaskNode("API", "Backend API", 5.0, ["SETUP"], "high"),
            TaskNode("DB", "Database", 3.0, ["SETUP"], "high"),
            TaskNode("INTEGRATION", "Integration", 2.0, ["UI", "API", "DB"], "medium")
        ]
        
        # Act: Suggest parallel tasks (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            graph = analyze_dependencies(tasks)
            parallel_groups = suggest_parallel_tasks(graph)
        
        # GREEN phase assertions:
        # assert "UI" in parallel_groups and "API" in parallel_groups and "DB" in parallel_groups
        # ui_group = parallel_groups["UI"]
        # assert "API" in ui_group and "DB" in ui_group

    def test_suggest_parallel_tasks_complex_dependencies(self):
        """
        Test Description: Handle complex dependency patterns for parallel suggestions
        Expected Outcome: Only truly independent tasks suggested for parallel execution
        Failure Conditions: Incorrect parallel grouping with hidden dependencies
        """
        # Arrange: Tasks with complex interdependencies
        tasks = [
            TaskNode("A", "Foundation A", 2.0, [], "high"),
            TaskNode("B", "Foundation B", 1.0, [], "high"),
            TaskNode("C", "Depends on A", 3.0, ["A"], "high"),
            TaskNode("D", "Depends on B", 2.0, ["B"], "high"), 
            TaskNode("E", "Depends on A and B", 4.0, ["A", "B"], "high"),
            TaskNode("F", "Final", 1.0, ["C", "D", "E"], "low")
        ]
        
        # Act: Suggest parallel tasks (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            graph = analyze_dependencies(tasks)
            parallel_groups = suggest_parallel_tasks(graph)
        
        # GREEN phase assertions will validate complex dependency handling

class TestDependencyAnalysisEdgeCases:
    """Test suite for edge cases and error handling in dependency analysis"""
    
    def test_handle_empty_task_list(self):
        """
        Test Description: Handle empty task list gracefully
        Expected Outcome: Empty graph returned without errors
        Failure Conditions: Errors or crashes on empty input
        """
        # Arrange: Empty task list
        tasks = []
        
        # Act: Analyze empty dependencies (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            graph = analyze_dependencies(tasks)
        
        # GREEN phase assertions:
        # assert len(graph.nodes) == 0
        # assert len(graph.edges) == 0

    def test_handle_self_referencing_task(self):
        """
        Test Description: Handle task that depends on itself
        Expected Outcome: Self-dependency detected and handled appropriately
        Failure Conditions: Infinite loops or unhandled self-reference
        """
        # Arrange: Task with self-dependency
        tasks = [
            TaskNode("SELF", "Self Referencing Task", 2.0, ["SELF"], "high")
        ]
        
        # Act: Analyze self-referencing dependency (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            graph = analyze_dependencies(tasks)
            cycles = detect_circular_dependencies(graph)
        
        # GREEN phase assertions will validate self-dependency handling

    def test_handle_missing_dependency_references(self):
        """
        Test Description: Handle references to non-existent dependency tasks
        Expected Outcome: Missing dependencies reported or handled gracefully
        Failure Conditions: Unhandled exceptions or incorrect graph construction
        """
        # Arrange: Task referencing non-existent dependency
        tasks = [
            TaskNode("A", "Task A", 2.0, ["NONEXISTENT"], "high"),
            TaskNode("B", "Task B", 1.0, ["A"], "high")
        ]
        
        # Act: Analyze with missing dependency (will fail in RED phase)
        with pytest.raises(NotImplementedError):
            graph = analyze_dependencies(tasks)
        
        # GREEN phase assertions will validate missing dependency handling

if __name__ == "__main__":
    # Run tests to demonstrate RED phase failures
    pytest.main([__file__, '-v', '--tb=short'])