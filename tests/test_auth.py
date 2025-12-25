"""Tests for authentication functionality.

This module tests Google OAuth authentication flow and user management.
"""

import pytest
from fastapi.testclient import TestClient

from app.models import User


@pytest.mark.asyncio
async def test_login_page(client: TestClient):
    """Test login page loads correctly."""
    response = client.get("/login")
    assert response.status_code == 200
    assert "Sign in with Google" in response.text


@pytest.mark.asyncio
async def test_root_redirects_to_login_when_not_authenticated(client: TestClient):
    """Test root route redirects to login when not authenticated."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
async def test_logout(authenticated_client: TestClient):
    """Test logout functionality."""
    # Should redirect to login
    response = authenticated_client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"

    # Session should be cleared
    response = authenticated_client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302  # Should redirect to login


@pytest.mark.asyncio
async def test_user_creation(db_session, test_user: User):
    """Test user creation in database."""
    assert test_user.id is not None
    assert test_user.email == "test@example.com"
    assert test_user.google_id == "test_google_id_123"


@pytest.mark.asyncio
async def test_dashboard_requires_auth(client: TestClient):
    """Test dashboard requires authentication."""
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
async def test_dashboard_accessible_when_authenticated(authenticated_client: TestClient):
    """Test dashboard is accessible when authenticated."""
    response = authenticated_client.get("/dashboard")
    assert response.status_code == 200
    assert "Welcome" in response.text

