"""
Performance optimization utilities for Streamlit app.
Implements lazy loading and chart caching to improve performance.
"""
import hashlib
import streamlit as st
import pandas as pd
import time
from typing import Any, Callable, Optional, Dict
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Cache TTL in seconds (5 minutes)
CHART_CACHE_TTL = 300

class PerformanceMonitor:
    """Monitor and track performance improvements."""
    
    @staticmethod
    def start_timer(operation_name: str) -> str:
        """Start timing an operation."""
        timer_key = f"timer_{operation_name}_{int(time.time() * 1000)}"
        st.session_state[timer_key] = time.time()
        return timer_key
    
    @staticmethod
    def end_timer(timer_key: str, operation_name: str) -> float:
        """End timing and return duration."""
        if timer_key in st.session_state:
            duration = time.time() - st.session_state[timer_key]
            del st.session_state[timer_key]
            logger.info(f"⏱️ {operation_name} completed in {duration:.2f}s")
            return duration
        return 0.0
    
    @staticmethod
    def show_performance_metrics():
        """Show performance improvement metrics."""
        if hasattr(st.session_state, 'perf_metrics'):
            with st.expander("🚀 Performance Metrics", expanded=False):
                for metric, value in st.session_state.perf_metrics.items():
                    st.metric(metric, f"{value:.2f}s")


def generate_cache_key(data: Any, prefix: str = "") -> str:
    """Generate a stable cache key for data."""
    if isinstance(data, pd.DataFrame):
        # Create hash based on shape, columns, and sample of data
        key_parts = [
            str(data.shape),
            str(list(data.columns)),
        ]
        
        # Safely handle first and last row data
        if len(data) > 0:
            try:
                first_row = data.iloc[0].to_dict()
                last_row = data.iloc[-1].to_dict()
                
                # Convert datetime objects to strings for consistent hashing
                for k, v in first_row.items():
                    if pd.api.types.is_datetime64_any_dtype(type(v)):
                        first_row[k] = str(v)
                for k, v in last_row.items():
                    if pd.api.types.is_datetime64_any_dtype(type(v)):
                        last_row[k] = str(v)
                        
                key_parts.append(str(first_row))
                key_parts.append(str(last_row))
            except Exception:
                # Fallback: use just shape and columns if row access fails
                key_parts.append(f"rows_{len(data)}")
        else:
            key_parts.append("empty_df")
        
        key_string = "_".join(key_parts)
    elif isinstance(data, pd.Series):
        # Handle Series objects
        key_parts = [
            str(data.shape),
            str(data.name),
            str(data.dtype)
        ]
        if len(data) > 0:
            key_parts.append(str(data.iloc[0]))
            key_parts.append(str(data.iloc[-1]))
        key_string = "_".join(key_parts)
    else:
        key_string = str(data)
    
    # Generate hash
    hash_obj = hashlib.md5(key_string.encode())
    return f"{prefix}_{hash_obj.hexdigest()[:12]}"


