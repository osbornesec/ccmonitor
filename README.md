# CCMonitor - Claude Code Conversation Monitor

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

CCMonitor is an intelligent conversation monitoring and analysis system specifically designed for Claude Code JSONL files. It provides sophisticated analysis capabilities, real-time monitoring, and comprehensive reporting for conversation files.

## 🚀 Features

### Core Capabilities
- **Real-time Conversation Monitoring**: Track Claude Code project conversations as they change
- **Comprehensive Analysis**: Deep analysis of conversation patterns, message types, and structure
- **Batch Processing**: Analyze multiple JSONL files with parallel processing
- **Rich Reporting**: Export analysis results in JSON, CSV, and HTML formats
- **Professional CLI**: Clean command-line interface with colored output and progress indicators

### Analysis Features
- **Message Type Distribution**: Understand conversation composition (user, assistant, tool calls)
- **Conversation Structure**: Analyze conversation depth, chains, and flow patterns
- **File Statistics**: Track file sizes, message counts, and processing metrics
- **Pattern Recognition**: Identify conversation patterns and development workflows
- **Performance Metrics**: Processing time analysis and efficiency reporting

### Monitoring Features
- **Change Detection**: Real-time monitoring of JSONL file modifications
- **State Management**: Resume monitoring from where you left off
- **Flexible Patterns**: Monitor specific file patterns and directories
- **Detailed Logging**: Comprehensive change logs with timestamps

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- uv (recommended) or pip for package management

### Quick Install
```bash
# Clone the repository
git clone <repository-url>
cd ccmonitor

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

### Verify Installation
```bash
ccmonitor --version
```

## 🎯 Quick Start

### Basic Usage
```bash
# Monitor Claude Code projects directory
ccmonitor monitor

# Analyze a single conversation file
ccmonitor analyze conversation.jsonl

# Batch analyze multiple files
ccmonitor batch /path/to/conversations --recursive
```

### Common Scenarios

#### 1. Real-time Conversation Monitoring
```bash
# Monitor default Claude Code directory
ccmonitor monitor

# Monitor custom directory with 10-second intervals
ccmonitor monitor --directory /path/to/conversations --interval 10

# Monitor and save changes to custom file
ccmonitor monitor --output my_changes.txt
```

#### 2. Single File Analysis
```bash
# Basic analysis
ccmonitor analyze conversation.jsonl

# Detailed analysis with HTML report
ccmonitor analyze conversation.jsonl --detailed --format html --output report.html

# JSON export for further processing
ccmonitor analyze conversation.jsonl --format json --output analysis.json
```

#### 3. Batch Analysis
```bash
# Analyze all JSONL files in directory
ccmonitor batch /path/to/conversations

# Recursive analysis with CSV export
ccmonitor batch /path/to/conversations --recursive --format csv --output results.csv

# Parallel processing with 8 workers
ccmonitor batch /path/to/conversations --parallel 8
```

#### 4. Process Historical Changes
```bash
# Process all existing files once
ccmonitor monitor --process-all

# Process only changes since last run
ccmonitor monitor --since-last-run
```

## 🛠️ CLI Commands

### Main Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `monitor` | Real-time conversation monitoring | `ccmonitor monitor --interval 5` |
| `analyze` | Analyze single file or directory | `ccmonitor analyze file.jsonl --detailed` |
| `batch` | Batch process multiple files | `ccmonitor batch /dir --recursive` |
| `config` | Manage configuration | `ccmonitor config show` |

### Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `--verbose`, `-v` | Enable detailed logging | `False` |
| `--format` | Output format (table/json/csv/html) | `table` |
| `--output`, `-o` | Output file path | `stdout` |
| `--recursive`, `-r` | Process directories recursively | `False` |
| `--parallel` | Number of parallel workers | `4` |

## 📊 Analysis Reports

CCMonitor provides rich analysis reports with comprehensive metrics:

### File-level Analysis
- Total message count and types
- File size and processing time
- Conversation depth and structure
- Pattern recognition results

### Batch Analysis
- Summary statistics across all files
- Success/failure rates
- Performance metrics
- Comparative analysis

### Export Formats
- **JSON**: Machine-readable format for integration
- **CSV**: Spreadsheet-compatible tabular data  
- **HTML**: Rich formatted reports with visualizations
- **Table**: Terminal-friendly tabular display

## 🔧 Configuration

### Default Configuration
CCMonitor uses sensible defaults but can be customized:

```bash
# Show current configuration
ccmonitor config show

