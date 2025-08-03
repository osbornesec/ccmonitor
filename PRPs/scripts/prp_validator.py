#!/usr/bin/env python3
"""
PRP Quality Validator with 4-Level Validation

Validates Product Requirement Prompts for completeness, TDD methodology,
context sufficiency, and implementation readiness.
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

try:
    import orjson as json_lib
    def json_loads(s): return json_lib.loads(s)
    def json_dumps(obj, **kwargs): return json_lib.dumps(obj).decode('utf-8')
except ImportError:
    import json as json_lib
    json_loads = json_lib.loads
    json_dumps = json_lib.dumps

@dataclass
class ValidationResult:
    """Result of PRP validation with detailed feedback"""
    passed: bool
    score: float  # 0-100
    issues: List[str]
    warnings: List[str]
    suggestions: List[str]
    level: str  # template, tdd, context, implementation

@dataclass
class PRPAnalysis:
    """Complete analysis of a PRP document"""
    sections: Dict[str, bool]  # Required sections present
    tdd_integration: bool
    context_completeness: float  # 0-100
    implementation_clarity: float  # 0-100
    validation_loops: int  # Number of validation levels
    total_score: float  # Overall quality score

class PRPValidator:
    """Comprehensive PRP quality validation system"""
    
    REQUIRED_SECTIONS = [
        'Goal', 'Why', 'What', 'All Needed Context', 
        'Implementation Blueprint', 'Validation Loop'
    ]
    
    TDD_KEYWORDS = [
        'test', 'tdd', 'red-green-refactor', 'failing test',
        'test-first', 'pytest', 'jest', 'coverage'
    ]
    
    CONTEXT_INDICATORS = [
        'file:', 'url:', 'pattern:', 'gotcha:', 'critical:',
        'example:', 'docfile:', 'why:'
    ]
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.validation_history = []
    
    def validate_prp(self, prp_path: Path) -> ValidationResult:
        """
        Validate a PRP file for quality and completeness
        
        Args:
            prp_path: Path to PRP markdown file
            
        Returns:
            ValidationResult with detailed validation feedback
        """
        try:
            content = prp_path.read_text(encoding='utf-8')
            analysis = self._analyze_prp_content(content)
            result = self._evaluate_analysis(analysis, prp_path.name)
            
            # Log validation for improvement tracking
            self._log_validation(prp_path, result, analysis)
            
            return result
            
        except Exception as e:
            return ValidationResult(
                passed=False,
                score=0.0,
                issues=[f"Failed to validate PRP: {str(e)}"],
                warnings=[],
                suggestions=["Check file format and accessibility"],
                level="error"
            )
    
    def validate_template(self, template_path: Path) -> ValidationResult:
        """Validate PRP template structure and completeness"""
        content = template_path.read_text(encoding='utf-8')
        
        issues = []
        warnings = []
        suggestions = []
        score = 100.0
        
        # Check template metadata
        if not content.startswith('name:'):
            issues.append("Template missing name metadata")
            score -= 20
        
        if 'description:' not in content:
            issues.append("Template missing description metadata")
            score -= 10
        
        # Check template sections
        for section in self.REQUIRED_SECTIONS:
            if f"## {section}" not in content:
                issues.append(f"Template missing required section: {section}")
                score -= 15
        
        # Check TDD integration
        tdd_count = sum(1 for keyword in self.TDD_KEYWORDS 
                       if keyword.lower() in content.lower())
        if tdd_count < 3:
            warnings.append("Template has limited TDD methodology integration")
            score -= 5
        
        # Check validation loop structure
        validation_levels = content.count('Level ')
        if validation_levels < 4:
            issues.append("Template missing 4-level validation structure")
            score -= 20
        
        return ValidationResult(
            passed=len(issues) == 0,
            score=max(0, score),
            issues=issues,
            warnings=warnings,
            suggestions=suggestions,
            level="template"
        )
    
    def _analyze_prp_content(self, content: str) -> PRPAnalysis:
        """Analyze PRP content for structure and quality indicators"""
        
        # Check required sections
        sections = {}
        for section in self.REQUIRED_SECTIONS:
            sections[section] = f"## {section}" in content
        
        # Analyze TDD integration
        tdd_count = sum(1 for keyword in self.TDD_KEYWORDS 
                       if keyword.lower() in content.lower())
        tdd_integration = tdd_count >= 5  # Threshold for good TDD integration
        
        # Analyze context completeness
        context_indicators = sum(1 for indicator in self.CONTEXT_INDICATORS 
                               if indicator in content)
        context_completeness = min(100.0, (context_indicators / 10) * 100)
        
        # Analyze implementation clarity
        implementation_indicators = [
            'task 1:', 'task 2:', 'implement:', 'follow pattern:',
            'dependencies:', 'placement:', 'naming:'
        ]
        impl_count = sum(1 for indicator in implementation_indicators 
                        if indicator.lower() in content.lower())
        implementation_clarity = min(100.0, (impl_count / 8) * 100)
        
        # Count validation levels
        validation_loops = content.count('Level ')
        
        # Calculate total score
        section_score = (sum(sections.values()) / len(sections)) * 40
        tdd_score = 20 if tdd_integration else 0  
        context_score = context_completeness * 0.25
        impl_score = implementation_clarity * 0.15
        total_score = section_score + tdd_score + context_score + impl_score
        
        return PRPAnalysis(
            sections=sections,
            tdd_integration=tdd_integration,
            context_completeness=context_completeness,
            implementation_clarity=implementation_clarity,
            validation_loops=validation_loops,
            total_score=total_score
        )
    
    def _evaluate_analysis(self, analysis: PRPAnalysis, filename: str) -> ValidationResult:
        """Evaluate PRP analysis and generate validation result"""
        
        issues = []
        warnings = []
        suggestions = []
        
        # Check required sections
        missing_sections = [section for section, present in analysis.sections.items() 
                          if not present]
        if missing_sections:
            issues.extend([f"Missing required section: {section}" 
                          for section in missing_sections])
        
        # Check TDD integration
        if not analysis.tdd_integration:
            issues.append("Insufficient TDD methodology integration")
            suggestions.append("Add more TDD keywords: tests, red-green-refactor, test-first")
        
        # Check context completeness
        if analysis.context_completeness < 50:
            issues.append("Insufficient context for implementation")
            suggestions.append("Add more context indicators: file paths, examples, gotchas")
        elif analysis.context_completeness < 75:
            warnings.append("Context could be more comprehensive")
        
        # Check implementation clarity
        if analysis.implementation_clarity < 60:
            issues.append("Implementation blueprint lacks clarity")
            suggestions.append("Add more task details, dependencies, and patterns")
        
        # Check validation loops
        if analysis.validation_loops < 4:
            issues.append("Missing 4-level validation loop structure")
            suggestions.append("Add Level 0-4 validation sections")
        elif analysis.validation_loops > 4:
            warnings.append("More than 4 validation levels may be overcomplicated")
        
        # Determine pass/fail
        passed = (len(issues) == 0 and 
                 analysis.total_score >= (90 if self.strict_mode else 70))
        
        return ValidationResult(
            passed=passed,
            score=analysis.total_score,
            issues=issues,
            warnings=warnings,
            suggestions=suggestions,
            level="comprehensive"
        )
    
    def _log_validation(self, prp_path: Path, result: ValidationResult, 
                       analysis: PRPAnalysis):
        """Log validation results for tracking and improvement"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'file': str(prp_path),
            'passed': result.passed,
            'score': result.score,
            'issues_count': len(result.issues),
            'warnings_count': len(result.warnings),
            'tdd_integration': analysis.tdd_integration,
            'context_completeness': analysis.context_completeness,
            'implementation_clarity': analysis.implementation_clarity,
            'validation_loops': analysis.validation_loops
        }
        
        log_file = Path('.claude/state/prp_validation.jsonl')
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json_dumps(log_entry) + '\n')

