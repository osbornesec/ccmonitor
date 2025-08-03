# temporal_analysis.py

## Overview

The `temporal_analysis.py` module provides sophisticated time-based analysis capabilities for JSONL conversation files. It implements multiple temporal decay algorithms, conversation velocity analysis, and time-based importance weighting to optimize message retention strategies.

## Features

### Temporal Decay Algorithms
- **Linear decay**: Gradual importance reduction over time
- **Exponential decay**: Rapid importance decrease with configurable rates  
- **Logarithmic decay**: Balanced decay that preserves recent content
- **Step decay**: Threshold-based importance drops at specific intervals
- **Custom decay functions**: Extensible framework for specialized algorithms

### Time Analysis Capabilities
- **Conversation velocity tracking**: Measures discussion pace and intensity
- **Activity pattern detection**: Identifies high/low activity periods
- **Temporal clustering**: Groups messages by time-based similarity
- **Age distribution analysis**: Statistical breakdown of message ages
- **Reference-aware decay**: Adjusts decay for cross-referenced content

## Architecture

### Core Components

#### 1. Temporal Decay Engine
```python
class TemporalDecayEngine:
    """
    Main engine for applying time-based importance modifications.
    Supports multiple decay algorithms with configurable parameters.
    """
    
    def apply_temporal_decay(self, importance_score, age_days, decay_mode='exponential'):
        """
        Apply temporal decay to importance scores based on message age.
        
        Args:
            importance_score (float): Original importance (0.0-1.0)
            age_days (float): Message age in days
            decay_mode (str): Algorithm to use for decay calculation
            
        Returns:
            float: Adjusted importance score with temporal decay applied
        """
```

#### 2. Conversation Velocity Analyzer
```python
class ConversationVelocityAnalyzer:
    """
    Analyzes conversation pace and adjusts temporal parameters accordingly.
    High-velocity conversations may preserve more recent content.
    """
    
    def calculate_velocity_metrics(self, messages):
        """
        Calculate conversation velocity and intensity metrics.
        
        Returns:
            dict: Velocity statistics including messages/hour, peak periods,
                  activity patterns, and conversation intensity scores
        """
```

#### 3. Reference-Aware Temporal Analysis
```python
def analyze_temporal_references(messages, reference_boost=0.3):
    """
    Adjust temporal decay for messages that are cross-referenced.
    Referenced content gets reduced decay to preserve context.
    """
```

## Temporal Decay Algorithms

### 1. Linear Decay
```python
def linear_decay(importance_score, age_days, decay_rate=0.1):
    """
    Linear reduction in importance over time.
    Formula: score * (1 - min(age_days * decay_rate, 1.0))
    
    Characteristics:
    - Predictable, steady decay
    - Good for uniform content aging
    - Easy to understand and configure
    """
```

### 2. Exponential Decay
```python
def exponential_decay(importance_score, age_days, decay_rate=0.1):
    """
    Exponential reduction emphasizing recent content.
    Formula: score * exp(-age_days * decay_rate)
    
    Characteristics:
    - Rapid decay for older content
    - Strong preservation of recent messages
    - Natural modeling of human memory patterns
    """
```

### 3. Logarithmic Decay
```python
def logarithmic_decay(importance_score, age_days, decay_rate=0.2):
    """
    Logarithmic decay providing balanced retention.
    Formula: score * (1 - log(1 + age_days * decay_rate))
    
    Characteristics:
    - Balanced approach between linear and exponential
    - Good for conversations with varying importance over time
    - Preserves some older content while emphasizing recent
    """
```

### 4. Step Decay
```python
def step_decay(importance_score, age_days, steps=[(7, 0.8), (30, 0.5), (90, 0.2)]):
    """
    Threshold-based decay with discrete importance levels.
    
    Characteristics:
    - Clear importance boundaries
    - Configurable time thresholds
    - Good for policy-based retention
    """
```

