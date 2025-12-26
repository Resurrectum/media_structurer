'''
Find and Report Duplicate Media Files

Queries the hash database to find duplicate files and generates reports.
'''

import os
import sys
import csv
import argparse
from duplicate_detection_db import DuplicateDetectionDB
from logger import logger
import config


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


def format_resolution(width: int, height: int) -> str:
    '''
    @brief Format resolution string
    @param width Width in pixels
    @param height Height in pixels
    @return Formatted string (e.g., "1920x1080")
    '''
    if width and height:
        return f"{width}x{height}"
    return "N/A"


def format_duration(duration: float) -> str:
    '''
    @brief Format video duration in human-readable format
    @param duration Duration in seconds
    @return Formatted string (e.g., "1h 23m 45s")
    '''
    if duration is None:
        return "N/A"

    hours = int(duration // 3600)
    minutes = int((duration % 3600) // 60)
    seconds = int(duration % 60)

    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


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


def display_duplicates(duplicates: list, verbose: bool = False):
    '''
    @brief Display duplicate groups in terminal
    @param duplicates List of duplicate groups from database
    @param verbose Show full file paths if True
    '''
    # Filter out RAW+JPEG pairs (false positives)
    filtered_duplicates = [
        (phash, files) for phash, files in duplicates
        if not is_mixed_format_group(files)
    ]

    print("=" * 80)
    print("DUPLICATE FILES REPORT")
    print("=" * 80)
    print(f"(Filtered out {len(duplicates) - len(filtered_duplicates)} RAW+JPEG pairs)")
    print("=" * 80)

    total_duplicate_files = 0
    total_wasted_space = 0

    for idx, (phash, files) in enumerate(filtered_duplicates, 1):
        print(f"\n{'=' * 80}")
        print(f"Duplicate Group #{idx} ({len(files)} files)")
        print(f"{'=' * 80}")

        # Calculate wasted space (all files except the largest one)
        largest_size = files[0]['file_size']  # Already sorted by size DESC
        wasted_space = sum(f['file_size'] for f in files[1:])
        total_wasted_space += wasted_space

        print(f"Wasted space in this group: {format_size(wasted_space)}")
        print()

        for file_idx, file_info in enumerate(files, 1):
            total_duplicate_files += 1

            path = file_info['file_path']
            if not verbose:
                path = os.path.basename(path)

            size = format_size(file_info['file_size'])
            resolution = format_resolution(file_info['width'], file_info['height'])
            media_type = file_info['media_type']

            print(f"  [{file_idx}] {path}")
            print(f"      Size: {size} | Resolution: {resolution} | Type: {media_type}")

            if file_info['duration'] is not None:
                duration = format_duration(file_info['duration'])
                print(f"      Duration: {duration}")

            if verbose:
                print(f"      Full path: {path}")

            print()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total duplicate groups: {len(filtered_duplicates)}")
    print(f"Total duplicate files: {total_duplicate_files}")
    print(f"Total wasted space: {format_size(total_wasted_space)}")
    print(f"  (If you delete all but the largest file in each group)")
    print("=" * 80)


def export_to_csv(duplicates: list, output_file: str):
    '''
    @brief Export duplicates to CSV file
    @param duplicates List of duplicate groups from database
    @param output_file Path to output CSV file
    '''
    # Filter out RAW+JPEG pairs (false positives)
    filtered_duplicates = [
        (phash, files) for phash, files in duplicates
        if not is_mixed_format_group(files)
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'group_id', 'file_path', 'file_size', 'size_formatted',
            'media_type', 'resolution', 'duration', 'perceptual_hash'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for group_id, (phash, files) in enumerate(filtered_duplicates, 1):
            for file_info in files:
                writer.writerow({
                    'group_id': group_id,
                    'file_path': file_info['file_path'],
                    'file_size': file_info['file_size'],
                    'size_formatted': format_size(file_info['file_size']),
                    'media_type': file_info['media_type'],
                    'resolution': format_resolution(file_info['width'], file_info['height']),
                    'duration': format_duration(file_info['duration']),
                    'perceptual_hash': phash
                })

    print(f"\nDuplicates exported to: {output_file}")
    print(f"(Filtered out {len(duplicates) - len(filtered_duplicates)} RAW+JPEG pairs)")
    logger.info(f"Duplicates exported to CSV: {output_file} (filtered {len(duplicates) - len(filtered_duplicates)} RAW+JPEG pairs)")


def main():
    '''
    @brief Main entry point for duplicate finder
    '''
    parser = argparse.ArgumentParser(
        description='Find and report duplicate media files from hash database'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show full file paths'
    )
    parser.add_argument(
        '-o', '--output',
        metavar='FILE',
        help='Export duplicates to CSV file'
    )
    parser.add_argument(
        '--db',
        default='media_hashes.db',
        help='Path to database file (default: media_hashes.db)'
    )

    args = parser.parse_args()

    # Initialize database
    if not os.path.exists(args.db):
        print(f"Error: Database file not found: {args.db}")
        print("Run 'python calculate_hashes.py' first to create the database.")
        sys.exit(1)

    db = DuplicateDetectionDB(args.db)

    # Get database stats
    stats = db.get_stats()
    print(f"\nDatabase stats:")
    print(f"  Total files: {stats['total_files']}")
    print(f"  Images: {stats['images']}")
    print(f"  Videos: {stats['videos']}")
    print(f"  Duplicate files: {stats['duplicate_files']}")

    if stats['duplicate_files'] == 0:
        print("\nNo duplicates found! Your library is clean.")
        db.close()
        return

    # Find duplicates
    print("\nSearching for duplicates...")
    duplicates = db.get_duplicates()

    # Display results
    display_duplicates(duplicates, verbose=args.verbose)

    # Export to CSV if requested
    if args.output:
        export_to_csv(duplicates, args.output)

    db.close()


if __name__ == '__main__':
    main()
