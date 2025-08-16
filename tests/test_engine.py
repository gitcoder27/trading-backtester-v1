import pandas as pd
import numpy as np
import pytest
from backtester.engine import _vectorized_backtest_core, BacktestEngine
from backtester.strategy_base import StrategyBase


def test_vectorized_backtest_core():
    signals = np.array([0, 1, -1])
    prices = np.array([100.0, 101.0, 102.0])
    core = getattr(_vectorized_backtest_core, 'py_func', _vectorized_backtest_core)
    equity = core(
        signals,
        prices,
        option_delta=1.0,
        option_qty=1,
        option_price_per_unit=1.0,
        fee_per_trade=0.0,
        slippage=0.0,
        initial_equity=1000.0,
    )
    assert equity[-1] == pytest.approx(1001.0)


class DummyStrategy(StrategyBase):
    _use_fast_vectorized = True

    def generate_signals(self, data):
        df = data.copy()
        df['signal'] = [0, 1, -1]
        return df


def test_backtest_engine_run():
    data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=3, freq='min'),
        'close': [100.0, 101.0, 102.0],
    })
    engine = BacktestEngine(
        data,
        DummyStrategy(),
        initial_cash=1000.0,
        option_delta=1.0,
        lots=1,
        option_price_per_unit=1.0,
        fee_per_trade=0.0,
        slippage=0.0,
    )
    result = engine.run()
    equity_df = result['equity_curve']
    assert equity_df['equity'].iloc[-1] == pytest.approx(1075.0)
    trade_log = result['trade_log']
    assert len(trade_log) == 1
    assert trade_log['pnl'].iloc[0] == pytest.approx(75.0)


def test_vectorized_backtest_core_extended():
    signals = np.array([-1, -1, 1, 1])
    prices = np.array([100.0, 99.0, 101.0, 100.0])
    core = getattr(_vectorized_backtest_core, 'py_func', _vectorized_backtest_core)
    equity = core(
        signals,
        prices,
        option_delta=1.0,
        option_qty=1,
        option_price_per_unit=1.0,
        fee_per_trade=1.0,
        slippage=0.5,
        initial_equity=1000.0,
    )
    assert equity[-1] == pytest.approx(994.0)
    assert len(equity) == len(signals) + 1


def test_generate_trade_log_from_signals():
    data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=4, freq='min'),
        'close': [100.0, 102.0, 101.0, 103.0],
        'signal': [1, -1, 1, 1],
    })
    engine = BacktestEngine(
        data,
        DummyStrategy(),
        option_delta=1.0,
        lots=1,
        option_price_per_unit=1.0,
        fee_per_trade=1.0,
        slippage=0.5,
    )
    trade_log = engine._generate_trade_log_from_signals(data, np.zeros(len(data) + 1))
    assert trade_log['direction'].tolist() == ['long', 'short', 'long']
    assert trade_log['exit_reason'].tolist() == ['Signal Reversal', 'Signal Reversal', 'End of Data']
    assert trade_log['pnl'].tolist() == [pytest.approx(74.0), pytest.approx(-1.0), pytest.approx(74.0)]


def test_generate_trade_log_from_signals_short_entry():
    data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=2, freq='min'),
        'close': [100.0, 99.0],
        'signal': [-1, 0],
    })
    engine = BacktestEngine(
        data,
        DummyStrategy(),
        option_delta=1.0,
        lots=1,
        option_price_per_unit=1.0,
        fee_per_trade=0.0,
        slippage=0.5,
    )
    trade_log = engine._generate_trade_log_from_signals(data, np.zeros(len(data) + 1))
    assert trade_log['direction'].tolist() == ['short']


class TraditionalStrategy(StrategyBase):
    def generate_signals(self, data):
        df = data.copy()
        df['signal'] = [1, -1, 1, 1, 1]
        df['exit_indicator'] = df['close']
        return df

    def should_exit(self, position, row, entry_price):
        if position == 'long' and row['close'] > entry_price + 1:
            return True, 'Take Profit Exit'
        if position == 'short' and row['close'] < entry_price - 1:
            return True, 'Take Profit Exit'
        return False, ''

    def indicator_config(self):
        return [{'column': 'exit_indicator'}]


def test_backtest_engine_traditional_run():
    data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=5, freq='min'),
        'close': [100.0, 102.0, 100.0, 101.0, 101.0],
    })
    engine = BacktestEngine(
        data,
        TraditionalStrategy(),
        initial_cash=1000.0,
        option_delta=1.0,
        lots=1,
        option_price_per_unit=1.0,
        fee_per_trade=1.0,
        slippage=0.5,
    )
    result = engine.run()
    assert 'indicators' in result
    trade_log = result['trade_log']
    assert len(trade_log) == 3
    assert trade_log['exit_reason'].tolist() == ['Take Profit Exit', 'Take Profit Exit', 'End of Data']


class ShortOnlyStrategy(StrategyBase):
    def generate_signals(self, data):
        df = data.copy()
        df['signal'] = [-1, -1]
        df['exit_indicator'] = df['close']
        return df

    def should_exit(self, position, row, entry_price):
        return False, ''

    def indicator_config(self):
        return [{'column': 'exit_indicator'}]


