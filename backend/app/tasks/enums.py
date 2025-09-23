"""Enumerations for background job infrastructure."""

from __future__ import annotations

from enum import Enum


class JobType(str, Enum):
    """Supported background job types."""

    BACKTEST = "backtest"
    OPTIMIZATION = "optimization"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class JobStatus(str, Enum):
    """Lifecycle states for background jobs."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    TERMINAL = {COMPLETED, FAILED, CANCELLED}

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value

    @property
    def is_finished(self) -> bool:
        """Return ``True`` when the status represents a terminal state."""

        return self in self.TERMINAL
