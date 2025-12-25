#!/bin/bash
# Build script for Docker images

set -e

echo "🐳 Building Secret Santa Docker Image"
echo "======================================"

# Default to uv Dockerfile
DOCKERFILE="${1:-Dockerfile.uv}"
TAG="${2:-secret-santa:latest}"

echo "Using Dockerfile: $DOCKERFILE"
echo "Tag: $TAG"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Make sure to create .env before running the container."
    echo ""
fi

# Build the image
echo "Building image..."
# Check if --no-cache flag is provided as third argument
if [ "$3" = "--no-cache" ]; then
    echo "⚠️  Using --no-cache flag (slower but ensures fresh build)"
    docker build --no-cache -f "$DOCKERFILE" -t "$TAG" .
else
    echo "💡 Tip: Use './build-docker.sh $DOCKERFILE $TAG --no-cache' to force fresh build"
    docker build -f "$DOCKERFILE" -t "$TAG" .
fi

echo ""
echo "✅ Build complete!"
echo ""
echo "To run the container:"
echo "  docker run -d -p 8000:8000 --env-file .env -v santa_data:/app/data $TAG"
echo ""
echo "Or use docker-compose:"
echo "  docker-compose up -d"
