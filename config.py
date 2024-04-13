'''File to import configuration from a toml file and do further processing'''
import os
import toml

# Import configuration from a toml file
config = toml.load('config.toml')


source_dirs = config['source_dirs']
dest_dir_pictures = config['dest_dir_pictures']
dest_dir_pictures_raw = config['dest_dir_pictures_raw']
no_exif_directories_both = config['no_exif_directories_both']

no_exif_dir_pictures = os.path.join(dest_dir_pictures, no_exif_directories_both)
no_exif_dir_pictures_raw = os.path.join(dest_dir_pictures_raw, no_exif_directories_both)
