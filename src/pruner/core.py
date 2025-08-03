"""
Core JSONLPruner implementation
Phase 2 - Central pruning system with configurable levels and context preservation
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, Counter

# Import Phase 1 validated components
from ..jsonl_analysis.analyzer import JSONLAnalyzer, ConversationFlowAnalyzer
from ..jsonl_analysis.scoring import ImportanceScorer, MessageScoreAnalyzer
from ..jsonl_analysis.patterns import PatternAnalyzer
from ..jsonl_analysis.exceptions import InvalidJSONLError
from ..temporal.decay_engine import DecayMode, analyze_conversation_velocity

# Import Phase 2 components
from .compressor import SmartTruncator, SemanticSummarizer, ReferenceAnalyzer, ChainIntegrityValidator
from .filters import ContentFilter, CompressionRulesEngine, ContentClassifier, DebuggingPreserver
from .graph import ConversationGraphBuilder

logger = logging.getLogger(__name__)


class JSONLPruner:
    """
    Core pruning engine that intelligently removes redundant content while preserving
    essential conversation context and maintaining conversation flow integrity.
    
    Features:
    - Configurable pruning levels (light/medium/aggressive)
    - Context-aware compression algorithms
    - Pattern-based content filtering
    - Conversation dependency preservation
    - Streaming processing for large files
    - Performance targets: <1s for 1000 messages, <100MB memory
    """
    
    def __init__(self, pruning_level: str = 'medium', custom_weights: Optional[Dict[str, int]] = None,
                 temporal_decay: bool = False, decay_mode: DecayMode = DecayMode.SIMPLE,
                 conversation_context: Optional[Dict[str, Any]] = None):
        """
        Initialize pruner with specified configuration
        
        Args:
            pruning_level: Pruning aggressiveness ('light', 'medium', 'aggressive')
            custom_weights: Optional custom importance weights
            temporal_decay: Enable temporal decay for time-based importance weighting
            decay_mode: Temporal decay mode to use
            conversation_context: Conversation velocity and analysis context
            
        Raises:
            ValueError: If pruning_level is invalid
        """
        # Validate pruning level
        valid_levels = ['light', 'medium', 'aggressive', 'ultra']
        if pruning_level not in valid_levels:
            raise ValueError(f"Invalid pruning level: {pruning_level}. Must be one of: {valid_levels}")
        
        self.pruning_level = pruning_level
        
        # Set importance thresholds based on pruning level
        self.importance_threshold = {
            'light': 20,      # Keep messages with score >= 20
            'medium': 40,     # Keep messages with score >= 40  
            'aggressive': 60, # Keep messages with score >= 60
            'ultra': 80       # Keep messages with score >= 80 (only highest value content)
        }[pruning_level]
        
        # Ultra mode bypasses safety mechanisms for maximum compression
        self.ultra_mode = (pruning_level == 'ultra')
        
        # Store temporal decay settings
        self.temporal_decay = temporal_decay
        self.decay_mode = decay_mode
        self.conversation_context = conversation_context
        
        # Initialize Phase 1 components
        self.analyzer = JSONLAnalyzer()
        self.flow_analyzer = ConversationFlowAnalyzer()
        self.importance_scorer = ImportanceScorer(
            weights=custom_weights, 
            temporal_decay=temporal_decay, 
            decay_mode=decay_mode
        )
        self.score_analyzer = MessageScoreAnalyzer(self.importance_scorer)
        self.pattern_analyzer = PatternAnalyzer()
        
        # Initialize Phase 2 components
        self.content_filter = ContentFilter()
        self.compression_rules = CompressionRulesEngine()
        self.content_classifier = ContentClassifier()
        self.debugging_preserver = DebuggingPreserver()
        self.graph_builder = ConversationGraphBuilder()
        
        # Initialize compressors
        self.smart_truncator = SmartTruncator()
        self.semantic_summarizer = SemanticSummarizer()
        self.reference_analyzer = ReferenceAnalyzer()
        self.chain_validator = ChainIntegrityValidator()
        
        # Processing statistics
        self.stats = {
            'messages_processed': 0,
            'messages_preserved': 0,
            'messages_removed': 0,
            'messages_compressed': 0,
            'malformed_entries': 0,
            'processing_time': 0.0,
            'compression_ratio': 0.0
        }
    
    def process_file(self, input_path: Path, output_path: Path) -> Dict[str, Any]:
        """
        Process JSONL file with intelligent pruning and compression
        
        Args:
            input_path: Path to input JSONL file
            output_path: Path to output pruned JSONL file
            
        Returns:
            Dictionary with processing statistics and metrics
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            InvalidJSONLError: If input file is malformed
        """
        start_time = time.perf_counter()
        
        try:
            # Load and validate messages
            logger.info(f"Loading messages from {input_path}")
            messages = self._load_messages_streaming(input_path)
            
            if not messages:
                logger.warning("No valid messages found in input file")
                self._write_empty_output(output_path)
                return self._get_stats(time.perf_counter() - start_time)
            
            # Analyze conversation velocity for temporal decay (if not already provided)
            if self.temporal_decay and not self.conversation_context:
                logger.info("Analyzing conversation velocity for temporal decay")
                self.conversation_context = analyze_conversation_velocity(messages)
                logger.info(f"Conversation velocity: {self.conversation_context['message_frequency']:.2f} msg/hour")
            
            # Update importance scorer with conversation context if temporal decay is enabled
            if self.temporal_decay and self.conversation_context:
                logger.info(f"Temporal decay enabled with {len(self.conversation_context.get('current_topics', []))} active topics")
            
            # Build conversation graph for dependency analysis
            logger.info("Building conversation graph")
            conversation_graph = self.graph_builder.build_graph(messages)
            
            # Analyze cross-references to preserve referenced content
            logger.info("Analyzing cross-references")
            references = self.reference_analyzer.analyze_cross_references(messages)
            
            # Identify important messages using multiple criteria
            logger.info("Identifying important messages")
            important_messages = self._identify_important_messages(messages, conversation_graph, references)
            
            # Apply context-aware pruning with dependency preservation
            logger.info("Applying context-aware pruning")
            pruned_messages = self._prune_with_context_preservation(
                messages, important_messages, conversation_graph, references
            )
            
            # Apply content compression to remaining messages
            logger.info("Applying content compression")
            compressed_messages = self._apply_content_compression(pruned_messages)
            
            # Validate conversation integrity (optional for performance)
            integrity_result = {'chains_preserved': True}  # Skip for now to avoid recursion issues
            if len(messages) < 100:  # Only validate small conversations for now
                logger.info("Validating conversation integrity")
                try:
                    integrity_result = self.chain_validator.validate_chain_integrity(messages, compressed_messages)
                    
                    if not integrity_result['chains_preserved']:
                        logger.warning("Conversation integrity issues detected")
                        # Could implement fallback strategy here
                except Exception as e:
                    logger.warning(f"Chain validation failed: {e}")
                    integrity_result = {'chains_preserved': False, 'error': str(e)}
            
            # Write optimized output
            logger.info(f"Writing pruned output to {output_path}")
            self._save_jsonl_optimized(compressed_messages, output_path)
            
            # Calculate final statistics
            processing_time = time.perf_counter() - start_time
            return self._calculate_final_stats(messages, compressed_messages, processing_time)
            
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            raise
    
    def process_file_streaming(self, input_path: Path, output_path: Path, chunk_size: int = 1000) -> Dict[str, Any]:
        """
        Process very large files using streaming to manage memory usage
        
        Args:
            input_path: Path to input JSONL file
            output_path: Path to output pruned JSONL file  
            chunk_size: Number of messages to process in each chunk
            
        Returns:
            Dictionary with processing statistics
        """
        start_time = time.perf_counter()
        total_stats = {
            'messages_processed': 0,
            'messages_preserved': 0,
            'messages_removed': 0,
            'messages_compressed': 0,
            'malformed_entries': 0
        }
        
        logger.info(f"Streaming processing with chunk size {chunk_size}")
        
        with open(output_path, 'w', encoding='utf-8') as output_file:
            chunk_messages = []
            
            # Process file in chunks
            with open(input_path, 'r', encoding='utf-8') as input_file:
                for line_num, line in enumerate(input_file, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        message = json.loads(line)
                        if self.analyzer.validate_entry_structure(message):
                            chunk_messages.append(message)
                        else:
                            total_stats['malformed_entries'] += 1
                            
                    except json.JSONDecodeError:
                        total_stats['malformed_entries'] += 1
                        continue
                    
                    # Process chunk when full
                    if len(chunk_messages) >= chunk_size:
                        chunk_stats = self._process_chunk(chunk_messages, output_file)
                        self._update_total_stats(total_stats, chunk_stats)
                        chunk_messages = []
                
                # Process final chunk
                if chunk_messages:
                    chunk_stats = self._process_chunk(chunk_messages, output_file)
                    self._update_total_stats(total_stats, chunk_stats)
        
        # Calculate final results
        processing_time = time.perf_counter() - start_time
        total_stats['processing_time'] = processing_time
        
        if total_stats['messages_processed'] > 0:
            total_stats['compression_ratio'] = total_stats['messages_removed'] / total_stats['messages_processed']
        else:
            total_stats['compression_ratio'] = 0.0
        
        logger.info(f"Streaming processing completed in {processing_time:.3f}s")
        return total_stats
    
    def _load_messages_streaming(self, input_path: Path) -> List[Dict[str, Any]]:
        """Load messages from JSONL file with error handling"""
        try:
            messages = self.analyzer.parse_jsonl_file(input_path)
            self.stats['messages_processed'] = len(messages)
            return messages
        except InvalidJSONLError as e:
            logger.error(f"Invalid JSONL file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading file: {e}")
            raise InvalidJSONLError(f"Failed to load JSONL file: {e}")
    
    def _identify_important_messages(
        self, 
        messages: List[Dict[str, Any]], 
        conversation_graph: Dict[str, Any],
        references: Dict[str, Any]
    ) -> Set[str]:
        """
        Identify important messages using multiple criteria:
        1. Importance scoring algorithm
        2. Conversation dependency analysis (unless ultra mode)
        3. Cross-reference preservation (unless ultra mode)
        4. Pattern-based classification (unless ultra mode)
        """
        important_uuids = set()
        
        # 1. Apply importance scoring threshold
        for message in messages:
            # Pass conversation context for temporal decay if enabled
            if self.temporal_decay and self.conversation_context:
                # For temporal decay, we need to temporarily update the scorer's decay engine context
                if hasattr(self.importance_scorer, 'decay_engine') and self.importance_scorer.decay_engine:
                    score = self.importance_scorer.decay_engine.calculate_decay_factor(
                        message, conversation_context=self.conversation_context
                    )
                    base_score = self.importance_scorer.calculate_message_importance(message, apply_temporal_decay=False)
                    score = base_score * score
                else:
                    score = self.importance_scorer.calculate_message_importance(message)
            else:
                score = self.importance_scorer.calculate_message_importance(message)
                
            if score >= self.importance_threshold:
                important_uuids.add(message['uuid'])
        
        # Ultra mode: ONLY use importance scores - bypass all safety mechanisms
        if self.ultra_mode:
            logger.info(f"Ultra mode: Using only importance scores, identified {len(important_uuids)} important messages out of {len(messages)}")
            return important_uuids
        
        # Standard modes: Apply additional preservation mechanisms
        
        # 2. Add messages in dependency chains of important messages
        dependency_preserved = self._get_dependency_preserved_messages(important_uuids, conversation_graph)
        important_uuids.update(dependency_preserved)
        
        # 3. Add cross-referenced messages
        if 'referenced_messages' in references:
            important_uuids.update(references['referenced_messages'])
        
        # 4. Add debugging and error-related messages
        for message in messages:
            if self.debugging_preserver.should_preserve(message):
                important_uuids.add(message['uuid'])
        
        # 5. Apply content classification override
        for message in messages:
            classification = self.content_classifier.classify_content_type(message)
            if classification == 'essential':
                important_uuids.add(message['uuid'])
        
        logger.info(f"Standard mode: Identified {len(important_uuids)} important messages out of {len(messages)} (including safety mechanisms)")
        return important_uuids
    
    def _get_dependency_preserved_messages(
        self, 
        important_uuids: Set[str], 
        conversation_graph: Dict[str, Any]
    ) -> Set[str]:
        """Get all messages that need to be preserved to maintain conversation chains"""
        preserved = set()
        
        # For each important message, preserve its ancestry chain
        for uuid in important_uuids:
            # Preserve parent chain
            current = uuid
            while current and current in conversation_graph:
                preserved.add(current)
                parent = conversation_graph[current].get('parent')
                if parent and parent in conversation_graph:
                    current = parent
                else:
                    break
            
            # Preserve essential children (responses to important questions)
            if current in conversation_graph:
                children = conversation_graph[current].get('children', [])
                for child_uuid in children:
                    if child_uuid in conversation_graph:
                        child_entry = conversation_graph[child_uuid]['entry']
                        # Preserve assistant responses to user questions
                        if child_entry.get('type') == 'assistant':
                            preserved.add(child_uuid)
        
        return preserved
    
    def _prune_with_context_preservation(
        self,
        messages: List[Dict[str, Any]],
        important_uuids: Set[str],
        conversation_graph: Dict[str, Any],
        references: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply pruning while preserving conversation context and dependencies"""
        preserved_messages = []
        
        for message in messages:
            uuid = message['uuid']
            
            # Always preserve important messages
            if uuid in important_uuids:
                preserved_messages.append(message)
                continue
            
            # Apply content filtering rules
            classification = self.content_filter.classify_message(message)
            
            if classification['category'] == 'high_importance':
                preserved_messages.append(message)
            elif classification['category'] == 'medium_importance':
                # Apply compression rules for medium importance
                compression_rule = self.compression_rules.get_compression_rule(message)
                if compression_rule['action'] == 'preserve':
                    preserved_messages.append(message)
                elif compression_rule['action'] == 'compress':
                    # Apply smart compression
                    compressed_message = self._apply_smart_compression(message, compression_rule)
                    preserved_messages.append(compressed_message)
                # else: remove message
            # Low importance messages are removed unless they have special significance
        
        self.stats['messages_preserved'] = len(preserved_messages)
        self.stats['messages_removed'] = len(messages) - len(preserved_messages)
        
        return preserved_messages
    
    def _apply_content_compression(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply content compression to reduce message sizes"""
        compressed_messages = []
        
        for message in messages:
            # Check if message needs compression
            compression_rule = self.compression_rules.get_compression_rule(message)
            
            if compression_rule['action'] == 'compress_heavily':
                compressed_message = self._apply_heavy_compression(message)
                compressed_messages.append(compressed_message)
                self.stats['messages_compressed'] += 1
            elif compression_rule['action'] == 'compress':
                compressed_message = self._apply_smart_compression(message, compression_rule)
                compressed_messages.append(compressed_message)
                self.stats['messages_compressed'] += 1
            else:
                compressed_messages.append(message)
        
        return compressed_messages
    
    def _apply_smart_compression(self, message: Dict[str, Any], compression_rule: Dict[str, Any]) -> Dict[str, Any]:
        """Apply smart compression based on content type and rules"""
        compressed_message = message.copy()
        
        # Extract message content
        if 'message' in compressed_message and isinstance(compressed_message['message'], dict):
            msg_content = compressed_message['message']
            
            # Compress large tool results
            if 'result' in msg_content and msg_content['result']:
                result_content = str(msg_content['result'])
                if len(result_content) > 1000:  # Compress large results
                    compressed_result = self.smart_truncator.truncate_content(
                        result_content, 
                        max_length=500,
                        preserve_lines=3
                    )
                    msg_content['result'] = compressed_result
            
            # Compress verbose content
            if 'content' in msg_content and msg_content['content']:
                content = str(msg_content['content'])
                if len(content) > 2000:  # Compress very long content
                    compressed_content = self.smart_truncator.truncate_content(
                        content,
                        max_length=1000,
                        preserve_lines=5
                    )
                    msg_content['content'] = compressed_content
        
        return compressed_message
    
    def _apply_heavy_compression(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Apply heavy compression for low-value content"""
        compressed_message = message.copy()
        
        # For system messages and hooks, create minimal summary
        if message.get('type') == 'system':
            content = message.get('message', {}).get('content', '')
            if 'hook' in content.lower():
                # Create hook summary
                compressed_message['message'] = {
                    'content': f"[HOOK SUMMARY] {content[:50]}..." if len(content) > 50 else content,
                    'original_length': len(content),
                    'compressed': True
                }
        
        return compressed_message
    
    def _process_chunk(self, chunk_messages: List[Dict[str, Any]], output_file) -> Dict[str, Any]:
        """Process a chunk of messages for streaming mode"""
        chunk_stats = {
            'messages_processed': len(chunk_messages),
            'messages_preserved': 0,
            'messages_removed': 0,
            'messages_compressed': 0
        }
        
        # Quick processing for streaming (simplified for performance)
        preserved_messages = []
        
        for message in chunk_messages:
            # Apply temporal decay if enabled (same logic as main method)
            if self.temporal_decay and self.conversation_context:
                if hasattr(self.importance_scorer, 'decay_engine') and self.importance_scorer.decay_engine:
                    decay_factor = self.importance_scorer.decay_engine.calculate_decay_factor(
                        message, conversation_context=self.conversation_context
                    )
                    base_score = self.importance_scorer.calculate_message_importance(message, apply_temporal_decay=False)
                    score = base_score * decay_factor
                else:
                    score = self.importance_scorer.calculate_message_importance(message)
            else:
                score = self.importance_scorer.calculate_message_importance(message)
            
            if score >= self.importance_threshold:
                preserved_messages.append(message)
            elif score >= self.importance_threshold - 20:  # Compression zone
                compressed_message = self._apply_smart_compression(
                    message, 
                    {'action': 'compress', 'compression_ratio': 0.5}
                )
                preserved_messages.append(compressed_message)
                chunk_stats['messages_compressed'] += 1
            # else: remove message
        
        chunk_stats['messages_preserved'] = len(preserved_messages)
        chunk_stats['messages_removed'] = chunk_stats['messages_processed'] - chunk_stats['messages_preserved']
        
        # Write chunk to output
        for message in preserved_messages:
            json.dump(message, output_file)
            output_file.write('\n')
        
        return chunk_stats
    
    def _update_total_stats(self, total_stats: Dict[str, Any], chunk_stats: Dict[str, Any]):
        """Update total statistics with chunk results"""
        for key in ['messages_processed', 'messages_preserved', 'messages_removed', 'messages_compressed']:
            total_stats[key] += chunk_stats[key]
    
    def _save_jsonl_optimized(self, messages: List[Dict[str, Any]], output_path: Path):
        """Save messages to JSONL file with optimized I/O"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for message in messages:
                    json.dump(message, f, separators=(',', ':'))  # Compact JSON
                    f.write('\n')
            
            logger.info(f"Successfully wrote {len(messages)} messages to {output_path}")
            
        except Exception as e:
            logger.error(f"Error writing output file: {e}")
            raise
    
    def _write_empty_output(self, output_path: Path):
        """Write empty output file"""
        output_path.touch()
        logger.info(f"Created empty output file at {output_path}")
    
    def _calculate_final_stats(
        self, 
        original_messages: List[Dict[str, Any]], 
        final_messages: List[Dict[str, Any]], 
        processing_time: float
    ) -> Dict[str, Any]:
        """Calculate final processing statistics"""
        stats = {
            'messages_processed': len(original_messages),
            'messages_preserved': len(final_messages),
            'messages_removed': len(original_messages) - len(final_messages),
            'messages_compressed': self.stats['messages_compressed'],
            'malformed_entries': self.stats['malformed_entries'],
            'processing_time': processing_time,
            'compression_ratio': (len(original_messages) - len(final_messages)) / len(original_messages) if original_messages else 0.0,
            'pruning_level': self.pruning_level,
            'importance_threshold': self.importance_threshold
        }
        
        # Calculate file size metrics if possible
        try:
            original_size = sum(len(json.dumps(msg)) for msg in original_messages)
            final_size = sum(len(json.dumps(msg)) for msg in final_messages)
            stats['size_reduction_ratio'] = (original_size - final_size) / original_size if original_size > 0 else 0.0
            stats['original_size_bytes'] = original_size
            stats['final_size_bytes'] = final_size
        except Exception:
            # If size calculation fails, skip it
            pass
        
        logger.info(f"Processing complete: {stats['compression_ratio']:.2f} compression ratio in {processing_time:.3f}s")
        return stats
    
    def _get_stats(self, processing_time: float) -> Dict[str, Any]:
        """Get current statistics"""
        stats = self.stats.copy()
        stats['processing_time'] = processing_time
        return stats