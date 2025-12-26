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
- `get_exif_date_and_device()`: EXIF extraction with format-specific handlers
- `create_directory_structure()`: Creates year/month directory hierarchy
- `rename_image()`: Generates standardized filename using ISO 8601-like format
- `extract_date_from_filename()`: Regex-based date extraction supporting multiple filename patterns (standard format, VLC screenshots, IMG_YYYYMMDD format)
- `copy_file_with_new_exif()`: Writes extracted dates back to EXIF metadata using piexif
- `handle_file_with_exif()` / `handle_file_without_exif()`: Routing logic
- `copy_srt_file()`: Handles subtitle files for videos (.lrf format)
- `process_file_non_media()`: Handles files that don't match any media extension

**`logger.py`**:
- Multi-level logging to separate files in `./logs/` directory (info.log, warning.log, error.log)
- Used throughout imagetools.py to track file operations

**`write_date_to_exif.py`**:
- Standalone utility for manually writing dates to EXIF data
- Interactive script that prompts for dates per image

**`exif_dashboard_streamlit.py`**:
- Web UI for batch EXIF date updates
- Displays images and allows setting date/time via sidebar controls

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

### Collision Handling
- Files with duplicate names get numeric suffixes (_1, _2, etc.)
- Implemented in both `copy_file_with_new_exif()` and `process_file_non_media()`

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
