import sys
import pandas as pd
from types import SimpleNamespace
import pytest

class DummyCM:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

def setup_streamlit(monkeypatch):
    st = SimpleNamespace(
        session_state={},
        spinner=lambda *a, **k: DummyCM(),
        success=lambda *a, **k: None,
        expander=lambda *a, **k: DummyCM(),
    )
    monkeypatch.setitem(sys.modules, 'streamlit', st)
    return st

@pytest.fixture
def st_mock(monkeypatch):
    return setup_streamlit(monkeypatch)


def import_runner(monkeypatch):
    import importlib, sys
    import backtester.performance_monitor as pm
    monkeypatch.setattr(pm, 'performance_timer', lambda f: f)
    if 'webapp.backtest_runner' in sys.modules:
        del sys.modules['webapp.backtest_runner']
    module = importlib.import_module('webapp.backtest_runner')
    return module


def test_run_backtest_basic(st_mock, monkeypatch):
    br = import_runner(monkeypatch)
    data = pd.DataFrame({'a':[1,2]})
    strategy = object()
    results = {
        'equity_curve': pd.DataFrame({'a':[1]}),
        'trade_log': pd.DataFrame({'a':[1]}),
        'indicators': pd.DataFrame({'a':[1]}),
    }
    monkeypatch.setattr(br, 'BacktestEngine', lambda *a, **k: SimpleNamespace(run=lambda: results))
    mon = SimpleNamespace(start_monitoring=lambda: None, stop_monitoring=lambda data_rows: {'total_time':1.0}, display_metrics=lambda: None)
    monkeypatch.setattr(br, 'PerformanceMonitor', lambda: mon)
    monkeypatch.setattr(br, 'filter_trades', lambda *a, **k: pd.DataFrame({'a':[2]}))
    out = br.run_backtest(data, strategy, 0,1,1,0, [], False,0,0, False, [], 0, False)
    assert 'equity_curve' in out


def test_run_backtest_with_filters(st_mock, monkeypatch):
    br = import_runner(monkeypatch)
    data = pd.DataFrame({'a':[1]})
    strategy = object()
    results = {
        'equity_curve': pd.DataFrame({'a':[1]}),
        'trade_log': pd.DataFrame({'direction':['long'], 'entry_time':[0], 'exit_time':[1]})
    }
    monkeypatch.setattr(br, 'BacktestEngine', lambda *a, **k: SimpleNamespace(run=lambda: results))
    mon = SimpleNamespace(start_monitoring=lambda: None, stop_monitoring=lambda data_rows: {'total_time':2.0}, display_metrics=lambda: None)
    monkeypatch.setattr(br, 'PerformanceMonitor', lambda: mon)
    called = {}
    def fake_filter(trades, directions, hours, weekdays):
        called['args'] = (directions, hours, weekdays)
        return trades
    monkeypatch.setattr(br, 'filter_trades', fake_filter)
    out = br.run_backtest(data, strategy,0,1,1,0,['LONG'], True,1,2, True,[1,2], 0, False)
    assert called['args'][0]==['long'] and called['args'][1]==(1,2) and called['args'][2]==[1,2]
    assert isinstance(out['trade_log'], pd.DataFrame)
