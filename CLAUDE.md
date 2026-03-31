# better-court-finder

A bot that polls the Better API for badminton court availability and notifies users via Telegram.

## Architecture

### Current state
- `src/main.py` — entrypoint, runs court updater + Telegram bot as concurrent async tasks via `asyncio.gather()`
- `src/tasks.py` — async task wrappers
- `src/poller/` — (target) fetches courts from Better API, diffs against cache, publishes events
- `src/services/court_fetcher.py` — HTTP fetching from Better API (to be collapsed into poller)
- `src/services/court_database.py` — SQLite-backed court storage (to be replaced by Redis)
- `src/services/court_updater.py` — orchestrates fetch + store (to be replaced by poller)
- `src/telegram_bot/` — Telegram bot, handles user commands and availability notifications
- `src/models/court.py` — Pydantic model for a court slot
- `src/utils/constants.py` — file paths and venue/activity slug strings (to be replaced by enums)

### Target architecture
```
src/
  poller/
    poller.py         # fetch → diff vs Redis cache → publish events → update cache
  subscribers/
    telegram/         # subscribes to Redis pub/sub, sends notifications
    discord/          # future
  models/
    court.py          # @dataclass, no parsing logic
    venue.py          # Venue and ActivitySlug StrEnums
  utils/
    constants.py      # file paths only (or gone entirely)
```

### Redis layout
- A Redis Set storing the current available courts (cache/source of truth)
- A Redis Pub/Sub channel (e.g. `court_availability`) with `{now_available: [...], now_unavailable: [...]}` payloads
- A Redis Set for the Telegram notify list (replaces `bot_config.toml`)

### Key decisions
- **No SQLite** — Redis replaces it entirely as the source of truth
- **No ICS files** — removed
- **No FastAPI/uvicorn** — removed; the app is just a poller + bot
- **No singletons** — `CourtDatabase`, `CourtUpdater`, `BotConfig` were singletons to share state; with Redis this is unnecessary
- **`StrEnum` for slugs** — venue/activity slugs are a fixed known set, use `StrEnum` so they behave as plain strings everywhere
- **`@dataclass` for `Court`** — move API wire-format parsing (dict → `time`, dict → `str`) into the poller; the model stays clean
- **`polling_interval`** — becomes an env var, not stored in config
- **Telegram notify list** — persisted in Redis (`SADD`/`SREM`/`SMEMBERS`), survives restarts

### How the bot couples to data (current)
`CourtDatabase` is called in only three places:
- `telegram_bot.py` — initial cache build + availability monitor (both removed with pub/sub)
- `handlers.py` — search queries (swap `CourtDatabase().get_*` for Redis lookups)

So the Redis swap touches the whole bot but each change is small.

---

## Refactor checklist

### 1. Enums and models
- [ ] Create `src/models/venue.py` with `Venue(StrEnum)` and `ActivitySlug(StrEnum)`
- [ ] Replace string literals in `constants.py` and `court_fetcher.py` with enum references
- [ ] Convert `Court` from Pydantic `BaseModel` to `@dataclass`
- [ ] Move API wire-format parsing (time dicts, price dicts) out of `Court` validators and into the poller
- [ ] Remove `class Config: frozen = True` — add `frozen=True` to `@dataclass` if hashability is still needed

### 2. Poller
- [ ] Create `src/poller/poller.py`
- [ ] Collapse `court_fetcher.py` logic directly into the poller
- [ ] Poller still writes to SQLite for now (keeps bot working during transition)
- [ ] Delete `src/services/court_fetcher.py` and `src/services/court_updater.py`

### 3. Redis cache (swap out SQLite)
- [ ] Add Redis client (`redis.asyncio`) — create `src/services/redis_client.py` or similar
- [ ] Poller writes available courts to Redis Set after each fetch
- [ ] Replace `CourtDatabase().get_all_available()` / `get_available_by_date()` / `get_available_by_time_range()` in handlers with Redis lookups
- [ ] Migrate notify list from `bot_config.toml` to Redis Set
- [ ] Delete `src/services/court_database.py`, `src/telegram_bot/bot_config.py`, `data/bot_config.toml`
- [ ] Delete `data/` folder entirely

### 4. Pub/sub
- [ ] Poller publishes `{now_available, now_unavailable}` diffs to Redis Pub/Sub channel after each fetch
- [ ] Replace `TelegramBot._availability_monitor_task` with a Redis subscriber
- [ ] Remove `self.cache` from `TelegramBot` (Redis is the cache now)
- [ ] Move notification logic out of `telegram_bot.py` into a subscriber class under `src/subscribers/telegram/`

### 5. Discord subscriber
- [ ] Create `src/subscribers/discord/` mirroring the Telegram subscriber structure
- [ ] Subscribe to the same Redis Pub/Sub channel