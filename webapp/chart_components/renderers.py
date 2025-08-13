"""
ECharts rendering functionality.
"""

from __future__ import annotations
import streamlit as st
import importlib.util
import importlib
import time
import logging
import pandas as pd
from typing import Optional, Dict, Any, List

from .models import ChartData, TradeData, ChartOptions, PerformanceSettings, RenderingError
from .config import ChartConfig
from .trade_viz import TradeVisualizer

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure debug messages are shown

# Check if ECharts is available
_HAS_ECHARTS = importlib.util.find_spec('streamlit_echarts') is not None


class EChartsRenderer:
    """Handles ECharts rendering for advanced charts."""
    
    def __init__(self, options: ChartOptions, performance: PerformanceSettings):
        self.options = options
        self.performance = performance
        self._st_echarts = None
        
    def is_available(self) -> bool:
        """Check if ECharts is available."""
        return _HAS_ECHARTS
    
    def _get_echarts_module(self):
        """Lazy load ECharts module."""
        if self._st_echarts is None:
            if not _HAS_ECHARTS:
                raise RenderingError("ECharts not available. Install with: pip install streamlit-echarts")
            
            try:
                self._st_echarts = importlib.import_module('streamlit_echarts').st_echarts
            except Exception as e:
                raise RenderingError(f"Failed to load ECharts: {e}")
        
        return self._st_echarts
    
    def render_chart(
        self,
        chart_data: ChartData,
        trade_data: TradeData,
        run_uid: int = 0,
        force_update: int = 0,
        force_rebuild: int = 0
    ) -> None:
        """Render the chart using ECharts."""
        try:
            st_echarts = self._get_echarts_module()
            
            # Prepare dataset for ECharts
            dataset = self._prepare_dataset(chart_data)
            x_min, x_max = self._get_time_bounds(dataset)
            
            # Build chart configuration (ChartConfig will handle overlay conversion)
            option = ChartConfig.build_echarts_option(
                dataset=dataset,
                overlays=chart_data.overlays,  # Pass original overlays, not converted ones
                trade_data=trade_data,
                options=self.options,
                performance=self.performance,
                x_min=x_min,
                x_max=x_max
            )
            
            # Generate unique component key
            component_key = self._generate_component_key(run_uid, force_update, force_rebuild)
            
            # Build resize events
            events = ChartConfig.build_resize_events()
            
            # Show performance information
            self._show_performance_info(chart_data, trade_data)
            
            # Render the chart
            st_echarts(
                option,
                height=self.options.height,
                theme=self.options.theme,
                key=component_key,
                events=events,
                renderer=self.performance.get_renderer_type(),
                width=self.options.width
            )
            
            # Show chart status
            self._show_chart_status(run_uid, chart_data)
            
        except Exception as e:
            logger.error(f"ECharts rendering failed: {e}")
            raise RenderingError(f"Chart rendering failed: {e}")
    
    def _prepare_dataset(self, chart_data: ChartData) -> List[List]:
        """Prepare dataset for ECharts candlestick chart."""
        dataset = []
        for candle in chart_data.candles:
            # Dataset format: [time(ms), open, close, low, high]
            time_ms = int(candle['time']) * 1000
            dataset.append([
                time_ms,
                candle['open'],
                candle['close'],
                candle['low'],
                candle['high']
            ])
        return dataset
    
    def _get_time_bounds(self, dataset: List[List]) -> tuple[Optional[int], Optional[int]]:
        """Get time bounds from dataset."""
        if not dataset:
            return None, None
        return int(dataset[0][0]), int(dataset[-1][0])
    
    def _generate_component_key(self, run_uid: int, force_update: int, force_rebuild: int) -> str:
        """Generate unique component key for ECharts."""
        # Use a timestamp-based approach to ensure the key is always unique
        timestamp = int(time.time() * 1000) % 100000  # Rolling timestamp
        return f"adv_echart_{run_uid}_{force_update}_{force_rebuild}_{timestamp}"
    
    def _show_performance_info(self, chart_data: ChartData, trade_data: TradeData) -> None:
        """Show performance information to user."""
        renderer_type = self.performance.get_renderer_type()
        
        perf_info = f"📈 Rendering {len(chart_data.candles)} candles, {len(trade_data.entries)} trades | Renderer: {renderer_type}"
        
        if not self.performance.tooltip_enabled:
            perf_info += " | Tooltip: OFF 🚀"
        if not self.performance.animation_enabled:
            perf_info += " | Animation: OFF ⚡"
        
        st.caption(perf_info)
        
        if chart_data.is_sampled:
            st.info(f"📊 Performance mode: Displaying {chart_data.sampled_length} of {chart_data.original_length} data points for optimal performance")
    
    def _show_chart_status(self, run_uid: int, chart_data: ChartData) -> None:
        """Show chart status information."""
        current_time = time.strftime("%H:%M:%S")
        status_parts = [f"Rendered at {current_time}", f"Run UID: {run_uid}"]
        
        if chart_data.is_sampled:
            status_parts.append(f"Sampled: {chart_data.sampled_length}/{chart_data.original_length}")
        
        st.caption(" | ".join(status_parts))
    
    @staticmethod
    def show_performance_tips() -> None:
        """Show performance optimization tips."""
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


class PlotlyFallbackRenderer:
    """Fallback renderer using Plotly when ECharts is not available."""
    
    @staticmethod
    def render_chart(data, trades, indicators, indicator_cfg):
        """Render chart using Plotly as fallback."""
        try:
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
            
        except ImportError:
            st.error("❌ Neither ECharts nor Plotly are available for chart rendering.")
            st.info("Please install one of: pip install streamlit-echarts OR pip install plotly")
        except Exception as e:
            logger.error(f"Plotly fallback rendering failed: {e}")
            st.error(f"❌ Chart rendering failed: {e}")
