"""Pydantic schemas for job API responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.app.tasks import JobStatus


class JobSummary(BaseModel):
    id: int
    status: JobStatus
    progress: Optional[float] = None
    current_step: Optional[str] = None
    total_steps: Optional[int] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class JobListResponse(BaseModel):
    success: bool = True
    jobs: List[JobSummary]
    count: int


class JobStatusResponse(BaseModel):
    success: bool
    job: JobSummary


class JobResultResponse(BaseModel):
    success: bool
    job_id: str
    results: Optional[Dict[str, Any]] = None
    status: Optional[JobStatus] = None
    error: Optional[str] = Field(default=None, description="Error message when job failed")
