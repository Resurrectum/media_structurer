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

## Running the Application

### Local Execution

```bash
python main.py
```

### Docker Deployment

For running on a server (e.g., with Syncthing to eliminate network traffic):

```bash
# See DOCKER_DEPLOYMENT.md for complete instructions
./deploy.sh                          # Deploy to remote server
ssh server "cd ~/repos/media_structurer && docker-compose up"
```

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for complete Docker deployment guide.

## Duplicate Detection

The project includes perceptual hash-based duplicate detection to identify visually identical images and videos:
- Fast parallel processing using all CPU cores
- Finds duplicates regardless of EXIF differences, file names, or minor edits
- Automatic cleanup tool with intelligent strategies (keep largest, remove collision suffixes, keep oldest)
- Excludes RAW+JPEG pairs from duplicate reports (intentional format conversions)

See `DUPLICATE_DETECTION.md` for complete documentation.
