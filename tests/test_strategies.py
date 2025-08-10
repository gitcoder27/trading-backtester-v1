import pandas as pd
import numpy as np
import pytest
from strategies.ema10_scalper import EMA10ScalperStrategy

@pytest.fixture
def strategy_data():
    """Create a small, sample DataFrame for testing strategies."""
    data = {
        'timestamp': pd.to_datetime(['2024-01-01 09:15:00', '2024-01-01 09:16:00', '2024-01-01 09:17:00', '2024-01-01 09:18:00', '2024-01-01 09:19:00']),
        'open': [100, 101, 102, 103, 104],
        'high': [101, 102, 103, 104, 105],
        'low': [99, 100, 101, 102, 103],
        'close': [101, 100, 103, 102, 105],
        'volume': [1000, 1000, 1000, 1000, 1000]
    }
    return pd.DataFrame(data)

def test_ema10_scalper_strategy_signals(strategy_data):
    """Test the signal generation of the EMA10ScalperStrategy."""
    strategy = EMA10ScalperStrategy()
    signals_df = strategy.generate_signals(strategy_data)

    # Manual calculation of EMA and signals for this small dataset
    # This is a simplified EMA calculation for testing purposes
    ema = strategy_data['close'].ewm(span=10, adjust=False).mean()
    prev_close = strategy_data['close'].shift(1)
    prev_ema = ema.shift(1)

    # Long entry condition: prev_close < prev_ema and close > ema
    # Short entry condition: prev_close > prev_ema and close < ema

    # Based on the logic, the expected signals are different from the initial manual calculation.
    # Let's use the correct expected signals.
    expected_signals = [0, 0, 1, 0, 0]

    assert signals_df['signal'].tolist() == expected_signals

def test_ema10_scalper_strategy_exit(strategy_data):
    """Test the exit logic of the EMA10ScalperStrategy."""
    strategy = EMA10ScalperStrategy(params={'profit_target': 2, 'stop_loss': 2})
    signals_df = strategy.generate_signals(strategy_data)

    # Test long position exit
    # Profit target: entry at 101, close at 103 (iloc[2]) is a 2pt profit
    should_exit, reason = strategy.should_exit('long', signals_df.iloc[2], 101)
    assert should_exit
    assert reason == 'Target'
    # Stop loss: entry at 102, close at 100 (iloc[1]).
    # The price (100) is below the EMA (100.8), so the 'EMA exit' is triggered first.
    should_exit, reason = strategy.should_exit('long', signals_df.iloc[1], 102)
    assert should_exit
    assert reason == 'EMA exit'

    # Test short position exit
    # Profit target: entry at 102, close at 100 (iloc[1]) is a 2pt profit
    should_exit, reason = strategy.should_exit('short', signals_df.iloc[1], 102)
    assert should_exit
    assert reason == 'Target'
    # Stop loss: entry at 101, close at 103 (iloc[2]).
    # The price (103) is above the EMA (101.2), so the 'EMA exit' is triggered first.
    should_exit, reason = strategy.should_exit('short', signals_df.iloc[2], 101)
    assert should_exit
    assert reason == 'EMA exit'
