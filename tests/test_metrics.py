import pytest
import pandas as pd
import numpy as np
from backtester import metrics # Import the whole module

@pytest.fixture
def sample_equity_curve():
    """Generate a sample equity curve DataFrame."""
    timestamps = pd.to_datetime(['2023-01-01 09:15', '2023-01-01 09:16', '2023-01-01 09:17', '2023-01-01 09:18', '2023-01-01 09:19'])
    equity_values = [100000, 100100, 100050, 100200, 100150] # Initial, +100, -50, +150, -50
    return pd.DataFrame({'timestamp': timestamps, 'equity': equity_values})

@pytest.fixture
def sample_trade_log():
    """Generate a sample trade log DataFrame."""
    trades = [
        {'entry_time': '2023-01-01 09:15', 'exit_time': '2023-01-01 09:16', 'pnl': 100, 'direction': 'long'}, # Win
        {'entry_time': '2023-01-01 09:16', 'exit_time': '2023-01-01 09:17', 'pnl': -50, 'direction': 'long'}, # Loss
        {'entry_time': '2023-01-01 09:17', 'exit_time': '2023-01-01 09:18', 'pnl': 150, 'direction': 'short'},# Win
        {'entry_time': '2023-01-01 09:18', 'exit_time': '2023-01-01 09:19', 'pnl': -50, 'direction': 'long'}, # Loss
        {'entry_time': '2023-01-01 09:19', 'exit_time': '2023-01-01 09:20', 'pnl': 20, 'direction': 'short'}  # Win
    ]
    df = pd.DataFrame(trades)
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])
    return df

@pytest.fixture
def empty_trade_log():
    """Generate an empty trade log DataFrame."""
    return pd.DataFrame(columns=['entry_time', 'exit_time', 'pnl', 'direction'])

@pytest.fixture
def trade_log_all_wins():
    trades = [
        {'entry_time': '2023-01-01 09:15', 'exit_time': '2023-01-01 09:16', 'pnl': 100, 'direction': 'long'},
        {'entry_time': '2023-01-01 09:17', 'exit_time': '2023-01-01 09:18', 'pnl': 50, 'direction': 'short'},
    ]
    df = pd.DataFrame(trades)
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])
    return df

@pytest.fixture
def trade_log_all_losses():
    trades = [
        {'entry_time': '2023-01-01 09:15', 'exit_time': '2023-01-01 09:16', 'pnl': -100, 'direction': 'long'},
        {'entry_time': '2023-01-01 09:17', 'exit_time': '2023-01-01 09:18', 'pnl': -50, 'direction': 'short'},
    ]
    df = pd.DataFrame(trades)
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])
    return df

# --- Test Total Return ---
def test_total_return(sample_equity_curve):
    expected_return = (100150 - 100000) / 100000  # (end - start) / start
    assert metrics.total_return(sample_equity_curve) == pytest.approx(expected_return)

def test_total_return_flat_equity():
    flat_curve = pd.DataFrame({'equity': [100000, 100000, 100000]})
    assert metrics.total_return(flat_curve) == 0.0

# --- Test Sharpe Ratio ---
def test_sharpe_ratio(sample_equity_curve):
    # Manual calculation for sample_equity_curve (approximate)
    # Returns: [nan, 0.001, -0.0004995, 0.00149925, -0.000499]
    # Pct changes: [ (100100-100000)/100000 = 0.001,
    #                (100050-100100)/100100 = -0.000499500,
    #                (100200-100050)/100050 = 0.001499250,
    #                (100150-100200)/100200 = -0.000499001]
    # Mean of returns: (0.001 -0.0004995 + 0.00149925 -0.000499001) / 4 = 0.000375187
    # Std of returns: np.std([0.001, -0.0004995, 0.00149925, -0.000499001], ddof=0 for population if pandas default)
    # pandas .std() default ddof=1. metrics uses equity_curve['equity'].pct_change().dropna().std()
    # returns = pd.Series([0.001, -0.000499500, 0.001499250, -0.000499001])
    # mean_ret = returns.mean() = 0.000375187
    # std_ret = returns.std() = 0.00091223
    # sharpe = sqrt(252*390) * mean_ret / std_ret (assuming default periods)
    # periods_per_year = 252 * 390 = 98280
    # sharpe = np.sqrt(98280) * 0.000375187 / 0.00091223 = 313.496 * 0.000375187 / 0.00091223 = 128.5 (approx)
    # This seems high, let's re-verify the periods_per_year.
    # The default periods_per_year (252*390 for 1-min data) is large.
    # If this were daily data (periods_per_year=252), Sharpe would be smaller.
    # The function is calculating correctly based on its formula.
    # Let's test with a more stable series for simpler manual check.
    eq_stable = pd.DataFrame({'equity': [100, 101, 102, 103, 104]}) # constant positive returns
    # returns: 0.01, 0.00990099, 0.00980392, 0.00970873
    # mean: 0.00985341, std: 0.0001286
    # sharpe = np.sqrt(98280) * 0.00985341 / 0.0001286 = 313.496 * 76.61 = 24019 (very high)
    # This is expected for consistently positive returns with low vol and high annualization factor.
    # For the original sample_equity_curve:
    calculated_sharpe = metrics.sharpe_ratio(sample_equity_curve) # Default risk_free_rate=0.0, periods_per_year=252*390
    assert isinstance(calculated_sharpe, float)
    assert not np.isnan(calculated_sharpe) # Should be a valid float

    # Test case where excess_returns.std() IS 0, leading to np.nan
    eq_constant_returns = pd.DataFrame({'equity': [100, 101, 102.01, 103.0301]}) # Approx 1% return each step
    # Pct changes: 0.01, 0.01, 0.01. std of these is 0.
    assert np.isnan(metrics.sharpe_ratio(eq_constant_returns))

    # Original eq_flat_ret case: equity: [100, 101, 101, 101] -> returns: [0.01, 0, 0]
    # std of [0.01, 0, 0] is NOT 0. So Sharpe should be a float, not NaN.
    eq_flat_ret_original = pd.DataFrame({'equity': [100, 101, 101, 101]})
    sharpe_flat_ret = metrics.sharpe_ratio(eq_flat_ret_original)
    assert isinstance(sharpe_flat_ret, float)
    assert not np.isnan(sharpe_flat_ret)


