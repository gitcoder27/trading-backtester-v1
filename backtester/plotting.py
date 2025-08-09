"""
plotting.py
Plotting utilities for backtest reporting.
"""
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import pandas as pd

from plotly.subplots import make_subplots

def plot_trades_on_candlestick_plotly(data, trades, indicators=None, indicator_cfg=None, title="Trades on Candlestick Chart", show=True):
    """
    Plot historical price as a candlestick chart with trade entries/exits overlaid, using Plotly in dark mode.
    Supports subplots for indicators (e.g., RSI) with panel=2.
    Returns the Plotly figure object.
    indicator_cfg: list of dicts from strategy.indicator_config()
    """
    # Determine if any indicator needs a second panel
    # Normalize indicator_cfg to a list for robust handling
    cfg_list = []
    if isinstance(indicator_cfg, list):
        cfg_list = indicator_cfg
    elif isinstance(indicator_cfg, dict):
        cfg_list = [indicator_cfg]
    has_panel2 = any((cfg.get('panel', 1) == 2) for cfg in cfg_list)
    rows = 2 if has_panel2 else 1
    specs = [[{"secondary_y": False}] for _ in range(rows)]
    row_heights = [0.7, 0.3] if rows == 2 else [1.0]
    shared_x = True
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=shared_x, row_heights=row_heights, vertical_spacing=0.03)
    # Main candlestick chart (row 1)
    fig.add_trace(go.Candlestick(
        x=data['timestamp'],
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name='Price'), row=1, col=1)
    # Add indicators
    if indicators is not None and cfg_list:
        for cfg in cfg_list:
            col = cfg.get('column')
            if cfg.get('plot', True) and col in indicators.columns:
                panel = cfg.get('panel', 1)
                trace = go.Scatter(
                    x=indicators['timestamp'],
                    y=indicators[col],
                    mode='lines',
                    name=cfg.get('label', col),
                    line=dict(color=cfg.get('color', 'gray'), width=1, dash=cfg.get('type', 'solid'))
                )
                fig.add_trace(trace, row=panel, col=1)
                # If RSI, add horizontal lines
                if col.lower().startswith('rsi') and panel == 2:
                    for lvl, color in zip([20, 50, 80], ['red', 'gray', 'green']):
                        fig.add_hline(y=lvl, line_dash='dot', line_color=color, row=2, col=1)
    # Add trades (row 1) with batched traces for performance
    if trades is not None and len(trades) > 0:
        # Prepare entries and exits as single scatter traces with high-contrast styling
        entries_x, entries_y = [], []
        exits_x, exits_y = [], []
        # Prepare line segments for winners and losers separately using None separators
        win_x, win_y = [], []
        loss_x, loss_y = [], []
        for _, tr in trades.iterrows():
            is_win = (tr.get('pnl', 0) or 0) > 0
            # Entries
            entries_x.append(tr.get('entry_time'))
            entries_y.append(tr.get('entry_price'))
            # Exits
            exits_x.append(tr.get('exit_time'))
            exits_y.append(tr.get('exit_price'))
            # Lines
            if is_win:
                win_x.extend([tr.get('entry_time'), tr.get('exit_time'), None])
                win_y.extend([tr.get('entry_price'), tr.get('exit_price'), None])
            else:
                loss_x.extend([tr.get('entry_time'), tr.get('exit_time'), None])
                loss_y.extend([tr.get('entry_price'), tr.get('exit_price'), None])
        # Entries trace (non-GL to ensure marker symbols render reliably)
        fig.add_trace(go.Scatter(
            x=entries_x,
            y=entries_y,
            mode='markers',
            marker=dict(
                color='#81D4FA',  # soft light blue
                symbol='triangle-up',
                size=9,
                opacity=0.9,
                line=dict(color='#B0BEC5', width=1.0)  # soft grey outline
            ),
            name='Entries',
            showlegend=False,
            hovertemplate='Entry<br>Time: %{x}<br>Price: %{y}<extra></extra>'
        ), row=1, col=1)
        # Exits trace (non-GL)
        fig.add_trace(go.Scatter(
            x=exits_x,
            y=exits_y,
            mode='markers',
            marker=dict(
                color='#FFE082',  # soft amber
                symbol='x',
                size=9,
                opacity=0.9,
                line=dict(color='#B0BEC5', width=1.0)
            ),
            name='Exits',
            showlegend=False,
            hovertemplate='Exit<br>Time: %{x}<br>Price: %{y}<extra></extra>'
        ), row=1, col=1)
        # Winner line segments (non-GL to support dashed style clearly)
        if win_x:
            fig.add_trace(go.Scatter(
                x=win_x,
                y=win_y,
                mode='lines',
                line=dict(color='#B0BEC5', width=1.5, dash='dot'),  # light grey
                name='Winning Trades',
                showlegend=False,
                hoverinfo='skip'
            ), row=1, col=1)
        # Loser line segments (non-GL)
        if loss_x:
            fig.add_trace(go.Scatter(
                x=loss_x,
                y=loss_y,
                mode='lines',
                line=dict(color='#B0BEC5', width=1.5, dash='dot'),  # light grey
                name='Losing Trades',
                showlegend=False,
                hoverinfo='skip'
            ), row=1, col=1)
    fig.update_layout(
        title=title,
        template='plotly_dark',
        xaxis_rangeslider_visible=False,
        uirevision='chart-static',
        xaxis=dict(
            rangebreaks=[
                dict(bounds=["sat", "mon"]),
                dict(bounds=[15.5, 9.25], pattern="hour")
            ]
        )
    )
    fig.update_yaxes(title_text='Price', row=1, col=1)
    if rows == 2:
        fig.update_yaxes(title_text='RSI', row=2, col=1, range=[0, 100])
    fig.update_xaxes(title_text='Time', row=rows, col=1)
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
        return fig
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
