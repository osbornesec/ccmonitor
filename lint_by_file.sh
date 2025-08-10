#!/bin/bash

# Comprehensive Python Linting Analysis Script
# Organizes all linting issues by file with detailed reporting

set -euo pipefail

# Colors for output (disabled when piping)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    CYAN=''
    BOLD=''
    NC=''
fi

# Configuration
OUTPUT_DIR="lint_report"
BY_FILE_DIR="${OUTPUT_DIR}/by_file"
BY_SEVERITY_DIR="${OUTPUT_DIR}/by_severity"
BY_ERROR_CODE_DIR="${OUTPUT_DIR}/by_error_code"
BY_CATEGORY_DIR="${OUTPUT_DIR}/by_category"
BY_FIX_DIFFICULTY_DIR="${OUTPUT_DIR}/by_fix_difficulty"
BY_PRIORITY_DIR="${OUTPUT_DIR}/by_priority"
RAW_RUFF_OUTPUT="${OUTPUT_DIR}/raw_ruff_output.txt"
RAW_MYPY_OUTPUT="${OUTPUT_DIR}/raw_mypy_output.txt"
JSON_RUFF_OUTPUT="${OUTPUT_DIR}/ruff_output.json"
SUMMARY_FILE="${OUTPUT_DIR}/summary.txt"
STATS_FILE="${OUTPUT_DIR}/statistics.txt"

# Clean up old lint report directory
if [ -d "${OUTPUT_DIR}" ]; then
    echo -e "${YELLOW}Cleaning up previous lint report directory...${NC}"
    rm -rf "${OUTPUT_DIR}"
fi

# Create output directories
mkdir -p "${BY_FILE_DIR}"
mkdir -p "${BY_SEVERITY_DIR}"
mkdir -p "${BY_ERROR_CODE_DIR}"
mkdir -p "${BY_CATEGORY_DIR}"
mkdir -p "${BY_FIX_DIFFICULTY_DIR}"
mkdir -p "${BY_PRIORITY_DIR}"

echo -e "${BOLD}${BLUE}=== Python Linting Analysis Tool ===${NC}"
echo -e "${CYAN}Output directory: ${OUTPUT_DIR}${NC}"
echo ""

# Step 1: Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: uv not found${NC}"
    exit 1
fi

# Step 2: Run ruff linting
echo -e "${YELLOW}Running ruff linting with strict rules...${NC}"
echo "This may take a while..."

# Using set +e to continue despite exit codes
set +e

# Run ruff with full output
uv run ruff check src/ --output-format=full 2>&1 | tee "${RAW_RUFF_OUTPUT}"
RUFF_EXIT_CODE=$?

# Also get JSON output for better parsing
uv run ruff check src/ --output-format=json 2>&1 > "${JSON_RUFF_OUTPUT}"

echo "Ruff exit code: ${RUFF_EXIT_CODE} (continuing regardless)"

# Step 3: Run mypy type checking
echo -e "${YELLOW}Running mypy type checking...${NC}"
uv run mypy src/ 2>&1 | tee "${RAW_MYPY_OUTPUT}"
MYPY_EXIT_CODE=$?

echo "MyPy exit code: ${MYPY_EXIT_CODE} (continuing regardless)"

set -e

echo -e "${GREEN}Linting analysis complete${NC}"
echo ""

# Step 4: Parse and organize issues by file
echo -e "${YELLOW}Parsing issues by file...${NC}"

# Create a Python script for parsing (more reliable than bash for complex parsing)
cat << 'EOF' > "${OUTPUT_DIR}/parse_python_lints.py"
#!/usr/bin/env python3
import json
import re
import sys
import os
from collections import defaultdict, Counter
from pathlib import Path
from datetime import datetime

