"""
Test suite for template_selector.py - TDD Red Phase
Tests for intelligent PRP template selection based on todo characteristics
"""
import pytest
from pathlib import Path
from typing import Dict, Any
import tempfile
import os


class TestTemplateSelector:
    """Test suite for PRP template selection functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        # Mock TodoItem for testing
        from PRPs.scripts.todo_parser import TodoItem
        
        # Simple todo for basic template
        self.simple_todo = TodoItem(
            id="SIMPLE-001",
            title="Fix typo in documentation",
            description="Update incorrect spelling in README.md",
            priority="Low",
            status="Not Started",
            dependencies=[],
            estimated_effort="1 hour",
            prp_reference=None,
            domain_areas=["documentation"],
            subtasks=["Find typo", "Correct spelling"],
            section="Low Priority"
        )
        
        # Medium complexity todo
        self.medium_todo = TodoItem(
            id="MEDIUM-001", 
            title="Add user profile page",
            description="Create user profile page with edit capabilities",
            priority="Medium",
            status="Not Started",
            dependencies=["AUTH-001"],
            estimated_effort="3-4 hours",
            prp_reference=None,
            domain_areas=["frontend", "react"],
            subtasks=["Design UI", "Implement form", "Add validation"],
            section="Medium Priority"
        )
        
        # Complex todo for comprehensive template
        self.complex_todo = TodoItem(
            id="COMPLEX-001",
            title="Implement user authentication system",
            description="Full authentication with JWT, OAuth2, and MFA",
            priority="High",
            status="Not Started", 
            dependencies=[],
            estimated_effort="8-12 hours",
            prp_reference=None,
            domain_areas=["python", "api", "database", "security"],
            subtasks=[
                "Design database schema",
                "Implement JWT authentication", 
                "Add OAuth2 providers",
                "Implement MFA",
                "Create security middleware",
                "Add comprehensive tests"
            ],
            section="High Priority"
        )
        
        # Refactoring todo
        self.refactoring_todo = TodoItem(
            id="REFACTOR-001",
            title="Optimize database queries",
            description="Refactor slow queries and add caching",
            priority="Medium",
            status="Not Started",
            dependencies=[],
            estimated_effort="4-6 hours",
            prp_reference=None,
            domain_areas=["database", "performance"],
            subtasks=["Profile queries", "Add indexes", "Implement caching"],
            section="Medium Priority"
        )
        
        # Create mock context package
        from PRPs.scripts.context_injector import ContextPackage
        self.mock_context = ContextPackage(
            code_examples=["example code"],
            documentation=["api docs"],
            gotchas=["watch out for this"],
            architectural_patterns=["MVC"],
            integration_points=["database", "api"],
            library_references=["django", "fastapi"],
            best_practices=["use async"],
            similar_implementations=["similar code"]
        )
    
    def test_template_selector_initialization(self):
        """Test that TemplateSelector can be initialized"""
        from PRPs.scripts.template_selector import TemplateSelector
        
        selector = TemplateSelector()
        assert selector is not None
        assert hasattr(selector, 'template_info')
        assert isinstance(selector.template_info, dict)
    
    def test_select_optimal_template_returns_path(self):
        """Test that template selection returns a valid template path"""
        from PRPs.scripts.template_selector import select_optimal_template
        
        template_path = select_optimal_template(self.complex_todo, self.mock_context)
        
        assert isinstance(template_path, str)
        assert template_path.endswith('.md')
        assert 'prp_' in template_path
    
    def test_simple_todo_selects_simple_template(self):
        """Test that simple todos select the simple task template"""
        from PRPs.scripts.template_selector import select_optimal_template
        
        template_path = select_optimal_template(self.simple_todo, self.mock_context)
        
        # Should select simple template for low complexity tasks
        assert 'simple' in template_path.lower() or 'basic' in template_path.lower()
    
    def test_complex_todo_selects_comprehensive_template(self):
        """Test that complex todos select comprehensive templates"""
        from PRPs.scripts.template_selector import select_optimal_template
        
        template_path = select_optimal_template(self.complex_todo, self.mock_context)
        
        # Should select comprehensive template for high complexity
        assert 'tdd_base' in template_path or 'comprehensive' in template_path
    
    def test_refactoring_todo_selects_refactor_template(self):
        """Test that refactoring todos select red-green-refactor template"""
        from PRPs.scripts.template_selector import select_optimal_template
        
        template_path = select_optimal_template(self.refactoring_todo, self.mock_context)
        
        # Should select refactoring-focused template
        assert 'refactor' in template_path.lower() or 'red_green' in template_path
    
    def test_frontend_todo_selects_bdd_template(self):
        """Test that frontend/user-facing todos select BDD template"""
        from PRPs.scripts.template_selector import select_optimal_template
        
        template_path = select_optimal_template(self.medium_todo, self.mock_context)
        
        # Should consider BDD template for frontend work
        # This might select BDD or another appropriate template
        assert template_path is not None
        assert '.md' in template_path
    
    def test_calculate_complexity_score(self):
        """Test complexity scoring algorithm"""
        from PRPs.scripts.template_selector import TemplateSelector
        
        selector = TemplateSelector()
        
        # Simple todo should have low complexity
        simple_score = selector._calculate_complexity_score(self.simple_todo)
        assert simple_score < 3.0
        
        # Complex todo should have high complexity
        complex_score = selector._calculate_complexity_score(self.complex_todo)
        assert complex_score > 5.0
        
        # Complex should be higher than simple
        assert complex_score > simple_score
    
    def test_analyze_domain_fit(self):
        """Test domain fitness analysis for templates"""
        from PRPs.scripts.template_selector import TemplateSelector
        
        selector = TemplateSelector()
        
        # Test domain fitness scoring
        api_domains = ["api", "backend", "database"]
        frontend_domains = ["frontend", "react", "ui"]
        
        # Different templates should score differently for different domains
        api_scores = selector._analyze_domain_fit("prp_tdd_base.md", api_domains)
        frontend_scores = selector._analyze_domain_fit("prp_bdd_specification.md", frontend_domains)
        
        assert isinstance(api_scores, (int, float))
        assert isinstance(frontend_scores, (int, float))
        assert api_scores >= 0
        assert frontend_scores >= 0
    
    def test_score_template_fit(self):
        """Test comprehensive template fitness scoring"""
        from PRPs.scripts.template_selector import TemplateSelector
        
        selector = TemplateSelector()
        
        # Score different templates for the complex todo
        scores = {}
        templates = ["prp_tdd_base.md", "prp_red_green_refactor.md", "prp_bdd_specification.md"]
        
        for template in templates:
            score = selector._score_template_fit(template, self.complex_todo, self.mock_context)
            scores[template] = score
            assert isinstance(score, (int, float))
            assert score >= 0
        
        # Should return different scores for different templates
        assert len(set(scores.values())) > 1
    
    def test_template_capabilities_loaded(self):
        """Test that template capabilities are properly loaded"""
        from PRPs.scripts.template_selector import TemplateSelector
        
        selector = TemplateSelector()
        
        # Should have template information loaded
        assert len(selector.template_info) > 0
        
        # Each template should have required metadata
        for template_name, info in selector.template_info.items():
            assert 'complexity' in info
            assert 'domains' in info
            assert 'validation_levels' in info
            assert isinstance(info['domains'], list)
            assert isinstance(info['validation_levels'], int)
    
    def test_effort_estimation_consideration(self):
        """Test that effort estimation influences template selection"""
        from PRPs.scripts.template_selector import TemplateSelector
        
        selector = TemplateSelector()
        
        # Short tasks should get lower complexity scores
        short_score = selector._calculate_complexity_score(self.simple_todo)
        
        # Long tasks should get higher complexity scores  
        long_score = selector._calculate_complexity_score(self.complex_todo)
        
        assert long_score > short_score
    
    def test_dependency_count_affects_complexity(self):
        """Test that dependency count affects complexity scoring"""
        from PRPs.scripts.template_selector import TemplateSelector
        
        selector = TemplateSelector()
        
        # Todo with no dependencies
        no_deps_score = selector._calculate_complexity_score(self.simple_todo)
        
        # Todo with dependencies
        deps_score = selector._calculate_complexity_score(self.medium_todo)
        
        # Dependencies should increase complexity
        assert deps_score >= no_deps_score
    
    def test_subtask_count_affects_complexity(self):
        """Test that number of subtasks affects complexity"""
        from PRPs.scripts.template_selector import TemplateSelector
        
        selector = TemplateSelector()
        
        # Todo with few subtasks
        few_subtasks_score = selector._calculate_complexity_score(self.simple_todo)
        
        # Todo with many subtasks  
        many_subtasks_score = selector._calculate_complexity_score(self.complex_todo)
        
        # More subtasks should increase complexity
        assert many_subtasks_score > few_subtasks_score
    
    def test_priority_influences_template_selection(self):
        """Test that todo priority influences template selection"""
        from PRPs.scripts.template_selector import select_optimal_template
        
        # High priority todos might prefer more comprehensive templates
        high_priority_template = select_optimal_template(self.complex_todo, self.mock_context)
        low_priority_template = select_optimal_template(self.simple_todo, self.mock_context)
        
        # Templates should be different for different priorities/complexities
        assert high_priority_template != low_priority_template
    
    def test_context_influences_selection(self):
        """Test that context package influences template selection"""
        from PRPs.scripts.template_selector import select_optimal_template
        from PRPs.scripts.context_injector import ContextPackage
        
        # Rich context should potentially influence template choice
        rich_context = ContextPackage(
            code_examples=["complex example 1", "complex example 2"],
            documentation=["comprehensive docs"],
            gotchas=["gotcha 1", "gotcha 2", "gotcha 3"],
            architectural_patterns=["MVC", "Repository", "Factory"],
            integration_points=["api", "database", "cache", "queue"],
            library_references=["django", "fastapi", "celery"],
            best_practices=["practice 1", "practice 2"],
            similar_implementations=["impl 1", "impl 2"]
        )
        
        # Empty context
        empty_context = ContextPackage()
        
        rich_template = select_optimal_template(self.medium_todo, rich_context)
        empty_template = select_optimal_template(self.medium_todo, empty_context)
        
        # Both should return valid templates
        assert rich_template is not None
        assert empty_template is not None
    
    def test_template_path_validation(self):
        """Test that returned template paths are valid"""
        from PRPs.scripts.template_selector import TemplateSelector
        
        selector = TemplateSelector()
        
        # Get all possible templates that could be returned
        test_todos = [self.simple_todo, self.medium_todo, self.complex_todo, self.refactoring_todo]
        
        for todo in test_todos:
            template = selector.select_optimal_template(todo, self.mock_context)
            
            # Should return valid template name
            assert isinstance(template, str)
            assert template.endswith('.md')
            assert 'prp_' in template
    
    def test_domain_keyword_matching(self):
        """Test that domain keywords are properly matched to templates"""
        from PRPs.scripts.template_selector import TemplateSelector
        
        selector = TemplateSelector()
        
        # Test specific domain matching
        api_domains = ["api", "backend", "database"]
        frontend_domains = ["frontend", "react", "vue"]
        testing_domains = ["testing", "pytest", "cypress"]
        
        # Should return appropriate scores for domain matches
        for domains in [api_domains, frontend_domains, testing_domains]:
            for template in selector.template_info.keys():
                score = selector._analyze_domain_fit(template, domains)
                assert isinstance(score, (int, float))
                assert score >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])