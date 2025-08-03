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

class ClaudeCodeMonitor:
    def __init__(self, projects_dir: str = None, output_file: str = "claude_session_changes.txt"):
        self.projects_dir = Path(projects_dir or os.path.expanduser("~/.claude/projects"))
        self.output_file = Path(output_file)
        self.file_timestamps: Dict[str, float] = {}
        self.file_sizes: Dict[str, int] = {}
        self.state_file = Path(".ccmonitor_state.pkl")
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Ensure output file exists
        self.output_file.touch(exist_ok=True)
    
    def save_state(self):
        """Save current state to file for --since-last-run functionality"""
        state = {
            'file_timestamps': self.file_timestamps,
            'file_sizes': self.file_sizes,
            'last_run': datetime.now().isoformat()
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
                    
            elif (mtime > self.file_timestamps[file_path] or 
                  size != self.file_sizes.get(file_path, 0)):
                # File modified - improved detection
                old_mtime = self.file_timestamps[file_path]
                old_size = self.file_sizes.get(file_path, 0)
                
                self.logger.info(f"File modified: {file_path}")
                self.logger.debug(f"  Size: {old_size} -> {size}")
                self.logger.debug(f"  mtime: {old_mtime} -> {mtime}")
                
                if size > old_size:
                    # File grew - read new content
                    changes = self.read_jsonl_changes(file_path, old_size)
                    if changes:
                        self.write_changes_to_file(file_path, changes)
                elif size < old_size:
                    # File shrunk - this is unusual but log it
                    self.logger.warning(f"File {file_path} shrunk from {old_size} to {size} bytes")
                    # Could re-read entire file if needed
                elif size == old_size and mtime > old_mtime:
                    # Same size but modified time changed - might be internal changes
                    self.logger.info(f"File {file_path} modified without size change - checking for changes")
                    # Try reading from current position to end to see if there are changes
                    changes = self.read_jsonl_changes(file_path, old_size)
                    if changes:
                        self.write_changes_to_file(file_path, changes)
                
                # Update tracking info
                self.file_timestamps[file_path] = mtime
                self.file_sizes[file_path] = size
        
        # Remove deleted files from tracking
        tracked_files = set(self.file_timestamps.keys())
        deleted_files = tracked_files - current_files
        for deleted_file in deleted_files:
            self.logger.info(f"File deleted: {deleted_file}")
            del self.file_timestamps[deleted_file]
            if deleted_file in self.file_sizes:
                del self.file_sizes[deleted_file]
        
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
    
    def run(self, check_interval: int = 5, process_all: bool = False, since_last_run: bool = False):
        """Run the monitor with specified options"""
        self.logger.info(f"Starting Claude Code Monitor...")
        self.logger.info(f"Monitoring directory: {self.projects_dir}")
        self.logger.info(f"Output file: {self.output_file}")
        
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
        description="Claude Code Monitor - Monitor ~/.claude/projects/ for JSONL changes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Normal monitoring mode (only new changes)
  python main.py --interval 2       # Monitor with 2-second intervals
  python main.py --process-all       # Process all existing JSONL files once and exit
  python main.py --since-last-run    # Process changes since last run and exit
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
    
    args = parser.parse_args()
    
    # Set up logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        print("Debug logging enabled")
    
    print("Claude Code Monitor - Monitoring ~/.claude/projects/ for JSONL changes")
    
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
    monitor = ClaudeCodeMonitor(output_file=args.output)
    monitor.run(
        check_interval=args.interval,
        process_all=args.process_all,
        since_last_run=args.since_last_run
    )


if __name__ == "__main__":
    main()
