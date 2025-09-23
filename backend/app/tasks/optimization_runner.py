"""Optimization job execution helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from .backtest_runner import JobCancelledError
from .enums import JobStatus
from .store import JobStore


@dataclass
class OptimizationJobPayload:
    """Normalized arguments for optimization jobs."""

    job_data: Dict[str, Any]


class OptimizationRunner:
    """Execute optimization jobs via the optimization service."""

    def __init__(self, store: JobStore, service_factory: Optional[Callable[[], Any]] = None):
        self._store = store
        self._service_factory = service_factory

    def run(
        self,
        job_id: str,
        payload: OptimizationJobPayload,
        cancel_requested: Callable[[], bool],
        progress: Callable[[float, Optional[str], Optional[int]], None],
        external_progress: Optional[Callable[[int, int], Any]] = None,
    ) -> None:
        try:
            if cancel_requested():
                raise JobCancelledError()

            self._store.update_status(job_id, JobStatus.RUNNING)
            total = int(payload.job_data.get("total_combinations") or 1)

            def update_progress(completed: int, total_steps: int) -> None:
                fraction = completed / total_steps if total_steps else 0.0
                progress(
                    fraction,
                    f"Completed {completed}/{total_steps} backtests",
                    total_steps,
                )
                if cancel_requested():
                    raise JobCancelledError()
                if external_progress:
                    external_progress(completed, total_steps)

            service = self._resolve_service()
            result = service.run_optimization(payload.job_data, update_progress)
            if result.get("success"):
                self._store.store_results(job_id, result)
                self._store.update_status(job_id, JobStatus.COMPLETED)
            else:
                self._store.update_status(
                    job_id,
                    JobStatus.FAILED,
                    error_message=result.get("error", "Optimization failed"),
                )
            progress(1.0, "Optimization completed", total)
        except JobCancelledError:
            self._store.update_status(job_id, JobStatus.CANCELLED)
        except Exception as exc:
            self._store.update_status(job_id, JobStatus.FAILED, error_message=str(exc))
            raise

    def _resolve_service(self):
        if self._service_factory:
            return self._service_factory()
        from backend.app.services.optimization_service import OptimizationService

        return OptimizationService()
