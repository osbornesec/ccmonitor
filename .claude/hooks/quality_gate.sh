#!/bin/bash

# Claude Code Hook: Rust Quality Gate Checker (Shell Script Version)
# Fast and simple quality gates implementation

set -euo pipefail

# Configuration
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
TIMEOUT=60
REQUIRED_CONFIGS=("rustfmt.toml" "Cargo.toml" ".cargo/config.toml")

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Change to project directory
cd "$PROJECT_DIR" 2>/dev/null || {
    echo "[WARN] Project directory not found: $PROJECT_DIR" >&2
    exit 1
}

# Check if all required config files exist
check_configs() {
    local all_exist=true
    for config in "${REQUIRED_CONFIGS[@]}"; do
        if [[ ! -f "$config" ]]; then
            echo "[WARN] Missing configuration file: $config" >&2
            all_exist=false
        fi
    done
    
    if [[ "$all_exist" == "false" ]]; then
        echo "Quality Gate: [SKIP] SKIPPED - Configuration files missing"
        echo '{"hookSpecificOutput": {"hookEventName": "Stop", "qualityGateStatus": "skipped", "configsExist": false}}'
        exit 0
    fi
    
    return 0
}

# Run a single quality check
run_check() {
    local name="$1"
    shift
    local cmd=("$@")
    
    echo -n "Running $name check... "
    
    if timeout "$TIMEOUT" "${cmd[@]}" >/dev/null 2>&1; then
        echo -e "${GREEN}[OK]${NC}"
        return 0
    else
        echo -e "${RED}[FAIL]${NC}"
        return 1
    fi
}

# Main execution
main() {
    echo "=== Rust Quality Gate Check ==="
    
    # Check configuration files
    check_configs
    
    # Initialize status tracking
    local format_status="failed"
    local clippy_status="failed" 
    local check_status="failed"
    local overall_status="failed"
    
    # Run format check
    if run_check "Format" cargo fmt -- --check; then
        format_status="passed"
    fi
    
    # Run clippy check
    if run_check "Clippy" cargo clippy -- -D warnings; then
        clippy_status="passed"
    fi
    
    # Run compilation check
    if run_check "Check" cargo check; then
        check_status="passed"
    fi
    
    # Determine overall status
    if [[ "$format_status" == "passed" && "$clippy_status" == "passed" && "$check_status" == "passed" ]]; then
        overall_status="passed"
    fi
    
    # Format status display
    local gate_display="[FAIL] FAILED"
    if [[ "$overall_status" == "passed" ]]; then
        gate_display="[OK] PASSED"
    fi
    
    local format_display="[FAIL]"
    if [[ "$format_status" == "passed" ]]; then
        format_display="[OK]"
    fi
    
    local clippy_display="[FAIL]"
    if [[ "$clippy_status" == "passed" ]]; then
        clippy_display="[OK]"
    fi
    
    local check_display="[FAIL]"
    if [[ "$check_status" == "passed" ]]; then
        check_display="[OK]"
    fi
    
    # Print status line
    echo "Quality Gate: $gate_display - Format: $format_display, Clippy: $clippy_display, Check: $check_display"
    
    # Output JSON for Claude Code hook
    cat <<EOF
{"hookSpecificOutput": {"hookEventName": "Stop", "qualityGateStatus": "$overall_status", "formatStatus": "$format_status", "lintStatus": "$clippy_status", "checkStatus": "$check_status", "configsExist": true, "timestamp": $(date +%s)}}
EOF
}

# Execute main function
main "$@"