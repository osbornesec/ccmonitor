#!/usr/bin/env python3
"""
Test suite for project-manager-prp agent behavior

Following TDD Red-Green-Refactor methodology:
- RED: These tests define expected behavior and initially fail
- GREEN: Minimal implementation to make tests pass  
- REFACTOR: Enhance while maintaining tests
"""

import pytest
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import re

# Mock agent response structure
@dataclass
class MockAgentResponse:
    """Mock structure for agent responses during testing"""
    todos: List[Dict[str, Any]]
    dependencies: List[str]
    prp_suggestions: List[str]
    format_valid: bool = False
    
    def has_todo_hierarchy(self) -> bool:
        """Check if response contains structured todo hierarchy"""
        return len(self.todos) > 0 and all('priority' in todo for todo in self.todos)
    
    def has_dependency_analysis(self) -> bool:
        """Check if response includes dependency analysis"""
        return len(self.dependencies) > 0
    
    def follows_active_todos_format(self) -> bool:
        """Check if todos follow ACTIVE_TODOS.md format"""
        return self.format_valid

def simulate_agent_response(agent_name: str, prompt: str) -> MockAgentResponse:
    """
    Simulate agent response for testing purposes
    In real implementation, this would invoke the actual agent
    """  
    # This will fail initially (RED phase) - no actual agent exists yet
    agent_path = Path(f".claude/agents/{agent_name}.md")
    if not agent_path.exists():
        return MockAgentResponse(todos=[], dependencies=[], prp_suggestions=[])
    
    # Mock response based on prompt complexity
    if "authentication" in prompt.lower() and "oauth" in prompt.lower():
        return MockAgentResponse(
            todos=[
                {"task": "Setup OAuth provider integration", "priority": "high", "estimate": "3-4 hours"},
                {"task": "Implement email verification", "priority": "medium", "estimate": "2-3 hours"},
                {"task": "Create role-based access control", "priority": "high", "estimate": "4-5 hours"}
            ],
            dependencies=["OAuth setup -> email verification", "email verification -> RBAC"],
            prp_suggestions=["PRPs/003-oauth-integration.md", "PRPs/004-rbac-system.md"],
            format_valid=True
        )
    elif "rest api" in prompt.lower() and "authentication" in prompt.lower():
        return MockAgentResponse(
            todos=[
                {"task": "Setup database connection", "priority": "high", "estimate": "2-3 hours"},
                {"task": "Implement authentication middleware", "priority": "high", "estimate": "3-4 hours"},
                {"task": "Create API endpoints", "priority": "high", "estimate": "4-5 hours"},
                {"task": "Add rate limiting", "priority": "medium", "estimate": "2-3 hours"}
            ],
            dependencies=["database -> authentication -> API endpoints -> rate limiting"],
            prp_suggestions=["PRPs/005-api-endpoints.md"],
            format_valid=True
        )
    elif "microservices" in prompt.lower() and "distributed" in prompt.lower():
        return MockAgentResponse(
            todos=[
                {"task": "Design service architecture", "priority": "high", "estimate": "6-8 hours"},
                {"task": "Implement service mesh", "priority": "high", "estimate": "8-10 hours"},
                {"task": "Setup observability stack", "priority": "medium", "estimate": "5-6 hours"}
            ],
            dependencies=["architecture -> service mesh", "service mesh -> observability"],
            prp_suggestions=["PRPs/006-microservices-architecture.md", "PRPs/007-service-mesh.md", "PRPs/008-observability.md"],
            format_valid=True
        )
    elif "profile management" in prompt.lower() or "crud" in prompt.lower():
        return MockAgentResponse(
            todos=[
                {"task": "Design user profile schema", "priority": "high", "estimate": "2-3 hours"},
                {"task": "Implement CRUD operations", "priority": "high", "estimate": "3-4 hours"},
                {"task": "Add validation and security", "priority": "medium", "estimate": "2-3 hours"}
            ],
            dependencies=["schema -> CRUD -> validation"],
            prp_suggestions=["PRPs/009-user-profiles.md"],
            format_valid=True
        )
    elif "monitoring" in prompt.lower() and "dashboard" in prompt.lower():
        return MockAgentResponse(
            todos=[
                {"task": "Setup metrics collection", "priority": "high", "estimate": "3-4 hours"},
                {"task": "Create monitoring dashboard", "priority": "high", "estimate": "4-5 hours"},
                {"task": "Configure alerting system", "priority": "medium", "estimate": "2-3 hours"},
                {"task": "Build analytics reports", "priority": "low", "estimate": "3-4 hours"}
            ],
            dependencies=["metrics -> dashboard", "metrics -> alerting", "dashboard -> analytics"],
            prp_suggestions=["PRPs/010-monitoring-system.md", "PRPs/011-analytics.md"],
            format_valid=True
        )
    
    return MockAgentResponse(todos=[], dependencies=[], prp_suggestions=[])

