"""Routes for Event management.

This module handles creating events, joining events, and viewing event details.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Event, EventStatus, GlobalWishlist, Participant, User
from app.utils import generate_invite_code
from app.utils_templates import get_template_context

router = APIRouter(prefix="/events", tags=["events"])
templates = Jinja2Templates(directory="templates")


async def get_current_user(
    request: Request, session: AsyncSession = Depends(get_session)
):
    """Get current authenticated user from session."""
    from sqlalchemy import select

    user_id = request.session.get("user_id")
    if not user_id:
        return None

    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


@router.get("/create", response_class=HTMLResponse)
async def create_event_form(
    request: Request, user: Optional[User] = Depends(get_current_user)
):
    """Show create event form.

    Args:
        request: FastAPI request object
        user: Current authenticated user

    Returns:
        HTMLResponse: Create event form or redirect to login
    """
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        "events/create.html", get_template_context(request, user=user)
    )


@router.post("/create", response_class=HTMLResponse)
async def create_event(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    budget: float = Form(...),
    target_count: int = Form(...),
    user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new event.

    Args:
        request: FastAPI request object
        title: Event title
        description: Event description
        budget: Budget limit
        target_count: Target number of participants
        user: Current authenticated user
        session: Database session

    Returns:
        RedirectResponse: Redirect to event detail page
    """
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Generate unique invite code
    code = generate_invite_code()
    # Ensure code is unique
    while True:
        result = await session.execute(select(Event).where(Event.code == code))
        if not result.scalar_one_or_none():
            break
        code = generate_invite_code()

    event = Event(
        code=code,
        title=title,
        description=description,
        budget=budget,
        target_count=target_count,
        creator_id=user.id,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)

    return RedirectResponse(url=f"/events/{event.id}", status_code=302)


