"""Application configuration and logging helpers."""

from __future__ import annotations

import logging
import logging.config
from functools import lru_cache
from pathlib import Path
from typing import List, Union

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(
        "sqlite:///./backend/database/backtester.db",
        env="DATABASE_URL",
        description="SQLAlchemy database URL",
    )
    log_level: str = Field("INFO", env="LOG_LEVEL")
    job_runner_max_workers: int = Field(2, env="JOB_RUNNER_MAX_WORKERS")
    cors_origins: Union[List[str], str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:5175",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://127.0.0.1:5175",
        ],
        env="CORS_ORIGINS",
    )
    data_dir: Path = Field(Path("data/market_data"), env="DATA_DIR")
    gzip_minimum_size: int = Field(500, env="GZIP_MINIMUM_SIZE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @validator("cors_origins", pre=True)
    def _split_origins(cls, value):  # type: ignore[override]
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @validator("log_level")
    def _normalize_log_level(cls, value: str) -> str:  # type: ignore[override]
        return value.upper()

    def __init__(self, **values):
        super().__init__(**values)
        if isinstance(self.cors_origins, str):
            object.__setattr__(
                self,
                "cors_origins",
                [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()],
            )


@lru_cache()
def get_settings() -> Settings:
    """Return application settings (cached)."""

    return Settings()


def configure_logging(settings: Settings) -> None:
    """Configure structured logging based on settings."""

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            }
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            }
        },
        "root": {
            "handlers": ["default"],
            "level": settings.log_level,
        },
    }
    logging.config.dictConfig(logging_config)


__all__ = ["Settings", "configure_logging", "get_settings"]
