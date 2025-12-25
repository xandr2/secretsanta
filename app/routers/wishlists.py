"""Routes for GlobalWishlist CRUD operations.

This module handles creating, reading, updating, and deleting wishlists,
as well as the public sharing functionality.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import GlobalWishlist, User
from app.utils_templates import get_template_context


def format_wishlist_content(content: str) -> dict:
    """Format wishlist content, detecting numbered lists.
    
    Args:
        content: Raw wishlist content
        
    Returns:
        dict with 'is_list' bool and 'items' list
    """
    if not content:
        return {"is_list": False, "items": []}
    
    lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
    if not lines:
        return {"is_list": False, "items": []}
    
    # Check if it's a numbered list (starts with "1.", "2.", etc.)
    is_list = False
    items = []
    
    for line in lines:
        # Check if line starts with number followed by dot and space
        stripped = line.strip()
        if len(stripped) > 2 and stripped[0].isdigit() and stripped[1] == '.':
            is_list = True
            # Extract item text (remove number and dot)
            parts = stripped.split('.', 1)
            if len(parts) > 1:
                items.append(parts[1].strip())
            else:
                items.append(stripped)
        else:
            if is_list:
                # If we already detected a list, treat this as continuation
                items.append(stripped)
            else:
                # Not a list format
                return {"is_list": False, "items": [content]}
    
    return {"is_list": is_list, "items": items if is_list else [content]}


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

router = APIRouter(prefix="/wishlists", tags=["wishlists"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def list_wishlists(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all wishlists for the current user.

    Args:
        request: FastAPI request object
        user: Current authenticated user
        session: Database session

    Returns:
        HTMLResponse: Wishlists list page or redirect to login
    """
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    result = await session.execute(
        select(GlobalWishlist).where(GlobalWishlist.user_id == user.id).order_by(GlobalWishlist.created_at.desc())
    )
    wishlists = result.scalars().all()

    # Format content for each wishlist
    formatted_wishlists = []
    for w in wishlists:
        formatted = format_wishlist_content(w.content or "")
        formatted_wishlists.append({"wishlist": w, "formatted": formatted})

    return templates.TemplateResponse(
        "wishlists/list.html",
        get_template_context(request, user=user, wishlists=formatted_wishlists),
    )


@router.get("/create", response_class=HTMLResponse)
async def create_wishlist_form(
    request: Request, user: Optional[User] = Depends(get_current_user)
):
    """Show create wishlist form.

    Args:
        request: FastAPI request object
        user: Current authenticated user

    Returns:
        HTMLResponse: Create wishlist form or redirect to login
    """
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        "wishlists/create.html", get_template_context(request, user=user)
    )


@router.post("/create", response_class=HTMLResponse)
async def create_wishlist(
    request: Request,
    title: str = Form(...),
    content: str = Form(""),
    user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new wishlist.

    Args:
        request: FastAPI request object
        title: Wishlist title
        content: Wishlist content
        user: Current authenticated user
        session: Database session

    Returns:
        RedirectResponse: Redirect to wishlists list
    """
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    wishlist = GlobalWishlist(user_id=user.id, title=title, content=content)
    session.add(wishlist)
    await session.commit()
    await session.refresh(wishlist)

    return RedirectResponse(url="/wishlists", status_code=302)


@router.get("/{wishlist_id}/edit", response_class=HTMLResponse)
async def edit_wishlist_form(
    request: Request,
    wishlist_id: int,
    user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Show edit wishlist form.

    Args:
        request: FastAPI request object
        wishlist_id: Wishlist ID
        user: Current authenticated user
        session: Database session

    Returns:
        HTMLResponse: Edit wishlist form or error
    """
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    result = await session.execute(
        select(GlobalWishlist).where(
            GlobalWishlist.id == wishlist_id, GlobalWishlist.user_id == user.id
        )
    )
    wishlist = result.scalar_one_or_none()

    if not wishlist:
        raise HTTPException(status_code=404, detail="Wishlist not found")

    return templates.TemplateResponse(
        "wishlists/edit.html",
        get_template_context(request, user=user, wishlist=wishlist),
    )


@router.post("/{wishlist_id}/edit", response_class=HTMLResponse)
async def update_wishlist(
    request: Request,
    wishlist_id: int,
    title: str = Form(...),
    content: str = Form(""),
    user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update a wishlist.

    Args:
        request: FastAPI request object
        wishlist_id: Wishlist ID
        title: Wishlist title
        content: Wishlist content
        user: Current authenticated user
        session: Database session

    Returns:
        RedirectResponse: Redirect to wishlists list
    """
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    result = await session.execute(
        select(GlobalWishlist).where(
            GlobalWishlist.id == wishlist_id, GlobalWishlist.user_id == user.id
        )
    )
    wishlist = result.scalar_one_or_none()

    if not wishlist:
        raise HTTPException(status_code=404, detail="Wishlist not found")

    wishlist.title = title
    wishlist.content = content
    session.add(wishlist)
    await session.commit()

    return RedirectResponse(url="/wishlists", status_code=302)


@router.post("/{wishlist_id}/delete", response_class=HTMLResponse)
async def delete_wishlist(
    request: Request,
    wishlist_id: int,
    user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a wishlist.

    Args:
        request: FastAPI request object
        wishlist_id: Wishlist ID
        user: Current authenticated user
        session: Database session

    Returns:
        RedirectResponse: Redirect to wishlists list
    """
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    result = await session.execute(
        select(GlobalWishlist).where(
            GlobalWishlist.id == wishlist_id, GlobalWishlist.user_id == user.id
        )
    )
    wishlist = result.scalar_one_or_none()

    if not wishlist:
        raise HTTPException(status_code=404, detail="Wishlist not found")

    await session.delete(wishlist)
    await session.commit()

    return RedirectResponse(url="/wishlists", status_code=302)


@router.get("/share/{share_uuid}", response_class=HTMLResponse)
async def share_wishlist(
    request: Request,
    share_uuid: str,
    session: AsyncSession = Depends(get_session),
):
    """Public share page for wishlist (no login required).

    Args:
        request: FastAPI request object
        share_uuid: Share UUID of the wishlist
        session: Database session

    Returns:
        HTMLResponse: Public wishlist view page
    """
    result = await session.execute(
        select(GlobalWishlist, User).join(User).where(
            GlobalWishlist.share_uuid == share_uuid
        )
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Wishlist not found")

    wishlist, owner = row

    # Format wishlist content
    formatted_content = format_wishlist_content(wishlist.content or "")

    return templates.TemplateResponse(
        "wishlists/share.html",
        get_template_context(
            request,
            wishlist=wishlist,
            owner=owner,
            formatted_content=formatted_content,
        ),
    )

