# ChunkSmith Setup Guide

## Prerequisites

- **Docker Desktop** is required to run ChunkSmith
  - Download from: https://www.docker.com/products/docker-desktop
  - Install and ensure Docker Desktop is running before proceeding

## Installation Steps

### 1. Pull the Docker Image

```bash
docker pull anshulnp/chunksmith-backend:latest
```

### 2. Create Environment File

Create a `.env` file with the following structure:

```env
# ==========================================
# Google API Keys
# ==========================================
GOOGLE_API_KEY=your_primary_google_api_key

# Multiple Google API Keys (Optional - for rate limit rotation)
GOOGLE_API_KEY_1=your_google_api_key_1
GOOGLE_API_KEY_2=your_google_api_key_2
GOOGLE_API_KEY_3=your_google_api_key_3
GOOGLE_API_KEY_4=your_google_api_key_4
GOOGLE_API_KEY_5=your_google_api_key_5
GOOGLE_API_KEY_6=your_google_api_key_6
GOOGLE_API_KEY_7=your_google_api_key_7
GOOGLE_API_KEY_8=your_google_api_key_8
GOOGLE_API_KEY_9=your_google_api_key_9
GOOGLE_API_KEY_10=your_google_api_key_10

# ==========================================
# Other API Keys
# ==========================================
GROQ_API_KEY=your_groq_api_key

# ==========================================
# Application Settings
# ==========================================
APP_ENV=development
DEBUG=true
API_TITLE=ChunkSmith Backend
API_VERSION=1.0.0

# ==========================================
# Server Settings
# ==========================================
HOST=0.0.0.0
PORT=8000

# ==========================================
# CORS Settings
# ==========================================
CORS_ORIGINS=*

# ==========================================
# File Upload Settings
# ==========================================
MAX_UPLOAD_SIZE=50000000  # 50MB in bytes
ALLOWED_EXTENSIONS=[".pdf"]

# ==========================================
# Database/Storage
# ==========================================
DATA_PATH=./data
CHROMA_DB_PATH=./data/chroma_db
```

**Note:** 
- Replace `your_primary_google_api_key`, `your_groq_api_key`, etc. with your actual API keys
- The multiple Google API keys (GOOGLE_API_KEY_1 to GOOGLE_API_KEY_10) are optional and used for rate limit rotation
- You can get Google API keys from: https://makersuite.google.com/app/apikey
- You can get Groq API keys from: https://console.groq.com/

### 3. Run the Container

```bash
docker run -d -p 8000:8000 --name chunksmith --env-file <path_to_your_env_file> anshulnp/chunksmith-backend:latest
```

Replace `<path_to_your_env_file>` with the actual path to your `.env` file.

**Example:**
```bash
docker run -d -p 8000:8000 --name chunksmith --env-file ./config/.env anshulnp/chunksmith-backend:latest
```

## Container Management

### Stop the Container
```bash
docker stop chunksmith
```

### Start the Container
```bash
docker start chunksmith
```

### Restart the Container
```bash
docker restart chunksmith
```

### View Container Logs
```bash
docker logs chunksmith
```

### Remove the Container
```bash
docker rm chunksmith
```

**Note:** You must stop the container before removing it, or use the force flag:
```bash
docker rm -f chunksmith
```

## Accessing ChunkSmith

### Backend API
Once the container is running, the backend API will be accessible at:
```
http://localhost:8000
```

You can verify it's running by visiting:
```
http://localhost:8000/docs
```
This will show the API documentation (if available).

### Frontend Application
The ChunkSmith frontend is hosted and running at:
```
https://multi-modul-rag.vercel.app/
```

Visit the frontend URL and configure your API endpoint to connect to your local backend:
- In the API configuration section of the frontend
- Set the API URL to: `http://localhost:8000`

## Troubleshooting

### Container won't start
- Ensure Docker Desktop is running
- Check if port 8000 is already in use: `netstat -ano | findstr :8000`
- Verify your `.env` file path is correct

### Can't access localhost:8000
- Verify the container is running: `docker ps`
- Check container logs for errors: `docker logs chunksmith`
- Ensure no firewall is blocking port 8000

### Frontend can't connect to backend
- Verify backend is accessible at `http://localhost:8000`
- Check browser console for CORS errors
- Ensure API configuration in frontend is set correctly

## Additional Commands

### View Running Containers
```bash
docker ps
```

### View All Containers (including stopped)
```bash
docker ps -a
```

### Execute Commands Inside Container
```bash
docker exec -it chunksmith /bin/bash
```

### Update to Latest Version
```bash
docker pull anshulnp/chunksmith-backend:latest
docker stop chunksmith
docker rm chunksmith
docker run -d -p 8000:8000 --name chunksmith --env-file <env_path> anshulnp/chunksmith-backend:latest
```

## Support

For issues or questions, please refer to the project documentation or contact the development team.
