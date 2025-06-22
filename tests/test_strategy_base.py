import pytest
from backtester.strategy_base import StrategyBase
import pandas as pd

class DummyStrategy(StrategyBase):
    # A concrete class for testing purposes, does not override methods
    pass

class ConcreteStrategy(StrategyBase):
    def generate_signals(self, data):
        signals = pd.Series(index=data.index, dtype=int)
        signals.iloc[0] = 1 # Buy signal
        signals.iloc[1] = -1 # Sell signal
        return data.assign(signal=signals.fillna(0))

    def should_exit(self, position, row, entry_price):
        if position == 'long' and row.close < entry_price * 0.9: # Exit on 10% loss
            return True, "Stop Loss"
        if position == 'short' and row.close > entry_price * 1.1: # Exit on 10% loss
            return True, "Stop Loss"
        return False, None

def test_strategy_base_generate_signals_not_implemented():
    """Test that StrategyBase.generate_signals raises NotImplementedError."""
    strategy = DummyStrategy()
    data = pd.DataFrame({'close': [10, 11, 12]})
    with pytest.raises(NotImplementedError, match="generate_signals must be implemented by the strategy."):
        strategy.generate_signals(data)

def test_strategy_base_should_exit_not_implemented():
    """Test that StrategyBase.should_exit raises NotImplementedError."""
    strategy = DummyStrategy()
    row = pd.Series({'close': 10}) # Mock row object
    with pytest.raises(NotImplementedError, match="should_exit must be implemented by the strategy."):
        strategy.should_exit('long', row, 9)

def test_concrete_strategy_can_be_instantiated():
    """Test that a concrete strategy inheriting from StrategyBase can be instantiated."""
    strategy = ConcreteStrategy()
    assert strategy is not None
    assert strategy.params == {}

def test_concrete_strategy_with_params():
    """Test that a concrete strategy can be instantiated with parameters."""
    params = {'param1': 10, 'param2': 'value'}
    strategy = ConcreteStrategy(params=params)
    assert strategy.params == params

def test_concrete_strategy_generate_signals():
    """Test that a concrete strategy's generate_signals method works as expected."""
    strategy = ConcreteStrategy()
    data = pd.DataFrame({
        'timestamp': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']),
        'open': [10, 11, 12],
        'high': [10.5, 11.5, 12.5],
        'low': [9.5, 10.5, 11.5],
        'close': [10, 11, 12]
    })
    processed_data = strategy.generate_signals(data)
    assert 'signal' in processed_data.columns
    assert processed_data['signal'].iloc[0] == 1
    assert processed_data['signal'].iloc[1] == -1
    assert processed_data['signal'].iloc[2] == 0

def test_concrete_strategy_should_exit():
    """Test that a concrete strategy's should_exit method works as expected."""
    strategy = ConcreteStrategy()

    # Test long position exit
    long_row_exit = pd.Series({'close': 8.9}) # Price dropped below 10% SL
    long_row_no_exit = pd.Series({'close': 9.5}) # Price dropped but not enough for SL

    exit_now, reason = strategy.should_exit('long', long_row_exit, 10)
    assert exit_now is True
    assert reason == "Stop Loss"

    exit_now, reason = strategy.should_exit('long', long_row_no_exit, 10)
    assert exit_now is False
    assert reason is None

    # Test short position exit
    short_row_exit = pd.Series({'close': 11.1}) # Price rose above 10% SL
    short_row_no_exit = pd.Series({'close': 10.5}) # Price rose but not enough for SL

    exit_now, reason = strategy.should_exit('short', short_row_exit, 10)
    assert exit_now is True
    assert reason == "Stop Loss"

    exit_now, reason = strategy.should_exit('short', short_row_no_exit, 10)
    assert exit_now is False
    assert reason is None
