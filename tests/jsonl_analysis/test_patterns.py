"""
Test suite for pattern recognition module
Following TDD methodology - tests written before implementation
"""

import pytest
import re
from pathlib import Path

# Import the modules we'll implement
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from src.jsonl_analysis.patterns import (
    PatternAnalyzer, 
    CodePatternDetector,
    ErrorPatternDetector, 
    ArchitecturalPatternDetector,
    HookPatternDetector,
    SystemPatternDetector
)


class TestPatternAnalyzer:
    """Test suite for the main pattern analyzer orchestrator"""
    
    @pytest.fixture
    def analyzer(self):
        """Create pattern analyzer instance"""
        return PatternAnalyzer()
    
    def test_analyze_content_comprehensive(self, analyzer):
        """Test comprehensive content analysis with multiple patterns"""
        content = """
        I need to edit the main.py file to fix a critical IndexError bug.
        The architecture decision is to use a factory pattern for user creation.
        Hook: post_tool_validator executed successfully.
        """
        
        patterns = analyzer.analyze_content(content)
        
        # Should detect multiple pattern types
        assert "code_changes" in patterns
        assert "error_solution" in patterns  
        assert "architectural_decision" in patterns
        assert "hook_log" in patterns
        
        # Should have reasonable confidence scores
        assert patterns["code_changes"]["confidence"] > 0.7
        assert patterns["error_solution"]["confidence"] > 0.7
        assert patterns["architectural_decision"]["confidence"] > 0.7
        assert patterns["hook_log"]["confidence"] > 0.9
    
    def test_analyze_message_structure(self, analyzer):
        """Test analysis of complete message structure"""
        message = {
            "type": "tool_call",
            "message": {
                "tool": "Edit",
                "parameters": {"file_path": "src/auth.py", "old_string": "bug", "new_string": "fix"},
                "result": "File edited successfully",
                "content": "Fixed authentication bug in login function"
            }
        }
        
        analysis = analyzer.analyze_message(message)
        
        # Should identify as high-importance code modification
        assert analysis["importance_indicators"]["code_changes"]
        assert analysis["importance_indicators"]["file_modification"]
        assert analysis["tool_usage"]["tool"] == "Edit"
        assert analysis["tool_usage"]["file_path"] == "src/auth.py"
    
    def test_batch_analysis_performance(self, analyzer):
        """Test batch analysis performance with many messages"""
        import time
        
        # Create batch of messages for testing
        messages = []
        for i in range(100):
            content_types = [
                f"Edit file{i}.py to implement feature",
                f"Fix NameError in function {i}",
                f"Architecture: use database for storage {i}",
                f"Hook: validation_{i} completed",
                f"How do I solve problem {i}?",
                f"Reading documentation about {i}"
            ]
            
            message = {
                "type": "assistant",
                "message": {"content": content_types[i % len(content_types)]}
            }
            messages.append(message)
        
        # Measure batch analysis time
        start_time = time.time()
        results = analyzer.batch_analyze(messages)
        analysis_time = time.time() - start_time
        
        # Should complete quickly (< 0.5 seconds for 100 messages)
        assert analysis_time < 0.5, f"Batch analysis took {analysis_time:.3f} seconds"
        assert len(results) == 100
        
        # All results should have pattern analysis
        for result in results:
            assert "patterns" in result
            assert "importance_score" in result


