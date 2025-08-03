#!/usr/bin/env python3
"""
Intelligent Project Analysis System for Multi-Agent PRP Orchestration

This system provides advanced project analysis capabilities including:
- Automated project complexity assessment and categorization
- Predictive execution time estimation with confidence intervals
- Optimal resource allocation and agent assignment strategies
- Risk assessment and mitigation recommendations
- Cost-benefit analysis for different execution approaches

Usage:
    analyzer = IntelligentProjectAnalyzer()
    analysis = await analyzer.analyze_project(project_dir, prp_files)
    recommendations = analyzer.get_optimization_recommendations(analysis)
"""

import asyncio
import json
import logging
import math
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from enum import Enum
import statistics

# Add project root to path
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PRPs.scripts.prp_coordination_system import PRPTask
from PRPs.scripts.knowledge_sharing_framework import KnowledgeSharingFramework, KnowledgeQuery, KnowledgeType


class ProjectComplexity(Enum):
    """Project complexity levels."""
    TRIVIAL = 1      # Simple scripts, single-file projects
    SIMPLE = 2       # Basic applications, few dependencies
    MODERATE = 3     # Standard applications with multiple components
    COMPLEX = 4      # Multi-service applications with integrations
    ENTERPRISE = 5   # Large-scale systems with multiple domains


class ProjectType(Enum):
    """Project type classifications."""
    WEB_APPLICATION = "web_application"
    API_SERVICE = "api_service"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    MICROSERVICE = "microservice"
    DATA_PIPELINE = "data_pipeline"
    ML_PROJECT = "ml_project"
    INFRASTRUCTURE = "infrastructure"
    LIBRARY = "library"
    INTEGRATION = "integration"


