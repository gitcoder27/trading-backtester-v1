"""Layout and axis configuration builders for charts."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..models import ChartOptions, PerformanceSettings
from .constants import ChartConstants


def build_grid_config(has_oscillators: bool = False, options: Optional[ChartOptions] = None) -> List[Dict[str, Any]]:
    """Build grid configuration for single or dual panel setup."""
    if has_oscillators:
        main_ratio = options.main_panel_ratio if options else 65
        osc_ratio = options.oscillator_panel_ratio if options else 25
        osc_top = main_ratio + 5  # Maintain gap between panels
        return [
            {
                'id': 'main',
                'left': 50,
                'right': 20,
                'top': 20,
                'height': f'{main_ratio}%'
            },
            {
                'id': 'oscillator',
                'left': 50,
                'right': 20,
                'top': f'{osc_top}%'
                ,
                'height': f'{osc_ratio}%'
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


def build_tooltip_config(performance: PerformanceSettings, options: ChartOptions) -> Dict[str, Any]:
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


def build_legend_config(performance: PerformanceSettings, options: ChartOptions) -> Dict[str, Any]:
    """Build legend configuration."""
    return {
        'show': True,
        'textStyle': {'color': options.text_color},
        'top': 10,
        'animation': performance.animation_enabled
    }


def build_toolbox_config() -> Dict[str, Any]:
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


def build_x_axis_config(options: ChartOptions, has_oscillators: bool = False) -> List[Dict[str, Any]]:
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


def build_y_axis_config(options: ChartOptions, performance: PerformanceSettings, has_oscillators: bool = False) -> List[Dict[str, Any]]:
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


def build_datazoom_config(
    x_min: Optional[int],
    x_max: Optional[int],
    performance: PerformanceSettings,
    has_oscillators: bool = False
) -> List[Dict[str, Any]]:
    """Build data zoom configuration."""
    base_x_config = {
        'startValue': x_min,
        'endValue': x_max,
        'throttle': performance.throttle_delay,
        'animation': performance.animation_enabled
    }

    # Vertical zoom shouldn't filter data to keep all points visible
    base_y_config = {
        'throttle': performance.throttle_delay,
        'animation': performance.animation_enabled,
        'filterMode': 'none'
    }

    # ZOOM FIX: Explicit synchronization for multi-panel charts
    if has_oscillators:
        # Use explicit axis linking with connect property for reliable sync
        zoom_config = [
            {
                'type': 'inside',
                **base_x_config,
                'xAxisIndex': [0, 1],
                'filterMode': 'none',  # Don't filter data, just zoom
                'moveOnMouseMove': True,
                'zoomOnMouseWheel': True
            },
            {
                'type': 'slider',
                **base_x_config,
                'xAxisIndex': [0, 1],
                'filterMode': 'none',  # Don't filter data, just zoom
                'show': True,
                'height': 20,
                'bottom': 10
            }
        ]
        if performance.vertical_zoom_enabled:
            zoom_config.extend([
                {
                    'type': 'inside',
                    **base_y_config,
                    'yAxisIndex': [0, 1],
                    'orient': 'vertical',
                    'moveOnMouseMove': True,
                    'zoomOnMouseWheel': True
                },
                {
                    'type': 'slider',
                    **base_y_config,
                    'yAxisIndex': [0, 1],
                    'orient': 'vertical',
                    'show': True,
                    'right': 0,
                    'width': 15
                }
            ])
        return zoom_config
    else:
        zoom_config = [
            {
                'type': 'inside',
                **base_x_config,
                'filterMode': 'none'
            },
            {
                'type': 'slider',
                **base_x_config,
                'filterMode': 'none'
            }
        ]
        if performance.vertical_zoom_enabled:
            zoom_config.extend([
                {
                    'type': 'inside',
                    **base_y_config,
                    'yAxisIndex': [0],
                    'orient': 'vertical',
                    'moveOnMouseMove': True,
                    'zoomOnMouseWheel': True
                },
                {
                    'type': 'slider',
                    **base_y_config,
                    'yAxisIndex': [0],
                    'orient': 'vertical',
                    'show': True,
                    'right': 0,
                    'width': 15
                }
            ])
        return zoom_config
