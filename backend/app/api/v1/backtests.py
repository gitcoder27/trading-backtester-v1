"""
Backtest API endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from typing import Optional, Dict, Any
import json
from sqlalchemy.orm import Session

from backend.app.services.backtest_service import BacktestService
from backend.app.services.backtest.backtest_service import BacktestServiceError
from backend.app.database.models import get_session_factory, Backtest, Dataset
from backend.app.schemas.backtest import (
    BacktestRequest, BacktestResponse, BacktestResult, ErrorResponse,
    EngineOptions
)

router = APIRouter(prefix="/api/v1/backtests", tags=["backtests"])

# Service instance
backtest_service = BacktestService()

# In-memory storage for results (Phase 1 - will be replaced with DB in Phase 3)
results_store: Dict[str, Dict[str, Any]] = {}
next_result_id = 1


@router.post("/", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """
    Run a backtest synchronously
    For small datasets, returns results immediately
    """
    global next_result_id
    
    try:
        # Convert Pydantic model to dict for service
        engine_options = request.engine_options.model_dump() if request.engine_options else {}
        
        # Resolve dataset path if dataset ID provided
        dataset_path = request.dataset_path
        if request.dataset and not dataset_path:
            SessionLocal = get_session_factory()
            db = SessionLocal()
            try:
                ds = db.query(Dataset).filter(Dataset.id == int(request.dataset)).first()
                if not ds:
                    raise HTTPException(status_code=404, detail=f"Dataset with ID {request.dataset} not found")
                dataset_path = ds.file_path
            finally:
                db.close()

        # Resolve numeric strategy IDs to module.class path for synchronous runs as well
        strategy_path = request.strategy
        if request.strategy.isdigit():
            from backend.app.services.strategy_service import StrategyRegistry
            strategy_registry = StrategyRegistry()
            strategy_id = int(request.strategy)
            try:
                strategy_info = strategy_registry.get_strategy_metadata(strategy_id)
            except Exception:
                raise HTTPException(status_code=404, detail=f"Strategy with ID {strategy_id} not found")
            strategy_path = f"{strategy_info['module_path']}.{strategy_info['class_name']}"

        # Run the backtest
        result_data = backtest_service.run_backtest(
            strategy=strategy_path,
            strategy_params=request.strategy_params,
            dataset_path=dataset_path,
            engine_options=engine_options
        )
        
        # Store result for later retrieval
        result_id = str(next_result_id)
        results_store[result_id] = result_data
        next_result_id += 1
        
        # Create result response
        result = BacktestResult(**result_data)
        
        return BacktestResponse(
            success=True,
            result=result,
            job_id=result_id
        )
        
    except (ValueError, BacktestServiceError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@router.post("/upload", response_model=BacktestResponse)
async def run_backtest_with_upload(
    file: UploadFile = File(...),
    strategy: str = Form(...),
    strategy_params: str = Form(default="{}"),
    engine_options: str = Form(default="{}")
):
    """
    Run a backtest with uploaded CSV data
    """
    global next_result_id
    
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
        
        # Run the backtest
        result_data = backtest_service.run_backtest(
            strategy=strategy,
            strategy_params=strategy_params_dict,
            csv_bytes=csv_bytes,
            engine_options=engine_options_dict
        )
        
        # Store result
        result_id = str(next_result_id)
        results_store[result_id] = result_data
        next_result_id += 1
        
        # Create result response
        result = BacktestResult(**result_data)
        
        return BacktestResponse(
            success=True,
            result=result,
            job_id=result_id
        )
        
    except (ValueError, BacktestServiceError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@router.get("/{backtest_id}", response_model=Dict[str, Any])
async def get_backtest_detail(backtest_id: int):
    """
    Get backtest details by ID from database
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    
    try:
        # Query backtest from database
        backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
        
        if not backtest:
            raise HTTPException(status_code=404, detail=f"Backtest with ID {backtest_id} not found")
        
        # Get dataset info if available
        dataset_name = "Unknown Dataset"
        if backtest.dataset_id:
            try:
                from backend.app.database.models import Dataset
                dataset = db.query(Dataset).filter(Dataset.id == backtest.dataset_id).first()
                if dataset:
                    dataset_name = dataset.name
            except Exception:
                pass
        
        # Calculate duration if both timestamps exist
        duration = None
        if backtest.created_at and backtest.completed_at:
            duration_seconds = (backtest.completed_at - backtest.created_at).total_seconds()
            duration = f"{int(duration_seconds // 60)}m"
        
        # Normalize results: handle JSON stored as string and enrich metrics
        results_obj: Any = backtest.results or {}
        try:
            if isinstance(results_obj, str):
                results_obj = json.loads(results_obj)
        except Exception:
            results_obj = {}

        # Extract metrics with sensible fallbacks
        metrics_out = {}
        if isinstance(results_obj, dict):
            metrics = results_obj.get('metrics', {}) or {}
            if isinstance(metrics, dict):
                # Provide common aliases expected by frontend
                if 'total_return_percent' not in metrics and 'total_return_pct' in metrics:
                    metrics['total_return_percent'] = metrics.get('total_return_pct')
                if 'max_drawdown_percent' not in metrics and 'max_drawdown_pct' in metrics:
                    metrics['max_drawdown_percent'] = metrics.get('max_drawdown_pct')
                # Ensure total_trades reflects trades length if missing/zero
                try:
                    trades_list = results_obj.get('trade_log') or results_obj.get('trades') or []
                    if (not metrics.get('total_trades')) and isinstance(trades_list, list):
                        metrics['total_trades'] = len(trades_list)
                except Exception:
                    pass
                metrics_out = metrics

        # Structure the response to match frontend expectations
        response = {
            "id": backtest.id,
            "strategy_name": backtest.strategy_name,
            "strategy": backtest.strategy_name,  # Frontend expects both
            "dataset_name": dataset_name,
            "dataset_id": backtest.dataset_id,
            "status": backtest.status or "completed",
            "created_at": backtest.created_at.isoformat() if backtest.created_at else None,
            "completed_at": backtest.completed_at.isoformat() if backtest.completed_at else None,
            "duration": duration,
            "parameters": backtest.strategy_params,
            "initial_capital": 100000,  # Default value, should be stored in results
            "results": results_obj
        }
        
        # Add metrics from results if available
        if isinstance(results_obj, dict):
            if metrics_out:
                response['metrics'] = metrics_out
            if 'engine_config' in results_obj:
                engine_config = results_obj['engine_config']
                response['initial_capital'] = engine_config.get('initial_cash', 100000)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve backtest: {str(e)}")
    finally:
        db.close()


