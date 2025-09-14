"""
Dataset management API endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from typing import Optional, List
import json

from backend.app.services.dataset_service import DatasetService
from backend.app.database.models import init_db

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])

# Initialize database on startup
init_db()

@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    symbol: Optional[str] = Form(None),
    exchange: Optional[str] = Form(None),
    data_source: Optional[str] = Form(None)
):
    """
    Upload a new dataset CSV file
    
    Args:
        file: CSV file upload
        name: Human-readable name for the dataset
        symbol: Trading symbol (e.g., 'NIFTY')
        exchange: Exchange name (e.g., 'NSE')
        data_source: Source of the data (e.g., 'Yahoo Finance')
        
    Returns:
        Dataset metadata and quality analysis
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Process dataset
        dataset_service = DatasetService()
        result = dataset_service.upload_dataset(
            file_name=file.filename,
            file_content=file_content,
            name=name,
            symbol=symbol,
            exchange=exchange,
            data_source=data_source
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload dataset: {str(e)}")


@router.get("/{dataset_id}/quality")
async def get_dataset_quality(dataset_id: int):
    """
    Get detailed quality analysis for a dataset
    
    Args:
        dataset_id: ID of the dataset
        
    Returns:
        Quality analysis including missing data, outliers, gaps, etc.
    """
    try:
        dataset_service = DatasetService()
        result = dataset_service.get_dataset_quality(dataset_id)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze dataset: {str(e)}")


@router.get("/")
async def list_datasets(limit: int = Query(50, ge=1, le=100)):
    """
    List all uploaded datasets
    
    Args:
        limit: Maximum number of datasets to return
        
    Returns:
        List of dataset metadata
    """
    try:
        dataset_service = DatasetService()
        datasets = dataset_service.list_datasets(limit=limit)
        
        return {
            'success': True,
            'datasets': datasets,
            'total': len(datasets)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list datasets: {str(e)}")


# Alias without trailing slash for clients that call /api/v1/datasets
@router.get("")
async def list_datasets_no_slash(limit: int = Query(50, ge=1, le=100)):
    return await list_datasets(limit=limit)


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: int):
    """
    Get detailed information about a specific dataset
    
    Args:
        dataset_id: ID of the dataset
        
    Returns:
        Dataset metadata and quality information
    """
    try:
        dataset_service = DatasetService()
        result = dataset_service.get_dataset_quality(dataset_id)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dataset: {str(e)}")


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: int):
    """
    Delete a dataset and its associated file
    
    Args:
        dataset_id: ID of the dataset to delete
        
    Returns:
        Deletion confirmation
    """
    try:
        dataset_service = DatasetService()
        result = dataset_service.delete_dataset(dataset_id)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete dataset: {str(e)}")


@router.get("/{dataset_id}/preview")
async def preview_dataset(
    dataset_id: int,
    rows: int = Query(10, ge=1, le=100)
):
    """
    Get a preview of the dataset (first N rows)
    
    Args:
        dataset_id: ID of the dataset
        rows: Number of rows to return
        
    Returns:
        Preview data and basic statistics
    """
    try:
        dataset_service = DatasetService()
        
        # Get dataset info
        dataset_info = dataset_service.get_dataset_quality(dataset_id)
        if not dataset_info['success']:
            raise ValueError("Dataset not found")
        
        dataset = dataset_info['dataset']
        
        # Read and preview the file
        import pandas as pd
        from pathlib import Path
        
        file_path = Path(dataset['file_path'])
        if not file_path.exists():
            raise ValueError("Dataset file not found")
        
        df = pd.read_csv(file_path)
        
        # Get preview data
        preview_data = df.head(rows).to_dict(orient='records')
        
        # Get basic statistics
        numeric_columns = df.select_dtypes(include=['number']).columns
        stats = {}
        
        for col in numeric_columns:
            stats[col] = {
                'mean': float(df[col].mean()) if not df[col].isna().all() else None,
                'std': float(df[col].std()) if not df[col].isna().all() else None,
                'min': float(df[col].min()) if not df[col].isna().all() else None,
                'max': float(df[col].max()) if not df[col].isna().all() else None,
                'count': int(df[col].count())
            }
        
        return {
            'success': True,
            'dataset_id': dataset_id,
            'dataset_info': dataset,
            'preview': preview_data,
            'statistics': stats,
            'total_rows': len(df),
            'columns': list(df.columns)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to preview dataset: {str(e)}")


@router.get("/{dataset_id}/download")
async def download_dataset(dataset_id: int):
    """
    Download the original dataset file
    
    Args:
        dataset_id: ID of the dataset
        
    Returns:
        File download response
    """
    try:
        from fastapi.responses import FileResponse
        from pathlib import Path
        
        dataset_service = DatasetService()
        
        # Get dataset info
        dataset_info = dataset_service.get_dataset_quality(dataset_id)
        if not dataset_info['success']:
            raise ValueError("Dataset not found")
        
        dataset = dataset_info['dataset']
        file_path = Path(dataset['file_path'])
        
        if not file_path.exists():
            raise ValueError("Dataset file not found")
        
        return FileResponse(
            path=str(file_path),
            filename=dataset['filename'],
            media_type='text/csv'
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download dataset: {str(e)}")


@router.get("/stats/summary")
async def get_datasets_summary():
    """
    Get summary statistics for all datasets
    
    Returns:
        Summary statistics and metrics
    """
    try:
        dataset_service = DatasetService()
        datasets = dataset_service.list_datasets(limit=1000)  # Get all datasets
        
        if not datasets:
            return {
                'success': True,
                'summary': {
                    'total_datasets': 0,
                    'total_file_size': 0,
                    'total_rows': 0,
                    'average_quality_score': 0,
                    'timeframes': {},
                    'exchanges': {},
                    'symbols': {}
                }
            }
        
        # Calculate summary statistics
        total_datasets = len(datasets)
        total_file_size = sum(d.get('file_size', 0) for d in datasets)
        total_rows = sum(d.get('rows_count', 0) for d in datasets)
        
        quality_scores = [d.get('data_quality_score') for d in datasets if d.get('data_quality_score') is not None]
        average_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Count timeframes
        timeframes = {}
        exchanges = {}
        symbols = {}
        
        for dataset in datasets:
            # Timeframes
            tf = dataset.get('timeframe')
            if tf:
                timeframes[tf] = timeframes.get(tf, 0) + 1
            
            # Exchanges
            exchange = dataset.get('exchange')
            if exchange:
                exchanges[exchange] = exchanges.get(exchange, 0) + 1
            
            # Symbols
            symbol = dataset.get('symbol')
            if symbol:
                symbols[symbol] = symbols.get(symbol, 0) + 1
        
        return {
            'success': True,
            'summary': {
                'total_datasets': total_datasets,
                'total_file_size': total_file_size,
                'total_rows': total_rows,
                'average_quality_score': round(average_quality_score, 1),
                'timeframes': timeframes,
                'exchanges': exchanges,
                'symbols': symbols
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")
