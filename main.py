import os
import shutil
from PIL import Image
import logging
import exifread
from dateutil.parser import parse
from datetime import datetime
import re

# Set up logging
logging.basicConfig(filename='logfile.log', level=logging.INFO, format='%(asctime)s %(message)s')


## @brief This function gets the date and device model from the EXIF data of an image.
#  @param image_path The path to the image file.
#  @return A tuple containing the date and device model from the EXIF data, or None if the EXIF data does not exist or an error occurs.
def get_exif_date_and_device(image_path):
    try:
        date = None
        device = None
        if image_path.lower().endswith(('.raw', '.cr2', '.nef', '.dng')):
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f)
                if 'EXIF DateTimeOriginal' in tags:
                    date_time = str(tags['EXIF DateTimeOriginal'])
                    date = datetime.strptime(date_time, '%Y:%m:%d %H:%M:%S')
                if 'Image Model' in tags:
                    device = str(tags['Image Model'])
        else:
            image = Image.open(image_path)
            exif_data = image._getexif()
            if exif_data is not None:
                date_time = exif_data.get(36867)  # DateTimeOriginal tag
                if date_time is not None:
                    date = datetime.strptime(date_time, '%Y:%m:%d %H:%M:%S')
                device = exif_data.get(272)  # Model tag
                if device is not None:
                    device = device.strip().replace(' ', '_')
        return date, device
    except Exception as e:
        logging.exception(f'Failed to get EXIF data from file {image_path} due to error: {e}')
    return None, None

## @brief This function creates a directory structure based on a date.
#  @param base_dir The base directory where the directory structure will be created.
#  @param date The date used to create the directory structure.
#  @return The path to the created month directory.
def create_directory_structure(base_dir, date):
    year = date.year
    month = date.month
    year_dir = os.path.join(base_dir, str(year))
    month_dir = os.path.join(year_dir, f"{year}-{month:02d}")
    os.makedirs(month_dir, exist_ok=True)
    return month_dir

## @brief This function renames an image file based on a date and device model.
#  @param image_path The path to the image file.
#  @param date The date used to rename the image file.
#  @param device The device model used to rename the image file.
#  @return The new name of the image file.
def rename_image(image_path, date, device):
    _, ext = os.path.splitext(image_path)
    new_name = date.isoformat() # use ISO 8601 format for date and time
    if device is not None:
        new_name += "_" + device
    new_name += ext
    return new_name

source_dir = "/home/rafael/Pictures"
dest_dir_pictures = "/home/rafael/Pictures2/Pictures"
dest_dir_pictures_raw = "/home/rafael/Pictures2/Pictures_RAW"

no_exif_dir_pictures = os.path.join(dest_dir_pictures, "no_exif")
no_exif_dir_pictures_raw = os.path.join(dest_dir_pictures_raw, "no_exif")
os.makedirs(no_exif_dir_pictures, exist_ok=True)
os.makedirs(no_exif_dir_pictures_raw, exist_ok=True)


## @brief This block of code iterates over all the images in the source directory.
def process_file(file, root, source_dir, dest_dir_pictures, no_exif_dir_pictures):
    source_path = os.path.join(root, file)
    try:
        date, device = get_exif_date_and_device(source_path)
        if date is not None:
            dest_dir = create_directory_structure(dest_dir_pictures, date)
            dest_path = os.path.join(dest_dir, rename_image(source_path, date, device))
        else:
            relative_path = os.path.relpath(root, source_dir)
            no_exif_dir = os.path.join(no_exif_dir_pictures, relative_path)
            os.makedirs(no_exif_dir, exist_ok=True)
            dest_path = os.path.join(no_exif_dir, file)
            logging.warning(f'No EXIF data found in file {source_path}')

            # Try to extract datetime from filename
            match = re.search(r'\d{4}[-:_\s]\d{2}[-:_\s]\d{2}[-:_\s]\d{2}[-:_\s]\d{2}[-:_\s]\d{2}', file)
            if not match:
                match = re.search(r'\d{4}-\d{2}-\d{2}-\d{2}h\d{2}m\d{2}s', file) # for VLC screenshots
            if match:
                date_str = match.group()
                try:
                    date = parse(date_str)
                    dest_dir = create_directory_structure(dest_dir_pictures, date)
                    dest_path = os.path.join(dest_dir, file)
                except ValueError:
                    logging.error(f'Unable to parse date from filename {file}')

        shutil.copy2(source_path, dest_path)
        logging.info(f'Copied file {source_path} to {dest_path}')
    except Exception as e:
        logging.error(f'Failed to copy file {source_path} due to error: {e}')

for root, dirs, files in os.walk(source_dir):
    for file in files:
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff')):
            process_file(file, root, source_dir, dest_dir_pictures, no_exif_dir_pictures)
        elif file.lower().endswith(('.raw', '.cr2', '.nef', '.dng')):  # add more RAW formats if needed
            process_file(file, root, source_dir, dest_dir_pictures_raw, no_exif_dir_pictures_raw)
