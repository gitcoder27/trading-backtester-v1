"""
Data models and type definitions for chart components.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Union, TypedDict
from dataclasses import dataclass, field
from datetime import datetime, date
import pandas as pd


class CandleData(TypedDict):
    """Type definition for candlestick data."""
    time: int
    open: float
    high: float
    low: float
    close: float


class TradePoint(TypedDict):
    """Type definition for trade entry/exit points."""
    value: List[Union[int, float]]
    itemStyle: Dict[str, Any]


class LineData(TypedDict):
    """Type definition for line chart data points."""
    time: int
    value: float


@dataclass
class ChartData:
    """Container for chart data."""
    candles: List[CandleData]
    overlays: List[Dict[str, Any]] = field(default_factory=list)
    oscillators: List[Dict[str, Any]] = field(default_factory=list)
    original_length: int = 0
    sampled_length: int = 0
    
    @property
    def is_sampled(self) -> bool:
        """Check if data was sampled for performance."""
        return self.original_length > self.sampled_length > 0
    
    @property
    def has_oscillators(self) -> bool:
        """Check if there are oscillators to display."""
        return len(self.oscillators) > 0


@dataclass 
class TradeData:
    """Container for trade visualization data."""
    entries: List[TradePoint] = field(default_factory=list)
    exits: List[TradePoint] = field(default_factory=list)
    win_lines: List[Union[List[Union[int, float]], None]] = field(default_factory=list)
    loss_lines: List[Union[List[Union[int, float]], None]] = field(default_factory=list)
    
    @property
    def has_trades(self) -> bool:
        """Check if there are any trades to display."""
        return len(self.entries) > 0 or len(self.exits) > 0


@dataclass
class PerformanceSettings:
    """Settings for chart performance optimization."""
    tooltip_enabled: bool = True
    animation_enabled: bool = False
    vertical_zoom_enabled: bool = True
    max_points: int = 2000
    progressive_threshold: int = 500
    large_threshold: int = 1000
    throttle_delay: int = 100
    
    def get_renderer_type(self) -> str:
        """Get optimal renderer type based on settings."""
        return 'canvas'  # Canvas is generally best for performance and quality


@dataclass
class ChartOptions:
    """Chart configuration options."""
    title: str = "Advanced Chart"
    height: str = "600px"
    width: str = "100%"
    theme: str = "dark"
    background_color: str = "#0e1117"
    # Panel height ratios for main/oscillator panels
    main_panel_ratio: int = 65
    oscillator_panel_ratio: int = 25
    
    # Color scheme
    up_color: str = "#26a69a"
    down_color: str = "#ef5350"
    grid_color: str = "#1f2937"
    text_color: str = "#d1d5db"
    border_color: str = "#374151"
    
    # Trade colors
    long_entry_color: str = "#22c55e"
    short_entry_color: str = "#ef4444"
    profit_exit_color: str = "#10b981"
    loss_exit_color: str = "#f59e0b"
    win_line_color: str = "#34d399"
    loss_line_color: str = "#fbbf24"


@dataclass
class ChartState:
    """Chart session state management."""
    data_id: int = -1
    render_chart: bool = False
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    force_update: int = 0
    force_rebuild: int = 0
    run_uid: int = 0
    
    def reset_for_new_data(self, new_data_id: int, min_date: date, max_date: date) -> None:
        """Reset state for new data."""
        self.data_id = new_data_id
        self.render_chart = False
        self.start_date = min_date
        self.end_date = max_date
        self.force_update += 1


class ChartError(Exception):
    """Custom exception for chart-related errors."""
    pass


class DataValidationError(ChartError):
    """Exception for data validation errors."""
    pass


class RenderingError(ChartError):
    """Exception for chart rendering errors."""
    pass
