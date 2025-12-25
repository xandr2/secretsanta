"""SQLModel database models for Secret Santa application.

This module defines all database models using SQLModel, including:
- User: Authentication and profile information
- GlobalWishlist: User's personal wishlists
- Event: Secret Santa events
- Participant: Users participating in events
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlmodel import Field, Relationship, SQLModel


class EventStatus(str, Enum):
    """Event status enumeration."""

    OPEN = "OPEN"
    MATCHED = "MATCHED"


class User(SQLModel, table=True):
    """User model for authentication and profile.

    Attributes:
        id: Primary key
        google_id: Google OAuth ID
        email: User email address
        name: User display name
        avatar: URL to user avatar image
        telegram_chat_id: Telegram chat ID for bot notifications
        connect_token: UUID token for Telegram linking
        created_at: Account creation timestamp
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    google_id: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    name: str
    avatar: Optional[str] = None
    telegram_chat_id: Optional[int] = Field(default=None, index=True)
    connect_token: str = Field(default_factory=lambda: str(uuid4()), unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    wishlists: list["GlobalWishlist"] = Relationship(back_populates="user")
    events_created: list["Event"] = Relationship(back_populates="creator")
    participants: list["Participant"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[Participant.user_id]"}
    )


class GlobalWishlist(SQLModel, table=True):
    """Global wishlist model for user's personal wishlists.

    Attributes:
        id: Primary key
        user_id: Foreign key to User
        title: Wishlist title (e.g., "$0-30", "$30-50", "Birthday")
        content: Wishlist content/text
        share_uuid: UUID for public sharing link
        created_at: Creation timestamp
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: str
    content: str = ""
    share_uuid: str = Field(default_factory=lambda: str(uuid4()), unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="wishlists")


class Event(SQLModel, table=True):
    """Event model for Secret Santa events.

    Attributes:
        id: Primary key
        code: 6-character invite code (e.g., "X7K-9P")
        title: Event title
        description: Event description
        budget: Budget limit
        target_count: Target number of participants
        status: Event status (OPEN or MATCHED)
        creator_id: Foreign key to User who created the event
        created_at: Creation timestamp
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True)
    title: str
    description: str = ""
    budget: float
    target_count: int
    status: EventStatus = Field(default=EventStatus.OPEN)
    creator_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    creator: User = Relationship(back_populates="events_created")
    participants: list["Participant"] = Relationship(back_populates="event")


class Participant(SQLModel, table=True):
    """Participant model for users in events.

    Attributes:
        id: Primary key
        user_id: Foreign key to User
        event_id: Foreign key to Event
        wishlist_text: Snapshot of wishlist text at join time
        santa_for_user_id: Foreign key to User (who this participant is Santa for)
        joined_at: Join timestamp
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    event_id: int = Field(foreign_key="event.id")
    wishlist_text: str = ""
    santa_for_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    joined_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(
        back_populates="participants",
        sa_relationship_kwargs={"foreign_keys": "[Participant.user_id]"}
    )
    event: Event = Relationship(back_populates="participants")
    santa_for: Optional[User] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Participant.santa_for_user_id]"}
    )

