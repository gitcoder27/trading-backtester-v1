"""
Clear all rows from the `datasets` table while preserving other data and schema.

Context
-------
After experimenting, you may want to repopulate datasets based on the files
on disk (e.g., using `scripts/register_datasets.py`). This script removes
existing `Dataset` rows from the local SQLite database so you can start fresh.

What it does
------------
- Deletes all rows from the `datasets` table only.
- Optionally deletes the corresponding CSV files on disk when `--delete-files`
  is provided (OFF by default). Use with care.
- Does NOT drop tables or touch trades/backtests/jobs tables.

Safety tips
-----------
- Stop the backend server to avoid SQLite locks before running this.
- Consider backing up your DB first, e.g.:
    cp backend/database/backtester.db backend/database/backtester.db.bak

Usage
-----
From the project root and within your Python virtualenv:

    source venv/bin/activate
    python scripts/clear_datasets.py --force

Optional flags:
  --delete-files : Also remove CSV files referenced by the datasets (default: off)
  --verbose      : Print detailed progress
  --force        : Skip interactive confirmation prompt

Notes
-----
- This does not validate or fix references from other tables (e.g., Backtest.dataset_id).
  If you have existing backtests that reference old dataset IDs, analytics endpoints
  may not find dataset details after clearing. That's expected when resetting.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List
import sys

# Ensure project root is on sys.path so `backend` imports resolve when run directly
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.database.models import get_session_factory, Dataset, init_db
from backend.app.utils.path_utils import resolve_dataset_path


def delete_dataset_files(file_paths: List[str], verbose: bool = False) -> int:
    """Delete files from disk, resolving relative paths as needed.
    Returns the count of files removed.
    """
    removed = 0
    for fp in file_paths:
        # Try resolve_dataset_path for robust handling across OS/WSL
        resolved = resolve_dataset_path(fp) or (ROOT / fp).as_posix()
        try:
            p = Path(resolved)
            if p.exists():
                p.unlink()
                removed += 1
                if verbose:
                    print(f"Removed file: {p}")
            else:
                if verbose:
                    print(f"File not found (skip): {p}")
        except Exception as e:
            if verbose:
                print(f"Failed to remove {fp}: {e}")
    return removed


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clear rows from the datasets table.")
    parser.add_argument("--delete-files", action="store_true", help="Also delete referenced CSV files from disk")
    parser.add_argument("--verbose", action="store_true", help="Print detailed progress")
    parser.add_argument("--force", action="store_true", help="Skip interactive confirmation prompt")

    args = parser.parse_args(argv)

    # Ensure database and tables exist before querying
    init_db()

    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        total = db.query(Dataset).count()
        if total == 0:
            print("datasets table is already empty.")
            return 0

        # Gather file paths before deletion if needed
        file_paths: List[str] = []
        if args.delete_files:
            file_paths = [row.file_path for row in db.query(Dataset.file_path).all() if row.file_path]

        print(f"About to delete {total} dataset record(s).")
        if args.delete_files:
            print(f"Additionally will attempt to remove {len(file_paths)} file(s) from disk.")

        if not args.force:
            confirm = input("Type 'yes' to proceed: ").strip().lower()
            if confirm != "yes":
                print("Aborted.")
                return 1

        # Delete DB rows
        deleted = db.query(Dataset).delete(synchronize_session=False)
        db.commit()
        print(f"Deleted {deleted} dataset row(s) from DB.")

        removed = 0
        if args.delete_files and file_paths:
            removed = delete_dataset_files(file_paths, verbose=args.verbose)
            print(f"Removed {removed} file(s) from disk.")

        remaining = db.query(Dataset).count()
        if args.verbose:
            print(f"Remaining rows in datasets: {remaining}")

        print("Done.")
        return 0

    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())

