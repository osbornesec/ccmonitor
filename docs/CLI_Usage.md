# Command Line Interface Reference

## Overview

This document provides comprehensive command-line interface (CLI) reference for all components of the JSONL Conversation Pruning System. Each script provides specialized functionality that can be used independently or as part of the integrated pipeline.

## 🛠️ Script Summary

| Script | Purpose | Primary Use Case |
|--------|---------|------------------|
| `main_with_pruning.py` | Pipeline orchestrator | Complete automated pruning |
| `cleanup_claude_projects.py` | File-level cleanup | Remove backup files and empty conversations |
| `cleanup_and_ultra_prune.py` | Message-level pruning | Intelligent message deletion and preservation |
| `temporal_analysis.py` | Time-based analysis | Temporal decay and conversation velocity analysis |
| `importance_engine.py` | Content scoring | Message importance analysis and scoring |

---

## 📋 main_with_pruning.py

### Purpose
Orchestrates the complete pruning pipeline, coordinating file cleanup, message analysis, and content pruning operations.

### Synopsis
```bash
python main_with_pruning.py [OPTIONS] --target PATH
```

### Required Arguments
- `--target PATH`: Target directory or file path for pruning operations

### Optional Arguments

#### Configuration Options
```bash
--config PATH                    # Custom configuration file (YAML format)
--dry-run                       # Preview operations without making changes
--force                         # Skip confirmation prompts
```

#### Pipeline Control
```bash
--stage STAGE                   # Run specific pipeline stage only
                               # Stages: preprocessing, file_cleanup, message_analysis,
                               #         content_pruning, postprocessing

--stages STAGE1,STAGE2         # Run multiple specific stages (comma-separated)
--skip-stages STAGE1,STAGE2    # Skip specified stages (comma-separated)
```

#### Processing Options
```bash
--parallel                      # Enable parallel processing
--max-workers N                # Maximum parallel workers (default: 4)
--importance-threshold N       # Override importance threshold (0.0-1.0)
--days-threshold N             # Override age threshold in days
```

#### Output and Reporting
```bash
--report-output PATH           # Directory for detailed reports
--detailed-reports             # Generate comprehensive analysis reports
--log-level LEVEL              # Logging level: DEBUG, INFO, WARNING, ERROR
```

#### Safety Options
```bash
--backup-dir PATH              # Custom backup directory
--no-backup                    # Disable automatic backups (not recommended)
```

### Usage Examples

#### Basic Pipeline Execution
```bash
# Run complete pruning pipeline
python main_with_pruning.py --target ~/.claude/projects

# Dry run with preview
python main_with_pruning.py --dry-run --target ~/.claude/projects

# Run with custom configuration
python main_with_pruning.py --config my_config.yaml --target ~/.claude/projects
```

#### Selective Stage Execution
```bash
# Run only file cleanup
python main_with_pruning.py --stage file_cleanup --target ~/.claude/projects

# Run analysis and pruning stages
python main_with_pruning.py --stages message_analysis,content_pruning --target ~/.claude/projects

# Skip file cleanup, run message operations only
python main_with_pruning.py --skip-stages file_cleanup --target ~/.claude/projects
```

#### Advanced Processing
```bash
# Parallel processing with detailed reports
python main_with_pruning.py --parallel --max-workers 6 --detailed-reports \
  --report-output ./reports --target ~/.claude/projects

# Custom thresholds and forced execution
python main_with_pruning.py --importance-threshold 0.7 --days-threshold 14 \
  --force --target ~/.claude/projects
```

### Exit Codes
- `0`: Success
- `1`: Configuration error
- `2`: Permission denied
- `3`: Insufficient disk space
- `4`: Processing error
- `5`: User cancelled operation

---

## 🗂️ cleanup_claude_projects.py

### Purpose
Performs file-level cleanup in Claude projects directory, removing backup files, empty conversations, and artifacts.

### Synopsis
```bash
python cleanup_claude_projects.py [OPTIONS]
```

### Optional Arguments
```bash
--dry-run                      # Show what would be deleted (default behavior)
--delete                       # Actually delete files (overrides --dry-run)
--force                        # Skip confirmation prompt (use with caution)
--max-deletions N              # Maximum files to delete (default: 1000)
```

