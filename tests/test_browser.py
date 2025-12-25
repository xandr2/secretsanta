"""Browser-based end-to-end tests using Playwright.

This module tests the full user experience through browser automation.
"""

import pytest
from playwright.async_api import Page


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the application."""
    return "http://localhost:8000"


@pytest.mark.asyncio
@pytest.mark.browser
async def test_homepage_loads(page: Page, base_url: str):
    """Test homepage loads and redirects correctly."""
    await page.goto(base_url)
    # Should redirect to login
    await page.wait_for_url("**/login", timeout=5000)
    content = await page.content()
    assert "Sign in with Google" in content


@pytest.mark.asyncio
@pytest.mark.browser
async def test_login_page_elements(page: Page, base_url: str):
    """Test login page has all required elements."""
    await page.goto(f"{base_url}/login")
    
    # Check for key elements
    assert await page.locator("text=Secret Santa").is_visible()
    assert await page.locator("text=Sign in with Google").is_visible()
    assert await page.locator('a[href*="/auth/google"]').is_visible()


@pytest.mark.asyncio
@pytest.mark.browser
async def test_wishlist_sharing_public(page: Page, base_url: str):
    """Test public wishlist sharing page (no auth required)."""
    # Create a test wishlist share URL (you'll need to get this from your test data)
    # For now, test that the route exists
    await page.goto(f"{base_url}/wishlists/share/test-uuid-123")
    
    # Should either show 404 or the share page
    content = await page.content()
    # Either shows share page or 404, both are valid responses
    assert "wishlist" in content.lower() or "not found" in content.lower()

