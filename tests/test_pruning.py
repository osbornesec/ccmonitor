"""
Comprehensive test suite for Phase 2 Core Pruning Engine
Following TDD methodology - tests written before implementation

Tests cover:
1. Core JSONLPruner functionality
2. Context-aware compression algorithms  
3. Content filtering system
4. Conversation dependency preservation
5. Performance and memory targets
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime
import time
import psutil
import os

# Import Phase 1 components that are validated
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.jsonl_analysis.analyzer import JSONLAnalyzer, ConversationFlowAnalyzer
from src.jsonl_analysis.scoring import ImportanceScorer, MessageScoreAnalyzer
from src.jsonl_analysis.patterns import PatternAnalyzer


class TestJSONLPruner:
    """Test suite for core JSONLPruner class with configurable pruning levels"""
    
    @pytest.fixture
    def sample_conversation_data(self):
        """Sample conversation data with various importance levels"""
        return [
            # High importance: User questions and error solutions
            {
                "uuid": "msg-001",
                "type": "user", 
                "parentUuid": None,
                "message": {"content": "I'm getting a NameError in my Python code. Can you help debug it?"},
                "timestamp": "2025-08-01T10:00:00"
            },
            {
                "uuid": "msg-002",
                "type": "assistant",
                "parentUuid": "msg-001", 
                "message": {"content": "I'll help debug the NameError. Let me examine your code file."},
                "timestamp": "2025-08-01T10:00:01"
            },
            {
                "uuid": "msg-003",
                "type": "tool_call",
                "parentUuid": "msg-002",
                "message": {
                    "tool": "Read",
                    "parameters": {"file_path": "/code/app.py"},
                    "result": "def function():\n    return undefined_var  # NameError here"
                },
                "timestamp": "2025-08-01T10:00:02"
            },
            {
                "uuid": "msg-004", 
                "type": "assistant",
                "parentUuid": "msg-003",
                "message": {"content": "Found the issue! The variable 'undefined_var' is not defined. Here's the fix:"},
                "timestamp": "2025-08-01T10:00:03"
            },
            {
                "uuid": "msg-005",
                "type": "tool_call",
                "parentUuid": "msg-004",
                "message": {
                    "tool": "Edit",
                    "parameters": {
                        "file_path": "/code/app.py",
                        "old_string": "return undefined_var",
                        "new_string": "return defined_var"
                    },
                    "result": "File edited successfully"
                },
                "timestamp": "2025-08-01T10:00:04"
            },
            
            # Medium importance: File operations and debugging
            {
                "uuid": "msg-006",
                "type": "tool_call", 
                "parentUuid": "msg-005",
                "message": {
                    "tool": "Bash",
                    "parameters": {"command": "python /code/app.py"},
                    "result": "Script runs successfully without errors"
                },
                "timestamp": "2025-08-01T10:00:05"
            },
            
            # Low importance: Hook logs and system validations
            {
                "uuid": "msg-007",
                "type": "system",
                "parentUuid": None,
                "message": {"content": "Hook: pre_tool_validator executed successfully"},
                "timestamp": "2025-08-01T10:00:06"
            },
            {
                "uuid": "msg-008",
                "type": "system", 
                "parentUuid": None,
                "message": {"content": "System validation: all dependencies up to date"},
                "timestamp": "2025-08-01T10:00:07"
            },
            {
                "uuid": "msg-009",
                "type": "tool_call",
                "parentUuid": "msg-002",
                "message": {
                    "tool": "TodoWrite",
                    "parameters": {"todos": []},
                    "result": "Todo list updated"
                },
                "timestamp": "2025-08-01T10:00:08"
            },
            
            # Very low importance: Empty outputs and confirmations
            {
                "uuid": "msg-010",
                "type": "tool_call",
                "parentUuid": "msg-009", 
                "message": {
                    "tool": "Bash",
                    "parameters": {"command": "echo 'test'"},
                    "result": "test"
                },
                "timestamp": "2025-08-01T10:00:09"
            }
        ]
    
    @pytest.fixture
    def large_conversation_data(self):
        """Generate large conversation data for performance testing"""
        messages = []
        for i in range(1000):
            msg_type = "user" if i % 4 == 0 else "assistant" if i % 4 == 1 else "tool_call"
            parent = f"msg-{i:03d}" if i > 0 else None
            
            if msg_type == "tool_call":
                content = {
                    "tool": ["Read", "Write", "Bash", "Grep", "TodoWrite"][i % 5],
                    "parameters": {"file_path": f"/test/file_{i}.py"},
                    "result": f"Large output content for message {i}" + "x" * 100
                }
            else:
                content = {"content": f"Message {i} content with varying importance levels"}
                
            messages.append({
                "uuid": f"msg-{i+1:03d}",
                "type": msg_type,
                "parentUuid": parent,
                "message": content,
                "timestamp": f"2025-08-01T10:{i//60:02d}:{i%60:02d}"
            })
        return messages
    
    def test_pruner_initialization_with_default_settings(self):
        """Test JSONLPruner initializes with correct default settings"""
        from src.pruner.core import JSONLPruner
        
        pruner = JSONLPruner()
        
        assert pruner.pruning_level == "medium"
        assert pruner.importance_threshold == 40
        assert hasattr(pruner, 'importance_scorer')
        assert hasattr(pruner, 'pattern_analyzer')
        assert hasattr(pruner, 'flow_analyzer')
    
    def test_pruner_initialization_with_custom_levels(self):
        """Test pruner with different pruning levels"""
        from src.pruner.core import JSONLPruner
        
        # Test light pruning
        light_pruner = JSONLPruner(pruning_level='light')
        assert light_pruner.importance_threshold == 20
        
        # Test aggressive pruning  
        aggressive_pruner = JSONLPruner(pruning_level='aggressive')
        assert aggressive_pruner.importance_threshold == 60
        
        # Test invalid level raises error
        with pytest.raises(ValueError, match="Invalid pruning level"):
            JSONLPruner(pruning_level='invalid')
    
    def test_process_file_basic_functionality(self, sample_conversation_data):
        """Test basic file processing pipeline"""
        from src.pruner.core import JSONLPruner
        
        pruner = JSONLPruner(pruning_level='medium')
        
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in sample_conversation_data:
                json.dump(entry, f)
                f.write('\n')
            input_path = Path(f.name)
        
        # Process file
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            result = pruner.process_file(input_path, output_path)
            
            # Verify processing results
            assert 'messages_processed' in result
            assert 'messages_preserved' in result  
            assert 'messages_removed' in result
            assert 'compression_ratio' in result
            assert 'processing_time' in result
            
            # Verify output file exists and is valid
            assert output_path.exists()
            
            # Load and verify output
            pruned_messages = []
            with open(output_path, 'r') as f:
                for line in f:
                    if line.strip():
                        pruned_messages.append(json.loads(line))
            
            # Should have fewer messages than input
            assert len(pruned_messages) < len(sample_conversation_data)
            
            # High importance messages should be preserved
            preserved_uuids = {msg['uuid'] for msg in pruned_messages}
            assert 'msg-001' in preserved_uuids  # User question
            assert 'msg-004' in preserved_uuids  # Error solution
            assert 'msg-005' in preserved_uuids  # Code fix
            
        finally:
            # Cleanup
            input_path.unlink()
            output_path.unlink()
    
    def test_conversation_dependency_preservation(self, sample_conversation_data):
        """Test that conversation dependencies are preserved during pruning"""
        from src.pruner.core import JSONLPruner
        
        pruner = JSONLPruner(pruning_level='aggressive')  # Aggressive to test preservation
        
        # Create input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in sample_conversation_data:
                json.dump(entry, f)
                f.write('\n')
            input_path = Path(f.name)
        
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            pruner.process_file(input_path, output_path)
            
            # Load pruned messages
            pruned_messages = []
            with open(output_path, 'r') as f:
                for line in f:
                    if line.strip():
                        pruned_messages.append(json.loads(line))
            
            # Verify conversation chains are intact
            uuid_to_msg = {msg['uuid']: msg for msg in pruned_messages}
            
            for msg in pruned_messages:
                parent_uuid = msg.get('parentUuid')
                if parent_uuid:
                    # If message is preserved, its parent should be preserved too
                    assert parent_uuid in uuid_to_msg, f"Parent {parent_uuid} missing for preserved message {msg['uuid']}"
            
        finally:
            input_path.unlink()
            output_path.unlink()
    
    def test_configurable_compression_targets(self, sample_conversation_data):
        """Test that different pruning levels achieve different compression ratios"""
        from src.pruner.core import JSONLPruner
        
        results = {}
        
        for level in ['light', 'medium', 'aggressive']:
            pruner = JSONLPruner(pruning_level=level)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                for entry in sample_conversation_data:
                    json.dump(entry, f)
                    f.write('\n')
                input_path = Path(f.name)
            
            with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
                output_path = Path(f.name)
            
            try:
                result = pruner.process_file(input_path, output_path)
                results[level] = result['compression_ratio']
            finally:
                input_path.unlink()
                output_path.unlink()
        
        # More aggressive pruning should achieve higher compression
        assert results['light'] < results['medium'] < results['aggressive']
        
        # Should achieve target reduction ranges
        assert 0.2 <= results['light'] <= 0.4   # 20-40% reduction for light
        assert 0.4 <= results['medium'] <= 0.6  # 40-60% reduction for medium
        assert 0.6 <= results['aggressive'] <= 0.8  # 60-80% reduction for aggressive


class TestContextAwareCompression:
    """Test suite for context-aware compression algorithms"""
    
    @pytest.fixture
    def large_tool_output_message(self):
        """Message with large tool output for compression testing"""
        large_output = "Line " + "\n".join([f"Output line {i} with detailed information" for i in range(500)])
        
        return {
            "uuid": "msg-large",
            "type": "tool_call",
            "parentUuid": "msg-parent",
            "message": {
                "tool": "Read",
                "parameters": {"file_path": "/large/file.py"},
                "result": large_output
            },
            "timestamp": "2025-08-01T10:00:00"
        }
    
    @pytest.fixture
    def repetitive_log_messages(self):
        """Messages with repetitive log content"""
        return [
            {
                "uuid": f"log-{i:03d}",
                "type": "system",
                "parentUuid": None,
                "message": {"content": f"Hook: validation_hook executed successfully at step {i}"},
                "timestamp": f"2025-08-01T10:00:{i:02d}"
            }
            for i in range(20)
        ]
    
    def test_smart_truncation_preserves_key_content(self, large_tool_output_message):
        """Test that smart truncation preserves beginning and end of large outputs"""
        from src.pruner.compressor import SmartTruncator
        
        truncator = SmartTruncator(max_length=200, preserve_lines=3)
        
        original_content = large_tool_output_message["message"]["result"]
        truncated = truncator.truncate_content(original_content)
        
        # Should be shorter than original
        assert len(truncated) < len(original_content)
        
        # Should preserve beginning lines
        original_lines = original_content.split('\n')
        truncated_lines = truncated.split('\n')
        
        assert truncated_lines[0] == original_lines[0]
        assert truncated_lines[1] == original_lines[1]
        assert truncated_lines[2] == original_lines[2]
        
        # Should preserve ending lines  
        assert truncated_lines[-1] == original_lines[-1]
        assert truncated_lines[-2] == original_lines[-2]
        assert truncated_lines[-3] == original_lines[-3]
        
        # Should have truncation marker
        assert "... [TRUNCATED" in truncated
    
    def test_semantic_summarization_of_logs(self, repetitive_log_messages):
        """Test semantic summarization of repetitive content"""
        from src.pruner.compressor import SemanticSummarizer
        
        summarizer = SemanticSummarizer()
        
        # Should detect repetitive pattern and summarize
        summary = summarizer.summarize_repetitive_content(repetitive_log_messages)
        
        assert "validation_hook executed successfully" in summary["pattern"]
        assert summary["count"] == 20
        assert summary["compressed"] is True
        assert len(summary["summary"]) < sum(len(msg["message"]["content"]) for msg in repetitive_log_messages)
    
    def test_reference_preservation_analysis(self):
        """Test that content referenced by later messages is preserved"""
        from src.pruner.compressor import ReferenceAnalyzer
        
        messages = [
            {
                "uuid": "msg-001",
                "type": "tool_call",
                "message": {
                    "tool": "Read",
                    "parameters": {"file_path": "/code/utils.py"},
                    "result": "def important_function():\n    return 'critical logic'"
                }
            },
            {
                "uuid": "msg-002", 
                "type": "assistant",
                "message": {"content": "Looking at the important_function in utils.py, I see the issue."}
            },
            {
                "uuid": "msg-003",
                "type": "tool_call", 
                "message": {
                    "tool": "Read",
                    "parameters": {"file_path": "/code/other.py"},
                    "result": "def unused_function():\n    return 'not referenced'"
                }
            }
        ]
        
        analyzer = ReferenceAnalyzer()
        references = analyzer.analyze_cross_references(messages)
        
        # msg-001 should be marked as referenced by msg-002
        assert "msg-001" in references["referenced_messages"]
        assert "important_function" in references["referenced_content"]["msg-001"]
        
        # msg-003 should not be marked as referenced
        assert "msg-003" not in references["referenced_messages"]
    
    def test_conversation_chain_integrity_maintained(self):
        """Test that conversation dependency chains remain intact"""
        from src.pruner.compressor import ChainIntegrityValidator
        
        original_messages = [
            {"uuid": "msg-001", "parentUuid": None},
            {"uuid": "msg-002", "parentUuid": "msg-001"},
            {"uuid": "msg-003", "parentUuid": "msg-002"},
            {"uuid": "msg-004", "parentUuid": "msg-002"},  # Branch
            {"uuid": "msg-005", "parentUuid": "msg-004"}
        ]
        
        # Simulate pruning that removes msg-003
        pruned_messages = [
            {"uuid": "msg-001", "parentUuid": None},
            {"uuid": "msg-002", "parentUuid": "msg-001"},
            {"uuid": "msg-004", "parentUuid": "msg-002"},
            {"uuid": "msg-005", "parentUuid": "msg-004"}
        ]
        
        validator = ChainIntegrityValidator()
        integrity_result = validator.validate_chain_integrity(original_messages, pruned_messages)
        
        assert integrity_result["chains_preserved"] is True
        assert integrity_result["orphaned_messages"] == []
        assert integrity_result["broken_chains"] == []


class TestContentFilteringSystem:
    """Test suite for pattern-based content filtering system"""
    
    @pytest.fixture
    def mixed_importance_messages(self):
        """Messages with varying importance patterns"""
        return [
            # High importance: Code changes
            {
                "uuid": "high-001",
                "type": "tool_call",
                "message": {
                    "tool": "Write",
                    "parameters": {"file_path": "/code/app.py", "content": "def new_function(): pass"},
                    "result": "File written successfully"
                }
            },
            
            # Medium importance: File analysis  
            {
                "uuid": "med-001",
                "type": "tool_call",
                "message": {
                    "tool": "Read", 
                    "parameters": {"file_path": "/code/existing.py"},
                    "result": "Existing code content"
                }
            },
            
            # Low importance: Hook logs
            {
                "uuid": "low-001",
                "type": "system",
                "message": {"content": "Hook: pre_tool_validator executed successfully"}
            },
            
            # Very low importance: Empty outputs
            {
                "uuid": "vlow-001",
                "type": "tool_call",
                "message": {
                    "tool": "Bash",
                    "parameters": {"command": "ls"},
                    "result": ""
                }
            }
        ]
    
    def test_pattern_based_filtering_rules(self, mixed_importance_messages):
        """Test that filtering rules correctly categorize message importance"""
        from src.pruner.filters import ContentFilter
        
        filter_engine = ContentFilter()
        
        results = []
        for msg in mixed_importance_messages:
            classification = filter_engine.classify_message(msg)
            results.append((msg["uuid"], classification))
        
        # Verify classifications
        classifications = dict(results)
        assert classifications["high-001"]["category"] == "high_importance"
        assert classifications["med-001"]["category"] == "medium_importance" 
        assert classifications["low-001"]["category"] == "low_importance"
        assert classifications["vlow-001"]["category"] == "very_low_importance"
    
    def test_compression_rules_engine(self):
        """Test different compression rules for different content types"""
        from src.pruner.filters import CompressionRulesEngine
        
        rules_engine = CompressionRulesEngine()
        
        # Test hook log compression rule
        hook_message = {
            "type": "system",
            "message": {"content": "Hook: optimization_hook completed in 0.1s"}
        }
        
        rule = rules_engine.get_compression_rule(hook_message)
        assert rule["action"] == "compress_heavily"
        assert rule["preserve_summary"] is True
        assert rule["compression_ratio"] >= 0.8
        
        # Test code modification preservation rule
        code_message = {
            "type": "tool_call", 
            "message": {
                "tool": "Edit",
                "parameters": {"file_path": "/code/app.py"},
                "result": "Code successfully modified"
            }
        }
        
        rule = rules_engine.get_compression_rule(code_message)
        assert rule["action"] == "preserve"
        assert rule["compression_ratio"] == 0.0
    
    def test_content_classification_accuracy(self, mixed_importance_messages):
        """Test accuracy of content classification system"""
        from src.pruner.filters import ContentClassifier
        
        classifier = ContentClassifier()
        
        # Test against known classifications
        expected = {
            "high-001": "essential",
            "med-001": "informational", 
            "low-001": "system_noise",
            "vlow-001": "noise"
        }
        
        correct_classifications = 0
        for msg in mixed_importance_messages:
            classification = classifier.classify_content_type(msg)
            if classification == expected[msg["uuid"]]:
                correct_classifications += 1
        
        # Should achieve >90% accuracy
        accuracy = correct_classifications / len(mixed_importance_messages)
        assert accuracy >= 0.9
    
    def test_debugging_info_preservation(self):
        """Test that debugging information and error traces are preserved"""
        from src.pruner.filters import DebuggingPreserver
        
        error_message = {
            "uuid": "error-001",
            "type": "tool_call",
            "message": {
                "tool": "Bash", 
                "parameters": {"command": "python app.py"},
                "result": "Traceback (most recent call last):\n  File 'app.py', line 10\n    return undefined_var\nNameError: name 'undefined_var' is not defined"
            }
        }
        
        solution_message = {
            "uuid": "solution-001",
            "type": "assistant",
            "message": {"content": "The error is caused by undefined_var. Here's the fix:"}
        }
        
        preserver = DebuggingPreserver()
        
        assert preserver.should_preserve(error_message) is True
        assert preserver.should_preserve(solution_message) is True
        assert preserver.get_preservation_reason(error_message) == "error_trace"
        assert preserver.get_preservation_reason(solution_message) == "error_solution"


class TestPerformanceBenchmarks:
    """Test suite for performance and memory usage benchmarks"""
    
    def test_processing_speed_target(self, large_conversation_data):
        """Test that processing speed meets target of <1 second for 1000 messages"""
        from src.pruner.core import JSONLPruner
        
        pruner = JSONLPruner(pruning_level='medium')
        
        # Create large input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in large_conversation_data:
                json.dump(entry, f)
                f.write('\n')
            input_path = Path(f.name)
        
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            start_time = time.time()
            result = pruner.process_file(input_path, output_path)
            processing_time = time.time() - start_time
            
            # Should process 1000 messages in <1 second
            assert processing_time < 1.0
            assert result['processing_time'] < 1.0
            
            # Verify performance metrics
            messages_per_second = len(large_conversation_data) / processing_time
            assert messages_per_second > 1000  # >1000 messages/second
            
        finally:
            input_path.unlink()
            output_path.unlink()
    
    def test_memory_usage_efficiency(self, large_conversation_data):
        """Test memory usage stays under 100MB for large files"""
        from src.pruner.core import JSONLPruner
        
        # Monitor memory usage
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        pruner = JSONLPruner(pruning_level='medium')
        
        # Create very large input file (10MB+)
        large_data = large_conversation_data * 10  # 10,000 messages
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in large_data:
                json.dump(entry, f)
                f.write('\n')
            input_path = Path(f.name)
        
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            pruner.process_file(input_path, output_path)
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = memory_after - memory_before
            
            # Memory usage should be <100MB
            assert memory_used < 100
            
        finally:
            input_path.unlink() 
            output_path.unlink()
    
    def test_compression_ratio_targets(self, large_conversation_data):
        """Test that compression ratios meet 50-80% targets"""
        from src.pruner.core import JSONLPruner
        
        for level, expected_range in [
            ('light', (0.2, 0.4)),
            ('medium', (0.4, 0.6)), 
            ('aggressive', (0.6, 0.8))
        ]:
            pruner = JSONLPruner(pruning_level=level)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                for entry in large_conversation_data:
                    json.dump(entry, f)
                    f.write('\n')
                input_path = Path(f.name)
            
            with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
                output_path = Path(f.name)
            
            try:
                result = pruner.process_file(input_path, output_path)
                compression_ratio = result['compression_ratio']
                
                # Should meet target range
                min_ratio, max_ratio = expected_range
                assert min_ratio <= compression_ratio <= max_ratio
                
            finally:
                input_path.unlink()
                output_path.unlink()
    
    def test_quality_preservation_metrics(self, sample_conversation_data):
        """Test that <1% false positive rate for important content removal"""
        from src.pruner.core import JSONLPruner
        
        pruner = JSONLPruner(pruning_level='aggressive')  # Most aggressive for testing
        
        # Identify truly important messages manually
        important_uuids = {"msg-001", "msg-002", "msg-004", "msg-005"}  # User question, error solution, code fix
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in sample_conversation_data:
                json.dump(entry, f)
                f.write('\n')
            input_path = Path(f.name)
        
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            pruner.process_file(input_path, output_path)
            
            # Load pruned messages
            preserved_uuids = set()
            with open(output_path, 'r') as f:
                for line in f:
                    if line.strip():
                        msg = json.loads(line)
                        preserved_uuids.add(msg['uuid'])
            
            # Calculate false positive rate (important messages removed)
            important_removed = important_uuids - preserved_uuids
            false_positive_rate = len(important_removed) / len(important_uuids)
            
            # Should have <1% false positive rate
            assert false_positive_rate < 0.01
            
        finally:
            input_path.unlink()
            output_path.unlink()


class TestIntegrationScenarios:
    """Integration tests for end-to-end pruning scenarios"""
    
    def test_malformed_json_handling(self):
        """Test graceful handling of malformed JSON entries"""
        from src.pruner.core import JSONLPruner
        
        pruner = JSONLPruner()
        
        # Create file with malformed JSON
        malformed_content = '''{"uuid": "msg-001", "type": "user", "message": {"content": "valid message"}}
{"uuid": "msg-002", "type": "assistant", "message": {invalid json}
{"uuid": "msg-003", "type": "user", "message": {"content": "another valid message"}}'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write(malformed_content)
            input_path = Path(f.name)
        
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            result = pruner.process_file(input_path, output_path)
            
            # Should handle malformed entries gracefully
            assert 'malformed_entries' in result
            assert result['malformed_entries'] == 1
            
            # Valid entries should still be processed
            assert result['messages_processed'] == 2
            
        finally:
            input_path.unlink()
            output_path.unlink()
    
    def test_empty_file_handling(self):
        """Test handling of empty input files"""
        from src.pruner.core import JSONLPruner
        
        pruner = JSONLPruner()
        
        # Create empty file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            input_path = Path(f.name)
        
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            result = pruner.process_file(input_path, output_path)
            
            assert result['messages_processed'] == 0
            assert result['messages_preserved'] == 0
            assert result['compression_ratio'] == 0.0
            
        finally:
            input_path.unlink()
            output_path.unlink()
    
    def test_very_large_file_streaming(self):
        """Test streaming processing for very large files"""
        from src.pruner.core import JSONLPruner
        
        # This test would create a very large file (100MB+) to test streaming
        # For now, we'll test the streaming interface exists
        
        pruner = JSONLPruner()
        
        # Verify streaming methods exist
        assert hasattr(pruner, 'process_file_streaming')
        assert callable(getattr(pruner, 'process_file_streaming'))
    
    def test_concurrent_processing_safety(self):
        """Test that pruner is safe for concurrent use"""
        from src.pruner.core import JSONLPruner
        import threading
        
        # Test that multiple pruner instances can run concurrently
        pruners = [JSONLPruner() for _ in range(3)]
        
        # Each should have independent state
        for i, pruner in enumerate(pruners):
            assert id(pruner.importance_scorer) != id(pruners[0].importance_scorer) if i > 0 else True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])