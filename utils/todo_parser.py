#!/usr/bin/env python3
"""
Todo parsing utilities for ACTIVE_TODOS.md format

Provides parsing and generation capabilities for maintaining
format compatibility with existing todo management workflows.
"""

import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TodoItem:
    """Represents a single todo item with metadata"""
    task: str
    priority: str
    estimate: str
    dependencies: List[str] = None
    prp: Optional[str] = None
    status: str = "Not Started"
    subtasks: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.subtasks is None:
            self.subtasks = []


@dataclass 
class TodoSection:
    """Represents a section of todos with priority and metadata"""
    title: str
    priority: str
    todos: List[TodoItem]
    section_dependencies: List[str] = None
    
    def __post_init__(self):
        if self.section_dependencies is None:
            self.section_dependencies = []


def parse_active_todos(content: str) -> List[TodoSection]:
    """
    Parse ACTIVE_TODOS.md content into structured TodoSection objects
    
    Args:
        content: Raw markdown content from ACTIVE_TODOS.md
        
    Returns:
        List of TodoSection objects with parsed todos
    """
    if not content.strip():
        return []
    
    sections = []
    current_section = None
    current_todo = None
    
    lines = content.split('\n')
    
    for line in lines:
        line = line.rstrip()
        
        # Parse section headers: ## Priority Level - Description (Dependencies: ...)
        section_match = re.match(r'^## (.+?)(?:\s*\(Dependencies:\s*(.+?)\))?$', line)
        if section_match:
            # Save previous section if exists
            if current_section:
                sections.append(current_section)
            
            section_title = section_match.group(1).strip()
            dependencies_str = section_match.group(2)
            
            # Extract priority from title
            priority = "medium"  # default
            if "high priority" in section_title.lower():
                priority = "high"
            elif "low priority" in section_title.lower():
                priority = "low"
            elif "medium priority" in section_title.lower():
                priority = "medium"
            
            # Parse dependencies
            section_deps = []
            if dependencies_str and dependencies_str.strip().lower() != "none":
                section_deps = [dep.strip() for dep in dependencies_str.split(',')]
            
            current_section = TodoSection(
                title=section_title,
                priority=priority, 
                todos=[],
                section_dependencies=section_deps
            )
            current_todo = None
            continue
        
        # Parse main todo items: - [ ] **PRP-XXX**: Task Description (Est: X-Y hours)
        todo_match = re.match(r'^- \[ \] \*\*([^*]+)\*\*:\s*(.+?)(?:\s*\(Est:\s*(.+?)\))?$', line)
        if todo_match and current_section:
            # Save previous todo if exists
            if current_todo:
                current_section.todos.append(current_todo)
            
            prp_id = todo_match.group(1).strip()
            task_desc = todo_match.group(2).strip()
            estimate = todo_match.group(3) if todo_match.group(3) else "1-2 hours"
            
            current_todo = TodoItem(
                task=task_desc,
                priority=current_section.priority,
                estimate=estimate
            )
            continue
        
        # Parse subtasks: - [ ] Subtask description
        if line.strip().startswith('- [ ]') and current_todo and not todo_match:
            subtask = line.strip()[5:].strip()  # Remove '- [ ] '
            current_todo.subtasks.append(subtask)
            continue
        
        # Parse metadata lines
        if current_todo and line.strip():
            # Status: Not Started/In Progress/Completed
            status_match = re.match(r'^\s*-\s*Status:\s*(.+)$', line)
            if status_match:
                current_todo.status = status_match.group(1).strip()
                continue
            
            # Dependencies: PRP-001, PRP-002 or None
            deps_match = re.match(r'^\s*-\s*Dependencies:\s*(.+)$', line)
            if deps_match:
                deps_str = deps_match.group(1).strip()
                if deps_str.lower() != "none":
                    current_todo.dependencies = [dep.strip() for dep in deps_str.split(',')]
                continue
            
            # PRP: `PRPs/XXX-description.md`
            prp_match = re.match(r'^\s*-\s*PRP:\s*`?([^`\s]+)`?$', line)
            if prp_match:
                current_todo.prp = prp_match.group(1).strip()
                continue
    
    # Save final todo and section
    if current_todo and current_section:
        current_section.todos.append(current_todo)
    if current_section:
        sections.append(current_section)
    
    return sections


def generate_todo_section(section: TodoSection) -> str:
    """
    Generate formatted todo section in ACTIVE_TODOS.md format
    
    Args:
        section: TodoSection object to format
        
    Returns:
        Formatted markdown string
    """
    # Format dependencies
    deps_str = "None"
    if section.section_dependencies:
        deps_str = ", ".join(section.section_dependencies)
    
    # Section header
    output = [f"## {section.title} (Dependencies: {deps_str})"]
    
    # Generate each todo
    for i, todo in enumerate(section.todos, 1):
        prp_id = f"PRP-{i:03d}"
        todo_line = f"- [ ] **{prp_id}**: {todo.task} (Est: {todo.estimate})"
        output.append(todo_line)
        
        # Add subtasks
        for subtask in todo.subtasks:
            output.append(f"  - [ ] {subtask}")
        
        # Add metadata
        output.append(f"  - Status: {todo.status}")
        
        # Add dependencies
        if todo.dependencies:
            deps = ", ".join(todo.dependencies)
            output.append(f"  - Dependencies: {deps}")
        else:
            output.append("  - Dependencies: None")
        
        # Add PRP reference if provided
        if todo.prp:
            output.append(f"  - PRP: `{todo.prp}`")
        
        # Add empty line between todos
        if i < len(section.todos):
            output.append("")
    
    return "\n".join(output)


def validate_todo_format(todo_content: str) -> bool:
    """
    Validate todo content follows ACTIVE_TODOS.md format requirements
    
    Args:
        todo_content: Raw todo content to validate
        
    Returns:
        True if format is valid, False otherwise
    """
    if not todo_content.strip():
        return True  # Empty content is valid
    
    try:
        sections = parse_active_todos(todo_content)
        
        # Basic validation rules
        for section in sections:
            # Check section has valid priority
            if section.priority not in ['high', 'medium', 'low']:
                return False
            
            # Check todos have required fields
            for todo in section.todos:
                if not todo.task or not todo.estimate:
                    return False
                
                # Validate estimate format
                if not re.search(r'\d+(?:-\d+)?\s*hours?', todo.estimate, re.IGNORECASE):
                    return False
                
                # Validate status
                if todo.status not in ['Not Started', 'In Progress', 'Completed']:
                    return False
        
        return True
        
    except Exception:
        return False


def load_active_todos(file_path: str = "ACTIVE_TODOS.md") -> List[TodoSection]:
    """
    Load and parse ACTIVE_TODOS.md file
    
    Args:
        file_path: Path to ACTIVE_TODOS.md file
        
    Returns:
        List of parsed TodoSection objects
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return parse_active_todos(content)
    except FileNotFoundError:
        return []


def save_active_todos(sections: List[TodoSection], file_path: str = "ACTIVE_TODOS.md") -> None:
    """
    Save TodoSection objects to ACTIVE_TODOS.md file
    
    Args:
        sections: List of TodoSection objects to save
        file_path: Path to save ACTIVE_TODOS.md file
    """
    output_lines = ["# Active Development Todos", ""]
    
    for section in sections:
        output_lines.append(generate_todo_section(section))
        output_lines.append("")  # Empty line between sections
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(output_lines))