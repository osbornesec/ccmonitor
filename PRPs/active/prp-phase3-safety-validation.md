# PRP: Safety & Validation System

## Objective
Implement comprehensive safety measures, backup systems, and validation procedures to ensure data integrity and enable safe recovery from any pruning failures.

## Success Criteria
- [ ] Create robust backup and recovery system with timestamped backups
- [ ] Implement multi-level validation procedures for pruned content
- [ ] Develop quality assurance test suite with comprehensive edge cases
- [ ] Ensure <1% false positive rate for important content removal
- [ ] Enable safe rollback from any failed operations

## Test-Driven Development Plan

### Phase 3.1: Backup and Recovery System

#### Tests to Write First
```python
def test_create_timestamped_backup():
    """Test backup creation with proper timestamping"""
    
def test_safe_pruning_with_backup():
    """Test pruning operation with automatic backup"""
    
def test_rollback_on_failure():
    """Test automatic rollback when pruning fails"""
    
def test_backup_integrity_verification():
    """Test backup file integrity validation"""
    
def test_cleanup_old_backups():
    """Test automated cleanup of old backup files"""
```

#### Implementation Tasks
1. **Safe Pruner Class**
   ```python
   class SafePruner:
       def prune_with_backup(self, file_path, pruning_level):
           # Create timestamped backup
           backup_path = f"{file_path}.backup.{int(time.time())}"
           shutil.copy2(file_path, backup_path)
           
           try:
               pruned_content = self.prune_file(file_path, pruning_level)
               self.validate_pruned_content(pruned_content)
               self.write_pruned_file(file_path, pruned_content)
               return {"success": True, "backup": backup_path}
           except Exception as e:
               self.restore_from_backup(file_path, backup_path)
               return {"success": False, "error": str(e)}
   ```

2. **Backup Management System**
   - Timestamped backup creation before any modification
   - Backup integrity verification using checksums
   - Automatic cleanup of backups older than configured retention period
   - Space-efficient backup storage with compression options

3. **Recovery Mechanisms**
   - Automatic rollback on validation failures
   - Manual recovery tools for user-initiated restoration
   - Backup verification before deletion
   - Recovery testing and validation

### Phase 3.2: Validation Procedures

#### Tests to Write First
```python
def test_jsonl_format_validation():
    """Test JSONL format integrity after pruning"""
    
def test_conversation_flow_integrity():
    """Test parentUuid chains remain intact"""
    
def test_essential_content_preservation():
    """Test code changes and decisions are retained"""
    
def test_size_reduction_metrics():
    """Test compression ratios meet targets"""
    
def test_performance_validation():
    """Test processing performance meets benchmarks"""
```

#### Implementation Tasks
1. **JSONL Format Validation**
   - Verify each line contains valid JSON
   - Check required fields are present (uuid, type, message)
   - Validate timestamp formats and message structure
   - Detect and report malformed entries

2. **Conversation Flow Integrity**
   - Verify parentUuid chains remain unbroken
   - Check that message dependencies are preserved
   - Validate conversation branch consistency
   - Detect orphaned messages or broken references

3. **Content Quality Validation**
   - Ensure all code modifications are preserved
   - Verify error/solution pairs remain intact
   - Check architectural decisions are retained
   - Validate file modification sequences

4. **Metrics Validation**
   - Measure and validate size reduction percentages
   - Track token count reductions
   - Monitor processing performance metrics
   - Calculate false positive rates for content removal

### Phase 3.3: Quality Assurance Test Suite

#### Tests to Write First
```python
def test_edge_case_malformed_json():
    """Test handling of malformed JSON entries"""
    
def test_edge_case_circular_references():
    """Test handling of circular parentUuid references"""
    
def test_edge_case_missing_parents():
    """Test handling of messages with missing parents"""
    
def test_edge_case_large_files():
    """Test performance on very large JSONL files"""
    
def test_edge_case_empty_messages():
    """Test handling of empty or null messages"""
```

#### Implementation Tasks
1. **Comprehensive Validation Function**
   ```python
   def validate_pruned_session(original_path, pruned_path):
       tests = [
           test_jsonl_format_valid(pruned_path),
           test_conversation_chains_intact(original_path, pruned_path),
           test_code_changes_preserved(original_path, pruned_path),
           test_error_solutions_retained(original_path, pruned_path),
           test_file_size_reduction(original_path, pruned_path)
       ]
       return all(tests)
   ```

2. **Edge Case Testing**
   - Malformed JSON handling and recovery
   - Circular reference detection and resolution
   - Missing parent message handling
   - Empty or null message processing
   - Very large file performance validation

3. **Regression Testing**
   - Automated testing against known good datasets
   - Performance regression detection
   - Content quality regression monitoring
   - False positive rate tracking over time

