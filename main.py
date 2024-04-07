import os
import logging
from imagetools import process_file
from config import *

# Set up logging
logging.basicConfig(filename='logfile.log', level=logging.INFO, format='%(asctime)s %(message)s')

os.makedirs(config['no_exif_dir_pictures'], exist_ok=True)
os.makedirs(['no_exif_dir_pictures_raw'], exist_ok=True)

def main():
    for source_dir in source_dirs:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff')):
                    process_file(file, root, source_dir, dest_dir_pictures, no_exif_dir_pictures)
                elif file.lower().endswith(('.raw', '.cr2', '.nef', '.dng')):  # add more RAW formats if needed
                    process_file(file, root, source_dir, dest_dir_pictures_raw, no_exif_dir_pictures_raw)


main()
