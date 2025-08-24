from __future__ import annotations
import os
import tempfile
import pandas as pd
import plotly.express as px
import streamlit as st
from typing import Dict, Any, List, Tuple

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
    trading_sessions_days,
    trading_sessions_years,
    daily_profit_target_stats,
)
from backtester.plotting import plot_trades_on_candlestick_plotly, plot_equity_curve
from backtester.html_report import generate_html_report

from .analytics import compute_drawdown, monthly_returns_heatmap, rolling_sharpe
from .advanced_chart import section_advanced_chart
from .performance_optimization import (
    cached_chart, 
    LazyTabManager, 
    ChartOptimizer, 
    PerformanceMonitor,
    show_cache_stats
)
from .chart_components import (
    ChartData, TradeData, ChartOptions, PerformanceSettings, ChartState,
    TimeUtil, DataProcessor, ChartControls, TradeVisualizer, TVLwRenderer,
)


@cached_chart("equity_curve", ttl=300)
def cached_plot_equity_curve(eq_for_display: pd.DataFrame):
    """Cached version of equity curve plotting."""
    return plot_equity_curve(eq_for_display, interactive=True)

@cached_chart("drawdown", ttl=300)  
def cached_compute_and_plot_drawdown(eq_for_display: pd.DataFrame):
    """Cached version of drawdown computation and plotting."""
    dd = compute_drawdown(eq_for_display)
    return px.area(dd, x='timestamp', y='drawdown', title='Underwater (Drawdown)', template='plotly_dark')

@cached_chart("candlestick", ttl=300)
def cached_plot_trades_candlestick(data: pd.DataFrame, trades: pd.DataFrame, indicators, indicator_cfg, max_points: int = 2000):
    """Cached version of trades on candlestick plotting with optimization."""
    # Optimize data for performance
    optimized_data, optimized_trades, was_sampled = ChartOptimizer.optimize_chart_data(data, trades, max_points)
    
    if was_sampled:
        st.info(f"📊 Displaying {len(optimized_data)} of {len(data)} data points for optimal performance")
    
    return plot_trades_on_candlestick_plotly(
        optimized_data,
        optimized_trades,
        indicators=indicators,
        indicator_cfg=indicator_cfg,
        title="Trades on Candlestick Chart",
        show=False,
    )

@cached_chart("analytics", ttl=300)
def cached_analytics_charts(eq_for_display: pd.DataFrame, shown_trades: pd.DataFrame):
    """Cached version of analytics charts generation."""
    charts = {}
    
    # PnL histogram
    if shown_trades is not None and not shown_trades.empty:
        charts['pnl_hist'] = px.histogram(
            shown_trades, x='pnl', nbins=50, 
            title='Trade PnL Distribution', 
            template='plotly_dark'
        )
    
    # Hourly win rate
    if shown_trades is not None and not shown_trades.empty and 'entry_time' in shown_trades:
        et = pd.to_datetime(shown_trades['entry_time'])
        dfh = shown_trades.copy()
        dfh['hour'] = et.dt.hour
        dfh['is_win'] = (dfh['pnl'] > 0).astype(int)
        agg = dfh.groupby('hour').agg(trades=('pnl', 'count'), winrate=('is_win','mean')).reset_index()
        charts['hourly_winrate'] = px.bar(
            agg, x='hour', y='winrate', 
            title='Win Rate by Hour', 
            template='plotly_dark'
        )
    
    # Monthly returns heatmap
    if eq_for_display is not None and not eq_for_display.empty:
        charts['monthly_heatmap'] = monthly_returns_heatmap(eq_for_display)
        
        # Rolling Sharpe
        rs = rolling_sharpe(eq_for_display, window=50)
        if not rs.empty:
            charts['rolling_sharpe'] = px.line(
                rs, x='timestamp', y='rolling_sharpe', 
                title='Rolling Sharpe (window=50)', 
                template='plotly_dark'
            )
    
    return charts


