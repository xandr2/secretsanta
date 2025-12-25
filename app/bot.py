"""Telegram bot integration for Secret Santa.

This module handles Telegram bot functionality including:
- User linking via /start command
- Event notifications
- Interactive event listing
"""

import asyncio
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackContext, CommandHandler, CallbackQueryHandler

from app.core.config import settings
from app.database import AsyncSessionLocal
from app.models import Event, Participant, User


# Global bot application instance
bot_application: Optional[Application] = None


async def get_db_session():
    """Get database session for bot operations."""
    async with AsyncSessionLocal() as session:
        yield session


async def start_command(update: Update, context: CallbackContext) -> None:
    """Handle /start command for linking user account.

    Args:
        update: Telegram update object
        context: Callback context
    """
    if not update.message:
        return

    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    text = update.message.text

    # Extract token from /start <token>
    token = None
    if text and len(text.split()) > 1:
        token = text.split()[1]

    async with AsyncSessionLocal() as session:
        if token:
            # Link user account
            result = await session.execute(
                select(User).where(User.connect_token == token)
            )
            user = result.scalar_one_or_none()

            if user:
                user.telegram_chat_id = chat_id
                session.add(user)
                await session.commit()
                await update.message.reply_text(
                    f"✅ Successfully linked! Welcome, {user.name}.\n\n"
                    "Use /myevents to see your events."
                )
            else:
                await update.message.reply_text(
                    "❌ Invalid token. Please use the link from your profile page."
                )
        else:
            # Check if already linked
            result = await session.execute(
                select(User).where(User.telegram_chat_id == chat_id)
            )
            user = result.scalar_one_or_none()

            if user:
                await update.message.reply_text(
                    f"Welcome back, {user.name}!\n\n"
                    "Use /myevents to see your events."
                )
            else:
                await update.message.reply_text(
                    "👋 Welcome to Secret Santa Bot!\n\n"
                    "To link your account, use the 'Connect Telegram' button "
                    "in your profile and click the link provided."
                )


