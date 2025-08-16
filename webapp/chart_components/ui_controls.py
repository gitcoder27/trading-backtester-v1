"""
UI controls for advanced chart functionality.
"""

from __future__ import annotations
import streamlit as st
from datetime import date
from typing import Tuple, Optional, List

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

        # Sanitize widget state for start date picker
        start_key = 'adv_chart_start_date_picker'
        start_session_val = st.session_state.get(start_key, safe_start)
        if start_session_val < min_date or start_session_val > max_date:
            st.session_state[start_key] = safe_start
        else:
            st.session_state.setdefault(start_key, start_session_val)

        with col1:
            start_date = st.date_input(
                "Start Date",
                value=st.session_state[start_key],
                min_value=min_date,
                max_value=max_date,
                key=start_key
            )

        # Sanitize widget state for end date picker
        end_key = 'adv_chart_end_date_picker'
        end_session_val = st.session_state.get(end_key, safe_end)
        if end_session_val < min_date or end_session_val > max_date:
            st.session_state[end_key] = safe_end
        else:
            st.session_state.setdefault(end_key, end_session_val)

        with col2:
            end_date = st.date_input(
                "End Date",
                value=st.session_state[end_key],
                min_value=min_date,
                max_value=max_date,
                key=end_key
            )
        
        with col3:
            st.write("")  # Spacer
            st.write("")  # Spacer
            go_clicked = st.button("Go", use_container_width=True, type="primary")
        
        return start_date, end_date, go_clicked

    @staticmethod
    def render_single_day_controls(
        min_date: date,
        max_date: date,
        available_dates: List[date]
    ) -> None:
        """Render controls for viewing a single trading day."""

        # Get current day from session or default to first available
        current_day = st.session_state.get('adv_chart_single_day', available_dates[0])
        if current_day not in available_dates:
            current_day = available_dates[0]
            st.session_state.adv_chart_single_day = current_day

        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        # Sanitize widget state for single day picker
        day_key = 'adv_chart_single_day_picker'
        day_session_val = st.session_state.get(day_key, current_day)
        if day_session_val < min_date or day_session_val > max_date:
            st.session_state[day_key] = current_day
        else:
            st.session_state.setdefault(day_key, day_session_val)

        with col1:
            single_day = st.date_input(
                "Single Day",
                value=st.session_state[day_key],
                min_value=min_date,
                max_value=max_date,
                key=day_key
            )

        prev_day = max([d for d in available_dates if d < single_day], default=single_day)
        next_day = min([d for d in available_dates if d > single_day], default=single_day)

        with col2:
            if st.button("Prev Day", key='adv_chart_prev_day', use_container_width=True, disabled=prev_day == single_day):
                st.session_state.adv_chart_single_day = prev_day
                st.session_state.adv_chart_start_date = prev_day
                st.session_state.adv_chart_end_date = prev_day
                st.session_state[day_key] = prev_day
                st.session_state.render_advanced_chart = True
                st.rerun()

        with col3:
            if st.button("Next Day", key='adv_chart_next_day', use_container_width=True, disabled=next_day == single_day):
                st.session_state.adv_chart_single_day = next_day
                st.session_state.adv_chart_start_date = next_day
                st.session_state.adv_chart_end_date = next_day
                st.session_state[day_key] = next_day
                st.session_state.render_advanced_chart = True
                st.rerun()

        with col4:
            if st.button("Go", key='adv_chart_single_day_go', use_container_width=True, type="primary"):
                st.session_state.adv_chart_single_day = single_day
                st.session_state.adv_chart_start_date = single_day
                st.session_state.adv_chart_end_date = single_day
                st.session_state[day_key] = single_day
                st.session_state.render_advanced_chart = True
                st.rerun()
    
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
        if 'adv_chart_vertical_zoom_enabled' not in st.session_state:
            st.session_state.adv_chart_vertical_zoom_enabled = bool(
                get_pref(prefs, 'adv_chart_vertical_zoom_enabled', True)
            )
        if 'adv_chart_height' not in st.session_state:
            st.session_state.adv_chart_height = int(
                get_pref(prefs, 'adv_chart_height', 600)
            )
        
        st.subheader("Performance Settings", help="Adjust these settings to optimize chart performance")
        
        col1, col2, col3 = st.columns(3)
        
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

        with col3:
            vertical_zoom_enabled = st.checkbox(
                "Vertical Zoom",
                value=st.session_state.adv_chart_vertical_zoom_enabled,
                help="Allow zooming on the price axis",
                key="adv_chart_vertical_zoom_enabled"
            )

        chart_height = st.number_input(
            "Chart Height (px)",
            min_value=300,
            max_value=1200,
            step=50,
            value=st.session_state.adv_chart_height,
            key="adv_chart_height",
            help="Total height of the rendered chart"
        )

        # Update preferences if changed
        ChartControls._update_preferences(
            prefs,
            tooltip_enabled,
            animation_enabled,
            chart_height,
            vertical_zoom_enabled,
        )

        return PerformanceSettings(
            tooltip_enabled=tooltip_enabled,
            animation_enabled=animation_enabled,
            vertical_zoom_enabled=vertical_zoom_enabled,
        )
    
    @staticmethod
    def _update_preferences(
        prefs: dict,
        tooltip_enabled: bool,
        animation_enabled: bool,
        chart_height: int,
        vertical_zoom_enabled: bool,
    ) -> None:
        """Update user preferences if they changed."""
        changed = False

        if prefs.get('adv_chart_tooltip_enabled', True) != tooltip_enabled:
            set_pref(prefs, 'adv_chart_tooltip_enabled', tooltip_enabled)
            changed = True

        if prefs.get('adv_chart_animation_enabled', False) != animation_enabled:
            set_pref(prefs, 'adv_chart_animation_enabled', animation_enabled)
            changed = True

        if prefs.get('adv_chart_height', 600) != chart_height:
            set_pref(prefs, 'adv_chart_height', chart_height)
            changed = True

        if prefs.get('adv_chart_vertical_zoom_enabled', True) != vertical_zoom_enabled:
            set_pref(prefs, 'adv_chart_vertical_zoom_enabled', vertical_zoom_enabled)
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
        if 'adv_chart_single_day' not in st.session_state:
            st.session_state.adv_chart_single_day = min_date
        
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
            st.session_state.adv_chart_single_day = state.start_date
            
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
        if start_date == end_date:
            st.session_state.adv_chart_single_day = start_date
    
    @staticmethod
    def should_render_chart() -> bool:
        """Check if chart should be rendered."""
        return st.session_state.get('render_advanced_chart', False)
    
    @staticmethod
    def show_chart_instructions() -> None:
        """Show instructions for using the chart."""
        st.info("Select a date range and click 'Go', or choose a single day and navigate with the controls below.")
    
    @staticmethod
    def validate_date_range(start_date: date, end_date: date) -> bool:
        """Validate that the date range is valid."""
        return start_date <= end_date
