# Claude-Prune CLI User Guide

A comprehensive command-line interface for intelligent JSONL conversation pruning with batch processing, scheduling, and detailed analytics.

## Installation

```bash
# Install from source
uv sync
uv run pip install -e .

# Or install directly
pip install claude-prune
```

## Quick Start

### Basic File Pruning

```bash
# Prune a single file with default settings (medium level)
claude-prune prune --file session.jsonl

# Prune with specific level and backup
claude-prune prune --file session.jsonl --level aggressive --backup

# Dry run to see what would be pruned
claude-prune --dry-run prune --file session.jsonl --stats
```

### Batch Processing

```bash
# Process all JSONL files in a directory
claude-prune batch --directory /projects

# Recursive processing with custom pattern
claude-prune batch --directory /data --recursive --pattern "conversation_*.jsonl"

# Parallel processing with 8 workers
claude-prune batch --directory /large_dataset --parallel 8
```

### Statistics and Analysis

```bash
# Basic statistics
claude-prune stats --file session.jsonl

# Detailed analysis with trends
claude-prune stats --file session.jsonl --trend

# Export report to JSON
claude-prune stats --file session.jsonl --format json --output report.json

# Analyze entire directory
claude-prune stats --directory /projects --recursive
```

## Commands Reference

### Global Options

- `--version`: Show version and exit
- `--verbose, -v`: Enable verbose output
- `--config PATH`: Configuration file path
- `--dry-run`: Show what would be done without making changes

### `prune` - Single File Pruning

Intelligently prune a single JSONL conversation file.

```bash
claude-prune prune [OPTIONS]
```

**Options:**
- `-f, --file PATH`: Input JSONL file to process (required)
- `-o, --output PATH`: Output file path (default: overwrites input)
- `-l, --level [light|medium|aggressive]`: Pruning aggressiveness level
- `--backup/--no-backup`: Create backup before processing (default: enabled)
- `--stats/--no-stats`: Display processing statistics
- `--progress/--no-progress`: Show progress bar

**Pruning Levels:**
- **Light**: Removes only obvious redundancy (20% threshold)
- **Medium**: Balanced pruning (40% threshold) - *default*
- **Aggressive**: Maximum compression (60% threshold)

**Examples:**
```bash
# Basic pruning with backup
claude-prune prune --file session.jsonl

# Aggressive pruning to specific output file
claude-prune prune --file input.jsonl --output pruned.jsonl --level aggressive

# Light pruning with statistics display
claude-prune prune --file data.jsonl --level light --stats
```

### `batch` - Batch Processing

Process multiple JSONL files efficiently with parallel processing.

```bash
claude-prune batch [OPTIONS]
```

**Options:**
- `-d, --directory PATH`: Directory to process (required)
- `-p, --pattern TEXT`: File pattern to match (default: `*.jsonl`)
- `-r, --recursive`: Process directories recursively
- `-l, --level [light|medium|aggressive]`: Pruning level (default: medium)
- `--parallel INT`: Number of parallel workers (default: 4)
- `--resume`: Resume interrupted batch operation
- `--backup/--no-backup`: Create backups before processing

**Examples:**
```bash
# Process all JSONL files in directory
claude-prune batch --directory /projects

# Recursive processing with custom pattern
claude-prune batch --directory /data --recursive --pattern "session_*.jsonl"

# High-performance processing
claude-prune batch --directory /large_dataset --parallel 8 --level light

# Resume interrupted operation
claude-prune batch --directory /projects --resume
```

### `stats` - Statistics and Analysis

Generate detailed statistics and analysis reports.

```bash
claude-prune stats [OPTIONS]
```

**Options:**
- `-f, --file PATH`: JSONL file to analyze
- `-d, --directory PATH`: Directory to analyze
- `-r, --recursive`: Analyze directories recursively
- `--format [table|json|csv|html]`: Output format (default: table)
- `-o, --output PATH`: Output file path
- `--trend`: Include trend analysis

**Examples:**
```bash
# Basic file analysis
claude-prune stats --file session.jsonl

# Directory analysis with trends
claude-prune stats --directory /projects --recursive --trend

# Export HTML report
claude-prune stats --file data.jsonl --format html --output report.html

# CSV export for data analysis
claude-prune stats --directory /data --format csv --output analysis.csv
```

### `schedule` - Automated Scheduling

Configure automatic pruning schedules for regular maintenance.

```bash
claude-prune schedule [OPTIONS]
```

**Options:**
- `--enable/--disable`: Enable or disable automatic scheduling
- `--policy [daily|weekly|monthly]`: Scheduling policy (default: weekly)
- `--level [light|medium|aggressive]`: Default pruning level (default: light)
- `--directories TEXT`: Directories to include (multiple allowed)
- `--show`: Show current scheduling configuration

**Examples:**
```bash
# Enable weekly light pruning
claude-prune schedule --enable --policy weekly --level light

# Add directories to monitor
claude-prune schedule --enable --directories /projects --directories /data

# Show current configuration
claude-prune schedule --show

# Disable scheduling
claude-prune schedule --disable
```

### `config` - Configuration Management

Manage configuration settings and profiles.

```bash
claude-prune config [SUBCOMMAND] [OPTIONS]
```

**Subcommands:**
- `show`: Display current configuration
- `set KEY VALUE`: Set configuration value

**Examples:**
```bash
# Show current configuration
claude-prune config show

# Set default pruning level
claude-prune config set default_level aggressive

# Set default parallel workers
claude-prune config set default_parallel_workers 8
```

## Configuration

### Configuration File

Create a configuration file at one of these locations:
- `./.claude-prune.yaml` (project-specific)
- `~/.claude-prune.yaml` (user-specific)
- `~/.config/claude-prune/config.yaml` (XDG standard)

