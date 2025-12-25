#!/bin/bash
# Browser test runner - starts server and runs browser tests

set -e

PORT=${TEST_PORT:-8001}
BASE_URL="http://localhost:${PORT}"

echo "🚀 Starting test server on port ${PORT}..."

# Start server in background
uv run uvicorn app.main:app --port ${PORT} --log-level warning > /tmp/test_server.log 2>&1 &
SERVER_PID=$!

# Wait for server to be ready
echo "⏳ Waiting for server to start..."
for i in {1..30}; do
    if curl -s "${BASE_URL}/login" > /dev/null 2>&1; then
        echo "✅ Server is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Server failed to start"
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Run browser tests
echo "🌐 Running browser tests..."
TEST_BASE_URL="${BASE_URL}" uv run pytest tests/test_browser_e2e.py -v --browser -m browser || TEST_EXIT=$?

# Cleanup
echo "🛑 Stopping server..."
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

exit ${TEST_EXIT:-0}

