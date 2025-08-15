"""
Backtest execution logic for Streamlit app with performance monitoring.
"""
import pandas as pd
import time
import streamlit as st
from backtester.engine import BacktestEngine
from backtester.performance_monitor import PerformanceMonitor, performance_timer
from webapp.analytics import adjust_equity_for_fees, filter_trades

@performance_timer
def run_backtest(data, strategy, option_delta, lots, price_per_unit, fee_per_trade, direction_filter, apply_time_filter, start_hour, end_hour, apply_weekday_filter, weekdays):
    """
    Enhanced backtest runner with performance monitoring.
    """
    # Initialize performance monitoring
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # Display progress
    with st.spinner('Running backtest...'):
        # Initialize engine
        engine = BacktestEngine(
            data,
            strategy,
            option_delta=option_delta,
            lots=lots,
            option_price_per_unit=price_per_unit,
        )
        
        # Run backtest
        results = engine.run()
        
    # Stop monitoring
    metrics = monitor.stop_monitoring(data_rows=len(data))
    
    # Display performance metrics
    st.success(f"Backtest completed in {metrics['total_time']:.2f}s")
    with st.expander("Performance Metrics", expanded=False):
        monitor.display_metrics()
    
    # Extract results
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

    return {
        'equity_curve': equity_curve,
        'trade_log': trade_log,
        'indicators': indicators,
        'shown_trades': shown_trades,
        'eq_for_display': eq_for_display,
        'performance_metrics': metrics,
    }
