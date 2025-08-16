"""
Streamlit Web App for the trading-backtester-v1 project.
Optimized for high performance backtesting with large datasets.
Now includes lazy loading and chart caching for improved UI performance.
"""
import time as _time
import pandas as pd
import streamlit as st

from backtester.html_report import generate_html_report
from backtester.metrics import (
    average_holding_time,
    largest_losing_trade,
    largest_winning_trade,
    max_consecutive_losses,
    max_consecutive_wins,
    max_drawdown,
    profit_factor,
    sharpe_ratio,
    total_return,
    win_rate,
)
from backtester.plotting import plot_equity_curve, plot_trades_on_candlestick_plotly
from backtester.optimization_utils import PerformanceOptimizer
from webapp.analytics import (
    compute_drawdown,
    filter_trades,
    monthly_returns_heatmap,
    rolling_sharpe,
)
from webapp.backtest_runner import run_backtest
from webapp.comparison import render_comparison_tab
from webapp.data_utils import filter_by_date
from webapp.export import render_export_tab
from webapp.session import seed_session_defaults, set_pref, save_prefs
from webapp.sidebar import cached_load_data_from_source, render_sidebar
from webapp.strategies_registry import STRATEGY_MAP
from webapp.tabs import render_tabs
from webapp.performance_optimization import (
    PerformanceMonitor, 
    LazyTabManager, 
    clear_chart_cache,
    show_cache_stats
)

# Configure performance optimizations
PerformanceOptimizer.configure_pandas()


def render_dashboard(
    data,
    trade_log,
    shown_trades,
    strategy,
    indicators,
    eq_for_display,
    config,
):
    """Renders all the main content tabs for the dashboard."""
    tabs = render_tabs(
        data,
        trade_log,
        shown_trades,
        strategy,
        indicators,
        eq_for_display,
        config.get("apply_filters_to_charts", False),
        config["strat_choice"],
        config["strat_params"],
        STRATEGY_MAP,
        config.get("option_delta", 1.0),
        config.get("lots", 1),
        config.get("price_per_unit", 1.0),
    )

    with tabs[6]:
        render_comparison_tab(
            data,
            shown_trades,
            config["strat_choice"],
            config["strat_params"],
            STRATEGY_MAP,
            config["option_delta"],
            config["lots"],
            config["price_per_unit"],
        )

    with tabs[7]:
        render_export_tab(eq_for_display, data, shown_trades, indicators, strategy)