# Python lint categories and their priority levels
LINT_CATEGORIES = {
    # Security - highest priority
    'S': {'priority': 1, 'category': 'security', 'description': 'Security vulnerabilities'},
    
    # Errors/Bugs - highest priority
    'E': {'priority': 1, 'category': 'errors', 'description': 'Syntax errors and bugs'},
    'F': {'priority': 1, 'category': 'errors', 'description': 'Pyflakes errors'},
    
    # Performance - high priority
    'PERF': {'priority': 2, 'category': 'performance', 'description': 'Performance issues'},
    'FURB': {'priority': 2, 'category': 'performance', 'description': 'Refurb performance lints'},
    
    # Import issues - medium-high priority
    'I': {'priority': 3, 'category': 'imports', 'description': 'Import sorting and organization'},
    'TID': {'priority': 3, 'category': 'imports', 'description': 'Tidy imports'},
    
    # Code quality - medium priority
    'C90': {'priority': 4, 'category': 'complexity', 'description': 'McCabe complexity'},
    'N': {'priority': 4, 'category': 'naming', 'description': 'PEP 8 naming conventions'},
    'A': {'priority': 4, 'category': 'quality', 'description': 'Flake8-builtins'},
    'B': {'priority': 4, 'category': 'quality', 'description': 'Flake8-bugbear'},
    'C4': {'priority': 4, 'category': 'quality', 'description': 'Flake8-comprehensions'},
    'PYI': {'priority': 4, 'category': 'quality', 'description': 'Flake8-pyi'},
    'RET': {'priority': 4, 'category': 'quality', 'description': 'Flake8-return'},
    'SIM': {'priority': 4, 'category': 'quality', 'description': 'Flake8-simplify'},
    
    # Documentation - medium priority
    'D': {'priority': 5, 'category': 'documentation', 'description': 'Pydocstyle documentation'},
    
    # Style - lower priority
    'W': {'priority': 6, 'category': 'style', 'description': 'PEP 8 style warnings'},
    'UP': {'priority': 6, 'category': 'style', 'description': 'Pyupgrade modern Python'},
    'Q': {'priority': 6, 'category': 'style', 'description': 'Flake8-quotes'},
    'COM': {'priority': 6, 'category': 'style', 'description': 'Flake8-commas'},
    'T20': {'priority': 6, 'category': 'style', 'description': 'Flake8-print'},
    'PIE': {'priority': 6, 'category': 'style', 'description': 'Flake8-pie'},
    'T10': {'priority': 6, 'category': 'style', 'description': 'Flake8-debugger'},
    'PT': {'priority': 6, 'category': 'style', 'description': 'Flake8-pytest-style'},
    'RSE': {'priority': 6, 'category': 'style', 'description': 'Flake8-raise'},
    'TCH': {'priority': 6, 'category': 'style', 'description': 'Flake8-type-checking'},
    'ARG': {'priority': 6, 'category': 'style', 'description': 'Flake8-unused-arguments'},
    'PTH': {'priority': 6, 'category': 'style', 'description': 'Flake8-use-pathlib'},
    'ERA': {'priority': 6, 'category': 'style', 'description': 'Eradicate commented code'},
    'PD': {'priority': 6, 'category': 'style', 'description': 'Pandas-vet'},
    'PGH': {'priority': 6, 'category': 'style', 'description': 'Pygrep-hooks'},
    'PLC': {'priority': 6, 'category': 'style', 'description': 'Pylint convention'},
    'PLE': {'priority': 6, 'category': 'style', 'description': 'Pylint error'},
    'PLR': {'priority': 6, 'category': 'style', 'description': 'Pylint refactor'},
    'PLW': {'priority': 6, 'category': 'style', 'description': 'Pylint warning'},
    'FLY': {'priority': 6, 'category': 'style', 'description': 'Flynt f-string'},
    'NPY': {'priority': 6, 'category': 'style', 'description': 'NumPy-specific'},
    'RUF': {'priority': 6, 'category': 'style', 'description': 'Ruff-specific'},
    
    # Default for unknown
    'unknown': {'priority': 7, 'category': 'unknown', 'description': 'Uncategorized lint'}
}

# Auto-fixable lint prefixes (ruff can fix these automatically)
AUTO_FIXABLE_LINTS = {
    'I001', 'I002',  # Import sorting
    'UP',  # Pyupgrade
    'Q000', 'Q001', 'Q002', 'Q003',  # Quotes
    'COM812', 'COM819',  # Commas  
    'W291', 'W292', 'W293',  # Whitespace
    'E111', 'E114', 'E117', 'E121', 'E122', 'E123', 'E124', 'E125', 'E126', 'E127', 'E128', 'E129', 'E131',  # Indentation
    'E201', 'E202', 'E203', 'E211', 'E221', 'E222', 'E223', 'E224', 'E225', 'E226', 'E227', 'E228',  # Spacing
    'E231', 'E241', 'E242', 'E251', 'E261', 'E262', 'E265', 'E266', 'E271', 'E272', 'E273', 'E274', 'E275',  # Spacing/Comments
    'RUF005',  # Collection literal
    'SIM108',  # Ternary operator
    'PIE790', 'PIE794', 'PIE796', 'PIE800', 'PIE804', 'PIE807', 'PIE810',  # Pie
    'T201', 'T203',  # Print statements
    'F401', 'F841',  # Unused imports/variables
}

