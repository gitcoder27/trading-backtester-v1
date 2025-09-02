"""
Tab rendering logic for Streamlit app with lazy loading and performance optimization.
"""
import streamlit as st
from webapp.ui_sections import (
    render_metrics,
    section_overview,
    section_chart,
    section_advanced_chart_lazy,
    section_tv_chart_lazy,
    section_trades,
    section_analytics
)
from webapp.performance_optimization import LazyTabManager, PerformanceMonitor

def render_tabs(
    data,
    trade_log,
    shown_trades,
    strategy,
    indicators,
    eq_for_display,
    apply_filters_to_charts,
    strat_choice,
    strat_params,
    STRATEGY_MAP,
    option_delta=1.0,
    lots=1,
    price_per_unit=1.0,
    daily_target=None,
):
    """Renders tabs with lazy loading for improved performance."""
    
    # Start performance monitoring
    timer_key = PerformanceMonitor.start_timer("tab_rendering")
    
    tabs = st.tabs(["Overview", "Chart", "Advanced Chart (Beta)", "TV Chart (Beta)", "Trades", "Analytics", "Sweep", "Compare", "Export"])

    # Always render Overview tab (most commonly used)
    with tabs[0]:
        render_metrics(eq_for_display, shown_trades, daily_target)
        section_overview(eq_for_display)

    # Lazy load other tabs
    with tabs[1]:
        if strategy is None:
            strat_cls = STRATEGY_MAP[strat_choice]
            strategy = strat_cls(params=strat_params)
        section_chart(data, shown_trades if apply_filters_to_charts else trade_log, strategy, indicators)

    with tabs[2]:
        if strategy is None:
            strat_cls = STRATEGY_MAP[strat_choice]
            strategy = strat_cls(params=strat_params)
        section_advanced_chart_lazy(data, shown_trades if apply_filters_to_charts else trade_log, strategy, indicators)

    with tabs[3]:
        if strategy is None:
            strat_cls = STRATEGY_MAP[strat_choice]
            strategy = strat_cls(params=strat_params)
        section_tv_chart_lazy(data, shown_trades if apply_filters_to_charts else trade_log, strategy, indicators)

    with tabs[4]:
        section_trades(shown_trades)

    with tabs[5]:
        section_analytics(eq_for_display, shown_trades)

    # Sweep, Compare, Export tabs with lazy loading
    with tabs[6]:
        if LazyTabManager.should_load_tab("Sweep"):
            from webapp.sweep import run_sweep
            st.subheader("Parameter Sweep")
            st.caption("Run grid search to optimize strategy parameters")
            
            # Simple sweep interface
            col1, col2 = st.columns(2)
            with col1:
                param_name = st.selectbox("Parameter", list(strat_params.keys()) if strat_params else [])
            with col2:
                if param_name:
                    start_val = st.number_input("Start", value=1)
                    end_val = st.number_input("End", value=10)
                    step_val = st.number_input("Step", value=1)
                    
            if st.button("Run Sweep") and param_name:
                sweep_params = {param_name: (start_val, end_val, step_val)}
                run_sweep(data, STRATEGY_MAP[strat_choice], strat_params, 
                         option_delta, lots, price_per_unit, sweep_params, 50)
        else:
            LazyTabManager.render_tab_placeholder("Sweep", "Parameter optimization functionality")

    with tabs[7]:
        if LazyTabManager.should_load_tab("Compare"):
            from webapp.comparison import render_comparison_tab
            render_comparison_tab(data, shown_trades, strat_choice, strat_params, 
                                STRATEGY_MAP, option_delta, lots, price_per_unit)
        else:
            LazyTabManager.render_tab_placeholder("Compare", "Multi-strategy comparison")

    with tabs[8]:
        if LazyTabManager.should_load_tab("Export"):
            from webapp.export import render_export_tab
            render_export_tab(eq_for_display, data, shown_trades, indicators, strategy)
        else:
            LazyTabManager.render_tab_placeholder("Export", "Download reports and data")

    # End performance monitoring
    PerformanceMonitor.end_timer(timer_key, "Total tab rendering")
    
    return tabs
