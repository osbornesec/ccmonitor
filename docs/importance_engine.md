# importance_engine.py

## Overview

The `importance_engine.py` module provides sophisticated content analysis and importance scoring for JSONL conversation messages. It implements multi-factor analysis to determine message significance, enabling intelligent preservation decisions during conversation pruning operations.

## Features

### Content Analysis Capabilities
- **Technical content detection**: Identifies code, error messages, and technical discussions
- **Semantic importance scoring**: Analyzes content depth and complexity
- **Cross-reference tracking**: Detects and weights inter-message relationships
- **Context awareness**: Considers conversation flow and message dependencies
- **Error criticality assessment**: Special handling for error messages and solutions

### Scoring Algorithms
- **Multi-factor scoring**: Combines multiple importance indicators
- **Weighted factor system**: Configurable importance factor weights
- **Adaptive thresholds**: Dynamic adjustment based on conversation characteristics
- **Reference boost system**: Enhanced scoring for cross-referenced content
- **User interaction weighting**: Different scoring for user vs assistant messages

## Architecture

### Core Components

#### 1. Content Analysis Engine
```python
class ContentAnalysisEngine:
    """
    Main engine for analyzing message content and extracting importance signals.
    """
    
    def analyze_content_complexity(self, message_content):
        """
        Analyze technical complexity and depth of message content.
        
        Returns:
            dict: Complexity metrics including technical_depth, code_presence,
                  error_indicators, and conceptual_complexity scores
        """
```

#### 2. Importance Scoring System
```python
class ImportanceScorer:
    """
    Multi-factor importance scoring system with configurable weights.
    """
    
    def calculate_importance_score(self, message_data, context_data):
        """
        Calculate comprehensive importance score for a message.
        
        Args:
            message_data (dict): Message content and metadata
            context_data (dict): Conversation context and cross-references
            
        Returns:
            float: Importance score between 0.0 and 1.0
        """
```

#### 3. Cross-Reference Analyzer
```python
class CrossReferenceAnalyzer:
    """
    Analyzes cross-references between messages and adjusts importance accordingly.
    """
    
    def detect_cross_references(self, messages):
        """
        Detect explicit and implicit references between messages.
        """
```

## Importance Scoring Factors

### 1. Content Complexity (Weight: 0.30)
```python
def analyze_content_complexity(content):
    """
    Technical complexity analysis:
    - Code snippet detection and complexity
    - Technical terminology density
    - Conceptual depth indicators
    - Problem-solving content
    """
    complexity_score = (
        code_complexity * 0.4 +
        technical_terminology * 0.3 +
        conceptual_depth * 0.2 +
        problem_solving_indicators * 0.1
    )
    return complexity_score
```

### 2. Technical Depth (Weight: 0.25)
```python
def analyze_technical_depth(content):
    """
    Technical depth assessment:
    - Programming language usage
    - System architecture discussions
    - Error diagnostics and solutions
    - Configuration and setup instructions
    """
    depth_indicators = {
        'programming_languages': detect_programming_languages(content),
        'system_concepts': detect_system_concepts(content),
        'error_analysis': detect_error_patterns(content),
        'technical_procedures': detect_procedures(content)
    }
    return calculate_depth_score(depth_indicators)
```

### 3. Error Criticality (Weight: 0.20)
```python
def analyze_error_criticality(content):
    """
    Error message and solution analysis:
    - Error severity assessment
    - Solution effectiveness indicators
    - Debugging information presence
    - Resolution outcome tracking
    """
    error_indicators = {
        'error_severity': assess_error_severity(content),
        'solution_quality': assess_solution_quality(content),
        'debugging_info': detect_debugging_content(content),
        'resolution_success': detect_resolution_markers(content)
    }
    return calculate_error_score(error_indicators)
```

### 4. Cross-References (Weight: 0.15)
```python
def analyze_cross_references(message, conversation_context):
    """
    Cross-reference importance analysis:
    - Direct message references
    - Implicit content connections
    - Follow-up relationships
    - Reference frequency and importance
    """
    reference_score = (
        direct_references * 0.5 +
        implicit_connections * 0.3 +
        follow_up_relationships * 0.2
    )
    return reference_score
```

