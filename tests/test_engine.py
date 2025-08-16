import pandas as pd
import numpy as np
import pytest
from backtester.engine import _vectorized_backtest_core, BacktestEngine
from backtester.strategy_base import StrategyBase


def test_vectorized_backtest_core():
    signals = np.array([0, 1, -1])
    prices = np.array([100.0, 101.0, 102.0])
    equity = _vectorized_backtest_core(
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
        'timestamp': pd.date_range('2024-01-01', periods=3, freq='T'),
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