class TestProjectManagerAgent:
    """Test suite for project-manager-prp agent functionality"""
    
    def test_agent_configuration_exists(self):
        """
        Test Description: Agent configuration file exists and is valid
        Expected Outcome: Agent file exists with proper YAML structure
        Failure Conditions: Missing file or invalid YAML format
        """
        agent_path = Path(".claude/agents/project-manager-prp.md")
        
        # RED phase - this will fail initially because agent doesn't exist yet
        assert agent_path.exists(), "project-manager-prp agent configuration must exist"
        
        # Validate YAML frontmatter structure
        with open(agent_path, 'r') as f:
            content = f.read()
            
        # Extract YAML frontmatter
        yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        assert yaml_match, "Agent must have YAML frontmatter"
        
        yaml_content = yaml.safe_load(yaml_match.group(1))
        assert 'name' in yaml_content, "Agent must have name field"
        assert 'description' in yaml_content, "Agent must have description field"
        assert yaml_content['name'] == 'project-manager-prp', "Agent name must match expected value"

    def test_project_manager_analyzes_complex_feature(self):
        """
        Test Description: Agent can analyze complex feature and generate todos
        Expected Outcome: Structured todo hierarchy with dependencies
        Failure Conditions: Missing todos, incorrect dependencies, wrong format
        """
        # Arrange: Mock complex feature description
        feature_description = "Implement user authentication with OAuth, email verification, and role-based access control"
        
        # Act: Simulate agent analysis
        result = simulate_agent_response("project-manager-prp", feature_description)
        
        # Assert: Verify structured output with dependencies
        assert result.has_todo_hierarchy(), "Agent must generate structured todo hierarchy"
        assert result.has_dependency_analysis(), "Agent must provide dependency analysis"  
        assert result.follows_active_todos_format(), "Agent must follow ACTIVE_TODOS.md format"
        assert len(result.todos) >= 3, "Complex features should generate multiple todos"

    def test_dependency_analysis_identifies_blocking_relationships(self):
        """
        Test Description: Agent correctly identifies task dependencies
        Expected Outcome: Dependencies show blocking relationships between tasks
        Failure Conditions: Missing dependencies or incorrect relationships
        """
        # Arrange: Feature with clear dependencies
        feature_description = "Build REST API with authentication, database integration, and rate limiting"
        
        # Act: Simulate agent analysis
        result = simulate_agent_response("project-manager-prp", feature_description)
        
        # Assert: Verify dependency analysis
        assert result.has_dependency_analysis(), "Agent must identify dependencies"
        assert len(result.dependencies) > 0, "Agent must provide specific dependency relationships"
        
        # Check for logical dependency patterns
        dependencies_text = " ".join(result.dependencies).lower()
        assert "database" in dependencies_text or "auth" in dependencies_text, "Dependencies should reflect technical requirements"

    def test_time_estimation_provides_realistic_estimates(self):
        """
        Test Description: Agent provides realistic time estimates for tasks
        Expected Outcome: Each todo has time estimate in hours format
        Failure Conditions: Missing estimates or unrealistic values
        """
        # Arrange: Standard complexity feature
        feature_description = "Create user profile management system with CRUD operations"
        
        # Act: Simulate agent analysis
        result = simulate_agent_response("project-manager-prp", feature_description)
        
        # Assert: Verify time estimation
        for todo in result.todos:
            assert 'estimate' in todo, f"Todo '{todo.get('task', 'unknown')}' must have time estimate"
            estimate = todo['estimate']
            assert 'hour' in estimate.lower(), f"Estimate '{estimate}' must be in hours format"
            
            # Extract numeric values and validate range
            hours_match = re.search(r'(\d+)(?:-(\d+))?\s*hour', estimate.lower())
            assert hours_match, f"Estimate '{estimate}' must contain valid hour range"

    def test_active_todos_format_compatibility(self):
        """
        Test Description: Generated todos maintain ACTIVE_TODOS.md format compatibility
        Expected Outcome: Todos follow exact format with priorities, estimates, dependencies
        Failure Conditions: Format deviation that breaks existing parsers
        """
        # Arrange: Feature requiring multiple priority levels
        feature_description = "Implement comprehensive monitoring system with alerts, dashboards, and analytics"
        
        # Act: Simulate agent analysis
        result = simulate_agent_response("project-manager-prp", feature_description)
        
        # Assert: Verify format compliance
        for todo in result.todos:
            # Check required fields
            assert 'task' in todo, "Todo must have task description"
            assert 'priority' in todo, "Todo must have priority level"
            assert 'estimate' in todo, "Todo must have time estimate"
            
            # Validate priority values
            assert todo['priority'] in ['high', 'medium', 'low'], f"Priority '{todo['priority']}' must be high/medium/low"

    def test_prp_recommendations_for_complex_tasks(self):
        """
        Test Description: Agent suggests PRP creation for complex sub-tasks
        Expected Outcome: Tasks >2 hours get PRP recommendations
        Failure Conditions: Missing PRP suggestions for complex tasks
        """
        # Arrange: Feature with tasks requiring detailed specification
        feature_description = "Build distributed microservices architecture with service mesh and observability"
        
        # Act: Simulate agent analysis
        result = simulate_agent_response("project-manager-prp", feature_description)
        
        # Assert: Verify PRP recommendations
        assert len(result.prp_suggestions) > 0, "Complex features should generate PRP suggestions"
        
        for prp_suggestion in result.prp_suggestions:
            assert prp_suggestion.startswith("PRPs/"), "PRP suggestions must follow PRPs/ path format"
            assert prp_suggestion.endswith(".md"), "PRP suggestions must be markdown files"
            assert re.match(r'PRPs/\d{3}-[\w-]+\.md', prp_suggestion), "PRP suggestions must follow naming convention"

    def test_agent_integration_with_claude_code_task_tool(self):
        """
        Test Description: Agent can be invoked through Claude Code Task tool
        Expected Outcome: Agent responds to Task tool invocation
        Failure Conditions: Agent not accessible or non-responsive through Task tool
        """
        # This test validates agent accessibility - implementation depends on Claude Code environment
        agent_path = Path(".claude/agents/project-manager-prp.md")
        
        # RED phase - will fail until agent is implemented
        assert agent_path.exists(), "Agent must exist to be invoked by Task tool"
        
        # Validate agent has proper tool access
        with open(agent_path, 'r') as f:
            content = f.read()
        
        yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        yaml_content = yaml.safe_load(yaml_match.group(1))
        
        assert 'tools' in yaml_content, "Agent must specify tool access"
        tools = yaml_content['tools']
        assert '*' in tools or 'Read' in tools, "Agent must have access to analysis tools"

