# main_with_pruning.py

## Overview

The `main_with_pruning.py` script serves as the unified orchestration layer for the JSONL conversation pruning system. It integrates all pruning components—file cleanup, message-level analysis, temporal decay, and importance scoring—into a cohesive automated pipeline with monitoring and configuration management.

## Features

### Orchestration Capabilities
- **Multi-stage pruning pipeline**: Coordinates file cleanup, message analysis, and content pruning
- **Automated monitoring**: Tracks pruning effectiveness and system performance
- **Configuration management**: Centralized settings for all pruning components
- **Error recovery**: Robust handling of partial failures with rollback capabilities
- **Progress reporting**: Real-time status updates and completion statistics

### Integration Features
- **File-level cleanup integration**: Coordinates with cleanup_claude_projects.py
- **Message-level pruning**: Integrates cleanup_and_ultra_prune.py processing
- **Temporal analysis**: Incorporates temporal_analysis.py algorithms
- **Importance scoring**: Leverages importance_engine.py for content evaluation
- **Batch processing**: Handles multiple conversation files efficiently

## Architecture

### Main Pipeline Components

#### 1. Pipeline Orchestrator
```python
class PruningPipelineOrchestrator:
    """
    Main orchestration class that coordinates all pruning operations.
    """
    
    def __init__(self, config_path=None):
        self.config = self.load_configuration(config_path)
        self.file_cleaner = FileCleanupManager()
        self.message_pruner = MessagePruningEngine()
        self.monitor = PruningMonitor()
        
    def execute_full_pipeline(self, target_paths):
        """
        Execute complete pruning pipeline across all target paths.
        """
```

#### 2. Configuration Manager
```python
class PruningConfigurationManager:
    """
    Centralized configuration management for all pruning components.
    """
    
    def load_configuration(self, config_path):
        """
        Load and validate pruning configuration from file.
        """
        
    def get_component_config(self, component_name):
        """
        Get configuration for specific pruning component.
        """
```

#### 3. Progress Monitor
```python
class PruningProgressMonitor:
    """
    Real-time monitoring and reporting of pruning operations.
    """
    
    def track_pipeline_progress(self, stage, progress_data):
        """
        Track progress through different pipeline stages.
        """
        
    def generate_completion_report(self):
        """
        Generate comprehensive report of pruning results.
        """
```

## Pipeline Stages

### Stage 1: Pre-Processing
```python
def stage_1_preprocessing(self, target_paths):
    """
    Prepare environment and validate inputs.
    
    Operations:
    - Validate target paths and permissions
    - Check available disk space
    - Create backup directories
    - Initialize monitoring systems
    """
    preprocessing_results = {
        'validated_paths': [],
        'backup_locations': {},
        'space_available': 0,
        'estimated_processing_time': 0
    }
    return preprocessing_results
```

### Stage 2: File-Level Cleanup
```python
def stage_2_file_cleanup(self, validated_paths):
    """
    Execute file-level cleanup operations.
    
    Operations:
    - Remove backup files (.backup, .backup-messages)
    - Delete empty JSONL files (0 bytes)
    - Clean timestamped backup files
    - Generate file cleanup statistics
    """
    from cleanup_claude_projects import cleanup_claude_projects
    
    cleanup_results = {}
    for path in validated_paths:
        result = cleanup_claude_projects(
            target_path=path,
            dry_run=self.config['file_cleanup']['dry_run'],
            max_deletions=self.config['file_cleanup']['max_deletions']
        )
        cleanup_results[path] = result
    
    return cleanup_results
```

### Stage 3: Message-Level Analysis
```python
def stage_3_message_analysis(self, cleaned_paths):
    """
    Analyze message importance and apply temporal decay.
    
    Operations:
    - Load conversation files
    - Calculate importance scores for each message
    - Apply temporal decay algorithms
    - Identify cross-references and dependencies
    - Generate analysis statistics
    """
    from importance_engine import ImportanceScorer
    from temporal_analysis import TemporalDecayEngine
    
    analysis_results = {}
    for path in cleaned_paths:
        conversation_files = discover_conversation_files(path)
        
        for file_path in conversation_files:
            messages = load_messages(file_path)
            analysis_result = self.analyze_conversation_messages(messages)
            analysis_results[file_path] = analysis_result
    
    return analysis_results
```