def main():
    """Main function to run the Streamlit app with performance optimizations."""
    st.set_page_config(page_title="Strategy Backtester", layout="wide")
    st.title("Strategy Backtester")
    st.caption("Interactive web app for running and analyzing backtests - Now with performance optimizations! 🚀")
    # Seed defaults once per session
    seed_session_defaults(st, STRATEGY_MAP)
    _prefs = st.session_state.get("_prefs_obj")

    # Render sidebar and get configuration values
    sidebar_config = render_sidebar()

    # Add performance controls at the bottom of the sidebar
    with st.sidebar:
        st.divider()
        st.subheader("🚀 Performance Controls")

        # Cache management
        with st.expander("Cache Management", expanded=False):
            show_cache_stats()
            if st.button("🗑️ Clear All Caches"):
                clear_chart_cache()
                # Clear other caches
                st.cache_data.clear()
                st.success("All caches cleared!")
                st.rerun()

        # Tab loading preferences
        with st.expander("Tab Loading", expanded=False):
            st.write("Tabs load lazily to improve performance.")
            if st.button("🔄 Reset Tab States"):
                keys_to_remove = [key for key in st.session_state.keys() if key.startswith('load_tab_')]
                for key in keys_to_remove:
                    del st.session_state[key]
                st.success("Tab states reset!")
                st.rerun()

    if sidebar_config["run_btn"]:
        # Start overall performance monitoring
        overall_timer = PerformanceMonitor.start_timer("complete_backtest_flow")
        
        # Persist preferences only when running a backtest
        # Collect current session state into prefs then save
        for k in [
            "mode",
            "timeframe",
            "data_file",
            "start_date",
            "end_date",
            "strategy",
            "debug",
            "ema10_ema_period",
            "ema10_pt",
            "ema10_sl",
            "ema50_ema_period",
            "ema50_pt",
            "rsi_period",
            "rsi_overbought",
            "rsi_oversold",
            "option_delta",
            "lots",
            "price_per_unit",
            "fee_per_trade",
            "direction_filter",
            "apply_time_filter",
            "start_hour",
            "end_hour",
            "apply_weekday_filter",
            "weekdays",
            "apply_filters_to_charts",
            "intraday",
        ]:
            if k in st.session_state:
                set_pref(_prefs, k, st.session_state[k])
        save_prefs(_prefs)

        if (
            sidebar_config["selected_file_path"] is None
            and sidebar_config["uploaded_bytes"] is None
        ):
            st.error("Please choose a CSV from data/ or upload one.")
            return

        data = cached_load_data_from_source(
            sidebar_config["selected_file_path"],
            sidebar_config["timeframe"],
            sidebar_config["uploaded_bytes"],
        )
        if data is None or data.empty:
            st.error("Failed to load data or data is empty.")
            return

        data = filter_by_date(
            data, sidebar_config["start_date"], sidebar_config["end_date"]
        )
        
        # Performance estimation and optimization suggestions
        data_rows = len(data)
        strategy_name = sidebar_config["strat_choice"]
        
        estimated_time = PerformanceOptimizer.estimate_processing_time(
            data_rows, 
            strategy_complexity=2.0 if 'complex' in strategy_name.lower() else 1.0
        )
        
        # Show performance info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"📊 Data points: {data_rows:,}")
        with col2:
            st.info(f"⏱️ Estimated time: {estimated_time:.1f}s")
        with col3:
            if estimated_time > 5:
                st.warning("⚠️ Large dataset detected")
        
        # Show optimization suggestions for large datasets
        if data_rows > 50000:
            suggestions = PerformanceOptimizer.suggest_optimizations(data_rows, strategy_name)
            if suggestions:
                with st.expander("💡 Performance Optimization Suggestions", expanded=False):
                    for suggestion in suggestions:
                        st.write(f"• {suggestion}")

        # Instantiate strategy
        strategy = sidebar_config["strat_cls"](params=sidebar_config["strat_params"])
        
        # Run backtest with progress indicator
        with st.spinner('🚀 Running optimized backtest...'):
            backtest_results = run_backtest(
                data,
                strategy,
                sidebar_config["option_delta"],
                sidebar_config["lots"],
                sidebar_config["price_per_unit"],
                sidebar_config["fee_per_trade"],
                sidebar_config["direction_filter"],
                sidebar_config["apply_time_filter"],
                sidebar_config["start_hour"],
                sidebar_config["end_hour"],
                sidebar_config["apply_weekday_filter"],
                sidebar_config["weekdays"],
                sidebar_config["intraday"],
            )

        # Persist this run's results for use across reruns
        st.session_state["last_results"] = {
            "equity_curve": backtest_results["equity_curve"],
            "trade_log": backtest_results["trade_log"],
            "indicators": backtest_results["indicators"],
            "data": data,
            "start_date": sidebar_config["start_date"],
            "end_date": sidebar_config["end_date"],
        }
        st.session_state["adv_chart_run_uid"] = int(_time.time() * 1000)
        st.session_state["last_strategy"] = strategy
        st.session_state["last_strategy_name"] = sidebar_config["strat_choice"]
        st.session_state["last_strat_params"] = sidebar_config["strat_params"]
        st.session_state["last_options"] = {
            "option_delta": sidebar_config["option_delta"],
            "lots": sidebar_config["lots"],
            "price_per_unit": sidebar_config["price_per_unit"],
        }

        # Mark all tabs for loading (fresh backtest)
        LazyTabManager.mark_tab_for_loading("Overview")
        LazyTabManager.mark_tab_for_loading("Chart") 
        LazyTabManager.mark_tab_for_loading("Advanced_Chart")
        LazyTabManager.mark_tab_for_loading("Trades")
        LazyTabManager.mark_tab_for_loading("Analytics")

        # Immediately render dashboard after backtest run
        with st.spinner('📊 Preparing dashboard...'):
            render_dashboard(
                data=data,
                trade_log=backtest_results["trade_log"],
                shown_trades=backtest_results["shown_trades"],
                strategy=strategy,
                indicators=backtest_results["indicators"],
                eq_for_display=backtest_results["eq_for_display"],
                config=sidebar_config,
            )
        
        # End overall performance monitoring
        total_time = PerformanceMonitor.end_timer(overall_timer, "Complete backtest flow")
        st.success(f"🎉 Complete workflow finished in {total_time:.2f}s")

    else:
        # If not running now, try to render last results
        lr = st.session_state.get("last_results")
        if not lr:
            st.info("Run a backtest to see charts and analytics.")
            return

        # Apply analytics adjustments/filters for current sidebar settings
        trade_log = lr["trade_log"]
        shown_trades = trade_log.copy()
        if (
            sidebar_config["direction_filter"]
            or sidebar_config["apply_time_filter"]
            or sidebar_config["apply_weekday_filter"]
        ):
            shown_trades = filter_trades(
                trade_log,
                directions=[d.lower() for d in sidebar_config["direction_filter"]],
                hours=(
                    (sidebar_config["start_hour"], sidebar_config["end_hour"])
                    if sidebar_config["apply_time_filter"]
                    else None
                ),
                weekdays=(
                    sidebar_config["weekdays"]
                    if sidebar_config["apply_weekday_filter"]
                    else None
                ),
            )

        eq_for_display = lr["equity_curve"]

        # Re-render dashboard with cached data and new UI settings
        render_dashboard(
            data=lr["data"],
            trade_log=trade_log,
            shown_trades=shown_trades,
            strategy=st.session_state.get("last_strategy"),
            indicators=lr.get("indicators"),
            eq_for_display=eq_for_display,
            config=sidebar_config,
        )


if __name__ == "__main__":
    main()
