"""
Tests for rate limiting functionality.
"""

import pytest
import time
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from rate_limiter import RateLimiter

class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def setup_method(self):
        """Setup test with temporary state directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.state_dir = Path(self.temp_dir)
        self.limiter = RateLimiter(interval_seconds=2, state_dir=self.state_dir)
    
    def teardown_method(self):
        """Cleanup temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_first_execution_allowed(self):
        """Test that first execution is always allowed."""
        assert self.limiter.can_execute("test_action") == True
    
    def test_rate_limiting_prevents_spam(self):
        """Test that rate limiting prevents rapid successive executions."""
        action_key = "test_action"
        
        # First execution should be allowed
        assert self.limiter.can_execute(action_key) == True
        self.limiter.record_execution(action_key)
        
        # Immediate second execution should be blocked
        assert self.limiter.can_execute(action_key) == False
    
    def test_rate_limiting_expires(self):
        """Test that rate limiting expires after interval."""
        action_key = "test_action"
        
        # Record execution
        self.limiter.record_execution(action_key)
        assert self.limiter.can_execute(action_key) == False
        
        # Mock time to simulate interval passage
        with patch('time.time', return_value=time.time() + 3):
            assert self.limiter.can_execute(action_key) == True
    
    def test_different_actions_independent(self):
        """Test that different actions have independent rate limits."""
        self.limiter.record_execution("action1")
        
        # Action1 should be rate limited
        assert self.limiter.can_execute("action1") == False
        
        # Action2 should be allowed
        assert self.limiter.can_execute("action2") == True
    
    def test_state_persistence(self):
        """Test that rate limiting state persists across instances."""
        action_key = "persistent_action"
        
        # Record execution with first instance
        self.limiter.record_execution(action_key)
        
        # Create new instance with same state directory
        new_limiter = RateLimiter(interval_seconds=2, state_dir=self.state_dir)
        
        # Should still be rate limited
        assert new_limiter.can_execute(action_key) == False
    
    def test_time_until_next(self):
        """Test time calculation until next allowed execution."""
        action_key = "timed_action"
        
        # Before any execution
        assert self.limiter.get_time_until_next(action_key) == 0.0
        
        # After execution
        self.limiter.record_execution(action_key)
        time_remaining = self.limiter.get_time_until_next(action_key)
        
        # Should be close to interval (allowing for small timing variations)
        assert 1.5 <= time_remaining <= 2.5
    
    def test_cleanup_old_entries(self):
        """Test cleanup of old rate limiting entries."""
        # Create old entry by mocking time
        old_time = time.time() - 25 * 3600  # 25 hours ago
        
        with patch('time.time', return_value=old_time):
            self.limiter.record_execution("old_action")
        
        # Record recent entry
        self.limiter.record_execution("new_action")
        
        # Cleanup entries older than 24 hours
        self.limiter.cleanup_old_entries(max_age_seconds=24 * 3600)
        
        # Old entry should be removed (can execute immediately)
        assert self.limiter.can_execute("old_action") == True
        
        # New entry should still be rate limited
        assert self.limiter.can_execute("new_action") == False
    
    def test_corrupted_state_file_recovery(self):
        """Test recovery from corrupted state file."""
        # Create corrupted state file
        state_file = self.state_dir / "rate_limits.json"
        with open(state_file, 'w') as f:
            f.write("invalid json content")
        
        # Should handle gracefully and allow execution
        assert self.limiter.can_execute("test_action") == True
    
    def test_readonly_state_directory(self):
        """Test graceful handling when state directory is readonly."""
        # Make state directory readonly
        self.state_dir.chmod(0o444)
        
        try:
            # Should not crash, but may not persist state
            assert self.limiter.can_execute("test_action") == True
            self.limiter.record_execution("test_action")
            
            # Should still function (even if state isn't persisted)
            result = self.limiter.can_execute("test_action")
            assert isinstance(result, bool)
            
        finally:
            # Restore permissions for cleanup
            self.state_dir.chmod(0o755)