### Stage 4: Content Pruning
```python
def stage_4_content_pruning(self, analysis_results):
    """
    Execute message pruning based on analysis results.
    
    Operations:
    - Apply importance thresholds
    - Execute temporal-based deletions
    - Preserve critical content and references
    - Create pruned conversation files
    - Generate pruning statistics
    """
    from cleanup_and_ultra_prune import ConversationPruner
    
    pruning_results = {}
    for file_path, analysis_data in analysis_results.items():
        pruner_config = self.config['message_pruning']
        
        pruning_result = self.prune_conversation_file(
            file_path=file_path,
            analysis_data=analysis_data,
            config=pruner_config
        )
        
        pruning_results[file_path] = pruning_result
    
    return pruning_results
```

### Stage 5: Post-Processing
```python
def stage_5_postprocessing(self, pruning_results):
    """
    Finalize pruning operations and generate reports.
    
    Operations:
    - Validate pruned file integrity
    - Generate comprehensive statistics
    - Clean up temporary files
    - Create success/failure reports
    - Update monitoring databases
    """
    postprocessing_results = {
        'files_processed': len(pruning_results),
        'total_size_reduction': 0,
        'messages_pruned': 0,
        'errors_encountered': [],
        'processing_time': 0
    }
    
    return postprocessing_results
```

## Configuration System

### Master Configuration File
```yaml
# pruning_config.yaml
pipeline:
  enable_monitoring: true
  backup_before_pruning: true
  parallel_processing: false
  max_concurrent_files: 4

file_cleanup:
  enabled: true
  dry_run: false
  max_deletions: 1000
  remove_empty_files: true
  remove_backup_files: true

message_analysis:
  importance_engine:
    factor_weights:
      content_complexity: 0.30
      technical_depth: 0.25
      error_criticality: 0.20
      cross_references: 0.15
      user_interaction: 0.10
  
  temporal_analysis:
    decay_mode: "exponential"
    decay_rate: 0.15
    enable_velocity_adjustment: true

message_pruning:
  importance_threshold: 0.4
  preserve_important_messages: false
  days_threshold: 7
  ultra_mode: false
  target_reduction: 0.8

monitoring:
  enable_progress_tracking: true
  generate_detailed_reports: true
  log_level: "INFO"
  save_statistics: true

error_handling:
  continue_on_error: true
  max_retries: 3
  rollback_on_failure: true
```

### Component-Specific Configurations
```python
def load_component_configurations(self):
    """
    Load configurations for individual components.
    """
    self.component_configs = {
        'file_cleanup': {
            'cleanup_claude_projects': self.config['file_cleanup']
        },
        'importance_scoring': {
            'importance_engine': self.config['message_analysis']['importance_engine']
        },
        'temporal_analysis': {
            'temporal_analysis': self.config['message_analysis']['temporal_analysis']
        },
        'message_pruning': {
            'cleanup_and_ultra_prune': self.config['message_pruning']
        }
    }
```

## Usage Examples

### Basic Pipeline Execution
```bash
# Run complete pruning pipeline
python main_with_pruning.py --target ~/.claude/projects

# Run with custom configuration
python main_with_pruning.py --config custom_pruning_config.yaml --target ~/.claude/projects

# Dry run mode (preview only)
python main_with_pruning.py --dry-run --target ~/.claude/projects
```

### Selective Stage Execution
```bash
# Run only file cleanup stage
python main_with_pruning.py --stage file_cleanup --target ~/.claude/projects

# Run message analysis and pruning only
python main_with_pruning.py --stages message_analysis,content_pruning --target ~/.claude/projects

# Skip file cleanup, run message-level operations
python main_with_pruning.py --skip-stages file_cleanup --target ~/.claude/projects
```

### Advanced Options
```bash
# Enable parallel processing
python main_with_pruning.py --parallel --max-workers 4 --target ~/.claude/projects

# Generate detailed reports
python main_with_pruning.py --detailed-reports --report-output ./pruning_reports/ --target ~/.claude/projects

# Custom thresholds
python main_with_pruning.py --importance-threshold 0.6 --days-threshold 14 --target ~/.claude/projects
```

## Command Line Interface

### Required Arguments
- `--target PATH`: Target directory or file path for pruning operations

### Optional Arguments
```bash
--config PATH              # Custom configuration file path
--dry-run                  # Preview operations without making changes
--stage STAGE              # Run specific pipeline stage only
--stages STAGE1,STAGE2     # Run multiple specific stages
--skip-stages STAGE1       # Skip specified stages
--parallel                 # Enable parallel processing
--max-workers N            # Maximum parallel workers (default: 4)
--importance-threshold N   # Override importance threshold (0.0-1.0)
--days-threshold N         # Override age threshold in days
--report-output PATH       # Directory for detailed reports
--detailed-reports         # Generate comprehensive analysis reports
--log-level LEVEL          # Logging level (DEBUG, INFO, WARNING, ERROR)
--backup-dir PATH          # Custom backup directory
--no-backup                # Disable automatic backups
--force                    # Skip confirmation prompts
```

