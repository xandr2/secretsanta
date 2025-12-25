"""Routes for user profile management.

This module handles profile-related routes including Telegram connection.
"""

from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database import get_session
from app.models import User
from app.utils_templates import get_template_context

router = APIRouter(prefix="/profile", tags=["profile"])


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


@router.get("/connect-telegram", response_class=HTMLResponse)
async def connect_telegram_page(
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Show Telegram connection page with link.

    Args:
        request: FastAPI request object
        user: Current authenticated user
        session: Database session

    Returns:
        HTMLResponse: Telegram connection page or redirect to login
    """
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Generate new token if needed (or reuse existing)
    if not user.connect_token:
        user.connect_token = str(uuid4())
        session.add(user)
        await session.commit()
        await session.refresh(user)

    # Get bot username from bot API if available, otherwise use settings or default
    bot_username = None
    
    # Try to get from bot application if it's initialized
    from app.bot import bot_application
    if bot_application and bot_application.bot:
        try:
            bot_info = await bot_application.bot.get_me()
            if bot_info and bot_info.username:
                bot_username = bot_info.username
        except Exception:
            pass
    
    # Fallback to settings or default
    if not bot_username:
        bot_username = settings.telegram_bot_username or 'YourBot'
    
    telegram_link = f"https://t.me/{bot_username}?start={user.connect_token}"

    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")

    return templates.TemplateResponse(
        "profile/connect_telegram.html",
        get_template_context(request, user=user, telegram_link=telegram_link),
    )