### 5. User Interaction (Weight: 0.10)
```python
def analyze_user_interaction(message_data):
    """
    User interaction pattern analysis:
    - User vs assistant message weighting
    - Question-answer pair identification
    - User feedback and confirmation
    - Interaction sequence importance
    """
    interaction_factors = {
        'message_type': message_data.get('type', 'assistant'),
        'user_engagement': detect_user_engagement(message_data),
        'feedback_indicators': detect_feedback_patterns(message_data),
        'sequence_position': analyze_sequence_position(message_data)
    }
    return calculate_interaction_score(interaction_factors)
```

## Content Detection Algorithms

### Code Detection
```python
def detect_code_content(content):
    """
    Sophisticated code detection with multiple strategies:
    - Syntax highlighting markers
    - Programming language patterns
    - Code block delimiters
    - Function/class/variable naming patterns
    """
    code_indicators = {
        'syntax_blocks': detect_syntax_blocks(content),
        'language_keywords': detect_language_keywords(content),
        'code_patterns': detect_code_patterns(content),
        'structured_code': detect_structured_code(content)
    }
    
    code_score = calculate_code_complexity(code_indicators)
    return {
        'has_code': any(code_indicators.values()),
        'code_complexity': code_score,
        'languages_detected': identify_languages(content),
        'code_quality': assess_code_quality(content)
    }
```

### Error Message Detection
```python
def detect_error_patterns(content):
    """
    Comprehensive error message detection:
    - Stack traces and exception patterns
    - Error keywords and phrases
    - HTTP status codes and system errors
    - Warning and critical message indicators
    """
    error_patterns = [
        r'(?i)(error|exception|traceback|stack\s+trace)',
        r'(?i)(failed|failure|unable\s+to|cannot)',
        r'(?i)(warning|critical|fatal|panic)',
        r'\b\d{3}\s+(error|not\s+found|forbidden)',
        r'(?i)(syntax\s+error|runtime\s+error|compilation\s+error)'
    ]
    
    detected_errors = []
    for pattern in error_patterns:
        matches = re.findall(pattern, content)
        detected_errors.extend(matches)
    
    return {
        'error_count': len(detected_errors),
        'error_types': classify_errors(detected_errors),
        'severity': assess_error_severity(detected_errors),
        'has_solution': detect_solution_markers(content)
    }
```

### Technical Terminology Detection
```python
def detect_technical_terminology(content):
    """
    Technical vocabulary and concept detection:
    - Programming terminology
    - System administration concepts
    - Software development practices
    - Technology-specific vocabulary
    """
    technical_dictionaries = {
        'programming': load_programming_terms(),
        'systems': load_system_terms(),
        'development': load_development_terms(),
        'networking': load_networking_terms()
    }
    
    terminology_scores = {}
    for category, terms in technical_dictionaries.items():
        matches = count_term_matches(content, terms)
        terminology_scores[category] = calculate_terminology_density(matches, content)
    
    return terminology_scores
```

## Importance Calculation Pipeline

### 1. Content Preprocessing
```python
def preprocess_message_content(message_data):
    """
    Prepare message content for analysis:
    - Text normalization and cleaning
    - Code block extraction and preservation
    - Metadata enrichment
    - Language detection
    """
    processed_content = {
        'normalized_text': normalize_text(message_data['content']),
        'code_blocks': extract_code_blocks(message_data['content']),
        'metadata': extract_metadata(message_data),
        'language': detect_primary_language(message_data['content'])
    }
    return processed_content
```

### 2. Multi-Factor Analysis
```python
def perform_multifactor_analysis(processed_content, context_data):
    """
    Execute all importance analysis factors:
    """
    analysis_results = {
        'content_complexity': analyze_content_complexity(processed_content),
        'technical_depth': analyze_technical_depth(processed_content),
        'error_criticality': analyze_error_criticality(processed_content),
        'cross_references': analyze_cross_references(processed_content, context_data),
        'user_interaction': analyze_user_interaction(processed_content)
    }
    return analysis_results
```

