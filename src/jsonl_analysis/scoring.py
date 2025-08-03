"""
Importance scoring algorithm for JSONL messages
Following TDD methodology - implementation based on test requirements
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict, Counter

from .exceptions import InvalidMessageError
from ..temporal.decay_engine import ExponentialDecayEngine, DecayMode

logger = logging.getLogger(__name__)


class ImportanceScorer:
    """Calculates importance scores for JSONL messages using weighted criteria"""
    
    def __init__(self, weights: Optional[Dict[str, int]] = None, temporal_decay: bool = False, decay_mode: DecayMode = DecayMode.SIMPLE, 
                 consider_dependencies: bool = True):
        """
        Initialize scorer with importance weights
        
        Args:
            weights: Custom weight configuration for scoring criteria
            temporal_decay: Whether to apply temporal decay to scores
            decay_mode: Mode for temporal decay calculation
            consider_dependencies: Whether to boost scores for messages with parent-child relationships
        """
        # Default weights from PRP specification
        self.weights = weights or {
            "code_changes": 40,          # High importance
            "error_solution": 35,        # High importance
            "architectural_decision": 30, # High importance
            "user_question": 20,         # Medium importance
            "file_modification": 25,     # Medium importance
            "debugging_info": 15,        # Medium importance
            "hook_log": -30,             # Low importance penalty
            "system_validation": -25,    # Low importance penalty
            "empty_output": -20,         # Low importance penalty
            "conversation_root": 15,     # Boost for conversation starters
            "conversation_chain": 10,    # Boost for messages in conversation chains
            "conversation_conclusion": 8 # Boost for conversation endings
        }
        
        # Dependency scoring configuration
        self.consider_dependencies = consider_dependencies
        self.dependency_weights = {
            "has_children": 12,          # Boost for messages with children
            "is_root": 10,               # Boost for root messages (conversation starters)
            "chain_length_multiplier": 2, # Multiplier based on conversation chain length
            "recent_child_bonus": 15     # Extra boost if has recent children
        }
        
        # Initialize temporal decay engine if enabled
        self.temporal_decay_enabled = temporal_decay
        self.decay_engine = None
        if temporal_decay:
            self.decay_engine = ExponentialDecayEngine(mode=decay_mode)
            logger.info(f"Temporal decay enabled with mode: {decay_mode.value}")
        
        # Conversation context tracking
        self.conversation_graph: Optional[Dict[str, Any]] = None
        self.message_relationships: Dict[str, Dict[str, Any]] = {}
        
        # Compile regex patterns for performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient pattern matching"""
        self.patterns = {
            # Code change patterns
            "code_changes": [
                re.compile(r'\b(edit|write|create|implement|add|update|modify|delete|refactor)\b.*\.(py|js|ts|rs|go|java|cpp|c|h|php|rb|swift)', re.IGNORECASE),
                re.compile(r'\b(def|function|class|interface|struct|enum)\s+\w+', re.IGNORECASE),
                re.compile(r'\b(import|from|require|include|using)\b', re.IGNORECASE),
                re.compile(r'\b(edit|write|create|implement)\s+(file|function|class|method)', re.IGNORECASE),
                re.compile(r'\b(implement|create|build|develop)\b.*\b(system|feature|component|module|application|service)', re.IGNORECASE)
            ],
            
            # Error/solution patterns
            "error_solution": [
                re.compile(r'\b(error|exception|traceback|stack\s+trace|failed|failure|bug|critical|fatal)\b', re.IGNORECASE),
                re.compile(r'\b(fix|fixed|resolve|resolved|solution|debug|debugging|patch)\b', re.IGNORECASE),
                re.compile(r'\b\w*Error\b|\b\w*Exception\b', re.IGNORECASE),
                re.compile(r'\b(nameerror|typeerror|indexerror|attributeerror|valueerror)\b', re.IGNORECASE)
            ],
            
            # Architectural decision patterns
            "architectural_decision": [
                re.compile(r'\b(architecture|design|pattern|framework|approach|strategy)\b', re.IGNORECASE),
                re.compile(r'\b(decided|decision|choice|chose|select|selected)\b', re.IGNORECASE),
                re.compile(r'\b(microservices|monolith|database|api|rest|graphql)\b', re.IGNORECASE),
                re.compile(r'\b(factory|singleton|observer|strategy|builder|decorator)\s+pattern\b', re.IGNORECASE)
            ],
            
            # User question patterns
            "user_question": [
                re.compile(r'\b(how|what|why|when|where|which|can\s+you|could\s+you|help|assist)\b', re.IGNORECASE),
                re.compile(r'\?', re.IGNORECASE),
                re.compile(r'\b(explain|show|teach|guide|recommend|suggest)\b', re.IGNORECASE)
            ],
            
            # File modification patterns
            "file_modification": [
                re.compile(r'\b(read|reading|examine|analyzing|check|review)\b.*\.(py|js|ts|rs|go|java|cpp|c|h|php|rb|swift|md|txt|json|yaml|yml)', re.IGNORECASE),
                re.compile(r'\b(file|directory|folder|path|document)\b', re.IGNORECASE),
                re.compile(r'\b(structure|organization|layout)\b', re.IGNORECASE)
            ],
            
            # Debugging patterns
            "debugging_info": [
                re.compile(r'\b(debug|debugging|investigate|analyze|trace|step|breakpoint)\b', re.IGNORECASE),
                re.compile(r'\b(print|log|console|output|stdout|stderr)\b', re.IGNORECASE),
                re.compile(r'\b(test|testing|verify|validation|check)\b', re.IGNORECASE)
            ],
            
            # Hook system patterns
            "hook_log": [
                re.compile(r'\bhook\b:?\s*\w+', re.IGNORECASE),
                re.compile(r'\[hook\]', re.IGNORECASE),
                re.compile(r'\b(pre_tool|post_tool|context|memory|auto).*\b(hook|executed|completed)', re.IGNORECASE),
                re.compile(r'\b(optimization|pruning|validation).*\b(hook|completed|executed)', re.IGNORECASE)
            ],
            
            # System validation patterns
            "system_validation": [
                re.compile(r'\b(validated|validation|check\s+passed|syntax\s+check|permissions|health\s+check)\b', re.IGNORECASE),
                re.compile(r'\b(dependencies.*up\s+to\s+date|configuration.*validated|systems.*operational)\b', re.IGNORECASE),
                re.compile(r'\b(ready|online|started|running|operational)\b', re.IGNORECASE)
            ],
            
            # Empty output patterns
            "empty_output": [
                re.compile(r'^\s*$'),  # Empty or whitespace only
                re.compile(r'^\s*(ok|done|success|completed|acknowledged|confirmed|received)\s*$', re.IGNORECASE),
                re.compile(r'^\s*[-_.]\s*$')  # Single punctuation
            ]
        }
        
        # Tool-specific scoring
        self.tool_scores = {
            "Write": 40,      # File modification
            "Edit": 40,       # File modification
            "MultiEdit": 40,  # File modification
            "Read": 20,       # File reading
            "Glob": 15,       # File discovery
            "Grep": 20,       # Content search
            "Bash": 25,       # Command execution
            "TodoWrite": 5    # Todo management
        }
    
    def build_conversation_context(self, messages: List[Dict[str, Any]]) -> None:
        """
        Build conversation context graph for dependency-aware scoring.
        
        Args:
            messages: List of all messages in the conversation
        """
        self.message_relationships.clear()
        
        # Build parent-child relationships
        for message in messages:
            uuid = message.get('uuid', '')
            parent_uuid = message.get('parentUuid')
            
            if uuid:
                self.message_relationships[uuid] = {
                    'parent_uuid': parent_uuid,
                    'children_uuids': set(),
                    'is_root': parent_uuid is None,
                    'chain_depth': 0,
                    'message_type': message.get('type', ''),
                    'timestamp': message.get('timestamp', ''),
                    'has_recent_children': False
                }
        
        # Build children relationships and calculate chain depths
        for uuid, relationship in self.message_relationships.items():
            parent_uuid = relationship['parent_uuid']
            if parent_uuid and parent_uuid in self.message_relationships:
                self.message_relationships[parent_uuid]['children_uuids'].add(uuid)
        
        # Calculate chain depths (distance from root)
        def calculate_depth(uuid: str, current_depth: int = 0) -> None:
            if uuid in self.message_relationships:
                self.message_relationships[uuid]['chain_depth'] = current_depth
                for child_uuid in self.message_relationships[uuid]['children_uuids']:
                    calculate_depth(child_uuid, current_depth + 1)
        
        # Calculate depths from all root nodes
        for uuid, relationship in self.message_relationships.items():
            if relationship['is_root']:
                calculate_depth(uuid, 0)
        
        # Check for recent children (within last 7 days)
        from datetime import datetime, timedelta
        now = datetime.now()
        recent_threshold = now - timedelta(days=7)
        
        for uuid, relationship in self.message_relationships.items():
            for child_uuid in relationship['children_uuids']:
                child_relationship = self.message_relationships.get(child_uuid, {})
                child_timestamp = child_relationship.get('timestamp', '')
                if child_timestamp:
                    try:
                        child_time = datetime.fromisoformat(child_timestamp.replace('Z', '+00:00'))
                        if child_time > recent_threshold:
                            relationship['has_recent_children'] = True
                            break
                    except (ValueError, TypeError):
                        continue
        
        logger.info(f"📊 Built conversation context: {len(self.message_relationships)} messages, "
                   f"{sum(1 for r in self.message_relationships.values() if r['is_root'])} roots")
    
    def calculate_message_importance(self, message: Dict[str, Any], apply_temporal_decay: bool = True) -> float:
        """
        Calculate importance score for a single message
        
        Args:
            message: Message dictionary to score
            apply_temporal_decay: Whether to apply temporal decay (if enabled)
            
        Returns:
            Importance score between 0-100 (float with temporal decay)
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
            
            # Apply temporal decay if enabled
            if self.temporal_decay_enabled and apply_temporal_decay and self.decay_engine:
                decay_factor = self.decay_engine.calculate_decay_factor(message)
                score = score * decay_factor
                logger.debug(f"Applied temporal decay factor {decay_factor:.3f} to message with score {score:.1f}")
            
            # Ensure score is within bounds [0, 100]
            return max(0.0, min(100.0, float(score)))
            
        except Exception as e:
            logger.warning(f"Error calculating importance score: {e}")
            return 0  # Return neutral score on error
    
    def _extract_message_content(self, message: Dict[str, Any]) -> str:
        """Extract textual content from message for analysis"""
        content_parts = []
        
        # Get main content
        if "message" in message:
            msg_content = message["message"]
            if isinstance(msg_content, dict):
                # Extract content field
                if "content" in msg_content and msg_content["content"]:
                    content_parts.append(str(msg_content["content"]))
                
                # Extract tool information
                if "tool" in msg_content:
                    content_parts.append(f"Tool: {msg_content['tool']}")
                
                # Extract parameters
                if "parameters" in msg_content:
                    params = msg_content["parameters"]
                    if isinstance(params, dict):
                        content_parts.extend(str(v) for v in params.values() if v)
                
                # Extract result
                if "result" in msg_content and msg_content["result"]:
                    result = str(msg_content["result"])
                    # Limit result length to avoid skewing scores
                    if len(result) > 500:
                        result = result[:500] + "..."
                    content_parts.append(result)
            else:
                content_parts.append(str(msg_content))
        
        return " ".join(content_parts)
    
    def _score_content_patterns(self, content: str) -> int:
        """Score content based on pattern matching"""
        score = 0
        
        for pattern_type, patterns in self.patterns.items():
            if self._matches_patterns(content, patterns):
                weight = self.weights.get(pattern_type, 0)
                score += weight
        
        return score
    
    def _matches_patterns(self, content: str, patterns: List[re.Pattern]) -> bool:
        """Check if content matches any of the given patterns"""
        if not content:
            # Special case for empty content
            return patterns == self.patterns["empty_output"]
        
        for pattern in patterns:
            if pattern.search(content):
                return True
        return False
    
    def _score_message_type(self, message_type: str, content: str) -> int:
        """Apply scoring based on message type"""
        score = 0
        
        # User questions get importance boost
        if message_type == "user":
            # Check if it's actually a question
            if self._matches_patterns(content, self.patterns["user_question"]):
                score += 5  # Additional boost for actual questions
        
        return score
    
    def _score_tool_usage(self, message: Dict[str, Any]) -> int:
        """Score based on tool usage patterns"""
        if message.get("type") != "tool_call":
            return 0
        
        tool_name = message.get("message", {}).get("tool")
        if not tool_name:
            return 0
        
        # Apply tool-specific scoring
        return self.tool_scores.get(tool_name, 10)  # Default score for unknown tools
    
    def _score_conversation_dependencies(self, message: Dict[str, Any]) -> int:
        """
        Score message based on its role in conversation dependencies.
        
        Args:
            message: Message to score based on conversation context
            
        Returns:
            Additional score points based on conversation dependencies
        """
        uuid = message.get('uuid', '')
        if not uuid or uuid not in self.message_relationships:
            return 0
        
        relationship = self.message_relationships[uuid]
        score = 0
        
        # Root message bonus (conversation starters are important)
        if relationship['is_root']:
            score += self.dependency_weights['is_root']
            score += self.weights.get('conversation_root', 0)
        
        # Has children bonus (important if other messages depend on this one)
        if relationship['children_uuids']:
            score += self.dependency_weights['has_children']
            score += self.weights.get('conversation_chain', 0)
            
            # Extra bonus if children are recent (within 7 days)
            if relationship['has_recent_children']:
                score += self.dependency_weights['recent_child_bonus']
        
        # Chain depth bonus (deeper conversations may be more valuable)
        chain_depth = relationship['chain_depth']
        if chain_depth > 0:
            # Moderate bonus for being part of a conversation chain
            chain_bonus = min(chain_depth * self.dependency_weights['chain_length_multiplier'], 20)
            score += chain_bonus
        
        # Conversation conclusion bonus (last messages in chains can be important)
        if relationship['children_uuids'] == set():  # Leaf node
            if chain_depth > 2:  # Only if it's part of a substantial conversation
                score += self.weights.get('conversation_conclusion', 0)
        
        logger.debug(f"Dependency score for {uuid}: +{score} (root: {relationship['is_root']}, "
                    f"children: {len(relationship['children_uuids'])}, depth: {chain_depth})")
        
        return score
    
    def set_temporal_decay(self, enabled: bool, mode: DecayMode = DecayMode.SIMPLE):
        """Enable or disable temporal decay scoring."""
        self.temporal_decay_enabled = enabled
        if enabled:
            self.decay_engine = ExponentialDecayEngine(mode=mode)
            logger.info(f"Temporal decay enabled with mode: {mode.value}")
        else:
            self.decay_engine = None
            logger.info("Temporal decay disabled")
    
    def get_temporal_stats(self) -> Optional[Dict[str, Any]]:
        """Get temporal decay statistics if decay is enabled."""
        if self.decay_engine:
            return self.decay_engine.get_statistics()
        return None
    
    def reset_temporal_stats(self):
        """Reset temporal decay statistics."""
        if self.decay_engine:
            self.decay_engine.reset_statistics()
    
    def get_dependency_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about conversation dependencies.
        
        Returns:
            Dictionary with dependency statistics
        """
        if not self.message_relationships:
            return {"error": "No conversation context built. Call build_conversation_context() first."}
        
        stats = {
            "total_messages": len(self.message_relationships),
            "root_messages": sum(1 for r in self.message_relationships.values() if r['is_root']),
            "messages_with_children": sum(1 for r in self.message_relationships.values() if r['children_uuids']),
            "messages_with_recent_children": sum(1 for r in self.message_relationships.values() if r['has_recent_children']),
            "average_chain_depth": 0,
            "max_chain_depth": 0,
            "conversation_chains": 0
        }
        
        if stats["total_messages"] > 0:
            depths = [r['chain_depth'] for r in self.message_relationships.values()]
            stats["average_chain_depth"] = sum(depths) / len(depths)
            stats["max_chain_depth"] = max(depths)
            
            # Count distinct conversation chains (count root messages)
            stats["conversation_chains"] = stats["root_messages"]
        
        return stats
    
    def score_messages_with_context(self, messages: List[Dict[str, Any]], 
                                   apply_temporal_decay: bool = True) -> List[Tuple[str, float]]:
        """
        Score multiple messages with full conversation context.
        
        Args:
            messages: List of messages to score
            apply_temporal_decay: Whether to apply temporal decay
            
        Returns:
            List of (uuid, score) tuples
        """
        if self.consider_dependencies:
            self.build_conversation_context(messages)
        
        scored_messages = []
        for message in messages:
            uuid = message.get('uuid', '')
            score = self.calculate_message_importance(message, apply_temporal_decay)
            scored_messages.append((uuid, score))
        
        return scored_messages


