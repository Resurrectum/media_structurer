'''Image tools for the image processing script.'''
import os
import re
import string
import shutil
from datetime import datetime
from PIL import Image
import exifread
import piexif
from dateutil.parser import parse
from pymediainfo import MediaInfo
from logger import logger, collision_logger
import config
import hashlib


def calculate_file_hash(file_path, algorithm='md5'):
    '''
    @brief Calculate hash of a file using specified algorithm.
    @param file_path Path to the file to hash
    @param algorithm Hash algorithm to use ('md5' or 'sha256')
    @return Hexadecimal hash string
    '''
    hash_func = hashlib.md5() if algorithm == 'md5' else hashlib.sha256()

    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def are_files_identical(file_path1, file_path2):
    '''
    @brief Check if two files are identical by comparing their hashes.
    @param file_path1 Path to first file
    @param file_path2 Path to second file
    @return True if files are identical, False otherwise
    '''
    # Quick check: compare file sizes first (optimization)
    if os.path.getsize(file_path1) != os.path.getsize(file_path2):
        return False

    # If sizes match, compare hashes
    hash1 = calculate_file_hash(file_path1)
    hash2 = calculate_file_hash(file_path2)

    return hash1 == hash2


def get_exif_date_and_device(file_path):
    '''
    @brief This function gets the date and device model from the EXIF data of an image or video.
    @param file_path The path to the image or video file.
    @return A tuple containing the date and device model from the EXIF data, 
    or None if the EXIF data does not exist or an error occurs.
    '''
    try:
        date = None
        device = None
        if file_path.lower().endswith(tuple(config.raw_extensions)): # for RAW files
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f)
                if 'EXIF DateTimeOriginal' in tags:
                    date_time = str(tags['EXIF DateTimeOriginal'])
                    date = datetime.strptime(date_time, '%Y:%m:%d %H:%M:%S')
                if 'Image Model' in tags:
                    device = str(tags['Image Model'])
        elif file_path.lower().endswith(tuple(config.video_extensions)): # for video files
            try:
                media_info = MediaInfo.parse(file_path)
                for track in media_info.tracks:
                    if track.track_type == 'General':
                        date_string = track.encoded_date or track.recorded_date
                        if date_string:
                            date_string = date_string.replace('UTC ', '') # remove 'UTC ' from the date string if it exists
                        try:
                            date = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            date = parse(date_string)
                        device = None
            except Exception as e:
                logger.error('Failed to get creation date from video file %s due to error: %s', file_path, e)
                date = None
                device = None
        else: # for other image files
            image = Image.open(file_path)
            exif_data = image._getexif()
            if exif_data is not None:
                date_time = exif_data.get(36867)  # DateTimeOriginal tag
                if date_time is not None:
                    # Remove null characters from the datetime string
                    date_time = date_time.replace('\x00', '')
                    date = datetime.strptime(date_time, '%Y:%m:%d %H:%M:%S')
                device = exif_data.get(272)  # Model tag
                if device is not None:
                    device = device.strip().replace(' ', '_')
                    # Remove non-printable characters from the device model
                    device = ''.join(filter(lambda x: x in string.printable, device))
                    # Replace non-alphanumeric characters with underscores
                    device = re.sub(r'\W+', '_', device)
        return date, device
    except Exception as e:
        logger.warning('Failed to get EXIF data from file %s due to error: %s', file_path, e)
    return None, None



def create_directory_structure(base_dir, date):
    '''
    @brief This function creates a directory structure based on a date.
    @param base_dir The base directory where the directory structure will be created.
    @param date The date used to create the directory structure.
    @return The path to the created month directory.
    '''
    year = date.year
    month = date.month
    year_dir = os.path.join(base_dir, str(year))
    month_dir = os.path.join(year_dir, f"{year}-{month:02d}")
    os.makedirs(month_dir, exist_ok=True)
    return month_dir


