"""
Refactored JSONL analyzer following clean code principles
- Single Responsibility Principle
- Strategy Pattern for validation
- Extract Method Pattern
- Dependency Injection
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Protocol
from collections import defaultdict, Counter
from datetime import datetime
from dataclasses import dataclass
from abc import ABC, abstractmethod

from .exceptions import InvalidJSONLError, MalformedEntryError, ConversationFlowError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ValidationRule:
    """Immutable validation rule configuration"""
    required_fields: Set[str]
    valid_message_types: Set[str]
    strict_mode: bool = True


@dataclass(frozen=True)
class AnalysisResult:
    """Immutable analysis result"""
    valid_entries: List[Dict[str, Any]]
    malformed_count: int
    total_lines: int
    message_types: Dict[str, int]
    tool_usage: Dict[str, Any]
    success: bool = True
    error_message: Optional[str] = None


class EntryValidator(ABC):
    """Abstract base class for entry validation strategies"""
    
    @abstractmethod
    def validate(self, entry: Dict[str, Any]) -> bool:
        """Validate a single entry"""
        pass
    
    @abstractmethod
    def get_validation_errors(self, entry: Dict[str, Any]) -> List[str]:
        """Get detailed validation errors for an entry"""
        pass


class StandardEntryValidator(EntryValidator):
    """Standard entry validator implementation"""
    
    def __init__(self, validation_rule: ValidationRule):
        self.validation_rule = validation_rule
    
    def validate(self, entry: Dict[str, Any]) -> bool:
        """Validate entry structure and content"""
        return len(self.get_validation_errors(entry)) == 0
    
    def get_validation_errors(self, entry: Dict[str, Any]) -> List[str]:
        """Get detailed validation errors"""
        errors = []
        
        # Check if entry is a dictionary
        if not isinstance(entry, dict):
            errors.append("Entry must be a dictionary")
            return errors
        
        # Check required fields
        missing_fields = self.validation_rule.required_fields - entry.keys()
        if missing_fields:
            errors.append(f"Missing required fields: {missing_fields}")
        
        # Validate message type
        message_type = entry.get("type")
        if message_type not in self.validation_rule.valid_message_types:
            errors.append(f"Invalid message type: {message_type}")
        
        # Validate message structure
        message = entry.get("message")
        if not isinstance(message, dict):
            errors.append("Message field must be a dictionary")
        
        # Validate UUID
        uuid = entry.get("uuid")
        if not isinstance(uuid, str) or not uuid.strip():
            errors.append("UUID must be a non-empty string")
        
        return errors


class JSONLParser:
    """Handles JSONL file parsing operations"""
    
    def __init__(self, validator: EntryValidator):
        self.validator = validator
    
    def parse_file(self, file_path: Path) -> AnalysisResult:
        """Parse JSONL file and return analysis result"""
        if not file_path.exists():
            return AnalysisResult(
                valid_entries=[],
                malformed_count=0,
                total_lines=0,
                message_types={},
                tool_usage={},
                success=False,
                error_message=f"File not found: {file_path}"
            )
        
        try:
            return self._parse_file_content(file_path)
        except Exception as e:
            logger.error(f"Failed to parse JSONL file: {e}")
            return AnalysisResult(
                valid_entries=[],
                malformed_count=0,
                total_lines=0,
                message_types={},
                tool_usage={},
                success=False,
                error_message=str(e)
            )
    
    def _parse_file_content(self, file_path: Path) -> AnalysisResult:
        """Parse file content and analyze entries"""
        valid_entries = []
        malformed_count = 0
        total_lines = 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                total_lines = line_num
                line = line.strip()
                
                if not line:  # Skip empty lines
                    continue
                
                try:
                    entry = json.loads(line)
                    if self.validator.validate(entry):
                        valid_entries.append(entry)
                    else:
                        malformed_count += 1
                        self._log_validation_errors(line_num, entry)
                        
                except json.JSONDecodeError as e:
                    malformed_count += 1
                    logger.warning(f"Invalid JSON at line {line_num}: {e}")
        
        # Analyze the parsed entries
        message_types = self._analyze_message_types(valid_entries)
        tool_usage = self._analyze_tool_usage(valid_entries)
        
        if malformed_count > 0:
            logger.info(f"Parsed {len(valid_entries)} valid entries, "
                       f"skipped {malformed_count} malformed entries")
        
        return AnalysisResult(
            valid_entries=valid_entries,
            malformed_count=malformed_count,
            total_lines=total_lines,
            message_types=message_types,
            tool_usage=tool_usage
        )
    
    def _log_validation_errors(self, line_num: int, entry: Dict[str, Any]) -> None:
        """Log validation errors for debugging"""
        errors = self.validator.get_validation_errors(entry)
        for error in errors:
            logger.warning(f"Validation error at line {line_num}: {error}")
    
    def _analyze_message_types(self, entries: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze message types in the entries"""
        type_counter = Counter()
        for entry in entries:
            message_type = entry.get("type", "unknown")
            type_counter[message_type] += 1
        return dict(type_counter)
    
    def _analyze_tool_usage(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze tool usage patterns"""
        tools_used = Counter()
        
        for entry in entries:
            if entry.get("type") == "tool_call":
                message = entry.get("message", {})
                tool_name = message.get("tool")
                if tool_name:
                    tools_used[tool_name] += 1
        
        return {
            "tools_used": dict(tools_used),
            "total_tool_calls": sum(tools_used.values()),
            "unique_tools": len(tools_used)
        }


class DependencyMapper:
    """Handles conversation dependency mapping"""
    
    def map_dependencies(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build dependency map from parentUuid relationships"""
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
                    "entry": entry,
                    "depth": 0
                }
        
        # Second pass: build parent-child relationships
        for uuid, info in dependency_map.items():
            parent_uuid = info["parent"]
            
            if parent_uuid:
                if parent_uuid in dependency_map:
                    dependency_map[parent_uuid]["children"].append(uuid)
                else:
                    orphans.append(uuid)
        
        # Third pass: calculate depths
        self._calculate_depths(dependency_map)
        
        return {
            "dependency_map": dependency_map,
            "orphans": orphans,
            "total_messages": len(dependency_map),
            "orphaned_messages": len(orphans)
        }
    
    def _calculate_depths(self, dependency_map: Dict[str, Any]) -> None:
        """Calculate conversation depth for each message"""
        # Find root messages (no parent)
        roots = [uuid for uuid, info in dependency_map.items() 
                if not info["parent"]]
        
        # Calculate depths using BFS
        for root in roots:
            self._calculate_depth_recursive(root, 0, dependency_map)
    
    def _calculate_depth_recursive(self, uuid: str, depth: int, 
                                 dependency_map: Dict[str, Any]) -> None:
        """Recursively calculate depth"""
        if uuid not in dependency_map:
            return
        
        dependency_map[uuid]["depth"] = depth
        
        # Process children
        children = dependency_map[uuid]["children"]
        for child_uuid in children:
            self._calculate_depth_recursive(child_uuid, depth + 1, dependency_map)