def render_metrics(equity_curve: pd.DataFrame, trade_log: pd.DataFrame, daily_target=None):
    if equity_curve is None or len(equity_curve) == 0 or 'equity' not in equity_curve.columns:
        st.info("No equity data to compute metrics.")
        return
    start_amount = float(equity_curve['equity'].iloc[0])
    final_amount = float(equity_curve['equity'].iloc[-1])

    kpis = {
        "Start Amount": start_amount,
        "Final Amount": final_amount,
        "Total Return (%)": total_return(equity_curve) * 100,
        "Sharpe Ratio": sharpe_ratio(equity_curve),
        "Max Drawdown (%)": max_drawdown(equity_curve) * 100,
        "Win Rate (%)": win_rate(trade_log) * 100,
        "Total Trades": len(trade_log),
        "Profit Factor": profit_factor(trade_log),
        "Largest Win": largest_winning_trade(trade_log),
        "Largest Loss": largest_losing_trade(trade_log),
        "Avg Holding (min)": average_holding_time(trade_log) if len(trade_log) else 0,
        "Max Consec Wins": max_consecutive_wins(trade_log),
        "Max Consec Losses": max_consecutive_losses(trade_log),
        "Trading Sessions (days)": trading_sessions_days(equity_curve),
        "Trading Sessions (years)": trading_sessions_years(equity_curve),
    }

    if len(trade_log) > 0 and 'direction' in trade_log.columns:
        long_trades = trade_log[trade_log['direction'].str.lower().isin(['buy', 'long'])]
        short_trades = trade_log[trade_log['direction'].str.lower().isin(['sell', 'short'])]
        win_long_trades = long_trades[long_trades['pnl'] > 0]
        win_short_trades = short_trades[short_trades['pnl'] > 0]
        kpis.update({
            "Total Long Trades": len(long_trades),
            "Total Short Trades": len(short_trades),
            "Winning Long Trades": len(win_long_trades),
            "Winning Short Trades": len(win_short_trades),
        })

    if daily_target is not None:
        stats = daily_profit_target_stats(trade_log, daily_target)
        hit_rate = stats['target_hit_rate'] * 100 if stats['target_hit_rate'] == stats['target_hit_rate'] else float('nan')
        kpis.update({
            "Days Traded": stats['days_traded'],
            "Days Target Hit": stats['days_target_hit'],
            "Daily Target Hit Rate (%)": hit_rate,
            "Best Day PnL": stats['max_daily_pnl'],
            "Worst Day PnL": stats['min_daily_pnl'],
            "Avg Day PnL": stats['avg_daily_pnl'],
        })

    cols = st.columns(4)
    items = list(kpis.items())
    for i, (k, v) in enumerate(items):
        with cols[i % 4]:
            st.metric(k, f"{v:.2f}" if isinstance(v, float) else str(v))


def section_overview(eq_for_display: pd.DataFrame):
    """Overview section with cached charts and performance monitoring."""
    return LazyTabManager.conditional_render(
        "Overview", 
        _render_overview_content, 
        eq_for_display,
        description="Shows equity curve and drawdown charts"
    )

def _render_overview_content(eq_for_display: pd.DataFrame):
    """Internal function to render overview content."""
    st.subheader("Performance Metrics")
    if eq_for_display is None or len(eq_for_display) == 0:
        st.info("No equity curve to display.")
        return
    
    c1, c2 = st.columns([2, 1])
    with c1:
        fig_eq = cached_plot_equity_curve(eq_for_display)
        st.plotly_chart(fig_eq, use_container_width=True)
    with c2:
        fig_dd = cached_compute_and_plot_drawdown(eq_for_display)
        st.plotly_chart(fig_dd, use_container_width=True)
    
    # Show performance stats in expander
    with st.expander("🚀 Performance Info", expanded=False):
        show_cache_stats()


def section_chart(data: pd.DataFrame, trades: pd.DataFrame, strategy, indicators):
    """Chart section with lazy loading and optimization."""
    return LazyTabManager.conditional_render(
        "Chart", 
        _render_chart_content, 
        data, trades, strategy, indicators,
        description="Shows candlestick chart with trades overlaid"
    )

def _render_chart_content(data: pd.DataFrame, trades: pd.DataFrame, strategy, indicators):
    """Internal function to render chart content."""
    if data is None or len(data) == 0:
        st.info("No price data to chart.")
        return
    
    # Performance settings
    col1, col2 = st.columns([3, 1])
    with col2:
        max_points = st.selectbox(
            "Chart Resolution", 
            [1000, 2000, 5000, "All"], 
            index=1,
            help="Lower values = faster rendering"
        )
        if max_points == "All":
            max_points = len(data)
    
    with col1:
        st.write("")  # Spacer
    
    # Prepare trade data
    tlog = trades.reset_index(drop=True).copy()
    tlog['trade_id'] = tlog.index
    indicator_cfg = strategy.indicator_config() if hasattr(strategy, 'indicator_config') else []
    
    # Generate cached chart
    fig_trades = cached_plot_trades_candlestick(
        data, tlog, indicators, indicator_cfg, max_points
    )
    st.plotly_chart(fig_trades, use_container_width=True)




