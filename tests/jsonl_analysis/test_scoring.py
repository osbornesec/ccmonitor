"""
Test suite for importance scoring algorithm
Following TDD methodology - tests written before implementation
"""

import pytest
import json
from pathlib import Path

# Import the modules we'll implement
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from src.jsonl_analysis.scoring import ImportanceScorer, MessageScoreAnalyzer
from src.jsonl_analysis.exceptions import InvalidMessageError


class TestImportanceScorer:
    """Test suite for message importance scoring algorithm"""
    
    @pytest.fixture
    def scorer(self):
        """Create scorer instance with default weights"""
        return ImportanceScorer()
    
    @pytest.fixture
    def custom_scorer(self):
        """Create scorer with custom weight configuration"""
        custom_weights = {
            "code_changes": 45,      # Higher weight for code
            "error_solution": 40,    # High weight for solutions
            "architectural_decision": 35,
            "user_question": 25,     # Higher weight for questions
            "file_modification": 30,
            "debugging_info": 20,
            "hook_log": -35,         # Higher penalty for hooks
            "system_validation": -30,
            "empty_output": -25
        }
        return ImportanceScorer(weights=custom_weights)
    
    def test_code_change_scoring_high(self, scorer):
        """Test high importance scoring for code modifications"""
        code_messages = [
            {"message": {"content": "Edit file main.py to add new function"}},
            {"message": {"content": "Write new implementation in src/utils.py"}},
            {"message": {"content": "Create class UserAuthenticator"}},
            {"message": {"content": "Implement error handling in login()"}},
            {"type": "tool_call", "message": {"tool": "Write", "parameters": {"file_path": "app.py"}}},
            {"type": "tool_call", "message": {"tool": "Edit", "parameters": {"file_path": "config.py"}}},
        ]
        
        for msg in code_messages:
            score = scorer.calculate_message_importance(msg)
            # Code messages should score high (>= 30) - they may match different patterns with different weights
            assert score >= 30, f"Code message scored {score}, expected >= 30: {msg}"
    
    def test_error_solution_scoring_high(self, scorer):
        """Test high importance scoring for error/solution pairs"""
        error_solution_messages = [
            {"message": {"content": "Fix critical bug in payment processing"}},
            {"message": {"content": "Resolved NameError in calculate_total function"}},
            {"message": {"content": "Traceback shows issue in line 45: IndexError"}},
            {"message": {"content": "Error: Cannot find module 'express' - installing dependencies"}},
            {"message": {"content": "Exception in authentication: ValueError"}},
            {"message": {"content": "Debugging the failed test in test_user.py"}},
        ]
        
        for msg in error_solution_messages:
            score = scorer.calculate_message_importance(msg)
            assert score >= 35, f"Error/solution message scored {score}, expected >= 35: {msg}"
    
    def test_architectural_decision_scoring(self, scorer):
        """Test scoring for architectural and design decisions"""
        architectural_messages = [
            {"message": {"content": "Decided to use REST API instead of GraphQL"}},
            {"message": {"content": "Architecture: microservices with Docker containers"}},
            {"message": {"content": "Design pattern: implementing factory method"}},
            {"message": {"content": "Database schema: users table with foreign keys"}},
            {"message": {"content": "Framework choice: React for frontend, Node.js backend"}},
            {"message": {"content": "Security approach: JWT tokens with refresh mechanism"}},
        ]
        
        for msg in architectural_messages:
            score = scorer.calculate_message_importance(msg)
            assert score >= 30, f"Architectural message scored {score}, expected >= 30: {msg}"
    
    def test_user_question_scoring_medium(self, scorer):
        """Test medium importance scoring for user questions"""
        question_messages = [
            {"type": "user", "message": {"content": "How do I implement authentication?"}},
            {"type": "user", "message": {"content": "What's the best way to handle errors?"}},
            {"type": "user", "message": {"content": "Can you help me optimize this query?"}},
            {"type": "user", "message": {"content": "Why is my API returning 500 errors?"}},
        ]
        
        for msg in question_messages:
            score = scorer.calculate_message_importance(msg)
            # User questions should score at least 20, but may score higher if they contain other important keywords
            assert score >= 20, f"User question scored {score}, expected >= 20: {msg}"
            # Should not exceed 100 (clamped)
            assert score <= 100, f"User question scored {score}, expected <= 100: {msg}"
    
    def test_file_modification_scoring_medium(self, scorer):
        """Test medium importance scoring for file operations"""
        file_messages = [
            {"type": "tool_call", "message": {"tool": "Read", "parameters": {"file_path": "main.py"}}},
            {"type": "tool_call", "message": {"tool": "Glob", "parameters": {"pattern": "*.py"}}},
            {"message": {"content": "Reading configuration file to understand setup"}},
            {"message": {"content": "Examining the project structure"}},
        ]
        
        for msg in file_messages:
            score = scorer.calculate_message_importance(msg)
            # File operations should score in medium range - tool calls may score higher due to combined patterns
            assert score >= 10, f"File modification scored {score}, expected >= 10: {msg}"
            assert score <= 50, f"File modification scored {score}, expected <= 50: {msg}"
    
    def test_hook_log_penalty_high(self, scorer):
        """Test high penalty scoring for hook system logs"""
        hook_messages = [
            {"message": {"content": "Hook: pre_tool_validator executed successfully"}},
            {"message": {"content": "Post-tool hook: logging action to database"}},
            {"message": {"content": "Context pruning hook: removed 50 entries"}},
            {"message": {"content": "Security hook: validated file permissions"}},
            {"message": {"content": "[HOOK] Memory optimization completed"}},
            {"message": {"content": "Auto-commit hook: changes saved to git"}},
        ]
        
        for msg in hook_messages:
            score = scorer.calculate_message_importance(msg)
            assert score <= 10, f"Hook message scored {score}, expected <= 10: {msg}"
    
    def test_system_validation_penalty(self, scorer):
        """Test penalty scoring for system validation messages"""
        validation_messages = [
            {"message": {"content": "File permissions validated successfully"}},
            {"message": {"content": "Syntax check passed"}},
            {"message": {"content": "Dependencies are up to date"}},
            {"message": {"content": "Configuration validated"}},
            {"message": {"content": "Health check: all systems operational"}},
        ]
        
        for msg in validation_messages:
            score = scorer.calculate_message_importance(msg)
            assert score <= 15, f"Validation message scored {score}, expected <= 15: {msg}"
    
    def test_empty_output_penalty(self, scorer):
        """Test penalty scoring for empty or minimal output"""
        empty_messages = [
            {"message": {"content": ""}},
            {"message": {"content": "   "}},  # Whitespace only
            {"message": {"content": "OK"}},
            {"message": {"content": "Done"}},
            {"message": {"content": "Success"}},
            {"message": {"result": ""}},  # Empty tool result
        ]
        
        for msg in empty_messages:
            score = scorer.calculate_message_importance(msg)
            assert score <= 5, f"Empty message scored {score}, expected <= 5: {msg}"
    
    def test_edge_case_scoring(self, scorer):
        """Test scoring for edge cases and unusual message structures"""
        edge_cases = [
            {},  # Completely empty message
            {"message": {}},  # Empty message content
            {"type": "unknown", "message": {"content": "Unknown message type"}},
            {"message": {"content": None}},  # Null content
            {"message": {"content": "A" * 10000}},  # Very long content
        ]
        
        for msg in edge_cases:
            # Should not raise exception and return reasonable score
            score = scorer.calculate_message_importance(msg)
            assert 0 <= score <= 100, f"Edge case scored {score}, expected 0-100: {msg}"
    
    def test_score_bounds(self, scorer):
        """Test that scores are always within 0-100 range"""
        # Test extreme cases that should be clamped
        test_messages = [
            # Multiple high-value indicators (should clamp to 100)
            {"message": {"content": "Fix critical bug by implementing new architecture and editing main.py"}},
            # Multiple penalties (should clamp to 0)
            {"message": {"content": "Hook: validation completed successfully with empty result"}},
        ]
        
        for msg in test_messages:
            score = scorer.calculate_message_importance(msg)
            assert 0 <= score <= 100, f"Score {score} outside bounds for: {msg}"
    
    def test_custom_weights(self, custom_scorer):
        """Test scorer with custom weight configuration"""
        code_msg = {"message": {"content": "Edit file main.py"}}
        question_msg = {"type": "user", "message": {"content": "How do I fix this?"}}
        
        # Custom scorer should give different scores
        code_score = custom_scorer.calculate_message_importance(code_msg)
        question_score = custom_scorer.calculate_message_importance(question_msg)
        
        assert code_score >= 45, f"Custom code score {code_score}, expected >= 45"
        assert question_score >= 25, f"Custom question score {question_score}, expected >= 25"


