"""
Comprehensive Safety Test Suite for Phase 3 - Safety & Validation System
Test-Driven Development approach for bulletproof data protection

Tests cover:
1. Safe Pruning Engine with automatic backup and rollback
2. Multi-level validation procedures 
3. Backup management with integrity verification
4. Quality assurance and edge case handling
5. Monitoring and reporting framework
"""

import pytest
import json
import tempfile
import shutil
import hashlib
import time
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import test fixtures
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))


class TestSafePruningEngine:
    """Test suite for SafePruner with automatic backup and rollback"""
    
    @pytest.fixture
    def sample_jsonl_data(self):
        """Valid JSONL data for testing"""
        return [
            {
                "uuid": "msg-001",
                "type": "user",
                "parentUuid": None,
                "message": {"content": "Help me debug this error"},
                "timestamp": "2025-08-01T10:00:00"
            },
            {
                "uuid": "msg-002", 
                "type": "assistant",
                "parentUuid": "msg-001",
                "message": {"content": "I'll help you debug that error. Let me examine the code."},
                "timestamp": "2025-08-01T10:00:01"
            },
            {
                "uuid": "msg-003",
                "type": "tool_call",
                "parentUuid": "msg-002",
                "message": {
                    "tool": "Read",
                    "parameters": {"file_path": "/code/app.py"},
                    "result": "def buggy_function():\n    return undefined_variable"
                },
                "timestamp": "2025-08-01T10:00:02"
            }
        ]
    
    @pytest.fixture
    def corrupted_jsonl_data(self):
        """Corrupted JSONL data for failure testing"""
        return [
            '{"uuid": "msg-001", "type": "user", "message": {"content": "valid"}}\n',
            '{"uuid": "msg-002", "type": "assistant", "message": {invalid json}\n',
            '{"uuid": "msg-003", "type": "user", "message": {"content": "valid again"}}\n'
        ]
    
    def test_safe_pruner_creates_backup_before_processing(self, sample_jsonl_data):
        """Test that SafePruner always creates verified backup before modification"""
        from src.pruner.safety import SafePruner
        
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in sample_jsonl_data:
                json.dump(entry, f)
                f.write('\n')
            input_path = Path(f.name)
        
        output_path = input_path.with_suffix('.pruned.jsonl')
        
        try:
            safe_pruner = SafePruner(pruning_level='medium')
            result = safe_pruner.prune_with_complete_safety(input_path, output_path)
            
            # Backup should be created and verified
            assert result['success'] is True
            assert 'backup_path' in result
            assert Path(result['backup_path']).exists()
            
            # Backup should be identical to original
            backup_path = Path(result['backup_path'])
            original_content = input_path.read_text()
            
            # Handle compressed backups
            if backup_path.suffix == '.gz':
                import gzip
                with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                    backup_content = f.read()
            else:
                backup_content = backup_path.read_text()
            
            assert backup_content == original_content
            
            # Backup should have checksum verification
            assert 'backup_checksum' in result
            assert result['backup_verified'] is True
            
        finally:
            # Cleanup
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)
            if 'backup_path' in locals():
                Path(result['backup_path']).unlink(missing_ok=True)
    
    def test_automatic_rollback_on_validation_failure(self, sample_jsonl_data):
        """Test that SafePruner automatically rolls back on validation failure"""
        from src.pruner.safety import SafePruner
        
        # Create input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in sample_jsonl_data:
                json.dump(entry, f)
                f.write('\n')
            input_path = Path(f.name)
        
        output_path = input_path.with_suffix('.pruned.jsonl')
        
        try:
            # Mock validator to force failure
            with patch('src.pruner.safety.ValidationFramework') as mock_validator:
                mock_validator.return_value.validate_pruned_content.return_value = {
                    'valid': False,
                    'errors': ['Conversation chain broken'],
                    'critical': True
                }
                
                safe_pruner = SafePruner(pruning_level='medium')
                result = safe_pruner.prune_with_complete_safety(input_path, output_path)
                
                # Should fail gracefully and rollback
                assert result['success'] is False
                assert result['recovered'] is True
                assert 'error' in result
                
                # Original file should be unchanged
                assert input_path.exists()
                original_content = input_path.read_text()
                assert len(original_content.strip().split('\n')) == 3
                
                # Output file should not exist or be empty
                assert not output_path.exists() or output_path.stat().st_size == 0
        
        finally:
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)
    
    def test_atomic_operations_ensure_data_integrity(self, sample_jsonl_data):
        """Test that all operations are atomic - either complete success or complete rollback"""
        from src.pruner.safety import SafePruner
        
        # Create input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in sample_jsonl_data:
                json.dump(entry, f)
                f.write('\n')
            input_path = Path(f.name)
        
        output_path = input_path.with_suffix('.pruned.jsonl')
        
        try:
            # Mock file write to fail partway through
            with patch('src.pruner.safety.SafePruner._atomic_write_with_verification') as mock_write:
                mock_write.side_effect = IOError("Disk full")
                
                safe_pruner = SafePruner(pruning_level='medium')
                result = safe_pruner.prune_with_complete_safety(input_path, output_path)
                
                # Should fail and rollback completely
                assert result['success'] is False
                assert result['recovered'] is True
                
                # No partial files should remain
                assert not output_path.exists()
                
                # Original should be intact
                assert input_path.exists()
                
        finally:
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)
    
    def test_checkpoint_system_enables_recovery(self, sample_jsonl_data):
        """Test checkpoint system allows recovery from any point in processing"""
        from src.pruner.safety import SafePruner
        
        # Create input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in sample_jsonl_data:
                json.dump(entry, f)
                f.write('\n')
            input_path = Path(f.name)
        
        output_path = input_path.with_suffix('.pruned.jsonl')
        
        try:
            safe_pruner = SafePruner(pruning_level='medium')
            
            # Create checkpoint
            checkpoint_id = safe_pruner.create_checkpoint(input_path)
            assert checkpoint_id is not None
            assert len(checkpoint_id) > 0
            
            # Simulate failure and recovery
            recovery_result = safe_pruner.recover_from_checkpoint(checkpoint_id)
            assert recovery_result['success'] is True
            assert recovery_result['restored_files'] > 0
            
        finally:
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)
    
    def test_zero_data_loss_guarantee(self, sample_jsonl_data):
        """Test that zero data loss is guaranteed even in worst-case scenarios"""
        from src.pruner.safety import SafePruner
        
        # Create input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in sample_jsonl_data:
                json.dump(entry, f)
                f.write('\n')
            input_path = Path(f.name)
        
        original_content = input_path.read_text()
        original_checksum = hashlib.sha256(original_content.encode()).hexdigest()
        
        try:
            safe_pruner = SafePruner(pruning_level='medium')
            
            # Simulate multiple types of failures
            failure_scenarios = [
                'validation_failure',
                'write_failure', 
                'checksum_mismatch',
                'permission_denied'
            ]
            
            for scenario in failure_scenarios:
                with patch.object(safe_pruner, '_simulate_failure') as mock_fail:
                    mock_fail.return_value = scenario
                    
                    result = safe_pruner.prune_with_complete_safety(input_path, input_path.with_suffix('.out'))
                    
                    # Original file should be intact after any failure
                    assert input_path.exists()
                    current_content = input_path.read_text()
                    current_checksum = hashlib.sha256(current_content.encode()).hexdigest()
                    assert current_checksum == original_checksum
        
        finally:
            input_path.unlink(missing_ok=True)


