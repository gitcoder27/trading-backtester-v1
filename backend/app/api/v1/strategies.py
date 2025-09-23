"""
Strategy management API endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json

from backend.app.services.strategy_service import StrategyRegistry
from backend.app.database.models import init_db

router = APIRouter(prefix="/api/v1/strategies", tags=["strategies"])

# Initialize database on startup
init_db()

@router.get("/discover")
async def discover_strategies():
    """
    Discover all strategies in the strategies/ directory
    
    Returns:
        List of discovered strategies with metadata
    """
    try:
        registry = StrategyRegistry()
        strategies = registry.discover_strategies()
        
        return {
            'success': True,
            'strategies': strategies,
            'total': len(strategies)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to discover strategies: {str(e)}")


from pydantic import BaseModel

class StrategyRegistrationRequest(BaseModel):
    strategy_ids: Optional[List[str]] = None


class StrategyCodeUpdateRequest(BaseModel):
    content: str


class StrategyCodeCreateRequest(BaseModel):
    file_name: str
    content: str
    overwrite: bool = False

@router.post("/register")
async def register_strategies(request: StrategyRegistrationRequest = None):
    """
    Register discovered strategies in the database
    
    Args:
        strategy_ids: Optional list of strategy IDs to register. If None, registers all discovered strategies.
    
    Returns:
        Summary of registration process
    """
    try:
        registry = StrategyRegistry()
        strategy_ids = request.strategy_ids if request else None
        result = registry.register_strategies(strategy_ids=strategy_ids)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Registration failed'))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register strategies: {str(e)}")


@router.get("/")
async def list_strategies(
    active_only: bool = Query(True, description="Only return active strategies"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of strategies to return")
):
    """
    List all registered strategies
    
    Args:
        active_only: Only return active strategies
        limit: Maximum number of strategies to return
        
    Returns:
        List of strategy metadata
    """
    try:
        registry = StrategyRegistry()
        strategies = registry.list_strategies(active_only=active_only)
        
        # Apply limit
        if len(strategies) > limit:
            strategies = strategies[:limit]
        
        return {
            'success': True,
            'strategies': strategies,
            'total': len(strategies),
            'active_only': active_only
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list strategies: {str(e)}")


@router.get("/{strategy_id}")
async def get_strategy(strategy_id: int):
    """
    Get detailed information about a specific strategy
    
    Args:
        strategy_id: ID of the strategy
        
    Returns:
        Strategy metadata including parameters schema
    """
    try:
        registry = StrategyRegistry()
        strategy = registry.get_strategy_metadata(strategy_id)
        
        return {
            'success': True,
            'strategy': strategy
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get strategy: {str(e)}")


@router.get("/{strategy_id}/code")
async def get_strategy_code(strategy_id: int):
    """Return Python source code for a registered strategy."""
    registry = StrategyRegistry()
    try:
        source = registry.get_strategy_source(strategy_id)
        return {
            'success': True,
            'strategy_id': source['strategy_id'],
            'module_path': source['module_path'],
            'class_name': source['class_name'],
            'file_path': source['file_path'],
            'content': source['content']
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load strategy code: {str(e)}")


@router.put("/{strategy_id}/code")
async def update_strategy_code(strategy_id: int, request: StrategyCodeUpdateRequest):
    """Persist edits to a strategy source file."""
    registry = StrategyRegistry()
    try:
        result = registry.update_strategy_source(strategy_id, request.content)
        return {
            'success': True,
            'strategy_id': result['strategy_id'],
            'module_path': result['module_path'],
            'file_path': result['file_path'],
            'updated': True,
            'registration': result.get('registration')
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update strategy code: {str(e)}")


@router.post("/code")
async def create_strategy_code(request: StrategyCodeCreateRequest):
    """Create a new strategy Python file under the strategies directory."""
    registry = StrategyRegistry()
    try:
        result = registry.create_strategy_source(request.file_name, request.content, request.overwrite)
        return {
            'success': True,
            'file_path': result['file_path'],
            'module_path': result['module_path'],
            'created': result['created'],
            'registration': result.get('registration'),
            'registered_ids': result.get('registered_ids', [])
        }
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create strategy file: {str(e)}")


@router.post("/{strategy_id}/validate")
async def validate_strategy(
    strategy_id: int,
    file: Optional[UploadFile] = File(None),
    parameters: str = Form("{}")
):
    """
    Validate a strategy by attempting to instantiate and run it
    
    Args:
        strategy_id: ID of the strategy to validate
        file: Optional CSV file for testing (if not provided, uses sample data)
        parameters: JSON string of parameters to test with
        
    Returns:
        Validation results with any errors or warnings
    """
    try:
        # Parse parameters
        try:
            params = json.loads(parameters)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON in parameters: {e}")
        
        # Read sample data if provided
        sample_data = None
        if file:
            if not file.filename.lower().endswith('.csv'):
                raise HTTPException(status_code=400, detail="Only CSV files are supported for validation")
            sample_data = await file.read()
        
        # Validate strategy
        registry = StrategyRegistry()
        result = registry.validate_strategy(
            strategy_id=strategy_id,
            sample_data=sample_data,
            parameters=params
        )
        
        return {
            'success': True,
            'strategy_id': strategy_id,
            'validation': result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate strategy: {str(e)}")


@router.post("/validate-by-path")
async def validate_strategy_by_path(
    module_path: str = Form(...),
    class_name: str = Form(...),
    file: Optional[UploadFile] = File(None),
    parameters: str = Form("{}")
):
    """
    Validate a strategy by module path and class name (for testing unregistered strategies)
    
    Args:
        module_path: Module path (e.g., 'strategies.ema10_scalper')
        class_name: Class name (e.g., 'EMA10ScalperStrategy')
        file: Optional CSV file for testing
        parameters: JSON string of parameters to test with
        
    Returns:
        Validation results with any errors or warnings
    """
    try:
        # Parse parameters
        try:
            params = json.loads(parameters)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON in parameters: {e}")
        
        # Read sample data if provided
        sample_data = None
        if file:
            if not file.filename.lower().endswith('.csv'):
                raise HTTPException(status_code=400, detail="Only CSV files are supported for validation")
            sample_data = await file.read()
        
        # Validate strategy
        registry = StrategyRegistry()
        result = registry.validate_strategy_by_path(
            module_path=module_path,
            class_name=class_name,
            sample_data=sample_data,
            parameters=params
        )
        
        return {
            'success': True,
            'module_path': module_path,
            'class_name': class_name,
            'validation': result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate strategy: {str(e)}")


@router.get("/{strategy_id}/schema")
async def get_strategy_parameters_schema(strategy_id: int):
    """
    Get the parameters schema for a strategy
    
    Args:
        strategy_id: ID of the strategy
        
    Returns:
        Parameters schema and default values
    """
    try:
        registry = StrategyRegistry()
        strategy = registry.get_strategy_metadata(strategy_id)
        
        return {
            'success': True,
            'strategy_id': strategy_id,
            'strategy_name': strategy['name'],
            'parameters_schema': strategy.get('parameters_schema', {}),
            'default_parameters': strategy.get('default_parameters', {})
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get strategy schema: {str(e)}")


@router.patch("/{strategy_id}")
async def update_strategy(
    strategy_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None)
):
    """
    Update strategy metadata
    
    Args:
        strategy_id: ID of the strategy
        name: New name for the strategy
        description: New description
        is_active: Whether the strategy is active
        
    Returns:
        Updated strategy information
    """
    try:
        from backend.app.database.models import get_session_factory, Strategy
        
        SessionLocal = get_session_factory()
        db = SessionLocal()
        
        try:
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                raise HTTPException(status_code=404, detail="Strategy not found")
            
            # Update fields if provided
            if name is not None:
                strategy.name = name
            if description is not None:
                strategy.description = description
            if is_active is not None:
                strategy.is_active = is_active
            
            db.commit()
            db.refresh(strategy)
            
            # Get updated strategy
            registry = StrategyRegistry()
            updated_strategy = registry.get_strategy_metadata(strategy_id)
            
            return {
                'success': True,
                'strategy': updated_strategy
            }
            
        finally:
            db.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update strategy: {str(e)}")


@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: int):
    """Delete a strategy, archive its file, and remove metadata."""
    registry = StrategyRegistry()
    try:
        result = registry.delete_strategy(strategy_id)
        return {
            'success': True,
            'strategy_id': result['strategy_id'],
            'file_removed': result['file_removed'],
            'archive_path': result['archive_path'],
            'module_path': result['module_path'],
            'class_name': result['class_name'],
            'shared_module': result['shared_module'],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete strategy: {str(e)}")


@router.get("/stats/summary")
async def get_strategies_summary():
    """
    Get summary statistics for all strategies
    
    Returns:
        Summary statistics and metrics
    """
    try:
        registry = StrategyRegistry()
        strategies = registry.list_strategies(active_only=False)
        
        total_strategies = len(strategies)
        active_strategies = len([s for s in strategies if s.get('is_active', True)])
        
        # Count strategies by module
        modules = {}
        for strategy in strategies:
            module = strategy.get('module_path', 'unknown').split('.')[-1]
            modules[module] = modules.get(module, 0) + 1
        
        # Calculate average performance if available
        performances = [s.get('avg_performance') for s in strategies if s.get('avg_performance') is not None]
        avg_performance = sum(performances) / len(performances) if performances else None
        
        # Count total backtests
        total_backtests = sum(s.get('total_backtests', 0) for s in strategies)
        
        return {
            'success': True,
            'summary': {
                'total_strategies': total_strategies,
                'active_strategies': active_strategies,
                'inactive_strategies': total_strategies - active_strategies,
                'total_backtests': total_backtests,
                'average_performance': avg_performance,
                'strategies_by_module': modules
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")
