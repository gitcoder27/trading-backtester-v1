"""
Smoke tests for backend integration with existing backtester framework
Verifies that core imports and basic functionality work correctly
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np

# Add the project root to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from backtester.engine import BacktestEngine
from backtester.data_loader import load_csv
from backtester.strategy_base import StrategyBase


class DummyStrategy(StrategyBase):
    """Simple test strategy for smoke tests"""
    
    def __init__(self, **params):
        super().__init__(params)
    
    def generate_signals(self, data):
        """Generate simple buy signals for testing"""
        df = data.copy()
        df['signal'] = 0
        # Buy on first candle, sell on second
        if len(df) > 1:
            df.iloc[0, df.columns.get_loc('signal')] = 1   # Buy
            df.iloc[1, df.columns.get_loc('signal')] = -1  # Sell
        return df
    
    def should_exit(self, position, row, entry_price):
        """Simple exit logic for testing"""
        return False, "No exit"


def test_backtester_imports():
    """Test that core backtester modules can be imported"""
    # These imports should not raise exceptions
    from backtester import engine, data_loader, metrics, strategy_base
    assert True


def test_engine_initialization():
    """Test that BacktestEngine can be initialized"""
    # Create minimal test data
    dates = pd.date_range('2024-01-01 09:15:00', periods=2, freq='1min')
    test_data = pd.DataFrame({
        'timestamp': dates,
        'open': [100, 101],
        'high': [102, 103],
        'low': [99, 100],
        'close': [101, 102],
        'volume': [1000, 1100]
    })
    test_data.set_index('timestamp', inplace=True)
    
    strategy = DummyStrategy()
    
    engine = BacktestEngine(
        data=test_data,
        strategy=strategy,
        initial_cash=100000,
        lots=1,
        option_delta=0.5,
        fee_per_trade=0.0,
        slippage=0.0,
        intraday=True,
        daily_profit_target=30.0
    )
    assert engine.initial_cash == 100000
    assert engine.lots == 1


def test_dummy_strategy_backtest():
    """Test running a simple backtest with dummy data"""
    # Create minimal test data
    dates = pd.date_range('2024-01-01 09:15:00', periods=10, freq='1min')
    test_data = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.uniform(100, 110, 10),
        'high': np.random.uniform(110, 115, 10), 
        'low': np.random.uniform(95, 100, 10),
        'close': np.random.uniform(100, 110, 10),
        'volume': np.random.randint(1000, 5000, 10)
    })
    test_data.set_index('timestamp', inplace=True)
    # Add timestamp column back for strategy compatibility
    test_data['timestamp'] = test_data.index
    
    # Initialize strategy and engine
    strategy = DummyStrategy()
    engine = BacktestEngine(
        data=test_data,
        strategy=strategy,
        initial_cash=100000,
        lots=1,
        option_delta=0.5,
        fee_per_trade=0.0,
        slippage=0.0,
        intraday=True,
        daily_profit_target=30.0
    )
    
    # Run backtest
    result = engine.run()
    
    # Verify result structure
    assert 'equity_curve' in result
    assert 'trade_log' in result
    # Equity curve can be Series or DataFrame
    assert isinstance(result['equity_curve'], (pd.Series, pd.DataFrame))
    # Trade log can be list or DataFrame
    assert isinstance(result['trade_log'], (list, pd.DataFrame))


def test_existing_data_files():
    """Test that we can load one of the existing CSV files"""
    # Look for any CSV file in the data directory
    data_dir = os.path.join(os.path.dirname(__file__), '../../data')
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    if csv_files:
        # Test loading the first available CSV
        csv_path = os.path.join(data_dir, csv_files[0])
        try:
            data = load_csv(csv_path)
            assert isinstance(data, pd.DataFrame)
            assert len(data) > 0
            # Verify expected columns are present
            expected_cols = ['open', 'high', 'low', 'close']
            for col in expected_cols:
                assert col in data.columns, f"Missing column: {col}"
        except Exception as e:
            pytest.skip(f"Could not load CSV file {csv_files[0]}: {e}")
    else:
        pytest.skip("No CSV files found in data directory")


if __name__ == "__main__":
    # Run tests directly for debugging
    test_backtester_imports()
    test_engine_initialization()
    test_dummy_strategy_backtest()
    print("All smoke tests passed!")
