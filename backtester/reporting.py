"""
reporting.py
Functions for generating plots, trade logs, and comparison tables for backtest results.
"""

import matplotlib.pyplot as plt
import plotly.graph_objs as go
import pandas as pd
def plot_trades_on_candlestick_plotly(data, trades, indicators=None, title="Trades on Candlestick Chart"):
    """
    Plot historical price as a candlestick chart with trade entries/exits overlaid, using Plotly in dark mode.
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
    fig.show()

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