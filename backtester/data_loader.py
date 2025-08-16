"""
data_loader.py
Optimized utility functions for loading and preprocessing historical trading data.
"""

import pandas as pd
import numpy as np

def load_csv(filepath, timeframe='1min'):
    """
    Optimized loading of historical data from a CSV file with memory efficiency.
    timeframe: pandas offset alias (e.g. '1min', '2min', '5min', '10min').
    Returns a pandas DataFrame.
    """
    # Specify dtypes for better memory usage
    dtype_dict = {
        'open': 'float32',
        'high': 'float32', 
        'low': 'float32',
        'close': 'float32',
        'volume': 'int32'
    }
    
    # Use chunking for large files to avoid memory issues
    try:
        df = pd.read_csv(
            filepath, 
            dtype=dtype_dict,
            parse_dates=['timestamp'],
            date_format='ISO8601'  # Faster parsing for ISO format
        )
    except Exception:
        # Fallback to standard loading if optimized version fails
        df = pd.read_csv(filepath)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Set index for efficient resampling
    df = df.set_index('timestamp')
    
    # Only resample if needed (avoid unnecessary computation)
    if timeframe != '1min':
        # Use efficient aggregation
        agg_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        }
        
        # Only include volume if it exists
        if 'volume' in df.columns:
            agg_dict['volume'] = 'sum'
            
        df = df.resample(timeframe).agg(agg_dict).dropna()
    
    # Reset index and ensure proper column order
    df = df.reset_index()
    
    # Ensure required columns exist
    required_cols = ['timestamp', 'open', 'high', 'low', 'close']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in data")
    
    return df

def optimize_dataframe_memory(df):
    """
    Optimize DataFrame memory usage by downcasting numeric types.
    """
    for col in df.columns:
        if df[col].dtype == 'float64':
            df[col] = pd.to_numeric(df[col], downcast='float')
        elif df[col].dtype == 'int64':
            df[col] = pd.to_numeric(df[col], downcast='integer')
    
    return df
