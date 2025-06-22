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
    df = pd.read_csv(filepath, parse_dates=False) # Read timestamp as string first
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce') # Coerce invalid dates to NaT

    # Drop rows where timestamp became NaT, as they cannot be processed reliably
    df.dropna(subset=['timestamp'], inplace=True)
    if df.empty: # If all rows had invalid timestamps
        return df.reset_index(drop=True)


    df = df.set_index('timestamp')
    if timeframe != '1T' and timeframe != '1min': # Allow '1min' as equivalent to '1T'
        # Use 'min' for future compatibility if 'T' is fully removed.
        # For now, assume timeframe is passed correctly (e.g. '2min', '5T')
        # The warning comes from pandas when 'T' is used in resample.
        # If timeframe itself is '1T', we skip resampling.
        # If it's '2T', '5T', etc., it will use 'T'.
        # If it's '2min', '5min', it will use 'min'.
        # The test uses '2T', so the warning is expected for now unless we change the test's input.
        # To fix the warning source, we could replace 'T' with 'min' if timeframe ends with 'T'.
        # For example: if timeframe.endswith('T'): timeframe = timeframe[:-1] + 'min'

        # Let's apply the fix for 'T' to 'min' here to remove the warning
        current_timeframe = timeframe
        if isinstance(timeframe, str) and timeframe.endswith('T'):
            current_timeframe = timeframe[:-1] + 'min'
            if timeframe == '1T': # Special case, if '1T' was meant to be '1min' and not skip
                current_timeframe = '1min'

        # The original logic only resamples if timeframe is NOT '1T'.
        # If '1min' is passed, it should also skip resampling if data is already 1-min.
        # The check `if timeframe != '1T':` handles this.
        # To also make `if timeframe != '1min':` skip, we'd need to adjust.
        # The simplest way is to ensure '1T' and '1min' are treated as "no resampling needed for 1-min base data".
        # The current problem is the FutureWarning from using '2T', '5T', etc.

        df = df.resample(current_timeframe).agg({
            'open':  'first',
            'high':  'max',
            'low':   'min',
            'close': 'last',
            'volume':'sum'
        }).dropna()
    df = df.reset_index()
    return df