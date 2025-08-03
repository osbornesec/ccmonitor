"""
Core Pruning Engine for JSONL conversation files
Phase 2 & 3 implementation of ccmonitor pruning system

Provides intelligent content removal while preserving conversation integrity
and essential context for development workflows.

Phase 3 adds comprehensive safety measures, validation, and backup systems.
"""

from .core import JSONLPruner
from .compressor import SmartTruncator, SemanticSummarizer, ReferenceAnalyzer, ChainIntegrityValidator
from .filters import ContentFilter, CompressionRulesEngine, ContentClassifier, DebuggingPreserver
from .graph import ConversationGraphBuilder
from .safety import SafePruner, SafePruningCheckpoint, safe_pruning_context
from .validator import ValidationFramework

__all__ = [
    'JSONLPruner',
    'SmartTruncator', 
    'SemanticSummarizer',
    'ReferenceAnalyzer',
    'ChainIntegrityValidator',
    'ContentFilter',
    'CompressionRulesEngine', 
    'ContentClassifier',
    'DebuggingPreserver',
    'ConversationGraphBuilder',
    'SafePruner',
    'SafePruningCheckpoint',
    'safe_pruning_context',
    'ValidationFramework'
]

__version__ = "3.0.0"