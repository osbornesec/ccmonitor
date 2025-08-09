# CCMonitor CLI Flags and Options Reference

This document provides a comprehensive reference for all command-line flags and options available in the CCMonitor system.

## Table of Contents

1. [Main CLI Tool (`claude-prune`)](#main-cli-tool-claude-prune)
2. [Basic Monitor Script (`main.py`)](#basic-monitor-script-mainpy)
3. [Advanced Monitor with Pruning (`main_with_pruning.py`)](#advanced-monitor-with-pruning-main_with_pruningpy)
4. [Common Flag Patterns](#common-flag-patterns)
5. [Configuration Files](#configuration-files)

---

## Main CLI Tool (`claude-prune`)

The primary CLI tool installed as `claude-prune` provides the most comprehensive set of options.

### Global Options

These options are available for all commands:

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--version` | - | flag | false | Show version and exit |
| `--verbose` | `-v` | flag | false | Enable verbose output |
| `--config` | - | path | default | Configuration file path |
| `--dry-run` | - | flag | false | Show what would be done without making changes |

**Examples:**
```bash
claude-prune --version
claude-prune --verbose prune session.jsonl
claude-prune --config custom.yaml --dry-run prune data.jsonl
```

---

### Command: `prune`

Prune a single JSONL conversation file.

| Flag | Short | Type | Options | Default | Description |
|------|-------|------|---------|---------|-------------|
| `--file` | `-f` | path | - | required | Input JSONL file to process |
| `--output` | `-o` | path | - | auto | Output file path (default: overwrites input or adds .pruned suffix) |
| `--level` | `-l` | choice | light, medium, aggressive, ultra | medium | Pruning aggressiveness level |
| `--temporal-decay` | - | flag | - | false | Enable temporal decay for time-based importance weighting |
| `--no-temporal-decay` | - | flag | - | false | Disable temporal decay (explicit) |
| `--decay-mode` | - | choice | none, simple, multi_stage, content_aware, adaptive | simple | Temporal decay mode |
| `--decay-preset` | - | choice | development, debugging, conversation, analysis, aggressive, conservative | - | Use temporal decay preset configuration |
| `--backup` | - | flag | - | true | Create backup before processing |
| `--no-backup` | - | flag | - | false | Disable backup creation |
| `--stats` | - | flag | - | false | Display processing statistics |
| `--no-stats` | - | flag | - | true | Disable statistics display |
| `--progress` | - | flag | - | true | Show progress bar |
| `--no-progress` | - | flag | - | false | Hide progress bar |

**Examples:**
```bash
# Basic pruning with backup
claude-prune prune session.jsonl --level light --backup

# Aggressive pruning with custom output and stats
claude-prune prune data.jsonl --output pruned.jsonl --level aggressive --stats

# Temporal decay with preset
claude-prune prune conversation.jsonl --temporal-decay --decay-preset debugging

# Dry run with no backup
claude-prune prune large_file.jsonl --level ultra --no-backup --dry-run
```

---

### Command: `batch`

Process multiple JSONL files in batch mode.

| Flag | Short | Type | Options | Default | Description |
|------|-------|------|---------|---------|-------------|
| `--directory` | `-d` | path | - | required | Directory to process |
| `--pattern` | `-p` | string | - | *.jsonl | File pattern to match |
| `--recursive` | `-r` | flag | - | false | Process directories recursively |
| `--level` | `-l` | choice | light, medium, aggressive, ultra | medium | Pruning aggressiveness level |
| `--temporal-decay` | - | flag | - | false | Enable temporal decay for time-based importance weighting |
| `--no-temporal-decay` | - | flag | - | false | Disable temporal decay (explicit) |
| `--decay-mode` | - | choice | none, simple, multi_stage, content_aware, adaptive | simple | Temporal decay mode |
| `--decay-preset` | - | choice | development, debugging, conversation, analysis, aggressive, conservative | - | Use temporal decay preset configuration |
| `--parallel` | - | integer | - | 4 | Number of parallel workers |
| `--resume` | - | flag | - | false | Resume interrupted batch operation |
| `--backup` | - | flag | - | true | Create backups before processing |
| `--no-backup` | - | flag | - | false | Disable backup creation |

**Examples:**
```bash
# Basic batch processing
claude-prune batch /projects --pattern "*.jsonl" --recursive

# High-performance batch with more workers
claude-prune batch /data --level aggressive --parallel 8

# Resume interrupted operation
claude-prune batch /work --resume

# Custom pattern with no backups
claude-prune batch /logs --pattern "conversation_*.jsonl" --no-backup
```

---

### Command: `stats`

Generate statistics and analysis reports.

| Flag | Short | Type | Options | Default | Description |
|------|-------|------|---------|---------|-------------|
| `--file` | `-f` | path | - | - | JSONL file to analyze |
| `--directory` | `-d` | path | - | - | Directory to analyze |
| `--recursive` | `-r` | flag | - | false | Analyze directories recursively |
| `--format` | - | choice | table, json, csv, html | table | Output format |
| `--output` | `-o` | path | - | stdout | Output file path |
| `--trend` | - | flag | - | false | Include trend analysis |

**Note:** Either `--file` or `--directory` must be specified.

**Examples:**
```bash
# Analyze single file with JSON output
claude-prune stats session.jsonl --format json --output report.json

# Analyze directory with trend analysis
claude-prune stats --directory /projects --recursive --trend

# Generate HTML report
claude-prune stats data.jsonl --format html --output report.html

# Quick table view
claude-prune stats conversation.jsonl
```

---

### Command: `schedule`

Configure automatic pruning schedules.

| Flag | Short | Type | Options | Default | Description |
|------|-------|------|---------|---------|-------------|
| `--enable` | - | flag | - | false | Enable automatic scheduling |
| `--disable` | - | flag | - | false | Disable automatic scheduling |
| `--policy` | - | choice | daily, weekly, monthly | weekly | Scheduling policy |
| `--level` | - | choice | light, medium, aggressive, ultra | light | Default pruning level for scheduled operations |
| `--temporal-decay` | - | flag | - | false | Enable temporal decay for scheduled operations |
| `--no-temporal-decay` | - | flag | - | false | Disable temporal decay for scheduled operations |
| `--decay-preset` | - | choice | development, debugging, conversation, analysis, aggressive, conservative | development | Temporal decay preset for scheduled operations |
| `--directories` | - | multiple | - | - | Directories to include in scheduled pruning |
| `--show` | - | flag | - | false | Show current scheduling configuration |

**Examples:**
```bash
# Enable weekly light pruning
claude-prune schedule --enable --policy weekly --level light

# Add directories to scheduled pruning
claude-prune schedule --directories /projects /work /data

# Show current configuration
claude-prune schedule --show

# Disable scheduling
claude-prune schedule --disable
```

---

## Basic Monitor Script (`main.py`)

Simple monitoring script for tracking changes in Claude Code projects.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--interval` | `-i` | integer | 5 | Check interval in seconds |
| `--process-all` | `-a` | flag | false | Process all existing JSONL files and exit |
| `--since-last-run` | `-s` | flag | false | Process only changes since last run and exit |
| `--output` | `-o` | string | claude_session_changes.txt | Output file path |
| `--verbose` | `-v` | flag | false | Enable verbose debug logging |

**Examples:**
```bash
# Normal monitoring mode
python main.py

# Fast monitoring with 2-second intervals
python main.py --interval 2

# Process all files once and exit
python main.py --process-all

# Process only recent changes
python main.py --since-last-run

# Custom output file with verbose logging
python main.py --output my_changes.txt --verbose
```

---

## Advanced Monitor with Pruning (`main_with_pruning.py`)

Enhanced monitoring script with automatic JSONL pruning capabilities.

### Basic Options

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--interval` | `-i` | integer | 5 | Check interval in seconds |
| `--process-all` | `-a` | flag | false | Process all existing JSONL files and exit |
| `--since-last-run` | `-s` | flag | false | Process only changes since last run and exit |
| `--output` | `-o` | string | claude_session_changes.txt | Output file path |
| `--verbose` | `-v` | flag | false | Enable verbose debug logging |

### Pruning-Specific Options

| Flag | Short | Type | Options | Default | Description |
|------|-------|------|---------|---------|-------------|
| `--no-pruning` | - | flag | - | false | Disable automatic pruning (monitoring only) |
| `--pruning-level` | - | choice | light, medium, aggressive, ultra | medium | Pruning aggressiveness level |
| `--no-backup` | - | flag | - | false | Disable automatic backup before pruning |
| `--threshold` | - | integer | - | 100 | Only prune files larger than this size in KB |

**Examples:**
```bash
# Normal monitoring with pruning
python main_with_pruning.py

# Aggressive pruning for large files
python main_with_pruning.py --pruning-level aggressive --threshold 50

# Monitoring only (no pruning)
python main_with_pruning.py --no-pruning

# Fast operation without backups
python main_with_pruning.py --no-backup --interval 2

# Process all files with ultra pruning
python main_with_pruning.py --process-all --pruning-level ultra
```

---

## Common Flag Patterns

### Safety-First Approach
```bash
# Always use dry-run first
claude-prune prune session.jsonl --level aggressive --dry-run

# Then run with backup
claude-prune prune session.jsonl --level aggressive --backup
```

### Performance Optimization
```bash
# Batch processing with maximum workers
claude-prune batch /data --parallel 8 --no-backup

# Streaming mode for large files
python main_with_pruning.py --threshold 50 --no-backup
```

### Development Workflow
```bash
# Light pruning for active development
claude-prune prune session.jsonl --level light --temporal-decay --decay-preset development

# Regular maintenance
claude-prune batch ~/.claude/projects --level medium --recursive
```

### Analysis and Reporting
```bash
# Comprehensive analysis
claude-prune stats ~/.claude/projects --recursive --format json --output analysis.json --trend

# Quick file check
claude-prune stats session.jsonl --format table
```

---

## Configuration Files

### YAML Configuration Structure

```yaml
# config/custom.yaml
pruning:
  level: medium                    # light, medium, aggressive, ultra
  preserve_errors: true
  preserve_context_chains: true
  min_importance_threshold: 0.3

temporal:
  decay_mode: adaptive            # none, simple, multi_stage, content_aware, adaptive
  max_age_days: 30
  importance_boost_factor: 1.5
  preset: development             # development, debugging, conversation, analysis, aggressive, conservative

safety:
  auto_backup: true
  validation_level: strict        # basic, normal, strict
  max_deletions_per_run: 1000

batch:
  parallel_workers: 4
  chunk_size: 100
  resume_on_failure: true

output:
  format: table                   # table, json, csv, html
  verbose: false
  progress: true
  colors: true
```

### Using Configuration Files

```bash
# Use custom configuration
claude-prune --config config/custom.yaml prune session.jsonl

# Override specific settings
claude-prune --config config/custom.yaml prune session.jsonl --level ultra --no-backup
```

---

## Best Practices

### Flag Combinations

1. **Safe Exploration**: Always start with `--dry-run`
2. **Production Use**: Use `--backup` for safety
3. **Performance**: Use `--parallel` for batch operations
4. **Analysis**: Use `--stats` and `--verbose` for insights
5. **Automation**: Use `schedule` command for regular maintenance

### Common Workflows

```bash
# 1. Analyze before pruning
claude-prune stats session.jsonl --verbose
claude-prune prune session.jsonl --level medium --dry-run
claude-prune prune session.jsonl --level medium --backup

# 2. Batch processing workflow
claude-prune stats /projects --recursive --format json --output before.json
claude-prune batch /projects --level light --recursive --backup
claude-prune stats /projects --recursive --format json --output after.json

# 3. Emergency cleanup
claude-prune prune large_file.jsonl --level ultra --dry-run
claude-prune prune large_file.jsonl --level ultra --backup --stats
```

### Error Recovery

```bash
# If something goes wrong, backups are automatically created with timestamps
# Restore from backup: just copy the .backup file back to original name

# Check what happened
claude-prune stats session.jsonl --verbose

# Validate file integrity
python -c "import json; [json.loads(line) for line in open('session.jsonl')]"
```

---

This documentation covers all available flags and options in the CCMonitor system. For more examples and advanced usage patterns, refer to the main README.md file.