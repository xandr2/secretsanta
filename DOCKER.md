# Docker Deployment Guide

This guide explains how to build and run the Secret Santa application using Docker.

## Prerequisites

- Docker installed and running
- Docker Compose (optional, but recommended)
- `.env` file configured (see [README.md](README.md))

## Quick Start

### Using Docker Compose (Recommended)

**Production:**
```bash
docker-compose up -d
```

**Development (with hot-reload):**
```bash
docker-compose -f docker-compose.dev.yml up
```

### Using Docker Directly

**Build the image:**
```bash
# Using uv (faster)
docker build -f Dockerfile.uv -t secret-santa:latest .

# Or using traditional pip
docker build -f Dockerfile -t secret-santa:latest .
```

**Run the container:**
```bash
docker run -d \
  --name secret_santa \
  -p 8000:8000 \
  --env-file .env \
  -v secret_santa_data:/app/data \
  secret-santa:latest
```

## Dockerfiles

### Dockerfile (Traditional)
- Uses `pip` and `requirements.txt`
- Standard Python approach
- Good for compatibility

### Dockerfile.uv (Recommended)
- Uses `uv` for faster dependency resolution
- Faster builds and smaller images
- Recommended for production

## Environment Variables

The container reads environment variables from:
1. `.env` file (via `--env-file` or `env_file` in docker-compose)
2. Environment variables passed to the container

**Required variables:**
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `SECRET_KEY`

**Optional variables:**
- `DATABASE_URL` (defaults to SQLite in `/app/data`)
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_BOT_USERNAME`

## Volumes

The application uses a Docker volume for data persistence:
- `santa_data`: Stores the SQLite database and other persistent data

In production, you may want to use a named volume or bind mount:
```yaml
volumes:
  - ./data:/app/data  # Bind mount (for easy access)
  # OR
  - santa_data:/app/data  # Named volume (recommended)
```

## Health Checks

Both Dockerfiles include health checks that verify the application is responding:
- Checks `/login` endpoint every 30 seconds
- Container marked unhealthy if checks fail 3 times

## Building for Production

**Optimized build:**
```bash
docker build \
  --target production \
  -f Dockerfile.uv \
  -t secret-santa:latest \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  .
```

## Troubleshooting

### Container won't start
1. Check logs: `docker logs secret_santa_web`
2. Verify `.env` file exists and has required variables
3. Check port 8000 is not already in use

### Database issues
1. Ensure volume is mounted correctly
2. Check file permissions on data directory
3. Verify `DATABASE_URL` points to `/app/data/` inside container

### Bot not working
1. Verify `TELEGRAM_BOT_TOKEN` is set correctly
2. Check bot logs in container output
3. Ensure bot username is configured or auto-detected

### View logs
```bash
# Docker Compose
docker-compose logs -f

# Docker directly
docker logs -f secret_santa_web
```

## Development Workflow

For development with hot-reload:
```bash
docker-compose -f docker-compose.dev.yml up
```

This mounts the `./app` directory so code changes are reflected immediately.

## Production Deployment

### Building and Pushing to Docker Hub

1. **Build and tag the image:**
   ```bash
   docker build -f Dockerfile.uv -t xandr2/secret-santa:latest .
   ```

2. **Login to Docker Hub:**
   ```bash
   docker login -u xandr2
   ```

3. **Push the image:**
   ```bash
   docker push xandr2/secret-santa:latest
   ```

   Or use the helper script:
   ```bash
   ./push-docker.sh
   ```

4. **Deploy using Docker Hub image:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Using Custom Registry

1. **Build the image:**
   ```bash
   docker build -f Dockerfile.uv -t secret-santa:latest .
   ```

2. **Tag for your registry:**
   ```bash
   docker tag secret-santa:latest your-registry/secret-santa:latest
   ```

3. **Push to registry:**
   ```bash
   docker push your-registry/secret-santa:latest
   ```

4. **Deploy:**
   ```bash
   docker-compose up -d
   ```

## Security Notes

- Never commit `.env` file to version control
- Use Docker secrets or environment variables for sensitive data
- Keep base images updated
- Regularly update dependencies

## Multi-stage Builds (Future Enhancement)

For even smaller images, consider multi-stage builds:
```dockerfile
FROM python:3.11-slim as builder
# Install dependencies
FROM python:3.11-slim
# Copy only runtime dependencies
```

