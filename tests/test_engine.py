import pandas as pd
import pytest
from backtester.engine import BacktestEngine
from strategies.ema10_scalper import EMA10ScalperStrategy

@pytest.fixture
def sample_data():
    """Create a small, sample DataFrame for testing."""
    data = {
        'timestamp': pd.to_datetime(['2024-01-01 09:15:00', '2024-01-01 09:16:00', '2024-01-01 09:17:00', '2024-01-01 09:18:00', '2024-01-01 09:19:00', '2024-01-01 09:20:00']),
        'open': [100, 101, 102, 103, 104, 105],
        'high': [101, 102, 103, 104, 105, 106],
        'low': [99, 100, 101, 102, 103, 104],
        'close': [101, 102, 103, 104, 105, 106],
        'volume': [1000, 1000, 1000, 1000, 1000, 1000]
    }
    return pd.DataFrame(data)

def test_backtest_engine_run(sample_data):
    """Test that the BacktestEngine runs without errors."""
    strategy = EMA10ScalperStrategy()
    engine = BacktestEngine(sample_data, strategy)
    results = engine.run()

    assert results is not None
    assert 'equity_curve' in results
    assert 'trade_log' in results
    assert not results['equity_curve'].empty
    # The trade log can be empty if no trades were generated, which is fine for this test.
    assert isinstance(results['trade_log'], pd.DataFrame)
