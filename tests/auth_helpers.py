"""Authentication helpers for tests.

This module provides utilities to mock authentication in tests.
"""

from typing import Optional

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


def setup_auth_override(app: FastAPI, test_user: User):
    """Set up authentication override for all routers.

    Args:
        app: FastAPI application
        test_user: Test user to authenticate as
    """
    from fastapi import Depends, Request
    from app.database import get_session
    from app.main import get_current_user
    from app.routers import events, profile, wishlists

    async def override_get_current_user(
        request: Request, session: AsyncSession = Depends(get_session)
    ):
        return test_user

    # Override main app's get_current_user
    app.dependency_overrides[get_current_user] = override_get_current_user

    # Override router-level get_current_user functions
    app.dependency_overrides[wishlists.get_current_user] = override_get_current_user
    app.dependency_overrides[events.get_current_user] = override_get_current_user
    app.dependency_overrides[profile.get_current_user] = override_get_current_user


def teardown_auth_override(app: FastAPI):
    """Remove authentication overrides.

    Args:
        app: FastAPI application
    """
    from app.main import get_current_user
    from app.routers import events, profile, wishlists

    overrides_to_remove = [
        get_current_user,
        wishlists.get_current_user,
        events.get_current_user,
        profile.get_current_user,
    ]

    for override in overrides_to_remove:
        if override in app.dependency_overrides:
            del app.dependency_overrides[override]

