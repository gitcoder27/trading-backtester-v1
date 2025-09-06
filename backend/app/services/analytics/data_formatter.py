"""
Data Formatter
Utility functions for formatting and converting data structures
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json


class DataFormatter:
    """Utility class for data formatting and conversion operations"""
    
    @staticmethod
    def safe_float(value: Any, default: float = 0.0) -> float:
        """Safely convert value to float with fallback"""
        try:
            if pd.isna(value):
                return default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_int(value: Any, default: int = 0) -> int:
        """Safely convert value to int with fallback"""
        try:
            if pd.isna(value):
                return default
            return int(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def format_timestamp(timestamp: Any) -> Optional[str]:
        """Convert timestamp to ISO string format"""
        try:
            if pd.isna(timestamp):
                return None
            if isinstance(timestamp, pd.Timestamp):
                return timestamp.isoformat()
            elif isinstance(timestamp, np.datetime64):
                return pd.Timestamp(timestamp).isoformat()
            elif isinstance(timestamp, datetime):
                return timestamp.isoformat()
            else:
                # Try to parse as datetime
                dt = pd.to_datetime(timestamp)
                return dt.isoformat()
        except Exception:
            return None
    
    @staticmethod
    def clean_dataframe_for_json(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert DataFrame to JSON-serializable list of dictionaries"""
        if df.empty:
            return []
        
        records = []
        for _, row in df.iterrows():
            record = {}
            for key, value in row.items():
                if pd.isna(value):
                    record[key] = None
                elif isinstance(value, pd.Timestamp):
                    record[key] = value.isoformat()
                elif isinstance(value, np.datetime64):
                    record[key] = pd.Timestamp(value).isoformat()
                elif isinstance(value, (np.int64, np.int32)):
                    record[key] = int(value)
                elif isinstance(value, (np.float64, np.float32)):
                    record[key] = float(value)
                else:
                    record[key] = value
            records.append(record)
        
        return records

    @staticmethod
    def sanitize_json(data: Any) -> Any:
        """Recursively sanitize data for JSON serialization.

        - Converts NaN/Inf/-Inf floats to 0.0
        - Converts numpy types to native Python types
        - Leaves structures (dict/list) intact while sanitizing children
        """
        import math
        import numpy as np

        # Primitives
        if isinstance(data, float):
            if math.isnan(data) or math.isinf(data):
                return 0.0
            return float(data)
        if isinstance(data, (np.floating,)):
            val = float(data)
            if math.isnan(val) or math.isinf(val):
                return 0.0
            return val
        if isinstance(data, (np.integer,)):
            return int(data)
        if isinstance(data, (np.bool_,)):
            return bool(data)

        # Containers
        if isinstance(data, dict):
            return {k: DataFormatter.sanitize_json(v) for k, v in data.items()}
        if isinstance(data, list):
            return [DataFormatter.sanitize_json(v) for v in data]

        # Leave other types as-is (str, None, etc.)
        return data
    
    @staticmethod
    def get_column_mapping(columns: List[str]) -> Dict[str, str]:
        """
        Create a mapping from actual column names to standardized names.
        Handles different naming conventions (timestamp, time, date, etc.)
        """
        mapping = {}
        
        # Map timestamp column
        for col in columns:
            if col.lower() in ['timestamp', 'time', 'datetime', 'date']:
                mapping['timestamp'] = col
                break
        
        # Map OHLC columns
        ohlc_mappings = {
            'open': ['open', 'Open', 'OPEN', 'o'],
            'high': ['high', 'High', 'HIGH', 'h'],
            'low': ['low', 'Low', 'LOW', 'l'],
            'close': ['close', 'Close', 'CLOSE', 'c']
        }
        
        for standard_name, variants in ohlc_mappings.items():
            for col in columns:
                if col in variants:
                    mapping[standard_name] = col
                    break
        
        return mapping
    
    @staticmethod
    def normalize_returns_data(equity_curve: pd.DataFrame) -> pd.Series:
        """Extract and normalize returns from equity curve"""
        if equity_curve.empty or 'equity' not in equity_curve.columns:
            return pd.Series([], dtype=float)
        
        try:
            equity_values = equity_curve['equity'].astype(float)
            if len(equity_values) < 2:
                return pd.Series([], dtype=float)
            
            returns = equity_values.pct_change().dropna()
            
            # Use timestamp index if available
            if 'timestamp' in equity_curve.columns:
                try:
                    timestamps = pd.to_datetime(equity_curve['timestamp'])
                    if len(timestamps) == len(returns) + 1:  # Account for first NaN from pct_change
                        returns.index = timestamps.iloc[1:]
                except Exception:
                    pass  # Keep default index if timestamp parsing fails
            
            return returns
        except Exception:
            return pd.Series([], dtype=float)
    
    @staticmethod
    def calculate_annualization_factor(data_frequency: str = 'minute') -> float:
        """Calculate annualization factor based on data frequency"""
        factors = {
            'minute': 252 * 60 * 6.5,  # 252 trading days * 60 min/hour * 6.5 hours/day
            'hour': 252 * 6.5,         # 252 trading days * 6.5 hours/day
            'daily': 252,              # 252 trading days
            'weekly': 52,              # 52 weeks
            'monthly': 12              # 12 months
        }
        return factors.get(data_frequency.lower(), 252)
    
    @staticmethod
    def validate_required_columns(df: pd.DataFrame, required_cols: List[str]) -> Dict[str, Any]:
        """Validate that DataFrame has required columns"""
        if df.empty:
            return {
                'valid': False,
                'error': 'DataFrame is empty',
                'missing_columns': required_cols
            }
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return {
                'valid': False,
                'error': f'Missing required columns: {missing_cols}',
                'missing_columns': missing_cols,
                'available_columns': list(df.columns)
            }
        
        return {'valid': True}
    
    @staticmethod
    def format_percentage(value: float, decimal_places: int = 2) -> str:
        """Format value as percentage string"""
        try:
            return f"{value:.{decimal_places}f}%"
        except (ValueError, TypeError):
            return "0.00%"
    
    @staticmethod
    def format_currency(value: float, currency: str = "$") -> str:
        """Format value as currency string"""
        try:
            return f"{currency}{value:,.2f}"
        except (ValueError, TypeError):
            return f"{currency}0.00"