### 3. Score Aggregation
```python
def aggregate_importance_scores(analysis_results, factor_weights=None):
    """
    Combine individual factor scores into final importance score:
    """
    if factor_weights is None:
        factor_weights = {
            'content_complexity': 0.30,
            'technical_depth': 0.25,
            'error_criticality': 0.20,
            'cross_references': 0.15,
            'user_interaction': 0.10
        }
    
    weighted_score = sum(
        analysis_results[factor] * factor_weights[factor]
        for factor in factor_weights
    )
    
    # Normalize to 0.0-1.0 range
    final_score = max(0.0, min(1.0, weighted_score))
    return final_score
```

## Configuration and Customization

### Factor Weight Configuration
```python
# Default factor weights
DEFAULT_FACTOR_WEIGHTS = {
    'content_complexity': 0.30,
    'technical_depth': 0.25,
    'error_criticality': 0.20,
    'cross_references': 0.15,
    'user_interaction': 0.10
}

# Specialized configurations for different use cases
CONFIGURATION_PRESETS = {
    'code_focused': {
        'content_complexity': 0.40,
        'technical_depth': 0.35,
        'error_criticality': 0.15,
        'cross_references': 0.07,
        'user_interaction': 0.03
    },
    'error_focused': {
        'content_complexity': 0.20,
        'technical_depth': 0.20,
        'error_criticality': 0.45,
        'cross_references': 0.10,
        'user_interaction': 0.05
    },
    'conversation_focused': {
        'content_complexity': 0.15,
        'technical_depth': 0.15,
        'error_criticality': 0.10,
        'cross_references': 0.35,
        'user_interaction': 0.25
    }
}
```

### Custom Importance Rules
```python
def apply_custom_importance_rules(message_data, base_score):
    """
    Apply domain-specific importance rules:
    """
    adjusted_score = base_score
    
    # Boost for architectural decisions
    if detect_architectural_content(message_data['content']):
        adjusted_score *= 1.3
    
    # Boost for successful problem resolutions
    if detect_successful_resolution(message_data, conversation_context):
        adjusted_score *= 1.2
    
    # Reduce for routine confirmations
    if detect_routine_confirmation(message_data['content']):
        adjusted_score *= 0.7
    
    return min(1.0, adjusted_score)
```

## Usage Examples

### Basic Importance Analysis
```python
from importance_engine import ImportanceScorer

# Initialize scorer
scorer = ImportanceScorer()

# Analyze single message
message_data = {
    'content': 'Here is the bug fix for the authentication error: ...',
    'type': 'assistant',
    'timestamp': '2025-08-03T10:00:00Z'
}

context_data = {
    'conversation_history': previous_messages,
    'cross_references': detected_references
}

importance_score = scorer.calculate_importance_score(message_data, context_data)
print(f"Importance score: {importance_score:.3f}")
```

### Batch Processing
```python
def analyze_conversation_importance(messages):
    """
    Analyze importance for entire conversation.
    """
    scorer = ImportanceScorer()
    results = []
    
    for i, message in enumerate(messages):
        context_data = {
            'conversation_history': messages[:i],
            'cross_references': detect_references(message, messages)
        }
        
        importance = scorer.calculate_importance_score(message, context_data)
        results.append({
            'message_index': i,
            'importance_score': importance,
            'message_uuid': message.get('uuid'),
            'analysis_details': scorer.get_last_analysis_details()
        })
    
    return results
```

### Custom Configuration
```python
# Use specialized configuration
custom_weights = CONFIGURATION_PRESETS['code_focused']
scorer = ImportanceScorer(factor_weights=custom_weights)

# Add custom rules
def boost_learning_content(message_data, base_score):
    if 'learn' in message_data['content'].lower():
        return base_score * 1.1
    return base_score

scorer.add_custom_rule(boost_learning_content)
```

## Integration with Pruning Systems

