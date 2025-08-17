"""
Refactored advanced chart functionality.

This module provides a clean, maintainable interface for advanced charting
with proper separation of concerns and industry-standard practices.

Original implementation was refactored for better:
- Maintainability: Separated into logical components
- Readability: Clear class and function responsibilities  
- Production readiness: Proper error handling and logging
- Industry standards: Type hints, documentation, and patterns

The refactored version maintains full backward compatibility while improving
code organization and reducing technical debt.
"""

from __future__ import annotations
import pandas as pd
import streamlit as st
import logging
from typing import Optional

from .chart_components import (
    ChartData, TradeData, ChartOptions, PerformanceSettings, ChartState,
    TimeUtil, DataProcessor, EChartsRenderer, PlotlyFallbackRenderer,
    ChartControls, TradeVisualizer
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AdvancedChartManager:
    """Main manager class for advanced chart functionality."""
    
    def __init__(self):
        default_height = st.session_state.get('adv_chart_height', 600)
        if default_height < 500:
            main_ratio, osc_ratio = 60, 30
        else:
            main_ratio, osc_ratio = 65, 25
        self.options = ChartOptions(
            height=f"{default_height}px",
            main_panel_ratio=main_ratio,
            oscillator_panel_ratio=osc_ratio
        )
        self.performance_settings = None
        self.chart_state = None
    
    def render_chart_section(
        self, 
        data: pd.DataFrame, 
        trades: pd.DataFrame, 
        strategy, 
        indicators: Optional[pd.DataFrame]
    ) -> None:
        """
        Main entry point for rendering the advanced chart section.
        
        Args:
            data: OHLC price data DataFrame
            trades: Trades DataFrame  
            strategy: Strategy object with indicator_config method
            indicators: Optional indicators DataFrame
        """
        try:
            st.subheader("Advanced Chart (Beta)")
            
            # Add custom CSS for compact styling
            st.markdown("""
            <style>
            .stExpander > div:first-child {
                font-size: 0.9rem !important;
                font-weight: 500 !important;
            }
            .stExpander [data-testid="stExpanderDetails"] {
                padding-top: 0.5rem !important;
                padding-bottom: 0.5rem !important;
            }
            .stDateInput > div > div > label {
                font-size: 0.85rem !important;
            }
            .stDateInput > div > div {
                margin-bottom: 0.5rem !important;
            }
            .stButton > button {
                font-size: 0.85rem !important;
                height: 2.4rem !important;
                margin-top: 0rem !important;
                padding: 0.25rem 0.75rem !important;
            }
            .stCheckbox > label {
                font-size: 0.85rem !important;
            }
            .stNumberInput > div > div > label {
                font-size: 0.85rem !important;
            }
            /* Align buttons with form inputs */
            div[data-testid="column"] > div > div > div > button {
                margin-top: 1.7rem !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Early validation
            if not self._validate_input_data(data):
                return
            
            # Initialize chart state management
            min_date, max_date = DataProcessor.get_data_date_range(data)
            current_data_id = id(data)
            
            backtest_results = st.session_state.get('last_results', {})
            backtest_start = backtest_results.get('start_date')
            backtest_end = backtest_results.get('end_date')
            
            self.chart_state = ChartControls.manage_chart_state(
                data_id=current_data_id,
                min_date=min_date,
                max_date=max_date,
                backtest_start=backtest_start,
                backtest_end=backtest_end
            )
            
            # Render UI controls
            self._render_ui_controls(min_date, max_date, data)

            # Update chart options from user-selected height
            selected_height = st.session_state.get('adv_chart_height', 600)
            self.options.height = f"{selected_height}px"
            if selected_height < 500:
                self.options.main_panel_ratio = 60
                self.options.oscillator_panel_ratio = 30
            else:
                self.options.main_panel_ratio = 65
                self.options.oscillator_panel_ratio = 25

            # Load current performance settings
            self.performance_settings = ChartControls.get_performance_settings()

            # Check if chart should be rendered
            if not ChartControls.should_render_chart():
                ChartControls.show_chart_instructions()
                return
            
            # Process and filter data
            chart_data = self._process_chart_data(data, strategy, indicators)
            
            if not chart_data.candles:
                st.warning("⚠️ No valid candles to display for the selected range.")
                return
            
            # Process trade data
            filtered_trades = self._filter_trades_data(trades)
            trade_data = TradeVisualizer.process_trades_for_chart(filtered_trades, self.options)

            # Render the chart
            self._render_chart(chart_data, trade_data)

            # Performance settings section below the chart
            with st.expander("⚙️ Performance Settings", expanded=False):
                self.performance_settings = ChartControls.render_performance_controls()
            
        except Exception as e:
            logger.error(f"Chart rendering failed: {e}")
            st.error(f"❌ Failed to render chart: {e}")
    
    def _validate_input_data(self, data: pd.DataFrame) -> bool:
        """Validate input data and show appropriate messages."""
        try:
            if data is None or data.empty:
                st.info("No price data to chart. Run a backtest first.")
                return False
            
            DataProcessor.validate_data_structure(data)
            return True
            
        except Exception as e:
            st.error(f"❌ Data validation failed: {e}")
            return False
    
    def _render_ui_controls(self, min_date, max_date, data) -> None:
        """Render all UI controls for the chart."""

        # Date range controls (now first, collapsed by default)
        with st.expander("📊 Chart Date Range", expanded=False):
            start_date, end_date, go_clicked = ChartControls.render_date_range_controls(
                min_date=min_date,
                max_date=max_date,
                current_start=self.chart_state.start_date,
                current_end=self.chart_state.end_date
            )

            if go_clicked:
                if ChartControls.validate_date_range(start_date, end_date):
                    ChartControls.update_chart_state_for_render(start_date, end_date)
                    st.rerun()
                else:
                    st.error("❌ Invalid date range: Start date must be before end date.")

        # Single day controls (now second, expanded by default)
        with st.expander("📅 Single Day Navigation", expanded=True):
            try:
                if 'timestamp' in data.columns:
                    timestamps = pd.to_datetime(data['timestamp'])
                else:
                    timestamps = pd.to_datetime(data.index)

                available_dates = sorted(list(set([ts.date() for ts in timestamps])))

                if available_dates:
                    ChartControls.render_single_day_controls(min_date, max_date, available_dates)
                else:
                    st.warning("⚠️ No valid dates found in data for single day navigation.")

            except Exception as e:
                st.error(f"❌ Error in single day navigation setup: {e}")
                st.info("💡 Single day navigation is temporarily unavailable. You can still use the date range controls above.")
    
    def _process_chart_data(self, data: pd.DataFrame, strategy, indicators: Optional[pd.DataFrame]) -> ChartData:
        """Process and prepare chart data."""
        # Filter data by date range
        start_dt, end_dt = self.chart_state.start_date, self.chart_state.end_date
        start_datetime = pd.to_datetime(start_dt)
        end_datetime = pd.to_datetime(end_dt).replace(hour=23, minute=59, second=59)
        
        filtered_data = DataProcessor.filter_data_by_date_range(data, start_datetime, end_datetime)
        
        # Filter indicators by the same date range as the main data
        if indicators is not None:
            filtered_indicators = DataProcessor.filter_data_by_date_range(indicators, start_datetime, end_datetime)
        else:
            filtered_indicators = indicators
        
        # ✨ NEW: Align timestamps to ensure synchronization between panels
        # This fixes the issue where RSI warm-up period causes misaligned timestamps
        aligned_data, aligned_indicators = DataProcessor.align_data_timestamps(
            filtered_data, filtered_indicators
        )
        
        # Clean and validate OHLC data
        clean_data = DataProcessor.clean_and_validate_ohlc_data(aligned_data)
        
        # Sample data for performance if needed
        sampled_data, was_sampled = DataProcessor.sample_data_for_performance(
            clean_data, self.performance_settings.max_points if self.performance_settings else 2000
        )
        
        # Convert to candlestick format
        candles = DataProcessor.convert_to_candlestick_data(sampled_data)
        
        # Build overlay data from the aligned indicators
        indicator_config = strategy.indicator_config() if hasattr(strategy, 'indicator_config') else []
        overlays, oscillators = DataProcessor.build_overlay_data(aligned_indicators, indicator_config)
        
        return ChartData(
            candles=candles,
            overlays=overlays,
            oscillators=oscillators,
            original_length=len(clean_data),
            sampled_length=len(sampled_data) if was_sampled else len(clean_data)
        )
    
    def _filter_trades_data(self, trades: pd.DataFrame) -> pd.DataFrame:
        """Filter trades data by current date range."""
        if trades is None or trades.empty:
            return pd.DataFrame()
        
        start_dt = pd.to_datetime(self.chart_state.start_date)
        end_dt = pd.to_datetime(self.chart_state.end_date).replace(hour=23, minute=59, second=59)
        
        return DataProcessor.filter_trades_by_date_range(trades, start_dt, end_dt)
    
    def _render_chart(self, chart_data: ChartData, trade_data: TradeData) -> None:
        """Render the chart using the appropriate renderer."""
        
        # Try ECharts first
        echarts_renderer = EChartsRenderer(self.options, self.performance_settings)
        
        if echarts_renderer.is_available():
            try:
                echarts_renderer.render_chart(
                    chart_data=chart_data,
                    trade_data=trade_data,
                    run_uid=self.chart_state.run_uid,
                    force_update=self.chart_state.force_update,
                    force_rebuild=self.chart_state.force_rebuild
                )
                
                
            except Exception as e:
                logger.error(f"ECharts rendering failed, falling back to Plotly: {e}")
                self._render_plotly_fallback(chart_data, trade_data)
        else:
            st.info("ECharts not available. Install with: pip install streamlit-echarts")
            self._render_plotly_fallback(chart_data, trade_data)
    
    def _render_plotly_fallback(self, chart_data: ChartData, trade_data: TradeData) -> None:
        """Render chart using Plotly fallback."""
        try:
            # Convert data back to DataFrame format for Plotly
            # This is a temporary solution - ideally Plotly renderer should accept our data models
            start_dt = pd.to_datetime(self.chart_state.start_date)
            end_dt = pd.to_datetime(self.chart_state.end_date).replace(hour=23, minute=59, second=59)
            
            # Get original data for Plotly (it expects DataFrame format)
            data = st.session_state.get('last_data')  # This should be set by the calling code
            trades = st.session_state.get('last_trades')
            indicators = st.session_state.get('last_indicators')
            strategy = st.session_state.get('last_strategy')
            
            if data is not None:
                filtered_data = DataProcessor.filter_data_by_date_range(data, start_dt, end_dt)
                filtered_trades = self._filter_trades_data(trades) if trades is not None else pd.DataFrame()
                
                indicator_config = strategy.indicator_config() if hasattr(strategy, 'indicator_config') else []
                
                PlotlyFallbackRenderer.render_chart(
                    data=filtered_data,
                    trades=filtered_trades,
                    indicators=indicators,  # Use original indicators parameter
                    indicator_cfg=indicator_config
                )
            else:
                st.error("❌ Cannot render fallback chart: Original data not available in session state")
                
        except Exception as e:
            logger.error(f"Plotly fallback failed: {e}")
            st.error(f"❌ Chart rendering completely failed: {e}")


# Create a global instance for backward compatibility
_chart_manager = AdvancedChartManager()


def section_advanced_chart(data: pd.DataFrame, trades: pd.DataFrame, strategy, indicators):
    """
    Legacy function for backward compatibility.
    
    This maintains the same interface as the original function while using
    the new refactored implementation.
    
    Args:
        data: OHLC price data DataFrame
        trades: Trades DataFrame
        strategy: Strategy object with indicator_config method
        indicators: Optional indicators DataFrame
    """
    # Store data in session state for potential Plotly fallback
    st.session_state.last_data = data
    st.session_state.last_trades = trades
    st.session_state.last_indicators = indicators
    st.session_state.last_strategy = strategy
    
    # Use the new chart manager
    _chart_manager.render_chart_section(data, trades, strategy, indicators)


# Legacy utility functions for backward compatibility
def _to_iso_utc(ts_series: pd.Series) -> pd.Series:
    """Legacy function - use TimeUtil.to_iso_utc instead."""
    return TimeUtil.to_iso_utc(ts_series)


def _to_epoch_seconds(ts_series: pd.Series) -> pd.Series:
    """Legacy function - use TimeUtil.to_epoch_seconds instead."""
    return TimeUtil.to_epoch_seconds(ts_series)
