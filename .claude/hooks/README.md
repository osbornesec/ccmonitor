# Claude Code Hooks - Rust Quality Gates

This directory contains Claude Code hooks for enforcing enterprise-grade Rust code quality standards.

## Overview

The quality gate system ensures that all Rust code meets strict formatting, linting, and compilation standards before Claude finishes responding. This prevents low-quality code from being committed and maintains consistent code quality across the project.

## Hook Files

### 1. `quality_gate.py` (Recommended)
- **Purpose**: Comprehensive Python-based quality gate checker
- **Features**: Detailed error reporting, timeout handling, structured JSON output
- **Use Case**: Production environments requiring detailed diagnostics
- **Execution Time**: ~10-15 seconds for full checks

### 2. `quality_gate.sh` (Lightweight)
- **Purpose**: Fast shell script-based quality gate checker  
- **Features**: Quick execution, colored output, minimal dependencies
- **Use Case**: Development environments prioritizing speed
- **Execution Time**: ~5-8 seconds for full checks

### 3. Hook Configuration in `.claude/settings.json`
- **Current**: Uses Python script for maximum reliability
- **Alternative**: Can be switched to shell script for faster execution

## Quality Checks Performed

### 1. Configuration Validation
Ensures all required configuration files exist:
- `rustfmt.toml` - Formatting rules
- `Cargo.toml` - Project configuration with linting rules
- `.cargo/config.toml` - Build flags and compiler settings

### 2. Format Check (`cargo fmt -- --check`)
- **Purpose**: Ensures consistent code formatting
- **Standards**: Max 100 chars, vertical imports, strict formatting
- **Failure Action**: Blocks completion, shows diff output

### 3. Lint Check (`cargo clippy -- -D warnings`)
- **Purpose**: Enforces 60+ strict linting rules
- **Standards**: Pedantic rules, restriction rules, zero warnings allowed
- **Failure Action**: Blocks completion, shows detailed violations

### 4. Compilation Check (`cargo check`)
- **Purpose**: Verifies code compiles successfully
- **Standards**: All warnings treated as errors
- **Failure Action**: Blocks completion, shows compiler errors

## Installation & Configuration

### Current Setup (Already Configured)
The Python-based quality gate is already configured in your `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "description": "Final quality gate check before stopping",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/quality_gate.py\"",
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

### Alternative Configurations

#### Switch to Shell Script (Faster)
```json
"command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/quality_gate.sh\""
```

#### Inline Python (Emergency Fallback)
```json
"command": "python3 -c \"import json,sys,os,subprocess;pd=os.environ.get('CLAUDE_PROJECT_DIR',os.getcwd());os.chdir(pd) if os.path.exists(pd) else None;ce=all(os.path.exists(f) for f in ['rustfmt.toml','Cargo.toml','.cargo/config.toml']);r={} if not ce else {n:subprocess.run(cmd,capture_output=True,text=True,timeout=60) for n,cmd in [('fmt',['cargo','fmt','--','--check']),('clippy',['cargo','clippy','--','-D','warnings']),('check',['cargo','check'])]};ap=ce and all(x.returncode==0 for x in r.values());gs='[OK] PASSED' if ap else '[FAIL] FAILED';fs='[OK]' if ce and r.get('fmt',type('',(),{'returncode':1})).returncode==0 else '[FAIL]';cs='[OK]' if ce and r.get('clippy',type('',(),{'returncode':1})).returncode==0 else '[FAIL]';cks='[OK]' if ce and r.get('check',type('',(),{'returncode':1})).returncode==0 else '[FAIL]';print(f'Quality Gate: {gs} - Format: {fs}, Clippy: {cs}, Check: {cks}');print(json.dumps({'hookSpecificOutput':{'hookEventName':'Stop','qualityGateStatus':'passed' if ap else 'failed','formatStatus':'passed' if ce and r.get('fmt',type('',(),{'returncode':1})).returncode==0 else 'failed','lintStatus':'passed' if ce and r.get('clippy',type('',(),{'returncode':1})).returncode==0 else 'failed','checkStatus':'passed' if ce and r.get('check',type('',(),{'returncode':1})).returncode==0 else 'failed','configsExist':ce}}))\""
```

## Testing Hooks

### Manual Testing
```bash
# Test Python version
cd /path/to/project
python3 .claude/hooks/quality_gate.py

# Test shell version  
cd /path/to/project
./.claude/hooks/quality_gate.sh

