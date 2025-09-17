"""Database repository helpers for datasets."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from sqlalchemy.orm import Session

from backend.app.database.models import Dataset, get_session_factory
from .analysis import DatasetAnalysis


class DatasetRepository:
    """Encapsulates dataset persistence operations."""

    def __init__(self, session_factory: Optional[Callable[[], Session]] = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    def _session(self) -> Session:
        return self._session_factory()

    def create_dataset(
        self,
        *,
        file_path: Union[Path, str],
        file_name: str,
        file_size: int,
        analysis: DatasetAnalysis,
        name: Optional[str] = None,
        symbol: Optional[str] = None,
        exchange: Optional[str] = None,
        data_source: Optional[str] = None,
    ) -> Dataset:
        session = self._session()
        try:
            dataset = Dataset(
                name=name or file_name,
                filename=file_name,
                file_path=str(file_path),
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
                symbol=symbol,
                exchange=exchange,
                data_source=data_source,
                quality_checks=analysis.quality_checks,
            )
            session.add(dataset)
            session.commit()
            session.refresh(dataset)
            return dataset
        finally:
            session.close()

    def get_by_file_path(self, file_path: str) -> Optional[Dataset]:
        session = self._session()
        try:
            return (
                session.query(Dataset)
                .filter(Dataset.file_path == file_path)
                .first()
            )
        finally:
            session.close()

    def get(self, dataset_id: int) -> Optional[Dataset]:
        session = self._session()
        try:
            return session.query(Dataset).filter(Dataset.id == dataset_id).first()
        finally:
            session.close()

    def list(self, limit: int = 50) -> List[Dataset]:
        session = self._session()
        try:
            return (
                session.query(Dataset)
                .order_by(Dataset.created_at.desc())
                .limit(limit)
                .all()
            )
        finally:
            session.close()

    def delete(self, dataset_id: int) -> Optional[Dataset]:
        session = self._session()
        try:
            dataset = session.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                return None
            session.delete(dataset)
            session.commit()
            return dataset
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_quality_checks(
        self, dataset: Dataset, analysis: DatasetAnalysis
    ) -> Dataset:
        session = self._session()
        try:
            merged = session.merge(dataset)
            merged.quality_checks = analysis.quality_checks
            merged.data_quality_score = analysis.quality_score
            session.commit()
            session.refresh(merged)
            return merged
        finally:
            session.close()

    def touch_last_accessed(self, dataset: Dataset) -> None:
        session = self._session()
        try:
            merged = session.merge(dataset)
            merged.last_accessed = datetime.now(timezone.utc)
            session.commit()
        finally:
            session.close()

    @staticmethod
    def to_dict(dataset: Dataset, *, include_quality: bool = True) -> Dict[str, Any]:
        result = {
            "id": dataset.id,
            "name": dataset.name,
            "filename": dataset.filename
            or (Path(dataset.file_path).name if dataset.file_path else None),
            "file_path": dataset.file_path,
            "file_size": dataset.file_size,
            "rows_count": dataset.rows_count or dataset.rows,
            "columns": dataset.columns,
            "timeframe": dataset.timeframe,
            "start_date": dataset.start_date.isoformat()
            if dataset.start_date
            else None,
            "end_date": dataset.end_date.isoformat() if dataset.end_date else None,
            "missing_data_pct": dataset.missing_data_pct,
            "data_quality_score": dataset.data_quality_score,
            "has_gaps": dataset.has_gaps,
            "timezone": dataset.timezone,
            "symbol": dataset.symbol,
            "exchange": dataset.exchange,
            "data_source": dataset.data_source,
            "backtest_count": dataset.backtest_count,
            "created_at": dataset.created_at.isoformat()
            if dataset.created_at
            else None,
            "last_accessed": dataset.last_accessed.isoformat()
            if dataset.last_accessed
            else None,
        }
        if include_quality and dataset.quality_checks:
            result["quality_checks"] = dataset.quality_checks
        return result
