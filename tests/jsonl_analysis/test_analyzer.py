"""
Test suite for JSONL analyzer module
Following TDD methodology - tests written before implementation
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import mock_open, patch

# Import the modules we'll implement
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from src.jsonl_analysis.analyzer import JSONLAnalyzer, ConversationFlowAnalyzer
from src.jsonl_analysis.exceptions import InvalidJSONLError, MalformedEntryError


class TestJSONLAnalyzer:
    """Test suite for basic JSONL parsing and structure validation"""
    
    @pytest.fixture
    def sample_jsonl_entries(self):
        """Factory for creating test JSONL entries"""
        return [
            {
                "uuid": "msg-001",
                "type": "user",
                "parentUuid": None,
                "message": {"content": "Hello, can you help me debug this code?"},
                "timestamp": "2025-08-01T19:51:21.024033"
            },
            {
                "uuid": "msg-002", 
                "type": "assistant",
                "parentUuid": "msg-001",
                "message": {"content": "I'll help you debug the code. Let me examine the file."},
                "timestamp": "2025-08-01T19:51:25.124033"
            },
            {
                "uuid": "msg-003",
                "type": "tool_call",
                "parentUuid": "msg-002", 
                "message": {
                    "tool": "Read",
                    "parameters": {"file_path": "/path/to/file.py"},
                    "result": "def buggy_function():\n    return x + y  # NameError"
                },
                "timestamp": "2025-08-01T19:51:26.124033"
            }
        ]
    
    @pytest.fixture
    def malformed_jsonl_entries(self):
        """Test data with various malformed entries"""
        return [
            '{"uuid": "valid-001", "type": "user", "message": {"content": "valid"}}',
            '{"uuid": "missing-type", "message": {"content": "no type field"}}',
            '{"uuid": "invalid-json", "type": "user" "message": "missing comma"}',
            '',  # Empty line
            'not json at all',
            '{"uuid": "msg-004", "type": "assistant", "message": {"content": "valid after errors"}}'
        ]
    
    def test_parse_jsonl_file_valid(self, sample_jsonl_entries):
        """Test basic JSONL file parsing with valid entries"""
        analyzer = JSONLAnalyzer()
        
        # Create temporary JSONL file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in sample_jsonl_entries:
                json.dump(entry, f)
                f.write('\n')
            temp_path = Path(f.name)
        
        try:
            # Test parsing
            entries = analyzer.parse_jsonl_file(temp_path)
            
            # Assertions
            assert len(entries) == 3
            assert entries[0]["uuid"] == "msg-001"
            assert entries[0]["type"] == "user"
            assert entries[1]["parentUuid"] == "msg-001"
            assert entries[2]["message"]["tool"] == "Read"
            
        finally:
            temp_path.unlink()  # Cleanup
    
    def test_parse_jsonl_file_malformed(self, malformed_jsonl_entries):
        """Test JSONL parsing with malformed entries"""
        analyzer = JSONLAnalyzer()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for line in malformed_jsonl_entries:
                f.write(line + '\n')
            temp_path = Path(f.name)
        
        try:
            # Should handle malformed entries gracefully
            entries = analyzer.parse_jsonl_file(temp_path)
            
            # Should only return valid entries
            assert len(entries) == 2  # Only valid and final valid entries
            assert entries[0]["uuid"] == "valid-001"
            assert entries[1]["uuid"] == "msg-004"
            
        finally:
            temp_path.unlink()
    
    def test_parse_nonexistent_file(self):
        """Test handling of nonexistent files"""
        analyzer = JSONLAnalyzer()
        
        with pytest.raises(FileNotFoundError):
            analyzer.parse_jsonl_file(Path("/nonexistent/file.jsonl"))
    
    def test_validate_entry_structure_valid(self, sample_jsonl_entries):
        """Test entry structure validation for valid entries"""
        analyzer = JSONLAnalyzer()
        
        for entry in sample_jsonl_entries:
            # Should not raise exception
            is_valid = analyzer.validate_entry_structure(entry)
            assert is_valid is True
    
    def test_validate_entry_structure_invalid(self):
        """Test entry structure validation for invalid entries"""
        analyzer = JSONLAnalyzer()
        
        invalid_entries = [
            {},  # Empty entry
            {"uuid": "test"},  # Missing required fields
            {"type": "user", "message": "test"},  # Missing uuid
            {"uuid": "test", "type": "invalid_type", "message": {"content": "test"}}  # Invalid type
        ]
        
        for entry in invalid_entries:
            is_valid = analyzer.validate_entry_structure(entry)
            assert is_valid is False
    
    def test_identify_message_types(self, sample_jsonl_entries):
        """Test categorization of user/assistant/system messages"""
        analyzer = JSONLAnalyzer()
        
        types = analyzer.identify_message_types(sample_jsonl_entries)
        
        expected_types = {
            "user": 1,
            "assistant": 1, 
            "tool_call": 1
        }
        
        assert types == expected_types
    
    def test_extract_tool_usage_patterns(self, sample_jsonl_entries):
        """Test identification and categorization of tool calls"""
        analyzer = JSONLAnalyzer()
        
        patterns = analyzer.extract_tool_usage_patterns(sample_jsonl_entries)
        
        # Should identify Read tool usage
        assert "Read" in patterns["tools_used"]
        assert patterns["tools_used"]["Read"] == 1
        assert patterns["total_tool_calls"] == 1
        assert patterns["tool_sequences"] == [["Read"]]


class TestConversationFlowAnalyzer:
    """Test suite for conversation dependency mapping and flow analysis"""
    
    @pytest.fixture
    def conversation_chain(self):
        """Create a conversation with branching and dependencies"""
        return [
            {"uuid": "root", "parentUuid": None, "type": "user", "message": {"content": "Start"}},
            {"uuid": "reply-1", "parentUuid": "root", "type": "assistant", "message": {"content": "Response 1"}},
            {"uuid": "tool-1", "parentUuid": "reply-1", "type": "tool_call", "message": {"tool": "Read"}},
            {"uuid": "reply-2", "parentUuid": "tool-1", "type": "assistant", "message": {"content": "Analysis"}},
            {"uuid": "user-2", "parentUuid": "reply-2", "type": "user", "message": {"content": "Follow up"}},
            {"uuid": "branch-1", "parentUuid": "reply-1", "type": "assistant", "message": {"content": "Alternative response"}},
            {"uuid": "orphan", "parentUuid": "nonexistent", "type": "user", "message": {"content": "Orphaned message"}}
        ]
    
    def test_map_conversation_dependencies(self, conversation_chain):
        """Test parentUuid chain mapping and flow analysis"""
        analyzer = ConversationFlowAnalyzer()
        
        dependency_map = analyzer.map_conversation_dependencies(conversation_chain)
        
        # Test parent-child relationships
        assert dependency_map["root"]["children"] == ["reply-1"]
        assert dependency_map["reply-1"]["children"] == ["tool-1", "branch-1"]
        assert dependency_map["tool-1"]["parent"] == "reply-1"
        assert dependency_map["user-2"]["parent"] == "reply-2"
        
        # Test orphan detection
        assert "orphan" in dependency_map["orphans"]
    
    def test_identify_conversation_branches(self, conversation_chain):
        """Test identification of conversation branches and merges"""
        analyzer = ConversationFlowAnalyzer()
        
        branches = analyzer.identify_conversation_branches(conversation_chain)
        
        # Should identify branch point at reply-1
        assert "reply-1" in branches["branch_points"]
        assert len(branches["branch_points"]["reply-1"]) == 2
        assert set(branches["branch_points"]["reply-1"]) == {"tool-1", "branch-1"}
    
    def test_map_tool_call_sequences(self, conversation_chain):
        """Test mapping of tool call sequences and their relationships"""
        analyzer = ConversationFlowAnalyzer()
        
        # Add more tool calls for testing sequences
        extended_chain = conversation_chain + [
            {"uuid": "tool-2", "parentUuid": "reply-2", "type": "tool_call", "message": {"tool": "Write"}},
            {"uuid": "tool-3", "parentUuid": "tool-2", "type": "tool_call", "message": {"tool": "Bash"}}
        ]
        
        sequences = analyzer.map_tool_call_sequences(extended_chain)
        
        # Should identify tool sequences
        assert len(sequences) >= 1
        # Should find Read -> Write -> Bash sequence
        tool_sequence = [seq for seq in sequences if "Read" in seq and "Write" in seq]
        assert len(tool_sequence) > 0
    
    def test_detect_circular_references(self):
        """Test detection of circular parentUuid references"""
        analyzer = ConversationFlowAnalyzer()
        
        circular_chain = [
            {"uuid": "a", "parentUuid": "c", "type": "user", "message": {"content": "A"}},
            {"uuid": "b", "parentUuid": "a", "type": "assistant", "message": {"content": "B"}}, 
            {"uuid": "c", "parentUuid": "b", "type": "user", "message": {"content": "C"}}
        ]
        
        circular_refs = analyzer.detect_circular_references(circular_chain)
        
        # Should detect the A -> C -> B -> A cycle
        assert len(circular_refs) > 0
        assert set(circular_refs[0]) == {"a", "b", "c"}
    
    def test_calculate_conversation_depth(self, conversation_chain):
        """Test calculation of conversation thread depth"""
        analyzer = ConversationFlowAnalyzer()
        
        depth_map = analyzer.calculate_conversation_depth(conversation_chain)
        
        # Test expected depths
        assert depth_map["root"] == 0
        assert depth_map["reply-1"] == 1
        assert depth_map["tool-1"] == 2
        assert depth_map["reply-2"] == 3
        assert depth_map["user-2"] == 4
        assert depth_map["branch-1"] == 2  # Branch from reply-1
        
        # Orphan should have depth None or special handling
        assert depth_map.get("orphan") in [None, -1]


class TestJSONLAnalyzerIntegration:
    """Integration tests combining analyzer components"""
    
    def test_full_analysis_pipeline(self):
        """Test complete analysis pipeline from file to insights"""
        analyzer = JSONLAnalyzer()
        flow_analyzer = ConversationFlowAnalyzer()
        
        # Create comprehensive test data
        test_data = [
            {"uuid": "start", "parentUuid": None, "type": "user", "message": {"content": "Help me implement a feature"}},
            {"uuid": "plan", "parentUuid": "start", "type": "assistant", "message": {"content": "I'll help you plan the implementation"}},
            {"uuid": "read-code", "parentUuid": "plan", "type": "tool_call", "message": {"tool": "Read", "result": "existing code"}},
            {"uuid": "analyze", "parentUuid": "read-code", "type": "assistant", "message": {"content": "Based on the code, here's the plan..."}},
            {"uuid": "implement", "parentUuid": "analyze", "type": "tool_call", "message": {"tool": "Write", "result": "new implementation"}},
            {"uuid": "test", "parentUuid": "implement", "type": "tool_call", "message": {"tool": "Bash", "result": "tests passed"}},
            {"uuid": "complete", "parentUuid": "test", "type": "assistant", "message": {"content": "Feature implemented successfully"}}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in test_data:
                json.dump(entry, f)
                f.write('\n')
            temp_path = Path(f.name)
        
        try:
            # Parse and analyze
            entries = analyzer.parse_jsonl_file(temp_path)
            message_types = analyzer.identify_message_types(entries)
            tool_patterns = analyzer.extract_tool_usage_patterns(entries)
            dependencies = flow_analyzer.map_conversation_dependencies(entries)
            depths = flow_analyzer.calculate_conversation_depth(entries)
            
            # Verify comprehensive analysis results
            assert len(entries) == 7
            assert message_types["user"] == 1
            assert message_types["assistant"] == 3
            assert message_types["tool_call"] == 3
            
            assert set(tool_patterns["tools_used"].keys()) == {"Read", "Write", "Bash"}
            assert tool_patterns["tool_sequences"][0] == ["Read", "Write", "Bash"]
            
            assert max(depths.values()) == 6  # Deepest conversation thread
            assert dependencies["start"]["children"] == ["plan"]
            
        finally:
            temp_path.unlink()
    
    def test_performance_large_file(self):
        """Test performance requirements: <1 second for 1000-line JSONL file"""
        import time
        
        analyzer = JSONLAnalyzer()
        
        # Generate 1000 entries
        large_data = []
        for i in range(1000):
            entry = {
                "uuid": f"msg-{i:04d}",
                "parentUuid": f"msg-{i-1:04d}" if i > 0 else None,
                "type": "user" if i % 2 == 0 else "assistant",
                "message": {"content": f"Message content {i}"},
                "timestamp": f"2025-08-01T19:51:{(21 + i) % 60:02d}.024033"
            }
            large_data.append(entry)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in large_data:
                json.dump(entry, f)
                f.write('\n')
            temp_path = Path(f.name)
        
        try:
            # Measure parsing performance
            start_time = time.time()
            entries = analyzer.parse_jsonl_file(temp_path)
            parse_time = time.time() - start_time
            
            # Should complete in less than 1 second
            assert parse_time < 1.0, f"Parsing took {parse_time:.2f} seconds, expected < 1.0"
            assert len(entries) == 1000
            
        finally:
            temp_path.unlink()
    
    def test_memory_usage_large_file(self):
        """Test memory usage requirements: <50MB for largest sample files"""
        import tracemalloc
        
        analyzer = JSONLAnalyzer()
        
        # Generate large dataset (simulating real conversation)
        large_data = []
        for i in range(5000):  # Larger dataset for memory testing
            content = f"This is message {i} with substantial content. " * 10  # ~500 chars each
            entry = {
                "uuid": f"msg-{i:05d}",
                "parentUuid": f"msg-{i-1:05d}" if i > 0 else None,
                "type": "tool_call" if i % 10 == 0 else ("user" if i % 2 == 0 else "assistant"),
                "message": {
                    "content": content,
                    "tool": "Read" if i % 10 == 0 else None,
                    "result": f"Tool result {i}" * 20 if i % 10 == 0 else None
                },
                "timestamp": f"2025-08-01T{(19 + i // 3600) % 24:02d}:{(51 + (i // 60) % 60) % 60:02d}:{(21 + i) % 60:02d}.024033"
            }
            large_data.append(entry)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in large_data:
                json.dump(entry, f)
                f.write('\n')
            temp_path = Path(f.name)
        
        try:
            # Measure memory usage
            tracemalloc.start()
            entries = analyzer.parse_jsonl_file(temp_path)
            
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # Convert to MB
            peak_mb = peak / 1024 / 1024
            
            # Should use less than 50MB
            assert peak_mb < 50, f"Memory usage was {peak_mb:.2f} MB, expected < 50 MB"
            assert len(entries) == 5000
            
        finally:
            temp_path.unlink()


# Test data factories for reuse across test modules
@pytest.fixture
def make_jsonl_entry():
    """Factory fixture for creating test JSONL entries"""
    def _make_entry(
        uuid=None,
        parent_uuid=None, 
        message_type="user",
        content="test content",
        tool=None,
        result=None,
        timestamp=None
    ):
        entry = {
            "uuid": uuid or f"test-{id(object())}",
            "type": message_type,
            "parentUuid": parent_uuid,
            "message": {"content": content},
            "timestamp": timestamp or "2025-08-01T19:51:21.024033"
        }
        
        if tool:
            entry["message"]["tool"] = tool
            entry["message"]["result"] = result or f"Result for {tool}"
            entry["type"] = "tool_call"
            
        return entry
    
    return _make_entry


@pytest.fixture  
def make_conversation_chain():
    """Factory fixture for creating conversation chains"""
    def _make_chain(length=5, branching=False):
        chain = []
        
        # Root message
        chain.append({
            "uuid": "root",
            "parentUuid": None,
            "type": "user", 
            "message": {"content": "Start conversation"},
            "timestamp": "2025-08-01T19:51:21.024033"
        })
        
        # Sequential messages
        for i in range(1, length):
            chain.append({
                "uuid": f"msg-{i}",
                "parentUuid": chain[i-1]["uuid"],
                "type": "assistant" if i % 2 == 1 else "user",
                "message": {"content": f"Message {i}"},
                "timestamp": f"2025-08-01T19:51:{(21 + i) % 60:02d}.024033"
            })
        
        # Add branch if requested
        if branching and length > 2:
            chain.append({
                "uuid": "branch",
                "parentUuid": "msg-1",  # Branch from second message
                "type": "assistant",
                "message": {"content": "Branched response"},
                "timestamp": "2025-08-01T19:52:00.024033"
            })
        
        return chain
    
    return _make_chain