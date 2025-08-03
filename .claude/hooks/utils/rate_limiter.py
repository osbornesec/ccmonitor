"""
Rate limiting utility for Claude Code hooks.
Prevents notification spam by enforcing time-based intervals.
"""

import json
import time
from pathlib import Path
from typing import Dict, Optional
import threading

class RateLimiter:
    """
    Time-based rate limiting with persistent state.
    
    Stores last execution times in JSON file to enforce
    minimum intervals between actions.
    """
    
    def __init__(self, interval_seconds: int = 240, state_dir: Optional[Path] = None):
        """
        Initialize rate limiter.
        
        Args:
            interval_seconds: Minimum time between executions (default 4 minutes)
            state_dir: Directory for state files (default: .claude/state/)
        """
        self.interval = interval_seconds
        self.state_dir = state_dir or Path(".claude/state")
        self.state_file = self.state_dir / "rate_limits.json"
        self._lock = threading.Lock()
        
        # Ensure state directory exists
        self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def can_execute(self, action_key: str) -> bool:
        """
        Check if enough time has elapsed since last execution.
        
        Args:
            action_key: Unique identifier for the action
            
        Returns:
            True if action can execute, False if rate limited
        """
        with self._lock:
            state = self._load_state()
            
            if action_key not in state:
                return True
            
            last_execution = state[action_key].get("last_execution", 0)
            elapsed = time.time() - last_execution
            
            return elapsed >= self.interval
    
    def record_execution(self, action_key: str) -> None:
        """
        Record execution time for rate limiting.
        
        Args:
            action_key: Unique identifier for the action
        """
        with self._lock:
            state = self._load_state()
            
            if action_key not in state:
                state[action_key] = {}
            
            state[action_key]["last_execution"] = time.time()
            self._save_state(state)
    
    def get_time_until_next(self, action_key: str) -> float:
        """
        Get seconds until next execution is allowed.
        
        Args:
            action_key: Unique identifier for the action
            
        Returns:
            Seconds until next execution (0 if can execute now)
        """
        with self._lock:
            state = self._load_state()
            
            if action_key not in state:
                return 0.0
            
            last_execution = state[action_key].get("last_execution", 0)
            elapsed = time.time() - last_execution
            remaining = self.interval - elapsed
            
            return max(0.0, remaining)
    
    def _load_state(self) -> Dict:
        """Load rate limiting state from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupted or unreadable, start fresh
            pass
        
        return {}
    
    def _save_state(self, state: Dict) -> None:
        """Save rate limiting state to file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except IOError:
            # If we can't save state, fail silently to avoid interrupting workflow
            pass
    
    def cleanup_old_entries(self, max_age_seconds: int = 86400) -> None:
        """
        Remove old entries from state file.
        
        Args:
            max_age_seconds: Remove entries older than this (default 24 hours)
        """
        with self._lock:
            state = self._load_state()
            current_time = time.time()
            
            # Remove entries older than max_age
            state = {
                key: value for key, value in state.items()
                if current_time - value.get("last_execution", 0) < max_age_seconds
            }
            
            self._save_state(state)