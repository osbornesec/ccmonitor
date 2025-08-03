#!/usr/bin/env python3
"""
Comprehensive tests for conversation integrity validation.

This test suite ensures that the critical issue of orphaned parent references
is properly handled by the dependency tracking system.
"""

import unittest
import tempfile
import json
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from conversation_dependency_tracker import ConversationDependencyGraph


class TestConversationIntegrity(unittest.TestCase):
    """Test cases for conversation integrity validation."""
    
    def setUp(self):
        """Set up test environment."""
        self.graph = ConversationDependencyGraph()
        
    def create_test_conversation(self, scenario="basic"):
        """Create test conversations for different scenarios."""
        
        scenarios = {
            "basic": [
                {"uuid": "msg-001", "type": "user", "message": {"content": "Start"}, "timestamp": "2025-01-01T10:00:00Z"},
                {"uuid": "msg-002", "type": "assistant", "message": {"content": "Response"}, "timestamp": "2025-01-01T10:01:00Z", "parentUuid": "msg-001"},
                {"uuid": "msg-003", "type": "user", "message": {"content": "Follow-up"}, "timestamp": "2025-08-03T10:00:00Z", "parentUuid": "msg-002"}
            ],
            
            "complex_chain": [
                {"uuid": "root-1", "type": "user", "message": {"content": "Question A"}, "timestamp": "2025-01-01T10:00:00Z"},
                {"uuid": "resp-1", "type": "assistant", "message": {"content": "Answer A"}, "timestamp": "2025-01-01T10:01:00Z", "parentUuid": "root-1"},
                {"uuid": "follow-1", "type": "user", "message": {"content": "Follow A"}, "timestamp": "2025-01-01T10:02:00Z", "parentUuid": "resp-1"},
                {"uuid": "resp-2", "type": "assistant", "message": {"content": "Answer B"}, "timestamp": "2025-01-01T10:03:00Z", "parentUuid": "follow-1"},
                {"uuid": "recent", "type": "user", "message": {"content": "Recent message"}, "timestamp": "2025-08-03T10:00:00Z", "parentUuid": "resp-2"},
                {"uuid": "isolated", "type": "system", "message": {"content": "Isolated"}, "timestamp": "2025-01-01T10:05:00Z"}
            ],
            
            "multiple_roots": [
                {"uuid": "root-1", "type": "user", "message": {"content": "Chain 1 start"}, "timestamp": "2025-01-01T10:00:00Z"},
                {"uuid": "child-1", "type": "assistant", "message": {"content": "Chain 1 response"}, "timestamp": "2025-01-01T10:01:00Z", "parentUuid": "root-1"},
                {"uuid": "root-2", "type": "user", "message": {"content": "Chain 2 start"}, "timestamp": "2025-01-01T10:02:00Z"},
                {"uuid": "child-2", "type": "assistant", "message": {"content": "Chain 2 response"}, "timestamp": "2025-08-03T10:00:00Z", "parentUuid": "root-2"},
                {"uuid": "orphan", "type": "system", "message": {"content": "No dependencies"}, "timestamp": "2025-01-01T10:05:00Z"}
            ]
        }
        
        return scenarios.get(scenario, scenarios["basic"])
    
    def write_test_file(self, messages):
        """Write messages to a temporary JSONL file."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False)
        for message in messages:
            temp_file.write(json.dumps(message) + '\n')
        temp_file.close()
        return Path(temp_file.name)
    
    def test_basic_orphaned_reference_detection(self):
        """Test detection of basic orphaned parent references."""
        messages = self.create_test_conversation("basic")
        temp_file = self.write_test_file(messages)
        
        try:
            # Load conversation
            success = self.graph.load_from_jsonl(temp_file)
            self.assertTrue(success, "Should successfully load conversation")
            
            # Simulate naive age-based deletion (keeping only recent message)
            remaining_messages = {"msg-003"}  # Only recent message
            
            # Validate integrity
            is_valid, issues = self.graph.validate_conversation_integrity(remaining_messages)
            
            # Should detect the orphaned reference
            self.assertFalse(is_valid, "Should detect orphaned reference")
            self.assertEqual(len(issues), 1, "Should find exactly one integrity issue")
            self.assertIn("msg-003", issues[0], "Issue should mention the orphaned child")
            self.assertIn("msg-002", issues[0], "Issue should mention the missing parent")
            
        finally:
            temp_file.unlink()
    
    def test_orphaned_reference_fixing(self):
        """Test automatic fixing of orphaned references."""
        messages = self.create_test_conversation("basic")
        temp_file = self.write_test_file(messages)
        
        try:
            # Load conversation
            success = self.graph.load_from_jsonl(temp_file)
            self.assertTrue(success, "Should successfully load conversation")
            
            # Test the fix mechanism
            remaining_messages = {"msg-003"}  # Only recent message
            required_parents = self.graph.get_messages_requiring_parents(remaining_messages)
            
            # Should require both parent and grandparent
            expected_parents = {"msg-001", "msg-002"}
            self.assertEqual(required_parents, expected_parents, "Should require complete parent chain")
            
            # Validate that including required parents fixes the issue
            fixed_remaining = remaining_messages | required_parents
            is_valid, issues = self.graph.validate_conversation_integrity(fixed_remaining)
            
            self.assertTrue(is_valid, "Should be valid after including required parents")
            self.assertEqual(len(issues), 0, "Should have no integrity issues after fix")
            
        finally:
            temp_file.unlink()
    
    def test_complex_conversation_chain_integrity(self):
        """Test integrity validation on complex conversation chains."""
        messages = self.create_test_conversation("complex_chain")
        temp_file = self.write_test_file(messages)
        
        try:
            # Load conversation
            success = self.graph.load_from_jsonl(temp_file)
            self.assertTrue(success, "Should successfully load conversation")
            
            # Test keeping only the recent message (should require full chain)
            remaining_messages = {"recent"}
            required_parents = self.graph.get_messages_requiring_parents(remaining_messages)
            
            # Should require the entire conversation chain
            expected_parents = {"root-1", "resp-1", "follow-1", "resp-2"}
            self.assertEqual(required_parents, expected_parents, "Should require entire conversation chain")
            
            # Test that isolated message can be safely removed
            all_messages = set(msg["uuid"] for msg in messages)
            remaining_with_parents = remaining_messages | required_parents
            
            # Should be able to delete isolated message
            can_delete = all_messages - remaining_with_parents
            self.assertIn("isolated", can_delete, "Should be able to delete isolated message")
            
            # Validate final integrity
            is_valid, issues = self.graph.validate_conversation_integrity(remaining_with_parents)
            self.assertTrue(is_valid, "Should be valid with complete conversation chain")
            
        finally:
            temp_file.unlink()
    
    def test_multiple_conversation_roots(self):
        """Test integrity with multiple independent conversation chains."""
        messages = self.create_test_conversation("multiple_roots")
        temp_file = self.write_test_file(messages)
        
        try:
            # Load conversation
            success = self.graph.load_from_jsonl(temp_file)
            self.assertTrue(success, "Should successfully load conversation")
            
            # Test keeping only one recent message from chain 2
            remaining_messages = {"child-2"}
            required_parents = self.graph.get_messages_requiring_parents(remaining_messages)
            
            # Should only require parent from same chain
            expected_parents = {"root-2"}
            self.assertEqual(required_parents, expected_parents, "Should only require parent from same chain")
            
            # Should be able to delete entire chain 1 and orphan
            all_messages = set(msg["uuid"] for msg in messages)
            remaining_with_parents = remaining_messages | required_parents
            can_delete = all_messages - remaining_with_parents
            
            expected_deletable = {"root-1", "child-1", "orphan"}
            self.assertEqual(can_delete, expected_deletable, "Should be able to delete independent chains")
            
            # Validate final integrity
            is_valid, issues = self.graph.validate_conversation_integrity(remaining_with_parents)
            self.assertTrue(is_valid, "Should be valid with only one complete chain")
            
        finally:
            temp_file.unlink()
    
    def test_dependency_aware_deletion_prevents_orphans(self):
        """Test that dependency-aware deletion automatically prevents orphans."""
        messages = self.create_test_conversation("basic")
        temp_file = self.write_test_file(messages)
        
        try:
            # Load conversation
            success = self.graph.load_from_jsonl(temp_file)
            self.assertTrue(success, "Should successfully load conversation")
            
            # Simulate age-based deletion candidates
            old_messages = {"msg-001", "msg-002"}  # msg-003 is recent
            
            # Apply dependency tracking
            self.graph.mark_for_deletion(old_messages)
            safe_deletions = self.graph.get_safe_deletion_set()
            
            # Should not be able to delete any messages due to dependencies
            self.assertEqual(len(safe_deletions), 0, "Should not delete any messages with dependencies")
            
            # Calculate what would remain
            all_messages = set(msg["uuid"] for msg in messages)
            remaining_messages = all_messages - safe_deletions
            
            # Validate that the result has perfect integrity
            is_valid, issues = self.graph.validate_conversation_integrity(remaining_messages)
            self.assertTrue(is_valid, "Dependency-aware deletion should maintain perfect integrity")
            self.assertEqual(len(issues), 0, "Should have zero integrity violations")
            
        finally:
            temp_file.unlink()
    
    def test_edge_case_missing_parent_references(self):
        """Test handling of messages that reference non-existent parents."""
        # Create conversation with broken reference
        messages = [
            {"uuid": "msg-001", "type": "user", "message": {"content": "Valid message"}, "timestamp": "2025-08-03T10:00:00Z"},
            {"uuid": "msg-002", "type": "assistant", "message": {"content": "Broken reference"}, "timestamp": "2025-08-03T10:01:00Z", "parentUuid": "missing-parent"}
        ]
        
        temp_file = self.write_test_file(messages)
        
        try:
            # Load conversation (should handle broken references gracefully)
            success = self.graph.load_from_jsonl(temp_file)
            self.assertTrue(success, "Should load even with broken references")
            
            # Test integrity validation with broken reference
            remaining_messages = {"msg-001", "msg-002"}
            is_valid, issues = self.graph.validate_conversation_integrity(remaining_messages)
            
            # Should detect the broken reference
            self.assertFalse(is_valid, "Should detect broken parent reference")
            self.assertTrue(any("missing-parent" in issue for issue in issues), "Should mention missing parent")
            
        finally:
            temp_file.unlink()
    
    def test_performance_with_large_conversation(self):
        """Test integrity validation performance with larger conversations."""
        # Create a larger conversation chain
        messages = []
        for i in range(100):
            if i == 0:
                messages.append({
                    "uuid": f"msg-{i:03d}",
                    "type": "user",
                    "message": {"content": f"Message {i}"},
                    "timestamp": "2025-01-01T10:00:00Z"
                })
            else:
                messages.append({
                    "uuid": f"msg-{i:03d}",
                    "type": "assistant" if i % 2 == 1 else "user",
                    "message": {"content": f"Message {i}"},
                    "timestamp": "2025-01-01T10:00:00Z" if i < 90 else "2025-08-03T10:00:00Z",
                    "parentUuid": f"msg-{i-1:03d}"
                })
        
        temp_file = self.write_test_file(messages)
        
        try:
            # Load and validate (should complete in reasonable time)
            import time
            start_time = time.time()
            
            success = self.graph.load_from_jsonl(temp_file)
            self.assertTrue(success, "Should load large conversation")
            
            # Test integrity validation
            remaining_messages = {f"msg-{i:03d}" for i in range(90, 100)}  # Keep last 10
            required_parents = self.graph.get_messages_requiring_parents(remaining_messages)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Should complete in under 1 second
            self.assertLess(processing_time, 1.0, "Should process large conversation quickly")
            
            # Should require entire chain
            self.assertEqual(len(required_parents), 90, "Should require all 90 parent messages")
            
        finally:
            temp_file.unlink()


def run_tests():
    """Run all conversation integrity tests."""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_tests()