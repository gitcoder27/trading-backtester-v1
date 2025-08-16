import os
import pandas as pd
import numpy as np
import pytest

from backtester import (
    data_loader,
    html_report,
    plotting,
    reporting,
    strategy_base,
    trade_log,
    metrics,
    optimization_utils as ou,
    performance_monitor,
)


def test_data_loader_fallback_and_missing(tmp_path, monkeypatch):
    real_read_csv = pd.read_csv
    calls = {'n': 0}

    def fake_read_csv(filepath, *args, **kwargs):
        if calls['n'] == 0:
            calls['n'] += 1
            raise Exception('fail')
        return real_read_csv(filepath, *args, **kwargs)

    monkeypatch.setattr(pd, 'read_csv', fake_read_csv)
    df = pd.DataFrame({
        'timestamp': ['2024-01-01'],
        'open': [1.0],
        'high': [1.0],
        'low': [1.0],
        'close': [1.0],
        'volume': [1]
    })
    csv_path = tmp_path / 'data.csv'
    df.to_csv(csv_path, index=False)
    out = data_loader.load_csv(csv_path)
    assert 'timestamp' in out.columns

    bad_path = tmp_path / 'bad.csv'
    pd.DataFrame({'timestamp': ['2024-01-01']}).to_csv(bad_path, index=False)
    with pytest.raises(ValueError):
        data_loader.load_csv(bad_path)


def test_strategy_base_not_implemented():
    base = strategy_base.StrategyBase()
    with pytest.raises(NotImplementedError):
        base.generate_signals(pd.DataFrame())
    with pytest.raises(NotImplementedError):
        base.should_exit('long', {}, 0)


def test_reporting_imports():
    from backtester.reporting import plot_equity_curve, save_trade_log, comparison_table, generate_html_report
    assert callable(plot_equity_curve)
    assert callable(save_trade_log)
    assert callable(comparison_table)
    assert callable(generate_html_report)


def test_html_report_generation(tmp_path, monkeypatch):
    class DummyFig:
        def to_html(self, *args, **kwargs):
            return '<div>trade</div>'
    # patch plotting function used inside html_report
    monkeypatch.setattr(plotting, 'plot_trades_on_candlestick_plotly', lambda *a, **k: DummyFig())
    import plotly.offline as pyo
    monkeypatch.setattr(pyo, 'plot', lambda *a, **k: '<div>eq</div>')
    eq = pd.DataFrame({'timestamp': [1, 2], 'equity': [100, 110]})
    data = pd.DataFrame({
        'timestamp': [1, 2],
        'open': [1, 1],
        'high': [1, 1],
        'low': [1, 1],
        'close': [1, 1]
    })
    trades = pd.DataFrame({
        'entry_time': [1],
        'entry_price': [1],
        'direction': ['long'],
        'exit_time': [2],
        'exit_price': [2],
        'pnl': [1]
    })
    indicators = pd.DataFrame({'timestamp': [1, 2], 'ema': [1, 1]})
    metrics_dict = {'a': 1}
    out_file = tmp_path / 'report.html'
    html_report.generate_html_report(eq, data, trades, indicators, metrics_dict, str(out_file))
    assert out_file.exists()
    def raise_err(*args, **kwargs):
        raise Exception('boom')
    monkeypatch.setattr(plotting, 'plot_trades_on_candlestick_plotly', raise_err)
    html_report.generate_html_report(eq, data, trades, indicators, metrics_dict, str(out_file))


def test_plotting_functions(monkeypatch):
    ts = pd.date_range('2024', periods=3, freq='T')
    data = pd.DataFrame({
        'timestamp': ts,
        'open': [1, 1, 1],
        'high': [2, 2, 2],
        'low': [0, 0, 0],
        'close': [1, 2, 1]
    })
    trades = pd.DataFrame({
        'entry_time': [ts[0], ts[1]],
        'entry_price': [1, 2],
        'exit_time': [ts[1], ts[2]],
        'exit_price': [2, 1],
        'pnl': [1, -1],
        'direction': ['long', 'short']
    })
    indicators = pd.DataFrame({'timestamp': ts, 'rsi': [30, 50, 80]})
    indicator_cfg = [{'column': 'rsi', 'panel': 2, 'plot': True, 'label': 'RSI'}]
    monkeypatch.setattr(plotting.go.Figure, 'show', lambda self: None)
    fig = plotting.plot_trades_on_candlestick_plotly(data, trades, indicators, indicator_cfg, show=False)
    assert isinstance(fig, plotting.go.Figure)
    eq_curve = pd.DataFrame({'timestamp': ts, 'equity': [100, 110, 105]})
    plotting.plot_equity_curve(eq_curve)
    plotting.plot_equity_curve(eq_curve, interactive=True)
    plotting.plot_trades_on_price(data, trades, indicators, indicator_cfg, interactive=False)
    plotting.plot_trades_on_price(data, trades, indicators, indicator_cfg, interactive=True)


def test_trade_log_empty(tmp_path):
    empty = pd.DataFrame(columns=['entry_time', 'exit_time', 'pnl'])
    file_path = tmp_path / 'log.csv'
    trade_log.save_trade_log(empty, file_path)
    assert file_path.exists()


def test_metrics_edge_cases():
    eq = pd.DataFrame({'timestamp': pd.date_range('2024', periods=2, freq='T'), 'equity': [100, 100]})
    empty_tl = pd.DataFrame({'pnl': [], 'entry_time': [], 'exit_time': []})
    assert np.isnan(metrics.sharpe_ratio(eq))
    assert np.isnan(metrics.win_rate(empty_tl))
    assert np.isnan(metrics.profit_factor(empty_tl))
    assert np.isnan(metrics.largest_winning_trade(empty_tl))
    assert np.isnan(metrics.largest_losing_trade(empty_tl))
    assert np.isnan(metrics.average_holding_time(empty_tl))
    assert metrics.max_consecutive_wins(empty_tl) == 0
    assert metrics.max_consecutive_losses(empty_tl) == 0
    assert metrics.trading_sessions_days(None) == 0
    assert np.isnan(metrics.trading_sessions_years(eq, trading_days_per_year=0))


def test_optimization_utils_extra(monkeypatch):
    df = pd.DataFrame({'close': np.arange(1, 20, dtype=float)})
    monkeypatch.setattr(ou, 'fast_rsi', lambda arr: 0.0)
    df2 = ou.vectorized_signal_generation(df.copy(), strategy_type='rsi_bounce')
    assert 'signal' in df2.columns
    ou.PerformanceOptimizer.configure_pandas()


def test_performance_monitor_extras(monkeypatch):
    pm = performance_monitor.PerformanceMonitor()
    pm.start_monitoring()
    pm.stop_monitoring(data_rows=10)
    class Dummy:
        def metric(self, *a, **k):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass
    monkeypatch.setattr(performance_monitor.st, 'columns', lambda n: [Dummy(), Dummy(), Dummy(), Dummy()])
    pm.display_metrics()

    monkeypatch.setattr(performance_monitor.st, 'session_state', {})
    @performance_monitor.performance_timer
    def add(a, b):
        time = a + b
        return time
    assert add(1, 2) == 3
    assert 'add' in performance_monitor.st.session_state['performance_times']
    performance_monitor.optimize_pandas_performance()
