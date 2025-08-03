"""
Comprehensive Edge Case Test Collection for Phase 3 Safety System
Tests all possible failure scenarios and recovery mechanisms

Edge Cases Covered:
1. File system failures (disk full, permissions, concurrent access)
2. Data corruption scenarios (partial writes, encoding issues)
3. Memory pressure and resource constraints
4. Network interruptions and timeout scenarios
5. Malformed data and recovery procedures
"""

import pytest
import json
import tempfile
import shutil
import time
import os
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import concurrent.futures
import signal
import psutil

# Import test fixtures
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))


class TestFileSystemFailures:
    """Test file system related failure scenarios and recovery"""
    
    def test_disk_full_during_backup(self):
        """Test graceful handling when disk fills up during backup creation"""
        from src.pruner.safety import SafePruner
        from src.utils.backup import BackupManager
        
        # Create test data
        test_data = [{"uuid": f"msg-{i:03d}", "content": "test"} for i in range(100)]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in test_data:
                json.dump(entry, f)
                f.write('\n')
            input_file = Path(f.name)
        
        try:
            # Mock disk full error during backup
            with patch('shutil.copy2') as mock_copy:
                mock_copy.side_effect = OSError(28, "No space left on device")
                
                safe_pruner = SafePruner(pruning_level='medium')
                result = safe_pruner.prune_with_complete_safety(input_file, input_file.with_suffix('.out'))
                
                # Should fail gracefully without corrupting original
                assert result['success'] is False
                assert result['recovered'] is True
                assert 'disk_full' in str(result['error']).lower() or 'space' in str(result['error']).lower()
                
                # Original file should be intact
                assert input_file.exists()
                restored_data = []
                with open(input_file) as f:
                    for line in f:
                        if line.strip():
                            restored_data.append(json.loads(line))
                assert len(restored_data) == 100
        
        finally:
            input_file.unlink()
    
    def test_permission_denied_scenarios(self):
        """Test handling of permission denied errors"""
        from src.pruner.safety import SafePruner
        
        # Create test file
        test_data = [{"uuid": "msg-001", "content": "test"}]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            json.dump(test_data[0], f)
            input_file = Path(f.name)
        
        try:
            # Make file read-only
            input_file.chmod(0o444)
            output_file = input_file.with_suffix('.out')
            
            # Mock permission error on backup directory
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                mock_mkdir.side_effect = PermissionError("Permission denied")
                
                safe_pruner = SafePruner(pruning_level='medium')
                result = safe_pruner.prune_with_complete_safety(input_file, output_file)
                
                # Should fail gracefully
                assert result['success'] is False
                assert result['recovered'] is True
                assert 'permission' in str(result['error']).lower()
        
        finally:
            input_file.chmod(0o644)  # Restore permissions for cleanup
            input_file.unlink()
    
    def test_concurrent_file_access_conflicts(self):
        """Test handling of concurrent file access conflicts"""
        from src.pruner.safety import SafePruner
        import fcntl
        
        # Create test file
        test_data = [{"uuid": f"msg-{i:03d}", "content": f"test {i}"} for i in range(50)]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in test_data:
                json.dump(entry, f)
                f.write('\n')
            input_file = Path(f.name)
        
        def concurrent_lock_task():
            """Task that locks the file"""
            try:
                with open(input_file, 'r') as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    time.sleep(2)  # Hold lock for 2 seconds
            except:
                pass  # Ignore lock conflicts
        
        try:
            # Start concurrent task that locks the file
            thread = threading.Thread(target=concurrent_lock_task)
            thread.start()
            time.sleep(0.1)  # Ensure lock is acquired
            
            # Try to process file while locked
            safe_pruner = SafePruner(pruning_level='medium')
            result = safe_pruner.prune_with_complete_safety(
                input_file, 
                input_file.with_suffix('.out'),
                timeout=1.0  # Short timeout
            )
            
            # Should handle lock conflict gracefully
            if not result['success']:
                assert result['recovered'] is True
                assert 'lock' in str(result['error']).lower() or 'access' in str(result['error']).lower()
            
            thread.join()
        
        finally:
            input_file.unlink()
    
    def test_filesystem_readonly_scenarios(self):
        """Test behavior when filesystem becomes read-only"""
        from src.pruner.safety import SafePruner
        
        # Create test file
        test_data = [{"uuid": "msg-001", "content": "readonly test"}]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            json.dump(test_data[0], f)
            input_file = Path(f.name)
        
        try:
            # Mock read-only filesystem
            with patch('pathlib.Path.write_text') as mock_write:
                mock_write.side_effect = OSError(30, "Read-only file system")
                
                safe_pruner = SafePruner(pruning_level='medium')
                result = safe_pruner.prune_with_complete_safety(input_file, input_file.with_suffix('.out'))
                
                # Should detect read-only filesystem and fail safely
                assert result['success'] is False
                assert result['recovered'] is True
                assert 'read-only' in str(result['error']).lower() or 'readonly' in str(result['error']).lower()
        
        finally:
            input_file.unlink()


