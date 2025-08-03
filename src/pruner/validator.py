"""
Multi-Level Validation Framework for Data Integrity
Phase 3 - Comprehensive validation procedures for safe pruning

Validation Levels:
- Level 0: Pre-operation validation (file accessibility, format check)
- Level 1: Backup integrity verification (checksum validation)
- Level 2: Pruning validation (conversation integrity, content preservation)
- Level 3: Post-operation validation (file format, size metrics)
- Level 4: Recovery testing (backup restoration verification)

Features:
- JSONL format validation and structure integrity
- Conversation flow and parentUuid chain preservation
- Essential content preservation verification (<1% false positive rate)
- Size reduction metrics and performance validation
- Circular reference detection and resolution
- Orphaned message identification
- Duplicate UUID detection
"""

import json
import logging
import time
import hashlib
import shutil
import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from collections import defaultdict, Counter
from datetime import datetime
import tempfile

# Import Phase 1 components for validation
from ..jsonl_analysis.analyzer import JSONLAnalyzer, ConversationFlowAnalyzer
from ..jsonl_analysis.scoring import ImportanceScorer
from ..jsonl_analysis.patterns import PatternAnalyzer

logger = logging.getLogger(__name__)


class ValidationFramework:
    """
    Comprehensive validation framework with five validation levels
    
    Ensures data integrity, conversation flow preservation, and
    provides detailed validation reports with pass/fail status.
    """
    
    def __init__(self, false_positive_threshold: float = 0.01):
        """
        Initialize validation framework
        
        Args:
            false_positive_threshold: Maximum allowed false positive rate (default 1%)
        """
        self.false_positive_threshold = false_positive_threshold
        
        # Initialize Phase 1 validators
        self.jsonl_analyzer = JSONLAnalyzer()
        self.flow_analyzer = ConversationFlowAnalyzer()
        self.importance_scorer = ImportanceScorer()
        self.pattern_analyzer = PatternAnalyzer()
        
        # Validation statistics
        self.validation_stats = {
            'total_validations': 0,
            'level_0_passes': 0,
            'level_1_passes': 0,
            'level_2_passes': 0,
            'level_3_passes': 0,
            'level_4_passes': 0,
            'validation_failures': 0,
            'false_positives_detected': 0,
            'circular_references_found': 0,
            'orphaned_messages_found': 0
        }
    
    def validate_level_0_pre_operation(self, file_path: Path) -> Dict[str, Any]:
        """
        Level 0: Pre-operation validation
        - File accessibility and existence
        - Basic JSONL format validation
        - File size and readability checks
        """
        start_time = time.perf_counter()
        result = {
            'valid': True,
            'level': 0,
            'errors': [],
            'warnings': [],
            'accessible': False,
            'format_valid': False,
            'file_size': 0,
            'estimated_entries': 0
        }
        
        try:
            # Check file accessibility
            if not file_path.exists():
                result['errors'].append(f'File not found: {file_path}')
                result['valid'] = False
                result['accessible'] = False
            elif not file_path.is_file():
                result['errors'].append(f'Path is not a file: {file_path}')
                result['valid'] = False
                result['accessible'] = False
            elif not os.access(file_path, os.R_OK):
                result['errors'].append(f'File not accessible: {file_path}')
                result['valid'] = False
                result['accessible'] = False
            else:
                result['accessible'] = True
                result['file_size'] = file_path.stat().st_size
                
                # Check if file is empty
                if result['file_size'] == 0:
                    result['warnings'].append('File is empty')
                    result['estimated_entries'] = 0
                else:
                    # Validate JSONL format by sampling
                    format_result = self._validate_jsonl_format_sample(file_path)
                    result['format_valid'] = format_result['valid']
                    result['estimated_entries'] = format_result['estimated_entries']
                    
                    if not format_result['valid']:
                        result['errors'].extend(format_result['errors'])
                        result['valid'] = False
                    
                    # Check for reasonable file size
                    if result['file_size'] > 1024 * 1024 * 1024:  # >1GB
                        result['warnings'].append('File is very large (>1GB) - consider streaming processing')
            
            result['duration'] = time.perf_counter() - start_time
            
            if result['valid']:
                self.validation_stats['level_0_passes'] += 1
            else:
                self.validation_stats['validation_failures'] += 1
            
            logger.debug(f"Level 0 validation: {'PASS' if result['valid'] else 'FAIL'} in {result['duration']:.3f}s")
            return result
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f'Validation error: {str(e)}')
            result['duration'] = time.perf_counter() - start_time
            logger.error(f"Level 0 validation failed: {e}")
            return result
    
    def validate_level_1_backup_integrity(self, original_path: Path, backup_path: Path) -> Dict[str, Any]:
        """
        Level 1: Backup integrity verification
        - Checksum comparison between original and backup
        - File size verification
        - Content sampling verification
        """
        start_time = time.perf_counter()
        result = {
            'valid': True,
            'level': 1,
            'errors': [],
            'warnings': [],
            'checksums_match': False,
            'sizes_match': False,
            'backup_complete': False,
            'original_checksum': None,
            'backup_checksum': None
        }
        
        try:
            # Check both files exist
            if not original_path.exists():
                result['errors'].append(f'Original file not found: {original_path}')
                result['valid'] = False
            
            if not backup_path.exists():
                result['errors'].append(f'Backup file not found: {backup_path}')
                result['valid'] = False
            
            if not result['valid']:
                result['duration'] = time.perf_counter() - start_time
                return result
            
            # Calculate checksums
            result['original_checksum'] = self._calculate_file_checksum(original_path)
            result['backup_checksum'] = self._calculate_file_checksum(backup_path)
            result['checksums_match'] = result['original_checksum'] == result['backup_checksum']
            
            # Compare file sizes
            original_size = original_path.stat().st_size
            backup_size = backup_path.stat().st_size
            result['sizes_match'] = original_size == backup_size
            result['original_size'] = original_size
            result['backup_size'] = backup_size
            
            # Content sampling verification (for compressed backups)
            if result['checksums_match'] and result['sizes_match']:
                result['backup_complete'] = True
            elif backup_path.suffix == '.gz':
                # For compressed backups, verify content can be restored
                content_match = self._verify_compressed_backup_content(original_path, backup_path)
                result['backup_complete'] = content_match
                if not content_match:
                    result['errors'].append('Compressed backup content does not match original')
                    result['valid'] = False
            else:
                result['errors'].append('Checksum or size mismatch between original and backup')
                result['valid'] = False
            
            # Final validation
            if not (result['checksums_match'] or result['backup_complete']):
                result['valid'] = False
            
            result['duration'] = time.perf_counter() - start_time
            
            if result['valid']:
                self.validation_stats['level_1_passes'] += 1
            else:
                self.validation_stats['validation_failures'] += 1
                result['checksum_mismatch'] = True
            
            logger.debug(f"Level 1 validation: {'PASS' if result['valid'] else 'FAIL'} in {result['duration']:.3f}s")
            return result
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f'Backup integrity validation error: {str(e)}')
            result['duration'] = time.perf_counter() - start_time
            logger.error(f"Level 1 validation failed: {e}")
            return result
    
    def validate_level_2_pruning_integrity(
        self, 
        original_messages: List[Dict[str, Any]], 
        pruned_messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Level 2: Pruning validation
        - Conversation chains integrity
        - Essential content preservation
        - False positive rate calculation
        - Dependency preservation
        """
        start_time = time.perf_counter()
        result = {
            'valid': True,
            'level': 2,
            'errors': [],
            'warnings': [],
            'conversation_chains_intact': True,
            'essential_content_preserved': True,
            'false_positive_rate': 0.0,
            'orphaned_messages': [],
            'broken_chains': [],
            'preserved_count': len(pruned_messages),
            'removed_count': len(original_messages) - len(pruned_messages),
            'compression_ratio': 0.0
        }
        
        try:
            if len(original_messages) == 0:
                result['warnings'].append('No original messages to validate')
                result['duration'] = time.perf_counter() - start_time
                return result
            
            # Calculate compression ratio
            result['compression_ratio'] = result['removed_count'] / len(original_messages)
            
            # Build UUID mappings
            original_uuids = {msg['uuid'] for msg in original_messages}
            pruned_uuids = {msg['uuid'] for msg in pruned_messages}
            
            # Validate conversation chain integrity
            chain_result = self._validate_conversation_chains(original_messages, pruned_messages)
            result['conversation_chains_intact'] = chain_result['intact']
            result['orphaned_messages'] = chain_result['orphaned']
            result['broken_chains'] = chain_result['broken']
            
            if not chain_result['intact']:
                result['errors'].append(f"Conversation chains broken: {len(chain_result['broken'])} chains affected")
                result['valid'] = False
            
            # Validate essential content preservation
            essential_result = self._validate_essential_content_preservation(original_messages, pruned_messages)
            result['essential_content_preserved'] = essential_result['preserved']
            result['false_positive_rate'] = essential_result['false_positive_rate']
            result['essential_messages_removed'] = essential_result['essential_removed']
            
            if result['false_positive_rate'] > self.false_positive_threshold:
                result['errors'].append(f"False positive rate {result['false_positive_rate']:.3f} exceeds threshold {self.false_positive_threshold}")
                result['valid'] = False
                self.validation_stats['false_positives_detected'] += 1
            
            # Validate dependency preservation
            dependency_result = self._validate_dependency_preservation(original_messages, pruned_messages)
            if not dependency_result['dependencies_preserved']:
                result['errors'].append(f"Critical dependencies broken: {dependency_result['broken_dependencies']}")
                result['warnings'].extend(dependency_result['warnings'])
            
            # Check for data corruption
            corruption_result = self._check_data_corruption(pruned_messages)
            if corruption_result['corruption_detected']:
                result['errors'].append(f"Data corruption detected: {corruption_result['issues']}")
                result['valid'] = False
            
            result['duration'] = time.perf_counter() - start_time
            
            if result['valid']:
                self.validation_stats['level_2_passes'] += 1
            else:
                self.validation_stats['validation_failures'] += 1
            
            logger.debug(f"Level 2 validation: {'PASS' if result['valid'] else 'FAIL'} in {result['duration']:.3f}s")
            return result
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f'Pruning integrity validation error: {str(e)}')
            result['duration'] = time.perf_counter() - start_time
            logger.error(f"Level 2 validation failed: {e}")
            return result
    
    def validate_level_3_post_operation(
        self, 
        original_count: int, 
        output_path: Path, 
        target_compression: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Level 3: Post-operation validation
        - Output file format validation
        - Size metrics verification
        - Performance target validation
        """
        start_time = time.perf_counter()
        result = {
            'valid': True,
            'level': 3,
            'errors': [],
            'warnings': [],
            'format_valid': False,
            'compression_achieved': 0.0,
            'within_target_range': True,
            'output_count': 0,
            'processing_time': 0.0
        }
        
        try:
            # Validate output file exists and is readable
            if not output_path.exists():
                result['errors'].append(f'Output file not found: {output_path}')
                result['valid'] = False
                result['duration'] = time.perf_counter() - start_time
                return result
            
            # Validate output format
            format_result = self._validate_jsonl_format_complete(output_path)
            result['format_valid'] = format_result['valid']
            result['output_count'] = format_result['entry_count']
            
            if not format_result['valid']:
                result['errors'].extend(format_result['errors'])
                result['valid'] = False
            
            # Calculate compression metrics
            if original_count > 0:
                result['compression_achieved'] = (original_count - result['output_count']) / original_count
            
            # Validate compression target
            if target_compression is not None:
                tolerance = 0.1  # 10% tolerance
                if abs(result['compression_achieved'] - target_compression) > tolerance:
                    result['within_target_range'] = False
                    result['warnings'].append(
                        f"Compression {result['compression_achieved']:.3f} outside target range "
                        f"{target_compression:.3f} ± {tolerance:.1f}"
                    )
            
            # Validate reasonable compression ratio
            if result['compression_achieved'] < 0:
                result['errors'].append('Negative compression ratio - output larger than input')
                result['valid'] = False
            elif result['compression_achieved'] > 0.95:
                result['warnings'].append('Very high compression ratio (>95%) - verify essential content preserved')
            
            # Check output file is not empty when input had content
            if original_count > 0 and result['output_count'] == 0:
                result['errors'].append('Output file is empty despite non-empty input')
                result['valid'] = False
            
            result['duration'] = time.perf_counter() - start_time
            
            if result['valid']:
                self.validation_stats['level_3_passes'] += 1
            else:
                self.validation_stats['validation_failures'] += 1
            
            logger.debug(f"Level 3 validation: {'PASS' if result['valid'] else 'FAIL'} in {result['duration']:.3f}s")
            return result
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f'Post-operation validation error: {str(e)}')
            result['duration'] = time.perf_counter() - start_time
            logger.error(f"Level 3 validation failed: {e}")
            return result
    
    def validate_level_4_recovery_capability(self, original_path: Path, backup_path: Path) -> Dict[str, Any]:
        """
        Level 4: Recovery testing
        - Backup restoration verification
        - Data integrity after recovery
        - Recovery procedure testing
        """
        start_time = time.perf_counter()
        result = {
            'valid': True,
            'level': 4,
            'errors': [],
            'warnings': [],
            'backup_restorable': False,
            'recovery_successful': False,
            'data_integrity_maintained': False,
            'recovery_time': 0.0
        }
        
        try:
            # Create temporary copy for testing
            with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as temp_file:
                temp_path = Path(temp_file.name)
            
            recovery_start = time.perf_counter()
            
            try:
                # Test backup restoration
                if backup_path.suffix == '.gz':
                    # Test compressed backup restoration
                    import gzip
                    with gzip.open(backup_path, 'rb') as gz_file:
                        with open(temp_path, 'wb') as temp_file:
                            shutil.copyfileobj(gz_file, temp_file)
                else:
                    # Test regular backup restoration
                    shutil.copy2(backup_path, temp_path)
                
                result['backup_restorable'] = True
                result['recovery_time'] = time.perf_counter() - recovery_start
                
                # Verify restored content integrity
                if original_path.exists():
                    original_checksum = self._calculate_file_checksum(original_path)
                    restored_checksum = self._calculate_file_checksum(temp_path)
                    result['data_integrity_maintained'] = original_checksum == restored_checksum
                else:
                    # If original doesn't exist, validate restored format
                    format_result = self._validate_jsonl_format_complete(temp_path)
                    result['data_integrity_maintained'] = format_result['valid']
                
                if result['data_integrity_maintained']:
                    result['recovery_successful'] = True
                else:
                    result['errors'].append('Data integrity check failed after recovery')
                    result['valid'] = False
                
            except Exception as restore_error:
                result['errors'].append(f'Backup restoration failed: {str(restore_error)}')
                result['valid'] = False
            
            finally:
                # Cleanup temporary file
                temp_path.unlink(missing_ok=True)
            
            # Test recovery procedure performance
            if result['recovery_time'] > 30.0:  # >30 seconds is concerning
                result['warnings'].append(f'Recovery time {result["recovery_time"]:.1f}s exceeds recommended 30s')
            
            result['duration'] = time.perf_counter() - start_time
            
            if result['valid']:
                self.validation_stats['level_4_passes'] += 1
            else:
                self.validation_stats['validation_failures'] += 1
            
            logger.debug(f"Level 4 validation: {'PASS' if result['valid'] else 'FAIL'} in {result['duration']:.3f}s")
            return result
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f'Recovery capability validation error: {str(e)}')
            result['duration'] = time.perf_counter() - start_time
            logger.error(f"Level 4 validation failed: {e}")
            return result
    
    def run_comprehensive_validation(
        self,
        input_path: Path,
        output_path: Path,
        backup_path: Path,
        original_messages: List[Dict[str, Any]],
        pruned_messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run complete validation pipeline with all levels
        
        Returns comprehensive validation report with overall status
        """
        start_time = time.perf_counter()
        
        # Run all validation levels
        level_0 = self.validate_level_0_pre_operation(input_path)
        level_1 = self.validate_level_1_backup_integrity(input_path, backup_path)
        level_2 = self.validate_level_2_pruning_integrity(original_messages, pruned_messages)
        level_3 = self.validate_level_3_post_operation(len(original_messages), output_path)
        level_4 = self.validate_level_4_recovery_capability(input_path, backup_path)
        
        # Calculate overall result
        all_levels = [level_0, level_1, level_2, level_3, level_4]
        overall_valid = all(level['valid'] for level in all_levels)
        
        total_time = time.perf_counter() - start_time
        self.validation_stats['total_validations'] += 1
        
        result = {
            'overall_valid': overall_valid,
            'validation_time': total_time,
            'level_0': level_0,
            'level_1': level_1,
            'level_2': level_2,
            'level_3': level_3,
            'level_4': level_4,
            'failed_levels': [f'level_{i}' for i, level in enumerate(all_levels) if not level['valid']],
            'total_errors': sum(len(level['errors']) for level in all_levels),
            'total_warnings': sum(len(level['warnings']) for level in all_levels),
            'performance_summary': {
                'total_validation_time': total_time,
                'level_times': [level['duration'] for level in all_levels],
                'within_5s_target': total_time < 5.0
            }
        }
        
        logger.info(f"Comprehensive validation: {'PASS' if overall_valid else 'FAIL'} in {total_time:.3f}s")
        return result
    
    # Edge case detection methods
    
    def detect_circular_references(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect circular references in parentUuid chains"""
        result = {
            'circular_references_found': False,
            'circular_chains': [],
            'affected_messages': []
        }
        
        try:
            # Build parent-child mapping
            parent_map = {}
            for msg in messages:
                uuid = msg.get('uuid')
                parent_uuid = msg.get('parentUuid')
                if uuid and parent_uuid:
                    parent_map[uuid] = parent_uuid
            
            # Detect cycles using DFS
            visited = set()
            rec_stack = set()
            
            def has_cycle(node, path):
                if node in rec_stack:
                    # Found cycle
                    cycle_start = path.index(node)
                    cycle = path[cycle_start:] + [node]
                    return cycle
                
                if node in visited:
                    return None
                
                visited.add(node)
                rec_stack.add(node)
                path.append(node)
                
                if node in parent_map:
                    cycle = has_cycle(parent_map[node], path)
                    if cycle:
                        return cycle
                
                rec_stack.remove(node)
                path.pop()
                return None
            
            # Check each node for cycles
            for uuid in parent_map:
                if uuid not in visited:
                    cycle = has_cycle(uuid, [])
                    if cycle:
                        result['circular_references_found'] = True
                        result['circular_chains'].append(cycle)
                        result['affected_messages'].extend(cycle)
            
            if result['circular_references_found']:
                self.validation_stats['circular_references_found'] += len(result['circular_chains'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting circular references: {e}")
            return {'error': str(e), 'circular_references_found': False}
    
    def detect_orphaned_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect messages with missing parent references"""
        result = {
            'orphaned_messages_found': False,
            'orphaned_messages': [],
            'missing_parents': []
        }
        
        try:
            # Build UUID set
            existing_uuids = {msg.get('uuid') for msg in messages if msg.get('uuid')}
            
            # Find orphaned messages
            for msg in messages:
                uuid = msg.get('uuid')
                parent_uuid = msg.get('parentUuid')
                
                if parent_uuid and parent_uuid not in existing_uuids:
                    result['orphaned_messages_found'] = True
                    result['orphaned_messages'].append(uuid)
                    result['missing_parents'].append(parent_uuid)
            
            if result['orphaned_messages_found']:
                self.validation_stats['orphaned_messages_found'] += len(result['orphaned_messages'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting orphaned messages: {e}")
            return {'error': str(e), 'orphaned_messages_found': False}
    
    def detect_duplicate_uuids(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect duplicate UUIDs in message data"""
        result = {
            'duplicates_found': False,
            'duplicate_uuids': [],
            'duplicate_count': 0
        }
        
        try:
            uuid_counts = Counter()
            for msg in messages:
                uuid = msg.get('uuid')
                if uuid:
                    uuid_counts[uuid] += 1
            
            # Find duplicates
            duplicates = {uuid: count for uuid, count in uuid_counts.items() if count > 1}
            
            if duplicates:
                result['duplicates_found'] = True
                result['duplicate_uuids'] = list(duplicates.keys())
                result['duplicate_count'] = len(duplicates)
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting duplicate UUIDs: {e}")
            return {'error': str(e), 'duplicates_found': False}
    
    def validate_required_fields(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate that all messages have required fields"""
        result = {
            'valid': True,
            'missing_fields_detected': False,
            'invalid_entries': [],
            'required_fields': ['uuid', 'type', 'message']
        }
        
        try:
            for i, msg in enumerate(messages):
                missing_fields = []
                for field in result['required_fields']:
                    if field not in msg or msg[field] is None:
                        missing_fields.append(field)
                
                if missing_fields:
                    result['missing_fields_detected'] = True
                    result['valid'] = False
                    result['invalid_entries'].append({
                        'index': i,
                        'uuid': msg.get('uuid', 'unknown'),
                        'missing_fields': missing_fields
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating required fields: {e}")
            return {'valid': False, 'error': str(e)}
    
    def validate_json_structure(self, file_path: Path) -> Dict[str, Any]:
        """Validate JSON structure of file"""
        result = {
            'valid': True,
            'corruption_detected': False,
            'corrupted_lines': [],
            'total_lines': 0,
            'valid_lines': 0
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    result['total_lines'] += 1
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    try:
                        json.loads(line)
                        result['valid_lines'] += 1
                    except json.JSONDecodeError as e:
                        result['corruption_detected'] = True
                        result['corrupted_lines'].append({
                            'line': line_num,
                            'error': str(e),
                            'content': line[:100] + '...' if len(line) > 100 else line
                        })
            
            if result['corruption_detected']:
                result['valid'] = False
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating JSON structure: {e}")
            return {'valid': False, 'error': str(e)}
    
    def validate_with_fallback(self, original_data: List[Dict[str, Any]], pruned_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate with fallback to local validation if network services fail"""
        result = {
            'network_service_available': False,
            'validation_method': 'local_fallback',
            'valid': None
        }
        
        try:
            # Try network validation first (mock for now)
            try:
                # This would be a real network call in production
                # import requests
                # response = requests.post('https://validation-service.com/validate', json=data, timeout=5)
                # if response.status_code == 200:
                #     result['network_service_available'] = True
                #     result['validation_method'] = 'network_service'
                #     return response.json()
                raise ConnectionError("Network service unavailable")
                
            except (ConnectionError, Exception):
                # Fall back to local validation
                logger.info("Network validation service unavailable, using local validation")
                local_result = self.validate_level_2_pruning_integrity(original_data, pruned_data)
                result['valid'] = local_result['valid']
                result['local_validation_details'] = local_result
                
                return result
                
        except Exception as e:
            logger.error(f"Validation with fallback failed: {e}")
            result['valid'] = False
            result['error'] = str(e)
            return result
    
    # Helper methods
    
    def _validate_jsonl_format_sample(self, file_path: Path, sample_lines: int = 10) -> Dict[str, Any]:
        """Validate JSONL format by sampling first N lines"""
        result = {
            'valid': True,
            'errors': [],
            'estimated_entries': 0,
            'sample_size': 0
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                valid_count = 0
                total_lines = 0
                
                for line_num, line in enumerate(f, 1):
                    total_lines += 1
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        if isinstance(data, dict):
                            valid_count += 1
                        else:
                            result['errors'].append(f'Line {line_num}: Expected JSON object, got {type(data).__name__}')
                    except json.JSONDecodeError as e:
                        result['errors'].append(f'Line {line_num}: {str(e)}')
                    
                    if line_num >= sample_lines:
                        result['sample_size'] = line_num
                        break
                
                # Estimate total entries
                if total_lines > 0:
                    valid_ratio = valid_count / total_lines
                    if valid_ratio < 0.5:
                        result['valid'] = False
                        result['errors'].append(f'Low valid JSON ratio: {valid_ratio:.2f}')
                    
                    # Estimate total entries by counting remaining lines
                    remaining_lines = sum(1 for _ in f)
                    result['estimated_entries'] = int((total_lines + remaining_lines) * valid_ratio)
                
            return result
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f'File reading error: {str(e)}')
            return result
    
    def _validate_jsonl_format_complete(self, file_path: Path) -> Dict[str, Any]:
        """Complete JSONL format validation"""
        result = {
            'valid': True,
            'errors': [],
            'entry_count': 0,
            'malformed_lines': 0
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        if isinstance(data, dict):
                            result['entry_count'] += 1
                        else:
                            result['malformed_lines'] += 1
                            result['errors'].append(f'Line {line_num}: Expected JSON object')
                    except json.JSONDecodeError:
                        result['malformed_lines'] += 1
                        result['errors'].append(f'Line {line_num}: Invalid JSON')
            
            if result['malformed_lines'] > 0:
                result['valid'] = False
            
            return result
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f'Complete validation error: {str(e)}')
            return result
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _verify_compressed_backup_content(self, original_path: Path, backup_path: Path) -> bool:
        """Verify compressed backup content matches original"""
        try:
            import gzip
            with gzip.open(backup_path, 'rt', encoding='utf-8') as gz_file:
                backup_content = gz_file.read()
            
            with open(original_path, 'r', encoding='utf-8') as orig_file:
                original_content = orig_file.read()
            
            return backup_content == original_content
            
        except Exception as e:
            logger.error(f"Error verifying compressed backup: {e}")
            return False
    
    def _validate_conversation_chains(
        self, 
        original_messages: List[Dict[str, Any]], 
        pruned_messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate conversation chain integrity after pruning"""
        result = {
            'intact': True,
            'orphaned': [],
            'broken': []
        }
        
        try:
            # Build UUID sets
            original_uuids = {msg['uuid'] for msg in original_messages if 'uuid' in msg}
            pruned_uuids = {msg['uuid'] for msg in pruned_messages if 'uuid' in msg}
            
            # Check for orphaned messages in pruned set
            for msg in pruned_messages:
                parent_uuid = msg.get('parentUuid')
                if parent_uuid and parent_uuid not in pruned_uuids:
                    # Check if parent existed in original
                    if parent_uuid in original_uuids:
                        result['orphaned'].append(msg['uuid'])
                        result['intact'] = False
            
            # Check for broken conversation chains
            chains = defaultdict(list)
            for msg in original_messages:
                parent_uuid = msg.get('parentUuid')
                if parent_uuid:
                    chains[parent_uuid].append(msg['uuid'])
            
            for parent_uuid, children in chains.items():
                if parent_uuid in pruned_uuids:
                    # Parent preserved, check children
                    preserved_children = [child for child in children if child in pruned_uuids]
                    if len(preserved_children) == 0 and len(children) > 0:
                        # All children removed but parent preserved
                        result['broken'].append({
                            'parent': parent_uuid,
                            'removed_children': children
                        })
                        result['intact'] = False
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating conversation chains: {e}")
            return {'intact': False, 'error': str(e)}
    
    def _validate_essential_content_preservation(
        self, 
        original_messages: List[Dict[str, Any]], 
        pruned_messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate that essential content is preserved with low false positive rate"""
        result = {
            'preserved': True,
            'false_positive_rate': 0.0,
            'essential_removed': [],
            'total_essential': 0
        }
        
        try:
            # Identify essential messages using importance scoring
            essential_uuids = set()
            for msg in original_messages:
                score = self.importance_scorer.calculate_message_importance(msg)
                if score >= 60:  # High importance threshold
                    essential_uuids.add(msg['uuid'])
                    result['total_essential'] += 1
            
            # Check how many essential messages were removed
            pruned_uuids = {msg['uuid'] for msg in pruned_messages if 'uuid' in msg}
            removed_essential = essential_uuids - pruned_uuids
            
            result['essential_removed'] = list(removed_essential)
            
            # Calculate false positive rate
            if result['total_essential'] > 0:
                result['false_positive_rate'] = len(removed_essential) / result['total_essential']
            
            # Check if within threshold
            if result['false_positive_rate'] > self.false_positive_threshold:
                result['preserved'] = False
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating essential content preservation: {e}")
            return {'preserved': False, 'error': str(e)}
    
    def _validate_dependency_preservation(
        self, 
        original_messages: List[Dict[str, Any]], 
        pruned_messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate that critical dependencies are preserved"""
        result = {
            'dependencies_preserved': True,
            'broken_dependencies': [],
            'warnings': []
        }
        
        try:
            # Use flow analyzer to identify dependencies
            dependencies = self.flow_analyzer.map_conversation_dependencies(original_messages)
            pruned_uuids = {msg['uuid'] for msg in pruned_messages if 'uuid' in msg}
            
            # Check each dependency
            for dep in dependencies.get('critical_paths', []):
                for uuid in dep:
                    if uuid not in pruned_uuids:
                        result['broken_dependencies'].append(dep)
                        result['dependencies_preserved'] = False
                        break
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating dependency preservation: {e}")
            return {'dependencies_preserved': False, 'error': str(e)}
    
    def _check_data_corruption(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check for data corruption in pruned messages"""
        result = {
            'corruption_detected': False,
            'issues': []
        }
        
        try:
            for i, msg in enumerate(messages):
                # Check for basic structure
                if not isinstance(msg, dict):
                    result['corruption_detected'] = True
                    result['issues'].append(f'Message {i}: Not a dictionary')
                    continue
                
                # Check for required fields
                if 'uuid' not in msg:
                    result['corruption_detected'] = True
                    result['issues'].append(f'Message {i}: Missing UUID')
                
                # Check for invalid UUID format
                uuid = msg.get('uuid')
                if uuid and not isinstance(uuid, str):
                    result['corruption_detected'] = True
                    result['issues'].append(f'Message {i}: Invalid UUID type')
                
                # Check message structure
                if 'message' in msg and msg['message'] is not None:
                    if not isinstance(msg['message'], dict):
                        result['corruption_detected'] = True
                        result['issues'].append(f'Message {i}: Invalid message structure')
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking data corruption: {e}")
            return {'corruption_detected': True, 'error': str(e)}
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive validation statistics"""
        total_validations = max(1, self.validation_stats['total_validations'])
        
        return {
            'total_validations': self.validation_stats['total_validations'],
            'success_rates': {
                'level_0': self.validation_stats['level_0_passes'] / total_validations,
                'level_1': self.validation_stats['level_1_passes'] / total_validations,
                'level_2': self.validation_stats['level_2_passes'] / total_validations,
                'level_3': self.validation_stats['level_3_passes'] / total_validations,
                'level_4': self.validation_stats['level_4_passes'] / total_validations,
            },
            'failure_rate': self.validation_stats['validation_failures'] / total_validations,
            'false_positive_detections': self.validation_stats['false_positives_detected'],
            'edge_cases_found': {
                'circular_references': self.validation_stats['circular_references_found'],
                'orphaned_messages': self.validation_stats['orphaned_messages_found']
            }
        }