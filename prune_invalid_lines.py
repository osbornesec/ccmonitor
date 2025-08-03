#!/usr/bin/env python3
"""
Invalid Line Pruning Tool
Removes malformed JSON lines from JSONL files to maximize pruning effectiveness.
"""

import json
import argparse
from pathlib import Path
from typing import List, Tuple


def analyze_and_clean_jsonl(input_file: Path, output_file: Path = None) -> dict:
    """
    Analyze and clean JSONL file by removing invalid entries
    
    Returns:
        Statistics about cleaning operation
    """
    if output_file is None:
        output_file = input_file
    
    valid_lines = []
    invalid_lines = []
    total_lines = 0
    
    required_fields = {"uuid", "type", "message"}
    
    # Read and analyze
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            total_lines += 1
            line = line.strip()
            if not line:
                continue
                
            try:
                entry = json.loads(line)
                
                # Check if it has required conversation fields
                if isinstance(entry, dict) and all(field in entry for field in required_fields):
                    valid_lines.append(line)
                else:
                    invalid_lines.append((line_num, line, "missing_required_fields"))
                    
            except json.JSONDecodeError as e:
                invalid_lines.append((line_num, line, f"json_error: {e}"))
    
    # Write cleaned file
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in valid_lines:
            f.write(line + '\n')
    
    # Calculate stats
    original_size = input_file.stat().st_size
    new_size = output_file.stat().st_size
    size_reduction = original_size - new_size
    reduction_pct = (size_reduction / original_size) * 100 if original_size > 0 else 0
    
    return {
        'total_lines': total_lines,
        'valid_lines': len(valid_lines),
        'invalid_lines': len(invalid_lines),
        'invalid_percentage': len(invalid_lines) / total_lines * 100 if total_lines > 0 else 0,
        'original_size': original_size,
        'new_size': new_size,
        'size_reduction': size_reduction,
        'reduction_percentage': reduction_pct,
        'invalid_examples': invalid_lines[:5]  # First 5 examples
    }


def main():
    parser = argparse.ArgumentParser(description='Remove invalid lines from JSONL files')
    parser.add_argument('file', type=Path, help='JSONL file to clean')
    parser.add_argument('--output', '-o', type=Path, help='Output file (default: overwrites input)')
    parser.add_argument('--dry-run', action='store_true', help='Show analysis without making changes')
    
    args = parser.parse_args()
    
    if not args.file.exists():
        print(f"Error: File {args.file} not found")
        return 1
    
    output_file = args.output or args.file
    
    if args.dry_run:
        # Create temp file for dry run
        output_file = Path('/tmp/dry_run_clean.jsonl')
    
    print(f"Analyzing {args.file}...")
    stats = analyze_and_clean_jsonl(args.file, output_file)
    
    print(f"""
📊 Invalid Line Analysis Results:
   Total lines: {stats['total_lines']:,}
   Valid lines: {stats['valid_lines']:,}
   Invalid lines: {stats['invalid_lines']:,} ({stats['invalid_percentage']:.1f}%)
   
💾 Size Impact:
   Original size: {stats['original_size'] / 1024:.1f} KB
   New size: {stats['new_size'] / 1024:.1f} KB
   Reduction: {stats['size_reduction'] / 1024:.1f} KB ({stats['reduction_percentage']:.1f}%)

🔍 Invalid Line Examples:""")
    
    for line_num, content, reason in stats['invalid_examples']:
        preview = content[:100] + "..." if len(content) > 100 else content
        print(f"   Line {line_num}: {reason}")
        print(f"   Content: {preview}")
        print()
    
    if args.dry_run:
        print("🔥 This is a dry run - no files were modified")
        output_file.unlink()  # Clean up temp file
    else:
        print(f"✅ File cleaned and saved to {output_file}")
    
    return 0


if __name__ == "__main__":
    exit(main())