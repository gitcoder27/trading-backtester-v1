"""
Streamlit Web App for the trading-backtester-v1 project.
Allows selecting data, strategy and parameters, running backtests, viewing plots,
and downloading results/reports—all from the browser.
"""
import os
import tempfile
import pandas as pd
import plotly.express as px
import streamlit as st

from backtester.engine import BacktestEngine
from backtester.metrics import (
    total_return,
    sharpe_ratio,
    max_drawdown,
    win_rate,
    profit_factor,
    largest_winning_trade,
    largest_losing_trade,
    average_holding_time,
    max_consecutive_wins,
    max_consecutive_losses,
)
from backtester.plotting import plot_trades_on_candlestick_plotly, plot_equity_curve
from backtester.html_report import generate_html_report

from webapp.strategies_registry import STRATEGY_MAP
from webapp.data_utils import list_data_files, load_data_from_source, filter_by_date
from webapp.analytics import (
    compute_drawdown,
    rolling_sharpe,
    monthly_returns_heatmap,
    adjust_equity_for_fees,
    filter_trades,
)
from webapp.prefs import load_prefs, save_prefs, get_pref, set_pref
from webapp.ui_sections import render_metrics as ui_render_metrics
from webapp.ui_sections import section_overview, section_chart, section_advanced_chart, section_trades, section_analytics, section_compare, section_export


st.set_page_config(page_title="Strategy Backtester", layout="wide")
st.title("Strategy Backtester")
st.caption("Interactive web app for running and analyzing backtests.")

# Load persisted preferences (used as defaults)
_prefs = load_prefs()


def _parse_date(val):
    if val is None:
        return None
    if isinstance(val, str):
        try:
            return pd.to_datetime(val).date()
        except Exception:
            return None
    return val


def seed_session_defaults():
    if st.session_state.get('_prefs_applied', False):
        return
    # Data & timeframe
    st.session_state.setdefault('mode', get_pref(_prefs, 'mode', "Choose from data/"))
    st.session_state.setdefault('timeframe', get_pref(_prefs, 'timeframe', "1T"))
    st.session_state.setdefault('data_file', get_pref(_prefs, 'data_file', None))
    # Dates
    st.session_state.setdefault('start_date', _parse_date(get_pref(_prefs, 'start_date', None)))
    st.session_state.setdefault('end_date', _parse_date(get_pref(_prefs, 'end_date', None)))
    # Strategy & params
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
    # Execution & filters
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


@st.cache_data(show_spinner=False)
def cached_list_data_files(data_folder: str = "data"):
    return list_data_files(data_folder)


@st.cache_data(show_spinner=True)
def cached_load_data_from_source(file_path: str | None, timeframe: str, uploaded_bytes: bytes | None):
    return load_data_from_source(file_path, timeframe, uploaded_bytes)


def strategy_selector():
    choice = st.selectbox("Strategy", list(STRATEGY_MAP.keys()), index=0)
    return choice, STRATEGY_MAP[choice]


# Seed defaults once per session
seed_session_defaults()