def test_backtest_engine_traditional_run_final_short():
    data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=2, freq='min'),
        'close': [100.0, 99.0],
    })
    engine = BacktestEngine(
        data,
        ShortOnlyStrategy(),
        initial_cash=1000.0,
        option_delta=1.0,
        lots=1,
        option_price_per_unit=1.0,
        fee_per_trade=1.0,
        slippage=0.5,
    )
    result = engine.run()
    trade_log = result['trade_log']
    assert len(trade_log) == 1
    assert trade_log['exit_reason'].iloc[0] == 'End of Data'


class NoSignalStrategy(StrategyBase):
    def generate_signals(self, data):
        df = data.copy()
        df['signal'] = [0]
        df['exit_indicator'] = df['close']
        return df

    def should_exit(self, position, row, entry_price):
        return False, ''

    def indicator_config(self):
        return [{'column': 'exit_indicator'}]


def test_run_traditional_backtest_no_entry():
    data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=1, freq='min'),
        'close': [100.0],
    })
    strategy = NoSignalStrategy()
    engine = BacktestEngine(
        data,
        strategy,
        initial_cash=1000.0,
        option_delta=1.0,
        lots=1,
        option_price_per_unit=1.0,
        fee_per_trade=0.0,
        slippage=0.0,
    )
    df = strategy.generate_signals(data)
    equity_df, trade_log = engine._run_traditional_backtest(df, 75, ['exit_indicator'])
    assert trade_log.empty
    # Cover strategy methods
    assert strategy.should_exit('long', df.iloc[0], 100) == (False, '')
    assert strategy.indicator_config() == [{'column': 'exit_indicator'}]
    assert equity_df['equity'].iloc[0] == pytest.approx(1000.0)


def test_backtest_engine_run_equal_length_equity_curve(monkeypatch):
    class PatchStrategy(DummyStrategy):
        def generate_signals(self, data):
            df = data.copy()
            df['signal'] = [1, -1]
            return df

    def fake_core(signals, prices, option_delta, option_qty, option_price_per_unit, fee_per_trade, slippage, initial_equity):
        return np.full(len(signals), initial_equity)

    monkeypatch.setattr('backtester.engine._vectorized_backtest_core', fake_core)
    data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=2, freq='min'),
        'close': [100.0, 101.0],
    })
    engine = BacktestEngine(
        data,
        PatchStrategy(),
        initial_cash=1000.0,
        option_delta=1.0,
        lots=1,
        option_price_per_unit=1.0,
        fee_per_trade=0.0,
        slippage=0.0,
    )
    result = engine.run()
    assert len(result['equity_curve']) == len(data)


class IntradayStrategy(StrategyBase):
    _use_fast_vectorized = False

    def generate_signals(self, data):
        df = data.copy()
        df['signal'] = [1, 0, 0, 1]
        return df

    def should_exit(self, position, row, entry_price):
        return False, ''


def test_intraday_session_close():
    ts = pd.to_datetime(
        [
            '2024-01-01 15:00',
            '2024-01-01 15:14',
            '2024-01-01 15:15',
            '2024-01-01 15:16',
        ]
    )
    data = pd.DataFrame({'timestamp': ts, 'close': [100.0, 101.0, 102.0, 103.0]})
    engine = BacktestEngine(data, IntradayStrategy(), intraday=True)
    result = engine.run()
    trade_log = result['trade_log']
    assert len(trade_log) == 1
    assert trade_log['exit_reason'].iloc[0] == 'Session Close'
    assert trade_log['exit_time'].iloc[0] == ts[2]


class IntradayShortStrategy(StrategyBase):
    _use_fast_vectorized = False

    def generate_signals(self, data):
        df = data.copy()
        df['signal'] = [-1, 0, 0, 1]
        return df

    def should_exit(self, position, row, entry_price):
        return False, ''


def test_intraday_session_close_short_no_reentry():
    ts = pd.to_datetime(
        [
            '2024-01-01 15:00',
            '2024-01-01 15:14',
            '2024-01-01 15:15',
            '2024-01-01 15:16',
        ]
    )
    data = pd.DataFrame({'timestamp': ts, 'close': [100.0, 101.0, 102.0, 103.0]})
    engine = BacktestEngine(data, IntradayShortStrategy(), intraday=True)
    result = engine.run()
    trade_log = result['trade_log']
    assert len(trade_log) == 1
    assert trade_log['direction'].iloc[0] == 'short'
    assert trade_log['exit_reason'].iloc[0] == 'Session Close'
    assert trade_log['exit_time'].iloc[0] == ts[2]


class IntradayNoReentryStrategy(StrategyBase):
    _use_fast_vectorized = False

    def generate_signals(self, data):
        df = data.copy()
        df['signal'] = [0, 1]
        return df

    def should_exit(self, position, row, entry_price):
        return False, ''


def test_session_closed_prevents_new_entry():
    ts = pd.to_datetime(['2024-01-01 15:16', '2024-01-01 15:14'])
    data = pd.DataFrame({'timestamp': ts, 'close': [100.0, 101.0]})
    engine = BacktestEngine(data, IntradayNoReentryStrategy(), intraday=True)
    result = engine.run()
    trade_log = result['trade_log']
    assert trade_log.empty
