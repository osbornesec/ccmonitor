"""
Backup Management System with Checksums and Retention
Phase 3 - Comprehensive backup infrastructure for safe pruning

Features:
- Timestamped backup creation with metadata preservation
- Backup integrity verification using SHA256 checksums
- Space-efficient backup storage with optional compression
- Automated cleanup with configurable retention policies
- Backup chain management for progressive recovery
- Disaster recovery capabilities
"""

import json
import logging
import time
import hashlib
import shutil
import gzip
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import tempfile
import uuid as uuid_module
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class BackupMetadata:
    """Metadata for backup tracking and management"""
    backup_id: str
    original_file: str
    backup_path: str
    timestamp: str
    original_size: int
    backup_size: int
    checksum: str
    compressed: bool
    compression_ratio: float
    creation_time: float
    verification_status: str
    retention_expires: str


class BackupManager:
    """
    Comprehensive backup management system with integrity verification
    
    Provides timestamped backups, checksum verification, compression,
    retention policies, and disaster recovery capabilities.
    """
    
    def __init__(
        self,
        backup_location: Optional[str] = None,
        enable_compression: bool = True,
        compression_level: int = 6,
        retention_days: int = 7,
        max_backups: int = 10,
        verify_on_create: bool = True
    ):
        """
        Initialize backup manager
        
        Args:
            backup_location: Custom backup directory (default: ~/.claude/backups)
            enable_compression: Enable gzip compression for space efficiency
            compression_level: Gzip compression level (1-9)
            retention_days: Days to retain backups
            max_backups: Maximum number of backups per file
            verify_on_create: Verify backup integrity immediately after creation
        """
        self.enable_compression = enable_compression
        self.compression_level = compression_level
        self.retention_days = retention_days
        self.max_backups = max_backups
        self.verify_on_create = verify_on_create
        
        # Setup backup directory
        if backup_location:
            self.backup_dir = Path(backup_location)
        else:
            self.backup_dir = Path.home() / '.claude' / 'backups'
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata tracking
        self.metadata_file = self.backup_dir / 'backup_metadata.json'
        self.metadata = self._load_metadata()
        
        # Statistics
        self.stats = {
            'backups_created': 0,
            'backups_verified': 0,
            'backups_restored': 0,
            'verification_failures': 0,
            'space_saved_bytes': 0,
            'total_backup_time': 0.0
        }
    
    def create_timestamped_backup(self, file_path: Path) -> Dict[str, Any]:
        """
        Create timestamped backup with metadata and integrity verification
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            Dictionary with backup results and metadata
        """
        start_time = time.perf_counter()
        
        try:
            # Validate input file
            if not file_path.exists():
                return {'success': False, 'error': f'File not found: {file_path}'}
            
            if not file_path.is_file():
                return {'success': False, 'error': f'Path is not a file: {file_path}'}
            
            # Generate backup metadata
            backup_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid_module.uuid4().hex[:8]}"
            timestamp = datetime.now().isoformat()
            
            # Create backup filename
            file_stem = file_path.stem
            file_suffix = file_path.suffix
            if self.enable_compression:
                backup_filename = f"{file_stem}_backup_{backup_id}{file_suffix}.gz"
            else:
                backup_filename = f"{file_stem}_backup_{backup_id}{file_suffix}"
            
            backup_path = self.backup_dir / backup_filename
            
            # Calculate original file checksum and size
            original_checksum = self._calculate_checksum(file_path)
            original_size = file_path.stat().st_size
            
            # Create backup
            if self.enable_compression:
                backup_size = self._create_compressed_backup(file_path, backup_path)
            else:
                shutil.copy2(file_path, backup_path)
                backup_size = backup_path.stat().st_size
            
            # Calculate compression ratio
            compression_ratio = (original_size - backup_size) / original_size if original_size > 0 else 0.0
            
            # Create metadata
            expires_date = datetime.now() + timedelta(days=self.retention_days)
            metadata = BackupMetadata(
                backup_id=backup_id,
                original_file=str(file_path),
                backup_path=str(backup_path),
                timestamp=timestamp,
                original_size=original_size,
                backup_size=backup_size,
                checksum=original_checksum,
                compressed=self.enable_compression,
                compression_ratio=compression_ratio,
                creation_time=time.perf_counter() - start_time,
                verification_status='pending',
                retention_expires=expires_date.isoformat()
            )
            
            # Verify backup if enabled
            if self.verify_on_create:
                verification_result = self.verify_backup_integrity(file_path, backup_path)
                metadata.verification_status = 'verified' if verification_result['valid'] else 'failed'
                
                if not verification_result['valid']:
                    # Remove failed backup
                    backup_path.unlink(missing_ok=True)
                    return {
                        'success': False,
                        'error': 'Backup verification failed',
                        'verification_details': verification_result
                    }
            else:
                metadata.verification_status = 'skipped'
            
            # Store metadata
            self._store_backup_metadata(metadata)
            
            # Update statistics
            self.stats['backups_created'] += 1
            if metadata.verification_status == 'verified':
                self.stats['backups_verified'] += 1
            self.stats['space_saved_bytes'] += max(0, original_size - backup_size)
            self.stats['total_backup_time'] += metadata.creation_time
            
            logger.info(f"Created backup {backup_id} with {compression_ratio:.2%} compression in {metadata.creation_time:.3f}s")
            
            return {
                'success': True,
                'backup_id': backup_id,
                'backup_path': str(backup_path),
                'timestamp': timestamp,
                'checksum': original_checksum,
                'compressed': self.enable_compression,
                'compression_ratio': compression_ratio,
                'verification_status': metadata.verification_status,
                'creation_time': metadata.creation_time,
                'metadata': asdict(metadata)
            }
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def verify_backup_integrity(self, original_path: Path, backup_path: Path) -> Dict[str, Any]:
        """
        Verify backup integrity using checksum comparison
        
        Args:
            original_path: Path to original file
            backup_path: Path to backup file
            
        Returns:
            Dictionary with verification results
        """
        start_time = time.perf_counter()
        
        try:
            result = {
                'valid': True,
                'checksums_match': False,
                'sizes_match': False,
                'content_verified': False,
                'original_checksum': None,
                'backup_checksum': None,
                'verification_time': 0.0
            }
            
            # Check files exist
            if not original_path.exists():
                result['valid'] = False
                result['error'] = f'Original file not found: {original_path}'
                return result
            
            if not backup_path.exists():
                result['valid'] = False
                result['error'] = f'Backup file not found: {backup_path}'
                return result
            
            # Calculate original checksum
            result['original_checksum'] = self._calculate_checksum(original_path)
            
            # Handle compressed backups
            if backup_path.suffix == '.gz':
                # Verify compressed backup by extracting and comparing
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_path = Path(temp_file.name)
                
                try:
                    # Extract compressed backup
                    with gzip.open(backup_path, 'rb') as gz_file:
                        with open(temp_path, 'wb') as out_file:
                            shutil.copyfileobj(gz_file, out_file)
                    
                    # Calculate extracted checksum
                    result['backup_checksum'] = self._calculate_checksum(temp_path)
                    result['checksums_match'] = result['original_checksum'] == result['backup_checksum']
                    
                    # Compare sizes
                    result['sizes_match'] = original_path.stat().st_size == temp_path.stat().st_size
                    
                finally:
                    temp_path.unlink(missing_ok=True)
            else:
                # Direct backup verification
                result['backup_checksum'] = self._calculate_checksum(backup_path)
                result['checksums_match'] = result['original_checksum'] == result['backup_checksum']
                result['sizes_match'] = original_path.stat().st_size == backup_path.stat().st_size
            
            # Content verification by sampling (for large files)
            if result['checksums_match'] and result['sizes_match']:
                result['content_verified'] = True
            elif original_path.stat().st_size > 100 * 1024 * 1024:  # >100MB
                # Sample-based verification for large files
                result['content_verified'] = self._verify_content_sample(original_path, backup_path)
            
            # Overall validity
            result['valid'] = result['checksums_match'] and (result['sizes_match'] or result['content_verified'])
            
            result['verification_time'] = time.perf_counter() - start_time
            
            if result['valid']:
                self.stats['backups_verified'] += 1
            else:
                self.stats['verification_failures'] += 1
            
            logger.debug(f"Backup verification: {'PASS' if result['valid'] else 'FAIL'} in {result['verification_time']:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return {
                'valid': False,
                'error': str(e),
                'verification_time': time.perf_counter() - start_time
            }
    
    def restore_from_backup(self, backup_path: Path, target_path: Optional[Path] = None) -> str:
        """
        Restore file from backup
        
        Args:
            backup_path: Path to backup file
            target_path: Optional target path (default: extract content and return as string)
            
        Returns:
            Restored content as string or empty string if target_path provided
        """
        try:
            if backup_path.suffix == '.gz':
                # Restore from compressed backup
                with gzip.open(backup_path, 'rt', encoding='utf-8') as gz_file:
                    content = gz_file.read()
            else:
                # Restore from uncompressed backup
                with open(backup_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            if target_path:
                # Write to target file
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.stats['backups_restored'] += 1
                logger.info(f"Restored backup to {target_path}")
                return ""
            else:
                # Return content
                self.stats['backups_restored'] += 1
                return content
                
        except Exception as e:
            logger.error(f"Backup restoration failed: {e}")
            raise
    
    def cleanup_old_backups(self, file_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Clean up old backups based on retention policy
        
        Args:
            file_path: Optional specific file to clean backups for
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            removed_count = 0
            space_freed = 0
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            # Load current metadata
            current_metadata = self._load_metadata()
            updated_metadata = []
            
            for backup_info in current_metadata:
                should_remove = False
                backup_path = Path(backup_info['backup_path'])
                
                # Check retention policy
                backup_date = datetime.fromisoformat(backup_info['timestamp'])
                if backup_date < cutoff_date:
                    should_remove = True
                
                # Check max backups per file
                if file_path and backup_info['original_file'] == str(file_path):
                    # Count backups for this file
                    file_backups = [b for b in current_metadata if b['original_file'] == str(file_path)]
                    file_backups.sort(key=lambda x: x['timestamp'], reverse=True)
                    
                    if len(file_backups) > self.max_backups:
                        # Remove oldest backups beyond max_backups
                        backup_index = next((i for i, b in enumerate(file_backups) if b['backup_id'] == backup_info['backup_id']), -1)
                        if backup_index >= self.max_backups:
                            should_remove = True
                
                if should_remove and backup_path.exists():
                    try:
                        space_freed += backup_path.stat().st_size
                        backup_path.unlink()
                        removed_count += 1
                        logger.debug(f"Removed old backup: {backup_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove backup {backup_path}: {e}")
                        updated_metadata.append(backup_info)  # Keep in metadata if removal failed
                else:
                    updated_metadata.append(backup_info)
            
            # Update metadata file
            self._save_metadata(updated_metadata)
            
            logger.info(f"Cleanup removed {removed_count} backups, freed {space_freed / 1024 / 1024:.1f}MB")
            
            return {
                'success': True,
                'removed_count': removed_count,
                'retained_count': len(updated_metadata),
                'space_freed_bytes': space_freed,
                'space_freed_mb': space_freed / 1024 / 1024
            }
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def recover_from_backup_chain(self, original_path: Path) -> Dict[str, Any]:
        """
        Recover using backup chain - try most recent valid backup first
        
        Args:
            original_path: Path to original file that needs recovery
            
        Returns:
            Dictionary with recovery results
        """
        try:
            # Find all backups for this file
            current_metadata = self._load_metadata()
            file_backups = [
                backup for backup in current_metadata 
                if backup['original_file'] == str(original_path)
            ]
            
            if not file_backups:
                return {
                    'success': False,
                    'error': 'No backups found for file',
                    'recovered_from_backup': False
                }
            
            # Sort by timestamp (most recent first)
            file_backups.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Try each backup until one works
            for backup_info in file_backups:
                backup_path = Path(backup_info['backup_path'])
                
                if not backup_path.exists():
                    logger.warning(f"Backup file missing: {backup_path}")
                    continue
                
                try:
                    # Verify backup integrity first
                    if backup_info['verification_status'] == 'verified':
                        # Trust previously verified backup
                        verification_valid = True
                    else:
                        # Verify now
                        verification_result = self._verify_backup_standalone(backup_path, backup_info)
                        verification_valid = verification_result['valid']
                    
                    if verification_valid:
                        # Restore from this backup
                        self.restore_from_backup(backup_path, original_path)
                        
                        # Verify restoration
                        restored_checksum = self._calculate_checksum(original_path)
                        if restored_checksum == backup_info['checksum']:
                            logger.info(f"Successfully recovered from backup {backup_info['backup_id']}")
                            return {
                                'success': True,
                                'recovered_from_backup': True,
                                'backup_used': backup_info['backup_path'],
                                'backup_timestamp': backup_info['timestamp'],
                                'recovery_method': 'backup_chain'
                            }
                    
                except Exception as e:
                    logger.warning(f"Failed to restore from backup {backup_info['backup_id']}: {e}")
                    continue
            
            # No working backup found
            return {
                'success': False,
                'error': 'No valid backups found in chain',
                'attempted_backups': len(file_backups),
                'recovered_from_backup': False
            }
            
        except Exception as e:
            logger.error(f"Backup chain recovery failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'recovered_from_backup': False
            }
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """Get comprehensive backup statistics"""
        current_metadata = self._load_metadata()
        
        # Calculate statistics
        total_backups = len(current_metadata)
        total_original_size = sum(backup['original_size'] for backup in current_metadata)
        total_backup_size = sum(backup['backup_size'] for backup in current_metadata)
        
        compression_savings = total_original_size - total_backup_size
        avg_compression = compression_savings / total_original_size if total_original_size > 0 else 0
        
        # Group by verification status
        verification_stats = {}
        for backup in current_metadata:
            status = backup['verification_status']
            verification_stats[status] = verification_stats.get(status, 0) + 1
        
        return {
            'total_backups': total_backups,
            'total_original_size_mb': total_original_size / 1024 / 1024,
            'total_backup_size_mb': total_backup_size / 1024 / 1024,
            'space_savings_mb': compression_savings / 1024 / 1024,
            'average_compression_ratio': avg_compression,
            'verification_status_counts': verification_stats,
            'operation_stats': self.stats.copy(),
            'backup_directory': str(self.backup_dir),
            'retention_policy': {
                'retention_days': self.retention_days,
                'max_backups_per_file': self.max_backups
            }
        }
    
    def list_backups(self, file_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        List available backups
        
        Args:
            file_path: Optional file path to filter backups for specific file
            
        Returns:
            List of backup information dictionaries
        """
        current_metadata = self._load_metadata()
        
        if file_path:
            # Filter for specific file
            file_backups = [
                backup for backup in current_metadata 
                if backup['original_file'] == str(file_path)
            ]
            return sorted(file_backups, key=lambda x: x['timestamp'], reverse=True)
        else:
            # Return all backups
            return sorted(current_metadata, key=lambda x: x['timestamp'], reverse=True)
    
    # Helper methods
    
    def _create_compressed_backup(self, source_path: Path, backup_path: Path) -> int:
        """Create compressed backup and return size"""
        with open(source_path, 'rb') as src_file:
            with gzip.open(backup_path, 'wb', compresslevel=self.compression_level) as gz_file:
                shutil.copyfileobj(src_file, gz_file)
        
        return backup_path.stat().st_size
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _verify_content_sample(self, original_path: Path, backup_path: Path, sample_size: int = 1024) -> bool:
        """Verify backup content by sampling for large files"""
        try:
            # Sample beginning and end of files
            with open(original_path, 'rb') as orig_file:
                orig_start = orig_file.read(sample_size)
                orig_file.seek(-sample_size, 2)  # Seek to end - sample_size
                orig_end = orig_file.read(sample_size)
            
            if backup_path.suffix == '.gz':
                with gzip.open(backup_path, 'rb') as backup_file:
                    backup_start = backup_file.read(sample_size)
                    backup_file.seek(-sample_size, 2)
                    backup_end = backup_file.read(sample_size)
            else:
                with open(backup_path, 'rb') as backup_file:
                    backup_start = backup_file.read(sample_size)
                    backup_file.seek(-sample_size, 2)
                    backup_end = backup_file.read(sample_size)
            
            return orig_start == backup_start and orig_end == backup_end
            
        except Exception:
            return False
    
    def _verify_backup_standalone(self, backup_path: Path, backup_info: Dict[str, Any]) -> Dict[str, Any]:
        """Verify backup without original file (using stored checksum)"""
        try:
            if backup_path.suffix == '.gz':
                # Extract and verify compressed backup
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_path = Path(temp_file.name)
                
                try:
                    with gzip.open(backup_path, 'rb') as gz_file:
                        with open(temp_path, 'wb') as out_file:
                            shutil.copyfileobj(gz_file, out_file)
                    
                    backup_checksum = self._calculate_checksum(temp_path)
                    
                finally:
                    temp_path.unlink(missing_ok=True)
            else:
                backup_checksum = self._calculate_checksum(backup_path)
            
            return {
                'valid': backup_checksum == backup_info['checksum'],
                'checksum_match': backup_checksum == backup_info['checksum']
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _load_metadata(self) -> List[Dict[str, Any]]:
        """Load backup metadata from file"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            logger.warning(f"Failed to load backup metadata: {e}")
            return []
    
    def _save_metadata(self, metadata: List[Dict[str, Any]]):
        """Save backup metadata to file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save backup metadata: {e}")
    
    def _store_backup_metadata(self, metadata: BackupMetadata):
        """Store single backup metadata"""
        current_metadata = self._load_metadata()
        current_metadata.append(asdict(metadata))
        self._save_metadata(current_metadata)
        
        # Update instance metadata
        self.metadata = current_metadata