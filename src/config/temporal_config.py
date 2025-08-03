"""
Temporal configuration for exponential decay and time-based importance weighting.

This module provides preset configurations and customization options for
different conversation types and use cases.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional
from enum import Enum

from ..temporal.decay_engine import DecayMode


@dataclass
class TemporalConfig:
    """Configuration for temporal decay parameters."""
    
    # Core decay settings
    mode: DecayMode = DecayMode.SIMPLE
    enabled: bool = True
    
    # Decay constants by content type (lower = slower decay)
    decay_constants: Dict[str, float] = field(default_factory=lambda: {
        'error_messages': 0.1,      # Slow decay - errors stay relevant
        'code_changes': 0.3,        # Medium decay - code has lasting impact  
        'status_updates': 0.8,      # Fast decay - status becomes outdated
        'debugging_info': 0.2,      # Slow decay - debugging context valuable
        'general_chat': 0.6,        # Faster decay - less critical over time
        'architectural_decisions': 0.05,  # Very slow - architecture persists
        'default': 0.4             # Default for unclassified content
    })
    
    # Time windows in hours for multi-stage decay
    time_windows: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        'ultra_recent': (0, 1),      # 0-1 hours: minimal decay
        'recent': (1, 24),           # 1-24 hours: gentle decay
        'medium': (24, 168),         # 1-7 days: moderate decay  
        'old': (168, 720),           # 1-4 weeks: strong decay
        'ancient': (720, float('inf'))  # 4+ weeks: maximum decay
    })
    
    # Decay multipliers for each time window
    window_multipliers: Dict[str, float] = field(default_factory=lambda: {
        'ultra_recent': 1.0,    # No decay
        'recent': 0.1,          # Very slow decay
        'medium': 0.5,          # Moderate decay
        'old': 1.5,             # Strong decay  
        'ancient': 3.0          # Maximum decay
    })
    
    # Reference time (None = current time)
    reference_time: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert config to dictionary for serialization."""
        return {
            'mode': self.mode.value,
            'enabled': self.enabled,
            'decay_constants': self.decay_constants,
            'time_windows': self.time_windows,
            'window_multipliers': self.window_multipliers,
            'reference_time': self.reference_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TemporalConfig':
        """Create config from dictionary."""
        config = cls()
        config.mode = DecayMode(data.get('mode', DecayMode.SIMPLE.value))
        config.enabled = data.get('enabled', True)
        config.decay_constants.update(data.get('decay_constants', {}))
        config.time_windows.update(data.get('time_windows', {}))
        config.window_multipliers.update(data.get('window_multipliers', {}))
        config.reference_time = data.get('reference_time')
        return config


# Preset configurations for different use cases
PRESET_CONFIGS = {
    'development': TemporalConfig(
        mode=DecayMode.CONTENT_AWARE,
        decay_constants={
            'error_messages': 0.05,      # Very slow - debugging sessions
            'code_changes': 0.2,         # Slow - code context important
            'status_updates': 1.0,       # Fast - less relevant in dev
            'debugging_info': 0.1,       # Very slow - debugging context
            'general_chat': 0.4,         # Medium - some context needed
            'architectural_decisions': 0.02,  # Ultra slow - critical for dev
            'default': 0.3
        },
        window_multipliers={
            'ultra_recent': 1.0,    # No decay
            'recent': 0.05,         # Very slow decay
            'medium': 0.3,          # Slow decay
            'old': 1.0,             # Moderate decay
            'ancient': 2.0          # Strong decay
        }
    ),
    
    'debugging': TemporalConfig(
        mode=DecayMode.CONTENT_AWARE,
        decay_constants={
            'error_messages': 0.02,      # Ultra slow - errors are key
            'code_changes': 0.1,         # Slow - code context critical
            'status_updates': 0.6,       # Medium - some status relevant
            'debugging_info': 0.03,      # Ultra slow - debugging gold
            'general_chat': 0.8,         # Fast - focus on technical
            'architectural_decisions': 0.05,  # Very slow - context matters
            'default': 0.4
        },
        time_windows={
            'ultra_recent': (0, 2),      # Extended recent window
            'recent': (2, 48),           # Extended recent period
            'medium': (48, 336),         # 2 weeks
            'old': (336, 1440),          # 2 months
            'ancient': (1440, float('inf'))
        }
    ),
    
    'conversation': TemporalConfig(
        mode=DecayMode.MULTI_STAGE,
        decay_constants={
            'error_messages': 0.2,       # Medium - errors less critical
            'code_changes': 0.4,         # Medium - balanced approach
            'status_updates': 1.2,       # Fast - status less important
            'debugging_info': 0.3,       # Medium - some debug context
            'general_chat': 0.5,         # Medium - conversational context
            'architectural_decisions': 0.1,  # Slow - decisions matter
            'default': 0.5
        }
    ),
    
    'analysis': TemporalConfig(
        mode=DecayMode.SIMPLE,
        decay_constants={
            'error_messages': 0.3,       # Medium - balanced analysis
            'code_changes': 0.3,         # Medium - code context
            'status_updates': 0.9,       # Fast - status not critical
            'debugging_info': 0.4,       # Medium - some debug info
            'general_chat': 0.7,         # Faster - focus on technical
            'architectural_decisions': 0.15,  # Slow - decisions important
            'default': 0.4
        }
    ),
    
    'aggressive': TemporalConfig(
        mode=DecayMode.MULTI_STAGE,
        decay_constants={
            'error_messages': 0.4,       # Faster decay
            'code_changes': 0.6,         # Faster decay
            'status_updates': 1.5,       # Very fast decay
            'debugging_info': 0.5,       # Faster decay
            'general_chat': 1.0,         # Fast decay
            'architectural_decisions': 0.3,  # Faster decay
            'default': 0.7
        },
        window_multipliers={
            'ultra_recent': 1.0,
            'recent': 0.3,          # Moderate decay even for recent
            'medium': 1.0,          # Strong decay
            'old': 2.0,             # Very strong decay
            'ancient': 4.0          # Maximum decay
        }
    ),
    
    'conservative': TemporalConfig(
        mode=DecayMode.CONTENT_AWARE,
        decay_constants={
            'error_messages': 0.02,      # Ultra slow - preserve all errors
            'code_changes': 0.1,         # Very slow - preserve code context
            'status_updates': 0.3,       # Slow - even status has value
            'debugging_info': 0.05,      # Ultra slow - debugging precious
            'general_chat': 0.2,         # Slow - conversational context
            'architectural_decisions': 0.01,  # Ultra slow - critical decisions
            'default': 0.15
        },
        window_multipliers={
            'ultra_recent': 1.0,
            'recent': 0.02,         # Ultra slow decay
            'medium': 0.1,          # Very slow decay
            'old': 0.5,             # Slow decay
            'ancient': 1.0          # Moderate decay even for old
        }
    )
}


def get_preset_config(preset_name: str) -> TemporalConfig:
    """
    Get a preset temporal configuration.
    
    Args:
        preset_name: Name of the preset ('development', 'debugging', 'conversation', 
                    'analysis', 'aggressive', 'conservative')
        
    Returns:
        TemporalConfig instance
        
    Raises:
        ValueError: If preset_name is not recognized
    """
    if preset_name not in PRESET_CONFIGS:
        available = ', '.join(PRESET_CONFIGS.keys())
        raise ValueError(f"Unknown preset '{preset_name}'. Available presets: {available}")
    
    return PRESET_CONFIGS[preset_name]


def create_custom_config(
    mode: DecayMode = DecayMode.SIMPLE,
    base_preset: str = 'development',
    **overrides
) -> TemporalConfig:
    """
    Create a custom temporal configuration based on a preset with overrides.
    
    Args:
        mode: Decay mode to use
        base_preset: Base preset to start from
        **overrides: Override values for specific parameters
        
    Returns:
        TemporalConfig instance with custom settings
    """
    config = get_preset_config(base_preset)
    config.mode = mode
    
    # Apply overrides
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f"Unknown configuration parameter: {key}")
    
    return config


