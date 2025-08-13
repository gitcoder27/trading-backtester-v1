"""
UI controls for advanced chart functionality.
"""

from __future__ import annotations
import streamlit as st
from datetime import date
from typing import Tuple, Optional

from .models import DateRange, PerformanceSettings, ChartState
from ..prefs import load_prefs, save_prefs, get_pref, set_pref


class ChartControls:
    """Handles UI controls for the advanced chart."""
    
    @staticmethod
    def render_date_range_controls(
        min_date: date,
        max_date: date,
        current_start: date,
        current_end: date
    ) -> Tuple[date, date, bool]:
        """Render date range selection controls."""
        
        # Ensure current dates are within valid range
        safe_start = max(min_date, min(current_start, max_date))
        safe_end = max(min_date, min(current_end, max_date))
        
        col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
        
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=safe_start,
                min_value=min_date,
                max_value=max_date,
                key='adv_chart_start_date_picker'
            )
        
        with col2:
            end_date = st.date_input(
                "End Date",
                value=safe_end,
                min_value=min_date,
                max_value=max_date,
                key='adv_chart_end_date_picker'
            )
        
        with col3:
            st.write("")  # Spacer
            st.write("")  # Spacer
            go_clicked = st.button("Go", use_container_width=True, type="primary")
        
        return start_date, end_date, go_clicked
    
    @staticmethod
    def render_performance_controls() -> PerformanceSettings:
        """Render performance settings controls and return settings."""
        
        # Load preferences
        prefs = load_prefs()
        
        # Initialize session state from preferences if not set
        if 'adv_chart_tooltip_enabled' not in st.session_state:
            st.session_state.adv_chart_tooltip_enabled = bool(
                get_pref(prefs, 'adv_chart_tooltip_enabled', True)
            )
        if 'adv_chart_animation_enabled' not in st.session_state:
            st.session_state.adv_chart_animation_enabled = bool(
                get_pref(prefs, 'adv_chart_animation_enabled', False)
            )
        
        st.subheader("Performance Settings", help="Adjust these settings to optimize chart performance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            tooltip_enabled = st.checkbox(
                "Enable Tooltip",
                value=st.session_state.adv_chart_tooltip_enabled,
                help="Disable to reduce CPU usage on hover",
                key="adv_chart_tooltip_enabled"
            )
        
        with col2:
            animation_enabled = st.checkbox(
                "Enable Animations",
                value=st.session_state.adv_chart_animation_enabled,
                help="Disable for better performance",
                key="adv_chart_animation_enabled"
            )
        
        # Update preferences if changed
        ChartControls._update_preferences(prefs, tooltip_enabled, animation_enabled)
        
        return PerformanceSettings(
            tooltip_enabled=tooltip_enabled,
            animation_enabled=animation_enabled
        )
    
    @staticmethod
    def _update_preferences(prefs: dict, tooltip_enabled: bool, animation_enabled: bool) -> None:
        """Update user preferences if they changed."""
        changed = False
        
        if prefs.get('adv_chart_tooltip_enabled', True) != tooltip_enabled:
            set_pref(prefs, 'adv_chart_tooltip_enabled', tooltip_enabled)
            changed = True
        
        if prefs.get('adv_chart_animation_enabled', False) != animation_enabled:
            set_pref(prefs, 'adv_chart_animation_enabled', animation_enabled)
            changed = True
        
        if changed:
            save_prefs(prefs)
    
    @staticmethod
    def manage_chart_state(
        data_id: int,
        min_date: date,
        max_date: date,
        backtest_start: Optional[date] = None,
        backtest_end: Optional[date] = None
    ) -> ChartState:
        """Manage chart session state."""
        
        # Initialize session state if needed
        if 'adv_chart_data_id' not in st.session_state:
            st.session_state.adv_chart_data_id = -1
            st.session_state.render_advanced_chart = False
        
        # Create chart state object
        state = ChartState(
            data_id=st.session_state.get('adv_chart_data_id', -1),
            render_chart=st.session_state.get('render_advanced_chart', False),
            start_date=st.session_state.get('adv_chart_start_date', min_date),
            end_date=st.session_state.get('adv_chart_end_date', max_date),
            force_update=st.session_state.get('adv_chart_force_update', 0),
            force_rebuild=st.session_state.get('adv_chart_force_rebuild', 0),
            run_uid=st.session_state.get('adv_chart_run_uid', 0)
        )
        
        # Check if data changed
        if data_id != state.data_id:
            # New data detected, reset chart state
            state.reset_for_new_data(data_id, min_date, max_date)
            
            # Use backtest dates if available, otherwise use data range
            state.start_date = backtest_start or min_date
            state.end_date = backtest_end or max_date
            
            # Update session state
            ChartControls._update_session_state_from_chart_state(state)
            
            # Trigger rerun to update UI
            st.rerun()
        
        return state
    
    @staticmethod
    def _update_session_state_from_chart_state(state: ChartState) -> None:
        """Update session state from chart state object."""
        st.session_state.adv_chart_data_id = state.data_id
        st.session_state.render_advanced_chart = state.render_chart
        st.session_state.adv_chart_start_date = state.start_date
        st.session_state.adv_chart_end_date = state.end_date
        st.session_state.adv_chart_force_update = state.force_update
    
    @staticmethod
    def update_chart_state_for_render(start_date: date, end_date: date) -> None:
        """Update session state when user requests chart render."""
        st.session_state.adv_chart_start_date = start_date
        st.session_state.adv_chart_end_date = end_date
        st.session_state.render_advanced_chart = True
    
    @staticmethod
    def should_render_chart() -> bool:
        """Check if chart should be rendered."""
        return st.session_state.get('render_advanced_chart', False)
    
    @staticmethod
    def show_chart_instructions() -> None:
        """Show instructions for using the chart."""
        st.info("Select a date range and click 'Go' to render the chart.")
    
    @staticmethod
    def validate_date_range(start_date: date, end_date: date) -> bool:
        """Validate that the date range is valid."""
        return start_date <= end_date
