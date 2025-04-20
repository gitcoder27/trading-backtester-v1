"""
reporting.py
Functions for generating plots, trade logs, and comparison tables for backtest results.
"""

import matplotlib.pyplot as plt
import plotly.graph_objs as go
import pandas as pd

def plot_trades_on_candlestick_plotly(data, trades, indicators=None, title="Trades on Candlestick Chart", show=True):
    """
    Plot historical price as a candlestick chart with trade entries/exits overlaid, using Plotly in dark mode.
    Returns the Plotly figure object.
    """
    fig = go.Figure()

    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=data['timestamp'],
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name='Price'
    ))

    # Overlay EMA or other indicators if present
    if indicators is not None and 'ema' in indicators.columns:
        fig.add_trace(go.Scatter(
            x=indicators['timestamp'],
            y=indicators['ema'],
            mode='lines',
            name='EMA-10',
            line=dict(color='orange', width=1)
        ))

    # Overlay trades
    for _, trade in trades.iterrows():
        color = 'green' if trade['pnl'] > 0 else 'red'
        # Entry marker
        fig.add_trace(go.Scatter(
            x=[trade['entry_time']],
            y=[trade['entry_price']],
            mode='markers',
            marker=dict(color=color, symbol='triangle-up', size=10),
            name='Entry' if trade['direction'].lower() == 'buy' else 'Short Entry',
            showlegend=False
        ))
        # Exit marker
        fig.add_trace(go.Scatter(
            x=[trade['exit_time']],
            y=[trade['exit_price']],
            mode='markers',
            marker=dict(color=color, symbol='x', size=10),
            name='Exit',
            showlegend=False
        ))
        # Line between entry and exit
        fig.add_trace(go.Scatter(
            x=[trade['entry_time'], trade['exit_time']],
            y=[trade['entry_price'], trade['exit_price']],
            mode='lines',
            line=dict(color=color, width=2, dash='dot'),
            name='Trade',
            showlegend=False
        ))

    fig.update_layout(
        title=title,
        xaxis_title='Time',
        yaxis_title='Price',
        template='plotly_dark',
        xaxis_rangeslider_visible=False,
        xaxis=dict(
            rangebreaks=[
                # Remove weekends
                dict(bounds=["sat", "mon"]),
                # Remove non-trading hours (example: 15:30 to 09:15 for Indian markets)
                dict(bounds=[15.5, 9.25], pattern="hour")
            ]
        )
    )
    if show:
        fig.show()
    return fig


def plot_equity_curve(equity_curve, trades=None, indicators=None, title="Equity Curve", interactive=False):
    """
    Plot the equity curve, marking trades and indicators if provided.
    """
    if interactive:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=equity_curve['timestamp'], y=equity_curve['equity'], mode='lines', name='Equity'))
        fig.update_layout(title=title, xaxis_title='Time', yaxis_title='Equity')
        fig.show()
    else:
        plt.figure(figsize=(12, 6))
        plt.plot(equity_curve['timestamp'], equity_curve['equity'], label='Equity')
        plt.title(title)
        plt.xlabel('Time')
        plt.ylabel('Equity')
        plt.legend()
        plt.tight_layout()

def plot_trades_on_price(data, trades, indicators=None, title="Trades on Price Chart", interactive=False):
    """
    Plot price data with entry/exit points, profit/loss trades, and indicators.
    """
    if interactive:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data['timestamp'], y=data['close'], mode='lines', name='Close Price'))
        if indicators is not None and 'ema' in indicators.columns:
            fig.add_trace(go.Scatter(x=indicators['timestamp'], y=indicators['ema'], mode='lines', name='EMA-10'))
        # Plot trades
        for _, trade in trades.iterrows():
            color = 'green' if trade['pnl'] > 0 else 'red'
            fig.add_trace(go.Scatter(
                x=[trade['entry_time'], trade['exit_time']],
                y=[trade['entry_price'], trade['exit_price']],
                mode='markers+lines',
                marker=dict(color=color, size=10),
                line=dict(color=color, width=2),
                name=f"{trade['direction'].capitalize()} Trade"
            ))
        fig.update_layout(title=title, xaxis_title='Time', yaxis_title='Price')
        fig.show()
    else:
        plt.figure(figsize=(14, 7))
        plt.plot(data['timestamp'], data['close'], label='Close Price', color='blue', alpha=0.7)
        if indicators is not None and 'ema' in indicators.columns:
            plt.plot(indicators['timestamp'], indicators['ema'], label='EMA-10', color='orange', alpha=0.7)
        # Plot trades
        for _, trade in trades.iterrows():
            color = 'green' if trade['pnl'] > 0 else 'red'
            plt.scatter(trade['entry_time'], trade['entry_price'], color=color, marker='^' if trade['direction']=='long' else 'v', s=100, label='Entry' if _ == 0 else "")
            plt.scatter(trade['exit_time'], trade['exit_price'], color=color, marker='o', s=80, label='Exit' if _ == 0 else "")
            plt.plot([trade['entry_time'], trade['exit_time']], [trade['entry_price'], trade['exit_price']], color=color, linewidth=2, alpha=0.6)
        plt.title(title)
        plt.xlabel('Time')
        plt.ylabel('Price')
        plt.legend()
        plt.tight_layout()

