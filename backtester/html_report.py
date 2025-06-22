"""
html_report.py
HTML report generation for backtest reporting.
"""
import plotly.graph_objs as go
import pandas as pd
from typing import Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
from backtester.plotting import plot_trades_on_candlestick_plotly # Changed from relative to absolute

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
        if hasattr(metrics, 'get') and callable(getattr(metrics, 'get', None)):
            indicator_cfg = metrics.get('indicator_cfg', None)
        candlestick_fig = plot_trades_on_candlestick_plotly(
            data, trades, indicators=indicators, indicator_cfg=indicator_cfg, title="Trades on Candlestick Chart", show=False
        )
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
    df = pd.DataFrame(list(metrics.items()), columns=['Metric', 'Value'])
    metrics_table = df.to_html(index=False)
    # Jinja2 template rendering
    env = Environment(
        loader=FileSystemLoader(os.path.dirname(__file__)),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template('report_template.html')
    trades_dicts = trades.to_dict(orient='records')
    trade_log_columns = trades.columns.tolist()
    html = template.render(
        metrics_table=metrics_table,
        eq_div=eq_div,
        trade_div=trade_div,
        trade_log=trades_dicts,
        trade_log_columns=trade_log_columns
    )
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
