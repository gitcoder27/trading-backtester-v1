"""
Tab rendering logic for Streamlit app.
"""
# This module will contain tab rendering logic split from app.py

import streamlit as st
from webapp.ui_sections import render_metrics, section_overview, section_chart, section_advanced_chart, section_trades, section_analytics

def render_tabs(data, trade_log, shown_trades, strategy, indicators, eq_for_display, apply_filters_to_charts, strat_choice, strat_params, STRATEGY_MAP):
    tabs = st.tabs(["Overview", "Chart", "Advanced Chart (Beta)", "Trades", "Analytics", "Sweep", "Compare", "Export"])

    with tabs[0]:
        render_metrics(eq_for_display, shown_trades)
        section_overview(eq_for_display)

    with tabs[1]:
        if strategy is None:
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

    # Sweep, Compare, Export tabs are handled in their respective modules
    return tabs
