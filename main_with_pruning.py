import os
import time
import json
import pickle
import argparse
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, Optional
import logging

# Import the JSONL pruning system
from src.cli.main import cli as pruning_cli
from src.pruner.core import JSONLPruner
from src.pruner.safety import SafePruner

class ClaudeCodeMonitorWithPruning:
    def __init__(self, projects_dir: str = None, output_file: str = "claude_session_changes.txt", 
                 enable_pruning: bool = True, pruning_level: str = "medium", 
                 auto_backup: bool = True, pruning_threshold_kb: int = 100):
        self.projects_dir = Path(projects_dir or os.path.expanduser("~/.claude/projects"))
        self.output_file = Path(output_file)
        self.file_timestamps: Dict[str, float] = {}
        self.file_sizes: Dict[str, int] = {}
        self.state_file = Path(".ccmonitor_state.pkl")
        
        # Pruning configuration
        self.enable_pruning = enable_pruning
        self.pruning_level = pruning_level  # light, medium, aggressive
        self.auto_backup = auto_backup
        self.pruning_threshold_kb = pruning_threshold_kb  # Only prune files larger than this
        self.pruned_files_log = Path("pruned_files.log")
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Ensure output file exists
        self.output_file.touch(exist_ok=True)
        self.pruned_files_log.touch(exist_ok=True)
        
        # Initialize pruning system
        if self.enable_pruning:
            try:
                # Use the reliable core pruner for now
                self.pruner = JSONLPruner(pruning_level=self.pruning_level)
                backup_status = "with manual backup" if self.auto_backup else "no backup"
                self.logger.info(f"✅ Pruning system initialized with {self.pruning_level} level ({backup_status})")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize pruning system: {e}")
                self.enable_pruning = False
    
    def should_prune_file(self, file_path: str) -> bool:
        """Determine if a file should be pruned based on size and age"""
        try:
            file_stat = os.stat(file_path)
            file_size_kb = file_stat.st_size / 1024
            
            # Only prune files larger than threshold
            if file_size_kb < self.pruning_threshold_kb:
                self.logger.debug(f"Skipping pruning for {file_path}: {file_size_kb:.1f}KB < {self.pruning_threshold_kb}KB threshold")
                return False
            
            # Check if file has grown significantly since last check
            old_size = self.file_sizes.get(file_path, 0)
            if file_stat.st_size > old_size * 1.2:  # 20% growth
                self.logger.info(f"File {file_path} has grown significantly: {old_size/1024:.1f}KB → {file_size_kb:.1f}KB")
                return True
            
            # Or if file is simply large enough
            return file_size_kb >= self.pruning_threshold_kb
            
        except Exception as e:
            self.logger.error(f"Error checking file size for {file_path}: {e}")
            return False
    
    def prune_file(self, file_path: str) -> bool:
        """Prune a single JSONL file and log the results"""
        if not self.enable_pruning:
            return False
        
        try:
            file_path_obj = Path(file_path)
            original_size = file_path_obj.stat().st_size
            
            self.logger.info(f"🔄 Pruning {file_path} ({original_size/1024:.1f}KB) with {self.pruning_level} level...")
            
            # Create backup if requested
            backup_path = None
            if self.auto_backup:
                backup_path = file_path_obj.with_suffix(f"{file_path_obj.suffix}.backup.{int(time.time())}")
                import shutil
                shutil.copy2(file_path_obj, backup_path)
                self.logger.debug(f"Created backup: {backup_path}")
            
            # Perform pruning using the core pruner
            result = self.pruner.process_file(file_path_obj, file_path_obj)
            
            # Calculate results
            new_size = file_path_obj.stat().st_size
            size_reduction = original_size - new_size
            reduction_percent = (size_reduction / original_size) * 100 if original_size > 0 else 0
            
            # Log pruning results
            pruning_info = {
                'timestamp': datetime.now().isoformat(),
                'file': file_path,
                'original_size_kb': original_size / 1024,
                'new_size_kb': new_size / 1024,
                'size_reduction_kb': size_reduction / 1024,
                'reduction_percent': reduction_percent,
                'pruning_level': self.pruning_level,
                'messages_processed': result.get('messages_processed', 'unknown'),
                'messages_preserved': result.get('messages_preserved', 'unknown')
            }
            
            # Write to pruning log
            with open(self.pruned_files_log, 'a') as f:
                f.write(json.dumps(pruning_info) + '\n')
            
            self.logger.info(f"✅ Pruned {file_path}: {original_size/1024:.1f}KB → {new_size/1024:.1f}KB "
                           f"({reduction_percent:.1f}% reduction)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to prune {file_path}: {e}")
            return False
    
    def save_state(self):
        """Save current state to file for --since-last-run functionality"""
        state = {
            'file_timestamps': self.file_timestamps,
            'file_sizes': self.file_sizes,
            'last_run': datetime.now().isoformat(),
            'pruning_enabled': self.enable_pruning,
            'pruning_level': self.pruning_level
        }
        try:
            with open(self.state_file, 'wb') as f:
                pickle.dump(state, f)
            self.logger.debug(f"State saved to {self.state_file}")
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
    
    def load_state(self) -> bool:
        """Load previous state from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'rb') as f:
                    state = pickle.load(f)
                self.file_timestamps = state.get('file_timestamps', {})
                self.file_sizes = state.get('file_sizes', {})
                last_run = state.get('last_run', 'Unknown')
                self.logger.info(f"Loaded previous state from {last_run}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to load state: {e}")
        return False
        
    def scan_jsonl_files(self) -> Set[str]:
        """Scan for all JSONL files in projects directory"""
        jsonl_files = set()
        if self.projects_dir.exists():
            for project_dir in self.projects_dir.iterdir():
                if project_dir.is_dir():
                    for jsonl_file in project_dir.glob("*.jsonl"):
                        jsonl_files.add(str(jsonl_file))
        return jsonl_files
    
    def get_file_info(self, file_path: str) -> tuple:
        """Get file modification time and size"""
        try:
            stat = os.stat(file_path)
            return stat.st_mtime, stat.st_size
        except OSError as e:
            self.logger.debug(f"Error getting file info for {file_path}: {e}")
            return 0, 0
    
    def read_jsonl_changes(self, file_path: str, old_size: int) -> list:
        """Read new lines from JSONL file since last check"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.seek(old_size)
                new_lines = []
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            # Parse JSON to validate and format
                            data = json.loads(line)
                            new_lines.append(data)
                        except json.JSONDecodeError:
                            # If not valid JSON, still include the raw line
                            new_lines.append({"raw_line": line})
                return new_lines
        except Exception as e:
            self.logger.error(f"Error reading {file_path}: {e}")
            return []
    
    def write_changes_to_file(self, file_path: str, changes: list):
        """Write changes to the output text file"""
        if not changes:
            return
            
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"CHANGES DETECTED: {datetime.now().isoformat()}\n")
                f.write(f"FILE: {file_path}\n")
                f.write(f"NEW ENTRIES: {len(changes)}\n")
                f.write(f"{'='*80}\n")
                
                for i, change in enumerate(changes, 1):
                    f.write(f"\n--- Entry {i} ---\n")
                    if isinstance(change, dict) and "raw_line" in change:
                        f.write(f"Raw Line: {change['raw_line']}\n")
                    else:
                        f.write(f"JSON Data: {json.dumps(change, indent=2, ensure_ascii=False)}\n")
                
                f.write(f"\n{'='*80}\n\n")
                
        except Exception as e:
            self.logger.error(f"Error writing to output file: {e}")
    
    def check_for_changes(self, process_all: bool = False):
        """Check all JSONL files for changes"""
        current_files = self.scan_jsonl_files()
        self.logger.debug(f"Scanning {len(current_files)} JSONL files")
        
        files_that_need_pruning = []
        
        # Check for new or modified files
        for file_path in current_files:
            mtime, size = self.get_file_info(file_path)
            
            if file_path not in self.file_timestamps:
                # New file detected
                if process_all:
                    # Process all mode - read entire file
                    self.logger.info(f"Processing entire file: {file_path}")
                    changes = self.read_jsonl_changes(file_path, 0)
                    if changes:
                        self.write_changes_to_file(file_path, changes)
                else:
                    # Normal mode - just track it, don't read existing content
                    self.logger.info(f"New file detected (tracking for future changes): {file_path}")
                
                self.file_timestamps[file_path] = mtime
                self.file_sizes[file_path] = size
                
                # Check if new file needs pruning
                if self.should_prune_file(file_path):
                    files_that_need_pruning.append(file_path)
                    
            elif (mtime > self.file_timestamps[file_path] or 
                  size != self.file_sizes.get(file_path, 0)):
                # File modified - improved detection
                old_mtime = self.file_timestamps[file_path]
                old_size = self.file_sizes.get(file_path, 0)
                
                self.logger.info(f"File modified: {file_path}")
                self.logger.debug(f"  Size: {old_size} -> {size}")
                self.logger.debug(f"  mtime: {old_mtime} -> {mtime}")
                
                # Track changes for monitoring
                if size > old_size:
                    # File grew - read new content
                    changes = self.read_jsonl_changes(file_path, old_size)
                    if changes:
                        self.write_changes_to_file(file_path, changes)
                elif size < old_size:
                    # File shrunk - this is unusual but log it
                    self.logger.warning(f"File {file_path} shrunk from {old_size} to {size} bytes")
                elif size == old_size and mtime > old_mtime:
                    # Same size but modified time changed - might be internal changes
                    self.logger.info(f"File {file_path} modified without size change - checking for changes")
                    changes = self.read_jsonl_changes(file_path, old_size)
                    if changes:
                        self.write_changes_to_file(file_path, changes)
                
                # Update tracking info
                self.file_timestamps[file_path] = mtime
                self.file_sizes[file_path] = size
                
                # Check if modified file needs pruning
                if self.should_prune_file(file_path):
                    files_that_need_pruning.append(file_path)
        
        # Remove deleted files from tracking
        tracked_files = set(self.file_timestamps.keys())
        deleted_files = tracked_files - current_files
        for deleted_file in deleted_files:
            self.logger.info(f"File deleted: {deleted_file}")
            del self.file_timestamps[deleted_file]
            if deleted_file in self.file_sizes:
                del self.file_sizes[deleted_file]
        
        # Perform pruning on files that need it
        if files_that_need_pruning and self.enable_pruning:
            self.logger.info(f"🔄 Found {len(files_that_need_pruning)} files that need pruning")
            for file_path in files_that_need_pruning:
                self.prune_file(file_path)
                # Update file size tracking after pruning
                _, new_size = self.get_file_info(file_path)
                self.file_sizes[file_path] = new_size
        
        # Log summary statistics
        if deleted_files:
            self.logger.debug(f"Tracking {len(self.file_timestamps)} files, {len(deleted_files)} deleted")
        else:
            self.logger.debug(f"Tracking {len(self.file_timestamps)} files")
    
    def check_since_last_run(self):
        """Check for changes since last program run"""
        if not self.load_state():
            self.logger.warning("No previous state found. Use --process-all for initial run.")
            return
            
        self.logger.info("Checking for changes since last run...")
        self.check_for_changes()  # This will catch files that changed since last run
        
        # Also check for entirely new files that weren't tracked before
        current_files = self.scan_jsonl_files()
        for file_path in current_files:
            if file_path not in self.file_timestamps:
                self.logger.info(f"New file since last run: {file_path}")
                mtime, size = self.get_file_info(file_path)
                changes = self.read_jsonl_changes(file_path, 0)
                if changes:
                    self.write_changes_to_file(file_path, changes)
                self.file_timestamps[file_path] = mtime
                self.file_sizes[file_path] = size
                
                # Check if new file needs pruning
                if self.should_prune_file(file_path):
                    self.prune_file(file_path)
                    # Update file size after pruning
                    _, new_size = self.get_file_info(file_path)
                    self.file_sizes[file_path] = new_size
    
    def run(self, check_interval: int = 5, process_all: bool = False, since_last_run: bool = False):
        """Run the monitor with specified options"""
        self.logger.info(f"Starting Claude Code Monitor with Pruning...")
        self.logger.info(f"Monitoring directory: {self.projects_dir}")
        self.logger.info(f"Output file: {self.output_file}")
        if self.enable_pruning:
            self.logger.info(f"🔄 Pruning: {self.pruning_level} level, threshold: {self.pruning_threshold_kb}KB, backup: {self.auto_backup}")
        else:
            self.logger.info("❌ Pruning: Disabled")
        
        if since_last_run:
            # One-time check for changes since last run
            self.check_since_last_run()
            self.save_state()
            self.logger.info("Changes since last run processed. Exiting.")
            return
        elif process_all:
            # One-time processing of all files
            self.logger.info("Processing all existing JSONL files...")
            self.check_for_changes(process_all=True)
            self.save_state()
            self.logger.info("All files processed. Exiting.")
            return
        else:
            # Normal monitoring mode
            self.logger.info(f"Check interval: {check_interval} seconds")
            
            # Initial scan (track but don't process existing files)
            self.check_for_changes()
            
            try:
                while True:
                    time.sleep(check_interval)
                    self.check_for_changes()
                    self.save_state()  # Save state periodically
            except KeyboardInterrupt:
                self.logger.info("Monitor stopped by user")
                self.save_state()  # Save final state


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code Monitor with Automatic JSONL Pruning - Monitor ~/.claude/projects/ for JSONL changes and automatically optimize files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main_with_pruning.py                           # Normal monitoring mode with pruning
  python main_with_pruning.py --interval 2              # Monitor with 2-second intervals
  python main_with_pruning.py --process-all             # Process all existing JSONL files once and exit
  python main_with_pruning.py --since-last-run          # Process changes since last run and exit
  python main_with_pruning.py --no-pruning              # Disable automatic pruning
  python main_with_pruning.py --pruning-level aggressive --threshold 50  # Aggressive pruning for files >50KB
        """
    )
    
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=5,
        help='Check interval in seconds (default: 5)'
    )
    
    parser.add_argument(
        '--process-all', '-a',
        action='store_true',
        help='Process all existing JSONL files and exit (like original behavior)'
    )
    
    parser.add_argument(
        '--since-last-run', '-s',
        action='store_true',
        help='Process only changes since last program run and exit'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='claude_session_changes.txt',
        help='Output file path (default: claude_session_changes.txt)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose debug logging for troubleshooting'
    )
    
    # Pruning-specific arguments
    parser.add_argument(
        '--no-pruning',
        action='store_true',
        help='Disable automatic pruning (monitoring only)'
    )
    
    parser.add_argument(
        '--pruning-level',
        choices=['light', 'medium', 'aggressive', 'ultra'],
        default='medium',
        help='Pruning aggressiveness level (default: medium)'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Disable automatic backup before pruning (faster but less safe)'
    )
    
    parser.add_argument(
        '--threshold',
        type=int,
        default=100,
        help='Only prune files larger than this size in KB (default: 100)'
    )
    
    args = parser.parse_args()
    
    # Set up logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        print("Debug logging enabled")
    
    print("Claude Code Monitor with Automatic JSONL Pruning")
    print("Monitoring ~/.claude/projects/ for JSONL changes")
    
    if args.no_pruning:
        print("🔄 Pruning: DISABLED (monitoring only)")
    else:
        backup_status = "with backup" if not args.no_backup else "without backup"
        print(f"🔄 Pruning: {args.pruning_level} level, {args.threshold}KB+ files, {backup_status}")
    
    if args.process_all:
        print("Mode: Processing ALL existing JSONL files")
    elif args.since_last_run:
        print("Mode: Processing changes since last run")
    else:
        print("Mode: Real-time monitoring (only NEW changes after start)")
        print("Press Ctrl+C to stop")
    
    if args.verbose:
        print(f"Check interval: {args.interval} seconds")
        print(f"Output file: {args.output}")
    
    print()
    
    # Create and run the monitor
    monitor = ClaudeCodeMonitorWithPruning(
        output_file=args.output,
        enable_pruning=not args.no_pruning,
        pruning_level=args.pruning_level,
        auto_backup=not args.no_backup,
        pruning_threshold_kb=args.threshold
    )
    monitor.run(
        check_interval=args.interval,
        process_all=args.process_all,
        since_last_run=args.since_last_run
    )


if __name__ == "__main__":
    main()