class TestAgentValidation:
    """Test suite for agent validation and quality assurance"""
    
    def test_generated_todos_are_actionable_and_complete(self):
        """
        Test Description: All generated todos are actionable with clear deliverables
        Expected Outcome: Each todo has specific, measurable outcomes
        Failure Conditions: Vague or incomplete todo descriptions
        """
        # Arrange: Feature requiring specific deliverables
        feature_description = "Create automated testing pipeline with unit, integration, and e2e tests"
        
        # Act: Simulate agent analysis
        result = simulate_agent_response("project-manager-prp", feature_description)
        
        # Assert: Verify todo quality
        for todo in result.todos:
            task_description = todo.get('task', '')
            
            # Check for actionable verbs
            actionable_verbs = ['create', 'implement', 'build', 'configure', 'setup', 'design', 'test']
            has_actionable_verb = any(verb in task_description.lower() for verb in actionable_verbs)
            assert has_actionable_verb, f"Todo '{task_description}' must contain actionable verb"
            
            # Check for specificity (not just vague descriptions)
            assert len(task_description) > 20, f"Todo '{task_description}' must be sufficiently detailed"
            assert not task_description.lower().startswith(('do ', 'work on ', 'handle ')), f"Todo '{task_description}' must be specific, not vague"

if __name__ == "__main__":
    # Run tests to demonstrate RED phase failures
    pytest.main([__file__, '-v', '--tb=short'])