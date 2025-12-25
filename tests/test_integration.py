"""Integration tests for complete workflows.

This module tests end-to-end workflows combining multiple features.
"""

import pytest
from fastapi.testclient import TestClient

from app.models import Event, GlobalWishlist, Participant, User


@pytest.mark.asyncio
async def test_complete_wishlist_workflow(
    authenticated_client: TestClient, db_session, test_user: User
):
    """Test complete wishlist creation and sharing workflow."""
    # Create wishlist
    response = authenticated_client.post(
        "/wishlists/create",
        data={"title": "My Wishlist", "content": "1. Item 1\n2. Item 2"},
    )
    assert response.status_code == 302

    # Get wishlist from database
    from sqlalchemy import select

    result = await db_session.execute(
        select(GlobalWishlist).where(GlobalWishlist.user_id == test_user.id)
    )
    wishlist = result.scalar_one_or_none()
    assert wishlist is not None
    assert wishlist.title == "My Wishlist"

    # Access share link
    response = authenticated_client.get(f"/wishlists/share/{wishlist.share_uuid}")
    assert response.status_code == 200
    assert "My Wishlist" in response.text


@pytest.mark.asyncio
async def test_complete_event_workflow(
    authenticated_client: TestClient, db_session, test_user: User
):
    """Test complete event creation and joining workflow."""
    # Create event
    response = authenticated_client.post(
        "/events/create",
        data={
            "title": "Test Event",
            "description": "Test",
            "budget": "50",
            "target_count": "3",
        },
    )
    assert response.status_code == 302

    # Get event from database
    from sqlalchemy import select

    result = await db_session.execute(
        select(Event).where(Event.creator_id == test_user.id)
    )
    event = result.scalar_one_or_none()
    assert event is not None
    assert event.title == "Test Event"

    # View event detail
    response = authenticated_client.get(f"/events/{event.id}")
    assert response.status_code == 200
    assert "Test Event" in response.text
    assert event.code in response.text


@pytest.mark.asyncio
async def test_event_join_workflow(
    authenticated_client: TestClient, db_session, test_user: User
):
    """Test joining an event workflow."""
    from app.utils import generate_invite_code
    from sqlalchemy import select

    # Create event
    event = Event(
        code=generate_invite_code(),
        title="Join Test Event",
        budget=50.0,
        target_count=2,
        creator_id=test_user.id,
    )
    db_session.add(event)
    await db_session.commit()

    # Create wishlist for joining
    wishlist = GlobalWishlist(
        user_id=test_user.id,
        title="Join Wishlist",
        content="My wishlist items",
    )
    db_session.add(wishlist)
    await db_session.commit()

    # Join event
    response = authenticated_client.post(
        "/events/join",
        data={"code": event.code},
    )
    assert response.status_code == 200  # Should show wishlist selection

    # Confirm join with wishlist
    # Note: This would require getting the event_id from the response
    # For now, test the join confirmation endpoint directly
    response = authenticated_client.post(
        f"/events/{event.id}/join-confirm",
        data={"wishlist_id": str(wishlist.id)},
    )
    # Should redirect to event detail
    assert response.status_code == 302

    # Verify participant was created
    result = await db_session.execute(
        select(Participant).where(
            Participant.event_id == event.id, Participant.user_id == test_user.id
        )
    )
    participant = result.scalar_one_or_none()
    assert participant is not None
    assert participant.wishlist_text == wishlist.content