# Set configuration values
ccmonitor config set monitoring.interval 10
ccmonitor config set output.default_format json
```

### Monitoring Settings
- **Default directory**: `~/.claude/projects`
- **File pattern**: `*.jsonl`
- **Check interval**: 5 seconds
- **State persistence**: Enabled

### Processing Settings
- **Parallel workers**: 4 (max 8)
- **Memory optimization**: Enabled for large files
- **Progress indicators**: Enabled
- **Verbose logging**: Configurable

## 🏗️ Architecture

### Core Components

```
ccmonitor/
├── src/
│   ├── cli/                    # Command-line interface
│   │   ├── main.py            # Primary CLI commands
│   │   ├── batch.py           # Batch processing engine
│   │   ├── config.py          # Configuration management
│   │   └── utils.py           # CLI utilities
│   ├── jsonl_analysis/        # Analysis engine
│   │   ├── analyzer.py        # Core JSONL parsing and analysis
│   │   ├── scoring.py         # Analysis scoring algorithms
│   │   ├── patterns.py        # Pattern recognition
│   │   └── exceptions.py      # Custom exceptions
│   └── utils/                 # Shared utilities
├── tests/                     # Comprehensive test suite
└── main.py                    # Basic monitoring script
```

### Key Classes

- **`JSONLAnalyzer`**: Core analysis engine for parsing and analyzing conversations
- **`BatchProcessor`**: Parallel processing system for multiple files
- **`ConfigManager`**: Configuration management and persistence
- **`StatisticsGenerator`**: Report generation and export functionality

## 📈 Performance

### Benchmarks
- **Processing Speed**: 1000+ messages per second
- **Memory Usage**: <100MB for large conversation files  
- **Batch Processing**: Linear scaling with parallel workers
- **File Monitoring**: Real-time detection with minimal overhead

### Optimization Features
- Parallel batch processing with configurable workers
- Memory-efficient streaming for large files
- Intelligent file pattern matching
- State persistence for monitoring resume

## 🧪 Testing

### Run Test Suite
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/jsonl_analysis/    # Analysis engine tests
pytest tests/cli/               # CLI interface tests
```

### Test Coverage
- **Unit Tests**: Core functionality and edge cases
- **Integration Tests**: End-to-end workflows  
- **CLI Tests**: Command-line interface testing
- **Analysis Tests**: JSONL parsing and analysis validation

## 🔍 Troubleshooting

### Common Issues

**Large File Processing**
```bash
# For files >100MB, monitor will use streaming automatically
ccmonitor monitor --verbose  # Shows processing details
```

**Permission Issues**
```bash
# Ensure read permissions on target directories
ls -la ~/.claude/projects/
```

**Configuration Issues**
```bash
# Reset to defaults
ccmonitor config show
```

### Debug Mode
```bash
# Enable verbose logging
ccmonitor analyze file.jsonl --verbose

# Monitor with detailed output
ccmonitor monitor --verbose
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
uv sync --dev

# Install pre-commit hooks
pre-commit install

# Run linting
ruff check src/
ruff format src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for analysis of Claude Code conversation files
- Inspired by conversation analysis and data monitoring research
- Designed with performance and reliability as primary concerns

---

**CCMonitor** - Intelligent conversation monitoring and analysis for Claude Code workflows.