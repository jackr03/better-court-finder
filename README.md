# Better Court Finder
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![PostgreSQL](https://img.shields.io/badge/postgresql-4169e1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)

A service that polls Better's public API for badminton court availability across Manchester venues and pushes real-time notifications to subscribers via Telegram and Discord. Built with Python and `asyncio`, using Redis pub/sub to decouple the poller from delivery channels, and Postgres as the store for subscriptions.

## Architecture

- **Poller → Publisher → Subscriber → Notifier**: `CourtPoller` polls the upstream API on a fixed interval, set-diffs the current availability against the previous cycle, and publishes only the changes. It has no knowledge of who consumes them.
- **Redis pub/sub as transport**: changes are published per venue to `bcf:venues:{venue}`. Each notifier owns its own `CourtSubscriber`, pattern-subscribed to `bcf:venues:*`. Adding a new delivery channel only requires adding a `Notifier` subclass, not touching the polling logic.
- **Split persistence**: Postgres is authoritative for user -> venue subscriptions, Redis holds ephemeral availability snapshots (TTL'd) and carries change events.

## Features

- Real-time notifications on availability changes only (rather than every poll cycle)
- Telegram:
  - Notifications are per-venue and opt-in, toggled by the user via `/notifications`
  - Also has on-demand quick search across all venues, filtered by date, time range, or venue using `/search`
  - Long result sets split across messages at line boundaries to stay under Telegram's 4096-character limit, with a close button that clears the whole set
- Discord:
  - Broadcasts every change for a venue to its channel
  - Delivery is via per-venue webhooks, configured independently of Telegram

## Technical Details

- **Bounded concurrency** — `asyncio.Semaphore(10)` caps in-flight requests to the Better API while `asyncio.gather` fans out across every venue/activity/date combination
- **Retry with exponential backoff and equal jitter** — `get_backoff_delay` computes `base·2ⁿ/2 + uniform(0, base·2ⁿ/2)`, applied to upstream API calls (on 429, 5xx, and client/timeout errors) and Discord webhook posts
- **Redis hot cache** — court snapshots keyed `bcf:courts:{venue}:{date}` with a 600s TTL, read via `scan_iter` glob patterns for date/venue/time-range queries. User searches never hit the upstream API
- **Cold-start suppression** — the first poll cycle populates state without publishing, so subscribers aren't flooded on boot
- **Rate-limit handling** — `TelegramRetryAfter` is caught per-send and retried after the interval the API asks for; Discord's `retry_after` is honoured the same way

## Running Locally

Requires Docker and a Telegram bot token from [@BotFather](https://t.me/botfather).

1. Copy `.env.example` to `.env` and fill in:
   - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
   - `TELEGRAM_BOT_TOKEN`
   - `DISCORD_WEBHOOK_{VENUE_NAME}` (optional, per venue — e.g. `DISCORD_WEBHOOK_SUGDEN_SPORTS_CENTRE`)
     - Venues without a configured Discord webhook are logged as disabled on startup and skipped.
2. Start infrastructure:
```bash
  docker compose up
```
  Postgres runs `db/init.sql` on first boot to create the `subscriptions` table.

3. Run the bot, either containerised alongside infrastructure:
```bash
  docker compose --profile bot up --build
```
  or locally for faster development.
```bash
  pip install -r requirements.txt
  python -m src.main
```