class TestDataCorruptionScenarios:
    """Test data corruption scenarios and recovery mechanisms"""
    
    def test_partial_write_interruption(self):
        """Test recovery from partial write interruptions"""
        from src.pruner.safety import SafePruner
        
        # Create test data
        test_data = [{"uuid": f"msg-{i:03d}", "content": "data"} for i in range(100)]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in test_data:
                json.dump(entry, f)
                f.write('\n')
            input_file = Path(f.name)
        
        output_file = input_file.with_suffix('.out')
        
        try:
            # Mock interruption during write
            original_write = open.__enter__
            call_count = 0
            
            def mock_write_interrupt(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 3:  # Interrupt on 3rd write operation
                    raise KeyboardInterrupt("Simulated interruption")
                return original_write(*args, **kwargs)
            
            with patch('builtins.open.__enter__', side_effect=mock_write_interrupt):
                safe_pruner = SafePruner(pruning_level='medium')
                result = safe_pruner.prune_with_complete_safety(input_file, output_file)
                
                # Should recover from interruption
                assert result['success'] is False
                assert result['recovered'] is True
                
                # Output file should not exist or be empty
                assert not output_file.exists() or output_file.stat().st_size == 0
                
                # Original should be intact
                assert input_file.exists()
        
        finally:
            input_file.unlink()
            output_file.unlink(missing_ok=True)
    
    def test_encoding_corruption_handling(self):
        """Test handling of encoding corruption in files"""
        from src.pruner.safety import SafePruner
        
        # Create file with mixed encoding issues
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.jsonl', delete=False) as f:
            # Valid UTF-8
            f.write(b'{"uuid": "msg-001", "content": "valid"}\n')
            # Invalid UTF-8 sequence
            f.write(b'{"uuid": "msg-002", "content": "\xff\xfe invalid"}\n')
            # Valid UTF-8 again
            f.write(b'{"uuid": "msg-003", "content": "valid again"}\n')
            input_file = Path(f.name)
        
        output_file = input_file.with_suffix('.out')
        
        try:
            safe_pruner = SafePruner(pruning_level='medium')
            result = safe_pruner.prune_with_complete_safety(input_file, output_file)
            
            # Should handle encoding issues gracefully
            if result['success']:
                # Valid entries should be processed
                assert output_file.exists()
            else:
                # Should recover gracefully
                assert result['recovered'] is True
                assert 'encoding' in str(result['error']).lower() or 'utf' in str(result['error']).lower()
        
        finally:
            input_file.unlink()
            output_file.unlink(missing_ok=True)
    
    def test_checksum_mismatch_detection(self):
        """Test detection and handling of checksum mismatches"""
        from src.utils.backup import BackupManager
        
        # Create test file
        test_content = '{"uuid": "msg-001", "content": "checksum test"}\n'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write(test_content)
            input_file = Path(f.name)
        
        try:
            backup_manager = BackupManager()
            
            # Create backup
            backup_result = backup_manager.create_timestamped_backup(input_file)
            backup_file = Path(backup_result['backup_path'])
            
            # Corrupt backup file
            backup_file.write_text('{"corrupted": "data"}\n')
            
            # Verify checksum mismatch is detected
            integrity_result = backup_manager.verify_backup_integrity(input_file, backup_file)
            
            assert integrity_result['valid'] is False
            assert integrity_result['checksums_match'] is False
            assert 'checksum_mismatch' in integrity_result
        
        finally:
            input_file.unlink()
            if 'backup_path' in backup_result:
                Path(backup_result['backup_path']).unlink(missing_ok=True)
    
    def test_json_structure_corruption(self):
        """Test handling of corrupted JSON structure"""
        from src.pruner.validator import ValidationFramework
        
        validator = ValidationFramework()
        
        # Various JSON corruption scenarios
        corruption_scenarios = [
            '{"uuid": "msg-001", "type": "user"',  # Incomplete JSON
            '{"uuid": "msg-002", "type": "user"} extra_text',  # Extra text
            '{"uuid": "msg-003", "type":: "user"}',  # Invalid syntax
            '{uuid: "msg-004", "type": "user"}',  # Unquoted key
            '{"uuid": null, "type": "user"}',  # Null UUID
            '[]',  # Wrong data type
        ]
        
        for i, corrupted_json in enumerate(corruption_scenarios):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                f.write(corrupted_json + '\n')
                test_file = Path(f.name)
            
            try:
                result = validator.validate_json_structure(test_file)
                
                # Should detect corruption
                assert result['valid'] is False
                assert result['corruption_detected'] is True
                assert len(result['corrupted_lines']) > 0
                
            finally:
                test_file.unlink()


class TestMemoryPressureScenarios:
    """Test behavior under memory pressure and resource constraints"""
    
    def test_large_file_memory_management(self):
        """Test memory management with very large files"""
        from src.pruner.safety import SafePruner
        import psutil
        
        # Generate very large dataset
        large_data = []
        for i in range(100000):  # 100k messages
            large_data.append({
                "uuid": f"msg-{i:06d}",
                "type": "user" if i % 2 == 0 else "assistant",
                "parentUuid": f"msg-{i-1:06d}" if i > 0 else None,
                "message": {"content": f"Large message content {i} " + "x" * 100},
                "timestamp": f"2025-08-01T10:00:{i%60:02d}"
            })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in large_data:
                json.dump(entry, f)
                f.write('\n')
            input_file = Path(f.name)
        
        output_file = input_file.with_suffix('.out')
        
        try:
            # Monitor memory usage
            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            safe_pruner = SafePruner(pruning_level='medium', enable_streaming=True)
            result = safe_pruner.prune_with_complete_safety(input_file, output_file)
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = memory_after - memory_before
            
            # Should handle large files without excessive memory usage
            assert memory_used < 500  # <500MB for 100k messages
            assert result['success'] is True or result['recovered'] is True
            
        finally:
            input_file.unlink()
            output_file.unlink(missing_ok=True)
    
    def test_memory_exhaustion_recovery(self):
        """Test recovery from memory exhaustion scenarios"""
        from src.pruner.safety import SafePruner
        
        # Create test data
        test_data = [{"uuid": f"msg-{i:03d}", "content": "test"} for i in range(1000)]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in test_data:
                json.dump(entry, f)
                f.write('\n')
            input_file = Path(f.name)
        
        try:
            # Mock memory error
            with patch('src.pruner.core.JSONLPruner.process_file') as mock_process:
                mock_process.side_effect = MemoryError("Out of memory")
                
                safe_pruner = SafePruner(pruning_level='medium')
                result = safe_pruner.prune_with_complete_safety(input_file, input_file.with_suffix('.out'))
                
                # Should recover from memory error
                assert result['success'] is False
                assert result['recovered'] is True
                assert 'memory' in str(result['error']).lower()
        
        finally:
            input_file.unlink()
    
    def test_resource_limit_handling(self):
        """Test handling of system resource limits"""
        from src.pruner.safety import SafePruner
        
        # Create test file
        test_data = [{"uuid": f"msg-{i:03d}", "content": "resource test"} for i in range(100)]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in test_data:
                json.dump(entry, f)
                f.write('\n')
            input_file = Path(f.name)
        
        try:
            # Mock file descriptor limit
            with patch('builtins.open') as mock_open:
                mock_open.side_effect = OSError(24, "Too many open files")
                
                safe_pruner = SafePruner(pruning_level='medium')
                result = safe_pruner.prune_with_complete_safety(input_file, input_file.with_suffix('.out'))
                
                # Should handle resource limits
                assert result['success'] is False
                assert result['recovered'] is True
                assert 'resource' in str(result['error']).lower() or 'files' in str(result['error']).lower()
        
        finally:
            input_file.unlink()


class TestNetworkTimeoutScenarios:
    """Test behavior with network interruptions and timeouts"""
    
    def test_backup_to_network_storage_timeout(self):
        """Test timeout handling when backing up to network storage"""
        from src.utils.backup import BackupManager
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"uuid": "msg-001", "content": "network test"}\n')
            input_file = Path(f.name)
        
        try:
            # Mock network timeout
            with patch('shutil.copy2') as mock_copy:
                import socket
                mock_copy.side_effect = socket.timeout("Network timeout")
                
                backup_manager = BackupManager(backup_location="/network/path")
                result = backup_manager.create_timestamped_backup(input_file)
                
                # Should handle network timeout gracefully
                assert result['success'] is False
                assert 'timeout' in str(result['error']).lower() or 'network' in str(result['error']).lower()
        
        finally:
            input_file.unlink()
    
    def test_distributed_validation_network_failure(self):
        """Test validation when distributed validation services fail"""
        from src.pruner.validator import ValidationFramework
        
        validator = ValidationFramework()
        
        # Mock network service failure
        with patch('requests.post') as mock_post:
            mock_post.side_effect = ConnectionError("Network unreachable")
            
            # Test data
            test_data = [{"uuid": "msg-001", "content": "test"}]
            
            # Should fall back to local validation
            result = validator.validate_with_fallback(test_data, test_data)
            
            assert result['validation_method'] == 'local_fallback'
            assert result['network_service_available'] is False
            assert result['valid'] is not None  # Should still provide validation result