class TestCodePatternDetector:
    """Test suite for code pattern detection"""
    
    @pytest.fixture
    def detector(self):
        """Create code pattern detector"""
        return CodePatternDetector()
    
    def test_detect_file_modifications(self, detector):
        """Test detection of file modification patterns"""
        modification_texts = [
            "Edit file main.py to add authentication",
            "Write new function in utils.py",
            "Create class UserManager in models.py", 
            "Implement error handling in app.js",
            "Update configuration in config.yaml",
            "Delete obsolete code from legacy.py",
            "Refactor database.py for better performance"
        ]
        
        for text in modification_texts:
            patterns = detector.detect_patterns(text)
            assert patterns["file_modification"]["detected"], f"Failed to detect file modification in: {text}"
            assert patterns["file_modification"]["confidence"] > 0.7
    
    def test_detect_function_creation(self, detector):
        """Test detection of function/class creation patterns"""
        creation_texts = [
            "def calculate_total(items):",
            "class UserAuthenticator:",
            "function processPayment(amount) {",
            "public class PaymentProcessor {",
            "impl UserService for Database {",
            "fn hash_password(password: &str) -> String {"
        ]
        
        for text in creation_texts:
            patterns = detector.detect_patterns(text)
            assert patterns["function_creation"]["detected"], f"Failed to detect function creation in: {text}"
    
    def test_detect_import_statements(self, detector):
        """Test detection of import/dependency patterns"""
        import_texts = [
            "import pandas as pd",
            "from flask import Flask, request",
            "const express = require('express');",
            "use std::collections::HashMap;",
            "using System.Collections.Generic;",
            "#include <iostream>"
        ]
        
        for text in import_texts:
            patterns = detector.detect_patterns(text)
            assert patterns["imports"]["detected"], f"Failed to detect import in: {text}"
    
    def test_tool_call_detection(self, detector):
        """Test detection of code-related tool calls"""
        tool_messages = [
            {"tool": "Write", "parameters": {"file_path": "app.py"}},
            {"tool": "Edit", "parameters": {"file_path": "main.js", "old_string": "bug"}},
            {"tool": "MultiEdit", "parameters": {"file_path": "utils.py"}},
        ]
        
        for tool_msg in tool_messages:
            patterns = detector.detect_tool_patterns(tool_msg)
            assert patterns["code_modification"]["detected"], f"Failed to detect code tool: {tool_msg}"
            assert patterns["code_modification"]["confidence"] > 0.9
    
    def test_programming_language_detection(self, detector):
        """Test detection of specific programming languages"""
        language_examples = [
            ("def function():", "python"),
            ("function() {}", "javascript"),
            ("fn function() {}", "rust"),
            ("func function() {}", "go"),
            ("public void function() {}", "java"),
            ("function() {", "c"),
        ]
        
        for code, expected_lang in language_examples:
            patterns = detector.detect_patterns(code)
            detected_langs = patterns["programming_languages"]["languages"]
            assert expected_lang in detected_langs, f"Failed to detect {expected_lang} in: {code}"


class TestErrorPatternDetector:
    """Test suite for error pattern detection"""
    
    @pytest.fixture
    def detector(self):
        """Create error pattern detector"""
        return ErrorPatternDetector()
    
    def test_detect_error_keywords(self, detector):
        """Test detection of error-related keywords"""
        error_texts = [
            "NameError: name 'variable' is not defined",
            "TypeError: cannot concatenate str and int",
            "IndexError: list index out of range", 
            "AttributeError: object has no attribute",
            "ValueError: invalid literal for int()",
            "Exception occurred during processing",
            "Traceback (most recent call last):",
            "Stack trace shows error in line 42",
            "Critical bug found in payment system",
            "Fatal error: cannot connect to database"
        ]
        
        for text in error_texts:
            patterns = detector.detect_patterns(text)
            assert patterns["error_keywords"]["detected"], f"Failed to detect error in: {text}"
            assert patterns["error_keywords"]["confidence"] > 0.8
    
    def test_detect_solution_patterns(self, detector):
        """Test detection of solution/fix patterns"""
        solution_texts = [
            "Fixed the bug by adding null check",
            "Resolved issue by updating dependencies",
            "Solution: use try-catch block",
            "Debugging revealed the problem was",
            "To fix this error, we need to",
            "The issue is resolved by importing",
            "Patch applied successfully",
            "Workaround: use alternative method"
        ]
        
        for text in solution_texts:
            patterns = detector.detect_patterns(text)
            assert patterns["solution_keywords"]["detected"], f"Failed to detect solution in: {text}"
    
    def test_detect_debugging_activities(self, detector):
        """Test detection of debugging-related activities"""
        debugging_texts = [
            "Adding print statements to debug",
            "Setting breakpoint at line 45",
            "Analyzing stack trace to find root cause",
            "Testing with different input values",
            "Stepping through code execution",
            "Examining variable values",
            "Reproducing the error locally"
        ]
        
        for text in debugging_texts:
            patterns = detector.detect_patterns(text)
            assert patterns["debugging_activity"]["detected"], f"Failed to detect debugging in: {text}"
    
    def test_detect_test_failures(self, detector):
        """Test detection of test failure patterns"""
        test_failure_texts = [
            "Test failed: expected 5 but got 3",
            "AssertionError in test_user_login",
            "Unit test failing on line 23",
            "Integration test error: timeout",
            "pytest: FAILED tests/test_auth.py",
            "Test suite completed with 3 failures"
        ]
        
        for text in test_failure_texts:
            patterns = detector.detect_patterns(text)
            assert patterns["test_failure"]["detected"], f"Failed to detect test failure in: {text}"


