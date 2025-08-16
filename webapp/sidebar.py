"""
Sidebar UI configuration for Streamlit app.
"""
import streamlit as st
import os
import hashlib
import time
from webapp.data_utils import list_data_files, load_data_from_source
from webapp.session import set_pref, save_prefs
from webapp.strategies_registry import STRATEGY_MAP

# Global cache for data with memory management
_data_cache = {}
_cache_max_size = 5

@st.cache_data(show_spinner=False)
def cached_list_data_files(data_folder: str = "data"):
	return list_data_files(data_folder)

def _get_cache_key(file_path, timeframe, uploaded_bytes):
    """Generate a cache key for the given parameters."""
    if uploaded_bytes:
        file_hash = hashlib.md5(uploaded_bytes).hexdigest()
        return f"uploaded_{file_hash}_{timeframe}"
    else:
        return f"file_{file_path}_{timeframe}"

def _clean_cache():
    """Remove old cache entries if cache is too large."""
    global _data_cache
    if len(_data_cache) > _cache_max_size:
        oldest_key = min(_data_cache.keys(), key=lambda k: _data_cache[k]['timestamp'])
        del _data_cache[oldest_key]

@st.cache_data(show_spinner=True, ttl=3600)
def cached_load_data_from_source(file_path: str | None, timeframe: str, uploaded_bytes: bytes | None):
    """Enhanced caching with performance monitoring."""
    cache_key = _get_cache_key(file_path, timeframe, uploaded_bytes)
    
    # Check global cache first
    if cache_key in _data_cache:
        st.sidebar.success(f"Using cached data (loaded in {_data_cache[cache_key]['load_time']:.2f}s)")
        return _data_cache[cache_key]['data']
    
    # Load data if not in cache
    start_time = time.time()
    data = load_data_from_source(file_path, timeframe, uploaded_bytes)
    load_time = time.time() - start_time
    
    # Store in cache
    _data_cache[cache_key] = {
        'data': data,
        'timestamp': time.time(),
        'load_time': load_time
    }
    
    # Clean cache if needed
    _clean_cache()
    
    st.sidebar.info(f"Data loaded in {load_time:.2f}s ({len(data)} rows)")
    return data