# Test inline version (requires environment setup)
export CLAUDE_PROJECT_DIR=/path/to/project
# Run the inline command...
```

### Expected Output Format
```
Quality Gate: [FAIL] FAILED - Format: [FAIL], Clippy: [FAIL], Check: [OK]
{"hookSpecificOutput": {"hookEventName": "Stop", "qualityGateStatus": "failed", "formatStatus": "failed", "lintStatus": "failed", "checkStatus": "passed", "configsExist": true, "timestamp": 1754270507}}
```

### Hook Execution Flow
1. **Environment Check**: Verify `CLAUDE_PROJECT_DIR` and change directory
2. **Config Validation**: Check for required configuration files
3. **Quality Checks**: Run format, clippy, and check commands in sequence
4. **Status Reporting**: Generate human-readable status line
5. **JSON Output**: Provide structured data for Claude Code integration

## Troubleshooting

### Common Issues

#### 1. Permission Denied
```bash
chmod +x .claude/hooks/quality_gate.py
chmod +x .claude/hooks/quality_gate.sh
```

#### 2. Python/Bash Not Found
- **Python**: Ensure `python3` is in PATH
- **Bash**: Ensure `/bin/bash` exists (standard on Linux/macOS)

#### 3. Cargo Commands Fail
- **Solution**: Ensure you're in a valid Rust project directory
- **Check**: `cargo --version` should work
- **Verify**: Required config files exist

#### 4. Hook Not Triggering
- **JSON Syntax**: Validate `.claude/settings.json` syntax
- **File Paths**: Ensure hook scripts exist and are executable  
- **Environment**: Verify `CLAUDE_PROJECT_DIR` is set correctly

#### 5. Timeout Issues
- **Increase Timeout**: Set higher timeout value in settings.json
- **Check Performance**: Large projects may need more time
- **Network Issues**: Ensure cargo can download dependencies if needed

### Debugging Steps
1. **Test Manually**: Run hook scripts directly to verify they work
2. **Check Logs**: Look for error messages in Claude Code output
3. **Validate JSON**: Use `jq` to validate settings.json syntax
4. **File Permissions**: Ensure all files are readable/executable
5. **Environment Variables**: Check `CLAUDE_PROJECT_DIR` is correct

## Hook Output Specifications

### JSON Schema
```json
{
  "hookSpecificOutput": {
    "hookEventName": "Stop",
    "qualityGateStatus": "passed|failed|skipped",
    "formatStatus": "passed|failed",
    "lintStatus": "passed|failed", 
    "checkStatus": "passed|failed",
    "configsExist": boolean,
    "timestamp": number,
    "detailedResults": [...] // Python version only
  }
}
```

### Status Values
- **passed**: Check completed successfully
- **failed**: Check completed with errors
- **skipped**: Check was not run (missing configs)

## Performance Characteristics

| Version | Execution Time | Memory Usage | Output Detail |
|---------|---------------|--------------|---------------|
| Python  | 10-15s        | ~50MB        | Comprehensive |
| Shell   | 5-8s          | ~10MB        | Standard      |
| Inline  | 8-12s         | ~30MB        | Minimal       |

## Security Considerations

### Safe Execution
- All scripts use absolute paths
- No user input evaluation
- Timeout protection against hanging processes
- Error handling for all subprocess calls

### File Access
- Read-only access to source files
- No modification of project files
- Secure temporary file handling
- Proper cleanup on errors

## Integration with Existing Hooks

### Hook Execution Order
1. **PreToolUse**: Blocks protected file modifications
2. **PostToolUse**: Auto-formats, runs clippy, runs cargo check  
3. **Stop**: Final comprehensive quality gate ← **THIS HOOK**
4. **SessionStart**: Quality standards reminder

### Coordination with Other Hooks
- **Post-edit hooks**: Handle individual file changes
- **Stop hook**: Validates entire project state
- **Protection hooks**: Prevent configuration tampering
- **Session hooks**: Provide quality reminders

## Maintenance

### Regular Updates
- **Monthly**: Update Rust toolchain compatibility
- **Per Release**: Adjust for new clippy rules
- **As Needed**: Modify timeout values based on project size

### Performance Monitoring
- **Metrics**: Track execution times and failure rates
- **Optimization**: Adjust timeouts and parallel execution
- **Scaling**: Consider distributed checking for large projects

### Quality Improvements
- **Error Messages**: Enhance diagnostic output
- **Recovery**: Add automatic fix suggestions
- **Reporting**: Generate quality trend reports

---

## Quick Reference

### Enable Hook
✅ Already enabled in your `.claude/settings.json`

### Disable Hook
```json
"Stop": []
```

### Switch to Shell Version
```json
"command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/quality_gate.sh\""
```

### Emergency Bypass (Not Recommended)
Temporarily comment out the Stop hook section in settings.json, but this defeats the purpose of maintaining code quality.

---

*This documentation covers the complete Claude Code quality gate hook system for Rust projects. The hooks are designed to maintain enterprise-grade code quality while providing clear feedback and debugging capabilities.*