async def myevents_command(update: Update, context: CallbackContext) -> None:
    """Handle /myevents command to show user's events.

    Args:
        update: Telegram update object
        context: Callback context
    """
    if not update.message:
        return

    chat_id = update.message.chat_id

    async with AsyncSessionLocal() as session:
        # Find user by telegram_chat_id
        result = await session.execute(
            select(User).where(User.telegram_chat_id == chat_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await update.message.reply_text(
                "❌ Account not linked. Please use /start with your token first."
            )
            return

        # Get events user is participating in
        participants_result = await session.execute(
            select(Participant, Event)
            .join(Event, Participant.event_id == Event.id)
            .where(Participant.user_id == user.id)
            .order_by(Event.created_at.desc())
        )
        events_data = participants_result.all()

        if not events_data:
            await update.message.reply_text("You're not participating in any events yet.")
            return

        # Create inline keyboard with event buttons
        keyboard = []
        for participant, event in events_data:
            keyboard.append([
                InlineKeyboardButton(
                    f"{event.title} ({event.status})",
                    callback_data=f"event_{event.id}"
                )
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📋 Your Events:\n\nSelect an event to view details:",
            reply_markup=reply_markup,
        )


async def event_callback(update: Update, context: CallbackContext) -> None:
    """Handle event button callback.

    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    if not query:
        return

    await query.answer()

    event_id = int(query.data.split("_")[1])
    chat_id = query.message.chat_id if query.message else None

    if not chat_id:
        return

    async with AsyncSessionLocal() as session:
        # Get event with participants
        result = await session.execute(
            select(Event).where(Event.id == event_id)
        )
        event = result.scalar_one_or_none()

        if not event:
            await query.edit_message_text("❌ Event not found.")
            return

        # Get participants
        participants_result = await session.execute(
            select(Participant, User)
            .join(User, Participant.user_id == User.id)
            .where(Participant.event_id == event.id)
            .order_by(Participant.joined_at)
        )
        participants_data = participants_result.all()

        # Get current user
        user_result = await session.execute(
            select(User).where(User.telegram_chat_id == chat_id)
        )
        user = user_result.scalar_one_or_none()

        # Build message
        message = f"🎅 *{event.title}*\n\n"
        message += f"Status: {event.status}\n"
        message += f"Budget: ${event.budget:.2f}\n"
        message += f"Participants: {len(participants_data)}/{event.target_count}\n\n"

        if participants_data:
            message += "*Participants:*\n"
            for participant, p_user in participants_data:
                marker = "👤" if user and p_user.id == user.id else "•"
                message += f"{marker} {p_user.name}\n"

        # Show santa target if matched
        if user and event.status == "MATCHED":
            participant_result = await session.execute(
                select(Participant).where(
                    Participant.event_id == event.id,
                    Participant.user_id == user.id,
                )
            )
            participant = participant_result.scalar_one_or_none()

            if participant and participant.santa_for_user_id:
                target_result = await session.execute(
                    select(User).where(User.id == participant.santa_for_user_id)
                )
                target = target_result.scalar_one_or_none()

                if target:
                    message += f"\n🎁 *Your Santa Target:* {target.name}"

        await query.edit_message_text(message, parse_mode="Markdown")


async def send_event_notification(
    event_id: int,
    session: AsyncSession,
    notification_type: str,
    participant_name: str,
) -> None:
    """Send notification to event creator when someone joins or leaves.

    Args:
        event_id: Event ID
        session: Database session
        notification_type: Type of notification ("join" or "leave")
        participant_name: Name of the participant who joined/left
    """
    global bot_application

    if not bot_application:
        print("Bot not initialized. Skipping notifications.")
        return

    # Get event with creator
    result = await session.execute(
        select(Event, User)
        .join(User, Event.creator_id == User.id)
        .where(Event.id == event_id)
    )
    row = result.first()

    if not row:
        return

    event, creator = row

    # Check if creator has Telegram linked
    if not creator.telegram_chat_id:
        return

    # Get current participant count
    participants_result = await session.execute(
        select(Participant).where(Participant.event_id == event_id)
    )
    participant_count = len(list(participants_result.scalars().all()))

    # Build message
    if notification_type == "join":
        emoji = "✅"
        action = "joined"
    elif notification_type == "leave":
        emoji = "👋"
        action = "left"
    else:
        return

    message = (
        f"{emoji} *Event Update*\n\n"
        f"*{participant_name}* {action} your event:\n"
        f"*{event.title}*\n\n"
        f"Participants: {participant_count}/{event.target_count}"
    )

    try:
        await bot_application.bot.send_message(
            chat_id=creator.telegram_chat_id,
            text=message,
            parse_mode="Markdown",
        )
    except Exception as e:
        # Log error but don't fail
        print(f"Error sending event notification to {creator.telegram_chat_id}: {e}")


async def send_match_notifications(event_id: int, session: AsyncSession) -> None:
    """Send match notifications to all participants.

    Args:
        event_id: Event ID
        session: Database session
    """
    global bot_application

    if not bot_application:
        print("Bot not initialized. Skipping notifications.")
        return

    # Get event
    result = await session.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        return

    # Get all participants
    participants_result = await session.execute(
        select(Participant).where(Participant.event_id == event_id)
    )
    participants = participants_result.scalars().all()

    for participant in participants:
        if not participant.santa_for_user_id:
            continue

        # Get user
        user_result = await session.execute(
            select(User).where(User.id == participant.user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user or not user.telegram_chat_id:
            continue

        # Get target user
        target_result = await session.execute(
            select(User).where(User.id == participant.santa_for_user_id)
        )
        target = target_result.scalar_one_or_none()

        if not target:
            continue

        # Get target's participant record for wishlist
        target_participant_result = await session.execute(
            select(Participant).where(
                Participant.event_id == event_id,
                Participant.user_id == target.id,
            )
        )
        target_participant = target_participant_result.scalar_one_or_none()

        wishlist_text = target_participant.wishlist_text if target_participant else "No wishlist provided."

        message = (
            f"🎅 *Match Alert!*\n\n"
            f"You are the Santa for *{target.name}*!\n\n"
            f"*Their Wishlist:*\n{wishlist_text}"
        )

        try:
            await bot_application.bot.send_message(
                chat_id=user.telegram_chat_id,
                text=message,
                parse_mode="Markdown",
            )
        except Exception as e:
            # Log error in production
            print(f"Error sending notification to {user.telegram_chat_id}: {e}")


async def init_bot() -> Optional[Application]:
    """Initialize and start the Telegram bot.

    Returns:
        Optional[Application]: Bot application instance or None if token not set
    """
    if not settings.telegram_bot_token:
        print("Warning: TELEGRAM_BOT_TOKEN not set. Bot will not start.")
        return None

    try:
        application = Application.builder().token(settings.telegram_bot_token).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("myevents", myevents_command))
        application.add_handler(CallbackQueryHandler(event_callback, pattern="^event_"))

        return application
    except Exception as e:
        print(f"Error initializing bot: {e}")
        return None


async def start_bot() -> None:
    """Start the bot in the background."""
    global bot_application

    if not settings.telegram_bot_token:
        print("Telegram bot token not configured. Bot disabled.")
        return

    bot_application = await init_bot()
    if bot_application:
        await bot_application.initialize()
        await bot_application.start()
        if bot_application.updater:
            await bot_application.updater.start_polling()
        print("Telegram bot started successfully.")


async def stop_bot() -> None:
    """Stop the bot."""
    global bot_application

    if bot_application:
        await bot_application.updater.stop()
        await bot_application.stop()
        await bot_application.shutdown()
        bot_application = None

