"""
Batch processing system for claude-prune CLI
Phase 4.2 - Efficient batch operations with parallel processing and resume capability
"""

import json
import time
import logging
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from threading import Lock

from .utils import format_size, format_duration, is_jsonl_file
from ..pruner.core import JSONLPruner
from ..pruner.safety import SafePruner
from ..utils.backup import BackupManager

logger = logging.getLogger(__name__)


@dataclass
class BatchState:
    """State management for batch processing with resume capability"""
    
    directory: Path
    pattern: str
    recursive: bool
    level: str
    files_to_process: List[Path]
    processed_files: List[Path]
    failed_files: List[Dict[str, Any]]
    start_time: float
    parallel_workers: int = 4
    enable_backup: bool = True
    total_files_discovered: int = 0
    
    def save(self, state_file: Path):
        """Save batch state to file for resume capability"""
        state_data = {
            'directory': str(self.directory),
            'pattern': self.pattern,
            'recursive': self.recursive,
            'level': self.level,
            'files_to_process': [str(f) for f in self.files_to_process],
            'processed_files': [str(f) for f in self.processed_files],
            'failed_files': self.failed_files,
            'start_time': self.start_time,
            'parallel_workers': self.parallel_workers,
            'enable_backup': self.enable_backup,
            'total_files_discovered': self.total_files_discovered,
            'saved_at': time.time()
        }
        
        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2)
            logger.info(f"Batch state saved to {state_file}")
        except Exception as e:
            logger.error(f"Failed to save batch state: {e}")
            raise
    
    @classmethod
    def load(cls, state_file: Path) -> 'BatchState':
        """Load batch state from file"""
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            return cls(
                directory=Path(state_data['directory']),
                pattern=state_data['pattern'],
                recursive=state_data['recursive'],
                level=state_data['level'],
                files_to_process=[Path(f) for f in state_data['files_to_process']],
                processed_files=[Path(f) for f in state_data['processed_files']],
                failed_files=state_data['failed_files'],
                start_time=state_data['start_time'],
                parallel_workers=state_data.get('parallel_workers', 4),
                enable_backup=state_data.get('enable_backup', True),
                total_files_discovered=state_data.get('total_files_discovered', 0)
            )
        except Exception as e:
            logger.error(f"Failed to load batch state: {e}")
            raise
    
    def validate(self) -> List[str]:
        """Validate batch state configuration"""
        errors = []
        
        if not self.directory.exists():
            errors.append(f"Directory does not exist: {self.directory}")
        
        if self.level not in ['light', 'medium', 'aggressive']:
            errors.append(f"Invalid pruning level: {self.level}")
        
        if self.parallel_workers < 1 or self.parallel_workers > 16:
            errors.append(f"Invalid parallel workers: {self.parallel_workers}")
        
        if not self.pattern:
            errors.append("Pattern cannot be empty")
        
        return errors


