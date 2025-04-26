"""
plotting.py
Plotting utilities for backtest reporting.
"""
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import pandas as pd

def plot_trades_on_candlestick_plotly(data, trades, indicators=None, indicator_cfg=None, title="Trades on Candlestick Chart", show=True):
    """
    Plot historical price as a candlestick chart with trade entries/exits overlaid, using Plotly in dark mode.
    Returns the Plotly figure object.
    indicator_cfg: list of dicts from strategy.indicator_config()
    """
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=data['timestamp'],
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name='Price'
    ))
    if indicators is not None and indicator_cfg:
        for cfg in indicator_cfg:
            col = cfg.get('column')
            if cfg.get('plot', True) and col in indicators.columns:
                fig.add_trace(go.Scatter(
                    x=indicators['timestamp'],
                    y=indicators[col],
                    mode='lines',
                    name=cfg.get('label', col),
                    line=dict(color=cfg.get('color', 'gray'), width=1, dash=cfg.get('type', 'solid'))
                ))
    for _, trade in trades.iterrows():
        color = 'green' if trade['pnl'] > 0 else 'red'
        trade_id_str = str(trade['trade_id']) if 'trade_id' in trade else str(_)
        fig.add_trace(go.Scatter(
            x=[trade['entry_time']],
            y=[trade['entry_price']],
            mode='markers',
            marker=dict(color=color, symbol='triangle-up', size=10),
            name='Entry' if trade['direction'].lower() == 'buy' else 'Short Entry',
            showlegend=False,
            customdata=[[trade_id_str]],
            hovertemplate='Entry<br>Time: %{x}<br>Price: %{y}<extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=[trade['exit_time']],
            y=[trade['exit_price']],
            mode='markers',
            marker=dict(color=color, symbol='x', size=10),
            name='Exit',
            showlegend=False,
            customdata=[[trade_id_str]],
            hovertemplate='Exit<br>Time: %{x}<br>Price: %{y}<extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=[trade['entry_time'], trade['exit_time']],
            y=[trade['entry_price'], trade['exit_price']],
            mode='lines',
            line=dict(color=color, width=2, dash='dot'),
            name='Trade',
            showlegend=False,
            customdata=[[trade_id_str], [trade_id_str]],
            hovertemplate='Trade<br>Entry: %{x[0]}, Exit: %{x[1]}<extra></extra>'
        ))
    fig.update_layout(
        title=title,
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

def plot_trades_on_price(data, trades, indicators=None, indicator_cfg=None, title="Trades on Price Chart", interactive=False):
    """
    Plot price data with entry/exit points, profit/loss trades, and indicators.
    """
    if interactive:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data['timestamp'], y=data['close'], mode='lines', name='Close Price'))
        if indicators is not None and indicator_cfg:
            for cfg in indicator_cfg:
                col = cfg.get('column')
                if cfg.get('plot', True) and col in indicators.columns:
                    fig.add_trace(go.Scatter(
                        x=indicators['timestamp'],
                        y=indicators[col],
                        mode='lines',
                        name=cfg.get('label', col),
                        line=dict(color=cfg.get('color', 'gray'), width=1, dash=cfg.get('type', 'solid'))
                    ))
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
