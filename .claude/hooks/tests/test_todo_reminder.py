"""
Tests for todo reminder hook functionality.
"""

import pytest
import json
import tempfile
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add hook directory to path
hook_dir = Path(__file__).parent.parent
sys.path.insert(0, str(hook_dir))

from subagentstop_todo_reminder import TodoReminderHook

class TestTodoReminderHook:
    """Test todo reminder hook functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock the utilities to avoid file system dependencies
        self.mock_rate_limiter = MagicMock()
        self.mock_activity_detector = MagicMock()
        
        # Create hook instance
        self.hook = TodoReminderHook()
    
    def teardown_method(self):
        """Cleanup temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('subagentstop_todo_reminder.RateLimiter')
    @patch('subagentstop_todo_reminder.ActivityDetector')
    def test_hook_initialization(self, mock_activity_cls, mock_rate_cls):
        """Test hook initializes properly."""
        hook = TodoReminderHook()
        
        # Should initialize rate limiter with 4-minute interval
        mock_rate_cls.assert_called_once_with(interval_seconds=240)
        mock_activity_cls.assert_called_once()
    
    def test_rate_limited_execution_blocked(self):
        """Test that rate-limited executions are blocked."""
        # Mock rate limiter to return False
        self.hook.rate_limiter.can_execute.return_value = False
        
        input_data = {"tool": "Write", "status": "success"}
        result = self.hook.process_hook_input(input_data)
        
        assert result == False
        self.hook.rate_limiter.can_execute.assert_called_once_with("todo_reminder")
    
    def test_low_significance_score_blocked(self):
        """Test that low significance activities don't trigger reminders."""
        # Mock rate limiter to allow execution
        self.hook.rate_limiter.can_execute.return_value = True
        
        # Mock activity detector to return low significance
        mock_analysis = MagicMock()
        mock_analysis.significance_score = 10  # Below threshold
        mock_analysis.activity_type = ActivityType.IMPLEMENTATION
        mock_analysis.implementation_count = 1
        self.hook.activity_detector.analyze_recent_activity.return_value = mock_analysis
        
        input_data = {"tool": "Write", "status": "success"}
        result = self.hook.process_hook_input(input_data)
        
        assert result == False
    
    def test_research_activity_blocked(self):
        """Test that research activities don't trigger reminders."""
        # Mock rate limiter to allow execution
        self.hook.rate_limiter.can_execute.return_value = True
        
        # Mock activity detector to return research activity
        mock_analysis = MagicMock()
        mock_analysis.significance_score = 50  # Above threshold
        mock_analysis.activity_type = ActivityType.RESEARCH  # But research
        mock_analysis.implementation_count = 1
        self.hook.activity_detector.analyze_recent_activity.return_value = mock_analysis
        
        input_data = {"tool": "Read", "status": "success"}
        result = self.hook.process_hook_input(input_data)
        
        assert result == False
    
    def test_implementation_activity_triggers_reminder(self):
        """Test that significant implementation activities trigger reminders."""
        # Mock rate limiter to allow execution
        self.hook.rate_limiter.can_execute.return_value = True
        
        # Mock activity detector to return significant implementation
        mock_analysis = MagicMock()
        mock_analysis.significance_score = 50  # Above threshold
        mock_analysis.activity_type = ActivityType.IMPLEMENTATION
        mock_analysis.implementation_count = 3  # Sufficient implementation
        self.hook.activity_detector.analyze_recent_activity.return_value = mock_analysis
        
        input_data = {"tool": "Write", "status": "success"}
        result = self.hook.process_hook_input(input_data)
        
        assert result == True
        self.hook.rate_limiter.record_execution.assert_called_once_with("todo_reminder")
    
    def test_task_tool_implementation_triggers_reminder(self):
        """Test that Task tool with implementation work triggers reminders."""
        # Mock rate limiter to allow execution
        self.hook.rate_limiter.can_execute.return_value = True
        
        # Mock activity detector for mixed activity with implementation
        mock_analysis = MagicMock()
        mock_analysis.significance_score = 40  # Above threshold
        mock_analysis.activity_type = ActivityType.IMPLEMENTATION
        mock_analysis.implementation_count = 2  # Some implementation
        self.hook.activity_detector.analyze_recent_activity.return_value = mock_analysis
        
        input_data = {"tool": "Task", "status": "success"}
        result = self.hook.process_hook_input(input_data)
        
        assert result == True
    
    def test_error_handling_graceful(self):
        """Test that errors are handled gracefully without crashing."""
        # Mock rate limiter to raise exception
        self.hook.rate_limiter.can_execute.side_effect = Exception("Test error")
        
        input_data = {"tool": "Write", "status": "success"}
        result = self.hook.process_hook_input(input_data)
        
        # Should return False and not crash
        assert result == False
    
    def test_reminder_message_generation(self):
        """Test reminder message generation."""
        message = self.hook.generate_reminder_message()
        
        assert "ACTIVE_TODOS.md" in message
        assert "completed" in message.lower()
        assert len(message) > 20  # Should be substantive
    
    def test_completion_tools_high_priority(self):
        """Test that completion tools are given high priority."""
        # Mock for successful execution
        self.hook.rate_limiter.can_execute.return_value = True
        
        # Mock activity detector for minimal implementation
        mock_analysis = MagicMock()
        mock_analysis.significance_score = 35  # Just above threshold
        mock_analysis.activity_type = ActivityType.IMPLEMENTATION
        mock_analysis.implementation_count = 2  # Minimal implementation
        self.hook.activity_detector.analyze_recent_activity.return_value = mock_analysis
        
        # Test high-value completion tools
        for tool in ['Write', 'Edit', 'MultiEdit', 'Bash']:
            input_data = {"tool": tool, "status": "success"}
            result = self.hook.process_hook_input(input_data)
            assert result == True, f"Tool {tool} should trigger reminder"


