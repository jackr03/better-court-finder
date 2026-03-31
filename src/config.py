from dataclasses import dataclass


@dataclass(frozen=True)
class PollingConfig:
    interval: int = 300
    max_concurrent: int = 10
    max_retries: int = 3
    base_delay: float = 1.0

@dataclass(frozen=True)
class Config:
    polling: PollingConfig = PollingConfig()


CONFIG = Config()