def render_sidebar():
    with st.sidebar:
        st.header("Configuration")

        with st.expander("Data Selection", expanded=True):
            mode_options = ["Choose from data/", "Upload CSV"]
            mode_index = mode_options.index(st.session_state.get('mode', "Choose from data/")) if st.session_state.get('mode', "Choose from data/") in mode_options else 0
            mode = st.radio("Data Source", mode_options, index=mode_index, key='mode')

            tf_options = ["1min", "2min", "5min", "10min"]
            tf_index = tf_options.index(st.session_state.get('timeframe', "1min")) if st.session_state.get('timeframe', "1min") in tf_options else 0
            timeframe = st.selectbox("Timeframe", tf_options, index=tf_index, help="Pandas resample alias: 1min, 2min, etc.", key='timeframe')

            refresh_files = st.button("Refresh file list", key="refresh_files")

            selected_file_path = None
            uploaded_bytes = None
            if refresh_files:
                cached_list_data_files.clear()

            if mode == "Choose from data/":
                files = cached_list_data_files()
                if files:
                    df_index = files.index(st.session_state.get('data_file', files[0])) if st.session_state.get('data_file') in files else 0
                    file_name = st.selectbox("CSV File", files, index=df_index, key='data_file')
                    selected_file_path = os.path.join("data", file_name)
                else:
                    st.info("No CSV files found in data/.")
            else:
                up = st.file_uploader("Upload CSV", type=["csv"])
                if up is not None:
                    uploaded_bytes = up.read()

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start date", value=st.session_state.get('start_date', None), key='start_date')
            with col2:
                end_date = st.date_input("End date", value=st.session_state.get('end_date', None), key='end_date')

        with st.expander("Strategy & Params", expanded=False):
            s_keys = list(STRATEGY_MAP.keys())
            s_index = s_keys.index(st.session_state.get('strategy', s_keys[0])) if st.session_state.get('strategy') in s_keys else 0
            strat_choice = st.selectbox("Strategy", s_keys, index=s_index, key='strategy')
            strat_cls = STRATEGY_MAP[strat_choice]

            debug = st.checkbox("Enable debug logs", value=bool(st.session_state.get('debug', False)), key='debug')
            strat_params: dict = {"debug": debug}

            # Dynamically generate UI for strategy parameters
            if hasattr(strat_cls, 'get_params_config'):
                params_config = strat_cls.get_params_config()
                if params_config:
                    for config in params_config:
                        # Currently only supports number_input, can be extended
                        if config["type"] == "number_input":
                            default_val = config["default"]
                            min_val = config.get("min")
                            max_val = config.get("max")
                            step_val = config.get("step")
                            session_val = st.session_state.get(config["name"], default_val)

                            # Determine if any of the values require float handling
                            numeric_vals = [default_val, min_val, max_val, step_val]
                            use_float = any(
                                isinstance(v, float) and not float(v).is_integer()
                                for v in numeric_vals
                                if v is not None
                            )

                            if use_float:
                                value = st.number_input(
                                    label=config["label"],
                                    value=float(session_val),
                                    min_value=float(min_val) if min_val is not None else None,
                                    max_value=float(max_val) if max_val is not None else None,
                                    step=float(step_val) if step_val is not None else None,
                                    key=config["name"],
                                )
                            else:
                                value = st.number_input(
                                    label=config["label"],
                                    value=int(session_val),
                                    min_value=int(min_val) if min_val is not None else None,
                                    max_value=int(max_val) if max_val is not None else None,
                                    step=int(step_val) if step_val is not None else None,
                                    key=config["name"],
                                )
                            strat_params[config["param_key"]] = value
                else:
                    st.caption(f"{strat_choice} uses its internal defaults.")
            else:
                st.caption(f"{strat_choice} uses its internal defaults.")

        with st.expander("Execution & Options", expanded=False):
            option_delta = st.slider("Option Delta", min_value=0.1, max_value=1.0, value=float(st.session_state.get('option_delta', 0.5)), step=0.05, key='option_delta')
            lots = st.number_input("Lots (1 lot=75)", min_value=1, max_value=100, value=int(st.session_state.get('lots', 2)), step=1, key='lots')
            price_per_unit = st.number_input("Price per unit", min_value=0.1, max_value=1000.0, value=float(st.session_state.get('price_per_unit', 1.0)), step=0.1, key='price_per_unit')
            fee_per_trade = st.number_input("Fee per trade (absolute)", min_value=0.0, max_value=10000.0, value=float(st.session_state.get('fee_per_trade', 0.0)), step=1.0, help="Deducted from PnL per closed trade, for analytics/plots only", key='fee_per_trade')
            intraday = st.checkbox("Intraday mode (exit at 15:15)", value=bool(st.session_state.get('intraday', False)), key='intraday')
            direction_filter = st.multiselect("Directions to include", ["long", "short"], default=st.session_state.get('direction_filter', ["long", "short"]), key='direction_filter')
            apply_time_filter = st.checkbox("Filter by trading hours", value=bool(st.session_state.get('apply_time_filter', False)), key='apply_time_filter')
            if apply_time_filter:
                start_hour = st.number_input("Start hour (0-23)", min_value=0, max_value=23, value=int(st.session_state.get('start_hour', 9)), key='start_hour')
                end_hour = st.number_input("End hour (0-23)", min_value=0, max_value=23, value=int(st.session_state.get('end_hour', 15)), key='end_hour')
            else:
                start_hour = st.session_state.get('start_hour', 9)
                end_hour = st.session_state.get('end_hour', 15)
            apply_weekday_filter = st.checkbox("Filter by weekdays", value=bool(st.session_state.get('apply_weekday_filter', False)), key='apply_weekday_filter')
            if apply_weekday_filter:
                weekdays = st.multiselect("Weekdays (0=Mon ... 6=Sun)", options=list(range(7)), default=st.session_state.get('weekdays', [0, 1, 2, 3, 4]), key='weekdays')
            else:
                weekdays = st.session_state.get('weekdays', [0, 1, 2, 3, 4])
            apply_filters_to_charts = st.checkbox("Apply filters to charts", value=bool(st.session_state.get('apply_filters_to_charts', False)), key='apply_filters_to_charts')

        run_btn = st.button("Run Backtest", type="primary", use_container_width=True)
        clear_btn = st.button("Clear Results", type="secondary", use_container_width=True)

        if clear_btn:
            for k in [
                'last_results', 'last_strategy', 'last_strategy_name', 'last_strat_params', 'last_options'
            ]:
                if k in st.session_state:
                    del st.session_state[k]

    return {
        'selected_file_path': selected_file_path,
        'uploaded_bytes': uploaded_bytes,
        'run_btn': run_btn,
        'clear_btn': clear_btn,
        'start_date': start_date,
        'end_date': end_date,
        'strat_choice': strat_choice,
        'strat_cls': strat_cls,
        'strat_params': strat_params,
        'option_delta': option_delta,
        'lots': lots,
        'price_per_unit': price_per_unit,
        'fee_per_trade': fee_per_trade,
        'direction_filter': direction_filter,
        'apply_time_filter': apply_time_filter,
        'start_hour': start_hour,
        'end_hour': end_hour,
        'apply_weekday_filter': apply_weekday_filter,
        'weekdays': weekdays,
        'apply_filters_to_charts': apply_filters_to_charts,
        'timeframe': timeframe,
        'intraday': intraday,
    }