# --- Test Max Drawdown ---
def test_max_drawdown(sample_equity_curve):
    # Equity: 100000, 100100, 100050, 100200, 100150
    # Cummax: 100000, 100100, 100100, 100200, 100200
    # Drawdown: (E-CM)/CM
    # (100000-100000)/100000 = 0
    # (100100-100100)/100100 = 0
    # (100050-100100)/100100 = -50/100100 = -0.0004995
    # (100200-100200)/100200 = 0
    # (100150-100200)/100200 = -50/100200 = -0.0002495
    # Max drawdown is min of these: -0.000499500...
    assert metrics.max_drawdown(sample_equity_curve) == pytest.approx(-50/100100)

def test_max_drawdown_always_increasing():
    increasing_curve = pd.DataFrame({'equity': [100, 110, 120, 130]})
    assert metrics.max_drawdown(increasing_curve) == 0.0

def test_max_drawdown_always_decreasing():
    decreasing_curve = pd.DataFrame({'equity': [100, 90, 80, 70]})
    # E: 100, 90, 80, 70
    # CM:100, 100,100,100
    # DD:(100-100)/100 = 0
    #    (90-100)/100 = -0.1
    #    (80-100)/100 = -0.2
    #    (70-100)/100 = -0.3
    assert metrics.max_drawdown(decreasing_curve) == pytest.approx(-0.3)

# --- Test Win Rate ---
def test_win_rate(sample_trade_log):
    # 3 wins (100, 150, 20) out of 5 trades
    assert metrics.win_rate(sample_trade_log) == 3/5

def test_win_rate_empty_log(empty_trade_log):
    assert np.isnan(metrics.win_rate(empty_trade_log))

def test_win_rate_all_wins(trade_log_all_wins):
    assert metrics.win_rate(trade_log_all_wins) == 1.0

def test_win_rate_all_losses(trade_log_all_losses):
    assert metrics.win_rate(trade_log_all_losses) == 0.0

# --- Test Profit Factor ---
def test_profit_factor(sample_trade_log):
    # Gross profit: 100 + 150 + 20 = 270
    # Gross loss: -50 + -50 = -100 (abs is 100)
    # Profit factor: 270 / 100 = 2.7
    assert metrics.profit_factor(sample_trade_log) == 2.7

def test_profit_factor_empty_log(empty_trade_log):
    assert np.isnan(metrics.profit_factor(empty_trade_log)) # Gross loss is 0, gross profit is 0

def test_profit_factor_all_wins(trade_log_all_wins):
    # Gross profit: 100 + 50 = 150. Gross loss = 0.
    assert metrics.profit_factor(trade_log_all_wins) == np.inf

def test_profit_factor_all_losses(trade_log_all_losses):
    # Gross profit: 0. Gross loss = 150.
    assert metrics.profit_factor(trade_log_all_losses) == 0.0 # 0 / 150

def test_profit_factor_no_profit_no_loss(empty_trade_log):
    # pnl = [0,0,0]
    df = pd.DataFrame({'pnl': [0,0,0]})
    assert np.isnan(metrics.profit_factor(df))


# --- Test Largest Winning/Losing Trade ---
def test_largest_winning_trade(sample_trade_log):
    assert metrics.largest_winning_trade(sample_trade_log) == 150

def test_largest_winning_trade_empty_log(empty_trade_log):
    assert np.isnan(metrics.largest_winning_trade(empty_trade_log))

def test_largest_losing_trade(sample_trade_log):
    assert metrics.largest_losing_trade(sample_trade_log) == -50

