# JSONL Conversation Pruning System - Documentation

## 📚 Documentation Index

Welcome to the comprehensive documentation for the JSONL Conversation Pruning System. This documentation provides detailed information about each component, usage patterns, and integration examples.

## 🏠 Start Here

### **[PROJECT_README.md](PROJECT_README.md)** - Project Overview
**Essential reading for all users**
- Complete project overview and architecture
- Quick start guide and installation
- Real-world performance results
- Configuration overview and safety features

### **[CLI_Usage.md](CLI_Usage.md)** - Command Line Reference
**Complete CLI reference for all scripts**
- Command syntax and options for all tools
- Usage examples and common patterns
- Safety recommendations and troubleshooting
- Integration examples and best practices

## 🔧 Component Documentation

### Core Pruning Engine
**[cleanup_and_ultra_prune.md](cleanup_and_ultra_prune.md)**
- Message-level pruning with intelligent content preservation
- Temporal deletion engine and ultra-mode compression
- Importance-based filtering and reference preservation
- Advanced configuration and performance optimization

### File Management
**[cleanup_claude_projects.md](cleanup_claude_projects.md)**
- File-level cleanup for backup files and empty conversations
- Safety mechanisms and deletion limits
- File classification and reporting
- Performance characteristics and integration points

### Analysis Engines

**[temporal_analysis.md](temporal_analysis.md)**
- Time-based analysis with multiple decay algorithms
- Conversation velocity tracking and pattern detection
- Reference-aware temporal adjustments
- Performance optimization and caching strategies

**[importance_engine.md](importance_engine.md)**
- Multi-factor importance scoring for message content
- Technical content detection and error analysis
- Cross-reference tracking and relationship mapping
- Machine learning integration and adaptive thresholds

### Pipeline Orchestration
**[main_with_pruning.md](main_with_pruning.md)**
- Complete pipeline orchestration and coordination
- Configuration management and error handling
- Monitoring, reporting, and batch processing
- Integration with external systems and APIs

## 📋 Quick Reference

### Most Common Tasks

| Task | Command | Documentation |
|------|---------|---------------|
| Complete automated cleanup | `python main_with_pruning.py --target ~/.claude/projects` | [main_with_pruning.md](main_with_pruning.md) |
| Remove backup files only | `python cleanup_claude_projects.py --delete` | [cleanup_claude_projects.md](cleanup_claude_projects.md) |
| Delete old messages (7+ days) | `python cleanup_and_ultra_prune.py file.jsonl --delete-old-messages` | [cleanup_and_ultra_prune.md](cleanup_and_ultra_prune.md) |
| Preview all changes | `python main_with_pruning.py --dry-run --target ~/.claude/projects` | [CLI_Usage.md](CLI_Usage.md) |

### Key Configuration Files
- `pruning_config.yaml` - Master configuration for all components
- Component-specific configurations in individual documentation
- Preset configurations for common use cases

## 🎯 Use Case Guides

### For Regular Maintenance
1. **Start with**: [PROJECT_README.md](PROJECT_README.md) - Quick Start section
2. **Configure**: Review configuration examples in component docs
3. **Execute**: Use [CLI_Usage.md](CLI_Usage.md) for command syntax
4. **Monitor**: Check reporting features in [main_with_pruning.md](main_with_pruning.md)

### For Custom Integration
1. **Architecture**: Review component responsibilities in [PROJECT_README.md](PROJECT_README.md)
2. **APIs**: Check integration points in individual component docs
3. **Configuration**: Customize settings using component documentation
4. **Automation**: Use [CLI_Usage.md](CLI_Usage.md) for scripting examples

### For Performance Optimization
1. **Analysis**: Use temporal and importance analysis documentation
2. **Tuning**: Review performance sections in component docs
3. **Monitoring**: Implement tracking from [main_with_pruning.md](main_with_pruning.md)
4. **Scaling**: Check parallel processing in [CLI_Usage.md](CLI_Usage.md)

## 🛡️ Safety and Best Practices

### Before You Start
- **Always use dry-run mode first**: Preview changes before execution
- **Create backups**: Manual or automatic backup before major operations
- **Start conservative**: Begin with gentler settings and gradually optimize
- **Test on small datasets**: Validate configuration with test data

### Critical Safety Features
- Automatic backup creation before destructive operations
- Configurable deletion limits and safety thresholds
- Comprehensive error handling with rollback capabilities
- Detailed logging and operation reporting

## 📊 Documentation Statistics

- **Total Documents**: 7 comprehensive guides
- **Total Pages**: 50+ pages of detailed documentation
- **Usage Examples**: 100+ command examples across all guides
- **Configuration Options**: 25+ configurable parameters documented
- **Safety Features**: 10+ built-in protection mechanisms explained

## 🔄 Documentation Updates

This documentation reflects the current implementation and includes:
- Real-world usage results and performance metrics
- User feedback integration (aggressive temporal deletion behavior)
- Comprehensive CLI reference with all current options
- Architecture decisions and design rationale
- Future roadmap and enhancement plans

## 🤝 Getting Help

### Documentation Navigation
1. **New users**: Start with [PROJECT_README.md](PROJECT_README.md)
2. **Command reference**: Go to [CLI_Usage.md](CLI_Usage.md)
3. **Component details**: Check individual component documentation
4. **Troubleshooting**: Each component doc includes troubleshooting sections

### Common Questions
- **"How do I start?"** → [PROJECT_README.md](PROJECT_README.md) Quick Start
- **"What commands do I use?"** → [CLI_Usage.md](CLI_Usage.md)
- **"How do I configure X?"** → Relevant component documentation
- **"Something went wrong!"** → Troubleshooting sections in component docs

## 📈 Project Evolution

### Recent Enhancements
- **User-requested behavior**: Aggressive temporal deletion ignoring importance for old messages
- **Zero-byte file cleanup**: Enhanced file cleanup to remove empty conversation files
- **Performance optimization**: Real-world performance data and optimization recommendations
- **Comprehensive documentation**: Complete documentation coverage for all components

### Future Documentation Plans
- Interactive examples and tutorials
- Video walkthroughs for complex operations
- Integration guides for specific use cases
- Performance tuning cookbook

---

**Note**: This documentation is actively maintained and reflects the current state of the system. For the most up-to-date information, refer to the individual component documentation files listed above.