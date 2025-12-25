"""Pytest configuration and fixtures.

This module provides shared fixtures for all tests including:
- Database setup and teardown
- Test client
- Test users
- Mock OAuth
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.main import app
from app.models import Event, GlobalWishlist, Participant, User


# Use in-memory database for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    future=True,
)

TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session.

    Yields:
        AsyncSession: Test database session
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> TestClient:
    """Create a test client.

    Args:
        db_session: Test database session

    Returns:
        TestClient: FastAPI test client
    """
    from app.database import get_session

    # Override database dependency
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user.

    Args:
        db_session: Test database session

    Returns:
        User: Test user instance
    """
    user = User(
        google_id="test_google_id_123",
        email="test@example.com",
        name="Test User",
        avatar="https://example.com/avatar.jpg",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def authenticated_client(client: TestClient, test_user: User, db_session: AsyncSession) -> TestClient:
    """Create an authenticated test client.

    Args:
        client: Test client
        test_user: Test user
        db_session: Database session

    Returns:
        TestClient: Authenticated test client
    """
    from tests.auth_helpers import setup_auth_override, teardown_auth_override
    
    # Set up authentication override
    setup_auth_override(app, test_user)
    
    yield client
    
    # Clean up
    teardown_auth_override(app)
