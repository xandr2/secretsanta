#!/bin/bash
# Diagnostic script to check Docker build issues

set -e

echo "🔍 Docker Build Diagnostics"
echo "=========================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running"
    exit 1
fi

echo "1. Checking Docker build context..."
echo "   Current directory: $(pwd)"
echo "   Files that will be copied (excluding .dockerignore):"
echo ""
docker build --dry-run -f Dockerfile.uv . 2>&1 | grep -i "copy\|add" || echo "   (Run 'docker build --dry-run -f Dockerfile.uv .' for details)"
echo ""

echo "2. Checking for cached layers..."
echo "   Recent images:"
docker images | head -5
echo ""

echo "3. Checking if code files exist locally..."
if [ -f "app/main.py" ]; then
    echo "   ✅ app/main.py exists"
    echo "   Last modified: $(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" app/main.py 2>/dev/null || stat -c "%y" app/main.py 2>/dev/null | cut -d' ' -f1-2)"
else
    echo "   ❌ app/main.py NOT FOUND"
fi
echo ""

echo "4. Testing build with --no-cache (dry run)..."
echo "   This will show what Docker would build:"
echo "   Run: docker build --no-cache -f Dockerfile.uv -t secret-santa:test ."
echo ""

echo "5. Checking for stale containers..."
echo "   Running containers:"
docker ps --filter "name=secret_santa" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
echo ""

echo "6. Recommendations:"
echo "   - Use --no-cache flag to force fresh build:"
echo "     docker build --no-cache -f Dockerfile.uv -t secret-santa:latest ."
echo ""
echo "   - Or use a unique tag instead of 'latest':"
echo "     docker build -f Dockerfile.uv -t secret-santa:$(date +%Y%m%d-%H%M%S) ."
echo ""
echo "   - Check what's actually in the image:"
echo "     docker run --rm secret-santa:latest cat app/main.py | head -20"
echo ""

