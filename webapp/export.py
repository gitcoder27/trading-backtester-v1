"""
Export and report download logic for Streamlit app.
"""
# This module will contain export logic split from app.py

import streamlit as st
from backtester.metrics import (
    total_return, sharpe_ratio, max_drawdown, win_rate, profit_factor,
    largest_winning_trade, largest_losing_trade, average_holding_time,
    max_consecutive_wins, max_consecutive_losses
)
from webapp.ui_sections import section_export

def render_export_tab(eq_for_display, data, shown_trades, indicators, strategy):
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
