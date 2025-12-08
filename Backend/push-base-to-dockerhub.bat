REM ============================================
REM push-base-to-dockerhub.bat
REM Push BASE image (dependencies) - SLOW
REM ============================================
@echo off
echo ============================================
echo 🏗️  ChunkSmith - Push BASE Image
echo ============================================
echo.
echo ⚠️  Only run when you change pyproject.toml!
echo ⚠️  This will take 15-30 minutes
echo.

docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running
    pause
    exit /b 1
)

set /p DOCKER_USERNAME="Enter your Docker Hub username: "
if "%DOCKER_USERNAME%"=="" (
    echo ❌ Username cannot be empty
    pause
    exit /b 1
)

echo.
set /p CHANGED="Have you changed pyproject.toml? (yes/no): "
if /i not "%CHANGED%"=="yes" (
    echo ⚠️  No need to rebuild base image!
    echo ⚠️  Use 'push-app-to-dockerhub.bat' instead
    pause
    exit /b 0
)

echo.
docker login
cd ..
echo 🔨 Building base image...
docker build -t %DOCKER_USERNAME%/chunksmith:latest -f Backend/Dockerfile.base .
if errorlevel 1 (
    echo ❌ Build failed
    cd Backend
    pause
    exit /b 1
)

echo 📤 Pushing base image...
docker push %DOCKER_USERNAME%/chunksmith:latest
if errorlevel 1 (
    echo ❌ Push failed
    cd Backend
    pause
    exit /b 1
)

echo.
echo ============================================
echo ✅ SUCCESS! Base image pushed
echo ============================================
echo.
cd Backend
pause