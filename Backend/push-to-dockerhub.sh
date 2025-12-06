#!/bin/bash

# ChunkSmith Backend - Push to Docker Hub (Linux/Mac)
# This script automates building and pushing your Docker image

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "============================================"
echo "🐳 ChunkSmith - Push to Docker Hub"
echo "============================================"
echo ""

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Get Docker Hub username
read -p "Enter your Docker Hub username: " DOCKER_USERNAME
if [ -z "$DOCKER_USERNAME" ]; then
    echo -e "${RED}❌ Username cannot be empty${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}📝 Image will be: $DOCKER_USERNAME/chunksmith-backend${NC}"
echo ""

# Get version tag (optional)
read -p "Enter version tag (e.g., v1.0.0) or press Enter for 'latest' only: " VERSION_TAG
echo ""

# Login to Docker Hub
echo "🔐 Logging into Docker Hub..."
docker login
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker login failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Logged in successfully${NC}"
echo ""

# Navigate to project root
cd ..
echo -e "${BLUE}📂 Building from: $(pwd)${NC}"
echo ""

# Build the image
echo "🔨 Building Docker image..."
echo "This may take a few minutes..."
echo ""
docker build -t $DOCKER_USERNAME/chunksmith-backend:latest -f Backend/Dockerfile .
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed${NC}"
    cd Backend
    exit 1
fi
echo -e "${GREEN}✅ Build successful${NC}"
echo ""

# Tag with version if provided
if [ ! -z "$VERSION_TAG" ]; then
    echo "🏷️  Tagging with version: $VERSION_TAG"
    docker tag $DOCKER_USERNAME/chunksmith-backend:latest $DOCKER_USERNAME/chunksmith-backend:$VERSION_TAG
    echo -e "${GREEN}✅ Tagged successfully${NC}"
    echo ""
fi

# Get current date for date tag
DATE_TAG=$(date +%Y-%m-%d)
echo "🏷️  Tagging with date: $DATE_TAG"
docker tag $DOCKER_USERNAME/chunksmith-backend:latest $DOCKER_USERNAME/chunksmith-backend:$DATE_TAG
echo -e "${GREEN}✅ Tagged successfully${NC}"
echo ""

# Show all tags
echo "📋 Image tags created:"
docker images | grep $DOCKER_USERNAME/chunksmith-backend
echo ""

# Ask for confirmation
read -p "🚀 Ready to push to Docker Hub. Continue? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo -e "${RED}❌ Push cancelled${NC}"
    cd Backend
    exit 0
fi
echo ""

# Push latest tag
echo "📤 Pushing latest tag..."
docker push $DOCKER_USERNAME/chunksmith-backend:latest
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Push failed${NC}"
    cd Backend
    exit 1
fi
echo -e "${GREEN}✅ Pushed latest tag${NC}"
echo ""

# Push version tag if provided
if [ ! -z "$VERSION_TAG" ]; then
    echo "📤 Pushing version tag: $VERSION_TAG..."
    docker push $DOCKER_USERNAME/chunksmith-backend:$VERSION_TAG
    echo -e "${GREEN}✅ Pushed version tag${NC}"
    echo ""
fi

# Push date tag
echo "📤 Pushing date tag: $DATE_TAG..."
docker push $DOCKER_USERNAME/chunksmith-backend:$DATE_TAG
echo -e "${GREEN}✅ Pushed date tag${NC}"
echo ""

# Success message
echo "============================================"
echo -e "${GREEN}✅ SUCCESS! Image pushed to Docker Hub${NC}"
echo "============================================"
echo ""
echo "🌐 View your image at:"
echo "https://hub.docker.com/r/$DOCKER_USERNAME/chunksmith-backend"
echo ""
echo "📥 Anyone can now pull your image with:"
echo "docker pull $DOCKER_USERNAME/chunksmith-backend:latest"
echo ""
echo "🏷️  Available tags:"
echo "- latest"
if [ ! -z "$VERSION_TAG" ]; then
    echo "- $VERSION_TAG"
fi
echo "- $DATE_TAG"
echo ""
echo "💡 Don't forget to:"
echo "1. Update the README on Docker Hub"
echo "2. Add usage instructions"
echo "3. List required environment variables"
echo ""

cd Backend
