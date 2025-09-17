"""
Optimization API endpoints
Provides parameter optimization functionality for trading strategies
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Union, Optional
from pydantic import BaseModel, Field

from backend.app.api.dependencies import (
    get_dataset_service,
    get_job_runner_dependency,
    get_optimization_service,
)
from backend.app.services.dataset_service import DatasetService
from backend.app.services.optimization import ParameterGridError, generate_parameter_grid
from backend.app.services.optimization_service import OptimizationService
from backend.app.tasks import JobRunner, JobStatus

router = APIRouter(prefix="/api/v1/optimize", tags=["optimization"])


class ParameterRange(BaseModel):
    type: str = Field(..., description="Type of parameter range: 'range' or 'choice'")
    start: Optional[Union[int, float]] = Field(None, description="Start value for range type")
    stop: Optional[Union[int, float]] = Field(None, description="Stop value for range type")
    step: Optional[Union[int, float]] = Field(1, description="Step size for range type")
    values: Optional[List[Union[int, float, str]]] = Field(None, description="List of values for choice type")


class OptimizationRequest(BaseModel):
    strategy_path: str = Field(..., description="Module path to strategy class (e.g., 'strategies.ema10_scalper.EMA10ScalperStrategy')")
    dataset_id: int = Field(..., description="ID of dataset to use for optimization")
    param_ranges: Dict[str, ParameterRange] = Field(..., description="Parameter ranges to optimize")
    optimization_metric: str = Field("sharpe_ratio", description="Metric to optimize (sharpe_ratio, total_return_pct, profit_factor, etc.)")
    engine_options: Optional[Dict[str, Any]] = Field(None, description="Engine configuration options")
    max_workers: int = Field(2, description="Number of parallel workers", ge=1, le=8)
    validation_split: float = Field(0.3, description="Fraction of data to reserve for validation", ge=0.1, le=0.5)


@router.post("/")
async def start_optimization(
    request: OptimizationRequest,
    optimization_service: OptimizationService = Depends(get_optimization_service),
) -> Dict[str, Any]:
    """
    Start a parameter optimization job
    
    This endpoint submits an optimization job to run in the background.
    Use the returned job_id to check status and retrieve results.
    
    Example parameter ranges:
    ```json
    {
      "param_ranges": {
        "ema_period": {
          "type": "range",
          "start": 10,
          "stop": 50,
          "step": 5
        },
        "rsi_period": {
          "type": "choice",
          "values": [14, 21, 28]
        }
      }
    }
    ```
    """
    # Convert Pydantic models to dictionaries for the service
    param_ranges_dict = {}
    for param_name, param_range in request.param_ranges.items():
        param_ranges_dict[param_name] = param_range.dict(exclude_none=True)
    
    result = optimization_service.start_optimization_job(
        strategy_path=request.strategy_path,
        dataset_id=request.dataset_id,
        param_ranges=param_ranges_dict,
        optimization_metric=request.optimization_metric,
        engine_options=request.engine_options,
        max_workers=request.max_workers,
        validation_split=request.validation_split
    )
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result


@router.get("/{job_id}/status")
async def get_optimization_status(
    job_id: str,
    job_runner: JobRunner = Depends(get_job_runner_dependency),
) -> Dict[str, Any]:
    """
    Get the status of an optimization job
    
    Returns current progress, estimated completion time, and any intermediate results
    """
    job = job_runner.get_job_status(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Optimization job not found")
    
    return {
        'success': True,
        'job_id': job_id,
        'status': job['status'].value,
        'progress': job.get('progress', {}),
        'created_at': job.get('created_at'),
        'started_at': job.get('started_at'),
        'completed_at': job.get('completed_at'),
        'error': job.get('error')
    }


@router.get("/{job_id}/results")
async def get_optimization_results(
    job_id: str,
    optimization_service: OptimizationService = Depends(get_optimization_service),
) -> Dict[str, Any]:
    """
    Get the results of a completed optimization job
    
    Returns:
    - Best parameters found
    - Optimization scores for all parameter combinations
    - Validation results (out-of-sample performance)
    - Parameter sensitivity analysis
    - Performance distribution analysis
    """
    result = optimization_service.get_optimization_results(job_id)
    
    if not result['success']:
        if 'not found' in result['error']:
            raise HTTPException(status_code=404, detail=result['error'])
        else:
            raise HTTPException(status_code=400, detail=result['error'])
    
    return result


@router.post("/{job_id}/cancel")
async def cancel_optimization(
    job_id: str,
    job_runner: JobRunner = Depends(get_job_runner_dependency),
) -> Dict[str, Any]:
    """
    Cancel a running optimization job
    
    Note: Jobs that are already running may take some time to stop gracefully
    """
    success = job_runner.cancel_job(job_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Optimization job not found")
    
    return {
        'success': True,
        'job_id': job_id,
        'message': 'Optimization job cancelled'
    }


@router.get("/")
async def list_optimization_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    job_runner: JobRunner = Depends(get_job_runner_dependency),
) -> Dict[str, Any]:
    """
    List optimization jobs with optional filtering
    
    Parameters:
    - status: Filter by job status (pending, running, completed, failed, cancelled)
    - limit: Maximum number of jobs to return
    - offset: Number of jobs to skip (for pagination)
    """
    jobs = job_runner.list_jobs(
        job_type='optimization',
        status=status,
        limit=limit,
        offset=offset
    )
    
    return {
        'success': True,
        'jobs': jobs,
        'count': len(jobs)
    }


@router.get("/stats/summary")
async def get_optimization_stats(
    job_runner: JobRunner = Depends(get_job_runner_dependency),
) -> Dict[str, Any]:
    """
    Get summary statistics for optimization jobs
    
    Returns counts by status, average completion times, etc.
    """
    stats = job_runner.get_job_stats('optimization')
    
    return {
        'success': True,
        'stats': stats
    }


@router.post("/validate")
async def validate_optimization_request(
    request: OptimizationRequest,
    optimization_service: OptimizationService = Depends(get_optimization_service),
    dataset_service: DatasetService = Depends(get_dataset_service),
) -> Dict[str, Any]:
    """
    Validate an optimization request without running it
    
    Checks parameter ranges, dataset availability, strategy validity, etc.
    Returns estimated runtime and number of parameter combinations.
    """
    try:
        # Convert parameter ranges
        param_ranges_dict = {
            name: config.dict(exclude_none=True)
            for name, config in request.param_ranges.items()
        }

        try:
            param_combinations = generate_parameter_grid(param_ranges_dict)
        except ParameterGridError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        try:
            dataset_service.get_dataset_quality(request.dataset_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Dataset not found")

        estimated_time_minutes = optimization_service._estimate_optimization_time(len(param_combinations))
        
        return {
            'success': True,
            'validation': {
                'total_combinations': len(param_combinations),
                'estimated_time_minutes': estimated_time_minutes,
                'dataset_exists': True,
                'parameter_ranges_valid': True,
                'warnings': [
                    "Large optimization runs may take significant time"
                ] if len(param_combinations) > 100 else []
            }
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@router.get("/metrics")
async def get_available_optimization_metrics() -> Dict[str, Any]:
    """
    Get list of available optimization metrics
    
    Returns all metrics that can be used as optimization targets
    """
    return {
        'success': True,
        'metrics': {
            'sharpe_ratio': {
                'description': 'Risk-adjusted return (return/volatility)',
                'higher_is_better': True,
                'recommended': True
            },
            'total_return_pct': {
                'description': 'Total percentage return',
                'higher_is_better': True,
                'recommended': True
            },
            'profit_factor': {
                'description': 'Ratio of gross profits to gross losses',
                'higher_is_better': True,
                'recommended': True
            },
            'max_drawdown_pct': {
                'description': 'Maximum peak-to-trough decline',
                'higher_is_better': False,
                'recommended': False
            },
            'win_rate': {
                'description': 'Percentage of winning trades',
                'higher_is_better': True,
                'recommended': False
            },
            'sortino_ratio': {
                'description': 'Return relative to downside risk',
                'higher_is_better': True,
                'recommended': True
            },
            'calmar_ratio': {
                'description': 'Return relative to maximum drawdown',
                'higher_is_better': True,
                'recommended': True
            }
        }
    }


@router.post("/quick")
async def quick_optimization(
    strategy_path: str,
    dataset_id: int,
    param_name: str,
    param_values: List[Union[int, float]],
    optimization_metric: str = "sharpe_ratio",
    optimization_service: OptimizationService = Depends(get_optimization_service),
) -> Dict[str, Any]:
    """
    Run a quick optimization for a single parameter
    
    This is a simplified endpoint for testing single parameter sensitivity.
    Results are returned immediately (not as a background job).
    """
    if len(param_values) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 values allowed for quick optimization")
    
    # Create parameter range
    param_ranges = {
        param_name: {
            'type': 'choice',
            'values': param_values
        }
    }
    
    job_data = {
        'strategy_path': strategy_path,
        'dataset_id': dataset_id,
        'param_ranges': param_ranges,
        'param_combinations': generate_parameter_grid(param_ranges),
        'optimization_metric': optimization_metric,
        'engine_options': {},
        'max_workers': 1,
        'validation_split': 0.2
    }
    
    result = optimization_service.run_optimization(job_data)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result
