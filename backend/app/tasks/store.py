"""Database access helpers for background jobs."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database.models import Backtest, BacktestJob, Dataset, get_session_factory
from .enums import JobStatus, JobType


class JobStore:
    """Encapsulates persistence for background jobs and results."""

    def __init__(self, session_factory: Optional[Callable[[], Session]] = None):
        self._session_factory = session_factory or get_session_factory()

    def _session(self) -> Session:
        return self._session_factory()

    def _coerce_job_id(self, job_id: str | int) -> int:
        if isinstance(job_id, int):
            return job_id
        try:
            return int(job_id)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid job id {job_id}") from exc

    @staticmethod
    def _serialize_dt(value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None

    @staticmethod
    def _serialize_job(job: BacktestJob) -> Dict[str, Any]:
        return {
            "id": job.id,
            "status": JobStatus(job.status),
            "strategy": job.strategy,
            "strategy_params": job.strategy_params or {},
            "engine_options": job.engine_options or {},
            "dataset_path": job.dataset_path,
            "progress": job.progress or 0.0,
            "current_step": job.current_step,
            "total_steps": job.total_steps,
            "created_at": JobStore._serialize_dt(job.created_at),
            "started_at": JobStore._serialize_dt(job.started_at),
            "completed_at": JobStore._serialize_dt(job.completed_at),
            "estimated_duration": job.estimated_duration,
            "actual_duration": job.actual_duration,
            "error_message": job.error_message,
        }

    def create_backtest_job(
        self,
        strategy: str,
        strategy_params: Optional[Dict[str, Any]],
        dataset_path: Optional[str],
        engine_options: Optional[Dict[str, Any]],
    ) -> str:
        session = self._session()
        try:
            job = BacktestJob(
                strategy=strategy,
                strategy_params=strategy_params or {},
                engine_options=engine_options or {},
                dataset_path=dataset_path,
                status=JobStatus.PENDING.value,
                progress=0.0,
            )
            session.add(job)
            session.commit()
            session.refresh(job)
            return str(job.id)
        finally:
            session.close()

    def create_optimization_job(self, job_data: Dict[str, Any]) -> str:
        session = self._session()
        try:
            job = BacktestJob(
                strategy=JobType.OPTIMIZATION.value,
                strategy_params=job_data.get("param_ranges") or {},
                engine_options=job_data.get("engine_options") or {},
                dataset_path=str(job_data.get("dataset_id")) if job_data.get("dataset_id") is not None else None,
                status=JobStatus.PENDING.value,
                progress=0.0,
                total_steps=job_data.get("total_combinations"),
                estimated_duration=job_data.get("estimated_duration"),
            )
            session.add(job)
            session.commit()
            session.refresh(job)
            return str(job.id)
        finally:
            session.close()

    def update_progress(
        self,
        job_id: str | int,
        progress: float,
        step: Optional[str],
        total_steps: Optional[int],
    ) -> None:
        session = self._session()
        try:
            job = session.get(BacktestJob, self._coerce_job_id(job_id))
            if not job:
                return
            job.progress = max(0.0, min(1.0, float(progress)))
            if step is not None:
                job.current_step = step
            if total_steps is not None:
                job.total_steps = total_steps
            session.commit()
        except Exception:
            session.rollback()
            return None
        finally:
            session.close()

    def update_status(
        self,
        job_id: str | int,
        status: JobStatus,
        *,
        error_message: Optional[str] = None,
        result_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        session = self._session()
        try:
            job = session.get(BacktestJob, self._coerce_job_id(job_id))
            if not job:
                return
            job.status = status.value
            if error_message is not None:
                job.error_message = error_message
            if result_data is not None:
                job.result_data = json.dumps(result_data)
            now = datetime.utcnow()
            if status is JobStatus.RUNNING and job.started_at is None:
                job.started_at = now
            elif status in JobStatus.TERMINAL:
                job.completed_at = now
                job.actual_duration = (job.completed_at - (job.started_at or now)).total_seconds()
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def store_results(self, job_id: str | int, result: Dict[str, Any]) -> None:
        session = self._session()
        try:
            job = session.get(BacktestJob, self._coerce_job_id(job_id))
            if not job:
                return
            job.result_data = json.dumps(result)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_job(self, job_id: str | int) -> Optional[Dict[str, Any]]:
        session = self._session()
        try:
            job = session.get(BacktestJob, self._coerce_job_id(job_id))
            if job is None:
                return None
            return self._serialize_job(job)
        finally:
            session.close()

    def get_job_results(self, job_id: str | int) -> Optional[Dict[str, Any]]:
        session = self._session()
        try:
            job = session.get(BacktestJob, self._coerce_job_id(job_id))
            if not job or job.result_data is None:
                return None
            return json.loads(job.result_data)
        finally:
            session.close()

    def delete_job(self, job_id: str | int) -> bool:
        session = self._session()
        try:
            job = session.get(BacktestJob, self._coerce_job_id(job_id))
            if not job:
                return False
            session.delete(job)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def list_jobs(
        self,
        *,
        job_type: Optional[JobType] = None,
        status: Optional[JobStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        session = self._session()
        try:
            query = session.query(BacktestJob)
            if job_type is JobType.OPTIMIZATION:
                query = query.filter(BacktestJob.strategy == JobType.OPTIMIZATION.value)
            elif job_type is JobType.BACKTEST:
                query = query.filter(BacktestJob.strategy != JobType.OPTIMIZATION.value)
            if status is not None:
                query = query.filter(BacktestJob.status == status.value)
            jobs = (
                query.order_by(BacktestJob.created_at.desc()).offset(offset).limit(limit).all()
            )
            return [self._serialize_job(job) for job in jobs]
        finally:
            session.close()

    def job_stats(self, job_type: Optional[JobType] = None) -> Dict[str, Any]:
        session = self._session()
        try:
            query = session.query(BacktestJob)
            if job_type is JobType.OPTIMIZATION:
                query = query.filter(BacktestJob.strategy == JobType.OPTIMIZATION.value)
            elif job_type is JobType.BACKTEST:
                query = query.filter(BacktestJob.strategy != JobType.OPTIMIZATION.value)
            status_counts = {
                row.status: row.count
                for row in session.query(
                    BacktestJob.status, func.count(BacktestJob.id).label("count")
                ).filter(query.whereclause if query.whereclause is not None else True)
                .group_by(BacktestJob.status)
                .all()
            }
            completed_jobs = (
                query.filter(
                    BacktestJob.status == JobStatus.COMPLETED.value,
                    BacktestJob.actual_duration.isnot(None),
                ).all()
            )
            avg_duration = (
                sum(job.actual_duration for job in completed_jobs if job.actual_duration)
                / len(completed_jobs)
                if completed_jobs
                else 0
            )
            return {
                "status_counts": status_counts,
                "total_jobs": sum(status_counts.values()),
                "average_completion_time_seconds": avg_duration,
            }
        finally:
            session.close()

    def create_backtest_record(
        self,
        *,
        strategy: str,
        strategy_params: Optional[Dict[str, Any]],
        result: Dict[str, Any],
        dataset_path: Optional[str],
        dataset_id: Optional[int],
    ) -> Optional[int]:
        session = self._session()
        try:
            dataset_ref = dataset_id
            if dataset_ref is None and dataset_path:
                target = Path(dataset_path).name.lower()
                for candidate in session.query(Dataset).all():
                    try:
                        if Path(candidate.file_path).name.lower() == target:
                            dataset_ref = candidate.id
                            break
                    except Exception:
                        continue
            backtest = Backtest(
                strategy_name=strategy,
                strategy_params=strategy_params or {},
                dataset_id=dataset_ref,
                status="completed",
                results=result,
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
            session.add(backtest)
            session.commit()
            session.refresh(backtest)
            return backtest.id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
