import os
os.environ["NUMBA_DISABLE_JIT"] = "1"

import numpy as np
import pandas as pd
import pytest
from backtester import optimization_utils as ou


def test_fast_ema_sma():
    prices = np.array([1.0, 2.0, 3.0, 4.0])
    ema = ou.fast_ema(prices, 2)
    sma = ou.fast_sma(prices, 2)
    expected_ema = [1.0, 1.6666667, 2.5555556, 3.5185185]
    expected_sma = [np.nan, 1.5, 2.5, 3.5]
    assert np.allclose(ema, expected_ema, atol=1e-6, equal_nan=True)
    assert np.allclose(sma, expected_sma, atol=1e-6, equal_nan=True)


def test_fast_bollinger_bands():
    prices = np.array([1.0, 2.0, 3.0, 4.0])
    upper, mid, lower = ou.fast_bollinger_bands(prices, period=2, std_dev=2)
    assert mid[-1] == pytest.approx(3.5)
    assert upper[-1] > mid[-1]
    assert lower[-1] < mid[-1]


def test_fast_rsi():
    prices = np.array([1, 2, 3, 2, 3, 4, 3, 4, 5, 4, 5, 6, 5, 6, 7, 6, 7, 8, 7, 8])
    rsi = ou.fast_rsi(prices, period=14)
    assert not np.isnan(rsi[-1])


def test_fast_rsi_all_gains():
    prices = np.arange(1, 40, dtype=float)
    rsi = ou.fast_rsi(prices, period=14)
    assert rsi[-1] == 100


def test_optimize_dataframe_memory():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [1.0, 2.0, 3.0]})
    df_opt, saved = ou.optimize_dataframe_memory(df.copy())
    assert saved >= 0
    assert df_opt['a'].dtype != 'int64'
    assert df_opt['b'].dtype != 'float64'


def test_vectorized_signal_generation():
    df = pd.DataFrame({'close': [1, 2, 3, 4]})
    df = ou.vectorized_signal_generation(df.copy(), strategy_type='ema_cross')
    assert 'signal' in df.columns
    assert set(df['signal'].unique()) <= {0, 1, -1}


def test_performance_optimizer():
    est = ou.PerformanceOptimizer.estimate_processing_time(100000, 1.5)
    assert est > 0
    suggestions = ou.PerformanceOptimizer.suggest_optimizations(200000, 'ema_strategy')
    assert any('vectorized' in s.lower() for s in suggestions)


def test_suggest_optimizations_high_rows_rsi():
    suggestions = ou.PerformanceOptimizer.suggest_optimizations(600000, 'rsi_strategy')
    joined = ' '.join(suggestions).lower()
    assert 'chunking' in joined
    assert 'fast_rsi' in joined
