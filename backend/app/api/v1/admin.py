"""Administrative maintenance endpoints for the trading backtester."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from backend.app.config import get_settings
from backend.app.database.models import (
    Backtest,
    BacktestJob,
    BacktestMetrics,
    Dataset,
    Trade,
    get_session_factory,
)
from backend.app.services.datasets.storage import DatasetStorage


router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _safe_delete_file(storage: DatasetStorage, file_path: str | None) -> None:
    if not file_path:
        return
    try:
        storage.delete(file_path)
    except FileNotFoundError:
        # File already removed; ignore.
        pass
    except Exception:
        # Swallow unexpected errors to avoid failing the operation because of a single file.
        pass


@router.delete("/datasets", response_model=Dict[str, Any])
async def clear_datasets() -> Dict[str, Any]:
    """Remove all dataset records and associated stored files."""

    SessionLocal = get_session_factory()
    db = SessionLocal()
    storage = DatasetStorage(get_settings().data_dir)

    try:
        datasets = db.query(Dataset).all()
        deleted_files = 0
        for dataset in datasets:
            if dataset.file_path:
                _safe_delete_file(storage, dataset.file_path)
                deleted_files += 1

        deleted_records = db.query(Dataset).delete(synchronize_session=False)
        db.commit()

        return {
            "success": True,
            "deleted_records": int(deleted_records),
            "deleted_files": deleted_files,
            "message": f"Removed {deleted_records} datasets",
        }
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear datasets: {exc}") from exc
    finally:
        db.close()


@router.delete("/backtests", response_model=Dict[str, Any])
async def clear_backtests() -> Dict[str, Any]:
    """Remove all backtest records and related analytics artifacts."""

    SessionLocal = get_session_factory()
    db = SessionLocal()

    try:
        trades_deleted = db.query(Trade).delete(synchronize_session=False)
        metrics_deleted = db.query(BacktestMetrics).delete(synchronize_session=False)
        backtests_deleted = db.query(Backtest).delete(synchronize_session=False)

        # Reset dataset backtest counters to keep metadata consistent.
        db.query(Dataset).update({Dataset.backtest_count: 0})

        db.commit()

        return {
            "success": True,
            "deleted_trades": int(trades_deleted or 0),
            "deleted_metrics": int(metrics_deleted or 0),
            "deleted_backtests": int(backtests_deleted or 0),
            "message": "All backtests and associated data removed",
        }
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear backtests: {exc}") from exc
    finally:
        db.close()


@router.delete("/jobs", response_model=Dict[str, Any])
async def clear_jobs() -> Dict[str, Any]:
    """Remove all backtest jobs."""

    SessionLocal = get_session_factory()
    db = SessionLocal()

    try:
        jobs_deleted = db.query(BacktestJob).delete(synchronize_session=False)
        db.commit()

        return {
            "success": True,
            "deleted_jobs": int(jobs_deleted or 0),
            "message": "Backtest job queue cleared",
        }
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear jobs: {exc}") from exc
    finally:
        db.close()
