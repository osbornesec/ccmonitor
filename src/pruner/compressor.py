"""
Context-aware compression algorithms for JSONL content
Phase 2 - Smart truncation, semantic summarization, and reference analysis
"""

import re
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, Counter
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SmartTruncator:
    """
    Intelligently truncates large content while preserving key information
    at the beginning and end of outputs
    """
    
    def __init__(self, max_length: int = 1000, preserve_lines: int = 3):
        """
        Initialize truncator with configuration
        
        Args:
            max_length: Maximum length of truncated content
            preserve_lines: Number of lines to preserve from start/end
        """
        self.max_length = max_length
        self.preserve_lines = preserve_lines
    
    def truncate_content(self, content: str, max_length: Optional[int] = None, preserve_lines: Optional[int] = None) -> str:
        """
        Truncate content while preserving beginning and end
        
        Args:
            content: Content to truncate
            max_length: Override default max length
            preserve_lines: Override default preserve lines
            
        Returns:
            Truncated content with preservation markers
        """
        if not content or isinstance(content, (int, float, bool)):
            return str(content) if content is not None else ""
        
        content = str(content)
        max_len = max_length or self.max_length
        preserve = preserve_lines or self.preserve_lines
        
        # If content is already short enough, return as-is
        if len(content) <= max_len:
            return content
        
        lines = content.split('\n')
        
        # If very few lines, use character-based truncation
        if len(lines) <= preserve * 2:
            return self._truncate_characters(content, max_len)
        
        # Line-based truncation
        start_lines = lines[:preserve]
        end_lines = lines[-preserve:]
        
        # Calculate how much content we're removing
        total_lines = len(lines)
        removed_lines = total_lines - (preserve * 2)
        
        # Estimate content size
        start_content = '\n'.join(start_lines)
        end_content = '\n'.join(end_lines)
        
        # Create truncation marker
        truncation_marker = f"\n... [TRUNCATED {removed_lines} lines ({len(content) - len(start_content) - len(end_content)} chars)] ...\n"
        
        truncated = start_content + truncation_marker + end_content
        
        # If still too long, apply character truncation to preserved parts
        if len(truncated) > max_len:
            return self._truncate_characters(content, max_len)
        
        return truncated
    
    def _truncate_characters(self, content: str, max_length: int) -> str:
        """Apply character-based truncation for very long content"""
        if len(content) <= max_length:
            return content
        
        # Reserve space for truncation marker
        marker = "... [TRUNCATED] ..."
        available_space = max_length - len(marker)
        
        if available_space <= 20:  # Too little space
            return content[:max_length - 3] + "..."
        
        # Split available space between start and end
        start_chars = available_space // 2
        end_chars = available_space - start_chars
        
        start_part = content[:start_chars].rstrip()
        end_part = content[-end_chars:].lstrip()
        
        return start_part + marker + end_part
    
    def truncate_tool_output(self, tool_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Specifically truncate tool output while preserving structure
        
        Args:
            tool_message: Tool call message to truncate
            
        Returns:
            Message with truncated output
        """
        truncated_message = tool_message.copy()
        
        if 'message' in truncated_message:
            msg_content = truncated_message['message']
            if isinstance(msg_content, dict) and 'result' in msg_content:
                original_result = msg_content['result']
                
                if original_result and len(str(original_result)) > 500:
                    truncated_result = self.truncate_content(
                        str(original_result),
                        max_length=500,
                        preserve_lines=2
                    )
                    
                    msg_content['result'] = truncated_result
                    msg_content['_truncated'] = True
                    msg_content['_original_length'] = len(str(original_result))
        
        return truncated_message


class SemanticSummarizer:
    """
    Provides semantic summarization for repetitive and verbose content
    """
    
    def __init__(self):
        """Initialize semantic summarizer"""
        self.repetition_threshold = 3  # Minimum repetitions to trigger summarization
        self.similarity_threshold = 0.8  # Similarity threshold for grouping
    
    def summarize_repetitive_content(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect and summarize repetitive message patterns
        
        Args:
            messages: List of messages to analyze
            
        Returns:
            Summary information about repetitive patterns
        """
        # Group messages by content similarity
        content_groups = self._group_similar_messages(messages)
        
        summaries = []
        total_compressed = 0
        
        for group_key, group_messages in content_groups.items():
            if len(group_messages) >= self.repetition_threshold:
                summary = self._create_group_summary(group_messages)
                summaries.append(summary)
                total_compressed += len(group_messages)
        
        return {
            'summaries': summaries,
            'total_messages_compressed': total_compressed,
            'compression_groups': len(summaries),
            'compressed': total_compressed > 0
        }
    
    def _group_similar_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group messages by content similarity"""
        groups = defaultdict(list)
        
        for message in messages:
            content = self._extract_comparable_content(message)
            
            # Create signature for grouping
            signature = self._create_content_signature(content)
            groups[signature].append(message)
        
        # Filter out groups that are too small
        return {k: v for k, v in groups.items() if len(v) >= self.repetition_threshold}
    
    def _extract_comparable_content(self, message: Dict[str, Any]) -> str:
        """Extract content for comparison"""
        if 'message' in message:
            msg_content = message['message']
            if isinstance(msg_content, dict):
                if 'content' in msg_content:
                    return str(msg_content['content'])
                elif 'tool' in msg_content:
                    # For tool calls, include tool name and basic parameters
                    tool_info = f"Tool: {msg_content['tool']}"
                    if 'parameters' in msg_content:
                        params = msg_content['parameters']
                        if isinstance(params, dict):
                            # Include key parameter patterns
                            if 'command' in params:
                                tool_info += f" Command pattern"
                            if 'file_path' in params:
                                tool_info += f" File operation"
                    return tool_info
        
        return ""
    
    def _create_content_signature(self, content: str) -> str:
        """Create signature for content grouping"""
        if not content:
            return "empty"
        
        # Normalize content for pattern matching
        normalized = content.lower().strip()
        
        # Extract key patterns
        patterns = []
        
        # Hook patterns
        if 'hook' in normalized:
            hook_match = re.search(r'hook[:\s]*(\w+)', normalized)
            if hook_match:
                patterns.append(f"hook_{hook_match.group(1)}")
            else:
                patterns.append("hook_generic")
        
        # Validation patterns
        if any(word in normalized for word in ['validation', 'check', 'verified']):
            patterns.append("validation")
        
        # Tool patterns
        if 'tool:' in normalized:
            tool_match = re.search(r'tool:\s*(\w+)', normalized)
            if tool_match:
                patterns.append(f"tool_{tool_match.group(1)}")
        
        # Error patterns
        if any(word in normalized for word in ['error', 'exception', 'failed']):
            patterns.append("error")
        
        # Success patterns
        if any(word in normalized for word in ['success', 'completed', 'done']):
            patterns.append("success")
        
        # If no patterns found, use first few words
        if not patterns:
            words = normalized.split()[:3]
            patterns.append('_'.join(words))
        
        return '|'.join(patterns)
    
    def _create_group_summary(self, group_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create summary for a group of similar messages"""
        if not group_messages:
            return {}
        
        first_message = group_messages[0]
        content = self._extract_comparable_content(first_message)
        
        # Extract pattern
        pattern = self._create_content_signature(content)
        
        # Count occurrences
        count = len(group_messages)
        
        # Get time range
        timestamps = []
        for msg in group_messages:
            if 'timestamp' in msg:
                timestamps.append(msg['timestamp'])
        
        time_range = {
            'start': min(timestamps) if timestamps else None,
            'end': max(timestamps) if timestamps else None
        }
        
        # Calculate original vs compressed size
        original_size = sum(len(str(msg.get('message', {}))) for msg in group_messages)
        
        summary_text = f"Repeated pattern: {pattern} (occurred {count} times)"
        compressed_size = len(summary_text)
        
        return {
            'pattern': pattern,
            'count': count,
            'time_range': time_range,
            'summary': summary_text,
            'original_size': original_size,
            'compressed_size': compressed_size,
            'compression_ratio': 1 - (compressed_size / original_size) if original_size > 0 else 0,
            'sample_message': first_message,
            'compressed': True
        }
    
    def compress_verbose_logs(self, content: str, max_length: int = 200) -> Dict[str, Any]:
        """
        Compress verbose log content to essential information
        
        Args:
            content: Log content to compress
            max_length: Maximum length of compressed content
            
        Returns:
            Compression result with summary
        """
        if len(content) <= max_length:
            return {
                'compressed_content': content,
                'compressed': False,
                'original_length': len(content),
                'compression_ratio': 0.0
            }
        
        # Extract key information from logs
        lines = content.split('\n')
        
        # Identify important log elements
        important_lines = []
        error_lines = []
        summary_info = []
        
        for line in lines:
            line_lower = line.lower()
            
            # Capture errors and warnings
            if any(keyword in line_lower for keyword in ['error', 'exception', 'warning', 'failed']):
                error_lines.append(line.strip())
            
            # Capture important status changes
            elif any(keyword in line_lower for keyword in ['started', 'completed', 'initialized', 'finished']):
                important_lines.append(line.strip())
            
            # Capture summary information
            elif any(keyword in line_lower for keyword in ['total', 'summary', 'result', 'final']):
                summary_info.append(line.strip())
        
        # Build compressed content
        compressed_parts = []
        
        if error_lines:
            compressed_parts.append(f"Errors: {'; '.join(error_lines[:2])}")
        
        if important_lines:
            compressed_parts.append(f"Status: {'; '.join(important_lines[:2])}")
        
        if summary_info:
            compressed_parts.append(f"Summary: {'; '.join(summary_info[:1])}")
        
        if not compressed_parts:
            # Fallback to first and last lines
            if len(lines) > 2:
                compressed_parts.append(f"Start: {lines[0].strip()}")
                compressed_parts.append(f"End: {lines[-1].strip()}")
            else:
                compressed_parts.append(content[:max_length])
        
        compressed_content = ' | '.join(compressed_parts)
        
        # Ensure we don't exceed max length
        if len(compressed_content) > max_length:
            compressed_content = compressed_content[:max_length-3] + "..."
        
        return {
            'compressed_content': compressed_content,
            'compressed': True,
            'original_length': len(content),
            'compressed_length': len(compressed_content),
            'compression_ratio': 1 - (len(compressed_content) / len(content)),
            'lines_processed': len(lines),
            'errors_found': len(error_lines),
            'status_updates': len(important_lines)
        }


class ReferenceAnalyzer:
    """
    Analyzes cross-references between messages to preserve referenced content
    """
    
    def __init__(self):
        """Initialize reference analyzer"""
        self.reference_patterns = [
            # File references
            re.compile(r'(?:in|from|see|check|look at|examine)\s+([/\w.-]+\.(?:py|js|ts|rs|go|java|cpp|c|h|php|rb|swift|md|txt|json|yaml|yml))', re.IGNORECASE),
            
            # Function/method references
            re.compile(r'(?:function|method|class)\s+(\w+)', re.IGNORECASE),
            re.compile(r'(\w+)(?:\(\)|\.)', re.IGNORECASE),
            
            # Variable references
            re.compile(r'(?:variable|var)\s+(\w+)', re.IGNORECASE),
            
            # Error references
            re.compile(r'(?:error|exception|issue).*?(\w+Error|\w+Exception)', re.IGNORECASE),
            
            # Tool output references
            re.compile(r'(?:output|result|shows?).*?(?:above|below|previous)', re.IGNORECASE),
            
            # Line number references
            re.compile(r'line\s+(\d+)', re.IGNORECASE),
            
            # Message references
            re.compile(r'(?:message|msg|previous|earlier).*?(\w+)', re.IGNORECASE)
        ]
    
    def analyze_cross_references(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze cross-references between messages to identify what content is referenced
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Dictionary with reference analysis results
        """
        referenced_messages = set()
        referenced_content = defaultdict(set)
        reference_graph = defaultdict(list)
        
        # Build content index for efficient searching
        content_index = self._build_content_index(messages)
        
        # Analyze each message for references
        for i, message in enumerate(messages):
            message_content = self._extract_message_text(message)
            uuid = message.get('uuid', f'msg_{i}')
            
            # Find references in this message
            references = self._find_references_in_content(message_content, content_index, messages)
            
            for ref_type, ref_data in references.items():
                for ref_uuid, ref_content in ref_data:
                    referenced_messages.add(ref_uuid)
                    referenced_content[ref_uuid].update(ref_content)
                    reference_graph[uuid].append((ref_uuid, ref_type))
        
        return {
            'referenced_messages': referenced_messages,
            'referenced_content': dict(referenced_content),
            'reference_graph': dict(reference_graph),
            'total_references': sum(len(refs) for refs in reference_graph.values()),
            'messages_with_references': len(reference_graph),
            'messages_being_referenced': len(referenced_messages)
        }
    
    def _build_content_index(self, messages: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Build searchable content index"""
        index = {}
        
        for message in messages:
            uuid = message.get('uuid', '')
            content = self._extract_message_text(message)
            
            # Extract searchable elements
            elements = {
                'full_content': content,
                'tool_name': '',
                'file_paths': [],
                'functions': [],
                'variables': [],
                'errors': []
            }
            
            # Extract tool information
            if message.get('type') == 'tool_call':
                msg_content = message.get('message', {})
                elements['tool_name'] = msg_content.get('tool', '')
                
                # Extract file paths
                params = msg_content.get('parameters', {})
                if 'file_path' in params:
                    elements['file_paths'].append(params['file_path'])
            
            # Extract code elements from content
            elements['functions'].extend(re.findall(r'\bdef\s+(\w+)\s*\(', content))
            elements['functions'].extend(re.findall(r'\bfunction\s+(\w+)\s*\(', content))
            elements['functions'].extend(re.findall(r'\bclass\s+(\w+)', content))
            
            # Extract variables
            elements['variables'].extend(re.findall(r'\b(\w+)\s*=', content))
            
            # Extract errors
            elements['errors'].extend(re.findall(r'(\w+Error|\w+Exception)', content))
            
            index[uuid] = elements
        
        return index
    
    def _extract_message_text(self, message: Dict[str, Any]) -> str:
        """Extract all text content from message"""
        text_parts = []
        
        if 'message' in message:
            msg_content = message['message']
            if isinstance(msg_content, dict):
                # Extract all text fields
                for key, value in msg_content.items():
                    if isinstance(value, str):
                        text_parts.append(value)
                    elif isinstance(value, dict):
                        # Extract from nested dictionaries
                        for nested_value in value.values():
                            if isinstance(nested_value, str):
                                text_parts.append(nested_value)
            else:
                text_parts.append(str(msg_content))
        
        return ' '.join(text_parts)
    
    def _find_references_in_content(
        self, 
        content: str, 
        content_index: Dict[str, Dict[str, Any]], 
        messages: List[Dict[str, Any]]
    ) -> Dict[str, List[Tuple[str, Set[str]]]]:
        """Find references in content using pattern matching and index lookup"""
        references = defaultdict(list)
        
        # Direct pattern matching
        for pattern in self.reference_patterns:
            matches = pattern.findall(content)
            for match in matches:
                # Find which messages contain this referenced item
                for uuid, indexed_content in content_index.items():
                    if self._content_contains_reference(match, indexed_content):
                        references['pattern_match'].append((uuid, {match}))
        
        # Contextual references (looking at previous/following messages)
        context_refs = self._find_contextual_references(content, messages)
        references.update(context_refs)
        
        return references
    
    def _content_contains_reference(self, reference: str, indexed_content: Dict[str, Any]) -> bool:
        """Check if indexed content contains the reference"""
        ref_lower = reference.lower()
        
        # Check in full content
        if ref_lower in indexed_content['full_content'].lower():
            return True
        
        # Check in specific elements
        for element_list in [indexed_content['file_paths'], indexed_content['functions'], 
                           indexed_content['variables'], indexed_content['errors']]:
            if any(ref_lower in str(item).lower() for item in element_list):
                return True
        
        return False
    
    def _find_contextual_references(self, content: str, messages: List[Dict[str, Any]]) -> Dict[str, List[Tuple[str, Set[str]]]]:
        """Find contextual references like 'the error above', 'previous output', etc."""
        references = defaultdict(list)
        
        # Look for temporal references
        if re.search(r'\b(?:above|previous|earlier|before)\b', content, re.IGNORECASE):
            # This message references something earlier
            # For now, mark the relationship but don't try to resolve specific content
            references['temporal_reference'].append(('previous_context', {'temporal_reference'}))
        
        if re.search(r'\b(?:below|next|following|after)\b', content, re.IGNORECASE):
            references['temporal_reference'].append(('following_context', {'temporal_reference'}))
        
        return references


class ChainIntegrityValidator:
    """
    Validates that conversation dependency chains remain intact after pruning
    """
    
    def __init__(self):
        """Initialize chain integrity validator"""
        pass
    
    def validate_chain_integrity(
        self, 
        original_messages: List[Dict[str, Any]], 
        pruned_messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate that conversation chains are preserved after pruning
        
        Args:
            original_messages: Original message list
            pruned_messages: Pruned message list
            
        Returns:
            Dictionary with integrity validation results
        """
        # Build UUID sets
        original_uuids = {msg['uuid'] for msg in original_messages}
        pruned_uuids = {msg['uuid'] for msg in pruned_messages}
        
        # Build parent-child maps
        original_parent_map = {msg['uuid']: msg.get('parentUuid') for msg in original_messages}
        pruned_parent_map = {msg['uuid']: msg.get('parentUuid') for msg in pruned_messages}
        
        # Find broken chains and orphaned messages
        broken_chains = []
        orphaned_messages = []
        preserved_chains = []
        
        for message in pruned_messages:
            uuid = message['uuid']
            parent_uuid = message.get('parentUuid')
            
            if parent_uuid:
                if parent_uuid not in pruned_uuids:
                    # Parent was removed - this creates an orphan
                    orphaned_messages.append({
                        'uuid': uuid,
                        'missing_parent': parent_uuid,
                        'message_type': message.get('type', 'unknown')
                    })
                else:
                    # Chain is preserved
                    preserved_chains.append((parent_uuid, uuid))
            # Root messages (no parent) are always valid
        
        # Find conversation branches that were broken
        original_chains = self._build_conversation_chains(original_messages)
        pruned_chains = self._build_conversation_chains(pruned_messages)
        
        for chain_id, original_chain in original_chains.items():
            if chain_id in pruned_chains:
                pruned_chain = pruned_chains[chain_id]
                
                # Check if chain has gaps
                gaps = self._find_chain_gaps(original_chain, pruned_chain)
                if gaps:
                    broken_chains.append({
                        'chain_id': chain_id,
                        'original_length': len(original_chain),
                        'pruned_length': len(pruned_chain),
                        'gaps': gaps
                    })
        
        # Calculate integrity metrics
        total_chains = len(original_chains)
        intact_chains = total_chains - len(broken_chains)
        
        integrity_score = intact_chains / total_chains if total_chains > 0 else 1.0
        
        return {
            'chains_preserved': len(orphaned_messages) == 0 and len(broken_chains) == 0,
            'integrity_score': integrity_score,
            'total_original_chains': total_chains,
            'intact_chains': intact_chains,
            'broken_chains': broken_chains,
            'orphaned_messages': orphaned_messages,
            'preserved_chain_count': len(preserved_chains),
            'messages_preserved': len(pruned_messages),
            'messages_removed': len(original_messages) - len(pruned_messages)
        }
    
    def _build_conversation_chains(self, messages: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Build conversation chains from messages"""
        # Find root messages (no parent)
        roots = [msg for msg in messages if not msg.get('parentUuid')]
        
        # Build chains starting from each root
        chains = {}
        
        for root in roots:
            chain = self._build_chain_from_root(root['uuid'], messages)
            if len(chain) > 1:  # Only include multi-message chains
                chains[root['uuid']] = chain
        
        return chains
    
    def _build_chain_from_root(self, root_uuid: str, messages: List[Dict[str, Any]]) -> List[str]:
        """Build conversation chain starting from root message"""
        uuid_to_msg = {msg['uuid']: msg for msg in messages}
        
        # Build children map
        children_map = defaultdict(list)
        for msg in messages:
            parent = msg.get('parentUuid')
            if parent:
                children_map[parent].append(msg['uuid'])
        
        # Traverse chain (depth-first for longest path)
        def traverse(uuid: str, path: List[str]) -> List[str]:
            current_path = path + [uuid]
            
            if uuid not in children_map:
                return current_path
            
            # Find longest path among children
            longest_path = current_path
            for child_uuid in children_map[uuid]:
                child_path = traverse(child_uuid, current_path)
                if len(child_path) > len(longest_path):
                    longest_path = child_path
            
            return longest_path
        
        return traverse(root_uuid, [])
    
    def _find_chain_gaps(self, original_chain: List[str], pruned_chain: List[str]) -> List[Dict[str, Any]]:
        """Find gaps in conversation chain after pruning"""
        gaps = []
        
        # Convert to sets for easier comparison
        original_set = set(original_chain)
        pruned_set = set(pruned_chain)
        
        # Find removed messages
        removed_messages = original_set - pruned_set
        
        if removed_messages:
            # Group consecutive removed messages
            for i, uuid in enumerate(original_chain):
                if uuid in removed_messages:
                    # Find start and end of gap
                    gap_start = i
                    gap_end = i
                    
                    while gap_end < len(original_chain) - 1 and original_chain[gap_end + 1] in removed_messages:
                        gap_end += 1
                    
                    gaps.append({
                        'start_index': gap_start,
                        'end_index': gap_end,
                        'removed_messages': original_chain[gap_start:gap_end + 1],
                        'gap_size': gap_end - gap_start + 1
                    })
                    
                    # Skip ahead past this gap
                    i = gap_end
        
        return gaps