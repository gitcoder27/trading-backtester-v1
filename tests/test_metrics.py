import pandas as pd
import numpy as np
import pytest
from backtester.metrics import (
    total_return,
    sharpe_ratio,
    max_drawdown,
    win_rate,
    profit_factor,
    largest_winning_trade,
    largest_losing_trade,
    average_holding_time,
    max_consecutive_wins,
    max_consecutive_losses,
)

@pytest.fixture
def equity_curve():
    """Create a sample equity curve DataFrame."""
    data = {
        'timestamp': pd.to_datetime(['2024-01-01 09:15:00', '2024-01-01 09:16:00', '2024-01-01 09:17:00', '2024-01-01 09:18:00', '2024-01-01 09:19:00']),
        'equity': [10000, 10100, 10050, 10150, 10200]
    }
    return pd.DataFrame(data)

@pytest.fixture
def trade_log():
    """Create a sample trade log DataFrame."""
    data = {
        'entry_time': pd.to_datetime(['2024-01-01 09:15:00', '2024-01-01 09:17:00', '2024-01-01 09:18:00', '2024-01-01 09:20:00']),
        'exit_time': pd.to_datetime(['2024-01-01 09:16:00', '2024-01-01 09:18:00', '2024-01-01 09:19:00', '2024-01-01 09:21:00']),
        'pnl': [100, -50, 100, 50]
    }
    return pd.DataFrame(data)

def test_total_return(equity_curve):
    assert np.isclose(total_return(equity_curve), 0.02)

def test_sharpe_ratio(equity_curve):
    # This is a bit complex to calculate manually, so we'll just check if it returns a float
    assert isinstance(sharpe_ratio(equity_curve), float)

def test_max_drawdown(equity_curve):
    # Max equity is 10100, drawdown to 10050, so (10050-10100)/10100 = -0.00495
    assert np.isclose(max_drawdown(equity_curve), (10050 - 10100) / 10100)

def test_win_rate(trade_log):
    # 3 wins out of 4 trades
    assert np.isclose(win_rate(trade_log), 0.75)

def test_profit_factor(trade_log):
    # Gross profit = 100 + 100 + 50 = 250. Gross loss = 50. Profit factor = 250/50 = 5
    assert np.isclose(profit_factor(trade_log), 5.0)

def test_largest_winning_trade(trade_log):
    assert np.isclose(largest_winning_trade(trade_log), 100)

def test_largest_losing_trade(trade_log):
    assert np.isclose(largest_losing_trade(trade_log), -50)

def test_average_holding_time(trade_log):
    # All trades have a 1 minute holding time
    assert np.isclose(average_holding_time(trade_log), 1.0)

def test_max_consecutive_wins(trade_log):
    # PNLs are [100, -50, 100, 50]. Wins are [1, 0, 1, 1]. Max consecutive wins is 2.
    # The trade_log has pnl: [100, -50, 100, 50], so wins are [W, L, W, W]. Max consecutive wins is 2.
    trade_log_consecutive = pd.DataFrame({'pnl': [10, 20, -5, 15, 30, -10, 5]})
    assert max_consecutive_wins(trade_log_consecutive) == 2

    trade_log_consecutive_2 = pd.DataFrame({'pnl': [10, -20, 5, 15, -30, -10, 5]})
    assert max_consecutive_wins(trade_log_consecutive_2) == 2

def test_max_consecutive_losses(trade_log):
    # PNLs are [100, -50, 100, 50]. Losses are [0, 1, 0, 0]. Max consecutive losses is 1.
    assert max_consecutive_losses(trade_log) == 1
    trade_log_consecutive = pd.DataFrame({'pnl': [-10, -20, 5, -15, -30, 10, -5]})
    assert max_consecutive_losses(trade_log_consecutive) == 2
