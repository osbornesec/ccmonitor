"""
Agent enhancement validation script
Validates that all agents are properly enhanced with PRP capabilities and TDD integration
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any
import argparse
import json
from dataclasses import dataclass


@dataclass
class AgentValidationResult:
    """Results of agent enhancement validation"""
    agent_name: str
    has_prp_capabilities: bool
    has_tdd_integration: bool
    has_validation_loop: bool
    has_autonomous_workflow: bool
    domain_specific_tools_identified: bool
    consistency_score: float
    missing_sections: List[str]
    recommendations: List[str]


class AgentEnhancementValidator:
    """Validates agent enhancement consistency and completeness"""
    
    REQUIRED_SECTIONS = [
        "PRP Execution Capabilities",
        "TDD Methodology Integration", 
        "4-Level Validation Loop",
        "Autonomous Workflow Integration"
    ]
    
    REQUIRED_SUBSECTIONS = [
        "PRP Structure Understanding",
        "Context-Aware Implementation",
        "Status Reporting",
        "Error Handling and Recovery"
    ]
    
    def __init__(self, agents_dir: Path):
        """Initialize validator with agents directory"""
        self.agents_dir = Path(agents_dir)
        self.validation_results: List[AgentValidationResult] = []
        
    def validate_all_agents(self) -> Dict[str, Any]:
        """Validate all agents in the directory"""
        agent_files = list(self.agents_dir.glob("*.md"))
        agent_files = [f for f in agent_files if not f.name.startswith('meta-')]  # Skip meta-agent
        
        print(f"Validating {len(agent_files)} agent files...")
        
        results = []
        for agent_file in agent_files:
            result = self.validate_single_agent(agent_file)
            results.append(result)
            self.validation_results.append(result)
        
        # Generate summary statistics
        summary = self._generate_summary(results)
        return summary
    
    def validate_single_agent(self, agent_file: Path) -> AgentValidationResult:
        """Validate a single agent file"""
        agent_name = agent_file.stem
        content = agent_file.read_text(encoding='utf-8')
        
        # Check for required sections
        has_prp = self._check_section(content, "PRP Execution Capabilities")
        has_tdd = self._check_section(content, "TDD Methodology Integration")
        has_validation = self._check_section(content, "4-Level Validation Loop")
        has_workflow = self._check_section(content, "Autonomous Workflow Integration")
        
        # Check for domain-specific tool identification
        has_domain_tools = self._check_domain_tools(content, agent_name)
        
        # Calculate consistency score
        consistency_score = self._calculate_consistency_score(content)
        
        # Identify missing sections
        missing_sections = []
        for section in self.REQUIRED_SECTIONS:
            if not self._check_section(content, section):
                missing_sections.append(section)
        
        for subsection in self.REQUIRED_SUBSECTIONS:
            if not self._check_section(content, subsection):
                missing_sections.append(subsection)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            agent_name, content, missing_sections
        )
        
        return AgentValidationResult(
            agent_name=agent_name,
            has_prp_capabilities=has_prp,
            has_tdd_integration=has_tdd,
            has_validation_loop=has_validation,
            has_autonomous_workflow=has_workflow,
            domain_specific_tools_identified=has_domain_tools,
            consistency_score=consistency_score,
            missing_sections=missing_sections,
            recommendations=recommendations
        )
    
    def _check_section(self, content: str, section_name: str) -> bool:
        """Check if a section exists in the content"""
        # Use regex to match section headers
        patterns = [
            f"## {re.escape(section_name)}",
            f"### {re.escape(section_name)}",
            f"#### {re.escape(section_name)}"
        ]
        
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        # Also check for inline mentions
        return section_name.lower() in content.lower()
    
    def _check_domain_tools(self, content: str, agent_name: str) -> bool:
        """Check if domain-specific tools are identified"""
        domain_tool_patterns = {
            'python-specialist': ['pytest', 'mypy', 'ruff', 'black'],
            'javascript-typescript-specialist': ['jest', 'eslint', 'prettier', 'typescript'],
            'react-specialist': ['jest', 'react testing library', 'eslint', 'typescript'],
            'go-specialist': ['go test', 'gofmt', 'golint', 'go vet'],
            'rust-specialist': ['cargo test', 'rustfmt', 'clippy', 'cargo'],
            'java-specialist': ['junit', 'maven', 'gradle', 'checkstyle'],
            'docker-kubernetes-specialist': ['docker', 'kubectl', 'helm', 'hadolint'],
            'postgresql-specialist': ['psql', 'pgbench', 'pg_dump', 'pg_restore'],
            'api-design-specialist': ['postman', 'swagger', 'openapi', 'curl'],
            'aws-specialist': ['aws cli', 'cloudformation', 'terraform', 'sam'],
            'security-analyst': ['bandit', 'safety', 'trivy', 'nmap'],
            'performance-optimizer': ['profiler', 'benchmark', 'flamegraph', 'perf']
        }
        
        if agent_name not in domain_tool_patterns:
            return True  # No specific tools defined for this agent
        
        expected_tools = domain_tool_patterns[agent_name]
        content_lower = content.lower()
        
        found_tools = sum(1 for tool in expected_tools if tool.lower() in content_lower)
        return found_tools >= len(expected_tools) // 2  # At least half of expected tools
    
    def _calculate_consistency_score(self, content: str) -> float:
        """Calculate consistency score based on standard patterns"""
        score = 0.0
        max_score = 10.0
        
        # Check for TDD phases
        if 'red phase' in content.lower(): score += 1.0
        if 'green phase' in content.lower(): score += 1.0  
        if 'refactor phase' in content.lower(): score += 1.0
        
        # Check for validation levels
        for level in range(5):  # Levels 0-4
            if f'level {level}' in content.lower(): score += 0.5
        
        # Check for autonomous execution patterns
        if 'autonomous execution' in content.lower(): score += 1.0
        if 'status reporting' in content.lower(): score += 1.0
        if 'error handling' in content.lower(): score += 1.0
        
        # Check for context awareness
        if 'context-aware' in content.lower(): score += 1.0
        if 'codebase patterns' in content.lower(): score += 1.0
        
        return min(score / max_score * 100, 100.0)
    
    def _generate_recommendations(self, agent_name: str, content: str, 
                                missing_sections: List[str]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if missing_sections:
            recommendations.append(
                f"Add missing sections: {', '.join(missing_sections[:3])}"
            )
        
        if 'red phase' not in content.lower():
            recommendations.append("Add explicit TDD Red Phase documentation")
            
        if 'green phase' not in content.lower():
            recommendations.append("Add explicit TDD Green Phase documentation")
            
        if 'refactor phase' not in content.lower():
            recommendations.append("Add explicit TDD Refactor Phase documentation")
        
        # Domain-specific recommendations
        domain_recommendations = {
            'python-specialist': "Include pytest, mypy, ruff in validation loop",
            'react-specialist': "Include Jest, RTL, TypeScript in testing approach",
            'api-design-specialist': "Include OpenAPI validation and load testing",
            'security-analyst': "Include security scanning tools and threat modeling"
        }
        
        if agent_name in domain_recommendations:
            tool_content = content.lower()
            if not any(tool in tool_content for tool in ['pytest', 'jest', 'test']):
                recommendations.append(domain_recommendations[agent_name])
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _generate_summary(self, results: List[AgentValidationResult]) -> Dict[str, Any]:
        """Generate validation summary statistics"""
        total_agents = len(results)
        
        prp_capable = sum(1 for r in results if r.has_prp_capabilities)
        tdd_integrated = sum(1 for r in results if r.has_tdd_integration)
        validation_loops = sum(1 for r in results if r.has_validation_loop)
        autonomous_ready = sum(1 for r in results if r.has_autonomous_workflow)
        
        avg_consistency = sum(r.consistency_score for r in results) / total_agents if total_agents > 0 else 0
        
        fully_enhanced = sum(1 for r in results if (
            r.has_prp_capabilities and 
            r.has_tdd_integration and 
            r.has_validation_loop and 
            r.has_autonomous_workflow
        ))
        
        return {
            'total_agents': total_agents,
            'prp_capable_agents': prp_capable,
            'tdd_integrated_agents': tdd_integrated,
            'validation_loop_agents': validation_loops,
            'autonomous_ready_agents': autonomous_ready,
            'fully_enhanced_agents': fully_enhanced,
            'average_consistency_score': round(avg_consistency, 2),
            'enhancement_completion_percentage': round(fully_enhanced / total_agents * 100, 2) if total_agents > 0 else 0,
            'agents_needing_work': [r.agent_name for r in results if not (
                r.has_prp_capabilities and r.has_tdd_integration and 
                r.has_validation_loop and r.has_autonomous_workflow
            )]
        }
    
    def generate_report(self, output_file: Path = None) -> str:
        """Generate detailed validation report"""
        if not self.validation_results:
            return "No validation results available. Run validate_all_agents() first."
        
        summary = self._generate_summary(self.validation_results)
        
        report = f"""# Agent Enhancement Validation Report

