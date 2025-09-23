"""Background job orchestration."""

from __future__ import annotations

import logging
import time
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Event, Lock, Timer
from typing import Any, Callable, Dict, Optional

from backend.app.config import get_settings
from backend.app.database.models import get_session_factory as _get_session_factory
from .backtest_runner import BacktestJobPayload, BacktestRunner, JobCancelledError
from .enums import JobStatus, JobType
from .optimization_runner import OptimizationJobPayload, OptimizationRunner
from .store import JobStore

logger = logging.getLogger(__name__)


class ProgressCallback:
    """Throttle persistence-heavy progress updates."""

    def __init__(self, job_id: str, job_runner: "JobRunner", *, min_interval: float = 1.0):
        self.job_id = job_id
        self.job_runner = job_runner
        self._min_interval = min_interval
        self._last_update = 0.0

    def __call__(
        self,
        progress: float,
        step: Optional[str] = None,
        total_steps: Optional[int] = None,
    ) -> None:
        now = time.time()
        if progress < 1.0 and (now - self._last_update) < self._min_interval:
            return
        self._last_update = now
        self.job_runner.update_job_progress(self.job_id, progress, step, total_steps)


class JobRunner:
    """Facade that coordinates background job execution and persistence."""

    def __init__(
        self,
        max_workers: Optional[int] = None,
        *,
        store: Optional[JobStore] = None,
        backtest_runner: Optional[BacktestRunner] = None,
        optimization_runner: Optional[OptimizationRunner] = None,
    ):
        settings = get_settings()
        pool_size = max_workers or settings.job_runner_max_workers
        self._executor = ThreadPoolExecutor(
            max_workers=pool_size,
            thread_name_prefix="job-runner",
        )
        self._store = store or JobStore()
        self._backtest_runner = backtest_runner or BacktestRunner(self._store)
        self._optimization_runner = (
            optimization_runner or OptimizationRunner(self._store)
        )
        self._active_jobs: Dict[str, Future] = {}
        self._cancellations: Dict[str, Event] = {}
        self._lock = Lock()

    @property
    def executor(self) -> ThreadPoolExecutor:
        return self._executor

    @property
    def active_jobs(self) -> Dict[str, Future]:
        return self._active_jobs

    def submit_job(
        self,
        *,
        job_type: JobType | str = JobType.BACKTEST,
        job_data: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int], Any]] = None,
        strategy: Optional[str] = None,
        strategy_params: Optional[Dict[str, Any]] = None,
        dataset_path: Optional[str] = None,
        dataset_id: Optional[int] = None,
        csv_bytes: Optional[bytes] = None,
        engine_options: Optional[Dict[str, Any]] = None,
    ) -> str:
        normalized_type = self._normalize_job_type(job_type)
        if normalized_type is JobType.BACKTEST:
            if not strategy:
                raise ValueError("strategy is required for backtest jobs")
            job_id = self._store.create_backtest_job(
                strategy=strategy,
                strategy_params=strategy_params,
                dataset_path=dataset_path,
                engine_options=engine_options,
            )
            payload = BacktestJobPayload(
                strategy=strategy,
                strategy_params=strategy_params or {},
                dataset_path=dataset_path,
                dataset_id=dataset_id,
                csv_bytes=csv_bytes,
                engine_options=engine_options or {},
            )
            cancel_event = Event()
            start_event = Event()
            with self._lock:
                self._cancellations[job_id] = cancel_event
            future = self._executor.submit(
                self._run_backtest_job,
                job_id,
                payload,
                cancel_event,
                start_event,
            )
        elif normalized_type is JobType.OPTIMIZATION:
            if job_data is None:
                raise ValueError("job_data required for optimization jobs")
            job_id = self._store.create_optimization_job(job_data)
            payload = OptimizationJobPayload(job_data=job_data)
            cancel_event = Event()
            start_event = Event()
            with self._lock:
                self._cancellations[job_id] = cancel_event
            future = self._executor.submit(
                self._run_optimization_job,
                job_id,
                payload,
                cancel_event,
                progress_callback,
                start_event,
            )
        else:
            raise ValueError(f"Unknown job type: {job_type}")

        with self._lock:
            self._active_jobs[job_id] = future
        Timer(0.01, start_event.set).start()
        logger.info("Submitted %s job %s", normalized_type.value, job_id)
        return job_id

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._store.get_job(job_id)

    def get_job_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        job = self._store.get_job(job_id)
        if not job or job["status"] is not JobStatus.COMPLETED:
            return None
        return self._store.get_job_results(job_id)

    def cancel_job(self, job_id: str) -> bool:
        with self._lock:
            event = self._cancellations.get(job_id)
            if not event:
                return False
            event.set()
        self._store.update_status(job_id, JobStatus.CANCELLED)
        logger.info("Cancellation requested for job %s", job_id)
        return True

    def delete_job(self, job_id: str) -> bool:
        with self._lock:
            event = self._cancellations.pop(job_id, None)
            if event:
                event.set()
            self._active_jobs.pop(job_id, None)
        return self._store.delete_job(job_id)

    def job_stats(self) -> Dict[str, Any]:
        return self._store.job_stats()

    def list_jobs(
        self,
        limit: int = 50,
        *,
        job_type: Optional[JobType | str] = None,
        status: Optional[JobStatus | str] = None,
        offset: int = 0,
    ) -> list[Dict[str, Any]]:
        normalized_type = (
            self._normalize_job_type(job_type) if job_type is not None else None
        )
        normalized_status = (
            JobStatus(status) if isinstance(status, str) else status
        )
        return self._store.list_jobs(
            job_type=normalized_type,
            status=normalized_status,
            limit=limit,
            offset=offset,
        )

    def get_job_stats(self, job_type: Optional[JobType | str] = None) -> Dict[str, Any]:
        normalized_type = (
            self._normalize_job_type(job_type) if job_type is not None else None
        )
        return self._store.job_stats(normalized_type)

    def update_job_progress(
        self,
        job_id: str,
        progress: float,
        step: Optional[str] = None,
        total_steps: Optional[int] = None,
    ) -> None:
        self._store.update_progress(job_id, progress, step, total_steps)

    def is_cancelled(self, job_id: str) -> bool:
        with self._lock:
            event = self._cancellations.get(job_id)
            return event.is_set() if event else False

    def shutdown(self, wait: bool = True) -> None:
        logger.info("Shutting down job runner")
        with self._lock:
            for event in self._cancellations.values():
                event.set()
            self._active_jobs.clear()
            self._cancellations.clear()
        self._executor.shutdown(wait=wait)

    def _run_backtest_job(
        self,
        job_id: str,
        payload: BacktestJobPayload,
        cancel_event: Event,
        start_event: Event,
    ) -> None:
        start_event.wait()
        progress = ProgressCallback(job_id, self)
        try:
            self._backtest_runner.run(job_id, payload, cancel_event.is_set, progress)
        except JobCancelledError:
            logger.info("Backtest job %s cancelled", job_id)
        except Exception:
            logger.exception("Backtest job %s failed", job_id)
            raise
        finally:
            self._cleanup(job_id)

    def _run_optimization_job(
        self,
        job_id: str,
        payload: OptimizationJobPayload,
        cancel_event: Event,
        external_progress: Optional[Callable[[int, int], Any]],
        start_event: Event,
    ) -> None:
        start_event.wait()
        progress = ProgressCallback(job_id, self)
        try:
            self._optimization_runner.run(
                job_id,
                payload,
                cancel_event.is_set,
                progress,
                external_progress,
            )
        except JobCancelledError:
            logger.info("Optimization job %s cancelled", job_id)
        except Exception:
            logger.exception("Optimization job %s failed", job_id)
            raise
        finally:
            self._cleanup(job_id)

    def _cleanup(self, job_id: str) -> None:
        with self._lock:
            self._active_jobs.pop(job_id, None)
            self._cancellations.pop(job_id, None)

    @staticmethod
    def _normalize_job_type(job_type: JobType | str) -> JobType:
        if isinstance(job_type, JobType):
            return job_type
        return JobType(job_type)


_job_runner: Optional[JobRunner] = None

# Backwards compatibility hook for tests that patch get_session_factory
get_session_factory = _get_session_factory


def get_job_runner() -> JobRunner:
    global _job_runner
    if _job_runner is None:
        _job_runner = JobRunner()
    return _job_runner


def shutdown_job_runner() -> None:
    global _job_runner
    if _job_runner is not None:
        _job_runner.shutdown()
        _job_runner = None
