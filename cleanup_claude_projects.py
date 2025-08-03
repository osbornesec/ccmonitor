#!/usr/bin/env python3
"""
Cleanup script for ~/.claude/projects directory
Removes all files except .jsonl files, keeping only the primary conversation files
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def cleanup_claude_projects(dry_run: bool = True, max_deletions: int = 1000) -> Dict[str, Any]:
    """
    Clean up ~/.claude/projects directory by removing all non-primary JSONL files
    
    Args:
        dry_run: If True, only show what would be deleted
        max_deletions: Safety limit on number of files to delete
        
    Returns:
        Dictionary with cleanup statistics
    """
    projects_dir = Path.home() / '.claude' / 'projects'
    
    if not projects_dir.exists():
        return {'error': f'Directory not found: {projects_dir}'}
    
    # Files to delete (everything except primary .jsonl files)
    files_to_delete = []
    total_files = 0
    total_size = 0
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(projects_dir):
        root_path = Path(root)
        
        for file in files:
            file_path = root_path / file
            total_files += 1
            file_size = file_path.stat().st_size
            
            # Keep only primary .jsonl files (not backup files) that have content
            if file_path.suffix == '.jsonl' and not any(backup_marker in file_path.name for backup_marker in ['.backup', 'backup-messages']):
                # Check if the file is empty (zero bytes)
                if file_size == 0:
                    # Empty JSONL file - delete it
                    files_to_delete.append({
                        'path': file_path,
                        'size': file_size,
                        'type': 'Empty JSONL Files'
                    })
                    total_size += file_size
                else:
                    # This is a primary JSONL file with content - keep it
                    logger.debug(f"   ✅ Keeping: {file_path.relative_to(projects_dir)}")
                    continue
            else:
                # This file should be deleted
                files_to_delete.append({
                    'path': file_path,
                    'size': file_size,
                    'type': _get_file_type(file_path)
                })
                total_size += file_size
    
    # Apply safety limit
    if len(files_to_delete) > max_deletions:
        logger.warning(f"⚠️  Found {len(files_to_delete)} files to delete, limiting to {max_deletions} for safety")
        files_to_delete = files_to_delete[:max_deletions]
    
    # Group files by type for better reporting
    files_by_type = {}
    for file_info in files_to_delete:
        file_type = file_info['type']
        if file_type not in files_by_type:
            files_by_type[file_type] = []
        files_by_type[file_type].append(file_info)
    
    deleted_count = 0
    deleted_size = 0
    errors = []
    
    if files_to_delete:
        logger.info(f"🧹 Found {len(files_to_delete)} files to clean up:")
        
        # Show summary by file type
        for file_type, type_files in files_by_type.items():
            type_size = sum(f['size'] for f in type_files)
            logger.info(f"   📁 {file_type}: {len(type_files)} files ({type_size / 1024 / 1024:.1f} MB)")
        
        if dry_run:
            logger.info(f"\\n{'[DRY RUN]' if dry_run else ''} Would delete {len(files_to_delete)} files...")
        else:
            logger.info(f"\\n🗑️  Deleting {len(files_to_delete)} files...")
        
        for file_info in files_to_delete:
            file_path = file_info['path']
            size = file_info['size']
            
            if dry_run:
                logger.info(f"   [DRY RUN] Would delete: {file_path.relative_to(projects_dir)} ({size/1024:.1f} KB)")
            else:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    deleted_size += size
                    logger.info(f"   🗑️  Deleted: {file_path.relative_to(projects_dir)} ({size/1024:.1f} KB)")
                except Exception as e:
                    errors.append(f"Failed to delete {file_path}: {e}")
                    logger.error(f"   ❌ Failed to delete {file_path.relative_to(projects_dir)}: {e}")
    else:
        logger.info("✅ No files to clean up - directory is already clean")
    
    # Count remaining JSONL files
    remaining_jsonl = len([f for f in Path(projects_dir).rglob('*.jsonl') 
                          if not any(marker in f.name for marker in ['.backup', 'backup-messages'])])
    
    return {
        'total_files_scanned': total_files,
        'files_to_delete': len(files_to_delete),
        'files_deleted': deleted_count,
        'files_by_type': {ftype: len(files) for ftype, files in files_by_type.items()},
        'size_freed': deleted_size,
        'remaining_jsonl_files': remaining_jsonl,
        'errors': errors,
        'dry_run': dry_run,
        'projects_directory': str(projects_dir)
    }

def _get_file_type(file_path: Path) -> str:
    """Classify file type for reporting"""
    name = file_path.name.lower()
    
    if '.backup-messages.' in name:
        return 'Message Backup Files'
    elif '.backup.' in name or name.endswith('.backup'):
        return 'Regular Backup Files'
    elif '.jsonl.' in name and name.count('.') > 1:
        return 'Timestamped Backup Files'
    elif file_path.suffix == '.jsonl':
        return 'JSONL Files (non-primary)'
    else:
        return f'{file_path.suffix.upper()[1:] if file_path.suffix else "No Extension"} Files'

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up ~/.claude/projects directory')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Show what would be deleted without actually deleting (default)')
    parser.add_argument('--delete', action='store_true',
                       help='Actually delete files (overrides --dry-run)')
    parser.add_argument('--max-deletions', type=int, default=1000,
                       help='Maximum number of files to delete (safety limit)')
    parser.add_argument('--force', action='store_true',
                       help='Skip confirmation prompt (use with caution)')
    
    args = parser.parse_args()
    
    # If --delete is specified, turn off dry_run
    dry_run = not args.delete
    
    if dry_run:
        logger.info("🔍 DRY RUN MODE - No files will be deleted")
    else:
        logger.info("⚠️  DELETION MODE - Files will be permanently deleted")
        
        # Ask for confirmation unless --force is used
        if not args.force:
            response = input("Are you sure you want to delete files? Type 'yes' to confirm: ")
            if response.lower() != 'yes':
                logger.info("❌ Operation cancelled")
                return 1
        else:
            logger.info("🚀 Force mode enabled - skipping confirmation")
    
    logger.info(f"🧹 Cleaning ~/.claude/projects directory...")
    logger.info("   📁 Keeping: Primary .jsonl conversation files")
    logger.info("   🗑️  Removing: .backup files, .backup-messages files, timestamped backups\\n")
    
    result = cleanup_claude_projects(dry_run=dry_run, max_deletions=args.max_deletions)
    
    if result.get('error'):
        logger.error(f"❌ {result['error']}")
        return 1
    
    # Summary
    logger.info(f"\\n🎊 CLEANUP SUMMARY:")
    logger.info(f"   📊 Files scanned: {result['total_files_scanned']:,}")
    logger.info(f"   🗑️  Files {'would be deleted' if dry_run else 'deleted'}: {result['files_deleted']:,}")
    logger.info(f"   💾 Space {'would be freed' if dry_run else 'freed'}: {result['size_freed'] / 1024 / 1024:.1f} MB")
    logger.info(f"   📁 Primary JSONL files remaining: {result['remaining_jsonl_files']:,}")
    
    if result.get('files_by_type'):
        logger.info(f"\\n📂 Files by type:")
        for file_type, count in result['files_by_type'].items():
            logger.info(f"   • {file_type}: {count:,} files")
    
    if result['errors']:
        logger.info(f"\\n❌ Errors encountered: {len(result['errors'])}")
        for error in result['errors'][:5]:  # Show first 5 errors
            logger.error(f"   {error}")
    
    if dry_run:
        logger.info(f"\\n💡 To actually delete files, run with --delete flag")
    
    return 0

if __name__ == "__main__":
    exit(main())