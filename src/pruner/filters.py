"""
Content filtering system with pattern-based rules
Phase 2 - Classification and compression rules for different content types
"""

import re
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict
from enum import Enum

# Import Phase 1 pattern analysis
from ..jsonl_analysis.patterns import PatternAnalyzer
from ..jsonl_analysis.scoring import ImportanceScorer

logger = logging.getLogger(__name__)


class ContentCategory(Enum):
    """Content importance categories"""
    HIGH_IMPORTANCE = "high_importance"
    MEDIUM_IMPORTANCE = "medium_importance" 
    LOW_IMPORTANCE = "low_importance"
    VERY_LOW_IMPORTANCE = "very_low_importance"


class ContentType(Enum):
    """Content type classifications"""
    ESSENTIAL = "essential"          # Must preserve
    INFORMATIONAL = "informational"  # Useful but compressible
    SYSTEM_NOISE = "system_noise"    # Low value system messages
    NOISE = "noise"                  # Can be heavily compressed or removed


class CompressionAction(Enum):
    """Compression actions"""
    PRESERVE = "preserve"            # Keep as-is
    COMPRESS = "compress"            # Apply smart compression
    COMPRESS_HEAVILY = "compress_heavily"  # Heavy compression/summarization
    REMOVE = "remove"                # Remove entirely


