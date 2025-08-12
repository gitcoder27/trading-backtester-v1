import pandas as pd
import numpy as np
import pytest
from backtester.engine import BacktestEngineRefactored as BacktestEngine, OptionsPnLCalculator
from backtester.strategy_base import StrategyBase

@pytest.fixture
def sample_market_data():
    """Fixture for a small, predictable market data DataFrame."""
    dates = pd.to_datetime(pd.date_range(start="2023-01-01", periods=10))
    data = {
        'timestamp': dates,
        'open': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        'high': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        'low': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
    }
    return pd.DataFrame(data)

class SimpleTestStrategy(StrategyBase):
    """A simple strategy that generates a long signal on bar 2 and a short signal on bar 6."""
    def __init__(self, params=None):
        super().__init__(params)
        # For the current engine, we need to provide the exit logic parameters
        self.params = params or {'profit_target': 2, 'stop_loss': 2}

    def generate_signals(self, data):
        df = data.copy()
        df['signal'] = 0
        df.loc[2, 'signal'] = 1  # Long entry at index 2 (price 102)
        df.loc[6, 'signal'] = -1 # Short entry at index 6 (price 106)

        # The current engine needs an 'ema' column for its exit logic.
        # We'll provide a dummy one that doesn't interfere with PT/SL.
        df['ema'] = np.nan
        df.loc[df['signal'] == 1, 'ema'] = df['close'] - 50
        df.loc[df['signal'] == -1, 'ema'] = df['close'] + 50
        df['ema'].ffill(inplace=True)
        return df

    def should_exit(self, position, row, entry_price):
        # This method is used by the old engine, but the new Numba engine has the logic hardcoded.
        # This highlights a design issue to be fixed later. For now, we test the Numba engine.
        return False, ""


def test_engine_long_trade_pt(sample_market_data):
    """Test a simple long trade that hits the profit target."""
    strategy = SimpleTestStrategy(params={'profit_target': 2, 'stop_loss': 10})
    engine = BacktestEngine(sample_market_data, strategy)

    results = engine.run()
    trade_log = results['trade_log']

    assert len(trade_log) == 2
    trade = trade_log[trade_log['direction'] == 'long'].iloc[0]

    assert trade['direction'] == 'long'
    assert trade['entry_price'] == 102 # Entry on bar 2
    assert trade['exit_price'] == 104  # Exit on bar 4 (102 + 2 PT)


def test_engine_short_trade_sl(sample_market_data):
    """Test a simple short trade that hits the stop loss."""
    # Modify the data to trigger a stop loss on the short trade
    sample_market_data.loc[8, 'close'] = 108 # SL for short from 106 is 108

    strategy = SimpleTestStrategy(params={'profit_target': 10, 'stop_loss': 2})
    engine = BacktestEngine(sample_market_data, strategy)

    results = engine.run()
    trade_log = results['trade_log']

    # We expect two trades now, the first long one and the second short one
    assert len(trade_log) == 2

    short_trade = trade_log[trade_log['direction'] == 'short'].iloc[0]

    assert short_trade['entry_price'] == 106 # Entry on bar 6
    assert short_trade['exit_price'] == 108  # Exit on bar 8 (106 + 2 SL)
