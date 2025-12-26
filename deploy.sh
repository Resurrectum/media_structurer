#!/bin/bash

# Media Structurer - Docker Deployment Script
# This script syncs code to tricc via rsync and builds the image on tricc

set -e  # Exit on error

# Configuration
IMAGE_NAME="media-structurer"
IMAGE_TAG="latest"
REMOTE_HOST="rafael@tricc"
REMOTE_DIR="/home/rafael/repos/media_structurer"
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================"
echo "Media Structurer - Docker Deployment"
echo "========================================"
echo ""

# Step 1: Create remote directory
echo "[1/4] Setting up remote directory..."
ssh ${REMOTE_HOST} "mkdir -p ${REMOTE_DIR}"

if [ $? -eq 0 ]; then
    echo "✓ Remote directory ready"
else
    echo "✗ Failed to create remote directory"
    exit 1
fi
echo ""

# Step 2: Sync code to tricc via rsync
echo "[2/4] Syncing code to tricc via rsync..."
rsync -av --delete \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.venv' \
    --exclude='venv' \
    --exclude='logs/' \
    --exclude='config.toml' \
    --exclude='.DS_Store' \
    --exclude='.vscode' \
    "${LOCAL_DIR}/" "${REMOTE_HOST}:${REMOTE_DIR}/"

if [ $? -eq 0 ]; then
    echo "✓ Code synced to tricc"
else
    echo "✗ Failed to sync code"
    exit 1
fi
echo ""

# Step 3: Build Docker image on tricc
echo "[3/4] Building Docker image on tricc..."
ssh ${REMOTE_HOST} "cd ${REMOTE_DIR} && docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."

if [ $? -eq 0 ]; then
    echo "✓ Docker image built on tricc"
else
    echo "✗ Failed to build Docker image"
    exit 1
fi
echo ""

# Step 4: Setup configuration
echo "[4/4] Setting up configuration..."
ssh ${REMOTE_HOST} "
    cd ${REMOTE_DIR}
    mkdir -p logs
"

echo "✓ Configuration setup complete"
echo ""

# Display next steps
echo "========================================"
echo "Deployment Complete!"
echo "========================================"
echo ""
echo "Next Steps:"
echo "========================================"
echo ""
echo "1. SSH into tricc and configure paths:"
echo "   ssh ${REMOTE_HOST}"
echo "   cd ${REMOTE_DIR}"
echo ""
echo "2. Edit config.tricc.toml with actual datalake/destination paths"
echo "   nano config.tricc.toml"
echo ""
echo "3. Edit docker-compose.yml volume mappings:"
echo "   nano docker-compose.yml"
echo "   Update all '/path/to/...' with actual paths on tricc"
echo ""
echo "4. Run the container:"
echo "   docker-compose up"
echo ""
echo "   Or run in background:"
echo "   docker-compose up -d"
echo ""
echo "5. View logs:"
echo "   docker-compose logs -f"
echo ""
echo "========================================"
echo ""
echo "📍 Repository location on tricc: ${REMOTE_DIR}"
echo ""
