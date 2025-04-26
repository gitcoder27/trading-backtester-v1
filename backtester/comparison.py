"""
comparison.py
Comparison table generation for backtest reporting.
"""
import pandas as pd
from typing import List, Dict, Optional

def comparison_table(results: list, filepath: Optional[str]=None) -> pd.DataFrame:
    """
    Generate a comparison table for multiple strategies.
    Args:
        results: List of dicts with keys: 'strategy', 'total_return', 'sharpe', 'max_drawdown', 'win_rate'
        filepath: Optional path to save the table as CSV
    Returns:
        pd.DataFrame: The comparison table
    """
    df = pd.DataFrame(results)
    if filepath:
        df.to_csv(filepath, index=False)
    return df