class TestArchitecturalPatternDetector:
    """Test suite for architectural pattern detection"""
    
    @pytest.fixture
    def detector(self):
        """Create architectural pattern detector"""
        return ArchitecturalPatternDetector()
    
    def test_detect_design_patterns(self, detector):
        """Test detection of design pattern discussions"""
        design_texts = [
            "Implementing factory pattern for user creation",
            "Using observer pattern for event handling", 
            "Singleton pattern for database connection",
            "Strategy pattern for payment processing",
            "Builder pattern for complex objects",
            "Decorator pattern to add functionality",
            "MVC architecture for web application"
        ]
        
        for text in design_texts:
            patterns = detector.detect_patterns(text)
            assert patterns["design_patterns"]["detected"], f"Failed to detect design pattern in: {text}"
    
    def test_detect_architectural_decisions(self, detector):
        """Test detection of architectural decision keywords"""
        architecture_texts = [
            "Architecture decision: use microservices",
            "Framework choice: React vs Vue.js",
            "Database design: PostgreSQL with Redis cache", 
            "API design: REST vs GraphQL",
            "Deployment strategy: Docker containers",
            "Security approach: JWT with OAuth2",
            "Scalability plan: horizontal scaling"
        ]
        
        for text in architecture_texts:
            patterns = detector.detect_patterns(text)
            assert patterns["architectural_decisions"]["detected"], f"Failed to detect architecture in: {text}"
    
    def test_detect_technology_choices(self, detector):
        """Test detection of technology selection discussions"""
        technology_texts = [
            "Choosing between React and Angular",
            "Database: MongoDB vs PostgreSQL",
            "Cloud provider: AWS vs Azure vs GCP",
            "Programming language: Python vs Node.js",
            "Framework: Django vs Flask vs FastAPI",
            "Testing library: Jest vs Mocha"
        ]
        
        for text in technology_texts:
            patterns = detector.detect_patterns(text)
            assert patterns["technology_choices"]["detected"], f"Failed to detect technology choice in: {text}"
    
    def test_detect_system_design(self, detector):
        """Test detection of system design discussions"""
        system_texts = [
            "Load balancer distributes traffic",
            "Message queue for async processing",
            "Caching layer for performance",
            "Database sharding strategy",
            "Service mesh for communication",
            "Event-driven architecture",
            "API gateway pattern"
        ]
        
        for text in system_texts:
            patterns = detector.detect_patterns(text)
            assert patterns["system_design"]["detected"], f"Failed to detect system design in: {text}"