def get_lint_info(lint_code):
    """Get category, priority, and fix difficulty for a lint code"""
    # Extract the main category from the lint code
    for category_prefix, info in LINT_CATEGORIES.items():
        if lint_code.startswith(category_prefix):
            break
    else:
        info = LINT_CATEGORIES['unknown']
    
    # Check if it's auto-fixable
    is_auto_fixable = any(lint_code.startswith(prefix) or lint_code == prefix 
                         for prefix in AUTO_FIXABLE_LINTS)
    fix_difficulty = 'auto' if is_auto_fixable else 'manual'
    
    return {
        'category': info['category'],
        'priority': info['priority'],
        'fix_difficulty': fix_difficulty,
        'description': info['description']
    }

def parse_ruff_json(json_file):
    """Parse ruff JSON output"""
    by_file = defaultdict(list)
    issue_types = defaultdict(int)
    by_error_code = defaultdict(list)
    by_category = defaultdict(list)
    by_fix_difficulty = defaultdict(list)
    by_priority = defaultdict(list)
    
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
            
            for issue in data:
                file_name = issue.get('filename', 'unknown')
                code = issue.get('code', 'unknown')
                message = issue.get('message', '')
                line = issue.get('location', {}).get('row', 0)
                column = issue.get('location', {}).get('column', 0)
                
                issue_info = {
                    'file': file_name,
                    'level': 'error' if issue.get('noqa', False) else 'warning',
                    'code': code,
                    'message': message,
                    'line': line,
                    'column': column,
                    'url': issue.get('url', '')
                }
                
                by_file[file_name].append(issue_info)
                issue_types[code] += 1
                
                # Get lint categorization
                lint_info = get_lint_info(code)
                issue_info.update(lint_info)
                
                # Organize by various criteria
                by_error_code[code].append(issue_info)
                by_category[lint_info['category']].append(issue_info)
                by_fix_difficulty[lint_info['fix_difficulty']].append(issue_info)
                by_priority[lint_info['priority']].append(issue_info)
                
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    return by_file, issue_types, by_error_code, by_category, by_fix_difficulty, by_priority

def parse_ruff_text(text_file):
    """Parse ruff text output and organize by file"""
    by_file = defaultdict(list)
    by_severity = defaultdict(list)
    issue_count = defaultdict(lambda: defaultdict(int))
    
    try:
        with open(text_file, 'r') as f:
            for line in f:
                # Match ruff output format: file:line:column: code message
                match = re.match(r'^([^:]+):(\d+):(\d+):\s+(\w+)\s+(.+)$', line.strip())
                if match:
                    file_path, line_num, col_num, code, message = match.groups()
                    
                    issue_text = f"{code}: {message} (line {line_num}, col {col_num})"
                    by_file[file_path].append(issue_text)
                    by_severity['warnings'].append(f"File: {file_path}\n{issue_text}")
                    issue_count[file_path]['warnings'] += 1
    except FileNotFoundError:
        pass
    
    return by_file, by_severity, issue_count

def parse_mypy_output(mypy_file):
    """Parse mypy output and organize by file"""
    by_file = defaultdict(list)
    by_severity = defaultdict(list) 
    issue_count = defaultdict(lambda: defaultdict(int))
    
    try:
        with open(mypy_file, 'r') as f:
            for line in f:
                # Match mypy output format: file:line: error: message
                match = re.match(r'^([^:]+):(\d+):\s+(error|warning|note):\s+(.+)$', line.strip())
                if match:
                    file_path, line_num, severity, message = match.groups()
                    
                    issue_text = f"mypy {severity}: {message} (line {line_num})"
                    by_file[file_path].append(issue_text)
                    by_severity[f'mypy_{severity}s'].append(f"File: {file_path}\n{issue_text}")
                    issue_count[file_path][f'mypy_{severity}s'] += 1
    except FileNotFoundError:
        pass
    
    return by_file, by_severity, issue_count

