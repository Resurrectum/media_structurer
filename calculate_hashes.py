'''
Calculate Perceptual Hashes for Media Library

Main script to scan media directories, calculate perceptual hashes using
parallel processing, and store results in SQLite database.
'''

import os
import sys
import argparse
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from duplicate_detection_db import DuplicateDetectionDB
from hash_calculator import process_media_file
from logger import logger
import config


def get_media_type(file_path: str) -> str:
    '''
    @brief Determine media type based on file extension
    @param file_path Path to file
    @return 'image', 'video', or 'unknown'
    '''
    ext = os.path.splitext(file_path)[1].lower()

    if ext in config.image_extensions or ext in config.raw_extensions:
        return 'image'
    elif ext in config.video_extensions:
        return 'video'
    else:
        return 'unknown'


def scan_media_directories(directories: list, db: DuplicateDetectionDB) -> list:
    '''
    @brief Scan directories for media files that need processing
    @param directories List of directory paths to scan
    @param db Database instance to check for existing entries
    @return List of tuples (file_path, media_type) to process
    '''
    files_to_process = []

    logger.info(f"Scanning directories: {directories}")

    for directory in directories:
        if not os.path.exists(directory):
            logger.error(f"Directory does not exist: {directory}")
            continue

        for root, dirs, files in os.walk(directory):
            for filename in files:
                file_path = os.path.join(root, filename)
                media_type = get_media_type(file_path)

                if media_type == 'unknown':
                    continue

                # Check if file needs processing
                try:
                    modification_time = os.path.getmtime(file_path)

                    # Skip if already in database with same modification time
                    if db.file_exists_in_db(file_path, modification_time):
                        continue

                    files_to_process.append((file_path, media_type))

                except Exception as e:
                    logger.error(f"Error checking file {file_path}: {e}")

    return files_to_process


def main():
    '''
    @brief Main entry point for hash calculation
    '''
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Calculate perceptual hashes for media library with parallel processing'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Remove database entries for files that no longer exist on disk'
    )
    parser.add_argument(
        '--rebuild',
        action='store_true',
        help='Clear database and recalculate all hashes from scratch'
    )
    parser.add_argument(
        '--db',
        default='media_hashes.db',
        help='Path to database file (default: media_hashes.db)'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Media Library Perceptual Hash Calculator")
    print("=" * 60)

    # Initialize database
    db = DuplicateDetectionDB(args.db)
    logger.info("Database initialized")

    # Handle rebuild flag
    if args.rebuild:
        print("\n[REBUILD MODE] Clearing database...")
        db.rebuild_database()
        logger.info("Database cleared for rebuild")
        print("Database cleared. All files will be reprocessed.")

    # Get current stats
    stats = db.get_stats()
    print(f"\nCurrent database stats:")
    print(f"  Total files in DB: {stats['total_files']}")
    print(f"  Images: {stats['images']}")
    print(f"  Videos: {stats['videos']}")
    print(f"  Duplicate files: {stats['duplicate_files']}")

    # Handle cleanup flag
    if args.cleanup:
        print("\n[CLEANUP MODE] Checking for deleted files...")
        removed_count = db.cleanup_deleted_files()
        print(f"Removed {removed_count} stale entries from database")
        logger.info(f"Cleanup complete. Removed {removed_count} stale entries")

        if removed_count > 0:
            # Show updated stats after cleanup
            stats = db.get_stats()
            print(f"\nUpdated database stats:")
            print(f"  Total files in DB: {stats['total_files']}")
            print(f"  Images: {stats['images']}")
            print(f"  Videos: {stats['videos']}")
            print(f"  Duplicate files: {stats['duplicate_files']}")

    # Scan directories for files to process
    directories_to_scan = [
        config.dest_dir_pictures,
        config.dest_dir_pictures_raw,
        config.dest_dir_videos
    ]

    print(f"\nScanning directories for new/modified files...")
    files_to_process = scan_media_directories(directories_to_scan, db)

    if not files_to_process:
        print("\nNo new files to process. Database is up to date!")
        db.close()
        return

    print(f"\nFound {len(files_to_process)} files to process")
    print(f"  Images: {sum(1 for f in files_to_process if f[1] == 'image')}")
    print(f"  Videos: {sum(1 for f in files_to_process if f[1] == 'video')}")

    # Calculate hashes using parallel processing
    num_cores = cpu_count()
    print(f"\nProcessing with {num_cores} CPU cores...")

    successful = 0
    failed = 0

    with Pool(processes=num_cores) as pool:
        # Use tqdm for progress bar
        results = list(tqdm(
            pool.imap_unordered(process_media_file, files_to_process),
            total=len(files_to_process),
            desc="Calculating hashes",
            unit="files"
        ))

        # Store results in database
        print("\nStoring results in database...")
        for result in tqdm(results, desc="Saving to DB", unit="files"):
            if result is not None:
                try:
                    db.insert_hash(
                        file_path=result['file_path'],
                        perceptual_hash=result['perceptual_hash'],
                        file_size=result['file_size'],
                        modification_time=result['modification_time'],
                        media_type=result['media_type'],
                        width=result['width'],
                        height=result['height'],
                        duration=result['duration']
                    )
                    successful += 1
                except Exception as e:
                    logger.error(f"Failed to store result: {e}")
                    failed += 1
            else:
                failed += 1

    # Final stats
    print("\n" + "=" * 60)
    print("Processing complete!")
    print(f"  Successfully processed: {successful} files")
    print(f"  Failed: {failed} files")

    final_stats = db.get_stats()
    print(f"\nFinal database stats:")
    print(f"  Total files in DB: {final_stats['total_files']}")
    print(f"  Images: {final_stats['images']}")
    print(f"  Videos: {final_stats['videos']}")
    print(f"  Unique hashes: {final_stats['unique_hashes']}")
    print(f"  Duplicate files: {final_stats['duplicate_files']}")

    if final_stats['duplicate_files'] > 0:
        print(f"\nRun 'python find_duplicates.py' to see duplicate files")

    print("=" * 60)

    logger.info(f"Hash calculation complete. Processed: {successful}, Failed: {failed}")
    db.close()


if __name__ == '__main__':
    main()
