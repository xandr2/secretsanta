# Testing Guide

This document describes how to run tests for the Secret Santa application.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py           # Shared fixtures
├── test_auth.py          # Authentication tests
├── test_wishlists.py     # Wishlist CRUD tests
├── test_events.py        # Event management tests
├── test_utils.py         # Utility function tests
├── test_integration.py   # End-to-end workflow tests
└── test_browser_e2e.py   # Browser-based UI tests
```

## Running Tests

### Unit Tests (Fast, No Browser Required)

```bash
# Run all unit tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_auth.py -v

# Run specific test
uv run pytest tests/test_auth.py::test_login_page -v

# Run with coverage
uv run pytest tests/ --cov=app --cov-report=html
```

### Browser Tests (Requires Running Server)

Browser tests use Playwright to test the UI in a real browser.

**Option 1: Manual Server Start**

1. Start the server in one terminal:
   ```bash
   uv run uvicorn app.main:app --reload --port 8001
   ```

2. Run browser tests in another terminal:
   ```bash
   TEST_BASE_URL=http://localhost:8001 uv run pytest tests/test_browser_e2e.py -v --browser -m browser
   ```

**Option 2: Automated (Recommended)**

Use the test runner script:
```bash
./run_tests.sh --browser
```

Or use pytest-playwright directly:
```bash
uv run pytest tests/test_browser_e2e.py -v --browser -m browser
```

## Test Categories

### Unit Tests
- Test individual functions and components
- Fast execution
- No external dependencies
- Examples: `test_utils.py`, `test_auth.py`

### Integration Tests
- Test workflows combining multiple features
- May use test database
- Examples: `test_integration.py`

### Browser Tests
- Test full UI flows
- Require running server
- Use Playwright for automation
- Examples: `test_browser_e2e.py`

## Writing New Tests

### Example Unit Test

```python
import pytest
from fastapi.testclient import TestClient

def test_my_feature(client: TestClient):
    """Test my feature."""
    response = client.get("/my-route")
    assert response.status_code == 200
```

### Example Browser Test

```python
import pytest
from playwright.async_api import Page

@pytest.mark.asyncio
@pytest.mark.browser
async def test_my_ui_flow(page: Page, base_url: str):
    """Test UI flow."""
    await page.goto(f"{base_url}/my-page")
    await expect(page.locator("text=Expected Text")).toBeVisible()
```

## Test Fixtures

Available fixtures (from `conftest.py`):

- `db_session`: Async database session (test database)
- `client`: FastAPI test client
- `test_user`: Test user instance
- `authenticated_client`: Authenticated test client
- `base_url`: Base URL for browser tests

## Continuous Integration

To run tests in CI:

```bash
# Install dependencies
uv sync --dev

# Install Playwright browsers
uv run playwright install chromium

# Run all tests
uv run pytest tests/ -v

# Run browser tests (if server available)
TEST_BASE_URL=http://localhost:8000 uv run pytest tests/test_browser_e2e.py --browser -m browser
```

## Troubleshooting

### Tests fail with database errors
- Make sure test database is properly isolated
- Check that `db_session` fixture is being used

### Browser tests fail
- Ensure server is running on the expected port
- Check `TEST_BASE_URL` environment variable
- Verify Playwright browsers are installed: `uv run playwright install chromium`

### Import errors
- Make sure you're running tests from project root
- Verify `app` package is installed: `uv sync`