## Pipeline Monitoring

### Real-Time Progress Tracking
```python
class PipelineProgressTracker:
    """
    Real-time tracking of pipeline execution progress.
    """
    
    def __init__(self):
        self.stage_progress = {}
        self.overall_progress = 0.0
        self.start_time = None
        self.estimated_completion = None
    
    def update_stage_progress(self, stage_name, progress_percent):
        """
        Update progress for specific pipeline stage.
        """
        self.stage_progress[stage_name] = progress_percent
        self.calculate_overall_progress()
        self.estimate_completion_time()
        
    def generate_progress_report(self):
        """
        Generate formatted progress report.
        """
        return {
            'overall_progress': self.overall_progress,
            'stage_progress': self.stage_progress,
            'elapsed_time': self.get_elapsed_time(),
            'estimated_remaining': self.get_estimated_remaining_time(),
            'current_stage': self.get_current_stage()
        }
```

### Performance Metrics
```python
def collect_performance_metrics(self):
    """
    Collect comprehensive performance metrics for pipeline execution.
    """
    metrics = {
        'execution_time': {
            'total_time': 0.0,
            'stage_times': {},
            'average_file_processing_time': 0.0
        },
        'throughput': {
            'files_per_second': 0.0,
            'messages_per_second': 0.0,
            'bytes_per_second': 0.0
        },
        'resource_usage': {
            'peak_memory_usage': 0.0,
            'average_cpu_usage': 0.0,
            'disk_io_operations': 0
        },
        'pruning_effectiveness': {
            'size_reduction_ratio': 0.0,
            'message_reduction_ratio': 0.0,
            'importance_distribution': {}
        }
    }
    return metrics
```

## Error Handling and Recovery

### Error Classification
```python
class PipelineErrorHandler:
    """
    Comprehensive error handling and recovery system.
    """
    
    ERROR_TYPES = {
        'PERMISSION_ERROR': 'File permission issues',
        'DISK_SPACE_ERROR': 'Insufficient disk space',
        'CORRUPTION_ERROR': 'File corruption detected',
        'CONFIGURATION_ERROR': 'Invalid configuration',
        'PROCESSING_ERROR': 'Content processing failure'
    }
    
    def handle_pipeline_error(self, error, stage, context):
        """
        Handle errors with appropriate recovery strategies.
        """
        error_type = self.classify_error(error)
        recovery_strategy = self.get_recovery_strategy(error_type, stage)
        
        return self.execute_recovery_strategy(recovery_strategy, context)
```

### Rollback Capabilities
```python
def execute_rollback(self, checkpoint_data):
    """
    Rollback pipeline operations to previous checkpoint.
    
    Rollback operations:
    - Restore files from backups
    - Revert configuration changes
    - Clean up partial processing results
    - Reset monitoring state
    """
    rollback_results = {
        'files_restored': 0,
        'rollback_successful': True,
        'errors_during_rollback': [],
        'final_state': 'restored'
    }
    
    try:
        # Restore files from backup
        for backup_info in checkpoint_data['backups']:
            self.restore_file_from_backup(backup_info)
            rollback_results['files_restored'] += 1
        
        # Clean up temporary files
        self.cleanup_temporary_files(checkpoint_data['temp_files'])
        
        # Reset monitoring state
        self.monitor.reset_to_checkpoint(checkpoint_data['monitor_state'])
        
    except Exception as e:
        rollback_results['rollback_successful'] = False
        rollback_results['errors_during_rollback'].append(str(e))
    
    return rollback_results
```

## Batch Processing

### Multi-Directory Processing
```python
def process_multiple_directories(self, directory_list):
    """
    Process multiple directories in batch with optimized resource usage.
    """
    batch_results = {}
    
    for directory_path in directory_list:
        try:
            self.monitor.start_directory_processing(directory_path)
            
            # Execute pipeline for directory
            directory_result = self.execute_full_pipeline([directory_path])
            batch_results[directory_path] = directory_result
            
            self.monitor.complete_directory_processing(directory_path)
            
        except Exception as e:
            batch_results[directory_path] = {
                'success': False,
                'error': str(e),
                'stage_failed': self.monitor.get_current_stage()
            }
    
    return batch_results
```

