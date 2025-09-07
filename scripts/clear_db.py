"""
Clear all data from the SQLite database while keeping the schema intact.

Usage (from repo root, with venv activated):
    python scripts/clear_db.py

What it does:
- Disables foreign keys for the session
- Deletes rows from all tables in reverse dependency order
- Attempts to reset AUTOINCREMENT counters (sqlite_sequence) if present
- Re-enables foreign keys

This script is idempotent and safe to run multiple times. It does NOT drop tables.
"""

from sqlalchemy import text
from pathlib import Path
import sys

# Ensure project root is on sys.path so `backend` package imports resolve
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.database.models import Base, get_engine


def clear_all_data() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        # Disable FKs for bulk deletes in SQLite session
        conn.exec_driver_sql("PRAGMA foreign_keys=OFF;")

        # Delete in reverse dependency order
        for table in reversed(list(Base.metadata.sorted_tables)):
            conn.execute(table.delete())

        # Reset AUTOINCREMENT counters if table exists
        try:
            conn.exec_driver_sql("DELETE FROM sqlite_sequence;")
        except Exception:
            # sqlite_sequence doesn't exist if no AUTOINCREMENT used; ignore
            pass

        # Re-enable FKs
        conn.exec_driver_sql("PRAGMA foreign_keys=ON;")


def main() -> None:
    clear_all_data()
    print("Database data cleared. Schema preserved.")


if __name__ == "__main__":
    main()