with st.sidebar:
    st.header("Configuration")

    with st.expander("Data Selection", expanded=True):
        mode_options = ["Choose from data/", "Upload CSV"]
        mode_index = mode_options.index(st.session_state.get('mode', "Choose from data/")) if st.session_state.get('mode', "Choose from data/") in mode_options else 0
        mode = st.radio("Data Source", mode_options, index=mode_index, key='mode')

        tf_options = ["1T", "2T", "5T", "10T"]
        tf_index = tf_options.index(st.session_state.get('timeframe', "1T")) if st.session_state.get('timeframe', "1T") in tf_options else 0
        timeframe = st.selectbox("Timeframe", tf_options, index=tf_index, help="Pandas resample alias: 1T=1min, etc.", key='timeframe')

        selected_file_path = None
        uploaded_bytes = None
        if mode == "Choose from data/":
            files = cached_list_data_files()
            if files:
                df_index = files.index(st.session_state.get('data_file', files[0])) if st.session_state.get('data_file') in files else 0
                file_name = st.selectbox("CSV File", files, index=df_index, key='data_file')
                selected_file_path = os.path.join("data", file_name)
            else:
                st.info("No CSV files found in data/.")
        else:
            up = st.file_uploader("Upload CSV", type=["csv"])  # no key to avoid persisting large bytes in session
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
        if strat_choice.startswith("EMA10"):
            ema_period = st.number_input("EMA Period", min_value=5, max_value=200, value=int(st.session_state.get('ema10_ema_period', 10)), step=1, key='ema10_ema_period')
            pt = st.number_input("Profit Target (pts)", min_value=1, max_value=400, value=int(st.session_state.get('ema10_pt', 20)), step=1, key='ema10_pt')
            sl = st.number_input("Stop Loss (pts)", min_value=1, max_value=400, value=int(st.session_state.get('ema10_sl', 15)), step=1, key='ema10_sl')
            strat_params.update({"ema_period": int(ema_period), "profit_target": int(pt), "stop_loss": int(sl)})
        elif strat_choice.startswith("EMA44"):
            st.caption("EMA44 strategy with fixed params (period=44).")
        elif strat_choice.startswith("EMA50"):
            ema_period = st.number_input("EMA Period", min_value=10, max_value=200, value=int(st.session_state.get('ema50_ema_period', 50)), step=1, key='ema50_ema_period')
            pt = st.number_input("Profit Target (pts)", min_value=1, max_value=400, value=int(st.session_state.get('ema50_pt', 20)), step=1, key='ema50_pt')
            strat_params.update({"ema_period": int(ema_period), "profit_target_points": int(pt)})
        elif strat_choice.startswith("RSI"):
            rsi_period = st.number_input("RSI Period", min_value=2, max_value=50, value=int(st.session_state.get('rsi_period', 9)), step=1, key='rsi_period')
            overbought = st.number_input("Overbought", min_value=50, max_value=100, value=int(st.session_state.get('rsi_overbought', 80)), step=1, key='rsi_overbought')
            oversold = st.number_input("Oversold", min_value=0, max_value=50, value=int(st.session_state.get('rsi_oversold', 20)), step=1, key='rsi_oversold')
            strat_params.update({"rsi_period": int(rsi_period), "overbought": int(overbought), "oversold": int(oversold)})
        elif strat_choice.startswith("FirstCandle"):
            st.caption("First Candle Breakout uses its internal defaults.")
        elif strat_choice.startswith("BBands"):
            st.caption("Bollinger Bands scalper uses its internal defaults.")

    with st.expander("Execution & Options", expanded=False):
        option_delta = st.slider("Option Delta", min_value=0.1, max_value=1.0, value=float(st.session_state.get('option_delta', 0.5)), step=0.05, key='option_delta')
        lots = st.number_input("Lots (1 lot=75)", min_value=1, max_value=100, value=int(st.session_state.get('lots', 2)), step=1, key='lots')
        price_per_unit = st.number_input("Price per unit", min_value=0.1, max_value=1000.0, value=float(st.session_state.get('price_per_unit', 1.0)), step=0.1, key='price_per_unit')
        fee_per_trade = st.number_input("Fee per trade (absolute)", min_value=0.0, max_value=10000.0, value=float(st.session_state.get('fee_per_trade', 0.0)), step=1.0, help="Deducted from PnL per closed trade, for analytics/plots only", key='fee_per_trade')
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

# Note: We do NOT save prefs here. Saving only happens when "Run Backtest" is clicked.


