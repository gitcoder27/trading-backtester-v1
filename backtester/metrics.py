"""
metrics.py
Functions for calculating backtest performance metrics.
"""

import numpy as np

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
    """
    equity = equity_curve['equity']
    roll_max = equity.cummax()
    drawdown = (equity - roll_max) / roll_max
    return drawdown.min()

def win_rate(trade_log):
    """
    Calculate the win rate from the trade log.
    """
    if len(trade_log) == 0:
        return np.nan
    wins = (trade_log['pnl'] > 0).sum()
    return wins / len(trade_log)