def section_trades(trades: pd.DataFrame):
    """Trades section with lazy loading."""
    return LazyTabManager.conditional_render(
        "Trades", 
        _render_trades_content, 
        trades,
        description="Shows detailed trade log and summary metrics"
    )

def _render_trades_content(trades: pd.DataFrame):
    """Internal function to render trades content."""
    st.caption("Filtered trades shown below (if filters enabled in sidebar)")
    if trades is None or trades.empty:
        st.info("No trades to display.")
        return
    # Show both normal_pnl and options pnl columns if present
    display_cols = [
        'trade_date', 'entry_time', 'entry_price', 'direction',
        'exit_time', 'exit_price', 'normal_pnl', 'pnl',
        'exit_reason', 'daily_target_hit'
    ]
    # Only show columns that exist in the DataFrame
    display_cols = [c for c in display_cols if c in trades.columns]
    st.dataframe(trades[display_cols])
    colA, colB, colC = st.columns(3)
    with colA:
        st.metric("Win Rate (%)", f"{win_rate(trades)*100:.2f}")
    with colB:
        st.metric("Profit Factor", f"{profit_factor(trades):.2f}")
    with colC:
        st.metric("Total Trades", str(len(trades)))


def section_analytics(eq_for_display: pd.DataFrame, shown_trades: pd.DataFrame):
    """Analytics section with lazy loading and cached charts."""
    return LazyTabManager.conditional_render(
        "Analytics", 
        _render_analytics_content, 
        eq_for_display, shown_trades,
        description="Shows advanced analytics: PnL distribution, hourly patterns, monthly returns, rolling Sharpe"
    )

def _render_analytics_content(eq_for_display: pd.DataFrame, shown_trades: pd.DataFrame):
    """Internal function to render analytics content."""
    # Get all cached charts at once
    charts = cached_analytics_charts(eq_for_display, shown_trades)
    
    # Render charts if available
    if 'pnl_hist' in charts:
        st.plotly_chart(charts['pnl_hist'], use_container_width=True)
    
    if 'hourly_winrate' in charts:
        st.plotly_chart(charts['hourly_winrate'], use_container_width=True)
    
    if 'monthly_heatmap' in charts and charts['monthly_heatmap'] is not None:
        st.plotly_chart(charts['monthly_heatmap'], use_container_width=True)
    
    if 'rolling_sharpe' in charts:
        st.plotly_chart(charts['rolling_sharpe'], use_container_width=True)


def section_advanced_chart_lazy(data: pd.DataFrame, trades: pd.DataFrame, strategy, indicators):
    """Advanced chart section with lazy loading."""
    return LazyTabManager.conditional_render(
        "Advanced_Chart", 
        section_advanced_chart, 
        data, trades, strategy, indicators,
        description="Shows interactive ECharts/Plotly candlestick chart with advanced features"
    )


