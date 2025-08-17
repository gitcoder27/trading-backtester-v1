import sys
import types
import pandas as pd
import pytest
from types import SimpleNamespace

class DummyCM:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

class SessionState(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__

def setup_streamlit(monkeypatch):
    st = types.SimpleNamespace(
        session_state=SessionState(),
        subheader=lambda *a, **k: None,
        info=lambda *a, **k: None,
        error=lambda *a, **k: None,
        warning=lambda *a, **k: None,
        rerun=lambda: None,
        spinner=lambda *a, **k: DummyCM(),
        success=lambda *a, **k: None,
        expander=lambda *a, **k: DummyCM(),
        markdown=lambda *a, **k: None,
    )
    monkeypatch.setitem(sys.modules, 'streamlit', st)
    return st

@pytest.fixture
def st_mock(monkeypatch):
    return setup_streamlit(monkeypatch)


def import_ac(monkeypatch):
    import importlib
    if 'webapp.advanced_chart' in sys.modules:
        del sys.modules['webapp.advanced_chart']
    module = importlib.import_module('webapp.advanced_chart')
    return module


def test_manager_init_height_branch(st_mock, monkeypatch):
    st_mock.session_state.adv_chart_height = 400
    ac = import_ac(monkeypatch)
    mgr = ac.AdvancedChartManager()
    assert mgr.options.main_panel_ratio == 60
    st_mock.session_state.adv_chart_height = 700
    mgr2 = ac.AdvancedChartManager()
    assert mgr2.options.main_panel_ratio == 65


def test_validate_input_data(st_mock, monkeypatch):
    ac = import_ac(monkeypatch)
    mgr = ac.AdvancedChartManager()
    assert not mgr._validate_input_data(pd.DataFrame())
    # valid path
    monkeypatch.setattr(ac.DataProcessor, 'validate_data_structure', lambda d: True)
    data = pd.DataFrame({'a':[1]})
    assert mgr._validate_input_data(data)
    # exception path
    def raise_err(d):
        raise ValueError('bad')
    monkeypatch.setattr(ac.DataProcessor, 'validate_data_structure', raise_err)
    assert not mgr._validate_input_data(data)


def test_render_ui_controls(st_mock, monkeypatch):
    ac = import_ac(monkeypatch)
    mgr = ac.AdvancedChartManager()
    mgr.chart_state = SimpleNamespace(start_date='2024-01-01', end_date='2024-01-05')
    # go clicked valid
    cc = SimpleNamespace(
        render_date_range_controls=lambda **k: ('2024-01-01','2024-01-10',True),
        validate_date_range=lambda s,e: True,
        update_chart_state_for_render=lambda s,e: st_mock.session_state.update({'updated':True}),
        render_single_day_controls=lambda *a, **k: None,
        should_render_chart=lambda: True,
        render_performance_controls=lambda: SimpleNamespace(max_points=100),
    )
    monkeypatch.setattr(ac, 'ChartControls', cc)
    monkeypatch.setattr(st_mock, 'rerun', lambda : st_mock.session_state.update({'rerun':True}))
    data = pd.DataFrame({'a': range(10)}, index=pd.date_range('2024-01-01','2024-01-10'))
    mgr._render_ui_controls('2024-01-01','2024-01-10', data)
    assert st_mock.session_state.get('rerun')
    # invalid date range
    cc_invalid = SimpleNamespace(
        render_date_range_controls=lambda **k: ('2024-01-10','2024-01-01',True),
        validate_date_range=lambda s,e: False,
        update_chart_state_for_render=lambda s,e: None,
        render_single_day_controls=lambda *a, **k: None,
        should_render_chart=lambda: False,
        render_performance_controls=lambda: None,
    )
    monkeypatch.setattr(ac, 'ChartControls', cc_invalid)
    mgr._render_ui_controls('2024-01-01','2024-01-10', data)


def test_process_and_filter(st_mock, monkeypatch):
    ac = import_ac(monkeypatch)
    mgr = ac.AdvancedChartManager()
    mgr.chart_state = SimpleNamespace(start_date='2024-01-01', end_date='2024-01-05')
    mgr.performance_settings = SimpleNamespace(max_points=10)
    # patches
    monkeypatch.setattr(ac.DataProcessor, 'filter_data_by_date_range', lambda d,s,e: 'filtered')
    monkeypatch.setattr(ac.DataProcessor, 'align_data_timestamps', lambda d,i: ('aligned', 'ialigned'))
    monkeypatch.setattr(ac.DataProcessor, 'clean_and_validate_ohlc_data', lambda d: 'clean')
    monkeypatch.setattr(ac.DataProcessor, 'sample_data_for_performance', lambda d,m: ('sampled', True))
    monkeypatch.setattr(ac.DataProcessor, 'convert_to_candlestick_data', lambda d: [1])
    monkeypatch.setattr(ac.DataProcessor, 'build_overlay_data', lambda i,c: ('ov','osc'))
    strategy = SimpleNamespace(indicator_config=lambda: ['x'])
    cd = mgr._process_chart_data('data', strategy, 'ind')
    assert cd.candles == [1]
    # indicators None path
    monkeypatch.setattr(ac.DataProcessor, 'align_data_timestamps', lambda d,i: ('aligned', None))
    cd2 = mgr._process_chart_data('data', strategy, None)
    assert cd2.overlays == 'ov'
    # trades filter
    monkeypatch.setattr(ac.DataProcessor, 'filter_trades_by_date_range', lambda t,s,e: pd.DataFrame({'a':[1]}))
    trades = pd.DataFrame({'a':[1]})
    out = mgr._filter_trades_data(trades)
    assert not out.empty
    assert mgr._filter_trades_data(pd.DataFrame()).empty


def test_render_chart_paths(st_mock, monkeypatch):
    ac = import_ac(monkeypatch)
    mgr = ac.AdvancedChartManager()
    mgr.options = SimpleNamespace()
    mgr.performance_settings = None
    mgr.chart_state = SimpleNamespace(run_uid=1, force_update=False, force_rebuild=False)
    chart_data = SimpleNamespace()
    trade_data = SimpleNamespace()
    # Success path
    class DummyRenderer:
        def __init__(self, *a, **k):
            pass
        def is_available(self):
            return True
        def render_chart(self, **k):
            pass
    monkeypatch.setattr(ac, 'EChartsRenderer', DummyRenderer)
    mgr._render_chart(chart_data, trade_data)

    # Exception path
    class FailRenderer(DummyRenderer):
        def render_chart(self, **k):
            raise Exception('boom')
    monkeypatch.setattr(ac, 'EChartsRenderer', FailRenderer)
    fallback = []
    monkeypatch.setattr(mgr, '_render_plotly_fallback', lambda c,t: fallback.append(1))
    mgr._render_chart(chart_data, trade_data)
    assert fallback
    # Not available path
    class NoRenderer(DummyRenderer):
        def is_available(self):
            return False
    monkeypatch.setattr(ac, 'EChartsRenderer', NoRenderer)
    mgr._render_chart(chart_data, trade_data)


def test_render_plotly_fallback(st_mock, monkeypatch):
    ac = import_ac(monkeypatch)
    mgr = ac.AdvancedChartManager()
    mgr.chart_state = SimpleNamespace(start_date='2024-01-01', end_date='2024-01-02')
    st_mock.session_state.update({
        'last_data':'data',
        'last_trades':'tr',
        'last_indicators':'ind',
        'last_strategy':SimpleNamespace(indicator_config=lambda: ['x'])
    })
    monkeypatch.setattr(ac.DataProcessor, 'filter_data_by_date_range', lambda d,s,e: pd.DataFrame({'a':[1]}))
    monkeypatch.setattr(mgr, '_filter_trades_data', lambda t: pd.DataFrame({'a':[1]}))
    monkeypatch.setattr(ac.PlotlyFallbackRenderer, 'render_chart', lambda **k: st_mock.session_state.update({'plotly':True}))
    mgr._render_plotly_fallback(SimpleNamespace(), SimpleNamespace())
    assert st_mock.session_state.get('plotly')
    # data missing
    st_mock.session_state['last_data']=None
    mgr._render_plotly_fallback(SimpleNamespace(), SimpleNamespace())
    # exception path
    st_mock.session_state['last_data']='data'
    def raise_err(*a,**k):
        raise Exception('x')
    monkeypatch.setattr(ac.DataProcessor, 'filter_data_by_date_range', raise_err)
    mgr._render_plotly_fallback(SimpleNamespace(), SimpleNamespace())


def test_render_chart_section_variants(st_mock, monkeypatch):
    ac = import_ac(monkeypatch)
    mgr = ac.AdvancedChartManager()
    data = pd.DataFrame({'timestamp':[1]})
    trades = pd.DataFrame({'a':[1]})
    strategy = SimpleNamespace(indicator_config=lambda: [])
    # early validation failure
    monkeypatch.setattr(mgr, '_validate_input_data', lambda d: False)
    mgr.render_chart_section(data, trades, strategy, None)
    # should_render_chart False
    def manage_chart_state(**k):
        return SimpleNamespace(start_date='2024-01-01', end_date='2024-01-02', run_uid=1, force_update=False, force_rebuild=False)

    cc = SimpleNamespace(
        manage_chart_state=manage_chart_state,
        render_date_range_controls=lambda **k: ('2024-01-01','2024-01-02',False),
        render_single_day_controls=lambda *a, **k: None,
        should_render_chart=lambda : False,
        show_chart_instructions=lambda : st_mock.session_state.update({'inst':True}),
        get_performance_settings=lambda : SimpleNamespace()
    )
    monkeypatch.setattr(ac, 'ChartControls', cc)
    monkeypatch.setattr(mgr, '_validate_input_data', lambda d: True)
    monkeypatch.setattr(ac.DataProcessor, 'get_data_date_range', lambda d: ('2024-01-01','2024-01-10'))
    mgr.render_chart_section(data, trades, strategy, None)
    assert st_mock.session_state.get('inst')
    # no candles
    cc.should_render_chart=lambda : True
    monkeypatch.setattr(mgr, '_render_ui_controls', lambda a,b,c=None: None)
    monkeypatch.setattr(mgr, '_process_chart_data', lambda *a, **k: SimpleNamespace(candles=[]))
    mgr.render_chart_section(data, trades, strategy, None)
    # full path with high height
    monkeypatch.setattr(mgr, '_process_chart_data', lambda *a, **k: SimpleNamespace(candles=[1]))
    monkeypatch.setattr(mgr, '_filter_trades_data', lambda t: pd.DataFrame())
    monkeypatch.setattr(ac.TradeVisualizer, 'process_trades_for_chart', lambda t,o: SimpleNamespace())
    monkeypatch.setattr(mgr, '_render_chart', lambda c,t: st_mock.session_state.update({'rendered':True}))
    mgr.render_chart_section(data, trades, strategy, None)
    assert st_mock.session_state.get('rendered')
    # branch with low height
    st_mock.session_state.adv_chart_height = 400
    mgr.render_chart_section(data, trades, strategy, None)


def test_render_chart_section_exception(st_mock, monkeypatch):
    ac = import_ac(monkeypatch)
    mgr = ac.AdvancedChartManager()
    data = pd.DataFrame({'timestamp':[1]})
    trades = pd.DataFrame()
    strategy = SimpleNamespace(indicator_config=lambda: [])
    monkeypatch.setattr(mgr, '_validate_input_data', lambda d: True)
    monkeypatch.setattr(ac.DataProcessor, 'get_data_date_range', lambda d: ('2024-01-01','2024-01-02'))
    cc = SimpleNamespace(
        manage_chart_state=lambda **k: SimpleNamespace(start_date='2024-01-01', end_date='2024-01-02', run_uid=1, force_update=False, force_rebuild=False),
        render_date_range_controls=lambda **k: ('2024-01-01','2024-01-02',False),
        should_render_chart=lambda : True,
        render_performance_controls=lambda: SimpleNamespace(max_points=100)
    )
    monkeypatch.setattr(ac, 'ChartControls', cc)
    monkeypatch.setattr(mgr, '_render_ui_controls', lambda a,b,c=None: None)
    def boom(*a, **k):
        raise Exception('boom')
    monkeypatch.setattr(mgr, '_process_chart_data', boom)
    mgr.render_chart_section(data, trades, strategy, None)


def test_section_and_util_funcs(st_mock, monkeypatch):
    ac = import_ac(monkeypatch)
    called = {}
    monkeypatch.setattr(ac._chart_manager, 'render_chart_section', lambda *a, **k: called.setdefault('done', True))
    data = pd.DataFrame({'a':[1]})
    trades = pd.DataFrame({'b':[2]})
    ac.section_advanced_chart(data, trades, None, None)
    assert called['done']
    # utilities
    monkeypatch.setattr(ac.TimeUtil, 'to_iso_utc', lambda s: s)
    monkeypatch.setattr(ac.TimeUtil, 'to_epoch_seconds', lambda s: s)
    ser = pd.Series(pd.date_range('2024', periods=1))
    assert ac._to_iso_utc(ser) is ser
    assert ac._to_epoch_seconds(ser) is ser