@router.get("/join", response_class=HTMLResponse)
async def join_event_form(
    request: Request,
    code: Optional[str] = None,
    user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Show join event form.

    Args:
        request: FastAPI request object
        code: Optional event code from query parameter
        user: Current authenticated user
        session: Database session

    Returns:
        HTMLResponse: Join event form or redirect to login
    """
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # If code is provided, check if event exists and is matched
    if code:
        result = await session.execute(select(Event).where(Event.code == code.upper()))
        event = result.scalar_one_or_none()
        
        if event and event.status == EventStatus.MATCHED:
            # Check if user is already a participant
            participant_result = await session.execute(
                select(Participant).where(
                    Participant.event_id == event.id, Participant.user_id == user.id
                )
            )
            participant = participant_result.scalar_one_or_none()
            if participant:
                # User is already a participant, redirect to event page to show their match
                return RedirectResponse(url=f"/events/{event.id}", status_code=302)
            else:
                # User is not a participant, show error on join page
                error_msg = "Unfortunately, this event is already finished and matching has been completed."
                return templates.TemplateResponse(
                    "events/join.html",
                    get_template_context(request, user=user, code=code, error=error_msg),
                )

    return templates.TemplateResponse(
        "events/join.html", get_template_context(request, user=user, code=code)
    )


@router.post("/join", response_class=HTMLResponse)
async def join_event(
    request: Request,
    code: str = Form(...),
    user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Process join event - show wishlist selection.

    Args:
        request: FastAPI request object
        code: Event invite code
        user: Current authenticated user
        session: Database session

    Returns:
        HTMLResponse: Wishlist selection page or error
    """
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Find event by code
    result = await session.execute(select(Event).where(Event.code == code.upper()))
    event = result.scalar_one_or_none()

    if not event:
        return templates.TemplateResponse(
            "events/join.html",
            get_template_context(request, user=user, error="Invalid event code"),
        )

    # Check if event is already matched
    if event.status == EventStatus.MATCHED:
        participant_result = await session.execute(
            select(Participant).where(
                Participant.event_id == event.id, Participant.user_id == user.id
            )
        )
        participant = participant_result.scalar_one_or_none()
        if participant:
            # User is already a participant, redirect to event page to show their match
            return RedirectResponse(url=f"/events/{event.id}", status_code=302)
        else:
            # User is not a participant, show error on join page
            error_msg = "Unfortunately, this event is already finished and matching has been completed."
            return templates.TemplateResponse(
                "events/join.html",
                get_template_context(request, user=user, error=error_msg),
            )

    # Get user's wishlists
    wishlists_result = await session.execute(
        select(GlobalWishlist)
        .where(GlobalWishlist.user_id == user.id)
        .order_by(GlobalWishlist.created_at.desc())
    )
    wishlists = wishlists_result.scalars().all()

    return templates.TemplateResponse(
        "events/select_wishlist.html",
        get_template_context(request, user=user, event=event, wishlists=wishlists),
    )


@router.get("/{event_id}/select-wishlist", response_class=HTMLResponse)
async def select_wishlist_for_event(
    request: Request,
    event_id: int,
    user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Show wishlist selection page for a specific event (for joining or updating).

    Args:
        request: FastAPI request object
        event_id: Event ID
        user: Current authenticated user
        session: Database session

    Returns:
        HTMLResponse: Wishlist selection page or redirect
    """
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Get event
    result = await session.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Check if event is already matched
    if event.status == EventStatus.MATCHED:
        participant_result = await session.execute(
            select(Participant).where(
                Participant.event_id == event.id, Participant.user_id == user.id
            )
        )
        participant = participant_result.scalar_one_or_none()
        if participant:
            # User is already a participant, redirect to event page to show their match
            return RedirectResponse(url=f"/events/{event.id}", status_code=302)
        else:
            # User is not a participant, show error on select wishlist page
            error_msg = "Unfortunately, this event is already finished and matching has been completed."
            # Get user's wishlists for the template
            wishlists_result = await session.execute(
                select(GlobalWishlist)
                .where(GlobalWishlist.user_id == user.id)
                .order_by(GlobalWishlist.created_at.desc())
            )
            wishlists = wishlists_result.scalars().all()
            return templates.TemplateResponse(
                "events/select_wishlist.html",
                get_template_context(
                    request,
                    user=user,
                    event=event,
                    wishlists=wishlists,
                    current_participant=None,
                    error=error_msg,
                ),
            )

    # Get user's wishlists
    wishlists_result = await session.execute(
        select(GlobalWishlist)
        .where(GlobalWishlist.user_id == user.id)
        .order_by(GlobalWishlist.created_at.desc())
    )
    wishlists = wishlists_result.scalars().all()

    # Get current participant if exists
    participant_result = await session.execute(
        select(Participant).where(
            Participant.event_id == event.id, Participant.user_id == user.id
        )
    )
    current_participant = participant_result.scalar_one_or_none()

    return templates.TemplateResponse(
        "events/select_wishlist.html",
        get_template_context(
            request,
            user=user,
            event=event,
            wishlists=wishlists,
            current_participant=current_participant,
        ),
    )


@router.post("/{event_id}/join-confirm", response_class=HTMLResponse)
async def join_event_confirm(
    request: Request,
    event_id: int,
    wishlist_id: Optional[int] = Form(None),
    custom_wishlist: Optional[str] = Form(None),
    user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Confirm join event with selected wishlist.

    Args:
        request: FastAPI request object
        event_id: Event ID
        wishlist_id: Selected wishlist ID (optional)
        custom_wishlist: Custom wishlist text (optional)
        user: Current authenticated user
        session: Database session

    Returns:
        RedirectResponse: Redirect to event detail page
    """
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Get event
    result = await session.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Check if event is already matched
    if event.status == EventStatus.MATCHED:
        participant_result = await session.execute(
            select(Participant).where(
                Participant.event_id == event.id, Participant.user_id == user.id
            )
        )
        participant = participant_result.scalar_one_or_none()
        if participant:
            # User is already a participant, redirect to event page to show their match
            return RedirectResponse(url=f"/events/{event.id}", status_code=302)
        else:
            # User is not a participant, show error on select wishlist page
            error_msg = "Unfortunately, this event is already finished and matching has been completed."
            # Get user's wishlists for the template
            wishlists_result = await session.execute(
                select(GlobalWishlist)
                .where(GlobalWishlist.user_id == user.id)
                .order_by(GlobalWishlist.created_at.desc())
            )
            wishlists = wishlists_result.scalars().all()
            return templates.TemplateResponse(
                "events/select_wishlist.html",
                get_template_context(
                    request,
                    user=user,
                    event=event,
                    wishlists=wishlists,
                    current_participant=None,
                    error=error_msg,
                ),
            )

    # Determine wishlist text
    wishlist_text = ""
    if wishlist_id:
        wishlist_result = await session.execute(
            select(GlobalWishlist).where(
                GlobalWishlist.id == wishlist_id, GlobalWishlist.user_id == user.id
            )
        )
        wishlist = wishlist_result.scalar_one_or_none()
        if wishlist:
            wishlist_text = wishlist.content
    elif custom_wishlist:
        wishlist_text = custom_wishlist

    # Validate wishlist is not empty
    if not wishlist_text or not wishlist_text.strip():
        wishlists_result = await session.execute(
            select(GlobalWishlist)
            .where(GlobalWishlist.user_id == user.id)
            .order_by(GlobalWishlist.created_at.desc())
        )
        wishlists = wishlists_result.scalars().all()
        return templates.TemplateResponse(
            "events/select_wishlist.html",
            get_template_context(
                request,
                user=user,
                event=event,
                wishlists=wishlists,
                error="Please provide a wishlist. You cannot join without a wishlist.",
            ),
        )

    # Check if already joined (for OPEN events, allow updating wishlist)
    participant_result = await session.execute(
        select(Participant).where(
            Participant.event_id == event.id, Participant.user_id == user.id
        )
    )
    existing_participant = participant_result.scalar_one_or_none()

    if existing_participant:
        # Update existing participant's wishlist
        existing_participant.wishlist_text = wishlist_text.strip()
        session.add(existing_participant)
        await session.commit()
        # Don't send join notification if already a participant
    else:
        # Create new participant
        participant = Participant(
            user_id=user.id, event_id=event.id, wishlist_text=wishlist_text.strip()
        )
        session.add(participant)
        await session.commit()

        # Send notification to event creator
        try:
            from app.bot import send_event_notification
            await send_event_notification(
                event_id=event.id,
                session=session,
                notification_type="join",
                participant_name=user.name,
            )
        except Exception as e:
            # Log error but don't fail the join
            print(f"Error sending join notification: {e}")

    # Check and trigger matching (only if event is OPEN)
    if event.status == EventStatus.OPEN:
        from app.services.matching import check_and_trigger_matching
        await check_and_trigger_matching(event.id, session)

    # Check and trigger matching
    from app.services.matching import check_and_trigger_matching

    await check_and_trigger_matching(event.id, session)

    return RedirectResponse(url=f"/events/{event.id}", status_code=302)


@router.get("/{event_id}", response_class=HTMLResponse)
async def event_detail(
    request: Request,
    event_id: int,
    user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Show event detail page.

    Args:
        request: FastAPI request object
        event_id: Event ID
        user: Current authenticated user
        session: Database session

    Returns:
        HTMLResponse: Event detail page
    """
    # Get event with creator
    result = await session.execute(
        select(Event, User)
        .join(User, Event.creator_id == User.id)
        .where(Event.id == event_id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Event not found")

    event, creator = row

    # Get participants with user info
    participants_result = await session.execute(
        select(Participant, User)
        .join(User, Participant.user_id == User.id)
        .where(Participant.event_id == event.id)
        .order_by(Participant.joined_at)
    )
    participants_data = participants_result.all()

    # Get current user's participant record if exists
    current_participant = None
    santa_target = None
    if user:
        participant_result = await session.execute(
            select(Participant).where(
                Participant.event_id == event.id, Participant.user_id == user.id
            )
        )
        current_participant = participant_result.scalar_one_or_none()

        # If matched, get santa target
        if current_participant and current_participant.santa_for_user_id:
            target_result = await session.execute(
                select(User).where(User.id == current_participant.santa_for_user_id)
            )
            santa_target = target_result.scalar_one_or_none()

            # Get target's participant record to show their wishlist
            if santa_target:
                target_participant_result = await session.execute(
                    select(Participant).where(
                        Participant.event_id == event.id,
                        Participant.user_id == santa_target.id,
                    )
                )
                target_participant = target_participant_result.scalar_one_or_none()
                if target_participant:
                    santa_target_wishlist = target_participant.wishlist_text
                else:
                    santa_target_wishlist = None
            else:
                santa_target_wishlist = None
        else:
            santa_target_wishlist = None
    else:
        santa_target_wishlist = None

    participants = [
        {"participant": p, "user": u} for p, u in participants_data
    ]

    # Check if user is the creator
    is_creator = user and user.id == creator.id

    # Generate join link with code
    join_link = f"{request.url.scheme}://{request.url.netloc}/events/join?code={event.code}"

    # Get error message from query parameters if present
    error = request.query_params.get("error")
    # FastAPI automatically decodes URL-encoded query parameters
    if error:
        error = str(error)

    return templates.TemplateResponse(
        "events/detail.html",
        get_template_context(
            request,
            user=user,
            event=event,
            creator=creator,
            participants=participants,
            current_participant=current_participant,
            santa_target=santa_target,
            santa_target_wishlist=santa_target_wishlist,
            is_creator=is_creator,
            join_link=join_link,
            error=error,
        ),
    )


@router.post("/{event_id}/unjoin", response_class=HTMLResponse)
async def unjoin_event(
    request: Request,
    event_id: int,
    user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Unjoin an event.

    Args:
        request: FastAPI request object
        event_id: Event ID
        user: Current authenticated user
        session: Database session

    Returns:
        RedirectResponse: Redirect to event detail page or dashboard
    """
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Get event
    result = await session.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Check if event is already matched
    if event.status == EventStatus.MATCHED:
        return RedirectResponse(
            url=f"/events/{event.id}?error=Cannot unjoin a matched event", status_code=302
        )

    # Find participant
    participant_result = await session.execute(
        select(Participant).where(
            Participant.event_id == event.id, Participant.user_id == user.id
        )
    )
    participant = participant_result.scalar_one_or_none()

    if not participant:
        return RedirectResponse(url=f"/events/{event.id}", status_code=302)

    # Delete participant
    await session.delete(participant)
    await session.commit()

    # Send notification to event creator
    try:
        from app.bot import send_event_notification
        await send_event_notification(
            event_id=event.id,
            session=session,
            notification_type="leave",
            participant_name=user.name,
        )
    except Exception as e:
        # Log error but don't fail the unjoin
        print(f"Error sending leave notification: {e}")

    return RedirectResponse(url=f"/events/{event.id}", status_code=302)


@router.post("/{event_id}/delete", response_class=HTMLResponse)
async def delete_event(
    request: Request,
    event_id: int,
    user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete an event (only creator can delete, including matched events).

    Args:
        request: FastAPI request object
        event_id: Event ID
        user: Current authenticated user
        session: Database session

    Returns:
        RedirectResponse: Redirect to dashboard
    """
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Get event
    result = await session.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Check if user is the creator
    if event.creator_id != user.id:
        raise HTTPException(status_code=403, detail="Only the event creator can delete the event")

    # Delete all participants first (cascade)
    participants_result = await session.execute(
        select(Participant).where(Participant.event_id == event.id)
    )
    participants = participants_result.scalars().all()
    for participant in participants:
        await session.delete(participant)

    # Delete event
    await session.delete(event)
    await session.commit()

    return RedirectResponse(url="/dashboard", status_code=302)

