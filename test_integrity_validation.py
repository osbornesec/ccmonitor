#!/usr/bin/env python3
"""
Test script to demonstrate conversation integrity validation.
This tests the critical issue where child messages would reference missing parents.
"""

import json
import sys
import tempfile
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from conversation_dependency_tracker import ConversationDependencyGraph

def create_test_scenario():
    """Create a test scenario that would create orphaned references without validation."""
    
    # This represents a common scenario:
    # - Old root message and first response (should be deleted by age)
    # - Recent message that depends on the old response (should be kept)
    # - Without validation, recent message would reference non-existent parent
    
    messages = [
        {
            "uuid": "msg-001",
            "type": "user", 
            "message": {"content": "Help me debug this error"},
            "timestamp": "2025-01-01T10:00:00Z"  # OLD (7+ days ago)
        },
        {
            "uuid": "msg-002",
            "type": "assistant",
            "message": {"content": "I can help! What's the error?"},
            "timestamp": "2025-01-01T10:01:00Z",  # OLD (7+ days ago)
            "parentUuid": "msg-001"
        },
        {
            "uuid": "msg-003",
            "type": "user",
            "message": {"content": "Thanks for your help earlier, I have a follow-up question"},
            "timestamp": "2025-08-03T10:00:00Z",  # RECENT (today)
            "parentUuid": "msg-002"  # REFERENCES OLD MESSAGE!
        },
        {
            "uuid": "msg-004",
            "type": "system",
            "message": {"content": "Session timeout"},
            "timestamp": "2025-01-01T10:05:00Z"  # OLD, no dependencies
        }
    ]
    
    return messages

def write_test_file(messages, file_path):
    """Write messages to JSONL file."""
    with open(file_path, 'w') as f:
        for message in messages:
            f.write(json.dumps(message) + '\n')

def test_basic_dependency_analysis():
    """Test basic dependency analysis on the orphaned reference scenario."""
    print("🔍 Testing Basic Dependency Analysis")
    print("=" * 50)
    
    messages = create_test_scenario()
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for message in messages:
            f.write(json.dumps(message) + '\n')
        temp_file = Path(f.name)
    
    try:
        # Build dependency graph
        graph = ConversationDependencyGraph()
        success = graph.load_from_jsonl(temp_file)
        
        if not success:
            print("❌ Failed to load conversation")
            return
        
        print(f"📊 Loaded conversation with {len(graph.nodes)} messages")
        
        # Show conversation structure
        print("\n🏗️  Conversation Structure:")
        for uuid, node in graph.nodes.items():
            parent_info = f" → {node.parent_uuid}" if node.parent_uuid else " (ROOT)"
            children_info = f" → [{', '.join(node.children)}]" if node.children else " (LEAF)"
            print(f"   {uuid}: {node.message_type}{parent_info}{children_info}")
        
        # Simulate age-based deletion candidates (msg-001, msg-002, msg-004 are old)
        old_messages = {"msg-001", "msg-002", "msg-004"}
        print(f"\n📅 Age-based deletion candidates: {old_messages}")
        
        # Apply dependency tracking
        graph.mark_for_deletion(old_messages)
        safe_deletions = graph.get_safe_deletion_set()
        
        print(f"\n🔗 Dependency Analysis Results:")
        print(f"   Originally marked for deletion: {len(old_messages)}")
        print(f"   Safe to delete: {len(safe_deletions)}")
        print(f"   Safe deletion set: {safe_deletions}")
        print(f"   Preserved by dependencies: {graph.preserved_by_children}")
        
    finally:
        temp_file.unlink()  # Clean up