def rename_image(image_path, date, device):
    '''
    @brief This function renames an image file based on a date and device model.
    @param image_path The path to the image file.
    @param date The date used to rename the image file.
    @param device The device model used to rename the image file.
    @return The new name of the image file.
    '''
    _, ext = os.path.splitext(image_path)
    new_name = date.strftime("%Y-%m-%dT%H_%M_%S")
    # ISO8601 uses colons and underscores, which is not recommended in filenames
    # new_name = date.isoformat() # use ISO 8601 format for date and time
    if device is not None:
        new_name += "_" + device
    new_name += ext
    return new_name



def process_file(file, root, source_dir, dest_dir_pictures, no_exif_dir_pictures):
    '''
    @brief This function processes one image at a time, takes EXIF, 
    analyses name if no Exif and pastes a copy to the destination folder. 
    '''
    source_path = os.path.join(root, file)
    try:
        date, device = get_exif_date_and_device(source_path)
        if date is not None:
            handle_file_with_exif(source_path, date, device, dest_dir_pictures)
        else:
            handle_file_without_exif(source_path, file, root, source_dir, no_exif_dir_pictures, dest_dir_pictures)
    except Exception:
        logger.error('File %s has no exif and no date could be guessed from filename. File copied to no_exif folder %s', source_path, no_exif_dir_pictures)


def copy_srt_file(video_file_path, destination_dir):
    '''if there are subtitle files for a video, rename and copy/move them to the destination directory'''
    base, _ = os.path.splitext(os.path.basename(video_file_path))
    srt_file_name = base.lower() + '.srt'
    dir_files = os.listdir(os.path.dirname(video_file_path))
    for file in dir_files:
        if file.lower() == srt_file_name:
            srt_file_path = os.path.join(os.path.dirname(video_file_path), file)
            destination_path = os.path.join(destination_dir, os.path.basename(srt_file_path))
            if config.careful:
                shutil.copy2(srt_file_path, destination_path)
                logger.info('Copied subtitle file %s to %s.', srt_file_path, destination_path)
            else:
                shutil.move(srt_file_path, destination_path)
                logger.info('Moved subtitle file %s to %s.', srt_file_path, destination_path)



def resolve_destination_path(source_path, dest_path):
    '''
    @brief Resolve destination path by handling collisions with hash-based duplicate detection.
    @param source_path Path to source file
    @param dest_path Intended destination path
    @return Tuple of (final_dest_path, is_duplicate) where is_duplicate indicates if file should be skipped
    '''
    if not os.path.exists(dest_path):
        return dest_path, False

    # Collision detected - check if it's a duplicate
    if are_files_identical(source_path, dest_path):
        # Log to general logger
        logger.info('Duplicate file detected, skipping: %s', source_path)

        # Log detailed information to collision log
        collision_logger.info(
            'DUPLICATE_SKIPPED | Source: %s | Existing: %s | Decision: File skipped (identical hash)',
            source_path,
            dest_path
        )
        return dest_path, True

    # Not a duplicate - add numeric suffix
    base, ext = os.path.splitext(dest_path)
    original_dest = dest_path
    suffix = 1
    while os.path.exists(dest_path):
        dest_path = f"{base}_{suffix}{ext}"
        suffix += 1

    # Log to general logger
    logger.warning('Name collision resolved with suffix: %s', dest_path)

    # Log detailed information to collision log
    collision_logger.warning(
        'COLLISION_RESOLVED | Source: %s | Original destination: %s | New destination: %s | Decision: Added suffix _%d (different hash)',
        source_path,
        original_dest,
        dest_path,
        suffix - 1
    )
    return dest_path, False


