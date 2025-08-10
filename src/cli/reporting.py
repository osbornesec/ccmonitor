"""Statistics and reporting system for CCMonitor CLI.

Comprehensive analytics and report generation for conversation monitoring.
"""

import json
import logging
import re
import statistics
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.jsonl_analysis.analyzer import JSONLAnalyzer
from src.jsonl_analysis.patterns import PatternAnalyzer
from src.jsonl_analysis.scoring import ImportanceScorer, MessageScoreAnalyzer

from .constants import (
    AGGRESSIVE_REDUCTION_FACTOR,
    CONSERVATIVE_REDUCTION_FACTOR,
    DECREASING_TREND_MULTIPLIER,
    DEPENDENCY_COMPLEXITY_THRESHOLD,
    FOCUSED_TOPIC_OVERLAP_THRESHOLD,
    HIGH_ACTIVITY_MESSAGES_PER_DAY,
    HIGH_CONFIDENCE_THRESHOLD,
    HIGH_DIVERSITY_CV_THRESHOLD,
    HIGH_IMPORTANT_CONTENT_THRESHOLD,
    IMPORTANT_ASSISTANT_MESSAGE_THRESHOLD,
    IMPORTANT_CONTENT_RATIO_THRESHOLD,
    INCREASING_TREND_MULTIPLIER,
    LARGE_CONVERSATION_CONFIDENCE_THRESHOLD,
    MAX_REASONABLE_RESPONSE_TIME,
    MEDIUM_DIVERSITY_CV_THRESHOLD,
    MIN_CONTENTS_FOR_TOPIC_PROGRESSION,
    MIN_HOURLY_COUNTS_FOR_TREND,
    MIN_KEYWORD_LENGTH,
    MIN_MESSAGES_FOR_ANALYSIS,
    MIN_MESSAGES_FOR_PATTERN_ANALYSIS,
    MIN_TIMESTAMPS_FOR_TREND,
    MIN_VALUES_FOR_TREND,
    MODERATE_CONFIDENCE_THRESHOLD,
    MODERATE_REDUCTION_FACTOR,
    REPETITIVE_CONTENT_THRESHOLD,
    SCATTERED_TOPIC_OVERLAP_THRESHOLD,
    SCORE_HIGH_THRESHOLD,
    SCORE_MEDIUM_THRESHOLD,
    SMALL_CONVERSATION_SIZE_THRESHOLD,
    SYSTEM_RATIO_THRESHOLD,
    TREND_SLOPE_DECREASE_THRESHOLD,
    TREND_SLOPE_INCREASE_THRESHOLD,
    VERBOSE_CODE_BLOCK_THRESHOLD,
    VERBOSE_CONTENT_LENGTH_THRESHOLD,
    VERBOSE_CONTENT_THRESHOLD,
    VERBOSE_SYSTEM_MESSAGE_THRESHOLD,
)
from .utils import format_duration, format_size, is_jsonl_file

logger = logging.getLogger(__name__)


@dataclass
class AnalysisConfig:
    """Configuration for analysis operations."""

    include_patterns: bool = False
    include_trends: bool = False
    recursive: bool = False
    start_time: float = 0.0


@dataclass
class ProcessedDirectoryData:
    """Processed data for directory analysis."""

    valid_files: list[Path]
    per_file_stats: list[dict[str, Any]]
    all_messages: list[dict[str, Any]]
    total_size: int


@dataclass
class AnalysisResult:
    """Data structure for analysis results."""

    file_path: str
    total_messages: int
    message_types: dict[str, int]
    average_message_length: float
    total_characters: int
    file_size_bytes: int
    analysis_time: float
    timestamp: str

    # Optional detailed analysis
    importance_distribution: dict[str, int] | None = None
    compression_potential: dict[str, dict[str, Any]] | None = None
    patterns_detected: dict[str, Any] | None = None
    temporal_analysis: dict[str, Any] | None = None
    content_categories: dict[str, Any] | None = None


