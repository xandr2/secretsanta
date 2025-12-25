# Docker Build Troubleshooting Guide

## Problem: Old Code in Docker Image

If you're seeing old code in your Docker image even after rebuilding, this is usually caused by **Docker layer caching**.

## Quick Fix

### Option 1: Force Fresh Build (Recommended)
```bash
# Build without cache
./build-docker.sh Dockerfile.uv secret-santa:latest --no-cache

# Or directly with docker
docker build --no-cache -f Dockerfile.uv -t secret-santa:latest .
```

### Option 2: Use Unique Tags
Instead of always using `latest`, use timestamps or version numbers:
```bash
./build-docker.sh Dockerfile.uv secret-santa:$(date +%Y%m%d-%H%M%S)
```

### Option 3: Rebuild Before Push
```bash
# Rebuild and push
./push-docker.sh latest --rebuild
```

## Diagnosis Steps

### 1. Run the Diagnostic Script
```bash
./diagnose-docker.sh
```

### 2. Verify What's in Your Image
```bash
# Check if your code is actually in the image
docker run --rm secret-santa:latest cat app/main.py | head -20

# Or inspect the file modification time inside container
docker run --rm secret-santa:latest ls -la app/main.py
```

### 3. Check Build Context
```bash
# See what Docker will copy (dry run)
docker build --dry-run -f Dockerfile.uv . 2>&1 | grep -i copy
```

### 4. Verify Local Code Changes
```bash
# Check when your files were last modified
ls -la app/*.py

# Compare with what's in the image
docker run --rm secret-santa:latest ls -la app/*.py
```

## Common Causes

1. **Docker Layer Caching**: Docker reuses cached layers when it thinks nothing changed
2. **Stale Image Tag**: Using `latest` tag can cause confusion - you might be running an old image
3. **Build Context Issues**: Files might be excluded by `.dockerignore`
4. **Container Not Restarted**: Old container still running with old image

## Solutions

### Solution 1: Always Use --no-cache for Production Builds
Update your CI/CD or build process to always use `--no-cache`:
```bash
docker build --no-cache -f Dockerfile.uv -t secret-santa:latest .
```

### Solution 2: Use Build Args to Invalidate Cache
Add a build argument that changes with each build:
```dockerfile
ARG BUILD_DATE=unknown
ENV BUILD_DATE=${BUILD_DATE}
```

Then build with:
```bash
docker build --build-arg BUILD_DATE=$(date +%s) -f Dockerfile.uv -t secret-santa:latest .
```

### Solution 3: Check Running Containers
Make sure you're not running an old container:
```bash
# Stop and remove old containers
docker ps -a | grep secret-santa
docker stop secret_santa_web
docker rm secret_santa_web

# Rebuild and restart
docker-compose up -d --build
```

### Solution 4: Verify Image Pull
If pulling from registry, make sure you're pulling the latest:
```bash
# Remove old image
docker rmi xandr2/secret-santa:latest

# Pull fresh
docker pull xandr2/secret-santa:latest
```

## Updated Build Scripts

The build scripts have been updated to support `--no-cache`:

```bash
# Build with cache (faster, but may use stale layers)
./build-docker.sh Dockerfile.uv secret-santa:latest

# Build without cache (slower, but guaranteed fresh)
./build-docker.sh Dockerfile.uv secret-santa:latest --no-cache

# Push with rebuild
./push-docker.sh latest --rebuild
```

## Best Practices

1. **Use version tags** instead of always using `latest`
2. **Use --no-cache** for production builds
3. **Verify image contents** before pushing
4. **Restart containers** after pulling new images
5. **Check build logs** for any warnings about cached layers

## Example Workflow

```bash
# 1. Make code changes
# ... edit files ...

# 2. Build fresh image
./build-docker.sh Dockerfile.uv secret-santa:latest --no-cache

# 3. Test locally
docker run --rm -p 8000:8000 secret-santa:latest

# 4. Verify code is updated
docker run --rm secret-santa:latest cat app/main.py | grep "your new code"

# 5. Push to registry
./push-docker.sh latest --rebuild

# 6. On server, pull and restart
docker pull xandr2/secret-santa:latest
docker-compose down
docker-compose up -d
```

