"""
Tests for activity detection and significance analysis.
"""

import pytest
import json
import time
import tempfile
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from activity_detector import ActivityDetector, ActivityType, ActivityAnalysis

class TestActivityDetector:
    """Test activity detection functionality."""
    
    def setup_method(self):
        """Setup test with temporary memory file."""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_file = Path(self.temp_dir) / "memory.jsonl"
        self.detector = ActivityDetector(memory_file=self.memory_file)
    
    def teardown_method(self):
        """Cleanup temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_memory_entry(self, tool_name: str, file_path: str = None, 
                           timestamp: str = None, content: str = ""):
        """Helper to create memory entry."""
        if timestamp is None:
            timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
        
        entry = {
            "timestamp": timestamp,
            "type": "assistant",
            "message": {
                "content": f'<invoke name="{tool_name}">\n{content}\n</invoke>',
                "tool_calls": [{
                    "function": {"name": tool_name}
                }]
            }
        }
        
        if file_path:
            entry["message"]["content"] = f'<invoke name="{tool_name}">\n<parameter name="file_path">{file_path}