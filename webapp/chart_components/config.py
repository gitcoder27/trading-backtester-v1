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
        overlays: Dict[int, List[Dict]],
        trade_data: TradeData,
        options: ChartOptions,
        performance: PerformanceSettings,
        x_min: Optional[int] = None,
        x_max: Optional[int] = None
    ) -> Dict[str, Any]:
        """Build complete ECharts configuration."""
        
        panel_keys = sorted(overlays.keys()) if overlays else [1]
        num_panels = len(panel_keys)

        grids = ChartConfig._build_grid_config(num_panels)
        x_axes = ChartConfig._build_x_axis_config(options, num_panels)
        y_axes = ChartConfig._build_y_axis_config(options, performance, num_panels)

        option = {
            'backgroundColor': options.background_color,
            'grid': grids,
            'tooltip': ChartConfig._build_tooltip_config(performance, options, num_panels),
            'legend': ChartConfig._build_legend_config(performance, options),
            'toolbox': ChartConfig._build_toolbox_config(),
            'xAxis': x_axes,
            'yAxis': y_axes,
            'dataZoom': ChartConfig._build_datazoom_config(x_min, x_max, performance, num_panels),
            'axisPointer': { 'link': [{'xAxisIndex': 'all'}] },
            'animation': performance.animation_enabled,
            'animationDuration': ChartConstants.ANIMATION_DURATION if performance.animation_enabled else 0,
            'animationEasing': ChartConstants.ANIMATION_EASING if performance.animation_enabled else None,
            'progressive': ChartConstants.PROGRESSIVE_THRESHOLD,
            'progressiveThreshold': performance.progressive_threshold,
            'dataset': [{'source': dataset}],
            'series': ChartConfig._build_series_config(overlays, trade_data, options, performance, len(dataset))
        }
        
        return option
    
    @staticmethod
    def _build_grid_config(num_panels: int) -> List[Dict[str, Any]]:
        """Build grid configuration for multiple panels."""
        grids = []
        total_height = 80  # Percentage
        panel_height = total_height / num_panels

        for i in range(num_panels):
            grids.append({
                'left': 50,
                'right': 20,
                'top': f'{10 + i * panel_height}%',
                'height': f'{panel_height * 0.85}%' # Space between panels
            })
        return grids
    
    @staticmethod
    def _build_tooltip_config(performance: PerformanceSettings, options: ChartOptions, num_panels: int) -> Dict[str, Any]:
        """Build tooltip configuration."""
        return {
            'trigger': 'axis',
            'axisPointer': {
                'type': 'cross',
                'link': [{'xAxisIndex': 'all'}]
            },
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
    def _build_x_axis_config(options: ChartOptions, num_panels: int) -> List[Dict[str, Any]]:
        """Build X-axis configuration for multiple panels."""
        axes = []
        for i in range(num_panels):
            axes.append({
                'type': 'time',
                'gridIndex': i,
                'axisLine': {'lineStyle': {'color': options.border_color}},
                'axisLabel': {'color': options.text_color, 'show': i == num_panels -1}, # Show labels only on last axis
                'animation': False
            })
        return axes
    
    @staticmethod
    def _build_y_axis_config(options: ChartOptions, performance: PerformanceSettings, num_panels: int) -> List[Dict[str, Any]]:
        """Build Y-axis configuration for multiple panels."""
        axes = []
        for i in range(num_panels):
            axes.append({
                'scale': True,
                'gridIndex': i,
                'axisLine': {'lineStyle': {'color': options.border_color}},
                'axisLabel': {'color': options.text_color},
                'splitLine': {'lineStyle': {'color': options.grid_color}},
                'animation': performance.animation_enabled
            })
        return axes
    
    @staticmethod
    def _build_datazoom_config(
        x_min: Optional[int], 
        x_max: Optional[int], 
        performance: PerformanceSettings,
        num_panels: int
    ) -> List[Dict[str, Any]]:
        """Build data zoom configuration for multiple panels."""
        base_config = {
            'xAxisIndex': list(range(num_panels)),
            'startValue': x_min,
            'endValue': x_max,
            'throttle': performance.throttle_delay,
            'animation': performance.animation_enabled
        }
        
        return [
            {'type': 'inside', **base_config},
            {'type': 'slider', 'show': True, **base_config}
        ]
    
    @staticmethod
    def _build_series_config(
        overlays: Dict[int, List[Dict]],
        trade_data: TradeData,
        options: ChartOptions,
        performance: PerformanceSettings,
        dataset_length: int
    ) -> List[Dict[str, Any]]:
        """Build series configuration."""
        series = []
        
        # Candlestick series
        series.append(ChartConfig._build_candlestick_series(options, performance, dataset_length))
        
        # Overlay series (indicators)
        series.extend(ChartConfig._build_overlay_series(overlays, performance))
        
        # Trade series
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
            'xAxisIndex': 0,
            'yAxisIndex': 0,
            'z': ChartConstants.Z_CANDLESTICKS,
            'animation': performance.animation_enabled,
            'large': dataset_length > performance.large_threshold,
            'largeThreshold': performance.large_threshold,
            'progressive': ChartConstants.PROGRESSIVE_THRESHOLD,
        }
    
    @staticmethod
    def _build_overlay_series(overlays: Dict[int, List[Dict]], performance: PerformanceSettings) -> List[Dict[str, Any]]:
        """Build overlay (indicator) series configuration."""
        ech_overlays = []
        panel_keys = sorted(overlays.keys())
        panel_map = {panel_id: i for i, panel_id in enumerate(panel_keys)}

        for panel_id, panel_overlays in overlays.items():
            axis_index = panel_map[panel_id]
            for overlay in panel_overlays:
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
                        'xAxisIndex': axis_index,
                        'yAxisIndex': axis_index,
                        'z': ChartConstants.Z_INDICATORS,
                        'animation': performance.animation_enabled,
                    })
        
        return ech_overlays
    
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
                'xAxisIndex': 0,
                'yAxisIndex': 0,
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
                'xAxisIndex': 0,
                'yAxisIndex': 0,
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
                'xAxisIndex': 0,
                'yAxisIndex': 0,
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
                'xAxisIndex': 0,
                'yAxisIndex': 0,
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
