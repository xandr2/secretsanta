#!/bin/bash
# Test runner script for Secret Santa application

set -e

echo "🧪 Running Secret Santa Tests"
echo "================================"

# Check if running browser tests
if [ "$1" == "--browser" ] || [ "$1" == "-b" ]; then
    echo "🌐 Running browser tests..."
    uv run pytest tests/ -v --browser -m browser
elif [ "$1" == "--all" ] || [ "$1" == "-a" ]; then
    echo "📦 Running all tests..."
    uv run pytest tests/ -v
elif [ "$1" == "--unit" ] || [ "$1" == "-u" ]; then
    echo "🔬 Running unit tests only..."
    uv run pytest tests/ -v -m "not browser"
else
    echo "📋 Running unit tests (use --browser for browser tests)..."
    uv run pytest tests/ -v -m "not browser"
fi

echo ""
echo "✅ Tests completed!"

