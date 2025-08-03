#!/usr/bin/env python3
"""
Conversation Dependency Tracker

Handles parent-child relationships in JSONL conversation files to ensure
proper message dependency preservation during pruning operations.

Key principle: Parent nodes must be preserved until ALL child nodes are deleted.
This maintains conversation flow integrity and prevents orphaned responses.
"""

import json
import logging
from typing import Dict, List, Set, Optional, Any, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MessageNode:
    """Represents a message in the conversation dependency graph."""
    uuid: str
    parent_uuid: Optional[str]
    message_type: str
    timestamp: str
    content: str
    importance_score: float = 0.0
    children: Set[str] = None
    is_marked_for_deletion: bool = False
    deletion_blocked_by_children: bool = False
    
    def __post_init__(self):
        if self.children is None:
            self.children = set()

class ConversationDependencyGraph:
    """
    Builds and manages dependency relationships between conversation messages.
    Ensures parent-child integrity during pruning operations.
    """
    
    def __init__(self):
        self.nodes: Dict[str, MessageNode] = {}
        self.root_nodes: Set[str] = set()  # Messages with no parent
        self.deletion_candidates: Set[str] = set()
        self.preserved_by_children: Set[str] = set()
        
    def load_from_jsonl(self, file_path: Path) -> bool:
        """
        Load conversation messages from JSONL file and build dependency graph.
        
        Args:
            file_path: Path to JSONL conversation file
            
        Returns:
            bool: True if successful, False if errors occurred
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                        
                    try:
                        message_data = json.loads(line)
                        self._add_message_to_graph(message_data)
                    except json.JSONDecodeError as e:
                        logger.warning(f"   ⚠️  Skipping malformed JSON on line {line_num}: {e}")
                        continue
            
            self._build_parent_child_relationships()
            logger.info(f"📊 Dependency graph built: {len(self.nodes)} messages, {len(self.root_nodes)} root nodes")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load conversation: {e}")
            return False
    
    def _add_message_to_graph(self, message_data: Dict[str, Any]) -> None:
        """Add a message to the dependency graph."""
        uuid = message_data.get('uuid', '')
        parent_uuid = message_data.get('parentUuid')
        message_type = message_data.get('type', 'unknown')
        timestamp = message_data.get('timestamp', '')
        
        # Extract content from nested message structure
        content = ''
        if 'message' in message_data and isinstance(message_data['message'], dict):
            content = message_data['message'].get('content', '')
        elif 'content' in message_data:
            content = message_data['content']
        
        # Create message node
        node = MessageNode(
            uuid=uuid,
            parent_uuid=parent_uuid,
            message_type=message_type,
            timestamp=timestamp,
            content=content
        )
        
        self.nodes[uuid] = node
        
        # Track root nodes (messages with no parent)
        if not parent_uuid:
            self.root_nodes.add(uuid)
    
    def _build_parent_child_relationships(self) -> None:
        """Build bidirectional parent-child relationships."""
        for node in self.nodes.values():
            if node.parent_uuid and node.parent_uuid in self.nodes:
                # Add this node as a child of its parent
                parent_node = self.nodes[node.parent_uuid]
                parent_node.children.add(node.uuid)
    
    def mark_for_deletion(self, message_uuids: Set[str]) -> None:
        """
        Mark messages for deletion, but block deletion if they have children.
        
        Args:
            message_uuids: Set of message UUIDs to mark for deletion
        """
        self.deletion_candidates = message_uuids.copy()
        
        for uuid in message_uuids:
            if uuid in self.nodes:
                self.nodes[uuid].is_marked_for_deletion = True
        
        # Check for parent-child conflicts
        self._resolve_parent_child_conflicts()
    
    def _resolve_parent_child_conflicts(self) -> None:
        """
        Resolve conflicts where parents are marked for deletion but have children
        that are NOT marked for deletion.
        
        Rule: Parents must be preserved until ALL children are deleted.
        This includes preserving the ENTIRE ancestral chain back to root nodes.
        """
        self.preserved_by_children.clear()
        
        # First pass: identify direct parent-child conflicts
        nodes_to_preserve = set()
        
        for uuid in self.deletion_candidates.copy():
            if uuid not in self.nodes:
                continue
                
            node = self.nodes[uuid]
            
            # Check if this node has any children that are NOT marked for deletion
            children_to_preserve = node.children - self.deletion_candidates
            
            if children_to_preserve:
                # This parent must be preserved because it has children staying
                nodes_to_preserve.add(uuid)
                logger.info(f"   🛡️  Preserving parent {uuid} (has {len(children_to_preserve)} children to preserve)")
        
        # Second pass: recursively preserve all ancestors of preserved nodes
        ancestors_to_preserve = set()
        
        def preserve_ancestors(node_uuid: str):
            """Recursively preserve all ancestors of a node."""
            if node_uuid in self.nodes:
                node = self.nodes[node_uuid]
                if node.parent_uuid and node.parent_uuid in self.deletion_candidates:
                    ancestors_to_preserve.add(node.parent_uuid)
                    logger.info(f"   🔗 Preserving ancestor {node.parent_uuid} (descendant {node_uuid} must stay)")
                    preserve_ancestors(node.parent_uuid)  # Recursive preservation
        
        # Preserve ancestors for all nodes that must be preserved
        for uuid in nodes_to_preserve:
            preserve_ancestors(uuid)
        
        # Also preserve ancestors for any messages that were NOT marked for deletion
        # (recent messages that need their conversation history preserved)
        for uuid, node in self.nodes.items():
            if uuid not in self.deletion_candidates:  # This is a recent/preserved message
                preserve_ancestors(uuid)
        
        # Combine direct preservations and ancestor preservations
        all_preserved = nodes_to_preserve | ancestors_to_preserve
        
        # Update tracking sets and node states
        for uuid in all_preserved:
            if uuid in self.nodes:
                self.nodes[uuid].deletion_blocked_by_children = True
                self.preserved_by_children.add(uuid)
                self.deletion_candidates.discard(uuid)
    
    def get_safe_deletion_set(self) -> Set[str]:
        """
        Get the set of messages that can be safely deleted without breaking
        parent-child relationships.
        
        Returns:
            Set[str]: UUIDs of messages safe to delete
        """
        return self.deletion_candidates - self.preserved_by_children
    
    def get_preservation_report(self) -> Dict[str, Any]:
        """
        Generate a detailed report of preservation decisions.
        
        Returns:
            Dict containing preservation statistics and details
        """
        total_messages = len(self.nodes)
        originally_marked = len(self.deletion_candidates) + len(self.preserved_by_children)
        actually_deletable = len(self.deletion_candidates)
        preserved_by_dependencies = len(self.preserved_by_children)
        
        # Analyze preservation reasons
        preservation_details = []
        for uuid in self.preserved_by_children:
            if uuid in self.nodes:
                node = self.nodes[uuid]
                children_preserved = node.children - self.deletion_candidates
                preservation_details.append({
                    'uuid': uuid,
                    'message_type': node.message_type,
                    'children_count': len(node.children),
                    'children_preserved': len(children_preserved),
                    'children_preserved_uuids': list(children_preserved)
                })
        
        return {
            'total_messages': total_messages,
            'originally_marked_for_deletion': originally_marked,
            'actually_deletable': actually_deletable,
            'preserved_by_dependencies': preserved_by_dependencies,
            'preservation_rate': preserved_by_dependencies / originally_marked if originally_marked > 0 else 0.0,
            'deletion_efficiency': actually_deletable / originally_marked if originally_marked > 0 else 0.0,
            'preservation_details': preservation_details
        }
    
    def get_conversation_chains(self) -> List[List[str]]:
        """
        Get all conversation chains (root to leaf paths) in the dependency graph.
        
        Returns:
            List of conversation chains, each chain is a list of message UUIDs
        """
        chains = []
        
        def build_chain(node_uuid: str, current_chain: List[str]) -> None:
            """Recursively build conversation chains."""
            current_chain.append(node_uuid)
            
            if node_uuid in self.nodes:
                node = self.nodes[node_uuid]
                
                if not node.children:
                    # Leaf node - end of chain
                    chains.append(current_chain.copy())
                else:
                    # Continue chain with each child
                    for child_uuid in node.children:
                        build_chain(child_uuid, current_chain)
            
            current_chain.pop()
        
        # Start chains from root nodes
        for root_uuid in self.root_nodes:
            build_chain(root_uuid, [])
        
        return chains
    
    def validate_deletion_safety(self, proposed_deletions: Set[str]) -> Tuple[bool, List[str]]:
        """
        Validate that a proposed deletion set won't break conversation integrity.
        
        Args:
            proposed_deletions: Set of message UUIDs proposed for deletion
            
        Returns:
            Tuple of (is_safe, list_of_issues)
        """
        issues = []
        
        for uuid in proposed_deletions:
            if uuid not in self.nodes:
                issues.append(f"Message {uuid} not found in conversation")
                continue
            
            node = self.nodes[uuid]
            
            # Check if this message has children that would be orphaned
            children_remaining = node.children - proposed_deletions
            if children_remaining:
                issues.append(
                    f"Message {uuid} has {len(children_remaining)} children that would be orphaned: "
                    f"{list(children_remaining)}"
                )
        
        return len(issues) == 0, issues
    
    def validate_conversation_integrity(self, remaining_messages: Set[str]) -> Tuple[bool, List[str]]:
        """
        Validate that remaining messages don't have orphaned parent references.
        
        This checks for the critical issue where a child message references a parent
        that would not exist in the pruned file, making the child invalid.
        
        Args:
            remaining_messages: Set of message UUIDs that will remain after deletion
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        orphaned_references = []
        
        for uuid in remaining_messages:
            if uuid not in self.nodes:
                issues.append(f"Message {uuid} not found in conversation graph")
                continue
            
            node = self.nodes[uuid]
            
            # Check if this message references a parent that won't exist
            if node.parent_uuid and node.parent_uuid not in remaining_messages:
                orphaned_references.append({
                    'child_uuid': uuid,
                    'missing_parent_uuid': node.parent_uuid,
                    'child_type': node.message_type,
                    'child_content_preview': node.content[:100] + "..." if len(node.content) > 100 else node.content
                })
                issues.append(
                    f"Message {uuid} references parent {node.parent_uuid} which will not exist in pruned file"
                )
        
        if orphaned_references:
            logger.warning(f"🚨 Found {len(orphaned_references)} orphaned parent references that would break conversation integrity!")
            for ref in orphaned_references:
                logger.warning(f"   • {ref['child_uuid']} → {ref['missing_parent_uuid']} (MISSING)")
        
        return len(issues) == 0, issues
    
    def detect_orphaned_children(self, remaining_messages: Set[str]) -> Set[str]:
        """
        Detect messages that would become orphaned children after deletion.
        
        Orphaned children are messages that reference parents which have been deleted,
        making them invalid and should be removed as well.
        
        Args:
            remaining_messages: Set of message UUIDs that will remain after deletion
            
        Returns:
            Set of message UUIDs that are orphaned children and should be removed
        """
        orphaned_children = set()
        
        for uuid in remaining_messages:
            if uuid not in self.nodes:
                continue
            
            node = self.nodes[uuid]
            
            # Check if this message has a parent reference
            if node.parent_uuid:
                # Check if the parent would not exist in remaining messages
                if node.parent_uuid not in remaining_messages:
                    orphaned_children.add(uuid)
                    logger.info(f"🧹 Detected orphaned child: {uuid} → {node.parent_uuid} (parent missing)")
        
        return orphaned_children
    
    def cleanup_orphaned_children(self, remaining_messages: Set[str]) -> Tuple[Set[str], List[str]]:
        """
        Remove orphaned children from remaining messages to ensure conversation integrity.
        
        This iteratively removes messages that reference deleted parents until
        no orphaned references remain.
        
        Args:
            remaining_messages: Set of message UUIDs that will remain after deletion
            
        Returns:
            Tuple of (cleaned_remaining_messages, list_of_removed_orphans)
        """
        cleaned_messages = remaining_messages.copy()
        removed_orphans = []
        iteration = 0
        max_iterations = len(self.nodes)  # Safety limit
        
        while iteration < max_iterations:
            orphaned_children = self.detect_orphaned_children(cleaned_messages)
            
            if not orphaned_children:
                break  # No more orphans found
            
            logger.info(f"🧹 Cleanup iteration {iteration + 1}: Found {len(orphaned_children)} orphaned children")
            
            # Remove orphaned children
            for orphan_uuid in orphaned_children:
                cleaned_messages.discard(orphan_uuid)
                removed_orphans.append(orphan_uuid)
                
                if orphan_uuid in self.nodes:
                    node = self.nodes[orphan_uuid]
                    logger.info(f"   🗑️  Removing orphan: {orphan_uuid} (referenced missing parent {node.parent_uuid})")
            
            iteration += 1
        
        if iteration >= max_iterations:
            logger.warning(f"⚠️  Orphan cleanup reached maximum iterations ({max_iterations}), may have circular references")
        
        logger.info(f"🧹 Orphan cleanup complete: Removed {len(removed_orphans)} orphaned children in {iteration} iterations")
        
        return cleaned_messages, removed_orphans
    
    def get_messages_requiring_parents(self, target_messages: Set[str]) -> Set[str]:
        """
        Get all parent messages that must be preserved to avoid orphaned references.
        
        Args:
            target_messages: Set of messages we want to keep
            
        Returns:
            Set of additional parent UUIDs that must be preserved for integrity
        """
        required_parents = set()
        
        def preserve_parent_chain(uuid: str):
            """Recursively preserve entire parent chain."""
            if uuid in self.nodes:
                node = self.nodes[uuid]
                if node.parent_uuid:
                    required_parents.add(node.parent_uuid)
                    preserve_parent_chain(node.parent_uuid)  # Recursive up the chain
        
        # For each target message, ensure its entire parent chain exists
        for uuid in target_messages:
            preserve_parent_chain(uuid)
        
        logger.info(f"🔗 Found {len(required_parents)} parent messages required for conversation integrity")
        
        return required_parents
    
    def get_orphan_prevention_set(self, deletion_candidates: Set[str]) -> Set[str]:
        """
        Calculate which additional messages must be preserved to prevent orphans.
        
        Args:
            deletion_candidates: Original set of messages marked for deletion
            
        Returns:
            Set of message UUIDs that must be preserved to prevent orphans
        """
        must_preserve = set()
        
        # Use iterative approach to handle multi-level dependencies
        current_deletions = deletion_candidates.copy()
        
        while True:
            new_preservations = set()
            
            for uuid in current_deletions.copy():
                if uuid not in self.nodes:
                    continue
                
                node = self.nodes[uuid]
                children_remaining = node.children - current_deletions
                
                if children_remaining:
                    # This parent must be preserved
                    new_preservations.add(uuid)
                    current_deletions.discard(uuid)
            
            if not new_preservations:
                break  # No new preservations needed
            
            must_preserve.update(new_preservations)
        
        return must_preserve
    
    def export_dependency_graph(self, output_path: Path) -> None:
        """
        Export the dependency graph to a JSON file for visualization or debugging.
        
        Args:
            output_path: Path to save the dependency graph JSON
        """
        graph_data = {
            'metadata': {
                'total_messages': len(self.nodes),
                'root_nodes': len(self.root_nodes),
                'max_depth': self._calculate_max_depth()
            },
            'nodes': [],
            'edges': []
        }
        
        # Export nodes
        for node in self.nodes.values():
            graph_data['nodes'].append({
                'uuid': node.uuid,
                'type': node.message_type,
                'timestamp': node.timestamp,
                'content_preview': node.content[:100] + '...' if len(node.content) > 100 else node.content,
                'importance_score': node.importance_score,
                'children_count': len(node.children),
                'is_root': node.uuid in self.root_nodes,
                'marked_for_deletion': node.is_marked_for_deletion,
                'deletion_blocked': node.deletion_blocked_by_children
            })
        
        # Export edges (parent-child relationships)
        for node in self.nodes.values():
            for child_uuid in node.children:
                graph_data['edges'].append({
                    'parent': node.uuid,
                    'child': child_uuid
                })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Dependency graph exported to {output_path}")
    
    def _calculate_max_depth(self) -> int:
        """Calculate the maximum depth of the conversation tree."""
        max_depth = 0
        
        def calculate_depth(node_uuid: str, current_depth: int) -> int:
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            if node_uuid in self.nodes:
                node = self.nodes[node_uuid]
                for child_uuid in node.children:
                    calculate_depth(child_uuid, current_depth + 1)
            
            return max_depth
        
        for root_uuid in self.root_nodes:
            calculate_depth(root_uuid, 1)
        
        return max_depth