class MessageScoreAnalyzer:
    """Analyzes importance score distributions and conversation patterns"""
    
    def __init__(self, scorer: Optional[ImportanceScorer] = None):
        """
        Initialize analyzer with optional custom scorer
        
        Args:
            scorer: Custom importance scorer instance
        """
        self.scorer = scorer or ImportanceScorer()
    
    def analyze_score_distribution(self, messages: List[Dict[str, Any]], 
                                 include_dependencies: bool = True) -> Dict[str, Any]:
        """
        Analyze distribution of importance scores across messages
        
        Args:
            messages: List of messages to analyze
            include_dependencies: Whether to include dependency scoring
            
        Returns:
            Dictionary with score distribution categories and dependency stats
        """
        # Build context if dependency scoring is enabled
        if include_dependencies and self.scorer.consider_dependencies:
            self.scorer.build_conversation_context(messages)
        
        distribution = {"high": 0, "medium": 0, "low": 0}
        scores = []
        
        for message in messages:
            score = self.scorer.calculate_message_importance(message)
            scores.append(score)
            
            if score >= 70:
                distribution["high"] += 1
            elif score >= 30:
                distribution["medium"] += 1
            else:
                distribution["low"] += 1
        
        result = {
            "distribution": distribution,
            "total_messages": len(messages),
            "average_score": sum(scores) / len(scores) if scores else 0,
            "score_range": {"min": min(scores), "max": max(scores)} if scores else {"min": 0, "max": 0}
        }
        
        # Add dependency statistics if available
        if include_dependencies and self.scorer.consider_dependencies:
            dependency_stats = self.scorer.get_dependency_statistics()
            result["dependency_stats"] = dependency_stats
        
        return result
    
    def identify_important_patterns(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify important conversation patterns and sequences
        
        Args:
            messages: List of messages to analyze
            
        Returns:
            Dictionary with identified patterns
        """
        patterns = {
            "error_solution_pairs": [],
            "tool_sequences": [],
            "code_modification_chains": []
        }
        
        # Find error-solution pairs
        for i, message in enumerate(messages):
            content = self.scorer._extract_message_content(message)
            
            # Look for error followed by solution
            if self.scorer._matches_patterns(content, self.scorer.patterns["error_solution"]):
                # Check next few messages for solutions
                for j in range(i + 1, min(i + 4, len(messages))):
                    next_content = self.scorer._extract_message_content(messages[j])
                    if self.scorer._matches_patterns(next_content, self.scorer.patterns["error_solution"]):
                        patterns["error_solution_pairs"].append((i, j))
                        break
        
        # Find tool sequences (allow assistant messages between tools)
        tool_calls = []
        for i, message in enumerate(messages):
            if message.get("type") == "tool_call":
                tool_name = message.get("message", {}).get("tool")
                if tool_name:
                    tool_calls.append((i, tool_name))
        
        # Group tool calls that are related (within reasonable distance)
        if len(tool_calls) > 1:
            current_sequence = [tool_calls[0]]
            for i in range(1, len(tool_calls)):
                prev_index, _ = tool_calls[i-1]
                curr_index, curr_tool = tool_calls[i]
                
                # If tools are within 5 messages of each other, consider them a sequence
                if curr_index - prev_index <= 5:
                    current_sequence.append((curr_index, curr_tool))
                else:
                    # End current sequence and start new one
                    if len(current_sequence) > 1:
                        patterns["tool_sequences"].append(current_sequence[:])
                    current_sequence = [(curr_index, curr_tool)]
            
            # Add final sequence if it has multiple tools
            if len(current_sequence) > 1:
                patterns["tool_sequences"].append(current_sequence)
        
        # Find code modification chains
        for i, message in enumerate(messages):
            content = self.scorer._extract_message_content(message)
            if self.scorer._matches_patterns(content, self.scorer.patterns["code_changes"]):
                patterns["code_modification_chains"].append(i)
        
        return patterns
    
    def calculate_conversation_value(self, messages: List[Dict[str, Any]], 
                                   include_dependencies: bool = True) -> Dict[str, Any]:
        """
        Calculate overall value metrics for conversation
        
        Args:
            messages: List of messages to analyze
            include_dependencies: Whether to include dependency-aware scoring
            
        Returns:
            Dictionary with conversation value metrics
        """
        if not messages:
            return {"total_score": 0, "average_score": 0, "high_value_ratio": 0, "pruning_potential": 0}
        
        # Build context if dependency scoring is enabled
        if include_dependencies and self.scorer.consider_dependencies:
            self.scorer.build_conversation_context(messages)
        
        scores = [self.scorer.calculate_message_importance(msg) for msg in messages]
        high_value_count = sum(1 for score in scores if score >= 70)
        low_value_count = sum(1 for score in scores if score < 20)
        
        metrics = {
            "total_score": sum(scores),
            "average_score": sum(scores) / len(scores),
            "high_value_ratio": high_value_count / len(messages),
            "pruning_potential": low_value_count / len(messages),
            "score_statistics": {
                "min": min(scores),
                "max": max(scores),
                "median": sorted(scores)[len(scores)//2] if scores else 0
            }
        }
        
        # Add dependency metrics if available
        if include_dependencies and self.scorer.consider_dependencies:
            dependency_stats = self.scorer.get_dependency_statistics()
            metrics["conversation_structure"] = {
                "conversation_chains": dependency_stats.get("conversation_chains", 0),
                "messages_with_children": dependency_stats.get("messages_with_children", 0),
                "messages_with_recent_children": dependency_stats.get("messages_with_recent_children", 0),
                "max_chain_depth": dependency_stats.get("max_chain_depth", 0)
            }
        
        return metrics
    
    def recommend_pruning_threshold(self, messages: List[Dict[str, Any]], target_reduction: float = 0.5) -> Dict[str, Any]:
        """
        Recommend optimal pruning threshold to achieve target reduction
        
        Args:
            messages: List of messages to analyze
            target_reduction: Target percentage of messages to remove (0.0-1.0)
            
        Returns:
            Dictionary with threshold recommendation
        """
        if not messages:
            return {"threshold": 0, "predicted_reduction": 0, "preserved_messages": 0, "removed_messages": 0}
        
        # Calculate scores for all messages
        scores = [self.scorer.calculate_message_importance(msg) for msg in messages]
        sorted_scores = sorted(scores)
        
        # Find threshold that achieves target reduction
        target_remove_count = int(len(messages) * target_reduction)
        if target_remove_count >= len(messages):
            threshold = 100
        elif target_remove_count == 0:
            threshold = 0
        else:
            threshold = sorted_scores[target_remove_count]
        
        # Calculate actual reduction with this threshold
        removed_count = sum(1 for score in scores if score < threshold)
        preserved_count = len(messages) - removed_count
        actual_reduction = removed_count / len(messages) if messages else 0
        
        return {
            "threshold": threshold,
            "predicted_reduction": actual_reduction,
            "preserved_messages": preserved_count,
            "removed_messages": removed_count
        }