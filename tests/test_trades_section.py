import sys
import pandas as pd
import importlib


class DummyCol:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class DummyStreamlit:
    def __init__(self):
        self.dataframe_df = None

    def caption(self, *a, **k):
        pass

    def info(self, *a, **k):
        pass

    def dataframe(self, df, *a, **k):
        self.dataframe_df = df

    def columns(self, n):
        return [DummyCol() for _ in range(n)]

    def metric(self, *a, **k):
        pass


def test_trades_section_shows_daily_pnl(monkeypatch):
    st = DummyStreamlit()
    monkeypatch.setitem(sys.modules, 'streamlit', st)
    if 'webapp.ui_sections' in sys.modules:
        del sys.modules['webapp.ui_sections']
    ui_sections = importlib.import_module('webapp.ui_sections')

    trades = pd.DataFrame({
        'entry_time': pd.to_datetime([
            '2024-01-01 09:15',
            '2024-01-01 10:00',
            '2024-01-02 09:20',
        ]),
        'exit_time': pd.to_datetime([
            '2024-01-01 09:25',
            '2024-01-01 10:10',
            '2024-01-02 09:30',
        ]),
        'entry_price': [100, 101, 102],
        'exit_price': [110, 100, 110],
        'direction': ['long', 'short', 'long'],
        'pnl': [10, -5, 7],
    })

    ui_sections._render_trades_content(trades)

    df = st.dataframe_df
    assert 'day_pnl' in df.columns
    assert list(df['day_pnl']) == [10, 5, 7]