### Usage Examples

#### Basic Cleanup Operations
```bash
# Preview cleanup (safe, default behavior)
python cleanup_claude_projects.py

# Alternative explicit dry-run
python cleanup_claude_projects.py --dry-run

# Execute cleanup with confirmation
python cleanup_claude_projects.py --delete

# Automated cleanup without confirmation
python cleanup_claude_projects.py --delete --force
```

#### Safety-Controlled Cleanup
```bash
# Limit deletions for safety
python cleanup_claude_projects.py --delete --max-deletions 500

# Conservative cleanup with manual review
python cleanup_claude_projects.py --delete --max-deletions 100
```

### File Types Processed
- **Backup files**: `.backup`, `.backup-messages.*`
- **Timestamped backups**: `.jsonl.TIMESTAMP`
- **Empty JSONL files**: Primary conversation files with 0 bytes
- **Preserved files**: Primary JSONL files with content

### Sample Output
```
🧹 Found 486 files to clean up:
   📁 Empty JSONL Files: 486 files (0.0 MB)

🗑️  Deleting 486 files...
   🗑️  Deleted: project-name/empty-conversation.jsonl (0.0 KB)
   ...

🎊 CLEANUP SUMMARY:
   📊 Files scanned: 1,092
   🗑️  Files deleted: 486
   💾 Space freed: 0.0 MB
   📁 Primary JSONL files remaining: 120
```

---

## ✂️ cleanup_and_ultra_prune.py

### Purpose
Performs intelligent message-level pruning with importance analysis, temporal decay, and conversation preservation.

### Synopsis
```bash
python cleanup_and_ultra_prune.py [INPUT_FILE] [OPTIONS]
```

### Required Arguments
- `INPUT_FILE`: Path to JSONL conversation file to process

### Core Pruning Options
```bash
--delete-old-messages          # Enable timestamp-based message deletion
--days-old N                   # Age threshold in days (default: 7)
--preserve-important-messages  # Preserve high-importance messages (default: False)
--importance-threshold N       # Minimum importance to preserve (0.0-1.0, default: 0.6)
```

### Temporal Analysis Options
```bash
--temporal-decay-mode MODE     # Decay algorithm: linear, exponential, logarithmic, step
--decay-rate N                 # Decay rate (default: 0.15)
--enable-velocity-adjustment   # Adjust based on conversation pace
--reference-boost N            # Importance boost for referenced content (default: 0.3)
```

### Ultra-Mode Options
```bash
--ultra-mode                   # Enable aggressive compression
--target-reduction N           # Target reduction ratio (default: 0.8 = 80%)
--preserve-critical            # Force preservation of critical content
```

### Processing Options
```bash
--dry-run                      # Preview changes without modifying file
--backup-suffix SUFFIX         # Custom backup file suffix (default: .backup)
--output-file PATH             # Custom output file path
```

### Usage Examples

#### Basic Message Deletion
```bash
# Delete all messages older than 7 days (ignoring importance)
python cleanup_and_ultra_prune.py conversation.jsonl --delete-old-messages

# Preview deletion without changes
python cleanup_and_ultra_prune.py conversation.jsonl --delete-old-messages --dry-run

# Custom age threshold
python cleanup_and_ultra_prune.py conversation.jsonl --delete-old-messages --days-old 14
```

#### Importance-Based Pruning
```bash
# Prune low-importance messages
python cleanup_and_ultra_prune.py conversation.jsonl --importance-threshold 0.6

# Preserve important messages while deleting old ones
python cleanup_and_ultra_prune.py conversation.jsonl --delete-old-messages \
  --preserve-important-messages --importance-threshold 0.7
```

#### Advanced Temporal Analysis
```bash
# Exponential decay with custom rate
python cleanup_and_ultra_prune.py conversation.jsonl --temporal-decay-mode exponential \
  --decay-rate 0.2 --importance-threshold 0.5

# Reference-aware processing
python cleanup_and_ultra_prune.py conversation.jsonl --enable-reference-analysis \
  --reference-boost 0.4
```

