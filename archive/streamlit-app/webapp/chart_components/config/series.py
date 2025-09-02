"""Series configuration builders for charts."""
from __future__ import annotations

from typing import Any, Dict, List

from ..models import ChartOptions, PerformanceSettings, TradeData
from .constants import ChartConstants


def build_series_config(
    overlays: List[Dict],
    oscillators: List[Dict],
    trade_data: TradeData,
    options: ChartOptions,
    performance: PerformanceSettings,
    dataset_length: int
) -> List[Dict[str, Any]]:
    """Build series configuration."""
    series: List[Dict[str, Any]] = []

    # Candlestick series (main panel)
    series.append(_build_candlestick_series(options, performance, dataset_length))

    # Overlay series (indicators on main panel)
    series.extend(_build_overlay_series(overlays, performance, grid_index=0, y_axis_index=0))

    # Oscillator series (indicators on oscillator panel)
    series.extend(_build_oscillator_series(oscillators, performance))

    # Trade series (main panel)
    series.extend(_build_trade_series(trade_data, options, performance))

    return series


def _build_candlestick_series(
    options: ChartOptions,
    performance: PerformanceSettings,
    dataset_length: int
) -> Dict[str, Any]:
    """Build candlestick series configuration."""
    return {
        'type': 'candlestick',
        'name': 'Price',
        'encode': {'x': 0, 'y': [1, 2, 3, 4]},
        'itemStyle': {
            'color': options.up_color,
            'color0': options.down_color,
            'borderColor': options.up_color,
            'borderColor0': options.down_color
        },
        'xAxisIndex': 0,  # Use first X-axis
        'yAxisIndex': 0,  # Use first Y-axis
        'z': ChartConstants.Z_CANDLESTICKS,
        'animation': performance.animation_enabled,
        'large': dataset_length > performance.large_threshold,
        'largeThreshold': performance.large_threshold,
        'progressive': ChartConstants.PROGRESSIVE_THRESHOLD,
        'barMinWidth': ChartConstants.CANDLE_MIN_WIDTH,
        'barMaxWidth': ChartConstants.CANDLE_MAX_WIDTH,
    }


def _build_overlay_series(
    overlays: List[Dict],
    performance: PerformanceSettings,
    grid_index: int = 0,
    y_axis_index: int = 0
) -> List[Dict[str, Any]]:
    """Build overlay (indicator) series configuration for main panel."""
    ech_overlays: List[Dict[str, Any]] = []

    for overlay in overlays:
        if overlay.get('type') == 'Line':
            data = overlay['data']

            ech_overlays.append({
                'type': 'line',
                'name': overlay.get('name', 'Indicator'),
                'showSymbol': False,
                'data': [[int(p['time']) * 1000, float(p['value'])] for p in data],
                'lineStyle': {
                    'width': ChartConstants.INDICATOR_LINE_WIDTH,
                    'color': overlay.get('options', {}).get('color', '#ccc')
                },
                'xAxisIndex': grid_index,
                'yAxisIndex': y_axis_index,
                'z': ChartConstants.Z_INDICATORS,
                'animation': performance.animation_enabled,
            })

    return ech_overlays


