"""Matching service for Secret Santa events.

This module handles the derangement shuffle algorithm to match participants
in Secret Santa events, ensuring no one is matched with themselves.
"""

import random
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event, EventStatus, Participant, User


def derangement_shuffle(items: List[int]) -> List[int]:
    """Perform derangement shuffle ensuring no element maps to itself.

    Args:
        items: List of IDs to shuffle

    Returns:
        List[int]: Shuffled list where no element is in its original position

    Example:
        >>> items = [1, 2, 3, 4]
        >>> result = derangement_shuffle(items)
        >>> assert result[0] != items[0]  # No element matches original position
    """
    if len(items) < 2:
        return items.copy()

    result = items.copy()
    max_attempts = 100

    for attempt in range(max_attempts):
        random.shuffle(result)
        # Check if derangement is valid (no element in original position)
        if all(result[i] != items[i] for i in range(len(items))):
            return result

    # Fallback: if we can't find a perfect derangement, try swapping
    result = items.copy()
    for i in range(len(result) - 1):
        j = random.randint(i + 1, len(result) - 1)
        result[i], result[j] = result[j], result[i]

    return result


async def check_and_trigger_matching(
    event_id: int, session: AsyncSession
) -> bool:
    """Check if event should be matched and trigger matching if conditions are met.

    Conditions:
        - Participant count equals target_count
        - All participants have non-empty wishlists
        - Event status is OPEN

    Args:
        event_id: Event ID to check
        session: Database session

    Returns:
        bool: True if matching was triggered, False otherwise
    """
    # Get event
    result = await session.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event or event.status != EventStatus.OPEN:
        return False

    # Get all participants
    participants_result = await session.execute(
        select(Participant).where(Participant.event_id == event_id)
    )
    participants = list(participants_result.scalars().all())

    # Check conditions
    if len(participants) != event.target_count:
        return False

    # Check all participants have non-empty wishlists
    if any(not p.wishlist_text.strip() for p in participants):
        return False

    # Perform derangement shuffle
    user_ids = [p.user_id for p in participants]
    shuffled_ids = derangement_shuffle(user_ids)

    # Create mapping
    matching_map = dict(zip(user_ids, shuffled_ids))

    # Update participants with santa_for_user_id
    for participant in participants:
        participant.santa_for_user_id = matching_map[participant.user_id]
        session.add(participant)

    # Update event status
    event.status = EventStatus.MATCHED
    session.add(event)

    await session.commit()

    # Trigger notifications (will be handled by bot)
    # Import here to avoid circular dependency
    try:
        from app.bot import send_match_notifications
        await send_match_notifications(event_id, session)
    except Exception as e:
        # Log error but don't fail the matching
        print(f"Error sending notifications: {e}")

    return True