class TestTodoReminderCLI:
    """Test command-line interface of todo reminder hook."""
    
    def setup_method(self):
        """Setup test environment."""
        self.hook_script = Path(__file__).parent.parent / "subagentstop_todo_reminder.py"
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_hook_script_exists_and_executable(self):
        """Test that hook script exists and is executable."""
        assert self.hook_script.exists()
        assert self.hook_script.is_file()
        # Check if executable bit is set
        assert self.hook_script.stat().st_mode & 0o111 != 0
    
    def test_invalid_json_input_handled(self):
        """Test handling of invalid JSON input."""
        # Run hook with invalid JSON
        result = subprocess.run(
            ["python", str(self.hook_script)],
            input="invalid json",
            text=True,
            capture_output=True
        )
        
        # Should exit with code 0 (no reminder)
        assert result.returncode == 0
    
    def test_empty_input_handled(self):
        """Test handling of empty input."""
        result = subprocess.run(
            ["python", str(self.hook_script)],
            input="",
            text=True,
            capture_output=True
        )
        
        # Should exit with code 0 (no reminder)
        assert result.returncode == 0
    
    @patch('subagentstop_todo_reminder.TodoReminderHook')
    def test_reminder_exit_code_2(self, mock_hook_cls):
        """Test that reminders exit with code 2 and output to stderr."""
        # Mock hook to trigger reminder
        mock_hook = MagicMock()
        mock_hook.process_hook_input.return_value = True
        mock_hook.generate_reminder_message.return_value = "Test reminder"
        mock_hook_cls.return_value = mock_hook
        
        input_data = {"tool": "Write", "status": "success"}
        
        result = subprocess.run(
            ["python", str(self.hook_script)],
            input=json.dumps(input_data),
            text=True,
            capture_output=True
        )
        
        # Should exit with code 2 for reminder
        assert result.returncode == 2
        # Reminder should be in stderr
        assert "Test reminder" in result.stderr
    
    @patch('subagentstop_todo_reminder.TodoReminderHook')
    def test_no_reminder_exit_code_0(self, mock_hook_cls):
        """Test that no reminder exits with code 0."""
        # Mock hook to not trigger reminder
        mock_hook = MagicMock()
        mock_hook.process_hook_input.return_value = False
        mock_hook_cls.return_value = mock_hook
        
        input_data = {"tool": "Read", "status": "success"}
        
        result = subprocess.run(
            ["python", str(self.hook_script)],
            input=json.dumps(input_data),
            text=True,
            capture_output=True
        )
        
        # Should exit with code 0 (no reminder)
        assert result.returncode == 0
        # Should not output to stderr
        assert result.stderr == ""