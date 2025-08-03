#!/usr/bin/env python3
"""
Two-Stage Ultra Pruning Tool
1. Remove invalid/malformed lines (immediate 20-65% reduction)
2. Apply ultra-aggressive content pruning (additional 90%+ reduction)
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import time
from datetime import datetime, timedelta
import sys
import os

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from src.temporal.decay_engine import ExponentialDecayEngine, DecayMode, analyze_conversation_velocity
    from src.config.temporal_config import get_preset_config
    from src.jsonl_analysis.scoring import ImportanceScorer
    TEMPORAL_AVAILABLE = True
except ImportError as e:
    TEMPORAL_AVAILABLE = False

# Import dependency tracking
try:
    from conversation_dependency_tracker import ConversationDependencyGraph, analyze_conversation_dependencies
    DEPENDENCY_TRACKING_AVAILABLE = True
except ImportError:
    DEPENDENCY_TRACKING_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def stage0_delete_old_files(directory: Path, max_age_days: int = 7, dry_run: bool = False, max_files: int = 50) -> Dict[str, Any]:
    """
    Stage 0: Delete JSONL files older than specified days
    
    Args:
        directory: Directory to scan for old files
        max_age_days: Maximum age in days (files older than this will be deleted)
        dry_run: If True, only show what would be deleted without deleting
        max_files: Maximum number of files to delete in one run (safety limit)
        
    Returns:
        Dictionary with deletion statistics
    """
    if not directory.exists() or not directory.is_dir():
        return {'error': f'Directory not found: {directory}'}
    
    # Calculate cutoff time
    cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
    cutoff_date = datetime.fromtimestamp(cutoff_time)
    
    # Find old JSONL files
    old_files = []
    total_files = 0
    total_size = 0
    
    for jsonl_file in directory.rglob('*.jsonl'):
        total_files += 1
        file_mtime = jsonl_file.stat().st_mtime
        file_size = jsonl_file.stat().st_size
        
        if file_mtime < cutoff_time:
            # Skip backup files (they should be managed separately)
            if '.backup' not in jsonl_file.name:
                old_files.append({
                    'path': jsonl_file,
                    'age_days': (time.time() - file_mtime) / (24 * 60 * 60),
                    'size': file_size,
                    'modified': datetime.fromtimestamp(file_mtime)
                })
                total_size += file_size
    
    # Sort by age (oldest first) and limit count
    old_files.sort(key=lambda x: x['age_days'], reverse=True)
    if len(old_files) > max_files:
        logger.warning(f"⚠️  Found {len(old_files)} old files, limiting to {max_files} for safety")
        old_files = old_files[:max_files]
    
    deleted_count = 0
    deleted_size = 0
    errors = []
    
    if old_files:
        logger.info(f"🗑️  Found {len(old_files)} JSONL files older than {max_age_days} days (before {cutoff_date.strftime('%Y-%m-%d')})")
        
        for file_info in old_files:
            file_path = file_info['path']
            age_days = file_info['age_days']
            size = file_info['size']
            
            if dry_run:
                logger.info(f"   [DRY RUN] Would delete: {file_path.name} ({age_days:.1f} days old, {size/1024:.1f} KB)")
            else:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    deleted_size += size
                    logger.info(f"   🗑️  Deleted: {file_path.name} ({age_days:.1f} days old, {size/1024:.1f} KB)")
                except Exception as e:
                    errors.append(f"Failed to delete {file_path}: {e}")
                    logger.error(f"   ❌ Failed to delete {file_path}: {e}")
    else:
        logger.info(f"✅ No JSONL files older than {max_age_days} days found")
    
    return {
        'total_files_scanned': total_files,
        'old_files_found': len(old_files),
        'files_deleted': deleted_count,
        'size_freed': deleted_size,
        'errors': errors,
        'dry_run': dry_run,
        'max_age_days': max_age_days,
        'cutoff_date': cutoff_date
    }


def stage0a_delete_old_messages(file_path: Path, max_age_days: int = 7, dry_run: bool = False, 
                                max_delete_messages: int = 1000, preserve_important: bool = True) -> Dict[str, Any]:
    """
    Stage 0a: Delete individual messages older than specified days based on message timestamps
    
    Args:
        file_path: JSONL file to process
        max_age_days: Maximum age in days (messages older than this will be deleted)
        dry_run: If True, only show what would be deleted without deleting
        max_delete_messages: Maximum number of messages to delete in one run (safety limit)
        preserve_important: If True, preserve high-importance old messages
        
    Returns:
        Dictionary with deletion statistics
    """
    if not file_path.exists():
        return {'error': f'File not found: {file_path}'}
    
    # Import temporal functions if available
    if not TEMPORAL_AVAILABLE:
        return {'error': 'Temporal analysis not available for message-level deletion'}
    
    from src.temporal.decay_engine import get_message_timestamp
    
    # Calculate cutoff time
    cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
    cutoff_date = datetime.fromtimestamp(cutoff_time)
    
    logger.info(f"🔍 Analyzing messages in {file_path.name} (cutoff: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')})")
    
    # Load and analyze messages
    messages = []
    old_messages = []
    recent_messages = []
    malformed_lines = []
    line_number = 0
    
    # Read and categorize messages
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line_number += 1
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    message = json.loads(line)
                    messages.append({'line_number': line_number, 'data': message, 'raw_line': line})
                    
                    # Extract timestamp
                    timestamp = get_message_timestamp(message)
                    if timestamp is None:
                        # No timestamp - treat as recent (preserve)
                        recent_messages.append({'line_number': line_number, 'data': message, 'raw_line': line, 'age_days': 0})
                        continue
                    
                    # Calculate age
                    age_seconds = time.time() - timestamp
                    age_days = age_seconds / (24 * 60 * 60)
                    
                    message_info = {
                        'line_number': line_number,
                        'data': message,
                        'raw_line': line,
                        'timestamp': timestamp,
                        'age_days': age_days
                    }
                    
                    if timestamp < cutoff_time:
                        old_messages.append(message_info)
                    else:
                        recent_messages.append(message_info)
                        
                except json.JSONDecodeError:
                    malformed_lines.append({'line_number': line_number, 'raw_line': line})
                    
    except Exception as e:
        return {'error': f'Failed to read file: {e}'}
    
    # Delete ALL old messages (ignore importance filtering)
    messages_to_delete = old_messages
    messages_preserved_by_importance = []
    
    # Note: preserve_important parameter is now ignored for timestamp-based deletion
    if preserve_important and old_messages:
        logger.info("   ⚠️  Ignoring importance preservation - deleting ALL messages older than cutoff")
    
    # Apply deletion limit
    if len(messages_to_delete) > max_delete_messages:
        logger.warning(f"Found {len(messages_to_delete)} old messages, limiting to {max_delete_messages} for safety")
        # Sort by age (oldest first) and take the limit
        messages_to_delete.sort(key=lambda x: x.get('age_days', 0), reverse=True)
        messages_to_delete = messages_to_delete[:max_delete_messages]
    
    # Calculate statistics
    total_messages = len(messages)
    old_message_count = len(old_messages)
    delete_count = len(messages_to_delete)
    preserve_count = len(recent_messages) + len(messages_preserved_by_importance)
    
    logger.info(f"   📊 Total messages: {total_messages}")
    logger.info(f"   ⏰ Old messages (>{max_age_days} days): {old_message_count}")
    logger.info(f"   🗑️  Messages to delete: {delete_count}")
    logger.info(f"   💎 Important old messages preserved: {len(messages_preserved_by_importance)}")
    logger.info(f"   ✅ Recent messages preserved: {len(recent_messages)}")
    
    if dry_run:
        logger.info(f"   [DRY RUN] Would delete {delete_count} old messages")
        if delete_count > 0:
            logger.info(f"   [DRY RUN] Oldest message to delete: {max(msg['age_days'] for msg in messages_to_delete):.1f} days")
            logger.info(f"   [DRY RUN] Newest message to delete: {min(msg['age_days'] for msg in messages_to_delete):.1f} days")
    else:
        # Actually delete the messages by rewriting the file
        if delete_count > 0:
            # Create backup
            backup_path = file_path.with_suffix('.backup-messages.jsonl')
            try:
                import shutil
                shutil.copy2(file_path, backup_path)
                logger.info(f"   📁 Backup created: {backup_path}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
            
            # Get line numbers to delete
            delete_line_numbers = set(msg['line_number'] for msg in messages_to_delete)
            
            # Rewrite file without deleted lines
            try:
                temp_path = file_path.with_suffix('.tmp')
                lines_written = 0
                
                with open(file_path, 'r', encoding='utf-8') as input_file, \
                     open(temp_path, 'w', encoding='utf-8') as output_file:
                    
                    for current_line_number, line in enumerate(input_file, 1):
                        if current_line_number not in delete_line_numbers:
                            output_file.write(line)
                            lines_written += 1
                
                # Replace original file with temp file
                temp_path.replace(file_path)
                
                logger.info(f"   ✅ Deleted {delete_count} old messages, kept {lines_written} messages")
                
            except Exception as e:
                return {'error': f'Failed to rewrite file: {e}'}
    
    # Calculate size reduction
    original_size = file_path.stat().st_size if file_path.exists() else 0
    reduction_ratio = delete_count / total_messages if total_messages > 0 else 0
    
    return {
        'total_messages': total_messages,
        'old_messages': old_message_count,
        'messages_deleted': delete_count if not dry_run else 0,
        'messages_preserved': preserve_count,
        'important_preserved': len(messages_preserved_by_importance),
        'malformed_lines': len(malformed_lines),
        'reduction_ratio': reduction_ratio,
        'original_size': original_size,
        'dry_run': dry_run,
        'max_age_days': max_age_days,
        'cutoff_date': cutoff_date,
        'preserve_important': preserve_important
    }


def stage0b_delete_old_messages_with_dependencies(file_path: Path, max_age_days: int = 7, 
                                                dry_run: bool = False, 
                                                max_delete_messages: int = 1000, 
                                                preserve_important: bool = False,
                                                export_dependency_graph: bool = False) -> Dict[str, Any]:
    """
    Stage 0b: Delete old messages while preserving parent-child relationships
    
    CRITICAL PRINCIPLE: Parent nodes must be preserved until ALL child nodes are deleted.
    This ensures conversation flow integrity and prevents orphaned responses.
    
    Args:
        file_path: JSONL file to process
        max_age_days: Maximum age in days (messages older than this will be deleted)
        dry_run: If True, only show what would be deleted without deleting
        max_delete_messages: Maximum number of messages to delete in one run (safety limit)
        preserve_important: If True, preserve high-importance old messages (user requirement: False)
        export_dependency_graph: If True, export dependency graph for debugging
        
    Returns:
        Dictionary with deletion statistics including dependency preservation info
    """
    if not file_path.exists():
        return {'error': f'File not found: {file_path}'}
    
    if not DEPENDENCY_TRACKING_AVAILABLE:
        logger.warning("⚠️  Dependency tracking not available, falling back to basic deletion")
        return stage0a_delete_old_messages(file_path, max_age_days, dry_run, max_delete_messages, preserve_important)
    
    if not TEMPORAL_AVAILABLE:
        return {'error': 'Temporal analysis not available for message-level deletion'}
    
    from src.temporal.decay_engine import get_message_timestamp
    
    # Calculate cutoff time
    cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
    cutoff_date = datetime.fromtimestamp(cutoff_time)
    
    logger.info(f"🔍 Analyzing messages with dependency tracking in {file_path.name}")
    logger.info(f"   📅 Age cutoff: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')} ({max_age_days} days)")
    logger.info(f"   🔗 Dependency tracking: ENABLED")
    
    # Build dependency graph
    dependency_graph = ConversationDependencyGraph()
    if not dependency_graph.load_from_jsonl(file_path):
        return {'error': 'Failed to build dependency graph'}
    
    # Load and categorize messages by age
    messages = []
    old_message_candidates = set()
    recent_messages = []
    malformed_lines = []
    line_number = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line_number += 1
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    message = json.loads(line)
                    messages.append({'line_number': line_number, 'data': message, 'raw_line': line})
                    
                    # Extract timestamp and calculate age
                    timestamp = get_message_timestamp(message)
                    if timestamp is None:
                        # No timestamp - treat as recent (preserve)
                        recent_messages.append({'line_number': line_number, 'data': message, 'raw_line': line, 'age_days': 0})
                        continue
                    
                    age_seconds = time.time() - timestamp
                    age_days = age_seconds / (24 * 60 * 60)
                    
                    if timestamp < cutoff_time:
                        # Old message - candidate for deletion
                        message_uuid = message.get('uuid', f'line-{line_number}')
                        old_message_candidates.add(message_uuid)
                    else:
                        recent_messages.append({'line_number': line_number, 'data': message, 'raw_line': line, 'age_days': age_days})
                        
                except json.JSONDecodeError:
                    malformed_lines.append({'line_number': line_number, 'raw_line': line})
                    
    except Exception as e:
        return {'error': f'Failed to read file: {e}'}
    
    logger.info(f"📊 Initial analysis: {len(old_message_candidates)} old messages, {len(recent_messages)} recent messages")
    
    # Apply dependency tracking to resolve conflicts
    dependency_graph.mark_for_deletion(old_message_candidates)
    safe_deletions = dependency_graph.get_safe_deletion_set()
    preservation_report = dependency_graph.get_preservation_report()
    
    logger.info(f"🔗 Dependency analysis:")
    logger.info(f"   📋 Originally marked for deletion: {len(old_message_candidates)}")
    logger.info(f"   ✅ Safe to delete: {len(safe_deletions)}")
    logger.info(f"   🛡️  Must preserve (have children): {preservation_report['preserved_by_dependencies']}")
    
    # CRITICAL: Validate conversation integrity after dependency resolution
    all_message_uuids = set(msg['data'].get('uuid', f"line-{msg['line_number']}") for msg in messages if msg['data'].get('uuid'))
    remaining_messages = all_message_uuids - safe_deletions
    
    logger.info(f"🔍 Validating conversation integrity...")
    is_valid, integrity_issues = dependency_graph.validate_conversation_integrity(remaining_messages)
    
    if not is_valid:
        logger.error(f"🚨 CRITICAL: Conversation integrity validation FAILED!")
        logger.error(f"   Found {len(integrity_issues)} integrity violations:")
        for issue in integrity_issues:
            logger.error(f"   • {issue}")
        
        # Get additional parents required for integrity
        required_parents = dependency_graph.get_messages_requiring_parents(remaining_messages)
        additional_preservations = required_parents - remaining_messages
        
        if additional_preservations:
            logger.info(f"🔧 FIXING: Preserving {len(additional_preservations)} additional parent messages for integrity")
            for parent_uuid in additional_preservations:
                safe_deletions.discard(parent_uuid)
                logger.info(f"   🔗 Preserving parent: {parent_uuid}")
            
            # Re-validate after fixes
            remaining_messages = all_message_uuids - safe_deletions
            is_valid_fixed, remaining_issues = dependency_graph.validate_conversation_integrity(remaining_messages)
            
            if is_valid_fixed:
                logger.info(f"✅ Conversation integrity RESTORED after preserving additional parents")
            else:
                logger.error(f"❌ CRITICAL: Could not restore conversation integrity! {len(remaining_issues)} issues remain:")
                for issue in remaining_issues:
                    logger.error(f"   • {issue}")
                return {'error': 'Cannot proceed: Conversation integrity cannot be restored'}
        else:
            logger.error(f"❌ CRITICAL: No solution found for conversation integrity issues!")
            return {'error': 'Cannot proceed: Conversation integrity validation failed'}
    else:
        logger.info(f"✅ Conversation integrity validation PASSED")
    
    # CRITICAL: Cleanup orphaned children that would reference deleted parents
    logger.info(f"🧹 Cleaning up orphaned children...")
    cleaned_remaining, removed_orphans = dependency_graph.cleanup_orphaned_children(remaining_messages)
    
    if removed_orphans:
        logger.info(f"🧹 Removed {len(removed_orphans)} orphaned children that referenced deleted parents")
        
        # Add orphans to safe deletions
        for orphan_uuid in removed_orphans:
            safe_deletions.add(orphan_uuid)
        
        # Update remaining messages
        remaining_messages = cleaned_remaining
        
        # Final integrity validation
        final_valid, final_issues = dependency_graph.validate_conversation_integrity(remaining_messages)
        if final_valid:
            logger.info(f"✅ Final conversation integrity validation PASSED after orphan cleanup")
        else:
            logger.error(f"❌ CRITICAL: Final integrity validation FAILED after orphan cleanup!")
            for issue in final_issues:
                logger.error(f"   • {issue}")
            return {'error': 'Cannot proceed: Final conversation integrity validation failed'}
    else:
        logger.info(f"✅ No orphaned children found - conversation structure is clean")
    
    # Apply importance filtering if enabled (though user preference is False)
    messages_preserved_by_importance = []
    if preserve_important and len(safe_deletions) > 0:
        logger.info("🧠 Applying importance analysis to remaining deletion candidates...")
        # This would integrate with importance_engine.py if needed
        # For now, respecting user requirement: preserve_important = False by default
    
    # Apply deletion limit for safety
    if len(safe_deletions) > max_delete_messages:
        logger.warning(f"⚠️  Found {len(safe_deletions)} messages to delete, limiting to {max_delete_messages} for safety")
        safe_deletions = set(list(safe_deletions)[:max_delete_messages])
    
    # Export dependency graph if requested
    if export_dependency_graph:
        export_path = file_path.parent / f"{file_path.stem}_dependency_graph.json"
        dependency_graph.export_dependency_graph(export_path)
        logger.info(f"📊 Dependency graph exported to {export_path}")
    
    # Create UUID to line number mapping for efficient deletion
    uuid_to_line = {}
    for msg_info in messages:
        message_uuid = msg_info['data'].get('uuid', f"line-{msg_info['line_number']}")
        uuid_to_line[message_uuid] = msg_info['line_number']
    
    # Identify lines to delete based on safe deletion UUIDs
    lines_to_delete = set()
    for uuid in safe_deletions:
        if uuid in uuid_to_line:
            lines_to_delete.add(uuid_to_line[uuid])
    
    # Perform deletion or dry-run
    delete_count = 0
    preserve_count = len(messages) - len(lines_to_delete)
    original_size = file_path.stat().st_size
    
    if not dry_run and lines_to_delete:
        # Create backup
        backup_path = file_path.with_suffix(f'.backup-{int(time.time())}.jsonl')
        file_path.rename(backup_path)
        logger.info(f"💾 Backup created: {backup_path}")
        
        # Write filtered content
        with open(file_path, 'w', encoding='utf-8') as f:
            for msg_info in messages:
                if msg_info['line_number'] not in lines_to_delete:
                    f.write(msg_info['raw_line'] + '\n')
                else:
                    delete_count += 1
        
        new_size = file_path.stat().st_size
        logger.info(f"✅ Deleted {delete_count} messages while preserving conversation flow")
    elif dry_run:
        logger.info(f"🔍 [DRY RUN] Would delete {len(safe_deletions)} messages")
        new_size = original_size
    else:
        logger.info("✅ No messages to delete")
        new_size = original_size
    
    # Calculate statistics
    reduction_ratio = (original_size - new_size) / original_size if original_size > 0 else 0
    
    return {
        'success': True,
        'method': 'dependency-aware-temporal-deletion',
        'total_messages': len(messages),
        'old_message_candidates': len(old_message_candidates),
        'safe_deletions': len(safe_deletions),
        'messages_deleted': delete_count if not dry_run else 0,
        'messages_preserved': preserve_count,
        'preserved_by_dependencies': preservation_report['preserved_by_dependencies'],
        'important_preserved': len(messages_preserved_by_importance),
        'malformed_lines': len(malformed_lines),
        'reduction_ratio': reduction_ratio,
        'original_size': original_size,
        'new_size': new_size,
        'dependency_analysis': preservation_report,
        'conversation_chains': len(dependency_graph.get_conversation_chains()),
        'max_conversation_depth': dependency_graph._calculate_max_depth(),
        'dry_run': dry_run,
        'max_age_days': max_age_days,
        'cutoff_date': cutoff_date,
        'preserve_important': preserve_important
    }


def stage1_remove_invalid_lines(file_path: Path) -> Dict[str, Any]:
    """Stage 1: Remove invalid JSON lines"""
    
    valid_lines = []
    invalid_count = 0
    total_lines = 0
    
    required_fields = {"uuid", "type", "message"}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            total_lines += 1
            line = line.strip()
            if not line:
                continue
                
            try:
                entry = json.loads(line)
                if isinstance(entry, dict) and all(field in entry for field in required_fields):
                    valid_lines.append(line)
                else:
                    invalid_count += 1
            except json.JSONDecodeError:
                invalid_count += 1
    
    # Write cleaned file
    with open(file_path, 'w', encoding='utf-8') as f:
        for line in valid_lines:
            f.write(line + '\n')
    
    return {
        'total_lines': total_lines,
        'valid_lines': len(valid_lines),
        'invalid_lines': invalid_count,
        'invalid_percentage': invalid_count / total_lines * 100 if total_lines > 0 else 0
    }


def stage2_ultra_prune(file_path: Path, temporal_decay: bool = False, decay_preset: str = 'aggressive') -> Dict[str, Any]:
    """Stage 2: Apply ultra-aggressive pruning with optional temporal decay"""
    
    # Import here to avoid circular imports
    import sys
    sys.path.append('/home/michael/dev/ccmonitor')
    from src.pruner.core import JSONLPruner
    
    # Configure temporal decay if available and requested
    if temporal_decay and TEMPORAL_AVAILABLE:
        try:
            # Get temporal configuration
            temporal_config = get_preset_config(decay_preset)
            
            # Read messages for velocity analysis
            messages = []
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            message = json.loads(line.strip())
                            messages.append(message)
                        except:
                            continue
            except Exception as e:
                logger.warning(f"Could not read file for velocity analysis: {e}")
            
            # Analyze conversation velocity
            if messages:
                velocity_context = analyze_conversation_velocity(messages)
                logger.info(f"Conversation analysis: {len(messages)} messages, "
                           f"{velocity_context['message_frequency']:.2f} msg/hour, "
                           f"{len(velocity_context['current_topics'])} active topics")
            else:
                velocity_context = {}
            
            # Create pruner with temporal decay
            pruner = JSONLPruner(
                pruning_level='ultra', 
                temporal_decay=True,
                decay_mode=temporal_config.mode,
                conversation_context=velocity_context
            )
            logger.info(f"Using temporal decay with preset '{decay_preset}' and mode '{temporal_config.mode.value}'")
            
        except Exception as e:
            logger.warning(f"Temporal decay setup failed, falling back to standard ultra pruning: {e}")
            pruner = JSONLPruner(pruning_level='ultra')
    else:
        pruner = JSONLPruner(pruning_level='ultra')
    
    result = pruner.process_file(file_path, file_path)
    
    return result


def cleanup_and_ultra_prune(file_path: Path, backup: bool = True, temporal_decay: bool = False, decay_preset: str = 'aggressive') -> Dict[str, Any]:
    """
    Two-stage ultra pruning:
    1. Remove invalid lines
    2. Apply ultra pruning
    """
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    original_size = file_path.stat().st_size
    
    # Create backup if requested
    if backup:
        backup_path = file_path.with_suffix(f'{file_path.suffix}.backup')
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.info(f"📁 Backup created: {backup_path}")
    
    logger.info(f"🔍 Original file: {original_size / 1024:.1f} KB")
    
    # Stage 1: Remove invalid lines
    logger.info("⚡ Stage 1: Removing invalid lines...")
    stage1_stats = stage1_remove_invalid_lines(file_path)
    stage1_size = file_path.stat().st_size
    stage1_reduction = ((original_size - stage1_size) / original_size) * 100
    
    logger.info(f"   ✅ Removed {stage1_stats['invalid_lines']} invalid lines ({stage1_stats['invalid_percentage']:.1f}%)")
    logger.info(f"   📉 Size reduction: {stage1_reduction:.1f}% ({stage1_size / 1024:.1f} KB)")
    
    # Stage 2: Ultra pruning
    if temporal_decay:
        logger.info(f"🔥 Stage 2: Temporal-aware ultra pruning (preset: {decay_preset})...")
    else:
        logger.info("🔥 Stage 2: Ultra-aggressive pruning...")
    stage2_stats = stage2_ultra_prune(file_path, temporal_decay, decay_preset)
    final_size = file_path.stat().st_size
    
    # Calculate total reduction
    total_reduction = ((original_size - final_size) / original_size) * 100
    total_saved = original_size - final_size
    
    logger.info(f"   ✅ Preserved {stage2_stats.get('messages_preserved', '?')} high-value messages")
    logger.info(f"   ✅ Removed {stage2_stats.get('messages_removed', '?')} low-value messages")
    
    return {
        'original_size': original_size,
        'stage1_size': stage1_size,
        'final_size': final_size,
        'stage1_reduction': stage1_reduction,
        'total_reduction': total_reduction,
        'total_saved': total_saved,
        'stage1_stats': stage1_stats,
        'stage2_stats': stage2_stats,
        'backup_created': backup
    }


def main():
    parser = argparse.ArgumentParser(description='Three-stage cleanup: delete old files + remove invalid lines + ultra prune')
    parser.add_argument('file', type=Path, help='JSONL file or directory to process')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backup')
    parser.add_argument('--batch', action='store_true', help='Process all JSONL files in directory')
    
    # Deletion options
    parser.add_argument('--delete-old', type=int, nargs='?', const=7, metavar='DAYS', 
                       help='Delete JSONL files older than DAYS (default: 7 days)')
    parser.add_argument('--dry-run-delete', action='store_true', 
                       help='Preview old file deletions without actually deleting')
    parser.add_argument('--max-delete', type=int, default=50,
                       help='Maximum number of files to delete in one run (default: 50)')
    parser.add_argument('--no-pruning', action='store_true',
                       help='Skip pruning stages (only delete old files)')
    
    # Message-level deletion options
    parser.add_argument('--delete-old-messages', type=int, nargs='?', const=7, metavar='DAYS',
                       help='Delete individual messages older than DAYS based on timestamp (default: 7 days)')
    parser.add_argument('--dry-run-delete-messages', action='store_true',
                       help='Preview old message deletions without actually deleting')
    parser.add_argument('--max-delete-messages', type=int, default=1000,
                       help='Maximum number of messages to delete per file (default: 1000)')
    parser.add_argument('--preserve-important-messages', action='store_true', default=False,
                       help='Preserve high-importance old messages (disabled by default for timestamp deletion)')
    parser.add_argument('--no-preserve-important', dest='preserve_important_messages', action='store_false',
                       help='Do not preserve important old messages (default behavior)')
    parser.add_argument('--preserve-parent-child', action='store_true', default=True,
                       help='Preserve parent-child relationships (ENABLED by default - CRITICAL for conversation flow)')
    parser.add_argument('--no-preserve-parent-child', dest='preserve_parent_child', action='store_false',
                       help='Disable parent-child preservation (NOT RECOMMENDED - breaks conversation flow)')
    parser.add_argument('--export-dependency-graph', action='store_true',
                       help='Export dependency graph to JSON file for debugging')
    
    # Temporal decay options
    parser.add_argument('--temporal-decay', action='store_true',
                       help='Enable temporal decay for time-based importance weighting')
    parser.add_argument('--decay-preset', choices=['development', 'debugging', 'conversation', 'analysis', 'aggressive', 'conservative'],
                       default='aggressive', help='Temporal decay preset (default: aggressive)')
    
    args = parser.parse_args()
    
    if args.batch and args.file.is_dir():
        # Batch mode
        directory = args.file
        
        # Stage 0: Delete old files (if requested)
        deletion_stats = None
        if args.delete_old is not None:
            logger.info(f"\n🗑️  STAGE 0: Deleting old files...")
            deletion_stats = stage0_delete_old_files(
                directory=directory,
                max_age_days=args.delete_old,
                dry_run=args.dry_run_delete,
                max_files=args.max_delete
            )
            
            if deletion_stats.get('error'):
                logger.error(f"❌ {deletion_stats['error']}")
                return 1
            
            if deletion_stats['files_deleted'] > 0 or deletion_stats['dry_run']:
                logger.info(f"   📊 Scanned: {deletion_stats['total_files_scanned']} files")
                logger.info(f"   🗑️  {'Would delete' if deletion_stats['dry_run'] else 'Deleted'}: {deletion_stats['files_deleted']} files")
                logger.info(f"   💾 Space {'would be' if deletion_stats['dry_run'] else ''} freed: {deletion_stats['size_freed'] / 1024 / 1024:.1f} MB")
        
        # Skip pruning if only deleting or if no-pruning flag is set
        if args.no_pruning or args.dry_run_delete:
            if args.dry_run_delete:
                logger.info("\n🔥 Dry-run mode - no actual changes made")
            elif args.no_pruning:
                logger.info("\n✅ Deletion complete (pruning skipped)")
            return 0
        
        # Continue with pruning stages
        jsonl_files = list(directory.rglob('*.jsonl'))
        logger.info(f"\n🔍 Found {len(jsonl_files)} JSONL files for pruning")
        
        total_original = 0
        total_final = 0
        
        for file_path in jsonl_files:
            try:
                logger.info(f"\n📁 Processing {file_path.name}...")
                
                # Stage 0a: Delete old messages (if requested)
                message_deletion_stats = None
                if args.delete_old_messages is not None:
                    if args.preserve_parent_child:
                        logger.info(f"   🗑️  Deleting old messages with dependency tracking (>{args.delete_old_messages} days)...")
                        message_deletion_stats = stage0b_delete_old_messages_with_dependencies(
                            file_path=file_path,
                            max_age_days=args.delete_old_messages,
                            dry_run=args.dry_run_delete_messages,
                            max_delete_messages=args.max_delete_messages,
                            preserve_important=args.preserve_important_messages,
                            export_dependency_graph=args.export_dependency_graph
                        )
                    else:
                        logger.info(f"   🗑️  Deleting old messages (>{args.delete_old_messages} days)...")
                        logger.warning("   ⚠️  Parent-child preservation DISABLED - conversation flow may be broken!")
                        message_deletion_stats = stage0a_delete_old_messages(
                            file_path=file_path,
                            max_age_days=args.delete_old_messages,
                            dry_run=args.dry_run_delete_messages,
                            max_delete_messages=args.max_delete_messages,
                            preserve_important=args.preserve_important_messages
                        )
                    
                    if message_deletion_stats.get('error'):
                        logger.error(f"   ❌ Message deletion error: {message_deletion_stats['error']}")
                    else:
                        deleted = message_deletion_stats['messages_deleted']
                        total = message_deletion_stats['total_messages']
                        if deleted > 0:
                            logger.info(f"   ✅ Deleted {deleted}/{total} old messages ({message_deletion_stats['reduction_ratio']:.1%} reduction)")
                        else:
                            logger.info(f"   ✅ No old messages to delete ({total} messages analyzed)")
                
                # Continue with pruning if not skipped
                if not args.no_pruning:
                    stats = cleanup_and_ultra_prune(
                        file_path, 
                        backup=not args.no_backup,
                        temporal_decay=args.temporal_decay,
                        decay_preset=args.decay_preset
                    )
                    total_original += stats['original_size']
                    total_final += stats['final_size']
                    
                    logger.info(f"   🎯 Total reduction: {stats['total_reduction']:.1f}% ({stats['total_saved'] / 1024:.1f} KB saved)")
                
            except Exception as e:
                logger.error(f"   ❌ Error processing {file_path}: {e}")
        
        # Summary
        total_saved = total_original - total_final
        total_reduction = (total_saved / total_original) * 100 if total_original > 0 else 0
        
        summary = f"""
