from dataclasses import dataclass


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
    ttl: int = 330


@dataclass(frozen=True)
class Config:
    polling: PollingConfig = PollingConfig()
    redis: RedisConfig = RedisConfig()


CONFIG = Config()