class TestValidationFramework:
    """Test suite for multi-level validation procedures"""
    
    @pytest.fixture
    def validation_test_data(self):
        """Data for validation testing"""
        return {
            'original': [
                {"uuid": "msg-001", "type": "user", "parentUuid": None, "message": {"content": "test"}},
                {"uuid": "msg-002", "type": "assistant", "parentUuid": "msg-001", "message": {"content": "response"}},
                {"uuid": "msg-003", "type": "tool_call", "parentUuid": "msg-002", "message": {"tool": "Read", "result": "data"}}
            ],
            'pruned_valid': [
                {"uuid": "msg-001", "type": "user", "parentUuid": None, "message": {"content": "test"}},
                {"uuid": "msg-002", "type": "assistant", "parentUuid": "msg-001", "message": {"content": "response"}}
            ],
            'pruned_invalid': [
                {"uuid": "msg-002", "type": "assistant", "parentUuid": "msg-001", "message": {"content": "response"}},
                {"uuid": "msg-003", "type": "tool_call", "parentUuid": "msg-999", "message": {"tool": "Read", "result": "data"}}
            ]
        }
    
    def test_level_0_pre_operation_validation(self, validation_test_data):
        """Test Level 0: Pre-operation validation (file accessibility, format check)"""
        from src.pruner.validator import ValidationFramework
        
        validator = ValidationFramework()
        
        # Test with valid file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in validation_test_data['original']:
                json.dump(entry, f)
                f.write('\n')
            valid_file = Path(f.name)
        
        try:
            result = validator.validate_level_0_pre_operation(valid_file)
            assert result['valid'] is True
            assert result['accessible'] is True
            assert result['format_valid'] is True
            assert len(result['errors']) == 0
            
        finally:
            valid_file.unlink()
        
        # Test with invalid file
        result = validator.validate_level_0_pre_operation(Path("/nonexistent/file.jsonl"))
        assert result['valid'] is False
        assert result['accessible'] is False
        assert 'File not found' in str(result['errors']) or 'File not accessible' in str(result['errors'])
    
    def test_level_1_backup_integrity_validation(self, validation_test_data):
        """Test Level 1: Backup integrity verification (checksum validation)"""
        from src.pruner.validator import ValidationFramework
        
        validator = ValidationFramework()
        
        # Create original file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in validation_test_data['original']:
                json.dump(entry, f)
                f.write('\n')
            original_file = Path(f.name)
        
        # Create backup
        backup_file = original_file.with_suffix('.backup.jsonl')
        shutil.copy2(original_file, backup_file)
        
        try:
            result = validator.validate_level_1_backup_integrity(original_file, backup_file)
            assert result['valid'] is True
            assert result['checksums_match'] is True
            assert result['backup_complete'] is True
            assert len(result['errors']) == 0
            
            # Test with corrupted backup
            backup_file.write_text("corrupted content")
            result = validator.validate_level_1_backup_integrity(original_file, backup_file)
            assert result['valid'] is False
            assert result['checksums_match'] is False
            
        finally:
            original_file.unlink()
            backup_file.unlink()
    
    def test_level_2_pruning_validation(self, validation_test_data):
        """Test Level 2: Pruning validation (conversation integrity, content preservation)"""
        from src.pruner.validator import ValidationFramework
        
        validator = ValidationFramework()
        
        # Test valid pruning
        result = validator.validate_level_2_pruning_integrity(
            validation_test_data['original'],
            validation_test_data['pruned_valid']
        )
        assert result['valid'] is True
        assert result['conversation_chains_intact'] is True
        assert result['essential_content_preserved'] is True
        assert result['false_positive_rate'] < 0.01
        
        # Test invalid pruning (broken chains)
        result = validator.validate_level_2_pruning_integrity(
            validation_test_data['original'],
            validation_test_data['pruned_invalid']
        )
        assert result['valid'] is False
        assert result['conversation_chains_intact'] is False
        assert 'orphaned_messages' in result
        assert len(result['orphaned_messages']) > 0
    
    def test_level_3_post_operation_validation(self, validation_test_data):
        """Test Level 3: Post-operation validation (file format, size metrics)"""
        from src.pruner.validator import ValidationFramework
        
        validator = ValidationFramework()
        
        # Create output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in validation_test_data['pruned_valid']:
                json.dump(entry, f)
                f.write('\n')
            output_file = Path(f.name)
        
        try:
            result = validator.validate_level_3_post_operation(
                len(validation_test_data['original']),
                output_file,
                target_compression=0.5
            )
            assert result['valid'] is True
            assert result['format_valid'] is True
            assert result['compression_achieved'] > 0
            assert result['within_target_range'] is True
            
        finally:
            output_file.unlink()
    
    def test_level_4_recovery_testing(self, validation_test_data):
        """Test Level 4: Recovery testing (backup restoration verification)"""
        from src.pruner.validator import ValidationFramework
        
        validator = ValidationFramework()
        
        # Create original and backup files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in validation_test_data['original']:
                json.dump(entry, f)
                f.write('\n')
            original_file = Path(f.name)
        
        backup_file = original_file.with_suffix('.backup.jsonl')
        shutil.copy2(original_file, backup_file)
        
        # Simulate corruption of original
        original_file.write_text("corrupted data")
        
        try:
            result = validator.validate_level_4_recovery_capability(original_file, backup_file)
            assert result['valid'] is True
            assert result['backup_restorable'] is True
            assert result['recovery_successful'] is True
            assert result['data_integrity_maintained'] is True
            
        finally:
            original_file.unlink()
            backup_file.unlink()
    
    def test_comprehensive_validation_pipeline(self, validation_test_data):
        """Test complete validation pipeline with all levels"""
        from src.pruner.validator import ValidationFramework
        
        validator = ValidationFramework()
        
        # Create test files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in validation_test_data['original']:
                json.dump(entry, f)
                f.write('\n')
            input_file = Path(f.name)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in validation_test_data['pruned_valid']:
                json.dump(entry, f)
                f.write('\n')
            output_file = Path(f.name)
        
        backup_file = input_file.with_suffix('.backup.jsonl')
        shutil.copy2(input_file, backup_file)
        
        try:
            result = validator.run_comprehensive_validation(
                input_file, 
                output_file, 
                backup_file,
                validation_test_data['original'],
                validation_test_data['pruned_valid']
            )
            
            assert result['overall_valid'] is True
            assert result['level_0']['valid'] is True
            assert result['level_1']['valid'] is True
            assert result['level_2']['valid'] is True
            assert result['level_3']['valid'] is True
            assert result['level_4']['valid'] is True
            assert result['validation_time'] < 5.0  # <5 seconds requirement
            
        finally:
            input_file.unlink()
            output_file.unlink()
            backup_file.unlink()


