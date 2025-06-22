import pytest
import pandas as pd
from backtester.engine import BacktestEngine
from backtester.data_loader import load_csv
from backtester.strategy_base import StrategyBase # Added this import
from tests.fixtures.mock_strategy import MockStrategy, NoSignalStrategy, BuyAndHoldStrategy # Adjusted import
import os

@pytest.fixture
def sample_data_for_engine():
    """Load sample data for engine tests."""
    # Construct path relative to this test file
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, 'fixtures', 'sample_data.csv')
    return load_csv(csv_path)

def test_engine_initialization(sample_data_for_engine):
    """Test BacktestEngine initialization."""
    strategy = MockStrategy()
    engine = BacktestEngine(data=sample_data_for_engine, strategy=strategy, initial_cash=50000)
    assert engine.initial_cash == 50000
    assert engine.strategy == strategy
    pd.testing.assert_frame_equal(engine.data, sample_data_for_engine)

def test_engine_run_mock_strategy(sample_data_for_engine):
    """Test a basic run of the engine with MockStrategy."""
    strategy = MockStrategy(params={'sl_pct': 0.01}) # 1% SL for this test
    engine = BacktestEngine(data=sample_data_for_engine, strategy=strategy)
    results = engine.run()

    assert 'equity_curve' in results
    assert 'trade_log' in results
    assert 'indicators' in results # MockStrategy provides 'indicator1'

    equity_curve = results['equity_curve']
    trade_log = results['trade_log']
    indicators = results['indicators']

    assert not equity_curve.empty
    assert 'timestamp' in equity_curve.columns and 'equity' in equity_curve.columns
    assert equity_curve['equity'].iloc[0] == engine.initial_cash

    # MockStrategy:
    # 1. Buys at 101 (close of first row)
    # sample_data.csv:
    # 2023-01-01 09:15:00,100,102,99,101,1000 <- Buy at 101
    # 2023-01-01 09:16:00,101,103,100,102,1200
    # 2023-01-01 09:17:00,102,104,101,103,1100 <- Short signal here, but already in long. SL check: 103 vs 101*(1-0.01)=99.99. No SL.
    # 2023-01-01 09:18:00,103,105,102,104,1300
    # 2023-01-01 09:19:00,104,106,103,105,1050
    # 2023-01-01 09:20:00,105,105,100,100,1500 <- SL hit: 100 < 101*(1-0.01)=99.99 is false. 100 < 99.99 is false. Oh, SL is 101 * (1-0.01) = 99.99. Close is 100. So not hit.
    # Let's re-check MockStrategy logic for should_exit: row.close < entry_price * (1 - self.sl_pct)
    # Entry price = 101. sl_pct = 0.01. Threshold = 101 * 0.99 = 99.99.
    # Row with close 100: 100 < 99.99 is FALSE. No exit.
    # The first trade (long at 101) should hit SL at price 99 (close of data.iloc[7])
    # SL threshold = 101 * (1 - 0.01) = 99.99. row.close = 99. 99 < 99.99 is TRUE.

    assert not trade_log.empty
    assert len(trade_log) == 1 # One trade expected, closed by SL
    first_trade = trade_log.iloc[0]
    assert first_trade['direction'] == 'long'
    assert first_trade['entry_price'] == 101 # Close of first bar (data.iloc[0].close)
    assert first_trade['exit_price'] == 99  # SL hit at data.iloc[7].close
    assert first_trade['pnl'] == 99 - 101   # -2
    assert first_trade['exit_reason'] == 'SL Hit (1.0%)' # From MockStrategy with sl_pct=0.01

    # Equity curve check
    assert equity_curve['equity'].iloc[-1] == engine.initial_cash - 2 # PNL is -2

    assert 'indicator1' in indicators.columns
    assert len(indicators) == len(sample_data_for_engine)

