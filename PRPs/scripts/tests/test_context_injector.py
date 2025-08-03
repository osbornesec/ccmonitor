"""
Test suite for context_injector.py - TDD Red Phase
Tests for intelligent context analysis and injection for PRP enhancement
"""
import pytest
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional
import tempfile
import os


@dataclass 
class ContextPackage:
    """Context package with all needed information for PRP generation"""
    code_examples: List[str]
    documentation: List[str]
    gotchas: List[str]
    architectural_patterns: List[str]
    integration_points: List[str]
    library_references: List[str]
    best_practices: List[str]
    similar_implementations: List[str]


class TestContextInjector:
    """Test suite for context injection functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        # Create a mock project structure for context analysis
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Create some example files for context extraction
        (self.test_dir / 'src').mkdir()
        (self.test_dir / 'docs').mkdir()
        (self.test_dir / 'tests').mkdir()
        
        # Sample Python file
        python_file = self.test_dir / 'src' / 'user_model.py'
        python_file.write_text('''
"""User model with authentication"""
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.email
''')
        
        # Sample API file
        api_file = self.test_dir / 'src' / 'api.py'
        api_file.write_text('''
"""API endpoints for user management"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: str

@app.get("/users/{user_id}")
async def get_user(user_id: int) -> UserResponse:
    # Implementation here
    pass
''')
        
        # Sample documentation
        doc_file = self.test_dir / 'docs' / 'api_guide.md'
        doc_file.write_text('''
# API Guide

## Authentication
All endpoints require JWT authentication.

## Common Gotchas
- Always validate email uniqueness
- Use timezone-aware datetime fields
- Handle database connection pooling properly

