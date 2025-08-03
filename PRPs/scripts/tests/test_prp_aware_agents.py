"""
Test suite for PRP-aware agent functionality
Validates that enhanced agents can properly execute PRPs with TDD methodology
"""
import pytest
from pathlib import Path
import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from PRPs.scripts.validate_agent_enhancements import AgentEnhancementValidator


class TestPRPAwareAgents:
    """Test suite for PRP-aware agent capabilities"""
    
    @pytest.fixture
    def agents_dir(self):
        """Get the agents directory"""
        project_root = Path(__file__).parent.parent.parent.parent
        return project_root / ".claude" / "agents"
    
    @pytest.fixture
    def validator(self, agents_dir):
        """Create agent validator instance"""
        return AgentEnhancementValidator(agents_dir)
    
    @pytest.fixture
    def enhanced_agents(self):
        """List of agents that should be enhanced"""
        return [
            "code-reviewer",
            "performance-optimizer", 
            "refactoring-expert",
            "security-analyst",
            "test-writer",
            "python-specialist",
            "javascript-typescript-specialist",
            "go-specialist",
            "rust-specialist",
            "java-specialist",
            "react-specialist",
            "nextjs-specialist",
            "vuejs-specialist",
            "flutter-specialist",
            "docker-kubernetes-specialist",
            "aws-specialist"
        ]
    
    def test_enhanced_agents_have_prp_capabilities(self, validator, enhanced_agents, agents_dir):
        """Test that enhanced agents have PRP execution capabilities"""
        for agent_name in enhanced_agents:
            agent_file = agents_dir / f"{agent_name}.md"
            if agent_file.exists():
                result = validator.validate_single_agent(agent_file)
                assert result.has_prp_capabilities, f"{agent_name} missing PRP capabilities"
                assert result.has_tdd_integration, f"{agent_name} missing TDD integration"
                assert result.has_validation_loop, f"{agent_name} missing validation loop"
                assert result.has_autonomous_workflow, f"{agent_name} missing autonomous workflow"
    
    def test_enhanced_agents_have_consistent_structure(self, validator, enhanced_agents, agents_dir):
        """Test that enhanced agents follow consistent PRP structure"""
        required_sections = [
            "PRP Execution Capabilities",
            "PRP Structure Understanding",
            "TDD Methodology Integration",
            "4-Level Validation Loop",
            "Autonomous Execution Pattern",
            "Context-Aware Implementation",
            "Autonomous Workflow Integration"
        ]
        
        for agent_name in enhanced_agents:
            agent_file = agents_dir / f"{agent_name}.md"
            if agent_file.exists():
                content = agent_file.read_text(encoding='utf-8')
                for section in required_sections:
                    assert section in content, f"{agent_name} missing section: {section}"
    
    def test_tdd_phases_documented(self, enhanced_agents, agents_dir):
        """Test that TDD phases are properly documented"""
        tdd_phases = ["Red Phase", "Green Phase", "Refactor Phase"]
        
        for agent_name in enhanced_agents:
            agent_file = agents_dir / f"{agent_name}.md"
            if agent_file.exists():
                content = agent_file.read_text(encoding='utf-8')
                for phase in tdd_phases:
                    assert phase in content, f"{agent_name} missing TDD phase: {phase}"
    
    def test_validation_levels_documented(self, enhanced_agents, agents_dir):
        """Test that 4-level validation loop is properly documented"""
        validation_levels = ["Level 0", "Level 1", "Level 2", "Level 3", "Level 4"]
        
        for agent_name in enhanced_agents:
            agent_file = agents_dir / f"{agent_name}.md"
            if agent_file.exists():
                content = agent_file.read_text(encoding='utf-8')
                level_count = sum(1 for level in validation_levels if level in content)
                assert level_count >= 4, f"{agent_name} has insufficient validation levels: {level_count}/5"
    
    def test_autonomous_workflow_components(self, enhanced_agents, agents_dir):
        """Test that autonomous workflow components are documented"""
        workflow_components = [
            "Status Reporting",
            "Multi-Agent Coordination", 
            "Error Handling and Recovery",
            "Performance and Efficiency"
        ]
        
        for agent_name in enhanced_agents:
            agent_file = agents_dir / f"{agent_name}.md"
            if agent_file.exists():
                content = agent_file.read_text(encoding='utf-8')
                for component in workflow_components:
                    assert component in content, f"{agent_name} missing workflow component: {component}"
    
    def test_domain_specific_tools_identified(self, validator, enhanced_agents, agents_dir):
        """Test that domain-specific tools are identified for each agent"""
        for agent_name in enhanced_agents:
            agent_file = agents_dir / f"{agent_name}.md"
            if agent_file.exists():
                result = validator.validate_single_agent(agent_file)
                # Allow some flexibility for specialized agents
                if agent_name in ["python-specialist", "javascript-typescript-specialist", "go-specialist", "rust-specialist", "java-specialist"]:
                    assert result.domain_specific_tools_identified, f"{agent_name} missing domain-specific tools"
    
    def test_consistency_scores_acceptable(self, validator, enhanced_agents, agents_dir):
        """Test that enhanced agents have acceptable consistency scores"""
        min_consistency_score = 60.0  # Minimum acceptable consistency
        
        for agent_name in enhanced_agents:
            agent_file = agents_dir / f"{agent_name}.md"
            if agent_file.exists():
                result = validator.validate_single_agent(agent_file)
                assert result.consistency_score >= min_consistency_score, \
                    f"{agent_name} consistency score too low: {result.consistency_score:.1f}% < {min_consistency_score}%"
    
    def test_no_missing_critical_sections(self, validator, enhanced_agents, agents_dir):
        """Test that enhanced agents have no missing critical sections"""
        for agent_name in enhanced_agents:
            agent_file = agents_dir / f"{agent_name}.md"
            if agent_file.exists():
                result = validator.validate_single_agent(agent_file)
                critical_missing = [s for s in result.missing_sections if 
                                  any(critical in s for critical in 
                                      ["PRP Execution", "TDD Methodology", "Validation Loop", "Autonomous Workflow"])]
                assert len(critical_missing) == 0, \
                    f"{agent_name} missing critical sections: {critical_missing}"
    
    def test_agent_enhancement_template_exists(self):
        """Test that the agent enhancement template exists and is well-formed"""
        project_root = Path(__file__).parent.parent.parent.parent
        template_path = project_root / "PRPs" / "templates" / "prp_agent_enhancement_template.md"
        
        assert template_path.exists(), "Agent enhancement template missing"
        
        template_content = template_path.read_text(encoding='utf-8')
        required_template_sections = [
            "Enhancement Pattern Structure",
            "Domain-Specific TDD Integration Examples", 
            "Enhancement Implementation Checklist",
            "Quality Standards"
        ]
        
        for section in required_template_sections:
            assert section in template_content, f"Template missing section: {section}"
    
    def test_validation_script_functionality(self, validator, agents_dir):
        """Test that the validation script works correctly"""
        # Test validation of all agents
        summary = validator.validate_all_agents()
        
        assert 'total_agents' in summary
        assert 'fully_enhanced_agents' in summary
        assert 'enhancement_completion_percentage' in summary
        assert 'average_consistency_score' in summary
        
        assert summary['total_agents'] > 0, "No agents found"
        assert summary['enhancement_completion_percentage'] >= 0, "Invalid completion percentage"
        assert summary['average_consistency_score'] >= 0, "Invalid consistency score"
    
    @pytest.mark.parametrize("agent_name", [
        "python-specialist", 
        "javascript-typescript-specialist",
        "go-specialist",
        "rust-specialist", 
        "java-specialist",
        "react-specialist",
        "nextjs-specialist",
        "vuejs-specialist",
        "flutter-specialist",
        "docker-kubernetes-specialist",
        "aws-specialist"
    ])
    def test_specialists_have_framework_references(self, agent_name, agents_dir):
        """Test that language specialists reference appropriate testing frameworks"""
        agent_file = agents_dir / f"{agent_name}.md"
        if not agent_file.exists():
            pytest.skip(f"Agent file {agent_name}.md not found")
        
        content = agent_file.read_text(encoding='utf-8').lower()
        
        framework_mapping = {
            "python-specialist": ["pytest", "mypy", "ruff"],
            "javascript-typescript-specialist": ["jest", "eslint", "typescript"],
            "go-specialist": ["go test", "go fmt", "go vet"],
            "rust-specialist": ["cargo test", "rustfmt", "clippy"],
            "java-specialist": ["junit", "maven", "gradle"],
            "react-specialist": ["jest", "react testing library", "eslint"],
            "nextjs-specialist": ["jest", "playwright", "next lint"],
            "vuejs-specialist": ["vitest", "vue test utils", "cypress"],
            "flutter-specialist": ["flutter test", "dart analyze", "widget testing"],
            "docker-kubernetes-specialist": ["testcontainers", "hadolint", "kubernetes"],
            "aws-specialist": ["aws cdk", "localstack", "cloudformation"]
        }
        
        expected_frameworks = framework_mapping.get(agent_name, [])
        found_frameworks = [fw for fw in expected_frameworks if fw.lower() in content]
        
        assert len(found_frameworks) >= len(expected_frameworks) // 2, \
            f"{agent_name} missing key frameworks. Found: {found_frameworks}, Expected: {expected_frameworks}"