class BranchAnalyzer:
    """Analyzes conversation branching patterns"""
    
    def analyze_branches(self, dependency_map: Dict[str, Any]) -> Dict[str, Any]:
        """Identify conversation branch points"""
        branch_points = {}
        
        for uuid, info in dependency_map.items():
            children = info["children"]
            if len(children) > 1:
                branch_points[uuid] = {
                    "children": children,
                    "branch_count": len(children),
                    "message_type": info["entry"].get("type", "unknown")
                }
        
        return {
            "branch_points": branch_points,
            "total_branches": len(branch_points),
            "max_branch_width": max(
                len(children) for children in 
                (info["children"] for info in branch_points.values())
            ) if branch_points else 0
        }


class ToolSequenceAnalyzer:
    """Analyzes tool call sequences"""
    
    def __init__(self, dependency_mapper: DependencyMapper):
        self.dependency_mapper = dependency_mapper
    
    def analyze_tool_sequences(self, entries: List[Dict[str, Any]]) -> List[List[str]]:
        """Map sequences of tool calls using dependency relationships"""
        dependency_data = self.dependency_mapper.map_dependencies(entries)
        dependency_map = dependency_data["dependency_map"]
        
        sequences = []
        visited_tools = set()
        
        # Find tool call chains
        for uuid, info in dependency_map.items():
            if uuid in visited_tools:
                continue
            
            entry = info["entry"]
            if entry.get("type") == "tool_call":
                tool_name = entry.get("message", {}).get("tool")
                if tool_name:
                    sequence, sequence_uuids = self._build_tool_sequence(
                        uuid, dependency_map, [tool_name], [uuid]
                    )
                    if sequence:
                        sequences.append(sequence)
                        visited_tools.update(sequence_uuids)
        
        return sequences
    
    def _build_tool_sequence(self, start_uuid: str, dependency_map: Dict[str, Any],
                           current_sequence: List[str], current_uuids: List[str]) -> Tuple[List[str], List[str]]:
        """Build tool sequence by following dependency chain"""
        if start_uuid not in dependency_map:
            return current_sequence, current_uuids
        
        sequence = current_sequence[:]
        uuids = current_uuids[:]
        current = start_uuid
        
        while current in dependency_map:
            children = dependency_map[current]["children"]
            tool_child = self._find_tool_child(children, dependency_map)
            
            if tool_child and tool_child not in uuids:
                tool_entry = dependency_map[tool_child]["entry"]
                tool_name = tool_entry.get("message", {}).get("tool")
                if tool_name:
                    sequence.append(tool_name)
                    uuids.append(tool_child)
                    current = tool_child
                else:
                    break
            else:
                break
        
        return sequence, uuids
    
    def _find_tool_child(self, children: List[str], 
                        dependency_map: Dict[str, Any]) -> Optional[str]:
        """Find tool call child in children list"""
        for child_uuid in children:
            if child_uuid in dependency_map:
                child_entry = dependency_map[child_uuid]["entry"]
                if child_entry.get("type") == "tool_call":
                    return child_uuid
                
                # Check for tool calls in assistant message children
                if child_entry.get("type") == "assistant":
                    grandchildren = dependency_map[child_uuid]["children"]
                    for grandchild_uuid in grandchildren:
                        if grandchild_uuid in dependency_map:
                            grandchild_entry = dependency_map[grandchild_uuid]["entry"]
                            if grandchild_entry.get("type") == "tool_call":
                                return grandchild_uuid
        
        return None