class TrendAnalyzer:
    """Analyzer for temporal trends and patterns in conversations."""

    def __init__(self) -> None:
        """Initialize the TrendAnalyzer with a PatternAnalyzer."""
        self.pattern_analyzer = PatternAnalyzer()

    def analyze_temporal_patterns(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Analyze temporal patterns in message data.

        Args:
            messages: List of message dictionaries

        Returns:
            Dictionary with temporal analysis results

        """
        timestamps, hourly_dist, daily_dist = self._extract_timestamp_data(messages)

        if not timestamps:
            return self._create_empty_temporal_analysis()

        return self._create_temporal_analysis_result(
            timestamps, hourly_dist, daily_dist, messages,
        )

    def _extract_timestamp_data(
        self, messages: list[dict[str, Any]],
    ) -> tuple[list[datetime], defaultdict[int, int], defaultdict[str, int]]:
        """Extract and parse timestamp data from messages."""
        timestamps = []
        hourly_distribution: defaultdict[int, int] = defaultdict(int)
        daily_distribution: defaultdict[str, int] = defaultdict(int)

        for message in messages:
            timestamp = message.get("timestamp")
            if timestamp:
                dt = self._parse_timestamp(timestamp)
                if dt:
                    timestamps.append(dt)
                    hourly_distribution[dt.hour] += 1
                    daily_distribution[dt.strftime("%Y-%m-%d")] += 1

        return timestamps, hourly_distribution, daily_distribution

    def _parse_timestamp(self, timestamp: str | float) -> datetime | None:
        """Parse various timestamp formats."""
        try:
            if isinstance(timestamp, str):
                return self._parse_string_timestamp(timestamp)
            if isinstance(timestamp, int | float):
                return datetime.fromtimestamp(timestamp, tz=UTC)
        except (ValueError, TypeError) as e:
            logger.debug("Failed to parse timestamp %s: %s", timestamp, e)
        return None

    def _parse_string_timestamp(self, timestamp: str) -> datetime:
        """Parse string timestamp format."""
        if timestamp.endswith("Z"):
            return datetime.fromisoformat(timestamp)
        return datetime.fromisoformat(timestamp)

    def _create_empty_temporal_analysis(self) -> dict[str, Any]:
        """Create empty temporal analysis result."""
        return {
            "hourly_distribution": {},
            "daily_distribution": {},
            "peak_hours": [],
            "message_frequency_trend": "insufficient_data",
            "conversation_duration": 0,
            "active_days": 0,
        }

    def _create_temporal_analysis_result(
        self,
        timestamps: list[datetime],
        hourly_dist: defaultdict[int, int],
        daily_dist: defaultdict[str, int],
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Create complete temporal analysis result."""
        sorted_timestamps = sorted(timestamps)
        conversation_duration = (
            sorted_timestamps[-1] - sorted_timestamps[0]
        ).total_seconds()
        peak_hours = self._find_peak_hours(hourly_dist)

        return {
            "hourly_distribution": dict(hourly_dist),
            "daily_distribution": dict(daily_dist),
            "peak_hours": [hour for hour, count in peak_hours],
            "peak_hour_counts": dict(peak_hours),
            "conversation_duration": conversation_duration,
            "active_days": len(daily_dist),
            "average_messages_per_day": len(messages) / max(len(daily_dist), 1),
            "message_frequency_trend": self._calculate_frequency_trend(timestamps),
            "first_message": sorted_timestamps[0].isoformat() if timestamps else None,
            "last_message": sorted_timestamps[-1].isoformat() if timestamps else None,
        }

    def _find_peak_hours(
        self, hourly_distribution: defaultdict[int, int],
    ) -> list[tuple[int, int]]:
        """Find peak activity hours."""
        return sorted(
            hourly_distribution.items(), key=lambda x: x[1], reverse=True,
        )[:3]

    def analyze_conversation_flow(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Analyze conversation flow and interaction patterns.

        Args:
            messages: List of message dictionaries

        Returns:
            Dictionary with conversation flow analysis

        """
        message_counts = self._count_messages_by_type(messages)
        response_times, interaction_patterns = self._analyze_message_interactions(
            messages,
        )
        conversation_breaks = self._detect_conversation_breaks(messages)

        return self._create_conversation_flow_result(
            message_counts,
            response_times,
            interaction_patterns,
            conversation_breaks,
        )

    def _count_messages_by_type(
        self, messages: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Count messages by type."""
        return {
            "user": [m for m in messages if m.get("type") == "user"],
            "assistant": [m for m in messages if m.get("type") == "assistant"],
            "system": [m for m in messages if m.get("type") == "system"],
        }

    def _analyze_message_interactions(
        self, messages: list[dict[str, Any]],
    ) -> tuple[list[float], list[str]]:
        """Analyze message interactions and response times."""
        response_times = []
        interaction_patterns = []

        prev_message = None
        for message in messages:
            if prev_message:
                interaction_patterns.append(
                    self._create_transition_pattern(prev_message, message),
                )
                response_time = self._calculate_response_time(prev_message, message)
                if response_time:
                    response_times.append(response_time)
            prev_message = message

        return response_times, interaction_patterns

    def _create_transition_pattern(
        self, prev_message: dict[str, Any], curr_message: dict[str, Any],
    ) -> str:
        """Create transition pattern string."""
        return (
            f"{prev_message.get('type', 'unknown')} -> "
            f"{curr_message.get('type', 'unknown')}"
        )

    def _calculate_response_time(
        self, prev_message: dict[str, Any], curr_message: dict[str, Any],
    ) -> float | None:
        """Calculate response time between messages."""
        if not self._is_user_to_assistant(prev_message, curr_message):
            return None

        try:
            prev_time = self._parse_timestamp(prev_message["timestamp"])
            curr_time = self._parse_timestamp(
                curr_message["timestamp"],
            )
            if prev_time and curr_time:
                response_time = (curr_time - prev_time).total_seconds()
                if 0 < response_time < MAX_REASONABLE_RESPONSE_TIME:
                    return response_time
        except Exception as e:  # noqa: BLE001
            logger.debug("Failed to calculate response time: %s", e)
        return None

    def _is_user_to_assistant(
        self, prev_message: dict[str, Any], curr_message: dict[str, Any],
    ) -> bool:
        """Check if transition is from user to assistant."""
        return bool(prev_message.get("timestamp") and
                    curr_message.get("timestamp") and
                    prev_message.get("type") == "user" and
                    curr_message.get("type") == "assistant")

    def _create_conversation_flow_result(
        self,
        message_counts: dict[str, list[dict[str, Any]]],
        response_times: list[float],
        interaction_patterns: list[str],
        conversation_breaks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Create conversation flow analysis result."""
        pattern_counts = Counter(interaction_patterns)

        return {
            "user_assistant_ratio": len(message_counts["user"]) / max(
                len(message_counts["assistant"]), 1,
            ),
            "total_user_messages": len(message_counts["user"]),
            "total_assistant_messages": len(message_counts["assistant"]),
            "total_system_messages": len(message_counts["system"]),
            "average_response_time": (
                statistics.mean(response_times) if response_times else 0
            ),
            "median_response_time": (
                statistics.median(response_times) if response_times else 0
            ),
            "response_time_std": (
                statistics.stdev(response_times) if len(response_times) > 1 else 0
            ),
            "conversation_breaks": conversation_breaks,
            "interaction_patterns": dict(pattern_counts),
            "most_common_transitions": pattern_counts.most_common(5),
        }

    def detect_content_evolution(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Detect how content and topics evolve throughout the conversation.

        Args:
            messages: List of message dictionaries

        Returns:
            Dictionary with content evolution analysis

        """
        # Extract content from messages
        contents = []
        timestamps = []

        for message in messages:
            content = message.get("message", {}).get("content", "")
            timestamp = message.get("timestamp")

            if content and timestamp:
                contents.append(content)
                timestamps.append(self._parse_timestamp(timestamp))

        if len(contents) < MIN_MESSAGES_FOR_ANALYSIS:
            return {
                "topic_progression": "insufficient_data",
                "content_complexity_trend": "insufficient_data",
                "keyword_frequency_changes": {},
            }

        # Analyze content complexity over time
        complexity_scores = []
        for content in contents:
            # Simple complexity metrics
            word_count = len(content.split())
            unique_words = len(set(content.lower().split()))
            avg_word_length = sum(len(word) for word in content.split()) / max(
                word_count,
                1,
            )

            complexity = {
                "word_count": word_count,
                "unique_words": unique_words,
                "vocabulary_richness": unique_words / max(word_count, 1),
                "average_word_length": avg_word_length,
                "character_count": len(content),
                "code_blocks": content.count("```"),
                "technical_terms": self._count_technical_terms(content),
            }
            complexity_scores.append(complexity)

        # Calculate trends
        word_count_trend = self._calculate_trend(
            [c["word_count"] for c in complexity_scores],
        )
        complexity_trend = self._calculate_trend(
            [c["vocabulary_richness"] for c in complexity_scores],
        )

        # Topic progression analysis
        topic_keywords = self._extract_topic_keywords(contents)

        return {
            "content_complexity_trend": complexity_trend,
            "word_count_trend": word_count_trend,
            "average_complexity": {
                "word_count": statistics.mean(
                    [c["word_count"] for c in complexity_scores],
                ),
                "vocabulary_richness": statistics.mean(
                    [c["vocabulary_richness"] for c in complexity_scores],
                ),
                "technical_content": statistics.mean(
                    [c["technical_terms"] for c in complexity_scores],
                ),
            },
            "keyword_frequency_changes": topic_keywords,
            "topic_progression": self._analyze_topic_progression(contents),
        }

    def predict_compression_benefits(
        self,
        messages: list[dict[str, Any]],
        _historical_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Predict compression benefits based on content analysis.

        Args:
            messages: List of message dictionaries
            _historical_data: Optional historical compression data (unused)

        Returns:
            Dictionary with compression benefit predictions

        """
        content_metrics = self._analyze_content_characteristics(
            messages,
        )
        recommendation = self._determine_analysis_recommendation(
            content_metrics,
        )
        risk_assessment = self._assess_compression_risks(
            messages, content_metrics,
        )

        return {
            "recommended_analysis_level": recommendation["level"],
            "expected_size_reduction": recommendation["reduction"],
            "risk_assessment": risk_assessment,
            "content_analysis": content_metrics,
            "optimal_monitoring_schedule": self._suggest_optimal_schedule(messages),
        }

    def _analyze_content_characteristics(
        self, messages: list[dict[str, Any]],
    ) -> dict[str, float]:
        """Analyze content characteristics for compression prediction."""
        system_ratio = len(
            [m for m in messages if m.get("type") == "system"],
        ) / len(messages)
        repetitive_content = self._analyze_repetitive_content(messages)
        verbose_content = self._analyze_verbose_content(messages)
        important_content_ratio = self._estimate_important_content_ratio(
            messages,
        )

        return {
            "system_message_ratio": system_ratio,
            "repetitive_content_ratio": repetitive_content,
            "verbose_content_ratio": verbose_content,
            "important_content_ratio": important_content_ratio,
            "dependency_complexity": self._analyze_dependency_complexity(messages),
        }

    def _determine_analysis_recommendation(
        self, content_metrics: dict[str, float],
    ) -> dict[str, Any]:
        """Determine recommended analysis level and expected reduction."""
        system_ratio = content_metrics["system_message_ratio"]
        repetitive_content = content_metrics["repetitive_content_ratio"]
        verbose_content = content_metrics["verbose_content_ratio"]
        important_content_ratio = content_metrics["important_content_ratio"]

        if (
            system_ratio > SYSTEM_RATIO_THRESHOLD
            and repetitive_content > REPETITIVE_CONTENT_THRESHOLD
        ):
            return {"level": "aggressive", "reduction": AGGRESSIVE_REDUCTION_FACTOR}
        if (
            verbose_content > VERBOSE_CONTENT_THRESHOLD
            and important_content_ratio < IMPORTANT_CONTENT_RATIO_THRESHOLD
        ):
            return {"level": "medium", "reduction": MODERATE_REDUCTION_FACTOR}
        return {"level": "light", "reduction": CONSERVATIVE_REDUCTION_FACTOR}

    def _assess_compression_risks(
        self, messages: list[dict[str, Any]], content_metrics: dict[str, float],
    ) -> dict[str, Any]:
        """Assess risks associated with compression."""
        risk_factors = self._identify_risk_factors(messages, content_metrics)
        risk_level = self._calculate_risk_level(risk_factors)
        confidence = self._calculate_confidence(messages)

        return {
            "level": risk_level,
            "factors": risk_factors,
            "confidence": confidence,
        }

    def _identify_risk_factors(
        self, messages: list[dict[str, Any]], content_metrics: dict[str, float],
    ) -> list[str]:
        """Identify risk factors for compression."""
        risk_factors = []

        if content_metrics["dependency_complexity"] > DEPENDENCY_COMPLEXITY_THRESHOLD:
            risk_factors.append("high_dependency_complexity")
        if (
            content_metrics["important_content_ratio"]
            > HIGH_IMPORTANT_CONTENT_THRESHOLD
        ):
            risk_factors.append("high_important_content_ratio")
        if len(messages) < SMALL_CONVERSATION_SIZE_THRESHOLD:
            risk_factors.append("small_conversation_size")

        return risk_factors

    def _calculate_risk_level(self, risk_factors: list[str]) -> str:
        """Calculate overall risk level."""
        return "high" if len(risk_factors) > 1 else "medium" if risk_factors else "low"

    def _calculate_confidence(self, messages: list[dict[str, Any]]) -> float:
        """Calculate confidence level for predictions."""
        return (
            HIGH_CONFIDENCE_THRESHOLD
            if len(messages) > LARGE_CONVERSATION_CONFIDENCE_THRESHOLD
            else MODERATE_CONFIDENCE_THRESHOLD
        )


    def _calculate_frequency_trend(self, timestamps: list[datetime]) -> str:
        """Calculate message frequency trend."""
        if not self._has_sufficient_trend_data(timestamps):
            return "insufficient_data"

        hourly_counts = self._aggregate_hourly_counts(timestamps)
        return self._analyze_trend_pattern(hourly_counts)

    def _has_sufficient_trend_data(self, timestamps: list[datetime]) -> bool:
        """Check if there's enough data for trend analysis."""
        return len(timestamps) >= MIN_TIMESTAMPS_FOR_TREND

    def _aggregate_hourly_counts(self, timestamps: list[datetime]) -> list[int]:
        """Aggregate message counts by hour."""
        hourly_counts: defaultdict[datetime, int] = defaultdict(int)
        for ts in timestamps:
            hour_key = ts.replace(minute=0, second=0, microsecond=0)
            hourly_counts[hour_key] += 1
        return list(hourly_counts.values())

    def _analyze_trend_pattern(self, counts: list[int]) -> str:
        """Analyze trend pattern from hourly counts."""
        if len(counts) < MIN_HOURLY_COUNTS_FOR_TREND:
            return "stable"

        first_half_avg = statistics.mean(counts[: len(counts) // 2])
        second_half_avg = statistics.mean(counts[len(counts) // 2 :])

        return self._classify_trend(first_half_avg, second_half_avg)

    def _classify_trend(self, first_half: float, second_half: float) -> str:
        """Classify trend based on averages."""
        if second_half > first_half * INCREASING_TREND_MULTIPLIER:
            return "increasing"
        if second_half < first_half * DECREASING_TREND_MULTIPLIER:
            return "decreasing"
        return "stable"

    def _detect_conversation_breaks(
        self,
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Detect breaks in conversation (gaps > 1 hour)."""
        timestamped_messages = self._extract_timestamped_messages(messages)
        return self._find_time_gaps(timestamped_messages)

    def _extract_timestamped_messages(
        self, messages: list[dict[str, Any]],
    ) -> list[tuple[datetime, dict[str, Any]]]:
        """Extract messages with valid timestamps."""
        timestamped_messages = []

        for message in messages:
            ts_value = message.get("timestamp")
            if ts_value is not None:
                timestamp = self._parse_timestamp(ts_value)
                if timestamp:
                    timestamped_messages.append((timestamp, message))

        timestamped_messages.sort(key=lambda x: x[0])
        return timestamped_messages

    def _find_time_gaps(
        self, timestamped_messages: list[tuple[datetime, dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """Find significant time gaps between messages."""
        breaks = []

        for i in range(1, len(timestamped_messages)):
            prev_time, prev_msg = timestamped_messages[i - 1]
            curr_time, curr_msg = timestamped_messages[i]

            gap = (curr_time - prev_time).total_seconds()
            if self._is_significant_gap(gap):
                breaks.append(self._create_break_record(prev_msg, curr_msg, gap))

        return breaks

    def _is_significant_gap(self, gap_seconds: float) -> bool:
        """Check if gap is significant (> 1 hour)."""
        return gap_seconds > MAX_REASONABLE_RESPONSE_TIME

    def _create_break_record(
        self, prev_msg: dict[str, Any], curr_msg: dict[str, Any], gap: float,
    ) -> dict[str, Any]:
        """Create break record."""
        return {
            "start_message": prev_msg.get("uuid"),
            "end_message": curr_msg.get("uuid"),
            "gap_duration": gap,
            "gap_hours": gap / MAX_REASONABLE_RESPONSE_TIME,
        }

    def _count_technical_terms(self, content: str) -> int:
        """Count technical terms in content."""
        technical_patterns = [
            r"\b(?:function|class|method|variable|array|object|string|integer|boolean)\b",
            r"\b(?:API|HTTP|JSON|XML|SQL|database|server|client)\b",
            r"\b(?:algorithm|optimization|performance|efficiency|scalability)\b",
            r"```[^`]*```",  # Code blocks
            r"\b[A-Z][a-zA-Z]*Error\b",  # Error types
            # Python keywords
            r"\b(?:import|from|def|class|return|if|else|for|while)\b",
        ]

        count = 0
        for pattern in technical_patterns:
            count += len(re.findall(pattern, content, re.IGNORECASE))

        return count

    def _calculate_trend(self, values: list[float]) -> str:
        """Calculate trend direction from list of values."""
        if len(values) < MIN_VALUES_FOR_TREND:
            return "insufficient_data"

        # Simple linear trend calculation
        n = len(values)
        x_mean = n / 2
        y_mean = statistics.mean(values)

        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return "stable"

        slope = numerator / denominator

        if slope > TREND_SLOPE_INCREASE_THRESHOLD:
            return "increasing"
        if slope < TREND_SLOPE_DECREASE_THRESHOLD:
            return "decreasing"
        return "stable"

    def _extract_topic_keywords(self, contents: list[str]) -> dict[str, Any]:
        """Extract and track topic keywords over time."""
        # Simple keyword extraction
        all_words = []
        for content in contents:
            words = re.findall(r"\b[a-zA-Z]{4,}\b", content.lower())
            all_words.extend(words)

        # Count frequency
        word_counts = Counter(all_words)

        # Filter common words
        common_words = {
            "that",
            "this",
            "with",
            "have",
            "will",
            "from",
            "they",
            "been",
            "were",
            "said",
            "each",
            "which",
            "their",
            "time",
            "more",
            "very",
            "what",
            "know",
            "just",
            "first",
            "into",
            "over",
            "also",
            "after",
            "back",
            "other",
            "many",
            "than",
            "then",
            "them",
            "these",
            "some",
            "would",
            "make",
            "like",
            "him",
            "has",
            "had",
            "her",
            "or",
            "an",
            "my",
            "me",
            "as",
            "be",
            "on",
            "at",
            "by",
            "it",
            "to",
            "of",
            "and",
            "a",
            "the",
            "is",
            "you",
            "are",
            "for",
            "all",
            "any",
            "can",
            "was",
            "one",
            "our",
            "out",
            "day",
            "get",
            "his",
            "how",
            "its",
            "may",
            "new",
            "now",
            "old",
            "see",
            "two",
            "who",
            "boy",
            "did",
            "man",
            "men",
            "put",
            "say",
            "she",
            "too",
            "use",
        }

        filtered_words = {
            word: count
            for word, count in word_counts.items()
            if word not in common_words and count > 1
        }

        return {
            "top_keywords": dict(Counter(filtered_words).most_common(20)),
            "total_unique_words": len(word_counts),
            "vocabulary_size": len(filtered_words),
        }

    def _analyze_topic_progression(self, contents: list[str]) -> str:
        """Analyze how topics progress through the conversation."""
        if len(contents) < MIN_CONTENTS_FOR_TOPIC_PROGRESSION:
            return "insufficient_data"

        # Simple topic progression analysis
        # Could be enhanced with more sophisticated NLP

        # Look for patterns in content evolution
        first_quarter = contents[: len(contents) // 4]
        last_quarter = contents[-len(contents) // 4 :]

        first_keywords = self._extract_simple_keywords(" ".join(first_quarter))
        last_keywords = self._extract_simple_keywords(" ".join(last_quarter))

        overlap = len(set(first_keywords) & set(last_keywords))
        total_unique = len(set(first_keywords) | set(last_keywords))

        if total_unique == 0:
            return "stable"

        overlap_ratio = overlap / total_unique

        if overlap_ratio > FOCUSED_TOPIC_OVERLAP_THRESHOLD:
            return "focused"  # Topics remain similar
        if overlap_ratio < SCATTERED_TOPIC_OVERLAP_THRESHOLD:
            return "divergent"  # Topics change significantly
        return "evolving"  # Topics evolve gradually

    def _extract_simple_keywords(self, text: str) -> list[str]:
        """Extract simple keywords from text."""
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
        return [word for word in words if len(word) > MIN_KEYWORD_LENGTH]

    def _analyze_repetitive_content(
        self,
        messages: list[dict[str, Any]],
    ) -> float:
        """Analyze ratio of repetitive content."""
        contents = [m.get("message", {}).get("content", "") for m in messages]

        if len(contents) < MIN_MESSAGES_FOR_ANALYSIS:
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

    def _analyze_verbose_content(
        self,
        messages: list[dict[str, Any]],
    ) -> float:
        """Analyze ratio of verbose content that could be compressed."""
        verbose_count = 0

        for message in messages:
            content = message.get("message", {}).get("content", "")

            # Consider verbose if:
            # - Very long content (>2000 chars)
            # - Contains lots of code blocks
            # - System messages with verbose output

            is_verbose = (
                len(content) > VERBOSE_CONTENT_LENGTH_THRESHOLD
                or content.count("```") > VERBOSE_CODE_BLOCK_THRESHOLD
                or (
                    message.get("type") == "system"
                    and len(content) > VERBOSE_SYSTEM_MESSAGE_THRESHOLD
                )
            )

            if is_verbose:
                verbose_count += 1

        return verbose_count / len(messages) if messages else 0.0

    def _estimate_important_content_ratio(
        self,
        messages: list[dict[str, Any]],
    ) -> float:
        """Estimate ratio of important content."""
        # This is a simplified estimation
        # Could use the actual ImportanceScorer for more accuracy

        important_count = 0

        for message in messages:
            msg_type = message.get("type", "")
            content = message.get("message", {}).get("content", "")

            # Consider important if:
            # - User questions
            # - Assistant responses with code or detailed explanations
            # - Error messages or debugging content

            is_important = (
                msg_type == "user"
                or (
                    msg_type == "assistant"
                    and (
                        "```" in content
                        or len(content) > IMPORTANT_ASSISTANT_MESSAGE_THRESHOLD
                    )
                )
                or "error" in content.lower()
                or "exception" in content.lower()
            )

            if is_important:
                important_count += 1

        return important_count / len(messages) if messages else 0.0

    def _analyze_dependency_complexity(
        self,
        messages: list[dict[str, Any]],
    ) -> float:
        """Analyze complexity of message dependencies."""
        # Simple dependency analysis based on message references
        # Could be enhanced with actual conversation graph analysis

        reference_count = 0
        for message in messages:
            content = message.get("message", {}).get("content", "")

            # Look for references to previous messages
            if any(
                phrase in content.lower()
                for phrase in [
                    "as mentioned",
                    "previously",
                    "earlier",
                    "above",
                    "before",
                    "following up",
                    "regarding",
                ]
            ):
                reference_count += 1

        return reference_count / len(messages) if messages else 0.0

    def _suggest_optimal_schedule(
        self, messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Suggest optimal monitoring schedule."""
        timestamps = self._extract_valid_timestamps(messages)

        if not timestamps:
            return self._create_schedule_recommendation(
                "weekly", "low", "no_timestamp_data",
            )

        messages_per_day = self._calculate_activity_rate(timestamps, len(messages))
        return self._determine_schedule_from_activity(messages_per_day)

    def _extract_valid_timestamps(
        self, messages: list[dict[str, Any]],
    ) -> list[datetime]:
        """Extract valid timestamps from messages."""
        timestamps = []
        for message in messages:
            ts_value = message.get("timestamp")
            if ts_value is not None:
                parsed_ts = self._parse_timestamp(ts_value)
                if parsed_ts is not None:
                    timestamps.append(parsed_ts)
        return timestamps

    def _calculate_activity_rate(
        self, timestamps: list[datetime], message_count: int,
    ) -> float:
        """Calculate messages per day from timestamp data."""
        timestamps.sort()
        if len(timestamps) <= 1:
            return 1.0

        span_days = (timestamps[-1] - timestamps[0]).days
        return message_count / max(span_days, 1)

    def _determine_schedule_from_activity(
        self, messages_per_day: float,
    ) -> dict[str, Any]:
        """Determine schedule recommendation based on activity rate."""
        if messages_per_day > HIGH_ACTIVITY_MESSAGES_PER_DAY:
            return self._create_schedule_recommendation(
                "daily", "high", "high_message_volume",
            )

        if messages_per_day > MIN_MESSAGES_FOR_PATTERN_ANALYSIS:
            return self._create_schedule_recommendation(
                "weekly", "medium", "moderate_message_volume",
            )

        return self._create_schedule_recommendation(
            "monthly", "medium", "low_message_volume",
        )

    def _create_schedule_recommendation(
        self, frequency: str, confidence: str, reasoning: str,
    ) -> dict[str, Any]:
        """Create a standardized schedule recommendation."""
        return {
            "recommended_frequency": frequency,
            "confidence": confidence,
            "reasoning": reasoning,
        }


class ReportFormatter:
    """Formatter for generating reports in various formats."""

    def __init__(self) -> None:
        """Initialize ReportFormatter with trend analyzer."""
        self.trend_analyzer = TrendAnalyzer()

    def format_table(self, stats: dict[str, Any]) -> str:
        """Format statistics as a readable table."""
        output: list[str] = []
        self._add_report_header(output)
        self._add_basic_statistics(output, stats)
        self._add_compression_section(output, stats)
        self._add_patterns_section(output, stats)
        self._add_temporal_section(output, stats)
        self._add_performance_section(output, stats)
        return "\n".join(output)

    def _add_report_header(self, output: list[str]) -> None:
        """Add report header to output."""
        output.append("=" * 60)
        output.append("JSONL ANALYSIS REPORT")
        output.append("=" * 60)
        output.append("")

    def _add_basic_statistics(self, output: list[str], stats: dict[str, Any]) -> None:
        """Add basic statistics section to output."""
        output.append("BASIC STATISTICS")
        output.append("-" * 20)
        output.append(
            f"Total Messages:      {stats.get('total_messages', 0):,}",
        )

        if "message_types" in stats:
            output.append("Message Types:")
            for msg_type, count in stats["message_types"].items():
                output.append(f"  {msg_type.capitalize():12} {count:,}")

        avg_length = stats.get("average_message_length", 0)
        output.append(f"Average Length:      {avg_length:.1f} characters")
        output.append(
            f"Total Characters:    {stats.get('total_characters', 0):,}",
        )

        if "file_size_bytes" in stats:
            output.append(
                f"File Size:           {format_size(stats['file_size_bytes'])}",
            )

        output.append("")

    def _add_compression_section(
        self, output: list[str], stats: dict[str, Any],
    ) -> None:
        """Add compression potential section to output."""
        if "compression_potential" not in stats:
            return

        output.append("COMPRESSION POTENTIAL")
        output.append("-" * 25)
        for level, data in stats["compression_potential"].items():
            ratio = data.get("ratio", 0) * 100
            size_reduction = data.get("size_reduction", 0)
            size_str = format_size(size_reduction)
            output.append(
                f"{level.capitalize():12} {ratio:5.1f}% reduction ({size_str})",
            )
        output.append("")

    def _add_patterns_section(self, output: list[str], stats: dict[str, Any]) -> None:
        """Add patterns detected section to output."""
        if "patterns_detected" not in stats:
            return

        patterns = stats["patterns_detected"]
        output.append("CONTENT PATTERNS")
        output.append("-" * 20)

        if patterns.get("code_blocks", 0) > 0:
            output.append(
                f"Code Blocks:         {patterns['code_blocks']:,}",
            )
        if patterns.get("urls", 0) > 0:
            output.append(f"URLs:                {patterns['urls']:,}")
        if patterns.get("file_paths", 0) > 0:
            output.append(
                f"File Paths:          {patterns['file_paths']:,}",
            )

        output.append("")

    def _add_temporal_section(self, output: list[str], stats: dict[str, Any]) -> None:
        """Add temporal analysis section to output."""
        if "temporal_analysis" not in stats:
            return

        temporal = stats["temporal_analysis"]
        output.append("TEMPORAL ANALYSIS")
        output.append("-" * 20)

        if temporal.get("conversation_duration", 0) > 0:
            duration = temporal["conversation_duration"]
            output.append(
                f"Duration:            {format_duration(duration)}",
            )

        if temporal.get("peak_hours"):
            peak_hours = ", ".join(map(str, temporal["peak_hours"]))
            output.append(f"Peak Hours:          {peak_hours}")

        if "message_frequency_trend" in temporal:
            output.append(
                f"Frequency Trend:     {temporal['message_frequency_trend']}",
            )

        output.append("")

    def _add_performance_section(
        self, output: list[str], stats: dict[str, Any],
    ) -> None:
        """Add performance information section to output."""
        if "analysis_time" not in stats:
            return

        output.append("ANALYSIS PERFORMANCE")
        output.append("-" * 25)
        output.append(
            f"Analysis Time:       {stats['analysis_time']:.3f} seconds",
        )
        messages_per_sec = (
            stats.get("total_messages", 0) / max(stats["analysis_time"], 0.001)
        )
        output.append(f"Messages/Second:     {messages_per_sec:,.0f}")
        output.append("")

    def format_json(self, stats: dict[str, Any]) -> str:
        """Format statistics as JSON."""
        # Ensure all data is JSON serializable
        json_stats = self._make_json_serializable(stats)
        return json.dumps(json_stats, indent=2, sort_keys=True)

    def format_csv(self, stats: dict[str, Any]) -> str:
        """Format statistics as CSV."""
        output: list[str] = ["metric,value,category"]
        self._add_basic_csv_metrics(output, stats)
        self._add_message_types_csv(output, stats)
        self._add_compression_csv(output, stats)
        self._add_patterns_csv(output, stats)
        self._add_performance_csv(output, stats)
        return "\n".join(output)

    def _add_basic_csv_metrics(self, output: list[str], stats: dict[str, Any]) -> None:
        """Add basic metrics to CSV output."""
        output.append(f"total_messages,{stats.get('total_messages', 0)},basic")
        avg_msg_len = stats.get("average_message_length", 0)
        output.append(f"average_message_length,{avg_msg_len:.2f},basic")
        output.append(
            f"total_characters,{stats.get('total_characters', 0)},basic",
        )

        if "file_size_bytes" in stats:
            output.append(f"file_size_bytes,{stats['file_size_bytes']},basic")

    def _add_message_types_csv(self, output: list[str], stats: dict[str, Any]) -> None:
        """Add message types to CSV output."""
        if "message_types" not in stats:
            return

        for msg_type, count in stats["message_types"].items():
            output.append(f"messages_{msg_type},{count},message_types")

    def _add_compression_csv(self, output: list[str], stats: dict[str, Any]) -> None:
        """Add compression metrics to CSV output."""
        if "compression_potential" not in stats:
            return

        for level, data in stats["compression_potential"].items():
            ratio = data.get("ratio", 0)
            size_reduction = data.get("size_reduction", 0)
            output.append(
                f"compression_ratio_{level},{ratio:.3f},compression",
            )
            output.append(
                f"size_reduction_{level},{size_reduction},compression",
            )

    def _add_patterns_csv(self, output: list[str], stats: dict[str, Any]) -> None:
        """Add pattern metrics to CSV output."""
        if "patterns_detected" not in stats:
            return

        patterns = stats["patterns_detected"]
        for pattern_type, count in patterns.items():
            output.append(f"pattern_{pattern_type},{count},patterns")

    def _add_performance_csv(self, output: list[str], stats: dict[str, Any]) -> None:
        """Add performance metrics to CSV output."""
        if "analysis_time" in stats:
            output.append(
                f"analysis_time,{stats['analysis_time']:.3f},performance",
            )

    def format_html(self, stats: dict[str, Any]) -> str:
        """Format statistics as HTML report."""
        html: list[str] = []

        self._add_html_header(html)
        self._add_html_body_start(html)
        self._add_basic_statistics_html(html, stats)
        self._add_message_types_html(html, stats)
        self._add_compression_potential_html(html, stats)
        self._add_performance_html(html, stats)
        self._add_html_footer(html)

        return "\n".join(html)

    def _add_html_header(self, html: list[str]) -> None:
        """Add HTML document header."""
        html.extend([
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "    <meta charset='UTF-8'>",
            "    <meta name='viewport' content='width=device-width, "
            "initial-scale=1.0'>",
            "    <title>JSONL Analysis Report</title>",
            "    <style>",
            self._get_html_styles(),
            "    </style>",
            "</head>",
        ])

    def _add_html_body_start(self, html: list[str]) -> None:
        """Add HTML body opening and main container."""
        html.extend([
            "<body>",
            "    <div class='container'>",
            "        <h1>JSONL Analysis Report</h1>",
        ])

    def _add_basic_statistics_html(
        self, html: list[str], stats: dict[str, Any],
    ) -> None:
        """Add basic statistics section to HTML report."""
        html.extend([
            "        <div class='section'>",
            "            <h2>Basic Statistics</h2>",
            "            <div class='stats-grid'>",
        ])

        # Core statistics
        html.extend([
            (
                f"                <div class='stat'>"
                f"<span class='label'>Total Messages:</span> "
                f"<span class='value'>{stats.get('total_messages', 0):,}</span></div>"
            ),
            (
                f"                <div class='stat'>"
                f"<span class='label'>Average Length:</span> "
                f"<span class='value'>"
                f"{stats.get('average_message_length', 0):.1f} chars</span></div>"
            ),
            (
                f"                <div class='stat'>"
                f"<span class='label'>Total Characters:</span> "
                f"<span class='value'>{stats.get('total_characters', 0):,}</span></div>"
            ),
        ])

        # Optional file size
        if "file_size_bytes" in stats:
            html.append(
                f"                <div class='stat'>"
                f"<span class='label'>File Size:</span> "
                f"<span class='value'>{format_size(stats['file_size_bytes'])}</span>"
                f"</div>",
            )

        html.extend([
            "            </div>",
            "        </div>",
        ])

    def _add_message_types_html(self, html: list[str], stats: dict[str, Any]) -> None:
        """Add message types section to HTML report."""
        if "message_types" not in stats:
            return

        html.extend([
            "        <div class='section'>",
            "            <h2>Message Types</h2>",
            "            <div class='stats-grid'>",
        ])

        for msg_type, count in stats["message_types"].items():
            html.append(
                f"                <div class='stat'><span class='label'>"
                f"{msg_type.capitalize()}:</span> "
                f"<span class='value'>{count:,}</span></div>",
            )

        html.extend([
            "            </div>",
            "        </div>",
        ])

    def _add_compression_potential_html(
        self, html: list[str], stats: dict[str, Any],
    ) -> None:
        """Add compression potential section to HTML report."""
        if "compression_potential" not in stats:
            return

        html.extend([
            "        <div class='section'>",
            "            <h2>Compression Potential</h2>",
            "            <div class='compression-table'>",
            "                <table>",
            "                    <tr><th>Level</th><th>Reduction</th>"
            "<th>Size Saved</th></tr>",
        ])

        for level, data in stats["compression_potential"].items():
            ratio = data.get("ratio", 0) * 100
            size_reduction = data.get("size_reduction", 0)
            html.append(
                f"                    <tr><td>{level.capitalize()}</td>"
                f"<td>{ratio:.1f}%</td><td>{format_size(size_reduction)}</td></tr>",
            )

        html.extend([
            "                </table>",
            "            </div>",
            "        </div>",
        ])

    def _add_performance_html(self, html: list[str], stats: dict[str, Any]) -> None:
        """Add performance section to HTML report."""
        if "analysis_time" not in stats:
            return

        html.extend([
            "        <div class='section'>",
            "            <h2>Analysis Performance</h2>",
            "            <div class='stats-grid'>",
        ])

        html.append(
            f"                <div class='stat'>"
            f"<span class='label'>Analysis Time:</span> "
            f"<span class='value'>{stats['analysis_time']:.3f} seconds</span></div>",
        )

        messages_per_sec = (
            stats.get("total_messages", 0) / max(stats["analysis_time"], 0.001)
        )
        html.append(
            f"                <div class='stat'>"
            f"<span class='label'>Messages/Second:</span> "
            f"<span class='value'>{messages_per_sec:,.0f}</span></div>",
        )

        html.extend([
            "            </div>",
            "        </div>",
        ])

    def _add_html_footer(self, html: list[str]) -> None:
        """Add HTML document footer."""
        html.extend([
            "    </div>",
            "</body>",
            "</html>",
        ])

    def display_interactive(self, stats: dict[str, Any]) -> None:
        """Display interactive report (for CLI usage)."""
        # For CLI, just print the table format

    def _make_json_serializable(self, obj: object) -> object:
        """Convert object to JSON serializable format."""
        return self._convert_object_type(obj)

    def _convert_object_type(self, obj: object) -> object:
        """Convert object based on its type."""
        if isinstance(obj, dict):
            return self._serialize_dict(obj)
        if isinstance(obj, list | tuple):
            return self._serialize_sequence(obj)
        return self._convert_special_types(obj)

    def _convert_special_types(self, obj: object) -> object:
        """Convert special object types."""
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "__dict__"):
            return self._make_json_serializable(obj.__dict__)
        return obj

    def _serialize_dict(self, obj: dict[Any, Any]) -> dict[Any, Any]:
        """Serialize dictionary recursively."""
        return {k: self._make_json_serializable(v) for k, v in obj.items()}

    def _serialize_sequence(self, obj: list | tuple) -> list[Any]:
        """Serialize list or tuple recursively."""
        return [self._make_json_serializable(item) for item in obj]

    def _get_html_styles(self) -> str:
        """Get CSS styles for HTML report."""
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
    """Main statistics generator for JSONL files and directories."""

    def __init__(self, *, verbose: bool = False) -> None:
        """Initialize JSONLStatsGenerator.

        Args:
            verbose: Enable verbose logging output.

        """
        self.verbose = verbose
        self.analyzer = JSONLAnalyzer()
        self.importance_scorer = ImportanceScorer()
        self.score_analyzer = MessageScoreAnalyzer(self.importance_scorer)
        self.pattern_analyzer = PatternAnalyzer()
        self.trend_analyzer = TrendAnalyzer()
        self.formatter = ReportFormatter()

        if verbose:
            logger.setLevel(logging.DEBUG)

    def analyze_file(
        self,
        file_path: Path,
        *,
        include_trends: bool = False,
        include_patterns: bool = False,
        include_importance: bool = False,
    ) -> dict[str, Any]:
        """Analyze a single JSONL file.

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
            logger.info("Analyzing file: %s", file_path)

        return self._perform_file_analysis(
            file_path,
            start_time,
            include_trends=include_trends,
            include_patterns=include_patterns,
            include_importance=include_importance,
        )

    def _perform_file_analysis(
        self,
        file_path: Path,
        start_time: float,
        *,
        include_trends: bool,
        include_patterns: bool,
        include_importance: bool,
    ) -> dict[str, Any]:
        """Perform the actual file analysis with error handling."""
        try:
            messages = self._load_and_validate_messages(file_path)
            if not messages:
                return self._create_empty_result(
                    str(file_path), time.time() - start_time,
                )

            result = self._calculate_basic_statistics(messages, file_path)
            self._add_optional_analyses(
                result,
                messages,
                include_importance=include_importance,
                include_patterns=include_patterns,
                include_trends=include_trends,
            )
            self._add_performance_metadata(result, messages, start_time)
            self._log_analysis_completion(messages, start_time)
        except Exception:
            logger.exception("Error analyzing file %s", file_path)
            raise
        else:
            return result

    def _log_analysis_completion(
        self, messages: list[dict[str, Any]], start_time: float,
    ) -> None:
        """Log analysis completion if verbose mode is enabled."""
        if self.verbose:
            analysis_time = time.time() - start_time
            logger.info(
                "Analysis complete: %d messages in %.3fs",
                len(messages),
                analysis_time,
            )

    def _load_and_validate_messages(self, file_path: Path) -> list[dict[str, Any]]:
        """Load and validate messages from JSONL file."""
        messages = self.analyzer.parse_jsonl_file(file_path)
        if not messages:
            logger.warning("No messages found in %s", file_path)
        return messages

    def _add_optional_analyses(
        self,
        result: dict[str, Any],
        messages: list[dict[str, Any]],
        *,
        include_importance: bool,
        include_patterns: bool,
        include_trends: bool,
    ) -> None:
        """Add optional analysis sections to results."""
        if include_importance:
            self._add_importance_analysis(result, messages)

        if include_patterns:
            self._add_pattern_analysis(result, messages)

        if include_trends:
            self._add_trend_analysis(result, messages)

    def _add_importance_analysis(
        self, result: dict[str, Any], messages: list[dict[str, Any]],
    ) -> None:
        """Add importance distribution and compression potential analysis."""
        result["importance_distribution"] = self._analyze_importance_distribution(
            messages,
        )
        result["compression_potential"] = self._analyze_compression_potential(
            messages,
        )

    def _add_pattern_analysis(
        self, result: dict[str, Any], messages: list[dict[str, Any]],
    ) -> None:
        """Add pattern detection and content categorization analysis."""
        result["patterns_detected"] = self._analyze_patterns(messages)
        result["content_categories"] = self._categorize_content(messages)

    def _add_trend_analysis(
        self, result: dict[str, Any], messages: list[dict[str, Any]],
    ) -> None:
        """Add temporal and conversation flow analysis."""
        result["temporal_analysis"] = (
            self.trend_analyzer.analyze_temporal_patterns(messages)
        )
        result["conversation_flow"] = (
            self.trend_analyzer.analyze_conversation_flow(messages)
        )
        result["content_evolution"] = (
            self.trend_analyzer.detect_content_evolution(messages)
        )
        result["analysis_recommendations"] = (
            self.trend_analyzer.predict_compression_benefits(messages)
        )

    def _add_performance_metadata(
        self, result: dict[str, Any], messages: list[dict[str, Any]], start_time: float,
    ) -> None:
        """Add performance metadata to analysis results."""
        analysis_time = time.time() - start_time
        result["analysis_time"] = analysis_time
        result["analysis_performance"] = {
            "processing_time": analysis_time,
            "messages_per_second": len(messages) / max(analysis_time, 0.001),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def analyze_directory(
        self,
        directory: Path,
        *,
        recursive: bool = False,
        include_trends: bool = False,
        include_patterns: bool = False,
        include_importance: bool = False,
    ) -> dict[str, Any]:
        """Analyze all JSONL files in a directory.

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
            logger.info(
                "Analyzing directory: %s (recursive: %s)",
                directory,
                recursive,
            )

        valid_files = self._discover_valid_jsonl_files(directory, recursive=recursive)

        if not valid_files:
            return self._create_empty_directory_result(start_time)

        logger.info("Found %d JSONL files to analyze", len(valid_files))

        per_file_stats, all_messages, total_size = self._analyze_all_files(
            valid_files,
            include_trends=include_trends,
            include_patterns=include_patterns,
            include_importance=include_importance,
        )

        config = AnalysisConfig(
            include_patterns=include_patterns,
            include_trends=include_trends,
            recursive=recursive,
            start_time=start_time,
        )
        data = ProcessedDirectoryData(
            valid_files=valid_files,
            per_file_stats=per_file_stats,
            all_messages=all_messages,
            total_size=total_size,
        )
        return self._build_directory_result(data, directory, config)

    def _discover_valid_jsonl_files(
        self, directory: Path, *, recursive: bool,
    ) -> list[Path]:
        """Discover and filter valid JSONL files in directory."""
        if recursive:
            jsonl_files = list(directory.rglob("*.jsonl"))
        else:
            jsonl_files = list(directory.glob("*.jsonl"))

        return [f for f in jsonl_files if is_jsonl_file(f)]

    def _create_empty_directory_result(self, start_time: float) -> dict[str, Any]:
        """Create result for directory with no JSONL files."""
        logger.warning("No JSONL files found in directory")
        return {
            "total_files": 0,
            "total_messages": 0,
            "per_file_stats": [],
            "aggregated_stats": {},
            "analysis_time": time.time() - start_time,
        }

    def _analyze_all_files(
        self,
        valid_files: list[Path],
        *,
        include_trends: bool,
        include_patterns: bool,
        include_importance: bool,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
        """Analyze all files and collect statistics and messages."""
        per_file_stats = []
        all_messages = []
        total_size = 0

        for file_path in valid_files:
            file_stats, file_messages, file_size = (
                self._analyze_single_file_for_directory(
                    file_path,
                    include_trends=include_trends,
                    include_patterns=include_patterns,
                    include_importance=include_importance,
                )
            )

            per_file_stats.append(file_stats)
            all_messages.extend(file_messages)
            total_size += file_size

        return per_file_stats, all_messages, total_size

    def _analyze_single_file_for_directory(
        self,
        file_path: Path,
        *,
        include_trends: bool,
        include_patterns: bool,
        include_importance: bool,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
        """Analyze a single file and return stats, messages, and size."""
        try:
            file_stats = self.analyze_file(
                file_path,
                include_trends=include_trends,
                include_patterns=include_patterns,
                include_importance=include_importance,
            )
            file_messages = self.analyzer.parse_jsonl_file(file_path)
            file_size = file_path.stat().st_size
        except Exception as e:
            logger.exception("Failed to analyze %s", file_path)
            error_stats = self._create_error_stats(str(e))
            return error_stats, [], 0
        else:
            return file_stats, file_messages, file_size

    def _create_error_stats(self, error_message: str) -> dict[str, Any]:
        """Create error stats dictionary for failed file processing."""
        return {
            "error": error_message,
            "total_messages": 0,
            "analysis_time": 0,
        }

    def _build_directory_result(
        self,
        data: ProcessedDirectoryData,
        directory: Path,
        config: AnalysisConfig,
    ) -> dict[str, Any]:
        """Build the final directory analysis result."""
        aggregated_stats = self._calculate_aggregated_statistics(
            data.per_file_stats, data.total_size,
        )
        analysis_time = time.time() - config.start_time

        result = {
            "total_files": len(data.valid_files),
            "total_messages": len(data.all_messages),
            "per_file_stats": data.per_file_stats,
            "aggregated_stats": aggregated_stats,
            "analysis_time": analysis_time,
            "directory": str(directory),
            "recursive": config.recursive,
            "file_diversity": self._analyze_file_diversity(data.per_file_stats),
            "cross_file_patterns": (
                self._analyze_cross_file_patterns(data.per_file_stats)
                if config.include_patterns
                else None
            ),
        }

        if config.include_trends and data.all_messages:
            result["directory_trends"] = self.trend_analyzer.analyze_temporal_patterns(
                data.all_messages,
            )

        if self.verbose:
            logger.info(
                "Directory analysis complete: %d files, %d messages in %.3fs",
                len(data.valid_files),
                len(data.all_messages),
                analysis_time,
            )

        return result

    def simulate_analysis_levels(
        self,
        file_path: Path,
        levels: list[str] | None = None,
    ) -> dict[str, Any]:
        """Simulate different analysis levels without modifying files.

        Args:
            file_path: Path to JSONL file
            levels: List of analysis levels to simulate

        Returns:
            Dictionary with analysis simulation results

        """
        if levels is None:
            levels = ["light", "medium", "aggressive"]

        try:
            messages = self.analyzer.parse_jsonl_file(file_path)

            if not messages:
                return {level: {"error": "no_messages"} for level in levels}

            return self._simulate_all_levels(messages, file_path, levels)

        except Exception as e:
            logger.exception("Analysis simulation failed for %s", file_path)
            return {level: {"error": str(e)} for level in levels}

    def _simulate_all_levels(
        self,
        messages: list[dict[str, Any]],
        file_path: Path,
        levels: list[str],
    ) -> dict[str, Any]:
        """Simulate analysis for all specified levels."""
        results = {}
        original_size = file_path.stat().st_size

        for level in levels:
            preserved_count = self._count_preserved_messages(messages, level)
            results[level] = self._create_level_simulation_result(
                messages, preserved_count, original_size,
            )

        return results

    def _count_preserved_messages(
        self, messages: list[dict[str, Any]], level: str,
    ) -> int:
        """Count messages that would be preserved at the given analysis level."""
        threshold_map = {"light": 20, "medium": 40, "aggressive": 60}
        threshold = threshold_map[level]

        preserved_count = 0
        for message in messages:
            score = self.importance_scorer.calculate_message_importance(message)
            if score >= threshold:
                preserved_count += 1

        return preserved_count

    def _create_level_simulation_result(
        self,
        messages: list[dict[str, Any]],
        preserved_count: int,
        original_size: int,
    ) -> dict[str, Any]:
        """Create simulation result for a single analysis level."""
        removed_count = len(messages) - preserved_count
        compression_ratio = removed_count / len(messages) if messages else 0

        # Estimate size reduction
        estimated_final_size = int(original_size * (1 - compression_ratio * 0.8))
        estimated_reduction = original_size - estimated_final_size

        return {
            "messages_would_analyze": preserved_count,
            "messages_would_filter": removed_count,
            "analysis_ratio": compression_ratio,
            "estimated_focus_reduction": estimated_reduction,
            "estimated_focus_size": estimated_final_size,
            "estimated_focus_reduction_percent": (
                (estimated_reduction / original_size * 100) if original_size > 0 else 0
            ),
        }

    def export_report(
        self,
        stats: dict[str, Any],
        output_path: Path,
        format_type: str,
    ) -> None:
        """Export analysis report to file.

        Args:
            stats: Statistics dictionary
            output_path: Output file path
            format_type: Format type ('json', 'csv', 'html', 'table')

        """
        try:
            content = self._generate_report_content(stats, format_type)
            self._write_report_to_file(content, output_path, format_type)

        except Exception:
            logger.exception("Failed to export report")
            raise

    def _generate_report_content(self, stats: dict[str, Any], format_type: str) -> str:
        """Generate report content in the specified format."""
        format_methods = {
            "json": self.formatter.format_json,
            "csv": self.formatter.format_csv,
            "html": self.formatter.format_html,
            "table": self.formatter.format_table,
        }

        if format_type not in format_methods:
            msg = f"Unsupported format: {format_type}"
            raise ValueError(msg)

        return format_methods[format_type](stats)

    def _write_report_to_file(
        self, content: str, output_path: Path, format_type: str,
    ) -> None:
        """Write report content to file."""
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        with output_path.open("w", encoding="utf-8") as f:
            f.write(content)

        if self.verbose:
            logger.info("Report exported to %s in %s format", output_path, format_type)

    def display_report(
        self,
        stats: dict[str, Any],
        format_type: str = "table",
    ) -> None:
        """Display report to console.

        Args:
            stats: Statistics dictionary
            format_type: Display format ('table', 'json')

        """
        try:
            if format_type == "table":
                self.formatter.format_table(stats)
            elif format_type == "json":
                self.formatter.format_json(stats)
            else:
                self.formatter.format_table(
                    stats,
                )  # Default to table

        except Exception:
            logger.exception("Failed to display report")
            raise

    def _calculate_basic_statistics(
        self,
        messages: list[dict[str, Any]],
        file_path: Path,
    ) -> dict[str, Any]:
        """Calculate basic statistics for messages."""
        if not messages:
            return self._create_empty_result(str(file_path), 0)

        # Message type distribution
        message_types = Counter(m.get("type", "unknown") for m in messages)

        # Content analysis
        content_lengths = []
        total_characters = 0

        for message in messages:
            content = message.get("message", {}).get("content", "")
            content_length = len(content)
            content_lengths.append(content_length)
            total_characters += content_length

        average_length = statistics.mean(content_lengths) if content_lengths else 0

        return {
            "file_path": str(file_path),
            "total_messages": len(messages),
            "message_types": dict(message_types),
            "average_message_length": average_length,
            "median_message_length": (
                statistics.median(content_lengths) if content_lengths else 0
            ),
            "total_characters": total_characters,
            "file_size_bytes": file_path.stat().st_size,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _analyze_importance_distribution(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Analyze importance score distribution."""
        scores = []
        for message in messages:
            score = self.importance_scorer.calculate_message_importance(
                message,
            )
            scores.append(score)

        if not scores:
            return {"high": 0, "medium": 0, "low": 0}

        high_count = len([s for s in scores if s >= SCORE_HIGH_THRESHOLD])
        medium_count = len([
            s for s in scores
            if SCORE_MEDIUM_THRESHOLD <= s < SCORE_HIGH_THRESHOLD
        ])
        low_count = len([s for s in scores if s < SCORE_MEDIUM_THRESHOLD])

        return {
            "high_importance_messages": high_count,
            "medium_importance_messages": medium_count,
            "low_importance_messages": low_count,
            "average_importance_score": statistics.mean(scores),
            "median_importance_score": statistics.median(scores),
            "score_distribution": {
                "high": high_count,
                "medium": medium_count,
                "low": low_count,
            },
        }

    def _analyze_compression_potential(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Analyze compression potential for different levels."""
        potential = {}

        for level in ["light", "medium", "aggressive"]:
            threshold = {"light": 20, "medium": 40, "aggressive": 60}[level]
            preserved = 0

            for message in messages:
                score = self.importance_scorer.calculate_message_importance(
                    message,
                )
                if score >= threshold:
                    preserved += 1

            removed = len(messages) - preserved
            ratio = removed / len(messages) if messages else 0

            # Rough size estimation
            avg_message_size = 150  # Rough estimate
            estimated_size_reduction = removed * avg_message_size

            potential[level] = {
                "messages_preserved": preserved,
                "messages_removed": removed,
                "ratio": ratio,
                "size_reduction": estimated_size_reduction,
            }

        return potential

    def _analyze_patterns(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Analyze content patterns."""
        code_blocks = 0
        urls = 0
        file_paths = 0
        commands = 0

        for message in messages:
            content = message.get("message", {}).get("content", "")

            # Use pattern analyzer
            patterns = self.pattern_analyzer.analyze_content(content)

            code_blocks += len(patterns.get("code_blocks", []))
            urls += len(patterns.get("urls", []))
            file_paths += len(patterns.get("file_paths", []))
            commands += len(patterns.get("commands", []))

        return {
            "code_blocks": code_blocks,
            "urls": urls,
            "file_paths": file_paths,
            "commands": commands,
        }

    def _categorize_content(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Categorize content types."""
        categories = {
            "programming_content": 0,
            "conversational_content": 0,
            "system_content": 0,
            "error_debugging": 0,
            "documentation": 0,
        }

        for message in messages:
            category = self._determine_message_category(message)
            categories[category] += 1

        return categories

    def _determine_message_category(self, message: dict[str, Any]) -> str:
        """Determine the category for a single message."""
        content = message.get("message", {}).get("content", "").lower()
        msg_type = message.get("type", "")

        # Check message type first
        if msg_type == "system":
            return "system_content"

        # Check content patterns in priority order
        category_patterns = {
            "error_debugging": ["error", "exception", "traceback", "debug"],
            "programming_content": ["```", "function", "class", "import", "def"],
            "documentation": ["documentation", "readme", "guide", "tutorial"],
        }

        for category, patterns in category_patterns.items():
            if any(term in content for term in patterns):
                return category

        # Default to conversational content
        return "conversational_content"

    def _calculate_aggregated_statistics(
        self, per_file_stats: list[dict[str, Any]], total_size: int,
    ) -> dict[str, Any]:
        """Calculate aggregated statistics across all files."""
        if not per_file_stats:
            return {}

        # Aggregate basic metrics
        total_messages = sum(stats.get("total_messages", 0) for stats in per_file_stats)
        total_chars = sum(stats.get("total_characters", 0) for stats in per_file_stats)
        avg_messages_per_file = (
            total_messages / len(per_file_stats) if per_file_stats else 0
        )

        # Aggregate message types
        aggregated_types: defaultdict[str, int] = defaultdict(int)
        for stats in per_file_stats:
            for msg_type, count in stats.get("message_types", {}).items():
                aggregated_types[msg_type] += count

        return {
            "total_size_bytes": total_size,
            "total_characters": total_chars,
            "average_messages_per_file": avg_messages_per_file,
            "aggregated_message_types": dict(aggregated_types),
            "files_with_errors": len(
                [s for s in per_file_stats if "error" in s],
            ),
            "average_file_size": (
                total_size / len(per_file_stats) if per_file_stats else 0
            ),
        }

    def _analyze_file_diversity(
        self,
        per_file_stats: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Analyze diversity across files."""
        if not per_file_stats:
            return {}

        message_counts = [
            stats.get("total_messages", 0)
            for stats in per_file_stats
            if "error" not in stats
        ]

        if not message_counts:
            return {"diversity": "no_data"}

        # Calculate coefficient of variation
        mean_messages = statistics.mean(message_counts)
        std_messages = (
            statistics.stdev(message_counts) if len(message_counts) > 1 else 0
        )
        cv = std_messages / mean_messages if mean_messages > 0 else 0

        if cv > HIGH_DIVERSITY_CV_THRESHOLD:
            diversity_level = "high"
        elif cv > MEDIUM_DIVERSITY_CV_THRESHOLD:
            diversity_level = "medium"
        else:
            diversity_level = "low"

        return {
            "diversity_level": diversity_level,
            "coefficient_of_variation": cv,
            "min_messages": min(message_counts),
            "max_messages": max(message_counts),
            "mean_messages": mean_messages,
        }

    def _analyze_cross_file_patterns(
        self,
        per_file_stats: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Analyze patterns that span across files."""
        if not per_file_stats:
            return {}

        # Simple cross-file pattern analysis
        files_with_code = len(
            [
                s
                for s in per_file_stats
                if s.get("patterns_detected", {}).get("code_blocks", 0) > 0
            ],
        )

        files_with_errors = len(
            [
                s
                for s in per_file_stats
                if s.get("content_categories", {}).get("error_debugging", 0) > 0
            ],
        )

        return {
            "files_with_code_blocks": files_with_code,
            "files_with_error_content": files_with_errors,
            "code_prevalence": (
                files_with_code / len(per_file_stats) if per_file_stats else 0
            ),
            "error_prevalence": (
                files_with_errors / len(per_file_stats) if per_file_stats else 0
            ),
        }

    def _create_empty_result(
        self,
        file_path: str,
        analysis_time: float,
    ) -> dict[str, Any]:
        """Create empty result for files with no messages."""
        return {
            "file_path": file_path,
            "total_messages": 0,
            "message_types": {},
            "average_message_length": 0,
            "total_characters": 0,
            "file_size_bytes": 0,
            "analysis_time": analysis_time,
            "timestamp": datetime.now(UTC).isoformat(),
        }
