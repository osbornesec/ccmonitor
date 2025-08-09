# AST Tools Installation & Usage Guide for AI Coding Assistants

A comprehensive guide to installing and using Abstract Syntax Tree (AST) tools that enhance AI coding assistant capabilities for understanding and analyzing codebases.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Universal Tools](#universal-tools)
4. [Language-Specific Tools](#language-specific-tools)
5. [AI Assistant Integration](#ai-assistant-integration)
6. [Configuration & Best Practices](#configuration--best-practices)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Usage](#advanced-usage)

## Overview

This guide focuses on tools that provide the highest value for AI coding assistants to understand codebases across multiple programming languages. The tools are prioritized by impact and ease of integration.

### Why AST Tools for AI Assistants?

- **Structural Understanding**: AI can understand code structure beyond text patterns
- **Semantic Accuracy**: Precise code analysis vs. regex-based matching
- **Multi-language Support**: Consistent APIs across different programming languages
- **Real-time Analysis**: Fast enough for interactive development workflows

## Quick Start

### Essential Installation (5 minutes)

```bash
# Install the two most impactful tools
npm install -g tree-sitter-cli
cargo install ast-grep --locked

# Verify installation
tree-sitter --version
ast-grep --version
```

### Basic Usage Test

```bash
# Test Tree-sitter with a sample file
echo "function hello() { return 'world'; }" > test.js
tree-sitter parse test.js

# Test ast-grep pattern matching
ast-grep -l javascript 'function $NAME() { $$$ }' test.js
```

## Universal Tools

### 1. Tree-sitter CLI

**Purpose**: Universal incremental parser for any programming language
**Best for**: Real-time syntax analysis, editor integration, structural navigation

#### Installation

```bash
# Method 1: npm (recommended)
npm install -g tree-sitter-cli

# Method 2: Cargo (Rust)
cargo install --locked tree-sitter-cli

# Method 3: Homebrew (macOS/Linux)
brew install tree-sitter

# Method 4: Download binary
# Visit: https://github.com/tree-sitter/tree-sitter/releases
```

#### Prerequisites

- **Node.js**: Required for parser generation
- **C/C++ compiler**: For building parsers (gcc, clang, or MSVC)
- **Git**: For downloading language grammars

#### Basic Usage

```bash
# Parse a file and show syntax tree
tree-sitter parse filename.py

# Parse multiple files
tree-sitter parse src/**/*.js

# Generate parser from grammar (for grammar development)
tree-sitter generate

# Test parser with test cases
tree-sitter test

# Interactive playground (web interface)
tree-sitter playground
```

#### Language Grammar Setup

```bash
# Clone popular language grammars
git clone https://github.com/tree-sitter/tree-sitter-python
git clone https://github.com/tree-sitter/tree-sitter-javascript
git clone https://github.com/tree-sitter/tree-sitter-typescript
git clone https://github.com/tree-sitter/tree-sitter-go
git clone https://github.com/tree-sitter/tree-sitter-rust

# Build a grammar (inside grammar directory)
cd tree-sitter-python
tree-sitter generate
tree-sitter test
```

#### AI Assistant Integration Example

```python
# Python example using py-tree-sitter
from tree_sitter import Language, Parser
import tree_sitter_python as tspython

# Load language
PY_LANGUAGE = Language(tspython.language(), "python")
parser = Parser()
parser.set_language(PY_LANGUAGE)

# Parse code
code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""

tree = parser.parse(bytes(code, "utf8"))

# Query for function definitions
query = PY_LANGUAGE.query("""
(function_definition
  name: (identifier) @function.name
  parameters: (parameters) @function.params)
""")

matches = query.captures(tree.root_node)
for node, capture_name in matches:
    print(f"{capture_name}: {node.text.decode('utf8')}")
```

### 2. ast-grep

**Purpose**: Universal code search, analysis, and transformation using AST patterns
**Best for**: Structural code search, linting, automated refactoring

#### Installation

```bash
# Method 1: Cargo (recommended)
cargo install ast-grep --locked

# Method 2: Homebrew
brew install ast-grep

# Method 3: npm
npm install -g @ast-grep/cli

# Method 4: pip
pip install ast-grep-cli

# Method 5: Nix
nix-shell -p ast-grep

# Verify installation
ast-grep --version
# or
sg --version
```

#### Basic Usage

```bash
# Search for patterns in code
ast-grep -l javascript 'if ($condition) { $$$ }' src/

# Find all function calls
ast-grep -l python '$func($$$)' .

# Search with context
ast-grep -l typescript 'interface $name { $$$ }' --context 3

# Replace patterns
ast-grep -l python 'print($arg)' -r 'console.log($arg)' --interactive

# Count matches
ast-grep -l go 'func $name($$$) { $$$ }' --json | jq length
```

#### Project Setup for Advanced Usage

```bash
# Initialize ast-grep project
cd your-project
ast-grep new

# Follow prompts to set up:
# - Rule directory (rules/)
# - Test directory (rule-tests/)
# - Configuration file (sgconfig.yml)

# Project structure created:
# your-project/
# ├── sgconfig.yml      # Configuration
# ├── rules/            # Custom rules
# ├── rule-tests/       # Rule tests
# └── utils/            # Utility rules
```

#### Custom Rules Example

Create `rules/no-console-log.yml`:

```yaml
id: no-console-log
message: Avoid using console.log in production
severity: warning
language: typescript
rule:
  pattern: console.log($$$)
  inside:
    not:
      pattern: |
        if (process.env.NODE_ENV === 'development') {
          $$$
        }
```

Run custom rules:

```bash
# Scan with all rules
ast-grep scan

# Scan specific rule
ast-grep scan --rule no-console-log

# Fix automatically
ast-grep scan --fix
```

#### AI Assistant Integration Patterns

```bash
# Extract all function signatures for AI context
ast-grep -l python 'def $name($params): $$$' --json > functions.json

# Find complex functions (AI review candidates)
ast-grep -l javascript 'function $name($$$) { $body }' --where 'body.length > 50'

# Identify code patterns for AI analysis
ast-grep -l typescript 'class $name extends $base { $$$ }' --format '$name -> $base'
```

## Language-Specific Tools

### 3. Babel Parser (JavaScript/TypeScript)

**Purpose**: Industry-standard JavaScript/TypeScript AST parsing
**Best for**: Modern JS/TS syntax, JSX, experimental features

#### Installation

```bash
# Core packages
npm install @babel/parser @babel/traverse @babel/types

# Optional: Code generation
npm install @babel/generator

# Global installation for CLI usage
npm install -g @babel/cli @babel/core
```

#### Basic Usage

```javascript
const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;
const generate = require("@babel/generator").default;

// Parse code with TypeScript support
const code = `
const greet = (name: string): string => {
  return \`Hello, \${name}!\`;
};
`;

const ast = parser.parse(code, {
  sourceType: "module",
  plugins: [
    "typescript",
    "jsx",
    "decorators-legacy",
    "classProperties"
  ]
});

// Traverse and analyze
traverse(ast, {
  FunctionDeclaration(path) {
    console.log("Function:", path.node.id.name);
  },
  ArrowFunctionExpression(path) {
    console.log("Arrow function found");
  },
  TSTypeAnnotation(path) {
    console.log("Type annotation:", path.node.typeAnnotation);
  }
});

// Generate code back
const output = generate(ast);
console.log(output.code);
```

#### Advanced Analysis Example

```javascript
const fs = require('fs');
const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;

// Analyze a whole project
function analyzeProject(directory) {
  const analysis = {
    functions: [],
    imports: [],
    exports: [],
    types: []
  };

  // Read all JS/TS files
  const files = getJSFiles(directory);
  
  files.forEach(file => {
    const code = fs.readFileSync(file, 'utf8');
    const ast = parser.parse(code, {
      sourceType: "module",
      plugins: ["typescript", "jsx"]
    });

    traverse(ast, {
      FunctionDeclaration(path) {
        analysis.functions.push({
          name: path.node.id.name,
          file: file,
          params: path.node.params.length,
          async: path.node.async
        });
      },
      ImportDeclaration(path) {
        analysis.imports.push({
          source: path.node.source.value,
          file: file
        });
      },
      TSInterfaceDeclaration(path) {
        analysis.types.push({
          name: path.node.id.name,
          file: file
        });
      }
    });
  });

  return analysis;
}
```

### 4. Semgrep (Multi-language Static Analysis)

**Purpose**: Pattern-based static analysis across 30+ languages
**Best for**: Security analysis, code quality, custom pattern detection

#### Installation

```bash
# Method 1: pip (recommended)
python3 -m pip install semgrep

# Method 2: Homebrew
brew install semgrep

# Method 3: Docker
docker pull returntocorp/semgrep

# Method 4: Binary download
# Visit: https://github.com/returntocorp/semgrep/releases

# Verify installation
semgrep --version
```

#### Basic Usage

```bash
# Scan with built-in rules
semgrep --config=auto .

# Language-specific scans
semgrep --config=python .
semgrep --config=javascript .
semgrep --config=go .

# Security-focused scan
semgrep --config=p/security-audit .

# Performance scan
semgrep --config=p/performance .

# Custom pattern
semgrep --pattern 'requests.get($URL, verify=False)' --lang python .
```

#### Custom Rules

Create `custom-rules.yml`:

```yaml
rules:
  - id: hardcoded-secret
    pattern: |
      password = "$VALUE"
    message: Hardcoded password detected
    languages: [python, javascript]
    severity: ERROR

  - id: sql-injection-risk
    patterns:
      - pattern: |
          cursor.execute($QUERY)
      - pattern-inside: |
          $QUERY = $USER_INPUT + ...
    message: Potential SQL injection
    languages: [python]
    severity: WARNING

  - id: missing-error-handling
    pattern: |
      try:
        $...BODY
      except:
        pass
    message: Empty except block - add proper error handling
    languages: [python]
    severity: INFO
```

Run custom rules:

```bash
semgrep --config=custom-rules.yml .
```

#### AI Assistant Integration

```bash
# Generate analysis reports for AI
semgrep --config=auto --json --output=analysis.json .

# Extract patterns for AI learning
semgrep --config=p/security-audit --sarif --output=security.sarif .

# Continuous analysis
semgrep ci --config=auto
```

## AI Assistant Integration

### Integration Strategies

#### 1. Automated Codebase Analysis

```bash
#!/bin/bash
# analyze-codebase.sh - Generate comprehensive codebase analysis for AI

echo "Generating codebase analysis for AI assistant..."

# Create analysis directory
mkdir -p .ai-analysis

# Tree-sitter structure analysis
echo "Analyzing code structure with Tree-sitter..."
find . -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.go" | \
  head -100 | \
  xargs -I {} tree-sitter parse {} > .ai-analysis/structure.txt

# ast-grep pattern extraction
echo "Extracting patterns with ast-grep..."
ast-grep -l python 'class $name: $$$' --json > .ai-analysis/python-classes.json
ast-grep -l javascript 'function $name($args) { $$$ }' --json > .ai-analysis/js-functions.json
ast-grep -l typescript 'interface $name { $$$ }' --json > .ai-analysis/ts-interfaces.json

# Semgrep analysis
echo "Running static analysis with Semgrep..."
semgrep --config=auto --json --output=.ai-analysis/semgrep-analysis.json .

# Generate summary
echo "Analysis complete. Files generated in .ai-analysis/"
ls -la .ai-analysis/
```

#### 2. Real-time Code Understanding

```python
# ai-code-assistant.py - Real-time code analysis for AI
import json
import subprocess
from pathlib import Path

class CodebaseAnalyzer:
    def __init__(self, project_path):
        self.project_path = Path(project_path)
        
    def analyze_file(self, file_path):
        """Analyze a single file with multiple tools"""
        analysis = {}
        
        # Tree-sitter parsing
        try:
            result = subprocess.run(
                ['tree-sitter', 'parse', str(file_path)],
                capture_output=True, text=True
            )
            analysis['structure'] = result.stdout
        except Exception as e:
            analysis['structure'] = f"Error: {e}"
            
        # ast-grep pattern extraction
        try:
            result = subprocess.run(
                ['ast-grep', '-l', self._get_language(file_path), 
                 'function $name($$$) { $$$ }', str(file_path), '--json'],
                capture_output=True, text=True
            )
            analysis['patterns'] = json.loads(result.stdout) if result.stdout else []
        except Exception as e:
            analysis['patterns'] = []
            
        return analysis
    
    def _get_language(self, file_path):
        """Determine language from file extension"""
        suffix = file_path.suffix
        mapping = {
            '.py': 'python',
            '.js': 'javascript', 
            '.ts': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
            '.java': 'java'
        }
        return mapping.get(suffix, 'text')
    
    def get_project_overview(self):
        """Generate high-level project analysis"""
        overview = {
            'languages': self._detect_languages(),
            'structure': self._analyze_structure(),
            'patterns': self._extract_common_patterns()
        }
        return overview
    
    def _detect_languages(self):
        """Detect programming languages in project"""
        languages = {}
        for file_path in self.project_path.rglob('*'):
            if file_path.is_file():
                lang = self._get_language(file_path)
                if lang != 'text':
                    languages[lang] = languages.get(lang, 0) + 1
        return languages

# Usage example
analyzer = CodebaseAnalyzer('/path/to/project')
overview = analyzer.get_project_overview()
print(json.dumps(overview, indent=2))
```

#### 3. Workflow Integration

```bash
# .ai-assistant/config.sh - Configuration for AI tools

# Tool locations
export TREE_SITTER_CLI="tree-sitter"
export AST_GREP_CLI="ast-grep"
export SEMGREP_CLI="semgrep"

# Common analysis patterns
alias analyze-functions="ast-grep -l auto 'function \$name(\$\$\$) { \$\$\$ }' --json"
alias analyze-classes="ast-grep -l auto 'class \$name { \$\$\$ }' --json"
alias analyze-imports="ast-grep -l auto 'import \$\$\$ from \$source' --json"

# Project analysis shortcuts
alias project-overview="bash ~/.ai-assistant/analyze-project.sh"
alias security-scan="semgrep --config=p/security-audit --json"
alias code-quality="semgrep --config=p/code-quality --json"

# Real-time file analysis
function analyze-file() {
    local file="$1"
    echo "=== Tree-sitter Analysis ==="
    tree-sitter parse "$file"
    echo -e "\n=== Pattern Analysis ==="
    ast-grep -l auto 'function $name($$$) { $$$ }' "$file"
    echo -e "\n=== Security Check ==="
    semgrep --config=p/security-audit "$file"
}
```

## Configuration & Best Practices

### Tree-sitter Configuration

Create `~/.tree-sitter/config.json`:

```json
{
  "parser-directories": [
    "/home/user/.tree-sitter/parsers",
    "/usr/local/lib/tree-sitter-parsers"
  ],
  "theme": {
    "keyword": "bold blue",
    "string": "green",
    "comment": "gray"
  }
}
```

### ast-grep Project Configuration

Create `sgconfig.yml`:

```yaml
# Global configuration for ast-grep
ruleDirs: ["rules", "team-rules"]
testDirs: ["rule-tests"]
utilDirs: ["utils"]

# Language specific settings
languages:
  typescript:
    extensions: [".ts", ".tsx"]
    
  javascript:
    extensions: [".js", ".jsx", ".mjs"]
    
  python:
    extensions: [".py", ".pyx"]

# Output formatting
outputFormat: "github"
```

### Semgrep Configuration

Create `.semgrep.yml`:

```yaml
# Semgrep configuration
rules:
  - paths:
      include:
        - "*.py"
        - "*.js"
        - "*.ts"
      exclude:
        - "test_*.py"
        - "*.test.js"
        - "node_modules/"
        - ".git/"
        
auto_fix: false
quiet: false
json: false
```

### Performance Optimization

#### Parallel Processing

```bash
# Parallel analysis with GNU parallel
find . -name "*.py" | parallel -j8 tree-sitter parse {}

# Parallel ast-grep analysis
find . -name "*.js" | parallel -j4 ast-grep -l javascript 'function $name($$$) {}' {}
```

#### Selective Analysis

```bash
# Only analyze changed files (git)
git diff --name-only HEAD~1 | grep -E '\.(py|js|ts)$' | xargs ast-grep scan

# Analyze by file size (skip large files)
find . -name "*.py" -size -100k | xargs semgrep --config=auto
```

### Memory Management

```bash
# Limit memory usage for large projects
export NODE_OPTIONS="--max-old-space-size=4096"  # For Tree-sitter
ulimit -v 8000000  # Limit virtual memory to 8GB
```

## Troubleshooting

### Common Installation Issues

#### Tree-sitter Issues

```bash
# Node.js version compatibility
node --version  # Should be >= 16.0.0

# Rebuild parsers if needed
cd ~/.tree-sitter/parsers
tree-sitter generate

# Clear cache
rm -rf ~/.tree-sitter/cache
```

#### ast-grep Issues

```bash
# Rust compilation issues
rustc --version  # Should be >= 1.70.0
cargo install --force ast-grep

# Permission issues
sudo chown -R $USER ~/.cargo
```

#### Semgrep Issues

```bash
# Python version check
python3 --version  # Should be >= 3.8

# Virtual environment installation
python3 -m venv semgrep-env
source semgrep-env/bin/activate
pip install semgrep
```

### Performance Issues

#### Large Project Optimization

```bash
# Use .gitignore patterns
ast-grep scan --respect-gitignore

# Limit file types
semgrep --include="*.py" --include="*.js" .

# Exclude directories
tree-sitter parse --exclude node_modules --exclude .git
```

#### Memory Usage

```bash
# Monitor memory usage
top -p $(pgrep tree-sitter)
htop -p $(pgrep ast-grep)

# Streaming analysis for large files
split -l 1000 large_file.py temp_chunk_
for chunk in temp_chunk_*; do
    tree-sitter parse "$chunk"
done
rm temp_chunk_*
```

### Platform-Specific Issues

#### Windows (WSL Recommended)

```powershell
# Install WSL2
wsl --install

# Use WSL for better compatibility
wsl -d Ubuntu-20.04
cd /mnt/c/your-project
```

#### macOS

```bash
# Xcode command line tools
xcode-select --install

# Homebrew permissions
sudo chown -R $(whoami) /usr/local/Homebrew
```

## Advanced Usage

### Custom Tool Integration

#### VS Code Extension Setup

Create `.vscode/settings.json`:

```json
{
  "astGrep.enable": true,
  "astGrep.serverPath": "/usr/local/bin/ast-grep",
  "treeSitter.enable": true,
  "semgrep.enable": true,
  "semgrep.configPath": ".semgrep.yml"
}
```

#### Vim/Neovim Integration

```lua
-- Tree-sitter setup for Neovim
require'nvim-treesitter.configs'.setup {
  ensure_installed = {"python", "javascript", "typescript", "go", "rust"},
  auto_install = true,
  highlight = {
    enable = true,
    additional_vim_regex_highlighting = false,
  },
  indent = {
    enable = true
  }
}
```

### CI/CD Integration

#### GitHub Actions

Create `.github/workflows/ast-analysis.yml`:

```yaml
name: AST Analysis
on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install AST tools
        run: |
          npm install -g tree-sitter-cli
          cargo install ast-grep
          pip install semgrep
          
      - name: Run analysis
        run: |
          tree-sitter parse src/ > structure-analysis.txt
          ast-grep scan --json > pattern-analysis.json
          semgrep --config=auto --json > security-analysis.json
          
      - name: Upload analysis
        uses: actions/upload-artifact@v3
        with:
          name: ast-analysis
          path: |
            structure-analysis.txt
            pattern-analysis.json
            security-analysis.json
```

### Custom Rule Development

#### Complex ast-grep Rules

```yaml
# rules/complex-validation.yml
id: require-error-handling
message: Functions should include error handling
severity: warning
language: python
rule:
  all:
    - pattern: |
        def $func($$$):
          $$$body
    - inside:
        not:
          any:
            - pattern: "try: $$$"
            - pattern: "except $$$: $$$"
            - pattern: "raise $$$"
  where:
    body.length > 5
```

#### Advanced Semgrep Patterns

```yaml
# Advanced pattern matching
rules:
  - id: complex-api-pattern
    patterns:
      - pattern-either:
          - pattern: |
              async def $FUNC(...):
                ...
                response = requests.$METHOD(...)
                ...
          - pattern: |
              def $FUNC(...):
                ...
                response = requests.$METHOD(...)
                ...
      - pattern-inside: |
          class $CLASS:
            ...
      - pattern-not: |
          try:
            ...
            response = requests.$METHOD(...)
            ...
          except requests.RequestException:
            ...
    message: API calls should be wrapped in proper exception handling
    languages: [python]
    severity: WARNING
```

### Performance Benchmarking

```bash
#!/bin/bash
# benchmark-tools.sh - Compare AST tool performance

PROJECT_DIR="/path/to/large/project"
RESULTS_FILE="benchmark-results.txt"

echo "AST Tools Performance Benchmark" > $RESULTS_FILE
echo "Project: $PROJECT_DIR" >> $RESULTS_FILE
echo "Date: $(date)" >> $RESULTS_FILE
echo "=========================" >> $RESULTS_FILE

# Tree-sitter benchmark
echo "Tree-sitter parsing..." >> $RESULTS_FILE
time (find $PROJECT_DIR -name "*.py" | head -100 | xargs tree-sitter parse > /dev/null) 2>> $RESULTS_FILE

# ast-grep benchmark
echo "ast-grep analysis..." >> $RESULTS_FILE
time (ast-grep -l python 'def $name($$$): $$$' $PROJECT_DIR > /dev/null) 2>> $RESULTS_FILE

# Semgrep benchmark
echo "Semgrep analysis..." >> $RESULTS_FILE
time (semgrep --config=auto $PROJECT_DIR > /dev/null) 2>> $RESULTS_FILE

echo "Benchmark complete. Results in $RESULTS_FILE"
```

This comprehensive guide provides everything needed to set up and effectively use AST tools for enhancing AI coding assistant capabilities. The tools work together to provide a complete understanding of codebase structure, patterns, and quality across multiple programming languages.