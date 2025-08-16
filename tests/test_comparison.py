import pandas as pd
from backtester.comparison import comparison_table


def test_comparison_table(tmp_path):
    results = [
        {'strategy': 'A', 'total_return': 0.1, 'sharpe': 1.0, 'max_drawdown': 0.05, 'win_rate': 0.6},
        {'strategy': 'B', 'total_return': 0.2, 'sharpe': 1.5, 'max_drawdown': 0.04, 'win_rate': 0.7},
    ]
    file_path = tmp_path / 'cmp.csv'
    df = comparison_table(results, filepath=file_path)
    assert isinstance(df, pd.DataFrame)
    assert file_path.exists()
    out = pd.read_csv(file_path)
    assert len(out) == 2
