"""
Backtest execution logic for Streamlit app.
"""
# This module will contain backtest execution logic split from app.py

import pandas as pd
from backtester.engine import BacktestEngine
from webapp.analytics import adjust_equity_for_fees, filter_trades

def run_backtest(data, strategy, option_delta, lots, price_per_unit, fee_per_trade, direction_filter, apply_time_filter, start_hour, end_hour, apply_weekday_filter, weekdays):
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

    return {
        'equity_curve': equity_curve,
        'trade_log': trade_log,
        'indicators': indicators,
        'shown_trades': shown_trades,
        'eq_for_display': eq_for_display,
    }
