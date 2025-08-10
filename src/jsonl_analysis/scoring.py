"""Importance scoring algorithm for JSONL messages.

Following TDD methodology - implementation based on test requirements.
"""

import logging
import re
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from .constants import (
    BASH_TOOL_SCORE,
    CHAIN_LENGTH_MULTIPLIER,
    CONVERSATION_CHAIN_BOOST,
    CONVERSATION_CONCLUSION_BOOST,
    CONVERSATION_ROOT_BOOST,
    DEFAULT_ARCHITECTURAL_DECISION_WEIGHT,
    DEFAULT_CODE_CHANGES_WEIGHT,
    DEFAULT_DEBUGGING_INFO_WEIGHT,
    DEFAULT_ERROR_SOLUTION_WEIGHT,
    DEFAULT_FILE_MODIFICATION_WEIGHT,
    DEFAULT_TOOL_SCORE,
    DEFAULT_USER_QUESTION_WEIGHT,
    EDIT_TOOL_SCORE,
    EMPTY_OUTPUT_PENALTY,
    GLOB_TOOL_SCORE,
    GREP_TOOL_SCORE,
    HAS_CHILDREN_BOOST,
    HIGH_VALUE_THRESHOLD,
    HOOK_LOG_PENALTY,
    IS_ROOT_BOOST,
    LOW_VALUE_THRESHOLD,
    MAX_DEPENDENCY_CHAIN_BONUS,
    MIN_CHAIN_DEPTH_FOR_CONCLUSION,
    MULTIEDIT_TOOL_SCORE,
    READ_TOOL_SCORE,
    RECENT_CHILD_BONUS,
    RECENT_CHILD_DAYS_THRESHOLD,
    RESULT_TRUNCATE_LENGTH,
    SYSTEM_VALIDATION_PENALTY,
    TODO_WRITE_SCORE,
    TOOL_SEQUENCE_PROXIMITY_THRESHOLD,
    WRITE_TOOL_SCORE,
)

logger = logging.getLogger(__name__)


