"""
Exponential decay engine for time-based importance weighting.

This module implements sophisticated temporal decay functions that assign
higher importance to recent messages while gracefully degrading older content.
"""

import json
import math
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class DecayMode(Enum):
    """Temporal decay modes for different conversation types."""
    NONE = "none"
    SIMPLE = "simple"
    MULTI_STAGE = "multi_stage"
    CONTENT_AWARE = "content_aware"
    ADAPTIVE = "adaptive"


class ExponentialDecayEngine:
    """
    Advanced exponential decay engine for temporal importance weighting.
    
    Implements multiple decay strategies including simple exponential decay,
    multi-stage decay with different time windows, and content-aware decay
    that adjusts based on message type.
    """
    
    # Default decay constants by content type (lower = slower decay)
    DEFAULT_DECAY_CONSTANTS = {
        'error_messages': 0.1,      # Slow decay - errors stay relevant
        'code_changes': 0.3,        # Medium decay - code has lasting impact  
        'status_updates': 0.8,      # Fast decay - status becomes outdated
        'debugging_info': 0.2,      # Slow decay - debugging context valuable
        'general_chat': 0.6,        # Faster decay - less critical over time
        'architectural_decisions': 0.05,  # Very slow - architecture persists
        'default': 0.4             # Default for unclassified content
    }
    
    # Time windows in hours for multi-stage decay
    DEFAULT_TIME_WINDOWS = {
        'ultra_recent': (0, 1),      # 0-1 hours: minimal decay
        'recent': (1, 24),           # 1-24 hours: gentle decay
        'medium': (24, 168),         # 1-7 days: moderate decay  
        'old': (168, 720),           # 1-4 weeks: strong decay
        'ancient': (720, float('inf'))  # 4+ weeks: maximum decay
    }
    
    # Decay multipliers for each time window
    DEFAULT_WINDOW_MULTIPLIERS = {
        'ultra_recent': 1.0,    # No decay
        'recent': 0.1,          # Very slow decay
        'medium': 0.5,          # Moderate decay
        'old': 1.5,             # Strong decay  
        'ancient': 3.0          # Maximum decay
    }
    
    def __init__(
        self, 
        mode: DecayMode = DecayMode.SIMPLE,
        decay_constants: Optional[Dict[str, float]] = None,
        time_windows: Optional[Dict[str, Tuple[float, float]]] = None,
        window_multipliers: Optional[Dict[str, float]] = None,
        reference_time: Optional[float] = None
    ):
        """
        Initialize the exponential decay engine.
        
        Args:
            mode: Decay mode to use
            decay_constants: Custom decay constants by content type
            time_windows: Custom time windows for multi-stage decay
            window_multipliers: Custom multipliers for time windows
            reference_time: Reference timestamp (defaults to current time)
        """
        self.mode = mode
        self.decay_constants = decay_constants or self.DEFAULT_DECAY_CONSTANTS.copy()
        self.time_windows = time_windows or self.DEFAULT_TIME_WINDOWS.copy()
        self.window_multipliers = window_multipliers or self.DEFAULT_WINDOW_MULTIPLIERS.copy()
        self.reference_time = reference_time or time.time()
        
        # Statistics tracking
        self.stats = {
            'messages_processed': 0,
            'average_decay_factor': 0.0,
            'decay_factors_by_type': {},
            'time_distribution': {},
            'velocity_adjustments': 0,
            'reference_adjustments': 0
        }
        
        # Conversation velocity tracking
        self.conversation_velocity = None
        self.velocity_adjusted = False
        
        logger.info(f"Initialized ExponentialDecayEngine with mode: {mode.value}")
    
    def calculate_decay_factor(
        self, 
        message: Dict[str, Any], 
        content_type: Optional[str] = None,
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate the decay factor for a message based on its age and type.
        
        Args:
            message: The message dictionary
            content_type: Optional content type classification
            
        Returns:
            Decay factor between 0.0 and 1.0 (1.0 = no decay, 0.0 = maximum decay)
        """
        if self.mode == DecayMode.NONE:
            return 1.0
            
        # Get message timestamp
        timestamp = get_message_timestamp(message)
        if timestamp is None:
            logger.warning("No timestamp found in message, using reference time")
            return 1.0
            
        # Calculate time delta in hours
        time_delta_hours = calculate_time_delta(timestamp, self.reference_time, unit='hours')
        
        # Classify content type if not provided
        if content_type is None:
            content_type = self._classify_content_type(message)
            
        # Calculate decay factor based on mode
        if self.mode == DecayMode.SIMPLE:
            decay_factor = self._simple_decay(time_delta_hours, content_type)
        elif self.mode == DecayMode.MULTI_STAGE:
            decay_factor = self._multi_stage_decay(time_delta_hours, content_type)
        elif self.mode == DecayMode.CONTENT_AWARE:
            decay_factor = self._content_aware_decay(time_delta_hours, content_type, message)
        elif self.mode == DecayMode.ADAPTIVE:
            decay_factor = self._adaptive_decay(time_delta_hours, content_type, message)
        else:
            decay_factor = self._simple_decay(time_delta_hours, content_type)
            
        # Update statistics
        self._update_stats(content_type, decay_factor, time_delta_hours)
        
        return max(0.0, min(1.0, decay_factor))  # Clamp between 0 and 1
    
    def _simple_decay(self, time_delta_hours: float, content_type: str) -> float:
        """Simple exponential decay: e^(-λ * t)"""
        lambda_val = self.decay_constants.get(content_type, self.decay_constants['default'])
        return math.exp(-lambda_val * time_delta_hours)
    
    def _multi_stage_decay(self, time_delta_hours: float, content_type: str) -> float:
        """Multi-stage decay with different rates for different time windows."""
        # Find which time window this message falls into
        window_name = None
        for name, (start, end) in self.time_windows.items():
            if start <= time_delta_hours < end:
                window_name = name
                break
                
        if window_name is None:
            window_name = 'ancient'  # Default to ancient for very old messages
            
        # Get base decay constant and window multiplier
        base_lambda = self.decay_constants.get(content_type, self.decay_constants['default'])
        window_multiplier = self.window_multipliers.get(window_name, 1.0)
        effective_lambda = base_lambda * window_multiplier
        
        # Apply decay within the time window
        window_start = self.time_windows[window_name][0]
        relative_time = time_delta_hours - window_start
        
        return math.exp(-effective_lambda * relative_time)
    
    def _content_aware_decay(self, time_delta_hours: float, content_type: str, message: Dict[str, Any]) -> float:
        """Content-aware decay that adjusts based on message content and context."""
        base_decay = self._multi_stage_decay(time_delta_hours, content_type)
        
        # Adjust decay based on content characteristics
        content_text = self._extract_message_content(message)
        
        # Boost factor for important content patterns
        boost_factor = 1.0
        
        # Error patterns get slower decay
        if any(pattern in content_text.lower() for pattern in ['error', 'exception', 'failed', 'crash']):
            boost_factor *= 1.3
            
        # Solution patterns get slower decay
        if any(pattern in content_text.lower() for pattern in ['fixed', 'solved', 'working', 'solution']):
            boost_factor *= 1.2
            
        # Code patterns get moderate boost
        if any(pattern in content_text for pattern in ['def ', 'class ', 'import ', 'function']):
            boost_factor *= 1.1
            
        # Configuration/setup patterns decay faster
        if any(pattern in content_text.lower() for pattern in ['configured', 'installed', 'setup', 'initialized']):
            boost_factor *= 0.9
            
        return base_decay * boost_factor
    
    def _adaptive_decay(self, time_delta_hours: float, content_type: str, message: Dict[str, Any]) -> float:
        """Adaptive decay that learns from conversation patterns (simplified version)."""
        # For now, use content-aware decay with additional conversation context
        base_decay = self._content_aware_decay(time_delta_hours, content_type, message)
        
        # TODO: Implement learning from conversation patterns
        # This could include:
        # - Message frequency analysis
        # - Topic continuity detection
        # - Reference pattern learning
        
        return base_decay
    
    def _classify_content_type(self, message: Dict[str, Any]) -> str:
        """Classify message content type for appropriate decay constants."""
        content = self._extract_message_content(message)
        content_lower = content.lower()
        
        # Check for error messages
        if any(pattern in content_lower for pattern in ['error', 'exception', 'traceback', 'failed', 'crash']):
            return 'error_messages'
            
        # Check for debugging info
        if any(pattern in content_lower for pattern in ['debug', 'trace', 'log', 'verbose', 'info:']):
            return 'debugging_info'
            
        # Check for code changes
        if any(pattern in content for pattern in ['def ', 'class ', 'import ', 'function', '```', 'def(', 'class(']):
            return 'code_changes'
            
        # Check for status updates
        if any(pattern in content_lower for pattern in ['completed', 'finished', 'done', 'status:', 'progress']):
            return 'status_updates'
            
        # Check for architectural decisions
        if any(pattern in content_lower for pattern in ['architecture', 'design', 'approach', 'strategy', 'decision']):
            return 'architectural_decisions'
            
        return 'default'
    
    def _extract_message_content(self, message: Dict[str, Any]) -> str:
        """Extract text content from a message for analysis."""
        # Try various common fields for message content
        for field in ['content', 'text', 'message', 'body', 'prompt', 'response']:
            if field in message and isinstance(message[field], str):
                return message[field]
                
        # If no text content found, convert entire message to string
        return str(message)
    
    def _update_stats(self, content_type: str, decay_factor: float, time_delta_hours: float):
        """Update internal statistics for monitoring and analysis."""
        self.stats['messages_processed'] += 1
        
        # Update average decay factor
        total_messages = self.stats['messages_processed']
        current_avg = self.stats['average_decay_factor']
        self.stats['average_decay_factor'] = ((current_avg * (total_messages - 1)) + decay_factor) / total_messages
        
        # Update by content type
        if content_type not in self.stats['decay_factors_by_type']:
            self.stats['decay_factors_by_type'][content_type] = []
        self.stats['decay_factors_by_type'][content_type].append(decay_factor)
        
        # Update time distribution
        time_bucket = self._get_time_bucket(time_delta_hours)
        if time_bucket not in self.stats['time_distribution']:
            self.stats['time_distribution'][time_bucket] = 0
        self.stats['time_distribution'][time_bucket] += 1
    
    def _get_time_bucket(self, time_delta_hours: float) -> str:
        """Get time bucket for statistics."""
        for name, (start, end) in self.time_windows.items():
            if start <= time_delta_hours < end:
                return name
        return 'ancient'
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get decay engine statistics."""
        stats_copy = self.stats.copy()
        
        # Calculate averages by content type
        for content_type, factors in stats_copy['decay_factors_by_type'].items():
            if factors:
                stats_copy['decay_factors_by_type'][content_type] = {
                    'average': sum(factors) / len(factors),
                    'count': len(factors),
                    'min': min(factors),
                    'max': max(factors)
                }
                
        return stats_copy
    
    def _apply_velocity_adjustment(self, base_constants: Dict[str, float], conversation_context: Dict[str, Any]) -> Dict[str, float]:
        """Apply conversation velocity adjustments to decay constants."""
        message_frequency = conversation_context.get('message_frequency', 1.0)
        conversation_length = conversation_context.get('conversation_length', 0)
        
        # Calculate velocity adjustment factor
        if message_frequency > 10:  # High velocity (>10 msg/hour)
            velocity_factor = 0.5  # Slow down decay by 50%
        elif message_frequency > 5:  # Medium velocity (5-10 msg/hour)
            velocity_factor = 0.7  # Slow down decay by 30%
        elif message_frequency > 1:  # Low velocity (1-5 msg/hour)
            velocity_factor = 0.9  # Slow down decay by 10%
        else:  # Very low velocity (<1 msg/hour)
            velocity_factor = 1.2  # Speed up decay by 20%
        
        # Apply length adjustment for very long conversations
        if conversation_length > 1000:
            velocity_factor *= 0.9  # Additional slowdown for long conversations
        
        # Create adjusted constants
        adjusted_constants = {}
        for content_type, constant in base_constants.items():
            adjusted_constants[content_type] = constant * velocity_factor
        
        if velocity_factor != 1.0:
            self.stats['velocity_adjustments'] += 1
            self.velocity_adjusted = True
            self.conversation_velocity = message_frequency
        
        return adjusted_constants
    
    def _is_referenced_message(self, message: Dict[str, Any], conversation_context: Dict[str, Any]) -> bool:
        """Check if message is referenced by later messages."""
        # Look for message references in conversation context
        references = conversation_context.get('message_references', {})
        message_id = self._get_message_id(message)
        
        if message_id and message_id in references:
            return references[message_id] > 1  # Referenced more than once
        
        # Simple heuristic: check if message contains unique identifiers that might be referenced
        content = self._extract_message_content(message)
        return any(pattern in content.lower() for pattern in ['function ', 'class ', 'error:', 'solution:'])
    
    def _is_topic_continuation(self, message: Dict[str, Any], conversation_context: Dict[str, Any]) -> bool:
        """Check if message continues an active topic thread."""
        # Simple heuristic: check for topic keywords in recent message history
        current_topics = conversation_context.get('current_topics', [])
        content = self._extract_message_content(message).lower()
        
        return any(topic.lower() in content for topic in current_topics)
    
    def _get_message_id(self, message: Dict[str, Any]) -> Optional[str]:
        """Extract message ID for reference tracking."""
        for field in ['id', 'uuid', 'message_id', 'msg_id']:
            if field in message:
                return str(message[field])
        return None
    
    def reset_statistics(self):
        """Reset internal statistics."""
        self.stats = {
            'messages_processed': 0,
            'average_decay_factor': 0.0,
            'decay_factors_by_type': {},
            'time_distribution': {},
            'velocity_adjustments': 0,
            'reference_adjustments': 0
        }
        self.conversation_velocity = None
        self.velocity_adjusted = False


def get_message_timestamp(message: Dict[str, Any]) -> Optional[float]:
    """
    Extract timestamp from a message in various common formats.
    
    Args:
        message: Message dictionary
        
    Returns:
        Unix timestamp as float, or None if not found
    """
    # Try various timestamp field names
    for field in ['timestamp', 'time', 'created_at', 'sent_at', 'date', 'ts']:
        if field in message:
            timestamp_value = message[field]
            
            # Handle different timestamp formats
            if isinstance(timestamp_value, (int, float)):
                # Unix timestamp
                return float(timestamp_value)
            elif isinstance(timestamp_value, str):
                # ISO format or other string formats
                try:
                    # Try ISO format
                    dt = datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                    return dt.timestamp()
                except ValueError:
                    # Try other common formats
                    try:
                        dt = datetime.strptime(timestamp_value, '%Y-%m-%d %H:%M:%S')
                        return dt.timestamp()
                    except ValueError:
                        continue
                        
    return None


def calculate_time_delta(timestamp: float, reference_time: float, unit: str = 'hours') -> float:
    """
    Calculate time difference between timestamp and reference time.
    
    Args:
        timestamp: Message timestamp
        reference_time: Reference timestamp (usually current time)
        unit: Time unit ('hours', 'days', 'minutes', 'seconds')
        
    Returns:
        Time delta in specified unit
    """
    delta_seconds = abs(reference_time - timestamp)
    
    if unit == 'seconds':
        return delta_seconds
    elif unit == 'minutes':
        return delta_seconds / 60
    elif unit == 'hours':
        return delta_seconds / 3600
    elif unit == 'days':
        return delta_seconds / 86400
    else:
        raise ValueError(f"Unsupported time unit: {unit}")


def analyze_conversation_velocity(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze conversation velocity and patterns for decay adjustment.
    
    Args:
        messages: List of conversation messages
        
    Returns:
        Dictionary with velocity analysis results
    """
    if not messages:
        return {
            'message_frequency': 0.0,
            'conversation_length': 0,
            'time_span_hours': 0.0,
            'current_topics': [],
            'message_references': {}
        }
    
    # Extract timestamps
    timestamps = []
    for msg in messages:
        ts = get_message_timestamp(msg)
        if ts:
            timestamps.append(ts)
    
    if len(timestamps) < 2:
        return {
            'message_frequency': 1.0,
            'conversation_length': len(messages),
            'time_span_hours': 1.0,
            'current_topics': [],
            'message_references': {}
        }
    
    # Calculate time span and frequency
    time_span_seconds = max(timestamps) - min(timestamps)
    time_span_hours = time_span_seconds / 3600 if time_span_seconds > 0 else 1.0
    message_frequency = len(messages) / time_span_hours if time_span_hours > 0 else 1.0
    
    # Extract topics from recent messages (simple keyword extraction)
    current_topics = _extract_current_topics(messages[-10:])  # Last 10 messages
    
    # Build simple reference map
    message_references = _build_reference_map(messages)
    
    return {
        'message_frequency': message_frequency,
        'conversation_length': len(messages),
        'time_span_hours': time_span_hours,
        'current_topics': current_topics,
        'message_references': message_references
    }


def _extract_current_topics(recent_messages: List[Dict[str, Any]]) -> List[str]:
    """Extract current conversation topics from recent messages."""
    topics = set()
    
    for msg in recent_messages:
        content = str(msg.get('message', {}).get('content', '')).lower()
        
        # Look for key technical terms that might indicate topics
        topic_patterns = [
            r'\b(function|class|method|variable)\s+(\w+)',
            r'\b(error|exception|bug)\s+in\s+(\w+)',
            r'\b(implement|create|build)\s+(\w+)',
            r'\b(debug|fix|solve)\s+(\w+)',
            r'\b(api|database|server|client)\s+(\w+)'
        ]
        
        import re
        for pattern in topic_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    topics.add(match[1])  # Second capture group
                else:
                    topics.add(match)
    
    return list(topics)[:5]  # Return top 5 topics


def _build_reference_map(messages: List[Dict[str, Any]]) -> Dict[str, int]:
    """Build a map of message references for importance tracking."""
    references = {}
    
    # Simple heuristic: count mentions of function/class names, error types, etc.
    important_terms = set()
    
    # First pass: extract important terms
    for msg in messages:
        content = str(msg.get('message', {}).get('content', '')).lower()
        
        import re
        # Extract function/class names
        func_matches = re.findall(r'\b(def|function|class)\s+(\w+)', content)
        for match in func_matches:
            important_terms.add(match[1])
        
        # Extract error types
        error_matches = re.findall(r'\b(\w*error|\w*exception)\b', content)
        important_terms.update(error_matches)
    
    # Second pass: count references to important terms
    for term in important_terms:
        count = 0
        for msg in messages:
            content = str(msg.get('message', {}).get('content', '')).lower()
            if term.lower() in content:
                count += 1
        if count > 1:
            references[term] = count
    
    return references