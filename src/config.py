import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

from src.models.venue import Venue

load_dotenv()

@dataclass(frozen=True)
class PollingConfig:
    interval: int = 300
    max_concurrent: int = 10
    max_retries: int = 3
    base_delay: float = 1.0


@dataclass(frozen=True)
class RedisConfig:
    host: str
    port: int
    namespace: str = 'bcf'
    ttl: int = 600 # 2x PollingConfig.interval lets us survive a failed cycle


def _load_redis_config() -> RedisConfig:
    return RedisConfig(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379))
    )


@dataclass(frozen=True)
class PostgresConfig:
    user: str
    password: str
    database: str
    host: str
    port: int


def _load_postgres_config() -> PostgresConfig:
    return PostgresConfig(
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
        database=os.environ['POSTGRES_DB'],
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', 5432))
    )


@dataclass(frozen=True)
class DiscordConfig:
    webhooks: dict[Venue, str]
    backoff_delay: float = 1.0
    max_retries: int = 3


def _load_discord_config() -> DiscordConfig:
    webhooks = {}
    for venue in Venue:
        url = os.getenv(f'DISCORD_WEBHOOK_{venue.name}')
        if url:
            webhooks[venue] = url

    return DiscordConfig(
        webhooks=webhooks
    )


@dataclass(frozen=True)
class TelegramConfig:
    token: str
    multi_message_delay: float = 0.075


def _load_telegram_config() -> TelegramConfig:
    return TelegramConfig(
        token=os.environ['TELEGRAM_BOT_TOKEN']
    )


@dataclass(frozen=True)
class Config:
    logging_level: int
    polling: PollingConfig
    redis: RedisConfig
    postgres: PostgresConfig
    discord: DiscordConfig
    telegram: TelegramConfig


def _load_config() -> Config:
    return Config(
        logging_level=logging.INFO,
        polling=PollingConfig(),
        redis=_load_redis_config(),
        postgres=_load_postgres_config(),
        discord=_load_discord_config(),
        telegram=_load_telegram_config(),

    )


CONFIG = _load_config()