@router.get("/{result_id}/results", response_model=BacktestResponse)
async def get_backtest_results(result_id: str):
    """
    Get backtest results by ID (legacy endpoint for in-memory results)
    """
    if result_id not in results_store:
        raise HTTPException(status_code=404, detail="Backtest result not found")
    
    try:
        result_data = results_store[result_id]
        result = BacktestResult(**result_data)
        
        return BacktestResponse(
            success=True,
            result=result,
            job_id=result_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve results: {str(e)}")


@router.get("/", response_model=Dict[str, Any])
async def list_backtests(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Number of items per page")
):
    """
    List all stored backtest results from the database
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    
    try:
        # Calculate offset for pagination
        offset = (page - 1) * size
        
        # Query backtests from database
        total_count = db.query(Backtest).count()
        backtests = db.query(Backtest).offset(offset).limit(size).all()
        
        # Format response
        backtest_list = []
        for bt in backtests:
            # Extract metrics from results if available, robust to JSON strings
            metrics_out = {}
            results_obj: Any = bt.results
            try:
                if isinstance(results_obj, str):
                    results_obj = json.loads(results_obj)
            except Exception:
                results_obj = {}

            if isinstance(results_obj, dict):
                metrics = results_obj.get('metrics', {}) or {}
                if isinstance(metrics, dict):
                    # Provide common aliases expected by frontend
                    if 'total_return_percent' not in metrics and 'total_return_pct' in metrics:
                        metrics['total_return_percent'] = metrics.get('total_return_pct')
                    if 'max_drawdown_percent' not in metrics and 'max_drawdown_pct' in metrics:
                        metrics['max_drawdown_percent'] = metrics.get('max_drawdown_pct')

                    # Ensure total_trades reflects trades length if missing/zero
                    try:
                        trades_list = results_obj.get('trade_log') or results_obj.get('trades') or []
                        if (not metrics.get('total_trades')) and isinstance(trades_list, list):
                            metrics['total_trades'] = len(trades_list)
                    except Exception:
                        pass

                    metrics_out = metrics
            
            backtest_list.append({
                "id": bt.id,
                "job_id": bt.backtest_job_id if hasattr(bt, 'backtest_job_id') and bt.backtest_job_id is not None else None,
                "strategy_name": bt.strategy_name,
                "strategy_params": bt.strategy_params,
                "status": bt.status,
                "created_at": bt.created_at.isoformat() if bt.created_at else None,
                "completed_at": bt.completed_at.isoformat() if bt.completed_at else None,
                "metrics": metrics_out
            })
        
        return {
            "total": total_count,
            "page": page,
            "size": size,
            "results": backtest_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve backtests: {str(e)}")
    finally:
        db.close()

# Alias without trailing slash for clients that call /api/v1/backtests
@router.get("", response_model=Dict[str, Any])
async def list_backtests_no_slash(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Number of items per page")
):
    return await list_backtests(page=page, size=size)
