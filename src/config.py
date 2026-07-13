import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class PollingConfig:
    interval: int = 300
    max_concurrent: int = 10
    max_retries: int = 3
    base_delay: float = 1.0


@dataclass(frozen=True)
class RedisConfig:
    host: str = 'localhost'
    port: int = 6379
    ttl: int = 600 # 2x PollingConfig.interval lets us survive a failed cycle
    namespace: str = 'bcf'


@dataclass(frozen=True)
class PostgresConfig:
    user: str
    password: str
    database: str
    host: str = 'localhost'
    port: int = 5432


def _load_postgres_config() -> PostgresConfig:
    return PostgresConfig(
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
        database=os.environ['POSTGRES_DB']
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
    logging_level = logging.INFO
    polling: PollingConfig = PollingConfig()
    redis: RedisConfig = RedisConfig()
    postgres: PostgresConfig = _load_postgres_config()
    telegram: TelegramConfig = _load_telegram_config()


CONFIG = Config()