"""FastAPI application entry point.

This module sets up the FastAPI application with Google OAuth authentication,
database initialization, and route handlers.
"""

from contextlib import asynccontextmanager
from typing import Optional

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.database import get_session, init_db
from app.models import User
from app.routers import events, profile, wishlists
from app.utils_templates import get_template_context

# Initialize templates
templates = Jinja2Templates(directory="templates")

# OAuth configuration
oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id or "",
    client_secret=settings.google_client_secret or "",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)




@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown.

    Args:
        app: FastAPI application instance
    """
    # Startup: Initialize database
    await init_db()

    # Start Telegram bot
    from app.bot import start_bot, stop_bot

    import asyncio

    bot_task = None
    try:
        bot_task = asyncio.create_task(start_bot())
    except Exception as e:
        print(f"Warning: Could not start bot: {e}")

    yield

    # Shutdown: Stop bot
    try:
        await stop_bot()
        if bot_task:
            bot_task.cancel()
            try:
                await bot_task
            except asyncio.CancelledError:
                pass
    except Exception as e:
        print(f"Error stopping bot: {e}")


# Create FastAPI app
app = FastAPI(
    title="Secret Santa",
    description="Self-hosted Secret Santa gift exchange organizer",
    lifespan=lifespan,
)

# Add session middleware for OAuth with proper cookie settings
# Configure cookies for OAuth CSRF protection
cookie_kwargs = {
    "secret_key": settings.secret_key,
    "same_site": settings.cookie_same_site,
    "https_only": settings.cookie_secure,
}
if settings.cookie_domain:
    cookie_kwargs["domain"] = settings.cookie_domain

app.add_middleware(SessionMiddleware, **cookie_kwargs)

# Register routers
app.include_router(wishlists.router)
app.include_router(profile.router)
app.include_router(events.router)


async def get_current_user(
    request: Request, session: AsyncSession = Depends(get_session)
) -> Optional[User]:
    """Get current authenticated user from session.

    Args:
        request: FastAPI request object
        session: Database session

    Returns:
        Optional[User]: Current user or None if not authenticated
    """
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    from sqlalchemy import select

    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


@app.get("/", response_class=HTMLResponse)
async def root(
    request: Request, session: AsyncSession = Depends(get_session)
):
    """Root route - redirects to login or dashboard.

    Args:
        request: FastAPI request object
        session: Database session

    Returns:
        HTMLResponse: Redirect response
    """
    user = await get_current_user(request, session)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page route.

    Args:
        request: FastAPI request object

    Returns:
        HTMLResponse: Login page template
    """
    return templates.TemplateResponse("login.html", get_template_context(request))


@app.get("/auth/google")
async def google_auth(request: Request):
    """Initiate Google OAuth flow.

    Args:
        request: FastAPI request object

    Returns:
        RedirectResponse: Redirect to Google OAuth
    """
    # Use configured redirect URI if provided, otherwise auto-detect from request
    if settings.google_redirect_uri:
        redirect_uri = settings.google_redirect_uri
    else:
        redirect_uri = str(request.url_for("google_auth_callback"))
    
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/auth/google/callback", name="google_auth_callback")
async def google_auth_callback(
    request: Request, session: AsyncSession = Depends(get_session)
):
    """Handle Google OAuth callback.

    Args:
        request: FastAPI request object
        session: Database session

    Returns:
        RedirectResponse: Redirect to dashboard or login
    """
    try:
        token = await oauth.google.authorize_access_token(request)
        
        # Fetch user info from Google's userinfo endpoint
        # Authlib may include userinfo in token response, but we fetch it explicitly to be sure
        user_info = token.get("userinfo")
        if not user_info:
            # Fetch user info using the access token
            import httpx
            access_token = token.get("access_token")
            if not access_token:
                print(f"No access token in response. Token keys: {list(token.keys())}")
                return RedirectResponse(url="/login?error=auth_failed", status_code=302)
            
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                if resp.status_code == 200:
                    user_info = resp.json()
                else:
                    print(f"Failed to fetch user info: Status {resp.status_code}")
                    print(f"Response: {resp.text}")
                    return RedirectResponse(url="/login?error=auth_failed", status_code=302)

        google_id = user_info.get("sub") or user_info.get("id")
        email = user_info.get("email")
        name = user_info.get("name", "")
        avatar = user_info.get("picture")

        if not google_id or not email:
            print(f"Missing user info: google_id={google_id}, email={email}")
            return RedirectResponse(url="/login?error=invalid_user", status_code=302)

        # Check if user exists
        from sqlalchemy import select

        result = await session.execute(
            select(User).where(User.google_id == google_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            # Create new user
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                avatar=avatar,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            # Update existing user info (name and avatar may change)
            user.name = name
            if avatar:
                user.avatar = avatar
            session.add(user)
            await session.commit()
            await session.refresh(user)

        # Set session
        request.session["user_id"] = user.id

        return RedirectResponse(url="/dashboard", status_code=302)

    except Exception as e:
        # Log error for debugging
        import traceback
        print(f"OAuth callback error: {e}")
        print(traceback.format_exc())
        return RedirectResponse(url="/login?error=auth_failed", status_code=302)


@app.get("/logout")
async def logout(request: Request):
    """Logout route.

    Args:
        request: FastAPI request object

    Returns:
        RedirectResponse: Redirect to login
    """
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Dashboard route showing user's wishlists and events.

    Args:
        request: FastAPI request object
        user: Current authenticated user
        session: Database session

    Returns:
        HTMLResponse: Dashboard page or redirect to login
    """
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    from sqlalchemy import select
    from app.models import GlobalWishlist, Event, Participant

    # Get user's wishlists
    wishlists_result = await session.execute(
        select(GlobalWishlist)
        .where(GlobalWishlist.user_id == user.id)
        .order_by(GlobalWishlist.created_at.desc())
        .limit(5)
    )
    wishlists = wishlists_result.scalars().all()

    # Get events created by user
    events_created_result = await session.execute(
        select(Event)
        .where(Event.creator_id == user.id)
        .order_by(Event.created_at.desc())
        .limit(5)
    )
    events_created = events_created_result.scalars().all()

    # Get events user is participating in
    participants_result = await session.execute(
        select(Participant)
        .where(Participant.user_id == user.id)
        .order_by(Participant.joined_at.desc())
        .limit(5)
    )
    participants = participants_result.scalars().all()
    event_ids = [p.event_id for p in participants]
    events_joined = []
    if event_ids:
        events_joined_result = await session.execute(
            select(Event).where(Event.id.in_(event_ids))
        )
        events_joined = events_joined_result.scalars().all()

    return templates.TemplateResponse(
        "dashboard.html",
        get_template_context(
            request,
            user=user,
            wishlists=wishlists,
            events_created=events_created,
            events_joined=events_joined,
        ),
    )

