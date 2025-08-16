"""
Session state and preferences management for Streamlit app.
"""
import pandas as pd
from webapp.prefs import load_prefs, get_pref

def _parse_date(val):
    if val is None:
        return None
    if isinstance(val, str):
        try:
            return pd.to_datetime(val).date()
        except Exception:
            return None
    return val

def set_pref(prefs, key, value):
    from webapp.prefs import set_pref as _set_pref
    return _set_pref(prefs, key, value)

def save_prefs(prefs):
    from webapp.prefs import save_prefs as _save_prefs
    return _save_prefs(prefs)

def seed_session_defaults(st, STRATEGY_MAP):
    from webapp.prefs import load_prefs
    _prefs = load_prefs()
    st.session_state['_prefs_obj'] = _prefs
    st.session_state['_set_pref'] = set_pref
    st.session_state['_save_prefs'] = save_prefs
    if st.session_state.get('_prefs_applied', False):
        return
    st.session_state.setdefault('mode', get_pref(_prefs, 'mode', "Choose from data/"))
    st.session_state.setdefault('timeframe', get_pref(_prefs, 'timeframe', "1min"))
    st.session_state.setdefault('data_file', get_pref(_prefs, 'data_file', None))
    st.session_state.setdefault('start_date', _parse_date(get_pref(_prefs, 'start_date', None)))
    st.session_state.setdefault('end_date', _parse_date(get_pref(_prefs, 'end_date', None)))
    st.session_state.setdefault('strategy', get_pref(_prefs, 'strategy', list(STRATEGY_MAP.keys())[0]))
    st.session_state.setdefault('debug', bool(get_pref(_prefs, 'debug', False)))
    st.session_state.setdefault('ema10_ema_period', int(get_pref(_prefs, 'ema10_ema_period', 10)))
    st.session_state.setdefault('ema10_pt', int(get_pref(_prefs, 'ema10_pt', 20)))
    st.session_state.setdefault('ema10_sl', int(get_pref(_prefs, 'ema10_sl', 15)))
    st.session_state.setdefault('ema50_ema_period', int(get_pref(_prefs, 'ema50_ema_period', 50)))
    st.session_state.setdefault('ema50_pt', int(get_pref(_prefs, 'ema50_pt', 20)))
    st.session_state.setdefault('rsi_period', int(get_pref(_prefs, 'rsi_period', 9)))
    st.session_state.setdefault('rsi_overbought', int(get_pref(_prefs, 'rsi_overbought', 80)))
    st.session_state.setdefault('rsi_oversold', int(get_pref(_prefs, 'rsi_oversold', 20)))
    st.session_state.setdefault('option_delta', float(get_pref(_prefs, 'option_delta', 0.5)))
    st.session_state.setdefault('lots', int(get_pref(_prefs, 'lots', 2)))
    st.session_state.setdefault('price_per_unit', float(get_pref(_prefs, 'price_per_unit', 1.0)))
    st.session_state.setdefault('fee_per_trade', float(get_pref(_prefs, 'fee_per_trade', 0.0)))
    st.session_state.setdefault('direction_filter', list(get_pref(_prefs, 'direction_filter', ["long", "short"])))
    st.session_state.setdefault('apply_time_filter', bool(get_pref(_prefs, 'apply_time_filter', False)))
    st.session_state.setdefault('start_hour', int(get_pref(_prefs, 'start_hour', 9)))
    st.session_state.setdefault('end_hour', int(get_pref(_prefs, 'end_hour', 15)))
    st.session_state.setdefault('apply_weekday_filter', bool(get_pref(_prefs, 'apply_weekday_filter', False)))
    st.session_state.setdefault('weekdays', list(get_pref(_prefs, 'weekdays', [0, 1, 2, 3, 4])))
    st.session_state.setdefault('apply_filters_to_charts', bool(get_pref(_prefs, 'apply_filters_to_charts', False)))
    st.session_state['_prefs_applied'] = True