## Conversation Velocity Analysis

### Velocity Metrics
```python
velocity_metrics = {
    'messages_per_hour': float,      # Average message frequency
    'peak_activity_periods': list,   # High-activity time windows
    'conversation_intensity': float, # Overall discussion intensity (0.0-1.0)
    'activity_distribution': dict,   # Hourly/daily activity patterns
    'burst_detection': list,         # Rapid-fire conversation periods
    'idle_periods': list             # Low/no activity periods
}
```

### Velocity-Based Adjustments
- **High velocity conversations**: Preserve more recent content, apply gentler decay
- **Steady-pace conversations**: Use standard decay parameters
- **Burst conversations**: Identify and preserve burst periods
- **Idle conversations**: Apply more aggressive decay to fill periods

## Time-Based Configuration

### Decay Presets
```python
DECAY_PRESETS = {
    'conservative': {
        'mode': 'logarithmic',
        'decay_rate': 0.1,
        'preserve_threshold': 0.3
    },
    'balanced': {
        'mode': 'exponential', 
        'decay_rate': 0.15,
        'preserve_threshold': 0.4
    },
    'aggressive': {
        'mode': 'exponential',
        'decay_rate': 0.3,
        'preserve_threshold': 0.6
    },
    'policy_based': {
        'mode': 'step',
        'steps': [(7, 0.8), (30, 0.5), (90, 0.2)],
        'preserve_threshold': 0.5
    }
}
```

### Custom Configuration
```python
temporal_config = {
    'decay_algorithm': 'exponential',
    'decay_rate': 0.2,
    'min_importance_threshold': 0.1,
    'reference_boost': 0.3,
    'velocity_adjustment': True,
    'conversation_context_window': 24,  # hours
    'preserve_recent_threshold': 2      # days
}
```

## Usage Examples

### Basic Temporal Decay
```python
from temporal_analysis import TemporalDecayEngine

# Initialize decay engine
decay_engine = TemporalDecayEngine()

# Apply exponential decay to importance scores
original_score = 0.8
age_days = 14
decayed_score = decay_engine.apply_temporal_decay(
    importance_score=original_score,
    age_days=age_days,
    decay_mode='exponential',
    decay_rate=0.1
)

print(f"Original: {original_score}, Decayed: {decayed_score:.3f}")
# Output: Original: 0.8, Decayed: 0.197
```

### Conversation Velocity Analysis
```python
from temporal_analysis import ConversationVelocityAnalyzer

# Analyze conversation patterns
velocity_analyzer = ConversationVelocityAnalyzer()
messages = load_conversation_messages("conversation.jsonl")

velocity_metrics = velocity_analyzer.calculate_velocity_metrics(messages)
print(f"Messages per hour: {velocity_metrics['messages_per_hour']:.2f}")
print(f"Conversation intensity: {velocity_metrics['conversation_intensity']:.2f}")
```

### Reference-Aware Temporal Analysis  
```python
from temporal_analysis import analyze_temporal_references

# Apply reference-aware decay
messages_with_references = analyze_temporal_references(
    messages=conversation_messages,
    reference_boost=0.3  # 30% decay reduction for referenced content
)

# Referenced messages will have slower decay rates
```

### Preset-Based Configuration
```python
from temporal_analysis import apply_temporal_preset

# Use predefined configuration
result = apply_temporal_preset(
    messages=conversation_messages,
    preset='balanced',
    custom_overrides={'decay_rate': 0.12}
)
```

## Integration with Pruning Systems

### Message-Level Integration
```python
# In cleanup_and_ultra_prune.py
from temporal_analysis import TemporalDecayEngine

def analyze_message_importance_with_temporal(message_data, context_data):
    # Calculate base importance
    base_importance = calculate_base_importance(message_data, context_data)
    
    # Apply temporal decay
    age_days = calculate_message_age_days(message_data['timestamp'])
    decay_engine = TemporalDecayEngine()
    
    final_importance = decay_engine.apply_temporal_decay(
        importance_score=base_importance,
        age_days=age_days,
        decay_mode='exponential',
        decay_rate=0.15
    )
    
    return final_importance
```

