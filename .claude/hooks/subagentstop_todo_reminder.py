#!/usr/bin/env python3
"""
Claude Code Todo Reminder Hook

Monitors subagent completion and reminds the AI system to update ACTIVE_TODOS.md
with implemented work. Uses rate limiting to prevent spam and smart detection
to only remind when actual implementation occurs.

Hook Type: PostToolUse
Trigger: After tool execution
Output: Exit code 2 with stderr reminder for significant implementation work
"""

import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Add utils to path for imports
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from rate_limiter import RateLimiter
from activity_detector import ActivityDetector, ActivityType

# Configure logging (errors only, to avoid cluttering output)
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(".claude/hooks.log"), mode='a'),
        logging.NullHandler()  # Suppress console output
    ]
)
logger = logging.getLogger(__name__)

class TodoReminderHook:
    """
    Intelligent todo reminder hook with rate limiting and activity detection.
    """
    
    def __init__(self):
        """Initialize hook components."""
        self.rate_limiter = RateLimiter(interval_seconds=240)  # 4 minutes
        self.activity_detector = ActivityDetector()
        
        # Configuration
        self.min_significance_score = 30  # Minimum score to trigger reminder
        self.action_key = "todo_reminder"
    
    def process_hook_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Process hook input and determine if reminder is needed.
        
        Args:
            input_data: Hook input data from Claude Code
            
        Returns:
            True if reminder should be shown, False otherwise
        """
        try:
            # Check rate limiting first
            if not self.rate_limiter.can_execute(self.action_key):
                logger.debug(f"Rate limited - {self.rate_limiter.get_time_until_next(self.action_key):.1f}s remaining")
                return False
            
            # Analyze recent activity
            activity_analysis = self.activity_detector.analyze_recent_activity(lookback_minutes=5)
            
            # Determine if reminder is warranted
            should_remind = self._should_remind(input_data, activity_analysis)
            
            if should_remind:
                # Record execution to enforce rate limiting
                self.rate_limiter.record_execution(self.action_key)
                logger.info(f"Todo reminder triggered: {activity_analysis.summary}")
                return True
            
            logger.debug(f"No reminder needed: {activity_analysis.summary}")
            return False
            
        except Exception as e:
            logger.error(f"Error processing hook input: {e}")
            return False
    
    def _should_remind(self, input_data: Dict[str, Any], activity_analysis) -> bool:
        """
        Determine if reminder should be shown based on activity analysis.
        
        Args:
            input_data: Hook input data
            activity_analysis: Recent activity analysis
            
        Returns:
            True if reminder is warranted
        """
        # Check significance score threshold
        if activity_analysis.significance_score < self.min_significance_score:
            return False
        
        # Must be implementation activity (not just research)
        if activity_analysis.activity_type != ActivityType.IMPLEMENTATION:
            return False
        
        # Must have some actual implementation actions
        if activity_analysis.implementation_count < 2:
            return False
        
        # Additional checks based on input data
        tool_name = input_data.get('tool', '')
        
        # High-value tools that likely indicate completion
        completion_tools = {'Write', 'Edit', 'MultiEdit', 'Bash'}
        if tool_name in completion_tools:
            return True
        
        # Task tool - check if it was implementation-focused
        if tool_name == 'Task' and activity_analysis.implementation_count > 0:
            return True
        
        return False
    
    def generate_reminder_message(self) -> str:
        """Generate appropriate reminder message."""
        return (
            "Update ACTIVE_TODOS.md with completed implementation work. "
            "Mark completed items and update status for work in progress."
        )

def main():
    """
    Main hook execution function.
    
    Reads input from stdin, processes activity, and outputs reminder if needed.
    Exit codes:
        0: No reminder needed
        2: Reminder needed (message sent to stderr)
    """
    try:
        # Read hook input data from stdin
        try:
            input_data = json.load(sys.stdin)
        except json.JSONDecodeError:
            # If no valid JSON input, treat as no-op
            sys.exit(0)
        
        # Initialize and process hook
        hook = TodoReminderHook()
        
        if hook.process_hook_input(input_data):
            # Output reminder to stderr and exit with code 2
            reminder_message = hook.generate_reminder_message()
            print(reminder_message, file=sys.stderr)
            sys.exit(2)
        
        # No reminder needed
        sys.exit(0)
        
    except Exception as e:
        # Log error but don't interrupt workflow
        logger.error(f"Todo reminder hook failed: {e}")
        sys.exit(0)

if __name__ == "__main__":
    main()