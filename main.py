import os
from imagetools import process_file, process_file_non_media
from config import (
    source_dirs, image_extensions, raw_extensions, video_extensions,
    dest_dir_pictures, dest_dir_pictures_raw, dest_dir_videos, 
    non_media_directory, no_exif_dir_pictures, 
    no_exif_dir_pictures_raw, no_exif_dir_videos)

# Set up logging
# logging.basicConfig(filename='logfile.log', level=logging.INFO, format='%(asctime)s %(message)s')


def main():
    for source_dir in source_dirs:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.lower().endswith(tuple(image_extensions)): # for image files
                    process_file(file, root, source_dir, dest_dir_pictures, no_exif_dir_pictures)
                elif file.lower().endswith(tuple(raw_extensions)): # for RAW files
                    process_file(file, root, source_dir, dest_dir_pictures_raw, no_exif_dir_pictures_raw)
                elif file.lower().endswith(tuple(video_extensions)): # for video files
                    process_file(file, root, source_dir, dest_dir_videos, no_exif_dir_videos)
                else: # for non-media files
                    process_file_non_media(file, root, source_dir, non_media_directory)


main()
