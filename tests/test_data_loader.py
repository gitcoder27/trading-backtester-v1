import pandas as pd
import numpy as np
from backtester.data_loader import load_csv, optimize_dataframe_memory


def test_load_csv_basic(tmp_path):
    data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=4, freq='T'),
        'open': [1, 2, 3, 4],
        'high': [1, 2, 3, 4],
        'low': [1, 2, 3, 4],
        'close': [1, 2, 3, 4],
        'volume': [10, 20, 30, 40],
    })
    file_path = tmp_path / 'data.csv'
    data.to_csv(file_path, index=False)

    df = load_csv(file_path)
    assert list(df.columns) == ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    assert len(df) == 4


def test_load_csv_resample(tmp_path):
    data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=4, freq='T'),
        'open': [1, 2, 3, 4],
        'high': [1, 2, 3, 4],
        'low': [1, 2, 3, 4],
        'close': [1, 2, 3, 4],
        'volume': [10, 20, 30, 40],
    })
    file_path = tmp_path / 'data.csv'
    data.to_csv(file_path, index=False)

    df = load_csv(file_path, timeframe='2T')
    assert len(df) == 2
    assert df['volume'].tolist() == [30, 70]


def test_optimize_dataframe_memory():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [1.0, 2.0, 3.0]})
    df_optimized = optimize_dataframe_memory(df.copy())
    assert str(df_optimized['a'].dtype).startswith('int') and df_optimized['a'].dtype != 'int64'
    assert str(df_optimized['b'].dtype).startswith('float') and df_optimized['b'].dtype != 'float64'