## Summary Statistics
- **Total Agents**: {summary['total_agents']}
- **Fully Enhanced**: {summary['fully_enhanced_agents']} ({summary['enhancement_completion_percentage']}%)
- **Average Consistency Score**: {summary['average_consistency_score']}/100

## Enhancement Status Breakdown
- **PRP Capable**: {summary['prp_capable_agents']}/{summary['total_agents']}
- **TDD Integrated**: {summary['tdd_integrated_agents']}/{summary['total_agents']}
- **Validation Loops**: {summary['validation_loop_agents']}/{summary['total_agents']}
- **Autonomous Ready**: {summary['autonomous_ready_agents']}/{summary['total_agents']}

## Agents Needing Enhancement
"""
        
        if summary['agents_needing_work']:
            for agent_name in summary['agents_needing_work']:
                result = next(r for r in self.validation_results if r.agent_name == agent_name)
                report += f"\n### {agent_name}\n"
                report += f"- **Missing Sections**: {', '.join(result.missing_sections[:3]) if result.missing_sections else 'None'}\n"
                report += f"- **Consistency Score**: {result.consistency_score:.1f}/100\n"
                if result.recommendations:
                    report += f"- **Recommendations**: {result.recommendations[0]}\n"
        else:
            report += "\n✅ All agents are fully enhanced!\n"
        
        report += f"""
