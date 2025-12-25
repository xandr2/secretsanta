"""Database connection and initialization logic.

This module handles SQLite database connection using SQLModel with async support.
It provides functions to initialize the database and create tables on startup.
"""

import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings
from app.models import Event, GlobalWishlist, Participant, User


# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    future=True,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session():
    """Get async database session for FastAPI dependency injection.

    Yields:
        AsyncSession: Database session

    Example:
        Used as FastAPI dependency:
        async def my_route(session: AsyncSession = Depends(get_session)):
            ...
    """
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Initialize database and create all tables.

    This function should be called on application startup to ensure
    all database tables are created. It also ensures the data directory exists.

    Example:
        await init_db()
    """
    # Ensure data directory exists for SQLite
    if "sqlite" in settings.database_url:
        # Extract directory path from database URL
        db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
        # Handle relative paths
        if db_path.startswith("./"):
            db_path = db_path[2:]
        elif not db_path.startswith("/"):
            db_path = f"./{db_path}"
        
        # Get directory path
        db_dir = os.path.dirname(db_path)
        if db_dir:
            Path(db_dir).mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