### Message-Level Integration
```python
# In cleanup_and_ultra_prune.py
from importance_engine import ImportanceScorer

def analyze_message_importance(message_data, context_data):
    """
    Integrated importance analysis for pruning decisions.
    """
    scorer = ImportanceScorer()
    
    # Calculate base importance
    base_importance = scorer.calculate_importance_score(message_data, context_data)
    
    # Apply temporal decay (from temporal_analysis.py)
    age_days = calculate_message_age_days(message_data['timestamp'])
    temporal_factor = apply_temporal_decay(age_days)
    
    # Final importance with temporal adjustment
    final_importance = base_importance * temporal_factor
    
    return {
        'importance_score': final_importance,
        'base_importance': base_importance,
        'temporal_factor': temporal_factor,
        'analysis_details': scorer.get_analysis_breakdown()
    }
```

### Threshold-Based Filtering
```python
def filter_by_importance(messages, importance_threshold=0.6):
    """
    Filter messages based on importance threshold.
    """
    scorer = ImportanceScorer()
    filtered_messages = []
    
    for message in messages:
        context_data = build_context_data(message, messages)
        importance = scorer.calculate_importance_score(message, context_data)
        
        if importance >= importance_threshold:
            filtered_messages.append({
                'message': message,
                'importance': importance
            })
    
    return filtered_messages
```

## Performance Optimization

### Caching Strategies
```python
class ImportanceScorerWithCache:
    """
    Cached version of importance scorer for improved performance.
    """
    
    def __init__(self):
        self.analysis_cache = {}
        self.term_detection_cache = {}
        
    def calculate_importance_score_cached(self, message_data, context_data):
        """
        Calculate importance with caching for repeated analysis.
        """
        # Create cache key from message content hash
        content_hash = hash(message_data['content'])
        cache_key = (content_hash, hash(str(context_data)))
        
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        # Calculate if not cached
        score = self.calculate_importance_score(message_data, context_data)
        self.analysis_cache[cache_key] = score
        
        return score
```

### Batch Processing Optimization
```python
def batch_analyze_importance(messages, batch_size=100):
    """
    Optimized batch processing for large message sets.
    """
    scorer = ImportanceScorer()
    results = []
    
    # Pre-compute common analysis elements
    technical_terms = scorer.load_technical_dictionaries()
    error_patterns = scorer.compile_error_patterns()
    
    for batch_start in range(0, len(messages), batch_size):
        batch_end = min(batch_start + batch_size, len(messages))
        batch_messages = messages[batch_start:batch_end]
        
        # Batch process content analysis
        batch_results = scorer.batch_analyze_content(
            batch_messages,
            precomputed_terms=technical_terms,
            precompiled_patterns=error_patterns
        )
        
        results.extend(batch_results)
    
    return results
```

## Advanced Features

### Machine Learning Integration
```python
class MLEnhancedImportanceScorer:
    """
    Importance scorer enhanced with machine learning models.
    """
    
    def __init__(self, model_path=None):
        self.base_scorer = ImportanceScorer()
        self.ml_model = self.load_ml_model(model_path)
        
    def calculate_ml_enhanced_score(self, message_data, context_data):
        """
        Combine rule-based scoring with ML predictions.
        """
        # Get rule-based score
        rule_based_score = self.base_scorer.calculate_importance_score(
            message_data, context_data
        )
        
        # Get ML prediction
        features = self.extract_ml_features(message_data, context_data)
        ml_score = self.ml_model.predict(features)
        
        # Combine scores (weighted average)
        combined_score = (rule_based_score * 0.7) + (ml_score * 0.3)
        
        return combined_score
```

### Adaptive Threshold Learning
```python
class AdaptiveThresholdScorer:
    """
    Scorer that learns optimal thresholds from user feedback.
    """
    
    def __init__(self):
        self.feedback_history = []
        self.threshold_model = None
        
    def record_user_feedback(self, message, predicted_importance, user_rating):
        """
        Record user feedback on importance predictions.
        """
        self.feedback_history.append({
            'message_features': self.extract_features(message),
            'predicted_importance': predicted_importance,
            'user_rating': user_rating,
            'timestamp': datetime.now()
        })
        
        # Retrain threshold model periodically
        if len(self.feedback_history) % 100 == 0:
            self.retrain_threshold_model()
```