class ImportanceScorer:
    """Calculates importance scores for JSONL messages using weighted criteria."""

    def __init__(
        self,
        weights: dict[str, int] | None = None,
        *,
        consider_dependencies: bool = True,
    ) -> None:
        """Initialize scorer with importance weights.

        Args:
            weights: Custom weight configuration for scoring criteria
            consider_dependencies: Whether to boost scores for messages with
                parent-child relationships

        """
        # Default weights from PRP specification
        self.weights = weights or {
            "code_changes": DEFAULT_CODE_CHANGES_WEIGHT,
            "error_solution": DEFAULT_ERROR_SOLUTION_WEIGHT,
            "architectural_decision": DEFAULT_ARCHITECTURAL_DECISION_WEIGHT,
            "user_question": DEFAULT_USER_QUESTION_WEIGHT,
            "file_modification": DEFAULT_FILE_MODIFICATION_WEIGHT,
            "debugging_info": DEFAULT_DEBUGGING_INFO_WEIGHT,
            "hook_log": HOOK_LOG_PENALTY,
            "system_validation": SYSTEM_VALIDATION_PENALTY,
            "empty_output": EMPTY_OUTPUT_PENALTY,
            "conversation_root": CONVERSATION_ROOT_BOOST,
            "conversation_chain": CONVERSATION_CHAIN_BOOST,
            "conversation_conclusion": CONVERSATION_CONCLUSION_BOOST,
        }

        # Dependency scoring configuration
        self.consider_dependencies = consider_dependencies
        self.dependency_weights = {
            "has_children": HAS_CHILDREN_BOOST,
            "is_root": IS_ROOT_BOOST,
            "chain_length_multiplier": CHAIN_LENGTH_MULTIPLIER,
            "recent_child_bonus": RECENT_CHILD_BONUS,
        }

        # Conversation context tracking
        self.conversation_graph: dict[str, Any] | None = None
        self.message_relationships: dict[str, dict[str, Any]] = {}

        # Compile regex patterns for performance
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficient pattern matching."""
        self.patterns = {
            # Code change patterns
            "code_changes": [
                re.compile(
                    r"\b(edit|write|create|implement|add|update|modify|delete|refactor)\b.*\.(py|js|ts|rs|go|java|cpp|c|h|php|rb|swift)",
                    re.IGNORECASE,
                ),
                re.compile(
                    r"\b(def|function|class|interface|struct|enum)\s+\w+",
                    re.IGNORECASE,
                ),
                re.compile(r"\b(import|from|require|include|using)\b", re.IGNORECASE),
                re.compile(
                    r"\b(edit|write|create|implement)\s+(file|function|class|method)",
                    re.IGNORECASE,
                ),
                re.compile(
                    r"\b(implement|create|build|develop)\b.*\b(system|feature|component|module|application|service)",
                    re.IGNORECASE,
                ),
            ],
            # Error/solution patterns
            "error_solution": [
                re.compile(
                    r"\b(error|exception|traceback|stack\s+trace|failed|failure|bug|critical|fatal)\b",
                    re.IGNORECASE,
                ),
                re.compile(
                    r"\b(fix|fixed|resolve|resolved|solution|debug|debugging|patch)\b",
                    re.IGNORECASE,
                ),
                re.compile(r"\b\w*Error\b|\b\w*Exception\b", re.IGNORECASE),
                re.compile(
                    r"\b(nameerror|typeerror|indexerror|attributeerror|valueerror)\b",
                    re.IGNORECASE,
                ),
            ],
            # Architectural decision patterns
            "architectural_decision": [
                re.compile(
                    r"\b(architecture|design|pattern|framework|approach|strategy)\b",
                    re.IGNORECASE,
                ),
                re.compile(
                    r"\b(decided|decision|choice|chose|select|selected)\b",
                    re.IGNORECASE,
                ),
                re.compile(
                    r"\b(microservices|monolith|database|api|rest|graphql)\b",
                    re.IGNORECASE,
                ),
                re.compile(
                    r"\b(factory|singleton|observer|strategy|builder|decorator)\s+pattern\b",
                    re.IGNORECASE,
                ),
            ],
            # User question patterns
            "user_question": [
                re.compile(
                    r"\b(how|what|why|when|where|which|can\s+you|could\s+you|help|assist)\b",
                    re.IGNORECASE,
                ),
                re.compile(r"\?", re.IGNORECASE),
                re.compile(
                    r"\b(explain|show|teach|guide|recommend|suggest)\b", re.IGNORECASE,
                ),
            ],
            # File modification patterns
            "file_modification": [
                re.compile(
                    r"\b(read|reading|examine|analyzing|check|review)\b.*\.(py|js|ts|rs|go|java|cpp|c|h|php|rb|swift|md|txt|json|yaml|yml)",
                    re.IGNORECASE,
                ),
                re.compile(r"\b(file|directory|folder|path|document)\b", re.IGNORECASE),
                re.compile(r"\b(structure|organization|layout)\b", re.IGNORECASE),
            ],
            # Debugging patterns
            "debugging_info": [
                re.compile(
                    r"\b(debug|debugging|investigate|analyze|trace|step|breakpoint)\b",
                    re.IGNORECASE,
                ),
                re.compile(
                    r"\b(print|log|console|output|stdout|stderr)\b", re.IGNORECASE,
                ),
                re.compile(
                    r"\b(test|testing|verify|validation|check)\b", re.IGNORECASE,
                ),
            ],
            # Hook system patterns
            "hook_log": [
                re.compile(r"\bhook\b:?\s*\w+", re.IGNORECASE),
                re.compile(r"\[hook\]", re.IGNORECASE),
                re.compile(
                    r"\b(pre_tool|post_tool|context|memory|auto).*\b(hook|executed|completed)",
                    re.IGNORECASE,
                ),
                re.compile(
                    r"\b(optimization|validation).*\b(hook|completed|executed)",
                    re.IGNORECASE,
                ),
            ],
            # System validation patterns
            "system_validation": [
                re.compile(
                    r"\b(validated|validation|check\s+passed|syntax\s+check|permissions|health\s+check)\b",
                    re.IGNORECASE,
                ),
                re.compile(
                    r"\b(dependencies.*up\s+to\s+date|configuration.*validated|systems.*operational)\b",
                    re.IGNORECASE,
                ),
                re.compile(
                    r"\b(ready|online|started|running|operational)\b", re.IGNORECASE,
                ),
            ],
            # Empty output patterns
            "empty_output": [
                re.compile(r"^\s*$"),  # Empty or whitespace only
                re.compile(
                    r"^\s*(ok|done|success|completed|acknowledged|confirmed|received)\s*$",
                    re.IGNORECASE,
                ),
                re.compile(r"^\s*[-_.]\s*$"),  # Single punctuation
            ],
        }

        # Tool-specific scoring
        self.tool_scores = {
            "Write": WRITE_TOOL_SCORE,
            "Edit": EDIT_TOOL_SCORE,
            "MultiEdit": MULTIEDIT_TOOL_SCORE,
            "Read": READ_TOOL_SCORE,
            "Glob": GLOB_TOOL_SCORE,
            "Grep": GREP_TOOL_SCORE,
            "Bash": BASH_TOOL_SCORE,
            "TodoWrite": TODO_WRITE_SCORE,
        }

    def build_conversation_context(self, messages: list[dict[str, Any]]) -> None:
        """Build conversation context graph for dependency-aware scoring.

        Args:
            messages: List of all messages in the conversation

        """
        self.message_relationships.clear()
        self._initialize_message_relationships(messages)
        self._build_children_relationships()
        self._calculate_chain_depths()
        self._mark_recent_children()
        self._log_context_stats()

    def _initialize_message_relationships(self, messages: list[dict[str, Any]]) -> None:
        """Initialize message relationships from messages."""
        for message in messages:
            uuid = message.get("uuid", "")
            parent_uuid = message.get("parentUuid")

            if uuid:
                self.message_relationships[uuid] = {
                    "parent_uuid": parent_uuid,
                    "children_uuids": set(),
                    "is_root": parent_uuid is None,
                    "chain_depth": 0,
                    "message_type": message.get("type", ""),
                    "timestamp": message.get("timestamp", ""),
                    "has_recent_children": False,
                }

    def _build_children_relationships(self) -> None:
        """Build children relationships from parent-child data."""
        for uuid, relationship in self.message_relationships.items():
            parent_uuid = relationship["parent_uuid"]
            if parent_uuid and parent_uuid in self.message_relationships:
                self.message_relationships[parent_uuid]["children_uuids"].add(uuid)

    def _calculate_chain_depths(self) -> None:
        """Calculate chain depths (distance from root) for all messages."""
        def calculate_depth(uuid: str, current_depth: int = 0) -> None:
            self._set_depth_for_node(uuid, current_depth)
            self._propagate_depth_to_children(uuid, current_depth)

        # Calculate depths from all root nodes
        self._process_root_nodes(calculate_depth)

    def _set_depth_for_node(self, uuid: str, current_depth: int) -> None:
        """Set the chain depth for a specific node."""
        if uuid in self.message_relationships:
            self.message_relationships[uuid]["chain_depth"] = current_depth

    def _propagate_depth_to_children(self, uuid: str, current_depth: int) -> None:
        """Propagate depth calculation to all children nodes."""
        if uuid not in self.message_relationships:
            return

        for child_uuid in self.message_relationships[uuid]["children_uuids"]:
            self._calculate_child_depth(child_uuid, current_depth + 1)

    def _calculate_child_depth(self, child_uuid: str, depth: int) -> None:
        """Calculate depth for a child node recursively."""
        self._set_depth_for_node(child_uuid, depth)
        self._propagate_depth_to_children(child_uuid, depth)

    def _process_root_nodes(
        self, calculate_depth_fn: Callable[[str, int], None],
    ) -> None:
        """Process all root nodes for depth calculation."""
        for uuid, relationship in self.message_relationships.items():
            if relationship["is_root"]:
                calculate_depth_fn(uuid, 0)

    def _mark_recent_children(self) -> None:
        """Mark messages that have recent children."""
        now = datetime.now(UTC)
        recent_threshold = now - timedelta(days=RECENT_CHILD_DAYS_THRESHOLD)

        for relationship in self.message_relationships.values():
            for child_uuid in relationship["children_uuids"]:
                child_relationship = self.message_relationships.get(child_uuid, {})
                child_timestamp = child_relationship.get("timestamp", "")
                if self._is_timestamp_recent(child_timestamp, recent_threshold):
                    relationship["has_recent_children"] = True
                    break

    def _is_timestamp_recent(self, timestamp: str, threshold: datetime) -> bool:
        """Check if timestamp is more recent than threshold."""
        if not timestamp:
            return False
        try:
            child_time = datetime.fromisoformat(timestamp)
        except (ValueError, TypeError):
            return False
        else:
            return child_time > threshold

    def _log_context_stats(self) -> None:
        """Log statistics about the built conversation context."""
        root_count = sum(1 for r in self.message_relationships.values() if r["is_root"])
        logger.info(
            "📊 Built conversation context: %d messages, %d roots",
            len(self.message_relationships),
            root_count,
        )

    def calculate_message_importance(self, message: dict[str, Any]) -> float:
        """Calculate importance score for a single message.

        Args:
            message: Message dictionary to score

        Returns:
            Importance score between 0-100

        """
        try:
            score = 0

            # Extract content for analysis
            content = self._extract_message_content(message)
            message_type = message.get("type", "")

            # Apply pattern-based scoring
            score += self._score_content_patterns(content)

            # Apply message type specific scoring
            score += self._score_message_type(message_type, content)

            # Apply tool-specific scoring
            score += self._score_tool_usage(message)

            # Apply dependency-aware scoring
            if self.consider_dependencies:
                score += self._score_conversation_dependencies(message)

            # Ensure score is within bounds [0, 100]
            return max(0.0, min(100.0, float(score)))

        except (ValueError, TypeError, AttributeError, KeyError) as e:
            logger.warning("Error calculating importance score: %s", e)
            return 0  # Return neutral score on error

    def _extract_message_content(self, message: dict[str, Any]) -> str:
        """Extract textual content from message for analysis."""
        if "message" not in message:
            return ""

        msg_content = message["message"]
        content_parts = self._process_message_content(msg_content)
        return " ".join(content_parts)

    def _process_message_content(
        self, msg_content: dict[str, Any] | str,
    ) -> list[str]:
        """Process message content based on its type."""
        if isinstance(msg_content, dict):
            return self._extract_dict_content(msg_content)
        return [str(msg_content)]

    def _extract_dict_content(self, msg_content: dict[str, Any]) -> list[str]:
        """Extract content from dictionary message."""
        content_parts = []

        content_parts.extend(self._extract_basic_content(msg_content))
        content_parts.extend(self._extract_tool_content(msg_content))
        content_parts.extend(self._extract_parameters_content(msg_content))
        content_parts.extend(self._extract_result_content(msg_content))

        return content_parts

    def _extract_basic_content(self, msg_content: dict[str, Any]) -> list[str]:
        """Extract basic content field."""
        if msg_content.get("content"):
            return [str(msg_content["content"])]
        return []

    def _extract_tool_content(self, msg_content: dict[str, Any]) -> list[str]:
        """Extract tool information."""
        if "tool" in msg_content:
            return [f"Tool: {msg_content['tool']}"]
        return []

    def _extract_parameters_content(self, msg_content: dict[str, Any]) -> list[str]:
        """Extract parameters content."""
        if "parameters" not in msg_content:
            return []

        params = msg_content["parameters"]
        if isinstance(params, dict):
            return [str(v) for v in params.values() if v]
        return []

    def _extract_result_content(self, msg_content: dict[str, Any]) -> list[str]:
        """Extract and truncate result content."""
        if not msg_content.get("result"):
            return []

        result = str(msg_content["result"])
        if len(result) > RESULT_TRUNCATE_LENGTH:
            result = result[:RESULT_TRUNCATE_LENGTH] + "..."
        return [result]

    def _score_content_patterns(self, content: str) -> int:
        """Score content based on pattern matching."""
        score = 0

        for pattern_type, patterns in self.patterns.items():
            if self._matches_patterns(content, patterns):
                weight = self.weights.get(pattern_type, 0)
                score += weight

        return score

    def _matches_patterns(self, content: str, patterns: list[re.Pattern]) -> bool:
        """Check if content matches any of the given patterns."""
        if not content:
            # Special case for empty content
            return patterns == self.patterns["empty_output"]

        return any(pattern.search(content) for pattern in patterns)

    def _score_message_type(self, message_type: str, content: str) -> int:
        """Apply scoring based on message type."""
        score = 0

        # User questions get importance boost
        if (message_type == "user" and
                self._matches_patterns(content, self.patterns["user_question"])):
                score += 5  # Additional boost for actual questions

        return score

    def _score_tool_usage(self, message: dict[str, Any]) -> int:
        """Score based on tool usage patterns."""
        if message.get("type") != "tool_call":
            return 0

        tool_name = message.get("message", {}).get("tool")
        if not tool_name:
            return 0

        # Apply tool-specific scoring
        return self.tool_scores.get(tool_name, DEFAULT_TOOL_SCORE)

    def _score_conversation_dependencies(self, message: dict[str, Any]) -> int:
        """Score message based on its role in conversation dependencies.

        Args:
            message: Message to score based on conversation context

        Returns:
            Additional score points based on conversation dependencies

        """
        uuid = message.get("uuid", "")
        if not uuid or uuid not in self.message_relationships:
            return 0

        relationship = self.message_relationships[uuid]
        score = 0

        # Apply individual scoring strategies
        score += self._score_root_message(relationship)
        score += self._score_children_relationships(relationship)
        score += self._score_chain_depth(relationship)
        score += self._score_conversation_conclusion(relationship)

        logger.debug(
            "Dependency score for %s: +%d (root: %s, children: %d, depth: %d)",
            uuid,
            score,
            relationship["is_root"],
            len(relationship["children_uuids"]),
            relationship["chain_depth"],
        )

        return score

    def _score_root_message(self, relationship: dict[str, Any]) -> int:
        """Score bonus for root messages (conversation starters)."""
        if not relationship["is_root"]:
            return 0
        return (
            self.dependency_weights["is_root"]
            + self.weights.get("conversation_root", 0)
        )

    def _score_children_relationships(self, relationship: dict[str, Any]) -> int:
        """Score bonus for messages with children and recent activity."""
        if not relationship["children_uuids"]:
            return 0

        score = (
            self.dependency_weights["has_children"]
            + self.weights.get("conversation_chain", 0)
        )

        # Extra bonus if children are recent (within 7 days)
        if relationship["has_recent_children"]:
            score += self.dependency_weights["recent_child_bonus"]

        return score

    def _score_chain_depth(self, relationship: dict[str, Any]) -> int:
        """Score bonus based on conversation chain depth."""
        chain_depth = relationship["chain_depth"]
        if chain_depth <= 0:
            return 0

        # Moderate bonus for being part of a conversation chain
        return min(
            int(chain_depth * self.dependency_weights["chain_length_multiplier"]),
            MAX_DEPENDENCY_CHAIN_BONUS,
        )

    def _score_conversation_conclusion(self, relationship: dict[str, Any]) -> int:
        """Score bonus for conversation conclusions (leaf nodes in deep chains)."""
        # Check if this is a leaf node (no children)
        if relationship["children_uuids"] != set():
            return 0

        # Only award bonus for conclusions in deeper conversations
        if relationship["chain_depth"] > MIN_CHAIN_DEPTH_FOR_CONCLUSION:
            return self.weights.get("conversation_conclusion", 0)

        return 0

    def set_temporal_decay(self, *, enabled: bool, mode: str = "simple") -> None:
        """Stub method for backwards compatibility. Does nothing."""

    def get_temporal_stats(self) -> dict[str, Any] | None:
        """Stub method for backwards compatibility. Returns None."""
        return None

    def reset_temporal_stats(self) -> None:
        """Stub method for backwards compatibility. Does nothing."""

    def get_dependency_statistics(self) -> dict[str, Any]:
        """Get statistics about conversation dependencies.

        Returns:
            Dictionary with dependency statistics

        """
        if not self.message_relationships:
            return {
                "error": (
                    "No conversation context built. "
                    "Call build_conversation_context() first."
                ),
            }

        stats = {
            "total_messages": len(self.message_relationships),
            "root_messages": sum(
                1 for r in self.message_relationships.values() if r["is_root"]
            ),
            "messages_with_children": sum(
                1 for r in self.message_relationships.values() if r["children_uuids"]
            ),
            "messages_with_recent_children": sum(
                1
                for r in self.message_relationships.values()
                if r["has_recent_children"]
            ),
            "average_chain_depth": 0,
            "max_chain_depth": 0,
            "conversation_chains": 0,
        }

        if stats["total_messages"] > 0:
            depths = [r["chain_depth"] for r in self.message_relationships.values()]
            stats["average_chain_depth"] = sum(depths) / len(depths)
            stats["max_chain_depth"] = max(depths)

            # Count distinct conversation chains (count root messages)
            stats["conversation_chains"] = stats["root_messages"]

        return stats

    def score_messages_with_context(
        self, messages: list[dict[str, Any]],
    ) -> list[tuple[str, float]]:
        """Score multiple messages with full conversation context.

        Args:
            messages: List of messages to score

        Returns:
            List of (uuid, score) tuples

        """
        if self.consider_dependencies:
            self.build_conversation_context(messages)

        scored_messages = []
        for message in messages:
            uuid = message.get("uuid", "")
            score = self.calculate_message_importance(message)
            scored_messages.append((uuid, score))

        return scored_messages

    def extract_message_content_public(self, message: dict[str, Any]) -> str:
        """Public method to extract message content for external access."""
        return self._extract_message_content(message)

    def matches_patterns_public(self, content: str, patterns: list[re.Pattern]) -> bool:
        """Public method to match patterns for external access."""
        return self._matches_patterns(content, patterns)


class MessageScoreAnalyzer:
    """Analyzes importance score distributions and conversation patterns."""

    def __init__(self, scorer: ImportanceScorer | None = None) -> None:
        """Initialize analyzer with optional custom scorer.

        Args:
            scorer: Custom importance scorer instance

        """
        self.scorer = scorer or ImportanceScorer()

    def analyze_score_distribution(
        self,
        messages: list[dict[str, Any]],
        *,
        include_dependencies: bool = True,
    ) -> dict[str, Any]:
        """Analyze distribution of importance scores across messages.

        Args:
            messages: List of messages to analyze
            include_dependencies: Whether to include dependency scoring

        Returns:
            Dictionary with score distribution categories and dependency stats

        """
        self._prepare_scoring_context(
            messages, include_dependencies=include_dependencies,
        )

        distribution, scores = self._calculate_score_distribution(messages)

        result = self._build_distribution_result(distribution, scores, len(messages))

        if include_dependencies and self.scorer.consider_dependencies:
            result["dependency_stats"] = self.scorer.get_dependency_statistics()

        return result

    def _prepare_scoring_context(
        self,
        messages: list[dict[str, Any]],
        *,
        include_dependencies: bool,
    ) -> None:
        """Prepare scoring context if dependency scoring is enabled."""
        if include_dependencies and self.scorer.consider_dependencies:
            self.scorer.build_conversation_context(messages)

    def _calculate_score_distribution(
        self, messages: list[dict[str, Any]],
    ) -> tuple[dict[str, int], list[float]]:
        """Calculate score distribution across all messages."""
        distribution = {"high": 0, "medium": 0, "low": 0}
        scores = []

        for message in messages:
            score = self.scorer.calculate_message_importance(message)
            scores.append(float(score))
            self._categorize_score(score, distribution)

        return distribution, scores

    def _categorize_score(self, score: float, distribution: dict[str, int]) -> None:
        """Categorize a single score into high/medium/low."""
        if score >= HIGH_VALUE_THRESHOLD:
            distribution["high"] += 1
        elif score >= LOW_VALUE_THRESHOLD:
            distribution["medium"] += 1
        else:
            distribution["low"] += 1

    def _build_distribution_result(
        self, distribution: dict[str, int], scores: list[float], total_messages: int,
    ) -> dict[str, Any]:
        """Build the final distribution result dictionary."""
        return {
            "distribution": distribution,
            "total_messages": total_messages,
            "average_score": sum(scores) / len(scores) if scores else 0,
            "score_range": (
                {"min": min(scores), "max": max(scores)}
                if scores
                else {"min": 0, "max": 0}
            ),
        }

    def identify_important_patterns(
        self, messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Identify important conversation patterns and sequences.

        Args:
            messages: List of messages to analyze

        Returns:
            Dictionary with identified patterns

        """
        patterns: dict[str, list[Any]] = {
            "error_solution_pairs": [],
            "tool_sequences": [],
            "code_modification_chains": [],
        }

        patterns["error_solution_pairs"] = self._find_error_solution_pairs(messages)
        patterns["tool_sequences"] = self._find_tool_sequences(messages)
        patterns["code_modification_chains"] = self._find_code_modification_chains(
            messages,
        )

        return patterns

    def _find_error_solution_pairs(
        self, messages: list[dict[str, Any]],
    ) -> list[tuple[int, int]]:
        """Find error-solution pairs in messages."""
        pairs = []
        for i, message in enumerate(messages):
            content = self.scorer.extract_message_content_public(message)

            # Look for error followed by solution
            if self.scorer.matches_patterns_public(
                content, self.scorer.patterns["error_solution"],
            ):
                # Check next few messages for solutions
                for j in range(i + 1, min(i + 4, len(messages))):
                    next_content = self.scorer.extract_message_content_public(
                        messages[j],
                    )
                    if self.scorer.matches_patterns_public(
                        next_content, self.scorer.patterns["error_solution"],
                    ):
                        pairs.append((i, j))
                        break
        return pairs

    def _find_tool_sequences(
        self, messages: list[dict[str, Any]],
    ) -> list[list[tuple[int, str]]]:
        """Find tool call sequences in messages."""
        tool_calls = self._extract_tool_calls(messages)
        if len(tool_calls) <= 1:
            return []

        return self._group_tool_calls(tool_calls)

    def _extract_tool_calls(
        self, messages: list[dict[str, Any]],
    ) -> list[tuple[int, str]]:
        """Extract tool calls from messages."""
        tool_calls = []
        for i, message in enumerate(messages):
            if message.get("type") == "tool_call":
                tool_name = message.get("message", {}).get("tool")
                if tool_name:
                    tool_calls.append((i, tool_name))
        return tool_calls

    def _group_tool_calls(
        self, tool_calls: list[tuple[int, str]],
    ) -> list[list[tuple[int, str]]]:
        """Group tool calls into sequences based on proximity."""
        sequences = []
        current_sequence = [tool_calls[0]]

        for i in range(1, len(tool_calls)):
            prev_index, _ = tool_calls[i - 1]
            curr_index, curr_tool = tool_calls[i]

            # If tools are within proximity threshold, consider them a sequence
            if curr_index - prev_index <= TOOL_SEQUENCE_PROXIMITY_THRESHOLD:
                current_sequence.append((curr_index, curr_tool))
            else:
                # End current sequence and start new one
                if len(current_sequence) > 1:
                    sequences.append(current_sequence[:])
                current_sequence = [(curr_index, curr_tool)]

        # Add final sequence if it has multiple tools
        if len(current_sequence) > 1:
            sequences.append(current_sequence)

        return sequences

    def _find_code_modification_chains(
        self, messages: list[dict[str, Any]],
    ) -> list[int]:
        """Find code modification chains in messages."""
        chains = []
        for i, message in enumerate(messages):
            content = self.scorer.extract_message_content_public(message)
            if self.scorer.matches_patterns_public(
                content, self.scorer.patterns["code_changes"],
            ):
                chains.append(i)
        return chains

    def calculate_conversation_value(
        self,
        messages: list[dict[str, Any]],
        *,
        include_dependencies: bool = True,
    ) -> dict[str, Any]:
        """Calculate overall value metrics for conversation.

        Args:
            messages: List of messages to analyze
            include_dependencies: Whether to include dependency-aware scoring

        Returns:
            Dictionary with conversation value metrics

        """
        if not messages:
            return {
                "total_score": 0,
                "average_score": 0,
                "high_value_ratio": 0,
                "low_value_ratio": 0,
            }

        # Build context if dependency scoring is enabled
        if include_dependencies and self.scorer.consider_dependencies:
            self.scorer.build_conversation_context(messages)

        scores = [self.scorer.calculate_message_importance(msg) for msg in messages]
        high_value_count = sum(1 for score in scores if score >= HIGH_VALUE_THRESHOLD)
        low_value_count = sum(1 for score in scores if score < LOW_VALUE_THRESHOLD)

        metrics = {
            "total_score": sum(scores),
            "average_score": sum(scores) / len(scores),
            "high_value_ratio": high_value_count / len(messages),
            "low_value_ratio": low_value_count / len(messages),
            "score_statistics": {
                "min": min(scores),
                "max": max(scores),
                "median": sorted(scores)[len(scores) // 2] if scores else 0,
            },
        }

        # Add dependency metrics if available
        if include_dependencies and self.scorer.consider_dependencies:
            dependency_stats = self.scorer.get_dependency_statistics()
            metrics["conversation_structure"] = {
                "conversation_chains": dependency_stats.get("conversation_chains", 0),
                "messages_with_children": dependency_stats.get(
                    "messages_with_children", 0,
                ),
                "messages_with_recent_children": dependency_stats.get(
                    "messages_with_recent_children", 0,
                ),
                "max_chain_depth": dependency_stats.get("max_chain_depth", 0),
            }

        return metrics

    def recommend_analysis_threshold(
        self, messages: list[dict[str, Any]], target_focus: float = 0.5,
    ) -> dict[str, Any]:
        """Recommend optimal analysis threshold to achieve target focus.

        Args:
            messages: List of messages to analyze
            target_focus: Target percentage of messages to focus on (0.0-1.0)

        Returns:
            Dictionary with threshold recommendation

        """
        if not messages:
            return {
                "threshold": 0,
                "predicted_focus": 0,
                "high_importance_messages": 0,
                "low_importance_messages": 0,
            }

        # Calculate scores for all messages
        scores = [self.scorer.calculate_message_importance(msg) for msg in messages]
        sorted_scores = sorted(scores, reverse=True)

        # Find threshold that achieves target focus
        target_focus_count = int(len(messages) * target_focus)
        if target_focus_count >= len(messages):
            threshold = 0.0
        elif target_focus_count == 0:
            threshold = 100.0
        else:
            threshold = float(sorted_scores[target_focus_count - 1])

        # Calculate actual focus with this threshold
        high_importance_count = sum(1 for score in scores if score >= threshold)
        low_importance_count = len(messages) - high_importance_count
        actual_focus = high_importance_count / len(messages) if messages else 0

        return {
            "threshold": threshold,
            "predicted_focus": actual_focus,
            "high_importance_messages": high_importance_count,
            "low_importance_messages": low_importance_count,
        }
