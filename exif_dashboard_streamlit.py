import streamlit as st
from PIL import Image
import numpy as np
import os
from datetime import datetime
import write_date_to_exif as wde

# List of image paths
image_paths = [os.path.join(root, file) for root, dirs, files in os.walk('/home/rafael/Downloads/datalake/no_exif_jpg') for file in files if file.lower().endswith('.jpg')]

# Sidebar inputs
st.sidebar.title("Image EXIF Updater")
date = st.sidebar.date_input('Date', datetime.today())
time = st.sidebar.time_input('Time', datetime.now().time())
submit = st.sidebar.button('Submit')

# Display the first image
img_path = image_paths[0]
img = Image.open(img_path)
img_array = np.array(img)
st.image(img_array, use_column_width=True)
st.write(f'Image path: {img_path}')

# Update the EXIF data and display the next image when the submit button is clicked
if submit:
    # Combine the date and time into a datetime object
    date_time = datetime.combine(date, time)
    # Write the selected date and time to the EXIF data of the current image
    wde.write_datetime_to_exif(img_path, date_time)
    st.success(f'Successfully updated EXIF data of {img_path}')