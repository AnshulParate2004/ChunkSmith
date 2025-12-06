@echo off
REM ChunkSmith Backend - Push to Docker Hub (Windows)
REM This script automates building and pushing your Docker image

echo ============================================
echo 🐳 ChunkSmith - Push to Docker Hub
echo ============================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running
    echo Please start Docker Desktop and try again
    pause
    exit /b 1
)
echo ✅ Docker is running
echo.

REM Get Docker Hub username
set /p DOCKER_USERNAME="Enter your Docker Hub username: "
if "%DOCKER_USERNAME%"=="" (
    echo ❌ Username cannot be empty
    pause
    exit /b 1
)

echo.
echo 📝 Image will be: %DOCKER_USERNAME%/chunksmith-backend
echo.

REM Get version tag (optional)
set /p VERSION_TAG="Enter version tag (e.g., v1.0.0) or press Enter for 'latest' only: "
echo.

REM Login to Docker Hub
echo 🔐 Logging into Docker Hub...
docker login
if errorlevel 1 (
    echo ❌ Docker login failed
    pause
    exit /b 1
)
echo ✅ Logged in successfully
echo.

REM Navigate to project root (where pyproject.toml is)
cd ..
echo 📂 Building from: %CD%
echo.

REM Build the image
echo 🔨 Building Docker image...
echo This may take a few minutes...
echo.
docker build -t %DOCKER_USERNAME%/chunksmith-backend:latest -f Backend/Dockerfile .
if errorlevel 1 (
    echo ❌ Build failed
    cd Backend
    pause
    exit /b 1
)
echo ✅ Build successful
echo.

REM Tag with version if provided
if not "%VERSION_TAG%"=="" (
    echo 🏷️  Tagging with version: %VERSION_TAG%
    docker tag %DOCKER_USERNAME%/chunksmith-backend:latest %DOCKER_USERNAME%/chunksmith-backend:%VERSION_TAG%
    echo ✅ Tagged successfully
    echo.
)

REM Get current date for date tag
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set DATE_TAG=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%
echo 🏷️  Tagging with date: %DATE_TAG%
docker tag %DOCKER_USERNAME%/chunksmith-backend:latest %DOCKER_USERNAME%/chunksmith-backend:%DATE_TAG%
echo ✅ Tagged successfully
echo.

REM Show all tags
echo 📋 Image tags created:
docker images | findstr %DOCKER_USERNAME%/chunksmith-backend
echo.

REM Ask for confirmation
set /p CONFIRM="🚀 Ready to push to Docker Hub. Continue? (yes/no): "
if /i not "%CONFIRM%"=="yes" (
    echo ❌ Push cancelled
    cd Backend
    pause
    exit /b 0
)
echo.

REM Push latest tag
echo 📤 Pushing latest tag...
docker push %DOCKER_USERNAME%/chunksmith-backend:latest
if errorlevel 1 (
    echo ❌ Push failed
    cd Backend
    pause
    exit /b 1
)
echo ✅ Pushed latest tag
echo.

REM Push version tag if provided
if not "%VERSION_TAG%"=="" (
    echo 📤 Pushing version tag: %VERSION_TAG%...
    docker push %DOCKER_USERNAME%/chunksmith-backend:%VERSION_TAG%
    echo ✅ Pushed version tag
    echo.
)

REM Push date tag
echo 📤 Pushing date tag: %DATE_TAG%...
docker push %DOCKER_USERNAME%/chunksmith-backend:%DATE_TAG%
echo ✅ Pushed date tag
echo.

REM Success message
echo ============================================
echo ✅ SUCCESS! Image pushed to Docker Hub
echo ============================================
echo.
echo 🌐 View your image at:
echo https://hub.docker.com/r/%DOCKER_USERNAME%/chunksmith-backend
echo.
echo 📥 Anyone can now pull your image with:
echo docker pull %DOCKER_USERNAME%/chunksmith-backend:latest
echo.
echo 🏷️  Available tags:
echo - latest
if not "%VERSION_TAG%"=="" echo - %VERSION_TAG%
echo - %DATE_TAG%
echo.
echo 💡 Don't forget to:
echo 1. Update the README on Docker Hub
echo 2. Add usage instructions
echo 3. List required environment variables
echo.

cd Backend
pause
