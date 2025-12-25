#!/bin/bash
# Push Docker image to Docker Hub

set -e

DOCKER_USERNAME="${DOCKER_USERNAME:-xandr2}"
IMAGE_NAME="${IMAGE_NAME:-secret-santa}"
TAG="${1:-latest}"
FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"

echo "🐳 Pushing Secret Santa Docker Image to Docker Hub"
echo "=================================================="
echo "Repository: ${FULL_IMAGE_NAME}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    exit 1
fi

# Check if image exists locally or if --rebuild flag is provided
REBUILD="${2:-}"
if [ "$REBUILD" = "--rebuild" ] || ! docker images | grep -q "${DOCKER_USERNAME}/${IMAGE_NAME}.*${TAG}"; then
    if [ "$REBUILD" = "--rebuild" ]; then
        echo "🔄 Rebuilding image (--rebuild flag detected)..."
        docker build --no-cache -f Dockerfile.uv -t "${FULL_IMAGE_NAME}" .
    else
        echo "⚠️  Image ${FULL_IMAGE_NAME} not found locally"
        echo "Building image first..."
        docker build -f Dockerfile.uv -t "${FULL_IMAGE_NAME}" .
    fi
    echo ""
fi

# Login to Docker Hub (if not already logged in)
echo "Checking Docker Hub login status..."
if ! docker info | grep -q "Username"; then
    echo "Please login to Docker Hub:"
    docker login -u "${DOCKER_USERNAME}"
    echo ""
fi

# Push the image
echo "Pushing ${FULL_IMAGE_NAME} to Docker Hub..."
docker push "${FULL_IMAGE_NAME}"

echo ""
echo "✅ Successfully pushed ${FULL_IMAGE_NAME}"
echo ""
echo "You can now pull it with:"
echo "  docker pull ${FULL_IMAGE_NAME}"
echo ""
echo "Or use it in docker-compose:"
echo "  image: ${FULL_IMAGE_NAME}"