def _build_oscillator_series(
    oscillators: List[Dict],
    performance: PerformanceSettings
) -> List[Dict[str, Any]]:
    """Build oscillator series configuration for oscillator panel."""
    ech_oscillators: List[Dict[str, Any]] = []

    for oscillator in oscillators:
        if oscillator.get('type') == 'Line':
            data = oscillator['data']
            color = oscillator.get('options', {}).get('color', '#4285f4')
            name = oscillator.get('name', 'Oscillator')

            ech_oscillators.append({
                'type': 'line',
                'name': name,
                'showSymbol': False,
                'data': [[int(p['time']) * 1000, float(p['value'])] for p in data],
                'lineStyle': {
                    'width': ChartConstants.INDICATOR_LINE_WIDTH + 1,  # Slightly thicker for oscillators
                    'color': color
                },
                'xAxisIndex': 1,  # Use second X-axis (oscillator panel)
                'yAxisIndex': 1,  # Use second Y-axis (oscillator panel)
                'z': ChartConstants.Z_INDICATORS,
                'animation': performance.animation_enabled,
            })

            # Add reference lines for RSI (20, 50, 80)
            if name.lower().startswith('rsi'):
                for level, line_color in [(20, '#ff4444'), (50, '#888888'), (80, '#44ff44')]:
                    ech_oscillators.append({
                        'type': 'line',
                        'name': f'RSI {level}',
                        'showSymbol': False,
                        'data': [[int(data[0]['time']) * 1000, level], [int(data[-1]['time']) * 1000, level]],
                        'lineStyle': {
                            'width': ChartConstants.INDICATOR_LINE_WIDTH,
                            'color': line_color,
                            'type': 'dashed'
                        },
                        'xAxisIndex': 1,
                        'yAxisIndex': 1,
                        'z': ChartConstants.Z_INDICATORS,
                        'animation': performance.animation_enabled,
                        'tooltip': {'show': False},
                    })

    return ech_oscillators


def _build_trade_series(
    trade_data: TradeData,
    options: ChartOptions,
    performance: PerformanceSettings
) -> List[Dict[str, Any]]:
    """Build trade visualization series."""
    series: List[Dict[str, Any]] = []

    # Winning trade lines
    if trade_data.win_lines:
        series.append({
            'type': 'line',
            'name': 'Winning Trades',
            'data': trade_data.win_lines,
            'showSymbol': False,
            'lineStyle': {
                'color': options.win_line_color,
                'width': ChartConstants.TRADE_LINE_WIDTH,
                'type': 'dashed'
            },
            'xAxisIndex': 0,  # Use first X-axis (main panel)
            'yAxisIndex': 0,  # Use first Y-axis (main panel)
            'z': ChartConstants.Z_TRADE_LINES,
            'animation': performance.animation_enabled,
            'progressive': ChartConstants.PROGRESSIVE_THRESHOLD // 2,
            'tooltip': {'show': False},
        })

    # Losing trade lines
    if trade_data.loss_lines:
        series.append({
            'type': 'line',
            'name': 'Losing Trades',
            'data': trade_data.loss_lines,
            'showSymbol': False,
            'lineStyle': {
                'color': options.loss_line_color,
                'width': ChartConstants.TRADE_LINE_WIDTH,
                'type': 'dashed'
            },
            'xAxisIndex': 0,  # Use first X-axis (main panel)
            'yAxisIndex': 0,  # Use first Y-axis (main panel)
            'z': ChartConstants.Z_TRADE_LINES,
            'animation': performance.animation_enabled,
            'progressive': ChartConstants.PROGRESSIVE_THRESHOLD // 2,
            'tooltip': {'show': False},
        })

    # Entry points
    if trade_data.entries:
        series.append({
            'type': 'scatter',
            'name': 'Entry Points',
            'symbol': 'circle',
            'symbolSize': ChartConstants.TRADE_SYMBOL_SIZE,
            'data': trade_data.entries,
            'emphasis': {'scale': True},
            'xAxisIndex': 0,  # Use first X-axis (main panel)
            'yAxisIndex': 0,  # Use first Y-axis (main panel)
            'z': ChartConstants.Z_TRADE_POINTS,
            'animation': performance.animation_enabled,
            'large': len(trade_data.entries) > 100,
            'largeThreshold': 100,
            'tooltip': {'show': False},
        })

    # Exit points
    if trade_data.exits:
        series.append({
            'type': 'scatter',
            'name': 'Exit Points',
            'symbol': 'rect',
            'symbolSize': ChartConstants.TRADE_SYMBOL_SIZE,
            'data': trade_data.exits,
            'emphasis': {'scale': True},
            'xAxisIndex': 0,  # Use first X-axis (main panel)
            'yAxisIndex': 0,  # Use first Y-axis (main panel)
            'z': ChartConstants.Z_TRADE_POINTS,
            'animation': performance.animation_enabled,
            'large': len(trade_data.exits) > 100,
            'largeThreshold': 100,
            'tooltip': {'show': False},
        })

    return series
