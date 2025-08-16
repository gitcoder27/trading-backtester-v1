"""
metrics.py
Functions for calculating backtest performance metrics.
"""

import numpy as np
import pandas as pd

def total_return(equity_curve):
    """
    Calculate total return from the equity curve.
    """
    start = equity_curve['equity'].iloc[0]
    end = equity_curve['equity'].iloc[-1]
    return (end - start) / start

def sharpe_ratio(equity_curve, risk_free_rate=0.0, periods_per_year=252*390):
    """
    Calculate the Sharpe ratio.
    Assumes equity_curve is at 1-minute frequency (252 trading days, 390 minutes per day).
    """
    returns = equity_curve['equity'].pct_change().dropna()
    excess_returns = returns - (risk_free_rate / periods_per_year)
    if excess_returns.std() == 0:
        return np.nan
    sharpe = np.sqrt(periods_per_year) * excess_returns.mean() / excess_returns.std()
    return sharpe

def max_drawdown(equity_curve):
    """
    Calculate the maximum drawdown.

    Returns the magnitude of the largest peak-to-trough decline in the
    equity curve as a positive percentage.
    """
    equity = equity_curve['equity']
    roll_max = equity.cummax()
    drawdown = (equity - roll_max) / roll_max
    # drawdown values are negative; convert to positive magnitude
    return -drawdown.min()

def win_rate(trade_log):
    """
    Calculate the win rate from the trade log.
    """
    if len(trade_log) == 0:
        return np.nan
    wins = (trade_log['pnl'] > 0).sum()
    return wins / len(trade_log)

def profit_factor(trade_log):
    """
    Calculate the profit factor: gross profit / gross loss.
    """
    if len(trade_log) == 0:
        return np.nan
    gross_profit = trade_log.loc[trade_log['pnl'] > 0, 'pnl'].sum()
    gross_loss = trade_log.loc[trade_log['pnl'] < 0, 'pnl'].sum()
    if gross_loss == 0:
        return np.inf if gross_profit > 0 else np.nan
    return gross_profit / abs(gross_loss)

def largest_winning_trade(trade_log):
    """
    Return the largest winning trade PnL.
    """
    if len(trade_log) == 0:
        return np.nan
    return trade_log['pnl'].max()

def largest_losing_trade(trade_log):
    """
    Return the largest losing trade PnL.
    """
    if len(trade_log) == 0:
        return np.nan
    return trade_log['pnl'].min()

def average_holding_time(trade_log):
    """
    Calculate the average holding time of trades (in minutes).
    Assumes 'entry_time' and 'exit_time' are pandas datetime or convertible.
    """
    if len(trade_log) == 0:
        return np.nan
    entry = pd.to_datetime(trade_log['entry_time'])
    exit = pd.to_datetime(trade_log['exit_time'])
    holding_times = (exit - entry).dt.total_seconds() / 60
    return holding_times.mean()

def max_consecutive_wins(trade_log):
    """
    Calculate the maximum consecutive winning trades.
    """
    if len(trade_log) == 0:
        return 0
    win_mask = (trade_log['pnl'] > 0).astype(int)
    return _max_consecutive_count(win_mask)

def max_consecutive_losses(trade_log):
    """
    Calculate the maximum consecutive losing trades.
    """
    if len(trade_log) == 0:
        return 0
    loss_mask = (trade_log['pnl'] < 0).astype(int)
    return _max_consecutive_count(loss_mask)

def _max_consecutive_count(mask):
    # Vectorized helper for counting max consecutive 1s in a Series
    # mask should be a pandas Series or 1D numpy array of 0/1
    mask = pd.Series(mask)
    if mask.empty:
        return 0
    # Find runs of 1s
    is_one = mask == 1
    group = (is_one != is_one.shift()).cumsum()
    runs = is_one.groupby(group).sum()
    return runs.max() if not runs.empty else 0


def trading_sessions_days(equity_curve: pd.DataFrame) -> int:
    """
    Count the number of unique trading sessions (days) present in the equity curve.
    This uses the actual timestamps in the data, so holidays/weekends with no data
    are naturally excluded.
    """
    if equity_curve is None or len(equity_curve) == 0 or 'timestamp' not in equity_curve.columns:
        return 0
    dates = pd.to_datetime(equity_curve['timestamp']).dt.date
    return int(pd.Series(dates).nunique())


def trading_sessions_years(equity_curve: pd.DataFrame, trading_days_per_year: int = 252) -> float:
    """
    Convert trading session days into years using a given trading-days-per-year basis (default 252).
    """
    days = trading_sessions_days(equity_curve)
    if trading_days_per_year <= 0:
        return np.nan
    return days / float(trading_days_per_year)