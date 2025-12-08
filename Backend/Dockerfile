ARG DOCKER_USERNAME=anshulnp
FROM ${DOCKER_USERNAME}/chunksmith-backend:latest

WORKDIR /app

# Copy ONLY the code in the current Backend folder
COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
