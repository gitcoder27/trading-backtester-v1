"""Pytest configuration for backend tests."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Ensure each test session uses an isolated SQLite database so that running
# the backend test suite never mutates the development database under
# backend/database/backtester.db.
# ---------------------------------------------------------------------------
_TEST_DB_DIR = Path(tempfile.mkdtemp(prefix="backtester_pytest_"))
_TEST_DB_PATH = _TEST_DB_DIR / "test.db"

# Point SQLAlchemy at the temporary database **before** backend modules are
# imported so they pick up the new connection information.
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"

# Clear the cached settings so the new DATABASE_URL is respected.
from backend.app.config import get_settings  # noqa: E402

get_settings.cache_clear()

# Initialise a fresh schema in the temporary database.
from backend.app.database.models import create_tables, get_engine  # noqa: E402

create_tables()


@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_database() -> None:
    """Dispose of the test database file when the test session ends."""

    try:
        yield
    finally:
        # Dispose any pooled connections before attempting to delete the file.
        try:
            engine = get_engine()
            engine.dispose()
        except Exception:
            pass

        if _TEST_DB_PATH.exists():
            _TEST_DB_PATH.unlink()
        if _TEST_DB_DIR.exists():
            try:
                _TEST_DB_DIR.rmdir()
            except OSError:
                # Directory not empty; leave it for inspection.
                pass
