'''File to import configuration from a toml file and do further processing'''
import os
import toml

# Import configuration from a toml file
config = toml.load('config.toml')


careful = config['careful']

source_dirs = config['source_dirs']
dest_dir_pictures = config['dest_dir_pictures']
dest_dir_pictures_raw = config['dest_dir_pictures_raw']
dest_dir_videos = config['dest_dir_videos']
no_exif_directories_all = config['no_exif_directories_all']
non_media_directory = config['dest_non_media']

no_exif_dir_pictures = os.path.join(dest_dir_pictures, no_exif_directories_all)
no_exif_dir_pictures_raw = os.path.join(dest_dir_pictures_raw, no_exif_directories_all)
no_exif_dir_videos = os.path.join(dest_dir_videos, no_exif_directories_all)

# file extensions
image_extensions = config['FileExtensions']['image_extensions']
raw_extensions = config['FileExtensions']['raw_extensions']
video_extensions = config['FileExtensions']['video_extensions']
