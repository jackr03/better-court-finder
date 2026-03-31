from dataclasses import dataclass


@dataclass(frozen=True)
class PollingConfig:
    interval: int = 300
    max_concurrent: int = 10

@dataclass(frozen=True)
class Config:
    polling: PollingConfig = PollingConfig()


CONFIG = Config()