if run_btn:
    # Persist preferences only when running a backtest
    # Collect current session state into prefs then save
    for k in [
        'mode', 'timeframe', 'data_file', 'start_date', 'end_date', 'strategy', 'debug',
        'ema10_ema_period', 'ema10_pt', 'ema10_sl', 'ema50_ema_period', 'ema50_pt',
        'rsi_period', 'rsi_overbought', 'rsi_oversold', 'option_delta', 'lots',
        'price_per_unit', 'fee_per_trade', 'direction_filter', 'apply_time_filter',
        'start_hour', 'end_hour', 'apply_weekday_filter', 'weekdays', 'apply_filters_to_charts'
    ]:
        if k in st.session_state:
            set_pref(_prefs, k, st.session_state[k])
    save_prefs(_prefs)

    # Resolve inputs for run
    mode = st.session_state.get('mode', "Choose from data/")
    timeframe = st.session_state.get('timeframe', "1T")
    start_date = st.session_state.get('start_date', None)
    end_date = st.session_state.get('end_date', None)
    strat_choice = st.session_state.get('strategy', list(STRATEGY_MAP.keys())[0])
    strat_cls = STRATEGY_MAP[strat_choice]
    option_delta = float(st.session_state.get('option_delta', 0.5))
    lots = int(st.session_state.get('lots', 2))
    price_per_unit = float(st.session_state.get('price_per_unit', 1.0))
    fee_per_trade = float(st.session_state.get('fee_per_trade', 0.0))
    direction_filter = list(st.session_state.get('direction_filter', ["long", "short"]))
    apply_time_filter = bool(st.session_state.get('apply_time_filter', False))
    start_hour = int(st.session_state.get('start_hour', 9))
    end_hour = int(st.session_state.get('end_hour', 15))
    apply_weekday_filter = bool(st.session_state.get('apply_weekday_filter', False))
    weekdays = list(st.session_state.get('weekdays', [0, 1, 2, 3, 4]))
    apply_filters_to_charts = bool(st.session_state.get('apply_filters_to_charts', False))

    # Strategy-specific params reconstruction
    debug = bool(st.session_state.get('debug', False))
    strat_params = {"debug": debug}
    if strat_choice.startswith("EMA10"):
        strat_params.update({
            "ema_period": int(st.session_state.get('ema10_ema_period', 10)),
            "profit_target": int(st.session_state.get('ema10_pt', 20)),
            "stop_loss": int(st.session_state.get('ema10_sl', 15)),
        })
    elif strat_choice.startswith("EMA50"):
        strat_params.update({
            "ema_period": int(st.session_state.get('ema50_ema_period', 50)),
            "profit_target_points": int(st.session_state.get('ema50_pt', 20)),
        })
    elif strat_choice.startswith("RSI"):
        strat_params.update({
            "rsi_period": int(st.session_state.get('rsi_period', 9)),
            "overbought": int(st.session_state.get('rsi_overbought', 80)),
            "oversold": int(st.session_state.get('rsi_oversold', 20)),
        })

    if selected_file_path is None and uploaded_bytes is None:
        st.error("Please choose a CSV from data/ or upload one.")
    else:
        data = cached_load_data_from_source(selected_file_path, timeframe, uploaded_bytes)
        if data is None or data.empty:
            st.error("Failed to load data or data is empty.")
        else:
            data = filter_by_date(data, start_date, end_date)
            # Instantiate strategy
            strategy = strat_cls(params=strat_params)

            engine = BacktestEngine(
                data,
                strategy,
                option_delta=option_delta,
                lots=lots,
                option_price_per_unit=price_per_unit,
            )
            results = engine.run()

            equity_curve = results['equity_curve']
            trade_log = results['trade_log']
            indicators = results['indicators'] if 'indicators' in results else None

            # Apply analytics adjustments/filters
            shown_trades = trade_log.copy()
            if direction_filter or apply_time_filter or apply_weekday_filter:
                shown_trades = filter_trades(
                    trade_log,
                    directions=[d.lower() for d in direction_filter],
                    hours=(start_hour, end_hour) if apply_time_filter else None,
                    weekdays=weekdays if apply_weekday_filter else None,
                )
            eq_for_display = equity_curve
            if fee_per_trade > 0:
                eq_for_display = adjust_equity_for_fees(equity_curve, trade_log, fee_per_trade)

            # Persist this run's results for use across reruns (e.g., chart controls)
            st.session_state['last_results'] = {
                'equity_curve': equity_curve,
                'trade_log': trade_log,
                'indicators': indicators,
                'data': data,
                'start_date': start_date,
                'end_date': end_date,
            }
            # Bump a run UID so Advanced Chart can use it in its component key
            import time as _time
            st.session_state['adv_chart_run_uid'] = int(_time.time() * 1000)
            st.session_state['last_strategy'] = strategy
            st.session_state['last_strategy_name'] = strat_choice
            st.session_state['last_strat_params'] = strat_params
            st.session_state['last_options'] = {
                'option_delta': option_delta,
                'lots': lots,
                'price_per_unit': price_per_unit,
            }

            # Tabs: Overview | Chart | Advanced Chart (Beta) | Trades | Analytics | Sweep | Compare | Export
            tabs = st.tabs(["Overview", "Chart", "Advanced Chart (Beta)", "Trades", "Analytics", "Sweep", "Compare", "Export"])

            # Overview
            with tabs[0]:
                st.subheader("Performance Metrics")
                ui_render_metrics(eq_for_display, shown_trades)
                section_overview(eq_for_display)

            # Chart
            with tabs[1]:
                section_chart(data, shown_trades if apply_filters_to_charts else trade_log, strategy, indicators)

            # Advanced Chart (Beta)
            with tabs[2]:
                section_advanced_chart(data, shown_trades if apply_filters_to_charts else trade_log, strategy, indicators)

            # Trades
            with tabs[3]:
                section_trades(shown_trades)

            # Analytics
            with tabs[4]:
                section_analytics(eq_for_display, shown_trades)

            # Sweep
            with tabs[5]:
                st.caption("Parameter sweep: run small grid search over selected strategy parameters.")
                do_sweep = st.checkbox("Enable sweep for this strategy", value=False)
                max_runs = st.number_input("Max combinations", min_value=10, max_value=2000, value=200, step=10)
                sweep_params = {}
                if do_sweep:
                    if strat_choice.startswith("EMA10") or strat_choice.startswith("EMA50"):
                        p_from = st.number_input("EMA Period from", 5, 200, value=10)
                        p_to = st.number_input("EMA Period to", 5, 200, value=30)
                        p_step = st.number_input("EMA Period step", 1, 50, value=5)
                        pt_from = st.number_input("Target from", 1, 200, value=10)
                        pt_to = st.number_input("Target to", 1, 400, value=40)
                        pt_step = st.number_input("Target step", 1, 100, value=10)
                        if strat_choice.startswith("EMA10"):
                            sl_from = st.number_input("Stop from", 1, 200, value=10)
                            sl_to = st.number_input("Stop to", 1, 400, value=30)
                            sl_step = st.number_input("Stop step", 1, 100, value=10)
                        else:
                            sl_from = sl_to = sl_step = None
                        sweep_params = {
                            'ema_period': (p_from, p_to, p_step),
                            'profit_target': (pt_from, pt_to, pt_step) if strat_choice.startswith("EMA10") else None,
                            'profit_target_points': (pt_from, pt_to, pt_step) if strat_choice.startswith("EMA50") else None,
                            'stop_loss': (sl_from, sl_to, sl_step) if strat_choice.startswith("EMA10") else None,
                        }
                    elif strat_choice.startswith("RSI"):
                        r_from = st.number_input("RSI Period from", 2, 50, value=6)
                        r_to = st.number_input("RSI Period to", 2, 50, value=14)
                        r_step = st.number_input("RSI Period step", 1, 10, value=2)
                        sweep_params = {'rsi_period': (r_from, r_to, r_step)}
                    run_sweep = st.button("Run Sweep")
                    if run_sweep and sweep_params:
                        # Build grid
                        grids = []
                        for k, rng in sweep_params.items():
                            if rng is None:
                                continue
                            a,b,c = rng
                            grids.append((k, list(range(int(a), int(b)+1, int(c)))))
                        combos = [{}]
                        for k, vals in grids:
                            combos = [dict(x, **{k:v}) for x in combos for v in vals]
                        if len(combos) > max_runs:
                            combos = combos[:int(max_runs)]
                        rows = []
                        prog = st.progress(0.0)
                        for i,params_ in enumerate(combos):
                            p = dict(strat_params)
                            p.update(params_)
                            s = strat_cls(params=p)
                            engine2 = BacktestEngine(data, s, option_delta=option_delta, lots=lots, option_price_per_unit=price_per_unit)
                            r2 = engine2.run()
                            eq2 = r2['equity_curve']
                            t2 = r2['trade_log']
                            rows.append({
                                **params_,
                                'Total Return %': total_return(eq2)*100,
                                'Sharpe': sharpe_ratio(eq2),
                                'MaxDD %': max_drawdown(eq2)*100,
                                'WinRate %': win_rate(t2)*100,
                                'PF': profit_factor(t2),
                                'Trades': len(t2),
                            })
                            prog.progress((i+1)/len(combos))
                        resdf = pd.DataFrame(rows)
                        st.dataframe(resdf.sort_values(['Total Return %','Sharpe'], ascending=[False, False]), use_container_width=True)
                        if len(grids) == 2:
                            # 2D heatmap on first metric
                            (k1, v1), (k2, v2) = grids[0], grids[1]
                            piv = resdf.pivot(index=k1, columns=k2, values='Total Return %')
                            fig_heat = px.imshow(piv, text_auto=True, color_continuous_scale='RdYlGn', origin='lower', title='Sweep Heatmap (Total Return %)')
                            st.plotly_chart(fig_heat, use_container_width=True)
