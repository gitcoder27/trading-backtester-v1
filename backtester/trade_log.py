"""
trade_log.py
Save or export trade logs for backtest reporting.
"""
import pandas as pd

def save_trade_log(trade_log: pd.DataFrame, filepath: str) -> None:
    """
    Save the trade log to a CSV file, with cumulative and daily PnL columns.
    """
    trade_log = trade_log.copy()
    trade_log['final_pnl'] = trade_log['pnl'].cumsum()
    entry_time = pd.to_datetime(trade_log['entry_time'])
    trade_log['entry_time'] = entry_time
    trade_log['trade_date'] = trade_log['entry_time'].dt.date
    trade_log['day_pnl'] = trade_log.groupby('trade_date')['pnl'].cumsum()
    trade_log.to_csv(filepath, index=False)