class TestMessageScoreAnalyzer:
    """Test suite for analyzing message score distributions and patterns"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return MessageScoreAnalyzer()
    
    @pytest.fixture
    def sample_conversation(self):
        """Create sample conversation with varying importance levels"""
        return [
            {"uuid": "msg-1", "type": "user", "message": {"content": "Help me debug this error"}},
            {"uuid": "msg-2", "type": "assistant", "message": {"content": "I'll help you fix the error"}},
            {"uuid": "msg-3", "type": "tool_call", "message": {"tool": "Read", "parameters": {"file_path": "app.py"}}},
            {"uuid": "msg-4", "type": "assistant", "message": {"content": "Found the bug: NameError in line 42"}},
            {"uuid": "msg-5", "type": "tool_call", "message": {"tool": "Edit", "parameters": {"file_path": "app.py"}}},
            {"uuid": "msg-6", "type": "assistant", "message": {"content": "Fixed the error by importing missing module"}},
            {"uuid": "msg-7", "type": "tool_call", "message": {"tool": "Bash", "parameters": {"command": "python app.py"}}},
            {"uuid": "msg-8", "type": "assistant", "message": {"content": "Hook: post_tool_logger executed"}},
            {"uuid": "msg-9", "type": "assistant", "message": {"content": "Test passed successfully"}},
        ]
    
    def test_analyze_score_distribution(self, analyzer, sample_conversation):
        """Test analysis of importance score distribution"""
        distribution = analyzer.analyze_score_distribution(sample_conversation)
        
        # Should categorize messages by importance level
        assert "high" in distribution  # >= 70 points
        assert "medium" in distribution  # 30-69 points
        assert "low" in distribution  # < 30 points
        
        # Should have reasonable distribution
        total_messages = distribution["high"] + distribution["medium"] + distribution["low"]
        assert total_messages == len(sample_conversation)
        
        # Specific expectations for this conversation
        assert distribution["high"] >= 2, "Should have high-importance messages (error fixing, code editing)"
        assert distribution["low"] >= 1, "Should have low-importance messages (hook logs)"
    
    def test_identify_important_patterns(self, analyzer, sample_conversation):
        """Test identification of important conversation patterns"""
        patterns = analyzer.identify_important_patterns(sample_conversation)
        
        # Should identify error-solution patterns
        assert "error_solution_pairs" in patterns
        assert len(patterns["error_solution_pairs"]) >= 1
        
        # Should identify tool usage sequences
        assert "tool_sequences" in patterns
        assert len(patterns["tool_sequences"]) >= 1
        
        # Should identify code modification chains
        assert "code_modification_chains" in patterns
    
    def test_calculate_conversation_value(self, analyzer, sample_conversation):
        """Test calculation of overall conversation value"""
        value_metrics = analyzer.calculate_conversation_value(sample_conversation)
        
        # Should provide multiple value metrics
        assert "total_score" in value_metrics
        assert "average_score" in value_metrics
        assert "high_value_ratio" in value_metrics
        assert "pruning_potential" in value_metrics
        
        # Scores should be reasonable
        assert value_metrics["total_score"] > 0
        assert 0 <= value_metrics["average_score"] <= 100
        assert 0 <= value_metrics["high_value_ratio"] <= 1
        assert 0 <= value_metrics["pruning_potential"] <= 1
    
    def test_recommend_pruning_threshold(self, analyzer, sample_conversation):
        """Test recommendation of optimal pruning thresholds"""
        recommendation = analyzer.recommend_pruning_threshold(
            sample_conversation, 
            target_reduction=0.5  # 50% reduction
        )
        
        # Should provide threshold recommendation
        assert "threshold" in recommendation
        assert "predicted_reduction" in recommendation
        assert "preserved_messages" in recommendation
        assert "removed_messages" in recommendation
        
        # Threshold should be reasonable
        assert 0 <= recommendation["threshold"] <= 100
        assert abs(recommendation["predicted_reduction"] - 0.5) < 0.2  # Within 20% of target


class TestParametrizedScoring:
    """Parametrized tests for comprehensive scoring validation"""
    
    @pytest.mark.parametrize(
        "content,expected_min_score,description",
        [
            # High importance scenarios
            ("Edit file main.py to fix critical bug", 70, "Code fix combination"),
            ("Implement new authentication system", 40, "Code implementation"),
            ("Architecture decision: use microservices", 30, "Architectural decision"),
            ("Fix IndexError in process_data function", 35, "Error solution"),
            
            # Medium importance scenarios
            ("How do I handle user authentication?", 20, "User question"),
            ("Reading configuration file", 15, "File operation"),
            ("Analyzing project structure", 10, "Analysis activity"),
            
            # Low importance scenarios  
            ("Hook: validation completed", 0, "Hook log"),
            ("Syntax check passed", 0, "System validation"),
            ("", 0, "Empty content"),
            ("OK", 0, "Minimal response"),
        ],
    )
    def test_scoring_scenarios(self, content, expected_min_score, description):
        """Test various scoring scenarios with expected minimum scores"""
        scorer = ImportanceScorer()
        message = {"message": {"content": content}}
        
        score = scorer.calculate_message_importance(message)
        assert score >= expected_min_score, f"{description}: scored {score}, expected >= {expected_min_score}"
    
    @pytest.mark.parametrize(
        "tool_name,expected_category",
        [
            ("Write", "high"),      # File modification
            ("Edit", "high"),       # File modification
            ("Read", "medium"),     # File reading
            ("Glob", "medium"),     # File discovery
            ("Grep", "medium"),     # Content search
            ("Bash", "medium"),     # Command execution
            ("TodoWrite", "low"),   # Todo management
        ],
    )
    def test_tool_call_scoring(self, tool_name, expected_category):
        """Test scoring of different tool call types"""
        scorer = ImportanceScorer()
        message = {
            "type": "tool_call",
            "message": {
                "tool": tool_name,
                "parameters": {"test": "value"},
                "result": "Tool execution result"
            }
        }
        
        score = scorer.calculate_message_importance(message)
        
        # Define score ranges for categories
        if expected_category == "high":
            assert score >= 30, f"{tool_name} tool scored {score}, expected high (>= 30)"
        elif expected_category == "medium":
            assert 10 <= score < 30, f"{tool_name} tool scored {score}, expected medium (10-29)"
        else:  # low
            assert score < 10, f"{tool_name} tool scored {score}, expected low (< 10)"
    
    @pytest.mark.parametrize(
        "message_type,base_content,expected_boost",
        [
            ("user", "How do I implement this feature?", True),    # User questions get boost
            ("assistant", "I'll help you implement it", False),   # Assistant responses don't
            ("tool_call", "Read file.py", False),                # Tool calls scored separately
        ],
    )
    def test_message_type_influence(self, message_type, base_content, expected_boost):
        """Test how message type influences scoring"""
        scorer = ImportanceScorer()
        
        message = {
            "type": message_type,
            "message": {"content": base_content}
        }
        
        score = scorer.calculate_message_importance(message)
        
        if expected_boost and message_type == "user":
            # User questions should get importance boost
            assert score >= 20, f"User message scored {score}, expected boost for questions"


class TestScoringPerformance:
    """Test scoring algorithm performance requirements"""
    
    def test_scoring_speed(self):
        """Test that scoring meets performance requirements"""
        import time
        
        scorer = ImportanceScorer()
        
        # Generate large set of messages for performance testing
        test_messages = []
        for i in range(1000):
            content_types = [
                f"Edit file{i}.py",
                f"Fix error in function{i}",
                f"How do I implement feature{i}?",
                f"Hook: action{i} completed",
                f"Reading file{i}.txt",
                ""
            ]
            content = content_types[i % len(content_types)]
            
            message = {
                "type": "user" if i % 3 == 0 else "assistant",
                "message": {"content": content}
            }
            test_messages.append(message)
        
        # Measure scoring performance
        start_time = time.time()
        scores = [scorer.calculate_message_importance(msg) for msg in test_messages]
        scoring_time = time.time() - start_time
        
        # Should score 1000 messages in reasonable time (< 0.1 seconds)
        assert scoring_time < 0.1, f"Scoring took {scoring_time:.3f} seconds for 1000 messages"
        assert len(scores) == 1000
        assert all(0 <= score <= 100 for score in scores)
    
    def test_memory_efficiency(self):
        """Test that scorer doesn't leak memory with repeated use"""
        import tracemalloc
        
        scorer = ImportanceScorer()
        
        # Test message
        message = {"message": {"content": "Edit file main.py to fix bug"}}
        
        tracemalloc.start()
        
        # Score message many times to test for memory leaks
        for _ in range(10000):
            score = scorer.calculate_message_importance(message)
            assert 0 <= score <= 100
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Memory usage should be minimal (< 1MB)
        peak_mb = peak / 1024 / 1024
        assert peak_mb < 1, f"Memory usage was {peak_mb:.2f} MB, expected < 1 MB"