def save_trade_log(trade_log, filepath):
    """
    Save the trade log to a CSV file.
    """
    # Add final_pnl (cumulative PnL)
    trade_log = trade_log.copy()
    trade_log['final_pnl'] = trade_log['pnl'].cumsum()

    # Ensure entry_time is datetime
    entry_time = pd.to_datetime(trade_log['entry_time'])
    trade_log['entry_time'] = entry_time

    # Add day_pnl (cumulative PnL per day)
    trade_log['trade_date'] = trade_log['entry_time'].dt.date
    trade_log['day_pnl'] = trade_log.groupby('trade_date')['pnl'].cumsum()

    trade_log.to_csv(filepath, index=False)

def comparison_table(results, filepath=None):
    """
    Generate a comparison table for multiple strategies.
    """
    # results: list of dicts with keys: 'strategy', 'total_return', 'sharpe', 'max_drawdown', 'win_rate'
    df = pd.DataFrame(results)
    if filepath:
        df.to_csv(filepath, index=False)
    return df

def generate_html_report(equity_curve, data, trades, indicators, metrics, filepath):
    """
    Generate a standalone HTML report with equity curve, trades chart, and performance metrics table.
    """
    import plotly.offline as pyo
    import os
    # Equity curve figure
    eq_fig = go.Figure()
    eq_fig.add_trace(go.Scatter(
        x=equity_curve['timestamp'],
        y=equity_curve['equity'],
        mode='lines',
        name='Equity'
    ))
    eq_fig.update_layout(title='Equity Curve', xaxis_title='Time', yaxis_title='Equity')
    eq_div = pyo.plot(eq_fig, include_plotlyjs=False, output_type='div')

    # Trades candlestick figure (reuse the runtime plot function for consistency, but add customdata for JS interactivity)
    trades = trades.reset_index(drop=True).copy()
    trades['trade_id'] = trades.index  # Unique ID for each trade

    # Build chart with customdata for each trade marker/line
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
        # Entry
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
        # Exit
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
        # Line
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

    # Trade log table with data-tradeid
    trades_table = trades[['trade_id', 'entry_time', 'exit_time', 'entry_price', 'exit_price', 'direction', 'pnl']].copy()
    # Round numeric columns to 2 decimals
    for col in ['entry_price', 'exit_price', 'pnl']:
        trades_table[col] = trades_table[col].round(2)
    trades_table['entry_time'] = trades_table['entry_time'].astype(str)
    trades_table['exit_time'] = trades_table['exit_time'].astype(str)
    # Custom HTML for table rows
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

    # Metrics table
    df = pd.DataFrame(metrics, index=[0]).T.reset_index()
    df.columns = ['Metric', 'Value']
    metrics_table = df.to_html(index=False)

    # Build full HTML with JS for interactivity
    html = f"""
<html><head><meta charset='utf-8'>
<script src='https://cdn.plot.ly/plotly-latest.min.js'></script>
<title>Backtest Report</title>
<style>
/* Trade Log Table Modern Styling */
.trade-log-container {{
  width: 100%;
  overflow-x: auto;
  margin: 0 auto 2em auto;
  box-sizing: border-box;
}}
.trade-log-table {{
  width: 100%;
  border-collapse: collapse;
  font-family: 'Segoe UI', Arial, sans-serif;
  font-size: 15px;
  background: #23272e;
  color: #eaeaea;
  box-shadow: 0 2px 12px rgba(0,0,0,0.09);
  border-radius: 8px;
  overflow: hidden;
}}
.trade-log-table th, .trade-log-table td {{
  padding: 0.6em 1em;
  text-align: center;
}}
.trade-log-table th {{
  background: #2c313a;
  color: #ffd700;
  font-weight: 600;
  border-bottom: 2px solid #444;
}}
.trade-log-table tr:nth-child(even) {{
  background: #262b33;
}}
.trade-log-table tr:nth-child(odd) {{
  background: #23272e;
}}
.trade-log-table tr:hover {{
  background: #39414f;
  color: #fff;
  cursor: pointer;
}}
tr.selected {{
  background-color: #ffe066 !important;
  color: #23272e !important;
}}
@media (max-width: 700px) {{
  .trade-log-table th, .trade-log-table td {{
    font-size: 13px;
    padding: 0.4em 0.5em;
  }}
}}
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
    // Get all trade log rows
    const rows = document.querySelectorAll('#trade_log_table tbody tr');
    let lastSelected = null;
    let lastTraces = [];
    // Get Plotly chart
    const chart = document.getElementById('trade_chart');
    // Find all traces with customdata for trade highlighting
    const plotlyData = chart.data;
    // Build trade_id to trace indices map
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
        // Reset previous highlights
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
        // Highlight current
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
            // Remove previous selection
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