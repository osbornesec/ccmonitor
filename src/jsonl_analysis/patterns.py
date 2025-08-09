"""
Pattern recognition module for JSONL content analysis
Following TDD methodology - implementation based on test requirements
"""

import re
import logging
from typing import Dict, List, Any, Pattern, Set, Tuple
from collections import defaultdict
from abc import ABC, abstractmethod

from .exceptions import PatternDetectionError

logger = logging.getLogger(__name__)


class BasePatternDetector(ABC):
    """Abstract base class for pattern detectors"""
    
    def __init__(self):
        """Initialize detector with compiled patterns"""
        self._compiled_patterns = {}
        self._compile_patterns()
    
    @abstractmethod
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching"""
        pass
    
    @abstractmethod
    def detect_patterns(self, content: str) -> Dict[str, Any]:
        """Detect patterns in content"""
        pass
    
    def _match_pattern(self, content: str, pattern: Pattern) -> bool:
        """Check if content matches pattern"""
        return bool(pattern.search(content))
    
    def _calculate_confidence(self, matches: List[bool]) -> float:
        """Calculate confidence score based on pattern matches"""
        if not matches:
            return 0.0
        return sum(matches) / len(matches)


class CodePatternDetector(BasePatternDetector):
    """Detects code-related patterns in message content"""
    
    def _compile_patterns(self):
        """Compile code-related regex patterns"""
        self._compiled_patterns = {
            "file_modification": [
                re.compile(r'\b(edit|write|create|implement|add|update|modify|delete|refactor)\b', re.IGNORECASE),
                re.compile(r'\b(file|script|module|component)\b', re.IGNORECASE),
                re.compile(r'\.(py|js|ts|rs|go|java|cpp|c|h|php|rb|swift|kt|scala)[\s\'\"]', re.IGNORECASE)
            ],
            
            "function_creation": [
                re.compile(r'\bdef\s+\w+\s*\(', re.IGNORECASE),
                re.compile(r'\bfunction\s+\w+\s*\(', re.IGNORECASE),
                re.compile(r'\bclass\s+\w+', re.IGNORECASE),
                re.compile(r'\binterface\s+\w+', re.IGNORECASE),
                re.compile(r'\bstruct\s+\w+', re.IGNORECASE),
                re.compile(r'\bfn\s+\w+\s*\(', re.IGNORECASE),
                re.compile(r'\bpublic\s+(class|interface|function)', re.IGNORECASE),
                re.compile(r'\bimpl\s+\w+', re.IGNORECASE)
            ],
            
            "imports": [
                re.compile(r'\bimport\s+\w+', re.IGNORECASE),
                re.compile(r'\bfrom\s+\w+\s+import', re.IGNORECASE),
                re.compile(r'\brequire\s*\(', re.IGNORECASE),
                re.compile(r'\buse\s+\w+', re.IGNORECASE),
                re.compile(r'\busing\s+\w+', re.IGNORECASE),
                re.compile(r'#include\s*<\w+>', re.IGNORECASE)
            ],
            
            "programming_languages": {
                "python": re.compile(r'\b(def|import|from|class|if\s+__name__|\.py)\b', re.IGNORECASE),
                "javascript": re.compile(r'\b(function|const|let|var|require|\.js|=>)\b', re.IGNORECASE),
                "typescript": re.compile(r'\b(interface|type|\.ts|\.tsx)\b', re.IGNORECASE),
                "rust": re.compile(r'\b(fn|impl|use|struct|enum|\.rs)\b', re.IGNORECASE),
                "go": re.compile(r'\b(func|package|import|\.go)\b', re.IGNORECASE),
                "java": re.compile(r'\b(public\s+class|public\s+interface|\.java)\b', re.IGNORECASE),
                "c": re.compile(r'\b(#include|void|int\s+main|\.c)\b', re.IGNORECASE)
            }
        }
    
    def detect_patterns(self, content: str) -> Dict[str, Any]:
        """Detect code-related patterns in content"""
        patterns = {}
        
        # File modification patterns
        file_mod_matches = [self._match_pattern(content, p) for p in self._compiled_patterns["file_modification"]]
        patterns["file_modification"] = {
            "detected": any(file_mod_matches),
            "confidence": self._calculate_confidence(file_mod_matches),
            "matches": sum(file_mod_matches)
        }
        
        # Function creation patterns
        func_matches = [self._match_pattern(content, p) for p in self._compiled_patterns["function_creation"]]
        patterns["function_creation"] = {
            "detected": any(func_matches),
            "confidence": self._calculate_confidence(func_matches),
            "matches": sum(func_matches)
        }
        
        # Import patterns
        import_matches = [self._match_pattern(content, p) for p in self._compiled_patterns["imports"]]
        patterns["imports"] = {
            "detected": any(import_matches),
            "confidence": self._calculate_confidence(import_matches),
            "matches": sum(import_matches)
        }
        
        # Programming language detection
        detected_languages = []
        for lang, pattern in self._compiled_patterns["programming_languages"].items():
            if self._match_pattern(content, pattern):
                detected_languages.append(lang)
        
        patterns["programming_languages"] = {
            "detected": len(detected_languages) > 0,
            "languages": detected_languages,
            "count": len(detected_languages)
        }
        
        return patterns
    
    def detect_tool_patterns(self, tool_message: Dict[str, Any]) -> Dict[str, Any]:
        """Detect code-related patterns in tool calls"""
        patterns = {}
        
        tool_name = tool_message.get("tool", "")
        parameters = tool_message.get("parameters", {})
        
        # Code modification tools
        code_tools = {"Write", "Edit", "MultiEdit"}
        patterns["code_modification"] = {
            "detected": tool_name in code_tools,
            "confidence": 1.0 if tool_name in code_tools else 0.0,
            "tool": tool_name
        }
        
        # File path analysis
        file_path = parameters.get("file_path", "")
        if file_path:
            code_extensions = re.compile(r'\.(py|js|ts|rs|go|java|cpp|c|h|php|rb|swift)$', re.IGNORECASE)
            patterns["code_file"] = {
                "detected": bool(code_extensions.search(file_path)),
                "confidence": 1.0 if code_extensions.search(file_path) else 0.0,
                "file_path": file_path
            }
        
        return patterns


class ErrorPatternDetector(BasePatternDetector):
    """Detects error and solution patterns in message content"""
    
    def _compile_patterns(self):
        """Compile error-related regex patterns"""
        self._compiled_patterns = {
            "error_keywords": [
                re.compile(r'\b(error|exception|traceback|stack\s+trace)\b', re.IGNORECASE),
                re.compile(r'\b(failed|failure|crash|crashed|fatal)\b', re.IGNORECASE),
                re.compile(r'\b(bug|critical|severe|urgent)\b', re.IGNORECASE),
                re.compile(r'\b\w*Error\b|\b\w*Exception\b'),  # CamelCase errors
                re.compile(r'\b(nameerror|typeerror|indexerror|attributeerror|valueerror|keyerror)\b', re.IGNORECASE)
            ],
            
            "solution_keywords": [
                re.compile(r'\b(fix|fixed|resolve|resolved|solution)\b', re.IGNORECASE),
                re.compile(r'\b(patch|workaround|repair|correct)\b', re.IGNORECASE),
                re.compile(r'\b(debug|debugging|debugged)\b', re.IGNORECASE),
                re.compile(r'\bto\s+fix\b|\bthe\s+fix\b', re.IGNORECASE)
            ],
            
            "debugging_activity": [
                re.compile(r'\b(debug|debugging|investigate|analyze|trace)\b', re.IGNORECASE),
                re.compile(r'\b(breakpoint|step|print|console|log)\b', re.IGNORECASE),
                re.compile(r'\b(examine|inspect|check|verify)\b', re.IGNORECASE),
                re.compile(r'\b(reproduce|replicate|isolate)\b', re.IGNORECASE)
            ],
            
            "test_failure": [
                re.compile(r'\b(test\s+fail|failed\s+test|assertion\s*error)\b', re.IGNORECASE),
                re.compile(r'\b(unit\s+test|integration\s+test).*\b(fail|error)\b', re.IGNORECASE),
                re.compile(r'\b(pytest|jest|mocha).*\b(fail|error)\b', re.IGNORECASE),
                re.compile(r'\bexpected.*but\s+got\b', re.IGNORECASE)
            ]
        }
    
    def detect_patterns(self, content: str) -> Dict[str, Any]:
        """Detect error and solution patterns in content"""
        patterns = {}
        
        # Error keyword patterns
        error_matches = [self._match_pattern(content, p) for p in self._compiled_patterns["error_keywords"]]
        patterns["error_keywords"] = {
            "detected": any(error_matches),
            "confidence": min(1.0, self._calculate_confidence(error_matches) + 0.3),  # Boost confidence
            "matches": sum(error_matches)
        }
        
        # Solution keyword patterns
        solution_matches = [self._match_pattern(content, p) for p in self._compiled_patterns["solution_keywords"]]
        patterns["solution_keywords"] = {
            "detected": any(solution_matches),
            "confidence": self._calculate_confidence(solution_matches),
            "matches": sum(solution_matches)
        }
        
        # Debugging activity patterns
        debug_matches = [self._match_pattern(content, p) for p in self._compiled_patterns["debugging_activity"]]
        patterns["debugging_activity"] = {
            "detected": any(debug_matches),
            "confidence": self._calculate_confidence(debug_matches),
            "matches": sum(debug_matches)
        }
        
        # Test failure patterns
        test_matches = [self._match_pattern(content, p) for p in self._compiled_patterns["test_failure"]]
        patterns["test_failure"] = {
            "detected": any(test_matches),
            "confidence": self._calculate_confidence(test_matches),
            "matches": sum(test_matches)
        }
        
        return patterns


class ArchitecturalPatternDetector(BasePatternDetector):
    """Detects architectural and design decision patterns"""
    
    def _compile_patterns(self):
        """Compile architectural pattern regex"""
        self._compiled_patterns = {
            "design_patterns": [
                re.compile(r'\b(factory|singleton|observer|strategy|builder|decorator|adapter|facade)\s+pattern\b', re.IGNORECASE),
                re.compile(r'\b(mvc|mvp|mvvm|model.*view.*controller)\b', re.IGNORECASE),
                re.compile(r'\b(repository|service|dao|dto)\s+pattern\b', re.IGNORECASE)
            ],
            
            "architectural_decisions": [
                re.compile(r'\b(architecture|architectural)\s+(decision|choice|approach)\b', re.IGNORECASE),
                re.compile(r'\b(framework\s+choice|technology\s+choice|decided\s+to\s+use)\b', re.IGNORECASE),
                re.compile(r'\b(microservices|monolith|serverless|event.*driven)\b', re.IGNORECASE),
                re.compile(r'\b(database\s+design|api\s+design|system\s+design)\b', re.IGNORECASE)
            ],
            
            "technology_choices": [
                re.compile(r'\b(react\s+vs|angular\s+vs|vue\s+vs|django\s+vs|flask\s+vs)\b', re.IGNORECASE),
                re.compile(r'\b(mongodb\s+vs|postgresql\s+vs|mysql\s+vs)\b', re.IGNORECASE),
                re.compile(r'\b(aws\s+vs|azure\s+vs|gcp\s+vs)\b', re.IGNORECASE),
                re.compile(r'\bchoosing\s+between\b|\bchoice.*between\b', re.IGNORECASE)
            ],
            
            "system_design": [
                re.compile(r'\b(load\s+balancer|message\s+queue|caching\s+layer)\b', re.IGNORECASE),
                re.compile(r'\b(database\s+sharding|service\s+mesh|api\s+gateway)\b', re.IGNORECASE),
                re.compile(r'\b(event.*driven|async.*processing|scalability)\b', re.IGNORECASE),
                re.compile(r'\b(distributed\s+system|horizontal\s+scaling|vertical\s+scaling)\b', re.IGNORECASE)
            ]
        }
    
    def detect_patterns(self, content: str) -> Dict[str, Any]:
        """Detect architectural patterns in content"""
        patterns = {}
        
        # Design patterns
        design_matches = [self._match_pattern(content, p) for p in self._compiled_patterns["design_patterns"]]
        patterns["design_patterns"] = {
            "detected": any(design_matches),
            "confidence": self._calculate_confidence(design_matches),
            "matches": sum(design_matches)
        }
        
        # Architectural decisions
        arch_matches = [self._match_pattern(content, p) for p in self._compiled_patterns["architectural_decisions"]]
        patterns["architectural_decisions"] = {
            "detected": any(arch_matches),
            "confidence": self._calculate_confidence(arch_matches),
            "matches": sum(arch_matches)
        }
        
        # Technology choices
        tech_matches = [self._match_pattern(content, p) for p in self._compiled_patterns["technology_choices"]]
        patterns["technology_choices"] = {
            "detected": any(tech_matches),
            "confidence": self._calculate_confidence(tech_matches),
            "matches": sum(tech_matches)
        }
        
        # System design
        system_matches = [self._match_pattern(content, p) for p in self._compiled_patterns["system_design"]]
        patterns["system_design"] = {
            "detected": any(system_matches),
            "confidence": self._calculate_confidence(system_matches),
            "matches": sum(system_matches)
        }
        
        return patterns


class HookPatternDetector(BasePatternDetector):
    """Detects hook system and automation patterns"""
    
    def _compile_patterns(self):
        """Compile hook-related regex patterns"""
        self._compiled_patterns = {
            "hook_execution": [
                re.compile(r'\bhook\b:?\s*\w+', re.IGNORECASE),
                re.compile(r'\[hook\]', re.IGNORECASE),
                re.compile(r'\b(pre_tool|post_tool|context|memory).*\b(hook|executed|completed)\b', re.IGNORECASE),
                re.compile(r'\bhook.*\b(execution|time|completed|executed)\b', re.IGNORECASE)
            ],
            
            "hook_types": {
                "pre_tool": re.compile(r'\bpre_tool\b', re.IGNORECASE),
                "post_tool": re.compile(r'\bpost_tool\b', re.IGNORECASE),
                "context": re.compile(r'\bcontext.*\b(memory|optimization)\b', re.IGNORECASE),
                "security": re.compile(r'\bsecurity.*\b(hook|validator|validation)\b', re.IGNORECASE),
                "optimization": re.compile(r'\b(memory|performance).*\b(optimization|optimizer)\b', re.IGNORECASE),
                "automation": re.compile(r'\b(auto|automatic).*\b(commit|save|backup)\b', re.IGNORECASE)
            },
            
            "automation": [
                re.compile(r'\b(automated|automatic|auto).*\b(backup|commit|save|deploy)\b', re.IGNORECASE),
                re.compile(r'\b(scheduled|continuous).*\b(task|integration|deployment)\b', re.IGNORECASE),
                re.compile(r'\b(pipeline|workflow).*\b(trigger|execute|complete)\b', re.IGNORECASE)
            ]
        }
    
    def detect_patterns(self, content: str) -> Dict[str, Any]:
        """Detect hook and automation patterns in content"""
        patterns = {}
        
        # Hook execution patterns
        hook_matches = [self._match_pattern(content, p) for p in self._compiled_patterns["hook_execution"]]
        patterns["hook_execution"] = {
            "detected": any(hook_matches),
            "confidence": min(1.0, self._calculate_confidence(hook_matches) + 0.4),  # High confidence boost
            "matches": sum(hook_matches)
        }
        
        # Hook type detection
        detected_types = []
        for hook_type, pattern in self._compiled_patterns["hook_types"].items():
            if self._match_pattern(content, pattern):
                detected_types.append(hook_type)
        
        patterns["hook_types"] = {
            "detected": len(detected_types) > 0,
            "types": detected_types,
            "count": len(detected_types)
        }
        
        # Automation patterns
        auto_matches = [self._match_pattern(content, p) for p in self._compiled_patterns["automation"]]
        patterns["automation"] = {
            "detected": any(auto_matches),
            "confidence": self._calculate_confidence(auto_matches),
            "matches": sum(auto_matches)
        }
        
        return patterns


class SystemPatternDetector(BasePatternDetector):
    """Detects system validation and status patterns"""
    
    def _compile_patterns(self):
        """Compile system-related regex patterns"""
        self._compiled_patterns = {
            "validation": [
                re.compile(r'\b(validated|validation|check.*passed|syntax.*check)\b', re.IGNORECASE),
                re.compile(r'\b(permissions.*validated|health.*check|security.*scan)\b', re.IGNORECASE),
                re.compile(r'\b(dependencies.*up.*to.*date|configuration.*validated)\b', re.IGNORECASE),
                re.compile(r'\b(formatting.*check|linting.*passed)\b', re.IGNORECASE)
            ],
            
            "status": [
                re.compile(r'\b(system\s+ready|service\s+started|connection\s+established)\b', re.IGNORECASE),
                re.compile(r'\b(database\s+online|all\s+services\s+running|systems.*operational)\b', re.IGNORECASE),
                re.compile(r'\b(ready.*process|startup.*complete)\b', re.IGNORECASE)
            ],
            
            "confirmation": [
                re.compile(r'^\s*(ok|done|success|completed|acknowledged|confirmed|received)\s*$', re.IGNORECASE),
                re.compile(r'^\s*(yes|no|true|false)\s*$', re.IGNORECASE)
            ],
            
            "empty_content": [
                re.compile(r'^\s*$'),  # Empty or whitespace only
                re.compile(r'^\s*[-_.]\s*$'),  # Single punctuation
                re.compile(r'^\s*\.\s*$')  # Single period
            ]
        }
    
    def detect_patterns(self, content: str) -> Dict[str, Any]:
        """Detect system and validation patterns in content"""
        patterns = {}
        
        # Validation patterns
        val_matches = [self._match_pattern(content, p) for p in self._compiled_patterns["validation"]]
        patterns["validation"] = {
            "detected": any(val_matches),
            "confidence": self._calculate_confidence(val_matches),
            "matches": sum(val_matches)
        }
        
        # Status patterns
        status_matches = [self._match_pattern(content, p) for p in self._compiled_patterns["status"]]
        patterns["status"] = {
            "detected": any(status_matches),
            "confidence": self._calculate_confidence(status_matches),
            "matches": sum(status_matches)
        }
        
        # Confirmation patterns
        conf_matches = [self._match_pattern(content, p) for p in self._compiled_patterns["confirmation"]]
        patterns["confirmation"] = {
            "detected": any(conf_matches),
            "confidence": self._calculate_confidence(conf_matches),
            "matches": sum(conf_matches)
        }
        
        # Empty content patterns
        empty_matches = [self._match_pattern(content, p) for p in self._compiled_patterns["empty_content"]]
        patterns["empty_content"] = {
            "detected": any(empty_matches),
            "confidence": 1.0 if any(empty_matches) else 0.0,
            "matches": sum(empty_matches)
        }
        
        return patterns


class PatternAnalyzer:
    """Main orchestrator for pattern analysis using all detectors"""
    
    def __init__(self):
        """Initialize analyzer with all pattern detectors"""
        self.detectors = {
            "code": CodePatternDetector(),
            "error": ErrorPatternDetector(),
            "architectural": ArchitecturalPatternDetector(),
            "hook": HookPatternDetector(),
            "system": SystemPatternDetector()
        }
        
        # Pattern type mapping for importance scoring
        self.importance_mapping = {
            "code_changes": ["code.file_modification", "code.function_creation", "code.imports"],
            "error_solution": ["error.error_keywords", "error.solution_keywords", "error.debugging_activity"],
            "architectural_decision": ["architectural.design_patterns", "architectural.architectural_decisions", 
                                     "architectural.technology_choices", "architectural.system_design"],
            "hook_log": ["hook.hook_execution", "hook.automation"],
            "system_validation": ["system.validation", "system.status", "system.confirmation", "system.empty_content"]
        }
    
    def analyze_content(self, content: str) -> Dict[str, Any]:
        """
        Comprehensive pattern analysis of content
        
        Args:
            content: Text content to analyze
            
        Returns:
            Dictionary with pattern analysis results
        """
        all_patterns = {}
        
        # Run all detectors
        for detector_name, detector in self.detectors.items():
            try:
                patterns = detector.detect_patterns(content)
                for pattern_name, pattern_data in patterns.items():
                    key = f"{detector_name}.{pattern_name}"
                    all_patterns[key] = pattern_data
            except Exception as e:
                logger.warning(f"Error in {detector_name} detector: {e}")
        
        # Map to importance categories
        importance_patterns = {}
        for importance_type, pattern_keys in self.importance_mapping.items():
            detected = False
            confidence_scores = []
            
            for pattern_key in pattern_keys:
                if pattern_key in all_patterns and all_patterns[pattern_key]["detected"]:
                    detected = True
                    confidence_scores.append(all_patterns[pattern_key]["confidence"])
            
            importance_patterns[importance_type] = {
                "detected": detected,
                "confidence": max(confidence_scores) if confidence_scores else 0.0,
                "pattern_matches": len(confidence_scores)
            }
        
        return importance_patterns
    
    def analyze_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze complete message structure including tool calls
        
        Args:
            message: Complete message dictionary
            
        Returns:
            Dictionary with comprehensive message analysis
        """
        # Extract content for pattern analysis
        content = self._extract_content(message)
        content_patterns = self.analyze_content(content)
        
        # Analyze tool usage if applicable
        tool_usage = {}
        if message.get("type") == "tool_call":
            tool_msg = message.get("message", {})
            tool_usage = {
                "tool": tool_msg.get("tool"),
                "file_path": tool_msg.get("parameters", {}).get("file_path"),
                "is_code_tool": tool_msg.get("tool") in {"Write", "Edit", "MultiEdit"}
            }
        
        # Determine importance indicators
        importance_indicators = {}
        for pattern_type, pattern_data in content_patterns.items():
            importance_indicators[pattern_type] = pattern_data["detected"]
        
        return {
            "patterns": content_patterns,
            "importance_indicators": importance_indicators,
            "tool_usage": tool_usage,
            "content_length": len(content),
            "message_type": message.get("type", "unknown")
        }
    
    def batch_analyze(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze batch of messages efficiently
        
        Args:
            messages: List of messages to analyze
            
        Returns:
            List of analysis results
        """
        results = []
        
        for message in messages:
            try:
                analysis = self.analyze_message(message)
                # Add importance score for convenience
                try:
                    from .scoring import ImportanceScorer
                    scorer = ImportanceScorer()
                    analysis["importance_score"] = scorer.calculate_message_importance(message)
                except ImportError:
                    # Avoid circular import during testing
                    analysis["importance_score"] = 0
                results.append(analysis)
            except Exception as e:
                logger.warning(f"Error analyzing message {message.get('uuid', 'unknown')}: {e}")
                # Return basic analysis on error
                results.append({
                    "patterns": {},
                    "importance_indicators": {},
                    "tool_usage": {},
                    "content_length": 0,
                    "message_type": "error",
                    "importance_score": 0,
                    "error": str(e)
                })
        
        return results
    
    def _extract_content(self, message: Dict[str, Any]) -> str:
        """Extract textual content from message for analysis"""
        content_parts = []
        
        if "message" in message:
            msg_content = message["message"]
            if isinstance(msg_content, dict):
                # Extract all textual content
                for key, value in msg_content.items():
                    if isinstance(value, str) and value.strip():
                        content_parts.append(value)
                    elif isinstance(value, dict):
                        # Extract from nested dictionaries
                        for nested_value in value.values():
                            if isinstance(nested_value, str) and nested_value.strip():
                                content_parts.append(nested_value)
            else:
                content_parts.append(str(msg_content))
        
        return " ".join(content_parts)