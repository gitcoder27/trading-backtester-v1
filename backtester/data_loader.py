"""
data_loader.py
Utility functions for loading and preprocessing historical trading data.
"""

import pandas as pd

def load_csv(filepath):
    """
    Load historical data from a CSV file.
    Returns a pandas DataFrame.
    """
    return pd.read_csv(filepath, parse_dates=['timestamp'])