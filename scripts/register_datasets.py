"""
Register existing CSV market data files into the local SQLite database.

Why this exists
----------------
During development you may already have historical CSV files in the
`data/` folder. The normal UI flow uploads a CSV and creates a
`Dataset` record in the DB. After clearing the DB, you likely don't want to
re-upload large files one-by-one. This standalone script scans the filesystem
and inserts `Dataset` rows that point to the CSVs already on disk.

What it does
------------
- Recursively scans one or more directories (default: `data/`) for
  `*.csv` files.
- Analyzes each CSV via the shared `DatasetAnalyzer` to populate
  metadata (rows, timeframe, columns, quality, etc.).
- Inserts a `Dataset` row for each file that is not already registered.
- Skips files already present in the DB (by exact `file_path`).

What it does NOT do
-------------------
- It does not upload files or copy/move data — it only references existing
  files on disk.
- It does not drop or modify tables; only inserts `Dataset` rows.

Usage
-----
From the project root and within your Python virtualenv:

    source venv/bin/activate
    python scripts/register_datasets.py \
        --dir data \
        --dir data \
        --pattern "*.csv" \
        --verbose

Optional flags:
  --dry-run   : Analyze and show which datasets would be registered, but don't write to DB
  --max N     : Limit how many files to process (helps testing)
  --pattern   : Glob pattern (default: *.csv)
  --dir PATH  : Directory to scan (can provide multiple)
  --verbose   : Print detailed progress

Notes
-----
- Always stop the backend server before bulk insert to avoid SQLite locks.
- Consider making a backup first: `cp backend/database/backtester.db backend/database/backtester.db.bak`.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable, List, Tuple
import sys

# Ensure project root is on sys.path so `backend` imports resolve when run directly
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.database.models import get_session_factory, Dataset
from backend.app.services.dataset_service import DatasetService


def iter_csv_files(dirs: Iterable[Path], pattern: str = "*.csv") -> Iterable[Path]:
    """Yield CSV files recursively from the given directories."""
    seen: set[Path] = set()
    for d in dirs:
        if not d.exists():
            continue
        for path in d.rglob(pattern):
            if path.is_file() and path.suffix.lower() == ".csv":
                # Normalize to relative path where possible for stable DB entries
                try:
                    rel = path.relative_to(ROOT)
                except ValueError:
                    rel = path
                if rel not in seen:
                    seen.add(rel)
                    yield rel


def path_for_db(p: Path) -> str:
    """Return a file_path string suitable for storing in DB.
    Prefer a POSIX-style relative path from repo root if under the project; else absolute.
    """
    try:
        rel = p.relative_to(ROOT)
        return rel.as_posix()
    except ValueError:
        # Outside repo root; store absolute POSIX path
        return p.resolve().as_posix()


def is_already_registered(db_session, file_path_str: str) -> bool:
    """Check if a dataset with the same file_path already exists."""
    return db_session.query(Dataset).filter(Dataset.file_path == file_path_str).first() is not None


def register_file(service: DatasetService, db_session, csv_path: Path, verbose: bool = False) -> Tuple[bool, str]:
    """Analyze CSV and insert a Dataset row. Returns (created, message)."""
    file_path_str = path_for_db(csv_path)

    if is_already_registered(db_session, file_path_str):
        return False, f"SKIP already registered: {file_path_str}"

    abs_path = (ROOT / file_path_str).resolve() if not csv_path.is_absolute() else csv_path
    if not abs_path.exists():
        return False, f"MISSING on disk: {abs_path}"

    # Analyze using shared analyzer
    analysis = service.analyzer.analyze(abs_path)

    # Build Dataset row
    file_size = os.path.getsize(abs_path)
    name = csv_path.stem
    filename = csv_path.name

    dataset = Dataset(
        name=name,
        filename=filename,
        file_path=file_path_str,
        file_size=file_size,
        rows_count=analysis.rows_count,
        columns=analysis.columns,
        timeframe=analysis.timeframe,
        start_date=analysis.start_date,
        end_date=analysis.end_date,
        missing_data_pct=analysis.missing_data_pct,
        data_quality_score=analysis.quality_score,
        has_gaps=analysis.has_gaps,
        timezone=analysis.timezone,
        # Optional metadata left as None by default: symbol, exchange, data_source
        quality_checks=analysis.quality_checks,
    )

    db_session.add(dataset)
    db_session.commit()
    if verbose:
        db_session.refresh(dataset)
    return True, f"ADDED dataset id={getattr(dataset, 'id', '?')} from {file_path_str}"


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register existing CSV datasets into the local DB.")
    parser.add_argument(
        "--dir",
        dest="dirs",
        action="append",
        default=["data"],
        help="Directory to scan (can be provided multiple times). Defaults to data.",
    )
    parser.add_argument("--pattern", default="*.csv", help="Glob pattern to match files (default: *.csv)")
    parser.add_argument("--max", dest="max_files", type=int, default=0, help="Limit how many files to process (0 = no limit)")
    parser.add_argument("--dry-run", action="store_true", help="Analyze and report but do not write to DB")
    parser.add_argument("--verbose", action="store_true", help="Print detailed progress")

    args = parser.parse_args(argv)

    dirs = [Path(d) if os.path.isabs(d) else ROOT / d for d in args.dirs]
    files = list(iter_csv_files(dirs, args.pattern))
    if args.max_files and len(files) > args.max_files:
        files = files[: args.max_files]

    if not files:
        print("No CSV files found. Checked:")
        for d in dirs:
            print(f"  - {d}")
        return 0

    print(f"Found {len(files)} CSV files to consider.")
    if args.dry_run:
        print("Dry run: no changes will be made to the database.")

    # Prepare services
    SessionLocal = get_session_factory()
    service = DatasetService()
    created = 0
    skipped = 0
    missing = 0
    errors: List[str] = []

    db = SessionLocal()
    try:
        for csv_rel in files:
            if args.verbose:
                print(f"Processing: {csv_rel}")
            try:
                if args.dry_run:
                    # Simulate analysis and registration decision
                    file_path_str = path_for_db(csv_rel)
                    if is_already_registered(db, file_path_str):
                        skipped += 1
                        if args.verbose:
                            print(f"  -> already registered: {file_path_str}")
                        continue
                    abs_path = (ROOT / file_path_str).resolve() if not csv_rel.is_absolute() else csv_rel
                    if not abs_path.exists():
                        missing += 1
                        print(f"  -> missing on disk: {abs_path}")
                        continue
                    # Analyze only for reporting context
                    analysis = service.analyzer.analyze(abs_path)
                    print(
                        f"  -> would add: rows={analysis.rows_count} timeframe={analysis.timeframe} path={file_path_str}"
                    )
                    created += 1
                else:
                    ok, msg = register_file(service, db, csv_rel, verbose=args.verbose)
                    if ok:
                        created += 1
                    else:
                        if msg.startswith("MISSING"):
                            missing += 1
                        else:
                            skipped += 1
                    if args.verbose:
                        print(f"  -> {msg}")
            except Exception as e:
                errors.append(f"{csv_rel}: {e}")
                if args.verbose:
                    print(f"  !! error: {e}")
    finally:
        db.close()

    print("\nSummary:")
    print(f"  Created: {created}")
    print(f"  Skipped: {skipped}")
    print(f"  Missing: {missing}")
    if errors:
        print(f"  Errors: {len(errors)} (see below)")
        for line in errors:
            print(f"    - {line}")

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
