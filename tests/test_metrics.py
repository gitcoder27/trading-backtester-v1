import pandas as pd
import numpy as np
import pytest
from backtester import metrics


def make_equity_curve():
    return pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=5, freq='min'),
        'equity': [100, 110, 105, 115, 120],
    })


def make_trade_log():
    return pd.DataFrame({
        'entry_time': pd.date_range('2024-01-01', periods=3, freq='min'),
        'exit_time': pd.date_range('2024-01-01 00:01', periods=3, freq='min'),
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
    eq = pd.DataFrame({'timestamp': pd.date_range('2024-01-01', periods=3, freq='min'), 'equity': [100, 100, 100]})
    assert np.isnan(metrics.sharpe_ratio(eq))


def test_profit_factor_no_losses():
    tl = pd.DataFrame({'pnl': [5, 10], 'entry_time': pd.date_range('2024', periods=2, freq='min'), 'exit_time': pd.date_range('2024', periods=2, freq='min')})
    assert metrics.profit_factor(tl) == np.inf


def test_max_consecutive_count_empty():
    assert metrics._max_consecutive_count([]) == 0


def test_daily_profit_target_stats():
    tl = pd.DataFrame({
        'entry_time': pd.to_datetime([
            '2024-01-01 09:30',
            '2024-01-01 10:00',
            '2024-01-02 09:30',
            '2024-01-02 10:00',
        ]),
        'exit_time': pd.date_range('2024-01-01 09:45', periods=4, freq='30min'),
        'pnl': [8, 5, -2, 3],
    })
    stats = metrics.daily_profit_target_stats(tl, daily_target=10)
    assert stats['days_traded'] == 2
    assert stats['days_target_hit'] == 1
    assert stats['target_hit_rate'] == pytest.approx(0.5)
    assert stats['max_daily_pnl'] == 13
    assert stats['min_daily_pnl'] == 1
    assert stats['avg_daily_pnl'] == pytest.approx(7.0)


def test_empty_trade_log():
    empty_trade_log = pd.DataFrame(columns=['entry_time', 'exit_time', 'pnl'])
    assert np.isnan(metrics.win_rate(empty_trade_log))
    assert np.isnan(metrics.profit_factor(empty_trade_log))
    assert np.isnan(metrics.largest_winning_trade(empty_trade_log))
    assert np.isnan(metrics.largest_losing_trade(empty_trade_log))
    assert np.isnan(metrics.average_holding_time(empty_trade_log))
    assert metrics.max_consecutive_wins(empty_trade_log) == 0
    assert metrics.max_consecutive_losses(empty_trade_log) == 0
    stats = metrics.daily_profit_target_stats(empty_trade_log, daily_target=10)
    assert stats['days_traded'] == 0
    assert stats['days_target_hit'] == 0
    assert np.isnan(stats['target_hit_rate'])
    assert np.isnan(stats['max_daily_pnl'])
    assert np.isnan(stats['min_daily_pnl'])
    assert np.isnan(stats['avg_daily_pnl'])

def test_max_drawdown_with_drawdown():
    eq_curve = pd.DataFrame({
        'timestamp': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05']),
        'equity': [100, 120, 110, 100, 130]
    })
    assert metrics.max_drawdown(eq_curve) == pytest.approx(0.16666666666666669)

def test_profit_factor_zero_loss():
    trade_log_wins = pd.DataFrame({'pnl': [10, 20]})
    assert metrics.profit_factor(trade_log_wins) == np.inf
    trade_log_no_wins = pd.DataFrame({'pnl': [0, 0]})
    assert np.isnan(metrics.profit_factor(trade_log_no_wins))

def test_trading_sessions_days_non_empty():
    eq_curve = pd.DataFrame({
        'timestamp': pd.to_datetime(['2024-01-01', '2024-01-01', '2024-01-02']),
        'equity': [100, 110, 105]
    })
    assert metrics.trading_sessions_days(eq_curve) == 2

def test_trading_sessions_years_invalid_input():
    eq_curve = pd.DataFrame({
        'timestamp': pd.to_datetime(['2024-01-01']),
        'equity': [100]
    })
    assert np.isnan(metrics.trading_sessions_years(eq_curve, trading_days_per_year=0))
    assert np.isnan(metrics.trading_sessions_years(eq_curve, trading_days_per_year=-1))


def test_trading_sessions_days_empty_and_none():
    assert metrics.trading_sessions_days(None) == 0
    assert metrics.trading_sessions_days(pd.DataFrame()) == 0
    assert metrics.trading_sessions_days(pd.DataFrame({'equity': [100]})) == 0