## Monitoring and Analytics

### Importance Distribution Analysis
```python
def analyze_importance_distribution(conversation_messages):
    """
    Analyze the distribution of importance scores in a conversation.
    """
    scorer = ImportanceScorer()
    scores = []
    
    for message in conversation_messages:
        context_data = build_context_data(message, conversation_messages)
        importance = scorer.calculate_importance_score(message, context_data)
        scores.append(importance)
    
    distribution_stats = {
        'mean_importance': np.mean(scores),
        'median_importance': np.median(scores),
        'std_importance': np.std(scores),
        'importance_quartiles': np.percentile(scores, [25, 50, 75]),
        'high_importance_ratio': len([s for s in scores if s > 0.7]) / len(scores),
        'low_importance_ratio': len([s for s in scores if s < 0.3]) / len(scores)
    }
    
    return distribution_stats
```

### Factor Contribution Analysis
```python
def analyze_factor_contributions(messages):
    """
    Analyze which importance factors contribute most to scoring decisions.
    """
    scorer = ImportanceScorer()
    factor_contributions = {
        'content_complexity': [],
        'technical_depth': [],
        'error_criticality': [],
        'cross_references': [],
        'user_interaction': []
    }
    
    for message in messages:
        context_data = build_context_data(message, messages)
        analysis_details = scorer.get_detailed_analysis(message, context_data)
        
        for factor, score in analysis_details['factor_scores'].items():
            factor_contributions[factor].append(score)
    
    # Calculate average contribution per factor
    avg_contributions = {
        factor: np.mean(scores) 
        for factor, scores in factor_contributions.items()
    }
    
    return avg_contributions
```

## Error Handling and Validation

### Content Validation
```python
def validate_message_content(message_data):
    """
    Validate message structure and content for importance analysis.
    """
    required_fields = ['content', 'type', 'timestamp']
    
    for field in required_fields:
        if field not in message_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate content is not empty
    if not message_data['content'].strip():
        logger.warning("Empty message content detected")
        return False
    
    # Validate timestamp format
    try:
        parse_timestamp(message_data['timestamp'])
    except ValueError:
        logger.warning(f"Invalid timestamp format: {message_data['timestamp']}")
        return False
    
    return True
```

### Graceful Degradation
```python
def safe_importance_calculation(message_data, context_data):
    """
    Importance calculation with graceful error handling.
    """
    try:
        return calculate_importance_score(message_data, context_data)
    except Exception as e:
        logger.error(f"Error calculating importance: {e}")
        
        # Return conservative default score
        return 0.5  # Medium importance as fallback
```

## Configuration Files

### YAML Configuration
```yaml
# importance_config.yaml
importance_engine:
  factor_weights:
    content_complexity: 0.30
    technical_depth: 0.25
    error_criticality: 0.20
    cross_references: 0.15
    user_interaction: 0.10
  
  content_analysis:
    enable_code_detection: true
    enable_error_detection: true
    enable_technical_terms: true
    
  thresholds:
    high_importance: 0.7
    medium_importance: 0.4
    low_importance: 0.2
    
  performance:
    enable_caching: true
    batch_size: 100
    cache_size_limit: 10000
```

## Future Enhancements

### Planned Features
- **Semantic similarity analysis**: Content similarity-based importance
- **Learning from user behavior**: Adaptive importance based on user interactions
- **Multi-language support**: Enhanced analysis for non-English content
- **Domain-specific models**: Specialized importance models for different fields

### Advanced Algorithms
- **Neural importance scoring**: Deep learning models for importance prediction
- **Graph-based analysis**: Message relationship graphs for importance propagation
- **Contextual embeddings**: Use of transformer models for content understanding
- **Real-time adaptation**: Dynamic adjustment of importance criteria

## Related Documentation
- [cleanup_and_ultra_prune.md](cleanup_and_ultra_prune.md) - Message pruning integration
- [temporal_analysis.md](temporal_analysis.md) - Temporal importance factors
- [PROJECT_README.md](PROJECT_README.md) - Project overview
- [CLI_Usage.md](CLI_Usage.md) - Command-line interface