def test_engine_run_mock_strategy_with_sl_hit(sample_data_for_engine):
    """Test MockStrategy where stop loss is hit."""
    # Modify data slightly to ensure SL hit for long position
    data_copy = sample_data_for_engine.copy()
    # data_copy.loc[1, 'close'] = 90 # Original data: 102. Entry at 101. SL at 101 * (1-0.05) = 95.95
                                     # If close at index 1 is 90, SL is hit.
    # MockStrategy buys at data.iloc[0].close (101)
    # SL is 1% (param for this test) => 101 * (1-0.01) = 99.99
    # Let's make the close of the second bar (index 1) trigger the SL
    data_copy.loc[data_copy.index[1], 'close'] = 99 # This is data_copy.iloc[1]['close']

    strategy = MockStrategy(params={'sl_pct': 0.01})
    engine = BacktestEngine(data=data_copy, strategy=strategy)
    results = engine.run()
    trade_log = results['trade_log']

    # Expected:
    # 1. Long entry at 101 (close of data.iloc[0])
    # 2. SL hit at 99 (close of data.iloc[1]), PnL = 99 - 101 = -2
    # 3. Short entry at data.iloc[2].close. Original data close is 103.
    #    SL for short is 1% => 103 * (1+0.01) = 104.03
    #    Remaining data closes: 104, 105, 100.
    #    At close 104, not SL. At close 105, SL hit (105 > 104.03). PnL = 103 - 105 = -2
    #    Or, if the short entry is on the original data.iloc[2].close (103),
    #    and then it's held till end of data (close 100). PnL = 103 - 100 = 3.
    # The engine logic for re-entry after SL: "Immediate re-entry if exit was indicator-based and signal flips"
    # Our SL exit reason is "SL Hit (1.0%)". This does not end with "exit". So no immediate re-entry.
    # The next signal is at index 2 (-1 for short). This should trigger a new short trade.

    assert len(trade_log) == 2

    # Trade 1: Long that hits SL
    long_trade = trade_log.iloc[0]
    assert long_trade['direction'] == 'long'
    assert long_trade['entry_price'] == 101
    assert long_trade['exit_price'] == 99 # SL hit here
    assert long_trade['pnl'] == -2
    assert long_trade['exit_reason'] == 'SL Hit (1.0%)'

    # Trade 2: Short entry after SL, held till end
    short_trade = trade_log.iloc[1]
    assert short_trade['direction'] == 'short'
    # Short entry occurs at data.iloc[2].close. In data_copy, iloc[2] is original data's third row.
    # data_copy.iloc[0].close = 101 (entry)
    # data_copy.iloc[1].close = 99 (exit)
    # data_copy.iloc[2].close = 103 (short entry)
    # data_copy.iloc[3].close = 104
    # data_copy.iloc[4].close = 105
    # data_copy.iloc[5].close = 100 (original last close)
    # Short SL is 103 * (1 + 0.01) = 104.03.
    # data_copy.iloc[3].close is 104. Not SL.
    # data_copy.iloc[4].close is 105. SL HIT at 105.
    assert short_trade['entry_price'] == data_copy['close'].iloc[2] # 103
    assert short_trade['exit_price'] == 105 # SL hit at 105
    assert short_trade['pnl'] == 103 - 105 # -2
    assert short_trade['exit_reason'] == 'SL Hit (1.0%)' # MockStrategy's SL reason

    final_equity = engine.initial_cash - 2 - 2 # Long loss -2, Short loss -2
    assert results['equity_curve']['equity'].iloc[-1] == final_equity


def test_engine_run_no_signal_strategy(sample_data_for_engine):
    """Test engine with a strategy that generates no trades."""
    strategy = NoSignalStrategy()
    engine = BacktestEngine(data=sample_data_for_engine, strategy=strategy)
    results = engine.run()

    assert results['trade_log'].empty
    assert results['equity_curve']['equity'].iloc[-1] == engine.initial_cash
    assert all(results['equity_curve']['equity'] == engine.initial_cash)
    # NoSignalStrategy has no indicator_config, so 'indicators' might be missing or empty
    assert 'indicators' not in results or results['indicators'] is None or results['indicators'].empty


def test_engine_run_buy_and_hold_strategy(sample_data_for_engine):
    """Test engine with a buy and hold strategy."""
    strategy = BuyAndHoldStrategy()
    engine = BacktestEngine(data=sample_data_for_engine, strategy=strategy)
    results = engine.run()

    trade_log = results['trade_log']
    assert len(trade_log) == 1

    trade = trade_log.iloc[0]
    assert trade['direction'] == 'long'
    assert trade['entry_price'] == sample_data_for_engine['close'].iloc[0] # 101
    assert trade['exit_price'] == sample_data_for_engine['close'].iloc[-1] # 100
    assert trade['pnl'] == sample_data_for_engine['close'].iloc[-1] - sample_data_for_engine['close'].iloc[0] # 100 - 101 = -1
    assert trade['exit_reason'] == 'End of Data'

    assert results['equity_curve']['equity'].iloc[-1] == engine.initial_cash -1

