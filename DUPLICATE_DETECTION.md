# Duplicate Detection Feature

This module provides perceptual hash-based duplicate detection for your organized media library.

## Overview

The duplicate detection system uses **perceptual hashing** to identify visually identical images and videos, regardless of:
- Different EXIF metadata
- Different file names
- Minor compression differences
- Different file sizes (for videos at different resolutions)

## Key Features

- **Fast parallel processing** using all CPU cores
- **Incremental updates** - only processes new/modified files on subsequent runs
- **SQLite database** - persistent storage of hash values
- **Smart duplicate detection** - finds exact visual matches
- **Detailed reports** - export to CSV, shows wasted space
- **Video support** - extracts keyframes for comparison

## Installation

Install the required dependencies:

```bash
pip install imagehash tqdm
```

### System Requirements

For video processing, you need `ffmpeg` and `ffprobe` installed:

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Fedora
sudo dnf install ffmpeg
```

## Usage

### 1. Initial Hash Calculation

Calculate perceptual hashes for all media files in your library:

```bash
python calculate_hashes.py
```

**First run timing:** ~10-20 minutes for 30,000 files on a 12-core system
**Subsequent runs:** Only processes new/modified files (~seconds)

The script will:
- Scan destination directories from `config.toml`
- Calculate perceptual hashes using all CPU cores
- Store results in `media_hashes.db`
- Show progress bars and statistics

### 2. Find Duplicates

Query the database to find duplicate files:

```bash
# Basic usage - show duplicate groups
python find_duplicates.py

# Show full file paths
python find_duplicates.py -v

# Export to CSV
python find_duplicates.py -o duplicates.csv
```

The report will show:
- Duplicate groups (files with identical visual content)
- File sizes, resolutions, and durations
- Total wasted space
- Suggestions for which files to keep

### 3. Database Maintenance

The database tracks files using their paths and modification times. Here are the maintenance options:

#### Cleanup Deleted Files

Remove database entries for files that no longer exist on disk:

```bash
python calculate_hashes.py --cleanup
```

**When to use:**
- After deleting duplicate files
- After reorganizing your media library
- Periodically to remove stale entries

**What it does:**
- Checks each database entry against the file system
- Removes entries where the file no longer exists
- Shows how many entries were removed
- Processes new/modified files afterward (unless using `--cleanup` only)

#### Rebuild Database

Clear the entire database and recalculate all hashes from scratch:

```bash
python calculate_hashes.py --rebuild
```

**When to use:**
- After moving large numbers of files within your library
- If you suspect the database is out of sync
- When you want a fresh start

**What it does:**
- Clears all database entries
- Processes every media file in your library
- Takes the same time as the initial run (~10-20 minutes)

#### Combine Cleanup with Normal Processing

You can run cleanup as part of your regular update:

```bash
python calculate_hashes.py --cleanup
```

This will:
1. Remove stale entries for deleted files
2. Scan for new/modified files
3. Process them and update the database

### 4. Integration with Media Structurer

The duplicate detection is designed to integrate with the main media structurer workflow:

**Future integration:** When a file is processed by `main.py`, it will automatically calculate and store its perceptual hash in the database. This ensures the database stays up-to-date without manual intervention.

## Database Schema

The SQLite database (`media_hashes.db`) stores:

| Column | Type | Description |
|--------|------|-------------|
| file_path | TEXT | Absolute path to file (PRIMARY KEY) |
| perceptual_hash | TEXT | 256-bit perceptual hash (16x16) |
| file_size | INTEGER | File size in bytes |
| modification_time | REAL | File modification timestamp |
| media_type | TEXT | 'image' or 'video' |
| width | INTEGER | Width in pixels |
| height | INTEGER | Height in pixels |
| duration | REAL | Video duration in seconds (NULL for images) |
| created_at | TIMESTAMP | Database entry creation time |

**Indexed on:** `perceptual_hash` for fast duplicate lookups

## How It Works

### Image Processing
1. Opens image with PIL
2. Calculates 16x16 perceptual hash (256-bit for accuracy)
3. Hash is invariant to minor edits, compression, EXIF changes
4. Stores hash + metadata in database

### Video Processing
1. Uses `ffprobe` to get dimensions and duration
2. Extracts a single keyframe at 10% into the video using `ffmpeg`
3. Calculates perceptual hash of the extracted frame
4. Cleans up temporary files
5. Stores hash + metadata in database

### Incremental Updates
- Before processing a file, checks if it exists in DB with same modification time
- Skips files that haven't changed
- Only processes new files or files modified since last scan

### Handling File System Changes

**Modified Files:**
- Automatically detected by comparing file modification time
- Hash is recalculated and database entry is updated
- Works for edits in image processing tools, video re-encoding, etc.

**Deleted Files:**
- Database entries are NOT automatically removed
- Use `--cleanup` flag to remove stale entries
- Prevents accidental data loss if files are temporarily unmounted

**Moved Files:**
- Moving a file within your library creates a NEW database entry at the new path
- Old path entry becomes stale (orphaned)
- Use `--cleanup` to remove old entries after moving files
- Alternative: Use `--rebuild` if you've reorganized large portions of your library

**Example workflow after reorganization:**
```bash
# After moving/deleting files
python calculate_hashes.py --cleanup

# Or for major reorganization
python calculate_hashes.py --rebuild
```

## Example Output

```
Database stats:
  Total files: 29,280
  Images: 27,596
  Videos: 1,684
  Duplicate files: 342

Duplicate Group #1 (3 files)
Wasted space in this group: 18.4 MB

  [1] 2019-08-21T17_40_44_Canon_EOS_5D.jpg
      Size: 8.2 MB | Resolution: 5472x3648 | Type: image

  [2] 2019-08-21T17_40_44_Canon_EOS_5D_1.jpg
      Size: 6.1 MB | Resolution: 3000x2000 | Type: image

  [3] 2019-08-21T17_40_44.jpg
      Size: 4.1 MB | Resolution: 1920x1280 | Type: image
```

## Performance

**Test system:** Intel i7-1260P (12 cores), 62GB RAM

| Operation | Time |
|-----------|------|
| Process 27,596 images | ~1-2 minutes |
| Process 1,684 videos | ~5-15 minutes |
| Find duplicates in DB | <1 second |

**Storage:** The database file is typically <10MB for 30,000 files.

## Notes

- The database file (`media_hashes.db`) is excluded from git via `.gitignore`
- Videos are compared using keyframes, not entire video streams
- Perceptual hashing is robust but not perfect - always review results before deleting files
- Larger hash sizes (16x16) provide better accuracy at the cost of slightly slower processing

## Troubleshooting

**"ffmpeg not found" error:**
Install ffmpeg system-wide (see Installation section)

**Slow processing:**
- Normal on first run with large libraries
- Subsequent runs are much faster (incremental)
- Video processing is slower than images

**False positives:**
- Very rare with 16x16 hash size
- Check file contents before deleting duplicates

**Database out of sync:**
Delete `media_hashes.db` and run `calculate_hashes.py` again