def write_error_code_reports(by_error_code, output_dir):
    """Write reports organized by error code"""
    error_code_dir = output_dir / "by_error_code"
    
    # Sort by frequency
    sorted_codes = sorted(by_error_code.items(), key=lambda x: len(x[1]), reverse=True)
    
    for error_code, issues in sorted_codes:
        safe_filename = error_code.replace(':', '_').replace('::', '_')
        output_file = error_code_dir / f"{safe_filename}.txt"
        
        lint_info = get_lint_info(error_code)
        
        with open(output_file, 'w') as f:
            f.write(f"=== {error_code} ===\n")
            f.write(f"Category: {lint_info['category']}\n")
            f.write(f"Priority: {lint_info['priority']}\n")
            f.write(f"Fix Difficulty: {lint_info['fix_difficulty']}\n")
            f.write(f"Description: {lint_info['description']}\n")
            f.write(f"Total occurrences: {len(issues)}\n")
            if issues and issues[0].get('url'):
                f.write(f"Documentation: {issues[0]['url']}\n")
            f.write("=" * 60 + "\n\n")
            
            # Group by file
            by_file = defaultdict(list)
            for issue in issues:
                by_file[issue['file']].append(issue)
            
            for file_path, file_issues in sorted(by_file.items()):
                f.write(f"File: {file_path} ({len(file_issues)} occurrences)\n")
                f.write("-" * 50 + "\n")
                for issue in file_issues:
                    f.write(f"  Line {issue['line']}: {issue['message']}\n")
                f.write("\n")

def write_category_reports(by_category, output_dir):
    """Write reports organized by lint category"""
    category_dir = output_dir / "by_category"
    
    # Sort by priority (security first, then by issue count)
    priority_order = ['security', 'errors', 'performance', 'imports', 'complexity', 
                     'naming', 'quality', 'documentation', 'style', 'unknown']
    sorted_categories = []
    for category in priority_order:
        if category in by_category:
            sorted_categories.append((category, by_category[category]))
    
    for category, issues in sorted_categories:
        output_file = category_dir / f"{category}.txt"
        
        with open(output_file, 'w') as f:
            f.write(f"=== {category.upper()} LINTS ===\n")
            f.write(f"Total issues: {len(issues)}\n\n")
            
            # Group by error code within category
            by_code = defaultdict(list)
            for issue in issues:
                by_code[issue['code']].append(issue)
            
            sorted_codes = sorted(by_code.items(), key=lambda x: len(x[1]), reverse=True)
            
            for code, code_issues in sorted_codes:
                lint_info = get_lint_info(code)
                f.write(f"{code} ({len(code_issues)} occurrences)\n")
                f.write(f"  Priority: {lint_info['priority']}\n")
                f.write(f"  Fix: {lint_info['fix_difficulty']}\n")
                f.write(f"  Description: {lint_info['description']}\n")
                if code_issues and code_issues[0].get('url'):
                    f.write(f"  URL: {code_issues[0]['url']}\n")
                
                # Show top files affected
                file_counts = Counter(issue['file'] for issue in code_issues)
                top_files = file_counts.most_common(5)
                f.write(f"  Top affected files:\n")
                for file_path, count in top_files:
                    f.write(f"    {file_path}: {count}\n")
                f.write("\n")

def write_priority_reports(by_priority, output_dir):
    """Write reports organized by priority"""
    priority_dir = output_dir / "by_priority"
    
    priority_names = {
        1: 'critical_security_errors',
        2: 'high_performance',
        3: 'medium_imports',
        4: 'medium_quality',
        5: 'medium_documentation',
        6: 'low_style',
        7: 'unknown'
    }
    
    for priority_level, issues in sorted(by_priority.items()):
        priority_name = priority_names.get(priority_level, f'priority_{priority_level}')
        output_file = priority_dir / f"{priority_name}.txt"
        
        with open(output_file, 'w') as f:
            f.write(f"=== PRIORITY {priority_level} ({priority_name.upper()}) ===\n")
            f.write(f"Total issues: {len(issues)}\n\n")
            
            # Group by category within priority
            by_category = defaultdict(list)
            for issue in issues:
                by_category[issue['category']].append(issue)
            
            for category, cat_issues in sorted(by_category.items()):
                f.write(f"{category.upper()}: {len(cat_issues)} issues\n")
                
                # Show top error codes in this category
                code_counts = Counter(issue['code'] for issue in cat_issues)
                top_codes = code_counts.most_common(10)
                for code, count in top_codes:
                    f.write(f"  {code}: {count}\n")
                f.write("\n")

