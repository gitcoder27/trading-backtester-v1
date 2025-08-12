"""
data_loader.py
Utility functions for loading and preprocessing historical trading data.
"""

import pandas as pd

def load_csv(filepath, timeframe='1T'):
    """
    Load historical data from a CSV file and resample if needed.
    timeframe: pandas offset alias (e.g. '1T', '2T', '5T', '10T').
    Returns a pandas DataFrame.
    """
    df = pd.read_csv(filepath)
    # Parse timestamps while preserving timezone information
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')
    if timeframe != '1T':
        df = df.resample(timeframe).agg({
            'open':  'first',
            'high':  'max',
            'low':   'min',
            'close': 'last',
            'volume':'sum'
        }).dropna()
    df = df.reset_index()
    return df