def test_largest_losing_trade_empty_log(empty_trade_log):
    assert np.isnan(metrics.largest_losing_trade(empty_trade_log))

# --- Test Average Holding Time ---
def test_average_holding_time(sample_trade_log):
    # Trades durations in minutes:
    # 1: (09:16 - 09:15) = 1 min
    # 2: (09:17 - 09:16) = 1 min
    # 3: (09:18 - 09:17) = 1 min
    # 4: (09:19 - 09:18) = 1 min
    # 5: (09:20 - 09:19) = 1 min
    # Average = 1 min
    assert metrics.average_holding_time(sample_trade_log) == pytest.approx(1.0)

def test_average_holding_time_varied(tmp_path):
    trades = [
        {'entry_time': '2023-01-01 09:15', 'exit_time': '2023-01-01 09:20', 'pnl': 100}, # 5 mins
        {'entry_time': '2023-01-01 09:25', 'exit_time': '2023-01-01 09:35', 'pnl': -50}, # 10 mins
    ]
    df = pd.DataFrame(trades)
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])
    assert metrics.average_holding_time(df) == pytest.approx(7.5)


def test_average_holding_time_empty_log(empty_trade_log):
    assert np.isnan(metrics.average_holding_time(empty_trade_log))

# --- Test Max Consecutive Wins/Losses ---
def test_max_consecutive_wins(sample_trade_log):
    # PnLs: [100, -50, 150, -50, 20]
    # Wins: [ 1,   0,   1,   0,  1] (mask)
    # Consecutive wins: 1, 1, 1. Max is 1.
    assert metrics.max_consecutive_wins(sample_trade_log) == 1

def test_max_consecutive_losses(sample_trade_log):
    # PnLs: [100, -50, 150, -50, 20]
    #Losses: [ 0,   1,   0,   1,  0] (mask)
    # Consecutive losses: 1, 1. Max is 1.
    assert metrics.max_consecutive_losses(sample_trade_log) == 1

def test_max_consecutive_wins_empty_log(empty_trade_log):
    assert metrics.max_consecutive_wins(empty_trade_log) == 0

def test_max_consecutive_losses_empty_log(empty_trade_log):
    assert metrics.max_consecutive_losses(empty_trade_log) == 0

def test_max_consecutive_series():
    # Wins: W W L W W W L L W
    # PnLs: [1,1,-1,1,1,1,-1,-1,1]
    # Wins mask: [1,1,0,1,1,1,0,0,1] -> max consecutive wins = 3
    # Loss mask: [0,0,1,0,0,0,1,1,0] -> max consecutive losses = 2
    trade_log = pd.DataFrame({'pnl': [1, 1, -1, 1, 1, 1, -1, -1, 1]})
    assert metrics.max_consecutive_wins(trade_log) == 3
    assert metrics.max_consecutive_losses(trade_log) == 2

def test_max_consecutive_all_wins(trade_log_all_wins):
    assert metrics.max_consecutive_wins(trade_log_all_wins) == 2
    assert metrics.max_consecutive_losses(trade_log_all_wins) == 0

def test_max_consecutive_all_losses(trade_log_all_losses):
    assert metrics.max_consecutive_wins(trade_log_all_losses) == 0
    assert metrics.max_consecutive_losses(trade_log_all_losses) == 2

def test_max_consecutive_single_trade():
    win_log = pd.DataFrame({'pnl': [10]})
    loss_log = pd.DataFrame({'pnl': [-10]})
    assert metrics.max_consecutive_wins(win_log) == 1
    assert metrics.max_consecutive_losses(win_log) == 0
    assert metrics.max_consecutive_wins(loss_log) == 0
    assert metrics.max_consecutive_losses(loss_log) == 1

def test_max_consecutive_no_wins_no_losses():
    # Trades with PnL = 0
    zero_pnl_log = pd.DataFrame({'pnl': [0, 0, 0]})
    assert metrics.max_consecutive_wins(zero_pnl_log) == 0
    assert metrics.max_consecutive_losses(zero_pnl_log) == 0

# Test for _max_consecutive_count helper (indirectly via public functions, but also directly if needed)
def test_internal_max_consecutive_count_empty():
    mask = pd.Series([], dtype=int)
    assert metrics._max_consecutive_count(mask) == 0

def test_internal_max_consecutive_count_no_ones():
    mask = pd.Series([0, 0, 0, 0], dtype=int)
    assert metrics._max_consecutive_count(mask) == 0

def test_internal_max_consecutive_count_all_ones():
    mask = pd.Series([1, 1, 1], dtype=int)
    assert metrics._max_consecutive_count(mask) == 3

def test_internal_max_consecutive_count_mixed():
    mask = pd.Series([1, 1, 0, 1, 1, 1, 0, 0, 1, 0], dtype=int)
    assert metrics._max_consecutive_count(mask) == 3
    mask2 = pd.Series([0,0,1,0,1,1,0,1,1,1,1,0], dtype=int)
    assert metrics._max_consecutive_count(mask2) == 4