def get_velocity_adjusted_config(
    base_config: TemporalConfig,
    message_frequency: float,
    conversation_length: int
) -> TemporalConfig:
    """
    Adjust temporal configuration based on conversation velocity.
    
    High-velocity conversations (many messages in short time) may need 
    slower decay to maintain context coherence.
    
    Args:
        base_config: Base temporal configuration
        message_frequency: Messages per hour
        conversation_length: Total number of messages
        
    Returns:
        Velocity-adjusted TemporalConfig
    """
    # Create a copy of the base config
    adjusted_config = TemporalConfig(
        mode=base_config.mode,
        enabled=base_config.enabled,
        decay_constants=base_config.decay_constants.copy(),
        time_windows=base_config.time_windows.copy(),
        window_multipliers=base_config.window_multipliers.copy(),
        reference_time=base_config.reference_time
    )
    
    # Calculate velocity adjustment factor
    # Higher frequency = slower decay (more compressed time perception)
    if message_frequency > 10:  # High velocity (>10 msg/hour)
        velocity_factor = 0.5  # Slow down decay by 50%
    elif message_frequency > 5:  # Medium velocity (5-10 msg/hour)
        velocity_factor = 0.7  # Slow down decay by 30%
    elif message_frequency > 1:  # Low velocity (1-5 msg/hour)
        velocity_factor = 0.9  # Slow down decay by 10%
    else:  # Very low velocity (<1 msg/hour)
        velocity_factor = 1.2  # Speed up decay by 20%
    
    # Apply velocity adjustment to decay constants
    for content_type in adjusted_config.decay_constants:
        adjusted_config.decay_constants[content_type] *= velocity_factor
    
    # Adjust time windows for very long conversations
    if conversation_length > 1000:  # Very long conversation
        # Compress time windows slightly
        compression_factor = 0.8
        for window_name, (start, end) in adjusted_config.time_windows.items():
            new_start = start * compression_factor
            new_end = end * compression_factor if end != float('inf') else end
            adjusted_config.time_windows[window_name] = (new_start, new_end)
    
    return adjusted_config