import os
import shutil
from PIL import Image
import logging
import exifread

def get_exif_date_and_device(image_path):
    try:
        date = None
        device = None
        if image_path.lower().endswith('.dng'):
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f)
                print(tags)  # print all tags
                if 'EXIF DateTimeOriginal' in tags:
                    date = str(tags['EXIF DateTimeOriginal']).split(" ")[0].replace(":", "-")
                if 'Image Model' in tags:
                    device = str(tags['Image Model'])
        else:
            image = Image.open(image_path)
            exif_data = image._getexif()
            if exif_data is not None:
                for tag, value in exif_data.items():
                    if tag == 36867:  # DateTimeOriginal tag
                        date = value.split(" ")[0].replace(":", "-")
                    elif tag == 272:  # Model tag
                        device = value
        return date, device
    except:
        pass
    return None, None

image_path = '/home/rafael/Pictures/2008/2008-07/RAW/2008-07-27_17-25-16.dng'

get_exif_date_and_device(image_path)
