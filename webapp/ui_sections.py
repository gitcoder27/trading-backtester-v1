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


def render_metrics(equity_curve: pd.DataFrame, trade_log: pd.DataFrame):
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
        'entry_time', 'entry_price', 'direction', 'exit_time', 'exit_price',
        'normal_pnl', 'pnl', 'exit_reason'
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
