"""
Statistics and reporting system for claude-prune CLI
Phase 4.3 - Comprehensive analytics and report generation
"""

import json
import csv
import time
import statistics
import logging
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from html import escape

from .utils import format_size, format_duration, is_jsonl_file
from ..jsonl_analysis.analyzer import JSONLAnalyzer
from ..jsonl_analysis.scoring import ImportanceScorer, MessageScoreAnalyzer
from ..jsonl_analysis.patterns import PatternAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Data structure for analysis results"""
    
    file_path: str
    total_messages: int
    message_types: Dict[str, int]
    average_message_length: float
    total_characters: int
    file_size_bytes: int
    analysis_time: float
    timestamp: str
    
    # Optional detailed analysis
    importance_distribution: Optional[Dict[str, int]] = None
    compression_potential: Optional[Dict[str, Dict[str, Any]]] = None
    patterns_detected: Optional[Dict[str, Any]] = None
    temporal_analysis: Optional[Dict[str, Any]] = None
    content_categories: Optional[Dict[str, Any]] = None


class TrendAnalyzer:
    """Analyzer for temporal trends and patterns in conversations"""
    
    def __init__(self):
        self.pattern_analyzer = PatternAnalyzer()
    
    def analyze_temporal_patterns(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze temporal patterns in message data
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Dictionary with temporal analysis results
        """
        timestamps = []
        hourly_distribution = defaultdict(int)
        daily_distribution = defaultdict(int)
        
        for message in messages:
            timestamp = message.get('timestamp')
            if timestamp:
                try:
                    # Handle various timestamp formats
                    if isinstance(timestamp, str):
                        if timestamp.endswith('Z'):
                            dt = datetime.fromisoformat(timestamp[:-1] + '+00:00')
                        else:
                            dt = datetime.fromisoformat(timestamp)
                    elif isinstance(timestamp, (int, float)):
                        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                    else:
                        continue
                    
                    timestamps.append(dt)
                    hourly_distribution[dt.hour] += 1
                    daily_distribution[dt.strftime('%Y-%m-%d')] += 1
                    
                except (ValueError, TypeError) as e:
                    logger.debug(f"Failed to parse timestamp {timestamp}: {e}")
                    continue
        
        if not timestamps:
            return {
                'hourly_distribution': {},
                'daily_distribution': {},
                'peak_hours': [],
                'message_frequency_trend': 'insufficient_data',
                'conversation_duration': 0,
                'active_days': 0
            }
        
        # Calculate patterns
        sorted_timestamps = sorted(timestamps)
        conversation_duration = (sorted_timestamps[-1] - sorted_timestamps[0]).total_seconds()
        
        # Find peak hours
        peak_hours = sorted(hourly_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Calculate activity frequency
        total_days = len(daily_distribution)
        avg_messages_per_day = len(messages) / max(total_days, 1)
        
        return {
            'hourly_distribution': dict(hourly_distribution),
            'daily_distribution': dict(daily_distribution),
            'peak_hours': [hour for hour, count in peak_hours],
            'peak_hour_counts': dict(peak_hours),
            'conversation_duration': conversation_duration,
            'active_days': total_days,
            'average_messages_per_day': avg_messages_per_day,
            'message_frequency_trend': self._calculate_frequency_trend(timestamps),
            'first_message': sorted_timestamps[0].isoformat() if timestamps else None,
            'last_message': sorted_timestamps[-1].isoformat() if timestamps else None
        }
    
    def analyze_conversation_flow(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze conversation flow and interaction patterns
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Dictionary with conversation flow analysis
        """
        user_messages = [m for m in messages if m.get('type') == 'user']
        assistant_messages = [m for m in messages if m.get('type') == 'assistant']
        system_messages = [m for m in messages if m.get('type') == 'system']
        
        # Calculate response times
        response_times = []
        interaction_patterns = []
        
        prev_message = None
        for message in messages:
            if prev_message:
                # Track interaction type transitions
                transition = f"{prev_message.get('type', 'unknown')} -> {message.get('type', 'unknown')}"
                interaction_patterns.append(transition)
                
                # Calculate response time if both have timestamps
                if (prev_message.get('timestamp') and message.get('timestamp') and
                    prev_message.get('type') == 'user' and message.get('type') == 'assistant'):
                    try:
                        prev_time = self._parse_timestamp(prev_message['timestamp'])
                        curr_time = self._parse_timestamp(message['timestamp'])
                        if prev_time and curr_time:
                            response_time = (curr_time - prev_time).total_seconds()
                            if 0 < response_time < 3600:  # Reasonable response time
                                response_times.append(response_time)
                    except Exception:
                        pass
            
            prev_message = message
        
        # Analyze interaction patterns
        pattern_counts = Counter(interaction_patterns)
        
        # Calculate conversation breaks (gaps > 1 hour)
        conversation_breaks = self._detect_conversation_breaks(messages)
        
        return {
            'user_assistant_ratio': len(user_messages) / max(len(assistant_messages), 1),
            'total_user_messages': len(user_messages),
            'total_assistant_messages': len(assistant_messages),
            'total_system_messages': len(system_messages),
            'average_response_time': statistics.mean(response_times) if response_times else 0,
            'median_response_time': statistics.median(response_times) if response_times else 0,
            'response_time_std': statistics.stdev(response_times) if len(response_times) > 1 else 0,
            'conversation_breaks': conversation_breaks,
            'interaction_patterns': dict(pattern_counts),
            'most_common_transitions': pattern_counts.most_common(5)
        }
    
    def detect_content_evolution(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect how content and topics evolve throughout the conversation
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Dictionary with content evolution analysis
        """
        # Extract content from messages
        contents = []
        timestamps = []
        
        for message in messages:
            content = message.get('message', {}).get('content', '')
            timestamp = message.get('timestamp')
            
            if content and timestamp:
                contents.append(content)
                timestamps.append(self._parse_timestamp(timestamp))
        
        if len(contents) < 2:
            return {
                'topic_progression': 'insufficient_data',
                'content_complexity_trend': 'insufficient_data',
                'keyword_frequency_changes': {}
            }
        
        # Analyze content complexity over time
        complexity_scores = []
        for content in contents:
            # Simple complexity metrics
            word_count = len(content.split())
            unique_words = len(set(content.lower().split()))
            avg_word_length = sum(len(word) for word in content.split()) / max(word_count, 1)
            
            complexity = {
                'word_count': word_count,
                'unique_words': unique_words,
                'vocabulary_richness': unique_words / max(word_count, 1),
                'average_word_length': avg_word_length,
                'character_count': len(content),
                'code_blocks': content.count('```'),
                'technical_terms': self._count_technical_terms(content)
            }
            complexity_scores.append(complexity)
        
        # Calculate trends
        word_count_trend = self._calculate_trend([c['word_count'] for c in complexity_scores])
        complexity_trend = self._calculate_trend([c['vocabulary_richness'] for c in complexity_scores])
        
        # Topic progression analysis
        topic_keywords = self._extract_topic_keywords(contents)
        
        return {
            'content_complexity_trend': complexity_trend,
            'word_count_trend': word_count_trend,
            'average_complexity': {
                'word_count': statistics.mean([c['word_count'] for c in complexity_scores]),
                'vocabulary_richness': statistics.mean([c['vocabulary_richness'] for c in complexity_scores]),
                'technical_content': statistics.mean([c['technical_terms'] for c in complexity_scores])
            },
            'keyword_frequency_changes': topic_keywords,
            'topic_progression': self._analyze_topic_progression(contents)
        }
    
    def predict_compression_benefits(self, messages: List[Dict[str, Any]], 
                                   historical_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Predict compression benefits based on content analysis
        
        Args:
            messages: List of message dictionaries
            historical_data: Optional historical compression data
            
        Returns:
            Dictionary with compression benefit predictions
        """
        # Analyze content characteristics
        system_ratio = len([m for m in messages if m.get('type') == 'system']) / len(messages)
        repetitive_content = self._analyze_repetitive_content(messages)
        verbose_content = self._analyze_verbose_content(messages)
        
        # Calculate risk factors
        important_content_ratio = self._estimate_important_content_ratio(messages)
        dependency_complexity = self._analyze_dependency_complexity(messages)
        
        # Predict optimal pruning level
        if system_ratio > 0.3 and repetitive_content > 0.4:
            recommended_level = 'aggressive'
            expected_reduction = 0.6
        elif verbose_content > 0.5 and important_content_ratio < 0.7:
            recommended_level = 'medium'
            expected_reduction = 0.4
        else:
            recommended_level = 'light'
            expected_reduction = 0.2
        
        # Risk assessment
        risk_factors = []
        if dependency_complexity > 0.7:
            risk_factors.append('high_dependency_complexity')
        if important_content_ratio > 0.8:
            risk_factors.append('high_important_content_ratio')
        if len(messages) < 50:
            risk_factors.append('small_conversation_size')
        
        risk_level = 'high' if len(risk_factors) > 1 else 'medium' if risk_factors else 'low'
        
        return {
            'recommended_pruning_level': recommended_level,
            'expected_size_reduction': expected_reduction,
            'risk_assessment': {
                'level': risk_level,
                'factors': risk_factors,
                'confidence': 0.8 if len(messages) > 100 else 0.6
            },
            'content_analysis': {
                'system_message_ratio': system_ratio,
                'repetitive_content_ratio': repetitive_content,
                'verbose_content_ratio': verbose_content,
                'important_content_ratio': important_content_ratio
            },
            'optimal_schedule': self._suggest_optimal_schedule(messages, historical_data)
        }
    
    def _parse_timestamp(self, timestamp: Union[str, int, float]) -> Optional[datetime]:
        """Parse various timestamp formats"""
        try:
            if isinstance(timestamp, str):
                if timestamp.endswith('Z'):
                    return datetime.fromisoformat(timestamp[:-1] + '+00:00')
                else:
                    return datetime.fromisoformat(timestamp)
            elif isinstance(timestamp, (int, float)):
                return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except (ValueError, TypeError):
            return None
        return None
    
    def _calculate_frequency_trend(self, timestamps: List[datetime]) -> str:
        """Calculate message frequency trend"""
        if len(timestamps) < 10:
            return 'insufficient_data'
        
        # Calculate messages per hour for trend analysis
        hourly_counts = defaultdict(int)
        for ts in timestamps:
            hour_key = ts.replace(minute=0, second=0, microsecond=0)
            hourly_counts[hour_key] += 1
        
        counts = list(hourly_counts.values())
        if len(counts) < 3:
            return 'stable'
        
        # Simple trend calculation
        first_half = statistics.mean(counts[:len(counts)//2])
        second_half = statistics.mean(counts[len(counts)//2:])
        
        if second_half > first_half * 1.2:
            return 'increasing'
        elif second_half < first_half * 0.8:
            return 'decreasing'
        else:
            return 'stable'
    
    def _detect_conversation_breaks(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect breaks in conversation (gaps > 1 hour)"""
        breaks = []
        timestamps = []
        
        for message in messages:
            timestamp = self._parse_timestamp(message.get('timestamp'))
            if timestamp:
                timestamps.append((timestamp, message))
        
        timestamps.sort(key=lambda x: x[0])
        
        for i in range(1, len(timestamps)):
            prev_time, prev_msg = timestamps[i-1]
            curr_time, curr_msg = timestamps[i]
            
            gap = (curr_time - prev_time).total_seconds()
            if gap > 3600:  # 1 hour gap
                breaks.append({
                    'start_message': prev_msg.get('uuid'),
                    'end_message': curr_msg.get('uuid'),
                    'gap_duration': gap,
                    'gap_hours': gap / 3600
                })
        
        return breaks
    
    def _count_technical_terms(self, content: str) -> int:
        """Count technical terms in content"""
        technical_patterns = [
            r'\b(?:function|class|method|variable|array|object|string|integer|boolean)\b',
            r'\b(?:API|HTTP|JSON|XML|SQL|database|server|client)\b',
            r'\b(?:algorithm|optimization|performance|efficiency|scalability)\b',
            r'```[^`]*```',  # Code blocks
            r'\b[A-Z][a-zA-Z]*Error\b',  # Error types
            r'\b(?:import|from|def|class|return|if|else|for|while)\b'  # Python keywords
        ]
        
        count = 0
        for pattern in technical_patterns:
            import re
            count += len(re.findall(pattern, content, re.IGNORECASE))
        
        return count
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from list of values"""
        if len(values) < 3:
            return 'insufficient_data'
        
        # Simple linear trend calculation
        n = len(values)
        x_mean = n / 2
        y_mean = statistics.mean(values)
        
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 'stable'
        
        slope = numerator / denominator
        
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def _extract_topic_keywords(self, contents: List[str]) -> Dict[str, Any]:
        """Extract and track topic keywords over time"""
        import re
        
        # Simple keyword extraction
        all_words = []
        for content in contents:
            words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
            all_words.extend(words)
        
        # Count frequency
        word_counts = Counter(all_words)
        
        # Filter common words
        common_words = {'that', 'this', 'with', 'have', 'will', 'from', 'they', 'been', 'were', 'said', 'each', 'which', 'their', 'time', 'more', 'very', 'what', 'know', 'just', 'first', 'into', 'over', 'also', 'after', 'back', 'other', 'many', 'than', 'then', 'them', 'these', 'some', 'would', 'make', 'like', 'him', 'has', 'had', 'her', 'or', 'an', 'my', 'me', 'as', 'be', 'on', 'at', 'by', 'it', 'to', 'of', 'and', 'a', 'the', 'is', 'you', 'are', 'for', 'all', 'any', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'man', 'men', 'put', 'say', 'she', 'too', 'use'}
        
        filtered_words = {word: count for word, count in word_counts.items() 
                         if word not in common_words and count > 1}
        
        return {
            'top_keywords': dict(Counter(filtered_words).most_common(20)),
            'total_unique_words': len(word_counts),
            'vocabulary_size': len(filtered_words)
        }
    
    def _analyze_topic_progression(self, contents: List[str]) -> str:
        """Analyze how topics progress through the conversation"""
        if len(contents) < 5:
            return 'insufficient_data'
        
        # Simple topic progression analysis
        # Could be enhanced with more sophisticated NLP
        
        # Look for patterns in content evolution
        first_quarter = contents[:len(contents)//4]
        last_quarter = contents[-len(contents)//4:]
        
        first_keywords = self._extract_simple_keywords(' '.join(first_quarter))
        last_keywords = self._extract_simple_keywords(' '.join(last_quarter))
        
        overlap = len(set(first_keywords) & set(last_keywords))
        total_unique = len(set(first_keywords) | set(last_keywords))
        
        if total_unique == 0:
            return 'stable'
        
        overlap_ratio = overlap / total_unique
        
        if overlap_ratio > 0.7:
            return 'focused'  # Topics remain similar
        elif overlap_ratio < 0.3:
            return 'divergent'  # Topics change significantly
        else:
            return 'evolving'  # Topics evolve gradually
    
    def _extract_simple_keywords(self, text: str) -> List[str]:
        """Extract simple keywords from text"""
        import re
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        return [word for word in words if len(word) > 3]
    
    def _analyze_repetitive_content(self, messages: List[Dict[str, Any]]) -> float:
        """Analyze ratio of repetitive content"""
        contents = [m.get('message', {}).get('content', '') for m in messages]
        
        if len(contents) < 2:
            return 0.0
        
        # Look for repeated phrases and system messages
        repeated_count = 0
        seen_contents = set()
        
        for content in contents:
            if content in seen_contents:
                repeated_count += 1
            else:
                seen_contents.add(content)
        
        return repeated_count / len(contents)
    
    def _analyze_verbose_content(self, messages: List[Dict[str, Any]]) -> float:
        """Analyze ratio of verbose content that could be compressed"""
        verbose_count = 0
        
        for message in messages:
            content = message.get('message', {}).get('content', '')
            
            # Consider verbose if:
            # - Very long content (>2000 chars)
            # - Contains lots of code blocks
            # - System messages with verbose output
            
            is_verbose = (
                len(content) > 2000 or
                content.count('```') > 2 or
                (message.get('type') == 'system' and len(content) > 500)
            )
            
            if is_verbose:
                verbose_count += 1
        
        return verbose_count / len(messages) if messages else 0.0
    
    def _estimate_important_content_ratio(self, messages: List[Dict[str, Any]]) -> float:
        """Estimate ratio of important content"""
        # This is a simplified estimation
        # Could use the actual ImportanceScorer for more accuracy
        
        important_count = 0
        
        for message in messages:
            msg_type = message.get('type', '')
            content = message.get('message', {}).get('content', '')
            
            # Consider important if:
            # - User questions
            # - Assistant responses with code or detailed explanations
            # - Error messages or debugging content
            
            is_important = (
                msg_type == 'user' or
                (msg_type == 'assistant' and ('```' in content or len(content) > 200)) or
                'error' in content.lower() or
                'exception' in content.lower()
            )
            
            if is_important:
                important_count += 1
        
        return important_count / len(messages) if messages else 0.0
    
    def _analyze_dependency_complexity(self, messages: List[Dict[str, Any]]) -> float:
        """Analyze complexity of message dependencies"""
        # Simple dependency analysis based on message references
        # Could be enhanced with actual conversation graph analysis
        
        reference_count = 0
        for message in messages:
            content = message.get('message', {}).get('content', '')
            
            # Look for references to previous messages
            if any(phrase in content.lower() for phrase in [
                'as mentioned', 'previously', 'earlier', 'above', 
                'before', 'following up', 'regarding'
            ]):
                reference_count += 1
        
        return reference_count / len(messages) if messages else 0.0
    
    def _suggest_optimal_schedule(self, messages: List[Dict[str, Any]], 
                                historical_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Suggest optimal pruning schedule"""
        # Analyze message patterns to suggest schedule
        timestamps = [self._parse_timestamp(m.get('timestamp')) for m in messages if m.get('timestamp')]
        timestamps = [ts for ts in timestamps if ts is not None]
        
        if not timestamps:
            return {
                'recommended_frequency': 'weekly',
                'confidence': 'low',
                'reasoning': 'no_timestamp_data'
            }
        
        # Calculate activity patterns
        timestamps.sort()
        if len(timestamps) > 1:
            span_days = (timestamps[-1] - timestamps[0]).days
            messages_per_day = len(messages) / max(span_days, 1)
        else:
            messages_per_day = 1
        
        # Suggest schedule based on activity
        if messages_per_day > 50:
            return {
                'recommended_frequency': 'daily',
                'confidence': 'high',
                'reasoning': 'high_message_volume'
            }
        elif messages_per_day > 10:
            return {
                'recommended_frequency': 'weekly',
                'confidence': 'medium',
                'reasoning': 'moderate_message_volume'
            }
        else:
            return {
                'recommended_frequency': 'monthly',
                'confidence': 'medium',
                'reasoning': 'low_message_volume'
            }


class ReportFormatter:
    """Formatter for generating reports in various formats"""
    
    def __init__(self):
        self.trend_analyzer = TrendAnalyzer()
    
    def format_table(self, stats: Dict[str, Any]) -> str:
        """Format statistics as a readable table"""
        output = []
        output.append("=" * 60)
        output.append("JSONL ANALYSIS REPORT")
        output.append("=" * 60)
        output.append("")
        
        # Basic statistics
        output.append("BASIC STATISTICS")
        output.append("-" * 20)
        output.append(f"Total Messages:      {stats.get('total_messages', 0):,}")
        
        if 'message_types' in stats:
            output.append("Message Types:")
            for msg_type, count in stats['message_types'].items():
                output.append(f"  {msg_type.capitalize():12} {count:,}")
        
        output.append(f"Average Length:      {stats.get('average_message_length', 0):.1f} characters")
        output.append(f"Total Characters:    {stats.get('total_characters', 0):,}")
        
        if 'file_size_bytes' in stats:
            output.append(f"File Size:           {format_size(stats['file_size_bytes'])}")
        
        output.append("")
        
        # Compression potential
        if 'compression_potential' in stats:
            output.append("COMPRESSION POTENTIAL")
            output.append("-" * 25)
            for level, data in stats['compression_potential'].items():
                ratio = data.get('ratio', 0) * 100
                size_reduction = data.get('size_reduction', 0)
                output.append(f"{level.capitalize():12} {ratio:5.1f}% reduction ({format_size(size_reduction)})")
            output.append("")
        
        # Patterns detected
        if 'patterns_detected' in stats:
            patterns = stats['patterns_detected']
            output.append("CONTENT PATTERNS")
            output.append("-" * 20)
            
            if patterns.get('code_blocks', 0) > 0:
                output.append(f"Code Blocks:         {patterns['code_blocks']:,}")
            if patterns.get('urls', 0) > 0:
                output.append(f"URLs:                {patterns['urls']:,}")
            if patterns.get('file_paths', 0) > 0:
                output.append(f"File Paths:          {patterns['file_paths']:,}")
            
            output.append("")
        
        # Temporal analysis
        if 'temporal_analysis' in stats:
            temporal = stats['temporal_analysis']
            output.append("TEMPORAL ANALYSIS")
            output.append("-" * 20)
            
            if temporal.get('conversation_duration', 0) > 0:
                duration = temporal['conversation_duration']
                output.append(f"Duration:            {format_duration(duration)}")
            
            if temporal.get('peak_hours'):
                peak_hours = ', '.join(map(str, temporal['peak_hours']))
                output.append(f"Peak Hours:          {peak_hours}")
            
            if 'message_frequency_trend' in temporal:
                output.append(f"Frequency Trend:     {temporal['message_frequency_trend']}")
            
            output.append("")
        
        # Performance info
        if 'analysis_time' in stats:
            output.append("ANALYSIS PERFORMANCE")
            output.append("-" * 25)
            output.append(f"Analysis Time:       {stats['analysis_time']:.3f} seconds")
            output.append(f"Messages/Second:     {stats.get('total_messages', 0) / max(stats['analysis_time'], 0.001):,.0f}")
            output.append("")
        
        return "\n".join(output)
    
    def format_json(self, stats: Dict[str, Any]) -> str:
        """Format statistics as JSON"""
        # Ensure all data is JSON serializable
        json_stats = self._make_json_serializable(stats)
        return json.dumps(json_stats, indent=2, sort_keys=True)
    
    def format_csv(self, stats: Dict[str, Any]) -> str:
        """Format statistics as CSV"""
        output = []
        output.append("metric,value,category")
        
        # Basic metrics
        output.append(f"total_messages,{stats.get('total_messages', 0)},basic")
        output.append(f"average_message_length,{stats.get('average_message_length', 0):.2f},basic")
        output.append(f"total_characters,{stats.get('total_characters', 0)},basic")
        
        if 'file_size_bytes' in stats:
            output.append(f"file_size_bytes,{stats['file_size_bytes']},basic")
        
        # Message types
        if 'message_types' in stats:
            for msg_type, count in stats['message_types'].items():
                output.append(f"messages_{msg_type},{count},message_types")
        
        # Compression potential
        if 'compression_potential' in stats:
            for level, data in stats['compression_potential'].items():
                ratio = data.get('ratio', 0)
                size_reduction = data.get('size_reduction', 0)
                output.append(f"compression_ratio_{level},{ratio:.3f},compression")
                output.append(f"size_reduction_{level},{size_reduction},compression")
        
        # Patterns
        if 'patterns_detected' in stats:
            patterns = stats['patterns_detected']
            for pattern_type, count in patterns.items():
                output.append(f"pattern_{pattern_type},{count},patterns")
        
        # Performance
        if 'analysis_time' in stats:
            output.append(f"analysis_time,{stats['analysis_time']:.3f},performance")
        
        return "\n".join(output)
    
    def format_html(self, stats: Dict[str, Any]) -> str:
        """Format statistics as HTML report"""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html lang='en'>")
        html.append("<head>")
        html.append("    <meta charset='UTF-8'>")
        html.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html.append("    <title>JSONL Analysis Report</title>")
        html.append("    <style>")
        html.append(self._get_html_styles())
        html.append("    </style>")
        html.append("</head>")
        html.append("<body>")
        html.append("    <div class='container'>")
        html.append("        <h1>JSONL Analysis Report</h1>")
        
        # Basic statistics
        html.append("        <div class='section'>")
        html.append("            <h2>Basic Statistics</h2>")
        html.append("            <div class='stats-grid'>")
        html.append(f"                <div class='stat'><span class='label'>Total Messages:</span> <span class='value'>{stats.get('total_messages', 0):,}</span></div>")
        html.append(f"                <div class='stat'><span class='label'>Average Length:</span> <span class='value'>{stats.get('average_message_length', 0):.1f} chars</span></div>")
        html.append(f"                <div class='stat'><span class='label'>Total Characters:</span> <span class='value'>{stats.get('total_characters', 0):,}</span></div>")
        
        if 'file_size_bytes' in stats:
            html.append(f"                <div class='stat'><span class='label'>File Size:</span> <span class='value'>{format_size(stats['file_size_bytes'])}</span></div>")
        
        html.append("            </div>")
        html.append("        </div>")
        
        # Message types
        if 'message_types' in stats:
            html.append("        <div class='section'>")
            html.append("            <h2>Message Types</h2>")
            html.append("            <div class='stats-grid'>")
            for msg_type, count in stats['message_types'].items():
                html.append(f"                <div class='stat'><span class='label'>{msg_type.capitalize()}:</span> <span class='value'>{count:,}</span></div>")
            html.append("            </div>")
            html.append("        </div>")
        
        # Compression potential
        if 'compression_potential' in stats:
            html.append("        <div class='section'>")
            html.append("            <h2>Compression Potential</h2>")
            html.append("            <div class='compression-table'>")
            html.append("                <table>")
            html.append("                    <tr><th>Level</th><th>Reduction</th><th>Size Saved</th></tr>")
            for level, data in stats['compression_potential'].items():
                ratio = data.get('ratio', 0) * 100
                size_reduction = data.get('size_reduction', 0)
                html.append(f"                    <tr><td>{level.capitalize()}</td><td>{ratio:.1f}%</td><td>{format_size(size_reduction)}</td></tr>")
            html.append("                </table>")
            html.append("            </div>")
            html.append("        </div>")
        
        # Performance
        if 'analysis_time' in stats:
            html.append("        <div class='section'>")
            html.append("            <h2>Analysis Performance</h2>")
            html.append("            <div class='stats-grid'>")
            html.append(f"                <div class='stat'><span class='label'>Analysis Time:</span> <span class='value'>{stats['analysis_time']:.3f} seconds</span></div>")
            messages_per_sec = stats.get('total_messages', 0) / max(stats['analysis_time'], 0.001)
            html.append(f"                <div class='stat'><span class='label'>Messages/Second:</span> <span class='value'>{messages_per_sec:,.0f}</span></div>")
            html.append("            </div>")
            html.append("        </div>")
        
        html.append("    </div>")
        html.append("</body>")
        html.append("</html>")
        
        return "\n".join(html)
    
    def display_interactive(self, stats: Dict[str, Any]):
        """Display interactive report (for CLI usage)"""
        # For CLI, just print the table format
        print(self.format_table(stats))
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """Convert object to JSON serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return self._make_json_serializable(obj.__dict__)
        else:
            return obj
    
    def _get_html_styles(self) -> str:
        """Get CSS styles for HTML report"""
        return """
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            background-color: #fafafa;
            border-radius: 5px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .stat {
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #3498db;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .label {
            font-weight: bold;
            color: #555;
        }
        .value {
            color: #2c3e50;
            font-size: 1.1em;
            font-weight: bold;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            background-color: white;
            border-radius: 5px;
            overflow: hidden;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        """


class StatisticsGenerator:
    """Main statistics generator for JSONL files and directories"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.analyzer = JSONLAnalyzer()
        self.importance_scorer = ImportanceScorer()
        self.score_analyzer = MessageScoreAnalyzer(self.importance_scorer)
        self.pattern_analyzer = PatternAnalyzer()
        self.trend_analyzer = TrendAnalyzer()
        self.formatter = ReportFormatter()
        
        if verbose:
            logger.setLevel(logging.DEBUG)
    
    def analyze_file(self, file_path: Path, include_trends: bool = False, 
                    include_patterns: bool = False, include_importance: bool = False) -> Dict[str, Any]:
        """
        Analyze a single JSONL file
        
        Args:
            file_path: Path to JSONL file
            include_trends: Whether to include trend analysis
            include_patterns: Whether to include pattern analysis
            include_importance: Whether to include importance analysis
            
        Returns:
            Dictionary with analysis results
        """
        start_time = time.time()
        
        if self.verbose:
            logger.info(f"Analyzing file: {file_path}")
        
        try:
            # Load messages
            messages = self.analyzer.parse_jsonl_file(file_path)
            
            if not messages:
                logger.warning(f"No messages found in {file_path}")
                return self._create_empty_result(str(file_path), time.time() - start_time)
            
            # Basic statistics
            result = self._calculate_basic_statistics(messages, file_path)
            
            # Optional analyses
            if include_importance:
                result['importance_distribution'] = self._analyze_importance_distribution(messages)
                result['compression_potential'] = self._analyze_compression_potential(messages)
            
            if include_patterns:
                result['patterns_detected'] = self._analyze_patterns(messages)
                result['content_categories'] = self._categorize_content(messages)
            
            if include_trends:
                result['temporal_analysis'] = self.trend_analyzer.analyze_temporal_patterns(messages)
                result['conversation_flow'] = self.trend_analyzer.analyze_conversation_flow(messages)
                result['content_evolution'] = self.trend_analyzer.detect_content_evolution(messages)
                result['compression_recommendations'] = self.trend_analyzer.predict_compression_benefits(messages)
            
            # Add performance metadata
            analysis_time = time.time() - start_time
            result['analysis_time'] = analysis_time
            result['analysis_performance'] = {
                'processing_time': analysis_time,
                'messages_per_second': len(messages) / max(analysis_time, 0.001),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            if self.verbose:
                logger.info(f"Analysis complete: {len(messages)} messages in {analysis_time:.3f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            raise
    
    def analyze_directory(self, directory: Path, recursive: bool = False, 
                         include_trends: bool = False, include_patterns: bool = False,
                         include_importance: bool = False) -> Dict[str, Any]:
        """
        Analyze all JSONL files in a directory
        
        Args:
            directory: Directory to analyze
            recursive: Whether to search recursively
            include_trends: Whether to include trend analysis
            include_patterns: Whether to include pattern analysis
            include_importance: Whether to include importance analysis
            
        Returns:
            Dictionary with aggregated analysis results
        """
        start_time = time.time()
        
        if self.verbose:
            logger.info(f"Analyzing directory: {directory} (recursive: {recursive})")
        
        # Discover JSONL files
        if recursive:
            jsonl_files = list(directory.rglob("*.jsonl"))
        else:
            jsonl_files = list(directory.glob("*.jsonl"))
        
        # Filter valid JSONL files
        valid_files = [f for f in jsonl_files if is_jsonl_file(f)]
        
        if not valid_files:
            logger.warning(f"No JSONL files found in {directory}")
            return {
                'total_files': 0,
                'total_messages': 0,
                'per_file_stats': [],
                'aggregated_stats': {},
                'analysis_time': time.time() - start_time
            }
        
        logger.info(f"Found {len(valid_files)} JSONL files to analyze")
        
        # Analyze each file
        per_file_stats = []
        all_messages = []
        total_size = 0
        
        for file_path in valid_files:
            try:
                file_stats = self.analyze_file(
                    file_path,
                    include_trends=include_trends,
                    include_patterns=include_patterns,
                    include_importance=include_importance
                )
                per_file_stats.append(file_stats)
                
                # Collect messages for aggregated analysis
                file_messages = self.analyzer.parse_jsonl_file(file_path)
                all_messages.extend(file_messages)
                total_size += file_path.stat().st_size
                
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
                # Add error entry
                per_file_stats.append({
                    'file_path': str(file_path),
                    'error': str(e),
                    'total_messages': 0,
                    'analysis_time': 0
                })
        
        # Calculate aggregated statistics
        aggregated_stats = self._calculate_aggregated_statistics(per_file_stats, all_messages, total_size)
        
        analysis_time = time.time() - start_time
        
        result = {
            'total_files': len(valid_files),
            'total_messages': len(all_messages),
            'per_file_stats': per_file_stats,
            'aggregated_stats': aggregated_stats,
            'analysis_time': analysis_time,
            'directory': str(directory),
            'recursive': recursive,
            'file_diversity': self._analyze_file_diversity(per_file_stats),
            'cross_file_patterns': self._analyze_cross_file_patterns(per_file_stats) if include_patterns else None
        }
        
        if include_trends and all_messages:
            result['directory_trends'] = self.trend_analyzer.analyze_temporal_patterns(all_messages)
        
        if self.verbose:
            logger.info(f"Directory analysis complete: {len(valid_files)} files, {len(all_messages)} messages in {analysis_time:.3f}s")
        
        return result
    
    def simulate_compression(self, file_path: Path, levels: List[str] = None) -> Dict[str, Any]:
        """
        Simulate compression without actually modifying files
        
        Args:
            file_path: Path to JSONL file
            levels: List of pruning levels to simulate
            
        Returns:
            Dictionary with compression simulation results
        """
        if levels is None:
            levels = ['light', 'medium', 'aggressive']
        
        try:
            messages = self.analyzer.parse_jsonl_file(file_path)
            
            if not messages:
                return {level: {'error': 'no_messages'} for level in levels}
            
            results = {}
            
            for level in levels:
                threshold = {'light': 20, 'medium': 40, 'aggressive': 60}[level]
                preserved_count = 0
                
                for message in messages:
                    score = self.importance_scorer.calculate_message_importance(message)
                    if score >= threshold:
                        preserved_count += 1
                
                removed_count = len(messages) - preserved_count
                compression_ratio = removed_count / len(messages) if messages else 0
                
                # Estimate size reduction
                original_size = file_path.stat().st_size
                estimated_final_size = int(original_size * (1 - compression_ratio * 0.8))
                estimated_reduction = original_size - estimated_final_size
                
                results[level] = {
                    'messages_would_preserve': preserved_count,
                    'messages_would_remove': removed_count,
                    'compression_ratio': compression_ratio,
                    'estimated_size_reduction': estimated_reduction,
                    'estimated_final_size': estimated_final_size,
                    'estimated_size_reduction_percent': (estimated_reduction / original_size * 100) if original_size > 0 else 0
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Compression simulation failed for {file_path}: {e}")
            return {level: {'error': str(e)} for level in levels}
    
    def export_report(self, stats: Dict[str, Any], output_path: Path, format_type: str):
        """
        Export analysis report to file
        
        Args:
            stats: Statistics dictionary
            output_path: Output file path
            format_type: Format type ('json', 'csv', 'html', 'table')
        """
        try:
            if format_type == 'json':
                content = self.formatter.format_json(stats)
            elif format_type == 'csv':
                content = self.formatter.format_csv(stats)
            elif format_type == 'html':
                content = self.formatter.format_html(stats)
            elif format_type == 'table':
                content = self.formatter.format_table(stats)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            if self.verbose:
                logger.info(f"Report exported to {output_path} in {format_type} format")
                
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            raise
    
    def display_report(self, stats: Dict[str, Any], format_type: str = 'table'):
        """
        Display report to console
        
        Args:
            stats: Statistics dictionary
            format_type: Display format ('table', 'json')
        """
        try:
            if format_type == 'table':
                content = self.formatter.format_table(stats)
            elif format_type == 'json':
                content = self.formatter.format_json(stats)
            else:
                content = self.formatter.format_table(stats)  # Default to table
            
            print(content)
            
        except Exception as e:
            logger.error(f"Failed to display report: {e}")
            raise
    
    def _calculate_basic_statistics(self, messages: List[Dict[str, Any]], file_path: Path) -> Dict[str, Any]:
        """Calculate basic statistics for messages"""
        if not messages:
            return self._create_empty_result(str(file_path), 0)
        
        # Message type distribution
        message_types = Counter(m.get('type', 'unknown') for m in messages)
        
        # Content analysis
        content_lengths = []
        total_characters = 0
        
        for message in messages:
            content = message.get('message', {}).get('content', '')
            content_length = len(content)
            content_lengths.append(content_length)
            total_characters += content_length
        
        average_length = statistics.mean(content_lengths) if content_lengths else 0
        
        return {
            'file_path': str(file_path),
            'total_messages': len(messages),
            'message_types': dict(message_types),
            'average_message_length': average_length,
            'median_message_length': statistics.median(content_lengths) if content_lengths else 0,
            'total_characters': total_characters,
            'file_size_bytes': file_path.stat().st_size,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _analyze_importance_distribution(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze importance score distribution"""
        scores = []
        for message in messages:
            score = self.importance_scorer.calculate_message_importance(message)
            scores.append(score)
        
        if not scores:
            return {'high': 0, 'medium': 0, 'low': 0}
        
        high_count = len([s for s in scores if s >= 60])
        medium_count = len([s for s in scores if 30 <= s < 60])
        low_count = len([s for s in scores if s < 30])
        
        return {
            'high_importance_messages': high_count,
            'medium_importance_messages': medium_count,
            'low_importance_messages': low_count,
            'average_importance_score': statistics.mean(scores),
            'median_importance_score': statistics.median(scores),
            'score_distribution': {
                'high': high_count,
                'medium': medium_count,
                'low': low_count
            }
        }
    
    def _analyze_compression_potential(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze compression potential for different levels"""
        potential = {}
        
        for level in ['light', 'medium', 'aggressive']:
            threshold = {'light': 20, 'medium': 40, 'aggressive': 60}[level]
            preserved = 0
            
            for message in messages:
                score = self.importance_scorer.calculate_message_importance(message)
                if score >= threshold:
                    preserved += 1
            
            removed = len(messages) - preserved
            ratio = removed / len(messages) if messages else 0
            
            # Rough size estimation
            avg_message_size = 150  # Rough estimate
            estimated_size_reduction = removed * avg_message_size
            
            potential[level] = {
                'messages_preserved': preserved,
                'messages_removed': removed,
                'ratio': ratio,
                'size_reduction': estimated_size_reduction
            }
        
        return potential
    
    def _analyze_patterns(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content patterns"""
        code_blocks = 0
        urls = 0
        file_paths = 0
        commands = 0
        
        for message in messages:
            content = message.get('message', {}).get('content', '')
            
            # Use pattern analyzer
            patterns = self.pattern_analyzer.analyze_content_patterns(content)
            
            code_blocks += len(patterns.get('code_blocks', []))
            urls += len(patterns.get('urls', []))
            file_paths += len(patterns.get('file_paths', []))
            commands += len(patterns.get('commands', []))
        
        return {
            'code_blocks': code_blocks,
            'urls': urls,
            'file_paths': file_paths,
            'commands': commands
        }
    
    def _categorize_content(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Categorize content types"""
        categories = {
            'programming_content': 0,
            'conversational_content': 0,
            'system_content': 0,
            'error_debugging': 0,
            'documentation': 0
        }
        
        for message in messages:
            content = message.get('message', {}).get('content', '').lower()
            msg_type = message.get('type', '')
            
            if msg_type == 'system':
                categories['system_content'] += 1
            elif any(term in content for term in ['error', 'exception', 'traceback', 'debug']):
                categories['error_debugging'] += 1
            elif any(term in content for term in ['```', 'function', 'class', 'import', 'def']):
                categories['programming_content'] += 1
            elif any(term in content for term in ['documentation', 'readme', 'guide', 'tutorial']):
                categories['documentation'] += 1
            else:
                categories['conversational_content'] += 1
        
        return categories
    
    def _calculate_aggregated_statistics(self, per_file_stats: List[Dict[str, Any]], 
                                       all_messages: List[Dict[str, Any]], total_size: int) -> Dict[str, Any]:
        """Calculate aggregated statistics across all files"""
        if not per_file_stats:
            return {}
        
        # Aggregate basic metrics
        total_messages = sum(stats.get('total_messages', 0) for stats in per_file_stats)
        total_chars = sum(stats.get('total_characters', 0) for stats in per_file_stats)
        avg_messages_per_file = total_messages / len(per_file_stats) if per_file_stats else 0
        
        # Aggregate message types
        aggregated_types = defaultdict(int)
        for stats in per_file_stats:
            for msg_type, count in stats.get('message_types', {}).items():
                aggregated_types[msg_type] += count
        
        return {
            'total_size_bytes': total_size,
            'total_characters': total_chars,
            'average_messages_per_file': avg_messages_per_file,
            'aggregated_message_types': dict(aggregated_types),
            'files_with_errors': len([s for s in per_file_stats if 'error' in s]),
            'average_file_size': total_size / len(per_file_stats) if per_file_stats else 0
        }
    
    def _analyze_file_diversity(self, per_file_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze diversity across files"""
        if not per_file_stats:
            return {}
        
        message_counts = [stats.get('total_messages', 0) for stats in per_file_stats if 'error' not in stats]
        
        if not message_counts:
            return {'diversity': 'no_data'}
        
        # Calculate coefficient of variation
        mean_messages = statistics.mean(message_counts)
        std_messages = statistics.stdev(message_counts) if len(message_counts) > 1 else 0
        cv = std_messages / mean_messages if mean_messages > 0 else 0
        
        diversity_level = 'high' if cv > 0.5 else 'medium' if cv > 0.2 else 'low'
        
        return {
            'diversity_level': diversity_level,
            'coefficient_of_variation': cv,
            'min_messages': min(message_counts),
            'max_messages': max(message_counts),
            'mean_messages': mean_messages
        }
    
    def _analyze_cross_file_patterns(self, per_file_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns that span across files"""
        if not per_file_stats:
            return {}
        
        # Simple cross-file pattern analysis
        files_with_code = len([s for s in per_file_stats 
                              if s.get('patterns_detected', {}).get('code_blocks', 0) > 0])
        
        files_with_errors = len([s for s in per_file_stats 
                                if s.get('content_categories', {}).get('error_debugging', 0) > 0])
        
        return {
            'files_with_code_blocks': files_with_code,
            'files_with_error_content': files_with_errors,
            'code_prevalence': files_with_code / len(per_file_stats) if per_file_stats else 0,
            'error_prevalence': files_with_errors / len(per_file_stats) if per_file_stats else 0
        }
    
    def _create_empty_result(self, file_path: str, analysis_time: float) -> Dict[str, Any]:
        """Create empty result for files with no messages"""
        return {
            'file_path': file_path,
            'total_messages': 0,
            'message_types': {},
            'average_message_length': 0,
            'total_characters': 0,
            'file_size_bytes': 0,
            'analysis_time': analysis_time,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }