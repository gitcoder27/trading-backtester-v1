"""
Job management API endpoints for background backtests
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional, Dict, Any
import json

from backend.app.api.dependencies import get_dataset_service, get_job_runner_dependency
from backend.app.schemas.backtest import BacktestRequest
from backend.app.schemas.job import JobListResponse, JobResultResponse, JobStatusResponse
from backend.app.database.models import init_db
from backend.app.services.dataset_service import DatasetService
from backend.app.tasks import JobStatus, JobRunner

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])

# Initialize database on startup
init_db()

@router.get("/stats", response_model=Dict[str, Any])
async def get_job_stats(job_runner: JobRunner = Depends(get_job_runner_dependency)):
    """
    Get statistics about job execution.
    Note: Declared before dynamic `/{job_id}` routes to avoid shadowing
    that can lead to 422 errors when requesting `/stats`.
    """
    raw_stats = job_runner.job_stats()
    status_counts = raw_stats.get("status_counts", {}) if isinstance(raw_stats, dict) else {}

    stats = {
        "total_jobs": raw_stats.get("total_jobs", 0) if isinstance(raw_stats, dict) else 0,
        "pending": status_counts.get(JobStatus.PENDING.value, 0),
        "running": status_counts.get(JobStatus.RUNNING.value, 0),
        "completed": status_counts.get(JobStatus.COMPLETED.value, 0),
        "failed": status_counts.get(JobStatus.FAILED.value, 0),
        "cancelled": status_counts.get(JobStatus.CANCELLED.value, 0),
        "average_completion_time_seconds": raw_stats.get("average_completion_time_seconds") if isinstance(raw_stats, dict) else None,
    }

    return {"success": True, "stats": stats}

@router.post("/", response_model=Dict[str, Any])
async def submit_backtest_job(
    request: BacktestRequest,
    job_runner: JobRunner = Depends(get_job_runner_dependency),
    dataset_service: DatasetService = Depends(get_dataset_service),
):
    """
    Submit a backtest job for background execution
    Returns immediately with job ID for status tracking
    """
    try:
        # Convert Pydantic model to dict for service
        engine_options = request.engine_options.model_dump() if request.engine_options else {}
        # Bridge naming differences: map daily_profit_target -> daily_target for engine
        try:
            use_daily = engine_options.get('use_daily_profit_target', True)
            if not use_daily:
                engine_options.pop('daily_target', None)
                if 'daily_profit_target' in engine_options:
                    engine_options['daily_profit_target'] = None
            else:
                if 'daily_profit_target' in engine_options and 'daily_target' not in engine_options:
                    engine_options['daily_target'] = engine_options.get('daily_profit_target')
        except Exception:
            pass
        
        # Resolve dataset path from dataset ID if needed
        dataset_path = request.dataset_path
        dataset_id = int(request.dataset) if request.dataset else None
        if dataset_id and not dataset_path:
            try:
                dataset_info = dataset_service.get_dataset_quality(dataset_id)
            except ValueError as exc:
                raise HTTPException(status_code=404, detail=str(exc))
            dataset_meta = dataset_info['dataset']
            candidate_path = dataset_meta.get('file_path')
            if candidate_path:
                resolved = dataset_service.storage.resolve(candidate_path)
                if not resolved.exists():
                    raise HTTPException(status_code=404, detail="Dataset file not found on disk")
                dataset_path = str(resolved)

        if not dataset_path:
            raise HTTPException(status_code=400, detail="Either dataset or dataset_path must be provided")
        
        # Resolve numeric strategy ID to module.class path by DB ID (not list index)
        strategy_path = request.strategy
        if request.strategy.isdigit():
            from backend.app.services.strategy_service import StrategyRegistry
            strategy_registry = StrategyRegistry()
            strategy_id = int(request.strategy)
            try:
                strategy_info = strategy_registry.get_strategy_metadata(strategy_id)
            except Exception:
                raise HTTPException(status_code=404, detail=f"Strategy with ID {strategy_id} not found")
            # Combine module_path and class_name for BacktestService
            strategy_path = f"{strategy_info['module_path']}.{strategy_info['class_name']}"
        
        # Submit job
        job_id = job_runner.submit_job(
            strategy=strategy_path,
            strategy_params=request.strategy_params,
            dataset_path=dataset_path,
            dataset_id=int(request.dataset) if request.dataset else None,
            engine_options=engine_options
        )
        
        return {
            "success": True,
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "message": "Job submitted for background execution"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: int,
    job_runner: JobRunner = Depends(get_job_runner_dependency),
):
    """
    Get the status and details of a specific job
    """
    try:
        job = job_runner.get_job_status(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return {"success": True, "job": job}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.post("/upload", response_model=Dict[str, Any])
async def submit_backtest_job_with_upload(
    file: UploadFile = File(...),
    strategy: str = Form(...),
    strategy_params: str = Form(default="{}"),
    engine_options: str = Form(default="{}"),
    job_runner: JobRunner = Depends(get_job_runner_dependency),
):
    """
    Submit a backtest job with uploaded CSV data for background execution
    """
    try:
        # Parse JSON parameters
        try:
            strategy_params_dict = json.loads(strategy_params)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON in strategy_params: {e}")
        
        try:
            engine_options_dict = json.loads(engine_options)
            # Bridge naming differences for upload as well
            use_daily = engine_options_dict.get('use_daily_profit_target', True)
            if not use_daily:
                engine_options_dict.pop('daily_target', None)
                if 'daily_profit_target' in engine_options_dict:
                    engine_options_dict['daily_profit_target'] = None
            else:
                if 'daily_profit_target' in engine_options_dict and 'daily_target' not in engine_options_dict:
                    engine_options_dict['daily_target'] = engine_options_dict.get('daily_profit_target')
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON in engine_options: {e}")
        
        # Read uploaded file
        csv_bytes = await file.read()
        
        # Submit job
        job_id = job_runner.submit_job(
            strategy=strategy,
            strategy_params=strategy_params_dict,
            csv_bytes=csv_bytes,
            engine_options=engine_options_dict
        )
        
        return {
            "success": True,
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "message": "Job submitted for background execution"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status_detail(
    job_id: int,
    job_runner: JobRunner = Depends(get_job_runner_dependency),
):
    """
    Get the current status and progress of a background job
    """
    try:
        status = job_runner.get_job_status(job_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {"success": True, "job": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.get("/{job_id}/results", response_model=JobResultResponse)
async def get_job_results(
    job_id: int,
    job_runner: JobRunner = Depends(get_job_runner_dependency),
):
    """
    Get the results of a completed background job
    """
    try:
        # First check if job exists and is completed
        status = job_runner.get_job_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if status["status"] != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=400, 
                detail=f"Job is not completed yet. Current status: {status['status']}"
            )
        
        # Get results
        results = job_runner.get_job_results(job_id)
        if not results:
            raise HTTPException(status_code=404, detail="Job results not found")
        
        return {
            "success": True,
            "job_id": str(job_id),
            "status": status["status"],
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job results: {str(e)}")


@router.post("/{job_id}/cancel", response_model=Dict[str, Any])
async def cancel_job(
    job_id: int,
    job_runner: JobRunner = Depends(get_job_runner_dependency),
):
    """
    Cancel a running background job
    """
    try:
        # Check if job exists
        status = job_runner.get_job_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if status["status"] in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel job with status: {status['status']}"
            )
        
        # Attempt to cancel
        cancelled = job_runner.cancel_job(job_id)
        
        if cancelled:
            return {
                "success": True,
                "message": f"Cancellation requested for job {job_id}",
                "job_id": job_id
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to cancel job")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    limit: Optional[int] = 50,
    page: Optional[int] = None,
    size: Optional[int] = None,
    sort: Optional[str] = None,
    order: Optional[str] = None,
    job_runner: JobRunner = Depends(get_job_runner_dependency),
):
    """
    List recent background jobs with their status
    """
    effective_limit = limit or size or 50
    effective_limit = max(1, min(100, effective_limit))

    jobs = job_runner.list_jobs(limit=effective_limit)
    stats = job_runner.job_stats()

    return {
        "success": True,
        "jobs": jobs,
        "count": len(jobs),
        "total": stats.get("total_jobs", len(jobs)),
        "limit": effective_limit,
        "page": page or 1,
        "size": effective_limit,
        "sort": sort,
        "order": order,
    }

# Alias without trailing slash for clients that call /api/v1/jobs
@router.get("", response_model=JobListResponse)
async def list_jobs_no_slash(limit: int = 50, job_runner: JobRunner = Depends(get_job_runner_dependency)):
    return await list_jobs(limit=limit, job_runner=job_runner)


@router.delete("/{job_id}", response_model=Dict[str, Any])
async def delete_job(
    job_id: int,
    job_runner: JobRunner = Depends(get_job_runner_dependency),
):
    """
    Delete a job from the system
    """
    try:
        # Check if job exists
        job = job_runner.get_job_status(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Cancel job if it's running
        if job["status"] in [JobStatus.PENDING, JobStatus.RUNNING]:
            job_runner.cancel_job(job_id)
        
        # Delete job from database
        success = job_runner.delete_job(job_id)
        
        if success:
            return {
                "success": True,
                "message": f"Job {job_id} deleted successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete job")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")
