#!/usr/bin/env python3
"""
Test script for Claude Code hooks validation.
Validates hook configurations and tests execution.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple


class HookTester:
    """Comprehensive hook testing and validation."""

    def __init__(self, project_dir: str = None):
        """Initialize the hook tester."""
        self.project_dir = Path(project_dir or os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd()))
        self.claude_dir = self.project_dir / '.claude'
        self.hooks_dir = self.claude_dir / 'hooks'
        self.settings_file = self.claude_dir / 'settings.json'

    def validate_json_syntax(self) -> Tuple[bool, str]:
        """Validate settings.json syntax."""
        try:
            with open(self.settings_file, 'r') as f:
                json.load(f)
            return True, "✅ JSON syntax is valid"
        except json.JSONDecodeError as e:
            return False, f"❌ JSON syntax error: {e}"
        except FileNotFoundError:
            return False, f"❌ Settings file not found: {self.settings_file}"

    def validate_file_permissions(self) -> List[Tuple[bool, str]]:
        """Check file permissions for hook scripts."""
        results = []
        
        hook_files = [
            'quality_gate.py',
            'quality_gate.sh',
        ]
        
        for hook_file in hook_files:
            file_path = self.hooks_dir / hook_file
            if file_path.exists():
                if os.access(file_path, os.X_OK):
                    results.append((True, f"✅ {hook_file} is executable"))
                else:
                    results.append((False, f"❌ {hook_file} is not executable"))
            else:
                results.append((False, f"❌ {hook_file} not found"))
        
        return results

    def validate_hook_configuration(self) -> List[Tuple[bool, str]]:
        """Validate hook configuration in settings.json."""
        results = []
        
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
            
            # Check if hooks section exists
            if 'hooks' not in settings:
                results.append((False, "❌ No 'hooks' section in settings.json"))
                return results
            
            hooks = settings['hooks']
            
            # Check Stop hook
            if 'Stop' in hooks:
                stop_hooks = hooks['Stop']
                if stop_hooks and len(stop_hooks) > 0:
                    stop_hook = stop_hooks[0]
                    if 'hooks' in stop_hook and len(stop_hook['hooks']) > 0:
                        command_hook = stop_hook['hooks'][0]
                        if 'command' in command_hook:
                            command = command_hook['command']
                            if 'quality_gate' in command:
                                results.append((True, "✅ Stop hook configured with quality gate"))
                            else:
                                results.append((False, f"❌ Stop hook command doesn't reference quality gate: {command}"))
                        else:
                            results.append((False, "❌ Stop hook missing 'command' field"))
                    else:
                        results.append((False, "❌ Stop hook missing 'hooks' array"))
                else:
                    results.append((False, "❌ Stop hook array is empty"))
            else:
                results.append((False, "❌ No Stop hook configured"))
            
            # Check other important hooks
            important_hooks = ['PreToolUse', 'PostToolUse', 'UserPromptSubmit']
            for hook_name in important_hooks:
                if hook_name in hooks:
                    results.append((True, f"✅ {hook_name} hook configured"))
                else:
                    results.append((False, f"⚠️ {hook_name} hook not configured"))
            
        except Exception as e:
            results.append((False, f"❌ Error validating hook configuration: {e}"))
        
        return results

    def test_python_quality_gate(self) -> Tuple[bool, str, str]:
        """Test the Python quality gate script."""
        script_path = self.hooks_dir / 'quality_gate.py'
        
        if not script_path.exists():
            return False, "❌ quality_gate.py not found", ""
        
        try:
            # Set environment
            env = os.environ.copy()
            env['CLAUDE_PROJECT_DIR'] = str(self.project_dir)
            
            result = subprocess.run(
                ['python3', str(script_path)],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.project_dir),
                env=env
            )
            
            # Check if JSON output is valid
            lines = result.stdout.strip().split('\n')
            json_line = lines[-1] if lines else ""
            
            try:
                json_data = json.loads(json_line)
                if 'hookSpecificOutput' in json_data:
                    return True, "✅ Python quality gate executed successfully", result.stdout
                else:
                    return False, "❌ Python quality gate output missing hookSpecificOutput", result.stdout
            except json.JSONDecodeError:
                return False, f"❌ Python quality gate output invalid JSON: {json_line}", result.stdout
                
        except subprocess.TimeoutExpired:
            return False, "❌ Python quality gate timed out", ""
        except Exception as e:
            return False, f"❌ Python quality gate error: {e}", ""

    def test_shell_quality_gate(self) -> Tuple[bool, str, str]:
        """Test the shell quality gate script."""
        script_path = self.hooks_dir / 'quality_gate.sh'
        
        if not script_path.exists():
            return False, "❌ quality_gate.sh not found", ""
        
        try:
            # Set environment
            env = os.environ.copy()
            env['CLAUDE_PROJECT_DIR'] = str(self.project_dir)
            
            result = subprocess.run(
                ['bash', str(script_path)],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.project_dir),
                env=env
            )
            
            # Check if JSON output is valid
            lines = result.stdout.strip().split('\n')
            json_line = lines[-1] if lines else ""
            
            try:
                json_data = json.loads(json_line)
                if 'hookSpecificOutput' in json_data:
                    return True, "✅ Shell quality gate executed successfully", result.stdout
                else:
                    return False, "❌ Shell quality gate output missing hookSpecificOutput", result.stdout
            except json.JSONDecodeError:
                return False, f"❌ Shell quality gate output invalid JSON: {json_line}", result.stdout
                
        except subprocess.TimeoutExpired:
            return False, "❌ Shell quality gate timed out", ""
        except Exception as e:
            return False, f"❌ Shell quality gate error: {e}", ""

    def validate_rust_environment(self) -> List[Tuple[bool, str]]:
        """Validate Rust development environment."""
        results = []
        
        # Check Rust toolchain
        try:
            result = subprocess.run(['cargo', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                results.append((True, f"✅ Cargo available: {result.stdout.strip()}"))
            else:
                results.append((False, "❌ Cargo not available"))
        except FileNotFoundError:
            results.append((False, "❌ Cargo not found in PATH"))
        
        # Check required config files
        config_files = ['rustfmt.toml', 'Cargo.toml', '.cargo/config.toml']
        for config_file in config_files:
            config_path = self.project_dir / config_file
            if config_path.exists():
                results.append((True, f"✅ {config_file} exists"))
            else:
                results.append((False, f"❌ {config_file} missing"))
        
        return results

    def run_comprehensive_test(self) -> None:
        """Run all tests and display results."""
        print("🔍 Claude Code Hooks Validation")
        print("=" * 50)
        
        # JSON syntax validation
        print("\n📝 JSON Syntax Validation")
        success, message = self.validate_json_syntax()
        print(f"  {message}")
        
        # File permissions
        print("\n🔒 File Permissions")
        for success, message in self.validate_file_permissions():
            print(f"  {message}")
        
        # Hook configuration
        print("\n⚙️ Hook Configuration")
        for success, message in self.validate_hook_configuration():
            print(f"  {message}")
        
        # Rust environment
        print("\n🦀 Rust Environment")
        for success, message in self.validate_rust_environment():
            print(f"  {message}")
        
        # Python quality gate test
        print("\n🐍 Python Quality Gate Test")
        success, message, output = self.test_python_quality_gate()
        print(f"  {message}")
        if output and len(output.split('\n')) <= 5:
            print(f"  Output: {output.strip()}")
        
        # Shell quality gate test
        print("\n🐚 Shell Quality Gate Test") 
        success, message, output = self.test_shell_quality_gate()
        print(f"  {message}")
        if output and len(output.split('\n')) <= 5:
            print(f"  Output: {output.strip()}")
        
        print("\n" + "=" * 50)
        print("✅ Hook validation complete!")
        print("\n💡 Next Steps:")
        print("  1. Fix any ❌ issues shown above")
        print("  2. Test with: /hooks command in Claude Code")
        print("  3. Verify hooks trigger during Stop events")


def main():
    """Main entry point."""
    tester = HookTester()
    tester.run_comprehensive_test()


if __name__ == '__main__':
    main()