def analyze_conversation_dependencies(file_path: Path, 
                                   deletion_candidates: Set[str] = None,
                                   export_graph: bool = False) -> Dict[str, Any]:
    """
    Analyze conversation dependencies and provide safe deletion recommendations.
    
    Args:
        file_path: Path to JSONL conversation file
        deletion_candidates: Set of message UUIDs being considered for deletion
        export_graph: Whether to export dependency graph for visualization
        
    Returns:
        Dictionary with analysis results and recommendations
    """
    logger.info(f"🔍 Analyzing conversation dependencies in {file_path.name}")
    
    # Build dependency graph
    graph = ConversationDependencyGraph()
    if not graph.load_from_jsonl(file_path):
        return {'error': 'Failed to load conversation file'}
    
    result = {
        'file_path': str(file_path),
        'total_messages': len(graph.nodes),
        'root_messages': len(graph.root_nodes),
        'conversation_chains': len(graph.get_conversation_chains()),
        'max_depth': graph._calculate_max_depth()
    }
    
    # Analyze deletion candidates if provided
    if deletion_candidates:
        graph.mark_for_deletion(deletion_candidates)
        
        safe_deletions = graph.get_safe_deletion_set()
        preservation_report = graph.get_preservation_report()
        
        result.update({
            'deletion_analysis': {
                'originally_proposed': len(deletion_candidates),
                'safe_to_delete': len(safe_deletions),
                'must_preserve': preservation_report['preserved_by_dependencies'],
                'safe_deletion_uuids': list(safe_deletions),
                'preserved_uuids': list(graph.preserved_by_children),
                'preservation_details': preservation_report['preservation_details']
            }
        })
        
        # Validation
        is_safe, issues = graph.validate_deletion_safety(safe_deletions)
        result['deletion_analysis']['validation'] = {
            'is_safe': is_safe,
            'issues': issues
        }
    
    # Export graph if requested
    if export_graph:
        export_path = file_path.parent / f"{file_path.stem}_dependency_graph.json"
        graph.export_dependency_graph(export_path)
        result['exported_graph'] = str(export_path)
    
    return result