### Velocity-Adjusted Processing
```python
def velocity_adjusted_pruning(messages, target_reduction=0.8):
    # Analyze conversation velocity
    velocity_analyzer = ConversationVelocityAnalyzer()
    velocity_metrics = velocity_analyzer.calculate_velocity_metrics(messages)
    
    # Adjust pruning parameters based on velocity
    if velocity_metrics['conversation_intensity'] > 0.7:
        # High-intensity conversation - preserve more content
        adjusted_reduction = target_reduction * 0.8
        decay_rate = 0.1
    else:
        # Normal conversation - standard pruning
        adjusted_reduction = target_reduction
        decay_rate = 0.15
    
    return apply_temporal_pruning(messages, adjusted_reduction, decay_rate)
```

## Advanced Features

### Time Window Analysis
```python
def analyze_time_windows(messages, window_size_hours=24):
    """
    Analyze conversation activity in time windows.
    Identify periods of high/low activity for targeted preservation.
    """
    windows = []
    current_window = []
    
    for message in messages:
        # Group messages by time windows
        # Calculate activity metrics for each window
        # Identify patterns and anomalies
    
    return {
        'high_activity_windows': high_activity_periods,
        'low_activity_windows': low_activity_periods, 
        'activity_distribution': window_statistics
    }
```

### Contextual Decay Adjustment
```python
def contextual_decay_adjustment(message, conversation_context):
    """
    Adjust decay based on conversation context:
    - Technical discussions: Slower decay
    - Error resolution: Preserve error-solution pairs
    - Code review: Maintain code-comment relationships
    """
    base_decay_rate = 0.15
    
    # Technical content adjustment
    if detect_technical_content(message):
        decay_rate = base_decay_rate * 0.7
    
    # Error-solution pair preservation
    if is_error_resolution_sequence(message, conversation_context):
        decay_rate = base_decay_rate * 0.5
        
    return decay_rate
```

### Adaptive Temporal Parameters
```python
class AdaptiveTemporalEngine:
    """
    Automatically adjusts temporal parameters based on conversation characteristics.
    """
    
    def auto_configure_temporal_params(self, messages):
        """
        Analyze conversation to determine optimal temporal parameters.
        """
        # Analyze conversation patterns
        velocity_metrics = self.analyze_velocity(messages)
        content_metrics = self.analyze_content_distribution(messages)
        reference_metrics = self.analyze_reference_patterns(messages)
        
        # Determine optimal configuration
        optimal_config = self.calculate_optimal_params(
            velocity_metrics,
            content_metrics, 
            reference_metrics
        )
        
        return optimal_config
```

## Performance Optimization

### Efficient Timestamp Processing
```python
def efficient_age_calculation(messages):
    """
    Optimized age calculation for large message sets.
    Uses vectorized operations and caching.
    """
    current_time = datetime.now(timezone.utc)
    
    # Vectorized age calculation
    timestamps = [parse_timestamp(msg['timestamp']) for msg in messages]
    age_deltas = [(current_time - ts).total_seconds() / 86400 for ts in timestamps]
    
    return age_deltas
```

### Caching Strategies
```python
class TemporalAnalysisCache:
    """
    Cache temporal analysis results to avoid recomputation.
    """
    
    def __init__(self):
        self.velocity_cache = {}
        self.decay_cache = {}
        
    def get_cached_velocity(self, conversation_hash):
        """Get cached velocity metrics if available."""
        return self.velocity_cache.get(conversation_hash)
        
    def cache_decay_result(self, message_hash, decay_params, result):
        """Cache decay calculation results."""
        cache_key = (message_hash, tuple(decay_params.items()))
        self.decay_cache[cache_key] = result
```