class RiskLevel(Enum):
    """Risk assessment levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ComplexityMetrics:
    """Detailed complexity analysis metrics."""
    total_tasks: int = 0
    unique_domains: int = 0
    dependency_depth: int = 0
    integration_points: int = 0
    external_services: int = 0
    security_requirements: int = 0
    performance_requirements: int = 0
    testing_complexity: int = 0
    deployment_complexity: int = 0
    overall_score: float = 0.0


@dataclass
class ResourceRequirement:
    """Resource requirement specification."""
    agent_type: str
    estimated_hours: float
    confidence: float
    priority: int
    parallel_capability: bool = True
    dependencies: List[str] = field(default_factory=list)
    special_requirements: List[str] = field(default_factory=list)


@dataclass
class RiskAssessment:
    """Risk assessment for project execution."""
    risk_id: str
    category: str
    level: RiskLevel
    description: str
    impact: str
    probability: float
    mitigation_strategies: List[str] = field(default_factory=list)
    affected_components: List[str] = field(default_factory=list)


@dataclass
class ExecutionScenario:
    """Different execution scenarios with trade-offs."""
    scenario_id: str
    name: str
    description: str
    estimated_duration: float
    estimated_cost: float
    resource_requirements: List[ResourceRequirement]
    success_probability: float
    quality_score: float
    risk_level: RiskLevel
    trade_offs: Dict[str, str] = field(default_factory=dict)


@dataclass
class ProjectAnalysis:
    """Comprehensive project analysis results."""
    project_id: str
    project_name: str
    project_type: ProjectType
    complexity: ProjectComplexity
    complexity_metrics: ComplexityMetrics
    total_estimated_hours: float
    confidence_interval: Tuple[float, float]
    resource_requirements: List[ResourceRequirement]
    risk_assessments: List[RiskAssessment]
    execution_scenarios: List[ExecutionScenario]
    optimization_opportunities: List[str]
    recommended_scenario: str
    analysis_timestamp: datetime = field(default_factory=datetime.now)


class IntelligentProjectAnalyzer:
    """
    Advanced project analysis system that provides intelligent insights
    for optimal multi-agent orchestration planning and execution.
    """

    def __init__(self, knowledge_framework: KnowledgeSharingFramework = None):
        self.logger = self._setup_logging()
        self.knowledge_framework = knowledge_framework or KnowledgeSharingFramework()
        
        # Analysis patterns and heuristics
        self.complexity_patterns = self._initialize_complexity_patterns()
        self.project_type_indicators = self._initialize_project_type_indicators()
        self.risk_patterns = self._initialize_risk_patterns()
        
        # Historical data for predictions
        self.historical_projects: List[ProjectAnalysis] = []
        self.execution_baselines: Dict[str, Dict[str, float]] = {}
        
        self.logger.info("Intelligent Project Analyzer initialized")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for project analyzer."""
        logger = logging.getLogger("IntelligentProjectAnalyzer")
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _initialize_complexity_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize patterns for complexity analysis."""
        return {
            "database_operations": {
                "indicators": ["database", "sql", "migration", "schema", "query"],
                "complexity_multiplier": 1.3,
                "integration_points": 2
            },
            "authentication_systems": {
                "indicators": ["auth", "login", "jwt", "oauth", "security"],
                "complexity_multiplier": 1.5,
                "security_requirements": 3
            },
            "api_integrations": {
                "indicators": ["api", "rest", "graphql", "endpoint", "service"],
                "complexity_multiplier": 1.2,
                "integration_points": 1
            },
            "real_time_features": {
                "indicators": ["websocket", "realtime", "live", "streaming"],
                "complexity_multiplier": 1.4,
                "performance_requirements": 2
            },
            "payment_processing": {
                "indicators": ["payment", "stripe", "paypal", "transaction"],
                "complexity_multiplier": 1.6,
                "security_requirements": 4,
                "integration_points": 3
            },
            "machine_learning": {
                "indicators": ["ml", "ai", "model", "training", "prediction"],
                "complexity_multiplier": 1.8,
                "performance_requirements": 3
            },
            "microservices": {
                "indicators": ["microservice", "docker", "kubernetes", "container"],
                "complexity_multiplier": 1.7,
                "deployment_complexity": 3
            },
            "testing_infrastructure": {
                "indicators": ["test", "testing", "coverage", "e2e", "integration"],
                "complexity_multiplier": 1.1,
                "testing_complexity": 2
            }
        }

    def _initialize_project_type_indicators(self) -> Dict[ProjectType, List[str]]:
        """Initialize indicators for project type classification."""
        return {
            ProjectType.WEB_APPLICATION: [
                "web", "frontend", "backend", "fullstack", "react", "vue", "angular",
                "html", "css", "javascript", "responsive"
            ],
            ProjectType.API_SERVICE: [
                "api", "rest", "graphql", "endpoint", "service", "microservice",
                "fastapi", "express", "flask", "django"
            ],
            ProjectType.MOBILE_APP: [
                "mobile", "android", "ios", "flutter", "react-native", "native",
                "app", "smartphone", "tablet"
            ],
            ProjectType.DESKTOP_APP: [
                "desktop", "gui", "window", "electron", "tkinter", "qt",
                "native", "cross-platform"
            ],
            ProjectType.MICROSERVICE: [
                "microservice", "service", "docker", "kubernetes", "container",
                "distributed", "scalable"
            ],
            ProjectType.DATA_PIPELINE: [
                "data", "pipeline", "etl", "processing", "analytics", "warehouse",
                "streaming", "batch", "airflow"
            ],
            ProjectType.ML_PROJECT: [
                "machine learning", "ml", "ai", "model", "training", "prediction",
                "tensorflow", "pytorch", "scikit", "data science"
            ],
            ProjectType.INFRASTRUCTURE: [
                "infrastructure", "devops", "deployment", "ci/cd", "terraform",
                "ansible", "kubernetes", "cloud"
            ],
            ProjectType.LIBRARY: [
                "library", "package", "sdk", "framework", "utility", "tool",
                "reusable", "component"
            ],
            ProjectType.INTEGRATION: [
                "integration", "connector", "adapter", "bridge", "sync",
                "migration", "import", "export"
            ]
        }

    def _initialize_risk_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize patterns for risk assessment."""
        return {
            "external_dependencies": {
                "indicators": ["api", "service", "external", "third-party"],
                "risk_level": RiskLevel.MEDIUM,
                "impact": "Integration failures or service downtime",
                "mitigation": ["Implement circuit breakers", "Add fallback mechanisms", "Monitor external services"]
            },
            "complex_algorithms": {
                "indicators": ["algorithm", "optimization", "complex", "performance"],
                "risk_level": RiskLevel.MEDIUM,
                "impact": "Performance issues or incorrect implementations",
                "mitigation": ["Thorough testing", "Performance benchmarking", "Code review"]
            },
            "security_critical": {
                "indicators": ["security", "authentication", "encryption", "sensitive"],
                "risk_level": RiskLevel.HIGH,
                "impact": "Security vulnerabilities or data breaches",
                "mitigation": ["Security audits", "Penetration testing", "Regular updates"]
            },
            "new_technology": {
                "indicators": ["new", "experimental", "beta", "cutting-edge"],
                "risk_level": RiskLevel.HIGH,
                "impact": "Technology instability or lack of support",
                "mitigation": ["Proof of concept", "Fallback options", "Regular updates"]
            },
            "tight_deadlines": {
                "indicators": ["urgent", "asap", "deadline", "rush"],
                "risk_level": RiskLevel.MEDIUM,
                "impact": "Quality compromises or incomplete features",
                "mitigation": ["Scope reduction", "Additional resources", "Quality gates"]
            }
        }

    async def analyze_project(self, project_dir: str, prp_files: List[str], 
                            tasks: List[PRPTask] = None) -> ProjectAnalysis:
        """
        Perform comprehensive project analysis including complexity assessment,
        resource planning, risk analysis, and optimization recommendations.
        
        Args:
            project_dir: Directory containing the project
            prp_files: List of PRP files to analyze
            tasks: Optional pre-parsed tasks
            
        Returns:
            ProjectAnalysis with comprehensive insights
        """
        project_name = Path(project_dir).name
        project_id = f"proj_{int(datetime.now().timestamp())}"
        
        self.logger.info(f"🔍 Starting intelligent analysis for project: {project_name}")
        
        # Phase 1: Basic project analysis
        prp_content = await self._load_prp_content(prp_files)
        project_type = self._classify_project_type(prp_content)
        
        # Phase 2: Complexity analysis
        complexity_metrics = await self._analyze_complexity(prp_content, tasks)
        complexity_level = self._determine_complexity_level(complexity_metrics)
        
        # Phase 3: Resource requirement analysis
        resource_requirements = await self._analyze_resource_requirements(
            prp_content, complexity_metrics, tasks
        )
        
        # Phase 4: Time estimation with historical data
        time_estimates = await self._estimate_execution_time(
            project_type, complexity_metrics, resource_requirements
        )
        
        # Phase 5: Risk assessment
        risk_assessments = await self._assess_project_risks(
            prp_content, complexity_metrics, project_type
        )
        
        # Phase 6: Generate execution scenarios
        execution_scenarios = await self._generate_execution_scenarios(
            resource_requirements, time_estimates, risk_assessments
        )
        
        # Phase 7: Optimization opportunities
        optimization_opportunities = await self._identify_optimization_opportunities(
            complexity_metrics, resource_requirements, execution_scenarios
        )
        
        # Phase 8: Select recommended scenario
        recommended_scenario = self._select_recommended_scenario(execution_scenarios)
        
        # Create comprehensive analysis
        analysis = ProjectAnalysis(
            project_id=project_id,
            project_name=project_name,
            project_type=project_type,
            complexity=complexity_level,
            complexity_metrics=complexity_metrics,
            total_estimated_hours=time_estimates["expected"],
            confidence_interval=(time_estimates["min"], time_estimates["max"]),
            resource_requirements=resource_requirements,
            risk_assessments=risk_assessments,
            execution_scenarios=execution_scenarios,
            optimization_opportunities=optimization_opportunities,
            recommended_scenario=recommended_scenario
        )
        
        # Store for future reference
        self.historical_projects.append(analysis)
        
        self.logger.info(f"✅ Project analysis complete: {complexity_level.name} complexity, "
                        f"{time_estimates['expected']:.1f}h estimated")
        
        return analysis

    async def _load_prp_content(self, prp_files: List[str]) -> str:
        """Load and combine content from all PRP files."""
        combined_content = ""
        
        for prp_file in prp_files:
            try:
                with open(prp_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    combined_content += content + "\n\n"
            except Exception as e:
                self.logger.warning(f"Could not load PRP file {prp_file}: {e}")
        
        return combined_content.lower()

    def _classify_project_type(self, content: str) -> ProjectType:
        """Classify project type based on content analysis."""
        type_scores = {}
        
        for project_type, indicators in self.project_type_indicators.items():
            score = 0
            for indicator in indicators:
                score += content.count(indicator)
            type_scores[project_type] = score
        
        # Return the type with highest score, default to WEB_APPLICATION
        if not type_scores or max(type_scores.values()) == 0:
            return ProjectType.WEB_APPLICATION
        
        return max(type_scores.items(), key=lambda x: x[1])[0]

    async def _analyze_complexity(self, content: str, tasks: List[PRPTask] = None) -> ComplexityMetrics:
        """Analyze project complexity using multiple heuristics."""
        metrics = ComplexityMetrics()
        
        # Basic metrics from content
        if tasks:
            metrics.total_tasks = len(tasks)
            domains = set(task.domain for task in tasks)
            metrics.unique_domains = len(domains)
            
            # Calculate dependency depth
            max_deps = max(len(task.dependencies) for task in tasks) if tasks else 0
            metrics.dependency_depth = max_deps
        else:
            # Estimate from content
            task_indicators = ["implement", "create", "build", "develop", "add"]
            metrics.total_tasks = sum(content.count(indicator) for indicator in task_indicators)
            metrics.unique_domains = len(re.findall(r'\b\w+(?:specialist|service|component)\b', content))
        
        # Pattern-based analysis
        for pattern_name, pattern_data in self.complexity_patterns.items():
            pattern_score = 0
            for indicator in pattern_data["indicators"]:
                pattern_score += content.count(indicator)
            
            if pattern_score > 0:
                # Apply pattern-specific complexity contributions
                metrics.integration_points += pattern_data.get("integration_points", 0) * pattern_score
                metrics.security_requirements += pattern_data.get("security_requirements", 0) * pattern_score
                metrics.performance_requirements += pattern_data.get("performance_requirements", 0) * pattern_score
                metrics.testing_complexity += pattern_data.get("testing_complexity", 0) * pattern_score
                metrics.deployment_complexity += pattern_data.get("deployment_complexity", 0) * pattern_score
        
        # External services detection
        external_indicators = ["api", "service", "integration", "third-party", "external"]
        metrics.external_services = sum(content.count(indicator) for indicator in external_indicators)
        
        # Calculate overall complexity score
        metrics.overall_score = self._calculate_overall_complexity_score(metrics)
        
        return metrics

    def _calculate_overall_complexity_score(self, metrics: ComplexityMetrics) -> float:
        """Calculate overall complexity score from individual metrics."""
        # Weighted complexity calculation
        weights = {
            "total_tasks": 0.2,
            "unique_domains": 0.15,
            "dependency_depth": 0.1,
            "integration_points": 0.15,
            "external_services": 0.1,
            "security_requirements": 0.1,
            "performance_requirements": 0.1,
            "testing_complexity": 0.05,
            "deployment_complexity": 0.05
        }
        
        score = 0.0
        for metric_name, weight in weights.items():
            value = getattr(metrics, metric_name, 0)
            score += value * weight
        
        return min(score, 10.0)  # Cap at 10.0

    def _determine_complexity_level(self, metrics: ComplexityMetrics) -> ProjectComplexity:
        """Determine complexity level from metrics."""
        score = metrics.overall_score
        
        if score <= 2.0:
            return ProjectComplexity.TRIVIAL
        elif score <= 4.0:
            return ProjectComplexity.SIMPLE
        elif score <= 6.0:
            return ProjectComplexity.MODERATE
        elif score <= 8.0:
            return ProjectComplexity.COMPLEX
        else:
            return ProjectComplexity.ENTERPRISE

    async def _analyze_resource_requirements(self, content: str, metrics: ComplexityMetrics,
                                           tasks: List[PRPTask] = None) -> List[ResourceRequirement]:
        """Analyze required resources and agent assignments."""
        requirements = []
        
        # Domain-based resource analysis
        domain_patterns = {
            "python": ["python", "django", "flask", "fastapi"],
            "javascript": ["javascript", "node", "react", "vue"],
            "database": ["database", "sql", "postgresql", "mongodb"],
            "security": ["security", "auth", "encryption"],
            "performance": ["performance", "optimization", "scaling"],
            "testing": ["test", "testing", "quality"],
            "devops": ["docker", "kubernetes", "deployment", "ci/cd"]
        }
        
        for domain, indicators in domain_patterns.items():
            domain_score = sum(content.count(indicator) for indicator in indicators)
            if domain_score > 0:
                # Estimate hours based on complexity and domain involvement
                base_hours = domain_score * 2  # 2 hours per mention
                complexity_multiplier = 1 + (metrics.overall_score / 10)
                estimated_hours = base_hours * complexity_multiplier
                
                requirement = ResourceRequirement(
                    agent_type=f"{domain}-specialist",
                    estimated_hours=estimated_hours,
                    confidence=0.7 + (domain_score / 10),  # Higher confidence with more mentions
                    priority=self._calculate_domain_priority(domain, content),
                    parallel_capability=domain not in ["database", "security"],
                    special_requirements=self._identify_special_requirements(domain, content)
                )
                requirements.append(requirement)
        
        return requirements

    def _calculate_domain_priority(self, domain: str, content: str) -> int:
        """Calculate priority for a domain based on content analysis."""
        critical_domains = ["security", "database", "performance"]
        if domain in critical_domains:
            return 1
        
        high_priority_indicators = ["critical", "important", "essential", "required"]
        domain_context = self._extract_domain_context(domain, content)
        
        for indicator in high_priority_indicators:
            if indicator in domain_context:
                return 2
        
        return 3

    def _extract_domain_context(self, domain: str, content: str) -> str:
        """Extract context around domain mentions."""
        # Simple context extraction - could be enhanced with NLP
        sentences = content.split('.')
        domain_context = ""
        
        for sentence in sentences:
            if domain in sentence:
                domain_context += sentence + " "
        
        return domain_context.lower()

    def _identify_special_requirements(self, domain: str, content: str) -> List[str]:
        """Identify special requirements for a domain."""
        special_requirements = []
        
        if domain == "security":
            if "compliance" in content:
                special_requirements.append("compliance_expertise")
            if "penetration" in content:
                special_requirements.append("penetration_testing")
        
        elif domain == "performance":
            if "scale" in content or "scaling" in content:
                special_requirements.append("scalability_expertise")
            if "real-time" in content:
                special_requirements.append("realtime_optimization")
        
        elif domain == "database":
            if "migration" in content:
                special_requirements.append("migration_expertise")
            if "replication" in content:
                special_requirements.append("replication_setup")
        
        return special_requirements

    async def _estimate_execution_time(self, project_type: ProjectType, 
                                     metrics: ComplexityMetrics,
                                     requirements: List[ResourceRequirement]) -> Dict[str, float]:
        """Estimate execution time with confidence intervals."""
        # Base estimation from resource requirements
        base_hours = sum(req.estimated_hours for req in requirements)
        
        # Apply complexity multipliers
        complexity_multipliers = {
            ProjectComplexity.TRIVIAL: 0.8,
            ProjectComplexity.SIMPLE: 1.0,
            ProjectComplexity.MODERATE: 1.3,
            ProjectComplexity.COMPLEX: 1.7,
            ProjectComplexity.ENTERPRISE: 2.2
        }
        
        complexity_level = self._determine_complexity_level(metrics)
        complexity_multiplier = complexity_multipliers[complexity_level]
        
        # Apply project type multipliers
        type_multipliers = {
            ProjectType.WEB_APPLICATION: 1.0,
            ProjectType.API_SERVICE: 0.8,
            ProjectType.MOBILE_APP: 1.2,
            ProjectType.DESKTOP_APP: 1.1,
            ProjectType.MICROSERVICE: 0.9,
            ProjectType.DATA_PIPELINE: 1.3,
            ProjectType.ML_PROJECT: 1.8,
            ProjectType.INFRASTRUCTURE: 1.4,
            ProjectType.LIBRARY: 0.7,
            ProjectType.INTEGRATION: 1.1
        }
        
        type_multiplier = type_multipliers.get(project_type, 1.0)
        
        # Calculate expected time
        expected_hours = base_hours * complexity_multiplier * type_multiplier
        
        # Add uncertainty based on historical data or heuristics
        uncertainty_factor = 0.3 + (metrics.overall_score / 20)  # 30-80% uncertainty
        
        min_hours = expected_hours * (1 - uncertainty_factor)
        max_hours = expected_hours * (1 + uncertainty_factor)
        
        # Query historical data for calibration
        historical_adjustment = await self._get_historical_adjustment(project_type, complexity_level)
        
        return {
            "expected": expected_hours * historical_adjustment,
            "min": min_hours * historical_adjustment,
            "max": max_hours * historical_adjustment,
            "confidence": 1.0 - uncertainty_factor
        }

    async def _get_historical_adjustment(self, project_type: ProjectType, 
                                       complexity: ProjectComplexity) -> float:
        """Get historical adjustment factor based on past projects."""
        # Query knowledge framework for historical project data
        if not self.knowledge_framework:
            return 1.0
        
        query = KnowledgeQuery(
            requesting_agent="project-analyzer",
            task_domain="project_management",
            task_description=f"{project_type.value} {complexity.name} project estimation",
            context={"analysis_type": "time_estimation"},
            knowledge_types=[KnowledgeType.PERFORMANCE, KnowledgeType.PATTERN],
            max_results=10,
            min_relevance=0.3
        )
        
        historical_knowledge = await self.knowledge_framework.query_knowledge(query)
        
        if not historical_knowledge:
            return 1.0
        
        # Calculate adjustment based on historical performance
        adjustments = []
        for knowledge in historical_knowledge:
            if "time_adjustment" in knowledge.content:
                adjustments.append(knowledge.content["time_adjustment"])
        
        if adjustments:
            return statistics.mean(adjustments)
        
        return 1.0

    async def _assess_project_risks(self, content: str, metrics: ComplexityMetrics,
                                  project_type: ProjectType) -> List[RiskAssessment]:
        """Assess project risks and provide mitigation strategies."""
        risks = []
        
        # Pattern-based risk detection
        for risk_name, risk_data in self.risk_patterns.items():
            risk_score = 0
            for indicator in risk_data["indicators"]:
                risk_score += content.count(indicator)
            
            if risk_score > 0:
                risk = RiskAssessment(
                    risk_id=f"risk_{len(risks)+1:03d}",
                    category=risk_name,
                    level=risk_data["risk_level"],
                    description=f"Risk detected based on {risk_score} indicators",
                    impact=risk_data["impact"],
                    probability=min(risk_score * 0.2, 1.0),
                    mitigation_strategies=risk_data["mitigation"],
                    affected_components=[risk_name]
                )
                risks.append(risk)
        
        # Complexity-based risks
        if metrics.overall_score > 7:
            risks.append(RiskAssessment(
                risk_id=f"risk_{len(risks)+1:03d}",
                category="high_complexity",
                level=RiskLevel.HIGH,
                description="Project complexity exceeds recommended thresholds",
                impact="Extended development time and potential quality issues",
                probability=0.8,
                mitigation_strategies=[
                    "Break down into smaller phases",
                    "Increase testing coverage",
                    "Add code review checkpoints"
                ]
            ))
        
        # Integration risks
        if metrics.integration_points > 5:
            risks.append(RiskAssessment(
                risk_id=f"risk_{len(risks)+1:03d}",
                category="integration_complexity",
                level=RiskLevel.MEDIUM,
                description="High number of integration points detected",
                impact="Integration failures and testing complexity",
                probability=0.6,
                mitigation_strategies=[
                    "Implement integration tests",
                    "Use contract testing",
                    "Plan integration phases carefully"
                ]
            ))
        
        return risks

    async def _generate_execution_scenarios(self, requirements: List[ResourceRequirement],
                                          time_estimates: Dict[str, float],
                                          risks: List[RiskAssessment]) -> List[ExecutionScenario]:
        """Generate different execution scenarios with trade-offs."""
        scenarios = []
        
        # Scenario 1: Optimal (Recommended)
        optimal_scenario = ExecutionScenario(
            scenario_id="optimal",
            name="Optimal Execution",
            description="Balanced approach optimizing for quality, time, and resources",
            estimated_duration=time_estimates["expected"],
            estimated_cost=self._calculate_scenario_cost(requirements, 1.0),
            resource_requirements=requirements,
            success_probability=0.85,
            quality_score=0.9,
            risk_level=self._calculate_overall_risk_level(risks),
            trade_offs={
                "time": "Standard development timeline",
                "cost": "Moderate resource allocation",
                "quality": "High quality with comprehensive testing"
            }
        )
        scenarios.append(optimal_scenario)
        
        # Scenario 2: Fast Track
        fast_requirements = self._adjust_requirements_for_speed(requirements)
        fast_scenario = ExecutionScenario(
            scenario_id="fast_track",
            name="Fast Track Execution",
            description="Accelerated delivery with increased parallel execution",
            estimated_duration=time_estimates["expected"] * 0.7,
            estimated_cost=self._calculate_scenario_cost(fast_requirements, 1.3),
            resource_requirements=fast_requirements,
            success_probability=0.75,
            quality_score=0.8,
            risk_level=RiskLevel.MEDIUM,
            trade_offs={
                "time": "30% faster delivery",
                "cost": "30% higher resource cost",
                "quality": "Slightly reduced testing depth"
            }
        )
        scenarios.append(fast_scenario)
        
        # Scenario 3: Conservative
        conservative_requirements = self._adjust_requirements_for_safety(requirements)
        conservative_scenario = ExecutionScenario(
            scenario_id="conservative",
            name="Conservative Execution",
            description="Risk-minimized approach with extensive validation",
            estimated_duration=time_estimates["expected"] * 1.4,
            estimated_cost=self._calculate_scenario_cost(conservative_requirements, 1.2),
            resource_requirements=conservative_requirements,
            success_probability=0.95,
            quality_score=0.95,
            risk_level=RiskLevel.LOW,
            trade_offs={
                "time": "40% longer development time",
                "cost": "20% higher due to extensive testing",
                "quality": "Maximum quality assurance"
            }
        )
        scenarios.append(conservative_scenario)
        
        return scenarios

    def _calculate_scenario_cost(self, requirements: List[ResourceRequirement], 
                               multiplier: float) -> float:
        """Calculate cost for execution scenario."""
        # Simple cost calculation based on estimated hours
        hourly_rates = {
            "python-specialist": 100,
            "javascript-specialist": 95,
            "database-specialist": 110,
            "security-specialist": 120,
            "performance-specialist": 115,
            "testing-specialist": 90,
            "devops-specialist": 105
        }
        
        total_cost = 0
        for req in requirements:
            rate = hourly_rates.get(req.agent_type, 100)
            total_cost += req.estimated_hours * rate
        
        return total_cost * multiplier

    def _adjust_requirements_for_speed(self, requirements: List[ResourceRequirement]) -> List[ResourceRequirement]:
        """Adjust requirements for fast track scenario."""
        adjusted = []
        for req in requirements:
            adjusted_req = ResourceRequirement(
                agent_type=req.agent_type,
                estimated_hours=req.estimated_hours * 0.8,  # Reduce time estimate
                confidence=req.confidence * 0.9,  # Slightly lower confidence
                priority=req.priority,
                parallel_capability=True,  # Force parallel where possible
                dependencies=req.dependencies,
                special_requirements=req.special_requirements + ["fast_track_mode"]
            )
            adjusted.append(adjusted_req)
        return adjusted

    def _adjust_requirements_for_safety(self, requirements: List[ResourceRequirement]) -> List[ResourceRequirement]:
        """Adjust requirements for conservative scenario."""
        adjusted = []
        for req in requirements:
            adjusted_req = ResourceRequirement(
                agent_type=req.agent_type,
                estimated_hours=req.estimated_hours * 1.3,  # Add buffer time
                confidence=req.confidence * 1.1,  # Higher confidence
                priority=req.priority,
                parallel_capability=req.parallel_capability,
                dependencies=req.dependencies,
                special_requirements=req.special_requirements + ["extensive_validation", "peer_review"]
            )
            adjusted.append(adjusted_req)
        return adjusted

    def _calculate_overall_risk_level(self, risks: List[RiskAssessment]) -> RiskLevel:
        """Calculate overall risk level from individual risks."""
        if not risks:
            return RiskLevel.LOW
        
        risk_scores = [risk.level.value for risk in risks]
        avg_risk = statistics.mean(risk_scores)
        
        if avg_risk >= 3.5:
            return RiskLevel.CRITICAL
        elif avg_risk >= 2.5:
            return RiskLevel.HIGH
        elif avg_risk >= 1.5:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    async def _identify_optimization_opportunities(self, metrics: ComplexityMetrics,
                                                 requirements: List[ResourceRequirement],
                                                 scenarios: List[ExecutionScenario]) -> List[str]:
        """Identify opportunities for optimization."""
        opportunities = []
        
        # Parallelization opportunities
        parallel_agents = sum(1 for req in requirements if req.parallel_capability)
        if parallel_agents > 2:
            opportunities.append(
                f"Parallel execution possible with {parallel_agents} agents to reduce timeline by 40-60%"
            )
        
        # Resource optimization
        high_hour_requirements = [req for req in requirements if req.estimated_hours > 20]
        if len(high_hour_requirements) > 1:
            opportunities.append(
                "Consider breaking down large tasks to enable better load distribution"
            )
        
        # Domain consolidation
        domain_counts = {}
        for req in requirements:
            domain = req.agent_type.split('-')[0]
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        if max(domain_counts.values()) > 1:
            opportunities.append(
                "Multiple tasks in same domain detected - consider consolidating for efficiency"
            )
        
        # Risk mitigation
        if metrics.overall_score > 6:
            opportunities.append(
                "High complexity detected - consider phased delivery approach"
            )
        
        # Knowledge reuse
        knowledge_query = KnowledgeQuery(
            requesting_agent="project-analyzer",
            task_domain="optimization",
            task_description="project execution optimization patterns",
            context={"complexity": metrics.overall_score},
            knowledge_types=[KnowledgeType.OPTIMIZATION, KnowledgeType.BEST_PRACTICE],
            max_results=5
        )
        
        historical_optimizations = await self.knowledge_framework.query_knowledge(knowledge_query)
        for knowledge in historical_optimizations:
            if "optimization_tip" in knowledge.content:
                opportunities.append(knowledge.content["optimization_tip"])
        
        return opportunities

    def _select_recommended_scenario(self, scenarios: List[ExecutionScenario]) -> str:
        """Select the recommended execution scenario."""
        # Score scenarios based on multiple factors
        scored_scenarios = []
        
        for scenario in scenarios:
            # Balanced scoring considering success probability, quality, and reasonable risk
            score = (
                scenario.success_probability * 0.4 +
                scenario.quality_score * 0.3 +
                (1.0 - scenario.risk_level.value / 4.0) * 0.2 +
                (1.0 / scenario.estimated_duration if scenario.estimated_duration > 0 else 0) * 0.1
            )
            scored_scenarios.append((scenario.scenario_id, score))
        
        # Return the scenario with the highest score
        return max(scored_scenarios, key=lambda x: x[1])[0]

    def get_analysis_summary(self, analysis: ProjectAnalysis) -> str:
        """Generate a human-readable analysis summary."""
        return f"""
# Project Analysis Summary: {analysis.project_name}

## Overview
- **Project Type**: {analysis.project_type.value}
- **Complexity Level**: {analysis.complexity.name}
- **Estimated Duration**: {analysis.total_estimated_hours:.1f} hours ({analysis.confidence_interval[0]:.1f}-{analysis.confidence_interval[1]:.1f}h range)
- **Recommended Scenario**: {analysis.recommended_scenario}

## Complexity Breakdown
- Total Tasks: {analysis.complexity_metrics.total_tasks}
- Unique Domains: {analysis.complexity_metrics.unique_domains}
- Integration Points: {analysis.complexity_metrics.integration_points}
- External Services: {analysis.complexity_metrics.external_services}
- Overall Complexity Score: {analysis.complexity_metrics.overall_score:.1f}/10

## Resource Requirements
{chr(10).join([f"- {req.agent_type}: {req.estimated_hours:.1f}h (Priority {req.priority})" for req in analysis.resource_requirements])}

## Risk Assessment
{chr(10).join([f"- {risk.level.name}: {risk.description}" for risk in analysis.risk_assessments])}

## Optimization Opportunities
{chr(10).join([f"- {opp}" for opp in analysis.optimization_opportunities])}

## Execution Scenarios
{chr(10).join([f"- **{scenario.name}**: {scenario.estimated_duration:.1f}h, {scenario.success_probability:.0%} success rate" for scenario in analysis.execution_scenarios])}
"""


# Example usage
async def main():
    """Example usage of the Intelligent Project Analyzer."""
    analyzer = IntelligentProjectAnalyzer()
    
    # Example analysis (would need actual PRP files)
    # analysis = await analyzer.analyze_project(
    #     project_dir="/path/to/project",
    #     prp_files=["complex_ecommerce.md"]
    # )
    
    # print(analyzer.get_analysis_summary(analysis))
    
    print("🧠 Intelligent Project Analyzer ready for advanced project analysis")


if __name__ == "__main__":
    asyncio.run(main())