class TestPRPIntegration:
    """Test PRP integration capabilities"""
    
    @pytest.fixture
    def agents_dir(self):
        """Get the agents directory"""
        project_root = Path(__file__).parent.parent.parent.parent
        return project_root / ".claude" / "agents"
    
    def test_active_todos_integration_references(self, agents_dir):
        """Test that enhanced agents reference ACTIVE_TODOS.md integration"""
        enhanced_agents = [
            "code-reviewer", "performance-optimizer", "python-specialist",
            "javascript-typescript-specialist", "react-specialist"
        ]
        
        for agent_name in enhanced_agents:
            agent_file = agents_dir / f"{agent_name}.md"
            if agent_file.exists():
                content = agent_file.read_text(encoding='utf-8')
                assert "ACTIVE_TODOS.md" in content, f"{agent_name} missing ACTIVE_TODOS.md integration reference"
    
    def test_multi_agent_coordination_references(self, agents_dir):
        """Test that agents reference multi-agent coordination"""
        enhanced_agents = [
            "code-reviewer", "security-analyst", "python-specialist"
        ]
        
        for agent_name in enhanced_agents:
            agent_file = agents_dir / f"{agent_name}.md"
            if agent_file.exists():
                content = agent_file.read_text(encoding='utf-8')
                assert "Multi-Agent Coordination" in content, f"{agent_name} missing multi-agent coordination"
                # Should reference at least one other specialist
                specialist_references = [
                    "security-analyst", "performance-optimizer", "test-writer", 
                    "python-specialist", "api-design-specialist"
                ]
                has_specialist_ref = any(spec in content.lower() for spec in specialist_references)
                assert has_specialist_ref, f"{agent_name} doesn't reference other specialists"


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v", "--tb=short"])