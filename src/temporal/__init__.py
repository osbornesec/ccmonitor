"""
Temporal analysis module for JSONL conversation data.

This module provides time-based importance weighting and decay functions
for intelligent context pruning based on message age and temporal patterns.
"""

from .decay_engine import (
    ExponentialDecayEngine,
    DecayMode,
    calculate_time_delta,
    get_message_timestamp
)

__all__ = [
    'ExponentialDecayEngine',
    'DecayMode', 
    'calculate_time_delta',
    'get_message_timestamp'
]