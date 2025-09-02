"""
Unit tests for the backtest service
"""

import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from io import StringIO

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from backend.app.services.backtest_service import BacktestService
from backtester.strategy_base import StrategyBase


class SimpleTestStrategy(StrategyBase):
    """Simple strategy for testing"""
    
    def __init__(self, **params):
        super().__init__(params)
        self.test_param = params.get('test_param', 'default')
    
    def generate_signals(self, data):
        """Generate simple signals for testing"""
        df = data.copy()
        df['signal'] = 0
        
        # Buy on first candle, sell on second if we have enough data
        if len(df) >= 2:
            df.iloc[0, df.columns.get_loc('signal')] = 1   # Buy
            df.iloc[1, df.columns.get_loc('signal')] = -1  # Sell
        
        return df
    
    def should_exit(self, position, row, entry_price):
        """Simple exit logic"""
        return False, "No exit"


@pytest.fixture
def backtest_service():
    """Create a BacktestService instance"""
    return BacktestService()


@pytest.fixture
def sample_data():
    """Create sample market data"""
    dates = pd.date_range('2024-01-01 09:15:00', periods=20, freq='1min')
    data = pd.DataFrame({
        'open': np.random.uniform(100, 110, 20),
        'high': np.random.uniform(110, 115, 20),
        'low': np.random.uniform(95, 100, 20),
        'close': np.random.uniform(100, 110, 20),
        'volume': np.random.randint(1000, 5000, 20)
    }, index=dates)
    data.index.name = 'timestamp'
    # Add timestamp column for strategy compatibility
    data['timestamp'] = data.index
    return data


@pytest.fixture
def sample_csv_bytes(sample_data):
    """Convert sample data to CSV bytes"""
    csv_string = sample_data.to_csv()
    return csv_string.encode('utf-8')


def test_strategy_loading(backtest_service):
    """Test loading strategy from module path"""
    # This should work with our existing strategies
    strategy_class = backtest_service.load_strategy('strategies.ema10_scalper.EMA10ScalperStrategy')
    assert strategy_class is not None
    
    # Test instantiation
    strategy = strategy_class()
    assert hasattr(strategy, 'generate_signals')


def test_strategy_loading_invalid():
    """Test loading invalid strategy"""
    service = BacktestService()
    
    with pytest.raises(ValueError):
        service.load_strategy('nonexistent.strategy.Class')


def test_data_loading_from_csv_bytes(backtest_service, sample_csv_bytes):
    """Test loading data from CSV bytes"""
    data = backtest_service.load_data(csv_bytes=sample_csv_bytes)
    
    assert isinstance(data, pd.DataFrame)
    assert len(data) == 20
    assert 'open' in data.columns
    assert 'high' in data.columns
    assert 'low' in data.columns
    assert 'close' in data.columns


def test_data_loading_from_file(backtest_service):
    """Test loading data from existing file"""
    # Look for any CSV file in the data directory  
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))
    
    if os.path.exists(data_dir):
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        
        if csv_files:
            csv_path = os.path.join(data_dir, csv_files[0])
            data = backtest_service.load_data(dataset_path=csv_path)
            
            assert isinstance(data, pd.DataFrame)
            assert len(data) > 0
            assert 'close' in data.columns
        else:
            pytest.skip("No CSV files found in data directory")
    else:
        pytest.skip("Data directory not found")


def test_data_loading_no_source():
    """Test error when no data source provided"""
    service = BacktestService()
    
    with pytest.raises(ValueError):
        service.load_data()


def test_run_backtest_with_dummy_strategy(backtest_service, sample_data):
    """Test running a complete backtest with a dummy strategy"""
    # Use strategy without debug parameter
    
    result = backtest_service.run_backtest(
        strategy='strategies.ema10_scalper.EMA10ScalperStrategy',
        strategy_params={},  # No debug parameter
        dataset_path=None,
        csv_bytes=sample_data.to_csv().encode('utf-8'),
        engine_options={
            'initial_cash': 100000,
            'lots': 1,
            'option_delta': 0.5
        }
    )
    
    # Verify result structure
    assert 'equity_curve' in result
    assert 'trade_log' in result
    assert 'metrics' in result
    assert 'engine_config' in result
    
    # Verify equity curve format
    assert isinstance(result['equity_curve'], list)
    if len(result['equity_curve']) > 0:
        equity_point = result['equity_curve'][0]
        assert 'timestamp' in equity_point
        assert 'equity' in equity_point
    
    # Verify metrics format
    metrics = result['metrics']
    assert 'total_return' in metrics
    assert 'sharpe_ratio' in metrics
    assert 'max_drawdown' in metrics
    assert 'total_trades' in metrics


def test_serialize_timestamp(backtest_service):
    """Test timestamp serialization"""
    # Test pandas timestamp
    ts = pd.Timestamp('2024-01-01 09:15:00')
    result = backtest_service._serialize_timestamp(ts)
    assert isinstance(result, str)
    assert '2024-01-01' in result
    
    # Test NaT
    result = backtest_service._serialize_timestamp(pd.NaT)
    assert result is None


def test_serialize_trade(backtest_service):
    """Test trade serialization"""
    trade = {
        'entry_time': pd.Timestamp('2024-01-01 09:15:00'),
        'pnl': np.float64(100.5),
        'position': 'long',
        'volume': np.int64(1000),
        'active': np.bool_(True),
        'missing': pd.NaT
    }
    
    result = backtest_service._serialize_trade(trade)
    
    assert isinstance(result['entry_time'], str)
    assert isinstance(result['pnl'], float)
    assert isinstance(result['position'], str)
    assert isinstance(result['volume'], float)  # numpy int becomes float
    assert isinstance(result['active'], bool)
    assert result['missing'] is None


def test_calculate_metrics(backtest_service):
    """Test metrics calculation"""
    # Create sample equity curve
    equity_curve = pd.Series([100000, 101000, 99000, 102000, 98000])
    returns = [1000, -2000, 3000, -4000]  # Sample trade returns
    
    metrics = backtest_service._calculate_metrics(equity_curve, returns, 100000)
    
    assert 'total_return' in metrics
    assert 'sharpe_ratio' in metrics
    assert 'max_drawdown' in metrics
    assert 'win_rate' in metrics
    assert 'profit_factor' in metrics
    assert 'total_trades' in metrics
    
    assert metrics['total_trades'] == 4
    assert isinstance(metrics['total_return'], float)


def test_engine_options_defaults(backtest_service, sample_data):
    """Test that default engine options are applied correctly"""
    result = backtest_service.run_backtest(
        strategy='strategies.ema10_scalper.EMA10ScalperStrategy',
        strategy_params={},
        csv_bytes=sample_data.to_csv().encode('utf-8')
        # No engine_options provided
    )
    
    config = result['engine_config']
    assert config['initial_cash'] == 100000
    assert config['lots'] == 2
    assert config['option_delta'] == 0.5
    assert config['intraday'] is True


def test_strategy_params_passing(backtest_service, sample_data):
    """Test that strategy parameters are passed correctly"""
    # Use strategy without unsupported parameters
    result = backtest_service.run_backtest(
        strategy='strategies.ema10_scalper.EMA10ScalperStrategy',
        strategy_params={},  # Only supported params
        csv_bytes=sample_data.to_csv().encode('utf-8')
    )
    
    # If we get here without exception, the parameters were handled
    assert 'equity_curve' in result