#### Ultra-Mode Compression
```bash
# Aggressive compression (remove 80% of messages)
python cleanup_and_ultra_prune.py conversation.jsonl --ultra-mode

# Custom reduction target
python cleanup_and_ultra_prune.py conversation.jsonl --ultra-mode --target-reduction 0.9

# Ultra-mode with critical content preservation
python cleanup_and_ultra_prune.py conversation.jsonl --ultra-mode --preserve-critical
```

### Sample Output
```
📊 CONVERSATION ANALYSIS:
   📝 Total messages: 1,247
   ⏰ Messages older than 7 days: 892 (71.5%)
   🔍 High importance messages: 178 (14.3%)
   🔗 Cross-referenced messages: 45 (3.6%)

🗑️  MESSAGE DELETION SUMMARY:
   🗑️  Messages deleted: 892 (71.5%)
   ✅ Messages preserved: 355 (28.5%)
   💾 Size reduction: 2.3 MB (68.2%)
   ⚡ Processing time: 0.8 seconds
```

---

## ⏰ temporal_analysis.py

### Purpose
Provides temporal analysis capabilities including decay algorithms, conversation velocity analysis, and time-based importance weighting.

### Synopsis
```bash
python temporal_analysis.py [INPUT_FILE] [OPTIONS]
```

### Analysis Options
```bash
--analyze-velocity             # Perform conversation velocity analysis
--decay-mode MODE              # Decay algorithm: linear, exponential, logarithmic, step
--decay-rate N                 # Decay rate parameter (default: 0.15)
--time-window N                # Analysis time window in hours (default: 24)
```

### Output Options
```bash
--output-format FORMAT         # Output format: json, yaml, csv (default: json)
--save-results PATH            # Save analysis results to file
--detailed-analysis            # Include detailed breakdown in output
```

### Usage Examples

#### Velocity Analysis
```bash
# Analyze conversation velocity patterns
python temporal_analysis.py conversation.jsonl --analyze-velocity

# Detailed velocity analysis with custom time window
python temporal_analysis.py conversation.jsonl --analyze-velocity \
  --time-window 48 --detailed-analysis
```

#### Decay Algorithm Testing
```bash
# Test different decay algorithms
python temporal_analysis.py conversation.jsonl --decay-mode exponential --decay-rate 0.1
python temporal_analysis.py conversation.jsonl --decay-mode linear --decay-rate 0.05
python temporal_analysis.py conversation.jsonl --decay-mode logarithmic --decay-rate 0.2
```

#### Analysis Export
```bash
# Export analysis results
python temporal_analysis.py conversation.jsonl --analyze-velocity \
  --output-format json --save-results analysis_results.json

# CSV export for spreadsheet analysis
python temporal_analysis.py conversation.jsonl --analyze-velocity \
  --output-format csv --save-results velocity_data.csv
```

---

## 🧠 importance_engine.py

### Purpose
Analyzes message content and calculates importance scores using multi-factor analysis including technical complexity, error criticality, and cross-references.

### Synopsis
```bash
python importance_engine.py [INPUT_FILE] [OPTIONS]
```

### Analysis Options
```bash
--factor-weights WEIGHTS       # Custom factor weights (JSON format)
--preset PRESET                # Use preset configuration: conservative, balanced, aggressive,
                               #                           code_focused, error_focused
--enable-cross-references      # Enable cross-reference analysis
--enable-code-detection        # Enable code content detection
```

### Output Options
```bash
--output-scores PATH           # Save importance scores to file
--detailed-breakdown           # Include detailed factor analysis
--threshold N                  # Highlight messages above threshold (default: 0.6)
```

### Usage Examples

#### Basic Importance Analysis
```bash
# Analyze message importance with default settings
python importance_engine.py conversation.jsonl

# Use balanced preset configuration
python importance_engine.py conversation.jsonl --preset balanced
```

#### Custom Configuration
```bash
# Code-focused analysis
python importance_engine.py conversation.jsonl --preset code_focused \
  --enable-code-detection --detailed-breakdown

# Error-focused analysis
python importance_engine.py conversation.jsonl --preset error_focused \
  --threshold 0.5
```