## Best Practices
- Use async/await for database operations
- Implement proper error handling
- Add rate limiting to endpoints
''')
        
        # Mock TodoItem for testing
        from PRPs.scripts.todo_parser import TodoItem
        self.test_todo = TodoItem(
            id="TEST-001",
            title="Create user authentication system",
            description="Implement user registration and login with JWT tokens",
            priority="High", 
            status="Not Started",
            dependencies=[],
            estimated_effort="4-6 hours",
            prp_reference=None,
            domain_areas=["python", "api", "database", "security"],
            subtasks=["Create user model", "Add JWT authentication", "Create login endpoint"],
            section="High Priority"
        )
    
    def teardown_method(self):
        """Cleanup test fixtures"""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_context_injector_initialization(self):
        """Test that ContextInjector can be initialized"""
        from PRPs.scripts.context_injector import ContextInjector
        
        injector = ContextInjector(project_root=self.test_dir)
        assert injector is not None
        assert injector.project_root == self.test_dir
    
    def test_inject_context_for_todo_returns_package(self):
        """Test that context injection returns a ContextPackage"""
        from PRPs.scripts.context_injector import ContextInjector, ContextPackage
        
        injector = ContextInjector(project_root=self.test_dir)
        context = injector.inject_context_for_todo(self.test_todo)
        
        assert isinstance(context, ContextPackage)
        assert hasattr(context, 'code_examples')
        assert hasattr(context, 'documentation')
        assert hasattr(context, 'gotchas')
    
    def test_find_code_examples_by_domain(self):
        """Test that code examples are found based on domain analysis"""
        from PRPs.scripts.context_injector import ContextInjector
        
        injector = ContextInjector(project_root=self.test_dir)
        context = injector.inject_context_for_todo(self.test_todo)
        
        # Should find Python examples since domain includes 'python'
        assert len(context.code_examples) > 0
        
        # Should contain relevant code from our test files
        code_text = '\n'.join(context.code_examples)
        assert 'User' in code_text or 'user' in code_text.lower()
    
    def test_extract_documentation_references(self):
        """Test that documentation is extracted and included"""
        from PRPs.scripts.context_injector import ContextInjector
        
        injector = ContextInjector(project_root=self.test_dir)
        context = injector.inject_context_for_todo(self.test_todo)
        
        # Should extract documentation
        assert len(context.documentation) > 0
        
        # Should include our test documentation
        doc_text = '\n'.join(context.documentation)
        assert 'Authentication' in doc_text or 'API Guide' in doc_text or 'Gotchas' in doc_text
    
    def test_identify_gotchas_and_pitfalls(self):
        """Test that common gotchas are identified"""
        from PRPs.scripts.context_injector import ContextInjector
        
        injector = ContextInjector(project_root=self.test_dir)
        context = injector.inject_context_for_todo(self.test_todo)
        
        # Should identify gotchas from documentation
        assert len(context.gotchas) > 0
        
        # Should include specific gotchas from our test doc
        gotcha_text = '\n'.join(context.gotchas)
        assert 'email uniqueness' in gotcha_text.lower() or 'timezone' in gotcha_text.lower()
    
    def test_find_architectural_patterns(self):
        """Test that architectural patterns are identified"""
        from PRPs.scripts.context_injector import ContextInjector
        
        injector = ContextInjector(project_root=self.test_dir)
        context = injector.inject_context_for_todo(self.test_todo)
        
        # Should identify patterns based on code analysis
        assert isinstance(context.architectural_patterns, list)
        
        # May include patterns like MVC, API patterns, etc.
        if context.architectural_patterns:
            pattern_text = '\n'.join(context.architectural_patterns)
            assert len(pattern_text) > 0
    
    def test_identify_integration_points(self):
        """Test that integration points are identified"""
        from PRPs.scripts.context_injector import ContextInjector
        
        injector = ContextInjector(project_root=self.test_dir)
        context = injector.inject_context_for_todo(self.test_todo)
        
        # Should identify integration points
        assert isinstance(context.integration_points, list)
        
        # For authentication system, should identify database, API, etc.
    
    def test_extract_library_references(self):
        """Test that library references are extracted"""
        from PRPs.scripts.context_injector import ContextInjector
        
        injector = ContextInjector(project_root=self.test_dir)
        context = injector.inject_context_for_todo(self.test_todo)
        
        # Should extract library references from imports
        assert isinstance(context.library_references, list)
        
        # Should include libraries from our test files
        if context.library_references:
            lib_text = '\n'.join(context.library_references)
            assert 'django' in lib_text.lower() or 'fastapi' in lib_text.lower()
    
    def test_include_best_practices(self):
        """Test that best practices are included"""
        from PRPs.scripts.context_injector import ContextInjector
        
        injector = ContextInjector(project_root=self.test_dir)
        context = injector.inject_context_for_todo(self.test_todo)
        
        # Should extract best practices
        assert isinstance(context.best_practices, list)
        
        # Should include practices from our documentation
        if context.best_practices:
            practices_text = '\n'.join(context.best_practices)
            assert 'async' in practices_text.lower() or 'error handling' in practices_text.lower() or 'best practices' in practices_text.lower()
    
    def test_find_similar_implementations(self):
        """Test that similar implementations are found"""
        from PRPs.scripts.context_injector import ContextInjector
        
        injector = ContextInjector(project_root=self.test_dir)
        context = injector.inject_context_for_todo(self.test_todo)
        
        # Should find similar implementations in codebase
        assert isinstance(context.similar_implementations, list)
    
    def test_context_relevance_scoring(self):
        """Test that context is scored for relevance"""
        from PRPs.scripts.context_injector import ContextInjector
        
        injector = ContextInjector(project_root=self.test_dir)
        
        # Test with highly relevant todo
        relevant_context = injector.inject_context_for_todo(self.test_todo)
        
        # Should have more content for relevant domains
        total_relevant = (len(relevant_context.code_examples) + 
                         len(relevant_context.documentation) +
                         len(relevant_context.gotchas))
        
        # Create irrelevant todo
        from PRPs.scripts.todo_parser import TodoItem
        irrelevant_todo = TodoItem(
            id="TEST-002",
            title="Create mobile game UI",
            description="Build mobile game interface with animations",
            priority="Low",
            status="Not Started", 
            dependencies=[],
            estimated_effort="8 hours",
            prp_reference=None,
            domain_areas=["flutter", "mobile", "gaming"],
            subtasks=["Design UI", "Add animations"],
            section="Low Priority"
        )
        
        irrelevant_context = injector.inject_context_for_todo(irrelevant_todo)
        total_irrelevant = (len(irrelevant_context.code_examples) + 
                           len(irrelevant_context.documentation) +
                           len(irrelevant_context.gotchas))
        
        # Relevant context should have more information
        assert total_relevant >= total_irrelevant
    
    def test_context_caching(self):
        """Test that context can be cached for performance"""
        from PRPs.scripts.context_injector import ContextInjector
        
        injector = ContextInjector(project_root=self.test_dir, use_cache=True)
        
        # First call should populate cache
        context1 = injector.inject_context_for_todo(self.test_todo)
        
        # Second call should use cache
        context2 = injector.inject_context_for_todo(self.test_todo)
        
        # Results should be identical
        assert context1.code_examples == context2.code_examples
        assert context1.documentation == context2.documentation
    
    def test_empty_project_handling(self):
        """Test handling of empty projects"""
        from PRPs.scripts.context_injector import ContextInjector
        
        empty_dir = Path(tempfile.mkdtemp())
        try:
            injector = ContextInjector(project_root=empty_dir)
            context = injector.inject_context_for_todo(self.test_todo)
            
            # Should handle gracefully without errors
            from PRPs.scripts.context_injector import ContextPackage
            assert isinstance(context, ContextPackage)
            
        finally:
            import shutil
            shutil.rmtree(empty_dir)
    
    def test_file_type_filtering(self):
        """Test that only relevant file types are analyzed"""
        from PRPs.scripts.context_injector import ContextInjector
        
        # Add some non-code files
        (self.test_dir / 'image.png').write_bytes(b'fake image data')
        (self.test_dir / 'video.mp4').write_bytes(b'fake video data')
        
        injector = ContextInjector(project_root=self.test_dir)
        context = injector.inject_context_for_todo(self.test_todo)
        
        # Should only include text-based code files
        # Binary files should be ignored
        from PRPs.scripts.context_injector import ContextPackage
        assert isinstance(context, ContextPackage)
    
    def test_context_size_limits(self):
        """Test that context size is limited to prevent token overflow"""
        from PRPs.scripts.context_injector import ContextInjector
        
        injector = ContextInjector(project_root=self.test_dir, max_context_size=1000)
        context = injector.inject_context_for_todo(self.test_todo)
        
        # Total context should respect size limits
        total_context = (
            '\n'.join(context.code_examples) +
            '\n'.join(context.documentation) +
            '\n'.join(context.gotchas) +
            '\n'.join(context.architectural_patterns) +
            '\n'.join(context.integration_points) +
            '\n'.join(context.library_references) +
            '\n'.join(context.best_practices) +
            '\n'.join(context.similar_implementations)
        )
        
        # Should respect size limits (with some tolerance for structure)
        assert len(total_context) <= 2000  # Allow some overhead


if __name__ == "__main__":
    pytest.main([__file__, "-v"])