class TestHookPatternDetector:
    """Test suite for hook system pattern detection"""
    
    @pytest.fixture
    def detector(self):
        """Create hook pattern detector"""
        return HookPatternDetector()
    
    def test_detect_hook_execution_logs(self, detector):
        """Test detection of hook execution messages"""
        hook_texts = [
            "Hook: pre_tool_validator executed successfully",
            "Post-tool hook: logging action to database",
            "Context pruning hook: removed 50 entries",
            "Security hook: validated file permissions",
            "[HOOK] Memory optimization completed",
            "Auto-commit hook: changes saved to git",
            "Hook execution time: 0.05 seconds"
        ]
        
        for text in hook_texts:
            patterns = detector.detect_patterns(text)
            assert patterns["hook_execution"]["detected"], f"Failed to detect hook in: {text}"
            assert patterns["hook_execution"]["confidence"] > 0.9
    
    def test_detect_hook_types(self, detector):
        """Test detection of specific hook types"""
        hook_type_examples = [
            ("pre_tool_validator", "pre_tool"),
            ("post_tool_logger", "post_tool"),
            ("context_pruner", "context"),
            ("security_validator", "security"),
            ("memory_optimizer", "optimization"),
            ("auto_commit_hook", "automation")
        ]
        
        for hook_name, expected_type in hook_type_examples:
            text = f"Hook: {hook_name} executed"
            patterns = detector.detect_patterns(text)
            
            detected_types = patterns["hook_types"]["types"]
            assert expected_type in detected_types, f"Failed to detect {expected_type} hook type in: {text}"
    
    def test_detect_automation_messages(self, detector):
        """Test detection of automation system messages"""
        automation_texts = [
            "Automated backup completed successfully",
            "Scheduled task: update dependencies",
            "Auto-formatting applied to code",
            "Continuous integration pipeline triggered",
            "Automatic deployment to staging environment"
        ]
        
        for text in automation_texts:
            patterns = detector.detect_patterns(text)
            assert patterns["automation"]["detected"], f"Failed to detect automation in: {text}"


class TestSystemPatternDetector:
    """Test suite for system validation pattern detection"""
    
    @pytest.fixture
    def detector(self):
        """Create system pattern detector"""
        return SystemPatternDetector()
    
    def test_detect_validation_messages(self, detector):
        """Test detection of system validation patterns"""
        validation_texts = [
            "File permissions validated successfully",
            "Syntax check passed",
            "Dependencies are up to date",
            "Configuration validated",
            "Health check: all systems operational",
            "Security scan completed - no issues",
            "Code formatting check passed"
        ]
        
        for text in validation_texts:
            patterns = detector.detect_patterns(text)
            assert patterns["validation"]["detected"], f"Failed to detect validation in: {text}"
    
    def test_detect_status_messages(self, detector):
        """Test detection of system status messages"""
        status_texts = [
            "System ready",
            "Service started successfully",
            "Connection established",
            "Database online",
            "All services running",
            "Ready to process requests"
        ]
        
        for text in status_texts:
            patterns = detector.detect_patterns(text)
            assert patterns["status"]["detected"], f"Failed to detect status in: {text}"
    
    def test_detect_confirmation_messages(self, detector):
        """Test detection of simple confirmation messages"""
        confirmation_texts = [
            "OK",
            "Done",
            "Success",
            "Completed",
            "Acknowledged",
            "Confirmed",
            "Received"
        ]
        
        for text in confirmation_texts:
            patterns = detector.detect_patterns(text)
            assert patterns["confirmation"]["detected"], f"Failed to detect confirmation in: {text}"
    
    def test_detect_empty_content(self, detector):
        """Test detection of empty or minimal content"""
        empty_contents = [
            "",
            "   ",
            "\n\n",
            "\t",
            ".",
            "-"
        ]
        
        for content in empty_contents:
            patterns = detector.detect_patterns(content)
            assert patterns["empty_content"]["detected"], f"Failed to detect empty content: '{content}'"


