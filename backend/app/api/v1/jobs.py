"""
Job management API endpoints for background backtests
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Optional, Dict, Any
import json

from backend.app.tasks.job_runner import get_job_runner, JobStatus
from backend.app.schemas.backtest import BacktestRequest, EngineOptions
from backend.app.database.models import init_db, Dataset, get_session_factory

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])

# Initialize database on startup
init_db()

@router.post("/", response_model=Dict[str, Any])
async def submit_backtest_job(request: BacktestRequest):
    """
    Submit a backtest job for background execution
    Returns immediately with job ID for status tracking
    """
    try:
        job_runner = get_job_runner()
        
        # Convert Pydantic model to dict for service
        engine_options = request.engine_options.model_dump() if request.engine_options else {}
        
        # Resolve dataset path from dataset ID if needed
        dataset_path = request.dataset_path
        if request.dataset and not dataset_path:
            db = get_session_factory()()
            try:
                dataset = db.query(Dataset).filter(Dataset.id == int(request.dataset)).first()
                if not dataset:
                    raise HTTPException(status_code=404, detail=f"Dataset with ID {request.dataset} not found")
                dataset_path = dataset.file_path
            finally:
                db.close()
        
        if not dataset_path:
            raise HTTPException(status_code=400, detail="Either dataset or dataset_path must be provided")
        
        # Resolve strategy ID to strategy path if needed (strategy is just a number)
        strategy_path = request.strategy
        if request.strategy.isdigit():
            # Import strategy registry to resolve strategy ID
            from backend.app.services.strategy_service import StrategyRegistry
            strategy_registry = StrategyRegistry()
            strategies = strategy_registry.list_strategies()
            
            strategy_id = int(request.strategy)
            if 1 <= strategy_id <= len(strategies):
                strategy_info = strategies[strategy_id - 1]  # 1-indexed to 0-indexed
                # Combine module_path and class_name for BacktestService
                strategy_path = f"{strategy_info['module_path']}.{strategy_info['class_name']}"
            else:
                raise HTTPException(status_code=404, detail=f"Strategy with ID {strategy_id} not found")
        
        # Submit job
        job_id = job_runner.submit_job(
            strategy=strategy_path,
            strategy_params=request.strategy_params,
            dataset_path=dataset_path,
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


@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_job_status(job_id: int):
    """
    Get the status and details of a specific job
    """
    try:
        job_runner = get_job_runner()
        job = job_runner.get_job_status(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return job
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.post("/upload", response_model=Dict[str, Any])
async def submit_backtest_job_with_upload(
    file: UploadFile = File(...),
    strategy: str = Form(...),
    strategy_params: str = Form(default="{}"),
    engine_options: str = Form(default="{}")
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
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON in engine_options: {e}")
        
        # Read uploaded file
        csv_bytes = await file.read()
        
        # Submit job
        job_runner = get_job_runner()
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


@router.get("/{job_id}/status", response_model=Dict[str, Any])
async def get_job_status_detail(job_id: int):
    """
    Get the current status and progress of a background job
    """
    try:
        job_runner = get_job_runner()
        status = job_runner.get_job_status(job_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "success": True,
            "job": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.get("/{job_id}/results", response_model=Dict[str, Any])
async def get_job_results(job_id: int):
    """
    Get the results of a completed background job
    """
    try:
        job_runner = get_job_runner()
        
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
            "job_id": job_id,
            "status": status["status"],
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job results: {str(e)}")


@router.post("/{job_id}/cancel", response_model=Dict[str, Any])
async def cancel_job(job_id: int):
    """
    Cancel a running background job
    """
    try:
        job_runner = get_job_runner()
        
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


@router.get("/", response_model=Dict[str, Any])
async def list_jobs(limit: int = 50):
    """
    List recent background jobs with their status
    """
    if limit > 100:
        limit = 100  # Limit maximum to prevent abuse
    
    job_runner = get_job_runner()
    jobs = job_runner.list_jobs(limit=limit)
    
    return {
        "success": True,
        "jobs": jobs,
        "total": len(jobs)
    }

# Alias without trailing slash for clients that call /api/v1/jobs
@router.get("", response_model=Dict[str, Any])
async def list_jobs_no_slash(limit: int = 50):
    return await list_jobs(limit=limit)


@router.get("/stats", response_model=Dict[str, Any])
async def get_job_stats():
    """
    Get statistics about job execution
    """
    job_runner = get_job_runner()
    jobs = job_runner.list_jobs(limit=100)
    
    # Calculate stats
    stats = {
        "total_jobs": len(jobs),
        "pending": len([j for j in jobs if j["status"] == JobStatus.PENDING]),
        "running": len([j for j in jobs if j["status"] == JobStatus.RUNNING]),
        "completed": len([j for j in jobs if j["status"] == JobStatus.COMPLETED]),
        "failed": len([j for j in jobs if j["status"] == JobStatus.FAILED]),
        "cancelled": len([j for j in jobs if j["status"] == JobStatus.CANCELLED])
    }
    
    return {
        "success": True,
        "stats": stats
    }


@router.delete("/{job_id}", response_model=Dict[str, Any])
async def delete_job(job_id: int):
    """
    Delete a job from the system
    """
    try:
        job_runner = get_job_runner()
        
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
