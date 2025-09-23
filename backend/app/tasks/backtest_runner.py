"""Backtest job execution helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from backend.app.services.backtest_service import BacktestService

from .enums import JobStatus
from .store import JobStore


class JobCancelledError(RuntimeError):
    """Raised when a job receives a cancellation request."""


@dataclass
class BacktestJobPayload:
    """Normalized parameters required to execute a backtest."""

    strategy: str
    strategy_params: Dict[str, Any]
    dataset_path: Optional[str]
    dataset_id: Optional[int]
    csv_bytes: Optional[bytes]
    engine_options: Dict[str, Any]


class BacktestRunner:
    """Execute a backtest job while persisting status and progress."""

    def __init__(self, store: JobStore, service: Optional[BacktestService] = None):
        self._store = store
        self._service = service or BacktestService()

    def run(
        self,
        job_id: str,
        payload: BacktestJobPayload,
        cancel_requested: Callable[[], bool],
        progress: Callable[[float, Optional[str], Optional[int]], None],
    ) -> None:
        try:
            if cancel_requested():
                raise JobCancelledError()

            self._store.update_status(job_id, JobStatus.RUNNING)
            steps = 5
            progress(0.1, "Loading strategy", steps)
            self._ensure_not_cancelled(cancel_requested)

            progress(0.2, "Loading data", steps)
            self._ensure_not_cancelled(cancel_requested)

            def engine_progress(value: float, step: Optional[str] = None) -> None:
                scaled = 0.3 + (value * 0.5)
                progress(min(scaled, 0.8), step or "Running backtest", steps)
                self._ensure_not_cancelled(cancel_requested)

            result = self._service.run_backtest(
                strategy=payload.strategy,
                strategy_params=payload.strategy_params,
                dataset_path=payload.dataset_path,
                csv_bytes=payload.csv_bytes,
                engine_options=payload.engine_options,
                progress_callback=engine_progress,
            )

            self._ensure_not_cancelled(cancel_requested)
            progress(0.9, "Finalizing results", steps)

            if result.get("success"):
                self._store.create_backtest_record(
                    strategy=payload.strategy,
                    strategy_params=payload.strategy_params,
                    result=result,
                    dataset_path=payload.dataset_path,
                    dataset_id=payload.dataset_id,
                )

            self._store.store_results(job_id, result)
            self._store.update_status(job_id, JobStatus.COMPLETED)
            progress(1.0, "Completed", steps)
        except JobCancelledError:
            self._store.update_status(job_id, JobStatus.CANCELLED)
        except Exception as exc:
            self._store.update_status(job_id, JobStatus.FAILED, error_message=str(exc))
            raise

    @staticmethod
    def _ensure_not_cancelled(cancel_requested: Callable[[], bool]) -> None:
        if cancel_requested():
            raise JobCancelledError()
