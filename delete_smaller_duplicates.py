'''
Delete Smaller Image Duplicates

For each duplicate group containing images, keeps the largest version
and deletes smaller ones.
'''

import os
import sys
import argparse
from duplicate_detection_db import DuplicateDetectionDB
from logger import logger
import config


def is_mixed_format_group(files: list) -> bool:
    '''
    @brief Check if duplicate group contains both RAW and JPEG formats
    @param files List of file info dictionaries
    @return True if group has mixed RAW/JPEG formats (false positive), False otherwise
    '''
    has_raw = False
    has_jpeg = False

    for file_info in files:
        ext = os.path.splitext(file_info['file_path'])[1].lower()

        if ext in config.raw_extensions:
            has_raw = True
        elif ext in config.image_extensions:
            has_jpeg = True

    # If group has both RAW and JPEG, it's a false positive (format conversion pair)
    return has_raw and has_jpeg


def is_image_group(files: list) -> bool:
    '''
    @brief Check if all files in group are images (not videos)
    @param files List of file info dictionaries
    @return True if all files are images, False otherwise
    '''
    for file_info in files:
        if file_info['media_type'] != 'image':
            return False
    return True


def has_size_difference(files: list) -> bool:
    '''
    @brief Check if files have different sizes
    @param files List of file info dictionaries
    @return True if at least two files have different sizes
    '''
    if len(files) < 2:
        return False

    sizes = set(f['file_size'] for f in files)
    return len(sizes) > 1


def has_numeric_suffix(file_path: str) -> bool:
    '''
    @brief Check if filename has collision suffix like _1, _2, etc. (not timestamp parts)
    @param file_path Path to file
    @return True if filename has numeric collision suffix before extension
    '''
    import re
    basename = os.path.splitext(os.path.basename(file_path))[0]

    # Match the timestamp pattern first to avoid false positives
    # Format: YYYY-MM-DDTHH_MM_SS
    timestamp_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}_\d{2}_\d{2}'

    # Find the timestamp
    timestamp_match = re.search(timestamp_pattern, basename)
    if not timestamp_match:
        # No timestamp found, use simple suffix detection
        return bool(re.search(r'_\d+$', basename))

    # Get the part after the timestamp
    after_timestamp = basename[timestamp_match.end():]

    # Check if it ends with _digits (collision suffix)
    # Valid formats after timestamp: "", "_Camera", "_Camera_1", "_1", "_1_2"
    # Collision suffix pattern: _\d+ at the very end
    return bool(re.search(r'_\d+$', after_timestamp))


def get_file_timestamp(file_info: dict) -> float:
    '''
    @brief Get modification timestamp from file info
    @param file_info File info dictionary
    @return Modification timestamp as float
    '''
    return file_info.get('modification_time', 0)


def process_duplicate_group(group_files: list, dry_run: bool = True) -> dict:
    '''
    @brief Process a duplicate group, keeping best version and deleting others
    @param group_files List of file info dictionaries in the duplicate group
    @param dry_run If True, only report what would be deleted without deleting
    @return Dictionary with stats: kept_file, deleted_files, space_freed, reason, or None if skipped
    '''
    # Skip RAW+JPEG pairs
    if is_mixed_format_group(group_files):
        return None

    # Only process image groups
    if not is_image_group(group_files):
        return None

    # Determine strategy based on file sizes
    if has_size_difference(group_files):
        # Strategy 1: Different sizes - keep largest
        files_sorted = sorted(group_files, key=lambda f: int(f['file_size']), reverse=True)
        keep_file = files_sorted[0]
        delete_files = files_sorted[1:]
        reason = "largest size"

        # Validate that we're actually keeping the largest
        for f in delete_files:
            if f['file_size'] > keep_file['file_size']:
                logger.error(f"BUG: Trying to delete larger file! Keep: {keep_file['file_size']}, Delete: {f['file_size']}")
                return None  # Skip this group if something is wrong
    else:
        # Strategy 2: Same size - prefer files without suffix, or keep oldest
        files_with_suffix = [f for f in group_files if has_numeric_suffix(f['file_path'])]
        files_without_suffix = [f for f in group_files if not has_numeric_suffix(f['file_path'])]

        if files_without_suffix and files_with_suffix:
            # Delete files with suffixes, keep those without
            # Among files without suffix, keep the oldest
            files_without_suffix_sorted = sorted(files_without_suffix, key=get_file_timestamp)
            keep_file = files_without_suffix_sorted[0]  # Oldest without suffix
            delete_files = files_with_suffix + files_without_suffix_sorted[1:]
            reason = "no suffix + oldest"
        else:
            # All have suffixes or none have suffixes - keep oldest
            files_sorted = sorted(group_files, key=get_file_timestamp)
            keep_file = files_sorted[0]  # Oldest
            delete_files = files_sorted[1:]
            reason = "oldest timestamp"

    result = {
        'kept_file': keep_file['file_path'],
        'kept_size': keep_file['file_size'],
        'kept_reason': reason,
        'deleted_files': [],
        'space_freed': 0
    }

    for file_info in delete_files:
        file_path = file_info['file_path']
        file_size = file_info['file_size']

        if not os.path.exists(file_path):
            logger.warning(f"File no longer exists, skipping: {file_path}")
            continue

        if dry_run:
            print(f"  [DRY RUN] Would delete: {file_path}")
            print(f"            Size: {format_size(file_size)}")
            result['deleted_files'].append(file_path)
            result['space_freed'] += file_size
        else:
            try:
                os.remove(file_path)
                logger.info(f"DELETED smaller duplicate: {file_path}")
                print(f"  Deleted: {file_path}")
                print(f"           Size: {format_size(file_size)}")
                result['deleted_files'].append(file_path)
                result['space_freed'] += file_size
            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {e}")
                print(f"  ERROR: Failed to delete {file_path}: {e}")

    return result


