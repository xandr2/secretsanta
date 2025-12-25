#!/usr/bin/env python3
"""Run browser tests with a live server.

This script starts the FastAPI server and runs browser tests against it.
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

import uvicorn


def start_server():
    """Start the FastAPI server in a subprocess."""
    # Set test environment
    env = os.environ.copy()
    env["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test.db"
    env["SECRET_KEY"] = "test_secret_key_for_testing_only"
    
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8001"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return process


def wait_for_server(url: str = "http://localhost:8001", timeout: int = 30):
    """Wait for server to be ready."""
    import httpx
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = httpx.get(url, timeout=1)
            if response.status_code in [200, 302, 404]:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


if __name__ == "__main__":
    import os
    
    print("🚀 Starting test server...")
    server_process = start_server()
    
    try:
        print("⏳ Waiting for server to start...")
        if wait_for_server():
            print("✅ Server is ready!")
            print("🌐 Running browser tests...")
            
            # Run pytest with browser tests
            result = subprocess.run(
                ["uv", "run", "pytest", "tests/test_browser_e2e.py", "-v", "--browser", "-m", "browser"],
                env={**os.environ, "TEST_BASE_URL": "http://localhost:8001"},
            )
            sys.exit(result.returncode)
        else:
            print("❌ Server failed to start")
            sys.exit(1)
    finally:
        print("🛑 Stopping server...")
        server_process.terminate()
        server_process.wait()

