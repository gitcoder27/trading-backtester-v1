from __future__ import annotations
import pandas as pd
import streamlit as st
import importlib.util

_HAS_ECHARTS = importlib.util.find_spec('streamlit_echarts') is not None


def _to_iso_utc(ts_series: pd.Series) -> pd.Series:
    s = pd.to_datetime(ts_series, utc=True)
    return s.dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def _to_epoch_seconds(ts_series: pd.Series) -> pd.Series:
    """Return integer seconds since epoch (UTC)."""
    s = pd.to_datetime(ts_series, utc=True)
    return (s.view('int64') // 10**9).astype(int)


def section_advanced_chart(data: pd.DataFrame, trades: pd.DataFrame, strategy, indicators):
    """Advanced chart using a high-performance renderer (ECharts)."""
    st.subheader("Advanced Chart (Beta)")
    if data is None or len(data) == 0:
        st.info("No price data to chart.")
        return
    # We support multiple renderers (Plotly, Lightweight, ECharts); don't require any single one.

    ts_col = 'timestamp'
    df = data.copy()
    if not pd.api.types.is_datetime64_any_dtype(df[ts_col]):
        df[ts_col] = pd.to_datetime(df[ts_col])
    # Use UTCTimestamp seconds for maximum compatibility
    df['time'] = _to_epoch_seconds(df[ts_col])
    df = df.sort_values('time').reset_index(drop=True)

    # Drop rows with invalid OHLC or time; enforce sane bounds
    df = df.dropna(subset=['open', 'high', 'low', 'close', 'time'])
    # Ensure numeric
    for c in ['open', 'high', 'low', 'close']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(subset=['open', 'high', 'low', 'close'])
    # Keep only finite numbers
    import numpy as np
    df = df[np.isfinite(df[['open','high','low','close']]).all(axis=1)]
    # Filter out rows with inverted highs/lows
    df = df[df['high'] >= df['low']]
    # Deduplicate time (keep last)
    df = df.drop_duplicates(subset=['time'], keep='last')

    # Candlesticks
    price_cols = ['open', 'high', 'low', 'close']
    for pc in price_cols:
        if pc not in df.columns:
            st.warning("Chart data missing required OHLC columns.")
            return
    # Cast to native Python types for JSON serialization safety
    candles = [
        {
            'time': int(r['time']),
            'open': float(r['open']),
            'high': float(r['high']),
            'low': float(r['low']),
            'close': float(r['close']),
        }
        for _, r in df[['time'] + price_cols].iterrows()
    ]

    # Build overlays (panel=1)
    overlays = []
    indicator_cfg = strategy.indicator_config() if hasattr(strategy, 'indicator_config') else []
    if indicators is not None and len(indicator_cfg):
        indf = indicators.copy()
        if not pd.api.types.is_datetime64_any_dtype(indf[ts_col]):
            indf[ts_col] = pd.to_datetime(indf[ts_col])
        indf['time'] = _to_epoch_seconds(indf[ts_col])
        for cfg in indicator_cfg:
            col = cfg.get('column')
            if cfg.get('plot', True) and col in indf.columns and cfg.get('panel', 1) == 1:
                color = cfg.get('color', '#cccccc')
                od = indf[['time', col]].dropna().copy()
                overlays.append({
                    'type': 'Line',
                    'data': [{'time': int(t), 'value': float(v)} for t, v in zip(od['time'], od[col])],
                    'options': {
                        'color': color,
                        'lineWidth': 1,
                        'priceLineVisible': False,
                        'lastValueVisible': False,
                    },
                    'priceScaleId': 'right',
                })

    # Render with ECharts by default (fast)
    if _HAS_ECHARTS:
        import importlib
        st_echarts = importlib.import_module('streamlit_echarts').st_echarts  # type: ignore
        # Dataset: [time(ms), open, close, low, high]
        df_e = df[['time','open','close','low','high']].copy()
        df_e['tms'] = (pd.to_datetime(df_e['time'], unit='s', utc=True).view('int64') // 10**6).astype('int64')
        dataset = df_e[['tms','open','close','low','high']].values.tolist()

        # Overlays -> line series
        ech_overlays = []
        for s in overlays:
            if s.get('type') == 'Line':
                od = s['data']
                ech_overlays.append({
                    'type': 'line',
                    'name': 'overlay',
                    'showSymbol': False,
                    'data': [[int(x['time'])*1000, float(x['value'])] for x in od],
                    'lineStyle': {'width': 1, 'color': s.get('options',{}).get('color','#ccc')},
                    'yAxisIndex': 0,
                    'z': 2,
                })

        # Trades -> scatter series at entry/exit prices + line segments (win/loss)
        entries, exits = [], []
        win_lines, loss_lines = [], []
        if trades is not None and not trades.empty and {'entry_time','entry_price','exit_time','exit_price'}.issubset(trades.columns):
            tdf = trades.copy()
            tdf['entry_time'] = pd.to_datetime(tdf['entry_time'], utc=True)
            tdf['exit_time'] = pd.to_datetime(tdf['exit_time'], utc=True)
            for _, tr in tdf.iterrows():
                dir_is_long = str(tr.get('direction','long')).lower() == 'long'
                pnl = float(tr.get('pnl', 0) or 0)
                ec = '#22c55e' if dir_is_long else '#ef4444'
                xc = '#22c55e' if pnl >= 0 else '#ef4444'
                et = int(tr['entry_time'].value // 10**6)
                xt = int(tr['exit_time'].value // 10**6)
                ep = float(tr.get('entry_price', None) or df['close'].iloc[0])
                xp = float(tr.get('exit_price', None) or df['close'].iloc[0])
                entries.append({'value': [et, ep], 'itemStyle': {'color': ec, 'borderColor': '#e5e7eb', 'borderWidth': 1.2}})
                exits.append({'value': [xt, xp], 'itemStyle': {'color': xc, 'borderColor': '#e5e7eb', 'borderWidth': 1.2}})
                if pnl >= 0:
                    win_lines.extend([[et, ep], [xt, xp], None])
                else:
                    loss_lines.extend([[et, ep], [xt, xp], None])

        option = {
            'backgroundColor': '#0e1117',
            'grid': {'left': 50, 'right': 20, 'top': 20, 'bottom': 35},
            'tooltip': {'trigger': 'axis'},
            'legend': {
                'show': True,
                'textStyle': {'color': '#d1d5db'},
                'top': 10,
            },
            'toolbox': {
                'show': True,
                'feature': {
                    'saveAsImage': {'show': True},
                    'restore': {'show': True},
                    'dataZoom': {'show': True},
                },
                'right': 20,
            },
            'xAxis': {
                'type': 'time',
                'axisLine': {'lineStyle': {'color': '#374151'}},
                'axisLabel': {'color': '#d1d5db'},
            },
            'yAxis': {
                'scale': True,
                'axisLine': {'lineStyle': {'color': '#374151'}},
                'axisLabel': {'color': '#d1d5db'},
                'splitLine': {'lineStyle': {'color': '#1f2937'}},
            },
            'dataZoom': [
                {'type': 'inside', 'start': 80, 'end': 100},
                {'type': 'slider', 'start': 80, 'end': 100}
            ],
            'dataset': [{'source': dataset}],
            'series': [
                {
                    'type': 'candlestick',
                    'name': 'Price',
                    'encode': {'x': 0, 'y': [1,2,3,4]},
                    'itemStyle': {
                        'color': '#26a69a',
                        'color0': '#ef5350',
                        'borderColor': '#26a69a',
                        'borderColor0': '#ef5350'
                    },
                    'z': 1,
                },
                *ech_overlays,
                {
                    'type': 'line',
                    'name': 'Winning Trades',
                    'data': win_lines,
                    'showSymbol': False,
                    'lineStyle': {'color': '#93a1a1', 'width': 1.5, 'type': 'dotted'},
                    'z': 2,
                },
                {
                    'type': 'line',
                    'name': 'Losing Trades',
                    'data': loss_lines,
                    'showSymbol': False,
                    'lineStyle': {'color': '#93a1a1', 'width': 1.5, 'type': 'dotted'},
                    'z': 2,
                },
                {
                    'type': 'scatter',
                    'name': 'Entries',
                    'symbol': 'triangle',
                    'symbolSize': 10,
                    'data': entries,
                    'emphasis': {'scale': True},
                    'z': 3,
                },
                {
                    'type': 'scatter',
                    'name': 'Exits',
                    'symbol': 'triangle',
                    'symbolRotate': 180,
                    'symbolSize': 10,
                    'data': exits,
                    'emphasis': {'scale': True},
                    'z': 3,
                },
            ],
        }
        st_echarts(option, height='600px', theme='dark')
        return

    # If ECharts isn’t available, fallback to Plotly
    from backtester.plotting import plot_trades_on_candlestick_plotly
    fig = plot_trades_on_candlestick_plotly(
        data,
        trades if trades is not None else pd.DataFrame(),
        indicators=indicators,
        indicator_cfg=indicator_cfg,
        title="Advanced Chart (Plotly)",
        show=False,
    )
    st.plotly_chart(fig, use_container_width=True)