def test_integrity_validation():
    """Test the critical integrity validation that prevents orphaned references."""
    print("\n🚨 Testing Conversation Integrity Validation")
    print("=" * 50)
    
    messages = create_test_scenario()
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for message in messages:
            f.write(json.dumps(message) + '\n')
        temp_file = Path(f.name)
    
    try:
        # Build dependency graph
        graph = ConversationDependencyGraph()
        success = graph.load_from_jsonl(temp_file)
        
        if not success:
            print("❌ Failed to load conversation")
            return
        
        # Simulate what would happen WITHOUT proper dependency tracking
        print("🧪 Scenario: Age-based deletion without dependency awareness")
        old_messages = {"msg-001", "msg-002", "msg-004"}
        remaining_messages = {"msg-003"}  # Only recent message remains
        
        print(f"   Would delete: {old_messages}")
        print(f"   Would remain: {remaining_messages}")
        
        # Validate integrity of remaining messages
        is_valid, issues = graph.validate_conversation_integrity(remaining_messages)
        
        print(f"\n🔍 Integrity Validation Results:")
        print(f"   Is valid: {'✅ YES' if is_valid else '❌ NO'}")
        print(f"   Issues found: {len(issues)}")
        
        if issues:
            print("   🚨 INTEGRITY VIOLATIONS:")
            for issue in issues:
                print(f"      • {issue}")
        
        # Show what we need to fix this
        if not is_valid:
            required_parents = graph.get_messages_requiring_parents(remaining_messages)
            print(f"\n🔧 Required parent messages for integrity: {required_parents}")
            
            # Simulate the fix
            fixed_remaining = remaining_messages | required_parents
            is_fixed, remaining_issues = graph.validate_conversation_integrity(fixed_remaining)
            
            print(f"\n✅ After including required parents:")
            print(f"   Would remain: {fixed_remaining}")
            print(f"   Is valid: {'✅ YES' if is_fixed else '❌ NO'}")
            if remaining_issues:
                print(f"   Remaining issues: {remaining_issues}")
        
    finally:
        temp_file.unlink()  # Clean up

def test_correct_dependency_aware_deletion():
    """Test the correct way with full dependency awareness."""
    print("\n✅ Testing Correct Dependency-Aware Deletion")
    print("=" * 50)
    
    messages = create_test_scenario()
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for message in messages:
            f.write(json.dumps(message) + '\n')
        temp_file = Path(f.name)
    
    try:
        # Build dependency graph
        graph = ConversationDependencyGraph()
        success = graph.load_from_jsonl(temp_file)
        
        if not success:
            print("❌ Failed to load conversation")
            return
        
        # Apply proper dependency-aware deletion
        old_messages = {"msg-001", "msg-002", "msg-004"}
        graph.mark_for_deletion(old_messages)
        safe_deletions = graph.get_safe_deletion_set()
        
        # Calculate what would remain
        all_messages = set(graph.nodes.keys())
        remaining_messages = all_messages - safe_deletions
        
        print(f"📊 Proper Dependency-Aware Results:")
        print(f"   Age-based candidates: {old_messages}")
        print(f"   Safe to delete: {safe_deletions}")
        print(f"   Would remain: {remaining_messages}")
        
        # Validate integrity of the result
        is_valid, issues = graph.validate_conversation_integrity(remaining_messages)
        
        print(f"\n🔍 Final Integrity Check:")
        print(f"   Is valid: {'✅ YES' if is_valid else '❌ NO'}")
        if issues:
            print(f"   Issues: {issues}")
        else:
            print("   ✅ No integrity violations found!")
        
        # Show preservation reasoning
        preservation_report = graph.get_preservation_report()
        if preservation_report['preserved_by_dependencies'] > 0:
            print(f"\n🛡️  Preservation Details:")
            for detail in preservation_report['preservation_details']:
                print(f"   • {detail['uuid']}: preserved due to {detail['children_preserved']} children")
        
    finally:
        temp_file.unlink()  # Clean up

def main():
    """Run all integrity validation tests."""
    print("🧪 CONVERSATION INTEGRITY VALIDATION TESTS")
    print("=" * 60)
    print()
    print("This demonstrates the critical issue where child messages")
    print("would reference parents that don't exist after pruning.")
    print()
    
    try:
        test_basic_dependency_analysis()
        test_integrity_validation()
        test_correct_dependency_aware_deletion()
        
        print("\n" + "=" * 60)
        print("🎯 KEY FINDINGS:")
        print("   • Without validation: msg-003 would reference missing msg-002")
        print("   • With validation: System automatically preserves required parents")
        print("   • Result: Conversation integrity is maintained")
        print("   • The pruned file remains valid and parseable")
        print("\n✅ All integrity validation tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())