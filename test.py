from pymediainfo import MediaInfo
from datetime import datetime
import os

# file_path = '/home/rafael/Downloads/PXL_20220816_120645826.TS.mp4'
# file_path = '/home/rafael/Downloads/C0005.MP4'
file_path = '/home/rafael/Downloads/00099.MTS'

media_info = MediaInfo.parse(file_path)
for track in media_info.tracks:
    if track.track_type == 'General':
        date_string = track.encoded_date.replace('UTC ', '') # remove 'UTC ' from the date string if it exists
        date = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        device = None