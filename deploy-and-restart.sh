#!/bin/bash

# Media Structurer - Deploy and Auto-Restart Script
# This script syncs code, builds image, and restarts the container

set -e

REMOTE_HOST="rafael@tricc"
REMOTE_DIR="/home/rafael/repos/media_structurer"

echo "========================================"
echo "Deploying and Restarting..."
echo "========================================"
echo ""

# Run the main deploy script
./deploy.sh

# Restart the container on tricc
echo ""
echo "Restarting container on tricc..."
ssh ${REMOTE_HOST} "cd ${REMOTE_DIR} && docker-compose down && docker-compose up -d"

if [ $? -eq 0 ]; then
    echo "✓ Container restarted successfully"
    echo ""
    echo "View logs with:"
    echo "  ssh ${REMOTE_HOST} 'cd ${REMOTE_DIR} && docker-compose logs -f'"
else
    echo "✗ Failed to restart container"
    exit 1
fi
