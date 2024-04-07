'''Image tools for the image processing script.'''
import os, re, shutil, piexif, logging, exifread
from PIL import Image
from datetime import datetime
from dateutil.parser import parse

def get_exif_date_and_device(image_path):
    '''
    @brief This function gets the date and device model from the EXIF data of an image.
    @param image_path The path to the image file.
    @return A tuple containing the date and device model from the EXIF data, or None if the EXIF data does not exist or an error occurs.
    '''
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
    new_name = date.isoformat() # use ISO 8601 format for date and time
    if device is not None:
        new_name += "_" + device
    new_name += ext
    return new_name



def process_file(file, root, source_dir, dest_dir_pictures, no_exif_dir_pictures):
    '''
    @brief This block processes one image at a time, takes EXIF, 
    analyses name if no Exif and pastes a copy to the destination folder. 
    '''
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
            match = re.search(r'\d{4}[-:_\s]\d{2}[-:_\s]\d{2}[-:_\s]\d{2}[-:_\s\.]\d{2}[-:_\s\.]\d{2}', file)
            if not match:
                match = re.search(r'\d{4}-\d{2}-\d{2}-\d{2}h\d{2}m\d{2}s', file) # for VLC screenshots
            if not match:
                match = re.search(r'\d{4}\d{2}\d{2}_\d{2}\d{2}\d{2}', file) # for filenames like 'IMG_20190821_174044_240.jpg'
            if match:
                date_str = match.group()
                date_str = date_str.replace('.', ':') # replace dots with colons, for parser compatibility
                try:
                    date = parse(date_str, fuzzy = True)  # pulls non date info into datetime MUST DEBUG
                    if date > datetime.now():
                        logging.warning(f'Parsing date in file {file} returns future date {date}. File moved to no_exif directory.')
                    else:
                        dest_dir = create_directory_structure(dest_dir_pictures, date)
                        dest_path = os.path.join(dest_dir, file)
                except ValueError:
                    logging.error(f'Unable to parse date from filename {file}')
            # Add suffix if a file already exists in the destination
        suffix = 0
        while os.path.exists(dest_path):
            base, ext = os.path.splitext(dest_path)
            suffix += 1
            dest_path = f"{base}_{suffix}{ext}"
        
        shutil.copy2(source_path, dest_path)
        logging.info(f'Copied file {source_path} to {dest_path}.')
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
    except Exception as e:
        logging.error(f'Failed to copy file {source_path} due to error: {e} using filename.')
