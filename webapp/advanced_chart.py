from __future__ import annotations
import pandas as pd
import streamlit as st

try:
    from streamlit_lightweight_charts import renderLightweightCharts
    _HAS_LWC = True
except Exception:
    _HAS_LWC = False


def section_advanced_chart(data: pd.DataFrame, trades: pd.DataFrame, strategy, indicators):
    """
    Advanced, ultra-smooth interactive chart using TradingView Lightweight Charts
    via streamlit-lightweight-charts. This is isolated from ui_sections to keep
    UI code lean and maintainable.
    """
    st.subheader("Advanced Chart (Beta)")
    if data is None or len(data) == 0:
        st.info("No price data to chart.")
        return
    if not _HAS_LWC:
        st.warning("streamlit-lightweight-charts not installed. Please pip install it to view this chart.")
        return

    ts_col = 'timestamp'
    df = data.copy()
    if not pd.api.types.is_datetime64_any_dtype(df[ts_col]):
        df[ts_col] = pd.to_datetime(df[ts_col])
    # epoch seconds, sorted
    df['time'] = (df[ts_col].astype('int64') // 10**9).astype(int)
    df = df.sort_values('time').reset_index(drop=True)

    candles = df[['time', 'open', 'high', 'low', 'close']].astype(
        {'open': 'float64', 'high': 'float64', 'low': 'float64', 'close': 'float64'}
    ).to_dict('records')

    # Overlays (only panel=1 indicators)
    overlays = []
    indicator_cfg = strategy.indicator_config() if hasattr(strategy, 'indicator_config') else []
    if indicators is not None and len(indicator_cfg):
        indf = indicators.copy()
        if not pd.api.types.is_datetime64_any_dtype(indf[ts_col]):
            indf[ts_col] = pd.to_datetime(indf[ts_col])
        indf['time'] = (indf[ts_col].astype('int64') // 10**9).astype(int)
        for cfg in indicator_cfg:
            col = cfg.get('column')
            if cfg.get('plot', True) and col in indf.columns and cfg.get('panel', 1) == 1:
                color = cfg.get('color', '#cccccc')
                overlays.append({
                    'type': 'Line',
                    'data': [{'time': int(r['time']), 'value': float(r[col])}
                             for _, r in indf.iterrows() if pd.notnull(r[col])],
                    'options': {
                        'color': color,
                        'lineWidth': 1,
                        'priceLineVisible': False,
                        'lastValueVisible': False,
                    },
                })

    # Markers (kept, but can be toggled if needed)
    trade_markers = []
    if trades is not None and not trades.empty and 'entry_time' in trades and 'exit_time' in trades:
        tdf = trades.copy()
        for col in ['entry_time', 'exit_time']:
            if not pd.api.types.is_datetime64_any_dtype(tdf[col]):
                tdf[col] = pd.to_datetime(tdf[col])
        tdf['entry_sec'] = (tdf['entry_time'].astype('int64') // 10**9).astype(int)
        tdf['exit_sec'] = (tdf['exit_time'].astype('int64') // 10**9).astype(int)
        for _, tr in tdf.iterrows():
            is_win = (tr.get('pnl', 0) or 0) > 0
            color = '#66bb6a' if is_win else '#ef5350'
            trade_markers.append({
                'time': int(tr['entry_sec']),
                'position': 'belowBar',
                'color': color,
                'shape': 'arrowUp' if str(tr.get('direction', 'long')).lower() == 'long' else 'arrowDown',
                'text': f"Entry @ {tr.get('entry_price')}",
            })
            trade_markers.append({
                'time': int(tr['exit_sec']),
                'position': 'aboveBar',
                'color': color,
                'shape': 'circle',
                'text': f"Exit @ {tr.get('exit_price')} | PnL: {tr.get('pnl')}",
            })

    series = [
        {
            'type': 'Candlestick',
            'data': candles,
            'markers': trade_markers,
            'options': {
                'upColor': '#26a69a',
                'downColor': '#ef5350',
                'borderVisible': False,
                'wickUpColor': '#26a69a',
                'wickDownColor': '#ef5350',
            }
        }
    ] + overlays

    # Add close line for guaranteed visibility
    series.append({
        'type': 'Line',
        'data': [{'time': int(t), 'value': float(v)} for t, v in zip(df['time'], df['close'])],
        'options': {'color': '#f59e0b', 'lineWidth': 1, 'priceLineVisible': False, 'lastValueVisible': False}
    })

    chartOptions = {
        'layout': {
            'background': {'type': 'solid', 'color': '#0e1117'},
            'textColor': '#d1d5db',
        },
        'grid': {
            'vertLines': {'color': '#1f2937'},
            'horzLines': {'color': '#1f2937'},
        },
        'timeScale': {
            'borderColor': '#374151',
            'timeVisible': True,
            'secondsVisible': False,
            'rightOffset': 5,
            'barSpacing': 6,
        },
        'rightPriceScale': {'borderColor': '#374151'},
        'crosshair': {'mode': 1},
        'handleScroll': {'mouseWheel': True, 'pressedMouseMove': True},
        'handleScale': {'axisPressedMouseMove': True, 'mouseWheel': True, 'pinch': True},
        'autoSize': True,
        'height': 600,
    }

    # Quick counts for sanity
    try:
        overlays_points = sum(len(s.get('data', [])) for s in overlays)
        st.caption(f"Candles: {len(candles)} | Overlays points: {overlays_points} | Markers: {len(trade_markers)}")
    except Exception:
        pass

    # Render (options inside chart dict has widest compatibility)
    renderLightweightCharts(
        charts=[{'chart': chartOptions, 'series': series}],
        key='advanced_chart_beta'
    )