else:
    # If not running now, try to render last results (keeps charts when changing UI controls)
    lr = st.session_state.get('last_results')
    if not lr:
        st.info("Run a backtest to see charts and analytics.")
    else:
        equity_curve = lr['equity_curve']
        trade_log = lr['trade_log']
        indicators = lr.get('indicators')
        data = lr.get('data')
        strategy = st.session_state.get('last_strategy')
        strat_choice = st.session_state.get('last_strategy_name', list(STRATEGY_MAP.keys())[0])
        strat_params = st.session_state.get('last_strat_params', {"debug": False})
        opts = st.session_state.get('last_options', {})
        option_delta = float(opts.get('option_delta', st.session_state.get('option_delta', 0.5)))
        lots = int(opts.get('lots', st.session_state.get('lots', 2)))
        price_per_unit = float(opts.get('price_per_unit', st.session_state.get('price_per_unit', 1.0)))

        # Apply analytics adjustments/filters for current sidebar settings
        shown_trades = trade_log.copy()
        direction_filter = list(st.session_state.get('direction_filter', ["long", "short"]))
        apply_time_filter = bool(st.session_state.get('apply_time_filter', False))
        start_hour = int(st.session_state.get('start_hour', 9))
        end_hour = int(st.session_state.get('end_hour', 15))
        apply_weekday_filter = bool(st.session_state.get('apply_weekday_filter', False))
        weekdays = list(st.session_state.get('weekdays', [0, 1, 2, 3, 4]))
        apply_filters_to_charts = bool(st.session_state.get('apply_filters_to_charts', False))

        if direction_filter or apply_time_filter or apply_weekday_filter:
            shown_trades = filter_trades(
                trade_log,
                directions=[d.lower() for d in direction_filter],
                hours=(start_hour, end_hour) if apply_time_filter else None,
                weekdays=weekdays if apply_weekday_filter else None,
            )
        eq_for_display = equity_curve
        fee_per_trade = float(st.session_state.get('fee_per_trade', 0.0))
        if fee_per_trade > 0:
            eq_for_display = adjust_equity_for_fees(equity_curve, trade_log, fee_per_trade)

        tabs = st.tabs(["Overview", "Chart", "Advanced Chart (Beta)", "Trades", "Analytics", "Sweep", "Compare", "Export"])

        with tabs[0]:
            st.subheader("Performance Metrics")
            ui_render_metrics(eq_for_display, shown_trades)
            section_overview(eq_for_display)

        with tabs[1]:
            if strategy is None:
                # Recreate strategy for indicator_config if needed
                strat_cls = STRATEGY_MAP[strat_choice]
                strategy = strat_cls(params=strat_params)
            section_chart(data, shown_trades if apply_filters_to_charts else trade_log, strategy, indicators)

        with tabs[2]:
            if strategy is None:
                strat_cls = STRATEGY_MAP[strat_choice]
                strategy = strat_cls(params=strat_params)
            section_advanced_chart(data, shown_trades if apply_filters_to_charts else trade_log, strategy, indicators)

        with tabs[3]:
            section_trades(shown_trades)

        with tabs[4]:
            section_analytics(eq_for_display, shown_trades)

        with tabs[5]:
            st.caption("Parameter sweep: run small grid search over selected strategy parameters.")
            do_sweep = st.checkbox("Enable sweep for this strategy", value=False)
            max_runs = st.number_input("Max combinations", min_value=10, max_value=2000, value=200, step=10)
            sweep_params = {}
            if do_sweep:
                if strat_choice.startswith("EMA10") or strat_choice.startswith("EMA50"):
                    p_from = st.number_input("EMA Period from", 5, 200, value=10)
                    p_to = st.number_input("EMA Period to", 5, 200, value=30)
                    p_step = st.number_input("EMA Period step", 1, 50, value=5)
                    pt_from = st.number_input("Target from", 1, 200, value=10)
                    pt_to = st.number_input("Target to", 1, 400, value=40)
                    pt_step = st.number_input("Target step", 1, 100, value=10)
                    if strat_choice.startswith("EMA10"):
                        sl_from = st.number_input("Stop from", 1, 200, value=10)
                        sl_to = st.number_input("Stop to", 1, 400, value=30)
                        sl_step = st.number_input("Stop step", 1, 100, value=10)
                    else:
                        sl_from = sl_to = sl_step = None
                    sweep_params = {
                        'ema_period': (p_from, p_to, p_step),
                        'profit_target': (pt_from, pt_to, pt_step) if strat_choice.startswith("EMA10") else None,
                        'profit_target_points': (pt_from, pt_to, pt_step) if strat_choice.startswith("EMA50") else None,
                        'stop_loss': (sl_from, sl_to, sl_step) if strat_choice.startswith("EMA10") else None,
                    }
                elif strat_choice.startswith("RSI"):
                    r_from = st.number_input("RSI Period from", 2, 50, value=6)
                    r_to = st.number_input("RSI Period to", 2, 50, value=14)
                    r_step = st.number_input("RSI Period step", 1, 10, value=2)
                    sweep_params = {'rsi_period': (r_from, r_to, r_step)}
                run_sweep = st.button("Run Sweep")
                if run_sweep and sweep_params:
                    grids = []
                    for k, rng in sweep_params.items():
                        if rng is None:
                            continue
                        a,b,c = rng
                        grids.append((k, list(range(int(a), int(b)+1, int(c)))))
                    combos = [{}]
                    for k, vals in grids:
                        combos = [dict(x, **{k:v}) for x in combos for v in vals]
                    if len(combos) > max_runs:
                        combos = combos[:int(max_runs)]
                    rows = []
                    prog = st.progress(0.0)
                    strat_cls = STRATEGY_MAP[strat_choice]
                    for i,params_ in enumerate(combos):
                        p = dict(strat_params)
                        p.update(params_)
                        s = strat_cls(params=p)
                        engine2 = BacktestEngine(data, s, option_delta=option_delta, lots=lots, option_price_per_unit=price_per_unit)
                        r2 = engine2.run()
                        eq2 = r2['equity_curve']
                        t2 = r2['trade_log']
                        rows.append({
                            **params_,
                            'Total Return %': total_return(eq2)*100,
                            'Sharpe': sharpe_ratio(eq2),
                            'MaxDD %': max_drawdown(eq2)*100,
                            'WinRate %': win_rate(t2)*100,
                            'PF': profit_factor(t2),
                            'Trades': len(t2),
                        })
                        prog.progress((i+1)/len(combos))
                    resdf = pd.DataFrame(rows)
                    st.dataframe(resdf.sort_values(['Total Return %','Sharpe'], ascending=[False, False]), use_container_width=True)
                    if len(grids) == 2:
                        (k1, v1), (k2, v2) = grids[0], grids[1]
                        piv = resdf.pivot(index=k1, columns=k2, values='Total Return %')
                        fig_heat = px.imshow(piv, text_auto=True, color_continuous_scale='RdYlGn', origin='lower', title='Sweep Heatmap (Total Return %)')
                        st.plotly_chart(fig_heat, use_container_width=True)

        with tabs[6]:
            st.caption("Compare multiple strategies with default/current params")
            picks = st.multiselect("Strategies", list(STRATEGY_MAP.keys()), default=[strat_choice])
            if st.button("Run Comparison") and picks:
                section_compare(data, picks, strat_choice, strat_params, STRATEGY_MAP, option_delta, lots, price_per_unit)

        with tabs[7]:
            st.subheader("Export & Report")
            metrics_dict = {
                'Start Amount': float(eq_for_display['equity'].iloc[0]),
                'Final Amount': float(eq_for_display['equity'].iloc[-1]),
                'Total Return (%)': total_return(eq_for_display)*100,
                'Sharpe Ratio': sharpe_ratio(eq_for_display),
                'Max Drawdown (%)': max_drawdown(eq_for_display)*100,
                'Win Rate (%)': win_rate(shown_trades)*100,
                'Total Trades': len(shown_trades),
                'Profit Factor': profit_factor(shown_trades),
                'Largest Winning Trade': largest_winning_trade(shown_trades),
                'Largest Losing Trade': largest_losing_trade(shown_trades),
                'Average Holding Time (min)': average_holding_time(shown_trades),
                'Max Consecutive Wins': max_consecutive_wins(shown_trades),
                'Max Consecutive Losses': max_consecutive_losses(shown_trades),
                'indicator_cfg': strategy.indicator_config() if hasattr(strategy, 'indicator_config') else [],
            }
            section_export(eq_for_display, data, shown_trades, indicators, strategy, metrics_dict)