def format_size(size_bytes: int) -> str:
    '''
    @brief Format file size in human-readable format
    @param size_bytes Size in bytes
    @return Formatted string (e.g., "15.3 MB")
    '''
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def main():
    '''
    @brief Main entry point for smaller duplicate deletion
    '''
    parser = argparse.ArgumentParser(
        description='Delete image duplicates using intelligent strategy: keep largest size, remove files with numeric suffixes, or keep oldest timestamp'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually delete files (default is dry-run mode)'
    )
    parser.add_argument(
        '--db',
        default='media_hashes.db',
        help='Path to database file (default: media_hashes.db)'
    )

    args = parser.parse_args()

    # Check if database exists
    if not os.path.exists(args.db):
        print(f"Error: Database file not found: {args.db}")
        print("Run 'python calculate_hashes.py' first to create the database.")
        sys.exit(1)

    # Initialize database
    db = DuplicateDetectionDB(args.db)

    print("=" * 80)
    print("DELETE IMAGE DUPLICATES")
    print("=" * 80)
    print("Strategy:")
    print("  - Different sizes: Keep largest")
    print("  - Same size with suffixes: Delete files with _1, _2, etc.")
    print("  - Same size without suffixes: Keep oldest timestamp")
    print("=" * 80)

    if args.execute:
        print("\n⚠️  EXECUTE MODE - Files will be permanently deleted!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            db.close()
            return
    else:
        print("\n🔍 DRY RUN MODE - No files will be deleted")
        print("   Use --execute flag to actually delete files")

    print("\nFetching duplicate groups from database...")
    duplicates = db.get_duplicates()

    print(f"Found {len(duplicates)} total duplicate groups\n")

    # Process each duplicate group
    groups_processed = 0
    total_files_to_delete = 0
    total_space_to_free = 0

    print("Processing duplicate groups...")
    print("=" * 80)

    for idx, (phash, files) in enumerate(duplicates, 1):
        result = process_duplicate_group(files, dry_run=not args.execute)

        if result is not None:
            groups_processed += 1
            total_files_to_delete += len(result['deleted_files'])
            total_space_to_free += result['space_freed']

            print(f"\nDuplicate Group #{idx}")
            print(f"  Keeping ({result['kept_reason']}): {result['kept_file']}")
            print(f"  Size: {format_size(result['kept_size'])}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total duplicate groups examined: {len(duplicates)}")
    print(f"Groups processed: {groups_processed}")
    print(f"Image files {'deleted' if args.execute else 'to delete'}: {total_files_to_delete}")
    print(f"Space {'freed' if args.execute else 'to free'}: {format_size(total_space_to_free)}")

    if not args.execute and total_files_to_delete > 0:
        print("\n💡 Run with --execute flag to actually delete these files:")
        print("   python delete_smaller_duplicates.py --execute")

    if args.execute and total_files_to_delete > 0:
        print("\n✅ Deletion complete. Run cleanup to update database:")
        print("   python calculate_hashes.py --cleanup")

    print("=" * 80)

    db.close()


if __name__ == '__main__':
    main()
