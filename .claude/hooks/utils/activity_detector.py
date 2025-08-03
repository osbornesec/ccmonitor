"""
Activity detection and significance analysis for Claude Code hooks.
Distinguishes between implementation work and research activities.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, NamedTuple
from dataclasses import dataclass
from enum import Enum

class ActivityType(Enum):
    """Types of development activities."""
    IMPLEMENTATION = "implementation"
    RESEARCH = "research"
    MAINTENANCE = "maintenance"
    TESTING = "testing"

@dataclass
class ActivityAnalysis:
    """Result of activity analysis."""
    activity_type: ActivityType
    significance_score: int  # 0-100
    implementation_count: int
    research_count: int
    recent_files_modified: List[str]
    summary: str

class ActivityDetector:
    """
    Analyzes tool usage patterns to determine implementation significance.
    
    Distinguishes between:
    - Implementation: File creation, modification, code writing
    - Research: Reading files, searching, documentation lookup
    - Maintenance: Testing, validation, cleanup
    """
    
    def __init__(self, memory_file: Optional[Path] = None):
        """
        Initialize activity detector.
        
        Args:
            memory_file: Path to memory.jsonl file (default: .claude/memory.jsonl)
        """
        self.memory_file = memory_file or Path(".claude/memory.jsonl")
        
        # Tool classifications
        self.implementation_tools = {
            'Write', 'Edit', 'MultiEdit', 'Bash', 'NotebookEdit'
        }
        
        self.research_tools = {
            'Read', 'Grep', 'Glob', 'WebFetch', 'WebSearch', 'NotebookRead'
        }
        
        self.maintenance_tools = {
            'LS', 'Task'  # Task tool can be either, depends on context
        }
        
        # File patterns that indicate implementation
        self.implementation_patterns = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.rs', '.go', 
            '.java', '.cpp', '.c', '.h', '.css', '.html', '.vue',
            '.sql', '.sh', '.yml', '.yaml', '.json', '.toml'
        }
        
        # File patterns that indicate documentation/research
        self.documentation_patterns = {
            '.md', '.txt', '.rst', '.pdf', '.doc', '.docx'
        }
    
    def analyze_recent_activity(self, lookback_minutes: int = 10) -> ActivityAnalysis:
        """
        Analyze recent activity to determine significance.
        
        Args:
            lookback_minutes: How far back to analyze (default 10 minutes)
            
        Returns:
            ActivityAnalysis with significance assessment
        """
        cutoff_time = time.time() - (lookback_minutes * 60)
        recent_entries = self._load_recent_memory(cutoff_time)
        
        if not recent_entries:
            return ActivityAnalysis(
                activity_type=ActivityType.RESEARCH,
                significance_score=0,
                implementation_count=0,
                research_count=0,
                recent_files_modified=[],
                summary="No recent activity detected"
            )
        
        return self._analyze_entries(recent_entries)
    
    def _load_recent_memory(self, cutoff_time: float) -> List[Dict]:
        """Load memory entries after cutoff time."""
        recent_entries = []
        
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            entry_time = self._parse_timestamp(entry.get('timestamp'))
                            
                            if entry_time and entry_time >= cutoff_time:
                                recent_entries.append(entry)
                        except json.JSONDecodeError:
                            continue
        except IOError:
            pass
        
        return recent_entries
    
    def _analyze_entries(self, entries: List[Dict]) -> ActivityAnalysis:
        """Analyze memory entries for activity patterns."""
        implementation_count = 0
        research_count = 0
        maintenance_count = 0
        files_modified = set()
        
        for entry in entries:
            tool_name = self._extract_tool_name(entry)
            file_path = self._extract_file_path(entry)
            
            if tool_name in self.implementation_tools:
                implementation_count += 1
                if file_path and self._is_implementation_file(file_path):
                    files_modified.add(file_path)
                    implementation_count += 1  # Extra weight for code files
            
            elif tool_name in self.research_tools:
                research_count += 1
            
            elif tool_name in self.maintenance_tools:
                maintenance_count += 1
                # Task tool analysis - check if it's implementation-focused
                if tool_name == 'Task' and self._is_implementation_task(entry):
                    implementation_count += 2  # Task tool doing implementation
            
            # Bash commands can be implementation or maintenance
            if tool_name == 'Bash':
                if self._is_implementation_bash(entry):
                    implementation_count += 1
        
        # Calculate significance score
        significance_score = self._calculate_significance(
            implementation_count, research_count, maintenance_count, len(files_modified)
        )
        
        # Determine primary activity type
        activity_type = self._determine_activity_type(
            implementation_count, research_count, maintenance_count
        )
        
        # Generate summary
        summary = self._generate_summary(
            activity_type, implementation_count, research_count, 
            maintenance_count, files_modified
        )
        
        return ActivityAnalysis(
            activity_type=activity_type,
            significance_score=significance_score,
            implementation_count=implementation_count,
            research_count=research_count,
            recent_files_modified=list(files_modified),
            summary=summary
        )
    
    def _extract_tool_name(self, entry: Dict) -> str:
        """Extract tool name from memory entry."""
        message = entry.get('message', {})
        
        # Check tool_calls in message
        if 'tool_calls' in message:
            tool_calls = message['tool_calls']
            if tool_calls and len(tool_calls) > 0:
                return tool_calls[0].get('function', {}).get('name', '')
        
        # Check content for tool usage patterns
        content = message.get('content', '')
        if 'antml:invoke name=' in content:
            # Extract tool name from antml:invoke
            start = content.find('antml:invoke name="') + 18
            end = content.find('"', start)
            if start > 17 and end > start:
                return content[start:end]
        
        return ''
    
    def _extract_file_path(self, entry: Dict) -> Optional[str]:
        """Extract file path from memory entry."""
        message = entry.get('message', {})
        content = message.get('content', '')
        
        # Look for file_path parameter
        if 'file_path' in content:
            # Extract file path from parameter
            start = content.find('file_path">') + 11
            end = content.find('</', start)
            if start > 10 and end > start:
                return content[start:end]
        
        # Look for common file references
        for pattern in ['/home/', './', '../']:
            if pattern in content:
                # Simple extraction - could be improved
                lines = content.split('\n')
                for line in lines:
                    if pattern in line and any(ext in line for ext in 
                                             self.implementation_patterns.union(self.documentation_patterns)):
                        return line.strip()
        
        return None
    
    def _is_implementation_file(self, file_path: str) -> bool:
        """Check if file path indicates implementation work."""
        return any(file_path.endswith(pattern) for pattern in self.implementation_patterns)
    
    def _is_implementation_task(self, entry: Dict) -> bool:
        """Analyze Task tool usage to determine if it's implementation-focused."""
        content = entry.get('message', {}).get('content', '').lower()
        
        implementation_keywords = [
            'implement', 'create', 'write', 'build', 'develop',
            'code', 'function', 'class', 'module', 'feature'
        ]
        
        research_keywords = [
            'analyze', 'search', 'find', 'look', 'check', 'examine'
        ]
        
        impl_score = sum(1 for keyword in implementation_keywords if keyword in content)
        research_score = sum(1 for keyword in research_keywords if keyword in content)
        
        return impl_score > research_score
    
    def _is_implementation_bash(self, entry: Dict) -> bool:
        """Analyze Bash command to determine if it's implementation-related."""
        content = entry.get('message', {}).get('content', '').lower()
        
        implementation_commands = [
            'git add', 'git commit', 'npm install', 'pip install',
            'mkdir', 'touch', 'mv', 'cp', 'chmod +x'
        ]
        
        return any(cmd in content for cmd in implementation_commands)
    
    def _calculate_significance(self, impl_count: int, research_count: int, 
                               maint_count: int, files_count: int) -> int:
        """Calculate overall significance score (0-100)."""
        # Base score from implementation activities
        score = impl_count * 15
        
        # Bonus for file modifications
        score += files_count * 10
        
        # Penalty for high research-to-implementation ratio
        total_activity = impl_count + research_count + maint_count
        if total_activity > 0:
            research_ratio = research_count / total_activity
            if research_ratio > 0.7:  # >70% research
                score = int(score * 0.5)  # Reduce significance
        
        # Ensure score is in valid range
        return max(0, min(100, score))
    
    def _determine_activity_type(self, impl_count: int, research_count: int, 
                                maint_count: int) -> ActivityType:
        """Determine primary activity type."""
        if impl_count > research_count and impl_count > maint_count:
            return ActivityType.IMPLEMENTATION
        elif research_count > impl_count and research_count > maint_count:
            return ActivityType.RESEARCH
        elif maint_count > 0:
            return ActivityType.MAINTENANCE
        else:
            return ActivityType.RESEARCH  # Default
    
    def _generate_summary(self, activity_type: ActivityType, impl_count: int, 
                         research_count: int, maint_count: int, 
                         files_modified: set) -> str:
        """Generate human-readable activity summary."""
        if activity_type == ActivityType.IMPLEMENTATION:
            if files_modified:
                return f"Implementation work: {impl_count} actions, {len(files_modified)} files modified"
            else:
                return f"Implementation work: {impl_count} implementation actions"
        elif activity_type == ActivityType.RESEARCH:
            return f"Research activity: {research_count} research actions, {impl_count} implementation actions"
        elif activity_type == ActivityType.MAINTENANCE:
            return f"Maintenance activity: {maint_count} maintenance actions"
        else:
            return "Mixed development activity"
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[float]:
        """Parse timestamp string to Unix time."""
        if not timestamp_str:
            return None
        
        try:
            # Handle ISO format: 2025-08-01T19:51:21.024033
            if 'T' in timestamp_str:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                return dt.timestamp()
        except (ValueError, ImportError):
            pass
        
        return None