#### Factor Weight Customization
```bash
# Custom factor weights (JSON format)
python importance_engine.py conversation.jsonl \
  --factor-weights '{"content_complexity": 0.4, "technical_depth": 0.3, "error_criticality": 0.2, "cross_references": 0.1}'

# Export detailed analysis
python importance_engine.py conversation.jsonl --detailed-breakdown \
  --output-scores importance_analysis.json
```

---

## 🔧 Common Usage Patterns

### 1. Complete Automated Cleanup
```bash
# One-command complete cleanup
python main_with_pruning.py --target ~/.claude/projects --force

# Safe preview of complete cleanup
python main_with_pruning.py --target ~/.claude/projects --dry-run --detailed-reports
```

### 2. Conservative Message Pruning
```bash
# Conservative pruning: only remove very old messages
python cleanup_and_ultra_prune.py conversation.jsonl --delete-old-messages \
  --days-old 30 --preserve-important-messages --importance-threshold 0.3
```

### 3. Aggressive Space Optimization
```bash
# Maximum compression for storage optimization
python cleanup_and_ultra_prune.py conversation.jsonl --ultra-mode \
  --target-reduction 0.9 --importance-threshold 0.8
```

### 4. Technical Content Preservation
```bash
# Optimize for technical content preservation
python main_with_pruning.py --target ~/.claude/projects \
  --config code_focused_config.yaml --importance-threshold 0.5
```

### 5. Batch Processing Multiple Files
```bash
# Process multiple conversation files
for file in *.jsonl; do
  python cleanup_and_ultra_prune.py "$file" --delete-old-messages --days-old 7
done

# Parallel batch processing with main pipeline
python main_with_pruning.py --target ~/conversations --parallel --max-workers 8
```

---

## 🚨 Safety Recommendations

### Always Use Dry-Run First
```bash
# ALWAYS preview changes first
python script.py --dry-run [other options]

# Then execute after reviewing
python script.py [other options]
```

### Backup Important Data
```bash
# Manual backup before major operations
cp -r ~/.claude/projects ~/.claude/projects.backup.$(date +%Y%m%d)

# Use built-in backup features
python main_with_pruning.py --backup-dir ./my_backups --target ~/.claude/projects
```

### Start with Conservative Settings
```bash
# Begin with conservative thresholds
python cleanup_and_ultra_prune.py conversation.jsonl --delete-old-messages \
  --days-old 30 --preserve-important-messages --importance-threshold 0.3

# Gradually increase aggressiveness
python cleanup_and_ultra_prune.py conversation.jsonl --delete-old-messages \
  --days-old 14 --importance-threshold 0.5
```

---

## 🐛 Troubleshooting Common Issues

### Permission Errors
```bash
# Check file permissions
ls -la ~/.claude/projects

# Fix permissions if needed
chmod -R u+w ~/.claude/projects
```

### Configuration Validation
```bash
# Validate configuration file
python main_with_pruning.py --validate-config pruning_config.yaml

# Test with minimal configuration
python main_with_pruning.py --target test_data --dry-run
```

### Memory Issues with Large Files
```bash
# Use streaming mode for large files
python cleanup_and_ultra_prune.py large_conversation.jsonl --stream-processing

# Process in smaller batches
python main_with_pruning.py --target large_directory --batch-size 50
```

### Recovery from Failed Operations
```bash
# Restore from automatic backup
cp conversation.jsonl.backup conversation.jsonl

# Use rollback feature in main pipeline
python main_with_pruning.py --rollback --backup-id 20250803_143022
```

---

## 📖 Additional Resources

### Configuration Examples
- See individual component documentation for detailed configuration options
- Example YAML configuration files in `docs/` directory
- Preset configurations for common use cases

### Performance Tuning
- Use `--parallel` for multiple file processing
- Adjust `--max-workers` based on system resources
- Consider `--batch-size` for memory-constrained environments

### Integration Examples
- Cron job setup for automated maintenance
- Integration with backup systems
- Custom scripting for specialized workflows

---

For detailed information about specific components, refer to the individual documentation files:
- [cleanup_and_ultra_prune.md](cleanup_and_ultra_prune.md)
- [cleanup_claude_projects.md](cleanup_claude_projects.md)
- [temporal_analysis.md](temporal_analysis.md)
- [importance_engine.md](importance_engine.md)
- [main_with_pruning.md](main_with_pruning.md)