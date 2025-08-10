"""JSONL analyzer module for parsing and analyzing conversation files.

Following TDD methodology - implementation based on test requirements.
"""

import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any

from .exceptions import InvalidJSONLError

logger = logging.getLogger(__name__)


class JSONLAnalyzer:
    """Analyzes JSONL conversation files for structure and patterns."""

    def __init__(self) -> None:
        """Initialize analyzer with default configuration."""
        self.required_fields = {"uuid", "type", "message"}
        self.valid_message_types = {"user", "assistant", "tool_call", "system"}
        self.parsed_entries: list[dict[str, Any]] = []

    def parse_jsonl_file(self, file_path: Path) -> list[dict[str, Any]]:
        """Parse JSONL file and return list of valid entries.

        Args:
            file_path: Path to JSONL file

        Returns:
            List of parsed and validated JSON entries

        Raises:
            FileNotFoundError: If file doesn't exist
            InvalidJSONLError: If file structure is invalid

        """
        if not file_path.exists():
            msg = f"JSONL file not found: {file_path}"
            raise FileNotFoundError(msg)

        try:
            entries, malformed_count = self._parse_file_lines(file_path)
            self._log_parsing_results(entries, malformed_count)
        except Exception as e:
            msg = f"Failed to parse JSONL file: {e}"
            raise InvalidJSONLError(msg) from e
        else:
            self.parsed_entries = entries
            return entries

    def _parse_file_lines(self, file_path: Path) -> tuple[list[dict[str, Any]], int]:
        """Parse all lines in the JSONL file and return entries with error count."""
        entries = []
        malformed_count = 0

        with file_path.open(encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                stripped_line = line.strip()
                if not stripped_line:  # Skip empty lines
                    continue

                entry, is_valid = self._parse_single_line(stripped_line, line_num)
                if is_valid and entry:
                    entries.append(entry)
                elif not is_valid:
                    malformed_count += 1

        return entries, malformed_count

    def _parse_single_line(
        self, line: str, line_num: int,
    ) -> tuple[dict[str, Any] | None, bool]:
        """Parse a single line and return the entry and validity status."""
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as e:
            logger.warning("Invalid JSON at line %d: %s", line_num, e)
            return None, False
        else:
            if self.validate_entry_structure(entry):
                return entry, True
            logger.warning("Invalid entry structure at line %d", line_num)
            return None, False

    def _log_parsing_results(
        self, entries: list[dict[str, Any]], malformed_count: int,
    ) -> None:
        """Log the results of the parsing operation."""
        if malformed_count > 0:
            logger.info(
                "Parsed %d valid entries, skipped %d malformed entries",
                len(entries),
                malformed_count,
            )

    def validate_entry_structure(self, entry: dict[str, Any]) -> bool:
        """Validate that entry has required structure for conversation analysis.

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
        return isinstance(entry.get("uuid"), str)

    def identify_message_types(self, entries: list[dict[str, Any]]) -> dict[str, int]:
        """Categorize messages by type and count occurrences.

        Args:
            entries: List of parsed JSONL entries

        Returns:
            Dictionary with message type counts

        """
        type_counts: Counter[str] = Counter()

        for entry in entries:
            message_type = entry.get("type", "unknown")
            type_counts[message_type] += 1

        return dict(type_counts)

    def extract_tool_usage_patterns(
        self, entries: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Identify and categorize tool usage patterns in conversation.

        Args:
            entries: List of parsed JSONL entries

        Returns:
            Dictionary with tool usage analysis

        """
        tools_used = self._collect_tool_usage(entries)
        tool_sequences = self._extract_tool_sequences(entries)

        return {
            "tools_used": dict(tools_used),
            "total_tool_calls": sum(tools_used.values()),
            "tool_sequences": tool_sequences,
            "unique_tools": len(tools_used),
        }

    def _collect_tool_usage(self, entries: list[dict[str, Any]]) -> Counter[str]:
        """Collect tool usage counts from entries."""
        tools_used: Counter[str] = Counter()

        for entry in entries:
            if entry.get("type") == "tool_call":
                message = entry.get("message", {})
                tool_name = message.get("tool")
                if tool_name:
                    tools_used[tool_name] += 1

        return tools_used

    def _extract_tool_sequences(self, entries: list[dict[str, Any]]) -> list[list[str]]:
        """Extract tool sequences using conversation flow analysis."""
        # Try flow-based sequence detection first
        flow_analyzer = ConversationFlowAnalyzer()
        sequences = flow_analyzer.map_tool_call_sequences(entries)

        if sequences:
            return sequences

        # Fall back to simple sequential detection
        return self._extract_simple_sequences(entries)

    def _extract_simple_sequences(
        self, entries: list[dict[str, Any]],
    ) -> list[list[str]]:
        """Extract tool sequences using simple sequential detection."""
        tool_sequences: list[list[str]] = []
        current_sequence: list[str] = []

        for entry in entries:
            if self._is_tool_call(entry):
                current_sequence = self._process_tool_call_entry(
                    entry, current_sequence, tool_sequences,
                )
            elif self._should_end_sequence(entry, current_sequence):
                tool_sequences.append(current_sequence[:])
                current_sequence = []

        # Add final sequence if exists
        if current_sequence:
            tool_sequences.append(current_sequence)

        return tool_sequences

    def _process_tool_call_entry(
        self,
        entry: dict[str, Any],
        current_sequence: list[str],
        tool_sequences: list[list[str]],
    ) -> list[str]:
        """Process a tool call entry and update the current sequence."""
        tool_name = self._get_tool_name(entry)
        if tool_name:
            current_sequence.append(tool_name)
            return current_sequence
        if current_sequence:
            # End current sequence if tool name missing
            tool_sequences.append(current_sequence[:])
            return []
        return current_sequence

    def _is_tool_call(self, entry: dict[str, Any]) -> bool:
        """Check if entry is a tool call."""
        return entry.get("type") == "tool_call"

    def _get_tool_name(self, entry: dict[str, Any]) -> str | None:
        """Get tool name from tool call entry."""
        message = entry.get("message", {})
        tool_name = message.get("tool")
        return tool_name if isinstance(tool_name, str) else None

    def _should_end_sequence(
        self, entry: dict[str, Any], current_sequence: list[str],
    ) -> bool:
        """Check if entry should end current tool sequence."""
        return entry.get("type") != "assistant" and bool(current_sequence)


class ConversationFlowAnalyzer:
    """Analyzes conversation flow and dependencies using parentUuid chains."""

    def __init__(self) -> None:
        """Initialize flow analyzer."""
        self.dependency_map: dict[str, dict[str, Any]] = {}
        self.orphans: list[str] = []

    def map_conversation_dependencies(
        self, entries: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build dependency map from parentUuid relationships.

        Args:
            entries: List of conversation entries

        Returns:
            Dictionary mapping message dependencies and relationships

        """
        dependency_map: dict[str, Any] = {}
        orphans: list[str] = []

        # First pass: create uuid mapping
        self._create_uuid_mapping(entries, dependency_map)

        # Second pass: build parent-child relationships
        self._build_parent_child_relationships(dependency_map, orphans)

        # Add orphans list to result
        dependency_map["orphans"] = orphans

        self.dependency_map = dependency_map
        return dependency_map

    def _create_uuid_mapping(
        self, entries: list[dict[str, Any]], dependency_map: dict[str, Any],
    ) -> None:
        """Create initial UUID mapping for all entries."""
        for entry in entries:
            uuid = entry.get("uuid")
            if uuid:
                dependency_map[uuid] = {
                    "parent": entry.get("parentUuid"),
                    "children": [],
                    "entry": entry,
                }

    def _build_parent_child_relationships(
        self, dependency_map: dict[str, Any], orphans: list[str],
    ) -> None:
        """Build parent-child relationships and identify orphans."""
        for uuid, info in dependency_map.items():
            parent_uuid = info["parent"]

            if not parent_uuid:
                continue

            if parent_uuid in dependency_map:
                # Valid parent relationship
                dependency_map[parent_uuid]["children"].append(uuid)
            else:
                # Orphaned message (parent doesn't exist)
                orphans.append(uuid)

    def identify_conversation_branches(
        self, entries: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Identify points where conversation branches into multiple threads.

        Args:
            entries: List of conversation entries

        Returns:
            Dictionary with branching analysis

        """
        if not hasattr(self, "dependency_map") or not self.dependency_map:
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
            "max_branch_width": (
                max(len(children) for children in branch_points.values())
                if branch_points
                else 0
            ),
        }

    def map_tool_call_sequences(self, entries: list[dict[str, Any]]) -> list[list[str]]:
        """Map sequences of tool calls and their relationships.

        Args:
            entries: List of conversation entries

        Returns:
            List of tool call sequences

        """
        self._ensure_dependency_map_exists(entries)

        sequences: list[list[str]] = []
        visited_tools: set[str] = set()

        # Find tool call chains by following parent-child relationships
        for uuid, info in self.dependency_map.items():
            if self._should_skip_uuid(uuid, visited_tools):
                continue

            sequences, visited_tools = self._process_tool_call_for_sequences(
                uuid, info, sequences, visited_tools,
            )

        return sequences

    def _ensure_dependency_map_exists(self, entries: list[dict[str, Any]]) -> None:
        """Ensure dependency map is built before processing."""
        if not hasattr(self, "dependency_map") or not self.dependency_map:
            self.map_conversation_dependencies(entries)

    def _should_skip_uuid(self, uuid: str, visited_tools: set[str]) -> bool:
        """Check if UUID should be skipped during sequence building."""
        return uuid == "orphans" or uuid in visited_tools

    def _process_tool_call_for_sequences(
        self,
        uuid: str,
        info: dict[str, Any],
        sequences: list[list[str]],
        visited_tools: set[str],
    ) -> tuple[list[list[str]], set[str]]:
        """Process a tool call entry to build sequences."""
        entry = info["entry"]
        if entry.get("type") != "tool_call":
            return sequences, visited_tools

        tool_name = entry.get("message", {}).get("tool")
        if not tool_name:
            return sequences, visited_tools

        # Build sequence starting from this tool
        sequence, sequence_uuids = self._build_tool_sequence_with_uuids(
            uuid, [tool_name], [uuid],
        )
        if len(sequence) >= 1:  # Include all sequences
            sequences.append(sequence)
            visited_tools.update(sequence_uuids)

        return sequences, visited_tools

    def _build_tool_sequence_with_uuids(
        self, start_uuid: str, current_sequence: list[str], current_uuids: list[str],
    ) -> tuple[list[str], list[str]]:
        """Build tool sequence by following children, tracking UUIDs."""
        if not self.dependency_map or start_uuid not in self.dependency_map:
            return current_sequence, current_uuids

        sequence = current_sequence[:]
        uuids = current_uuids[:]
        current = start_uuid

        while current in self.dependency_map:
            tool_child = self._find_tool_child(current)
            if not tool_child:
                break

            tool_info = self._extract_tool_info(tool_child)
            if not tool_info or tool_child in uuids:
                break

            sequence.append(tool_info)
            uuids.append(tool_child)
            current = tool_child

        return sequence, uuids

    def _find_tool_child(self, parent_uuid: str) -> str | None:
        """Find tool call child in dependency chain."""
        if parent_uuid not in self.dependency_map:
            return None

        children = self.dependency_map[parent_uuid]["children"]
        return self._search_for_tool_in_children(children)

    def _search_for_tool_in_children(self, children: list[str]) -> str | None:
        """Search for tool calls in children, including grandchildren."""
        for child_uuid in children:
            if child_uuid not in self.dependency_map:
                continue

            # Check if child is directly a tool call
            direct_tool = self._check_for_direct_tool_call(child_uuid)
            if direct_tool:
                return direct_tool

            # Check grandchildren if child is assistant
            grandchild_tool = self._check_for_grandchild_tool_calls(child_uuid)
            if grandchild_tool:
                return grandchild_tool

        return None

    def _check_for_direct_tool_call(self, child_uuid: str) -> str | None:
        """Check if child is a direct tool call."""
        child_entry = self.dependency_map[child_uuid]["entry"]
        if child_entry.get("type") == "tool_call":
            return child_uuid
        return None

    def _check_for_grandchild_tool_calls(self, child_uuid: str) -> str | None:
        """Check for tool calls in grandchildren of assistant messages."""
        child_entry = self.dependency_map[child_uuid]["entry"]
        if child_entry.get("type") != "assistant":
            return None

        return self._find_tool_in_grandchildren(child_uuid)

    def _find_tool_in_grandchildren(self, parent_uuid: str) -> str | None:
        """Find tool calls in grandchildren of assistant messages."""
        if parent_uuid not in self.dependency_map:
            return None

        for grandchild_uuid in self.dependency_map[parent_uuid]["children"]:
            if (
                isinstance(grandchild_uuid, str)
                and grandchild_uuid in self.dependency_map
            ):
                grandchild_entry = self.dependency_map[grandchild_uuid]["entry"]
                if grandchild_entry.get("type") == "tool_call":
                    return grandchild_uuid

        return None

    def _extract_tool_info(self, tool_uuid: str) -> str | None:
        """Extract tool name from tool call entry."""
        if tool_uuid not in self.dependency_map:
            return None

        tool_entry = self.dependency_map[tool_uuid]["entry"]
        tool_name = tool_entry.get("message", {}).get("tool")
        return tool_name if isinstance(tool_name, str) else None

    def _build_tool_sequence(
        self, start_uuid: str, current_sequence: list[str],
    ) -> list[str]:
        """Build tool sequence by following children (legacy method)."""
        sequence, _ = self._build_tool_sequence_with_uuids(
            start_uuid, current_sequence, [start_uuid],
        )
        return sequence

    def detect_circular_references(
        self, entries: list[dict[str, Any]],
    ) -> list[list[str]]:
        """Detect circular parentUuid references in conversation.

        Args:
            entries: List of conversation entries

        Returns:
            List of circular reference chains

        """
        uuid_to_parent = self._build_parent_mapping(entries)
        return self._find_all_circular_references(uuid_to_parent)

    def _build_parent_mapping(self, entries: list[dict[str, Any]]) -> dict[str, str]:
        """Build mapping from UUID to parent UUID."""
        uuid_to_parent = {}
        for entry in entries:
            uuid = entry.get("uuid")
            parent_uuid = entry.get("parentUuid")
            if uuid and parent_uuid:
                uuid_to_parent[uuid] = parent_uuid
        return uuid_to_parent

    def _find_all_circular_references(
        self, uuid_to_parent: dict[str, str],
    ) -> list[list[str]]:
        """Find all circular references in the parent mapping."""
        circular_refs = []
        visited = set()

        for start_uuid in uuid_to_parent:
            if start_uuid in visited:
                continue

            cycle, path_nodes = self._detect_cycle_from_node(start_uuid, uuid_to_parent)
            if cycle:
                circular_refs.append(cycle)

            # Mark all nodes in this path as visited
            visited.update(path_nodes)

        return circular_refs

    def _detect_cycle_from_node(
        self, start_uuid: str, uuid_to_parent: dict[str, str],
    ) -> tuple[list[str] | None, list[str]]:
        """Detect cycle starting from a specific node."""
        path: list[str] = []
        path_set = set()
        current = start_uuid

        # Follow parent chain
        while current and current in uuid_to_parent:
            if current in path_set:
                # Found cycle
                cycle_start = path.index(current)
                return path[cycle_start:], path

            path.append(current)
            path_set.add(current)
            current = uuid_to_parent[current]

        return None, path

    def calculate_conversation_depth(
        self, entries: list[dict[str, Any]],
    ) -> dict[str, int]:
        """Calculate depth of each message in conversation tree.

        Args:
            entries: List of conversation entries

        Returns:
            Dictionary mapping uuid to conversation depth

        """
        self._ensure_dependency_map_exists(entries)

        depths: dict[str, int] = {}
        roots = self._find_root_messages()

        # Calculate depths from each root
        self._assign_depths_from_roots(roots, depths)

        # Handle orphans (assign special depth)
        self._assign_orphan_depths(depths)

        return depths

    def _find_root_messages(self) -> list[str]:
        """Find root messages (messages with no parent)."""
        roots = []
        for uuid, info in self.dependency_map.items():
            if uuid == "orphans":
                continue
            if not info["parent"]:
                roots.append(uuid)
        return roots

    def _assign_depths_from_roots(
        self, roots: list[str], depths: dict[str, int],
    ) -> None:
        """Calculate depths using recursive traversal from each root."""
        for root in roots:
            self._calculate_depth_recursive(root, 0, depths)

    def _assign_orphan_depths(self, depths: dict[str, int]) -> None:
        """Assign special depth to orphaned messages."""
        for orphan_uuid in self.dependency_map.get("orphans", []):
            depths[orphan_uuid] = -1

    def _calculate_depth_recursive(
        self, uuid: str, depth: int, depths: dict[str, int],
    ) -> None:
        """Recursively calculate depth for message tree."""
        if uuid not in self.dependency_map:
            return

        # Set depth for current message
        depths[uuid] = depth

        # Recursively process children
        children = self.dependency_map[uuid]["children"]
        for child_uuid in children:
            self._calculate_depth_recursive(child_uuid, depth + 1, depths)
