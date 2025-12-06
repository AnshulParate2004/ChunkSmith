@echo off
REM ChunkSmith Backend - Quick Start Script (Windows)
REM This script helps you set up and run the backend quickly

echo ============================================
echo 🚀 ChunkSmith Backend - Docker Setup
echo ============================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed
    echo Please install Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo ✅ Docker is installed

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed
    pause
    exit /b 1
)
echo ✅ Docker Compose is installed
echo.

REM Check for .env file
if not exist ".env" (
    echo ⚠️  .env file not found
    if exist ".env.example" (
        echo Creating .env from .env.example...
        copy .env.example .env
        echo ✅ Created .env file
        echo.
        echo ⚠️  Please edit .env and add your API keys:
        echo    - GOOGLE_API_KEY
        echo    - GROQ_API_KEY
        echo.
        pause
    ) else (
        echo ❌ .env.example not found
        pause
        exit /b 1
    )
) else (
    echo ✅ .env file found
)
echo.

REM Create data directories
echo 📁 Creating data directories...
if not exist "data\uploads" mkdir data\uploads
if not exist "data\images" mkdir data\images
if not exist "data\pickle" mkdir data\pickle
if not exist "data\json" mkdir data\json
if not exist "data\chroma_db" mkdir data\chroma_db
echo ✅ Data directories created
echo.

REM Menu
echo What would you like to do?
echo 1) Build and start (fresh build)
echo 2) Start existing containers
echo 3) Stop containers
echo 4) View logs
echo 5) Rebuild from scratch
echo 6) Production deployment
echo 7) Clean everything (remove containers and volumes)
echo.
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto build_start
if "%choice%"=="2" goto start
if "%choice%"=="3" goto stop
if "%choice%"=="4" goto logs
if "%choice%"=="5" goto rebuild
if "%choice%"=="6" goto production
if "%choice%"=="7" goto clean
goto invalid

:build_start
echo.
echo 🔨 Building and starting containers...
docker-compose up -d --build
echo.
echo ✅ Containers started successfully!
echo.
echo 🌐 Access your API at:
echo    - Base URL: http://localhost:8000
echo    - Docs: http://localhost:8000/docs
echo    - Health: http://localhost:8000/api/health
echo.
echo 📋 View logs with: docker-compose logs -f
goto end

:start
echo.
echo ▶️  Starting containers...
docker-compose start
echo ✅ Containers started
goto end

:stop
echo.
echo ⏸️  Stopping containers...
docker-compose stop
echo ✅ Containers stopped
goto end

:logs
echo.
echo 📋 Showing logs (Ctrl+C to exit)...
docker-compose logs -f
goto end

:rebuild
echo.
echo 🗑️  Removing old containers...
docker-compose down -v
echo 🔨 Rebuilding from scratch...
docker-compose build --no-cache
echo ▶️  Starting fresh containers...
docker-compose up -d
echo ✅ Fresh build complete!
goto end

:production
echo.
echo 🏭 Starting production deployment...
docker-compose -f docker-compose.prod.yml up -d --build
echo ✅ Production containers started!
goto end

:clean
echo.
echo 🗑️  WARNING: This will remove all containers, volumes, and data!
set /p confirm="Are you sure? (yes/no): "
if /i "%confirm%"=="yes" (
    echo Cleaning up...
    docker-compose down -v
    rmdir /s /q data 2>nul
    echo ✅ Everything cleaned!
) else (
    echo ❌ Cancelled
)
goto end

:invalid
echo ❌ Invalid choice
goto end

:end
echo.
echo ✨ Done!
pause