def section_tv_chart(data: pd.DataFrame, trades: pd.DataFrame, strategy, indicators):
    """TradingView Lightweight Chart section (mirrors advanced chart flow)."""
    import streamlit as st
    st.subheader("TV Chart (Beta)")

    if data is None or len(data) == 0:
        st.info("No price data to chart. Run a backtest first.")
        return

    # Chart state setup (TV chart uses its own namespaced session keys to avoid conflicts)
    min_date, max_date = DataProcessor.get_data_date_range(data)
    last_results = st.session_state.get('last_results', {})
    backtest_start = last_results.get('start_date') or min_date
    backtest_end = last_results.get('end_date') or max_date

    # Reset TV chart dates if data_id changes
    if st.session_state.get('tv_chart_data_id', -1) != id(data):
        st.session_state['tv_chart_data_id'] = id(data)
        st.session_state['tv_chart_start_date'] = backtest_start
        st.session_state['tv_chart_end_date'] = backtest_end
        st.session_state['tv_chart_single_day'] = backtest_start
        st.session_state['tv_chart_render'] = False

    # Ensure defaults exist
    st.session_state.setdefault('tv_chart_start_date', backtest_start)
    st.session_state.setdefault('tv_chart_end_date', backtest_end)
    st.session_state.setdefault('tv_chart_single_day', backtest_start)
    st.session_state.setdefault('tv_chart_render', False)

    with st.expander("📊 Chart Date Range", expanded=False):
        # Sanitize values within range
        cur_start = max(min_date, min(st.session_state['tv_chart_start_date'], max_date))
        cur_end = max(min_date, min(st.session_state['tv_chart_end_date'], max_date))
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            sdt = st.date_input(
                "Start Date",
                value=cur_start,
                min_value=min_date,
                max_value=max_date,
                key='tv_chart_start_date_picker'
            )
        with col2:
            edt = st.date_input(
                "End Date",
                value=cur_end,
                min_value=min_date,
                max_value=max_date,
                key='tv_chart_end_date_picker'
            )
        with col3:
            go = st.button("Go", use_container_width=True, type="primary", key='tv_chart_go')
        if go:
            if sdt <= edt:
                st.session_state['tv_chart_start_date'] = sdt
                st.session_state['tv_chart_end_date'] = edt
                st.session_state['tv_chart_render'] = True
                st.rerun()
            else:
                st.error("❌ Invalid date range: Start date must be before end date.")

    with st.expander("📅 Single Day Navigation", expanded=True):
        try:
            timestamps = pd.to_datetime(data['timestamp'] if 'timestamp' in data.columns else data.index)
            available_dates = sorted(list(set([ts.date() for ts in timestamps])))
            if available_dates:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    single_day = st.date_input(
                        "Single Day",
                        value=st.session_state.get('tv_chart_single_day', available_dates[0]),
                        min_value=min_date,
                        max_value=max_date,
                        key='tv_chart_single_day_picker'
                    )
                cur_day = st.session_state.get('tv_chart_single_day', available_dates[0])
                prev_day = max([d for d in available_dates if d < cur_day], default=cur_day)
                next_day = min([d for d in available_dates if d > cur_day], default=cur_day)
                with col2:
                    if st.button("Prev Day", key='tv_chart_prev_day', use_container_width=True, disabled=prev_day == cur_day):
                        st.session_state['tv_chart_single_day'] = prev_day
                        st.session_state['tv_chart_start_date'] = prev_day
                        st.session_state['tv_chart_end_date'] = prev_day
                        st.session_state['tv_chart_render'] = True
                        if 'tv_chart_single_day_picker' in st.session_state:
                            del st.session_state['tv_chart_single_day_picker']
                        st.rerun()
                with col3:
                    if st.button("Next Day", key='tv_chart_next_day', use_container_width=True, disabled=next_day == cur_day):
                        st.session_state['tv_chart_single_day'] = next_day
                        st.session_state['tv_chart_start_date'] = next_day
                        st.session_state['tv_chart_end_date'] = next_day
                        st.session_state['tv_chart_render'] = True
                        if 'tv_chart_single_day_picker' in st.session_state:
                            del st.session_state['tv_chart_single_day_picker']
                        st.rerun()
                with col4:
                    if st.button("Go", key='tv_chart_single_day_go', use_container_width=True, type="primary"):
                        st.session_state['tv_chart_single_day'] = single_day
                        st.session_state['tv_chart_start_date'] = single_day
                        st.session_state['tv_chart_end_date'] = single_day
                        st.session_state['tv_chart_render'] = True
                        st.rerun()
            else:
                st.warning("⚠️ No valid dates found in data for single day navigation.")
        except Exception:
            st.info("Single day navigation unavailable.")

    if not st.session_state.get('tv_chart_render', False):
        st.info("Select a date range and click 'Go', or choose a single day and navigate with the controls below.")
        return

    # Prepare data
    start_dt = pd.to_datetime(st.session_state['tv_chart_start_date'])
    end_dt = pd.to_datetime(st.session_state['tv_chart_end_date']).replace(hour=23, minute=59, second=59)

    filtered_data = DataProcessor.filter_data_by_date_range(data, start_dt, end_dt)
    filtered_ind = DataProcessor.filter_data_by_date_range(indicators, start_dt, end_dt) if indicators is not None else None
    aligned_data, aligned_ind = DataProcessor.align_data_timestamps(filtered_data, filtered_ind)
    clean_data = DataProcessor.clean_and_validate_ohlc_data(aligned_data)

    # Performance: sampling consistent with advanced chart
    perf = ChartControls.get_performance_settings()
    sampled_data, _ = DataProcessor.sample_data_for_performance(clean_data, perf.max_points)
    candles = DataProcessor.convert_to_candlestick_data(sampled_data)

    indicator_cfg = strategy.indicator_config() if hasattr(strategy, 'indicator_config') else []
    overlays, oscillators = DataProcessor.build_overlay_data(aligned_ind, indicator_cfg)

    cdata = ChartData(
        candles=candles,
        overlays=overlays,
        oscillators=oscillators,
        original_length=len(clean_data),
        sampled_length=len(sampled_data),
    )

    tlog = DataProcessor.filter_trades_by_date_range(trades, start_dt, end_dt) if trades is not None else None
    tdata = TradeVisualizer.process_trades_for_chart(tlog if tlog is not None else pd.DataFrame(), ChartOptions())

    # Enhanced full-width styling for TV chart section
    st.markdown("""
    <style>
    /* Comprehensive TV chart width optimization */
    .element-container:has(> div > iframe[title="streamlit.components.v1.html"]) {
        width: 100% !important;
        max-width: none !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
    }
    
    /* Ensure block containers don't constrain the TV chart */
    div[data-testid="stVerticalBlock"]:has(iframe[title="streamlit.components.v1.html"]) {
        width: 100% !important;
        max-width: none !important;
        padding: 0 !important;
    }
    
    /* Ensure the main content area uses full width for charts */
    .main .block-container:has(iframe[title="streamlit.components.v1.html"]) {
        max-width: none !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    renderer = TVLwRenderer(ChartOptions(height=f"{st.session_state.get('adv_chart_height', 600)}px"), perf)
    renderer.render_chart(cdata, tdata, overlays_enabled=True)


def section_tv_chart_lazy(data: pd.DataFrame, trades: pd.DataFrame, strategy, indicators):
    """Lazy-loaded wrapper for TV chart section."""
    return LazyTabManager.conditional_render(
        "TV_Chart",
        section_tv_chart,
        data, trades, strategy, indicators,
        description="Shows candlesticks + trades using TradingView Lightweight Charts"
    )


def section_compare(data: pd.DataFrame, picks: List[str], strat_choice: str, strat_params: Dict[str, Any], strategy_map, option_delta: float, lots: int, price_per_unit: float):
    """Compare multiple strategies side by side."""
    import plotly.graph_objs as go
    from backtester.engine import BacktestEngine
    from backtester.metrics import total_return, sharpe_ratio, max_drawdown, win_rate, profit_factor

    comp_rows = []
    fig_cmp = go.Figure()
    for name in picks:
        cls = strategy_map[name]
        p = dict(strat_params) if name == strat_choice else {"debug": False}
        s = cls(params=p)
        eng = BacktestEngine(data, s, option_delta=option_delta, lots=lots, option_price_per_unit=price_per_unit)
        rr = eng.run()
        eq = rr['equity_curve']
        tl = rr['trade_log']
        fig_cmp.add_scatter(x=eq['timestamp'], y=eq['equity'], mode='lines', name=name)
        comp_rows.append({
            'Strategy': name,
            'Total Return %': total_return(eq)*100,
            'Sharpe': sharpe_ratio(eq),
            'MaxDD %': max_drawdown(eq)*100,
            'WinRate %': win_rate(tl)*100,
            'PF': profit_factor(tl),
            'Trades': len(tl),
        })
    fig_cmp.update_layout(title='Equity Curves', xaxis_title='Time', yaxis_title='Equity')
    st.plotly_chart(fig_cmp, use_container_width=True)
    st.dataframe(pd.DataFrame(comp_rows).sort_values(['Total Return %','Sharpe'], ascending=[False, False]))


def section_export(eq_for_display: pd.DataFrame, data: pd.DataFrame, shown_trades: pd.DataFrame, indicators, strategy, metrics_dict: Dict[str, Any]):
    if shown_trades is not None and not shown_trades.empty:
        csv_bytes = shown_trades.to_csv(index=False).encode('utf-8')
        st.download_button("Download Trades CSV", data=csv_bytes, file_name=f"{strategy.__class__.__name__}_trades.csv", mime="text/csv")
    else:
        st.caption("No trades to export.")
    if eq_for_display is not None and not eq_for_display.empty:
        eq_bytes = eq_for_display.to_csv(index=False).encode('utf-8')
        st.download_button("Download Equity CSV", data=eq_bytes, file_name=f"{strategy.__class__.__name__}_equity.csv", mime="text/csv")
    else:
        st.caption("No equity to export.")
    if st.button("Generate HTML Report"):
        with st.spinner("Generating report..."):
            if eq_for_display is None or eq_for_display.empty:
                st.warning("Cannot generate report: equity curve is empty.")
                return
            tmpdir = tempfile.mkdtemp()
            report_path = os.path.join(tmpdir, "report.html")
            generate_html_report(eq_for_display, data, shown_trades, indicators, metrics_dict, report_path)
            with open(report_path, 'rb') as f:
                html_bytes = f.read()
        st.download_button("Download HTML Report", data=html_bytes, file_name="report.html", mime="text/html")
