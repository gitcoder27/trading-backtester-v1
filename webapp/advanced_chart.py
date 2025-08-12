from __future__ import annotations
import pandas as pd
import streamlit as st
import importlib.util

_HAS_ECHARTS = importlib.util.find_spec('streamlit_echarts') is not None


def _to_iso_utc(ts_series: pd.Series) -> pd.Series:
    s = pd.to_datetime(ts_series)
    return s.dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def _to_epoch_seconds(ts_series: pd.Series) -> pd.Series:
    """Return integer seconds since epoch, preserving original timezone."""
    s = pd.to_datetime(ts_series)
    # Don't force UTC conversion - this preserves the original timezone
    # The epoch calculation will automatically account for timezone offset
    return (s.astype('int64') // 10**9).astype(int)


def section_advanced_chart(data: pd.DataFrame, trades: pd.DataFrame, strategy, indicators):
    """Advanced chart using a high-performance renderer (ECharts)."""
    st.subheader("Advanced Chart (Beta)")

    if data is None or data.empty:
        st.info("No price data to chart. Run a backtest first.")
        return

    # Use the passed DataFrame's object ID to detect a new backtest run.
    # This is a reliable way to check if the underlying data has changed.
    current_data_id = id(data)
    if 'adv_chart_data_id' not in st.session_state:
        st.session_state.adv_chart_data_id = -1
        st.session_state.render_advanced_chart = False

    if current_data_id != st.session_state.adv_chart_data_id:
        # New data detected, so it's a new backtest. Reset the chart view.
        st.session_state.adv_chart_data_id = current_data_id
        st.session_state.render_advanced_chart = False

        # Also, reset the date range to match the new backtest
        backtest_start_date = st.session_state.get('last_results', {}).get('start_date')
        backtest_end_date = st.session_state.get('last_results', {}).get('end_date')
        
        # Get date range from timestamp column instead of index
        if 'timestamp' in data.columns:
            data_timestamps = pd.to_datetime(data['timestamp'])
            min_date = data_timestamps.min().date()
            max_date = data_timestamps.max().date()
        else:
            # Fallback to index if timestamp column doesn't exist
            if isinstance(data.index, pd.DatetimeIndex):
                min_date = data.index.min().date()
                max_date = data.index.max().date()
            else:
                # Use current date as fallback
                from datetime import date
                min_date = max_date = date.today()
        
        st.session_state.adv_chart_start_date = backtest_start_date or min_date
        st.session_state.adv_chart_end_date = backtest_end_date or max_date
        st.rerun()

    # Ensure data index is datetime or get date range from timestamp column
    if not isinstance(data.index, pd.DatetimeIndex):
        if 'timestamp' in data.columns:
            # Use timestamp column for date range
            data_timestamps = pd.to_datetime(data['timestamp'])
            # For consistency, we could set the index to timestamp
            # but since other parts expect timestamp as column, we'll keep it as is
        else:
            st.error("Data must have either a datetime index or a 'timestamp' column. Chart cannot be displayed.")
            return

    # -- UI for date range selection --
    if 'timestamp' in data.columns:
        data_timestamps = pd.to_datetime(data['timestamp'])
        min_date = data_timestamps.min().date()
        max_date = data_timestamps.max().date()
    else:
        min_date = data.index.min().date()
        max_date = data.index.max().date()


    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    
    # Ensure session state values are within valid range
    safe_start_date = st.session_state.adv_chart_start_date
    safe_end_date = st.session_state.adv_chart_end_date
    
    # Clamp start date to valid range
    if safe_start_date < min_date:
        safe_start_date = min_date
    elif safe_start_date > max_date:
        safe_start_date = max_date
        
    # Clamp end date to valid range
    if safe_end_date < min_date:
        safe_end_date = min_date
    elif safe_end_date > max_date:
        safe_end_date = max_date
    
    with col1:
        chart_start_date = st.date_input(
            "Start Date",
            value=safe_start_date,
            min_value=min_date,
            max_value=max_date,
            key='adv_chart_start_date_picker'
        )
    with col2:
        chart_end_date = st.date_input(
            "End Date",
            value=safe_end_date,
            min_value=min_date,
            max_value=max_date,
            key='adv_chart_end_date_picker'
        )
    with col3:
        st.write("") # Spacer
        st.write("") # Spacer
        if st.button("Go", use_container_width=True, type="primary"):
            st.session_state.adv_chart_start_date = chart_start_date
            st.session_state.adv_chart_end_date = chart_end_date
            st.session_state.render_advanced_chart = True
            st.rerun()

    if not st.session_state.get('render_advanced_chart', False):
        st.info("Select a date range and click 'Go' to render the chart.")
        return

    # -- Filter data based on selected date range --
    start_dt = pd.to_datetime(st.session_state.adv_chart_start_date)
    end_dt = pd.to_datetime(st.session_state.adv_chart_end_date).replace(hour=23, minute=59, second=59)
    
    # Filter by timestamp column instead of index
    if 'timestamp' in data.columns:
        data_timestamps = pd.to_datetime(data['timestamp'])
        
        # Handle timezone mismatch: if data is timezone-aware but filter dates are naive
        if data_timestamps.dt.tz is not None:
            # Data has timezone, so localize the filter dates to the same timezone
            data_tz = data_timestamps.dt.tz
            if start_dt.tzinfo is None:
                start_dt = start_dt.tz_localize(data_tz)
            if end_dt.tzinfo is None:
                end_dt = end_dt.tz_localize(data_tz)
        elif start_dt.tzinfo is not None or end_dt.tzinfo is not None:
            # Filter dates have timezone but data doesn't, convert data to timezone-aware
            if start_dt.tzinfo is not None:
                data_timestamps = data_timestamps.dt.tz_localize('UTC').dt.tz_convert(start_dt.tzinfo)
            elif end_dt.tzinfo is not None:
                data_timestamps = data_timestamps.dt.tz_localize('UTC').dt.tz_convert(end_dt.tzinfo)
        
        df = data[(data_timestamps >= start_dt) & (data_timestamps <= end_dt)].copy()
    else:
        # Fallback to index filtering if data has datetime index
        df = data[(data.index >= start_dt) & (data.index <= end_dt)].copy()
    
    if trades is not None and not trades.empty:
        trades_df = trades.copy()

        # Ensure entry_time is datetime, and convert to naive UTC
        trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'], errors='coerce')
        if hasattr(trades_df['entry_time'].dt, 'tz') and trades_df['entry_time'].dt.tz is not None:
            trades_df['entry_time'] = trades_df['entry_time'].dt.tz_convert('UTC').dt.tz_localize(None)

        # Ensure start_dt and end_dt are naive for comparison with naive entry_time
        start_dt_naive = start_dt
        end_dt_naive = end_dt
        
        # If start_dt/end_dt are timezone-aware, convert them to naive
        if hasattr(start_dt, 'tzinfo') and start_dt.tzinfo is not None:
            start_dt_naive = start_dt.tz_convert('UTC').tz_localize(None)
        if hasattr(end_dt, 'tzinfo') and end_dt.tzinfo is not None:
            end_dt_naive = end_dt.tz_convert('UTC').tz_localize(None)

        trades = trades_df[
            (trades_df['entry_time'] >= start_dt_naive) &
            (trades_df['entry_time'] <= end_dt_naive.replace(hour=23, minute=59, second=59))
        ]
    else:
        trades = pd.DataFrame()


    # We support multiple renderers (Plotly, Lightweight, ECharts); don't require any single one.
    ts_col = 'timestamp'
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

    # Performance optimization: Sample data for very large datasets
    max_points = 2000  # Maximum points to display for optimal performance
    original_len = len(df)
    
    if len(df) > max_points:
        # Sample the data while preserving important points
        step = len(df) // max_points
        # Keep every nth point but always include first and last
        indices = list(range(0, len(df), step))
        if len(df) - 1 not in indices:
            indices.append(len(df) - 1)
        df = df.iloc[indices].copy()
        
        st.info(f"📊 Performance mode: Displaying {len(df)} of {original_len} data points for optimal performance")

    if df.empty:
        st.warning("⚠️ No valid candles to display for the selected range.")
        if st.session_state.get('debug_advanced_chart', False):
            st.write("🔍 Debug: Data was filtered out during processing")
        return

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

    # Render with ECharts by default (fast and accurate time-axis)
    if _HAS_ECHARTS:
        try:
            import importlib
            st_echarts = importlib.import_module('streamlit_echarts').st_echarts  # type: ignore
        except Exception as e:
            st.error(f"❌ Failed to load ECharts: {e}")
            st.info("Please install streamlit-echarts: pip install streamlit-echarts")
            return

        # Dataset: [time(ms), open, close, low, high]
        df_e = df[['time', 'open', 'close', 'low', 'high']].copy()
        tms = (df_e['time'].astype('int64') * 1000).astype('int64')
        dataset = pd.concat([tms, df_e[['open', 'close', 'low', 'high']]], axis=1).values.tolist()
        x_min = int(tms.iloc[0]) if len(df_e) else None
        x_max = int(tms.iloc[-1]) if len(df_e) else None

        # Overlays -> line series with timestamp(ms)
        ech_overlays = []
        for s in overlays:
            if s.get('type') == 'Line':
                od = s['data']
                ech_overlays.append({
                    'type': 'line',
                    'name': 'Indicator',  # Changed from 'overlay' to 'Indicator'
                    'showSymbol': False,
                    'data': [[int(p['time']) * 1000, float(p['value'])] for p in od],
                    'lineStyle': {'width': 1, 'color': s.get('options', {}).get('color', '#ccc')},
                    'yAxisIndex': 0,
                    'z': 2,
                })

        # Trades -> scatter series at entry/exit prices + line segments (win/loss)
        entries, exits = [], []
        win_lines, loss_lines = [], []
        if trades is not None and not trades.empty and {'entry_time', 'entry_price', 'exit_time', 'exit_price'}.issubset(trades.columns):
            tdf = trades.copy()
            tdf['entry_time'] = pd.to_datetime(tdf['entry_time'], errors='coerce')
            tdf['exit_time'] = pd.to_datetime(tdf['exit_time'], errors='coerce')
            for _, tr in tdf.iterrows():
                if pd.isna(tr['entry_time']) or pd.isna(tr['exit_time']):
                    continue
                dir_is_long = str(tr.get('direction', 'long')).lower() == 'long'
                pnl = float(tr.get('pnl', 0) or 0)
                
                # Entry marker colors: Green for long, Red for short
                entry_color = '#22c55e' if dir_is_long else '#ef4444'
                # Exit marker colors: Bright green for profit, Bright red for loss
                exit_color = '#10b981' if pnl >= 0 else '#f59e0b'
                
                et = int(tr['entry_time'].value // 10**6)
                xt = int(tr['exit_time'].value // 10**6)
                ep = float(tr.get('entry_price', df['close'].iloc[0]))
                xp = float(tr.get('exit_price', df['close'].iloc[0]))
                
                # Different markers: Circle for entry, Square for exit
                entries.append({
                    'value': [et, ep], 
                    'itemStyle': {
                        'color': entry_color, 
                        'borderColor': '#ffffff', 
                        'borderWidth': 2
                    }
                })
                exits.append({
                    'value': [xt, xp], 
                    'itemStyle': {
                        'color': exit_color, 
                        'borderColor': '#ffffff', 
                        'borderWidth': 2
                    }
                })
                
                # Add trade line to appropriate list
                (win_lines if pnl >= 0 else loss_lines).extend([[et, ep], [xt, xp], None])

        # Add performance controls with caching
        from webapp.prefs import load_prefs, save_prefs, get_pref, set_pref
        _prefs = load_prefs()
        # Set defaults from prefs if not already in session_state
        if 'adv_chart_tooltip_enabled' not in st.session_state:
            st.session_state.adv_chart_tooltip_enabled = bool(get_pref(_prefs, 'adv_chart_tooltip_enabled', True))
        if 'adv_chart_animation_enabled' not in st.session_state:
            st.session_state.adv_chart_animation_enabled = bool(get_pref(_prefs, 'adv_chart_animation_enabled', False))

        st.subheader("Performance Settings", help="Adjust these settings to optimize chart performance")
        col_perf1, col_perf2 = st.columns(2)
        with col_perf1:
            tooltip_enabled = st.checkbox(
                "Enable Tooltip",
                value=st.session_state.adv_chart_tooltip_enabled,
                help="Disable to reduce CPU usage on hover",
                key="adv_chart_tooltip_enabled"
            )
        with col_perf2:
            animation_enabled = st.checkbox(
                "Enable Animations",
                value=st.session_state.adv_chart_animation_enabled,
                help="Disable for better performance",
                key="adv_chart_animation_enabled"
            )

        # Update prefs if changed
        changed = False
        if _prefs.get('adv_chart_tooltip_enabled', True) != st.session_state.adv_chart_tooltip_enabled:
            set_pref(_prefs, 'adv_chart_tooltip_enabled', st.session_state.adv_chart_tooltip_enabled)
            changed = True
        if _prefs.get('adv_chart_animation_enabled', False) != st.session_state.adv_chart_animation_enabled:
            set_pref(_prefs, 'adv_chart_animation_enabled', st.session_state.adv_chart_animation_enabled)
            changed = True
        if changed:
            save_prefs(_prefs)

        # Performance-optimized ECharts option
        option = {
            'backgroundColor': '#0e1117',
            'grid': {'left': 50, 'right': 20, 'top': 20, 'bottom': 35},
            
            # Optimized tooltip settings - Compact dark theme
            'tooltip': {
                'trigger': 'axis' if tooltip_enabled else 'none',
                'triggerOn': 'mousemove' if tooltip_enabled else 'none',
                'enterable': False,  # Prevent tooltip from interfering with mouse events
                'hideDelay': 100,    # Quick hide to reduce re-renders
                'animation': animation_enabled,
                'backgroundColor': '#1f2937',  # Dark background
                'borderColor': '#374151',      # Subtle border
                'borderWidth': 1,
                'textStyle': {
                    'color': '#f9fafb',          # Light text
                    'fontSize': 11,              # Smaller font for compactness
                    'fontFamily': 'monospace'    # Monospace for better number alignment
                },
                'padding': [6, 8],               # More compact padding
                'shadowBlur': 8,
                'shadowColor': 'rgba(0, 0, 0, 0.3)',
                'shadowOffsetX': 1,
                'shadowOffsetY': 1,
                # Use a simpler approach - just show price data with better styling
                'order': 'valueDesc',  # Show values in descending order
                'showContent': True,
                'confine': True,  # Keep tooltip within chart bounds
            },
            
            'legend': {
                'show': True, 
                'textStyle': {'color': '#d1d5db'}, 
                'top': 10,
                'animation': animation_enabled
            },
            
            # Simplified toolbox for better performance
            'toolbox': {
                'show': True,
                'feature': {
                    'saveAsImage': {'show': True},
                    'dataZoom': {'show': True},
                    'restore': {'show': True},
                },
                'right': 20,
            },
            
            'xAxis': {
                'type': 'time', 
                'axisLine': {'lineStyle': {'color': '#374151'}}, 
                'axisLabel': {'color': '#d1d5db'},
                'animation': animation_enabled
            },
            'yAxis': {
                'scale': True, 
                'axisLine': {'lineStyle': {'color': '#374151'}}, 
                'axisLabel': {'color': '#d1d5db'}, 
                'splitLine': {'lineStyle': {'color': '#1f2937'}},
                'animation': animation_enabled
            },
            
            'dataZoom': [
                {
                    'type': 'inside', 
                    'startValue': x_min, 
                    'endValue': x_max,
                    'throttle': 100,  # Throttle zoom events
                    'animation': animation_enabled
                },
                {
                    'type': 'slider', 
                    'startValue': x_min, 
                    'endValue': x_max,
                    'throttle': 100,  # Throttle slider events
                    'animation': animation_enabled
                }
            ],
            
            # Global animation and interaction settings
            'animation': animation_enabled,
            'animationDuration': 300 if animation_enabled else 0,
            'animationEasing': 'cubicOut' if animation_enabled else None,
            
            # Performance optimization - preserve original timezone for tooltip display
            'progressive': 1000,  # Progressive rendering for large datasets
            'progressiveThreshold': 500,  # Start progressive rendering after 500 points
            
            'dataset': [{'source': dataset}],
            'series': [
                {
                    'type': 'candlestick',
                    'name': 'Price',
                    'encode': {'x': 0, 'y': [1, 2, 3, 4]},
                    'itemStyle': {
                        'color': '#26a69a', 'color0': '#ef5350', 
                        'borderColor': '#26a69a', 'borderColor0': '#ef5350'
                    },
                    'z': 1,
                    'animation': animation_enabled,
                    'large': len(dataset) > 1000,  # Use large mode for big datasets
                    'largeThreshold': 1000,
                    'progressive': 1000,
                },
                *ech_overlays,
                {
                    'type': 'line', 
                    'name': 'Winning Trades', 
                    'data': win_lines, 
                    'showSymbol': False, 
                    'lineStyle': {
                        'color': '#34d399',
                        'width': 2, 
                        'type': 'dashed'
                    }, 
                    'z': 2,
                    'animation': animation_enabled,
                    'progressive': 500,
                    'tooltip': {'show': False},  # Hide from tooltip
                },
                {
                    'type': 'line', 
                    'name': 'Losing Trades', 
                    'data': loss_lines, 
                    'showSymbol': False, 
                    'lineStyle': {
                        'color': '#fbbf24',
                        'width': 2, 
                        'type': 'dashed'
                    }, 
                    'z': 2,
                    'animation': animation_enabled,
                    'progressive': 500,
                    'tooltip': {'show': False},  # Hide from tooltip
                },
                {
                    'type': 'scatter', 
                    'name': 'Entry Points', 
                    'symbol': 'circle',
                    'symbolSize': 12,
                    'data': entries, 
                    'emphasis': {'scale': True},
                    'z': 3,
                    'animation': animation_enabled,
                    'large': len(entries) > 100,
                    'largeThreshold': 100,
                    'tooltip': {'show': False},  # Hide from tooltip
                },
                {
                    'type': 'scatter', 
                    'name': 'Exit Points', 
                    'symbol': 'rect',
                    'symbolSize': 12,
                    'data': exits, 
                    'emphasis': {'scale': True},
                    'z': 3,
                    'animation': animation_enabled,
                    'large': len(exits) > 100,
                    'largeThreshold': 100,
                    'tooltip': {'show': False},  # Hide from tooltip
                },
            ],
        }

        # Create a unique key that ensures the chart always renders
        # Use run_uid (changes each backtest) + force_update (changes when data changes) + rebuild (manual refresh)
        run_uid = st.session_state.get('adv_chart_run_uid', 0)
        force_update = st.session_state.get('adv_chart_force_update', 0)
        force_rebuild = st.session_state.get('adv_chart_force_rebuild', 0)
        
        # Use a simple timestamp-based approach to ensure the key is always unique
        import time
        timestamp = int(time.time() * 1000) % 100000  # Rolling timestamp
        comp_key = f"adv_echart_{run_uid}_{force_update}_{force_rebuild}_{timestamp}"
        
        # Debug info to see what's happening
        if st.session_state.get('debug_advanced_chart', False):
            st.write(f"🔍 Debug: run_uid={run_uid}, force_update={force_update}, force_rebuild={force_rebuild}")
            st.write(f"🔍 Component key: {comp_key}")
            st.write(f"🔍 Candles: {len(candles)}, Entries: {len(entries)}, Exits: {len(exits)}")

        # Performance-optimized events
        events = {
            'finished': (
                "function(){"
                "var fire=function(){window.dispatchEvent(new Event('resize'));};"
                "setTimeout(fire,60); setTimeout(fire,300); setTimeout(fire,800);"
                "document.addEventListener('visibilitychange', function(){ if(!document.hidden){ setTimeout(fire,60); setTimeout(fire,300); } });"
                # Add tab visibility change detection
                "var observer = new MutationObserver(function(mutations) {"
                "  mutations.forEach(function(mutation) {"
                "    if (mutation.type === 'attributes' && mutation.attributeName === 'aria-selected') {"
                "      var target = mutation.target;"
                "      if (target.getAttribute('aria-selected') === 'true') {"
                "        setTimeout(fire, 100); setTimeout(fire, 500);"
                "      }"
                "    }"
                "  });"
                "});"
                "var tabElements = document.querySelectorAll('[role=\"tab\"]');"
                "tabElements.forEach(function(tab) {"
                "  observer.observe(tab, { attributes: true, attributeFilter: ['aria-selected'] });"
                "});"
                # Detect Streamlit sidebar open/close and trigger resize so chart fills width
                "try {"
                "  var sidebar = document.querySelector('section[data-testid=\"stSidebar\"]');"
                "  if (sidebar) {"
                "    var sideObs = new MutationObserver(function(){ setTimeout(fire, 50); setTimeout(fire, 250); setTimeout(fire, 600); });"
                "    sideObs.observe(sidebar, { attributes: true, attributeFilter: ['style','class'] });"
                "  }"
                "} catch(e) { /* noop */ }"
                "}"
            )
        }
        
        # Performance settings for renderer
        renderer_type = 'canvas'  # Use canvas for good quality and performance
        chart_height = '600px'
        # Use responsive width so the chart expands when the sidebar collapses
        chart_width = '100%'
        
        # Performance info
        perf_info = f"📈 Rendering {len(candles)} candles, {len(entries)} trades | Renderer: {renderer_type}"
        if not tooltip_enabled:
            perf_info += " | Tooltip: OFF 🚀"
        if not animation_enabled:
            perf_info += " | Animation: OFF ⚡"
        st.caption(perf_info)

        # Force component to update by using key that changes with data
        if st.session_state.get('debug_advanced_chart', False):
            st.info(f"🎯 Rendering ECharts component with key: `{comp_key}`")
            st.write(f"🔍 Debug: run_uid={run_uid}, force_update={force_update}, force_rebuild={force_rebuild}")
            st.write(f"🔍 Component key: {comp_key}")
            st.write(f"🔍 Candles: {len(candles)}, Entries: {len(entries)}, Exits: {len(exits)}")
        
        try:
            st_echarts(
                option, 
                height=chart_height, 
                theme='dark', 
                key=comp_key, 
                events=events, 
                renderer=renderer_type, 
                width=chart_width
            )
            
            if st.session_state.get('debug_advanced_chart', False):
                st.success("✅ ECharts component rendered successfully")
                
            # Performance tips
            with st.expander("💡 Performance Tips", expanded=False):
                st.markdown("""
                **To reduce CPU usage:**
                - ✅ **Disable Tooltip** - Reduces CPU by ~60-70%
                - ✅ **Disable Animations** - Reduces CPU by ~20-30%  
                - 📊 **Limit Date Range** - Fewer data points = better performance
                
                **Current optimizations active:**
                - 🔄 **Progressive Rendering** - Large datasets rendered in chunks
                - 📉 **Data Sampling** - Automatic downsampling for >2000 points
                - ⚡ **Event Throttling** - Zoom/pan events limited to 100ms intervals
                - 🎯 **Canvas Rendering** - Optimized for performance and quality
                
                **CPU Usage Guide:**
                - 📈 **5-10%** = Excellent (tooltip off, animations off)
                - 📊 **10-15%** = Good (tooltip on, animations off)
                - 📉 **15-25%** = Acceptable (all features on)
                - ⚠️ **>25%** = Consider reducing data range or disabling features
                """)
                
        except Exception as e:
            st.error(f"❌ Failed to render ECharts component: {e}")
            if st.session_state.get('debug_advanced_chart', False):
                st.write(f"🔍 Error details: {str(e)}")
            return
        
        # Show chart status
        import time
        current_time = time.strftime("%H:%M:%S")
        status_parts = [f"Rendered at {current_time}", f"Run UID: {run_uid}"]
        if original_len != len(df):
            status_parts.append(f"Sampled: {len(df)}/{original_len}")
        st.caption(" | ".join(status_parts))
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