**Example configuration:**
```yaml
# Core settings
default_level: medium
default_backup: true
default_verbose: false

# Batch processing
default_parallel_workers: 4
default_pattern: "*.jsonl"
default_recursive: false

# Output settings
default_output_format: table
colorize_output: true

# Performance settings
chunk_size: 1000
memory_limit_mb: 512

# Safety settings
require_confirmation: true
max_file_size_mb: 100
backup_retention_days: 30

# Scheduling
schedule_enabled: false
schedule_policy: weekly
schedule_level: light
schedule_directories: []
```

### Environment Variables

Override configuration with environment variables:

```bash
export CLAUDE_PRUNE_LEVEL=aggressive
export CLAUDE_PRUNE_PARALLEL=8
export CLAUDE_PRUNE_VERBOSE=true
export CLAUDE_PRUNE_BACKUP=false
```

## Advanced Usage

### Dry Run Mode

Use `--dry-run` to preview operations without making changes:

```bash
# See what would be pruned
claude-prune --dry-run prune --file session.jsonl --stats

# Preview batch operation
claude-prune --dry-run batch --directory /projects --recursive
```

### Resume Interrupted Operations

Batch operations can be resumed if interrupted:

```bash
# Start batch operation
claude-prune batch --directory /large_dataset

# If interrupted, resume with:
claude-prune batch --directory /large_dataset --resume
```

### Custom Patterns and Filtering

```bash
# Process only specific file patterns
claude-prune batch --directory /data --pattern "conversation_2024*.jsonl"

# Exclude files with size filtering (via configuration)
# Files larger than max_file_size_mb will be skipped
```

### Performance Optimization

```bash
# High-performance batch processing
claude-prune batch \
  --directory /massive_dataset \
  --parallel 16 \
  --level light \
  --no-backup

# Memory-constrained environments
claude-prune batch \
  --directory /data \
  --parallel 2 \
  --level medium
```

## Output Formats

### Table Format (Default)
Human-readable tabular output perfect for terminal viewing.

### JSON Format
Machine-readable structured data for integration with other tools.

### CSV Format
Spreadsheet-compatible format for data analysis.

### HTML Format
Rich formatted reports with styling for sharing and archiving.

## Best Practices

### 1. Start with Light Pruning
Begin with `--level light` to understand the impact before using more aggressive levels.

### 2. Always Use Backups
Keep the default `--backup` enabled, especially for important conversations.

### 3. Test with Dry Run
Use `--dry-run` to preview operations before executing them.

### 4. Monitor Performance
Use `--stats` to track compression ratios and processing performance.

### 5. Batch Processing Strategy
- Use parallel processing for large datasets
- Process files during off-peak hours
- Enable scheduling for regular maintenance

### 6. Regular Analysis
Use the `stats` command regularly to:
- Monitor conversation growth
- Identify compression opportunities
- Track system performance

## Troubleshooting

### Common Issues

**CLI not found after installation:**
```bash
# Ensure the package is installed correctly
pip list | grep claude-prune

# Check if the script is in PATH
which claude-prune
```

**Permission errors:**
```bash
# Ensure write permissions for output directory
chmod 755 /output/directory

# Check file permissions
ls -la session.jsonl
```

**Memory issues with large files:**
```bash
# Reduce parallel workers
claude-prune batch --directory /data --parallel 2

# Process smaller batches
claude-prune batch --directory /data --pattern "session_001*.jsonl"
```

**Configuration not loading:**
```bash
# Check configuration file syntax
claude-prune config show

# Use explicit configuration file
claude-prune --config /path/to/config.yaml prune --file session.jsonl
```

### Performance Tuning

**For Large Datasets:**
- Increase `--parallel` workers (up to CPU count)
- Use `--level light` for faster processing
- Disable `--backup` if not needed
- Process in smaller batches

**For Memory-Constrained Systems:**
- Reduce `--parallel` workers
- Set lower `memory_limit_mb` in configuration
- Process files individually instead of batch mode

**For Network Storage:**
- Reduce parallel workers to avoid overwhelming network
- Use local temporary directory for processing
- Enable compression to reduce I/O

## Integration Examples

### Shell Scripts

```bash
#!/bin/bash
# Daily maintenance script

echo "Starting daily JSONL maintenance..."

# Prune recent conversations (light level)
claude-prune batch \
  --directory /var/conversations \
  --recursive \
  --level light \
  --parallel 4

# Generate daily report
claude-prune stats \
  --directory /var/conversations \
  --recursive \
  --format json \
  --output "/var/reports/daily-$(date +%Y%m%d).json"

echo "Maintenance complete"
```

### Cron Jobs

```bash
# Daily at 2 AM
0 2 * * * /usr/local/bin/claude-prune schedule --run

# Weekly analysis report
0 9 * * 1 /usr/local/bin/claude-prune stats --directory /data --format html --output /reports/weekly.html
```

### Python Integration

```python
import subprocess
import json

# Run analysis and parse results
result = subprocess.run([
    'claude-prune', 'stats', 
    '--file', 'session.jsonl', 
    '--format', 'json'
], capture_output=True, text=True)

if result.returncode == 0:
    stats = json.loads(result.stdout)
    print(f"Total messages: {stats['total_messages']}")
    print(f"Compression potential: {stats.get('compression_potential', {})}")
```

## Support and Contributing

For issues, feature requests, or contributions, please visit the project repository.

### Reporting Issues

When reporting issues, please include:
- Command used
- Error message (with `--verbose` output)
- Sample JSONL file (if possible)
- System information

### Feature Requests

We welcome feature requests for:
- Additional output formats
- New pruning algorithms
- Integration with other tools
- Performance improvements