class TestMalformedDataRecovery:
    """Test comprehensive malformed data handling and recovery"""
    
    def test_mixed_valid_invalid_json_processing(self):
        """Test processing files with mix of valid and invalid JSON"""
        from src.pruner.safety import SafePruner
        
        # Create file with mixed content
        mixed_content = [
            '{"uuid": "msg-001", "type": "user", "message": {"content": "valid"}}',
            '{"uuid": "msg-002", "type": "assistant", "message": {invalid syntax here}',
            '{"uuid": "msg-003", "type": "user", "message": {"content": "also valid"}}',
            'not json at all',
            '{"uuid": "msg-004", "type": "assistant", "message": {"content": "final valid"}}'
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for line in mixed_content:
                f.write(line + '\n')
            input_file = Path(f.name)
        
        output_file = input_file.with_suffix('.out')
        
        try:
            safe_pruner = SafePruner(pruning_level='medium')
            result = safe_pruner.prune_with_complete_safety(input_file, output_file)
            
            # Should process valid entries and report malformed ones
            assert 'malformed_entries_detected' in result
            assert result['malformed_entries_detected'] >= 2  # At least 2 invalid entries
            
            if result['success']:
                # Valid entries should be processed
                valid_entries = []
                with open(output_file) as f:
                    for line in f:
                        if line.strip():
                            valid_entries.append(json.loads(line))
                assert len(valid_entries) >= 3  # At least 3 valid entries
        
        finally:
            input_file.unlink()
            output_file.unlink(missing_ok=True)
    
    def test_truncated_file_recovery(self):
        """Test recovery from truncated files"""
        from src.pruner.safety import SafePruner
        
        # Create normal file
        normal_content = [
            {"uuid": "msg-001", "type": "user", "message": {"content": "complete"}},
            {"uuid": "msg-002", "type": "assistant", "message": {"content": "also complete"}}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in normal_content:
                json.dump(entry, f)
                f.write('\n')
            # Add truncated entry
            f.write('{"uuid": "msg-003", "type": "user", "mess')  # Truncated
            input_file = Path(f.name)
        
        output_file = input_file.with_suffix('.out')
        
        try:
            safe_pruner = SafePruner(pruning_level='medium')
            result = safe_pruner.prune_with_complete_safety(input_file, output_file)
            
            # Should handle truncation gracefully
            assert 'truncation_detected' in result or 'malformed_entries_detected' in result
            
            if result['success']:
                # Complete entries should be processed
                valid_entries = []
                with open(output_file) as f:
                    for line in f:
                        if line.strip():
                            valid_entries.append(json.loads(line))
                assert len(valid_entries) >= 2  # Complete entries
        
        finally:
            input_file.unlink()
            output_file.unlink(missing_ok=True)
    
    def test_duplicate_uuid_handling(self):
        """Test handling of duplicate UUIDs in data"""
        from src.pruner.validator import ValidationFramework
        
        validator = ValidationFramework()
        
        # Create data with duplicate UUIDs
        duplicate_data = [
            {"uuid": "msg-001", "type": "user", "message": {"content": "first"}},
            {"uuid": "msg-002", "type": "assistant", "message": {"content": "response"}},
            {"uuid": "msg-001", "type": "user", "message": {"content": "duplicate"}},  # Duplicate UUID
            {"uuid": "msg-003", "type": "tool_call", "message": {"tool": "Read"}}
        ]
        
        result = validator.detect_duplicate_uuids(duplicate_data)
        
        assert result['duplicates_found'] is True
        assert 'msg-001' in result['duplicate_uuids']
        assert len(result['duplicate_uuids']) == 1
        assert result['duplicate_count'] == 1
    
    def test_missing_required_fields_handling(self):
        """Test handling of messages missing required fields"""
        from src.pruner.validator import ValidationFramework
        
        validator = ValidationFramework()
        
        # Create data with missing required fields
        incomplete_data = [
            {"uuid": "msg-001", "type": "user", "message": {"content": "complete"}},
            {"type": "assistant", "message": {"content": "missing uuid"}},  # No UUID
            {"uuid": "msg-003", "message": {"content": "missing type"}},  # No type
            {"uuid": "msg-004", "type": "user"},  # No message
            {"uuid": "msg-005", "type": "assistant", "message": {"content": "complete again"}}
        ]
        
        result = validator.validate_required_fields(incomplete_data)
        
        assert result['valid'] is False
        assert result['missing_fields_detected'] is True
        assert len(result['invalid_entries']) >= 3  # At least 3 invalid entries
        assert any('uuid' in str(entry) for entry in result['invalid_entries'])
        assert any('type' in str(entry) for entry in result['invalid_entries'])
        assert any('message' in str(entry) for entry in result['invalid_entries'])


class TestConcurrencyAndRaceConditions:
    """Test concurrent operations and race condition handling"""
    
    def test_concurrent_backup_creation(self):
        """Test safety of concurrent backup creation"""
        from src.utils.backup import BackupManager
        
        # Create test file
        test_content = '{"uuid": "msg-001", "content": "concurrent test"}\n'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write(test_content)
            input_file = Path(f.name)
        
        def create_backup_task(task_id):
            """Concurrent backup creation task"""
            try:
                backup_manager = BackupManager()
                result = backup_manager.create_timestamped_backup(input_file)
                return result
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        try:
            # Run concurrent backup creation
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(create_backup_task, i) for i in range(5)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # All tasks should succeed or fail gracefully
            successful_backups = [r for r in results if r.get('success', False)]
            assert len(successful_backups) >= 1  # At least one should succeed
            
            # No corruption should occur
            for result in successful_backups:
                backup_path = Path(result['backup_path'])
                assert backup_path.exists()
                assert backup_path.read_text() == test_content
        
        finally:
            input_file.unlink()
            # Cleanup backup files
            for result in results:
                if result.get('success') and 'backup_path' in result:
                    Path(result['backup_path']).unlink(missing_ok=True)
    
    def test_race_condition_file_modification(self):
        """Test race conditions during file modification"""
        from src.pruner.safety import SafePruner
        
        # Create test file
        test_data = [{"uuid": f"msg-{i:03d}", "content": "race test"} for i in range(100)]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in test_data:
                json.dump(entry, f)
                f.write('\n')
            input_file = Path(f.name)
        
        results = []
        
        def modify_file_task():
            """Task that modifies the file during processing"""
            try:
                time.sleep(0.1)  # Wait for processing to start
                with open(input_file, 'a') as f:
                    f.write('{"uuid": "modified", "content": "added during processing"}\n')
                return True
            except:
                return False
        
        def process_file_task():
            """Task that processes the file"""
            try:
                safe_pruner = SafePruner(pruning_level='medium')
                result = safe_pruner.prune_with_complete_safety(input_file, input_file.with_suffix('.out'))
                return result
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        try:
            # Start both tasks concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                modify_future = executor.submit(modify_file_task)
                process_future = executor.submit(process_file_task)
                
                modify_result = modify_future.result()
                process_result = process_future.result()
            
            # Processing should handle concurrent modification gracefully
            if not process_result.get('success', False):
                assert process_result.get('recovered', False)
                assert 'concurrent' in str(process_result.get('error', '')).lower() or \
                       'modified' in str(process_result.get('error', '')).lower()
        
        finally:
            input_file.unlink()
            Path(str(input_file) + '.out').unlink(missing_ok=True)
    
    def test_signal_interruption_handling(self):
        """Test handling of signal interruptions (SIGINT, SIGTERM)"""
        from src.pruner.safety import SafePruner
        
        # Create test file
        test_data = [{"uuid": f"msg-{i:03d}", "content": "signal test"} for i in range(1000)]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in test_data:
                json.dump(entry, f)
                f.write('\n')
            input_file = Path(f.name)
        
        output_file = input_file.with_suffix('.out')
        
        def interrupt_task():
            """Task that sends interrupt signal"""
            time.sleep(0.2)  # Wait for processing to start
            os.kill(os.getpid(), signal.SIGINT)
        
        try:
            # Start interrupt task
            interrupt_thread = threading.Thread(target=interrupt_task)
            interrupt_thread.start()
            
            # Process file with signal handling
            safe_pruner = SafePruner(pruning_level='medium', handle_signals=True)
            
            try:
                result = safe_pruner.prune_with_complete_safety(input_file, output_file)
            except KeyboardInterrupt:
                # Should have cleanup mechanism
                result = {'success': False, 'interrupted': True, 'recovered': True}
            
            interrupt_thread.join()
            
            # Should handle interruption gracefully
            if not result.get('success', False):
                assert result.get('recovered', False) or result.get('interrupted', False)
                
                # No partial files should remain
                assert not output_file.exists() or output_file.stat().st_size == 0
                
                # Original should be intact
                assert input_file.exists()
        
        finally:
            input_file.unlink()
            output_file.unlink(missing_ok=True)


class TestRecoveryProcedures:
    """Test comprehensive recovery procedures from various failure states"""
    
    def test_backup_chain_recovery(self):
        """Test recovery using backup chain when multiple failures occur"""
        from src.utils.backup import BackupManager
        
        # Create test file
        original_content = '{"uuid": "msg-001", "content": "original"}\n'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write(original_content)
            input_file = Path(f.name)
        
        try:
            backup_manager = BackupManager()
            
            # Create multiple backups
            backup1 = backup_manager.create_timestamped_backup(input_file)
            time.sleep(0.1)
            
            # Modify file
            input_file.write_text('{"uuid": "msg-002", "content": "modified"}\n')
            backup2 = backup_manager.create_timestamped_backup(input_file)
            
            # Corrupt current file
            input_file.write_text("corrupted data")
            
            # Corrupt most recent backup
            Path(backup2['backup_path']).write_text("also corrupted")
            
            # Recovery should use earlier backup
            recovery_result = backup_manager.recover_from_backup_chain(input_file)
            
            assert recovery_result['success'] is True
            assert recovery_result['recovered_from_backup'] is True
            assert recovery_result['backup_used'] == backup1['backup_path']
            
            # File should be restored to first backup content
            restored_content = input_file.read_text()
            assert restored_content == original_content
        
        finally:
            input_file.unlink()
            if 'backup_path' in backup1:
                Path(backup1['backup_path']).unlink(missing_ok=True)
            if 'backup_path' in backup2:
                Path(backup2['backup_path']).unlink(missing_ok=True)
    
    def test_progressive_recovery_strategy(self):
        """Test progressive recovery strategy with multiple fallback levels"""
        from src.pruner.safety import SafePruner
        
        # Create test file
        test_data = [{"uuid": f"msg-{i:03d}", "content": "recovery test"} for i in range(100)]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in test_data:
                json.dump(entry, f)
                f.write('\n')
            input_file = Path(f.name)
        
        try:
            safe_pruner = SafePruner(pruning_level='medium')
            
            # Test progressive recovery levels
            recovery_levels = [
                'memory_cleanup',
                'temp_file_cleanup', 
                'backup_restoration',
                'emergency_stop'
            ]
            
            for level in recovery_levels:
                recovery_result = safe_pruner.execute_recovery_strategy(input_file, level)
                
                assert 'strategy_executed' in recovery_result
                assert recovery_result['strategy_executed'] == level
                assert recovery_result['success'] is True or recovery_result['partial_success'] is True
        
        finally:
            input_file.unlink()
    
    def test_disaster_recovery_complete_restore(self):
        """Test complete disaster recovery from total system failure"""
        from src.utils.backup import BackupManager
        from src.pruner.safety import SafePruner
        
        # Create test environment
        test_data = [{"uuid": f"msg-{i:03d}", "content": "disaster test"} for i in range(50)]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in test_data:
                json.dump(entry, f)
                f.write('\n')
            input_file = Path(f.name)
        
        try:
            # Create complete backup environment
            backup_manager = BackupManager()
            safe_pruner = SafePruner(pruning_level='medium')
            
            # Create backup
            backup_result = backup_manager.create_timestamped_backup(input_file)
            
            # Simulate complete disaster (file corruption, metadata loss)
            input_file.write_text("total corruption")
            
            # Execute disaster recovery
            disaster_recovery = safe_pruner.execute_disaster_recovery(
                input_file,
                backup_manager=backup_manager
            )
            
            assert disaster_recovery['success'] is True
            assert disaster_recovery['recovery_method'] in ['backup_restore', 'emergency_backup']
            assert disaster_recovery['data_integrity_verified'] is True
            
            # Verify complete restoration
            restored_data = []
            with open(input_file) as f:
                for line in f:
                    if line.strip():
                        restored_data.append(json.loads(line))
            
            assert len(restored_data) == 50  # All original data restored
        
        finally:
            input_file.unlink()
            if 'backup_path' in backup_result:
                Path(backup_result['backup_path']).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])