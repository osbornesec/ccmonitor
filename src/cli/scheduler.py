"""
Automated scheduling system for claude-prune CLI
Phase 4.4 - Intelligent scheduling with age-based policies
"""

import json
import logging
import time
import schedule
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from .config import ConfigManager
from .batch import BatchProcessor
from .utils import format_duration, ensure_directory

logger = logging.getLogger(__name__)


@dataclass
class ScheduleConfig:
    """Configuration for automated scheduling"""
    
    enabled: bool = False
    policy: str = 'weekly'  # daily, weekly, monthly
    level: str = 'light'
    directories: List[str] = None
    time_of_day: str = '02:00'  # 2 AM default
    exclude_patterns: List[str] = None
    min_age_days: int = 7  # Only process files older than 7 days
    max_file_size_mb: int = 100
    enable_backup: bool = True
    parallel_workers: int = 2
    
    # Execution tracking
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    last_run_stats: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.directories is None:
            self.directories = []
        if self.exclude_patterns is None:
            self.exclude_patterns = ['*.backup.*', '*.temp.*', '*tmp*']


class ScheduleManager:
    """
    Manager for automated pruning schedules
    
    Features:
    - Configurable scheduling policies (daily/weekly/monthly)
    - Age-based pruning to avoid processing new files
    - Directory-specific configurations
    - Execution tracking and reporting
    - Safe execution with comprehensive error handling
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.config_manager = ConfigManager()
        self.schedule_config_file = Path.home() / '.config' / 'claude-prune' / 'schedule.json'
        self.schedule_config = self._load_schedule_config()
        
        if verbose:
            logger.setLevel(logging.DEBUG)
    
    def setup_schedule(self, policy: str = 'weekly', level: str = 'light', 
                      directories: Optional[List[str]] = None, time_of_day: str = '02:00',
                      min_age_days: int = 7) -> Dict[str, Any]:
        """
        Setup automated pruning schedule
        
        Args:
            policy: Scheduling policy ('daily', 'weekly', 'monthly')
            level: Default pruning level
            directories: List of directories to monitor
            time_of_day: Time to run (HH:MM format)
            min_age_days: Minimum file age before processing
            
        Returns:
            Dictionary with setup results
        """
        try:
            # Validate inputs
            if policy not in ['daily', 'weekly', 'monthly']:
                raise ValueError(f"Invalid policy: {policy}")
            
            if level not in ['light', 'medium', 'aggressive']:
                raise ValueError(f"Invalid level: {level}")
            
            # Update schedule configuration
            self.schedule_config.enabled = True
            self.schedule_config.policy = policy
            self.schedule_config.level = level
            self.schedule_config.time_of_day = time_of_day
            self.schedule_config.min_age_days = min_age_days
            
            if directories:
                # Validate directories
                valid_dirs = []
                for directory in directories:
                    dir_path = Path(directory)
                    if dir_path.exists() and dir_path.is_dir():
                        valid_dirs.append(str(dir_path.resolve()))
                    else:
                        logger.warning(f"Directory does not exist: {directory}")
                
                self.schedule_config.directories = valid_dirs
            
            # Calculate next run time
            next_run = self._calculate_next_run(policy, time_of_day)
            self.schedule_config.next_run = next_run.isoformat()
            
            # Save configuration
            self._save_schedule_config()
            
            # Setup system scheduler (if available)
            try:
                self._setup_system_scheduler()
            except Exception as e:
                logger.warning(f"Failed to setup system scheduler: {e}")
            
            logger.info(f"Schedule setup complete: {policy} at {time_of_day}")
            
            return {
                'success': True,
                'policy': policy,
                'level': level,
                'directories': self.schedule_config.directories,
                'next_run': self.schedule_config.next_run,
                'min_age_days': min_age_days
            }
            
        except Exception as e:
            logger.error(f"Failed to setup schedule: {e}")
            raise
    
    def disable_schedule(self) -> Dict[str, Any]:
        """
        Disable automated scheduling
        
        Returns:
            Dictionary with disable results
        """
        try:
            self.schedule_config.enabled = False
            self.schedule_config.next_run = None
            
            # Save configuration
            self._save_schedule_config()
            
            # Remove system scheduler entries
            try:
                self._remove_system_scheduler()
            except Exception as e:
                logger.warning(f"Failed to remove system scheduler entries: {e}")
            
            logger.info("Automated scheduling disabled")
            
            return {
                'success': True,
                'message': 'Automated scheduling disabled'
            }
            
        except Exception as e:
            logger.error(f"Failed to disable schedule: {e}")
            raise
    
    def run_scheduled_pruning(self) -> Dict[str, Any]:
        """
        Execute scheduled pruning operation
        
        Returns:
            Dictionary with execution results
        """
        start_time = time.time()
        
        try:
            if not self.schedule_config.enabled:
                return {
                    'success': False,
                    'message': 'Scheduling is not enabled'
                }
            
            logger.info("Starting scheduled pruning operation")
            
            # Track execution
            execution_start = datetime.now(timezone.utc)
            self.schedule_config.run_count += 1
            
            # Process all configured directories
            results = []
            total_files_processed = 0
            total_errors = 0
            
            for directory in self.schedule_config.directories:
                try:
                    dir_result = self._process_directory_scheduled(Path(directory))
                    results.append(dir_result)
                    
                    total_files_processed += dir_result.get('files_processed', 0)
                    total_errors += dir_result.get('files_failed', 0)
                    
                except Exception as e:
                    logger.error(f"Error processing directory {directory}: {e}")
                    error_result = {
                        'directory': directory,
                        'success': False,
                        'error': str(e),
                        'files_processed': 0,
                        'files_failed': 1
                    }
                    results.append(error_result)
                    total_errors += 1
            
            # Update execution tracking
            execution_time = time.time() - start_time
            self.schedule_config.last_run = execution_start.isoformat()
            
            # Calculate next run
            next_run = self._calculate_next_run(
                self.schedule_config.policy, 
                self.schedule_config.time_of_day
            )
            self.schedule_config.next_run = next_run.isoformat()
            
            # Save execution stats
            execution_stats = {
                'execution_time': execution_time,
                'directories_processed': len(self.schedule_config.directories),
                'total_files_processed': total_files_processed,
                'total_errors': total_errors,
                'success_rate': (total_files_processed - total_errors) / max(total_files_processed, 1),
                'timestamp': execution_start.isoformat()
            }
            
            self.schedule_config.last_run_stats = execution_stats
            
            # Save updated configuration
            self._save_schedule_config()
            
            logger.info(f"Scheduled pruning complete: {total_files_processed} files processed in {format_duration(execution_time)}")
            
            return {
                'success': True,
                'execution_stats': execution_stats,
                'directory_results': results,
                'next_run': self.schedule_config.next_run
            }
            
        except Exception as e:
            logger.error(f"Scheduled pruning failed: {e}")
            
            # Still update last run time to avoid repeated failures
            self.schedule_config.last_run = datetime.now(timezone.utc).isoformat()
            self._save_schedule_config()
            
            raise
    
    def get_current_config(self) -> Dict[str, Any]:
        """
        Get current scheduling configuration
        
        Returns:
            Dictionary with current configuration
        """
        config_dict = asdict(self.schedule_config)
        
        # Add computed fields
        if self.schedule_config.next_run:
            try:
                next_run_dt = datetime.fromisoformat(self.schedule_config.next_run)
                time_until_next = next_run_dt - datetime.now(timezone.utc)
                config_dict['time_until_next_run'] = time_until_next.total_seconds()
                config_dict['time_until_next_run_formatted'] = format_duration(time_until_next.total_seconds())
            except Exception:
                config_dict['time_until_next_run'] = None
        
        # Add status information
        config_dict['status'] = 'enabled' if self.schedule_config.enabled else 'disabled'
        config_dict['directories_exist'] = [
            Path(d).exists() for d in self.schedule_config.directories
        ]
        
        return config_dict
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get execution history
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of execution records
        """
        # For now, return the last run stats
        # In a full implementation, this would read from a persistent log
        
        if self.schedule_config.last_run_stats:
            return [self.schedule_config.last_run_stats]
        else:
            return []
    
    def check_schedule_health(self) -> Dict[str, Any]:
        """
        Check the health of the scheduling system
        
        Returns:
            Dictionary with health check results
        """
        health_issues = []
        
        # Check if enabled but no directories configured
        if self.schedule_config.enabled and not self.schedule_config.directories:
            health_issues.append("No directories configured for monitoring")
        
        # Check if directories exist
        for directory in self.schedule_config.directories:
            if not Path(directory).exists():
                health_issues.append(f"Directory does not exist: {directory}")
        
        # Check if next run is in the past
        if self.schedule_config.next_run:
            try:
                next_run_dt = datetime.fromisoformat(self.schedule_config.next_run)
                if next_run_dt < datetime.now(timezone.utc):
                    health_issues.append("Next run is scheduled in the past")
            except Exception:
                health_issues.append("Invalid next run timestamp")
        
        # Check system scheduler availability
        scheduler_available = self._check_system_scheduler_availability()
        
        return {
            'healthy': len(health_issues) == 0,
            'issues': health_issues,
            'scheduler_available': scheduler_available,
            'configuration_valid': len(health_issues) == 0,
            'last_check': datetime.now(timezone.utc).isoformat()
        }
    
    def _load_schedule_config(self) -> ScheduleConfig:
        """Load schedule configuration from file"""
        try:
            if self.schedule_config_file.exists():
                with open(self.schedule_config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Convert to ScheduleConfig object
                return ScheduleConfig(**config_data)
            else:
                # Return default configuration
                return ScheduleConfig()
                
        except Exception as e:
            logger.warning(f"Failed to load schedule config, using defaults: {e}")
            return ScheduleConfig()
    
    def _save_schedule_config(self):
        """Save schedule configuration to file"""
        try:
            # Ensure config directory exists
            ensure_directory(self.schedule_config_file.parent)
            
            # Save configuration
            config_data = asdict(self.schedule_config)
            
            with open(self.schedule_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
            
            if self.verbose:
                logger.debug(f"Schedule configuration saved to {self.schedule_config_file}")
                
        except Exception as e:
            logger.error(f"Failed to save schedule configuration: {e}")
            raise
    
    def _calculate_next_run(self, policy: str, time_of_day: str) -> datetime:
        """Calculate next run time based on policy"""
        try:
            # Parse time of day
            hour, minute = map(int, time_of_day.split(':'))
            
            # Get current time
            now = datetime.now(timezone.utc)
            
            # Calculate next run
            if policy == 'daily':
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
            
            elif policy == 'weekly':
                # Run on Sundays
                days_until_sunday = (6 - now.weekday()) % 7
                if days_until_sunday == 0:  # Today is Sunday
                    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if next_run <= now:
                        days_until_sunday = 7  # Next Sunday
                
                next_run = now + timedelta(days=days_until_sunday)
                next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            elif policy == 'monthly':
                # Run on the first day of next month
                if now.month == 12:
                    next_month = now.replace(year=now.year + 1, month=1, day=1)
                else:
                    next_month = now.replace(month=now.month + 1, day=1)
                
                next_run = next_month.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            else:
                raise ValueError(f"Invalid policy: {policy}")
            
            return next_run
            
        except Exception as e:
            logger.error(f"Failed to calculate next run time: {e}")
            # Fallback to tomorrow at the specified time
            tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
            return tomorrow.replace(hour=2, minute=0, second=0, microsecond=0)
    
    def _process_directory_scheduled(self, directory: Path) -> Dict[str, Any]:
        """Process a directory as part of scheduled operation"""
        try:
            logger.info(f"Processing directory for scheduled pruning: {directory}")
            
            # Initialize batch processor with schedule-specific settings
            batch_processor = BatchProcessor(
                directory=directory,
                pattern="*.jsonl",
                recursive=True,
                level=self.schedule_config.level,
                parallel_workers=self.schedule_config.parallel_workers,
                enable_backup=self.schedule_config.enable_backup,
                dry_run=False,  # Scheduled runs are real
                verbose=self.verbose,
                min_age_days=self.schedule_config.min_age_days,
                max_file_size_mb=self.schedule_config.max_file_size_mb
            )
            
            # Process directory
            result = batch_processor.process_directory()
            
            # Add directory-specific information
            result['directory'] = str(directory)
            result['scheduled_execution'] = True
            result['schedule_policy'] = self.schedule_config.policy
            result['schedule_level'] = self.schedule_config.level
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process directory {directory}: {e}")
            return {
                'directory': str(directory),
                'success': False,
                'error': str(e),
                'files_processed': 0,
                'files_failed': 1
            }
    
    def _setup_system_scheduler(self):
        """Setup system-level scheduler (cron/systemd)"""
        # This would implement system scheduler integration
        # For now, we'll just log that it's not implemented
        
        logger.info("System scheduler integration not implemented - using application-level scheduling")
        
        # In a full implementation, this would:
        # 1. Create a cron job (Linux/macOS)
        # 2. Create a scheduled task (Windows)
        # 3. Use systemd timers (modern Linux)
        
        # Example cron entry:
        # 0 2 * * 0 /usr/local/bin/claude-prune schedule --run
        
        pass
    
    def _remove_system_scheduler(self):
        """Remove system-level scheduler entries"""
        # This would remove system scheduler integration
        logger.info("Removing system scheduler entries (not implemented)")
        pass
    
    def _check_system_scheduler_availability(self) -> bool:
        """Check if system scheduler is available"""
        # Simple check for common schedulers
        import shutil
        
        # Check for cron
        if shutil.which('crontab'):
            return True
        
        # Check for systemctl (systemd)
        if shutil.which('systemctl'):
            return True
        
        # Check for schtasks (Windows)
        if shutil.which('schtasks'):
            return True
        
        return False


class ScheduledExecutor:
    """
    Executor for running scheduled operations
    
    This class can be used as a standalone scheduler or integrated
    with external scheduling systems.
    """
    
    def __init__(self):
        self.manager = ScheduleManager(verbose=True)
    
    def run_pending(self):
        """Run any pending scheduled operations"""
        try:
            config = self.manager.get_current_config()
            
            if not config['enabled']:
                return
            
            # Check if it's time to run
            if config.get('next_run'):
                next_run_dt = datetime.fromisoformat(config['next_run'])
                if datetime.now(timezone.utc) >= next_run_dt:
                    logger.info("Executing scheduled pruning operation")
                    result = self.manager.run_scheduled_pruning()
                    logger.info(f"Scheduled operation completed: {result['success']}")
                    return result
            
        except Exception as e:
            logger.error(f"Error in scheduled executor: {e}")
    
    def start_daemon(self, check_interval: int = 300):
        """
        Start daemon mode for continuous scheduling
        
        Args:
            check_interval: Check interval in seconds (default: 5 minutes)
        """
        logger.info(f"Starting schedule daemon (check interval: {check_interval}s)")
        
        try:
            while True:
                self.run_pending()
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            logger.info("Schedule daemon stopped by user")
        except Exception as e:
            logger.error(f"Schedule daemon error: {e}")
            raise


# CLI integration functions

def main_scheduled_run():
    """Main function for scheduled execution (can be called from cron/systemd)"""
    try:
        manager = ScheduleManager(verbose=True)
        result = manager.run_scheduled_pruning()
        
        if result['success']:
            print(f"Scheduled pruning completed successfully")
            print(f"Files processed: {result['execution_stats']['total_files_processed']}")
            print(f"Execution time: {format_duration(result['execution_stats']['execution_time'])}")
        else:
            print(f"Scheduled pruning failed: {result.get('message', 'Unknown error')}")
            exit(1)
            
    except Exception as e:
        print(f"Scheduled execution failed: {e}")
        exit(1)


if __name__ == '__main__':
    # Allow direct execution for testing
    main_scheduled_run()