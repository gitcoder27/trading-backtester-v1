"""
Multi-strategy comparison logic for Streamlit app.
"""
# This module will contain comparison logic split from app.py

import streamlit as st
from webapp.ui_sections import section_compare

def render_comparison_tab(data, picks, strat_choice, strat_params, STRATEGY_MAP, option_delta, lots, price_per_unit):
    st.caption("Compare multiple strategies with default/current params")
    selected = st.multiselect("Strategies", list(STRATEGY_MAP.keys()), default=[strat_choice])
    if st.button("Run Comparison") and selected:
        section_compare(data, selected, strat_choice, strat_params, STRATEGY_MAP, option_delta, lots, price_per_unit)
