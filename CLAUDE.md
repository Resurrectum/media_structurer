# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Media Structurer is a Python tool that organizes photos, RAW images, and videos into a structured directory hierarchy based on EXIF metadata. It automatically renames files using timestamps and camera models, handles files without EXIF data, and can extract dates from filenames.

## Coding Principles and Standards

When adding or modifying code in this repository, strictly adhere to these principles:

### Core Principles

**Separation of Concerns**
- Each module and function should have a single, well-defined responsibility
- Keep business logic separate from I/O operations, configuration, and presentation
- Example: EXIF extraction, file operations, and logging are handled by separate modules

**DRY (Don't Repeat Yourself)**
- Extract common patterns into reusable functions
- If logic appears in multiple places, refactor into a shared utility
- Avoid copy-paste programming

**KISS (Keep It Simple, Stupid)**
- Prefer simple, straightforward solutions over clever or complex ones
- Code should be easy to read and understand
- Avoid unnecessary abstractions or premature optimization

**YAGNI (You Aren't Gonna Need It)**
- Only implement features that are actually needed now
- Don't add functionality for hypothetical future requirements
- Keep the codebase minimal and focused

### Code Quality Standards

**Documentation**
- All functions must have docstrings following the existing format:
  ```python
  '''
  @brief Brief description of what the function does
  @param param_name Description of parameter
  @return Description of return value
  '''
  ```
- Complex logic should include inline comments explaining the "why", not the "what"
- Update CLAUDE.md when adding architectural changes

**Clean Design Patterns**
- Optimize for readability and reusability
- Use descriptive variable and function names
- Keep functions small and focused (ideally under 30 lines)
- Minimize function parameters (ideally 3 or fewer)
- Return early to reduce nesting depth

**Code Reusability**
- Design functions to be generic and reusable where possible
- Use function parameters instead of hardcoding values
- Consider whether logic could be useful in other contexts before implementing

## Running the Application

### Local Development

**Main organizer script:**
```bash
python main.py
```

**EXIF dashboard (Streamlit):**
```bash
streamlit run exif_dashboard_streamlit.py
```

**Manual EXIF writing utility:**
```bash
python write_date_to_exif.py
```

### Docker Deployment

**Deploy to remote server (e.g., tricc):**
```bash
./deploy.sh                          # Syncs code via rsync and builds image on server
```

**Run on server:**
```bash
ssh rafael@tricc
cd ~/repos/media_structurer
docker-compose up                    # Run once
docker-compose up -d                 # Run in background
```

**Update deployment:**
```bash
./deploy.sh                          # Re-sync and rebuild
./deploy-and-restart.sh              # Re-sync, rebuild, and auto-restart container
```

See `DOCKER_DEPLOYMENT.md` for complete deployment guide including:
- Configuration of volume paths for Syncthing integration
- Automation options (cron, systemd, folder watch)
- Troubleshooting

**Duplicate detection (calculate hashes):**
```bash
python calculate_hashes.py           # Initial run or incremental update
python calculate_hashes.py --cleanup # Remove stale entries for deleted files
python calculate_hashes.py --rebuild # Clear DB and recalculate all hashes
```

**Duplicate detection (find duplicates):**
```bash
python find_duplicates.py           # Display duplicate groups
python find_duplicates.py -v        # Show full file paths
python find_duplicates.py -o out.csv # Export to CSV
```

**Duplicate cleanup (delete duplicates):**
```bash
python delete_smaller_duplicates.py              # Dry-run mode
python delete_smaller_duplicates.py --execute    # Actually delete files
```

See `DUPLICATE_DETECTION.md` for complete documentation.

## Configuration

All configuration is managed through `config.toml`:

- `careful`: When `true`, files are copied instead of moved (safe mode)
- `source_dirs`: Array of source directories to scan for media files
- `dest_dir_pictures`, `dest_dir_pictures_raw`, `dest_dir_videos`: Destination directories for organized media
- `dest_non_media`: Directory for non-media files
- `no_exif_directories_all`: Child directory name for files without EXIF data (e.g., "no_exif")
- `FileExtensions`: Defines which file extensions are treated as images, RAW files, or videos

The `config.py` module loads and processes this TOML configuration, creating derived paths like `no_exif_dir_pictures`.

## Architecture

### Core Processing Flow

1. **Entry point** (`main.py`): Walks through source directories, classifies files by extension, and dispatches to appropriate handlers
2. **File classification**: Files are categorized as images, RAW files, videos, or non-media based on extensions
3. **EXIF extraction** (`imagetools.get_exif_date_and_device()`):
   - For images: Uses PIL to read EXIF tags 36867 (DateTimeOriginal) and 272 (Model)
   - For RAW files: Uses exifread library
   - For videos: Uses pymediainfo to extract encoded_date or recorded_date
4. **File routing**:
   - **With EXIF**: Creates `YYYY/YYYY-MM/` directory structure, renames to `YYYY-MM-DDTHH_MM_SS_cameramodel.ext`, then copies/moves
   - **Without EXIF**: Attempts to extract date from filename using regex patterns, writes date to EXIF if found, otherwise places in `no_exif/` subdirectory

### Key Components

**`imagetools.py`** (core logic):
- `calculate_file_hash()`: Computes MD5/SHA256 hash of files in chunks for memory efficiency
- `are_files_identical()`: Compares files using size check and hash comparison
- `resolve_destination_path()`: Centralized collision handling with hash-based duplicate detection
- `get_exif_date_and_device()`: EXIF extraction with format-specific handlers
- `create_directory_structure()`: Creates year/month directory hierarchy
- `rename_image()`: Generates standardized filename using ISO 8601-like format
- `extract_date_from_filename()`: Regex-based date extraction supporting multiple filename patterns (standard format, VLC screenshots, IMG_YYYYMMDD format)
- `copy_file_with_new_exif()`: Writes extracted dates back to EXIF metadata using piexif
- `handle_file_with_exif()` / `handle_file_without_exif()`: Routing logic
- `copy_srt_file()`: Handles subtitle files for videos (.lrf format)
- `process_file_non_media()`: Handles files that don't match any media extension

**`logger.py`**:
- Multi-level logging to separate files in `./logs/` directory:
  - `info.log`: General information about file operations
  - `warning.log`: Warnings and non-critical issues
  - `error.log`: Errors and failures
  - `collision.log`: **Dedicated log for all collision detection events** (duplicates and name collisions)
- Collision logger (`collision_logger`) is separate and logs detailed information about duplicate detection decisions

**`write_date_to_exif.py`**:
- Standalone utility for manually writing dates to EXIF data
- Interactive script that prompts for dates per image

**`exif_dashboard_streamlit.py`**:
- Web UI for batch EXIF date updates
- Displays images and allows setting date/time via sidebar controls

**Duplicate Detection Module** (`duplicate_detection_db.py`, `hash_calculator.py`, `calculate_hashes.py`, `find_duplicates.py`, `delete_smaller_duplicates.py`):
- **`duplicate_detection_db.py`**: SQLite database manager for storing perceptual hashes
  - Schema includes file path, hash, size, dimensions, modification time
  - Indexed on perceptual_hash for fast duplicate lookups
  - Methods for cleanup (removing stale entries) and rebuild (clearing database)
- **`hash_calculator.py`**: Parallel processing for calculating perceptual hashes
  - `calculate_image_phash()`: Uses imagehash library with 16x16 hash size (256-bit)
  - `calculate_video_phash()`: Extracts keyframe at 10% using ffmpeg, then hashes it
  - `process_media_file()`: Worker function for parallel pool processing
- **`calculate_hashes.py`**: Main script for scanning and hashing media library
  - Uses multiprocessing.Pool with all CPU cores
  - Incremental updates (only processes new/modified files)
  - Flags: `--cleanup` (remove stale entries), `--rebuild` (clear and recalculate all)
- **`find_duplicates.py`**: Query and report duplicates from database
  - Groups files by perceptual hash, calculates wasted space
  - Automatically filters out RAW+JPEG pairs (intentional format conversions)
  - Export to CSV, verbose mode for full paths
- **`delete_smaller_duplicates.py`**: Intelligent duplicate cleanup tool
  - Strategy 1: Different sizes → keep largest
  - Strategy 2: Same size with collision suffixes (_1, _2, etc.) → delete suffixed files, keep original
  - Strategy 3: Same size without clear preference → keep oldest timestamp
  - Automatically skips RAW+JPEG pairs and videos (only processes images)
  - Dry-run mode by default, requires `--execute` flag to delete files

**How it differs from collision detection:**
- Collision detection (in `imagetools.py`) uses MD5/SHA256 hashes of entire file content for exact binary matches during the organizing process
- Duplicate detection uses perceptual hashes of visual content to find visually identical files regardless of EXIF differences, compression, or minor edits

## Important Implementation Notes

### EXIF Handling
- Different libraries are required for different formats: PIL for standard images, exifread for RAW, pymediainfo for videos
- EXIF datetime format is `YYYY:MM:DD HH:MM:SS` (colons in date, space separator)
- The system updates three EXIF fields when writing dates: DateTimeOriginal, DateTimeDigitized, and DateTime

### File Operation Modes
- The `config.careful` flag controls copy vs. move behavior throughout the codebase
- All file operations check this flag via `config.careful` to determine shutil.copy2() vs. shutil.move()
- Subtitle files (.srt) are handled automatically for video files

### Filename Date Extraction
The regex patterns in `extract_date_from_filename()` handle:
- Standard format: `YYYY-MM-DD HH:MM:SS` with various delimiters (-, :, _, space, .)
- VLC screenshots: `YYYY-MM-DD-HHhMMmSSs`
- Camera format: `YYYYMMDD_HHMMSS` (e.g., IMG_20190821_174044.jpg)

### Collision Handling (Hash-based Duplicate Detection)

The system uses intelligent collision detection with hash-based duplicate detection to prevent data loss and avoid storing duplicate files:

**Collision Resolution Flow:**
1. When a destination file already exists, `resolve_destination_path()` is invoked
2. File sizes are compared first (quick optimization)
3. If sizes match, MD5 hashes are calculated for both files
4. **If hashes match** → Duplicate detected, file is skipped (logged as INFO)
5. **If hashes differ** → Genuine collision, numeric suffix added (_1, _2, etc.) and logged as WARNING

**Key Benefits:**
- **Idempotent**: Running the script multiple times won't create duplicates
- **Prevents data loss**: Burst mode photos (same camera, same second) are preserved with suffixes
- **Efficient**: Hashes calculated only on collision, not for every file
- **Consistent**: All file types (media with/without EXIF, non-media) use the same logic

**Implementation:**
- `calculate_file_hash()`: Computes MD5 hash in 8KB chunks for memory efficiency
- `are_files_identical()`: Size check followed by hash comparison
- `resolve_destination_path()`: Centralized collision handling used by all file processing functions

**Collision Log Format (`./logs/collision.log`):**

All collision events are logged to a dedicated file for audit purposes:

```
# Duplicate detected (file skipped):
2025-01-29 14:23:45 - INFO - DUPLICATE_SKIPPED | Source: /path/to/source.jpg | Existing: /path/to/dest.jpg | Decision: File skipped (identical hash)

# Name collision (suffix added):
2025-01-29 14:23:46 - WARNING - COLLISION_RESOLVED | Source: /path/to/source.jpg | Original destination: /path/to/dest.jpg | New destination: /path/to/dest_1.jpg | Decision: Added suffix _1 (different hash)
```

This dedicated log allows you to:
- Review all duplicate files that were skipped
- Identify burst photos or similar files that got suffixes
- Audit the collision detection algorithm's decisions
- Verify that no data was lost or incorrectly deduplicated

## Dependencies

Core libraries used:
- `PIL` (Pillow): Standard image EXIF reading
- `exifread`: RAW file EXIF extraction
- `piexif`: EXIF data writing/modification
- `pymediainfo`: Video metadata extraction
- `toml`: Configuration parsing
- `python-dateutil`: Flexible date parsing
- `streamlit`: Dashboard UI (optional)
- `numpy`: Dashboard support (optional)

Duplicate detection libraries:
- `imagehash`: Perceptual hashing for images
- `tqdm`: Progress bars for long-running operations
- `ffmpeg` / `ffprobe`: Video frame extraction and metadata (system dependency, not Python package)

All dependencies are specified in `pyproject.toml` for modern Python package management.

## Deployment

The project includes Docker deployment support for running on servers:

**Files:**
- `Dockerfile`: Container image with all dependencies
- `docker-compose.yml`: Container orchestration with volume mappings
- `config.tricc.toml`: Configuration template for server deployment
- `deploy.sh`: Automated rsync-based deployment script
- `deploy-and-restart.sh`: Deploy and auto-restart container
- `.dockerignore`: Excludes unnecessary files from image

**Use case:** Run Media Structurer on a Syncthing master server to eliminate unnecessary network traffic (files sync once, get organized locally, no sync-back needed).

See `DOCKER_DEPLOYMENT.md` for complete deployment documentation.