class TestBackupManagementSystem:
    """Test suite for backup management with checksums and retention"""
    
    def test_timestamped_backup_creation(self):
        """Test creation of timestamped backups with metadata"""
        from src.utils.backup import BackupManager
        
        backup_manager = BackupManager()
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"uuid": "test", "content": "test data"}\n')
            test_file = Path(f.name)
        
        try:
            backup_result = backup_manager.create_timestamped_backup(test_file)
            
            assert backup_result['success'] is True
            assert 'backup_path' in backup_result
            assert 'timestamp' in backup_result
            assert 'checksum' in backup_result
            assert 'metadata' in backup_result
            
            backup_path = Path(backup_result['backup_path'])
            assert backup_path.exists()
            
            # Verify timestamp is in filename
            assert datetime.now().strftime('%Y%m%d') in backup_path.name
            
            # Verify content integrity (handle compressed backups)
            original_content = test_file.read_text()
            if backup_path.suffix == '.gz':
                import gzip
                with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                    backup_content = f.read()
            else:
                backup_content = backup_path.read_text()
            
            assert backup_content == original_content
            
        finally:
            test_file.unlink()
            if 'backup_path' in backup_result:
                Path(backup_result['backup_path']).unlink(missing_ok=True)
    
    def test_backup_integrity_verification(self):
        """Test backup integrity verification using checksums"""
        from src.utils.backup import BackupManager
        
        backup_manager = BackupManager()
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"uuid": "test", "content": "integrity test"}\n')
            test_file = Path(f.name)
        
        try:
            # Create backup
            backup_result = backup_manager.create_timestamped_backup(test_file)
            backup_path = Path(backup_result['backup_path'])
            
            # Verify integrity
            integrity_result = backup_manager.verify_backup_integrity(test_file, backup_path)
            assert integrity_result['valid'] is True
            assert integrity_result['checksums_match'] is True
            assert integrity_result['sizes_match'] is True
            
            # Corrupt backup and test
            backup_path.write_text("corrupted content")
            integrity_result = backup_manager.verify_backup_integrity(test_file, backup_path)
            assert integrity_result['valid'] is False
            assert integrity_result['checksums_match'] is False
            
        finally:
            test_file.unlink()
            if 'backup_path' in backup_result:
                Path(backup_result['backup_path']).unlink(missing_ok=True)
    
    def test_automatic_cleanup_retention_policy(self):
        """Test automated cleanup of old backups with retention policies"""
        from src.utils.backup import BackupManager
        
        backup_manager = BackupManager(retention_days=7, max_backups=5)
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"uuid": "test", "content": "retention test"}\n')
            test_file = Path(f.name)
        
        backup_paths = []
        try:
            # Create multiple backups
            for i in range(10):
                backup_result = backup_manager.create_timestamped_backup(test_file)
                backup_paths.append(Path(backup_result['backup_path']))
                time.sleep(0.1)  # Ensure different timestamps
            
            # Apply retention policy
            cleanup_result = backup_manager.cleanup_old_backups(test_file)
            
            assert cleanup_result['success'] is True
            assert cleanup_result['removed_count'] > 0
            assert cleanup_result['retained_count'] <= 5
            
            # Verify only recent backups remain
            remaining_backups = [p for p in backup_paths if p.exists()]
            assert len(remaining_backups) <= 5
            
        finally:
            test_file.unlink()
            for backup_path in backup_paths:
                backup_path.unlink(missing_ok=True)
    
    def test_space_efficient_compression(self):
        """Test space-efficient backup storage with compression"""
        from src.utils.backup import BackupManager
        
        backup_manager = BackupManager(enable_compression=True)
        
        # Create large test file
        large_content = '\n'.join([
            f'{{"uuid": "msg-{i:03d}", "content": "test content that repeats" * 10}}'
            for i in range(1000)
        ])
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write(large_content)
            test_file = Path(f.name)
        
        try:
            backup_result = backup_manager.create_timestamped_backup(test_file)
            backup_path = Path(backup_result['backup_path'])
            
            # Verify compression achieved
            original_size = test_file.stat().st_size
            backup_size = backup_path.stat().st_size
            compression_ratio = (original_size - backup_size) / original_size
            
            assert compression_ratio > 0.1  # At least 10% compression
            assert backup_result['compressed'] is True
            assert backup_result['compression_ratio'] > 0.1
            
            # Verify data can be restored
            restored_content = backup_manager.restore_from_backup(backup_path)
            assert restored_content == large_content
            
        finally:
            test_file.unlink()
            if 'backup_path' in backup_result:
                Path(backup_result['backup_path']).unlink(missing_ok=True)


