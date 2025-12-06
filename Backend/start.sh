#!/bin/bash

# ChunkSmith Backend - Quick Start Script
# This script helps you set up and run the backend quickly

set -e  # Exit on error

echo "🚀 ChunkSmith Backend - Docker Setup"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo -e "${GREEN}✅ Docker is installed${NC}"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker Compose is installed${NC}"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo "Creating .env from .env.example..."
    
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env file${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env and add your API keys:${NC}"
        echo "   - GOOGLE_API_KEY"
        echo "   - GROQ_API_KEY"
        echo ""
        read -p "Press Enter after you've updated .env file..."
    else
        echo -e "${RED}❌ .env.example not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env file found${NC}"
fi

echo ""

# Create data directories if they don't exist
echo "📁 Creating data directories..."
mkdir -p data/uploads data/images data/pickle data/json data/chroma_db
echo -e "${GREEN}✅ Data directories created${NC}"
echo ""

# Ask user what to do
echo "What would you like to do?"
echo "1) Build and start (fresh build)"
echo "2) Start existing containers"
echo "3) Stop containers"
echo "4) View logs"
echo "5) Rebuild from scratch"
echo "6) Production deployment"
echo ""
read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        echo ""
        echo "🔨 Building and starting containers..."
        docker-compose up -d --build
        echo ""
        echo -e "${GREEN}✅ Containers started successfully!${NC}"
        echo ""
        echo "🌐 Access your API at:"
        echo "   - Base URL: http://localhost:8000"
        echo "   - Docs: http://localhost:8000/docs"
        echo "   - Health: http://localhost:8000/api/health"
        echo ""
        echo "📋 View logs with: docker-compose logs -f"
        ;;
    2)
        echo ""
        echo "▶️  Starting containers..."
        docker-compose start
        echo -e "${GREEN}✅ Containers started${NC}"
        ;;
    3)
        echo ""
        echo "⏸️  Stopping containers..."
        docker-compose stop
        echo -e "${GREEN}✅ Containers stopped${NC}"
        ;;
    4)
        echo ""
        echo "📋 Showing logs (Ctrl+C to exit)..."
        docker-compose logs -f
        ;;
    5)
        echo ""
        echo "🗑️  Removing old containers..."
        docker-compose down -v
        echo "🔨 Rebuilding from scratch..."
        docker-compose build --no-cache
        echo "▶️  Starting fresh containers..."
        docker-compose up -d
        echo -e "${GREEN}✅ Fresh build complete!${NC}"
        ;;
    6)
        echo ""
        echo "🏭 Starting production deployment..."
        docker-compose -f docker-compose.prod.yml up -d --build
        echo -e "${GREEN}✅ Production containers started!${NC}"
        ;;
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "✨ Done!"
