import pandas as pd
import numpy as np
import pytest
from backtester.metrics import (
    total_return,
    sharpe_ratio,
    max_drawdown,
    win_rate,
    profit_factor,
)

@pytest.fixture
def sample_equity_curve():
    """Fixture for a sample equity curve."""
    dates = pd.to_datetime(pd.date_range(start="2023-01-01", periods=10))
    equity = pd.Series([100, 110, 105, 115, 120, 110, 100, 95, 105, 110], index=dates)
    return pd.DataFrame({'timestamp': dates, 'equity': equity})

@pytest.fixture
def flat_equity_curve():
    """Fixture for a flat equity curve (no returns)."""
    dates = pd.to_datetime(pd.date_range(start="2023-01-01", periods=10))
    equity = pd.Series([100] * 10, index=dates)
    return pd.DataFrame({'timestamp': dates, 'equity': equity})

@pytest.fixture
def sample_trade_log():
    """Fixture for a sample trade log."""
    trades = [
        {'pnl': 10}, {'pnl': -5}, {'pnl': 20}, {'pnl': -10}, {'pnl': 15}
    ]
    return pd.DataFrame(trades)

def test_total_return(sample_equity_curve):
    """Test the total_return function."""
    # (110 - 100) / 100 = 0.1
    assert total_return(sample_equity_curve) == pytest.approx(0.1)

def test_total_return_empty():
    """Test total_return with an empty DataFrame."""
    empty_curve = pd.DataFrame(columns=['timestamp', 'equity'])
    assert total_return(empty_curve) == 0.0

def test_sharpe_ratio(sample_equity_curve):
    """Test the sharpe_ratio function with an explicit periods_per_year."""
    # We are checking if it returns a plausible float, not the exact value.
    # The default is now 252, so we'll test with a different value.
    sharpe = sharpe_ratio(sample_equity_curve, periods_per_year=365)
    assert isinstance(sharpe, float)
    assert not np.isnan(sharpe)

def test_sharpe_ratio_no_volatility(flat_equity_curve):
    """Test sharpe_ratio with zero volatility."""
    assert np.isnan(sharpe_ratio(flat_equity_curve))

def test_sharpe_ratio_insufficient_data():
    """Test sharpe_ratio with insufficient data to calculate returns."""
    dates = pd.to_datetime(pd.date_range(start="2023-01-01", periods=1))
    equity = pd.Series([100], index=dates)
    insufficient_curve = pd.DataFrame({'timestamp': dates, 'equity': equity})
    assert np.isnan(sharpe_ratio(insufficient_curve))

def test_max_drawdown(sample_equity_curve):
    """Test the max_drawdown function."""
    # Max equity is 120. Drawdown points are 110, 100, 95.
    # Drawdowns from 120: (110-120)/120 = -0.0833, (100-120)/120 = -0.1667, (95-120)/120 = -0.2083
    # Max drawdown is at 95.
    assert max_drawdown(sample_equity_curve) == pytest.approx((95 - 120) / 120)

def test_win_rate(sample_trade_log):
    """Test the win_rate function."""
    # 3 wins out of 5 trades = 0.6
    assert win_rate(sample_trade_log) == pytest.approx(0.6)

def test_win_rate_no_trades():
    """Test win_rate with an empty trade log."""
    empty_log = pd.DataFrame(columns=['pnl'])
    assert np.isnan(win_rate(empty_log))

def test_profit_factor(sample_trade_log):
    """Test the profit_factor function."""
    # Gross profit = 10 + 20 + 15 = 45
    # Gross loss = 5 + 10 = 15
    # Profit factor = 45 / 15 = 3.0
    assert profit_factor(sample_trade_log) == pytest.approx(3.0)

def test_profit_factor_no_losses():
    """Test profit_factor with no losing trades."""
    winning_trades = pd.DataFrame([{'pnl': 10}, {'pnl': 20}])
    assert profit_factor(winning_trades) == np.inf
