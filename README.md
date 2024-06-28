Easy python script that takes all your photos and orders them in a structured way:
- a folder for the year the picutre was taken. For instance `2024`
- inside that folder, 12 folders for the month the picture was taken, for instance `2024-01`
- inside that folder all photos taken in the month 2024-01, named `YYYY-MM-DD_hh_mm_ss-camera_model.jpg`
- RAW images are recognised and stored in a specific `RAW` folder with the same structure as described above
- Photos without exif data are saved in a `no_exif` folder
- Photos without exif data, where the date is stored in the name of the image, it is derived from the name, written into the exif data of the image and renamed and stored accordingly
- the script is configured via a `toml` configuration file
- a `careful` execution mode is possible. In that case the photos are not moved but copied (duplicated) in a target folder
- all steps are logged in a log-file
