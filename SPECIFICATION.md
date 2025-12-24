# Project: Self-Hosted Secret Santa

## 1. Overview
A lightweight, mobile-friendly web application for organizing Secret Santa gift exchanges.
- **Host:** Raspberry Pi (Dockerized).
- **Access:** Public web via Cloudflare Tunnel.
- **User Base:** Personal use (friends & family).

## 2. Tech Stack
- **Backend:** FastAPI (Python 3.11+).
- **Database:** SQLite with SQLModel (Async preferred).
- **Frontend:** Server-Side Rendered (SSR) HTML using Jinja2 templates.
- **Styling:** Tailwind CSS + DaisyUI (loaded via CDN for simplicity).
- **Auth:** Google OAuth2 (using `authlib` + `starlette.middleware.sessions`).
- **Bot:** `python-telegram-bot` (Async).

## 3. Core Features

### A. Authentication & User Profile
- **Google Login:** Users log in to access the app.
- **Telegram Linking:**
  - User profile shows a "Connect Telegram" button.
  - Links to `https://t.me/YourBot?start=<user_uuid_token>`.
  - Bot receives `/start <token>`, looks up the user by token, and saves `chat_id`.

### B. Wishlist Management (The "Global" List)
- Users can create multiple personal wishlists.
- **Budget Buckets:** Users categorize lists (e.g., "$0-30", "$30-50", "$100+", "Birthday").
- **Public Sharing:**
  - "Share" button generates a unique link: `/wishlist/share/<uuid>`.
  - This link is public (no login required) and read-only.

### C. Event Logic
- **Create Event:**
  - Inputs: Title, Description, Budget Limit, **Target Participant Count**.
  - System generates a 6-character Invite Code (e.g., `X7K-9P`).
- **Join Event:**
  - User enters Code.
  - **Prompt:** "Choose a Wishlist". User selects one of their Global Lists or writes a new one.
  - **Snapshot:** The text is *copied* to the `Participant` record (changes to global list later do not affect active events).
- **Dashboard:**
  - "My Events" (Created by me).
  - "Participating" (Joined).

### D. The "Magic" (Auto-Matching)
- **Trigger:** System checks condition on every "Join" or "Wishlist Update".
- **Condition:** `Count(Participants) == Event.target_count` AND `All participants have non-empty wishlists`.
- **Execution:**
  1. **Algorithm:** Derangement Shuffle (A cannot match A).
  2. **Persistence:** Save `santa_for_user_id` pairs in DB.
  3. **Status:** Update Event status to `MATCHED`.
  4. **Notification:** Trigger Telegram Bot.

### E. Telegram Bot Integration
- **Notifications:**
  - **Match Alert:** "🎅 You are the Santa for **[Name]**! Here is their wishlist:\n[Wishlist Text]" (No click needed).
- **Interactive Commands:**
  - `/myevents`: Lists active events as Inline Buttons.
  - **Button Click:** Edits message to show:
    - Event Title & Status.
    - Participant Count (e.g. "3/5").
    - List of Names (e.g. "Alice, Bob, You...").

## 4. Database Schema (SQLModel)

1. **User:** `id`, `google_id`, `email`, `name`, `avatar`, `telegram_chat_id`, `connect_token` (for linking).
2. **GlobalWishlist:** `id`, `user_id`, `title` (e.g. "$50"), `content`, `share_uuid`.
3. **Event:** `id`, `code`, `title`, `budget`, `target_count`, `status` (OPEN, MATCHED).
4. **Participant:** `id`, `user_id`, `event_id`, `wishlist_text`, `santa_for_user_id` (FK).

## 5. UI/UX Requirements
- **Theme:** DaisyUI "Winter" theme (clean, white/blue/red).
- **Responsiveness:** Mobile-first. Big buttons.
- **Cards:** Events and Wishlists should be displayed as cards.
