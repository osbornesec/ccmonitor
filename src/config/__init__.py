"""
Configuration module for JSONL conversation processing.

This module provides configuration management for various components
including temporal decay, pruning options, and processing parameters.
"""

from .temporal_config import (
    TemporalConfig,
    get_preset_config,
    PRESET_CONFIGS
)

__all__ = [
    'TemporalConfig',
    'get_preset_config', 
    'PRESET_CONFIGS'
]