### Parallel Processing
```python
def execute_parallel_processing(self, file_list, max_workers=4):
    """
    Execute pruning operations in parallel for improved performance.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    parallel_results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks for parallel execution
        future_to_file = {
            executor.submit(self.process_single_file, file_path): file_path
            for file_path in file_list
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()
                parallel_results[file_path] = result
            except Exception as e:
                parallel_results[file_path] = {
                    'success': False,
                    'error': str(e)
                }
    
    return parallel_results
```

## Reporting and Analytics

### Comprehensive Reporting
```python
def generate_comprehensive_report(self, pipeline_results):
    """
    Generate detailed report of all pruning operations.
    """
    report = {
        'executive_summary': self.generate_executive_summary(pipeline_results),
        'detailed_statistics': self.generate_detailed_statistics(pipeline_results),
        'performance_metrics': self.collect_performance_metrics(),
        'error_analysis': self.analyze_errors(pipeline_results),
        'recommendations': self.generate_recommendations(pipeline_results)
    }
    
    return report

def generate_executive_summary(self, results):
    """
    Executive summary of pruning operations.
    """
    summary = {
        'total_files_processed': 0,
        'total_size_reduction': 0,
        'total_messages_pruned': 0,
        'processing_time': 0,
        'success_rate': 0.0,
        'key_achievements': [],
        'areas_for_improvement': []
    }
    
    return summary
```

### Performance Analytics
```python
def analyze_pruning_effectiveness(self, results):
    """
    Analyze effectiveness of pruning operations.
    """
    effectiveness_metrics = {
        'size_reduction_by_stage': {},
        'importance_score_distribution': {},
        'temporal_decay_impact': {},
        'cross_reference_preservation': {},
        'content_type_analysis': {}
    }
    
    return effectiveness_metrics
```

## Integration Points

### External System Integration
```python
class ExternalSystemIntegrator:
    """
    Integration with external monitoring and management systems.
    """
    
    def integrate_with_claude_hooks(self):
        """
        Integration with Claude Code hook system.
        """
        pass
    
    def send_metrics_to_monitoring(self, metrics):
        """
        Send performance metrics to external monitoring systems.
        """
        pass
    
    def trigger_backup_systems(self, backup_request):
        """
        Trigger external backup systems before pruning.
        """
        pass
```

### API Interface
```python
class PruningAPIInterface:
    """
    RESTful API interface for remote pruning operations.
    """
    
    def start_pruning_job(self, request_data):
        """
        Start asynchronous pruning job via API.
        """
        pass
    
    def get_job_status(self, job_id):
        """
        Get status of running pruning job.
        """
        pass
    
    def get_job_results(self, job_id):
        """
        Get results of completed pruning job.
        """
        pass
```

## Future Enhancements

### Planned Features
- **Machine learning optimization**: ML-based parameter tuning
- **Real-time processing**: Continuous pruning as conversations grow
- **Cloud integration**: Support for cloud-based conversation storage
- **Advanced analytics**: Predictive analysis of pruning effectiveness

### Performance Improvements
- **GPU acceleration**: Leverage GPU for large-scale text analysis
- **Streaming processing**: Handle massive conversation files efficiently
- **Distributed processing**: Multi-machine processing capabilities
- **Incremental pruning**: Only process changed content

## Troubleshooting

### Common Issues
1. **Memory issues with large files**: Use streaming processing mode
2. **Permission errors**: Check file system permissions
3. **Configuration conflicts**: Validate configuration file syntax
4. **Incomplete processing**: Check disk space and system resources

### Diagnostic Tools
```bash
# Diagnostic mode
python main_with_pruning.py --diagnostic --target ~/.claude/projects

# Validate configuration
python main_with_pruning.py --validate-config pruning_config.yaml

# Test pipeline components
python main_with_pruning.py --test-components --target test_data/
```

## Related Documentation
- [cleanup_and_ultra_prune.md](cleanup_and_ultra_prune.md) - Message-level pruning
- [cleanup_claude_projects.md](cleanup_claude_projects.md) - File-level cleanup
- [temporal_analysis.md](temporal_analysis.md) - Temporal analysis algorithms
- [importance_engine.md](importance_engine.md) - Importance scoring system
- [PROJECT_README.md](PROJECT_README.md) - Project overview
- [CLI_Usage.md](CLI_Usage.md) - Command-line reference