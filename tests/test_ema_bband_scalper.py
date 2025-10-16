import pandas as pd
import pytest

from strategies.ema_bband_scalper import EmaBbandScalper


def _build_buy_scenario():
    close = [100, 99, 98, 99, 100, 101.5, 102, 103, 102, 103, 104]
    open_ = [c - 0.5 for c in close]
    high = [c + 0.5 for c in close]
    low = [o - 0.3 for o in open_]
    return pd.DataFrame(
        {
            'timestamp': pd.date_range('2024-01-01', periods=len(close), freq='min'),
            'open': open_,
            'high': high,
            'low': low,
            'close': close,
        }
    )


def _build_sell_scenario():
    close = [104, 103, 102.5, 102, 103, 102, 101, 100, 99, 98]
    open_ = [c + 0.4 for c in close]
    low = [c - 0.5 for c in close]
    high = [o + 0.6 for o in open_]
    return pd.DataFrame(
        {
            'timestamp': pd.date_range('2024-01-02', periods=len(close), freq='min'),
            'open': open_,
            'high': high,
            'low': low,
            'close': close,
        }
    )


@pytest.fixture()
def default_params():
    return {
        'fast_period': 3,
        'slow_period': 5,
        'bb_period': 3,
        'bb_std_dev': 2.0,
        'swing_lookback': 2,
    }


def test_buy_signal_requires_pullback_and_bullish_confirmation(default_params):
    data = _build_buy_scenario()
    strategy = EmaBbandScalper(default_params)

    result = strategy.generate_signals(data)
    entries = result[result['signal'] == 1]

    assert len(entries) == 1
    entry = entries.iloc[0]

    assert entry['timestamp'] == pd.Timestamp('2024-01-01 00:08:00')
    assert entry['stop_loss'] <= entry['low']
    assert entry['take_profit'] == pytest.approx(entry['bb_upper'])


def test_sell_signal_requires_pullback_and_bearish_confirmation(default_params):
    data = _build_sell_scenario()
    strategy = EmaBbandScalper(default_params)

    result = strategy.generate_signals(data)
    entries = result[result['signal'] == -1]

    assert len(entries) == 1
    entry = entries.iloc[0]

    assert entry['timestamp'] == pd.Timestamp('2024-01-02 00:02:00')
    assert entry['stop_loss'] >= entry['high']
    assert entry['take_profit'] == pytest.approx(entry['bb_lower'])
