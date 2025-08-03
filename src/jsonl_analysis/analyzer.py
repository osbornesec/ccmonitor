"""
JSONL analyzer module for parsing and analyzing conversation files
Following TDD methodology - implementation based on test requirements
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, Counter
from datetime import datetime

from .exceptions import InvalidJSONLError, MalformedEntryError, ConversationFlowError

logger = logging.getLogger(__name__)


class JSONLAnalyzer:
    """Analyzes JSONL conversation files for structure and patterns"""
    
    def __init__(self):
        """Initialize analyzer with default configuration"""
        self.required_fields = {"uuid", "type", "message"}
        self.valid_message_types = {"user", "assistant", "tool_call", "system"}
        self.parsed_entries = []
        
    def parse_jsonl_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse JSONL file and return list of valid entries
        
        Args:
            file_path: Path to JSONL file
            
        Returns:
            List of parsed and validated JSON entries
            
        Raises:
            FileNotFoundError: If file doesn't exist
            InvalidJSONLError: If file structure is invalid
        """
        if not file_path.exists():
            raise FileNotFoundError(f"JSONL file not found: {file_path}")
            
        entries = []
        malformed_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue
                        
                    try:
                        entry = json.loads(line)
                        if self.validate_entry_structure(entry):
                            entries.append(entry)
                        else:
                            malformed_count += 1
                            logger.warning(f"Invalid entry structure at line {line_num}")
                            
                    except json.JSONDecodeError as e:
                        malformed_count += 1
                        logger.warning(f"Invalid JSON at line {line_num}: {e}")
                        continue
                        
        except Exception as e:
            raise InvalidJSONLError(f"Failed to parse JSONL file: {e}")
            
        if malformed_count > 0:
            logger.info(f"Parsed {len(entries)} valid entries, skipped {malformed_count} malformed entries")
            
        self.parsed_entries = entries
        return entries
    
    def validate_entry_structure(self, entry: Dict[str, Any]) -> bool:
        """
        Validate that entry has required structure for conversation analysis
        
        Args:
            entry: JSON entry to validate
            
        Returns:
            True if entry is valid, False otherwise
        """
        if not isinstance(entry, dict):
            return False
            
        # Check required fields
        if not all(field in entry for field in self.required_fields):
            return False
            
        # Validate message type
        if entry.get("type") not in self.valid_message_types:
            return False
            
        # Validate message structure
        message = entry.get("message")
        if not isinstance(message, dict):
            return False
            
        # UUID should be string
        if not isinstance(entry.get("uuid"), str):
            return False
            
        return True
    
    def identify_message_types(self, entries: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Categorize messages by type and count occurrences
        
        Args:
            entries: List of parsed JSONL entries
            
        Returns:
            Dictionary with message type counts
        """
        type_counts = Counter()
        
        for entry in entries:
            message_type = entry.get("type", "unknown")
            type_counts[message_type] += 1
            
        return dict(type_counts)
    
    def extract_tool_usage_patterns(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify and categorize tool usage patterns in conversation
        
        Args:
            entries: List of parsed JSONL entries
            
        Returns:
            Dictionary with tool usage analysis
        """
        tools_used = Counter()
        tool_sequences = []
        
        # First pass: collect tool usage
        for entry in entries:
            if entry.get("type") == "tool_call":
                message = entry.get("message", {})
                tool_name = message.get("tool")
                if tool_name:
                    tools_used[tool_name] += 1
        
        # Second pass: find tool sequences using conversation flow
        flow_analyzer = ConversationFlowAnalyzer()
        sequences = flow_analyzer.map_tool_call_sequences(entries)
        
        # If no flow-based sequences found, fall back to simple sequential detection
        if not sequences:
            current_sequence = []
            for entry in entries:
                if entry.get("type") == "tool_call":
                    message = entry.get("message", {})
                    tool_name = message.get("tool")
                    
                    if tool_name:
                        current_sequence.append(tool_name)
                    else:
                        # End current sequence if tool name missing
                        if current_sequence:
                            tool_sequences.append(current_sequence[:])
                            current_sequence = []
                else:
                    # Non-tool message ends current sequence only if it's not an assistant response
                    if entry.get("type") != "assistant" and current_sequence:
                        tool_sequences.append(current_sequence[:])
                        current_sequence = []
            
            # Add final sequence if exists
            if current_sequence:
                tool_sequences.append(current_sequence)
        else:
            tool_sequences = sequences
            
        return {
            "tools_used": dict(tools_used),
            "total_tool_calls": sum(tools_used.values()),
            "tool_sequences": tool_sequences,
            "unique_tools": len(tools_used)
        }


class ConversationFlowAnalyzer:
    """Analyzes conversation flow and dependencies using parentUuid chains"""
    
    def __init__(self):
        """Initialize flow analyzer"""
        self.dependency_map = {}
        self.orphans = []
        
    def map_conversation_dependencies(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build dependency map from parentUuid relationships
        
        Args:
            entries: List of conversation entries
            
        Returns:
            Dictionary mapping message dependencies and relationships
        """
        dependency_map = {}
        uuid_to_entry = {}
        orphans = []
        
        # First pass: create uuid mapping
        for entry in entries:
            uuid = entry.get("uuid")
            if uuid:
                uuid_to_entry[uuid] = entry
                dependency_map[uuid] = {
                    "parent": entry.get("parentUuid"),
                    "children": [],
                    "entry": entry
                }
        
        # Second pass: build parent-child relationships
        for uuid, info in dependency_map.items():
            parent_uuid = info["parent"]
            
            if parent_uuid:
                if parent_uuid in dependency_map:
                    # Valid parent relationship
                    dependency_map[parent_uuid]["children"].append(uuid)
                else:
                    # Orphaned message (parent doesn't exist)
                    orphans.append(uuid)
        
        # Add orphans list to result
        dependency_map["orphans"] = orphans
        
        self.dependency_map = dependency_map
        return dependency_map
    
    def identify_conversation_branches(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify points where conversation branches into multiple threads
        
        Args:
            entries: List of conversation entries
            
        Returns:
            Dictionary with branching analysis
        """
        if not hasattr(self, 'dependency_map') or not self.dependency_map:
            self.map_conversation_dependencies(entries)
            
        branch_points = {}
        
        for uuid, info in self.dependency_map.items():
            if uuid == "orphans":
                continue
                
            children = info["children"]
            if len(children) > 1:
                # This message has multiple responses (branch point)
                branch_points[uuid] = children
                
        return {
            "branch_points": branch_points,
            "total_branches": len(branch_points),
            "max_branch_width": max(len(children) for children in branch_points.values()) if branch_points else 0
        }
    
    def map_tool_call_sequences(self, entries: List[Dict[str, Any]]) -> List[List[str]]:
        """
        Map sequences of tool calls and their relationships
        
        Args:
            entries: List of conversation entries
            
        Returns:
            List of tool call sequences
        """
        if not hasattr(self, 'dependency_map') or not self.dependency_map:
            self.map_conversation_dependencies(entries)
            
        sequences = []
        visited_tools = set()
        
        # Find tool call chains by following parent-child relationships
        for uuid, info in self.dependency_map.items():
            if uuid == "orphans" or uuid in visited_tools:
                continue
                
            entry = info["entry"]
            if entry.get("type") == "tool_call":
                tool_name = entry.get("message", {}).get("tool")
                if tool_name:
                    # Build sequence starting from this tool
                    sequence, sequence_uuids = self._build_tool_sequence_with_uuids(uuid, [tool_name], [uuid])
                    if len(sequence) >= 1:  # Include all sequences
                        sequences.append(sequence)
                        visited_tools.update(sequence_uuids)
        
        return sequences
    
    def _build_tool_sequence_with_uuids(self, start_uuid: str, current_sequence: List[str], current_uuids: List[str]) -> Tuple[List[str], List[str]]:
        """Build tool sequence by following children, tracking UUIDs"""
        if not self.dependency_map or start_uuid not in self.dependency_map:
            return current_sequence, current_uuids
        
        # Look for tool call children in the dependency chain
        current = start_uuid
        sequence = current_sequence[:]
        uuids = current_uuids[:]
        
        while current in self.dependency_map:
            children = self.dependency_map[current]["children"]
            tool_child = None
            
            # Find direct tool call child OR tool call descended from assistant messages
            for child_uuid in children:
                if child_uuid in self.dependency_map:
                    child_entry = self.dependency_map[child_uuid]["entry"]
                    if child_entry.get("type") == "tool_call":
                        tool_child = child_uuid
                        break
                    elif child_entry.get("type") == "assistant":
                        # Check if this assistant message has tool call children
                        for grandchild_uuid in self.dependency_map[child_uuid]["children"]:
                            if grandchild_uuid in self.dependency_map:
                                grandchild_entry = self.dependency_map[grandchild_uuid]["entry"]
                                if grandchild_entry.get("type") == "tool_call":
                                    tool_child = grandchild_uuid
                                    break
                        if tool_child:
                            break
            
            if tool_child:
                tool_entry = self.dependency_map[tool_child]["entry"]
                tool_name = tool_entry.get("message", {}).get("tool")
                if tool_name and tool_child not in uuids:
                    sequence.append(tool_name)
                    uuids.append(tool_child)
                    current = tool_child
                else:
                    break
            else:
                break
        
        return sequence, uuids
    
    def _build_tool_sequence(self, start_uuid: str, current_sequence: List[str]) -> List[str]:
        """Build tool sequence by following children (legacy method)"""
        sequence, _ = self._build_tool_sequence_with_uuids(start_uuid, current_sequence, [start_uuid])
        return sequence
    
    def detect_circular_references(self, entries: List[Dict[str, Any]]) -> List[List[str]]:
        """
        Detect circular parentUuid references in conversation
        
        Args:
            entries: List of conversation entries
            
        Returns:
            List of circular reference chains
        """
        uuid_to_parent = {}
        
        # Build parent mapping
        for entry in entries:
            uuid = entry.get("uuid")
            parent_uuid = entry.get("parentUuid")
            if uuid and parent_uuid:
                uuid_to_parent[uuid] = parent_uuid
        
        circular_refs = []
        visited = set()
        
        # Check each message for circular references
        for start_uuid in uuid_to_parent:
            if start_uuid in visited:
                continue
                
            path = []
            current = start_uuid
            path_set = set()
            
            # Follow parent chain
            while current and current in uuid_to_parent:
                if current in path_set:
                    # Found cycle
                    cycle_start = path.index(current)
                    cycle = path[cycle_start:]
                    circular_refs.append(cycle)
                    break
                    
                path.append(current)
                path_set.add(current)
                current = uuid_to_parent[current]
            
            # Mark all nodes in this path as visited
            visited.update(path)
        
        return circular_refs
    
    def calculate_conversation_depth(self, entries: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate depth of each message in conversation tree
        
        Args:
            entries: List of conversation entries
            
        Returns:
            Dictionary mapping uuid to conversation depth
        """
        if not hasattr(self, 'dependency_map') or not self.dependency_map:
            self.map_conversation_dependencies(entries)
            
        depths = {}
        
        # Find root messages (no parent)
        roots = []
        for uuid, info in self.dependency_map.items():
            if uuid == "orphans":
                continue
            if not info["parent"]:
                roots.append(uuid)
                
        # Calculate depths using BFS from each root
        for root in roots:
            self._calculate_depth_recursive(root, 0, depths)
            
        # Handle orphans (assign special depth)
        for orphan_uuid in self.dependency_map.get("orphans", []):
            depths[orphan_uuid] = -1
            
        return depths
    
    def _calculate_depth_recursive(self, uuid: str, depth: int, depths: Dict[str, int]):
        """Recursively calculate depth for message tree"""
        if uuid not in self.dependency_map:
            return
            
        # Set depth for current message
        depths[uuid] = depth
        
        # Recursively process children
        children = self.dependency_map[uuid]["children"]
        for child_uuid in children:
            self._calculate_depth_recursive(child_uuid, depth + 1, depths)