class BatchProcessor:
    """
    Batch processor for processing multiple JSONL files efficiently
    
    Features:
    - Parallel processing with configurable worker count
    - Progress tracking and reporting
    - Resume capability for interrupted operations
    - Memory management and resource monitoring
    - Comprehensive error handling and recovery
    """
    
    def __init__(
        self,
        directory: Path,
        pattern: str = "*.jsonl",
        recursive: bool = False,
        level: str = "medium",
        parallel_workers: int = 4,
        enable_backup: bool = True,
        dry_run: bool = False,
        verbose: bool = False,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        memory_limit_mb: int = 512,
        min_age_days: Optional[int] = None,
        max_file_size_mb: Optional[int] = None
    ):
        """
        Initialize batch processor
        
        Args:
            directory: Directory to process
            pattern: File pattern to match (e.g., "*.jsonl")
            recursive: Whether to process subdirectories
            level: Pruning level ('light', 'medium', 'aggressive')
            parallel_workers: Number of parallel worker threads
            enable_backup: Whether to create backups before processing
            dry_run: Whether to perform dry run (no file modifications)
            verbose: Whether to enable verbose logging
            progress_callback: Optional callback for progress updates
            memory_limit_mb: Memory limit in megabytes
            min_age_days: Minimum file age in days for processing
            max_file_size_mb: Maximum file size in megabytes for processing
        """
        self.directory = directory
        self.pattern = pattern
        self.recursive = recursive
        self.level = level
        self.parallel_workers = min(parallel_workers, 16)  # Cap at 16 workers
        self.enable_backup = enable_backup
        self.dry_run = dry_run
        self.verbose = verbose
        self.progress_callback = progress_callback
        self.memory_limit_mb = memory_limit_mb
        self.min_age_days = min_age_days
        self.max_file_size_mb = max_file_size_mb
        
        # State management
        self.state_file = directory / ".claude_prune_state"
        self.lock = Lock()
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'files_successful': 0,
            'files_failed': 0,
            'total_messages_processed': 0,
            'total_messages_removed': 0,
            'total_size_reduction': 0,
            'processing_errors': [],
            'start_time': 0,
            'end_time': 0
        }
        
        # Initialize components
        self.backup_manager = BackupManager() if enable_backup else None
        
        if verbose:
            logger.setLevel(logging.DEBUG)
    
    def discover_files(self) -> List[Path]:
        """
        Discover JSONL files in the directory based on configuration
        
        Returns:
            List of JSONL file paths to process
        """
        logger.info(f"Discovering files in {self.directory} with pattern '{self.pattern}'")
        
        if self.recursive:
            discovered_files = list(self.directory.rglob(self.pattern))
        else:
            discovered_files = list(self.directory.glob(self.pattern))
        
        # Filter files based on criteria
        filtered_files = []
        for file_path in discovered_files:
            if not file_path.is_file():
                continue
            
            # Check if it's actually a JSONL file
            if not is_jsonl_file(file_path):
                logger.debug(f"Skipping non-JSONL file: {file_path}")
                continue
            
            # Apply age filter
            if self.min_age_days is not None:
                file_age_days = (time.time() - file_path.stat().st_mtime) / (24 * 3600)
                if file_age_days < self.min_age_days:
                    logger.debug(f"Skipping file too new: {file_path} (age: {file_age_days:.1f} days)")
                    continue
            
            # Apply size filter
            if self.max_file_size_mb is not None:
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                if file_size_mb > self.max_file_size_mb:
                    logger.debug(f"Skipping file too large: {file_path} (size: {file_size_mb:.1f} MB)")
                    continue
            
            filtered_files.append(file_path)
        
        logger.info(f"Discovered {len(filtered_files)} files to process")
        return sorted(filtered_files)
    
    def process_directory(self) -> Dict[str, Any]:
        """
        Process all discovered files in the directory
        
        Returns:
            Dictionary with processing results and statistics
        """
        start_time = time.time()
        self.stats['start_time'] = start_time
        
        try:
            # Discover files to process
            files_to_process = self.discover_files()
            
            if not files_to_process:
                logger.warning("No JSONL files found to process")
                return self._create_result_summary([], start_time)
            
            # Create batch state
            batch_state = BatchState(
                directory=self.directory,
                pattern=self.pattern,
                recursive=self.recursive,
                level=self.level,
                files_to_process=files_to_process.copy(),
                processed_files=[],
                failed_files=[],
                start_time=start_time,
                parallel_workers=self.parallel_workers,
                enable_backup=self.enable_backup,
                total_files_discovered=len(files_to_process)
            )
            
            # Save initial state for resume capability
            if not self.dry_run:
                batch_state.save(self.state_file)
            
            # Process files
            detailed_results = self._process_files_parallel(files_to_process, batch_state)
            
            # Clean up state file on successful completion
            if not self.dry_run and self.state_file.exists():
                self.state_file.unlink()
            
            return self._create_result_summary(detailed_results, start_time)
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            self.stats['processing_errors'].append(str(e))
            raise
    
    def resume_processing(self) -> Dict[str, Any]:
        """
        Resume interrupted batch processing from saved state
        
        Returns:
            Dictionary with processing results and statistics
        """
        if not self.state_file.exists():
            raise FileNotFoundError("No batch state file found for resume")
        
        logger.info("Resuming batch processing from saved state")
        
        try:
            # Load saved state
            batch_state = BatchState.load(self.state_file)
            
            # Validate state
            validation_errors = batch_state.validate()
            if validation_errors:
                raise ValueError(f"Invalid batch state: {'; '.join(validation_errors)}")
            
            # Update configuration from loaded state
            self.level = batch_state.level
            self.parallel_workers = batch_state.parallel_workers
            self.enable_backup = batch_state.enable_backup
            
            # Process remaining files
            files_to_process = batch_state.files_to_process
            
            if not files_to_process:
                logger.info("No remaining files to process")
                return self._create_resume_result_summary(batch_state, [])
            
            logger.info(f"Resuming processing of {len(files_to_process)} remaining files")
            
            # Process files
            detailed_results = self._process_files_parallel(files_to_process, batch_state)
            
            # Clean up state file on successful completion
            if self.state_file.exists():
                self.state_file.unlink()
            
            return self._create_resume_result_summary(batch_state, detailed_results)
            
        except Exception as e:
            logger.error(f"Resume processing failed: {e}")
            raise
    
    def _process_files_parallel(self, files: List[Path], batch_state: BatchState) -> List[Dict[str, Any]]:
        """
        Process files using parallel execution
        
        Args:
            files: List of file paths to process
            batch_state: Batch processing state
            
        Returns:
            List of detailed processing results
        """
        detailed_results = []
        
        # Limit workers based on system resources and file count
        effective_workers = min(
            self.parallel_workers,
            len(files),
            psutil.cpu_count() or 4
        )
        
        logger.info(f"Processing {len(files)} files with {effective_workers} parallel workers")
        
        if self.progress_callback:
            self.progress_callback(0, len(files), "Starting batch processing")
        
        with ThreadPoolExecutor(max_workers=effective_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self._process_single_file, file_path): file_path
                for file_path in files
            }
            
            completed_count = 0
            
            # Process completed tasks
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                completed_count += 1
                
                try:
                    result = future.result()
                    detailed_results.append(result)
                    
                    # Update batch state
                    with self.lock:
                        if result.get('success', False):
                            batch_state.processed_files.append(file_path)
                            self.stats['files_successful'] += 1
                        else:
                            batch_state.failed_files.append({
                                'file': str(file_path),
                                'error': result.get('error', 'Unknown error'),
                                'timestamp': time.time()
                            })
                            self.stats['files_failed'] += 1
                        
                        # Remove from files_to_process
                        if file_path in batch_state.files_to_process:
                            batch_state.files_to_process.remove(file_path)
                        
                        # Update statistics
                        if 'messages_processed' in result:
                            self.stats['total_messages_processed'] += result['messages_processed']
                        if 'messages_removed' in result:
                            self.stats['total_messages_removed'] += result['messages_removed']
                        if 'size_reduction_bytes' in result:
                            self.stats['total_size_reduction'] += result['size_reduction_bytes']
                        
                        self.stats['files_processed'] += 1
                    
                    # Progress callback
                    if self.progress_callback:
                        self.progress_callback(completed_count, len(files), str(file_path))
                    
                    # Save intermediate state (every 5 files or if memory usage is high)
                    if not self.dry_run and (completed_count % 5 == 0 or self._check_memory_usage()):
                        try:
                            batch_state.save(self.state_file)
                        except Exception as e:
                            logger.warning(f"Failed to save intermediate state: {e}")
                    
                    # Memory management
                    if self._check_memory_usage():
                        logger.warning("High memory usage detected, pausing briefly")
                        time.sleep(1)
                
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    
                    error_result = {
                        'file': str(file_path),
                        'success': False,
                        'error': str(e),
                        'processing_time': 0
                    }
                    detailed_results.append(error_result)
                    
                    with self.lock:
                        batch_state.failed_files.append({
                            'file': str(file_path),
                            'error': str(e),
                            'timestamp': time.time()
                        })
                        self.stats['files_failed'] += 1
                        self.stats['files_processed'] += 1
                        self.stats['processing_errors'].append(f"{file_path}: {e}")
        
        return detailed_results
    
    def _process_single_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Process a single JSONL file
        
        Args:
            file_path: Path to the JSONL file
            
        Returns:
            Dictionary with processing results
        """
        start_time = time.time()
        
        try:
            if self.verbose:
                logger.info(f"Processing file: {file_path}")
            
            # Get original file size
            original_size = file_path.stat().st_size
            
            if self.dry_run:
                # Simulate processing for dry run
                result = self._simulate_processing(file_path)
                result.update({
                    'file': str(file_path),
                    'success': True,
                    'processing_time': time.time() - start_time,
                    'original_size_bytes': original_size,
                    'dry_run': True
                })
                return result
            
            # Create backup if enabled
            backup_path = None
            if self.backup_manager:
                try:
                    backup_result = self.backup_manager.create_timestamped_backup(file_path)
                    if backup_result.get('success', False):
                        backup_path = backup_result.get('backup_path')
                        if self.verbose:
                            logger.debug(f"Backup created: {backup_path}")
                    else:
                        logger.warning(f"Backup creation failed: {backup_result.get('error', 'Unknown error')}")
                except Exception as e:
                    logger.warning(f"Failed to create backup for {file_path}: {e}")
            
            # Initialize pruner
            if self.enable_backup:
                pruner = SafePruner(
                    pruning_level=self.level,
                    enable_compression=True,
                    backup_retention_days=7,
                    handle_signals=False  # Disable signal handling in threads
                )
            else:
                from ..pruner.core import JSONLPruner
                pruner = JSONLPruner(pruning_level=self.level)
            
            # Process file
            if hasattr(pruner, 'prune_with_complete_safety'):
                processing_result = pruner.prune_with_complete_safety(file_path, file_path)
            elif hasattr(pruner, 'process_file'):
                processing_result = pruner.process_file(file_path, file_path)
            else:
                # Fallback - use JSONLPruner directly
                from ..pruner.core import JSONLPruner
                fallback_pruner = JSONLPruner(pruning_level=self.level)
                processing_result = fallback_pruner.process_file(file_path, file_path)
            
            # Calculate size reduction
            final_size = file_path.stat().st_size
            size_reduction = original_size - final_size
            
            result = {
                'file': str(file_path),
                'success': True,
                'processing_time': time.time() - start_time,
                'original_size_bytes': original_size,
                'final_size_bytes': final_size,
                'size_reduction_bytes': size_reduction,
                'size_reduction_percent': (size_reduction / original_size * 100) if original_size > 0 else 0,
                'backup_created': backup_path is not None,
                'backup_path': str(backup_path) if backup_path else None
            }
            
            # Add pruning statistics
            if processing_result:
                result.update({
                    'messages_processed': processing_result.get('messages_processed', 0),
                    'messages_preserved': processing_result.get('messages_preserved', 0),
                    'messages_removed': processing_result.get('messages_removed', 0),
                    'compression_ratio': processing_result.get('compression_ratio', 0)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            
            # Restore backup if processing failed and backup exists
            if backup_path and self.backup_manager:
                backup_path_obj = Path(backup_path) if isinstance(backup_path, str) else backup_path
                if backup_path_obj.exists():
                    try:
                        self.backup_manager.restore_from_backup(backup_path_obj, file_path)
                        logger.info(f"Restored original file from backup: {file_path}")
                    except Exception as restore_e:
                        logger.error(f"Failed to restore backup for {file_path}: {restore_e}")
            
            return {
                'file': str(file_path),
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time,
                'original_size_bytes': file_path.stat().st_size if file_path.exists() else 0
            }
    
    def _simulate_processing(self, file_path: Path) -> Dict[str, Any]:
        """
        Simulate processing for dry-run mode
        
        Args:
            file_path: Path to the JSONL file
            
        Returns:
            Dictionary with simulated processing results
        """
        try:
            from ..jsonl_analysis.analyzer import JSONLAnalyzer
            from ..jsonl_analysis.scoring import ImportanceScorer
            
            analyzer = JSONLAnalyzer()
            scorer = ImportanceScorer()
            
            # Load and analyze messages
            messages = analyzer.parse_jsonl_file(file_path)
            
            # Calculate what would be preserved
            threshold = {'light': 20, 'medium': 40, 'aggressive': 60}[self.level]
            preserved_count = 0
            
            for message in messages:
                score = scorer.calculate_message_importance(message)
                if score >= threshold:
                    preserved_count += 1
            
            removed_count = len(messages) - preserved_count
            compression_ratio = removed_count / len(messages) if messages else 0
            
            # Estimate size reduction (rough approximation)
            original_size = file_path.stat().st_size
            estimated_final_size = int(original_size * (1 - compression_ratio * 0.8))
            estimated_reduction = original_size - estimated_final_size
            
            return {
                'messages_processed': len(messages),
                'messages_preserved': preserved_count,
                'messages_removed': removed_count,
                'compression_ratio': compression_ratio,
                'estimated_final_size_bytes': estimated_final_size,
                'estimated_size_reduction_bytes': estimated_reduction,
                'estimated_size_reduction_percent': (estimated_reduction / original_size * 100) if original_size > 0 else 0
            }
            
        except Exception as e:
            logger.warning(f"Dry run simulation failed for {file_path}: {e}")
            return {
                'messages_processed': 0,
                'messages_preserved': 0,
                'messages_removed': 0,
                'compression_ratio': 0,
                'estimated_final_size_bytes': file_path.stat().st_size,
                'estimated_size_reduction_bytes': 0,
                'estimated_size_reduction_percent': 0,
                'simulation_error': str(e)
            }
    
    def _check_memory_usage(self) -> bool:
        """
        Check if memory usage exceeds configured limit
        
        Returns:
            True if memory usage is high, False otherwise
        """
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            return memory_mb > self.memory_limit_mb
        except Exception:
            return False
    
    def _create_result_summary(self, detailed_results: List[Dict[str, Any]], start_time: float) -> Dict[str, Any]:
        """Create summary of batch processing results"""
        end_time = time.time()
        self.stats['end_time'] = end_time
        
        total_original_size = sum(r.get('original_size_bytes', 0) for r in detailed_results)
        total_final_size = sum(r.get('final_size_bytes', 0) for r in detailed_results if r.get('success', False))
        
        if self.dry_run:
            total_final_size = sum(r.get('estimated_final_size_bytes', 0) for r in detailed_results)
        
        return {
            'files_processed': len(detailed_results),
            'files_successful': self.stats['files_successful'],
            'files_failed': self.stats['files_failed'],
            'total_time': end_time - start_time,
            'total_messages_processed': self.stats['total_messages_processed'],
            'total_messages_removed': self.stats['total_messages_removed'],
            'total_original_size_bytes': total_original_size,
            'total_final_size_bytes': total_final_size,
            'total_size_reduction_bytes': total_original_size - total_final_size,
            'total_size_reduction_percent': ((total_original_size - total_final_size) / total_original_size * 100) if total_original_size > 0 else 0,
            'average_processing_time': (end_time - start_time) / len(detailed_results) if detailed_results else 0,
            'parallel_workers_used': self.parallel_workers,
            'processing_errors': self.stats['processing_errors'],
            'detailed_results': detailed_results,
            'dry_run': self.dry_run,
            'configuration': {
                'directory': str(self.directory),
                'pattern': self.pattern,
                'recursive': self.recursive,
                'level': self.level,
                'enable_backup': self.enable_backup
            }
        }
    
    def _create_resume_result_summary(self, batch_state: BatchState, detailed_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create summary for resumed batch processing"""
        result = self._create_result_summary(detailed_results, batch_state.start_time)
        
        # Add resume-specific information
        result.update({
            'resumed_operation': True,
            'files_previously_processed': len(batch_state.processed_files),
            'files_previously_failed': len(batch_state.failed_files),
            'total_files': batch_state.total_files_discovered,
            'original_start_time': batch_state.start_time,
            'resume_time': time.time()
        })
        
        return result
    
    def save_state(self, state: BatchState, state_file: Path):
        """Save batch state to file"""
        state.save(state_file)
    
    def load_state(self, state_file: Path) -> BatchState:
        """Load batch state from file"""
        return BatchState.load(state_file)