def write_fix_difficulty_reports(by_fix_difficulty, output_dir):
    """Write reports organized by fix difficulty"""
    difficulty_dir = output_dir / "by_fix_difficulty"
    
    for difficulty, issues in sorted(by_fix_difficulty.items()):
        output_file = difficulty_dir / f"{difficulty}.txt"
        
        with open(output_file, 'w') as f:
            f.write(f"=== {difficulty.upper()} FIXES ===\n")
            f.write(f"Total issues: {len(issues)}\n")
            
            if difficulty == 'auto':
                f.write("\nThese can be fixed automatically with 'uv run ruff check --fix src/'\n")
            else:
                f.write("\nThese require manual intervention\n")
            
            f.write("=" * 60 + "\n\n")
            
            # Group by error code
            by_code = defaultdict(list)
            for issue in issues:
                by_code[issue['code']].append(issue)
            
            sorted_codes = sorted(by_code.items(), key=lambda x: len(x[1]), reverse=True)
            
            for code, code_issues in sorted_codes:
                lint_info = get_lint_info(code)
                f.write(f"{code} ({len(code_issues)} occurrences)\n")
                f.write(f"  Category: {lint_info['category']}\n")
                f.write(f"  Priority: {lint_info['priority']}\n")
                f.write(f"  Description: {lint_info['description']}\n")
                
                # Show distribution across files
                file_counts = Counter(issue['file'] for issue in code_issues)
                f.write(f"  Files affected: {len(file_counts)}\n")
                if len(file_counts) <= 5:
                    for file_path, count in file_counts.most_common():
                        f.write(f"    {file_path}: {count}\n")
                else:
                    for file_path, count in file_counts.most_common(3):
                        f.write(f"    {file_path}: {count}\n")
                    f.write(f"    ... and {len(file_counts) - 3} more files\n")
                f.write("\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: parse_python_lints.py <output_dir>")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    ruff_text_file = output_dir / "raw_ruff_output.txt"
    ruff_json_file = output_dir / "ruff_output.json"
    mypy_file = output_dir / "raw_mypy_output.txt"
    by_file_dir = output_dir / "by_file"
    by_severity_dir = output_dir / "by_severity"
    
    print("Parsing Python linting output...")
    
    # Parse ruff text output
    ruff_by_file, ruff_by_severity, ruff_issue_count = parse_ruff_text(ruff_text_file)
    
    # Parse ruff JSON output for detailed analysis
    json_by_file, issue_types, by_error_code, by_category, by_fix_difficulty, by_priority = parse_ruff_json(ruff_json_file)
    
    # Parse mypy output
    mypy_by_file, mypy_by_severity, mypy_issue_count = parse_mypy_output(mypy_file)
    
    # Merge all results
    all_by_file = defaultdict(list)
    all_by_severity = defaultdict(list)
    all_issue_count = defaultdict(lambda: defaultdict(int))
    
    # Merge ruff results
    for file_path, issues in ruff_by_file.items():
        all_by_file[file_path].extend(issues)
        for severity, count in ruff_issue_count[file_path].items():
            all_issue_count[file_path][severity] += count
    
    for severity, issues in ruff_by_severity.items():
        all_by_severity[severity].extend(issues)
    
    # Merge mypy results
    for file_path, issues in mypy_by_file.items():
        all_by_file[file_path].extend(issues)
        for severity, count in mypy_issue_count[file_path].items():
            all_issue_count[file_path][severity] += count
    
    for severity, issues in mypy_by_severity.items():
        all_by_severity[severity].extend(issues)
    
    print(f"Found {len(issue_types)} different error codes in {len(all_by_file)} files")
    
    # Write individual file reports
    for file_path, issues in all_by_file.items():
        safe_filename = file_path.replace('/', '_').replace('\\', '_')
        output_file = by_file_dir / f"{safe_filename}.txt"
        
        with open(output_file, 'w') as f:
            f.write(f"=== Linting Issues for {file_path} ===\n")
            f.write(f"Total issues: {len(issues)}\n")
            
            # Count different issue types for this file
            counts = all_issue_count[file_path]
            for issue_type, count in counts.items():
                f.write(f"{issue_type}: {count}\n")
            
            f.write("=" * 60 + "\n\n")
            
            for i, issue in enumerate(issues, 1):
                f.write(f"{i}. {issue}\n")
                f.write("-" * 40 + "\n")
    
    # Write severity-based reports
    for severity, issues in all_by_severity.items():
        output_file = by_severity_dir / f"{severity}.txt"
        with open(output_file, 'w') as f:
            f.write(f"=== All {severity.upper().replace('_', ' ')} ===\n")
            f.write(f"Total: {len(issues)}\n")
            f.write("=" * 60 + "\n\n")
            
            for issue in issues:
                f.write(issue)
                f.write("\n" + "=" * 60 + "\n\n")
    
    # Write new organizational reports (only if we have JSON data)
    if issue_types:
        print("Writing error code reports...")
        write_error_code_reports(by_error_code, output_dir)
        
        print("Writing category reports...")
        write_category_reports(by_category, output_dir)
        
        print("Writing priority reports...")
        write_priority_reports(by_priority, output_dir)
        
        print("Writing fix difficulty reports...")
        write_fix_difficulty_reports(by_fix_difficulty, output_dir)
    
    
    # Generate enhanced summary
    summary_file = output_dir / "summary.txt"
    with open(summary_file, 'w') as f:
        f.write("=== COMPREHENSIVE PYTHON LINTING SUMMARY ===\n\n")
        
        # Basic statistics
        sorted_files = sorted(all_issue_count.items(), 
                            key=lambda x: sum(x[1].values()), 
                            reverse=True)
        
        total_ruff_warnings = sum(counts.get('warnings', 0) for _, counts in sorted_files)
        total_mypy_errors = sum(counts.get('mypy_errors', 0) for _, counts in sorted_files)
        total_mypy_warnings = sum(counts.get('mypy_warnings', 0) for _, counts in sorted_files)
        total_issues = total_ruff_warnings + total_mypy_errors + total_mypy_warnings
        
        f.write("OVERVIEW:\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total files analyzed: {len(sorted_files)}\n")
        f.write(f"Total issues: {total_issues}\n")
        f.write(f"  - Ruff warnings: {total_ruff_warnings}\n")
        f.write(f"  - MyPy errors: {total_mypy_errors}\n")
        f.write(f"  - MyPy warnings: {total_mypy_warnings}\n\n")
        
        # Priority breakdown (if available)
        if by_priority:
            f.write("PRIORITY BREAKDOWN:\n")
            f.write("-" * 40 + "\n")
            priority_names = {
                1: 'Critical (Security/Errors)',
                2: 'High (Performance)', 
                3: 'Medium (Imports)',
                4: 'Medium (Quality)',
                5: 'Medium (Documentation)',
                6: 'Low (Style)',
                7: 'Unknown'
            }
            for priority in sorted(by_priority.keys()):
                count = len(by_priority[priority])
                name = priority_names.get(priority, f'Priority {priority}')
                f.write(f"  {name}: {count}\n")
            f.write("\n")
        
        # Fix difficulty breakdown (if available)
        if by_fix_difficulty:
            f.write("FIX DIFFICULTY:\n")
            f.write("-" * 40 + "\n")
            for difficulty in sorted(by_fix_difficulty.keys()):
                count = len(by_fix_difficulty[difficulty])
                f.write(f"  {difficulty.capitalize()} fixes: {count}\n")
            f.write("\n")
        
        # Top error codes (if available)
        if issue_types:
            f.write("TOP 15 ERROR CODES:\n")
            f.write("-" * 40 + "\n")
            sorted_types = sorted(issue_types.items(), key=lambda x: x[1], reverse=True)[:15]
            for error_code, count in sorted_types:
                lint_info = get_lint_info(error_code)
                f.write(f"  {error_code:<35} {count:>5} ({lint_info['category']})\n")
            f.write("\n")
        
        # Files needing most attention
        f.write("FILES NEEDING ATTENTION:\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'File':<50} {'Ruff':>8} {'MyPy Err':>10} {'MyPy Warn':>10} {'Total':>8}\n")
        f.write("-" * 80 + "\n")
        
        for file_path, counts in sorted_files[:15]:
            ruff_warns = counts.get('warnings', 0)
            mypy_errs = counts.get('mypy_errors', 0)
            mypy_warns = counts.get('mypy_warnings', 0)
            total = ruff_warns + mypy_errs + mypy_warns
            
            # Truncate long file paths
            display_path = file_path if len(file_path) <= 50 else "..." + file_path[-47:]
            f.write(f"{display_path:<50} {ruff_warns:>8} {mypy_errs:>10} {mypy_warns:>10} {total:>8}\n")
    
    # Generate enhanced statistics
    stats_file = output_dir / "statistics.txt"
    with open(stats_file, 'w') as f:
        f.write("=== COMPREHENSIVE PYTHON LINTING STATISTICS ===\n\n")
        f.write(f"Total files with issues: {len(all_issue_count)}\n")
        f.write(f"Total ruff warnings: {total_ruff_warnings}\n")
        f.write(f"Total mypy errors: {total_mypy_errors}\n")
        f.write(f"Total mypy warnings: {total_mypy_warnings}\n")
        f.write(f"Total issues: {total_issues}\n")
        f.write(f"Unique error codes: {len(issue_types)}\n\n")
        
        if all_issue_count:
            avg_issues = total_issues / len(all_issue_count)
            f.write(f"Average issues per file: {avg_issues:.2f}\n\n")
    
    print("✅ All reports generated successfully!")