def main():
    """Command-line interface for dependency analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Analyze conversation dependencies and ensure safe message deletion'
    )
    parser.add_argument('input_file', type=Path, help='JSONL conversation file to analyze')
    parser.add_argument('--export-graph', action='store_true',
                       help='Export dependency graph to JSON file')
    parser.add_argument('--deletion-candidates', type=str,
                       help='Comma-separated list of message UUIDs to test for deletion')
    
    args = parser.parse_args()
    
    # Parse deletion candidates
    deletion_candidates = None
    if args.deletion_candidates:
        deletion_candidates = set(args.deletion_candidates.split(','))
    
    # Analyze dependencies
    result = analyze_conversation_dependencies(
        file_path=args.input_file,
        deletion_candidates=deletion_candidates,
        export_graph=args.export_graph
    )
    
    if 'error' in result:
        logger.error(f"❌ {result['error']}")
        return 1
    
    # Display results
    logger.info(f"\n📊 DEPENDENCY ANALYSIS RESULTS:")
    logger.info(f"   📝 Total messages: {result['total_messages']}")
    logger.info(f"   🌳 Root messages: {result['root_messages']}")
    logger.info(f"   🔗 Conversation chains: {result['conversation_chains']}")
    logger.info(f"   📏 Maximum depth: {result['max_depth']}")
    
    if 'deletion_analysis' in result:
        analysis = result['deletion_analysis']
        logger.info(f"\n🗑️  DELETION ANALYSIS:")
        logger.info(f"   📋 Originally proposed: {analysis['originally_proposed']}")
        logger.info(f"   ✅ Safe to delete: {analysis['safe_to_delete']}")
        logger.info(f"   🛡️  Must preserve: {analysis['must_preserve']}")
        
        if analysis['must_preserve'] > 0:
            logger.info(f"\n🔗 PRESERVATION DETAILS:")
            for detail in analysis['preservation_details']:
                logger.info(f"   • {detail['uuid']}: {detail['children_preserved']} children to preserve")
    
    return 0


if __name__ == "__main__":
    exit(main())