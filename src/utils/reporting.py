"""
Validation Reporting and Monitoring Framework
Phase 3 - Comprehensive reporting and alerting for safety operations

Features:
- Detailed validation reports with pass/fail status
- Performance metrics tracking and analysis
- Quality metrics and trend analysis
- Error logging with actionable recommendations
- Alerting systems for validation failures
- Real-time monitoring dashboards
"""

import json
import logging
import time
import sqlite3
import os
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import statistics

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
    """Structured validation report"""
    report_id: str
    timestamp: str
    operation_type: str
    overall_status: str
    validation_summary: Dict[str, Any]
    detailed_results: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    recommendations: List[str]
    failed_levels: List[str]
    error_count: int
    warning_count: int


@dataclass
class PerformanceMetric:
    """Performance measurement data"""
    operation: str
    start_time: float
    end_time: float
    duration: float
    memory_usage_mb: float
    cpu_usage_percent: float
    metadata: Dict[str, Any]


@dataclass
class QualityMetric:
    """Quality measurement data"""
    timestamp: str
    compression_ratio: float
    false_positive_rate: float
    integrity_maintained: bool
    processing_speed: float
    error_rate: float
    user_satisfaction: Optional[float]


class ValidationReporter:
    """
    Comprehensive validation reporting system
    
    Generates detailed reports with actionable insights and recommendations
    """
    
    def __init__(self, report_dir: Optional[Path] = None):
        """
        Initialize validation reporter
        
        Args:
            report_dir: Custom directory for reports (default: ~/.claude/reports)
        """
        if report_dir:
            self.report_dir = report_dir
        else:
            self.report_dir = Path.home() / '.claude' / 'reports'
        
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # Report templates and configurations
        self.report_templates = {
            'comprehensive': self._comprehensive_report_template,
            'summary': self._summary_report_template,
            'performance': self._performance_report_template,
            'quality': self._quality_report_template
        }
    
    def generate_validation_report(
        self, 
        validation_results: Dict[str, Any],
        operation_type: str = 'analysis',
        report_type: str = 'comprehensive'
    ) -> Dict[str, Any]:
        """
        Generate comprehensive validation report
        
        Args:
            validation_results: Results from ValidationFramework.run_comprehensive_validation
            operation_type: Type of operation being reported
            report_type: Type of report to generate
            
        Returns:
            Dictionary containing the generated report
        """
        try:
            report_id = f"{operation_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            timestamp = datetime.now().isoformat()
            
            # Determine overall status
            overall_status = 'PASSED' if validation_results.get('overall_valid', False) else 'FAILED'
            
            # Extract failed levels
            failed_levels = validation_results.get('failed_levels', [])
            
            # Count errors and warnings
            error_count = validation_results.get('total_errors', 0)
            warning_count = validation_results.get('total_warnings', 0)
            
            # Generate validation summary
            validation_summary = {
                'total_levels_tested': 5,
                'levels_passed': 5 - len(failed_levels),
                'levels_failed': len(failed_levels),
                'success_rate': (5 - len(failed_levels)) / 5,
                'critical_failures': self._identify_critical_failures(validation_results),
                'validation_time': validation_results.get('validation_time', 0.0)
            }
            
            # Extract performance metrics
            performance_metrics = {
                'total_validation_time': validation_results.get('validation_time', 0.0),
                'individual_level_times': validation_results.get('performance_summary', {}).get('level_times', []),
                'within_5s_target': validation_results.get('performance_summary', {}).get('within_5s_target', False),
                'average_level_time': 0.0,
                'slowest_level': None,
                'fastest_level': None
            }
            
            # Calculate performance statistics
            if performance_metrics['individual_level_times']:
                level_times = performance_metrics['individual_level_times']
                performance_metrics['average_level_time'] = statistics.mean(level_times)
                performance_metrics['slowest_level'] = f"level_{level_times.index(max(level_times))}"
                performance_metrics['fastest_level'] = f"level_{level_times.index(min(level_times))}"
            
            # Extract quality metrics
            quality_metrics = self._extract_quality_metrics(validation_results)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(validation_results, failed_levels)
            
            # Create report structure
            report = ValidationReport(
                report_id=report_id,
                timestamp=timestamp,
                operation_type=operation_type,
                overall_status=overall_status,
                validation_summary=validation_summary,
                detailed_results=validation_results,
                performance_metrics=performance_metrics,
                quality_metrics=quality_metrics,
                recommendations=recommendations,
                failed_levels=failed_levels,
                error_count=error_count,
                warning_count=warning_count
            )
            
            # Generate report using template
            if report_type in self.report_templates:
                formatted_report = self.report_templates[report_type](report)
            else:
                formatted_report = self._comprehensive_report_template(report)
            
            # Save report to file
            report_file = self.report_dir / f"{report_id}.json"
            with open(report_file, 'w') as f:
                json.dump(formatted_report, f, indent=2)
            
            logger.info(f"Generated {report_type} validation report: {report_id}")
            return formatted_report
            
        except Exception as e:
            logger.error(f"Error generating validation report: {e}")
            return {
                'error': str(e),
                'report_generation_failed': True,
                'timestamp': datetime.now().isoformat()
            }
    
    def _comprehensive_report_template(self, report: ValidationReport) -> Dict[str, Any]:
        """Generate comprehensive report template"""
        return {
            'report_metadata': {
                'report_id': report.report_id,
                'timestamp': report.timestamp,
                'operation_type': report.operation_type,
                'report_type': 'comprehensive'
            },
            'executive_summary': {
                'overall_status': report.overall_status,
                'success_rate': f"{report.validation_summary['success_rate']:.1%}",
                'critical_issues': len(report.validation_summary['critical_failures']),
                'recommendations_count': len(report.recommendations),
                'performance_acceptable': report.performance_metrics['within_5s_target']
            },
            'validation_results': {
                'summary': report.validation_summary,
                'detailed_breakdown': {
                    'level_0_pre_operation': self._format_level_result(report.detailed_results.get('level_0', {})),
                    'level_1_backup_integrity': self._format_level_result(report.detailed_results.get('level_1', {})),
                    'level_2_analysis_integrity': self._format_level_result(report.detailed_results.get('level_2', {})),
                    'level_3_post_operation': self._format_level_result(report.detailed_results.get('level_3', {})),
                    'level_4_recovery_testing': self._format_level_result(report.detailed_results.get('level_4', {}))
                }
            },
            'performance_analysis': {
                'timing_analysis': report.performance_metrics,
                'bottleneck_identification': self._identify_performance_bottlenecks(report.performance_metrics),
                'optimization_suggestions': self._suggest_performance_optimizations(report.performance_metrics)
            },
            'quality_assessment': {
                'metrics': report.quality_metrics,
                'quality_score': self._calculate_quality_score(report.quality_metrics),
                'trend_analysis': 'Baseline measurement' if not hasattr(self, 'historical_quality') else self._analyze_quality_trends()
            },
            'recommendations': {
                'immediate_actions': [rec for rec in report.recommendations if 'immediate' in rec.lower()],
                'preventive_measures': [rec for rec in report.recommendations if 'prevent' in rec.lower()],
                'optimization_opportunities': [rec for rec in report.recommendations if 'optimize' in rec.lower()]
            },
            'error_analysis': {
                'error_summary': {
                    'total_errors': report.error_count,
                    'total_warnings': report.warning_count,
                    'failed_levels': report.failed_levels
                },
                'error_details': self._extract_error_details(report.detailed_results),
                'impact_assessment': self._assess_error_impact(report.detailed_results)
            }
        }
    
    def _summary_report_template(self, report: ValidationReport) -> Dict[str, Any]:
        """Generate summary report template"""
        return {
            'report_id': report.report_id,
            'timestamp': report.timestamp,
            'overall_status': report.overall_status,
            'summary': {
                'levels_passed': report.validation_summary['levels_passed'],
                'levels_failed': report.validation_summary['levels_failed'],
                'validation_time': f"{report.performance_metrics['total_validation_time']:.3f}s",
                'quality_score': self._calculate_quality_score(report.quality_metrics),
                'recommendations_count': len(report.recommendations)
            },
            'key_issues': report.validation_summary['critical_failures'][:3],  # Top 3 issues
            'top_recommendations': report.recommendations[:3]  # Top 3 recommendations
        }
    
    def _performance_report_template(self, report: ValidationReport) -> Dict[str, Any]:
        """Generate performance-focused report template"""
        return {
            'report_id': report.report_id,
            'timestamp': report.timestamp,
            'performance_summary': {
                'total_time': report.performance_metrics['total_validation_time'],
                'target_met': report.performance_metrics['within_5s_target'],
                'average_level_time': report.performance_metrics['average_level_time'],
                'performance_rating': 'Excellent' if report.performance_metrics['within_5s_target'] else 'Needs Improvement'
            },
            'timing_breakdown': {
                'level_times': report.performance_metrics['individual_level_times'],
                'slowest_level': report.performance_metrics['slowest_level'],
                'fastest_level': report.performance_metrics['fastest_level']
            },
            'optimization_recommendations': self._suggest_performance_optimizations(report.performance_metrics)
        }
    
    def _quality_report_template(self, report: ValidationReport) -> Dict[str, Any]:
        """Generate quality-focused report template"""
        quality_score = self._calculate_quality_score(report.quality_metrics)
        
        return {
            'report_id': report.report_id,
            'timestamp': report.timestamp,
            'quality_summary': {
                'overall_score': quality_score,
                'rating': self._get_quality_rating(quality_score),
                'false_positive_rate': report.quality_metrics.get('false_positive_rate', 0.0),
                'integrity_maintained': report.quality_metrics.get('integrity_maintained', True)
            },
            'quality_metrics': report.quality_metrics,
            'quality_recommendations': [
                rec for rec in report.recommendations 
                if any(keyword in rec.lower() for keyword in ['quality', 'accuracy', 'precision'])
            ]
        }
    
    def _identify_critical_failures(self, validation_results: Dict[str, Any]) -> List[str]:
        """Identify critical validation failures"""
        critical_failures = []
        
        for level_key, level_result in validation_results.items():
            if level_key.startswith('level_') and isinstance(level_result, dict):
                if not level_result.get('valid', True):
                    for error in level_result.get('errors', []):
                        if any(keyword in error.lower() for keyword in ['critical', 'corruption', 'integrity', 'loss']):
                            critical_failures.append(f"{level_key}: {error}")
        
        return critical_failures
    
    def _extract_quality_metrics(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract quality metrics from validation results"""
        quality_metrics = {
            'false_positive_rate': 0.0,
            'integrity_maintained': True,
            'compression_efficiency': 0.0,
            'processing_accuracy': 1.0,
            'data_preservation_rate': 1.0
        }
        
        # Extract from level 2 results (analysis integrity)
        level_2 = validation_results.get('level_2', {})
        if level_2:
            quality_metrics['false_positive_rate'] = level_2.get('false_positive_rate', 0.0)
            quality_metrics['integrity_maintained'] = level_2.get('conversation_chains_intact', True)
            quality_metrics['compression_efficiency'] = level_2.get('compression_ratio', 0.0)
        
        # Extract from level 3 results (post-operation)
        level_3 = validation_results.get('level_3', {})
        if level_3:
            quality_metrics['processing_accuracy'] = 1.0 if level_3.get('format_valid', True) else 0.0
        
        return quality_metrics
    
    def _generate_recommendations(self, validation_results: Dict[str, Any], failed_levels: List[str]) -> List[str]:
        """Generate actionable recommendations based on validation results"""
        recommendations = []
        
        # Level-specific recommendations
        if 'level_0' in failed_levels:
            recommendations.append("Immediate: Verify file accessibility and format before processing")
            recommendations.append("Preventive: Implement pre-processing file validation checks")
        
        if 'level_1' in failed_levels:
            recommendations.append("Critical: Check backup creation process and storage integrity")
            recommendations.append("Immediate: Verify backup storage location has sufficient space")
        
        if 'level_2' in failed_levels:
            level_2 = validation_results.get('level_2', {})
            if level_2.get('false_positive_rate', 0) > 0.01:
                recommendations.append("Optimize: Adjust importance scoring to reduce false positive rate")
            if not level_2.get('conversation_chains_intact', True):
                recommendations.append("Critical: Review conversation dependency preservation logic")
        
        if 'level_3' in failed_levels:
            recommendations.append("Immediate: Validate output file format and structure")
            recommendations.append("Optimize: Review compression targets and thresholds")
        
        if 'level_4' in failed_levels:
            recommendations.append("Critical: Test backup restoration procedures")
            recommendations.append("Preventive: Implement automated backup verification")
        
        # Performance recommendations
        performance = validation_results.get('performance_summary', {})
        if not performance.get('within_5s_target', True):
            recommendations.append("Optimize: Consider streaming processing for large files")
            recommendations.append("Optimize: Profile and optimize slowest validation levels")
        
        # Quality recommendations
        quality_metrics = self._extract_quality_metrics(validation_results)
        quality_score = self._calculate_quality_score(quality_metrics)
        if quality_score < 0.8:
            recommendations.append("Quality: Review and enhance validation criteria")
            recommendations.append("Quality: Implement additional quality assurance measures")
        
        return recommendations
    
    def _format_level_result(self, level_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format individual level result for reporting"""
        if not level_result:
            return {'status': 'Not Available', 'details': {}}
        
        return {
            'status': 'PASS' if level_result.get('valid', False) else 'FAIL',
            'duration': f"{level_result.get('duration', 0.0):.3f}s",
            'error_count': len(level_result.get('errors', [])),
            'warning_count': len(level_result.get('warnings', [])),
            'key_metrics': {k: v for k, v in level_result.items() 
                          if k not in ['valid', 'errors', 'warnings', 'duration']},
            'errors': level_result.get('errors', []),
            'warnings': level_result.get('warnings', [])
        }
    
    def _identify_performance_bottlenecks(self, performance_metrics: Dict[str, Any]) -> List[str]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        level_times = performance_metrics.get('individual_level_times', [])
        if level_times:
            avg_time = statistics.mean(level_times)
            for i, time_val in enumerate(level_times):
                if time_val > avg_time * 2:  # Significantly slower than average
                    bottlenecks.append(f"Level {i} takes {time_val:.3f}s (significantly above average {avg_time:.3f}s)")
        
        total_time = performance_metrics.get('total_validation_time', 0.0)
        if total_time > 5.0:
            bottlenecks.append(f"Total validation time {total_time:.3f}s exceeds 5s target")
        
        return bottlenecks
    
    def _suggest_performance_optimizations(self, performance_metrics: Dict[str, Any]) -> List[str]:
        """Suggest performance optimizations"""
        suggestions = []
        
        total_time = performance_metrics.get('total_validation_time', 0.0)
        if total_time > 5.0:
            suggestions.append("Consider parallel validation of independent levels")
            suggestions.append("Implement caching for repeated validations")
            suggestions.append("Optimize slowest validation level")
        
        level_times = performance_metrics.get('individual_level_times', [])
        if level_times and max(level_times) > 2.0:
            slowest_level = performance_metrics.get('slowest_level', 'unknown')
            suggestions.append(f"Focus optimization efforts on {slowest_level}")
        
        return suggestions
    
    def _calculate_quality_score(self, quality_metrics: Dict[str, Any]) -> float:
        """Calculate overall quality score (0.0 to 1.0)"""
        try:
            # Weighted scoring
            weights = {
                'false_positive_rate': -1.0,  # Lower is better
                'integrity_maintained': 0.3,
                'compression_efficiency': 0.2,
                'processing_accuracy': 0.3,
                'data_preservation_rate': 0.2
            }
            
            score = 0.0
            total_weight = 0.0
            
            for metric, weight in weights.items():
                if metric in quality_metrics:
                    value = quality_metrics[metric]
                    if metric == 'false_positive_rate':
                        # Convert false positive rate to positive score (1 - rate)
                        contribution = (1.0 - min(value, 1.0)) * abs(weight)
                    elif isinstance(value, bool):
                        contribution = (1.0 if value else 0.0) * weight
                    else:
                        contribution = min(value, 1.0) * weight
                    
                    score += contribution
                    total_weight += abs(weight)
            
            return max(0.0, min(1.0, score / total_weight if total_weight > 0 else 0.0))
            
        except Exception as e:
            logger.warning(f"Error calculating quality score: {e}")
            return 0.5  # Default middle score
    
    def _get_quality_rating(self, quality_score: float) -> str:
        """Convert quality score to rating"""
        if quality_score >= 0.9:
            return "Excellent"
        elif quality_score >= 0.8:
            return "Good" 
        elif quality_score >= 0.7:
            return "Acceptable"
        elif quality_score >= 0.6:
            return "Needs Improvement"
        else:
            return "Poor"
    
    def _extract_error_details(self, validation_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract detailed error information"""
        error_details = []
        
        for level_key, level_result in validation_results.items():
            if level_key.startswith('level_') and isinstance(level_result, dict):
                for error in level_result.get('errors', []):
                    error_details.append({
                        'level': level_key,
                        'error': error,
                        'severity': 'Critical' if any(keyword in error.lower() 
                                                    for keyword in ['critical', 'corruption', 'loss']) else 'High'
                    })
        
        return error_details
    
    def _assess_error_impact(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the impact of validation errors"""
        error_details = self._extract_error_details(validation_results)
        
        impact_assessment = {
            'data_loss_risk': 'Low',
            'operation_safety': 'Safe',
            'recommendation': 'Proceed with caution'
        }
        
        critical_errors = [err for err in error_details if err['severity'] == 'Critical']
        if critical_errors:
            impact_assessment['data_loss_risk'] = 'High'
            impact_assessment['operation_safety'] = 'Unsafe'
            impact_assessment['recommendation'] = 'Do not proceed - fix critical issues first'
        elif len(error_details) > 3:
            impact_assessment['data_loss_risk'] = 'Medium'
            impact_assessment['operation_safety'] = 'Risky'
            impact_assessment['recommendation'] = 'Review and fix errors before proceeding'
        
        return impact_assessment


class PerformanceTracker:
    """
    Performance metrics tracking and analysis system
    
    Monitors timing, memory usage, and resource utilization
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize performance tracker
        
        Args:
            db_path: Custom database path (default: ~/.claude/performance.db)
        """
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = Path.home() / '.claude' / 'performance.db'
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Active operations tracking
        self.active_operations = {}
        self.operation_history = deque(maxlen=1000)  # Keep last 1000 operations
        
        # Initialize database
        self._init_database()
    
    def start_operation(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start tracking an operation
        
        Args:
            operation_name: Name of the operation
            metadata: Optional metadata about the operation
            
        Returns:
            Operation ID for tracking
        """
        import psutil
        
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"
        
        self.active_operations[operation_id] = {
            'name': operation_name,
            'start_time': time.perf_counter(),
            'start_memory': psutil.Process().memory_info().rss / 1024 / 1024,  # MB
            'metadata': metadata or {}
        }
        
        return operation_id
    
    def end_operation(self, operation_id: str) -> Optional[PerformanceMetric]:
        """
        End tracking an operation
        
        Args:
            operation_id: Operation ID from start_operation
            
        Returns:
            PerformanceMetric object if operation was found
        """
        if operation_id not in self.active_operations:
            logger.warning(f"Operation {operation_id} not found in active operations")
            return None
        
        import psutil
        
        operation_data = self.active_operations.pop(operation_id)
        end_time = time.perf_counter()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        metric = PerformanceMetric(
            operation=operation_data['name'],
            start_time=operation_data['start_time'],
            end_time=end_time,
            duration=end_time - operation_data['start_time'],
            memory_usage_mb=end_memory - operation_data['start_memory'],
            cpu_usage_percent=psutil.Process().cpu_percent(),
            metadata=operation_data['metadata']
        )
        
        # Store in history and database
        self.operation_history.append(metric)
        self._store_metric(metric)
        
        return metric
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        try:
            # Calculate metrics from recent operations
            recent_operations = list(self.operation_history)[-100:]  # Last 100 operations
            
            if not recent_operations:
                return {
                    'operations': {},
                    'total_duration': 0.0,
                    'average_duration': 0.0,
                    'memory_usage': 0.0,
                    'cpu_usage': 0.0
                }
            
            # Group by operation type
            operations_by_type = defaultdict(list)
            for op in recent_operations:
                operations_by_type[op.operation].append(op)
            
            # Calculate statistics for each operation type
            operation_stats = {}
            for op_type, ops in operations_by_type.items():
                durations = [op.duration for op in ops]
                memory_usages = [op.memory_usage_mb for op in ops]
                
                operation_stats[op_type] = {
                    'count': len(ops),
                    'total_duration': sum(durations),
                    'average_duration': statistics.mean(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                    'average_memory_usage': statistics.mean(memory_usages),
                    'total_memory_usage': sum(memory_usages)
                }
            
            # Overall statistics
            all_durations = [op.duration for op in recent_operations]
            all_memory = [op.memory_usage_mb for op in recent_operations]
            
            return {
                'operations': operation_stats,
                'total_duration': sum(all_durations),
                'average_duration': statistics.mean(all_durations),
                'memory_usage': statistics.mean(all_memory),
                'cpu_usage': statistics.mean([op.cpu_usage_percent for op in recent_operations]),
                'operation_count': len(recent_operations),
                'performance_trends': self._analyze_performance_trends()
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {'error': str(e)}
    
    def _init_database(self):
        """Initialize SQLite database for performance tracking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        operation TEXT NOT NULL,
                        duration REAL NOT NULL,
                        memory_usage_mb REAL NOT NULL,
                        cpu_usage_percent REAL NOT NULL,
                        metadata TEXT
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize performance database: {e}")
    
    def _store_metric(self, metric: PerformanceMetric):
        """Store performance metric in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO performance_metrics 
                    (timestamp, operation, duration, memory_usage_mb, cpu_usage_percent, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    metric.operation,
                    metric.duration,
                    metric.memory_usage_mb,
                    metric.cpu_usage_percent,
                    json.dumps(metric.metadata)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store performance metric: {e}")
    
    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends from historical data"""
        try:
            # Get last 30 days of data
            cutoff_date = datetime.now() - timedelta(days=30)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT operation, duration, memory_usage_mb, timestamp
                    FROM performance_metrics
                    WHERE timestamp > ?
                    ORDER BY timestamp
                ''', (cutoff_date.isoformat(),))
                
                rows = cursor.fetchall()
            
            if not rows:
                return {'trend': 'insufficient_data'}
            
            # Analyze trends
            operations_by_day = defaultdict(list)
            for operation, duration, memory, timestamp in rows:
                day = datetime.fromisoformat(timestamp).date()
                operations_by_day[day].append({
                    'operation': operation,
                    'duration': duration,
                    'memory': memory
                })
            
            # Calculate daily averages
            daily_averages = []
            for day, ops in sorted(operations_by_day.items()):
                avg_duration = statistics.mean([op['duration'] for op in ops])
                avg_memory = statistics.mean([op['memory'] for op in ops])
                daily_averages.append({
                    'date': day.isoformat(),
                    'avg_duration': avg_duration,
                    'avg_memory': avg_memory,
                    'operation_count': len(ops)
                })
            
            # Determine trend
            if len(daily_averages) >= 7:
                recent_avg = statistics.mean([day['avg_duration'] for day in daily_averages[-7:]])
                earlier_avg = statistics.mean([day['avg_duration'] for day in daily_averages[:7]])
                
                if recent_avg < earlier_avg * 0.9:
                    trend = 'improving'
                elif recent_avg > earlier_avg * 1.1:
                    trend = 'degrading'
                else:
                    trend = 'stable'
            else:
                trend = 'insufficient_data'
            
            return {
                'trend': trend,
                'daily_averages': daily_averages[-14:],  # Last 14 days
                'total_operations': len(rows)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing performance trends: {e}")
            return {'trend': 'error', 'error': str(e)}


class QualityTracker:
    """
    Quality metrics tracking and trend analysis system
    
    Monitors quality indicators and identifies trends
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize quality tracker
        
        Args:
            db_path: Custom database path (default: ~/.claude/quality.db)
        """
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = Path.home() / '.claude' / 'quality.db'
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Quality history
        self.quality_history = deque(maxlen=500)  # Keep last 500 measurements
        
        # Initialize database
        self._init_database()
    
    def record_operation(self, quality_data: Dict[str, Any]):
        """
        Record quality metrics for an operation
        
        Args:
            quality_data: Dictionary containing quality metrics
        """
        try:
            timestamp = datetime.now().isoformat()
            
            metric = QualityMetric(
                timestamp=timestamp,
                compression_ratio=quality_data.get('compression_ratio', 0.0),
                false_positive_rate=quality_data.get('false_positive_rate', 0.0),
                integrity_maintained=quality_data.get('integrity_maintained', True),
                processing_speed=quality_data.get('processing_speed', 0.0),
                error_rate=quality_data.get('error_rate', 0.0),
                user_satisfaction=quality_data.get('user_satisfaction')
            )
            
            # Store in history and database
            self.quality_history.append(metric)
            self._store_quality_metric(metric)
            
        except Exception as e:
            logger.error(f"Error recording quality operation: {e}")
    
    def analyze_quality_trends(self) -> Dict[str, Any]:
        """Analyze quality trends and return comprehensive metrics"""
        try:
            if not self.quality_history:
                return {
                    'average_compression_ratio': 0.0,
                    'average_false_positive_rate': 0.0,
                    'integrity_success_rate': 1.0,
                    'trend_analysis': 'insufficient_data'
                }
            
            recent_metrics = list(self.quality_history)
            
            # Calculate averages
            avg_compression = statistics.mean([m.compression_ratio for m in recent_metrics])
            avg_false_positive = statistics.mean([m.false_positive_rate for m in recent_metrics])
            integrity_rate = sum(1 for m in recent_metrics if m.integrity_maintained) / len(recent_metrics)
            avg_error_rate = statistics.mean([m.error_rate for m in recent_metrics])
            
            # Trend analysis
            trend_analysis = self._analyze_trends(recent_metrics)
            
            # Quality score calculation
            quality_score = self._calculate_overall_quality_score(recent_metrics)
            
            return {
                'average_compression_ratio': avg_compression,
                'average_false_positive_rate': avg_false_positive,
                'integrity_success_rate': integrity_rate,
                'average_error_rate': avg_error_rate,
                'quality_score': quality_score,
                'trend_analysis': trend_analysis,
                'measurement_count': len(recent_metrics),
                'quality_rating': self._get_quality_rating(quality_score)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing quality trends: {e}")
            return {'error': str(e)}
    
    def _init_database(self):
        """Initialize SQLite database for quality tracking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS quality_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        compression_ratio REAL NOT NULL,
                        false_positive_rate REAL NOT NULL,
                        integrity_maintained INTEGER NOT NULL,
                        processing_speed REAL NOT NULL,
                        error_rate REAL NOT NULL,
                        user_satisfaction REAL
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize quality database: {e}")
    
    def _store_quality_metric(self, metric: QualityMetric):
        """Store quality metric in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO quality_metrics 
                    (timestamp, compression_ratio, false_positive_rate, integrity_maintained, 
                     processing_speed, error_rate, user_satisfaction)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metric.timestamp,
                    metric.compression_ratio,
                    metric.false_positive_rate,
                    1 if metric.integrity_maintained else 0,
                    metric.processing_speed,
                    metric.error_rate,
                    metric.user_satisfaction
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store quality metric: {e}")
    
    def _analyze_trends(self, metrics: List[QualityMetric]) -> Dict[str, Any]:
        """Analyze quality trends over time"""
        if len(metrics) < 10:
            return {'trend': 'insufficient_data'}
        
        try:
            # Split into recent and earlier periods
            mid_point = len(metrics) // 2
            earlier_metrics = metrics[:mid_point]
            recent_metrics = metrics[mid_point:]
            
            # Compare averages
            earlier_false_pos = statistics.mean([m.false_positive_rate for m in earlier_metrics])
            recent_false_pos = statistics.mean([m.false_positive_rate for m in recent_metrics])
            
            earlier_integrity = sum(1 for m in earlier_metrics if m.integrity_maintained) / len(earlier_metrics)
            recent_integrity = sum(1 for m in recent_metrics if m.integrity_maintained) / len(recent_metrics)
            
            # Determine trends
            false_pos_trend = 'improving' if recent_false_pos < earlier_false_pos else 'degrading' if recent_false_pos > earlier_false_pos else 'stable'
            integrity_trend = 'improving' if recent_integrity > earlier_integrity else 'degrading' if recent_integrity < earlier_integrity else 'stable'
            
            return {
                'false_positive_trend': false_pos_trend,
                'integrity_trend': integrity_trend,
                'overall_trend': 'improving' if false_pos_trend == 'improving' and integrity_trend != 'degrading' else 'degrading' if false_pos_trend == 'degrading' or integrity_trend == 'degrading' else 'stable'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {'trend': 'error', 'error': str(e)}
    
    def _calculate_overall_quality_score(self, metrics: List[QualityMetric]) -> float:
        """Calculate overall quality score from metrics"""
        if not metrics:
            return 0.5
        
        try:
            # Weighted scoring
            false_pos_score = 1.0 - statistics.mean([m.false_positive_rate for m in metrics])
            integrity_score = sum(1 for m in metrics if m.integrity_maintained) / len(metrics)
            error_score = 1.0 - statistics.mean([m.error_rate for m in metrics])
            
            # Weighted average
            overall_score = (false_pos_score * 0.4 + integrity_score * 0.4 + error_score * 0.2)
            return max(0.0, min(1.0, overall_score))
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.5
    
    def _get_quality_rating(self, quality_score: float) -> str:
        """Convert quality score to rating"""
        if quality_score >= 0.9:
            return "Excellent"
        elif quality_score >= 0.8:
            return "Good"
        elif quality_score >= 0.7:
            return "Acceptable"
        elif quality_score >= 0.6:
            return "Needs Improvement"
        else:
            return "Poor"


class ErrorLogger:
    """
    Error logging system with actionable recommendations
    
    Categorizes errors and provides specific remediation guidance
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize error logger
        
        Args:
            log_dir: Custom directory for error logs (default: ~/.claude/error_logs)
        """
        if log_dir:
            self.log_dir = log_dir
        else:
            self.log_dir = Path.home() / '.claude' / 'error_logs'
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Error categories and recommendations
        self.error_recommendations = {
            'validation_failure': {
                'actions': [
                    'Review validation criteria and thresholds',
                    'Check input data format and structure',
                    'Verify conversation chain integrity'
                ],
                'priority': 'high'
            },
            'backup_failure': {
                'actions': [
                    'Check available disk space',
                    'Verify backup directory permissions',
                    'Test backup storage location accessibility'
                ],
                'priority': 'critical'
            },
            'analysis_failure': {
                'actions': [
                    'Review analysis algorithm parameters',
                    'Check for data corruption in input',
                    'Verify memory and resource availability'
                ],
                'priority': 'high'
            },
            'performance_issue': {
                'actions': [
                    'Profile processing bottlenecks',
                    'Consider streaming for large files',
                    'Optimize validation procedures'
                ],
                'priority': 'medium'
            },
            'unexpected_error': {
                'actions': [
                    'Review error logs for patterns',
                    'Check system resources and dependencies',
                    'Implement additional error handling'
                ],
                'priority': 'critical'
            }
        }
        
        # Error history
        self.error_history = deque(maxlen=1000)
    
    def log_error(self, error_data: Dict[str, Any]):
        """
        Log error with context and generate recommendations
        
        Args:
            error_data: Dictionary containing error information
        """
        try:
            timestamp = datetime.now().isoformat()
            error_entry = {
                'timestamp': timestamp,
                'type': error_data.get('type', 'unknown'),
                'details': error_data.get('details', ''),
                'severity': error_data.get('severity', 'medium'),
                'context': error_data.get('context', {}),
                'recommendations': self._get_error_recommendations(error_data.get('type', 'unknown'))
            }
            
            # Store in history
            self.error_history.append(error_entry)
            
            # Write to log file
            log_file = self.log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.json"
            with open(log_file, 'a') as f:
                json.dump(error_entry, f)
                f.write('\n')
            
            logger.error(f"Logged error: {error_data.get('type', 'unknown')} - {error_data.get('details', '')}")
            
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
    
    def get_actionable_recommendations(self) -> List[Dict[str, Any]]:
        """Get actionable recommendations based on recent errors"""
        try:
            recent_errors = list(self.error_history)[-50:]  # Last 50 errors
            
            if not recent_errors:
                return []
            
            # Analyze error patterns
            error_counts = defaultdict(int)
            severity_counts = defaultdict(int)
            
            for error in recent_errors:
                error_counts[error['type']] += 1
                severity_counts[error['severity']] += 1
            
            recommendations = []
            
            # Generate recommendations based on frequent errors
            for error_type, count in error_counts.items():
                if count >= 3:  # Recurring error
                    recommendations.append({
                        'action': f'Address recurring {error_type} errors',
                        'priority': 'high',
                        'description': f'{error_type} has occurred {count} times recently',
                        'specific_actions': self.error_recommendations.get(error_type, {}).get('actions', [])
                    })
            
            # Add severity-based recommendations
            if severity_counts.get('critical', 0) > 0:
                recommendations.append({
                    'action': 'Immediate attention required for critical errors',
                    'priority': 'critical',
                    'description': f'{severity_counts["critical"]} critical errors detected',
                    'specific_actions': ['Stop operations until critical errors are resolved']
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _get_error_recommendations(self, error_type: str) -> List[str]:
        """Get specific recommendations for error type"""
        return self.error_recommendations.get(error_type, {}).get('actions', ['Review error details and context'])


class AlertingSystem:
    """
    Alerting system for validation failures and performance issues
    
    Provides configurable thresholds and notification mechanisms
    """
    
    def __init__(self):
        """Initialize alerting system"""
        self.alert_thresholds = {
            'false_positive_rate': 0.01,
            'processing_time': 5.0,
            'integrity_failures': 0,
            'backup_failures': 0,
            'quality_score': 0.7
        }
        
        self.alert_callbacks = []
        self.alert_history = deque(maxlen=100)
    
    def configure_thresholds(self, thresholds: Dict[str, float]):
        """Configure alert thresholds"""
        self.alert_thresholds.update(thresholds)
        logger.info(f"Updated alert thresholds: {thresholds}")
    
    def add_alert_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback function for alerts"""
        self.alert_callbacks.append(callback)
    
    def check_alert_conditions(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if any alert conditions are met"""
        alerts = []
        
        for metric_name, threshold in self.alert_thresholds.items():
            if metric_name in metrics:
                value = metrics[metric_name]
                
                # Check threshold based on metric type
                if metric_name in ['false_positive_rate', 'processing_time'] and value > threshold:
                    alerts.append({
                        'type': 'threshold_exceeded',
                        'metric': metric_name,
                        'value': value,
                        'threshold': threshold,
                        'severity': 'high' if value > threshold * 1.5 else 'medium',
                        'timestamp': datetime.now().isoformat()
                    })
                elif metric_name in ['integrity_failures', 'backup_failures'] and value > threshold:
                    alerts.append({
                        'type': 'failure_detected',
                        'metric': metric_name,
                        'value': value,
                        'threshold': threshold,
                        'severity': 'critical',
                        'timestamp': datetime.now().isoformat()
                    })
                elif metric_name == 'quality_score' and value < threshold:
                    alerts.append({
                        'type': 'quality_degradation',
                        'metric': metric_name,
                        'value': value,
                        'threshold': threshold,
                        'severity': 'medium',
                        'timestamp': datetime.now().isoformat()
                    })
        
        # Store alerts and trigger callbacks
        for alert in alerts:
            self.alert_history.append(alert)
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Alert callback failed: {e}")
        
        return alerts