if __name__ == "__main__":
    main()
EOF

# Make Python script executable
chmod +x "${OUTPUT_DIR}/parse_python_lints.py"

# Run the Python parser
if command -v python3 &> /dev/null; then
    python3 "${OUTPUT_DIR}/parse_python_lints.py" "${OUTPUT_DIR}"
    echo -e "${GREEN}Issue parsing complete${NC}"
else
    echo -e "${YELLOW}Warning: Python 3 not found. Skipping detailed parsing.${NC}"
fi

# Step 5: Run additional checks
echo ""
echo -e "${YELLOW}Running additional checks...${NC}"

# Format check
echo "Checking formatting..." 
uv run ruff format --check src/ 2>&1 > "${OUTPUT_DIR}/format_check.txt" || echo "Formatting issues found (see format_check.txt)"

# Import sorting check
echo "Checking import sorting..."
uv run ruff check --select I src/ 2>&1 > "${OUTPUT_DIR}/import_check.txt" || echo "Import sorting issues found (see import_check.txt)"

# Build/install check
echo "Checking package installation..."
uv pip check 2>&1 > "${OUTPUT_DIR}/pip_check.txt" || echo "Package dependency issues found (see pip_check.txt)"

# Step 6: Display summary
echo ""
echo -e "${BOLD}${GREEN}=== Analysis Complete ===${NC}"
echo ""

