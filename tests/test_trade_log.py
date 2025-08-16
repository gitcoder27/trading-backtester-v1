import pandas as pd
import pytest
from backtester.trade_log import save_trade_log


def test_save_trade_log(tmp_path):
    tl = pd.DataFrame({
        'entry_time': pd.to_datetime(['2024-01-01 09:15', '2024-01-01 09:30']),
        'exit_time': pd.to_datetime(['2024-01-01 09:20', '2024-01-01 09:35']),
        'pnl': [10, -5],
    })
    file_path = tmp_path / 'log.csv'
    save_trade_log(tl, file_path)
    out = pd.read_csv(file_path)
    assert 'final_pnl' in out.columns
    assert 'day_pnl' in out.columns
    assert out['final_pnl'].iloc[-1] == 5