def generate_validation_report(results: List[Tuple[Path, ValidationResult]], 
                             output_path: Optional[Path] = None) -> str:
    """Generate comprehensive validation report"""
    
    total_prps = len(results)
    passed_prps = sum(1 for _, result in results if result.passed)
    avg_score = sum(result.score for _, result in results) / total_prps if total_prps > 0 else 0
    
    report = f"""
# PRP Validation Report
Generated: {datetime.now().isoformat()}

## Summary
- Total PRPs Validated: {total_prps}
- Passed Validation: {passed_prps} ({passed_prps/total_prps*100:.1f}%)
- Average Quality Score: {avg_score:.1f}/100

## Detailed Results
"""
    
    for prp_path, result in results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        report += f"\n### {prp_path.name} - {status} ({result.score:.1f}/100)\n"
        
        if result.issues:
            report += "**Issues:**\n"
            for issue in result.issues:
                report += f"- {issue}\n"
        
        if result.warnings:
            report += "**Warnings:**\n"
            for warning in result.warnings:
                report += f"- {warning}\n"
        
        if result.suggestions:
            report += "**Suggestions:**\n"
            for suggestion in result.suggestions:
                report += f"- {suggestion}\n"
    
    # Add improvement recommendations
    common_issues = {}
    for _, result in results:
        for issue in result.issues:
            common_issues[issue] = common_issues.get(issue, 0) + 1
    
    if common_issues:
        report += "\n## Common Issues\n"
        for issue, count in sorted(common_issues.items(), key=lambda x: x[1], reverse=True):
            report += f"- {issue} ({count} PRPs)\n"
    
    if output_path:
        output_path.write_text(report, encoding='utf-8')
        print(f"Report saved to: {output_path}")
    
    return report