class ContentFilter:
    """
    Main content filtering engine that classifies messages by importance
    and applies appropriate filtering rules
    """
    
    def __init__(self):
        """Initialize content filter with pattern analyzer and scorer"""
        self.pattern_analyzer = PatternAnalyzer()
        self.importance_scorer = ImportanceScorer()
        
        # Content classification rules
        self.classification_rules = {
            ContentCategory.HIGH_IMPORTANCE: [
                self._is_user_question,
                self._is_error_solution,
                self._is_code_modification,
                self._is_architectural_decision,
                self._is_critical_debugging
            ],
            ContentCategory.MEDIUM_IMPORTANCE: [
                self._is_file_operation,
                self._is_debugging_activity,
                self._is_assistant_explanation,
                self._is_test_execution
            ],
            ContentCategory.LOW_IMPORTANCE: [
                self._is_system_validation,
                self._is_status_message,
                self._is_routine_tool_call
            ],
            ContentCategory.VERY_LOW_IMPORTANCE: [
                self._is_hook_log,
                self._is_empty_output,
                self._is_confirmation_only
            ]
        }
    
    def classify_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify message importance and determine filtering approach
        
        Args:
            message: Message to classify
            
        Returns:
            Classification result with category and confidence
        """
        # Get importance score from Phase 1 scorer
        importance_score = self.importance_scorer.calculate_message_importance(message)
        
        # Get pattern analysis
        pattern_analysis = self.pattern_analyzer.analyze_message(message)
        
        # Apply classification rules
        category = self._determine_category(message, importance_score, pattern_analysis)
        
        # Calculate confidence based on multiple factors
        confidence = self._calculate_classification_confidence(
            importance_score, pattern_analysis, category
        )
        
        return {
            'category': category.value,
            'importance_score': importance_score,
            'confidence': confidence,
            'patterns': pattern_analysis['patterns'],
            'reasoning': self._get_classification_reasoning(category, pattern_analysis)
        }
    
    def _determine_category(
        self, 
        message: Dict[str, Any], 
        importance_score: int,
        pattern_analysis: Dict[str, Any]
    ) -> ContentCategory:
        """Determine content category using rules and scoring"""
        
        # Apply rule-based classification
        for category, rules in self.classification_rules.items():
            for rule in rules:
                if rule(message, pattern_analysis):
                    return category
        
        # Fallback to importance score
        if importance_score >= 70:
            return ContentCategory.HIGH_IMPORTANCE
        elif importance_score >= 40:
            return ContentCategory.MEDIUM_IMPORTANCE
        elif importance_score >= 20:
            return ContentCategory.LOW_IMPORTANCE
        else:
            return ContentCategory.VERY_LOW_IMPORTANCE
    
    def _calculate_classification_confidence(
        self,
        importance_score: int,
        pattern_analysis: Dict[str, Any],
        category: ContentCategory
    ) -> float:
        """Calculate confidence in classification"""
        confidence_factors = []
        
        # Importance score confidence
        if importance_score >= 80 or importance_score <= 10:
            confidence_factors.append(0.9)  # Very confident about extreme scores
        elif importance_score >= 60 or importance_score <= 20:
            confidence_factors.append(0.7)  # Confident about high/low scores
        else:
            confidence_factors.append(0.5)  # Less confident about medium scores
        
        # Pattern confidence
        patterns = pattern_analysis.get('patterns', {})
        pattern_confidence = 0.0
        
        for pattern_type, pattern_data in patterns.items():
            if pattern_data.get('detected', False):
                pattern_confidence = max(pattern_confidence, pattern_data.get('confidence', 0))
        
        confidence_factors.append(pattern_confidence)
        
        # Average confidence
        return sum(confidence_factors) / len(confidence_factors)
    
    def _get_classification_reasoning(
        self,
        category: ContentCategory,
        pattern_analysis: Dict[str, Any]
    ) -> List[str]:
        """Get human-readable reasoning for classification"""
        reasoning = []
        
        patterns = pattern_analysis.get('patterns', {})
        
        # Add reasoning based on detected patterns
        for pattern_type, pattern_data in patterns.items():
            if pattern_data.get('detected', False):
                confidence = pattern_data.get('confidence', 0)
                if confidence > 0.5:
                    reasoning.append(f"Detected {pattern_type} (confidence: {confidence:.2f})")
        
        # Add category-specific reasoning
        category_reasoning = {
            ContentCategory.HIGH_IMPORTANCE: "Essential for development workflow",
            ContentCategory.MEDIUM_IMPORTANCE: "Useful for context and debugging",
            ContentCategory.LOW_IMPORTANCE: "System information with limited value",
            ContentCategory.VERY_LOW_IMPORTANCE: "Noise or redundant information"
        }
        
        reasoning.append(category_reasoning[category])
        
        return reasoning
    
    # Classification rule methods
    def _is_user_question(self, message: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> bool:
        """Check if message is a user question"""
        return (message.get('type') == 'user' and 
                pattern_analysis.get('importance_indicators', {}).get('user_question', False))
    
    def _is_error_solution(self, message: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> bool:
        """Check if message contains error solution"""
        return pattern_analysis.get('importance_indicators', {}).get('error_solution', False)
    
    def _is_code_modification(self, message: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> bool:
        """Check if message involves code modification"""
        return (message.get('type') == 'tool_call' and
                message.get('message', {}).get('tool') in ['Write', 'Edit', 'MultiEdit'])
    
    def _is_architectural_decision(self, message: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> bool:
        """Check if message contains architectural decisions"""
        return pattern_analysis.get('importance_indicators', {}).get('architectural_decision', False)
    
    def _is_critical_debugging(self, message: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> bool:
        """Check if message contains critical debugging information"""
        content = self._extract_content(message)
        return any(keyword in content.lower() for keyword in [
            'traceback', 'stack trace', 'critical error', 'fatal error', 'exception'
        ])
    
    def _is_file_operation(self, message: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> bool:
        """Check if message is a file operation"""
        return (message.get('type') == 'tool_call' and
                message.get('message', {}).get('tool') in ['Read', 'Glob', 'Grep'])
    
    def _is_debugging_activity(self, message: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> bool:
        """Check if message involves debugging activity"""
        return pattern_analysis.get('importance_indicators', {}).get('debugging_info', False)
    
    def _is_assistant_explanation(self, message: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> bool:
        """Check if message is an assistant explanation"""
        return (message.get('type') == 'assistant' and
                len(self._extract_content(message)) > 50)  # Substantial explanation
    
    def _is_test_execution(self, message: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> bool:
        """Check if message involves test execution"""
        content = self._extract_content(message)
        return any(keyword in content.lower() for keyword in [
            'pytest', 'test', 'unittest', 'jest', 'mocha', 'karma'
        ])
    
    def _is_system_validation(self, message: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> bool:
        """Check if message is system validation"""
        return pattern_analysis.get('importance_indicators', {}).get('system_validation', False)
    
    def _is_status_message(self, message: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> bool:
        """Check if message is a status message"""
        content = self._extract_content(message)
        return any(keyword in content.lower() for keyword in [
            'status', 'ready', 'online', 'started', 'running', 'operational'
        ])
    
    def _is_routine_tool_call(self, message: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> bool:
        """Check if message is a routine tool call"""
        return (message.get('type') == 'tool_call' and
                message.get('message', {}).get('tool') in ['TodoWrite'] and
                len(self._extract_content(message)) < 100)
    
    def _is_hook_log(self, message: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> bool:
        """Check if message is a hook log"""
        return pattern_analysis.get('importance_indicators', {}).get('hook_log', False)
    
    def _is_empty_output(self, message: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> bool:
        """Check if message has empty output"""
        return pattern_analysis.get('importance_indicators', {}).get('empty_output', False)
    
    def _is_confirmation_only(self, message: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> bool:
        """Check if message is confirmation only"""
        content = self._extract_content(message).strip().lower()
        return content in ['ok', 'done', 'success', 'completed', 'acknowledged', 'confirmed', 'received']
    
    def _extract_content(self, message: Dict[str, Any]) -> str:
        """Extract textual content from message"""
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


class CompressionRulesEngine:
    """
    Engine for determining appropriate compression rules for different content types
    """
    
    def __init__(self):
        """Initialize compression rules engine"""
        self.content_filter = ContentFilter()
        
        # Compression rules mapping
        self.compression_rules = {
            ContentCategory.HIGH_IMPORTANCE: {
                'action': CompressionAction.PRESERVE,
                'compression_ratio': 0.0,
                'preserve_summary': False
            },
            ContentCategory.MEDIUM_IMPORTANCE: {
                'action': CompressionAction.COMPRESS,
                'compression_ratio': 0.3,
                'preserve_summary': True
            },
            ContentCategory.LOW_IMPORTANCE: {
                'action': CompressionAction.COMPRESS_HEAVILY,
                'compression_ratio': 0.7,
                'preserve_summary': True
            },
            ContentCategory.VERY_LOW_IMPORTANCE: {
                'action': CompressionAction.COMPRESS_HEAVILY,
                'compression_ratio': 0.8,
                'preserve_summary': False
            }
        }
        
        # Tool-specific rules
        self.tool_rules = {
            'Write': {'action': CompressionAction.PRESERVE},
            'Edit': {'action': CompressionAction.PRESERVE},
            'MultiEdit': {'action': CompressionAction.PRESERVE},
            'Read': {'action': CompressionAction.COMPRESS, 'compression_ratio': 0.4},
            'Bash': {'action': CompressionAction.COMPRESS, 'compression_ratio': 0.5},
            'Grep': {'action': CompressionAction.COMPRESS, 'compression_ratio': 0.6},
            'Glob': {'action': CompressionAction.COMPRESS, 'compression_ratio': 0.6},
            'TodoWrite': {'action': CompressionAction.COMPRESS_HEAVILY, 'compression_ratio': 0.8}
        }
    
    def get_compression_rule(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get appropriate compression rule for message
        
        Args:
            message: Message to get compression rule for
            
        Returns:
            Dictionary with compression rule details
        """
        # Get message classification
        classification = self.content_filter.classify_message(message)
        category = ContentCategory(classification['category'])
        
        # Get base rule for category
        base_rule = self.compression_rules[category].copy()
        
        # Apply tool-specific overrides
        if message.get('type') == 'tool_call':
            tool_name = message.get('message', {}).get('tool')
            if tool_name in self.tool_rules:
                tool_rule = self.tool_rules[tool_name]
                base_rule.update(tool_rule)
        
        # Apply content-specific adjustments
        base_rule.update(self._get_content_specific_adjustments(message, classification))
        
        return base_rule
    
    def _get_content_specific_adjustments(
        self, 
        message: Dict[str, Any], 
        classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get content-specific rule adjustments"""
        adjustments = {}
        
        # Adjust based on content size
        content = self._extract_content(message)
        content_length = len(content)
        
        if content_length > 5000:  # Very large content
            adjustments['compression_ratio'] = min(
                adjustments.get('compression_ratio', 0.5) + 0.2, 0.9
            )
        elif content_length < 50:  # Very small content
            adjustments['compression_ratio'] = max(
                adjustments.get('compression_ratio', 0.5) - 0.2, 0.0
            )
        
        # Adjust based on error content
        if 'error' in content.lower() or 'exception' in content.lower():
            adjustments['action'] = CompressionAction.PRESERVE
            adjustments['compression_ratio'] = 0.0
        
        # Adjust based on patterns
        patterns = classification.get('patterns', {})
        if patterns.get('error.error_keywords', {}).get('detected', False):
            adjustments['preserve_summary'] = True
        
        return adjustments
    
    def _extract_content(self, message: Dict[str, Any]) -> str:
        """Extract content for analysis"""
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


class ContentClassifier:
    """
    Classifies content types for specialized handling
    """
    
    def __init__(self):
        """Initialize content classifier"""
        self.classification_patterns = {
            ContentType.ESSENTIAL: [
                re.compile(r'\b(critical|important|essential|must|required|necessary)\b', re.IGNORECASE),
                re.compile(r'\b(error|exception|failed|failure|bug|issue)\b.*\b(fix|solve|resolve)\b', re.IGNORECASE),
                re.compile(r'\b(user|question|ask|help|how)\b', re.IGNORECASE),
            ],
            ContentType.INFORMATIONAL: [
                re.compile(r'\b(info|information|detail|explain|describe|show)\b', re.IGNORECASE),
                re.compile(r'\b(read|examine|check|analyze|review)\b', re.IGNORECASE),
                re.compile(r'\b(function|method|class|variable|file)\b', re.IGNORECASE),
            ],
            ContentType.SYSTEM_NOISE: [
                re.compile(r'\b(validation|check.*passed|status|ready|online)\b', re.IGNORECASE),
                re.compile(r'\b(system|service|process).*\b(started|running|operational)\b', re.IGNORECASE),
            ],
            ContentType.NOISE: [
                re.compile(r'\bhook\b.*\b(executed|completed|finished)\b', re.IGNORECASE),
                re.compile(r'^\s*(ok|done|success|completed|yes|no)\s*$', re.IGNORECASE),
                re.compile(r'^\s*$'),  # Empty content
            ]
        }
    
    def classify_content_type(self, message: Dict[str, Any]) -> str:
        """
        Classify content type of message
        
        Args:
            message: Message to classify
            
        Returns:
            Content type classification
        """
        content = self._extract_content(message)
        
        # Apply pattern matching in order of priority
        for content_type, patterns in self.classification_patterns.items():
            for pattern in patterns:
                if pattern.search(content):
                    return content_type.value
        
        # Default classification based on message type
        msg_type = message.get('type', 'unknown')
        if msg_type == 'user':
            return ContentType.ESSENTIAL.value
        elif msg_type == 'assistant':
            return ContentType.INFORMATIONAL.value
        elif msg_type == 'tool_call':
            tool_name = message.get('message', {}).get('tool', '')
            if tool_name in ['Write', 'Edit', 'MultiEdit']:
                return ContentType.ESSENTIAL.value
            else:
                return ContentType.INFORMATIONAL.value
        else:
            return ContentType.SYSTEM_NOISE.value
    
    def _extract_content(self, message: Dict[str, Any]) -> str:
        """Extract content for classification"""
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


class DebuggingPreserver:
    """
    Specialized filter for preserving debugging information and error traces
    """
    
    def __init__(self):
        """Initialize debugging preserver"""
        self.debug_patterns = {
            'error_trace': [
                re.compile(r'\btraceback\b', re.IGNORECASE),
                re.compile(r'\bstack\s+trace\b', re.IGNORECASE),
                re.compile(r'\b\w*Error\b|\b\w*Exception\b'),
                re.compile(r'\bFailed\b|\bError\b.*\bat\s+line\b', re.IGNORECASE),
            ],
            'error_solution': [
                re.compile(r'\bfix\b.*\berror\b|\berror\b.*\bfix\b', re.IGNORECASE),
                re.compile(r'\bsolution\b|\bresolve\b|\bdebug\b', re.IGNORECASE),
                re.compile(r'\bhere.*fix\b|\bthe\s+fix\b', re.IGNORECASE),
            ],
            'debug_output': [
                re.compile(r'\bdebug\b|\bdebugging\b', re.IGNORECASE),
                re.compile(r'\bprint\b|\bconsole\.log\b|\blog\b', re.IGNORECASE),
                re.compile(r'\bbreakpoint\b|\bstep\b|\btrace\b', re.IGNORECASE),
            ],
            'test_failure': [
                re.compile(r'\btest\s+failed\b|\bfailed\s+test\b', re.IGNORECASE),
                re.compile(r'\bassertion\s*error\b|\bassert\b.*\bfail\b', re.IGNORECASE),
                re.compile(r'\bpytest\b|\bjest\b|\bmocha\b.*\bfail\b', re.IGNORECASE),
            ]
        }
    
    def should_preserve(self, message: Dict[str, Any]) -> bool:
        """
        Check if message should be preserved for debugging purposes
        
        Args:
            message: Message to check
            
        Returns:
            True if message should be preserved
        """
        content = self._extract_content(message)
        
        # Check all debug patterns
        for pattern_type, patterns in self.debug_patterns.items():
            for pattern in patterns:
                if pattern.search(content):
                    return True
        
        # Check message metadata
        if message.get('type') == 'tool_call':
            tool_name = message.get('message', {}).get('tool', '')
            result = message.get('message', {}).get('result', '')
            
            # Preserve tool calls that resulted in errors
            if any(keyword in str(result).lower() for keyword in ['error', 'exception', 'failed', 'traceback']):
                return True
        
        return False
    
    def get_preservation_reason(self, message: Dict[str, Any]) -> str:
        """
        Get reason why message should be preserved
        
        Args:
            message: Message to analyze
            
        Returns:
            Preservation reason string
        """
        content = self._extract_content(message)
        
        # Find matching pattern type
        for pattern_type, patterns in self.debug_patterns.items():
            for pattern in patterns:
                if pattern.search(content):
                    return pattern_type
        
        # Check tool result errors
        if message.get('type') == 'tool_call':
            result = message.get('message', {}).get('result', '')
            if any(keyword in str(result).lower() for keyword in ['error', 'exception', 'failed']):
                return 'tool_error'
        
        return 'debugging_context'
    
    def _extract_content(self, message: Dict[str, Any]) -> str:
        """Extract content for analysis"""
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