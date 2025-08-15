"""
Chart configuration constants and builders.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from .models import ChartOptions, PerformanceSettings, TradeData


class ChartConstants:
    """Constants for chart configuration."""
    
    # Performance limits
    DEFAULT_MAX_POINTS = 2000
    PROGRESSIVE_THRESHOLD = 500
    LARGE_THRESHOLD = 1000
    THROTTLE_DELAY = 100
    
    # Chart dimensions
    DEFAULT_HEIGHT = "600px"
    DEFAULT_WIDTH = "100%"
    
    # Animation settings
    ANIMATION_DURATION = 300
    ANIMATION_EASING = "cubicOut"
    
    # Tooltip settings
    TOOLTIP_HIDE_DELAY = 100
    TOOLTIP_PADDING = [6, 8]
    TOOLTIP_FONT_SIZE = 11
    
    # Symbol sizes
    TRADE_SYMBOL_SIZE = 12
    TRADE_LINE_WIDTH = 2
    INDICATOR_LINE_WIDTH = 1
    
    # Z-index layers
    Z_CANDLESTICKS = 1
    Z_INDICATORS = 2
    Z_TRADE_LINES = 2
    Z_TRADE_POINTS = 3


class ChartConfig:
    """Builder class for chart configuration."""
    
    @staticmethod
    def build_echarts_option(
        dataset: List[List],
        overlays: List[Dict],
        oscillators: List[Dict],
        trade_data: TradeData,
        options: ChartOptions,
        performance: PerformanceSettings,
        x_min: Optional[int] = None,
        x_max: Optional[int] = None
    ) -> Dict[str, Any]:
        """Build complete ECharts configuration."""
        
        # Check if we need oscillator panel
        has_oscillators = len(oscillators) > 0
        
        option = {
            'backgroundColor': options.background_color,
            'grid': ChartConfig._build_grid_config(has_oscillators),
            'tooltip': ChartConfig._build_tooltip_config(performance, options),
            'legend': ChartConfig._build_legend_config(performance, options),
            'toolbox': ChartConfig._build_toolbox_config(),
            'xAxis': ChartConfig._build_x_axis_config(options, has_oscillators),
            'yAxis': ChartConfig._build_y_axis_config(options, performance, has_oscillators),
            'dataZoom': ChartConfig._build_datazoom_config(x_min, x_max, performance, has_oscillators),
            'animation': performance.animation_enabled,
            'animationDuration': ChartConstants.ANIMATION_DURATION if performance.animation_enabled else 0,
            'animationEasing': ChartConstants.ANIMATION_EASING if performance.animation_enabled else None,
            'progressive': ChartConstants.PROGRESSIVE_THRESHOLD,
            'progressiveThreshold': performance.progressive_threshold,
            'dataset': [{'source': dataset}],
            'series': ChartConfig._build_series_config(overlays, oscillators, trade_data, options, performance, len(dataset))
        }
        
        return option
    
    @staticmethod
    def _build_grid_config(has_oscillators: bool = False) -> List[Dict[str, Any]]:
        """Build grid configuration for single or dual panel setup."""
        if has_oscillators:
            # Dual panel setup: Main panel (70%) and oscillator panel (30%)
            return [
                {
                    'id': 'main',
                    'left': 50,
                    'right': 20,
                    'top': 20,
                    'height': '65%'  # Main chart takes 65%
                },
                {
                    'id': 'oscillator',
                    'left': 50,
                    'right': 20,
                    'top': '70%',  # Start at 70% from top
                    'height': '25%'  # Oscillator panel takes 25%
                }
            ]
        else:
            # Single panel setup
            return [{
                'id': 'main',
                'left': 50,
                'right': 20,
                'top': 20,
                'bottom': 35
            }]
    
    @staticmethod
    def _build_tooltip_config(performance: PerformanceSettings, options: ChartOptions) -> Dict[str, Any]:
        """Build tooltip configuration."""
        return {
            'trigger': 'axis' if performance.tooltip_enabled else 'none',
            'triggerOn': 'mousemove' if performance.tooltip_enabled else 'none',
            'enterable': False,
            'hideDelay': ChartConstants.TOOLTIP_HIDE_DELAY,
            'animation': performance.animation_enabled,
            'backgroundColor': '#1f2937',
            'borderColor': options.border_color,
            'borderWidth': 1,
            'textStyle': {
                'color': options.text_color,
                'fontSize': ChartConstants.TOOLTIP_FONT_SIZE,
                'fontFamily': 'monospace'
            },
            'padding': ChartConstants.TOOLTIP_PADDING,
            'shadowBlur': 8,
            'shadowColor': 'rgba(0, 0, 0, 0.3)',
            'shadowOffsetX': 1,
            'shadowOffsetY': 1,
            'order': 'valueDesc',
            'showContent': True,
            'confine': True,
        }
    
    @staticmethod
    def _build_legend_config(performance: PerformanceSettings, options: ChartOptions) -> Dict[str, Any]:
        """Build legend configuration."""
        return {
            'show': True,
            'textStyle': {'color': options.text_color},
            'top': 10,
            'animation': performance.animation_enabled
        }
    
    @staticmethod
    def _build_toolbox_config() -> Dict[str, Any]:
        """Build toolbox configuration."""
        return {
            'show': True,
            'feature': {
                'saveAsImage': {'show': True},
                'dataZoom': {'show': True},
                'restore': {'show': True},
            },
            'right': 20,
        }
    
    @staticmethod
    def _build_x_axis_config(options: ChartOptions, has_oscillators: bool = False) -> List[Dict[str, Any]]:
        """Build X-axis configuration for single or dual panel setup."""
        base_config = {
            'type': 'time',
            'axisLine': {'lineStyle': {'color': options.border_color}},
            'axisLabel': {'color': options.text_color},
            'animation': False  # X-axis animation usually not needed
        }
        
        # ZOOM FIX: Use single X-axis for both panels to avoid sync issues
        # This ensures perfect zoom synchronization between main and oscillator panels
        if has_oscillators:
            return [
                {
                    **base_config,
                    'gridIndex': 0,
                    'axisLabel': {'show': False}  # Hide labels on main chart
                },
                {
                    **base_config,
                    'gridIndex': 1,  # Show labels on oscillator chart
                    'position': 'bottom'  # Explicitly position at bottom
                }
            ]
        else:
            return [base_config]
    
    @staticmethod
    def _build_y_axis_config(options: ChartOptions, performance: PerformanceSettings, has_oscillators: bool = False) -> List[Dict[str, Any]]:
        """Build Y-axis configuration for single or dual panel setup."""
        main_y_axis = {
            'scale': True,
            'axisLine': {'lineStyle': {'color': options.border_color}},
            'axisLabel': {'color': options.text_color},
            'splitLine': {'lineStyle': {'color': options.grid_color}},
            'animation': performance.animation_enabled,
            'name': 'Price',
            'nameTextStyle': {'color': options.text_color}
        }
        
        if has_oscillators:
            oscillator_y_axis = {
                'scale': False,
                'axisLine': {'lineStyle': {'color': options.border_color}},
                'axisLabel': {'color': options.text_color},
                'splitLine': {'lineStyle': {'color': options.grid_color}},
                'animation': performance.animation_enabled,
                'gridIndex': 1,
                'name': 'Oscillator',
                'nameTextStyle': {'color': options.text_color},
                'min': 0,
                'max': 100  # Default range for RSI and similar oscillators
            }
            return [main_y_axis, oscillator_y_axis]
        else:
            return [main_y_axis]
    
    @staticmethod
    def _build_datazoom_config(
        x_min: Optional[int], 
        x_max: Optional[int], 
        performance: PerformanceSettings,
        has_oscillators: bool = False
    ) -> List[Dict[str, Any]]:
        """Build data zoom configuration."""
        base_config = {
            'startValue': x_min,
            'endValue': x_max,
            'throttle': performance.throttle_delay,
            'animation': performance.animation_enabled
        }
        
        # ZOOM FIX: Explicit synchronization for multi-panel charts
        if has_oscillators:
            # Use explicit axis linking with connect property for reliable sync
            return [
                {
                    'type': 'inside', 
                    **base_config, 
                    'xAxisIndex': [0, 1],
                    'filterMode': 'none',  # Don't filter data, just zoom
                    'moveOnMouseMove': True,
                    'zoomOnMouseWheel': True
                },
                {
                    'type': 'slider', 
                    **base_config, 
                    'xAxisIndex': [0, 1],
                    'filterMode': 'none',  # Don't filter data, just zoom
                    'show': True,
                    'height': 20,
                    'bottom': 10
                }
            ]
        else:
            return [
                {'type': 'inside', **base_config},
                {'type': 'slider', **base_config}
            ]
    
    @staticmethod
    def _build_series_config(
        overlays: List[Dict],
        oscillators: List[Dict],
        trade_data: TradeData,
        options: ChartOptions,
        performance: PerformanceSettings,
        dataset_length: int
    ) -> List[Dict[str, Any]]:
        """Build series configuration."""
        series = []
        
        # Candlestick series (main panel)
        series.append(ChartConfig._build_candlestick_series(options, performance, dataset_length))
        
        # Overlay series (indicators on main panel)
        series.extend(ChartConfig._build_overlay_series(overlays, performance, grid_index=0, y_axis_index=0))
        
        # Oscillator series (indicators on oscillator panel)
        series.extend(ChartConfig._build_oscillator_series(oscillators, performance))
        
        # Trade series (main panel)
        series.extend(ChartConfig._build_trade_series(trade_data, options, performance))
        
        return series
    
    @staticmethod
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
        }
    
    @staticmethod
    def _build_overlay_series(overlays: List[Dict], performance: PerformanceSettings, grid_index: int = 0, y_axis_index: int = 0) -> List[Dict[str, Any]]:
        """Build overlay (indicator) series configuration for main panel."""
        ech_overlays = []
        
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
    
    @staticmethod
    def _build_oscillator_series(oscillators: List[Dict], performance: PerformanceSettings) -> List[Dict[str, Any]]:
        """Build oscillator series configuration for oscillator panel."""
        ech_oscillators = []
        
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
                                'width': 1,
                                'color': line_color,
                                'type': 'dashed',
                                'opacity': 0.6
                            },
                            'xAxisIndex': 1,  # ZOOM FIX: Ensure reference lines use same X-axis
                            'yAxisIndex': 1,  # ZOOM FIX: Ensure reference lines use same Y-axis
                            'z': ChartConstants.Z_INDICATORS - 1,  # Behind main oscillator line
                            'animation': False,
                            'silent': True,  # Don't show in legend or tooltip
                            'showInLegend': False,
                        })
        
        return ech_oscillators
    
    @staticmethod
    def _build_trade_series(
        trade_data: TradeData,
        options: ChartOptions,
        performance: PerformanceSettings
    ) -> List[Dict[str, Any]]:
        """Build trade visualization series."""
        series = []
        
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
    
    @staticmethod
    def build_resize_events() -> Dict[str, str]:
        """Build JavaScript events for chart resizing."""
        return {
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
