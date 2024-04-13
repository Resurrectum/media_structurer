'''Image tools for the image processing script.'''
import os
import re
import shutil
from datetime import datetime
from PIL import Image
import exifread
import piexif
from dateutil.parser import parse
from logger import logger

def get_exif_date_and_device(image_path):
    '''
    @brief This function gets the date and device model from the EXIF data of an image.
    @param image_path The path to the image file.
    @return A tuple containing the date and device model from the EXIF data, 
    or None if the EXIF data does not exist or an error occurs.
    '''
    try:
        date = None
        device = None
        if image_path.lower().endswith(('.raw', '.cr2', '.nef', '.dng')): # for RAW files
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f)
                if 'EXIF DateTimeOriginal' in tags:
                    date_time = str(tags['EXIF DateTimeOriginal'])
                    date = datetime.strptime(date_time, '%Y:%m:%d %H:%M:%S')
                if 'Image Model' in tags:
                    device = str(tags['Image Model'])
        else: # for other image files
            image = Image.open(image_path)
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
        return date, device
    except Exception as e:
        logger.warning('Failed to get EXIF data from file %s due to error: %s', image_path, e)
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


def handle_file_with_exif(source_path, date, device, dest_dir_pictures):
    dest_dir = create_directory_structure(dest_dir_pictures, date)
    dest_path = os.path.join(dest_dir, rename_image(source_path, date, device))
    shutil.copy2(source_path, dest_path)
    logger.info('Copied file %s to %s.', source_path, dest_path)


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
    # Add suffix if a file already exists in the destination
    suffix = 0
    while os.path.exists(dest_path):
        base, ext = os.path.splitext(dest_path)
        suffix += 1
        dest_path = f"{base}_{suffix}{ext}"
        logger.warning('A file named %s already exists in %s. The filename will get a suffix.', file, dest_path)
    
    shutil.copy2(source_path, dest_path)
    logger.info('Copied file %s to %s.', source_path, dest_path)
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