def main():
    """Main CLI interface for PRP validation"""
    parser = argparse.ArgumentParser(description="Validate PRP quality and completeness")
    parser.add_argument('--prp', type=Path, help="Single PRP file to validate")
    parser.add_argument('--prps-dir', type=Path, default=Path('PRPs'), 
                       help="Directory containing PRPs to validate")
    parser.add_argument('--templates', action='store_true', 
                       help="Validate templates instead of PRPs")
    parser.add_argument('--strict', action='store_true', 
                       help="Use strict validation mode")
    parser.add_argument('--report', type=Path, 
                       help="Generate report and save to file")
    parser.add_argument('--json', action='store_true', 
                       help="Output results in JSON format")
    
    args = parser.parse_args()
    
    validator = PRPValidator(strict_mode=args.strict)
    results = []
    
    if args.prp:
        # Validate single PRP
        result = validator.validate_prp(args.prp)
        results.append((args.prp, result))
    elif args.templates:
        # Validate templates
        templates_dir = args.prps_dir / 'templates'
        if templates_dir.exists():
            for template_file in templates_dir.glob('*.md'):
                result = validator.validate_template(template_file)
                results.append((template_file, result))
    else:
        # Validate all PRPs in directory
        for prp_file in args.prps_dir.glob('*.md'):
            if not prp_file.name.startswith('README'):
                result = validator.validate_prp(prp_file)
                results.append((prp_file, result))
    
    if not results:
        print("No PRP files found to validate")
        return 1
    
    # Output results
    if args.json:
        json_results = []
        for prp_path, result in results:
            json_results.append({
                'file': str(prp_path),
                'passed': result.passed,
                'score': result.score,
                'issues': result.issues,
                'warnings': result.warnings,
                'suggestions': result.suggestions
            })
        print(json_dumps(json_results, indent=2))
    else:
        # Generate and display report
        report = generate_validation_report(results, args.report)
        if not args.report:
            print(report)
    
    # Exit with error code if any validation failed
    failed_count = sum(1 for _, result in results if not result.passed)
    return 1 if failed_count > 0 else 0

if __name__ == '__main__':
    sys.exit(main())