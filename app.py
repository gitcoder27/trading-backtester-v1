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

from webapp.backtest_runner import run_backtest
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
from webapp.ui_sections import render_metrics as ui_render_metrics
from webapp.ui_sections import section_overview, section_chart, section_advanced_chart, section_trades, section_analytics, section_compare, section_export
from webapp.session import seed_session_defaults, set_pref, save_prefs
from webapp.sidebar import cached_list_data_files, cached_load_data_from_source



st.set_page_config(page_title="Strategy Backtester", layout="wide")
st.title("Strategy Backtester")
st.caption("Interactive web app for running and analyzing backtests.")


# Seed defaults once per session
seed_session_defaults(st, STRATEGY_MAP)
_prefs = st.session_state.get('_prefs_obj')

# Render sidebar and get configuration values
from webapp.sidebar import render_sidebar
sidebar_config = render_sidebar()


if sidebar_config['run_btn']:
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

    if sidebar_config['selected_file_path'] is None and sidebar_config['uploaded_bytes'] is None:
        st.error("Please choose a CSV from data/ or upload one.")
    else:
        data = cached_load_data_from_source(sidebar_config['selected_file_path'], sidebar_config['timeframe'], sidebar_config['uploaded_bytes'])
        if data is None or data.empty:
            st.error("Failed to load data or data is empty.")
        else:
            data = filter_by_date(data, start_date, end_date)

            # Instantiate strategy
            strategy = sidebar_config['strat_cls'](params=sidebar_config['strat_params'])
            backtest_results = run_backtest(
                data,
                strategy,
                sidebar_config['option_delta'],
                sidebar_config['lots'],
                sidebar_config['price_per_unit'],
                sidebar_config['fee_per_trade'],
                sidebar_config['direction_filter'],
                sidebar_config['apply_time_filter'],
                sidebar_config['start_hour'],
                sidebar_config['end_hour'],
                sidebar_config['apply_weekday_filter'],
                sidebar_config['weekdays'],
            )

            equity_curve = backtest_results['equity_curve']
            trade_log = backtest_results['trade_log']
            indicators = backtest_results['indicators']
            shown_trades = backtest_results['shown_trades']
            eq_for_display = backtest_results['eq_for_display']

            # Persist this run's results for use across reruns (e.g., chart controls)
            st.session_state['last_results'] = {
                'equity_curve': equity_curve,
                'trade_log': trade_log,
                'indicators': indicators,
                'data': data,
                'start_date': sidebar_config['start_date'],
                'end_date': sidebar_config['end_date'],
            }
            import time as _time
            st.session_state['adv_chart_run_uid'] = int(_time.time() * 1000)
            st.session_state['last_strategy'] = strategy
            st.session_state['last_strategy_name'] = sidebar_config['strat_choice']
            st.session_state['last_strat_params'] = sidebar_config['strat_params']
            st.session_state['last_options'] = {
                'option_delta': sidebar_config['option_delta'],
                'lots': sidebar_config['lots'],
                'price_per_unit': sidebar_config['price_per_unit'],
            }

            # Immediately render dashboard after backtest run
            from webapp.tabs import render_tabs
            from webapp.comparison import render_comparison_tab
            from webapp.export import render_export_tab

            tabs = render_tabs(
                data,
                trade_log,
                shown_trades,
                strategy,
                indicators,
                eq_for_display,
                sidebar_config.get('apply_filters_to_charts', False),
                sidebar_config['strat_choice'],
                sidebar_config['strat_params'],
                STRATEGY_MAP
            )

            # Sweep tab already modularized

            with tabs[6]:
                render_comparison_tab(
                    data,
                    shown_trades,
                    sidebar_config['strat_choice'],
                    sidebar_config['strat_params'],
                    STRATEGY_MAP,
                    sidebar_config['option_delta'],
                    sidebar_config['lots'],
                    sidebar_config['price_per_unit']
                )

            with tabs[7]:
                render_export_tab(
                    eq_for_display,
                    data,
                    shown_trades,
                    indicators,
                    strategy
                )
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

        from webapp.tabs import render_tabs
        from webapp.comparison import render_comparison_tab
        from webapp.export import render_export_tab

        tabs = render_tabs(
            data,
            trade_log,
            shown_trades,
            strategy,
            indicators,
            eq_for_display,
            apply_filters_to_charts,
            strat_choice,
            strat_params,
            STRATEGY_MAP
        )

        # Sweep tab already modularized

        with tabs[6]:
            render_comparison_tab(
                data,
                shown_trades,
                strat_choice,
                strat_params,
                STRATEGY_MAP,
                option_delta,
                lots,
                price_per_unit
            )

        with tabs[7]:
            render_export_tab(
                eq_for_display,
                data,
                shown_trades,
                indicators,
                strategy
            )
