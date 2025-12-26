# Docker Deployment Guide for Media Structurer

This guide explains how to deploy Media Structurer to `tricc` using Docker, eliminating unnecessary network traffic in your Syncthing setup.

## Why Docker on tricc?

**Current inefficient flow:**
1. Devices → sync to `tricc:/datalake`
2. `tricc:/datalake` → sync to `stark:/datalake`
3. Media structurer runs on `stark`, reorganizes files
4. `stark:/organized` → syncs back to `tricc:/organized`

**New efficient flow:**
1. Devices → sync to `tricc:/datalake`
2. Media structurer runs **directly on `tricc`**, reorganizes files locally
3. ✅ No unnecessary network traffic!

## Prerequisites

- Docker installed on `tricc` (already verified: ✓)
- SSH access to `tricc` (already configured: ✓)
- rsync installed (standard on most Linux systems)

## Quick Start

### 1. Deploy to tricc (from stark)

Run the automated deployment script:

```bash
./deploy.sh
```

This script will:
- Create the remote directory on tricc at `/home/rafael/repos/media_structurer`
- Sync code via rsync (excludes .git, .venv, logs, etc.)
- Build the Docker image **on tricc**
- Set up configuration directories
- Display next steps

### 2. Configure paths on tricc

SSH into tricc:

```bash
ssh rafael@tricc
cd ~/media-structurer
```

Edit `config.tricc.toml` with actual paths on tricc:

```bash
nano config.tricc.toml
```

Update the `source_dirs` to point to your actual datalake location.

### 3. Update docker-compose.yml volume mappings

Edit the volume mappings to match your actual paths on tricc:

```bash
nano docker-compose.yml
```

Replace all `/path/to/...` placeholders with actual paths. For example:

```yaml
volumes:
  - ./config.tricc.toml:/app/config.toml:ro
  - /home/rafael/Sync/datalake:/data/datalake:rw
  - /home/rafael/Pictures:/data/Pictures:rw
  - /home/rafael/Pictures/RAW:/data/Pictures/RAW:rw
  - /home/rafael/Videos:/data/Videos:rw
  - /home/rafael/fromLake_NonMedia:/data/fromLake_NonMedia:rw
  - ./logs:/app/logs:rw
```

### 4. Run the container

**One-time run:**
```bash
docker-compose up
```

**Run in background:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f
```

**Stop the container:**
```bash
docker-compose down
```

## Automation Options

### Option A: Cron Job (Scheduled)

Run media structurer every hour:

```bash
crontab -e
```

Add this line:
```
0 * * * * cd ~/media-structurer && docker-compose up >> ~/media-structurer/cron.log 2>&1
```

### Option B: Syncthing Folder Watch (Event-driven)

Use `inotifywait` to trigger when new files arrive:

```bash
#!/bin/bash
# Save as ~/media-structurer/watch.sh

while inotifywait -r -e create,moved_to /path/to/datalake; do
    cd ~/media-structurer
    docker-compose up
    sleep 60  # Debounce: wait 60s before watching again
done
```

Make executable and run in background:
```bash
chmod +x ~/media-structurer/watch.sh
nohup ~/media-structurer/watch.sh &
```

### Option C: Systemd Service (Best for production)

Create `/etc/systemd/system/media-structurer-watch.service`:

```ini
[Unit]
Description=Media Structurer Folder Watch
After=network.target docker.service

[Service]
Type=simple
User=rafael
WorkingDirectory=/home/rafael/media-structurer
ExecStart=/home/rafael/media-structurer/watch.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable media-structurer-watch
sudo systemctl start media-structurer-watch
sudo systemctl status media-structurer-watch
```

## Updating the Container

When you make changes to the code on stark:

1. **On stark**, run the deployment script again:
   ```bash
   ./deploy.sh
   ```

   This will:
   - Sync only changed files via rsync (fast!)
   - Rebuild the Docker image on tricc
   - Keep your config files intact

2. **On tricc**, restart the container:
   ```bash
   cd ~/repos/media_structurer
   docker-compose down
   docker-compose up -d
   ```

## Troubleshooting

### Permission Issues

If you encounter permission errors, uncomment and adjust the `user` line in `docker-compose.yml`:

```yaml
user: "1000:1000"  # Replace with your UID:GID on tricc
```

Find your UID/GID on tricc:
```bash
id
```

### Image Not Found

If Docker can't find the image on tricc:

```bash
# Check if image exists
docker images | grep media-structurer

# If not, re-run deployment from stark
```

### Configuration Issues

Check the logs:
```bash
docker-compose logs
```

Verify volume mounts are correct:
```bash
docker-compose config
```

### Test Run

Do a dry run with `careful = true` in config:

```bash
nano config.tricc.toml  # Set careful = true
docker-compose up
```

This will copy files instead of moving them, allowing you to verify everything works before committing to moves.

## Files Created

- `Dockerfile` - Container image definition
- `pyproject.toml` - Python dependencies
- `docker-compose.yml` - Container orchestration
- `config.tricc.toml` - Configuration template for tricc
- `deploy.sh` - Automated deployment script
- `DOCKER_DEPLOYMENT.md` - This documentation

## Benefits of This Setup

✅ **Eliminates double network traffic** - Files only sync once
✅ **Isolated environment** - No dependency conflicts
✅ **Reproducible** - Same environment every time
✅ **Easy updates** - Just run `deploy.sh` again
✅ **Logs persist** - Stored in `~/media-structurer/logs` on tricc
✅ **Safe testing** - Use `careful = true` for dry runs
