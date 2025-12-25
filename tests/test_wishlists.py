"""Tests for wishlist functionality.

This module tests CRUD operations for wishlists and sharing.
"""

import pytest
from fastapi.testclient import TestClient

from app.models import GlobalWishlist, User


@pytest.mark.asyncio
async def test_create_wishlist(authenticated_client: TestClient, test_user: User):
    """Test creating a wishlist."""
    response = authenticated_client.get("/wishlists/create")
    assert response.status_code == 200

    # Create wishlist
    response = authenticated_client.post(
        "/wishlists/create",
        data={"title": "Test Wishlist", "content": "1. Item one\n2. Item two"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/wishlists"


@pytest.mark.asyncio
async def test_list_wishlists(authenticated_client: TestClient, db_session, test_user: User):
    """Test listing wishlists."""
    # Create a test wishlist
    wishlist = GlobalWishlist(
        user_id=test_user.id,
        title="Test Wishlist",
        content="1. Item one\n2. Item two",
    )
    db_session.add(wishlist)
    await db_session.commit()

    response = authenticated_client.get("/wishlists")
    assert response.status_code == 200
    assert "Test Wishlist" in response.text


@pytest.mark.asyncio
async def test_edit_wishlist(authenticated_client: TestClient, db_session, test_user: User):
    """Test editing a wishlist."""
    # Create a test wishlist
    wishlist = GlobalWishlist(
        user_id=test_user.id,
        title="Original Title",
        content="Original content",
    )
    db_session.add(wishlist)
    await db_session.commit()

    # Edit wishlist
    response = authenticated_client.post(
        f"/wishlists/{wishlist.id}/edit",
        data={"title": "Updated Title", "content": "Updated content"},
        follow_redirects=False,
    )
    assert response.status_code == 302

    # Verify update
    await db_session.refresh(wishlist)
    assert wishlist.title == "Updated Title"
    assert wishlist.content == "Updated content"


@pytest.mark.asyncio
async def test_delete_wishlist(authenticated_client: TestClient, db_session, test_user: User):
    """Test deleting a wishlist."""
    # Create a test wishlist
    wishlist = GlobalWishlist(
        user_id=test_user.id,
        title="To Delete",
        content="Content",
    )
    db_session.add(wishlist)
    await db_session.commit()
    wishlist_id = wishlist.id

    # Delete wishlist
    response = authenticated_client.post(
        f"/wishlists/{wishlist_id}/delete",
        follow_redirects=False,
    )
    assert response.status_code == 302

    # Verify deletion
    from sqlalchemy import select

    result = await db_session.execute(
        select(GlobalWishlist).where(GlobalWishlist.id == wishlist_id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_share_wishlist_public(client: TestClient, db_session, test_user: User):
    """Test public wishlist sharing (no auth required)."""
    # Create a test wishlist
    wishlist = GlobalWishlist(
        user_id=test_user.id,
        title="Shared Wishlist",
        content="1. Item one\n2. Item two",
    )
    db_session.add(wishlist)
    await db_session.commit()

    # Access share link without authentication
    response = client.get(f"/wishlists/share/{wishlist.share_uuid}")
    assert response.status_code == 200
    assert "Shared Wishlist" in response.text
    assert "Shared by:" in response.text
    assert test_user.name in response.text


@pytest.mark.asyncio
async def test_wishlist_formatting(authenticated_client: TestClient, db_session, test_user: User):
    """Test wishlist content formatting for numbered lists."""
    from app.routers.wishlists import format_wishlist_content

    # Test numbered list
    content = "1. tetris\n2. smt"
    formatted = format_wishlist_content(content)
    assert formatted["is_list"] is True
    assert formatted["items"] == ["tetris", "smt"]

    # Test plain text
    content = "Just some text"
    formatted = format_wishlist_content(content)
    assert formatted["is_list"] is False
    assert formatted["items"] == [content]