class CircularReferenceDetector:
    """Detects circular references in conversation dependencies"""
    
    def detect_circular_references(self, entries: List[Dict[str, Any]]) -> List[List[str]]:
        """Detect circular parentUuid references"""
        uuid_to_parent = self._build_parent_mapping(entries)
        circular_refs = []
        visited = set()
        
        for start_uuid in uuid_to_parent:
            if start_uuid in visited:
                continue
            
            cycle = self._detect_cycle_from_node(start_uuid, uuid_to_parent)
            if cycle:
                circular_refs.append(cycle)
                visited.update(cycle)
        
        return circular_refs
    
    def _build_parent_mapping(self, entries: List[Dict[str, Any]]) -> Dict[str, str]:
        """Build mapping from UUID to parent UUID"""
        uuid_to_parent = {}
        for entry in entries:
            uuid = entry.get("uuid")
            parent_uuid = entry.get("parentUuid")
            if uuid and parent_uuid:
                uuid_to_parent[uuid] = parent_uuid
        return uuid_to_parent
    
    def _detect_cycle_from_node(self, start_uuid: str, 
                               uuid_to_parent: Dict[str, str]) -> Optional[List[str]]:
        """Detect cycle starting from a specific node"""
        path = []
        path_set = set()
        current = start_uuid
        
        while current and current in uuid_to_parent:
            if current in path_set:
                # Found cycle
                cycle_start = path.index(current)
                return path[cycle_start:]
            
            path.append(current)
            path_set.add(current)
            current = uuid_to_parent[current]
        
        return None