## Detailed Agent Analysis

| Agent | PRP | TDD | Validation | Autonomous | Consistency | Status |
|-------|-----|-----|------------|------------|-------------|--------|
"""
        
        for result in sorted(self.validation_results, key=lambda x: x.consistency_score, reverse=True):
            prp_icon = "✅" if result.has_prp_capabilities else "❌"
            tdd_icon = "✅" if result.has_tdd_integration else "❌"
            val_icon = "✅" if result.has_validation_loop else "❌"
            auto_icon = "✅" if result.has_autonomous_workflow else "❌"
            
            fully_enhanced = all([
                result.has_prp_capabilities, 
                result.has_tdd_integration,
                result.has_validation_loop, 
                result.has_autonomous_workflow
            ])
            status = "✅ Complete" if fully_enhanced else "🔄 In Progress"
            
            report += f"| {result.agent_name} | {prp_icon} | {tdd_icon} | {val_icon} | {auto_icon} | {result.consistency_score:.1f}% | {status} |\n"
        
        if output_file:
            output_file.write_text(report, encoding='utf-8')
            print(f"Report saved to: {output_file}")
        
        return report


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(description='Validate agent enhancements')
    parser.add_argument('--agents-dir', default='.claude/agents', 
                       help='Directory containing agent files')
    parser.add_argument('--output', help='Output report file')
    parser.add_argument('--check-consistency', action='store_true',
                       help='Check consistency across all agents')
    parser.add_argument('--agent', help='Validate specific agent only') 
    parser.add_argument('--json', action='store_true',
                       help='Output results as JSON')
    
    args = parser.parse_args()
    
    # Determine project root and agents directory
    project_root = Path(__file__).parent.parent.parent
    agents_dir = project_root / args.agents_dir
    
    if not agents_dir.exists():
        print(f"ERROR: Agents directory not found: {agents_dir}")
        return 1
    
    validator = AgentEnhancementValidator(agents_dir)
    
    if args.agent:
        # Validate single agent
        agent_file = agents_dir / f"{args.agent}.md"
        if not agent_file.exists():
            print(f"ERROR: Agent file not found: {agent_file}")
            return 1
        
        result = validator.validate_single_agent(agent_file)
        
        if args.json:
            import json
            print(json.dumps(result.__dict__, indent=2))
        else:
            print(f"\n=== {result.agent_name} Validation ===")
            print(f"PRP Capabilities: {'✅' if result.has_prp_capabilities else '❌'}")
            print(f"TDD Integration: {'✅' if result.has_tdd_integration else '❌'}")
            print(f"Validation Loop: {'✅' if result.has_validation_loop else '❌'}")
            print(f"Autonomous Workflow: {'✅' if result.has_autonomous_workflow else '❌'}")
            print(f"Consistency Score: {result.consistency_score:.1f}/100")
            
            if result.missing_sections:
                print(f"\nMissing Sections:")
                for section in result.missing_sections[:5]:
                    print(f"  - {section}")
            
            if result.recommendations:
                print(f"\nRecommendations:")
                for rec in result.recommendations[:3]:
                    print(f"  - {rec}")
    
    else:
        # Validate all agents
        summary = validator.validate_all_agents()
        
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print(f"\n=== Agent Enhancement Validation Summary ===")
            print(f"Total Agents: {summary['total_agents']}")
            print(f"Fully Enhanced: {summary['fully_enhanced_agents']} ({summary['enhancement_completion_percentage']}%)")
            print(f"Average Consistency: {summary['average_consistency_score']}/100")
            
            if summary['agents_needing_work']:
                print(f"\nAgents Needing Work ({len(summary['agents_needing_work'])}):")
                for agent in summary['agents_needing_work']:
                    print(f"  - {agent}")
        
        # Generate report if requested
        if args.output or args.check_consistency:
            output_path = Path(args.output) if args.output else project_root / "agent_enhancement_report.md"
            report = validator.generate_report(output_path)
            
            if not args.output:
                print(f"\nReport generated: {output_path}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())