4. **Stress Testing**
   - Processing very large JSONL files (10MB+)
   - High-frequency batch processing
   - Memory pressure testing
   - Concurrent operation testing

### Phase 3.4: Monitoring and Reporting

#### Tests to Write First
```python
def test_validation_report_generation():
    """Test comprehensive validation report creation"""
    
def test_performance_metrics_tracking():
    """Test performance metrics collection and reporting"""
    
def test_error_logging_and_alerting():
    """Test error detection and notification systems"""
    
def test_quality_metrics_dashboard():
    """Test quality metrics visualization and tracking"""
```

#### Implementation Tasks
1. **Validation Reporting**
   - Detailed validation reports with pass/fail status
   - Performance metrics and timing data
   - Size reduction statistics and effectiveness metrics
   - Error logs with actionable recommendations

2. **Quality Metrics Tracking**
   - False positive rate monitoring
   - Content preservation effectiveness
   - User satisfaction tracking
   - Performance trend analysis

3. **Error Handling and Alerting**
   - Comprehensive error logging with context
   - Automatic alerting for validation failures
   - Performance degradation detection
   - User notification systems

## Deliverables
1. **Safe Pruning Engine** (`src/pruner/safety.py`)
2. **Validation Framework** (`src/pruner/validator.py`)
3. **Backup Management System** (`src/utils/backup.py`)
4. **Quality Assurance Suite** (`tests/test_safety.py`)
5. **Edge Case Test Collection** (`tests/test_edge_cases.py`)
6. **Validation Reporting Tools** (`src/utils/reporting.py`)

## Dependencies
- Phase 2 completion (core pruning engine)
- Python libraries: `json`, `shutil`, `hashlib`, `datetime`
- Testing framework: `pytest`
- Sample datasets including edge cases

## Context7 Documentation References

### Shutil Module for Safe File Operations
Using Python's shutil module for robust backup and file management:

```python
import shutil
import time
from pathlib import Path
import hashlib

class SafeBackupManager:
    def create_timestamped_backup(self, file_path: Path) -> Path:
        """Create backup with timestamp using shutil.copy2 to preserve metadata"""
        timestamp = int(time.time())
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup.{timestamp}")
        
        # Use copy2 to preserve timestamps and metadata
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def verify_backup_integrity(self, original: Path, backup: Path) -> bool:
        """Verify backup integrity using checksums"""
        def get_file_hash(file_path: Path) -> str:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        
        return get_file_hash(original) == get_file_hash(backup)
    
    def cleanup_old_backups(self, directory: Path, max_age_days: int = 30):
        """Remove backups older than specified days"""
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600
        
        for backup_file in directory.glob("*.backup.*"):
            try:
                # Extract timestamp from filename
                timestamp = int(backup_file.suffixes[-1][1:])  # Remove the dot
                if current_time - timestamp > max_age_seconds:
                    backup_file.unlink()
            except (ValueError, IndexError):
                # Skip files that don't match expected pattern
                continue

# Safe file operations with automatic rollback
class SafeFileOperations:
    def safe_operation_with_rollback(self, file_path: Path, operation_func):
        """Perform file operation with automatic rollback on failure"""
        backup_path = None
        try:
            # Create backup before modification
            backup_path = shutil.copy2(file_path, 
                                     file_path.with_suffix(f"{file_path.suffix}.tmp"))
            
            # Perform the operation
            result = operation_func(file_path)
            
            # If successful, remove backup
            Path(backup_path).unlink()
            return result
            
        except Exception as e:
            # Rollback on failure
            if backup_path and Path(backup_path).exists():
                shutil.move(backup_path, file_path)
            raise e
```

### Pytest Patterns for Safety Testing
Comprehensive safety testing with file operations:

```python
import pytest
import tempfile
import shutil
from pathlib import Path

@pytest.fixture
def temp_file_system(tmp_path):
    """Create temporary file system for testing"""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()
    
    # Create test JSONL file
    test_file = test_dir / "test.jsonl"
    test_data = [
        {"uuid": "1", "type": "user", "message": {"content": "Important data"}},
        {"uuid": "2", "type": "assistant", "message": {"content": "Critical response"}},
    ]
    
    with open(test_file, 'w') as f:
        for entry in test_data:
            json.dump(entry, f)
            f.write('\n')
    
    return {"dir": test_dir, "file": test_file, "data": test_data}

def test_backup_preserves_metadata(temp_file_system):
    """Test that backups preserve file metadata"""
    original_file = temp_file_system["file"]
    backup_manager = SafeBackupManager()
    
    # Get original stats
    original_stat = original_file.stat()
    
    # Create backup
    backup_path = backup_manager.create_timestamped_backup(original_file)
    backup_stat = backup_path.stat()
    
    # Verify metadata preservation (size, content)
    assert backup_stat.st_size == original_stat.st_size
    assert original_file.read_text() == backup_path.read_text()

def test_rollback_on_operation_failure(temp_file_system):
    """Test automatic rollback when operation fails"""
    test_file = temp_file_system["file"]
    original_content = test_file.read_text()
    
    safe_ops = SafeFileOperations()
    
    def failing_operation(file_path):
        # Modify file then fail
        file_path.write_text("corrupted data")
        raise ValueError("Simulated failure")
    
    # Operation should fail and rollback
    with pytest.raises(ValueError):
        safe_ops.safe_operation_with_rollback(test_file, failing_operation)
    
    # Verify file was restored
    assert test_file.read_text() == original_content

# Parametrized testing for edge cases
@pytest.mark.parametrize(
    "corruption_type,expected_recovery",
    [
        ("truncated_file", True),
        ("invalid_json", True), 
        ("permission_denied", False),  # Some failures can't be recovered
        ("disk_full", False),
    ],
)
def test_corruption_recovery(temp_file_system, corruption_type, expected_recovery):
    """Test recovery from various types of file corruption"""
    test_file = temp_file_system["file"]
    backup_manager = SafeBackupManager()
    
    # Create backup
    backup_path = backup_manager.create_timestamped_backup(test_file)
    
    # Simulate corruption based on type
    if corruption_type == "truncated_file":
        test_file.write_text("truncated")
    elif corruption_type == "invalid_json":
        test_file.write_text("invalid json content")
    
    # Attempt recovery
    if expected_recovery:
        shutil.copy2(backup_path, test_file)
        assert backup_manager.verify_backup_integrity(test_file, backup_path)
    else:
        # Some corruption types need special handling
        pass
```

### Error Handling and Validation Patterns
Robust error handling using Python standard patterns:

```python
import json
from typing import List, Dict, Optional
import logging

class ValidationError(Exception):
    """Custom exception for validation failures"""
    pass

class JSONLValidator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_jsonl_format(self, file_path: Path) -> List[str]:
        """Validate JSONL format and return list of issues"""
        issues = []
        
        try:
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        json.loads(line.strip())
                    except json.JSONDecodeError as e:
                        issues.append(f"Line {line_num}: Invalid JSON - {e}")
        except IOError as e:
            issues.append(f"File access error: {e}")
        
        return issues
    
    def validate_conversation_integrity(self, entries: List[Dict]) -> Dict[str, int]:
        """Validate conversation chain integrity"""
        stats = {
            "total_messages": len(entries),
            "orphaned_messages": 0,
            "broken_chains": 0,
            "duplicate_uuids": 0
        }
        
        uuids = set()
        parent_uuids = set()
        
        for entry in entries:
            uuid = entry.get("uuid")
            parent_uuid = entry.get("parentUuid")
            
            # Check for duplicates
            if uuid in uuids:
                stats["duplicate_uuids"] += 1
            uuids.add(uuid)
            
            # Collect parent references
            if parent_uuid:
                parent_uuids.add(parent_uuid)
        
        # Find orphaned messages (parent doesn't exist)
        orphaned = parent_uuids - uuids
        stats["orphaned_messages"] = len(orphaned)
        
        return stats
    
    def validate_content_preservation(self, original: List[Dict], 
                                    pruned: List[Dict]) -> bool:
        """Validate that important content was preserved"""
        original_important = self._extract_important_content(original)
        pruned_important = self._extract_important_content(pruned)
        
        # Calculate preservation ratio
        preservation_ratio = len(pruned_important) / len(original_important)
        
        # Should preserve at least 90% of important content
        return preservation_ratio >= 0.90
    
    def _extract_important_content(self, entries: List[Dict]) -> List[str]:
        """Extract important content patterns"""
        important = []
        important_patterns = [
            "error", "fix", "implement", "create", "write", 
            "class", "function", "def ", "git commit"
        ]
        
        for entry in entries:
            content = entry.get("message", {}).get("content", "").lower()
            if any(pattern in content for pattern in important_patterns):
                important.append(entry.get("uuid", ""))
        
        return important
```

## Safety Requirements
- Mandatory backup creation before any file modification
- Multi-level validation at each processing stage
- Automatic rollback on any validation failure
- User confirmation for aggressive pruning operations
- Comprehensive audit logging for all operations

## Acceptance Criteria
- All tests pass with >98% coverage including edge cases
- <1% false positive rate for important content removal
- 100% backup and recovery success rate in testing
- All validation procedures complete in <5 seconds
- Zero data loss incidents during extensive testing

## Risk Mitigation
- Conservative validation thresholds initially
- Extensive testing on non-production data first
- Manual review capabilities for borderline cases
- Graduated rollout with monitoring at each stage
- Comprehensive documentation of all safety procedures

## Next Steps
Upon completion, this PRP enables Phase 4 (CLI Tool & Automation) development with production-ready safety measures and confidence in data integrity preservation.