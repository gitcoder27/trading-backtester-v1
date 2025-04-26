"""
html_report.py
HTML report generation for backtest reporting.
"""
import plotly.graph_objs as go
import pandas as pd
from typing import Any

def generate_html_report(equity_curve: pd.DataFrame, data: pd.DataFrame, trades: pd.DataFrame, indicators: pd.DataFrame, metrics: dict, filepath: str) -> None:
    """
    Generate a standalone HTML report with equity curve, trades chart, and performance metrics table.
    """
    import plotly.offline as pyo
    import os
    eq_fig = go.Figure()
    eq_fig.add_trace(go.Scatter(
        x=equity_curve['timestamp'],
        y=equity_curve['equity'],
        mode='lines',
        name='Equity'
    ))
    eq_fig.update_layout(title='Equity Curve', xaxis_title='Time', yaxis_title='Equity')
    eq_div = pyo.plot(eq_fig, include_plotlyjs=False, output_type='div')
    trades = trades.reset_index(drop=True).copy()
    trades['trade_id'] = trades.index
    # Use shared plot_trades_on_candlestick_plotly for consistent plotting logic
    try:
        from .plotting import plot_trades_on_candlestick_plotly
        # If indicator_cfg is available from strategy, pass it; else fallback
        indicator_cfg = None
        # Try to get indicator_cfg from metrics, else infer from indicators
        if hasattr(metrics, 'get') and callable(getattr(metrics, 'get', None)):
            indicator_cfg = metrics.get('indicator_cfg', None)
        # Removed fallback inference; rely solely on injected indicator_cfg.
        trades = trades.reset_index(drop=True).copy()
        trades['trade_id'] = trades.index
        candlestick_fig = plot_trades_on_candlestick_plotly(
            data, trades, indicators=indicators, indicator_cfg=indicator_cfg, title="Trades on Candlestick Chart", show=False
        )
        # Add customdata for trade_id to all trade markers/lines for JS interactivity
        for i, trace in enumerate(candlestick_fig.data):
            if i >= len(candlestick_fig.data):
                break
            # Only add trade_id to trade markers/lines (skip price/indicator traces)
            if hasattr(trace, 'name') and trace.name in ['Entry', 'Short Entry', 'Exit', 'Trade']:
                # Find corresponding trade_id by matching x/y to trades
                # This is a best-effort approach for now
                if hasattr(trace, 'x') and hasattr(trace, 'y'):
                    for idx, trade in trades.iterrows():
                        if (list(trace.x) == [trade['entry_time']]) or (list(trace.x) == [trade['exit_time']]) or (list(trace.x) == [trade['entry_time'], trade['exit_time']]):
                            trace.customdata = [[trade['trade_id']]] * len(trace.x)
        trade_div = candlestick_fig.to_html(full_html=False, include_plotlyjs='cdn', div_id='trade_chart')
    except Exception as e:
        # Fallback to old logic if plot_trades_on_candlestick_plotly is unavailable or errors
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=data['timestamp'],
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            name='Price'
        ))
        if indicators is not None and 'ema' in indicators.columns:
            fig.add_trace(go.Scatter(
                x=indicators['timestamp'],
                y=indicators['ema'],
                mode='lines',
                name='EMA-10',
                line=dict(color='orange', width=1)
            ))
        for _, trade in trades.iterrows():
            color = 'green' if trade['pnl'] > 0 else 'red'
            trade_id = trade['trade_id']
            fig.add_trace(go.Scatter(
                x=[trade['entry_time']],
                y=[trade['entry_price']],
                mode='markers',
                marker=dict(color=color, symbol='triangle-up', size=10),
                name='Entry' if trade['direction'].lower() == 'buy' else 'Short Entry',
                showlegend=False,
                customdata=[[trade_id]],
                hovertemplate='Entry<br>Time: %{x}<br>Price: %{y}<extra></extra>'
            ))
            fig.add_trace(go.Scatter(
                x=[trade['exit_time']],
                y=[trade['exit_price']],
                mode='markers',
                marker=dict(color=color, symbol='x', size=10),
                name='Exit',
                showlegend=False,
                customdata=[[trade_id]],
                hovertemplate='Exit<br>Time: %{x}<br>Price: %{y}<extra></extra>'
            ))
            fig.add_trace(go.Scatter(
                x=[trade['entry_time'], trade['exit_time']],
                y=[trade['entry_price'], trade['exit_price']],
                mode='lines',
                line=dict(color=color, width=2, dash='dot'),
                name='Trade',
                showlegend=False,
                customdata=[[trade_id], [trade_id]],
                hovertemplate='Trade<br>Entry: %{x[0]}, Exit: %{x[1]}<extra></extra>'
            ))
        fig.update_layout(
            title="Trades on Candlestick Chart",
            xaxis_title='Time',
            yaxis_title='Price',
            template='plotly_dark',
            xaxis_rangeslider_visible=False,
            xaxis=dict(
                rangebreaks=[
                    dict(bounds=["sat", "mon"]),
                    dict(bounds=[15.5, 9.25], pattern="hour")
                ]
            )
        )
        trade_div = fig.to_html(full_html=False, include_plotlyjs='cdn', div_id='trade_chart')
    trades_table = trades[['trade_id', 'entry_time', 'exit_time', 'entry_price', 'exit_price', 'direction', 'pnl']].copy()
    for col in ['entry_price', 'exit_price', 'pnl']:
        trades_table[col] = trades_table[col].round(2)
    trades_table['entry_time'] = trades_table['entry_time'].astype(str)
    trades_table['exit_time'] = trades_table['exit_time'].astype(str)
    table_rows = "\n".join([
        f"<tr data-tradeid='{row.trade_id}'><td>{row.entry_time}</td><td>{row.exit_time}</td><td>{row.entry_price}</td><td>{row.exit_price}</td><td>{row.direction}</td><td>{row.pnl}</td></tr>"
        for row in trades_table.itertuples()
    ])
    trades_table_html = f"""
    <div class="trade-log-container">
    <table id="trade_log_table" class="trade-log-table">
      <thead>
        <tr>
          <th>Entry Time</th>
          <th>Exit Time</th>
          <th>Entry Price</th>
          <th>Exit Price</th>
          <th>Direction</th>
          <th>PNL</th>
        </tr>
      </thead>
      <tbody>
        {table_rows}
      </tbody>
    </table>
    </div>
    """
    # Exclude indicator configuration from the metrics table to keep only scalar values
    metrics_for_table = {k: v for k, v in metrics.items() if k != 'indicator_cfg'}
    df = pd.DataFrame(metrics_for_table, index=[0]).T.reset_index()
    df.columns = ['Metric', 'Value']
    metrics_table = df.to_html(index=False)
    html = f"""
<html><head><meta charset='utf-8'>
<script src='https://cdn.plot.ly/plotly-latest.min.js'></script>
<title>Backtest Report</title>
<style>
.trade-log-container {{ width: 100%; overflow-x: auto; margin: 0 auto 2em auto; box-sizing: border-box; }}
.trade-log-table {{ width: 100%; border-collapse: collapse; font-family: 'Segoe UI', Arial, sans-serif; font-size: 15px; background: #23272e; color: #eaeaea; box-shadow: 0 2px 12px rgba(0,0,0,0.09); border-radius: 8px; overflow: hidden; }}
.trade-log-table th, .trade-log-table td {{ padding: 0.6em 1em; text-align: center; }}
.trade-log-table th {{ background: #2c313a; color: #ffd700; font-weight: 600; border-bottom: 2px solid #444; }}
.trade-log-table tr:nth-child(even) {{ background: #262b33; }}
.trade-log-table tr:nth-child(odd) {{ background: #23272e; }}
.trade-log-table tr:hover {{ background: #39414f; color: #fff; cursor: pointer; }}
tr.selected {{ background-color: #ffe066 !important; color: #23272e !important; }}
@media (max-width: 700px) {{ .trade-log-table th, .trade-log-table td {{ font-size: 13px; padding: 0.4em 0.5em; }} }}
</style>
</head><body>
<h1>Backtest Report</h1>
<h2>Performance Metrics</h2>
{metrics_table}
<h2>Equity Curve</h2>
{eq_div}
<h2>Trades on Candlestick Chart</h2>
{trade_div}
<h2>Trade Log</h2>
{trades_table_html}
<script>
(function() {{
    const rows = document.querySelectorAll('#trade_log_table tbody tr');
    let lastSelected = null;
    let lastTraces = [];
    const chart = document.getElementById('trade_chart');
    const plotlyData = chart.data;
    const tradeIdToTraces = {{}};
    plotlyData.forEach((trace, idx) => {{
        if (trace.customdata && trace.customdata.length > 0) {{
            let ids = Array.isArray(trace.customdata[0]) ? trace.customdata.map(cd => cd[0]) : trace.customdata;
            ids.forEach((trade_id) => {{
                if (trade_id !== undefined) {{
                    if (!tradeIdToTraces[trade_id]) tradeIdToTraces[trade_id] = [];
                    tradeIdToTraces[trade_id].push(idx);
                }}
            }});
        }}
    }});
    function highlightTrade(trade_id) {{
        if (lastTraces.length > 0) {{
            lastTraces.forEach(idx => {{
                const orig = plotlyData[idx];
                let update = {{}};
                if (orig.mode && orig.mode.includes('markers')) {{
                    update.marker = {{...orig.marker, size: 10, color: orig.marker.color}};
                }}
                if (orig.mode && orig.mode.includes('lines')) {{
                    update.line = {{...orig.line, width: 2, color: orig.line.color, dash: orig.line.dash}};
                }}
                Plotly.restyle(chart, update, [idx]);
            }});
        }}
        const highlightColor = '#FFD700';
        let highlightTraces = tradeIdToTraces[trade_id] || [];
        highlightTraces.forEach(idx => {{
            const orig = plotlyData[idx];
            let update = {{}};
            if (orig.mode && orig.mode.includes('markers')) {{
                update.marker = {{...orig.marker, size: 18, color: highlightColor}};
            }}
            if (orig.mode && orig.mode.includes('lines')) {{
                update.line = {{...orig.line, width: 5, color: highlightColor, dash: orig.line.dash}};
            }}
            Plotly.restyle(chart, update, [idx]);
        }});
        lastTraces = highlightTraces;
    }}
    rows.forEach(row => {{
        row.addEventListener('click', function() {{
            if (lastSelected) lastSelected.classList.remove('selected');
            this.classList.add('selected');
            lastSelected = this;
            const trade_id = this.getAttribute('data-tradeid');
            highlightTrade(trade_id);
        }});
    }});
}})();
</script>
</body></html>
"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