## Monitoring and Analytics

### Temporal Analysis Metrics
```python
temporal_analytics = {
    'average_message_age': float,
    'age_distribution': {
        '0-1_days': int,
        '1-7_days': int, 
        '7-30_days': int,
        '30+_days': int
    },
    'decay_effectiveness': float,      # How much importance was reduced
    'preservation_rate': float,        # Percentage of content preserved
    'velocity_classification': str,    # slow/medium/fast/burst
    'temporal_compression_ratio': float # Size reduction from temporal pruning
}
```

### Performance Metrics
```python
performance_metrics = {
    'temporal_analysis_time': float,   # Seconds for temporal analysis
    'decay_calculation_time': float,   # Time for decay calculations
    'velocity_analysis_time': float,   # Time for velocity analysis
    'cache_hit_rate': float,          # Efficiency of caching
    'messages_processed_per_second': float
}
```

## Error Handling and Edge Cases

### Timestamp Validation
```python
def validate_and_parse_timestamp(timestamp_str):
    """
    Robust timestamp parsing with multiple format support.
    """
    supported_formats = [
        '%Y-%m-%dT%H:%M:%S.%fZ',      # ISO format with microseconds
        '%Y-%m-%dT%H:%M:%SZ',         # ISO format without microseconds
        '%Y-%m-%d %H:%M:%S',          # Standard datetime format
        '%Y-%m-%d'                    # Date only
    ]
    
    for fmt in supported_formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
            
    # Fallback: current time for unparseable timestamps
    logger.warning(f"Could not parse timestamp: {timestamp_str}")
    return datetime.now(timezone.utc)
```

### Boundary Condition Handling
```python
def safe_decay_calculation(importance_score, age_days, decay_rate):
    """
    Safe decay calculation with boundary checks.
    """
    # Validate inputs
    importance_score = max(0.0, min(1.0, importance_score))
    age_days = max(0.0, age_days)
    decay_rate = max(0.0, min(1.0, decay_rate))
    
    # Calculate decay with overflow protection
    decay_factor = math.exp(-age_days * decay_rate)
    result = importance_score * decay_factor
    
    # Ensure result is in valid range
    return max(0.0, min(1.0, result))
```

## Configuration Files

### YAML Configuration
```yaml
# temporal_config.yaml
temporal_analysis:
  default_decay_mode: "exponential"
  default_decay_rate: 0.15
  
  presets:
    conservative:
      decay_mode: "logarithmic"
      decay_rate: 0.1
      preserve_threshold: 0.3
    
    aggressive:
      decay_mode: "exponential" 
      decay_rate: 0.3
      preserve_threshold: 0.6

  velocity_analysis:
    enable_velocity_adjustment: true
    velocity_window_hours: 24
    intensity_threshold: 0.7
    
  reference_awareness:
    enable_reference_boost: true
    reference_boost_factor: 0.3
    cross_reference_detection: true
```

## Future Enhancements

### Planned Features
- **Machine learning-based decay**: Learn optimal decay patterns from user behavior
- **Semantic temporal analysis**: Adjust decay based on content semantic similarity
- **Multi-conversation temporal correlation**: Cross-conversation temporal patterns
- **Predictive temporal modeling**: Forecast future conversation patterns

### Advanced Algorithms
- **Attention-based temporal weighting**: Use attention mechanisms for importance
- **Contextual temporal clustering**: Group messages by temporal and semantic similarity
- **Dynamic decay rate adjustment**: Real-time optimization of decay parameters
- **Temporal anomaly detection**: Identify unusual temporal patterns

## Related Documentation
- [cleanup_and_ultra_prune.md](cleanup_and_ultra_prune.md) - Message pruning integration
- [importance_engine.md](importance_engine.md) - Importance scoring system
- [PROJECT_README.md](PROJECT_README.md) - Project overview
- [CLI_Usage.md](CLI_Usage.md) - Command-line interface