if [ -f "${SUMMARY_FILE}" ]; then
    echo -e "${CYAN}Summary:${NC}"
    head -n 25 "${SUMMARY_FILE}"
    echo ""
    echo -e "${YELLOW}Full summary available at: ${SUMMARY_FILE}${NC}"
fi

if [ -f "${STATS_FILE}" ]; then
    echo ""
    echo -e "${CYAN}Statistics:${NC}"
    cat "${STATS_FILE}"
fi

echo ""
echo -e "${BOLD}${BLUE}Output files created:${NC}"
echo "  - Ruff report: ${RAW_RUFF_OUTPUT}"
echo "  - MyPy report: ${RAW_MYPY_OUTPUT}"
echo "  - JSON data: ${JSON_RUFF_OUTPUT}"
echo "  - Summary: ${SUMMARY_FILE}"
echo "  - Statistics: ${STATS_FILE}"
echo "  - By file: ${BY_FILE_DIR}/"
echo "  - By severity: ${BY_SEVERITY_DIR}/"
echo "  - By error code: ${BY_ERROR_CODE_DIR}/"
echo "  - By category: ${BY_CATEGORY_DIR}/"
echo "  - By fix difficulty: ${BY_FIX_DIFFICULTY_DIR}/"
echo "  - By priority: ${BY_PRIORITY_DIR}/"
echo ""
echo -e "${GREEN}Reports saved to: ${OUTPUT_DIR}/${NC}"
echo ""
echo -e "${BOLD}${CYAN}New organizational features:${NC}"
echo "  📊 Error code separation: Individual files for each ruff/mypy rule"
echo "  🎯 Category separation: Security, errors, performance, imports, quality, style"
echo "  🔧 Fix difficulty: Auto-fixable vs manual intervention required"
echo "  ⚡ Priority levels: Critical to low priority systematic fixing order"
echo "  📈 Progress tracking: Compare with previous runs to measure improvement"
echo ""
echo -e "${BOLD}${YELLOW}Quick fix commands:${NC}"
echo "  Auto-fix issues: ${GREEN}uv run ruff check --fix src/${NC}"
echo "  Format code: ${GREEN}uv run ruff format src/${NC}"
echo "  Type check: ${GREEN}uv run mypy src/${NC}"