def cached_chart(cache_key_prefix: str = "", ttl: int = CHART_CACHE_TTL):
    """
    Decorator for caching chart generation functions.
    
    Args:
        cache_key_prefix: Prefix for cache key
        ttl: Time to live in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Generate cache key based on function arguments
                key_parts = [cache_key_prefix, func.__name__]
                
                # Add data hashes for args
                for i, arg in enumerate(args):
                    if isinstance(arg, (pd.DataFrame, pd.Series)):
                        key_parts.append(generate_cache_key(arg, f"arg{i}"))
                    else:
                        key_parts.append(str(hash(str(arg))))
                
                # Add kwargs
                for k, v in kwargs.items():
                    if isinstance(v, (pd.DataFrame, pd.Series)):
                        key_parts.append(generate_cache_key(v, k))
                    else:
                        key_parts.append(f"{k}_{hash(str(v))}")
                
                cache_key = "_".join(key_parts)
                
                # Check cache
                cache_data = st.session_state.get(f"chart_cache_{cache_key}")
                if cache_data:
                    created_time, result = cache_data
                    if time.time() - created_time < ttl:
                        logger.info(f"📈 Using cached chart for {func.__name__}")
                        return result
                
                # Generate chart and cache it
                timer_key = PerformanceMonitor.start_timer(f"chart_{func.__name__}")
                result = func(*args, **kwargs)
                duration = PerformanceMonitor.end_timer(timer_key, f"Chart generation: {func.__name__}")
                
                # Store in cache
                st.session_state[f"chart_cache_{cache_key}"] = (time.time(), result)
                
                # Track performance
                if 'perf_metrics' not in st.session_state:
                    st.session_state.perf_metrics = {}
                st.session_state.perf_metrics[f"{func.__name__}_time"] = duration
                
                return result
                
            except Exception as e:
                logger.warning(f"Chart caching failed for {func.__name__}: {e}")
                # Fall back to generating chart without caching
                return func(*args, **kwargs)
        return wrapper
    return decorator


class LazyTabManager:
    """Manages lazy loading of tab content."""
    
    @staticmethod
    def should_load_tab(tab_name: str) -> bool:
        """Check if a tab should be loaded."""
        # Load tab if it's been explicitly requested or if it's the default tab
        return st.session_state.get(f"load_tab_{tab_name}", tab_name == "Overview")
    
    @staticmethod
    def mark_tab_for_loading(tab_name: str):
        """Mark a tab for loading on next render."""
        st.session_state[f"load_tab_{tab_name}"] = True
    
    @staticmethod
    def render_tab_placeholder(tab_name: str, description: str = ""):
        """Render a placeholder for an unloaded tab."""
        st.info(f"📊 {tab_name} tab content will load when you first visit it. {description}")
        if st.button(f"Load {tab_name} Content", key=f"load_{tab_name}_btn"):
            LazyTabManager.mark_tab_for_loading(tab_name)
            st.rerun()
    
    @staticmethod
    def conditional_render(tab_name: str, render_func: Callable, *args, **kwargs):
        """Conditionally render tab content based on loading state."""
        if LazyTabManager.should_load_tab(tab_name):
            timer_key = PerformanceMonitor.start_timer(f"tab_{tab_name}")
            
            # Remove 'description' from kwargs as it's only for placeholder
            render_kwargs = {k: v for k, v in kwargs.items() if k != 'description'}
            
            result = render_func(*args, **render_kwargs)
            PerformanceMonitor.end_timer(timer_key, f"Tab rendering: {tab_name}")
            return result
        else:
            LazyTabManager.render_tab_placeholder(tab_name, kwargs.get('description', ''))
            return None


class ChartOptimizer:
    """Optimizes chart rendering for large datasets."""
    
    @staticmethod
    def should_sample_data(data: pd.DataFrame, max_points: int = 2000) -> bool:
        """Check if data should be sampled for performance."""
        return len(data) > max_points
    
    @staticmethod
    def sample_data_for_charts(data: pd.DataFrame, max_points: int = 2000) -> tuple[pd.DataFrame, bool]:
        """Sample data for chart rendering if needed."""
        if data is None or data.empty:
            return data, False
            
        if not ChartOptimizer.should_sample_data(data, max_points):
            return data, False
        
        # Smart sampling: keep more recent data
        step = len(data) // max_points
        if step < 2:
            return data, False
        
        try:
            # Take every nth point, but ensure we get recent data
            recent_data = data.iloc[-max_points//4:]  # Last 25% at full resolution
            sampled_data = data.iloc[:-max_points//4:step]  # Earlier data sampled
            
            combined_data = pd.concat([sampled_data, recent_data]).drop_duplicates().sort_index()
            
            logger.info(f"📊 Sampled data from {len(data)} to {len(combined_data)} points for performance")
            return combined_data, True
        except Exception as e:
            logger.warning(f"Data sampling failed: {e}. Using original data.")
            return data, False
    
    @staticmethod
    def optimize_chart_data(data: pd.DataFrame, trades: pd.DataFrame = None, max_points: int = 2000) -> tuple[pd.DataFrame, pd.DataFrame, bool]:
        """Optimize both price data and trades for chart rendering."""
        optimized_data, was_sampled = ChartOptimizer.sample_data_for_charts(data, max_points)
        
        if trades is not None and was_sampled and not trades.empty:
            # Filter trades to match the optimized data time range
            start_time = optimized_data['timestamp'].min()
            end_time = optimized_data['timestamp'].max()
            
            # Ensure datetime compatibility by converting to pandas datetime
            if 'entry_time' in trades.columns:
                # Convert entry_time to datetime if it isn't already
                trades_copy = trades.copy()
                trades_copy['entry_time'] = pd.to_datetime(trades_copy['entry_time'])
                
                # Convert start_time and end_time to the same timezone-naive format
                start_time = pd.to_datetime(start_time).tz_localize(None) if pd.to_datetime(start_time).tz is not None else pd.to_datetime(start_time)
                end_time = pd.to_datetime(end_time).tz_localize(None) if pd.to_datetime(end_time).tz is not None else pd.to_datetime(end_time)
                
                # Make sure trades entry_time is also timezone-naive
                if trades_copy['entry_time'].dt.tz is not None:
                    trades_copy['entry_time'] = trades_copy['entry_time'].dt.tz_localize(None)
                
                optimized_trades = trades_copy[
                    (trades_copy['entry_time'] >= start_time) & 
                    (trades_copy['entry_time'] <= end_time)
                ].copy()
            else:
                optimized_trades = trades.copy()
        else:
            optimized_trades = trades.copy() if trades is not None else None
        
        return optimized_data, optimized_trades, was_sampled


def clear_chart_cache():
    """Clear all cached charts."""
    keys_to_remove = [key for key in st.session_state.keys() if key.startswith('chart_cache_')]
    for key in keys_to_remove:
        del st.session_state[key]
    st.success(f"🗑️ Cleared {len(keys_to_remove)} cached charts")


def show_cache_stats():
    """Show cache statistics."""
    cache_keys = [key for key in st.session_state.keys() if key.startswith('chart_cache_')]
    if cache_keys:
        st.info(f"📈 {len(cache_keys)} charts cached for better performance")
        if st.button("Clear Cache"):
            clear_chart_cache()
            st.rerun()
    else:
        st.info("📈 No charts cached yet")
