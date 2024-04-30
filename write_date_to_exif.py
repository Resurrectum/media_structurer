import os
import piexif
from datetime import datetime
from config import image_extensions

def write_datetime_to_exif(image_path, date):
    # Convert the date to the format required by EXIF
    exif_date = date.strftime('%Y:%m:%d %H:%M:%S')

    # Load the existing EXIF data
    exif_dict = piexif.load(image_path)

    # Update the EXIF data with the new date
    exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = exif_date
    exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = exif_date

    # Write the updated EXIF data back to the image
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, image_path)



def main(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(tuple(image_extensions)):
                image_path = os.path.join(root, file)
                date_string = input(f"Enter a date for {image_path}: ")
                date = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
                write_datetime_to_exif(image_path, date)

main('/home/rafael/Downloads/datalake/no_exif_jpg')