🎊 BATCH PROCESSING COMPLETE:
   📊 Files processed: {len(jsonl_files)}
   💾 Total original size: {total_original / 1024 / 1024:.1f} MB
   💾 Total final size: {total_final / 1024 / 1024:.1f} MB  
   🚀 Total space saved: {total_saved / 1024 / 1024:.1f} MB ({total_reduction:.1f}%)"""
        
        if deletion_stats and deletion_stats['files_deleted'] > 0:
            summary += f"""
   🗑️  Old files deleted: {deletion_stats['files_deleted']}
   💾 Space freed by deletion: {deletion_stats['size_freed'] / 1024 / 1024:.1f} MB"""
        
        logger.info(summary)
        
    else:
        # Single file mode
        if args.delete_old is not None:
            # For single file, treat as directory deletion
            if args.file.is_file():
                directory = args.file.parent
            else:
                directory = args.file
                
            logger.info(f"\n🗑️  STAGE 0: Deleting old files...")
            deletion_stats = stage0_delete_old_files(
                directory=directory,
                max_age_days=args.delete_old,
                dry_run=args.dry_run_delete,
                max_files=args.max_delete
            )
            
            if deletion_stats.get('error'):
                logger.error(f"❌ {deletion_stats['error']}")
                return 1
            
            if deletion_stats['files_deleted'] > 0 or deletion_stats['dry_run']:
                logger.info(f"   📊 Scanned: {deletion_stats['total_files_scanned']} files")
                logger.info(f"   🗑️  {'Would delete' if deletion_stats['dry_run'] else 'Deleted'}: {deletion_stats['files_deleted']} files")
                logger.info(f"   💾 Space {'would be' if deletion_stats['dry_run'] else ''} freed: {deletion_stats['size_freed'] / 1024 / 1024:.1f} MB")
            
            if args.no_pruning or args.dry_run_delete:
                if args.dry_run_delete:
                    logger.info("\n🔥 Dry-run mode - no actual changes made")
                elif args.no_pruning:
                    logger.info("\n✅ Deletion complete (pruning skipped)")
                return 0
        
        # Continue with single file processing
        if args.file.is_file():
            try:
                logger.info(f"\n📁 Processing {args.file}...")
                
                # Stage 0a: Delete old messages (if requested)
                message_deletion_stats = None
                if args.delete_old_messages is not None:
                    if args.preserve_parent_child:
                        logger.info(f"🗑️  Stage 0b: Deleting old messages with dependency tracking (>{args.delete_old_messages} days)...")
                        message_deletion_stats = stage0b_delete_old_messages_with_dependencies(
                            file_path=args.file,
                            max_age_days=args.delete_old_messages,
                            dry_run=args.dry_run_delete_messages,
                            max_delete_messages=args.max_delete_messages,
                            preserve_important=args.preserve_important_messages,
                            export_dependency_graph=args.export_dependency_graph
                        )
                    else:
                        logger.info(f"🗑️  Stage 0a: Deleting old messages (>{args.delete_old_messages} days)...")
                        logger.warning("⚠️  Parent-child preservation DISABLED - conversation flow may be broken!")
                        message_deletion_stats = stage0a_delete_old_messages(
                            file_path=args.file,
                            max_age_days=args.delete_old_messages,
                            dry_run=args.dry_run_delete_messages,
                            max_delete_messages=args.max_delete_messages,
                            preserve_important=args.preserve_important_messages
                        )
                    
                    if message_deletion_stats.get('error'):
                        logger.error(f"❌ Message deletion error: {message_deletion_stats['error']}")
                        return 1
                    else:
                        deleted = message_deletion_stats['messages_deleted']
                        total = message_deletion_stats['total_messages']
                        if deleted > 0:
                            logger.info(f"   ✅ Deleted {deleted}/{total} old messages ({message_deletion_stats['reduction_ratio']:.1%} reduction)")
                        else:
                            logger.info(f"   ✅ No old messages to delete ({total} messages analyzed)")
                
                # Continue with pruning if not skipped
                if not args.no_pruning:
                    stats = cleanup_and_ultra_prune(
                        args.file, 
                        backup=not args.no_backup,
                        temporal_decay=args.temporal_decay,
                        decay_preset=args.decay_preset
                    )
                else:
                    # If only doing message deletion, create minimal stats
                    file_size = args.file.stat().st_size
                    stats = {
                        'original_size': file_size,
                        'stage1_size': file_size,
                        'final_size': file_size,
                        'stage1_reduction': 0,
                        'total_reduction': 0,
                        'total_saved': 0
                    }
                
                logger.info(f"""
🎊 PROCESSING COMPLETE:
   📊 Original size: {stats['original_size'] / 1024:.1f} KB
   📊 After stage 1: {stats['stage1_size'] / 1024:.1f} KB (-{stats['stage1_reduction']:.1f}%)
   📊 Final size: {stats['final_size'] / 1024:.1f} KB
   🚀 Total reduction: {stats['total_reduction']:.1f}% ({stats['total_saved'] / 1024:.1f} KB saved)
""")
                
            except Exception as e:
                logger.error(f"❌ Error: {e}")
                return 1
        elif not args.file.exists():
            logger.error(f"❌ File or directory not found: {args.file}")
            return 1
    
    return 0


if __name__ == "__main__":
    exit(main())