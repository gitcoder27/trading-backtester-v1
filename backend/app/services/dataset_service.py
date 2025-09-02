"""
Dataset management service for upload, validation, and quality analysis
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import hashlib

from backend.app.database.models import get_session_factory, Dataset


class DatasetService:
    """Service for managing dataset uploads and quality analysis"""
    
    def __init__(self, data_dir: str = "data/market_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.SessionLocal = get_session_factory()
    
    def upload_dataset(
        self,
        file_name: str,
        file_content: bytes,
        name: Optional[str] = None,
        symbol: Optional[str] = None,
        exchange: Optional[str] = None,
        data_source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload and process a new dataset
        
        Args:
            file_name: Original filename
            file_content: Raw CSV file content
            name: Human-readable name for the dataset
            symbol: Trading symbol (e.g., 'NIFTY')
            exchange: Exchange name (e.g., 'NSE')
            data_source: Source of the data (e.g., 'Yahoo Finance')
            
        Returns:
            Dict with dataset metadata and quality analysis
        """
        # Generate unique filename to avoid conflicts
        file_hash = hashlib.md5(file_content).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file_hash}_{file_name}"
        file_path = self.data_dir / safe_filename
        
        # Save file to disk
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Analyze the dataset
        try:
            analysis = self._analyze_dataset(file_path)
            
            # Create database record
            db = self.SessionLocal()
            try:
                dataset = Dataset(
                    name=name or file_name,
                    filename=file_name,
                    file_path=str(file_path),
                    file_size=len(file_content),
                    rows_count=analysis['rows_count'],
                    columns=analysis['columns'],
                    timeframe=analysis['timeframe'],
                    start_date=analysis['start_date'],
                    end_date=analysis['end_date'],
                    missing_data_pct=analysis['missing_data_pct'],
                    data_quality_score=analysis['quality_score'],
                    has_gaps=analysis['has_gaps'],
                    timezone=analysis['timezone'],
                    symbol=symbol,
                    exchange=exchange,
                    data_source=data_source,
                    quality_checks=analysis['quality_checks']
                )
                
                db.add(dataset)
                db.commit()
                db.refresh(dataset)
                
                return {
                    'success': True,
                    'dataset_id': dataset.id,
                    'dataset': self._dataset_to_dict(dataset),
                    'analysis': analysis
                }
                
            finally:
                db.close()
                
        except Exception as e:
            # Clean up file if analysis fails
            if file_path.exists():
                file_path.unlink()
            raise ValueError(f"Failed to analyze dataset: {str(e)}")
    
    def get_dataset_quality(self, dataset_id: int) -> Dict[str, Any]:
        """Get quality analysis for a dataset"""
        db = self.SessionLocal()
        try:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                raise ValueError(f"Dataset {dataset_id} not found")
            
            # Update last accessed
            dataset.last_accessed = datetime.utcnow()
            db.commit()
            
            # Re-run quality analysis if needed
            if not dataset.quality_checks:
                analysis = self._analyze_dataset(Path(dataset.file_path))
                dataset.quality_checks = analysis['quality_checks']
                dataset.data_quality_score = analysis['quality_score']
                db.commit()
            
            return {
                'success': True,
                'dataset_id': dataset.id,
                'dataset': self._dataset_to_dict(dataset),
                'quality_analysis': dataset.quality_checks
            }
            
        finally:
            db.close()
    
    def list_datasets(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all datasets with basic metadata"""
        db = self.SessionLocal()
        try:
            datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).limit(limit).all()
            return [self._dataset_to_dict(dataset, include_quality=False) for dataset in datasets]
        finally:
            db.close()
    
    def delete_dataset(self, dataset_id: int) -> Dict[str, Any]:
        """Delete a dataset and its file"""
        db = self.SessionLocal()
        try:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                raise ValueError(f"Dataset {dataset_id} not found")
            
            # Delete file
            file_path = Path(dataset.file_path)
            if file_path.exists():
                file_path.unlink()
            
            # Delete database record
            db.delete(dataset)
            db.commit()
            
            return {
                'success': True,
                'message': f"Dataset {dataset_id} deleted successfully"
            }
            
        finally:
            db.close()
    
    def _analyze_dataset(self, file_path: Path) -> Dict[str, Any]:
        """Perform comprehensive analysis of a dataset"""
        try:
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            # Basic info
            rows_count = len(df)
            columns = list(df.columns)
            
            # Detect timestamp column
            timestamp_col = self._detect_timestamp_column(df)
            if timestamp_col:
                df[timestamp_col] = pd.to_datetime(df[timestamp_col])
                df = df.sort_values(timestamp_col)
                start_date = df[timestamp_col].min()
                end_date = df[timestamp_col].max()
                timeframe = self._detect_timeframe(df[timestamp_col])
                timezone_info = self._detect_timezone(df[timestamp_col])
            else:
                start_date = end_date = None
                timeframe = "unknown"
                timezone_info = "unknown"
            
            # Quality checks
            quality_checks = {
                'has_timestamp': timestamp_col is not None,
                'required_columns': self._check_required_columns(df),
                'missing_data': self._check_missing_data(df),
                'data_types': self._check_data_types(df),
                'timestamp_gaps': self._check_timestamp_gaps(df, timestamp_col) if timestamp_col else {},
                'outliers': self._check_outliers(df),
                'duplicates': self._check_duplicates(df, timestamp_col)
            }
            
            # Calculate overall quality score
            quality_score = self._calculate_quality_score(quality_checks)
            
            # Check for gaps
            has_gaps = quality_checks['timestamp_gaps'].get('has_gaps', False)
            
            # Missing data percentage
            missing_data_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
            
            # Make everything JSON serializable
            analysis = {
                'rows_count': rows_count,
                'columns': columns,
                'timeframe': timeframe,
                'start_date': start_date,
                'end_date': end_date,
                'missing_data_pct': float(missing_data_pct),
                'quality_score': quality_score,
                'has_gaps': bool(has_gaps),
                'timezone': timezone_info,
                'quality_checks': self._make_json_serializable(quality_checks)
            }
            
            return analysis
            
        except Exception as e:
            raise ValueError(f"Failed to analyze dataset: {str(e)}")
    
    def _detect_timestamp_column(self, df: pd.DataFrame) -> Optional[str]:
        """Detect the timestamp column in the dataframe"""
        # Common timestamp column names
        timestamp_candidates = ['timestamp', 'time', 'date', 'datetime', 'Date', 'Time', 'DateTime']
        
        # Check if index is datetime
        if pd.api.types.is_datetime64_any_dtype(df.index):
            return df.index.name or 'index'
        
        # Check columns
        for col in timestamp_candidates:
            if col in df.columns:
                try:
                    pd.to_datetime(df[col].head(10))  # Test conversion
                    return col
                except:
                    continue
        
        # Try to find any column that looks like datetime
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    sample = df[col].dropna().head(10)
                    if len(sample) > 0:
                        pd.to_datetime(sample)
                        return col
                except:
                    continue
        
        return None
    
    def _detect_timeframe(self, timestamp_series: pd.Series) -> str:
        """Detect the timeframe of the data"""
        if len(timestamp_series) < 2:
            return "unknown"
        
        # Calculate time differences
        time_diffs = timestamp_series.diff().dropna()
        mode_diff = time_diffs.mode()
        
        if len(mode_diff) == 0:
            return "unknown"
        
        diff_seconds = mode_diff.iloc[0].total_seconds()
        
        if diff_seconds == 60:
            return "1min"
        elif diff_seconds == 300:
            return "5min"
        elif diff_seconds == 900:
            return "15min"
        elif diff_seconds == 3600:
            return "1h"
        elif diff_seconds == 86400:
            return "1d"
        else:
            return f"{int(diff_seconds)}s"
    
    def _detect_timezone(self, timestamp_series: pd.Series) -> str:
        """Detect timezone information"""
        if hasattr(timestamp_series.dtype, 'tz') and timestamp_series.dtype.tz:
            return str(timestamp_series.dtype.tz)
        return "naive"
    
    def _check_required_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check for required OHLCV columns"""
        required_cols = ['open', 'high', 'low', 'close']
        optional_cols = ['volume']
        
        missing_required = [col for col in required_cols if col not in df.columns]
        missing_optional = [col for col in optional_cols if col not in df.columns]
        
        return {
            'has_all_required': len(missing_required) == 0,
            'missing_required': missing_required,
            'missing_optional': missing_optional,
            'available_columns': list(df.columns)
        }
    
    def _check_missing_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check for missing data patterns"""
        missing_by_column = df.isnull().sum().to_dict()
        total_missing = sum(missing_by_column.values())
        total_cells = len(df) * len(df.columns)
        missing_pct = (total_missing / total_cells) * 100
        
        return {
            'total_missing': total_missing,
            'missing_percentage': missing_pct,
            'missing_by_column': missing_by_column,
            'has_missing': total_missing > 0
        }
    
    def _check_data_types(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check data types for numeric columns"""
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        type_issues = {}
        
        for col in numeric_cols:
            if col in df.columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    type_issues[col] = str(df[col].dtype)
        
        return {
            'numeric_columns_correct': len(type_issues) == 0,
            'type_issues': type_issues,
            'column_types': {col: str(df[col].dtype) for col in df.columns}
        }
    
    def _check_timestamp_gaps(self, df: pd.DataFrame, timestamp_col: str) -> Dict[str, Any]:
        """Check for gaps in timestamp data"""
        if not timestamp_col or timestamp_col not in df.columns:
            return {'has_gaps': False, 'gap_count': 0}
        
        timestamps = pd.to_datetime(df[timestamp_col]).sort_values()
        if len(timestamps) < 2:
            return {'has_gaps': False, 'gap_count': 0}
        
        # Calculate expected frequency
        time_diffs = timestamps.diff().dropna()
        expected_freq = time_diffs.mode().iloc[0] if len(time_diffs.mode()) > 0 else None
        
        if not expected_freq:
            return {'has_gaps': False, 'gap_count': 0}
        
        # Find gaps larger than expected
        large_gaps = time_diffs[time_diffs > expected_freq * 1.5]
        
        return {
            'has_gaps': len(large_gaps) > 0,
            'gap_count': len(large_gaps),
            'largest_gap': large_gaps.max() if len(large_gaps) > 0 else None,
            'expected_frequency': str(expected_freq)
        }
    
    def _check_outliers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check for price outliers"""
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        outliers = {}
        
        for col in numeric_cols:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outlier_count = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
                outliers[col] = {
                    'count': outlier_count,
                    'percentage': (outlier_count / len(df)) * 100
                }
        
        total_outliers = sum(data['count'] for data in outliers.values())
        
        return {
            'has_outliers': total_outliers > 0,
            'total_outliers': total_outliers,
            'by_column': outliers
        }
    
    def _check_duplicates(self, df: pd.DataFrame, timestamp_col: str) -> Dict[str, Any]:
        """Check for duplicate timestamps"""
        if not timestamp_col or timestamp_col not in df.columns:
            return {'has_duplicates': False, 'duplicate_count': 0}
        
        duplicate_count = df[timestamp_col].duplicated().sum()
        
        return {
            'has_duplicates': duplicate_count > 0,
            'duplicate_count': duplicate_count,
            'unique_timestamps': df[timestamp_col].nunique(),
            'total_rows': len(df)
        }
    
    def _calculate_quality_score(self, quality_checks: Dict[str, Any]) -> float:
        """Calculate overall quality score (0-100)"""
        score = 100.0
        
        # Deduct for missing required columns
        if not quality_checks['required_columns']['has_all_required']:
            score -= 30
        
        # Deduct for missing data
        missing_pct = quality_checks['missing_data']['missing_percentage']
        score -= min(missing_pct * 2, 20)  # Max 20 points deduction
        
        # Deduct for wrong data types
        if not quality_checks['data_types']['numeric_columns_correct']:
            score -= 15
        
        # Deduct for timestamp gaps
        if quality_checks['timestamp_gaps']['has_gaps']:
            gap_count = quality_checks['timestamp_gaps']['gap_count']
            score -= min(gap_count * 2, 15)  # Max 15 points deduction
        
        # Deduct for outliers
        if quality_checks['outliers']['has_outliers']:
            outlier_pct = sum(data['percentage'] for data in quality_checks['outliers']['by_column'].values())
            score -= min(outlier_pct / 10, 10)  # Max 10 points deduction
        
        # Deduct for duplicates
        if quality_checks['duplicates']['has_duplicates']:
            dup_pct = (quality_checks['duplicates']['duplicate_count'] / quality_checks['duplicates']['total_rows']) * 100
            score -= min(dup_pct, 10)  # Max 10 points deduction
        
        return max(0.0, round(score, 1))
    
    def _make_json_serializable(self, obj):
        """Convert numpy types and other non-serializable types to JSON-compatible types"""
        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, pd.Timedelta):
            return str(obj)
        elif obj is None or isinstance(obj, (bool, int, float, str)):
            return obj
        else:
            return str(obj)  # Convert anything else to string
    
    def _dataset_to_dict(self, dataset: Dataset, include_quality: bool = True) -> Dict[str, Any]:
        """Convert dataset model to dictionary"""
        result = {
            'id': dataset.id,
            'name': dataset.name,
            'filename': dataset.filename,
            'file_path': dataset.file_path,
            'file_size': dataset.file_size,
            'rows_count': dataset.rows_count,
            'columns': dataset.columns,
            'timeframe': dataset.timeframe,
            'start_date': dataset.start_date.isoformat() if dataset.start_date else None,
            'end_date': dataset.end_date.isoformat() if dataset.end_date else None,
            'missing_data_pct': dataset.missing_data_pct,
            'data_quality_score': dataset.data_quality_score,
            'has_gaps': dataset.has_gaps,
            'timezone': dataset.timezone,
            'symbol': dataset.symbol,
            'exchange': dataset.exchange,
            'data_source': dataset.data_source,
            'backtest_count': dataset.backtest_count,
            'created_at': dataset.created_at.isoformat() if dataset.created_at else None,
            'last_accessed': dataset.last_accessed.isoformat() if dataset.last_accessed else None
        }
        
        if include_quality and dataset.quality_checks:
            result['quality_checks'] = dataset.quality_checks
        
        return result

    def get_dataset_data(self, dataset_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Load actual data from a dataset file
        
        Args:
            dataset_id: ID of the dataset to load
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            
        Returns:
            Dict containing the dataset data and metadata
        """
        db = self.SessionLocal()
        try:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if not dataset:
                return {'success': False, 'error': 'Dataset not found'}
            
            if not os.path.exists(dataset.file_path):
                return {'success': False, 'error': 'Dataset file not found on disk'}
            
            # Load the data
            try:
                df = pd.read_csv(dataset.file_path)
                
                # Try to identify timestamp column
                timestamp_col = None
                for col in ['timestamp', 'time', 'datetime', 'date', 'Timestamp', 'DateTime', 'Date']:
                    if col in df.columns:
                        timestamp_col = col
                        break
                
                if timestamp_col:
                    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
                    
                    # Apply date filters if provided
                    if start_date:
                        start_dt = pd.to_datetime(start_date)
                        df = df[df[timestamp_col] >= start_dt]
                    
                    if end_date:
                        end_dt = pd.to_datetime(end_date)
                        df = df[df[timestamp_col] <= end_dt]
                    
                    # Sort by timestamp
                    df = df.sort_values(timestamp_col).reset_index(drop=True)
                
                # Convert DataFrame to records (list of dicts)
                data_records = df.to_dict('records')
                
                # Update last accessed time
                dataset.last_accessed = datetime.now(timezone.utc)
                db.commit()
                
                return {
                    'success': True,
                    'dataset_id': dataset_id,
                    'data': data_records,
                    'rows_count': len(data_records),
                    'columns': list(df.columns),
                    'date_range': {
                        'start': df[timestamp_col].min().isoformat() if timestamp_col and not df.empty else None,
                        'end': df[timestamp_col].max().isoformat() if timestamp_col and not df.empty else None,
                    } if timestamp_col else None,
                    'metadata': self._dataset_to_dict(dataset, include_quality=False)
                }
                
            except Exception as e:
                return {'success': False, 'error': f'Error loading dataset: {str(e)}'}
                
        finally:
            db.close()
