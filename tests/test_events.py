"""Tests for event functionality.

This module tests event creation, joining, and matching logic.
"""

import pytest
from fastapi.testclient import TestClient

from app.models import Event, EventStatus, Participant, User
from app.utils import generate_invite_code


@pytest.mark.asyncio
async def test_create_event(authenticated_client: TestClient, test_user: User):
    """Test creating an event."""
    response = authenticated_client.get("/events/create")
    assert response.status_code == 200

    # Create event
    response = authenticated_client.post(
        "/events/create",
        data={
            "title": "Christmas 2024",
            "description": "Secret Santa event",
            "budget": "50.00",
            "target_count": "5",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/events/" in response.headers["location"]


@pytest.mark.asyncio
async def test_event_detail(authenticated_client: TestClient, db_session, test_user: User):
    """Test viewing event details."""
    from app.utils import generate_invite_code

    # Create test event
    event = Event(
        code=generate_invite_code(),
        title="Test Event",
        description="Test description",
        budget=50.0,
        target_count=3,
        creator_id=test_user.id,
    )
    db_session.add(event)
    await db_session.commit()

    response = authenticated_client.get(f"/events/{event.id}")
    assert response.status_code == 200
    assert "Test Event" in response.text
    assert event.code in response.text


@pytest.mark.asyncio
async def test_join_event_form(authenticated_client: TestClient):
    """Test join event form."""
    response = authenticated_client.get("/events/join")
    assert response.status_code == 200
    assert "Event Code" in response.text


@pytest.mark.asyncio
async def test_join_event_invalid_code(authenticated_client: TestClient):
    """Test joining event with invalid code."""
    response = authenticated_client.post(
        "/events/join",
        data={"code": "INVALID"},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Invalid event code" in response.text or "error" in response.text.lower()


@pytest.mark.asyncio
async def test_matching_logic(db_session, test_user: User):
    """Test derangement shuffle matching logic."""
    from app.services.matching import check_and_trigger_matching, derangement_shuffle

    # Test derangement shuffle
    items = [1, 2, 3, 4]
    shuffled = derangement_shuffle(items)
    assert len(shuffled) == len(items)
    assert all(shuffled[i] != items[i] for i in range(len(items)))

    # Create event with target count
    event = Event(
        code="TEST-01",
        title="Test Match",
        budget=50.0,
        target_count=3,
        creator_id=test_user.id,
    )
    db_session.add(event)
    await db_session.commit()

    # Create additional test users
    user2 = User(
        google_id="test2",
        email="test2@example.com",
        name="Test User 2",
    )
    user3 = User(
        google_id="test3",
        email="test3@example.com",
        name="Test User 3",
    )
    db_session.add(user2)
    db_session.add(user3)
    await db_session.commit()

    # Create participants
    p1 = Participant(
        user_id=test_user.id,
        event_id=event.id,
        wishlist_text="Wishlist 1",
    )
    p2 = Participant(
        user_id=user2.id,
        event_id=event.id,
        wishlist_text="Wishlist 2",
    )
    p3 = Participant(
        user_id=user3.id,
        event_id=event.id,
        wishlist_text="Wishlist 3",
    )
    db_session.add(p1)
    db_session.add(p2)
    db_session.add(p3)
    await db_session.commit()

    # Trigger matching
    result = await check_and_trigger_matching(event.id, db_session)
    assert result is True

    # Verify event is matched
    await db_session.refresh(event)
    assert event.status == EventStatus.MATCHED

    # Verify all participants have santa_for_user_id
    await db_session.refresh(p1)
    await db_session.refresh(p2)
    await db_session.refresh(p3)
    assert p1.santa_for_user_id is not None
    assert p2.santa_for_user_id is not None
    assert p3.santa_for_user_id is not None

    # Verify no one is their own santa
    assert p1.santa_for_user_id != p1.user_id
    assert p2.santa_for_user_id != p2.user_id
    assert p3.santa_for_user_id != p3.user_id

