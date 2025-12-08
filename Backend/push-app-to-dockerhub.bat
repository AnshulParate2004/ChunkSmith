@echo off
echo ============================================
echo 🚀 ChunkSmith - Push APP Image (FAST!)
echo ============================================
echo.

docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running
    pause
    exit /b 1
)

set DOCKER_USERNAME=anshulnp

echo.
set /p VERSION_TAG="Enter version (or press Enter for 'latest'): "
echo.

docker login

cd Backend

echo 🔨 Building FAST app image...
docker build --build-arg DOCKER_USERNAME=%DOCKER_USERNAME% ^
    -t %DOCKER_USERNAME%/chunksmith-app:latest ^
    -f Dockerfile .

if errorlevel 1 (
    echo ❌ Build failed
    pause
    exit /b 1
)

if not "%VERSION_TAG%"=="" (
    docker tag %DOCKER_USERNAME%/chunksmith-app:latest %DOCKER_USERNAME%/chunksmith-app:%VERSION_TAG%
)

for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set DATE_TAG=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%

docker tag %DOCKER_USERNAME%/chunksmith-app:latest %DOCKER_USERNAME%/chunksmith-app:%DATE_TAG%

echo 📤 Pushing small APP image...
docker push %DOCKER_USERNAME%/chunksmith-app:latest

if not "%VERSION_TAG%"=="" (
    docker push %DOCKER_USERNAME%/chunksmith-app:%VERSION_TAG%
)
docker push %DOCKER_USERNAME%/chunksmith-app:%DATE_TAG%

echo.
echo ============================================
echo ✅ SUCCESS! Pushed app image!
echo ============================================
echo.
pause
