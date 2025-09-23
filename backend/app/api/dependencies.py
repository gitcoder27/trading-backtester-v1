"""Shared API dependencies for FastAPI routers."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from backend.app.services.dataset_service import DatasetService
from backend.app.services.optimization_service import OptimizationService
from backend.app.tasks import JobRunner, get_job_runner


@lru_cache()
def _dataset_service() -> DatasetService:
    return DatasetService()


def get_dataset_service() -> DatasetService:
    """Return a cached dataset service instance."""

    return _dataset_service()


def get_job_runner_dependency() -> JobRunner:
    """Return the global job runner."""

    return get_job_runner()


def get_optimization_service(
    dataset_service: DatasetService = Depends(get_dataset_service),
) -> OptimizationService:
    """Create an optimization service sharing dataset infrastructure."""

    return OptimizationService(
        dataset_repository=dataset_service.repository,
        storage=dataset_service.storage,
    )