def handle_file_with_exif(source_path, date, device, dest_dir_pictures):
    dest_dir = create_directory_structure(dest_dir_pictures, date)
    dest_path = os.path.join(dest_dir, rename_image(source_path, date, device))

    # Resolve collisions and check for duplicates
    dest_path, is_duplicate = resolve_destination_path(source_path, dest_path)

    if is_duplicate:
        return  # Skip duplicate file

    if config.careful:
        shutil.copy2(source_path, dest_path)
        logger.info('Copied file %s to %s.', source_path, dest_path)
    else:
        shutil.move(source_path, dest_path)
        logger.info('Moved file %s to %s.', source_path, dest_path)
    if source_path.lower().endswith(".lrf"):
        copy_srt_file(source_path, dest_dir)


def handle_file_without_exif(source_path, file, root, source_dir, no_exif_dir_pictures, dest_dir_pictures):
    relative_path = os.path.relpath(root, source_dir)
    no_exif_dir = os.path.join(no_exif_dir_pictures, relative_path)
    os.makedirs(no_exif_dir, exist_ok=True)
    dest_path = os.path.join(no_exif_dir, file)
    logger.warning('No EXIF data found in file %s, trying to extract date from filename.', source_path)

    date = extract_date_from_filename(file)
    if date is not None and date <= datetime.now():
        dest_dir = create_directory_structure(dest_dir_pictures, date)
        # replace the no_exif-dest_path with the new dest_path
        dest_path = os.path.join(dest_dir, rename_image(source_path, date, device=None))

    copy_file_with_new_exif(source_path, dest_path, date, file)


def extract_date_from_filename(file):
    match = re.search(r'\d{4}[-:_\s]\d{2}[-:_\s]\d{2}[-:_\s]\d{2}[-:_\s\.]\d{2}[-:_\s\.]\d{2}', file)
    if not match:
        match = re.search(r'\d{4}-\d{2}-\d{2}-\d{2}h\d{2}m\d{2}s', file) # for VLC screenshots
    if not match:
        match = re.search(r'\d{4}\d{2}\d{2}_\d{2}\d{2}\d{2}', file) # for filenames like 'IMG_20190821_174044_240.jpg'
    if match:
        date_str = match.group().replace('.', ':') # replace dots with colons, for parser compatibility
        try:
            date = parse(date_str, fuzzy = True)  # pulls non date info into datetime MUST DEBUG
            logger.info('Parsed date %s from filename %s.', date_str, file)
            return date
        except ValueError:
            logger.error('Unable to parse date from filename %s', file)
    return None


def copy_file_with_new_exif(source_path, dest_path, date, file):
    # Resolve collisions and check for duplicates
    dest_path, is_duplicate = resolve_destination_path(source_path, dest_path)

    if is_duplicate:
        return  # Skip duplicate file

    if config.careful:
        shutil.copy2(source_path, dest_path)
        logger.info('Copied file %s to %s.', source_path, dest_path)
    else:
        shutil.move(source_path, dest_path)
        logger.info('Moved file %s to %s.', source_path, dest_path)

    # Load the EXIF data from the copied file
    exif_dict = piexif.load(dest_path)
    # Convert the date to the format expected by EXIF
    date_str = date.strftime('%Y:%m:%d %H:%M:%S')
    # Update the EXIF data with the new date
    exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = date_str
    exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = date_str
    exif_dict['0th'][piexif.ImageIFD.DateTime] = date_str

    # Write the updated EXIF data back to the file
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, dest_path)

def process_file_non_media(file, root, source_dir, non_media_dir):
    source_path = os.path.join(root, file)
    destination = os.path.join(non_media_dir, file)

    # Resolve collisions and check for duplicates
    destination, is_duplicate = resolve_destination_path(source_path, destination)

    if is_duplicate:
        return  # Skip duplicate file

    destination_dir = os.path.dirname(destination)
    os.makedirs(destination_dir, exist_ok=True)

    if config.careful:
        shutil.copy2(source_path, destination)
        logger.info('Copied non-media file %s to %s.', file, destination)
    else:
        shutil.move(source_path, destination)
        logger.info('Moved non-media file %s to %s.', file, destination)