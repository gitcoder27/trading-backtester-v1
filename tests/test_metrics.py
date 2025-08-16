import pandas as pd
import numpy as np
import pytest
from backtester import metrics


def make_equity_curve():
    return pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=5, freq='T'),
        'equity': [100, 110, 105, 115, 120],
    })


def make_trade_log():
    return pd.DataFrame({
        'entry_time': pd.date_range('2024-01-01', periods=3, freq='T'),
        'exit_time': pd.date_range('2024-01-01 00:01', periods=3, freq='T'),
        'pnl': [10, -5, 15],
    })


def test_total_return():
    eq = make_equity_curve()
    assert metrics.total_return(eq) == pytest.approx(0.2)


def test_sharpe_ratio():
    eq = make_equity_curve()
    sr = metrics.sharpe_ratio(eq)
    assert np.isfinite(sr)


def test_max_drawdown():
    eq = make_equity_curve()
    md = metrics.max_drawdown(eq)
    assert md == pytest.approx(0.0454545, rel=1e-4)


def test_win_rate_and_profit_factor():
    tl = make_trade_log()
    assert metrics.win_rate(tl) == pytest.approx(2/3)
    pf = metrics.profit_factor(tl)
    assert pf == pytest.approx((10+15)/5)


def test_largest_trades():
    tl = make_trade_log()
    assert metrics.largest_winning_trade(tl) == 15
    assert metrics.largest_losing_trade(tl) == -5


def test_average_holding_time_and_consecutive():
    tl = make_trade_log()
    avg = metrics.average_holding_time(tl)
    assert avg == 1
    assert metrics.max_consecutive_wins(tl) == 1
    assert metrics.max_consecutive_losses(tl) == 1


def test_trading_sessions():
    eq = make_equity_curve()
    days = metrics.trading_sessions_days(eq)
    years = metrics.trading_sessions_years(eq, trading_days_per_year=252)
    assert days == 1
    assert years == pytest.approx(1/252)


def test_sharpe_ratio_zero_std():
    eq = pd.DataFrame({'timestamp': pd.date_range('2024-01-01', periods=3, freq='T'), 'equity': [100, 100, 100]})
    assert np.isnan(metrics.sharpe_ratio(eq))


def test_profit_factor_no_losses():
    tl = pd.DataFrame({'pnl': [5, 10], 'entry_time': pd.date_range('2024', periods=2, freq='T'), 'exit_time': pd.date_range('2024', periods=2, freq='T')})
    assert metrics.profit_factor(tl) == np.inf


def test_max_consecutive_count_empty():
    assert metrics._max_consecutive_count([]) == 0