class TestPatternPerformance:
    """Test pattern detection performance requirements"""
    
    def test_regex_compilation_caching(self):
        """Test that regex patterns are compiled and cached for performance"""
        detector = CodePatternDetector()
        
        # Access compiled patterns
        assert hasattr(detector, '_compiled_patterns')
        assert len(detector._compiled_patterns) > 0
        
        # All patterns should be compiled regex objects
        for pattern in detector._compiled_patterns.values():
            assert isinstance(pattern, re.Pattern)
    
    def test_pattern_detection_speed(self):
        """Test that pattern detection meets performance requirements"""
        import time
        
        detector = PatternAnalyzer()
        
        # Generate test content
        test_contents = [
            "Edit file main.py to fix critical bug",
            "Architecture: microservices with Docker",
            "Hook: validation completed successfully",
            "How do I implement authentication?",
            "NameError in calculate_total function",
            "Reading configuration file"
        ] * 100  # 600 total analyses
        
        # Measure pattern detection time
        start_time = time.time()
        results = [detector.analyze_content(content) for content in test_contents]
        detection_time = time.time() - start_time
        
        # Should complete quickly (< 0.2 seconds for 600 analyses)
        assert detection_time < 0.2, f"Pattern detection took {detection_time:.3f} seconds"
        assert len(results) == 600
    
    def test_memory_efficiency_patterns(self):
        """Test memory efficiency of pattern detection"""
        import tracemalloc
        
        detector = PatternAnalyzer()
        test_content = "Edit file main.py to fix critical IndexError bug with new architecture"
        
        tracemalloc.start()
        
        # Analyze same content many times to test for memory leaks
        for _ in range(1000):
            patterns = detector.analyze_content(test_content)
            assert "code_changes" in patterns
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Memory usage should be minimal (< 2MB)
        peak_mb = peak / 1024 / 1024
        assert peak_mb < 2, f"Memory usage was {peak_mb:.2f} MB, expected < 2 MB"


class TestPatternValidation:
    """Test pattern detection accuracy and validation"""
    
    @pytest.mark.parametrize(
        "content,expected_patterns,description",
        [
            # Code modification patterns
            ("Edit main.py file", ["code_changes", "file_modification"], "Basic file edit"),
            ("def new_function():", ["code_changes", "function_creation"], "Function definition"),
            ("import pandas as pd", ["code_changes", "imports"], "Import statement"),
            
            # Error/solution patterns
            ("NameError: variable not defined", ["error_solution", "error_keywords"], "Python error"),
            ("Fixed bug by adding null check", ["error_solution", "solution_keywords"], "Bug fix"),
            ("Debugging the authentication issue", ["error_solution", "debugging_activity"], "Debugging"),
            
            # Architectural patterns
            ("Use factory pattern for user creation", ["architectural_decision", "design_patterns"], "Design pattern"),
            ("Architecture: microservices approach", ["architectural_decision"], "Architecture decision"),
            
            # Hook patterns
            ("Hook: pre_tool_validator executed", ["hook_log", "hook_execution"], "Hook execution"),
            ("Auto-commit hook saved changes", ["hook_log", "automation"], "Automation hook"),
            
            # System patterns
            ("File permissions validated", ["system_validation", "validation"], "System validation"),
            ("OK", ["system_validation", "confirmation"], "Simple confirmation"),
            ("", ["system_validation", "empty_content"], "Empty content"),
        ],
    )
    def test_pattern_detection_accuracy(self, content, expected_patterns, description):
        """Test accuracy of pattern detection for known examples"""
        analyzer = PatternAnalyzer()
        patterns = analyzer.analyze_content(content)
        
        for expected_pattern in expected_patterns:
            assert expected_pattern in patterns, f"{description}: Missing pattern '{expected_pattern}' in: {content}"
            assert patterns[expected_pattern]["detected"], f"{description}: Pattern '{expected_pattern}' not detected in: {content}"
            assert patterns[expected_pattern]["confidence"] > 0.5, f"{description}: Low confidence for '{expected_pattern}' in: {content}"