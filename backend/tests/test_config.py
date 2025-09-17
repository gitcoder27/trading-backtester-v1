"""Tests for application configuration helpers."""

import logging

from backend.app.config import Settings, configure_logging


def test_settings_parse_cors(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://a.com,http://b.com")
    settings = Settings()
    assert settings.cors_origins == ["http://a.com", "http://b.com"]


def test_configure_logging_sets_level(monkeypatch):
    settings = Settings(log_level="DEBUG")
    configure_logging(settings)
    logger = logging.getLogger("backend.app.config")
    assert logger.isEnabledFor(logging.DEBUG)
