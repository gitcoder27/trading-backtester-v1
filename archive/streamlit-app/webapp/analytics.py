from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.express as px

__all__ = [
    'compute_returns',
    'compute_drawdown',
    'rolling_sharpe',
    'monthly_returns_heatmap',
    'filter_trades',
]


def compute_returns(equity_curve: pd.DataFrame) -> pd.Series:
    eq = equity_curve['equity'].astype(float).values
    if len(eq) < 2:
        return pd.Series([], dtype=float)
    rets = np.diff(eq)
    idx = equity_curve['timestamp'].iloc[1:]
    return pd.Series(rets, index=idx)


def compute_drawdown(equity_curve: pd.DataFrame) -> pd.DataFrame:
    eq = equity_curve['equity'].astype(float)
    cummax = eq.cummax()
    dd = (eq / cummax) - 1.0
    return pd.DataFrame({
        'timestamp': equity_curve['timestamp'],
        'drawdown': dd
    })


def rolling_sharpe(equity_curve: pd.DataFrame, window: int = 50) -> pd.DataFrame:
    rets = compute_returns(equity_curve)
    if rets.empty:
        return pd.DataFrame({'timestamp': [], 'rolling_sharpe': []})
    # 252 trading days * 6.5 hours * 60 minutes for a minute-like bar annualization
    s = rets.rolling(window).apply(lambda x: (x.mean() / (x.std() + 1e-9)) * np.sqrt(252*60*6.5), raw=False)
    return pd.DataFrame({'timestamp': s.index, 'rolling_sharpe': s.values})


def monthly_returns_heatmap(equity_curve: pd.DataFrame):
    rets = compute_returns(equity_curve)
    if rets.empty:
        return None
    df = rets.to_frame('ret')
    df['month'] = df.index.to_period('M').astype(str)
    piv = df.groupby('month')['ret'].sum().reset_index()
    piv['Year'] = piv['month'].str[:4]
    piv['Mon'] = piv['month'].str[5:7]
    table = piv.pivot(index='Year', columns='Mon', values='ret').fillna(0.0)
    fig = px.imshow(
        table,
        text_auto=True,
        color_continuous_scale='RdYlGn',
        aspect='auto',
        origin='lower',
        title='Monthly Returns Heatmap',
    )
    return fig


def filter_trades(trades: pd.DataFrame, directions: list[str], hours=None, weekdays=None) -> pd.DataFrame:
    if trades is None or trades.empty:
        return trades
    df = trades.copy()
    if directions:
        df = df[df['direction'].str.lower().isin(directions)]
    if hours is not None:
        sh, eh = hours
        et = pd.to_datetime(df['entry_time'])
        df = df[(et.dt.hour >= sh) & (et.dt.hour <= eh)]
    if weekdays is not None:
        et = pd.to_datetime(df['entry_time'])
        df = df[et.dt.weekday.isin(weekdays)]
    return df