class TestEdgeCaseHandling:
    """Test suite for comprehensive edge case testing"""
    
    def test_malformed_json_recovery(self):
        """Test handling and recovery from malformed JSON entries"""
        from src.pruner.safety import SafePruner
        
        # Create file with mixed valid and invalid JSON
        malformed_content = '''{"uuid": "msg-001", "type": "user", "message": {"content": "valid"}}
{"uuid": "msg-002", "type": "assistant", "message": {invalid json here}
{"uuid": "msg-003", "type": "user", "message": {"content": "also valid"}}
{"incomplete": "json"'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write(malformed_content)
            input_file = Path(f.name)
        
        output_file = input_file.with_suffix('.pruned.jsonl')
        
        try:
            safe_pruner = SafePruner(pruning_level='medium')
            result = safe_pruner.prune_with_complete_safety(input_file, output_file)
            
            # Should handle gracefully
            assert result['success'] is True or result['recovered'] is True
            assert 'malformed_entries_detected' in result
            assert result['malformed_entries_detected'] > 0
            
            # Valid entries should be processed
            if result['success']:
                assert output_file.exists()
                with open(output_file) as f:
                    valid_entries = [json.loads(line) for line in f if line.strip()]
                    assert len(valid_entries) >= 2  # At least 2 valid entries
            
        finally:
            input_file.unlink()
            output_file.unlink(missing_ok=True)
    
    def test_circular_reference_detection(self):
        """Test detection and resolution of circular references"""
        from src.pruner.validator import ValidationFramework
        
        validator = ValidationFramework()
        
        # Create circular reference scenario
        circular_data = [
            {"uuid": "msg-001", "parentUuid": "msg-003"},  # Points to msg-003
            {"uuid": "msg-002", "parentUuid": "msg-001"},  # Points to msg-001
            {"uuid": "msg-003", "parentUuid": "msg-002"}   # Points to msg-002 (circular)
        ]
        
        result = validator.detect_circular_references(circular_data)
        
        assert result['circular_references_found'] is True
        assert len(result['circular_chains']) > 0
        assert 'msg-001' in str(result['circular_chains'])
        assert 'msg-002' in str(result['circular_chains'])
        assert 'msg-003' in str(result['circular_chains'])
    
    def test_missing_parent_message_handling(self):
        """Test handling of orphaned messages with missing parents"""
        from src.pruner.validator import ValidationFramework
        
        validator = ValidationFramework()
        
        # Create orphaned message scenario
        orphaned_data = [
            {"uuid": "msg-001", "parentUuid": None},
            {"uuid": "msg-002", "parentUuid": "msg-999"},  # Parent doesn't exist
            {"uuid": "msg-003", "parentUuid": "msg-001"}   # Valid parent
        ]
        
        result = validator.detect_orphaned_messages(orphaned_data)
        
        assert result['orphaned_messages_found'] is True
        assert 'msg-002' in result['orphaned_messages']
        assert 'msg-003' not in result['orphaned_messages']
        assert len(result['orphaned_messages']) == 1
    
    def test_empty_null_message_processing(self):
        """Test processing of empty and null messages"""
        from src.pruner.safety import SafePruner
        
        # Create data with empty/null content
        edge_case_data = [
            {"uuid": "msg-001", "type": "user", "message": {"content": ""}},  # Empty content
            {"uuid": "msg-002", "type": "assistant", "message": None},         # Null message
            {"uuid": "msg-003", "type": "tool_call", "message": {}},          # Empty message object
            {"uuid": "msg-004", "type": "user", "message": {"content": "valid"}}  # Valid for comparison
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in edge_case_data:
                json.dump(entry, f)
                f.write('\n')
            input_file = Path(f.name)
        
        output_file = input_file.with_suffix('.pruned.jsonl')
        
        try:
            safe_pruner = SafePruner(pruning_level='medium')
            result = safe_pruner.prune_with_complete_safety(input_file, output_file)
            
            # Should handle edge cases gracefully
            assert result['success'] is True or result['recovered'] is True
            assert 'edge_cases_detected' in result
            
        finally:
            input_file.unlink()
            output_file.unlink(missing_ok=True)
    
    def test_very_large_file_performance(self):
        """Test performance validation with very large files (10MB+)"""
        from src.pruner.safety import SafePruner
        import psutil
        import os
        
        # Generate large dataset
        large_data = []
        for i in range(50000):  # Generate ~10MB of data
            large_data.append({
                "uuid": f"msg-{i:05d}",
                "type": "user" if i % 2 == 0 else "assistant",
                "parentUuid": f"msg-{i-1:05d}" if i > 0 else None,
                "message": {"content": f"Message {i} with some content that makes it reasonably sized"},
                "timestamp": f"2025-08-01T{i//3600:02d}:{(i//60)%60:02d}:{i%60:02d}"
            })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in large_data:
                json.dump(entry, f)
                f.write('\n')
            input_file = Path(f.name)
        
        output_file = input_file.with_suffix('.pruned.jsonl')
        
        try:
            # Monitor memory usage
            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            start_time = time.time()
            safe_pruner = SafePruner(pruning_level='medium')
            result = safe_pruner.prune_with_complete_safety(input_file, output_file)
            processing_time = time.time() - start_time
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = memory_after - memory_before
            
            # Performance targets
            assert processing_time < 30.0  # Should complete in <30 seconds
            assert memory_used < 200  # Should use <200MB additional memory
            assert result['success'] is True or result['recovered'] is True
            
        finally:
            input_file.unlink()
            output_file.unlink(missing_ok=True)
    
    def test_concurrent_access_safety(self):
        """Test safety under concurrent access scenarios"""
        from src.pruner.safety import SafePruner
        import threading
        import concurrent.futures
        
        # Create test data
        test_data = [
            {"uuid": f"msg-{i:03d}", "type": "user", "message": {"content": f"test {i}"}}
            for i in range(100)
        ]
        
        def concurrent_pruning_task(task_id):
            """Task for concurrent execution"""
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                for entry in test_data:
                    json.dump(entry, f)
                    f.write('\n')
                input_file = Path(f.name)
            
            output_file = input_file.with_suffix(f'.pruned_{task_id}.jsonl')
            
            try:
                safe_pruner = SafePruner(pruning_level='medium')
                result = safe_pruner.prune_with_complete_safety(input_file, output_file)
                return result
            finally:
                input_file.unlink(missing_ok=True)
                output_file.unlink(missing_ok=True)
        
        # Run concurrent tasks
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(concurrent_pruning_task, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All tasks should succeed or recover gracefully
        for result in results:
            assert result['success'] is True or result['recovered'] is True


class TestValidationReporting:
    """Test suite for validation reporting and monitoring framework"""
    
    def test_detailed_validation_report_generation(self):
        """Test generation of detailed validation reports with pass/fail status"""
        from src.utils.reporting import ValidationReporter
        
        reporter = ValidationReporter()
        
        # Sample validation results
        validation_results = {
            'level_0': {'valid': True, 'errors': [], 'duration': 0.1},
            'level_1': {'valid': True, 'errors': [], 'duration': 0.2},
            'level_2': {'valid': False, 'errors': ['Chain break detected'], 'duration': 0.3},
            'level_3': {'valid': True, 'errors': [], 'duration': 0.1},
            'level_4': {'valid': True, 'errors': [], 'duration': 0.2}
        }
        
        report = reporter.generate_validation_report(validation_results)
        
        assert 'overall_status' in report
        assert 'validation_summary' in report
        assert 'detailed_results' in report
        assert 'performance_metrics' in report
        assert 'recommendations' in report
        
        # Should identify overall failure due to level 2
        assert report['overall_status'] == 'FAILED'
        assert report['failed_levels'] == ['level_2']
        assert 'Chain break detected' in str(report['detailed_results']['level_2']['errors'])
    
    def test_performance_metrics_tracking(self):
        """Test performance metrics and timing data collection"""
        from src.utils.reporting import PerformanceTracker
        
        tracker = PerformanceTracker()
        
        # Simulate performance tracking
        tracker.start_operation('pruning')
        time.sleep(0.1)
        tracker.end_operation('pruning')
        
        tracker.start_operation('validation')
        time.sleep(0.05)
        tracker.end_operation('validation')
        
        metrics = tracker.get_performance_metrics()
        
        assert 'operations' in metrics
        assert 'pruning' in metrics['operations']
        assert 'validation' in metrics['operations']
        assert metrics['operations']['pruning']['duration'] >= 0.1
        assert metrics['operations']['validation']['duration'] >= 0.05
        assert 'total_duration' in metrics
        assert 'memory_usage' in metrics
    
    def test_quality_metrics_tracking(self):
        """Test quality metrics tracking and trend analysis"""
        from src.utils.reporting import QualityTracker
        
        tracker = QualityTracker()
        
        # Track multiple operations
        operations = [
            {'compression_ratio': 0.6, 'false_positive_rate': 0.005, 'integrity_maintained': True},
            {'compression_ratio': 0.55, 'false_positive_rate': 0.008, 'integrity_maintained': True},
            {'compression_ratio': 0.65, 'false_positive_rate': 0.003, 'integrity_maintained': True}
        ]
        
        for op in operations:
            tracker.record_operation(op)
        
        trends = tracker.analyze_quality_trends()
        
        assert 'average_compression_ratio' in trends
        assert 'average_false_positive_rate' in trends
        assert 'integrity_success_rate' in trends
        assert trends['average_false_positive_rate'] < 0.01  # <1% requirement
        assert trends['integrity_success_rate'] == 1.0
    
    def test_error_logging_actionable_recommendations(self):
        """Test error logging with actionable recommendations"""
        from src.utils.reporting import ErrorLogger
        
        logger = ErrorLogger()
        
        # Log different types of errors
        errors = [
            {'type': 'validation_failure', 'details': 'Conversation chain broken', 'severity': 'high'},
            {'type': 'backup_failure', 'details': 'Checksum mismatch', 'severity': 'critical'},
            {'type': 'performance_issue', 'details': 'Processing time exceeded', 'severity': 'medium'}
        ]
        
        for error in errors:
            logger.log_error(error)
        
        recommendations = logger.get_actionable_recommendations()
        
        assert len(recommendations) > 0
        for rec in recommendations:
            assert 'action' in rec
            assert 'priority' in rec
            assert 'description' in rec
        
        # Should have specific recommendations for each error type
        actions = [rec['action'] for rec in recommendations]
        assert any('chain integrity' in action.lower() for action in actions)
        assert any('backup' in action.lower() for action in actions)
    
    def test_alerting_system_validation_failures(self):
        """Test alerting systems for validation failures"""
        from src.utils.reporting import AlertingSystem
        
        alerting = AlertingSystem()
        
        # Configure alert thresholds
        alerting.configure_thresholds({
            'false_positive_rate': 0.01,
            'processing_time': 5.0,
            'integrity_failures': 0
        })
        
        # Test various alert conditions
        test_cases = [
            {'false_positive_rate': 0.02, 'should_alert': True},
            {'processing_time': 6.0, 'should_alert': True},
            {'integrity_failures': 1, 'should_alert': True},
            {'false_positive_rate': 0.005, 'processing_time': 2.0, 'should_alert': False}
        ]
        
        for case in test_cases:
            alerts = alerting.check_alert_conditions(case)
            if case['should_alert']:
                assert len(alerts) > 0
            else:
                assert len(alerts) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])