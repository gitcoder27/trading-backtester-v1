"""High-level chart configuration builder."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..models import ChartOptions, PerformanceSettings, TradeData
from .constants import ChartConstants
from .layout import (
    build_datazoom_config,
    build_grid_config,
    build_legend_config,
    build_toolbox_config,
    build_tooltip_config,
    build_x_axis_config,
    build_y_axis_config,
)
from .series import build_series_config
from .events import build_resize_events as _build_resize_events


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
        x_max: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Build complete ECharts configuration."""
        has_oscillators = len(oscillators) > 0
        return {
            'backgroundColor': options.background_color,
            'grid': build_grid_config(has_oscillators, options),
            'tooltip': build_tooltip_config(performance, options),
            'legend': build_legend_config(performance, options),
            'toolbox': build_toolbox_config(),
            'xAxis': build_x_axis_config(options, has_oscillators),
            'yAxis': build_y_axis_config(options, performance, has_oscillators),
            'dataZoom': build_datazoom_config(x_min, x_max, performance, has_oscillators),
            'animation': performance.animation_enabled,
            'animationDuration': ChartConstants.ANIMATION_DURATION if performance.animation_enabled else 0,
            'animationEasing': ChartConstants.ANIMATION_EASING if performance.animation_enabled else None,
            'progressive': ChartConstants.PROGRESSIVE_THRESHOLD,
            'progressiveThreshold': performance.progressive_threshold,
            'dataset': [{'source': dataset}],
            'series': build_series_config(
                overlays, oscillators, trade_data, options, performance, len(dataset)
            ),
        }

    @staticmethod
    def build_resize_events() -> Dict[str, str]:
        """Build JavaScript events for chart resizing."""
        return _build_resize_events()