def test_engine_with_empty_data():
    """Test engine with empty input data."""
    empty_df = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'signal'])
    strategy = MockStrategy()
    engine = BacktestEngine(data=empty_df, strategy=strategy)
    results = engine.run()

    assert results['trade_log'].empty
    assert results['equity_curve'].empty # Equity curve will be empty as no rows in df for timestamp
    # Or it might have one row with initial cash if generate_signals returns empty df with timestamp
    # Current engine.run() : equity_curve_df = pd.DataFrame({'timestamp': df['timestamp'], ...})
    # If df is empty (after generate_signals), then equity_curve_df will be empty.

    # If strategy.generate_signals returns data with no rows, df['timestamp'] will be empty.
    # equity_curve list will also be empty. So equity_curve_df will be empty. Correct.

def test_engine_indicator_passing(sample_data_for_engine):
    """Test that indicators from strategy are correctly passed through."""
    strategy = MockStrategy() # MockStrategy creates 'indicator1'
    engine = BacktestEngine(data=sample_data_for_engine, strategy=strategy)
    results = engine.run()

    assert 'indicators' in results
    indicators_df = results['indicators']
    assert isinstance(indicators_df, pd.DataFrame)
    assert 'timestamp' in indicators_df.columns
    assert 'indicator1' in indicators_df.columns
    assert len(indicators_df) == len(sample_data_for_engine)
    # Check if indicator values are as expected (close * 1.01)
    expected_indicator1 = sample_data_for_engine['close'] * 1.01
    pd.testing.assert_series_equal(indicators_df['indicator1'], expected_indicator1, check_names=False, rtol=1e-5)

class StrategyWithNoIndicatorConfig(StrategyBase):
    def generate_signals(self, data):
        # Adds an indicator column but does not define indicator_config
        data['my_indicator'] = data['close'] + 10
        data['signal'] = 0 # No signals
        return data

    def should_exit(self, position, row, entry_price):
        return False, None

def test_engine_strategy_without_indicator_config(sample_data_for_engine):
    """Test engine with a strategy that produces indicators but has no indicator_config."""
    strategy = StrategyWithNoIndicatorConfig()
    engine = BacktestEngine(data=sample_data_for_engine, strategy=strategy)
    results = engine.run()

    # Engine tries to get indicator_cols from strategy.indicator_config()
    # If it's not present, indicator_cfg will be []. indicator_cols will be [].
    # So, results['indicators'] should not be populated based on columns.
    assert 'indicators' not in results or results['indicators'] is None

class StrategyWithEmptyIndicatorConfig(StrategyBase):
    def generate_signals(self, data):
        data['my_indicator'] = data['close'] + 10
        data['signal'] = 0
        return data

    def should_exit(self, position, row, entry_price):
        return False, None

    def indicator_config(self):
        return [] # Explicitly empty

def test_engine_strategy_with_empty_indicator_config(sample_data_for_engine):
    """Test engine with a strategy that has an empty indicator_config list."""
    strategy = StrategyWithEmptyIndicatorConfig()
    engine = BacktestEngine(data=sample_data_for_engine, strategy=strategy)
    results = engine.run()
    assert 'indicators' not in results or results['indicators'] is None

class StrategyWithIndicatorConfigNone(StrategyBase):
    def generate_signals(self, data):
        data['my_indicator'] = data['close'] + 10
        data['signal'] = 0
        return data

    def should_exit(self, position, row, entry_price):
        return False, None

    def indicator_config(self):
        return None # Explicitly None

def test_engine_strategy_with_indicator_config_none(sample_data_for_engine):
    """Test engine with a strategy that returns None for indicator_config."""
    strategy = StrategyWithIndicatorConfigNone()
    engine = BacktestEngine(data=sample_data_for_engine, strategy=strategy)
    results = engine.run()
    assert 'indicators' not in results or results['indicators'] is None
