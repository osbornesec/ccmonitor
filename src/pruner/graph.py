"""
Conversation graph builder for dependency preservation
Phase 2 - Build and analyze conversation dependency graphs from parentUuid chains
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConversationNode:
    """Represents a node in the conversation graph"""
    uuid: str
    message: Dict[str, Any]
    parent_uuid: Optional[str]
    children_uuids: List[str]
    depth: int
    importance_score: float
    node_type: str  # 'root', 'branch', 'leaf', 'chain'


class ConversationGraphBuilder:
    """
    Builds conversation dependency graphs from parentUuid relationships
    and provides analysis methods for dependency preservation
    """
    
    def __init__(self):
        """Initialize conversation graph builder"""
        self.graph = {}
        self.roots = []
        self.orphans = []
        self.statistics = {}
    
    def build_graph(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build conversation graph from messages using parentUuid relationships
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Dictionary representation of conversation graph with analysis
        """
        # Reset state
        self.graph = {}
        self.roots = []
        self.orphans = []
        
        # Build nodes
        nodes = self._create_nodes(messages)
        
        # Build relationships
        self._build_relationships(nodes)
        
        # Analyze graph structure
        self._analyze_graph_structure()
        
        # Calculate node importance and types
        self._calculate_node_properties()
        
        return {
            'nodes': {uuid: self._node_to_dict(node) for uuid, node in self.graph.items()},
            'roots': self.roots,
            'orphans': self.orphans,
            'statistics': self.statistics,
            'conversation_chains': self._extract_conversation_chains(),
            'branch_points': self._find_branch_points(),
            'critical_paths': self._find_critical_paths()
        }
    
    def _create_nodes(self, messages: List[Dict[str, Any]]) -> Dict[str, ConversationNode]:
        """Create conversation nodes from messages"""
        nodes = {}
        
        for message in messages:
            uuid = message.get('uuid', '')
            if not uuid:
                logger.warning("Message missing UUID, skipping")
                continue
            
            parent_uuid = message.get('parentUuid')
            
            node = ConversationNode(
                uuid=uuid,
                message=message,
                parent_uuid=parent_uuid,
                children_uuids=[],
                depth=0,
                importance_score=0.0,
                node_type='unknown'
            )
            
            nodes[uuid] = node
        
        return nodes
    
    def _build_relationships(self, nodes: Dict[str, ConversationNode]):
        """Build parent-child relationships between nodes"""
        for uuid, node in nodes.items():
            parent_uuid = node.parent_uuid
            
            if parent_uuid:
                if parent_uuid in nodes:
                    # Valid parent relationship
                    parent_node = nodes[parent_uuid]
                    parent_node.children_uuids.append(uuid)
                else:
                    # Orphaned node (parent doesn't exist)
                    logger.warning(f"Orphaned node {uuid} - parent {parent_uuid} not found")
                    self.orphans.append(uuid)
            else:
                # Root node
                self.roots.append(uuid)
        
        # Store processed graph
        self.graph = nodes
        
        logger.info(f"Built graph with {len(nodes)} nodes, {len(self.roots)} roots, {len(self.orphans)} orphans")
    
    def _analyze_graph_structure(self):
        """Analyze graph structure and compute statistics"""
        total_nodes = len(self.graph)
        total_edges = sum(len(node.children_uuids) for node in self.graph.values())
        
        # Calculate depth for each node
        self._calculate_depths()
        
        # Find leaf nodes
        leaf_nodes = [uuid for uuid, node in self.graph.items() if not node.children_uuids]
        
        # Calculate branching factor
        branch_nodes = [node for node in self.graph.values() if len(node.children_uuids) > 1]
        max_branching_factor = max((len(node.children_uuids) for node in branch_nodes), default=0)
        avg_branching_factor = (sum(len(node.children_uuids) for node in branch_nodes) / 
                               len(branch_nodes)) if branch_nodes else 0
        
        # Calculate graph metrics
        max_depth = max((node.depth for node in self.graph.values()), default=0)
        avg_depth = sum(node.depth for node in self.graph.values()) / total_nodes if total_nodes > 0 else 0
        
        # Find longest chains
        longest_chains = self._find_longest_chains()
        
        self.statistics = {
            'total_nodes': total_nodes,
            'total_edges': total_edges,
            'root_nodes': len(self.roots),
            'leaf_nodes': len(leaf_nodes),
            'orphan_nodes': len(self.orphans),
            'branch_nodes': len(branch_nodes),
            'max_depth': max_depth,
            'avg_depth': avg_depth,
            'max_branching_factor': max_branching_factor,
            'avg_branching_factor': avg_branching_factor,
            'longest_chain_length': max((len(chain) for chain in longest_chains), default=0),
            'total_chains': len(longest_chains),
            'connectivity_ratio': (total_edges / total_nodes) if total_nodes > 0 else 0
        }
    
    def _calculate_depths(self):
        """Calculate depth for each node using BFS from roots"""
        # Initialize root depths
        for root_uuid in self.roots:
            if root_uuid in self.graph:
                self.graph[root_uuid].depth = 0
        
        # BFS to calculate depths
        queue = deque(self.roots)
        visited = set(self.roots)
        
        while queue:
            current_uuid = queue.popleft()
            current_node = self.graph[current_uuid]
            
            for child_uuid in current_node.children_uuids:
                if child_uuid in self.graph and child_uuid not in visited:
                    child_node = self.graph[child_uuid]
                    child_node.depth = current_node.depth + 1
                    queue.append(child_uuid)
                    visited.add(child_uuid)
        
        # Handle orphans (assign special depth)
        for orphan_uuid in self.orphans:
            if orphan_uuid in self.graph:
                self.graph[orphan_uuid].depth = -1
    
    def _calculate_node_properties(self):
        """Calculate importance scores and node types"""
        from ..jsonl_analysis.scoring import ImportanceScorer
        
        scorer = ImportanceScorer()
        
        for uuid, node in self.graph.items():
            # Calculate importance score
            node.importance_score = scorer.calculate_message_importance(node.message)
            
            # Determine node type
            node.node_type = self._determine_node_type(node)
    
    def _determine_node_type(self, node: ConversationNode) -> str:
        """Determine the type of conversation node"""
        if not node.parent_uuid:
            return 'root'
        elif not node.children_uuids:
            return 'leaf'
        elif len(node.children_uuids) > 1:
            return 'branch'
        else:
            return 'chain'
    
    def _extract_conversation_chains(self) -> List[List[str]]:
        """Extract linear conversation chains from the graph using iterative approach"""
        chains = []
        
        # For each root, find the longest chain
        for root_uuid in self.roots:
            if root_uuid in self.graph:
                chain = self._build_longest_chain_from_root(root_uuid)
                if len(chain) > 1:  # Only include multi-message chains
                    chains.append(chain)
        
        return chains
    
    def _build_longest_chain_from_root(self, root_uuid: str) -> List[str]:
        """Build longest chain from root using iterative approach"""
        if root_uuid not in self.graph:
            return []
        
        chain = [root_uuid]
        current_uuid = root_uuid
        visited = set([root_uuid])
        
        # Follow the chain, preferring the child with most descendants
        while current_uuid in self.graph:
            node = self.graph[current_uuid]
            children = node.children_uuids
            
            if not children:
                break
            
            # Find unvisited child with most descendants (or first unvisited child)
            best_child = None
            for child_uuid in children:
                if child_uuid not in visited and child_uuid in self.graph:
                    best_child = child_uuid
                    break
            
            if best_child:
                chain.append(best_child)
                visited.add(best_child)
                current_uuid = best_child
            else:
                break
        
        return chain
    
    def _find_longest_chains(self) -> List[List[str]]:
        """Find the longest conversation chains in the graph"""
        all_chains = self._extract_conversation_chains()
        
        if not all_chains:
            return []
        
        max_length = max(len(chain) for chain in all_chains)
        longest_chains = [chain for chain in all_chains if len(chain) == max_length]
        
        return longest_chains
    
    def _find_branch_points(self) -> Dict[str, Dict[str, Any]]:
        """Find points where conversation branches into multiple threads"""
        branch_points = {}
        
        for uuid, node in self.graph.items():
            if len(node.children_uuids) > 1:
                # This is a branch point
                branch_info = {
                    'node_uuid': uuid,
                    'children': node.children_uuids,
                    'branch_factor': len(node.children_uuids),
                    'depth': node.depth,
                    'importance_score': node.importance_score,
                    'message_type': node.message.get('type', 'unknown')
                }
                
                # Analyze children importance
                children_scores = []
                for child_uuid in node.children_uuids:
                    if child_uuid in self.graph:
                        children_scores.append(self.graph[child_uuid].importance_score)
                
                branch_info['children_importance'] = {
                    'scores': children_scores,
                    'max_score': max(children_scores) if children_scores else 0,
                    'avg_score': sum(children_scores) / len(children_scores) if children_scores else 0
                }
                
                branch_points[uuid] = branch_info
        
        return branch_points
    
    def _find_critical_paths(self) -> List[Dict[str, Any]]:
        """Find critical paths in the conversation graph"""
        critical_paths = []
        
        # Find paths with high importance scores
        all_chains = self._extract_conversation_chains()
        
        for chain in all_chains:
            # Calculate chain importance
            chain_importance = self._calculate_chain_importance(chain)
            
            # Consider chains with high average importance as critical
            if chain_importance['avg_importance'] >= 50:  # Threshold for critical paths
                critical_path = {
                    'chain': chain,
                    'length': len(chain),
                    'total_importance': chain_importance['total_importance'],
                    'avg_importance': chain_importance['avg_importance'],
                    'contains_errors': chain_importance['contains_errors'],
                    'contains_code_changes': chain_importance['contains_code_changes'],
                    'start_type': self.graph[chain[0]].message.get('type', 'unknown') if chain else 'unknown',
                    'end_type': self.graph[chain[-1]].message.get('type', 'unknown') if chain else 'unknown'
                }
                critical_paths.append(critical_path)
        
        # Sort by importance
        critical_paths.sort(key=lambda x: x['avg_importance'], reverse=True)
        
        return critical_paths
    
    def _calculate_chain_importance(self, chain: List[str]) -> Dict[str, Any]:
        """Calculate importance metrics for a conversation chain"""
        if not chain:
            return {
                'total_importance': 0,
                'avg_importance': 0,
                'contains_errors': False,
                'contains_code_changes': False
            }
        
        total_importance = 0
        contains_errors = False
        contains_code_changes = False
        
        for uuid in chain:
            if uuid in self.graph:
                node = self.graph[uuid]
                total_importance += node.importance_score
                
                # Check for error-related content
                message_content = self._extract_message_content(node.message)
                if any(keyword in message_content.lower() for keyword in ['error', 'exception', 'failed', 'traceback']):
                    contains_errors = True
                
                # Check for code changes
                if (node.message.get('type') == 'tool_call' and 
                    node.message.get('message', {}).get('tool') in ['Write', 'Edit', 'MultiEdit']):
                    contains_code_changes = True
        
        return {
            'total_importance': total_importance,
            'avg_importance': total_importance / len(chain),
            'contains_errors': contains_errors,
            'contains_code_changes': contains_code_changes
        }
    
    def _extract_message_content(self, message: Dict[str, Any]) -> str:
        """Extract text content from message"""
        if 'message' in message:
            msg_content = message['message']
            if isinstance(msg_content, dict):
                content_parts = []
                for key, value in msg_content.items():
                    if isinstance(value, str):
                        content_parts.append(value)
                return ' '.join(content_parts)
            else:
                return str(msg_content)
        return ""
    
    def _node_to_dict(self, node: ConversationNode) -> Dict[str, Any]:
        """Convert ConversationNode to dictionary representation"""
        return {
            'uuid': node.uuid,
            'parent_uuid': node.parent_uuid,
            'children_uuids': node.children_uuids,
            'depth': node.depth,
            'importance_score': node.importance_score,
            'node_type': node.node_type,
            'message_type': node.message.get('type', 'unknown'),
            'timestamp': node.message.get('timestamp'),
            'has_children': len(node.children_uuids) > 0,
            'is_root': node.parent_uuid is None,
            'is_leaf': len(node.children_uuids) == 0
        }
    
    def get_dependency_preserved_uuids(
        self, 
        important_uuids: Set[str], 
        preserve_parents: bool = True,
        preserve_children: bool = False
    ) -> Set[str]:
        """
        Get UUIDs that need to be preserved to maintain conversation dependencies
        
        Args:
            important_uuids: Set of UUIDs marked as important
            preserve_parents: Whether to preserve parent chains
            preserve_children: Whether to preserve children of important messages
            
        Returns:
            Set of UUIDs that must be preserved for dependency integrity
        """
        preserved_uuids = set(important_uuids)
        
        for uuid in important_uuids:
            if uuid not in self.graph:
                continue
            
            # Preserve parent chain
            if preserve_parents:
                current = uuid
                while current and current in self.graph:
                    preserved_uuids.add(current)
                    parent_uuid = self.graph[current].parent_uuid
                    if parent_uuid and parent_uuid in self.graph:
                        current = parent_uuid
                    else:
                        break
            
            # Preserve children
            if preserve_children:
                self._preserve_children_recursive(uuid, preserved_uuids)
        
        return preserved_uuids
    
    def _preserve_children_recursive(self, uuid: str, preserved_uuids: Set[str]):
        """Recursively preserve children of a node"""
        if uuid not in self.graph:
            return
        
        node = self.graph[uuid]
        for child_uuid in node.children_uuids:
            if child_uuid not in preserved_uuids:
                preserved_uuids.add(child_uuid)
                self._preserve_children_recursive(child_uuid, preserved_uuids)
    
    def validate_graph_integrity(self) -> Dict[str, Any]:
        """Validate the integrity of the conversation graph"""
        issues = []
        
        # Check for circular references
        circular_refs = self._detect_circular_references()
        if circular_refs:
            issues.append(f"Circular references detected: {circular_refs}")
        
        # Check for orphaned nodes
        if self.orphans:
            issues.append(f"{len(self.orphans)} orphaned nodes found")
        
        # Check for duplicate UUIDs
        uuids = list(self.graph.keys())
        if len(uuids) != len(set(uuids)):
            issues.append("Duplicate UUIDs detected")
        
        # Check parent-child consistency
        inconsistencies = self._check_parent_child_consistency()
        if inconsistencies:
            issues.extend(inconsistencies)
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'total_nodes': len(self.graph),
            'orphaned_nodes': len(self.orphans),
            'root_nodes': len(self.roots)
        }
    
    def _detect_circular_references(self) -> List[List[str]]:
        """Detect circular references in parent-child relationships"""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(uuid: str, path: List[str]) -> bool:
            if uuid in rec_stack:
                # Found cycle
                cycle_start = path.index(uuid)
                cycles.append(path[cycle_start:] + [uuid])
                return True
            
            if uuid in visited:
                return False
            
            visited.add(uuid)
            rec_stack.add(uuid)
            
            if uuid in self.graph:
                for child_uuid in self.graph[uuid].children_uuids:
                    if dfs(child_uuid, path + [uuid]):
                        return True
            
            rec_stack.remove(uuid)
            return False
        
        # Check each unvisited node
        for uuid in self.graph:
            if uuid not in visited:
                dfs(uuid, [])
        
        return cycles
    
    def _check_parent_child_consistency(self) -> List[str]:
        """Check consistency between parent and children relationships"""
        inconsistencies = []
        
        for uuid, node in self.graph.items():
            # Check that parent's children list includes this node
            if node.parent_uuid and node.parent_uuid in self.graph:
                parent_node = self.graph[node.parent_uuid]
                if uuid not in parent_node.children_uuids:
                    inconsistencies.append(
                        f"Node {uuid} claims parent {node.parent_uuid} but parent doesn't list it as child"
                    )
            
            # Check that children's parent points back to this node
            for child_uuid in node.children_uuids:
                if child_uuid in self.graph:
                    child_node = self.graph[child_uuid]
                    if child_node.parent_uuid != uuid:
                        inconsistencies.append(
                            f"Node {uuid} claims child {child_uuid} but child's parent is {child_node.parent_uuid}"
                        )
        
        return inconsistencies