class RefactoredJSONLAnalyzer:
    """
    Refactored JSONL analyzer following clean code principles
    - Single Responsibility Principle
    - Dependency Injection
    - Strategy Pattern for validation
    """
    
    def __init__(self, validation_rule: Optional[ValidationRule] = None):
        # Setup validation rule
        self.validation_rule = validation_rule or ValidationRule(
            required_fields={"uuid", "type", "message"},
            valid_message_types={"user", "assistant", "tool_call", "system"}
        )
        
        # Initialize components with dependency injection
        self.validator = StandardEntryValidator(self.validation_rule)
        self.parser = JSONLParser(self.validator)
        self.dependency_mapper = DependencyMapper()
        self.branch_analyzer = BranchAnalyzer()
        self.tool_sequence_analyzer = ToolSequenceAnalyzer(self.dependency_mapper)
        self.circular_reference_detector = CircularReferenceDetector()
    
    def parse_jsonl_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse JSONL file and return valid entries (backward compatibility)"""
        result = self.parser.parse_file(file_path)
        if not result.success:
            raise InvalidJSONLError(result.error_message or "Failed to parse JSONL file")
        return result.valid_entries
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Perform comprehensive analysis of JSONL file"""
        # Parse file
        parse_result = self.parser.parse_file(file_path)
        if not parse_result.success:
            raise InvalidJSONLError(parse_result.error_message or "Failed to parse file")
        
        entries = parse_result.valid_entries
        
        # Perform various analyses
        dependency_data = self.dependency_mapper.map_dependencies(entries)
        branch_analysis = self.branch_analyzer.analyze_branches(dependency_data["dependency_map"])
        tool_sequences = self.tool_sequence_analyzer.analyze_tool_sequences(entries)
        circular_refs = self.circular_reference_detector.detect_circular_references(entries)
        
        return {
            "parsing": {
                "total_lines": parse_result.total_lines,
                "valid_entries": len(parse_result.valid_entries),
                "malformed_entries": parse_result.malformed_count,
                "success_rate": len(parse_result.valid_entries) / parse_result.total_lines if parse_result.total_lines > 0 else 0
            },
            "message_types": parse_result.message_types,
            "tool_usage": {
                **parse_result.tool_usage,
                "tool_sequences": tool_sequences
            },
            "conversation_flow": {
                "total_messages": dependency_data["total_messages"],
                "orphaned_messages": dependency_data["orphaned_messages"],
                "branch_analysis": branch_analysis,
                "circular_references": circular_refs
            }
        }
    
    def validate_entry_structure(self, entry: Dict[str, Any]) -> bool:
        """Validate entry structure (backward compatibility)"""
        return self.validator.validate(entry)


class RefactoredConversationFlowAnalyzer:
    """
    Refactored conversation flow analyzer with clean architecture
    """
    
    def __init__(self):
        self.dependency_mapper = DependencyMapper()
        self.branch_analyzer = BranchAnalyzer()
        self.tool_sequence_analyzer = ToolSequenceAnalyzer(self.dependency_mapper)
        self.circular_reference_detector = CircularReferenceDetector()
    
    def map_conversation_dependencies(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Map conversation dependencies (backward compatibility)"""
        dependency_data = self.dependency_mapper.map_dependencies(entries)
        
        # Convert to backward compatible format
        dependency_map = dependency_data["dependency_map"].copy()
        dependency_map["orphans"] = dependency_data["orphans"]
        
        return dependency_map
    
    def identify_conversation_branches(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify conversation branches (backward compatibility)"""
        dependency_data = self.dependency_mapper.map_dependencies(entries)
        return self.branch_analyzer.analyze_branches(dependency_data["dependency_map"])
    
    def map_tool_call_sequences(self, entries: List[Dict[str, Any]]) -> List[List[str]]:
        """Map tool call sequences (backward compatibility)"""
        return self.tool_sequence_analyzer.analyze_tool_sequences(entries)
    
    def detect_circular_references(self, entries: List[Dict[str, Any]]) -> List[List[str]]:
        """Detect circular references (backward compatibility)"""
        return self.circular_reference_detector.detect_circular_references(entries)
    
    def calculate_conversation_depth(self, entries: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate conversation depth (backward compatibility)"""
        dependency_data = self.dependency_mapper.map_dependencies(entries)
        dependency_map = dependency_data["dependency_map"]
        
        depths = {}
        for uuid, info in dependency_map.items():
            depths[uuid] = info["depth"]
        
        # Handle orphans
        for orphan_uuid in dependency_data["orphans"]:
            depths[orphan_uuid] = -1
        
        return depths